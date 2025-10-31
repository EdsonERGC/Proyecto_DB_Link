import oracledb
import mysql.connector
from mysql.connector import Error as MySQLError
from flask import Flask, render_template, jsonify, request
import random  # para generar el número aleatorio

app = Flask(_name_)

# ========= Config de conexiones (ajusta si cambia tu red) =========
ORCL = {
    "host": "192.168.184.130",
    "port": 1521,
    "service": "XEPDB1",
    "user": "PROYECTO",
    "password": "proyecto",
}
MYSQL = {
    "host": "192.168.184.130",
    "port": 3306,
    "db": "Proyecto1",
    "user": "admin",
    "password": "12345",
}

# ========= Helpers de conexión =========
def get_oracle_conn():
    dsn = f"{ORCL['host']}:{ORCL['port']}/{ORCL['service']}"
    return oracledb.connect(user=ORCL["user"], password=ORCL["password"], dsn=dsn)

def get_mysql_conn():
    return mysql.connector.connect(
        host=MYSQL["host"],
        user=MYSQL["user"],
        password=MYSQL["password"],
        database=MYSQL["db"],
        port=MYSQL["port"],
        connection_timeout=5,
    )

# ========= Campos compartidos =========
CAMPOS = [
    "PERSONA",
    "DPI",
    "PRIMER_NOMBRE",
    "SEGUNDO_NOMBRE",
    "PRIMER_APELLIDO",
    "SEGUNDO_APELLIDO",
    "DIRECCION",
    "TELEFONO_CASA",
    "TELEFONO_MOVIL",
    "SALARIO_BASE",
    "BONIFICACION",
]

# ========= Utilidades =========
def _rand5() -> str:
    return f"{random.randint(10000, 99999)}"

def _id_oracle() -> str:
    return f"OR-{_rand5()}"

def _id_mysql() -> str:
    return f"MY-{_rand5()}"

# ========= Pruebas simples =========
def ConectionOracle():
    conn = cursor = None
    try:
        conn = get_oracle_conn()
        cursor = conn.cursor()
        ##cursor.execute("SELECT * FROM PERSONAS FETCH FIRST 1 ROWS ONLY")
        return "Conexión exitosa a Oracle"
    except oracledb.Error as e:
        return f"Error al conectar a Oracle: {e}"
    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except:
            pass

def ConectionMYSQL():
    conn = None
    try:
        conn = get_mysql_conn()
        if conn.is_connected():
            return "Conexión exitosa a MySQL"
        return "No se pudo establecer conexión a MySQL"
    except MySQLError as e:
        return f"Error al conectar a MySQL: {e}"
    finally:
        try:
            if conn and conn.is_connected(): conn.close()
        except:
            pass

# ========= Lectura y sincronización =========
def fetch_all_mysql_personas():
    conn = get_mysql_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(f"SELECT {', '.join(CAMPOS)} FROM PERSONAS")
        return cur.fetchall()
    finally:
        cur.close(); conn.close()

def fetch_all_oracle_personas():
    conn = get_oracle_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT {', '.join(CAMPOS)} FROM PERSONAS")
        rows = cur.fetchall()
        res = []
        for r in rows:
            res.append({CAMPOS[i]: r[i] for i in range(len(CAMPOS))})
        return res
    finally:
        cur.close(); conn.close()

def upsert_into_oracle(rows):
    if not rows:
        return 0
    conn = get_oracle_conn()
    cur = conn.cursor()
    merged = 0
    try:
        merge_sql = """
        MERGE INTO PERSONAS t
        USING (
          SELECT :PERSONA PERSONA,
                 :DPI DPI,
                 :PRIMER_NOMBRE PRIMER_NOMBRE,
                 :SEGUNDO_NOMBRE SEGUNDO_NOMBRE,
                 :PRIMER_APELLIDO PRIMER_APELLIDO,
                 :SEGUNDO_APELLIDO SEGUNDO_APELLIDO,
                 :DIRECCION DIRECCION,
                 :TELEFONO_CASA TELEFONO_CASA,
                 :TELEFONO_MOVIL TELEFONO_MOVIL,
                 :SALARIO_BASE SALARIO_BASE,
                 :BONIFICACION BONIFICACION
          FROM dual
        ) s
        ON (t.PERSONA = s.PERSONA)
        WHEN MATCHED THEN UPDATE SET
          t.DPI = s.DPI,
          t.PRIMER_NOMBRE = s.PRIMER_NOMBRE,
          t.SEGUNDO_NOMBRE = s.SEGUNDO_NOMBRE,
          t.PRIMER_APELLIDO = s.PRIMER_APELLIDO,
          t.SEGUNDO_APELLIDO = s.SEGUNDO_APELLIDO,
          t.DIRECCION = s.DIRECCION,
          t.TELEFONO_CASA = s.TELEFONO_CASA,
          t.TELEFONO_MOVIL = s.TELEFONO_MOVIL,
          t.SALARIO_BASE = s.SALARIO_BASE,
          t.BONIFICACION = s.BONIFICACION
        WHEN NOT MATCHED THEN INSERT
          (PERSONA, DPI, PRIMER_NOMBRE, SEGUNDO_NOMBRE, PRIMER_APELLIDO,
           SEGUNDO_APELLIDO, DIRECCION, TELEFONO_CASA, TELEFONO_MOVIL,
           SALARIO_BASE, BONIFICACION)
        VALUES
          (s.PERSONA, s.DPI, s.PRIMER_NOMBRE, s.SEGUNDO_NOMBRE, s.PRIMER_APELLIDO,
           s.SEGUNDO_APELLIDO, s.DIRECCION, s.TELEFONO_CASA, s.TELEFONO_MOVIL,
           s.SALARIO_BASE, s.BONIFICACION)
        """
        for row in rows:
            vals = {k: row.get(k) for k in CAMPOS}
            cur.execute(merge_sql, vals)
            merged += 1
        conn.commit()
        return merged
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close(); conn.close()

def upsert_into_mysql(rows):
    if not rows:
        return 0
    conn = get_mysql_conn()
    cur = conn.cursor()
    try:
        placeholders = ", ".join(["%s"] * len(CAMPOS))
        insert_sql = f"""
        INSERT INTO PERSONAS ({', '.join(CAMPOS)})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE
          DPI=VALUES(DPI),
          PRIMER_NOMBRE=VALUES(PRIMER_NOMBRE),
          SEGUNDO_NOMBRE=VALUES(SEGUNDO_NOMBRE),
          PRIMER_APELLIDO=VALUES(PRIMER_APELLIDO),
          SEGUNDO_APELLIDO=VALUES(SEGUNDO_APELLIDO),
          DIRECCION=VALUES(DIRECCION),
          TELEFONO_CASA=VALUES(TELEFONO_CASA),
          TELEFONO_MOVIL=VALUES(TELEFONO_MOVIL),
          SALARIO_BASE=VALUES(SALARIO_BASE),
          BONIFICACION=VALUES(BONIFICACION)
        """
        data = [tuple(r.get(k) for k in CAMPOS) for r in rows]
        cur.executemany(insert_sql, data)
        conn.commit()
        return cur.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close(); conn.close()
