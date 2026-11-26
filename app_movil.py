import os
import threading
import flet as ft
from modelos.modelo import ModeloDulceria
from servicios.repositorio_ventas import RepositorioVentas
from vistas.generador_tickets import generar_comprobante_ticket_pdf, generar_ticket_pdf

ICONS = getattr(ft, "Icons", getattr(ft, "icons", None))
BTN_CLS = getattr(ft, "Button", getattr(ft, "ElevatedButton", None))
OPT_CLS = getattr(ft, "DropdownOption", None) or ft.dropdown.Option
ALIGN_CENTER = getattr(ft.Alignment, "CENTER", ft.Alignment(0, 0))

COLOR_MARCA = "#C2284E"
COLOR_FONDO = "#FFF8F5"
COLOR_AMARILLO = "#F4D03F"
COLOR_VERDE = "#27AE60"
COLOR_ROJO = "#C0392B"
COLOR_AZUL = "#3A8D96"
COLOR_MORADO = "#8E44AD"
LIMITE_RENDER = 20

DIR_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
DIR_TICKETS_WEB = os.path.join(DIR_ASSETS, "tickets")
os.makedirs(DIR_TICKETS_WEB, exist_ok=True)


def borde_all(ancho, color):
    clase = getattr(ft, "Border", None)
    if clase and hasattr(clase, "all"):
        return clase.all(ancho, color)
    return ft.border.all(ancho, color)


def crear_boton(texto, on_click, bgcolor=None, color=None, width=None, height=None, expand=False, url=None):
    kwargs = dict(
        content=ft.Text(texto, color=color, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        bgcolor=bgcolor,
        color=color,
        width=width,
        height=height,
        expand=expand,
        on_click=on_click,
    )
    if url:
        kwargs["url"] = url
    return BTN_CLS(**kwargs)


def conectar_dropdown(cmb, callback):
    if hasattr(cmb, "on_select"):
        cmb.on_select = callback
    else:
        cmb.on_change = callback


def main(page: ft.Page):
    page.title = "Dulcería Algorrico - Caja Móvil"
    page.bgcolor = COLOR_FONDO
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.scroll = ft.ScrollMode.ADAPTIVE

    modelo = ModeloDulceria()
    repo_ventas = RepositorioVentas()

    sesion = {
        "usuario": None,
        "id_usuario": None,
        "rol": None,
        "id_turno": None,
        "vista_actual": 0,
        "pagos": [],
        "datos_factura": None,
        "ventas_cache": None,
        "ultimo_comprobante": None,
    }

    def mostrar_aviso(mensaje, color=COLOR_VERDE):
        sb = ft.SnackBar(content=ft.Text(mensaje, color="#FFFFFF"), bgcolor=color)
        if hasattr(page, "show_dialog"):
            page.show_dialog(sb)
        elif hasattr(page, "open"):
            page.open(sb)
        else:
            page.overlay.append(sb)
            sb.open = True
            page.update()

    def abrir_dialogo(dlg):
        if hasattr(page, "show_dialog"):
            page.show_dialog(dlg)
        elif hasattr(page, "open"):
            page.open(dlg)
        else:
            page.dialog = dlg
            dlg.open = True
            page.update()

    def cerrar_dialogo(dlg):
        if hasattr(page, "pop_dialog"):
            page.pop_dialog()
        elif hasattr(page, "close"):
            page.close(dlg)
        else:
            dlg.open = False
            page.update()

    def preparar_pdf_ticket(venta):
        folio = venta.get("folio", "venta")
        nombre_pdf = f"Ticket_{folio}.pdf"
        ruta_pdf = os.path.join(DIR_TICKETS_WEB, nombre_pdf)
        generar_comprobante_ticket_pdf(ruta_pdf, venta)
        return f"/tickets/{nombre_pdf}"

    def preparar_pdf_factura(venta, factura):
        folio = venta.get("folio_factura") or venta.get("folio", "venta")
        rfc = factura.get("rfc", "XAXX010101000")
        nombre_pdf = f"Factura_{folio}_{rfc}.pdf"
        ruta_pdf = os.path.join(DIR_TICKETS_WEB, nombre_pdf)
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
        return f"/tickets/{nombre_pdf}"

    def mostrar_login():
        page.appbar = None
        page.navigation_bar = None
        page.controls.clear()

        txt_user = ft.TextField(label="Usuario", width=290, bgcolor="#FFFFFF")
        txt_pass = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            width=290,
            bgcolor="#FFFFFF",
        )
        cmb_caja = ft.Dropdown(
            label="Caja a operar (1-4)",
            width=290,
            value="1",
            options=[OPT_CLS(key=str(i), text=f"CAJA-0{i}") for i in range(1, 5)],
        )

        def iniciar_sesion(e):
            u = (txt_user.value or "").strip()
            p = (txt_pass.value or "").strip()
            if not u or not p:
                mostrar_aviso("Ingresa usuario y contraseña.", COLOR_ROJO)
                return

            user_data = modelo.validar_usuario(u, p)
            if not user_data:
                mostrar_aviso("Usuario o contraseña incorrectos.", COLOR_ROJO)
                return

            rol = modelo.obtener_rol(user_data["id_rol"])
            if rol.strip().lower() != "cajero":
                mostrar_aviso("Acceso exclusivo para Cajeros. Usa la versión de escritorio.", COLOR_ROJO)
                return

            sesion["usuario"] = u
            sesion["id_usuario"] = user_data["id_usuario"]
            sesion["rol"] = rol
            sesion["ventas_cache"] = None
            sesion["datos_factura"] = None
            sesion["ultimo_comprobante"] = None

            corte = modelo._ejecutar_consulta(
                """SELECT id_corte_caja FROM cortes_caja
                   WHERE id_usuario = %s AND estado = 'abierto'
                   ORDER BY id_corte_caja DESC LIMIT 1""",
                (sesion["id_usuario"],),
                fetch=True,
            )
            if corte:
                sesion["id_turno"] = corte["id_corte_caja"]
            else:
                num_caja = int(cmb_caja.value or 1)
                sesion["id_turno"] = modelo._ejecutar_consulta(
                    "INSERT INTO cortes_caja (fondo_inicial, id_usuario, id_caja) VALUES (500.00, %s, %s)",
                    (sesion["id_usuario"], num_caja),
                )

            mostrar_aviso(f"Turno #{sesion['id_turno']} activo — {u}", COLOR_VERDE)
            cargar_layout_principal()

        txt_pass.on_submit = iniciar_sesion

        tarjeta_login = ft.Container(
            bgcolor="#FFFFFF",
            border=borde_all(2, "#F3C6D1"),
            border_radius=12,
            padding=24,
            width=340,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    ft.Text("🍬 Algorrico", size=28, weight=ft.FontWeight.BOLD, color=COLOR_MARCA),
                    ft.Text("Caja Móvil — Exclusivo Cajero", size=14, color="#555555"),
                    txt_user,
                    txt_pass,
                    cmb_caja,
                    crear_boton(
                        "ABRIR CAJA E INGRESAR",
                        on_click=iniciar_sesion,
                        bgcolor=COLOR_MARCA,
                        color="#FFFFFF",
                        width=290,
                        height=44,
                    ),
                ],
            ),
        )

        page.add(ft.Container(expand=True, alignment=ALIGN_CENTER, padding=16, content=tarjeta_login))
        page.update()

    contenedor_cuerpo = ft.Container(padding=12, expand=True)

    def vista_punto_venta():
        txt_buscar = ft.TextField(label="Buscar (nombre o código)", bgcolor="#FFFFFF", dense=True)
        lista_prods = ft.Column(spacing=6)
        lista_carrito = ft.Column(spacing=6)
        lbl_desglose = ft.Text("", size=12, color="#555555")
        lbl_total = ft.Text("TOTAL: $0.00", size=18, weight=ft.FontWeight.BOLD, color=COLOR_VERDE)

        def refrescar_carrito():
            lista_carrito.controls.clear()
            if not modelo.ticket_actual:
                lista_carrito.controls.append(ft.Text("Carrito vacío. Agrega productos.", size=12, color="#777777"))
            else:
                for item in modelo.ticket_actual:
                    nombre = item["producto"]
                    lista_carrito.controls.append(
                        ft.Container(
                            bgcolor="#FFFFFF",
                            border=borde_all(1, "#DDDDDD"),
                            border_radius=8,
                            padding=8,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Column(
                                        expand=True,
                                        spacing=2,
                                        controls=[
                                            ft.Text(nombre, weight=ft.FontWeight.BOLD, size=13),
                                            ft.Text(f"Cant: {item['cantidad']}  |  ${float(item['subtotal']):.2f}", size=12, color="#555555"),
                                        ],
                                    ),
                                    ft.Row(
                                        spacing=0,
                                        controls=[
                                            ft.IconButton(icon=ICONS.REMOVE_CIRCLE_OUTLINE, icon_color="#E67E22", on_click=lambda e, n=nombre: modificar_item(n, -1)),
                                            ft.IconButton(icon=ICONS.ADD_CIRCLE_OUTLINE, icon_color=COLOR_VERDE, on_click=lambda e, n=nombre: modificar_item(n, 1)),
                                            ft.IconButton(icon=ICONS.DELETE_OUTLINE, icon_color=COLOR_ROJO, on_click=lambda e, n=nombre: quitar_item(n)),
                                        ],
                                    ),
                                ],
                            ),
                        )
                    )

            sub, iva, total = modelo.calcular_desglose()
            lbl_desglose.value = f"Subtotal: ${sub:.2f}  |  IVA (16%): ${iva:.2f}"
            lbl_total.value = f"TOTAL (IVA incl.): ${total:.2f}"
            page.update()

        def agregar_item(prod):
            res = modelo.agregar_al_ticket(prod["nombre"], 1)
            if res == "stock_insuficiente":
                mostrar_aviso(f"Sin stock suficiente de {prod['nombre']}.", COLOR_ROJO)
                return
            refrescar_carrito()

        def modificar_item(nombre, delta):
            ok, msg = modelo.actualizar_cantidad_ticket(nombre, delta)
            if not ok:
                mostrar_aviso(msg, COLOR_ROJO)
                return
            refrescar_carrito()

        def quitar_item(nombre):
            modelo.quitar_del_ticket(nombre)
            refrescar_carrito()

        def limpiar_carrito(e):
            modelo.ticket_actual.clear()
            sesion["pagos"].clear()
            sesion["datos_factura"] = None
            refrescar_carrito()

        def refrescar_catalogo(e=None):
            lista_prods.controls.clear()
            texto = (txt_buscar.value or "").strip().lower()
            prods = [p for p in modelo.inventario if p["stock"] > 0]
            if texto:
                prods = [
                    p for p in prods
                    if p["nombre"].lower().startswith(texto)
                    or str(p.get("codigo_barras") or "").lower().startswith(texto)
                ]

            for p in prods[:LIMITE_RENDER]:
                lista_prods.controls.append(
                    ft.Container(
                        bgcolor="#FFFFFF",
                        border=borde_all(1, "#DDDDDD"),
                        border_radius=8,
                        padding=10,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    expand=True,
                                    spacing=2,
                                    controls=[
                                        ft.Text(p["nombre"], weight=ft.FontWeight.BOLD, size=13),
                                        ft.Text(
                                            f"${p['precio']:.2f}  |  Stock: {p['stock']}",
                                            size=12,
                                            color=COLOR_ROJO if p["stock"] <= p.get("stock_minimo", 5) else "#555555",
                                        ),
                                    ],
                                ),
                                crear_boton(
                                    "+1",
                                    on_click=lambda ev, prod=p: agregar_item(prod),
                                    bgcolor=COLOR_AMARILLO,
                                    color="#000000",
                                ),
                            ],
                        ),
                    )
                )
            page.update()

        txt_buscar.on_change = refrescar_catalogo
        refrescar_catalogo()
        refrescar_carrito()

        panel_catalogo = ft.Container(
            col={"xs": 12, "md": 6},
            content=ft.Column(spacing=8, controls=[ft.Text("Punto de Venta", weight=ft.FontWeight.BOLD, size=16, color=COLOR_MARCA), txt_buscar, lista_prods]),
        )

        panel_carrito = ft.Container(
            col={"xs": 12, "md": 6},
            bgcolor="#F4F4F4",
            border=borde_all(1, "#CCCCCC"),
            border_radius=10,
            padding=12,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text("Ticket de Venta", weight=ft.FontWeight.BOLD, size=15),
                    lista_carrito,
                    ft.Divider(),
                    lbl_desglose,
                    lbl_total,
                    crear_boton(
                        "CONTINUAR A COBROS Y PAGOS",
                        on_click=lambda e: cambiar_seccion(1),
                        bgcolor=COLOR_AMARILLO,
                        color="#000000",
                        height=44,
                        width=400,
                    ),
                    crear_boton(
                        "LIMPIAR CARRITO",
                        on_click=limpiar_carrito,
                        bgcolor=COLOR_ROJO,
                        color="#FFFFFF",
                        height=40,
                        width=400,
                    ),
                ],
            ),
        )

        return ft.ResponsiveRow(controls=[panel_catalogo, panel_carrito], spacing=12, run_spacing=12)

    def vista_cobros():
        lbl_resumen = ft.Text("", size=13, color="#555555")
        lbl_total = ft.Text("$0.00", size=26, weight=ft.FontWeight.BOLD, color=COLOR_VERDE)
        lbl_estado_pago = ft.Text("", size=13, weight=ft.FontWeight.BOLD)
        lbl_factura = ft.Text("", size=12, color="#666666", text_align=ft.TextAlign.CENTER)
        lista_pagos = ft.Column(spacing=6)
        panel_comprobante = ft.Column(spacing=6)

        cmb_metodo = ft.Dropdown(
            label="Método de pago",
            value="Efectivo",
            options=[
                OPT_CLS(key="Efectivo", text="Efectivo"),
                OPT_CLS(key="Tarjeta de débito", text="Tarjeta de débito"),
                OPT_CLS(key="Tarjeta de crédito", text="Tarjeta de crédito"),
            ],
        )
        txt_monto = ft.TextField(label="Monto ($)", keyboard_type=ft.KeyboardType.NUMBER, bgcolor="#FFFFFF", dense=True)
        txt_ref = ft.TextField(label="Referencia tarjeta (si aplica)", bgcolor="#FFFFFF", disabled=True, dense=True)

        def on_metodo_change(e):
            es_ef = cmb_metodo.value == "Efectivo"
            txt_ref.disabled = es_ef
            if es_ef:
                txt_ref.value = ""
            page.update()

        conectar_dropdown(cmb_metodo, on_metodo_change)

        def refrescar_estado_factura():
            df = sesion.get("datos_factura")
            if df:
                lbl_factura.value = f"Factura: {df['rfc']} ({df['razon_social']})"
                lbl_factura.color = COLOR_VERDE
            else:
                lbl_factura.value = "Factura: No solicitada"
                lbl_factura.color = "#666666"

        def refrescar_comprobante():
            panel_comprobante.controls.clear()
            comp = sesion.get("ultimo_comprobante")
            if not comp:
                return
            venta = comp["venta"]
            factura = comp.get("factura")
            url_ticket = preparar_pdf_ticket(venta)
            botones = [
                crear_boton(
                    f"DESCARGAR TICKET ({venta['folio']})",
                    on_click=None,
                    bgcolor=COLOR_AZUL,
                    color="#FFFFFF",
                    height=42,
                    url=url_ticket,
                )
            ]
            if factura:
                url_fac = preparar_pdf_factura(venta, factura)
                botones.append(
                    crear_boton(
                        f"DESCARGAR FACTURA ({venta.get('folio_factura') or venta['folio']})",
                        on_click=None,
                        bgcolor=COLOR_MORADO,
                        color="#FFFFFF",
                        height=42,
                        url=url_fac,
                    )
                )
            panel_comprobante.controls.extend([ft.Divider(), *botones])

        def abrir_modal_factura(e):
            actual = sesion.get("datos_factura") or {}
            e_rfc = ft.TextField(label="RFC", value=actual.get("rfc", ""), bgcolor="#FFFFFF", dense=True)
            e_razon = ft.TextField(label="Razón Social", value=actual.get("razon_social", ""), bgcolor="#FFFFFF", dense=True)
            e_regimen = ft.TextField(label="Régimen Fiscal", value=actual.get("regimen", ""), bgcolor="#FFFFFF", dense=True)
            e_cp = ft.TextField(label="Código Postal", value=actual.get("cp", ""), bgcolor="#FFFFFF", dense=True)
            e_correo = ft.TextField(label="Correo", value=actual.get("correo", ""), bgcolor="#FFFFFF", dense=True)

            def guardar_fac(ev):
                vals = {
                    "rfc": (e_rfc.value or "").strip().upper(),
                    "razon_social": (e_razon.value or "").strip(),
                    "regimen": (e_regimen.value or "").strip(),
                    "cp": (e_cp.value or "").strip(),
                    "correo": (e_correo.value or "").strip(),
                }
                if not all(vals.values()):
                    mostrar_aviso("Completa todos los datos fiscales.", COLOR_ROJO)
                    return
                sesion["datos_factura"] = vals
                refrescar_estado_factura()
                cerrar_dialogo(dlg_fac)
                page.update()

            def quitar_fac(ev):
                sesion["datos_factura"] = None
                refrescar_estado_factura()
                cerrar_dialogo(dlg_fac)
                page.update()

            acciones = [
                ft.TextButton(content=ft.Text("Cancelar"), on_click=lambda ev: cerrar_dialogo(dlg_fac)),
            ]
            if sesion.get("datos_factura"):
                acciones.append(
                    crear_boton("Quitar", on_click=quitar_fac, bgcolor=COLOR_ROJO, color="#FFFFFF")
                )
            acciones.append(
                crear_boton("Guardar", on_click=guardar_fac, bgcolor=COLOR_VERDE, color="#FFFFFF")
            )

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
            abrir_dialogo(dlg_fac)

        def refrescar_pagos():
            sub, iva, total = modelo.calcular_desglose()
            pagado = round(sum(p["monto"] for p in sesion["pagos"]), 2)
            restante = round(max(0.0, total - pagado), 2)
            cambio = round(max(0.0, pagado - total), 2)

            lbl_resumen.value = f"Subtotal: ${sub:.2f}  |  IVA (16%): ${iva:.2f}"
            lbl_total.value = f"${total:.2f}"
            lbl_estado_pago.value = f"Pagado: ${pagado:.2f}  |  Restante: ${restante:.2f}  |  Cambio: ${cambio:.2f}"

            if restante > 0 and not txt_monto.value:
                txt_monto.value = f"{restante:.2f}"

            lista_pagos.controls.clear()
            if not sesion["pagos"]:
                lista_pagos.controls.append(ft.Text("Sin pagos agregados.", size=12, color="#777777"))
            else:
                nombres_m = {1: "Efectivo", 2: "Tarjeta débito", 3: "Tarjeta crédito"}
                for idx, p in enumerate(sesion["pagos"]):
                    ref_txt = f" | Ref: {p['referencia']}" if p.get("referencia") else ""
                    lista_pagos.controls.append(
                        ft.Container(
                            bgcolor="#FFFFFF",
                            border=borde_all(1, "#DDDDDD"),
                            border_radius=8,
                            padding=8,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(f"{nombres_m.get(p['id_metodo_pago'], 'Pago')}{ref_txt}", size=13, expand=True),
                                    ft.Text(f"${p['monto']:.2f}", weight=ft.FontWeight.BOLD, size=13),
                                    ft.IconButton(
                                        icon=ICONS.DELETE_OUTLINE,
                                        icon_color=COLOR_ROJO,
                                        on_click=lambda e, i=idx: (sesion["pagos"].pop(i), refrescar_pagos()),
                                    ),
                                ],
                            ),
                        )
                    )
            refrescar_estado_factura()
            refrescar_comprobante()
            page.update()

        def agregar_pago(e):
            try:
                monto = round(float((txt_monto.value or "").strip()), 2)
                if monto <= 0:
                    raise ValueError
            except ValueError:
                mostrar_aviso("Ingresa un monto válido.", COLOR_ROJO)
                return

            metodo = cmb_metodo.value
            id_m = 1 if metodo == "Efectivo" else (2 if metodo == "Tarjeta de débito" else 3)
            ref = None
            if id_m != 1:
                ref = (txt_ref.value or "").strip()
                if not ref:
                    mostrar_aviso("Ingresa la referencia de la tarjeta.", COLOR_ROJO)
                    return

            sesion["pagos"].append({"id_metodo_pago": id_m, "monto": monto, "referencia": ref})
            txt_monto.value = ""
            txt_ref.value = ""
            refrescar_pagos()

        def confirmar_cobro(e):
            if not modelo.ticket_actual:
                mostrar_aviso("El carrito está vacío. Agrega productos en Venta.", COLOR_ROJO)
                return
            total = modelo.calcular_total()
            pagado = round(sum(p["monto"] for p in sesion["pagos"]), 2)
            if pagado < total:
                mostrar_aviso(f"Faltan ${total - pagado:.2f} por cubrir.", COLOR_ROJO)
                return

            factura_actual = dict(sesion["datos_factura"]) if sesion.get("datos_factura") else None
            detalle_items = "\n".join(
                f"• {i['producto']} x{i['cantidad']} (${float(i['subtotal']):.2f})"
                for i in modelo.ticket_actual
            )

            def ejecutar_cobro(ev):
                cerrar_dialogo(dlg_conf)
                try:
                    resumen = repo_ventas.registrar(
                        modelo.ticket_actual,
                        sesion["pagos"],
                        sesion["id_turno"],
                        datos_factura=factura_actual,
                    )
                    sesion["ultimo_comprobante"] = {"venta": resumen, "factura": factura_actual}
                    modelo.ticket_actual.clear()
                    sesion["pagos"].clear()
                    sesion["datos_factura"] = None
                    modelo.invalidar_inventario()
                    sesion["ventas_cache"] = None
                    mostrar_aviso(f"Venta {resumen['folio']} registrada. Cambio: ${resumen['cambio']:.2f}", COLOR_VERDE)
                    refrescar_pagos()
                except Exception as ex:
                    mostrar_aviso(f"Error al cobrar: {ex}", COLOR_ROJO)

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
                        ft.Text(f"Total: ${total:.2f}  |  Recibido: ${pagado:.2f}  |  Cambio: ${pagado - total:.2f}", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(f"Factura: {factura_actual['rfc'] if factura_actual else 'No solicitada'}", size=12),
                        ft.Text(
                            "Verifica los productos antes de emitir el ticket. No se aceptan cancelaciones, cambios ni devoluciones.",
                            size=12,
                            color=COLOR_ROJO,
                        ),
                    ],
                ),
                actions=[
                    ft.TextButton(content=ft.Text("Revisar"), on_click=lambda ev: cerrar_dialogo(dlg_conf)),
                    crear_boton("Confirmar y Emitir", on_click=ejecutar_cobro, bgcolor=COLOR_VERDE, color="#FFFFFF"),
                ],
            )
            abrir_dialogo(dlg_conf)

        refrescar_pagos()

        return ft.Container(
            bgcolor="#FFFFFF",
            border=borde_all(1, "#DDDDDD"),
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
                            crear_boton("+ AGREGAR PAGO", on_click=agregar_pago, bgcolor=COLOR_VERDE, color="#FFFFFF", expand=True, height=42),
                            crear_boton("LIMPIAR", on_click=lambda e: (sesion["pagos"].clear(), refrescar_pagos()), bgcolor=COLOR_ROJO, color="#FFFFFF", height=42),
                        ]
                    ),
                    lista_pagos,
                    ft.Divider(),
                    lbl_factura,
                    crear_boton("AGREGAR / EDITAR FACTURA", on_click=abrir_modal_factura, bgcolor=COLOR_MORADO, color="#FFFFFF", height=40),
                    crear_boton("CONFIRMAR COBRO", on_click=confirmar_cobro, bgcolor=COLOR_AMARILLO, color="#000000", height=46),
                    panel_comprobante,
                ],
            ),
        )

    def vista_tickets():
        lista_tickets = ft.Column(spacing=8)
        lbl_estado = ft.Text("Cargando tickets...", size=13, color="#555555")

        def ver_detalle_ticket(venta):
            lineas = [
                f"Folio: {venta.get('folio', 'N/D')}",
                f"Fecha: {venta.get('fecha', 'N/D')}",
                f"Método: {venta.get('metodo_pago', 'N/D')}",
                f"Estado factura: {venta.get('estado_factura', 'Sin Factura')}",
                "",
                "PRODUCTOS:",
            ]
            for art in venta.get("articulos", []):
                lineas.append(f"• {art.get('producto', 'Producto')} x{art.get('cantidad', 0)} — ${float(art.get('subtotal', 0)):.2f}")
            lineas.extend(["", f"TOTAL: ${float(venta.get('total', 0)):.2f}"])

            url_pdf = preparar_pdf_ticket(venta)

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Ticket {venta.get('folio', '')}"),
                content=ft.Column(tight=True, scroll=ft.ScrollMode.AUTO, controls=[ft.Text("\n".join(lineas), size=13)]),
                actions=[
                    ft.TextButton(content=ft.Text("Cerrar"), on_click=lambda e: cerrar_dialogo(dlg)),
                    crear_boton("GUARDAR PDF", on_click=None, bgcolor=COLOR_AMARILLO, color="#000000", url=url_pdf),
                ],
            )
            abrir_dialogo(dlg)

        def pintar_tickets(ventas):
            lista_tickets.controls.clear()
            if not ventas:
                lbl_estado.value = "No hay compras registradas."
            else:
                lbl_estado.value = f"Mostrando últimos {min(len(ventas), 25)} tickets."
                for v in ventas[:25]:
                    url_pdf = preparar_pdf_ticket(v)
                    lista_tickets.controls.append(
                        ft.Container(
                            bgcolor="#FFFFFF",
                            border=borde_all(1, "#DDDDDD"),
                            border_radius=8,
                            padding=10,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Column(
                                        expand=True,
                                        spacing=2,
                                        controls=[
                                            ft.Text(f"{v.get('folio', '')} — ${float(v.get('total', 0)):.2f}", weight=ft.FontWeight.BOLD, size=14),
                                            ft.Text(f"{v.get('fecha', '')} | {v.get('metodo_pago', '')}", size=12, color="#555555"),
                                        ],
                                    ),
                                    ft.Row(
                                        spacing=4,
                                        controls=[
                                            ft.IconButton(icon=ICONS.VISIBILITY, icon_color=COLOR_AZUL, tooltip="Ver detalle", on_click=lambda e, venta=v: ver_detalle_ticket(venta)),
                                            crear_boton("PDF", on_click=None, bgcolor=COLOR_AMARILLO, color="#000000", url=url_pdf),
                                        ],
                                    ),
                                ],
                            ),
                        )
                    )
            page.update()

        def cargar_datos(forzar=False):
            if not forzar and sesion["ventas_cache"] is not None:
                pintar_tickets(sesion["ventas_cache"])
                return

            lbl_estado.value = "Consultando tickets..."
            lista_tickets.controls.clear()
            page.update()

            def _worker():
                try:
                    ventas = repo_ventas.obtener_todas(limite=50) or []
                    sesion["ventas_cache"] = ventas
                    pintar_tickets(ventas)
                except Exception as exc:
                    lbl_estado.value = f"Error al cargar tickets: {exc}"
                    page.update()

            threading.Thread(target=_worker, daemon=True).start()

        cargar_datos(forzar=False)

        return ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Tickets de Venta", weight=ft.FontWeight.BOLD, size=17, color=COLOR_MARCA),
                        crear_boton("ACTUALIZAR", on_click=lambda e: cargar_datos(forzar=True), bgcolor=COLOR_AZUL, color="#FFFFFF"),
                    ],
                ),
                lbl_estado,
                lista_tickets,
            ],
        )

    def vista_historial():
        txt_fecha = ft.TextField(label="Filtrar fecha (AAAA-MM-DD, vacío = recientes)", bgcolor="#FFFFFF", dense=True, expand=True)
        lbl_info = ft.Text("Ventas recientes", size=14, weight=ft.FontWeight.BOLD, color=COLOR_AZUL)
        lista_hist = ft.Column(spacing=6)

        def pintar_historial(ventas):
            filtro = (txt_fecha.value or "").strip()
            filtradas = [v for v in ventas if not filtro or str(v.get("fecha", "")).startswith(filtro)]
            lbl_info.value = f"Registros mostrados: {min(len(filtradas), 25)}"

            lista_hist.controls.clear()
            if not filtradas:
                lista_hist.controls.append(ft.Text("No se encontraron ventas para ese filtro.", size=13, color="#666666"))
            else:
                for v in filtradas[:25]:
                    prods_txt = ", ".join(f"{a.get('producto', '')} (x{a.get('cantidad', 0)})" for a in v.get("articulos", []))
                    lista_hist.controls.append(
                        ft.Container(
                            bgcolor="#FFFFFF",
                            border=borde_all(1, "#DDDDDD"),
                            border_radius=8,
                            padding=10,
                            content=ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text(v.get("folio", ""), weight=ft.FontWeight.BOLD, size=13),
                                            ft.Text(f"${float(v.get('total', 0)):.2f}", weight=ft.FontWeight.BOLD, color=COLOR_VERDE, size=13),
                                        ],
                                    ),
                                    ft.Text(f"{v.get('fecha', '')}  |  {v.get('metodo_pago', '')}  |  {v.get('estado_factura', '')}", size=11, color="#555555"),
                                    ft.Text(prods_txt or "Sin detalle", size=12, color="#333333"),
                                ],
                            ),
                        )
                    )
            page.update()

        def buscar_historial(e=None, forzar=False):
            if not forzar and sesion["ventas_cache"] is not None:
                pintar_historial(sesion["ventas_cache"])
                return

            lbl_info.value = "Consultando ventas..."
            lista_hist.controls.clear()
            page.update()

            def _worker():
                try:
                    ventas = repo_ventas.obtener_todas(limite=50) or []
                    sesion["ventas_cache"] = ventas
                    pintar_historial(ventas)
                except Exception as exc:
                    lbl_info.value = f"Error: {exc}"
                    page.update()

            threading.Thread(target=_worker, daemon=True).start()

        buscar_historial(forzar=False)

        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("Historial de Ventas", weight=ft.FontWeight.BOLD, size=17, color=COLOR_MARCA),
                ft.Row(
                    controls=[
                        txt_fecha,
                        crear_boton("BUSCAR", on_click=lambda e: buscar_historial(forzar=True), bgcolor=COLOR_AMARILLO, color="#000000"),
                    ]
                ),
                lbl_info,
                lista_hist,
            ],
        )

    def vista_cierre_caja():
        resumen = modelo.obtener_resumen_turno_db(sesion["id_turno"])
        txt_efectivo = ft.TextField(
            label="Efectivo físico contado ($)",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="#FFFFFF",
        )

        inicio = resumen.get("fecha_hora_inicio")
        inicio_str = inicio.strftime("%d/%m/%Y %H:%M:%S") if hasattr(inicio, "strftime") else str(inicio or "N/D")

        filas = [
            ("Usuario / Rol:", f"{sesion['usuario']} ({sesion['rol']})"),
            ("Caja / Turno:", f"{resumen.get('numero_caja', 'N/D')} (Corte #{sesion['id_turno']})"),
            ("Inicio de turno:", inicio_str),
            ("Fondo inicial:", f"${resumen.get('fondo_inicial', 500.0):,.2f}"),
            ("Ventas realizadas:", f"{resumen.get('num_ventas', 0)} (Total: ${resumen.get('total_ventas', 0.0):,.2f})"),
            ("Cobros con tarjeta:", f"${resumen.get('total_tarjeta_cobrado', 0.0):,.2f}"),
        ]

        def finalizar_turno(e):
            try:
                contado = round(float((txt_efectivo.value or "").strip()), 2)
                if contado < 0:
                    raise ValueError
            except ValueError:
                mostrar_aviso("Ingresa un monto válido (0 o mayor).", COLOR_ROJO)
                return

            modelo._ejecutar_consulta(
                "UPDATE cortes_caja SET fecha_hora_fin=NOW(), efectivo_contado=%s, estado='cerrado' WHERE id_corte_caja=%s",
                (contado, sesion["id_turno"]),
            )
            modelo.ticket_actual.clear()
            sesion["pagos"].clear()
            sesion["datos_factura"] = None
            sesion["ultimo_comprobante"] = None
            sesion["id_turno"] = None
            sesion["ventas_cache"] = None
            mostrar_aviso("Turno finalizado y corte de caja registrado.", COLOR_VERDE)
            mostrar_login()

        return ft.Container(
            bgcolor="#FFFFFF",
            border=borde_all(1, "#DDDDDD"),
            border_radius=10,
            padding=16,
            content=ft.Column(
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Text("CIERRE DE CAJA", weight=ft.FontWeight.BOLD, size=18, color=COLOR_MARCA, text_align=ft.TextAlign.CENTER),
                    ft.Text("Es obligatorio realizar el corte antes de cerrar sesión", size=12, color="#555555", text_align=ft.TextAlign.CENTER),
                    ft.Divider(),
                    *[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(k, weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(v, size=13),
                            ],
                        )
                        for k, v in filas
                    ],
                    ft.Divider(),
                    txt_efectivo,
                    crear_boton(
                        "FINALIZAR TURNO Y CERRAR SESIÓN",
                        on_click=finalizar_turno,
                        bgcolor=COLOR_ROJO,
                        color="#FFFFFF",
                        height=46,
                    ),
                ],
            ),
        )

    def cambiar_seccion(indice):
        sesion["vista_actual"] = indice
        if page.navigation_bar:
            page.navigation_bar.selected_index = indice
        vistas = [vista_punto_venta, vista_cobros, vista_tickets, vista_historial, vista_cierre_caja]
        contenedor_cuerpo.content = vistas[indice]()
        page.update()

    def cargar_layout_principal():
        page.controls.clear()
        page.appbar = ft.AppBar(
            title=ft.Text(f"🍬 Algorrico — {sesion['usuario']}", color="#FFFFFF", weight=ft.FontWeight.BOLD, size=15),
            bgcolor=COLOR_MARCA,
            actions=[
                ft.IconButton(
                    icon=ICONS.LOGOUT,
                    icon_color="#FFFFFF",
                    tooltip="Cierre de Caja",
                    on_click=lambda e: cambiar_seccion(4),
                )
            ],
        )

        page.navigation_bar = ft.NavigationBar(
            selected_index=0,
            bgcolor="#FFFFFF",
            on_change=lambda e: cambiar_seccion(e.control.selected_index),
            destinations=[
                ft.NavigationBarDestination(icon=ICONS.POINT_OF_SALE, label="Venta"),
                ft.NavigationBarDestination(icon=ICONS.PAYMENTS, label="Cobros"),
                ft.NavigationBarDestination(icon=ICONS.RECEIPT_LONG, label="Tickets"),
                ft.NavigationBarDestination(icon=ICONS.HISTORY, label="Historial"),
                ft.NavigationBarDestination(icon=ICONS.LOCK_CLOCK, label="Cierre"),
            ],
        )

        page.add(contenedor_cuerpo)
        cambiar_seccion(0)

    mostrar_login()


if __name__ == "__main__":
    puerto = int(os.getenv("PORT", 8550))
    host = "0.0.0.0" if os.getenv("RENDER") else "127.0.0.1"
    if hasattr(ft, "run"):
        ft.run(main, view=ft.AppView.WEB_BROWSER, host=host, port=puerto, assets_dir=DIR_ASSETS)
    else:
        ft.app(target=main, view=ft.AppView.WEB_BROWSER, host=host, port=puerto, assets_dir=DIR_ASSETS)