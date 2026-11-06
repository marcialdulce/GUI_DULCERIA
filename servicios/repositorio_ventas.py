import uuid
import threading
from datetime import datetime
from modelos.conexion import conectar_bd

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


class RepositorioVentas:
    def __init__(self):
        self.conexion_bd = conectar_bd
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Registrar UNA venta (transacción única: venta + detalles + stock + factura)
    # ------------------------------------------------------------------
    def registrar(self, metodo_pago, total, articulos, facturado=False, usuario_actual=None,
                  id_turno=None, datos_factura=None, descontar_stock=True):
        conexion = conectar_bd()
        if not conexion:
            raise ConnectionError("No hay conexión con la base de datos.")
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)
            folio = "V-" + uuid.uuid4().hex[:8].upper()
            fecha_hora = datetime.now().strftime(FORMATO_FECHA)
            ticket_pdf = f"tickets/Ticket_{folio}.pdf"

            id_usuario = None
            if usuario_actual:
                cursor.execute("SELECT id_usuario FROM USUARIOS WHERE username = %s", (usuario_actual,))
                fila = cursor.fetchone()
                if fila: id_usuario = fila["id_usuario"]

            cursor.execute(
                """INSERT INTO VENTAS (folio, fecha_hora, total, metodo_pago, facturada, ticket_pdf, id_usuario, id_turno)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (folio, fecha_hora, float(total), metodo_pago, int(facturado), ticket_pdf, id_usuario, id_turno))
            id_venta = cursor.lastrowid

            for art in articulos:
                cursor.execute("SELECT id_producto FROM PRODUCTOS WHERE nombre_dulce = %s", (art["producto"],))
                id_producto = cursor.fetchone()["id_producto"]
                cantidad = int(art["cantidad"])
                precio_unit = round(float(art["subtotal"]) / cantidad, 2)
                cursor.execute(
                    """INSERT INTO DETALLES_VENTAS (cantidad, precio_unitario, subtotal, id_venta, id_producto)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (cantidad, precio_unit, float(art["subtotal"]), id_venta, id_producto))
                if descontar_stock:
                    # Condición stock >= cantidad: evita vender lo que ya no hay (dos cajas a la vez)
                    cursor.execute(
                        "UPDATE PRODUCTOS SET stock_actual = stock_actual - %s WHERE id_producto = %s AND stock_actual >= %s",
                        (cantidad, id_producto, cantidad))
                    if cursor.rowcount == 0:
                        raise ValueError(f"Stock insuficiente de '{art['producto']}'.")

            if facturado and datos_factura:
                cursor.execute(
                    """INSERT INTO FACTURA (nombre, apellidos, rfc, correo, id_venta)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (datos_factura.get("nombre", ""), datos_factura.get("apellidos", ""),
                     datos_factura.get("rfc", ""), datos_factura.get("correo", ""), id_venta))

            conexion.commit()
            return {"id_venta": id_venta, "folio": folio, "fecha": fecha_hora, "metodo_pago": metodo_pago,
                    "total": total, "articulos": articulos, "ticket_pdf": ticket_pdf}
        except Exception:
            conexion.rollback()
            raise
        finally:
            if cursor: cursor.close()
            conexion.close()

    def actualizar_ruta_factura(self, id_venta, ruta_pdf):
        """Guarda dónde quedó el PDF de la factura (el usuario lo elige DESPUÉS de cobrar)."""
        conexion = conectar_bd()
        if not conexion: return
        try:
            cur = conexion.cursor()
            cur.execute("UPDATE FACTURA SET ruta_pdf = %s WHERE id_venta = %s", (ruta_pdf, id_venta))
            conexion.commit()
            cur.close()
        finally:
            conexion.close()

    # ------------------------------------------------------------------
    # Carga masiva (script demo): una sola conexión, sin tocar el stock
    # ------------------------------------------------------------------
    def registrar_lote(self, ventas):
        conexion = conectar_bd()
        if not conexion:
            raise ConnectionError("No hay conexión con la base de datos.")
        try:
            cur = conexion.cursor(dictionary=True)
            cur.execute("SELECT nombre_dulce, id_producto FROM PRODUCTOS")
            ids = {f["nombre_dulce"]: f["id_producto"] for f in cur.fetchall()}
            for v in ventas:
                cur.execute(
                    """INSERT INTO VENTAS (folio, fecha_hora, total, metodo_pago, facturada, ticket_pdf)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (v["folio"], v["fecha"], v["total"], v["metodo_pago"], int(v.get("facturado", False)),
                     f"tickets/Ticket_{v['folio']}.pdf"))
                id_venta = cur.lastrowid
                filas = [(int(a["cantidad"]), round(float(a["subtotal"]) / int(a["cantidad"]), 2),
                          float(a["subtotal"]), id_venta, ids[a["producto"]]) for a in v["articulos"]]
                cur.executemany(
                    """INSERT INTO DETALLES_VENTAS (cantidad, precio_unitario, subtotal, id_venta, id_producto)
                       VALUES (%s,%s,%s,%s,%s)""", filas)
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------
    def tamano_actual(self, usuario=None):
        conexion = conectar_bd()
        if not conexion: return 0
        try:
            cur = conexion.cursor()
            if usuario:
                cur.execute("""SELECT COUNT(*) FROM VENTAS v JOIN USUARIOS u ON v.id_usuario = u.id_usuario
                               WHERE u.username = %s""", (usuario,))
            else:
                cur.execute("SELECT COUNT(*) FROM VENTAS")
            total = cur.fetchone()[0]
            cur.close()
            return total
        finally:
            conexion.close()

    def iterar(self, limite_registros, usuario=None):
        """Un solo JOIN (antes: 1 consulta por venta). Devuelve (venta_dict, n_leidas)."""
        conexion = conectar_bd()
        if not conexion: return
        try:
            cursor = conexion.cursor(dictionary=True, buffered=False)
            sql = """
                SELECT v.id_venta, v.folio, v.fecha_hora, v.total, v.metodo_pago, v.ticket_pdf, v.facturada,
                       dv.cantidad, dv.subtotal, p.nombre_dulce AS producto
                FROM VENTAS v
                LEFT JOIN DETALLES_VENTAS dv ON dv.id_venta = v.id_venta
                LEFT JOIN PRODUCTOS p ON p.id_producto = dv.id_producto
                {filtro}
                ORDER BY v.id_venta ASC
            """
            if usuario:
                filtro = "WHERE v.id_usuario = (SELECT id_usuario FROM USUARIOS WHERE username = %s)"
                cursor.execute(sql.replace("{filtro}", filtro), (usuario,))
            else:
                cursor.execute(sql.replace("{filtro}", ""))

            actual, leidas = None, 0
            for fila in cursor:
                if actual is None or fila["id_venta"] != actual["_id"]:
                    if actual is not None:
                        leidas += 1
                        if leidas > limite_registros: return
                        yield self._sin_id(actual), leidas
                    actual = {"_id": fila["id_venta"], "folio": fila["folio"], "fecha": str(fila["fecha_hora"]),
                              "metodo_pago": fila["metodo_pago"], "total": float(fila["total"]),
                              "ticket_pdf": fila["ticket_pdf"], "facturada": bool(fila["facturada"]), "articulos": []}
                if fila["producto"] is not None:
                    actual["articulos"].append({"producto": fila["producto"], "cantidad": fila["cantidad"],
                                                "subtotal": float(fila["subtotal"])})
            if actual is not None:
                leidas += 1
                if leidas <= limite_registros:
                    yield self._sin_id(actual), leidas
            cursor.close()
        finally:
            conexion.close()

    @staticmethod
    def _sin_id(v):
        v = dict(v); v.pop("_id", None); return v

    def obtener_todas(self, usuario=None):
        return [v for v, _ in self.iterar(float("inf"), usuario)]

    def efectivo_turno(self, id_turno):
        """Efectivo que DEBE haber en caja por las ventas en efectivo de ese turno (cálculo en SQL)."""
        conexion = conectar_bd()
        if not conexion: return 0.0
        try:
            cur = conexion.cursor()
            cur.execute("SELECT COALESCE(SUM(total),0) FROM VENTAS WHERE id_turno = %s AND metodo_pago = 'Efectivo'", (id_turno,))
            total = float(cur.fetchone()[0])
            cur.close()
            return total
        finally:
            conexion.close()
