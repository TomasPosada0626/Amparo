# M5 · Amparo cabe y corre rápido

## S14 · Destilación de un componente

Código: [`amparo/pipelines/m5_destilacion.py`](../amparo/pipelines/m5_destilacion.py).
Notebook: [`S14_destilacion.ipynb`](S14_destilacion.ipynb), que solo llama al código.
Sigue la **Parte B** del lab de la profe (datos sintéticos + LoRA).

### Qué componente y por qué

Scorecard de M4, corrida de demo `20261101T203828Z_demo` (L4, 11 casos):

| componente | mediana | p95 | mín–máx | parte de la mediana |
|---|---|---|---|---|
| VLM Qwen2-VL-2B (leer el documento) | 3.7 s | 4.4 s | 2.7–4.4 s | 34 % |
| **M3 brazo 4 (agente gpt-oss-120b + reglas)** | **6.4 s** | **14.8 s** | **3.3–14.8 s** | **59 %** |
| total por caso | 10.8 s | 17.8 s | 7.0–17.8 s | 100 % |

M3 es lo más lento y lo que más varía. Llama de 3 a 7 veces a un modelo de 117 B para
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

Se mide contra el profesor medido de nuevo en la misma corrida y la misma GPU, sobre los
130 casos de M3 (`eval_set_v3` + `eval_set_m3`). Las cifras de referencia son las del
brazo 4 en `results/m3_scorecard.csv`.

| cláusula | se cumple si | referencia del profesor (M3) |
|---|---|---|
| acierto jurídico | baja **como máximo 5 puntos** | 67.5 % (81/120) → ≥ 62.5 % |
| alucinación normativa | **0 %** | 0 % |
| adversariales | bajan **como máximo 8 puntos** (con 42 casos, perder 4 ya incumple) | 73.8 % (31/42) → ≥ 65.8 % |
| velocidad de M3 | mediana **≥ 3×** más rápida | 6.4 s → ≤ ~2.1 s |
| estabilidad de M3 | **p95 ≤ 5 s** | hoy 14.8 s |

- **Puntos y no porcentaje relativo:** de 67.5 % a 62.5 % se pierden 5 puntos.
- **Por qué 5 y no 2:** el propio profesor varía entre repeticiones (13/18 en el delta de
  M4). Un contrato más estrecho que ese ruido no se puede verificar.
- **El tiempo es solo de M3.** El VLM (~3.7 s) no se destila: se ataca en S15, cuando se
  cuantice.

### Resultado

*Pendiente de la corrida.* La tabla antes/después, el veredicto del contrato y los casos
que el estudiante pierde salen en `m5/destilacion.json`.

### Qué cede el estudiante (para *limitaciones y ética*)

- **Los casos perdidos:** `m5/destilacion.json → casos_perdidos`.
- **La herramienta de términos** (`calcular_termino`): el estudiante no la tiene.
- **La consulta al corpus de normas:** el estudiante no la hace. El fundamento lo sigue
  poniendo el motor.
- **Los errores del profesor:** los hereda (`acuerdo_profesor_gold`).
