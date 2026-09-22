"""Retrieve: busqueda por similitud de coseno, top-k.

Etapa 5 de 7 del pipeline RAG (S07). Online / consulta.

Deliberadamente simple: sin hybrid search (BM25 + denso), sin reranking con
cross-encoder, sin fusion de rankings (RRF). Eso es S08, y solo entra si la
tabla de consultas fallidas de docs/m3_decisiones_rag.md (seccion 8) lo
justifica con un delta medido -- mismo estandar que M1/M2.
"""
from __future__ import annotations

from tools.rag import config
from tools.rag.embed_store import SearchResult, VectorStore, embed_query


def apply_score_floor(
    results: list[SearchResult], min_score: float = config.RETRIEVAL_MIN_SCORE
) -> list[SearchResult]:
    """Descarta los resultados por debajo del umbral.

    Funcion aparte (y pura) porque es la que decide si la valvula de escape se
    activa: "no encontre nada relevante" no es lo mismo que "encontre algo poco
    relevante y lo meti al prompt igual". Lo segundo es lo que produce
    respuestas con cita real y contenido equivocado.
    """
    return [r for r in results if r.score >= min_score]


def retrieve(
    query: str,
    store: VectorStore,
    *,
    top_k: int = config.TOP_K,
    min_score: float | None = config.RETRIEVAL_MIN_SCORE,
) -> list[SearchResult]:
    """Recupera los chunks mas similares a la consulta.

    min_score=None desactiva el piso -- util solo para calibrarlo (ver seccion 5
    de docs/m3_decisiones_rag.md: el valor actual es un punto de partida, no una
    medicion, y hay que mirar la distribucion de scores con y sin cobertura en
    el corpus antes de fijarlo).
    """
    resultados = store.search(embed_query(query), top_k=top_k)
    if min_score is None:
        return resultados
    return apply_score_floor(resultados, min_score)
