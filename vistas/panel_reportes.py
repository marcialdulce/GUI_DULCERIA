import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from vistas import estilos

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
DIAS = ["Todos"] + [str(d) for d in range(1, 32)]


class PanelReportes(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        tk.Label(self, text="CENTRO DE ANÁLISIS FINANCIERO", bg="#3A8D96", fg="white", font=("Arial", 12, "bold")).pack(fill="x", pady=(5, 2))

        # --- BARRA GLOBAL DE FILTROS (AÑO / MES / DÍA / CAJA) ---
        frame_filtros = tk.Frame(self, bg="#FFFFFF", bd=1, relief="solid")
        frame_filtros.pack(fill="x", padx=10, pady=6)

        anios = ["Todos"] + self.controlador.obtener_anios_reportes()

        tk.Label(frame_filtros, text="Año:", bg="white", font=("Arial", 9, "bold")).pack(side="left", padx=(10, 4), pady=6)
        self.cmb_anio = ttk.Combobox(frame_filtros, values=anios, state="readonly", width=8)
        self.cmb_anio.set("Todos")
        self.cmb_anio.pack(side="left", padx=4)

        tk.Label(frame_filtros, text="Mes:", bg="white", font=("Arial", 9, "bold")).pack(side="left", padx=(10, 4))
        self.cmb_mes = ttk.Combobox(frame_filtros, values=MESES, state="readonly", width=15)
        self.cmb_mes.set("Todos")
        self.cmb_mes.pack(side="left", padx=4)

        tk.Label(frame_filtros, text="Día:", bg="white", font=("Arial", 9, "bold")).pack(side="left", padx=(10, 4))
        self.cmb_dia = ttk.Combobox(frame_filtros, values=DIAS, state="readonly", width=7)
        self.cmb_dia.set("Todos")
        self.cmb_dia.pack(side="left", padx=4)

        tk.Label(frame_filtros, text="Caja:", bg="white", font=("Arial", 9, "bold")).pack(side="left", padx=(10, 4))
        self.cmb_caja = ttk.Combobox(frame_filtros, values=["Todas", "CAJA-01", "CAJA-02", "CAJA-03", "CAJA-04"], state="readonly", width=10)
        self.cmb_caja.set("Todas")
        self.cmb_caja.pack(side="left", padx=4)

        tk.Button(
            frame_filtros, text="APLICAR FILTROS", bg="#27AE60", fg="white",
            font=("Arial", 9, "bold"), relief="flat", cursor="hand2", padx=12, pady=4,
            command=self.actualizar_todo,
        ).pack(side="right", padx=10, pady=4)

        # --- PESTAÑAS ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.tab_tabla = tk.Frame(self.notebook, bg=estilos.FONDO)
        self.tab_grafica = tk.Frame(self.notebook, bg="white")

        self.notebook.add(self.tab_tabla, text=" Resumen y Tabulador de Utilidades")
        self.notebook.add(self.tab_grafica, text=" Gráfica de Rendimiento por Caja")

        self._construir_tab_tabla()
        self._construir_tab_grafica()
        self.actualizar_todo()

    def _leer_filtros(self):
        anio_sel = self.cmb_anio.get()
        mes_sel = self.cmb_mes.get()
        dia_sel = self.cmb_dia.get()

        anio = int(anio_sel) if anio_sel != "Todos" else None
        mes = int(mes_sel.split(" - ")[0]) if mes_sel != "Todos" else None
        dia = int(dia_sel) if dia_sel != "Todos" else None
        caja = self.cmb_caja.get()
        return anio, mes, dia, caja

    def _construir_tab_tabla(self):
        # Fila 1 de KPIs financieros
        kpi_row1 = tk.Frame(self.tab_tabla, bg=estilos.FONDO)
        kpi_row1.pack(fill="x", padx=15, pady=(10, 4))

        self.lbl_ingreso = tk.Label(kpi_row1, text="Ingresos: $0.00", font=("Arial", 11, "bold"), fg="#27AE60", bg="white", relief="solid", bd=1, pady=6)
        self.lbl_ingreso.pack(side="left", padx=4, fill="x", expand=True)

        self.lbl_costo = tk.Label(kpi_row1, text="Costos: $0.00", font=("Arial", 11, "bold"), fg="#E74C3C", bg="white", relief="solid", bd=1, pady=6)
        self.lbl_costo.pack(side="left", padx=4, fill="x", expand=True)

        self.lbl_utilidad = tk.Label(kpi_row1, text="Ganancia Neta: $0.00", font=("Arial", 11, "bold"), fg="#2980B9", bg="white", relief="solid", bd=1, pady=6)
        self.lbl_utilidad.pack(side="left", padx=4, fill="x", expand=True)

        # Fila 2 de KPIs operativos (dulces vendidos, apartados, facturas, mermas)
        kpi_row2 = tk.Frame(self.tab_tabla, bg=estilos.FONDO)
        kpi_row2.pack(fill="x", padx=15, pady=(2, 8))

        self.lbl_dulces = tk.Label(kpi_row2, text="Dulces vendidos: 0", font=("Arial", 9, "bold"), fg="#4A2E35", bg="#FFFFFF", relief="solid", bd=1, pady=5)
        self.lbl_dulces.pack(side="left", padx=4, fill="x", expand=True)

        self.lbl_apartados = tk.Label(kpi_row2, text="Apartados: 0", font=("Arial", 9, "bold"), fg="#8E44AD", bg="#FFFFFF", relief="solid", bd=1, pady=5)
        self.lbl_apartados.pack(side="left", padx=4, fill="x", expand=True)

        self.lbl_extra = tk.Label(kpi_row2, text="Facturas: 0  |  Mermas: 0 uds", font=("Arial", 9, "bold"), fg="#555555", bg="#FFFFFF", relief="solid", bd=1, pady=5)
        self.lbl_extra.pack(side="left", padx=4, fill="x", expand=True)

        # Tabla de dulces vendidos en el periodo
        cols = ("PRODUCTO", "VENDIDOS", "INGRESOS", "COSTO UNIT.", "GANANCIA")
        self.tabla = ttk.Treeview(self.tab_tabla, columns=cols, show="headings", height=11)

        anchos = [300, 95, 115, 115, 115]
        for i, c in enumerate(cols):
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="w" if c == "PRODUCTO" else "center", width=anchos[i])

        self.tabla.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def _construir_tab_grafica(self):
        self.frame_canvas = tk.Frame(self.tab_grafica, bg="white")
        self.frame_canvas.pack(fill="both", expand=True, padx=15, pady=10)

    def actualizar_todo(self):
        anio, mes, dia, caja = self._leer_filtros()
        self.cargar_datos_tabla(anio, mes, dia)
        self.generar_grafica(anio, mes, dia, caja)

    def cargar_datos_tabla(self, anio=None, mes=None, dia=None):
        try:
            datos = self.controlador.obtener_reporte_ganancias(anio=anio, mes=mes, dia=dia)

            self.lbl_ingreso.config(text=f"Ingresos ({datos['num_ventas']} vtas): ${datos['ingreso_total']:,.2f}")
            self.lbl_costo.config(text=f"Costos: ${datos['costo_total']:,.2f}")
            self.lbl_utilidad.config(text=f"Ganancia Neta: ${datos['utilidad_bruta']:,.2f}")

            self.lbl_dulces.config(text=f"Dulces vendidos: {datos['dulces_vendidos']:,} uds")
            self.lbl_apartados.config(
                text=f"Apartados: {datos['num_apartados']} (P:{datos['apartados_pendientes']} L:{datos['apartados_liquidados']} C:{datos['apartados_cancelados']}) | Cobrado: ${datos['ingresos_apartados']:,.2f}"
            )
            self.lbl_extra.config(text=f"Facturas: {datos['num_facturas']}  |  Mermas: {datos['mermas_unidades']} uds")

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
            messagebox.showerror("Error", f"Fallo al cargar reporte: {e}")

    def generar_grafica(self, anio=None, mes=None, dia=None, caja="Todas"):
        for widget in self.frame_canvas.winfo_children():
            widget.destroy()

        datos = self.controlador.obtener_datos_grafica(anio=anio, mes=mes, dia=dia, caja=caja)
        if not datos:
            tk.Label(self.frame_canvas, text="No hay ventas registradas para el periodo seleccionado.", bg="white", font=("Arial", 13)).pack(pady=80)
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