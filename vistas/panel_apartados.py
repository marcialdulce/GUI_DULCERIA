import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class PanelApartados(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg="#F9F4F0")
        self.controlador = controlador
        self.carrito = [] # Carrito local

        tk.Label(self, text="CONTROL DE APARTADOS", bg="#2D929A", fg="white", font=("Arial", 11, "bold")).pack(fill="x", padx=15, pady=5)
        
        frame_btns = tk.Frame(self, bg="#F9F4F0")
        frame_btns.pack(fill="x", padx=15, pady=5)
        tk.Button(frame_btns, text="+ NUEVO APARTADO", bg="#27AE60", fg="white", command=self.abrir_nuevo_apartado).pack(side="left")
        tk.Button(frame_btns, text=" LIQUIDAR SELECCIONADO", bg="#2980B9", fg="white", command=self.liquidar_apartado).pack(side="left", padx=10)
        tk.Button(frame_btns, text=" CANCELAR", bg="#C0392B", fg="white", command=self.cancelar_apartado).pack(side="right")

        self.tabla = ttk.Treeview(self, columns=("SEL", "ID", "CLIENTE", "PRODUCTO", "FECHA", "TOTAL", "PAGADO", "ESTADO"), show="headings")
        self.tabla.heading("SEL", text="[ ]"); self.tabla.column("SEL", width=40, anchor="center")
        self.tabla.heading("ID", text="ID")
        self.tabla.heading("CLIENTE", text="CLIENTE")
        self.tabla.heading("PRODUCTO", text="PRODUCTO")
        self.tabla.heading("FECHA", text="ENTREGA")
        self.tabla.heading("TOTAL", text="TOTAL")
        self.tabla.heading("PAGADO", text="PAGADO")
        self.tabla.heading("ESTADO", text="ESTADO")
        for c in ("ID","CLIENTE","PRODUCTO","FECHA","TOTAL","PAGADO","ESTADO"): self.tabla.column(c, anchor="center", width=100)
        self.tabla.pack(fill="both", expand=True, padx=15, pady=5)
        self.tabla.bind("<ButtonRelease-1>", self.toggle_sel)
        
        self.cargar_tabla()

    def toggle_sel(self, event):
        item = self.tabla.identify_row(event.y)
        if item:
            vals = list(self.tabla.item(item, "values"))
            vals[0] = "☑" if vals[0] == "☐" else "☐"
            self.tabla.item(item, values=vals)

    def cargar_tabla(self):
        for row in self.tabla.get_children(): self.tabla.delete(row)
        for item in self.controlador.obtener_lista_apartados():
            self.tabla.insert("", "end", values=(
                "☐", item["id_apartado"], item["nombre"], item["producto"], item["fecha"], 
                f"${float(item['subtotal'])+float(item['impuesto']):.2f}", 
                f"${float(item['pagado']):.2f}", item["estado"]
            ))

    def liquidar_apartado(self):
        sel = [self.tabla.item(i)["values"] for i in self.tabla.get_children() if self.tabla.item(i)["values"][0] == "☑"]
        if not sel: return messagebox.showwarning("Aviso", "Marca un apartado.")
        
        item = sel[0]
        if item[7] == "liquidado": return messagebox.showinfo("Info", "Ya está liquidado.")
        
        total = float(item[5].replace('$',''))
        pagado = float(item[6].replace('$',''))
        saldo = total - pagado

        # Pago simple para saldo (Podría ser mixto, pero simplificamos a 1 método)
        pago = tk.simpledialog.askfloat("Liquidar", f"Saldo pendiente: ${saldo:.2f}\n¿Con cuánto paga el cliente?")
        if pago and pago >= saldo:
            if self.controlador.liquidar_apartado(item[1], [{"monto": pago, "id_metodo_pago": 1}]):
                messagebox.showinfo("Éxito", f"Liquidado. Cambio: ${pago - saldo:.2f}")
                self.cargar_tabla()

    def cancelar_apartado(self):
        sel = [self.tabla.item(i)["values"] for i in self.tabla.get_children() if self.tabla.item(i)["values"][0] == "☑"]
        if not sel: return
        if messagebox.askyesno("Cancelar", "El anticipo NO es reembolsable. ¿Continuar?"):
            self.controlador.cancelar_apartado(sel[0][1])
            self.cargar_tabla()

    def abrir_nuevo_apartado(self):
        modal = tk.Toplevel(self)
        modal.geometry("450x550")
        modal.title("Nuevo Apartado (Carrito)")
        modal.grab_set()
        self.carrito.clear()

        tk.Label(modal, text="Nombre:").pack(); e_nombre = tk.Entry(modal); e_nombre.pack()
        tk.Label(modal, text="Teléfono:").pack(); e_tel = tk.Entry(modal); e_tel.pack()
        tk.Label(modal, text="Fecha (AAAA-MM-DD):").pack(); e_fecha = tk.Entry(modal); e_fecha.insert(0, datetime.now().strftime("%Y-%m-%d")); e_fecha.pack()

        frame_add = tk.Frame(modal); frame_add.pack(pady=10)
        cmb_prods = ttk.Combobox(frame_add, values=self.controlador.obtener_nombres_productos(), state="readonly", width=20)
        cmb_prods.pack(side="left", padx=5)
        e_cant = tk.Entry(frame_add, width=5); e_cant.pack(side="left")

        tabla_c = ttk.Treeview(modal, columns=("PROD", "CANT"), show="headings", height=5)
        tabla_c.heading("PROD", text="Producto"); tabla_c.heading("CANT", text="Cant")
        tabla_c.pack(fill="x", padx=20, pady=10)

        def agregar():
            prod = next((p for p in self.controlador.modelo.inventario if p["nombre"] == cmb_prods.get()), None)
            if prod:
                cant = int(e_cant.get())
                self.carrito.append({"id_producto": prod["id_producto"], "nombre": prod["nombre"], "precio_unitario": prod["precio"], "cantidad": cant})
                tabla_c.insert("", "end", values=(prod["nombre"], cant))
        
        tk.Button(frame_add, text="+", command=agregar).pack(side="left")

        tk.Label(modal, text="Método Pago Anticipo (50%):").pack()
        cmb_metodo = ttk.Combobox(modal, values=["Efectivo", "Tarjeta de débito", "Tarjeta de crédito"], state="readonly")
        cmb_metodo.current(0); cmb_metodo.pack()

        def guardar():
            total = sum(a["precio_unitario"] * a["cantidad"] for a in self.carrito)
            anticipo = round(total * 0.50, 2)
            id_metodo = 1 if cmb_metodo.get() == "Efectivo" else (2 if cmb_metodo.get() == "Tarjeta de débito" else 3)
            
            ok, msg = self.controlador.registrar_apartado(
                e_nombre.get(), e_tel.get(), e_fecha.get(), self.carrito, 
                [{"monto": anticipo, "id_metodo_pago": id_metodo}]
            )
            if ok:
                messagebox.showinfo("Éxito", f"Guardado. Cobrar anticipo: ${anticipo:.2f}")
                modal.destroy(); self.cargar_tabla()
            else: messagebox.showerror("Error", msg)

        tk.Button(modal, text="REGISTRAR APARTADO", bg="#27AE60", fg="white", command=guardar).pack(pady=15)
        