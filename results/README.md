# Corridas guardadas

Cual es la corrida vigente de cada modulo, y cual quedo atras y por que. Sin
esto hay dos carpetas por modulo y nada dice cual leer: el 2026-10-09 se
calificaron las generaciones del 6 de octubre sin que nada fallara.

**Nada se borra.** Casi todas estan referenciadas desde el codigo, los
notebooks o los docs -- `tests/evaluation/test_rutas.py` lee
`m1_2026-10-06/finetuned_results.jsonl` y `tools/rag/config.py` justifica sus
umbrales con `busqueda_v2/` -- y las que quedaron atras son la evidencia de por
que cambio un numero. Borrarlas convierte una correccion documentada en un
cambio inexplicable.

## Vigentes

| Modulo | Carpeta | Adaptador | Que mide |
|---|---|---|---|
| M1 | `m1_2026-10-09/` | `8ce3cc2b` | fine-tuning, 334 de validacion (231 v1 + 103 v2) |
| M2 | `m2_2026-10-09/` | `8ce3cc2b` | juez sobre 231 sin contexto, 75 del eval set, 103 con contexto |
| M3 S08 | `m3_s08_2026-10-09/` | `8ce3cc2b` | A/B/C de busqueda, 11975 chunks |
| M3 S10 | `m3_s10_2026-10-09/` | `8ce3cc2b` | RAG de una pasada, RAGAS, guardia de rutas |

Las cuatro comparten adaptador (`8ce3cc2bc9306974`) y eval set
(`a5151999c2095d00`), asi que sus cifras se pueden leer juntas.

## Quedaron atras

| Carpeta | Por que no es la vigente |
|---|---|
| `m1_2026-10-06/` | indice de 3420 chunks y dataset de 1536 (sin los v2). La lee `tests/evaluation/test_rutas.py`. |
| `m2_2026-10-06/` | juez sobre el adaptador anterior. Citada en `README.md` y `docs/m3_decisiones_rag.md`. |
| `m3_s07_2026-10-07/` | **corrio sobre el modelo base** (`USE_LORA = False`): no mide el afinado. Se guarda porque es la prueba de ese error. |
| `m3_s08_2026-10-07/` | indice de 3420 chunks, antes de las normas agregadas el 2026-10-08. |
| `m3_s10_2026-10-07/` | la fase 5c nunca ejecuto en esa corrida (bug de variable, arreglado el 2026-10-09). |
| `busqueda_v2/` | barrido de umbral y enrutador. No es una corrida de modulo: es lo que justifica `RETRIEVAL_MIN_SCORE = 0.81` y `USE_ENRUTADOR = True` en `tools/rag/config.py`. |

## Cifras reemplazadas por un cambio de metodo

No son correcciones de datos: el modelo no cambio, cambio como se mide.

- **M1, "citas inventadas" 34.7 % / 27.5 %** (334 mezclados). `has_invented_citation`
  marca cualquier cita numerada, y 103 de esos 334 traen contexto donde citar es
  lo correcto. Separado: v1 sin contexto 12.6 % -> **0.0 %**; v2 con contexto sin
  respaldo 1.9 % -> 2.9 %. La celda del desglose esta al final de
  `colab/m1_finetune.ipynb`.
- **M2 fase 4b, B1 15/55** -> **24/55**. El criterio nombraba la norma por su
  slug (`LEY-1564-2012`) y el juez marcaba mal las citas que decian "Codigo
  General del Proceso". Arreglado el 2026-10-09; B2 no cambia porque su criterio
  no nombra fuentes.

## Abierto

- **Abstencion descalibrada.** En los B2 sinteticos no escapa nunca (0/35, cita
  25 veces un articulo que no responde). Con retrieval real escapa de mas: en
  S10 `una_pasada` solo 18 de 45 gold orientan. No lo explica `n_retrieved`
  (32 de 72 casos con 5 fragmentos escapan), asi que falta saber que lo dispara.
- **B3 0/13**: nunca dijo que parte de la respuesta no estaba respaldada.
- **Cara a cara vs juez compuesto**: compuesto 3.47 -> 4.121 a favor del
  afinado, pares 73 vs 106 a favor del baseline, 42 inconsistentes segun el
  orden. No es la longitud: entre los pares decididos la brecha es *mayor*
  donde gana el afinado (190 vs 171.5 palabras medianas).
- **Corpus**: el Codigo Sustantivo del Trabajo indexado no trae la Ley 2466 de
  2025 (ver `docs/m3_cobertura_corpus.md`).
