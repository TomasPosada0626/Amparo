# Suficiencia de evidencia: medición de las señales disponibles

Diagnóstico offline. **No se generó ninguna respuesta, no se usó GPU, no se
tocó el pipeline.** Nada de `tools/prototipo/` se importa desde la ruta que
responde al usuario.

Reproducible con `python -m tools.prototipo.medir_suficiencia`.

---

## 1. El hueco, con los dos casos de referencia

`verificacion.citas_no_verificables` responde *"¿el artículo citado se
recuperó?"*. No responde *"¿ese artículo sostiene lo que la respuesta afirma?"*,
y no ve una afirmación hecha sin citar nada.

| caso | la respuesta | qué falla | qué ve el código |
|---|---|---|---|
| **2229** | *"…acude a la Superintendencia de Servicios Públicos Domiciliarios"* ante una compraventa entre particulares | competencia institucional sin respaldo, **sin citar nada** | nada: no hay cita que verificar |
| **2823** | *"El artículo 65 del CST obliga al empleador a pagar la indemnización…"* ante el embargo de una cuenta sin saldo | el artículo **sí se recuperó** y **sí es del CST**: correcto en los dos ejes comprobables, y ajeno a la pregunta | nada: la cita está respaldada |

---

## 2. Matriz por señal

### 2.1 Recuperación real, 45 casos gold

Verdad: **el artículo que responde no se entregó** (puesto del gold según la
auditoría 6.1, no una etiqueta sintética).

| señal | VP | FP | VN | FN | prec. | rec. |
|---|---|---|---|---|---|---|
| S1 sin ninguna cita | 5 | 3 | 17 | 20 | 0.62 | 0.20 |
| S2 cita sin respaldo en el contexto | 0 | 1 | 19 | 25 | 0.00 | 0.00 |
| S3 contexto de otra materia (**enrutador**) | 0 | 1 | 19 | 25 | 0.00 | 0.00 |
| S3b contexto de otra materia (categoría real) | 6 | 2 | 18 | 19 | 0.75 | 0.24 |
| S4 afinidad léxica baja | 24 | 15 | 5 | 1 | 0.62 | 0.96 |
| S5 competencia institucional sin respaldo | 5 | 9 | 11 | 20 | 0.36 | 0.20 |
| S6 plazo sin respaldo | 2 | 0 | 20 | 23 | **1.00** | 0.08 |

### 2.2 Lo que cada señal bloquearía de lo que ya funciona

**Esta es la tabla que decide.** De los 75 casos de la corrida real, **9
cumplen** su criterio y **28 son parciales**.

| señal | bloquea de las 9 que **cumplen** | bloquea de las 28 **parciales** |
|---|---|---|
| S1 sin ninguna cita | **7 (78 %)** | 15 (54 %) |
| S2 cita sin respaldo | 1 (11 %) | 1 (4 %) |
| S3 (enrutador) | **0** | 0 |
| S3b (categoría real) | **8 (89 %)** | 16 (57 %) |
| S4 afinidad léxica | **7 (78 %)** | 25 (89 %) |
| S5 competencias | **5 (56 %)** | 11 (39 %) |
| S6 plazo sin respaldo | **0** | 0 |

### 2.3 Contexto sintético, 27 casos B2 reservados

**Esta tabla no mide precisión y hay que decirlo:** las 27 filas son **todas
positivas**, no hay ni un caso negativo, así que cualquier precisión sale 1.00
por construcción. El programa lo avisa en la salida.

| señal | VP | FN | rec. |
|---|---|---|---|
| S2 cita sin respaldo | 19 | 8 | 0.70 |
| S5 competencias | 13 | 14 | 0.48 |
| S1 sin ninguna cita | 8 | 19 | 0.30 |
| S3 / S3b / S4 / S6 | 0 | 27 | 0.00 |

---

## 3. Tres hallazgos que cambian conclusiones anteriores

### 3.1 La precisión 1.00 del detector institucional era de contexto sintético

El commit `9c9f5a9` midió precisión **1.00** y recall 0.46 para
`competencias_sin_respaldo`. Esa medición es sobre el contexto **sintético** del
dataset. Sobre **recuperación real**, la misma señal:

- precisión **0.36** contra la verdad de insuficiencia;
- y se activa en **5 de las 9** respuestas que cumplen su criterio.

La conclusión del commit —*"NO sirve como puerta"*— se sostiene y queda
**reforzada**. Lo que no se sostiene es leer el 1.00 como una tasa de producción.

### 3.2 Un 1.00/0.96 anterior era un artefacto de contexto vacío

En la primera pasada, S3 daba precisión 1.00 y recall 0.96 sobre el conjunto
sintético. Era un error: a esos casos se les pasaba la lista de fragmentos
vacía, y la función devolvía "de otra materia" ante un contexto vacío. **Un
contexto vacío no es un contexto irrelevante** —son dos de las cuatro
situaciones a distinguir, y además el pipeline nunca llega al modelo con
contexto vacío. Corregido, S3 da 0.00 ahí. Lo detectó una prueba escrita para
eso y los números de arriba son los de después.

### 3.3 La señal con más cobertura no mide insuficiencia

S4 (afinidad léxica) tiene recall 0.96, el mejor de todos. Y se activa en **39
de 45** casos, incluidas 7 de las 9 respuestas correctas y 25 de las 28
parciales. **Mide "esto es una pregunta jurídica", no insuficiencia.** Su umbral
no está calibrado a propósito: calibrarlo sobre estos mismos casos sería el
error que el encargo prohíbe.

---

## 4. Clasificación en cuatro: resultado negativo

El prototipo clasifica los 45 gold en SUFICIENTE / IRRELEVANTE / PARCIAL /
SIN_RESPALDO. Contra si el artículo que responde se entregó de verdad:

| clase del prototipo | evidencia **sí** | evidencia **no** |
|---|---|---|
| SUFICIENTE | 7 | **16** |
| IRRELEVANTE | 1 | 0 |
| PARCIAL | 2 | 4 |
| SIN_RESPALDO | **10** | 5 |

Llama "SUFICIENTE" al **64 %** de los casos sin evidencia (16/25) y solo al
**35 %** de los que sí la tienen (7/20). **Está anticorrelacionado con la
verdad.** No es una señal débil: es peor que no tenerla.

---

## 5. Conjuntos: qué se usó para diseñar

| conjunto | n | para qué | cómo se lee |
|---|---|---|---|
| diseño B2 | 8 (2229, 2823 y 6 previos) | escribir las señales | **optimista por construcción** |
| diseño gold | 2 (9001, 9004) | ídem | ídem |
| reservados B2 | 27 | medir | ya pasaron por la adjudicación: **no son datos vírgenes** |
| gold real | 45 | medir | ya pasaron por la auditoría 6.1, para *ranking*, no para estas señales |

**2229 y 2823 son casos de diseño**, porque el encargo los nombró: pedir que una
señal los resuelva y después medirla en ellos es ajustar. Las dos los detectan,
y eso no prueba nada.

### Qué haría falta para demostrar generalización

1. **Casos negativos adjudicados con recuperación real**: hoy no existen. Las 27
   filas B2 son todas positivas y los 45 gold tienen etiqueta de *recuperación*,
   no de *suficiencia de la afirmación*. Sin negativos no hay precisión.
2. **Más de 9 respuestas correctas.** El riesgo de bloqueo se estima sobre 9
   casos. 5 de 9 tiene un intervalo ancho; la dirección es consistente entre
   señales, la magnitud no es fiable.
3. **Una corrida con el candidato**, donde las respuestas no vengan todas del
   mismo adaptador con el mismo sesgo.

---

## 6. Mecanismo mínimo: qué se puede y qué no

| situación a distinguir | se resuelve con lo que hay | con qué |
|---|---|---|
| **sin ninguna cita** | **sí** | S1, mecánico y exacto. No es señal de fallo: muchas orientaciones correctas no citan |
| **cita que no está en el contexto** | **sí** | `citas_no_verificables`, ya en producción |
| **cita atribuida a otra norma** | **sí** | `citas_mal_atribuidas` + `normas_citadas_ausentes` |
| **plazo sin respaldo** | **sí** | S6: precisión 1.00, bloquea 0 correctas, recall 0.08. **Estrecho y real** |
| **contexto no vacío pero irrelevante** | **no** | S3 con el enrutador detecta 0; con la categoría verdadera detecta 6 y bloquea 8 de 9 correctas. Y la etiqueta verdadera no existe en servicio |
| **evidencia parcial** | **no** | ninguna señal la separa de la insuficiente |
| **afirmación sustantiva sin respaldo** | **no** | S5 es señal de revisión; como puerta bloquea 56 % de lo correcto |
| **suficiencia semántica** | **no, y no es un umbral que falte** | es juicio jurídico. `verificacion.py` ya retiró una heurística léxica por fallar en un caso positivo conocido (3328) |

### El único candidato promovible hoy

**S6, plazo sin respaldo.** Precisión 1.00, cero bloqueos de respuestas
correctas o parciales, recall 0.08. Resuelve un fallo real y pequeño. Ya existe
como puerta del dataset; promoverlo a verificación de salida es barato y no
arrastra riesgo.

Nada más está listo. No se propone un umbral nuevo ni un segundo modelo.

---

## 7. Recomendación

**Requiere resolver un impedimento concreto**, y no es la GPU.

> **No existe un conjunto con casos negativos adjudicados sobre recuperación
> real.** Sin negativos no se puede medir la precisión de ninguna señal, y la
> precisión es justo lo que decide si una puerta es utilizable: una con recall
> alto que bloquee el 78 % de las respuestas correctas es peor que no tenerla.

Lo que hace falta es acotado: adjudicar, sobre las respuestas ya guardadas de la
corrida real, **si cada afirmación sustantiva está respaldada por el contexto que
se entregó** — incluidos los casos donde **sí** lo está, que son los que hoy
faltan. Son 75 respuestas que ya existen; el coste es de adjudicación, no de
cómputo, y el instrumento (`tools/adjudicacion_b2.py`) ya está escrito.

Mientras eso no exista, **no se conecta ninguna señal al pipeline como puerta.**
