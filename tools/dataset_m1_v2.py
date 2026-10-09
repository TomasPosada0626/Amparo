"""Une dataset_legal.jsonl (v1) y dataset_v2.jsonl (v2) en el archivo con el que
entrena M1.

Por que unir y no reemplazar. v1 ensena a responder en lenguaje claro, nombrar
el mecanismo y ser prudente, y eso esta medido: 3.0 % de entidades inventadas y
4.4 % de ruta incorrecta en la corrida del 2026-10-06. Reescribirlo arriesga esa
conducta y, sobre todo, cambia dos cosas a la vez: no se podria saber si una
mejora vino de ensenar a citar o de haber reescrito los ejemplos. v2 agrega una
conducta nueva -- usar el contexto y decir de donde sale -- sin tocar la
anterior.

Hay una razon tecnica ademas de la de atribucion: los dos modos traen system
prompts distintos (el de M1 y el de prompt_template, que le suma las reglas del
CONTEXTO). Entrenando con la mezcla, el modelo aprende la conducta CONDICIONAL:
cuando ve las reglas del CONTEXTO cita de ahi, y cuando no, responde como antes.
Reescribir todo en formato RAG le quitaria la mitad de esa senal.

El split es lo delicado. Cada ejemplo tiene que caer del lado que le corresponde
o la validacion deja de medir:

  - v1 se parte con stratified_split, igual que siempre. Asi la validacion sigue
    siendo la misma de M2 del 2026-10-06 y las cifras se pueden comparar.
  - v2 se parte con split_v2, que manda cada ejemplo al mismo lado que su
    pregunta base. Si la misma pregunta quedara sin contexto en train y con
    contexto en val, val estaria midiendo memoria.

El archivo sale con `origen` (v1/v2) y `split` (train/val) ya resueltos, para
que el notebook filtre en vez de recalcular: el split depende de la semilla y de
val_fraction, y recalcularlo en otro lado es una oportunidad de que no coincida.

    python -m tools.dataset_m1_v2 --check    # valida sin escribir
    python -m tools.dataset_m1_v2            # escribe data/dataset_m1_v2.jsonl
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from tools.evaluation import config, dataset

SALIDA = config.PROJECT_ROOT / "data" / "dataset_m1_v2.jsonl"
RUTA_V2 = config.PROJECT_ROOT / "data" / "dataset_v2.jsonl"

# Columnas que solo sirven para construir y auditar v2: el notebook de M1 las
# quita antes del SFT. Se conservan en el archivo para poder rastrear de donde
# salio cada ejemplo.
COLUMNAS_SOLO_V2 = ("modo", "base_id", "pregunta", "fuentes", "contexto",
                    "contexto_origen", "buscador")


def cargar_v2(ruta: Path = RUTA_V2) -> list[dict]:
    if not ruta.exists():
        raise SystemExit(
            f"Falta {ruta}. Generalo con: python -m tools.dataset_v2"
        )
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def construir(records_v1: list[dict], records_v2: list[dict]) -> list[dict]:
    """v1 + v2 con `origen` y `split` resueltos."""
    _, val_v1 = dataset.stratified_split(records_v1)
    ids_val_v1 = {r["id"] for r in val_v1}

    train_v2, val_v2 = dataset.split_v2(records_v2, records_v1)
    ids_val_v2 = {r["id"] for r in val_v2}

    salida = []
    for r in records_v1:
        salida.append({**r, "origen": "v1",
                       "split": "val" if r["id"] in ids_val_v1 else "train"})
    for r in records_v2:
        salida.append({**r, "origen": "v2",
                       "split": "val" if r["id"] in ids_val_v2 else "train"})
    return salida


def revisar(combinado: list[dict], records_v1: list[dict], records_v2: list[dict]) -> list[str]:
    """Las comprobaciones que, de fallar, invalidan el entrenamiento entero."""
    fallos = []

    ids = Counter(r["id"] for r in combinado)
    repetidos = [i for i, n in ids.items() if n > 1]
    if repetidos:
        fallos.append(f"ids repetidos entre v1 y v2: {sorted(repetidos)[:10]}")

    if len(combinado) != len(records_v1) + len(records_v2):
        fallos.append("se perdieron o duplicaron ejemplos al unir")

    sin_split = [r["id"] for r in combinado if r.get("split") not in ("train", "val")]
    if sin_split:
        fallos.append(f"ejemplos sin split: {sin_split[:10]}")

    # La que de verdad importa: un ejemplo de v2 cuya pregunta base quedo en la
    # validacion de M1 NO puede entrenar, o val mide lo que el modelo ya vio.
    _, val_v1 = dataset.stratified_split(records_v1)
    ids_val_v1 = {r["id"] for r in val_v1}
    fuga = [r["id"] for r in combinado
            if r.get("origen") == "v2" and r.get("split") == "train"
            and r.get("base_id") in ids_val_v1]
    if fuga:
        fallos.append(f"v2 en train con base en la validacion de M1: {fuga[:10]}")

    # Y el espejo: v1 no se movio de donde estaba.
    v1_combinado = {r["id"]: r.get("split") for r in combinado if r.get("origen") == "v1"}
    movidos = [i for i in ids_val_v1 if v1_combinado.get(i) != "val"]
    if movidos:
        fallos.append(f"v1 cambio de split, rompe la comparacion con M2: {movidos[:10]}")

    return fallos


def resumen(combinado: list[dict]) -> str:
    por = Counter((r.get("origen"), r.get("split")) for r in combinado)
    modos = Counter(r.get("modo") for r in combinado if r["origen"] == "v2")
    lineas = [
        f"  v1  train {por[('v1', 'train')]:>5}   val {por[('v1', 'val')]:>4}",
        f"  v2  train {por[('v2', 'train')]:>5}   val {por[('v2', 'val')]:>4}",
        f"  total {len(combinado)}",
        f"  modos de v2: {dict(modos)}",
    ]
    return "\n".join(lineas)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="valida sin escribir")
    args = p.parse_args()

    v1 = dataset.load_records()
    v2 = cargar_v2()
    combinado = construir(v1, v2)

    print(resumen(combinado))
    fallos = revisar(combinado, v1, v2)
    if fallos:
        print("\nNO se escribe el dataset:")
        for f in fallos:
            print(f"  [FALLA] {f}")
        raise SystemExit(1)
    print("\n  todas las comprobaciones pasan")

    if args.check:
        print("--check: no se escribio nada.")
        return

    SALIDA.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in combinado) + "\n",
        encoding="utf-8")
    print(f"\nEscrito {SALIDA} ({len(combinado)} ejemplos)")


if __name__ == "__main__":
    main()
