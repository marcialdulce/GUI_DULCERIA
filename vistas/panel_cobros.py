import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos

class PanelCobros(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.pagos = []
        self.datos_factura = None

        tk.Label(self, text="COBRO Y FACTURACIÓN", bg=estilos.FONDO, font=("Arial", 18, "bold")).pack(pady=10)
        self.lbl_total = tk.Label(self, text="$0.00", bg=estilos.FONDO, fg="#27AE60", font=("Arial", 24, "bold"))
        self.lbl_total.pack()

        frame_pago = tk.Frame(self, bg=estilos.FONDO); frame_pago.pack(pady=10)
        self.cmb_metodo = ttk.Combobox(frame_pago, values=["Efectivo", "Tarjeta de débito", "Tarjeta de crédito"], state="readonly")
        self.cmb_metodo.current(0); self.cmb_metodo.pack(side="left")
        
        self.e_monto = tk.Entry(frame_pago, width=10); self.e_monto.pack(side="left", padx=5)
        self.e_ref = tk.Entry(frame_pago, width=15); self.e_ref.insert(0, "Ref. Tarjeta"); self.e_ref.pack(side="left", padx=5)
        
        tk.Button(frame_pago, text="+ Pago", command=self.agregar_pago).pack(side="left")

        self.tabla_pagos = ttk.Treeview(self, columns=("M", "R", "MONTO"), show="headings", height=4)
        for c in ("M", "R", "MONTO"): self.tabla_pagos.heading(c, text=c)
        self.tabla_pagos.pack(fill="x", padx=50)

        tk.Button(self, text="🧾 AGREGAR FACTURA", bg="#8E44AD", fg="white", command=self.abrir_factura).pack(pady=10)
        tk.Button(self, text="CONFIRMAR COBRO", bg="#F4D03F", font=("Arial", 12, "bold"), command=self.cobrar).pack(pady=10)

        self.refrescar()

    def refrescar(self):
        _, _, total = self.controlador.obtener_datos_ventas()
        self.lbl_total.config(text=f"${total:.2f}")

    def agregar_pago(self):
        try: monto = float(self.e_monto.get())
        except: return
        metodo = self.cmb_metodo.get()
        id_m = 1 if metodo == "Efectivo" else (2 if metodo == "Tarjeta de débito" else 3)
        ref = self.e_ref.get() if metodo != "Efectivo" and self.e_ref.get() != "Ref. Tarjeta" else None
        
        self.pagos.append({"id_metodo_pago": id_m, "monto": monto, "referencia": ref})
        self.tabla_pagos.insert("", "end", values=(metodo, ref or "-", f"${monto:.2f}"))
        self.e_monto.delete(0, "end")

    def abrir_factura(self):
        modal = tk.Toplevel(self)
        modal.geometry("350x400")
        
        campos = [("RFC:", "rfc"), ("Razón Social:", "razon_social"), ("Régimen Fiscal:", "regimen"), ("Código Postal:", "cp"), ("Correo:", "correo")]
        entries = {}
        for txt, key in campos:
            tk.Label(modal, text=txt).pack()
            e = tk.Entry(modal); e.pack()
            entries[key] = e

        def guardar():
            self.datos_factura = {"requiere": True}
            for k, e in entries.items(): self.datos_factura[k] = e.get()
            messagebox.showinfo("Éxito", "Datos fiscales listos.")
            modal.destroy()

        tk.Button(modal, text="GUARDAR DATOS", command=guardar).pack(pady=10)

    def cobrar(self):
        exito, msg = self.controlador.procesar_cobro_avanzado(self.pagos, self.datos_factura)
        if exito:
            messagebox.showinfo("Éxito", msg)
            self.pagos.clear(); self.tabla_pagos.delete(*self.tabla_pagos.get_children())
            self.datos_factura = None
            self.refrescar()
        else:
            messagebox.showerror("Error", msg)