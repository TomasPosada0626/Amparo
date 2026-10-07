"""Tests de la hybrid search (S08): BM25 + RRF.

Corren sin GPU: rank_bm25 es Python puro y el recuperador denso se sustituye por
un store fake con un ranking fijo. RRF se prueba como funcion pura. La parte que
SI necesita GPU -- el embedding de la consulta dentro de hybrid_search -- se
aisla monkeypatcheando embed_query, igual que se haria con e5 en local.
"""
import pytest

from tools.rag import hybrid
from tools.rag.embed_store import SearchResult


def make_result(chunk_id, score, *, dense_score="mismo", articulos=None, fuente="Ley 1480 de 2011"):
    r = SearchResult(
        chunk_id=chunk_id,
        text=f"texto de {chunk_id}",
        fuente=fuente,
        url_fuente=f"https://suin/{chunk_id}",
        score=score,
        articulos_incluidos=articulos or [],
    )
    if dense_score != "mismo":
        r.dense_score = dense_score
    return r


# --- RRF: funcion pura -------------------------------------------------------

def test_rrf_premia_el_consenso_entre_los_dos_rankings():
    """Un chunk que ambos recuperadores ponen arriba debe ganarle a uno que solo
    un recuperador ama. Es el punto de fusionar: consenso > entusiasmo aislado."""
    denso = [make_result("A", 0.9), make_result("B", 0.8), make_result("C", 0.7)]
    lexico = [make_result("C", 12.0), make_result("A", 8.0), make_result("Z", 4.0)]

    fusionado = hybrid.reciprocal_rank_fusion([denso, lexico], top_k=4)
    ids = [r.chunk_id for r in fusionado]

    # A aparece 1o y 2o; C aparece 3o y 1o. Ambos con consenso, arriba de B y Z
    # que aparecen en una sola lista.
    assert ids[0] in {"A", "C"}
    assert ids[1] in {"A", "C"}
    assert set(ids[:2]) == {"A", "C"}


def test_rrf_ignora_la_escala_de_los_puntajes():
    """BM25 (~12) y coseno (~0.8) son incomparables: RRF usa el PUESTO, no el
    valor. Multiplicar por 100 los scores de una lista no debe cambiar el orden
    fusionado -- si lo cambiara, estariamos promediando escalas, que es el error
    que RRF evita."""
    denso = [make_result("A", 0.9), make_result("B", 0.8)]
    lexico = [make_result("B", 12.0), make_result("A", 8.0)]
    lexico_inflado = [make_result("B", 1200.0), make_result("A", 800.0)]

    orden_1 = [r.chunk_id for r in hybrid.reciprocal_rank_fusion([denso, lexico], top_k=2)]
    orden_2 = [r.chunk_id for r in hybrid.reciprocal_rank_fusion([denso, lexico_inflado], top_k=2)]

    assert orden_1 == orden_2


def test_rrf_conserva_la_metadata_citable():
    """La fusion no puede perder la cita: si el chunk fusionado pierde fuente o
    url, el resultado es incitable y todo el RAG deja de servir para su proposito."""
    denso = [make_result("A", 0.9, articulos=["64"], fuente="Codigo Sustantivo del Trabajo")]
    lexico = [make_result("A", 5.0, articulos=["64"], fuente="Codigo Sustantivo del Trabajo")]

    [fusionado] = hybrid.reciprocal_rank_fusion([denso, lexico], top_k=1)

    assert fusionado.fuente == "Codigo Sustantivo del Trabajo"
    assert fusionado.url_fuente == "https://suin/A"
    assert fusionado.articulos_incluidos == ["64"]
    assert "Articulo 64" in fusionado.cita


def test_rrf_preserva_el_dense_score_para_la_valvula_de_escape():
    """`score` pasa a ser el puntaje RRF, pero dense_score debe conservar el
    coseno de e5: es lo que lee la valvula de escape, calibrada sobre e5 y no
    sobre RRF. Si el chunk vino del denso en una lista y de BM25 (dense_score
    None) en otra, gana el coseno."""
    denso = [make_result("A", 0.83, dense_score=0.83)]
    lexico = [make_result("A", 9.0, dense_score=None)]

    [fusionado] = hybrid.reciprocal_rank_fusion([denso, lexico], top_k=1)

    assert fusionado.dense_score == 0.83
    assert fusionado.score != 0.83  # score es RRF, no el coseno


def test_rrf_marca_none_el_dense_score_de_un_chunk_solo_lexico():
    """Un chunk que solo trajo BM25 no tiene coseno: dense_score debe quedar
    None, para que la valvula de escape sepa que ese chunk no pasa su umbral (no
    tiene score denso que comparar)."""
    denso = [make_result("A", 0.9, dense_score=0.9)]
    lexico = [make_result("SOLO_BM25", 7.0, dense_score=None)]

    fusionado = hybrid.reciprocal_rank_fusion([denso, lexico], top_k=2)
    por_id = {r.chunk_id: r for r in fusionado}

    assert por_id["SOLO_BM25"].dense_score is None


# --- BM25: indice real -------------------------------------------------------

def corpus_fake():
    return [
        {"chunk_id": "c1", "text": "El derecho de peticion se resuelve en quince dias", "fuente": "CPACA", "url_fuente": "u1", "articulos_incluidos": ["14"], "vigente": True},
        {"chunk_id": "c2", "text": "Articulo 64 justas causas para terminar el contrato de trabajo", "fuente": "CST", "url_fuente": "u2", "articulos_incluidos": ["64"], "vigente": True},
        {"chunk_id": "c3", "text": "La garantia legal del producto cubre defectos de fabrica", "fuente": "Ley 1480", "url_fuente": "u3", "articulos_incluidos": ["8"], "vigente": True},
    ]


def test_bm25_encuentra_el_termino_exacto_que_el_denso_difuminaria():
    """El caso de uso de BM25: 'articulo 64' literal. Debe poner c2 de primero,
    que es justo donde el denso mezcla el 64 con articulos semanticamente
    parecidos."""
    idx = hybrid.BM25Index(corpus_fake())

    resultados = idx.search("articulo 64 despido", top_n=3)

    assert resultados[0].chunk_id == "c2"
    assert resultados[0].dense_score is None  # no vino por la via densa


def test_bm25_no_devuelve_chunks_sin_ninguna_coincidencia_lexica():
    """Un chunk donde no coincidio un solo termino es ruido, no un candidato:
    incluirlo solo ensuciaria la fusion."""
    idx = hybrid.BM25Index(corpus_fake())

    resultados = idx.search("garantia producto", top_n=3)
    ids = [r.chunk_id for r in resultados]

    assert "c3" in ids
    assert "c1" not in ids  # 'garantia'/'producto' no aparecen en c1


def test_bm25_sobre_indice_vacio_no_revienta():
    """Un store recien creado tiene metadata vacia: BM25 debe devolver [] en vez
    de fallar (rank_bm25 divide por el largo promedio de documento)."""
    idx = hybrid.BM25Index([])

    assert len(idx) == 0
    assert idx.search("lo que sea", top_n=5) == []


# --- hybrid_search: integracion con store fake ------------------------------

class FakeStore:
    """Store denso fake: devuelve un ranking fijo de SearchResult, para probar
    hybrid_search sin e5 ni faiss."""

    def __init__(self, ranking):
        self._ranking = ranking

    def search(self, query_embedding, top_k):
        return self._ranking[:top_k]


def test_hybrid_search_fusiona_denso_y_bm25(monkeypatch):
    """El pegamento: hybrid_search corre el denso (fake) y BM25 (real) y los
    fusiona. Con 'articulo 64', BM25 sube c2; el denso trae c1. La fusion debe
    contener ambos."""
    # embed_query llama a e5 (GPU): se sustituye por un vector cualquiera, el
    # FakeStore lo ignora.
    monkeypatch.setattr(hybrid, "embed_query", lambda q: [0.0])

    denso_ranking = [
        make_result("c1", 0.82, articulos=["14"], fuente="CPACA"),
        make_result("c3", 0.79, articulos=["8"], fuente="Ley 1480"),
    ]
    store = FakeStore(denso_ranking)
    bm25 = hybrid.BM25Index(corpus_fake())

    fusionado = hybrid.hybrid_search("articulo 64 justas causas", store, bm25, top_n=3, top_k=5)
    ids = [r.chunk_id for r in fusionado]

    assert "c2" in ids  # lo aporto BM25 (termino exacto)
    assert "c1" in ids  # lo aporto el denso


def test_bm25_encuentra_aunque_la_pregunta_venga_sin_tildes():
    """RAG-1: el corpus viene con tildes y las preguntas sin ellas.

    No es un descuido de quien pregunta: el dataset de M1 y el eval set estan
    escritos sin tildes a proposito, porque asi escribe la gente desde el
    celular. Con el tokenizador anterior el termino nunca empataba, y 33 de las
    75 preguntas del eval set perdian al menos una palabra que SI esta en el
    corpus ("liquidacion", "credito", "cedula", "cirugia"). Es la causa de que
    "Me despidieron sin pagarme la liquidacion" trajera articulos del Codigo
    General del Proceso en vez de los laborales.
    """
    from tools.rag.hybrid import tokenize

    for sin_tilde, con_tilde in (("liquidacion", "liquidación"),
                                 ("peticion", "petición"),
                                 ("credito", "crédito"),
                                 ("cedula", "cédula")):
        assert tokenize(sin_tilde) == tokenize(con_tilde), (
            f"{sin_tilde!r} y {con_tilde!r} siguen siendo tokens distintos")


def test_la_enne_no_se_confunde_con_la_ene():
    """Quitar todas las marcas combinantes convertiria "año" en "ano", que en
    texto legal no es lo mismo. La ñ se recompone antes de filtrar."""
    from tools.rag.hybrid import tokenize

    assert tokenize("año") != tokenize("ano")
    assert tokenize("año") == ["año"]
    # Y sigue empatando consigo misma venga como venga normalizada.
    import unicodedata
    assert tokenize(unicodedata.normalize("NFD", "año")) == tokenize("año")


def _res(chunk_id, fuente, articulos, dense=None):
    from tools.rag.embed_store import SearchResult
    return SearchResult(chunk_id=chunk_id, text=f"texto de {chunk_id}", fuente=fuente,
                        url_fuente="http://x", score=1.0, articulos_incluidos=articulos,
                        dense_score=dense)


def test_un_articulo_que_solo_encuentra_bm25_llega_al_top_k():
    """RAG-2: la aritmetica del RRF se lo impedia.

    Un chunk en las dos listas suma 1/(k+1) dos veces; uno de solo BM25, aunque
    quede primero, suma 1/(k+1) una vez -- 0.0328 contra 0.0164 con k=60. Como
    el denso casi siempre aporta cinco chunks que tambien estan en la lexica, el
    candidato lexico puro nunca entraba al top-5. Y ese es exactamente el caso
    para el que existe la busqueda hibrida: en la demo de S08, para "articulo 64
    del Codigo Sustantivo del Trabajo", B devolvia los articulos 468, 62 y 466.
    """
    from tools.rag.hybrid import promover_referencias_exactas, reciprocal_rank_fusion

    CST = "Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo)"
    consenso = [_res(f"cst::{n}", CST, [str(n)], dense=0.85) for n in (46, 158, 165, 468, 62)]
    solo_bm25 = _res("cst::64", CST, ["64"])          # sin dense_score
    query = "que dice el articulo 64 del codigo sustantivo del trabajo"

    fusionados = reciprocal_rank_fusion([consenso, consenso + [solo_bm25]], top_k=10)
    ids_sin_promover = [r.chunk_id for r in fusionados[:5]]
    assert "cst::64" not in ids_sin_promover, (
        "el escenario de la prueba no reproduce el fallo que RAG-2 describe")

    promovidos = promover_referencias_exactas(fusionados, query)
    assert promovidos[0].chunk_id == "cst::64", (
        f"la referencia exacta sigue sin subir: {[r.chunk_id for r in promovidos[:5]]}")


def test_no_se_promueve_el_mismo_numero_de_otra_norma():
    """El articulo 64 del Codigo General del Proceso no puede subir ante una
    pregunta que nombra el Codigo Sustantivo del Trabajo."""
    from tools.rag.hybrid import promover_referencias_exactas

    CST = "Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo)"
    CGP = "Ley 1564 de 2012 (Codigo General del Proceso)"
    resultados = [_res("cgp::64", CGP, ["64"]), _res("cst::20", CST, ["20"], dense=0.85)]

    promovidos = promover_referencias_exactas(
        resultados, "que dice el articulo 64 del codigo sustantivo del trabajo")

    # Ninguno de los dos es referencia exacta: el 64 es de otra norma y el 20 no
    # lo cita la consulta. Asi que el orden tiene que quedar intacto.
    assert [r.chunk_id for r in promovidos] == ["cgp::64", "cst::20"], (
        "promovio un articulo con el numero correcto pero de la norma equivocada")
