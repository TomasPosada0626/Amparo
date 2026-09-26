"""Tests de las constantes del RAG avanzado (S08) en tools/rag/config.py.

No prueban comportamiento -- prueban que el contrato de configuracion existe y
es coherente, para que un error de dedo (INPUT_N menor que OUTPUT_K, RRF_K = 0)
se vea aca y no en medio de una corrida de Colab. Mismo espiritu que el resto de
tests del RAG: correr sin GPU, sin faiss, sin el stack pesado.
"""
from tools.rag import config


def test_las_banderas_maestras_arrancan_en_falso():
    """El default es el comportamiento S07 (sistema A): con las dos banderas en
    False el retrieval es denso puro, y por eso los 125 tests de S07 no cambian.
    El delta A/B/C solo es atribuible si el punto de partida es el ingenuo."""
    assert config.USE_HYBRID is False
    assert config.USE_RERANK is False


def test_hybrid_top_n_supera_el_top_k_final():
    """La fusion RRF necesita ver mas abajo de TOP_K en cada ranking para premiar
    el consenso: si solo mirara el top-5, un buen candidato que un recuperador
    pone 6o se perderia antes de fusionar."""
    assert config.HYBRID_TOP_N > config.TOP_K


def test_rrf_k_es_el_valor_del_paper():
    """60 es el default de Cormack et al. (2009). No se calibra en M3: el aporte
    de RRF es la robustez a escalas incomparables, no un k fino."""
    assert config.RRF_K == 60


def test_el_embudo_del_reranker_reordena_de_muchos_a_pocos():
    """INPUT_N > OUTPUT_K es lo que hace que el embudo sea un embudo: se recupera
    mucho barato y se reordena poco caro. Si fueran iguales, el cross-encoder no
    tendria nada que descartar."""
    assert config.RERANK_INPUT_N > config.RERANK_OUTPUT_K


def test_el_prompt_sigue_recibiendo_top_k_chunks():
    """El reranking cambia QUE chunks llegan al prompt, no CUANTOS: el augment de
    S07 espera TOP_K, y mantenerlo asi deja el delta atribuible al reordenamiento
    y no a un cambio en el tamaño del contexto."""
    assert config.RERANK_OUTPUT_K == config.TOP_K


def test_el_reranker_es_un_cross_encoder_multilingue():
    """Mismo criterio que e5: el caso de Amparo es consulta coloquial en español
    -> texto normativo, asi que el reranker tiene que entender español."""
    assert "mmarco" in config.RERANK_MODEL_ID.lower()


def test_importar_config_no_arrastra_el_stack_pesado():
    """config.py debe seguir siendo importable sin torch/faiss/sentence-
    transformers: es lo que permite que estos tests corran en local. Si alguien
    agrega un import pesado a nivel de modulo, esto lo delata."""
    import sys

    assert "torch" not in sys.modules
    assert "sentence_transformers" not in sys.modules
