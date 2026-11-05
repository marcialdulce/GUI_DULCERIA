"""Hash de contraseñas con la librería estándar (sin dependencias extra).
Formato guardado en USUARIOS.contraseña:  pbkdf2_sha256$iteraciones$sal_hex$hash_hex
"""
import hashlib
import hmac
import os

ITERACIONES = 200_000


def hashear_password(password, sal=None):
    sal = sal or os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal.hex()}${h.hex()}"


def verificar_password(password, guardado):
    try:
        algoritmo, iteraciones, sal_hex, hash_hex = guardado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                bytes.fromhex(sal_hex), int(iteraciones))
        return hmac.compare_digest(h.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False
