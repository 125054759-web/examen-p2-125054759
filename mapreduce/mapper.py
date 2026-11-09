#!/usr/bin/env python3
"""
mapper.py  —  Pregunta 9: Ingreso total por HORA DEL DIA (0-23) y CATEGORIA.

Entrada (una linea del CSV):
    id,fecha_hora,tienda,categoria,producto,cantidad,precio_unitario,metodo_pago
    1,2025-03-14 18:22:05,T007,Ropa,ROP-0012,3,149.90,Tarjeta

Salida (clave TAB valor):
    18|Ropa<TAB>44970
    - clave = hora con 2 digitos + "|" + categoria  (asi Hadoop ordena 00,01,...,23)
    - valor = ingreso de esa venta en CENTAVOS (cantidad x precio x 100), como entero.
      Usamos enteros para que la suma sea exacta y coincida con el script secuencial.
"""
import sys


def contar(nombre):
    # Hadoop Streaming lee esta linea de stderr y la muestra como contador del job.
    sys.stderr.write(f"reporter:counter:Calidad,{nombre},1\n")


for linea in sys.stdin:
    campos = linea.rstrip("\r\n").split(",")

    # 1) Ignorar el encabezado
    if campos[0] == "id":
        continue

    # 2) Linea mal formada: numero de columnas incorrecto -> se salta, el job sigue
    if len(campos) != 8:
        contar("LineasMalformadas")
        continue

    try:
        fecha_hora = campos[1]                       # "2025-03-14 18:22:05"
        hora = int(fecha_hora.split(" ")[1].split(":")[0])
        categoria = campos[3].strip()
        cantidad = int(campos[5])
        centavos = round(float(campos[6]) * 100)     # 149.90 -> 14990

        if not (0 <= hora <= 23) or not categoria:
            raise ValueError("hora o categoria invalida")
    except (ValueError, IndexError):
        # 3) Datos que no se pueden convertir -> se salta, el job sigue
        contar("LineasMalformadas")
        continue

    ingreso_centavos = cantidad * centavos
    print(f"{hora:02d}|{categoria}\t{ingreso_centavos}")
