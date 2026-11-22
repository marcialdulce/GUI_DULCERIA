import tkinter as tk
from tkinter import messagebox
from vistas import estilos


def _construir_resumen_turno(contenedor, resumen, mostrar_esperado=True):
    filas = [
        ("Usuario / Rol:", f"{resumen['usuario']} ({resumen['rol']})"),
        ("Caja / Turno:", f"{resumen['numero_caja']}  (Corte #{resumen['id_corte_caja']})"),
        ("Inicio de turno:", resumen["inicio"]),
        ("Hora de cierre:", resumen["fin"]),
        ("Tiempo trabajado:", resumen["duracion"]),
        ("Fondo inicial:", f"${resumen['fondo_inicial']:,.2f}"),
        ("Ventas realizadas:", f"{resumen['num_ventas']}  (Total: ${resumen['total_ventas']:,.2f})"),
        ("Apartados registrados:", str(resumen["num_apartados"])),
        ("Cobros con tarjeta:", f"${resumen['total_tarjeta_cobrado']:,.2f}"),
    ]
    if mostrar_esperado:
        filas.append(("Cobros en efectivo:", f"${resumen['total_efectivo_cobrado']:,.2f}"))
        filas.append(("Efectivo esperado en caja:", f"${resumen['efectivo_esperado']:,.2f}"))

    for etiqueta, valor in filas:
        fila = tk.Frame(contenedor, bg="#FFFFFF")
        fila.pack(fill="x", padx=20, pady=4)
        tk.Label(fila, text=etiqueta, bg="#FFFFFF", fg="#555555", font=("Arial", 10, "bold"), width=24, anchor="w").pack(side="left")
        color_val = "#27AE60" if "esperado" in etiqueta.lower() else "#4A2E35"
        tk.Label(fila, text=valor, bg="#FFFFFF", fg=color_val, font=("Arial", 10, "bold" if "esperado" in etiqueta.lower() else "normal"), anchor="w").pack(side="left", fill="x", expand=True)


class DialogoCierreCaja(tk.Toplevel):
    """Modal preventivo de corte de caja al cerrar sesión o salir del sistema."""

    def __init__(self, parent, resumen):
        super().__init__(parent)
        self.resumen = resumen
        self.efectivo_confirmado = None
        self.es_admin = (resumen.get("rol") == "Administrador")

        self.title("Cierre de Caja Obligatorio")
        self.geometry("500x540")
        self.configure(bg=estilos.FONDO)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text="CIERRE DE CAJA", bg=estilos.FONDO, fg="#4A2E35", font=("Arial", 18, "bold")).pack(pady=(14, 2))
        subtitulo = (
            "Resumen financiero del turno (Administrador)"
            if self.es_admin
            else "Arqueo de caja ciego — Cuenta e ingresa el efectivo físico en caja"
        )
        tk.Label(self, text=subtitulo, bg=estilos.FONDO, fg="#555555", font=("Arial", 9)).pack(pady=(0, 10))

        tarjeta = tk.Frame(self, bg="#FFFFFF", bd=1, relief="solid")
        tarjeta.pack(fill="x", padx=25, pady=6)
        _construir_resumen_turno(tarjeta, resumen, mostrar_esperado=self.es_admin)

        frame_input = tk.Frame(self, bg=estilos.FONDO)
        frame_input.pack(fill="x", padx=25, pady=(12, 6))
        tk.Label(frame_input, text="Efectivo físico contado en caja ($):", bg=estilos.FONDO, font=("Arial", 10, "bold")).pack(anchor="w")
        self.e_efectivo = tk.Entry(frame_input, font=("Arial", 12))
        self.e_efectivo.pack(fill="x", pady=4)
        self.e_efectivo.focus_set()
        self.e_efectivo.bind("<Return>", lambda e: self._confirmar())

        frame_btns = tk.Frame(self, bg=estilos.FONDO)
        frame_btns.pack(fill="x", padx=25, pady=(10, 14))
        tk.Button(
            frame_btns, text="CONFIRMAR CIERRE", bg="#D9534F", fg="white",
            font=("Arial", 10, "bold"), relief="flat", cursor="hand2", padx=14, pady=8,
            command=self._confirmar,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        tk.Button(
            frame_btns, text="CANCELAR", bg="#95A5A6", fg="white",
            font=("Arial", 10, "bold"), relief="flat", cursor="hand2", padx=14, pady=8,
            command=self.destroy,
        ).pack(side="right", expand=True, fill="x", padx=(6, 0))

    def _confirmar(self):
        try:
            efectivo_fisico = round(float(self.e_efectivo.get().strip()), 2)
            if efectivo_fisico < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Dato inválido", "Ingresa una cantidad numérica válida (0 o mayor).", parent=self)
            return

        diferencia = round(efectivo_fisico - self.resumen["efectivo_esperado"], 2)
        if diferencia == 0:
            messagebox.showinfo("Cierre Guardado", "El arqueo se registró correctamente. La caja cuadra a la perfección.", parent=self)
        elif diferencia > 0:
            detalle = f" (+${diferencia:,.2f})" if self.es_admin else ""
            messagebox.showwarning("Cierre Realizado", f"El arqueo se registró con sobrante en caja{detalle}.", parent=self)
        else:
            detalle = f" (-${abs(diferencia):,.2f})" if self.es_admin else ""
            messagebox.showerror("Cierre Hecho", f"El arqueo se registró con faltante en caja{detalle}.", parent=self)

        self.efectivo_confirmado = efectivo_fisico
        self.destroy()


class PanelCierreCaja(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.resumen = controlador.obtener_resumen_cierre_caja()
        es_admin = (self.resumen.get("rol") == "Administrador")

        tk.Label(self, text="CIERRE DE CAJA", bg=estilos.FONDO, fg="#4A2E35", font=("Arial", 20, "bold")).pack(pady=(22, 4))
        tk.Label(self, text="Resumen del turno actual antes de cerrar sesión", bg=estilos.FONDO, fg="#555555", font=("Arial", 10)).pack(pady=(0, 12))

        tarjeta = tk.Frame(self, bg="#FFFFFF", bd=1, relief="solid")
        tarjeta.pack(fill="x", padx=90, pady=8)
        _construir_resumen_turno(tarjeta, self.resumen, mostrar_esperado=es_admin)

        frame_input = tk.Frame(self, bg=estilos.FONDO)
        frame_input.pack(pady=(12, 6))
        tk.Label(frame_input, text="Efectivo físico contado ($):", bg=estilos.FONDO, font=("Arial", 11, "bold")).pack(side="left", padx=(0, 8))
        self.e_efectivo = tk.Entry(frame_input, width=16, font=("Arial", 11))
        self.e_efectivo.pack(side="left")

        tk.Button(
            self,
            text="FINALIZAR TURNO Y CERRAR SESIÓN",
            bg="#D9534F",
            fg="#FFFFFF",
            activebackground="#C9302C",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            font=("Arial", 11, "bold"),
            padx=18,
            pady=10,
            command=self.confirmar_cierre,
        ).pack(pady=14)

    def confirmar_cierre(self):
        try:
            efectivo_fisico = round(float(self.e_efectivo.get().strip()), 2)
            if efectivo_fisico < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Dato inválido", "Ingresa el efectivo físico contado en caja antes de finalizar el turno.")
            return

        if not messagebox.askyesno("Confirmar cierre", f"¿Confirmar cierre de caja con efectivo contado de ${efectivo_fisico:,.2f}?"):
            return

        diferencia = round(efectivo_fisico - self.resumen["efectivo_esperado"], 2)
        if diferencia == 0:
            messagebox.showinfo("Cierre Guardado", "El arqueo ha sido registrado. La caja cuadra a la perfección.")
        elif diferencia > 0:
            messagebox.showwarning("Cierre Registrado", "El arqueo ha sido registrado con un sobrante en caja. Esto será notificado al Administrador.")
        else:
            messagebox.showerror("Cierre Registrado", "El arqueo ha sido registrado con un faltante en caja. Esto será notificado al Administrador.")

        self.controlador.cerrar_sesion(efectivo_fisico)