"""Evalua en CPU la corrida final del paso 7 de M3 (colab/m3_paso7_corrida_final.ipynb).

Lee `eval_records_<sistema>_<conjunto>.jsonl` (bajados de Drive,
rag/corridas_paso7/) y, por sistema y conjunto:

  - acierto: el articulo gold entre los fragmentos que DE VERDAD recibio el
    modelo (retrieved_chunks de cada registro, no una re-busqueda);
  - juez del RAG (`juez_rag.py`): solo con --juzgar, porque llama a Groq;
  - abstencion pura y latencia.

A sobre el eval set no se genera en esa corrida: se toma de
results/m3_s10_2026-10-14/eval_records_una_pasada_lora.json (determinista).

    python -m tools.evaluation.evaluar_paso7 --dir <carpeta>             # sin Groq
    python -m tools.evaluation.evaluar_paso7 --dir <carpeta> --juzgar    # con Groq (autorizacion)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
A_EVAL_SET = RAIZ / "results" / "m3_s10_2026-10-14" / "eval_records_una_pasada_lora.json"
SISTEMAS = ("A", "A_servicio", "R", "R_servicio", "R_servicio2")
CONJUNTOS = ("eval_set", "confirmacion")


def cargar(carpeta: Path, sistema: str, conjunto: str) -> list[dict] | None:
    if sistema == "A" and conjunto == "eval_set":
        return json.loads(A_EVAL_SET.read_text(encoding="utf-8"))
    ruta = carpeta / f"eval_records_{sistema}_{conjunto}.jsonl"
    if not ruta.exists():
        return None
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def _etiquetas(conjunto: str) -> dict[str, dict[str, set[str]]]:
    if conjunto == "eval_set":
        from tools import auditoria_61
        return auditoria_61.gold_aprobado()[0]
    from tools.evaluation import preguntas_confirmacion
    return preguntas_confirmacion.gold()


def _articulos_por_chunk() -> dict[str, tuple[str, list[str]]]:
    from tools.rag import config
    salida = {}
    with open(config.FAISS_METADATA_PATH, encoding="utf-8") as f:
        for l in f:
            m = json.loads(l)
            salida[m["chunk_id"]] = (m["doc_id"], [str(a) for a in m.get("articulos_incluidos") or []])
    return salida


def acierto(records: list[dict], etiquetas: dict, por_chunk: dict, k: int = 5) -> dict:
    """Cuantas gold tienen el articulo correcto entre los primeros k fragmentos recibidos."""
    from tools.rag.chunk import normalizar_numero

    aciertos, total = [], 0
    for r in records:
        et = etiquetas.get(str(r["id"]))
        if not et:
            continue
        total += 1
        norm = {d: {normalizar_numero(a) for a in arts} for d, arts in et.items()}
        for c in r.get("retrieved_chunks", [])[:k]:
            doc, arts = por_chunk.get(c["chunk_id"], (None, []))
            if any(normalizar_numero(a) in norm.get(doc, set()) for a in arts):
                aciertos.append(str(r["id"]))
                break
    return {"aciertos": len(aciertos), "de": total, "ids": sorted(aciertos)}


def resumen(carpeta: Path, juzgar: bool = False) -> dict:
    from tools.evaluation.ragas_metrics import es_abstencion_pura

    por_chunk = _articulos_por_chunk()
    salida = {}
    for conjunto in CONJUNTOS:
        etiquetas = _etiquetas(conjunto)
        registros_conjunto = None
        if juzgar:
            from tools.evaluation import eval_set, preguntas_confirmacion
            registros_conjunto = (eval_set.load_eval_set() if conjunto == "eval_set"
                                  else preguntas_confirmacion.cargar())
        for sistema in SISTEMAS:
            recs = cargar(carpeta, sistema, conjunto)
            if recs is None:
                continue
            gold = [r for r in recs if r.get("tipo") == "gold"]
            fila = {
                "n": len(recs),
                "acierto_top5_gold": acierto(gold, etiquetas, por_chunk),
                "abstencion_pura_gold": sum(es_abstencion_pura(r["answer"]) for r in gold),
                "segundos_media": (round(sum(r.get("segundos", 0) for r in recs) / len(recs), 2)
                                   if any("segundos" in r for r in recs) else None),
            }
            if juzgar:
                from tools.evaluation import criterio, juez_rag
                v = juez_rag.evaluar(recs, registros_conjunto, criterio.generador_groq(), label=sistema,
                                     checkpoint_path=carpeta / f"juez_rag_checkpoint_{sistema}_{conjunto}.jsonl")
                fila["juez_rag"] = criterio.resumen(v).get(sistema, {})
            salida[f"{sistema}/{conjunto}"] = fila
    return salida


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--juzgar", action="store_true", help="llama al juez del RAG (Groq)")
    a = ap.parse_args(argv)
    r = resumen(a.dir, a.juzgar)
    for clave, f in r.items():
        ac = f["acierto_top5_gold"]
        linea = f"{clave:26} articulo en top-5 {ac['aciertos']:2}/{ac['de']}  abstencion {f['abstencion_pura_gold']:2}"
        if "juez_rag" in f and "gold" in f["juez_rag"]:
            g = f["juez_rag"]["gold"]
            linea += f"  | juez gold: cumple {g['cumple']} parcial {g['parcial']} no {g['no_cumple']}"
        print(linea)
    (a.dir / "resumen_paso7.json").write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
