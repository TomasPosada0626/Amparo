"""Carga del eval set propio de M2 (data/eval_set.json): ejemplos gold
escritos a mano (no sacados del dataset de entrenamiento/validacion de M1)
mas casos adversariales, cada uno con un campo 'criterio' explicito que
describe que debe/no debe hacer la respuesta -- no solo que tan parecida es
al texto de referencia. Mismo esquema que data/dataset_legal.jsonl
(messages: system/user/assistant) para poder reusar
generation.generate_batch sin cambios.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.evaluation import config

EVAL_SET_PATH = config.PROJECT_ROOT / "data" / "eval_set.json"

REQUIRED_FIELDS = ("id", "category", "tipo", "criterio", "messages")
VALID_TIPOS = ("gold", "adversarial")


def load_eval_set(path: Path = EVAL_SET_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        records: list[dict] = json.load(f)
    return records


def gold_examples(records: list[dict]) -> list[dict]:
    return [r for r in records if r["tipo"] == "gold"]


def adversarial_examples(records: list[dict]) -> list[dict]:
    return [r for r in records if r["tipo"] == "adversarial"]


def _normalizar_pregunta(texto: str) -> str:
    import re
    import unicodedata

    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


def solapamiento(eval_records: list[dict], train_records: list[dict], val_records: list[dict]) -> dict:
    """Ids del eval set cuya pregunta (normalizada) aparece en train o en val.

    En train seria fuga: el modelo habria visto la pregunta con su respuesta.
    En val no es fuga, pero esos casos no son "propios": repiten preguntas de
    la validacion de M1. Al 2026-10-04, 20 de las 50 gold (9011-9030) son copia
    literal de preguntas de validacion y ninguna esta en train."""
    def preguntas(rs):
        return {_normalizar_pregunta(r["messages"][1]["content"]) for r in rs}

    en_train, en_val = preguntas(train_records), preguntas(val_records)
    salida = {"en_train": [], "en_val": []}
    for r in eval_records:
        q = _normalizar_pregunta(r["messages"][1]["content"])
        if q in en_train:
            salida["en_train"].append(r["id"])
        elif q in en_val:
            salida["en_val"].append(r["id"])
    return salida
