import os
import queue
import threading
from tkinter import messagebox, simpledialog
from datetime import datetime
from reportlab.pdfgen import canvas
from modelos.modelo import ModeloDulceria
from servicios.repositorio_ventas import RepositorioVentas
from servicios.repositorio_apartados import RepositorioApartados
from servicios.repositorio_pedidos import RepositorioPedidos
from servicios.tareas_ventas import TareaCargarVentas, TareaExportarReporte

class ControladorDulceria:
    def __init__(self):
        self.modelo = ModeloDulceria()
        self.repo_ventas = RepositorioVentas()
        self.repo_apartados = RepositorioApartados()
        self.repo_pedidos = RepositorioPedidos()
        self.usuario_actual = None
        self.id_usuario_actual = None
        self.rol_actual = None
        self.inicio_sesion = None
        self.id_turno_actual = None
        self.vista = None

        # --- Variables para el Historial ---
        self.cola_tareas = queue.Queue()
        self.hilo_carga = None
        self.hilo_export = None
        self._cancelar_carga = threading.Event()
        self.resumen_ventas = None
        self.estado_carga = {"estado": "inactivo", "porcentaje": 0.0, "leidas": 0, "mensaje": ""}
        self.estado_export = {"estado": "inactivo", "ruta": ""}
        self._notificaciones = []

    def procesar_login(self, usuario, password):
        user_data = self.modelo.validar_usuario(usuario, password)
        if user_data:
            self.usuario_actual = usuario
            self.id_usuario_actual = user_data["id_usuario"]
            self.rol_actual = self.modelo.obtener_rol(user_data["id_rol"])
            self.inicio_sesion = datetime.now()
            
            self.vista.pantallas["PantallaLogin"].entry_usuario.delete(0, "end")
            self.vista.pantallas["PantallaLogin"].entry_pass.delete(0, "end")

            if self.rol_actual == "Cajero":
                # REGLA 7: Selección de Caja
                num_caja = simpledialog.askinteger("Abrir Caja", "¿En qué número de caja vas a trabajar? (1-4)", minvalue=1, maxvalue=4)
                if not num_caja:
                    messagebox.showwarning("Cancelado", "Debes seleccionar una caja para iniciar.")
                    return
                
                self.id_turno_actual = self.modelo._ejecutar_consulta(
                    "INSERT INTO cortes_caja (fondo_inicial, id_usuario, id_caja) VALUES (500.00, %s, %s)", 
                    (self.id_usuario_actual, num_caja)
                )
                opciones = ["PUNTO DE VENTA", "COBROS Y PAGOS", "TICKETS", "HISTORIAL DE VENTAS", "CIERRE DE CAJA"]
            else:
                opciones = ["INICIO", "NUEVA VENTA", "REPORTES", "COBROS Y PAGOS", "INVENTARIO", "APARTADOS", "PROVEEDORES", "HISTORIAL"]

            messagebox.showinfo("Bienvenido", f"Sesión iniciada como {usuario} ({self.rol_actual})")
            self.vista.pantallas["MenuPrincipal"].configurar_acceso(usuario, self.rol_actual, opciones)
            self.vista.mostrar_pantalla("MenuPrincipal")
        else:
            self.vista.mostrar_alerta("Datos incorrectos", "Las claves son incorrectas.", "error")

    # ---------------- HISTORIAL (HILOS) ----------------
    def iniciar_carga_ventas(self, fecha_filtro=""):
        if self.estado_carga["estado"] in ("cargando", "cancelando"): return False
        self._cancelar_carga = threading.Event()
        filtro_usuario = self.usuario_actual if self.rol_actual == "Cajero" else None
        
        tarea = TareaCargarVentas(self.repo_ventas, self.cola_tareas, self._cancelar_carga, fecha_filtro, usuario_filtro=filtro_usuario)
        self.hilo_carga = threading.Thread(target=tarea.run, name="HiloCargaVentas", daemon=True)
        self.estado_carga = {"estado": "cargando", "porcentaje": 0.0, "leidas": 0, "mensaje": ""}
        self.hilo_carga.start()
        return True

    def cancelar_carga_ventas(self):
        if self.estado_carga["estado"] == "cargando":
            self.estado_carga["estado"] = "cancelando"
            self._cancelar_carga.set()

    def exportar_reporte(self, carpeta):
        if self.resumen_ventas is None:
            return (
                False,
                "Primero carga las ventas (botón BUSCAR) para tener datos que"
                " exportar.",
            )
        if self.estado_export["estado"] == "guardando":
            return False, "Ya se está guardando un reporte. Espera a que termine."

        carpeta = (carpeta or "").strip() or "reportes"
        tarea = TareaExportarReporte(self.resumen_ventas, carpeta, self.cola_tareas)
        self.hilo_export = threading.Thread(
            target=tarea.run, name="HiloExportarReporte", daemon=True
        )
        self.estado_export = {"estado": "guardando", "ruta": ""}
        self.hilo_export.start()
        return True, ""

    def hay_tareas_activas(self):
        return self.estado_carga["estado"] in (
            "cargando",
            "cancelando",
        ) or self.estado_export["estado"] == "guardando"

    def sondear_tareas(self):
        while True:
            try:
                msg = self.cola_tareas.get_nowait()
            except queue.Empty:
                return
            self._aplicar_mensaje(msg)

    def _aplicar_mensaje(self, msg):
        tipo = msg["tipo"]
        if msg["tarea"] == "carga":
            e = self.estado_carga
            if tipo == "progreso":
                e["porcentaje"], e["leidas"] = msg["porcentaje"], msg["leidas"]
            elif tipo == "terminado":
                self.resumen_ventas = msg["resumen"]
                e.update(estado="terminado", porcentaje=100.0, leidas=msg["leidas"])
            elif tipo == "cancelado":
                e["estado"] = "cancelado"
            elif tipo == "error":
                e.update(estado="error", mensaje=msg["mensaje"])
                self._notificaciones.append(
                    ("error", "Error al cargar ventas", msg["mensaje"])
                )
        else:
            if tipo == "terminado":
                self.estado_export = {"estado": "terminado", "ruta": msg["ruta"]}
                self._notificaciones.append((
                    "info",
                    "Reporte generado",
                    "El reporte se guardó"
                    f" en:\n{os.path.abspath(msg['ruta'])}",
                ))
            elif tipo == "error":
                self.estado_export = {"estado": "error", "ruta": ""}
                self._notificaciones.append(
                    ("error", "No se pudo guardar el reporte", msg["mensaje"])
                )

    def tomar_notificaciones(self):
        pendientes, self._notificaciones = self._notificaciones, []
        return pendientes

    # ---------------- OTROS MÉTODOS ----------------
    def obtener_reporte_ganancias(self):
        return self.modelo.obtener_reporte_ganancias()

    def registrar_merma(self, id_producto, cantidad, motivo):
        return self.modelo.registrar_merma(id_producto, cantidad, motivo)

    def obtener_inventario_filtrado(self, texto, marca, categoria):
        productos = self.modelo.inventario
        filtrados = []
        texto_busqueda = (texto or "").strip().lower()

        for p in productos:
            nombre_prod = p["nombre"].lower()
            marca_prod = p["marca"].lower()
            
            # Buscar si el texto está INCLUIDO en el nombre o en la marca (no requiere coincidencia exacta)
            if texto_busqueda and (texto_busqueda not in nombre_prod and texto_busqueda not in marca_prod):
                continue
                
            if marca != "Todas" and p["marca"] != marca: 
                continue
            if categoria != "Todas" and p["categoria"] != categoria: 
                continue
                
            filtrados.append(p)
            
        return filtrados
    
    def obtener_proveedores(self):
        return self.modelo.obtener_proveedores()

    def obtener_productos_proveedor(self, id_proveedor):
        return self.modelo.obtener_productos_proveedor(id_proveedor)

    def crear_pedido_manual(self, id_proveedor, articulos):
        return self.repo_pedidos.crear_pedido_manual(id_proveedor, self.id_usuario_actual, articulos)

    def obtener_pedidos_activos(self):
        return self.modelo.obtener_pedidos_activos()

    def recibir_pedido(self, id_pedido):
        return self.modelo.recibir_pedido_proveedor(id_pedido)

    def obtener_lista_apartados(self):
        return self.modelo.obtener_apartados()

    def registrar_apartado(self, nombre, telefono, fecha, articulos, pagos):
        try:
            self.repo_apartados.registrar_apartado(nombre, telefono, fecha, articulos, self.id_turno_actual, pagos)
            return True, "Apartado registrado con éxito."
        except Exception as e:
            return False, str(e)

    def liquidar_apartado(self, id_apartado, pagos):
        return self.repo_apartados.liquidar_apartado(id_apartado, pagos, self.id_turno_actual)

    def cancelar_apartado(self, id_apartado):
        self.modelo._ejecutar_consulta("UPDATE apartados SET estado='cancelado' WHERE id_apartado=%s", (id_apartado,))
        return True

    def procesar_cobro_avanzado(self, pagos, datos_factura):
        if not self.modelo.ticket_actual: return False, "Carrito vacío"
        total = self.modelo.calcular_total()
        total_pagado = sum(p["monto"] for p in pagos)
        if total_pagado < total: return False, f"Faltan ${total - total_pagado:.2f}"

        try:
            self.repo_ventas.registrar(self.modelo.ticket_actual, pagos, self.id_turno_actual, datos_factura)
            self.modelo.ticket_actual.clear()
            return True, f"Venta exitosa. Cambio: ${total_pagado - total:.2f}"
        except Exception as e:
            return False, str(e)

    def obtener_datos_ventas(self):
        return self.modelo.inventario, self.modelo.ticket_actual, self.modelo.calcular_total()

    def obtener_nombres_productos(self):
        return [p["nombre"] for p in self.modelo.inventario]

    def vaciar_ticket_actual(self):
        self.modelo.ticket_actual.clear()
        
    def eliminar_proveedor(self, id_proveedor):
        return self.modelo.eliminar_proveedor(id_proveedor)

    def obtener_resumen_cierre_caja(self):
        fin = datetime.now()
        inicio = self.inicio_sesion or fin
        duracion = fin - inicio
        segundos = max(0, int(duracion.total_seconds()))
        horas, resto = divmod(segundos, 3600)
        minutos, segundos = divmod(resto, 60)
        efectivo = self.repo_ventas.efectivo_turno(self.id_turno_actual) if self.id_turno_actual else 0.0
        return {
            "usuario": self.usuario_actual or "", "inicio": inicio.strftime("%d/%m/%Y %H:%M:%S"),
            "fin": fin.strftime("%d/%m/%Y %H:%M:%S"), "duracion": f"{horas:02d}h {minutos:02d}m {segundos:02d}s",
            "efectivo_esperado": efectivo 
        }
        
    def procesar_agregar(self, producto_diccionario, cantidad):
        """Pide al modelo que meta el producto al ticket con la cantidad especificada."""
        res = self.modelo.agregar_al_ticket(producto_diccionario["nombre"], cantidad)
        
        if res == "stock_insuficiente":
            from tkinter import messagebox
            messagebox.showwarning("Sin stock", f"No hay existencias suficientes de {producto_diccionario['nombre']}.")
            return False
        return True
    
    def cerrar_sesion(self, efectivo_fisico=None):
        if efectivo_fisico is not None and self.id_turno_actual:
            self.modelo._ejecutar_consulta("UPDATE cortes_caja SET fecha_hora_fin=NOW(), efectivo_contado=%s, estado='cerrado' WHERE id_corte_caja=%s", (efectivo_fisico, self.id_turno_actual))
        self.modelo.ticket_actual.clear()
        self.usuario_actual = None
        self.vista.pantallas["MenuPrincipal"].configurar_acceso("", None, [])
        self.vista.mostrar_pantalla("PantallaLogin")
        self.vista.pantallas["PantallaLogin"].entry_usuario.delete(0, "end")
        self.vista.pantallas["PantallaLogin"].entry_pass.delete(0, "end")