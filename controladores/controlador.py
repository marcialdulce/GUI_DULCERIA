import os
import queue
import threading
from tkinter import messagebox, simpledialog
from datetime import datetime
from modelos.modelo import ModeloDulceria
from servicios.repositorio_ventas import RepositorioVentas
from servicios.tareas_ventas import TareaCargarVentas, TareaExportarReporte

class ControladorDulceria:
    def __init__(self):
        self.modelo = ModeloDulceria()
        self.repo_ventas = RepositorioVentas()
        
        self.usuario_actual = None
        self.id_usuario_actual = None
        self.rol_actual = None
        self.inicio_sesion = None
        self.id_turno_actual = None
        self.vista = None
        
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
            
            self.vista.mostrar_alerta("Inicio de sesión", f"¡Bienvenido/a, {usuario}!", "info")
            self.vista.pantallas["PantallaLogin"].entry_usuario.delete(0, "end")
            self.vista.pantallas["PantallaLogin"].entry_pass.delete(0, "end")

            if self.rol_actual == "Cajero":
                opciones = ["PUNTO DE VENTA", "COBROS Y PAGOS", "TICKETS", "HISTORIAL DE VENTAS", "CIERRE DE CAJA"]
                self.id_turno_actual = self.modelo.abrir_turno(self.id_usuario_actual, id_caja=1)
            else:
                opciones = ["INICIO", "NUEVA VENTA", "COBROS Y PAGOS", "INVENTARIO", "APARTADOS", "PROVEEDORES", "HISTORIAL"]

            self.vista.pantallas["MenuPrincipal"].configurar_acceso(usuario, self.rol_actual, opciones)
            self.vista.mostrar_pantalla("MenuPrincipal")
        else:
            self.vista.mostrar_alerta("Datos incorrectos", "Las claves de acceso no son correctas.", "error")
            self.vista.pantallas["PantallaLogin"].entry_pass.delete(0, "end")

    # ---------------- PRODUCTOS / INVENTARIO ----------------
    def procesar_eliminar_producto(self, nombre_producto):
        if self.rol_actual != "Administrador":
            return False, "No tienes permisos."
        if self.modelo.eliminar_producto(nombre_producto):
            return True, f"Producto '{nombre_producto}' eliminado."
        return False, "Error al eliminar."

    def obtener_inventario_filtrado(self, texto, marca, categoria):
        return self.modelo.obtener_inventario_filtrado(texto, marca, categoria)

    def obtener_pedidos_activos(self):
        return self.modelo.obtener_pedidos_activos()

    def recibir_pedido(self, id_pedido):
        return self.modelo.recibir_pedido_proveedor(id_pedido)

    def cancelar_pedido(self, id_pedido):
        return self.modelo.cancelar_pedido_proveedor(id_pedido)

    # ---------------- PROVEEDORES ----------------
    def obtener_proveedores(self):
        return self.modelo.obtener_proveedores()

    def procesar_nuevo_proveedor(self, nombre, telefono, correo):
        if self.rol_actual != "Administrador": return False, "Acceso denegado."
        resultado = self.modelo.agregar_proveedor(nombre, telefono, correo)
        if resultado == "nombre_vacio": return False, "El nombre no puede estar vacío."
        if resultado == "ya_existe": return False, f"Ya existe '{nombre}'."
        return True, f"Proveedor '{nombre}' agregado."

    def procesar_eliminar_proveedor(self, proveedor_id):
        if self.rol_actual != "Administrador": return False
        self.modelo.eliminar_proveedor(proveedor_id)
        return True

    # ---------------- APARTADOS ----------------
    def obtener_lista_apartados(self):
        return self.modelo.obtener_apartados()

    def obtener_nombres_productos(self):
        return self.modelo.obtener_nombres_productos()

    def registrar_apartado(self, nombre, telefono, fecha, prod_nombre, cant_str, metodo_texto):
        try:
            cant = int(cant_str)
            if cant <= 0: raise ValueError
        except ValueError:
            return False, "La cantidad debe ser un número entero positivo."
            
        return self.modelo.registrar_apartado(nombre, telefono, fecha, prod_nombre, cant, metodo_texto, self.id_turno_actual)

    def cancelar_apartado(self, id_apartado):
        return self.modelo.cancelar_apartado(id_apartado)

    # ---------------- COBROS Y VENTAS ----------------
    def procesar_cobro_avanzado(self, pagos, datos_factura):
        if not self.modelo.ticket_actual:
            messagebox.showwarning("Aviso", "El ticket está vacío.")
            return False

        total = self.modelo.calcular_total()
        total_pagado = sum(p["monto"] for p in pagos)
        
        if total_pagado < total:
            messagebox.showwarning("Pago insuficiente", f"El total es ${total:.2f}, ingresaste ${total_pagado:.2f}.")
            return False

        carrito_respaldo = [dict(i) for i in self.modelo.ticket_actual]
        
        try:
            self.repo_ventas.registrar(
                articulos=carrito_respaldo,
                pagos=pagos,
                id_corte_caja=self.id_turno_actual,
                datos_factura=datos_factura
            )
            self.modelo.ticket_actual.clear()
            
            cambio = total_pagado - total
            mensaje = f"¡Venta procesada con éxito!\nTotal: ${total:.2f}\n"
            if cambio > 0:
                mensaje += f"Cambio a entregar: ${cambio:.2f}"
            
            messagebox.showinfo("Ticket Cobrado", mensaje)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la venta: {e}")
            return False

    def procesar_agregar(self, nombre_producto):
        cantidad = simpledialog.askinteger("Cantidad", f"¿Cuántos '{nombre_producto}' deseas agregar?")
        if cantidad and cantidad > 0:
            resultado = self.modelo.agregar_al_ticket(nombre_producto, cantidad)
            if resultado == "stock_insuficiente": messagebox.showerror("Error", "No hay suficiente stock.")
            elif resultado == "no_encontrado": messagebox.showerror("Error", "Producto no encontrado.")

    def obtener_datos_ventas(self):
        return self.modelo.inventario, self.modelo.ticket_actual, self.modelo.calcular_total()

    def vaciar_ticket_actual(self):
        self.modelo.ticket_actual.clear()

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
        if self.resumen_ventas is None: return False, "Primero carga las ventas."
        if self.estado_export["estado"] == "guardando": return False, "Ya se está guardando."
        carpeta = (carpeta or "").strip() or "reportes"
        tarea = TareaExportarReporte(self.resumen_ventas, carpeta, self.cola_tareas)
        self.hilo_export = threading.Thread(target=tarea.run, name="HiloExportarReporte", daemon=True)
        self.estado_export = {"estado": "guardando", "ruta": ""}
        self.hilo_export.start()
        return True, ""

    def hay_tareas_activas(self):
        return self.estado_carga["estado"] in ("cargando", "cancelando") or self.estado_export["estado"] == "guardando"

    def sondear_tareas(self):
        while True:
            try: msg = self.cola_tareas.get_nowait()
            except queue.Empty: return
            self._aplicar_mensaje(msg)

    def _aplicar_mensaje(self, msg):
        tipo = msg["tipo"]
        if msg["tarea"] == "carga":
            e = self.estado_carga
            if tipo == "progreso": e["porcentaje"], e["leidas"] = msg["porcentaje"], msg["leidas"]
            elif tipo == "terminado": self.resumen_ventas = msg["resumen"]; e.update(estado="terminado", porcentaje=100.0, leidas=msg["leidas"])
            elif tipo == "cancelado": e["estado"] = "cancelado"
            elif tipo == "error": e.update(estado="error", mensaje=msg["mensaje"]); self._notificaciones.append(("error", "Error al cargar", msg["mensaje"]))
        else:
            if tipo == "terminado": self.estado_export = {"estado": "terminado", "ruta": msg["ruta"]}; self._notificaciones.append(("info", "Reporte generado", f"Guardado en:\n{os.path.abspath(msg['ruta'])}"))
            elif tipo == "error": self.estado_export = {"estado": "error", "ruta": ""}; self._notificaciones.append(("error", "Error al guardar", msg["mensaje"]))

    def tomar_notificaciones(self):
        pendientes, self._notificaciones = self._notificaciones, []
        return pendientes

    # ---------------- CIERRE DE CAJA ----------------
    def obtener_resumen_cierre_caja(self):
        fin = datetime.now()
        inicio = self.inicio_sesion or fin
        duracion = fin - inicio
        segundos = max(0, int(duracion.total_seconds()))
        horas, resto = divmod(segundos, 3600)
        minutos, segundos = divmod(resto, 60)

        efectivo_esperado = self.repo_ventas.efectivo_turno(self.id_turno_actual) if self.id_turno_actual else 0.0

        return {
            "usuario": self.usuario_actual or "",
            "inicio": inicio.strftime("%d/%m/%Y %H:%M:%S"),
            "fin": fin.strftime("%d/%m/%Y %H:%M:%S"),
            "duracion": f"{horas:02d}h {minutos:02d}m {segundos:02d}s",
            "efectivo_esperado": efectivo_esperado 
        }

    def cerrar_sesion(self, efectivo_fisico=None):
        if efectivo_fisico is not None and self.id_turno_actual:
            self.modelo.cerrar_turno(self.id_turno_actual, efectivo_fisico)
            self.id_turno_actual = None

        self.modelo.ticket_actual.clear()
        self.usuario_actual = None
        self.rol_actual = None
        self.vista.pantallas["MenuPrincipal"].configurar_acceso("", None, [])
        self.vista.mostrar_pantalla("PantallaLogin")
        self.vista.pantallas["PantallaLogin"].entry_usuario.delete(0, "end")
        self.vista.pantallas["PantallaLogin"].entry_pass.delete(0, "end")