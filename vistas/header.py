import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime


class LogoDulceriaHeader(tk.Frame):
    """Encabezado principal adaptable de Dulcería Algorrico."""

    def __init__(
        self,
        parent,
        usuario_activo="Usuario",
        comando_logout=None,
        logo_path="assets/logo_dulce.jpg",
        user_icon_path="assets/user_icon.png",
        *args,
        **kwargs,
    ):
        super().__init__(parent, bg="#F9C0CB", height=96, *args, **kwargs)
        self.pack_propagate(False)

        self.usuario_activo = usuario_activo
        self.comando_logout = comando_logout
        self.logo_path = logo_path
        self.user_icon_path = user_icon_path
        self._after_reloj = None

        self._construir_ui()

    def _construir_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        frame_logo = tk.Frame(self, bg="#F9C0CB")
        frame_logo.pack(side="left", padx=15, pady=8)

        try:
            img = Image.open(self.logo_path)
            alto_deseado = 68
            ancho_original, alto_original = img.size
            ancho_deseado = int((ancho_original * alto_deseado) / alto_original)

            img = img.resize((ancho_deseado, alto_deseado), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)

            tk.Label(frame_logo, image=self.logo_img, bg="#F9C0CB", bd=0).pack(side="left")
        except Exception:
            tk.Label(frame_logo, text="🍬 Algorrico", font=("Arial", 20, "bold"), bg="#F9C0CB", fg="#8E244D").pack(side="left")

        frame_usuario = tk.Frame(self, bg="#F9C0CB")
        frame_usuario.pack(side="right", padx=15, pady=12)

        # A) Icono de usuario (extremo derecho)
        try:
            user_img = Image.open(self.user_icon_path)
            user_img = user_img.resize((36, 36), Image.Resampling.LANCZOS)
            self.icon_user_img = ImageTk.PhotoImage(user_img)
            tk.Label(frame_usuario, image=self.icon_user_img, bg="#F9C0CB").pack(side="right", padx=(10, 0))
        except Exception:
            tk.Label(frame_usuario, text="👤", font=("Segoe UI Emoji", 20), bg="#F9C0CB").pack(side="right", padx=(10, 0))

        # B) Bloque vertical: Saludo arriba, Fecha y Hora completa abajo
        frame_info = tk.Frame(frame_usuario, bg="#F9C0CB")
        frame_info.pack(side="right", padx=(12, 4))

        self.lbl_saludo = tk.Label(
            frame_info,
            text=f"¡Hola de nuevo, {self.usuario_activo}!",
            font=("Arial", 10, "bold"),
            fg="#000000",
            bg="#F9C0CB",
            anchor="e",
        )
        self.lbl_saludo.pack(anchor="e")

        self.lbl_reloj = tk.Label(
            frame_info,
            text="",
            font=("Segoe UI", 9),
            fg="#4A2E35",
            bg="#F9C0CB",
            anchor="e",
        )
        self.lbl_reloj.pack(anchor="e", pady=(2, 0))

        # C) Botón de Cerrar Sesión
        if self.comando_logout:
            tk.Button(
                frame_usuario,
                text="Cerrar Sesión",
                bg="#D9534F",
                fg="#FFFFFF",
                font=("Arial", 8, "bold"),
                activebackground="#C9302C",
                activeforeground="#FFFFFF",
                relief="flat",
                cursor="hand2",
                padx=8,
                pady=4,
                command=self.comando_logout,
            ).pack(side="right", padx=(0, 12))

        self.actualizar_reloj()

    def actualizar_usuario(self, nuevo_usuario):
        self.usuario_activo = nuevo_usuario
        if hasattr(self, "lbl_saludo"):
            self.lbl_saludo.config(text=f"¡Hola de nuevo, {self.usuario_activo}!")

    def actualizar_reloj(self):
        ahora = datetime.now()
        tiempo_formateado = f"📅 {ahora.strftime('%d/%m/%Y')}   ⏰ {ahora.strftime('%H:%M:%S')}"
        if hasattr(self, "lbl_reloj") and self.lbl_reloj.winfo_exists():
            self.lbl_reloj.config(text=tiempo_formateado)
            self._after_reloj = self.after(1000, self.actualizar_reloj)