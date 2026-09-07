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
        total = self.modelo.calcular_total()
        
        if total == 0:
            messagebox.showwarning("Aviso", "El ticket está vacío. Agrega productos primero.")
            return

        # Abre una ventanita preguntando la cantidad de pago
        pago = simpledialog.askfloat("Cobrar Venta", f"Total a cobrar: ${total:.2f}\n¿Con cuánto efectivo paga el cliente?")
        
        if pago is not None: # Si el usuario no presionó "Cancelar"
            exito, cambio = self.modelo.procesar_cobro(pago)
            
            if exito:
                messagebox.showinfo("Venta Exitosa", f"Venta procesada correctamente.\n\nCambio a entregar: ${cambio:.2f}")
                self.actualizar_ticket_visual() # Limpia la pantalla para la siguiente venta
            else:
                messagebox.showerror("Pago Insuficiente", f"Faltan ${total - pago:.2f} para completar la venta.")