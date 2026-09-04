"""Carga y split estratificado del dataset legal.

Replica EXACTA de la celda 7 de colab/baseline_finetune.ipynb (M1): agrupa
por categoria (orden de primera aparicion), baraja cada grupo con un RNG
local sembrado (bit-identico a random.seed(seed)+random.shuffle del
notebook), separa max(1, round(len(items)*val_fraction)) por categoria, y
al final baraja train/val una vez cada uno -- en ese orden. No cambiar el
numero ni el orden de las llamadas a rng.shuffle(): eso rompe la
reproducibilidad byte-a-byte del split ya usado para el baseline publicado
en la wiki (3.4% / 17.7% de similitud).
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from random import Random

from tools.evaluation import config


def load_records(path: Path = config.LOCAL_DATASET_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def system_prompt(records: list[dict]) -> str:
    return records[0]["messages"][0]["content"]


def stratified_split(
    records: list[dict],
    val_fraction: float = config.VAL_FRACTION,
    seed: int = config.RANDOM_SEED,
) -> tuple[list[dict], list[dict]]:
    rng = Random(seed)

    by_category: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_category[record["category"]].append(record)

    train_records: list[dict] = []
    val_records: list[dict] = []
    for _category, items in by_category.items():
        items = items[:]
        rng.shuffle(items)
        n_val = max(1, round(len(items) * val_fraction))
        val_records.extend(items[:n_val])
        train_records.extend(items[n_val:])

    rng.shuffle(train_records)
    rng.shuffle(val_records)
    return train_records, val_records
