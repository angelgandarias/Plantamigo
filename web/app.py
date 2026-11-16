import os
import sys
import threading
import time
 
from flask import Flask, jsonify, render_template, request

# Rutas para poder importar "sensores" (raíz del repo) y "repertorio" (que importa
# buzzer.py desde sensores/) al arrancar con `python web/app.py` desde cualquier sitio.
CARPETA_WEB = os.path.dirname(os.path.abspath(__file__))
RAIZ_REPO = os.path.dirname(CARPETA_WEB)
sys.path.insert(0, RAIZ_REPO)
sys.path.insert(0, os.path.join(RAIZ_REPO, "sensores"))

from sensores.buzzer import tocar, CANCION_PREDETERMINADA
from sensores.repertorio import REPERTORIO
from sensores.temperature import leer_temperatura
from sensores.lightSensor import leer_luz
from sensores.moisture import abrir_bus, leer_dos_humedades, media
from basedatos.acumulador import Acumulador, guardar_media_diaria
from basedatos.consultas import datos_del_dia, ErrorConexionBD, ErrorConsultaBD
from datetime import datetime
 
INTERVALO = 5 
 
app = Flask(__name__)
sonando = threading.Lock()
BUS_I2C = abrir_bus()  # ADC del hat (humedad en A2 y A4), se abre una sola vez

ultima = {"temperatura": None, "hora": None, "luz": None}

# --- Humedad del suelo (media de los 2 sensores en A2 y A4) ---
ultima_humedad = {"humedad": None, "hora": None}
ID_PLANTA = os.environ.get("ID_PLANTA")  # planta a la que se asignan las lecturas

# Cada 300 segunds (5 minutos) hará una lectura
INTERVALO_APUNTE = 300

# Ruta donde estan las lecturas de hoy
RUTA_FICHERO = os.path.join(CARPETA_WEB, "instance", "lecturas_hoy.jsonl")

# Funcion a la que se llamará cuando se tenga que guardar en la base de datos las medias
def guardar_dia(dia, medias):
    guardar_media_diaria(int(ID_PLANTA), dia, medias)

acumulador = Acumulador(RUTA_FICHERO, guardar_dia)


def lector_en_segundo_plano():
    while True:
        temperatura = leer_temperatura()
        light = leer_luz()
        if temperatura is not None:
            ultima["temperatura"] = round(temperatura, 1)
        if light is not None:
            ultima["luz"] = round(light[0],1)
        ultima["hora"] = time.time()
        time.sleep(INTERVALO)
 

def lector_humedad_en_segundo_plano():
    """Lee los dos sensores, calcula la media y la guarda en memoria.

    Va en su propio hilo para no depender del sensor de temperatura.
    """
    while True:
        # Lectura de los dos sensores y media (ignora el que falle; None si fallan los dos)
        humedad = media(leer_dos_humedades(BUS_I2C))
        if humedad is not None:
            ultima_humedad["humedad"] = round(humedad, 1)
            ultima_humedad["hora"] = time.time()
        time.sleep(INTERVALO)


# El hilo que irá apuntando los datos cada 5 minutos
def apuntar_lecturas_en_segundo_plano():

    while True:
        time.sleep(INTERVALO_APUNTE)
        acumulador.anadir(
            temperatura=ultima["temperatura"], humedad=ultima_humedad["humedad"], luz=ultima["luz"]
        )

# El hilo que mira si el dia ha llegado a su fin
def cerrar_dia_en_segundo_plano():
    while True:
        try:
            acumulador.cerrar_dias_pendientes()
        except Exception as error: 
            print(f"[BD] No se pudo guardar la media del día: {error}")
        time.sleep(60)


@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")
 
 
@app.route("/api/temperatura")
def api_temperatura():
    hora = ultima["hora"]
    antiguedad = None if hora is None else round(time.time() - hora)
    return jsonify(temperatura=ultima["temperatura"], antiguedad_s=antiguedad)


@app.route("/api/luz")
def api_luz():
    hora = ultima["hora"]
    antiguedad = None if hora is None else round(time.time() - hora)
    return jsonify(luz=ultima["luz"], antiguedad_s=antiguedad)
 
 
@app.route("/api/humedad")
def api_humedad():
    hora = ultima_humedad["hora"]
    antiguedad = None if hora is None else round(time.time() - hora)
    return jsonify(humedad=ultima_humedad["humedad"], antiguedad_s=antiguedad)


@app.route("/api/canciones", methods=["GET"])
def listar_canciones():
    return jsonify({"canciones": list(REPERTORIO.keys())})


@app.route("/api/melodia", methods=["POST"])
def tocar_melodia():
    if not sonando.acquire(blocking=False):
        return jsonify(mensaje="Ya está sonando, espera un momento 🎶"), 409
    try:
        data = request.get_json() or {}
        cancion = data.get("cancion") or CANCION_PREDETERMINADA
        tocar(cancion)
        return jsonify(mensaje="¡Melodía terminada! 🌼")
    except Exception as error:
        return jsonify(mensaje=f"Error con el buzzer: {error}"), 500
    finally:
        sonando.release()


# Consular a la BD por los datos de la planta segun la fecha
@app.route("/api/dia/<fecha>")
def api_dia(fecha):

    # Convertir la fecha en formato AÑO-MES-DÍA en una que Python pueda leer
    try:
        dia = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return jsonify(error="fecha", mensaje="Fecha no válida"), 400

    # Llama a datos_del_dia de consultas.py que consulta Postgres y devuelve el resultado como JSON al navegador
    try:
        return jsonify(datos_del_dia(dia))
    except ErrorConexionBD as error:
        print(f"[BD] No se pudo conectar: {error}")
        return jsonify(error="conexion", mensaje="No se ha podido conectar con la base de datos"), 503
    except ErrorConsultaBD as error:
        print(f"[BD] Error en la consulta: {error}")
        return jsonify(error="consulta", mensaje="La base de datos ha dado un error al consultar"), 500

 
if __name__ == "__main__":
    threading.Thread(target=lector_en_segundo_plano, daemon=True).start()
    threading.Thread(target=lector_humedad_en_segundo_plano, daemon=True).start()
    if ID_PLANTA:
        threading.Thread(target=apuntar_lecturas_en_segundo_plano, daemon=True).start()
        threading.Thread(target=cerrar_dia_en_segundo_plano, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, threaded=True)
