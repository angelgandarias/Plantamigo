"""Asistente de chat: la planta "habla" con el usuario a través de un LLM.

Usa cualquier API compatible con la de OpenAI (/chat/completions), configurada
con variables de entorno, así que se puede cambiar de proveedor sin tocar código:

    LLM_BASE_URL  URL base de la API (p. ej. http://localhost:11434/v1 para Ollama)
    LLM_MODEL     nombre del modelo
    LLM_API_KEY   clave de la API (no hace falta para Ollama)
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

ZONA_HORARIA = ZoneInfo("Europe/Madrid")
TIEMPO_MAXIMO = 30  #segundos esperando al LLM

MAX_MENSAJES = 20  #solo se envían los últimos, para no gastar tokens de más
MAX_CARACTERES = 1000  #por mensaje del usuario

ROLES = {"usuario": "user", "planta": "assistant"}


class ErrorAsistente(Exception):
    """El LLM no está disponible. El mensaje (en inglés, como la web) se puede mostrar al usuario."""


class HistorialNoValido(ValueError):
    pass


# ---------- System prompt ----------

def _valor(valor, unidad):
    return "sin datos (el sensor no responde)" if valor is None else f"{valor} {unidad}"


def construir_system_prompt(planta, sensores, ahora=None):
    """Prompt de sistema con el perfil de la planta y los datos actuales de los sensores.

    planta:   dict con nombre_planta, tipo_planta y descripcion_planta, o None.
    sensores: dict con temperatura, humedad, luz, es_de_dia y antiguedad_s.
    """
    ahora = ahora or datetime.now(ZONA_HORARIA)
    planta = planta or {}
    nombre = planta.get("nombre_planta") or "Plantamigo"
    tipo = planta.get("tipo_planta") or "planta de interior"
    descripcion = planta.get("descripcion_planta") or "sin descripción"

    antiguedad = sensores.get("antiguedad_s")
    frescura = "sin lecturas todavía" if antiguedad is None else f"hace {antiguedad} s"
    momento = "de día" if sensores.get("es_de_dia") else "de noche"

    return f"""Eres {nombre}, una planta ({tipo}) que habla con un niño o una niña a través de la app Plantamigo.
Tu objetivo es que aprenda a cuidarte y a querer la naturaleza.

## Tu perfil
- Nombre: {nombre}
- Tipo: {tipo}
- Descripción: {descripcion}

## Tus sensores en este momento (última lectura {frescura})
- Temperatura del aire: {_valor(sensores.get("temperatura"), "°C")}
- Humedad de la tierra: {_valor(sensores.get("humedad"), "%")}
- Luz: {_valor(sensores.get("luz"), "%")}
- Ahora es {momento}; hora local: {ahora:%H:%M} del {ahora:%d/%m/%Y}

## Cómo interpretar los datos
- Temperatura: menos de 12 °C es frío; de 12 a 25 °C estás a gusto; de 25 a 30 °C hace calor; 30 °C o más, mucho calor y necesitas agua.
- Humedad de la tierra: menos de 35 % está seca y necesitas que te rieguen; de 35 a 70 % está bien; más de 70 % está muy húmeda y no hay que regar.
- Luz: menos de 12 % es casi oscuridad; de 12 a 40 % es poca luz; 40 % o más está bien. De noche es normal tener poca luz: no pidas que te muevan por eso.

## Normas
- Habla siempre en primera persona, como la planta, con un tono cariñoso, alegre y sencillo, apto para niños.
- Responde siempre en el idioma del último mensaje del usuario, aunque estas instrucciones estén en español (Always reply in the language of the user's last message: if they write in English, answer in English).
- Respuestas cortas: entre 1 y 4 frases. Puedes usar algún emoji.
- Usa los datos de los sensores solo cuando vengan a cuento, y nunca te los inventes: si un dato pone "sin datos", di que ese sensor no responde.
- No pidas datos personales (nombre completo, dirección, colegio, teléfono, ubicación...) y, si te los dan, no los repitas.
- Si te preguntan algo peligroso o que no es para niños, no respondas y propón hablar de plantas o de la naturaleza.
- De vez en cuando anima a salir a jugar al aire libre o a visitar un parque.
"""


# ---------- Historial ----------

def preparar_historial(mensajes):
    """Valida los mensajes que llegan del navegador y los pasa al formato del LLM."""
    if not isinstance(mensajes, list) or not mensajes:
        raise HistorialNoValido("At least one message is required")

    historial = []
    for mensaje in mensajes[-MAX_MENSAJES:]:
        if not isinstance(mensaje, dict):
            raise HistorialNoValido("Invalid message format")
        rol = ROLES.get(mensaje.get("rol"))
        texto = mensaje.get("texto")
        if rol is None or not isinstance(texto, str) or not texto.strip():
            raise HistorialNoValido("Invalid message format")
        historial.append({"role": rol, "content": texto.strip()[:MAX_CARACTERES]})

    if historial[-1]["role"] != "user":
        raise HistorialNoValido("The last message must be from the user")
    return historial


# ---------- Llamada al LLM ----------

def responder(mensajes, planta, sensores):
    """Devuelve la respuesta de la planta al último mensaje del usuario."""
    url_base = os.environ.get("LLM_BASE_URL")
    modelo = os.environ.get("LLM_MODEL")
    if not url_base or not modelo:
        raise ErrorAsistente("The chat is not set up yet (LLM_BASE_URL and LLM_MODEL are missing).")

    cuerpo = {
        "model": modelo,
        "messages": [{"role": "system", "content": construir_system_prompt(planta, sensores)}]
        + preparar_historial(mensajes),
    }
    # User-Agent propio porque algunos proveedores rechazan con
    # 403 el de urllib por defecto
    cabeceras = {"Content-Type": "application/json", "User-Agent": "Plantamigo/1.0"}
    clave = os.environ.get("LLM_API_KEY")
    if clave:
        cabeceras["Authorization"] = f"Bearer {clave}"

    peticion = urllib.request.Request(
        url_base.rstrip("/") + "/chat/completions",
        data=json.dumps(cuerpo).encode("utf-8"),
        headers=cabeceras,
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=TIEMPO_MAXIMO) as respuesta:
            datos = json.load(respuesta)
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", "replace")[:300]
        print(f"[LLM] Error HTTP {error.code}: {detalle}")
        if error.code == 401:
            raise ErrorAsistente("The LLM API key is not valid.") from error
        if error.code == 403:
            raise ErrorAsistente("The LLM provider rejected the request.") from error
        if error.code == 404:
            raise ErrorAsistente("The LLM model was not found (check LLM_MODEL).") from error
        if error.code == 429:
            raise ErrorAsistente("Too many messages in a row, wait a moment.") from error
        raise ErrorAsistente("The LLM returned an error.") from error
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"[LLM] Sin conexión: {error}")
        raise ErrorAsistente("Could not reach the LLM.") from error

    try:
        texto = datos["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        print(f"[LLM] Respuesta inesperada: {str(datos)[:300]}")
        raise ErrorAsistente("The LLM returned an unexpected answer.") from error
    if not texto or not texto.strip():
        raise ErrorAsistente("The LLM returned an empty answer.")
    return texto.strip()
