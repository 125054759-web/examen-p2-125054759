#!/usr/bin/env python3
"""
reducer.py  —  Pregunta 9: Ingreso total por HORA DEL DIA (0-23) y CATEGORIA.

Hadoop entrega las lineas del mapper YA ORDENADAS por clave, asi que todas
las ventas de "18|Ropa" llegan juntas. Vamos sumando mientras la clave sea
la misma y, cuando cambia, imprimimos el total de la clave anterior.

Entrada:  18|Ropa<TAB>44970
Salida:   18<TAB>Ropa<TAB>123456.78     (hora, categoria, ingreso total en pesos)
"""
import sys


def emitir(clave, total_centavos):
    hora, categoria = clave.split("|", 1)
    pesos, cent = divmod(total_centavos, 100)
    print(f"{hora}\t{categoria}\t{pesos}.{cent:02d}")


clave_actual = None
total = 0

for linea in sys.stdin:
    try:
        clave, valor = linea.rstrip("\r\n").split("\t", 1)
        valor = int(valor)
    except ValueError:
        continue  # linea rara: se ignora

    if clave != clave_actual:
        if clave_actual is not None:
            emitir(clave_actual, total)
        clave_actual = clave
        total = 0

    total += valor

# No olvidar la ultima clave
if clave_actual is not None:
    emitir(clave_actual, total)
