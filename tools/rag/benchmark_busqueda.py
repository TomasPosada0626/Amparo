"""Benchmark de la busqueda: ¿trae el articulo que responde la pregunta?

RAGAS mide la busqueda con un juez (context recall), y eso cuesta cupo de Groq,
tarda y mezcla dos cosas: si se trajo la norma y como la leyo el juez. Para
decidir entre configuraciones de busqueda hace falta una medida directa, sin
juez y que corra en segundos: los 45 casos gold del eval set tienen etiquetados
los articulos que los responden (data/eval_set_articulos.json), y un caso es
acierto si la busqueda trae al menos uno en su top-k.

Ademas mide el piso de la valvula de escape: con cada piso candidato, cuantos
gold se quedan sin contexto (malo: el sistema se niega a responder) y cuantos
adversariales tambien (bueno, en los que piden algo que el corpus no tiene).

Uso:
  python -m tools.rag.benchmark_busqueda --bm25        # local, sin modelos
  python -m tools.rag.benchmark_busqueda --indice      # en Colab, con e5 y FAISS
                                                       # (artifacts/ con el indice)
Escribe results/busqueda_<fecha>.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from typing import Callable, Sequence

from tools.rag import config
from tools.rag.chunk import normalizar_numero

ETIQUETAS_PATH = config.PROJECT_ROOT / "data" / "eval_set_articulos.json"
EVAL_SET_PATH = config.PROJECT_ROOT / "data" / "eval_set.json"
KS = (1, 3, 5, 10)
PISOS = (None, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83)


def cargar_etiquetas() -> dict[int, dict[str, set[str]]]:
    with open(ETIQUETAS_PATH, encoding="utf-8") as f:
        casos = json.load(f)["casos"]
    return {int(i): {d: {normalizar_numero(a) for a in arts} for d, arts in lab.items()}
            for i, lab in casos.items()}


def acierta(resultados: Sequence, etiqueta: dict[str, set[str]]) -> bool:
    return any(normalizar_numero(a) in etiqueta.get(r.doc_id, set())
               for r in resultados for a in r.articulos_incluidos)


def evaluar(buscar: Callable[[str], list], etiquetas=None, registros=None) -> dict:
    """buscar(consulta) -> lista ordenada de SearchResult (al menos max(KS))."""
    etiquetas = etiquetas if etiquetas is not None else cargar_etiquetas()
    if registros is None:
        with open(EVAL_SET_PATH, encoding="utf-8") as f:
            registros = json.load(f)
    por_id = {r["id"]: r for r in registros}
    aciertos = {k: 0 for k in KS}
    rr, por_caso = [], {}
    for i, etiqueta in etiquetas.items():
        res = buscar(por_id[i]["messages"][1]["content"])
        puesto = next((n for n in range(1, len(res) + 1) if acierta(res[n - 1:n], etiqueta)), None)
        for k in KS:
            aciertos[k] += bool(puesto and puesto <= k)
        rr.append(1 / puesto if puesto else 0.0)
        por_caso[i] = puesto
    n = len(etiquetas)
    return {"n": n, **{f"acierto@{k}": round(aciertos[k] / n, 3) for k in KS},
            "mrr": round(sum(rr) / n, 3), "puesto_por_caso": por_caso}


def barrer_pisos(buscar_con_scores: Callable[[str], list], registros=None, pisos=PISOS) -> list[dict]:
    """Con cada piso de coseno, gold sin contexto y adversariales sin contexto.
    buscar_con_scores devuelve los candidatos con dense_score, sin piso."""
    from tools.rag.retrieve import apply_score_floor

    if registros is None:
        with open(EVAL_SET_PATH, encoding="utf-8") as f:
            registros = json.load(f)
    etiquetas = cargar_etiquetas()
    candidatos = {r["id"]: (r, buscar_con_scores(r["messages"][1]["content"])) for r in registros}
    filas = []
    for piso in pisos:
        gold_vacio = adv_vacio = gold_ok = 0
        for i, (r, res) in candidatos.items():
            q = r["messages"][1]["content"]
            quedan = res if piso is None else apply_score_floor(res, piso, q)
            top = quedan[: config.TOP_K]
            if r["tipo"] == "gold":
                gold_vacio += not top
                gold_ok += i in etiquetas and acierta(top, etiquetas[i])
            else:
                adv_vacio += not top
        n_gold = sum(1 for r in registros if r["tipo"] == "gold")
        n_adv = len(registros) - n_gold
        filas.append({"piso": piso, "gold_sin_contexto": f"{gold_vacio}/{n_gold}",
                      "adversariales_sin_contexto": f"{adv_vacio}/{n_adv}",
                      "gold_acierto@5": f"{gold_ok}/{len(etiquetas)}"})
    return filas


def _bm25_local():
    from tools.rag import corpus, ingest
    from tools.rag.chunk import chunk_corpus
    from tools.rag.embed_store import chunk_to_metadata
    from tools.rag.enrutador import enrutador_por_defecto, priorizar
    from tools.rag.hybrid import BM25Index

    docs = ingest.ingest_corpus(corpus.to_ingest_manifest())
    chunks = chunk_corpus([{"doc_id": d.doc_id, "text": d.text, "fuente": d.fuente, "tipo": d.tipo,
                            "url_fuente": d.url_fuente, "vigente": d.vigente} for d in docs])
    bm25 = BM25Index([chunk_to_metadata(c) for c in chunks])
    enr = enrutador_por_defecto()
    return {
        "bm25": lambda q: bm25.search(q, 10),
        "bm25+enrutador": lambda q: priorizar(bm25.search(q, config.ENRUTADOR_POOL), enr.normas(q))[:10],
    }


def _indice():
    from tools.rag import pipeline
    from tools.rag.hybrid import BM25Index
    from tools.rag.retrieve import retrieve

    store = pipeline.load_index()
    bm25 = BM25Index(store.metadata)

    def conf(**kw):
        return lambda q: retrieve(q, store, top_k=10, min_score=None, bm25=bm25, **kw)

    return {
        "A denso": conf(use_router=False),
        "A denso+enrutador": conf(use_router=True),
        "B hybrid+enrutador": conf(use_router=True, use_hybrid=True),
        "C rerank+enrutador": conf(use_router=True, use_hybrid=True, use_rerank=True),
    }, conf


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--bm25", action="store_true", help="solo BM25, local y sin modelos")
    grupo.add_argument("--indice", action="store_true", help="con el indice FAISS y e5 (Colab)")
    args = parser.parse_args(argv)

    salida = {"fecha": dt.date.today().isoformat(), "configuraciones": {}}
    if args.bm25:
        configs = _bm25_local()
    else:
        configs, conf = _indice()
        salida["pisos_denso+enrutador"] = barrer_pisos(conf(use_router=True))
        salida["pisos_denso"] = barrer_pisos(conf(use_router=False))
    print(f"{'configuracion':24s}{'@1':>7}{'@3':>7}{'@5':>7}{'@10':>7}{'mrr':>7}")
    for nombre, buscar in configs.items():
        r = evaluar(buscar)
        salida["configuraciones"][nombre] = r
        print(f"{nombre:24s}" + "".join(f"{r[f'acierto@{k}']:>7.2f}" for k in KS) + f"{r['mrr']:>7.2f}")
    for clave in ("pisos_denso", "pisos_denso+enrutador"):
        if clave in salida:
            print(f"\n{clave}:")
            for fila in salida[clave]:
                print("  ", fila)
    destino = config.PROJECT_ROOT / "results" / f"busqueda_{salida['fecha']}{'_bm25' if args.bm25 else ''}.json"
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n->", destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
