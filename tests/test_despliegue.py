"""Tests de M5 · S15 · Parte B: amparo/despliegue.py y m5/space/app.py.

Sin GPU, sin red y sin modelos: el VLM, M3 (Groq) y el codificador del
indice son dobles. NO se ejecuta de verdad: `armar_amparo` con los modelos
reales, `precalcular_indice` con e5 ni el Space. Eso corre en Colab/Kaggle/HF.
"""
from __future__ import annotations

import importlib.util
import json
import logging

import numpy as np
import pytest

from amparo import despliegue as dsp
from amparo.config import RAIZ

SALIDA = ("Derecho: salud (art. 49 CP)\nAccionado: EPS\nMecanismo: acción de tutela\n"
          "Procedencia: sí — r\nPretensión: p")


# --------------------------------------------------------------------------
# configuracion
# --------------------------------------------------------------------------
@pytest.mark.parametrize("env, cuda, esperado", [
    ({}, True, ("fp16", None)),            # int4 no cumplio el contrato de S15
    ({"AMPARO_VLM": "int4"}, True, ("int4", None)),
    ({}, False, ("cpu", dsp.MAX_PIXELS_CPU)),
    ({"AMPARO_VLM": "int4"}, False, ("cpu", dsp.MAX_PIXELS_CPU)),   # sin GPU no hay int4
    ({"AMPARO_VLM": "off"}, False, ("off", None)),
    ({"AMPARO_VLM": "fp16"}, True, ("fp16", None)),
    ({"AMPARO_MAX_PIXELS": "100352"}, False, ("cpu", 100352)),
])
def test_config_desde_entorno(env, cuda, esperado):
    c = dsp.config_desde_entorno(env, cuda=cuda)
    assert (c["vlm"], c["max_pixels"]) == esperado


def test_config_rechaza_un_vlm_desconocido():
    with pytest.raises(ValueError):
        dsp.config_desde_entorno({"AMPARO_VLM": "int2"}, cuda=True)


def test_share_solo_con_la_variable():
    assert not dsp.config_desde_entorno({}, cuda=False)["share"]
    assert dsp.config_desde_entorno({"AMPARO_SHARE": "1"}, cuda=False)["share"]


# --------------------------------------------------------------------------
# indice precalculado
# --------------------------------------------------------------------------
class _Encoder:
    def __init__(self):
        self.llamadas = 0

    def encode(self, textos, **kw):
        self.llamadas += 1
        return np.ones((len(textos), 4), dtype="float32")


@pytest.fixture
def encoder_falso(monkeypatch):
    from amparo.rag import recuperacion as rag
    enc = _Encoder()
    monkeypatch.setattr(rag.Indice, "_encoder", lambda self: enc)
    return enc


CHUNKS = [{"id": f"c{i}", "texto": f"articulo {i} de la ley", "norma": "Ley 1",
           "articulo": f"art. {i}", "titulo": "t"}
          for i in range(5)]


def test_indice_precalculado_se_carga_sin_codificar_el_corpus(tmp_path, encoder_falso):
    ruta = dsp.precalcular_indice(tmp_path / "i.npz", chunks=CHUNKS)
    antes = encoder_falso.llamadas
    ind, origen = dsp.cargar_indice(ruta, chunks=CHUNKS)
    assert origen == "precalculado" and encoder_falso.llamadas == antes
    assert ind._emb.shape == (5, 4)


def test_indice_de_otro_corpus_se_reconstruye(tmp_path, encoder_falso):
    ruta = dsp.precalcular_indice(tmp_path / "i.npz", chunks=CHUNKS)
    otro = CHUNKS[:4] + [{**CHUNKS[4], "texto": "cambio el texto"}]
    _ind, origen = dsp.cargar_indice(ruta, chunks=otro)
    assert origen == "construido al arrancar"


def test_sin_archivo_se_construye_al_arrancar(tmp_path, encoder_falso):
    _ind, origen = dsp.cargar_indice(tmp_path / "no_existe.npz", chunks=CHUNKS)
    assert origen == "construido al arrancar"


# --------------------------------------------------------------------------
# una consulta
# --------------------------------------------------------------------------
class _Agente:
    def __init__(self):
        self.fallos_extraccion, self.guardadas = [], 0
        self.trazas = [{"regla": "tutela", "mecanismo_del_motor": "tutela", "hechos": {}}]

    def guardar_cache(self):
        self.guardadas += 1


class _Amparo:
    def __init__(self, falla=None, falla_dentro=None):
        self.agente, self.falla, self.falla_dentro = _Agente(), falla, falla_dentro

    def responder(self, pregunta, imagen=None):
        if self.falla:
            raise self.falla
        if self.falla_dentro:                      # como Agente._hechos: no lanza
            self.agente.fallos_extraccion.append({"error": self.falla_dentro})
        return {"respuesta": SALIDA,
                "por_que": {"regla": "tutela", "se_abstuvo": False, "hechos": [],
                            "normas_consultadas": [], "mecanismo_del_motor": "tutela",
                            "motivo_abstencion": "", "herramientas": []},
                "leido": None, "segundos": {"lectura del documento": None, "decisión (M3)": 1.2}}


def test_consulta_normal_registra_y_guarda_la_cache():
    a = _Amparo()
    md, reg = dsp.consultar(a, "Mi EPS no me da la cirugía. Cédula 1036123456", ver_version="m5")
    assert "acción de tutela" in md and reg["ok"]
    assert reg["mecanismo"] == "tutela" and reg["m3_ms"] == 1200
    assert "[num]" in reg["pregunta"] and "1036123456" not in reg["pregunta"]
    assert a.agente.guardadas == 1


def test_si_groq_falla_por_dentro_no_se_muestra_la_tutela():
    """El agente se traga el error y el motor diria tutela: la app lo detecta."""
    md, reg = dsp.consultar(_Amparo(falla_dentro="RateLimitError"), "pregunta")
    assert md == dsp.MENSAJE_API and not reg["ok"] and "tutela" not in md
    assert reg["error"].startswith("api")


def test_si_groq_no_responde_mensaje_amable():
    class APIConnectionError(Exception):
        pass
    md, reg = dsp.consultar(_Amparo(falla=APIConnectionError("Connection error to groq")), "p")
    assert md == dsp.MENSAJE_API and not reg["ok"]


def test_sin_vision_lo_dice():
    a = _Amparo(falla=dsp.SinVision("Esta versión de Amparo no lee fotos"))
    md, reg = dsp.consultar(a, "p", imagen=object())
    assert "no lee fotos" in md and reg["error"] == "sin_vision" and reg["ruta"] == "con_imagen"


def test_registrar_escribe_una_linea_json_y_alimenta_wandb():
    class _W:
        run = True
        logs: list = []

        @classmethod
        def log(cls, d):
            cls.logs.append(d)
    _md, reg = dsp.consultar(_Amparo(), "p")
    linea = dsp.registrar(reg, log=logging.getLogger("t"), wandb_mod=_W)
    assert json.loads(linea)["ok"] is True
    assert _W.logs[0]["ok"] == 1 and _W.logs[0]["mecanismo_tutela"] == 1


def test_health_cuenta_las_consultas(tmp_path):
    log = tmp_path / "p.jsonl"
    log.write_text('{"ok": true}\n{"ok": false}\n', encoding="utf-8")
    h = dsp.health({"vlm": "cpu"}, 0, log, {"describe": "m5-demo", "commit": "abc"})
    assert h["consultas"] == 2 and h["consultas_ok"] == 1 and h["version"] == "m5-demo"


# --------------------------------------------------------------------------
# la app, sin modelos
# --------------------------------------------------------------------------
def test_la_app_arma_la_interfaz_y_responde(tmp_path, monkeypatch):
    pytest.importorskip("gradio")
    monkeypatch.setenv("AMPARO_LOG", str(tmp_path / "p.jsonl"))
    monkeypatch.setenv("AMPARO_VLM", "off")
    monkeypatch.delenv("WANDB_API_KEY", raising=False)
    monkeypatch.setattr(dsp, "armar_amparo", lambda cfg, **kw: (_Amparo(), {"vlm": cfg["vlm"]}))
    spec = importlib.util.spec_from_file_location("app_amparo", RAIZ / "m5" / "space" / "app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    pasos = list(app.responder("Mi EPS no me autoriza la cirugía", None))
    assert pasos[0].startswith("⏳") and "acción de tutela" in pasos[-1]
    assert app.estado()["vlm"] == "off"
    assert all(p.exists() for _q, p in [(e[0], __import__("pathlib").Path(e[1])) for e in app.EJEMPLOS])


# --------------------------------------------------------------------------
# ZeroGPU (el Space)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("env", [{"AMPARO_ZEROGPU": "1"}, {"SPACES_ZERO_GPU": "true"}])
def test_zerogpu_usa_fp16_aunque_torch_no_vea_gpu(env):
    c = dsp.config_desde_entorno(env, cuda=False)
    assert c["zerogpu"] and c["vlm"] == "fp16" and c["max_pixels"] is None


def test_sin_zerogpu_no_se_activa():
    assert not dsp.config_desde_entorno({}, cuda=True)["zerogpu"]


def test_armar_en_zerogpu_precarga_m3_y_carga_el_vlm_sin_device_map(monkeypatch):
    from amparo.multimodal import enchufe
    from amparo.multimodal import sistema_visual
    llamadas = []

    class _Ind:
        def _encoder(self):
            llamadas.append("encoder")

        def _reranker(self):
            llamadas.append("reranker")

    class _Lector:
        def __init__(self, **kw):
            llamadas.append(("lector", kw))

    monkeypatch.setattr(dsp, "cargar_indice", lambda ruta: (_Ind(), "precalculado"))
    monkeypatch.setattr(enchufe, "construir_responder_m3",
                        lambda **kw: (lambda r: "x", type("A", (), {"modelo": "m"})()))
    monkeypatch.setattr(sistema_visual, "LectorVisual", _Lector)
    _amp, estado = dsp.armar_amparo(dsp.config_desde_entorno({"AMPARO_ZEROGPU": "1"}, cuda=False))
    assert llamadas[:2] == ["encoder", "reranker"]
    kw = llamadas[2][1]
    assert kw["device"] == "cuda" and kw["device_map"] is None and kw["cuantizacion"] is None
    assert estado["hardware"] == "ZeroGPU"


def test_recargar_caches_trae_lo_que_otro_proceso_escribio(tmp_path):
    (tmp_path / "agente.json").write_text('{"k1": "v1"}', encoding="utf-8")
    (tmp_path / "consultas.json").write_text('{"r": "q"}', encoding="utf-8")
    tr = type("T", (), {})()
    tr.cache, tr.ruta = {}, tmp_path / "consultas.json"
    ag = type("A", (), {})()
    ag._cache, ag._ruta_cache, ag.transformador = {"k0": "v0"}, tmp_path / "agente.json", tr
    dsp.recargar_caches(ag)
    assert ag._cache == {"k0": "v0", "k1": "v1"} and tr.cache == {"r": "q"}


def test_guardar_caches_guarda_las_dos():
    hecho = []
    tr = type("T", (), {"guardar": lambda self: hecho.append("tr")})()
    ag = type("A", (), {"guardar_cache": lambda self: hecho.append("ag"), "transformador": tr})()
    dsp.guardar_caches(ag)
    assert hecho == ["ag", "tr"]


def test_la_app_en_zerogpu_decora_la_consulta(tmp_path, monkeypatch):
    pytest.importorskip("gradio")
    import sys
    import types
    decorados = []
    falso = types.ModuleType("spaces")

    def GPU(duration=60):
        def deco(f):
            decorados.append((f.__name__, duration))
            return f
        return deco
    falso.GPU = GPU
    monkeypatch.setitem(sys.modules, "spaces", falso)
    monkeypatch.setenv("AMPARO_LOG", str(tmp_path / "p.jsonl"))
    monkeypatch.setenv("AMPARO_ZEROGPU", "1")
    monkeypatch.delenv("WANDB_API_KEY", raising=False)
    monkeypatch.setattr(dsp, "armar_amparo",
                        lambda cfg, **kw: (_Amparo(), {"vlm": cfg["vlm"], "hardware": "ZeroGPU"}))
    spec = importlib.util.spec_from_file_location("app_zerogpu", RAIZ / "m5" / "space" / "app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    assert decorados == [("_consultar", 90)]
    assert "acción de tutela" in list(app.responder("Mi EPS no me autoriza", None))[-1]


# --------------------------------------------------------------------------
# la respuesta en lenguaje natural
# --------------------------------------------------------------------------
from amparo.nucleo import schema  # noqa: E402

VO = ("Derecho: peticion (art. 23 CP; art. 6.1 Decreto 2591 de 1991)\nAccionado: inquilino\n"
      "Mecanismo: vía judicial ordinaria\nProcedencia: no — existe otro medio de defensa judicial "
      "idóneo y eficaz en concreto\nPretensión: exigir el pago de los alquileres adeudados")
ABST = schema.render_salida(schema.abstenerse(
    {"derecho": "x", "fundamento": "", "accionado": "a", "mecanismo": "tutela", "procede": True,
     "razon": "r", "pretension": "p"}, "es una consulta comercial"))


def _res(salida, abstuvo=False, leido=None):
    return {"respuesta": salida, "leido": leido, "segundos": {"decisión (M3)": 3.2},
            "por_que": {"regla": None if abstuvo else "subsidiariedad", "se_abstuvo": abstuvo,
                        "hechos": [] if abstuvo else ["otro_medio_judicial", "medio_eficaz"],
                        "normas_consultadas": [], "mecanismo_del_motor": "via_ordinaria",
                        "motivo_abstencion": "", "herramientas": []}}


@pytest.mark.parametrize("salida, debe", [
    (SALIDA, "acción de tutela"),
    (VO, "vía judicial ordinaria"),
    (SALIDA.replace("acción de tutela", "acción popular (Ley 472 de 1998)")
     .replace("Procedencia: sí — r", "Procedencia: no — r"), "acción popular"),
    (SALIDA.replace("acción de tutela", "acción de cumplimiento (Ley 393 de 1997)")
     .replace("Procedencia: sí — r", "Procedencia: no — r"), "acción de cumplimiento"),
    (SALIDA.replace("acción de tutela", "habeas corpus (Ley 1095 de 2006)")
     .replace("Procedencia: sí — r", "Procedencia: no — r"), "hábeas corpus"),
])
def test_plantilla_por_mecanismo(salida, debe):
    assert debe in dsp.plantilla(schema.parse_salida(salida))


def test_plantilla_de_via_ordinaria_no_nombra_el_derecho():
    t = dsp.plantilla(dsp.bloque_para_redaccion(schema.parse_salida(VO)))
    assert "petici" not in t.lower() and "tutela" in t


def test_plantilla_de_abstencion_pide_los_hechos_y_da_el_motivo():
    t = dsp.plantilla(schema.parse_salida(ABST))
    assert "qué pasó" in t and "consulta comercial" in t


def test_bloque_para_redaccion_quita_el_derecho_y_su_articulo_en_via_ordinaria():
    b = dsp.bloque_para_redaccion(schema.parse_salida(VO))
    assert b["derecho"] is None and b["fundamento"] == "art. 6.1 Decreto 2591 de 1991"
    t = dsp.bloque_para_redaccion(schema.parse_salida(SALIDA))
    assert t["derecho"] == "salud"                       # en tutela no se toca


def test_la_abstencion_no_llama_al_redactor():
    llamadas = []
    r = dsp.redactar_respuesta(_res(ABST, abstuvo=True), lambda s, u: llamadas.append(1) or "x")
    assert llamadas == [] and r["fuente"] == "plantilla_abstencion"


def test_redaccion_valida_se_usa_y_al_redactor_no_le_llega_el_derecho_en_via_ordinaria():
    vistos = []

    def generar(sistema, usuario):
        vistos.append(usuario)
        return ("Entiendo tu situación. Esto no procede por tutela: el camino es la vía judicial "
                "ordinaria (art. 6.1 Decreto 2591 de 1991). Esto es un triaje automático, "
                "no un concepto jurídico.")
    r = dsp.redactar_respuesta(_res(VO), generar)
    assert r["fuente"] == "modelo" and r["valido"] is True
    assert "peticion" not in vistos[0] and "art. 23 CP" not in vistos[0]


def test_redaccion_que_no_dice_el_mecanismo_cae_a_la_plantilla():
    r = dsp.redactar_respuesta(_res(VO), lambda s, u: "Te recomiendo buscar ayuda pronto.")
    assert r["fuente"] == "plantilla" and r["valido"] is False


def test_redaccion_con_norma_intrusa_cae_a_la_plantilla():
    r = dsp.redactar_respuesta(_res(VO), lambda s, u: (
        "No procede la tutela; vía ordinaria según el art. 29 CP."))
    assert r["fuente"] == "plantilla" and r["valido"] is False


def test_si_groq_falla_en_la_redaccion_queda_la_plantilla():
    def generar(s, u):
        raise ConnectionError("groq caido")
    r = dsp.redactar_respuesta(_res(VO), generar)
    assert r["fuente"] == "plantilla" and r["valido"] is None


def test_formatear_para_usuario_pone_el_parrafo_arriba_y_la_ficha_plegada():
    leido = {"rotulo": "Leído del documento · no verificado", "advertencias": [],
             "campos": {"fecha": None, "plazo_dias": 15}, "crudo": "{}"}
    md = dsp.formatear_para_usuario(_res(VO, leido=leido),
                                    {"texto": "Párrafo.", "fuente": "plantilla", "valido": None, "ms": 0})
    assert md.index("Párrafo.") < md.index("Por qué") < md.index("<details>")
    assert "Mecanismo: vía judicial ordinaria" in md.split("<details>")[1]   # la ficha evaluada
    assert "**Fecha:** _no se aprecia_" in md and "**Plazo (días):** 15" in md
    assert dsp.AVISO_ABOGADO in md


def test_presentar_registra_como_se_redacto():
    res, md, reg = dsp.consultar_res(_Amparo(), "p")
    out = dsp.presentar(res, md, reg, generar=None)
    assert reg["redaccion"] == "plantilla" and "acción de tutela" in out
