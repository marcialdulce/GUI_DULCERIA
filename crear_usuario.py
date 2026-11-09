import bcrypt
from modelos.conexion import conectar_bd

def crear_usuario_admin():
    print("--- CREAR NUEVO USUARIO ADMINISTRADOR ---")
    username = input("Username: ")
    password = input("Contraseña: ")
    nombre = input("Nombre: ")
    ap_paterno = input("Apellido Paterno: ")
    ap_materno = input("Apellido Materno: ")

    # Encriptar la contraseña (truncada a 72 bytes máximo por requerimiento de bcrypt)
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8')[:72], salt).decode('utf-8')

    # Conectar a la base de datos
    conexion = conectar_bd()
    if conexion:
        try:
            cursor = conexion.cursor()
            # Insertamos con id_rol = 1 para que sea Administrador
            query = """
                INSERT INTO usuarios (username, password_hash, nombre, ap_paterno, ap_materno, estado, id_rol)
                VALUES (%s, %s, %s, %s, %s, 'activo', 1)
            """
            cursor.execute(query, (username, password_hash, nombre, ap_paterno, ap_materno))
            conexion.commit()
            print(f"\n¡Éxito! El usuario '{username}' ha sido creado como Administrador.")
            print("Ya puedes iniciar sesión en el sistema.")
        except Exception as e:
            print(f"\nError al crear el usuario en la BD: {e}")
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()

if __name__ == "__main__":
    crear_usuario_admin()