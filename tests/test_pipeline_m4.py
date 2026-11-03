"""Tests de amparo/pipelines/m4_multimodal.py: las etapas del notebook de
evaluacion de M4, encadenadas sobre el paquete.

Los modulos que llama (`sistema_visual`, `corrida_m4`, `scorecard`,
`criterios`, `enchufe`) tienen sus propias pruebas en tests/m4/. Aqui se
prueba el pipeline: que cada etapa llama a lo que debe, escribe donde debe y
deja en el contexto lo que la siguiente necesita.

Sin GPU, sin red y sin modelos: el lector visual, M3 y la carga de imagenes
son dobles. NO se ejecuta de verdad: `LectorVisual()` (baja Qwen2-VL-2B), el
enchufe contra Groq, `cargar` sobre una URL ni la descarga desde Colab.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from amparo.config import RAIZ
from amparo.multimodal import corrida_m4, enchufe, sistema_visual
from amparo.nucleo import schema
from amparo.pipelines import m4_multimodal as m4

sys.path.insert(0, str(RAIZ / "tests"))
from autoprueba_agente import ClienteGuionado, IndiceFalso  # noqa: E402

SALIDA_TUTELA = schema.render_salida({"derecho": "salud", "accionado": "EPS", "mecanismo": "tutela",
                                      "procede": True, "razon": "r", "pretension": "p"})
necesita_results = pytest.mark.skipif(
    not (RAIZ / "results" / "m3_scorecard.csv").exists(),
    reason="results/ de M3 no esta en esta copia del repo")


class LectorFalso:
    dtype, device = "float32", "cpu"

    def __init__(self):
        self.vistas = []

    def ver(self, imagen, instruccion=None):
        self.vistas.append(imagen)
        js = {"tipo_documento": "oficio", "entidad": None, "fecha": None,
              "plazo_dias": 15, "pretension_visible": None}
        return json.dumps(js), js

    def preguntar(self, imagen, pregunta, system=None, max_new_tokens=256):
        return "SI"


class AgenteFalso:
    def __init__(self):
        self.cache_guardada = 0

    def guardar_cache(self):
        self.cache_guardada += 1


class AmparoFalso:
    def __init__(self):
        self.preguntas = []

    def responder_markdown(self, pregunta, imagen=None):
        self.preguntas.append(pregunta)
        return f"**Respuesta** a: {pregunta[:20]}"


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    """Contexto con la carpeta de la corrida en tmp_path y dobles en lugar de
    VLM y M3; `vaciar_caches` cuenta las veces que se pide."""
    vaciados = []
    monkeypatch.setattr(enchufe, "vaciar_caches", lambda agente: vaciados.append(agente))
    c = m4.Contexto(corrida_id="20261103T000000Z", carpeta=tmp_path)
    m4.cargar_lector(c, lector=LectorFalso())
    c.responder_m3 = lambda relato: SALIDA_TUTELA
    c.agente_m3 = AgenteFalso()
    c.vaciados = vaciados
    return c


# --------------------------------------------------------------------------
# preparar, imagenes, lector, ver
# --------------------------------------------------------------------------
def test_preparar_para_sin_clave_y_crea_la_carpeta_de_la_corrida(monkeypatch, tmp_path):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(m4.os, "chdir", lambda p: None)
    monkeypatch.setattr(corrida_m4, "nueva", lambda etiqueta: ("CID", tmp_path / f"CID_{etiqueta}"))
    with pytest.raises(SystemExit, match="GROQ_API_KEY"):
        m4.preparar()
    c = m4.preparar(exigir_clave=False)
    assert (c.corrida_id, c.carpeta.name) == ("CID", "CID_demo")


def test_cargar_lector_expone_ver_y_preguntar_del_mismo_lector(ctx):
    assert ctx.ver.__self__ is ctx.lector and ctx.preguntar.__self__ is ctx.lector


def test_cargar_imagenes_y_probar_ver(ctx):
    m4.cargar_imagenes(ctx, cargar_fn=lambda ruta: f"img:{Path(ruta).name}")
    assert list(ctx.imgs) == list(m4.IMAGENES)
    filas = m4.probar_ver(ctx)
    assert len(filas) == 3 and all(f["js"]["plazo_dias"] == 15 for f in filas)
    assert ctx.lector.vistas == list(ctx.imgs.values())


def test_cargar_normaliza_a_rgb(tmp_path):
    Image = pytest.importorskip("PIL.Image", reason="pillow no esta en este entorno (extra [vlm])")
    p = tmp_path / "doc.png"
    Image.new("L", (4, 4), 128).save(p)
    assert m4.cargar(str(p)).mode == "RGB"


# --------------------------------------------------------------------------
# enchufe: M3 real con dobles, Amparo y manifiesto
# --------------------------------------------------------------------------
class _Transformador:
    def __init__(self):
        self.cache = {}

    def __call__(self, relato):
        return relato


@necesita_results
def test_enchufar_m3_arma_amparo_y_guarda_el_manifiesto(ctx):
    ctx.imgs = {"a": "IMAGEN"}
    cliente = ClienteGuionado([[("buscar_normas", '{"consulta": "derecho a la salud"}')], None])
    md = m4.enchufar_m3(ctx, cliente=cliente, indice=IndiceFalso(), transformador=_Transformador())
    assert isinstance(ctx.amparo, sistema_visual.Amparo) and ctx.amparo.lector is ctx.lector
    assert "Leído del documento" in md                       # la respuesta en tres bloques
    man = json.loads((ctx.carpeta / "corrida_m4.json").read_text(encoding="utf-8"))
    assert man["id"] == ctx.corrida_id and man["vlm"]["modelo"] == sistema_visual.VLM_ID
    assert man["m3"]["brazo"] == enchufe.SISTEMA_M3


# --------------------------------------------------------------------------
# eval set, harness, deltas, resumen, plan B y cierre (de punta a punta)
# --------------------------------------------------------------------------
def test_validar_eval_set_sobre_el_csv_real_del_repo(ctx):
    casos = m4.validar_eval_set(ctx)
    assert len(casos) >= 5 and sum(c["tipo"] == "adversarial" for c in casos) == 1
    assert ctx.casos == casos


@necesita_results
def test_de_punta_a_punta_sobre_el_eval_set_real(ctx):
    m4.validar_eval_set(ctx)
    res = m4.correr_harness(ctx, cargar_fn=lambda ruta: ruta)
    assert (ctx.carpeta / "scorecard_m4.csv").exists() and (ctx.carpeta / "delta_m4.json").exists()
    assert res["sistema_m3"] == enchufe.SISTEMA_M3 and ctx.agente_m3.cache_guardada == 1

    di = m4.delta_imagen(ctx)
    assert (ctx.carpeta / "delta_imagen_m4.json").exists()
    assert di["n"] == sum(c["criterio"] == "exacto" for c in ctx.casos)
    assert ctx.vaciados[0] is ctx.agente_m3                  # la cache se vacia antes del delta

    dr = m4.delta_repetido(ctx, repeticiones=1)
    assert (ctx.carpeta / "delta_imagen_repetido_m4.json").exists() and dr["n_casos"] >= 1

    tabla = m4.resumen(ctx)
    assert list(tabla.columns) == ["id", "criterio", "tipo", "nota", "segundos",
                                   "segundos_ver", "etapa", "lectura_vlm"]
    assert len(tabla) == len(ctx.casos)

    ctx.amparo = AmparoFalso()
    ctx.manifiesto = corrida_m4.manifiesto(ctx.corrida_id)
    ruta_b = m4.plan_b(ctx, cargar_fn=lambda ruta: ruta)
    texto = ruta_b.read_text(encoding="utf-8")
    assert all(f"## {cid} ·" in texto for cid in m4.PLAN_B) and "No es una ejecución en vivo" in texto

    ruta = m4.cerrar(ctx)
    man = json.loads(Path(ruta).read_text(encoding="utf-8"))
    assert set(man["resumen"]) == {"notas_por_criterio", "exacto_aciertos", "latencia_por_caso_s",
                                   "delta_una_pasada", "delta_repetido"}
    assert "scorecard_m4.csv" in man["archivos"]             # el cierre sella lo que hay en la carpeta


def test_descargar_fuera_de_colab_deja_el_zip(ctx):
    (ctx.carpeta / "scorecard_m4.csv").write_text("x")
    zip_ = m4.descargar(ctx)
    assert Path(zip_).exists() and zip_.endswith(".zip")


# --------------------------------------------------------------------------
# los notebooks de M4 siguen anclados a demo-final
# --------------------------------------------------------------------------
@pytest.mark.parametrize("nombre", ["M4_pipeline.ipynb", "M4_demo.ipynb"])
def test_los_notebooks_de_m4_clonan_demo_final(nombre):
    """Por la revision docente (H3) los notebooks reproducen lo evaluado: clonan
    el tag fijo `demo-final`, no `main`. Este pipeline no los reemplaza."""
    nb = json.loads((RAIZ / "m4" / "pipeline" / nombre).read_text(encoding="utf-8"))
    codigo = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    assert "'demo-final'" in codigo
