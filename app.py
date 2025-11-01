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
---------------------------------------------CINTIA----------------------------------------------

# ========= Inserciones unitarias =========
def _normalize_record_with_random_id_for(target: str, data: dict) -> dict:
    """
    Normaliza un registro y genera PERSONA con prefijo según el destino:
    target in {'oracle','mysql'}
    """
    rec = {k: data.get(k) for k in CAMPOS}
    if not rec.get("PERSONA") or not isinstance(rec.get("PERSONA"), str):
        rec["PERSONA"] = _id_oracle() if target == "oracle" else _id_mysql()
    # numéricos
    for k in ("SALARIO_BASE", "BONIFICACION"):
        v = rec.get(k)
        rec[k] = float(v) if (v not in (None, "")) else None
    return rec

def insert_persona_oracle(data: dict) -> str:
    rec = _normalize_record_with_random_id_for("oracle", data)
    conn = cur = None
    try:
        conn = get_oracle_conn()
        cur = conn.cursor()
        sql = f"""
        INSERT INTO PERSONAS ({', '.join(CAMPOS)})
        VALUES (:PERSONA, :DPI, :PRIMER_NOMBRE, :SEGUNDO_NOMBRE, :PRIMER_APELLIDO,
                :SEGUNDO_APELLIDO, :DIRECCION, :TELEFONO_CASA, :TELEFONO_MOVIL,
                :SALARIO_BASE, :BONIFICACION)
        """
        cur.execute(sql, rec)
        conn.commit()
        return rec["PERSONA"]  # p.ej. OR-12345
    except Exception as e:
        if conn: conn.rollback()
        raise e
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except:
            pass

def insert_persona_mysql(data: dict) -> str:
    rec = _normalize_record_with_random_id_for("mysql", data)
    conn = cur = None
    try:
        conn = get_mysql_conn()
        cur = conn.cursor()
        placeholders = ", ".join(["%s"] * len(CAMPOS))
        sql = f"""
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
        row = tuple(rec.get(k) for k in CAMPOS)
        cur.execute(sql, row)
        conn.commit()
        return rec["PERSONA"]  # p.ej. MY-67890
    except Exception as e:
        if conn: conn.rollback()
        raise e
    finally:
        try:
            if cur: cur.close()
            if conn and conn.is_connected(): conn.close()
        except:
            pass

# ========= Eliminaciones por PERSONA =========
def delete_persona_oracle(persona_id: str) -> int:
    conn = cur = None
    try:
        conn = get_oracle_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM PERSONAS WHERE PERSONA = :id", {"id": persona_id})
        affected = cur.rowcount
        conn.commit()
        return affected or 0
    except Exception as e:
        if conn: conn.rollback()
        raise e
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except:
            pass

def delete_persona_mysql(persona_id: str) -> int:
    conn = cur = None
    try:
        conn = get_mysql_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM PERSONAS WHERE PERSONA = %s", (persona_id,))
        affected = cur.rowcount
        conn.commit()
        return affected or 0
    except Exception as e:
        if conn: conn.rollback()
        raise e
    finally:
        try:
            if cur: cur.close()
            if conn and conn.is_connected(): conn.close()
        except:
            pass

# ========= Rutas Flask =========
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/test_oracle")
def test_oracle():
    result = ConectionOracle()
    return jsonify({"message": result})

@app.route("/test_mysql")
def test_mysql():
    result = ConectionMYSQL()
    return jsonify({"message": result})

@app.route("/sync_mysql_to_oracle")
def sync_mysql_to_oracle():
    try:
        rows = fetch_all_mysql_personas()
        upserted = upsert_into_oracle(rows)
        return jsonify({
            "ok": True,
            "direction": "mysql->oracle",
            "rows_read": len(rows),
            "rows_upserted": upserted
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/sync_oracle_to_mysql")
def sync_oracle_to_mysql():
    try:
        rows = fetch_all_oracle_personas()
        upserted = upsert_into_mysql(rows)
        return jsonify({
            "ok": True,
            "direction": "oracle->mysql",
            "rows_read": len(rows),
            "rows_upserted": upserted
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/sync_both")
def sync_both():
    try:
        m_rows = fetch_all_mysql_personas()
        m_up = upsert_into_oracle(m_rows)
        o_rows = fetch_all_oracle_personas()
        o_up = upsert_into_mysql(o_rows)
        return jsonify({
            "ok": True,
            "mysql_to_oracle": {"read": len(m_rows), "upserted": m_up},
            "oracle_to_mysql": {"read": len(o_rows), "upserted": o_up},
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# --- Guardar en ORACLE (con prefijo OR-)
@app.post("/oracle/personas")
def api_insert_persona_oracle():
    try:
        payload = request.get_json(force=True) or {}
        new_id = insert_persona_oracle(payload)
        return jsonify({
            "ok": True,
            "message": f"Registro insertado en Oracle con ID {new_id}",
            "persona_id": new_id
        }), 201
    except Exception as e:
        return jsonify({"ok": False, "message": f"Error: {e}"}), 400

# --- Guardar en MYSQL (con prefijo MY-)
@app.post("/mysql/personas")
def api_insert_persona_mysql():
    try:
        payload = request.get_json(force=True) or {}
        new_id = insert_persona_mysql(payload)
        return jsonify({
            "ok": True,
            "message": f"Registro insertado en MySQL con ID {new_id}",
            "persona_id": new_id
        }), 201
    except Exception as e:
        return jsonify({"ok": False, "message": f"Error: {e}"}), 400

# --- Eliminar en ORACLE por PERSONA (string)
@app.delete("/oracle/personas/<persona_id>")
def api_delete_persona_oracle(persona_id: str):
    try:
        affected = delete_persona_oracle(persona_id)
        return jsonify({
            "ok": True,
            "message": f"Eliminadas {affected} fila(s) en Oracle",
            "deleted": affected
        }), 200
    except Exception as e:
        return jsonify({"ok": False, "message": f"Error: {e}"}), 400

# --- Eliminar en MYSQL por PERSONA (string)
@app.delete("/mysql/personas/<persona_id>")
def api_delete_persona_mysql(persona_id: str):
    try:
        affected = delete_persona_mysql(persona_id)
        return jsonify({
            "ok": True,
            "message": f"Eliminadas {affected} fila(s) en MySQL",
            "deleted": affected
        }), 200
    except Exception as e:
        return jsonify({"ok": False, "message": f"Error: {e}"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
