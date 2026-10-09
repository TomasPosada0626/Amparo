"""El dataset de M1 v2: v1 + v2 + las variantes contrastivas.

Qué cambia frente a `dataset_m1_v2.jsonl`. Nada de lo que ya estaba: los 1536
de v1 y los 755 de v2 entran con el mismo split. Se suman las 418 variantes
contrastivas de `tools/dataset_contrastivo.py`, todas a `train`.

Por qué. El adaptador v1 se abstuvo en 0 de 35 casos B2. De las 601 preguntas
base con contexto en entrenamiento, solo UNA aparecia en mas de un modo, asi
que el modo era predecible desde la pregunta y el modelo podia memorizarlo en
vez de leer el contexto. Las variantes ponen la misma pregunta con un contexto
que no responde, y eso sube a 402 las preguntas vistas en varios modos.

Lo que NO se toca, porque si se mueve la comparacion v1 contra v2 deja de ser
valida:

  - la validacion sigue siendo la misma: 334 registros (231 de v1, 103 de v2);
  - los splits de v1 y de v2 quedan donde estaban;
  - `data/eval_set.json` y `data/eval_set_articulos.json` no se usan aqui.

    python -m tools.dataset_m1_v3            # escribe data/dataset_m1_v3.jsonl
    python -m tools.dataset_m1_v3 --check    # valida sin escribir
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from tools.evaluation import config, dataset

RUTA_V2 = config.PROJECT_ROOT / "data" / "dataset_m1_v2.jsonl"
RUTA_CONTRASTIVO = config.PROJECT_ROOT / "data" / "dataset_contrastivo.jsonl"
SALIDA = config.PROJECT_ROOT / "data" / "dataset_m1_v3.jsonl"

# La validacion de M1 v1, que tiene que sobrevivir intacta.
N_VAL_ESPERADA = 334


def _leer(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def construir(base: list[dict] | None = None,
              contrastivo: list[dict] | None = None) -> list[dict]:
    """El combinado, sin recalcular ningun split.

    `dataset_m1_v2.jsonl` ya trae `origen` y `split` resueltos, asi que aqui no
    se vuelve a partir nada: recalcular el split con otra version del dataset
    moveria ejemplos de lado y la validacion dejaria de ser la de v1.
    """
    base = base if base is not None else _leer(RUTA_V2)
    contrastivo = contrastivo if contrastivo is not None else _leer(RUTA_CONTRASTIVO)
    return [*base, *contrastivo]


def revisar(combinado: list[dict], base: list[dict], contrastivo: list[dict],
            n_val: int | None = N_VAL_ESPERADA) -> list[str]:
    """Lo que, de fallar, invalida el entrenamiento o la comparacion.

    `n_val` es el tamano que debe tener la validacion; con None no se
    comprueba, que es lo que necesitan las pruebas con datos de juguete. El
    valor real se deja por defecto para que el CLI no pueda saltarselo.
    """
    fallos = []

    ids = Counter(r["id"] for r in combinado)
    repetidos = [i for i, n in ids.items() if n > 1]
    if repetidos:
        fallos.append(f"ids repetidos: {sorted(repetidos)[:10]}")

    if len(combinado) != len(base) + len(contrastivo):
        fallos.append("se perdieron o duplicaron ejemplos al unir")

    sin_split = [r["id"] for r in combinado if r.get("split") not in ("train", "val")]
    if sin_split:
        fallos.append(f"ejemplos sin split: {sin_split[:10]}")

    # La validacion es la medicion: si cambia, no hay con que comparar v1.
    val = [r for r in combinado if r["split"] == "val"]
    if n_val is not None and len(val) != n_val:
        fallos.append(f"la validacion tiene {len(val)} y no {n_val}: "
                      "la comparacion con v1 deja de ser valida")
    val_base = {r["id"] for r in base if r.get("split") == "val"}
    val_nueva = {r["id"] for r in val}
    if val_base != val_nueva:
        fallos.append("la validacion no es la misma que la de v1 "
                      f"(sobran {sorted(val_nueva - val_base)[:5]}, "
                      f"faltan {sorted(val_base - val_nueva)[:5]})")

    # Los splits de lo que ya existia no se movieron.
    split_base = {r["id"]: r.get("split") for r in base}
    movidos = [r["id"] for r in combinado
               if r["id"] in split_base and r["split"] != split_base[r["id"]]]
    if movidos:
        fallos.append(f"ejemplos que cambiaron de split: {movidos[:10]}")

    # Las variantes solo entrenan.
    fuera = [r["id"] for r in contrastivo if r.get("split") != "train"]
    if fuera:
        fallos.append(f"variantes contrastivas fuera de train: {fuera[:10]}")

    # Y ninguna puede venir de una pregunta que quedo en la validacion de v1.
    ids_val_v1 = {r["id"] for r in base if r.get("origen") == "v1" and r.get("split") == "val"}
    fuga = [r["id"] for r in contrastivo if r.get("base_id") in ids_val_v1]
    if fuga:
        fallos.append(f"variantes con base en la validacion de M1: {fuga[:10]}")

    # El par tiene que existir, o la variante no contrasta con nada.
    ids_base = {r["id"] for r in base}
    sueltas = [r["id"] for r in contrastivo if r.get("par_de") not in ids_base]
    if sueltas:
        fallos.append(f"variantes sin su ejemplo original: {sueltas[:10]}")

    return fallos


def resumen(combinado: list[dict], base: list[dict]) -> str:
    def masa(rs):
        return sum(len(r["messages"][-1]["content"]) for r in rs)

    lineas = []
    tr = [r for r in combinado if r["split"] == "train"]
    val = [r for r in combinado if r["split"] == "val"]
    lineas.append(f"total {len(combinado)} | train {len(tr)} | val {len(val)}")

    por_origen = Counter(r.get("origen") for r in combinado)
    lineas.append("por origen: " + ", ".join(f"{k} {v}" for k, v in sorted(
        por_origen.items(), key=lambda kv: str(kv[0]))))

    grupos = {"v1": [r for r in tr if not r.get("modo")]}
    for m in ("B1", "B2", "B3"):
        grupos[m] = [r for r in tr if r.get("modo") == m]
    c_tot = masa([r for g in grupos.values() for r in g])
    lineas.append(f"{'grupo':6}{'n':>7}{'% ejemplos':>13}{'% senal':>10}")
    for k, g in grupos.items():
        lineas.append(f"{k:6}{len(g):>7}{len(g) / len(tr):>12.1%}{masa(g) / c_tot:>10.1%}")

    por_base: dict = {}
    for r in tr:
        if r.get("modo"):
            por_base.setdefault(r.get("base_id"), set()).add(r["modo"])
    lineas.append(f"preguntas vistas en mas de un modo: "
                  f"{sum(1 for s in por_base.values() if len(s) > 1)}")

    val_igual = ({r["id"] for r in val}
                 == {r["id"] for r in base if r.get("split") == "val"})
    lineas.append(f"la validacion es la misma que la de v1: {'si' if val_igual else 'NO'}")
    return "\n".join(lineas)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="valida sin escribir")
    args = p.parse_args(argv)

    base = _leer(RUTA_V2)
    contrastivo = _leer(RUTA_CONTRASTIVO)
    combinado = construir(base, contrastivo)

    fallos = revisar(combinado, base, contrastivo)
    if fallos:
        for f in fallos:
            print(f"  - {f}")
        raise SystemExit(f"{len(fallos)} fallos: no se escribe nada")

    if not args.check:
        SALIDA.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in combinado) + "\n",
            encoding="utf-8")
        print(f"Escrito {SALIDA}")
    else:
        print("Sin fallos (no se escribio nada)")
    print()
    print(resumen(combinado, base))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
