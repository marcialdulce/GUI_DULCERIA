import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from vistas import estilos

MAX_TARJETAS = 40
MS_ESPERA_BUSQUEDA = 250


class PanelVentas(tk.Frame):
    def __init__(self, parent, controlador, modo_punto_venta=False, ir_a_cobros=None):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.modo_punto_venta = modo_punto_venta
        self.ir_a_cobros = ir_a_cobros
        self._productos_filtrados = []
        self._producto_marcado = None

        contenedor_principal = tk.Frame(self, bg=estilos.FONDO)
        contenedor_principal.pack(fill="both", expand=True, padx=15, pady=15)

        # --- PANEL IZQUIERDO: CATÁLOGO DE PRODUCTOS ---
        panel_izq = tk.Frame(contenedor_principal, bg=estilos.FONDO)
        panel_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))

        barra_busqueda = tk.Frame(panel_izq, bg="#3A8D96", height=42)
        barra_busqueda.pack(fill="x", pady=(0, 10))
        barra_busqueda.pack_propagate(False)

        tk.Label(
            barra_busqueda,
            text="BUSCAR (Inicio nombre / Código):",
            bg="#3A8D96",
            fg=estilos.BLANCO,
            font=("Arial", 9, "bold"),
        ).pack(side="left", padx=10)

        self.txt_buscar_venta = tk.Entry(barra_busqueda, width=22)
        self.txt_buscar_venta.pack(side="right", padx=10, pady=8)
        self._id_busqueda = None
        self.txt_buscar_venta.bind("<KeyRelease>", self._programar_busqueda)
        self.txt_buscar_venta.bind("<Return>", self._agregar_por_enter)

        self.canvas_productos = tk.Canvas(panel_izq, bg="#EAEAEA", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(panel_izq, orient="vertical", command=self.canvas_productos.yview)
        self.canvas_productos.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas_productos.pack(side="left", fill="both", expand=True)

        self.frame_lista = tk.Frame(self.canvas_productos, bg="#EAEAEA")
        self.canvas_window = self.canvas_productos.create_window((0, 0), window=self.frame_lista, anchor="nw")
        self.frame_lista.bind("<Configure>", lambda e: self.canvas_productos.configure(scrollregion=self.canvas_productos.bbox("all")))
        self.canvas_productos.bind("<Configure>", lambda e: self.canvas_productos.itemconfig(self.canvas_window, width=e.width))
        self.canvas_productos.bind("<Enter>", self._activar_scroll)
        self.canvas_productos.bind("<Leave>", self._desactivar_scroll)

        # --- PANEL DERECHO: TICKET DE VENTA ---
        panel_der = tk.Frame(contenedor_principal, bg="#F4F4F4", bd=1, relief="solid")
        panel_der.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Label(panel_der, text="TICKET DE VENTA (Marca [ ] para editar)", bg="#F4F4F4", font=("Arial", 10, "bold")).pack(pady=(10, 6))

        columnas = ("SEL", "PRODUCTO", "CANTIDAD", "PRECIO")
        self.tabla_ticket = ttk.Treeview(panel_der, columns=columnas, show="headings", height=8)
        self.tabla_ticket.heading("SEL", text="[ ]")
        self.tabla_ticket.column("SEL", width=38, anchor="center", stretch=False)

        anchos = {"PRODUCTO": 180, "CANTIDAD": 70, "PRECIO": 85}
        for col in columnas[1:]:
            self.tabla_ticket.heading(col, text=col)
            self.tabla_ticket.column(col, width=anchos[col], anchor="w" if col == "PRODUCTO" else "center")

        self.tabla_ticket.tag_configure("marcado", background="#D6EAF8", foreground="#1B4F72")
        self.tabla_ticket.pack(fill="both", expand=True, padx=10)
        self.tabla_ticket.bind("<ButtonRelease-1>", self._toggle_seleccion_ticket)

        # Controles de edición individual del carrito
        frame_editar = tk.Frame(panel_der, bg="#F4F4F4")
        frame_editar.pack(fill="x", padx=10, pady=(8, 4))

        tk.Button(
            frame_editar, text="- 1", bg="#E67E22", fg="white",
            font=("Arial", 9, "bold"), width=5, relief="flat", cursor="hand2",
            command=lambda: self._modificar_seleccionado(-1),
        ).pack(side="left", padx=(0, 5))

        tk.Button(
            frame_editar, text="+ 1", bg="#27AE60", fg="white",
            font=("Arial", 9, "bold"), width=5, relief="flat", cursor="hand2",
            command=lambda: self._modificar_seleccionado(1),
        ).pack(side="left", padx=(0, 5))

        tk.Button(
            frame_editar, text="QUITAR ARTÍCULO", bg="#C0392B", fg="white",
            font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
            command=self._quitar_seleccionado,
        ).pack(side="right")

        # Desglose con IVA incluido
        frame_desglose = tk.Frame(panel_der, bg="#F4F4F4")
        frame_desglose.pack(fill="x", padx=20, pady=(10, 8))

        fila_sub = tk.Frame(frame_desglose, bg="#F4F4F4")
        fila_sub.pack(fill="x")
        tk.Label(fila_sub, text="Subtotal (sin IVA):", bg="#F4F4F4", fg="#555555", font=("Arial", 10)).pack(side="left")
        self.label_subtotal = tk.Label(fila_sub, text="$0.00", bg="#F4F4F4", fg="#555555", font=("Arial", 10))
        self.label_subtotal.pack(side="right")

        fila_iva = tk.Frame(frame_desglose, bg="#F4F4F4")
        fila_iva.pack(fill="x", pady=(2, 4))
        tk.Label(fila_iva, text="IVA incluido (16%):", bg="#F4F4F4", fg="#555555", font=("Arial", 10)).pack(side="left")
        self.label_iva = tk.Label(fila_iva, text="$0.00", bg="#F4F4F4", fg="#555555", font=("Arial", 10))
        self.label_iva.pack(side="right")

        ttk.Separator(frame_desglose, orient="horizontal").pack(fill="x", pady=4)

        fila_total = tk.Frame(frame_desglose, bg="#F4F4F4")
        fila_total.pack(fill="x")
        tk.Label(fila_total, text="TOTAL (IVA incl.)", bg="#F4F4F4", font=("Arial", 12, "bold")).pack(side="left")
        self.label_total = tk.Label(fila_total, text="$0.00", bg="#F4F4F4", fg="#27AE60", font=("Arial", 12, "bold"))
        self.label_total.pack(side="right")

        tk.Button(
            panel_der, text="CONTINUAR A COBROS Y PAGOS", bg="#F4D03F",
            font=("Arial", 10, "bold"), relief="flat", cursor="hand2",
            command=self._continuar_a_cobros,
        ).pack(fill="x", padx=15, pady=(6, 8))

        tk.Button(
            panel_der, text="LIMPIAR CARRITO", bg="#D9534F", fg="white",
            font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
            command=self.limpiar_carrito,
        ).pack(fill="x", padx=15, pady=(0, 12))

        self.refrescar_pantalla()

    def _toggle_seleccion_ticket(self, event):
        """Marca con ☑ únicamente la fila clickeada y desmarca las demás."""
        fila_id = self.tabla_ticket.identify_row(event.y)
        if not fila_id:
            return

        vals_click = list(self.tabla_ticket.item(fila_id, "values"))
        estaba_marcado = vals_click[0] == "☑"

        for iid in self.tabla_ticket.get_children():
            vals = list(self.tabla_ticket.item(iid, "values"))
            vals[0] = "☐"
            self.tabla_ticket.item(iid, values=vals, tags=())

        if estaba_marcado:
            self._producto_marcado = None
        else:
            vals_click[0] = "☑"
            self.tabla_ticket.item(fila_id, values=vals_click, tags=("marcado",))
            self._producto_marcado = vals_click[1]

    def _programar_busqueda(self, event=None):
        if self._id_busqueda is not None:
            self.after_cancel(self._id_busqueda)
        self._id_busqueda = self.after(MS_ESPERA_BUSQUEDA, self._aplicar_busqueda)

    def _aplicar_busqueda(self):
        self._id_busqueda = None
        productos, _, _ = self.controlador.obtener_datos_ventas()
        self.dibujar_catalogo(productos)
        self.canvas_productos.yview_moveto(0)

    def _agregar_por_enter(self, event=None):
        texto = self.txt_buscar_venta.get().strip()
        if not texto:
            return

        prod_codigo = self.controlador.buscar_producto_por_codigo(texto)
        if prod_codigo:
            if prod_codigo["stock"] <= 0:
                messagebox.showwarning("Sin stock", f"No hay existencias de '{prod_codigo['nombre']}'.")
                return
            if self.controlador.procesar_agregar(prod_codigo, 1):
                self.txt_buscar_venta.delete(0, "end")
                self.refrescar_pantalla()
            return

        self._aplicar_busqueda()
        if len(self._productos_filtrados) == 1:
            self.intentar_agregar(self._productos_filtrados[0])

    def dibujar_catalogo(self, productos_disponibles):
        texto = self.txt_buscar_venta.get().strip().lower()
        if texto:
            productos_disponibles = [
                p for p in productos_disponibles
                if p["nombre"].lower().startswith(texto)
                or str(p.get("codigo_barras") or "").lower().startswith(texto)
            ]

        self._productos_filtrados = productos_disponibles

        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        if not productos_disponibles:
            tk.Label(
                self.frame_lista,
                text="No se encontraron productos que inicien con ese texto.",
                bg="#EAEAEA",
                fg="#666666",
                font=("Arial", 9, "italic"),
            ).pack(pady=20)
            return

        for producto in productos_disponibles[:MAX_TARJETAS]:
            item = tk.Frame(self.frame_lista, bg=estilos.BLANCO, pady=8, padx=10, bd=1, relief="solid")
            item.pack(fill="x", pady=2, padx=2)

            color_stock = "#C0392B" if producto["stock"] <= producto.get("stock_minimo", 5) else estilos.NEGRO
            codigo_txt = producto.get("codigo_barras") or "S/C"

            tk.Label(item, text=producto["nombre"], bg=estilos.BLANCO, font=("Arial", 9, "bold")).grid(
                row=0, column=0, sticky="w", columnspan=3
            )
            tk.Label(item, text=f"${float(producto['precio']):.2f}", bg=estilos.BLANCO, font=("Arial", 9)).grid(
                row=1, column=0, sticky="w", pady=3
            )
            tk.Label(item, text=f"STOCK: {producto['stock']}", bg=estilos.BLANCO, fg=color_stock, font=("Arial", 9, "bold")).grid(
                row=1, column=1, sticky="w", padx=12
            )
            tk.Label(item, text=f"COD: {codigo_txt}", bg=estilos.BLANCO, fg="#777777", font=("Arial", 8)).grid(
                row=1, column=2, sticky="w", padx=6
            )

            btn_agregar = tk.Button(
                item, text="AGREGAR", bg="#F4D03F", fg=estilos.NEGRO,
                font=("Arial", 9, "bold"), width=11, relief="flat", cursor="hand2",
                command=lambda p=producto: self.intentar_agregar(p),
            )
            btn_agregar.grid(row=0, column=3, rowspan=2, sticky="e", padx=5)
            item.grid_columnconfigure(3, weight=1)

    def intentar_agregar(self, producto):
        if producto["stock"] <= 0:
            messagebox.showwarning("Atención", f"No hay existencias del producto '{producto['nombre']}'.")
            return

        cantidad_pedida = simpledialog.askinteger(
            "Cantidad",
            f"¿Cuántas unidades de\n{producto['nombre']}\ndeseas agregar?",
            minvalue=1,
            maxvalue=producto["stock"],
            initialvalue=1,
        )
        if not cantidad_pedida:
            return

        _, carrito, _ = self.controlador.obtener_datos_ventas()
        cantidad_en_carrito = sum(p["cantidad"] for p in carrito if p.get("producto") == producto["nombre"])

        if (cantidad_en_carrito + cantidad_pedida) > producto["stock"]:
            messagebox.showwarning(
                "Atención",
                f"Límite excedido. Ya tienes {cantidad_en_carrito} en el carrito y solo hay {producto['stock']} en stock.",
            )
            return

        if self.controlador.procesar_agregar(producto, cantidad_pedida):
            _, carrito, _ = self.controlador.obtener_datos_ventas()
            self.dibujar_ticket(carrito, mantener_marcado=self._producto_marcado)

    def _nombre_marcado(self):
        for iid in self.tabla_ticket.get_children():
            vals = self.tabla_ticket.item(iid, "values")
            if vals and vals[0] == "☑":
                return vals[1]
        messagebox.showwarning("Selección", "Marca la casilla [ ] del artículo en el ticket.")
        return None

    def _modificar_seleccionado(self, delta):
        nombre = self._nombre_marcado()
        if not nombre:
            return
        ok, msg = self.controlador.actualizar_cantidad_ticket(nombre, delta)
        if not ok:
            messagebox.showwarning("Stock", msg)
            return
        _, carrito, _ = self.controlador.obtener_datos_ventas()
        self._producto_marcado = None if msg == "eliminado" else nombre
        self.dibujar_ticket(carrito, mantener_marcado=self._producto_marcado)

    def _quitar_seleccionado(self):
        nombre = self._nombre_marcado()
        if not nombre:
            return
        self.controlador.quitar_del_ticket(nombre)
        self._producto_marcado = None
        _, carrito, _ = self.controlador.obtener_datos_ventas()
        self.dibujar_ticket(carrito)

    def _continuar_a_cobros(self):
        _, carrito, _ = self.controlador.obtener_datos_ventas()
        if not carrito:
            messagebox.showwarning("Carrito vacío", "Agrega al menos un producto antes de pasar a cobros.")
            return
        if self.ir_a_cobros:
            self.ir_a_cobros()

    def dibujar_ticket(self, carrito, mantener_marcado=None):
        for fila in self.tabla_ticket.get_children():
            self.tabla_ticket.delete(fila)

        encontrado = False
        for item in carrito:
            nombre_prod = item.get("producto") or item.get("nombre") or "Desconocido"
            es_marcado = bool(mantener_marcado and nombre_prod == mantener_marcado)
            if es_marcado:
                encontrado = True
            self.tabla_ticket.insert(
                "",
                "end",
                values=("☑" if es_marcado else "☐", nombre_prod, item["cantidad"], f"${float(item['subtotal']):.2f}"),
                tags=("marcado",) if es_marcado else (),
            )

        if not encontrado:
            self._producto_marcado = None

        subtotal, iva, total = self.controlador.obtener_desglose_ticket()
        self.label_subtotal.config(text=f"${subtotal:.2f}")
        self.label_iva.config(text=f"${iva:.2f}")
        self.label_total.config(text=f"${total:.2f}")

    def refrescar_pantalla(self):
        productos, carrito, _ = self.controlador.obtener_datos_ventas()
        self.dibujar_catalogo(productos)
        self.dibujar_ticket(carrito, mantener_marcado=self._producto_marcado)

    def limpiar_carrito(self):
        _, carrito, _ = self.controlador.obtener_datos_ventas()
        if not carrito:
            return
        if messagebox.askyesno("Limpiar Carrito", "¿Estás seguro de vaciar el carrito actual? (Aún no se ha cobrado)"):
            self._producto_marcado = None
            self.controlador.vaciar_ticket_actual()
            self.refrescar_pantalla()

    def _activar_scroll(self, event=None):
        self.canvas_productos.bind_all("<MouseWheel>", self._on_mousewheel)

    def _desactivar_scroll(self, event=None):
        self.canvas_productos.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        if self.canvas_productos.winfo_exists():
            self.canvas_productos.yview_scroll(int(-1 * (event.delta / 120)), "units")