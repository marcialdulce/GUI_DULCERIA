import tkinter as tk
from tkinter import messagebox
from vistas.estilos import estilos
from vistas.login import PantallaLogin
from vistas.menu_principal import MenuPrincipal

class VistaDulceria(tk.Tk):
    def __init__(self, controlador):
        super().__init__()
        self.controlador = controlador
        self.title("Dulcería")
        self.geometry("1000x650")
        self.resizable(False, False)
        self.configure(bg=estilos.FONDO)

        self.contenedor = tk.Frame(self, bg=estilos.FONDO)
        self.contenedor.pack(fill="both", expand=True)
        self.contenedor.grid_rowconfigure(0, weight=1)
        self.contenedor.grid_columnconfigure(0, weight=1)

        self.pantallas = {}

        for Pantalla in (PantallaLogin, MenuPrincipal):
            frame = Pantalla(parent=self.contenedor, controlador=self.controlador)
            self.pantallas[Pantalla.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.mostrar_pantalla("PantallaLogin")

    def mostrar_pantalla(self, nombre):
        self.pantallas[nombre].tkraise()

    def mostrar_alerta(self, titulo, mensaje, tipo="info"):
        if tipo == "info":
            messagebox.showinfo(titulo, mensaje)
        else:
            messagebox.showerror(titulo, mensaje)