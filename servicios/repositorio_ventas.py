from datetime import datetime
from modelos.conexion import conectar_bd

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


class RepositorioVentas:
    def __init__(self):
        self.conexion_bd = conectar_bd

    def _siguiente_folio(self, cursor, tabla, prefijo, ancho=6, incluir_anio=False):
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        n = cursor.fetchone()[0] + 1
        if incluir_anio:
            return f"{prefijo}-{datetime.now().year}-{n:0{ancho}d}"
        return f"{prefijo}-{n:0{ancho}d}"

    def registrar(self, carrito, pagos, id_turno, datos_factura=None):
        conexion = conectar_bd()
        if not conexion: raise Exception("No se pudo conectar a la base de datos.")
        cursor = None
        try:
            cursor = conexion.cursor()

            if not id_turno:
                cursor.execute("SELECT MAX(id_corte_caja) FROM cortes_caja")
                r = cursor.fetchone()
                id_turno = r[0] if (r and r[0]) else 1

            subtotal = sum(item["subtotal"] for item in carrito)
            impuesto = subtotal * 0.16
            folio = self._siguiente_folio(cursor, "ventas", "VTA", 6)

            cursor.execute("""
                INSERT INTO ventas (folio, subtotal, impuesto, id_corte_caja)
                VALUES (%s, %s, %s, %s)
            """, (folio, subtotal, impuesto, id_turno))
            id_venta = cursor.lastrowid

            for item in carrito:
                cursor.execute("""
                    INSERT INTO detalles_ventas (cantidad, precio_unitario, descuento, subtotal, id_venta, id_producto)
                    VALUES (%s, %s, 0.00, %s, %s, %s)
                """, (item["cantidad"], item["precio_unitario"], item["subtotal"],
                      id_venta, item["id_producto"]))

            for p in pagos:
                cursor.execute("""
                    INSERT INTO pagos_ventas (monto, id_venta, id_metodo_pago, id_corte_caja, referencia_pago)
                    VALUES (%s, %s, %s, %s, %s)
                """, (p["monto"], id_venta, p["id_metodo_pago"], id_turno, p.get("referencia")))

            if datos_factura:
                folio_fac = self._siguiente_folio(cursor, "facturas", "FAC", 4, incluir_anio=True)
                cursor.execute("""
                    INSERT INTO facturas (folio, rfc, razon_social, regimen_fiscal, cp_fiscal,
                                          correo, total, id_venta)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (folio_fac, datos_factura["rfc"], datos_factura["razon_social"],
                      datos_factura["regimen"], datos_factura["cp"],
                      datos_factura["correo"], subtotal + impuesto, id_venta))

            conexion.commit()
            return folio
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
            ev = float(cur.fetchone()[0])
            cur.execute("SELECT COALESCE(SUM(monto), 0) FROM pagos_apartados WHERE id_corte_caja = %s AND id_metodo_pago = 1", (id_corte_caja,))
            ea = float(cur.fetchone()[0])
            return ev + ea
        finally:
            conexion.close()

    def tamano_actual(self, usuario_filtro=None):
        conexion = conectar_bd()
        if not conexion: return 0
        try:
            cur = conexion.cursor()
            if usuario_filtro:
                cur.execute("""
                    SELECT COUNT(*) FROM ventas v
                    JOIN cortes_caja c ON v.id_corte_caja = c.id_corte_caja
                    JOIN usuarios u ON c.id_usuario = u.id_usuario
                    WHERE u.username = %s
                """, (usuario_filtro,))
            else:
                cur.execute("SELECT COUNT(*) FROM ventas")
            return cur.fetchone()[0]
        finally:
            conexion.close()

    def iterar(self, limite, usuario_filtro=None):
        conexion = conectar_bd()
        if not conexion: return
        try:
            cur = conexion.cursor(dictionary=True)
            filtro, params = "", []
            if usuario_filtro:
                filtro = """WHERE v.id_corte_caja IN (
                    SELECT c.id_corte_caja FROM cortes_caja c
                    JOIN usuarios u ON c.id_usuario = u.id_usuario
                    WHERE u.username = %s)"""
                params = [usuario_filtro]
            
            # Corregido: Sin DATE_FORMAT de SQL, se maneja en Python
            cur.execute(f"""
                SELECT v.id_venta, v.folio, v.fecha_hora,
                       v.subtotal, (v.subtotal + v.impuesto) AS total,
                       COALESCE((SELECT mp.nombre_metodo_pago FROM pagos_ventas pv
                                 JOIN metodos_pago mp ON pv.id_metodo_pago = mp.id_metodo_pago
                                 WHERE pv.id_venta = v.id_venta LIMIT 1), 'Efectivo') AS metodo_pago
                FROM ventas v {filtro}
                ORDER BY v.fecha_hora LIMIT %s
            """, params + [limite])
            
            ventas = cur.fetchall()
            for i, v in enumerate(ventas, 1):
                v["fecha"] = v["fecha_hora"].strftime("%Y-%m-%d %H:%M:%S") if v.get("fecha_hora") else ""
                cur.execute("""
                    SELECT p.nombre_dulce AS producto, dv.cantidad, dv.subtotal
                    FROM detalles_ventas dv
                    JOIN productos p ON dv.id_producto = p.id_producto
                    WHERE dv.id_venta = %s
                """, (v["id_venta"],))
                v["articulos"] = cur.fetchall()
                v["total"] = float(v["total"])
                yield v, i
        finally:
            conexion.close()

    def obtener_todas(self):
        conexion = conectar_bd()
        if not conexion: return []
        try:
            cur = conexion.cursor(dictionary=True)
            # Corregido: Sin DATE_FORMAT de SQL, se maneja en Python
            cur.execute("""
                SELECT v.id_venta, v.folio, v.fecha_hora,
                       v.subtotal, (v.subtotal + v.impuesto) AS total,
                       COALESCE((SELECT mp.nombre_metodo_pago FROM pagos_ventas pv
                                 JOIN metodos_pago mp ON pv.id_metodo_pago = mp.id_metodo_pago
                                 WHERE pv.id_venta = v.id_venta LIMIT 1), 'Efectivo') AS metodo_pago,
                       CASE WHEN f.id_factura IS NOT NULL THEN 'Facturada' ELSE 'Sin Factura' END AS estado_factura
                FROM ventas v
                LEFT JOIN facturas f ON v.id_venta = f.id_venta
                ORDER BY v.fecha_hora DESC
            """)
            rows = cur.fetchall()
            for r in rows:
                r["fecha"] = r["fecha_hora"].strftime("%Y-%m-%d %H:%M:%S") if r.get("fecha_hora") else ""
                cur.execute("""
                    SELECT p.nombre_dulce AS producto, dv.cantidad, dv.subtotal
                    FROM detalles_ventas dv
                    JOIN productos p ON dv.id_producto = p.id_producto
                    WHERE dv.id_venta = %s
                """, (r["id_venta"],))
                r["articulos"] = cur.fetchall()
                r["total"] = float(r["total"])
            return rows
        finally:
            conexion.close()