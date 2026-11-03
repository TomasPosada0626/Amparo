"""Tests de M5 · S14: amparo/pipelines/m5_destilacion.py.

Sin GPU, sin red y sin modelos: el profesor (Groq), el estudiante (Qwen) y el
cliente que escribe relatos son dobles. NO se ejecuta de verdad: armar el
profesor real, `entrenar_estudiante`, `cargar_estudiante`, `generador` y
`medir` con Groq. Eso solo corre en Colab.
"""
from __future__ import annotations

import json

import pytest

from amparo.nucleo import schema
from amparo.nucleo.reglas import HECHOS_EXTRAIBLES, Hechos, decidir
from amparo.pipelines import m5_destilacion as m5


def _libres(e: dict) -> dict:
    return {"derecho": e["derecho"], "accionado": e["accionado"],
            "pretension": e["pretension"], "no_triable": False, "motivo_no_triable": ""}


def _hechos(e: dict) -> Hechos:
    return Hechos(**{k: v for k, v in e["hechos"].items() if k in HECHOS_EXTRAIBLES})


CON_HECHOS = [e for e in schema.cargar() if e.get("hechos") and e.get("mecanismo")]


# --------------------------------------------------------------------------
# el JSON compacto no pierde nada al pasar por Agente._hechos
# --------------------------------------------------------------------------
def test_objetivo_omite_los_valores_por_defecto():
    d = m5.objetivo(Hechos(afectacion_individual=True, medio_eficaz=False),
                    {"derecho": "salud", "accionado": "EPS", "pretension": "autorizar"})
    assert d == {"afectacion_individual": True, "medio_eficaz": False,
                 "derecho": "salud", "accionado": "EPS", "pretension": "autorizar"}


@pytest.mark.parametrize("e", CON_HECHOS[:40], ids=lambda e: e["id"])
def test_el_estudiante_que_copia_al_profesor_decide_lo_mismo(e):
    """Si el estudiante escribe EXACTAMENTE el JSON del profesor, la salida
    sale del mismo motor: el mismo mecanismo que `decidir` sobre esos hechos."""
    h = _hechos(e)
    texto = m5.a_texto(m5.objetivo(h, _libres(e)))
    est = m5.agente_estudiante(lambda relato: texto)
    salida = est(e["relato"])
    p = schema.parse_salida(salida)
    assert p["mecanismo"] == decidir(h).mecanismo
    assert est.trazas[-1]["pasos"] == 0                     # sin herramientas
    assert est.contadores["hechos_no_parseados"] == 0


def test_el_estudiante_recibe_el_relato_y_no_el_prompt_del_profesor():
    vistos = []
    est = m5.agente_estudiante(lambda r: vistos.append(r) or '{"derecho":"salud"}')
    est("Mi EPS no me entrega un medicamento.")
    assert vistos == ["Mi EPS no me entrega un medicamento."]


def test_la_valvula_de_abstencion_llega_intacta():
    texto = m5.a_texto({"caso_triable": False, "motivo_no_triable": "es una consulta academica",
                        "derecho": "ninguno", "accionado": "x", "pretension": "y"})
    p = schema.parse_salida(m5.agente_estudiante(lambda r: texto)("¿Que es una tutela?"))
    assert p["mecanismo"] is None


def test_json_roto_del_estudiante_se_cuenta_y_no_se_disimula():
    est = m5.agente_estudiante(lambda r: "no se")
    est("relato")
    assert est.contadores["hechos_no_parseados"] == 1


def test_el_prompt_del_estudiante_nombra_todos_los_hechos_extraibles():
    s = m5.sistema_estudiante()
    for k in HECHOS_EXTRAIBLES:
        assert k in s, k


# --------------------------------------------------------------------------
# 1 · el scorecard de M4
# --------------------------------------------------------------------------
def test_latencia_por_componente_sobre_el_scorecard_de_m4(capsys):
    try:
        m5.corrida_m4_con_tiempos()
    except FileNotFoundError:
        pytest.skip("esta rama aun no trae las corridas de M4 con segundos_ver (estan en main)")
    out = m5.latencia_por_componente()
    comp = out["componentes"]
    assert out["n"] > 0
    assert set(comp) == {"VLM Qwen2-VL-2B (lectura del documento)",
                         "M3 brazo 4 (agente gpt-oss-120b + reglas)", "total por caso"}
    assert out["mas_lento"] in comp


def test_latencia_por_componente_resta_bien(tmp_path):
    sc = tmp_path / "sc.csv"
    sc.write_text("id,segundos\na,10\nb,4\nc,6\n", encoding="utf-8")
    tr = tmp_path / "tr.json"
    tr.write_text(json.dumps({"a": {"segundos_ver": 3}, "b": {"segundos_ver": 3},
                              "c": {"segundos_ver": 4}}), encoding="utf-8")
    out = m5.latencia_por_componente(sc, tr)
    m3 = out["componentes"]["M3 brazo 4 (agente gpt-oss-120b + reglas)"]
    assert (m3["min_s"], m3["mediana_s"], m3["max_s"]) == (1, 2, 7)
    assert out["mas_lento"].startswith("VLM")              # mediana 3 contra 2


# --------------------------------------------------------------------------
# B1 · relatos y pares
# --------------------------------------------------------------------------
class _ClienteRelatos:
    def __init__(self, textos=None, falla=None):
        self.n, self.textos, self.falla = 0, textos, falla
        self.chat = type("C", (), {})()
        self.chat.completions = type("X", (), {"create": self.create})()

    def create(self, **kw):
        self.n += 1
        if self.falla and self.n >= self.falla[0]:
            raise self.falla[1]
        texto = (self.textos(self.n) if self.textos else
                 f"Relato sintetico numero {self.n} sobre un problema con la entidad del municipio.")
        return m5._Respuesta(texto)


def test_escribir_relatos_retoma_y_filtra_la_fuga(tmp_path):
    ctx = m5.Contexto(carpeta=tmp_path)
    ev = m5.cargar_eval()
    copia = ev[0]["relato"]
    cli = _ClienteRelatos(textos=lambda n: copia if n == 1 else
                          f"Caso inventado {n}: el vecino me cerro el paso a mi finca y no puedo salir.")
    rel = m5.escribir_relatos(ctx, n_por_tema=1, cliente=cli)
    assert all(r["coseno_max_eval"] < m5.UMBRAL_FUGA for r in rel)
    assert len(rel) == cli.n - 1                                 # la copia del eval sale
    n = cli.n
    m5.escribir_relatos(ctx, n_por_tema=1, cliente=cli)         # todo hecho: no llama
    assert cli.n == n


def test_escribir_relatos_para_si_se_acaba_el_cupo_y_guarda(tmp_path):
    class RateLimitError(Exception):
        pass
    ctx = m5.Contexto(carpeta=tmp_path)
    cli = _ClienteRelatos(falla=(4, RateLimitError("429 rate limit")))
    with pytest.raises(m5.CupoAgotado):
        m5.escribir_relatos(ctx, n_por_tema=1, cliente=cli)
    assert len(json.loads((tmp_path / "relatos_sinteticos.json").read_text(encoding="utf-8"))) == 3


class _ProfesorFalso:
    """Lo que `etiquetar_con_profesor` usa del Agente."""
    def __init__(self, malos=(), cupo_en=None):
        self.fallos_extraccion, self.contadores = [], {"hechos_no_parseados": 0}
        self.malos, self.cupo_en, self.guardadas = set(malos), cupo_en, 0

    def _bucle(self, relato):
        return [], {"pasos": 2}

    def _hechos(self, mensajes, relato):
        if relato == self.cupo_en:
            self.fallos_extraccion.append({"error": "RateLimitError", "detalle": "429"})
        elif relato in self.malos:
            self.fallos_extraccion.append({"error": "BadRequestError", "detalle": "400"})
        return Hechos(afectacion_individual=True), {"derecho": "salud", "accionado": "EPS",
                                                    "pretension": "autorizar", "no_triable": False}

    def guardar_cache(self):
        self.guardadas += 1


def test_etiquetar_descarta_lo_que_el_profesor_no_pudo_extraer(tmp_path):
    ds = schema.cargar()
    ctx = m5.Contexto(carpeta=tmp_path, agente_profesor=_ProfesorFalso(malos={ds[0]["relato"]}))
    pares = m5.etiquetar_con_profesor(ctx)
    assert len(pares) == len(ds) - 1
    assert ds[0]["id"] not in {p["id"] for p in pares}
    assert pares[0]["objetivo"]["afectacion_individual"] is True
    assert {p["split"] for p in pares} == {"train", "validation"}


def test_etiquetar_para_con_el_cupo_y_retoma(tmp_path):
    ds = schema.cargar()
    prof = _ProfesorFalso(cupo_en=ds[3]["relato"])
    ctx = m5.Contexto(carpeta=tmp_path, agente_profesor=prof)
    with pytest.raises(m5.CupoAgotado):
        m5.etiquetar_con_profesor(ctx)
    guardados = json.loads((tmp_path / "pares_profesor.json").read_text(encoding="utf-8"))
    assert len(guardados) == 3
    prof.cupo_en = None
    assert len(m5.etiquetar_con_profesor(ctx)) == len(ds)


# --------------------------------------------------------------------------
# B3 y 5 · medir, tabla y contrato
# --------------------------------------------------------------------------
def test_correr_con_reloj_retoma_y_no_inventa_respuestas(tmp_path):
    casos = [{"id": "a", "relato": "x"}, {"id": "b", "relato": "y"}]

    def sis(r):
        if r == "y":
            raise ValueError("boom")
        return "salida"
    out = m5.correr_con_reloj(sis, casos, tmp_path / "e.json", "prueba")
    assert out["a"]["salida"] == "salida" and out["b"]["salida"] == ""
    assert out["b"]["error"].startswith("ValueError")
    llamadas = []
    m5.correr_con_reloj(lambda r: llamadas.append(r), casos, tmp_path / "e.json", "prueba")
    assert llamadas == []


def _ctx_medido(tmp_path, seg_prof, seg_est, estropear=0):
    from amparo.evaluacion import harness
    ev = m5.cargar_eval()
    gold = [schema.render_salida(e) if e.get("mecanismo") else
            schema.render_salida(schema.abstenerse({**e}, "")) for e in ev]
    est = list(gold)
    for i in range(estropear):
        est[i] = ""
    ctx = m5.Contexto(carpeta=tmp_path, eval_set=ev, n_parametros_estudiante=494_000_000)
    for quien, sal, s in (("profesor", gold, seg_prof), ("estudiante", est, seg_est)):
        ctx.medidas[quien] = {"salidas": sal, "segundos": [s] * len(ev),
                              "scorecard": harness.harness(ev, sal, quien),
                              "aciertos": harness.acierto_por_item(sal, ev)}
    return ctx


def test_tabla_contrato_cumplido(tmp_path):
    ctx = _ctx_medido(tmp_path, 6.0, 1.0)
    df = m5.tabla(ctx)
    v = ctx.medidas["tabla"]["veredicto"]
    assert len(df) == 2 and v["cumple"] and v["gano_latencia_x"] == 6.0
    assert v["gano_tamano_x"] == round(117e9 / 494e6)


def test_tabla_contrato_no_cumplido_si_pierde_mas_de_lo_aceptado(tmp_path):
    ctx = _ctx_medido(tmp_path, 6.0, 1.0, estropear=12)
    m5.tabla(ctx)
    v = ctx.medidas["tabla"]["veredicto"]
    assert v["perdio_puntos"] > m5.CONTRATO["acepto_perder_puntos"] and not v["cumple"]
    assert "1.5B" in v["si_no_cumple"]
    perdidos = m5.casos_perdidos(ctx)
    assert {p["id"] for p in perdidos} <= {e["id"] for e in ctx.eval_set[:12]}


def test_tabla_contrato_no_cumplido_si_no_gana_latencia(tmp_path):
    ctx = _ctx_medido(tmp_path, 6.0, 4.0)
    m5.tabla(ctx)
    assert not ctx.medidas["tabla"]["veredicto"]["cumple"]


def test_guardar_escribe_lo_que_va_al_repo(tmp_path):
    ctx = _ctx_medido(tmp_path, 6.0, 1.0)
    m5.tabla(ctx)
    m5.casos_perdidos(ctx)
    ctx.pares = [{"id": "T01", "relato": "r", "split": "train", "objetivo": {"derecho": "salud"}}]
    rutas = m5.guardar(ctx, carpeta=tmp_path / "m5")
    d = json.loads((tmp_path / "m5" / "destilacion.json").read_text(encoding="utf-8"))
    assert d["veredicto"]["cumple"] and d["profesor"]["licencia"].startswith("Apache")
    assert len(rutas) == 2


def test_acuerdo_profesor_gold_con_un_profesor_perfecto(tmp_path):
    ctx = m5.Contexto(carpeta=tmp_path)
    ctx.pares = [{"id": e["id"], "objetivo": m5.objetivo(_hechos(e), _libres(e))}
                 for e in CON_HECHOS]
    out = m5.acuerdo_profesor_gold(ctx)
    malos = [e["id"] for e in CON_HECHOS if decidir(_hechos(e)).mecanismo != e["mecanismo"]]
    assert out["n"] == len(CON_HECHOS)
    assert out["acierto"] == round((len(CON_HECHOS) - len(malos)) / len(CON_HECHOS), 3)
