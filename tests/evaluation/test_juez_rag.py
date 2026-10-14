"""El juez del RAG tiene que ver lo que vio el modelo y dejarle citar.

El juez de M2 no veia los fragmentos y castigaba toda cita "sin verificar": en
el RAG eso es castigar lo que se le pide. Estas pruebas vigilan que el prompt
lleve los fragmentos y la regla de citas, que la huella cambie si cambian los
fragmentos, y que el juez de M2 siga igual (mismas huellas: sus checkpoints
siguen valiendo).
"""
from __future__ import annotations

import json
from types import SimpleNamespace

from tools.evaluation import criterio, eval_set, juez_rag
from tools.evaluation.checkpoint import huella

VEREDICTO_OK = '{"veredicto": "cumple", "errores_juridicos": [], "justificacion": "ok"}'


def _juez_falso(respuesta=VEREDICTO_OK):
    vistos: list[tuple[str, str]] = []

    def generar(system_prompt, prompt, max_tokens):
        vistos.append((system_prompt, prompt))
        return respuesta

    return generar, vistos


def _record(registro, respuesta="Segun el articulo 20 de la Ley 820 de 2003, puedes reclamar.",
            contextos=("Articulo 20. Reajuste del canon de arrendamiento ...",)):
    return {"id": registro["id"], "question": registro["messages"][1]["content"], "answer": respuesta,
            "contexts": list(contextos),
            "retrieved_chunks": [{"cita": "Ley 820 de 2003 (Arrendamiento), Articulo 20"} for _ in contextos]}


def test_el_prompt_lleva_los_fragmentos_la_guia_y_la_regla_de_citas():
    registro = eval_set.load_eval_set()[0]
    juez, vistos = _juez_falso()

    juez_rag.evaluar([_record(registro)], [registro], juez, label="A", progress_every=0)

    system, prompt = vistos[0]
    assert system == juez_rag.JUEZ_RAG_SYSTEM_PROMPT
    assert "[1] Ley 820 de 2003 (Arrendamiento), Articulo 20" in prompt
    assert "Reajuste del canon" in prompt
    assert registro["criterio"][:60] in prompt
    assert "Citar articulos de los fragmentos que aplican a la pregunta esta bien" in prompt
    assert "no cite numeros de norma" in prompt      # la excepcion a los criterios escritos sin RAG


def test_estar_en_los_fragmentos_no_hace_pertinente_una_cita():
    """La version rag-2026-10-14 solo castigaba la cita que no estaba en los
    fragmentos: una de los fragmentos que no aplicaba pasaba como buena (9063:
    bonos pensionales para una pregunta por el valor de la pension)."""
    registro = eval_set.load_eval_set()[0]
    g = juez_rag.generaciones([_record(registro)], "A")[0]
    prompt = juez_rag._prompt(g, registro)
    assert "NO aplica a la pregunta es un error AUNQUE aparezca en los fragmentos" in prompt
    assert "omite algo esencial" in prompt
    assert juez_rag.JUEZ_RAG_PROMPT_VERSION != "rag-2026-10-14"   # la huella cambia: nada se reusa del juez viejo


def test_sin_fragmentos_el_juez_lo_sabe():
    assert "no recibio ningun fragmento" in juez_rag.formatear_fragmentos({"contexts": []})


def test_la_huella_cambia_si_cambian_los_fragmentos():
    registro = eval_set.load_eval_set()[0]
    a = juez_rag.generaciones([_record(registro)], "A")[0]
    b = juez_rag.generaciones([_record(registro, contextos=("otro fragmento",))], "A")[0]
    assert juez_rag._huella(a, registro) != juez_rag._huella(b, registro)


def test_el_checkpoint_evita_volver_a_llamar_al_juez(tmp_path):
    registros = eval_set.load_eval_set()[:3]
    records = [_record(r) for r in registros]
    ck = tmp_path / "ck.jsonl"
    juez, vistos = _juez_falso()
    juez_rag.evaluar(records, registros, juez, label="A", checkpoint_path=ck, progress_every=0)
    assert len(vistos) == 3

    juez2, vistos2 = _juez_falso()
    v = juez_rag.evaluar(records, registros, juez2, label="A", checkpoint_path=ck, progress_every=0)
    assert vistos2 == [] and [x.veredicto for x in v] == ["cumple"] * 3


def test_el_resumen_es_el_de_siempre():
    registros = eval_set.load_eval_set()[:2]
    juez, _ = _juez_falso('{"veredicto": "parcial", "errores_juridicos": ["x"], "justificacion": "j"}')
    v = juez_rag.evaluar([_record(r) for r in registros], registros, juez, label="A", progress_every=0)
    res = criterio.resumen(v)
    total = sum(r["parcial"] for r in res["A"].values())
    assert total == 2


def test_el_juez_de_m2_no_cambia():
    """Mismo prompt y misma huella que antes de existir juez_rag: los checkpoints
    de M2 siguen valiendo y M2 se mide igual."""
    registro = eval_set.load_eval_set()[0]
    g = SimpleNamespace(id=registro["id"], query="q", generated="r", label="m2")
    juez, vistos = _juez_falso()

    criterio.evaluar_contra_criterio([g], [registro], juez, progress_every=0)

    system, prompt = vistos[0]
    assert system == criterio.CRITERIO_SYSTEM_PROMPT
    assert prompt == criterio.build_criterio_prompt("q", registro["criterio"], registro["tipo"], "r")


def test_el_juez_de_m2_conserva_sus_huellas(tmp_path):
    registro = eval_set.load_eval_set()[0]
    g = SimpleNamespace(id=registro["id"], query="q", generated="r", label="m2")
    ck = tmp_path / "ck.jsonl"
    criterio.evaluar_contra_criterio([g], [registro], _juez_falso()[0], checkpoint_path=ck, progress_every=0)
    fila = json.loads(ck.read_text(encoding="utf-8").splitlines()[0])
    assert fila["huella"] == huella(criterio.CRITERIO_PROMPT_VERSION, "q", registro["criterio"], "r")
