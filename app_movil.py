import os
import flet as ft
from modelos.modelo import ModeloDulceria
from servicios.repositorio_ventas import RepositorioVentas

# Compatibilidad entre versiones de Flet (0.x y 0.80+ / 1.0)
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
LIMITE_RENDER = 20  # Paginación para reducir uso de RAM y bateria en celular


def borde_all(ancho, color):
    clase = getattr(ft, "Border", None)
    if clase and hasattr(clase, "all"):
        return clase.all(ancho, color)
    return ft.border.all(ancho, color)


def padding_simetrico(horizontal=0, vertical=0):
    clase = getattr(ft, "Padding", None)
    if clase and hasattr(clase, "symmetric"):
        return clase.symmetric(horizontal=horizontal, vertical=vertical)
    return ft.padding.symmetric(horizontal=horizontal, vertical=vertical)


def crear_boton(texto, on_click, bgcolor=None, color=None, width=None, height=None, expand=False):
    return BTN_CLS(
        content=ft.Text(texto, color=color, weight=ft.FontWeight.BOLD),
        bgcolor=bgcolor,
        color=color,
        width=width,
        height=height,
        expand=expand,
        on_click=on_click,
    )


def conectar_dropdown(cmb, callback):
    if hasattr(cmb, "on_select"):
        cmb.on_select = callback
    else:
        cmb.on_change = callback


def main(page: ft.Page):
    page.title = "Dulcería Algorrico - Multiplataforma"
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

    # ==========================================================
    # 1. PANTALLA DE LOGIN Y APERTURA DE CAJA 
    # ==========================================================
    def mostrar_login():
        page.appbar = None
        page.navigation_bar = None
        page.controls.clear()

        txt_user = ft.TextField(label="Usuario", width=300, bgcolor="#FFFFFF")
        txt_pass = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            width=300,
            bgcolor="#FFFFFF",
        )
        cmb_caja = ft.Dropdown(
            label="Caja a operar (1-4)",
            width=300,
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

            sesion["usuario"] = u
            sesion["id_usuario"] = user_data["id_usuario"]
            sesion["rol"] = modelo.obtener_rol(user_data["id_rol"])

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

            mostrar_aviso(f"Bienvenido, {u} ({sesion['rol']})", COLOR_VERDE)
            cargar_layout_principal()

        txt_pass.on_submit = iniciar_sesion

        tarjeta_login = ft.Container(
            bgcolor="#FFFFFF",
            border=borde_all(2, "#F3C6D1"),
            border_radius=12,
            padding=28,
            width=360,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    ft.Text("🍬 Algorrico", size=28, weight=ft.FontWeight.BOLD, color=COLOR_MARCA),
                    ft.Text("Acceso Móvil y Escritorio", size=14, color="#555555"),
                    txt_user,
                    txt_pass,
                    cmb_caja,
                    crear_boton(
                        "INGRESAR AL SISTEMA",
                        on_click=iniciar_sesion,
                        bgcolor=COLOR_MARCA,
                        color="#FFFFFF",
                        width=300,
                        height=44,
                    ),
                ],
            ),
        )

        page.add(
            ft.Container(
                expand=True,
                alignment=ALIGN_CENTER,
                padding=20,
                content=tarjeta_login,
            )
        )
        page.update()

    # ==========================================================
    # 2. CIERRE DE CAJA OBLIGATORIO
    # ==========================================================
    def abrir_cierre_caja(e=None):
        resumen = modelo.obtener_resumen_turno_db(sesion["id_turno"])
        es_admin = sesion["rol"] == "Administrador"
        txt_efectivo = ft.TextField(
            label="Efectivo físico contado ($)",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        lineas = [
            f"Usuario: {sesion['usuario']} ({sesion['rol']})",
            f"Caja: {resumen.get('numero_caja', 'N/D')} (Turno #{sesion['id_turno']})",
            f"Fondo inicial: ${resumen.get('fondo_inicial', 500.0):,.2f}",
            f"Ventas realizadas: {resumen.get('num_ventas', 0)} (${resumen.get('total_ventas', 0.0):,.2f})",
            f"Cobros tarjeta: ${resumen.get('total_tarjeta_cobrado', 0.0):,.2f}",
        ]
        if es_admin:
            lineas.append(f"Efectivo esperado: ${resumen.get('efectivo_esperado', 500.0):,.2f}")

        def confirmar_cierre(ev):
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
            sesion["id_turno"] = None
            cerrar_dialogo(dlg)
            mostrar_aviso("Corte de caja cerrado correctamente.", COLOR_VERDE)
            mostrar_login()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cierre de Caja Obligatorio"),
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=[ft.Text("\n".join(lineas), size=13), txt_efectivo],
            ),
            actions=[
                ft.TextButton(content=ft.Text("Cancelar"), on_click=lambda ev: cerrar_dialogo(dlg)),
                crear_boton("Confirmar cierre", on_click=confirmar_cierre, bgcolor=COLOR_ROJO, color="#FFFFFF"),
            ],
        )
        abrir_dialogo(dlg)

    # ==========================================================
    # 3. VISTAS PRINCIPALES ADAPTABLES
    # ==========================================================
    contenedor_cuerpo = ft.Container(padding=15, expand=True)

    def vista_inicio():
        inv = modelo.inventario
        activos = [p for p in inv if p["stock"] > 0]
        top_bajo = sorted(inv, key=lambda p: p["stock"])[:5]

        card_catalogo = ft.Container(
            col={"xs": 12, "md": 4},
            bgcolor="#FFFFFF",
            border=borde_all(2, COLOR_MARCA),
            border_radius=10,
            padding=18,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Text("Estado del catálogo", weight=ft.FontWeight.BOLD, size=15),
                    ft.Container(
                        bgcolor=COLOR_MARCA,
                        border_radius=8,
                        padding=padding_simetrico(horizontal=18, vertical=8),
                        content=ft.Text(str(len(activos)), size=26, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    ),
                    ft.Text("productos activos", color="#555555"),
                ],
            ),
        )

        filas_bajo = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(p["nombre"], expand=True, size=13),
                    ft.Text(
                        str(p["stock"]),
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_ROJO if p["stock"] <= p.get("stock_minimo", 5) else "#333333",
                    ),
                ],
            )
            for p in top_bajo
        ]

        card_stock = ft.Container(
            col={"xs": 12, "md": 4},
            bgcolor="#FFFFFF",
            border=borde_all(2, COLOR_MARCA),
            border_radius=10,
            padding=18,
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text("Stock más bajo (Top 5)", weight=ft.FontWeight.BOLD, size=15),
                    ft.Divider(height=1),
                    *filas_bajo,
                ],
            ),
        )

        card_venta = ft.Container(
            col={"xs": 12, "md": 4},
            bgcolor="#FFFFFF",
            border=borde_all(2, COLOR_MARCA),
            border_radius=10,
            padding=18,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Text("Punto de Venta", weight=ft.FontWeight.BOLD, size=15),
                    ft.Text(f"Turno #{sesion['id_turno']} activo y sincronizado con MySQL.", text_align=ft.TextAlign.CENTER, size=13),
                    crear_boton(
                        "INICIAR VENTA",
                        on_click=lambda e: cambiar_seccion(1),
                        bgcolor=COLOR_AMARILLO,
                        color="#000000",
                        width=200,
                        height=44,
                    ),
                ],
            ),
        )

        return ft.ResponsiveRow(controls=[card_catalogo, card_stock, card_venta], spacing=12, run_spacing=12)

    def vista_venta():
        txt_buscar = ft.TextField(label="Buscar dulce (inicio de nombre o código)", bgcolor="#FFFFFF")
        lista_prods = ft.Column(spacing=6)
        lista_carrito = ft.Column(spacing=6)
        lbl_desglose = ft.Text("", size=13, color="#555555")
        lbl_total = ft.Text("TOTAL: $0.00", size=18, weight=ft.FontWeight.BOLD, color=COLOR_VERDE)

        cmb_metodo = ft.Dropdown(
            label="Método de pago",
            value="Efectivo",
            options=[
                OPT_CLS(key="Efectivo", text="Efectivo"),
                OPT_CLS(key="Tarjeta de débito", text="Tarjeta de débito"),
                OPT_CLS(key="Tarjeta de crédito", text="Tarjeta de crédito"),
            ],
        )
        txt_monto = ft.TextField(label="Monto recibido ($)", keyboard_type=ft.KeyboardType.NUMBER, bgcolor="#FFFFFF")
        txt_ref = ft.TextField(label="Referencia tarjeta (si aplica)", bgcolor="#FFFFFF", disabled=True)
        lbl_pagos = ft.Text("Pagos agregados: $0.00", size=13, weight=ft.FontWeight.BOLD)

        def on_metodo_change(e):
            es_ef = cmb_metodo.value == "Efectivo"
            txt_ref.disabled = es_ef
            if es_ef:
                txt_ref.value = ""
            page.update()

        conectar_dropdown(cmb_metodo, on_metodo_change)

        def refrescar_carrito():
            lista_carrito.controls.clear()
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
                                    spacing=4,
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
            lbl_desglose.value = f"Subtotal (sin IVA): ${sub:.2f}  |  IVA incluido (16%): ${iva:.2f}"
            lbl_total.value = f"TOTAL (IVA incl.): ${total:.2f}"
            pagado = round(sum(p["monto"] for p in sesion["pagos"]), 2)
            restante = round(max(0.0, total - pagado), 2)
            cambio = round(max(0.0, pagado - total), 2)
            lbl_pagos.value = f"Pagado: ${pagado:.2f}  |  Restante: ${restante:.2f}  |  Cambio: ${cambio:.2f}"
            if restante > 0 and not txt_monto.value:
                txt_monto.value = f"{restante:.2f}"
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

        def refrescar_catalogo(e=None):
            lista_prods.controls.clear()
            texto = (txt_buscar.value or "").strip().lower()
            prods = modelo.inventario
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
            refrescar_carrito()

        def confirmar_cobro(e):
            if not modelo.ticket_actual:
                mostrar_aviso("El carrito está vacío.", COLOR_ROJO)
                return
            total = modelo.calcular_total()
            pagado = round(sum(p["monto"] for p in sesion["pagos"]), 2)
            if pagado < total:
                mostrar_aviso(f"Faltan ${total - pagado:.2f} por cubrir.", COLOR_ROJO)
                return

            def ejecutar_cobro(ev):
                cerrar_dialogo(dlg_conf)
                try:
                    resumen = repo_ventas.registrar(modelo.ticket_actual, sesion["pagos"], sesion["id_turno"])
                    modelo.ticket_actual.clear()
                    sesion["pagos"].clear()
                    modelo.invalidar_inventario()
                    mostrar_aviso(f"Venta {resumen['folio']} guardada. Cambio: ${resumen['cambio']:.2f}", COLOR_VERDE)
                    refrescar_catalogo()
                    refrescar_carrito()
                except Exception as ex:
                    mostrar_aviso(f"Error al cobrar: {ex}", COLOR_ROJO)

            dlg_conf = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar Venta (Regla #4)"),
                content=ft.Text(
                    f"Total a cobrar: ${total:.2f}\nRecibido: ${pagado:.2f}\nCambio: ${pagado - total:.2f}\n\n"
                    "No se aceptan cambios ni devoluciones. ¿Confirmar cobro?"
                ),
                actions=[
                    ft.TextButton(content=ft.Text("Cancelar"), on_click=lambda ev: cerrar_dialogo(dlg_conf)),
                    crear_boton("Confirmar", on_click=ejecutar_cobro, bgcolor=COLOR_VERDE, color="#FFFFFF"),
                ],
            )
            abrir_dialogo(dlg_conf)

        txt_buscar.on_change = refrescar_catalogo
        refrescar_catalogo()
        refrescar_carrito()

        panel_catalogo = ft.Container(
            col={"xs": 12, "md": 6},
            content=ft.Column(spacing=10, controls=[ft.Text("Catálogo (Top 20)", weight=ft.FontWeight.BOLD, size=15), txt_buscar, lista_prods]),
        )

        panel_ticket = ft.Container(
            col={"xs": 12, "md": 6},
            bgcolor="#F4F4F4",
            border=borde_all(1, "#CCCCCC"),
            border_radius=10,
            padding=14,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text("Ticket y Cobro", weight=ft.FontWeight.BOLD, size=15),
                    lista_carrito,
                    ft.Divider(),
                    lbl_desglose,
                    lbl_total,
                    cmb_metodo,
                    txt_monto,
                    txt_ref,
                    ft.Row(
                        controls=[
                            crear_boton("+ Pago", on_click=agregar_pago, bgcolor=COLOR_AZUL, color="#FFFFFF", expand=True),
                            ft.OutlinedButton(content=ft.Text("Limpiar pagos"), on_click=lambda e: (sesion["pagos"].clear(), refrescar_carrito())),
                        ]
                    ),
                    lbl_pagos,
                    crear_boton("CONFIRMAR COBRO", on_click=confirmar_cobro, bgcolor=COLOR_VERDE, color="#FFFFFF", height=44, width=400),
                ],
            ),
        )

        return ft.ResponsiveRow(controls=[panel_catalogo, panel_ticket], spacing=15, run_spacing=15)

    def vista_inventario():
        txt_buscar = ft.TextField(label="Buscar en inventario (inicio)", bgcolor="#FFFFFF", expand=True)
        cmb_estado = ft.Dropdown(
            label="Estado",
            width=140,
            value="Todos",
            options=[OPT_CLS(key=x, text=x) for x in ("Todos", "AGOTADO", "BAJO", "OK")],
        )
        lista_inv = ft.Column(spacing=6)

        def cargar_inv(e=None):
            lista_inv.controls.clear()
            texto = (txt_buscar.value or "").strip().lower()
            filtro = cmb_estado.value

            for p in modelo.inventario:
                if texto and not (
                    p["nombre"].lower().startswith(texto)
                    or str(p.get("codigo_barras") or "").lower().startswith(texto)
                ):
                    continue
                stock = int(p["stock"])
                minimo = int(p.get("stock_minimo") or 5)
                estado = "AGOTADO" if stock == 0 else ("BAJO" if stock <= minimo else "OK")
                if filtro != "Todos" and estado != filtro:
                    continue

                bg_fila = "#FADBD8" if estado == "AGOTADO" else ("#FCF3CF" if estado == "BAJO" else "#FFFFFF")
                lista_inv.controls.append(
                    ft.Container(
                        bgcolor=bg_fila,
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
                                        ft.Text(f"Precio: ${p['precio']:.2f}  |  Mínimo: {minimo}", size=12, color="#555555"),
                                    ],
                                ),
                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                    spacing=2,
                                    controls=[
                                        ft.Text(f"Stock: {stock}", weight=ft.FontWeight.BOLD, size=13),
                                        ft.Text(estado, size=11, weight=ft.FontWeight.BOLD, color=COLOR_ROJO if estado != "OK" else COLOR_VERDE),
                                    ],
                                ),
                            ],
                        ),
                    )
                )
                if len(lista_inv.controls) >= 30:
                    break
            page.update()

        txt_buscar.on_change = cargar_inv
        conectar_dropdown(cmb_estado, cargar_inv)
        cargar_inv()

        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("Inventario en Tiempo Real (Sincronizado)", weight=ft.FontWeight.BOLD, size=16),
                ft.Row(controls=[txt_buscar, cmb_estado]),
                lista_inv,
            ],
        )

    def vista_apartados():
        lista_ap = ft.Column(spacing=8)
        for item in modelo.obtener_apartados()[:25]:
            estado = str(item["estado"]).lower()
            total = round(float(item["subtotal"]) + float(item["impuesto"]), 2)
            pagado = round(float(item["pagado"]), 2)
            bg = "#FCF3CF" if estado == "pendiente" else ("#EAFAF1" if estado == "liquidado" else "#FADBD8")
            lista_ap.controls.append(
                ft.Container(
                    bgcolor=bg,
                    border=borde_all(1, "#CCCCCC"),
                    border_radius=8,
                    padding=10,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(f"#{item['id_apartado']} - {item['nombre']}", weight=ft.FontWeight.BOLD, size=13),
                                    ft.Text(estado.upper(), weight=ft.FontWeight.BOLD, size=12),
                                ],
                            ),
                            ft.Text(f"Productos: {item['producto']}", size=12),
                            ft.Text(f"Entrega: {item['fecha']}  |  Total: ${total:.2f}  |  Pagado: ${pagado:.2f}", size=12, color="#444444"),
                        ],
                    ),
                )
            )
        return ft.Column(spacing=10, controls=[ft.Text("Apartados (Pendientes primero)", weight=ft.FontWeight.BOLD, size=16), lista_ap])

    def cambiar_seccion(indice):
        sesion["vista_actual"] = indice
        if page.navigation_bar:
            page.navigation_bar.selected_index = indice
        vistas = [vista_inicio, vista_venta, vista_inventario, vista_apartados]
        contenedor_cuerpo.content = vistas[indice]()
        page.update()

    def cargar_layout_principal():
        page.controls.clear()
        page.appbar = ft.AppBar(
            title=ft.Text(f"🍬 Algorrico — {sesion['usuario']}", color="#FFFFFF", weight=ft.FontWeight.BOLD, size=16),
            bgcolor=COLOR_MARCA,
            actions=[
                ft.IconButton(
                    icon=ICONS.LOGOUT,
                    icon_color="#FFFFFF",
                    tooltip="Cierre de Caja y Salir",
                    on_click=abrir_cierre_caja,
                )
            ],
        )

        page.navigation_bar = ft.NavigationBar(
            selected_index=0,
            bgcolor="#FFFFFF",
            on_change=lambda e: cambiar_seccion(e.control.selected_index),
            destinations=[
                ft.NavigationBarDestination(icon=ICONS.HOME, label="Inicio"),
                ft.NavigationBarDestination(icon=ICONS.POINT_OF_SALE, label="Venta"),
                ft.NavigationBarDestination(icon=ICONS.INVENTORY, label="Inventario"),
                ft.NavigationBarDestination(icon=ICONS.BOOKMARK, label="Apartados"),
            ],
        )

        page.add(contenedor_cuerpo)
        cambiar_seccion(0)

    mostrar_login()


if __name__ == "__main__":
    puerto = int(os.getenv("PORT", 8550))
    if hasattr(ft, "run"):
        ft.run(main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=puerto)
    else:
        ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=puerto)