import tkinter as tk
from tkinter import messagebox, simpledialog
from modelo import ModeloDulceria
from vista import VistaDulceria

class ControladorDulceria:
    def __init__(self):
        self.modelo = ModeloDulceria()
        self.vista = VistaDulceria(self)
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
            
            # Actualizar nombre y cambiar pantalla
            self.vista.pantallas["PantallaPrincipal"].actualizar_usuario(usuario)
            self.vista.mostrar_pantalla("PantallaPrincipal")
        else:
           # VENTANA EMERGENTE DE ERROR
            self.vista.mostrar_alerta(
                "Datos incorrectos", 
                "Las claves de acceso o los datos ingresados no son correctos.\nPor favor, intente nuevamente.", 
                "error"
            )
            self.vista.pantallas["PantallaLogin"].txt_password.delete(0, 'end')

    def cobrar_ticket(self):
        # 1. Declarar y calcular el total primero
        total = self.modelo.calcular_total()
        
        if total == 0:
            messagebox.showwarning("Aviso", "El ticket está vacío. Agrega productos primero.")
            return

        # 2. Abre una ventanita preguntando la cantidad de pago
        pago = simpledialog.askfloat("Cobrar Venta", f"Total a cobrar: ${total:.2f}\n¿Con cuánto efectivo paga el cliente?")
        
        if pago is not None: # Si el usuario no presionó "Cancelar"
            exito, cambio = self.modelo.procesar_cobro(pago)
            
            if exito:
                messagebox.showinfo("Venta Exitosa", f"Venta procesada correctamente.\n\nCambio a entregar: ${cambio:.2f}")
                self.actualizar_ticket_visual()
                
                # Recarga la vista para actualizar el stock en las tarjetas
                self.vista.pantallas["PantallaPrincipal"].mostrar_seccion("NUEVA VENTA")
            else:
                messagebox.showerror("Pago Insuficiente", f"Faltan ${total - pago:.2f} para completar la venta.")

    def procesar_agregar(self, nombre_producto):
        # Lanza una ventana emergente nativa pidiendo la cantidad
        cantidad = simpledialog.askinteger("Cantidad", f"¿Cuántos {nombre_producto} deseas agregar?")
        
        if cantidad and cantidad > 0:
            resultado = self.modelo.agregar_al_ticket(nombre_producto, cantidad)
            
            if resultado == True:
                self.actualizar_ticket_visual()
            elif resultado == "stock_insuficiente":
                messagebox.showerror("Error de Stock", "No existe cantidad suficiente")
            else:
                messagebox.showerror("Error", "Producto no encontrado")

    def actualizar_ticket_visual(self):
        # Accedemos a la pantalla principal donde está dibujada la tabla
        pantalla = self.vista.pantallas["PantallaPrincipal"]
        
        # 1. Borramos los datos viejos de la tabla para no duplicar
        for fila in pantalla.tabla_ticket.get_children():
            pantalla.tabla_ticket.delete(fila)
            
        # 2. Dibujamos fila por fila leyendo la memoria del Modelo
        for item in self.modelo.ticket_actual:
            pantalla.tabla_ticket.insert("", "end", values=(
                item["producto"], 
                item["cantidad"], 
                f"${item['subtotal']:.2f}"
            ))
            
        # 3. Actualizamos la etiqueta del Total ($0.00)
        total = self.modelo.calcular_total()
        pantalla.label_total.config(text=f"${total:.2f}")

    def cerrar_sesion(self):
         # 1. Limpiamos el ticket temporal por seguridad para el siguiente usuario
           self.modelo.ticket_actual.clear()
        
        # 2. Le ordenamos a la ventana principal que muestre el Login
           self.vista.mostrar_pantalla("PantallaLogin")
         
        # 3. Limpiamos las cajas de texto del login si es necesario (opcional)
        # (Opcional, pero deja la pantalla de login limpia)
           login_screen = self.vista.pantallas["PantallaLogin"]
           login_screen.txt_usuario.delete(0, tk.END)
           login_screen.txt_password.delete(0, tk.END)