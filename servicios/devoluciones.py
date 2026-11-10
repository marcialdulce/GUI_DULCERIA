import os
import json
import uuid
from datetime import datetime

class ServicioDevoluciones:
    def __init__(self, ruta="datos/devoluciones.jsonl"):
        self.ruta = ruta

    def obtener_cantidades_devueltas(self):
        acumulado = {}
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                for linea in f:
                    if not linea.strip(): continue
                    try:
                        d = json.loads(linea)
                        clave = (d["folio"], d["producto"])
                        acumulado[clave] = acumulado.get(clave, 0) + int(d["cantidad"])
                    except (ValueError, KeyError, TypeError):
                        continue
        except FileNotFoundError:
            pass
        return acumulado

    def registrar(self, folio_venta, producto, cantidad, importe, motivo, usuario):
        devolucion = {
            "folio_devolucion": "D-" + uuid.uuid4().hex[:8].upper(),
            "folio": folio_venta, 
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "producto": producto, 
            "cantidad": cantidad, 
            "importe": importe,
            "motivo": motivo.strip(), 
            "usuario": usuario
        }
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        with open(self.ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps(devolucion, ensure_ascii=False) + "\n")
        return devolucion