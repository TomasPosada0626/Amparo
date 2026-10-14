"""El acierto del paso 7 se mide sobre lo que el modelo RECIBIO, no sobre una re-busqueda."""
from __future__ import annotations

import json

from tools.evaluation import evaluar_paso7 as ep


def _rec(cid, chunks, tipo="gold"):
    return {"id": cid, "tipo": tipo, "answer": "x", "retrieved_chunks": [{"chunk_id": c} for c in chunks]}


POR_CHUNK = {"c1": ("ley820", ["20"]), "c2": ("cst", ["64"]), "c3": ("ley820", ["16"])}


def test_cuenta_el_articulo_gold_entre_los_primeros_k():
    et = {"1": {"ley820": {"16"}}, "2": {"cst": {"64"}}}
    recs = [_rec(1, ["c1", "c3"]), _rec(2, ["c1"])]
    r = ep.acierto(recs, et, POR_CHUNK)
    assert (r["aciertos"], r["de"], r["ids"]) == (1, 2, ["1"])


def test_fuera_de_los_primeros_k_no_cuenta():
    et = {"1": {"ley820": {"16"}}}
    assert ep.acierto([_rec(1, ["c1", "c3"])], et, POR_CHUNK, k=1)["aciertos"] == 0


def test_la_norma_correcta_con_otro_articulo_no_es_acierto():
    """Es justo el fallo que diagnostico el paso 7: la ley correcta, el articulo no."""
    et = {"1": {"ley820": {"16"}}}
    assert ep.acierto([_rec(1, ["c1"])], et, POR_CHUNK)["aciertos"] == 0


def test_lee_los_jsonl_de_la_corrida(tmp_path):
    (tmp_path / "eval_records_R_confirmacion.jsonl").write_text(
        json.dumps(_rec(9501, ["c1"])) + "\n", encoding="utf-8")
    assert ep.cargar(tmp_path, "R", "confirmacion")[0]["id"] == 9501
    assert ep.cargar(tmp_path, "R_servicio", "confirmacion") is None
    assert len(ep.cargar(tmp_path, "A", "eval_set")) == 75     # A sale de S10 del 2026-10-14
