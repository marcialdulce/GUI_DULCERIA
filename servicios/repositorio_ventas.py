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
        if not id_turno:
            raise ValueError("No hay un turno de caja abierto para registrar esta venta.")

        conexion = conectar_bd()
        if not conexion:
            raise ConnectionError("No se pudo conectar a la base de datos.")
        cursor = None
        try:
            cursor = conexion.cursor()

            # Precios con IVA (16%) incluido: se desglosa sin sumar impuesto extra
            total = round(sum(float(item["subtotal"]) for item in carrito), 2)
            subtotal = round(total / 1.16, 2)
            impuesto = round(total - subtotal, 2)
            folio = self._siguiente_folio(cursor, "ventas", "VTA", 6)

            cursor.execute("""
                INSERT INTO ventas (folio, subtotal, impuesto, id_corte_caja)
                VALUES (%s, %s, %s, %s)
            """, (folio, subtotal, impuesto, id_turno))
            id_venta = cursor.lastrowid

            for item in carrito:
                cantidad = int(item["cantidad"])
                id_prod = item["id_producto"]

                cursor.execute("""
                    SELECT stock_resultante
                    FROM movimientos_inventario
                    WHERE id_producto = %s
                    ORDER BY id_movimiento_inventario DESC
                    LIMIT 1
                    FOR UPDATE
                """, (id_prod,))
                fila_stock = cursor.fetchone()
                stock_actual = int(fila_stock[0]) if fila_stock else 0

                if cantidad > stock_actual:
                    raise ValueError(
                        f"Stock insuficiente para '{item['producto']}'. "
                        f"Disponible: {stock_actual}, solicitado: {cantidad}."
                    )

                cursor.execute("""
                    INSERT INTO detalles_ventas (cantidad, precio_unitario, descuento, subtotal, id_venta, id_producto)
                    VALUES (%s, %s, 0.00, %s, %s, %s)
                """, (cantidad, item["precio_unitario"], item["subtotal"], id_venta, id_prod))
                id_detalle_venta = cursor.lastrowid

                nuevo_stock = stock_actual - cantidad
                cursor.execute("""
                    INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto, id_detalle_venta)
                    VALUES ('salida', %s, %s, %s, %s)
                """, (-cantidad, nuevo_stock, id_prod, id_detalle_venta))

            for p in pagos:
                cursor.execute("""
                    INSERT INTO pagos_ventas (monto, id_venta, id_metodo_pago, id_corte_caja, referencia_pago)
                    VALUES (%s, %s, %s, %s, %s)
                """, (p["monto"], id_venta, p["id_metodo_pago"], id_turno, p.get("referencia")))

            folio_fac = None
            if datos_factura:
                folio_fac = self._siguiente_folio(cursor, "facturas", "FAC", 4, incluir_anio=True)
                cursor.execute("""
                    INSERT INTO facturas (folio, rfc, razon_social, regimen_fiscal, cp_fiscal,
                                          correo, total, id_venta)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    folio_fac,
                    datos_factura["rfc"],
                    datos_factura["razon_social"],
                    datos_factura["regimen"],
                    datos_factura["cp"],
                    datos_factura["correo"],
                    total,
                    id_venta,
                ))

            conexion.commit()

            nombres_metodos = {1: "Efectivo", 2: "Tarjeta de débito", 3: "Tarjeta de crédito"}
            metodos_usados = list(dict.fromkeys(
                nombres_metodos.get(p["id_metodo_pago"], "Efectivo") for p in pagos
            ))
            metodo_resumen = metodos_usados[0] if len(metodos_usados) == 1 else "Pago mixto"
            total_pagado = round(sum(float(p["monto"]) for p in pagos), 2)

            return {
                "id_venta": id_venta,
                "folio": folio,
                "folio_factura": folio_fac,
                "fecha": datetime.now().strftime(FORMATO_FECHA),
                "subtotal": subtotal,
                "impuesto": impuesto,
                "total": total,
                "metodo_pago": metodo_resumen,
                "total_pagado": total_pagado,
                "cambio": round(max(0.0, total_pagado - total), 2),
                "articulos": [dict(item) for item in carrito],
            }
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conexion.is_connected():
                conexion.close()

    def efectivo_turno(self, id_corte_caja):
        conexion = conectar_bd()
        if not conexion:
            return 0.0
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
        if not conexion:
            return 0
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
        if not conexion:
            return
        try:
            cur = conexion.cursor(dictionary=True)
            filtro, params = "", []
            if usuario_filtro:
                filtro = """WHERE v.id_corte_caja IN (
                    SELECT c.id_corte_caja FROM cortes_caja c
                    JOIN usuarios u ON c.id_usuario = u.id_usuario
                    WHERE u.username = %s)"""
                params = [usuario_filtro]

            cur.execute(f"""
                SELECT v.id_venta, v.folio, v.fecha_hora,
                       v.subtotal, v.impuesto, (v.subtotal + v.impuesto) AS total,
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
                v["subtotal"] = float(v["subtotal"])
                v["impuesto"] = float(v["impuesto"])
                v["total"] = float(v["total"])
                yield v, i
        finally:
            conexion.close()

    def obtener_todas(self, limite=50):
        conexion = conectar_bd()
        if not conexion:
            return []
        try:
            cur = conexion.cursor(dictionary=True)
            limite_sql = f"LIMIT {int(limite)}" if limite else ""
            cur.execute(f"""
                SELECT v.id_venta, v.folio, v.fecha_hora,
                       v.subtotal, v.impuesto, (v.subtotal + v.impuesto) AS total,
                       COALESCE((SELECT mp.nombre_metodo_pago FROM pagos_ventas pv
                                 JOIN metodos_pago mp ON pv.id_metodo_pago = mp.id_metodo_pago
                                 WHERE pv.id_venta = v.id_venta LIMIT 1), 'Efectivo') AS metodo_pago,
                       CASE WHEN f.id_factura IS NOT NULL THEN 'Facturada' ELSE 'Sin Factura' END AS estado_factura,
                       f.folio AS folio_factura
                FROM ventas v
                LEFT JOIN facturas f ON v.id_venta = f.id_venta
                ORDER BY v.id_venta DESC
                {limite_sql}
            """)
            rows = cur.fetchall()
            if not rows:
                return []

            ids_venta = [r["id_venta"] for r in rows]
            placeholders = ", ".join(["%s"] * len(ids_venta))
            cur.execute(f"""
                SELECT dv.id_venta, p.nombre_dulce AS producto, dv.cantidad, dv.precio_unitario, dv.subtotal
                FROM detalles_ventas dv
                JOIN productos p ON dv.id_producto = p.id_producto
                WHERE dv.id_venta IN ({placeholders})
            """, tuple(ids_venta))

            detalles_por_venta = {vid: [] for vid in ids_venta}
            for det in cur.fetchall():
                detalles_por_venta[det["id_venta"]].append({
                    "producto": det["producto"],
                    "cantidad": int(det["cantidad"]),
                    "precio_unitario": float(det.get("precio_unitario") or 0),
                    "subtotal": float(det["subtotal"]),
                })

            for r in rows:
                fh = r.get("fecha_hora")
                r["fecha"] = fh.strftime("%Y-%m-%d %H:%M:%S") if hasattr(fh, "strftime") else str(fh or "")
                r["articulos"] = detalles_por_venta.get(r["id_venta"], [])
                r["subtotal"] = float(r.get("subtotal") or 0)
                r["impuesto"] = float(r.get("impuesto") or 0)
                r["total"] = float(r["total"])
            return rows
        finally:
            conexion.close()

    def obtener_por_turno(self, id_corte_caja, limite=200):
        if not id_corte_caja:
            return []
        conexion = conectar_bd()
        if not conexion:
            return []
        try:
            cur = conexion.cursor(dictionary=True)
            limite_sql = f"LIMIT {int(limite)}" if limite else ""
            cur.execute(f"""
                SELECT v.id_venta, v.folio, v.fecha_hora,
                       v.subtotal, v.impuesto, (v.subtotal + v.impuesto) AS total,
                       COALESCE((SELECT mp.nombre_metodo_pago FROM pagos_ventas pv
                                 JOIN metodos_pago mp ON pv.id_metodo_pago = mp.id_metodo_pago
                                 WHERE pv.id_venta = v.id_venta LIMIT 1), 'Efectivo') AS metodo_pago,
                       CASE WHEN f.id_factura IS NOT NULL THEN 'Facturada' ELSE 'Sin Factura' END AS estado_factura,
                       f.folio AS folio_factura
                FROM ventas v
                LEFT JOIN facturas f ON v.id_venta = f.id_venta
                WHERE v.id_corte_caja = %s
                ORDER BY v.id_venta DESC
                {limite_sql}
            """, (id_corte_caja,))
            rows = cur.fetchall()
            if not rows:
                return []

            ids_venta = [r["id_venta"] for r in rows]
            placeholders = ", ".join(["%s"] * len(ids_venta))
            cur.execute(f"""
                SELECT dv.id_venta, p.nombre_dulce AS producto, dv.cantidad, dv.precio_unitario, dv.subtotal
                FROM detalles_ventas dv
                JOIN productos p ON dv.id_producto = p.id_producto
                WHERE dv.id_venta IN ({placeholders})
            """, tuple(ids_venta))

            detalles_por_venta = {vid: [] for vid in ids_venta}
            for det in cur.fetchall():
                detalles_por_venta[det["id_venta"]].append({
                    "producto": det["producto"],
                    "cantidad": int(det["cantidad"]),
                    "precio_unitario": float(det.get("precio_unitario") or 0),
                    "subtotal": float(det["subtotal"]),
                })

            for r in rows:
                fh = r.get("fecha_hora")
                r["fecha"] = fh.strftime("%Y-%m-%d %H:%M:%S") if hasattr(fh, "strftime") else str(fh or "")
                r["articulos"] = detalles_por_venta.get(r["id_venta"], [])
                r["subtotal"] = float(r.get("subtotal") or 0)
                r["impuesto"] = float(r.get("impuesto") or 0)
                r["total"] = float(r["total"])
            return rows
        finally:
            conexion.close()