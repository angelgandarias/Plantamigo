import os

import psycopg  # el mismo driver que usa basedatos/__init__.py

ZONA_HORARIA = "Europe/Madrid"  # el "día" del calendario es el día en España


class ErrorConexionBD(Exception):
    """No se ha podido conectar con la base de datos (apagada, mala contraseña...)."""


class ErrorConsultaBD(Exception):
    """Hay conexión, pero la consulta ha fallado (falta una tabla, SQL mal...)."""


# Resumen de un día, una fila por planta. Los límites del día se calculan en hora
# de Madrid, porque la columna "fecha" guarda el instante exacto (TIMESTAMPTZ).
SQL_DIA = """
    SELECT p.nombre_planta,
           p.tipo_planta,
           count(*)                                AS lecturas,
           round(avg(d.temperatura), 1)            AS temperatura_media,
           round(min(d.temperatura), 1)            AS temperatura_min,
           round(max(d.temperatura), 1)            AS temperatura_max,
           round(avg(d.humedad), 1)                AS humedad_media,
           round(avg(d.luz)::numeric, 1)           AS luz_media,
           round(avg(d.calidad_aire)::numeric, 1)  AS calidad_aire_media
    FROM datos_planta d
    JOIN plantas p USING (id_planta)
    WHERE d.fecha >= %(dia)s::timestamp AT TIME ZONE '{zona}'
      AND d.fecha <  (%(dia)s::date + 1)::timestamp AT TIME ZONE '{zona}'
    GROUP BY p.id_planta, p.nombre_planta, p.tipo_planta
    ORDER BY p.nombre_planta
""".format(zona=ZONA_HORARIA)


def _numero(valor):
    """NUMERIC llega como Decimal; el JSON necesita float. NULL -> None."""
    return None if valor is None else float(valor)


def datos_del_dia(dia):
    """Devuelve el resumen de un día (objeto date) para cada planta.

    {"fecha": "2026-11-12", "hay_datos": True, "plantas": [ {...}, ... ]}

    Lanza ErrorConexionBD si no hay conexión y ErrorConsultaBD si la consulta falla.
    """
    try:
        conexion = psycopg.connect(os.environ.get("DATABASE_URL", ""), connect_timeout=3)
    except psycopg.Error as error:
        raise ErrorConexionBD(error) from error

    try:
        with conexion.cursor() as cursor:
            cursor.execute(SQL_DIA, {"dia": dia})
            filas = cursor.fetchall()
    except psycopg.OperationalError as error:  # se cayó la conexión a mitad
        raise ErrorConexionBD(error) from error
    except psycopg.Error as error:
        raise ErrorConsultaBD(error) from error
    finally:
        conexion.close()

    plantas = [
        {
            "nombre": f[0],
            "tipo": f[1],
            "lecturas": f[2],
            "temperatura_media": _numero(f[3]),
            "temperatura_min": _numero(f[4]),
            "temperatura_max": _numero(f[5]),
            "humedad_media": _numero(f[6]),
            "luz_media": _numero(f[7]),
            "calidad_aire_media": _numero(f[8]),
        }
        for f in filas
    ]
    return {"fecha": dia.isoformat(), "hay_datos": bool(plantas), "plantas": plantas}