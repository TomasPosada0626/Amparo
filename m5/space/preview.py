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


def responder(etiqueta):
    """Arma el markdown con la capa de presentacion REAL de `despliegue.py`,
    sin generador de Groq (usa la plantilla fija, como cuando no hay clave)."""
    res = EJEMPLOS[etiqueta]
    reg = {"ts": time.time(), "ok": True, "latencia_ms": 0}
    return dsp.presentar(res, None, reg, generar=None)


VERSION = dsp.version(RAIZ)

with gr.Blocks(title="Amparo · vista previa") as demo:
    gr.HTML(dsp.encabezado_html(VERSION))
    gr.HTML(dsp.AVISO_HTML)
    gr.Markdown("<sub>**VISTA PREVIA** del frontend · respuestas de ejemplo, sin modelos "
                "ni Groq.</sub>")
    with gr.Row():
        with gr.Column():
            caso = gr.Radio(list(EJEMPLOS), value=list(EJEMPLOS)[0],
                            label="Caso de ejemplo")
            boton = gr.Button("Ver respuesta", variant="primary")
        with gr.Column():
            out = gr.Markdown()
    boton.click(responder, caso, out)
    demo.load(responder, caso, out)

if __name__ == "__main__":
    demo.launch(theme=dsp.tema(), css=dsp.CSS, server_name="127.0.0.1")
