"""Tests del enrutador por categoria (tools/rag/enrutador.py). Sin GPU ni red."""
from tools.rag import enrutador as en
from tools.rag import retrieve as rt
from tools.rag.embed_store import SearchResult


def _r(chunk_id, doc_id, score=0.9):
    return SearchResult(chunk_id=chunk_id, text=chunk_id, fuente=doc_id, url_fuente="u", score=score,
                        articulos_incluidos=["1"], dense_score=score, doc_id=doc_id)


def test_priorizar_sube_las_normas_permitidas_sin_borrar_las_demas():
    rs = [_r("a", "cst"), _r("b", "ley820"), _r("c", "cpaca"), _r("d", "ley820")]
    out = en.priorizar(rs, {"ley820"})
    assert [r.chunk_id for r in out] == ["b", "d", "a", "c"]


def test_priorizar_sin_filtro_no_cambia_nada():
    rs = [_r("a", "cst"), _r("b", "ley820")]
    assert en.priorizar(rs, None) == rs


def test_el_enrutador_real_reconoce_categorias_obvias():
    e = en.enrutador_por_defecto()
    assert e.categorias("mi arrendador me quiere subir el canon de arrendamiento")[0] == "Arriendo"
    assert "Salud / EPS" in e.categorias("la EPS no me autoriza la cirugia que me ordeno el medico")
    normas = e.normas("me subieron el arriendo el doble")
    assert "arrendamiento_vivienda_urbana_ley_820_2003" in normas
    assert "constitucion_politica_1991" in normas          # transversal, siempre


def test_toda_categoria_del_corpus_tiene_normas_en_el_enrutador():
    from tools.rag import corpus

    e = en.enrutador_por_defecto()
    for categoria in corpus.CATEGORIAS_OBJETIVO:
        assert e.normas_de.get(categoria), categoria


class _StoreFijo:
    """Devuelve siempre la misma lista; registra cuantos candidatos pidieron."""

    def __init__(self, resultados):
        self.resultados = resultados
        self.pedidos = []
        self.metadata = []

    def search(self, embedding, top_k):
        self.pedidos.append(top_k)
        return self.resultados[:top_k]


class _EnrutadorFijo:
    def __init__(self, permitidas):
        self.permitidas = permitidas

    def normas(self, consulta):
        return self.permitidas


def test_retrieve_con_enrutador_pide_mas_candidatos_y_prioriza(monkeypatch):
    monkeypatch.setattr(rt, "embed_query", lambda q: [0.0])
    store = _StoreFijo([_r("a", "cst"), _r("b", "cpaca"), _r("c", "ley820")])
    out = rt.retrieve("q", store, top_k=2, min_score=None, use_router=True,
                      enrutador=_EnrutadorFijo({"ley820"}))
    assert [r.chunk_id for r in out] == ["c", "a"]
    assert store.pedidos[0] >= rt.config.ENRUTADOR_POOL


def test_retrieve_sin_enrutador_es_el_de_siempre(monkeypatch):
    monkeypatch.setattr(rt, "embed_query", lambda q: [0.0])
    store = _StoreFijo([_r("a", "cst"), _r("b", "cpaca"), _r("c", "ley820")])
    out = rt.retrieve("q", store, top_k=2, min_score=None, use_router=False)
    assert [r.chunk_id for r in out] == ["a", "b"] and store.pedidos == [2]
