"""Reusar el baseline (modelo base, sin adaptador) de una corrida anterior.

El baseline no depende del adaptador ni del dataset de entrenamiento: con la
misma revision del modelo base, el mismo prompt por registro y la misma
validacion, el modelo base recibe exactamente las mismas entradas. Generarlo
cuesta ~90 min de A100 (105 709 tokens en la corrida de v3, 2026-10-12), y
volver a generarlo no da un resultado "mas valido": el control de reproduccion
de la fase B mostro que dos generaciones del mismo modelo ya divergen por deriva
numerica (3 de 10 identicas).

Se reusa **solo si se comprueba todo lo que lo hace equivalente**, registro por
registro. Si algo no cuadra se devuelve None con el motivo y el notebook genera
el baseline de cero: reusar mal es peor que gastar GPU.

    revision        la de la corrida anterior == la de esta
    ids             los mismos que la validacion de esta corrida, sin faltantes
    contenido       messages identicos (la validacion es intocable EN CONTENIDO, H3)
    prompt          huella_prompt(item) == prompt_sistema guardado
    esquema         los campos que exige el notebook
"""
from __future__ import annotations

import json
from pathlib import Path

ARCHIVO = "base_results.jsonl"


def _leer(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def motivos_para_no_reusar(directorio, val_records: list[dict], revision: str,
                           campos: set[str] = frozenset()) -> tuple[list[str], list[dict]]:
    """(motivos, filas en el orden de `val_records`). Sin motivos, se puede reusar."""
    from tools.evaluation.dataset import huella_prompt

    d = Path(directorio)
    ruta, firma = d / ARCHIVO, d / "corrida.json"
    if not ruta.exists() or not firma.exists():
        return [f"no estan {ARCHIVO} y corrida.json en {d}"], []
    rev = json.loads(firma.read_text(encoding="utf-8")).get("revision_base")
    if not revision or rev != revision:
        return [f"revision del modelo base distinta: {rev} frente a {revision}"], []

    por_id = {r["id"]: r for r in _leer(ruta)}
    motivos: list[str] = []
    faltan = [v["id"] for v in val_records if v["id"] not in por_id]
    sobran = sorted(set(por_id) - {v["id"] for v in val_records})
    if faltan:
        motivos.append(f"{len(faltan)} ids de la validacion sin baseline: {faltan[:5]}")
    if sobran:
        motivos.append(f"{len(sobran)} ids que no son de esta validacion: {sobran[:5]}")
    distintos_contenido, distintos_prompt = [], []
    for v in val_records:
        r = por_id.get(v["id"])
        if r is None:
            continue
        if r.get("messages") != v.get("messages"):
            distintos_contenido.append(v["id"])
        if r.get("prompt_sistema") != huella_prompt(v):
            distintos_prompt.append(v["id"])
    if distintos_contenido:
        motivos.append(f"{len(distintos_contenido)} registros con otro contenido: {distintos_contenido[:5]}")
    if distintos_prompt:
        motivos.append(f"{len(distintos_prompt)} registros con otro prompt: {distintos_prompt[:5]}")
    sin_campos = [r["id"] for r in por_id.values() if not set(campos) <= set(r)]
    if sin_campos:
        motivos.append(f"{len(sin_campos)} filas de un esquema anterior: {sin_campos[:5]}")
    if motivos:
        return motivos, []
    return [], [por_id[v["id"]] for v in val_records]


def reusar_base(directorio, val_records: list[dict], revision: str,
                campos: set[str] = frozenset()) -> list[dict] | None:
    """Las filas del baseline anterior, en el orden de esta validacion, o None."""
    motivos, filas = motivos_para_no_reusar(directorio, val_records, revision, campos)
    if motivos:
        print("No se reusa el baseline anterior; se genera de cero:")
        for m in motivos:
            print(f"  - {m}")
        return None
    print(f"Baseline reusado de {directorio}: {len(filas)} registros, misma revision, "
          "mismo contenido y mismo prompt registro por registro.")
    return filas
