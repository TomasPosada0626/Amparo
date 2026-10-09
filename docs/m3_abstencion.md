# La abstencion esta descalibrada, y son dos problemas distintos

Corrida `m3_s10_2026-10-09` (commit `5c884760`, adaptador `8ce3cc2bc9306974`,
indice `19657d22583f93d0`, eval set `a5151999c2095d00`, 11975 chunks).

El hallazgo que cerro esta pregunta salio de la fase 5c de S10, que **nunca
habia ejecutado** antes del 2026-10-09 (un bug de variable la rompia en
silencio desde el 7 de octubre).

## Lo que parecia

Sobre los 103 ejemplos con contexto sintetico de `data/dataset_v2.jsonl`, el
modelo **no se abstiene nunca**: 0 de 35 casos B2, y en 25 de ellos cita un
articulo que estaba en el contexto pero no responde la pregunta. De ahi la
lectura de que al modelo le falta aprender a abstenerse.

## Lo que pasa con retrieval real

Lo contrario, y en los casos donde si hay que responder:

| | gold | adversarial |
|---|---|---|
| escapes | 27 de 45 (60 %) | 24 de 30 (80 %) |
| orientan | 18 | 6 |

En adversariales escapar es lo correcto y la prudencia sale 1.00. En gold,
escapar 60 % de las veces no lo es.

Medir esto bien importa: contar los escapes con la frase sin tilde
(`RESPUESTA_SIN_CONTEXTO`) da 8 en vez de 27, porque el modelo escribe
"informacion" con tilde. La medicion correcta es
`tools/evaluation/ragas_metrics.es_valvula_de_escape`, que acepta las dos
formas, y es la que usan la fase 5 y `domain_metric.resumen_por_modo`.

## Quien decide el escape

Ninguno de los 27 escapes en gold lo fuerza el pipeline:

```
lo decidio el MODELO         27
por codigo (umbral/citas)     0
```

Eso descarta tres causas:

- **no es el umbral** `RETRIEVAL_MIN_SCORE = 0.81`: ningun escape viene de ahi
  (`escape_por_codigo` es `null` en los 27);
- **no es el verificador de citas**: `citas_rechazadas` vacio en todos;
- **no es la cantidad de contexto**: 52 de 72 casos con 5 fragmentos escapan.

## El corte que reparte la culpa

Cruzando `escape` con `context_recall` por caso
(`ragas_checkpoint_una_pasada_lora.jsonl`), los 27 escapes en gold se parten:

| escapes en gold | n | de quien es |
|---|---|---|
| `context_recall = 0` | 13 | **de la recuperacion**. No habia nada que usar: abstenerse fue correcto. |
| `0 < recall < 0.5` | 5 | evidencia parcial. Debia responder esa parte y avisar del hueco. |
| `recall >= 0.5` | 9 | **del modelo**. La evidencia estaba y escapo igual. |

Seis de esos 9 tenian `recall = 1.00`: recuperacion perfecta y aun asi
respondio que no tenia informacion verificada (ids 9002, 9004, 9031, 9034,
9040, 9053).

Y cuando la evidencia esta, la decision es una moneda al aire: con
`recall >= 0.5`, **9 escapan y 9 orientan**.

El modelo no es del todo insensible a la evidencia -- el recall medio es 0.477
donde orienta y 0.340 donde escapa, y con `recall = 0` escapa 13 de 17 veces,
que es lo correcto -- pero no discrimina en el punto que decide.

## Las cuatro configuraciones

| config | gold | escapes | `recall=0` | escapa con evidencia | orienta con evidencia |
|---|---|---|---|---|---|
| A_denso | 45 | 27 | 17 | 9 | 9 |
| B_hybrid | 45 | 33 | 17 | **14** | 5 |
| C_rerank | 45 | 28 | 15 | 10 | 8 |
| una_pasada | 45 | 27 | 17 | 9 | 9 |

Dos cosas:

1. **Los 17 casos sin evidencia son casi los mismos en las cuatro.** Hibrido y
   reranking no los arreglan: no es un problema de ranking, es de que el corpus
   no tiene (o no trocea bien) lo que esos casos necesitan.
2. **B_hybrid es la peor en la decision que importa**: escapa 14 veces teniendo
   evidencia contra 5 que orienta, casi 3 a 1 en contra. A y una_pasada quedan
   9 a 9. Eso es una razon mejor para preferir A que "tiene el mejor recall",
   porque mide la calidad de la decision y no solo la recuperacion.

Los 17 `recall = 0` estan repartidos finos entre categorias (1 o 2 cada una, y
8 de ellas tienen solo 1 o 2 casos gold en total), asi que no es una norma
faltante: es cobertura ancha.

## Que arreglar, y que no

Son dos trabajos distintos y no se tocan:

- **Recuperacion** (13 escapes correctos + los 5 parciales): cobertura del
  corpus y troceado. Aqui entra la Ley 2466 de 2025, que el Codigo Sustantivo
  del Trabajo indexado no trae (`docs/m3_cobertura_corpus.md`).
- **Modelo** (9 escapes con evidencia, y los 0 de 35 en B2): dataset y prompt.
  El modelo decide escapar por algo que no es la suficiencia de la evidencia.

**No bajar el umbral ni subir TOP_K**: ningun escape viene del filtrado, asi
que aflojarlo solo agrega ruido.

**No reentrenar todavia** sin saber por que escapa con `recall = 1.00`. Un
dataset con mas ejemplos B2 empujaria hacia mas abstencion, que es el fallo
dominante en produccion.

## Lo que falta para cerrar el modelo

Comparar base y afinado con el mismo indice, prompt y eval set. Si el base no
escapa en esos 9 casos y el afinado si, el escape lo instalo el fine-tuning.
S07 corrio sobre el base pero con el indice de 3420 chunks, asi que no sirve
para comparar.

## Lo que esto explica

- **gold 1 de 45 en la fase 4b de M2.** 28 de los 44 fallos son escapes, no
  errores juridicos: se abstuvo cuando debia responder.
- **`faithfulness 0.51` con `n_faithfulness = 18`.** Se promedia solo sobre las
  que orientan, mientras recall y precision usan los 45. El codigo ya guarda
  los `n_`; el scorecard tiene que mostrarlos.
- **B3 0 de 13 en M1.** Nunca dijo que parte no estaba respaldada, y los 5 casos
  de evidencia parcial de aqui son el mismo comportamiento ausente.
