import tkinter as tk
from vistas.estilos import estilos
from vistas.panel_inicio import PanelInicio
from vistas.panel_ventas import PanelVentas
from vistas.panel_inventario import PanelInventario
from vistas.panel_apartados import PanelApartados
from vistas.panel_agotados import PanelAgotados
from vistas.login import PantallaLogin


class MenuPrincipal(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        # ====================================================
        # ENCABEZADO SUPERIOR
        # ====================================================
        encabezado = tk.Frame(self, bg=estilos.ROSA_CLARO, height=115)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)

        tk.Label(encabezado, text="🍬", font=("Segoe UI Emoji", 40), bg=estilos.ROSA_CLARO).place(x=45, y=25)
        
        btn_logout = tk.Button(encabezado, text="Cerrar Sesión", bg="#D9534F", fg=estilos.BLANCO, font=("Arial", 8, "bold"), activebackground="#C9302C", activeforeground=estilos.BLANCO, relief="flat", cursor="hand2", command=self.controlador.cerrar_sesion)
        btn_logout.place(relx=0.82, y=88, anchor="center")
        
        tk.Label(encabezado, text="Dulcería", font=("Segoe Script", 25), bg=estilos.ROSA_CLARO, fg=estilos.NEGRO).place(x=115, y=33)

        self.lbl_usuario = tk.Label(encabezado, text="", font=("Arial", 10, "bold"), bg=estilos.ROSA_CLARO, fg=estilos.NEGRO)
        self.lbl_usuario.place(relx=0.91, y=88, anchor="center")

        icono = tk.Canvas(encabezado, width=55, height=65, bg=estilos.ROSA_CLARO, highlightthickness=0)
        icono.place(relx=0.94, y=15)
        icono.create_oval(14, 2, 38, 26, fill=estilos.NEGRO, outline=estilos.NEGRO)
        icono.create_arc(5, 28, 48, 66, start=0, extent=180, fill=estilos.NEGRO, outline=estilos.NEGRO)

        # ====================================================
        # MENU DE NAVEGACION (BOTONES LATERALES/SUPERIORES)
        # ====================================================
        menu = tk.Frame(self, bg=estilos.ROSA_MENU, height=42)
        menu.pack(fill="x")
        menu.pack_propagate(False)

        opciones = ["INICIO", "NUEVA VENTA", "INVENTARIO", "AGOTADOS", "APARTADOS", "HISTORIAL"]
        self.botones_menu = {}

        for opcion in opciones:
            boton = tk.Button(menu, text=opcion, bg=estilos.ROSA_MENU, fg=estilos.BLANCO, activebackground=estilos.ROSA_MENU_ACTIVO, activeforeground=estilos.BLANCO, bd=0, relief="flat", font=("Arial", 9, "bold"), cursor="hand2", command=lambda op=opcion: self.mostrar_seccion(op))
            boton.pack(side="left", fill="both", expand=True)
            self.botones_menu[opcion] = boton

        # ====================================================
        # CONTENEDOR CENTRAL (Donde se inyectan los paneles)
        # ====================================================
        self.contenido = tk.Frame(self, bg=estilos.FONDO)
        self.contenido.pack(fill="both", expand=True)

        # Iniciar por defecto en la primera pantalla
        self.mostrar_seccion("INICIO")


    def actualizar_usuario(self, usuario):
        self.lbl_usuario.config(text=usuario)

    def mostrar_seccion(self, opcion):
        # 1. Colorear el boton activo
        for nombre, boton in self.botones_menu.items():
            if nombre == opcion:
                boton.config(bg=estilos.ROSA_MENU_ACTIVO)
            else:
                boton.config(bg=estilos.ROSA_MENU)

        # 2. Limpiar el contenido de la pantalla anterior
        for widget in self.contenido.winfo_children():
            widget.destroy()

        # 3. Mostrar panel 
        if opcion == "INICIO":
            panel = PanelInicio(self.contenido, self.controlador, self.mostrar_seccion)
            panel.pack(fill="both", expand=True)
            
        elif opcion == "NUEVA VENTA":
            panel = PanelVentas(self.contenido, self.controlador)
            panel.pack(fill="both", expand=True)

        elif opcion == "INVENTARIO":
            panel = PanelInventario(self.contenido, self.controlador)
            panel.pack(fill="both", expand=True)

        elif opcion == "APARTADOS":
            panel = PanelApartados(self.contenido, self.controlador)
            panel.pack(fill="both", expand=True)

        elif opcion == "AGOTADOS":
            panel = PanelAgotados(self.contenido, self.controlador)
            panel.pack(fill="both", expand=True)
            
        else:
            tk.Label(self.contenido, text=f"Pantalla de {opcion}\n(Pendiente de modularizar)", font=("Arial", 22, "bold"), bg=estilos.FONDO, fg="#333333").pack(pady=150)