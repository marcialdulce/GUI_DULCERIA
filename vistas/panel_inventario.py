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
        self.txt_buscar_inv.bind("<KeyRelease>", lambda e: self.aplicar_filtros_inventario())

        tk.Label(barra_filtros, text="MARCA", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 9, "bold")).pack(side="left", padx=(15, 5))
        self.combo_marca = ttk.Combobox(barra_filtros, values=["Todas", "Ricolino", "Carlos V", "Totis"], width=12, state="readonly")
        self.combo_marca.current(0)
        self.combo_marca.pack(side="left")
        self.combo_marca.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros_inventario())

        tk.Label(barra_filtros, text="CATEGORÍA", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 9, "bold")).pack(side="left", padx=(15, 5))
        self.combo_categoria = ttk.Combobox(barra_filtros, values=["Todas", "Chocolates", "Gomitas", "Dulces", "Frituras"], width=12, state="readonly")
        self.combo_categoria.current(0)
        self.combo_categoria.pack(side="left")
        self.combo_categoria.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros_inventario())

        columnas = ("PRODUCTO", "MARCA", "CATEGORÍA", "PRECIO", "STOCK", "ESTADO")
        self.tabla_inv = ttk.Treeview(panel_principal, columns=columnas, show="headings", height=8)

        for col in columnas:
            self.tabla_inv.heading(col, text=col)
            self.tabla_inv.column(col, anchor="center", width=110)

        self.tabla_inv.pack(fill="both", expand=True, pady=5)
        self.aplicar_filtros_inventario()

    # La función de filtros ahora vive exclusivamente dentro de esta clase
    def aplicar_filtros_inventario(self):
        for fila in self.tabla_inv.get_children():
            self.tabla_inv.delete(fila)

        texto_busqueda = self.txt_buscar_inv.get().lower()
        marca_seleccionada = self.combo_marca.get()
        categoria_seleccionada = self.combo_categoria.get()

        for producto in self.controlador.modelo.inventario:
            coincide_nombre = texto_busqueda in producto["nombre"].lower()
            coincide_marca = marca_seleccionada == "Todas" or producto["marca"] == marca_seleccionada
            coincide_cat = categoria_seleccionada == "Todas" or producto["categoria"] == categoria_seleccionada

            if coincide_nombre and coincide_marca and coincide_cat:
                if producto["stock"] == 0:
                    estado = "AGOTADO"
                elif producto["stock"] < 15:
                    estado = "BAJO"
                else:
                    estado = "MEDIO"

                self.tabla_inv.insert("", "end", values=(
                    producto["nombre"], producto["marca"], producto["categoria"],
                    f"${producto['precio']:.2f}", producto["stock"], estado
                ))