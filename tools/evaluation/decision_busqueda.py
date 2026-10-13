"""La decision de busqueda de M3 y el juez de criterio sobre las respuestas del RAG.

**La regla se fijo antes de correr** (`docs/m3_plan_colab_2026-10-13.md`): se
adopta C (enrutador + hybrid + reranker) en lugar de A (denso + enrutador) si,
en el RAGAS de las 45 gold,

  1. la media de las cuatro metricas es mayor que la de A, y
  2. ninguna de las cuatro baja mas de `TOLERANCIA` frente a A.

Si falta una de las dos corridas, o alguna metrica no se pudo calcular, se queda
A: la decision no se toma con datos incompletos.

`generaciones_rag` pone las respuestas del RAG en la forma que espera
`criterio.evaluar_contra_criterio`, el mismo juez que M2 aplica al modelo sin
RAG: asi la cifra de "responde bien" de M3 se lee igual que la de M2.
"""
from __future__ import annotations

from types import SimpleNamespace

METRICAS = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
TOLERANCIA = 0.03
A, C = "A_denso", "C_rerank"


def decidir(resumen_abc: dict) -> dict:
    """{"elegida", "motivo", "medias", "diferencias"} a partir de ragas_metrics.resumen."""
    a, c = resumen_abc.get(A), resumen_abc.get(C)
    if not a or not c:
        return {"elegida": A, "motivo": "falta la corrida de A o la de C: se queda A",
                "medias": {}, "diferencias": {}}
    faltan = [m for m in METRICAS if a.get(m) is None or c.get(m) is None]
    if faltan:
        return {"elegida": A, "motivo": f"sin valor en {faltan}: se queda A",
                "medias": {}, "diferencias": {}}
    medias = {k: round(sum(r[m] for m in METRICAS) / len(METRICAS), 4) for k, r in ((A, a), (C, c))}
    diferencias = {m: round(c[m] - a[m], 4) for m in METRICAS}
    sube = medias[C] > medias[A]
    peor = min(diferencias.values())
    if sube and peor >= -TOLERANCIA:
        motivo = (f"C sube la media de {medias[A]} a {medias[C]} y ninguna metrica baja mas de "
                  f"{TOLERANCIA} (la que mas baja: {peor})")
        return {"elegida": C, "motivo": motivo, "medias": medias, "diferencias": diferencias}
    if not sube:
        motivo = f"C no sube la media ({medias[C]} frente a {medias[A]}): se queda A"
    else:
        motivo = f"C sube la media pero una metrica baja {peor} (mas que {TOLERANCIA}): se queda A"
    return {"elegida": A, "motivo": motivo, "medias": medias, "diferencias": diferencias}


def generaciones_rag(records: list[dict], label: str) -> list[SimpleNamespace]:
    """Registros de `pipeline.to_eval_record` con la forma .id/.query/.generated/.label."""
    return [SimpleNamespace(id=r["id"], query=r["question"], generated=r["answer"], label=label)
            for r in records]
