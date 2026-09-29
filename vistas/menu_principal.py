import tkinter as tk
from vistas import estilos
from vistas.panel_inicio import PanelInicio
from vistas.panel_ventas import PanelVentas
from vistas.panel_inventario import PanelInventario
from vistas.panel_apartados import PanelApartados
from vistas.panel_historial import PanelHistorial
from vistas.login import PantallaLogin
from vistas.header import LogoDulceriaHeader


class MenuPrincipal(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        # ====================================================
        # ENCABEZADO SUPERIOR UNIFICADO
        # ====================================================
        self.header = LogoDulceriaHeader(
            parent=self,
            usuario_activo="Usuario",
            comando_logout=self.controlador.cerrar_sesion,
            logo_path="assets/logo_dulce.jpg",
            user_icon_path="assets/user_icon.png"
        )
        self.header.pack(fill="x")

        # ====================================================
        # MENU DE NAVEGACION (BOTONES SUPERIORES)
        # ====================================================
        menu = tk.Frame(self, bg=estilos.ROSA_MENU, height=42)
        menu.pack(fill="x")
        menu.pack_propagate(False)

        opciones = ["INICIO", "NUEVA VENTA", "INVENTARIO", "APARTADOS", "HISTORIAL"]
        self.botones_menu = {}

        for opcion in opciones:
            boton = tk.Button(
                menu, text=opcion, bg=estilos.ROSA_MENU, fg=estilos.BLANCO, 
                activebackground=estilos.ROSA_MENU_ACTIVO, activeforeground=estilos.BLANCO, 
                bd=0, relief="flat", font=("Arial", 9, "bold"), cursor="hand2", 
                command=lambda op=opcion: self.mostrar_seccion(op)
            )
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
        """Actualiza el nombre del usuario en el header reutilizable"""
        self.header.actualizar_usuario(usuario)

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

        elif opcion == "HISTORIAL":
            panel = PanelHistorial(self.contenido, self.controlador)
            panel.pack(fill="both", expand=True)
   
        else:
            tk.Label(
                self.contenido, text=f"Pantalla de {opcion}\n(Pendiente...)", 
                font=("Arial", 22, "bold"), bg=estilos.FONDO, fg="#333333"
            ).pack(pady=150)