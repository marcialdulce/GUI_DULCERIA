import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos


class PanelDevoluciones(tk.Frame):
    """Busca ventas y registra devoluciones parciales con reposición de stock."""
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.ventas = []
        self.venta_actual = None
        self.articulo_actual = None

        tk.Label(self, text="DEVOLUCIONES Y CANCELACIONES", bg=estilos.FONDO,
                 fg="#4A2E35", font=("Arial", 20, "bold")).pack(pady=(18, 10))
        filtros = tk.Frame(self, bg=estilos.FONDO)
        filtros.pack(fill="x", padx=25, pady=8)
        tk.Label(filtros, text="Folio de venta:", bg=estilos.FONDO,
                 font=("Arial", 10, "bold")).pack(side="left")
        self.entry_folio = tk.Entry(filtros, width=24, font=("Arial", 10))
        self.entry_folio.pack(side="left", padx=8)
        tk.Button(filtros, text="BUSCAR VENTA", bg="#F4D03F", relief="flat",
                  font=("Arial", 9, "bold"), command=self.buscar_venta).pack(side="left", padx=5)
        tk.Button(filtros, text="MOSTRAR TODAS", bg="#D9EDEF", relief="flat",
                  command=self.mostrar_todas).pack(side="left", padx=5)

        marco = tk.Frame(self, bg="white", bd=1, relief="solid")
        marco.pack(fill="both", expand=True, padx=25, pady=8)
        tk.Label(marco, text="PRODUCTOS DE LA VENTA", bg="white",
                 font=("Arial", 11, "bold")).pack(pady=8)
        cols = ("producto", "cantidad", "devueltos", "disponibles", "importe")
        self.tabla = ttk.Treeview(marco, columns=cols, show="headings", height=9)
        titulos = {"producto":"PRODUCTO", "cantidad":"COMPRADOS", "devueltos":"DEVUELTOS",
                   "disponibles":"DISPONIBLES", "importe":"IMPORTE ORIGINAL"}
        anchos = {"producto":230, "cantidad":90, "devueltos":90, "disponibles":90, "importe":130}
        for c in cols:
            self.tabla.heading(c, text=titulos[c]); self.tabla.column(c, width=anchos[c], anchor="center")
        self.tabla.pack(fill="both", expand=True, padx=12, pady=8)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_articulo)

        acciones = tk.LabelFrame(self, text="REGISTRAR DEVOLUCIÓN", bg=estilos.FONDO,
                                 font=("Arial", 10, "bold"), padx=12, pady=10)
        acciones.pack(fill="x", padx=25, pady=(5, 15))
        fila = tk.Frame(acciones, bg=estilos.FONDO); fila.pack(fill="x")
        tk.Label(fila, text="Cantidad:", bg=estilos.FONDO).pack(side="left")
        self.cantidad = tk.Spinbox(fila, from_=1, to=999, width=6); self.cantidad.pack(side="left", padx=6)
        tk.Label(fila, text="Motivo:", bg=estilos.FONDO).pack(side="left", padx=(15, 3))
        self.motivo = tk.StringVar()
        ttk.Combobox(fila, textvariable=self.motivo, width=25, state="readonly",
                     values=("Producto dañado", "Producto equivocado", "Compra duplicada", "Cliente ya no lo necesita", "Otro")).pack(side="left", padx=5)
        self.importe_label = tk.Label(fila, text="Reembolso estimado: $0.00", bg=estilos.FONDO,
                                      fg="#3A8D96", font=("Arial", 10, "bold"))
        self.importe_label.pack(side="left", padx=12)
        tk.Button(acciones, text="CALCULAR DEVOLUCIÓN", bg="#D9EDEF", relief="flat",
                  command=self.calcular).pack(side="left", padx=5, pady=10)
        tk.Button(acciones, text="CONFIRMAR DEVOLUCIÓN", bg="#F4D03F", relief="flat",
                  font=("Arial", 9, "bold"), command=self.confirmar).pack(side="right", padx=5, pady=10)
        self.mostrar_todas()

    def mostrar_todas(self):
        self.ventas = self.controlador.obtener_ventas_para_devolucion()
        self.venta_actual = None; self.articulo_actual = None
        self._limpiar_tabla()

    def _limpiar_tabla(self):
        for iid in self.tabla.get_children(): self.tabla.delete(iid)

    def buscar_venta(self):
        folio = self.entry_folio.get().strip().upper()
        if not folio:
            messagebox.showwarning("Folio requerido", "Escribe el folio del ticket.", parent=self); return
        self.ventas = self.controlador.obtener_ventas_para_devolucion()
        venta = next((v for v in self.ventas if str(v.get("folio", "")).upper() == folio), None)
        if not venta:
            messagebox.showerror("Venta no encontrada", "No existe una venta con ese folio.", parent=self); return
        self.venta_actual = venta; self.articulo_actual = None; self._limpiar_tabla()
        devueltos = self.controlador.obtener_cantidades_devueltas()
        for a in venta.get("articulos", []):
            qty = int(a.get("cantidad", 0)); d = devueltos.get((folio, a.get("producto")), 0)
            disponible = max(0, qty-d)
            self.tabla.insert("", "end", values=(a.get("producto"), qty, d, disponible, f"${float(a.get('subtotal',0)):.2f}"))
        if not venta.get("articulos"):
            messagebox.showwarning("Sin productos", "La venta no contiene artículos consultables.", parent=self)

    def seleccionar_articulo(self, _event=None):
        sel = self.tabla.selection()
        if not sel or not self.venta_actual: return
        valores = self.tabla.item(sel[0], "values")
        self.articulo_actual = next((a for a in self.venta_actual.get("articulos", []) if a.get("producto") == valores[0]), None)
        disponible = int(valores[3])
        self.cantidad.config(from_=1, to=max(1, disponible)); self.cantidad.delete(0, "end"); self.cantidad.insert(0, "1")
        self.calcular()

    def calcular(self):
        if not self.articulo_actual:
            messagebox.showwarning("Selecciona un producto", "Primero busca una venta y selecciona un producto.", parent=self); return
        try: cantidad = int(self.cantidad.get())
        except ValueError: cantidad = 0
        qty = max(int(self.articulo_actual.get("cantidad", 1)), 1)
        importe = float(self.articulo_actual.get("subtotal", 0)) / qty * max(cantidad, 0)
        self.importe_label.config(text=f"Reembolso estimado: ${importe:.2f}")

    def confirmar(self):
        if not self.venta_actual or not self.articulo_actual:
            messagebox.showwarning("Datos incompletos", "Busca una venta y selecciona el producto que devolverás.", parent=self); return
        try: cantidad = int(self.cantidad.get())
        except ValueError:
            messagebox.showerror("Cantidad inválida", "Escribe una cantidad válida.", parent=self); return
        motivo = self.motivo.get().strip()
        if not motivo:
            messagebox.showwarning("Motivo requerido", "Selecciona el motivo de la devolución.", parent=self); return
        nombre = self.articulo_actual.get("producto")
        ok, resultado = self.controlador.registrar_devolucion(self.venta_actual, nombre, cantidad, motivo)
        if not ok:
            messagebox.showerror("No se pudo devolver", resultado, parent=self); return
        messagebox.showinfo("Devolución registrada",
            f"Folio de devolución: {resultado['folio_devolucion']}\nProducto: {nombre}\nCantidad: {cantidad}\nReembolso: ${resultado['importe']:.2f}\n\nEl inventario fue actualizado.", parent=self)
        self.buscar_venta()
        
