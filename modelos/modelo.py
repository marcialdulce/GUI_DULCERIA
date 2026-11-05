from modelos.conexion import ConexionBD
from seguridad import verificar_password

UMBRAL_STOCK_BAJO = 15   # misma regla que usa la vista de inventario

class ModeloDulceria:
    def __init__(self):
        self.conexion_bd = ConexionBD()
        self.ticket_actual = [] 
        
    def _ejecutar_consulta(self, query, parametros=None, fetch=False, fetchall=False):
        """SELECT -> dict / lista de dicts.  INSERT/UPDATE/DELETE -> lastrowid (o True)."""
        conexion = self.conexion_bd.conectar()
        if not conexion: return None
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute(query, parametros or ())
            if fetch: return cursor.fetchone()
            if fetchall: return cursor.fetchall()
            conexion.commit()
            return cursor.lastrowid or True      # <- antes devolvía None
        except Exception:
            conexion.rollback()
            raise
        finally:
            if cursor: cursor.close()
            if conexion.is_connected(): conexion.close()
                

    # ---------------- Usuarios y Roles ----------------
    def validar_usuario(self, username, password):
        query = "SELECT `contraseña` AS clave FROM USUARIOS WHERE username = %s AND estatus = 'Activo'"
        usuario = self._ejecutar_consulta(query, (username,), fetch=True)
        return bool(usuario) and verificar_password(password, usuario["clave"])

    def obtener_rol(self, username):
        query = """
            SELECT r.nombre_rol FROM USUARIOS u 
            JOIN ROLES r ON u.id_rol = r.id_rol 
            WHERE u.username = %s
        """
        resultado = self._ejecutar_consulta(query, (username,), fetch=True)
        return resultado["nombre_rol"] if resultado else "Cajero"

    def obtener_id_usuario(self, username):
        query = "SELECT id_usuario FROM USUARIOS WHERE username = %s"
        resultado = self._ejecutar_consulta(query, (username,), fetch=True)
        return resultado["id_usuario"] if resultado else None
    

    # ---------------- Proveedores ----------------
    def agregar_proveedor(self, nombre, telefono="", correo=""):
        if not nombre or not nombre.strip(): return "nombre_vacio"
        existe = self._ejecutar_consulta("SELECT id_proveedor FROM PROVEEDORES WHERE empresa = %s", (nombre,), fetch=True)
        if existe: return "ya_existe"
        
        query = "INSERT INTO PROVEEDORES (empresa, telefono, correo) VALUES (%s, %s, %s)"
        self._ejecutar_consulta(query, (nombre.strip(), telefono.strip(), correo.strip()))
        return True

    def obtener_proveedores(self):
        query = "SELECT id_proveedor as id, empresa as nombre, telefono, correo FROM PROVEEDORES"
        return self._ejecutar_consulta(query, fetchall=True) or []
    
    def editar_proveedor(self, proveedor_id, telefono, correo):
        query = "UPDATE PROVEEDORES SET telefono = %s, correo = %s WHERE id_proveedor = %s"
        self._ejecutar_consulta(query, (telefono, correo, proveedor_id))
        return True
    
    def eliminar_proveedor(self, proveedor_id):
        self._ejecutar_consulta("UPDATE PRODUCTOS SET id_proveedor = NULL WHERE id_proveedor = %s", (proveedor_id,))
        self._ejecutar_consulta("DELETE FROM PROVEEDORES WHERE id_proveedor = %s", (proveedor_id,))
        return True
    
    
        # ---------------- Pedidos a Proveedor ----------------
    def registrar_pedido_proveedor(self, nombre_producto, cantidad, username):
        id_usuario = self.obtener_id_usuario(username)
        # Buscamos el ID del producto y del proveedor
        query_prod = "SELECT id_producto, id_proveedor FROM PRODUCTOS WHERE nombre_dulce = %s"
        prod = self._ejecutar_consulta(query_prod, (nombre_producto,), fetch=True)
        
        if not prod: return False
        
        query = """
            INSERT INTO PEDIDOS_PROVEEDOR (cantidad, id_producto, id_proveedor, id_usuario)
            VALUES (%s, %s, %s, %s)
        """
        self._ejecutar_consulta(query, (cantidad, prod["id_producto"], prod["id_proveedor"], id_usuario))
        return True

    def obtener_pedidos_proveedor(self):
        query = """
            SELECT pp.id_pedido, p.nombre_dulce as producto, pp.cantidad, pp.estado
            FROM PEDIDOS_PROVEEDOR pp
            JOIN PRODUCTOS p ON pp.id_producto = p.id_producto
            WHERE pp.estado = 'Pendiente'
        """
        return self._ejecutar_consulta(query, fetchall=True) or []

    def eliminar_pedido_proveedor(self, id_pedido):
        self._ejecutar_consulta("UPDATE PEDIDOS_PROVEEDOR SET estado = 'Cancelado' WHERE id_pedido = %s AND estado = 'Pendiente'", (id_pedido,))
        return True

    def recibir_pedido_proveedor(self, id_pedido):
        """Marca el pedido como Recibido y SUMA la cantidad al stock (en una sola transacción)."""
        con = self.conexion_bd.conectar()
        if not con: return False
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT id_producto, cantidad FROM PEDIDOS_PROVEEDOR WHERE id_pedido=%s AND estado='Pendiente' FOR UPDATE", (id_pedido,))
            ped = cur.fetchone()
            if not ped: con.rollback(); return False
            cur.execute("UPDATE PRODUCTOS SET stock_actual = stock_actual + %s WHERE id_producto = %s", (ped["cantidad"], ped["id_producto"]))
            cur.execute("UPDATE PEDIDOS_PROVEEDOR SET estado='Recibido' WHERE id_pedido=%s", (id_pedido,))
            con.commit()
            return True
        except Exception:
            con.rollback(); raise
        finally:
            con.close()

    def crear_pedidos_reposicion(self, username, cantidad=50):
        """Reposición automática: un pedido Pendiente por cada producto bajo en stock que aún no tenga uno."""
        id_usuario = self.obtener_id_usuario(username)
        if not id_usuario: return 0
        faltantes = self._ejecutar_consulta("""
            SELECT p.id_producto, p.id_proveedor FROM PRODUCTOS p
            WHERE p.activo = 1 AND p.stock_actual < %s
              AND NOT EXISTS (SELECT 1 FROM PEDIDOS_PROVEEDOR pp
                              WHERE pp.id_producto = p.id_producto AND pp.estado = 'Pendiente')
        """, (UMBRAL_STOCK_BAJO,), fetchall=True) or []
        for f in faltantes:
            self._ejecutar_consulta(
                "INSERT INTO PEDIDOS_PROVEEDOR (cantidad, id_producto, id_proveedor, id_usuario) VALUES (%s,%s,%s,%s)",
                (cantidad, f["id_producto"], f["id_proveedor"], id_usuario))
        return len(faltantes)

    # ---------------- Productos (Inventario) ----------------
    def _obtener_o_crear_fk(self, tabla, columna_id, columna_nombre, valor):
        query_sel = f"SELECT {columna_id} FROM {tabla} WHERE {columna_nombre} = %s"
        res = self._ejecutar_consulta(query_sel, (valor,), fetch=True)
        if res: return res[columna_id]
        self._ejecutar_consulta(f"INSERT INTO {tabla} ({columna_nombre}) VALUES (%s)", (valor,))
        return self._ejecutar_consulta(query_sel, (valor,), fetch=True)[columna_id]

    def agregar_producto(self, nombre, marca, categoria, precio, stock, proveedor_id=None):
        if not nombre or not nombre.strip(): return "nombre_vacio"
        if self._ejecutar_consulta("SELECT id_producto FROM PRODUCTOS WHERE nombre_dulce = %s", (nombre,), fetch=True):
            return "ya_existe"
        if float(precio) <= 0 or int(stock) < 0: return "datos_invalidos"

        id_marca = self._obtener_o_crear_fk("MARCAS", "id_marca", "nombre_marca", marca.strip() or "Genérica")
        id_categoria = self._obtener_o_crear_fk("CATEGORIAS", "id_categoria", "nombre_categoria", categoria.strip() or "General")

        query = """
            INSERT INTO PRODUCTOS (nombre_dulce, precio_venta, stock_actual, stock_minimo, activo, id_categoria, id_marca, id_proveedor)
            VALUES (%s, %s, %s, 5, 1, %s, %s, %s)
        """
        self._ejecutar_consulta(query, (nombre.strip(), float(precio), int(stock), id_categoria, id_marca, proveedor_id))
        return True
    
    def eliminar_producto(self, nombre_producto):
        query = "UPDATE PRODUCTOS SET activo = 0 WHERE nombre_dulce = %s"
        self._ejecutar_consulta(query, (nombre_producto,))
        return True

    def editar_producto(self, nombre_original, nuevos_datos):
        id_marca = self._obtener_o_crear_fk("MARCAS", "id_marca", "nombre_marca", nuevos_datos["marca"])
        id_categoria = self._obtener_o_crear_fk("CATEGORIAS", "id_categoria", "nombre_categoria", nuevos_datos["categoria"])
        
        query = """
            UPDATE PRODUCTOS SET nombre_dulce = %s, precio_venta = %s, stock_actual = %s, 
            id_marca = %s, id_categoria = %s WHERE nombre_dulce = %s
        """
        self._ejecutar_consulta(query, (
            nuevos_datos["nombre"], float(nuevos_datos["precio"]), int(nuevos_datos["stock"]),
            id_marca, id_categoria, nombre_original
        ))
        return True

    @staticmethod
    def _estado_stock(stock):
        if stock == 0:
            return "AGOTADO"
        if stock < UMBRAL_STOCK_BAJO:
            return "BAJO"
        return "MEDIO"

    def obtener_inventario_filtrado(self, texto_busqueda, marca, categoria):
        query = """
            SELECT p.nombre_dulce as nombre, m.nombre_marca as marca, c.nombre_categoria as categoria, 
                   p.precio_venta as precio, p.stock_actual as stock, pr.empresa as proveedor
            FROM PRODUCTOS p
            LEFT JOIN MARCAS m ON p.id_marca = m.id_marca
            LEFT JOIN CATEGORIAS c ON p.id_categoria = c.id_categoria
            LEFT JOIN PROVEEDORES pr ON p.id_proveedor = pr.id_proveedor
            WHERE p.activo = 1 AND p.nombre_dulce LIKE %s
        """
        params = [f"%{texto_busqueda}%"]
        if marca != "Todas":
            query += " AND m.nombre_marca = %s"
            params.append(marca)
        if categoria != "Todas":
            query += " AND c.nombre_categoria = %s"
            params.append(categoria)

        resultados_db = self._ejecutar_consulta(query, tuple(params), fetchall=True) or []
        resultados = []
        for prod in resultados_db:
            prod["estado"] = self._estado_stock(prod["stock"])
            prod["proveedor"] = prod["proveedor"] or "—"
            resultados.append(prod)
        return resultados
    

    @property
    def inventario(self):
        """Catálogo activo para PanelVentas / PanelInicio (claves: nombre, marca, categoria, precio, stock)."""
        filas = self._ejecutar_consulta("""
            SELECT p.nombre_dulce AS nombre, m.nombre_marca AS marca, c.nombre_categoria AS categoria,
                   p.precio_venta AS precio, p.stock_actual AS stock
            FROM PRODUCTOS p
            LEFT JOIN MARCAS m ON p.id_marca = m.id_marca
            LEFT JOIN CATEGORIAS c ON p.id_categoria = c.id_categoria
            WHERE p.activo = 1 ORDER BY p.nombre_dulce
        """, fetchall=True) or []
        for f in filas: f["precio"] = float(f["precio"])
        return filas

    # ---------------- Ticket y Ventas ----------------
    def agregar_al_ticket(self, nombre_producto, cantidad):
        query = "SELECT precio_venta, stock_actual FROM PRODUCTOS WHERE nombre_dulce = %s AND activo = 1"
        dulce = self._ejecutar_consulta(query, (nombre_producto,), fetch=True)
        if not dulce: return "no_encontrado"

        item_en_ticket = next((item for item in self.ticket_actual if item["producto"] == nombre_producto), None)
        cantidad_actual = item_en_ticket["cantidad"] if item_en_ticket else 0
        
        if (cantidad_actual + cantidad) > dulce["stock_actual"]: return "stock_insuficiente"

        if item_en_ticket:
            item_en_ticket["cantidad"] += cantidad
            item_en_ticket["subtotal"] = item_en_ticket["cantidad"] * float(dulce["precio_venta"])
        else:
            self.ticket_actual.append({
                "producto": nombre_producto, "cantidad": cantidad, 
                "subtotal": float(dulce["precio_venta"]) * cantidad
            })
        return True
         
    def calcular_total(self):
        return sum(item["subtotal"] for item in self.ticket_actual)

    def procesar_cobro(self, pago_cliente):
        """Solo valida el pago y calcula el cambio. El descuento de stock se hace dentro de la
        MISMA transacción que guarda la venta (RepositorioVentas.registrar), así nunca quedan desfasados."""
        total = self.calcular_total()
        if pago_cliente >= total:
            return True, pago_cliente - total
        return False, 0.0
    
    
        # ---------------- Turnos y Cajas ----------------
    def abrir_turno(self, username):
        id_usuario = self.obtener_id_usuario(username)
        if not id_usuario: return None
        
        # Caja 1 = principal (la inserta 02_dulceria_datos_base.sql)
        query = "INSERT INTO TURNOS_CAJA (id_usuario, id_caja) VALUES (%s, 1)"
        id_turno = self._ejecutar_consulta(query, (id_usuario,))
        return id_turno if id_turno is not True else None

    def cerrar_turno(self, id_turno, efectivo_contado, efectivo_esperado):
        diferencia = float(efectivo_contado) - float(efectivo_esperado)
        query = """
            UPDATE TURNOS_CAJA 
            SET fecha_hora_fin = NOW(), efectivo_contado = %s, efectivo_esperado = %s, diferencia = %s 
            WHERE id_turno = %s
        """
        self._ejecutar_consulta(query, (efectivo_contado, efectivo_esperado, diferencia, id_turno))
        
        
    # ---------------- Apartados ----------------
    def obtener_apartados(self):
        query = """
            SELECT a.id_apartado, a.nombre_cliente AS nombre,
                   DATE_FORMAT(a.fecha_entrega, '%d/%m/%Y') AS fecha,
                   a.estado, p.nombre_dulce AS producto, p.precio_venta AS precio,
                   da.cantidad AS unidades
            FROM APARTADOS a
            JOIN DETALLES_APARTADOS da ON a.id_apartado = da.id_apartado
            JOIN PRODUCTOS p ON da.id_producto = p.id_producto
            ORDER BY a.fecha_entrega
        """
        filas = self._ejecutar_consulta(query, fetchall=True) or []
        for f in filas: f["precio"] = float(f["precio"])
        return filas

    def registrar_apartado(self, nombre_cliente, fecha_entrega, anticipo, articulos, username):
        """articulos = [{"producto": nombre, "cantidad": n}, ...]; fecha_entrega = 'AAAA-MM-DD'.
        Guarda cabecera + detalles en una transacción. NO descuenta stock (se descuenta al entregar)."""
        id_usuario = self.obtener_id_usuario(username)
        if not id_usuario or not articulos: return None
        con = self.conexion_bd.conectar()
        if not con: return None
        try:
            cur = con.cursor(dictionary=True)
            lineas, total = [], 0.0
            for art in articulos:
                cur.execute("SELECT id_producto, precio_venta FROM PRODUCTOS WHERE nombre_dulce=%s AND activo=1", (art["producto"],))
                p = cur.fetchone()
                if not p: raise ValueError(f"Producto no encontrado: {art['producto']}")
                sub = float(p["precio_venta"]) * int(art["cantidad"])
                total += sub
                lineas.append((int(art["cantidad"]), sub, p["id_producto"]))
            cur.execute("""INSERT INTO APARTADOS (nombre_cliente, fecha_entrega, anticipo, total, id_usuario)
                           VALUES (%s,%s,%s,%s,%s)""", (nombre_cliente, fecha_entrega, float(anticipo), total, id_usuario))
            id_apartado = cur.lastrowid
            for cant, sub, id_prod in lineas:
                cur.execute("INSERT INTO DETALLES_APARTADOS (cantidad, subtotal, id_apartado, id_producto) VALUES (%s,%s,%s,%s)",
                            (cant, sub, id_apartado, id_prod))
            con.commit()
            return id_apartado
        except Exception:
            con.rollback(); raise
        finally:
            con.close()

    def cambiar_estado_apartado(self, id_apartado, estado):
        if estado not in ("Pendiente", "Entregado", "Cancelado"): return False
        self._ejecutar_consulta("UPDATE APARTADOS SET estado=%s WHERE id_apartado=%s", (estado, id_apartado))
        return True
