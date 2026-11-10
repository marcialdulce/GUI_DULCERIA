import os
import subprocess
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# =========================================================
# 1. GENERAR FACTURA (Hoja tamaño carta)
# =========================================================
def generar_ticket_pdf(ruta_completa, rfc, razon_social, total, carrito_comprado, metodo_pago, pago, cambio):
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c = canvas.Canvas(ruta_completa, pagesize=letter)

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

    try:
        if os.name == 'nt':
            os.startfile(ruta_completa)
        else:
            subprocess.Popen(['xdg-open', ruta_completa])
    except Exception as e:
        print(f"No se pudo abrir el PDF automáticamente: {e}")


# =========================================================
# 2. GENERAR TICKET (Hoja tamaño ticket para el Cajero)
# =========================================================
def generar_comprobante_ticket_pdf(ruta_completa, venta):
    """Genera el comprobante PDF de una venta ya registrada."""
    os.makedirs(os.path.dirname(ruta_completa) or ".", exist_ok=True)
    c = canvas.Canvas(ruta_completa, pagesize=(300, 520))
    ancho, alto = 300, 520
    y = alto - 35
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(ancho / 2, y, "DULCERÍA MVC")
    y -= 18
    c.setFont("Helvetica", 8)
    c.drawCentredString(ancho / 2, y, "COMPROBANTE DE COMPRA")
    y -= 22
    c.drawString(18, y, f"Folio: {venta.get('folio', 'N/D')}")
    y -= 13
    c.drawString(18, y, f"Fecha: {venta.get('fecha', 'N/D')}")
    y -= 13
    c.drawString(18, y, f"Pago: {venta.get('metodo_pago', 'N/D')}")
    y -= 12
    c.line(18, y, ancho - 18, y)
    y -= 16
    c.setFont("Helvetica-Bold", 8)
    c.drawString(18, y, "PRODUCTO")
    c.drawRightString(ancho - 18, y, "IMPORTE")
    y -= 12
    c.setFont("Helvetica", 8)
    
    for articulo in venta.get("articulos", []):
        nombre = str(articulo.get("producto", ""))[:27]
        cantidad = int(articulo.get("cantidad", 0))
        subtotal = float(articulo.get("subtotal", 0))
        c.drawString(18, y, nombre)
        c.drawRightString(ancho - 18, y, f"${subtotal:.2f}")
        y -= 11
        c.drawString(22, y, f"Cantidad: {cantidad}")
        y -= 14
        if y < 75:
            c.showPage()
            y = alto - 35
            c.setFont("Helvetica", 8)
            
    c.line(18, y, ancho - 18, y)
    y -= 22
    c.setFont("Helvetica-Bold", 11)
    c.drawString(18, y, "TOTAL:")
    c.drawRightString(ancho - 18, y, f"${float(venta.get('total', 0)):.2f}")
    y -= 28
    c.setFont("Helvetica", 8)
    c.drawCentredString(ancho / 2, y, "Gracias por su compra")
    c.save()
    return ruta_completa