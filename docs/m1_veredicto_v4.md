# Veredicto de v4 — prueba barata, 2026-10-13

> **Después de este veredicto**, Tomás quitó la abstención de los requisitos y
> M1 se cerró con v1 (`docs/m1_cierre.md`). La propuesta de v5 de abajo no se hizo.

**v4 no pasa la prueba barata y se descarta sin evaluación completa. v1 sigue en
producción.** Lo que v4 vino a corregir (H22: abstenciones que mandaban a la
autoridad equivocada) sí quedó corregido; la sobreabstención, que no era su
variable, quedó igual que en v3.

Todas las cifras salen de `results/m1_v4_2026-10-13/` y se recalcularon con
`python -m tools.evaluation.prueba_barata` sobre esos archivos: dan el mismo
veredicto que imprimió el notebook.

## La corrida

| | |
|---|---|
| corrida | `20261013-5a95ede7`, A100, commit `d45005a` |
| dataset | `5cec3fdf891260fd`: v3 + H22 (289 punteros de contrastivos) + H25 (4 B2 a mano) |
| revisión del modelo base | `a09a35458c702b33eeacc393d103063234e8bc28`, fijada |
| hiperparámetros | los de v1 y v3 (r=16, α=32, 3 épocas, lr 2e-4, seed 42) |
| entrenamiento | 49 min; `eval_loss` 1,287 → 1,226 → 1,219 (v3: 1,33 → 1,26 → 1,25) |
| adaptador | `101a9c9d945fad68` (`huella_archivo` del `.safetensors`); `dbd63a426dca4156` con `corrida.guardar_adaptador` |
| baseline | reusado de v3 tras la verificación registro por registro |

El historial completo de entrenamiento y el manifiesto quedaron en Drive
(`evaluacion/20261013-5a95ede7/`).

## La prueba barata

| fila | v4 | umbral | v1 ref. | v1 hoy (control) | v3 |
|---|---|---|---|---|---|
| suficiente: se abstiene | **25/55** | ≤ 6 | 4 | 5 | 22 |
| suficiente: cita el artículo que responde | **25/55** | ≥ 39 | 41 | 40 | 29 |
| parcial: dice que falta | 12/13 | ≥ 11 | 11 | 10 | 13 |
| irrelevante: se abstiene | 40/49 | ≥ 25 | 19 | 20 | 39 |
| irrelevante: cita sin respaldo | 0 | 0 | 1 | 1 | 0 |
| gold con RAG real: abstención pura | **30/45** | ≤ 10 | 10 | 8 | 30 |

**El control es válido**: v1, medido en la misma sesión, se separa de su
referencia en 2 casos como máximo (tolerancia: 3), con el mismo buscador y el
mismo índice. La cifra de v4 no es deriva del entorno.

## Qué cambió y qué no

**H22 se corrigió, que era lo que v4 venía a hacer.** Abstenciones que nombran
una Superintendencia, Secretaría o Ministerio:

| | gold | escenarios |
|---|---|---|
| v3 | 8 de 30 | 24 de 72 |
| v4 | **2 de 30** | **2 de 76** |

Ahí estaban 6 de los 9 fallos críticos de v1 reevaluado. 26 de las 30
abstenciones de v4 en gold encaminan a un consultorio jurídico universitario.

**La sobreabstención es la de v3, caso por caso.** De las 30 abstenciones en
gold, 29 son las mismas que las de v3. Separando por si el artículo que responde
llegó al contexto:

| | con el artículo delante | sin él |
|---|---|---|
| v1 (control de hoy) | 3 de 21 | 5 de 24 |
| v3 | 13 de 21 | 17 de 24 |
| v4 | 13 de 21 | 17 de 24 |

Con el artículo correcto delante, v4 se abstiene en 13 de 21: no es que la
búsqueda falle, el modelo no distingue un contexto útil.

## La lectura

Dos candidatos seguidos, con el mismo dataset salvo los punteros, se abstienen
igual. La sobreabstención viene de **cómo se distribuyen los modos en los
ejemplos con contexto**, no de los punteros:

| | ejemplos con contexto en train | de ellos, abstención | proporción |
|---|---|---|---|
| v1 | 652 | 228 B2 (contexto de otras categorías) | **35 %** |
| v3 y v4 | 941 | 228 B2 + 289 contrastivos (contexto de la misma categoría) | **55 %** |

En v3 y v4, ante un contexto de la materia correcta la respuesta más frecuente
del entrenamiento es abstenerse. El modelo aprendió esa proporción, no a leer si
el artículo está.

## Lo siguiente: v5, con una sola variable

**El número de contrastivos**, que es la hipótesis de Martín y la que esta
lectura apunta. Lo demás queda como en v4, incluidos los B2 con contexto de la
misma categoría (son los que enseñan a distinguir, y v1 no los tenía).

| contrastivos | proporción de abstención con contexto |
|---|---|
| 289 (v4) | 55 % |
| 100 | 43 % |
| 0 | 35 % (la de v1, con B2 más difíciles) |

La propuesta es **100**, estratificados por categoría. Es el punto medio: baja la
proporción hacia la de v1 sin perder del todo la señal de "la misma pregunta en
dos modos", que es para lo que se crearon los contrastivos. Mismo protocolo: se
entrena, se corre la prueba barata y, solo si pasa, la evaluación completa.
Requiere autorización de GPU (~70 min de A100).

**Lo que no se pide:** que v5 resuelva la búsqueda. El artículo correcto llega en
21 de 45 consultas (H23); D3 seguirá siendo difícil mientras eso no mejore, y esa
es la palanca de M3.
