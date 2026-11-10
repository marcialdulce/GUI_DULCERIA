import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from vistas import estilos

# Constantes para evitar duplicación (SonarQube)
MSG_EXITO = "Éxito"
MSG_ERROR = "Error"
MSG_AVISO = "Aviso"

class PanelInventario(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.es_admin = (controlador.rol_actual == "Administrador")

        barra = tk.Frame(self, bg="#3A8D96", height=40)
        barra.pack(fill="x", pady=10)
        
        frame_filtros = tk.Frame(self, bg="#3A8D96")
        frame_filtros.pack(fill="x", pady=5)
        
        tk.Label(frame_filtros, text="BUSCAR:", bg="#3A8D96", fg="white").pack(side="left", padx=10)
        self.e_buscar = tk.Entry(frame_filtros, width=30)
        self.e_buscar.pack(side="left", padx=5)
        self.e_buscar.bind("<KeyRelease>", lambda e: self.notificar_filtros())

        if self.es_admin:
            tk.Button(barra, text="+ NUEVO PRODUCTO", bg="#27AE60", fg="white", command=self.abrir_formulario_nuevo).pack(side="left", padx=5)
            tk.Button(barra, text="EDITAR SELECCIONADO", bg="#2980B9", fg="white", command=self.editar_seleccionado).pack(side="left", padx=5)
            tk.Button(barra, text="ELIMINAR SELECCIONADO", bg="#C0392B", fg="white", command=self.eliminar_seleccionado).pack(side="left", padx=5)

        tk.Button(barra, text="REGISTRAR MERMA", bg="#E74C3C", fg="white", command=self.abrir_merma).pack(side="right", padx=10)

        columnas = ("SEL", "ID", "PRODUCTO", "PRECIO", "STOCK", "ESTADO")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings")
        
        self.tabla.heading("SEL", text="[ ]")
        self.tabla.column("SEL", width=40, anchor="center")
        
        anchos = {"ID": 60, "PRODUCTO": 350, "PRECIO": 100, "STOCK": 100, "ESTADO": 100}
        for c in columnas[1:]:
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="center", width=anchos[c])

        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)
        self.tabla.bind("<ButtonRelease-1>", self.toggle_sel)
        self.notificar_filtros()

    def toggle_sel(self, event):
        item = self.tabla.identify_row(event.y)
        if item:
            vals = list(self.tabla.item(item, "values"))
            vals[0] = "☑" if vals[0] == "☐" else "☐"
            self.tabla.item(item, values=vals)

    def obtener_seleccionados(self):
        return [self.tabla.item(i)["values"] for i in self.tabla.get_children() if self.tabla.item(i)["values"][0] == "☑"]

    def notificar_filtros(self):
        datos = self.controlador.obtener_inventario_filtrado(self.e_buscar.get().lower(), "Todas", "Todas")
        for f in self.tabla.get_children(): 
            self.tabla.delete(f)
        for p in datos:
            self.tabla.insert("", "end", values=("☐", p["id_producto"], p["nombre"], f"${p['precio']:.2f}", p["stock"], "AGOTADO" if p["stock"] == 0 else "OK"))

    def abrir_merma(self):
        sel = self.obtener_seleccionados()
        if not sel: 
            return messagebox.showwarning(MSG_AVISO, "Marca la casilla de un producto.")
        
        item = sel[0]
        id_prod, nombre = item[1], item[2]
        cant = simpledialog.askinteger("Merma", f"¿Unidades de '{nombre}' perdidas/dañadas?")
        if cant and cant > 0:
            ok, msg = self.controlador.registrar_merma(id_prod, cant, "Merma manual")
            if ok:
                messagebox.showinfo(MSG_EXITO, msg)
                self.notificar_filtros()
            else:
                messagebox.showerror(MSG_ERROR, msg)

    def _producto_por_id(self, id_prod):
        return next((p for p in self.controlador.modelo.inventario if int(p["id_producto"]) == int(id_prod)), None)

    def editar_seleccionado(self):
        sel = self.obtener_seleccionados()
        if not sel: 
            return messagebox.showwarning(MSG_AVISO, "Marca la casilla de un producto.")
        prod = self._producto_por_id(sel[0][1])
        if prod: 
            self.abrir_formulario(prod)

    def eliminar_seleccionado(self):
        sel = self.obtener_seleccionados()
        if not sel: 
            return messagebox.showwarning(MSG_AVISO, "Marca la casilla del producto a dar de baja.")
        
        id_prod, nombre = sel[0][1], sel[0][2]
        if not messagebox.askyesno("Confirmar", f"¿Dar de baja '{nombre}'?\nEl producto quedará inactivo."):
            return
        ok, msg = self.controlador.eliminar_producto(id_prod)
        if ok:
            messagebox.showinfo(MSG_EXITO, msg)
            self.notificar_filtros()
        else:
            messagebox.showerror(MSG_ERROR, msg)

    def abrir_formulario_nuevo(self):
        self.abrir_formulario(None)

    # --- MÉTODOS DE APOYO PARA EL FORMULARIO (Reducen la complejidad) ---

    def _agregar_campo_texto(self, modal, entradas, label, key, val=""):
        tk.Label(modal, text=label, anchor="w").pack(fill="x", padx=15, pady=(6, 0))
        e = tk.Entry(modal)
        e.insert(0, str(val))
        e.pack(fill="x", padx=15)
        entradas[key] = ("entry", e)

    def _agregar_combo(self, modal, entradas, label, key, opciones, id_sel=None):
        tk.Label(modal, text=label, anchor="w").pack(fill="x", padx=15, pady=(6, 0))
        cmb = ttk.Combobox(modal, values=[o["nombre"] for o in opciones], state="readonly")
        if id_sel:
            for i, o in enumerate(opciones):
                if o["id"] == id_sel:
                    cmb.current(i)
                    break
        elif opciones:
            cmb.current(0)
        cmb.pack(fill="x", padx=15)
        entradas[key] = ("combo", cmb, opciones)

    def abrir_formulario(self, producto):
        es_nuevo = producto is None
        modal = tk.Toplevel(self)
        modal.title("Nuevo Producto" if es_nuevo else "Editar Producto")
        modal.geometry("420x600")
        modal.grab_set()

        p = producto or {}
        
        marcas = self.controlador.obtener_marcas()
        categorias = self.controlador.obtener_categorias()
        unidades = self.controlador.obtener_unidades()
        proveedores = self.controlador.obtener_proveedores()
        entradas = {}

        self._agregar_campo_texto(modal, entradas, "Código de barras:", "codigo_barras", p.get("codigo_barras", ""))
        self._agregar_campo_texto(modal, entradas, "Nombre del dulce:", "nombre_dulce", p.get("nombre", ""))
        self._agregar_campo_texto(modal, entradas, "Precio venta:", "precio_venta", p.get("precio", ""))
        self._agregar_campo_texto(modal, entradas, "Stock mínimo:", "stock_minimo", p.get("stock_minimo", 5))
        
        self._agregar_combo(modal, entradas, "Marca:", "id_marca", marcas, p.get("id_marca"))
        self._agregar_combo(modal, entradas, "Categoría:", "id_categoria", categorias, p.get("id_categoria"))
        self._agregar_combo(modal, entradas, "Unidad:", "id_unidad", unidades, p.get("id_unidad"))
        self._agregar_combo(modal, entradas, "Proveedor:", "id_proveedor", proveedores, p.get("id_proveedor"))

        tk.Button(
            modal, text="GUARDAR", bg="#27AE60", fg="white", font=("Arial", 11, "bold"),
            command=lambda: self._procesar_guardado(modal, es_nuevo, producto, entradas)
        ).pack(pady=20, fill="x", padx=15)

    # --- DIVISIÓN DE LÓGICA PARA REDUCIR COMPLEJIDAD COGNITIVA ---

    def _parsear_entry(self, key, val):
        raw = val.strip()
        if key == "precio_venta":
            return float(raw) if raw else 0.0
        if key == "stock_minimo":
            return int(raw) if raw else 0
        return raw

    def _parsear_combo(self, info):
        idx = info[1].current()
        return info[2][idx]["id"] if idx >= 0 else None

    def _extraer_datos_formulario(self, entradas):
        datos = {}
        for key, info in entradas.items():
            if info[0] == "entry":
                datos[key] = self._parsear_entry(key, info[1].get())
            else:
                datos[key] = self._parsear_combo(info)
        return datos

    def _procesar_guardado(self, modal, es_nuevo, producto, entradas):
        try:
            datos = self._extraer_datos_formulario(entradas)
            
            if es_nuevo:
                ok, msg = self.controlador.crear_producto(datos)
            else:
                ok, msg = self.controlador.actualizar_producto(producto["id_producto"], datos)

            if ok:
                messagebox.showinfo(MSG_EXITO, msg)
                modal.destroy()
                self.notificar_filtros()
            else:
                messagebox.showerror(MSG_ERROR, msg)
        except ValueError:
            messagebox.showerror("Datos inválidos", "Revisa que el precio y el stock sean números válidos.")