"""
Acceso al archivo de ventas (formato JSON Lines: una venta por línea).

Se ubica en la capa de servicios porque es infraestructura de persistencia.
Lo comparten dos "mundos" que corren en paralelo:

  * El hilo principal (Tkinter), que REGISTRA una venta cada vez que se cobra.
  * El hilo de segundo plano (TareaCargarVentas), que LEE todo el archivo.

Cómo se evita que se pisen (ver también docs/HILOS_VENTAS.md):

  1. El archivo es "append-only": solo se agregan líneas al final, nunca se
     modifican las anteriores.
  2. Toda escritura y la lectura del tamaño del archivo pasan por el mismo
     Lock, de modo que una línea nunca se ve a medias.
  3. El lector toma una "foto" del tamaño del archivo al empezar y solo lee
     hasta ese byte. Lo que se agregue después se ignora (se verá en la
     siguiente carga). Así el lector NO necesita retener el Lock mientras
     procesa, y el cobro nunca se queda esperando a una lectura larga.
"""
import json
import os
import threading
import uuid
from datetime import datetime

RUTA_VENTAS = os.path.join("datos", "ventas.jsonl")
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


class RepositorioVentas:

    def __init__(self, ruta=RUTA_VENTAS):
        self.ruta = ruta
        self._lock = threading.Lock()

    # ---------------------------------------------------------- escritura
    def registrar(self, metodo_pago, total, articulos, facturado=False):
        """Agrega UNA venta al final del archivo y la devuelve."""
        venta = {
            "folio": "V-" + uuid.uuid4().hex[:8].upper(),
            "fecha": datetime.now().strftime(FORMATO_FECHA),
            "metodo_pago": metodo_pago,
            "facturado": bool(facturado),
            "total": round(float(total), 2),
            "articulos": [
                {
                    "producto": a["producto"],
                    "cantidad": int(a["cantidad"]),
                    "subtotal": round(float(a["subtotal"]), 2),
                }
                for a in articulos
            ],
        }
        self.registrar_lote([venta])
        return venta

    def registrar_lote(self, ventas):
        """Agrega varias ventas con UN solo acceso al archivo (usado por el
        generador de datos de prueba)."""
        texto = "".join(json.dumps(v, ensure_ascii=False) + "\n" for v in ventas)
        with self._lock:
            carpeta = os.path.dirname(self.ruta)
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)
            with open(self.ruta, "ab") as f:
                f.write(texto.encode("utf-8"))

    # ------------------------------------------------------------ lectura
    def tamano_actual(self):
        """Foto del tamaño del archivo en bytes (0 si aún no existe)."""
        with self._lock:
            try:
                return os.path.getsize(self.ruta)
            except FileNotFoundError:
                return 0

    def iterar(self, limite_bytes):
        """Recorre el archivo línea por línea SIN cargarlo completo en memoria.

        Produce tuplas (venta | None, bytes_leidos). Devuelve None en la venta
        cuando la línea no es un JSON válido. Se detiene al llegar a
        `limite_bytes` (la foto tomada con tamano_actual()).
        """
        try:
            archivo = open(self.ruta, "rb")
        except FileNotFoundError:
            return  # todavía no hay ventas registradas

        leidos = 0
        with archivo:
            for linea in archivo:
                leidos += len(linea)
                if leidos > limite_bytes:
                    break  # lo agregado después de la foto no se toca
                if not linea.strip():
                    continue
                try:
                    venta = json.loads(linea)
                except ValueError:
                    venta = None
                yield venta, leidos
