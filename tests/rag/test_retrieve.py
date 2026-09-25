"""Tests del punto de entrada retrieve() con los tres sistemas A/B/C.

Corren sin GPU: el recuperador denso es un FakeStore con ranking fijo, embed_query
se monkeypatchea (en retrieve Y en hybrid, porque hybrid_search lo importa a su
modulo), BM25 es real (Python puro) y el cross-encoder se inyecta como scorer
fake. Lo que se prueba es la ORQUESTACION -- que los defaults reproducen S07, que
las banderas encadenan las etapas, y que la valvula de escape sigue operando
sobre dense_score.
"""
from tools.rag import config, hybrid, retrieve
from tools.rag.embed_store import SearchResult
from tools.rag.hybrid import BM25Index


def sin_gpu(monkeypatch):
    """Mockea embed_query en los DOS modulos que lo usan: retrieve (sistema A) y
    hybrid (sistemas B/C). Sin esto, el sistema B descargaria e5 de verdad."""
    monkeypatch.setattr(retrieve, "embed_query", lambda q: [0.0])
    monkeypatch.setattr(hybrid, "embed_query", lambda q: [0.0])


def make_result(chunk_id, dense_score, *, articulos=None, fuente="Ley 1480 de 2011"):
    return SearchResult(
        chunk_id=chunk_id,
        text=f"texto de {chunk_id}",
        fuente=fuente,
        url_fuente=f"https://suin/{chunk_id}",
        score=dense_score,
        articulos_incluidos=articulos or [],
        dense_score=dense_score,
    )


class FakeStore:
    """Store denso fake. `metadata` alimenta a BM25; `search` devuelve el ranking
    denso fijo (ignora el embedding)."""

    def __init__(self, ranking, metadata=None):
        self._ranking = ranking
        self.metadata = metadata or []

    def search(self, query_embedding, top_k):
        return self._ranking[:top_k]


CORPUS = [
    {"chunk_id": "c1", "text": "El derecho de peticion se resuelve en quince dias", "fuente": "CPACA", "url_fuente": "u1", "articulos_incluidos": ["14"], "vigente": True},
    {"chunk_id": "c2", "text": "Articulo 64 justas causas para terminar el contrato de trabajo", "fuente": "CST", "url_fuente": "u2", "articulos_incluidos": ["64"], "vigente": True},
    {"chunk_id": "c3", "text": "La garantia legal del producto cubre defectos de fabrica", "fuente": "Ley 1480", "url_fuente": "u3", "articulos_incluidos": ["8"], "vigente": True},
]


# --- Sistema A: denso puro (comportamiento S07) -----------------------------

def test_sistema_A_por_defecto_es_denso_puro(monkeypatch):
    """Con las dos banderas apagadas, retrieve() no toca BM25 ni el reranker:
    devuelve el ranking del store tal cual, recortado a top_k. Es literalmente
    el retrieval de S07."""
    sin_gpu(monkeypatch)
    ranking = [make_result("c1", 0.90), make_result("c2", 0.88), make_result("c3", 0.85)]
    store = FakeStore(ranking, CORPUS)

    resultado = retrieve.retrieve("cualquier consulta", store, top_k=2, min_score=None)

    assert [r.chunk_id for r in resultado] == ["c1", "c2"]


def test_la_valvula_de_escape_filtra_por_dense_score(monkeypatch):
    """El chunk con coseno bajo el piso no entra, aunque el store lo trajera."""
    sin_gpu(monkeypatch)
    ranking = [make_result("c1", 0.90), make_result("c2", 0.50)]  # c2 bajo 0.80
    store = FakeStore(ranking, CORPUS)

    resultado = retrieve.retrieve("consulta", store, top_k=5, min_score=0.80)

    assert [r.chunk_id for r in resultado] == ["c1"]


# --- Sistema B: +hybrid ------------------------------------------------------

def test_sistema_B_hybrid_incorpora_candidatos_de_bm25(monkeypatch):
    """Con use_hybrid, un termino exacto ('articulo 64') que BM25 rescata debe
    aparecer aunque el ranking denso no lo trajera arriba. min_score=None para
    aislar el efecto de la fusion de la valvula."""
    sin_gpu(monkeypatch)
    # El denso solo trae c1 y c3; c2 (el del articulo 64) lo aporta BM25.
    ranking = [make_result("c1", 0.82, fuente="CPACA"), make_result("c3", 0.80, fuente="Ley 1480")]
    store = FakeStore(ranking, CORPUS)

    resultado = retrieve.retrieve(
        "articulo 64 justas causas", store, top_k=5, min_score=None, use_hybrid=True
    )
    ids = [r.chunk_id for r in resultado]

    assert "c2" in ids  # rescatado por BM25


def test_sistema_B_acepta_un_bm25_ya_construido(monkeypatch):
    """En un lote, el BM25Index se construye una vez y se reusa. retrieve() debe
    aceptarlo en vez de reconstruirlo por consulta."""
    sin_gpu(monkeypatch)
    ranking = [make_result("c1", 0.82, fuente="CPACA")]
    store = FakeStore(ranking, CORPUS)
    bm25 = BM25Index(CORPUS)

    resultado = retrieve.retrieve(
        "articulo 64", store, top_k=5, min_score=None, use_hybrid=True, bm25=bm25
    )

    assert any(r.chunk_id == "c2" for r in resultado)


# --- Sistema C: +hybrid +reranker -------------------------------------------

# El scorer fake identifica el chunk por una palabra distintiva de su texto (el
# texto NO contiene el chunk_id). c2 = "trabajo", c1 = "peticion", c3 = "garantia".
def scorer_por_palabra(preferencias):
    def _scorer(pares):
        puntajes = []
        for _, texto in pares:
            p = 0.0
            for palabra, valor in preferencias.items():
                if palabra in texto:
                    p = valor
                    break
            puntajes.append(p)
        return puntajes
    return _scorer


def test_sistema_C_reordena_con_el_cross_encoder(monkeypatch):
    """Con use_rerank, el scorer inyectado decide el orden final. Se verifica que
    el reranker corre sobre los candidatos de hybrid y que el orden es el suyo."""
    sin_gpu(monkeypatch)
    ranking = [make_result("c1", 0.85, fuente="CPACA"), make_result("c3", 0.83, fuente="Ley 1480")]
    store = FakeStore(ranking, CORPUS)

    # El cross-encoder fake prefiere c2 (trabajo), luego c1 (peticion), luego c3 (garantia).
    scorer = scorer_por_palabra({"trabajo": 0.9, "peticion": 0.5, "garantia": 0.1})

    resultado = retrieve.retrieve(
        "articulo 64", store, top_k=3, min_score=None,
        use_hybrid=True, use_rerank=True, _reranker_scorer=scorer,
    )
    ids = [r.chunk_id for r in resultado]

    assert ids[0] == "c2"  # el reranker lo puso primero


def test_sistema_C_respeta_la_valvula_de_escape_sobre_dense_score(monkeypatch):
    """Aunque el cross-encoder ame un chunk (score alto), si su coseno e5 esta
    bajo el piso no entra: la valvula lee dense_score, no el score del reranker.
    Es la decision de diseno central de la integracion."""
    sin_gpu(monkeypatch)
    ranking = [make_result("c1", 0.90, fuente="CPACA")]
    store = FakeStore(ranking, CORPUS)

    # El reranker le da a c2 (dense_score None, solo BM25) el puntaje mas alto.
    scorer = scorer_por_palabra({"trabajo": 9.9})

    resultado = retrieve.retrieve(
        "articulo 64", store, top_k=5, min_score=0.80,
        use_hybrid=True, use_rerank=True, _reranker_scorer=scorer,
    )
    ids = [r.chunk_id for r in resultado]

    # c2 tiene dense_score None (solo BM25) -> no pasa el piso, pese al score 9.9.
    assert "c2" not in ids
    assert "c1" in ids


def test_el_reranker_recibe_mas_candidatos_de_los_que_devuelve(monkeypatch):
    """El embudo: retrieve pide RERANK_INPUT_N candidatos y el reranker devuelve
    top_k. Se comprueba que el scorer recibe mas pares que el top_k final."""
    sin_gpu(monkeypatch)
    # Store con muchos candidatos densos.
    corpus_grande = [
        {"chunk_id": f"d{i}", "text": f"contrato trabajo articulo numero {i}", "fuente": "CST", "url_fuente": f"u{i}", "articulos_incluidos": [str(i)], "vigente": True}
        for i in range(20)
    ]
    ranking = [make_result(f"d{i}", 0.85, fuente="CST") for i in range(20)]
    store = FakeStore(ranking, corpus_grande)

    vistos = {}
    def scorer(pares):
        vistos["n"] = len(pares)
        return [1.0 / (i + 1) for i in range(len(pares))]

    resultado = retrieve.retrieve(
        "contrato trabajo", store, top_k=3, min_score=None,
        use_hybrid=True, use_rerank=True, _reranker_scorer=scorer,
    )

    assert len(resultado) == 3          # top_k final
    assert vistos["n"] > 3              # el reranker vio mas candidatos que el top_k
