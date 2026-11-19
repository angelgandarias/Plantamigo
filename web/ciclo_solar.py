"""Día y noche según la posición del sol (librería astral).

La ubicación se pasa siempre como parámetro: hoy todos los usuarios usan
UBICACION_PREDETERMINADA (Bilbao), pero si algún día cada usuario/planta tiene
su propia ubicación basta con crear otro LocationInfo y pasarlo a es_de_dia().
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from astral import LocationInfo
from astral.sun import elevation, sun

UBICACION_PREDETERMINADA = LocationInfo(
    name="Bilbao",
    region="Spain",
    timezone="Europe/Madrid",
    latitude=43.2630,
    longitude=-2.9350,
)


def ubicacion(nombre, region, zona_horaria, latitud, longitud):
    """Crea una ubicación (p. ej. a partir de los datos de un perfil de usuario)."""
    return LocationInfo(nombre, region, zona_horaria, latitud, longitud)


def es_de_dia(ubicacion=UBICACION_PREDETERMINADA, momento=None):
    """True si `momento` (por defecto, ahora) está entre la salida y la puesta del sol."""
    zona = ZoneInfo(ubicacion.timezone)
    momento = datetime.now(zona) if momento is None else momento.astimezone(zona)
    try:
        s = sun(ubicacion.observer, date=momento.date(), tzinfo=zona)
        return s["sunrise"] <= momento < s["sunset"]
    except ValueError:
        # Cerca de los polos el sol puede no salir/ponerse en todo el día:
        # decidimos según si está por encima del horizonte.
        return elevation(ubicacion.observer, momento) > 0
