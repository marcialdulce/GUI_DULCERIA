import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

class PantallaLogin(tk.Frame):
    def __init__(self, parent, controlador=None, on_login_success=None, logo_path="assets/logo_dulce.jpg"):
        super().__init__(parent, bg="#FFF0F3") # Fondo general pastel suave
        
        self.controlador = controlador
        self.on_login_success = on_login_success
        self.logo_path = logo_path

        self._construir_ui()

    def _construir_ui(self):
        # Contenedor principal tipo "Tarjeta" (Card)
        card_frame = tk.Frame(self, bg="#FFFFFF", bd=0, relief="flat")
        card_frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=500)
        card_frame.config(highlightbackground="#F3C6D1", highlightthickness=2)

        # 1. Logo superior
        try:
            img = Image.open(self.logo_path)
            ancho_deseado = 160
            ancho_original, alto_original = img.size
            alto_deseado = int((alto_original * ancho_deseado) / ancho_original)
            
            img = img.resize((ancho_deseado, alto_deseado), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            
            lbl_logo = tk.Label(card_frame, image=self.logo_img, bg="#FFFFFF", bd=0)
            lbl_logo.pack(pady=(30, 10))
        except Exception as e:
            print(f"Error cargando logo: {e}")
            lbl_logo = tk.Label(card_frame, text="🍬 Algorrico", font=("Segoe UI", 20, "bold"), fg="#D9534F", bg="#FFFFFF")
            lbl_logo.pack(pady=(35, 15))

        # 2. Título de bienvenida
        lbl_titulo = tk.Label(
            card_frame, 
            text="¡Bienvenido al Sistema!", 
            font=("Segoe UI", 14, "bold"), 
            fg="#4A2E35", 
            bg="#FFFFFF"
        )
        lbl_titulo.pack(pady=(0, 20))

        # 3. Campo de Usuario
        frame_usuario = tk.Frame(card_frame, bg="#FFFFFF")
        frame_usuario.pack(fill="x", padx=45, pady=6)
        
        lbl_user = tk.Label(frame_usuario, text="👤 Usuario", font=("Segoe UI", 9, "bold"), fg="#7A5C65", bg="#FFFFFF")
        lbl_user.pack(anchor="w", pady=(0, 3))
        
        self.entry_usuario = tk.Entry(
            frame_usuario, 
            font=("Segoe UI", 11), 
            bg="#F9F1F3", 
            fg="#333333", 
            relief="flat", 
            highlightbackground="#E2C1CB", 
            highlightcolor="#D9534F", 
            highlightthickness=1
        )
        self.entry_usuario.pack(fill="x", ipady=6)

        # 4. Campo de Contraseña
        frame_pass = tk.Frame(card_frame, bg="#FFFFFF")
        frame_pass.pack(fill="x", padx=45, pady=10)
        
        lbl_pass = tk.Label(frame_pass, text="🔒 Contraseña", font=("Segoe UI", 9, "bold"), fg="#7A5C65", bg="#FFFFFF")
        lbl_pass.pack(anchor="w", pady=(0, 3))
        
        self.entry_pass = tk.Entry(
            frame_pass, 
            font=("Segoe UI", 11), 
            bg="#F9F1F3", 
            fg="#333333", 
            show="•", 
            relief="flat", 
            highlightbackground="#E2C1CB", 
            highlightcolor="#D9534F", 
            highlightthickness=1
        )
        self.entry_pass.pack(fill="x", ipady=6)
        self.entry_pass.bind("<Return>", lambda event: self.verificar_credenciales())

        # 5. Botón Ingresar
        btn_ingresar = tk.Button(
            card_frame, 
            text="Ingresar al Sistema", 
            font=("Segoe UI", 10, "bold"), 
            bg="#D9534F", 
            fg="#FFFFFF", 
            activebackground="#C9302C", 
            activeforeground="#FFFFFF", 
            relief="flat", 
            cursor="hand2",
            command=self.verificar_credenciales
        )
        btn_ingresar.pack(fill="x", padx=45, pady=(25, 20), ipady=8)

    def verificar_credenciales(self):
        usuario = self.entry_usuario.get().strip()
        password = self.entry_pass.get().strip()
        
        # Validación de campos vacíos
        if not usuario or not password:
            messagebox.showerror("Campos vacíos", "Por favor, ingresa tu usuario y contraseña.")
            return

        # 1. Si existe callback on_login_success, le enviamos usuario y contraseña
        if self.on_login_success:
            try:
                self.on_login_success(usuario, password)
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error al iniciar sesión: {e}")
        # 2. Si se pasó el controlador directamente, llamamos a su método de validación real
        elif self.controlador and hasattr(self.controlador, 'procesar_login'):
            self.controlador.procesar_login(usuario, password)
        else:
            messagebox.showerror("Error de configuración", "No se encontró el controlador para validar la sesión.")