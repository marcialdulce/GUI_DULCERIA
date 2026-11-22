import time
from modelos.conexion import conectar_bd
from seguridad import verificar_password

SEGUNDOS_CACHE_INVENTARIO = 30


class ModeloDulceria:
    def __init__(self):
        self.conexion_bd = conectar_bd
        self.ticket_actual = []
        self._cache_inventario = None
        self._cache_inventario_hora = 0.0

    def _ejecutar_consulta(self, query, parametros=None, fetch=False, fetchall=False):
        conexion = conectar_bd()
        if not conexion:
            return None
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True, buffered=True)
            cursor.execute(query, parametros or ())
            if fetch:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            conexion.commit()
            self.invalidar_inventario()
            return cursor.lastrowid or True
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conexion.is_connected():
                conexion.close()

    def validar_usuario(self, username, password):
        query = "SELECT id_usuario, id_rol, password_hash FROM usuarios WHERE username = %s AND estado = 'activo'"
        resultado = self._ejecutar_consulta(query, (username.strip(),), fetch=True)
        if resultado and verificar_password(password, resultado["password_hash"]):
            return resultado
        return None

    def obtener_rol(self, id_rol):
        resultado = self._ejecutar_consulta("SELECT nombre_rol FROM roles WHERE id_rol = %s", (id_rol,), fetch=True)
        return resultado["nombre_rol"] if resultado else "Cajero"

    def invalidar_inventario(self):
        self._cache_inventario = None

    @property
    def inventario(self):
        vencido = (time.monotonic() - self._cache_inventario_hora) > SEGUNDOS_CACHE_INVENTARIO
        if self._cache_inventario is None or vencido:
            self._cache_inventario = self._consultar_inventario()
            self._cache_inventario_hora = time.monotonic()
        return self._cache_inventario

    def _consultar_inventario(self):
        query = """
            SELECT p.id_producto, p.codigo_barras, p.nombre_dulce AS nombre,
                   m.nombre_marca AS marca, c.nombre_categoria AS categoria,
                   p.precio_venta AS precio, p.stock_minimo,
                   p.id_marca, p.id_categoria, p.id_unidad, p.id_proveedor,
                   COALESCE((
                       SELECT stock_resultante FROM movimientos_inventario mi
                       WHERE mi.id_producto = p.id_producto
                       ORDER BY mi.id_movimiento_inventario DESC LIMIT 1
                   ), 0) AS stock_actual
            FROM productos p
            LEFT JOIN marcas m ON p.id_marca = m.id_marca
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE p.estado = 'activo' ORDER BY p.nombre_dulce
        """
        filas = self._ejecutar_consulta(query, fetchall=True) or []
        for f in filas:
            f["precio"] = float(f["precio"])
            f["stock"] = int(f["stock_actual"])
        return filas

    # ---------------- CRUD de Productos (Con Stock Actual) ----------------
    def crear_producto(self, datos):
        codigo = str(datos.get("codigo_barras") or "").strip()
        if not codigo:
            return False, "El código de barras es obligatorio."

        con = conectar_bd()
        if not con:
            return False, "No se pudo conectar a la base de datos."
        cur = None
        try:
            cur = con.cursor()
            cur.execute("""
                INSERT INTO productos
                (codigo_barras, nombre_dulce, precio_venta, stock_minimo, estado,
                 id_marca, id_categoria, id_unidad, id_proveedor)
                VALUES (%s, %s, %s, %s, 'activo', %s, %s, %s, %s)
            """, (
                codigo,
                datos["nombre_dulce"],
                datos["precio_venta"],
                datos.get("stock_minimo", 5),
                datos.get("id_marca"),
                datos.get("id_categoria"),
                datos.get("id_unidad"),
                datos.get("id_proveedor"),
            ))
            id_nuevo = cur.lastrowid
            stock_inicial = int(datos.get("stock_actual", 0))
            if stock_inicial > 0:
                cur.execute("""
                    INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto)
                    VALUES ('entrada', %s, %s, %s)
                """, (stock_inicial, stock_inicial, id_nuevo))

            con.commit()
            self.invalidar_inventario()
            return True, f"Producto creado exitosamente con stock inicial de {stock_inicial} unidades."
        except Exception as e:
            con.rollback()
            if "Duplicate entry" in str(e):
                return False, f"Ya existe un producto con el código de barras '{codigo}'."
            return False, f"Error al crear el producto: {str(e)}"
        finally:
            if cur:
                cur.close()
            if con.is_connected():
                con.close()

    def actualizar_producto(self, id_producto, datos):
        codigo = str(datos.get("codigo_barras") or "").strip()
        if not codigo:
            return False, "El código de barras es obligatorio."

        con = conectar_bd()
        if not con:
            return False, "No se pudo conectar a la base de datos."
        cur = None
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("""
                UPDATE productos
                SET codigo_barras=%s, nombre_dulce=%s, precio_venta=%s, stock_minimo=%s,
                    id_marca=%s, id_categoria=%s, id_unidad=%s, id_proveedor=%s
                WHERE id_producto=%s
            """, (
                codigo,
                datos["nombre_dulce"],
                datos["precio_venta"],
                datos.get("stock_minimo", 5),
                datos.get("id_marca"),
                datos.get("id_categoria"),
                datos.get("id_unidad"),
                datos.get("id_proveedor"),
                id_producto,
            ))

            if "stock_actual" in datos:
                nuevo_stock = int(datos["stock_actual"])
                cur.execute("""
                    SELECT stock_resultante
                    FROM movimientos_inventario
                    WHERE id_producto = %s
                    ORDER BY id_movimiento_inventario DESC
                    LIMIT 1
                """, (id_producto,))
                fila = cur.fetchone()
                stock_previo = int(fila["stock_resultante"]) if fila else 0
                diferencia = nuevo_stock - stock_previo
                if diferencia != 0:
                    cur.execute("""
                        INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto)
                        VALUES ('ajuste', %s, %s, %s)
                    """, (diferencia, nuevo_stock, id_producto))

            con.commit()
            self.invalidar_inventario()
            return True, "Producto y existencias actualizados exitosamente."
        except Exception as e:
            con.rollback()
            if "Duplicate entry" in str(e):
                return False, f"Ya existe otro producto con el código de barras '{codigo}'."
            return False, f"Error al actualizar el producto: {str(e)}"
        finally:
            if cur:
                cur.close()
            if con.is_connected():
                con.close()

    # ---------------- Catálogos ----------------
    def obtener_marcas(self):
        query = "SELECT id_marca AS id, nombre_marca AS nombre FROM marcas ORDER BY nombre_marca"
        return self._ejecutar_consulta(query, fetchall=True) or []

    def obtener_categorias(self):
        query = "SELECT id_categoria AS id, nombre_categoria AS nombre FROM categorias ORDER BY nombre_categoria"
        return self._ejecutar_consulta(query, fetchall=True) or []

    def obtener_unidades(self):
        query = "SELECT id_unidad AS id, nombre_unidad AS nombre FROM unidades ORDER BY nombre_unidad"
        return self._ejecutar_consulta(query, fetchall=True) or []

    def eliminar_producto(self, id_producto):
        con = conectar_bd()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("""
                SELECT stock_resultante
                FROM movimientos_inventario
                WHERE id_producto=%s
                ORDER BY id_movimiento_inventario DESC
                LIMIT 1
            """, (id_producto,))
            res = cur.fetchone()
            stock_actual = res["stock_resultante"] if res else 0

            if stock_actual > 0:
                cur.execute("""
                    INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto)
                    VALUES ('ajuste', %s, 0, %s)
                """, (-stock_actual, id_producto))

            cur.execute("UPDATE productos SET estado='inactivo' WHERE id_producto=%s", (id_producto,))
            con.commit()
            self.invalidar_inventario()
            return True, "Producto eliminado y stock ajustado a 0 correctamente."
        except Exception as e:
            con.rollback()
            return False, f"Error al eliminar producto: {str(e)}"
        finally:
            if con.is_connected():
                con.close()

    def registrar_merma(self, id_producto, cantidad, motivo="Merma manual"):
        con = conectar_bd()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("""
                SELECT stock_resultante
                FROM movimientos_inventario
                WHERE id_producto=%s
                ORDER BY id_movimiento_inventario DESC
                LIMIT 1
            """, (id_producto,))
            res = cur.fetchone()
            stock_actual = res["stock_resultante"] if res else 0
            if cantidad > stock_actual:
                return False, "No puedes mermar más de lo que tienes en stock."

            nuevo_stock = stock_actual - cantidad
            cur.execute("""
                INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto)
                VALUES ('ajuste', %s, %s, %s)
            """, (-cantidad, nuevo_stock, id_producto))

            con.commit()
            self.invalidar_inventario()
            return True, f"Merma registrada correctamente ({motivo})."
        except Exception as e:
            con.rollback()
            return False, str(e)
        finally:
            if con.is_connected():
                con.close()

    # ---------------- Carrito y Cálculo con IVA Incluido ----------------
    def agregar_al_ticket(self, nombre_producto, cantidad):
        prod = next((p for p in self.inventario if p["nombre"] == nombre_producto), None)
        if not prod:
            return "no_encontrado"
        item = next((i for i in self.ticket_actual if i["producto"] == nombre_producto), None)
        cant_actual = item["cantidad"] if item else 0
        if (cant_actual + cantidad) > prod["stock"]:
            return "stock_insuficiente"
        if item:
            item["cantidad"] += cantidad
            item["subtotal"] = round(item["cantidad"] * prod["precio"], 2)
        else:
            self.ticket_actual.append({
                "id_producto": prod["id_producto"],
                "producto": nombre_producto,
                "cantidad": cantidad,
                "precio_unitario": prod["precio"],
                "subtotal": round(prod["precio"] * cantidad, 2),
            })
        return True

    def calcular_total(self):
        return round(sum(float(i["subtotal"]) for i in self.ticket_actual), 2)

    def calcular_desglose(self):
        total = round(sum(float(i["subtotal"]) for i in self.ticket_actual), 2)
        subtotal = round(total / 1.16, 2)
        iva = round(total - subtotal, 2)
        return subtotal, iva, total

    def actualizar_cantidad_ticket(self, nombre_producto, delta):
        item = next((i for i in self.ticket_actual if i["producto"] == nombre_producto), None)
        if not item:
            return False, "El artículo no está en el carrito."

        nueva_cantidad = int(item["cantidad"]) + int(delta)
        if nueva_cantidad <= 0:
            self.ticket_actual.remove(item)
            return True, "eliminado"

        if delta > 0:
            prod = next((p for p in self.inventario if p["nombre"] == nombre_producto), None)
            if not prod or nueva_cantidad > prod["stock"]:
                disponible = prod["stock"] if prod else 0
                return False, f"Stock máximo alcanzado ({disponible} disponibles)."

        item["cantidad"] = nueva_cantidad
        item["subtotal"] = round(nueva_cantidad * float(item["precio_unitario"]), 2)
        return True, "ok"

    def quitar_del_ticket(self, nombre_producto):
        for i, item in enumerate(self.ticket_actual):
            if item["producto"] == nombre_producto:
                self.ticket_actual.pop(i)
                return True
        return False

    # ---------------- Reportes por Año / Mes / Día ----------------
    def _clausula_fecha(self, columna, anio=None, mes=None, dia=None):
        condiciones, params = [], []
        if anio:
            condiciones.append(f"YEAR({columna}) = %s")
            params.append(int(anio))
        if mes:
            condiciones.append(f"MONTH({columna}) = %s")
            params.append(int(mes))
        if dia:
            condiciones.append(f"DAY({columna}) = %s")
            params.append(int(dia))
        where_extra = (" AND " + " AND ".join(condiciones)) if condiciones else ""
        return where_extra, params

    def obtener_anios_disponibles(self):
        filas = self._ejecutar_consulta("""
            SELECT DISTINCT YEAR(fecha_hora) AS anio FROM ventas
            UNION
            SELECT DISTINCT YEAR(fecha_hora_apartado) AS anio FROM apartados
            ORDER BY anio DESC
        """, fetchall=True) or []
        return [str(f["anio"]) for f in filas if f.get("anio")]

    def obtener_reporte_ganancias(self, anio=None, mes=None, dia=None):
        where_v, params_v = self._clausula_fecha("v.fecha_hora", anio, mes, dia)
        where_a, params_a = self._clausula_fecha("a.fecha_hora_apartado", anio, mes, dia)
        where_pa, params_pa = self._clausula_fecha("pa.fecha_hora", anio, mes, dia)
        where_f, params_f = self._clausula_fecha("f.fecha_hora_emision", anio, mes, dia)
        where_m, params_m = self._clausula_fecha("mi.fecha_hora_movimiento", anio, mes, dia)

        lista = self._ejecutar_consulta(f"""
            SELECT p.nombre_dulce,
                   SUM(dv.cantidad) AS unidades_vendidas,
                   SUM(dv.subtotal) AS ingresos_totales,
                   COALESCE((
                       SELECT dpp.costo_unitario
                       FROM detalles_pedidos_proveedores dpp
                       WHERE dpp.id_producto = p.id_producto
                       ORDER BY dpp.id_detalle_pedido_proveedor DESC
                       LIMIT 1
                   ), 0) AS costo_unitario
            FROM ventas v
            JOIN detalles_ventas dv ON v.id_venta = dv.id_venta
            JOIN productos p ON dv.id_producto = p.id_producto
            WHERE 1=1 {where_v}
            GROUP BY p.id_producto, p.nombre_dulce
            ORDER BY ingresos_totales DESC
        """, tuple(params_v), fetchall=True) or []

        ingreso_total = 0.0
        costo_total = 0.0
        dulces_vendidos = 0
        for prod in lista:
            uds = int(prod["unidades_vendidas"] or 0)
            ing = float(prod["ingresos_totales"] or 0)
            c_unit = float(prod["costo_unitario"] or 0)
            costo_prod = round(uds * c_unit, 2)
            ganancia = round(ing - costo_prod, 2)

            prod["unidades_vendidas"] = uds
            prod["ingresos_totales"] = round(ing, 2)
            prod["costo_unitario"] = round(c_unit, 2)
            prod["ganancia_neta"] = ganancia
            prod["ganancia_bruta"] = ganancia
            prod["producto"] = prod["nombre_dulce"]

            dulces_vendidos += uds
            ingreso_total += ing
            costo_total += costo_prod

        res_ventas = self._ejecutar_consulta(f"""
            SELECT COUNT(*) AS num_ventas,
                   COALESCE(SUM(v.subtotal + v.impuesto), 0) AS total_con_iva
            FROM ventas v
            WHERE 1=1 {where_v}
        """, tuple(params_v), fetch=True) or {}

        res_apartados = self._ejecutar_consulta(f"""
            SELECT COUNT(*) AS total_apartados,
                   SUM(CASE WHEN a.estado = 'pendiente' THEN 1 ELSE 0 END) AS pendientes,
                   SUM(CASE WHEN a.estado = 'liquidado' THEN 1 ELSE 0 END) AS liquidados,
                   SUM(CASE WHEN a.estado = 'cancelado' THEN 1 ELSE 0 END) AS cancelados
            FROM apartados a
            WHERE 1=1 {where_a}
        """, tuple(params_a), fetch=True) or {}

        res_pagos_ap = self._ejecutar_consulta(f"""
            SELECT COALESCE(SUM(pa.monto), 0) AS cobrado_apartados
            FROM pagos_apartados pa
            WHERE 1=1 {where_pa}
        """, tuple(params_pa), fetch=True) or {}

        res_facturas = self._ejecutar_consulta(f"""
            SELECT COUNT(*) AS num_facturas
            FROM facturas f
            WHERE 1=1 {where_f}
        """, tuple(params_f), fetch=True) or {}

        res_mermas = self._ejecutar_consulta(f"""
            SELECT COALESCE(SUM(ABS(mi.cantidad)), 0) AS mermas
            FROM movimientos_inventario mi
            WHERE mi.tipo = 'ajuste' AND mi.cantidad < 0 {where_m}
        """, tuple(params_m), fetch=True) or {}

        return {
            "ingreso_total": round(ingreso_total, 2),
            "costo_total": round(costo_total, 2),
            "utilidad_bruta": round(ingreso_total - costo_total, 2),
            "num_ventas": int(res_ventas.get("num_ventas") or 0),
            "total_cobrado_ventas": round(float(res_ventas.get("total_con_iva") or 0), 2),
            "dulces_vendidos": dulces_vendidos,
            "num_apartados": int(res_apartados.get("total_apartados") or 0),
            "apartados_pendientes": int(res_apartados.get("pendientes") or 0),
            "apartados_liquidados": int(res_apartados.get("liquidados") or 0),
            "apartados_cancelados": int(res_apartados.get("cancelados") or 0),
            "ingresos_apartados": round(float(res_pagos_ap.get("cobrado_apartados") or 0), 2),
            "num_facturas": int(res_facturas.get("num_facturas") or 0),
            "mermas_unidades": int(res_mermas.get("mermas") or 0),
            "detalle": lista,
        }

    def obtener_datos_grafica(self, anio=None, mes=None, dia=None, caja_filtro=None):
        where_v, params = self._clausula_fecha("v.fecha_hora", anio, mes, dia)
        query = f"""
            SELECT ca.numero_caja, SUM(dv.subtotal) AS ingresos_totales
            FROM ventas v
            JOIN detalles_ventas dv ON v.id_venta = dv.id_venta
            JOIN cortes_caja c ON v.id_corte_caja = c.id_corte_caja
            JOIN cajas ca ON c.id_caja = ca.id_caja
            WHERE 1=1 {where_v}
        """
        if caja_filtro and caja_filtro != "Todas":
            query += " AND ca.numero_caja = %s"
            params.append(caja_filtro)
        query += " GROUP BY ca.numero_caja ORDER BY ca.numero_caja ASC"
        return self._ejecutar_consulta(query, tuple(params), fetchall=True) or []

    # ---------------- Proveedores y Pedidos ----------------
    def obtener_proveedores(self):
        return self._ejecutar_consulta("SELECT id_proveedor AS id, empresa AS nombre, telefono, correo FROM proveedores ORDER BY empresa", fetchall=True) or []

    def obtener_productos_proveedor(self, id_proveedor):
        return self._ejecutar_consulta("""
            SELECT p.id_producto AS id, p.nombre_dulce AS nombre, p.precio_venta,
                   COALESCE((SELECT costo_unitario FROM detalles_pedidos_proveedores dpp
                             WHERE dpp.id_producto = p.id_producto
                             ORDER BY id_detalle_pedido_proveedor DESC LIMIT 1),
                            p.precio_venta * 0.6) AS costo
            FROM productos p WHERE p.id_proveedor = %s AND p.estado = 'activo'
        """, (id_proveedor,), fetchall=True) or []

    def obtener_pedidos_activos(self):
        return self._ejecutar_consulta("""
            SELECT pp.id_pedido_proveedor AS id_pedido,
                   prov.empresa AS proveedor,
                   GROUP_CONCAT(CONCAT(p.nombre_dulce, ' (x', dpp.cantidad, ')') SEPARATOR ', ') AS productos,
                   SUM(dpp.cantidad) AS total_piezas,
                   pp.estado,
                   (pp.subtotal + pp.impuesto) AS total
            FROM pedidos_proveedores pp
            JOIN proveedores prov ON pp.id_proveedor = prov.id_proveedor
            JOIN detalles_pedidos_proveedores dpp ON pp.id_pedido_proveedor = dpp.id_pedido_proveedor
            JOIN productos p ON dpp.id_producto = p.id_producto
            WHERE pp.estado = 'solicitado'
            GROUP BY pp.id_pedido_proveedor, prov.empresa, pp.estado, pp.subtotal, pp.impuesto
            ORDER BY pp.id_pedido_proveedor DESC
        """, fetchall=True) or []

    def recibir_pedido_proveedor(self, id_pedido):
        con = conectar_bd()
        if not con:
            return False, "No se pudo conectar a la base de datos."
        cur = None
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT estado FROM pedidos_proveedores WHERE id_pedido_proveedor = %s FOR UPDATE", (id_pedido,))
            pedido = cur.fetchone()
            if not pedido:
                return False, f"No se encontró el pedido #{id_pedido}."
            if pedido["estado"] != "solicitado":
                return False, f"El pedido #{id_pedido} ya se encuentra en estado '{pedido['estado']}'."

            cur.execute("""
                SELECT id_producto, cantidad, id_detalle_pedido_proveedor
                FROM detalles_pedidos_proveedores
                WHERE id_pedido_proveedor = %s
            """, (id_pedido,))
            detalles = cur.fetchall()
            if not detalles:
                return False, f"El pedido #{id_pedido} no tiene productos registrados."

            piezas_recibidas = 0
            for det in detalles:
                cant = int(det["cantidad"])
                cur.execute("""
                    SELECT stock_resultante
                    FROM movimientos_inventario
                    WHERE id_producto = %s
                    ORDER BY id_movimiento_inventario DESC
                    LIMIT 1
                    FOR UPDATE
                """, (det["id_producto"],))
                r = cur.fetchone()
                stock_actual = int(r["stock_resultante"]) if r else 0
                cur.execute("""
                    INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto, id_detalle_pedido_proveedor)
                    VALUES ('entrada', %s, %s, %s, %s)
                """, (cant, stock_actual + cant, det["id_producto"], det["id_detalle_pedido_proveedor"]))
                piezas_recibidas += cant

            cur.execute("UPDATE pedidos_proveedores SET estado='recibido' WHERE id_pedido_proveedor=%s", (id_pedido,))
            con.commit()
            self.invalidar_inventario()
            return True, f"Pedido #{id_pedido} recibido correctamente. Se sumaron {piezas_recibidas} piezas al inventario."
        except Exception as e:
            con.rollback()
            return False, f"Error al recibir mercancía: {e}"
        finally:
            if cur:
                cur.close()
            if con.is_connected():
                con.close()

    def eliminar_proveedor(self, id_proveedor):
        try:
            self._ejecutar_consulta("DELETE FROM proveedores WHERE id_proveedor = %s", (id_proveedor,))
            return True
        except Exception as e:
            print(f"Error al eliminar proveedor: {e}")
            return False

    def crear_proveedor(self, empresa, telefono, correo):
        query = "INSERT INTO proveedores (empresa, telefono, correo) VALUES (%s, %s, %s)"
        try:
            self._ejecutar_consulta(query, (empresa.strip(), telefono.strip() or None, correo.strip() or None))
            return True, "Proveedor registrado correctamente."
        except Exception as e:
            if "Duplicate entry" in str(e):
                return False, f"Ya existe un proveedor registrado con el nombre '{empresa}'."
            return False, f"Error al registrar proveedor: {e}"

    def actualizar_proveedor(self, id_proveedor, empresa, telefono, correo):
        query = "UPDATE proveedores SET empresa=%s, telefono=%s, correo=%s WHERE id_proveedor=%s"
        try:
            self._ejecutar_consulta(query, (empresa.strip(), telefono.strip() or None, correo.strip() or None, id_proveedor))
            return True, "Proveedor actualizado correctamente."
        except Exception as e:
            if "Duplicate entry" in str(e):
                return False, f"Ya existe otro proveedor con el nombre '{empresa}'."
            return False, f"Error al actualizar proveedor: {e}"

    # ---------------- Apartados y Turnos de Caja ----------------
    def obtener_apartados(self):
        return self._ejecutar_consulta("""
            SELECT a.id_apartado,
                   a.nombre_cliente AS nombre,
                   DATE_FORMAT(a.fecha_entrega, '%d/%m/%Y') AS fecha,
                   a.estado,
                   GROUP_CONCAT(CONCAT(p.nombre_dulce, ' (x', da.cantidad, ')') SEPARATOR ', ') AS producto,
                   SUM(da.cantidad) AS unidades,
                   a.subtotal,
                   a.impuesto,
                   COALESCE((SELECT SUM(pa.monto) FROM pagos_apartados pa
                             WHERE pa.id_apartado = a.id_apartado), 0) AS pagado
            FROM apartados a
            JOIN detalles_apartados da ON a.id_apartado = da.id_apartado
            JOIN productos p ON da.id_producto = p.id_producto
            GROUP BY a.id_apartado, a.nombre_cliente, a.fecha_entrega, a.estado, a.subtotal, a.impuesto
            ORDER BY FIELD(a.estado, 'pendiente', 'liquidado', 'cancelado'), a.fecha_entrega ASC
        """, fetchall=True) or []

    def obtener_resumen_turno_db(self, id_corte_caja):
        if not id_corte_caja:
            return {}
        info = self._ejecutar_consulta("""
            SELECT cc.id_corte_caja, cc.fecha_hora_inicio, cc.fondo_inicial, ca.numero_caja
            FROM cortes_caja cc
            JOIN cajas ca ON cc.id_caja = ca.id_caja
            WHERE cc.id_corte_caja = %s
        """, (id_corte_caja,), fetch=True) or {}

        ventas_turno = self._ejecutar_consulta("""
            SELECT COUNT(*) AS num_ventas,
                   COALESCE(SUM(subtotal + impuesto), 0) AS total_ventas
            FROM ventas
            WHERE id_corte_caja = %s
        """, (id_corte_caja,), fetch=True) or {}

        pagos_v = self._ejecutar_consulta("""
            SELECT COALESCE(SUM(CASE WHEN id_metodo_pago = 1 THEN monto ELSE 0 END), 0) AS efectivo,
                   COALESCE(SUM(CASE WHEN id_metodo_pago IN (2, 3) THEN monto ELSE 0 END), 0) AS tarjeta
            FROM pagos_ventas
            WHERE id_corte_caja = %s
        """, (id_corte_caja,), fetch=True) or {}

        ap_turno = self._ejecutar_consulta("""
            SELECT COUNT(*) AS num_apartados
            FROM apartados
            WHERE id_corte_caja = %s
        """, (id_corte_caja,), fetch=True) or {}

        pagos_a = self._ejecutar_consulta("""
            SELECT COALESCE(SUM(CASE WHEN id_metodo_pago = 1 THEN monto ELSE 0 END), 0) AS efectivo,
                   COALESCE(SUM(CASE WHEN id_metodo_pago IN (2, 3) THEN monto ELSE 0 END), 0) AS tarjeta
            FROM pagos_apartados
            WHERE id_corte_caja = %s
        """, (id_corte_caja,), fetch=True) or {}

        fondo = float(info.get("fondo_inicial") or 0.0)
        ef_v = float(pagos_v.get("efectivo") or 0.0)
        tj_v = float(pagos_v.get("tarjeta") or 0.0)
        ef_a = float(pagos_a.get("efectivo") or 0.0)
        tj_a = float(pagos_a.get("tarjeta") or 0.0)

        return {
            "id_corte_caja": id_corte_caja,
            "numero_caja": info.get("numero_caja", "N/D"),
            "fecha_hora_inicio": info.get("fecha_hora_inicio"),
            "fondo_inicial": round(fondo, 2),
            "num_ventas": int(ventas_turno.get("num_ventas") or 0),
            "total_ventas": round(float(ventas_turno.get("total_ventas") or 0.0), 2),
            "num_apartados": int(ap_turno.get("num_apartados") or 0),
            "efectivo_ventas": round(ef_v, 2),
            "tarjeta_ventas": round(tj_v, 2),
            "efectivo_apartados": round(ef_a, 2),
            "tarjeta_apartados": round(tj_a, 2),
            "total_efectivo_cobrado": round(ef_v + ef_a, 2),
            "total_tarjeta_cobrado": round(tj_v + tj_a, 2),
            "efectivo_esperado": round(fondo + ef_v + ef_a, 2),
        }