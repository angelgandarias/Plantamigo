import time
from grove.grove_light_sensor_v1_2 import GroveLightSensor

PIN = 0            # canal analógico (A0) donde está conectado el sensor
VALOR_MAX = 1000   # lectura con la máxima luz; ajústalo al calibrar
INTERVALO = 5      # segundos entre lecturas

light_sensor = GroveLightSensor(PIN)


def leer_luz():
    """Devuelve (porcentaje, valor_bruto) de luz."""
    valor = light_sensor.light
    porcentaje = min(max(valor / VALOR_MAX * 100, 0), 100)
    return porcentaje, valor

'''
while True:
    porcentaje, valor = leer_luz()
    print(f"Luz: {porcentaje:.1f}% (valor bruto: {valor})")
    time.sleep(INTERVALO)'''
