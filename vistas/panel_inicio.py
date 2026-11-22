import tkinter as tk
from vistas import estilos

FUENTE_EMOJI = ("Segoe UI EMOJI", 38)


class PanelInicio(tk.Frame):
    def __init__(self, parent, controlador, comando_navegar):
        super().__init__(parent, bg=estilos.FONDO)
        self.controlador = controlador
        self.comando_navegar = comando_navegar

        contenedor = tk.Frame(self, bg=estilos.FONDO)
        contenedor.pack(fill="both", expand=True, padx=30, pady=30)

        inventario = self.controlador.modelo.inventario
        productos_disponibles = [p for p in inventario if p["stock"] > 0]
        productos_bajo_stock = sorted(inventario, key=lambda p: p["stock"])[:5]

        def crear_tarjeta(titulo):
            tarjeta_externa = tk.Frame(contenedor, bg="#D95A78")
            tarjeta_externa.pack(side="left", fill="both", expand=True, padx=10)

            tarjeta = tk.Frame(tarjeta_externa, bg=estilos.BLANCO, bd=1, relief="solid")
            tarjeta.pack(fill="both", expand=True, padx=4, pady=4)

            encabezado = tk.Frame(tarjeta, bg="#F8F8F8", height=45)
            encabezado.pack(fill="x")
            encabezado.pack_propagate(False)

            tk.Label(encabezado, text="●", fg="#F2C500", bg="#F8F8F8", font=("Arial", 12)).pack(side="left", padx=(10, 2))
            tk.Label(encabezado, text="●", fg="#E78BA6", bg="#F8F8F8", font=("Arial", 12)).pack(side="left")
            tk.Label(encabezado, text=titulo, bg="#F8F8F8", fg="#555555", font=("Arial", 9, "bold")).pack(side="left", padx=10)

            return tarjeta

 
        tarjeta_catalogo = crear_tarjeta("Estado del catálogo")
        tk.Label(
            tarjeta_catalogo,
            text=str(len(productos_disponibles)),
            bg=estilos.ROSA_MENU,
            fg=estilos.BLANCO,
            font=("Arial", 14, "bold"),
            padx=12,
            pady=4,
        ).pack(pady=(25, 8))
        tk.Label(tarjeta_catalogo, text="productos activos", bg=estilos.BLANCO, fg="#555555", font=("Arial", 11)).pack()
        tk.Label(tarjeta_catalogo, text="🛒", bg=estilos.BLANCO, fg="#555555", font=FUENTE_EMOJI).pack(pady=20)

        tarjeta_stock = crear_tarjeta("Stock más bajo (Top 5)")
        tabla_top = tk.Frame(tarjeta_stock, bg=estilos.BLANCO)
        tabla_top.pack(fill="x", padx=16, pady=(18, 10))
        tabla_top.grid_columnconfigure(0, weight=1)
        tabla_top.grid_columnconfigure(1, weight=0)

        tk.Label(tabla_top, text="ARTÍCULO", bg=estilos.BLANCO, fg="#555555", font=("Arial", 8, "bold"), anchor="w").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        tk.Label(tabla_top, text="STOCK", bg=estilos.BLANCO, fg="#555555", font=("Arial", 8, "bold"), anchor="e").grid(
            row=0, column=1, sticky="e", padx=(12, 0), pady=(0, 6)
        )

        for idx, producto in enumerate(productos_bajo_stock, start=1):
            stock_val = int(producto["stock"])
            minimo = int(producto.get("stock_minimo") or 5)
            color_num = "#C0392B" if stock_val <= minimo else "#555555"

            tk.Label(
                tabla_top,
                text=producto["nombre"],
                bg=estilos.BLANCO,
                fg="#444444",
                font=("Arial", 9),
                anchor="w",
                justify="left",
                wraplength=200,
            ).grid(row=idx, column=0, sticky="w", pady=3)

            tk.Label(
                tabla_top,
                text=str(stock_val),
                bg=estilos.BLANCO,
                fg=color_num,
                font=("Arial", 9, "bold"),
                anchor="e",
            ).grid(row=idx, column=1, sticky="ne", padx=(12, 0), pady=3)

        tk.Label(tarjeta_stock, text="📦", bg=estilos.BLANCO, fg="#555555", font=FUENTE_EMOJI).pack(pady=10)

        tarjeta_cobro = crear_tarjeta("Cobro de artículos")
        tk.Label(tarjeta_cobro, text="¡Caja abierta y lista\npara operar!", bg=estilos.BLANCO, fg="#555555", font=("Arial", 11), justify="center").pack(pady=(25, 15))
        tk.Button(
            tarjeta_cobro,
            text="INICIAR VENTA",
            bg="#F4D03F",
            fg=estilos.NEGRO,
            activebackground="#E5C12E",
            font=("Arial", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8,
            command=lambda: self.comando_navegar("NUEVA VENTA"),
        ).pack()
        tk.Label(tarjeta_cobro, text="🧾", bg=estilos.BLANCO, fg="#555555", font=FUENTE_EMOJI).pack(pady=18)