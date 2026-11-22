"""
Hilo encargado de generar las facturas PDF en segundo plano.
"""
import threading
import time
from vistas.generador_tickets import generar_ticket_pdf

lock_pdf = threading.Lock()


class HiloFactura(threading.Thread):
    """Genera una factura PDF en segundo plano para no bloquear la UI."""

    def __init__(
        self,
        ruta_completa,
        rfc,
        razon_social,
        total,
        carrito,
        metodo_pago,
        pago,
        cambio,
        regimen_fiscal="",
        cp_fiscal="",
        correo="",
        folio_factura="N/D",
        prioridad=5,
    ):
        super().__init__(name=f"HiloFactura-{rfc}", daemon=True)

        self.ruta_completa = ruta_completa
        self.rfc = rfc
        self.razon_social = razon_social
        self.total = total
        self.carrito = [dict(item) for item in carrito]
        self.metodo_pago = metodo_pago
        self.pago = pago
        self.cambio = cambio
        self.regimen_fiscal = regimen_fiscal
        self.cp_fiscal = cp_fiscal
        self.correo = correo
        self.folio_factura = folio_factura
        self._prioridad = prioridad
        self.exito = False
        self.error = None

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()

    def run(self):
        try:
            for _ in range(15):
                if self._stop_event.is_set():
                    print(f"[{self.name}] Hilo detenido antes de generar la factura.")
                    return
                self._pause_event.wait()
                time.sleep(0.1)

            with lock_pdf:
                generar_ticket_pdf(
                    ruta_completa=self.ruta_completa,
                    rfc=self.rfc,
                    razon_social=self.razon_social,
                    total=self.total,
                    carrito_comprado=self.carrito,
                    metodo_pago=self.metodo_pago,
                    pago=self.pago,
                    cambio=self.cambio,
                    regimen_fiscal=self.regimen_fiscal,
                    cp_fiscal=self.cp_fiscal,
                    correo=self.correo,
                    folio_factura=self.folio_factura,
                )

            self.exito = True
            print(f"[{self.name}] Factura generada: {self.ruta_completa}")
        except FileNotFoundError:
            self.error = "La carpeta destino no existe o fue movida."
            print(f"[{self.name}] Error: Carpeta no encontrada")
        except PermissionError:
            self.error = "No hay permisos para guardar el archivo. Verifica que no esté abierto."
            print(f"[{self.name}] Error: Permiso denegado")
        except Exception as e:
            self.error = str(e)
            print(f"[{self.name}] Error inesperado: {e}")

    def stop(self):
        self._stop_event.set()
        self._pause_event.set()

    def suspend(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def set_prioridad(self, valor):
        self._prioridad = valor

    def get_prioridad(self):
        return self._prioridad

    def get_nombre(self):
        return self.name