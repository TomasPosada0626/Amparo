# M1 — Auditoría previa al entrenamiento candidato

**Commit auditado:** `dab242d` (rama `m3.5`, sincronizada con `origin`, árbol limpio).
**Fecha:** 2026-10-10. **Suite:** 744 passed, 4 skipped.
**Alcance:** gold, dataset, abstención, índice, corpus y código de entrenamiento y
evaluación (`colab/m1_finetune.ipynb`).
**Método:** cada afirmación verificada contra el repositorio en esta pasada, no
contra informes anteriores. Sin GPU, sin inferencia, sin cambios.

---

## Veredicto

> **Todavía no lista para el entrenamiento candidato.**
>
> El impedimento no está en el entrenamiento sino en la **evaluación**: el
> notebook mide la abstención con la instrucción de abstenerse **quitada del
> prompt**. Entrenar ahora gastaría GPU para obtener una cifra de B2 que no
> mide lo que se quiere medir. Y las líneas base del protocolo (1/35, 15/35)
> se midieron igual.

Todo lo demás —dataset, gold, índice, corpus, identidad de corrida— está en
orden y verificado.

---

## 1. Hallazgo crítico — la evaluación usa el system prompt equivocado

### Qué pasa

`evaluate()` construye cada generación con un único prompt:

```python
SYSTEM_PROMPT = records[0]['messages'][0]['content']   # celda 13
...
messages = [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': query}]
```

`records[0]` es el id 1, de origen `v1`: el prompt **sin contexto** (554
caracteres). Pero el dataset tiene **dos** prompts, y el entrenamiento usa el
de cada registro (`prompt: mensajes[:2]`, celda 22):

| | prompt sin contexto (v1) | prompt con contexto (v2, contrastivo) |
|---|---|---|
| longitud | 554 caracteres | 1350 caracteres |
| reglas para usar el CONTEXTO | no | sí |
| **instrucción de abstenerse** | **no** | **"Si el CONTEXTO no contiene información suficiente para responder con fundamento, responde exactamente con esta frase y nada más: 'No tengo información verificada…'"** |

De los 334 registros de validación, **103 tienen contexto** —55 B1, **35 B2**,
13 B3— y se evalúan con el prompt que no les corresponde. Los 35 B2 son
exactamente los que miden la abstención.

**El modelo se entrena con la instrucción de abstenerse y se evalúa sin ella.**

### Desde cuándo

Verificado en el notebook de los commits que produjeron las dos corridas
históricas, leyendo `git_commit` de cada `run_manifest.json`:

| corrida | commit | `SYSTEM_PROMPT` | `records[0]` |
|---|---|---|---|
| `m1_2026-10-09` (v1) | `7323227` | `records[0]['messages'][0]['content']` | id 1, `v1`, sin contexto |
| `m1_v2_2026-10-09` (v2) | `de7c4cc` | ídem | ídem |

### Qué invalida

| cifra | dónde se usa | estado |
|---|---|---|
| **0/35** abstención literal | diagnóstico de B2 | medida sin la instrucción |
| **1/35** `B2_funcional` | línea base del protocolo | medida sin la instrucción |
| **15/35** fallos críticos | umbral de lectura del protocolo | medida sin la instrucción |
| B1 y B3 sobre los 103 con contexto | métricas de citas | medidas con el prompt equivocado |
| las 231 sin contexto | todo lo demás | **correctas**: su prompt es el v1 |

**Lo que no invalida:** el diagnóstico del atajo. Que los B2 del dataset
tuvieran 0 % de contexto de su propia categoría está medido sobre los datos, no
sobre las respuestas, y la corrección de v3 sigue siendo necesaria.

**Lo que no sabemos:** cuánto del 0/35 era esto. Es posible que v1 se abstenga
bastante mejor con el prompt correcto, y es posible que no — el atajo es real.
Hoy no hay ninguna medición que lo distinga.

### Corrección y la decisión que abre

La corrección es de una línea, en CPU: usar el prompt del propio registro.

```python
messages = [item['messages'][0], {'role': 'user', 'content': query}]
```

**Pero abre una decisión que no es mía.** Un candidato evaluado con el prompt
correcto **no se puede comparar** con el 1/35 medido sin él: se confundiría el
efecto de corregir el prompt con el de reentrenar. Dos caminos:

| | qué es | coste | qué permite afirmar |
|---|---|---|---|
| **A** | re-evaluar el adaptador **v1 existente** con el prompt correcto, sin entrenar | inferencia: 103 generaciones, ~35 min en A100 | una línea base válida, **y saber si hace falta entrenar** |
| **B** | entrenar el candidato y medirlo contra el 1/35 | una corrida completa | nada sobre si v3 mejoró: la diferencia mezclaría dos cambios |

**Recomiendo A antes que nada.** Es más barato que entrenar y contesta la
pregunta que todo el plan de M1 da por respondida: si v1, con el prompt que le
dice que se abstenga, se abstiene. Si lo hace razonablemente, el candidato
cambia de objetivo. Si no, la línea base queda bien medida y el candidato se
compara contra algo real.

---

## 2. Hallazgo alto — el dev que elige la época ve el 63 % de sus preguntas en entrenamiento

### Qué pasa

La celda 22 recorta el dev de `train_records` al azar, estratificado por
categoría, para elegir la época. Pero el dataset tiene preguntas repetidas a
propósito: cada variante contrastiva comparte la pregunta con su original, y
cada ejemplo `v2` comparte la de su base `v1`. El recorte aleatorio las separa.

Reproducido con la semilla del notebook (42):

| | |
|---|---|
| fit / dev | 2113 / 179 |
| pares contrastivos partidos entre fit y dev | **51** de 335 |
| ejemplos de dev cuya pregunta exacta está en fit | **113 de 179 (63 %)** |

### Por qué importa

La celda 23 tiene `load_best_model_at_end=True` con `metric_for_best_model=
'eval_loss'`: **el dev decide qué época se queda como adaptador final**. Con dos
tercios de sus preguntas ya vistas, la pérdida de dev premia memorizar, y sesga
la elección hacia la época más memorizada.

**No contamina la validación final.** Los 334 se separan por pregunta
(`split_v2`) y ya está verificado: 0 contrastivas en validación y los mismos
334 ids que antes de reconstruir.

**Es preexistente**: los pares contrastivos existían antes de v3 (418).

### Corrección

En CPU: recortar el dev por **grupo de pregunta** (`base_id` / `par_de`), igual
que `split_v2` hace con la validación, para que un par caiga entero de un lado.

---

## 2b. Hallazgo alto — los 35 B2 de validación cambiaron de contenido (lo introduje yo)

Apareció al preparar la reevaluación de v1. **Es un defecto mío del commit
`33cc019`**: `rehacer_b2_a_mano` reconstruyó el contexto de los 263 B2 escritos a
mano, **incluidos los 35 que están en validación**.

| | |
|---|---|
| registros de validación con contenido distinto al de la base `9c9f5a9` | **35**, todos B2 |
| ids de validación | los mismos 334 |

En dos informes anteriores afirmé que la validación estaba intacta. **La prueba
en que me apoyaba comparaba ids, no contenido.** Los ids siguen siendo los
mismos; lo que dicen esos 35 registros, no.

**Qué implica:**
- la validación ya no es la misma sobre la que se evaluaron v1 y v2, justo en los
  casos que miden la abstención;
- las adjudicaciones de contexto de `m1_b2_adjudicacion.csv` se hicieron sobre
  los contextos viejos;
- un candidato evaluado sobre el dataset actual no sería comparable con v1.

**Qué NO afecta:** la reevaluación de v1, que lee los registros de la corrida
histórica. Ni el entrenamiento: los 228 B2 de entrenamiento sí debían cambiar.

**Estado:** documentado con una prueba `xfail(strict=True)` que se vuelve roja
cuando se corrija. **No lo corregí**: restaurar los 35 modifica el dataset y es
una decisión (decisión 7 del protocolo). La recomendación es restaurarlos.

---

## Estado de los arreglos (2026-10-10, mismo día)

| hallazgo | estado |
|---|---|
| 1. prompt de evaluación | **corregido** en CPU: `evaluate()` y el entrenamiento usan la misma `prompt_de()`; cada respuesta guarda `prompt_sistema` y `con_contexto`; `system_prompt()` falla si recibe prompts mezclados |
| 2. dev contaminado | **corregido** en CPU: `split_dev()` por grupo de pregunta. 0 preguntas compartidas con fit (antes 113 de 179), 0 pares partidos (antes 51) |
| 2b. 35 B2 de validación | **documentado, pendiente de decisión** |
| revisión del modelo base de v1 | **recuperada**: `a09a35458c702b33eeacc393d103063234e8bc28`, del historial de commits de HF |
| reevaluación de v1 | **preparada**: `tools/evaluation/reevaluacion_v1.py` y `colab/m1_reevaluacion_v1.ipynb`, probada con `--dry-run` |

---

## 3. Verificado y en orden

| área | comprobación | resultado |
|---|---|---|
| **Dataset** | huella sha1 contra `config.DATASET_SHA1` | `37e579ad0bfac6bd` = `37e579ad0bfac6bd` |
| | composición | 2626: `v1` 1536, `v2` 755, `contrastivo` 335; train 2292, val 334 |
| | puertas de calidad | 19 de 19 |
| | fuga en los tres controles | 0, 0, 0 |
| | validación respecto a la base | mismos 334 ids; 231 `v1` + 103 `v2` |
| | B2 con contexto de su propia categoría | 85 % (antes 0 %) |
| | atajo "si no hay nada de mi categoría, abstente" | −2,2 pts sobre la base (antes +41,3) |
| | contrastivos | 263 objetivos distintos, el más repetido 2 |
| **Entrenamiento** | truncamiento | **ninguno**: máx. 2596 tokens < `MAX_SEQ_LENGTH` 3072 |
| | pérdida | solo sobre la respuesta (formato prompt/completion) |
| | prompt de entrenamiento | el de cada registro ✓ |
| | hiperparámetros | r=16, α=32, dropout 0,05, q/k/v/o, 3 épocas, lr 2e-4, batch efectivo 16, semilla 42 — iguales a v1 |
| | revisión del modelo base | se exige y se pasa a las dos cargas |
| | identidad de corrida | firma de 6 campos + huella de pesos + guardado sin sobrescritura |
| **Índice** | `rag_index.faiss` | `19657d22583f93d0` ✓ en `artifacts/` |
| | `rag_index_metadata.jsonl` | `8cd72136235d6dfe` ✓ en `artifacts/` |
| **Corpus** | huella portable | `1c552822959e2932` ✓ |
| **Eval set** | `huella_archivo` | `a5151999c2095d00` ✓ — 45 gold + 30 adversariales |
| **Gold** | adjudicadas | 92 de 217 (A 27, B′ 62, B nombradas 3) |
| | pendientes que afectan acierto@k | **0** de 125 |
| **Adjudicación B2** | revisión jurídica | 35 de 35 cumplida; los 35 están en validación |
| **Regeneración** | `dataset_build.py` | se niega a escribir si el dataset ya existe ✓ |

---

## 4. Hallazgos menores

**Cuatro algoritmos llamados "la huella".** `config.huella_dataset` (sha1, CRLF
normalizado), `manifiesto.huella_archivo` (sha256, **sin** normalizar CRLF),
`dataset_v3.huella` (sha256 sobre registros canónicos) y
`corrida.huella_directorio` (sha256, CRLF normalizado). En esta auditoría casi
reporto una discrepancia del eval set que era solo un algoritmo distinto. Y
`huella_archivo` no normaliza CRLF con `core.autocrlf=true`: `eval_set.json`
está en disco con CRLF, así que su huella puede diferir entre Windows y Colab.
Hoy coincide; no está garantizado.

**Herramientas con texto obsoleto.** `dataset_build.py` habla de "418
contrastivas". `dataset_contrastivo.py` sigue generando los contrastivos viejos
—11 objetivos, regla B2 histórica— a un archivo de revisión. No tocan el
dataset, pero confunden a quien las lea.

---

## 5. Pendientes conocidos que no bloquean entrenar

| pendiente | impacto | paso mínimo |
|---|---|---|
| 18 marcas del gold B/C | 0 en acierto@k; solo el techo de suficiencia | marcar en `docs/m3_articulos_gold_bc_para_marcar.md` |
| 71 variantes `MISMO_CAPITULO` | riesgo residual documentado | revisión jurídica opcional |
| 28 B2 `AFINIDAD_ALTA_REVISAR` | posible pregunta con respuesta en el corpus | revisión jurídica opcional |
| art. 57 del CST desactualizado | casos 9051 y 4630 | única corrección que exige reconstruir el índice |
| 64 fragmentos derogatorios | 6 puestos en 3 casos gold | filtro posterior a la recuperación; **no implementado** |
| regresión de rutas | base 4 → v1 6 → v2 8 | medida, sin corregir |
| 4 categorías no enrutables | auditoría 6.1 | enrutador |
| puerta de suficiencia | sin negativos adjudicados no hay precisión | adjudicar las 75 respuestas guardadas |
| prueba de 4 escenarios con recuperación real | diseñada | GPU |
| **urgencias** | **fuera de alcance** por decisión de producto | el entrenamiento no demostrará seguridad ante urgencias |

---

## 6. Orden recomendado

```
1. [CPU]        corregir evaluate(): prompt del propio registro
2. [CPU]        recortar el dev por grupo de pregunta
3. [decision]   A o B de la seccion 1
4. [GPU, infer] si A: re-evaluar v1 con el prompt correcto (~35 min)
5. [decision]   con esa cifra, confirmar o reajustar el objetivo del candidato
6. [GPU]        entrenar el candidato sobre data/dataset.jsonl
7. [abogado]    adjudicar las respuestas nuevas
8. [CPU]        las diez dimensiones del protocolo, contra una linea base valida
```

Los pasos 1 y 2 son pequeños, en CPU y con prueba. El 3 es tuyo.
