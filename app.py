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





def ConectionMYSQL():
    try:
        connection = mysql.connector.connect(
            host="192.168.184.130",
            user="admin",
            password="12345",
            database="Proyecto1",
            port=3306
        )

        if connection.is_connected():
            return "Conexión exitosa a MySQL"

    except Error as e:
        return f"Error al conectar a MySQL: {e}"

    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/test_oracle')
def test_oracle():
    result = ConectionOracle()
    return jsonify({"message": result})


@app.route('/test_mysql')
def test_mysql():
    result = ConectionMYSQL()
    return jsonify({"message": result})


if _name_ == '_main_':
    app.run(host='0.0.0.0', port=5000, debug=True)
