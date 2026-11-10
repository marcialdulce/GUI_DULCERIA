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
        if not conexion: return None
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True, buffered=True)
            cursor.execute(query, parametros or ())
            if fetch: return cursor.fetchone()
            if fetchall: return cursor.fetchall()
            conexion.commit()
            self.invalidar_inventario()
            return cursor.lastrowid or True
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            if cursor: cursor.close()
            if conexion.is_connected(): conexion.close()

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

    def obtener_categorias(self):
        return self._ejecutar_consulta("SELECT id_categoria AS id, nombre_categoria AS nombre FROM categorias ORDER BY nombre_categoria", fetchall=True) or []

    def obtener_marcas(self):
        return self._ejecutar_consulta("SELECT id_marca AS id, nombre_marca AS nombre FROM marcas ORDER BY nombre_marca", fetchall=True) or []

    def obtener_unidades(self):
        return self._ejecutar_consulta("SELECT id_unidad AS id, nombre_unidad AS nombre FROM unidades ORDER BY nombre_unidad", fetchall=True) or []

    def crear_producto(self, datos):
        try:
            self._ejecutar_consulta("""
                INSERT INTO productos (codigo_barras, nombre_dulce, precio_venta, stock_minimo,
                                       estado, id_marca, id_categoria, id_unidad, id_proveedor)
                VALUES (%s, %s, %s, %s, 'activo', %s, %s, %s, %s)
            """, (datos["codigo_barras"], datos["nombre_dulce"], datos["precio_venta"],
                  datos.get("stock_minimo", 5), datos["id_marca"], datos["id_categoria"],
                  datos["id_unidad"], datos.get("id_proveedor")))
            return True, "Producto creado correctamente."
        except Exception as e:
            return False, f"No se pudo crear: {e}"

    def actualizar_producto(self, id_producto, datos):
        try:
            self._ejecutar_consulta("""
                UPDATE productos SET codigo_barras=%s, nombre_dulce=%s, precio_venta=%s,
                                     stock_minimo=%s, id_marca=%s, id_categoria=%s,
                                     id_unidad=%s, id_proveedor=%s
                WHERE id_producto=%s
            """, (datos["codigo_barras"], datos["nombre_dulce"], datos["precio_venta"],
                  datos["stock_minimo"], datos["id_marca"], datos["id_categoria"],
                  datos["id_unidad"], datos.get("id_proveedor"), id_producto))
            return True, "Producto actualizado."
        except Exception as e:
            return False, f"No se pudo actualizar: {e}"

    def eliminar_producto(self, id_producto):
        try:
            self._ejecutar_consulta("UPDATE productos SET estado='inactivo' WHERE id_producto=%s", (id_producto,))
            return True, "Producto dado de baja (inactivo)."
        except Exception as e:
            return False, f"No se pudo eliminar: {e}"

    def registrar_merma(self, id_producto, cantidad, motivo):
        con = conectar_bd()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("""SELECT stock_resultante FROM movimientos_inventario
                           WHERE id_producto=%s ORDER BY id_movimiento_inventario DESC LIMIT 1""",
                        (id_producto,))
            res = cur.fetchone()
            stock_actual = res["stock_resultante"] if res else 0
            if cantidad > stock_actual:
                return False, "No puedes mermar más de lo que tienes en stock."
            
            nuevo_stock = stock_actual - cantidad
            # Se registra exactamente como 'ajuste' con cantidad negativa
            cur.execute("""
                INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto)
                VALUES ('ajuste', %s, %s, %s)
            """, (-cantidad, nuevo_stock, id_producto))
            
            con.commit()
            self.invalidar_inventario()
            return True, "Merma registrada correctamente."
        except Exception as e:
            con.rollback()
            return False, str(e)
        finally:
            if con.is_connected(): con.close()

    def agregar_al_ticket(self, nombre_producto, cantidad):
        prod = next((p for p in self.inventario if p["nombre"] == nombre_producto), None)
        if not prod: return "no_encontrado"
        item = next((i for i in self.ticket_actual if i["producto"] == nombre_producto), None)
        cant_actual = item["cantidad"] if item else 0
        if (cant_actual + cantidad) > prod["stock"]: return "stock_insuficiente"
        if item:
            item["cantidad"] += cantidad
            item["subtotal"] = item["cantidad"] * prod["precio"]
        else:
            self.ticket_actual.append({
                "id_producto": prod["id_producto"], "producto": nombre_producto,
                "cantidad": cantidad, "precio_unitario": prod["precio"],
                "subtotal": prod["precio"] * cantidad
            })
        return True

    def calcular_total(self):
        sub = sum(i["subtotal"] for i in self.ticket_actual)
        return sub + round(sub * 0.16, 2)

    def obtener_reporte_ganancias(self):
        totales = self._ejecutar_consulta("""
            SELECT SUM(ingresos_totales) AS ingreso_total,
                   SUM(costo_inversion) AS costo_total,
                   SUM(ganancia_neta_real) AS utilidad_bruta
            FROM vw_analisis_financiero_mensual
        """, fetch=True)
        if not totales or totales['ingreso_total'] is None:
            totales = {'ingreso_total': 0, 'costo_total': 0, 'utilidad_bruta': 0}
        lista = self._ejecutar_consulta("""
            SELECT p.nombre_dulce, SUM(dv.cantidad) AS unidades_vendidas,
                   SUM(dv.subtotal) AS ingresos_totales,
                   COALESCE((SELECT costo_unitario FROM detalles_pedidos_proveedores dpp
                             WHERE dpp.id_producto = p.id_producto
                             ORDER BY id_detalle_pedido_proveedor DESC LIMIT 1), 0) AS costo_unitario
            FROM productos p JOIN detalles_ventas dv ON p.id_producto = dv.id_producto
            GROUP BY p.id_producto, p.nombre_dulce ORDER BY ingresos_totales DESC
        """, fetchall=True) or []
        for prod in lista:
            prod['ganancia_neta'] = prod['ingresos_totales'] - (prod['unidades_vendidas'] * prod['costo_unitario'])
            prod['ganancia_bruta'] = prod['ganancia_neta']
            prod['producto'] = prod['nombre_dulce']
        return {
            'ingreso_total': float(totales.get('ingreso_total') or 0),
            'costo_total': float(totales.get('costo_total') or 0),
            'utilidad_bruta': float(totales.get('utilidad_bruta') or 0),
            'detalle': lista
        }

    def obtener_datos_grafica(self, mes_filtro=None, caja_filtro=None):
        query = """
            SELECT ca.numero_caja, SUM(dv.subtotal) AS ingresos_totales
            FROM ventas v
            JOIN detalles_ventas dv ON v.id_venta = dv.id_venta
            JOIN cortes_caja c ON v.id_corte_caja = c.id_corte_caja
            JOIN cajas ca ON c.id_caja = ca.id_caja
            WHERE 1=1
        """
        params = []
        if mes_filtro:
            query += " AND MONTH(v.fecha_hora) = %s"; params.append(mes_filtro)
        if caja_filtro and caja_filtro != "Todas":
            query += " AND ca.numero_caja = %s"; params.append(caja_filtro)
        query += " GROUP BY ca.numero_caja ORDER BY ca.numero_caja ASC"
        return self._ejecutar_consulta(query, tuple(params), fetchall=True) or []

    def obtener_proveedores(self):
        return self._ejecutar_consulta("SELECT id_proveedor AS id, empresa AS nombre, telefono, correo FROM proveedores", fetchall=True) or []

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
            SELECT pp.id_pedido_proveedor AS id_pedido, p.nombre_dulce AS producto,
                   dpp.cantidad, pp.estado, pp.subtotal
            FROM pedidos_proveedores pp
            JOIN detalles_pedidos_proveedores dpp ON pp.id_pedido_proveedor = dpp.id_pedido_proveedor
            JOIN productos p ON dpp.id_producto = p.id_producto
            WHERE pp.estado = 'solicitado'
        """, fetchall=True) or []

    def recibir_pedido_proveedor(self, id_pedido):
        con = conectar_bd()
        if not con: return False
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("""SELECT id_producto, cantidad, id_detalle_pedido_proveedor
                           FROM detalles_pedidos_proveedores WHERE id_pedido_proveedor = %s""", (id_pedido,))
            for det in cur.fetchall():
                cur.execute("""SELECT stock_resultante FROM movimientos_inventario
                               WHERE id_producto=%s ORDER BY id_movimiento_inventario DESC LIMIT 1""", (det["id_producto"],))
                r = cur.fetchone()
                stock_actual = r["stock_resultante"] if r else 0
                cur.execute("""
                    INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto, id_detalle_pedido_proveedor)
                    VALUES ('entrada', %s, %s, %s, %s)
                """, (det["cantidad"], stock_actual + det["cantidad"], det["id_producto"], det["id_detalle_pedido_proveedor"]))
            cur.execute("UPDATE pedidos_proveedores SET estado='recibido' WHERE id_pedido_proveedor=%s", (id_pedido,))
            con.commit()
            self.invalidar_inventario()
            return True
        except Exception:
            con.rollback(); return False
        finally:
            con.close()

    def eliminar_proveedor(self, id_proveedor):
        try:
            self._ejecutar_consulta("DELETE FROM proveedores WHERE id_proveedor = %s", (id_proveedor,))
            return True
        except Exception as e:
            print(f"Error al eliminar proveedor: {e}")
            return False

    def obtener_apartados(self):
        return self._ejecutar_consulta("""
            SELECT a.id_apartado, a.nombre_cliente AS nombre,
                   DATE_FORMAT(a.fecha_entrega, '%d/%m/%Y') AS fecha, a.estado,
                   p.nombre_dulce AS producto, da.cantidad AS unidades,
                   a.subtotal, a.impuesto,
                   (SELECT COALESCE(SUM(monto), 0) FROM pagos_apartados pa
                    WHERE pa.id_apartado = a.id_apartado) AS pagado
            FROM apartados a
            JOIN detalles_apartados da ON a.id_apartado = da.id_apartado
            JOIN productos p ON da.id_producto = p.id_producto
            ORDER BY a.fecha_entrega
        """, fetchall=True) or []