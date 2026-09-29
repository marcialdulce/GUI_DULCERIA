import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class LogoDulceriaHeader(tk.Frame):
    """
    Componente reutilizable de interfaz gráfica para el encabezado principal de la dulcería.
    Dibuja el logo del dulce, la tipografía del título, el saludo dinámico, el icono de perfil y el botón de cerrar sesión.
    """
    def __init__(self, parent, usuario_activo="Usuario", comando_logout=None, logo_path="assets/logo_dulce.png", user_icon_path="assets/user_icon.png", *args, **kwargs):
        super().__init__(parent, bg="#F9C0CB", height=115, *args, **kwargs) # Ajustado a 115 para que coincida con tu diseño
        self.pack_propagate(False) # Mantener la altura fija
        
        self.usuario_activo = usuario_activo
        self.comando_logout = comando_logout
        self.logo_path = logo_path
        self.user_icon_path = user_icon_path
        
        self._construir_ui()

    def _construir_ui(self):
        # Limpiar widgets previos si se reconstruye
        for widget in self.winfo_children():
            widget.destroy()

        # 1. Sección Izquierda: Logo + Nombre "Dulcería"
        frame_logo = tk.Frame(self, bg="#F9C0CB")
        frame_logo.pack(side="left", padx=15, pady=25)

        # Cargar imagen del logo del dulce si existe
        try:
            img = Image.open(self.logo_path)
            img = img.resize((50, 50), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            lbl_logo_img = tk.Label(frame_logo, image=self.logo_img, bg="#F9C0CB")
            lbl_logo_img.pack(side="left", padx=(0, 10))
        except Exception:
            lbl_logo_fallback = tk.Label(frame_logo, text="🍬", font=("Segoe UI Emoji", 35), bg="#F9C0CB")
            lbl_logo_fallback.pack(side="left", padx=(0, 10))

        # Texto del Nombre del Negocio
        lbl_titulo = tk.Label(
            frame_logo, 
            text="Dulcería", 
            font=("Segoe Script", 25), 
            fg="#000000", 
            bg="#F9C0CB"
        )
        lbl_titulo.pack(side="left")

        # 2. Sección Derecha: Botón Logout + Saludo + Icono de Perfil
        frame_usuario = tk.Frame(self, bg="#F9C0CB")
        frame_usuario.pack(side="right", padx=15, pady=25)

        # Botón de Cerrar Sesión
        if self.comando_logout:
            btn_logout = tk.Button(
                frame_usuario, text="Cerrar Sesión", bg="#D9534F", fg="#FFFFFF", 
                font=("Arial", 8, "bold"), activebackground="#C9302C", 
                activeforeground="#FFFFFF", relief="flat", cursor="hand2", 
                command=self.comando_logout
            )
            btn_logout.pack(side="left", padx=(0, 15))

        # Saludo dinámico
        self.lbl_saludo = tk.Label(
            frame_usuario, 
            text=f"¡Hola de nuevo, {self.usuario_activo}!", 
            font=("Arial", 10, "bold"), 
            fg="#000000", 
            bg="#F9C0CB"
        )
        self.lbl_saludo.pack(side="left", padx=(0, 15))

        # Cargar icono de usuario (o fallback)
        try:
            user_img = Image.open(self.user_icon_path)
            user_img = user_img.resize((40, 40), Image.Resampling.LANCZOS)
            self.icon_user_img = ImageTk.PhotoImage(user_img)
            lbl_user_icon = tk.Label(frame_usuario, image=self.icon_user_img, bg="#F9C0CB")
            lbl_user_icon.pack(side="left")
        except Exception:
            lbl_user_fallback = tk.Label(frame_usuario, text="👤", font=("Arial", 22), bg="#F9C0CB")
            lbl_user_fallback.pack(side="left")

    def actualizar_usuario(self, nuevo_usuario):
        """Método público para cambiar el nombre del usuario dinámicamente."""
        self.usuario_activo = nuevo_usuario
        self._construir_ui()
