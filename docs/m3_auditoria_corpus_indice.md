# Auditoria de corpus, indice y recuperacion

**Solo lectura.** No se modifico corpus, codigo, configuracion, notebooks,
manifiestos, datasets, indices ni resultados. No se reindexo, no se uso GPU y
no se escribio el CSV de adjudicacion.

Rama auditada: **`m3.5`**, commit `d0a7c01`. (El encargo decia `m3.9`; no
existe esa rama en el repositorio.)

---

## La respuesta

**Hay que mejorar la recuperacion. El corpus solo necesita una correccion
puntual y acotada.**

La cobertura dejo de ser el cuello de botella y hay una medicion que lo prueba:
el corpus paso de 10 normas y unos 3 400 chunks a 36 normas y **11 975 chunks**,
y el `context_recall` global se quedo donde estaba.

| | chunks | context_recall global |
|---|---|---|
| Antes de ampliar (s08 2026-10-07) | ~3 400 | ~0.40 (ponderado de 0.49 / 0.29) |
| Con el corpus completo (s08 2026-10-09) | **11 975** | **0.394** |

Triplicar el corpus no movio el recall. Lo que hizo fue redistribuirlo: tres
categorias mejoraron mucho y otras empeoraron.

---

## 1. Resumen ejecutivo

Cinco hechos medidos, cada uno con su archivo:

**1. El indice evaluado SI corresponde al corpus del repositorio.** El
`hash_corpus` de S08 y S10 (`1c552822959e2932`) se reproduce exactamente
calculandolo sobre los blobs de git en ambos commits y en HEAD. Los dos modulos
comparten `hash_indice` (`19657d22583f93d0`) y `n_chunks` (11 975), asi que
midieron sobre lo mismo y son comparables entre si.

**2. El documento de cobertura esta vencido en un punto central.**
`docs/m3_cobertura_corpus.md` dice "todavia **sin indice reconstruido**". Es
falso hoy: 11 975 chunks corresponden al corpus ampliado de 36 normas (la
estimacion del propio documento era "unos 11 900"). El indice se reconstruyo y
se evaluo.

**3. La cobertura esta practicamente resuelta.** `CATEGORIAS_SIN_NORMA` esta
vacio, `FUERA_DE_ALCANCE` esta vacio, 27 de 27 categorias objetivo cubiertas, y
`NORMAS_PENDIENTES` tiene dos entradas, una de ellas sin categoria asignada.

**4. Y aun asi, siete categorias cuya norma SI esta indexada miden recall
0.00.** Derecho comercial, Pensiones y seguridad social, Procedimiento civil -
recursos, Conciliacion prejudicial, Comparendos de transito, Educacion /
debido proceso disciplinario, Contratacion estatal y facturacion, Derecho
administrativo general. Sus normas estan todas en `data/corpus/normas/`.

**5. El retriever casi no discrimina.** Sobre los 370 chunks recuperados en
S08 config A:

| | |
|---|---|
| minimo | 0.810 (exactamente `RETRIEVAL_MIN_SCORE`) |
| p25 | 0.827 |
| mediana | 0.833 |
| maximo | 0.880 |
| por debajo de 0.85 | **333 de 370 (90 %)** |

Toda la masa cabe en una banda de 0.07. Entre el mejor chunk de todo el
benchmark y el peor que pasa el filtro hay esa diferencia, sobre 11 975
candidatos. El top-5 se decide con muy poca senal.

Y el discriminante que separa recuperacion de cobertura: **17 de 45 casos
tienen recall 0.00, pero solo 1 caso no recupero ningun chunk.** En los otros
16 el sistema trajo cinco fragmentos y ninguno servia. Eso es ranking, no
ausencia.

---

## 2. Hallazgos comprobados, con referencias

### 2.1 Recall por categoria sobre el indice reconstruido

`results/m3_s10_2026-10-09/ragas_checkpoint_A_denso_8890b0bb.jsonl`, 45 casos.

| Categoria | n | recall | antes (doc cobertura) |
|---|---|---|---|
| Derecho comercial | 2 | **0.00** | 0.00 (estaba fuera del corpus) |
| Pensiones y seguridad social | 2 | **0.00** | 0.12 **empeoro** |
| Procedimiento civil - recursos | 2 | 0.00 | n/d |
| Prestamos informales y usura | 1 | 0.00 | n/d |
| Conciliacion prejudicial | 1 | 0.00 | n/d |
| Comparendos de transito | 1 | 0.00 | n/d |
| Educacion / debido proceso | 1 | **0.00** | 0.00 (estaba fuera) |
| Contratacion estatal | 1 | **0.00** | 0.00 (estaba fuera) |
| Derecho administrativo general | 1 | **0.00** | 0.00 (ya estaba indexada) |
| Propiedad intelectual - marcas | 1 | 0.25 | 0.00 |
| Licencias urbanisticas | 1 | 0.25 | 0.00 |
| Relaciones laborales | 4 | 0.33 | n/d |
| Embargos | 3 | 0.39 | n/d |
| Accidentes de transito | 3 | 0.42 | 0.28 |
| Arriendo | 3 | 0.50 | n/d |
| Reporte en centrales de riesgo | 3 | 0.61 | n/d |
| Derecho ambiental sancionatorio | 1 | **0.67** | 0.00 |
| Despido | 2 | **0.83** | 0.12 |
| Garantias de consumo | 2 | 0.83 | n/d |
| Salud / EPS | 3 | **0.83** | 0.17 |
| Acceso a informacion publica | 1 | 1.00 | n/d |
| Derecho de familia - alimentos | 1 | 1.00 | n/d |

Lectura: ampliar el corpus **si funciono donde la norma faltaba de verdad**
(Despido 0.12 -> 0.83 con la Ley 1010 y la Ley 2452; Salud 0.17 -> 0.83 con la
Ley 1751; Ambiental 0.00 -> 0.67 con la Ley 1333). Donde la norma ya estaba o
donde el problema era otro, no movio nada, y Pensiones empeoro. El efecto
distractor que el propio documento de cobertura anticipo ("mas candidatos
significa mas distractores") **esta medido**: el saldo global es cero.

### 2.2 La maquinaria de recuperacion extra empeora el recall

`results/m3_s08_2026-10-09/ragas_resumen_abc.json`:

| Config | context_recall | context_precision | recall 0 | faithfulness |
|---|---|---|---|---|
| A denso | **0.394** | 0.558 | 17/45 | 0.510 |
| B hybrid (BM25 + RRF) | 0.381 | **0.629** | 17/45 | 0.525 |
| C rerank (cross-encoder) | **0.352** | 0.603 | 15/45 | 0.541 |

Hybrid y rerank **suben la precision y bajan el recall**. Con `TOP_K = 5` eso
es un intercambio malo para este producto: el problema es que el fragmento
pertinente no llega, no que lleguen demasiados. `USE_RERANK = False` en
`tools/rag/config.py:109` es, segun estos numeros, la decision correcta.

### 2.3 Los prefijos de e5 estan bien: esa hipotesis queda descartada

El documento de cobertura listaba "el prefijo de e5" como tercera sospecha.
Verificado en `tools/rag/embed_store.py:150-185`: `_embed_with_prefix` aplica
el prefijo, hace mean pooling enmascarado y normaliza L2, y se expone solo via
`embed_query` / `embed_passages`, que usan `E5_QUERY_PREFIX` ("query: ") y
`E5_PASSAGE_PREFIX` ("passage: ") de `tools/rag/config.py:42-43`. No hay ruta
que embeba sin prefijo. **Hipotesis descartada.**

Queda abierta la pregunta de si `multilingual-e5-base` es suficiente para
consulta coloquial contra texto normativo, que es otra cosa y no se puede
decidir sin medir.

### 2.4 Vigencia: el articulo 57 del CST, confirmado

Es el unico hallazgo de corpus con evidencia dura, y lo verifique leyendo el
archivo, no asumiendolo.

`data/corpus/normas/codigo_sustantivo_trabajo_decreto_2663_1950.md`, articulo
57: concede licencias para **sufragio, cargos oficiales transitorios de forzosa
aceptacion, grave calamidad domestica, comisiones sindicales y entierro de
companeros**. Comprobado por busqueda literal en el fragmento del articulo:

| termino | aparece |
|---|---|
| citacion | no |
| comisaria | no |
| violencia | no |
| judicial | no |
| administrativa | no |

El front matter dice `status: "in_force"` y `last_updated: "2026-10-08"`. Las
dos cosas inducen a error: la fecha es de la conversion, no de la version del
texto.

El archivo si anota la Ley 2466 de 2025, pero **solo en los articulos 3 y 4**, y
su propia nota lo dice: *"solo anota la Ley 2466 de 2025 en sus primeros
articulos: no trae, p. ej., el nocturno desde las 7 p. m."*. Coincide con
`corpus.NORMAS_PENDIENTES`.

Consecuencia, ya registrada en el caso 4630: **la recuperacion no podia traer
ese derecho ni con ranking perfecto.** Es cobertura/vigencia, no recuperacion
ni generacion.

### 2.5 Concentracion de la recuperacion

De 370 chunks recuperados, aparecen 31 normas distintas de 36. Las cuatro mas
recuperadas se llevan el 37 %:

| Norma | chunks | % |
|---|---|---|
| Codigo Sustantivo del Trabajo | 51 | 13.8 |
| Codigo General del Proceso | 33 | 8.9 |
| Codigo Civil | 31 | 8.4 |
| CPACA | 23 | 6.2 |

El Codigo Civil es una de las normas que mas chunks aporta al indice (~3 900
entre el y el de Comercio, segun el documento de cobertura) y aparece en el 8 %
de las recuperaciones. **Hipotesis, no medicion:** normas muy grandes y de
lenguaje general compiten por consultas de otras materias. Se puede comprobar
sin reindexar (ver 6.1).

### 2.6 Defecto de trazabilidad en la huella del corpus

`tools/rag/manifiesto.py:64` calcula `hash_corpus` sobre los bytes crudos y con
`patron="*.md"`. Dos consecuencias:

1. **No normaliza fin de linea.** En un checkout de Windows (CRLF) da
   `1bd16dcc1baccc6b`; el registrado es `1c552822959e2932`. No es que el corpus
   haya cambiado -- es la misma trampa que ya corregimos en
   `config.huella_dataset`, que si normaliza. Verificar la huella desde Windows
   da un falso positivo de "el corpus cambio".
2. **Incluye `README.md`.** Editar la documentacion del corpus cambia el
   `hash_corpus` sin que ninguna norma cambie. Comprobado: excluyendo el README
   da `b55318d8e6d46b6d`.

No invalida ninguna medicion pasada. Si hace que la comprobacion sea
inservible desde una maquina Windows, que es donde se trabaja.

---

## 3. Matriz de fallos por caso (B2)

**Las adjudicaciones comparativas siguen siendo provisionales**: el CSV oficial
conserva las 35 en `pendiente`.

Cruce de las categorias de los 35 casos B2 con el recall medido en S08:
**14 de los 35 caen en categorias que miden recall 0.00**. Y la adjudicacion,
hecha leyendo los fragmentos, dice `pertinencia_contexto` **insuficiente en 27
de 35** y parcial en 8. Las dos mediciones, independientes, apuntan a lo mismo.

| case_id | Pregunta (resumen) | Clase | Evidencia | Confianza |
|---|---|---|---|---|
| 4630 | permiso laboral para citas de comisaria | **V** | art. 57 CST indexado sin los supuestos de 2025 (2.4) | **alta** |
| 2917 | foto-multa, duda de la velocidad | **G** | el art. 223-A estaba en el contexto y v2 afirma que "permite objetar"; el texto dice lo contrario | **alta** |
| 3729 | cuota alimentaria | **G** | v2 cita "Ley 2222 de 2022"; el contexto trae la Ley 2220 | **alta** |
| 3328 | entrega internacional B2B | **G** | los dos atribuyen al art. 46 lo que dice el art. 50; ambos articulos en el contexto | **alta** |
| 3517 | multa por plan de manejo ambiental | **G** | el art. 63 de la Ley 1801 estaba en el fragmento 1 y v2 dice no tenerlo | **alta** |
| 4226 | donde denunciar un gota a gota | **G** | el art. 67 dice "a la autoridad"; v2 dice "ante la Fiscalia" | media |
| 3327 | mantenimiento en leasing | **G** | v2 extiende el art. 98 CST a clausulas que no menciona | media |
| 2424, 3321 | laboral / deuda B2B | **R** | v1 construye sobre el art. 141 de la Ley 142 (servicios publicos) en dos materias ajenas: el contexto traia la norma equivocada | media |
| 3026 | base de datos de colegios | **R** | se recupero la Ley 1266 (habeas data financiero) para un portal de datos abiertos | media |
| 3621 | contrato en dolares | **R** | se recupero el art. 195 CST (patrimonio gravable) | media |
| 3022 | correo de la alcaldia | **R** | se recupero el art. 121 sobre animales encontrados | media |
| 2229, 2823, 3626 | compraventa / embargo / contrato vencido | **R** | normas de otra materia en el contexto (Ley 142 art. 137; CST art. 65; CST art. 38) | media |
| 3118, 3122 | conciliacion: costo y duracion | **R/C** | categoria Conciliacion prejudicial mide recall 0.00 con la Ley 2220 indexada | media |
| 4128 | doble pension | **R/C** | Pensiones mide 0.00 y **empeoro** tras ampliar; la Ley 100 esta indexada | media |
| 3920 | licencia urbanistica | **R** | Licencias urbanisticas mide 0.25 con la Ley 388 indexada | media |
| 4724 | energia en la vereda | **R** | Servicios publicos: se recupero el art. 34 de la Ley 388 (suelo suburbano) | media |
| 3822, 4324, 4026, 4127, 4321, 2822, 3428, 3423, 2126, 3124, 3228, 2221, 4623, 4225, 3628, 2823 | varias | **P** | sin traza de recuperacion por caso en el registro B2: no se puede separar R de C sin reproducir la consulta | -- |

Resumen de clases con evidencia suficiente: **V 1 · G 7 · R 12 · R/C 4 · P
resto.** Ninguna **I** (el indice corresponde al corpus, 1.1) y ninguna **E**
con evidencia (ver 7.3).

Nota metodologica exigida por el encargo: **ninguno de los casos G se arregla
reindexando.** Son siete casos donde el fragmento correcto estaba en el
contexto y el modelo lo leyo mal, lo atribuyo mal u omitio una condicion. Y al
contrario: los 12 **R** no se arreglan tocando el corpus.

---

## 4. Correcciones priorizadas

### Grupo 1 — Corpus (poco, y acotado)

| hallazgo | evidencia | casos | impacto | confianza | correccion | riesgo de regresion | prueba de aceptacion |
|---|---|---|---|---|---|---|---|
| art. 57 CST sin la reforma de 2025 | 2.4, lectura del archivo | 4630 y, por frecuencia, Despido + Relaciones laborales (6 casos gold) | **alto** | **alta** | incorporar el texto de la Ley 2466 de 2025 | cambia `hash_corpus` e `hash_indice`: obliga a recorrer S07/S08/S10 | una consulta por licencia por citacion judicial recupera el art. 57 reformado |
| `status: in_force` enganoso | 2.4 | transversal | medio | alta | distinguir en el front matter la fecha de conversion de la version del texto | ninguno si solo cambia metadata, pero mueve `hash_corpus` | el front matter declara la version, no solo la fecha de conversion |
| Ley 1123 de 2007 ausente | `corpus.NORMAS_PENDIENTES` | ninguno medido | **bajo** | alta | **incorporacion opcional**: no hay categoria asignada ni caso que la pida | — | — |

### Grupo 2 — Indice y recuperacion (aqui esta el trabajo)

| hallazgo | evidencia | casos | impacto | confianza | correccion | riesgo de regresion | prueba de aceptacion |
|---|---|---|---|---|---|---|---|
| 16 casos recuperan 5 chunks y ninguno sirve | 1.5 | 16/45 | **alto** | **alta** | medir primero donde cae el chunk correcto (6.1) antes de cambiar nada | ninguno: es medicion | acierto@30 por caso, para separar "no esta en candidatos" de "esta y queda abajo" |
| 7 categorias con norma indexada y recall 0.00 | 2.1 | 9/45 | **alto** | **alta** | revisar el enrutador por categoria y el filtrado antes de tocar top-k | el enrutador ya tuvo una regresion (`enrutador.py`) | recall > 0 en las 7 sin bajar las que estan en 0.83+ |
| banda de score de 0.07 y piso de 0.81 casi inoperante | 1.5 | transversal | **alto** | media | el piso absoluto no discrimina en esta distribucion; evaluar margen relativo | subir el piso deja casos sin contexto (ya pasa en 1) | n de casos sin contexto y recall, a la vez |
| Pensiones empeoro al ampliar (0.12 -> 0.00) | 2.1 | 2/45 | medio | **alta** | identificar que normas desplazaron a la Ley 100 | — | recall de Pensiones > 0.12 |
| hybrid y rerank bajan recall | 2.2 | transversal | medio | **alta** | mantener A denso; no activar rerank | ninguno | el que cambie debe subir recall, no solo precision |
| normas grandes concentran recuperacion | 2.5 | hipotesis | medio | **baja** | medir aporte por norma antes de proponer nada | — | recall por categoria estable al ponderar por norma |
| `hash_corpus` sin normalizar CRLF y con README | 2.6 | trazabilidad | medio | **alta** | normalizar como `huella_dataset`; excluir README | **ninguno sobre mediciones**; cambia el valor registrado, asi que hay que anotar la equivalencia | el hash coincide en Windows y en Colab para el mismo contenido |

### Grupo 3 — Modelo e instrucciones

| hallazgo | evidencia | casos | impacto | confianza | correccion | riesgo de regresion | prueba de aceptacion |
|---|---|---|---|---|---|---|---|
| atribucion entre articulos del mismo contexto | 3328, 2917, 3729, 4226, 3327 | 5 | **alto** | **alta** | el verificador ya cubre leyes homonimas por numero (`verificacion.py:170-190`); falta el caso articulo-a-articulo dentro de la misma ley | — | 3328 detectado: el art. 46 no sostiene lo que se le atribuye |
| afirmar lo contrario del texto | 2917 | 1 | **alto** | **alta** | pertenece al dataset, no al corpus | — | — |
| abstenerse teniendo la norma | 3517 | 1 | medio | **alta** | es el reverso de los pares contrastivos de v2 | v2 ya muestra esta regresion | 3517 cita el art. 63 y advierte el supuesto |

**Sobre lo que una prueba automatica garantiza.** `verificacion.py` comprueba
que el **numero de norma** citado coincida con la fuente, y por eso detecta
"Ley 2222" contra "Ley 2220" (caso 3729). **No** detecta el caso 3328 --
atribuir al articulo 46 el contenido del 50 cuando los dos estan en el contexto
y son de la misma ley -- y una heuristica lexica para eso se probo y se retiro
por fallar en el caso 3328. Queda fuera de alcance.

---

## 5. Riesgos de tocar el corpus o reindexar ahora

1. **Se pierde la comparabilidad S08/S10.** Cualquier cambio en
   `data/corpus/normas/` mueve `hash_corpus` y, al reindexar, `hash_indice`.
   S08 y S10 comparten hoy los dos hashes; es lo que permite afirmar que
   midieron sobre lo mismo. Hay que recorrer S07, S08 y S10 en ese orden.
2. **M1 v2 queda a medias.** El marcador 12/14/9 se midio contra respuestas
   generadas con este contexto. Si el contexto cambia, las 35 comparaciones
   describen un sistema que ya no existe, y la adjudicacion de Leonardo
   quedaria referida a un estado anterior.
3. **Reindexar cuesta GPU**, que esta restringida.
4. **El corpus no se puede regenerar en esta maquina.** `pdftotext` instalado
   es Xpdf 4.06 y no reproduce los nueve `.md` convertidos: pierde texto.
   `tools/corpus_pdf.py` ya se detiene antes de intentarlo. Incorporar la Ley
   2466 por la via de PDF exige poppler-utils primero.
5. **Riesgo de ampliar mas el corpus**: ya hay evidencia medida de que
   anadir normas puede bajar el recall de categorias que funcionaban
   (Pensiones). Ampliar sin medir es apostar.

**Recomendacion:** no tocar el corpus ni el indice hasta cerrar B2 y ejecutar
las mediciones de la fase 6, que no requieren reindexar.

---

## 6. Plan de validacion, sin ejecutar

Ninguna de estas pruebas se corrio. Las dos primeras **necesitan el indice**,
que no esta en el repositorio (vive en Drive), asi que son para una fase
posterior en Colab y sin GPU (el embedding de 45 consultas es CPU).

### 6.1 Acierto@k por caso — la prueba que decide el orden del trabajo

Para los 45 casos gold, recuperar k = 5, 10, 30 y 100 **sin reindexar** y
registrar en que puesto aparece el primer chunk pertinente.

- Si el chunk correcto esta en el top-100 pero no en el top-5 -> **ranking**:
  el trabajo es reordenar, y el corpus esta bien.
- Si no esta ni en el top-100 -> **representacion**: el chunking o el embedding,
  y ahi si hay trabajo de corpus.

Criterio de aceptacion fijado de antemano: si en 10 o mas de los 16 casos con
recall 0 y contexto no vacio el chunk correcto esta entre los 100 primeros, el
diagnostico es ranking y no se toca el corpus.

### 6.2 El enrutador sobre las 7 categorias en cero

Pasar las consultas de esas 7 categorias por `enrutador.py` y comprobar a que
norma enrutan. Es barato y **no necesita el indice**: se puede correr ya.

Criterio: si el enrutador manda a una norma distinta de la pertinente en 4 o
mas de las 7, el enrutador es la causa y se corrige ahi.

### 6.3 Conjunto de consultas que detecta los hallazgos

| hallazgo | consulta | resultado esperado hoy | tras corregir |
|---|---|---|---|
| 2.4 vigencia | "me citaron a la comisaria, me dan permiso en el trabajo" | art. 57 sin el supuesto | art. 57 reformado |
| 2.1 Pensiones | las 2 consultas gold de Pensiones | recall 0.00 | > 0.12 |
| 2.1 Conciliacion | la consulta gold de Conciliacion | recall 0.00 | > 0 con la Ley 2220 |
| 2.5 distractores | consulta laboral | medir si aparece Codigo Civil | sin cambio en las que ya andan |

### 6.4 No degradar lo que funciona

Antes/despues sobre los mismos 45 casos, misma config A denso, mismo eval set
(`hash_eval_set = a5151999c2095d00`, congelado). Las categorias en 0.83 y 1.00
(Despido, Salud / EPS, Garantias de consumo, Acceso a informacion publica,
Derecho de familia) son el control: si alguna baja, el cambio se revierte.

### 6.5 Trazabilidad

Antes de reindexar, anotar `hash_corpus`, `hash_indice`,
`hash_metadata_indice`, `n_chunks`, `hash_dataset`, `hash_eval_set`,
`hash_adaptador` y `git_commit`, que el manifiesto ya registra. Y arreglar
**primero** el defecto de 2.6, para que la huella del corpus sea comprobable
desde Windows -- si no, la verificacion posterior dara un desajuste falso.

### 6.6 Cuando reconstruir el indice

Una sola vez, y solo cuando: (a) B2 este escrito en el CSV, (b) 6.1 y 6.2 esten
medidos, (c) este decidido si se incorpora la Ley 2466, y (d) poppler-utils
este instalado. Entonces se recorren S07, S08 y S10 en ese orden, y se publica
la tabla de equivalencia de hashes para no perder la comparacion.

---

## 7. Incertidumbres que requieren mas evidencia

1. **Si el chunk correcto esta entre los candidatos.** Es la incognita que
   decide si el trabajo es de ranking o de representacion, y no se puede
   responder sin el indice. La resuelve 6.1.
2. **Por que Pensiones empeoro.** Hecho medido (0.12 -> 0.00); la causa no.
3. **Integridad de extraccion (clase E).** No encontre evidencia de articulos
   perdidos en los `.md` indexados, pero **tampoco la busque de forma
   exhaustiva**: lo que comprobe es que el Xpdf de esta maquina pierde texto al
   reconvertir, que es un problema distinto -- el corpus comiteado es el bueno.
   Una auditoria de integridad articulo por articulo contra las fuentes esta
   sin hacer.
4. **Si `multilingual-e5-base` alcanza** para consulta coloquial contra texto
   normativo. La banda de 0.07 es compatible con un modelo poco discriminante
   en este dominio y tambien con que el corpus tenga muchos chunks parecidos.
   No se puede separar sin medir contra otro modelo.
5. **Chunking.** `MAX_TOKENS_PER_CHUNK = 350` sigue siendo la primera sospecha
   del documento de cobertura y **no la verifique**: haria falta revisar si
   articulos largos quedan partidos entre condicion y excepcion. Es trabajo
   pendiente, no un hallazgo.
6. **Las 19 clases P de la matriz.** El registro de B2 no guarda la traza de
   recuperacion por caso, asi que no se puede separar R de C. Si se quiere
   cerrar esa columna, hay que reproducir las consultas (6.1 lo haria de paso).
7. **Los 42 comparativos inconsistentes de M2** siguen sin explicacion y
   podrian tocar la fiabilidad del juez, que es quien produce el
   `context_recall` de toda esta auditoria.

---

# Anexo: resultado de 6.2 (enrutador) — ejecutado

Solo lectura, sin indice FAISS, sin GPU, sin Colab. Fuentes:
`data/eval_set.json`, `data/eval_set_articulos.json` (45 casos con articulo
gold etiquetado) y `results/m3_s08_2026-10-09/eval_records_config_a.json`.

## El enrutador no es la causa

Criterio de aceptacion, fijado antes de medir: *"si el enrutador manda a una
norma distinta de la pertinente en 4 o mas de las 7 categorias, el enrutador
es la causa"*. **No se cumple.**

Primero, un hueco de trazabilidad que hubo que resolver: el manifiesto de S08 y
S10 **no registra `USE_ENRUTADOR` ni `ENRUTADOR_POOL`**. Su seccion
`retrieval` solo guarda modelo de embedding, top_k, piso y tamanos de chunk.
Resuelto por git: `USE_ENRUTADOR = True` en `tools/rag/config.py:129` tanto en
`8fd29a69` (S08) como en `5c884760` (S10). **El enrutador estaba encendido
cuando esas categorias midieron 0.00**, asi que "falta activarlo" queda
descartado.

Comportamiento sobre los 45 casos gold:

| | casos |
|---|---|
| Prioriza la norma gold | **39 / 45 (87 %)** |
| Relega la norma gold | 4 |
| No predice categoria (no filtra) | 2 |

Y en los 12 casos de las categorias que midieron recall 0.00: **prioriza
correctamente en 8**, relega en 2, no filtra en 2. El enrutador explica, como
maximo, 4 de esos 12.

Tampoco es un filtro decorativo. Estrecha de verdad:

| | |
|---|---|
| Normas priorizadas por consulta | mediana **8 de 36** |
| Fraccion del texto del corpus | mediana **28 %** (min 17 %, max 100 %) |
| Casos que priorizan mas de la mitad del texto | 2 / 45 |

## Lo que si aparecio, y es mas grande

La medicion que no buscaba esta prueba. Separando acierto@5 por nivel:

| nivel | acierto@5 |
|---|---|
| La **norma** gold llega al top-5 | **39 / 45 — 87 %** |
| El **articulo** gold llega al top-5 | **21 / 45 — 47 %** |
| No llega ni la norma | 6 / 45 — 13 % |

**En 18 casos la norma correcta llega y el articulo correcto no.** Es el grupo
de fallos mas grande del benchmark, y no lo explica ni la cobertura (la norma
esta indexada), ni el enrutador (la priorizo), ni la recuperacion a nivel de
norma (llego al top-5).

Y cae cerca. De los 28 fallos de articulo con la norma correcta presente:

| | |
|---|---|
| A 5 articulos o menos del gold | **15 (54 %)** |
| Distancia mediana | **4 articulos** |
| Casos donde trajo el articulo **contiguo** | **6** |

Ejemplos, con el articulo pedido y el traido:

| caso | categoria | norma | gold | trajo |
|---|---|---|---|---|
| 9056 | Embargos | CGP | 597 | 593, **598, 599** |
| 9039 | Centrales de riesgo | Ley 1266 | 13 | **14**, 16, 19-A |
| 9035 | Arriendo | Ley 820 | 16 | **15**, 22, 23, 25, 8 |
| 9063 | Pensiones | Ley 100 | 21, 34 | **33, 35**, 117, 14, 27 |
| 9004 | Salud / EPS | Ley 1751 | 2, 6 | 10 |
| 9050 | Derecho comercial | C. Comercio | 712, 730, 731, 784, 793 | 714, 720, 721, 724, 728 |

El sistema encuentra el vecindario correcto y escoge mal dentro de el. Eso es
**granularidad y ranking a nivel de chunk**, que es exactamente la
incertidumbre nº 5 de este informe -- `MAX_TOKENS_PER_CHUNK = 350` -- y deja de
ser sospecha: ahora tiene evidencia.

## Defectos reales del enrutador, menores

1. **Dos casos sin categoria predicha** (no prioriza nada): 9010
   (conciliacion: *"demandar a mi ex-socio... ¿tengo que hacer algo antes?"*) y
   9050 (*"recibi un cheque y el banco lo devolvio"*).
2. **Dos casos mal enrutados**: 9042, la fotomulta, predice **Arriendo** y
   **Embargos** siendo Comparendos de transito; 9049, *"vendo ropa por
   Instagram, ¿registro en Camara de Comercio?"*, predice Propiedad intelectual
   y Garantias de consumo cuando el gold es el Codigo de Comercio.
3. **Las transversales ocupan el 15 % del top-5** (34 de 225 chunks), y el
   CPACA solo aporta 18 de esos 34. La Ley 1581 es transversal y pesa 8.3 % del
   corpus, pero solo aparece 4 veces: impacto bajo. No es prioritario.

## Que cambia en el plan

**6.1 hay que rediseñarla.** Estaba planteada como acierto@k sin precisar el
nivel; medirla por norma daria 87 % y pareceria que todo esta bien. Debe
medirse **a nivel de articulo**, y la pregunta pasa a ser: cuando el articulo
gold no esta en el top-5, ¿esta en el top-30 o en el top-100 de la misma norma?

- Si esta -> **ranking de chunks**: reordenar dentro de la norma.
- Si no esta -> **representacion**: el chunk que contiene ese articulo no se
  parece a la pregunta, y ahi el trabajo es de chunking o de embedding.

**La auditoria de chunking sube a primera prioridad**, por delante de 6.1, y
es lo unico que hace falta ahora: solo necesita `rag_index_metadata.jsonl`, sin
FAISS, sin GPU. Lo que hay que mirar es si el articulo gold de esos 18 casos
quedo partido, fusionado con el vecino o sin su encabezado.

## Alcance de lo medido

Esto se midio sobre los **45 casos gold**, no sobre los 35 de B2. En la matriz
de la seccion 3 clasifique 12 casos B2 como **R** porque el contexto traia
normas de otra materia, y eso sigue sostenido por las respuestas guardadas. Lo
que esta medicion agrega es que, **en el eval set**, la norma correcta suele
llegar: el fallo dominante esta un nivel mas abajo. Los dos hechos no se
contradicen -- son conjuntos distintos -- pero si cambian el orden del trabajo.

El etiquetado de `eval_set_articulos.json` esta **pendiente de revision
juridica** segun su propia nota. Todo este anexo depende de el.

---

# Anexo: auditoria de chunking — ejecutada

Solo lectura, sin FAISS, sin GPU. Fuente:
`results/m3_s08_2026-10-09/rag_index_metadata.jsonl`, 11 975 lineas, verificado
contra el manifiesto: `huella_archivo` da **8cd72136235d6dfe**, que es el
`hash_metadata_indice` de S08 y S10. Es la metadata del indice evaluado, sin
CRLF.

## Lo que esta bien, y conviene decirlo primero

| | |
|---|---|
| Chunks con exactamente un articulo | **11 835 de 11 975 (98.8 %)** |
| Chunks sin articulo identificado | **0** |
| Articulos gold **ausentes del indice** | **0** |

Ese ultimo numero cierra dos hipotesis de golpe. En los 18 casos donde llega la
norma correcta y no el articulo, **el articulo gold siempre esta en el indice**.
No es cobertura, y no es perdida de extraccion (clase **E** de la matriz): el
texto esta ahi. El fallo es de recuperacion.

## El hallazgo: los articulos partidos fallan 3.6 veces mas

| | |
|---|---|
| Articulos distintos en el indice | 10 740 |
| Partidos en 2 o mas chunks | **1 231 — 11.5 %** (tasa base) |
| Partidos, entre los fallos de articulo del eval set | **22 de 53 — 41.5 %** |

Bajo la tasa base, de 53 observaciones se esperarian unos **6** articulos
partidos. Hay **22**. Los articulos partidos estan sobrerrepresentados entre los
fallos por un factor de **3.6**.

Los peores reparten un articulo en muchos pedazos: el articulo 135 del Codigo
de Policia en **7 chunks**, el 291 del CGP en **5**, el 597 del CGP en **4**.

## Y el mecanismo, que es lo accionable

Un articulo partido deja un chunk inicial y uno o varios de continuacion. De
los **2 069 chunks de continuacion** del indice:

| | |
|---|---|
| Conservan el encabezado "Articulo N" | **9 (0 %)** |
| **No** lo conservan | **2 060 (100 %)** |

Empiezan a mitad de frase. Ejemplos reales:

| chunk | es parte de | empieza |
|---|---|---|
| `constitucion_politica_1991::chunk40` | art. 42 | *"Los efectos civiles de todo matrimonio cesaran por divorcio..."* |
| `constitucion_politica_1991::chunk66` | art. 67 | *"administracion de los servicios educativos estatales..."* |
| `constitucion_politica_1991::chunk136` | art. 135 | *"debate no podra extenderse a asuntos ajenos al cuestionario..."* |

La metadata **si** sabe de que articulo es (`articulos_incluidos` lo trae, y por
eso la **cita** sale bien cuando el chunk se recupera). Pero el **texto que ve
el embedder no dice de que articulo es**. Para e5 y para BM25, ese chunk no
tiene ancla: ni el numero del articulo, ni su enunciado, ni su encabezado. Son
**2 069 chunks, el 17 % del indice**, semanticamente huerfanos.

Eso explica el patron del anexo anterior. El articulo vecino **si** tiene su
encabezado y es una unidad limpia, asi que gana la comparacion contra la
continuacion del articulo correcto. De ahi que 15 de 28 fallos caigan a cinco
articulos o menos del gold, y 6 traigan literalmente el contiguo:

| caso | norma | gold | estado del gold | trajo |
|---|---|---|---|---|
| 9056 | CGP | 597 | **partido en 4** | 593, 598, 599 |
| 9057 | CGP | 291 | **partido en 5** | 468, 470, 593 |
| 9004 | Ley 1751 | 6 | **partido en 5** | 10 |
| 9039 | Ley 1266 | 13 | **partido en 2** | 14, 16, 19-A |
| 9066 | Ley 1801 | 135, 140 | **partidos en 7 y 6** | — |

## Lo que esto NO explica

De los 53 fallos de articulo, **29 estan en su propio chunk, con encabezado, y
aun asi no se recuperan**. Mas de la mitad. Ejemplos: el art. 16 de la Ley 820
(9035), el art. 23 de la Constitucion (9064), los arts. 1546, 1602 y 1613 del
Codigo Civil (9067), el art. 87 de la Ley 115 (9058).

Asi que hay **dos problemas distintos**, y conviene no fundirlos:

1. **Continuaciones huerfanas** -- 22 de 53, con mecanismo identificado y
   correccion clara.
2. **Ranking de chunks limpios** -- 29 de 53, sin mecanismo identificado. Es
   aqui donde sigue haciendo falta 6.1 (acierto@k por articulo), porque la
   pregunta abierta es si esos chunks estan en el top-30 y quedan fuera del
   top-5, o si no aparecen en absoluto.

## Correccion propuesta y su prueba

| | |
|---|---|
| **Correccion** | que cada chunk de continuacion lleve su encabezado: anteponer al texto el numero y el enunciado del articulo, o un prefijo explicito de continuacion |
| **Componente** | el chunker (`tools/rag/chunk.py`), no el corpus: los `.md` estan bien |
| **Impacto esperado** | 22 de 53 fallos de articulo; en el eval set, hasta 18 casos |
| **Confianza** | **media-alta** en el mecanismo; la magnitud de la mejora no esta medida |
| **Riesgo de regresion** | cambia el texto de 2 069 chunks, luego `hash_indice` y `n_chunks`: obliga a recorrer S07, S08 y S10. Anteponer texto repetido tambien puede subir la similitud de chunks entre si y crear nuevos distractores |
| **Prueba de aceptacion** | acierto@5 **por articulo** sube de 21/45; y las categorias que hoy estan en 0.83 y 1.00 no bajan |

**Esto no se toca ahora.** Requiere reindexar, y reindexar exige cerrar primero
6.1 para no gastar la unica reconstruccion en una sola hipotesis.

## Limites de este anexo

1. Depende de `data/eval_set_articulos.json`, **pendiente de revision
   juridica** segun su propia nota.
2. Son **53 observaciones** de articulo sobre 45 casos. El exceso (22 frente a
   los ~6 esperados) es grande, pero los absolutos son pequenos.
3. No comprobe si la particion rompe la relacion entre un articulo y sus
   paragrafos o excepciones, que era la formulacion original de la sospecha en
   `docs/m3_cobertura_corpus.md`. Lo que esta medido es la perdida del
   encabezado, que es un mecanismo distinto y mas simple.
4. `MAX_TOKENS_PER_CHUNK = 350` no queda absuelto ni condenado: la particion es
   su consecuencia, pero no medi si un limite mayor reduciria los 1 231
   articulos partidos sin crear otros problemas.
