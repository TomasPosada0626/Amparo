# Cobertura del corpus frente al eval set

Medido sobre `results/m3_s08_2026-10-07/` (configuracion A denso, 45 casos gold,
context recall del juez Groq). El corpus indexa 10 normas que cubren 9
categorias (`tools/rag/corpus.py`, `CATEGORIAS_OBJETIVO`); el eval set pregunta
por 27.

## El numero

| | casos gold | recall 0 | recall promedio |
|---|---|---|---|
| Categorias del corpus | 24 | 8 (33 %) | 0.49 |
| Fuera del corpus | 21 | 11 (52 %) | 0.29 |

Casi la mitad del eval set pregunta por dominios que el corpus no indexa. Pero
el corte no es limpio: hay categorias cubiertas que recuperan pesimo y
categorias no cubiertas que recuperan bien. Por eso conviene separar los dos
problemas.

## Problema 1 -- normas que no estan

Ocho categorias con recall 0.00, todas fuera del corpus:

| Categoria | Casos | Norma que la cubriria | Estado |
|---|---|---|---|
| Derecho comercial | 2 | Codigo de Comercio (Decreto 410 de 1971) | **ya descargado**, marcado `FUERA_DE_ALCANCE` |
| Contratos empresariales (B2B) | 1 | Codigo de Comercio + Codigo Civil | **ya descargados**, ambos excluidos |
| Contratacion estatal y facturacion | 1 | Ley 80 de 1993 y Ley 1150 de 2007 | falta descargar |
| Derecho ambiental sancionatorio | 1 | Ley 1333 de 2009 | falta descargar |
| Licencias urbanisticas | 1 | Ley 388 de 1997 | falta descargar |
| Propiedad intelectual - marcas | 1 | Decision 486 de 2000 (CAN) | falta descargar |
| Educacion / debido proceso disciplinario | 1 | Ley 115 de 1994 | falta descargar |
| Derecho administrativo general | 1 | **ya cubierta** -- ver problema 2 | -- |

Tres de los ocho casos salen de archivos que ya estan en `data/corpus/normas/`
y solo hay que sacarlos de `FUERA_DE_ALCANCE`. Es el cambio mas barato.

## Problema 2 -- la norma esta y aun asi no se recupera

Esto no lo arregla ampliar el corpus, y es mas grave porque toca el nucleo del
producto:

| Categoria | Casos | Recall | Norma indexada |
|---|---|---|---|
| Derecho administrativo general | 1 | **0.00** | Ley 1437 (CPACA) |
| Despido | 2 | **0.12** | Decreto 2663 (Codigo Sustantivo del Trabajo) |
| Pensiones y seguridad social | 2 | **0.12** | Ley 100 de 1993 |
| Salud / EPS | 3 | **0.17** | Ley 100 + Constitucion |
| Accidentes de transito | 3 | 0.28 | Ley 769 (Codigo de Transito) |

Despido y Salud / EPS son dos de las nueve categorias que el corpus existe para
cubrir, y recuperan peor que varias categorias que nadie indexo. Caso concreto
ya documentado: el articulo 86 de la Constitucion (la tutela) no se recupera
para la pregunta 9102 en ninguna configuracion, estando indexado.

Candidatos a revisar, en orden de sospecha:

1. **El chunking.** Un articulo largo partido por `MAX_TOKENS_PER_CHUNK = 350`
   puede dejar la condicion en un chunk y la excepcion en otro.
2. **El piso de 0.82** (`RETRIEVAL_MIN_SCORE`) con `TOP_K = 5`: en 5 de los 45
   casos gold no pasa ningun chunk.
3. **El prefijo de e5**: consulta coloquial contra texto normativo es
   retrieval asimetrico, y es donde e5 deberia brillar. Si no lo hace en
   Despido, vale medir el embedding aparte del pipeline.

## Que NO es el problema

El reranking y la hybrid search no mueven esto: las tres configuraciones se
quedan sin contexto en los mismos 8 casos. Tampoco es el modelo -- la
faithfulness es 0.58 cuando el contexto sirve y 0.13 cuando no.

## Si se amplia el corpus

Cambia `hash_indice` y las cifras dejan de ser comparables con la corrida del
2026-10-07. Hay que recorrer S07, S08 y S10, en ese orden.
