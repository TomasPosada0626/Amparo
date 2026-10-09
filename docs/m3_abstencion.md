# Abstencion y recuperacion: lo que decian las metricas y lo que dicen los datos

Corrida `m3_s10_2026-10-09` y `m3_s08_2026-10-09` (commit `5c884760`, adaptador
`8ce3cc2bc9306974`, indice `19657d22583f93d0`, eval set `a5151999c2095d00`,
11975 chunks, 37 normas).

Este documento se reescribio dos veces. La primera version concluyo que el
modelo sobre-abstiene con retrieval real y que el problema grande era la
cobertura del corpus. **Las dos conclusiones eran errores de medicion**, y
quedan abajo con lo que las desmintio, porque el error es la parte util.

## 1. Abstenerse no es lo mismo que acotar una duda

`es_valvula_de_escape` busca la frase de escape como subcadena, asi que marca
igual dos cosas distintas: negarse a orientar, y orientar diciendo de paso que
hay algo que no se puede afirmar. El caso 9002 conto como escape:

> "El articulo 62 del Codigo Sustantivo del Trabajo permite terminar el
> contrato cuando el empleador incumple sistematicamente sus obligaciones...
> **No tengo informacion verificada** sobre como se valoran esas causales en un
> despido por presion. Reune el acta, mensajes y testigos."

Eso es exactamente lo que piden los ejemplos B3 del dataset.

`es_abstencion_pura` exige la frase **y** que la respuesta no cite ningun
articulo. Con esa medicion:

| config | gold: abstencion pura | orienta y acota | adversarial: abstencion pura | "escape" por subcadena (gold) |
|---|---|---|---|---|
| A denso+enrutador | 8/45 (18 %) | 19 | 20/30 (67 %) | 27/45 (60 %) |
| B hybrid+enrutador | 14/45 (31 %) | 19 | 22/30 (73 %) | 33/45 (73 %) |
| C rerank+enrutador | 14/45 (31 %) | 14 | 19/30 (63 %) | 28/45 (62 %) |
| `una_pasada` | 8/45 (18 %) | 19 | 20/30 (67 %) | 27/45 (60 %) |

`una_pasada` y `A denso+enrutador` coinciden porque son la misma
configuracion.

**El modelo discrimina**: en produccion se abstiene de verdad 3.7 veces mas en
adversariales que en gold (67 % contra 18 %), y 37 de 45 casos gold reciben
respuesta de fondo. La subcadena convertia eso en "60 % de escape en gold".

De las 8 abstenciones puras en gold, cruzadas con `context_recall`:

| | n |
|---|---|
| `recall = 0` | 5 |
| `0 < recall < 0.5` | 2 |
| `recall >= 0.5` | **1** |

**Una sola abstencion en 45 casos gold** ocurrio con evidencia razonable. Las 5
con `recall = 0` son correctas: no habia nada que usar.

Esto tambien corrige la lectura de B3 en M1 (0 de 13): la conducta de avisar
del hueco aparece en 19 de 45 casos con retrieval real. Lo que falla en B3 es
el formato que exige el criterio, no la conducta.

### Quien decide el escape

Ninguna de las respuestas con la frase en gold la fuerza el pipeline:
`escape_por_codigo` es `null` en las 27 y `citas_rechazadas` esta vacio. Asi
que **no es el umbral** `RETRIEVAL_MIN_SCORE = 0.81`, **no es el verificador de
citas** y **no es la cantidad de contexto** (52 de 72 casos con 5 fragmentos la
contienen). Bajar el umbral o subir TOP_K no toca nada de esto.

## 2. El corpus no es el problema; el ranking si

17 de los 45 casos gold tienen `context_recall = 0`. La primera version de este
documento concluyo que era cobertura del corpus, razonando que hibrido y
reranking no movian ese conteo. **El razonamiento estaba mal**: las tres
configuraciones reordenan el mismo fondo de candidatos, asi que fallar las tres
no distingue "no esta" de "no se encuentra".

Cruzando los 17 con las etiquetas de `data/eval_set_articulos.json`, que dicen
que articulo responde cada caso:

| | n |
|---|---|
| la norma esperada **no esta** en el corpus | **0** |
| esta, pero no se recupero el articulo | 16 |
| se recupero el articulo esperado y `recall` dio 0 igual | 3 |

**Las 17 normas estan todas indexadas.** Ni una falta. Y en 3 casos (9051,
9064, 9069) el articulo correcto si se recupero y RAGAS puntuo `recall = 0`:
una razon mas para no tratar `context_recall` como prueba de suficiencia.

### El ranking si mueve la aguja

`results/busqueda_v2/busqueda_2026-10-09.json` trae el puesto del articulo
esperado por caso:

| config | @1 | @3 | @5 | @10 | MRR |
|---|---|---|---|---|---|
| A denso | 0.222 | 0.289 | 0.333 | 0.511 | 0.283 |
| **A denso+enrutador** (produccion) | 0.178 | 0.356 | 0.467 | 0.556 | 0.281 |
| B hybrid+enrutador | **0.289** | 0.422 | 0.489 | 0.600 | **0.378** |
| C rerank+enrutador | 0.244 | **0.467** | **0.533** | **0.644** | 0.361 |

Y sobre los 17 casos con `recall = 0`, cuantos ponen el articulo esperado en el
top-5:

| A | A+enrutador | B hybrid | C rerank |
|---|---|---|---|
| 1 | 3 | **6** | **6** |

`USE_ENRUTADOR` se justifico comparando A contra A+enrutador (acierto@5 0.333
-> 0.467, ver `tools/rag/config.py`), y la medicion era correcta. Lo que no se
noto es que B y C ya eran mejores que A+enrutador, que es lo que corre en
produccion.

### Los 8 que ninguna configuracion encuentra

9010, 9035, 9038, 9042, 9049, 9050, 9058 y 9055 no aparecen en el top-10 de
ninguna configuracion (9055 solo con A denso puro, en el puesto 1, y se pierde
en las otras tres). El articulo esta indexado y ninguna estrategia de busqueda
lo saca. Ahi el trabajo es de embedding o de troceado, no de reordenamiento ni
de corpus.

## 3. La tension que queda

B y C encuentran el articulo esperado mas seguido (@5 0.489 y 0.533 contra
0.467) y a la vez **se abstienen mas** en gold (31 % contra 18 %). No tengo
explicacion medida para eso. La hipotesis a comprobar es que al cambiar que
fragmentos ocupan los 5 cupos, entran fragmentos mas precisos pero mas cortos,
y el modelo los lee como insuficientes.

No hay configuracion que domine: A responde mas en gold y recupera peor, C
recupera mejor y abstiene mas. Elegir exige decidir que se optimiza, y
conviene medirlo con `es_abstencion_pura` y acierto@5 juntos, no con
`escape_en_gold`.

## 4. Que hacer

1. **Probar hybrid+rerank en produccion.** Rescata 6 de los 17 casos sin
   evidencia contra 3 de la configuracion actual, y gana en @3, @5 y @10.
   Medir a la vez si la abstencion en gold sube.
2. **Los 8 casos que nadie encuentra**: revisar el troceado y el embedding de
   esas normas. No es cobertura.
3. **Las metricas publicadas**: `escape_en_gold = 0.60` y
   `escape_en_adversariales = 0.80` cuentan subcadenas. Reportar abstencion
   pura aparte, y mostrar los denominadores: `faithfulness = 0.51` se promedia
   sobre `n = 18`, no sobre 45.
4. **No reentrenar.** Una sobre-abstencion en 45 casos gold no lo justifica.

La Ley 2466 de 2025 sigue pendiente para lo laboral
(`docs/m3_cobertura_corpus.md`), pero **no explica ninguno de estos 17 casos**.

## Lo que no se cayo

**B2 en los ejemplos sinteticos: 0 de 35.** Ahi la frase de escape no aparece
ni una vez, asi que no es el fallo de medicion de la seccion 1. Con contextos
que traen articulos bien formados pero de otra materia, el modelo cita en 25 de
35 en vez de abstenerse. Es el unico hallazgo de abstencion que sobrevivio a
las dos correcciones.
