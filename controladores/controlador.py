import tkinter as tk
import os
from tkinter import messagebox, simpledialog
from datetime import datetime
from reportlab.pdfgen import canvas
from modelos.modelo import ModeloDulceria
from vistas.ventana_principal import VistaDulceria
from vistas.generador_tickets import generar_ticket_pdf

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

        carrito_respaldo = self.modelo.ticket_actual.copy()

        # Procesamos el cobro 
        exito, cambio = self.modelo.procesar_cobro(pago)
        
        if exito:
            mensaje = f"¡Venta procesada con éxito!\n\nMétodo de pago: {tipo_pago}\n"
            if tipo_pago == "Efectivo":
                mensaje += f"Cambio a entregar: ${cambio:.2f}\n"
            
            # Si el usuario solicitó factura
            if datos_factura and datos_factura.get("requiere"):
                nombre_archivo = f"Factura_{datos_factura['rfc']}.pdf"
                
                # Unir el nombre y apellidos para mandarlo como "Razón Social"
                razon_social_cliente = f"{datos_factura.get('nombre', '')} {datos_factura.get('apellidos', '')}".strip()
                
                generar_ticket_pdf(
                    nombre_archivo=nombre_archivo,
                    rfc=datos_factura['rfc'],
                    razon_social=razon_social_cliente,
                    total=total,
                    carrito_comprado=carrito_respaldo,
                    metodo_pago=tipo_pago,
                    pago=pago,
                    cambio=cambio
                )
                
                mensaje += f"\n--- FACTURA GENERADA ---\n" \
                           f"Nombre: {datos_factura['nombre']} {datos_factura['apellidos']}\n" \
                           f"Correo: {datos_factura['correo']}\n" \
                           f"RFC: {datos_factura['rfc']}\n" \
                           f"Archivo: {nombre_archivo}"
            
            messagebox.showinfo("Ticket Cobrado", mensaje)
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

    def solicitar_proveedor(self, nombre_producto, stock_actual):
        # Aquí puedes programar la lógica de envío de correo, pedido simulado o registro en BD
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
        login_screen.txt_usuario.delete(0, tk.END)
        login_screen.txt_password.delete(0, tk.END)

    def procesar_filtro_inventario(self, texto, marca, categoria):
        # Obtiene la lista filtrada desde el modelo
        return self.modelo.obtener_inventario_filtrado(texto, marca, categoria)
