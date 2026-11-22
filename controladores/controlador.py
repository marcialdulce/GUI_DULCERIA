import os
import queue
import threading
from tkinter import messagebox, simpledialog
from datetime import datetime
from modelos.modelo import ModeloDulceria
from servicios.repositorio_ventas import RepositorioVentas
from servicios.repositorio_apartados import RepositorioApartados
from servicios.repositorio_pedidos import RepositorioPedidos
from servicios.tareas_ventas import TareaCargarVentas, TareaExportarReporte


class ControladorDulceria:
    def __init__(self):
        self.modelo = ModeloDulceria()
        self.repo_ventas = RepositorioVentas()
        self.repo_apartados = RepositorioApartados()
        self.repo_pedidos = RepositorioPedidos()
        self.usuario_actual = None
        self.id_usuario_actual = None
        self.rol_actual = None
        self.inicio_sesion = None
        self.id_turno_actual = None
        self.vista = None

        # --- Variables para el Historial ---
        self.cola_tareas = queue.Queue()
        self.hilo_carga = None
        self.hilo_export = None
        self._cancelar_carga = threading.Event()
        self.resumen_ventas = None
        self.estado_carga = {"estado": "inactivo", "porcentaje": 0.0, "leidas": 0, "mensaje": ""}
        self.estado_export = {"estado": "inactivo", "ruta": ""}
        self._notificaciones = []

    # ---------------- SESIÓN Y TURNOS DE CAJA (Regla #7) ----------------
    def procesar_login(self, usuario, password):
        user_data = self.modelo.validar_usuario(usuario, password)
        if user_data:
            self.usuario_actual = usuario
            self.id_usuario_actual = user_data["id_usuario"]
            self.rol_actual = self.modelo.obtener_rol(user_data["id_rol"])
            self.inicio_sesion = datetime.now()

            corte_abierto = self.modelo._ejecutar_consulta(
                """SELECT id_corte_caja FROM cortes_caja
                   WHERE id_usuario = %s AND estado = 'abierto'
                   ORDER BY id_corte_caja DESC LIMIT 1""",
                (self.id_usuario_actual,),
                fetch=True,
            )

            if corte_abierto:
                self.id_turno_actual = corte_abierto["id_corte_caja"]
            else:
                num_caja = simpledialog.askinteger(
                    "Abrir Caja",
                    f"Hola {usuario} ({self.rol_actual}).\n¿En qué número de caja vas a operar? (1-4)",
                    minvalue=1,
                    maxvalue=4,
                )
                if not num_caja:
                    messagebox.showwarning("Cancelado", "Debes seleccionar una caja para iniciar turno.")
                    return

                self.id_turno_actual = self.modelo._ejecutar_consulta(
                    "INSERT INTO cortes_caja (fondo_inicial, id_usuario, id_caja) VALUES (500.00, %s, %s)",
                    (self.id_usuario_actual, num_caja),
                )

            self.vista.pantallas["PantallaLogin"].entry_usuario.delete(0, "end")
            self.vista.pantallas["PantallaLogin"].entry_pass.delete(0, "end")

            if self.rol_actual == "Cajero":
                opciones = [
                    "PUNTO DE VENTA",
                    "COBROS Y PAGOS",
                    "TICKETS",
                    "HISTORIAL DE VENTAS",
                    "CIERRE DE CAJA",
                ]
            else:
                opciones = [
                    "INICIO",
                    "NUEVA VENTA",
                    "REPORTES",
                    "COBROS Y PAGOS",
                    "INVENTARIO",
                    "APARTADOS",
                    "PROVEEDORES",
                    "HISTORIAL",
                    "CIERRE DE CAJA",
                ]

            messagebox.showinfo("Bienvenido", f"Sesión iniciada como {usuario} ({self.rol_actual})")
            self.vista.pantallas["MenuPrincipal"].configurar_acceso(usuario, self.rol_actual, opciones)
            self.vista.mostrar_pantalla("MenuPrincipal")
        else:
            self.vista.mostrar_alerta("Datos incorrectos", "Las claves son incorrectas.", "error")

    def obtener_resumen_cierre_caja(self):
        fin = datetime.now()
        datos_db = self.modelo.obtener_resumen_turno_db(self.id_turno_actual) if self.id_turno_actual else {}
        inicio = datos_db.get("fecha_hora_inicio") or self.inicio_sesion or fin
        duracion = fin - inicio
        segundos = max(0, int(duracion.total_seconds()))
        horas, resto = divmod(segundos, 3600)
        minutos, segundos = divmod(resto, 60)

        return {
            "usuario": self.usuario_actual or "",
            "rol": self.rol_actual or "",
            "id_corte_caja": self.id_turno_actual,
            "numero_caja": datos_db.get("numero_caja", "N/D"),
            "inicio": inicio.strftime("%d/%m/%Y %H:%M:%S"),
            "fin": fin.strftime("%d/%m/%Y %H:%M:%S"),
            "duracion": f"{horas:02d}h {minutos:02d}m {segundos:02d}s",
            "fondo_inicial": datos_db.get("fondo_inicial", 500.0),
            "num_ventas": datos_db.get("num_ventas", 0),
            "total_ventas": datos_db.get("total_ventas", 0.0),
            "num_apartados": datos_db.get("num_apartados", 0),
            "efectivo_ventas": datos_db.get("efectivo_ventas", 0.0),
            "tarjeta_ventas": datos_db.get("tarjeta_ventas", 0.0),
            "efectivo_apartados": datos_db.get("efectivo_apartados", 0.0),
            "tarjeta_apartados": datos_db.get("tarjeta_apartados", 0.0),
            "total_efectivo_cobrado": datos_db.get("total_efectivo_cobrado", 0.0),
            "total_tarjeta_cobrado": datos_db.get("total_tarjeta_cobrado", 0.0),
            "efectivo_esperado": datos_db.get("efectivo_esperado", 500.0),
        }

    def cerrar_sesion(self, efectivo_fisico=None):
        if self.id_turno_actual:
            if efectivo_fisico is None:
                from vistas.panel_cierre_caja import DialogoCierreCaja
                resumen = self.obtener_resumen_cierre_caja()
                dialogo = DialogoCierreCaja(self.vista, resumen)
                self.vista.wait_window(dialogo)
                if dialogo.efectivo_confirmado is None:
                    return False
                efectivo_fisico = dialogo.efectivo_confirmado

            self.modelo._ejecutar_consulta(
                "UPDATE cortes_caja SET fecha_hora_fin=NOW(), efectivo_contado=%s, estado='cerrado' WHERE id_corte_caja=%s",
                (efectivo_fisico, self.id_turno_actual),
            )
            self.id_turno_actual = None

        self.modelo.ticket_actual.clear()
        self.usuario_actual = None
        self.rol_actual = None
        self.vista.pantallas["MenuPrincipal"].configurar_acceso("", None, [])
        self.vista.mostrar_pantalla("PantallaLogin")
        self.vista.pantallas["PantallaLogin"].entry_usuario.delete(0, "end")
        self.vista.pantallas["PantallaLogin"].entry_pass.delete(0, "end")
        return True

    def intentar_cerrar_aplicacion(self):
        """Medida preventiva al cerrar la ventana: obliga a efectuar el corte de caja si hay turno abierto."""
        if self.id_turno_actual:
            messagebox.showinfo(
                "Corte de Caja Preventivo",
                "Tienes un turno de caja abierto.\nDebes realizar tu cierre de caja antes de salir del sistema.",
            )
            return self.cerrar_sesion()
        return True

    # ---------------- HISTORIAL (HILOS) ----------------
    def iniciar_carga_ventas(self, fecha_filtro=""):
        if self.estado_carga["estado"] in ("cargando", "cancelando"):
            return False
        self._cancelar_carga = threading.Event()
        filtro_usuario = self.usuario_actual if self.rol_actual == "Cajero" else None

        tarea = TareaCargarVentas(
            self.repo_ventas,
            self.cola_tareas,
            self._cancelar_carga,
            fecha_filtro,
            usuario_filtro=filtro_usuario,
        )
        self.hilo_carga = threading.Thread(target=tarea.run, name="HiloCargaVentas", daemon=True)
        self.estado_carga = {"estado": "cargando", "porcentaje": 0.0, "leidas": 0, "mensaje": ""}
        self.hilo_carga.start()
        return True

    def cancelar_carga_ventas(self):
        if self.estado_carga["estado"] == "cargando":
            self.estado_carga["estado"] = "cancelando"
            self._cancelar_carga.set()

    def exportar_reporte(self, carpeta):
        if self.resumen_ventas is None:
            return (
                False,
                "Primero carga las ventas (botón BUSCAR) para tener datos que exportar.",
            )
        if self.estado_export["estado"] == "guardando":
            return False, "Ya se está guardando un reporte. Espera a que termine."

        carpeta = (carpeta or "").strip() or "reportes"
        tarea = TareaExportarReporte(self.resumen_ventas, carpeta, self.cola_tareas)
        self.hilo_export = threading.Thread(
            target=tarea.run, name="HiloExportarReporte", daemon=True
        )
        self.estado_export = {"estado": "guardando", "ruta": ""}
        self.hilo_export.start()
        return True, ""

    def hay_tareas_activas(self):
        return self.estado_carga["estado"] in (
            "cargando",
            "cancelando",
        ) or self.estado_export["estado"] == "guardando"

    def sondear_tareas(self):
        while True:
            try:
                msg = self.cola_tareas.get_nowait()
            except queue.Empty:
                return
            self._aplicar_mensaje(msg)

    def _aplicar_mensaje(self, msg):
        tipo = msg["tipo"]
        if msg["tarea"] == "carga":
            e = self.estado_carga
            if tipo == "progreso":
                e["porcentaje"], e["leidas"] = msg["porcentaje"], msg["leidas"]
            elif tipo == "terminado":
                self.resumen_ventas = msg["resumen"]
                e.update(estado="terminado", porcentaje=100.0, leidas=msg["leidas"])
            elif tipo == "cancelado":
                e["estado"] = "cancelado"
            elif tipo == "error":
                e.update(estado="error", mensaje=msg["mensaje"])
                self._notificaciones.append(
                    ("error", "Error al cargar ventas", msg["mensaje"])
                )
        else:
            if tipo == "terminado":
                self.estado_export = {"estado": "terminado", "ruta": msg["ruta"]}
                self._notificaciones.append((
                    "info",
                    "Reporte generado",
                    f"El reporte se guardó en:\n{os.path.abspath(msg['ruta'])}",
                ))
            elif tipo == "error":
                self.estado_export = {"estado": "error", "ruta": ""}
                self._notificaciones.append(
                    ("error", "No se pudo guardar el reporte", msg["mensaje"])
                )

    def tomar_notificaciones(self):
        pendientes, self._notificaciones = self._notificaciones, []
        return pendientes

    # ---------------- REPORTES ----------------
    def obtener_anios_reportes(self):
        return self.modelo.obtener_anios_disponibles()

    def obtener_reporte_ganancias(self, anio=None, mes=None, dia=None):
        return self.modelo.obtener_reporte_ganancias(anio=anio, mes=mes, dia=dia)

    def obtener_datos_grafica(self, anio=None, mes=None, dia=None, caja=None):
        return self.modelo.obtener_datos_grafica(anio=anio, mes=mes, dia=dia, caja_filtro=caja)

    # ---------------- INVENTARIO ----------------
    def registrar_merma(self, id_producto, cantidad, motivo):
        return self.modelo.registrar_merma(id_producto, cantidad, motivo)

    def obtener_inventario_filtrado(self, texto, marca, categoria):
        productos = self.modelo.inventario
        filtrados = []
        texto_busqueda = (texto or "").strip().lower()

        for p in productos:
            nombre_prod = p["nombre"].lower()
            codigo_prod = str(p.get("codigo_barras") or "").lower()

            if texto_busqueda and not (
                nombre_prod.startswith(texto_busqueda) or codigo_prod.startswith(texto_busqueda)
            ):
                continue

            if marca != "Todas" and p["marca"] != marca:
                continue
            if categoria != "Todas" and p["categoria"] != categoria:
                continue

            filtrados.append(p)

        return filtrados

    # ---------------- PROVEEDORES Y PEDIDOS ----------------
    def obtener_proveedores(self):
        return self.modelo.obtener_proveedores()

    def obtener_productos_proveedor(self, id_proveedor):
        return self.modelo.obtener_productos_proveedor(id_proveedor)

    def crear_pedido_manual(self, id_proveedor, articulos):
        return self.repo_pedidos.crear_pedido_manual(id_proveedor, self.id_usuario_actual, articulos)

    def obtener_pedidos_activos(self):
        return self.modelo.obtener_pedidos_activos()

    def recibir_pedido(self, id_pedido):
        return self.modelo.recibir_pedido_proveedor(id_pedido)

    def eliminar_proveedor(self, id_proveedor):
        return self.modelo.eliminar_proveedor(id_proveedor)

    def crear_proveedor(self, empresa, telefono, correo):
        if not (empresa or "").strip():
            return False, "El nombre de la empresa es obligatorio."
        return self.modelo.crear_proveedor(empresa, telefono or "", correo or "")

    def actualizar_proveedor(self, id_proveedor, empresa, telefono, correo):
        if not (empresa or "").strip():
            return False, "El nombre de la empresa es obligatorio."
        return self.modelo.actualizar_proveedor(id_proveedor, empresa, telefono or "", correo or "")

    # ---------------- APARTADOS ----------------
    def obtener_lista_apartados(self):
        return self.modelo.obtener_apartados()

    def registrar_apartado(self, nombre, telefono, fecha, articulos, pagos):
        try:
            self.repo_apartados.registrar_apartado(nombre, telefono, fecha, articulos, self.id_turno_actual, pagos)
            self.modelo.invalidar_inventario()
            return True, "Apartado registrado con éxito y stock reservado."
        except Exception as e:
            return False, str(e)

    def liquidar_apartado(self, id_apartado, pagos):
        return self.repo_apartados.liquidar_apartado(id_apartado, pagos, self.id_turno_actual)

    def cancelar_apartado(self, id_apartado):
        ok, msg = self.repo_apartados.cancelar_apartado(id_apartado)
        if ok:
            self.modelo.invalidar_inventario()
        return ok, msg

    # ---------------- VENTAS Y COBROS ----------------
    def procesar_cobro_avanzado(self, pagos, datos_factura):
        if not self.modelo.ticket_actual:
            return False, "Carrito vacío.", None
        total = self.modelo.calcular_total()
        total_pagado = round(sum(float(p["monto"]) for p in pagos), 2)
        if total_pagado < total:
            return False, f"Faltan ${total - total_pagado:.2f}", None

        try:
            resumen_venta = self.repo_ventas.registrar(
                self.modelo.ticket_actual,
                pagos,
                self.id_turno_actual,
                datos_factura,
            )
            self.modelo.ticket_actual.clear()
            self.modelo.invalidar_inventario()
            return True, f"Venta {resumen_venta['folio']} exitosa. Cambio: ${resumen_venta['cambio']:.2f}", resumen_venta
        except Exception as e:
            return False, str(e), None

    def obtener_datos_ventas(self):
        return self.modelo.inventario, self.modelo.ticket_actual, self.modelo.calcular_total()

    def obtener_nombres_productos(self):
        return [p["nombre"] for p in self.modelo.inventario]

    def vaciar_ticket_actual(self):
        self.modelo.ticket_actual.clear()

    def procesar_agregar(self, producto_diccionario, cantidad):
        res = self.modelo.agregar_al_ticket(producto_diccionario["nombre"], cantidad)
        if res == "stock_insuficiente":
            messagebox.showwarning("Sin stock", f"No hay existencias suficientes de {producto_diccionario['nombre']}.")
            return False
        return True

    def obtener_desglose_ticket(self):
        return self.modelo.calcular_desglose()

    def actualizar_cantidad_ticket(self, nombre_producto, delta):
        return self.modelo.actualizar_cantidad_ticket(nombre_producto, delta)

    def quitar_del_ticket(self, nombre_producto):
        return self.modelo.quitar_del_ticket(nombre_producto)

    def buscar_producto_por_codigo(self, codigo):
        codigo_limpio = (codigo or "").strip().lower()
        if not codigo_limpio:
            return None
        return next(
            (p for p in self.modelo.inventario if str(p.get("codigo_barras") or "").strip().lower() == codigo_limpio),
            None,
        )

    # ---------------- CATÁLOGOS Y CRUD DE PRODUCTOS ----------------
    def obtener_marcas(self):
        return self.modelo.obtener_marcas()

    def obtener_categorias(self):
        return self.modelo.obtener_categorias()

    def obtener_unidades(self):
        return self.modelo.obtener_unidades()

    def crear_producto(self, datos):
        if datos.get("precio_venta", 0) <= 0:
            return False, "El precio de venta debe ser mayor a 0."
        if datos.get("stock_actual", 0) < 0:
            return False, "El stock actual no puede ser negativo."
        if not datos.get("nombre_dulce"):
            return False, "El nombre del producto no puede estar vacío."
        return self.modelo.crear_producto(datos)

    def actualizar_producto(self, id_producto, datos):
        if datos.get("precio_venta", 0) <= 0:
            return False, "El precio de venta debe ser mayor a 0."
        if datos.get("stock_actual", 0) < 0:
            return False, "El stock actual no puede ser negativo."
        if not datos.get("nombre_dulce"):
            return False, "El nombre del producto no puede estar vacío."
        return self.modelo.actualizar_producto(id_producto, datos)

    def eliminar_producto(self, id_producto):
        if self.rol_actual != "Administrador":
            return False, "Solo un administrador puede eliminar productos."
        return self.modelo.eliminar_producto(id_producto)