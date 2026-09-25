import tkinter as tk
from tkinter import ttk
from vistas import estilos

class PanelVentas(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        # ====================================================
        # PANEL IZQUIERDO (Buscador y Catálogo)
        # ====================================================
        panel_izq = tk.Frame(self, bg=estilos.FONDO)
        panel_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        barra_busqueda = tk.Frame(panel_izq, bg="#3A8D96", height=40)
        barra_busqueda.pack(fill="x")
        barra_busqueda.pack_propagate(False)

        tk.Label(barra_busqueda, text="BUSCAR PRODUCTO", bg="#3A8D96", fg=estilos.BLANCO, font=("Arial", 10, "bold")).pack(side="left", padx=10)
        self.txt_buscar_venta = tk.Entry(barra_busqueda, width=20)
        self.txt_buscar_venta.pack(side="right", padx=10, pady=8)

        self.frame_lista = tk.Frame(panel_izq, bg="#EAEAEA")
        self.frame_lista.pack(fill="both", expand=True, pady=10)


        # ====================================================
        # PANEL DERECHO (Ticket de Venta)
        # ====================================================
        panel_der = tk.Frame(self, bg="#F4F4F4", bd=1, relief="solid")
        panel_der.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=20)

        tk.Label(panel_der, text="TICKET DE VENTA", bg="#F4F4F4", font=("Arial", 10, "bold")).pack(pady=10)

        columnas = ("PRODUCTO", "CANTIDAD", "PRECIO")
        self.tabla_ticket = ttk.Treeview(panel_der, columns=columnas, show="headings", height=12)

        for col in columnas:
            self.tabla_ticket.heading(col, text=col)

        self.tabla_ticket.column("PRODUCTO", width=150)
        self.tabla_ticket.column("CANTIDAD", width=80, anchor="center")
        self.tabla_ticket.column("PRECIO", width=80, anchor="center")
        self.tabla_ticket.pack(fill="both", expand=True, padx=10)

        frame_total = tk.Frame(panel_der, bg="#F4F4F4")
        frame_total.pack(fill="x", padx=20, pady=15)
        tk.Label(frame_total, text="TOTAL", bg="#F4F4F4", font=("Arial", 12, "bold")).pack(side="left")
        
        self.label_total = tk.Label(frame_total, text="$0.00", bg="#F4F4F4", font=("Arial", 12, "bold"))
        self.label_total.pack(side="right")

        frame_botones = tk.Frame(panel_der, bg="#F4F4F4")
        frame_botones.pack(fill="x", padx=10, pady=10)
        tk.Button(frame_botones, text="COBRAR", bg="#F4D03F", font=("Arial", 10, "bold"), relief="flat", command=self.intentar_cobrar).pack(side="right", expand=True, fill="x", padx=5)
        self.refrescar_pantalla()

    def intentar_agregar(self, nombre_producto):
            self.controlador.procesar_agregar(nombre_producto)
            self.refrescar_pantalla()

    def intentar_cobrar(self):
        # El controlador hace la validacion matematica y muestra los mensajes
        self.controlador.cobrar_ticket()
        # La pantalla se vuelve a dibujar sola
        self.refrescar_pantalla()
    
    # El controlador llama a esta funcion pasandole la lista del modelo
    def dibujar_catalogo(self, productos_disponibles):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        for producto in productos_disponibles:
            item = tk.Frame(self.frame_lista, bg=estilos.BLANCO, pady=10, padx=10, bd=1, relief="solid")
            item.pack(fill="x", pady=2, padx=2)

            tk.Label(item, text=producto["nombre"], bg=estilos.BLANCO, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", columnspan=2)
            tk.Label(item, text=f"${producto['precio']:.2f}", bg=estilos.BLANCO, font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=5)
            tk.Label(item, text=f"STOCK: {producto['stock']}", bg=estilos.BLANCO, font=("Arial", 9)).grid(row=1, column=1, sticky="w", padx=20)

            btn_agregar = tk.Button(item, text="AGREGAR", bg="#F4D03F", fg=estilos.NEGRO, font=("Arial", 9, "bold"), width=15, relief="flat", 
                                    command=lambda p=producto["nombre"]: self.intentar_agregar(p))
            btn_agregar.grid(row=0, column=2, rowspan=2, sticky="e", padx=10)
            item.grid_columnconfigure(2, weight=1)

    # El controlador llama a esta funcion pasandole el carrito y el total
    def dibujar_ticket(self, carrito, total):
        # Borrar la tabla vieja
        for fila in self.tabla_ticket.get_children():
            self.tabla_ticket.delete(fila)

        # Insertar el nuevo carrito
        for item in carrito:
            self.tabla_ticket.insert("", "end", values=(item["producto"], item["cantidad"], f"${item['subtotal']:.2f}"))

        # Actualizamos la etiqueta del total visual
        self.label_total.config(text=f"${total:.2f}")

    def refrescar_pantalla(self):
        # Le pedimos los datos al Controlador
        productos, carrito, total = self.controlador.obtener_datos_ventas()
        self.dibujar_catalogo(productos)
        self.dibujar_ticket(carrito, total)