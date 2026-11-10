from modelos.conexion import conectar_bd

class RepositorioPedidos:
    def __init__(self):
        self.conexion_bd = conectar_bd

    def registrar_pedido(self, id_proveedor, id_usuario, articulos):
        conexion = conectar_bd()
        try:
            cursor = conexion.cursor(dictionary=True)
            subtotal = sum(a["cantidad"] * a["costo_unitario"] for a in articulos)
            impuesto = round(subtotal * 0.16, 2)
            
            cursor.execute("""
                INSERT INTO pedidos_proveedores (subtotal, impuesto, estado, id_usuario, id_proveedor)
                VALUES (%s, %s, 'solicitado', %s, %s)
            """, (subtotal, impuesto, id_usuario, id_proveedor))
            id_pedido = cursor.lastrowid
            
            for art in articulos:
                sub_art = art["cantidad"] * art["costo_unitario"]
                cursor.execute("""
                    INSERT INTO detalles_pedidos_proveedores (cantidad, costo_unitario, subtotal, id_pedido_proveedor, id_producto)
                    VALUES (%s, %s, %s, %s, %s)
                """, (art["cantidad"], art["costo_unitario"], sub_art, id_pedido, art["id_producto"]))
                
            conexion.commit()
            return id_pedido
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            conexion.close()

    def recibir_pedido(self, id_pedido):
        con = conectar_bd()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("""
                SELECT dpp.id_producto, dpp.cantidad, dpp.id_detalle_pedido_proveedor
                FROM detalles_pedidos_proveedores dpp
                WHERE dpp.id_pedido_proveedor = %s
            """, (id_pedido,))
            detalles = cur.fetchall()
            
            for det in detalles:
                # Obtener stock actual (Regla 10: el stock se calcula del último movimiento)
                cur.execute("""SELECT stock_resultante FROM movimientos_inventario 
                               WHERE id_producto=%s ORDER BY id_movimiento_inventario DESC LIMIT 1""", (det["id_producto"],))
                res = cur.fetchone()
                stock_actual = res["stock_resultante"] if res else 0
                nuevo_stock = stock_actual + det["cantidad"]

                # Registrar entrada al inventario (Regla 10)
                cur.execute("""
                    INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto, id_detalle_pedido_proveedor)
                    VALUES ('entrada', %s, %s, %s, %s)
                """, (det["cantidad"], nuevo_stock, det["id_producto"], det["id_detalle_pedido_proveedor"]))
                
            cur.execute("UPDATE pedidos_proveedores SET estado='recibido' WHERE id_pedido_proveedor=%s", (id_pedido,))
            con.commit()
            return True
        except Exception:
            con.rollback()
            return False
        finally:
            con.close()

    def cancelar_pedido(self, id_pedido):
        con = conectar_bd()
        try:
            cur = con.cursor()
            cur.execute("UPDATE pedidos_proveedores SET estado='cancelado' WHERE id_pedido_proveedor=%s", (id_pedido,))
            con.commit()
            return True
        except Exception:
            con.rollback()
            return False
        finally:
            con.close() 