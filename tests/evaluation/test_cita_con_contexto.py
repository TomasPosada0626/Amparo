"""La metrica de citas, cuando la respuesta se genero con contexto.

has_invented_citation nacio para M1 sin contexto, donde toda cita salia de la
memoria del modelo. Desde data/dataset_v2.jsonl hay ejemplos CON contexto y ahi
citar es lo correcto: sobre la corrida del 2026-10-09 esa funcion reportaba
89.3 % de citas inventadas en v2 cuando la cifra honesta era 2.9 %.
"""
from __future__ import annotations

from tools.evaluation.domain_metric import (
    cita_no_respaldada,
    has_invented_citation,
    resumen_por_modo,
)

CONTEXTO = [{"cita": "Ley 820 de 2003, Articulo 20", "articulos": ["20"]},
            {"cita": "Ley 820 de 2003, Articulo 18", "articulos": ["18"]}]


def test_sin_contexto_se_comporta_como_la_metrica_vieja():
    """Compatibilidad hacia atras: los 1536 ejemplos de v1 no tienen contexto y
    sus cifras tienen que seguir siendo comparables con las del 2026-10-06."""
    texto = "El articulo 20 de la Ley 820 de 2003 limita el reajuste."

    assert has_invented_citation(texto)
    assert cita_no_respaldada(texto, None)
    assert cita_no_respaldada(texto, [])


def test_citar_un_articulo_del_contexto_no_es_invencion():
    texto = "El articulo 20 de la Ley 820 de 2003 limita el reajuste anual."

    assert has_invented_citation(texto)          # la vieja lo marca
    assert not cita_no_respaldada(texto, CONTEXTO)   # la nueva no


def test_citar_un_articulo_que_no_estaba_si_es_invencion():
    texto = "El articulo 99 de la Ley 820 de 2003 dice otra cosa."

    assert cita_no_respaldada(texto, CONTEXTO)


def test_no_citar_nada_nunca_es_invencion():
    assert not cita_no_respaldada("Acude a un centro de conciliacion.", CONTEXTO)
    assert not cita_no_respaldada("Acude a un centro de conciliacion.", None)


def test_respaldada_no_quiere_decir_correcta():
    """El fallo que destapo la corrida del 2026-10-09: en los casos B2 el
    contexto NO responde la pregunta, el modelo cito igual, y las 25 citas
    dieron 'respaldada' porque el articulo si estaba ahi. La metrica comprueba
    procedencia, no pertinencia; por eso hace falta el corte por modo."""
    texto = "El articulo 18 de la Ley 820 de 2003 limita el canon al 1 %."

    assert not cita_no_respaldada(texto, CONTEXTO)


def test_el_resumen_por_modo_separa_citar_de_citar_cuando_debia():
    registros = [
        {"modo": "B1", "generated": "El articulo 20 de la Ley 820 de 2003 lo limita.",
         "contexto": CONTEXTO},
        {"modo": "B2", "generated": "El articulo 18 de la Ley 820 de 2003 dice algo.",
         "contexto": CONTEXTO},
        {"modo": "B2",
         "generated": "No tengo informacion verificada sobre esto en mi base de conocimiento.",
         "contexto": CONTEXTO},
    ]

    r = resumen_por_modo(registros)

    assert r["B1"] == {"n": 1, "citan": 1, "escapan": 0, "no_respaldadas": 0}
    assert r["B2"]["n"] == 2
    assert r["B2"]["citan"] == 1      # uno cito teniendo contexto que no responde
    assert r["B2"]["escapan"] == 1    # el otro hizo lo correcto


def test_los_registros_sin_modo_no_entran_al_resumen():
    """Los de v1 no tienen modo: el resumen es de la parte con contexto."""
    r = resumen_por_modo([{"generated": "algo", "contexto": None}])

    assert r == {}
