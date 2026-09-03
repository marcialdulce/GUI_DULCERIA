import tkinter as tk

# COLORES
ROSA = "#F2C2CC"
ROJO = "#C93B5A"
CREMA = "#FFF9F5"
BLANCO = "#FFFFFF"
NEGRO = "#222222"

# VENTANA PRINCIPAL
ventana = tk.Tk()
ventana.title("Dulcería")
ventana.geometry("1000x650")
ventana.configure(bg=CREMA)

# ENCABEZADO
encabezado = tk.Frame(
    ventana,
    bg=ROSA,
    height=105
)
encabezado.pack(fill="x")
encabezado.pack_propagate(False)

# NOMBRE
nombre = tk.Label(
    encabezado,
    text="Dulcería",
    font=("Arial", 28),
    bg=ROSA,
    fg=NEGRO
)
nombre.place(x=125, y=30)

# MENU
menu = tk.Frame(
    ventana,
    bg=ROJO,
    height=45
)
menu.pack(fill="x")
menu.pack_propagate(False)

# AREA PRINCIPAL
contenido = tk.Frame(
    ventana,
    bg=CREMA
)
contenido.pack(
    fill="both",
    expand=True
)

# EJECUTAR
ventana.mainloop()
