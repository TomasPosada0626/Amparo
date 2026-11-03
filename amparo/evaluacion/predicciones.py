"""Las predicciones de M1 (`results/m1_predicciones.json`), como las leen M2 y M3.

M2 y M3 repetian la misma lectura. `publicar()` estampa `_corrida` en el
archivo y la version anterior lo tiraba al desenvolver `datos`: el corrida.json
de M2 documentaba datos y codigo, pero no cual de las corridas de M1 produjo
las salidas que el juez estaba puntuando.
"""
from __future__ import annotations

import json

from amparo.config import RESULTS
from amparo.nucleo import schema


def cargar_m1(ruta=RESULTS / "m1_predicciones.json", eval_set: list[dict] | None = None):
    """Devuelve `(preds, corrida_m1)`.

    `preds` es la lista de `{"id", "base", "finetuned", ...}` y `corrida_m1`
    el id de la corrida de M1 que la publico (None si el archivo no lo trae).
    Con `eval_set`, comprueba que el orden de ids coincida: si no, cada
    prediccion se compararia contra el gold de otro caso.
    """
    bruto = json.loads(open(ruta, encoding="utf-8").read())
    corrida_m1 = bruto.get("_corrida") if isinstance(bruto, dict) else None
    preds = bruto["datos"] if isinstance(bruto, dict) and "datos" in bruto else bruto
    print("predicciones de la corrida m1:", corrida_m1 or "(sin registrar)")
    if eval_set is not None:
        assert [p["id"] for p in preds] == [e["id"] for e in eval_set], "el orden no coincide"
    return preds, corrida_m1


def recortar(preds: list[dict]) -> tuple[list[str], list[str]]:
    """Recorte DEFENSIVO de las colas degeneradas: `(sal_base, sal_ft)`.

    M1 ya recorta en el origen, asi que lo esperable aqui es cero. Si sale
    distinto de cero, las predicciones vienen de una corrida anterior al
    arreglo, y hay que saberlo ANTES de que el juez puntue: leeria la cola
    degenerada y penalizaria nuestra basura, no el razonamiento del modelo.
    """
    pares_base = [schema.recortar_al_bloque(p["base"]) for p in preds]
    pares_ft = [schema.recortar_al_bloque(p["finetuned"]) for p in preds]
    rec_base = sum(r for _, r in pares_base)
    rec_ft = sum(r for _, r in pares_ft)
    if rec_base or rec_ft:
        print(f"ATENCION: hubo que recortar colas degeneradas aqui "
              f"({rec_base} en base, {rec_ft} en ajustado). Estas predicciones "
              f"son de una corrida anterior al arreglo de M1.")
    else:
        print("recorte defensivo: 0 colas degeneradas (M1 ya recorto en el origen)")
    return [t for t, _ in pares_base], [t for t, _ in pares_ft]
