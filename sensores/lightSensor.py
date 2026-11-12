import time
from grove.grove_light_sensor_v1_2 import GroveLightSensor

PIN = 0            # canal analógico (A0) donde está conectado el sensor
VALOR_MAX = 1000   # lectura con la máxima luz; ajústalo al calibrar
INTERVALO = 5      # segundos entre lecturas

light_sensor = GroveLightSensor(PIN)

while True:
    valor = light_sensor.light
    porcentaje = min(max(valor / VALOR_MAX * 100, 0), 100)
    print(f"Luz: {porcentaje:.1f}% (valor bruto: {valor})")
    time.sleep(INTERVALO)