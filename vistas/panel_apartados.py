import tkinter as tk
from tkinter import ttk
from vistas import estilos

class PanelApartados(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        # ----------------------------------------------------
        # 1. BARRA SUPERIOR (Se empaqueta PRIMERO para que quede arriba)
        # ----------------------------------------------------
        frame_titulo = tk.Frame(self, bg="#3A8D96", height=40)
        frame_titulo.pack(fill="x", side="top")
        frame_titulo.pack_propagate(False)

        tk.Label(
            frame_titulo,
            text="  CONTROL DE APARTADOS",
            bg="#3A8D96",
            fg="white",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=10)

        # ----------------------------------------------------
        # 2. PANEL PRINCIPAL (Para contener la tabla y sus márgenes)
        # ----------------------------------------------------
        panel_principal = tk.Frame(self, bg=estilos.FONDO)
        panel_principal.pack(fill="both", expand=True, padx=20, pady=10)

        # ----------------------------------------------------
        # 3. TABLA DE APARTADOS
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