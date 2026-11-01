import json
import os

class ModeloDulceria:

    RUTA_DATOS = "datos/dulceria.json"

    def __init__(self):
        # Usuarios del sistema
        self.usuarios = {
            "Dulce": "1234",
            "America": "1234",
            "Daniel": "1234",
            "Yeray": "1234",
            "Josue": "1234",
            "cajero01": "caja123"
        }

        # Diccionario de roles
        self.roles = {
            "Dulce": "Administrador",
            "America": "Administrador",
            "Daniel": "Administrador",
            "Yeray": "Administrador",
            "Josue": "Administrador",
            "cajero01": "Cajero"
        }

        self.ticket_actual = [] 
        self.historial_ventas = []
        self.proveedores = []
        
        # Inventario: Cargarlo desde el JSON
        self.inventario = []
        self._cargar_inventario()

        if not self.inventario:
            self._cargar_inventario_por_defecto()
            self.guardar_inventario()

    # ---------------- Persistencia JSON ----------------
    def _cargar_inventario(self):
        """Lee el inventario desde el JSON. Si no existe, deja la lista vacía."""
        if not os.path.exists(self.RUTA_DATOS):
            return
        try:
            with open(self.RUTA_DATOS, "r", encoding="utf-8") as f:
                datos = json.load(f)
            self.inventario = datos.get("inventario", [])
            self.proveedores = datos.get("proveedores", [])
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Modelo] Error al cargar inventario: {e}")
            self.inventario = []
            self.proveedores = []

    def guardar_inventario(self):
        """Escribe el inventario actual en el JSON."""
        carpeta = os.path.dirname(self.RUTA_DATOS)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(self.RUTA_DATOS, "w", encoding="utf-8") as f:
            json.dump({
               "inventario": self.inventario,
               "proveedores": self.proveedores
            }, f, indent=4, ensure_ascii=False)

    # ---------------- Proveedores ----------------
    def agregar_proveedor(self, nombre, telefono="", correo=""):
        if not nombre or not nombre.strip():
            return "nombre_vacio"
        if any(p["nombre"].lower() == nombre.strip().lower() for p in self.proveedores):
            return "ya_existe"

        nuevo_id = max((p["id"] for p in self.proveedores), default=0) + 1
        self.proveedores.append({
            "id": nuevo_id,
            "nombre": nombre.strip(),
            "telefono": telefono.strip(),
            "correo": correo.strip()
        })
        self.guardar_inventario()
        return nuevo_id

    def obtener_proveedor(self, proveedor_id):
        return next((p for p in self.proveedores if p["id"] == proveedor_id), None)
    
    def editar_proveedor(self, proveedor_id, telefono, correo):
        prov = self.obtener_proveedor(proveedor_id)
        if prov:
            prov["telefono"] = telefono
            prov["correo"] = correo
            self.guardar_inventario()
            return True
        return False
    
    def eliminar_proveedor(self, proveedor_id):
        self.proveedores = [p for p in self.proveedores if p["id"] != proveedor_id]
        for prod in self.inventario:
            if prod.get("proveedor_id") == proveedor_id:
                prod["proveedor_id"] = None
        self.guardar_inventario()
        return True

    def _cargar_inventario_por_defecto(self):
        self.inventario = [
            {"nombre": "Gomitas", "marca": "Ricolino", "categoria": "Gomitas", "precio": 15.0, "stock": 20},
            {"nombre": "Chocolate", "marca": "Carlos V", "categoria": "Chocolates", "precio": 12.0, "stock": 15},
            {"nombre": "Pap's", "marca": "Totis", "categoria": "Frituras", "precio": 4.0, "stock": 50},
            {"nombre": "Panditas", "marca": "Ricolino", "categoria": "Gomitas", "precio": 20.0, "stock": 10},
            {"nombre": "Kranky", "marca": "Ricolino", "categoria": "Chocolates", "precio": 14.0, "stock": 25},
            {"nombre": "Bubulubu", "marca": "Ricolino", "categoria": "Chocolates", "precio": 16.0, "stock": 30},
            {"nombre": "Carlos V Blanco", "marca": "Carlos V", "categoria": "Chocolates", "precio": 13.0, "stock": 20},
            {"nombre": "Moritas", "marca": "Ricolino", "categoria": "Gomitas", "precio": 12.0, "stock": 40},
            {"nombre": "Mangomitas", "marca": "Ricolino", "categoria": "Gomitas", "precio": 15.0, "stock": 35},
            {"nombre": "Donitas Sal y Limón", "marca": "Totis", "categoria": "Frituras", "precio": 6.0, "stock": 60},
            {"nombre": "Donitas Picantes", "marca": "Totis", "categoria": "Frituras", "precio": 5.0, "stock": 55},
        ]

    def agregar_producto(self, nombre, marca, categoria, precio, stock, proveedor_id=None):
        if not nombre or not nombre.strip():
            return "nombre_vacio"
        if any(p["nombre"].lower() == nombre.strip().lower() for p in self.inventario):
            return "ya_existe"
        if precio <= 0 or stock < 0:
            return "datos_invalidos"

        self.inventario.append({
            "nombre": nombre.strip(),
            "marca": marca.strip() or "Genérica",
            "categoria": categoria.strip() or "General",
            "precio": float(precio),
            "stock": int(stock),
            "proveedor_id": proveedor_id
        })
        self.guardar_inventario()
        return True
    
    def eliminar_producto(self, nombre_producto):
        producto = next((p for p in self.inventario if p["nombre"] == nombre_producto), None)
        if producto:
            self.inventario.remove(producto)
            self.guardar_inventario()
            return True
        return False

    def editar_producto(self, nombre_original, nuevos_datos):
        producto = next((p for p in self.inventario if p["nombre"] == nombre_original), None)
        if producto:
            producto["nombre"] = nuevos_datos.get("nombre", producto["nombre"])
            producto["marca"] = nuevos_datos.get("marca", producto["marca"])
            producto["categoria"] = nuevos_datos.get("categoria", producto["categoria"])
            producto["precio"] = float(nuevos_datos.get("precio", producto["precio"]))
            producto["stock"] = int(nuevos_datos.get("stock", producto["stock"]))
            self.guardar_inventario()
            return True
        return False

    # ---------------- Usuarios y Roles ----------------
    def validar_usuario(self, usuario, password):
        return usuario in self.usuarios and self.usuarios[usuario] == password

    def obtener_rol(self, usuario):
        return self.roles.get(usuario, "Cajero")

    # ---------------- Ticket y Ventas ----------------
    def agregar_al_ticket(self, nombre_producto, cantidad):
        dulce = next((d for d in self.inventario if d["nombre"] == nombre_producto), None)
        if not dulce:
            return "no_encontrado"

        item_en_ticket = next((item for item in self.ticket_actual if item["producto"] == nombre_producto), None)
        cantidad_actual = item_en_ticket["cantidad"] if item_en_ticket else 0
        
        if (cantidad_actual + cantidad) > dulce["stock"]:
            return "stock_insuficiente"

        if item_en_ticket:
            item_en_ticket["cantidad"] += cantidad
            item_en_ticket["subtotal"] = item_en_ticket["cantidad"] * dulce["precio"]
        else:
            self.ticket_actual.append({
                "producto": nombre_producto,
                "cantidad": cantidad,
                "subtotal": dulce["precio"] * cantidad
            })
        return True
         
    def calcular_total(self):
        return sum(item["subtotal"] for item in self.ticket_actual)

    def procesar_cobro(self, pago_cliente):
        total = self.calcular_total()
        if pago_cliente >= total:
            cambio = pago_cliente - total
            for item_ticket in self.ticket_actual:
                for dulce in self.inventario:
                    if dulce["nombre"] == item_ticket["producto"]:
                        dulce["stock"] -= item_ticket["cantidad"]
            self.ticket_actual.clear()
            return True, cambio
        return False, 0.0

    def obtener_inventario_filtrado(self, texto_busqueda, marca, categoria):
        resultados = []
        for producto in self.inventario:
            coincide_nombre = texto_busqueda in producto["nombre"].lower()
            coincide_marca = marca == "Todas" or producto["marca"] == marca
            coincide_cat = categoria == "Todas" or producto["categoria"] == categoria
            prov = self.obtener_proveedor(producto.get("proveedor_id"))
            nombre_prov = prov["nombre"] if prov else "—"

            if coincide_nombre and coincide_marca and coincide_cat:
                if producto["stock"] == 0:
                    estado = "AGOTADO"
                elif producto["stock"] < 15:
                    estado = "BAJO"
                else:
                    estado = "MEDIO"

                resultados.append({
                    "nombre": producto["nombre"],
                    "marca": producto["marca"],
                    "categoria": producto["categoria"],
                    "precio": producto["precio"],
                    "stock": producto["stock"],
                    "estado": estado,
                    "proveedor": nombre_prov
                })
        return resultados