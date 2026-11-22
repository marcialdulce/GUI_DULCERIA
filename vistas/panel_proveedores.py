import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos

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
        frame_btns.pack(fill="x", padx=20, pady=8)

        tk.Button(frame_btns, text="+ NUEVO PROVEEDOR", bg="#16A085", fg="white", font=("Arial", 9, "bold"), relief="flat", cursor="hand2", command=lambda: self.abrir_formulario_proveedor(None)).pack(side="left", padx=(0, 6))
        tk.Button(frame_btns, text="EDITAR PROVEEDOR", bg="#F39C12", fg="white", font=("Arial", 9, "bold"), relief="flat", cursor="hand2", command=self.editar_proveedor_seleccionado).pack(side="left", padx=6)
        tk.Button(frame_btns, text="+ NUEVO PEDIDO MANUAL", bg="#27AE60", fg="white", font=("Arial", 9, "bold"), relief="flat", cursor="hand2", command=self.nuevo_pedido).pack(side="left", padx=6)
        tk.Button(frame_btns, text="VER PEDIDOS ACTIVOS", bg="#2980B9", fg="white", font=("Arial", 9, "bold"), relief="flat", cursor="hand2", command=self.ver_pedidos).pack(side="left", padx=6)
        tk.Button(frame_btns, text="- ELIMINAR", bg="#E74C3C", fg="white", font=("Arial", 9, "bold"), relief="flat", cursor="hand2", command=self.eliminar_proveedor_seleccionado).pack(side="right")

        frame_buscar = tk.Frame(self, bg=estilos.FONDO)
        frame_buscar.pack(fill="x", padx=20, pady=(0, 6))
        tk.Label(frame_buscar, text="Buscar proveedor:", bg=estilos.FONDO, font=("Arial", 9, "bold")).pack(side="left")
        self.e_buscar = tk.Entry(frame_buscar, width=32)
        self.e_buscar.pack(side="left", padx=8)
        self.e_buscar.bind("<KeyRelease>", lambda e: self.refrescar())

        cols = ("SEL", "ID", "NOMBRE", "TELÉFONO", "CORREO")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", height=15)

        self.tabla.heading("SEL", text="[ ]")
        self.tabla.column("SEL", width=40, anchor="center")

        anchos = {"ID": 55, "NOMBRE": 300, "TELÉFONO": 150, "CORREO": 260}
        for c in cols[1:]:
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="w" if c in ("NOMBRE", "CORREO") else "center", width=anchos[c])

        self.tabla.pack(fill="both", expand=True, padx=20, pady=(0, 10))
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
        texto = self.e_buscar.get().strip().lower() if hasattr(self, "e_buscar") else ""
        for row in self.tabla.get_children():
            self.tabla.delete(row)

        for p in self.controlador.obtener_proveedores():
            nombre = str(p.get("nombre") or "")
            tel = str(p.get("telefono") or "")
            correo = str(p.get("correo") or "")
            if texto and texto not in nombre.lower() and texto not in tel.lower() and texto not in correo.lower():
                continue
            self.tabla.insert("", "end", values=("☐", p["id"], nombre, tel, correo))

    def editar_proveedor_seleccionado(self):
        sel = self.obtener_seleccionados()
        if not sel:
            messagebox.showwarning(MSG_AVISO, "Marca la casilla del proveedor que deseas editar.")
            return
        fila = sel[0]
        proveedor = {"id": fila[1], "nombre": fila[2], "telefono": fila[3], "correo": fila[4]}
        self.abrir_formulario_proveedor(proveedor)

    def abrir_formulario_proveedor(self, proveedor=None):
        es_nuevo = proveedor is None
        modal = tk.Toplevel(self)
        modal.title("Nuevo Proveedor" if es_nuevo else "Editar Proveedor")
        modal.geometry("380x270")
        modal.grab_set()

        p = proveedor or {}

        tk.Label(modal, text="Nombre de la empresa:", anchor="w").pack(fill="x", padx=20, pady=(14, 2))
        e_empresa = tk.Entry(modal)
        e_empresa.insert(0, str(p.get("nombre", "")))
        e_empresa.pack(fill="x", padx=20)

        tk.Label(modal, text="Teléfono:", anchor="w").pack(fill="x", padx=20, pady=(10, 2))
        e_tel = tk.Entry(modal)
        e_tel.insert(0, str(p.get("telefono", "")))
        e_tel.pack(fill="x", padx=20)

        tk.Label(modal, text="Correo electrónico:", anchor="w").pack(fill="x", padx=20, pady=(10, 2))
        e_correo = tk.Entry(modal)
        e_correo.insert(0, str(p.get("correo", "")))
        e_correo.pack(fill="x", padx=20)

        def guardar():
            if es_nuevo:
                ok, msg = self.controlador.crear_proveedor(e_empresa.get(), e_tel.get(), e_correo.get())
            else:
                ok, msg = self.controlador.actualizar_proveedor(p["id"], e_empresa.get(), e_tel.get(), e_correo.get())

            if ok:
                messagebox.showinfo(MSG_EXITO, msg, parent=modal)
                modal.destroy()
                self.refrescar()
            else:
                messagebox.showerror(MSG_ERROR, msg, parent=modal)

        tk.Button(modal, text="GUARDAR PROVEEDOR", bg="#27AE60", fg="white", font=("Arial", 10, "bold"), command=guardar).pack(fill="x", padx=20, pady=20)

    def eliminar_proveedor_seleccionado(self):
        sel = self.obtener_seleccionados()
        if not sel:
            messagebox.showwarning(MSG_AVISO, "Marca la casilla del proveedor a eliminar.")
            return

        id_prov, nombre_prov = sel[0][1], sel[0][2]

        if messagebox.askyesno("Confirmar", f"¿Eliminar a '{nombre_prov}'?\n(No se puede si tiene pedidos o productos registrados)"):
            if self.controlador.eliminar_proveedor(id_prov):
                messagebox.showinfo(MSG_EXITO, "Proveedor eliminado.")
                self.refrescar()
            else:
                messagebox.showerror(MSG_ERROR, "No se pudo eliminar. Tiene pedidos o productos vinculados.")

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
                    costo_val = float(self.e_costo.get().replace("Costo $", "").strip() or p.get("costo", p.get("precio_venta", 0)))
                    self.carrito_pedido.append({"id_producto": p["id"], "cantidad": cant, "costo_unitario": costo_val})
                    self.tabla_modal.insert("", "end", values=(prod_nombre, cant, f"${costo_val:.2f}"))
                    self.e_cant.delete(0, "end")
                    break
        except ValueError:
            messagebox.showerror(MSG_ERROR, "La cantidad debe ser un número entero.")

    def _guardar_pedido(self):
        prov = next((p for p in self.controlador.obtener_proveedores() if p["nombre"] == self.cmb_prov.get()), None)
        if prov and self.carrito_pedido:
            if self.controlador.crear_pedido_manual(prov["id"], self.carrito_pedido):
                messagebox.showinfo(MSG_EXITO, "Pedido enviado al proveedor.")
                if self.modal:
                    self.modal.destroy()
            else:
                messagebox.showerror(MSG_ERROR, "No se pudo guardar.")

    def nuevo_pedido(self):
        self.modal = tk.Toplevel(self)
        self.modal.geometry("500x600")
        self.modal.title("Crear Pedido a Proveedor")
        self.modal.grab_set()
        self.carrito_pedido.clear()

        tk.Label(self.modal, text="Proveedor:").pack(pady=(10, 2))
        self.cmb_prov = ttk.Combobox(self.modal, values=[p["nombre"] for p in self.controlador.obtener_proveedores()], state="readonly", width=35)
        self.cmb_prov.pack()

        frame_add = tk.Frame(self.modal)
        frame_add.pack(pady=10)
        self.cmb_prods = ttk.Combobox(frame_add, state="readonly", width=25)
        self.cmb_prods.pack(side="left")
        self.e_cant = tk.Entry(frame_add, width=5)
        self.e_cant.pack(side="left", padx=4)
        self.e_costo = tk.Entry(frame_add, width=8)
        self.e_costo.pack(side="left")
        self.e_costo.insert(0, "Costo $")

        self.tabla_modal = ttk.Treeview(self.modal, columns=("PROD", "CANT", "COSTO"), show="headings", height=8)
        for c in ("PROD", "CANT", "COSTO"):
            self.tabla_modal.heading(c, text=c)
        self.tabla_modal.column("PROD", width=250)
        self.tabla_modal.column("CANT", width=50, anchor="center")
        self.tabla_modal.column("COSTO", width=80, anchor="center")
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
        tabla.column("ID", width=80, anchor="center")
        tabla.column("PROD", width=300)
        tabla.column("CANT", width=80, anchor="center")
        tabla.column("TOTAL", width=100, anchor="center")
        tabla.pack(fill="both", expand=True, padx=10, pady=10)

        for p in self.controlador.obtener_pedidos_activos():
            tabla.insert("", "end", values=(p["id_pedido"], p["producto"], p["cantidad"], f"${float(p['subtotal']):.2f}"))

        tk.Button(
            modal, text="RECIBIR MERCANCÍA", bg="#27AE60", fg="white",
            command=lambda: self._recibir_mercancia(tabla, modal),
        ).pack(pady=10)