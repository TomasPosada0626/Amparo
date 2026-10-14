"""R2 del paso 7 de M3: ¿un cross-encoder fuerte elige el articulo correcto?

En el diagnostico del 2026-10-14, en 19 de las 25 gold que fallan la busqueda
trae la NORMA correcta (casi siempre en el puesto 1) pero no el articulo: el
reranker es la pieza que debe elegir el articulo dentro de la norma.

Tres pasos separados, para que quepa en un PC de 8 GB (e5, el indice y un
cross-encoder grande juntos no caben) y para que el paso caro se pueda correr
donde haya GPU:

  1. candidatos: los N que veria el reranker en produccion (busqueda densa +
     enrutador, sin reordenar), guardados en un json. Necesita e5 y el indice.
  2. puntuar:    el cross-encoder puntua cada par (pregunta, fragmento). Carga
     solo el cross-encoder; guarda lo hecho y retoma si se corta.
  3. medir:      reordena con esos puntajes y da el puesto del articulo gold.

    python -m tools.rag.experimento_rerank candidatos --salida <dir>
    python -m tools.rag.experimento_rerank puntuar --dir <dir> --modelo BAAI/bge-reranker-v2-m3 [--con-cita]
    python -m tools.rag.experimento_rerank medir --dir <dir> --modelo BAAI/bge-reranker-v2-m3 [--con-cita]

La vara es la de experimento_embeddings.medir: 45 gold, etiquetas de
`auditoria_61.gold_aprobado`, sin piso. El conjunto de confirmacion no se mira.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from types import SimpleNamespace

from tools.rag import config

KS = (1, 3, 5, 10)


def _nombre(modelo: str, con_cita: bool) -> str:
    return modelo.replace("/", "__") + ("__con_cita" if con_cita else "")


def candidatos(salida: Path, n: int = config.RERANK_INPUT_N, borradores: dict[str, str] | None = None) -> Path:
    """Paso 1: los n candidatos de cada gold, en el orden en que los recibe el reranker.

    borradores (R4): la busqueda densa embebe la pregunta mas un borrador de
    respuesta del modelo; el enrutador y el reranker siguen leyendo la pregunta."""
    from tools import auditoria_61
    from tools.evaluation import eval_set
    from tools.rag import retrieve as retrieve_mod
    from tools.rag.chunk import texto_indexable
    from tools.rag.embed_store import FaissStore, embed_query

    store = FaissStore.load()
    etiquetas, _ = auditoria_61.gold_aprobado()
    preguntas = {str(r["id"]): r["messages"][1]["content"] for r in eval_set.load_eval_set()}
    if borradores:
        vectores = {preguntas[c]: embed_query(preguntas[c] + " " + borradores[c]) for c in etiquetas}
        retrieve_mod.embed_query = lambda q: vectores[q]
    datos = {}
    for cid in sorted(etiquetas):
        res = retrieve_mod.retrieve(preguntas[cid], store, top_k=n, min_score=None, use_rerank=False)
        datos[cid] = {
            "pregunta": preguntas[cid],
            "gold": {d: sorted(a) for d, a in etiquetas[cid].items()},
            "candidatos": [{"chunk_id": r.chunk_id, "doc_id": r.doc_id, "dense_score": r.dense_score,
                            "articulos": list(r.articulos_incluidos), "texto": r.text,
                            "texto_con_cita": texto_indexable(r)} for r in res],
        }
    salida.mkdir(parents=True, exist_ok=True)
    destino = salida / "candidatos.json"
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(datos)} preguntas x {n} candidatos -> {destino}")
    return destino


def puntuar(carpeta: Path, modelo: str, con_cita: bool = False, max_length: int = config.RERANK_MAX_LENGTH) -> Path:
    """Paso 2: puntajes del cross-encoder, uno por par. Retoma desde lo guardado."""
    from sentence_transformers import CrossEncoder

    datos = json.loads((carpeta / "candidatos.json").read_text(encoding="utf-8"))
    destino = carpeta / f"puntajes__{_nombre(modelo, con_cita)}.json"
    hechos = json.loads(destino.read_text(encoding="utf-8")) if destino.exists() else {}
    ce = CrossEncoder(modelo, max_length=max_length)
    campo = "texto_con_cita" if con_cita else "texto"
    inicio, nuevos = time.perf_counter(), 0
    for cid, d in datos.items():
        if cid in hechos:
            continue
        pares = [(d["pregunta"], c[campo]) for c in d["candidatos"]]
        hechos[cid] = [float(x) for x in ce.predict(pares)]
        destino.write_text(json.dumps(hechos) + "\n", encoding="utf-8")
        nuevos += 1
        ritmo = (time.perf_counter() - inicio) / nuevos
        print(f"[{modelo}] {len(hechos)}/{len(datos)} -- {ritmo:.0f}s por pregunta, "
              f"ETA ~{ritmo * (len(datos) - len(hechos)) / 60:.0f} min", flush=True)
    return destino


def medir(carpeta: Path, modelo: str | None, con_cita: bool = False, top_k: int = 10,
          piso: float | None = None) -> dict:
    """Paso 3: puesto del articulo gold tras reordenar (modelo=None: sin reordenar).

    piso: como en retrieve, despues de reordenar se quitan los fragmentos con
    coseno de e5 por debajo del piso, y entonces se corta el top_k."""
    from tools.rag.benchmark_busqueda import acierta

    datos = json.loads((carpeta / "candidatos.json").read_text(encoding="utf-8"))
    puntajes = None
    if modelo:
        puntajes = json.loads((carpeta / f"puntajes__{_nombre(modelo, con_cita)}.json").read_text(encoding="utf-8"))
    puestos = {}
    for cid, d in datos.items():
        res = [SimpleNamespace(doc_id=c["doc_id"], articulos_incluidos=c["articulos"],
                               dense_score=c.get("dense_score")) for c in d["candidatos"]]
        if puntajes is not None:
            res = [r for r, _ in sorted(zip(res, puntajes[cid]), key=lambda x: -x[1])]
        if piso is not None:
            res = [r for r in res if r.dense_score is not None and r.dense_score >= piso]
        res = res[:top_k]
        etiqueta = {doc: set(a) for doc, a in d["gold"].items()}
        puestos[cid] = next((n for n in range(1, len(res) + 1) if acierta(res[n - 1:n], etiqueta)), None)
    acierto = {f"@{k}": sum(1 for p in puestos.values() if p is not None and p <= k) for k in KS}
    return {"modelo": modelo or "sin reordenar", "con_cita": con_cita, "piso": piso, "n": len(puestos),
            "acierto": acierto, "puestos": puestos}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="paso", required=True)
    c = sub.add_parser("candidatos")
    c.add_argument("--salida", type=Path, required=True)
    c.add_argument("--n", type=int, default=config.RERANK_INPUT_N)
    c.add_argument("--borradores", type=Path, help="R4: jsonl con id y generated")
    for nombre in ("puntuar", "medir"):
        p = sub.add_parser(nombre)
        p.add_argument("--dir", type=Path, required=True)
        p.add_argument("--modelo", default=None)
        p.add_argument("--con-cita", action="store_true")
        p.add_argument("--piso", type=float, default=None)
    a = ap.parse_args(argv)
    if a.paso == "candidatos":
        borr = None
        if a.borradores:
            filas = [json.loads(l) for l in a.borradores.read_text(encoding="utf-8").splitlines() if l.strip()]
            borr = {str(f["id"]): f["generated"] for f in filas}
        candidatos(a.salida, a.n, borr)
    elif a.paso == "puntuar":
        puntuar(a.dir, a.modelo, a.con_cita)
    else:
        r = medir(a.dir, a.modelo, a.con_cita, piso=a.piso)
        print(f"{r['modelo']} (con cita: {r['con_cita']}, piso {a.piso}): " +
              "  ".join(f"{k} {v}/{r['n']}" for k, v in r["acierto"].items()))
        sufijo = f"__piso{a.piso}" if a.piso is not None else ""
        (a.dir / f"medicion__{_nombre(r['modelo'].replace(' ', '_'), a.con_cita)}{sufijo}.json").write_text(
            json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
