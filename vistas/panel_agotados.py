import tkinter as tk
from tkinter import ttk
from vistas import estilos

class PanelAgotados(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        panel_principal = tk.Frame(self, bg=estilos.FONDO)
        panel_principal.pack(fill="both", expand=True, padx=35, pady=35)

        # ----------------------------------------------------
        # TABLA DE AGOTADOS
        # ----------------------------------------------------
        columnas = ("PRODUCTO", "MARCA", "STOCK", "ESTADO")
        self.tabla_agotados = ttk.Treeview(panel_principal, columns=columnas, show="headings", height=16)

        for col in columnas:
            self.tabla_agotados.heading(col, text=col)

        self.tabla_agotados.column("PRODUCTO", width=250, anchor="center")
        self.tabla_agotados.column("MARCA", width=200, anchor="center")
        self.tabla_agotados.column("STOCK", width=150, anchor="center")
        self.tabla_agotados.column("ESTADO", width=150, anchor="center")

        self.tabla_agotados.pack(fill="both", expand=True)
        self.refrescar_pantalla()

    def intentar_actualizar(self):
        self.refrescar_pantalla()

    def dibujar_tabla(self, datos_agotados):
        for fila in self.tabla_agotados.get_children():
            self.tabla_agotados.delete(fila)

        for fila_datos in datos_agotados:
            self.tabla_agotados.insert("", "end", values=fila_datos)

    def refrescar_pantalla(self):
        datos = self.controlador.obtener_datos_agotados()
        self.dibujar_tabla(datos)