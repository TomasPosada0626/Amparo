"""La calibracion tiene que juzgar la RESPUESTA DE REFERENCIA, no otra cosa.

Si por un error tomara la pregunta, o la respuesta de alguno de los modelos, el
numero que saldria seguiria pareciendo una calibracion creible y no lo seria:
diria que la vara esta bien cuando no se ha medido la vara. El fallo seria
silencioso, asi que se vigila con una prueba.
"""
from __future__ import annotations

from tools.evaluation import calibrar_criterios, criterio, eval_set


def _juez_falso(respuesta_fija: str):
    """Devuelve siempre el mismo veredicto y registra que prompts recibio."""
    vistos: list[str] = []

    def generar(system_prompt: str, prompt: str, max_tokens: int) -> str:
        vistos.append(prompt)
        return respuesta_fija

    return generar, vistos


def test_califica_la_respuesta_de_referencia_de_cada_caso():
    registros = eval_set.load_eval_set()
    refs = calibrar_criterios.generaciones_de_referencia(registros)

    assert len(refs) == len(registros)
    for generacion, registro in zip(refs, registros):
        assert generacion.id == registro["id"]
        assert generacion.query == registro["messages"][1]["content"]
        assert generacion.generated == registro["messages"][2]["content"], (
            f"el caso {registro['id']} no esta calificando su respuesta de referencia"
        )


def test_el_label_distingue_la_calibracion_de_un_modelo():
    """En el resumen conviven baseline, fine_tuned y esta fila. Si compartieran
    label, la calibracion se mezclaria con un modelo y nadie lo notaria."""
    refs = calibrar_criterios.generaciones_de_referencia(eval_set.load_eval_set())
    assert {g.label for g in refs} == {"referencia"}
    assert calibrar_criterios.LABEL not in ("baseline", "fine_tuned")


def test_el_prompt_del_juez_lleva_el_criterio_y_la_referencia():
    registros = eval_set.load_eval_set()[:3]
    refs = calibrar_criterios.generaciones_de_referencia(registros)
    juez, vistos = _juez_falso(
        '{"veredicto": "cumple", "errores_juridicos": [], "justificacion": "ok"}')

    criterio.evaluar_contra_criterio(refs, registros, juez, progress_every=0)

    assert len(vistos) == len(registros)
    for prompt, registro in zip(vistos, registros):
        assert registro["criterio"][:60] in prompt, "el prompt no lleva el criterio del caso"
        assert registro["messages"][2]["content"][:60] in prompt, (
            "el prompt no lleva la respuesta de referencia"
        )


def test_un_veredicto_negativo_sale_en_el_informe():
    """El informe existe para listar los criterios a revisar: si una referencia
    no cumple su propio criterio, tiene que verse."""
    registros = eval_set.load_eval_set()[:2]
    refs = calibrar_criterios.generaciones_de_referencia(registros)
    juez, _ = _juez_falso(
        '{"veredicto": "no_cumple", "errores_juridicos": [], '
        '"justificacion": "el criterio exige algo que la referencia no hace"}')

    veredictos = criterio.evaluar_contra_criterio(refs, registros, juez, progress_every=0)
    texto = calibrar_criterios.informe(criterio.resumen(veredictos), veredictos)

    assert "Criterios a revisar" in texto
    assert str(registros[0]["id"]) in texto
    assert "cumple 0 %" in texto
