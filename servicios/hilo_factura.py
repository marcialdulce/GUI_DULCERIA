""""
Hilo encargado de generar las facturas PDF en segundo plano.
Se ubica en la capa de servicios porque es una utilidad de
infraestructura
"""
import threading
import time
from vistas.generador_tickets import generar_ticket_pdf

lock_pdf = threading.Lock()

class HiloFactura(threading.Thread):
    """Genera una factura PDF en segundo plano para no bloquear la UI"""

    def __init__(self, nombre_archivo, rfc, razon_social, total,
                 carrito, metodo_pago, pago, cambio, prioridad=5):
        
        # setName(): Se usa name= para asignar el nombre del hilo
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

        # Atributos de control (prioridad, stop, pause)
        self._prioridad = prioridad
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set() # Inicia despierto (no pausado)

    # run()  el cuerpo del hilo
    def run(self):

          # Simulamos que ReportLab tarda 3 segundos en preparar el PDF
          # Hacemos 30 iteraciones de 0.1 segundos para poder pausar o detener el hilo en el proceso
        try:
            for _ in range(30):

                # Verificamos si se solicitó STOP (detener)
                if self._stop_event.is_set():
                    print(f"[{self.name}] Hilo detenido antes de generar la factura.")
                    return # Sale del hilo y pasa a DEAD

                # Verificamos si se solicitó SUSPEND (pausar)
                self._pause_event.wait() # Si _pause_event esta en False, el hilo se queda esperando aqui

                # Pausa real de 0.1 segundos
                time.sleep(0.1)
        
            # Si otro hilo esta en uso, este hilo esperara su turno para otro proceso
            with lock_pdf:
                # Simulamos trabajo de ReportLab
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
        except FileNotFoundError:
            self.error = "La carpeta 'facturas' no existe o fue movida. Por favor, créala de nuevo."
            print(f"[{self.name}] Error: Carpeta no encontrada")
        except PermissionError:
            self.error = "No hay permisos para guardar el archivo. Verifica que no esté abierto en otro programa."
            print(f"[{self.name}] Error: Permiso denegado")
        except Exception as e:
            self.error = str(e)
            print(f"[{self.name}] Error inesperado: {e}")

    # --- Métodos solicitados  ---

    def stop(self):
        # Detiene el hilo (reemplaza a stop() de Java)
        self._stop_event.set()
        self._pause_event.set() # Lo despierta por si estaba pausado para que pueda morir

    def suspend(self):
        # Pausa el hilo (reemplaza a suspend() de Java)
        self._pause_event.clear()

    def resume(self):
        # Reanuda el hilo (reemplaza a resume() de Java)
        self._pause_event.set()

    def set_prioridad(self, valor):
        """setPriority() simulado."""
        self._prioridad = valor

    def get_prioridad(self):
        """getPriority() simulado."""
        return self._prioridad

    def get_nombre(self):
        """getName()."""
        return self.name