import uuid
import threading
from datetime import datetime
from modelos.conexion import ConexionBD

class RepositorioVentas:
    def __init__(self):
        self.conexion_bd = ConexionBD()
        self._lock = threading.Lock()

    def registrar(self, metodo_pago, total, articulos, facturado=False, usuario_actual=None):
        conexion = self.conexion_bd.conectar()
        if not conexion: return None
        try:
            cursor = conexion.cursor(dictionary=True)
            folio = "V-" + uuid.uuid4().hex[:8].upper()
            fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ticket_pdf = f"tickets/Ticket_{folio}.pdf"
            
            # Obtener ID del usuario
            id_usuario = None
            if usuario_actual:
                cursor.execute("SELECT id_usuario FROM USUARIOS WHERE username = %s", (usuario_actual,))
                res_usu = cursor.fetchone()
                if res_usu: id_usuario = res_usu["id_usuario"]

            # 1. Insertar Venta
            query_venta = """
                INSERT INTO VENTAS (folio, fecha_hora, total, metodo_pago, facturada, ticket_pdf, id_usuario)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_venta, (folio, fecha_hora, float(total), metodo_pago, int(facturado), ticket_pdf, id_usuario))
            id_venta = cursor.lastrowid

            # 2. Insertar Detalles
            for art in articulos:
                cursor.execute("SELECT id_producto FROM PRODUCTOS WHERE nombre_dulce = %s", (art["producto"],))
                id_producto = cursor.fetchone()["id_producto"]
                precio_unit = float(art["subtotal"]) / int(art["cantidad"])
                
                query_detalle = """
                    INSERT INTO DETALLES_VENTAS (cantidad, precio_unitario, subtotal, id_venta, id_producto)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query_detalle, (int(art["cantidad"]), precio_unit, float(art["subtotal"]), id_venta, id_producto))
            
            conexion.commit()
            return {"folio": folio, "fecha": fecha_hora, "metodo_pago": metodo_pago, "total": total, "articulos": articulos, "ticket_pdf": ticket_pdf}
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            cursor.close()
            conexion.close()

    def registrar_lote(self, ventas):
        # Utilizado por el script generar_ventas_demo.py
        for v in ventas:
            self.registrar(v["metodo_pago"], v["total"], v["articulos"], v["facturado"])

    def tamano_actual(self):
        # Retorna el total de registros en BD para la barra de progreso
        conexion = self.conexion_bd.conectar()
        if not conexion: return 0
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM VENTAS")
        total = cursor.fetchone()[0]
        cursor.close()
        conexion.close()
        return total

    def iterar(self, limite_registros):
        # Itera devolviendo diccionarios compatibles con tareas_ventas.py
        conexion = self.conexion_bd.conectar()
        if not conexion: return
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM VENTAS ORDER BY id_venta ASC")
        
        leidas = 0
        for row_venta in cursor:
            leidas += 1
            if leidas > limite_registros: break
            
            # Formatear al estilo JSON anterior para no romper el hilo
            venta = {
                "folio": row_venta["folio"],
                "fecha": str(row_venta["fecha_hora"]),
                "metodo_pago": row_venta["metodo_pago"],
                "total": float(row_venta["total"]),
                "articulos": []
            }
            # En un sistema real se haría un JOIN óptimo, aquí priorizamos mantener la compatibilidad con el Hilo
            cursor_det = conexion.cursor(dictionary=True)
            cursor_det.execute("""
                SELECT dv.cantidad, dv.subtotal, p.nombre_dulce as producto
                FROM DETALLES_VENTAS dv
                JOIN PRODUCTOS p ON dv.id_producto = p.id_producto
                WHERE dv.id_venta = %s
            """, (row_venta["id_venta"],))
            venta["articulos"] = cursor_det.fetchall()
            cursor_det.close()
            
            yield venta, leidas # Envía los "registros leídos" en vez de "bytes"
            
        cursor.close()
        conexion.close()

    def obtener_todas(self):
        return list(v for v, _ in self.iterar(float('inf')))