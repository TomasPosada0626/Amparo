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
    """El system prompt UNICO de un grupo de registros. Falla si hay mas de uno.

    **Por que falla en vez de devolver el primero.** El dataset tiene dos prompts
    a proposito: uno sin contexto y otro, para los ejemplos con contexto, que
    agrega las reglas del CONTEXTO y la orden de abstenerse. El notebook de M1
    tomaba `records[0]` para generar las 334 respuestas de validacion, y los 103
    con contexto -- los 35 B2 entre ellos -- se evaluaron **sin la orden de
    abstenerse** en las corridas del 2026-10-09. Devolver el primero en silencio
    es exactamente esa trampa. Para grupos mezclados, `prompt_de(record)`.
    """
    distintos = {r["messages"][0]["content"] for r in records}
    if len(distintos) > 1:
        raise ValueError(
            f"estos registros usan {len(distintos)} system prompts distintos: no hay "
            f"uno solo que devolver. Genera cada uno con prompt_de(record).")
    return records[0]["messages"][0]["content"]


def prompt_de(record: dict) -> list[dict]:
    """[system, user] del propio registro: **lo mismo para entrenar y para evaluar**.

    El entrenamiento usa `messages[:2]` de cada registro (formato prompt/
    completion de TRL). La evaluacion tiene que usar exactamente eso, o se mide
    el modelo con instrucciones distintas de las que aprendio. Que las dos
    llamen a esta funcion es lo que impide que vuelvan a separarse.
    """
    mensajes = record.get("messages") or []
    if (len(mensajes) < 2 or mensajes[0].get("role") != "system"
            or mensajes[1].get("role") != "user"):
        raise ValueError(
            f"el registro {record.get('id')} no empieza por [system, user]")
    return [dict(mensajes[0]), dict(mensajes[1])]


def huella_prompt(record: dict) -> str:
    """sha256 corto del system prompt con el que se genera un registro.

    Se guarda en cada respuesta. Las corridas del 2026-10-09 no lo guardaban, y
    por eso hubo que reconstruir del codigo -- no de los resultados -- que
    prompt se habia usado.
    """
    import hashlib

    return hashlib.sha256(
        prompt_de(record)[0]["content"].encode("utf-8")).hexdigest()[:12]


# --- Dev para elegir la epoca, por grupo de pregunta --------------------------

def _pregunta_normalizada(record: dict) -> str:
    """La pregunta sin contexto, sin tildes ni puntuacion, en minusculas."""
    import re
    import unicodedata

    q = record.get("pregunta")
    if not q:
        q = record["messages"][1]["content"].split("PREGUNTA DEL USUARIO:", 1)[-1]
    q = unicodedata.normalize("NFKD", q).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", q).split())


def grupos_de_pregunta(records: list[dict]) -> dict:
    """id -> id del representante de su grupo de pregunta.

    Dos registros van al mismo grupo si comparten la pregunta normalizada, o si
    uno es la base (`base_id`) o el par contrastivo (`par_de`) del otro. Los
    enlaces a ids que no estan en `records` se ignoran.
    """
    padre = {r["id"]: r["id"] for r in records}

    def raiz(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    def unir(a, b):
        if a in padre and b in padre:
            ra, rb = raiz(a), raiz(b)
            if ra != rb:
                padre[max(ra, rb)] = min(ra, rb)

    por_texto: dict = {}
    for r in sorted(records, key=lambda x: x["id"]):
        texto = _pregunta_normalizada(r)
        if texto in por_texto:
            unir(r["id"], por_texto[texto])
        else:
            por_texto[texto] = r["id"]
        for campo in ("base_id", "par_de"):
            if r.get(campo) is not None:
                unir(r["id"], r[campo])
    return {i: raiz(i) for i in padre}


def split_dev(train_records: list[dict], fraccion: float = 0.08,
              seed: int = config.RANDOM_SEED) -> tuple[list[dict], list[dict]]:
    """(fit, dev): el dev que elige la epoca, **sin partir grupos de pregunta**.

    El recorte anterior era aleatorio por registro dentro de cada categoria. Como
    cada variante contrastiva comparte la pregunta con su original y cada ejemplo
    con contexto la comparte con su base sin contexto, el recorte las separaba:
    medido con la semilla 42, **113 de los 179 ejemplos de dev (63 %) tenian su
    pregunta exacta en fit**. Y el dev decide la epoca
    (`load_best_model_at_end=True` con `eval_loss`), asi que premiaba memorizar.

    Aqui se reparten grupos enteros, estratificados por categoria, hasta llegar a
    `fraccion` de los registros de cada una. Los grupos se ordenan por id antes
    de barajar, asi que el resultado no depende del orden de entrada.

    Solo recibe los registros de entrenamiento: **la validacion de 334 no se
    toca**.
    """
    grupo = grupos_de_pregunta(train_records)
    miembros: dict = defaultdict(list)
    for r in train_records:
        miembros[grupo[r["id"]]].append(r)

    por_categoria: dict = defaultdict(list)
    for g, rs in miembros.items():
        # Todos los de un grupo comparten categoria: la base y su version con
        # contexto, y el original y su contrastiva. Si alguna vez no, decide la
        # primera en orden alfabetico, para que sea determinista.
        por_categoria[sorted({r["category"] for r in rs})[0]].append(g)

    rng = Random(seed)
    fit, dev = [], []
    for _categoria, grupos in sorted(por_categoria.items()):
        grupos = sorted(grupos)
        rng.shuffle(grupos)
        objetivo = max(1, round(sum(len(miembros[g]) for g in grupos) * fraccion))
        en_dev = 0
        for g in grupos:
            if en_dev < objetivo:
                dev.extend(miembros[g])
                en_dev += len(miembros[g])
            else:
                fit.extend(miembros[g])
    fit.sort(key=lambda r: r["id"])
    dev.sort(key=lambda r: r["id"])
    return fit, dev


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
