# M3 · Sistema RAG — decisiones

Documento de decisiones del sistema RAG de Amparo. Cubre las dos mitades de M3:

- **Parte I — RAG ingenuo (S07), secciones 1-10:** `ingest → chunk → embed →
  store` offline, `retrieve → augment → generate` online.
- **Parte II — RAG avanzado (S08) + tool use (S10), secciones 11-19:** hybrid
  search, reranking y el retrieval expuesto como herramienta.

Mismo estándar de documentación que M1/M2: **decisión + justificación +
evidencia**, no solo qué se eligió.

Fecha: 2026-09-21 (Parte I) · 2026-09-24 (Parte II) · código:
[`tools/rag/`](../tools/rag/) · ejecución:
[`colab/rag_ingenuo.ipynb`](../colab/rag_ingenuo.ipynb) (S07) ·
[`colab/rag_avanzado.ipynb`](../colab/rag_avanzado.ipynb) (S08/S10)

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

- **`TOP_K`: 5** · **`RETRIEVAL_MIN_SCORE`: 0.80** (umbral de la válvula de escape)
- **Estado de la evidencia: SIN CALIBRAR.** Es un pendiente explícito:
  - El 0.3 que traía la plantilla de la skill **no sirve para e5**: sus
    embeddings son poco dispersos y pares de textos sin ninguna relación suelen
    dar coseno ~0.70-0.75. Con un piso de 0.3 la válvula de escape nunca se
    activaría y el sistema respondería con contexto irrelevante en vez de admitir
    que no sabe — precisamente el fallo que este RAG debe cerrar.
  - 0.80 es un punto de partida derivado de ese rango, no una medición. La
    **fase 5 del notebook** hace la calibración: recupera sin piso, compara la
    distribución de scores de preguntas con y sin cobertura, y el corte se anota
    acá.

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
| **Índice construido (embeddings)** | ⬜ | requiere correr las fases 1-2 del notebook en Colab |
| **Válvula de escape probada end-to-end** | ⬜ | fase 4 del notebook |
| **`RETRIEVAL_MIN_SCORE` calibrado** | ⬜ | fase 5 del notebook; anotar el resultado en la sección 5 |
| **Corrida sobre `eval_set.json`** | ⬜ | fase 6 del notebook (56 registros: 50 gold + 6 adversariales) |
| Consultas fallidas anotadas | ⬜ | tabla de la sección 9, se llena con la corrida |

## 9. Consultas fallidas anotadas (insumo para decidir si S08 hace falta)

Vacía a propósito. Se llena con consultas reales fallidas una vez el índice esté
construido. Sirve como el diagnóstico *a posteriori* que valida la decisión de la
sección 12 (por qué hybrid y reranking) — mismo estándar que M1/M2: nada se
declara medido sin un delta medido.

| Consulta | Síntoma | Etapa responsable (ingest/chunk/embed/retrieve/generate) | ¿Técnica de S08 que lo arreglaría? |
|---|---|---|---|
| | | | |

> Esta tabla se llena con el diagnóstico por consulta de la Fase 2 de
> [`colab/rag_avanzado.ipynb`](../colab/rag_avanzado.ipynb).

## 10. Qué se entrega y quién continúa

**Parte I — RAG ingenuo (S07):** las 7 etapas, el corpus decidido e ingerido, el
prompt aumentado con válvula de escape, el notebook que lo corre, y la salida de
la corrida en formato Ragas (`question` / `answer` / `contexts` /
`ground_truth`) más la evidencia de retrieval por consulta.

**Parte II — RAG avanzado (S08) + tool use (S10):** hybrid search, reranking y el
retrieval-as-tool. Documentado en las secciones 11-19; código en
`tools/rag/{hybrid,rerank,tools}.py` integrado por bandera en `retrieve.py` /
`pipeline.py`; ejecución en [`colab/rag_avanzado.ipynb`](../colab/rag_avanzado.ipynb).

**Continúa otra persona:** la **evaluación** con Ragas y con el harness de
`tools/evaluation/` sobre las tres corridas A/B/C. El contrato entre las mitades
es `pipeline.to_eval_record()`: ese formato es lo que la evaluación consume, y por
eso está fijado con tests que corren contra el `eval_set.json` real. El RAG
avanzado solo le agregó dos campos de trazabilidad (`used_hybrid`/`used_rerank`)
sin romper el contrato.

---

# Parte II · RAG avanzado (S08) + tool use (S10)

Continúa la Parte I. Las dos técnicas avanzadas de recuperación (hybrid search y
reranking) y la herramienta de S10 (retrieval-as-tool). La evaluación (Ragas +
harness de M2) la corre otra persona sobre las salidas de este pipeline, por el
contrato `pipeline.to_eval_record()` (sección 10).

## 11. Estado de la evidencia — leer primero

La regla del proyecto (M1/M2 y la Parte I) es **nada entra sin un delta medido**.
Aquí hay una tensión honesta que conviene declarar de entrada:

- La tabla de "consultas fallidas" de la sección 9 está **vacía**, porque el
  índice FAISS todavía no se ha construido en Colab (varios ítems del checklist
  de la sección 8 siguen abiertos). Sin esa tabla, no hay un delta medido
  *previo* que diga cuál técnica hace falta.
- La entrega M3 (dom 27 SEP) exige ≥2 técnicas avanzadas + ≥1 tool.

**Decisión tomada:** implementar las dos técnicas con **justificación a priori
por las características conocidas del corpus y del dominio** (documentadas abajo y
ya observadas en M2 y en la Parte I), y dejar el código y el notebook preparados
para que el compañero de evaluación **mida el delta A/B/C** y cierre la
justificación. Todo lo que en esta parte sea hipótesis y no medición está marcado
como tal, con un puntero a la fase del notebook que lo valida (sección 19).

Esto **no** es saltarse la regla: es separar "por qué es razonable esperar que la
técnica ayude" (diseño, a priori) de "cuánto ayudó de hecho" (evaluación, a
posteriori). Lo primero es lo que justifica implementarla; lo segundo es lo que
la entrega reporta. Presentar una hipótesis como medición sí violaría el
estándar, y por eso se evita.

## 12. Qué técnicas y por qué esas

De las cuatro familias que enseña S08 (hybrid search, reranking, y las query
transformations: multi-query / HyDE / step-back / decomposition), se implementan
**hybrid search** y **reranking**. Cada una ataca un fallo *conocido* del
retrieval de Amparo:

### 12.1 Hybrid search (BM25 + denso) — el punto ciego de los términos exactos

- **Decisión:** agregar BM25 (búsqueda léxica) al retrieval denso de e5 y
  fusionar con RRF.
- **Justificación (a priori, por el dominio):** el RAG ingenuo usa e5, que
  recupera por **significado**. Eso es lo correcto para la consulta coloquial de
  Amparo, pero tiene un punto ciego documentado: los **términos exactos** que el
  denso difumina. En derecho eso pesa — "artículo 64", "Ley 1480", "habeas data"
  son cadenas literales, y los embeddings densos tienden a mezclar el artículo 64
  con el 46 o el 65 porque son semánticamente vecinos. Esto no es especulación
  genérica: la sección 3 ya documenta que e5 fue elegido por su fuerza en la
  asimetría de registro (consulta coloquial → texto normativo), fuerza que es
  justamente ortogonal a la coincidencia léxica exacta. BM25 puntúa por términos
  raros, que es donde el denso falla, y sus fallos **no están correlacionados**
  con los del denso — por eso la mezcla paga en vez de amplificar el mismo error.
- **Evidencia disponible hoy:** el test
  [`test_bm25_encuentra_el_termino_exacto_que_el_denso_difuminaria`](../tests/rag/test_hybrid.py)
  muestra el mecanismo sobre un corpus mínimo. El delta agregado sobre el eval
  set real lo mide la Fase 4 del notebook.

### 12.2 Reranking (cross-encoder) — el ruido en el top-k

- **Decisión:** reordenar los candidatos con un cross-encoder antes de armar el
  prompt, en patrón embudo.
- **Justificación (a priori, por el modelo):** el retrieval denso y BM25 son
  **bi-encoders / léxicos**: comparan la consulta y cada chunk por separado.
  Baratos y escalables, pero pierden matices. La sección 5 ya documenta que los
  cosenos de e5 son **poco dispersos** (dos textos sin relación dan ~0.70-0.75),
  lo que significa que su top-k trae **ruido**: chunks que parecen relevantes por
  vector pero no responden la pregunta. Un cross-encoder lee el par (consulta,
  chunk) **junto**, con atención cruzada, y produce un puntaje de relevancia
  mucho más fino. Es caro por par, así que solo se corre sobre los pocos
  candidatos que ya trajo el recuperador barato.
- **Evidencia disponible hoy:** los tests de
  [`test_rerank.py`](../tests/rag/test_rerank.py) prueban la lógica del embudo
  (entra top-N, sale top-k, reordena por el puntaje del cross-encoder). El delta
  agregado lo mide la Fase 4.

### 12.3 Por qué NO multi-query (ni HyDE, ni step-back, ni decomposition) — todavía

- **Decisión:** no implementar query transformation como técnica de retrieval en
  esta entrega.
- **Justificación:**
  1. **Suficiencia:** la entrega pide ≥2 técnicas; hybrid + reranking ya las
     cubren, y son las dos que atacan fallos *conocidos* de Amparo. Agregar una
     tercera sin un fallo identificado que la motive sería justo el "entra por
     moda" que el estándar del proyecto rechaza.
  2. **Riesgo en el dominio:** multi-query y HyDE hacen que un LLM **reescriba o
     invente** texto de consulta antes de buscar. En un asistente jurídico cuyo
     principio duro #1 es *no inventar normas*, meter texto generado en la etapa
     de recuperación agrega una superficie de alucinación nueva que habría que
     controlar. No se descarta, pero exige más cuidado del que cabe aquí.
  3. **Ya hay query transformation, por otra vía:** el tool use de S10 (sección
     16) deja que el modelo **reformule** la consulta al decidir qué buscar. Es
     multi-query implícito, pero acotado — el modelo transforma *una* consulta
     con un propósito claro, no genera N variantes especulativas.
- **Puntero:** si el diagnóstico por consulta de la Fase 2 muestra un fallo que
  solo una query transformation arregla (p. ej. consultas compuestas que piden
  decomposition), queda como el siguiente candidato natural, y esta sección se
  actualiza con esa evidencia.

## 13. Diseño de la fusión: Reciprocal Rank Fusion (RRF)

- **Decisión:** fusionar los rankings denso y léxico con RRF,
  `RRF(chunk) = Σ 1/(k + puesto)`, con `k = 60`. Código:
  [`hybrid.reciprocal_rank_fusion`](../tools/rag/hybrid.py).
- **Justificación — por qué puestos y no puntajes:** BM25 devuelve puntajes en el
  orden de ~12 y el coseno de e5 en el orden de ~0.8. **Son escalas
  incomparables**: promediarlos, sumarlos o normalizarlos con min-max mezcla dos
  unidades que no significan lo mismo, y el resultado depende más de la escala
  que de la relevancia. RRF ignora el valor del puntaje y usa solo el **puesto**
  (qué tan arriba quedó el chunk en cada lista), que sí es comparable entre
  recuperadores. Un chunk que ambos ponen arriba (consenso) le gana a uno que
  solo un recuperador ama.
- **Por qué `k = 60`:** es el valor del paper original (Cormack, Clarke &
  Buettcher, 2009) y el default de facto. Amortigua el peso de los primeros
  puestos para que ningún ranking domine la fusión por sí solo. **No se calibra**
  en M3: el aporte de RRF es la robustez a las escalas, no un `k` fino, y
  calibrarlo sin un delta que lo motive sería sobre-ingeniería.
- **Evidencia:** [`test_rrf_ignora_la_escala_de_los_puntajes`](../tests/rag/test_hybrid.py)
  multiplica por 100 los puntajes de una lista y verifica que el orden fusionado
  **no cambia** — la prueba de que RRF no está promediando escalas.

## 14. El patrón embudo y el cross-encoder elegido

- **Decisión:** patrón embudo — recuperar `RERANK_INPUT_N = 30` candidatos
  baratos (hybrid) y reordenar con el cross-encoder para quedarse con
  `RERANK_OUTPUT_K = TOP_K = 5`. Modelo:
  `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`.
- **Justificación del embudo:** el cross-encoder es caro por par, así que no se
  puede correr sobre los 3.425 chunks del corpus. El embudo paga el cross-encoder
  solo N=30 veces por consulta (no una vez por chunk), y el prompt sigue
  recibiendo TOP_K=5 chunks — el mismo tamaño de contexto que la Parte I, para
  que el delta sea atribuible al **reordenamiento** y no a un cambio en cuánto
  contexto ve el modelo.
- **Justificación del modelo:** se elige un cross-encoder **abierto y
  multilingüe** entrenado en mMARCO por el mismo motivo que e5 en el retrieval
  denso (sección 3): el caso de Amparo es consulta coloquial en español → texto
  normativo, así que el reranker tiene que entender español. Es también el modelo
  del lab de S08, lo que mantiene la trazabilidad con el material del curso.
- **Evidencia:** [`test_el_embudo_recorta_de_muchos_a_pocos`](../tests/rag/test_rerank.py)
  y [`test_el_reranker_recibe_mas_candidatos_de_los_que_devuelve`](../tests/rag/test_retrieve.py).

## 15. DECISIÓN CENTRAL — sobre qué score opera la válvula de escape

Esta es la decisión de diseño más delicada de toda la integración, porque toca la
pieza que la Parte I definió como su razón de ser: la válvula de escape.

- **El problema:** el umbral `RETRIEVAL_MIN_SCORE = 0.80` está **calibrado sobre
  el coseno de e5** (sección 5: los cosenos de e5 son poco dispersos, por eso
  0.80 y no el 0.3 típico de otros modelos). Pero en el pipeline avanzado, el
  campo `score` de cada resultado **cambia de significado**: en el sistema A es el
  coseno, tras la fusión RRF es el puntaje RRF (~0.016), y tras el reranking es el
  del cross-encoder (otra escala). Si la válvula filtrara por `score`, en B
  compararía 0.016 contra 0.80 y **descartaría todo**; en C compararía un puntaje
  de cross-encoder sin relación con 0.80. La válvula quedaría rota,
  silenciosamente.
- **Decisión:** se agregó a `SearchResult` un campo **`dense_score`** que
  preserva el coseno de e5 **a lo largo de todo el pipeline**, y
  `apply_score_floor` filtra por `dense_score`, no por `score`. Así la válvula
  sigue midiendo exactamente lo que fue calibrada para medir — la relevancia
  **semántica** del chunk — sin importar cómo se haya reordenado después. Código:
  [`retrieve.apply_score_floor`](../tools/rag/retrieve.py) y el campo en
  [`embed_store.SearchResult`](../tools/rag/embed_store.py).
- **Consecuencia deliberada — el chunk "solo BM25":** un chunk que solo trajo
  BM25 (coincidencia léxica pura, sin que e5 lo considerara relevante) tiene
  `dense_score = None` y **no pasa el piso**. Esto es correcto y buscado: el
  umbral es una afirmación sobre la relevancia *semántica*, y "este chunk comparte
  palabras pero e5 no lo ve relacionado" no es evidencia suficiente para
  fundamentar una respuesta jurídica. BM25 aporta **ordenando** candidatos que sí
  tienen respaldo semántico hacia arriba (vía RRF), no colando candidatos que el
  denso rechazó.
- **Trampa evitada (documentada en el código):** el `__post_init__` de
  `SearchResult` copia `score → dense_score` cuando este es `None`, para que el
  código de la Parte I vea el coseno sin cambios. Eso obliga a que el reranking y
  RRF asignen `dense_score` **después** de construir el objeto (no en el
  constructor), o el auto-copiado lo sobrescribiría con el puntaje del reordenador
  — justo el bug que la válvula debe evitar. Está anotado en
  [`rerank.rerank`](../tools/rag/rerank.py).
- **Evidencia:**
  [`test_sistema_C_respeta_la_valvula_de_escape_sobre_dense_score`](../tests/rag/test_retrieve.py)
  le da a un chunk solo-BM25 el puntaje de cross-encoder más alto y verifica que
  **igual no entra** al resultado, porque su `dense_score` es `None`.

## 16. Tool use (S10): retrieval-as-tool con una sola herramienta

- **Decisión:** exponer el retrieval avanzado como **una** herramienta,
  `buscar_normas`, con function calling: el modelo decide si llamarla, propone un
  JSON `{"tool": ..., "args": {...}}`, nosotros lo ejecutamos y le devolvemos los
  chunks como observación. Código: [`tools/rag/tools.py`](../tools/rag/tools.py).
- **Justificación — por qué tool y no RAG de una pasada:**
  1. **Deja que el modelo reformule la consulta** antes de buscar (query
     transformation implícita y acotada, ver sección 12.3).
  2. **Deja que el modelo decida no buscar** cuando la pregunta no lo amerita (un
     saludo, una aclaración), ahorrando una recuperación inútil. El RAG de una
     pasada busca siempre.
  3. **Conecta S08 con S10 sin superficie nueva:** la tool *es* el retrieval
     avanzado (hybrid + rerank), envuelto. No hay una segunda ruta de
     recuperación que mantener en sincronía.
- **Justificación — por qué UNA sola herramienta:** Amparo no puede *actuar*
  sobre el mundo (no radica una tutela, no paga una multa, no calcula un plazo con
  autoridad legal). Su única acción legítima es **consultar fuentes verificadas**.
  Darle una calculadora o herramientas de dominio sin un caso de uso real sería
  superficie sin justificación — el mismo estándar que rechaza agregar técnicas de
  retrieval "por moda". Una herramienta, la que corresponde al rol del producto.
- **Decisiones de robustez (patrón del lab S10):**
  - JSON malformado o sin campo `tool` → `extraer_tool_call` devuelve `None` y el
    bucle lo interpreta como "el modelo respondió directo". Un modelo pequeño a
    veces no emite JSON válido, y eso **no debe tumbar el bucle**: degrada a
    responder directo.
  - Un error de validación (tool inexistente, args faltantes) se devuelve como
    **observación** (string), no se lanza: el modelo lo lee y puede corregir en la
    siguiente vuelta.
  - La observación trae la **cita** de cada chunk, igual que el prompt aumentado
    de la Parte I: es lo que permite que el modelo cite algo que apareció de
    verdad y no de memoria.
  - `max_llamadas` acota el bucle para que un modelo que insiste en pedir la
    herramienta no corra indefinidamente.
- **Evidencia:** [`test_tools.py`](../tests/rag/test_tools.py) — 12 tests que
  cubren el parser, el dispatcher con su validación, y el bucle
  propone→ejecuta→observa→responde, todo con la generación mockeada (sin GPU).

## 17. Composición sin romper S07: el experimento A/B/C

- **Decisión:** las dos técnicas se activan por **bandera** (`use_hybrid`,
  `use_rerank`) sobre un único punto de entrada, `retrieve.retrieve`, y se
  propagan hasta `pipeline.answer_query`. Con ambas apagadas (el default de
  `config.USE_HYBRID`/`USE_RERANK`), el retrieval es **literalmente** el de la
  Parte I.
- **Justificación:** el experimento de S08 es un A/B/C controlado donde lo único
  que cambia entre sistemas es el retrieval. Si el código de A viviera en una
  función distinta del de B, un cambio accidental en una y no en la otra haría el
  delta no atribuible. Con banderas sobre el mismo camino, A **es** S07, y los
  125 tests originales del RAG lo garantizan (siguen verdes: la suite completa
  pasó de 125 a 168 tests en `tests/rag/`, +43 nuevos, 0 regresiones).
- **Trazabilidad:** cada `eval_record` lleva `used_hybrid`/`used_rerank`, así que
  las tres corridas quedan etiquetadas por sistema y el compañero de evaluación
  puede separar el desempeño de A, B y C sin ambigüedad.

| Sistema | `use_hybrid` | `use_rerank` | Retrieval |
|---|---|---|---|
| A ingenuo (S07) | False | False | denso puro (coseno e5) |
| B +hybrid | True | False | denso + BM25, fusión RRF |
| C +reranker | True | True | hybrid → cross-encoder reordena |

## 18. Dónde corre cada cosa (mismo patrón que M1/M2/S07)

- **Liviano, en `requirements.txt` y testeable en local sin GPU:** `rank_bm25`
  (Python puro). Toda la lógica pura — RRF, el parser de tool-calls, la
  orquestación A/B/C, el dispatcher — se prueba en local con el recuperador denso
  y el cross-encoder sustituidos por dobles de test.
- **Pesado, solo en Colab (import perezoso):** el cross-encoder
  (`sentence-transformers`), e5 y Qwen. En local, sin la dependencia, el reranker
  falla con un `ImportError` **explícito** que dice que corre en Colab — nunca un
  `ModuleNotFoundError` mudo.
- **Ejecución:** [`colab/rag_avanzado.ipynb`](../colab/rag_avanzado.ipynb) carga
  el índice de Drive, construye el BM25 una vez, corre la demo A/B/C sobre
  retrieval, la corrida A/B/C sobre el eval set con latencia, y la demo del tool
  use.

## 19. Hipótesis vs. medido — qué falta y quién lo cierra

| Afirmación | Estado | Dónde se cierra |
|---|---|---|
| Hybrid rescata términos exactos que e5 difumina | **hipótesis** (probada en unit test, no en el eval set real) | Fase 2 del notebook (diagnóstico por consulta) |
| Reranking limpia el ruido del top-k | **hipótesis** | Fase 2 + delta de Fase 4 |
| B > A / C > B en calidad | **sin medir** | evaluación del compañero sobre las corridas de Fase 4 |
| Latencia por sistema | **se mide en Fase 4** | ya en el notebook |
| A ≡ retrieval de S07 | **medido** | 125 tests de S07 verdes + `test_sistema_A_por_defecto_es_denso_puro` |
| La válvula de escape sobrevive a B y C | **medido** (unit test) | `test_sistema_C_respeta_la_valvula_de_escape_sobre_dense_score` |

**Lo que continúa el compañero de evaluación:** correr el harness de M2 y las
cuatro métricas de RAGAS sobre `eval_records_sistema_{A,B,C}.json`, llenar la
tabla de deltas (esqueleto en la Fase 4 del notebook) y escribir la lectura
honesta que pide la entrega M3 (qué técnica movió qué, qué costó en latencia, qué
falla queda abierta). El contrato es `pipeline.to_eval_record()`, sin cambios
respecto de S07 salvo los dos campos de trazabilidad `used_hybrid`/`used_rerank`.
