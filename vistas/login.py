import tkinter as tk
from vistas.estilos import estilos

class PantallaLogin(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador

        tk.Label(self, text="Inicio de Sesión - Dulcería", font=("Arial", 20, "bold"), bg=estilos.FONDO).pack(pady=(100, 30))
        
        tk.Label(self, text="Usuario:", font=("Arial", 11), bg=estilos.FONDO).pack(pady=5)
        self.txt_usuario = tk.Entry(self, width=30, font=("Arial", 11))
        self.txt_usuario.pack(pady=5)

        tk.Label(self, text="Contraseña:", font=("Arial", 11), bg=estilos.FONDO).pack(pady=5)
        self.txt_password = tk.Entry(self, show="*", width=30, font=("Arial", 11))
        self.txt_password.pack(pady=5)

        tk.Button(self, text="Ingresar", command=self.enviar_datos, width=18, bg=estilos.ROSA_MENU, fg=estilos.BLANCO, activebackground=estilos.ROSA_MENU_ACTIVO, activeforeground=estilos.BLANCO, bd=0, font=("Arial", 10, "bold")).pack(pady=25)
        self.txt_password.bind("<Return>", lambda event: self.enviar_datos())

    def enviar_datos(self):
        usuario = self.txt_usuario.get().strip()
        password = self.txt_password.get()
        self.controlador.procesar_login(usuario, password)