from modelos.conexion import conectar_bd

class RepositorioApartados:
    def __init__(self):
        self.conexion_bd = conectar_bd

    def registrar_apartado(self, nombre, telefono, fecha, articulos, id_turno, pagos):
        cursor = None
        try:
            cursor = self.conexion.cursor()
            
            # --- SOLUCIÓN PARA ADMINISTRADORES ---
            # Si id_turno viene vacío (None), consultamos el último corte abierto o cerrado en general
            if not id_turno:
                cursor.execute("SELECT MAX(id_corte_caja) FROM cortes_caja")
                resultado = cursor.fetchone()
                id_turno = resultado[0] if (resultado and resultado[0]) else 1
            
            # Cálculos financieros
            subtotal = sum(a["cant"] * a["precio"] for a in articulos)
            impuesto = subtotal * 0.16
            
            # 1. Guardar el encabezado
            cursor.execute("""
                INSERT INTO apartados (nombre_cliente, telefono_cliente, fecha_entrega, subtotal, impuesto, estado, id_corte_caja)
                VALUES (%s, %s, %s, %s, %s, 'pendiente', %s)
            """, (nombre, telefono, fecha, subtotal, impuesto, id_turno))
            
            id_apartado = cursor.lastrowid
            
            # 2. Guardar los detalles (productos apartados)
            for art in articulos:
                cursor.execute("""
                    INSERT INTO detalles_apartados (cantidad, precio_unitario, descuento, subtotal, id_apartado, id_producto)
                    VALUES (%s, %s, 0.00, %s, %s, %s)
                """, (art["cant"], art["precio"], art["cant"] * art["precio"], id_apartado, art["id"]))
            
            # 3. Guardar los pagos realizados (anticipos)
            for p in pagos:
                cursor.execute("""
                    INSERT INTO pagos_apartados (monto, id_apartado, id_metodo_pago, id_corte_caja)
                    VALUES (%s, %s, %s, %s)
                """, (p["monto"], id_apartado, p["id_metodo"], id_turno))
            
            # Confirmar e inyectar en la base de datos
            self.conexion.commit()
            
        except Exception as e:
            self.conexion.rollback()
            raise e
        finally:
            if cursor: 
                cursor.close()

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
        except Exception:
            self.conexion.rollback()
            raise