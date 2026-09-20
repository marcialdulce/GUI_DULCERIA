
from vistas.ventana_principal import VistaDulceria 

# ============================================================
# EJECUCIÓN POR PARTE DEL MAIN 
# ============================================================
import controlador

if __name__ == "__main__":

    ctrl = controlador.ControladorDulceria() 
    app = VistaDulceria(ctrl)
    ctrl.vista = app
    app.mainloop()separar vista.py en el paquete vistas/ y organizar MVC