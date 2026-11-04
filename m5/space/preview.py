"""Vista previa del frontend de Amparo, SIN cargar modelos ni Groq.

Para iterar el diseño rapido: levanta la misma interfaz de `app.py`, pero en
vez de llamar al VLM y a M3 usa respuestas de ejemplo ya armadas, con la
estructura `res` real que produce `Amparo.responder`. Asi lo que se ve es el
HTML real que genera `despliegue.presentar()` / `formatear_para_usuario()`,
con el CSS y el layout de verdad, pero arranca en segundos y sin clave.

    python m5/space/preview.py      ->  http://localhost:7860

NO es parte del Space: `m5/space/README.md` solo sube `app.py`,
`requirements.txt` y su `README.md`. Este archivo no toca ninguna logica
evaluada (ni la decision de M3 ni `formatear()` de M4): solo arma casos de
muestra y reusa la capa de presentacion de `despliegue.py`.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = next((p for p in [AQUI, *AQUI.parents]
             if (p / "amparo" / "nucleo" / "schema.py").exists()), AQUI)
sys.path.insert(0, str(RAIZ))

import gradio as gr                                        # noqa: E402

from amparo import despliegue as dsp                       # noqa: E402


# ---------------------------------------------------------------------------
# Casos de ejemplo: la estructura `res` que devuelve `Amparo.responder`, a
# mano, para no cargar nada. Cubren las tres formas que la UI tiene que pintar
# bien: con mecanismo + documento, abstencion, y via ordinaria.
# ---------------------------------------------------------------------------
_TUTELA = {
    "respuesta": (
        "mecanismo: tutela\n"
        "derecho: salud\n"
        "accionado: EPS Sanitas\n"
        "pretension: autorizar la cirugía de cadera ordenada por el ortopedista\n"
        "fundamento: art. 86 CP; art. 6 Decreto 2591 de 1991"
    ),
    "por_que": {
        "regla": "6.1 · no hay otro medio judicial eficaz",
        "mecanismo_del_motor": "tutela",
        "se_abstuvo": False,
        "motivo_abstencion": "",
        "hechos": ["afectacion_individual", "perjuicio_irremediable",
                   "sujeto_especial_proteccion"],
        "normas_consultadas": ["art. 86 CP", "art. 6 · Decreto 2591 de 1991"],
        "herramientas": [],
    },
    "leido": {
        "rotulo": "Lo que se leyó del documento",
        "campos": {"tipo_documento": "respuesta de EPS", "entidad": "EPS Sanitas",
                   "fecha": "2026-10-14", "plazo_dias": None,
                   "pretension_visible": "niega la autorización de la cirugía"},
        "crudo": "",
        "advertencias": [],
    },
    "segundos": {"lectura del documento": 3.7, "decisión (M3)": 5.9},
}

_ABSTENCION = {
    "respuesta": (
        "mecanismo: no_determinable\n"
        "razon: La consulta no describe una situación concreta con un accionado "
        "y una orden que un juez pudiera dar."
    ),
    "por_que": {
        "regla": None, "mecanismo_del_motor": None, "se_abstuvo": True,
        "motivo_abstencion": "no se describe una situación propia del solicitante "
                             "con alguien a quien dirigir la acción",
        "hechos": [], "normas_consultadas": [], "herramientas": [],
    },
    "leido": None,
    "segundos": {"lectura del documento": None, "decisión (M3)": 2.1},
}

_VIA_ORDINARIA = {
    "respuesta": (
        "mecanismo: via_ordinaria\n"
        "derecho: no_determinado\n"
        "accionado: arrendatario\n"
        "pretension: cobrar los cánones de arrendamiento adeudados\n"
        "razon: existe un proceso judicial ordinario idóneo para el cobro\n"
        "fundamento: art. 6.1 Decreto 2591 de 1991"
    ),
    "por_que": {
        "regla": "6.1 · existe otro medio judicial eficaz",
        "mecanismo_del_motor": "via_ordinaria",
        "se_abstuvo": False, "motivo_abstencion": "",
        "hechos": ["otro_medio_judicial"],
        "normas_consultadas": ["art. 6 · Decreto 2591 de 1991"],
        "herramientas": [],
    },
    "leido": None,
    "segundos": {"lectura del documento": None, "decisión (M3)": 4.3},
}

EJEMPLOS = {
    "⚖️  Tutela (salud, con documento)": _TUTELA,
    "🤔  Abstención (no es un caso)": _ABSTENCION,
    "📄  Vía ordinaria (cobro)": _VIA_ORDINARIA,
}

# El "mensaje del usuario" que acompaña a cada caso, para la burbuja de chat.
PREGUNTAS = {
    "⚖️  Tutela (salud, con documento)":
        "Tengo 68 años y mi EPS me negó la cirugía de cadera que ordenó el ortopedista. "
        "Adjunto la respuesta de la EPS. ¿Qué mecanismo me corresponde?",
    "🤔  Abstención (no es un caso)":
        "¿En qué debería invertir mis ahorros este año?",
    "📄  Vía ordinaria (cobro)":
        "Un arrendatario me debe varios meses de arriendo y no me quiere pagar. "
        "¿Puedo poner una tutela?",
}


def responder(etiqueta, historial):
    """Simula enviar el caso: agrega la burbuja del usuario y la respuesta de
    Amparo al chat. El markdown de la respuesta lo arma la capa de presentacion
    REAL de `despliegue.py`, sin generador de Groq (plantilla fija)."""
    res = EJEMPLOS[etiqueta]
    reg = {"ts": time.time(), "ok": True, "latencia_ms": 0}
    md = dsp.presentar(res, None, reg, generar=None)
    historial = (historial or []) + [
        {"role": "user", "content": PREGUNTAS[etiqueta]},
        {"role": "assistant", "content": md},
    ]
    return historial


def limpiar():
    return []


VERSION = dsp.version(RAIZ)
AVATAR = str(AQUI / "avatar.svg") if (AQUI / "avatar.svg").exists() else None

with gr.Blocks(title="Amparo · vista previa") as demo:
    with gr.Column(elem_id="amparo-chat-wrap"):
        gr.HTML(dsp.encabezado_html(VERSION))
        gr.HTML(dsp.AVISO_HTML)
        chat = gr.Chatbot(
            elem_id="amparo-chat", label="", show_label=False, height=520,
            avatar_images=(None, AVATAR), watermark="VISTA PREVIA · respuestas de ejemplo")
        with gr.Row(elem_id="amparo-barra"):
            caso = gr.Dropdown(list(EJEMPLOS), value=list(EJEMPLOS)[0],
                               label="", show_label=False, container=False, scale=5)
            enviar = gr.Button("Enviar ↑", variant="primary", scale=0, min_width=110)
        with gr.Row():
            nuevo = gr.Button("🗑 Limpiar conversación", variant="secondary", size="sm")
    enviar.click(responder, [caso, chat], chat)
    nuevo.click(limpiar, None, chat)

if __name__ == "__main__":
    demo.launch(theme=dsp.tema(), css=dsp.CSS, server_name="127.0.0.1")
