import tkinter as tk
from tkinter import ttk
from vistas import estilos

class PanelInventario(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO) 
        self.controlador = controlador

        panel_principal = tk.Frame(self, bg=estilos.FONDO)
        panel_principal.pack(fill="both", expand=True, padx=20, pady=10)

        barra_filtros = tk.Frame(panel_principal, bg="#3A8D96", height=40)
        barra_filtros.pack(fill="x", pady=(0, 10))
        barra_filtros.pack_propagate(False)

        tk.Label(barra_filtros, text="BUSCAR", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 9, "bold")).pack(side="left", padx=10)
        self.txt_buscar_inv = tk.Entry(barra_filtros, width=18)
        self.txt_buscar_inv.pack(side="left", padx=5)
        self.txt_buscar_inv.bind("<KeyRelease>", lambda e: self.notificar_filtros())

        tk.Label(barra_filtros, text="MARCA", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 9, "bold")).pack(side="left", padx=(15, 5))
        self.combo_marca = ttk.Combobox(barra_filtros, values=["Todas", "Ricolino", "Carlos V", "Totis"], width=12, state="readonly")
        self.combo_marca.current(0)
        self.combo_marca.pack(side="left")
        self.combo_marca.bind("<<ComboboxSelected>>", lambda e: self.notificar_filtros())

        tk.Label(barra_filtros, text="CATEGORÍA", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 9, "bold")).pack(side="left", padx=(15, 5))
        self.combo_categoria = ttk.Combobox(barra_filtros, values=["Todas", "Chocolates", "Gomitas", "Frituras"], width=12, state="readonly")
        self.combo_categoria.current(0)
        self.combo_categoria.pack(side="left")
        self.combo_categoria.bind("<<ComboboxSelected>>", lambda e: self.notificar_filtros())

        columnas = ("PRODUCTO", "MARCA", "CATEGORÍA", "PRECIO", "STOCK", "ESTADO")
        self.tabla_inv = ttk.Treeview(panel_principal, columns=columnas, show="headings", height=8)

        for col in columnas:
            self.tabla_inv.heading(col, text=col)
            self.tabla_inv.column(col, anchor="center", width=110)

        self.tabla_inv.pack(fill="both", expand=True, pady=5)
        self.notificar_filtros()

    def  notificar_filtros(self):
        # Obtiene los valores de las cajas de texto
        texto = self.txt_buscar_inv.get().lower()
        marca = self.combo_marca.get()
        categoria = self.combo_categoria.get()

        datos_procesados = self.controlador.procesar_filtro_inventario(texto, marca, categoria)

        self.actualizar_tabla(datos_procesados)
       
    def actualizar_tabla(self, datos_procesados):
        # Borra el contenido actual de la tabla
        for fila in self.tabla_inv.get_children():
            self.tabla_inv.delete(fila)

        # Inserta los nuevos datos en la tabla
        for prod in datos_procesados:
            self.tabla_inv.insert("", "end", values=(
                prod["nombre"], prod ["marca"], prod["categoria"],
                prod["precio"], prod["stock"], prod["estado"]
            ))