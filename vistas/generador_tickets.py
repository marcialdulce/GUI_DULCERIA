# Archivo: generador_tickets.py
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generar_ticket_pdf(nombre_archivo, productos_comprados, total):
    # Obtener fecha y hora actual automáticamente
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Crear el documento PDF
    c = canvas.Canvas(nombre_archivo, pagesize=letter)
    
    # Cabecera del ticket
    c.drawString(100, 750, "=== DULCERÍA LA ESTRELLA ===")
    c.drawString(100, 735, f"Fecha: {fecha_actual}")
    c.drawString(100, 720, "-" * 40)
    
    # Listado de productos (espera una lista de tuplas: [("Producto", precio), ...])
    y = 700
    for producto, precio in productos_comprados:
        c.drawString(100, y, f"{producto} - ${precio:.2f}")
        y -= 20
        
    c.drawString(100, y - 10, "-" * 40)
    c.drawString(100, y - 30, f"TOTAL A PAGAR: ${total:.2f}")
    
    c.save()
    print(f"Ticket generado exitosamente: {nombre_archivo}")