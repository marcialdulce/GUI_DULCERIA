import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos

class PanelInventario(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO) 
        self.controlador = controlador

        panel_principal = tk.Frame(self, bg=estilos.FONDO)
        panel_principal.pack(fill="both", expand=True, padx=20, pady=10)

        # Barra de Filtros Superior
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

        # Configuración de estilos para los colores de las filas en el Treeview
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25, font=("Arial", 9))
        self.style.configure("Treeview.Heading", font=("Arial", 9, "bold"))

        # Definimos las columnas incluyendo la opción de gestión/proveedor
        columnas = ("PRODUCTO", "MARCA", "CATEGORÍA", "PRECIO", "STOCK", "ESTADO", "ACCIÓN")
        self.tabla_inv = ttk.Treeview(panel_principal, columns=columnas, show="headings", height=10)

        for col in columnas:
            self.tabla_inv.heading(col, text=col)
            if col == "ACCIÓN":
                self.tabla_inv.column(col, anchor="center", width=130)
            else:
                self.tabla_inv.column(col, anchor="center", width=100)

        self.tabla_inv.pack(fill="both", expand=True, pady=5)
        
        # Evento para detectar clics en la tabla (útil para el botón de solicitar)
        self.tabla_inv.bind("<ButtonRelease-1>", self.clic_en_tabla)

        self.notificar_filtros()

    def notificar_filtros(self):
        texto = self.txt_buscar_inv.get().lower()
        marca = self.combo_marca.get()
        categoria = self.combo_categoria.get()

        datos_procesados = self.controlador.procesar_filtro_inventario(texto, marca, categoria)
        self.actualizar_tabla(datos_procesados)
       
    def actualizar_tabla(self, datos_procesados):
        for fila in self.tabla_inv.get_children():
            self.tabla_inv.delete(fila)

        for prod in datos_procesados:
            stock = prod["stock"]
            
            if stock == 0:
                estado = "AGOTADO"
                tag = "agotado"
                accion = "⚠️ SOLICITAR"
            elif stock < 15:
                estado = "BAJO"
                tag = "bajo"
                accion = "📦 RELLENAR"
            else:
                estado = "ÓPTIMO"
                tag = "optimo"
                accion = "---"

            # AQUÍ QUITAMOS "item_id =" PARA QUE NO MARQUE LA ADVERTENCIA
            self.tabla_inv.insert("", "end", values=(
                prod["nombre"], prod["marca"], prod["categoria"],
                f"${prod['precio']:.2f}", stock, estado, accion
            ), tags=(tag,))

        # Aplicamos colores de fondo a las filas según su estado crítico
        self.tabla_inv.tag_configure("agotado", background="#FADBD8")  # Rojo claro
        self.tabla_inv.tag_configure("bajo", background="#FCF3CF")     # Amarillo claro
        self.tabla_inv.tag_configure("optimo", background="#D4EFDF")   # Verde claro

    def clic_en_tabla(self, event):
        # Detecta si el usuario hizo clic en la columna de acción para solicitar al proveedor
        region = self.tabla_inv.identify("region", event.x, event.y)
        if region == "cell":
            columna = self.tabla_inv.identify_column(event.x)
            item = self.tabla_inv.identify_row(event.y)
            
            if columna == "#7":  # Columna de ACCIÓN
                valores = self.tabla_inv.item(item, "values")
                if valores:
                    nombre_producto = valores[0]
                    stock_actual = valores[4]
                    estado = valores[5]
                    
                    if estado != "ÓPTIMO":
                        # Llamamos al controlador para simular el pedido al proveedor
                        self.controlador.solicitar_proveedor(nombre_producto, stock_actual)
                    else:
                        messagebox.showinfo("Inventario Óptimo", f"El producto '{nombre_producto}' cuenta con stock suficiente.")