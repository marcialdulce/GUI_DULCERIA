import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from vistas import estilos

class PanelReportes(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        tk.Label(self, text="CENTRO DE ANÁLISIS FINANCIERO", bg="#3A8D96", fg="white", font=("Arial", 12, "bold")).pack(fill="x", pady=5)

        # Crear sistema de pestañas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Crear las dos ventanas para las pestañas
        self.tab_grafica = tk.Frame(self.notebook, bg="white")
        self.tab_tabla = tk.Frame(self.notebook, bg=estilos.FONDO)

        self.notebook.add(self.tab_grafica, text=" Gráfica de Rendimiento")
        self.notebook.add(self.tab_tabla, text=" Tabulador de Utilidades")

        self.construir_pestaña_grafica()
        self.construir_pestaña_tabla()

    def construir_pestaña_grafica(self):
        # --- BARRA DE FILTROS PARA GRÁFICA ---
        frame_filtros = tk.Frame(self.tab_grafica, bg="white")
        frame_filtros.pack(pady=10)
        
        tk.Label(frame_filtros, text="Mes (1-12):", bg="white", font=("Arial", 10, "bold")).pack(side="left")
        self.e_mes = tk.Entry(frame_filtros, width=5, highlightthickness=1, highlightbackground="gray")
        self.e_mes.pack(side="left", padx=5)
        
        tk.Label(frame_filtros, text="Caja:", bg="white", font=("Arial", 10, "bold")).pack(side="left", padx=(15,0))
        self.cmb_caja = ttk.Combobox(frame_filtros, values=["Todas", "CAJA-01", "CAJA-02", "CAJA-03", "CAJA-04"], state="readonly", width=12)
        self.cmb_caja.set("Todas")
        self.cmb_caja.pack(side="left", padx=5)

        tk.Button(frame_filtros, text="ACTUALIZAR GRÁFICA", bg="#27AE60", fg="white", font=("Arial", 9, "bold"), command=self.generar_grafica).pack(side="left", padx=20)

        # --- CONTENEDOR DE LA GRÁFICA ---
        self.frame_canvas = tk.Frame(self.tab_grafica, bg="white")
        self.frame_canvas.pack(fill="both", expand=True, padx=20, pady=10)

        self.generar_grafica()

    def generar_grafica(self):
        for widget in self.frame_canvas.winfo_children():
            widget.destroy()

        mes = self.e_mes.get().strip() or None
        caja = self.cmb_caja.get()
        datos = self.controlador.modelo.obtener_datos_grafica(mes, caja)

        if not datos:
            tk.Label(self.frame_canvas, text="No hay ventas registradas con estos filtros.", bg="white", font=("Arial", 14)).pack(pady=100)
            return

        cajas = [d["numero_caja"] for d in datos]
        ingresos = [float(d["ingresos_totales"]) for d in datos]

        figura = Figure(figsize=(8, 5), dpi=100)
        ax = figura.add_subplot(111)
        
        colores = ['#2980B9', '#27AE60', '#F39C12', '#E74C3C']
        barras = ax.bar(cajas, ingresos, color=colores[:len(cajas)], edgecolor='black', width=0.6)
        
        ax.set_title("Rendimiento e Ingresos por Caja", fontsize=16, fontweight='bold', pad=15)
        ax.set_ylabel("Total Vendido ($)", fontsize=12)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        for barra in barras:
            altura = barra.get_height()
            ax.text(barra.get_x() + barra.get_width()/2., altura + (max(ingresos)*0.01), 
                    f'${altura:,.2f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

        canvas = FigureCanvasTkAgg(figura, master=self.frame_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, anchor="center")

    def construir_pestaña_tabla(self):
        # --- RECUADROS FINANCIEROS GLOBALES ---
        frame_kpis = tk.Frame(self.tab_tabla, bg=estilos.FONDO)
        frame_kpis.pack(fill="x", pady=15, padx=20)
        
        self.lbl_ingreso = tk.Label(frame_kpis, text="$0.00", font=("Arial", 20, "bold"), fg="#27AE60", bg="white", width=15, relief="solid", bd=1)
        self.lbl_ingreso.pack(side="left", padx=10, expand=True)
        
        self.lbl_costo = tk.Label(frame_kpis, text="$0.00", font=("Arial", 20, "bold"), fg="#E74C3C", bg="white", width=15, relief="solid", bd=1)
        self.lbl_costo.pack(side="left", padx=10, expand=True)
        
        self.lbl_utilidad = tk.Label(frame_kpis, text="$0.00", font=("Arial", 20, "bold"), fg="#2980B9", bg="white", width=15, relief="solid", bd=1)
        self.lbl_utilidad.pack(side="left", padx=10, expand=True)

        # --- TABLA DE DESGLOSE POR PRODUCTO ---
        cols = ("PRODUCTO", "VENDIDOS", "INGRESOS", "COSTO UNIT.", "GANANCIA")
        self.tabla = ttk.Treeview(self.tab_tabla, columns=cols, show="headings", height=12)
        
        anchos = [300, 100, 120, 120, 120]
        for i, c in enumerate(cols):
            self.tabla.heading(c, text=c)
            self.tabla.column(c, anchor="center", width=anchos[i])
            
        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Button(self.tab_tabla, text="ACTUALIZAR TABLA", bg="#3A8D96", fg="white", font=("Arial", 10, "bold"), command=self.cargar_datos_tabla).pack(pady=10)
        
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
                    f"${float(p['ganancia_neta']):,.2f}"
                ))
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Fallo al cargar datos: {e}")
            
        
    