"""Diagnóstico temporal del ADC del hat: imprime los 8 canales a la vez.

Uso (en la Pi):  python3 sensores/diagnostico_adc.py

Prueba guiada:
  1. Deja todo quieto unos segundos.
  2. Tapa con la mano el sensor de LUZ (A0)  -> ¿qué columnas cambian?
  3. Mete SOLO un sensor de humedad en agua   -> ¿qué columna salta?
Se puede borrar cuando se resuelva.
"""

from time import sleep, strftime

from smbus2 import SMBus

from moisture import DIRECCION_HAT, I2C_BUS

REGISTROS = {"raw": 0x10, "volt": 0x20, "ratio": 0x30}


def leer(bus, registro, canal):
    try:
        return bus.read_word_data(DIRECCION_HAT, registro + canal)
    except OSError:
        return None


if __name__ == "__main__":
    bus = SMBus(I2C_BUS)
    print(f"ADC en 0x{DIRECCION_HAT:02x}. Columnas = canales 0..7 (A0 usa 0-1, A2 usa 2-3, A4 usa 4-5)")
    try:
        while True:
            print(f"--- {strftime('%H:%M:%S')}")
            for nombre, base in REGISTROS.items():
                valores = [leer(bus, base, c) for c in range(8)]
                print(f"{nombre:>5}: " + " ".join(f"{'--' if v is None else v:>5}" for v in valores))
            sleep(1)
    except KeyboardInterrupt:
        print("\nParado.")
