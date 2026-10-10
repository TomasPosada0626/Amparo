# Auditoria integral de Amparo

**Solo lectura.** No se modifico codigo, corpus, metadata, indice, datasets,
notebooks, resultados, CSV ni configuracion. No se ejecuto Colab ni GPU, no se
entreno, no se reconstruyo el indice y no se hizo commit ni push. El unico
archivo nuevo es este informe.

Estado de partida verificado: rama **`m3.5`**, HEAD **`1e75060`**, arbol
**limpio**, **8 commits locales sin empujar** a `origin/m3.5`.

---

## La respuesta

**Amparo es hoy un sistema con el andamiaje de evaluacion mas solido que su
capacidad real.** La trazabilidad funciona, los instrumentos de adjudicacion
funcionan, y gracias a eso sabemos con precision que tres cosas no funcionan.

### Los tres problemas que mas limitan su fiabilidad

**1. La referencia contra la que medimos esta parcialmente mal, y solo 1 de sus
4 clases esta validada.**

De las 27 etiquetas gold de clase A, **4 eran aciertos falsos** (aprobado por
Leonardo Galeano el 2026-10-10). Depurarlas baja el acierto@5 por articulo de
**21/45 (47 %) a 17/45 (38 %)**. Quedan **190 de 217 filas en `pendiente`**,
entre ellas los 62 candidatos a omision que podrian empujar en la direccion
contraria. Mientras eso siga abierto, **ninguna medicion de recuperacion es
concluyente**, y por tanto ninguna decision de reindexado es defendible.

**2. La abstencion no funciona, ni antes ni despues del reentrenamiento.**

Medido ahora sobre las respuestas guardadas de los 35 casos B2, con
`es_abstencion_pura`:

| | abstenciones puras |
|---|---|
| v1 (adaptador de produccion) | **0 / 35** |
| v2 (con pares contrastivos) | **0 / 35** |

Y en esos mismos 35 casos la adjudicacion dice `pertinencia_contexto`
**insuficiente en 27 de 35**. El sistema nunca dice "no puedo responder con
esto" cuando el contexto no alcanza. Para un asistente juridico dirigido a
personas sin formacion juridica, esa es la conducta de seguridad central, y los
pares contrastivos no la arreglaron.

**3. La recuperacion acierta la norma pero no el articulo.**

Acierto@5 del **87 % por norma** frente al **47 % por articulo** (38 % con el
gold depurado). Hay un mecanismo diagnosticado para parte de ello -- 2 060
chunks de continuacion sin encabezado -- pero explica 22 de 53 fallos. Los
otros 29 son articulos que estan en su propio chunk, con encabezado, y aun asi
no se recuperan: **sin mecanismo identificado**.

---

## 1. Resumen ejecutivo

### Lo que si es fiable

| Componente | Evidencia |
|---|---|
| Trazabilidad de artefactos | `hash_corpus` de S08/S10 (`1c552822959e2932`) se reproduce exacto desde los blobs de git en ambos commits y en HEAD. `hash_metadata_indice` (`8cd72136235d6dfe`) verificado contra la copia local. S08 y S10 comparten `hash_indice` y `n_chunks`: midieron sobre lo mismo. |
| Huella del dataset | `db0b6e65126cab25`, calculada = esperada. |
| Cobertura normativa | 27/27 categorias objetivo. `CATEGORIAS_SIN_NORMA` vacio, `FUERA_DE_ALCANCE` vacio, `NORMAS_PENDIENTES` con 2 entradas (una sin categoria asignada). |
| Integridad de extraccion en lo indexado | De los 155 articulos gold, **0 ausentes del indice**. 11 835 de 11 975 chunks (98.8 %) con exactamente un articulo; 0 chunks sin articulo identificado. |
| Prefijos de e5 | `embed_store.py:150-185` aplica prefijo, mean pooling enmascarado y L2; se expone solo via `embed_query`/`embed_passages`. No hay ruta que embeba sin prefijo. |
| Ausencia de fuga lexica train/eval | 75 casos del eval set contra 2 709 registros: **0 coincidencias exactas**, Jaccard maximo 0.44, mediana 0.27, ninguno sobre 0.45. |
| Instrumentos de adjudicacion | B2 cerrado con diff verificado celda por celda; validadores que rechazan escribir si se toca una columna no autorizada. |

### Lo que esta demostradamente roto

Abstencion (0/35), calidad del gold (4 aciertos falsos confirmados),
recuperacion a nivel de articulo (38-47 %), una laguna del verificador de citas
(abajo), y la vigencia del articulo 57 del CST.

### Tres conclusiones anteriores que esta auditoria deja sin efecto

El encargo pide señalarlas explicitamente. Las tres son mias.

**a) "El verificador cubre las leyes homonimas por numero y por eso detecta el
caso 3729."** **Falso**, y lo afirme en el informe de auditoria anterior y en un
mensaje de commit. Probado ahora: con el contexto trayendo la Ley 2220 y la
respuesta citando *"el articulo 5 de la Ley 2222 de 2022"*,
`citas_no_respaldadas` devuelve `[]`, `citas_mal_atribuidas` devuelve `[]`,
`citas_no_verificables` devuelve `[]` y `es_prudente` devuelve `True`. **La cita
pasa todos los controles mecanicos.**

Lo que la correccion hizo -- y lo que su prueba asserta, literalmente
`[("", "5")]` -- es **impedir que la cita se resuelva falsamente** a la Ley
2220. Eso evita un falso positivo de atribucion correcta; **no levanta ninguna
bandera**. La señal existe (`citas_atribuidas` devuelve atribucion vacia) y
**ningun llamador la usa**.

**b) "Las normas grandes concentran la recuperacion."** **No sustentado, y
probablemente al revés.** El Codigo Civil y el de Comercio son el **33 % del
indice** (2 047 + 1 901 de 11 975 chunks) y aparecen en el **13.5 %** de las
recuperaciones. Estan **sub**-representados respecto de su tamaño, no
sobre-representados. La hipotesis del distractor por volumen queda descartada en
esta forma.

**c) "53 observaciones de articulo."** Era el numero de **fallos**, no el total
de etiquetas. Son **155** observaciones en 75 pares (caso, norma), mas 62
candidatos a omision: **217 filas**.

---

## 2. Mapa de componentes y dependencias

```
                    data/corpus/pdf (9)         espejo SUIN (27 normas)
                            |                            |
                      corpus_pdf.py  <-- requiere poppler-utils
                            |                            |
                    data/corpus/normas/*.md  (36 normas + README, 9.6 MB)
                            |                 hash_corpus 1c552822959e2932
                            v
                       chunk.py  (MAX_TOKENS_PER_CHUNK = 350)
                            |
             +--------------+--------------+
             |                             |
   rag_index.faiss (48 MB, Drive)   rag_index_metadata.jsonl (12 MB)
   hash_indice 19657d22583f93d0     hash_metadata 8cd72136235d6dfe
             |                             |     11 975 chunks
             +--------------+--------------+
                            v
   pregunta -> enrutador (TF-IDF+LR, USE_ENRUTADOR=True) -> candidatos (pool 300)
            -> denso e5-base / BM25+RRF / rerank -> piso 0.81 -> TOP_K=5
            -> prompt_template -> Qwen2.5-7B + adaptador LoRA
            -> verificacion.py
                            |
                            v
        S08 / S10  <--- eval_set.json (75) + eval_set_articulos.json (45 gold)
                                                  hash_eval_set a5151999c2095d00
```

**Dependencias que importan para el orden del trabajo:**

1. `eval_set_articulos.json` **gobierna** toda conclusion sobre recuperacion. Es
   la raiz del grafo de decision, y esta validada en 27 de 217 filas.
2. Cualquier cambio en `normas/*.md` o en `chunk.py` invalida `hash_indice` y
   obliga a recorrer S07, S08 y S10. **Hay una sola reconstruccion que gastar.**
3. El dataset y el adaptador son independientes del corpus: la abstencion se
   puede trabajar **sin** tocar el indice. Es la unica rama paralelizable.
4. `verificacion.py` no depende de nada mas: su laguna se corrige aislada.

---

## 3. Matriz consolidada de hallazgos

| id | componente | defecto | evidencia exacta | artefactos | casos | impacto | confianza | causa raiz probable | dependencias | correccion candidata | riesgo de regresion | prueba de aceptacion |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **H1** | Gold / evaluacion | 4 etiquetas gold eran aciertos falsos; 190 de 217 filas sin validar | `docs/m3_articulos_gold_validacion.csv`; dictamen clase A aprobado 2026-10-10 | eval_set_articulos.json | 9040, 9051, 9064, 9069 | **alto**: acierto@5 47 %->38 % | **alta** (clase A validada por abogado) | etiquetado por similitud tematica, no por si el articulo resuelve la consulta | ninguna | adjudicar clase B' (62), luego B (82) y C (46) | ninguno: no se toca el sistema | las 217 filas sin `pendiente`, o las pendientes justificadas |
| **H2** | Dataset / modelo | 0 de 35 abstenciones puras, en v1 y en v2, con contexto insuficiente en 27 de 35 | `es_abstencion_pura` sobre `tools.adjudicacion_b2.respuestas()`; CSV B2 | adaptadores v1 y v3, dataset.jsonl | los 35 B2 | **alto**: es la conducta de seguridad del producto | **alta** (medido) | ver H3 y H4 | H3, H4 | rediseñar los ejemplos B2, no solo añadir mas | requiere entrenamiento: GPU | abstenciones puras > 0 en los casos de pertinencia insuficiente |
| **H3** | Dataset | Validacion sin una sola pregunta multimodo: el atajo que los contrastivos corrigen **no se mide** | 418 de 652 preguntas de train en 2+ modos; **0 de 103** en val | dataset.jsonl | todo el entrenamiento de v2 | **alto**: el val loss de v2 fue ciego a lo que se corregia | **alta** (medido) | los 418 contrastivos se asignaron todos a `train` | ninguna | reparticion con contrastivos en val | cambia el split: hay que rehacer la comparacion v1/v2 | val contiene preguntas multimodo en proporcion a train |
| **H4** | Dataset | Proporciones de modo muy distintas entre train y val | train B1 31 % / B2 60 % / B3 8 %; val B1 53 % / B2 34 % / B3 13 % | dataset.jsonl | idem | medio-alto | **alta** (medido) | los contrastivos (todos B2, todos train) desbalancearon train sin tocar val | H3 | estratificar el split por modo | idem H3 | diferencia de proporcion por modo < 5 puntos |
| **H5** | Citas | Una cita que nombra una ley ausente del contexto, con numero de articulo coincidente, **pasa todos los controles** | sonda sobre `verificacion.py`: las cuatro funciones devuelven vacio / `True` para el caso 3729 | verificacion.py | 3729, y cualquier caso analogo | **alto**: es un error de fundamentacion invisible | **alta** (medido) | `citas_atribuidas` devuelve atribucion vacia y ningun llamador la usa como señal | ninguna | tratar la atribucion sin resolver como cita no verificable | bajo; puede subir falsos positivos con normas nombradas de forma informal | el caso 3729 se detecta, y las 12 pruebas existentes siguen pasando |
| **H6** | Corpus / vigencia | El art. 57 del CST indexado es anterior a la reforma de 2025 | lectura del `.md`: licencias para sufragio, cargos oficiales, grave calamidad, comisiones sindicales, entierro; 0 menciones a citacion / comisaria / violencia / judicial | normas/codigo_sustantivo_trabajo_decreto_2663_1950.md | 4630 y, por frecuencia, Despido y Relaciones laborales | **alto** | **alta** | el espejo compila hasta 2021 y solo anota la Ley 2466 en los arts. 3 y 4 | poppler-utils; contraste con fuente oficial | incorporar el texto reformado | mueve `hash_corpus` e `hash_indice` | una consulta por licencia por citacion judicial recupera el art. 57 reformado |
| **H7** | Corpus / metadatos | `vigente` es `True` en **los 11 975 chunks**: no transporta informacion | conteo sobre la metadata del indice | metadata del indice, chunk.py | transversal | medio | **alta** (medido) | el campo se escribe por defecto | H6 | poblarlo, o retirarlo para no sugerir una garantia que no da | ninguno si solo es metadata | el art. 57 preexistente no figura como `vigente: True` |
| **H8** | Corpus / metadatos | `status: in_force` y `last_updated` presentan la fecha de **conversion** como si fuera de vigencia | front matter del CST: `status: "in_force"`, `last_updated: "2026-10-08"` | normas/*.md | transversal | medio | **alta** | el conversor escribe la fecha de ejecucion | ninguna | separar fecha de conversion de version del texto | ninguno funcional; mueve `hash_corpus` | el front matter declara la version, no solo cuando se convirtio |
| **H9** | Indice / chunking | 2 060 de 2 069 chunks de continuacion no conservan el encabezado "Articulo N" | metadata del indice | chunk.py, indice | 22 de 53 fallos de articulo | **alto** | **media-alta** en el mecanismo; magnitud no medida | el chunker parte por presupuesto de tokens sin reinyectar el encabezado | 6.1; H1 | anteponer el encabezado al chunk de continuacion | cambia 2 069 chunks; texto repetido puede crear nuevos distractores | acierto@5 por articulo sube sobre la linea base depurada, sin bajar las categorias en 0.83+ |
| **H10** | Indice / ranking | 29 de 53 fallos de articulo son articulos en su propio chunk, con encabezado | cruce metadata x registros S08 | indice, retrieve.py | 29 observaciones | **alto** | **alta** en el hecho; **ninguna** en la causa | sin determinar | **6.1** | ninguna todavia: medir primero | — | 6.1 separa "fuera del top-100" de "dentro y mal ordenado" |
| **H11** | Recuperacion | La distribucion de score es una banda de 0.07 y el piso de 0.81 casi no discrimina | 370 chunks: min 0.810, p25 0.827, mediana 0.833, max 0.880; 90 % bajo 0.85 | S08 config A | transversal | medio-alto | **alta** (medido) | e5-base sobre consulta coloquial vs texto normativo | H1, 6.1 | evaluar margen relativo en vez de piso absoluto | subir el piso deja casos sin contexto (ya pasa en 1 de 45) | n de casos sin contexto y recall, medidos a la vez |
| **H12** | Recuperacion | Hybrid y rerank **bajan** el recall | A 0.394 / B 0.381 / C 0.352 | ragas_resumen_abc.json | transversal | bajo (ya se actua bien) | **alta** (medido) | candidatos pobres: reordenar no crea señal | — | mantener A denso y `USE_RERANK=False` | ninguno | el que cambie debe subir recall, no solo precision |
| **H13** | Trazabilidad | `huella_directorio` no normaliza fin de linea e incluye `README.md` | `manifiesto.py:64`; desde Windows da `1bd16dcc1baccc6b` frente al registrado | manifiesto.py | verificacion de cualquier corrida | medio | **alta** (medido, me ocurrio) | se copio el patron sin la correccion que si tiene `huella_dataset` | ninguna | normalizar y excluir el README | cambia el valor registrado: hay que publicar la equivalencia | el hash coincide en Windows y en Colab para el mismo contenido |
| **H14** | Trazabilidad | El manifiesto **no registra** `USE_ENRUTADOR` ni `ENRUTADOR_POOL` | seccion `retrieval` de los dos `run_manifest.json` | manifiesto.py | S08, S10 | medio | **alta** | el campo nunca se añadio | ninguna | registrarlos | ninguno | el manifiesto permite reconstruir la configuracion sin consultar git |
| **H15** | Corpus / reproducibilidad | El `pdftotext` instalado (Xpdf 4.06) no reproduce ninguno de los 9 `.md`: pierde texto | reconversion de los 9 y muestreo: 24 pasajes de los `.md` ausentes de su extraccion | corpus_pdf.py | los 9 convertidos de PDF | medio (mitigado) | **alta** (medido) | Git for Windows trae el pdftotext de Xpdf en el PATH | ninguna | ya hay guarda que detiene la conversion; falta instalar poppler | ninguno | `implementacion_pdftotext()` devuelve "poppler" y el test deja de saltarse |
| **H16** | Evaluacion | No hay resultados de S07 en `results/` | listado del directorio | — | comparabilidad | medio | **alta** | no se versionaron | — | registrar la linea base de S07 o declarar que no existe | ninguno | el plan de reindexado no referencia una linea base inexistente |
| **H17** | Dataset | B3 es el modo mas delgado: 88 ejemplos de train, 13 de val | conteo sobre dataset.jsonl | dataset.jsonl | el modo B3 | medio | **alta** (medido) | el generador produjo pocos | H3 | ampliar B3 | requiere entrenamiento | B3 con masa comparable a su dificultad |
| **H18** | Citas / modelo | 5 de los 35 casos B2 tienen error de atribucion con el fragmento correcto en el contexto | dictamenes B2 tandas 1-4 | respuestas v1/v2 | 2917, 3328, 3729, 4226, 3327 | **alto** | **alta** | generacion, no recuperacion | H5 | H5 detecta uno de los cinco; los otros necesitan evaluacion semantica | — | el verificador detecta 3729; se documenta que 3328 y 2917 quedan fuera de alcance mecanico |

---

## 4. Evidencia de los problemas ya demostrados

### 4.1 La laguna del verificador (H5), probada funcion por funcion

Contexto: un chunk de la *Ley 2220 de 2022* con el articulo 5.
Respuesta: *"El articulo 5 de la Ley 2222 de 2022 regula la conciliacion."*

| funcion | devuelve |
|---|---|
| `citas_no_respaldadas` | `[]` -- el numero 5 si existe en el contexto |
| `citas_mal_atribuidas` | `[]` -- no hay fuente contra la que contradecir |
| `citas_no_verificables` | `[]` |
| `es_prudente` | `True` |
| `citas_atribuidas` | `[('', '5')]` **<- la señal, sin usar** |

Las ocho clases de defecto que pide el encargo, probadas:

| clase de defecto | ¿lo detecta? |
|---|---|
| Numero de articulo inexistente en el contexto | **si** (`citas_no_respaldadas`) |
| Articulo presente, atribuido a otra norma nombrada | **si** (`citas_mal_atribuidas`) |
| Ley homonima por numero (3729) | **no** |
| Articulo vecino de la misma ley (3328: 46 por 50) | **no** |
| Cita correcta que no respalda la afirmacion (2917) | **no** |
| Cita parcial usada para conclusion mas amplia (4128) | **no** |
| Articulo mencionado para rechazar su aplicacion (2221) | **no** -- y esta bien: no es defecto |
| Precision no textual ("la autoridad" -> "la Fiscalia", 4226) | **no** |

De las ocho, dos se detectan. **"Cero errores detectados" no significa "cero
errores juridicos"**, y conviene que ningun scorecard lo presente asi.

### 4.2 El atajo del dataset, y por que la validacion no lo veia (H3, H4)

| | preguntas con contexto | en 2+ modos |
|---|---|---|
| train | 652 | **418 (64 %)** |
| val | 103 | **0 (0 %)** |

Los 418 contrastivos son **todos B2 y todos de train**. La consecuencia es
metodologica: durante el entrenamiento de v2, el val loss media sobre un
conjunto donde el modo **sigue siendo predecible desde la pregunta**, que es
justo el atajo que los pares venian a romper.

Masa de tokens del target en train, que es la señal real del loss:

| modo | ejemplos | % ejemplos | % masa | media de tokens |
|---|---|---|---|---|
| B1 | 336 | 31 % | **50 %** | 106 |
| B2 | 646 | 60 % | **37 %** | 41 |
| B3 | 88 | 8 % | 13 % | 109 |

Los contrastivos **si** rebalancearon la masa (B2 pasa a 37 %), y aun asi la
abstencion sigue en 0/35. **Eso debilita la hipotesis de que el desbalance de
masa era la causa**, y señala el contenido de los ejemplos B2 antes que su
cantidad.

### 4.3 Distribucion del indice (corrige la hipotesis del distractor)

| norma | chunks | % del indice | % de recuperaciones |
|---|---|---|---|
| Codigo Civil | 2 047 | 17.1 % | 8.4 % |
| Codigo de Comercio | 1 901 | 15.9 % | 5.1 % |
| CGP | 975 | 8.1 % | 8.9 % |
| **5 mayores** | — | **52 %** | — |

Mediana de 196 chunks por norma; minimo 5 (Ley 1648). Los dos codigos grandes
son el 33 % del indice y el 13.5 % de las recuperaciones: **sub**-representados.
La hipotesis del distractor por volumen no se sostiene en esta forma; el
enrutador parece estar conteniendolos.

---

## 5. Incertidumbres y pruebas pendientes

1. **Donde cae el articulo correcto cuando no entra en el top-5** (H10, 29
   observaciones). Es la incognita que decide si el trabajo es de ranking o de
   representacion. La resuelve **6.1**, que **no se ejecuto**: requiere el
   `.faiss`, que esta en Drive, y `torch` + `faiss-cpu`, que no estan
   instalados localmente. Diseñada, no ejecutada.
2. **Las 190 filas de gold sin adjudicar** (H1), entre ellas 62 candidatos a
   omision que pueden subir el 38 %.
3. **Por que Pensiones empeoro** al ampliar el corpus (0.12 -> 0.00). Hecho
   medido; causa no.
4. **Si `multilingual-e5-base` alcanza** para consulta coloquial contra texto
   normativo (H11). La banda de 0.07 es compatible con un modelo poco
   discriminante y tambien con un indice de chunks muy parecidos entre si. No
   se puede separar sin medir contra otro modelo.
5. **Fuga semantica** train/eval. Descartada la lexica; la semantica exigiria
   embeddings, que no corren aqui. Las categorias coinciden por diseño, asi que
   el solapamiento tematico es esperado y no es fuga por si mismo.
6. **Si los ejemplos B2 inducen a rechazar evidencia valida.** El caso 3517 es
   la unica evidencia directa (v2 dice no tener una norma que estaba en el
   fragmento 1), y **un caso no hace tendencia**. Requiere revisar el contenido
   de los 418 contrastivos, no solo su conteo.
7. **Integridad de extraccion articulo por articulo** contra fuentes oficiales.
   No hecha. Lo verificado es que los articulos **gold** estan todos en el
   indice, que es mucho mas estrecho.
8. **Los 42 comparativos inconsistentes de M2.** Sin explicacion, y pesan sobre
   el juez que produce todo el `context_recall` de esta auditoria.
9. **Vigencia del resto del corpus.** Solo el art. 57 del CST esta verificado.
   El codigo no puede establecer el derecho vigente: esto exige contraste con
   fuente oficial y validacion profesional, norma por norma.

---

## 6. Plan de correccion priorizado

### P0 — invalidan conclusiones si no se hacen primero

**P0.1 Terminar la adjudicacion del gold** (H1).
*Resuelve:* que ninguna medicion de recuperacion sea concluyente.
*Archivos:* `docs/m3_articulos_gold_validacion.csv` (solo las columnas de
veredicto).
*Dependencias:* ninguna. *Riesgo:* ninguno, no toca el sistema.
*Orden:* clase B' (62, riesgo de fallo falso), luego B (82), luego C (46).
*Aceptacion:* 0 filas en `pendiente` sin justificacion; el acierto@5 depurado
se publica como **la** linea base.
*Requiere validacion juridica.*

**P0.2 Cerrar la laguna del verificador** (H5).
*Resuelve:* un error de fundamentacion que hoy es invisible.
*Archivos:* `tools/rag/verificacion.py`, mas una prueba.
*Dependencias:* ninguna. *Riesgo:* bajo, puede subir falsos positivos cuando la
respuesta nombra una norma informalmente.
*Aceptacion:* el caso 3729 se detecta y las 12 pruebas existentes siguen
pasando. **No requiere reindexar ni entrenar.**

**P0.3 Arreglar `huella_directorio`** (H13) y **registrar la configuracion del
enrutador en el manifiesto** (H14).
*Resuelve:* que la huella del corpus no se pueda comprobar desde la maquina
donde se trabaja, y que la palanca mas importante no quede registrada.
*Aceptacion:* el hash coincide en Windows y en Colab; el manifiesto permite
reconstruir la configuracion sin consultar git. Hacerlo **antes** de reindexar,
o la verificacion posterior dara un desajuste falso.

### P1 — alto impacto, con evidencia

**P1.1 Ejecutar 6.1, acierto@k por articulo** (H10).
En Colab, CPU, sin reconstruir el indice. **Por articulo, no por norma**: por
norma da 87 % y parece que todo esta bien.
*Dependencia:* P0.1, o los numeros se miden contra un gold que sabemos
defectuoso.
*Umbral fijado de antemano:* si en 10 o mas de los 29 casos de H10 el articulo
correcto esta entre los 100 primeros, el diagnostico es **ranking** y el corpus
no se toca.

**P1.2 Rediseñar los ejemplos B2** (H2).
La evidencia nueva reorienta esto: la masa de tokens ya se rebalanceo (B2 al
37 %) y la abstencion sigue en 0/35, asi que el problema esta en **que dicen**
los ejemplos, no en cuantos son. Antes de entrenar, inspeccionar el contenido
de los 418 contrastivos: si su target es una abstencion que el `system` no
distingue de una respuesta corta, el modelo no puede aprender la diferencia.
*Riesgo:* exige GPU. **No ejecutar sin autorizacion expresa.**

**P1.3 Rehacer el split con contrastivos en validacion** (H3, H4).
*Riesgo importante:* cambia el split, asi que la comparacion v1/v2 ya
registrada deja de ser comparable. Hay que decidir si se conserva la actual
como historica.
*Aceptacion:* val con preguntas multimodo en proporcion a train, y diferencia
de proporcion por modo menor a 5 puntos.

**P1.4 Vigencia del art. 57 del CST** (H6), con `status` y `vigente` (H7, H8).
*Dependencia:* poppler-utils (H15) y contraste con fuente oficial.
*Requiere validacion juridica.* Se integra en la **unica** reconstruccion.

### P2 — mejoras con evidencia, despues de medir

**P2.1 Encabezado en los chunks de continuacion** (H9). Explica 22 de 53
fallos. *Dependencia:* P1.1, porque gastar la unica reconstruccion en una
hipotesis que cubre menos de la mitad de los fallos es mal negocio.
**P2.2 Margen relativo en vez de piso absoluto** (H11). Dependencia: P1.1.
**P2.3 Ampliar B3** (H17).
**P2.4 Registrar o declarar la linea base de S07** (H16).

### P3 — no justifican tocar el sistema todavia

Ley 1123 de 2007 (sin categoria asignada ni caso que la pida). Reducir el peso
de las normas grandes: **la evidencia apunta en contra**.

### La unica reconstruccion

Se reindexa **una vez**, y solo cuando: (a) el gold este adjudicado, (b) 6.1
este medido, (c) este decidido si entra la Ley 2466, (d) poppler-utils este
instalado, y (e) P0.3 este hecho. Entran de golpe P1.4, P2.1 y P2.2. Despues se
recorren S07, S08 y S10 en ese orden, y se publica la tabla de equivalencia de
hashes.

---

## 7. Criterios cuantitativos

| intervencion | metrica | linea base | umbral de exito | control que no debe bajar |
|---|---|---|---|---|
| P0.1 | filas adjudicadas | 27/217 | 217/217 o pendientes justificadas | — |
| P0.2 | clases de defecto detectadas | 2 de 8 | 3 de 8 (entra la ley homonima) | las 12 pruebas de atribucion |
| P0.3 | hash reproducible en Windows | no | si | `hash_corpus` de S08/S10 sigue reproduciendose desde git |
| P1.1 | acierto@5/@10/@30/@100 por articulo | @5 = 17/45 depurado | — (es medicion) | — |
| P1.2 | abstenciones puras en pertinencia insuficiente | 0/27 | > 0, y sin que B1 pierda fundamentacion | acierto de cita en los casos B1 |
| P1.3 | diferencia de proporcion por modo train/val | hasta 26 puntos | < 5 puntos | — |
| P2.1 | acierto@5 por articulo | el depurado de P0.1 | sube | Despido, Salud/EPS, Garantias, Acceso a informacion, Familia (0.83-1.00) |
| P2.2 | recall **y** casos sin contexto | 0.394 y 1/45 | recall sube sin que suban los casos sin contexto | — |

**Todos los umbrales se fijan antes de ejecutar.** Y ninguna prueba automatica
se presenta como garantia de correccion juridica: la de P0.2 garantiza que se
detecta una ley nombrada que no esta en el contexto, y nada mas.

---

## 8. Riesgos de regresion y decisiones congeladas

### Congelado hasta medir

| decision | hasta |
|---|---|
| Tocar `chunk.py` | que 6.1 este medido (P1.1) |
| Reconstruir el indice | las cinco condiciones de arriba |
| Tocar `data/corpus/normas/` | validacion juridica de vigencia y poppler instalado |
| Reentrenar | autorizacion expresa de GPU, y el rediseño de B2 antes del entrenamiento |
| Cambiar el split | decidir si la comparacion v1/v2 registrada se conserva como historica |
| `USE_RERANK`, hybrid | nada que hacer: la evidencia dice mantenerlos como estan |

### Riesgos concretos

1. **Perder la comparabilidad S08/S10.** Hoy comparten `hash_indice`,
   `hash_corpus` y `n_chunks`. Es lo que permite afirmar que midieron sobre lo
   mismo.
2. **Invalidar B2.** El 12/14/9 se midio contra respuestas generadas con este
   contexto. Si el contexto cambia, las 35 comparaciones describen un sistema
   que ya no existe, y la adjudicacion de Leonardo queda referida a un estado
   anterior.
3. **Ampliar el corpus puede bajar el recall.** Ya paso con Pensiones
   (0.12 -> 0.00). Ampliar sin medir es apostar.
4. **El encabezado repetido en 2 069 chunks** sube la similitud entre chunks y
   puede crear distractores nuevos. No esta medido.
5. **El corpus no se puede regenerar en esta maquina** (H15). La guarda ya lo
   impide, pero significa que la via del PDF esta cerrada hasta instalar
   poppler.
6. **Reparar el gold puede empujar en las dos direcciones.** Los `no_responde`
   bajan la linea base; los 62 candidatos a omision la suben. El resultado neto
   **no se conoce**, y conviene no anunciarlo antes de P0.1.

---

## 9. Estado final de Git y archivos

| | |
|---|---|
| Rama | `m3.5` |
| HEAD | `1e75060` |
| Arbol de trabajo | limpio antes de esta auditoria |
| Commits locales sin empujar | **8** respecto de `origin/m3.5` |
| Commits hechos en esta auditoria | **ninguno** |

**Archivo nuevo:** `docs/m3_auditoria_integral.md` (este informe).
**Archivos modificados:** ninguno.

Artefactos **inspeccionados**: todo lo versionado en git, mas
`results/m3_s08_2026-10-09/rag_index_metadata.jsonl` (12 MB, bajado de Drive,
ignorado por git, huella verificada).

Artefactos **no accesibles**, y por tanto no inspeccionados ni afirmados:
`rag_index.faiss` (48 MB, solo en Drive), los adaptadores LoRA (solo en Drive;
su `hash_adaptador` consta en los manifiestos pero no se verifico contra el
archivo), y los resultados de S07 (no existen en `results/`).

Comprobaciones locales ejecutadas, todas de solo lectura: huellas de corpus,
dataset y metadata; conteos sobre el dataset y la metadata del indice; sonda de
`verificacion.py` por llamada a funcion; cruce de registros de S08 con el gold;
y la suite de pruebas, que antes de esta auditoria daba **651 passed, 4
skipped**.
