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
            {"nombre": "Gomitas", "marca": "Ricolino", "precio": 15.0, "stock": 20},
            {"nombre": "Chocolate", "marca": "Carlos V", "precio": 12.0, "stock": 15},
            {"nombre": "Mazapán",  "marca": "De la Rosa", "precio": 5.0, "stock": 50},
            {"nombre": "Panditas",  "marca": "Ricolino", "precio": 20.0, "stock": 10}
        ]

        # Validación de los usuarios dentro del sistema
        def validar_usuario (self, usuario, password):
           if usuario in self.usuarios and self.usuarios[usuario] == password:
                return True
           return False

        def agregar_al_ticket(self, nombre_producto, cantidad):
         for dulce in self.inventario:
            if dulce["nombre"] == nombre_producto:
                self.ticket_actual.append({
                    "producto": nombre_producto,
                    "cantidad": cantidad,
                    "subtotal": dulce["precio"] * cantidad
                })
                return True
         return False

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
            



        
        