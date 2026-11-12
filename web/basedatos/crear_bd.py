"""Crea desde cero la base de datos de Plantamigo en un PostgreSQL local.

Uso (desde la raíz del repositorio):
    python web/basedatos/crear_bd.py               # crea usuario, base de datos y tablas
    python web/basedatos/crear_bd.py --prueba      # además carga datos de ejemplo
    python web/basedatos/crear_bd.py --reiniciar   # borra la base de datos y la vuelve a crear

Pide la contraseña del administrador "postgres".
"""

import argparse
import getpass
import os
from pathlib import Path

import psycopg
from psycopg import sql

CARPETA = Path(__file__).resolve().parent

NOMBRE_BD = "plantamigodb"
USUARIO_BD = "plantamigo"


def ejecutar_fichero(conexion, nombre):
    conexion.execute((CARPETA / nombre).read_text(encoding="utf-8"))
    print(f"  ✔ {nombre}")


def preparar_usuario_y_bd(args, contrasena_admin):
    """Con el administrador: crea el usuario y la base de datos si no existen."""
    with psycopg.connect(
        host=args.host, port=args.port, user=args.admin,
        password=contrasena_admin, dbname="postgres", autocommit=True,
    ) as conexion:
        if conexion.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (USUARIO_BD,)).fetchone():
            print(f"El usuario '{USUARIO_BD}' ya existe.")
        else:
            conexion.execute(sql.SQL("CREATE USER {} WITH PASSWORD {}").format(
                sql.Identifier(USUARIO_BD), sql.Literal(args.contrasena)))
            print(f"Usuario '{USUARIO_BD}' creado.")

        existe = conexion.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (NOMBRE_BD,)).fetchone()
        if existe and args.reiniciar:
            conexion.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(NOMBRE_BD)))
            print(f"Base de datos '{NOMBRE_BD}' borrada.")
            existe = False
        if existe:
            print(f"La base de datos '{NOMBRE_BD}' ya existe.")
        else:
            conexion.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(NOMBRE_BD), sql.Identifier(USUARIO_BD)))
            print(f"Base de datos '{NOMBRE_BD}' creada.")


def crear_tablas(args):
    """Con el usuario del proyecto, para que las tablas sean suyas."""
    with psycopg.connect(
        host=args.host, port=args.port, user=USUARIO_BD,
        password=args.contrasena, dbname=NOMBRE_BD, autocommit=True,
    ) as conexion:
        print("Ejecutando scripts:")
        ejecutar_fichero(conexion, "schema.sql")
        ejecutar_fichero(conexion, "datos_iniciales.sql")

        if args.prueba:
            if conexion.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone():
                print("  - datos_prueba.sql omitido: ya hay usuarios (usa --reiniciar para empezar de cero)")
            else:
                ejecutar_fichero(conexion, "datos_prueba.sql")


def main():
    parser = argparse.ArgumentParser(description="Crea la base de datos de Plantamigo.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--admin", default="postgres", help="usuario administrador de PostgreSQL")
    parser.add_argument("--contrasena", default="plantamigo123",
                        help=f"contraseña del usuario '{USUARIO_BD}' (solo se usa al crearlo)")
    parser.add_argument("--prueba", action="store_true", help="cargar datos de ejemplo")
    parser.add_argument("--reiniciar", action="store_true",
                        help="BORRAR la base de datos y crearla de nuevo")
    args = parser.parse_args()

    if args.reiniciar:
        respuesta = input(f"Se borrarán TODOS los datos de '{NOMBRE_BD}'. Escribe 'si' para continuar: ")
        if respuesta.strip().lower() not in ("si", "sí"):
            print("Cancelado.")
            return

    contrasena_admin = os.environ.get("PGPASSWORD") or getpass.getpass(
        f"Contraseña del usuario '{args.admin}' de PostgreSQL: ")

    try:
        preparar_usuario_y_bd(args, contrasena_admin)
        crear_tablas(args)
    except psycopg.OperationalError as error:
        raise SystemExit(f"\nNo se pudo conectar a PostgreSQL:\n{error}")

    print(f"\nListo. Conéctate desde DBeaver a '{NOMBRE_BD}' con el usuario '{USUARIO_BD}'.")


if __name__ == "__main__":
    main()
