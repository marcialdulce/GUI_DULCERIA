# ============================================================
# USUARIOS DEL SISTEMA
# ============================================================

class ModeloDulceria:

        def __init__(self):

         # Usuarios del sistema
         self.usuarios = {
                        "Dulce" : "1234",
                        "America" : "1234",
                        "Daniel" : "1234",
                        "Yeray" : "1234",
                        "Josue" : "1234"
         }

        # El ticket debe iniciar completamente vacío
         self.ticket_actual = [] 
        
        # Definimos exactamente 4 productos con sus datos reales
         self.inventario = [
            {"nombre": "Gomitas", "marca": "Ricolino", "categoria": "Gomitas", "precio": 15.0, "stock": 20},
            {"nombre": "Chocolate", "marca": "Carlos V", "categoria": "Chocolates", "precio": 12.0, "stock": 15},
            {"nombre": "Pap's",  "marca": "Totis", "categoria": "Frituras", "precio": 4.0, "stock": 50},
            {"nombre": "Panditas",  "marca": "Ricolino", "categoria": "Gomitas", "precio": 20.0, "stock": 10}
        ]

        # Validación de los usuarios dentro del sistema
        def validar_usuario (self, usuario, password):
           if usuario in self.usuarios and self.usuarios[usuario] == password:
                return True
           return False 

        def agregar_al_ticket(self, nombre_producto, cantidad):
            # Buscar el producto directamente en el inventario
            dulce = next((d for d in self.inventario if d["nombre"] == nombre_producto), None)
            
            if not dulce:
                return "no_encontrado"

            # Buscar si el producto ya existe en el ticket actual
            item_en_ticket = next((item for item in self.ticket_actual if item["producto"] == nombre_producto), None)

            # Validar si hay suficiente stock disponible sumando lo que ya hay
            cantidad_actual = item_en_ticket["cantidad"] if item_en_ticket else 0
            
            if (cantidad_actual + cantidad) > dulce["stock"]:
                return "stock_insuficiente"

            #  Si pasa la validación, actualizamos el existente o agregamos uno nuevo
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

        # Evaluar y calcular el cambio para el ticket
        def procesar_cobro(self, pago_cliente):
            total = self.calcular_total()
            if pago_cliente >= total:
                cambio = pago_cliente - total

                # Descontar del stock antes de vaciar el ticket
                for item_ticket in self.ticket_actual:
                 for dulce in self.inventario:
                    if dulce["nombre"] == item_ticket["producto"]:
                        dulce["stock"] -= item_ticket["cantidad"]
                        
                 self.ticket_actual.clear() # Vaciamos la lista temporal
                return True, cambio
            return False, 0.0

        def obtener_inventario_filtrado(self, texto_busqueda, marca, categoria):
            resultados = []

            for producto in self.inventario:
                # Veirifica si el proudcto coincide con los filtros
                coincide_nombre = texto_busqueda in producto["nombre"].lower()
                coincide_marca = marca == "Todas" or producto["marca"] == marca
                coincide_cat = categoria == "Todas" or producto["categoria"] == categoria

                if coincide_nombre and coincide_marca and coincide_cat:

                    # Asigna el estado dependiendo de la cantidad en stock
                    if producto["stock"] == 0:
                        estado = "AGOTADO"
                    elif producto["stock"] < 15:
                        estado = "BAJO"
                    else:
                        estado = "MEDIO"

                    # Guarda el producto con su nuevo estado en la lista
                    resultados.append({
                        "nombre": producto["nombre"],
                        "marca": producto["marca"],
                        "categoria": producto["categoria"],
                        "precio": producto["precio"],
                        "stock": producto["stock"],
                        "estado": estado

                    })

            return resultados

        def registrar_venta_historica(self, total, metodo_pago, requiere_factura, rfc="", razon_social=""):
            datos_venta = {
                "total": total,
                "metodo_pago": metodo_pago,
                "facturado": requiere_factura,
                "datos_fiscales": {
                    "rfc": rfc,
                    "razon_social": razon_social
                },
                "articulos": self.ticket_actual.copy() 
            }

            self.historial_ventas.append(datos_venta)
            

        
        