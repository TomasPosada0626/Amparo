"""Ayudas para escribir data/dataset_src_v2/*.md (dataset de M1 v2).

  python -m tools.dataset_v2_ayuda normas "Arriendo"
      normas de la categoria (identifier, nombre) y las transversales
  python -m tools.dataset_v2_ayuda bases "Arriendo"
      preguntas del dataset de M1 de esa categoria: id, lado del split, si ya se
      uso en v2, parecido con el eval set, pregunta y respuesta original
  python -m tools.dataset_v2_ayuda art LEY-820-2003 20
      texto completo del articulo tal como lo vera el modelo
  python -m tools.dataset_v2_ayuda buscar "deposito arriendo" [LEY-820-2003]
      BM25 sobre el corpus (o sobre una norma): que articulos hablan de eso
"""
from __future__ import annotations

import json
import sys


def _c():
    from tools.dataset_v2 import cargar_corpus

    return cargar_corpus()


def normas(categoria: str) -> None:
    from tools.rag import corpus, ingest

    for n in corpus.NORMAS_EN_ALCANCE:
        if categoria in n.categorias or corpus.TRANSVERSAL in n.categorias:
            ident = ingest.read_frontmatter(n.path)["identifier"]
            marca = "(transversal)" if corpus.TRANSVERSAL in n.categorias else ""
            print(f"{ident:24s} {n.nombre_comun or n.filename} {marca}")


def bases(categoria: str) -> None:
    from tools.dataset_v2 import cargar_especificaciones
    from tools.evaluation import dataset, eval_set
    from tools.evaluation.similitud import IndiceTfidf

    recs = dataset.load_records()
    _, val = dataset.stratified_split(recs)
    en_val = {r["id"] for r in val}
    usadas = {e.base: e.id for e in cargar_especificaciones() if e.base is not None}
    ev = eval_set.load_eval_set()
    indice = IndiceTfidf([e["messages"][1]["content"] for e in ev])
    for r in recs:
        if r["category"] != categoria:
            continue
        q = r["messages"][1]["content"]
        mejor = indice.parecidos(q, 1)
        parecido = f"eval {ev[mejor[0][0]]['id']} {mejor[0][1]:.2f}" if mejor and mejor[0][1] >= 0.45 else ""
        uso = f"USADA en {usadas[r['id']]}" if r["id"] in usadas else ""
        lado = "val" if r["id"] in en_val else "train"
        print(f"## {r['id']} [{lado}] {uso} {parecido}\n  P: {q}\n  R: {r['messages'][2]['content']}\n")


def art(ident: str, numero: str) -> None:
    from tools.rag.chunk import normalizar_numero

    c = _c()
    idx = c.por_articulo.get((ident, normalizar_numero(numero)))
    if not idx:
        print(f"No esta: {ident} articulo {numero}")
        return
    for i in idx:
        r = c.resultados[i]
        print(f"--- {r.cita}  [chunk {r.chunk_id}]\n{r.text}\n")


def buscar(consulta: str, ident: str | None = None, n: int = 8) -> None:
    c = _c()
    doc = c.doc_de_identifier.get(ident) if ident else None
    ident_de = {v: k for k, v in c.doc_de_identifier.items()}
    for r in c.bm25.search(consulta, 2000 if doc else n):
        if doc and r.doc_id != doc:
            continue
        print(f"{ident_de[r.doc_id]}:{','.join(r.articulos_incluidos)}  {r.text[:220]!r}")
        n -= 1
        if n == 0:
            break


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"normas": normas, "bases": bases, "art": art, "buscar": buscar}[cmd](*args)
