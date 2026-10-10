# Auditoria integral del estado de Amparo

Diagnostico. **No se modifico nada** salvo este archivo: ni codigo, prompts,
configuracion, datasets, corpus, notebooks, indice, manifiestos ni resultados.
No se reentreno, no se genero inferencia, no se uso GPU ni creditos, no se
reconstruyo nada, no se instalo nada y no se hizo ninguna operacion de git que
altere el estado.

---

# 1. Resumen ejecutivo

Amparo tiene **un andamiaje de evaluacion mas solido que su capacidad medida**,
y esta auditoria no encuentra ningun defecto nuevo de infraestructura: encuentra
que **las propiedades de seguridad del producto no estan demostradas** y que
**dos de las tres cosas que si estan medidas van en contra del afinado**.

| | |
|---|---|
| Lo que funciona | trazabilidad de artefactos, instrumentos de adjudicacion, puertas del dataset, cadena RAG completa y operativa |
| Lo que falla, confirmado | seguridad en urgencias (**0 de 5**), abstencion funcional B2 (**1 de 35**), rutas juridicas (regresion monotona) |
| Lo que no esta demostrado | B2 con recuperacion real; el gold del eval set esta validado en 92 de 217 filas |
| Lo que nadie habia reconciliado | **M2 se contradice consigo mismo**: su rubrica dice que el afinado es mejor y su cara a cara dice que el modelo base gana |

**No hace falta entrenar ni reconstruir el indice ahora.** Las tres cosas que
bloquean son decisiones y mediciones, no artefactos.

---

# 2. Fotografia de Git y del entorno

| | |
|---|---|
| Repositorio | `C:/Users/USUARIO/Documents/Personal Proyects/Amparo` |
| Rama activa | **`m3.5`** |
| HEAD | **`51da0dc4bd339a734e0ef58d9e74afd59d638bba`** (`51da0dc`) |
| `git status` incluidos no seguidos | **limpio** |
| Commits sin empujar | **19** respecto de `origin/m3.5` |

**El contexto mencionaba `02fa7af`: ya no es el HEAD.** `VERIFICADO` que el
HEAD actual es `51da0dc`, dos commits despues.

| rama local | estado |
|---|---|
| `m3.5` | **ahead 19** de `origin/m3.5` |
| `main` | **behind 72** de `origin/main` |
| `RAGAS` | al dia con `origin/RAGAS` |

**`main` esta 72 commits atras.** Todo el trabajo de M1, M2 y M3 vive en ramas
y nada se ha integrado. `REQUIERE_DECISIÓN`.

Referencias remotas conocidas localmente: `origin/{main, develop, RAG, RAGAS,
m3.5}`. Remoto `https://github.com/TomasPosada0626/Amparo.git`. **No se
contacto la red.**

| entorno | |
|---|---|
| Python | **3.13.5**, venv del proyecto |
| Plataforma | Windows 11, AMD64 |
| Dependencias declaradas | `requirements.txt`: openai, python-docx, pypdf, python-dotenv, sacrebleu, rouge-score, numpy, pytest, faiss-cpu, rank_bm25, scikit-learn |
| Instalado fuera de `requirements` | `torch 2.14.1+cpu`, `faiss-cpu 1.15.1`, `transformers 5.15.0` |
| `sentence-transformers` | **ausente**: bloquea medir el reranking |
| Secretos | `.env` existe y **esta en `.gitignore`**. No se abrio ni se copio nada |

**Suite:** `NO_DEMOSTRADO en este HEAD exacto`. 662 pruebas recolectadas
(`--collect-only`, coste nulo). La ultima ejecucion completa dio **658 passed,
4 skipped** con el codigo ya presente, inmediatamente antes de que `51da0dc` lo
comiteara, asi que el estado del codigo es el mismo; **no se re-ejecuto en esta
auditoria por indicacion del usuario.**

---

# 3. Mapa de arquitectura e inventario

**329 archivos versionados.**

```
consulta
   |
   v
tools/rag/enrutador.py          TF-IDF + regresion logistica, 27 categorias
   |                            USE_ENRUTADOR=True, ENRUTADOR_POOL=300
   v
tools/rag/embed_store.py        FAISS plano + e5-base, prefijos query:/passage:
tools/rag/hybrid.py             BM25 + RRF (HYBRID_TOP_N=30)
tools/rag/rerank.py             cross-encoder (USE_RERANK=False)
   |
   v
tools/rag/retrieve.py           piso 0.81, TOP_K=5
   |
   v
tools/rag/prompt_template.py    system de 1350 caracteres
   |
   v
Qwen2.5-7B-Instruct + LoRA      adaptadores v1 (produccion) y v2
   |
   v
tools/rag/verificacion.py       citas; escape_por_codigo en pipeline.py:217
   |
   v
respuesta
```

| area | archivos | responsabilidad |
|---|---|---|
| `tools/rag` | 16 | cadena RAG completa |
| `tools/evaluation` | 29 | metricas, jueces, scorecards |
| `tools` (raiz) | 27 | generadores de dataset, adjudicacion, auditoria |
| `tests` | 46 (16 rag + 24 evaluation + 6 raiz) | 662 pruebas |
| `data` | 111 | dataset, corpus, eval set, fuentes |
| `docs` | 27 | decisiones, dictamenes, informes |
| `colab` | 5 notebooks | m1_finetune, m2_evaluacion, m3_busqueda_v2, m3_s08, m3_s10 |
| `results` | 61 | 10 corridas |

## Fuentes de verdad, y las duplicidades resueltas

| artefacto | fuente de verdad | huella |
|---|---|---|
| Dataset de entrenamiento | **`data/dataset.jsonl`**, 2 709 | sha1-LF `db0b6e65126cab25` |
| Fuentes de v2 | `data/dataset_src_v2/`, 27 archivos | — |
| Corpus | `data/corpus/normas/`, 36 normas + README | `1c552822959e2932` |
| Eval set | `data/eval_set.json`, 75 casos | `a5151999c2095d00` |
| Gold de articulos | `data/eval_set_articulos.json` + `docs/m3_articulos_gold_validacion.csv` | CSV `8e9afe720a93d5bb` |
| Indice | **solo en Drive y en `Downloads/`**, no versionado | `19657d22583f93d0` |

`data/dataset_v2.jsonl` y `data/dataset_m1_v3.jsonl` **no existen**: la
consolidacion los sustituyo por `dataset.jsonl`. `data/dataset_src/` (34
archivos) es la version anterior de las fuentes y **coexiste** con
`dataset_src_v2/` (27): `CONFLICTO_DOCUMENTAL` menor, nadie documenta cual es
vigente.

## No inspeccionado, y por que

| artefacto | razon | conclusion pendiente |
|---|---|---|
| `rag_index.faiss` | binario de 36.8 MB; se calculo su huella y se cargo su cabecera, no se analizo su contenido vectorial | ninguna: su huella coincide con la declarada |
| Adaptadores LoRA v1 y v2 | **solo en Drive**, no estan en disco local | sus `hash_adaptador` constan en los manifiestos pero **no se verificaron contra el archivo** |
| `.env` | contiene secretos | ninguna; esta ignorado correctamente |
| Notebooks, ejecucion | requeriria Colab y GPU | su codigo si se inspecciono |

---

# 4. Estado por componente

## M1 — dataset, entrenamiento, evaluacion

| criterio | evidencia | estado |
|---|---|---|
| Fuentes completas | 27/27 categorias, Conciliacion prejudicial incluida | `VERIFICADO` |
| Puertas de calidad | `analizar(755)`: 0 problemas, 0 repetidos, **0 fuga del eval set**; 15 pruebas | `VERIFICADO` |
| Muestra 4010 | `revisar(4010)` -> sin problemas | `VERIFICADO` |
| Dataset combinado | 2 709 = 1 536 v1 + 755 v2 + 418 contrastivo; huella coincide con `config.DATASET_SHA1` | `VERIFICADO` |
| Notebook sin hardcode | el `1536` es una **asercion de composicion**, no un tamaño fijo; split viene del archivo | `VERIFICADO` |
| Corrida final | `results/m1_v2_2026-10-09/`: 2 375 + 334 = 2 709, hiperparametros identicos a v1 | `VERIFICADO` |
| Revision juridica de las fuentes | aprobada por Leonardo, **confirmada por Tomas**; sin documento en Git | `VERIFICADO` con **deuda de trazabilidad** |
| **B1** respuesta fundamentada | citan **54/55** (v1: 55/55) | `VERIFICADO` |
| **B3** respuesta parcial | citan **13/13** (v1: 12/13) | `VERIFICADO` |
| **B2** literal (A) | **0/35** | `FALLA_CONFIRMADA` de formato |
| **B2** funcional | **1/35**, con **15 fallos criticos** | `FALLA_CONFIRMADA` |
| B2 con recuperacion real | — | `NO_DEMOSTRADO` |
| Cita de memoria | 29/231 base -> **0/231** v1 y v2 | `VERIFICADO` |
| Entidades inventadas | 11.4 % -> **2.7 %** | `VERIFICADO` |
| Integridad de salida | 0/334; `motivo_fin = {termino: 334}` | `VERIFICADO` |
| Rutas juridicas | confirmados base **4** -> v1 **6** -> v2 **8** | `FALLA_CONFIRMADA` |
| Urgencias | **0 de 5** seguras | `FALLA_CONFIRMADA` |

### B1, B2, B3 por separado

| | que debe demostrar | datos | evidencia real | que falta |
|---|---|---|---|---|
| **B1** | responde y cita cuando el contexto alcanza | 55 de validacion, contexto del dataset | 54/55 citan su fuente | comportamiento con **recuperacion real** |
| **B2** | abstiene cuando el contexto no sirve | 35 de validacion, contexto sintetico de otras normas | A 0/35, B 35/35, **B2_funcional 1/35** | lo mismo con recuperacion real, **y** una pasada de adjudicacion para poder puntuarlo |
| **B3** | responde la parte y avisa del hueco | 13 de validacion | 13/13 citan | que el **aviso** del hueco se mida, no solo la cita |

**B pasa 35/35 y `B2_funcional` 1/35 sobre las mismas respuestas.** `B` no
acredita seguridad: deja pasar competencias institucionales afirmadas sin
respaldo. De los 15 fallos criticos, **ninguno** viene de una cita inventada.

### Seguridad y enrutamiento

**Urgencias: 0 de 5 seguras.** Y las **dos** respuestas que cumplen la
abstencion literal (9130, 9133) son **las dos que fallan mas duro**. En 9130 el
sistema abstiene y omite que retener a una persona por una deuda es ilegal.
`FALLA_CONFIRMADA`, y la metrica vieja apuntaba al lado contrario.

**Rutas:** 19 casos distintos para 20 marcas en tres modelos; **casi ningun
solapamiento**. Confirmados tras leer cada respuesta: base 4, v1 6, v2 8, con 1
falso positivo (1530, que **rechaza** la conciliacion) y 1 que requiere
revision. Es un **patron sistematico solo en v2**: 7 de 8 son el mismo error
(*demandar* ante organos de control).

## M2 — comparacion afinado contra base

| | |
|---|---|
| Adaptador | **v1**, `8ce3cc2bc9306974` (produccion) |
| Conjunto | **231** casos: la mitad **sin contexto** del split de M1, no los 334 |
| `hash_dataset` | `5139e86a34de9d24`, el de **v1 solo**, no el combinado |
| Juez | Groq `openai/gpt-oss-120b` |
| Commit | `a43bee8` |

### La contradiccion interna de M2 — nadie la habia reconciliado

El **mismo juez**, sobre los **mismos 231 casos**, dice las dos cosas:

| medicion | veredicto |
|---|---|
| **Rubrica 1-5** | afinado **mejor**: compuesto 3.47 -> **4.121** [+0.527, +0.773], correccion juridica +0.502, prudencia +0.442, error juridico 66.7 % -> 49.8 % |
| **Cara a cara** | **el base gana 106 a 73**; el afinado gana el **41 %** de los decididos [IC95 34-48], intervalo que excluye el 50 % |

`CONFLICTO_DOCUMENTAL`, y es de primer orden: el scorecard reporta las dos sin
reconciliarlas. La lectura mas plausible -- y es **inferencia, no medicion** --
es que el afinado cambio riqueza por seguridad: **224.4 palabras -> 45.8**, y la
preferencia pareada premia la respuesta mas larga mientras la rubrica premia la
prudencia. No esta demostrado.

**Y la fiabilidad del juez esta cuantificada: 19.0 % de inconsistencia** (42 de
231 pares cambian de ganador al invertir el orden). Ese mismo juez produce el
`context_recall` de todo M3.

### Lo que M2 ya media y nadie leyo

`Ruta incorrecta (%)`: base **1.7 %** -> afinado **3.0 %**, diferencia +0.013
[-0.013, +0.039], **no significativa**. La regresion de rutas **ya estaba en el
scorecard de M2** desde el 2026-10-09. Lo que faltaba no era la medicion sino
el registro por caso y la confirmacion leyendo. `PARCIAL`.

## M3 y el pipeline RAG — mapa de fallos por etapa

| etapa | estado | evidencia |
|---|---|---|
| **Cobertura del corpus** | `VERIFICADO` sano | 27/27 categorias; `CATEGORIAS_SIN_NORMA` y `FUERA_DE_ALCANCE` vacios; **0 de 155 articulos gold ausentes del indice** |
| **Vigencia** | `FALLA_CONFIRMADA`, acotada | art. 57 del CST es anterior a la reforma de 2025; afecta a 4630 y 9051 |
| **Metadatos** | `FALLA_CONFIRMADA` | `vigente = True` en **los 11 975 chunks**: no transporta informacion. `status: in_force` con `last_updated` de la **conversion** |
| **Extraccion** | `VERIFICADO` sano en lo indexado, con riesgo de entorno | los `.md` comiteados son correctos; el `pdftotext` local (Xpdf 4.06) **no los reproduce y pierde texto**. Hay guarda que detiene la conversion |
| **Fragmentacion** | `PARCIAL` | 98.8 % de chunks con un solo articulo; **1 231 articulos partidos**; **2 060 de 2 069 continuaciones sin encabezado**. Pero **24 de 38 aciertos llegan por esos chunks**: la hipotesis de que son un pasivo **queda refutada** |
| **Ingesta** | `FALLA_CONFIRMADA` | **107 chunks** cuyo contenido completo es una derogatoria; 6 sitios del top-5 en 3 de 45 casos gold. En 9058, **4 de 5 fragmentos eran "Derogado"** |
| **Enrutador** | `FALLA_CONFIRMADA` | techo alto (+5 en @5 con enrutamiento perfecto) **y daño activo**: sin enrutador hay 4 ausentes del top-100, con el de produccion **7**. Mecanismo: 300 candidatos reordenados y cortados, y las normas priorizadas aportan 2 048 chunks en 9042 |
| **Categorias sin normas** | `FALLA_CONFIRMADA` | 4 categorias gold sin entrada en el mapa: Derecho comercial, Derecho penal - denuncia, Accion de tutela, Derecho de peticion |
| **Ranking** | `FALLA_CONFIRMADA`, es la causa dominante | acierto@5 **20/45**, @30 **37/45**: **17 de 45 tienen el articulo entre los puestos 6 y 30** |
| **Representacion** | `PARCIAL`, nucleo reducido | solo **3 casos** (9010, 9038, 9048) sin causa identificada fuera del top-100 |
| **Piso de score** | `FALLA_CONFIRMADA`, latente | funcion escalon: 21/45 hasta 0.81 y **17/45 en 0.82**. Produccion esta en 0.81, **inmediatamente debajo del acantilado** |
| **Hybrid y rerank** | `CONFLICTO_DOCUMENTAL` | acierto@5 por articulo: denso 16/45, hybrid 16/45, **rerank 0.533 en otra corrida**; `context_recall` los ordena **al reves**. `USE_RERANK=False` sin medir con `sentence-transformers` |
| **Verificacion de citas** | `PARCIAL` | detecta **3 de 8** clases de defecto tras la correccion de `51da0dc`... |
| **Escape por codigo** | `IMPLEMENTADO_NO_VALIDADO` | `pipeline.py:217` cubre contexto vacio; **nunca se dispara** porque la busqueda siempre devuelve algo |

### Rutas por las que una afirmacion no respaldada llega a la respuesta final

`VERIFICADO` por sonda de funciones. De las ocho clases de defecto de cita, el
verificador detecta tres y **deja pasar cinco**:

| clase | detecta |
|---|---|
| numero de articulo inexistente en el contexto | **si** |
| articulo presente atribuido a otra norma nombrada | **si** |
| ley nombrada ausente del contexto (caso 3729) | **si**, desde `51da0dc` |
| articulo **vecino de la misma ley** (3328: atribuir al 46 lo que dice el 50) | **no** |
| cita correcta que **no respalda** la afirmacion (2917) | **no** |
| cita parcial usada para conclusion mas amplia (4128) | **no** |
| precision no textual ("la autoridad" -> "la Fiscalia", 4226) | **no** |
| **competencia institucional afirmada sin respaldo** (2229) | **no** |

La ultima es la que `B2_funcional` destapa y la que mas pesa: **15 fallos
criticos y ninguno por cita inventada.**

## Corpus, fuentes e indice

| elemento | estado | huella |
|---|---|---|
| PDF fuente | 9 archivos versionados | — |
| Corpus procesado | 36 normas + README, 9.6 MB | `1c552822959e2932` **reproducido desde los blobs de git** |
| Chunks | 11 975 | metadata `8cd72136235d6dfe` **verificada** |
| Indice | 36.8 MB, **no versionado** | `19657d22583f93d0` **verificado contra el archivo** |
| Correspondencia indice / corpus / metadata | `VERIFICADO`: las cuatro huellas coinciden con las de S08, S10 y busqueda_v2 | |

**Validez juridica del corpus:** `FUERA_DE_ALCANCE` de una auditoria tecnica,
salvo el art. 57 del CST, donde la comparacion es textual y verificable. La
aprobacion de Leonardo esta **confirmada por Tomas** y se trata como deuda
documental, no como aprobacion faltante.

## Ingenieria y pruebas

| | estado |
|---|---|
| Duplicidad `dataset_src` / `dataset_src_v2` | `CONFLICTO_DOCUMENTAL` menor: coexisten sin que nada diga cual es vigente |
| `huella_directorio` no portable | `FALLA_CONFIRMADA`: no normaliza fin de linea **y** ordena comparando `Path`, insensible a mayusculas en Windows. Dos causas independientes |
| Dos funciones de huella del dataset | `FALLA_CONFIRMADA`: sha1-LF en `config` y sha256-LF en el manifiesto. Mismo contenido, un campo ambiguo |
| El manifiesto no registra el enrutador | `FALLA_CONFIRMADA`: ni `USE_ENRUTADOR` ni `ENRUTADOR_POOL`, que es la palanca de mas impacto |
| El manifiesto declara un piso que no se aplico | `FALLA_CONFIRMADA`: `busqueda_v2` dice `min_score 0.82` y se midio con `None` |
| `rutas_incorrectas` sin registrar | `PARCIAL`: existia desde antes y no estaba en `metricas_por_registro.csv`; ya hay herramienta aparte |
| Control de fuga | `VERIFICADO`: 0 coincidencias exactas, Jaccard maximo 0.44, prueba automatica |
| Split del dataset | `FALLA_CONFIRMADA`: **0 de 103** preguntas de validacion en 2+ modos frente a 418 de 652 en train; proporciones de modo divergen hasta 26 puntos |
| Secretos | `VERIFICADO`: `.env` ignorado; claves en secretos de Colab |
| Resultados historicos | `VERIFICADO`: 10 directorios, ninguno sobrescrito |
| `main` 72 commits atras | `REQUIERE_DECISIÓN` |
| S07 sin linea base | `FALLA_CONFIRMADA`: el plan de reindexado la referencia y **no existe en `results/`** |

---

# 5. Hallazgos criticos y bloqueantes

## P0

**H01 — Urgencias: 0 de 5 seguras, y la metrica premiaba las peores.**
En 9130 una persona pregunta por su madre retenida en una clinica y el sistema
abstiene omitiendo que la retencion por deuda es ilegal. Las dos respuestas que
cumplen la abstencion literal son las dos mas inseguras. Es riesgo directo al
usuario de un producto dirigido a personas sin formacion juridica.

## P1

**H02 — B2 funcional en 1 de 35, con 15 fallos criticos.**
**H03 — `B` no acredita seguridad**: pasa 35/35 mientras `B2_funcional` pasa 1.
**H04 — M2 se contradice consigo mismo** y su juez tiene 19 % de inconsistencia.
**H05 — El enrutador entierra 3 casos** que la densa sola encontraba.
**H06 — El ranking es la causa dominante**: 17 de 45 entre los puestos 6 y 30.
**H07 — Rutas juridicas: regresion monotona** base 4 -> v1 6 -> v2 8.
**H08 — El split no mide la conducta contrastiva**: 0 de 103 en validacion.

---

# 6. Matriz maestra de hallazgos

| ID | P | Area | Hallazgo | Evidencia | Estado | Impacto | Confianza | Dependencias | Accion minima | Validacion | Coste | Riesgo de regresion |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **H01** | **P0** | M1 seguridad | 0 de 5 urgencias seguras; la abstencion literal premia las 2 peores | `tools/evaluation/seguridad_urgencias.py`; casos 9129-9133 | `FALLA_CONFIRMADA` | riesgo al usuario | **alta** | H09 | resolver la discrepancia de 9131 y fijar la metrica como criterio | las 5 contra su propio `criterio` | solo lectura + decision | ninguno |
| **H02** | P1 | M1 B2 | `B2_funcional` 1/35, 15 fallos criticos | `tools/evaluation/b2_funcional.py`; CSV B2 | `FALLA_CONFIRMADA` con contexto sintetico | el sistema afirma sin respaldo | **alta** | H03, H10 | medir con recuperacion real | corrida de 4 condiciones + adjudicacion | **GPU** | ninguno |
| **H03** | P1 | evaluacion | `B` pasa 35/35 y no acredita seguridad | mismas 35 respuestas | `VERIFICADO` | da falsa tranquilidad | **alta** | — | conservar `B` como comprobacion separada, nunca como aceptacion | ya hecho | solo lectura | ninguno |
| **H04** | P1 | M2 | la rubrica dice afinado mejor y el cara a cara dice base mejor; juez con 19 % de flip | `results/m2_2026-10-09/scorecard.md`, `groq_cara_a_cara.json` | `CONFLICTO_DOCUMENTAL` | M2 no concluye nada firme | **alta** en los datos, **baja** en la causa | — | decidir cual medicion gobierna, por escrito | criterio documentado antes de volver a medir | decision | ninguno |
| **H05** | P1 | M3 enrutador | con enrutador 7 ausentes del top-100; sin el, 4 | `results/m3_enrutador_forzado_2026-10-10/` | `FALLA_CONFIRMADA` | entierra resultados correctos | **alta** | H06 | cupo mixto o prioridad blanda en vez de reordenar y cortar | ausentes bajan de 7 a 4 **y** @5 no baja de 20/45 | CPU | **medio**: toca `retrieve.py` |
| **H06** | P1 | M3 ranking | @5 20/45 frente a @30 37/45 | `results/m3_61_2026-10-10/` | `FALLA_CONFIRMADA` | el 38 % de los aciertos se pierde por el corte | **alta** | H10 | medir `top_k` **con** fidelidad en la misma corrida | acierto sube y faithfulness no baja | **GPU** | **alto**: mas ruido en el prompt |
| **H07** | P1 | M1 rutas | confirmados base 4 -> v1 6 -> v2 8; 7 de 8 de v2 son el mismo error | `results/m1_rutas_2026-10-10/rutas_por_registro.csv` | `FALLA_CONFIRMADA` | orienta a un vehiculo procesal inexistente | **alta** por caso; **media** en la tendencia (4/6/8 sobre 334) | — | corregir las fuentes de "demandar ante organo de control" | los 7 pasan a 0 y no suben base ni v1 | solo lectura + dataset | bajo |
| **H08** | P1 | dataset | 0 de 103 preguntas de validacion en 2+ modos; train 418 de 652 | conteo sobre `dataset.jsonl` | `FALLA_CONFIRMADA` | el val loss de v2 fue ciego a lo que se corregia | **alta** | H04 | reestratificar el split por modo y pregunta base | diferencia de proporcion < 5 puntos | CPU | **alto**: invalida la comparacion v1/v2 registrada |
| **H09** | P2 | evaluacion | la discrepancia de 9131 mueve urgencias entre 0/5 y 1/5 | `seguridad_urgencias.py` frente al dictamen manual | `REQUIERE_DECISIÓN` | el numero de aceptacion depende de ello | **alta** | — | decidir si "permite modificar el acuerdo" cuenta | criterio escrito | decision | ninguno |
| **H10** | P1 | evaluacion | `B2_funcional` no se puede puntuar sola: depende de la adjudicacion | `b2_funcional.py`, tabla de automatizacion | `VERIFICADO` | la corrida de 4 condiciones no produce su numero | **alta** | — | añadir la pasada de adjudicacion al plan | plan con el paso y su responsable | decision | ninguno |
| **H11** | P2 | M3 ingesta | 107 chunks que solo dicen "Derogado"; 4 de 5 fragmentos en 9058 | regla acotada con control en cero | `FALLA_CONFIRMADA` | gasta sitios del top-5 | **alta** | reindexado | excluir al ingerir | `n_chunks` 11 975 -> 11 868 y 9058 mejora | **reindexado** | bajo |
| **H12** | P2 | M3 corpus | art. 57 del CST anterior a la reforma de 2025 | lectura del `.md`; casos 4630 y 9051 | `FALLA_CONFIRMADA` | omite un derecho vigente | **alta** en el texto; la vigencia **requiere fuente oficial** | poppler, revision juridica | incorporar el texto reformado | una consulta por licencia por citacion lo recupera | **reindexado** + revision | bajo |
| **H13** | P2 | M3 enrutador | 4 categorias gold sin normas declaradas | `enrutador.normas_de` frente al eval set | `FALLA_CONFIRMADA` | 9048 y 9049 no se pueden enrutar | **alta** | — | declararlas en `NORMAS_EN_ALCANCE` | esas categorias priorizan su norma | CPU | bajo |
| **H14** | P2 | M3 config | el piso 0.81 esta al borde: 21/45 hasta 0.81, 17/45 en 0.82 | barrido de `busqueda_v2` | `VERIFICADO` | fragilidad latente | **alta** | H06 | no subirlo sin medir; documentar el acantilado | el barrido queda en el manifiesto | solo lectura | ninguno |
| **H15** | P3 | trazabilidad | `huella_directorio` no portable por dos causas | `manifiesto.py:64`; 67ac… frente a 1c55… | `FALLA_CONFIRMADA` | verificar da falso negativo en Windows | **alta** | — | normalizar fin de linea y ordenar por nombre | la huella coincide en Windows y Linux | solo lectura | bajo: cambia el valor registrado |
| **H16** | P3 | trazabilidad | dos funciones de huella del dataset en un campo ambiguo | manifiesto `68974d…` frente a `config` `db0b6e…` | `FALLA_CONFIRMADA` | parece desajuste y no lo es | **alta** | — | registrar ambos valores con su algoritmo | el manifiesto los nombra | solo lectura | ninguno |
| **H17** | P3 | trazabilidad | el manifiesto no registra el enrutador ni el piso efectivo | seccion `retrieval` de los 3 manifiestos | `FALLA_CONFIRMADA` | la palanca de mas impacto no queda registrada | **alta** | — | añadir los campos | reconstruir la config sin leer el codigo | solo lectura | ninguno |
| **H18** | P3 | M3 | el `pdftotext` local no reproduce el corpus y pierde texto | reconversion de los 9; 24 pasajes ausentes | `FALLA_CONFIRMADA`, **mitigada** | degradaria el corpus en silencio | **alta** | — | instalar poppler-utils | `implementacion_pdftotext()` da "poppler" | instalacion | ninguno: ya hay guarda |
| **H19** | P3 | M3 | `vigente = True` en los 11 975 chunks | conteo sobre la metadata | `FALLA_CONFIRMADA` | el campo no informa | **alta** | reindexado | poblarlo o retirarlo | el art. 57 no figura `vigente: True` | **reindexado** | ninguno |
| **H20** | P3 | gold | 125 de 217 filas sin veredicto individual | CSV `8e9afe720a93d5bb` | `PARCIAL` | @10/@30/@100 provisionales | **alta** | — | cerrar con el instrumento ya generado | 0 pendientes sin justificar | revision humana | ninguno |
| **H21** | P3 | M3 | S07 sin linea base en `results/` | listado del directorio | `FALLA_CONFIRMADA` | el plan referencia algo inexistente | **alta** | — | registrarla o declararla inexistente | el plan no la referencia | solo lectura | ninguno |
| **H22** | P3 | ingenieria | `dataset_src` y `dataset_src_v2` coexisten sin declarar vigencia | listado | `CONFLICTO_DOCUMENTAL` | riesgo de editar la equivocada | media | — | documentar cual es la fuente | README que lo diga | solo lectura | ninguno |
| **H23** | P3 | proceso | `main` 72 commits atras | `git branch -vv` | `REQUIERE_DECISIÓN` | nada integrado | **alta** | todos | decidir la estrategia de integracion | — | decision | — |

## Causa raiz compartida

| causa | hallazgos |
|---|---|
| **La evaluacion no mide seguridad, mide formato** | H01, H02, H03, H09, H10 |
| **El enrutador reordena y corta sobre un pool grande** | H05, H06 parcial, H13 |
| **Los manifiestos no registran el parametro efectivo** | H15, H16, H17, H21 |
| **Chunks sin contenido util ocupan el top-k** | H11, H19 |

No estan demostradas como una sola causa; se registra la relacion.

---

# 7. Cronologia de correcciones y regresiones

| problema original | correccion | donde | evidencia | estado |
|---|---|---|---|---|
| B2 en 0/35: el modo era predecible desde la pregunta | 418 pares contrastivos | dataset, adaptador v2 | el atajo se rompe: 418 de 652 multimodo | **la correccion funciono y no resolvio el problema**: B2 sigue en 0/35 |
| Cita de memoria en el 12.6 % sin contexto | afinado v1 | `m1_2026-10-09` | 29/231 -> 0/231 | `VERIFICADO` resuelto |
| Entidades inventadas 11.4 % | afinado | — | -> 2.7 % | `VERIFICADO` resuelto |
| Corpus sin cobertura: 9 de 27 categorias | ampliacion a 36 normas | `1c552822959e2932` | 27/27, 11 975 chunks | resuelto en cobertura; **el recall global no se movio** (~0.40 -> 0.394) |
| Atribucion a ley homonima (3729) | `_numero_compatible` | `verificacion.py` | **la correccion evitaba la falsa atribucion y no levantaba bandera** | **corregido de verdad en `51da0dc`** con `normas_citadas_ausentes` |
| Enrutador leia 2 709 registros en vez de 1 536 | `load_records(origen="v1")` | `enrutador.py` | — | `VERIFICADO` resuelto |
| El conversor de PDF degradaba el corpus en silencio | guarda de implementacion | `corpus_pdf.py` | se detiene con Xpdf | `VERIFICADO` mitigado |
| Rutas incorrectas sin registrar | herramienta aparte | `m1_rutas_2026-10-10` | 18 confirmados, 1 falso positivo | **medido, no corregido** |

## Correcciones propuestas que nunca se implementaron

| | donde se propuso | estado |
|---|---|---|
| Encabezado en los chunks de continuacion | `m3_auditoria_integral.md` H9 | **refutada**: 24 de 38 aciertos llegan por esos chunks |
| Filtro de derogatorias | dictamen de clase B' | diseñado y probado, **no implementado** |
| Arreglar `huella_directorio` | H13 del integral | **no implementado** |
| Registrar el enrutador en el manifiesto | H14 del integral | **no implementado** |

## Cambios cuya eficacia nunca se midio

| | |
|---|---|
| `USE_ENRUTADOR = True` | se midio **despues**, y resulto que **entierra 3 casos** |
| `USE_RERANK = False` | **no medido**: falta `sentence-transformers` |
| El piso en 0.81 | se midio despues: **esta al borde del acantilado** |

---

# 8. Contradicciones entre documentacion, codigo y resultados

| # | fuentes que discrepan | resolucion | fuente de verdad desde ahora |
|---|---|---|---|
| 1 | **M2**: rubrica dice afinado mejor; cara a cara dice base mejor | **sin resolver**. Las dos son del mismo juez sobre los mismos 231 casos | `REQUIERE_DECISIÓN`: cual medicion gobierna |
| 2 | `m3_cobertura_corpus.md` dice "sin indice reconstruido"; los manifiestos dan 11 975 chunks | **resuelta**: el documento esta vencido | los manifiestos |
| 3 | `busqueda_v2` manifiesto dice `min_score 0.82`; el codigo usa `None` | **resuelta** leyendo `benchmark_busqueda.py:_indice` | el codigo |
| 4 | `hash_dataset_entrenamiento 68974d…` frente a `config db0b6e…` | **resuelta**: sha256-LF frente a sha1-LF, mismo contenido | ambos, nombrados |
| 5 | `hash_corpus` desde Windows `1bd16d…`/`67ac5e…` frente a `1c5528…` | **resuelta**: CRLF **y** orden de `Path` insensible a mayusculas | el calculo desde blobs de git |
| 6 | "la abstencion no funciona, 0/35" frente a "20/30 adversariales" | **resuelta**: conjuntos distintos; abstiene cuando la **pregunta** lo señala, no cuando el **contexto** no sirve. Mismo adaptador y mismo prompt | las dos, con su alcance |
| 7 | `context_recall` ordena hybrid/rerank al reves que el acierto por articulo | **sin resolver**: distinto piso, distinto top_k y uno pasa por un juez con 19 % de flip | `REQUIERE_DECISIÓN` |
| 8 | Urgencias: dictamen manual 1/5, metrica 0/5 | **sin resolver**: solo 9131 | `REQUIERE_DECISIÓN` (H09) |
| 9 | "142 chunks de derogatoria" frente a 107 | **resuelta**: la heuristica laxa incluia articulos sustantivos y mezclaba gold con adversariales | la regla acotada, 107 |
| 10 | "las 128 filas no mueven el acierto@k" | **corregida**: cierto para @5, **falso** para @10 y mas alla | el analisis por clase |

### Clasificacion de la evidencia

| tipo | ejemplos |
|---|---|
| **Hechos del repositorio actual** | huellas, conteos, puertas del dataset, 662 pruebas, composicion del dataset |
| **Resultados de experimentos anteriores** | M1 v1/v2, M2, S08, S10, busqueda_v2, 6.1, matriz, enrutador forzado |
| **Afirmaciones historicas de informes** | "sin indice reconstruido", "142 chunks", "el piso casi no discrimina" -- **las tres superadas** |
| **Inferencias no verificadas** | que el afinado cambio riqueza por seguridad; que el enrutador contiene los codigos grandes |
| **Decisiones de producto pendientes** | H04, H09, H10, el umbral de B2, adoptar o no v2, integrar `main` |
| **Requiere revision juridica profesional** | vigencia norma por norma; los 5 errores de atribucion de B2; el etiquetado gold de 125 filas |

---

# 9. Lo que SI esta terminado y demostrado

| | evidencia |
|---|---|
| Trazabilidad de los cuatro artefactos de M3 | indice, metadata, corpus y eval set **verificados contra los archivos** |
| Cobertura del corpus | 27/27; **0 de 155 articulos gold ausentes del indice** |
| Puertas del dataset | 0 problemas, 0 repetidos, **0 fuga**; 15 pruebas |
| Ausencia de fuga train/eval | 0 exactas, Jaccard maximo 0.44 |
| El notebook entrena con el dataset correcto | asercion de composicion; 2 375 + 334 = 2 709 |
| Eliminacion de la cita de memoria | 29/231 -> **0/231** |
| Entidades inventadas | 11.4 % -> **2.7 %** |
| Integridad de salida y truncamiento | 0/334; `motivo_fin = {termino: 334}` |
| B1 y B3 citan su fuente | 54/55 y 13/13 |
| Prefijos de e5 | correctos; **hipotesis descartada** |
| Sin sobre-abstencion | **0 de 68** en B1 y B3 |
| El ranking es la causa dominante | 34 de 45 en el top-10 de alguna configuracion |
| La guarda del conversor de PDF | se detiene con el extractor equivocado |

---

# 10. Implementado pero no demostrado

| | por que |
|---|---|
| `escape_por_codigo` para contexto vacio | **nunca se dispara**: la busqueda siempre devuelve algo |
| `USE_RERANK = False` | falta `sentence-transformers` |
| El enrutador como mejora neta | **da +4 en @5 y entierra 3 casos**: el neto no esta establecido |
| Los 418 pares contrastivos | rompieron el atajo y **no produjeron la conducta**; y el split no los mide |
| `normas_citadas_ausentes` | 1 hallazgo en 668 respuestas, 0 falsos positivos; **no ejercitada en produccion** |
| El filtro de derogatorias | probado en simulacion, **no implementado** |
| B3 avisa del hueco | se mide que **cita**, no que **avise** |

---

# 11. Lo que sigue fallando

| | |
|---|---|
| **Urgencias** | 0 de 5 seguras |
| **B2 funcional** | 1 de 35, 15 fallos criticos |
| **Rutas** | base 4 -> v1 6 -> v2 8 confirmados |
| **Enrutador** | entierra 3 casos; 4 categorias gold sin normas |
| **Ranking** | 17 de 45 entre los puestos 6 y 30 |
| **Derogatorias** | 107 chunks ocupando el top-5 |
| **Art. 57 del CST** | version anterior a 2025 |
| **Split** | 0 de 103 en validacion multimodo |
| **M2** | se contradice y su juez tiene 19 % de flip |
| **Trazabilidad** | `huella_directorio`, doble huella, enrutador sin registrar, S07 sin linea base |

---

# 12. Lo que no puede determinarse

| | que falta |
|---|---|
| Si el afinado es mejor que el base | H04 sin resolver |
| Si B2 falla con recuperacion real | corrida de 4 condiciones + adjudicacion (**GPU**) |
| Si subir `top_k` mejora el producto | acierto y fidelidad en la misma corrida (**GPU**) |
| Si el rerank ayuda | falta `sentence-transformers` |
| Por que 9010, 9038 y 9048 no aparecen en el top-100 | sin mecanismo |
| Por que Pensiones empeoro al ampliar el corpus | hecho medido, causa no |
| Si `multilingual-e5-base` alcanza | no medido contra otro modelo |
| Vigencia del corpus salvo el art. 57 | requiere fuente oficial |
| Los adaptadores en disco | **solo estan en Drive**: su huella no se verifico contra el archivo |
| Si la particion separa un articulo de sus paragrafos | no medido; lo medido es la perdida del encabezado |

---

# 13. Plan unico de estabilizacion

Finito: **cuatro fases y una sola reconstruccion**, condicionada.

## Fase 0 — decisiones antes de tocar codigo (coste cero)

| # | decision | resuelve |
|---|---|---|
| 0.1 | Cual medicion de M2 gobierna: rubrica o cara a cara | H04 |
| 0.2 | La discrepancia de 9131 | H09, H01 |
| 0.3 | El umbral de B2: aceptacion 30/35 + cero criticos, y lectura calibrada sobre 1/35 | H02, H10 |
| 0.4 | Añadir la pasada de adjudicacion al plan de la corrida | H10 |
| 0.5 | Si se adopta v2. **La evidencia dice no**: 20 fallos criticos frente a 15 y 8 rutas frente a 6 | H07 |
| 0.6 | Estrategia de integracion de `main` | H23 |

**Nada de lo que sigue tiene sentido sin 0.1 a 0.4.**

## Fase 1 — correcciones sin GPU ni reindexado

| # | correccion | resuelve | prueba de aceptacion | regresion |
|---|---|---|---|---|
| 1.1 | `huella_directorio`: normalizar fin de linea y ordenar por nombre | H15 | coincide en Windows y Linux | publicar la equivalencia |
| 1.2 | Doble huella nombrada en el manifiesto | H16 | el manifiesto nombra los algoritmos | ninguna |
| 1.3 | Registrar `USE_ENRUTADOR`, `ENRUTADOR_POOL` y el piso efectivo | H17 | reconstruir la config sin leer el codigo | ninguna |
| 1.4 | Declarar las normas de las 4 categorias gold | H13 | esas categorias priorizan su norma; las 27 no empeoran | baja |
| 1.5 | `rutas_incorrectas` en las metricas por registro | H07 parcial | la proxima regresion se ve sola | ninguna |
| 1.6 | Corregir las fuentes de "demandar ante organo de control" | H07 | los 7 pasan a 0 | baja |
| 1.7 | Registrar o declarar inexistente la linea base de S07 | H21 | el plan no referencia lo que no existe | ninguna |
| 1.8 | Documentar la vigencia de `dataset_src` frente a `dataset_src_v2` | H22 | README que lo diga | ninguna |
| 1.9 | Instalar poppler-utils | H18 | `implementacion_pdftotext()` da "poppler" | ninguna |

**Todas juntas: son independientes y ninguna toca el indice.**

## Fase 2 — enrutador y ranking, CPU

| # | intervencion | hipotesis | condicion de exito |
|---|---|---|---|
| 2.1 | Cupo mixto o prioridad blanda en `retrieve.py` | el daño viene del corte, no de la prediccion | ausentes del top-100 bajan de **7 a 4** **y** @5 no baja de 20/45 |
| 2.2 | Cerrar las 125 filas del gold | los @10/@30 son provisionales | 0 pendientes sin justificar |
| 2.3 | Instalar `sentence-transformers` y medir el rerank | el acierto por articulo lo favorece | @5 sube con el gold aprobado y el mismo piso |

**Congelado durante la fase 2:** el indice `19657d22583f93d0`, el corpus, el
eval set y los 10 directorios de resultados.

## Fase 3 — la corrida con GPU, una sola, con autorizacion

| # | corrida | justificacion | condicion de exito |
|---|---|---|---|
| 3.1 | Las 4 condiciones por el pipeline real, adaptador v1 | es la unica evidencia que falta para B2 | **aceptacion**: `B2_funcional` >= 30/35 y 0 criticos. **Lectura**: > 1/35 y < 15 criticos |
| 3.2 | `top_k` 5 contra 30 **con fidelidad** | el acierto casi se duplica y el coste no esta medido | acierto sube **y** faithfulness no baja |
| 3.3 | Urgencias con la metrica de seguridad | H01 es P0 | las 5 contra su propio criterio |

**Las tres en la misma sesion de GPU**, mismo adaptador y mismo indice, para no
pagar la carga tres veces.

## Fase 4 — la unica reconstruccion, solo si la fase 3 lo confirma

| # | entra | condicion |
|---|---|---|
| 4.1 | Filtro de derogatorias puras (H11) | **siempre**: riesgo bajo, control en cero |
| 4.2 | `vigente` poblado o retirado (H19) | siempre |
| 4.3 | Art. 57 del CST (H12) | **solo** con fuente oficial verificada y validacion profesional |
| 4.4 | Front matter: fecha de conversion frente a version | siempre |
| 4.5 | Encabezado en continuaciones | **solo si** 3.1 o 3.2 lo justifican. **Hoy la evidencia esta en contra** |

Despues: recorrer S08 y S10 -- y S07 si se registra su linea base -- y publicar
la tabla de equivalencia de huellas.

**Lo que NO entra:** reentrenar. Ninguna fase lo exige, y H08 dice que antes
habria que reestratificar el split, lo que invalidaria la comparacion v1/v2
registrada.

---

# 14. Criterios objetivos de cierre

## M1

| criterio | umbral | estado |
|---|---|---|
| Dataset y puertas | 0 problemas, 0 fuga | **cumplido** |
| B1 | citan >= 50/55 | **cumplido** (54/55) |
| B3 | citan >= 11/13 **y** avisan del hueco | citan cumplido; **avisar no medido** |
| B2 funcional | >= 30/35 **y** 0 fallos criticos | **1/35 con 15**; pendiente de 3.1 |
| Urgencias | 5/5 por su propio criterio | **0/5** |
| Rutas | confirmados <= los del modelo base | **8 frente a 4** |
| Sin cita de memoria | 0/231 | **cumplido** |
| Reproducibilidad | manifiesto con huellas nombradas | parcial, pendiente de 1.2 y 1.3 |

## M2

| criterio | estado |
|---|---|
| Una medicion que gobierne, documentada | **pendiente**: H04 |
| Juez con flip < 10 % | **19 %**: no cumplido |
| Cobertura de los 334, no solo 231 | no cumplido |

## M3

| criterio | umbral | estado |
|---|---|---|
| Cobertura | 27/27 | **cumplido** |
| Gold validado | 217/217 | **92/217** |
| Acierto@5 por articulo | > 20/45 | linea base, pendiente de la fase 2 |
| Ausentes del top-100 | <= 4 | **7**: pendiente de 2.1 |
| Chunks sin contenido util | 0 | **107**: pendiente de 4.1 |
| Vigencia | sin norma vencida conocida | **art. 57**: pendiente de 4.3 |

## Proyecto

Cierra cuando: **M1 con urgencias en 5/5 y B2 funcional demostrado**, M2 con una
medicion que gobierne, M3 con el gold cerrado y el acierto medido tras la fase
2, y la trazabilidad con huellas nombradas y portables.

---

# 15. Registro de alcance

## Revisado

Estado de git y ramas; 329 archivos versionados por area; `tools/rag` (16),
`tools/evaluation` (29), `tools` (27); los 5 notebooks por su codigo; 27
documentos; 10 directorios de resultados con sus manifiestos; `data/` incluidos
dataset, corpus, eval set y fuentes; `requirements.txt` y el entorno instalado.

## Comprobaciones ejecutadas, todas de solo lectura

Huellas de corpus, dataset, metadata, indice, eval set y CSV del gold;
reproduccion del `hash_corpus` desde blobs de git; composicion del dataset por
origen, modo y split; recuento de multimodo en train y validacion; `b2_funcional`
sobre v1 y v2; contraste de A, B y `B2_funcional`; `seguridad_urgencias` sobre
los 5 casos; `rutas_incorrectas` sobre las 3 corridas con revision por caso;
lectura de `groq_cara_a_cara.json` y del scorecard de M2; recoleccion de 662
pruebas.

## Deliberadamente no ejecutado

| | razon |
|---|---|
| La suite completa en este HEAD | **el usuario lo rechazo**. Se corrio con el mismo codigo antes de `51da0dc`: 658 passed, 4 skipped |
| Inferencia, generacion, entrenamiento | prohibido y costoso |
| Busquedas experimentales, reranking, reindexado | prohibido |
| Instalar `sentence-transformers` | prohibido |
| Abrir `.env` | secretos |
| Verificar los adaptadores contra el archivo | **no estan en disco local** |

## Limitaciones

1. La suite no se re-ejecuto en este HEAD exacto.
2. Los adaptadores no se verificaron contra su archivo.
3. La validez juridica del corpus esta fuera del alcance tecnico salvo el
   art. 57, donde la comparacion es textual.
4. El contenido vectorial del indice no se analizo: solo su huella y su
   cabecera.
5. Los resultados historicos corresponden a versiones distintas y **no se
   presentan como mediciones actuales**.

---

# Respuestas a las ocho preguntas

**1. ¿En que estado real esta Amparo?** Infraestructura y trazabilidad
**solidas**; capacidad de producto **no demostrada**. Las tres propiedades de
seguridad que se midieron fallan: urgencias 0/5, B2 funcional 1/35, rutas en
regresion. Nada esta roto en el sentido de corrupcion; lo que falta es
demostrar que el sistema es seguro.

**2. ¿Que impide avanzar?** Cuatro decisiones, no cuatro arreglos: cual
medicion de M2 gobierna (H04), la discrepancia de 9131 (H09), el umbral de B2
(H02) y si la corrida puede puntuarse sin la pasada de adjudicacion (H10).
**Ninguna cuesta GPU.**

**3. ¿Que no hay que volver a tocar?** La cobertura del corpus; las puertas del
dataset; el control de fuga; la eliminacion de la cita de memoria; los prefijos
de e5; la ausencia de sobre-abstencion; la trazabilidad de los cuatro
artefactos; la guarda del conversor de PDF. Y **no volver a pedir la revision
juridica ya aprobada**: es deuda documental.

**4. ¿Hallazgos de una misma causa?** Cuatro grupos: la evaluacion mide formato
y no seguridad (H01, H02, H03, H09, H10); el enrutador reordena y corta sobre un
pool grande (H05, H06, H13); los manifiestos no registran el parametro efectivo
(H15, H16, H17, H21); chunks sin contenido util en el top-k (H11, H19).

**5. ¿Que corregir primero?** La **fase 0**, por una razon concreta: con la
metrica actual, entrenar o reindexar optimiza hacia el lado equivocado --
`es_abstencion_pura` premia la respuesta de 9130, que es la mas insegura del
conjunto.

**6. ¿Que no modificar sin evidencia?** El encabezado de las continuaciones: la
evidencia esta **en contra** (24 de 38 aciertos llegan por esos chunks). El
piso 0.81: esta al borde del acantilado. `USE_RERANK`: sin medir. El split: lo
invalidaria la comparacion v1/v2. Y el corpus, salvo el art. 57.

**7. ¿Hace falta entrenar, reindexar o gastar GPU ahora?** **No.** Entrenar:
no, el fallo de B2 no esta caracterizado y H08 dice que antes habria que
reestratificar el split. Reindexar: no, las dos correcciones que lo necesitan
(H11, H19) son P2 y deben ir juntas con lo que la fase 3 confirme. GPU: **si,
pero despues de la fase 0** -- las tres corridas en una sola sesion, con los
umbrales congelados por escrito.

**8. ¿La secuencia mas corta y segura?**

```
Fase 0  decisiones (0 GPU)              -> desbloquea todo
Fase 1  9 correcciones de trazabilidad  -> juntas, sin GPU ni indice
Fase 2  enrutador + gold + rerank (CPU) -> mide sin tocar el indice
Fase 3  UNA sesion de GPU, 3 corridas   -> con autorizacion y umbrales fijados
Fase 4  UNA reconstruccion, condicionada
```

Cuatro fases, una sesion de GPU, una reconstruccion. **No mas rondas de
auditoria**: lo que falta son decisiones y tres mediciones.
