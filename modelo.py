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

        
        