#!/usr/bin/env python3
"""
comparar.py  —  Verifica que la salida de Hadoop y la del script secuencial coinciden.

Uso:
    python3 comparar.py /data/output/resultado/part-00000 /data/output/secuencial.txt
"""
import sys

if len(sys.argv) != 3:
    sys.exit("Uso: python3 comparar.py <part-00000> <secuencial.txt>")


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return [l.rstrip("\r\n") for l in f if l.strip()]


a, b = leer(sys.argv[1]), leer(sys.argv[2])
print(f"Lineas Hadoop: {len(a)} | Lineas secuencial: {len(b)}")

diferencias = sorted(set(a) ^ set(b))
if not diferencias and len(a) == len(b):
    print("OK: los resultados COINCIDEN exactamente.")
else:
    print(f"DIFERENTES: {len(diferencias)} lineas no coinciden. Primeras:")
    for d in diferencias[:10]:
        print("  ", d)
    sys.exit(1)
