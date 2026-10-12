"""Sobreabstencion en los 45 gold con recuperacion real (fase C, paso C6).

El criterio D3 del protocolo (docs/m1_protocolo_aceptacion.md, fila 8) es
`es_abstencion_pura` sobre los 45 gold del eval set, <= 3/45: preguntas que el
sistema deberia responder y en las que dice "no tengo informacion".

Se mide con el RAG que se entrega (`pipeline.answer_query`, la misma ruta que
S10) y no con el contexto del dataset: la sobreabstencion que importa es la que
ve el usuario. Por eso una abstencion puede venir de tres lados, y el resumen
los separa:

  - `sin_contexto`: la busqueda no devolvio nada y el codigo escapa sin llamar
    al modelo. Es de recuperacion, igual para cualquier adaptador.
  - `citas_no_verificables`: el modelo respondio citando algo que no estaba en
    el contexto y el codigo lo reemplazo por la frase de escape.
  - `modelo`: el modelo mismo se abstuvo teniendo contexto. Es lo que cambia
    entre adaptadores y lo que el entrenamiento puede haber empeorado.

Se corre con v1 y con el candidato en la misma maquina: el diseno es pareado.
No toca las corridas de S10 en Drive (rag/corridas_s10): escribe en su propio
directorio, uno por corrida.

    python -m tools.evaluation.sobreabstencion_gold --correr --adaptador <dir> --salida <dir>
    python -m tools.evaluation.sobreabstencion_gold --comparar <dir_v1> <dir_candidato>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.evaluation import config

UMBRAL_D3 = 3


def origen_abstencion(fila: dict) -> str | None:
    """De donde salio la abstencion de una fila, o None si respondio."""
    if not fila.get("abstencion_pura"):
        return None
    escape = (fila.get("verificacion") or {}).get("escape_por_codigo")
    return escape or "modelo"


def resumir(filas: list[dict]) -> dict:
    n = len(filas)
    origenes = [origen_abstencion(f) for f in filas]
    total = sum(1 for o in origenes if o)
    return {
        "n": n,
        "abstencion_pura": f"{total}/{n}",
        "cumple_d3": total <= UMBRAL_D3,
        "por_origen": {o: origenes.count(o) for o in ("sin_contexto", "citas_no_verificables", "modelo")},
        "ids_abstencion": sorted(f["id"] for f, o in zip(filas, origenes) if o),
    }


def comparar(a: list[dict], b: list[dict]) -> dict:
    """Pareado por id: donde se abstiene uno y el otro no."""
    pa = {f["id"]: bool(f.get("abstencion_pura")) for f in a}
    pb = {f["id"]: bool(f.get("abstencion_pura")) for f in b}
    comunes = sorted(set(pa) & set(pb))
    return {
        "n_comunes": len(comunes),
        "solo_a": [i for i in comunes if pa[i] and not pb[i]],
        "solo_b": [i for i in comunes if pb[i] and not pa[i]],
        "ambos": [i for i in comunes if pa[i] and pb[i]],
    }


def _leer(ruta: Path) -> list[dict]:
    if not ruta.exists():
        return []
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


# --- Lo que corre en Colab -----------------------------------------------------

def correr(adaptador, salida) -> dict:
    from tools.evaluation import corrida, eval_set
    from tools.evaluation.ragas_metrics import es_abstencion_pura
    from tools.rag import config as rag_config, pipeline
    from tools.rag.manifiesto import huella_archivo

    huella_adaptador = huella_archivo(Path(adaptador) / "adapter_model.safetensors")
    try:  # informativo: el pipeline no fija la revision (H6), se anota cual habia
        from huggingface_hub import model_info

        revision = model_info(rag_config.BASE_MODEL_ID).sha
    except Exception:
        revision = None
    firma = corrida.firma(huella_dataset=huella_archivo(eval_set.EVAL_SET_PATH),
                          model_id=rag_config.BASE_MODEL_ID,
                          adaptador=f"gold-{huella_adaptador}", revision_base=revision,
                          raiz=config.PROJECT_ROOT)
    d = Path(salida) / firma["corrida_id"]
    corrida.escribir(d, firma)

    rag_config.LORA_ADAPTER_PATH = str(adaptador)
    store = pipeline.load_index()
    bundle = pipeline.load_model(use_lora=True)

    gold = eval_set.gold_examples(eval_set.load_eval_set())
    ruta = d / "gold_resultados.jsonl"
    hechos = {f["id"] for f in _leer(ruta)}
    for reg in gold:
        if reg["id"] in hechos:
            continue
        res = pipeline.answer_query(reg["messages"][1]["content"], store, use_lora=True,
                                    model_bundle=bundle,
                                    use_hybrid=rag_config.USE_HYBRID,
                                    use_rerank=rag_config.USE_RERANK)
        rec = pipeline.to_eval_record(res, reg)
        fila = {k: rec[k] for k in ("id", "category", "criterio", "question", "answer",
                                     "n_retrieved", "n_tokens", "cortada", "verificacion")}
        fila["retrieved"] = [c.get("chunk_id") for c in rec.get("retrieved_chunks") or []]
        fila["abstencion_pura"] = bool(es_abstencion_pura(rec["answer"]))
        with ruta.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")

    res = {"corrida_id": firma["corrida_id"], "huella_adaptador": huella_adaptador,
           **resumir(_leer(ruta))}
    (d / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--correr", action="store_true", help="genera los 45 gold en Colab")
    g.add_argument("--comparar", nargs=2, metavar=("DIR_A", "DIR_B"),
                   help="compara dos corridas ya hechas (CPU)")
    ap.add_argument("--adaptador")
    ap.add_argument("--salida")
    a = ap.parse_args(argv)

    if a.correr:
        if not (a.adaptador and a.salida):
            raise SystemExit("--correr necesita --adaptador y --salida")
        print(json.dumps(correr(a.adaptador, a.salida), ensure_ascii=False, indent=2))
        return 0
    fa, fb = (_leer(Path(x) / "gold_resultados.jsonl") for x in a.comparar)
    print(json.dumps({"a": resumir(fa), "b": resumir(fb), "pareado": comparar(fa, fb)},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
