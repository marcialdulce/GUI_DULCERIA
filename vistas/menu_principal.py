import tkinter as tk
from tkinter import messagebox
from vistas import estilos
from vistas.panel_inicio import PanelInicio
from vistas.panel_ventas import PanelVentas
from vistas.panel_cobros import PanelCobros           
from vistas.panel_tickets import PanelTickets        
from vistas.panel_inventario import PanelInventario
from vistas.panel_apartados import PanelApartados
from vistas.panel_historial import PanelHistorial
from vistas.panel_proveedores import PanelProveedores
from vistas.panel_cierre_caja import PanelCierreCaja
from vistas.header import LogoDulceriaHeader


class MenuPrincipal(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.rol_actual = None
        self.usuario_actual = ""
        self.opciones_actuales = []

        self.header = LogoDulceriaHeader(
            parent=self, 
            usuario_activo="", 
            comando_logout=self.controlador.cerrar_sesion, 
            logo_path="assets/logo_dulce.jpg", 
            user_icon_path="assets/user_icon.png"
        )
        self.header.pack(fill="x")

        self.menu = tk.Frame(self, bg=estilos.ROSA_MENU, height=42)
        self.menu.pack(fill="x")
        self.menu.pack_propagate(False)

        self.contenido = tk.Frame(self, bg=estilos.FONDO)
        self.contenido.pack(fill="both", expand=True)
        self.botones_menu = {}

    def configurar_acceso(self, usuario, rol, opciones_permitidas):
        self.usuario_actual = usuario
        self.rol_actual = rol
        self.opciones_actuales = opciones_permitidas

        if usuario:
            self.header.actualizar_usuario(f"{usuario} ({rol})")

        for widget in self.menu.winfo_children():
            widget.destroy()
        self.botones_menu.clear()

        for opcion in opciones_permitidas:
            boton = tk.Button(
                self.menu, text=opcion, bg=estilos.ROSA_MENU, fg=estilos.BLANCO, 
                activebackground=estilos.ROSA_MENU_ACTIVO, activeforeground=estilos.BLANCO, 
                bd=0, relief="flat", font=("Arial", 9, "bold"), cursor="hand2", 
                command=lambda op=opcion: self.mostrar_seccion(op)
            )
            boton.pack(side="left", fill="both", expand=True)
            self.botones_menu[opcion] = boton
        
        if opciones_permitidas:
            self.mostrar_seccion(opciones_permitidas[0])

    def mostrar_seccion(self, opcion):
        if opcion not in self.opciones_actuales:
            messagebox.showerror("Acceso restringido", "Tu cuenta no tiene permiso para abrir esta sección.")
            return

        for nombre, boton in self.botones_menu.items():
            boton.config(bg=estilos.ROSA_MENU_ACTIVO if nombre == opcion else estilos.ROSA_MENU)
        
        for widget in self.contenido.winfo_children():
            widget.destroy()

        #  DICCIONARIO DE PANELES
        paneles = {
            "INICIO": lambda: PanelInicio(self.contenido, self.controlador, self.mostrar_seccion),
            "NUEVA VENTA": lambda: PanelVentas(self.contenido, self.controlador),
            "PUNTO DE VENTA": lambda: PanelVentas(self.contenido, self.controlador, modo_punto_venta=True, ir_a_cobros=lambda: self.mostrar_seccion("COBROS Y PAGOS")),
            "COBROS Y PAGOS": lambda: PanelCobros(self.contenido, self.controlador),
            "INVENTARIO": lambda: PanelInventario(self.contenido, self.controlador),
            "APARTADOS": lambda: PanelApartados(self.contenido, self.controlador),
            "PROVEEDORES": lambda: PanelProveedores(self.contenido, self.controlador),
            "HISTORIAL": lambda: PanelHistorial(self.contenido, self.controlador),
            "HISTORIAL DE VENTAS": lambda: PanelHistorial(self.contenido, self.controlador),
            "TICKETS": lambda: PanelTickets(self.contenido, self.controlador),
            "CIERRE DE CAJA": lambda: PanelCierreCaja(self.contenido, self.controlador)
        }

        # Buscamos la opción en el diccionario y la ejecutamos
        generador_panel = paneles.get(opcion)
        if generador_panel:
            panel = generador_panel()
            panel.pack(fill="both", expand=True)