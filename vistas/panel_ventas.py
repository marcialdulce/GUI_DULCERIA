import tkinter as tk
from tkinter import ttk, messagebox
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

        self.frame_lista = tk.Frame(panel_izq, bg="#EAEAEA")
        self.frame_lista.pack(fill="both", expand=True)

        # ====================================================
        # PANEL DERECHO (Ticket de Venta)
        # ====================================================
        panel_der = tk.Frame(contenedor_principal, bg="#F4F4F4", bd=1, relief="solid")
        panel_der.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Label(panel_der, text="TICKET DE VENTA", bg="#F4F4F4", font=("Arial", 10, "bold")).pack(pady=10)

        columnas = ("PRODUCTO", "CANTIDAD", "PRECIO")
        self.tabla_ticket = ttk.Treeview(panel_der, columns=columnas, show="headings", height=6)

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

        # --------------OPCIONES DE COBRO Y FACTURA-------------
        self.metodo_pago = tk.StringVar(value="Efectivo")
        self.tipo_tarjeta = tk.StringVar(value="Crédito")
        self.quiere_facturar = tk.BooleanVar(value=False)

        frame_opciones = tk.Frame(panel_der, bg="#F4F4F4")
        frame_opciones.pack(fill="x", padx=20, pady=5)

        # Métodos de pago
        tk.Label(frame_opciones, text="Método de pago:", bg="#F4F4F4", font=("Arial", 9, "bold")).pack(anchor="w")
        frame_radios = tk.Frame(frame_opciones, bg="#F4F4F4")
        frame_radios.pack(anchor="w", pady=2)
        
        tk.Radiobutton(frame_radios, text="Efectivo", variable=self.metodo_pago, value="Efectivo", 
                       bg="#F4F4F4", command=self.toggle_metodo_pago).pack(side="left")
        tk.Radiobutton(frame_radios, text="Tarjeta", variable=self.metodo_pago, value="Tarjeta", 
                       bg="#F4F4F4", command=self.toggle_metodo_pago).pack(side="left")

        # Sub-opciones de Tarjeta (Crédito / Débito) - Ocultas por defecto
        self.frame_tipo_tarjeta = tk.Frame(frame_opciones, bg="#F4F4F4")
        tk.Radiobutton(self.frame_tipo_tarjeta, text="Crédito", variable=self.tipo_tarjeta, value="Crédito", bg="#F4F4F4").pack(side="left", padx=(0, 10))
        tk.Radiobutton(self.frame_tipo_tarjeta, text="Débito", variable=self.tipo_tarjeta, value="Débito", bg="#F4F4F4").pack(side="left")

        # Opción si el cliente desea facturar
        tk.Label(frame_opciones, text="¿El cliente requiere Factura?", bg="#F4F4F4", font=("Arial", 9, "bold")).pack(anchor="w", pady=(5,0))

        frame_radios_fac = tk.Frame(frame_opciones, bg="#F4F4F4")
        frame_radios_fac.pack(anchor="w")
        tk.Radiobutton(frame_radios_fac, text="No", variable=self.quiere_facturar, value=False, bg="#F4F4F4", command=self.toggle_datos_factura).pack(side="left")
        tk.Radiobutton(frame_radios_fac, text="Si", variable=self.quiere_facturar, value=True, bg="#F4F4F4", command=self.toggle_datos_factura).pack(side="left")
        
        # Formulario completo de factura (Oculto por defecto con Nombre, Correo y RFC)
        self.frame_datos_factura = tk.Frame(frame_opciones, bg="#F4F4F4")
        
        tk.Label(self.frame_datos_factura, text="Nombre Completo:", bg="#F4F4F4").grid(row=0, column=0, sticky="e", pady=2)
        self.entry_nombre = tk.Entry(self.frame_datos_factura, width=22)
        self.entry_nombre.grid(row=0, column=1, pady=2, padx=5)

        tk.Label(self.frame_datos_factura, text="Correo:", bg="#F4F4F4").grid(row=1, column=0, sticky="e", pady=2)
        self.entry_correo = tk.Entry(self.frame_datos_factura, width=22)
        self.entry_correo.grid(row=1, column=1, pady=2, padx=5)

        tk.Label(self.frame_datos_factura, text="RFC:", bg="#F4F4F4").grid(row=2, column=0, sticky="e", pady=2)
        self.entry_rfc = tk.Entry(self.frame_datos_factura, width=22)
        self.entry_rfc.grid(row=2, column=1, pady=2, padx=5)

        # BOTÓN DE COBRAR (Conectado a la función procesar_cobro_principal)
        frame_botones = tk.Frame(panel_der, bg="#F4F4F4")
        frame_botones.pack(fill="x", padx=10, pady=10)
        tk.Button(frame_botones, text="COBRAR", bg="#F4D03F", font=("Arial", 10, "bold"), relief="flat", command=self.procesar_cobro_principal).pack(side="right", expand=True, fill="x", padx=5)
        
        self.refrescar_pantalla()

    # FUNCIÓN PARA MOSTRAR/OCULTAR TIPO DE TARJETA
    def toggle_metodo_pago(self):
        if self.metodo_pago.get() == "Tarjeta":
            self.frame_tipo_tarjeta.pack(anchor="w", pady=2)
        else:
            self.frame_tipo_tarjeta.pack_forget()

    # FUNCIÓN QUE MUESTRA O OCULTA LOS DATOS DE LA FACTURA
    def toggle_datos_factura(self):
        if self.quiere_facturar.get():
            self.frame_datos_factura.pack(anchor="w", pady=5)
        else:
            self.frame_datos_factura.pack_forget()
            self.entry_nombre.delete(0, tk.END)
            self.entry_correo.delete(0, tk.END)
            self.entry_rfc.delete(0, tk.END)

    def intentar_agregar(self, nombre_producto):
        self.controlador.procesar_agregar(nombre_producto)
        self.refrescar_pantalla()

    # FUNCIÓN QUE EJECUTA EL COBRO DESDE LA PANTALLA PRINCIPAL
    def procesar_cobro_principal(self):
        metodo = self.metodo_pago.get()
        # Si pagó con tarjeta, podemos adjuntar si es crédito o débito (puedes estructurarlo como guste tu controlador)
        detalle_pago = f"{metodo} ({self.tipo_tarjeta.get()})" if metodo == "Tarjeta" else metodo

        datos_factura = None
        if self.quiere_facturar.get():
            datos_factura = {
                "requiere": True,
                "nombre": self.entry_nombre.get(),
                "correo": self.entry_correo.get(),
                "rfc": self.entry_rfc.get()
            }
            # Validación rápida opcional por si dejan campos vacíos al requerir factura
            if not datos_factura["nombre"] or not datos_factura["rfc"]:
                messagebox.showwarning("Campos incompletos", "Por favor completa los datos de facturación obligatorios.")
                return

        # Mandamos los datos recolectados al controlador
        if hasattr(self.controlador, "procesar_cobro_avanzado"):
            self.controlador.procesar_cobro_avanzado(detalle_pago, datos_factura)
        elif hasattr(self.controlador, "procesar_cobro"):
            self.controlador.procesar_cobro(detalle_pago, datos_factura)
        else:
            messagebox.showinfo("Éxito", "Cobro registrado correctamente.")

        self.refrescar_pantalla()

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