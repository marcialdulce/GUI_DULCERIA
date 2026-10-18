import tkinter as tk
import os
import queue
import threading
from tkinter import messagebox, simpledialog
from datetime import datetime
from reportlab.pdfgen import canvas
from modelos.modelo import ModeloDulceria
from vistas.ventana_principal import VistaDulceria
from vistas.generador_tickets import generar_ticket_pdf
from servicios.hilo_factura import HiloFactura
from servicios.repositorio_ventas import RepositorioVentas
from servicios.tareas_ventas import TareaCargarVentas, TareaExportarReporte

class ControladorDulceria:
    def __init__(self):
        self.modelo = ModeloDulceria()
        self.usuario_actual = None

        # --- Procesamiento de ventas en segundo plano (Thread + Runnable) ---
        # Estas variables SOLO se modifican desde el hilo principal (Tkinter).
        # Los hilos de trabajo no las tocan: se comunican por la cola.
        self.repo_ventas = RepositorioVentas()
        self.cola_tareas = queue.Queue()           # hilos de trabajo -> ventana
        self.hilo_carga = None
        self.hilo_export = None
        self._cancelar_carga = threading.Event()
        self.resumen_ventas = None                 # datos ya preparados (se reemplaza completo)
        self.estado_carga = {"estado": "inactivo", "porcentaje": 0.0, "leidas": 0, "mensaje": ""}
        self.estado_export = {"estado": "inactivo", "ruta": ""}
        self._notificaciones = []

    def iniciar(self):
        self.vista.mainloop()

    def procesar_login(self, usuario, password):
        # Validamos usando el Modelo
        es_valido = self.modelo.validar_usuario(usuario, password)

        if es_valido:
            self.usuario_actual = usuario
            self.vista.mostrar_alerta("Inicio de sesión", f"¡Bienvenido/a, {usuario}!", "info")
            
            # Limpiar campos en la vista usando los nombres correctos de los atributos
            self.vista.pantallas["PantallaLogin"].entry_usuario.delete(0, 'end')
            self.vista.pantallas["PantallaLogin"].entry_pass.delete(0, 'end')
            
            # Actualizar nombre y cambiar pantalla al nuevo Menu Principal
            self.vista.pantallas["MenuPrincipal"].actualizar_usuario(usuario)
            self.vista.mostrar_pantalla("MenuPrincipal")
        else:
            # VENTANA EMERGENTE DE ERROR
            self.vista.mostrar_alerta(
                "Datos incorrectos", 
                "Las claves de acceso o los datos ingresados no son correctos.\nPor favor, intente nuevamente.", 
                "error"
            )
            self.vista.pantallas["PantallaLogin"].entry_pass.delete(0, 'end')

    def procesar_cobro_avanzado(self, tipo_pago, datos_factura):
        total = self.modelo.calcular_total()
        
        if total == 0:
            messagebox.showwarning("Aviso", "El ticket está vacío. Agrega productos primero.")
            return

        pago = total  # Si es tarjeta, se cobra el monto exacto por defecto
        
        # Si paga en efectivo, pedimos la cantidad con un cuadro de diálogo
        if tipo_pago == "Efectivo":
            pago = simpledialog.askfloat("Cobrar en Efectivo", f"Total a cobrar: ${total:.2f}\n¿Con cuánto efectivo paga el cliente?")
            if pago is None:  # Si el usuario presiona "Cancelar"
                return

        carrito_respaldo = self.modelo.ticket_actual.copy()

        # Procesamos el cobro 
        exito, cambio = self.modelo.procesar_cobro(pago)
        
        if exito:

            self.modelo.guardar_inventario() # Persiste el inventario tras descontar el stock

            # Registra la venta en el historial (lo que luego lee la tarea en segundo plano)
            aviso_historial = ""
            try:
                self.repo_ventas.registrar(
                    metodo_pago=tipo_pago,
                    total=total,
                    articulos=carrito_respaldo,
                    facturado=bool(datos_factura and datos_factura.get("requiere")),
                )
            except OSError as e:
                # El cobro ya se hizo; solo avisamos que no quedó en el historial
                aviso_historial = f"\n\nAviso: la venta no se pudo guardar en el historial ({e.strerror or e})."

            mensaje = f"¡Venta procesada con éxito!\n\nMétodo de pago: {tipo_pago}\n"
            if tipo_pago == "Efectivo":
                mensaje += f"Cambio a entregar: ${cambio:.2f}\n"
            
                # Si el usuario solicitó factura
            if datos_factura and datos_factura.get("requiere"):
                    nombre_archivo = f"Factura_{datos_factura['rfc']}.pdf"
                    razon_social = f"{datos_factura.get('nombre','')} {datos_factura.get('apellidos','')}".strip()

                    # CREACIÓN DEL THREAD (Extendiendo la clase)
                    self.hilo_factura = HiloFactura(         
                        nombre_archivo=nombre_archivo,
                        rfc=datos_factura['rfc'],
                        razon_social=razon_social,
                        total=total,
                        carrito=carrito_respaldo,
                        metodo_pago=tipo_pago,
                        pago=pago,
                        cambio=cambio
                    )

                    # Metodos de control
                    self.hilo_factura.set_prioridad(9)
                    print(f"Nombre del hilo: {self.hilo_factura.get_nombre()}")
                    print(f"Prioridad: {self.hilo_factura.get_prioridad()}")

                    self.hilo_factura.start()
                    
                    # CREACIÓN DEL RUNNABLE (Pasando función al target)
                    # Este es el equivalente  al Runnable de Java: separar la tarea del hilo
                    
                    self.hilo_secundario = threading.Thread(
                        target=self._tarea_notificar_fin, 
                        args=(nombre_archivo, self.vista.pantallas["MenuPrincipal"].contenido.winfo_children()[0]),
                        daemon=True)
                    
                    self.hilo_secundario.start()
                
                    mensaje += "\n Factura generándose en segundo plano..."

            messagebox.showinfo("Ticket Cobrado", mensaje + aviso_historial)
           

    def _tarea_notificar_fin(self, nombre_archivo, panel_ventas):
            # Esta funcion es el "Runnable". Se ejecuta de forma paralela
            self.hilo_factura.join() # Espera a que el hilo de la factura muera (DEAD)

            if self.hilo_factura.exito:
                mensaje = f" Listo: {nombre_archivo}"
            # Usamos after(0, ...) para actualizar la interfaz de forma segura
                self.vista.after(0, lambda: panel_ventas.actualizar_estado_factura(mensaje, "green"))
            elif self.hilo_factura.error:
                mensaje = " Error al generar PDF"
                self.vista.after(0, lambda: panel_ventas.actualizar_estado_factura(mensaje, "red"))

              # Ventana emergente para mostrar el error
                self.vista.after(0, lambda e=self.hilo_factura.error: messagebox.showerror("Error de Facturación", f"No se pudo guardar el PDF:\n{e}"))
    
        
    # ========================================================
    # VENTAS EN SEGUNDO PLANO (Thread + Runnable)
    # ========================================================
    def iniciar_carga_ventas(self, fecha_filtro=""):
        """Lanza la lectura masiva en un hilo. Devuelve False si ya hay una en curso."""
        if self.estado_carga["estado"] in ("cargando", "cancelando"):
            return False

        self._cancelar_carga = threading.Event()
        # RUNNABLE: describe QUÉ se hace (leer y resumir las ventas)
        tarea = TareaCargarVentas(self.repo_ventas, self.cola_tareas,
                                  self._cancelar_carga, fecha_filtro)
        # THREAD: es QUIEN lo ejecuta, para que el mainloop siga atendiendo la ventana
        self.hilo_carga = threading.Thread(target=tarea.run, name="HiloCargaVentas", daemon=True)
        self.estado_carga = {"estado": "cargando", "porcentaje": 0.0, "leidas": 0, "mensaje": ""}
        self.hilo_carga.start()
        return True

    def cancelar_carga_ventas(self):
        if self.estado_carga["estado"] == "cargando":
            self.estado_carga["estado"] = "cancelando"
            self._cancelar_carga.set()

    def exportar_reporte(self, carpeta):
        """Guarda el resumen ya preparado en un CSV, en otro hilo. Devuelve (ok, mensaje)."""
        if self.resumen_ventas is None:
            return False, "Primero carga las ventas (botón BUSCAR) para tener datos que exportar."
        if self.estado_export["estado"] == "guardando":
            return False, "Ya se está guardando un reporte. Espera a que termine."

        carpeta = (carpeta or "").strip() or "reportes"
        tarea = TareaExportarReporte(self.resumen_ventas, carpeta, self.cola_tareas)
        self.hilo_export = threading.Thread(target=tarea.run, name="HiloExportarReporte", daemon=True)
        self.estado_export = {"estado": "guardando", "ruta": ""}
        self.hilo_export.start()
        return True, ""

    def hay_tareas_activas(self):
        return (self.estado_carga["estado"] in ("cargando", "cancelando")
                or self.estado_export["estado"] == "guardando")

    def sondear_tareas(self):
        """Lo llama la ventana con after(): vacía la cola y actualiza el estado.
        Es el ÚNICO lugar donde los mensajes de los hilos se vuelven estado."""
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
                self.resumen_ventas = msg["resumen"]   # se publica completo, de un golpe
                e.update(estado="terminado", porcentaje=100.0, leidas=msg["leidas"])
            elif tipo == "cancelado":
                e["estado"] = "cancelado"
            elif tipo == "error":
                e.update(estado="error", mensaje=msg["mensaje"])
                self._notificaciones.append(("error", "Error al cargar ventas", msg["mensaje"]))
        else:
            if tipo == "terminado":
                self.estado_export = {"estado": "terminado", "ruta": msg["ruta"]}
                self._notificaciones.append(("info", "Reporte generado",
                                             f"El reporte se guardó en:\n{os.path.abspath(msg['ruta'])}"))
            elif tipo == "error":
                self.estado_export = {"estado": "error", "ruta": ""}
                self._notificaciones.append(("error", "No se pudo guardar el reporte", msg["mensaje"]))

    def tomar_notificaciones(self):
        """Devuelve y vacía los avisos pendientes para mostrarlos en la ventana."""
        pendientes, self._notificaciones = self._notificaciones, []
        return pendientes

    def procesar_agregar(self, nombre_producto):
        cantidad = simpledialog.askinteger("Cantidad", f"¿Cuantos {nombre_producto} deseas agregar?")
        
        if cantidad and cantidad > 0:
            resultado = self.modelo.agregar_al_ticket(nombre_producto, cantidad)
            
            if resultado == "stock_insuficiente":
                messagebox.showerror("Error de Stock", "No existe cantidad suficiente")
            elif resultado == "no_encontrado":
                messagebox.showerror("Error", "Producto no encontrado")

        
    def obtener_datos_ventas(self):
        total = self.modelo.calcular_total()
        # Retorna el inventario, el carrito y el total
        return self.modelo.inventario, self.modelo.ticket_actual, total

    def solicitar_proveedor(self, nombre_producto, stock_actual):
        respuesta = messagebox.askyesno(
            "Pedido a Proveedor", 
            f"¿Deseas enviar una orden de abastecimiento al proveedor para:\n\n• Producto: {nombre_producto}\n• Stock actual: {stock_actual} unidades?"
        )
        if respuesta:
            messagebox.showinfo("Solicitud Exitosa", f"¡Pedido enviado al proveedor con éxito para el producto '{nombre_producto}'!")

    def cerrar_sesion(self):
        # Limpiamos el ticket temporal por seguridad para el siguiente usuario
        self.modelo.ticket_actual.clear()
        
        # Le ordenamos a la ventana principal que muestre el Login
        self.vista.mostrar_pantalla("PantallaLogin")
         
        # Limpiamos las cajas de texto del login
        login_screen = self.vista.pantallas["PantallaLogin"]
        login_screen.entry_usuario.delete(0, tk.END)
        login_screen.entry_pass.delete(0, tk.END)

    def procesar_filtro_inventario(self, texto, marca, categoria):
        # Obtiene la lista filtrada desde el modelo
        return self.modelo.obtener_inventario_filtrado(texto, marca, categoria)

        # ========================================================
    # PROVEEDORES
    # ========================================================
    def obtener_proveedores(self):
        """Devuelve la lista completa de proveedores."""
        return self.modelo.proveedores

    def procesar_nuevo_proveedor(self, nombre, telefono, correo):
        """Valida y delega al modelo. Devuelve (ok, mensaje)."""
        resultado = self.modelo.agregar_proveedor(nombre, telefono, correo)

        if resultado == "nombre_vacio":
            return False, "El nombre del proveedor no puede estar vacío."
        if resultado == "ya_existe":
            return False, f"Ya existe un proveedor con el nombre '{nombre}'."

        return True, f"Proveedor '{nombre}' agregado correctamente."

    def procesar_eliminar_proveedor(self, proveedor_id):
        """Elimina un proveedor y desvincula sus productos."""
        self.modelo.eliminar_proveedor(proveedor_id)
        return True

    def procesar_nuevo_producto(self, nombre, marca, categoria, precio, stock, proveedor_id=None):
        """Valida y delega al modelo. Devuelve (ok, mensaje)."""
        try:
            precio = float(precio)
            stock  = int(stock)
        except (ValueError, TypeError):
            return False, "Precio y stock deben ser números válidos."

        resultado = self.modelo.agregar_producto(nombre, marca, categoria, precio, stock, proveedor_id)

        if resultado == "nombre_vacio":
            return False, "El nombre del producto no puede estar vacío."
        if resultado == "ya_existe":
            return False, f"Ya existe un producto llamado '{nombre}'."
        if resultado == "datos_invalidos":
            return False, "El precio debe ser mayor a 0 y el stock no puede ser negativo."

        return True, f"Producto '{nombre}' agregado correctamente."
