# M3, paso 7 — Por qué la búsqueda no trae el artículo, y qué lo arregla (2026-10-14)

Meta fijada antes de medir (`docs/m3_protocolo_aceptacion.md`, 2): el artículo
correcto en el top-5 en **≥ 28 de 45** gold. Hoy: 21 con el piso de producción
(0,81), 20 sin piso.

## 1. Diagnóstico: dónde se pierde el artículo

El camino de una consulta: e5 la convierte en vector y trae los fragmentos más
parecidos; el enrutador adivina el tema y pone primero las normas de ese tema;
los 5 primeros van al modelo. Para las 25 gold en que el artículo no llega al
top-5 (sin piso), se siguió el camino caso por caso:

| dónde se pierde | casos |
|---|---|
| está entre los 50 primeros, pero no entre los 5 (orden) | 12 |
| la búsqueda densa no lo trae ni en los 50 primeros | 8 |
| el enrutador se equivoca de tema (p. ej. una fotomulta → Arriendo / Embargos) | 3 |
| al tema le falta una norma (ruido → Código de Policía; pasajero de taxi → Código de Comercio) | 2 |

**Hallazgo central:** en 19 de esas 25, la búsqueda **sí trae la norma correcta**
(casi siempre en el puesto 1), pero no el artículo. e5 reconoce de qué tema es la
pregunta, no qué artículo la responde. Lo que falta es una pieza que elija el
artículo dentro de la norma: un reordenador (cross-encoder) que lea la pregunta
y el artículo juntos.

Además, aun con el artículo en el top-5, el modelo responde bien solo 9 de 21
(juez del RAG): elige otro fragmento, omite ante quién acudir o se niega. Eso no
lo arregla la búsqueda; es el bloque de servicio del prompt (paso 4).

## 2. Cómo se mide

Siempre la misma vara: las 45 gold, las etiquetas aprobadas
(`auditoria_61.gold_aprobado`), puesto del primer artículo gold, **sin piso**
(el piso está calibrado sobre la escala de e5-base). Una sola variable por
medición. Control: producción da 7/16/20/25 en @1/@3/@5/@10 sin piso y 21 con
0,81, igual que `results/m3_busqueda_cpu_2026-10-13/`. El conjunto de
confirmación (26 preguntas nuevas) no se mira hasta el final.

Herramientas: `tools/rag/experimento_embeddings.py` (modelo de embeddings,
opciones de `retrieve`) y `tools/rag/experimento_rerank.py` (reordenadores, en
tres pasos para que quepan en un PC de 8 GB).

## 3. Resultados (top-5 de 45, sin piso)

| | qué cambia | @1 | @3 | **@5** | @10 | |
|---|---|---|---|---|---|---|
| producción | — | 7 | 16 | **20** | 25 | control |
| R1 | el enrutador no puede excluir las normas de los 3 primeros densos | 9 | 14 | **17** | 22 | **descartado**: arregla 9055, rompe 5 |
| reordenador actual (mmarco MiniLM) | reordena los 30 primeros | 10 | 18 | **22** | 27 | referencia (C sin híbrido) |
| **R2** | **bge-reranker-v2-m3** reordena los 30 primeros (lee el texto) | **16** | **22** | **27** | **32** | +7 en el top-5; gana 11, pierde 5 frente a producción |

R2 confirma el diagnóstico: la búsqueda traía la ley y faltaba quien eligiera el
artículo. El artículo correcto queda primero en 16 casos (7 en producción). Gana
9007, 9035, 9039, 9040, 9043, 9046, 9056, 9060, 9063, 9068 y 9069; pierde 9004,
9032, 9053, 9059 y 9066. Con 45 preguntas la diferencia no es concluyente por sí
sola (11 contra 5): la confirman o no las 26 preguntas nuevas en la corrida final.

R1 se fijó con N=3 antes de medirlo y no se ajusta mirando las 45. Al abrir las
normas de los primeros densos se cuelan fragmentos de otras normas que empujan
hacia abajo los de la norma correcta.

Las demás variantes, medidas con la misma vara:

| | qué cambia | @1 | @3 | **@5** | @10 |
|---|---|---|---|---|---|
| R2 con cita | el reordenador lee norma, artículo y capítulo | 15 | 21 | **27** | 33 |
| R4 | la búsqueda densa usa la pregunta + un borrador de respuesta del modelo (las respuestas sin RAG de M2) | 11 | 19 | **21** | 28 |
| R4 + R2 | borrador y reordenador fuerte | 17 | 22 | **27** | 30 |
| R2 con el piso de producción (0,81) | | 15 | 22 | **27** | 29 |

R3 (e5-large) quedó en pausa en la parte 9 de 47: el PC de 8 GB no da para
construir su índice y medir los reordenadores a la vez, y con R2 ya resuelto el
problema principal (el orden) no se justifica esperar 3 horas más.

## 4. Decisión (regla del protocolo, sección 3)

**Pasa a GPU R2: bge-reranker-v2-m3, leyendo el texto.** Es el de más aciertos
en el top-5 (27, frente a 20 de producción: +7). Empata en el top-5 con R2 con
cita y con R4 + R2; gana el desempate por el top-3 (22 frente a 21) y, frente a
R4 + R2, por cambiar menos cosas (R4 exige generar un borrador antes de buscar,
unos 3-4 s más por consulta). Con el piso de producción conserva los 27.
Queda en `results/m3_paso7_2026-10-14/busqueda_elegida.json`.

No se probaron combinaciones nuevas después de ver estas cifras: elegirlas
mirando las mismas 45 sería ajustarse a ellas. R2 y R4 aciertan conjuntos
distintos (entre los dos, 32 de 45), así que hay margen, pero tendría que
medirse sobre preguntas nuevas.

Elegir para GPU no es adoptar: se adopta solo si pasa la regla de búsqueda con
las respuestas generadas y se confirma en las 26 preguntas nuevas
(`colab/m3_paso7_corrida_final.ipynb`, prueba de humo `tools/humo_paso7.py`).

## 5. Corrida final en GPU (2026-10-14, A100)

`colab/m3_paso7_corrida_final.ipynb`, commit `54fd2f0`, adaptador v1
`8ce3cc2bc9306974`, indice `19657d22583f93d0`, eval set `a5151999c2095d00`.
Archivos en `results/m3_paso7_2026-10-14/corridas/` (bajados de Drive; 7 archivos
completos, sin repetidos, cada sistema con sus opciones). Evaluado en CPU con
`tools/evaluation/evaluar_paso7.py`; A sobre el eval set es la corrida de S10 del
2026-10-14 (determinista).

| sistema | eval set: articulo en top-5 | **eval set: gold bien respondidas** | no cumple | abstencion pura | **26 nuevas: articulo** | **26 nuevas: bien respondidas** |
|---|---|---|---|---|---|---|
| A (produccion) | 21 | **13** | 10 | 8 | 16 | **7** |
| A + bloque de servicio | 21 | 15 | 13 | 15 | 16 | 10 |
| **R (bge-reranker-v2-m3)** | **27** | **16** | **4** | 8 | **19** | 11 |
| R + bloque de servicio | 27 | 15 | 7 | 10 | 19 | **13** |

**Contra la meta** (`docs/m3_protocolo_aceptacion.md`, 2):

- Busqueda, >= 28: **27. No se alcanza, por 1.** En las preguntas nuevas sube de
  16 a 19: la mejora no es un ajuste a las 45.
- Respuesta, >= 18: **16 con R. No se alcanza, por 2.** La subida (+3) esta en el
  borde del ruido medido del juez (1 a 3). En las preguntas nuevas, 7 -> 11.
- Lo que mas mejora: las respuestas que **no cumplen** bajan de 10 a 4.

**El bloque de servicio no se adopta tal como esta.** Una variable por vez:
A -> A_servicio da +2 cumple pero +3 no cumple y casi duplica las abstenciones
(8 -> 15); R -> R_servicio da -1 en el eval set y +2 en las nuevas. Mezclado y
dentro del ruido, y empuja al modelo a negarse, lo contrario de lo que buscaba.

**Donde esta ahora el cuello de botella.** Con R, el articulo llega en 27 gold;
de esas, 10 cumplen, **15 son parciales** y 2 no cumplen. La busqueda dejo de
ser el problema principal: con el articulo en la mano, el modelo responde a
medias (omite la via o la entidad, o se apoya en otro fragmento). Eso no lo
arregla otra busqueda ni este prompt; es del modelo.

**Adopcion de R en produccion:** cumple tres de las cuatro condiciones (no
empeora en las nuevas: 16 -> 19 y 7 -> 11; el juez lo da mejor que A: 16 frente
a 13). Falta la regla de RAGAS (media mayor que A, ninguna metrica baja mas de
0,03), que gasta Groq (~110 mil tokens) y espera autorizacion.

## 6. Adopcion (2026-10-14)

RAGAS de R sobre las 45 gold, con el mismo juez y el mismo codigo que S10
(`results/m3_paso7_2026-10-14/corridas/ragas_resumen_A_vs_R.json`, 120 682
tokens del juez):

| | faithfulness | answer relevancy | context precision | context recall | **media** |
|---|---|---|---|---|---|
| A (produccion anterior) | 0,433 | 0,695 | 0,587 | 0,430 | 0,536 |
| **R** | 0,438 | 0,689 | **0,770** | **0,490** | **0,597** |

Sube la media y ninguna metrica baja mas de 0,03 (la que mas baja: answer
relevancy, -0,006). Con eso R cumple las cuatro condiciones del protocolo
(seccion 3): regla de RAGAS, no empeora en las preguntas nuevas (articulo 16 ->
19, juez 7 -> 11), el juez no lo da peor (13 -> 16) y la busqueda sube (21 ->
27). **Adoptado**: `config.USE_RERANK = True`, `RERANK_MODEL_ID =
"BAAI/bge-reranker-v2-m3"`, `RERANK_CON_CITA = False`. Latencia: 7,2 -> 8,5 s por
consulta en A100.

Coherencia con M1: el constructor del dataset (`dataset_v2.Buscador`) usa ahora la
misma bandera, asi que si el dataset se reconstruye sus contextos salen del
buscador que sirve (H4). El dataset actual no se reconstruyo: v1 se entreno con
contextos sin reranker, y en servicio recibe contextos mejores.

La meta no se alcanzo (27 de 28 en busqueda; 16 de 18 en respuesta). Con el
articulo en el contexto, el modelo responde bien 10 de 27 y a medias 15: lo que
falta es del modelo, no de la busqueda.
