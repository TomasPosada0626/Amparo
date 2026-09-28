"""Retrieve: recuperacion de chunks, configurable de ingenuo a avanzado.

Etapa 5 de 7 del pipeline RAG. Online / consulta.

Un unico punto de entrada, tres configuraciones, controladas por bandera:
  - A: denso puro (coseno e5, top-k). Es el DEFAULT.
  - B: denso + BM25, fusionados con RRF.
  - C: hybrid -> cross-encoder reordena el top-N a top-k.

Una sola funcion con banderas, en vez de tres funciones separadas, mantiene las
tres configuraciones sobre el mismo camino de codigo: lo unico que cambia entre
ellas es el retrieval, con el mismo prompt y el mismo generador. Asi cualquier
diferencia entre A, B y C es atribuible a la tecnica y no a una divergencia
accidental de implementacion. Con las dos banderas apagadas, A es identico al
retrieval base, y los tests lo garantizan.

Ver docs/m3_decisiones_rag.md para la justificacion de cada tecnica.
"""
from __future__ import annotations

import re

from tools.rag import config
from tools.rag.embed_store import SearchResult, VectorStore, embed_query

_MENCIONA_NORMA = re.compile(
    r"\b(ley|decreto|codigo|código|constituci|cst|cgp|cpaca|estatuto)", re.IGNORECASE
)


def es_referencia_exacta(resultado: SearchResult, query: str) -> bool:
    """¿El chunk contiene un articulo que la consulta cita explicitamente?

    Es el caso para el que existe la hybrid search: "¿que dice el articulo 64 del
    codigo sustantivo del trabajo?". BM25 encuentra el chunk por el termino
    exacto, pero si e5 no lo puso en su propio top, llega sin coseno
    (dense_score None) y el piso semantico lo descartaria. Esta regla lo deja
    pasar SOLO si la consulta cita ese numero de articulo y, cuando la consulta
    nombra una norma, el chunk es de esa norma (el 64 del CGP no pasa por una
    pregunta sobre el CST).

    Hallazgo que la motiva: corrida de S08 del 2026-09-27, ver
    docs/m3_decisiones_rag.md (seccion 25).
    """
    from tools.rag.agentico import _puntaje_norma, articulos_citados  # perezoso: evita ciclo

    citados = articulos_citados(query)
    if not citados:
        return False
    propios = {a.upper() for a in resultado.articulos_incluidos}
    if not citados & propios:
        return False
    if _MENCIONA_NORMA.search(query or ""):
        return _puntaje_norma(query, resultado.fuente) > 0
    return True


def pasa_el_piso(resultado: SearchResult, min_score: float, query: str = "") -> bool:
    """Criterio de la valvula de escape para UN chunk.

    - Con coseno de e5 (dense_score): pasa si supera el umbral calibrado.
    - Sin coseno (solo lo trajo BM25): pasa solo si es una referencia exacta a un
      articulo citado en la consulta (es_referencia_exacta). Un chunk lexico sin
      esa referencia no tiene como verificarse contra el umbral semantico, y se
      sigue descartando, como antes.
    """
    if resultado.dense_score is not None:
        return resultado.dense_score >= min_score
    return es_referencia_exacta(resultado, query)


def apply_score_floor(
    results: list[SearchResult], min_score: float = config.RETRIEVAL_MIN_SCORE, query: str = ""
) -> list[SearchResult]:
    """Descarta los resultados cuyo score DENSO cae por debajo del umbral.

    Funcion aparte (y pura) porque es la que decide si la valvula de escape se
    activa: "no encontre nada relevante" no es lo mismo que "encontre algo poco
    relevante y lo meti al prompt igual". Lo segundo es lo que produce respuestas
    con cita real y contenido equivocado.

    DECISION DE DISENO (S08): el filtro mira `dense_score`, NO `score`. El umbral
    RETRIEVAL_MIN_SCORE esta calibrado sobre el coseno de e5, pero tras la
    fusion RRF `score` es el puntaje RRF y tras el reranking es el del
    cross-encoder -- otras escalas, no comparables con ese umbral. dense_score
    preserva el coseno de e5 a lo largo de todo el pipeline, asi que la valvula sigue
    midiendo lo que fue calibrada para medir. Un chunk que solo trajo BM25 tiene
    dense_score=None (e5 no lo considero relevante) y por eso no pasa el piso:
    correcto, porque el umbral es una afirmacion sobre la relevancia SEMANTICA.
    Excepcion (S10, hallazgo de la corrida de S08): un chunk solo-BM25 que es
    referencia exacta a un articulo citado en la consulta si pasa. Ver
    pasa_el_piso y docs/m3_decisiones_rag.md (seccion 25).
    """
    return [r for r in results if pasa_el_piso(r, min_score, query)]


def retrieve(
    query: str,
    store: VectorStore,
    *,
    top_k: int = config.TOP_K,
    min_score: float | None = config.RETRIEVAL_MIN_SCORE,
    use_hybrid: bool = False,
    use_rerank: bool = False,
    bm25=None,
    _reranker_scorer=None,
) -> list[SearchResult]:
    """Recupera los chunks mas relevantes para la consulta.

    use_hybrid / use_rerank: arman los sistemas B y C. Con ambos en False el
    comportamiento es identico al de S07 (sistema A).

    min_score=None desactiva el piso -- util solo para calibrarlo (ver seccion 5
    de docs/m3_decisiones_rag.md). El piso opera sobre dense_score (ver
    apply_score_floor), asi que sigue teniendo sentido con hybrid y rerank.

    bm25: un BM25Index ya construido. Se pasa desde afuera para no reconstruirlo
    en cada consulta (construirlo recorre todo el corpus). Si use_hybrid=True y no
    se pasa, se construye aqui a partir de store.metadata -- correcto pero mas
    lento en un lote.

    _reranker_scorer: gancho de test para inyectar un scorer fake y no descargar
    el cross-encoder. En produccion es None y se usa el modelo real.
    """
    # Cuantos candidatos recuperar antes de recortar. Con reranker, el embudo
    # necesita RERANK_INPUT_N candidatos para que el cross-encoder tenga de donde
    # elegir; con hybrid solo, HYBRID_TOP_N; sin nada, top_k directo.
    if use_rerank:
        n_recuperar = config.RERANK_INPUT_N
    elif use_hybrid:
        n_recuperar = config.HYBRID_TOP_N
    else:
        n_recuperar = top_k

    # --- Etapa 1: candidatos (denso, o hybrid denso+BM25) -------------------
    if use_hybrid:
        from tools.rag.hybrid import BM25Index, hybrid_search

        if bm25 is None:
            bm25 = BM25Index(store.metadata)
        candidatos = hybrid_search(query, store, bm25, top_n=n_recuperar, top_k=n_recuperar)
    else:
        candidatos = store.search(embed_query(query), top_k=n_recuperar)

    # --- Etapa 2: reranking (opcional) --------------------------------------
    # El reranker ordena TODOS los candidatos; el recorte a top_k va despues del
    # piso (etapa 3).
    if use_rerank:
        from tools.rag.rerank import rerank

        candidatos = rerank(query, candidatos, top_k=len(candidatos), _scorer=_reranker_scorer)

    # --- Etapa 3: valvula de escape, y DESPUES el recorte a top_k -----------
    # Antes el recorte iba primero: en B y C, chunks solo-BM25 ocupaban puestos
    # del top_k y el piso los borraba despues, dejando menos de top_k chunks (o
    # ninguno) aunque hubiera candidatos validos mas abajo. Corrida de S08 del
    # 2026-09-27: 3.55 chunks promedio en B y 4 consultas gold sin contexto en C,
    # contra 4.57 y 0 en A. Filtrar primero y recortar despues llena el top_k con
    # los mejores candidatos que SI pasan. En A no cambia nada: la lista viene
    # ordenada por coseno y el piso solo quita la cola.
    if min_score is not None:
        candidatos = apply_score_floor(candidatos, min_score, query)
    return candidatos[:top_k]
