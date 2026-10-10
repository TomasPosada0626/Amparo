"""La guardia de entidades no debe marcar lo que el dataset ya tiene revisado.

La propiedad que importa es la tasa de falsos positivos: la lista blanca es
incompleta por naturaleza, asi que la unica forma de que la cifra sirva para
comparar baseline contra afinado es que no marque entidades reales. Las
respuestas de referencia de data/dataset_legal.jsonl son el patron de oro
disponible (se revisaron una por una al construir el dataset), asi que si la
guardia marca alguna, le falta una entidad a la lista blanca.

Este test ya hizo su trabajo una vez: la primera version marcaba el 11.4% del
dataset porque vigilaba usos genericos ("la Procuraduria", "un recurso",
"presenta una querella ante la Inspeccion") y la palabra "certificado", que en
espanol produce infinitos nombres legitimos.
"""
from __future__ import annotations

import json

from tools.evaluation import dataset as _dataset
from tools.evaluation import config
from tools.evaluation.entity_metric import (
    find_fabricated_entities,
    has_fabricated_entity,
)


def _respuestas_del_dataset() -> list[tuple[int, str]]:
    registros = _dataset.load_records()
    return [(r["id"], r["messages"][2]["content"]) for r in registros]


def test_cero_falsos_positivos_en_el_dataset():
    marcadas = [
        (id_, find_fabricated_entities(texto))
        for id_, texto in _respuestas_del_dataset()
        if has_fabricated_entity(texto)
    ]
    assert marcadas == [], (
        "La guardia marco respuestas de referencia, que son entidades reales ya "
        f"revisadas: {marcadas[:5]}. Agrega la entidad que falta a "
        "ENTIDADES_REALES en vez de reescribir la respuesta."
    )


def test_detecta_las_entidades_inventadas_de_la_corrida_del_2026_10_05():
    """Casos reales de la corrida, no inventados para el test."""
    for texto in (
        "puedes reclamar ante la Superintendencia de Pensiones",   # no existe
        "acude a la Comisaria de Policia mas cercana",             # es Inspeccion de Policia
        "avisa a la Defensoria del Nino",                          # es ICBF / Defensor de Familia
        "radica una querella de omision ante la Procuraduria",     # la figura no existe
        "preguntalo en la Secretaria de Interior",                 # es Ministerio del Interior
        "la Inspeccion general de trabajo puede sancionar",        # es Inspeccion del Trabajo
        "presenta un recurso de amparo",                           # figura no colombiana
    ):
        assert has_fabricated_entity(texto), f"no detecto la entidad inventada: {texto!r}"


def test_no_marca_el_uso_generico_ni_las_entidades_reales():
    for texto in (
        "presenta una querella ante la Inspeccion del Trabajo",
        "puedes quejarte en la Procuraduria",
        "interpon un recurso de reposicion",
        "pide el certificado de tradicion y libertad",
        "pide el certificado de la camara de comercio",
        "reclama en la Superintendencia de Industria y Comercio",
        "la Superintendencia Financiera vigila a los bancos",
        "acude a la Comisaria de Familia",
        "consulta en la secretaria del juzgado",
        "el Ministerio de Salud y Proteccion Social lo regula",
    ):
        assert not has_fabricated_entity(texto), (
            f"marco como inventada una entidad real o un uso generico: {texto!r}"
        )
