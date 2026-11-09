# Examen Segundo Parcial — Pipeline de datos contenerizado

| | |
|---|---|
| **Alumno** | _(tu nombre)_ |
| **Matrícula** | 125054759 |
| **Último dígito** | 9 |
| **Pregunta de negocio** | **Ingreso total (`cantidad × precio_unitario`) por hora del día (0–23) y categoría** |

## Arquitectura

```
 data/ventas_125054759.csv
        │  (volumen solo lectura → /data/input)
        ▼
 ┌──────────────┐  part-00000   ┌──────────────────────┐   SQL    ┌──────────────┐
 │   hadoop     │ ────────────► │ cargar_resultados.py │ ───────► │  db          │
 │ (standalone  │  ./salida     │ (corre en api)       │          │ PostgreSQL   │
 │  + SSH)      │               └──────────────────────┘          │ vol: pgdata  │
 └──────▲───────┘                                                 └──────▲───────┘
        │ ssh hadoop@hadoop                                              │ "db:5432"
 ┌──────┴──────────────────────────────────────────────────────────────┴───────┐
 │ api (Flask)  →  http://localhost:8000/resultados                            │
 └──────────────────────────────────────────────────────────────────────────────┘
              Todos en la red "red_datamart"
```

| Servicio | Qué hace | Detalles |
|---|---|---|
| `hadoop` | Ejecuta el job MapReduce (Hadoop Streaming) y el servidor SSH | Imagen propia `debian:bookworm-slim` + OpenJDK 17 + Python 3 + Hadoop 3.3.6 standalone |
| `db` | Guarda los resultados | `postgres:16`, volumen nombrado `pgdata`, credenciales en `.env` |
| `api` | CRUD en Flask sobre la tabla `ingreso_hora_categoria` | Se conecta a `db` por nombre de servicio, `depends_on: db` (healthy) |

## Estructura

```
examen-p2-125054759/
├── README.md
├── .gitignore              # incluye *.csv y .env
├── .env.example
├── docker-compose.yml
├── generar_dataset.py      # script del examen (Paso 0)
├── hadoop/
│   ├── Dockerfile
│   └── entrypoint.sh       # autoriza la llave de api y arranca sshd
├── mapreduce/
│   ├── mapper.py
│   ├── reducer.py
│   ├── secuencial.py
│   ├── comparar.py         # verifica que ambos resultados coinciden
│   └── correr_job.sh       # ejecuta y cronometra el job
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── scripts/
│   └── cargar_resultados.py
├── data/                   # aquí va el CSV (NO se sube a Git)
├── salida/                 # aquí escribe Hadoop (NO se sube a Git)
└── evidencias/             # capturas y logs
```

---

## Pasos para reproducir

> Requisitos: Docker Desktop (o Docker Engine + Compose v2) y Python 3 en tu máquina.
> Todos los comandos se ejecutan desde la carpeta del proyecto.

**1. Generar el dataset y ponerlo en `data/`**

```bash
python3 generar_dataset.py 125054759        # en Windows: python generar_dataset.py 125054759
mv ventas_125054759.csv data/                # en Windows: move ventas_125054759.csv data\
```

**2. Crear el archivo `.env`** (y cambiar la contraseña)

```bash
cp .env.example .env                         # en Windows: copy .env.example .env
```

**3. Levantar todo con un solo comando**

```bash
docker compose up --build -d
docker compose ps                            # los 3 servicios deben estar "running"/"healthy"
```

> La primera vez tarda varios minutos porque descarga Hadoop (~700 MB).

**4. Verificar Hadoop**

```bash
docker compose exec hadoop hadoop version
```

**5. SSH sin contraseña**

```bash
# a) ssh localhost dentro del contenedor hadoop
docker compose exec -u hadoop hadoop ssh localhost "hostname && hadoop version | head -1"

# b) desde el contenedor api hacia hadoop, por nombre de servicio
docker compose exec api ssh hadoop@hadoop "hostname && hadoop version | head -1"
```

**6. Ejecutar el job MapReduce (cronometrado)**

```bash
docker compose exec hadoop bash /mapreduce/correr_job.sh
```

El resultado queda en `salida/resultado/part-00000` (240 líneas = 24 horas × 10 categorías).

**7. Ejecutar la versión secuencial (cronometrada) y comparar**

```bash
docker compose exec hadoop bash -c "time python3 /mapreduce/secuencial.py /data/input/ventas_125054759.csv /data/output/secuencial.txt"
docker compose exec hadoop python3 /mapreduce/comparar.py /data/output/resultado/part-00000 /data/output/secuencial.txt
```

**8. Cargar los resultados en PostgreSQL**

```bash
docker compose exec api python /scripts/cargar_resultados.py
```

**9. Consultar la API**

```bash
curl http://localhost:8000/resultados                 # todos
curl http://localhost:8000/resultados/18              # hora 18 (todas las categorías)
curl http://localhost:8000/resultados/Ropa            # categoría Ropa (todas las horas)
curl http://localhost:8000/resultados/18/Ropa         # un registro
```

Escritura (CRUD):

```bash
curl -X POST   http://localhost:8000/resultados -H "Content-Type: application/json" \
     -d '{"hora": 3, "categoria": "Prueba", "ingreso_total": 100.50}'
curl -X PUT    http://localhost:8000/resultados/3/Prueba -H "Content-Type: application/json" \
     -d '{"ingreso_total": 200}'
curl -X DELETE http://localhost:8000/resultados/3/Prueba
```

> En Windows PowerShell usa `curl.exe` en lugar de `curl`, o abre las URLs GET en el navegador.

**10. Persistencia**

```bash
docker compose down          # apaga y borra contenedores, pero NO el volumen pgdata
docker compose up -d
curl http://localhost:8000/resultados/18     # los datos siguen ahí
```

---

## Evidencias

_(Pega aquí tus capturas o guarda los logs en `evidencias/`)_

- [ ] `hadoop version` → `evidencias/01_hadoop_version.png`
- [ ] `ssh localhost` sin contraseña → `evidencias/02_ssh_localhost.png`
- [ ] `ssh hadoop@hadoop` desde api → `evidencias/03_ssh_api_hadoop.png`
- [ ] Salida del job + tiempo → `evidencias/04_job_mapreduce.png`
- [ ] Secuencial + tiempo + comparación OK → `evidencias/05_secuencial.png`
- [ ] Carga a la BD → `evidencias/06_carga.png`
- [ ] Respuesta de la API → `evidencias/07_api.png`
- [ ] Datos tras `down` / `up` → `evidencias/08_persistencia.png`

### Resultado de referencia

Valores que deben salir con la matrícula 125054759 (sirven para comprobar que el job es correcto):

| Dato | Valor |
|---|---|
| Líneas en `part-00000` | 240 |
| Ingreso total de todo el año | $40,715,244,793.99 |
| Combinación con mayor ingreso | hora 08, Abarrotes: $173,884,805.58 |
| Combinación con menor ingreso | hora 01, Juguetes: $164,244,020.90 |
| Hora 18, Ropa | $171,243,505.19 |

---

## C2. Comparativa de rendimiento

| Método | Tiempo (`real`) | Resultado |
|---|---|---|
| Hadoop Streaming (standalone) | _(anota tu tiempo)_ | 240 líneas |
| Script secuencial en Python | _(anota tu tiempo)_ | 240 líneas |
| ¿Coinciden? | | ✅ `comparar.py` → "COINCIDEN exactamente" |

**¿Por qué uno fue más rápido?** El script secuencial fue más rápido porque, en modo
standalone, Hadoop no reparte el trabajo entre varias máquinas: corre todo en una sola JVM
sobre un solo equipo, procesando los splits de uno en uno, y además paga costos que el
script simple no tiene. Tiene que arrancar la JVM y el *LocalJobRunner*, partir el archivo
en *splits*, lanzar un proceso Python por tarea y pasarle cada línea por tuberías
(*streaming*). Después escribe a disco y ordena (*shuffle & sort*) millones de pares
clave-valor antes de que el reducer los sume. El script secuencial, en cambio, lee el
archivo una sola vez y acumula los 240 totales en un diccionario en memoria. Con 400 MB, que
caben de sobra en un solo equipo, el costo de coordinación de MapReduce es mayor que el
beneficio. MapReduce conviene cuando los datos no caben en una máquina y hay un clúster real
que procese en paralelo.

---

## Parte E. Teoría

**1. Modos de Hadoop.**
*Standalone (local)*: todo corre en un solo proceso Java, sin demonios y sobre el sistema de
archivos local; sirve para desarrollar y depurar. *Pseudo-distribuido*: todos los demonios
(NameNode, DataNode, ResourceManager, NodeManager) corren en una sola máquina como procesos
separados que se comunican por red/SSH, simulando un clúster. *Totalmente distribuido*: los
demonios se reparten en varias máquinas reales. **HDFS se usa en el pseudo-distribuido y en el
totalmente distribuido**; el standalone usa el disco local.

**2. ¿Por qué el dataset se monta como volumen y no con `COPY`?**
(a) Tamaño: un CSV de ~400 MB inflaría la imagen y haría cada build lento y pesado.
(b) Separar código y datos: con un volumen se puede cambiar o regenerar el dataset sin
reconstruir la imagen. (c) Seguridad y privacidad: los datos no quedan dentro de la imagen
(que podría publicarse) ni en el repositorio. (d) Montarlo como `:ro` (solo lectura) evita
que el contenedor modifique los datos originales.

**3. `docker compose down` vs `docker compose down -v`.**
`docker compose down` detiene y elimina contenedores y redes, pero **conserva los volúmenes
nombrados**. Por eso los datos de PostgreSQL en `pgdata` siguen ahí al volver a hacer `up`.
`docker compose down -v` además **elimina los volúmenes nombrados**: se pierde la base de datos
y al levantar de nuevo PostgreSQL arranca vacío. Hay que volver a correr `cargar_resultados.py`.

**4. ¿Por qué MapReduce no siempre es más rápido con 400 MB?**
Tiene un costo fijo alto: arranque de JVM, planificación de tareas, división en splits,
escritura intermedia a disco y *shuffle & sort*. Con Streaming, además, cada línea pasa entre
Java y Python. Con 400 MB en una sola máquina ese costo pesa más que el procesamiento, y un
script secuencial en memoria termina antes. MapReduce conviene cuando los datos son muy
grandes (decenas de GB o más, o no caben en una máquina) y hay un **clúster** con varios nodos
para procesar en paralelo cerca de los datos (HDFS), o cuando se necesita tolerancia a fallos.

**5. `CMD` vs `ENTRYPOINT`; `COPY` vs `ADD`.**
`ENTRYPOINT` define el ejecutable fijo del contenedor. `CMD` da el comando o los argumentos por
defecto y se reemplaza fácilmente al hacer `docker run imagen otro-comando`. Si existen los
dos, `CMD` se pasa como argumentos de `ENTRYPOINT`. `COPY` solo copia archivos locales del
contexto a la imagen. `ADD` hace lo mismo y además descarga URLs y descomprime
automáticamente archivos `.tar`. Se recomienda `COPY` por ser más predecible y usar `ADD`
solo cuando se necesita esa extracción.
