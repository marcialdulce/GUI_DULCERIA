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

        self.contenedor = tk.Frame(self, bg=FONDO)
        self.contenedor.pack(fill="both", expand=True)
        self.contenedor.grid_rowconfigure(0, weight=1)
        self.contenedor.grid_columnconfigure(0, weight=1)

        self.pantallas = {}
        for Pantalla in (PantallaLogin, PantallaPrincipal):
            frame = Pantalla(parent=self.contenedor, controlador=self.controlador) 
            self.pantallas[Pantalla.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.mostrar_pantalla("PantallaLogin")

    def mostrar_pantalla(self, nombre):
            self.pantallas[nombre].tkraise()

    def mostrar_alerta(self, titulo, mensaje, tipo="info"):
            if tipo == "info":
                  messagebox.showinfo(titulo, mensaje)
            else:
                 messagebox.showerror(titulo, mensaje)


# ============================================================
# INICIO DE SESIÓN
# ============================================================

class PantallaLogin(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg= FONDO)
        self.controlador = controlador

        tk.Label(self, text="Inicio de Sesión - Dulcería", font=("Arial", 20, "bold"), bg=FONDO).pack(pady=(100, 30))
        tk.Label(self, text="Usuario:", font=("Arial", 11), bg=FONDO).pack(pady=5)
        self.txt_usuario = tk.Entry(self, width=30, font=("Arial", 11))
        self.txt_usuario.pack(pady=5)

        tk.Label(self, text="Contraseña:", font=("Arial", 11), bg=FONDO).pack(pady=5)
        self.txt_password = tk.Entry(self, show="*", width=30, font=("Arial", 11))
        self.txt_password.pack(pady=5)

        tk.Button(
            self, text="Ingresar", command=self.enviar_datos, width=18,
            bg=ROSA_MENU, fg=BLANCO, activebackground=ROSA_MENU_ACTIVO,
            activeforeground=BLANCO, bd=0, font=("Arial", 10, "bold")
        ).pack(pady=25)

        self.txt_password.bind("<Return>", lambda event: self.enviar_datos())

    def enviar_datos(self):
        usuario = self.txt_usuario.get().strip()
        password = self.txt_password.get()
        # En lugar de validar aquí, se lo pasamos al Controlador
        self.controlador.procesar_login(usuario, password)

class PantallaPrincipal(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=FONDO)
        self.controlador = controlador

        encabezado = tk.Frame(self, bg=ROSA_CLARO, height=115)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)

        tk.Label(encabezado, text="🍬", font=("Segoe UI Emoji", 40), bg=ROSA_CLARO).place(x=45, y=25)
        tk.Label(encabezado, text="Dulcería", font=("Segoe Script", 25), bg=ROSA_CLARO, fg=NEGRO).place(x=115, y=33)

        self.lbl_usuario = tk.Label(encabezado, text="", font=("Arial", 10, "bold"), bg=ROSA_CLARO, fg=NEGRO)
        self.lbl_usuario.place(relx=0.91, y=88, anchor="center")

        icono = tk.Canvas(encabezado, width=55, height=65, bg=ROSA_CLARO, highlightthickness=0)
        icono.place(relx=0.94, y=15)
        icono.create_oval(14, 2, 38, 26, fill=NEGRO, outline=NEGRO)
        icono.create_arc(5, 28, 48, 66, start=0, extent=180, fill=NEGRO, outline=NEGRO)

        menu = tk.Frame(self, bg=ROSA_MENU, height=42)
        menu.pack(fill="x")
        menu.pack_propagate(False)

        opciones = ["INICIO", "NUEVA VENTA", "INVENTARIO", "AGOTADOS", "APARTADOS", "HISTORIAL"]
        self.botones_menu = {}

        for opcion in opciones:
            boton = tk.Button(
                menu, text=opcion, bg=ROSA_MENU, fg=BLANCO, activebackground=ROSA_MENU_ACTIVO,
                activeforeground=BLANCO, bd=0, relief="flat", font=("Arial", 9, "bold"),
                cursor="hand2", command=lambda op=opcion: self.mostrar_seccion(op)
            )
            boton.pack(side="left", fill="both", expand=True)
            self.botones_menu[opcion] = boton

        self.contenido = tk.Frame(self, bg=FONDO)
        self.contenido.pack(fill="both", expand=True)

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

        if opcion == "NUEVA VENTA":
            self.construir_nueva_venta()
        else:
            textos = {
                "INICIO": "Inicio", "INVENTARIO": "Inventario",
                "AGOTADOS": "Productos agotados", "APARTADOS": "Apartados", "HISTORIAL": "Historial"
            }
            tk.Label(
                self.contenido, text=textos.get(opcion, opcion), 
                font=("Arial", 22, "bold"), bg=FONDO, fg="#333333"
            ).pack(pady=60)

    def construir_nueva_venta(self):
        
          # --- PANEL IZQUIERDO (PRODUCTOS) ---
        panel_izq = tk.Frame(self.contenido, bg=FONDO)
        panel_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # Buscador
        barra_busqueda = tk.Frame(panel_izq, bg="#3A8D96", height=40)
        barra_busqueda.pack(fill="x")
        barra_busqueda.pack_propagate(False)
        tk.Label(barra_busqueda, text="BUSCAR PRODUCTO", bg="#3A8D96", fg=BLANCO, font=("Arial", 10, "bold")).pack(side="left", padx=10)
        tk.Entry(barra_busqueda, width=20).pack(side="right", padx=10, pady=8)

        # Lista de productos de ejemplo
        frame_lista = tk.Frame(panel_izq, bg="#EAEAEA")
        frame_lista.pack(fill="both", expand=True, pady=10)

        for i in range(4):
            item = tk.Frame(frame_lista, bg=BLANCO, pady=10, padx=10, bd=1, relief="solid")
            item.pack(fill="x", pady=2, padx=2)
            
            tk.Label(item, text="NOMBRE DEL PRODUCTO", bg=BLANCO, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", columnspan=2)
            tk.Label(item, text="$30.00", bg=BLANCO, font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=5)
            tk.Label(item, text="STOCK: 20", bg=BLANCO, font=("Arial", 9)).grid(row=1, column=1, sticky="w", padx=20)
            
            btn_agregar = tk.Button(item, text="AGREGAR", bg="#F4D03F", fg=NEGRO, font=("Arial", 9, "bold"), width=15, relief="flat")
            btn_agregar.grid(row=0, column=2, rowspan=2, sticky="e", padx=10)
            item.grid_columnconfigure(2, weight=1)

        # --- PANEL DERECHO (TICKET) ---
        panel_der = tk.Frame(self.contenido, bg="#F4F4F4", bd=1, relief="solid")
        panel_der.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=20)

        tk.Label(panel_der, text="TICKET DE VENTA", bg="#F4F4F4", font=("Arial", 10, "bold")).pack(pady=10)

        # Tabla del ticket (Treeview)
        columnas = ("PRODUCTO", "CANTIDAD", "PRECIO")
        tabla = ttk.Treeview(panel_der, columns=columnas, show="headings", height=12)
        tabla.heading("PRODUCTO", text="PRODUCTO")
        tabla.heading("CANTIDAD", text="CANTIDAD")
        tabla.heading("PRECIO", text="PRECIO")
        tabla.column("PRODUCTO", width=150)
        tabla.column("CANTIDAD", width=80, anchor="center")
        tabla.column("PRECIO", width=80, anchor="center")
        tabla.pack(fill="both", expand=True, padx=10)

        # Datos de ejemplo en el ticket
        tabla.insert("", "end", values=("GOMITAS", "2", "$30.00"))
        tabla.insert("", "end", values=("CHOCOLATE", "3", "$12.00"))

        # Total
        frame_total = tk.Frame(panel_der, bg="#F4F4F4")
        frame_total.pack(fill="x", padx=20, pady=15)
        tk.Label(frame_total, text="TOTAL", bg="#F4F4F4", font=("Arial", 12, "bold")).pack(side="left")
        tk.Label(frame_total, text="$42.00", bg="#F4F4F4", font=("Arial", 12, "bold")).pack(side="right")

        # Botones de cobro
        frame_botones = tk.Frame(panel_der, bg="#F4F4F4")
        frame_botones.pack(fill="x", padx=10, pady=10)
        tk.Button(frame_botones, text="CANCELAR", bg="#F4D03F", font=("Arial", 10, "bold"), relief="flat").pack(side="left", expand=True, fill="x", padx=5)
        tk.Button(frame_botones, text="COBRAR", bg="#F4D03F", font=("Arial", 10, "bold"), relief="flat").pack(side="right", expand=True, fill="x", padx=5)

 