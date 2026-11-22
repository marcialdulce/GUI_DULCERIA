import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from vistas import estilos
from vistas.login import PantallaLogin
from vistas.menu_principal import MenuPrincipal


class VistaDulceria(ttk.Window):
    def __init__(self, controlador):
        super().__init__(themename="flatly")
        self.controlador = controlador
        self.title("Dulcería")

        self.attributes("-fullscreen", True)
        self.configure(bg=estilos.FONDO)

        self.bind("<Escape>", self.salir_pantalla_completa)
        self.bind("<F11>", self.alternar_pantalla_completa)
        self.protocol("WM_DELETE_WINDOW", self.al_cerrar_ventana)

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

    def al_cerrar_ventana(self):
        try:
            if self.controlador.intentar_cerrar_aplicacion():
                self.destroy()
        except Exception as e:
            if messagebox.askyesno(
                "Error al cerrar caja",
                f"Ocurrió un error al intentar cerrar el turno:\n{e}\n\n¿Deseas forzar el cierre del programa?",
            ):
                self.destroy()

    def salir_pantalla_completa(self, event=None):
        self.attributes("-fullscreen", False)
        self.centrar_ventana()

    def alternar_pantalla_completa(self, event=None):
        estado_actual = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not estado_actual)
        if estado_actual:
            self.centrar_ventana()

    def centrar_ventana(self):
        self.update_idletasks()
        ancho_ventana = 1024
        alto_ventana = 700
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        x = (ancho_pantalla // 2) - (ancho_ventana // 2)
        y = (alto_pantalla // 2) - (alto_ventana // 2)
        self.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")