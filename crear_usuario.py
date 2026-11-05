"""Alta de usuarios con contraseña protegida.
Uso:  python crear_usuario.py <username> <Administrador|Cajero> "<Nombre>" "<Ap. paterno>" [ap_materno]
Pide la contraseña por teclado (no queda en el historial).
"""
import getpass
import sys
from modelos.conexion import ConexionBD
from seguridad import hashear_password

if len(sys.argv) < 5:
    sys.exit(__doc__)
username, rol, nombre, ap_pat = sys.argv[1:5]
ap_mat = sys.argv[5] if len(sys.argv) > 5 else None
pwd = getpass.getpass("Contraseña: ")
if len(pwd) < 6:
    sys.exit("La contraseña debe tener al menos 6 caracteres.")

con = ConexionBD().conectar()
cur = con.cursor()
cur.execute("""INSERT INTO USUARIOS (username, nombre, ap_paterno, ap_materno, `contraseña`, id_rol)
               VALUES (%s,%s,%s,%s,%s,(SELECT id_rol FROM ROLES WHERE nombre_rol=%s))""",
            (username, nombre, ap_pat, ap_mat, hashear_password(pwd), rol))
con.commit()
print("Usuario creado.")
