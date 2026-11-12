# Plantamigo
## Proyecto dedicado para los jovenes que no salen de casa 
### Dispone de diferentes funcionalidades 
* Incluye diferentes APIs para poder obtener informacion del entorno del usuario
* Una pantalla para poder ver las reacciones de la planta
* Un grafico en el que se puede ver todos los datos referentes a la planta

## Base de datos (PostgreSQL)

El esquema está en `web/basedatos/schema.sql` y el acceso desde Python en `web/basedatos/`.

Tablas: `usuarios`, `plantas`, `canciones`, `usuarios_canciones` (canciones desbloqueadas por cada usuario) y `datos_planta` (lecturas de los sensores).

Puesta en marcha (desde la raíz del repositorio):

1. Instalar dependencias: `pip install -r requirements.txt`
2. Crear usuario `plantamigo`, base de datos `plantamigodb` y tablas (pide la contraseña de `postgres`):
   `python web/basedatos/crear_bd.py`
   - `--prueba`: carga también datos de ejemplo.
   - `--reiniciar`: borra la base de datos y la crea de nuevo.
   - `--contrasena X`: contraseña del usuario `plantamigo` (por defecto `plantamigo123`, cámbiala fuera de pruebas locales).
3. Para la aplicación, definir la conexión en la variable de entorno `DATABASE_URL`:
   `postgresql://plantamigo:plantamigo123@localhost:5432/plantamigodb`

Pruebas (usan una base de datos desechable, se borran sus datos):
`TEST_DATABASE_URL=postgresql://... pytest tests`
