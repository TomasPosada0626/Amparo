"""El conjunto de confirmacion tiene que ser nuevo y medible.

Si una pregunta repite una de las 45 gold o del entrenamiento, deja de confirmar
nada; si su articulo gold no esta en el indice, el acierto@k no se puede medir.
"""
from __future__ import annotations

import json

import pytest

from tools.evaluation import preguntas_confirmacion as pc
from tools.rag import config as rag_config


def test_el_conjunto_actual_no_tiene_problemas_de_forma_ni_de_parecido():
    assert pc.problemas(pc.cargar()) == []


@pytest.mark.skipif(not rag_config.FAISS_METADATA_PATH.exists(), reason="el indice no esta en artifacts/")
def test_cada_articulo_gold_existe_en_el_indice():
    assert pc.problemas(pc.cargar(), rag_config.FAISS_METADATA_PATH) == []


def test_el_gold_tiene_la_forma_de_auditoria_61():
    g = pc.gold()
    assert g["9501"] == {"servicios_publicos_domiciliarios_ley_142_1994": {"158"}}
    assert all(isinstance(arts, set) for normas in g.values() for arts in normas.values())


def test_una_pregunta_copiada_se_detecta():
    eval_set = json.loads(pc.EVAL_SET.read_text(encoding="utf-8"))
    copia = dict(pc.cargar()[0], messages=eval_set[0]["messages"])
    assert any("se parece a eval_set" in p for p in pc.problemas([copia]))


def test_un_id_del_eval_set_se_detecta():
    caso = dict(pc.cargar()[0], id=9001)
    assert any("ya usa el eval set" in p for p in pc.problemas([caso]))


def test_un_articulo_que_no_existe_se_detecta(tmp_path):
    meta = tmp_path / "meta.jsonl"
    meta.write_text(json.dumps({"doc_id": "servicios_publicos_domiciliarios_ley_142_1994",
                                "articulos_incluidos": ["1"]}) + "\n", encoding="utf-8")
    p = pc.problemas(pc.cargar()[:1], meta)
    assert any("no tiene en el indice" in x for x in p)


def test_parecido_ignora_tildes_y_mayusculas():
    assert pc.parecido("¿Qué PASA con mi reclamo?", "que pasa con mi reclamo") == 1.0
