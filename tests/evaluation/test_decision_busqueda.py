"""La decision de busqueda de M3 (regla fijada antes de correr)."""
from __future__ import annotations

import re

from tools.evaluation import config
from tools.evaluation import decision_busqueda as db


def _r(f, ar, cp, cr):
    return {"faithfulness": f, "answer_relevancy": ar, "context_precision": cp, "context_recall": cr}


def test_c_se_adopta_si_sube_la_media_sin_bajar_de_mas():
    d = db.decidir({db.A: _r(0.50, 0.34, 0.56, 0.39), db.C: _r(0.54, 0.33, 0.60, 0.42)})
    assert d["elegida"] == db.C


def test_si_una_metrica_baja_mas_de_la_tolerancia_se_queda_a():
    """Como en la corrida del 2026-10-09: C subia context precision pero bajaba
    answer relevancy de 0,34 a 0,32 y context recall de 0,39 a 0,35."""
    d = db.decidir({db.A: _r(0.5099, 0.3368, 0.5582, 0.3944), db.C: _r(0.5412, 0.3201, 0.6029, 0.3519)})
    assert d["elegida"] == db.A and "baja" in d["motivo"]


def test_si_no_sube_la_media_se_queda_a():
    d = db.decidir({db.A: _r(0.5, 0.5, 0.5, 0.5), db.C: _r(0.5, 0.5, 0.5, 0.49)})
    assert d["elegida"] == db.A


def test_con_datos_incompletos_se_queda_a():
    assert db.decidir({})["elegida"] == db.A
    assert db.decidir({db.A: _r(0.5, 0.5, 0.5, 0.5)})["elegida"] == db.A
    d = db.decidir({db.A: _r(0.5, 0.5, 0.5, 0.5), db.C: _r(0.9, None, 0.9, 0.9)})
    assert d["elegida"] == db.A


def test_la_tolerancia_es_la_del_plan_escrito():
    plan = (config.PROJECT_ROOT / "docs" / "m3_plan_colab_2026-10-13.md").read_text(encoding="utf-8")
    assert re.search(r"baja más de 0,03", plan)
    assert db.TOLERANCIA == 0.03


def test_generaciones_rag_tiene_la_forma_del_juez_de_criterio():
    recs = [{"id": 9001, "question": "q", "answer": "a", "contexts": []}]
    g = db.generaciones_rag(recs, "C_rerank")[0]
    assert (g.id, g.query, g.generated, g.label) == (9001, "q", "a", "C_rerank")
