"""Lectura de sensores de humedad del suelo (Grove Moisture Sensor, analógico).

Se leen a través del ADC del Grove Base Hat (I2C, dirección 0x04).
Conectados a los puertos analógicos A2 y A4 (A0 está ocupado por el sensor de luz;
cada puerto analógico usa dos canales, por eso se salta de dos en dos).

Uso:
    python3 sensores/moisture.py

Necesita I2C activado (sudo raspi-config -> Interfaces -> I2C) y
    pip install smbus2
"""

from time import sleep, strftime

I2C_BUS = 1
DIRECCION_HAT = 0x04
REG_RAW = 0x10  # registro base de lectura en bruto (0x10 + canal)

CANAL_1 = 2  # puerto A2
CANAL_2 = 4  # puerto A4

# Calibración (valores en bruto del ADC de 12 bits, 0-4095).
# AJÚSTALOS: mide con el sensor al aire (seco) y metido en un vaso de agua (mojado).
RAW_SECO = 0
RAW_MOJADO = 2500

INTERVALO = 1  # segundos entre lecturas


def abrir_bus():
    """Abre el bus I2C. Devuelve None si no hay smbus2 o no hay bus."""
    try:
        from smbus2 import SMBus

        return SMBus(I2C_BUS)
    except (ImportError, OSError):
        return None


def leer_raw(bus, canal):
    """Valor en bruto del ADC para un canal (0-7), o None si falla."""
    if bus is None:
        return None
    try:
        return bus.read_word_data(DIRECCION_HAT, REG_RAW + canal)
    except OSError:
        return None


def raw_a_porcentaje(raw, seco=RAW_SECO, mojado=RAW_MOJADO):
    """Convierte el valor en bruto a % de humedad (0-100), limitado al rango."""
    if raw is None or mojado == seco:
        return None
    porcentaje = (raw - seco) / (mojado - seco) * 100
    return max(0.0, min(100.0, porcentaje))


def leer_humedad(bus, canal, muestras=5):
    """Humedad en % de un sensor, promediando varias muestras para quitar ruido.

    Devuelve None si todas las lecturas fallan.
    """
    valores = []
    for _ in range(muestras):
        raw = leer_raw(bus, canal)
        if raw is not None:
            valores.append(raw)
        sleep(0.01)
    if not valores:
        return None
    return raw_a_porcentaje(sum(valores) / len(valores))


def leer_dos_humedades(bus, canal_1=CANAL_1, canal_2=CANAL_2):
    """Lectura simultánea de los dos sensores: (humedad_1, humedad_2) en %.

    Cada elemento es None si ese sensor falló. Comparten el mismo bus I2C,
    así que se leen seguidos (son microsegundos, a efectos prácticos es a la vez).
    """
    return leer_humedad(bus, canal_1), leer_humedad(bus, canal_2)


def media(valores):
    """Media ignorando los sensores que fallaron (None). None si fallaron todos."""
    validos = [v for v in valores if v is not None]
    return sum(validos) / len(validos) if validos else None


def _fmt(valor):
    return "  fallo" if valor is None else f"{valor:5.1f} %"


if __name__ == "__main__":
    bus = abrir_bus()
    if bus is None:
        print("No puedo abrir el bus I2C (¿falta 'pip install smbus2' o activar I2C?)")
        raise SystemExit(1)

    print(f"Leyendo humedad en A{CANAL_1} y A{CANAL_2} cada {INTERVALO} s (Ctrl+C para parar)")
    try:
        while True:
            humedades = leer_dos_humedades(bus)
            raws = (leer_raw(bus, CANAL_1), leer_raw(bus, CANAL_2))
            print(
                f"[{strftime('%H:%M:%S')}] "
                f"Sensor 1: {_fmt(humedades[0])} | Sensor 2: {_fmt(humedades[1])} | "
                f"Media: {_fmt(media(humedades))}  (raw {raws[0]}, {raws[1]})"
            )
            sleep(INTERVALO)
    except KeyboardInterrupt:
        print("\nParado.")
