"""La prueba barata de un candidato (tools/evaluation/prueba_barata.py), en CPU."""
from __future__ import annotations

import json
import re

import pytest

from tools.evaluation import config
from tools.evaluation import prueba_barata as pb

RAIZ = config.PROJECT_ROOT
PROTOCOLO = RAIZ / "docs" / "m1_protocolo_aceptacion.md"
ESC = RAIZ / "results" / "m1_escenarios_2026-10-12"
GOLD = RAIZ / "results" / "m1_gold_c6_2026-10-12"


def _tabla_del_protocolo() -> dict[str, tuple[str, int, int]]:
    """{fila: (operador, umbral, v1)} de la tabla de la prueba barata."""
    texto = PROTOCOLO.read_text(encoding="utf-8")
    seccion = texto.split("### La prueba barata de un candidato nuevo", 1)[1].split("\n### ", 1)[0]
    filas = {}
    for linea in seccion.splitlines():
        # "**0**" sin signo es "ninguno": se lee como <= 0
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*([\d/]+)\s*\|\s*[\d/]+\s*\|\s*\*\*([≤≥])?\s*(\d+)", linea)
        if m:
            fila, v1, op, umbral = m.groups()
            filas[fila] = (">=" if op == "≥" else "<=", int(umbral), int(v1.split("/")[0]))
    return filas


def test_los_umbrales_son_los_del_protocolo():
    """Los umbrales se fijaron en el protocolo antes de v4; el codigo no puede
    decir otra cosa sin que esto falle."""
    tabla = _tabla_del_protocolo()
    assert len(tabla) == len(pb.CRITERIOS) == 6
    nombres_protocolo = {
        "suficiente: se abstiene": "suficiente: se abstiene",
        "suficiente: cita el articulo que responde": "suficiente: cita el artículo que responde",
        "parcial: dice que falta": "parcial: dice que falta",
        "irrelevante: se abstiene": "irrelevante: se abstiene",
        "irrelevante: cita sin respaldo": "irrelevante: cita sin respaldo",
        "gold con RAG real: abstencion pura": "gold con RAG real: abstención pura",
    }
    for nombre, _, _, op, umbral, ref in pb.CRITERIOS:
        assert tabla[nombres_protocolo[nombre]] == (op, umbral, ref), nombre


@pytest.mark.skipif(not ESC.exists() or not GOLD.exists(), reason="sin resultados del 2026-10-12")
def test_v3_no_la_habria_pasado():
    """El protocolo afirma que v3 la habria fallado. Se comprueba con sus datos."""
    r = pb.informe(ESC / "v3_20261012-9a8096d7", GOLD / "v3_20261012-af4852fc")
    assert not r["problemas"] and not r["pasa"]
    fallan = {f["fila"] for f in r["filas"] if not f["cumple"]}
    assert fallan == {"suficiente: se abstiene", "suficiente: cita el articulo que responde",
                      "gold con RAG real: abstencion pura"}


@pytest.mark.skipif(not ESC.exists() or not GOLD.exists(), reason="sin resultados del 2026-10-12")
def test_el_control_v1_coincide_con_su_referencia():
    esc = pb._resumen(ESC / "v1_20261012-686e5bca")
    gold = pb._resumen(GOLD / "v1_20261012-cfcfc6a4")
    assert pb.comparar_control(esc, gold) == []


def _escribir(d, resumen, revision=config.BASE_MODEL_REVISION):
    d.mkdir(parents=True)
    (d / "resumen.json").write_text(json.dumps(resumen), encoding="utf-8")
    (d / "corrida.json").write_text(json.dumps({"revision_base": revision}), encoding="utf-8")
    return d


ESC_OK = {"huella_escenarios": pb.HUELLA_ESCENARIOS, "huella_adaptador": "aaaa",
          "suficiente_se_abstiene": "5/55", "suficiente_cita_el_oraculo": "40/55",
          "parcial_dice_que_falta": "12/13", "irrelevante_se_abstiene": "30/49",
          "irrelevante_cita_sin_respaldo": 0}
GOLD_OK = {"huella_adaptador": "aaaa", "abstencion_pura": "8/45",
           "revision_base": config.BASE_MODEL_REVISION, "buscador": {"piso": 0.81}}


def test_un_candidato_que_cumple_las_seis_pasa(tmp_path):
    r = pb.informe(_escribir(tmp_path / "e", ESC_OK), _escribir(tmp_path / "g", GOLD_OK))
    assert r["pasa"] and not r["problemas"]


def test_basta_una_fila_para_no_pasar(tmp_path):
    esc = {**ESC_OK, "suficiente_se_abstiene": "7/55"}
    r = pb.informe(_escribir(tmp_path / "e", esc), _escribir(tmp_path / "g", GOLD_OK))
    assert not r["pasa"]


@pytest.mark.parametrize("cambio,donde", [
    ({"huella_escenarios": "otra"}, "esc"),
    ({"huella_adaptador": "bbbb"}, "gold"),
    ({"revision_base": "otra"}, "gold"),
])
def test_una_medicion_que_no_es_la_del_protocolo_no_se_juzga(tmp_path, cambio, donde):
    esc = {**ESC_OK, **(cambio if donde == "esc" else {})}
    gold = {**GOLD_OK, **(cambio if donde == "gold" else {})}
    r = pb.informe(_escribir(tmp_path / "e", esc), _escribir(tmp_path / "g", gold))
    assert r["problemas"] and not r["pasa"]


def test_escenarios_con_otra_revision_no_se_juzga(tmp_path):
    r = pb.informe(_escribir(tmp_path / "e", ESC_OK, revision="otra"), _escribir(tmp_path / "g", GOLD_OK))
    assert r["problemas"] and not r["pasa"]


def test_candidato_y_control_con_buscadores_distintos_no_se_juzga(tmp_path):
    ctrl_esc = {**ESC_OK, "huella_adaptador": "8ce3cc2bc9306974"}
    ctrl_gold = {**GOLD_OK, "huella_adaptador": "8ce3cc2bc9306974", "buscador": {"piso": 0.82}}
    r = pb.informe(_escribir(tmp_path / "e", ESC_OK), _escribir(tmp_path / "g", GOLD_OK),
                   _escribir(tmp_path / "ce", ctrl_esc), _escribir(tmp_path / "cg", ctrl_gold))
    assert any("buscador distinto" in p for p in r["problemas"]) and not r["pasa"]


def test_acepta_el_directorio_padre_con_una_sola_corrida(tmp_path):
    _escribir(tmp_path / "e" / "20261014-xxxx", ESC_OK)
    assert pb._resumen(tmp_path / "e")["huella_adaptador"] == "aaaa"


def test_las_filas_de_abstencion_ya_no_deciden(tmp_path):
    """Decision de Tomas del 2026-10-13: cuanto se abstiene no es criterio. Un
    candidato que se abstiene poco en irrelevante y mucho en gold pasa si
    responde bien con contexto suficiente y no inventa citas."""
    esc = {**ESC_OK, "irrelevante_se_abstiene": "5/49"}
    gold = {**GOLD_OK, "abstencion_pura": "30/45"}
    r = pb.informe(_escribir(tmp_path / "e", esc), _escribir(tmp_path / "g", gold))
    assert r["pasa"]
    informativas = {f["fila"] for f in r["filas"] if not f["decide"]}
    assert informativas == pb.INFORMATIVAS


def test_el_protocolo_dice_que_filas_ya_no_deciden():
    texto = PROTOCOLO.read_text(encoding="utf-8")
    nota = texto.split("Desde el 2026-10-13 (decisión de Tomás", 1)[1].split("\n\n", 1)[0]
    assert "irrelevante: se abstiene" in nota and "abstención pura" in nota
