import oracledb
import mysql.connector
from mysql.connector import Error
from flask import Flask, render_template, jsonify

app = Flask(_name_)

def ConectionOracle():
    host = "192.168.184.130"
    port = 1521
    service_name = "XEPDB1"
    user = "PROYECTO"
    password = "proyecto"

    try:
        conn = oracledb.connect(
            user=user,
            password=password,
            dsn=f"{host}:{port}/{service_name}"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM PERSONAS FETCH FIRST 1 ROWS ONLY")
        result = cursor.fetchone()
        return f"Conexión exitosa a Oracle. Primer registro: {result}"

    except oracledb.Error as e:
        return f"Error al conectar a Oracle: {e}"

    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


#comentario


