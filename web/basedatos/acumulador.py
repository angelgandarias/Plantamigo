import json
import os
import threading
from datetime import date

SENSORES = ["temperatura", "humedad", "luz"]

# Guardar en la base de datos los datos del día de hoy
def guardar_media_diaria(id_planta, dia, medias):
    from . import conectar

    # Abre la conexión con la BD
    with conectar() as conexion:
        conexion.execute(
            # La orden SQL para añadir una nueva fila a la tabla
            """INSERT INTO datos_planta (id_planta, fecha, temperatura, humedad, luz)
               VALUES (%s, %s::timestamp AT TIME ZONE 'Europe/Madrid', %s, %s, %s)
               ON CONFLICT (id_planta, fecha) DO NOTHING""",
            (id_planta, dia.isoformat(), medias["temperatura"], medias["humedad"], medias["luz"]),
        )

# Hace la media diaria de un sensor, el que se le introduzca
def calcular_media(lecturas, sensor):
    # Media de un sensor ignorando los valores vacíos
    valores = [l[sensor] for l in lecturas if l.get(sensor) is not None]

    # Si no hay ninguno, None
    if not valores:
        return None
    return round(sum(valores) / len(valores), 1)


class Acumulador:
    def __init__(self, ruta, guardar_media):
        self.ruta = ruta
        self.guardar_media = guardar_media  
        self.candado = threading.Lock() 
        os.makedirs(os.path.dirname(ruta), exist_ok=True)

    def anadir(self, **lectura):
        # Al dato del los sensores, le añade la fecha de hoy
        lectura["dia"] = date.today().isoformat()
        # Mete "el candado" para que nadie más pueda escribir mientras ocurre estre proceso
        with self.candado:
            # Guarda las medias en el RUTA_FICHERO antes especificado
            with open(self.ruta, "a", encoding="utf-8") as f:
                f.write(json.dumps(lectura) + "\n")

    def cerrar_dias_pendientes(self):
        # Mira qué día es hoy para borrar lo anterior
        hoy = date.today().isoformat()

        with self.candado:
            if not os.path.exists(self.ruta):
                return

            # Lee todas las lecturas del fichero
            with open(self.ruta, encoding="utf-8") as f:
                lecturas = [json.loads(linea) for linea in f if linea.strip()]

            # Por cada día ya terminado calcula su media y guardarla en la BD
            dias_terminados = sorted({l["dia"] for l in lecturas if l["dia"] < hoy})
            for dia in dias_terminados:
                del_dia = [l for l in lecturas if l["dia"] == dia]
                medias = {sensor: calcular_media(del_dia, sensor) for sensor in SENSORES}
                self.guardar_media(date.fromisoformat(dia), medias)  # si falla, no se borra nada

            if dias_terminados:
                # Al hacer el write, escribe por encima de los días anteriores, borrandolos
                with open(self.ruta, "w", encoding="utf-8") as f:
                    for l in lecturas:
                        if l["dia"] == hoy:
                            f.write(json.dumps(l) + "\n")
