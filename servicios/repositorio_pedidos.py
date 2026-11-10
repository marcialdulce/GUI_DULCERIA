from modelos.conexion import conectar_bd

class RepositorioPedidos:
    def __init__(self):
        self.conexion_bd = conectar_bd

    def crear_pedido_manual(self, id_proveedor, id_usuario, articulos):
        conexion = conectar_bd()
        try:
            cursor = conexion.cursor()
            subtotal = sum(a["cantidad"] * a["costo_unitario"] for a in articulos)
            impuesto = round(subtotal * 0.16, 2)
            
            cursor.execute("""
                INSERT INTO pedidos_proveedores (subtotal, impuesto, estado, id_usuario, id_proveedor)
                VALUES (%s, %s, 'solicitado', %s, %s)""", (subtotal, impuesto, id_usuario, id_proveedor))
            id_pedido = cursor.lastrowid
            
            for art in articulos:
                sub_art = art["cantidad"] * art["costo_unitario"]
                cursor.execute("""
                    INSERT INTO detalles_pedidos_proveedores (cantidad, costo_unitario, subtotal, id_pedido_proveedor, id_producto)
                    VALUES (%s, %s, %s, %s, %s)""", (art["cantidad"], art["costo_unitario"], sub_art, id_pedido, art["id_producto"]))
                
            conexion.commit()
            return True
        except Exception:  
            conexion.rollback()
            return False
        finally:
            conexion.close()