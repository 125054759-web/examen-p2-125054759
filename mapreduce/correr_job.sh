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

# Trabajamos desde una carpeta temporal (NO desde "/"): si se lanza desde la raiz,
# Hadoop Streaming falla con "would create file outside of /".
TRABAJO=$(mktemp -d /tmp/job_XXXX)
cd "$TRABAJO"

# Java 17: abre paquetes internos que algunas clases de Hadoop usan por reflexion.
export HADOOP_OPTS="$HADOOP_OPTS --add-opens java.base/java.lang=ALL-UNNAMED \
 --add-opens java.base/java.util=ALL-UNNAMED --add-opens java.base/java.io=ALL-UNNAMED \
 --add-opens java.base/java.net=ALL-UNNAMED --add-opens java.base/java.nio=ALL-UNNAMED \
 --add-opens java.base/sun.nio.ch=ALL-UNNAMED"

# En modo STANDALONE todo corre en esta misma maquina, asi que el mapper y el
# reducer se llaman con su ruta completa. (En un cluster real se enviarian a los
# nodos con la opcion -files.)
time hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.name="ingreso_hora_categoria_${MATRICULA}" \
  -D mapreduce.job.reduces=1 \
  -input "$ENTRADA" \
  -output "$SALIDA" \
  -mapper "python3 /mapreduce/mapper.py" \
  -reducer "python3 /mapreduce/reducer.py"

cd / && rm -rf "$TRABAJO"

echo
echo "Primeras lineas del resultado:"
head -n 12 "$SALIDA/part-00000"
echo "Total de lineas: $(wc -l < "$SALIDA/part-00000")"
