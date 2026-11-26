"""Buzzer de Plantamigo (pin D22 = GPIO22).
"""

import os
import sys
from time import sleep
from gpiozero import PWMOutputDevice
from repertorio import REPERTORIO

PIN = 22  # D22 en el Grove Base Hat = GPIO22
VOLUMEN = 0.5

CANCION_PREDETERMINADA = "himno_alegria"

semitonos = {
    "Do": 0, "Do#": 1, "Reb": 1,
    "Re": 2, "Re#": 3, "Mib": 3,
    "Mi": 4,
    "Fa": 5, "Fa#": 6, "Solb": 6,
    "Sol": 7, "Sol#": 8, "Lab": 8,
    "La": 9, "La#": 10, "Sib": 10,
    "Si": 11,
}
def nota_a_hz(nota):
    """Convierte una nota (ej. "Mi4", "Sol#3", "Sib4") a Hz."""
    # Una nota tiene dos partes: el nombre y el número de octava.
    # Ejemplo: "Sol#3" -> nombre = "Sol#", octava = 3
    # Avanzamos letra a letra hasta encontrar el número de la octava.
    nombre = ""
    numero = ""
    if nota == "REST":
        return 0

    for letra in nota:
        if letra.isdigit():
            numero += letra   # Guarda el número que encuentre
        else:
            nombre += letra   # Se queda con el resto (la nota y su # o b)

    if numero != "":
        octava = int(numero)
    else:
        octava = 4    
        
    semitono = semitonos[nombre]

    # El sistema MIDI numera las notas: cada octava son 12 semitonos y
    # La4 es el número 69, que suena exactamente a 440 Hz.
    numero_midi = (octava + 1) * 12 + semitono

    # A partir del número MIDI, cada semitono hacia arriba multiplica la
    # frecuencia por 2^(1/12). Esta fórmula da los Hz exactos de la nota.
    return round(440 * (2 ** ((numero_midi - 69) / 12)))


def tocar(nombre_cancion, volumen=VOLUMEN):
    """Toca una canción del repertorio buscando por su nombre."""
    cancion = REPERTORIO[nombre_cancion]
    buzzer = PWMOutputDevice(PIN)
    try:
        segundos_por_negra = cancion["negra"]
        for nota, duracion in cancion["notas"]:
            hz = nota_a_hz(nota)
            if hz > 0:
                buzzer.frequency = hz
                buzzer.value = volumen
                
            duracion_segundos = segundos_por_negra * duracion
            hueco = min(0.05, duracion_segundos * 0.1)
            sleep(max(0, duracion_segundos - hueco))

            buzzer.value = 0.0
            sleep(hueco)
    finally:
        buzzer.close()

def pitido(veces=2, hz=2000, duracion=0.12, volumen=VOLUMEN):
    
    buzzer = PWMOutputDevice(PIN)
    try:
        buzzer.frequency = hz
        for _ in range(veces):
            buzzer.value = volumen
            sleep(duracion)
            buzzer.value = 0.0
            sleep(duracion)
    finally:
        buzzer.close()
