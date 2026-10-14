# M3 — Resultados de la corrida de Colab del 2026-10-14

S08 y S10 corridos según `docs/m3_plan_colab_2026-10-13.md`, en A100, con v1
(`8ce3cc2bc9306974`), el índice `19657d22583f93d0` y el eval set
`a5151999c2095d00`. Commit del código: `10175ce`. Resultados en
`results/m3_s08_2026-10-14/` y `results/m3_s10_2026-10-14/`, copiados byte a
byte de Drive (`rag/corridas_abc/` y `rag/corridas_s10/`).

## La decisión: se queda A

La regla fijada antes de correr (`tools/evaluation/decision_busqueda.py`):
adoptar C si la media de las cuatro métricas de RAGAS sube frente a A y ninguna
baja más de 0,03.

| | faithfulness | answer relevancy | context precision | context recall | **media** |
|---|---|---|---|---|---|
| **A** — denso + enrutador (producción) | 0,433 (n=37) | **0,695** | 0,587 | **0,430** | **0,536** |
| B — + híbrido | 0,448 (n=31) | 0,580 | 0,613 | 0,382 | 0,506 |
| C — + híbrido + reranker | 0,467 (n=31) | 0,583 | **0,627** | 0,373 | 0,513 |
| C − A | +0,034 | **−0,112** | +0,040 | **−0,057** | −0,024 |

C no sube la media y baja dos métricas más allá de la tolerancia: **A se queda
en producción** y `tools/rag/config.py` no cambia (`USE_HYBRID` y `USE_RERANK`
siguen en `False`). La decisión se recalculó en local con el mismo módulo y da
lo mismo que guardó Colab.

Por qué pierde C: pone el artículo correcto más arriba (lo medido en CPU, 25/45
frente a 21/45 en el top-5), pero el modelo se abstiene más con su contexto: 14
abstenciones puras en gold frente a 8 de A. Una abstención vale 0 en answer
relevancy, y eso es lo que hunde la media. La caída de answer relevancy (−0,11)
es mucho mayor que el ruido del juez (abajo), así que la decisión no depende de
él.

## Cómo responde el sistema que se entrega (A, una pasada)

| | 2026-10-14 | 2026-10-09 |
|---|---|---|
| gold que **cumplen** su criterio (juez Groq) | **2 de 45** (21 parcial, 22 no cumple) | 1 de 45 (17 parcial, 27 no cumple) |
| adversariales que cumplen | 6 de 30 (13 parcial, 11 no cumple) | 8 de 30 (11 parcial, 11 no cumple) |
| gold con errores jurídicos según el juez | 31 de 45 (59 errores) | — |
| abstención pura en gold | 8 de 45 | 8 de 45 |
| abstención pura en adversariales | 20 de 30 | 20 de 30 |
| prudencia en adversariales | 100 % | 100 % |
| citas no respaldadas en gold | 0 | 0 |
| rutas incorrectas con RAG | **0 de 45 gold, 0 de 30 adversariales** | 0 (sobre 18 y 6: excluía abstenciones, H22) |
| latencia media | 7,9 s | 7,9 s |
| RAGAS faithfulness | 0,433 sobre 37 de 45 | 0,510 sobre 18 de 45 (H5) |
| RAGAS answer relevancy | 0,695 | 0,337 |
| RAGAS context precision / recall | 0,587 / 0,430 | 0,558 / 0,394 |

**Las respuestas son las mismas que el 2026-10-09.** Los 75 textos de la
corrida de una pasada son idénticos a los de aquella fecha y a los de A en S08
(el archivo de A y el de una pasada tienen el mismo md5, `8890b0bb…`). Lo que
cambió es cómo se miden:

- **RAGAS con abstención estricta (H5).** Antes se excluían 27 respuestas por
  *contener* la frase de escape; ahora solo las 8 que son abstención pura. Por
  eso faithfulness pasa a medirse sobre 37 casos y answer relevancy deja de
  contar como 0 respuestas que sí responden: de 0,34 a 0,70. La cifra vieja no
  era una medida del sistema; esta sí.
- **El juez de criterio.** De 1 a 2 gold que cumplen y de 17 a 21 parciales,
  **con las mismas respuestas**: es variación del juez, no una mejora del
  sistema. La cifra honesta es "1 o 2 de 45".
- **Las rutas** ahora cuentan las 75 respuestas (antes excluían las
  abstenciones, H22). Con RAG no hay ninguna ruta incorrecta. La fila
  "fine-tuned sin RAG" pasa de 2/45 a 0/45 porque ahora sale de la corrida de M2
  cerrada (`results/m2_2026-10-09/`), no de la del 2026-10-06.

## El ruido del juez, medido

En una pasada se volvieron a juzgar 19 filas (las que cambian de clase con H5).
Con los mismos contextos, context precision pasó de 0,558 a 0,587 y context
recall de 0,394 a 0,430: hasta 0,04 de diferencia en el agregado solo por
volver a preguntar al juez. Es del orden de la tolerancia de la regla (0,03).
Esta vez no importa (C pierde por 0,11 en answer relevancy), pero una
comparación futura con diferencias de 0,03 no se puede leer sin repetir el
juicio.

## El reuso de checkpoints funcionó

Los checkpoints de RAGAS del 2026-10-09 se sembraron en Drive y la corrida los
retomó. Comparando cada checkpoint con el del 2026-10-09 (que es su prefijo
exacto):

| sistema | filas nuevas | reusadas de una pasada | tokens del juez gastados hoy |
|---|---|---|---|
| una pasada | 19 | 0 | 54 022 |
| A | 19 | 19 | **0** |
| B | 19 | 1 | 52 998 |
| C | 14 | 0 | 40 388 |

Unos 147 mil tokens de RAGAS en total, más las 75 llamadas del juez de criterio,
en vez de unos 440 mil sin reuso (cuatro sistemas a ~110 mil). **Ojo al leer `tokens_juez` en los
resúmenes** (115 284, 122 161, 120 958): es la suma de las filas vigentes del
checkpoint, incluidas las juzgadas el 2026-10-09, no lo gastado en esta sesión.

## Lo que esta corrida no resuelve

- **Responde bien 1-2 de 45 gold.** El cuello de botella sigue siendo la
  recuperación: el artículo que responde llega al contexto en 21 de 45
  consultas, y en 10 no está ni en el top-30. Reordenar (C) sube el acierto,
  pero el modelo responde peor con ese contexto; la regla lo descartó.
- **H11** (artículo 57 del CST) y **H13** (enrutamiento) siguen abiertos.

## Archivos

`results/m3_s10_2026-10-14/`:
`eval_records_una_pasada_lora.json`, `ragas_resumen_lora.json`,
`ragas_resumen_abc.json`, `decision_busqueda.json`,
`criterio_resumen_A_denso_lora.json`, `criterio_checkpoint_A_denso_lora.jsonl`,
`rutas_5c.json`, `latencias_lora.json`, `run_manifest.json` y los checkpoints de
RAGAS (`ragas_checkpoint_{una_pasada_lora,A_denso_8890b0bb,B_hybrid_d3b41e26,C_rerank_87c83feb}.jsonl`).
Los cuatro últimos de la lista vienen de `rag/corridas_abc/` en Drive; el resto,
de `rag/corridas_s10/`.
