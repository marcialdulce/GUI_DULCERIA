import contextlib
import inspect
import os
import tempfile
import threading
import flet as ft
from modelos.modelo import ModeloDulceria
from servicios.repositorio_ventas import RepositorioVentas
from vistas.generador_tickets import generar_comprobante_ticket_pdf, generar_ticket_pdf

ICONS = getattr(ft, "Icons", getattr(ft, "icons", None))
BTN_CLS = getattr(ft, "Button", getattr(ft, "ElevatedButton", None))
OPT_CLS = getattr(ft, "DropdownOption", None) or ft.dropdown.Option
ALIGN_CENTER = getattr(ft.Alignment, "CENTER", ft.Alignment(0, 0))
TEXT_OVERFLOW = getattr(getattr(ft, "TextOverflow", None), "ELLIPSIS", None)

ICON_TIENDA = getattr(ICONS, "STOREFRONT", getattr(ICONS, "STORE", ICONS.POINT_OF_SALE))
ICON_DESCARGA = getattr(ICONS, "DOWNLOAD", getattr(ICONS, "FILE_DOWNLOAD", ICONS.RECEIPT_LONG))
ICON_ALERTA = getattr(ICONS, "WARNING_AMBER_ROUNDED", getattr(ICONS, "WARNING", ICONS.INFO))

COLOR_MARCA = "#C2284E"
COLOR_FONDO = "#FFF8F5"
COLOR_AMARILLO = "#F4D03F"
COLOR_VERDE = "#27AE60"
COLOR_ROJO = "#C0392B"
COLOR_AZUL = "#3A8D96"
COLOR_MORADO = "#8E44AD"
COLOR_BLANCO = "#FFFFFF"
COLOR_NEGRO = "#000000"
COLOR_GRIS_CLARO = "#F4F4F4"
COLOR_BORDE = "#DDDDDD"
COLOR_TEXTO_SEC = "#555555"
COLOR_TEXTO_SUAVE = "#666666"

METODO_EFECTIVO = "Efectivo"
METODO_DEBITO = "Tarjeta de débito"
METODO_CREDITO = "Tarjeta de crédito"
METODOS_ID = {
    METODO_EFECTIVO: 1,
    METODO_DEBITO: 2,
    METODO_CREDITO: 3,
}
NOMBRES_METODO = {
    1: METODO_EFECTIVO,
    2: "Tarjeta débito",
    3: "Tarjeta crédito",
}
ESTADO_SIN_FACTURA = "Sin Factura"
TXT_ACTUALIZAR = "ACTUALIZAR"
TXT_DESCARGAR_PDF = "DESCARGAR PDF"
TXT_CERRAR = "Cerrar"
FMT_FECHA = "%Y-%m-%d %H:%M:%S"

LIMITE_RENDER = 20
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_ASSETS = os.path.join(BASE_DIR, "assets")
DIR_FONTS = os.path.join(DIR_ASSETS, "fonts")


def _carpeta_escribible(ruta):
    if not ruta:
        return False
    try:
        os.makedirs(ruta, exist_ok=True)
        prueba = os.path.join(ruta, ".write_test")
        with open(prueba, "w", encoding="utf-8") as archivo:
            archivo.write("ok")
        os.remove(prueba)
        return True
    except OSError:
        return False


def obtener_dir_tickets(es_web=False):
    if es_web:
        ruta_web = os.path.join(DIR_ASSETS, "tickets")
        if _carpeta_escribible(ruta_web):
            return ruta_web

    app_data = os.getenv("FLET_APP_STORAGE_DATA")
    app_temp = os.getenv("FLET_APP_STORAGE_TEMP")
    candidatos = [
        "/storage/emulated/0/Download/Algorrico_Tickets",
        os.path.join(app_data, "tickets") if app_data else "",
        os.path.join(app_temp, "tickets") if app_temp else "",
        os.path.join(DIR_ASSETS, "tickets"),
        os.path.join(tempfile.gettempdir(), "algorrico_tickets"),
    ]
    for ruta in candidatos:
        if _carpeta_escribible(ruta):
            return ruta
    return tempfile.gettempdir()


def detectar_fuente_local():
    if not os.path.isdir(DIR_FONTS):
        return None
    preferidas = (
        "Roboto-Regular.ttf",
        "NotoSans-Regular.ttf",
        "Inter-Regular.ttf",
        "OpenSans-Regular.ttf",
    )
    for nombre in preferidas:
        if os.path.isfile(os.path.join(DIR_FONTS, nombre)):
            return f"/fonts/{nombre}"
    for archivo in sorted(os.listdir(DIR_FONTS)):
        if archivo.lower().endswith(".ttf"):
            return f"/fonts/{archivo}"
    return None


def borde_all(ancho, color):
    clase = getattr(ft, "Border", None)
    if clase and hasattr(clase, "all"):
        return clase.all(ancho, color)
    return ft.border.all(ancho, color)


def crear_texto(valor, **kwargs):
    if TEXT_OVERFLOW is not None and "overflow" not in kwargs and "max_lines" in kwargs:
        kwargs["overflow"] = TEXT_OVERFLOW
    return ft.Text(valor, **kwargs)


def crear_boton(texto, on_click=None, bgcolor=None, color=None, icon=None, **extra):
    lbl = crear_texto(
        texto,
        color=color,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
        no_wrap=False,
        max_lines=2,
    )
    contenido = lbl
    if icon is not None:
        contenido = ft.Row(
            controls=[ft.Icon(icon, color=color, size=18), lbl],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            tight=True,
        )
    kwargs = {
        "content": contenido,
        "bgcolor": bgcolor,
        "color": color,
        "on_click": on_click,
        **extra,
    }
    return BTN_CLS(**kwargs)


def conectar_dropdown(cmb, callback):
    if hasattr(cmb, "on_select"):
        cmb.on_select = callback
    else:
        cmb.on_change = callback


def _limpiar_nombre_archivo(valor, defecto):
    return str(valor or defecto).replace("/", "_").replace(" ", "_")


def _formatear_fecha(valor):
    if hasattr(valor, "strftime"):
        return valor.strftime(FMT_FECHA)
    return str(valor or "")


class AppMovil:
    def __init__(self, page: ft.Page):
        self.page = page
        self.es_web = bool(getattr(page, "web", False))
        self.modelo = ModeloDulceria()
        self.repo_ventas = RepositorioVentas()
        self.contenedor_cuerpo = ft.Container(padding=12, expand=True)

        self.usuario = None
        self.id_usuario = None
        self.rol = None
        self.id_turno = None
        self.vista_actual = 0
        self.pagos = []
        self.datos_factura = None
        self.ventas_turno_cache = None
        self.ultimo_comprobante = None

        self._configurar_pagina()

    def _configurar_pagina(self):
        self.page.title = "Dulcería Algorrico - Caja Móvil"
        self.page.bgcolor = COLOR_FONDO
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.ADAPTIVE

        # Carga fuente local para evitar fallos de texto en Android
        ruta_fuente = detectar_fuente_local()
        if ruta_fuente:
            self.page.fonts = {"AlgorricoFont": ruta_fuente}
            fuente = "AlgorricoFont"
        else:
            fuente = "Roboto"

        self.page.theme = ft.Theme(
            color_scheme_seed=COLOR_MARCA,
            font_family=fuente,
            use_material3=True,
        )

    def safe_update(self):
        with contextlib.suppress(Exception):
            self.page.update()

    def abrir_url_segura(self, url_destino):
        with contextlib.suppress(Exception):
            fn = getattr(self.page, "launch_url", None)
            if callable(fn):
                if inspect.iscoroutinefunction(fn):
                    self.page.run_task(fn, url_destino)
                else:
                    fn(url_destino)

    def mostrar_aviso(self, mensaje, color=COLOR_VERDE):
        kwargs_sb = {
            "content": ft.Container(
                padding=4,
                content=crear_texto(
                    str(mensaje),
                    color=COLOR_BLANCO,
                    size=14,
                    weight=ft.FontWeight.W_500,
                    no_wrap=False,
                    max_lines=3,
                ),
            ),
            "bgcolor": color,
            "duration": 3500,
        }
        if hasattr(ft, "SnackBarBehavior"):
            kwargs_sb["behavior"] = ft.SnackBarBehavior.FLOATING
        sb = ft.SnackBar(**kwargs_sb)
        self._mostrar_overlay(sb)

    def _mostrar_overlay(self, control):
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(control)
        elif hasattr(self.page, "open"):
            self.page.open(control)
        else:
            self.page.overlay.append(control)
            control.open = True
            self.safe_update()

    def abrir_dialogo(self, dlg):
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(dlg)
        elif hasattr(self.page, "open"):
            self.page.open(dlg)
        else:
            self.page.dialog = dlg
            dlg.open = True
            self.safe_update()

    def cerrar_dialogo(self, dlg):
        if hasattr(self.page, "pop_dialog"):
            self.page.pop_dialog()
        elif hasattr(self.page, "close"):
            self.page.close(dlg)
        else:
            dlg.open = False
            self.safe_update()

    def obtener_ventas_del_turno(self, id_turno):
        if not id_turno:
            return []
        if hasattr(self.repo_ventas, "obtener_por_turno"):
            return self.repo_ventas.obtener_por_turno(id_turno) or []
        return self._consultar_ventas_turno_respaldo(id_turno)

    def _consultar_ventas_turno_respaldo(self, id_turno):
        rows = self.modelo._ejecutar_consulta(
            """
            SELECT v.id_venta, v.folio, v.fecha_hora,
                   v.subtotal, v.impuesto, (v.subtotal + v.impuesto) AS total,
                   COALESCE((SELECT mp.nombre_metodo_pago FROM pagos_ventas pv
                             JOIN metodos_pago mp ON pv.id_metodo_pago = mp.id_metodo_pago
                             WHERE pv.id_venta = v.id_venta LIMIT 1), 'Efectivo') AS metodo_pago,
                   CASE WHEN f.id_factura IS NOT NULL THEN 'Facturada' ELSE 'Sin Factura' END AS estado_factura,
                   f.folio AS folio_factura
            FROM ventas v
            LEFT JOIN facturas f ON v.id_venta = f.id_venta
            WHERE v.id_corte_caja = %s
            ORDER BY v.id_venta DESC
            """,
            (id_turno,),
            fetchall=True,
        ) or []
        if not rows:
            return []

        ids = [r["id_venta"] for r in rows]
        ph = ", ".join(["%s"] * len(ids))
        detalles = self.modelo._ejecutar_consulta(
            f"""
            SELECT dv.id_venta, p.nombre_dulce AS producto, dv.cantidad, dv.precio_unitario, dv.subtotal
            FROM detalles_ventas dv
            JOIN productos p ON dv.id_producto = p.id_producto
            WHERE dv.id_venta IN ({ph})
            """,
            tuple(ids),
            fetchall=True,
        ) or []

        mapa = {vid: [] for vid in ids}
        for det in detalles:
            mapa[det["id_venta"]].append({
                "producto": det["producto"],
                "cantidad": int(det["cantidad"]),
                "precio_unitario": float(det.get("precio_unitario") or 0),
                "subtotal": float(det["subtotal"]),
            })

        for row in rows:
            row["fecha"] = _formatear_fecha(row.get("fecha_hora"))
            row["articulos"] = mapa.get(row["id_venta"], [])
            row["total"] = float(row["total"])
            row["subtotal"] = float(row.get("subtotal") or 0)
            row["impuesto"] = float(row.get("impuesto") or 0)
        return rows

    def preparar_pdf_ticket(self, venta):
        folio = _limpiar_nombre_archivo(venta.get("folio"), "venta")
        nombre_pdf = f"Ticket_{folio}.pdf"
        ruta_pdf = os.path.join(obtener_dir_tickets(self.es_web), nombre_pdf)
        generar_comprobante_ticket_pdf(ruta_pdf, venta)
        url_web = f"/tickets/{nombre_pdf}" if self.es_web else None
        return ruta_pdf, url_web

    def preparar_pdf_factura(self, venta, factura):
        folio = _limpiar_nombre_archivo(venta.get("folio_factura") or venta.get("folio"), "venta")
        rfc = _limpiar_nombre_archivo(factura.get("rfc"), "XAXX010101000")
        nombre_pdf = f"Factura_{folio}_{rfc}.pdf"
        ruta_pdf = os.path.join(obtener_dir_tickets(self.es_web), nombre_pdf)
        generar_ticket_pdf(
            ruta_completa=ruta_pdf,
            rfc=rfc,
            razon_social=factura.get("razon_social", ""),
            total=venta["total"],
            carrito_comprado=venta["articulos"],
            metodo_pago=venta["metodo_pago"],
            pago=venta["total_pagado"],
            cambio=venta["cambio"],
            regimen_fiscal=factura.get("regimen", ""),
            cp_fiscal=factura.get("cp", ""),
            correo=factura.get("correo", ""),
            folio_factura=folio,
        )
        url_web = f"/tickets/{nombre_pdf}" if self.es_web else None
        return ruta_pdf, url_web

    def _abrir_pdf_local(self, ruta_pdf):
        with contextlib.suppress(Exception):
            if os.name == "nt":
                os.startfile(ruta_pdf)
            else:
                self.abrir_url_segura(f"file://{ruta_pdf}")

    def descargar_comprobante_ticket(self, venta):
        try:
            ruta_pdf, url_web = self.preparar_pdf_ticket(venta)
        except Exception as ex:
            self.mostrar_aviso(f"No se pudo generar el PDF: {ex}", COLOR_ROJO)
            return

        folio = venta.get("folio", "Ticket")
        if self.es_web and url_web:
            self.abrir_url_segura(url_web)
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Ticket {folio} listo"),
                content=ft.Text(
                    "El comprobante PDF se generó correctamente. Si no inició la descarga, toca el botón de abajo.",
                    size=13,
                ),
                actions=[
                    ft.TextButton(content=ft.Text(TXT_CERRAR), on_click=lambda _: self.cerrar_dialogo(dlg)),
                    crear_boton(
                        TXT_DESCARGAR_PDF,
                        bgcolor=COLOR_AMARILLO,
                        color=COLOR_NEGRO,
                        icon=ICON_DESCARGA,
                        url=url_web,
                    ),
                ],
            )
            self.abrir_dialogo(dlg)
            return

        self._abrir_pdf_local(ruta_pdf)
        dlg_ok = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Ticket {folio} guardado"),
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=[
                    ft.Text("El ticket PDF se guardó en el dispositivo.", size=13),
                    ft.Container(
                        bgcolor=COLOR_GRIS_CLARO,
                        border=borde_all(1, COLOR_BORDE),
                        border_radius=6,
                        padding=8,
                        content=ft.Text(ruta_pdf, size=11, selectable=True, color="#333333"),
                    ),
                ],
            ),
            actions=[
                crear_boton("ACEPTAR", on_click=lambda _: self.cerrar_dialogo(dlg_ok), bgcolor=COLOR_VERDE, color=COLOR_BLANCO),
            ],
        )
        self.abrir_dialogo(dlg_ok)

    def descargar_comprobante_factura(self, venta, factura):
        try:
            ruta_pdf, url_web = self.preparar_pdf_factura(venta, factura)
        except Exception as ex:
            self.mostrar_aviso(f"No se pudo generar la factura PDF: {ex}", COLOR_ROJO)
            return

        folio = venta.get("folio_factura") or venta.get("folio", "Factura")
        if self.es_web and url_web:
            self.abrir_url_segura(url_web)
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Factura {folio} lista"),
                content=ft.Text(
                    "La factura PDF se generó correctamente. Si no inició la descarga, toca el botón de abajo.",
                    size=13,
                ),
                actions=[
                    ft.TextButton(content=ft.Text(TXT_CERRAR), on_click=lambda _: self.cerrar_dialogo(dlg)),
                    crear_boton(
                        "DESCARGAR FACTURA",
                        bgcolor=COLOR_MORADO,
                        color=COLOR_BLANCO,
                        icon=ICON_DESCARGA,
                        url=url_web,
                    ),
                ],
            )
            self.abrir_dialogo(dlg)
            return

        self._abrir_pdf_local(ruta_pdf)
        self.mostrar_aviso(f"Factura guardada en: {ruta_pdf}", COLOR_VERDE)

    def _abrir_o_recuperar_turno(self, id_usuario, num_caja):
        corte = self.modelo._ejecutar_consulta(
            """SELECT id_corte_caja FROM cortes_caja
               WHERE id_usuario = %s AND estado = 'abierto'
               ORDER BY id_corte_caja DESC LIMIT 1""",
            (id_usuario,),
            fetch=True,
        )
        if corte:
            return corte["id_corte_caja"]
        return self.modelo._ejecutar_consulta(
            "INSERT INTO cortes_caja (fondo_inicial, id_usuario, id_caja) VALUES (500.00, %s, %s)",
            (id_usuario, num_caja),
        )

    def _procesar_login(self, usuario, password, caja_str):
        if not usuario or not password:
            self.mostrar_aviso("Ingresa usuario y contraseña.", COLOR_ROJO)
            return

        try:
            user_data = self.modelo.validar_usuario(usuario, password)
        except Exception as ex:
            self.mostrar_aviso(f"Error de conexión con la base de datos: {ex}", COLOR_ROJO)
            return

        if not user_data:
            self.mostrar_aviso("Usuario o contraseña incorrectos.", COLOR_ROJO)
            return

        rol = self.modelo.obtener_rol(user_data["id_rol"])
        if rol.strip().lower() != "cajero":
            self.mostrar_aviso("Acceso exclusivo para Cajeros. Usa la versión de escritorio.", COLOR_ROJO)
            return

        try:
            id_turno = self._abrir_o_recuperar_turno(user_data["id_usuario"], int(caja_str or 1))
        except Exception as ex:
            self.mostrar_aviso(f"No se pudo abrir el turno de caja: {ex}", COLOR_ROJO)
            return

        self.usuario = usuario
        self.id_usuario = user_data["id_usuario"]
        self.rol = rol
        self.id_turno = id_turno
        self.ventas_turno_cache = None
        self.datos_factura = None
        self.ultimo_comprobante = None
        self.pagos.clear()
        self.modelo.ticket_actual.clear()

        self.mostrar_aviso(f"Turno #{id_turno} activo - {usuario}", COLOR_VERDE)
        self.cargar_layout_principal()

    def mostrar_login(self):
        self.page.appbar = None
        self.page.navigation_bar = None
        self.page.controls.clear()

        txt_user = ft.TextField(label="Usuario", width=290, bgcolor=COLOR_BLANCO)
        txt_pass = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            width=290,
            bgcolor=COLOR_BLANCO,
        )
        cmb_caja = ft.Dropdown(
            label="Caja a operar (1-4)",
            width=290,
            value="1",
            options=[OPT_CLS(key=str(i), text=f"CAJA-0{i}") for i in range(1, 5)],
        )

        def on_ingresar(_):
            self._procesar_login(
                (txt_user.value or "").strip(),
                (txt_pass.value or "").strip(),
                cmb_caja.value,
            )

        txt_pass.on_submit = on_ingresar

        tarjeta = ft.Container(
            bgcolor=COLOR_BLANCO,
            border=borde_all(2, "#F3C6D1"),
            border_radius=12,
            padding=24,
            width=340,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Icon(ICON_TIENDA, color=COLOR_MARCA, size=32),
                            ft.Text("Algorrico", size=28, weight=ft.FontWeight.BOLD, color=COLOR_MARCA),
                        ],
                    ),
                    ft.Text("Caja Móvil - Exclusivo Cajero", size=14, color=COLOR_TEXTO_SEC),
                    txt_user,
                    txt_pass,
                    cmb_caja,
                    crear_boton(
                        "ABRIR CAJA E INGRESAR",
                        on_click=on_ingresar,
                        bgcolor=COLOR_MARCA,
                        color=COLOR_BLANCO,
                        width=290,
                        height=44,
                    ),
                ],
            ),
        )

        self.page.add(ft.Container(expand=True, alignment=ALIGN_CENTER, padding=16, content=tarjeta))
        self.safe_update()

    def _tarjeta_item_carrito(self, item, on_modificar, on_quitar):
        nombre = item["producto"]
        return ft.Container(
            bgcolor=COLOR_BLANCO,
            border=borde_all(1, COLOR_BORDE),
            border_radius=8,
            padding=8,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            crear_texto(nombre, weight=ft.FontWeight.BOLD, size=13, max_lines=2),
                            ft.Text(
                                f"Cant: {item['cantidad']}  |  ${float(item['subtotal']):.2f}",
                                size=12,
                                color=COLOR_TEXTO_SEC,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=0,
                        tight=True,
                        controls=[
                            ft.IconButton(
                                icon=ICONS.REMOVE_CIRCLE_OUTLINE,
                                icon_color="#E67E22",
                                on_click=lambda _, n=nombre: on_modificar(n, -1),
                            ),
                            ft.IconButton(
                                icon=ICONS.ADD_CIRCLE_OUTLINE,
                                icon_color=COLOR_VERDE,
                                on_click=lambda _, n=nombre: on_modificar(n, 1),
                            ),
                            ft.IconButton(
                                icon=ICONS.DELETE_OUTLINE,
                                icon_color=COLOR_ROJO,
                                on_click=lambda _, n=nombre: on_quitar(n),
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _tarjeta_producto(self, prod, on_agregar):
        color_stock = COLOR_ROJO if prod["stock"] <= prod.get("stock_minimo", 5) else COLOR_TEXTO_SEC
        return ft.Container(
            bgcolor=COLOR_BLANCO,
            border=borde_all(1, COLOR_BORDE),
            border_radius=8,
            padding=10,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            crear_texto(prod["nombre"], weight=ft.FontWeight.BOLD, size=13, max_lines=2),
                            ft.Text(f"${prod['precio']:.2f}  |  Stock: {prod['stock']}", size=12, color=color_stock),
                        ],
                    ),
                    crear_boton(
                        "+1",
                        on_click=lambda _, p=prod: on_agregar(p),
                        bgcolor=COLOR_AMARILLO,
                        color=COLOR_NEGRO,
                    ),
                ],
            ),
        )

    def _filtrar_productos(self, texto):
        prods = [p for p in self.modelo.inventario if p["stock"] > 0]
        if not texto:
            return prods[:LIMITE_RENDER]
        return [
            p
            for p in prods
            if texto in p["nombre"].lower() or texto in str(p.get("codigo_barras") or "").lower()
        ][:LIMITE_RENDER]

    def _agregar_item_carrito(self, prod, refrescar_fn):
        if self.modelo.agregar_al_ticket(prod["nombre"], 1) == "stock_insuficiente":
            self.mostrar_aviso(f"Sin stock suficiente de {prod['nombre']}.", COLOR_ROJO)
            return
        refrescar_fn()

    def _modificar_item_carrito(self, nombre, delta, refrescar_fn):
        ok, msg = self.modelo.actualizar_cantidad_ticket(nombre, delta)
        if not ok:
            self.mostrar_aviso(msg, COLOR_ROJO)
            return
        refrescar_fn()

    def _quitar_item_carrito(self, nombre, refrescar_fn):
        self.modelo.quitar_del_ticket(nombre)
        refrescar_fn()

    def _limpiar_carrito(self, refrescar_fn):
        self.modelo.ticket_actual.clear()
        self.pagos.clear()
        self.datos_factura = None
        refrescar_fn()

    def _pintar_carrito(self, lista_carrito, lbl_desglose, lbl_total, refrescar_fn):
        lista_carrito.controls.clear()
        if not self.modelo.ticket_actual:
            lista_carrito.controls.append(
                ft.Text("Carrito vacío. Agrega productos desde el catálogo de abajo.", size=12, color="#777777")
            )
        else:
            def on_mod(nombre, delta):
                self._modificar_item_carrito(nombre, delta, refrescar_fn)

            def on_del(nombre):
                self._quitar_item_carrito(nombre, refrescar_fn)

            for item in self.modelo.ticket_actual:
                lista_carrito.controls.append(self._tarjeta_item_carrito(item, on_mod, on_del))

        sub, iva, total = self.modelo.calcular_desglose()
        lbl_desglose.value = f"Subtotal: ${sub:.2f}  |  IVA (16%): ${iva:.2f}"
        lbl_total.value = f"TOTAL (IVA incl.): ${total:.2f}"
        self.safe_update()

    def _pintar_catalogo(self, lista_prods, texto_busqueda, on_agregar):
        lista_prods.controls.clear()
        prods = self._filtrar_productos((texto_busqueda or "").strip().lower())
        if not prods:
            lista_prods.controls.append(
                ft.Text("No se encontraron productos disponibles.", size=13, color=COLOR_TEXTO_SUAVE)
            )
        else:
            for prod in prods:
                lista_prods.controls.append(self._tarjeta_producto(prod, on_agregar))
        self.safe_update()

    def vista_punto_venta(self):
        txt_buscar = ft.TextField(label="Buscar producto (nombre o código)", bgcolor=COLOR_BLANCO, dense=True)
        lista_prods = ft.Column(spacing=6)
        lista_carrito = ft.Column(spacing=6)
        lbl_desglose = ft.Text("", size=12, color=COLOR_TEXTO_SEC)
        lbl_total = ft.Text("TOTAL: $0.00", size=18, weight=ft.FontWeight.BOLD, color=COLOR_VERDE)

        def refrescar_carrito():
            self._pintar_carrito(lista_carrito, lbl_desglose, lbl_total, refrescar_carrito)

        def refrescar_catalogo(_=None):
            self._pintar_catalogo(
                lista_prods,
                txt_buscar.value,
                lambda prod: self._agregar_item_carrito(prod, refrescar_carrito),
            )

        txt_buscar.on_change = refrescar_catalogo
        refrescar_catalogo()
        refrescar_carrito()

        # Ticket arriba y catálogo abajo para pantallas móviles
        panel_carrito = ft.Container(
            col={"xs": 12, "md": 6},
            bgcolor=COLOR_GRIS_CLARO,
            border=borde_all(1, "#CCCCCC"),
            border_radius=10,
            padding=12,
            content=ft.Column(
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Ticket de Venta", weight=ft.FontWeight.BOLD, size=16, color=COLOR_MARCA),
                            ft.Text(f"Turno #{self.id_turno}", size=12, color=COLOR_TEXTO_SUAVE),
                        ],
                    ),
                    lista_carrito,
                    ft.Divider(),
                    lbl_desglose,
                    lbl_total,
                    crear_boton(
                        "CONTINUAR A COBROS Y PAGOS",
                        on_click=lambda _: self.cambiar_seccion(1),
                        bgcolor=COLOR_AMARILLO,
                        color=COLOR_NEGRO,
                        height=44,
                    ),
                    crear_boton(
                        "LIMPIAR CARRITO",
                        on_click=lambda _: self._limpiar_carrito(refrescar_carrito),
                        bgcolor=COLOR_ROJO,
                        color=COLOR_BLANCO,
                        height=40,
                    ),
                ],
            ),
        )

        panel_catalogo = ft.Container(
            col={"xs": 12, "md": 6},
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text("Catálogo de Productos", weight=ft.FontWeight.BOLD, size=16, color=COLOR_MARCA),
                    txt_buscar,
                    lista_prods,
                ],
            ),
        )

        return ft.ResponsiveRow(controls=[panel_carrito, panel_catalogo], spacing=12, run_spacing=12)

    def _abrir_modal_factura(self, on_actualizado):
        actual = self.datos_factura or {}
        e_rfc = ft.TextField(label="RFC", value=actual.get("rfc", ""), bgcolor=COLOR_BLANCO, dense=True)
        e_razon = ft.TextField(label="Razón Social", value=actual.get("razon_social", ""), bgcolor=COLOR_BLANCO, dense=True)
        e_regimen = ft.TextField(label="Régimen Fiscal", value=actual.get("regimen", ""), bgcolor=COLOR_BLANCO, dense=True)
        e_cp = ft.TextField(label="Código Postal", value=actual.get("cp", ""), bgcolor=COLOR_BLANCO, dense=True)
        e_correo = ft.TextField(label="Correo", value=actual.get("correo", ""), bgcolor=COLOR_BLANCO, dense=True)

        def guardar_fac(_):
            vals = {
                "rfc": (e_rfc.value or "").strip().upper(),
                "razon_social": (e_razon.value or "").strip(),
                "regimen": (e_regimen.value or "").strip(),
                "cp": (e_cp.value or "").strip(),
                "correo": (e_correo.value or "").strip(),
            }
            if not all(vals.values()):
                self.mostrar_aviso("Completa todos los datos fiscales.", COLOR_ROJO)
                return
            self.datos_factura = vals
            self.cerrar_dialogo(dlg_fac)
            on_actualizado()

        def quitar_fac(_):
            self.datos_factura = None
            self.cerrar_dialogo(dlg_fac)
            on_actualizado()

        acciones = [ft.TextButton(content=ft.Text("Cancelar"), on_click=lambda _: self.cerrar_dialogo(dlg_fac))]
        if self.datos_factura:
            acciones.append(crear_boton("Quitar", on_click=quitar_fac, bgcolor=COLOR_ROJO, color=COLOR_BLANCO))
        acciones.append(crear_boton("Guardar", on_click=guardar_fac, bgcolor=COLOR_VERDE, color=COLOR_BLANCO))

        dlg_fac = ft.AlertDialog(
            modal=True,
            title=ft.Text("Datos de Facturación"),
            content=ft.Column(
                tight=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=8,
                controls=[e_rfc, e_razon, e_regimen, e_cp, e_correo],
            ),
            actions=acciones,
        )
        self.abrir_dialogo(dlg_fac)

    def _confirmar_cobro(self, on_actualizado):
        if not self.modelo.ticket_actual:
            self.mostrar_aviso("El carrito está vacío. Agrega productos en Venta.", COLOR_ROJO)
            return

        total = self.modelo.calcular_total()
        pagado = round(sum(p["monto"] for p in self.pagos), 2)
        if pagado < total:
            self.mostrar_aviso(f"Faltan ${total - pagado:.2f} por cubrir.", COLOR_ROJO)
            return

        factura_actual = self.datos_factura.copy() if self.datos_factura else None
        detalle_items = "\n".join(
            f"- {i['producto']} x{i['cantidad']} (${float(i['subtotal']):.2f})"
            for i in self.modelo.ticket_actual
        )

        def ejecutar_cobro(_):
            self.cerrar_dialogo(dlg_conf)
            try:
                resumen = self.repo_ventas.registrar(
                    self.modelo.ticket_actual,
                    self.pagos,
                    self.id_turno,
                    datos_factura=factura_actual,
                )
            except Exception as ex:
                self.mostrar_aviso(f"Error al cobrar: {ex}", COLOR_ROJO)
                return

            self.ultimo_comprobante = {"venta": resumen, "factura": factura_actual}
            self.modelo.ticket_actual.clear()
            self.pagos.clear()
            self.datos_factura = None
            self.modelo.invalidar_inventario()
            self.ventas_turno_cache = None
            self.mostrar_aviso(f"Venta {resumen['folio']} registrada. Cambio: ${resumen['cambio']:.2f}", COLOR_VERDE)
            on_actualizado()

        rfc_texto = factura_actual["rfc"] if factura_actual else "No solicitada"
        dlg_conf = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Venta"),
            content=ft.Column(
                tight=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=6,
                controls=[
                    ft.Text(detalle_items, size=12),
                    ft.Divider(),
                    ft.Text(
                        f"Total: ${total:.2f}  |  Recibido: ${pagado:.2f}  |  Cambio: ${pagado - total:.2f}",
                        weight=ft.FontWeight.BOLD,
                        size=13,
                    ),
                    ft.Text(f"Factura: {rfc_texto}", size=12),
                    ft.Text(
                        "Verifica los productos antes de emitir el ticket. No se aceptan cancelaciones, cambios ni devoluciones.",
                        size=12,
                        color=COLOR_ROJO,
                    ),
                ],
            ),
            actions=[
                ft.TextButton(content=ft.Text("Revisar"), on_click=lambda _: self.cerrar_dialogo(dlg_conf)),
                crear_boton("Confirmar y Emitir", on_click=ejecutar_cobro, bgcolor=COLOR_VERDE, color=COLOR_BLANCO),
            ],
        )
        self.abrir_dialogo(dlg_conf)

    def _quitar_pago(self, indice, on_refrescar):
        self.pagos.pop(indice)
        on_refrescar()

    def _limpiar_pagos(self, on_refrescar):
        self.pagos.clear()
        on_refrescar()

    def _pintar_lista_pagos(self, lista_pagos, on_refrescar):
        lista_pagos.controls.clear()
        if not self.pagos:
            lista_pagos.controls.append(ft.Text("Sin pagos agregados.", size=12, color="#777777"))
            return

        for idx, pago in enumerate(self.pagos):
            ref_txt = f" | Ref: {pago['referencia']}" if pago.get("referencia") else ""
            nombre_m = NOMBRES_METODO.get(pago["id_metodo_pago"], "Pago")
            lista_pagos.controls.append(
                ft.Container(
                    bgcolor=COLOR_BLANCO,
                    border=borde_all(1, COLOR_BORDE),
                    border_radius=8,
                    padding=8,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(f"{nombre_m}{ref_txt}", size=13, expand=True),
                            ft.Text(f"${pago['monto']:.2f}", weight=ft.FontWeight.BOLD, size=13),
                            ft.IconButton(
                                icon=ICONS.DELETE_OUTLINE,
                                icon_color=COLOR_ROJO,
                                on_click=lambda _, i=idx: self._quitar_pago(i, on_refrescar),
                            ),
                        ],
                    ),
                )
            )

    def _pintar_botones_comprobante(self, panel_comprobante):
        panel_comprobante.controls.clear()
        if not self.ultimo_comprobante:
            return
        venta = self.ultimo_comprobante["venta"]
        factura = self.ultimo_comprobante.get("factura")
        botones = [
            crear_boton(
                f"DESCARGAR TICKET ({venta['folio']})",
                on_click=lambda _, v=venta: self.descargar_comprobante_ticket(v),
                bgcolor=COLOR_AZUL,
                color=COLOR_BLANCO,
                icon=ICON_DESCARGA,
                height=42,
            )
        ]
        if factura:
            folio_f = venta.get("folio_factura") or venta["folio"]
            botones.append(
                crear_boton(
                    f"DESCARGAR FACTURA ({folio_f})",
                    on_click=lambda _, v=venta, f=factura: self.descargar_comprobante_factura(v, f),
                    bgcolor=COLOR_MORADO,
                    color=COLOR_BLANCO,
                    icon=ICON_DESCARGA,
                    height=42,
                )
            )
        panel_comprobante.controls.extend([ft.Divider(), *botones])

    def _validar_y_agregar_pago(self, metodo, monto_str, ref_str):
        try:
            monto = round(float((monto_str or "").strip()), 2)
            if monto <= 0:
                raise ValueError
        except ValueError:
            self.mostrar_aviso("Ingresa un monto válido.", COLOR_ROJO)
            return False

        id_m = METODOS_ID.get(metodo, 1)
        ref = None
        if id_m != 1:
            ref = (ref_str or "").strip()
            if not ref:
                self.mostrar_aviso("Ingresa la referencia de la tarjeta.", COLOR_ROJO)
                return False

        self.pagos.append({"id_metodo_pago": id_m, "monto": monto, "referencia": ref})
        return True

    def vista_cobros(self):
        lbl_resumen = ft.Text("", size=13, color=COLOR_TEXTO_SEC)
        lbl_total = ft.Text("$0.00", size=26, weight=ft.FontWeight.BOLD, color=COLOR_VERDE)
        lbl_estado_pago = ft.Text("", size=13, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        lbl_factura = ft.Text("", size=12, color=COLOR_TEXTO_SUAVE, text_align=ft.TextAlign.CENTER)
        lista_pagos = ft.Column(spacing=6)
        panel_comprobante = ft.Column(spacing=6, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        cmb_metodo = ft.Dropdown(
            label="Método de pago",
            value=METODO_EFECTIVO,
            options=[
                OPT_CLS(key=METODO_EFECTIVO, text=METODO_EFECTIVO),
                OPT_CLS(key=METODO_DEBITO, text=METODO_DEBITO),
                OPT_CLS(key=METODO_CREDITO, text=METODO_CREDITO),
            ],
        )
        txt_monto = ft.TextField(label="Monto ($)", keyboard_type=ft.KeyboardType.NUMBER, bgcolor=COLOR_BLANCO, dense=True)
        txt_ref = ft.TextField(label="Referencia tarjeta (si aplica)", bgcolor=COLOR_BLANCO, disabled=True, dense=True)

        def on_metodo_change(_):
            es_ef = cmb_metodo.value == METODO_EFECTIVO
            txt_ref.disabled = es_ef
            if es_ef:
                txt_ref.value = ""
            self.safe_update()

        conectar_dropdown(cmb_metodo, on_metodo_change)

        def refrescar_pagos():
            sub, iva, total = self.modelo.calcular_desglose()
            pagado = round(sum(p["monto"] for p in self.pagos), 2)
            restante = round(max(0.0, total - pagado), 2)
            cambio = round(max(0.0, pagado - total), 2)

            lbl_resumen.value = f"Subtotal: ${sub:.2f}  |  IVA (16%): ${iva:.2f}"
            lbl_total.value = f"${total:.2f}"
            lbl_estado_pago.value = f"Pagado: ${pagado:.2f}  |  Restante: ${restante:.2f}  |  Cambio: ${cambio:.2f}"

            if restante > 0 and not txt_monto.value:
                txt_monto.value = f"{restante:.2f}"

            self._pintar_lista_pagos(lista_pagos, refrescar_pagos)
            df = self.datos_factura
            lbl_factura.value = f"Factura: {df['rfc']} ({df['razon_social']})" if df else "Factura: No solicitada"
            lbl_factura.color = COLOR_VERDE if df else COLOR_TEXTO_SUAVE
            self._pintar_botones_comprobante(panel_comprobante)
            self.safe_update()

        def on_agregar_pago(_):
            if self._validar_y_agregar_pago(cmb_metodo.value, txt_monto.value, txt_ref.value):
                txt_monto.value = ""
                txt_ref.value = ""
                refrescar_pagos()

        refrescar_pagos()

        return ft.Container(
            bgcolor=COLOR_BLANCO,
            border=borde_all(1, COLOR_BORDE),
            border_radius=10,
            padding=14,
            content=ft.Column(
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Text("Cobros y Pagos", weight=ft.FontWeight.BOLD, size=18, color=COLOR_MARCA, text_align=ft.TextAlign.CENTER),
                    ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[lbl_resumen, lbl_total, lbl_estado_pago]),
                    ft.Divider(),
                    cmb_metodo,
                    txt_monto,
                    txt_ref,
                    ft.Row(
                        controls=[
                            crear_boton("+ AGREGAR PAGO", on_click=on_agregar_pago, bgcolor=COLOR_VERDE, color=COLOR_BLANCO, expand=True, height=42),
                            crear_boton("LIMPIAR", on_click=lambda _: self._limpiar_pagos(refrescar_pagos), bgcolor=COLOR_ROJO, color=COLOR_BLANCO, height=42),
                        ]
                    ),
                    lista_pagos,
                    ft.Divider(),
                    lbl_factura,
                    crear_boton("AGREGAR / EDITAR FACTURA", on_click=lambda _: self._abrir_modal_factura(refrescar_pagos), bgcolor=COLOR_MORADO, color=COLOR_BLANCO, height=40),
                    crear_boton("CONFIRMAR COBRO", on_click=lambda _: self._confirmar_cobro(refrescar_pagos), bgcolor=COLOR_AMARILLO, color=COLOR_NEGRO, height=46),
                    panel_comprobante,
                ],
            ),
        )

    def _cargar_ventas_turno_async(self, forzar, on_exito, on_cargando, on_error):
        if not forzar and self.ventas_turno_cache is not None:
            on_exito(self.ventas_turno_cache)
            return

        on_cargando()
        turno_objetivo = self.id_turno

        def worker():
            try:
                ventas = self.obtener_ventas_del_turno(turno_objetivo)
                if self.id_turno == turno_objetivo:
                    self.ventas_turno_cache = ventas
                    on_exito(ventas)
            except Exception as exc:
                on_error(exc)

        threading.Thread(target=worker, daemon=True).start()

    def _ver_detalle_ticket(self, venta):
        lineas = [
            f"Folio: {venta.get('folio', 'N/D')}",
            f"Turno: #{self.id_turno}",
            f"Fecha: {venta.get('fecha', 'N/D')}",
            f"Método: {venta.get('metodo_pago', 'N/D')}",
            f"Estado factura: {venta.get('estado_factura', ESTADO_SIN_FACTURA)}",
            "",
            "PRODUCTOS:",
        ]
        for art in venta.get("articulos", []):
            lineas.append(f"- {art.get('producto', 'Producto')} x{art.get('cantidad', 0)} (${float(art.get('subtotal', 0)):.2f})")
        lineas.extend(["", f"Importe del ticket: ${float(venta.get('total', 0)):.2f}"])

        def descargar_y_cerrar(_):
            self.cerrar_dialogo(dlg)
            self.descargar_comprobante_ticket(venta)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Ticket {venta.get('folio', '')}"),
            content=ft.Column(tight=True, scroll=ft.ScrollMode.AUTO, controls=[ft.Text("\n".join(lineas), size=13)]),
            actions=[
                ft.TextButton(content=ft.Text(TXT_CERRAR), on_click=lambda _: self.cerrar_dialogo(dlg)),
                crear_boton(
                    TXT_DESCARGAR_PDF,
                    on_click=descargar_y_cerrar,
                    bgcolor=COLOR_AMARILLO,
                    color=COLOR_NEGRO,
                    icon=ICON_DESCARGA,
                ),
            ],
        )
        self.abrir_dialogo(dlg)

    def _tarjeta_ticket(self, venta):
        return ft.Container(
            bgcolor=COLOR_BLANCO,
            border=borde_all(1, COLOR_BORDE),
            border_radius=8,
            padding=10,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(f"{venta.get('folio', '')}  |  ${float(venta.get('total', 0)):.2f}", weight=ft.FontWeight.BOLD, size=14),
                            ft.Text(f"{venta.get('fecha', '')} | {venta.get('metodo_pago', '')}", size=12, color=COLOR_TEXTO_SEC),
                            ft.Text(venta.get("estado_factura", ESTADO_SIN_FACTURA), size=11, color=COLOR_AZUL),
                        ],
                    ),
                    ft.Row(
                        spacing=4,
                        tight=True,
                        controls=[
                            ft.IconButton(
                                icon=ICONS.VISIBILITY,
                                icon_color=COLOR_AZUL,
                                tooltip="Ver detalle",
                                on_click=lambda _, v=venta: self._ver_detalle_ticket(v),
                            ),
                            crear_boton(
                                "PDF",
                                on_click=lambda _, v=venta: self.descargar_comprobante_ticket(v),
                                bgcolor=COLOR_AMARILLO,
                                color=COLOR_NEGRO,
                                icon=ICON_DESCARGA,
                            ),
                        ],
                    ),
                ],
            ),
        )

    def vista_tickets(self):
        lista_tickets = ft.Column(spacing=8)
        id_turno = self.id_turno
        lbl_estado = ft.Text(f"Cargando tickets del Turno #{id_turno}...", size=13, color=COLOR_TEXTO_SEC)

        def pintar_tickets(ventas):
            lista_tickets.controls.clear()
            if not ventas:
                lbl_estado.value = f"Aún no hay tickets emitidos en el Turno #{id_turno}."
            else:
                lbl_estado.value = f"Turno #{id_turno} - Tickets emitidos: {len(ventas)}"
                for venta in ventas:
                    lista_tickets.controls.append(self._tarjeta_ticket(venta))
            self.safe_update()

        def on_cargando():
            lbl_estado.value = f"Consultando tickets del Turno #{id_turno}..."
            lista_tickets.controls.clear()
            self.safe_update()

        def on_error(exc):
            lbl_estado.value = f"Error al cargar tickets: {exc}"
            self.safe_update()

        def recargar(forzar=False):
            self._cargar_ventas_turno_async(forzar, pintar_tickets, on_cargando, on_error)

        recargar(forzar=False)

        return ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Tickets del Turno", weight=ft.FontWeight.BOLD, size=17, color=COLOR_MARCA),
                        crear_boton(TXT_ACTUALIZAR, on_click=lambda _: recargar(forzar=True), bgcolor=COLOR_AZUL, color=COLOR_BLANCO),
                    ],
                ),
                lbl_estado,
                lista_tickets,
            ],
        )

    def _coincide_filtro_venta(self, venta, texto):
        if texto in str(venta.get("folio", "")).lower():
            return True
        if texto in str(venta.get("metodo_pago", "")).lower():
            return True
        return any(texto in str(a.get("producto", "")).lower() for a in venta.get("articulos", []))

    def _tarjeta_historial(self, venta):
        prods_txt = ", ".join(
            f"{a.get('producto', '')} (x{a.get('cantidad', 0)})" for a in venta.get("articulos", [])
        )
        return ft.Container(
            bgcolor=COLOR_BLANCO,
            border=borde_all(1, COLOR_BORDE),
            border_radius=8,
            padding=10,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(venta.get("folio", ""), weight=ft.FontWeight.BOLD, size=14, color=COLOR_MARCA),
                            ft.Text(f"${float(venta.get('total', 0)):.2f}", weight=ft.FontWeight.BOLD, size=14, color=COLOR_VERDE),
                        ],
                    ),
                    ft.Text(
                        f"{venta.get('fecha', '')}  |  {venta.get('metodo_pago', '')}  |  {venta.get('estado_factura', ESTADO_SIN_FACTURA)}",
                        size=11,
                        color=COLOR_TEXTO_SEC,
                    ),
                    ft.Text(prods_txt or "Sin detalle", size=12, color="#222222"),
                ],
            ),
        )

    def vista_historial(self):
        id_turno = self.id_turno
        txt_filtro = ft.TextField(
            label="Buscar folio o producto en este turno",
            bgcolor=COLOR_BLANCO,
            dense=True,
            expand=True,
        )
        lbl_info = ft.Text(f"Ventas del Turno #{id_turno}", size=13, weight=ft.FontWeight.BOLD, color=COLOR_AZUL)
        lista_hist = ft.Column(spacing=6)

        def pintar_historial(ventas):
            q = (txt_filtro.value or "").strip().lower()
            filtradas = [v for v in ventas if self._coincide_filtro_venta(v, q)] if q else ventas[:]
            lbl_info.value = f"Turno #{id_turno} - Operaciones registradas: {len(filtradas)}"

            lista_hist.controls.clear()
            if not filtradas:
                lista_hist.controls.append(
                    ft.Text("No hay ventas registradas en este turno con ese criterio.", size=13, color=COLOR_TEXTO_SUAVE)
                )
            else:
                for venta in filtradas:
                    lista_hist.controls.append(self._tarjeta_historial(venta))
            self.safe_update()

        def on_cargando():
            lbl_info.value = f"Consultando ventas del Turno #{id_turno}..."
            lista_hist.controls.clear()
            self.safe_update()

        def on_error(exc):
            lbl_info.value = f"Error al consultar ventas: {exc}"
            self.safe_update()

        def cargar_historial(forzar=False):
            self._cargar_ventas_turno_async(forzar, pintar_historial, on_cargando, on_error)

        txt_filtro.on_change = lambda _: cargar_historial(forzar=False)
        cargar_historial(forzar=False)

        return ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Historial del Turno", weight=ft.FontWeight.BOLD, size=17, color=COLOR_MARCA),
                        crear_boton(TXT_ACTUALIZAR, on_click=lambda _: cargar_historial(forzar=True), bgcolor=COLOR_AZUL, color=COLOR_BLANCO),
                    ],
                ),
                ft.Row(
                    controls=[
                        txt_filtro,
                        crear_boton("BUSCAR", on_click=lambda _: cargar_historial(forzar=False), bgcolor=COLOR_AMARILLO, color=COLOR_NEGRO),
                    ]
                ),
                lbl_info,
                lista_hist,
            ],
        )

    def _mostrar_resultado_cierre(self, contado, hay_faltante):
        bloques = [
            ft.Text(
                "Tu cierre de caja se registró correctamente en el sistema.",
                size=14,
                weight=ft.FontWeight.BOLD,
                color=COLOR_VERDE,
            ),
            ft.Container(
                bgcolor=COLOR_GRIS_CLARO,
                border=borde_all(1, COLOR_BORDE),
                border_radius=8,
                padding=10,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Efectivo contado reportado:", size=13, weight=ft.FontWeight.BOLD),
                        ft.Text(f"${contado:,.2f}", size=14, weight=ft.FontWeight.BOLD, color=COLOR_MARCA),
                    ],
                ),
            ),
        ]

        if hay_faltante:
            bloques.append(
                ft.Container(
                    bgcolor="#FDEDEC",
                    border=borde_all(1, COLOR_ROJO),
                    border_radius=8,
                    padding=10,
                    content=ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Icon(ICON_ALERTA, color=COLOR_ROJO, size=22),
                            ft.Text(
                                "Se detectó un faltante en caja. El detalle del corte fue enviado para revisión del administrador.",
                                size=13,
                                color=COLOR_ROJO,
                                weight=ft.FontWeight.BOLD,
                                expand=True,
                            ),
                        ],
                    ),
                )
            )
        else:
            bloques.append(
                ft.Container(
                    bgcolor="#EAFAF1",
                    border=borde_all(1, COLOR_VERDE),
                    border_radius=8,
                    padding=10,
                    content=ft.Text(
                        "El reporte del corte fue registrado y enviado para revisión del administrador.",
                        size=13,
                        color="#1E8449",
                    ),
                )
            )

        def salir_a_login(_):
            self.cerrar_dialogo(dlg_cierre)
            self.mostrar_login()

        dlg_cierre = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cierre de Caja Finalizado"),
            content=ft.Column(tight=True, spacing=10, controls=bloques),
            actions=[
                crear_boton("ACEPTAR Y SALIR", on_click=salir_a_login, bgcolor=COLOR_MARCA, color=COLOR_BLANCO),
            ],
        )
        self.abrir_dialogo(dlg_cierre)

    def _procesar_cierre_caja(self, monto_str, fondo_inicial):
        try:
            contado = round(float((monto_str or "").strip()), 2)
            if contado < 0:
                raise ValueError
        except ValueError:
            self.mostrar_aviso("Ingresa un monto válido (0 o mayor).", COLOR_ROJO)
            return

        # Validación interna contra fondo inicial + efectivo del turno sin mostrar diferencias
        resumen_actual = self.modelo.obtener_resumen_turno_db(self.id_turno) or {}
        efectivo_esperado = float(resumen_actual.get("efectivo_esperado") or fondo_inicial)
        hay_faltante = contado < (efectivo_esperado - 0.009)

        try:
            self.modelo._ejecutar_consulta(
                "UPDATE cortes_caja SET fecha_hora_fin=NOW(), efectivo_contado=%s, estado='cerrado' WHERE id_corte_caja=%s",
                (contado, self.id_turno),
            )
        except Exception as ex:
            self.mostrar_aviso(f"Error al registrar el cierre: {ex}", COLOR_ROJO)
            return

        self.modelo.ticket_actual.clear()
        self.pagos.clear()
        self.datos_factura = None
        self.ultimo_comprobante = None
        self.id_turno = None
        self.ventas_turno_cache = None
        self._mostrar_resultado_cierre(contado, hay_faltante)

    def vista_cierre_caja(self):
        resumen = self.modelo.obtener_resumen_turno_db(self.id_turno) or {}
        txt_efectivo = ft.TextField(
            label="Efectivo físico contado ($)",
            hint_text="Ejemplo: 500.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=COLOR_BLANCO,
        )

        inicio = resumen.get("fecha_hora_inicio")
        inicio_str = inicio.strftime("%d/%m/%Y %H:%M:%S") if hasattr(inicio, "strftime") else str(inicio or "N/D")
        fondo_inicial = float(resumen.get("fondo_inicial") or 500.0)
        num_ventas = int(resumen.get("num_ventas") or 0)

        filas = [
            ("Usuario / Rol:", f"{self.usuario} ({self.rol})"),
            ("Caja / Turno:", f"{resumen.get('numero_caja', 'N/D')} (Corte #{self.id_turno})"),
            ("Inicio de turno:", inicio_str),
            ("Fondo inicial de caja:", f"${fondo_inicial:,.2f}"),
            ("Operaciones realizadas:", f"{num_ventas} venta(s)"),
        ]

        return ft.Container(
            bgcolor=COLOR_BLANCO,
            border=borde_all(1, COLOR_BORDE),
            border_radius=10,
            padding=16,
            content=ft.Column(
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Text("CIERRE DE CAJA (CORTE CIEGO)", weight=ft.FontWeight.BOLD, size=18, color=COLOR_MARCA, text_align=ft.TextAlign.CENTER),
                    ft.Text(
                        "Cuenta el dinero físico en tu caja e ingrésalo abajo. El reporte detallado se envía automáticamente a administración.",
                        size=12,
                        color=COLOR_TEXTO_SEC,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(),
                    *[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(k, weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(v, size=13, text_align=ft.TextAlign.RIGHT),
                            ],
                        )
                        for k, v in filas
                    ],
                    ft.Divider(),
                    txt_efectivo,
                    crear_boton(
                        "FINALIZAR TURNO Y CERRAR SESIÓN",
                        on_click=lambda _: self._procesar_cierre_caja(txt_efectivo.value, fondo_inicial),
                        bgcolor=COLOR_ROJO,
                        color=COLOR_BLANCO,
                        height=46,
                    ),
                ],
            ),
        )

    def cambiar_seccion(self, indice):
        self.vista_actual = indice
        if self.page.navigation_bar:
            self.page.navigation_bar.selected_index = indice
        vistas = (
            self.vista_punto_venta,
            self.vista_cobros,
            self.vista_tickets,
            self.vista_historial,
            self.vista_cierre_caja,
        )
        self.contenedor_cuerpo.content = vistas[indice]()
        self.safe_update()

    def cargar_layout_principal(self):
        self.page.controls.clear()
        self.page.appbar = ft.AppBar(
            title=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ICON_TIENDA, color=COLOR_BLANCO, size=20),
                    crear_texto(
                        f"Algorrico - {self.usuario}",
                        color=COLOR_BLANCO,
                        weight=ft.FontWeight.BOLD,
                        size=15,
                        max_lines=1,
                        expand=True,
                    ),
                ],
            ),
            bgcolor=COLOR_MARCA,
            actions=[
                ft.IconButton(
                    icon=ICONS.LOGOUT,
                    icon_color=COLOR_BLANCO,
                    tooltip="Cierre de Caja",
                    on_click=lambda _: self.cambiar_seccion(4),
                )
            ],
        )

        self.page.navigation_bar = ft.NavigationBar(
            selected_index=0,
            bgcolor=COLOR_BLANCO,
            on_change=lambda e: self.cambiar_seccion(e.control.selected_index),
            destinations=[
                ft.NavigationBarDestination(icon=ICONS.POINT_OF_SALE, label="Venta"),
                ft.NavigationBarDestination(icon=ICONS.PAYMENTS, label="Cobros"),
                ft.NavigationBarDestination(icon=ICONS.RECEIPT_LONG, label="Tickets"),
                ft.NavigationBarDestination(icon=ICONS.HISTORY, label="Historial"),
                ft.NavigationBarDestination(icon=ICONS.LOCK_CLOCK, label="Cierre"),
            ],
        )

        self.page.add(self.contenedor_cuerpo)
        self.cambiar_seccion(0)


def main(page: ft.Page):
    app = AppMovil(page)
    app.mostrar_login()


if __name__ == "__main__":
    puerto = int(os.getenv("PORT", 8550))
    modo_web = bool(os.getenv("RENDER") or os.getenv("FLET_WEB"))
    if modo_web:
        host = "0.0.0.0" if os.getenv("RENDER") else "127.0.0.1"
        if hasattr(ft, "run"):
            ft.run(main, view=ft.AppView.WEB_BROWSER, host=host, port=puerto, assets_dir=DIR_ASSETS)
        else:
            ft.app(target=main, view=ft.AppView.WEB_BROWSER, host=host, port=puerto, assets_dir=DIR_ASSETS)
    else:
        if hasattr(ft, "run"):
            ft.run(main, assets_dir=DIR_ASSETS)
        else:
            ft.app(target=main, assets_dir=DIR_ASSETS)