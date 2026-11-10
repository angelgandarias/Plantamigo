import glob
from time import sleep, strftime

INTERVALO = 0.5  # segundos entre lecturas


def buscar_sensor():
    """Busca la carpeta del sensor DHT que crea el driver del kernel."""
    for carpeta in glob.glob("/sys/bus/iio/devices/iio:device*"):
        try:
            with open(f"{carpeta}/name") as f:
                if f.read().strip().startswith("dht11"):
                    return carpeta
        except OSError:
            pass
    return None


def leer_temperatura(carpeta):
    """Devuelve la temperatura en °C, o None si la lectura falla."""
    try:
        with open(f"{carpeta}/in_temp_input") as f:
            return int(f.read()) / 1000  # viene en milésimas de grado
    except OSError:
        return None


if __name__ == "__main__":
    carpeta = buscar_sensor()
    if carpeta is None:
        print("No encuentro el sensor.")
        print("Falta 'dtoverlay=dht11,gpiopin=5' en /boot/firmware/config.txt o reiniciar.")
        raise SystemExit(1)

    print(f"Leyendo temperatura cada {INTERVALO} s (Ctrl+C para parar)")
    try:
        while True:
            temperatura = leer_temperatura(carpeta)
            hora = strftime("%H:%M:%S")
            if temperatura is None:
                print(f"[{hora}] Lectura fallida, reintento en {INTERVALO} s")
            else:
                print(f"[{hora}] Temperatura: {temperatura:.1f} °C")
            sleep(INTERVALO)
    except KeyboardInterrupt:
        print("\nParado.")
