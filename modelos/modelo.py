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
            cursor = conexion.cursor(dictionary=True)
            cursor.execute(query, parametros or ())
            if fetch: return cursor.fetchone()
            if fetchall: return cursor.fetchall()
            conexion.commit()
            self.invalidar_inventario()
            return cursor.lastrowid or True
        except Exception:
            conexion.rollback()
            raise
        finally:
            if cursor: cursor.close()
            if conexion.is_connected(): conexion.close()

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

    # ---------------- Inventario ----------------
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
        # Consulta estricta basada en el último movimiento registrado
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

    def obtener_inventario_filtrado(self, texto, marca, categoria):
        productos = self.inventario
        filtrados = []
        for p in productos:
            if texto and texto not in p["nombre"].lower() and texto not in p["marca"].lower():
                continue
            if marca != "Todas" and p["marca"] != marca:
                continue
            if categoria != "Todas" and p["categoria"] != categoria:
                continue
            filtrados.append(p)
        return filtrados

    def obtener_nombres_productos(self):
        # Solo muestra productos que tengan stock disponible para apartar
        return [p["nombre"] for p in self.inventario if p["stock"] > 0]

    def eliminar_producto(self, nombre_producto):
        # Borrado lógico (cambia el estado a inactivo)
        self._ejecutar_consulta("UPDATE productos SET estado = 'inactivo' WHERE nombre_dulce = %s", (nombre_producto,))
        return True

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

    # ---------------- Proveedores ----------------
    def agregar_proveedor(self, nombre, telefono="", correo=""):
        if not nombre or not nombre.strip(): return "nombre_vacio"
        existe = self._ejecutar_consulta("SELECT id_proveedor FROM proveedores WHERE empresa = %s", (nombre,), fetch=True)
        if existe: return "ya_existe"
        
        query = "INSERT INTO proveedores (empresa, telefono, correo) VALUES (%s, %s, %s)"
        self._ejecutar_consulta(query, (nombre.strip(), telefono.strip(), correo.strip()))
        return True

    def obtener_proveedores(self):
        query = "SELECT id_proveedor as id, empresa as nombre, telefono, correo FROM proveedores"
        return self._ejecutar_consulta(query, fetchall=True) or []
    
    def eliminar_proveedor(self, proveedor_id):
        self._ejecutar_consulta("UPDATE productos SET id_proveedor = NULL WHERE id_proveedor = %s", (proveedor_id,))
        self._ejecutar_consulta("DELETE FROM proveedores WHERE id_proveedor = %s", (proveedor_id,))
        return True

    # ---------------- Pedidos a Proveedores ----------------
    def obtener_pedidos_activos(self):
        query = """
            SELECT pp.id_pedido_proveedor as id_pedido, p.nombre_dulce as producto, 
                   dpp.cantidad, pp.estado
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
            cur.execute("""
                SELECT dpp.id_producto, dpp.cantidad, dpp.id_detalle_pedido_proveedor
                FROM detalles_pedidos_proveedores dpp
                WHERE dpp.id_pedido_proveedor = %s
            """, (id_pedido,))
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
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def cancelar_pedido_proveedor(self, id_pedido):
        self._ejecutar_consulta("UPDATE pedidos_proveedores SET estado='cancelado' WHERE id_pedido_proveedor=%s", (id_pedido,))
        return True

    # ---------------- Apartados ----------------
    def obtener_apartados(self):
        query = """
            SELECT a.id_apartado, a.nombre_cliente AS nombre, a.telefono_cliente AS telefono,
                   DATE_FORMAT(a.fecha_entrega, '%d/%m/%Y') AS fecha, a.estado, 
                   p.nombre_dulce AS producto, da.cantidad AS unidades
            FROM apartados a
            JOIN detalles_apartados da ON a.id_apartado = da.id_apartado
            JOIN productos p ON da.id_producto = p.id_producto
            ORDER BY a.fecha_entrega
        """
        return self._ejecutar_consulta(query, fetchall=True) or []

    def registrar_apartado(self, nombre, telefono, fecha_entrega, prod_nombre, cantidad, metodo_texto, id_corte_caja):
        prod = next((p for p in self.inventario if p["nombre"] == prod_nombre), None)
        if not prod: return False, "Producto no encontrado."
        if prod["stock"] < cantidad: return False, f"Stock insuficiente. Solo hay {prod['stock']} unidades."

        total = prod["precio"] * cantidad
        anticipo = round(total * 0.50, 2)
        id_metodo = 1 if metodo_texto == "Efectivo" else (2 if metodo_texto == "Tarjeta de débito" else 3)

        con = conectar_bd()
        if not con: return False, "Error de conexión a BD."
        try:
            cur = con.cursor(dictionary=True)
            subtotal = total
            impuesto = round(subtotal * 0.16, 2)
            
            cur.execute("""
                INSERT INTO apartados (nombre_cliente, telefono_cliente, fecha_entrega, subtotal, impuesto, estado, id_corte_caja)
                VALUES (%s, %s, %s, %s, %s, 'pendiente', %s)
            """, (nombre, telefono, fecha_entrega, subtotal, impuesto, id_corte_caja))
            id_apartado = cur.lastrowid
            
            cur.execute("""
                INSERT INTO detalles_apartados (cantidad, precio_unitario, subtotal, id_apartado, id_producto)
                VALUES (%s, %s, %s, %s, %s)
            """, (cantidad, prod["precio"], subtotal, id_apartado, prod["id_producto"]))
                
            cur.execute("""
                INSERT INTO pagos_apartados (monto, id_apartado, id_metodo_pago, id_corte_caja)
                VALUES (%s, %s, %s, %s)
            """, (anticipo, id_apartado, id_metodo, id_corte_caja))
            
            con.commit()
            return True, f"Éxito. Total: ${total:.2f}, Anticipo cobrado: ${anticipo:.2f}"
        except Exception as e:
            con.rollback()
            return False, str(e)
        finally:
            con.close()

    def cancelar_apartado(self, id_apartado):
        self._ejecutar_consulta("UPDATE apartados SET estado='cancelado' WHERE id_apartado=%s", (id_apartado,))
        return True