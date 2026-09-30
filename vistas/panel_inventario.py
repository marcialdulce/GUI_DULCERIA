import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos

class PanelInventario(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO) 
        self.controlador = controlador

        # Lista de pedidos vacía para que el usuario elija y agregue sus propios pedidos
        if not hasattr(self.controlador, "pedidos_activos"):
            self.controlador.pedidos_activos = []

        panel_principal = tk.Frame(self, bg=estilos.FONDO)
        panel_principal.pack(fill="both", expand=True, padx=20, pady=10)

        # Barra de Filtros Superior + Botón para ver/gestionar pedidos
        barra_filtros = tk.Frame(panel_principal, bg="#3A8D96", height=40)
        barra_filtros.pack(fill="x", pady=(0, 10))
        barra_filtros.pack_propagate(False)

        tk.Label(barra_filtros, text="BUSCAR", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 9, "bold")).pack(side="left", padx=10)
        self.txt_buscar_inv = tk.Entry(barra_filtros, width=15)
        self.txt_buscar_inv.pack(side="left", padx=5)
        self.txt_buscar_inv.bind("<KeyRelease>", lambda e: self.notificar_filtros())

        tk.Label(barra_filtros, text="MARCA", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 9, "bold")).pack(side="left", padx=(10, 5))
        self.combo_marca = ttk.Combobox(barra_filtros, values=["Todas", "Ricolino", "Carlos V", "Totis"], width=10, state="readonly")
        self.combo_marca.current(0)
        self.combo_marca.pack(side="left")
        self.combo_marca.bind("<<ComboboxSelected>>", lambda e: self.notificar_filtros())

        tk.Label(barra_filtros, text="CATEGORÍA", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 9, "bold")).pack(side="left", padx=(10, 5))
        self.combo_categoria = ttk.Combobox(barra_filtros, values=["Todas", "Chocolates", "Gomitas", "Frituras"], width=10, state="readonly")
        self.combo_categoria.current(0)
        self.combo_categoria.pack(side="left")
        self.combo_categoria.bind("<<ComboboxSelected>>", lambda e: self.notificar_filtros())

        # Botón integrador dentro de la misma pestaña para ver pedidos
        btn_pedidos = tk.Button(barra_filtros, text="📦 VER / CANCELAR PEDIDOS", bg="#2C3E50", fg=estilos.BLANCO, 
                                font=("Arial", 9, "bold"), command=self.abrir_ventana_pedidos)
        btn_pedidos.pack(side="right", padx=10, pady=5)

        # Configuración de estilos para los colores de las filas en el Treeview principal
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
        
        # Evento para detectar clics en la tabla
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

        # Extraer nombres de productos que tienen un pedido activo/pendiente
        productos_pedidos = [p["producto"] for p in self.controlador.pedidos_activos if p["estado"] in ["Pendiente", "En camino"]]

        for prod in datos_procesados:
            nombre = prod["nombre"]
            stock = prod["stock"]
            
            # Verificamos si ya tiene un pedido activo
            if nombre in productos_pedidos:
                estado = "PENDIENTE"
                tag = "pendiente"
                accion = "⏳ EN PROCESO"
            elif stock == 0:
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
                accion = "➕ PEDIR EXTRA"

            self.tabla_inv.insert("", "end", values=(
                nombre, prod["marca"], prod["categoria"],
                f"${prod['precio']:.2f}", stock, estado, accion
            ), tags=(tag,))

        # Aplicamos colores de fondo a las filas (cambiamos pendiente a azul pastel suave)
        self.tabla_inv.tag_configure("pendiente", background="#D4E6F1") # Azul pastel suave para pedidos en curso
        self.tabla_inv.tag_configure("agotado", background="#FADBD8")    # Rojo claro
        self.tabla_inv.tag_configure("bajo", background="#FCF3CF")       # Amarillo claro
        self.tabla_inv.tag_configure("optimo", background="#D4EFDF")     # Verde claro

    def clic_en_tabla(self, event):
        region = self.tabla_inv.identify("region", event.x, event.y)
        if region == "cell":
            columna = self.tabla_inv.identify_column(event.x)
            item = self.tabla_inv.identify_row(event.y)
            
            if columna == "#7":  # Columna de ACCIÓN
                valores = self.tabla_inv.item(item, "values")
                if valores:
                    nombre_producto = valores[0]
                    stock_actual = valores[4]
                    self.abrir_dialogo_solicitud(nombre_producto, stock_actual)

    def abrir_dialogo_solicitud(self, producto, stock_actual):
        """Ventana emergente para elegir la cantidad a solicitar al proveedor"""
        dialogo = tk.Toplevel(self)
        dialogo.title(f"Solicitar Proveedor - {producto}")
        dialogo.geometry("350x220")
        dialogo.config(bg=estilos.FONDO)
        dialogo.grab_set()

        tk.Label(dialogo, text=f"Producto: {producto}", font=("Arial", 10, "bold"), bg=estilos.FONDO).pack(pady=(15, 5))
        tk.Label(dialogo, text=f"Stock actual en almacén: {stock_actual}", font=("Arial", 9), bg=estilos.FONDO).pack(pady=5)

        tk.Label(dialogo, text="Cantidad a solicitar:", font=("Arial", 9, "bold"), bg=estilos.FONDO).pack(pady=5)
        txt_cantidad = tk.Spinbox(dialogo, from_=1, to=500, width=10, font=("Arial", 10))
        txt_cantidad.pack(pady=5)

        def confirmar_envio():
            cantidad = int(txt_cantidad.get())
            
            # Verificar si ya existe un pedido pendiente para este producto para acumular la cantidad
            pedido_existente = next((p for p in self.controlador.pedidos_activos if p["producto"] == producto and p["estado"] == "Pendiente"), None)
            
            if pedido_existente:
                pedido_existente["cantidad"] += cantidad
                messagebox.showinfo("Actualizado", f"El producto ya tenía un pedido pendiente. Se han sumado {cantidad} unidades (Total: {pedido_existente['cantidad']}).")
            else:
                nuevo_id = max([p["id"] for p in self.controlador.pedidos_activos], default=0) + 1
                self.controlador.pedidos_activos.append({
                    "id": nuevo_id,
                    "producto": producto,
                    "cantidad": cantidad,
                    "estado": "Pendiente"
                })
                messagebox.showinfo("Éxito", f"Se han solicitado {cantidad} unidades de {producto}.")
            
            dialogo.destroy()
            self.notificar_filtros() # Refrescar la tabla principal para que se pinte con el nuevo tono

        btn_enviar = tk.Button(dialogo, text="Confirmar Pedido", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 9, "bold"), command=confirmar_envio)
        btn_enviar.pack(pady=15)

    def abrir_ventana_pedidos(self):
        """Ventana para visualizar los pedidos hechos, seleccionarlos claramente y cancelarlos"""
        ventana_pedidos = tk.Toplevel(self)
        ventana_pedidos.title("Gestión de Pedidos Activos")
        ventana_pedidos.geometry("620x380")
        ventana_pedidos.config(bg=estilos.FONDO)
        ventana_pedidos.grab_set()

        tk.Label(ventana_pedidos, text="LISTA DE PEDIDOS A PROVEEDORES", font=("Arial", 11, "bold"), bg=estilos.FONDO).pack(pady=10)

        # Configurar estilo para que la fila seleccionada se pinte con un color distintivo claramente visible
        style_pedidos = ttk.Style()
        style_pedidos.map("Treeview", background=[('selected', '#2980B9')], foreground=[('selected', 'white')])

        cols_pedidos = ("ID", "PRODUCTO", "CANTIDAD", "ESTADO")
        tabla_pedidos = ttk.Treeview(ventana_pedidos, columns=cols_pedidos, show="headings", height=8, selectmode="browse")
        for col in cols_pedidos:
            tabla_pedidos.heading(col, text=col)
            tabla_pedidos.column(col, anchor="center", width=130)
        tabla_pedidos.pack(pady=5, padx=10, fill="both", expand=True)

        def actualizar_tabla_pedidos():
            for row in tabla_pedidos.get_children():
                tabla_pedidos.delete(row)
            for p in self.controlador.pedidos_activos:
                tabla_pedidos.insert("", "end", values=(p["id"], p["producto"], p["cantidad"], p["estado"]))

        actualizar_tabla_pedidos()

        def cancelar_pedido_seleccionado():
            seleccion = tabla_pedidos.selection()
            if not seleccion:
                messagebox.showwarning("Selección", "Por favor selecciona un pedido de la tabla para cancelar.")
                return
            
            item = tabla_pedidos.item(seleccion)
            id_pedido = item["values"][0]
            
            # Filtrar para eliminar el pedido cancelado
            self.controlador.pedidos_activos = [p for p in self.controlador.pedidos_activos if p["id"] != id_pedido]
            messagebox.showinfo("Cancelado", f"El pedido #{id_pedido} ha sido cancelado con éxito.")
            
            actualizar_tabla_pedidos()
            self.notificar_filtros() # Refrescar la tabla de inventario principal para quitar el color si ya no hay pedidos

        btn_cancelar = tk.Button(ventana_pedidos, text="❌ Cancelar Pedido Seleccionado", bg="#C0392B", fg=estilos.BLANCO, 
                                 font=("Arial", 9, "bold"), command=cancelar_pedido_seleccionado)
        btn_cancelar.pack(pady=12)