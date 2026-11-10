import os
import sys
import threading
import time
 
from flask import Flask, jsonify, render_template
 
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sensores.buzzer import melodia
from sensores.temperature import buscar_sensor, leer_temperatura 
 
INTERVALO = 5 
 
app = Flask(__name__)
sonando = threading.Lock()

ultima = {"temperatura": None, "hora": None}
 

def lector_en_segundo_plano():
    carpeta = buscar_sensor()
    if carpeta is None:
        print("AVISO: no encuentro el sensor de temperatura (¿falta el dtoverlay?)")
        return
    while True:
        temperatura = leer_temperatura(carpeta)
        if temperatura is not None:
            ultima["temperatura"] = round(temperatura, 1)
            ultima["hora"] = time.time()
        time.sleep(INTERVALO)
 
 
@app.route("/")
def inicio():
    return render_template("index.html")
 
 
@app.route("/api/temperatura")
def api_temperatura():
    hora = ultima["hora"]
    antiguedad = None if hora is None else round(time.time() - hora)
    return jsonify(temperatura=ultima["temperatura"], antiguedad_s=antiguedad)
 
 
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
 
 
if __name__ == "__main__":
    threading.Thread(target=lector_en_segundo_plano, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, threaded=True)