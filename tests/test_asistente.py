"""Pruebas del asistente de chat. No necesitan clave ni internet: usan un servidor LLM falso."""

import json
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from web import asistente

PLANTA = {"nombre_planta": "Sunny", "tipo_planta": "Girasol", "descripcion_planta": "En el balcón"}
SENSORES = {"temperatura": 31.5, "humedad": 20.0, "luz": None, "es_de_dia": False, "antiguedad_s": 4}


class ServidorFalso(BaseHTTPRequestHandler):
    """Imita /chat/completions: guarda la petición y responde lo que diga `respuesta`."""

    peticiones = []
    estado = 200
    respuesta = {"choices": [{"message": {"content": " ¡Hola! 🌻 "}}]}

    def do_POST(self):
        cuerpo = self.rfile.read(int(self.headers["Content-Length"]))
        ServidorFalso.peticiones.append(
            {"ruta": self.path, "auth": self.headers.get("Authorization"),
             "agente": self.headers.get("User-Agent"), "json": json.loads(cuerpo)}
        )
        datos = json.dumps(ServidorFalso.respuesta).encode()
        self.send_response(ServidorFalso.estado)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, *args):
        pass


@pytest.fixture
def llm(monkeypatch):
    servidor = HTTPServer(("127.0.0.1", 0), ServidorFalso)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    ServidorFalso.peticiones = []
    ServidorFalso.estado = 200
    monkeypatch.setenv("LLM_BASE_URL", f"http://127.0.0.1:{servidor.server_port}/v1/")
    monkeypatch.setenv("LLM_MODEL", "modelo-de-prueba")
    monkeypatch.setenv("LLM_API_KEY", "clave-de-prueba")
    yield ServidorFalso
    servidor.shutdown()


# ---------- System prompt ----------

def test_prompt_incluye_perfil_y_sensores():
    prompt = asistente.construir_system_prompt(PLANTA, SENSORES, datetime(2026, 11, 23, 21, 5))
    assert "Eres Sunny" in prompt and "Girasol" in prompt and "En el balcón" in prompt
    assert "31.5 °C" in prompt and "20.0 %" in prompt
    assert "Luz: sin datos" in prompt
    assert "Ahora es de noche" in prompt and "21:05" in prompt
    assert "hace 4 s" in prompt


def test_prompt_sin_planta_ni_lecturas():
    vacio = {"temperatura": None, "humedad": None, "luz": None, "es_de_dia": True, "antiguedad_s": None}
    prompt = asistente.construir_system_prompt(None, vacio)
    assert "Eres Plantamigo" in prompt
    assert "sin lecturas todavía" in prompt
    assert prompt.count("sin datos (el sensor no responde)") == 3


# ---------- Historial ----------

def test_historial_se_convierte_al_formato_del_llm():
    historial = asistente.preparar_historial(
        [{"rol": "planta", "texto": "Hola"}, {"rol": "usuario", "texto": "  ¿Qué tal?  "}]
    )
    assert historial == [
        {"role": "assistant", "content": "Hola"},
        {"role": "user", "content": "¿Qué tal?"},
    ]


def test_historial_se_recorta():
    mensajes = [{"rol": "usuario", "texto": "x" * 5000}] * 50
    historial = asistente.preparar_historial(mensajes)
    assert len(historial) == asistente.MAX_MENSAJES
    assert len(historial[-1]["content"]) == asistente.MAX_CARACTERES


@pytest.mark.parametrize("mensajes", [
    None, [], "hola", [{"rol": "usuario"}], [{"rol": "system", "texto": "x"}],
    [{"rol": "usuario", "texto": "   "}], [{"rol": "usuario", "texto": "hola"}, {"rol": "planta", "texto": "hey"}],
])
def test_historial_no_valido(mensajes):
    with pytest.raises(asistente.HistorialNoValido):
        asistente.preparar_historial(mensajes)


# ---------- Llamada al LLM ----------

def test_responder_envia_prompt_y_devuelve_texto(llm):
    texto = asistente.responder([{"rol": "usuario", "texto": "¿Tienes sed?"}], PLANTA, SENSORES)
    assert texto == "¡Hola! 🌻"

    peticion = llm.peticiones[0]
    assert peticion["ruta"] == "/v1/chat/completions"
    assert peticion["auth"] == "Bearer clave-de-prueba"
    assert peticion["agente"] == "Plantamigo/1.0"  # el de urllib lo bloquea Cloudflare (Groq)
    assert peticion["json"]["model"] == "modelo-de-prueba"
    mensajes = peticion["json"]["messages"]
    assert mensajes[0]["role"] == "system" and "20.0 %" in mensajes[0]["content"]
    assert mensajes[1] == {"role": "user", "content": "¿Tienes sed?"}


def test_responder_sin_clave_no_envia_authorization(llm, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY")
    asistente.responder([{"rol": "usuario", "texto": "hola"}], None, SENSORES)
    assert llm.peticiones[0]["auth"] is None


def test_responder_sin_configurar(monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    with pytest.raises(asistente.ErrorAsistente, match="not set up"):
        asistente.responder([{"rol": "usuario", "texto": "hola"}], None, SENSORES)


@pytest.mark.parametrize("estado, mensaje", [
    (401, "key"), (403, "rejected"), (404, "LLM_MODEL"), (429, "Too many"), (500, "error"),
])
def test_responder_errores_http(llm, estado, mensaje):
    llm.estado = estado
    with pytest.raises(asistente.ErrorAsistente, match=mensaje):
        asistente.responder([{"rol": "usuario", "texto": "hola"}], None, SENSORES)


def test_responder_sin_conexion(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:9/v1")
    monkeypatch.setenv("LLM_MODEL", "x")
    with pytest.raises(asistente.ErrorAsistente, match="Could not reach"):
        asistente.responder([{"rol": "usuario", "texto": "hola"}], None, SENSORES)


def test_responder_respuesta_rara(llm, monkeypatch):
    monkeypatch.setattr(llm, "respuesta", {"algo": "inesperado"})
    with pytest.raises(asistente.ErrorAsistente, match="unexpected"):
        asistente.responder([{"rol": "usuario", "texto": "hola"}], None, SENSORES)
