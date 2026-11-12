import os
import sys
import threading
import time
 
from flask import Flask, jsonify, render_template
 
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sensores.buzzer import melodia
from sensores.temperature import buscar_sensor, leer_temperatura
from sensores.moisture import abrir_bus, leer_dos_humedades
from basedatos.consultas import datos_del_dia, ErrorConexionBD, ErrorConsultaBD
from datetime import datetime
 
INTERVALO = 5 
 
app = Flask(__name__)
sonando = threading.Lock()
BUS_I2C = abrir_bus()  # ADC del hat (humedad en A2 y A4), se abre una sola vez

ultima = {"temperatura": None, "hora": None}
 

def lector_en_segundo_plano():
    carpeta = buscar_sensor()
    if carpeta is None:
        print("AVISO: no encuentro el sensor de temperatura (¿falta el dtoverlay?)")
        return
    while True:
        temperatura = leer_temperatura(carpeta)
        light = leer_luz()
        if temperatura is not None:
            ultima["temperatura"] = round(temperatura, 1)
        if light is not None:
            ultima["luz"] = light
        ultima["hora"] = time.time()
        time.sleep(INTERVALO)
 

# Funciones de estadisticas 
def lectura_simultanea_datos_brutos()-> tuple[float, float]:
    # Devuelve una tupla con la humedad (%) de los dos sensores (None si alguno falla)
    return leer_dos_humedades(BUS_I2C)
def obtener_media(tupla_datos:tuple[float, float])-> float:
    total:float = 0
    elementos = 0
    for dato in tupla_datos:
        elementos += 1
        total += dato
    return total / elementos

def formatear_dato_y_enviar():
    # TODO: Supongo que aqui deberia de formatear ese dato y enviarlo a la web 
    # Con formatear se refiere a json o algun otro formato?
    # para enviar supongo que debo hacer algun POST?
    return 

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
    return jsonify(temperatura=ultima["luz"], antiguedad_s=antiguedad)
 
 
@app.route("/api/melodia", methods=["POST"])
def tocar_melodia():
    if not sonando.acquire(blocking=False):
        return jsonify(mensaje="Ya está sonando, espera un momento 🎶"), 409
    try:
        melodia()
        return jsonify(mensaje="¡Melodía terminada! 🌼")
    except Exception as error:
        return jsonify(mensaje=f"Error con el buzzer: {error}"), 500
    finally:
        sonando.release()
 
@app.route("/api/dia/<fecha>")
def api_dia(fecha):
    """Resumen de un día (AAAA-MM-DD) desde la base de datos."""
    try:
        dia = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return jsonify(error="fecha", mensaje="Fecha no válida, usa AAAA-MM-DD"), 400
    try:
        return jsonify(datos_del_dia(dia))
    except ErrorConexionBD as error:
        print(f"[BD] No se pudo conectar: {error}")
        return jsonify(error="conexion",
                       mensaje="No se ha podido conectar con la base de datos"), 503
    except ErrorConsultaBD as error:
        print(f"[BD] Error en la consulta: {error}")
        return jsonify(error="consulta",
                       mensaje="La base de datos ha dado un error al consultar"), 500
 
if __name__ == "__main__":
    threading.Thread(target=lector_en_segundo_plano, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, threaded=True)
