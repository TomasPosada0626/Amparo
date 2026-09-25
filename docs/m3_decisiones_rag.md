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

## 9. Consultas fallidas anotadas

Registro de consultas donde el retrieval no trae el chunk correcto, con su
diagnóstico por etapa. Es el insumo empírico que respalda las decisiones de la
Parte II y el material de trabajo para afinar el pipeline.

| Consulta | Síntoma | Etapa responsable (ingest/chunk/embed/retrieve/generate) | Técnica que lo corrige |
|---|---|---|---|
| | | | |

## 10. Alcance de cada parte

**Parte I — RAG ingenuo (S07):** las 7 etapas, el corpus ingerido, el prompt
aumentado con válvula de escape y el notebook que lo corre. La salida se emite en
formato Ragas (`question` / `answer` / `contexts` / `ground_truth`) con la
evidencia de retrieval por consulta.

**Parte II — RAG avanzado (S08) + tool use (S10):** hybrid search, reranking y el
retrieval expuesto como herramienta. Código en `tools/rag/{hybrid,rerank,tools}.py`,
integrado por bandera en `retrieve.py` / `pipeline.py`; ejecución en
[`colab/rag_avanzado.ipynb`](../colab/rag_avanzado.ipynb).

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

El umbral `RETRIEVAL_MIN_SCORE = 0.80` está calibrado sobre el coseno de e5
(sección 5). En el pipeline avanzado, el campo `score` de cada resultado cambia de
significado: en el sistema denso es el coseno, tras la fusión RRF es el puntaje RRF
(~0.016) y tras el reranking es el del cross-encoder. Filtrar por `score`
descartaría todo en hybrid y compararía un puntaje sin relación con 0.80 en
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
superficie injustificada.

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
- **Ejecución:** [`colab/rag_avanzado.ipynb`](../colab/rag_avanzado.ipynb) carga
  el índice desde Drive, construye el BM25 una vez, corre la comparación A/B/C
  sobre retrieval, la corrida A/B/C sobre el eval set con su latencia, y la demo
  del tool use.
