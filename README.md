# Plantamigo

### Dispone de diferentes funcionalidades 
* Incluye diferentes APIs para poder obtener informacion del entorno del usuario
* Una pantalla para poder ver las reacciones de la planta
* Un grafico en el que se puede ver todos los datos referentes a la planta

## Base de datos (PostgreSQL)

El esquema está en `web/basedatos/schema.sql` y el acceso desde Python en `web/basedatos/`.
Guía completa de uso: [web/basedatos/README.md](web/basedatos/README.md).

Tablas: `usuarios`, `plantas`, `canciones`, `usuarios_canciones` (canciones desbloqueadas por cada usuario) y `datos_planta` (lecturas de los sensores).

Puesta en marcha (desde la raíz del repositorio):

1. Instalar dependencias: `pip install -r requirements.txt`
2. Crear usuario `plantamigo`, base de datos `plantamigodb` y tablas (pide la contraseña de `postgres`):
   `python web/basedatos/crear_bd.py`
   - `--prueba`: carga también datos de ejemplo.
   - `--reiniciar`: borra la base de datos y la crea de nuevo.
   - `--contrasena X`: contraseña del usuario `plantamigo` (por defecto `plantamigo123`, cámbiala fuera de pruebas locales).
3. Para la aplicación, definir la conexión en la variable de entorno `DATABASE_URL`:
   `postgresql://plantamigo:plantamigo123@localhost:5432/plantamigodb`

## Chat con la planta (LLM)

La página **Chat** (`/chat`) permite hablar con la planta. En cada mensaje,
`web/asistente.py` construye el *system prompt* con el perfil de la planta
(tabla `plantas`, según `ID_PLANTA`) y las lecturas actuales de los sensores,
y lo envía a un LLM.

Funciona con cualquier proveedor compatible con la API de OpenAI
(`/chat/completions`). Se configura con variables de entorno, sin tocar código:

| Variable | Obligatoria | Qué es |
|---|---|---|
| `LLM_BASE_URL` | Sí | URL base de la API del proveedor. |
| `LLM_MODEL` | Sí | Nombre del modelo (consúltalo en la web del proveedor, cambian a menudo). |
| `LLM_API_KEY` | Según el proveedor | Clave de la API. No hace falta para Ollama. |

| Proveedor | `LLM_BASE_URL` |
|---|---|
| Google Gemini (tiene capa gratuita) | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| Groq | `https://api.groq.com/openai/v1` |
| OpenAI | `https://api.openai.com/v1` |
| Ollama (local, gratis) | `http://localhost:11434/v1` |

Ejemplo (PowerShell; en Linux, `export VAR=valor`):

```powershell
$env:LLM_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
$env:LLM_MODEL="<nombre-del-modelo>"
$env:LLM_API_KEY="<tu-clave>"
python web/app_local.py
```

- Sin `LLM_BASE_URL` o `LLM_MODEL`, la web funciona igual y el chat muestra un aviso.
- Sin `ID_PLANTA` o sin base de datos, el chat usa un perfil genérico ("Plantamigo").
- Las conversaciones no se guardan: el historial vive solo en el navegador y se pierde al recargar.
  Los mensajes sí se envían al proveedor del LLM.
- No subáis la clave al repositorio.

## Probar en local (sin Raspberry Pi)

`python web/app_local.py` arranca la web con los sensores y el buzzer simulados
(no hace falta gpiozero, smbus2 ni grove.py). Para el calendario, define `DATABASE_URL` igual que arriba.

Pruebas (usan una base de datos desechable, se borran sus datos):
`TEST_DATABASE_URL=postgresql://... pytest tests`
