"""Tests del reranking (S08): el patron embudo con cross-encoder.

Corren sin GPU: se inyecta un `_scorer` fake (funcion pares -> puntajes) en vez
de descargar el cross-encoder. Lo que se prueba es la LOGICA del embudo -- que
reordena por el puntaje del reranker, que recorta a top_k, que conserva la
metadata citable y el dense_score para la valvula de escape -- no el modelo.
"""
from tools.rag import rerank
from tools.rag.embed_store import SearchResult


def make_result(chunk_id, dense_score, *, articulos=None):
    return SearchResult(
        chunk_id=chunk_id,
        text=f"texto de {chunk_id}",
        fuente="Ley 1480 de 2011",
        url_fuente=f"https://suin/{chunk_id}",
        score=dense_score,
        articulos_incluidos=articulos or [],
        dense_score=dense_score,
    )


def scorer_por_id(mapa):
    """Devuelve un _scorer que puntua cada par segun el chunk_id del texto."""
    def _scorer(pares):
        # cada par es (query, "texto de cX"); se extrae el id del final del texto
        return [mapa[texto.split()[-1]] for _, texto in pares]
    return _scorer


def test_el_reranker_reordena_por_su_propio_puntaje():
    """El punto del reranking: cambiar el orden que traia el recuperador barato.
    El candidato que el recuperador puso ultimo puede quedar primero si el
    cross-encoder lo juzga mas relevante."""
    candidatos = [make_result("c1", 0.85), make_result("c2", 0.82), make_result("c3", 0.80)]
    # El recuperador los trajo c1>c2>c3, pero el cross-encoder prefiere c3.
    scorer = scorer_por_id({"c1": 0.1, "c2": 0.2, "c3": 0.9})

    reordenado = rerank.rerank("consulta", candidatos, top_k=3, _scorer=scorer)

    assert [r.chunk_id for r in reordenado] == ["c3", "c2", "c1"]


def test_el_embudo_recorta_de_muchos_a_pocos():
    """Entra top-N, sale top_k: es lo que hace del reranking un embudo. Se le dan
    5 candidatos y se piden 2."""
    candidatos = [make_result(f"c{i}", 0.8) for i in range(5)]
    scorer = scorer_por_id({f"c{i}": float(i) for i in range(5)})

    reordenado = rerank.rerank("consulta", candidatos, top_k=2, _scorer=scorer)

    assert len(reordenado) == 2
    # Los de mayor puntaje del cross-encoder: c4 y c3.
    assert [r.chunk_id for r in reordenado] == ["c4", "c3"]


def test_el_score_devuelto_es_el_del_cross_encoder():
    """Tras reordenar, `score` debe ser el del cross-encoder (para que quien
    inspeccione vea por que quedo en ese puesto), no el coseno original."""
    candidatos = [make_result("c1", 0.85)]
    scorer = scorer_por_id({"c1": 7.3})

    [reordenado] = rerank.rerank("consulta", candidatos, top_k=1, _scorer=scorer)

    assert reordenado.score == 7.3


def test_el_reranker_conserva_el_dense_score_para_la_valvula_de_escape():
    """dense_score debe sobrevivir al reranking intacto: la valvula de escape
    lee el coseno de e5, no el puntaje del cross-encoder (otra escala, no
    calibrada como umbral)."""
    candidatos = [make_result("c1", 0.83)]
    scorer = scorer_por_id({"c1": 9.9})

    [reordenado] = rerank.rerank("consulta", candidatos, top_k=1, _scorer=scorer)

    assert reordenado.dense_score == 0.83
    assert reordenado.score == 9.9  # score si cambio; dense_score no


def test_el_reranker_conserva_la_metadata_citable():
    """Reordenar no puede perder la cita."""
    candidatos = [make_result("c1", 0.83, articulos=["64"])]
    scorer = scorer_por_id({"c1": 5.0})

    [reordenado] = rerank.rerank("consulta", candidatos, top_k=1, _scorer=scorer)

    assert reordenado.fuente == "Ley 1480 de 2011"
    assert reordenado.url_fuente == "https://suin/c1"
    assert reordenado.articulos_incluidos == ["64"]
    assert "Articulo 64" in reordenado.cita


def test_reranking_de_lista_vacia_devuelve_vacio():
    """Sin candidatos (la valvula de escape ya filtro todo, o el corpus no trajo
    nada) no hay nada que reordenar: [] y no un error."""
    assert rerank.rerank("consulta", [], top_k=5, _scorer=lambda p: []) == []
