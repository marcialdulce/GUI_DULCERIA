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

            cursor.close()
            cursor = conexion.cursor(dictionary=True)

            subtotal = round(sum(float(item["subtotal"]) for item in carrito), 2)
            impuesto = round(subtotal * 0.16, 2)
            total = round(subtotal + impuesto, 2)

            # Bloquea los productos (en orden) para que dos cajas no vendan la misma existencia
            ids = sorted({item["id_producto"] for item in carrito})
            cursor.execute("SELECT id_producto FROM productos WHERE id_producto IN (%s) ORDER BY id_producto FOR UPDATE"
                           % ",".join(["%s"] * len(ids)), tuple(ids))
            cursor.fetchall()

            # ventas.folio es NOT NULL y UNIQUE: se pone uno temporal y luego VTA-000001 (= id de la venta)
            cursor.execute("INSERT INTO ventas (folio, subtotal, impuesto, id_corte_caja) VALUES (%s, %s, %s, %s)",
                           ("TMP-" + uuid.uuid4().hex[:12], subtotal, impuesto, id_turno))
            id_venta = cursor.lastrowid
            cursor.execute("UPDATE ventas SET folio = %s WHERE id_venta = %s", (f"VTA-{id_venta:06d}", id_venta))

            for item in carrito:
                cursor.execute("""
                    INSERT INTO detalles_ventas (cantidad, precio_unitario, descuento, subtotal, id_venta, id_producto)
                    VALUES (%s, %s, 0.00, %s, %s, %s)
                """, (item["cantidad"], item["precio_unitario"], item["subtotal"], id_venta, item["id_producto"]))
                self._descontar_stock(cursor, item, cursor.lastrowid)

            # Los pagos deben sumar el total: si pagó de más en efectivo, el cambio no se registra
            exceso = round(sum(float(p["monto"]) for p in pagos) - total, 2)
            for p in pagos:
                monto = float(p["monto"])
                id_metodo = p.get("id_metodo_pago", p.get("id_metodo"))
                if exceso > 0 and id_metodo == 1:
                    quitar = min(exceso, monto)
                    monto, exceso = round(monto - quitar, 2), round(exceso - quitar, 2)
                if monto <= 0:
                    continue
                cursor.execute("""
                    INSERT INTO pagos_ventas (monto, referencia_pago, id_venta, id_metodo_pago, id_corte_caja)
                    VALUES (%s, %s, %s, %s, %s)
                """, (monto, p.get("referencia") or None, id_venta, id_metodo, id_turno))

            if datos_factura:
                cursor.execute("""
                    INSERT INTO facturas (folio, rfc, razon_social, regimen_fiscal, cp_fiscal, correo, total, id_venta)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (self._siguiente_folio_factura(cursor), datos_factura["rfc"].strip().upper(),
                      datos_factura["razon_social"], datos_factura["regimen"], datos_factura["cp"],
                      datos_factura["correo"], total, id_venta))

            conexion.commit()
            return True
            
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            if cursor: cursor.close()
            if conexion.is_connected(): conexion.close()

    @staticmethod
    def _descontar_stock(cursor, item, id_detalle_venta):
        """Salida de inventario por la venta (el stock = stock_resultante del último movimiento)."""
        cursor.execute("SELECT stock_resultante FROM movimientos_inventario WHERE id_producto = %s "
                       "ORDER BY id_movimiento_inventario DESC LIMIT 1", (item["id_producto"],))
        fila = cursor.fetchone()
        stock = int(fila["stock_resultante"]) if fila else 0
        if item["cantidad"] > stock:
            raise ValueError(f"Stock insuficiente de '{item.get('producto', item['id_producto'])}' (hay {stock}).")
        cursor.execute("""
            INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto, id_detalle_venta)
            VALUES ('salida', %s, %s, %s, %s)
        """, (item["cantidad"], stock - item["cantidad"], item["id_producto"], id_detalle_venta))

    @staticmethod
    def _siguiente_folio_factura(cursor):
        prefijo = f"FAC-{datetime.now().year}-"
        cursor.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(folio, %s) AS UNSIGNED)), 0) + 1 AS n "
                       "FROM facturas WHERE folio LIKE %s", (len(prefijo) + 1, prefijo + "%"))
        return f"{prefijo}{int(cursor.fetchone()['n']):04d}"

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