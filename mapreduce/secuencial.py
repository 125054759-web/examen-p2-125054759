#!/usr/bin/env python3
"""
secuencial.py  —  Misma pregunta que el job MapReduce, pero en un solo proceso
leyendo el CSV linea por linea (sin Hadoop). Sirve para la comparativa C2.

Uso:
    python3 secuencial.py /data/input/ventas_125054759.csv /data/output/secuencial.txt

La salida tiene EXACTAMENTE el mismo formato y orden que part-00000:
    hora<TAB>categoria<TAB>ingreso_total
"""
import sys
import time
from collections import defaultdict

if len(sys.argv) != 3:
    sys.exit("Uso: python3 secuencial.py <entrada.csv> <salida.txt>")

entrada, salida = sys.argv[1], sys.argv[2]
inicio = time.perf_counter()

totales = defaultdict(int)   # clave "HH|Categoria" -> centavos
malformadas = 0

with open(entrada, encoding="utf-8") as f:
    for linea in f:
        campos = linea.rstrip("\r\n").split(",")
        if campos[0] == "id":
            continue
        if len(campos) != 8:
            malformadas += 1
            continue
        try:
            hora = int(campos[1].split(" ")[1].split(":")[0])
            categoria = campos[3].strip()
            cantidad = int(campos[5])
            centavos = round(float(campos[6]) * 100)
            if not (0 <= hora <= 23) or not categoria:
                raise ValueError
        except (ValueError, IndexError):
            malformadas += 1
            continue
        totales[f"{hora:02d}|{categoria}"] += cantidad * centavos

with open(salida, "w", encoding="utf-8") as out:
    for clave in sorted(totales):          # mismo orden que Hadoop
        hora, categoria = clave.split("|", 1)
        pesos, cent = divmod(totales[clave], 100)
        out.write(f"{hora}\t{categoria}\t{pesos}.{cent:02d}\n")

print(f"Grupos: {len(totales)} | Lineas malformadas: {malformadas} | "
      f"Tiempo: {time.perf_counter() - inicio:.2f} s")
