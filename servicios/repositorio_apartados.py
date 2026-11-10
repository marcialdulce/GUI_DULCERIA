from modelos.conexion import conectar_bd

class RepositorioApartados:
    def __init__(self):
        self.conexion_bd = conectar_bd

    def registrar_apartado(self, nombre_cliente, telefono, fecha_entrega, articulos, id_corte_caja, pagos_anticipo):
        conexion = conectar_bd()
        try:
            cursor = conexion.cursor(dictionary=True)
            subtotal = sum(a["subtotal"] for a in articulos)
            impuesto = round(subtotal * 0.16, 2)
            
            # 1. Crear el apartado
            cursor.execute("""
                INSERT INTO apartados (nombre_cliente, telefono_cliente, fecha_entrega, subtotal, impuesto, estado, id_corte_caja)
                VALUES (%s, %s, %s, %s, %s, 'pendiente', %s)
            """, (nombre_cliente, telefono, fecha_entrega, subtotal, impuesto, id_corte_caja))
            id_apartado = cursor.lastrowid
            
            # 2. Insertar detalles
            for art in articulos:
                cursor.execute("""
                    INSERT INTO detalles_apartados (cantidad, precio_unitario, subtotal, id_apartado, id_producto)
                    VALUES (%s, %s, %s, %s, %s)
                """, (art["cantidad"], art["precio_unitario"], art["subtotal"], id_apartado, art["id_producto"]))
                
            # 3. Registrar Pagos del Anticipo
            for pago in pagos_anticipo:
                cursor.execute("""
                    INSERT INTO pagos_apartados (monto, id_apartado, id_metodo_pago, id_corte_caja)
                    VALUES (%s, %s, %s, %s)
                """, (pago["monto"], id_apartado, pago["id_metodo_pago"], id_corte_caja))

            conexion.commit()
            return id_apartado
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            conexion.close()

    def cancelar_apartado(self, id_apartado):
        conexion = conectar_bd()
        try:
            cursor = conexion.cursor()
            cursor.execute("UPDATE apartados SET estado = 'cancelado' WHERE id_apartado = %s", (id_apartado,))
            conexion.commit()
            return True
        except Exception:
            conexion.rollback()
            return False
        finally:
            conexion.close()