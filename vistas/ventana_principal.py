import tkinter as tk
from tkinter import messagebox
from vistas import estilos
from vistas.login import PantallaLogin
from vistas.menu_principal import MenuPrincipal

class VistaDulceria(tk.Tk):
    def __init__(self, controlador):
        super().__init__()
        self.controlador = controlador
        self.title("Dulcería")

        # CONFIGURACIÓN DE PANTALLA COMPLETA
        self.attributes('-fullscreen', True)  # Activa la pantalla completa
        self.configure(bg=estilos.FONDO)

        # Evento para salir de pantalla completa presionando la tecla Escape (ESC)
        self.bind("<Escape>", self.salir_pantalla_completa)
        self.bind("<F11>", self.alternar_pantalla_completa) # Opcional: F11 para alternar
        
        self.contenedor = tk.Frame(self, bg=estilos.FONDO)
        self.contenedor.pack(fill="both", expand=True)
        self.contenedor.grid_rowconfigure(0, weight=1)
        self.contenedor.grid_columnconfigure(0, weight=1)

        self.pantallas = {}

        for clase_pantalla in (PantallaLogin, MenuPrincipal):
            frame = clase_pantalla(parent=self.contenedor, controlador=self.controlador)
            self.pantallas[clase_pantalla.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew") 

        self.mostrar_pantalla("PantallaLogin")

    def mostrar_pantalla(self, nombre):
        self.pantallas[nombre].tkraise()

    def mostrar_alerta(self, titulo, mensaje, tipo="info"):
        if tipo == "info":
            messagebox.showinfo(titulo, mensaje)
        else:
            messagebox.showerror(titulo, mensaje)

    # Métodos auxiliares para controlar la pantalla completa
    def salir_pantalla_completa(self, event=None):
        self.attributes('-fullscreen', False)

    def alternar_pantalla_completa(self, event=None):
        estado_actual = self.attributes('-fullscreen')
        self.attributes('-fullscreen', not estado_actual)