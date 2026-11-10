from modelos.conexion import conectar_bd


class RepositorioApartados:
    def __init__(self):
        self.conexion_bd = conectar_bd

    def _resolver_turno(self, cursor, id_turno):
        if not id_turno:
            cursor.execute("SELECT MAX(id_corte_caja) FROM cortes_caja")
            r = cursor.fetchone()
            return r[0] if (r and r[0]) else 1
        return id_turno

    def registrar_apartado(self, nombre, telefono, fecha, articulos, id_turno, pagos):
        conexion = conectar_bd()
        cursor = None
        try:
            cursor = conexion.cursor()
            id_turno = self._resolver_turno(cursor, id_turno)

            subtotal = sum(a["cantidad"] * a["precio_unitario"] for a in articulos)
            impuesto = round(subtotal * 0.16, 2)

            cursor.execute("""
                INSERT INTO apartados (nombre_cliente, telefono_cliente, fecha_entrega,
                                       subtotal, impuesto, estado, id_corte_caja)
                VALUES (%s, %s, %s, %s, %s, 'pendiente', %s)
            """, (nombre, telefono, fecha, subtotal, impuesto, id_turno))
            id_apartado = cursor.lastrowid

            for art in articulos:
                sub = art["cantidad"] * art["precio_unitario"]
                cursor.execute("""
                    INSERT INTO detalles_apartados (cantidad, precio_unitario, descuento,
                                                    subtotal, id_apartado, id_producto)
                    VALUES (%s, %s, 0.00, %s, %s, %s)
                """, (art["cantidad"], art["precio_unitario"], sub, id_apartado, art["id_producto"]))

            for p in pagos:
                cursor.execute("""
                    INSERT INTO pagos_apartados (monto, id_apartado, id_metodo_pago, id_corte_caja)
                    VALUES (%s, %s, %s, %s)
                """, (p["monto"], id_apartado, p["id_metodo_pago"], id_turno))

            conexion.commit()
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            if cursor: cursor.close()
            if conexion.is_connected(): conexion.close()

    def liquidar_apartado(self, id_apartado, pagos, id_corte_caja):
        conexion = conectar_bd()
        cursor = None
        try:
            cursor = conexion.cursor()
            id_corte_caja = self._resolver_turno(cursor, id_corte_caja)

            for p in pagos:
                cursor.execute("""
                    INSERT INTO pagos_apartados (monto, id_apartado, id_metodo_pago,
                                                 id_corte_caja, referencia_pago)
                    VALUES (%s, %s, %s, %s, %s)
                """, (p["monto"], id_apartado, p["id_metodo_pago"],
                      id_corte_caja, p.get("referencia")))

            cursor.execute("UPDATE apartados SET estado='liquidado' WHERE id_apartado=%s", (id_apartado,))
            conexion.commit()
            return True
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            if cursor: cursor.close()
            if conexion.is_connected(): conexion.close()