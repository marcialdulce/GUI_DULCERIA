from modelos.conexion import conectar_bd

class RepositorioApartados:
    def __init__(self):
        self.conexion_bd = conectar_bd

    def registrar_apartado(self, nombre, telefono, fecha_entrega, articulos, id_corte_caja, pagos_anticipo):
        conexion = conectar_bd()
        try:
            cursor = conexion.cursor(dictionary=True)
            subtotal = sum(a["precio_unitario"] * a["cantidad"] for a in articulos)
            impuesto = round(subtotal * 0.16, 2)
            
            cursor.execute("""
                INSERT INTO apartados (nombre_cliente, telefono_cliente, fecha_entrega, subtotal, impuesto, estado, id_corte_caja)
                VALUES (%s, %s, %s, %s, %s, 'pendiente', %s)""", (nombre, telefono, fecha_entrega, subtotal, impuesto, id_corte_caja))
            id_apartado = cursor.lastrowid
            
            for art in articulos:
                cursor.execute("""
                    INSERT INTO detalles_apartados (cantidad, precio_unitario, subtotal, id_apartado, id_producto)
                    VALUES (%s, %s, %s, %s, %s)""", (art["cantidad"], art["precio_unitario"], art["precio_unitario"]*art["cantidad"], id_apartado, art["id_producto"]))
                
            for pago in pagos_anticipo:
                cursor.execute("""
                    INSERT INTO pagos_apartados (monto, id_apartado, id_metodo_pago, id_corte_caja, referencia_pago)
                    VALUES (%s, %s, %s, %s, %s)""", (pago["monto"], id_apartado, pago["id_metodo_pago"], id_corte_caja, pago.get("referencia", None)))

            conexion.commit()
            return id_apartado
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            conexion.close()

    def liquidar_apartado(self, id_apartado, pagos, id_corte_caja):
        conexion = conectar_bd()
        try:
            cursor = conexion.cursor()
            for pago in pagos:
                cursor.execute("""
                    INSERT INTO pagos_apartados (monto, id_apartado, id_metodo_pago, id_corte_caja, referencia_pago)
                    VALUES (%s, %s, %s, %s, %s)""", (pago["monto"], id_apartado, pago["id_metodo_pago"], id_corte_caja, pago.get("referencia", None)))
            
            cursor.execute("UPDATE apartados SET estado='liquidado' WHERE id_apartado=%s", (id_apartado,))
            conexion.commit()
            return True
        except Exception as e:
            conexion.rollback()
            return False
        finally:
            conexion.close()