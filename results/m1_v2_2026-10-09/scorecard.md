# Scorecard M1 v2 · 2026-10-10 — Pares contrastivos

Commit `de7c4cc` · adaptador `82089e4a0d9612a7` · dataset `data/dataset_m1_v3.jsonl`
(2709 = 1536 v1 + 755 v2 + 418 contrastivas) · eval set `a5151999c2095d00` ·
validacion de 334, **los mismos ids y el mismo contenido que v1** ·
NVIDIA A100-SXM4-80GB · QLoRA 4-bit, 3 epocas, seed 42.

Los 12 hiperparametros y la configuracion del LoRA son identicos a v1,
verificado clave por clave: 0 diferencias. **Lo unico que cambia es el
dataset.**

## Conclusion

**La hipotesis no se confirma. B2 sigue en 0 de 35.**

Los pares contrastivos se disenaron para romper un atajo concreto: en v1, de
las 601 preguntas base con contexto en entrenamiento solo UNA aparecia en mas
de un modo, asi que el modo era predecible desde la pregunta y el modelo podia
memorizarlo en vez de leer el contexto. Con las 418 variantes, 402 preguntas
aparecen con contexto suficiente y con contexto insuficiente.

**Funcionaron para lo que fueron disenados**, y aun asi no bastaron:

| B2 (35 casos) | v1 | v2 |
|---|---|---|
| **abstenciones (frase de escape)** | **0** | **0** |
| citan un articulo que no responde | 25 | **19** |
| no citan nada | 10 | **16** |
| arrancan con "No" | 15 | 19 |

El modelo si condiciona mas en el contexto: dejo de citar articulos
irrelevantes en 6 casos (-24 %) y 16 de 35 ya no citan nada. Las respuestas sin
cita son razonables -- "No te puedo decir cuanto cuesta porque depende de la
entidad que lo emite y de tu situacion".

Lo que no aprendio es a emitir la frase entrenada. Eso separa dos cosas que
antes estaban juntas en una sola cifra:

1. **discriminar contexto suficiente de insuficiente** -> mejoro;
2. **producir el formato de abstencion** -> cero, sin moverse.

## Nada se rompio

| | base | v1 | v2 |
|---|---|---|---|
| cita de memoria (231 sin contexto) | 29/231 = 12.6 % | **0/231** | **0/231** |
| cita sin respaldo (103 con contexto) | 2/103 | 3/103 | 3/103 |
| nombra ruta legal | 94.9 % | 96.7 % | 95.2 % |
| entidades inventadas | 11.4 % | 3.0 % | **2.7 %** |
| integridad (idioma / formato) | 4/334 | 0/334 | **0/334** |
| B1 citan | — | 55/55 | 54/55 |
| B3 citan | — | 12/13 | **13/13** |
| palabras (media) | 234 | 52 | 50 |

El patron de negacion **no se contagio** a donde no debe: B1 pasa de 1 a 2
respuestas que arrancan con "No", y los 231 sin contexto de 18 a 17.

**Truncamiento, con la medicion nueva: `motivo_fin = {termino: 334}`.** Las 334
cerraron con el token de fin de secuencia; cero cortadas, cero salidas vacias,
cero presupuestos agotados. En v1 esto no se registraba y hubo que descartarlo
acotandolo por longitud de palabras.

## Entrenamiento

| epoca | train_loss | eval_loss |
|---|---|---|
| 1 | ~1.24 | 1.2516 |
| 2 | ~1.04 | 1.1836 |
| 3 | ~0.99 | **1.1801** |

Sin repunte, y la brecha con el train (0.96) es moderada: no hay sobreajuste
visible. Se eligio el checkpoint de la epoca 3 por `eval_loss`. El historial
completo esta en `historial_entrenamiento_v2.json` -- la evidencia que en v1
solo existia en W&B y no se pudo recuperar al cerrar el modulo.

## El modelo base no cambio

v2 regenero el baseline y las **334 de 334** respuestas salieron identicas
caracter por caracter a las de `results/m1_2026-10-09/baseline_results.jsonl`.
Con `do_sample=False` la decodificacion es determinista, asi que cualquier
cambio de pesos o de tokenizer se habria filtrado a alguna.

Eso **no demuestra** que los modelos sean el mismo: dos modelos distintos
pueden coincidir en un conjunto finito. Descarta el escenario realista, que es
un commit nuevo en el repo de Qwen -- ni v1 ni v2 fijan `revision`, y la de v1
nunca quedo registrada.

## Por que no basta con mas datos

La pista esta en el 19 de 35 que arrancan con "No": el modelo alcanza el patron
de negacion y se va a su propia redaccion. La perdida de un LM causal se
promedia por token, y la frase fija compite en desventaja -- unos 40 tokens de
target contra 110 de una respuesta de fondo -- asi que una vez que arranca
distinto no vuelve a la frase. Con 646 ejemplos B2 (27.2 % de los ejemplos,
16.6 % de la senal) sigue sin producirla.

**Agregar mas ejemplos B2 no es la siguiente intervencion.** Las opciones, por
costo:

1. **Decidir si la frase exacta es un requisito de producto o un artefacto de
   la metrica.** Si lo que importa es que no afirme sin fundamento, "No te
   puedo decir cuanto cuesta porque depende de..." cumple, y la metrica deberia
   medir eso. Cero GPU.
2. **Peso por ejemplo en la perdida** en vez de promedio por token, para que un
   target de 40 tokens pese lo mismo que uno de 110.
3. **Forzarla en el pipeline y no en el modelo**: `escape_por_codigo` ya existe
   en `tools/rag/pipeline.py` y hoy no se dispara nunca.

## Veredicto

**v2 no se adopta todavia, y v1 sigue siendo el baseline.** La ruta de
produccion (`amparo-lora-adapter`) no se toca: el adaptador v2 vive en
`amparo-lora-adapter-v2`.

v2 es mejor que v1 en dos cosas pequenas (entidades inventadas 3.0 -> 2.7 %, B3
12 -> 13) y peor en una (B1 55 -> 54, ruta legal 96.7 -> 95.2 %). Ninguna
justifica cambiar de adaptador por si sola, y el fallo que motivo la corrida
sigue abierto.

Falta, si se decidiera adoptarlo: medir la sobre-abstencion con retrieval real
corriendo S10 con el adaptador v2. **No se corrio** porque B2 no mejoro y esa
corrida solo tenia sentido para comprobar que la mejora no costaba
sobre-abstencion.
