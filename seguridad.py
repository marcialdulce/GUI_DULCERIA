import bcrypt

def hashear_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verificar_password(password, guardado):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), guardado.encode('utf-8'))
    except Exception as e:
        print(f"Error crítico al verificar contraseña: {e}")
        return False