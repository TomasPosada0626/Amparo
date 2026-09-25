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

from tools.rag import config
from tools.rag.embed_store import SearchResult, VectorStore, embed_query


def apply_score_floor(
    results: list[SearchResult], min_score: float = config.RETRIEVAL_MIN_SCORE
) -> list[SearchResult]:
    """Descarta los resultados cuyo score DENSO cae por debajo del umbral.

    Funcion aparte (y pura) porque es la que decide si la valvula de escape se
    activa: "no encontre nada relevante" no es lo mismo que "encontre algo poco
    relevante y lo meti al prompt igual". Lo segundo es lo que produce respuestas
    con cita real y contenido equivocado.

    DECISION DE DISENO (S08): el filtro mira `dense_score`, NO `score`. El umbral
    RETRIEVAL_MIN_SCORE (0.80) esta calibrado sobre el coseno de e5, pero tras la
    fusion RRF `score` es el puntaje RRF y tras el reranking es el del
    cross-encoder -- otras escalas, no comparables con 0.80. dense_score preserva
    el coseno de e5 a lo largo de todo el pipeline, asi que la valvula sigue
    midiendo lo que fue calibrada para medir. Un chunk que solo trajo BM25 tiene
    dense_score=None (e5 no lo considero relevante) y por eso no pasa el piso:
    correcto, porque el umbral es una afirmacion sobre la relevancia SEMANTICA.
    Ver docs/m3_decisiones_rag.md.
    """
    return [r for r in results if r.dense_score is not None and r.dense_score >= min_score]


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
    if use_rerank:
        from tools.rag.rerank import rerank

        candidatos = rerank(query, candidatos, top_k=top_k, _scorer=_reranker_scorer)
    else:
        candidatos = candidatos[:top_k]

    # --- Etapa 3: valvula de escape -----------------------------------------
    # Va al FINAL, sobre el conjunto ya reordenado: da igual como se ordeno, un
    # chunk semanticamente irrelevante (dense_score bajo el piso) no debe entrar
    # al prompt. Se aplica despues del recorte a top_k para no re-expandir.
    if min_score is None:
        return candidatos
    return apply_score_floor(candidatos, min_score)
