import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos

class PanelInventario(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO) 
        self.controlador = controlador

        barra = tk.Frame(self, bg="#3A8D96", height=40); barra.pack(fill="x", pady=10)
        
        tk.Label(barra, text="BUSCAR:", bg="#3A8D96", fg="white").pack(side="left", padx=5)
        self.txt_buscar = tk.Entry(barra); self.txt_buscar.pack(side="left")
        self.txt_buscar.bind("<KeyRelease>", lambda e: self.notificar_filtros())

        tk.Button(barra, text=" REGISTRAR MERMA", bg="#E74C3C", fg="white", command=self.abrir_merma).pack(side="right", padx=10)

        columnas = ("ID", "PRODUCTO", "PRECIO", "STOCK", "ESTADO")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings")
        for c in columnas: self.tabla.heading(c, text=c); self.tabla.column(c, anchor="center")
        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.notificar_filtros()

    def notificar_filtros(self):
        datos = self.controlador.obtener_inventario_filtrado(self.txt_buscar.get().lower(), "Todas", "Todas")
        for f in self.tabla.get_children(): self.tabla.delete(f)
        for p in datos:
            self.tabla.insert("", "end", values=(p["id_producto"], p["nombre"], f"${p['precio']:.2f}", p["stock"], "AGOTADO" if p["stock"]==0 else "OK"))

    def abrir_merma(self):
        sel = self.tabla.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecciona un producto de la tabla.")
        
        item = self.tabla.item(sel[0])["values"]
        id_prod = item[0]
        nombre = item[1]
        
        cant = tk.simpledialog.askinteger("Merma", f"¿Cuántas unidades de '{nombre}' se perdieron/dañaron?")
        if cant and cant > 0:
            exito, msg = self.controlador.registrar_merma(id_prod, cant, "Merma manual")
            if exito:
                messagebox.showinfo("Éxito", msg)
                self.notificar_filtros()
            else:
                messagebox.showerror("Error", msg)