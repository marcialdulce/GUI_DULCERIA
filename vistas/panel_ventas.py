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
        tk.Entry(barra_busqueda, width=20).pack(side="right", padx=10, pady=8)

        frame_lista = tk.Frame(panel_izq, bg="#EAEAEA")
        frame_lista.pack(fill="both", expand=True, pady=10)

        # Llenado dinámico de productos
        for producto in self.controlador.modelo.inventario:
            item = tk.Frame(frame_lista, bg=estilos.BLANCO, pady=10, padx=10, bd=1, relief="solid")
            item.pack(fill="x", pady=2, padx=2)

            tk.Label(item, text=producto["nombre"], bg=estilos.BLANCO, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", columnspan=2)
            tk.Label(item, text=f"${producto['precio']:.2f}", bg=estilos.BLANCO, font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=5)
            tk.Label(item, text=f"STOCK: {producto['stock']}", bg=estilos.BLANCO, font=("Arial", 9)).grid(row=1, column=1, sticky="w", padx=20)

            btn_agregar = tk.Button(item, text="AGREGAR", bg="#F4D03F", fg=estilos.NEGRO, font=("Arial", 9, "bold"), width=15, relief="flat", command=lambda p=producto["nombre"]: self.controlador.procesar_agregar(p))
            btn_agregar.grid(row=0, column=2, rowspan=2, sticky="e", padx=10)
            item.grid_columnconfigure(2, weight=1)

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

        # Cargar artículos en el ticket actual
        for item in self.controlador.modelo.ticket_actual:
            self.tabla_ticket.insert("", "end", values=(item["producto"], item["cantidad"], f"${item['subtotal']:.2f}"))

        # Total
        frame_total = tk.Frame(panel_der, bg="#F4F4F4")
        frame_total.pack(fill="x", padx=20, pady=15)
        tk.Label(frame_total, text="TOTAL", bg="#F4F4F4", font=("Arial", 12, "bold")).pack(side="left")
        self.label_total = tk.Label(frame_total, text="$0.00", bg="#F4F4F4", font=("Arial", 12, "bold"))
        self.label_total.pack(side="right")

        # Botones de acción
        frame_botones = tk.Frame(panel_der, bg="#F4F4F4")
        frame_botones.pack(fill="x", padx=10, pady=10)
        tk.Button(frame_botones, text="CANCELAR", bg="#F4D03F", font=("Arial", 10, "bold"), relief="flat").pack(side="left", expand=True, fill="x", padx=5)
        tk.Button(frame_botones, text="COBRAR", bg="#F4D03F", font=("Arial", 10, "bold"), relief="flat", command=self.controlador.cobrar_ticket).pack(side="right", expand=True, fill="x", padx=5)