import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

class ConexionBD:
    def conectar(self):
        try:
            conexion = mysql.connector.connect(
                host=os.getenv("DB_HOST"),       
                user=os.getenv("DB_USER"),            
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"), 
                charset="utf8mb4"
            )
            if conexion.is_connected():
                print("Conexión exitosa a dulceria_db")
                return conexion
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
            return None