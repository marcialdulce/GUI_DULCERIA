import mysql.connector
from mysql.connector import Error

class ConexionBD:
    def conectar(self):
        try:
            conexion = mysql.connector.connect(
                host="localhost",
                user="root",        
                password="1234",        
                database="dulceria_db" 
            )
            return conexion
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
            return None