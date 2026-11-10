import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos

MAX_TARJETAS = 40        
MS_ESPERA_BUSQUEDA = 250  

class PanelVentas(tk.Frame):
    def __init__(self, parent, controlador, modo_punto_venta=False, ir_a_cobros=None):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.modo_punto_venta = modo_punto_venta
        self.ir_a_cobros = ir_a_cobros

        contenedor_principal = tk.Frame(self, bg=estilos.FONDO)
        contenedor_principal.pack(fill="both", expand=True, padx=15, pady=15)

        panel_izq = tk.Frame(contenedor_principal, bg=estilos.FONDO)
        panel_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))

        barra_busqueda = tk.Frame(panel_izq, bg="#3A8D96", height=40)
        barra_busqueda.pack(fill="x", pady=(0, 10))
        barra_busqueda.pack_propagate(False)

        tk.Label(barra_busqueda, text="BUSCAR PRODUCTO", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 10, "bold")).pack(side="left", padx=10)
        self.txt_buscar_venta = tk.Entry(barra_busqueda, width=20)
        self.txt_buscar_venta.pack(side="right", padx=10, pady=8)
        self._id_busqueda = None
        self.txt_buscar_venta.bind("<KeyRelease>", self._programar_busqueda)

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

        panel_der = tk.Frame(contenedor_principal, bg="#F4F4F4", bd=1, relief="solid")
        panel_der.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Label(panel_der, text="TICKET DE VENTA", bg="#F4F4F4", font=("Arial", 10, "bold")).pack(pady=10)

        columnas = ("PRODUCTO", "CANTIDAD", "PRECIO")
        self.tabla_ticket = ttk.Treeview(panel_der, columns=columnas, show="headings", height=6)
        for col in columnas:
            self.tabla_ticket.heading(col, text=col)
            self.tabla_ticket.column(col, width=140, anchor="center")
        self.tabla_ticket.pack(fill="both", expand=True, padx=10)

        frame_total = tk.Frame(panel_der, bg="#F4F4F4")
        frame_total.pack(fill="x", padx=20, pady=15)
        tk.Label(frame_total, text="TOTAL", bg="#F4F4F4", font=("Arial", 12, "bold")).pack(side="left")
        self.label_total = tk.Label(frame_total, text="$0.00", bg="#F4F4F4", font=("Arial", 12, "bold"))
        self.label_total.pack(side="right")
        
        tk.Button(panel_der, text="CONTINUAR A COBROS Y PAGOS", bg="#F4D03F",
                  font=("Arial", 10, "bold"), relief="flat", command=self.ir_a_cobros).pack(fill="x", padx=15, pady=15)
            
        tk.Button(panel_der, text="LIMPIAR CARRITO", bg="#D9534F", fg="white",
                  font=("Arial", 9, "bold"), relief="flat", command=self.limpiar_carrito).pack(fill="x", padx=15, pady=(0, 15))

        self.refrescar_pantalla()

    def _programar_busqueda(self, event=None):
        if self._id_busqueda is not None:
            self.after_cancel(self._id_busqueda)
        self._id_busqueda = self.after(MS_ESPERA_BUSQUEDA, self._aplicar_busqueda)

    def _aplicar_busqueda(self):
        self._id_busqueda = None
        productos, _, _ = self.controlador.obtener_datos_ventas()
        self.dibujar_catalogo(productos)
        self.canvas_productos.yview_moveto(0)

    def dibujar_catalogo(self, productos_disponibles):
        texto = self.txt_buscar_venta.get().strip().lower()
        if texto:
            productos_disponibles = [
                p for p in productos_disponibles
                if texto in p["nombre"].lower() or texto in (p.get("marca") or "").lower()
            ]
        
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        for producto in productos_disponibles[:MAX_TARJETAS]:
            item = tk.Frame(self.frame_lista, bg=estilos.BLANCO, pady=8, padx=10, bd=1, relief="solid")
            item.pack(fill="x", pady=2, padx=2)

            tk.Label(item, text=producto["nombre"], bg=estilos.BLANCO, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", columnspan=2)
            tk.Label(item, text=f"${producto['precio']:.2f}", bg=estilos.BLANCO, font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=3)
            tk.Label(item, text=f"STOCK: {producto['stock']}", bg=estilos.BLANCO, font=("Arial", 9)).grid(row=1, column=1, sticky="w", padx=15)

            btn_agregar = tk.Button(item, text="AGREGAR", bg="#F4D03F", fg=estilos.NEGRO, font=("Arial", 9, "bold"), width=12, relief="flat", 
                                    command=lambda p=producto["nombre"]: self.intentar_agregar(p))
            btn_agregar.grid(row=0, column=2, rowspan=2, sticky="e", padx=5)
            item.grid_columnconfigure(2, weight=1)

    def intentar_agregar(self, nombre_producto):
        self.controlador.procesar_agregar(nombre_producto)
        _, carrito, total = self.controlador.obtener_datos_ventas()
        self.dibujar_ticket(carrito, total)

    def dibujar_ticket(self, carrito, total):
        for fila in self.tabla_ticket.get_children():
            self.tabla_ticket.delete(fila)
        for item in carrito:
            self.tabla_ticket.insert("", "end", values=(item["producto"], item["cantidad"], f"${item['subtotal']:.2f}"))
        self.label_total.config(text=f"${total:.2f}")

    def refrescar_pantalla(self):
        productos, carrito, total = self.controlador.obtener_datos_ventas()
        self.dibujar_catalogo(productos)
        self.dibujar_ticket(carrito, total)

    def limpiar_carrito(self):
        if messagebox.askyesno("Limpiar Carrito", "¿Estás seguro de vaciar el carrito actual? (Aún no se ha cobrado)"):
            self.controlador.vaciar_ticket_actual()
            self.refrescar_pantalla()

    def _activar_scroll(self, event=None):
        self.canvas_productos.bind_all("<MouseWheel>", self._on_mousewheel)

    def _desactivar_scroll(self, event=None):
        self.canvas_productos.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        if self.canvas_productos.winfo_exists():
            self.canvas_productos.yview_scroll(int(-1 * (event.delta / 120)), "units")