
from vistas.ventana_principal import VistaDulceria 

# ============================================================
# EJECUCIÓN POR PARTE DEL MAIN 
# ============================================================
import controladores.controlador as controlador

if __name__ == "__main__":

    ctrl = controlador.ControladorDulceria() 
    app = VistaDulceria(ctrl)
    ctrl.vista = app
    app.mainloop()


    