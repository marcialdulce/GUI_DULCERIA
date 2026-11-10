import tkinter as tk
from tkinter import ttk
from vistas import estilos

class PanelReportes(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        tk.Label(self, text="REPORTE FINANCIERO Y GANANCIAS", bg=estilos.FONDO, fg="#4A2E35", font=("Arial", 18, "bold")).pack(pady=15)

        # Tarjetas de totales
        frame_totales = tk.Frame(self, bg=estilos.FONDO)
        frame_totales.pack(fill="x", padx=50, pady=10)

        self.lbl_ingreso = self._crear_tarjeta(frame_totales, "Ingresos Totales", "$0.00", "#27AE60")
        self.lbl_costo = self._crear_tarjeta(frame_totales, "Costos de Adquisición", "$0.00", "#E74C3C")
        self.lbl_utilidad = self._crear_tarjeta(frame_totales, "Utilidad Bruta", "$0.00", "#2980B9")

        # Tabla de productos
        frame_tabla = tk.Frame(self, bg=estilos.FONDO)
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("PRODUCTO", "VENDIDOS", "INGRESOS", "COSTO UNIT.", "GANANCIA")
        self.tabla = ttk.Treeview(frame_tabla, columns=cols, show="headings")
        for c in cols:
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="center", width=120)
        self.tabla.pack(fill="both", expand=True)

        tk.Button(self, text="ACTUALIZAR DATOS", bg="#3A8D96", fg="white", font=("Arial", 10, "bold"), command=self.cargar_datos).pack(pady=15)
        self.cargar_datos()

    def _crear_tarjeta(self, parent, titulo, valor_inicial, color):
        frame = tk.Frame(parent, bg="white", bd=1, relief="solid")
        frame.pack(side="left", fill="both", expand=True, padx=10)
        tk.Label(frame, text=titulo, bg="white", fg="#555", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        lbl = tk.Label(frame, text=valor_inicial, bg="white", fg=color, font=("Arial", 16, "bold"))
        lbl.pack(pady=(0, 10))
        return lbl

    def cargar_datos(self):
        datos = self.controlador.obtener_reporte_ganancias()
        
        self.lbl_ingreso.config(text=f"${datos['ingreso_total']:,.2f}")
        self.lbl_costo.config(text=f"${datos['costo_total']:,.2f}")
        self.lbl_utilidad.config(text=f"${datos['utilidad_bruta']:,.2f}")

        for row in self.tabla.get_children():
            self.tabla.delete(row)

        for p in datos["detalle"]:
            ganancia = float(p["ganancia_neta"])
            color_tag = "positivo" if ganancia >= 0 else "negativo"
            self.tabla.insert("", "end", values=(
                p["nombre_dulce"], p["unidades_vendidas"], 
                f"${float(p['ingresos_totales']):.2f}", f"${float(p['costo_unitario']):.2f}",
                f"${ganancia:.2f}"
            ), tags=(color_tag,))
        
        self.tabla.tag_configure("positivo", foreground="green")
        self.tabla.tag_configure("negativo", foreground="red")