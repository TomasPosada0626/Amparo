# Plan para Demo Day — Amparo

Amparo ya tiene lo más difícil de un producto de IA jurídica: una decisión que no inventa normas, porque el mecanismo lo pone la regla y no el LLM, y una evaluación en la que se puede creer. La Demo del 5 de noviembre es la oportunidad de **mostrarlo como producto**: una persona sube la foto de su documento, hace su pregunta y en segundos recibe una respuesta con su fundamento visible.

Este plan propone **tres prioridades** con cambios mínimos sobre el camino que ya existe. No hace falta rediseñar nada. Cada prioridad remite a las observaciones de [`README.md`](README.md).

## Dónde está hoy el recorrido completo

| Pieza | Qué hace en el recorrido | Dónde está | ¿Conectada al flujo con imagen? |
|---|---|---|---|
| **M4** | Qwen2-VL-2B lee la foto y extrae los hechos (`ver()`). | `m4/pipeline/M4_pipeline.ipynb`, celdas 9–10 | Sí |
| **M3** | El agente de Groq con el brazo 4 «agente + reglas»: extrae hechos, la regla del art. 6 decide, el RAG recupera el artículo y el LLM redacta las cinco líneas. | `m4/pipeline/enchufe_m3.py` (`construir_responder_m3`), sobre `src/agente.py`, `src/reglas.py` y `src/rag.py` | Sí: `sistema_multimodal(pregunta, imagen)`, celda 14 |
| **M2** | Harness y métricas con las que se mide todo. | `src/harness.py` y `m4/harness/` | Sí, en la evaluación (`scorecard_m4.csv`) |
| **M1** | Qwen2.5-7B con LoRA, el brazo 1, que es el mejor en el agregado de M3. | `notebooks/M1_finetuning.ipynb` | No. La razón está documentada en `enchufe_m3.py`: 7B y el VLM no caben juntos en una T4, y el brazo 4 es el que mejor aguanta las trampas. |

**Punto de entrada que sirve de base para el despliegue:** `sistema_multimodal(pregunta, imagen=None)`. Hoy vive en una celda; con ella y `construir_responder_m3()` ya existe el producto entero en una función. `python reproducir.py` verifica, sin GPU ni API, todo lo que se puede reproducir sin ellas.

---

## Prioridad 1 · [P1] La experiencia de punta a punta en una sola llamada, con el fundamento a la vista

- **Prioridad:** P1. Es necesaria para mostrar el producto, no solo el notebook.
- **Qué podría ocurrir durante la demo:**
  - El público ve celdas de Colab en lugar de una persona usando Amparo.
  - Si la respuesta aparece como cinco líneas sin la regla que decidió ni el artículo recuperado, se pierde justo lo que distingue a Amparo: un fundamento que no alucina.
  - Además, si no se explica dónde está M1 en el producto, el público puede preguntar por qué el modelo ajustado no aparece en el recorrido.
- **Evidencia exacta:**
  - `ver()` y `sistema_multimodal()` están definidos en celdas del notebook, celdas 10 y 14.
  - La celda 14 ya imprime la regla que cerró y las herramientas usadas, desde `agente_m3.trazas[-1]`.
  - El README de M4 reconoce que estas funciones viven en celdas.
  - `enchufe_m3.py` explica por qué se usa el brazo 4 y no el 1.
- **Cambio mínimo recomendado:**
  1. Mover `ver()` y `sistema_multimodal()`, sin cambiar su lógica, a un módulo importable, por ejemplo `m4/pipeline/multimodal.py`. El notebook pasa a importarlo, y el `app.py` que preparen para M5 lo importará igual.
  2. Que la salida que ve el usuario tenga tres bloques:
     - las cinco líneas;
     - **«Por qué»**: la regla que cerró y el artículo recuperado, tomados de la traza;
     - **«Lo que leímos de tu documento»**: los campos del VLM.
  3. Una frase de producto sobre M1. Por ejemplo: «el modelo ajustado (M1) fue nuestro mejor clasificador en el agregado; para el producto con imagen elegimos el agente con reglas porque nunca inventa la norma y cabe junto al lector visual». La elección y las palabras exactas son del equipo.
- **Qué NO hace falta rehacer:** el VLM, los prompts, M3, el motor de reglas, el harness ni las métricas. Tampoco hace falta meter el 7B en el despliegue.
- **Cómo verificar el cierre:**
  - `from m4.pipeline.multimodal import sistema_multimodal` funciona fuera del notebook.
  - Con m01 (foto y pregunta), la salida muestra los tres bloques.
  - Las pruebas existentes de `m4/tests` siguen pasando.
- **Quién lo asume:** lo decide el equipo.

## Prioridad 2 · [P1] La confianza como característica: «cuando no está seguro, lo dice»

- **Prioridad:** P1. Convierte el caso más delicado en el mejor momento de la demo.
- **Qué podría ocurrir durante la demo:**
  - En m10 el VLM escribe en `pretension_visible` un plazo («dos semanas hábiles») que no está en el documento, mientras `plazo_dias` queda en null.
  - Si eso aparece en pantalla como un hecho leído del documento, el público lo toma como verdad.
  - Lo valioso es que **el sistema no se lo cree**: al re-ejecutar M3 real con esa lectura, la respuesta fue «Mecanismo: no determinable», sin mencionar ningún plazo.
  - Es decir, el producto ya se comporta con seguridad. Falta que se **vea**.
- **Evidencia exacta:**
  - `m4/trazas_m4.json`, caso m10.
  - Reproducción con su `ver()` real (MPS fp16): la misma lectura.
  - Re-ejecución de M3 con `openai/gpt-oss-120b` y caché vacía: abstención (observación H2 del README).
  - m04 invierte el sentido de la frase leída, pero M3 decide el mecanismo correcto con y sin imagen.
- **Cambio mínimo recomendado:**
  1. Rotular en pantalla el bloque del VLM como **«Leído del documento, no verificado»**.
  2. Añadir una guarda que muestre una advertencia cuando el texto libre menciona un plazo que `plazo_dias` no tiene. Hay una propuesta de código con pruebas en la rama `revision/m4-evaluacion`, que pueden adoptar o reescribir.
  3. Presentar m10 en la demo como **el caso de seguridad**: «el lector visual vio algo que no está; Amparo lo marca y prefiere no decidir antes que inventar».
- **Qué NO hace falta rehacer:** el prompt del VLM ni el modelo. La abstención de M3 ya existe (`schema.PREGUNTA_TRIABLE` y el motor de reglas).
- **Cómo verificar el cierre:**
  - m10 muestra la advertencia y la abstención.
  - En los otros diez casos del eval set no aparece la advertencia; la guarda propuesta marca solo m10 sobre `trazas_m4.json`.
- **Quién lo asume:** lo decide el equipo.

## Prioridad 3 · [P1] Tres cifras de valor que se sostengan en vivo, sobre una versión fija y ensayada

- **Prioridad:** P1. Hace falta para sostener lo que se afirme en el escenario.
- **Qué podría ocurrir durante la demo:**
  - Que se afirme «la imagen mejora la respuesta» y una re-ejecución lo contradiga. En una tercera corrida con caché vacía, m06 sin imagen también acertó (H4).
  - Que se dé un tiempo de respuesta que mezcla el arranque en frío. El README atribuye los 30.8 s a un caso distinto, m02 (H1).
  - Que la versión que corre en vivo no sea la evaluada, porque el notebook clona la rama sin fijar un SHA (H3).
- **Evidencia exacta:**
  - `m4/delta_imagen_m4.json`: una corrida, con aporte en 1 de 3 casos.
  - `m4/README.md`, L95–98 y tabla de latencias.
  - Celda de clonado del notebook.
  - `results/m3_scorecard.csv`, brazo 4: acierto de mecanismo 0.675 (81/120) frente a una base mayoritaria de 0.458; tasa de alucinación normativa 0.0 (n=120).
- **Cambio mínimo recomendado:**
  1. **Tres cifras en lenguaje de producto, cada una con su denominador:**
     - Calidad frente a la base: «acierta la vía en 81 de 120 casos, frente a 55 de la regla trivial».
     - Seguridad: «0 normas inventadas en 120 respuestas».
     - Tiempo de respuesta con imagen: mediana por caso, sin el arranque en frío.
     
     Del aporte de la imagen, decir solo lo que sostenga una repetición k≥3 con caché vacía, por ejemplo «en m06 la imagen cambió la vía en X de 3 corridas».
  2. **Versión estable:** un tag (por ejemplo `demo-day`) clonado por SHA, y un manifiesto con commit, GPU, modelos y reranker.
  3. **Casos ensayados:** m01 (éxito), m06 (aporte visual) y m10 (seguridad), los mismos en cada ensayo.
  4. **Plan B rotulado:** una grabación o salida cacheada de esos tres casos, presentada como tal, por si falla la red, Groq o la GPU.
- **Qué NO hace falta rehacer:** el eval set, los criterios pre-registrados ni el scorecard, que se recalcula sin discrepancias.
- **Cómo verificar el cierre:**
  - El README y la diapositiva muestran las tres cifras con su denominador y su fuente.
  - `delta_imagen_m4.json` trae repeticiones.
  - El SHA del manifiesto coincide con el que corre en la demo.
- **Quién lo asume:** lo decide el equipo.

---

## Guion sugerido (bloques, sin minutos obligatorios)

1. **La persona y su decisión.** Alguien recibe un documento que le niega algo; puede ser el caso de la EPS (m01). Tiene una foto y una duda: ¿qué hago? ¿Tutela, acción popular, de cumplimiento? Equivocarse de vía le cuesta tiempo que no tiene.
2. **El momento «wow», en vivo.** Sube la foto y escribe su pregunta. En segundos ve:
   - las cinco líneas;
   - el «Por qué», con la regla del art. 6 que decidió y el artículo recuperado;
   - lo que Amparo leyó del documento.
3. **Lo que aporta la imagen.** m06 (corporación ambiental): qué cambia cuando el documento entra al relato. Contarlo con la tasa que dejen las repeticiones.
4. **La prueba de valor.** Tres cifras con denominador: calidad frente a la base, cero normas inventadas y tiempo de respuesta.
5. **Así se comporta con seguridad.** m10: el lector visual ve un plazo que no está en el documento; Amparo lo marca como no verificado y prefiere decir «no determinable» antes que inventar.
6. **Cómo lo operamos.** Versión fija, el estado del servicio y los registros, tal como queden al desplegar.
7. **Límites honestos y siguiente paso.**
   - Documentos sintéticos.
   - Pocos casos con imagen.
   - El juez visual es el mismo VLM.
   - No sustituye asesoría jurídica.
   - Roadmap que el equipo elija: por ejemplo, más adversariales, otro juez visual o documentos reales anonimizados.

## Al desplegar (M5), conviene…

Estas son sugerencias para cuando preparen la URL pública. No son observaciones sobre M4.

- Que `app.py` importe el mismo `sistema_multimodal` de la prioridad 1, para que la Demo use el código evaluado.
- Mostrar los tres bloques de salida y la advertencia de la prioridad 2.
- Mantener la clave de Groq como secreto del Space.
- Tener un health check que confirme que el VLM está cargado y que Groq responde.
- Registrar una línea JSON por petición, con caso, latencia de `ver()`, latencia de M3, regla y advertencias, sin texto del documento ni datos personales. De ahí salen la p50 y la p95.
- Llevar esas mismas cifras a W&B. Así la cifra de tiempo de la prioridad 3 sale de producción y no de una corrida suelta.
- Para la técnica de eficiencia: el VLM hoy carga en fp16 (celda 9). Cuantizarlo, por ejemplo a int8 o int4, y medirlo con el mismo eval set y los mismos criterios daría la tabla antes/después, con el acierto y el tiempo de `ver()` lado a lado.

## Backlog (después de la Demo)

- Un segundo juez visual distinto del VLM que se evalúa.
- Más casos adversariales y más casos `exacto`.
- `entidad` está en null en 6 de 6 casos.
- Responder los PR #13 y #14 de M3.
