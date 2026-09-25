# M3 · Sistema RAG — decisiones

Documento de decisiones del RAG ingenuo de Amparo (alcance S07: `ingest →
chunk → embed → store` offline, `retrieve → augment → generate` online).
Mismo estándar de documentación que M1/M2: **decisión + justificación +
evidencia**, no solo qué se eligió.

Fecha: 2026-09-21 · código: [`tools/rag/`](../tools/rag/) · ejecución:
[`colab/rag_ingenuo.ipynb`](../colab/rag_ingenuo.ipynb)

> **Por qué este RAG existe.** El M2 midió que el modelo fine-tuneado llega a
> **100% de cumplimiento de "no inventa citas"** en los 201 ejemplos de
> validación ([scorecard](../results/m2_scorecard_2026-09-19.md)), frente a
> 73.6% del baseline. Pero ese 100% es "aprendió a no citar", no "aprende a
> citar bien": en el eval set adversarial el modelo cede y cita cuando se le
> presiona por un número de artículo, sin tener de dónde verificarlo. Este RAG
> es la pieza que convierte eso en "cita correctamente porque tiene de dónde
> verificarlo", que es el principio duro #1 de [`PRODUCT.md`](../PRODUCT.md).

## 1. Corpus

- **Alcance: las 9 categorías cotidianas de mayor frecuencia** del dataset de
  M1, no el dominio completo. Son exactamente las 9 categorías con 61-63
  ejemplos cada una en `data/dataset_legal.jsonl` (las otras 15 tienen 51), así
  que es el mismo criterio de priorización con el que se construyó el dataset de
  fine-tuning: Salud/EPS, Garantías de consumo, Despido, Relaciones laborales,
  Arriendo, Reporte en centrales de riesgo, Accidentes de tránsito, Embargos y
  Comparendos de tránsito.
- **Justificación del alcance acotado:** un corpus acotado permite validar el
  pipeline completo —incluida la válvula de escape, que necesita preguntas
  *fuera* del corpus para poder probarse— antes de escalar. Cubrir "todo el
  derecho colombiano" de entrada convierte la curaduría de vigencia en un
  proyecto en sí mismo.
- **Volumen:** 17 normas descargadas en `data/corpus/normas/`, **10 indexadas**,
  7 declaradas fuera de alcance. Resultado: **3.425 chunks, todos con número de
  artículo**.

### Normas indexadas

| Norma | Categorías que cubre |
|---|---|
| Constitución Política de 1991 | transversal (arts. 15, 23, 49, 86) |
| Ley 1437 de 2011 (CPACA) | transversal — trae el derecho de petición vigente |
| Decreto 2591 de 1991 | transversal — procedimiento de la acción de tutela |
| Ley 100 de 1993 | Salud / EPS |
| Decreto 2663 de 1950 (Código Sustantivo del Trabajo) | Despido, Relaciones laborales |
| Ley 820 de 2003 | Arriendo |
| Ley 1266 de 2008 (hábeas data financiero) | Reporte en centrales de riesgo |
| Ley 1480 de 2011 (Estatuto del Consumidor) | Garantías de consumo |
| Ley 769 de 2002 (Código Nacional de Tránsito) | Accidentes y comparendos de tránsito |
| Ley 1564 de 2012 (Código General del Proceso) | Embargos |

La **Ley 1755 de 2015** no aparece como norma independiente porque no existe
como archivo separado: su texto sustituyó el Título II del CPACA y así quedó
consolidado en `cpaca_ley_1437_2011.md`. El mapeo norma → categorías vive en
código, en [`tools/rag/corpus.py`](../tools/rag/corpus.py), no solo en esta
tabla, y hay un test que verifica contra el dataset real que las 9 categorías
queden cubiertas.

### Normas descargadas que NO se indexan

Seis quedan fuera **por alcance** (Código Civil, Código de Comercio, Código
Penal, Código de Procedimiento Penal, Código de la Infancia y la Adolescencia,
Ley 1712 de transparencia): son normas válidas, pero cubren categorías que no
están entre las 9 priorizadas.

La séptima, la **Ley 1581 de 2012**, queda fuera **por calidad, no por
alcance**, y esto sí es una decisión con consecuencias: el archivo del espejo
intercala texto transcrito de otros instrumentos (aparece, por ejemplo, el
artículo 27 de la Convención sobre los Derechos del Niño), que el chunker
atribuiría a la Ley 1581 — una cita correcta en forma y falsa en contenido, que
es exactamente lo que el producto no puede hacer. La categoría "Reporte en
centrales de riesgo" queda cubierta por la Ley 1266 de 2008, cuyo archivo sí
está limpio (24 encabezados detectados para sus 22 artículos). Las exclusiones
están declaradas con su razón en `corpus.FUERA_DE_ALCANCE`, y un test verifica
que ninguna norma descargada quede sin clasificar: excluir en silencio es
indistinguible de un olvido.

### Procedencia y su límite

- **Fuente primaria:** SUIN-Juriscol (Ministerio de Justicia), el sistema
  normativo oficial del Estado colombiano. El campo `source` del frontmatter de
  cada archivo apunta al documento SUIN correspondiente, y el `ingest` lo lee de
  ahí en vez de que nadie lo escriba a mano.
- **Vía de descarga:** un espejo comunitario en GitHub que republica sin
  modificar el texto consolidado de SUIN, porque los dominios `.gov.co` están
  bloqueados por la política de red de la organización. **Decisión tomada y
  aceptada:** si el acceso directo al Estado colombiano no está disponible, esta
  procedencia es la correcta para el trabajo. Queda documentada, no asumida.
- **Excepción, la Constitución:** no estaba en el espejo. Se extrajo de un PDF
  de la edición de Political Database of the Americas (Georgetown University).
  Su campo de procedencia es una descripción, no una URL — es honesto respecto
  de lo que es, pero conviene saberlo.
- **Límite que hay que respetar:** es un espejo, no el Diario Oficial. Antes de
  citar un artículo en producción hay que verificarlo contra la fuente oficial.
  Esto no es teórico para un asistente jurídico: es la diferencia entre "cita
  verificada" y "cita verificable". Está anotado también en
  `data/corpus/normas/README.md`.
- **Fecha de corte:** 2026-09-21. Se registra por documento en `fecha_consulta`.
  Una derogatoria posterior no se refleja en el índice; por eso `vigente` es un
  campo explícito de cada chunk (leído de `status` del frontmatter) y no un
  supuesto.
- **Formato:** Markdown con frontmatter YAML. El corpus **sí se versiona** en el
  repo (son textos de dominio público); lo que no se versiona es la salida
  generada del ingest, que se reconstruye con `pipeline.build_index()`.

## 2. Backend de vector store

- **Elegido: FAISS** (`faiss-cpu`), con migración a pgvector prevista para
  cuando exista el backend FastAPI.
- **Razón (desviación documentada de la recomendación de la skill):** la skill
  recomienda pgvector con el argumento de "no agregar infraestructura nueva,
  porque Postgres ya está en el stack". Esa premisa **no se cumple**: el repo no
  contiene ni FastAPI, ni Postgres, ni Docker — PostgreSQL es una intención
  declarada en la wiki, no infraestructura existente. Con eso a la vista:
  1. **Dónde corre el cómputo.** Los embeddings y la generación corren en Colab,
     porque ahí está la GPU (mismo patrón que M1 y M2). Colab **no puede
     alcanzar un Postgres en localhost**; usar pgvector obligaría a montar un
     túnel o a contratar un Postgres gestionado, solo para M3. Un índice FAISS
     es un archivo que se mueve por Drive, igual que el adaptador LoRA de M1.
  2. **Escala.** A 3.425 chunks los dos backends sobran; no hay ninguna ventaja
     de rendimiento que justifique el costo de infraestructura.
- **Qué se pierde y cuándo se revisa:** se pierden los filtros híbridos nativos
  en SQL (`WHERE categoria = ... AND vigente = true ORDER BY embedding <=> q`).
  En esta fase el filtro de vigencia se aplica en Python, sobre-muestreando el
  top-k. La decisión se revisa cuando el backend FastAPI + Postgres exista.
  `embed_store.get_store("pgvector")` lanza un error explícito que apunta a esta
  sección — no se dejó una implementación de pgvector sin uso ni pruebas.

## 3. Modelo de embeddings

- **Elegido:** `intfloat/multilingual-e5-base`, 768 dimensiones.
- **Razón:** el retrieval de Amparo es **asimétrico**: la consulta es lenguaje
  coloquial de alguien en urgencia ("me despidieron sin pagarme la
  liquidación") y el documento objetivo es lenguaje normativo ("Artículo 64.
  Son justas causas para dar por terminado..."). e5 fue entrenado con objetivo
  de retrieval pregunta→pasaje, que es justo esa asimetría.
  - Se descartó **BETO** (el backbone de BERTScore en M2) pese a que reutilizarlo
    no habría agregado dependencias: es un modelo de lenguaje, no fue entrenado
    con objetivo de similitud. En este dominio recuperar el artículo equivocado
    es peor que no recuperar nada: produce una cita verificable al servicio de
    una respuesta errónea.
  - Se descartó **paraphrase-multilingual-mpnet-base-v2** (entrenado para
    similitud de paráfrasis, más débil en la asimetría de registro) y
    **text-embedding-3-small de OpenAI** (mete una dependencia de API pagada y
    de red en la indexación).
- **Detalle de implementación que no es opcional:** e5 requiere los prefijos
  `"query: "` y `"passage: "`. Omitirlos degrada el retrieval **en silencio** —
  no falla, solo recupera peor. Por eso `embed_store.py` expone
  `embed_passages()` y `embed_query()` por separado, para que el prefijo no
  dependa de que quien llame se acuerde.
- **Dónde corre:** en el notebook de Colab, como todo el stack pesado
  (`torch`/`transformers` no entran a `requirements.txt` — misma razón que en
  M1/M2). El índice FAISS resultante se guarda en Drive.

## 4. Chunking

- **`MAX_TOKENS_PER_CHUNK`: 350** · **`MIN_TOKENS_PER_CHUNK`: 40**
- **Estrategia:** jerárquica por unidad normativa (artículo), nunca de tamaño
  fijo ciego. Un chunk de tamaño fijo puede cortar la condición o la excepción de
  una norma a la mitad, lo que en dominio legal no degrada la respuesta: la
  invierte.
- **Resultado medido sobre el corpus real:** 3.425 chunks, **100% con número de
  artículo**, ninguno por encima del presupuesto de 350 tokens (mediana 174,
  p90 332).

### Ajustes que el corpus real obligó a hacer

1. **La limpieza del Markdown va en `ingest`, no en el chunker.** El corpus trae
   el articulado envuelto en sintaxis Markdown (`##### **Artículo 1º.**
   *Objeto*.`). Con el patrón anclado a inicio de línea, eso significaba **0
   artículos detectados en 9 de las 10 normas** — y no fallaba: producía chunks
   sin número de artículo, o sea un sistema capaz de citar la ley pero nunca el
   artículo. Se resolvió quitando los `#` y `*` en `extract_markdown_text()`,
   porque es un problema de formato de la fuente, no de estructura normativa.
   Medición antes/después: 406 → 8.874 encabezados detectados en el corpus
   completo; en el alcance indexado, 0% → 100% de chunks citables.
2. **El anclaje a inicio de línea se conserva**, y es deliberado: los textos
   legales se referencian a sí mismos todo el tiempo ("de conformidad con el
   artículo 23 de esta ley"). Sin el ancla, cada una de esas menciones abriría
   un chunk nuevo a mitad de un artículo.
3. **Artículos transitorios.** La Constitución tiene un artículo 1 permanente y
   un artículo transitorio 1, y son normas distintas: se citan como "Artículo
   transitorio 19", no "Artículo 19".
4. **Marca de ordinal.** Las normas viejas escriben "ARTICULO 5o." por "5º"; se
   normaliza a "5" para que no aparezcan dos citas distintas del mismo artículo,
   conservando los artículos bis del tipo "47A".
5. **Párrafo gigante dentro de un artículo largo.** Dividir solo por párrafo
   dejaba 15 chunks fuera de presupuesto (máx. 1.451 tokens). Como e5 trunca en
   512 **sin avisar**, la cola de esos artículos habría quedado invisible para el
   retrieval. Ahora un párrafo que por sí solo excede el presupuesto se divide
   por oración.
6. **El frontmatter no se indexa.** `modification_summary` trae decenas de
   referencias a otras normas; indexarlo haría que el retrieval devuelva ese
   bloque como si fuera articulado.

## 5. Retrieval

- **`TOP_K`: 5** · **`RETRIEVAL_MIN_SCORE`: 0.855** (umbral de la válvula de escape)
- **Estado de la evidencia: CALIBRADO** contra una corrida real (2026-09-25, `colab/rag_ingenuo.ipynb`, fase 5):
  - El 0.3 que traía la plantilla de la skill **no sirve para e5**: sus
    embeddings son poco dispersos y pares de textos sin ninguna relación suelen
    dar coseno ~0.70-0.75. Con un piso de 0.3 la válvula de escape nunca se
    activaría y el sistema respondería con contexto irrelevante en vez de admitir
    que no sabe — precisamente el fallo que este RAG debe cerrar.
  - **Distribución medida:** preguntas *con* cobertura real en el corpus dieron
    scores 0.825-0.879 (mediana 0.841, n=20); preguntas *sin* cobertura dieron
    0.840-0.854 (n=2). **Los dos rangos se solapan** — ningún umbral único los
    separa perfectamente.
  - **0.80 (el punto de partida) resultó ser demasiado bajo**: quedaba por
    debajo del mínimo medido incluso para preguntas *sin* cobertura (0.840), así
    que en la práctica casi nada se filtraba. Confirmado con un caso real: la
    consulta "me despidieron sin pagarme la liquidación" recuperó artículos
    sobre liquidación de sindicatos en insolvencia (Decreto 2663 de 1950, Art.
    419; score 0.845) — contexto real pero fuera de tema — y el modelo generó
    una respuesta con esa cita en vez de reconocer que el contexto no aplicaba.
    Ver sección 9.
  - **Decisión:** subir el umbral a 0.855 (justo por encima del máximo medido
    sin cobertura). Prioriza no dejar pasar contexto irrelevante, a costa de
    descartar también contexto relevante que caiga en la zona de solape
    (0.825-0.854) — es la misma prioridad de "prudencia sobre certeza" del resto
    del proyecto (M1/M2), no una solución perfecta. La muestra de calibración
    *sin cobertura* es chica (n=2); si se repiten fallos de recuperación
    después de este ajuste, hay que ampliarla antes de tocar el umbral de nuevo.

## 6. Generación

- **Modelo:** `Qwen/Qwen2.5-7B-Instruct`, el mismo de M1/M2, greedy
  (`do_sample=False`) y cargado con el mismo helper de `tools/evaluation/
  generation.py` para que las cifras sigan siendo comparables.
- **Dos configuraciones a comparar:** RAG sobre el modelo base y RAG sobre el
  fine-tuneado (`USE_LORA`). El delta dice si el fine-tuning sigue aportando
  cuando el modelo ya tiene fuentes verificadas en el contexto, o si el RAG lo
  vuelve redundante.
- **Prompt aumentado:** 4 partes (instrucción / contexto con fuente / válvula de
  escape / pregunta). La instrucción parte del `SYSTEM_PROMPT` **real** del
  dataset de M1, textual, para no cambiar el rol con el que el modelo fue
  fine-tuneado — si se cambiara, el delta dejaría de ser atribuible al RAG.

## 7. Cómo ejecutarlo

Todo corre desde [`colab/rag_ingenuo.ipynb`](../colab/rag_ingenuo.ipynb) (GPU
T4 o superior). Las fases 1-2 construyen el índice; las 3-6 lo consultan.

En local, sin GPU, se puede correr todo lo que no necesita el modelo:

```bash
pip install -r requirements.txt
python -m tools.rag.corpus     # valida el manifiesto y lista las normas en alcance
pytest tests/rag -q            # 125 tests, incluida la regresión sobre el corpus real
```

## 8. Estado del checklist

| Ítem | Estado | Evidencia |
|---|---|---|
| Corpus real documentado | ✅ | sección 1 + `tools/rag/corpus.py` |
| Corpus real ingerido y chunkeado | ✅ | 3.425 chunks, 100% citables; `tests/rag/test_corpus_real.py` |
| Metadata completa por chunk | ✅ | fuente, artículo, URL, capítulo y vigencia, leídos del frontmatter |
| Backend documentado con razón | ✅ | sección 2 |
| Prompt de 4 partes con válvula de escape | ✅ en unit tests | `tests/rag/test_prompt_template.py` |
| **Índice construido (embeddings)** | ✅ | corrida 2026-09-25, 3.425 chunks indexados |
| **Válvula de escape probada end-to-end** | ✅ | fase 4 del notebook: 2/2 consultas fuera de corpus respondieron correctamente "no tengo información" |
| **`RETRIEVAL_MIN_SCORE` calibrado** | ✅ | sección 5 -- subido de 0.80 a 0.855 tras medir la distribución real |
| **Corrida sobre `eval_set.json`** | ✅ | fase 6 del notebook, 56/56 consultas, 1 sin contexto recuperado |
| Consultas fallidas anotadas | ✅ (parcial) | sección 9 -- 1 caso real documentado; falta re-correr la fase 6 con el umbral nuevo (0.855) y anotar si aparecen más |

## 9. Consultas fallidas anotadas (insumo para decidir si S08 hace falta)

Se llena con consultas reales fallidas una vez el índice esté construido.
Hybrid search, reranking y query transformation (S08) **no** se implementan
hasta que esta tabla justifique cuál hace falta y por qué — mismo estándar que
M1/M2: nada entra sin un delta medido.

| Consulta | Síntoma | Etapa responsable (ingest/chunk/embed/retrieve/generate) | ¿Técnica de S08 que lo arreglaría? |
|---|---|---|---|
| "Me despidieron sin pagarme la liquidación, ¿qué puedo hacer?" (corrida 2026-09-25, `RETRIEVAL_MIN_SCORE=0.80`) | Recuperó Decreto 2663 de 1950 Art. 419 (liquidador de sindicatos en insolvencia) y varios artículos del Código General del Proceso (score máx. 0.845) -- confunde "liquidación laboral" (pago al trabajador despedido) con "liquidador" (figura de insolvencia/procedimiento civil). El modelo generó una respuesta basada en ese contexto equivocado en vez de activar la válvula de escape. | `embed` (la confusión semántica está en el embedding de la consulta, no en el chunking ni el índice) y `retrieve` (con el umbral de 0.80 vigente en ese momento, el score 0.845 pasaba el piso sin problema) | Reranking con cross-encoder es el candidato más directo -- un cross-encoder puede distinguir "liquidación de prestaciones laborales" de "liquidador judicial de una organización sindical" mejor que la similitud de embeddings densos sola. Con un solo caso documentado no alcanza para justificar implementarlo todavía; pendiente re-correr la fase 6 completa con `RETRIEVAL_MIN_SCORE=0.855` (ya aplicado) para ver si el umbral nuevo alcanza a filtrar este tipo de caso o si persiste. |

## 10. Qué se entrega y qué continúa otra persona

**Entrega de M3 (este trabajo):** el RAG ingenuo completo — las 7 etapas, el
corpus decidido e ingerido, el prompt aumentado con válvula de escape, el
notebook que lo corre, y la salida de la corrida en formato Ragas
(`question` / `answer` / `contexts` / `ground_truth`) más la evidencia de
retrieval por consulta.

**Continúa otra persona:** el RAG avanzado (S08: hybrid search, reranking, query
transformation) y la evaluación con Ragas y con el harness de
`tools/evaluation/`. El contrato entre las dos mitades es
`pipeline.to_eval_record()`: ese formato es lo que la evaluación consume, y por
eso está fijado con tests que corren contra el `eval_set.json` real.
