import tkinter as tk
import os
from tkinter import messagebox, simpledialog
from datetime import datetime
from reportlab.pdfgen import canvas
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

    def cobrar_ticket(self, metodo_pago="Efectivo", requiere_factura=False, rfc="", razon_social=""):
        # Pedir al modelo el carrito y el total
        total = self.modelo.calcular_total()

        if total == 0:
            if total == 0:
              messagebox.showwarning("Aviso", "El ticket se encuentra vacío. Agrega productos primero.")
            return

        # Validar los datos de la factura antes de cobrar
        if requiere_factura:
            if rfc.strip() == "" or razon_social.strip() == "":
                messagebox.showerror("Error", "Debe ingresar el RFC y la razón social para generar la factura.")
                return

        # IMPORTANTE: Guardamos una copia del carrito antes del cobro, 
        # porque el Modelo probablemente lo va a borrar al terminar la venta.
        carrito_comprado = self.modelo.ticket_actual.copy()

        # 2. Cobro (Efectivo o Tarjeta)
        cambio = 0.0
        if metodo_pago == "Efectivo":
            pago = simpledialog.askfloat("Cobrar Venta", f"Total a cobrar: ${total:.2f}\n¿Con cuánto efectivo paga el cliente?")
            if pago is None: 
                return # El usuario presionó Cancelar
            
            exito, cambio = self.modelo.procesar_cobro(pago)
        else:
            # Si es Tarjeta, asumimos que pasa el total exacto por la terminal
            exito, cambio = self.modelo.procesar_cobro(total)

        # Si el pago no fue exitoso (ej. no dio dinero suficiente)
        if not exito:
            messagebox.showerror("Pago Insuficiente", "El monto ingresado no cubre el total de la venta.")
            return

        # Generación del PDF si el cobro fue exitoso y pidieron factura
        if requiere_factura:
            try:
                if not os.path.exists("facturas"):
                    os.makedirs("facturas")

                # Guarda los archivos PDF dentro de la carpeta y se almacena en gitignore
                nombre_archivo = f"facturas/Factura_{rfc}.pdf"
                c = canvas.Canvas(nombre_archivo)
                fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

       
                c.setFont("Helvetica-Bold", 14)
                c.drawString(40, 800, "DULCERÍA MVC S.A. DE C.V.")
                c.setFont("Helvetica", 10)
                c.drawString(40, 785, "RFC: DULC202609MVC")
                c.drawString(40, 770, "Régimen Fiscal: 601 - General de Ley Personas Morales")
                c.drawString(40, 755, "C.P. de Expedición: 39355 (Acapulco, Gro.)")
                c.setFont("Helvetica-Bold", 12)
                c.drawString(320, 800, "FACTURA ELECTRÓNICA (CFDI 4.0)")
                c.setFont("Helvetica", 10)
                c.drawString(320, 785, f"Fecha: {fecha_actual}")
                c.drawString(320, 770, f"Receptor: {razon_social}")
                c.drawString(320, 755, f"RFC: {rfc}")
                # Asumimir valores genéricos 
                c.drawString(320, 740, "C.P.: 39355   |  Uso CFDI: G03 - Gastos en general")
                c.drawString(320, 725, "Régimen: 612 - Personas Físicas con")
                c.drawString(320, 710, "Actividades Empresariales")
                c.line(40, 685, 560, 685)

                c.setFont("Helvetica-Bold", 9)
                c.drawString(40, 675, "Clave SAT")
                c.drawString(100, 675, "Cant")
                c.drawString(140, 675, "UDM")
                c.drawString(180, 675, "Descripción")
                c.drawString(400, 675, "P. Unitario")
                c.drawString(480, 675, "Importe")
                c.line(40, 670, 560, 670)

                c.setFont("Helvetica", 9)
                y = 650
                #  IVA (16%) del total 
                subtotal_venta = total / 1.16
                iva_venta = total - subtotal_venta

                for item in carrito_comprado:
                    precio_sin_iva = (item['subtotal'] / item['cantidad']) / 1.16
                    importe_sin_iva = item['subtotal'] / 1.16

                    # Imprimir cada dato alineado con su título arriba
                    c.drawString(40, y, "50161800")
                    c.drawString(100, y, str(item['cantidad']))
                    c.drawString(140, y, "H87")
                    c.drawString(180, y, item['producto'])
                    c.drawString(400, y, f"${precio_sin_iva:.2f}") 
                    c.drawString(480, y, f"${importe_sin_iva:.2f}") 
                    y -= 20

                # TOTALES, MÉTODO DE PAGO Y CAMBIO 
                c.line(40, y, 560, y)
                y -= 20
                
                forma_pago_sat = "01 - Efectivo" if metodo_pago == "Efectivo" else "04 - Tarjeta de crédito"
                
                c.drawString(40, y, "Método de Pago: PUE - Pago en una sola exhibición")
                c.drawString(40, y-15, f"Forma de Pago: {forma_pago_sat}")
                c.drawString(40, y-30, "Moneda: MXN - Peso Mexicano")
                
                c.drawString(400, y, "Subtotal:")
                c.drawString(480, y, f"${subtotal_venta:.2f}")
                
                c.drawString(400, y-15, "IVA (16%):")
                c.drawString(480, y-15, f"${iva_venta:.2f}")
                
                c.setFont("Helvetica-Bold", 11)
                c.drawString(400, y-35, "TOTAL:")
                c.drawString(480, y-35, f"${total:.2f}")

                if metodo_pago == "Efectivo":
                    c.setFont("Helvetica", 10)
                    c.drawString(400, y-55, "Efectivo:")
                    c.drawString(480, y-55, f"${pago:.2f}")
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(400, y-70, "Cambio:")
                    c.drawString(480, y-70, f"${cambio:.2f}")

                c.save()
                
                messagebox.showinfo("Éxito", f"Venta procesada con {metodo_pago}.\nCambio: ${cambio:.2f}\n\nFactura '{nombre_archivo}' generada.")
            
            except Exception as e:
                messagebox.showerror("Error de PDF", f"Cobro exitoso, pero falló la creación del PDF: {e}")
        else:
            messagebox.showinfo("Venta Exitosa", f"Venta procesada correctamente con {metodo_pago}.\n\nCambio a entregar: ${cambio:.2f}")

       
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

     

        