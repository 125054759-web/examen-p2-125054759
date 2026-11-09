#!/usr/bin/env python3
"""
cargar_resultados.py — Lee la salida del job (part-00000) y la inserta en PostgreSQL.

Se ejecuta dentro del contenedor api (ahi estan psycopg2 y las variables del .env):
    docker compose exec api python /scripts/cargar_resultados.py

Opcional: otra ruta de entrada
    docker compose exec api python /scripts/cargar_resultados.py /data/output/resultado/part-00000

Si un registro (hora, categoria) ya existe, se ACTUALIZA (upsert), asi que se puede
correr varias veces sin duplicar datos.
"""
import glob
import os
import sys
import time

import psycopg2
from psycopg2.extras import execute_values

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/data/output/resultado"
TABLA = "ingreso_hora_categoria"

# Si nos dan una carpeta, leemos todos los part-*; si es un archivo, solo ese
archivos = sorted(glob.glob(os.path.join(RUTA, "part-*"))) if os.path.isdir(RUTA) else [RUTA]
if not archivos or not all(os.path.isfile(a) for a in archivos):
    sys.exit(f"No encuentro la salida del job en {RUTA}. ¿Ya corriste correr_job.sh?")

registros, saltadas = [], 0
for archivo in archivos:
    with open(archivo, encoding="utf-8") as f:
        for linea in f:
            partes = linea.rstrip("\r\n").split("\t")
            if len(partes) != 3:
                saltadas += 1
                continue
            hora, categoria, ingreso = partes
            registros.append((int(hora), categoria, ingreso))

# Conexion por NOMBRE DE SERVICIO ("db") usando las variables del .env
for intento in range(10):
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "db"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
        )
        break
    except psycopg2.OperationalError:
        print("Esperando a la base de datos...")
        time.sleep(2)
else:
    sys.exit("No se pudo conectar a la base de datos.")

with conn, conn.cursor() as cur:
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLA} (
            id            SERIAL PRIMARY KEY,
            hora          SMALLINT      NOT NULL CHECK (hora BETWEEN 0 AND 23),
            categoria     VARCHAR(50)   NOT NULL,
            ingreso_total NUMERIC(16,2) NOT NULL,
            UNIQUE (hora, categoria)
        )""")
    execute_values(cur, f"""
        INSERT INTO {TABLA} (hora, categoria, ingreso_total) VALUES %s
        ON CONFLICT (hora, categoria) DO UPDATE SET ingreso_total = EXCLUDED.ingreso_total
        """, registros)
    cur.execute(f"SELECT COUNT(*) FROM {TABLA}")
    total = cur.fetchone()[0]
conn.close()

print(f"Cargados {len(registros)} registros desde {', '.join(archivos)} "
      f"(lineas saltadas: {saltadas}). Filas en la tabla: {total}")
