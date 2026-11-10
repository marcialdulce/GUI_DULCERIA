import uuid
from datetime import datetime
from modelos.conexion import conectar_bd

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

class RepositorioVentas:
    def __init__(self):
        self.conexion_bd = conectar_bd

    def registrar(self, articulos, pagos, id_corte_caja, datos_factura=None):
        conexion = conectar_bd()
        if not conexion:
            raise ConnectionError("No hay conexión con la base de datos.")
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)
            folio = "V-" + uuid.uuid4().hex[:8].upper()
            fecha_hora = datetime.now().strftime(FORMATO_FECHA)
            
            subtotal = sum(a["subtotal"] for a in articulos)
            impuesto = round(subtotal * 0.16, 2)

            cursor.execute("""
                INSERT INTO ventas (folio, fecha_hora, subtotal, impuesto, id_corte_caja)
                VALUES (%s,%s,%s,%s,%s)""", (folio, fecha_hora, subtotal, impuesto, id_corte_caja))
            id_venta = cursor.lastrowid

            for art in articulos:
                cursor.execute("""
                    INSERT INTO detalles_ventas (cantidad, precio_unitario, subtotal, id_venta, id_producto)
                    VALUES (%s,%s,%s,%s,%s)""", (art["cantidad"], art["precio_unitario"], art["subtotal"], id_venta, art["id_producto"]))
                id_detalle_venta = cursor.lastrowid

                cursor.execute("SELECT stock_resultante FROM movimientos_inventario WHERE id_producto = %s ORDER BY id_movimiento_inventario DESC LIMIT 1", (art["id_producto"],))
                res_stock = cursor.fetchone()
                stock_actual = res_stock["stock_resultante"] if res_stock else 0
                nuevo_stock = stock_actual - art["cantidad"]

                cursor.execute("""
                    INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto, id_detalle_venta)
                    VALUES ('salida', %s, %s, %s, %s)""", (-art["cantidad"], nuevo_stock, art["id_producto"], id_detalle_venta))

            for pago in pagos:
                cursor.execute("""
                    INSERT INTO pagos_ventas (monto, id_venta, id_metodo_pago, id_corte_caja, referencia_pago)
                    VALUES (%s,%s,%s,%s,%s)""", (pago["monto"], id_venta, pago["id_metodo_pago"], id_corte_caja, pago.get("referencia", None)))

            if datos_factura and datos_factura.get("requiere"):
                cursor.execute("""
                    INSERT INTO facturas (folio, rfc, razon_social, regimen_fiscal, cp_fiscal, correo, total, id_venta)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", (
                    f"FAC-{folio}", datos_factura["rfc"], datos_factura.get("razon_social", "Público General"), 
                    datos_factura.get("regimen", "626"), datos_factura.get("cp", "39360"), 
                    datos_factura.get("correo", ""), subtotal + impuesto, id_venta))

            conexion.commit()
            return {"id_venta": id_venta, "folio": folio}
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            if cursor: cursor.close()
            conexion.close()

    def efectivo_turno(self, id_corte_caja):
        conexion = conectar_bd()
        if not conexion: return 0.0
        try:
            cur = conexion.cursor()
            cur.execute("SELECT COALESCE(SUM(monto), 0) FROM pagos_ventas WHERE id_corte_caja = %s AND id_metodo_pago = 1", (id_corte_caja,))
            efectivo_ventas = float(cur.fetchone()[0])
            cur.execute("SELECT COALESCE(SUM(monto), 0) FROM pagos_apartados WHERE id_corte_caja = %s AND id_metodo_pago = 1", (id_corte_caja,))
            efectivo_apartados = float(cur.fetchone()[0])
            return efectivo_ventas + efectivo_apartados
        finally:
            conexion.close()
            
    def obtener_todas(self):
        """Consulta todas las ventas registradas con su estado de facturación."""
        query = """
            SELECT 
                v.id_venta,
                v.folio,
                v.fecha_hora,
                v.subtotal,
                (v.subtotal + v.impuesto) AS total,
                CASE WHEN f.id_factura IS NOT NULL THEN 'Facturada' ELSE 'Sin Factura' END AS estado_factura
            FROM ventas v
            LEFT JOIN facturas f ON v.id_venta = f.id_venta
            ORDER BY v.fecha_hora DESC
        """
        return self._ejecutar_consulta(query, fetch=True)