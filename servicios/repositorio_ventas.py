import json
import os
import threading
import uuid
from datetime import datetime

RUTA_VENTAS = os.path.join("datos", "ventas.jsonl")
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

class RepositorioVentas:

    def __init__(self, ruta=RUTA_VENTAS):
        self.ruta = ruta
        self._lock = threading.Lock()

    def registrar(self, metodo_pago, total, articulos, facturado=False):
        venta = {
            "folio": "V-" + uuid.uuid4().hex[:8].upper(),
            "fecha": datetime.now().strftime(FORMATO_FECHA),
            "metodo_pago": metodo_pago,
            "facturado": bool(facturado),
            "total": round(float(total), 2),
            "articulos": [
                {
                    "producto": a["producto"],
                    "cantidad": int(a["cantidad"]),
                    "subtotal": round(float(a["subtotal"]), 2),
                }
                for a in articulos
            ],
        }
        venta["ticket_pdf"] = os.path.join("tickets", f"Ticket_{venta['folio']}.pdf")
        self.registrar_lote([venta])
        return venta

    def registrar_lote(self, ventas):
        texto = "".join(json.dumps(v, ensure_ascii=False) + "\n" for v in ventas)
        with self._lock:
            carpeta = os.path.dirname(self.ruta)
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)
            with open(self.ruta, "ab") as f:
                f.write(texto.encode("utf-8"))

    def tamano_actual(self):
        with self._lock:
            try:
                return os.path.getsize(self.ruta)
            except FileNotFoundError:
                return 0

    def iterar(self, limite_bytes):
        try:
            archivo = open(self.ruta, "rb")
        except FileNotFoundError:
            return

        leidos = 0
        with archivo:
            for linea in archivo:
                leidos += len(linea)
                if leidos > limite_bytes:
                    break
                if not linea.strip():
                    continue
                try:
                    venta = json.loads(linea)
                except ValueError:
                    venta = None
                yield venta, leidos

    def obtener_todas(self):
        ventas = []
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                for linea in f:
                    if linea.strip():
                        try:
                            ventas.append(json.loads(linea))
                        except ValueError:
                            continue
        except FileNotFoundError:
            pass
        return ventas