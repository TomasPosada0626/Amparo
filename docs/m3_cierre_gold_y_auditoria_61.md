# Cierre del gold y auditoria 6.1

No se modifico el corpus, los notebooks, el codigo del pipeline, el chunker, el
indice, el dataset ni los resultados experimentales. No se reindexo, no se uso
GPU ni Colab.

Rama `m3.5`, HEAD `9a0e6bb` al empezar, arbol limpio.

---

# A. Gold aprobado y linea base

## Lo registrado

| clase | filas | dictamen | registrado |
|---|---|---|---|
| A — sostiene el acierto | 27 | si | **si** |
| B' — candidato a omision | 62 | si | **si** |
| B — caso fallido | 82 | si (agregado) | **no** |
| C — redundante | 46 | si (agregado) | **no** |
| **total** | **217** | | **89** |

| veredicto | filas |
|---|---|
| `responde` | 16 |
| `responde_parcial` | 26 |
| `no_responde` | 47 |
| `pendiente` | **128** |

Validador: "Sin problemas". El script escribe solo la clase que se le pide y
comprueba que las demas no cambien; la comprobacion cruzada hubo que
corregirla, porque comparaba estado absoluto y señalaba la clase A -- ya
adjudicada -- como problema al registrar B'.

## La limitacion, que es la razon de las 128 pendientes

**El dictamen de las clases B y C no se puede registrar fielmente tal como
esta.** `docs/m3_articulos_gold_dictamen_claseBC.md` da los veredictos de forma
**agregada** -- 64/15/3 en B y 38/8/0 en C -- mas las excepciones nombradas una
por una (las tres `no_responde`, los `responde_parcial` por ejemplo). **No deja
constancia de que veredicto corresponde a cada una de las 128 filas.**

Registrarlas exigiria que yo asignara fila por fila unos veredictos que ese
documento nunca publico individualmente y que, por tanto, Leonardo no reviso
individualmente. El prompt pedia detenerse antes de inventar; esto es ese caso.

Lo que hace falta para cerrarlas: publicar la enumeracion fila por fila de las
128 y someterla a revision. Es trabajo mecanico de mi parte, no juridico, pero
debe pasar por el mismo procedimiento.

**Ninguna de las 128 mueve el acierto@k**: por definicion de las clases, ni las
de B ni las de C son el unico punto de acierto de su caso.

## Correcciones de aritmetica en mis propios resumenes

Dos, del mismo tipo, y las dos en tablas de resumen y no en los veredictos:

| documento | decia | es |
|---|---|---|
| Dictamen clase A | 12 / 11 / 4 | **13 / 9 / 5** |
| Dictamen clase B' | 3 / 16 / 43 | **3 / 17 / 42** |

## La linea base

Config **A denso + enrutador**, piso 0.81, registros de
`results/m3_s08_2026-10-09/eval_records_config_a.json`:

| estado del gold | acierto@5 por articulo |
|---|---|
| Original | 21 / 45 (46.7 %) |
| Con clase A aprobada | 17 / 45 (37.8 %) |
| **Con A y B' registradas** | **20 / 45 (44.4 %)** |

Los siete casos que cambiaron:

| caso | cambio | motivo |
|---|---|---|
| 9040, 9051, 9064, 9069 | acierto -> fallo | su etiqueta era un acierto falso |
| 9004, 9009, 9066 | fallo -> acierto | omision añadida |

**Validacion cruzada independiente:** `results/busqueda_v2/` mide acierto@5 =
0.467 = **21/45** con el gold original, con otro piso (0.82) y otro commit.
Coincide con los 21/45 que dan los registros de S08. Dos artefactos distintos,
el mismo numero.

## Huellas

| artefacto | huella | estado |
|---|---|---|
| `data/eval_set.json` | `a5151999c2095d00` | **coincide** con `hash_eval_set` de S08, S10 y busqueda_v2 |
| `data/eval_set_articulos.json` | `fa6c05f6c7aabb42` | sin modificar en esta fase |
| `docs/m3_articulos_gold_validacion.csv` | `b88c8154c5a852e1` | nuevo tras el registro |
| `data/dataset.jsonl` | `db0b6e65126cab25` | coincide con `config.DATASET_SHA1` |
| metadata del indice | `8cd72136235d6dfe` | **coincide** con `hash_metadata_indice` |
| `hash_indice` | `19657d22583f93d0` | **declarado** en los tres manifiestos; **no verificable** (el `.faiss` no esta aqui) |
| `hash_corpus` | `1c552822959e2932` | reproducido desde los blobs de git |

El gold (`eval_set_articulos.json`) **no se modifico**: la linea base se calcula
aplicando los veredictos del CSV como filtro, no editando el archivo de
referencia.

---

# B. Auditoria 6.1

## Lo que se pudo medir, y es mas de lo esperado

Existia ya un artefacto con la medicion por articulo que no habiamos usado:
**`results/busqueda_v2/busqueda_2026-10-09.json`**. Trae `puesto_por_caso`: el
puesto en que aparece el articulo gold, caso por caso, en cuatro
configuraciones.

Su manifiesto declara `hash_indice = 19657d22583f93d0`, `hash_corpus =
1c552822959e2932`, `hash_metadata_indice = 8cd72136235d6dfe` y `n_chunks =
11975`: **los mismos que S08 y S10**. Esta medido sobre el indice congelado.

Con una diferencia de configuracion que hay que respetar: usa
`retrieval_min_score = 0.82` y S08/S10 usan `0.81`. **No son corridas
equivalentes** y no se mezclan sus cifras.

### Acierto por articulo, indice congelado

| configuracion | @1 | @3 | @5 | @10 |
|---|---|---|---|---|
| A denso | 0.222 | 0.289 | 0.333 | 0.511 |
| A denso + enrutador | 0.178 | — | 0.467 | 0.556 |
| B hybrid + enrutador | 0.289 | — | 0.489 | 0.600 |
| **C rerank + enrutador** | 0.244 | — | **0.533** | **0.644** |

### Distribucion del puesto del articulo gold

| configuracion | puesto 1 | 2-5 | 6-10 | fuera del top-10 |
|---|---|---|---|---|
| A denso | 10 | 5 | 8 | 22 |
| A denso + enrutador | 8 | 13 | 4 | 20 |
| B hybrid + enrutador | 13 | 9 | 5 | 18 |
| C rerank + enrutador | 11 | 13 | 5 | 16 |

### El resultado que separa ranking de representacion

> **34 de los 45 articulos gold aparecen en el top-10 de al menos una
> configuracion. Solo 11 quedan fuera en las cuatro.**

Para **76 %** de los casos el articulo esta recuperable a profundidad 10: el
contenido **si** esta representado de forma encontrable, y lo que falla es el
**ranking o la seleccion**. Eso responde la pregunta central de 6.1 en la
direccion del ranking, no de la representacion.

Los 11 que quedan fuera en todas: **9004, 9010, 9035, 9038, 9042, 9048, 9049,
9050, 9057, 9058, 9066**. Son los candidatos a problema de representacion, y
coinciden con los casos de la clase B donde el articulo gold responde de forma
casi literal (la prohibicion de depositos, el contrato realidad, la caducidad al
año, el retracto).

Dos de los 11 tienen mecanismo ya identificado: **9058** es el caso donde cuatro
de los cinco fragmentos entregados eran la palabra "Derogado", y **9066** tiene
en su gold los arts. 135 y 140 de la Ley 1801, **partidos en 7 y 6 chunks**, que
son los peores del indice.

### Fallos de ranking puro: el articulo queda a un puesto

| configuracion | casos en puesto 6-10 |
|---|---|
| A denso + enrutador | 9007 (9), 9009 (10), 9056 (10), 9063 (9) |
| C rerank + enrutador | 9032 (6), 9039 (9), 9061 (8), 9062 (8), 9064 (8) |

Son 4 y 5 casos que **se recuperarian subiendo el corte**, sin tocar nada mas.
No lo propongo como correccion: subir `TOP_K` mete 5 fragmentos mas de ruido en
el prompt y eso hay que medirlo, no suponerlo.

## La contradiccion, que corrige una recomendacion mia

| configuracion | acierto@5 por articulo | `context_recall` RAGAS |
|---|---|---|
| A denso | 0.333 | **0.394** |
| B hybrid | 0.489 | 0.382 |
| C rerank | **0.533** | 0.352 |

**Las dos metricas ordenan las configuraciones al reves.** En acierto por
articulo el rerank es el mejor con diferencia -- 0.533 frente a 0.333, un 60 %
relativo --; en `context_recall` era el peor.

En el informe de auditoria integral concluí (H12) que *"hybrid y rerank bajan el
recall, mantener `USE_RERANK = False`"*, apoyandome **solo** en RAGAS. **Esa
recomendacion queda en suspenso.**

Cual creer, con lo que sabemos:

- El acierto por articulo es **mecanico**: el articulo gold esta en el top-k o
  no. No interviene ningun juez.
- El `context_recall` lo produce el juez Groq, y de ese juez tenemos **42
  comparaciones pareadas inconsistentes sin explicar** en M2.
- Pero el acierto depende del **gold**, que acabamos de corregir en 7 filas, y
  las cifras de la tabla son con el gold **original**.
- Y los dos pisos son distintos (0.82 frente a 0.81).

Conclusion honesta: **la metrica mecanica merece mas credito que la del juez**,
y dice que el rerank ayuda sustancialmente. Pero no es una decision: es una
hipotesis que hay que medir con el gold aprobado y el mismo piso.

## El bloqueo, declarado

**No se pudo medir @30 ni @100.** El artefacto disponible tiene profundidad
**10**: su `puesto_por_caso` vale `None` cuando el articulo no esta en los
primeros 10, y eso no distingue "puesto 11" de "ausente".

Para los **11 casos** que quedan fuera del top-10 en todas las configuraciones,
la pregunta sigue abierta, y es justo la que decide si hay que tocar el chunker.

| | |
|---|---|
| Falta | `rag_index.faiss` (48 MB, solo en Drive) |
| Falta | `torch` y `faiss-cpu`, no instalados en esta maquina |
| `hash_indice` | declarado en los manifiestos, **no verificado contra el archivo** |

**No se sustituyo el indice por uno recreado ni se simulo la medicion.**

### Pasos minimos para desbloquearlo, en CPU

1. Confirmar en Colab que `hash_indice` del `.faiss` en Drive es
   `19657d22583f93d0`. Si no coincide, **detenerse**: no seria el indice
   evaluado.
2. `pip install faiss-cpu` y `torch` en su variante CPU. El embedding de 45
   consultas con `multilingual-e5-base` es CPU-viable; no hace falta GPU.
3. Recuperar con `k = 100` **sin piso de score** y sin reconstruir nada, usando
   `tools/rag/retrieve.py` con la configuracion de los manifiestos.
4. Registrar, por caso: el puesto del primer articulo gold **aprobado**, si
   llego por un chunk inicial o por uno de continuacion, y la norma de cada uno
   de los 100.
5. Guardar el resultado en `results/<corrida>/` con su manifiesto, y comparar
   contra los 20/45 de la linea base.

Umbral fijado **antes** de ejecutar: si en **6 o mas** de los 11 casos el
articulo gold aparece entre los 100 primeros, el diagnostico es **ranking** y el
chunker no se toca en esta reconstruccion.

---

# C. Defectos demostrados frente a hipotesis

## Demostrados, con evidencia y archivo

| | evidencia |
|---|---|
| 4 aciertos falsos en el gold | clase A aprobada; acierto@5 pasa de 21/45 a 17/45 |
| 3 omisiones en el gold | clase B' registrada; vuelve a 20/45 |
| 107 chunks que solo dicen "Derogado" | regla acotada con control en cero; 6 sitios del top-5 en 3 de 45 casos gold |
| 2 060 de 2 069 chunks de continuacion sin encabezado | metadata del indice |
| Art. 57 del CST anterior a la reforma de 2025 | lectura del `.md`; afecta a 4630 y 9051 |
| El verificador deja pasar la ley nombrada ausente | corregido en `9a0e6bb`; 1 hallazgo en 668 respuestas, 0 falsos positivos |
| El ranking explica la mayoria de los fallos | **34 de 45 en el top-10 de alguna configuracion** |

## Hipotesis, sin demostrar

| | por que no esta demostrada |
|---|---|
| El rerank mejora el acierto por articulo | medido con el gold original y otro piso; hay que repetir |
| Los encabezados ausentes explican los 11 casos restantes | solo 2 de los 11 tienen mecanismo identificado |
| `MAX_TOKENS_PER_CHUNK = 350` es la causa de la particion | no se ha medido que haria un limite mayor |
| `multilingual-e5-base` no alcanza para este dominio | no se ha medido contra otro modelo |
| El `context_recall` de RAGAS es fiable | los 42 comparativos inconsistentes de M2 siguen sin explicar |

## Conclusion anterior que esta fase deja sin efecto

**H12 del informe integral.** Decia que hybrid y rerank bajan el recall y que
conviene mantener `USE_RERANK = False`. Se apoyaba solo en `context_recall`. La
medicion por articulo dice lo contrario y es mecanica. **En suspenso hasta
medirlo con el gold aprobado y el mismo piso.**

---

# D. Plan de reconstruccion unica

No ejecutar. Cada cambio con su prueba de aceptacion fijada de antemano.

| # | cambio | evidencia | casos | beneficio esperado | riesgo de regresion | prueba de aceptacion | archivos | impacto en reproducibilidad |
|---|---|---|---|---|---|---|---|---|
| **1** | Excluir al ingerir los chunks cuyo contenido completo sea una derogatoria | 107 chunks; 6 sitios del top-5 en 3 de 45 gold y 7 en 3 de 30 adversariales | 9005, 9052, 9058 (gold) | libera sitios del top-5; en 9058 cuatro de cinco | bajo. El control da 0 exclusiones de articulos sin la palabra "derogad"; el art. 380 de la Constitucion se conserva | `n_chunks` 11 975 -> 11 868; 0 chunks-derogatoria; ninguna categoria hoy en 0.83-1.00 baja | `tools/rag/chunk.py` o `ingest.py` | mueve `hash_indice` y `n_chunks` |
| **2** | Reinyectar el encabezado del articulo en los chunks de continuacion | 2 060 de 2 069 sin encabezado; los articulos partidos fallan 3.6 veces mas | 22 de 53 fallos de articulo | ancla lexica y semantica para el 17 % del indice | **medio.** Texto repetido en 2 069 chunks puede subir la similitud entre si y crear distractores nuevos. **No medido** | acierto@5 por articulo sube sobre 20/45 sin que bajen Despido, Salud/EPS, Garantias, Acceso a informacion y Familia | `tools/rag/chunk.py` | idem |
| **3** | Revisar `TOP_K` o el piso | 4-5 casos con el articulo en puesto 6-10 | 9007, 9009, 9056, 9063 y otros | recupera casos que fallan por un puesto | **medio.** Mas fragmentos = mas ruido en el prompt; puede bajar la fidelidad | acierto@5 **y** faithfulness medidos a la vez; la segunda no baja | `tools/rag/config.py` | no mueve el indice |
| **4** | Reconsiderar `USE_RERANK` | acierto@5 0.533 frente a 0.333 | transversal | +20 puntos de acierto por articulo, si se confirma | **alto de diagnostico**: la evidencia contradice la de RAGAS | repetir con el **gold aprobado** y el **mismo piso**; que suba acierto@5 sin bajar faithfulness | `tools/rag/config.py` | no mueve el indice |
| **5** | Actualizar el art. 57 del CST | texto indexado sin los supuestos de 2025; afecta a 4630 y 9051 | 2 casos, y Despido/Relaciones laborales por frecuencia | elimina el unico defecto de vigencia demostrado | bajo en lo tecnico; **requiere fuente oficial y validacion profesional** | una consulta por licencia por citacion judicial recupera el art. 57 reformado | `data/corpus/normas/...2663_1950.md` | mueve `hash_corpus` y `hash_indice` |
| **6** | Separar en el front matter la fecha de conversion de la version del texto | `status: in_force` y `last_updated: 2026-10-08` en un texto de 2021 | transversal | que el metadato deje de inducir a error | ninguno funcional | el front matter declara la version | `data/corpus/normas/*.md`, `corpus_pdf.py` | mueve `hash_corpus` |
| **7** | Poblar o retirar `vigente` | `True` en los 11 975 chunks: no transporta informacion | transversal | que el campo signifique algo | ninguno | el art. 57 preexistente no figura como `vigente: True` | `chunk.py` | mueve `hash_indice` |

## Orden propuesto

**Antes de reconstruir** (no mueven el indice): ejecutar 6.1 completo (desbloqueo
de arriba); medir **4** con el gold aprobado; arreglar
`manifiesto.huella_directorio` y registrar `USE_ENRUTADOR` en el manifiesto.

**En la reconstruccion**: **1** y **7** siempre -- riesgo bajo y evidencia
clara. **2** solo si 6.1 muestra que los 11 casos tienen el articulo entre los
100 primeros por representacion y no por ranking. **5** y **6** cuando la fuente
oficial este verificada.

**Despues**: recorrer S07 -- cuya linea base **no existe en `results/`**, y hay
que registrarla o declararla inexistente --, S08 y S10, y publicar la tabla de
equivalencia de hashes.

**Congelado hasta medir:** el chunker, el corpus, el indice, el pipeline, el
split del dataset y cualquier reentrenamiento.

---

## Archivos y pruebas

**Modificados en esta fase:**

| archivo | que cambio |
|---|---|
| `docs/m3_articulos_gold_validacion.csv` | 89 filas registradas (A 27 + B' 62); 128 en `pendiente` |
| `tools/aplicar_dictamen_articulos_gold.py` | dictamen de B', firma por clase, y correccion de la comprobacion cruzada |
| `docs/m3_articulos_gold_dictamen_claseB.md` | correccion del resumen: 17 y 42, no 16 y 43 |
| `docs/m3_cierre_gold_y_auditoria_61.md` | este informe (nuevo) |

**Sin tocar:** corpus, notebooks, chunker, pipeline, dataset, indice,
resultados experimentales y `data/eval_set_articulos.json`.

**Pruebas ejecutadas:** la suite completa (**658 passed, 4 skipped**), el
validador del instrumento ("Sin problemas") y la simulacion de cada registro
antes de escribir.
