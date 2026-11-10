import tkinter as tk
from tkinter import simpledialog, messagebox
from vistas import estilos

class PanelCierreCaja(tk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.resumen = controlador.obtener_resumen_cierre_caja()

        tk.Label(self, text="CIERRE DE CAJA", bg=estilos.FONDO, fg="#4A2E35", font=("Arial", 22, "bold")).pack(pady=(35, 8))
        tk.Label(self, text="Resumen de la sesión de trabajo del cajero", bg=estilos.FONDO, fg="#555555", font=("Arial", 11)).pack(pady=(0, 20))

        tarjeta = tk.Frame(self, bg="#FFFFFF", bd=1, relief="solid")
        tarjeta.pack(fill="x", padx=100, pady=10)
        datos = [
            ("Cajero", self.resumen["usuario"]),
            ("Hora de inicio de sesión", self.resumen["inicio"]),
            ("Hora de cierre", self.resumen["fin"]),
            ("Tiempo trabajado", self.resumen["duracion"]),
        ]
        for etiqueta, valor in datos:
            fila = tk.Frame(tarjeta, bg="#FFFFFF")
            fila.pack(fill="x", padx=25, pady=13)
            tk.Label(fila, text=etiqueta, bg="#FFFFFF", fg="#555555", font=("Arial", 11, "bold"), width=25, anchor="w").pack(side="left")
            tk.Label(fila, text=valor, bg="#FFFFFF", fg="#4A2E35", font=("Arial", 11), anchor="w").pack(side="left", fill="x", expand=True)

        tk.Label(self, text="Al confirmar, se cerrará tu sesión y regresarás a la pantalla de inicio de sesión.",
                 bg=estilos.FONDO, fg="#555555", font=("Arial", 10), wraplength=650, justify="center").pack(pady=(20, 15))
        
        tk.Button(self, text="FINALIZAR TURNO Y CERRAR SESIÓN",
                  bg="#D9534F", fg="#FFFFFF", activebackground="#C9302C", activeforeground="#FFFFFF", 
                  relief="flat", cursor="hand2", font=("Arial", 11, "bold"), padx=18, pady=12,
                  command=self.confirmar_cierre).pack(pady=8)

    def confirmar_cierre(self):
        if not messagebox.askyesno("Confirmar cierre", "¿Deseas finalizar tu turno y cerrar la caja?"):
            return
        
        efectivo_fisico = simpledialog.askfloat(
            "Arqueo de Caja Ciego", 
            "Por políticas de seguridad, ingresa el monto total de efectivo físico que contaste en la caja:"
        )
        
        if efectivo_fisico is None:
            return 
            
        diferencia = efectivo_fisico - self.resumen['efectivo_esperado']
        
        if diferencia == 0:
            messagebox.showinfo("Cierre Guardado", "El arqueo ha sido registrado. La caja cuadra a la perfección.")
        elif diferencia > 0:
            messagebox.showwarning("Cierre Registrado", "El arqueo ha sido registrado con un sobrante en caja. Esto será notificado al Administrador.")
        else:
            messagebox.showerror("Cierre Registrado", "El arqueo ha sido registrado con un faltante en caja. Esto será notificado al Administrador.")
            
        self.controlador.cerrar_sesion(efectivo_fisico)