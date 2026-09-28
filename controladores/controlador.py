import tkinter as tk
from tkinter import messagebox, simpledialog
from modelos.modelo import ModeloDulceria
from vistas.ventana_principal import VistaDulceria

class ControladorDulceria:
    def __init__(self):
        self.modelo = ModeloDulceria()
        self.usuario_actual = None

    def iniciar(self):
        self.vista.mainloop()

    def procesar_login(self, usuario, password):
        # Validamos usando el Modelo
        es_valido = self.modelo.validar_usuario(usuario, password)

        if es_valido:
            self.usuario_actual = usuario
            self.vista.mostrar_alerta("Inicio de sesión", f"¡Bienvenido/a, {usuario}!", "info")
            
            # Limpiar campos en la vista
            self.vista.pantallas["PantallaLogin"].txt_usuario.delete(0, 'end')
            self.vista.pantallas["PantallaLogin"].txt_password.delete(0, 'end')
            
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
            self.vista.pantallas["PantallaLogin"].txt_password.delete(0, 'end')

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

        # Procesamos el cobro utilizando la lógica existente de tu modelo
        exito, cambio = self.modelo.procesar_cobro(pago)
        
        if exito:
            mensaje = f"¡Venta procesada con éxito!\n\nMétodo de pago: {tipo_pago}\n"
            if tipo_pago == "Efectivo":
                mensaje += f"Cambio a entregar: ${cambio:.2f}\n"
            
            # Si el usuario solicitó factura, agregamos los datos al mensaje de éxito
            if datos_factura and datos_factura["requiere"]:
                mensaje += f"\n--- FACTURA GENERADA ---\n" \
                           f"Nombre: {datos_factura['nombre']} {datos_factura['apellidos']}\n" \
                           f"Correo: {datos_factura['correo']}\n" \
                           f"RFC: {datos_factura['rfc']}"
            
            messagebox.showinfo("Ticket Cobrado", mensaje)
            
            # Opcional: limpiar el ticket actual si tu modelo no lo hace automáticamente al cobrar
            self.modelo.ticket_actual.clear()
        else:
            messagebox.showerror("Pago Insuficiente", f"Faltan ${total - pago:.2f} para completar la venta.")

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

    def obtener_datos_agotados(self):
        productos_filtrados = []
        for producto in self.modelo.inventario:
            stock = producto["stock"]
            if stock < 15:
                estado = "AGOTADO" if stock == 0 else "BAJO"
                productos_filtrados.append((producto["nombre"], producto["marca"], stock, estado))
        
        return productos_filtrados

    def cerrar_sesion(self):
         # Limpiamos el ticket temporal por seguridad para el siguiente usuario
        self.modelo.ticket_actual.clear()
        
        # Le ordenamos a la ventana principal que muestre el Login
        self.vista.mostrar_pantalla("PantallaLogin")
         
        # Limpiamos las cajas de texto del login
        login_screen = self.vista.pantallas["PantallaLogin"]
        login_screen.txt_usuario.delete(0, tk.END)
        login_screen.txt_password.delete(0, tk.END)

    def procesar_filtro_inventario(self, texto, marca, categoria):
        # Obtiene la lista filtrada desde el modelo
        return self.modelo.obtener_inventario_filtrado(texto, marca, categoria)

     

        