import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class PanelApartados(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg="#F9F4F0")
        self.controlador = controlador

        titulo = tk.Frame(self, bg="#2D929A", height=35)
        titulo.pack(fill="x", side="top")
        titulo.pack_propagate(False)
        tk.Label(titulo, text="CONTROL DE APARTADOS", bg="#2D929A", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=15)

        frame_botones = tk.Frame(self, bg="#F9F4F0")
        frame_botones.pack(fill="x", padx=15, pady=10)
        
        tk.Button(frame_botones, text="+ NUEVO APARTADO", bg="#27AE60", fg="white", 
                  font=("Arial", 9, "bold"), command=self.abrir_nuevo_apartado).pack(side="left")
        tk.Button(frame_botones, text="❌ CANCELAR APARTADO SELECCIONADO", bg="#C0392B", fg="white", 
                  font=("Arial", 9, "bold"), command=self.cancelar_apartado).pack(side="right")

        frame_tabla = tk.Frame(self, bg="#F9F4F0")
        frame_tabla.pack(fill="both", expand=True, padx=15, pady=10)
        
        cols = ("ID", "CLIENTE", "PRODUCTO", "UNIDADES", "FECHA ENTREGA", "ESTADO")
        self.tabla = ttk.Treeview(frame_tabla, columns=cols, show="headings")
        for c in cols:
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="center", width=120)
        self.tabla.pack(fill="both", expand=True)
        
        self.cargar_tabla()

    def cargar_tabla(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for item in self.controlador.obtener_lista_apartados():
            self.tabla.insert("", "end", values=(
                item["id_apartado"], item["nombre"], item["producto"], 
                item["unidades"], item["fecha"], item["estado"]
            ))

    def cancelar_apartado(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Selección", "Selecciona un apartado de la tabla.")
            return
        
        # FIX: Extraer el primer elemento de la tupla
        item = self.tabla.item(sel[0])
        id_apartado = item["values"][0]
        estado = item["values"][5]

        if estado == "cancelado":
            messagebox.showinfo("Info", "Este apartado ya está cancelado.")
            return

        confirmacion = messagebox.askyesno(
            "Cancelar Apartado - Política Estricta", 
            " ADVERTENCIA:\n\nPor políticas de la dulcería, si cancelas este apartado, el anticipo entregado NO ES REEMBOLSABLE bajo ninguna circunstancia.\n\n¿Deseas continuar con la cancelación?"
        )
        
        if confirmacion:
            self.controlador.cancelar_apartado(id_apartado)
            messagebox.showinfo("Cancelado", "El apartado ha sido cancelado y el anticipo retenido.")
            self.cargar_tabla()

    def abrir_nuevo_apartado(self):
        modal = tk.Toplevel(self)
        modal.title("Registrar Nuevo Apartado")
        
        # Centrar ventana
        ancho, alto = 400, 520
        x = (modal.winfo_screenwidth() // 2) - (ancho // 2)
        y = (modal.winfo_screenheight() // 2) - (alto // 2)
        modal.geometry(f"{ancho}x{alto}+{x}+{y}")
        
        modal.config(bg="#F9F4F0")
        modal.grab_set()

        tk.Label(modal, text="NOMBRE DEL CLIENTE:", bg="#F9F4F0").pack(pady=(15, 5))
        entry_nombre = tk.Entry(modal, width=30)
        entry_nombre.pack()

        tk.Label(modal, text="TELÉFONO:", bg="#F9F4F0").pack(pady=5)
        entry_tel = tk.Entry(modal, width=30)
        entry_tel.pack()

        tk.Label(modal, text="FECHA DE ENTREGA (AAAA-MM-DD):", bg="#F9F4F0").pack(pady=5)
        entry_fecha = tk.Entry(modal, width=30)
        entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        entry_fecha.pack()

        tk.Label(modal, text="PRODUCTO (Solo con stock):", bg="#F9F4F0").pack(pady=5)
        productos = self.controlador.obtener_nombres_productos()
        combo_prod = ttk.Combobox(modal, values=productos, width=28, state="readonly")
        combo_prod.pack()

        tk.Label(modal, text="CANTIDAD:", bg="#F9F4F0").pack(pady=5)
        entry_cant = tk.Entry(modal, width=30)
        entry_cant.pack()

        tk.Label(modal, text="MÉTODO DE PAGO DEL ANTICIPO:", bg="#F9F4F0").pack(pady=5)
        combo_metodo = ttk.Combobox(modal, values=["Efectivo", "Tarjeta de débito", "Tarjeta de crédito"], width=28, state="readonly")
        combo_metodo.current(0)
        combo_metodo.pack()

        tk.Label(modal, text="(El sistema cobrará un anticipo del 50% obligatorio)", fg="red", bg="#F9F4F0", font=("Arial", 9, "italic")).pack(pady=15)

        def guardar():
            exito, mensaje = self.controlador.registrar_apartado(
                entry_nombre.get().strip(), entry_tel.get().strip(), entry_fecha.get().strip(),
                combo_prod.get(), entry_cant.get(), combo_metodo.get()
            )
            if exito:
                messagebox.showinfo("Éxito", mensaje)
                modal.destroy()
                self.cargar_tabla()
            else:
                messagebox.showerror("Error", mensaje)

        tk.Button(modal, text="COBRAR ANTICIPO Y GUARDAR", bg="#27AE60", fg="white", font=("Arial", 10, "bold"), command=guardar).pack(pady=15)