import os
import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv

load_dotenv()

_pool = None


def _crear_pool():
    config = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "charset": "utf8mb4",
    }
    if os.getenv("DB_PORT"):
        config["port"] = int(os.getenv("DB_PORT"))
    if os.getenv("DB_SSL_CA"):
        config["ssl_ca"] = os.getenv("DB_SSL_CA")
    return pooling.MySQLConnectionPool(pool_name="dulceria", pool_size=5, **config)


def conectar_bd():
    global _pool
    try:
        if _pool is None:
            _pool = _crear_pool()
            print("Pool de conexiones listo")
        return _pool.get_connection()
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None
