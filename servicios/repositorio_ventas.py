import uuid
from datetime import datetime
from modelos.conexion import conectar_bd

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

class RepositorioVentas:
    def __init__(self):
        self.conexion_bd = conectar_bd

    def registrar(self, carrito, pagos, id_turno, datos_factura=None):
        from modelos.conexion import conectar_bd
        conexion = conectar_bd()
        if not conexion: raise Exception("No se pudo conectar a la base de datos.")
        
        cursor = None
        try:
            cursor = conexion.cursor()
            
            # --- SOLUCIÓN PARA ADMINISTRADORES ---
            if not id_turno:
                cursor.execute("SELECT MAX(id_corte_caja) FROM cortes_caja")
                resultado = cursor.fetchone()
                id_turno = resultado[0] if (resultado and resultado[0]) else 1

            subtotal = sum(item["subtotal"] for item in carrito)
            impuesto = subtotal * 0.16
            
            cursor.execute("""
                INSERT INTO ventas (subtotal, impuesto, id_corte_caja)
                VALUES (%s, %s, %s)
            """, (subtotal, impuesto, id_turno))
            
            id_venta = cursor.lastrowid
            
            for item in carrito:
                cursor.execute("""
                    INSERT INTO detalles_ventas (cantidad, precio_unitario, descuento, subtotal, id_venta, id_producto)
                    VALUES (%s, %s, 0.00, %s, %s, %s)
                """, (item["cantidad"], item["precio_unitario"], item["subtotal"], id_venta, item["id_producto"]))
                
            for p in pagos:
                cursor.execute("""
                    INSERT INTO pagos_ventas (monto, id_venta, id_metodo_pago, id_corte_caja)
                    VALUES (%s, %s, %s, %s)
                """, (p["monto"], id_venta, p["id_metodo"], id_turno))
                
            if datos_factura:
                cursor.execute("""
                    INSERT INTO facturas (folio, rfc, razon_social, regimen_fiscal, cp_fiscal, correo, total, id_venta)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (datos_factura["folio"], datos_factura["rfc"], datos_factura["razon_social"], 
                      datos_factura["regimen"], datos_factura["cp"], datos_factura["correo"], 
                      subtotal + impuesto, id_venta))
                
            conexion.commit()
            return True
            
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            if cursor: cursor.close()
            if conexion.is_connected(): conexion.close()

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