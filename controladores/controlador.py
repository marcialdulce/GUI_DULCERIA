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
        self.vista.pantallas["MenuPrincipal"].mostrar_seccion("NUEVA VENTA")

    def cerrar_sesion(self):
         # Limpiamos el ticket temporal por seguridad para el siguiente usuario
        self.modelo.ticket_actual.clear()
        
        # Le ordenamos a la ventana principal que muestre el Login
        self.vista.mostrar_pantalla("PantallaLogin")
         
        # Limpiamos las cajas de texto del login
        login_screen = self.vista.pantallas["PantallaLogin"]
        login_screen.txt_usuario.delete(0, tk.END)
        login_screen.txt_password.delete(0, tk.END)