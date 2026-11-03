"""Tests de M3 fuera del notebook: `amparo/evaluacion/brazos.py` y las etapas
de `amparo/pipelines/m3_rag.py` que se pueden correr sin GPU ni API.

Todo con dobles: sistemas falsos, transformador falso con contadores, indice
falso y el cliente guionado de `tests/autoprueba_agente.py`, asi que no se
baja ningun modelo ni se llama a Groq.

LO QUE NO SE EJECUTA AQUI (necesita GPU, red o claves; queda para Colab):
corpus/chunking/recuperacion reales (bajan el embedder y el reranker),
`modelos` (Qwen2.5-7B + LoRA), `ragas_propio` y `ragas_libreria` (juez Groq y
libreria ragas), `scorecards` (juez), `publicar` (escribe en results/) y
`cierre` (scripts de data/).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from amparo.config import RAIZ
from amparo.ejecucion import arranque
from amparo.evaluacion import brazos as br
from amparo.evaluacion import costos
from amparo.nucleo import schema
from amparo.pipelines import m3_rag as m3

sys.path.insert(0, str(RAIZ / "tests"))
from autoprueba_agente import ClienteGuionado, IndiceFalso  # noqa: E402


def _salida(mec="tutela", procede=True):
    return schema.render_salida({"derecho": "salud", "accionado": "EPS", "mecanismo": mec,
                                 "procede": procede, "razon": "r", "pretension": "p"})


class Reloj:
    """perf_counter falso: cada lectura avanza `paso` segundos."""
    def __init__(self, paso=1.0):
        self.t, self.paso = 0.0, paso

    def __call__(self):
        self.t += self.paso
        return self.t


# --------------------------------------------------------------------------
# correr_brazo
# --------------------------------------------------------------------------
def test_correr_brazo_tolera_un_fallo_de_api_con_salida_vacia(capsys):
    def sis(relato):
        if "falla" in relato:
            raise RuntimeError("400 de Groq")
        return "ok:" + relato

    casos = [{"id": "a", "relato": "uno"}, {"id": "b", "relato": "falla"}, {"id": "c", "relato": "tres"}]
    r = br.correr_brazo(sis, "brazo X", casos, reloj=Reloj(1.0))
    assert r.salidas == {"a": "ok:uno", "b": "", "c": "ok:tres"}
    assert [f["id"] for f in r.fallos] == ["b"] and r.fallos[0]["error"] == "RuntimeError"
    out = capsys.readouterr().out
    assert "ETA" in out and "1 fallos de API" in out and "FALLO b: RuntimeError" in out


def test_correr_brazo_latencia_por_caso():
    # t0 = 1, luego una lectura por caso (2, 3) y la final (4): 3 s / 2 casos.
    r = br.correr_brazo(lambda x: x, "b", [{"id": "a", "relato": "x"}, {"id": "b", "relato": "y"}],
                        reloj=Reloj(1.0))
    assert r.latencia_s == pytest.approx(1.5)


def test_reloj_legible():
    assert br.reloj_legible(42) == "42s" and br.reloj_legible(125) == "2m05s"


# --------------------------------------------------------------------------
# CostoPorBrazo
# --------------------------------------------------------------------------
class TransformadorFalso:
    """Contadores acumulativos como `TransformadorConsulta`; el cache es un set."""
    def __init__(self):
        self.llamadas = self.fallos = 0
        self.cache = set()
        self.guardado = 0

    def __call__(self, relato):
        if relato not in self.cache:
            self.cache.add(relato)
            self.llamadas += 1
        return "rees:" + relato

    def multiples(self, relato, n=3):
        return [self(relato + str(i)) for i in range(n)]

    def hyde(self, relato):
        return self("hyde:" + relato)

    def guardar(self):
        self.guardado += 1


def test_costo_por_brazo_cuenta_reales_y_cache_y_cronometra_solo_las_reales():
    tr = TransformadorFalso()
    w = br.CostoPorBrazo(tr, tr, reloj=Reloj(0.010))      # 10 ms por lectura
    for r in ("a", "b", "a", "a"):
        w(r)
    k = w.costo()
    assert k["llamadas_reales"] == 2 and k["desde_cache"] == 2 and k["transformaciones"] == 4
    assert k["latencia_ms_media"] == pytest.approx(10.0)  # solo las 2 reales


def test_costo_por_brazo_reparte_el_contador_compartido():
    # Como en `recuperacion`: cada brazo se envuelve, corre y lee su costo
    # antes de que el siguiente use el mismo `tr`.
    tr = TransformadorFalso()
    w1 = br.CostoPorBrazo(tr, tr)
    w1("a"), w1("b")
    k1 = w1.costo()
    w2 = br.CostoPorBrazo(lambda r: tr.multiples(r, 3), tr)
    w2("c")
    k2 = w2.costo()
    assert k1["llamadas_reales"] == 2 and k2["llamadas_reales"] == 3
    assert tr.llamadas == 5                              # el acumulado es la suma, no lo de un brazo


def test_brazo_no_medido_sale_en_none_y_no_en_cero():
    fila = costos.tabla([br.BrazoNoMedido()])[0]
    assert fila["etiqueta"] == m3.BRAZO_1
    assert fila["llamadas_reales"] is None and fila["latencia_p50"] is None
    assert "sin instrumentar" in fila["nota"]


# --------------------------------------------------------------------------
# transformador_para
# --------------------------------------------------------------------------
def test_transformador_para_despliega_la_tecnica_que_gano():
    tr = TransformadorFalso()
    est, f, nombre = br.transformador_para("hibrido + multiconsulta", tr)
    assert (est, nombre) == ("hibrido", "multiconsulta (3)") and len(f("x")) == 3
    est, f, nombre = br.transformador_para("hibrido + hyde", tr)
    assert (est, nombre) == ("hibrido", "hyde") and f("x") == "rees:hyde:x"
    est, f, nombre = br.transformador_para("reranked + reescritura", tr)
    assert (est, f, nombre) == ("reranked", tr, "reescritura simple")
    est, f, nombre = br.transformador_para("reranked", tr)
    assert (est, f, nombre) == ("reranked", None, "ninguna")


# --------------------------------------------------------------------------
# matriz por caso y techo de la union
# --------------------------------------------------------------------------
EVAL = [{"id": "e1", "tipo": "gold", "categoria": "salud", "mecanismo": "tutela", "procede": True},
        {"id": "e2", "tipo": "adversarial", "categoria": "colectivo",
         "mecanismo": "accion_popular", "procede": True},
        {"id": "e3", "tipo": "gold", "categoria": "x", "mecanismo": "tutela", "procede": False}]


def test_matriz_por_caso_y_techo_de_la_union():
    brazos = {
        "A": {"e1": _salida("tutela"), "e2": _salida("tutela"), "e3": _salida("tutela", False)},
        "B": {"e1": _salida("tutela", False), "e2": _salida("accion_popular")},   # no cubre e3
    }
    filas = br.matriz_por_caso(brazos, EVAL)
    assert [f["id"] for f in filas] == ["e1", "e2", "e3"]
    assert filas[0]["brazos"]["A"]["acierta"] and not filas[0]["brazos"]["B"]["acierta"]
    assert "B" not in filas[2]["brazos"]
    t = br.techo_union(filas)
    assert t == {"n": 3, "por_brazo": {"A": 2, "B": 1}, "union": 3,
                 "margen_sobre_el_mejor": round(1 / 3, 4)}


# --------------------------------------------------------------------------
# checkpoint y brazos (pipeline), sin GPU ni Groq
# --------------------------------------------------------------------------
class CorridaFalsa:
    def __init__(self, carpeta: Path):
        self.dir = carpeta
        self.artefactos, self.notas = {}, []
        (carpeta / "cache").mkdir(parents=True, exist_ok=True)

    def ruta_cache(self, nombre):
        return self.dir / "cache" / nombre

    def guardar_json(self, nombre, obj):
        (self.dir / f"{nombre}.json").write_text(json.dumps(obj, ensure_ascii=False, default=str),
                                                 encoding="utf-8")
        self.artefactos[nombre] = f"{nombre}.json"

    def nota(self, texto):
        self.notas.append(texto)


class SistemaFalso:
    def __init__(self, etiqueta):
        self.etiqueta, self.llamadas = etiqueta, 0

    def __call__(self, relato):
        self.llamadas += 1
        return _salida()


def _ctx(tmp_path):
    ctx = m3.Contexto(c=CorridaFalsa(tmp_path))
    ctx.eval_set = [{"id": "e1", "relato": "me niegan un medicamento"},
                    {"id": "e2", "relato": "no responden mi peticion"}]
    ctx.eval_m3 = [{"id": "m1", "relato": "el municipio no cumple una ley"}]
    return ctx


def test_un_brazo_corrido_se_guarda_en_el_checkpoint_y_se_reutiliza(tmp_path):
    ctx = _ctx(tmp_path)
    m3._cargar_ck(ctx)
    sis = SistemaFalso("2 · prueba")
    m3._correr_o_reusar(ctx, sis, "brazo 2")
    assert sis.llamadas == 3
    ck = arranque.cargar_checkpoint(ctx.ruta_ck)
    assert set(ck["brazos"]["2 · prueba"]) == {"e1", "e2", "m1"}
    assert "brazo 2" in ck["latencias"] and ck["fallos"]["brazo 2"] == []

    # Otra sesion: el brazo ya estaba, no se vuelve a pagar.
    ctx2 = _ctx(tmp_path)
    m3._cargar_ck(ctx2)
    sis2 = SistemaFalso("2 · prueba")
    m3._correr_o_reusar(ctx2, sis2, "brazo 2")
    assert sis2.llamadas == 0 and ctx2.brazos["2 · prueba"] == ck["brazos"]["2 · prueba"]


def test_correr_brazos_sin_gpu_corre_el_agente_y_el_brazo_uno(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path)
    ctx.decision = {"elegida": "hibrido + multiconsulta"}
    ctx.indice, ctx.tr = IndiceFalso(), TransformadorFalso()
    preds = [{"id": "e1", "finetuned": _salida()}, {"id": "e2", "finetuned": _salida("via_ordinaria")}]
    monkeypatch.setattr(m3.predicciones, "cargar_m1",
                        lambda eval_set=None: (preds, "20261018T000000Z"))
    cliente = ClienteGuionado([[("buscar_normas", '{"consulta": "derecho a la salud"}')], None])

    m3.correr_brazos(ctx, cliente=cliente)

    assert ctx.s_ing is None and ctx.s_adv is None          # sin modelo, sin brazos 2-3
    assert ctx.brazos[m3.BRAZO_1] == {"e1": preds[0]["finetuned"], "e2": preds[1]["finetuned"]}
    assert set(ctx.brazos[m3.BRAZO_4]) == {"e1", "e2", "m1"}
    assert all(schema.parse_salida(s)["mecanismo"] for s in ctx.brazos[m3.BRAZO_4].values())
    assert ctx.corrida_m1 == "20261018T000000Z" and ctx.tr.guardado == 1
    for n in ("agente_resumen", "config_brazos", "recortes_m3", "agente_trazas"):
        assert n in ctx.c.artefactos
    conf = json.loads((tmp_path / "config_brazos.json").read_text(encoding="utf-8"))
    assert conf["transformacion_desplegada_brazo3"] == "sin brazo 3 (no hay GPU)"
    assert any("20261018T000000Z" in n for n in ctx.c.notas)


# --------------------------------------------------------------------------
# lo que la autoprueba y verificar_entrega leen del codigo
# --------------------------------------------------------------------------
FUENTE = (RAIZ / "amparo" / "pipelines" / "m3_rag.py").read_text(encoding="utf-8")


def test_el_pipeline_usa_el_checkpoint_de_los_brazos():
    for k in ("brazos_checkpoint", "cargar_checkpoint", "_ck_guardar"):
        assert k in FUENTE


def test_a_publicar_es_literal_y_coincide_con_lo_que_declara_arranque():
    destinos = re.findall(r"\(\s*\"([^\"]+)\"\s*,\s*\"(results/[^\"]+)\"\s*\)", FUENTE)
    assert len(destinos) == 14
    assert {d for _, d in destinos} == set(arranque.ORDEN["m3"]["produce"])


def test_cada_artefacto_se_genera_antes_de_la_lista_de_publicacion():
    corte = FUENTE.index("A_PUBLICAR = [")
    for nombre, _ in re.findall(r"\(\s*\"([^\"]+)\"\s*,\s*\"(results/[^\"]+)\"\s*\)", FUENTE):
        pos = [m.start() for p in (rf'guardar_(?:json|csv)\("{nombre}"',
                                    rf'c\.artefactos\["{nombre}"\]')
               for m in re.finditer(p, FUENTE)]
        assert pos and min(pos) < corte, f"'{nombre}' no se genera antes de publicarse"


def test_las_constantes_de_la_corrida_no_cambiaron():
    assert (m3.K, m3.K_AGENTE, m3.MUESTRA, m3.RAGAS_PIN, m3.MAX_NEW) == (5, 4, 8, "0.2.15", 220)
    assert m3.ARCHIVO_EVAL == "eval_set_v3.json"
