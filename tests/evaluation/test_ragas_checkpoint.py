"""El checkpoint de RAGAS no puede reusar notas de otra corrida.

Es el mismo fallo que M2 corrigio el 2026-10-02 y que volvio a aparecer en
RAGAS: el checkpoint se cargaba por id, sin mirar el contenido evaluado. En la
corrida del 2026-10-07 las tres rutas arrancaron en "30/45" y unos 29 de 45
casos por ruta heredaron las notas de respuestas anteriores -- de otro
adaptador, otro indice y otro prompt.

El fallo es silencioso: no hay excepcion, solo un numero creible calculado sobre
respuestas que el juez nunca leyo. Por eso se vigila con una prueba.
"""
from __future__ import annotations

import json

from tools.evaluation import ragas_metrics


def _registro(id_, respuesta, *, sistema="una_pasada"):
    return {
        "id": id_,
        "sistema": sistema,
        "tipo": "gold",
        "category": "Arriendo",
        "question": "me subieron el arriendo",
        "answer": respuesta,
        "contexts": ["Ley 820 de 2003, Articulo 20: el reajuste tiene tope."],
        "ground_truth": "El reajuste anual tiene un tope.",
    }


def _juez_que_cuenta(llamadas):
    """Juez falso: responde siempre lo mismo y anota cuantas veces lo llamaron."""
    def juez(system, prompt, max_tokens):
        llamadas.append(prompt)
        return ('{"faithfulness": 1.0, "context_precision": 1.0, '
                '"context_recall": 1.0, "preguntas": ["que dice?"]}'), 10
    return juez


def _embed(textos):
    return [[1.0, 0.0] for _ in textos]


def test_una_respuesta_distinta_con_el_mismo_id_se_vuelve_a_calificar(tmp_path):
    """El caso exacto del 2026-10-07: mismo id, otra respuesta, notas heredadas."""
    ck = tmp_path / "ragas.jsonl"

    primera = [_registro(9001, "Segun la Ley 820, el reajuste tiene un tope anual.")]
    llamadas_1 = []
    ragas_metrics.evaluar_corrida(primera, juez=_juez_que_cuenta(llamadas_1),
                                  embed=_embed, checkpoint_path=ck, progress_every=0)
    assert llamadas_1, "la primera corrida tenia que llamar al juez"

    # Misma pregunta y mismo id, pero el modelo (reentrenado) responde otra cosa.
    segunda = [_registro(9001, "No tengo informacion verificada sobre esto.")]
    llamadas_2 = []
    filas = ragas_metrics.evaluar_corrida(segunda, juez=_juez_que_cuenta(llamadas_2),
                                          embed=_embed, checkpoint_path=ck, progress_every=0)

    assert llamadas_2, (
        "reuso las notas de la respuesta anterior: el juez nunca leyo la respuesta nueva")
    assert len(filas) == 1
    assert filas[0]["huella"] == ragas_metrics.huella_de(segunda[0])


def test_la_misma_respuesta_si_se_reusa_y_no_gasta_juez(tmp_path):
    """La otra mitad: el checkpoint tiene que seguir sirviendo para lo que
    existe -- retomar una corrida cortada por cupo sin volver a pagar."""
    ck = tmp_path / "ragas.jsonl"
    registros = [_registro(9001, "Segun la Ley 820, el reajuste tiene un tope anual.")]

    llamadas_1 = []
    ragas_metrics.evaluar_corrida(registros, juez=_juez_que_cuenta(llamadas_1),
                                  embed=_embed, checkpoint_path=ck, progress_every=0)
    llamadas_2 = []
    filas = ragas_metrics.evaluar_corrida(registros, juez=_juez_que_cuenta(llamadas_2),
                                          embed=_embed, checkpoint_path=ck, progress_every=0)

    assert llamadas_2 == [], "volvio a llamar al juez por una respuesta identica"
    assert len(filas) == 1


def test_la_clave_distingue_la_misma_pregunta_en_rutas_distintas(tmp_path):
    """El mismo caso se evalua en una_pasada y una_pasada_dspy. Si la clave
    fuera solo el id, la segunda ruta heredaria las notas de la primera."""
    ck = tmp_path / "ragas.jsonl"
    una = [_registro(9001, "Respuesta de una pasada.", sistema="una_pasada")]
    una_pasada_dspy = [_registro(9001, "Respuesta con DSPy.", sistema="una_pasada_dspy")]

    ragas_metrics.evaluar_corrida(una, juez=_juez_que_cuenta([]), embed=_embed,
                                  checkpoint_path=ck, progress_every=0)
    llamadas = []
    ragas_metrics.evaluar_corrida(una_pasada_dspy, juez=_juez_que_cuenta(llamadas), embed=_embed,
                                  checkpoint_path=ck, progress_every=0)

    assert llamadas, "la ruta una_pasada_dspy heredo las notas de una_pasada"
    claves = {json.loads(l)["id"] for l in ck.read_text(encoding="utf-8").splitlines() if l.strip()}
    assert claves == {"una_pasada:9001", "una_pasada_dspy:9001"}
