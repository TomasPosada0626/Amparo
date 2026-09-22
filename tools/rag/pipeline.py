"""Pipeline: orquesta las 7 etapas del RAG ingenuo (S07).

Indexacion (offline):  ingest -> chunk -> embed -> store
Consulta (online):     retrieve -> augment -> generate

transformers/peft se importan solo dentro de generate() (import perezoso),
igual que en tools/evaluation/generation.py: el resto del pipeline es
importable y testeable sin GPU.

Dónde corre cada mitad (ver docs/m3_decisiones_rag.md): la indexacion y la
generacion corren en el notebook de Colab, porque ahi esta la GPU y ahi vive el
stack pesado; el indice FAISS resultante se guarda en Drive y se puede bajar a
local para inspeccionarlo.
"""
from __future__ import annotations

import time

from tools.rag import config, corpus
from tools.rag.chunk import chunk_corpus
from tools.rag.embed_store import embed_passages, get_store
from tools.rag.ingest import ingest_corpus, save_processed
from tools.rag.prompt_template import build_messages
from tools.rag.retrieve import retrieve

# Cada cuantos chunks se reporta progreso al construir el indice.
PROGRESO_CADA = 250


# --- Indexacion (offline) ---------------------------------------------------

def build_index(manifest: list[dict] | None = None, *, save: bool = True):
    """Corre ingest -> chunk -> embed -> store sobre el corpus completo.

    manifest: por defecto, el manifiesto declarado en corpus.py. Validarlo
    primero es a proposito: preferimos fallar antes de indexar que indexar un
    chunk cuya fuente no se puede comprobar.
    """
    if manifest is None:
        manifest = corpus.to_ingest_manifest()  # valida el manifiesto al construirlo

    print("[1/4] ingest...")
    docs = ingest_corpus(manifest)
    save_processed(docs)

    print("[2/4] chunk...")
    chunks = chunk_corpus(
        [
            {
                "doc_id": d.doc_id,
                "text": d.text,
                "fuente": d.fuente,
                "tipo": d.tipo,
                "url_fuente": d.url_fuente,
                "vigente": d.vigente,
            }
            for d in docs
        ]
    )
    print(f"      {len(docs)} documentos -> {len(chunks)} chunks")
    if not chunks:
        raise RuntimeError(
            "El chunker no produjo ningun chunk. Sintoma tipico: el texto "
            "extraido no conserva saltos de linea, asi que el patron de "
            "articulos no encuentra nada (ver chunk.ARTICLE_PATTERN)."
        )

    print(f"[3/4] embed ({config.EMBEDDING_MODEL_ID})...")
    # Se embebe por lotes grandes e imprimiendo progreso: son miles de chunks y
    # varios minutos: sin esto la celda de Colab no muestra nada y parece
    # trabada aunque este avanzando (mismo motivo por el que generate_batch de
    # tools/evaluation/generation.py imprime progreso).
    embeddings: list[list[float]] = []
    inicio = time.perf_counter()
    for i in range(0, len(chunks), PROGRESO_CADA):
        lote = [c.text for c in chunks[i : i + PROGRESO_CADA]]
        embeddings.extend(embed_passages(lote))
        hechos = len(embeddings)
        transcurrido = time.perf_counter() - inicio
        eta = (transcurrido / hechos) * (len(chunks) - hechos) / 60
        print(
            f"      {hechos}/{len(chunks)} ({100 * hechos / len(chunks):.0f}%) -- "
            f"ETA ~{eta:.1f} min"
        )

    print(f"[4/4] store ({config.VECTOR_STORE_BACKEND})...")
    store = get_store()
    store.add(chunks, embeddings)
    if save and hasattr(store, "save"):
        store.save()
        print(f"      indice -> {config.FAISS_INDEX_PATH}")

    print(f"Listo: {len(chunks)} chunks indexados.")
    return store


def load_index():
    """Carga el indice ya construido, para la mitad online del pipeline."""
    from tools.rag.embed_store import FaissStore

    return FaissStore.load()


# --- Consulta (online) ------------------------------------------------------

def answer_query(
    query: str,
    store,
    *,
    use_lora: bool = False,
    top_k: int = config.TOP_K,
    min_score: float | None = config.RETRIEVAL_MIN_SCORE,
    model_bundle=None,
) -> dict:
    """Corre retrieve -> augment -> generate para una consulta.

    use_lora: aplica el adaptador de M1 encima del modelo base. Comparar "RAG
    sobre base" vs. "RAG sobre fine-tuneado" es parte del checklist de M3: dice
    si el fine-tuning sigue aportando cuando el modelo ya tiene fuentes en el
    contexto, o si el RAG lo vuelve redundante.

    model_bundle: (model, tokenizer) ya cargado. Pasarlo siempre que se evalue
    un lote -- si no, cada llamada recarga 7B de pesos desde cero.

    Devuelve tambien la evidencia de retrieval (chunks, scores) para que el
    harness de tools/evaluation/ pueda auditar no solo el texto final sino que
    efectivamente hubo recuperacion antes de responder.
    """
    recuperados = retrieve(query, store, top_k=top_k, min_score=min_score)
    messages = build_messages(query, recuperados)
    respuesta = generate(messages, use_lora=use_lora, model_bundle=model_bundle)

    return {
        "query": query,
        "response": respuesta,
        # `contexts` va aparte y con el texto crudo porque es lo que consume un
        # evaluador de RAG (context precision/recall); `retrieved_chunks` es la
        # evidencia de auditoria: de donde salio cada contexto y con que score.
        "contexts": [r.text for r in recuperados],
        "retrieved_chunks": [
            {
                "chunk_id": r.chunk_id,
                "cita": r.cita,
                "url_fuente": r.url_fuente,
                "score": round(r.score, 4),
            }
            for r in recuperados
        ],
        "n_retrieved": len(recuperados),
        "used_lora": use_lora,
        "top_k": top_k,
        "min_score": min_score,
    }


def to_eval_record(resultado: dict, registro: dict) -> dict:
    """Convierte una respuesta del RAG al formato que espera un evaluador de RAG.

    Los nombres de campo (question / answer / contexts / ground_truth) son los
    que usa Ragas, para que la corrida de este RAG se pueda evaluar sin volver a
    transformarla. La evaluacion en si (Ragas, integracion con el harness de
    tools/evaluation/) NO es parte de este alcance: es el trabajo que continua
    despues de M3, y este formato es el contrato entre las dos mitades.

    registro: un registro de data/eval_set.json (id, category, tipo, criterio,
    messages[system, user, assistant]).
    """
    return {
        "id": registro["id"],
        "category": registro["category"],
        "tipo": registro["tipo"],
        "criterio": registro["criterio"],
        "question": resultado["query"],
        "answer": resultado["response"],
        "contexts": resultado["contexts"],
        "ground_truth": registro["messages"][2]["content"],
        "retrieved_chunks": resultado["retrieved_chunks"],
        "n_retrieved": resultado["n_retrieved"],
        "used_lora": resultado["used_lora"],
    }


def load_model(use_lora: bool = False):
    """Carga el modelo una sola vez, reutilizando tools/evaluation/generation.py.

    Reusa el cargador del harness de M2 (4-bit / QLoRA, mismo patron que M1) en
    vez de duplicar la logica: asi la generacion del RAG y la del scorecard de
    M2 comparten configuracion y las cifras siguen siendo comparables.
    """
    from tools.evaluation import generation

    model, tokenizer = generation.load_base_model(config.BASE_MODEL_ID)
    if use_lora:
        if not config.LORA_ADAPTER_PATH:
            raise ValueError(
                "use_lora=True pero LORA_ADAPTER_PATH no esta configurado en "
                "tools/rag/config.py"
            )
        model = generation.attach_adapter(model, config.LORA_ADAPTER_PATH)
    return model, tokenizer


def generate(messages: list[dict], *, use_lora: bool = False, model_bundle=None) -> str:
    """Genera la respuesta final con Qwen2.5-7B-Instruct.

    Greedy (do_sample=False), igual que M1/M2, para que las cifras sean
    comparables con el scorecard de M2. Import perezoso: requiere GPU.
    """
    from tools.evaluation import generation

    model, tokenizer = model_bundle if model_bundle else load_model(use_lora)
    system_prompt = next(m["content"] for m in messages if m["role"] == "system")
    user_content = next(m["content"] for m in messages if m["role"] == "user")
    return generation.run_chat_generation(
        model,
        tokenizer,
        system_prompt,
        user_content,
        config.MAX_NEW_TOKENS_GENERATION,
    )


if __name__ == "__main__":
    faltantes = corpus.pendientes()
    if faltantes:
        print(
            f"El corpus todavia no esta listo: {len(faltantes)} de "
            f"{len(corpus.NORMAS_OBJETIVO)} normas sin url_fuente verificada.\n"
            "Corre `python -m tools.rag.corpus` para ver cuales, descarga los "
            "HTML a data/rag_corpus_raw/ y completa la URL en corpus.py."
        )
    else:
        build_index()
