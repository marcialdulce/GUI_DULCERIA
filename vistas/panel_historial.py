import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import vistas.estilos as estilos

# Acepta "2026", "2026-10" o "2026-10-18" (o vacío = todas las ventas)
PATRON_FECHA = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
INTERVALO_SONDEO_MS = 150


class PanelHistorial(tk.Frame):
  """Historial de ventas.

  La lectura del archivo y la generación de reportes NO se hacen aquí: las
  ejecutan hilos de segundo plano (servicios/tareas_ventas.py). Este panel solo
  dispara las tareas y, cada 150 ms, le pregunta al controlador cómo van para
  dibujar la barra de progreso y la tabla. Así la ventana sigue respondiendo.
  """

  def __init__(self, parent, controlador):
    super().__init__(parent)
    self.controlador = controlador
    self._after_id = None
    self._resumen_mostrado = None
    fondo = getattr(estilos, "FONDO", "#FFF5F5")
    self.config(bg=fondo)

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
    frame_filtros = tk.Frame(self, bg=fondo)
    frame_filtros.pack(fill="x", padx=20, pady=(15, 5))

    tk.Label(
        frame_filtros,
        text="Filtrar por fecha (AAAA-MM-DD, vacío = todas):",
        bg=fondo,
        font=("Arial", 9),
    ).pack(side="left", padx=5)

    self.entry_fecha = tk.Entry(frame_filtros, width=15)
    self.entry_fecha.pack(side="left", padx=5)
    self.entry_fecha.bind("<Return>", lambda e: self.filtrar_ventas())

    self.btn_buscar = tk.Button(
        frame_filtros,
        text="BUSCAR",
        bg="#F4D03F",
        font=("Arial", 9, "bold"),
        relief="flat",
        command=self.filtrar_ventas,
    )
    self.btn_buscar.pack(side="left", padx=10)

    self.btn_cancelar = tk.Button(
        frame_filtros,
        text="CANCELAR",
        bg="#E6B0AA",
        font=("Arial", 9, "bold"),
        relief="flat",
        state="disabled",
        command=self.cancelar_carga,
    )
    self.btn_cancelar.pack(side="left")

    # Barra de progreso + estado de la tarea en segundo plano
    frame_progreso = tk.Frame(self, bg=fondo)
    frame_progreso.pack(fill="x", padx=25, pady=(0, 5))

    self.barra = ttk.Progressbar(frame_progreso, orient="horizontal", mode="determinate", maximum=100)
    self.barra.pack(side="left", fill="x", expand=True)

    self.lbl_estado = tk.Label(
        frame_progreso, text="Sin datos cargados. Presiona BUSCAR.",
        bg=fondo, fg="#555555", font=("Arial", 9), width=48, anchor="w",
    )
    self.lbl_estado.pack(side="left", padx=10)

    # Tabla para mostrar los tickets registrados
    columnas = ("Folio", "Fecha / Hora", "Productos", "Total", "Método de Pago")
    self.tabla_historial = ttk.Treeview(
        self, columns=columnas, show="headings", height=12
    )

    anchos = {"Folio": 100, "Fecha / Hora": 150, "Productos": 380, "Total": 90, "Método de Pago": 140}
    for col in columnas:
      self.tabla_historial.heading(col, text=col)
      self.tabla_historial.column(
          col, width=anchos[col], anchor="w" if col == "Productos" else "center")

    self.tabla_historial.pack(fill="both", expand=True, padx=20, pady=5)

    # Resumen inferior
    frame_resumen = tk.Frame(self, bg=fondo)
    frame_resumen.pack(fill="x", padx=20, pady=(10, 5))

    self.lbl_total_ventas = tk.Label(
        frame_resumen,
        text="Total Registrado: $0.00",
        font=("Arial", 11, "bold"),
        bg=fondo,
        fg="#2E86C1",
    )
    self.lbl_total_ventas.pack(side="left", padx=5)

    self.lbl_detalle = tk.Label(frame_resumen, text="", font=("Arial", 9), bg=fondo, fg="#555555")
    self.lbl_detalle.pack(side="left", padx=15)

    # Exportar el reporte (también en segundo plano)
    frame_export = tk.Frame(self, bg=fondo)
    frame_export.pack(fill="x", padx=20, pady=(0, 15))

    tk.Label(frame_export, text="Carpeta de reportes:", bg=fondo, font=("Arial", 9)).pack(side="left", padx=5)
    self.entry_carpeta = tk.Entry(frame_export, width=35)
    self.entry_carpeta.insert(0, "reportes")
    self.entry_carpeta.pack(side="left", padx=5)

    tk.Button(
        frame_export, text="...", bg="#EAEAEA", relief="flat", width=3,
        command=self.elegir_carpeta,
    ).pack(side="left")

    self.btn_exportar = tk.Button(
        frame_export,
        text="EXPORTAR REPORTE (CSV)",
        bg="#F4D03F",
        font=("Arial", 9, "bold"),
        relief="flat",
        state="disabled",
        command=self.exportar_reporte,
    )
    self.btn_exportar.pack(side="left", padx=10)

    # Si el panel se destruye (cambio de pestaña) dejamos de sondear
    self.bind("<Destroy>", self._al_destruir)

    # Si ya había datos o una tarea corriendo al volver a esta pestaña, lo retomamos
    self._actualizar_vista()
    self._programar_sondeo()

  # ------------------------------------------------------------ acciones
  def filtrar_ventas(self):
    fecha = self.entry_fecha.get().strip()
    if fecha and not PATRON_FECHA.match(fecha):
      messagebox.showwarning(
          "Fecha no válida",
          "Escribe la fecha como AAAA-MM-DD (también sirve AAAA-MM o AAAA),\n"
          "o déjala vacía para ver todas las ventas.")
      return

    # Lanza el hilo y regresa de inmediato: la ventana NO se bloquea
    if not self.controlador.iniciar_carga_ventas(fecha):
      messagebox.showinfo("En proceso", "Ya hay una carga de ventas en curso.")
      return
    self._actualizar_vista()
    self._programar_sondeo()

  def cancelar_carga(self):
    self.controlador.cancelar_carga_ventas()
    self._actualizar_vista()

  def exportar_reporte(self):
    ok, mensaje = self.controlador.exportar_reporte(self.entry_carpeta.get())
    if not ok:
      messagebox.showinfo("Exportar reporte", mensaje)
      return
    self._actualizar_vista()
    self._programar_sondeo()

  def elegir_carpeta(self):
    carpeta = filedialog.askdirectory(title="Carpeta donde guardar los reportes")
    if carpeta:
      self.entry_carpeta.delete(0, "end")
      self.entry_carpeta.insert(0, carpeta)

  # ------------------------------------------------------------- sondeo
  def _programar_sondeo(self):
    """Arranca el ciclo after() si hay algo en marcha y no hay uno activo."""
    if self._after_id is None and self.controlador.hay_tareas_activas():
      self._after_id = self.after(INTERVALO_SONDEO_MS, self._sondear)

  def _sondear(self):
    self._after_id = None
    self.controlador.sondear_tareas()
    self._actualizar_vista()
    self._programar_sondeo()

  def _al_destruir(self, event=None):
    if event is None or event.widget is self:
      if self._after_id is not None:
        try:
          self.after_cancel(self._after_id)
        except tk.TclError:
          pass
        self._after_id = None

  # ------------------------------------------------------------- dibujo
  def _actualizar_vista(self):
    c = self.controlador
    estado = c.estado_carga["estado"]
    cargando = estado in ("cargando", "cancelando")

    self.btn_buscar.config(state="disabled" if cargando else "normal")
    self.btn_cancelar.config(state="normal" if estado == "cargando" else "disabled")
    self.btn_exportar.config(
        state="normal" if (c.resumen_ventas is not None and c.estado_export["estado"] != "guardando")
        else "disabled")

    self.barra["value"] = c.estado_carga["porcentaje"]

    if estado == "cargando":
      self._estado(f"Leyendo ventas... {c.estado_carga['porcentaje']:.0f}% "
                   f"({c.estado_carga['leidas']:,} registros)", "#555555")
    elif estado == "cancelando":
      self._estado("Cancelando...", "#B9770E")
    elif estado == "cancelado":
      self._estado("Carga cancelada.", "#B9770E")
    elif estado == "error":
      self._estado("Error al cargar las ventas.", "red")
    elif estado == "terminado" and c.resumen_ventas is not None:
      self._estado(f"Listo: {c.resumen_ventas.ventas:,} ventas en {c.resumen_ventas.segundos:.1f} s", "green")

    if c.estado_export["estado"] == "guardando":
      self._estado("Guardando reporte...", "#555555")

    # Dibujar la tabla solo cuando llega un resultado nuevo
    if c.resumen_ventas is not None and c.resumen_ventas is not self._resumen_mostrado:
      self._resumen_mostrado = c.resumen_ventas
      self._llenar(c.resumen_ventas)

    for nivel, titulo, texto in c.tomar_notificaciones():
      (messagebox.showerror if nivel == "error" else messagebox.showinfo)(titulo, texto)

  def _estado(self, texto, color):
    self.lbl_estado.config(text=texto, fg=color)

  def _llenar(self, resumen):
    for fila in self.tabla_historial.get_children():
      self.tabla_historial.delete(fila)

    # Solo las últimas ventas: meter cientos de miles de filas congelaría la tabla
    for venta in reversed(resumen.ultimas):
      productos = ", ".join(f"{a['producto']} x{a['cantidad']}" for a in venta["articulos"])
      self.tabla_historial.insert("", "end", values=(
          venta.get("folio", "—"), venta["fecha"], productos,
          f"${float(venta['total']):.2f}", venta["metodo_pago"]))

    self.lbl_total_ventas.config(text=f"Total Registrado: ${resumen.ingreso_total:,.2f}")

    partes = [f"{resumen.ventas:,} ventas", f"ticket promedio ${resumen.ticket_promedio:,.2f}"]
    top = resumen.producto_mas_vendido()
    if top:
      partes.append(f"más vendido: {top[0]} ({top[1]:,} uds)")
    if resumen.ventas > len(resumen.ultimas):
      partes.append(f"tabla: últimas {len(resumen.ultimas)}")
    if resumen.lineas_invalidas:
      partes.append(f"{resumen.lineas_invalidas:,} líneas ignoradas")
    self.lbl_detalle.config(text="  |  ".join(partes))
