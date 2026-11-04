import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos

TITULO_EXITO = "Éxito"

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

        self.btn_hilo_reposicion = tk.Button(
            barra_filtros, text="⚡ SOLICITAR REPOSICIÓN", bg="#E67E22", fg=estilos.BLANCO, 
            font=("Arial", 9, "bold"), command=self.iniciar_hilo_reposicion
        )
        self.btn_hilo_reposicion.pack(side="right", padx=5, pady=5)

        btn_nuevo = tk.Button(
            barra_filtros, text="NUEVO PRODUCTO", bg="#27AE60", fg=estilos.BLANCO,
            font=("Arial", 9, "bold"), command=self.abrir_ventana_nuevo_producto
        )
        btn_nuevo.pack(side="right", padx=5, pady=5)

        btn_pedidos = tk.Button(barra_filtros, text="📦 VER / CANCELAR PEDIDOS", bg="#2C3E50", fg=estilos.BLANCO, 
                                font=("Arial", 9, "bold"), command=self.abrir_ventana_pedidos)
        btn_pedidos.pack(side="right", padx=5, pady=5)

        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25, font=("Arial", 9))
        self.style.configure("Treeview.Heading", font=("Arial", 9, "bold"))

        columnas = ("PRODUCTO", "MARCA", "CATEGORÍA", "PRECIO", "STOCK", "ESTADO", "PROVEEDOR", "ACCIÓN")
        self.tabla_inv = ttk.Treeview(panel_principal, columns=columnas, show="headings", height=10)

        for col in columnas:
            self.tabla_inv.heading(col, text=col)
            if col == "ACCIÓN":
                self.tabla_inv.column(col, anchor="center", width=130)
            elif col == "PROVEEDOR":
                self.tabla_inv.column(col, anchor="center", width=140)
            else:
                self.tabla_inv.column(col, anchor="center", width=100)

        self.tabla_inv.pack(fill="both", expand=True, pady=5)
        
        self.tabla_inv.bind("<ButtonRelease-1>", self.clic_en_tabla)
        self.tabla_inv.bind("<Double-Button-1>", self.doble_clic_editar) 

        self.notificar_filtros()

    # =========================================================================
    # HILO 4: REPOSICIÓN AUTOMÁTICA
    # =========================================================================
    def iniciar_hilo_reposicion(self):
        self.btn_hilo_reposicion.config(state="disabled", text="⏳ PROCESANDO REPOSICIÓN...")
        self.controlador.iniciar_reposicion_automatica(self._finalizar_hilo_reposicion)

    def _finalizar_hilo_reposicion(self, creados):
        # Tkinter exige que los cambios visuales se hagan en el hilo principal usando after()
        self.after(0, lambda: self._actualizar_ui_tras_reposicion(creados))

    def _actualizar_ui_tras_reposicion(self, creados):
        self.btn_hilo_reposicion.config(state="normal", text="⚡ SOLICITAR REPOSICIÓN")
        self.notificar_filtros()

        if creados > 0:
            messagebox.showinfo("Reposición Completada", f"Se han generado automáticamente {creados} órdenes de reposición.")
        else:
            messagebox.showinfo("Sin Cambios", "No se encontraron productos por agotarse o ya tienen un pedido pendiente activo.")

    # =========================================================================
    # MÉTODOS DE LA TABLA
    # =========================================================================
    def notificar_filtros(self):
        texto = self.txt_buscar_inv.get().lower()
        marca = self.combo_marca.get()
        categoria = self.combo_categoria.get()

        datos_procesados = self.controlador.procesar_filtro_inventario(texto, marca, categoria)
        self.actualizar_tabla(datos_procesados)
       
    def actualizar_tabla(self, datos_procesados):
        for fila in self.tabla_inv.get_children():
            self.tabla_inv.delete(fila)

        # Trae los pedidos directo de la BD
        productos_pedidos = [p["producto"] for p in self.controlador.obtener_pedidos_activos()]

        for prod in datos_procesados:
            nombre = prod["nombre"]
            stock = prod["stock"]
            
            if nombre in productos_pedidos:
                estado, tag, accion = "PENDIENTE", "pendiente", "⏳ EN PROCESO"
            elif stock == 0:
                estado, tag, accion = "AGOTADO", "agotado", "⚠️ SOLICITAR"
            elif stock < 15:
                estado, tag, accion = "BAJO", "bajo", "📦 RELLENAR"
            else:
                estado, tag, accion = "ÓPTIMO", "optimo", "+ PEDIR EXTRA"

            self.tabla_inv.insert("", "end", values=(
                nombre, prod["marca"], prod["categoria"],
                f"${prod['precio']:.2f}", stock, estado,
                prod["proveedor"], accion
            ), tags=(tag,))

        self.tabla_inv.tag_configure("pendiente", background="#D4E6F1")
        self.tabla_inv.tag_configure("agotado", background="#FADBD8")
        self.tabla_inv.tag_configure("bajo", background="#FCF3CF")
        self.tabla_inv.tag_configure("optimo", background="#D4EFDF")

    def clic_en_tabla(self, event):
        region = self.tabla_inv.identify("region", event.x, event.y)
        if region == "cell":
            columna = self.tabla_inv.identify_column(event.x)
            item = self.tabla_inv.identify_row(event.y)
            
            if columna == "#8":  # Columna de ACCIÓN
                valores = self.tabla_inv.item(item, "values")
                if valores:
                    self.abrir_dialogo_solicitud(valores[0], valores[4])

    # =========================================================================
    # MODALES: PEDIDOS
    # =========================================================================
    def abrir_dialogo_solicitud(self, producto, stock_actual):
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
            ok, msg = self.controlador.registrar_pedido_manual(producto, cantidad)
            
            if ok:
                messagebox.showinfo("Éxito", msg)
            else:
                messagebox.showerror("Error", msg)
            dialogo.destroy()
            self.notificar_filtros()

        tk.Button(dialogo, text="Confirmar Pedido", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 9, "bold"), command=confirmar_envio).pack(pady=15)

    def abrir_ventana_pedidos(self):
        ventana_pedidos = tk.Toplevel(self)
        ventana_pedidos.title("Gestión de Pedidos Activos")
        ventana_pedidos.geometry("620x380")
        ventana_pedidos.config(bg=estilos.FONDO)
        ventana_pedidos.grab_set()

        tk.Label(ventana_pedidos, text="LISTA DE PEDIDOS A PROVEEDORES", font=("Arial", 11, "bold"), bg=estilos.FONDO).pack(pady=10)

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

        def cancelar_pedido_seleccionado():
            seleccion = tabla_pedidos.selection()
            if not seleccion:
                messagebox.showwarning("Selección", "Por favor selecciona un pedido de la tabla para cancelar.", parent=ventana_pedidos)
                return
            
            item = tabla_pedidos.item(seleccion)
            id_pedido = item["values"][0] 
            
            self.controlador.cancelar_pedido(id_pedido)
            messagebox.showinfo("Cancelado", f"El pedido #{id_pedido} ha sido cancelado con éxito.", parent=ventana_pedidos)
            actualizar_tabla_pedidos()
            self.notificar_filtros()

        actualizar_tabla_pedidos()

        btn_cancelar = tk.Button(ventana_pedidos, text=" Cancelar Pedido Seleccionado", bg="#C0392B", fg=estilos.BLANCO, 
                                 font=("Arial", 9, "bold"), command=cancelar_pedido_seleccionado)
        btn_cancelar.pack(pady=12)

    # =========================================================================
    # MODALES: PRODUCTOS
    # =========================================================================
    def abrir_ventana_nuevo_producto(self):
        modal = tk.Toplevel(self)
        modal.title("Nuevo Producto")
        modal.geometry("420x460")
        modal.config(bg=estilos.FONDO)
        modal.grab_set()

        tk.Label(modal, text="ALTA DE PRODUCTO", bg=estilos.FONDO, font=("Arial", 12, "bold")).pack(pady=15)

        campos = tk.Frame(modal, bg=estilos.FONDO)
        campos.pack(pady=10)

        tk.Label(campos, text="Nombre:", bg=estilos.FONDO).grid(row=0, column=0, sticky="e", pady=5)
        entry_nombre = tk.Entry(campos, width=25)
        entry_nombre.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(campos, text="Marca:", bg=estilos.FONDO).grid(row=1, column=0, sticky="e", pady=5)
        entry_marca = tk.Entry(campos, width=25)
        entry_marca.grid(row=1, column=1, pady=5, padx=5)

        tk.Label(campos, text="Categoría:", bg=estilos.FONDO).grid(row=2, column=0, sticky="e", pady=5)
        combo_cat = ttk.Combobox(campos, values=["Gomitas", "Chocolates", "Frituras", "General"], width=22, state="readonly")
        combo_cat.current(0)
        combo_cat.grid(row=2, column=1, pady=5, padx=5)

        tk.Label(campos, text="Precio ($):", bg=estilos.FONDO).grid(row=3, column=0, sticky="e", pady=5)
        entry_precio = tk.Entry(campos, width=25)
        entry_precio.grid(row=3, column=1, pady=5, padx=5)

        tk.Label(campos, text="Stock inicial:", bg=estilos.FONDO).grid(row=4, column=0, sticky="e", pady=5)
        entry_stock = tk.Entry(campos, width=25)
        entry_stock.grid(row=4, column=1, pady=5, padx=5)

        tk.Label(campos, text="Proveedor:", bg=estilos.FONDO).grid(row=5, column=0, sticky="e", pady=5)

        proveedores = self.controlador.obtener_proveedores()
        opciones = ["— Sin proveedor —"] + [p["nombre"] for p in proveedores]
        mapa_prov = {p["nombre"]: p["id"] for p in proveedores}

        combo_prov = ttk.Combobox(campos, values=opciones, width=22, state="readonly")
        combo_prov.current(0)
        combo_prov.grid(row=5, column=1, pady=5, padx=5)

        if not proveedores:
            tk.Label(campos, text="(Registra proveedores en la pestaña PROVEEDORES)", bg=estilos.FONDO, fg="#C0392B", font=("Arial", 8, "italic")).grid(row=6, column=1, sticky="w")

        def guardar():
            nombre_prov_seleccionado = combo_prov.get()
            proveedor_id = mapa_prov.get(nombre_prov_seleccionado)

            ok, msg = self.controlador.procesar_nuevo_producto(
                entry_nombre.get(), entry_marca.get(), combo_cat.get(),
                entry_precio.get(), entry_stock.get(), proveedor_id
            )
            if ok:
                messagebox.showinfo(TITULO_EXITO, msg, parent=modal)
                modal.destroy()
                self.notificar_filtros()
            else:
                messagebox.showerror("Error", msg, parent=modal)

        tk.Button(modal, text="GUARDAR", bg="#27AE60", fg="white", font=("Arial", 10, "bold"), width=15, command=guardar).pack(pady=20)
        
    def doble_clic_editar(self, event):
        """Abre el modal de edición al hacer doble clic en una fila."""
        item = self.tabla_inv.identify_row(event.y)
        if not item:
            return
        valores = self.tabla_inv.item(item, "values")
        if valores:
            # Extraemos los datos visuales para pasarlos al modal (ya no dependemos de memoria)
            nombre = valores[0]
            marca = valores[1]
            categoria = valores[2]
            precio = valores[3].replace("$", "") # Quitamos el signo $
            stock = valores[4]
            self.abrir_ventana_editar_producto(nombre, marca, categoria, precio, stock)

    def abrir_ventana_editar_producto(self, nombre_original, marca_actual, categoria_actual, precio_actual, stock_actual):
        modal = tk.Toplevel(self)
        modal.title(f"Editar Producto - {nombre_original}")
        modal.geometry("420x420")
        modal.config(bg=estilos.FONDO)
        modal.grab_set()

        # Centrar modal
        x = (modal.winfo_screenwidth() // 2) - 210
        y = (modal.winfo_screenheight() // 2) - 210
        modal.geometry(f"420x420+{x}+{y}")

        tk.Label(modal, text="EDITAR PRODUCTO", bg=estilos.FONDO, font=("Arial", 12, "bold")).pack(pady=15)

        campos = tk.Frame(modal, bg=estilos.FONDO)
        campos.pack(pady=10)

        tk.Label(campos, text="Nombre:", bg=estilos.FONDO).grid(row=0, column=0, sticky="e", pady=5)
        entry_nombre = tk.Entry(campos, width=25)
        entry_nombre.insert(0, nombre_original)
        entry_nombre.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(campos, text="Marca:", bg=estilos.FONDO).grid(row=1, column=0, sticky="e", pady=5)
        entry_marca = tk.Entry(campos, width=25)
        entry_marca.insert(0, marca_actual)
        entry_marca.grid(row=1, column=1, pady=5, padx=5)

        tk.Label(campos, text="Categoría:", bg=estilos.FONDO).grid(row=2, column=0, sticky="e", pady=5)
        combo_cat = ttk.Combobox(campos, values=["Gomitas", "Chocolates", "Frituras", "General"], width=22, state="readonly")
        combo_cat.set(categoria_actual)
        combo_cat.grid(row=2, column=1, pady=5, padx=5)

        tk.Label(campos, text="Precio ($):", bg=estilos.FONDO).grid(row=3, column=0, sticky="e", pady=5)
        entry_precio = tk.Entry(campos, width=25)
        entry_precio.insert(0, precio_actual)
        entry_precio.grid(row=3, column=1, pady=5, padx=5)

        tk.Label(campos, text="Stock:", bg=estilos.FONDO).grid(row=4, column=0, sticky="e", pady=5)
        entry_stock = tk.Entry(campos, width=25)
        entry_stock.insert(0, stock_actual)
        entry_stock.grid(row=4, column=1, pady=5, padx=5)

        def guardar_cambios():
            ok, msg = self.controlador.procesar_editar_producto(
                nombre_original, entry_nombre.get(), entry_marca.get(),
                combo_cat.get(), entry_precio.get(), entry_stock.get()
            )
            if ok:
                messagebox.showinfo(TITULO_EXITO, msg, parent=modal)
                modal.destroy()
                self.notificar_filtros() 
            else:
                messagebox.showerror("Error", msg, parent=modal)

        tk.Button(modal, text="GUARDAR CAMBIOS", bg="#F4D03F", font=("Arial", 10, "bold"), relief="flat", command=guardar_cambios).pack(pady=20)