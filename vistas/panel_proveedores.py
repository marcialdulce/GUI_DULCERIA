import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos

# Constantes para evitar duplicación (SonarQube)
MSG_EXITO = "Éxito"
MSG_ERROR = "Error"
MSG_AVISO = "Aviso"
MSG_ATENCION = "Atención"

class PanelProveedores(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.carrito_pedido = []
        self.productos_prov = []
        self.modal = None

        tk.Label(self, text="GESTIÓN DE PROVEEDORES Y PEDIDOS", bg="#3A8D96", fg="white", font=("Arial", 11, "bold")).pack(fill="x", pady=5)
        
        frame_btns = tk.Frame(self, bg=estilos.FONDO)
        frame_btns.pack(pady=10)
        tk.Button(frame_btns, text="+ NUEVO PEDIDO MANUAL", bg="#27AE60", fg="white", command=self.nuevo_pedido).pack(side="left", padx=10)
        tk.Button(frame_btns, text="VER PEDIDOS ACTIVOS", bg="#2980B9", fg="white", command=self.ver_pedidos).pack(side="left", padx=10)
        tk.Button(frame_btns, text="- ELIMINAR SELECCIONADO", bg="#E74C3C", fg="white", command=self.eliminar_proveedor_seleccionado).pack(side="left")

        cols = ("SEL", "ID", "NOMBRE", "TELÉFONO", "CORREO")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", height=15)
        
        self.tabla.heading("SEL", text="[ ]")
        self.tabla.column("SEL", width=40, anchor="center")
        
        anchos = {"ID": 60, "NOMBRE": 300, "TELÉFONO": 150, "CORREO": 250}
        for c in cols[1:]: 
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="center", width=anchos[c])
            
        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)
        self.tabla.bind("<ButtonRelease-1>", self.toggle_sel)
        self.refrescar()

    def toggle_sel(self, event):
        item = self.tabla.identify_row(event.y)
        if item:
            vals = list(self.tabla.item(item, "values"))
            vals[0] = "☑" if vals[0] == "☐" else "☐"
            self.tabla.item(item, values=vals)

    def obtener_seleccionados(self):
        return [self.tabla.item(i)["values"] for i in self.tabla.get_children() if self.tabla.item(i)["values"][0] == "☑"]

    def refrescar(self):
        for row in self.tabla.get_children(): 
            self.tabla.delete(row)
        for p in self.controlador.obtener_proveedores():
            self.tabla.insert("", "end", values=("☐", p["id"], p["nombre"], p.get("telefono", ""), p.get("correo", "")))

    def eliminar_proveedor_seleccionado(self):
        sel = self.obtener_seleccionados()
        if not sel:
            messagebox.showwarning(MSG_AVISO, "Marca la casilla del proveedor a eliminar.")
            return

        id_prov, nombre_prov = sel[0][1], sel[0][2]

        if messagebox.askyesno("Confirmar", f"¿Eliminar a '{nombre_prov}'?\n(No se puede si tiene pedidos registrados)"):
            if self.controlador.eliminar_proveedor(id_prov):
                messagebox.showinfo(MSG_EXITO, "Proveedor eliminado.")
                self.refrescar()
            else:
                messagebox.showerror(MSG_ERROR, "No se pudo eliminar. Tiene pedidos vinculados.")

    def _cargar_prods(self, event):
        prov = next((p for p in self.controlador.obtener_proveedores() if p["nombre"] == self.cmb_prov.get()), None)
        if prov:
            self.productos_prov = self.controlador.obtener_productos_proveedor(prov["id"])
            self.cmb_prods["values"] = [p["nombre"] for p in self.productos_prov]

    def _agregar_al_carrito(self):
        try:
            prod_nombre = self.cmb_prods.get()
            texto_cant = self.e_cant.get().strip()
            if not texto_cant: 
                return messagebox.showwarning(MSG_ATENCION, "Ingresa una cantidad.")
            
            cant = int(texto_cant)
            if cant <= 0: 
                return messagebox.showwarning(MSG_ATENCION, "La cantidad debe ser mayor a cero.")
            
            for p in self.productos_prov:
                if p["nombre"] == prod_nombre:
                    costo_val = float(self.e_costo.get().replace('Costo $', '').strip() or p.get("costo", p.get("precio_venta", 0)))
                    self.carrito_pedido.append({"id_producto": p["id"], "cantidad": cant, "costo_unitario": costo_val})
                    self.tabla_modal.insert("", "end", values=(prod_nombre, cant, f"${costo_val:.2f}"))
                    self.e_cant.delete(0, 'end')
                    break
        except ValueError:
            messagebox.showerror(MSG_ERROR, "La cantidad debe ser un número entero.")

    def _guardar_pedido(self):
        prov = next((p for p in self.controlador.obtener_proveedores() if p["nombre"] == self.cmb_prov.get()), None)
        if prov and self.carrito_pedido:
            if self.controlador.crear_pedido_manual(prov["id"], self.carrito_pedido):
                messagebox.showinfo(MSG_EXITO, "Pedido enviado al proveedor.")
                if self.modal: self.modal.destroy()
            else: 
                messagebox.showerror(MSG_ERROR, "No se pudo guardar.")

    def nuevo_pedido(self):
        self.modal = tk.Toplevel(self)
        self.modal.geometry("500x600")
        self.modal.title("Crear Pedido a Proveedor")
        self.modal.grab_set()
        self.carrito_pedido.clear()

        tk.Label(self.modal, text="Proveedor:").pack()
        self.cmb_prov = ttk.Combobox(self.modal, values=[p["nombre"] for p in self.controlador.obtener_proveedores()], state="readonly")
        self.cmb_prov.pack()

        frame_add = tk.Frame(self.modal)
        frame_add.pack(pady=10)
        self.cmb_prods = ttk.Combobox(frame_add, state="readonly", width=25)
        self.cmb_prods.pack(side="left")
        self.e_cant = tk.Entry(frame_add, width=5)
        self.e_cant.pack(side="left")
        self.e_costo = tk.Entry(frame_add, width=8)
        self.e_costo.pack(side="left")
        self.e_costo.insert(0, "Costo $")

        self.tabla_modal = ttk.Treeview(self.modal, columns=("PROD", "CANT", "COSTO"), show="headings", height=8)
        for c in ("PROD", "CANT", "COSTO"): 
            self.tabla_modal.heading(c, text=c)
        self.tabla_modal.column("PROD", width=250)
        self.tabla_modal.column("CANT", width=50)
        self.tabla_modal.column("COSTO", width=80)
        self.tabla_modal.pack(fill="x", padx=20, pady=10)

        self.cmb_prov.bind("<<ComboboxSelected>>", self._cargar_prods)

        tk.Button(self.modal, text="+ AGREGAR AL PEDIDO", bg="#F1C40F", command=self._agregar_al_carrito).pack(pady=5)
        tk.Button(self.modal, text="GUARDAR PEDIDO", bg="#27AE60", fg="white", command=self._guardar_pedido).pack(pady=15)

    def _recibir_mercancia(self, tabla, modal):
        sel = tabla.selection()
        if sel:
            id_p = tabla.item(sel[0])["values"][0]
            if self.controlador.recibir_pedido(id_p):
                messagebox.showinfo(MSG_EXITO, "Mercancía recibida y stock actualizado.")
                modal.destroy()

    def ver_pedidos(self):
        modal = tk.Toplevel(self)
        modal.geometry("600x400")
        modal.title("Pedidos Activos")

        tabla = ttk.Treeview(modal, columns=("ID", "PROD", "CANT", "TOTAL"), show="headings")
        for c in ("ID", "PROD", "CANT", "TOTAL"): 
            tabla.heading(c, text=c)
        tabla.column("ID", width=80)
        tabla.column("PROD", width=300)
        tabla.column("CANT", width=80)
        tabla.column("TOTAL", width=100)
        tabla.pack(fill="both", expand=True, padx=10, pady=10)

        for p in self.controlador.obtener_pedidos_activos():
            tabla.insert("", "end", values=(p["id_pedido"], p["producto"], p["cantidad"], f"${float(p['subtotal']):.2f}"))

        # Se extrajo la función anidada a un método propio
        tk.Button(modal, text="RECIBIR MERCANCÍA", bg="#27AE60", fg="white", 
                  command=lambda: self._recibir_mercancia(tabla, modal)).pack(pady=10)