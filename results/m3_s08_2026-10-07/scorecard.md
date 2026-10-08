# Scorecard M3 · S08 — ¿Que busqueda es mejor?

Corrida: 2026-10-08 03:10-03:21 UTC (noche del 07 en Colombia) · commit
`d7de3c0a` · `USE_LORA = True`, adaptador `130d8f65b6e34746` · indice
`4269a04083d935fd` (3420 chunks) · eval set `a5151999c2095d00` (45 gold + 30
adversariales) · NVIDIA A100-SXM4-80GB.

Tres configuraciones sobre las mismas 75 preguntas, mismo prompt y mismo
generador: **A** denso (e5), **B** + hybrid (BM25 + RRF), **C** + rerank
(cross-encoder).

## Conclusion

**Gana A, el denso puro.** Ni hybrid ni rerank pagan su costo, y esto invierte
la conclusion del 2026-09-27, que daba C como mejor.

| Config | Context recall | Context precision | Faithfulness | Answer relevancy | Latencia |
|---|---|---|---|---|---|
| **A denso** | **0.39** | 0.56 | **0.42** | 0.76 | 5.47 s |
| B + hybrid | 0.37 | **0.59** | 0.39 | 0.76 | 5.42 s |
| C + rerank | 0.34 | 0.58 | 0.38 | 0.76 | 5.57 s |

Metricas sin juez (de `tasas_de_escape` y `puntaje_de_record`):

| | A | B | C |
|---|---|---|---|
| Sin contexto (gold) | 8 (5) | 8 (5) | 8 (5) |
| Articulos por consulta | 3.87 | 3.81 | 3.73 |
| Gold que citan algun articulo | 2/45 | 1/45 | 2/45 |
| Gold con cita no respaldada | 0 | 0 | 0 |
| Prudencia en adversariales | 30/30 | 30/30 | 30/30 |
| Honestidad con las fuentes (0-1) | 0.747 | 0.740 | 0.747 |

## Por que cambio respecto al 27-09

El informe de entonces (`results/m3_s08_busqueda_2026-09-27.md`) no se
equivoco: midio sobre otro eval set, de 56 casos, 19 de cuyas preguntas gold
copiaban preguntas de la validacion de M1. El commit `4d68d86` las reemplazo el
2026-10-06 por 19 nuevas, mas compuestas a proposito.

Separando los 45 gold de esta corrida entre las 26 que sobrevivieron y las 19
nuevas:

| Config | recall, 26 viejas | recall, 19 nuevas |
|---|---|---|
| A denso | 0.50 | 0.25 |
| B + hybrid | 0.49 | 0.20 |
| C + rerank | 0.50 | **0.11** |

Sobre las preguntas viejas las tres empatan en recall y C es la mejor en
precision (0.67). **El reranker se desploma en las compuestas.** Explicacion
mecanica: el cross-encoder puntua pares (pregunta, chunk) y favorece el que
calza con el aspecto dominante, desplazando al que cubre el segundo. Una
pregunta que exige combinar dos cosas pierde una.

Sobre las 26 comparables el sistema no empeoro: recall 0.50 contra 0.42 el
27-09. La caida del agregado es la poblacion nueva, no una regresion.

## El hallazgo de fondo

En 19 de los 45 casos gold (42 %) el context recall es 0: la busqueda no trajo
nada util. Y eso arrastra la generacion:

| | faithfulness |
|---|---|
| Cuando el contexto servia (recall > 0) | 0.58 |
| Cuando no trajo nada util (recall = 0) | 0.13 |

El 0.42 agregado lo produce ese 42 %, no un modelo peor: 0.58 esta en el mismo
rango que el 27-09 (0.55-0.61).

De los 19 fallos, 11 preguntan por categorias que el corpus no indexa -- cubre
9 y el eval set pregunta por 27. El detalle y que normas faltarian estan en
`docs/m3_cobertura_corpus.md`.

**Las citas son un problema aparte.** Con el contexto perfecto (recall = 1) el
modelo cito en **0 de 9** casos; la tasa es plana en ~4 % sin importar la
calidad del contexto. No es retrieval: M1 entrena con 0 de 1536 ejemplos que
citen un articulo, y M3 le pide citar en el prompt.

## Archivos

- `eval_records_config_{a,b,c}.json` — 75 registros cada uno, mismas preguntas.
- `ragas_checkpoint_*_<huella>.jsonl` — 45 filas (el juez solo evalua gold). La
  huella del nombre es el md5 del `eval_records` de al lado: verificado que
  coinciden.
- `ragas_resumen_abc.json`, `run_manifest.json`.

Las latencias de esta corrida no quedaron en archivo; el notebook ya las guarda
en `latencias_abc.json` a partir del commit `2fe3a63`.
