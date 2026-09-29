# Archivo: generador_tickets.py
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generar_ticket_pdf(nombre_archivo, rfc, razon_social, total, carrito_comprado, metodo_pago, pago, cambio):

    # Definir el nombre de la carpeta destino
    carpeta = "facturas"
    
    # Verificar si la carpeta existe, si no, Python la crea automaticamente
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
        
    # Unir la carpeta con el nombre del archivo (
    ruta_final = os.path.join(carpeta, nombre_archivo)

    # Obtener fecha y hora actual automáticamente
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Crear el documento PDF
    c = canvas.Canvas(ruta_final, pagesize=letter)

    # --- ELEMENTOS DE LA FACTURA ----
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, 750, "DULCERÍA MVC S.A. DE C.V.")
    c.setFont("Helvetica", 10)
    c.drawString(40, 735, "RFC: DULC202609MVC")
    c.drawString(40, 720, "Régimen Fiscal: 601 - General de Ley Personas Morales")
    c.drawString(40, 705, "C.P. de Expedición: 39355 (Acapulco, Gro.)")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(320, 750, "FACTURA ELECTRÓNICA (CFDI 4.0)")
    c.setFont("Helvetica", 10)
    c.drawString(320, 735, f"Fecha: {fecha_actual}")
    c.drawString(320, 720, f"Receptor: {razon_social}")
    c.drawString(320, 705, f"RFC: {rfc}")
    
    # Valores genéricos
    c.drawString(320, 690, "C.P.: 39355   |  Uso CFDI: G03 - Gastos en general")
    c.drawString(320, 675, "Régimen: 612 - Personas Físicas con")
    c.drawString(320, 660, "Actividades Empresariales")
    c.line(40, 635, 560, 635)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, 625, "Clave SAT")
    c.drawString(100, 625, "Cant")
    c.drawString(140, 625, "UDM")
    c.drawString(180, 625, "Descripción")
    c.drawString(400, 625, "P. Unitario")
    c.drawString(480, 625, "Importe")
    c.line(40, 620, 560, 620)

    c.setFont("Helvetica", 9)
    y = 600
    
    # Cálculos de IVA
    subtotal_venta = total / 1.16
    iva_venta = total - subtotal_venta

    for item in carrito_comprado:
        precio_sin_iva = (item['subtotal'] / item['cantidad']) / 1.16
        importe_sin_iva = item['subtotal'] / 1.16

        c.drawString(40, y, "50161800")
        c.drawString(100, y, str(item['cantidad']))
        c.drawString(140, y, "H87")
        c.drawString(180, y, item['producto'])
        c.drawString(400, y, f"${precio_sin_iva:.2f}") 
        c.drawString(480, y, f"${importe_sin_iva:.2f}") 
        y -= 20

    # TOTALES Y MÉTODO DE PAGO
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