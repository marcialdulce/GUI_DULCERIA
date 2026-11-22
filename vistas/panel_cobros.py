import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from vistas import estilos
from servicios.hilo_factura import HiloFactura
from vistas.generador_tickets import generar_comprobante_ticket_pdf, abrir_archivo_pdf


def guardar_ticket_con_explorador(resumen_venta, parent=None):
    folio = resumen_venta.get("folio", "venta")
    ruta_pdf = filedialog.asksaveasfilename(
        parent=parent,
        title="Guardar Ticket de Venta",
        defaultextension=".pdf",
        initialfile=f"Ticket_{folio}.pdf",
        filetypes=[("Archivo PDF", "*.pdf")],
    )
    if not ruta_pdf:
        return

    try:
        generar_comprobante_ticket_pdf(ruta_pdf, resumen_venta)
        messagebox.showinfo("Ticket guardado", f"Ticket guardado en:\n{ruta_pdf}", parent=parent)
        abrir_archivo_pdf(ruta_pdf)
    except Exception as e:
        messagebox.showerror("Error al generar ticket", str(e), parent=parent)


def guardar_factura_con_explorador(resumen_venta, datos_factura, parent=None):
    folio = resumen_venta.get("folio_factura") or resumen_venta.get("folio", "venta")
    rfc = datos_factura.get("rfc", "XAXX010101000")

    ruta_pdf = filedialog.asksaveasfilename(
        parent=parent,
        title="Guardar Factura PDF",
        defaultextension=".pdf",
        initialfile=f"Factura_{folio}_{rfc}.pdf",
        filetypes=[("Archivo PDF", "*.pdf")],
    )
    if not ruta_pdf:
        return None

    hilo = HiloFactura(
        ruta_completa=ruta_pdf,
        rfc=rfc,
        razon_social=datos_factura.get("razon_social", ""),
        total=resumen_venta["total"],
        carrito=resumen_venta["articulos"],
        metodo_pago=resumen_venta["metodo_pago"],
        pago=resumen_venta["total_pagado"],
        cambio=resumen_venta["cambio"],
        regimen_fiscal=datos_factura.get("regimen", ""),
        cp_fiscal=datos_factura.get("cp", ""),
        correo=datos_factura.get("correo", ""),
        folio_factura=folio,
    )
    hilo.start()
    messagebox.showinfo(
        "Factura en proceso",
        f"La factura se está generando en segundo plano y se guardará en:\n{ruta_pdf}",
        parent=parent,
    )
    return hilo


class PanelCobros(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.pagos = []
        self.datos_factura = None

        tk.Label(self, text="COBRO Y FACTURACIÓN", bg=estilos.FONDO, font=("Arial", 18, "bold")).pack(pady=(12, 4))

        self.lbl_desglose = tk.Label(self, text="Subtotal: $0.00  |  IVA (16%): $0.00", bg=estilos.FONDO, fg="#666666", font=("Arial", 10))
        self.lbl_desglose.pack()

        self.lbl_total = tk.Label(self, text="$0.00", bg=estilos.FONDO, fg="#27AE60", font=("Arial", 24, "bold"))
        self.lbl_total.pack()

        self.lbl_restante = tk.Label(
            self,
            text="Pagado: $0.00  |  Restante: $0.00  |  Cambio: $0.00",
            bg=estilos.FONDO,
            fg="#4A2E35",
            font=("Arial", 10, "bold"),
        )
        self.lbl_restante.pack(pady=(2, 8))

        # --- BARRA DE CAPTURA DE PAGO MIXTO (Regla #5) ---
        frame_pago = tk.Frame(self, bg=estilos.FONDO)
        frame_pago.pack(pady=8)

        tk.Label(frame_pago, text="Método:", bg=estilos.FONDO, font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
        self.cmb_metodo = ttk.Combobox(
            frame_pago,
            values=["Efectivo", "Tarjeta de débito", "Tarjeta de crédito"],
            state="readonly",
            width=18,
        )
        self.cmb_metodo.current(0)
        self.cmb_metodo.pack(side="left")
        self.cmb_metodo.bind("<<ComboboxSelected>>", self._actualizar_estado_referencia)

        tk.Label(frame_pago, text="Monto $:", bg=estilos.FONDO, font=("Arial", 9, "bold")).pack(side="left", padx=(10, 4))
        self.e_monto = tk.Entry(frame_pago, width=10)
        self.e_monto.pack(side="left", padx=4)
        self.e_monto.bind("<Return>", lambda e: self.agregar_pago())

        tk.Label(frame_pago, text="Ref. Tarjeta:", bg=estilos.FONDO, font=("Arial", 9, "bold")).pack(side="left", padx=(10, 4))
        self.e_ref = tk.Entry(frame_pago, width=16)
        self.e_ref.pack(side="left", padx=4)

        tk.Button(
            frame_pago, text="+ AGREGAR PAGO", bg="#27AE60", fg="white",
            font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
            command=self.agregar_pago,
        ).pack(side="left", padx=(8, 0))

        # --- TABLA DE PAGOS APLICADOS ---
        self.tabla_pagos = ttk.Treeview(self, columns=("MÉTODO", "REFERENCIA", "MONTO"), show="headings", height=4)
        anchos = {"MÉTODO": 200, "REFERENCIA": 220, "MONTO": 120}
        for c in ("MÉTODO", "REFERENCIA", "MONTO"):
            self.tabla_pagos.heading(c, text=c)
            self.tabla_pagos.column(c, width=anchos[c], anchor="center")
        self.tabla_pagos.pack(fill="x", padx=50, pady=(4, 4))

        # Botones para corregir pagos mal capturados
        frame_acciones_pago = tk.Frame(self, bg=estilos.FONDO)
        frame_acciones_pago.pack(fill="x", padx=50, pady=(2, 8))

        tk.Button(
            frame_acciones_pago, text="QUITAR PAGO SELECCIONADO", bg="#E67E22", fg="white",
            font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
            command=self.quitar_pago_seleccionado,
        ).pack(side="left")

        tk.Button(
            frame_acciones_pago, text="LIMPIAR PAGOS", bg="#C0392B", fg="white",
            font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
            command=self.limpiar_pagos,
        ).pack(side="right")

        self.lbl_estado_factura = tk.Label(self, text="Factura: No solicitada", bg=estilos.FONDO, fg="#666666", font=("Arial", 9))
        self.lbl_estado_factura.pack(pady=(4, 2))

        tk.Button(
            self, text="🧾 AGREGAR / EDITAR FACTURA", bg="#8E44AD", fg="white",
            font=("Arial", 9, "bold"), relief="flat", cursor="hand2", padx=12, pady=5,
            command=self.abrir_factura,
        ).pack(pady=6)

        tk.Button(
            self, text="CONFIRMAR COBRO", bg="#F4D03F",
            font=("Arial", 12, "bold"), relief="flat", cursor="hand2", padx=20, pady=8,
            command=self.cobrar,
        ).pack(pady=8)

        self._actualizar_estado_referencia()
        self.refrescar()

    def _actualizar_estado_referencia(self, event=None):
        """Deshabilita el campo de referencia cuando el método de pago es Efectivo."""
        if self.cmb_metodo.get() == "Efectivo":
            self.e_ref.config(state="normal")
            self.e_ref.delete(0, "end")
            self.e_ref.config(state="disabled")
        else:
            self.e_ref.config(state="normal")

    def refrescar(self):
        subtotal, iva, total = self.controlador.obtener_desglose_ticket()
        pagado = round(sum(p["monto"] for p in self.pagos), 2)
        restante = round(max(0.0, total - pagado), 2)
        cambio = round(max(0.0, pagado - total), 2)

        self.lbl_desglose.config(text=f"Subtotal: ${subtotal:.2f}  |  IVA (16%): ${iva:.2f}")
        self.lbl_total.config(text=f"${total:.2f}")
        self.lbl_restante.config(text=f"Pagado: ${pagado:.2f}  |  Restante: ${restante:.2f}  |  Cambio: ${cambio:.2f}")

        # Sugiere automáticamente el saldo restante en la caja de monto
        self.e_monto.delete(0, "end")
        if restante > 0:
            self.e_monto.insert(0, f"{restante:.2f}")

    def agregar_pago(self):
        try:
            monto = round(float(self.e_monto.get()), 2)
            if monto <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Monto inválido", "Ingresa una cantidad numérica mayor a 0.")
            return

        metodo = self.cmb_metodo.get()
        if metodo == "Efectivo":
            id_m = 1
            ref = None
        else:
            id_m = 2 if metodo == "Tarjeta de débito" else 3
            ref = self.e_ref.get().strip()
            if not ref:
                messagebox.showwarning("Referencia requerida", f"Ingresa la referencia o últimos 4 dígitos para {metodo}.")
                self.e_ref.focus_set()
                return

        self.pagos.append({"id_metodo_pago": id_m, "monto": monto, "referencia": ref})
        self.tabla_pagos.insert("", "end", values=(metodo, ref or "-", f"${monto:.2f}"))

        if metodo != "Efectivo":
            self.e_ref.delete(0, "end")
        self.refrescar()

    def quitar_pago_seleccionado(self):
        seleccion = self.tabla_pagos.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Selecciona el pago que deseas quitar.")
            return

        indice = self.tabla_pagos.index(seleccion[0])
        self.tabla_pagos.delete(seleccion[0])
        if 0 <= indice < len(self.pagos):
            self.pagos.pop(indice)
        self.refrescar()

    def limpiar_pagos(self):
        if not self.pagos:
            return
        self.pagos.clear()
        self.tabla_pagos.delete(*self.tabla_pagos.get_children())
        self.refrescar()

    def abrir_factura(self):
        modal = tk.Toplevel(self)
        modal.title("Datos de Facturación")
        modal.geometry("360x380")
        modal.grab_set()

        campos = [
            ("RFC:", "rfc"),
            ("Razón Social:", "razon_social"),
            ("Régimen Fiscal:", "regimen"),
            ("Código Postal:", "cp"),
            ("Correo:", "correo"),
        ]
        entries = {}
        for txt, key in campos:
            tk.Label(modal, text=txt).pack(pady=(6, 0))
            e = tk.Entry(modal, width=35)
            if self.datos_factura and key in self.datos_factura:
                e.insert(0, self.datos_factura[key])
            e.pack()
            entries[key] = e

        def guardar():
            datos = {"requiere": True}
            for k, e in entries.items():
                val = e.get().strip()
                if not val:
                    messagebox.showwarning("Campos incompletos", "Completa todos los datos fiscales.", parent=modal)
                    return
                datos[k] = val
            self.datos_factura = datos
            self.lbl_estado_factura.config(text=f"Factura lista para: {datos['rfc']} ({datos['razon_social']})", fg="#27AE60")
            messagebox.showinfo("Éxito", "Datos fiscales guardados.", parent=modal)
            modal.destroy()

        def quitar_factura():
            self.datos_factura = None
            self.lbl_estado_factura.config(text="Factura: No solicitada", fg="#666666")
            modal.destroy()

        tk.Button(modal, text="GUARDAR DATOS", bg="#27AE60", fg="white", command=guardar).pack(pady=(15, 5))
        if self.datos_factura:
            tk.Button(modal, text="QUITAR FACTURA", bg="#C0392B", fg="white", command=quitar_factura).pack(pady=4)

    def cobrar(self):
        _, carrito, total = self.controlador.obtener_datos_ventas()
        if not carrito:
            messagebox.showwarning("Carrito vacío", "Agrega productos en Nueva Venta antes de cobrar.")
            return

        total_pagado = round(sum(p["monto"] for p in self.pagos), 2)
        if total_pagado < total:
            messagebox.showwarning("Pago incompleto", f"Faltan ${total - total_pagado:.2f} por cubrir.")
            return

        cambio_est = round(total_pagado - total, 2)
        resumen_txt = (
            f"Artículos en ticket: {sum(i['cantidad'] for i in carrito)}\n"
            f"Total a cobrar (con IVA): ${total:.2f}\n"
            f"Total recibido: ${total_pagado:.2f}\n"
            f"Cambio: ${cambio_est:.2f}\n"
            f"Factura solicitada: {'Sí (' + self.datos_factura['rfc'] + ')' if self.datos_factura else 'No'}\n\n"
            "Recuerda: No se permiten cancelaciones ni devoluciones.\n"
            "¿Confirmar cobro y emitir comprobante?"
        )
        if not messagebox.askyesno("Confirmar Venta (Regla #4)", resumen_txt):
            return

        factura_actual = dict(self.datos_factura) if self.datos_factura else None
        exito, msg, resumen_venta = self.controlador.procesar_cobro_avanzado(self.pagos, factura_actual)

        if exito:
            messagebox.showinfo("Éxito", msg)
            guardar_ticket_con_explorador(resumen_venta, parent=self)

            if factura_actual:
                guardar_factura_con_explorador(resumen_venta, factura_actual, parent=self)

            self.pagos.clear()
            self.tabla_pagos.delete(*self.tabla_pagos.get_children())
            self.datos_factura = None
            self.lbl_estado_factura.config(text="Factura: No solicitada", fg="#666666")
            self.refrescar()
        else:
            messagebox.showerror("Error", msg)