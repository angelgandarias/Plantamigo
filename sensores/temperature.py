import glob
from seeed_dht import DHT
from time import sleep, strftime

# Puerto digital (D5) donde está conectado el sensor
PIN = 5  
# Cada cuanto tiempo hace una medición de temperatura
INTERVALO = 0.5
# Crea el objeto del sensor
sensor = DHT("11", PIN)

def leer_temperatura():
    """Devuelve la temperatura en °C o "None" si la lectura falla."""
    try:
        datos = sensor.read()

        # Solo nos interesa el segundo campo porque el primero es la humedad
        temperatura = datos[1]

        # Si falla la lectura...
        if temperatura is None:
            return None
        # Si no...
        else:
            return temperatura

    # Capturar otros errores que puedan ocurrir
    except Exception:
        return None

# Función principal
if __name__ == "__main__":
    print(f"Leyendo temperatura cada {INTERVALO}")
    try:
        # El bucle que tiene la lógica de lo que se imprime por pantalla
        while True:
            temperatura = leer_temperatura()
            hora = strftime("%H:%M:%S")

            if temperatura is None:
                print(f"[{hora}] Lectura fallida, reintento en {INTERVALO}")
            else:
                print(f"[{hora}] Temperatura: {temperatura:.1f} °C")
            sleep(INTERVALO)

    # Si detiene forzosamente
    except KeyboardInterrupt:
        print("\nParado.")
