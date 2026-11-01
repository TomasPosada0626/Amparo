"""Tests de M4 en el paquete: amparo/multimodal/vlm.py y amparo/pipelines/m4_multimodal.py.

Sin GPU, sin red y sin modelos: `preguntar`, M3 y la carga de imagenes son
dobles. NO se ejecuta de verdad: `cargar_vlm` (baja Qwen2-VL-2B), el
`preguntador` real sobre el modelo, `enchufar_m3` sin inyectar cliente (Groq)
y `cargar` sobre una URL. Eso solo corre en Colab.
"""
from __future__ import annotations

import json

import pytest

from amparo.multimodal import vlm
from amparo.nucleo import schema
from amparo.pipelines import m4_multimodal as m4

SALIDA_TUTELA = schema.render_salida({"derecho": "salud", "accionado": "EPS", "mecanismo": "tutela",
                                      "procede": True, "razon": "r", "pretension": "p"})


# --------------------------------------------------------------------------
# vlm
# --------------------------------------------------------------------------
@pytest.mark.parametrize("texto, esperado", [
    ('{"fecha": null, "plazo_dias": 15}', {"fecha": None, "plazo_dias": 15}),
    ('Claro, aqui esta:\n```json\n{"tipo_documento": "oficio"}\n```', {"tipo_documento": "oficio"}),
    ("no veo ningun documento", None),
    ('{"fecha": "15 de enero", }', None),          # JSON roto: fallo, no se disimula
    ("}{", None),
])
def test_parsear_json(texto, esperado):
    assert vlm.parsear_json(texto) == esperado


def test_ver_pasa_la_instruccion_del_dominio_y_la_valvula_en_system():
    llamadas = []

    def preguntar(imagen, pregunta, system=None):
        llamadas.append((imagen, pregunta, system))
        return '{"tipo_documento": "notificacion", "fecha": null}'

    crudo, js = vlm.ver("img", preguntar=preguntar)
    assert js == {"tipo_documento": "notificacion", "fecha": None}
    assert llamadas == [("img", vlm.INSTRUCCION_DOMINIO, vlm.VALVULA)]
    vlm.ver("img", "otra instruccion", preguntar=preguntar)
    assert llamadas[-1][1] == "otra instruccion"


def test_lector_da_la_firma_que_espera_correr_t6():
    ver = vlm.lector(lambda imagen, pregunta, system=None: "sin json")
    assert ver("img") == ("sin json", None)


def test_armar_relato_es_la_misma_formula_que_el_harness():
    from amparo.multimodal.scorecard import armar_relato
    for js, crudo in (({"fecha": "hoy"}, "x"), (None, "texto crudo"), ({}, "crudo")):
        assert vlm.armar_relato("P", js, crudo) == armar_relato("P", js, crudo)


def test_sistema_multimodal_suma_lo_visto_al_relato():
    relatos = []
    m3 = lambda r: (relatos.append(r), SALIDA_TUTELA)[1]
    ver = lambda img: ("crudo", {"tipo_documento": "oficio"})
    assert vlm.sistema_multimodal("¿Que hago?", "img", ver=ver, responder_m3=m3) == SALIDA_TUTELA
    assert relatos[0] == '¿Que hago?\n\nDATOS DEL DOCUMENTO ADJUNTO:\n{"tipo_documento": "oficio"}'
    vlm.sistema_multimodal("solo texto", None, ver=ver, responder_m3=m3)
    assert relatos[1] == "solo texto"                 # sin imagen, M3 responde solo


def test_cronometrar_devuelve_resultado_y_segundos():
    r, seg = vlm.cronometrar(lambda a, b=0: a + b, 2, b=3)
    assert r == 5 and isinstance(seg, float) and seg >= 0


def test_cargar_normaliza_a_rgb(tmp_path):
    Image = pytest.importorskip("PIL.Image", reason="pillow no esta en este entorno (extra [vlm])")
    p = tmp_path / "doc.png"
    Image.new("L", (4, 4), 128).save(p)
    assert vlm.cargar(str(p)).mode == "RGB"


# --------------------------------------------------------------------------
# pipeline (offline, con dobles)
# --------------------------------------------------------------------------
class AgenteFalso:
    def __init__(self):
        self.trazas = [{"regla": "art6", "herramientas": ["buscar"]}]
        self.cache_guardada = 0

    def guardar_cache(self):
        self.cache_guardada += 1


def _ctx():
    ctx = m4.Contexto()
    ctx.preguntar = lambda img, txt, system=None: "SI"
    ctx.ver = lambda img: ("crudo", {"tipo_documento": "oficio", "fecha": None, "plazo_dias": 15})
    ctx.responder_m3 = lambda relato: SALIDA_TUTELA
    ctx.agente_m3 = AgenteFalso()
    ctx.sistema_m3 = "4 · agente + reglas"
    return ctx


def test_preparar_para_sin_clave(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(m4.os, "chdir", lambda p: None)
    with pytest.raises(SystemExit, match="GROQ_API_KEY"):
        m4.preparar()
    assert isinstance(m4.preparar(exigir_clave=False), m4.Contexto)


def test_cargar_imagenes_y_probar_ver(capsys):
    ctx = _ctx()
    m4.cargar_imagenes(ctx, cargar_fn=lambda ruta: f"img:{ruta}")
    assert list(ctx.imgs) == list(m4.IMAGENES)
    filas = m4.probar_ver(ctx)
    assert len(filas) == 3 and all(f["js"]["plazo_dias"] == 15 for f in filas)


def test_enchufar_m3_usa_el_enchufe_y_corre_un_ejemplo(monkeypatch):
    import amparo.multimodal.enchufe as enchufe
    agente = AgenteFalso()
    recibidos = {}

    def construir(**kw):
        recibidos.update(kw)
        return (lambda relato: SALIDA_TUTELA), agente

    monkeypatch.setattr(enchufe, "construir_responder_m3", construir)
    ctx = _ctx()
    ctx.imgs = {"a": "img"}
    assert m4.enchufar_m3(ctx, cliente="falso") == SALIDA_TUTELA
    assert ctx.sistema_m3 == enchufe.SISTEMA_M3 and recibidos == {"cliente": "falso", "verbose": True}


def test_validar_eval_set_sobre_el_csv_real_del_repo():
    ctx = _ctx()
    casos = m4.validar_eval_set(ctx, ruta_casos=m4.RAIZ / m4.RUTA_CASOS,
                                carpeta_imagenes=m4.RAIZ / m4.CARPETA_IMAGENES)
    assert len(casos) >= 5 and sum(c["tipo"] == "adversarial" for c in casos) == 1


def test_correr_harness_y_delta_imagen_de_punta_a_punta(tmp_path):
    """Con el CSV de ejemplo y dobles: correr_t6 escribe scorecard y trazas;
    sin results/ falla al armar la tabla (lo esperado) y deja lo guardado, y
    delta_imagen se arma desde esas trazas."""
    import csv
    from amparo.multimodal import criterios
    ejemplo = m4.RAIZ / "m4" / "eval_set" / "casos_m4.ejemplo.csv"
    img = tmp_path / "imagenes"
    img.mkdir()
    for c in criterios.cargar_casos(ejemplo):
        (img / c["imagen"]).write_bytes(b"")
    ctx = _ctx()
    rutas = {"ruta_scorecard": tmp_path / "s.csv", "ruta_trazas": tmp_path / "t.json",
             "ruta_delta": tmp_path / "d.json"}
    with pytest.raises(FileNotFoundError):
        m4.correr_harness(ctx, cargar_fn=lambda r: r, ruta_casos=ejemplo, carpeta_imagenes=img,
                          ruta_m3_scorecard=tmp_path / "no.csv", ruta_m3_costos=tmp_path / "no.json",
                          **rutas)
    with open(rutas["ruta_scorecard"], encoding="utf-8", newline="") as f:
        assert len(list(csv.DictReader(f))) == len(criterios.cargar_casos(ejemplo))

    di = m4.delta_imagen(ctx, ruta_casos=ejemplo, ruta_trazas=rutas["ruta_trazas"],
                         ruta_salida=tmp_path / "di.json")
    assert di["n"] == sum(c["criterio"] == "exacto" for c in criterios.cargar_casos(ejemplo))
    assert ctx.agente_m3.cache_guardada == 1

    tabla = m4.resumen(rutas["ruta_scorecard"], rutas["ruta_trazas"])
    assert list(tabla.columns) == ["id", "criterio", "tipo", "nota", "segundos", "etapa", "lectura_vlm"]


def test_descargar_fuera_de_colab_lista_lo_que_existe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "s.csv").write_text("x")
    assert m4.descargar(("s.csv", "no.json")) == ["s.csv"]


def test_el_notebook_es_un_envoltorio_delgado():
    nb = json.loads((m4.RAIZ / "m4" / "pipeline" / "M4_pipeline.ipynb").read_text(encoding="utf-8"))
    codigo = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    todo = "\n".join(codigo)
    assert "from amparo.pipelines import m4_multimodal as m4" in todo
    assert "def " not in todo                        # la logica vive en el paquete
    assert all(not c.get("outputs") for c in nb["cells"] if c["cell_type"] == "code")
