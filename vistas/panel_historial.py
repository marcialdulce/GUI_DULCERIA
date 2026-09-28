import tkinter as tk
from tkinter import ttk, messagebox
import vistas.estilos as estilos


class PanelHistorial(tk.Frame):

  def __init__(self, parent, controlador):
    super().__init__(parent)
    self.controlador = controlador
    self.config(bg=getattr(estilos, "FONDO", "#FFF5F5"))

    # Cabecera limpia y unificada (igual al estilo general)
    frame_titulo = tk.Frame(self, bg="#3A8D96", height=40)
    frame_titulo.pack(fill="x")
    frame_titulo.pack_propagate(False)

    tk.Label(
        frame_titulo,
        text="  HISTORIAL DE VENTAS",
        bg="#3A8D96",
        fg="white",
        font=("Arial", 11, "bold"),
    ).pack(side="left", padx=10)

    # Barra superior de filtros
    frame_filtros = tk.Frame(self, bg=getattr(estilos, "FONDO", "#FFF5F5"))
    frame_filtros.pack(fill="x", padx=20, pady=15)

    tk.Label(
        frame_filtros,
        text="Filtrar por fecha (AAAA-MM-DD):",
        bg=getattr(estilos, "FONDO", "#FFF5F5"),
        font=("Arial", 9),
    ).pack(side="left", padx=5)

    self.entry_fecha = tk.Entry(frame_filtros, width=15)
    self.entry_fecha.pack(side="left", padx=5)

    tk.Button(
        frame_filtros,
        text="BUSCAR",
        bg="#F4D03F",
        font=("Arial", 9, "bold"),
        relief="flat",
        command=self.filtrar_ventas,
    ).pack(side="left", padx=10)

    # Tabla para mostrar los tickets registrados
    columnas = ("Folio", "Fecha / Hora", "Productos", "Total", "Método de Pago")
    self.tabla_historial = ttk.Treeview(
        self, columns=columnas, show="headings", height=12
    )

    for col in columnas:
      self.tabla_historial.heading(col, text=col)
      self.tabla_historial.column(col, width=140, anchor="center")

    self.tabla_historial.pack(fill="both", expand=True, padx=20, pady=5)

    # Resumen inferior
    frame_resumen = tk.Frame(self, bg=getattr(estilos, "FONDO", "#FFF5F5"))
    frame_resumen.pack(fill="x", padx=20, pady=15)

    self.lbl_total_ventas = tk.Label(
        frame_resumen,
        text="Total Registrado: $0.00",
        font=("Arial", 11, "bold"),
        bg=getattr(estilos, "FONDO", "#FFF5F5"),
        fg="#2E86C1",
    )
    self.lbl_total_ventas.pack(side="left", padx=5)

  def filtrar_ventas(self):
    fecha = self.entry_fecha.get()
    messagebox.showinfo("Filtro", f"Buscando ventas del día: {fecha}")