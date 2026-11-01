import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from vistas import estilos
from vistas.generador_tickets import generar_comprobante_ticket_pdf


class PanelTickets(tk.Frame):
    """Lista comprobantes de ventas y permite consultarlos, abrirlos o descargarlos."""
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.ventas = []
        self.venta_seleccionada = None

        tk.Label(self, text="TICKETS DE VENTA", bg=estilos.FONDO,
                 fg="#4A2E35", font=("Arial", 20, "bold")).pack(pady=(18, 8))
        tk.Label(self, text="Selecciona una compra para consultar sus datos o descargar su comprobante.",
                 bg=estilos.FONDO, fg="#555555", font=("Arial", 10)).pack(pady=(0, 10))

        principal = tk.Frame(self, bg="#F4F4F4", bd=1, relief="solid")
        principal.pack(fill="both", expand=True, padx=28, pady=10)
        tk.Label(principal, text="COMPRAS REGISTRADAS", bg="#F4F4F4",
                 font=("Arial", 11, "bold")).pack(anchor="w", padx=15, pady=(12, 5))

        columnas = ("FOLIO", "FECHA", "METODO", "TOTAL")
        self.tabla = ttk.Treeview(principal, columns=columnas, show="headings", height=8)
        for col in columnas:
            self.tabla.heading(col, text=col)
        self.tabla.column("FOLIO", width=125, anchor="center")
        self.tabla.column("FECHA", width=160, anchor="center")
        self.tabla.column("METODO", width=150, anchor="center")
        self.tabla.column("TOTAL", width=110, anchor="e")
        self.tabla.pack(fill="x", padx=15, pady=5)
        self.tabla.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        tk.Label(principal, text="DATOS DE LA COMPRA", bg="#F4F4F4",
                 font=("Arial", 11, "bold")).pack(anchor="w", padx=15, pady=(12, 5))
        self.detalle = tk.Text(principal, height=9, wrap="word", font=("Consolas", 9),
                               state="disabled", relief="solid", bd=1)
        self.detalle.pack(fill="both", expand=True, padx=15, pady=5)

        botones = tk.Frame(principal, bg="#F4F4F4")
        botones.pack(fill="x", padx=15, pady=12)
        tk.Button(botones, text="ACTUALIZAR LISTA", bg="#D9EDEF", relief="flat",
                  font=("Arial", 9, "bold"), command=self.cargar_tickets).pack(side="left", padx=4)
        tk.Button(botones, text="ABRIR TICKET PDF", bg="#D9EDEF", relief="flat",
                  font=("Arial", 9, "bold"), command=self.abrir_ticket).pack(side="right", padx=4)
        tk.Button(botones, text="DESCARGAR TICKET", bg="#F4D03F", relief="flat",
                  font=("Arial", 9, "bold"), command=self.descargar_ticket).pack(side="right", padx=4)
        self.cargar_tickets()

    def cargar_tickets(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        self.ventas = self.controlador.repo_ventas.obtener_todas()
        self.ventas.sort(key=lambda v: v.get("fecha", ""), reverse=True)
        self.venta_seleccionada = None
        for venta in self.ventas:
            # También crea comprobantes para ventas anteriores que aún no tenían PDF.
            ruta_pdf = venta.get("ticket_pdf") or os.path.join("tickets", f"Ticket_{venta.get('folio', 'venta')}.pdf")
            venta["ticket_pdf"] = ruta_pdf
            if not os.path.isfile(ruta_pdf):
                try:
                    generar_comprobante_ticket_pdf(ruta_pdf, venta)
                except Exception:
                    pass
            self.tabla.insert("", "end", iid=venta.get("folio"), values=(
                venta.get("folio", ""), venta.get("fecha", ""),
                venta.get("metodo_pago", ""), f"${float(venta.get('total', 0)):.2f}"
            ))
        self._escribir_detalle("Selecciona un ticket de la lista para ver los datos de la compra.")

    def _escribir_detalle(self, contenido):
        self.detalle.config(state="normal")
        self.detalle.delete("1.0", "end")
        self.detalle.insert("1.0", contenido)
        self.detalle.config(state="disabled")

    def mostrar_detalle(self, event=None):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        folio = seleccion[0]
        venta = next((v for v in self.ventas if v.get("folio") == folio), None)
        if not venta:
            return
        self.venta_seleccionada = venta
        lineas = [
            f"Folio: {venta.get('folio', 'N/D')}",
            f"Fecha: {venta.get('fecha', 'N/D')}",
            f"Método de pago: {venta.get('metodo_pago', 'N/D')}",
            "", "PRODUCTOS:"
        ]
        for art in venta.get("articulos", []):
            lineas.append(f"  • {art.get('producto', 'Producto')} | Cantidad: {art.get('cantidad', 0)} | Importe: ${float(art.get('subtotal', 0)):.2f}")
        lineas.extend(["", f"TOTAL DE LA COMPRA: ${float(venta.get('total', 0)):.2f}"])
        self._escribir_detalle("\n".join(lineas))

    def _ruta_ticket(self):
        if not self.venta_seleccionada:
            messagebox.showwarning("Selecciona un ticket", "Primero selecciona una compra de la lista.", parent=self)
            return None
        ruta = self.venta_seleccionada.get("ticket_pdf", "")
        if not ruta or not os.path.isfile(ruta):
            messagebox.showerror("Ticket no disponible", "No se encontró el PDF de este ticket. Actualiza el programa y genera una nueva venta para obtener su comprobante.", parent=self)
            return None
        return ruta

    def abrir_ticket(self):
        ruta = self._ruta_ticket()
        if not ruta:
            return
        try:
            if os.name == "nt":
                os.startfile(os.path.abspath(ruta))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", ruta])
            else:
                subprocess.Popen(["xdg-open", ruta])
        except Exception as exc:
            messagebox.showerror("No se pudo abrir", str(exc), parent=self)

    def descargar_ticket(self):
        ruta = self._ruta_ticket()
        if not ruta:
            return
        destino = filedialog.asksaveasfilename(
            parent=self, title="Guardar ticket", initialfile=os.path.basename(ruta),
            defaultextension=".pdf", filetypes=[("Documento PDF", "*.pdf")]
        )
        if not destino:
            return
        try:
            shutil.copy2(ruta, destino)
            messagebox.showinfo("Descarga completada", f"El ticket se guardó en:\n{destino}", parent=self)
        except OSError as exc:
            messagebox.showerror("Error al guardar", str(exc), parent=self)
