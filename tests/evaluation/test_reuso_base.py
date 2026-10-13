"""Reuso del baseline (tools/evaluation/reuso_base.py), en CPU."""
from __future__ import annotations

import copy
import json

import pytest

from tools.evaluation import config
from tools.evaluation.dataset import huella_prompt
from tools.evaluation.reuso_base import motivos_para_no_reusar, reusar_base

V3 = config.PROJECT_ROOT / "results" / "m1_v3_2026-10-12"


def _val():
    regs = [json.loads(l) for l in config.DATASET_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [r for r in regs if r["split"] == "val"]


def _corrida(tmp_path, val, revision=config.BASE_MODEL_REVISION, editar=None):
    filas = [{**v, "generated": "x", "prompt_sistema": huella_prompt(v)} for v in val]
    if editar:
        editar(filas)
    (tmp_path / "base_results.jsonl").write_text(
        "".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas), encoding="utf-8")
    (tmp_path / "corrida.json").write_text(json.dumps({"revision_base": revision}), encoding="utf-8")
    return tmp_path


@pytest.mark.skipif(not V3.exists(), reason="sin la corrida de v3")
def test_el_baseline_de_v3_vale_para_la_validacion_actual():
    """v4 solo cambia respuestas de contrastivos de TRAIN: la validacion, el
    prompt y la revision son los mismos, y el baseline de v3 se puede reusar."""
    motivos, filas = motivos_para_no_reusar(V3, _val(), config.BASE_MODEL_REVISION)
    assert motivos == [] and len(filas) == 334


def test_devuelve_en_el_orden_de_la_validacion(tmp_path):
    val = _val()[:20]
    d = _corrida(tmp_path, list(reversed(val)))
    filas = reusar_base(d, val, config.BASE_MODEL_REVISION)
    assert [f["id"] for f in filas] == [v["id"] for v in val]


def test_otra_revision_no_se_reusa(tmp_path):
    val = _val()[:5]
    assert reusar_base(_corrida(tmp_path, val, revision="otra"), val, config.BASE_MODEL_REVISION) is None


def test_otro_contenido_no_se_reusa(tmp_path):
    """H3: comparar ids no basta, la validacion es intocable en contenido."""
    val = _val()[:5]

    def editar(filas):
        filas[0]["messages"] = copy.deepcopy(filas[0]["messages"])
        filas[0]["messages"][-1]["content"] += " cambiado"
    motivos, _ = motivos_para_no_reusar(_corrida(tmp_path, val, editar=editar), val,
                                        config.BASE_MODEL_REVISION)
    assert any("otro contenido" in m for m in motivos)


def test_otro_prompt_no_se_reusa(tmp_path):
    val = _val()[:5]

    def editar(filas):
        filas[1]["prompt_sistema"] = "otro"
    motivos, _ = motivos_para_no_reusar(_corrida(tmp_path, val, editar=editar), val,
                                        config.BASE_MODEL_REVISION)
    assert any("otro prompt" in m for m in motivos)


def test_faltan_ids_no_se_reusa(tmp_path):
    val = _val()[:5]
    motivos, _ = motivos_para_no_reusar(_corrida(tmp_path, val[:4]), val, config.BASE_MODEL_REVISION)
    assert any("sin baseline" in m for m in motivos)


def test_esquema_viejo_no_se_reusa(tmp_path):
    val = _val()[:3]
    motivos, _ = motivos_para_no_reusar(_corrida(tmp_path, val), val, config.BASE_MODEL_REVISION,
                                        campos={"generated", "campo_nuevo"})
    assert any("esquema anterior" in m for m in motivos)
