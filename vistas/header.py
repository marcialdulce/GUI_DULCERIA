import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime

class LogoDulceriaHeader(tk.Frame):
    """
    Componente reutilizable de interfaz gráfica para el encabezado principal de la dulcería.
    Dibuja el logo con el nombre "Algorrico", la fecha/hora con emojis, el saludo, icono y botón de cerrar sesión.
    """
    def __init__(self, parent, usuario_activo="Usuario", comando_logout=None, logo_path="assets/logo_dulce.png", user_icon_path="assets/user_icon.png", *args, **kwargs):
        super().__init__(parent, bg="#F9C0CB", height=115, *args, **kwargs)
        self.pack_propagate(False)
        
        self.usuario_activo = usuario_activo
        self.comando_logout = comando_logout
        self.logo_path = logo_path
        self.user_icon_path = user_icon_path
        
        self._construir_ui()

    def _construir_ui(self):
        # Limpiar widgets previos si se reconstruye
        for widget in self.winfo_children():
            widget.destroy()

        # ==========================================================
        # 1. SECCIÓN IZQUIERDA: Logotipo Completo (Algorrico)
        # ==========================================================
        frame_logo = tk.Frame(self, bg="#F9C0CB")
        frame_logo.pack(side="left", padx=15, pady=5)

        try:
            img = Image.open(self.logo_path)
            alto_deseado = 95
            ancho_original, alto_original = img.size
            ancho_deseado = int((ancho_original * alto_deseado) / alto_original)
            
            img = img.resize((ancho_deseado, alto_deseado), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            
            lbl_logo_img = tk.Label(frame_logo, image=self.logo_img, bg="#F9C0CB", bd=0)
            lbl_logo_img.pack(side="left")
        except Exception:
            lbl_logo_fallback = tk.Label(frame_logo, text="🍬 Algorrico", font=("Arial", 20, "bold"), bg="#F9C0CB")
            lbl_logo_fallback.pack(side="left")

        # ==========================================================
        # 2. SECCIÓN DERECHA (Icono -> Saludo -> Cerrar Sesión -> Reloj con Emojis)
        # ==========================================================
        frame_usuario = tk.Frame(self, bg="#F9C0CB")
        frame_usuario.pack(side="right", padx=15, pady=25)

        # A) Icono de usuario (Extremo derecho)
        try:
            user_img = Image.open(self.user_icon_path)
            user_img = user_img.resize((40, 40), Image.Resampling.LANCZOS)
            self.icon_user_img = ImageTk.PhotoImage(user_img)
            lbl_user_icon = tk.Label(frame_usuario, image=self.icon_user_img, bg="#F9C0CB")
            lbl_user_icon.pack(side="right", padx=(10, 0))
        except Exception:
            lbl_user_fallback = tk.Label(frame_usuario, text="👤", font=("Arial", 22), bg="#F9C0CB")
            lbl_user_fallback.pack(side="right", padx=(10, 0))

        # B) Saludo dinámico (Al lado izquierdo del icono)
        self.lbl_saludo = tk.Label(
            frame_usuario, 
            text=f"¡Hola de nuevo, {self.usuario_activo}!", 
            font=("Arial", 10, "bold"), 
            fg="#000000", 
            bg="#F9C0CB"
        )
        self.lbl_saludo.pack(side="right", padx=(15, 0))

        # C) Botón de Cerrar Sesión (Al lado izquierdo del saludo)
        if self.comando_logout:
            btn_logout = tk.Button(
                frame_usuario, text="Cerrar Sesión", bg="#D9534F", fg="#FFFFFF", 
                font=("Arial", 8, "bold"), activebackground="#C9302C", 
                activeforeground="#FFFFFF", relief="flat", cursor="hand2", 
                command=self.comando_logout
            )
            btn_logout.pack(side="right", padx=(20, 0))

        # D) ETIQUETA DE FECHA Y HORA CON EMOJIS
        self.lbl_reloj = tk.Label(
            frame_usuario, 
            text="", 
            font=("Segoe UI", 9), 
            fg="#4A2E35", 
            bg="#F9C0CB"
        )
        self.lbl_reloj.pack(side="right", padx=(0, 15))

        # Iniciar la actualización del reloj
        self.actualizar_reloj()

    def actualizar_usuario(self, nuevo_usuario):
        """Método público seguro para cambiar el nombre del usuario dinámicamente."""
        self.usuario_activo = nuevo_usuario
        if hasattr(self, 'lbl_saludo'):
            self.lbl_saludo.config(text=f"¡Hola de nuevo, {self.usuario_activo}!")

    def actualizar_reloj(self):
        """Actualiza la fecha y la hora combinadas con emojis cada segundo."""
        ahora = datetime.now()
        # Formato limpio con emojis de calendario y reloj
        tiempo_formateado = f"📅 {ahora.strftime('%d/%m/%Y')}   ⏰ {ahora.strftime('%H:%M:%S')}"
        
        if hasattr(self, 'lbl_reloj'):
            self.lbl_reloj.config(text=tiempo_formateado)
            
        self.after(1000, self.actualizar_reloj)