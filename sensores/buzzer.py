"""Hola mundo del buzzer de Plantamigo (pin D22 = GPIO22).

Uso:
    python3 pruebas/hola_buzzer.py           # modo pitido (sirve para cualquier buzzer)
    python3 pruebas/hola_buzzer.py melodia   # modo melodía (solo buzzer PASIVO)

Si en modo pitido oyes tres pitidos claros -> tienes un buzzer ACTIVO (un solo tono).
Si solo oyes "clics" -> es PASIVO: prueba el modo melodía.
"""

import sys
from time import sleep

PIN = 22  # D22 en el Grove Base Hat = GPIO22


def pitido():
    from gpiozero import Buzzer

    buzzer = Buzzer(PIN)
    print("Pitando 3 veces en GPIO22...")
    for _ in range(3):
        buzzer.on()
        sleep(0.2)
        buzzer.off()
        sleep(0.2)
    print("¡Hecho!")


def melodia():
    from gpiozero import TonalBuzzer
    from gpiozero.tones import Tone

    # Rango A4-A6: los piezos suenan más limpios en agudos
    buzzer = TonalBuzzer(PIN, mid_tone=Tone("A5"), octaves=1)
    # Himno de la Alegría (Beethoven), tema principal en Do mayor
    n = 0.4  # duración de una negra en segundos (bájalo para ir más rápido)
    notas = [
        # Mi Mi Fa Sol | Sol Fa Mi Re | Do Do Re Mi | Mi. Re Re
        ("E5", n), ("E5", n), ("F5", n), ("G5", n),
        ("G5", n), ("F5", n), ("E5", n), ("D5", n),
        ("C5", n), ("C5", n), ("D5", n), ("E5", n),
        ("E5", n * 1.5), ("D5", n / 2), ("D5", n * 2),
        # Mi Mi Fa Sol | Sol Fa Mi Re | Do Do Re Mi | Re. Do Do
        ("E5", n), ("E5", n), ("F5", n), ("G5", n),
        ("G5", n), ("F5", n), ("E5", n), ("D5", n),
        ("C5", n), ("C5", n), ("D5", n), ("E5", n),
        ("D5", n * 1.5), ("C5", n / 2), ("C5", n * 2),
    ]
    print("Tocando el Himno de la Alegría en GPIO22...")
    for nota, duracion in notas:
        buzzer.play(Tone(nota))
        sleep(duracion - 0.05)
        buzzer.stop()
        sleep(0.05)  # pequeño silencio para que se distingan las notas repetidas
    buzzer.close()
    print("¡Hecho!")


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "melodia":
            melodia()
        else:
            pitido()
    except KeyboardInterrupt:
        print("\nInterrumpido.")
