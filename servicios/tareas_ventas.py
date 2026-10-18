"""
Tareas pesadas sobre las ventas, pensadas para correr en segundo plano.

Patrón Runnable + Thread (equivalente en Python al de Java):

    tarea = TareaCargarVentas(...)                 # el "Runnable": QUÉ se hace
    hilo  = threading.Thread(target=tarea.run)     # el "Thread":   QUIÉN lo ejecuta
    hilo.start()

Reglas que siguen estas clases:

  * NUNCA tocan widgets de Tkinter (Tkinter no es seguro entre hilos).
  * NUNCA modifican datos del modelo (inventario, ticket, etc.).
  * Se comunican con la ventana SOLO mediante una queue.Queue, que es segura
    entre hilos. La ventana la lee con `after()` desde su propio hilo.
  * El resultado (ResumenVentas) se construye en variables locales del hilo y
    se publica completo, una sola vez, al terminar. Después solo se lee.
"""
import csv
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

MAX_FILAS_TABLA = 200     # filas que se muestran en la tabla de la ventana
TAM_BLOQUE = 50           # cada cuántas ventas se avisa el progreso

# Solo para DEMOSTRACIONES: segundos que el hilo "descansa" tras cada bloque.
# Con 0 va a toda velocidad (500 ventas se leen en ~3 ms, demasiado rápido para
# capturar la pantalla). Para evidencias pon 0.2: con 500 ventas y bloques de 50
# la carga dura ~2 s y la barra avanza de 10 % en 10 %.
PAUSA_DEMO_SEGUNDOS = 0.0

# Evita que dos hilos escriban un reporte al mismo tiempo.
lock_reportes = threading.Lock()


@dataclass
class ResumenVentas:
    """Datos de ventas ya preparados para consultar y para generar reportes."""
    fecha_filtro: str = ""
    ventas: int = 0
    ingreso_total: float = 0.0
    por_metodo: dict = field(default_factory=dict)    # metodo -> {ventas, total}
    por_producto: dict = field(default_factory=dict)  # producto -> {unidades, ingreso}
    por_dia: dict = field(default_factory=dict)       # AAAA-MM-DD -> {ventas, total}
    ultimas: list = field(default_factory=list)       # últimas ventas (para la tabla)
    lineas_invalidas: int = 0
    segundos: float = 0.0
    generado: str = ""

    @property
    def ticket_promedio(self):
        return self.ingreso_total / self.ventas if self.ventas else 0.0

    def producto_mas_vendido(self):
        """Devuelve (nombre, unidades) o None si no hay ventas."""
        if not self.por_producto:
            return None
        nombre, datos = max(self.por_producto.items(), key=lambda kv: kv[1]["unidades"])
        return nombre, datos["unidades"]


# ======================================================================
# RUNNABLE 1: leer el archivo masivo y preparar el resumen
# ======================================================================
class TareaCargarVentas:
    """Runnable: lee el archivo de ventas y calcula el resumen."""

    def __init__(self, repositorio, cola, cancelar, fecha_filtro="", tam_bloque=TAM_BLOQUE):
        self.repo = repositorio
        self.cola = cola
        self.cancelar = cancelar              # threading.Event: "por favor, detente"
        self.fecha_filtro = fecha_filtro      # prefijo: "2026", "2026-10" o "2026-10-18"
        self.tam_bloque = tam_bloque

    def _avisar(self, tipo, **datos):
        self.cola.put({"tarea": "carga", "tipo": tipo, **datos})

    def run(self):
        inicio = time.perf_counter()
        try:
            # Foto del tamaño: solo se leerá hasta aquí (ver repositorio_ventas)
            limite = self.repo.tamano_actual()
            resumen = ResumenVentas(fecha_filtro=self.fecha_filtro)
            ultimas = deque(maxlen=MAX_FILAS_TABLA)
            leidas = 0

            for venta, bytes_leidos in self.repo.iterar(limite):
                leidas += 1

                if venta is None:
                    resumen.lineas_invalidas += 1
                else:
                    try:
                        if self._acumular(resumen, venta):
                            ultimas.append(venta)
                    except (KeyError, TypeError, ValueError, AttributeError):
                        resumen.lineas_invalidas += 1   # línea con formato inesperado

                if leidas % self.tam_bloque == 0:
                    if self.cancelar.is_set():
                        self._avisar("cancelado")
                        return
                    porcentaje = min(100.0, bytes_leidos * 100 / limite) if limite else 100.0
                    self._avisar("progreso", porcentaje=porcentaje, leidas=leidas)
                    if PAUSA_DEMO_SEGUNDOS:
                        time.sleep(PAUSA_DEMO_SEGUNDOS)

            resumen.ultimas = list(ultimas)
            resumen.segundos = time.perf_counter() - inicio
            resumen.generado = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._avisar("terminado", resumen=resumen, leidas=leidas)

        except OSError as e:
            self._avisar("error", mensaje=f"No se pudo leer el archivo de ventas: {e.strerror or e}")
        except Exception as e:  # último recurso: que el hilo nunca muera en silencio
            self._avisar("error", mensaje=f"Error inesperado al procesar las ventas: {e}")

    def _acumular(self, resumen, venta):
        """Suma una venta al resumen. Devuelve False si el filtro de fecha la excluye.

        Primero valida y convierte TODO; solo después modifica el resumen, así
        una línea dañada nunca lo deja a medio actualizar.
        """
        fecha = str(venta["fecha"])
        if not fecha.startswith(self.fecha_filtro):
            return False

        total = float(venta["total"])
        metodo = str(venta["metodo_pago"])
        articulos = [
            (str(a["producto"]), int(a["cantidad"]), float(a["subtotal"]))
            for a in venta["articulos"]
        ]

        resumen.ventas += 1
        resumen.ingreso_total += total

        m = resumen.por_metodo.setdefault(metodo, {"ventas": 0, "total": 0.0})
        m["ventas"] += 1
        m["total"] += total

        d = resumen.por_dia.setdefault(fecha[:10], {"ventas": 0, "total": 0.0})
        d["ventas"] += 1
        d["total"] += total

        for producto, cantidad, subtotal in articulos:
            p = resumen.por_producto.setdefault(producto, {"unidades": 0, "ingreso": 0.0})
            p["unidades"] += cantidad
            p["ingreso"] += subtotal
        return True


# ======================================================================
# RUNNABLE 2: guardar el reporte en disco
# ======================================================================
class TareaExportarReporte:
    """Runnable: escribe el resumen ya preparado en un archivo CSV."""

    def __init__(self, resumen, carpeta, cola):
        self.resumen = resumen    # solo se LEE; nadie lo modifica después de publicarse
        self.carpeta = carpeta
        self.cola = cola

    def _avisar(self, tipo, **datos):
        self.cola.put({"tarea": "export", "tipo": tipo, **datos})

    def run(self):
        ruta = ""
        temporal = ""
        try:
            nombre = f"reporte_ventas_{datetime.now():%Y%m%d_%H%M%S}.csv"
            ruta = os.path.join(self.carpeta, nombre)
            temporal = ruta + ".tmp"

            # Un solo hilo a la vez escribe reportes
            with lock_reportes:
                os.makedirs(self.carpeta, exist_ok=True)
                with open(temporal, "w", newline="", encoding="utf-8-sig") as f:
                    self._escribir(csv.writer(f))
                # Se escribe a un temporal y se renombra al final: nunca queda
                # un reporte a medias aunque falle algo en medio.
                os.replace(temporal, ruta)

            self._avisar("terminado", ruta=ruta)

        except FileNotFoundError:
            self._limpiar(temporal)
            self._avisar("error", mensaje=(
                f"La ubicación '{self.carpeta}' no está disponible o no existe.\n"
                "Elige otra carpeta e inténtalo de nuevo."))
        except PermissionError:
            self._limpiar(temporal)
            self._avisar("error", mensaje=(
                f"No hay permisos para guardar en '{self.carpeta}', "
                "o el archivo está abierto en otro programa."))
        except OSError as e:
            self._limpiar(temporal)
            self._avisar("error", mensaje=f"No se pudo guardar el reporte: {e.strerror or e}")
        except Exception as e:
            self._limpiar(temporal)
            self._avisar("error", mensaje=f"Error inesperado al generar el reporte: {e}")

    @staticmethod
    def _limpiar(temporal):
        try:
            if temporal and os.path.exists(temporal):
                os.remove(temporal)
        except OSError:
            pass

    def _escribir(self, w):
        r = self.resumen
        w.writerow(["REPORTE DE VENTAS - DULCERÍA"])
        w.writerow(["Generado", r.generado])
        w.writerow(["Filtro de fecha", r.fecha_filtro or "(todas)"])
        w.writerow(["Ventas registradas", r.ventas])
        w.writerow(["Total vendido", f"{r.ingreso_total:.2f}"])
        w.writerow(["Ticket promedio", f"{r.ticket_promedio:.2f}"])
        if r.lineas_invalidas:
            w.writerow(["Líneas ignoradas por formato inválido", r.lineas_invalidas])

        w.writerow([])
        w.writerow(["VENTAS POR MÉTODO DE PAGO"])
        w.writerow(["Método", "Ventas", "Total"])
        for metodo, d in sorted(r.por_metodo.items(), key=lambda kv: -kv[1]["total"]):
            w.writerow([metodo, d["ventas"], f"{d['total']:.2f}"])

        w.writerow([])
        w.writerow(["PRODUCTOS (de mayor a menor ingreso)"])
        w.writerow(["Producto", "Unidades", "Ingreso"])
        for producto, d in sorted(r.por_producto.items(), key=lambda kv: -kv[1]["ingreso"]):
            w.writerow([producto, d["unidades"], f"{d['ingreso']:.2f}"])

        w.writerow([])
        w.writerow(["VENTAS POR DÍA"])
        w.writerow(["Fecha", "Ventas", "Total"])
        for dia, d in sorted(r.por_dia.items()):
            w.writerow([dia, d["ventas"], f"{d['total']:.2f}"])
