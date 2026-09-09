import tkinter as tk
from tkinter import messagebox, ttk

# ============================================================
# COLORES
# ============================================================

ROSA_CLARO = "#F4C2CC"
ROSA_MENU = "#CF3D5B"
ROSA_MENU_ACTIVO = "#B52E4B"
FONDO = "#FFF9F5"
BLANCO = "#FFFFFF"
NEGRO = "#000000"


# ============================================================
# VENTANA PRINCIPAL
# ============================================================

class VistaDulceria(tk.Tk):

    def __init__(self, controlador):

        super().__init__()

        self.controlador = controlador

        self.title("Dulcería")
        self.geometry("1000x650")
        self.resizable(False, False)
        self.configure(bg=FONDO)

        self.contenedor = tk.Frame(
            self,
            bg=FONDO
        )

        self.contenedor.pack(
            fill="both",
            expand=True
        )

        self.contenedor.grid_rowconfigure(
            0,
            weight=1
        )

        self.contenedor.grid_columnconfigure(
            0,
            weight=1
        )

        self.pantallas = {}

        for Pantalla in (
            PantallaLogin,
            PantallaPrincipal
        ):

            frame = Pantalla(
                parent=self.contenedor,
                controlador=self.controlador
            )

            self.pantallas[Pantalla.__name__] = frame

            frame.grid(
                row=0,
                column=0,
                sticky="nsew"
            )

        self.mostrar_pantalla(
            "PantallaLogin"
        )


    def mostrar_pantalla(self, nombre):

        self.pantallas[nombre].tkraise()


    def mostrar_alerta(
        self,
        titulo,
        mensaje,
        tipo="info"
    ):

        if tipo == "info":

            messagebox.showinfo(
                titulo,
                mensaje
            )

        else:

            messagebox.showerror(
                titulo,
                mensaje
            )


# ============================================================
# INICIO DE SESIÓN
# ============================================================

class PantallaLogin(tk.Frame):

    def __init__(
        self,
        parent,
        controlador
    ):

        super().__init__(
            parent,
            bg=FONDO
        )

        self.controlador = controlador

        tk.Label(
            self,
            text="Inicio de Sesión - Dulcería",
            font=("Arial", 20, "bold"),
            bg=FONDO
        ).pack(
            pady=(100, 30)
        )

        tk.Label(
            self,
            text="Usuario:",
            font=("Arial", 11),
            bg=FONDO
        ).pack(
            pady=5
        )

        self.txt_usuario = tk.Entry(
            self,
            width=30,
            font=("Arial", 11)
        )

        self.txt_usuario.pack(
            pady=5
        )

        tk.Label(
            self,
            text="Contraseña:",
            font=("Arial", 11),
            bg=FONDO
        ).pack(
            pady=5
        )

        self.txt_password = tk.Entry(
            self,
            show="*",
            width=30,
            font=("Arial", 11)
        )

        self.txt_password.pack(
            pady=5
        )

        tk.Button(
            self,
            text="Ingresar",
            command=self.enviar_datos,
            width=18,
            bg=ROSA_MENU,
            fg=BLANCO,
            activebackground=ROSA_MENU_ACTIVO,
            activeforeground=BLANCO,
            bd=0,
            font=("Arial", 10, "bold")
        ).pack(
            pady=25
        )

        self.txt_password.bind(
            "<Return>",
            lambda event: self.enviar_datos()
        )


    def enviar_datos(self):

        usuario = self.txt_usuario.get().strip()

        password = self.txt_password.get()

        self.controlador.procesar_login(
            usuario,
            password
        )


# ============================================================
# PANTALLA PRINCIPAL
# ============================================================

class PantallaPrincipal(tk.Frame):

    def __init__(
        self,
        parent,
        controlador
    ):

        super().__init__(
            parent,
            bg=FONDO
        )

        self.controlador = controlador

        # ====================================================
        # ENCABEZADO
        # ====================================================

        encabezado = tk.Frame(
            self,
            bg=ROSA_CLARO,
            height=115
        )

        encabezado.pack(
            fill="x"
        )

        encabezado.pack_propagate(False)

        tk.Label(
            encabezado,
            text="🍬",
            font=("Segoe UI Emoji", 40),
            bg=ROSA_CLARO
        ).place(
            x=45,
            y=25
        )

        # Botón cerrar sesión

        btn_logout = tk.Button(
            encabezado,
            text="Cerrar Sesión",
            bg="#D9534F",
            fg=BLANCO,
            font=("Arial", 8, "bold"),
            activebackground="#C9302C",
            activeforeground=BLANCO,
            relief="flat",
            cursor="hand2",
            command=self.controlador.cerrar_sesion
        )

        btn_logout.place(
            relx=0.82,
            y=88,
            anchor="center"
        )

        tk.Label(
            encabezado,
            text="Dulcería",
            font=("Segoe Script", 25),
            bg=ROSA_CLARO,
            fg=NEGRO
        ).place(
            x=115,
            y=33
        )

        self.lbl_usuario = tk.Label(
            encabezado,
            text="",
            font=("Arial", 10, "bold"),
            bg=ROSA_CLARO,
            fg=NEGRO
        )

        self.lbl_usuario.place(
            relx=0.91,
            y=88,
            anchor="center"
        )

        # Icono de usuario

        icono = tk.Canvas(
            encabezado,
            width=55,
            height=65,
            bg=ROSA_CLARO,
            highlightthickness=0
        )

        icono.place(
            relx=0.94,
            y=15
        )

        icono.create_oval(
            14,
            2,
            38,
            26,
            fill=NEGRO,
            outline=NEGRO
        )

        icono.create_arc(
            5,
            28,
            48,
            66,
            start=0,
            extent=180,
            fill=NEGRO,
            outline=NEGRO
        )

        # ====================================================
        # MENÚ
        # ====================================================

        menu = tk.Frame(
            self,
            bg=ROSA_MENU,
            height=42
        )

        menu.pack(
            fill="x"
        )

        menu.pack_propagate(False)

        opciones = [
            "INICIO",
            "NUEVA VENTA",
            "INVENTARIO",
            "AGOTADOS",
            "APARTADOS",
            "HISTORIAL"
        ]

        self.botones_menu = {}

        for opcion in opciones:

            boton = tk.Button(
                menu,
                text=opcion,
                bg=ROSA_MENU,
                fg=BLANCO,
                activebackground=ROSA_MENU_ACTIVO,
                activeforeground=BLANCO,
                bd=0,
                relief="flat",
                font=("Arial", 9, "bold"),
                cursor="hand2",
                command=lambda op=opcion:
                self.mostrar_seccion(op)
            )

            boton.pack(
                side="left",
                fill="both",
                expand=True
            )

            self.botones_menu[opcion] = boton

        # ====================================================
        # CONTENIDO
        # ====================================================

        self.contenido = tk.Frame(
            self,
            bg=FONDO
        )

        self.contenido.pack(
            fill="both",
            expand=True
        )


    # ========================================================
    # ACTUALIZAR USUARIO
    # ========================================================

    def actualizar_usuario(
        self,
        usuario
    ):

        self.lbl_usuario.config(
            text=usuario
        )


    # ========================================================
    # MOSTRAR SECCIÓN
    # ========================================================

    def mostrar_seccion(
        self,
        opcion
    ):

        for nombre, boton in self.botones_menu.items():

            if nombre == opcion:

                boton.config(
                    bg=ROSA_MENU_ACTIVO
                )

            else:

                boton.config(
                    bg=ROSA_MENU
                )

        # Limpiar contenido anterior

        for widget in self.contenido.winfo_children():

            widget.destroy()

        # ====================================================
        # NUEVA VENTA
        # ====================================================

        if opcion == "NUEVA VENTA":

            self.construir_nueva_venta()

        # ====================================================
        # INVENTARIO
        # ====================================================

        elif opcion == "INVENTARIO":

            self.construir_inventario()

        # ====================================================
        # APARTADOS
        # ====================================================

        elif opcion == "APARTADOS":

            self.construir_apartados()

        # ====================================================
        # OTRAS SECCIONES
        # ====================================================

        else:

            textos = {

                "INICIO": "Inicio",

                "AGOTADOS":
                "Productos agotados",

                "HISTORIAL":
                "Historial"
            }

            tk.Label(
                self.contenido,
                text=textos.get(
                    opcion,
                    opcion
                ),
                font=("Arial", 22, "bold"),
                bg=FONDO,
                fg="#333333"
            ).pack(
                pady=60
            )


    # ========================================================
    # NUEVA VENTA
    # ========================================================

    def construir_nueva_venta(self):

        panel_izq = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        panel_izq.pack(
            side="left",
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        barra_busqueda = tk.Frame(
            panel_izq,
            bg="#3A8D96",
            height=40
        )

        barra_busqueda.pack(
            fill="x"
        )

        barra_busqueda.pack_propagate(False)

        tk.Label(
            barra_busqueda,
            text="BUSCAR PRODUCTO",
            bg="#3A8D96",
            fg=BLANCO,
            font=("Arial", 10, "bold")
        ).pack(
            side="left",
            padx=10
        )

        tk.Entry(
            barra_busqueda,
            width=20
        ).pack(
            side="right",
            padx=10,
            pady=8
        )

        frame_lista = tk.Frame(
            panel_izq,
            bg="#EAEAEA"
        )

        frame_lista.pack(
            fill="both",
            expand=True,
            pady=10
        )

        for producto in self.controlador.modelo.inventario:

            item = tk.Frame(
                frame_lista,
                bg=BLANCO,
                pady=10,
                padx=10,
                bd=1,
                relief="solid"
            )

            item.pack(
                fill="x",
                pady=2,
                padx=2
            )

            tk.Label(
                item,
                text=producto["nombre"],
                bg=BLANCO,
                font=("Arial", 9, "bold")
            ).grid(
                row=0,
                column=0,
                sticky="w",
                columnspan=2
            )

            tk.Label(
                item,
                text=f"${producto['precio']:.2f}",
                bg=BLANCO,
                font=("Arial", 9)
            ).grid(
                row=1,
                column=0,
                sticky="w",
                pady=5
            )

            tk.Label(
                item,
                text=f"STOCK: {producto['stock']}",
                bg=BLANCO,
                font=("Arial", 9)
            ).grid(
                row=1,
                column=1,
                sticky="w",
                padx=20
            )

            btn_agregar = tk.Button(
                item,
                text="AGREGAR",
                bg="#F4D03F",
                fg=NEGRO,
                font=("Arial", 9, "bold"),
                width=15,
                relief="flat",
                command=lambda p=producto["nombre"]:
                self.controlador.procesar_agregar(p)
            )

            btn_agregar.grid(
                row=0,
                column=2,
                rowspan=2,
                sticky="e",
                padx=10
            )

            item.grid_columnconfigure(
                2,
                weight=1
            )

        # ----------------------------------------------------
        # PANEL DERECHO
        # ----------------------------------------------------

        panel_der = tk.Frame(
            self.contenido,
            bg="#F4F4F4",
            bd=1,
            relief="solid"
        )

        panel_der.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(0, 20),
            pady=20
        )

        tk.Label(
            panel_der,
            text="TICKET DE VENTA",
            bg="#F4F4F4",
            font=("Arial", 10, "bold")
        ).pack(
            pady=10
        )

        columnas = (
            "PRODUCTO",
            "CANTIDAD",
            "PRECIO"
        )

        self.tabla_ticket = ttk.Treeview(
            panel_der,
            columns=columnas,
            show="headings",
            height=12
        )

        self.tabla_ticket.heading(
            "PRODUCTO",
            text="PRODUCTO"
        )

        self.tabla_ticket.heading(
            "CANTIDAD",
            text="CANTIDAD"
        )

        self.tabla_ticket.heading(
            "PRECIO",
            text="PRECIO"
        )

        self.tabla_ticket.column(
            "PRODUCTO",
            width=150
        )

        self.tabla_ticket.column(
            "CANTIDAD",
            width=80,
            anchor="center"
        )

        self.tabla_ticket.column(
            "PRECIO",
            width=80,
            anchor="center"
        )

        self.tabla_ticket.pack(
            fill="both",
            expand=True,
            padx=10
        )

        for item in self.controlador.modelo.ticket_actual:

            self.tabla_ticket.insert(
                "",
                "end",
                values=(
                    item["producto"],
                    item["cantidad"],
                    f"${item['subtotal']:.2f}"
                )
            )

        frame_total = tk.Frame(
            panel_der,
            bg="#F4F4F4"
        )

        frame_total.pack(
            fill="x",
            padx=20,
            pady=15
        )

        tk.Label(
            frame_total,
            text="TOTAL",
            bg="#F4F4F4",
            font=("Arial", 12, "bold")
        ).pack(
            side="left"
        )

        self.label_total = tk.Label(
            frame_total,
            text="$0.00",
            bg="#F4F4F4",
            font=("Arial", 12, "bold")
        )

        self.label_total.pack(
            side="right"
        )

        frame_botones = tk.Frame(
            panel_der,
            bg="#F4F4F4"
        )

        frame_botones.pack(
            fill="x",
            padx=10,
            pady=10
        )

        tk.Button(
            frame_botones,
            text="CANCELAR",
            bg="#F4D03F",
            font=("Arial", 10, "bold"),
            relief="flat"
        ).pack(
            side="left",
            expand=True,
            fill="x",
            padx=5
        )

        tk.Button(
            frame_botones,
            text="COBRAR",
            bg="#F4D03F",
            font=("Arial", 10, "bold"),
            relief="flat",
            command=self.controlador.cobrar_ticket
        ).pack(
            side="right",
            expand=True,
            fill="x",
            padx=5
        )


    # ========================================================
    # INVENTARIO
    # ========================================================

    def construir_inventario(self):

        panel_principal = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        panel_principal.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        barra_filtros = tk.Frame(
            panel_principal,
            bg="#3A8D96",
            height=40
        )

        barra_filtros.pack(
            fill="x",
            pady=(0, 10)
        )

        barra_filtros.pack_propagate(False)

        tk.Label(
            barra_filtros,
            text="BUSCAR",
            bg="#3A8D96",
            fg=BLANCO,
            font=("Arial", 9, "bold")
        ).pack(
            side="left",
            padx=10
        )

        self.txt_buscar_inv = tk.Entry(
            barra_filtros,
            width=18
        )

        self.txt_buscar_inv.pack(
            side="left",
            padx=5
        )

        self.txt_buscar_inv.bind(
            "<KeyRelease>",
            lambda e:
            self.aplicar_filtros_inventario()
        )

        tk.Label(
            barra_filtros,
            text="MARCA",
            bg="#3A8D96",
            fg=BLANCO,
            font=("Arial", 9, "bold")
        ).pack(
            side="left",
            padx=(15, 5)
        )

        self.combo_marca = ttk.Combobox(
            barra_filtros,
            values=[
                "Todas",
                "Ricolino",
                "Carlos V",
                "Totis"
            ],
            width=12,
            state="readonly"
        )

        self.combo_marca.current(0)

        self.combo_marca.pack(
            side="left"
        )

        self.combo_marca.bind(
            "<<ComboboxSelected>>",
            lambda e:
            self.aplicar_filtros_inventario()
        )

        tk.Label(
            barra_filtros,
            text="CATEGORÍA",
            bg="#3A8D96",
            fg=BLANCO,
            font=("Arial", 9, "bold")
        ).pack(
            side="left",
            padx=(15, 5)
        )

        self.combo_categoria = ttk.Combobox(
            barra_filtros,
            values=[
                "Todas",
                "Chocolates",
                "Gomitas",
                "Dulces",
                "Frituras"
            ],
            width=12,
            state="readonly"
        )

        self.combo_categoria.current(0)

        self.combo_categoria.pack(
            side="left"
        )

        self.combo_categoria.bind(
            "<<ComboboxSelected>>",
            lambda e:
            self.aplicar_filtros_inventario()
        )

        columnas = (
            "PRODUCTO",
            "MARCA",
            "CATEGORÍA",
            "PRECIO",
            "STOCK",
            "ESTADO"
        )

        self.tabla_inv = ttk.Treeview(
            panel_principal,
            columns=columnas,
            show="headings",
            height=8
        )

        for col in columnas:

            self.tabla_inv.heading(
                col,
                text=col
            )

            self.tabla_inv.column(
                col,
                anchor="center",
                width=110
            )

        self.tabla_inv.pack(
            fill="both",
            expand=True,
            pady=5
        )

        self.aplicar_filtros_inventario()


    # ========================================================
    # FILTROS INVENTARIO
    # ========================================================

    def aplicar_filtros_inventario(self):

        for fila in self.tabla_inv.get_children():

            self.tabla_inv.delete(
                fila
            )

        texto_busqueda = (
            self.txt_buscar_inv
            .get()
            .lower()
        )

        marca_seleccionada = (
            self.combo_marca
            .get()
        )

        categoria_seleccionada = (
            self.combo_categoria
            .get()
        )

        for producto in self.controlador.modelo.inventario:

            coincide_nombre = (
                texto_busqueda
                in producto["nombre"].lower()
            )

            coincide_marca = (
                marca_seleccionada == "Todas"
                or producto["marca"]
                == marca_seleccionada
            )

            coincide_cat = (
                categoria_seleccionada == "Todas"
                or producto["categoria"]
                == categoria_seleccionada
            )

            if (
                coincide_nombre
                and coincide_marca
                and coincide_cat
            ):

                if producto["stock"] == 0:

                    estado = "AGOTADO"

                elif producto["stock"] < 15:

                    estado = "BAJO"

                else:

                    estado = "MEDIO"

                self.tabla_inv.insert(
                    "",
                    "end",
                    values=(
                        producto["nombre"],
                        producto["marca"],
                        producto["categoria"],
                        f"${producto['precio']:.2f}",
                        producto["stock"],
                        estado
                    )
                )


    # ========================================================
    # APARTADOS
    # ========================================================

    def construir_apartados(self):

        panel_principal = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        panel_principal.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        # ----------------------------------------------------
        # BARRA SUPERIOR
        # ----------------------------------------------------

        barra_apartados = tk.Frame(
            panel_principal,
            bg="#3A8D96",
            height=40
        )

        barra_apartados.pack(
            fill="x",
            pady=(0, 10)
        )

        barra_apartados.pack_propagate(False)

        tk.Label(
            barra_apartados,
            text="APARTADOS",
            bg="#3A8D96",
            fg=BLANCO,
            font=("Arial", 9, "bold")
        ).pack(
            side="left",
            padx=12
        )

        # ----------------------------------------------------
        # TABLA DE APARTADOS
        # ----------------------------------------------------

        columnas = (
            "PRODUCTO",
            "NOMBRE",
            "FECHA DE ENTREGA",
            "PRECIO",
            "UNIDADES APARTADAS" 
        )

        self.tabla_apartados = ttk.Treeview(
            panel_principal,
            columns=columnas,
            show="headings",
            height=16
        )

        # ----------------------------------------------------
        # ENCABEZADOS
        # ----------------------------------------------------

        self.tabla_apartados.heading(
            "PRODUCTO",
            text="PRODUCTO"
        )

        self.tabla_apartados.heading(
            "NOMBRE",
            text="NOMBRE"
        )

        self.tabla_apartados.heading(
            "FECHA DE ENTREGA",
            text="FECHA DE ENTREGA"
        )

        self.tabla_apartados.heading(
            "PRECIO",
            text="PRECIO"
        )

        self.tabla_apartados.heading(
            "UNIDADES APARTADAS",
            text="UNIDADES APARTADAS"
        )

        # ----------------------------------------------------
        # TAMAÑO DE LAS COLUMNAS
        # ----------------------------------------------------

        self.tabla_apartados.column(
            "PRODUCTO",
            width=180,
            anchor="center"
        )

        self.tabla_apartados.column(
            "NOMBRE",
            width=180,
            anchor="center"
        )

        self.tabla_apartados.column(
            "FECHA DE ENTREGA",
            width=180,
            anchor="center"
        )

        self.tabla_apartados.column(
            "PRECIO",
            width=120,
            anchor="center"
        )

        self.tabla_apartados.column(
            "UNIDADES APARTADAS",
            width=220,
            anchor="center"
        )

        # ----------------------------------------------------
        # TABLA VACÍA
        # ----------------------------------------------------

        self.tabla_apartados.pack(
            fill="both",
            expand=True
        )
