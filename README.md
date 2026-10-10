# Amparo

**Asistente jurídico de derecho colombiano basado en IA.** Amparo responde
consultas legales en lenguaje cotidiano y las fundamenta en fuentes normativas
verificadas, en lugar de generar afirmaciones legales sin respaldo. Está pensado
para público general —no abogados— que enfrenta problemas legales frecuentes:
salud y EPS, despidos, arriendo, reportes en centrales de riesgo, tránsito,
garantías de consumo, embargos.

Su principio rector es **no inventar normas**: cada respuesta es trazable a una
fuente verificada o admite explícitamente la incertidumbre.

> Proyecto académico de la asignatura **Tópicos Especiales y Aplicaciones en IA
> (SI4006)** de la Universidad EAFIT. Simula un entorno LegalTech de producción
> para ejercitar buenas prácticas de ingeniería: arquitectura modular, decisiones
> de diseño documentadas, pruebas automatizadas y evaluación rigurosa.

---

## Por qué existe

Un modelo de lenguaje responde de memoria, y en derecho eso es peligroso: cuando
no sabe, completa con lo más probable e **inventa la cita de un artículo**. Una
cita con forma correcta y contenido falso es el peor resultado posible para un
asistente jurídico, porque *parece* confiable.

Amparo ataca ese problema en dos frentes:

1. **Fine-tuning** para que el modelo aprenda el tono prudente del dominio y deje
   de citar de memoria.
2. **RAG (Retrieval-Augmented Generation)** para darle un corpus de normas reales
   de donde recuperar y citar de forma verificable, con una **válvula de escape**
   que lo obliga a admitir cuándo no tiene información en lugar de improvisarla.

---

## Estado del proyecto

El desarrollo avanza por milestones. Cada uno cierra con decisiones documentadas
y evidencia medida.

| Milestone | Tema | Estado | Artefactos |
|---|---|:--:|---|
| **M1** | Fine-tuning (LoRA sobre Qwen2.5-7B-Instruct) | ✅ | `data/dataset.jsonl`, `colab/m1_finetune.ipynb` |
| **M2** | Harness de evaluación (juez LLM, métricas, sesgos) | ✅ | `tools/evaluation/`, `results/m2_2026-10-09/` |
| **M3** | RAG: búsqueda A/B/C (S08) + de una pasada (S10) | ✅ | `tools/rag/`, `docs/m3_decisiones_rag.md`, `results/m3_s08_2026-10-09/`, `results/m3_s10_2026-10-09/` |

### Resultados de M2 (231 ejemplos de validación sin contexto)

| Métrica | Baseline | Fine-tuned |
|---|---|---|
| Juez compuesto (1-5) | 3.47 | **4.121** |
| Respuestas con error jurídico (juez) | 66.7% | **49.8%** |
| Cita de memoria (231 sin contexto) | 12.6% | **0.0%** |
| Entidades inventadas | 11.4% | **3.0%** |
| Longitud media (palabras) | 224.4 | 45.8 |

El fine-tuning eliminó la cita de memoria: cero en 231 ejemplos. Pero hay un
desacuerdo sin resolver entre jueces -- el compuesto favorece al afinado y el
cara a cara favorece al baseline (73 contra 106, con 42 pares inconsistentes
según el orden) -- así que **todavía no se puede afirmar que el afinado sea
globalmente superior**. Ver `results/README.md`.

El fallo abierto es la abstención: con contexto que no responde la pregunta, el
modelo cita igual en vez de reconocer el límite. Ver `docs/m1_b2_matriz.md`.

---

## Arquitectura

```
Consulta del usuario
        │
        ▼
┌───────────────────────────────────────────────┐
│  RETRIEVAL (tools/rag)                          │
│  denso (e5) + BM25 → fusión RRF → cross-encoder │
│  → válvula de escape (umbral sobre coseno e5)   │
└───────────────────────────────────────────────┘
        │  chunks con cita verificable
        ▼
┌───────────────────────────────────────────────┐
│  PROMPT AUMENTADO (4 partes)                    │
│  instrucción · contexto con fuente ·            │
│  válvula de escape · pregunta                   │
└───────────────────────────────────────────────┘
        │
        ▼
   Qwen2.5-7B-Instruct (+ LoRA opcional)
        │
        ▼
   Respuesta fundamentada y citada
```

El retrieval se expone además como **herramienta** (function calling): el modelo
decide si consultar el corpus, reformula la consulta al hacerlo y responde
directo cuando la pregunta no requiere una norma.

### Pipeline RAG en detalle

**Offline (indexación):** `ingest → chunk → embed → store`
**Online (consulta):** `retrieve → augment → generate`

| Componente | Decisión | Por qué |
|---|---|---|
| Embeddings | `intfloat/multilingual-e5-base` | Entrenado para retrieval asimétrico consulta coloquial → texto normativo |
| Vector store | FAISS (`IndexFlatIP`) | El cómputo corre en Colab, que no alcanza un Postgres local; un índice FAISS es un archivo movible |
| Chunking | Jerárquico por artículo | Cortar un artículo a la mitad parte la condición o la excepción de la norma |
| Hybrid search | BM25 + denso, fusión RRF | BM25 rescata los términos exactos ("artículo 64", "Ley 1480") que el denso difumina |
| Reranking | Cross-encoder `mmarco-mMiniLMv2` | Limpia el ruido del top-k con atención cruzada consulta-chunk |
| Generación | Qwen2.5-7B-Instruct, greedy | El mismo de M1/M2, para que las cifras sean comparables |

Las decisiones completas —con su justificación y evidencia— están en
[`docs/m3_decisiones_rag.md`](docs/m3_decisiones_rag.md).

---

## Estructura del repositorio

```
Amparo/
├── tools/
│   ├── rag/                    # Pipeline RAG (M3)
│   │   ├── ingest.py           #   fuentes crudas → texto + metadata
│   │   ├── chunk.py            #   división jerárquica por artículo
│   │   ├── embed_store.py      #   embeddings e5 + índice FAISS
│   │   ├── corpus.py           #   manifiesto de normas indexadas
│   │   ├── retrieve.py         #   recuperación configurable (denso/hybrid/rerank)
│   │   ├── hybrid.py           #   BM25 + fusión RRF
│   │   ├── rerank.py           #   reranking con cross-encoder
│   │   ├── prompt_template.py  #   prompt aumentado de 4 partes
│   │   ├── verificacion.py     #   verificacion de citas: no entregar articulos ni sentencias que no se recuperaron
│   │   ├── dspy_prompt.py      #   optimizacion del prompt con DSPy (extra S10)
│   │   └── pipeline.py         #   orquesta las 7 etapas
│   ├── evaluation/             # Harness de evaluación (M2)
│   │   ├── generation.py       #   carga y generación con Qwen2.5-7B
│   │   ├── judge.py            #   juez LLM local
│   │   ├── external_judge.py   #   juez externo independiente (Groq)
│   │   ├── metrics_classic.py  #   BLEU, ROUGE, F1, BERTScore
│   │   ├── domain_metric.py    #   cumplimiento de no-inventar-citas
│   │   ├── bias.py            #   sesgos (longitud, posición, autopreferencia)
│   │   ├── ragas_metrics.py    #   métricas RAGAS con juez Groq (M3 · S10)
│   │   ├── tracking.py         #   registro de corridas en W&B (M3 · S10)
│   │   └── scorecard.py        #   reporte consolidado
│   ├── model_comparator/       # Herramienta interna de comparación de modelos
│   ├── dataset_build.py        # Arma los ejemplos sin contexto desde data/dataset_src/
│   └── dataset_v2.py           # Arma los ejemplos con contexto desde data/dataset_src_v2/
├── data/
│   ├── dataset.jsonl           # El único dataset: 2709 (1536 sin contexto + 755 con + 418 contrastivas)
│   ├── dataset_src/            # Fuentes en Markdown de los ejemplos sin contexto
│   ├── dataset_src_v2/         # Fuentes de los ejemplos con contexto (B1/B2/B3)
│   ├── eval_set.json           # Eval set propio: gold + adversariales (M2)
│   └── corpus/normas/          # Corpus de normas colombianas (versionado)
├── colab/                      # Notebooks de ejecución (GPU)
│   ├── m1_finetune.ipynb          #   M1
│   ├── m2_evaluacion.ipynb        #   M2
│   ├── m3_s07_rag_ingenuo.ipynb   #   M3 · S07
│   ├── m3_s08_rag_avanzado.ipynb  #   M3 · S08
│   ├── m3_s10_rag_agentico.ipynb  #   M3 · S10
│   └── m3_s10_extra_dspy.ipynb    #   M3 · S10 · extra DSPy
├── docs/                       # Decisiones de diseño por milestone
├── results/                    # Scorecards
├── tests/                      # Pruebas (corren sin GPU)
├── PRODUCT.md                  # Definición de producto
└── requirements.txt
```

### El corpus normativo

37 normas colombianas indexadas en 11.975 fragmentos, que cubren las 27
categorías del dataset. El catálogo con su alcance y sus notas está en
`tools/rag/corpus.py`; la cobertura por categoría, con lo que falta, en
`docs/m3_cobertura_corpus.md`.

Pendiente conocido: el Código Sustantivo del Trabajo indexado no incorpora la
Ley 2466 de 2025, lo que bloquea las consultas laborales afectadas por esa
reforma.

Resultado: **3.425 chunks, todos con número de artículo**. Fuente: SUIN-Juriscol
(Ministerio de Justicia), vía un espejo comunitario. Es un espejo, no el Diario
Oficial: antes de citar en producción hay que verificar contra la fuente oficial.

---

## Cómo empezar

### Requisitos

- Python 3.11+
- Para indexar y generar (e5, cross-encoder, Qwen2.5-7B): GPU. Se hace en Colab
  (T4 o superior), donde vive el stack pesado.
- En local se corre todo lo que no necesita GPU: la lógica del pipeline y los
  tests.

### Instalación local

```bash
git clone https://github.com/TomasPosada0626/Amparo.git
cd Amparo
pip install -r requirements.txt
```

`requirements.txt` es deliberadamente liviano: no incluye `torch`,
`transformers` ni `sentence-transformers`. Ese stack pesado se instala dentro de
los notebooks de Colab, para no reemplazar el build de PyTorch con CUDA que Colab
ya trae.

### Verificar el corpus y correr los tests (sin GPU)

```bash
python -m tools.rag.corpus     # valida el manifiesto y lista las normas indexadas
pytest tests/rag -q            # pruebas del pipeline RAG
pytest -q                      # toda la suite
```

### Ejecutar el pipeline completo (Colab)

1. **Indexar** — `colab/m3_s07_rag_ingenuo.ipynb` construye el índice FAISS y lo guarda
   en Drive.
2. **Consultar** — `colab/m3_s08_rag_avanzado.ipynb` carga el índice y compara las
   tres configuraciones de retrieval (denso / hybrid / hybrid + rerank).
3. **Evaluación** — `colab/m3_s10_rag_agentico.ipynb` corre el RAG de una pasada
   sobre el eval set, lo evalúa con RAGAS (juez Groq), mide la guardia de rutas y
   lo registra en W&B. Necesita los secretos de Colab `GROQ_API_KEY` y
   `WANDB_API_KEY`. Las rutas agénticas (tool use y ReAct) se retiraron el
   2026-10-08: dos corridas mostraron que no se pagan
   (`docs/m3_decisiones_rag.md`, sección 28).
4. **Extra DSPy** — `colab/m3_s10_extra_dspy.ipynb` optimiza el prompt de generación
   (BootstrapFewShot y MIPROv2) y lo valida en el eval set con RAGAS.

### Consultar desde código

```python
from tools.rag import pipeline
from tools.rag.hybrid import BM25Index

store = pipeline.load_index()
bm25 = BM25Index(store.metadata)
model_bundle = pipeline.load_model()

resultado = pipeline.answer_query(
    "me despidieron sin pagarme la liquidación, ¿qué hago?",
    store,
    bm25=bm25,
    use_hybrid=True,
    use_rerank=True,
    model_bundle=model_bundle,
)
print(resultado["response"])
for chunk in resultado["retrieved_chunks"]:
    print(f"  [{chunk['score']}] {chunk['cita']}")
```

---

## Principios de diseño

- **No inventar normas.** Toda cita es trazable a una fuente del corpus o se
  admite la incertidumbre. La válvula de escape es una pieza central, no un
  adorno defensivo.
- **Decisión + justificación + evidencia.** Ninguna técnica entra por moda: cada
  una corrige un fallo concreto y su elección está documentada.
- **Separar lo liviano de lo pesado.** El código puro (orquestación, fusión de
  rankings, parsers) corre y se prueba sin GPU; los modelos se importan de forma
  perezosa y viven en Colab.
- **Cambios atribuibles.** Las configuraciones de retrieval se activan por
  bandera sobre un único camino de código, de modo que cualquier diferencia de
  resultados sea atribuible a la técnica y no a la implementación.

---

## Modelos y tecnologías

- **LLM:** Qwen2.5-7B-Instruct (fine-tuning con LoRA / PEFT / TRL)
- **Embeddings:** intfloat/multilingual-e5-base
- **Reranker:** cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
- **Vector store:** FAISS (migración a pgvector prevista con el backend
  FastAPI + Postgres)
- **Evaluación:** juez LLM local + juez externo (Groq), métricas clásicas
  (BLEU, ROUGE, F1, BERTScore) y métricas de dominio

---

## Documentación

- [`PRODUCT.md`](PRODUCT.md) — definición de producto, usuarios y principios.
- [`docs/m3_decisiones_rag.md`](docs/m3_decisiones_rag.md) — decisiones de diseño
  del sistema RAG (ingenuo, avanzado y agéntico).
- [Wiki del proyecto](https://github.com/TomasPosada0626/Amparo/wiki) — análisis
  completo de cada milestone.

---

## Aviso

Amparo es un proyecto académico y de portafolio. No está expuesto a usuarios
reales ni sustituye la asesoría de un abogado. El corpus proviene de un espejo
comunitario de SUIN-Juriscol y debe verificarse contra la fuente oficial antes de
cualquier uso real.
