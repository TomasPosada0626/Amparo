"""Tests de M5 · S15 · Parte A: amparo/pipelines/m5_cuantizacion.py y los
parametros nuevos de `LectorVisual`.

Sin GPU, sin red y sin modelos: el VLM, M3 y el juez son dobles. NO se
ejecuta de verdad: cargar Qwen2-VL-2B en fp16 o int4 (bitsandbytes) ni M3
por Groq. Eso solo corre en Colab.
"""
from __future__ import annotations

import json

import pytest

from amparo.multimodal import criterios, scorecard
from amparo.pipelines import m5_cuantizacion as m5q

SALIDA = ("Derecho: salud (art. 49 CP)\nAccionado: EPS\nMecanismo: acción de tutela\n"
          "Procedencia: sí — r\nPretensión: p")


# --------------------------------------------------------------------------
# LectorVisual: cuantizacion y max_pixels
# --------------------------------------------------------------------------
class _Capturador:
    llamadas: list = []

    @classmethod
    def from_pretrained(cls, modelo_id, **kw):
        cls.llamadas.append((modelo_id, kw))
        return cls()


class _BnB:
    def __init__(self, **kw):
        self.kw = kw


@pytest.fixture
def transformers_falso(monkeypatch):
    """Un `transformers` de mentira en sys.modules: `LectorVisual` lo importa
    dentro de `__init__`, asi que ve este y nunca baja pesos."""
    import sys
    import types
    falso = types.ModuleType("transformers")
    falso.Qwen2VLForConditionalGeneration = _Capturador
    falso.AutoProcessor = _Capturador
    falso.BitsAndBytesConfig = _BnB
    _Capturador.llamadas = []
    monkeypatch.setitem(sys.modules, "transformers", falso)
    return _Capturador


def test_lector_sin_parametros_carga_igual_que_en_m4(transformers_falso):
    from amparo.multimodal.sistema_visual import LectorVisual
    LectorVisual(device="cuda")
    (_, kw_vlm), (_, kw_proc) = transformers_falso.llamadas
    assert set(kw_vlm) == {"torch_dtype", "device_map"}          # nada de cuantizacion
    assert kw_proc == {}                                          # ni de max_pixels


def test_lector_int4_usa_la_linea_del_lab(transformers_falso):
    import torch
    from amparo.multimodal.sistema_visual import LectorVisual
    lec = LectorVisual(device="cuda", cuantizacion="int4", max_pixels=401408)
    (_, kw_vlm), (_, kw_proc) = transformers_falso.llamadas
    bnb = kw_vlm["quantization_config"].kw
    assert bnb == {"load_in_4bit": True, "bnb_4bit_compute_dtype": torch.float16,
                   "bnb_4bit_quant_type": "nf4"}
    assert kw_proc == {"max_pixels": 401408}
    assert lec.cuantizacion == "int4"


def test_lector_int4_en_cpu_se_rechaza_antes_de_bajar_pesos(transformers_falso):
    from amparo.multimodal.sistema_visual import LectorVisual
    with pytest.raises(ValueError, match="GPU"):
        LectorVisual(device="cpu", cuantizacion="int4")
    assert transformers_falso.llamadas == []


def test_lector_cuantizacion_desconocida(transformers_falso):
    from amparo.multimodal.sistema_visual import LectorVisual
    with pytest.raises(ValueError, match="int4"):
        LectorVisual(device="cuda", cuantizacion="int2")


# --------------------------------------------------------------------------
# latencias (la funcion del lab)
# --------------------------------------------------------------------------
def test_latencias_descarta_el_calentamiento():
    tiempos = iter([0, 1, 1, 3, 3, 6, 6, 10, 10, 15])          # duran 1, 2, 3, 4 y 5
    llamadas = []
    p50, p95 = m5q.latencias(lambda img: llamadas.append(img), "img", n=5,
                             reloj=lambda: next(tiempos))
    assert len(llamadas) == 6                                     # 1 de calentamiento + 5
    assert (p50, p95) == (3, 5)


# --------------------------------------------------------------------------
# medir, tabla y contrato, con dobles
# --------------------------------------------------------------------------
LECTURA_BUENA = {"tipo_documento": "respuesta_peticion", "entidad": "Salud Serena EPS",
                 "fecha": "5 de octubre de 2026", "plazo_dias": 15,
                 "pretension_visible": "la cirugia de cadera"}


class _LectorFalso:
    """`ver` recibe la RUTA (los tests pasan `cargar_fn=str`): el documento
    borroso de m10 (doc06) se lee sin fecha ni plazo, salvo `m10` explicito."""
    def __init__(self, lectura, m10=None):
        self.lectura, self.vistas = lectura, 0
        self.m10 = m10 if m10 is not None else {**lectura, "fecha": None, "plazo_dias": None}

    def ver(self, imagen):
        self.vistas += 1
        js = dict(self.m10 if "doc06" in str(imagen) else self.lectura)
        return json.dumps(js), js

    def preguntar(self, imagen, texto, system=None):
        return "SI"


def _ctx(tmp_path, lect16, lect4, mem=(4.4, 1.5), monkeypatch=None):
    ctx = m5q.Contexto(carpeta=tmp_path)
    relatos = []
    ctx.responder_m3 = lambda r: relatos.append(r) or SALIDA
    cargas = iter([(lect16, mem[0]), (lect4, mem[1])])
    monkeypatch.setattr(m5q, "cargar", lambda cuantizar, lector_cls=None: next(cargas))
    return ctx, relatos


def test_medir_usa_el_juez_fp16_para_las_dos_cargas(tmp_path, monkeypatch):
    f16, f4 = _LectorFalso(LECTURA_BUENA), _LectorFalso(LECTURA_BUENA)
    preguntas = {"f16": 0, "f4": 0}
    f16.preguntar = lambda *a, **k: preguntas.__setitem__("f16", preguntas["f16"] + 1) or "SI"
    f4.preguntar = lambda *a, **k: preguntas.__setitem__("f4", preguntas["f4"] + 1) or "SI"
    ctx, _ = _ctx(tmp_path, f16, f4, monkeypatch=monkeypatch)
    m5q.medir(ctx, cargar_fn=str)
    n_juez = sum(1 for c in criterios.cargar_casos(scorecard.RUTA_CASOS) if c["criterio"] == "juez_vlm")
    assert preguntas == {"f16": 2 * n_juez, "f4": 0}             # el int4 nunca juzga
    assert set(ctx.medidas) == {"fp16", "int4"}
    assert (tmp_path / "medida_int4.json").exists()


def test_contrato_cumplido_si_lee_igual_y_ahorra_memoria(tmp_path, monkeypatch, capsys):
    ctx, _ = _ctx(tmp_path, _LectorFalso(LECTURA_BUENA), _LectorFalso(LECTURA_BUENA),
                  monkeypatch=monkeypatch)
    m5q.medir(ctx, cargar_fn=str)
    for q in ("fp16", "int4"):                                   # latencias fijas
        ctx.medidas[q]["lectura_p50_s"] = 3.7 if q == "fp16" else 4.0
    df = m5q.tabla(ctx)
    t = ctx.medidas["tabla"]
    assert len(df) == 2 and t["cumple"] and t["memoria_x"] == round(4.4 / 1.5, 2)
    assert m5q.lecturas_distintas(ctx) == []


def test_contrato_no_cumplido_si_inventa_la_fecha_de_m10(tmp_path, monkeypatch):
    """La valvula es innegociable: si int4 lee una fecha donde no la hay, NO."""
    inventa = dict(LECTURA_BUENA, fecha="3 de marzo de 2026", plazo_dias=10)
    ctx, _ = _ctx(tmp_path, _LectorFalso(LECTURA_BUENA),
                  _LectorFalso(LECTURA_BUENA, m10=inventa), monkeypatch=monkeypatch)
    m5q.medir(ctx, cargar_fn=str)
    for q in ("fp16", "int4"):
        ctx.medidas[q]["lectura_p50_s"] = 3.7
    m5q.tabla(ctx)
    cl = ctx.medidas["tabla"]["clausulas"]
    assert cl["valvula (m10)"]["cumple"] is False
    assert not ctx.medidas["tabla"]["cumple"]
    distintas = m5q.lecturas_distintas(ctx)
    assert distintas and "fecha" in distintas[0]["campos"]


def test_contrato_no_cumplido_si_la_lectura_es_mucho_mas_lenta(tmp_path, monkeypatch):
    ctx, _ = _ctx(tmp_path, _LectorFalso(LECTURA_BUENA), _LectorFalso(LECTURA_BUENA),
                  monkeypatch=monkeypatch)
    m5q.medir(ctx, cargar_fn=str)
    ctx.medidas["fp16"]["lectura_p50_s"], ctx.medidas["int4"]["lectura_p50_s"] = 3.0, 4.2
    m5q.tabla(ctx)
    cl = ctx.medidas["tabla"]["clausulas"]
    assert cl["latencia de la lectura"]["cumple"] is False        # +40 % > 30 %


def test_lectura_identica_da_el_mismo_relato_a_m3(tmp_path, monkeypatch):
    """Es lo que permite que la cache de M3 aisle el efecto de cuantizar."""
    ctx, relatos = _ctx(tmp_path, _LectorFalso(LECTURA_BUENA), _LectorFalso(LECTURA_BUENA),
                        monkeypatch=monkeypatch)
    m5q.medir(ctx, cargar_fn=str)
    mitad = len(relatos) // 2
    assert relatos[:mitad] == relatos[mitad:]


def test_guardar_escribe_en_m5_y_en_la_carpeta_de_trabajo(tmp_path, monkeypatch):
    ctx, _ = _ctx(tmp_path, _LectorFalso(LECTURA_BUENA), _LectorFalso(LECTURA_BUENA),
                  monkeypatch=monkeypatch)
    ctx.corrida = {"codigo": {"commit": "abc"}}
    m5q.medir(ctx, cargar_fn=str)
    m5q.tabla(ctx)
    m5q.lecturas_distintas(ctx)
    rutas = m5q.guardar(ctx, carpeta=tmp_path / "m5")
    d = json.loads((tmp_path / "m5" / "cuantizacion.json").read_text(encoding="utf-8"))
    assert len(rutas) == 2 and "fin_utc" in d["corrida"]
    assert d["vlm"]["licencia"].startswith("Apache")
    assert {"fp16", "int4"} == set(d["por_caso"])
