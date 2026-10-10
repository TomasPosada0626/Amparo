"""Carga y split estratificado del dataset legal.

Replica EXACTA de la celda 7 de colab/m1_finetune.ipynb (M1): agrupa
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


def _leer(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_records(path: Path = config.DATASET_PATH, origen: str | None = "v1") -> list[dict]:
    """Los ejemplos sin contexto (origen v1): los 1536 del dataset legal.

    `origen` filtra el unico dataset. Antes esto leia data/dataset_legal.jsonl,
    que ya no existe como archivo aparte; v3 lo contiene verbatim, asi que
    filtrar por origen devuelve los mismos 1536 registros con los mismos
    campos. Con origen=None devuelve los 2709.
    """
    registros = _leer(path)
    if origen is None:
        return registros
    return [r for r in registros if r.get("origen") == origen]


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


def load_records_v2(path: Path = config.DATASET_PATH) -> list[dict]:
    """Los ejemplos CON contexto (origen v2): los 755 de tools/dataset_v2.py.

    No incluye las 418 variantes contrastivas (origen `contrastivo`): son
    ejemplos de entrenamiento derivados, no parte de la fuente revisada.
    """
    if not path.exists():
        return []
    return load_records(path, origen="v2")


def split_v2(
    records_v2: list[dict],
    records_m1: list[dict],
    val_fraction: float = config.VAL_FRACTION,
    seed: int = config.RANDOM_SEED,
) -> tuple[list[dict], list[dict]]:
    """Particion de data/dataset_v2.jsonl SIN mover el split de M1.

    - Un ejemplo con pregunta base (`base_id`) cae del mismo lado que su base en
      el split de M1: si la misma pregunta estuviera sin contexto en train y con
      contexto en val, val mediria memoria.
    - Uno sin base se reparte estratificado por (categoria, modo), con el mismo
      metodo y semilla que stratified_split.
    data/dataset_legal.jsonl se sigue partiendo con stratified_split, intacto:
    asi la validacion de modo A es la misma de M2 del 2026-10-06."""
    _, val_m1 = stratified_split(records_m1, val_fraction, seed)
    ids_val = {r["id"] for r in val_m1}

    train, val, sin_base = [], [], []
    for r in records_v2:
        if r.get("base_id") is None:
            sin_base.append(r)
        elif r["base_id"] in ids_val:
            val.append(r)
        else:
            train.append(r)

    rng = Random(seed)
    grupos: dict = defaultdict(list)
    for r in sin_base:
        grupos[(r["category"], r.get("modo", ""))].append(r)
    for _clave, items in sorted(grupos.items()):
        items = items[:]
        rng.shuffle(items)
        n_val = round(len(items) * val_fraction)
        val.extend(items[:n_val])
        train.extend(items[n_val:])
    train.sort(key=lambda r: r["id"])
    val.sort(key=lambda r: r["id"])
    return train, val
