import tkinter as tk
from tkinter import ttk, messagebox
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

        btn_eliminar = tk.Button(barra_filtros, text=" ELIMINAR", bg="#C0392B", fg=estilos.BLANCO, 
                                 font=("Arial", 9, "bold"), command=self.eliminar_producto)
        btn_eliminar.pack(side="right", padx=5, pady=5)

        btn_pedidos = tk.Button(barra_filtros, text=" VER PEDIDOS", bg="#2C3E50", fg=estilos.BLANCO, 
                                font=("Arial", 9, "bold"), command=self.abrir_ventana_pedidos)
        btn_pedidos.pack(side="right", padx=5, pady=5)

        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25, font=("Arial", 9))
        self.style.configure("Treeview.Heading", font=("Arial", 9, "bold"))

        columnas = ("PRODUCTO", "MARCA", "CATEGORÍA", "PRECIO", "STOCK", "ESTADO")
        self.tabla_inv = ttk.Treeview(panel_principal, columns=columnas, show="headings", height=10)

        for col in columnas:
            self.tabla_inv.heading(col, text=col)
            self.tabla_inv.column(col, anchor="center", width=100)

        self.tabla_inv.pack(fill="both", expand=True, pady=5)
        self.notificar_filtros()

    def notificar_filtros(self):
        datos = self.controlador.obtener_inventario_filtrado(
            self.txt_buscar_inv.get().lower(), self.combo_marca.get(), self.combo_categoria.get()
        )
        self.actualizar_tabla(datos)
       
    def actualizar_tabla(self, datos_procesados):
        for fila in self.tabla_inv.get_children():
            self.tabla_inv.delete(fila)

        productos_pedidos = [p["producto"] for p in self.controlador.obtener_pedidos_activos()]

        for prod in datos_procesados:
            nombre = prod["nombre"]
            stock = prod["stock"]
            
            if nombre in productos_pedidos:
                estado, tag = "PENDIENTE", "pendiente"
            elif stock == 0:
                estado, tag = "AGOTADO", "agotado"
            elif stock < 15:
                estado, tag = "BAJO", "bajo"
            else:
                estado, tag = "ÓPTIMO", "optimo"

            self.tabla_inv.insert("", "end", values=(
                nombre, prod["marca"], prod["categoria"], f"${prod['precio']:.2f}", stock, estado
            ), tags=(tag,))

        self.tabla_inv.tag_configure("pendiente", background="#D4E6F1")
        self.tabla_inv.tag_configure("agotado", background="#FADBD8")
        self.tabla_inv.tag_configure("bajo", background="#FCF3CF")
        self.tabla_inv.tag_configure("optimo", background="#D4EFDF")

    def eliminar_producto(self):
        sel = self.tabla_inv.selection()
        if not sel:
            messagebox.showwarning("Selección", "Selecciona un producto de la tabla.")
            return
        item = self.tabla_inv.item(sel[0])
        nombre = item["values"][0]
        if messagebox.askyesno("Eliminar Producto", f"¿Estás seguro de eliminar '{nombre}'?"):
            exito, msg = self.controlador.procesar_eliminar_producto(nombre)
            if exito:
                messagebox.showinfo("Éxito", msg)
                self.notificar_filtros()
            else:
                messagebox.showerror("Error", msg)

    def abrir_ventana_pedidos(self):
        ventana_pedidos = tk.Toplevel(self)
        ventana_pedidos.title("Gestión de Pedidos Activos")
        ancho, alto = 620, 420
        x = (ventana_pedidos.winfo_screenwidth() // 2) - (ancho // 2)
        y = (ventana_pedidos.winfo_screenheight() // 2) - (alto // 2)
        ventana_pedidos.geometry(f"{ancho}x{alto}+{x}+{y}")
        ventana_pedidos.config(bg=estilos.FONDO)
        ventana_pedidos.grab_set()

        tk.Label(ventana_pedidos, text="PEDIDOS A PROVEEDORES PENDIENTES", font=("Arial", 11, "bold"), bg=estilos.FONDO).pack(pady=10)

        cols_pedidos = ("ID", "PRODUCTO", "CANTIDAD", "ESTADO")
        tabla_pedidos = ttk.Treeview(ventana_pedidos, columns=cols_pedidos, show="headings", height=8, selectmode="browse")
        for col in cols_pedidos:
            tabla_pedidos.heading(col, text=col)
            tabla_pedidos.column(col, anchor="center", width=130)
        tabla_pedidos.pack(pady=5, padx=10, fill="both", expand=True)

        def actualizar_tabla_pedidos():
            for row in tabla_pedidos.get_children():
                tabla_pedidos.delete(row)
            for p in self.controlador.obtener_pedidos_activos():
                tabla_pedidos.insert("", "end", values=(p["id_pedido"], p["producto"], p["cantidad"], p["estado"]))

        def recibir_pedido_seleccionado():
            seleccion = tabla_pedidos.selection()
            if not seleccion:
                messagebox.showwarning("Selección", "Selecciona un pedido.", parent=ventana_pedidos)
                return
            item = tabla_pedidos.item(seleccion[0])
            id_pedido = item["values"][0] 
            try:
                if self.controlador.recibir_pedido(id_pedido):
                    messagebox.showinfo("Recibido", f"Pedido #{id_pedido} recibido. Stock actualizado.", parent=ventana_pedidos)
                    actualizar_tabla_pedidos()
                    self.notificar_filtros()
            except Exception as e:
                messagebox.showerror("Error", f"Error: {e}", parent=ventana_pedidos)

        def cancelar_pedido_seleccionado():
            seleccion = tabla_pedidos.selection()
            if not seleccion:
                messagebox.showwarning("Selección", "Selecciona un pedido.", parent=ventana_pedidos)
                return
            item = tabla_pedidos.item(seleccion[0])
            id_pedido = item["values"][0] 
            self.controlador.cancelar_pedido(id_pedido)
            messagebox.showinfo("Cancelado", f"Pedido #{id_pedido} cancelado.", parent=ventana_pedidos)
            actualizar_tabla_pedidos()
            self.notificar_filtros()

        actualizar_tabla_pedidos()

        frame_btns = tk.Frame(ventana_pedidos, bg=estilos.FONDO)
        frame_btns.pack(pady=10)

        tk.Button(frame_btns, text=" RECIBIR MERCANCÍA", bg="#27AE60", fg="white", font=("Arial", 9, "bold"), command=recibir_pedido_seleccionado).pack(side="left", padx=5)
        tk.Button(frame_btns, text=" CANCELAR PEDIDO", bg="#C0392B", fg="white", font=("Arial", 9, "bold"), command=cancelar_pedido_seleccionado).pack(side="left", padx=5)