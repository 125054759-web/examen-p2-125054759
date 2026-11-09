"""
API (CRUD) de resultados — Pregunta 9: ingreso total por hora del dia y categoria.

Endpoints
  GET    /                              -> info y lista de endpoints
  GET    /resultados                    -> todos los registros
  GET    /resultados/<clave>            -> filtro: si <clave> es numero = HORA (0-23),
                                           si es texto = CATEGORIA (ej. Ropa)
  GET    /resultados/<hora>/<categoria> -> un registro exacto
  POST   /resultados                    -> crear   {"hora":5,"categoria":"Ropa","ingreso_total":123.45}
  PUT    /resultados/<hora>/<categoria> -> actualizar {"ingreso_total": 999.99}
  DELETE /resultados/<hora>/<categoria> -> borrar
"""
import os
import time

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "db"),       # nombre del SERVICIO en el compose
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.environ["POSTGRES_DB"],
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
}

TABLA = "ingreso_hora_categoria"
DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLA} (
    id            SERIAL PRIMARY KEY,
    hora          SMALLINT      NOT NULL CHECK (hora BETWEEN 0 AND 23),
    categoria     VARCHAR(50)   NOT NULL,
    ingreso_total NUMERIC(16,2) NOT NULL,
    UNIQUE (hora, categoria)
);
"""

app = Flask(__name__)
app.json.sort_keys = False


def conectar(reintentos=15):
    """Conecta a PostgreSQL; reintenta por si la base aun esta arrancando."""
    for intento in range(1, reintentos + 1):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except psycopg2.OperationalError:
            if intento == reintentos:
                raise
            time.sleep(2)


def consultar(sql, params=(), uno=False, escribir=False):
    conn = conectar()
    try:
        with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            if cur.description is None:
                return cur.rowcount
            return cur.fetchone() if uno else cur.fetchall()
    finally:
        conn.close()


def a_json(fila):
    return {
        "id": fila["id"],
        "hora": fila["hora"],
        "categoria": fila["categoria"],
        "ingreso_total": float(fila["ingreso_total"]),
    }


def error(mensaje, codigo):
    return jsonify({"error": mensaje}), codigo


# Crear la tabla al arrancar (una sola vez gracias a gunicorn --preload)
consultar(DDL)


@app.get("/")
def inicio():
    return jsonify({
        "servicio": "API DataMart - Ingreso total por hora del dia y categoria",
        "endpoints": [
            "GET /resultados",
            "GET /resultados/<hora o categoria>",
            "GET /resultados/<hora>/<categoria>",
            "POST /resultados",
            "PUT /resultados/<hora>/<categoria>",
            "DELETE /resultados/<hora>/<categoria>",
        ],
    })


@app.get("/resultados")
def listar():
    filas = consultar(f"SELECT * FROM {TABLA} ORDER BY hora, categoria")
    return jsonify([a_json(f) for f in filas])


@app.get("/resultados/<clave>")
def filtrar(clave):
    if clave.isdigit():                     # /resultados/18  -> por hora
        filas = consultar(f"SELECT * FROM {TABLA} WHERE hora = %s ORDER BY categoria",
                          (int(clave),))
    else:                                   # /resultados/Ropa -> por categoria
        filas = consultar(f"SELECT * FROM {TABLA} WHERE LOWER(categoria) = LOWER(%s) ORDER BY hora",
                          (clave,))
    if not filas:
        return error(f"No hay resultados para '{clave}'", 404)
    return jsonify([a_json(f) for f in filas])


@app.get("/resultados/<int:hora>/<categoria>")
def obtener(hora, categoria):
    fila = consultar(f"SELECT * FROM {TABLA} WHERE hora = %s AND LOWER(categoria) = LOWER(%s)",
                     (hora, categoria), uno=True)
    return jsonify(a_json(fila)) if fila else error("No encontrado", 404)


@app.post("/resultados")
def crear():
    datos = request.get_json(silent=True) or {}
    try:
        hora = int(datos["hora"])
        categoria = str(datos["categoria"]).strip()
        ingreso = float(datos["ingreso_total"])
        if not (0 <= hora <= 23) or not categoria:
            raise ValueError
    except (KeyError, TypeError, ValueError):
        return error("Envia JSON con hora (0-23), categoria e ingreso_total", 400)
    try:
        fila = consultar(
            f"INSERT INTO {TABLA} (hora, categoria, ingreso_total) VALUES (%s, %s, %s) RETURNING *",
            (hora, categoria, ingreso), uno=True)
    except psycopg2.errors.UniqueViolation:
        return error("Ya existe un registro para esa hora y categoria (usa PUT)", 409)
    return jsonify(a_json(fila)), 201


@app.put("/resultados/<int:hora>/<categoria>")
def actualizar(hora, categoria):
    datos = request.get_json(silent=True) or {}
    try:
        ingreso = float(datos["ingreso_total"])
    except (KeyError, TypeError, ValueError):
        return error("Envia JSON con ingreso_total", 400)
    fila = consultar(
        f"UPDATE {TABLA} SET ingreso_total = %s "
        f"WHERE hora = %s AND LOWER(categoria) = LOWER(%s) RETURNING *",
        (ingreso, hora, categoria), uno=True)
    return jsonify(a_json(fila)) if fila else error("No encontrado", 404)


@app.delete("/resultados/<int:hora>/<categoria>")
def borrar(hora, categoria):
    fila = consultar(
        f"DELETE FROM {TABLA} WHERE hora = %s AND LOWER(categoria) = LOWER(%s) RETURNING *",
        (hora, categoria), uno=True)
    return jsonify({"borrado": a_json(fila)}) if fila else error("No encontrado", 404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
