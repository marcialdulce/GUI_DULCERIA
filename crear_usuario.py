import bcrypt
from modelos.conexion import conectar_bd

def crear_usuarios():
    print("--- CREACIÓN DE USUARIOS SEGUROS ---")
    print("1. Administrador (Acceso total al sistema)")
    print("2. Cajero (Solo panel de ventas y cobros)")
    
    seleccion = input("\nElige el rol del usuario a crear (escribe 1 o 2): ")
    
    if seleccion == "1":
        id_rol = 1
        rol_texto = "Administrador"
    elif seleccion == "2":
        id_rol = 2
        rol_texto = "Cajero"
    else:
        print("Opción no válida. Cancelando...")
        return

    print(f"\n-- Ingresando datos para: {rol_texto} --")
    username = input("Username: ")
    password = input("Contraseña: ")
    nombre = input("Nombre: ")
    ap_paterno = input("Apellido Paterno: ")
    ap_materno = input("Apellido Materno: ")

    # Encriptación bcrypt truncada a 72 bytes por seguridad
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8')[:72], salt).decode('utf-8')

    conexion = conectar_bd()
    if conexion:
        try:
            cursor = conexion.cursor()
            # Se inserta en la nueva tabla usando el id_rol dinámico
            query = """
                INSERT INTO usuarios (username, password_hash, nombre, ap_paterno, ap_materno, estado, id_rol)
                VALUES (%s, %s, %s, %s, %s, 'activo', %s)
            """
            cursor.execute(query, (username, password_hash, nombre, ap_paterno, ap_materno, id_rol))
            conexion.commit()
            print(f"\n¡Éxito! El usuario '{username}' ha sido registrado en la base de datos como {rol_texto}.")
        except Exception as e:
            print(f"\nError al guardar en MySQL: {e}")
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()

if __name__ == "__main__":
    crear_usuarios()