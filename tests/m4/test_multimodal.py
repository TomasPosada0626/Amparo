"""
Pruebas de lo que se anadio tras la revision docente (PR #15 y #16), sin GPU
ni red: el modulo importable, la respuesta en tres bloques, el vaciado de
caches, el delta repetido y el manifiesto de corrida.

El M3 es el `agente.Agente` real con los dobles de `tests/autoprueba_agente.py`;
el VLM es un lector falso que devuelve lecturas fijas.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tests"))  # autoprueba_agente: ClienteGuionado, IndiceFalso

from amparo.multimodal import corrida_m4 as corrida             # noqa: E402
from amparo.multimodal import criterios                          # noqa: E402
from amparo.multimodal import enchufe as enchufe_m3              # noqa: E402
from amparo.multimodal import sistema_visual as multimodal       # noqa: E402
from amparo.multimodal import scorecard                          # noqa: E402
from amparo.nucleo import schema                                 # noqa: E402
from autoprueba_agente import ClienteGuionado, IndiceFalso       # noqa: E402

necesita_results = pytest.mark.skipif(
    not (RAIZ / "results" / "m3_scorecard.csv").exists(),
    reason="results/ de M3 no esta en esta copia del repo")

LECTURA_M10 = {"tipo_documento": "notificacion", "entidad": None, "fecha": None,
               "plazo_dias": None,
               "pretension_visible": "Usted cuenta con un plazo de dos semanas habiles"}
LECTURA_M01 = {"tipo_documento": "respuesta_peticion", "entidad": None,
               "fecha": "5 de octubre de 2026", "plazo_dias": None,
               "pretension_visible": "La EPS NIEGA la autorizacion del procedimiento"}


class LectorFalso:
    def __init__(self, js):
        self.js, self.llamadas = js, 0

    def ver(self, imagen, instruccion=None):
        self.llamadas += 1
        return json.dumps(self.js), self.js


class _Transformador:
    def __init__(self):
        self.cache = {"relato viejo": "consulta vieja"}

    def __call__(self, relato):
        return relato


def _m3(tmp_path):
    cliente = ClienteGuionado(
        [[("buscar_normas", '{"consulta": "derecho a la salud cirugia"}')], None])
    return enchufe_m3.construir_responder_m3(
        cliente, indice=IndiceFalso(), transformador=_Transformador(), cache_dir=tmp_path)


# --------------------------------------------------------------------------
# El modulo es el codigo evaluado
# --------------------------------------------------------------------------
def test_el_prompt_es_el_de_la_corrida_oficial():
    """Huellas de VALVULA e INSTRUCCION_DOMINIO tal como estaban en la celda 10
    del notebook en d158742, el commit de la corrida oficial del 2026-10-25.
    Si alguien cambia una coma del prompt, el sistema ya no es el evaluado."""
    h = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
    assert h(multimodal.VALVULA) == "5088a67d1f14b67b360ee649420869acdf21409c6e2a7882bc0b3efe42845e6e"
    assert h(multimodal.INSTRUCCION_DOMINIO) == "2402fa43e09cf84261e9e7d7a199f61811bed70514ef1f54e62b7da678e2072f"


@pytest.mark.parametrize("js, crudo", [
    (LECTURA_M01, "x"), (None, "texto que no es JSON"), ({}, "crudo vacio")])
def test_armar_relato_es_el_del_harness(js, crudo):
    assert multimodal.armar_relato("pregunta", js, crudo) == scorecard.armar_relato("pregunta", js, crudo)


def test_parsear_json():
    assert multimodal.parsear_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert multimodal.parsear_json("sin json") is None
    assert multimodal.parsear_json("{roto") is None


def test_sistema_multimodal_suma_la_lectura_al_relato():
    recibido = []
    salida = multimodal.sistema_multimodal(
        "¿que hago?", "IMAGEN", ver_fn=lambda img: ("crudo", LECTURA_M01),
        responder_m3=lambda r: recibido.append(r) or "ok")
    assert salida == "ok"
    assert recibido[0] == multimodal.armar_relato("¿que hago?", LECTURA_M01, "crudo")
    multimodal.sistema_multimodal("solo texto", None, ver_fn=None,
                                  responder_m3=lambda r: recibido.append(r) or "ok")
    assert recibido[-1] == "solo texto"


# --------------------------------------------------------------------------
# La respuesta en tres bloques
# --------------------------------------------------------------------------
@necesita_results
def test_responder_devuelve_los_tres_bloques(tmp_path):
    responder, ag = _m3(tmp_path)
    amparo = multimodal.Amparo(lector=LectorFalso(LECTURA_M01), responder_m3=responder, agente=ag)
    res = amparo.responder("Me llego esta carta de mi EPS", imagen="IMAGEN")
    assert schema.parse_salida(res["respuesta"]).get("mecanismo") in schema.MECANISMOS
    assert res["por_que"]["regla"] == ag.trazas[-1]["regla"]
    assert res["leido"]["rotulo"] == multimodal.ROTULO_LECTURA
    assert res["leido"]["campos"] == LECTURA_M01
    md = multimodal.formatear(res)
    for bloque in ("### Respuesta", "### Por qué", "### " + multimodal.ROTULO_LECTURA):
        assert bloque in md


@necesita_results
def test_el_caso_de_seguridad_muestra_el_aviso(tmp_path):
    """m10: el VLM escribe un plazo que no esta en el documento. La salida lo
    tiene que marcar, sin cambiar lo que recibe M3."""
    responder, ag = _m3(tmp_path)
    recibido = []
    amparo = multimodal.Amparo(lector=LectorFalso(LECTURA_M10),
                               responder_m3=lambda r: recibido.append(r) or responder(r),
                               agente=ag)
    res = amparo.responder("¿En cuantos dias se me vence el plazo?", imagen="IMAGEN")
    assert res["leido"]["advertencias"] == criterios.advertencias_lectura(LECTURA_M10) != []
    assert "⚠️" in multimodal.formatear(res)
    # El rotulo es de presentacion: el relato es el de la corrida evaluada.
    assert recibido[0] == multimodal.armar_relato("¿En cuantos dias se me vence el plazo?",
                                                  LECTURA_M10, json.dumps(LECTURA_M10))
    assert "no verificado" not in recibido[0]


@necesita_results
def test_sin_imagen_no_hay_bloque_de_lectura(tmp_path):
    responder, ag = _m3(tmp_path)
    lector = LectorFalso(LECTURA_M01)
    res = multimodal.Amparo(lector=lector, responder_m3=responder, agente=ag).responder("solo texto")
    assert res["leido"] is None and lector.llamadas == 0
    assert multimodal.ROTULO_LECTURA not in multimodal.formatear(res)


def test_por_que_traduce_los_ids_a_normas():
    traza = {"regla": "derechos_colectivos", "recuperados": ["CP-088", "X-1", "CP-088"],
             "hechos": {"derecho_colectivo": True, "dano_consumado": False},
             "mecanismo_del_motor": "accion_popular", "no_triable": False}
    pq = multimodal.por_que(traza, {"CP-088": "art. 88 · Constitución Política"})
    assert pq["normas_consultadas"] == ["art. 88 · Constitución Política", "X-1"]
    assert pq["hechos"] == ["derecho_colectivo"]
    md = multimodal.formatear({"respuesta": "Mecanismo: acción popular", "por_que": pq})
    assert "que cerró el caso:** `derechos_colectivos`" in md
    assert "Hechos que la activaron:** `derecho_colectivo`" in md
    assert "El mecanismo lo decide la regla" in md


def test_al_abstenerse_no_muestra_una_regla_que_cerro_el_caso():
    """m10 en la corrida 20261101T194319Z: el extractor marco el caso como no
    triable, pero el motor igual corrio y su regla (`incumplimiento_normativo`)
    aparecia como "la regla que cerro el caso", justo debajo de "prefirio no
    decidir". El hecho lo habia anotado el agente a partir del plazo inventado."""
    traza = {"regla": "incumplimiento_normativo", "recuperados": [],
             "hechos": {"incumplimiento_normativo": True, "titular_pide_lo_suyo": True},
             "mecanismo_del_motor": "accion_cumplimiento", "no_triable": True,
             "motivo_no_triable": "a) no es su caso — es una consulta sobre la fecha y el plazo"}
    md = multimodal.formatear({"respuesta": "Mecanismo: no determinable",
                               "por_que": multimodal.por_que(traza)})
    assert "prefirió no decidir**: a) no es su caso" in md
    assert "Ninguna regla del art. 6" in md
    assert "que cerró el caso:**" not in md and "Hechos que la activaron" not in md
    assert "El mecanismo lo decide la regla" not in md
    assert "sin llegar a una decisión:** `incumplimiento_normativo`, `titular_pide_lo_suyo`" in md
    assert "accion_cumplimiento" not in md


# --------------------------------------------------------------------------
# Vaciar caches y delta repetido (H4)
# --------------------------------------------------------------------------
@necesita_results
def test_vaciar_caches_deja_al_agente_sin_memoria(tmp_path):
    responder, ag = _m3(tmp_path)
    responder("un relato cualquiera")
    assert ag._cache and ag.transformador.cache
    enchufe_m3.vaciar_caches(ag)
    assert ag._cache == {} and ag.transformador.cache == {}


def _eval_repetido(tmp_path):
    casos = tmp_path / "casos.csv"
    casos.write_text("id,pregunta,imagen,esperado,criterio,tipo\n"
                     "a1,pregunta uno,x.png,accion_popular,exacto,normal\n"
                     "a2,pregunta dos,x.png,{\"tipo_documento\": \"oficio\"},campos,normal\n",
                     encoding="utf-8")
    trazas = tmp_path / "trazas.json"
    trazas.write_text(json.dumps({"a1": {"crudo": "c", "js": {"x": 1}, "segundos_ver": 4.0},
                                  "a2": {"crudo": "c", "js": {}}}), encoding="utf-8")
    return casos, trazas


def _bloque(mec):
    return f"Derecho: d\nAccionado: X\nMecanismo: {mec}\nProcedencia: si\nPretension: y"


def test_delta_repetido_exige_vaciar_la_cache(tmp_path):
    casos, trazas = _eval_repetido(tmp_path)
    with pytest.raises(ValueError, match="cache"):
        scorecard.delta_repetido(lambda r: _bloque("accion popular"), repeticiones=3,
                                 ruta_casos=casos, ruta_trazas=trazas,
                                 ruta_salida=tmp_path / "d.json")


def test_delta_repetido_cuenta_por_corrida_y_vacia_antes_de_cada_llamada(tmp_path):
    casos, trazas = _eval_repetido(tmp_path)
    # Sin imagen, M3 acierta solo en la 2a repeticion: la imagen aporta en 2 de 3.
    sin = iter([_bloque("accion de tutela"), _bloque("accion popular"), _bloque("accion de tutela")])
    vaciados = []

    def m3(relato):
        if "DATOS DEL DOCUMENTO ADJUNTO" in relato:
            return _bloque("accion popular")
        return next(sin)

    res = scorecard.delta_repetido(m3, repeticiones=3, vaciar_cache=lambda: vaciados.append(1),
                                   ruta_casos=casos, ruta_trazas=trazas,
                                   ruta_salida=tmp_path / "d.json")
    caso = res["casos"][0]
    assert res["n_casos"] == 1 and len(caso["repeticiones"]) == 3   # solo los `exacto`
    assert (caso["aciertos_con_imagen"], caso["aciertos_sin_imagen"], caso["aporta_en"]) == (3, 1, 2)
    assert "2 de 3" in caso["lectura"]
    assert len(vaciados) == 6                       # antes de cada llamada a M3
    assert res["aciertos_con_imagen"] == "3/3" and res["aciertos_sin_imagen"] == "1/3"
    assert res["mediana_segundos_ver"] == 4.0
    assert caso["mediana_segundos_con_imagen"] >= 4.0          # ver + M3
    assert json.loads((tmp_path / "d.json").read_text(encoding="utf-8"))["repeticiones"] == 3


# El tiempo de ver() registrado aparte lo fija
# test_scorecard.test_cronometro_mide_ver_mas_m3_y_deja_fuera_carga_y_juez.


# --------------------------------------------------------------------------
# Manifiesto de corrida (H3)
# --------------------------------------------------------------------------
@necesita_results
def test_manifiesto_registra_lo_que_atribuye_las_cifras(tmp_path):
    cid, carpeta = corrida.nueva("prueba", base=tmp_path)
    assert carpeta.is_dir() and cid in carpeta.name
    _, ag = _m3(tmp_path)
    man = corrida.manifiesto(cid, vlm_id=multimodal.VLM_ID, vlm_dtype="float16", agente=ag)
    assert man["codigo"]["commit"]                       # el repo es un git
    assert man["m3"]["brazo"] == enchufe_m3.SISTEMA_M3
    assert set(man["eval_set"]) >= {"casos_m4.csv", "imagenes/doc06_notificacion_borrosa.jpg"}
    (carpeta / "scorecard_m4.csv").write_text("id\n", encoding="utf-8")
    ruta = corrida.cerrar(man, carpeta, agente=ag, resumen={"exacto": "3/3"})
    leido = json.loads(ruta.read_text(encoding="utf-8"))
    assert leido["resumen"] == {"exacto": "3/3"} and "scorecard_m4.csv" in leido["archivos"]
    assert "fin_utc" in leido
