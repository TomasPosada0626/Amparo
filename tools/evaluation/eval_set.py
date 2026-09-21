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
