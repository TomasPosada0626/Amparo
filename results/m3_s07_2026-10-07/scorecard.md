# Scorecard M3 · S07 — RAG ingenuo

Corrida: 2026-10-07 18:02 UTC · commit `9aa992a` · **modelo base, sin adaptador**
(`USE_LORA = False`) · indice `4269a04083d935fd` (3420 chunks) · eval set
`a5151999c2095d00` (75 casos: 45 gold + 30 adversariales).

El manifiesto de esta carpeta se reconstruyo el 2026-10-08: la celda no se
ejecuto durante la corrida. Sus hashes si son los de la corrida; lo que
describe la sesion de regeneracion esta separado bajo `reconstruccion`.

## Conclusion

El retrieval denso recupera 4.0 chunks por consulta y deja 8 de 75 sin ningun
contexto (3 de ellas adversariales, donde no traer nada es lo correcto). A
9.8 s por consulta.

El resultado util de S07 no son esas cifras sino el analisis del umbral, que
sostiene el valor de `RETRIEVAL_MIN_SCORE` para S08 y S10.

## El umbral de la valvula de escape

| | n | min | mediana | max |
|---|---|---|---|---|
| Consultas CON cobertura real | 20 | 0.822 | 0.842 | 0.879 |
| Consultas SIN cobertura | 2 | 0.847 | — | 0.856 |

**Los dos rangos se solapan.** El minimo de las que si tienen cobertura (0.822)
queda por debajo del maximo de las que no (0.856), asi que ningun corte separa
los dos grupos: un umbral que deje pasar todas las buenas deja pasar tambien
las malas. El valor vigente, 0.82, esta elegido por debajo del minimo medido de
cobertura real para no repetir el problema de 0.855, que dejaba al 84 % de las
consultas sin chunks.

La consecuencia practica es que el umbral solo no alcanza como guardia: hay que
anotar la consulta como fallida, no confiar en que el score la separe.

## Comparabilidad

S07 corrio con el modelo **base** y S08/S10 con el adaptador de M1. Las cifras
de generacion (citas, escapes, respuestas) no son comparables entre ellos.

Las de retrieval si, y se cruzan: S07 reporto 8 consultas sin contexto y 4.0
chunks por consulta; S08 en configuracion A denso dio 8 y 4.04 sobre el mismo
indice y el mismo eval set. El retrieval no depende del modelo, y los numeros lo
confirman.

## Archivos

- `rag_eval_base_2026-10-07_180254.jsonl` — 75 registros en formato Ragas.
- `run_manifest.json` — reconstruido, ver arriba.
