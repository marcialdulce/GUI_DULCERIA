import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

MSG_EXITO = "Éxito"
MSG_AVISO = "Aviso"


class PanelApartados(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg="#F9F4F0")
        self.controlador = controlador
        self.carrito = []

        tk.Label(self, text="CONTROL DE APARTADOS", bg="#2D929A", fg="white", font=("Arial", 11, "bold")).pack(fill="x", padx=15, pady=5)

        frame_btns = tk.Frame(self, bg="#F9F4F0")
        frame_btns.pack(fill="x", padx=15, pady=8)

        tk.Button(frame_btns, text="+ NUEVO APARTADO", bg="#27AE60", fg="white", font=("Arial", 9, "bold"), relief="flat", cursor="hand2", command=self.abrir_nuevo_apartado).pack(side="left")
        tk.Button(frame_btns, text="LIQUIDAR SELECCIONADO", bg="#2980B9", fg="white", font=("Arial", 9, "bold"), relief="flat", cursor="hand2", command=self.liquidar_apartado).pack(side="left", padx=10)

        tk.Label(frame_btns, text="Mostrar:", bg="#F9F4F0", font=("Arial", 9, "bold")).pack(side="left", padx=(15, 5))
        self.cmb_filtro = ttk.Combobox(frame_btns, values=["Todos (Pendientes primero)", "Pendiente", "Liquidado", "Cancelado"], state="readonly", width=24)
        self.cmb_filtro.set("Todos (Pendientes primero)")
        self.cmb_filtro.pack(side="left")
        self.cmb_filtro.bind("<<ComboboxSelected>>", lambda e: self.cargar_tabla())

        tk.Button(frame_btns, text="CANCELAR", bg="#C0392B", fg="white", font=("Arial", 9, "bold"), relief="flat", cursor="hand2", command=self.cancelar_apartado).pack(side="right")

        columnas = ("SEL", "ID", "CLIENTE", "PRODUCTOS", "ENTREGA", "TOTAL", "PAGADO", "ESTADO")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings")

        self.tabla.heading("SEL", text="[ ]")
        self.tabla.column("SEL", width=38, anchor="center")

        anchos = {"ID": 48, "CLIENTE": 165, "PRODUCTOS": 265, "ENTREGA": 90, "TOTAL": 85, "PAGADO": 85, "ESTADO": 90}
        for c in columnas[1:]:
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="w" if c in ("CLIENTE", "PRODUCTOS") else "center", width=anchos[c])

        self.tabla.tag_configure("pendiente", background="#FCF3CF", foreground="#7D6608")
        self.tabla.tag_configure("liquidado", background="#EAFAF1", foreground="#1E8449")
        self.tabla.tag_configure("cancelado", background="#FADBD8", foreground="#922B21")

        self.tabla.pack(fill="both", expand=True, padx=15, pady=5)
        self.tabla.bind("<ButtonRelease-1>", self.toggle_sel)

        self.cargar_tabla()

    def toggle_sel(self, event):
        """Selección exclusiva de 1 apartado a la vez."""
        item = self.tabla.identify_row(event.y)
        if not item:
            return

        vals_click = list(self.tabla.item(item, "values"))
        estaba_marcado = vals_click[0] == "☑"

        for iid in self.tabla.get_children():
            vals = list(self.tabla.item(iid, "values"))
            if vals[0] == "☑":
                vals[0] = "☐"
                self.tabla.item(iid, values=vals)

        if not estaba_marcado:
            vals_click[0] = "☑"
            self.tabla.item(item, values=vals_click)

    def obtener_seleccionados(self):
        return [self.tabla.item(i)["values"] for i in self.tabla.get_children() if self.tabla.item(i)["values"][0] == "☑"]

    def cargar_tabla(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)

        filtro = self.cmb_filtro.get().lower()
        for item in self.controlador.obtener_lista_apartados():
            estado_raw = str(item["estado"]).lower()
            if filtro in ("pendiente", "liquidado", "cancelado") and estado_raw != filtro:
                continue

            total = round(float(item["subtotal"]) + float(item["impuesto"]), 2)
            pagado = round(float(item["pagado"]), 2)

            self.tabla.insert(
                "",
                "end",
                values=(
                    "☐",
                    item["id_apartado"],
                    item["nombre"],
                    item["producto"],
                    item["fecha"],
                    f"${total:.2f}",
                    f"${pagado:.2f}",
                    estado_raw.capitalize(),
                ),
                tags=(estado_raw,),
            )

    def liquidar_apartado(self):
        sel = self.obtener_seleccionados()
        if not sel:
            return messagebox.showwarning(MSG_AVISO, "Marca la casilla de 1 apartado.")

        item = sel[0]
        estado = str(item[7]).lower()
        if estado != "pendiente":
            return messagebox.showinfo("Info", f"Solo se pueden liquidar apartados pendientes (actual: {item[7]}).")

        total = float(str(item[5]).replace("$", ""))
        pagado = float(str(item[6]).replace("$", ""))
        saldo = round(max(0.0, total - pagado), 2)

        pago = simpledialog.askfloat("Liquidar", f"Cliente: {item[2]}\nSaldo pendiente: ${saldo:.2f}\n¿Con cuánto paga el cliente?", minvalue=0.0)
        if pago is None:
            return
        if pago < saldo:
            return messagebox.showwarning("Pago insuficiente", f"Faltan ${saldo - pago:.2f} para liquidar el apartado.")

        if self.controlador.liquidar_apartado(item[1], [{"monto": saldo, "id_metodo_pago": 1, "referencia": None}]):
            messagebox.showinfo(MSG_EXITO, f"Apartado liquidado. Cambio: ${pago - saldo:.2f}")
            self.cargar_tabla()

    def cancelar_apartado(self):
        sel = self.obtener_seleccionados()
        if not sel:
            return messagebox.showwarning(MSG_AVISO, "Marca la casilla de 1 apartado.")

        estado = str(sel[0][7]).lower()
        if estado != "pendiente":
            return messagebox.showinfo(MSG_AVISO, f"Solo se pueden cancelar apartados pendientes (estado actual: {sel[0][7]}).")

        if messagebox.askyesno("Cancelar", f"¿Cancelar el apartado #{sel[0][1]} de {sel[0][2]}?\nEl anticipo NO es reembolsable (Regla #9). El stock regresará al inventario."):
            ok, msg = self.controlador.cancelar_apartado(sel[0][1])
            if ok:
                messagebox.showinfo(MSG_EXITO, msg)
                self.cargar_tabla()
            else:
                messagebox.showerror("Error", msg)

    def abrir_nuevo_apartado(self):
        modal = tk.Toplevel(self)
        modal.geometry("460x560")
        modal.title("Nuevo Apartado (Carrito)")
        modal.grab_set()
        self.carrito.clear()

        tk.Label(modal, text="Nombre del cliente:").pack(pady=(8, 0))
        e_nombre = tk.Entry(modal, width=38)
        e_nombre.pack()

        tk.Label(modal, text="Teléfono:").pack(pady=(6, 0))
        e_tel = tk.Entry(modal, width=38)
        e_tel.pack()

        tk.Label(modal, text="Fecha de entrega (AAAA-MM-DD):").pack(pady=(6, 0))
        e_fecha = tk.Entry(modal, width=38)
        e_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        e_fecha.pack()

        frame_add = tk.Frame(modal)
        frame_add.pack(pady=10)

        cmb_prods = ttk.Combobox(frame_add, values=self.controlador.obtener_nombres_productos(), state="readonly", width=26)
        cmb_prods.pack(side="left", padx=5)

        e_cant = tk.Entry(frame_add, width=5)
        e_cant.pack(side="left")

        tabla_c = ttk.Treeview(modal, columns=("PROD", "CANT", "SUBTOTAL"), show="headings", height=5)
        tabla_c.heading("PROD", text="Producto")
        tabla_c.heading("CANT", text="Cant")
        tabla_c.heading("SUBTOTAL", text="Importe")
        tabla_c.column("PROD", width=220)
        tabla_c.column("CANT", width=55, anchor="center")
        tabla_c.column("SUBTOTAL", width=85, anchor="center")
        tabla_c.pack(fill="x", padx=20, pady=8)

        lbl_totales = tk.Label(modal, text="Total (IVA incl.): $0.00  |  Anticipo (50%): $0.00", font=("Arial", 9, "bold"), fg="#27AE60")
        lbl_totales.pack(pady=(0, 8))

        tk.Button(
            frame_add, text="+", width=3, bg="#F4D03F", font=("Arial", 9, "bold"),
            command=lambda: self._agregar_al_carrito(cmb_prods, e_cant, tabla_c, lbl_totales),
        ).pack(side="left", padx=4)

        tk.Label(modal, text="Método Pago Anticipo (50%):").pack()
        cmb_metodo = ttk.Combobox(modal, values=["Efectivo", "Tarjeta de débito", "Tarjeta de crédito"], state="readonly")
        cmb_metodo.current(0)
        cmb_metodo.pack(pady=4)

        tk.Button(
            modal, text="REGISTRAR APARTADO", bg="#27AE60", fg="white", font=("Arial", 10, "bold"),
            command=lambda: self._guardar_apartado(modal, e_nombre, e_tel, e_fecha, cmb_metodo),
        ).pack(pady=12)

    def _agregar_al_carrito(self, cmb_prods, e_cant, tabla_c, lbl_totales):
        prod = next((p for p in self.controlador.modelo.inventario if p["nombre"] == cmb_prods.get()), None)
        if not prod or not e_cant.get().isdigit():
            return
        cant = int(e_cant.get())
        if cant <= 0:
            return
        ya_en_carrito = sum(a["cantidad"] for a in self.carrito if a["id_producto"] == prod["id_producto"])
        if (ya_en_carrito + cant) > prod["stock"]:
            messagebox.showwarning("Stock insuficiente", f"Solo hay {prod['stock']} disponibles de '{prod['nombre']}'.")
            return
        sub = round(cant * prod["precio"], 2)
        self.carrito.append({
            "id_producto": prod["id_producto"],
            "nombre": prod["nombre"],
            "precio_unitario": prod["precio"],
            "cantidad": cant,
        })
        tabla_c.insert("", "end", values=(prod["nombre"], cant, f"${sub:.2f}"))
        e_cant.delete(0, "end")

        total = round(sum(a["precio_unitario"] * a["cantidad"] for a in self.carrito), 2)
        anticipo = round(total * 0.50, 2)
        lbl_totales.config(text=f"Total (IVA incl.): ${total:.2f}  |  Anticipo (50%): ${anticipo:.2f}")

    def _guardar_apartado(self, modal, e_nombre, e_tel, e_fecha, cmb_metodo):
        if not e_nombre.get().strip() or not self.carrito:
            return messagebox.showwarning(MSG_AVISO, "Faltan datos o productos.", parent=modal)

        total = round(sum(a["precio_unitario"] * a["cantidad"] for a in self.carrito), 2)
        anticipo = round(total * 0.50, 2)

        metodo_seleccionado = cmb_metodo.get()
        if metodo_seleccionado == "Efectivo":
            id_metodo = 1
        elif metodo_seleccionado == "Tarjeta de débito":
            id_metodo = 2
        else:
            id_metodo = 3

        ok, msg = self.controlador.registrar_apartado(
            e_nombre.get().strip(), e_tel.get().strip(), e_fecha.get().strip(), self.carrito,
            [{"monto": anticipo, "id_metodo_pago": id_metodo}],
        )

        if ok:
            messagebox.showinfo(
                MSG_EXITO,
                f"{msg}\nTotal (IVA incl.): ${total:.2f}\nCobrar anticipo (50%): ${anticipo:.2f}",
                parent=modal,
            )
            modal.destroy()
            self.cargar_tabla()
        else:
            messagebox.showerror("Error", msg, parent=modal)