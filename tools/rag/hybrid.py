"""Hybrid search: BM25 (lexico) + denso (semantico), fusionados con RRF.

Online / consulta. Complementa el retrieval denso del RAG base.

El retrieval denso con e5 recupera por SIGNIFICADO. Eso es lo correcto para la
consulta coloquial de Amparo ("me despidieron sin pagarme la liquidacion"), pero
difumina los TERMINOS EXACTOS. En derecho eso importa: "articulo 64", "Ley 1480",
"habeas data" son cadenas literales, y e5 tiende a mezclar el articulo 64 con el
46 o el 65 porque semanticamente se parecen. BM25 puntua por coincidencia lexica
premiando los terminos raros: cubre exactamente el punto ciego del denso, y sus
fallos no se correlacionan con los de e5, asi que combinarlos mejora la
recuperacion en vez de amplificar un mismo error.

La fusion es Reciprocal Rank Fusion (RRF), no un promedio de puntajes: los
puntajes de BM25 (~12.7) y del coseno (~0.83) viven en escalas incomparables y
promediarlos no significa nada. RRF fusiona PUESTOS -- cada documento suma
1/(k + puesto) en cada lista y se reordena por la suma. Es inmune a las escalas
y premia el consenso entre los dos recuperadores.

rank_bm25 es Python puro (no arrastra torch), asi que este modulo -- salvo la
parte densa, que llama a e5 -- corre sin GPU. El import de rank_bm25 es perezoso
para que importar el modulo no exija la dependencia si solo se usa la funcion
pura de RRF.
"""
from __future__ import annotations

import re

from tools.rag import config
from tools.rag.embed_store import SearchResult, VectorStore, embed_query, metadata_to_result

# Tokenizacion para BM25: minusculas + palabras alfanumericas. Deliberadamente
# simple (no stemming, no stopwords): en dominio legal los "terminos raros" que
# BM25 debe premiar son justo numeros y nombres propios ("1480", "habeas"), que
# no conviene alterar. Se mantiene \w+ con unicode para no perder tildes ni la ñ.
_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Texto -> lista de tokens en minuscula, para BM25."""
    return _TOKEN_PATTERN.findall(text.lower())


class BM25Index:
    """Indice lexico BM25 sobre los mismos chunks que el indice denso.

    Se construye a partir de store.metadata (la lista de dicts que el FaissStore
    ya guarda, uno por chunk, con su `text`): asi el corpus lexico y el semantico
    son literalmente los mismos chunks, en el mismo orden, y un puesto `i` de
    BM25 apunta al mismo chunk que el puesto `i` del denso. No se recomputa ni se
    re-lee nada del disco.
    """

    def __init__(self, metadata: list[dict]):
        from rank_bm25 import BM25Okapi  # import perezoso: dependencia de S08

        self._metadata = metadata
        corpus_tokens = [tokenize(m.get("text", "")) for m in metadata]
        # rank_bm25 no acepta un corpus vacio (divide por el largo promedio de
        # documento). Un indice vacio es un estado valido (store recien creado),
        # asi que se marca y search() devuelve [] en vez de reventar.
        self._vacio = len(corpus_tokens) == 0 or all(not t for t in corpus_tokens)
        self._bm25 = None if self._vacio else BM25Okapi(corpus_tokens)

    def __len__(self) -> int:
        return len(self._metadata)

    def search(self, query: str, top_n: int) -> list[SearchResult]:
        """Top-n chunks por score BM25, como SearchResult (misma moneda que el denso).

        El `score` que lleva el SearchResult es el de BM25 (no comparable con el
        coseno): sirve para ORDENAR dentro de esta lista, y la fusion posterior
        usa el PUESTO, no el valor. dense_score queda en None a proposito -- este
        chunk no vino por la via densa, y marcarlo asi permite que la fusion
        distinga "consenso de ambos" de "solo lexico".
        """
        if self._vacio or top_n <= 0:
            return []

        scores = self._bm25.get_scores(tokenize(query))
        # argsort descendente sin numpy expuesto en la firma: ordenamos indices
        # por score. Se cortan los de score 0 (ningun termino coincidio): incluir
        # un chunk sin una sola coincidencia lexica es ruido, no un candidato.
        ordenados = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        resultados: list[SearchResult] = []
        for idx in ordenados[:top_n]:
            if scores[idx] <= 0:
                break
            resultado = metadata_to_result(self._metadata[idx], float(scores[idx]))
            resultado.dense_score = None  # no vino por la via densa
            resultados.append(resultado)
        return resultados


def reciprocal_rank_fusion(
    rankings: list[list[SearchResult]], *, k: int = config.RRF_K, top_k: int
) -> list[SearchResult]:
    """Fusiona varios rankings en uno solo por Reciprocal Rank Fusion.

    RRF(chunk) = Σ_listas 1/(k + puesto_en_la_lista), sumando solo sobre las
    listas donde el chunk aparece. Se reordena por esa suma. Funcion PURA: no
    toca modelos ni disco, solo listas de SearchResult -- por eso es la parte de
    la hybrid search que se testea sin ninguna dependencia pesada.

    POR QUE puestos y no puntajes: los recuperadores devuelven scores en escalas
    incomparables (BM25 ~12.7, coseno ~0.83). Sumar 1/(k+puesto) ignora el valor
    del score y solo mira "que tan arriba" quedo el chunk en cada lista, que si
    es comparable. Un chunk que ambos recuperadores ponen arriba (consenso) gana
    sobre uno que solo un recuperador ama.

    El SearchResult resultante lleva en `score` el puntaje RRF (para ordenar) y
    conserva dense_score: si el chunk aparecio en algun ranking denso, ese valor
    sobrevive para la valvula de escape; si solo vino por BM25, queda None.
    """
    acumulado: dict[str, float] = {}
    representante: dict[str, SearchResult] = {}
    dense_score: dict[str, float | None] = {}

    for ranking in rankings:
        for puesto, resultado in enumerate(ranking):
            cid = resultado.chunk_id
            acumulado[cid] = acumulado.get(cid, 0.0) + 1.0 / (k + puesto + 1)
            # El primer SearchResult que veamos para este chunk queda como
            # representante (trae la metadata citable, que es identica en ambos
            # recuperadores porque es el mismo chunk).
            if cid not in representante:
                representante[cid] = resultado
            # dense_score: nos quedamos con el valor no-None si alguna lista lo
            # trae. Un chunk puede venir de BM25 (dense_score=None) en una lista y
            # del denso (coseno) en otra; el coseno es el que le sirve a la valvula.
            if dense_score.get(cid) is None and resultado.dense_score is not None:
                dense_score[cid] = resultado.dense_score

    fusionados: list[SearchResult] = []
    for cid, puntaje_rrf in sorted(acumulado.items(), key=lambda x: x[1], reverse=True):
        base = representante[cid]
        fusionado = metadata_to_result(
            {
                "chunk_id": base.chunk_id,
                "text": base.text,
                "fuente": base.fuente,
                "url_fuente": base.url_fuente,
                "doc_id": base.doc_id,
                "tipo": base.tipo,
                "articulos_incluidos": base.articulos_incluidos,
                "capitulo": base.capitulo,
                "vigente": base.vigente,
            },
            puntaje_rrf,
        )
        fusionado.dense_score = dense_score.get(cid)
        fusionados.append(fusionado)

    return fusionados[:top_k]


def hybrid_search(
    query: str,
    store: VectorStore,
    bm25: BM25Index,
    *,
    top_n: int = config.HYBRID_TOP_N,
    top_k: int = config.HYBRID_TOP_N,
) -> list[SearchResult]:
    """Recupera con denso y BM25 en paralelo y fusiona con RRF.

    top_n: cuantos candidatos pide CADA recuperador antes de fusionar.
    top_k: cuantos devuelve la fusion. Por defecto ambos son HYBRID_TOP_N porque
    hybrid_search suele alimentar el embudo del reranker (que recibe ~30 y
    reordena a 5); cuando se usa hybrid SIN reranker, quien llama recorta a TOP_K.

    Separar el recuperador denso (store.search) del lexico (bm25.search) y
    fusionar despues es lo que mantiene el diseño componible: el denso es
    exactamente el de S07, sin tocar.
    """
    denso = store.search(embed_query(query), top_k=top_n)
    lexico = bm25.search(query, top_n=top_n)
    return reciprocal_rank_fusion([denso, lexico], top_k=top_k)
