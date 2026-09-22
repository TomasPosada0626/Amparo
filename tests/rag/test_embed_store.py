"""Tests de la logica de embed_store que no llama al modelo ni necesita faiss.

Las funciones de embedding (embed_query/embed_passages) no se testean aca: solo
corren con torch/transformers, que viven en el notebook de Colab. Lo que si se
puede (y se debe) testear es todo lo demas: la normalizacion, la metadata que
viaja junto al vector, y el filtrado de resultados -- que es donde un error
produce una cita que apunta al chunk equivocado.
"""
import math

import numpy as np
import pytest

from tools.rag import config, embed_store
from tools.rag.chunk import Chunk


def chunk_de_prueba(**overrides) -> Chunk:
    base = dict(
        chunk_id="ley_1755_2015::chunk1",
        doc_id="ley_1755_2015",
        text="ARTÍCULO 14. Toda peticion debera resolverse en quince (15) dias.",
        fuente="Ley 1755 de 2015 (Derecho de peticion)",
        tipo="ley",
        url_fuente="https://www.funcionpublica.gov.co/eva/gestornormativo/ejemplo",
        articulos_incluidos=["14"],
        capitulo="CAPITULO I",
        vigente=True,
    )
    base.update(overrides)
    return Chunk(**base)


class FakeIndex:
    """Doble de un IndexFlatIP: devuelve los vecinos que se le indiquen.

    Permite testear el filtrado y el recorte de FaissStore.search sin instalar
    faiss ni construir un indice real.
    """

    def __init__(self, scores_por_indice: list[tuple[int, float]], d: int = 768):
        self._vecinos = scores_por_indice
        self.d = d
        self.ntotal = len(scores_por_indice)
        self.vectores_agregados = 0

    def add(self, vectores) -> None:
        self.vectores_agregados += len(vectores)
        self.ntotal += len(vectores)

    def search(self, _vector, k: int):
        recorte = self._vecinos[:k]
        scores = np.array([[s for _, s in recorte]], dtype="float32")
        indices = np.array([[i for i, _ in recorte]], dtype="int64")
        return scores, indices


# --- normalize ---------------------------------------------------------------

def test_normalize_deja_vectores_de_norma_uno():
    normalizados = embed_store.normalize([[3.0, 4.0], [1.0, 0.0]])

    assert math.isclose(float(np.linalg.norm(normalizados[0])), 1.0, rel_tol=1e-6)
    assert math.isclose(float(np.linalg.norm(normalizados[1])), 1.0, rel_tol=1e-6)


def test_normalize_acepta_un_vector_suelto_y_devuelve_matriz():
    """FaissStore.search recibe el embedding de la consulta como lista plana;
    faiss exige una matriz 2D."""
    normalizado = embed_store.normalize([3.0, 4.0])

    assert normalizado.shape == (1, 2)


def test_normalize_no_produce_nan_con_el_vector_cero():
    """Un solo NaN en el indice envenena todas las busquedas posteriores, asi
    que el vector cero se deja en cero en vez de dividir por su norma."""
    normalizado = embed_store.normalize([[0.0, 0.0, 0.0]])

    assert not np.isnan(normalizado).any()
    assert float(normalizado.sum()) == 0.0


def test_normalize_convierte_a_float32_como_espera_faiss():
    assert embed_store.normalize([[1.0, 2.0]]).dtype == np.dtype("float32")


# --- metadata ---------------------------------------------------------------

def test_la_metadata_guardada_conserva_todo_lo_necesario_para_citar():
    meta = embed_store.chunk_to_metadata(chunk_de_prueba())

    assert set(meta) == set(embed_store.METADATA_FIELDS)
    assert meta["fuente"] == "Ley 1755 de 2015 (Derecho de peticion)"
    assert meta["articulos_incluidos"] == ["14"]
    assert meta["url_fuente"].startswith("https://")


def test_metadata_y_search_result_hacen_ida_y_vuelta():
    meta = embed_store.chunk_to_metadata(chunk_de_prueba())
    resultado = embed_store.metadata_to_result(meta, score=0.91)

    assert resultado.chunk_id == meta["chunk_id"]
    assert resultado.cita == "Ley 1755 de 2015 (Derecho de peticion), Articulo 14"
    assert resultado.score == 0.91
    assert resultado.capitulo == "CAPITULO I"


def test_search_result_sin_articulos_no_falla_con_lista_none():
    resultado = embed_store.metadata_to_result(
        {"chunk_id": "x", "text": "t", "fuente": "f"}, score=0.5
    )

    assert resultado.articulos_incluidos == []
    assert resultado.cita == "f"


# --- FaissStore (con indice falso) ------------------------------------------

def test_add_rechaza_chunks_y_embeddings_desalineados():
    """Si el numero de vectores y de registros de metadata no coincide, cada
    busqueda devuelve la cita de otro chunk: un fallo silencioso y del tipo
    exacto que este proyecto no puede permitirse."""
    store = embed_store.FaissStore(dim=2, index=FakeIndex([], d=2))

    with pytest.raises(ValueError, match="no coinciden"):
        store.add([chunk_de_prueba()], [[0.1, 0.2], [0.3, 0.4]])


def test_add_vacio_no_toca_el_indice():
    indice = FakeIndex([], d=2)
    store = embed_store.FaissStore(dim=2, index=indice)

    store.add([], [])

    assert len(store) == 0
    assert indice.vectores_agregados == 0


def test_add_guarda_un_registro_de_metadata_por_vector():
    indice = FakeIndex([], d=2)
    store = embed_store.FaissStore(dim=2, index=indice)

    store.add([chunk_de_prueba(), chunk_de_prueba(chunk_id="c2")], [[1.0, 0.0], [0.0, 1.0]])

    assert len(store) == 2
    assert indice.vectores_agregados == 2


def test_search_sobre_indice_vacio_devuelve_lista_vacia():
    """Es el caso de "todavia no hay corpus": debe devolver vacio para que la
    valvula de escape se active, no reventar."""
    store = embed_store.FaissStore(dim=2, index=FakeIndex([], d=2))

    assert store.search([0.1, 0.2], top_k=5) == []


def test_search_descarta_los_chunks_no_vigentes():
    """FAISS no filtra antes de buscar (es el costo concreto de no usar
    pgvector), asi que el filtro de vigencia se aplica en Python. Si no
    funcionara, el sistema citaria una norma derogada como si estuviera viva."""
    chunks = [
        chunk_de_prueba(chunk_id="vigente", vigente=True),
        chunk_de_prueba(chunk_id="derogado", vigente=False),
    ]
    indice = FakeIndex([(1, 0.95), (0, 0.90)], d=2)
    store = embed_store.FaissStore(dim=2, index=indice)
    store._metadata = [embed_store.chunk_to_metadata(c) for c in chunks]

    resultados = store.search([0.1, 0.2], top_k=5)

    assert [r.chunk_id for r in resultados] == ["vigente"]


def test_search_recorta_a_top_k_despues_de_filtrar():
    indice = FakeIndex([(0, 0.99), (1, 0.95), (2, 0.91)], d=2)
    store = embed_store.FaissStore(dim=2, index=indice)
    store._metadata = [
        embed_store.chunk_to_metadata(chunk_de_prueba(chunk_id=f"c{i}")) for i in range(3)
    ]

    resultados = store.search([0.1, 0.2], top_k=2)

    assert [r.chunk_id for r in resultados] == ["c0", "c1"]
    assert resultados[0].score > resultados[1].score


def test_search_ignora_el_indice_menos_uno_de_faiss():
    """faiss rellena con -1 cuando pide mas vecinos que vectores existentes."""
    indice = FakeIndex([(0, 0.99), (-1, 0.0)], d=2)
    store = embed_store.FaissStore(dim=2, index=indice)
    store._metadata = [embed_store.chunk_to_metadata(chunk_de_prueba())]

    resultados = store.search([0.1, 0.2], top_k=5)

    assert len(resultados) == 1


# --- factory ----------------------------------------------------------------

def test_get_store_pgvector_falla_con_el_motivo_de_la_decision():
    """pgvector no esta implementado a proposito (decision 2 de M3): mejor un
    error que apunta a la decision documentada que una implementacion sin uso
    ni pruebas."""
    with pytest.raises(NotImplementedError, match="m3_decisiones_rag"):
        embed_store.get_store("pgvector")


def test_get_store_rechaza_un_backend_desconocido():
    with pytest.raises(ValueError, match="Backend desconocido"):
        embed_store.get_store("chroma")


def test_el_backend_configurado_es_faiss():
    assert config.VECTOR_STORE_BACKEND == "faiss"


def test_load_sin_indice_construido_explica_que_hacer():
    with pytest.raises(FileNotFoundError, match="build_index"):
        embed_store.FaissStore.load(
            index_path=config.ARTIFACTS_DIR / "no_existe.faiss",
            metadata_path=config.ARTIFACTS_DIR / "no_existe.jsonl",
        )
