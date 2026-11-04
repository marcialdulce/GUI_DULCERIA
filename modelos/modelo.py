from modelos.conexion import ConexionBD

class ModeloDulceria:
    def __init__(self):
        self.conexion_bd = ConexionBD()
        self.ticket_actual = [] 
        
    def _ejecutar_consulta(self, query, parametros=None, fetch=False, fetchall=False):
        conexion = self.conexion_bd.conectar()
        if not conexion: return None
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute(query, parametros or ())
            resultado = None
            if fetch: resultado = cursor.fetchone()
            elif fetchall: resultado = cursor.fetchall()
            else: conexion.commit()
            return resultado
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()

    # ---------------- Usuarios y Roles ----------------
    def validar_usuario(self, username, password):
        query = "SELECT id_usuario FROM USUARIOS WHERE username = %s AND contraseña = %s AND estatus = 'Activo'"
        usuario = self._ejecutar_consulta(query, (username, password), fetch=True)
        return usuario is not None

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
            estado = "AGOTADO" if prod["stock"] == 0 else "BAJO" if prod["stock"] < 15 else "MEDIO"
            prod["estado"] = estado
            prod["proveedor"] = prod["proveedor"] or "—"
            resultados.append(prod)
        return resultados

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
        total = self.calcular_total()
        if pago_cliente >= total:
            cambio = pago_cliente - total
            # Guardado atómico del descuento de stock en BD
            for item in self.ticket_actual:
                query = "UPDATE PRODUCTOS SET stock_actual = stock_actual - %s WHERE nombre_dulce = %s"
                self._ejecutar_consulta(query, (item["cantidad"], item["producto"]))
            self.ticket_actual.clear()
            return True, cambio
        return False, 0.0