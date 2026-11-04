"""Amparo · la app de la demo (M5 · S15, Parte B).

Es el `app.py` del lab de la profe con nuestro sistema dentro: la logica vive
en `amparo/despliegue.py` y `amparo/multimodal/sistema_visual.py` (el mismo
codigo que se evaluo en M4). Aqui solo esta la interfaz.

La misma app corre en los lugares de la tabla de despliegue de la profe:

  - **Hugging Face Space** (vitrina permanente). La tabla sugeria CPU Basic,
    pero desde julio de 2026 las cuentas gratis nuevas solo pueden crear
    Spaces con **ZeroGPU** (ver m5/README.md). En ZeroGPU la GPU existe solo
    dentro de las funciones con `@spaces.GPU`: por eso la consulta va
    decorada, los modelos se cargan al arrancar y el VLM va en fp16.
  - **Kaggle T4** (demo en vivo): `AMPARO_SHARE=1` da el enlace publico de
    Gradio y, con GPU, el VLM corre en fp16 (int4 no cumplio su contrato).
  - En CPU tambien funciona (`AMPARO_VLM` 'auto' limita la resolucion; 'off'
    la deja solo con texto).

Secretos (en *Settings -> Variables and secrets* del Space, nunca aqui):
`GROQ_API_KEY` (obligatoria) y `WANDB_API_KEY` (opcional).
Variables: `AMPARO_REF` (rama o tag del repo, defecto `m5`), `AMPARO_VLM`,
`AMPARO_MAX_PIXELS`, `AMPARO_SHARE`, `AMPARO_ZEROGPU` (1 en un Space ZeroGPU),
`AMPARO_GPU_S` (segundos de GPU por consulta en ZeroGPU, defecto 90).
"""
# `spaces` va primero: en ZeroGPU tiene que importarse antes que torch.
try:
    import spaces
except ImportError:                    # fuera de Hugging Face no existe
    spaces = None
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

T0 = time.time()

# ---- el codigo de Amparo: el repo en el tag pedido -------------------------
# Dentro del repo (local o Kaggle con el repo clonado) usa esa copia; en el
# Space clona el repo publico en `AMPARO_REF`. Asi la version que corre es un
# tag de git, visible en la pestaña Estado.
REPO = os.environ.get("AMPARO_REPO", "https://github.com/TomasPosada0626/Amparo.git")
REF = os.environ.get("AMPARO_REF", "m5")
AQUI = Path(__file__).resolve().parent
RAIZ = next((p for p in [AQUI, *AQUI.parents] if (p / "amparo" / "nucleo" / "schema.py").exists()),
            None)
if RAIZ is None:
    RAIZ = AQUI / "Amparo"
    if not RAIZ.is_dir():
        subprocess.run(["git", "clone", "-q", "--depth", "1", "-b", REF, REPO, str(RAIZ)],
                       check=True)
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("AMPARO_RAIZ", str(RAIZ))

import gradio as gr                                       # noqa: E402

from amparo import despliegue as dsp                     # noqa: E402

VERSION = dsp.version(RAIZ)
CFG = dsp.config_desde_entorno()

# ---- logging estructurado: una linea JSON por consulta (el lab) ------------
RUTA_LOG = Path(os.environ.get("AMPARO_LOG", "peticiones.jsonl"))
logging.basicConfig(level=logging.INFO, format="%(message)s",
                    handlers=[logging.FileHandler(RUTA_LOG), logging.StreamHandler()])
log = logging.getLogger("amparo")

# ---- W&B, si hay clave (una linea al arrancar, como en el lab) -------------
wandb = None
if os.environ.get("WANDB_API_KEY"):
    try:
        import wandb as _wandb
        _wandb.init(project=os.environ.get("WANDB_PROJECT", "amparo-m5"),
                    name=("zerogpu" if CFG.get("zerogpu") else "gpu" if CFG["cuda"] else "cpu")
                    + f"-{VERSION['describe']}",
                    config={**CFG, **VERSION})
        wandb = _wandb
    except Exception as ex:                                # noqa: BLE001
        print("W&B no arranco:", ex)

# ---- el sistema se carga UNA vez, aqui arriba ------------------------------
print("cargando Amparo:", json.dumps(CFG))
AMPARO, ESTADO = dsp.armar_amparo(CFG)
print("Amparo listo:", json.dumps(ESTADO))

# La capa de redaccion de M1 (medida en M1), con el mismo generador de Groq
# que se midio. Sin clave o si falla, la respuesta usa la plantilla fija.
GENERAR = None
if os.environ.get("GROQ_API_KEY"):
    try:
        import groq
        from amparo.sistemas import sistema as _sistema
        GENERAR = _sistema.generador_groq(groq.Groq(api_key=os.environ["GROQ_API_KEY"]),
                                          cache_path=str(dsp.CARPETA_CACHE / "redaccion.json"))
    except Exception as ex:                                # noqa: BLE001
        print("sin capa de redaccion (se usa la plantilla):", ex)

IMG = RAIZ / "m4" / "eval_set" / "imagenes"
EJEMPLOS = [
    ["Me llegó esta respuesta de mi EPS. Tengo 68 años y el ortopedista me ordenó esa cirugía "
     "porque ya casi no puedo caminar. ¿Qué mecanismo constitucional me corresponde?",
     str(IMG / "doc01_respuesta_eps.png")],
    ["Somos cuatro veredas que tomamos agua de esa quebrada y la curtiembre sigue vertiendo. "
     "Esta es la respuesta que nos dio la corporación ambiental. ¿Qué mecanismo constitucional "
     "nos corresponde?", str(IMG / "doc04_respuesta_car.png")],
    ["Es una foto de una notificación que me dejaron debajo de la puerta y se mojó. ¿De qué "
     "fecha es y en cuántos días se me vence el plazo?", str(IMG / "doc06_notificacion_borrosa.jpg")],
]


def _consultar(pregunta, imagen):
    """La decision (VLM + M3). En ZeroGPU es la que pide la GPU, y corre en
    otro proceso: por eso recarga de disco la cache de M3. La redaccion y el
    registro (log y W&B) van afuera, en el proceso principal: la redaccion es
    una llamada a Groq y no necesita GPU."""
    dsp.recargar_caches(getattr(AMPARO, "agente", None))
    return dsp.consultar_res(AMPARO, pregunta, imagen, ver_version=VERSION["describe"] or "")


if spaces is not None and CFG.get("zerogpu"):
    _consultar = spaces.GPU(duration=int(os.environ.get("AMPARO_GPU_S", "90")))(_consultar)


def responder(pregunta, imagen):
    if not (pregunta or "").strip():
        yield "_Escribe tu pregunta._"
        return
    if imagen is not None and CFG["vlm"] != "off":
        yield "⏳ **Leyendo el documento…**" + ("" if CFG["cuda"] else " (en CPU puede tardar un poco)")
    else:
        yield "⏳ **Analizando tu caso…**"
    res, md_error, reg = _consultar(pregunta, imagen)
    if res is not None:
        yield "⏳ **Redactando la respuesta…**"
    md = dsp.presentar(res, md_error, reg, GENERAR)
    dsp.registrar(reg, log=log, wandb_mod=wandb)
    yield md


def estado():
    return dsp.health(ESTADO, T0, RUTA_LOG, VERSION)


AVISO = ("Amparo **orienta**, no reemplaza a un abogado: propone el mecanismo constitucional "
         "(tutela, acción popular, de cumplimiento, hábeas corpus o vía ordinaria) con la regla "
         "del art. 6 del Decreto 2591 que lo decide. Lo leído de la foto es una lectura "
         "automática **no verificada**: revisa el documento original. Los documentos de "
         "ejemplo son sintéticos.")

with gr.Blocks(title="Amparo") as demo:
    gr.Markdown(f"# Amparo · triaje de acciones constitucionales\n{AVISO}\n\n"
                f"<sub>versión `{VERSION['describe']}` · visión `{CFG['vlm']}` · "
                f"{ESTADO.get('hardware', '')}</sub>")
    with gr.Tab("Consulta"):
        with gr.Row():
            with gr.Column():
                q = gr.Textbox(label="Tu pregunta", lines=4,
                               placeholder="Cuéntanos qué pasó y qué quieres lograr.")
                im = gr.Image(type="pil", label="Foto del documento (opcional)")
                boton = gr.Button("Responder", variant="primary")
            with gr.Column():
                out = gr.Markdown()
        gr.Examples(EJEMPLOS, [q, im], label="Casos de la demo")
        boton.click(responder, [q, im], out)
    with gr.Tab("Estado"):
        gr.JSON(value=estado, every=10)                   # el health check, visible

if __name__ == "__main__":
    demo.launch(theme=dsp.tema(), share=CFG["share"], server_name="0.0.0.0")
