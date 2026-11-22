import os
import subprocess
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def abrir_archivo_pdf(ruta_completa):
    """Abre un PDF con el visor predeterminado del sistema operativo."""
    try:
        if os.name == "nt":
            os.startfile(os.path.abspath(ruta_completa))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", ruta_completa])
        else:
            subprocess.Popen(["xdg-open", ruta_completa])
    except Exception as e:
        print(f"No se pudo abrir el PDF automáticamente: {e}")


# =========================================================
# 1. GENERAR FACTURA ELECTRÓNICA (Hoja tamaño carta)
# =========================================================
def generar_ticket_pdf(
    ruta_completa,
    rfc,
    razon_social,
    total,
    carrito_comprado,
    metodo_pago,
    pago,
    cambio,
    regimen_fiscal="612 - Personas Físicas con Actividades Empresariales",
    cp_fiscal="39355",
    correo="",
    folio_factura="N/D",
):
    os.makedirs(os.path.dirname(ruta_completa) or ".", exist_ok=True)
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    razon_social_segura = str(razon_social or "PÚBLICO EN GENERAL").replace("\n", " ").replace("\r", "").strip()[:45]
    rfc_seguro = str(rfc or "XAXX010101000").replace("\n", " ").replace("\r", "").strip()[:14]
    regimen_seguro = str(regimen_fiscal or "N/D").replace("\n", " ").replace("\r", "").strip()[:48]
    cp_seguro = str(cp_fiscal or "N/D").replace("\n", " ").replace("\r", "").strip()[:10]
    correo_seguro = str(correo or "").replace("\n", " ").replace("\r", "").strip()[:45]

    c = canvas.Canvas(ruta_completa, pagesize=letter)

    # Datos del Emisor (Izquierda)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, 750, "DULCERÍA ALGORRICO")
    c.setFont("Helvetica", 9)
    c.drawString(40, 735, "RFC Emisor: ALG260101ABC")
    c.drawString(40, 720, "Régimen Fiscal: 601 - General de Ley Personas Morales")
    c.drawString(40, 705, "Lugar de Expedición: Acapulco, Guerrero")
    c.drawString(40, 690, f"Folio Factura: {folio_factura}")

    # Datos del Receptor (Derecha)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(310, 750, "FACTURA ELECTRÓNICA (CFDI 4.0)")
    c.setFont("Helvetica", 9)
    c.drawString(310, 735, f"Fecha: {fecha_actual}")
    c.drawString(310, 720, f"Receptor: {razon_social_segura}")
    c.drawString(310, 705, f"RFC: {rfc_seguro}")
    c.drawString(310, 690, f"C.P.: {cp_seguro}  |  Uso CFDI: G03")
    c.drawString(310, 675, f"Régimen: {regimen_seguro}")
    if correo_seguro:
        c.drawString(310, 660, f"Correo: {correo_seguro}")
    c.line(40, 645, 560, 645)

    # Tabla de conceptos
    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, 632, "Clave SAT")
    c.drawString(100, 632, "Cant")
    c.drawString(140, 632, "UDM")
    c.drawString(180, 632, "Descripción")
    c.drawString(400, 632, "P. Unitario")
    c.drawString(480, 632, "Importe")
    c.line(40, 626, 560, 626)

    c.setFont("Helvetica", 9)
    y = 608

    subtotal_venta = 0.0
    for item in carrito_comprado:
        cantidad = int(item["cantidad"])
        importe_base = float(item["subtotal"])
        precio_base = float(item.get("precio_unitario", importe_base / max(cantidad, 1)))
        subtotal_venta += importe_base

        c.drawString(40, y, "50161800")
        c.drawString(100, y, str(cantidad))
        c.drawString(140, y, "H87")
        c.drawString(180, y, str(item["producto"])[:36])
        c.drawString(400, y, f"${precio_base:.2f}")
        c.drawString(480, y, f"${importe_base:.2f}")
        y -= 18

        if y < 140:
            c.showPage()
            y = 740
            c.setFont("Helvetica", 9)

    subtotal_venta = round(subtotal_venta, 2)
    iva_venta = round(subtotal_venta * 0.16, 2)
    total_calculado = round(subtotal_venta + iva_venta, 2)

    c.line(40, y, 560, y)
    y -= 20

    formas_sat = {
        "Efectivo": "01 - Efectivo",
        "Tarjeta de débito": "28 - Tarjeta de débito",
        "Tarjeta de crédito": "04 - Tarjeta de crédito",
        "Pago mixto": "99 - Pago mixto (Efectivo/Tarjeta)",
    }
    forma_pago_sat = formas_sat.get(metodo_pago, "01 - Efectivo")

    c.drawString(40, y, "Método de Pago: PUE - Pago en una sola exhibición")
    c.drawString(40, y - 15, f"Forma de Pago: {forma_pago_sat}")
    c.drawString(40, y - 30, "Moneda: MXN - Peso Mexicano")

    c.drawString(400, y, "Subtotal:")
    c.drawString(480, y, f"${subtotal_venta:.2f}")

    c.drawString(400, y - 15, "IVA (16%):")
    c.drawString(480, y - 15, f"${iva_venta:.2f}")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(400, y - 35, "TOTAL:")
    c.drawString(480, y - 35, f"${total_calculado:.2f}")

    c.setFont("Helvetica", 10)
    c.drawString(400, y - 55, "Pagado:")
    c.drawString(480, y - 55, f"${float(pago):.2f}")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(400, y - 70, "Cambio:")
    c.drawString(480, y - 70, f"${float(cambio):.2f}")

    c.save()
    abrir_archivo_pdf(ruta_completa)
    return ruta_completa


# =========================================================
# 2. GENERAR TICKET DE VENTA (Hoja tamaño ticket)
# =========================================================
def generar_comprobante_ticket_pdf(ruta_completa, venta):
    """Genera el comprobante PDF de una venta registrada."""
    os.makedirs(os.path.dirname(ruta_completa) or ".", exist_ok=True)
    c = canvas.Canvas(ruta_completa, pagesize=(300, 540))
    ancho, alto = 300, 540
    y = alto - 35

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(ancho / 2, y, "DULCERÍA ALGORRICO")
    y -= 16
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
        if y < 110:
            c.showPage()
            y = alto - 35
            c.setFont("Helvetica", 8)

    c.line(18, y, ancho - 18, y)
    y -= 16

    total_val = float(venta.get("total", 0))
    subtotal_val = venta.get("subtotal")
    impuesto_val = venta.get("impuesto")

    if subtotal_val is not None and impuesto_val is not None:
        c.setFont("Helvetica", 9)
        c.drawString(18, y, "SUBTOTAL:")
        c.drawRightString(ancho - 18, y, f"${float(subtotal_val):.2f}")
        y -= 13
        c.drawString(18, y, "IVA (16%):")
        c.drawRightString(ancho - 18, y, f"${float(impuesto_val):.2f}")
        y -= 16

    c.setFont("Helvetica-Bold", 11)
    c.drawString(18, y, "TOTAL:")
    c.drawRightString(ancho - 18, y, f"${total_val:.2f}")
    y -= 16

    if "total_pagado" in venta:
        c.setFont("Helvetica", 9)
        c.drawString(18, y, "PAGADO:")
        c.drawRightString(ancho - 18, y, f"${float(venta['total_pagado']):.2f}")
        y -= 13
        c.drawString(18, y, "CAMBIO:")
        c.drawRightString(ancho - 18, y, f"${float(venta.get('cambio', 0)):.2f}")
        y -= 18

    c.setFont("Helvetica", 8)
    c.drawCentredString(ancho / 2, y, "No se aceptan cambios ni devoluciones.")
    y -= 12
    c.drawCentredString(ancho / 2, y, "¡Gracias por su compra en Algorrico!")
    c.save()
    return ruta_completa