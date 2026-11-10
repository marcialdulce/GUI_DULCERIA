"""
Genera ventas de prueba MASIVAS directamente en MySQL (dulceria_db).

Uso (desde la carpeta del proyecto, con la aplicación cerrada):

    python generar_ventas_demo.py              # 500 ventas
    python generar_ventas_demo.py 5000         # más ventas
    python generar_ventas_demo.py 500 --reemplazar

Por defecto AGREGA ventas a las existentes. Con --reemplazar borra primero las ventas
(y sus detalles) para volver a empezar. Las ventas demo NO descuentan stock.
Requisito: los 11 productos de CATALOGO deben existir en PRODUCTOS (los trae 02_dulceria_datos_base.sql).
"""
import argparse
import random
import time
from datetime import datetime, timedelta

from servicios.repositorio_ventas import RepositorioVentas, FORMATO_FECHA

# (nombre, precio) del catálogo por defecto de la dulcería
CATALOGO = [
    ("Gomitas", 15.0), ("Chocolate", 12.0), ("Pap's", 4.0), ("Panditas", 20.0),
    ("Kranky", 14.0), ("Bubulubu", 16.0), ("Carlos V Blanco", 13.0),
    ("Moritas", 12.0), ("Mangomitas", 15.0), ("Donitas Sal y Limón", 6.0),
    ("Donitas Picantes", 5.0),
]
METODOS = ["Efectivo", "Tarjeta (Crédito)", "Tarjeta (Débito)"]
PESOS_METODOS = [55, 25, 20]
LOTE = 5000


def generar(cantidad, reemplazar=False, semilla=None):
    repo = RepositorioVentas()
    if reemplazar:
        con = repo.conexion_bd.conectar()
        cur = con.cursor()
        cur.execute("DELETE FROM FACTURA")          # primero los hijos (llaves foráneas)
        cur.execute("DELETE FROM DETALLES_VENTAS")
        cur.execute("DELETE FROM VENTAS")
        con.commit(); con.close()

    rnd = random.Random(semilla)  
    fin = datetime.now()
    inicio = fin - timedelta(days=365)
    paso = (fin - inicio) / cantidad          

    lote = []
    t0 = time.perf_counter()
    for i in range(cantidad):
        elegidos = rnd.sample(CATALOGO, rnd.randint(1, 4))  # NOSONAR
        articulos = []
        for nombre, precio in elegidos:
            cant = rnd.randint(1, 5)  # NOSONAR
            articulos.append({"producto": nombre, "cantidad": cant,
                              "subtotal": round(precio * cant, 2)})
        lote.append({
            "folio": f"D{i:07d}" if reemplazar else f"D{int(time.time()) % 10**6:06d}{i:05d}",  # único aunque se agregue
            "fecha": (inicio + paso * i).strftime(FORMATO_FECHA),
            "metodo_pago": rnd.choices(METODOS, PESOS_METODOS)[0],  # NOSONAR
            "facturado": rnd.random() < 0.05,  # NOSONAR
            "total": round(sum(a["subtotal"] for a in articulos), 2),
            "articulos": articulos,
        })
        if len(lote) == LOTE:
            repo.registrar_lote(lote)
            lote = []
            print(f"\r{i + 1:>9,} / {cantidad:,} ventas", end="", flush=True)
    if lote:
        repo.registrar_lote(lote)

    print(f"\rListo: {cantidad:,} ventas agregadas en {time.perf_counter() - t0:.1f} s "
          f"-> tabla VENTAS de MySQL ({repo.tamano_actual():,} ventas en total)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera ventas de prueba")
    ap.add_argument("cantidad", nargs="?", type=int, default=500)
    ap.add_argument("--reemplazar", action="store_true", help="borra el archivo antes de generar")
    ap.add_argument("--semilla", type=int, default=None)
    args = ap.parse_args()
    if args.cantidad < 1:
        ap.error("la cantidad debe ser mayor a 0")
    generar(args.cantidad, args.reemplazar, args.semilla)
