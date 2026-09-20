import tkinter as tk
from tkinter import ttk
from vistas.estilos import *

class PanelApartados(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=FONDO)
        self.controlador = controlador

        panel_principal = tk.Frame(self, bg=FONDO)
        panel_principal.pack(fill="both", expand=True, padx=20, pady=10)

        # ----------------------------------------------------
        # BARRA SUPERIOR
        # ----------------------------------------------------
        barra_apartados = tk.Frame(panel_principal, bg="#3A8D96", height=40)
        barra_apartados.pack(fill="x", pady=(0, 10))
        barra_apartados.pack_propagate(False)

        tk.Label(barra_apartados, text="APARTADOS", bg="#3A8D96", fg=BLANCO, font=("Arial", 9, "bold")).pack(side="left", padx=12)

        # ----------------------------------------------------
        # TABLA DE APARTADOS
        # ----------------------------------------------------
        columnas = ("PRODUCTO", "NOMBRE", "FECHA DE ENTREGA", "PRECIO", "UNIDADES APARTADAS")
        self.tabla_apartados = ttk.Treeview(panel_principal, columns=columnas, show="headings", height=16)

        for col in columnas:
            self.tabla_apartados.heading(col, text=col)

        self.tabla_apartados.column("PRODUCTO", width=180, anchor="center")
        self.tabla_apartados.column("NOMBRE", width=180, anchor="center")
        self.tabla_apartados.column("FECHA DE ENTREGA", width=180, anchor="center")
        self.tabla_apartados.column("PRECIO", width=120, anchor="center")
        self.tabla_apartados.column("UNIDADES APARTADAS", width=220, anchor="center")

        self.tabla_apartados.pack(fill="both", expand=True)