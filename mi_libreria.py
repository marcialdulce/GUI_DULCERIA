"""
mi_libreria.py
Librería para gestión de inventario, validación de stock, cálculo de ventas
finales y pedidos. No depende de ninguna interfaz gráfica, así que puedes
usarla desde Tkinter, consola o cualquier otro programa.

El inventario es un diccionario donde la clave es el código del producto:

    inventario = {
        "P001": {"nombre": "Paleta", "precio": 5.0, "stock": 40, "stock_minimo": 10},
    }

Uso:
    from mi_libreria import *
    inventario = {}
    agregar_producto(inventario, "P001", "Paleta", 5.0, 40, stock_minimo=10)
    venta = registrar_venta(inventario, {"P001": 3}, descuento=10)
    print(venta["total"])
"""

__version__ = "2.0.0"

TASA_IVA = 0.16  # Cambia este valor si necesitas otra tasa


# ---------------------------------------------------------------- Errores
class ProductoNoEncontradoError(Exception):
    """El código de producto no existe en el inventario."""


class StockInsuficienteError(Exception):
    """No hay suficientes unidades para completar la operación."""


# ------------------------------------------------------- Gestión de inventario
def agregar_producto(inventario, codigo, nombre, precio, stock=0, stock_minimo=5):
    """Agrega un producto nuevo. Valida que los datos sean correctos."""
    if codigo in inventario:
        raise ValueError(f"El código '{codigo}' ya existe.")
    if not nombre or not nombre.strip():
        raise ValueError("El nombre no puede estar vacío.")
    if precio < 0 or stock < 0 or stock_minimo < 0:
        raise ValueError("Precio, stock y stock mínimo no pueden ser negativos.")
    inventario[codigo] = {
        "nombre": nombre.strip(),
        "precio": float(precio),
        "stock": int(stock),
        "stock_minimo": int(stock_minimo),
    }
    return inventario[codigo]


def obtener_producto(inventario, codigo):
    """Devuelve el producto o lanza ProductoNoEncontradoError."""
    if codigo not in inventario:
        raise ProductoNoEncontradoError(f"El producto '{codigo}' no existe.")
    return inventario[codigo]


def eliminar_producto(inventario, codigo):
    """Elimina un producto del inventario."""
    obtener_producto(inventario, codigo)
    del inventario[codigo]


def actualizar_precio(inventario, codigo, nuevo_precio):
    """Cambia el precio de un producto."""
    if nuevo_precio < 0:
        raise ValueError("El precio no puede ser negativo.")
    obtener_producto(inventario, codigo)["precio"] = float(nuevo_precio)


def ajustar_stock(inventario, codigo, cantidad):
    """Suma (cantidad positiva) o resta (negativa) unidades al stock."""
    producto = obtener_producto(inventario, codigo)
    if producto["stock"] + cantidad < 0:
        raise StockInsuficienteError(
            f"Stock insuficiente de '{producto['nombre']}': "
            f"hay {producto['stock']}, se intentó restar {abs(cantidad)}."
        )
    producto["stock"] += cantidad
    return producto["stock"]


# ------------------------------------------------------- Validación de stock
def hay_stock(inventario, codigo, cantidad):
    """True si hay suficientes unidades disponibles."""
    if cantidad <= 0:
        return False
    return obtener_producto(inventario, codigo)["stock"] >= cantidad


def validar_carrito(inventario, carrito):
    """
    Revisa un carrito {codigo: cantidad} y devuelve una lista de problemas.
    Lista vacía = todo correcto.
    """
    problemas = []
    for codigo, cantidad in carrito.items():
        if codigo not in inventario:
            problemas.append(f"'{codigo}' no existe.")
        elif cantidad <= 0:
            problemas.append(f"Cantidad inválida para '{codigo}'.")
        elif inventario[codigo]["stock"] < cantidad:
            p = inventario[codigo]
            problemas.append(
                f"'{p['nombre']}': pediste {cantidad}, solo hay {p['stock']}."
            )
    return problemas


def productos_bajo_stock(inventario):
    """Lista de códigos cuyo stock es menor o igual al mínimo."""
    return [c for c, p in inventario.items() if p["stock"] <= p["stock_minimo"]]


# ------------------------------------------------------------------ Cálculos
def calcular_subtotal(precio, cantidad):
    return round(precio * cantidad, 2)


def calcular_descuento(monto, porcentaje):
    """Devuelve el monto que se descuenta (porcentaje entre 0 y 100)."""
    if not 0 <= porcentaje <= 100:
        raise ValueError("El descuento debe estar entre 0 y 100.")
    return round(monto * porcentaje / 100, 2)


def calcular_iva(base, tasa=TASA_IVA):
    return round(base * tasa, 2)


def formatear_precio(valor, moneda="$"):
    """12.5 -> '$12.50'"""
    return f"{moneda}{valor:,.2f}"


# ------------------------------------------------------------------- Ventas
def calcular_venta(inventario, carrito, descuento=0, tasa_iva=TASA_IVA):
    """
    Calcula el total de una venta SIN modificar el inventario (ideal para
    mostrar el resumen antes de confirmar). Lanza error si falta stock.

    Devuelve un diccionario con: detalle, subtotal, descuento, base, iva, total.
    """
    problemas = validar_carrito(inventario, carrito)
    if problemas:
        raise StockInsuficienteError(" | ".join(problemas))

    detalle = []
    subtotal = 0.0
    for codigo, cantidad in carrito.items():
        p = inventario[codigo]
        importe = calcular_subtotal(p["precio"], cantidad)
        subtotal += importe
        detalle.append({
            "codigo": codigo,
            "nombre": p["nombre"],
            "cantidad": cantidad,
            "precio": p["precio"],
            "importe": importe,
        })

    subtotal = round(subtotal, 2)
    monto_desc = calcular_descuento(subtotal, descuento)
    base = round(subtotal - monto_desc, 2)
    iva = calcular_iva(base, tasa_iva)
    return {
        "detalle": detalle,
        "subtotal": subtotal,
        "descuento": monto_desc,
        "base": base,
        "iva": iva,
        "total": round(base + iva, 2),
    }


def registrar_venta(inventario, carrito, descuento=0, tasa_iva=TASA_IVA):
    """Calcula la venta y descuenta las unidades vendidas del inventario."""
    venta = calcular_venta(inventario, carrito, descuento, tasa_iva)
    for codigo, cantidad in carrito.items():
        ajustar_stock(inventario, codigo, -cantidad)
    return venta


def calcular_cambio(total, pago):
    """Cambio a devolver. Lanza error si el pago no alcanza."""
    if pago < total:
        raise ValueError(f"Pago insuficiente: faltan {formatear_precio(total - pago)}.")
    return round(pago - total, 2)


# ------------------------------------------------------------------ Pedidos
def sugerir_pedido(inventario, stock_objetivo=30):
    """
    Para cada producto con stock bajo, calcula cuántas unidades pedir para
    llegar al stock objetivo. Devuelve {codigo: cantidad_a_pedir}.
    """
    pedido = {}
    for codigo in productos_bajo_stock(inventario):
        faltan = stock_objetivo - inventario[codigo]["stock"]
        if faltan > 0:
            pedido[codigo] = faltan
    return pedido


def calcular_costo_pedido(pedido, costos, tasa_iva=TASA_IVA):
    """
    Calcula el costo de un pedido a proveedor.
    pedido: {codigo: cantidad}   costos: {codigo: costo_unitario}
    """
    subtotal = 0.0
    for codigo, cantidad in pedido.items():
        if codigo not in costos:
            raise ProductoNoEncontradoError(f"Falta el costo de '{codigo}'.")
        subtotal += costos[codigo] * cantidad
    subtotal = round(subtotal, 2)
    iva = calcular_iva(subtotal, tasa_iva)
    return {"subtotal": subtotal, "iva": iva, "total": round(subtotal + iva, 2)}


def recibir_pedido(inventario, pedido):
    """Suma al inventario las unidades de un pedido recibido."""
    for codigo, cantidad in pedido.items():
        ajustar_stock(inventario, codigo, cantidad)


# ------------------------------------------------------------------- Prueba
if __name__ == "__main__":
    inv = {}
    agregar_producto(inv, "P001", "Paleta", 5, 40, stock_minimo=10)
    agregar_producto(inv, "P002", "Chocolate", 12.5, 8, stock_minimo=10)

    print("Bajo stock:", productos_bajo_stock(inv))
    venta = registrar_venta(inv, {"P001": 3, "P002": 2}, descuento=10)
    print("Total venta:", formatear_precio(venta["total"]))
    print("Cambio:", formatear_precio(calcular_cambio(venta["total"], 100)))

    pedido = sugerir_pedido(inv, stock_objetivo=30)
    print("Pedido sugerido:", pedido)
    print("Costo pedido:", calcular_costo_pedido(pedido, {"P002": 8.0}))
    recibir_pedido(inv, pedido)
    print("Stock final:", {c: p["stock"] for c, p in inv.items()})
