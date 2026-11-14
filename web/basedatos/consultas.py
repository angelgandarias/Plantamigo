import os
import psycopg 

ZONA_HORARIA = "Europe/Madrid" 

class ErrorConexionBD(Exception):
    pass

class ErrorConsultaBD(Exception):
    pass

# Consulta SQL
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

# Para cambiar de 
def numero(valor):
    return None if valor is None else float(valor)

def datos_del_dia(dia):
    # Trata de conectarse a la base de datos
    try:
        conexion = psycopg.connect(os.environ.get("DATABASE_URL", ""), connect_timeout=3)
    except psycopg.Error as error:
        raise ErrorConexionBD(error) from error

    # Busca en la BD por el día y pilla todas las filas resultantes
    try:
        with conexion.cursor() as cursor:
            cursor.execute(SQL_DIA, {"dia": dia})
            filas = cursor.fetchall()
    except psycopg.OperationalError as error: 
        raise ErrorConexionBD(error) from error
    except psycopg.Error as error:
        raise ErrorConsultaBD(error) from error
    finally:
        conexion.close()

    # Traduce las filas extraidas de la BD a un diccionario para que sea más facil de recuperar
    plantas = [
        {
            "nombre": f[0],
            "tipo": f[1],
            "lecturas": f[2],
            "temperatura_media": numero(f[3]),
            "temperatura_min": numero(f[4]),
            "temperatura_max": numero(f[5]),
            "humedad_media": numero(f[6]),
            "luz_media": numero(f[7]),
            "calidad_aire_media": numero(f[8]),
        }

        for f in filas
    ]

    # Devuelve los datos
    return {"fecha": dia.isoformat(), "hay_datos": bool(plantas), "plantas": plantas}