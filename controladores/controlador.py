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

        # 2. Abre una ventana preguntando la cantidad de pago
        pago = simpledialog.askfloat("Cobrar Venta", f"Total a cobrar: ${total:.2f}\n¿Con cuánto efectivo paga el cliente?")
        
        if pago is not None: # Si el usuario no presionó "Cancelar"
            exito, cambio = self.modelo.procesar_cobro(pago)
            
            if exito:
                messagebox.showinfo("Venta Exitosa", f"Venta procesada correctamente.\n\nCambio a entregar: ${cambio:.2f}")
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

     

        