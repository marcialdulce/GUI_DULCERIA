import tkinter as tk
from vistas.estilos import estilos

class PanelInicio(tk.Frame):
    def __init__(self, parent, controlador, comando_navegar):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.comando_navegar = comando_navegar 

        contenedor = tk.Frame(self, bg=estilos.FONDO)
        contenedor.pack(fill="both", expand=True, padx=35, pady=35)

        inventario = self.controlador.modelo.inventario
        productos_disponibles = [p for p in inventario if p["stock"] > 0]
        productos_bajo_stock = sorted(inventario, key=lambda p: p["stock"])[:2]

        def crear_tarjeta(titulo):
            tarjeta_externa = tk.Frame(contenedor, bg="#D95A78", width=260, height=300)
            tarjeta_externa.pack(side="left", fill="both", expand=True, padx=15)
            tarjeta_externa.pack_propagate(False)

            tarjeta = tk.Frame(tarjeta_externa, bg=estilos.BLANCO, bd=1, relief="solid")
            tarjeta.pack(fill="both", expand=True, padx=(0, 8), pady=(0, 8))

            encabezado = tk.Frame(tarjeta, bg="#F8F8F8", height=55)
            encabezado.pack(fill="x")
            encabezado.pack_propagate(False)

            tk.Label(encabezado, text="●", fg="#F2C500", bg="#F8F8F8", font=("Arial", 12)).pack(side="left", padx=(12, 3))
            tk.Label(encabezado, text="●", fg="#E78BA6", bg="#F8F8F8", font=("Arial", 12)).pack(side="left")
            tk.Label(encabezado, text=titulo, bg="#F8F8F8", fg="#555555", font=("Arial", 10, "bold")).pack(side="left", padx=12)

            return tarjeta

        # TARJETA 1
        tarjeta_catalogo = crear_tarjeta("Estado del catálogo")
        tk.Label(tarjeta_catalogo, text=str(len(productos_disponibles)), bg=estilos.ROSA_MENU, fg=estilos.BLANCO, font=("Arial", 14, "bold"), width=3, height=1).pack(pady=(25, 8))
        tk.Label(tarjeta_catalogo, text="unidades en venta", bg=estilos.BLANCO, fg="#555555", font=("Arial", 11)).pack()
        tk.Label(tarjeta_catalogo, text="🛒", bg=estilos.BLANCO, fg="#555555", font=("Segoe UI Emoji", 38)).pack(pady=20)

        # TARJETA 2
        tarjeta_stock = crear_tarjeta("Stock más bajo")
        tk.Label(tarjeta_stock, text="ARTÍCULO                 STOCK", bg=estilos.BLANCO, fg="#555555", font=("Arial", 8, "bold")).pack(anchor="w", padx=18, pady=(20, 8))

        for producto in productos_bajo_stock:
            fila = tk.Frame(tarjeta_stock, bg=estilos.BLANCO)
            fila.pack(fill="x", padx=18, pady=2)
            tk.Label(fila, text=producto["nombre"], bg=estilos.BLANCO, fg="#555555", font=("Arial", 9), anchor="w").pack(side="left")
            tk.Label(fila, text=str(producto["stock"]), bg=estilos.BLANCO, fg="#555555", font=("Arial", 9), anchor="e").pack(side="right")

        tk.Label(tarjeta_stock, text="📦", bg=estilos.BLANCO, fg="#555555", font=("Segoe UI Emoji", 38)).pack(pady=20)

        # TARJETA 3
        tarjeta_cobro = crear_tarjeta("Cobro de artículos")
        tk.Label(tarjeta_cobro, text="¡Caja abierta y lista\npara operar!", bg=estilos.BLANCO, fg="#555555", font=("Arial", 11), justify="center").pack(pady=(25, 15))
        tk.Button(tarjeta_cobro, text="INICIAR VENTA", bg="#F4D03F", fg=estilos.NEGRO, activebackground="#E5C12E", font=("Arial", 10, "bold"), relief="flat", cursor="hand2", padx=15, pady=8, command=lambda: self.comando_navegar("NUEVA VENTA")).pack()
        tk.Label(tarjeta_cobro, text="🧾", bg=estilos.BLANCO, fg="#555555", font=("Segoe UI Emoji", 38)).pack(pady=18)