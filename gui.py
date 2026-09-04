import tkinter as tk
from tkinter import messagebox

# ============================================================
# USUARIOS DEL SISTEMA
# ============================================================
USUARIOS = {
    "Dulce": "1234",
    "Scarlet": "1234",
    "Daniel": "1234",
    "Yeray": "1234",
    "Josue": "1234"
}

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
class DulceriaApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Dulcería")
        self.geometry("1000x650")
        self.resizable(False, False)
        self.configure(bg=FONDO)

        # Este contenedor ocupa TODA la ventana.
        self.contenedor = tk.Frame(self, bg=FONDO)
        self.contenedor.pack(fill="both", expand=True)

        # IMPORTANTE:
        # Sin estas dos líneas, las pantallas colocadas con grid()
        # sólo ocupan el tamaño mínimo de sus componentes.
        self.contenedor.grid_rowconfigure(0, weight=1)
        self.contenedor.grid_columnconfigure(0, weight=1)

        self.pantallas = {}

        for Pantalla in (PantallaLogin, PantallaPrincipal):
            frame = Pantalla(
                parent=self.contenedor,
                controlador=self
            )

            self.pantallas[Pantalla.__name__] = frame

            frame.grid(
                row=0,
                column=0,
                sticky="nsew"
            )

        self.mostrar_pantalla("PantallaLogin")

    def mostrar_pantalla(self, nombre):
        self.pantallas[nombre].tkraise()


# ============================================================
# INICIO DE SESIÓN
# ============================================================
class PantallaLogin(tk.Frame):

    def __init__(self, parent, controlador):
        super().__init__(parent, bg=FONDO)

        self.controlador = controlador

        tk.Label(
            self,
            text="Inicio de Sesión - Dulcería",
            font=("Arial", 20, "bold"),
            bg=FONDO
        ).pack(pady=(100, 30))

        tk.Label(
            self,
            text="Usuario:",
            font=("Arial", 11),
            bg=FONDO
        ).pack(pady=5)

        self.txt_usuario = tk.Entry(
            self,
            width=30,
            font=("Arial", 11)
        )
        self.txt_usuario.pack(pady=5)

        tk.Label(
            self,
            text="Contraseña:",
            font=("Arial", 11),
            bg=FONDO
        ).pack(pady=5)

        self.txt_password = tk.Entry(
            self,
            show="*",
            width=30,
            font=("Arial", 11)
        )
        self.txt_password.pack(pady=5)

        tk.Button(
            self,
            text="Ingresar",
            command=self.validar_login,
            width=18,
            bg=ROSA_MENU,
            fg=BLANCO,
            activebackground=ROSA_MENU_ACTIVO,
            activeforeground=BLANCO,
            bd=0,
            font=("Arial", 10, "bold")
        ).pack(pady=25)

        self.txt_password.bind(
            "<Return>",
            lambda event: self.validar_login()
        )

    def validar_login(self):

        usuario = self.txt_usuario.get().strip()
        password = self.txt_password.get()

        if usuario in USUARIOS and USUARIOS[usuario] == password:

            messagebox.showinfo(
                "Inicio de sesión",
                f"¡Bienvenido/a, {usuario}!"
            )

            # Guardamos el usuario que inició sesión
            self.controlador.usuario_actual = usuario

            self.txt_usuario.delete(0, tk.END)
            self.txt_password.delete(0, tk.END)

            # Actualizamos el nombre en la pantalla principal
            self.controlador.pantallas[
                "PantallaPrincipal"
            ].actualizar_usuario(usuario)

            self.controlador.mostrar_pantalla(
                "PantallaPrincipal"
            )

        else:
            messagebox.showerror(
                "Error",
                "Usuario o contraseña incorrectos."
            )


# ============================================================
# PANTALLA PRINCIPAL
# ============================================================
class PantallaPrincipal(tk.Frame):

    def __init__(self, parent, controlador):
        super().__init__(parent, bg=FONDO)

        self.controlador = controlador

        # --------------------------------------------------------
        # ENCABEZADO
        # --------------------------------------------------------
        encabezado = tk.Frame(
            self,
            bg=ROSA_CLARO,
            height=115
        )
        encabezado.pack(
            fill="x"
        )
        encabezado.pack_propagate(False)

        # Logo provisional:
        # mientras no tengas imagen, usamos un dulce como símbolo.
        tk.Label(
            encabezado,
            text="🍬",
            font=("Segoe UI Emoji", 40),
            bg=ROSA_CLARO
        ).place(
            x=45,
            y=25
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

        # Nombre del usuario conectado
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

        # Ícono sencillo de usuario
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
            14, 2,
            38, 26,
            fill=NEGRO,
            outline=NEGRO
        )

        icono.create_arc(
            5, 28,
            48, 66,
            start=0,
            extent=180,
            fill=NEGRO,
            outline=NEGRO
        )

        # --------------------------------------------------------
        # BARRA DEL MENÚ
        # --------------------------------------------------------
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

        # --------------------------------------------------------
        # ÁREA DE CONTENIDO
        # --------------------------------------------------------
        self.contenido = tk.Frame(
            self,
            bg=FONDO
        )
        self.contenido.pack(
            fill="both",
            expand=True
        )

        # Dejamos el área vacía al iniciar,
        # como en tu diseño.

    def actualizar_usuario(self, usuario):
        self.lbl_usuario.config(text=usuario)

    def mostrar_seccion(self, opcion):

        # Restaurar botones
        for nombre, boton in self.botones_menu.items():

            if nombre == opcion:
                boton.config(bg=ROSA_MENU_ACTIVO)
            else:
                boton.config(bg=ROSA_MENU)

        # Limpiar contenido anterior
        for widget in self.contenido.winfo_children():
            widget.destroy()

        # Por ahora sólo muestra el nombre de la sección.
        # Después aquí agregaremos cada módulo real.
        textos = {
            "INICIO": "Inicio",
            "NUEVA VENTA": "Nueva venta",
            "INVENTARIO": "Inventario",
            "AGOTADOS": "Productos agotados",
            "APARTADOS": "Apartados",
            "HISTORIAL": "Historial"
        }

        tk.Label(
            self.contenido,
            text=textos[opcion],
            font=("Arial", 22, "bold"),
            bg=FONDO,
            fg="#333333"
        ).pack(
            pady=60
        )


# ============================================================
# EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    app = DulceriaApp()
    app.mainloop()

