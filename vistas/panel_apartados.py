# ============================================================
# PANEL DE APARTADOS
# HILO 5 - GESTIÓN DE APARTADOS PENDIENTES
# ============================================================

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from servicios.hilo_apartados import HiloApartados


class PanelApartados(tk.Frame):

    def __init__(self, parent, controlador):
        super().__init__(parent, bg="#F9F4F0")
        self.controlador = controlador

        # Datos de prueba o desde el controlador
        if (
            hasattr(self.controlador, "apartados")
            and self.controlador.apartados
        ):
            self.apartados = self.controlador.apartados
        else:
            self.apartados = [
                {
                    "producto": "Gomitas",
                    "nombre": "Ana López",
                    "fecha": "21/10/2026",
                    "precio": "$15.00",
                    "unidades": 2,
                    "estado": "Pendiente",
                },
                {
                    "producto": "Chocolate",
                    "nombre": "Luis Pérez",
                    "fecha": "23/10/2026",
                    "precio": "$12.00",
                    "unidades": 4,
                    "estado": "Pendiente",
                },
                {
                    "producto": "Panditas",
                    "nombre": "María Ruiz",
                    "fecha": "30/10/2026",
                    "precio": "$20.00",
                    "unidades": 1,
                    "estado": "Pendiente",
                },
            ]

        self.lock = threading.Lock()
        self.cola_resultados = queue.Queue()
        self.hilo = None

        self.crear_interfaz()

    def crear_interfaz(self):
        # TÍTULO
        titulo = tk.Frame(self, bg="#2D929A", height=35)
        titulo.pack(fill="x", side="top")
        titulo.pack_propagate(False)

        tk.Label(
            titulo,
            text="CONTROL DE APARTADOS",
            bg="#2D929A",
            fg="white",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=15)

        # SUBTÍTULO
        subtitulo = tk.Frame(self, bg="#F9F4F0")
        subtitulo.pack(fill="x", padx=15, pady=(10, 0))

        tk.Label(
            subtitulo,
            text="Revisión de fechas límite (aviso con 3 días de anticipación)",
            bg="#F9F4F0",
            fg="#555555",
            font=("Arial", 9),
        ).pack(side="left")

        self.boton_revisar = tk.Button(
            subtitulo,
            text="Revisar apartados",
            bg="#2D929A",
            fg="white",
            font=("Arial", 9),
            relief="flat",
            padx=12,
            pady=5,
            command=self.iniciar_hilo,
        )
        self.boton_revisar.pack(side="right")

        # TABLA DE APARTADOS
        frame_tabla = tk.Frame(self, bg="#F9F4F0")
        frame_tabla.pack(fill="both", expand=True, padx=15, pady=10)

        columnas = (
            "producto",
            "nombre",
            "fecha",
            "precio",
            "unidades",
            "estado",
        )
        self.tabla = ttk.Treeview(
            frame_tabla, columns=columnas, show="headings"
        )

        self.tabla.heading("producto", text="PRODUCTO")
        self.tabla.heading("nombre", text="NOMBRE")
        self.tabla.heading("fecha", text="FECHA DE ENTREGA")
        self.tabla.heading("precio", text="PRECIO")
        self.tabla.heading("unidades", text="UNIDADES APARTADAS")
        self.tabla.heading("estado", text="ESTADO")

        self.tabla.column("producto", width=180, anchor="center")
        self.tabla.column("nombre", width=200, anchor="center")
        self.tabla.column("fecha", width=180, anchor="center")
        self.tabla.column("precio", width=120, anchor="center")
        self.tabla.column("unidades", width=180, anchor="center")
        self.tabla.column("estado", width=140, anchor="center")

        self.tabla.pack(fill="both", expand=True)

        self.cargar_tabla()

    def cargar_tabla(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)

        for item in self.apartados:
            self.tabla.insert(
                "",
                "end",
                values=(
                    item.get("producto", ""),
                    item.get("nombre", ""),
                    item.get("fecha", ""),
                    item.get("precio", ""),
                    item.get("unidades", ""),
                    item.get("estado", "Pendiente"),
                ),
            )

    def iniciar_hilo(self):
        if self.hilo is not None and self.hilo.is_alive():
            return

        self.boton_revisar.config(state="disabled")

        # Usamos la clase HiloApartados importada desde servicios.hilo_apartados
        self.hilo = HiloApartados(
            apartados=self.apartados,
            bloqueo=self.lock,
            cola_resultados=self.cola_resultados,
            dias_aviso=3,
        )
        self.hilo.start()

        # Sonda periódica mediante after() para revisar cuando haya resultados
        self.verificar_cola()

    def verificar_cola(self):
        try:
            # Intenta sacar resultado de la cola enviada por HiloApartados
            res = self.cola_resultados.get_nowait()
            self.boton_revisar.config(state="normal")

            if res.get("ok"):
                avisos = res.get("avisos", [])
                if avisos:
                    lineas = [a["mensaje"] for a in avisos]
                    texto_mensaje = "\n".join(lineas)
                    messagebox.showwarning("Avisos de apartados", texto_mensaje)
                else:
                    messagebox.showinfo(
                        "Avisos de apartados",
                        "No hay apartados próximos a vencer ni vencidos.",
                    )
            else:
                messagebox.showerror(
                    "Error", f"Ocurrió un error en el hilo: {res.get('error')}"
                )

        except queue.Empty:
            # Si el hilo sigue trabajando, volvemos a checar en 100 ms
            self.after(100, self.verificar_cola)