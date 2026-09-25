"""Tests de la parte de pipeline.py que no necesita GPU.

build_index() y generate() no se testean aca: cargan e5 y Qwen2.5-7B, y solo
corren dentro de Colab. Lo que si se testea es el contrato de salida, que es lo
que consume quien continue con el RAG avanzado y la evaluacion.
"""
from tools.evaluation import eval_set
from tools.rag import pipeline


def resultado_de_ejemplo(**overrides) -> dict:
    base = {
        "query": "¿Cuanto tiempo tiene la EPS para responder?",
        "response": "Segun la Ley 1437 de 2011, Articulo 14, quince dias.",
        "contexts": ["Articulo 14. Terminos para resolver..."],
        "retrieved_chunks": [
            {
                "chunk_id": "cpaca_ley_1437_2011::chunk14",
                "cita": "Ley 1437 de 2011 (CPACA), Articulo 14",
                "url_fuente": "https://www.suin-juriscol.gov.co/viewDocument.asp?id=1680117",
                "score": 0.87,
            }
        ],
        "n_retrieved": 1,
        "used_lora": False,
        "top_k": 5,
        "min_score": 0.8,
    }
    base.update(overrides)
    return base


def registro_de_ejemplo(**overrides) -> dict:
    base = {
        "id": 9001,
        "category": "Salud / EPS",
        "tipo": "gold",
        "criterio": "Debe mencionar el derecho de peticion y no inventar plazos.",
        "messages": [
            {"role": "system", "content": "Eres un asistente juridico..."},
            {"role": "user", "content": "¿Cuanto tiempo tiene la EPS para responder?"},
            {"role": "assistant", "content": "La entidad debe responder en quince dias habiles."},
        ],
    }
    base.update(overrides)
    return base


def test_el_registro_de_evaluacion_trae_los_campos_que_espera_ragas():
    """question / answer / contexts / ground_truth son los nombres de Ragas: la
    corrida de este RAG tiene que poder evaluarse sin volver a transformarla."""
    record = pipeline.to_eval_record(resultado_de_ejemplo(), registro_de_ejemplo())

    for campo in ("question", "answer", "contexts", "ground_truth"):
        assert campo in record, campo
    assert record["ground_truth"] == "La entidad debe responder en quince dias habiles."
    assert record["contexts"] == ["Articulo 14. Terminos para resolver..."]


def test_el_registro_conserva_la_trazabilidad_del_eval_set():
    """id / tipo / criterio vienen del eval set de M2: sin ellos no se puede
    separar el desempeno en gold vs. adversarial, que es la comparacion que
    mostro el problema que este RAG viene a resolver."""
    record = pipeline.to_eval_record(
        resultado_de_ejemplo(), registro_de_ejemplo(id=9101, tipo="adversarial")
    )

    assert record["id"] == 9101
    assert record["tipo"] == "adversarial"
    assert record["criterio"].strip()


def test_el_registro_conserva_la_evidencia_de_retrieval():
    """Permite auditar no solo el texto final sino de donde salio: que chunk, de
    que norma y con que score."""
    record = pipeline.to_eval_record(resultado_de_ejemplo(), registro_de_ejemplo())

    assert record["n_retrieved"] == 1
    assert record["retrieved_chunks"][0]["cita"].startswith("Ley 1437 de 2011")
    assert record["retrieved_chunks"][0]["url_fuente"].startswith("https://")


def test_una_respuesta_sin_contexto_queda_registrada_como_tal():
    """El caso de la valvula de escape: contexts vacio no es un error, es el
    resultado esperado cuando la pregunta esta fuera del corpus."""
    record = pipeline.to_eval_record(
        resultado_de_ejemplo(contexts=[], retrieved_chunks=[], n_retrieved=0),
        registro_de_ejemplo(tipo="adversarial"),
    )

    assert record["contexts"] == []
    assert record["n_retrieved"] == 0


def test_funciona_sobre_los_registros_reales_del_eval_set():
    """Contra data/eval_set.json real, no contra un dict inventado: si el
    esquema del eval set cambia, esto falla aca y no en medio de Colab."""
    registros = eval_set.load_eval_set()

    for registro in registros:
        record = pipeline.to_eval_record(resultado_de_ejemplo(), registro)
        assert record["ground_truth"].strip()
        assert record["tipo"] in eval_set.VALID_TIPOS


def test_el_eval_set_ampliado_sigue_teniendo_gold_y_adversariales():
    """El PR del corpus amplio el eval set de 13 a 56 registros; el RAG se corre
    sobre ese mismo set, asi que conviene verificar que la mezcla se mantiene."""
    registros = eval_set.load_eval_set()

    assert len(eval_set.gold_examples(registros)) >= 10
    assert len(eval_set.adversarial_examples(registros)) >= 3


def test_el_record_conserva_el_sistema_abc_que_lo_produjo():
    """used_hybrid/used_rerank etiquetan el registro con el sistema (A/B/C) que
    lo genero. Sin ellos, dos corridas del mismo eval set con numeros distintos
    serian indistinguibles y el delta de S08 no seria atribuible a la tecnica."""
    record = pipeline.to_eval_record(
        resultado_de_ejemplo(used_hybrid=True, used_rerank=True), registro_de_ejemplo()
    )

    assert record["used_hybrid"] is True
    assert record["used_rerank"] is True


def test_el_record_asume_sistema_A_si_no_se_declara_el_sistema():
    """Compatibilidad con el contrato S07: un resultado sin los flags (caller
    viejo) se registra como sistema A (denso puro), no revienta."""
    resultado = resultado_de_ejemplo()
    resultado.pop("used_hybrid", None)
    resultado.pop("used_rerank", None)

    record = pipeline.to_eval_record(resultado, registro_de_ejemplo())

    assert record["used_hybrid"] is False
    assert record["used_rerank"] is False
