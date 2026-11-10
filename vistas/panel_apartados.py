import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

class PanelApartados(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg="#F9F4F0")
        self.controlador = controlador
        self.carrito = []

        tk.Label(self, text="CONTROL DE APARTADOS", bg="#2D929A", fg="white", font=("Arial", 11, "bold")).pack(fill="x", padx=15, pady=5)
        
        frame_btns = tk.Frame(self, bg="#F9F4F0")
        frame_btns.pack(fill="x", padx=15, pady=10)
        tk.Button(frame_btns, text="+ NUEVO APARTADO", bg="#27AE60", fg="white", font=("Arial", 9, "bold"), command=self.abrir_nuevo_apartado).pack(side="left")
        tk.Button(frame_btns, text=" LIQUIDAR SELECCIONADO", bg="#2980B9", fg="white", font=("Arial", 9, "bold"), command=self.liquidar_apartado).pack(side="left", padx=10)
        tk.Button(frame_btns, text=" CANCELAR", bg="#C0392B", fg="white", font=("Arial", 9, "bold"), command=self.cancelar_apartado).pack(side="right")

        columnas = ("SEL", "ID", "CLIENTE", "PRODUCTO", "FECHA", "TOTAL", "PAGADO", "ESTADO")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings")
        
        self.tabla.heading("SEL", text="[ ]")
        self.tabla.column("SEL", width=40, anchor="center")
        
        anchos = {"ID": 50, "CLIENTE": 180, "PRODUCTO": 200, "FECHA": 100, "TOTAL": 90, "PAGADO": 90, "ESTADO": 100}
        for c in columnas[1:]:
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="center", width=anchos[c])
            
        self.tabla.pack(fill="both", expand=True, padx=15, pady=5)
        self.tabla.bind("<ButtonRelease-1>", self.toggle_sel)
        
        self.cargar_tabla()

    def toggle_sel(self, event):
        item = self.tabla.identify_row(event.y)
        if item:
            vals = list(self.tabla.item(item, "values"))
            vals[0] = "☑" if vals[0] == "☐" else "☐"
            self.tabla.item(item, values=vals)

    def obtener_seleccionados(self):
        return [self.tabla.item(i)["values"] for i in self.tabla.get_children() if self.tabla.item(i)["values"][0] == "☑"]

    def cargar_tabla(self):
        for row in self.tabla.get_children(): 
            self.tabla.delete(row)
        for item in self.controlador.obtener_lista_apartados():
            self.tabla.insert("", "end", values=(
                "☐", item["id_apartado"], item["nombre"], item["producto"], item["fecha"], 
                f"${float(item['subtotal'])+float(item['impuesto']):.2f}", 
                f"${float(item['pagado']):.2f}", item["estado"].capitalize()
            ))

    def liquidar_apartado(self):
        sel = self.obtener_seleccionados()
        if not sel: 
            return messagebox.showwarning("Aviso", "Marca la casilla de un apartado.")
        
        item = sel[0]
        if item[7].lower() == "liquidado": 
            return messagebox.showinfo("Info", "Este apartado ya está liquidado.")
        
        total = float(str(item[5]).replace('$',''))
        pagado = float(str(item[6]).replace('$',''))
        saldo = total - pagado

        pago = simpledialog.askfloat("Liquidar", f"Saldo pendiente: ${saldo:.2f}\n¿Con cuánto paga el cliente?")
        if pago and pago >= saldo:
            if self.controlador.liquidar_apartado(item[1], [{"monto": pago, "id_metodo_pago": 1, "referencia": None}]):
                messagebox.showinfo("Éxito", f"Liquidado. Cambio: ${pago - saldo:.2f}")
                self.cargar_tabla()

    def cancelar_apartado(self):
        sel = self.obtener_seleccionados()
        if not sel: 
            return messagebox.showwarning("Aviso", "Marca la casilla de un apartado.")
            
        if messagebox.askyesno("Cancelar", "El anticipo NO es reembolsable. ¿Continuar?"):
            self.controlador.cancelar_apartado(sel[0][1])
            self.cargar_tabla()

    # --- REFACTORIZACIÓN PARA REDUCIR COMPLEJIDAD ---

    def abrir_nuevo_apartado(self):
        modal = tk.Toplevel(self)
        modal.geometry("450x550")
        modal.title("Nuevo Apartado (Carrito)")
        modal.grab_set()
        self.carrito.clear()

        tk.Label(modal, text="Nombre:").pack()
        e_nombre = tk.Entry(modal)
        e_nombre.pack()
        
        tk.Label(modal, text="Teléfono:").pack()
        e_tel = tk.Entry(modal)
        e_tel.pack()
        
        tk.Label(modal, text="Fecha (AAAA-MM-DD):").pack()
        e_fecha = tk.Entry(modal)
        e_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        e_fecha.pack()

        frame_add = tk.Frame(modal)
        frame_add.pack(pady=10)
        
        cmb_prods = ttk.Combobox(frame_add, values=self.controlador.obtener_nombres_productos(), state="readonly", width=25)
        cmb_prods.pack(side="left", padx=5)
        
        e_cant = tk.Entry(frame_add, width=5)
        e_cant.pack(side="left")

        tabla_c = ttk.Treeview(modal, columns=("PROD", "CANT"), show="headings", height=5)
        tabla_c.heading("PROD", text="Producto")
        tabla_c.heading("CANT", text="Cant")
        tabla_c.column("PROD", width=250)
        tabla_c.column("CANT", width=50, anchor="center")
        tabla_c.pack(fill="x", padx=20, pady=10)

        # Se asigna la función auxiliar usando lambda
        btn_agregar = tk.Button(frame_add, text="+")
        btn_agregar.config(command=lambda: self._agregar_al_carrito(cmb_prods, e_cant, tabla_c))
        btn_agregar.pack(side="left")

        tk.Label(modal, text="Método Pago Anticipo (50%):").pack()
        cmb_metodo = ttk.Combobox(modal, values=["Efectivo", "Tarjeta de débito", "Tarjeta de crédito"], state="readonly")
        cmb_metodo.current(0)
        cmb_metodo.pack()

        # Se asigna la función auxiliar usando lambda
        btn_guardar = tk.Button(modal, text="REGISTRAR APARTADO", bg="#27AE60", fg="white")
        btn_guardar.config(command=lambda: self._guardar_apartado(modal, e_nombre, e_tel, e_fecha, cmb_metodo))
        btn_guardar.pack(pady=15)

    def _agregar_al_carrito(self, cmb_prods, e_cant, tabla_c):
        prod = next((p for p in self.controlador.modelo.inventario if p["nombre"] == cmb_prods.get()), None)
        if prod and e_cant.get().isdigit():
            cant = int(e_cant.get())
            if cant > 0:
                self.carrito.append({
                    "id_producto": prod["id_producto"], 
                    "nombre": prod["nombre"], 
                    "precio_unitario": prod["precio"], 
                    "cantidad": cant
                })
                tabla_c.insert("", "end", values=(prod["nombre"], cant))

    def _guardar_apartado(self, modal, e_nombre, e_tel, e_fecha, cmb_metodo):
        if not e_nombre.get() or not self.carrito:
            return messagebox.showwarning("Aviso", "Faltan datos o productos.", parent=modal)
            
        total = sum(a["precio_unitario"] * a["cantidad"] for a in self.carrito)
        anticipo = round(total * 0.50, 2)

        # CORRECCIÓN AQUÍ: Se reemplazó el condicional anidado por un if/elif/else
        metodo_seleccionado = cmb_metodo.get()
        if metodo_seleccionado == "Efectivo":
            id_metodo = 1
        elif metodo_seleccionado == "Tarjeta de débito":
            id_metodo = 2
        else:
            id_metodo = 3

        ok, msg = self.controlador.registrar_apartado(
            e_nombre.get(), e_tel.get(), e_fecha.get(), self.carrito, 
            [{"monto": anticipo, "id_metodo_pago": id_metodo}]
        )
        
        if ok:
            messagebox.showinfo("Éxito", f"Guardado. Cobrar anticipo: ${anticipo:.2f}", parent=modal)
            modal.destroy()
            self.cargar_tabla()
        else: 
            messagebox.showerror("Error", msg, parent=modal)