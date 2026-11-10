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
            # Agregamos buffered=True para evitar el error "Unread result found"
            cursor = conexion.cursor(dictionary=True, buffered=True)
            cursor.execute(query, parametros or ())
            
            # Respetamos tu lógica original de fetch vs fetchall
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

    def obtener_reporte_ganancias(self):
        """Obtiene el reporte financiero desde la nueva vista analítica mensual."""
        query = """
            SELECT 
                mes,
                anio,
                ingresos_totales,
                costo_inversion,
                ahorro_promociones,
                ganancia_neta_real
            FROM vw_analisis_financiero_mensual
            ORDER BY anio DESC, mes DESC
        """
        # CLAVE: Usamos fetchall=True para que cargue todos los meses de la tabla
        return self._ejecutar_consulta(query, fetchall=True)

    # ---------------- Usuarios ----------------
    def validar_usuario(self, username, password):
        query = "SELECT id_usuario, id_rol, password_hash FROM usuarios WHERE username = %s AND estado = 'activo'"
        resultado = self._ejecutar_consulta(query, (username.strip(),), fetch=True)
        if resultado and verificar_password(password, resultado["password_hash"]):
            return resultado 
        return None

    def obtener_rol(self, id_rol):
        query = "SELECT nombre_rol FROM roles WHERE id_rol = %s"
        resultado = self._ejecutar_consulta(query, (id_rol,), fetch=True)
        return resultado["nombre_rol"] if resultado else "Cajero"

    # ---------------- Inventario y Mermas ----------------
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
            SELECT p.id_producto, p.nombre_dulce AS nombre, m.nombre_marca AS marca, 
                   c.nombre_categoria AS categoria, p.precio_venta AS precio,
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

    def registrar_merma(self, id_producto, cantidad, motivo):
        con = conectar_bd()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT stock_resultante FROM movimientos_inventario WHERE id_producto=%s ORDER BY id_movimiento_inventario DESC LIMIT 1", (id_producto,))
            res = cur.fetchone()
            stock_actual = res["stock_resultante"] if res else 0
            
            if cantidad > stock_actual:
                return False, "No puedes mermar más de lo que tienes en stock."
                
            nuevo_stock = stock_actual - cantidad
            cur.execute("""
                INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, observaciones, id_producto)
                VALUES ('ajuste', %s, %s, %s, %s)
            """, (-cantidad, nuevo_stock, f"Merma: {motivo}", id_producto))
            con.commit()
            self.invalidar_inventario()
            return True, "Merma registrada correctamente."
        except Exception as e:
            con.rollback()
            return False, str(e)
        finally:
            if con.is_connected():
                con.close()

    def agregar_al_ticket(self, nombre_producto, cantidad):
        prod = next((p for p in self.inventario if p["nombre"] == nombre_producto), None)
        if not prod: return "no_encontrado"

        item_en_ticket = next((item for item in self.ticket_actual if item["producto"] == nombre_producto), None)
        cantidad_actual = item_en_ticket["cantidad"] if item_en_ticket else 0
        
        if (cantidad_actual + cantidad) > prod["stock"]: return "stock_insuficiente"

        if item_en_ticket:
            item_en_ticket["cantidad"] += cantidad
            item_en_ticket["subtotal"] = item_en_ticket["cantidad"] * prod["precio"]
        else:
            self.ticket_actual.append({
                "id_producto": prod["id_producto"],
                "producto": nombre_producto, 
                "cantidad": cantidad, 
                "precio_unitario": prod["precio"],
                "subtotal": prod["precio"] * cantidad
            })
        return True

    def calcular_total(self):
        subtotal = sum(item["subtotal"] for item in self.ticket_actual)
        return subtotal + round(subtotal * 0.16, 2)

    # ---------------- Reportes y Ganancias ----------------
    def obtener_reporte_ganancias(self):
        """Obtiene el reporte financiero asegurando los nombres exactos de llaves para Tkinter."""
        
        # 1. Totales globales desde la vista
        totales_query = """
            SELECT 
                SUM(ingresos_totales) AS ingreso_total,
                SUM(costo_inversion) AS costo_total,
                SUM(ganancia_neta_real) AS utilidad_bruta
            FROM vw_analisis_financiero_mensual
        """
        totales = self._ejecutar_consulta(totales_query, fetch=True)
        
        if not totales or totales['ingreso_total'] is None:
            totales = {'ingreso_total': 0, 'costo_total': 0, 'utilidad_bruta': 0}

        # 2. Desglose con los ALIAS EXACTOS que pide panel_reportes.py (unidades_vendidas, ingresos_totales, costo_unitario)
        productos_query = """
            SELECT 
                p.nombre_dulce, 
                SUM(dv.cantidad) AS unidades_vendidas, 
                SUM(dv.subtotal) AS ingresos_totales,
                COALESCE((SELECT costo_unitario FROM detalles_pedidos_proveedores dpp 
                          WHERE dpp.id_producto = p.id_producto 
                          ORDER BY id_detalle_pedido_proveedor DESC LIMIT 1), 0) AS costo_unitario
            FROM productos p
            JOIN detalles_ventas dv ON p.id_producto = dv.id_producto
            GROUP BY p.id_producto, p.nombre_dulce
            ORDER BY ingresos_totales DESC
        """
        lista = self._ejecutar_consulta(productos_query, fetchall=True) or []
        
        # 3. Empaquetamos todo cubriendo cualquier variable que la tabla visual pueda pedir
        for prod in lista:
            # Calculamos la ganancia restando los costos al ingreso
            prod['ganancia_neta'] = prod['ingresos_totales'] - (prod['unidades_vendidas'] * prod['costo_unitario'])
            
            # Duplicamos las variables para cubrir todas las posibilidades que la interfaz gráfica pueda exigir
            prod['ganancia_bruta'] = prod['ganancia_neta']
            prod['producto'] = prod['nombre_dulce']

        # 4. Retornamos el paquete final exacto
        return {
            'ingreso_total': float(totales.get('ingreso_total') or 0),
            'costo_total': float(totales.get('costo_total') or 0),
            'utilidad_bruta': float(totales.get('utilidad_bruta') or 0),
            'detalle': lista
        }
        
    # ---------------- Proveedores / Pedidos ----------------
    def obtener_proveedores(self):
        query = "SELECT id_proveedor as id, empresa as nombre, telefono, correo FROM proveedores"
        return self._ejecutar_consulta(query, fetchall=True) or []

    def obtener_productos_proveedor(self, id_proveedor):
        query = """
            SELECT id_producto, nombre_dulce as nombre, precio_venta 
            FROM productos WHERE id_proveedor = %s AND estado = 'activo'
        """
        return self._ejecutar_consulta(query, (id_proveedor,), fetchall=True) or []

    def obtener_pedidos_activos(self):
        query = """
            SELECT pp.id_pedido_proveedor as id_pedido, p.nombre_dulce as producto, 
                   dpp.cantidad, pp.estado, pp.subtotal
            FROM pedidos_proveedores pp
            JOIN detalles_pedidos_proveedores dpp ON pp.id_pedido_proveedor = dpp.id_pedido_proveedor
            JOIN productos p ON dpp.id_producto = p.id_producto
            WHERE pp.estado = 'solicitado'
        """
        return self._ejecutar_consulta(query, fetchall=True) or []

    def recibir_pedido_proveedor(self, id_pedido):
        con = conectar_bd()
        if not con: return False
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT id_producto, cantidad, id_detalle_pedido_proveedor FROM detalles_pedidos_proveedores WHERE id_pedido_proveedor = %s", (id_pedido,))
            detalles = cur.fetchall()
            
            for det in detalles:
                cur.execute("SELECT stock_resultante FROM movimientos_inventario WHERE id_producto=%s ORDER BY id_movimiento_inventario DESC LIMIT 1", (det["id_producto"],))
                res = cur.fetchone()
                stock_actual = res["stock_resultante"] if res else 0
                nuevo_stock = stock_actual + det["cantidad"]
                cur.execute("""
                    INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto, id_detalle_pedido_proveedor)
                    VALUES ('entrada', %s, %s, %s, %s)
                """, (det["cantidad"], nuevo_stock, det["id_producto"], det["id_detalle_pedido_proveedor"]))
                
            cur.execute("UPDATE pedidos_proveedores SET estado='recibido' WHERE id_pedido_proveedor=%s", (id_pedido,))
            con.commit()
            self.invalidar_inventario()
            return True
        except Exception:
            con.rollback()
            return False
        finally:
            con.close()

    # ---------------- Apartados ----------------
    def obtener_apartados(self):
        query = """
            SELECT a.id_apartado, a.nombre_cliente AS nombre, 
                   DATE_FORMAT(a.fecha_entrega, '%d/%m/%Y') AS fecha, a.estado, 
                   p.nombre_dulce AS producto, da.cantidad AS unidades, a.subtotal, a.impuesto,
                   (SELECT COALESCE(SUM(monto), 0) FROM pagos_apartados pa WHERE pa.id_apartado = a.id_apartado) as pagado
            FROM apartados a
            JOIN detalles_apartados da ON a.id_apartado = da.id_apartado
            JOIN productos p ON da.id_producto = p.id_producto
            ORDER BY a.fecha_entrega
        """
        return self._ejecutar_consulta(query, fetchall=True) or []
    
    
    def eliminar_proveedor(self, id_proveedor):
        """Elimina un proveedor de la base de datos."""
        query = "DELETE FROM proveedores WHERE id_proveedor = %s"
        try:
            self._ejecutar_consulta(query, (id_proveedor,))
            return True
        except Exception as e:
            # Capturar error si el proveedor tiene pedidos vinculados (integridad referencial)
            print(f"Error al eliminar proveedor: {e}")
            return False
        
    def obtener_datos_grafica(self, mes_filtro=None, caja_filtro=None):
        """Delega a SQL el filtrado por mes y caja, y suma los ingresos al instante."""
        query = """
            SELECT 
                ca.numero_caja,
                SUM(dv.subtotal) AS ingresos_totales
            FROM ventas v
            JOIN detalles_ventas dv ON v.id_venta = dv.id_venta
            JOIN cortes_caja c ON v.id_corte_caja = c.id_corte_caja
            JOIN cajas ca ON c.id_caja = ca.id_caja
            WHERE 1=1
        """
        params = []
        if mes_filtro:
            query += " AND MONTH(v.fecha_hora) = %s"
            params.append(mes_filtro)
            
        if caja_filtro and caja_filtro != "Todas":
            query += " AND ca.numero_caja = %s"
            params.append(caja_filtro)
            
        query += " GROUP BY ca.numero_caja ORDER BY ca.numero_caja ASC"
        
        return self._ejecutar_consulta(query, tuple(params), fetchall=True) or []