from grove.display.jhd1802 import JHD1802
from time import sleep
from buzzer import pitido

# Texto de cada una de las dos filas
FILA1 = "Hola mundo"
FILA2 = "Plantamigo"

FILA1HUMEDAD = "Hola, tengo sed"
FILA2HUMEDAD = "Dame agua!"

# Crea el objeto de la pantalla 
lcd = JHD1802()

# Dejar la fila 1 vacia por defecto porque no siempre va a ser obligatoria
def mostrar_texto(fila1, fila2=""):
    lcd.clear()
    # Sleep para que le de tiempo a la pantalla a borrar
    sleep(0.05)   

    # Empieza a escribir en la primera posición, fila 0 columna 0
    lcd.setCursor(0, 0)
    # Corta el texto en el caracter 16
    lcd.write(fila1[:16])

    # Lo mismo pero en la fila 1
    lcd.setCursor(1, 0)
    lcd.write(fila2[:16])

# Muestra el mensaje de sed, pita y lo quita pasados unos segundos
def aviso_sed(segundos=5):
    mostrar_texto(FILA1HUMEDAD, FILA2HUMEDAD)
    pitido()
    sleep(10)
    lcd.clear()

# Función principal
if __name__ == "__main__":
    try:
        mostrar_texto(FILA1, FILA2)




        # Mantiene el programa vivo
        while True:
            sleep(1)

    # Si se detiene forzosamente, deja la pantalla limpia
    except KeyboardInterrupt:
        lcd.clear()