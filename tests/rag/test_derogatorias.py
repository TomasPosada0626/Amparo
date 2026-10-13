"""H12: fragmentos que son solo una derogatoria (tools/rag/derogatorias.py)."""
from __future__ import annotations

import json

import pytest

from tools.rag import config, retrieve
from tools.rag.derogatorias import es_solo_derogatoria
from tools.rag.embed_store import SearchResult


# --- La regla, con los controles del dictamen de clase B' ----------------------

@pytest.mark.parametrize("texto", [
    "Articulo 226. Derogado por el articulo 39 de la Ley 1955 de 2019.",
    "ARTICULO 72. ENGANCHE PARA EL EXTERIOR. Articulo derogado por el paragrafo 3 "
    "del articulo 65 de la Ley 1429 de 2010.",
    "Articulo 1910. Derogado. Articulo 1911. Derogado Articulo 1912. Derogado.",
    "Articulo 616. Derogado\nTITULO III\nTRAMITES NOTARIALES",
])
def test_excluye_lo_que_solo_es_derogatoria(texto):
    assert es_solo_derogatoria(texto)


@pytest.mark.parametrize("texto", [
    # deroga OTRA norma: es contenido (art. 380 de la Constitucion)
    "Articulo 380. Queda derogada la Constitucion hasta ahora vigente con todas sus "
    "reformas. Esta Constitucion rige a partir del dia de su promulgacion.",
    # parcialmente derogado: el resto del texto sirve
    "Articulo 64. El inciso 2 fue derogado por la Ley 789 de 2002. En caso de terminacion "
    "unilateral sin justa causa el empleador pagara una indemnizacion.",
    # rotulo sin derogatoria: es otro defecto y no se toca aqui
    "ARTICULO 360. AFILIACION A VARIOS SINDICATOS.",
    "",
])
def test_conserva_lo_que_dice_algo_mas(texto):
    assert not es_solo_derogatoria(texto)


@pytest.mark.skipif(not config.FAISS_METADATA_PATH.exists(), reason="sin la metadata del indice")
def test_sobre_el_indice_evaluado():
    """El dictamen conto 107 con su implementacion; esta da 109. Las 2 de mas son
    stubs derogados seguidos de un encabezado de seccion, que tampoco responden.
    Lo que no puede cambiar: ningun excluido deja de decir "derogad"."""
    meta = [json.loads(l) for l in config.FAISS_METADATA_PATH.read_text(encoding="utf-8").splitlines()]
    excluidos = [m for m in meta if es_solo_derogatoria(m.get("text", ""))]
    assert len(excluidos) == 109
    assert all("derogad" in m["text"].lower() for m in excluidos)


# --- En retrieve: apagado por defecto, y el top-k sigue lleno -------------------

def _r(chunk_id, score, texto):
    return SearchResult(chunk_id=chunk_id, text=texto, fuente="CST", url_fuente="u", score=score,
                        articulos_incluidos=[], dense_score=score)


class _Store:
    def __init__(self, ranking):
        self.ranking, self.pedidos = ranking, []
        self.metadata = []

    def search(self, _emb, top_k):
        self.pedidos.append(top_k)
        return self.ranking[:top_k]


RANKING = ([_r(f"d{i}", 0.95 - i / 100, f"Articulo {i}. Derogado.") for i in range(4)]
           + [_r(f"v{i}", 0.90 - i / 100, f"Articulo {50 + i}. El empleador debe pagar.") for i in range(6)])


def test_apagado_por_defecto_no_cambia_el_buscador(monkeypatch):
    """Mientras se compara un candidato de M1 con v1, el buscador es el mismo."""
    assert config.FILTRAR_DEROGATORIAS is False
    monkeypatch.setattr(retrieve, "embed_query", lambda q: [0.0])
    out = retrieve.retrieve("q", _Store(RANKING), top_k=5, min_score=None, use_router=False)
    assert [r.chunk_id for r in out] == ["d0", "d1", "d2", "d3", "v0"]


def test_encendido_quita_las_derogatorias_y_llena_el_top_k(monkeypatch):
    monkeypatch.setattr(retrieve, "embed_query", lambda q: [0.0])
    store = _Store(RANKING)
    out = retrieve.retrieve("q", store, top_k=5, min_score=None, use_router=False,
                            filtrar_derogatorias=True)
    assert [r.chunk_id for r in out] == ["v0", "v1", "v2", "v3", "v4"]
    assert store.pedidos == [5 + retrieve.MARGEN_DEROGATORIAS]
