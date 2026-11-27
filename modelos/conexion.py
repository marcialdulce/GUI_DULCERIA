import os
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


def _cargar_entorno() -> None:
    candidatos = [
        BASE_DIR / "config_movil.env",
        Path.cwd() / "config_movil.env",
        BASE_DIR / ".env",
        Path.cwd() / ".env",
    ]
    for ruta in candidatos:
        try:
            if ruta.is_file():
                load_dotenv(dotenv_path=os.fspath(ruta), override=False)
                break
        except OSError:
            continue


def _resolver_ssl_ca() -> str | None:
    ca_env = (os.getenv("DB_SSL_CA") or "").strip()
    candidatos_ca = []
    if ca_env:
        p_env = Path(ca_env)
        candidatos_ca.append(p_env if p_env.is_absolute() else BASE_DIR / p_env)
        candidatos_ca.append(Path.cwd() / p_env)
    candidatos_ca.extend([
        BASE_DIR / "certs" / "isrgrootx1.pem",
        Path.cwd() / "certs" / "isrgrootx1.pem",
    ])
    for ca_path in candidatos_ca:
        try:
            if ca_path.is_file():
                return os.fspath(ca_path)
        except OSError:
            continue
    return None


_cargar_entorno()


def conectar_bd():
    host = (os.getenv("DB_HOST") or "").strip()
    port_raw = (os.getenv("DB_PORT") or "4000").strip()
    user = (os.getenv("DB_USER") or "").strip()
    password = os.getenv("DB_PASSWORD") or ""
    database = (os.getenv("DB_NAME") or "").strip()

    try:
        port = int(port_raw)
    except ValueError:
        port = 4000

    config = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
        "connection_timeout": 10,
    }

    ssl_ca = _resolver_ssl_ca()
    if ssl_ca:
        config["ssl_ca"] = ssl_ca
        config["ssl_verify_cert"] = True

    return mysql.connector.connect(**config)


def obtener_conexion():
    return conectar_bd()