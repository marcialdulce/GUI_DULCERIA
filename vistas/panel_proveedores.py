import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos

class PanelProveedores(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.carrito_pedido = []

        tk.Label(self, text="GESTIÓN DE PROVEEDORES Y PEDIDOS", bg="#3A8D96", fg="white", font=("Arial", 11, "bold")).pack(fill="x", pady=5)
        
        frame_btns = tk.Frame(self, bg=estilos.FONDO); frame_btns.pack(pady=10)
        tk.Button(frame_btns, text="+ NUEVO PEDIDO MANUAL", bg="#27AE60", fg="white", command=self.nuevo_pedido).pack(side="left", padx=10)
        tk.Button(frame_btns, text=" VER PEDIDOS ACTIVOS", bg="#2980B9", fg="white", command=self.ver_pedidos).pack(side="left")

        cols = ("ID", "NOMBRE", "TELÉFONO", "CORREO")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", height=15)
        for c in cols: self.tabla.heading(c, text=c); self.tabla.column(c, anchor="center", width=150)
        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)
        self.refrescar()

    def refrescar(self):
        for row in self.tabla.get_children(): self.tabla.delete(row)
        # Aquí usamos p.get() por si algún proveedor no tiene teléfono o correo en la BD
        for p in self.controlador.obtener_proveedores():
            self.tabla.insert("", "end", values=(p["id"], p["nombre"], p.get("telefono", ""), p.get("correo", "")))

    def nuevo_pedido(self):
        modal = tk.Toplevel(self)
        modal.geometry("500x600")
        modal.title("Crear Pedido a Proveedor")
        modal.grab_set()
        self.carrito_pedido.clear()

        tk.Label(modal, text="Proveedor:").pack()
        cmb_prov = ttk.Combobox(modal, values=[p["nombre"] for p in self.controlador.obtener_proveedores()], state="readonly")
        cmb_prov.pack()

        frame_add = tk.Frame(modal); frame_add.pack(pady=10)
        cmb_prods = ttk.Combobox(frame_add, state="readonly", width=25); cmb_prods.pack(side="left")
        e_cant = tk.Entry(frame_add, width=5); e_cant.pack(side="left")
        e_costo = tk.Entry(frame_add, width=8); e_costo.pack(side="left")
        e_costo.insert(0, "Costo $")

        tabla = ttk.Treeview(modal, columns=("PROD", "CANT", "COSTO"), show="headings", height=8)
        for c in ("PROD", "CANT", "COSTO"): tabla.heading(c, text=c)
        tabla.pack(fill="x", padx=20, pady=10)

        def cargar_prods(event):
            prov = next((p for p in self.controlador.obtener_proveedores() if p["nombre"] == cmb_prov.get()), None)
            if prov:
                prods = self.controlador.obtener_productos_proveedor(prov["id"])
                cmb_prods["values"] = [p["nombre"] for p in prods]

        cmb_prov.bind("<<ComboboxSelected>>", cargar_prods)

        def agregar():
            prod_nombre = cmb_prods.get()
            prov = next((p for p in self.controlador.obtener_proveedores() if p["nombre"] == cmb_prov.get()), None)
            prods = self.controlador.obtener_productos_proveedor(prov["id"])
            prod = next((p for p in prods if p["nombre"] == prod_nombre), None)
            
            if prod:
                cant = int(e_cant.get())
                costo = float(e_costo.get())
                self.carrito_pedido.append({"id_producto": prod["id_producto"], "cantidad": cant, "costo_unitario": costo})
                tabla.insert("", "end", values=(prod_nombre, cant, f"${costo:.2f}"))

        tk.Button(frame_add, text="+", command=agregar).pack(side="left")

        def guardar():
            prov = next((p for p in self.controlador.obtener_proveedores() if p["nombre"] == cmb_prov.get()), None)
            if prov and self.carrito_pedido:
                if self.controlador.crear_pedido_manual(prov["id"], self.carrito_pedido):
                    messagebox.showinfo("Éxito", "Pedido enviado al proveedor.")
                    modal.destroy()
                else: messagebox.showerror("Error", "No se pudo guardar.")

        tk.Button(modal, text="GUARDAR PEDIDO", bg="#27AE60", fg="white", command=guardar).pack(pady=15)

    def ver_pedidos(self):
        modal = tk.Toplevel(self)
        modal.geometry("600x400")
        modal.title("Pedidos Activos")

        tabla = ttk.Treeview(modal, columns=("ID", "PROD", "CANT", "TOTAL"), show="headings")
        for c in ("ID", "PROD", "CANT", "TOTAL"): tabla.heading(c, text=c)
        tabla.pack(fill="both", expand=True, padx=10, pady=10)

        for p in self.controlador.obtener_pedidos_activos():
            tabla.insert("", "end", values=(p["id_pedido"], p["producto"], p["cantidad"], f"${float(p['subtotal']):.2f}"))

        def recibir():
            sel = tabla.selection()
            if sel:
                id_p = tabla.item(sel[0])["values"][0]
                if self.controlador.recibir_pedido(id_p):
                    messagebox.showinfo("Éxito", "Mercancía recibida y stock actualizado.")
                    modal.destroy()

        tk.Button(modal, text="RECIBIR MERCANCÍA", bg="#27AE60", fg="white", command=recibir).pack(pady=10)