""""
Hilo encargado de generar las facturas PDF en segundo plano.
Se ubica en la capa de servicios porque es una utilidad de
infraestructura
"""
import threading
from vistas.generador_tickets import generar_ticket_pdf


class HiloFactura(threading.Thread):
    """Genera una factura PDF en segundo plano para no bloquear la UI"""

    def __init__(self, nombre_archivo, rfc, razon_social, total,
                 carrito, metodo_pago, pago, cambio, prioridad=5):
        super().__init__(name=f"HiloFactura-{rfc}", daemon=True)
        self.nombre_archivo = nombre_archivo
        self.rfc = rfc
        self.razon_social = razon_social
        self.total = total
        self.carrito = carrito
        self.metodo_pago = metodo_pago
        self.pago = pago
        self.cambio = cambio
        self._prioridad = prioridad
        self.exito = False
        self.error = None

    # run()  el cuerpo del hilo
    def run(self):
        try:
            generar_ticket_pdf(
                nombre_archivo=self.nombre_archivo,
                rfc=self.rfc,
                razon_social=self.razon_social,
                total=self.total,
                carrito_comprado=self.carrito,
                metodo_pago=self.metodo_pago,
                pago=self.pago,
                cambio=self.cambio
            )
            self.exito = True
            print(f"[{self.name}] Factura generada: {self.nombre_archivo}")
        except Exception as e:
            self.error = str(e)
            print(f"[{self.name}] Error: {e}")

    # setName / getName
    def get_nombre(self):
        return self.name

    # setPriority / getPriority (simulado)
    def set_prioridad(self, valor):
        self._prioridad = valor

    def get_prioridad(self):
        return self._prioridad