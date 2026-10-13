import tkinter as tk
from tkinter import ttk, messagebox
from vistas import estilos


class PanelProveedores(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        # ------- Título -------
        frame_titulo = tk.Frame(self, bg="#3A8D96", height=40)
        frame_titulo.pack(fill="x")
        frame_titulo.pack_propagate(False)
        tk.Label(frame_titulo, text="  GESTIÓN DE PROVEEDORES",
                 bg="#3A8D96", fg="white",
                 font=("Arial", 11, "bold")).pack(side="left", padx=10)

        # ------- Formulario de alta -------
        form = tk.Frame(self, bg=estilos.FONDO)
        form.pack(pady=15)

        tk.Label(form, text="Nombre:", bg=estilos.FONDO).grid(row=0, column=0, padx=5)
        self.entry_nombre = tk.Entry(form, width=25)
        self.entry_nombre.grid(row=0, column=1, padx=5)

        tk.Label(form, text="Teléfono:", bg=estilos.FONDO).grid(row=0, column=2, padx=5)
        self.entry_tel = tk.Entry(form, width=15)
        self.entry_tel.grid(row=0, column=3, padx=5)

        tk.Label(form, text="Correo:", bg=estilos.FONDO).grid(row=0, column=4, padx=5)
        self.entry_correo = tk.Entry(form, width=25)
        self.entry_correo.grid(row=0, column=5, padx=5)

        tk.Button(form, text="AGREGAR", bg="#27AE60", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.agregar).grid(row=0, column=6, padx=10)

        # ------- Tabla -------
        cols = ("ID", "NOMBRE", "TELÉFONO", "CORREO")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for c in cols:
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="center", width=180)
        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)

        # ------- Botón eliminar -------
        tk.Button(self, text="❌ Eliminar seleccionado",
                  bg="#C0392B", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.eliminar).pack(pady=10)

        self.refrescar()

    def refrescar(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for p in self.controlador.obtener_proveedores():
            self.tabla.insert("", "end",
                              values=(p["id"], p["nombre"], p["telefono"], p["correo"]))

    def agregar(self):
        ok, msg = self.controlador.procesar_nuevo_proveedor(
            self.entry_nombre.get(),
            self.entry_tel.get(),
            self.entry_correo.get()
        )
        if ok:
            messagebox.showinfo("Éxito", msg)
            self.entry_nombre.delete(0, "end")
            self.entry_tel.delete(0, "end")
            self.entry_correo.delete(0, "end")
            self.refrescar()
        else:
            messagebox.showerror("Error", msg)

    def eliminar(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Selección", "Selecciona un proveedor de la tabla.")
            return
        id_prov = self.tabla.item(sel)["values"][0]
        nombre  = self.tabla.item(sel)["values"][1]

        if not messagebox.askyesno("Confirmar",
                                   f"¿Eliminar al proveedor '{nombre}'?\n"
                                   "Los productos asociados quedarán sin proveedor."):
            return

        self.controlador.procesar_eliminar_proveedor(id_prov)
        messagebox.showinfo("Éxito", f"Proveedor '{nombre}' eliminado.")
        self.refrescar()