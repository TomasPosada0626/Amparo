# M5 · Amparo cabe y corre rápido

## S14 · Destilación de un componente

Código: [`amparo/pipelines/m5_destilacion.py`](../amparo/pipelines/m5_destilacion.py).
Notebook: [`S14_destilacion.ipynb`](S14_destilacion.ipynb), que solo llama al código. La versión
del repo es la que se ejecutó, con sus salidas.
Sigue la **Parte B** del lab de la profe (datos sintéticos + LoRA).

### Qué componente y por qué

Scorecard de M4, corrida de demo `20261101T203828Z_demo` (L4, 11 casos):

| componente | mediana | p95 | mín–máx | parte de la mediana |
|---|---|---|---|---|
| VLM Qwen2-VL-2B (leer el documento) | 3.7 s | 4.4 s | 2.7–4.4 s | 34 % |
| **M3 brazo 4 (agente gpt-oss-120b + reglas)** | **6.4 s** | **14.8 s** | **3.3–14.8 s** | **59 %** |
| total por caso | 10.8 s | 17.8 s | 7.0–17.8 s | 100 % |

M3 es lo más lento y lo que más varía. Llama de media 4.2 veces por caso (`results/m3_agente.json`) a un modelo de 117 B para
extraer **13 booleanos y tres frases**, porque el mecanismo lo decide el motor de reglas.
Esa pieza no necesita ser grande.

Usamos la forma B porque es el generador. La forma A no aplica: el profesor es una API y
no da logits.

### Profesor y estudiante

**Profesor:** el brazo 4 de M3, con gpt-oss-120b por Groq.
- Licencia Apache 2.0, que permite entrenar con sus salidas.
- Escribe los relatos nuevos a `T = 0.7`, como en el lab.
- Responde a `T = 0` y `seed = 42`, así que la etiqueta es reproducible.

**Estudiante:** Qwen2.5-0.5B-Instruct + LoRA, con la receta de S04.
- `r = 8`, `q_proj`/`v_proj`, `lr = 2e-4`, 3 épocas.
- Licencia Apache 2.0.
- Hace una sola llamada, sin herramientas.

**Qué aprende el estudiante:** solo el JSON de hechos. `decidir()` y `render_salida()`
siguen siendo los de M3, así que el estudiante no puede inventar normas.

### Contrato (escrito antes de entrenar)

**Se mide contra el profesor medido de nuevo en la misma corrida y la misma GPU**, sobre los
130 casos de M3 (`eval_set_v3` + `eval_set_m3`). Los umbrales son diferencias frente a ese
profesor, no cifras fijas. Así lo verifica `tabla()`.

| cláusula | se cumple si |
|---|---|
| acierto jurídico | el estudiante baja **como máximo 5 puntos** frente al profesor |
| alucinación normativa | **0 %** |
| adversariales | el estudiante baja **como máximo 8 puntos** frente al profesor |
| velocidad de M3 | mediana del estudiante **≥ 3×** más rápida que la del profesor |
| estabilidad de M3 | p95 del estudiante **≤ 5 s** |

**Como referencia** (no es el umbral), el brazo 4 en `results/m3_scorecard.csv` tiene:

- acierto jurídico de 67.5 % (81/120);
- 73.8 % en adversariales (31/42);
- mediana de M3 de 6.4 s en la demo de M4, con p95 de 14.8 s.

Si el profesor repitiera esas cifras, los umbrales serían ≥ 62.5 %, ≥ 65.8 % y ≤ ~2.1 s.

- **Puntos y no porcentaje relativo:** de 67.5 % a 62.5 % se pierden 5 puntos. Con 42
  adversariales, perder 4 casos (9.5 puntos) ya incumple.
- **Por qué 5 y no 2:** el propio profesor varía entre repeticiones (13/18 en el delta de
  M4). Un contrato más estrecho que ese ruido no se puede verificar.
- **El tiempo es solo de M3.** El VLM (~3.7 s) no se destila: se ataca en S15, cuando se
  cuantice.

### Resultado: el contrato NO se cumple

Corrida del 2026-11-03 (21:52–23:09 UTC), commit `f8c0e6c` (rama `m5`), en una NVIDIA
A100-SXM4-40GB de Colab. Los datos completos están en [`destilacion.json`](destilacion.json),
que incluye el manifiesto. Los pares con los que se entrenó están en
[`pares_profesor.json`](pares_profesor.json), y el notebook con sus salidas en
[`S14_destilacion.ipynb`](S14_destilacion.ipynb).

**Las cinco cláusulas:**

| cláusula | pedido | profesor | estudiante | ¿cumple? |
|---|---|---|---|---|
| acierto jurídico | baja ≤ 5 puntos | 74.2 % | 45.0 % (−29.2) | **NO** |
| alucinación normativa | 0 % | 0 % | 0 % | sí |
| adversariales | baja ≤ 8 puntos | 88.1 % | 11.9 % (−76.2) | **NO** |
| velocidad de M3 (mediana) | ≥ 3× | 6.09 s | 2.71 s (2.2×) | **NO** |
| estabilidad de M3 (p95) | ≤ 5 s | 12.35 s | 2.96 s | sí |

**La tabla antes/después completa:**

| | profesor · gpt-oss-120b (agente + reglas) | estudiante · Qwen2.5-0.5B + LoRA (+ reglas) |
|---|---|---|
| acierto en casos gold | 66.7 % | 62.8 % |
| acierto en adversariales | 88.1 % | 11.9 % |
| acierto en abstención (válvula) | 60 % | **0 %** |
| JSON inválidos | 0 | 0 |
| latencia p50 / p95 | 6.09 s / 12.35 s | 2.71 s / 2.96 s |
| llamadas por caso | 3.93 (medidas) | 1 |
| parámetros | 117 B (5.1 B activos) | 494 M (237× menos) |
| dónde corre | API de Groq | la GPU del sistema |

**Lectura:**
- **El estudiante colapsa a tutela.** En 59 de los 60 casos donde el profesor acierta y él
  no, responde tutela. De esos 60 casos, 32 son adversariales, 22 gold y 6 de abstención.
  El caso contrario ocurre 19 veces.
- **En los casos gold casi empata** (62.8 % contra 66.7 %). Lo que pierde es lo que la
  slide 19 de S14 predice que se pierde primero:
  - **lo raro:** vía ordinaria disfrazada de tutela, hábeas corpus, acción popular y de
    cumplimiento;
  - **la válvula de escape:** no se abstiene en ninguno de los 10 casos de abstención.
- **Lo que sí gana es estabilidad:** el p95 baja de 12.35 s a 2.96 s, porque hace una sola
  llamada en vez de un agente que da vueltas. Y no puede inventar normas, porque las sigue
  poniendo el motor.
- **La velocidad no llega a 3×.** Con un modelo tan chico, `generate` de Hugging Face paga
  un costo fijo por token. Servirlo con vLLM o llama.cpp es la palanca de S15.

**Por qué no alcanzó, y qué probaríamos** (es lo que el lab sugiere cuando el contrato no
se cumple):
- **El profesor es ruidoso.** Con sus propios hechos, el motor llega al mecanismo gold en
  100 de 142 relatos de M1 (70 %). El estudiante aprende de esas etiquetas.
- **El estudiante no terminó de aprender.** `eval_loss` siguió bajando en las tres épocas
  (0.648 → 0.585 → 0.577) y el mínimo está en la última.
- **Siguiente intento:** más épocas, más relatos (`N_POR_TEMA`) o un estudiante más grande
  (Qwen2.5-1.5B-Instruct).

### Decisión (2026-11-03): el sistema se queda con el profesor, y M5 cuantiza el VLM

**Por qué el sistema desplegado se queda con el profesor (brazo 4) y no con el estudiante:**
- **El contrato se escribió antes de entrenar y no se cumple en 3 de las 5 cláusulas.** La
  regla del lab es que el contrato no se mueve después de ver el resultado: *"si no lo
  escriben antes, después cualquier resultado parece bueno"*. No se cumplió, así que no se
  usa.
- **Lo que pierde el estudiante es justo lo que el usuario no puede revisar solo.** Cae de
  88 % a 12 % en adversariales y de 6/10 a 0/10 en abstención. Si alguien pregunta algo que
  no es un caso (dónde invertir, una duda académica), el estudiante le propone una tutela
  en vez de decirle que Amparo no aplica. En triaje jurídico, recomendar tutela por defecto
  es el error caro: manda a la persona a una acción improcedente.
- **Lo que gana no compensa.** El p95 baja de 12 s a 3 s y deja de depender de la API.
  Pero la mediana mejora solo 2.2×, y la seguridad (0 normas inventadas) ya la tenía el
  profesor, porque la pone el motor en los dos.

**Por qué la técnica de eficiencia de M5 es cuantizar el VLM.** Se evaluaron dos caminos:

| | 1 · destilación como limitación + cuantizar el VLM (**elegida**) | 2 · destilar imágenes + cuantizar M1 (7B) |
|---|---|---|
| ¿mejora lo que se despliega? | **sí**: el VLM (Qwen2-VL-2B) es el único modelo local del sistema de M4 | **no**: la demo usa el brazo 4 por Groq, no M1; cuantizar M1 no cambia lo que ve el usuario |
| ¿encaja con el lab? | la Parte A de S15 es justo "su generador o modelo en int4 con bitsandbytes" | la Parte A de S14 destila un **clasificador** por logits; el VLM **lee campos** (fechas, plazos, entidad) y una CNN chica no puede leer texto, así que habría que inventar una tarea que Amparo no tiene |
| trabajo antes de la demo (jue 5 nov) | una pieza nueva | dos piezas nuevas |
| qué se mide | memoria, p50/p95 y el harness de M4, sobre todo `campos` y `valvula`: fechas y números son la debilidad conocida del VLM | |

La rúbrica de M5 pide **una** técnica de eficiencia medida, *"destilado o cuantizado, con
contrato y tabla antes/después"* (README de S15). Con la cuantización del VLM se cumple, y
esta destilación queda como intento medido, con su columna de "qué cedió". La slide 14 de
S14 lo dice: *"un modelo destilado sin la columna 'qué cedió' no es ingeniería, es
marketing"*.

### Qué cede el estudiante (para *limitaciones y ética*)

- **La válvula de abstención:** 0 de 10, frente a 6 de 10 del profesor. Un usuario con una
  consulta fuera del dominio recibiría una tutela en vez de un "esto no es para mí".
- **Los casos raros y las trampas:** −76 puntos en adversariales. El detalle está en
  `destilacion.json → casos_perdidos`.
- **La herramienta de términos** (`calcular_termino`): el estudiante no la tiene.
- **La consulta al corpus de normas:** el estudiante no la hace. El fundamento lo sigue
  poniendo el motor, así que no inventa normas.
- **Los errores del profesor:** los hereda. Su acuerdo con el gold es 70 %.
