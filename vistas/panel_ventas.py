import tkinter as tk
from tkinter import ttk
from vistas import estilos

class PanelVentas(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        # Contenedor principal que se expande de forma responsiva al dividir pantalla
        contenedor_principal = tk.Frame(self, bg=estilos.FONDO)
        contenedor_principal.pack(fill="both", expand=True, padx=15, pady=15)

        # ====================================================
        # PANEL IZQUIERDO (Buscador y Catálogo)
        # ====================================================
        panel_izq = tk.Frame(contenedor_principal, bg=estilos.FONDO)
        panel_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))

        barra_busqueda = tk.Frame(panel_izq, bg="#3A8D96", height=40)
        barra_busqueda.pack(fill="x", pady=(0, 10))
        barra_busqueda.pack_propagate(False)

        tk.Label(barra_busqueda, text="BUSCAR PRODUCTO", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 10, "bold")).pack(side="left", padx=10)
        self.txt_buscar_venta = tk.Entry(barra_busqueda, width=20)
        self.txt_buscar_venta.pack(side="right", padx=10, pady=8)

        # Canvas con Scrollbar o Frame contenedor adaptativo para el catálogo
        self.frame_lista = tk.Frame(panel_izq, bg="#EAEAEA")
        self.frame_lista.pack(fill="both", expand=True)

        # ====================================================
        # PANEL DERECHO (Ticket de Venta)
        # ====================================================
        panel_der = tk.Frame(contenedor_principal, bg="#F4F4F4", bd=1, relief="solid")
        panel_der.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Label(panel_der, text="TICKET DE VENTA", bg="#F4F4F4", font=("Arial", 10, "bold")).pack(pady=10)

        columnas = ("PRODUCTO", "CANTIDAD", "PRECIO")
        self.tabla_ticket = ttk.Treeview(panel_der, columns=columnas, show="headings", height=12)

        for col in columnas:
            self.tabla_ticket.heading(col, text=col)

        self.tabla_ticket.column("PRODUCTO", width=140, anchor="w")
        self.tabla_ticket.column("CANTIDAD", width=70, anchor="center")
        self.tabla_ticket.column("PRECIO", width=70, anchor="center")
        self.tabla_ticket.pack(fill="both", expand=True, padx=10)

        frame_total = tk.Frame(panel_der, bg="#F4F4F4")
        frame_total.pack(fill="x", padx=20, pady=15)
        tk.Label(frame_total, text="TOTAL", bg="#F4F4F4", font=("Arial", 12, "bold")).pack(side="left")
        
        self.label_total = tk.Label(frame_total, text="$0.00", bg="#F4F4F4", font=("Arial", 12, "bold"))
        self.label_total.pack(side="right")

        frame_botones = tk.Frame(panel_der, bg="#F4F4F4")
        frame_botones.pack(fill="x", padx=10, pady=10)
        tk.Button(frame_botones, text="COBRAR", bg="#F4D03F", font=("Arial", 10, "bold"), relief="flat", command=self.abrir_ventana_cobro).pack(side="right", expand=True, fill="x", padx=5)
        
        self.refrescar_pantalla()

    def intentar_agregar(self, nombre_producto):
        # Llamamos al método original de tu controlador que ya funcionaba
        self.controlador.procesar_agregar(nombre_producto)
        self.refrescar_pantalla()

    def abrir_ventana_cobro(self):
        modal = tk.Toplevel(self)
        modal.title("Caja - Cobro y Facturación")
        modal.geometry("450x580")
        modal.config(bg=estilos.FONDO)
        modal.grab_set()

        tk.Label(modal, text="PROCESAR PAGO", bg=estilos.FONDO, font=("Arial", 12, "bold")).pack(pady=15)

        # Selección de Método de Pago
        frame_pago = tk.LabelFrame(modal, text=" Método de Pago ", bg=estilos.FONDO, font=("Arial", 10, "bold"))
        frame_pago.pack(fill="x", padx=20, pady=10)

        tipo_pago = tk.StringVar(value="Efectivo")
        tk.Radiobutton(frame_pago, text="Efectivo", variable=tipo_pago, value="Efectivo", bg=estilos.FONDO).pack(side="left", padx=20, pady=10)
        tk.Radiobutton(frame_pago, text="Tarjeta", variable=tipo_pago, value="Tarjeta", bg=estilos.FONDO).pack(side="right", padx=20, pady=10)

        # Sección de Facturación Opcional
        frame_factura = tk.LabelFrame(modal, text=" Datos de Facturación (Opcional) ", bg=estilos.FONDO, font=("Arial", 10, "bold"))
        frame_factura.pack(fill="x", padx=20, pady=10)

        # Función para habilitar o deshabilitar los campos según el Checkbutton
        def alternar_campos_factura():
            estado = "normal" if requiere_factura.get() else "disabled"
            txt_nombre.config(state=estado)
            txt_apellidos.config(state=estado)
            txt_correo.config(state=estado)
            txt_rfc.config(state=estado)

        requiere_factura = tk.BooleanVar(value=False)
        chk_factura = tk.Checkbutton(frame_factura, text="¿Requiere factura?", variable=requiere_factura, 
                                     command=alternar_campos_factura, bg=estilos.FONDO)
        chk_factura.pack(anchor="w", padx=10, pady=5)

        campos_factura_frame = tk.Frame(frame_factura, bg=estilos.FONDO)
        campos_factura_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(campos_factura_frame, text="Nombre(s):", bg=estilos.FONDO).grid(row=0, column=0, sticky="w", pady=2)
        txt_nombre = tk.Entry(campos_factura_frame, width=30, state="disabled")
        txt_nombre.grid(row=0, column=1, pady=2)

        tk.Label(campos_factura_frame, text="Apellidos:", bg=estilos.FONDO).grid(row=1, column=0, sticky="w", pady=2)
        txt_apellidos = tk.Entry(campos_factura_frame, width=30, state="disabled")
        txt_apellidos.grid(row=1, column=1, pady=2)

        tk.Label(campos_factura_frame, text="Correo:", bg=estilos.FONDO).grid(row=2, column=0, sticky="w", pady=2)
        txt_correo = tk.Entry(campos_factura_frame, width=30, state="disabled")
        txt_correo.grid(row=2, column=1, pady=2)

        tk.Label(campos_factura_frame, text="RFC:", bg=estilos.FONDO).grid(row=3, column=0, sticky="w", pady=2)
        txt_rfc = tk.Entry(campos_factura_frame, width=30, state="disabled")
        txt_rfc.grid(row=3, column=1, pady=2)

        def finalizar_cobro():
            # Aquí mandas los datos recolectados al controlador
            datos_factura = {
                "requiere": requiere_factura.get(),
                "nombre": txt_nombre.get(),
                "apellidos": txt_apellidos.get(),
                "correo": txt_correo.get(),
                "rfc": txt_rfc.get()
            } if requiere_factura.get() else None

            # Envias tipo de pago y datos de factura a tu controlador
            self.controlador.procesar_cobro_avanzado(tipo_pago.get(), datos_factura)
            modal.destroy()
            self.refrescar_pantalla()

        tk.Button(modal, text="CONFIRMAR COBRO", bg="#F4D03F", font=("Arial", 10, "bold"), relief="flat", command=finalizar_cobro).pack(pady=20)

    def dibujar_catalogo(self, productos_disponibles):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        for producto in productos_disponibles:
            item = tk.Frame(self.frame_lista, bg=estilos.BLANCO, pady=8, padx=10, bd=1, relief="solid")
            item.pack(fill="x", pady=2, padx=2)

            tk.Label(item, text=producto["nombre"], bg=estilos.BLANCO, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", columnspan=2)
            tk.Label(item, text=f"${producto['precio']:.2f}", bg=estilos.BLANCO, font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=3)
            tk.Label(item, text=f"STOCK: {producto['stock']}", bg=estilos.BLANCO, font=("Arial", 9)).grid(row=1, column=1, sticky="w", padx=15)

            btn_agregar = tk.Button(item, text="AGREGAR", bg="#F4D03F", fg=estilos.NEGRO, font=("Arial", 9, "bold"), width=12, relief="flat", 
                                    command=lambda p=producto["nombre"]: self.intentar_agregar(p))
            btn_agregar.grid(row=0, column=2, rowspan=2, sticky="e", padx=5)
            item.grid_columnconfigure(2, weight=1)

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