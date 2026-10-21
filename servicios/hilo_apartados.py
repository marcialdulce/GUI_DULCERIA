"""
Hilo 5: Gestión de apartados pendientes.
"""
import threading
from datetime import date, datetime


class HiloApartados(threading.Thread):

    def __init__(self, apartados, bloqueo, cola_resultados, dias_aviso=3):
        super().__init__(name="HiloGestionApartados", daemon=True)
        self.apartados = apartados
        self.bloqueo = bloqueo
        self.cola_resultados = cola_resultados
        self.dias_aviso = dias_aviso

    def run(self):
        try:
            hoy = date.today()
            avisos = []
            revisados = 0

            # Evita leer la lista mientras otro hilo la modifica.
            with self.bloqueo:
                copia_apartados = [dict(a) for a in self.apartados]

            for apartado in copia_apartados:
                if apartado.get("estado", "Pendiente").lower() != "pendiente":
                    continue

                fecha_texto = str(apartado.get("fecha", "")).strip()

                try:
                    fecha_limite = datetime.strptime(
                        fecha_texto, "%d/%m/%Y"
                    ).date()
                except ValueError:
                    avisos.append({
                        "tipo": "error",
                        "mensaje": (
                            "Fecha inválida en el apartado de "
                            f"{apartado.get('nombre', 'cliente desconocido')}: "
                            f"'{fecha_texto}'. Usa DD/MM/AAAA."
                        ),
                    })
                    continue

                revisados += 1
                dias_restantes = (fecha_limite - hoy).days

                if dias_restantes < 0:
                    avisos.append({
                        "tipo": "vencido",
                        "mensaje": (
                            "APARTADO VENCIDO: "
                            f"{apartado.get('nombre', 'Cliente')} — "
                            f"{apartado.get('producto', 'Producto')} "
                            f"(venció hace {abs(dias_restantes)} día(s))."
                        ),
                    })

                elif dias_restantes <= self.dias_aviso:
                    cuando = (
                        "vence hoy"
                        if dias_restantes == 0
                        else f"vence en {dias_restantes} día(s)"
                    )
                    avisos.append({
                        "tipo": "proximo",
                        "mensaje": (
                            "PRÓXIMO A VENCER: "
                            f"{apartado.get('nombre', 'Cliente')} — "
                            f"{apartado.get('producto', 'Producto')} "
                            f"({cuando})."
                        ),
                    })

            # Entrega los resultados a la interfaz.
            self.cola_resultados.put({
                "ok": True,
                "revisados": revisados,
                "avisos": avisos,
                "fecha_revision": hoy.strftime("%d/%m/%Y"),
            })

        except Exception as exc:
            # Informa el error sin cerrar la aplicación.
            self.cola_resultados.put({"ok": False, "error": str(exc)})