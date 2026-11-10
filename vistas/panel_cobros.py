import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos

class PanelCobros(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.pagos_registrados = [] 
        
        tk.Label(self, text="COBROS Y PAGOS MIXTOS", bg=estilos.FONDO,
                 fg="#4A2E35", font=("Arial", 20, "bold")).pack(pady=(20, 12))

        cuerpo = tk.Frame(self, bg="#F4F4F4", bd=1, relief="solid")
        cuerpo.pack(fill="both", expand=True, padx=35, pady=15)
        
        tk.Label(cuerpo, text="RESUMEN DE COMPRA", bg="#F4F4F4", font=("Arial", 12, "bold")).pack(pady=10)
        self.total_label = tk.Label(cuerpo, text="$0.00", bg="#F4F4F4", fg="#3A8D96", font=("Arial", 18, "bold"))
        self.total_label.pack()

        frame_pago = tk.Frame(cuerpo, bg="#F4F4F4")
        frame_pago.pack(fill="x", padx=25, pady=15)
        
        tk.Label(frame_pago, text="Método:", bg="#F4F4F4").pack(side="left")
        self.combo_metodo = ttk.Combobox(frame_pago, values=["Efectivo", "Tarjeta de débito", "Tarjeta de crédito"], state="readonly", width=18)
        self.combo_metodo.current(0)
        self.combo_metodo.pack(side="left", padx=5)

        tk.Label(frame_pago, text="Monto: $", bg="#F4F4F4").pack(side="left", padx=(10,0))
        self.entry_monto = tk.Entry(frame_pago, width=10)
        self.entry_monto.pack(side="left", padx=5)

        tk.Button(frame_pago, text="+ Agregar Pago", bg="#3A8D96", fg="white", command=self.agregar_pago).pack(side="left", padx=10)

        self.tabla_pagos = ttk.Treeview(cuerpo, columns=("Método", "Monto"), show="headings", height=5)
        self.tabla_pagos.heading("Método", text="MÉTODO DE PAGO")
        self.tabla_pagos.heading("Monto", text="MONTO")
        self.tabla_pagos.column("Método", anchor="center")
        self.tabla_pagos.column("Monto", anchor="center")
        self.tabla_pagos.pack(fill="x", padx=25, pady=5)

        botones = tk.Frame(cuerpo, bg="#F4F4F4")
        botones.pack(fill="x", padx=20, pady=20)
        
        tk.Button(botones, text="LIMPIAR PAGOS", bg="#E6B0AA", font=("Arial", 9, "bold"), command=self.limpiar_pagos).pack(side="left", padx=5)
        tk.Button(botones, text="CONFIRMAR Y COBRAR", bg="#F4D03F", font=("Arial", 10, "bold"), command=self.confirmar_cobro).pack(side="right", padx=5)

        self.refrescar()

    def refrescar(self):
        _, _, total = self.controlador.obtener_datos_ventas()
        self.total_label.config(text=f"${total:.2f}")

    def agregar_pago(self):
        try:
            monto = float(self.entry_monto.get())
            if monto <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ingresa un monto válido mayor a 0.")
            return

        metodo_texto = self.combo_metodo.get()
        id_metodo = 1 if metodo_texto == "Efectivo" else (2 if metodo_texto == "Tarjeta de débito" else 3)
        
        self.pagos_registrados.append({"id_metodo_pago": id_metodo, "monto": monto})
        self.tabla_pagos.insert("", "end", values=(metodo_texto, f"${monto:.2f}"))
        self.entry_monto.delete(0, "end")

    def limpiar_pagos(self):
        self.pagos_registrados.clear()
        for fila in self.tabla_pagos.get_children():
            self.tabla_pagos.delete(fila)

    def confirmar_cobro(self):
        _, carrito, _ = self.controlador.obtener_datos_ventas()
        if not carrito:
            messagebox.showwarning("Ticket vacío", "No hay productos en el carrito.")
            return
            
        if not self.pagos_registrados:
            messagebox.showwarning("Sin pagos", "Debes agregar al menos un método de pago.")
            return

        exito = self.controlador.procesar_cobro_avanzado(self.pagos_registrados, datos_factura=None)
        if exito:
            self.limpiar_pagos()
            self.refrescar()