#!/bin/bash
# correr_job.sh — Ejecuta el job de Hadoop Streaming y lo cronometra.
# Se corre DENTRO del contenedor hadoop:
#   docker compose exec hadoop bash /mapreduce/correr_job.sh
set -e

MATRICULA=${MATRICULA:-125054759}
ENTRADA=/data/input/ventas_${MATRICULA}.csv
SALIDA=/data/output/resultado

if [ ! -f "$ENTRADA" ]; then
  echo "No encuentro $ENTRADA. Pon el CSV en la carpeta data/ del proyecto." >&2
  exit 1
fi

# Hadoop falla si la carpeta de salida ya existe, asi que la borramos antes.
rm -rf "$SALIDA"

time hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.name="ingreso_hora_categoria_${MATRICULA}" \
  -D mapreduce.job.reduces=1 \
  -input "$ENTRADA" \
  -output "$SALIDA" \
  -mapper "python3 mapper.py" -reducer "python3 reducer.py" \
  -file /mapreduce/mapper.py -file /mapreduce/reducer.py

echo
echo "Primeras lineas del resultado:"
head -n 12 "$SALIDA/part-00000"
echo "Total de lineas: $(wc -l < "$SALIDA/part-00000")"
