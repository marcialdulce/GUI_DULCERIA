import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos


class PanelCobros(tk.Frame):
    """Pantalla exclusiva para recibir y confirmar el pago del ticket actual."""
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        tk.Label(self, text="COBROS Y PAGOS", bg=estilos.FONDO,
                 fg="#4A2E35", font=("Arial", 20, "bold")).pack(pady=(20, 12))

        cuerpo = tk.Frame(self, bg="#F4F4F4", bd=1, relief="solid")
        cuerpo.pack(fill="both", expand=True, padx=35, pady=15)
        tk.Label(cuerpo, text="RESUMEN DE COMPRA", bg="#F4F4F4",
                 font=("Arial", 12, "bold")).pack(pady=10)

        columnas = ("PRODUCTO", "CANTIDAD", "IMPORTE")
        self.tabla = ttk.Treeview(cuerpo, columns=columnas, show="headings", height=10)
        for col in columnas:
            self.tabla.heading(col, text=col)
        self.tabla.column("PRODUCTO", width=260, anchor="w")
        self.tabla.column("CANTIDAD", width=100, anchor="center")
        self.tabla.column("IMPORTE", width=120, anchor="e")
        self.tabla.pack(fill="both", expand=True, padx=20, pady=8)

        pie = tk.Frame(cuerpo, bg="#F4F4F4")
        pie.pack(fill="x", padx=25, pady=15)
        tk.Label(pie, text="TOTAL A PAGAR", bg="#F4F4F4",
                 font=("Arial", 13, "bold")).pack(side="left")
        self.total_label = tk.Label(pie, text="$0.00", bg="#F4F4F4",
                                    fg="#3A8D96", font=("Arial", 17, "bold"))
        self.total_label.pack(side="right")

        pago = tk.Frame(cuerpo, bg="#F4F4F4")
        pago.pack(fill="x", padx=25, pady=8)
        tk.Label(pago, text="Método de pago:", bg="#F4F4F4",
                 font=("Arial", 10, "bold")).pack(anchor="w")
        self.metodo = tk.StringVar(value="Efectivo")
        opciones = tk.Frame(pago, bg="#F4F4F4")
        opciones.pack(anchor="w", pady=5)
        tk.Radiobutton(opciones, text="Efectivo", variable=self.metodo,
                       value="Efectivo", bg="#F4F4F4").pack(side="left", padx=(0, 15))
        tk.Radiobutton(opciones, text="Tarjeta de crédito", variable=self.metodo,
                       value="Tarjeta (Crédito)", bg="#F4F4F4").pack(side="left", padx=(0, 15))
        tk.Radiobutton(opciones, text="Tarjeta de débito", variable=self.metodo,
                       value="Tarjeta (Débito)", bg="#F4F4F4").pack(side="left")

        botones = tk.Frame(cuerpo, bg="#F4F4F4")
        botones.pack(fill="x", padx=20, pady=(12, 20))
        tk.Button(botones, text="ACTUALIZAR RESUMEN", bg="#D9EDEF",
                  font=("Arial", 9, "bold"), relief="flat",
                  command=self.refrescar).pack(side="left", padx=5)
        tk.Button(botones, text="CONFIRMAR Y COBRAR", bg="#F4D03F",
                  font=("Arial", 10, "bold"), relief="flat",
                  command=self.confirmar_cobro).pack(side="right", padx=5)
        self.refrescar()

    def refrescar(self):
        _, carrito, total = self.controlador.obtener_datos_ventas()
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for item in carrito:
            self.tabla.insert("", "end", values=(item["producto"], item["cantidad"], f"${item['subtotal']:.2f}"))
        self.total_label.config(text=f"${total:.2f}")

    def confirmar_cobro(self):
        _, carrito, _ = self.controlador.obtener_datos_ventas()
        if not carrito:
            messagebox.showwarning("Ticket vacío", "Primero agrega productos desde Punto de Venta.", parent=self)
            return
        metodo = self.metodo.get()
        self.controlador.procesar_cobro_avanzado(metodo, None)
        self.refrescar()
    