# Base de datos de Plantamigo — guía de uso

Guía para usar la base de datos desde el backend (Flask) y el frontend.
Todo lo de esta carpeta funciona con **PostgreSQL 13 o superior**.

## Índice

1. [Qué hay en esta carpeta](#1-qué-hay-en-esta-carpeta)
2. [Puesta en marcha (una sola vez)](#2-puesta-en-marcha-una-sola-vez)
3. [Variables de entorno](#3-variables-de-entorno)
4. [Las tablas](#4-las-tablas)
5. [Funciones disponibles en Python](#5-funciones-disponibles-en-python)
6. [Media de las 7 últimas lecturas y limpieza](#6-media-de-las-7-últimas-lecturas-y-limpieza)
7. [Devolver datos al frontend (JSON)](#7-devolver-datos-al-frontend-json)
8. [Errores que pueden saltar](#8-errores-que-pueden-saltar)
9. [Tests](#9-tests)
10. [Problemas frecuentes](#10-problemas-frecuentes)

---

## 1. Qué hay en esta carpeta

| Fichero | Para qué sirve |
|---|---|
| `crear_bd.py` | Script que lo crea todo: usuario, base de datos y tablas. **Es lo único que hay que ejecutar.** |
| `schema.sql` | Definición de las tablas. Se puede ejecutar varias veces sin perder datos. |
| `datos_iniciales.sql` | Catálogo inicial de canciones (forma parte del proyecto real). |
| `datos_prueba.sql` | Usuarios, plantas y lecturas inventadas para probar. **No usar en producción.** |
| `__init__.py` | Funciones de Python para leer y escribir en la base de datos (sección 5). |
| `consultas.py` | Resumen diario para el calendario (`/api/dia/<fecha>`). |

## 2. Puesta en marcha (una sola vez)

Requisito: tener PostgreSQL instalado y conocer la contraseña del usuario `postgres`
(la que pusisteis al instalarlo; cada uno la suya, no hay que compartirla).

Desde la **raíz del repositorio**:

```bash
pip install -r requirements.txt
python web/basedatos/crear_bd.py --prueba
```

El script pide la contraseña de `postgres` (no se ve al escribirla, es normal) y crea:

- el usuario **`plantamigo`** con contraseña **`plantamigo123`**,
- la base de datos **`plantamigodb`**,
- las 5 tablas, las canciones iniciales y, con `--prueba`, datos de ejemplo.

| Opción | Efecto |
|---|---|
| *(sin opciones)* | Solo estructura y canciones, sin datos de ejemplo. |
| `--prueba` | Añade 2 usuarios (`ana`, `mikel`), 2 plantas (id 1 y 2) y 24 lecturas por planta. |
| `--reiniciar` | **Borra** la base de datos y la crea de nuevo (pide escribir `si`). |
| `--contrasena X` | Usa `X` como contraseña de `plantamigo` en vez de `plantamigo123`. |

Volver a ejecutarlo no rompe nada: lo que ya existe se salta y los datos de prueba no se duplican.

> ⚠️ Si estás dentro de `web/basedatos`, la ruta cambia: `python crear_bd.py --prueba`.

## 3. Variables de entorno

La app **no** lee ningún fichero `.env`: las variables hay que definirlas en la
misma terminal donde se arranca `app.py` o `app_local.py`.

| Variable | Obligatoria | Ejemplo | Para qué |
|---|---|---|---|
| `DATABASE_URL` | Sí | `postgresql://plantamigo:plantamigo123@localhost:5432/plantamigodb` | Conexión a la base de datos. |
| `ID_PLANTA` | Para guardar lecturas | `1` | Planta a la que `app.py` asigna las lecturas. **Debe existir** en la tabla `plantas`. |

Cómo definirlas según la terminal:

```bat
:: Windows (cmd)
set DATABASE_URL=postgresql://plantamigo:plantamigo123@localhost:5432/plantamigodb
set ID_PLANTA=1
python web/app_local.py
```

```powershell
# Windows (PowerShell)
$env:DATABASE_URL="postgresql://plantamigo:plantamigo123@localhost:5432/plantamigodb"
$env:ID_PLANTA="1"
python web/app_local.py
```

```bash
# Raspberry Pi / Linux / macOS
export DATABASE_URL=postgresql://plantamigo:plantamigo123@localhost:5432/plantamigodb
export ID_PLANTA=1
python web/app.py
```

Si la base de datos está en otro equipo (por ejemplo, la Raspberry Pi conectándose
al portátil), cambia `localhost` por la IP de ese equipo.

> 🔒 No subáis contraseñas reales al repositorio. `plantamigo123` es solo para pruebas locales.

## 4. Las tablas

```
usuarios 1──N plantas 1──N datos_planta
usuarios N──M canciones   (a través de usuarios_canciones)
```

**`usuarios`**

| Columna | Tipo | Notas |
|---|---|---|
| `id_usuario` | entero | Clave primaria, automática. |
| `nombre_usuario` | texto (50) | Único. |
| `email` | texto (254) | Único sin distinguir mayúsculas (`Ana@x.com` = `ana@x.com`). |
| `contrasena_hash` | texto | **Nunca** la contraseña en claro; la función `crear_usuario` la hashea. |
| `puntos` | entero | Empieza en 0, nunca negativo. |
| `fecha_registro` | fecha y hora | Automática. |

**`plantas`**

| Columna | Tipo | Notas |
|---|---|---|
| `id_planta` | entero | Clave primaria, automática. Es el valor de `ID_PLANTA`. |
| `id_usuario` | entero | Dueño de la planta. |
| `tipo_planta` | texto (100) | Por ejemplo, "Girasol". |
| `nombre_planta` | texto (100) | El nombre que le pone el usuario. |
| `descripcion_planta` | texto | Opcional. |
| `fecha_alta` | fecha y hora | Automática. |

**`datos_planta`** (lecturas de los sensores)

| Columna | Tipo | Unidad | Notas |
|---|---|---|---|
| `id_planta` | entero | | Planta a la que pertenece la lectura. |
| `fecha` | fecha y hora con zona | | Automática (hora del servidor de BD). |
| `temperatura` | decimal (1 decimal) | °C | DHT11. |
| `humedad` | decimal (1 decimal) | % | Media de los 2 sensores de suelo. Entre 0 y 100. |
| `luz` | real | % | Grove Light Sensor. ≥ 0. |
| `calidad_aire` | real | ppm aprox. | MQ135. ≥ 0. |

Todas las columnas de sensores **admiten NULL**: si un sensor falla o no está
conectado, se guarda la lectura con ese campo vacío. No hay dos lecturas de la
misma planta en el mismo instante.

**`canciones`**: `id_cancion`, `nombre_cancion` (único), `precio_puntos`.

**`usuarios_canciones`**: qué canciones tiene desbloqueadas cada usuario
(`id_usuario`, `id_cancion`, `fecha_obtencion`).

Al borrar un usuario se borran también sus plantas, sus lecturas y sus canciones desbloqueadas.

## 5. Funciones disponibles en Python

Se importan así desde `app.py` (que se ejecuta con la carpeta `web` en el path):

```python
from basedatos import guardar_lectura, ultimas_lecturas, media_y_limpieza
```

Cada función abre su propia conexión, hace su trabajo y la cierra; no hay que
gestionar conexiones a mano. Las filas se devuelven como **diccionarios**
(`fila["humedad"]`).

### Usuarios

| Función | Devuelve | Notas |
|---|---|---|
| `crear_usuario(nombre_usuario, email, contrasena)` | `id_usuario` | La contraseña se hashea sola. |
| `comprobar_credenciales(nombre_usuario, contrasena)` | dict del usuario o `None` | `None` si no existe o la contraseña es incorrecta. El dict **no** incluye el hash. |
| `sumar_puntos(id_usuario, puntos)` | nuevo total o `None` | Con `puntos` negativo resta. `None` si el usuario no existe. |

### Plantas

| Función | Devuelve |
|---|---|
| `crear_planta(id_usuario, tipo_planta, nombre_planta, descripcion_planta=None)` | `id_planta` |
| `plantas_de_usuario(id_usuario)` | lista de dicts |

### Lecturas de sensores

| Función | Devuelve | Notas |
|---|---|---|
| `guardar_lectura(id_planta, temperatura=None, humedad=None, luz=None, calidad_aire=None)` | nada | Pasad solo los sensores que tengáis; el resto queda NULL. |
| `ultimas_lecturas(id_planta, limite=100)` | lista de dicts | De la más reciente a la más antigua. |
| `media_y_limpieza(id_planta, n=7)` | dict o `None` | Ver sección 6. |

### Canciones

| Función | Devuelve | Notas |
|---|---|---|
| `canciones_de_usuario(id_usuario)` | lista de dicts | Las desbloqueadas. |
| `comprar_cancion(id_usuario, id_cancion)` | nada | Descuenta los puntos y la desbloquea **a la vez**: si no hay puntos, no cambia nada. Comprar una que ya tiene no cobra. |

### Ejemplo: crear el primer usuario y su planta

Si creasteis la base de datos **sin** `--prueba`, no hay ninguna planta y
`ID_PLANTA` no apuntará a nada. Ejecutad esto una vez desde la carpeta `web`
(con `DATABASE_URL` definida):

```bash
python -c "from basedatos import crear_usuario, crear_planta; u = crear_usuario('borja', 'borja@example.com', '1234'); print('ID_PLANTA =', crear_planta(u, 'Girasol', 'Sunny'))"
```

## 6. Media de las 7 últimas lecturas y limpieza

```python
resumen = media_y_limpieza(id_planta)        # n=7 por defecto
```

Qué hace, en una sola transacción:

1. Coge las **7 lecturas más recientes** de la planta.
2. Calcula la **media de cada sensor**, ignorando los valores vacíos (NULL).
3. **Borra** todas las lecturas de esa planta **anteriores** a esas 7.

Devuelve `None` si la planta no tiene lecturas, o un dict como este:

```python
{
    "lecturas": 7,           # cuántas lecturas entraron en la media (puede ser < 7)
    "desde": datetime(...),  # fecha de la más antigua de las 7
    "hasta": datetime(...),  # fecha de la más reciente
    "temperatura": None,     # None = ese sensor no tenía datos
    "humedad": 70.0,         # ya viene como float, listo para JSON
    "luz": None,
    "calidad_aire": None,
    "borradas": 3,           # lecturas antiguas eliminadas
}
```

Las lecturas que lleguen mientras se ejecuta **no se pierden**: solo se borra lo
anterior a la más antigua de las 7.

### Cómo llamarla desde `app.py`

Por ejemplo, en el hilo de humedad, justo después de guardar una lectura:

```python
from basedatos import guardar_lectura, media_y_limpieza

guardar_lectura(int(ID_PLANTA), humedad=ultima_humedad["humedad"])
resumen = media_y_limpieza(int(ID_PLANTA))
```

O exponerla en una ruta para el frontend:

```python
@app.route("/api/media")
def api_media():
    resumen = media_y_limpieza(int(ID_PLANTA))
    if resumen is None:
        return jsonify(hay_datos=False)
    return jsonify(hay_datos=True, **{k: resumen[k] for k in
                   ("lecturas", "temperatura", "humedad", "luz", "calidad_aire")})
```

> ⚠️ **Importante: afecta al calendario.** El calendario (`/api/dia/<fecha>`)
> calcula sus resúmenes a partir de `datos_planta`. Si `media_y_limpieza` se
> ejecuta a menudo, solo quedan las 7 últimas lecturas (unos 35 minutos con el
> guardado cada 5 min), así que **los días anteriores aparecerán vacíos**.
> Tenedlo en cuenta al decidir cada cuánto llamarla.

## 7. Devolver datos al frontend (JSON)

Flask convierte algunos tipos de PostgreSQL de forma poco práctica:

| Tipo en Python | Columnas | Cómo lo envía `jsonify` | Solución |
|---|---|---|---|
| `Decimal` | `temperatura`, `humedad` de `ultimas_lecturas()` | Como **texto**: `"21.4"` | `float(valor)` antes de enviarlo. |
| `datetime` | `fecha`, `fecha_registro`, `desde`, `hasta`... | `"Sat, 14 Nov 2026 10:00:00 GMT"` | `valor.isoformat()` → `"2026-11-14T10:00:00+00:00"`. |
| `None` | cualquier sensor sin dato | `null` | Comprobarlo en el JavaScript antes de mostrarlo. |

Ejemplo para enviar el histórico al gráfico:

```python
def a_json(fila):
    return {
        "fecha": fila["fecha"].isoformat(),
        **{k: None if fila[k] is None else float(fila[k])
           for k in ("temperatura", "humedad", "luz", "calidad_aire")},
    }

@app.route("/api/historico")
def api_historico():
    return jsonify([a_json(f) for f in ultimas_lecturas(int(ID_PLANTA), limite=50)])
```

`media_y_limpieza` ya devuelve las medias como `float`; solo `desde` y `hasta`
necesitan `.isoformat()` si se envían.

## 8. Errores que pueden saltar

| Excepción | Cuándo | Qué hacer |
|---|---|---|
| `RuntimeError("Falta la variable de entorno DATABASE_URL")` | No se definió `DATABASE_URL`. | Ver sección 3. |
| `psycopg.OperationalError` | PostgreSQL apagado, contraseña mala, IP incorrecta. | Responder 503 y seguir funcionando sin BD. |
| `psycopg.errors.UniqueViolation` | Nombre de usuario o email repetido. | Responder 409 "ya existe". |
| `psycopg.errors.CheckViolation` | Valor fuera de rango (humedad > 100, puntos < 0...). | Revisar el dato del sensor. |
| `psycopg.errors.ForeignKeyViolation` | `ID_PLANTA` o `id_usuario` que no existe. | Crear la planta primero (sección 5). |
| `basedatos.PuntosInsuficientes` | `comprar_cancion` sin puntos suficientes. | Responder 400 con un mensaje para el usuario. |
| `ValueError` | `comprar_cancion` con una canción que no existe. | Responder 404. |

En los hilos que leen sensores, envolved las llamadas en `try/except` (como ya
hace `lector_humedad_en_segundo_plano`) para que un fallo de la BD no pare las lecturas.

## 9. Tests

Necesitan una base de datos **vacía y desechable**: los tests **borran sus datos**.
No uséis `plantamigodb`.

```sql
-- En DBeaver o psql, como postgres:
CREATE DATABASE plantamigo_tests OWNER plantamigo;
```

```bash
pip install pytest
# PowerShell: $env:TEST_DATABASE_URL="postgresql://plantamigo:plantamigo123@localhost:5432/plantamigo_tests"
export TEST_DATABASE_URL=postgresql://plantamigo:plantamigo123@localhost:5432/plantamigo_tests
pytest tests
```

Sin `TEST_DATABASE_URL`, los tests se saltan en vez de fallar.

## 10. Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `can't open file '...\web\basedatos\web\basedatos\crear_bd.py'` | Se ejecutó desde `web/basedatos` con la ruta completa. | Desde la raíz: `python web/basedatos/crear_bd.py`. |
| `No module named 'psycopg'` | Faltan dependencias. | `pip install -r requirements.txt` |
| `No module named 'basedatos'` | Se importó desde fuera de `web`. | Arrancar con `python web/app.py` o `web/app_local.py`. |
| `password authentication failed for user "postgres"` | Contraseña de `postgres` incorrecta. | Es la de vuestra instalación de PostgreSQL. |
| `database "plantamigodb" does not exist` | No se ejecutó `crear_bd.py`. | Sección 2. |
| `relation "datos_planta" does not exist` | Conectado a otra base de datos (p. ej. `postgres`). | Revisar `DATABASE_URL` o la conexión de DBeaver. |
| La app arranca pero no guarda nada | Falta `ID_PLANTA`. | Sección 3. |
| `ForeignKeyViolation` al guardar lecturas | `ID_PLANTA` apunta a una planta que no existe. | Crear la planta (sección 5) o usar `--prueba`. |
| El calendario sale vacío en días pasados | `media_y_limpieza` borró las lecturas antiguas. | Ver el aviso de la sección 6. |
| En el JSON la temperatura sale entre comillas | `Decimal` sin convertir. | Sección 7. |
