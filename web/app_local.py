"""Arranca la web de Plantamigo en un ordenador normal, sin la Raspberry Pi.

Sustituye el hardware por versiones simuladas ANTES de importar app.py
(que no se modifica) y luego la arranca igual que `python web/app.py`:

    python web/app_local.py

- Temperatura (DHT11): valores aleatorios en vez de leer /sys/bus/iio.
- Humedad (ADC I2C del Grove Base Hat): un SMBus falso en lugar de smbus2.
- Luz (grove.py): un GroveLightSensor falso.
- Buzzer (gpiozero): imprime las notas por consola en lugar de sonar (dura lo mismo que la canción).

La base de datos sigue siendo real: define DATABASE_URL si quieres usar el calendario.
OJO: si defines también ID_PLANTA, se activan el acumulador y el cierre de día como en la Pi:
las lecturas simuladas se apuntan en web/instance/lecturas_hoy.jsonl cada 5 min y las medias
del día (simuladas) se guardan en esa BD.
"""

import os
import random
import sys
import types

CARPETA_WEB = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CARPETA_WEB))  # raíz del repo, para "sensores"
sys.path.insert(0, CARPETA_WEB)  # para "app" y "basedatos"
sys.path.insert(0, os.path.join(os.path.dirname(CARPETA_WEB), "sensores"))  # buzzer.py hace "from repertorio import ..."


def _modulo(nombre, **atributos):
    modulo = types.ModuleType(nombre)
    modulo.__dict__.update(atributos)
    sys.modules[nombre] = modulo
    return modulo


# ---------- Humedad: smbus2 falso ----------
class SMBusFalso:
    def __init__(self, bus):
        self.bus = bus

    def read_word_data(self, direccion, registro):
        return random.randint(600, 1900)  # en bruto, 12 bits

    def write_byte(self, direccion, valor):
        pass

    def read_byte(self, direccion):
        return 0

    def close(self):
        pass


_modulo("smbus2", SMBus=SMBusFalso)


# ---------- Luz: grove.py falso ----------
class GroveLightSensorFalso:
    def __init__(self, pin):
        self.pin = pin

    @property
    def light(self):
        return random.randint(200, 900)

# ---------- Temperatura: seeed_dht falso (para que temperature.py se pueda importar) ----------
class DHTFalso:
    def __init__(self, modelo, pin):
        self.modelo = modelo
        self.pin = pin

    def read(self):
        return random.uniform(40, 60), random.uniform(18, 26)  # (humedad, temperatura)


_modulo("seeed_dht", DHT=DHTFalso)

_modulo("grove")
_modulo("grove.grove_light_sensor_v1_2", GroveLightSensor=GroveLightSensorFalso)


# ---------- Buzzer: gpiozero falso ----------
class PWMOutputDeviceFalso:
    """Imita PWMOutputDevice: avisa por consola al cambiar de nota, sin sonar."""

    def __init__(self, pin, *args, **kwargs):
        self.pin = pin
        self.frequency = None
        self._value = 0.0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, valor):
        self._value = valor
        if valor:
            print(f"[buzzer simulado GPIO{self.pin}] {self.frequency} Hz (vol {valor})")

    def close(self):
        pass


_modulo("gpiozero", PWMOutputDevice=PWMOutputDeviceFalso)


# ---------- Temperatura: se parchea el módulo antes de que app.py lo importe ----------
import sensores.temperature as temperatura  # noqa: E402

temperatura.leer_temperatura = lambda: random.uniform(18.0, 26.0)


if __name__ == "__main__":
    import threading

    import app  # noqa: E402  (importa ya los sensores simulados)

    threading.Thread(target=app.lector_en_segundo_plano, daemon=True).start()
    threading.Thread(target=app.lector_humedad_en_segundo_plano, daemon=True).start()
    if app.ID_PLANTA:  # igual que en app.py
        threading.Thread(target=app.apuntar_lecturas_en_segundo_plano, daemon=True).start()
        threading.Thread(target=app.cerrar_dia_en_segundo_plano, daemon=True).start()
    app.app.run(host="127.0.0.1", port=5000, threaded=True, debug=False)
