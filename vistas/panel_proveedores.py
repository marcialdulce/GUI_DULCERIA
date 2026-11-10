import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos

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
        tk.Button(frame_btns, text=" VER PEDIDOS ACTIVOS", bg="#2980B9", fg="white", command=self.ver_pedidos).pack(side="left", padx=10)
        tk.Button(frame_btns, text="- ELIMINAR PROVEEDOR", bg="#E74C3C", fg="white", command=self.eliminar_proveedor_seleccionado).pack(side="left")

        cols = ("ID", "NOMBRE", "TELÉFONO", "CORREO")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", height=15)
        for c in cols: 
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="center", width=150)
        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)
        self.refrescar()

    def refrescar(self):
        for row in self.tabla.get_children(): 
            self.tabla.delete(row)
        for p in self.controlador.obtener_proveedores():
            self.tabla.insert("", "end", values=(p["id"], p["nombre"], p.get("telefono", ""), p.get("correo", "")))

    def eliminar_proveedor_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona un proveedor de la tabla para eliminarlo.")
            return

        item = self.tabla.item(seleccion[0])
        id_prov = item["values"][0]
        nombre_prov = item["values"][1]

        respuesta = messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar al proveedor '{nombre_prov}'?\n\nNota: No podrás eliminarlo si tiene pedidos registrados en el historial.")
        
        if respuesta:
            if self.controlador.eliminar_proveedor(id_prov):
                messagebox.showinfo( "Proveedor eliminado correctamente.")
                self.refrescar()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el proveedor. Es posible que tenga pedidos activos o históricos vinculados a él.")

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
                messagebox.showwarning("Atención", "Ingresa una cantidad.")
                return
                
            cant = int(texto_cant)
            if cant <= 0:
                messagebox.showwarning("Atención", "La cantidad debe ser mayor a cero.")
                return
            
            for p in self.productos_prov:
                if p["nombre"] == prod_nombre:
                    costo_val = float(self.e_costo.get().replace('Costo $', '').strip() or p["costo"])
                    self.carrito_pedido.append({"id": p["id"], "cant": cant, "costo": costo_val})
                    self.tabla_modal.insert("", "end", values=(prod_nombre, cant, f"${costo_val:.2f}"))
                    self.e_cant.delete(0, 'end')
                    break
                    
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número entero.")

    def _guardar_pedido(self):
        prov = next((p for p in self.controlador.obtener_proveedores() if p["nombre"] == self.cmb_prov.get()), None)
        if prov and self.carrito_pedido:
            if self.controlador.crear_pedido_manual(prov["id"], self.carrito_pedido):
                messagebox.showinfo("Éxito", "Pedido enviado al proveedor.")
                if self.modal: self.modal.destroy()
            else: 
                messagebox.showerror("Error", "No se pudo guardar.")

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
        self.tabla_modal.pack(fill="x", padx=20, pady=10)

        self.cmb_prov.bind("<<ComboboxSelected>>", self._cargar_prods)

        tk.Button(self.modal, text="+ AGREGAR AL PEDIDO", bg="#F1C40F", command=self._agregar_al_carrito).pack(pady=5)
        tk.Button(self.modal, text="GUARDAR PEDIDO", bg="#27AE60", fg="white", command=self._guardar_pedido).pack(pady=15)

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