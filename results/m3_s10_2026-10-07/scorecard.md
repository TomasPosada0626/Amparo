# Scorecard M3 · S10 — ¿Que forma de responder es mejor?

Corrida: 2026-10-08 04:52-05:18 UTC (noche del 07 en Colombia) · commit
`21cd93c5` · `USE_LORA = True`, adaptador `130d8f65b6e34746` · indice
`4269a04083d935fd` · eval set `a5151999c2095d00` (45 gold + 30 adversariales) ·
NVIDIA A100-SXM4-80GB · juez Groq `openai/gpt-oss-120b`.

Primera corrida en que S10 ejecuta sus 17 celdas de codigo. La fase 5c llevaba
corridas sin medir nada: usaba `eval_records`, variable que no existe en este
notebook, y arrancaba con `NameError` (corregido en `90771f7`).

## Conclusion

**Las rutas agenticas no se pagan.** El modelo nunca eligio buscar y cuestan
2.2 veces la latencia.

```
una_pasada   5.7 s/consulta | pasos 0.0 | busco el modelo: 0 | forzada por codigo:  0
tool_use    12.4 s/consulta | pasos 1.0 | busco el modelo: 0 | forzada por codigo: 75
react       12.4 s/consulta | pasos 2.4 | busco el modelo: 0 | forzada por codigo: 75
```

En las 75 consultas, en las dos rutas, la busqueda la forzo el codigo. La
capacidad que justifica un agente -- decidir cuando y que buscar -- no se
ejercio ni una vez.

| Ruta | faith | c.prec | c.rec | a.rel | prud.adv | esc.gold | cita!gold | s/cons |
|---|---|---|---|---|---|---|---|---|
| una_pasada | 0.38 | 0.58 | 0.34 | **0.76** | 1.00 | 0.11 | 0.00 | **5.66** |
| tool_use | 0.31 | 0.56 | 0.32 | 0.76 | 1.00 | 0.11 | 0.00 | 12.42 |
| react | **0.40** | 0.57 | **0.35** | 0.66 | 1.00 | 0.20 | 0.02 | 12.44 |

tool_use baja faithfulness. ReAct sube faith pero cae en answer relevancy, se
escapa el doble en gold y es la unica con citas no respaldadas.

**Replicado.** El informe del 2026-09-27 (`results/m3_s10_rutas_2026-09-27.md`),
sobre un eval set distinto, concluyo lo mismo: una pasada recomendada por
defecto, agente a 2.3-2.4 veces la latencia sin ganancia medible. Dos corridas
independientes, dos poblaciones, misma conclusion.

## Fase 5c — ¿el RAG corrige las rutas?

Es la pregunta que M3 debe contestar antes de decidir si se reentrena M1. Ruta
incorrecta por tipo, excluyendo escapes (una respuesta que no orienta no puede
equivocarse de ventanilla), con IC de Wilson al 95 %:

| Sistema | gold | adversarial |
|---|---|---|
| referencias (calibracion) | 0/45 = 0.0 % [0.0-7.9] | 0/30 = 0.0 % [0.0-11.3] |
| base sin RAG | 1/45 = 2.2 % [0.4-11.6] | 0/30 = 0.0 % [0.0-11.3] |
| fine-tuned sin RAG | 2/45 = 4.4 % [1.2-14.8] | 1/30 = 3.3 % [0.6-16.7] |
| una_pasada (con RAG) | 0/40 = 0.0 % [0.0-8.8] | 0/26 = 0.0 % [0.0-12.9] |
| tool_use (con RAG) | 1/40 = 2.5 % [0.4-12.9] | 0/27 = 0.0 % [0.0-12.5] |
| react (con RAG) | 1/36 = 2.8 % [0.5-14.2] | 0/25 = 0.0 % [0.0-13.3] |

La direccion es la esperada: el fine-tuned sin RAG se equivoca de ventanilla en
4.4 % de los gold y el RAG de una pasada en 0 %.

**Pero los intervalos se solapan casi del todo** ([1.2-14.8] contra [0.0-8.8]).
Con 0 a 2 errores sobre 36-45 casos no hay con que distinguirlos. La afirmacion
"el RAG corrige las rutas" **no se sostiene con este eval set**: los errores de
ruta son demasiado raros para medir la diferencia. Para sostenerla hacen falta
mas casos adversariales de ruta, no mas corridas.

## El cuello de botella

Context recall 0.32-0.35 en las tres rutas, que usan la misma busqueda. Lo
recuperado cubre un tercio de lo que dice la respuesta de referencia. Es el
mismo numero que sale en S08 y en la corrida del 27-09: ni la ruta, ni el
prompt, ni el reranking lo mueven. Ver `docs/m3_cobertura_corpus.md`.

## Archivos

- `eval_records_{una_pasada,tool_use,react}_lora.json` — 75 registros cada uno,
  con `sistema` y `traza`.
- `latencias_lora.json`, `ragas_resumen_lora.json`, `run_manifest.json`.
- `ragas_checkpoint_*_lora.jsonl` — 45 filas cada uno.

La tabla de la fase 5c no quedo en archivo en esta corrida; el notebook ya la
guarda en `rutas_5c.json` a partir del commit `2fe3a63`.
