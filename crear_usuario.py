"""Alta de usuarios con contraseña protegida.
Uso:  python crear_usuario.py <username> <Administrador|Cajero> "<Nombre>" "<Ap. paterno>" [ap_materno]
"""
import getpass
import sys
from modelos.conexion import conectar_bd
from seguridad import hashear_password

if len(sys.argv) < 5:
    sys.exit(__doc__)
username, rol, nombre, ap_pat = sys.argv[1:5]
ap_mat = sys.argv[5] if len(sys.argv) > 5 else None
pwd = getpass.getpass("Contraseña: ")
if len(pwd) < 6:
    sys.exit("La contraseña debe tener al menos 6 caracteres.")

con = conectar_bd()
cur = con.cursor()
cur.execute("""INSERT INTO usuarios (username, password_hash, nombre, ap_paterno, ap_materno, id_rol)
               VALUES (%s,%s,%s,%s,%s,(SELECT id_rol FROM roles WHERE nombre_rol=%s))""",
            (username, hashear_password(pwd), nombre, ap_pat, ap_mat, rol))
con.commit()
con.close()
print("Usuario creado.")