"""Arranca la web de Plantamigo en un ordenador normal, sin la Raspberry Pi.

Sustituye el hardware por versiones simuladas ANTES de importar app.py
(que no se modifica) y luego la arranca igual que `python web/app.py`:

    python web/app_local.py

- Temperatura (DHT11): valores aleatorios en vez de leer /sys/bus/iio.
- Humedad (ADC I2C del Grove Base Hat): un SMBus falso en lugar de smbus2.
- Luz (grove.py): un GroveLightSensor falso.
- Buzzer (gpiozero): imprime las notas por consola en lugar de sonar.

La base de datos sigue siendo real: define DATABASE_URL si quieres usar el calendario.
"""

import os
import random
import sys
import types

CARPETA_WEB = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CARPETA_WEB))  # raíz del repo, para "sensores"
sys.path.insert(0, CARPETA_WEB)  # para "app" y "basedatos"


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
        return random.randint(900, 1800)  # en bruto, 12 bits

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


_modulo("grove")
_modulo("grove.grove_light_sensor_v1_2", GroveLightSensor=GroveLightSensorFalso)


# ---------- Buzzer: gpiozero falso ----------
class Tone:
    def __init__(self, nota):
        self.nota = nota

    def __repr__(self):
        return f"Tone({self.nota!r})"


class BuzzerFalso:
    def __init__(self, pin, *args, **kwargs):
        self.pin = pin

    def on(self):
        print(f"[buzzer simulado GPIO{self.pin}] on")

    def off(self):
        print(f"[buzzer simulado GPIO{self.pin}] off")

    def play(self, tono):
        print(f"[buzzer simulado GPIO{self.pin}] {tono.nota}")

    def stop(self):
        pass

    def close(self):
        pass


_modulo("gpiozero", Buzzer=BuzzerFalso, TonalBuzzer=BuzzerFalso)
_modulo("gpiozero.tones", Tone=Tone)
sys.modules["gpiozero"].tones = sys.modules["gpiozero.tones"]


# ---------- Temperatura: se parchea el módulo antes de que app.py lo importe ----------
import sensores.temperature as temperatura  # noqa: E402

temperatura.buscar_sensor = lambda: "/simulado/dht11"
temperatura.leer_temperatura = lambda carpeta: random.uniform(18.0, 26.0)


if __name__ == "__main__":
    import threading

    import app  # noqa: E402  (importa ya los sensores simulados)

    threading.Thread(target=app.lector_en_segundo_plano, daemon=True).start()
    app.app.run(host="127.0.0.1", port=5000, threaded=True, debug=False)
