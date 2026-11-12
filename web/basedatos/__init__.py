"""Para acceder a la base de datos PostgreSQL de Plantamigo.

La cadena de conexión se lee de la variable de entorno DATABASE_URL:
    postgresql://plantamigo:contraseña@localhost:5432/plantamigodb

Para crear las tablas y el catálogo inicial:
    python -m web.basedatos
"""

import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from werkzeug.security import check_password_hash, generate_password_hash

CARPETA = Path(__file__).resolve().parent


class PuntosInsuficientes(Exception):
    pass


def conectar():
    """Abre una conexión nueva. Usar con `with` para que haga commit/rollback solo."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Falta la variable de entorno DATABASE_URL")
    return psycopg.connect(url, row_factory=dict_row)


def crear_esquema():
    """Crea las tablas si es que no existen y carga el catálogo inicial."""
    with conectar() as conexion:
        for fichero in ("schema.sql", "datos_iniciales.sql"):
            conexion.execute((CARPETA / fichero).read_text(encoding="utf-8"))


#---------- Usuarios ----------

def crear_usuario(nombre_usuario, email, contrasena):
    """Registra un usuario y devuelve su id. La contraseña se guarda hasheada."""
    with conectar() as conexion:
        fila = conexion.execute(
            """INSERT INTO usuarios (nombre_usuario, email, contrasena_hash)
               VALUES (%s, %s, %s) RETURNING id_usuario""",
            (nombre_usuario, email, generate_password_hash(contrasena)),
        ).fetchone()
    return fila["id_usuario"]


def comprobar_credenciales(nombre_usuario, contrasena):
    """Devuelve el usuario sin el hash si la contraseña es correcta, o None."""
    with conectar() as conexion:
        usuario = conexion.execute(
            "SELECT * FROM usuarios WHERE nombre_usuario = %s", (nombre_usuario,)
        ).fetchone()
    if usuario is None or not check_password_hash(usuario["contrasena_hash"], contrasena):
        return None
    del usuario["contrasena_hash"]
    return usuario


def sumar_puntos(id_usuario, puntos):
    """Suma (o resta, si es negativo) puntos y devuelve el nuevo total."""
    with conectar() as conexion:
        fila = conexion.execute(
            "UPDATE usuarios SET puntos = puntos + %s WHERE id_usuario = %s RETURNING puntos",
            (puntos, id_usuario),
        ).fetchone()
    return None if fila is None else fila["puntos"]


#---------- Plantas ----------

def crear_planta(id_usuario, tipo_planta, nombre_planta, descripcion_planta=None):
    with conectar() as conexion:
        fila = conexion.execute(
            """INSERT INTO plantas (id_usuario, tipo_planta, nombre_planta, descripcion_planta)
               VALUES (%s, %s, %s, %s) RETURNING id_planta""",
            (id_usuario, tipo_planta, nombre_planta, descripcion_planta),
        ).fetchone()
    return fila["id_planta"]


def plantas_de_usuario(id_usuario):
    with conectar() as conexion:
        return conexion.execute(
            "SELECT * FROM plantas WHERE id_usuario = %s ORDER BY id_planta", (id_usuario,)
        ).fetchall()


#---------- Datos de los sensores ----------

def guardar_lectura(id_planta, temperatura=None, humedad=None, luz=None, calidad_aire=None):
    """Guarda una lectura de sensores con la fecha actual del servidor."""
    with conectar() as conexion:
        conexion.execute(
            """INSERT INTO datos_planta (id_planta, temperatura, humedad, luz, calidad_aire)
               VALUES (%s, %s, %s, %s, %s)""",
            (id_planta, temperatura, humedad, luz, calidad_aire),
        )


def ultimas_lecturas(id_planta, limite=100):
    """Devuelve las últimas lecturas de una planta, de la más reciente a la más antigua."""
    with conectar() as conexion:
        return conexion.execute(
            "SELECT * FROM datos_planta WHERE id_planta = %s ORDER BY fecha DESC LIMIT %s",
            (id_planta, limite),
        ).fetchall()


#---------- Canciones ----------

def canciones_de_usuario(id_usuario):
    with conectar() as conexion:
        return conexion.execute(
            """SELECT c.* FROM canciones c
               JOIN usuarios_canciones uc USING (id_cancion)
               WHERE uc.id_usuario = %s ORDER BY c.nombre_cancion""",
            (id_usuario,),
        ).fetchall()


def comprar_cancion(id_usuario, id_cancion):
    """Desbloquea una canción descontando sus puntos, todo en una misma transacción."""
    with conectar() as conexion:
        cancion = conexion.execute(
            "SELECT precio_puntos FROM canciones WHERE id_cancion = %s", (id_cancion,)
        ).fetchone()
        if cancion is None:
            raise ValueError(f"No existe la canción {id_cancion}")

        insertada = conexion.execute(
            """INSERT INTO usuarios_canciones (id_usuario, id_cancion) VALUES (%s, %s)
               ON CONFLICT DO NOTHING""",
            (id_usuario, id_cancion),
        ).rowcount
        if not insertada:
            return  #ya la tenía: no se cobra otra vez

        pagada = conexion.execute(
            """UPDATE usuarios SET puntos = puntos - %s
               WHERE id_usuario = %s AND puntos >= %s""",
            (cancion["precio_puntos"], id_usuario, cancion["precio_puntos"]),
        ).rowcount
        if not pagada:
            raise PuntosInsuficientes()  #al salir del with se hace rollback del INSERT
