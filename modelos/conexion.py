import os
import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv

load_dotenv()

_pool = None


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

    ssl_ca = os.getenv("DB_SSL_CA")
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