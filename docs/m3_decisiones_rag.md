# M3 · Sistema RAG — decisiones

Documento de decisiones del sistema RAG de Amparo. Cubre las tres partes de M3:

- **Parte I — RAG ingenuo (S07), secciones 1-10:** `ingest → chunk → embed →
  store` offline, `retrieve → augment → generate` online.
- **Parte II — RAG avanzado (S08) + tool use (S10), secciones 11-17:** hybrid
  search, reranking y el retrieval expuesto como herramienta.
- **Parte III — RAG agéntico (S10), secciones 18-25:** el mini-agente ReAct,
  sus herramientas, la verificación de citas, la comparación de las tres rutas
  (una pasada, tool use, ReAct), su evaluación con RAGAS, el registro en W&B, la
  optimización del prompt con DSPy (extra) y los hallazgos de la corrida real de
  S08 con sus correcciones (sección 25).

Mismo estándar de documentación que M1/M2: **decisión + justificación +
evidencia**, no solo qué se eligió.

Fecha: 2026-09-21 (Parte I) · 2026-09-24 (Parte II) · código:
[`tools/rag/`](../tools/rag/) · ejecución:
[`colab/m3_s07_rag_ingenuo.ipynb`](../colab/m3_s07_rag_ingenuo.ipynb) (S07) ·
[`colab/m3_s08_rag_avanzado.ipynb`](../colab/m3_s08_rag_avanzado.ipynb) (S08) ·
[`colab/m3_s10_rag_agentico.ipynb`](../colab/m3_s10_rag_agentico.ipynb) (S10)

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

- **`TOP_K`: 5** · **`RETRIEVAL_MIN_SCORE`: 0.82** (umbral de la válvula de escape)
- **Estado de la evidencia: CALIBRADO** contra una corrida real (2026-09-25, `colab/m3_s07_rag_ingenuo.ipynb`, fase 5):
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
  - **Primera decisión:** subir el umbral a 0.855 (justo por encima del máximo medido
    sin cobertura). Prioriza no dejar pasar contexto irrelevante, a costa de
    descartar también contexto relevante que caiga en la zona de solape
    (0.825-0.854) — es la misma prioridad de "prudencia sobre certeza" del resto
    del proyecto (M1/M2), no una solución perfecta. La muestra de calibración
    *sin cobertura* es chica (n=2); si se repiten fallos de recuperación
    después de este ajuste, hay que ampliarla antes de tocar el umbral de nuevo.
  - **Ajuste final (0.855 → 0.82):** con 0.855, el 84% de las consultas del
    eval set se quedaba sin chunks: la mayor parte de la cobertura real cae en
    la zona de solape y el umbral la descartaba. Se bajó a 0.82, justo por
    debajo del mínimo medido con cobertura real (0.825). El costo es que los
    casos fuera de tema dentro del solape (como el de la liquidación, 0.845) ya
    no los filtra el umbral; ese fallo lo ataca el reranking de la Parte II
    (sección 11.2), que separa relevancia mejor que un piso de similitud.

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

Todo corre desde [`colab/m3_s07_rag_ingenuo.ipynb`](../colab/m3_s07_rag_ingenuo.ipynb) (GPU
T4 o superior). Las fases 1-2 construyen el índice; las 3-6 lo consultan.

En local, sin GPU, se puede correr todo lo que no necesita el modelo:

```bash
pip install -r requirements.txt
python -m tools.rag.corpus     # valida el manifiesto y lista las normas en alcance
pytest tests/rag -q            # 168 tests (S07 + S08), incluida la regresión sobre el corpus real
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
| **`RETRIEVAL_MIN_SCORE` calibrado** | ✅ | sección 5 -- 0.80 → 0.855 → 0.82 (final), con la distribución real medida |
| **Corrida sobre `eval_set.json`** | ✅ | fase 6 del notebook, 56/56 consultas, 1 sin contexto recuperado |
| Consultas fallidas anotadas | ✅ | sección 9 -- caso real documentado; lo ataca el reranking de la Parte II |

## 9. Consultas fallidas anotadas

Registro de consultas donde el retrieval no trae el chunk correcto, con su
diagnóstico por etapa. Es el insumo empírico que respalda las decisiones de la
Parte II y el material de trabajo para afinar el pipeline.

| Consulta | Síntoma | Etapa responsable (ingest/chunk/embed/retrieve/generate) | Técnica que lo corrige |
|---|---|---|---|
| "Me despidieron sin pagarme la liquidación, ¿qué puedo hacer?" (corrida 2026-09-25, `RETRIEVAL_MIN_SCORE=0.80`) | Recuperó Decreto 2663 de 1950 Art. 419 (liquidador de sindicatos en insolvencia) y varios artículos del Código General del Proceso (score máx. 0.845) -- confunde "liquidación laboral" (pago al trabajador despedido) con "liquidador" (figura de insolvencia/procedimiento civil). El modelo generó una respuesta basada en ese contexto equivocado en vez de activar la válvula de escape. | `embed` (la confusión semántica está en el embedding de la consulta, no en el chunking ni el índice) y `retrieve` (con el umbral de 0.80 vigente en ese momento, el score 0.845 pasaba el piso sin problema) | Reranking con cross-encoder es el candidato más directo -- un cross-encoder puede distinguir "liquidación de prestaciones laborales" de "liquidador judicial de una organización sindical" mejor que la similitud de embeddings densos sola. Implementado en la Parte II (sección 11.2, `tools/rag/rerank.py`). El umbral no lo resuelve solo: con el valor final (0.82) este score sigue pasando (sección 5). |
| "Me despidieron sin justa causa, ¿cuánto me deben de indemnización?" (revisión del corpus, 2026-09-26) | El corpus no contiene la regla vigente. `codigo_sustantivo_trabajo_decreto_2663_1950.md` trae el **texto original de 1950**: su "Artículo 64" trata de la terminación *con* justa causa y preaviso, y la tabla de indemnización del art. 64 vigente (modificado por la Ley 789 de 2002) no aparece en el archivo; la numeración tampoco coincide con el código vigente (la indemnización moratoria está en el 66 del corpus). La metadata dice `status: in_force`. El sistema puede citar "CST, Artículo 64" con un contenido que no es el vigente. | `ingest` (fuente: versión original en vez de la compilada vigente) — no la corrige ninguna técnica de retrieval | Reemplazar el archivo por la versión vigente compilada del CST y reconstruir el índice. Mientras tanto, los ejemplos de la S10 usan arriendo (Ley 820 de 2003) y plazos (CPACA), cuyo texto sí es el vigente. Revisar también las normas con muchas modificaciones (p. ej. Ley 100 de 1993). |
| Las 168 respuestas de la corrida A/B/C de S08 (2026-09-27, LoRA) | La frase de la válvula de escape **no apareció ni una vez**. En 5 casos gold sin contexto (p. ej. 9047 "me robaron el celular", config C) el modelo respondió de memoria. | `generate` (el modelo no obedece la regla del prompt) | Escape por código: sin contexto, responde el código sin llamar al modelo (sección 25, hallazgo 1). |
| 9102 "¿cuál es el número exacto del artículo de la Constitución que consagra la tutela?" (S08, config B) | Respondió "artículo 2" (es el 86), un artículo que no estaba entre los recuperados. | `generate` (cita de memoria bajo presión por un número exacto) | Verificación de citas en las tres rutas: se corrige una vez y, si insiste, escape por código (sección 25, hallazgo 2). |
| 9034 (arriendo, S08, config A) | Citó el "artículo 24" sin haberlo recuperado (se recuperaron los arts. 8, 10, 11, 22, 23 de la Ley 820). | `generate` | Igual que el anterior (sección 25, hallazgo 2). |
| Corrida A/B/C de S08 (2026-09-27): chunks por consulta y consultas vacías | B y C recuperan menos (3.55 y 3.71 chunks vs 4.57 en A) y C deja 4 casos gold sin contexto (A: 0). El chunk que la hybrid debía rescatar ("artículo 64", solo BM25) se descartaba. | `retrieve` (el recorte a top_k iba antes del piso, y el piso borraba todo lo solo-BM25) | Piso antes del recorte + excepción para referencias exactas a un artículo citado (sección 25, hallazgo 3). |
| 9102 "¿cuál es el número exacto del artículo de la Constitución que consagra la tutela?" (S08 corregido, 2026-09-27, A/B/C) | El artículo 86 (tutela) no aparece entre lo recuperado en ninguna de las tres configuraciones; lo recuperado son los arts. 1, 2, 4, 5, 42, 43, 51, 169 de la Constitución. | `retrieve` / `embed` (la consulta pregunta por "el número del artículo", no por el contenido de la tutela) | Pendiente: context recall de RAGAS (fase 5b de S10) lo debería mostrar; candidatos: expansión de consulta o `leer_articulo` en el agente. |

## 10. Alcance de cada parte

**Parte I — RAG ingenuo (S07):** las 7 etapas, el corpus ingerido, el prompt
aumentado con válvula de escape y el notebook que lo corre. La salida se emite en
formato Ragas (`question` / `answer` / `contexts` / `ground_truth`) con la
evidencia de retrieval por consulta.

**Parte II — RAG avanzado (S08) + tool use (S10):** hybrid search, reranking y el
retrieval expuesto como herramienta. Código en `tools/rag/{hybrid,rerank,tools}.py`,
integrado por bandera en `retrieve.py` / `pipeline.py`; ejecución en
[`colab/m3_s08_rag_avanzado.ipynb`](../colab/m3_s08_rag_avanzado.ipynb).

El contrato de salida es `pipeline.to_eval_record()`, estable entre las dos
partes: el RAG avanzado solo añade dos campos de trazabilidad
(`used_hybrid`/`used_rerank`) que identifican con qué configuración se generó
cada respuesta.

---

# Parte II · RAG avanzado (S08) + tool use (S10)

Sobre el RAG ingenuo de la Parte I se montan dos técnicas de recuperación —hybrid
search y reranking— y se expone el retrieval como herramienta con function
calling. Las tres se justifican por las características del corpus normativo y del
patrón de consulta de Amparo, ya establecidas en las secciones 3 y 5.

## 11. Técnicas elegidas: hybrid search y reranking

Cada técnica corrige un fallo concreto del retrieval denso de la Parte I.

### 11.1 Hybrid search (BM25 + denso): los términos exactos

El retrieval denso con e5 recupera por **significado**, que es lo adecuado para la
consulta coloquial de Amparo. Pero difumina los **términos exactos**, y en
derecho esos términos son decisivos: "artículo 64", "Ley 1480", "habeas data" son
cadenas literales, y los embeddings densos confunden el artículo 64 con el 46 o el
65 porque son vecinos semánticos. La sección 3 ya establece que e5 se eligió por
su fuerza en la asimetría de registro (consulta coloquial → texto normativo), una
fuerza ortogonal a la coincidencia léxica exacta.

BM25 puntúa por coincidencia de términos, premiando los raros: cubre exactamente
el punto ciego del denso, y sus fallos no se correlacionan con los de e5. Por eso
combinarlos mejora la recuperación en lugar de amplificar un mismo error. La
fusión de los dos rankings se hace con RRF (sección 12).

Código: [`tools/rag/hybrid.py`](../tools/rag/hybrid.py) · prueba del mecanismo:
[`test_bm25_encuentra_el_termino_exacto_que_el_denso_difuminaria`](../tests/rag/test_hybrid.py).

### 11.2 Reranking (cross-encoder): el ruido en el top-k

El retrieval denso y BM25 son bi-encoders y modelos léxicos: comparan la consulta
y cada chunk por separado. Son baratos y escalan, pero pierden matices. La sección
5 establece que los cosenos de e5 son poco dispersos (dos textos sin relación dan
~0.70-0.75), de modo que su top-k arrastra ruido: chunks que parecen relevantes
por vector pero no responden la pregunta.

El cross-encoder lee el par (consulta, chunk) junto, con atención cruzada, y
produce un puntaje de relevancia más fino. Es caro por par, así que se aplica solo
sobre los pocos candidatos que ya trajo el recuperador barato, en patrón embudo
(sección 13).

Código: [`tools/rag/rerank.py`](../tools/rag/rerank.py) · pruebas:
[`test_rerank.py`](../tests/rag/test_rerank.py).

### 11.3 Por qué no query transformation (multi-query, HyDE, step-back, decomposition)

Hybrid search y reranking atacan los dos fallos identificados del retrieval de
Amparo. Query transformation no entra por dos razones:

1. **Riesgo en el dominio.** Multi-query y HyDE hacen que un modelo reescriba o
   invente texto de consulta antes de buscar. En un asistente jurídico cuyo
   principio rector es no inventar normas, introducir texto generado en la etapa
   de recuperación abre una superficie de alucinación que contradice el diseño del
   sistema.
2. **Ya está cubierta por el tool use.** La herramienta de S10 (sección 15) deja
   que el modelo reformule la consulta al decidir qué buscar: una transformación
   acotada y con propósito, no la generación de variantes especulativas.

## 12. Fusión de rankings: Reciprocal Rank Fusion (RRF)

Los rankings denso y léxico se fusionan con RRF, `RRF(chunk) = Σ 1/(k + puesto)`,
con `k = 60`. Código: [`hybrid.reciprocal_rank_fusion`](../tools/rag/hybrid.py).

**Por qué puestos y no puntajes.** BM25 devuelve puntajes del orden de ~12 y el
coseno de e5 del orden de ~0.8: son escalas incomparables. Promediarlos, sumarlos
o normalizarlos con min-max mezcla unidades distintas y el resultado termina
dominado por la escala, no por la relevancia. RRF ignora el valor del puntaje y
usa solo el puesto —qué tan arriba quedó el chunk en cada lista—, que sí es
comparable entre recuperadores. Un chunk que ambos ubican arriba (consenso) gana
sobre uno que solo un recuperador prioriza.

**Por qué `k = 60`.** Es el valor del trabajo original de Cormack, Clarke y
Buettcher (2009). Amortigua el peso de los primeros puestos para que ningún
ranking domine la fusión por sí solo. El aporte de RRF es su robustez a las
escalas incomparables, no un ajuste fino de `k`.

Verificación: [`test_rrf_ignora_la_escala_de_los_puntajes`](../tests/rag/test_hybrid.py)
multiplica por 100 los puntajes de una lista y confirma que el orden fusionado no
cambia.

## 13. Patrón embudo y cross-encoder

Se recuperan `RERANK_INPUT_N = 30` candidatos baratos con hybrid search y el
cross-encoder los reordena para quedarse con `RERANK_OUTPUT_K = TOP_K = 5`.
Modelo: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`.

**El embudo.** El cross-encoder es caro por par y no puede correr sobre los 3.425
chunks del corpus. El embudo lo ejecuta solo 30 veces por consulta, no una vez por
chunk. El prompt sigue recibiendo 5 chunks, el mismo tamaño de contexto que la
Parte I: el reranking cambia *qué* chunks llegan al prompt, no *cuántos*.

**El modelo.** Un cross-encoder abierto y multilingüe entrenado en mMARCO, por el
mismo criterio con que se eligió e5 (sección 3): la consulta de Amparo es
coloquial en español y el chunk objetivo es texto normativo, así que el reranker
debe operar en español.

Verificación: [`test_el_embudo_recorta_de_muchos_a_pocos`](../tests/rag/test_rerank.py)
y [`test_el_reranker_recibe_mas_candidatos_de_los_que_devuelve`](../tests/rag/test_retrieve.py).

## 14. La válvula de escape a lo largo del pipeline

Esta es la decisión más delicada de la integración, porque toca la pieza central
del RAG de la Parte I: la válvula de escape.

El umbral `RETRIEVAL_MIN_SCORE` (0.82) está calibrado sobre el coseno de e5
(sección 5). En el pipeline avanzado, el campo `score` de cada resultado cambia de
significado: en el sistema denso es el coseno, tras la fusión RRF es el puntaje RRF
(~0.016) y tras el reranking es el del cross-encoder. Filtrar por `score`
descartaría todo en hybrid y compararía un puntaje sin relación con el umbral en
reranking: la válvula quedaría rota sin dar señal.

**Decisión.** `SearchResult` lleva un campo `dense_score` que preserva el coseno
de e5 a lo largo de todo el pipeline, y `apply_score_floor` filtra por
`dense_score`, nunca por `score`. La válvula sigue midiendo lo que fue calibrada
para medir —la relevancia semántica del chunk— sin importar cómo se reordene
después. Código: [`retrieve.apply_score_floor`](../tools/rag/retrieve.py) y el
campo en [`embed_store.SearchResult`](../tools/rag/embed_store.py).

**El chunk que solo trajo BM25.** Un chunk recuperado únicamente por coincidencia
léxica, sin que e5 lo considere relevante, tiene `dense_score = None` y no pasa el
piso. Es el comportamiento correcto: el umbral es una afirmación sobre relevancia
semántica, y compartir palabras no basta para fundamentar una respuesta jurídica.
BM25 aporta reordenando hacia arriba candidatos que ya tienen respaldo semántico,
no colando candidatos que el denso descartó.

> **Revisión (S10, con datos de la corrida real de S08).** Esta regla se mantiene
> con **una excepción acotada**: un chunk solo-BM25 pasa si es una *referencia
> exacta* a un artículo que la consulta cita, y —si la consulta nombra una norma—
> es de esa norma ("¿qué dice el artículo 64 del CST?"). Es justo el caso que la
> hybrid search existe para rescatar, y con la regla original se descartaba
> siempre. Además, el piso ahora se aplica **antes** del recorte a `top_k`. Detalle
> y evidencia en la sección 25, hallazgo 3.

El `__post_init__` de `SearchResult` copia `score → dense_score` cuando este viene
en `None`, para que el código de la Parte I siga viendo el coseno sin cambios. Por
eso el reranking y RRF asignan `dense_score` después de construir el objeto: de lo
contrario el auto-copiado lo sobrescribiría con el puntaje del reordenador.
Anotado en [`rerank.rerank`](../tools/rag/rerank.py).

Verificación:
[`test_sistema_C_respeta_la_valvula_de_escape_sobre_dense_score`](../tests/rag/test_retrieve.py)
asigna a un chunk solo-BM25 el mayor puntaje de cross-encoder y confirma que aun
así no entra al resultado.

## 15. Tool use (S10): el retrieval como herramienta

El retrieval avanzado se expone como una herramienta, `buscar_normas`, con
function calling: el modelo decide si llamarla, emite un JSON
`{"tool": ..., "args": {...}}`, el sistema lo ejecuta y le devuelve los chunks como
observación. Código: [`tools/rag/tools.py`](../tools/rag/tools.py).

**Por qué una herramienta y no recuperar siempre.** Exponer el retrieval como tool
le da al modelo dos capacidades que el RAG de una pasada no tiene: reformular la
consulta antes de buscar (transformación acotada, con propósito) y decidir no
buscar cuando la consulta no lo requiere —un saludo, una aclaración—, evitando una
recuperación inútil. La herramienta envuelve el mismo retrieval avanzado de las
secciones 11-14, sin abrir una segunda ruta de recuperación que mantener.

**Por qué una sola herramienta.** Amparo consulta fuentes verificadas; no ejecuta
acciones sobre el mundo (no radica una tutela, no paga una multa, no calcula plazos
con autoridad legal). Consultar el corpus es su única acción legítima, y
`buscar_normas` la cubre. Añadir herramientas sin un caso de uso real sería
superficie injustificada. (El agente ReAct de la Parte III sí suma una
calculadora: no es una acción sobre el mundo sino una herramienta de
razonamiento, y tiene un caso de uso medible; ver sección 18.)

**Robustez del bucle.**

- Un JSON malformado o sin campo `tool` hace que `extraer_tool_call` devuelva
  `None`, que el bucle interpreta como respuesta directa del modelo. Un modelo
  pequeño no siempre emite JSON válido; ante eso el sistema responde directo en
  lugar de fallar.
- Un error de validación (herramienta inexistente, argumentos ausentes) se
  devuelve como observación, no se lanza: el modelo lo lee y corrige en la
  siguiente vuelta.
- La observación incluye la cita de cada chunk, igual que el prompt aumentado de
  la Parte I, para que el modelo cite lo que efectivamente recuperó.
- `max_llamadas` acota el bucle para que un modelo que insista en pedir la
  herramienta no corra indefinidamente.
- El prompt del bucle incluye la frase exacta de la válvula de escape
  (`RESPUESTA_SIN_CONTEXTO`), la misma del RAG de una pasada, para que el harness
  la detecte igual en las dos rutas.
- La salida sigue el mismo contrato que `pipeline.answer_query` (`contexts`,
  `retrieved_chunks`, ...), con los chunks que devolvió la herramienta: sin eso
  la ruta no se podría evaluar con RAGAS.

Verificación: [`test_tools.py`](../tests/rag/test_tools.py) cubre el parser, el
dispatcher con su validación y el bucle propone → ejecuta → observa → responde.

## 16. Composición: el experimento A/B/C

Las dos técnicas se activan por bandera (`use_hybrid`, `use_rerank`) sobre un único
punto de entrada, `retrieve.retrieve`, propagado hasta `pipeline.answer_query`. Con
ambas banderas apagadas —el default de `config.USE_HYBRID`/`USE_RERANK`— el
retrieval es idéntico al de la Parte I.

Esto define tres configuraciones comparables donde lo único que cambia es el
retrieval; el prompt y el generador son los mismos:

| Sistema | `use_hybrid` | `use_rerank` | Retrieval |
|---|---|---|---|
| A | False | False | denso puro (coseno e5) |
| B | True | False | denso + BM25, fusión RRF |
| C | True | True | hybrid → cross-encoder reordena |

Mantener las tres sobre el mismo camino de código —en lugar de funciones
separadas— es lo que hace que cualquier diferencia entre ellas sea atribuible a la
técnica y no a una divergencia accidental de implementación. El sistema A
reproduce exactamente el retrieval de S07, garantizado por los tests de la Parte I
y por
[`test_sistema_A_por_defecto_es_denso_puro`](../tests/rag/test_retrieve.py). Cada
registro de salida lleva `used_hybrid`/`used_rerank`, de modo que las corridas de
los tres sistemas quedan etiquetadas y son separables.

## 17. Dónde corre cada componente

- **Liviano, en `requirements.txt`, ejecutable sin GPU:** `rank_bm25` (Python
  puro). La lógica pura —RRF, el parser de tool-calls, la orquestación A/B/C, el
  dispatcher— se prueba en local sustituyendo el recuperador denso y el
  cross-encoder por dobles de test.
- **Pesado, solo en Colab, con import perezoso:** el cross-encoder
  (`sentence-transformers`), e5 y Qwen. Sin la dependencia, el reranker falla con
  un `ImportError` explícito que indica que corre en Colab, no con un error mudo.
- **Ejecución:** [`colab/m3_s08_rag_avanzado.ipynb`](../colab/m3_s08_rag_avanzado.ipynb) carga
  el índice desde Drive, construye el BM25 una vez, corre la comparación A/B/C
  sobre retrieval y la corrida A/B/C sobre el eval set con su latencia. La demo
  del tool use está en `colab/m3_s10_rag_agentico.ipynb` (Parte III).

---

# Parte III · RAG agéntico (S10)

## 18. Mini-agente ReAct: cuándo hace falta encadenar pasos

El tool use de la sección 15 decide **si** buscar y **con qué consulta**, pero su
flujo es siempre buscar → responder. Hay consultas de Amparo que necesitan más de
un paso de naturaleza distinta: la **pregunta compuesta**, que pide una norma *y*
una operación sobre ella. Dos casos típicos:

- **Arriendo:** "pago 1.200.000 y el IPC del año pasado fue 5,2 %, ¿hasta cuánto
  me pueden subir?" → buscar el artículo 20 de la Ley 820 de 2003 (tope: 100 % del
  IPC) → calcular → responder citando la norma.
- **Plazos:** "radiqué un derecho de petición el 1 de septiembre, ¿cuándo me deben
  responder y si no, qué hago?" → buscar el término (CPACA, artículo 14: quince
  días) → contar los días hábiles → buscar la tutela → responder.

El RAG de una pasada trae la norma, pero deja la cuenta a la memoria del modelo,
que es donde se equivoca. (El ejemplo laboral del despido se descartó por el
problema del corpus del CST anotado en la sección 9.)

ReAct resuelve eso encadenando **pensamiento → acción → observación** hasta
responder. Código: [`tools/rag/agentico.py`](../tools/rag/agentico.py).

**Acciones.**

- `buscar_normas[consulta]`: el mismo retrieval avanzado del tool use (hybrid +
  rerank), invocado a través del mismo dispatcher. No se abre otra ruta de
  recuperación.
- `calculadora[expresion]`: aritmética exacta. Se evalúa con un parser de AST
  restringido (números, `+ - * / // % **`, paréntesis), **no con `eval()`**: la
  expresión la escribe el modelo, y `eval()` sobre texto generado ejecutaría
  código arbitrario. Convención: números sin separador de miles y con punto
  decimal (`1200000 * 1.052`). Acepta "2.000.000" (varios grupos de miles, no
  ambiguo), pero un solo punto (`1.052`) es siempre decimal: leerlo como miles
  daría, en el caso del IPC, un canon 1000 veces mayor sin ningún error visible.
- `leer_articulo[norma, número]`: lee un artículo **exacto** por su número,
  recorriendo la metadata del índice (sin búsqueda semántica). Reconoce la norma
  por número y año ("Ley 820 de 2003"), por nombre ("código sustantivo del
  trabajo") o por sigla (CST, CGP, CPACA); si el nombre es ambiguo pide precisar,
  y si la norma o el artículo no están en el corpus lo dice. Existe para el
  **usuario que se equivoca de artículo**: el prompt le pide al agente leer el
  artículo que menciona el usuario y comprobar que trate lo que pregunta; si no,
  decírselo y buscar el tema con `buscar_normas`, en vez de fundamentar en el
  número que le dieron. También sirve cuando una observación remite a otro
  artículo ("en los términos del artículo 13"). Lo que lee entra a `contexts` y a
  la verificación de citas igual que una búsqueda.
- `calcular_plazo[AAAA-MM-DD, n, habiles|calendario]`: fecha de vencimiento de un
  término, contando desde el día siguiente; en días hábiles salta sábados,
  domingos y festivos de Colombia, incluidos los trasladados por la Ley Emiliani
  (librería `holidays`). La observación dice qué festivos saltó. La herramienta
  **no** sabe cuántos días da la ley ni si son hábiles: eso lo dice la norma que
  el agente encontró. Solo cuenta.
- `Responder[respuesta]`: termina el bucle, si pasa la verificación de citas
  (sección 19).

**Ninguna herramienta contiene reglas legales.** Se descartó a propósito una tabla
de salarios mínimos o fórmulas de liquidación en código: serían reglas que no
salen del corpus y romperían el principio de citar solo fuentes verificadas.

**Por qué el formato de texto de ReAct y no JSON.** Es el formato del Lab B y
separa el pensamiento de la acción, que es lo que se audita. El parser toma la
*primera* acción de cada salida (un modelo pequeño a veces sigue escribiendo pasos
y observaciones inventadas que no se ejecutaron) y, para `Responder`, lee hasta el
último corchete (la respuesta puede citar "[1]" o tener varias líneas).

**Robustez.** Mismo criterio que el tool use: degradar, no romper.

- Una salida sin acción válida se toma como respuesta directa.
- Los errores de la calculadora vuelven como observación ("error: ...") para que
  el modelo corrija.
- `MAX_PASOS` (5) acota el bucle. Si se agota, se pide una respuesta final
  forzada; si tampoco llega, se responde con la frase de la válvula de escape. Es
  preferible admitir que no se resolvió que improvisar.

## 19. Verificación de citas: no inventar normas, como control y no como instrucción

El prompt ya le pide al modelo citar solo lo que vio, pero una instrucción se puede
ignorar. Por eso, antes de aceptar un `Responder`, el código extrae los artículos
que cita la respuesta ("artículo 20", "arts. 5, 6 y 7", "art. 6º") y los compara
con los que el agente **vio de verdad**: los `articulos_incluidos` de los chunks
que devolvieron sus búsquedas.

- **Si cita un artículo que no vio, la respuesta no se acepta.** Vuelve como
  observación ("tu respuesta cita el artículo X, que no aparece en tus
  observaciones") y el agente tiene que buscarlo o responder sin citarlo. El
  rechazo queda en la traza como `Responder (rechazado)` y consume un paso.
- **Si al final sigue citando algo que no vio**, se responde con la válvula de
  escape.
- **Los artículos que menciona el propio usuario cuentan como vistos.** Citar lo
  que el usuario dijo no es inventar, y la respuesta puede estar aclarando que ese
  artículo no trata lo que pregunta. Lo que el agente no debe hacer es
  fundamentar en ese artículo sin haberlo leído: para eso está `leer_articulo`
  (sección 18).

**Límite conocido:** compara números de artículo, no el par (norma, artículo).
Detecta el artículo inventado, pero no un artículo real atribuido a otra ley (el 20
de la Ley 820 citado como si fuera de la Ley 100). Cerrar ese caso exige extraer
también el nombre de la norma de la respuesta, que el modelo escribe de formas muy
variadas; queda como mejora.

El control nació en la ruta ReAct. La corrida real de S08 mostró citas inventadas
en el RAG de una pasada ("artículo 2" como el de la tutela), así que ahora corre
en las **tres rutas** con la misma función (`agentico.citas_no_verificables`, que
además rechaza sentencias, porque el corpus no tiene jurisprudencia): ver sección
25, hallazgo 2.

## 20. Contrato de salida y trazabilidad

Las tres rutas (una pasada, tool use, ReAct) devuelven el mismo contrato de
`pipeline.answer_query`, y `pipeline.to_eval_record` las lleva al formato RAGAS
sin casos especiales. Se agregan dos campos:

- `sistema`: `una_pasada`, `tool_use` o `react`, para que las corridas sean
  separables (mismo propósito que `used_hybrid`/`used_rerank` en A/B/C).
- `traza`: una fila por paso (pensamiento, acción, argumento, observación). Es la
  evidencia de auditoría: si una respuesta sale mal, dice en qué paso se torció.

En las rutas agénticas, `contexts` son **todos los chunks que el agente vio** en
sus búsquedas, sin duplicados: es contra eso que RAGAS mide si la respuesta se
apoyó en el contexto.

## 21. El experimento: ¿se justifica el agente?

No todo necesita un agente: cada paso es una generación más (latencia), y un
modelo que da vueltas puede empeorar una respuesta simple. Por eso las tres rutas
corren sobre el mismo eval set, con el mismo generador y el mismo retrieval
(configuración C), y lo único que cambia es quién decide cuándo y cuánto recuperar:

| Ruta | Qué decide el modelo | Costo esperado |
|---|---|---|
| Una pasada | nada | 1 generación |
| Tool use | si busca y con qué consulta | 2 generaciones típicas |
| ReAct | qué acciones encadena | 3 o más generaciones |

La corrida está en
[`colab/m3_s10_rag_agentico.ipynb`](../colab/m3_s10_rag_agentico.ipynb) (fase 4),
que guarda los registros y la latencia por ruta en `corridas_s10/` de Drive. Un
agente solo se justifica si mejora las métricas (RAGAS y harness) lo suficiente
para pagar su latencia.

Verificación: [`test_agentico.py`](../tests/rag/test_agentico.py) cubre el parser
de pasos; `leer_articulo` (artículo exacto, artículo dentro de un chunk
agrupado, siglas, norma o artículo que no está, norma ambigua, y el usuario
equivocado de artículo; más una prueba sobre el corpus real en
`test_corpus_real.py`); la calculadora (que no ejecuta código y que `1.052` es decimal);
`calcular_plazo` (días hábiles con festivos, calendario, errores); la verificación
de citas (cita vista, inventada, mencionada por el usuario; rechazo y corrección;
válvula de escape si insiste), y el bucle: pregunta compuesta, plazo, `contexts`
sin duplicados, paso a `to_eval_record` y límite de pasos.

## 22. Evaluación con RAGAS (Lab C)

RAGAS evalúa el RAG **por dentro**: toma cada caso resuelto (pregunta, contextos,
respuesta, referencia) y le calcula cuatro notas de 0 a 1, cada una comparando dos
piezas. Por eso dice **dónde** falla, cosa que el harness de M2 (que mira solo la
respuesta final) no puede. Código:
[`tools/evaluation/ragas_metrics.py`](../tools/evaluation/ragas_metrics.py).

| Métrica | Compara | Si sale baja, el problema es… |
|---|---|---|
| faithfulness | respuesta vs contextos | el generador inventa o completa de memoria |
| context_precision | contextos vs pregunta | ruido en el top-k (→ rerank) |
| context_recall | referencia vs contextos | el retrieval no encuentra (→ hybrid, corpus) |
| answer_relevancy | respuesta vs pregunta | divaga, o escapa cuando sí había respuesta |

**Decisión: implementación propia y no la librería `ragas`.**

1. **El juez es Groq (`openai/gpt-oss-120b`), no Qwen.** El M2 midió que el juez
   Qwen se prefirió a sí mismo 60 de 60 veces; usar el modelo evaluado como juez
   de RAGAS repetiría ese sesgo. Es el mismo juez externo de M2
   (`external_judge.py`). El agente ReAct sí usa Qwen, y debe: es el sistema
   evaluado, y las tres rutas tienen que compartir generador para ser comparables.
2. **Cupo.** La capa gratuita de Groq tiene un límite diario de tokens. La
   librería hace varias llamadas por métrica y reenvía el contexto en cada una.
   Aquí las tres métricas de contexto salen de **una sola llamada por caso**, que
   devuelve en JSON los veredictos de las tres; `answer_relevancy` es una llamada
   corta sin contexto. Cada caso cuesta del orden de 3.000-4.000 tokens (medido en
   `tokens_juez`), así que 50 casos × 3 rutas pueden no caber en un día: la
   corrida guarda un **checkpoint** por caso en Drive (el mismo mecanismo de M2) y
   se retoma al día siguiente o con la key de otro miembro.
3. **Mismo patrón del repo:** el juez y los embeddings se inyectan, así que las
   fórmulas y el parseo se prueban sin red ni GPU.

**Fórmulas (las de RAGAS).** Faithfulness: afirmaciones respaldadas / total.
Context precision: *average precision* sobre el ranking (un chunk útil en la
posición 1 vale más que en la 5). Context recall: oraciones de la referencia
atribuibles al contexto / total. Answer relevancy: coseno medio (e5) entre la
pregunta y tres preguntas que el juez genera desde la respuesta.

**Tratamiento de los adversariales.** En los casos **adversariales** lo correcto
es reconocer un límite, y RAGAS lo castigaría (answer relevancy 0). Pero no todos
esperan la frase de escape: de los 6 del eval set, uno espera que se priorice la
seguridad ante una amenaza, otro que no se garantice un resultado, otro que se
niegue a ayudar a ocultar bienes. Por eso RAGAS se calcula sobre los **gold**, y
los adversariales se miden con la **prudencia**
(`agentico.es_prudente`): usa la frase de escape, o no cita artículos que no vio,
no cita sentencias (el corpus no tiene jurisprudencia: serían de memoria) y no
promete resultados. Es un piso verificable; lo específico de cada adversarial lo
juzga el harness de M2 con su `criterio`. En los gold se reporta además la tasa de
escape (alta = se niega de más) y la de **citas no respaldadas** (debería ser 0).
En un caso gold que escapa, faithfulness no aplica (no afirmó nada) y answer
relevancy vale 0, como en RAGAS.

**Robustez.** Un veredicto mal formado deja la métrica en `None` (no en 0) y se
cuenta como fallo de parseo: un error del juez no puede pasar por un mal puntaje
del sistema. Cada promedio reporta sobre cuántos casos se calculó.

**Dos experimentos, un juez.** La fase 5 evalúa las rutas de S10 (una pasada,
tool use, ReAct: ¿qué forma de responder es mejor?) y la fase 5b las búsquedas de
S08 (A/B/C: ¿qué búsqueda es mejor?). S08 solo genera y reporta métricas sin juez;
todo lo que necesita a Groq corre en S10.

Verificación:
[`test_ragas_metrics.py`](../tests/evaluation/test_ragas_metrics.py) cubre las
fórmulas, el parseo, que el contexto viaja en una sola llamada, la válvula de
escape, el juez caído, el checkpoint y el resumen por ruta. Ejecución: fase 5 de
[`colab/m3_s10_rag_agentico.ipynb`](../colab/m3_s10_rag_agentico.ipynb).

## 23. Seguimiento en Weights & Biases

Los números de RAGAS se pierden si solo se miran en pantalla. Cada ruta se
registra como una corrida del proyecto `amparo-rag`, en la cuenta del equipo
(la misma entidad de M1), con: los promedios como escalares, una tabla por caso
(pregunta, respuesta, métricas) y, en las rutas agénticas, la **traza del agente**
paso a paso. Una corrida `comparativa` pone las rutas lado a lado, y todas las de
una sesión comparten un `group` para compararlas con versiones futuras del
sistema. Código: [`tools/evaluation/tracking.py`](../tools/evaluation/tracking.py).

**Credenciales.** Las keys (`WANDB_API_KEY`, `GROQ_API_KEY`) se leen de los
secretos de Colab y nunca se escriben en el notebook ni en el repo. Sin key de
W&B, la corrida sigue en modo offline y se sube después con `wandb sync`. La
entidad y el proyecto se pasan desde el notebook: el código no depende de una
cuenta.

Verificación: [`test_tracking.py`](../tests/evaluation/test_tracking.py), con un
módulo `wandb` falso. Ejecución: fase 6 del notebook de S10.

## 24. Extra: optimización del prompt con DSPy

Con una métrica confiable, el prompt se puede optimizar en vez de escribirlo a
mano: DSPy prueba instrucciones y ejemplos (few-shot), mide cada intento y se
queda con el mejor. Código: [`tools/rag/dspy_prompt.py`](../tools/rag/dspy_prompt.py);
ejecución: [`colab/m3_s10_extra_dspy.ipynb`](../colab/m3_s10_extra_dspy.ipynb).

**Qué se optimiza: el prompt de generación del RAG de una pasada**, con el
retrieval fijo (configuración C). Los contextos se recuperan una vez y se guardan;
la única variable es el prompt, así que cualquier cambio en el puntaje es
atribuible a él. Se eligió la generación (y no la reformulación de consultas del
tool use) porque es donde vive el principio de Amparo —citar solo lo que está en
el contexto, escapar cuando no hay— y porque se puede medir sin juez.

**Métrica programática (`metrica_amparo`).** Optimizar evalúa cientos de
respuestas; con un juez LLM se agotaría el cupo de Groq. La métrica usa las mismas
reglas verificables del agente ReAct (sección 19):

| Caso | 1.0 | 0.5 | 0.0 |
|---|---|---|---|
| gold con contexto | cita ≥1 artículo del contexto y ninguno ajeno | responde sin citar | cita algo ajeno, cita sentencias, promete resultado, o escapa teniendo contexto |
| gold sin contexto | escapa | — | responde de memoria |
| adversarial | es prudente (`es_prudente`) | — | no es prudente |

**No mide si la respuesta es jurídicamente correcta**; mide honestidad con las
fuentes. Por eso el prompt ganador se valida al final con RAGAS (juez Groq), y
solo se adopta si no empeora RAGAS ni la prudencia.

**Datos sin fuga.** El eval set es el test y se usa una sola vez al final.

- **train (46) y dev (24):** 40 + 20 preguntas del dataset de M1, solo de las 9
  categorías que cubre el corpus, **excluyendo las 20 que también están en el
  eval set**, repartidas por categoría con semilla fija (reproducible).
- **10 adversariales nuevos** (`ADVERSARIALES_DSPY`: 6 a train, 4 a dev), de los
  mismos tipos que los del eval set pero distintos, para que el prompt aprenda el
  comportamiento y no memorice el examen. Viven en el código, documentados, en vez
  de en un archivo aparte.
- La referencia de cada gold es la respuesta de M1, que no está anclada al corpus:
  por eso no entra a la métrica; solo sirve de ejemplo en los demos.

**Optimizadores, de menos a más:** el prompt escrito a mano (punto de partida,
misma métrica) → `BootstrapFewShot` (elige hasta 3 ejemplos entre las respuestas
perfectas en train) → `MIPROv2` en modo `light` (propone instrucciones candidatas y
busca la mejor combinación instrucción + ejemplos con optimización bayesiana,
midiendo en dev). Gana el mayor puntaje en dev; ante empate, el más simple.

**Modelo.** DSPy habla con el modelo por una API compatible con OpenAI, así que la
optimización corre con `qwen2.5:7b` en Ollama (misma familia y tamaño que el
generador; otra cuantización). Para que la cifra final sea comparable con las
demás rutas, **el test corre con el generador de HF**: el prompt ganador se
exporta a JSON (instrucciones + demos) y `pipeline.answer_query(prompt_optimizado=...)`
lo usa con la misma estructura system/user del prompt original. La salida se marca
`una_pasada_dspy` y se registra en W&B junto a las otras rutas.

**Versión fijada:** `dspy[optuna]==3.4.0` (la API de los optimizadores cambia entre
versiones; `optuna` lo exige MIPROv2). El flujo completo —evaluación,
`BootstrapFewShot`, `MIPROv2` y exportación— se verificó con esa versión usando un
modelo simulado.

**Adopción.** Si el prompt optimizado gana en test y no empeora RAGAS, se versiona
en `results/m3_dspy_prompt.json`. Si no gana, se reporta igual: es evidencia de que
el prompt escrito a mano ya estaba cerca del óptimo para esta métrica.

Verificación: [`test_dspy_prompt.py`](../tests/rag/test_dspy_prompt.py) cubre la
división (sin fuga, tamaños, categorías, reproducible, adversariales distintos), la
métrica en cada caso de la tabla, la exportación, los mensajes para HF y que
`answer_query` use el prompt optimizado sin cambiar el retrieval.

## 25. Hallazgos de la corrida real de S08 y correcciones

**La corrida.** `colab/m3_s08_rag_avanzado.ipynb`, 2026-09-27, con
`USE_LORA = True` (el modelo de M1 + RAG), sobre el eval set completo (50 gold +
6 adversariales) en las tres configuraciones. Registros en Drive
(`rag/corridas_abc/`). Se analizaron sin juez, con las reglas programáticas del
repo (`ragas_metrics.tasas_de_escape`, `dspy_prompt.puntaje_de_record`):

| | A denso | B + hybrid | C + rerank |
|---|---|---|---|
| Consultas sin contexto (de ellas gold) | 1 (0) | 2 (1) | 5 (4) |
| Chunks por consulta | 4.57 | 3.55 | 3.71 |
| Respuestas gold que citan algún artículo | 22 % | 10 % | 10 % |
| Respuestas gold con cita no respaldada | 1 | 0 | 0 |
| Prudencia en adversariales | 6/6 | 5/6 | 6/6 |
| Métrica de honestidad (0-1, `puntaje_de_record`) | 0.634 | 0.571 | 0.562 |
| Uso de la frase de escape | 0/56 | 0/56 | 0/56 |
| Latencia (s/consulta) | 6.42 | 6.34 | 6.30 |

B y C cambian mucho lo que se recupera (el primer chunk difiere del de A en 31 y
44 de 56 consultas), pero sin juez no se ven mejores que A. S08 no tiene juez: la
pregunta "¿qué búsqueda es mejor?" se responde con RAGAS (sobre todo context
recall y context precision) en la **fase 5b de `m3_s10_rag_agentico.ipynb`**, que
evalúa con el juez Groq las corridas A/B/C guardadas en Drive y las registra en
W&B en su propio grupo (`s08-abc-…`). La latencia casi no cambia: la domina la
generación (~6 s), no el retrieval.

### Hallazgo 1 — La válvula de escape del prompt nunca se activó

**Evidencia.** 0 de 168 respuestas usaron la frase de escape. En los casos sin
contexto, el modelo respondió igual, de memoria: 9049 (B), 9012, 9013, 9023 y 9047
(C). Ejemplo, 9047 "me robaron el celular": sin ninguna norma recuperada, respondió
sobre denuncias e indemnización.

**Causa.** La válvula existía solo como instrucción del prompt y el modelo no la
obedece. Con LoRA se suma que M1 le enseñó su propio estilo de prudencia ("revisa
tu contrato", "consulta a un abogado") en vez de la frase exacta. Es el mismo
problema que motivó el M3 —una regla que depende de que el modelo quiera
cumplirla— y el mismo que la sección 19 ya había resuelto con código en el agente
ReAct.

**Corrección: escape por código en las tres rutas.** Si no hay contexto, la
respuesta la da el código, **sin llamar al modelo**:
`RESPUESTA_ESCAPE_POR_CODIGO` (en `prompt_template.py`) = la frase de escape
(para que el harness la detecte) + una orientación fija sin normas: dónde
consultar y, si hay riesgo, la Línea 123. Así no se pierde la orientación de
seguridad que un adversarial como el de la amenaza necesita.

- Una pasada (`pipeline.answer_query`): si `retrieve` no trae nada.
- Tool use (`tools.responder_con_tools`): si usó la herramienta y no encontró
  ninguna norma. Un saludo, sin búsqueda, sigue respondiéndose normal.
- ReAct (`agentico.agente_react`): si buscó (`buscar_normas`/`leer_articulo`) y no
  encontró ninguna norma.

Cada salida registra en `verificacion.escape_por_codigo` si el código intervino y
por qué (`sin_contexto` o `citas_no_verificables`), para auditar.

### Hallazgo 2 — Citas inventadas bajo presión

**Evidencia.** 9102 (config B): se le pide "el número exacto del artículo de la
Constitución que consagra la tutela" y responde "artículo 2" (es el 86), que no
estaba entre lo recuperado. 9034 (config A): cita el "artículo 24" de la Ley 820
cuando lo recuperado eran los artículos 8, 10, 11, 22 y 23.

**Causa.** La verificación de citas (sección 19) solo existía en la ruta ReAct; el
RAG de una pasada y el tool use entregaban la respuesta sin revisarla.

**Corrección: la misma verificación en las tres rutas**
(`agentico.citas_no_verificables`: artículos no recuperados + sentencias, que el
corpus no tiene). Si la respuesta cita algo que no se puede verificar, se regenera
**una vez** con una nota de corrección; si insiste, escape por código. En una
respuesta limpia no hay costo extra: la segunda generación solo ocurre cuando hay
algo que corregir.

### Hallazgo 3 — La hybrid search descartaba justo lo que debía rescatar

**Evidencia.** B y C recuperan menos chunks (3.55 y 3.71 vs 4.57) y C deja 4 casos
gold sin contexto (A: 0). En la fase 2 del notebook de S08, para "¿qué dice el
artículo 64 del código sustantivo del trabajo?", C pone el artículo 64 del CST
(solo BM25) en primer lugar, pero eso es con el piso desactivado; en la corrida
real ese chunk se descartaba.

**Causa.** Dos cosas juntas en `retrieve`: (1) se recortaba a `top_k` y **después**
se aplicaba el piso, así que los chunks solo-BM25 ocupaban puestos del top-5 y el
piso los borraba, dejando menos de 5 aunque hubiera candidatos válidos más abajo;
(2) el piso descartaba **todo** chunk solo-BM25 (sección 14), incluida la referencia
exacta que motiva la hybrid search.

**Corrección.**

1. El piso se aplica **antes** del recorte: el top-5 se llena con los mejores
   candidatos que sí pasan. En A no cambia nada (la lista viene ordenada por
   coseno y el piso solo quita la cola), así que A sigue reproduciendo S07.
2. **Excepción acotada** a la regla de la sección 14 (`retrieve.es_referencia_exacta`):
   un chunk solo-BM25 pasa si contiene un artículo que la consulta cita
   explícitamente y, si la consulta nombra una norma, es de esa norma (el 64 del
   CGP no pasa por una pregunta sobre el CST). Un chunk solo-BM25 sin esa
   referencia se sigue descartando.

**Pendiente, para revisar con quien diseñó la Parte II:** la alternativa más
general sería calcular el coseno real de los chunks solo-BM25 (el índice FAISS
plano permite reconstruir sus vectores) y aplicarles el mismo piso que a los demás.
Se eligió la excepción acotada porque no cambia la API del store y cubre el caso
que motiva la técnica.

### Resultado de las correcciones (corrida "después", 2026-09-27)

Se volvió a correr S08 con las correcciones (mismas banderas, LoRA, 56 preguntas).
Tabla completa y casos en
[`results/m3_s08_busqueda_2026-09-27.md`](../results/m3_s08_busqueda_2026-09-27.md).

| | A antes → después | B antes → después | C antes → después |
|---|---|---|---|
| Consultas sin contexto (gold) | 1 (0) → 1 (0) | 2 (1) → 1 (0) | 5 (4) → **1 (0)** |
| Artículos por consulta | 4.57 → 4.57 | 3.55 → **4.57** | 3.71 → **4.57** |
| Citas no respaldadas (gold) | 1 → **0** | 0 → 0 | 0 → 0 |
| Prudencia en adversariales | 6/6 → 6/6 | 5/6 → **6/6** | 6/6 → 6/6 |
| Honestidad con las fuentes | 0.634 → 0.643 | 0.571 → **0.643** | 0.562 → **0.607** |
| Uso de la frase de escape | 0/56 → 1/56 | 0/56 → 1/56 | 0/56 → 1/56 |

- **Hallazgo 1:** el escape por código se activó en el único caso sin contexto
  (9101, California) en las tres configuraciones.
- **Hallazgo 2:** el modelo volvió a inventar las dos citas de la corrida anterior
  (9034 "artículo 24" en A, 9102 "artículo 2" en B); la verificación las rechazó y
  las respuestas regeneradas ya no las citan. **Límite observado:** en 9102 la
  respuesta corregida ya no inventa el número, pero afirma algo falso (que la
  Constitución no tiene un artículo de tutela). La verificación detecta números no
  recuperados, no afirmaciones falsas: eso lo mide faithfulness en RAGAS.
- **Hallazgo 3:** B y C ya no pierden artículos (4.57 por consulta, igual que A) y
  C pasó de 4 casos gold sin contexto a 0. La excepción para referencias exactas no
  se activó (ninguna pregunta del eval set cita un número de artículo del corpus):
  la mejora viene del piso antes del recorte.
- **Nuevo, para la evaluación con juez:** el artículo 86 (tutela) no se recupera
  en ninguna configuración para 9102: es una falla de búsqueda que context recall
  debería mostrar.

Sin juez, A y B quedan empatados y C un poco por debajo (cita menos). La pregunta
"¿qué búsqueda es mejor?" la cierra RAGAS en la fase 5b de S10.

### Qué cambia para las corridas siguientes

- La primera tabla de esta sección es **anterior** a las correcciones; el
  resultado después de corregir está arriba y en `results/`.
- **Fase 5 de S10 (RAGAS) ante el cupo de Groq:** un caso en el que el juez no
  respondió ya no se guarda en el checkpoint (antes quedaba marcado como evaluado
  y se saltaba al retomar); con límite por minuto el código espera y reintenta, y
  con el cupo diario agotado se detiene tras 3 fallos seguidos y avisa cuántos
  faltan. La fase 5b reusa las notas de casos idénticos (la configuración C de S08
  y la ruta "una pasada" de S10 son el mismo sistema), sin gastar juez.
- La corrida principal de S08, S10 y DSPy usa `USE_LORA = True`: Amparo es el
  modelo de M1 + RAG, y es lo que se entrega. `False` queda como ablación ("¿el
  fine-tuning sigue aportando con RAG?"). En S10 los archivos llevan sufijo
  `_lora`/`_base` y no se pisan; en S08 no, así que una segunda corrida sobrescribe
  la primera.

Verificación: `test_retrieve.py` (piso antes del recorte, referencia exacta,
norma nombrada), `test_pipeline.py` y `test_tools.py` (escape por código sin
llamar al modelo, corrección de una cita, escape si insiste, respuesta limpia sin
regenerar) y `test_agentico.py` (escape si buscó y no encontró, rechazo de
sentencias).
