import os
import queue
import threading
from tkinter import filedialog
from tkinter import messagebox, simpledialog
from datetime import datetime
from modelos.modelo import ModeloDulceria
from servicios.hilo_factura import HiloFactura
from servicios.repositorio_ventas import RepositorioVentas
from servicios.tareas_ventas import TareaCargarVentas, TareaExportarReporte
from vistas.ventana_principal import VistaDulceria


class ControladorDulceria:

    def __init__(self):
        self.modelo = ModeloDulceria()
        self.usuario_actual = None
        self.rol_actual = None
        self.inicio_sesion = None

        self.pedidos_activos = []
        self.repo_ventas = RepositorioVentas()
        self.cola_tareas = queue.Queue()
        self.hilo_carga = None
        self.hilo_export = None
        self._cancelar_carga = threading.Event()
        self.resumen_ventas = None
        self.estado_carga = {"estado": "inactivo", "porcentaje": 0.0, "leidas": 0, "mensaje": ""}
        self.estado_export = {"estado": "inactivo", "ruta": ""}
        self._notificaciones = []

    def iniciar(self):
        self.vista.mainloop()

    def procesar_login(self, usuario, password):
        es_valido = self.modelo.validar_usuario(usuario, password)

        if es_valido:
            self.usuario_actual = usuario
            self.rol_actual = self.modelo.obtener_rol(usuario)
            self.inicio_sesion = datetime.now()
            
            self.vista.mostrar_alerta("Inicio de sesión", f"¡Bienvenido/a, {usuario}!", "info")
            self.vista.pantallas["PantallaLogin"].entry_usuario.delete(0, "end")
            self.vista.pantallas["PantallaLogin"].entry_pass.delete(0, "end")

            # El controlador decide las opciones
            if self.rol_actual == "Cajero":
                opciones = ["PUNTO DE VENTA", "COBROS Y PAGOS", "TICKETS", "HISTORIAL DE VENTAS",  "CIERRE DE CAJA"]
            else:
                opciones = ["INICIO", "NUEVA VENTA", "INVENTARIO", "APARTADOS", "PROVEEDORES", "HISTORIAL"]

            self.vista.pantallas["MenuPrincipal"].configurar_acceso(usuario, self.rol_actual, opciones)
            self.vista.mostrar_pantalla("MenuPrincipal")
        else:
            self.vista.mostrar_alerta("Datos incorrectos", "Las claves de acceso o los datos ingresados no son correctos.\nPor favor, intente nuevamente.", "error")
            self.vista.pantallas["PantallaLogin"].entry_pass.delete(0, "end")
            
        # Abrimos el turno en la BD
        self.id_turno_actual = self.modelo.abrir_turno(usuario)

    def procesar_cobro_avanzado(self, tipo_pago, datos_factura):
        total = self.modelo.calcular_total()
        if total == 0:
            messagebox.showwarning("Aviso", "El ticket está vacío. Agrega productos primero.")
            return

        pago = self._solicitar_pago(total, tipo_pago)
        if pago is None: 
            return

        carrito_respaldo = self.modelo.ticket_actual.copy()
        exito, cambio = self.modelo.procesar_cobro(pago)
        
        if exito:
            aviso_historial = self._registrar_venta_historial(tipo_pago, total, carrito_respaldo, datos_factura)

            mensaje = f"¡Venta procesada con éxito!\n\nMétodo de pago: {tipo_pago}\n"
            if tipo_pago == "Efectivo":
                mensaje += f"Cambio a entregar: ${cambio:.2f}\n"
            
            if datos_factura and datos_factura.get("requiere"):
                # Si se genera factura, el método nos devuelve el texto extra
                mensaje += self._iniciar_hilo_factura(datos_factura, total, carrito_respaldo, tipo_pago, pago, cambio)

            messagebox.showinfo("Ticket Cobrado", mensaje + aviso_historial)

    def _solicitar_pago(self, total, tipo_pago):
        """Extrae la lógica de pedir el pago en efectivo."""
        if tipo_pago == "Efectivo":
            pago = simpledialog.askfloat("Cobrar en Efectivo", f"Total a cobrar: ${total:.2f}\n¿Con cuánto efectivo paga el cliente?")
            return pago
        return total

    def _registrar_venta_historial(self, tipo_pago, total, carrito, datos_factura):
        """Extrae la lógica de guardar en el archivo JSON."""
        try:
            self.repo_ventas.registrar(
                metodo_pago=tipo_pago,
                total=total,
                articulos=carrito,
                facturado=bool(datos_factura and datos_factura.get("requiere")),
            )
            return ""
        except OSError as e:
            return f"\n\nAviso: la venta no se pudo guardar en el historial ({e.strerror or e})."

    def _iniciar_hilo_factura(self, datos_factura, total, carrito, tipo_pago, pago, cambio):
        """Extrae la lógica de la ventana de guardado y la creación del Hilo."""
        nombre_archivo = f"Factura_{datos_factura['rfc']}.pdf"
        razon_social = f"{datos_factura.get('nombre','')} {datos_factura.get('apellidos','')}".strip()

        from tkinter import filedialog
        ruta_completa_pdf = filedialog.asksaveasfilename(
            title="Guardar Factura",
            defaultextension=".pdf",
            initialfile=nombre_archivo,
            filetypes=[("Archivos PDF", "*.pdf")]
        )

        if not ruta_completa_pdf:
            messagebox.showwarning("Aviso", "Se canceló el guardado de la factura.")
            return "" # Retorna vacío para que no añada texto al mensaje

        self.hilo_factura = HiloFactura(         
            ruta_completa=ruta_completa_pdf, 
            rfc=datos_factura['rfc'],
            razon_social=razon_social,
            total=total,
            carrito=carrito,
            metodo_pago=tipo_pago,
            pago=pago,
            cambio=cambio
        )
        self.hilo_factura.set_prioridad(9)
        self.hilo_factura.start()
        
        self.hilo_secundario = threading.Thread(
            target=self._tarea_notificar_fin, 
            args=(nombre_archivo, self.vista.pantallas["MenuPrincipal"].contenido.winfo_children()[0]),
            daemon=True)
        self.hilo_secundario.start()
        
        return "\n Factura generándose en segundo plano..."
      
    def _tarea_notificar_fin(self, nombre_archivo, panel_ventas):
        self.hilo_factura.join()
        if self.hilo_factura.exito:
            mensaje = f" Listo: {nombre_archivo}"
            self.vista.after(0, lambda: panel_ventas.actualizar_estado_factura(mensaje, "green"))
        elif self.hilo_factura.error:
            mensaje = " Error al generar PDF"
            self.vista.after(0, lambda: panel_ventas.actualizar_estado_factura(mensaje, "red"))
            self.vista.after(0, lambda e=self.hilo_factura.error: messagebox.showerror("Error de Facturación", f"No se pudo guardar el PDF:\n{e}"))

    # --- HILOS DE VENTAS EN SEGUNDO PLANO ---
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

    # --- MÉTODOS GENERALES ---
    def procesar_agregar(self, nombre_producto):
        cantidad = simpledialog.askinteger("Cantidad", f"¿Cuantos {nombre_producto} deseas agregar?")
        if cantidad and cantidad > 0:
            resultado = self.modelo.agregar_al_ticket(nombre_producto, cantidad)
            if resultado == "stock_insuficiente": messagebox.showerror("Error de Stock", "No existe cantidad suficiente")
            elif resultado == "no_encontrado": messagebox.showerror("Error", "Producto no encontrado")

    def procesar_eliminar_producto(self, nombre_producto):
        if self.rol_actual != "Administrador":
            return False, "No tienes permisos."
        if self.modelo.eliminar_producto(nombre_producto):
            return True, f"Producto '{nombre_producto}' eliminado."
        return False, "Error al eliminar."

    def procesar_editar_producto(self, nombre_original, nombre, marca, categoria, precio, stock):
        if self.rol_actual != "Administrador":
            return False, "Acceso denegado. Solo un Administrador puede editar productos."
            
        try:
            precio = float(precio)
            stock = int(stock)
        except (ValueError, TypeError):
            return False, "Precio y stock deben ser números válidos."
            
        if not nombre.strip():
            return False, "El nombre no puede estar vacío."

        datos = {
            "nombre": nombre.strip(),
            "marca": marca.strip() or "Genérica",
            "categoria": categoria.strip() or "General",
            "precio": precio,
            "stock": stock
        }
        
        if self.modelo.editar_producto(nombre_original, datos):
            return True, f"Producto '{nombre}' actualizado correctamente."
        return False, "Error al intentar actualizar el producto."
        
    def obtener_datos_ventas(self):
        return self.modelo.inventario, self.modelo.ticket_actual, self.modelo.calcular_total()

    def solicitar_proveedor(self, nombre_producto, stock_actual):
    # Agregamos {stock_actual} al mensaje
      mensaje = f"¿Deseas abastecer {nombre_producto}?\n\nStock actual: {stock_actual} unidades."
      
      if messagebox.askyesno("Pedido a Proveedor", mensaje):
        nuevo_id = max([p["id"] for p in self.pedidos_activos], default=0) + 1
        self.pedidos_activos.append({
            "id": nuevo_id,
            "producto": nombre_producto,
            "cantidad": 50,
            "estado": "Pendiente",
        })
        messagebox.showinfo("Éxito", f"Pedido enviado para {nombre_producto}.")

    def procesar_filtro_inventario(self, texto, marca, categoria):
        return self.modelo.obtener_inventario_filtrado(texto, marca, categoria)

    def obtener_proveedores(self):
        return self.modelo.proveedores

    def procesar_nuevo_proveedor(self, nombre, telefono, correo):
        
        if self.rol_actual != "Administrador":
            return False, "Acceso denegado. Solo un Administrador gestiona proveedores."
        
        resultado = self.modelo.agregar_proveedor(nombre, telefono, correo)
        if resultado == "nombre_vacio": return False, "El nombre no puede estar vacío."
        if resultado == "ya_existe": return False, f"Ya existe '{nombre}'."
        return True, f"Proveedor '{nombre}' agregado."
    
    def procesar_editar_proveedor(self, proveedor_id, telefono, correo):
        if self.rol_actual != "Administrador":
            return False, "No tienes permisos."
        if self.modelo.editar_proveedor(proveedor_id, telefono, correo):
            return True, "Proveedor actualizado."
        return False, "Error."

    def procesar_eliminar_proveedor(self, proveedor_id):
        if self.rol_actual != "Administrador":
            return False, "Acceso denegado."
        self.modelo.eliminar_proveedor(proveedor_id)
        return True

    def procesar_nuevo_producto(self, nombre, marca, categoria, precio, stock, proveedor_id=None):
        
        if self.rol_actual != "Administrador":
            return False, "Acceso denegado. Solo un Administrador puede crear productos."
        
        try: precio = float(precio); stock = int(stock)
        except (ValueError, TypeError): return False, "Precio y stock inválidos."
        resultado = self.modelo.agregar_producto(nombre, marca, categoria, precio, stock, proveedor_id)
        if resultado == "nombre_vacio": return False, "Nombre vacío."
        if resultado == "ya_existe": return False, f"Ya existe '{nombre}'."
        if resultado == "datos_invalidos": return False, "Precio > 0 y stock >= 0."
        return True, f"Producto '{nombre}' agregado."

    # --- MÉTODOS EXCLUSIVOS DEL CAJERO ---
    def obtener_resumen_cierre_caja(self):
        fin = datetime.now()
        inicio = self.inicio_sesion or fin
        duracion = fin - inicio
        segundos = max(0, int(duracion.total_seconds()))
        horas, resto = divmod(segundos, 3600)
        minutos, segundos = divmod(resto, 60)

        # Calculamos cuánto efectivo debería haber en caja
        ventas_turno = self.repo_ventas.obtener_todas()
        efectivo_esperado = 0.0
        
        for v in ventas_turno:
            # Verificamos si la venta se hizo en este turno (después de inicio_sesion)
            fecha_venta = datetime.strptime(v["fecha"], "%Y-%m-%d %H:%M:%S")
            if fecha_venta >= inicio and v["metodo_pago"] == "Efectivo":
                efectivo_esperado += float(v["total"])

        return {
            "usuario": self.usuario_actual or "",
            "inicio": inicio.strftime("%d/%m/%Y %H:%M:%S"),
            "fin": fin.strftime("%d/%m/%Y %H:%M:%S"),
            "duracion": f"{horas:02d} horas, {minutos:02d} minutos y {segundos:02d} segundos",
            "efectivo_esperado": efectivo_esperado 
        }

    def cerrar_sesion(self, efectivo_fisico=None):
        # Si se envió el efectivo_fisico desde el panel de cierre de caja, lo guardamos
        if efectivo_fisico is not None and hasattr(self, 'id_turno_actual') and self.id_turno_actual:
            resumen = self.obtener_resumen_cierre_caja()
            self.modelo.cerrar_turno(self.id_turno_actual, efectivo_fisico, resumen["efectivo_esperado"])
            self.id_turno_actual = None

        self.modelo.ticket_actual.clear()
        self.usuario_actual = None
        self.rol_actual = None
        self.inicio_sesion = None
        self.vista.pantallas["MenuPrincipal"].configurar_acceso("", None, [])
        self.vista.mostrar_pantalla("PantallaLogin")
        login_screen = self.vista.pantallas["PantallaLogin"]
        login_screen.entry_usuario.delete(0, "end")
        login_screen.entry_pass.delete(0, "end")
        
    def vaciar_ticket_actual(self):
        """Vacía el carrito de compras actual desde el modelo."""
        self.modelo.ticket_actual.clear()