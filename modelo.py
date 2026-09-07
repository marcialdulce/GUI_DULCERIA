# ============================================================
# USUARIOS DEL SISTEMA
# ============================================================

class ModeloDulceria:

        def __init__(self):
                self.usuarios = {
                        "Dulce" : "1234",
                        "America" : "1234",
                        "Daniel" : "1234",
                        "Yeray" : "1234",
                        "Josue" : "1234"
                }

# Validación de los usuarios dentro del sistema

        def validar_usuario (self, usuario, password):
                if usuario in self.usuarios and self.usuarios[usuario] == password:
                    return True
                return False

#Evaluar y calcular el cambio para el ticket

        def procesar_cobro(self, pago_cliente):
            total = self.calcular_total()
            if pago_cliente >= total:
                cambio = pago_cliente - total
                self.ticket_actual.clear() # Vaciamos la lista temporal
                return True, cambio
            return False, 0.0


        
        