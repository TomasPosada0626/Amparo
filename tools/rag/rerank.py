"""Reranking: un cross-encoder reordena los candidatos del retrieval.

Segunda de las dos tecnicas avanzadas de S08. Online / consulta.

POR QUE reranking en Amparo (justificacion a priori, ver
docs/m3_decisiones_rag.md):

El retrieval de S07 (y la hybrid search) usa BI-ENCODERS: vectorizan la consulta
y cada chunk POR SEPARADO y comparan vectores. Es barato y escala a miles de
chunks, pero pierde matices -- e5 tiene cosenos poco dispersos (dos textos sin
relacion dan ~0.70-0.75, ver docs/m3_decisiones_rag.md seccion 5), asi que su
top-k trae RUIDO: chunks que parecen relevantes por vector pero no responden la
pregunta. Un CROSS-ENCODER lee el par (consulta, chunk) JUNTO, con atencion
cruzada entre ambos, y produce un puntaje de relevancia mucho mas fino. Es caro
por par, asi que no se puede correr sobre todo el corpus.

El patron es un EMBUDO: recuperar mucho con lo barato (top-N con denso/hybrid),
reordenar poco con lo caro (el cross-encoder ve esos N y devuelve los K
mejores). Asi se paga el cross-encoder solo N veces por consulta, no una vez por
chunk del corpus.

sentence-transformers (el cross-encoder) es stack PESADO: depende de torch. Por
eso el import es perezoso y el modelo se cachea, igual que e5 en embed_store.py.
En local, sin la dependencia, rerank() falla con un mensaje que dice que corre
en Colab -- no con un ModuleNotFoundError mudo.
"""
from __future__ import annotations

from tools.rag import config
from tools.rag.embed_store import SearchResult

# Cache del cross-encoder: cargarlo son cientos de MB. Sin cache, la corrida
# sobre el eval set pagaria esa carga una vez por consulta. Mismo patron que
# embed_store._MODELO_CACHE.
_RERANKER_CACHE: dict[str, object] = {}


def load_reranker(model_id: str = config.RERANK_MODEL_ID):
    """Carga (una sola vez) el cross-encoder y lo deja en GPU si hay.

    Import perezoso de sentence-transformers: stack pesado, vive en Colab. El
    mensaje de error si falta la dependencia es explicito a proposito -- en local
    esto no corre, y un ModuleNotFoundError sin contexto no dice que hacer.
    """
    if model_id not in _RERANKER_CACHE:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as e:  # pragma: no cover - depende del entorno
            raise ImportError(
                "El reranking necesita sentence-transformers (stack pesado, no "
                "esta en requirements.txt). Corre en Colab, donde se instala junto "
                "a torch/transformers. Ver docs/m3_decisiones_rag.md."
            ) from e
        _RERANKER_CACHE[model_id] = CrossEncoder(model_id, max_length=config.RERANK_MAX_LENGTH)
    return _RERANKER_CACHE[model_id]


def rerank(
    query: str,
    candidates: list[SearchResult],
    *,
    top_k: int = config.RERANK_OUTPUT_K,
    model_id: str = config.RERANK_MODEL_ID,
    _scorer=None,
) -> list[SearchResult]:
    """Reordena `candidates` por relevancia (consulta, chunk) y devuelve los top_k.

    Es la salida del embudo: recibe los ~N candidatos que trajo el recuperador
    barato (denso o hybrid) y devuelve los K mejores segun el cross-encoder.

    El `score` del SearchResult devuelto pasa a ser el del cross-encoder (para
    que quien inspeccione vea por que quedo en ese puesto), pero dense_score se
    CONSERVA intacto: la valvula de escape sigue leyendo el coseno de e5, no el
    puntaje del reranker, que vive en otra escala y no esta calibrado como
    umbral. Ver docs/m3_decisiones_rag.md (valvula de escape).

    _scorer: inyectable para tests -- una funcion pares -> lista de puntajes.
    Por defecto usa el cross-encoder real (GPU). Permite probar la logica del
    embudo sin descargar el modelo.
    """
    if not candidates:
        return []

    pares = [(query, c.text) for c in candidates]
    if _scorer is not None:
        puntajes = _scorer(pares)
    else:
        modelo = load_reranker(model_id)
        puntajes = modelo.predict(pares)

    # Se reordena por puntaje del cross-encoder, descendente. zip preserva el
    # emparejamiento candidato<->puntaje aunque el scorer devuelva un ndarray.
    ordenados = sorted(zip(candidates, puntajes), key=lambda par: float(par[1]), reverse=True)

    reordenados: list[SearchResult] = []
    for candidato, puntaje in ordenados[:top_k]:
        # Se copia el SearchResult con el nuevo score. dense_score se asigna
        # DESPUES de construir, no en el constructor: si se pasara al constructor
        # como None (caso de un chunk que solo trajo BM25), __post_init__ lo
        # sobreescribiria con el score del cross-encoder -- justo lo que NO
        # queremos, porque la valvula de escape debe seguir viendo el coseno (o
        # None si no hubo coseno).
        nuevo = SearchResult(
            chunk_id=candidato.chunk_id,
            text=candidato.text,
            fuente=candidato.fuente,
            url_fuente=candidato.url_fuente,
            score=float(puntaje),
            doc_id=candidato.doc_id,
            tipo=candidato.tipo,
            articulos_incluidos=list(candidato.articulos_incluidos),
            capitulo=candidato.capitulo,
            vigente=candidato.vigente,
        )
        nuevo.dense_score = candidato.dense_score
        reordenados.append(nuevo)
    return reordenados
