import os
import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for ruta_env in (os.path.join(BASE_DIR, ".env"), os.path.join(BASE_DIR, "modelos", ".env")):
    if os.path.isfile(ruta_env):
        load_dotenv(ruta_env, override=False)
load_dotenv(override=False)

_pool = None


def _resolver_ruta_ssl(ssl_ca):
    if not ssl_ca:
        return None
    if os.path.isfile(ssl_ca):
        return ssl_ca
    for candidato in (
        os.path.join(BASE_DIR, ssl_ca),
        os.path.join(BASE_DIR, "assets", ssl_ca),
        os.path.join(BASE_DIR, "certs", os.path.basename(ssl_ca)),
    ):
        if os.path.isfile(candidato):
            return candidato
    return ssl_ca


def _crear_pool():
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME"),
        "charset": "utf8mb4",
        "time_zone": "-06:00",
    }

    ssl_ca = _resolver_ruta_ssl(os.getenv("DB_SSL_CA"))
    if ssl_ca:
        config["ssl_ca"] = ssl_ca
        config["ssl_verify_cert"] = True

    return pooling.MySQLConnectionPool(
        pool_name="dulceria",
        pool_size=8,
        **config
    )


def conectar_bd():
    global _pool
    try:
        if _pool is None:
            _pool = _crear_pool()
            print("Pool de conexiones listo")
        conn = _pool.get_connection()
        conn.ping(reconnect=True, attempts=2, delay=1)
        cur = conn.cursor()
        cur.execute("SET time_zone = '-06:00'")
        cur.close()
        return conn
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None