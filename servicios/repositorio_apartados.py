from modelos.conexion import conectar_bd


class RepositorioApartados:
    def __init__(self):
        self.conexion_bd = conectar_bd

    def _validar_turno(self, id_turno):
        if not id_turno:
            raise ValueError("No hay un turno de caja abierto para operar apartados.")
        return id_turno

    def registrar_apartado(self, nombre, telefono, fecha, articulos, id_turno, pagos):
        id_turno = self._validar_turno(id_turno)
        conexion = conectar_bd()
        if not conexion:
            raise ConnectionError("No se pudo conectar a la base de datos.")
        cursor = None
        try:
            cursor = conexion.cursor()

            total = round(sum(int(a["cantidad"]) * float(a["precio_unitario"]) for a in articulos), 2)
            subtotal = round(total / 1.16, 2)
            impuesto = round(total - subtotal, 2)
            
            cursor.execute("""
                INSERT INTO apartados (nombre_cliente, telefono_cliente, fecha_entrega,
                                       subtotal, impuesto, estado, id_corte_caja)
                VALUES (%s, %s, %s, %s, %s, 'pendiente', %s)
            """, (nombre, telefono, fecha, subtotal, impuesto, id_turno))
            id_apartado = cursor.lastrowid

            for art in articulos:
                cant = int(art["cantidad"])
                id_prod = art["id_producto"]

                cursor.execute("""
                    SELECT stock_resultante
                    FROM movimientos_inventario
                    WHERE id_producto = %s
                    ORDER BY id_movimiento_inventario DESC
                    LIMIT 1
                    FOR UPDATE
                """, (id_prod,))
                fila_stock = cursor.fetchone()
                stock_actual = int(fila_stock[0]) if fila_stock else 0

                if cant > stock_actual:
                    raise ValueError(
                        f"Stock insuficiente para apartar '{art['nombre']}'. "
                        f"Disponible: {stock_actual}, solicitado: {cant}."
                    )

                sub = round(cant * float(art["precio_unitario"]), 2)
                cursor.execute("""
                    INSERT INTO detalles_apartados (cantidad, precio_unitario, descuento,
                                                    subtotal, id_apartado, id_producto)
                    VALUES (%s, %s, 0.00, %s, %s, %s)
                """, (cant, art["precio_unitario"], sub, id_apartado, id_prod))
                id_detalle_apartado = cursor.lastrowid

                nuevo_stock = stock_actual - cant
                cursor.execute("""
                    INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto, id_detalle_apartado)
                    VALUES ('apartado', %s, %s, %s, %s)
                """, (-cant, nuevo_stock, id_prod, id_detalle_apartado))

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
            if cursor:
                cursor.close()
            if conexion.is_connected():
                conexion.close()

    def liquidar_apartado(self, id_apartado, pagos, id_corte_caja):
        id_corte_caja = self._validar_turno(id_corte_caja)
        conexion = conectar_bd()
        if not conexion:
            raise ConnectionError("No se pudo conectar a la base de datos.")
        cursor = None
        try:
            cursor = conexion.cursor()
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
            if cursor:
                cursor.close()
            if conexion.is_connected():
                conexion.close()

    def cancelar_apartado(self, id_apartado):
        conexion = conectar_bd()
        if not conexion:
            return False, "No se pudo conectar a la bd..."
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT estado FROM apartados WHERE id_apartado = %s FOR UPDATE", (id_apartado,))
            fila = cursor.fetchone()
            if not fila:
                return False, "Apartado no encontrado."
            if fila["estado"] != "pendiente":
                return False, f"No se puede cancelar un apartado en estado '{fila['estado']}'."

            cursor.execute("""
                SELECT id_detalle_apartado, id_producto, cantidad
                FROM detalles_apartados
                WHERE id_apartado = %s
            """, (id_apartado,))
            detalles = cursor.fetchall()

            for det in detalles:
                cursor.execute("""
                    SELECT stock_resultante
                    FROM movimientos_inventario
                    WHERE id_producto = %s
                    ORDER BY id_movimiento_inventario DESC
                    LIMIT 1
                    FOR UPDATE
                """, (det["id_producto"],))
                r = cursor.fetchone()
                stock_actual = int(r["stock_resultante"]) if r else 0
                nuevo_stock = stock_actual + int(det["cantidad"])

                cursor.execute("""
                    INSERT INTO movimientos_inventario (tipo, cantidad, stock_resultante, id_producto, id_detalle_apartado)
                    VALUES ('ajuste', %s, %s, %s, %s)
                """, (int(det["cantidad"]), nuevo_stock, det["id_producto"], det["id_detalle_apartado"]))

            cursor.execute("UPDATE apartados SET estado='cancelado' WHERE id_apartado=%s", (id_apartado,))
            conexion.commit()
            return True, "Apartado cancelado y stock restaurado al inventario."
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            if cursor:
                cursor.close()
            if conexion.is_connected():
                conexion.close()