import hmac

try:
    import bcrypt
except ImportError:
    bcrypt = None


def hashear_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")


def verificar_password(password, guardado):
    """bcrypt ($2y$/$2b$). Si el valor guardado NO es un hash (los usuarios de prueba de la BD
    traen 'usuario_1', 'usuario_2'...), se compara tal cual: solo para el entorno de pruebas."""
    if not guardado:
        return False
    if not guardado.startswith("$2"):
        return hmac.compare_digest(password, guardado)
    if bcrypt is None:
        print("Falta el paquete bcrypt: pip install bcrypt")
        return False
    try:
        normalizado = "$2b$" + guardado[4:] if guardado.startswith("$2y$") else guardado
        return bcrypt.checkpw(password.encode("utf-8")[:72], normalizado.encode("utf-8"))
    except ValueError:
        return False
