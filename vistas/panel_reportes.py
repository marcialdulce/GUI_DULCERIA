import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from vistas import estilos

TEXTO_INICIAL_KPI = "$0.00"
MESES = [
    "Todos",
    "1 - Enero",
    "2 - Febrero",
    "3 - Marzo",
    "4 - Abril",
    "5 - Mayo",
    "6 - Junio",
    "7 - Julio",
    "8 - Agosto",
    "9 - Septiembre",
    "10 - Octubre",
    "11 - Noviembre",
    "12 - Diciembre",
]


class PanelReportes(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        tk.Label(self, text="CENTRO DE ANÁLISIS FINANCIERO", bg="#3A8D96", fg="white", font=("Arial", 12, "bold")).pack(fill="x", pady=5)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_grafica = tk.Frame(self.notebook, bg="white")
        self.tab_tabla = tk.Frame(self.notebook, bg=estilos.FONDO)

        self.notebook.add(self.tab_grafica, text=" Gráfica de Rendimiento")
        self.notebook.add(self.tab_tabla, text=" Tabulador de Utilidades")

        self.construir_pestaña_grafica()
        self.construir_pestaña_tabla()

    def construir_pestaña_grafica(self):
        frame_filtros = tk.Frame(self.tab_grafica, bg="white")
        frame_filtros.pack(pady=10)

        tk.Label(frame_filtros, text="Mes:", bg="white", font=("Arial", 10, "bold")).pack(side="left")
        self.cmb_mes = ttk.Combobox(frame_filtros, values=MESES, state="readonly", width=16)
        self.cmb_mes.set("Todos")
        self.cmb_mes.pack(side="left", padx=5)

        tk.Label(frame_filtros, text="Caja:", bg="white", font=("Arial", 10, "bold")).pack(side="left", padx=(15, 0))
        self.cmb_caja = ttk.Combobox(frame_filtros, values=["Todas", "CAJA-01", "CAJA-02", "CAJA-03", "CAJA-04"], state="readonly", width=12)
        self.cmb_caja.set("Todas")
        self.cmb_caja.pack(side="left", padx=5)

        tk.Button(
            frame_filtros, text="ACTUALIZAR GRÁFICA", bg="#27AE60", fg="white",
            font=("Arial", 9, "bold"), relief="flat", cursor="hand2", padx=10, pady=4,
            command=self.generar_grafica,
        ).pack(side="left", padx=15)

        self.frame_canvas = tk.Frame(self.tab_grafica, bg="white")
        self.frame_canvas.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.generar_grafica()

    def generar_grafica(self):
        for widget in self.frame_canvas.winfo_children():
            widget.destroy()

        mes_sel = self.cmb_mes.get()
        mes = int(mes_sel.split(" - ")[0]) if mes_sel != "Todos" else None
        caja = self.cmb_caja.get()
        datos = self.controlador.modelo.obtener_datos_grafica(mes, caja)

        if not datos:
            tk.Label(self.frame_canvas, text="No hay ventas registradas con estos filtros.", bg="white", font=("Arial", 13)).pack(pady=80)
            return

        cajas = [d["numero_caja"] for d in datos]
        ingresos = [float(d["ingresos_totales"]) for d in datos]
        max_ingreso = max(ingresos) if ingresos else 1.0

        figura = Figure(figsize=(6.8, 3.8), dpi=95)
        ax = figura.add_subplot(111)

        colores = ["#2980B9", "#27AE60", "#F39C12", "#E74C3C"]
        barras = ax.bar(cajas, ingresos, color=colores[:len(cajas)], edgecolor="black", width=0.55)

        ax.set_title("Rendimiento e Ingresos por Caja", fontsize=13, fontweight="bold", pad=12)
        ax.set_ylabel("Total Vendido ($)", fontsize=10)
        ax.set_xlabel("Caja", fontsize=10)
        ax.set_ylim(0, max_ingreso * 1.18)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        for barra in barras:
            altura = barra.get_height()
            ax.text(
                barra.get_x() + barra.get_width() / 2.0,
                altura + (max_ingreso * 0.02),
                f"${altura:,.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

        figura.tight_layout()

        canvas = FigureCanvasTkAgg(figura, master=self.frame_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def construir_pestaña_tabla(self):
        frame_kpis = tk.Frame(self.tab_tabla, bg=estilos.FONDO)
        frame_kpis.pack(fill="x", pady=15, padx=20)

        self.lbl_ingreso = tk.Label(frame_kpis, text=TEXTO_INICIAL_KPI, font=("Arial", 14, "bold"), fg="#27AE60", bg="white", relief="solid", bd=1, pady=8)
        self.lbl_ingreso.pack(side="left", padx=8, fill="x", expand=True)

        self.lbl_costo = tk.Label(frame_kpis, text=TEXTO_INICIAL_KPI, font=("Arial", 14, "bold"), fg="#E74C3C", bg="white", relief="solid", bd=1, pady=8)
        self.lbl_costo.pack(side="left", padx=8, fill="x", expand=True)

        self.lbl_utilidad = tk.Label(frame_kpis, text=TEXTO_INICIAL_KPI, font=("Arial", 14, "bold"), fg="#2980B9", bg="white", relief="solid", bd=1, pady=8)
        self.lbl_utilidad.pack(side="left", padx=8, fill="x", expand=True)

        cols = ("PRODUCTO", "VENDIDOS", "INGRESOS", "COSTO UNIT.", "GANANCIA")
        self.tabla = ttk.Treeview(self.tab_tabla, columns=cols, show="headings", height=12)

        anchos = [300, 100, 120, 120, 120]
        for i, c in enumerate(cols):
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="w" if c == "PRODUCTO" else "center", width=anchos[i])

        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Button(
            self.tab_tabla, text="ACTUALIZAR TABLA", bg="#3A8D96", fg="white",
            font=("Arial", 10, "bold"), relief="flat", cursor="hand2", padx=12, pady=5,
            command=self.cargar_datos_tabla,
        ).pack(pady=10)

        self.cargar_datos_tabla()

    def cargar_datos_tabla(self):
        try:
            datos = self.controlador.obtener_reporte_ganancias()

            self.lbl_ingreso.config(text=f"Ingresos: ${datos['ingreso_total']:,.2f}")
            self.lbl_costo.config(text=f"Costos: ${datos['costo_total']:,.2f}")
            self.lbl_utilidad.config(text=f"Utilidad: ${datos['utilidad_bruta']:,.2f}")

            for row in self.tabla.get_children():
                self.tabla.delete(row)

            for p in datos["detalle"]:
                self.tabla.insert("", "end", values=(
                    p["nombre_dulce"],
                    p["unidades_vendidas"],
                    f"${float(p['ingresos_totales']):,.2f}",
                    f"${float(p['costo_unitario']):,.2f}",
                    f"${float(p['ganancia_neta']):,.2f}",
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al cargar datos: {e}")