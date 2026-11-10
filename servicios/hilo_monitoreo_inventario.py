"""
Hilo 2: Actualización y monitoreo del inventario
Comprueba existencias después de una venta y detecta productos agotados o con poco stock.
"""

import threading


class HiloMonitoreoInventario(threading.Thread):

  def __init__(self, inventario, callback_alerta=None, lock=None):
    super().__init__()
    self.inventario = inventario
    self.callback_alerta = callback_alerta
    self.lock = lock
    self.daemon = True

  def run(self):
    if self.lock:
      with self.lock:
        bajo_stock, agotados = self._verificar_existencias()
    else:
      bajo_stock, agotados = self._verificar_existencias()

    if self.callback_alerta:
      self.callback_alerta(bajo_stock, agotados)

  def _verificar_existencias(self):
    bajo_stock = []
    agotados = []

    # Soporta si el inventario viene como Diccionario o como Lista de diccionarios
    if isinstance(self.inventario, dict):
      elementos = self.inventario.items()
    elif isinstance(self.inventario, list):
      elementos = [
          (prod.get("id", idx), prod) for idx, prod in enumerate(self.inventario)
      ]
    else:
      elementos = []

    for codigo, datos in elementos:
      stock = datos.get("stock", 0)
      stock_minimo = datos.get("stock_minimo", 15)

      if stock == 0:
        agotados.append(datos.get("nombre", str(codigo)))
      elif stock <= stock_minimo:
        bajo_stock.append(
            f"{datos.get('nombre', str(codigo))} (Quedan: {stock})"
        )

    return bajo_stock, agotados