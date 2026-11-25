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
    }
    
    
    ssl_ca = os.getenv("DB_SSL_CA")
    if ssl_ca:
        config["ssl_ca"] = ssl_ca
        config["ssl_verify_cert"] = True
        
    return pooling.MySQLConnectionPool(
        pool_name="dulceria",
        pool_size=5,
        **config
    )
    
    
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
