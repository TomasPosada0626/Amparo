# Corridas y adaptadores

Que hay, cual es el vigente de cada modulo, y como reconocer cada adaptador.

Sin esto hubo dos carpetas por modulo y nada decia cual leer: el 2026-10-09 se
calificaron las generaciones del 6 de octubre sin que nada fallara.

## Los adaptadores

Viven en Drive, en `Colab Notebooks/Amparo/`. **No estan en git**: solo su
`adapter_config.json`, dentro de la carpeta de resultados de cada corrida. Son
lo unico del proyecto que lleva version en el nombre, y ahi si corresponde: son
modelos distintos que coexisten.

| carpeta en Drive | hash | dataset | que es |
|---|---|---|---|
| `amparo-lora-adapter` | `8ce3cc2bc9306974` | 2291 (1536 + 755) | **v1, produccion.** Lo lee `config.DRIVE_ADAPTER_DIR` y lo usan M2 y M3. **No se toca.** |
| `amparo-lora-adapter-v2` | `82089e4a0d9612a7` | 2709 (+418 contrastivas) | **v2, pares contrastivos.** Evidencia de que esa intervencion no corrigio B2. No esta adoptado. |

Cada uno costo unas 4-5 horas de A100, y **ninguno se borra**: son resultados
experimentales, no versiones acumuladas del mismo archivo. v1 es el baseline
contra el que se mide todo y v2 es la prueba de una hipotesis descartada.

Sobra, y se puede borrar: cualquier copia fechada
(`amparo-lora-adapter-v2-2026-10-10`), que es identica a la carpeta sin fecha
cuando la corrida se hizo una sola vez.

El proximo adaptador se llamaria `v3`, y el notebook lo toma de la variable
`ADAPTADOR` en `colab/m1_finetune.ipynb`, con dos `assert` que impiden escribir
sobre `v1` o sobre la ruta de produccion.

## Corridas vigentes

| Modulo | Carpeta | Adaptador | Que mide |
|---|---|---|---|
| M1 (v1) | `m1_2026-10-09/` | `8ce3cc2b` | fine-tuning, 334 de validacion (231 sin contexto + 103 con) |
| M1 (v2) | `m1_v2_2026-10-09/` | `82089e4a` | la misma validacion, con los pares contrastivos |
| M2 | `m2_2026-10-09/` | `8ce3cc2b` | juez sobre 231 sin contexto, 75 del eval set, 103 con contexto |
| M3 S08 | `m3_s08_2026-10-09/` | `8ce3cc2b` | A/B/C de busqueda, 11975 chunks |
| M3 S10 | `m3_s10_2026-10-09/` | `8ce3cc2b` | RAG de una pasada, RAGAS, guardia de rutas |

Las de M2 y M3 comparten adaptador (`8ce3cc2b`) y eval set (`a5151999`), asi
que sus cifras se leen juntas. Las dos de M1 comparten la validacion exacta
-- mismos ids y mismo contenido, verificado -- asi que v1 y v2 se comparan
directo.

`busqueda_v2/` no es una corrida de modulo: es el barrido que justifica
`RETRIEVAL_MIN_SCORE = 0.81` y `USE_ENRUTADOR = True` en `tools/rag/config.py`.

## Cifras reemplazadas por un cambio de metodo

No son correcciones de datos: el modelo no cambio, cambio como se mide.

- **M1, "citas inventadas" 34.7 % / 27.5 %** (334 mezclados).
  `has_invented_citation` marca cualquier cita numerada, y 103 de esos 334
  traen contexto donde citar es lo correcto. Separado: sin contexto 12.6 % ->
  **0.0 %**; con contexto sin respaldo 1.9 % -> 2.9 %.
- **M2 fase 4b, B1 15/55 -> 24/55.** El criterio nombraba la norma por su slug
  (`LEY-1564-2012`) y el juez marcaba mal las citas que decian "Codigo General
  del Proceso".
- **Abstencion: `escape_en_gold = 0.60` contaba subcadenas.** Una respuesta que
  orienta y acota una duda contenia la frase y se contaba como escape completo.
  Con `es_abstencion_pura`, las abstenciones reales en gold son 8 de 45.

## Abierto

- **B2: 0 de 35 abstenciones literales en v1 y en v2.** La causa raiz esta
  demostrada: el dataset se contradice 594 veces en entrenamiento -- la misma
  pregunta con respuesta de fondo en los ejemplos sin contexto y con la frase
  de escape en los B2. El criterio paso a medir conducta y no la frase literal;
  la matriz caso por caso esta en `docs/m1_b2_matriz.md` y espera revision
  juridica.
- **Recuperacion: 17 de 45 casos gold con `context_recall = 0`.** Las 17 normas
  estan en el corpus; lo que falla es el ranking. C (rerank) las rescata mejor
  que la configuracion de produccion. Ocho no las encuentra ninguna.
- **Cara a cara vs juez compuesto**: compuesto 3.47 -> 4.121 a favor del
  afinado, pares 73 vs 106 a favor del baseline, 42 inconsistentes segun el
  orden. No es la longitud: entre los pares decididos la brecha es *mayor*
  donde gana el afinado.
- **Corpus**: el Codigo Sustantivo del Trabajo indexado no trae la Ley 2466 de
  2025 (`docs/m3_cobertura_corpus.md`).
- **Etiquetas gold**: `data/eval_set_articulos.json` dice "pendiente de
  revision juridica". Las cifras de recuperacion dependen de ellas.
