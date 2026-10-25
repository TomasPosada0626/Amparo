# Harness de M4: decisiones de T5 y T6

Cada decisión va con su razón y con la evidencia que la sostiene. El formato
del CSV de casos tiene su propio documento:
[`../eval_set/FORMATO_CASOS.md`](../eval_set/FORMATO_CASOS.md).

## T5 · Criterios (`criterios.py`)

| # | Decisión | Por qué | Evidencia |
|---|---|---|---|
| 1 | `calificar()` es una función **nueva** en `m4/harness/` y `src/harness.py` no se toca. | `harness()` está hecha para el eval set de M2/M3 (`relato`, `mecanismo`, `procede`), no para casos con `esperado` y `criterio`. Además `src/` es intocable: `corridas.version_codigo()` hashea sus bytes. | No existe `calificar` en `src/` (grafo y grep). `harness(eval_set, salidas, etiqueta, juez=None)` en `src/harness.py:87`. |
| 2 | `nota_exacto` compara `schema.parse_salida(...)["mecanismo"]` con el esperado; si se espera abstención, usa `schema.se_abstuvo`. | Es el mismo parser y la misma comparación de mecanismo que usa M3, así que la comparación directa de T6 mide lo mismo en los dos lados. Cubre lo que pide la rúbrica: "la misma función de M2 califica los casos nuevos". | `metricas.acierto_por_caso` (`src/metricas.py:770`). |
| 3 | `campos` y `valvula` califican el JSON que devolvió `ver()`, no la respuesta de M3. Si no hay JSON, la nota es 0. | La respuesta final de M3 no contiene ese JSON. Un JSON que no se puede leer es un fallo del sistema (regla 2 del patrón input): no se disimula. | README_PLAN §3. |
| 4 | `juez_vlm` recibe `preguntar_fn` e `imagen`: el **objeto** ya cargado, no la ruta. La llamada es `preguntar(imagen, texto)`, **sin** `system=VALVULA` y con el `max_new_tokens` por defecto. Acordado con Santiago (T2). | El juez mira exactamente la imagen que miró `ver()`. `criterios.py` no importa PIL y se prueba sin GPU. La válvula es una instrucción para extraer datos, no para juzgar. | `preguntar(imagen, pregunta, system=None, max_new_tokens=256)`, celda 7 del notebook. |
| 5 | Para `juez_vlm` solo cuenta un SI o un NO exactos (se toleran la puntuación y las tildes). Cualquier otra respuesta vale 0. | Es el mismo criterio del juez de M2: una duda nunca se interpreta a favor del sistema. | Tests `test_juez_vlm_*`. |
| 6 | Un `esperado` mal formado es un **error de autoría** (`ValueError`, `validar_casos()`), no una nota 0. | Contarlo como fallo del sistema falsearía el scorecard. | `FORMATO_CASOS.md`. |

## T6 · Scorecard y tabla de delta (`scorecard.py`)

| # | Decisión | Por qué | Evidencia |
|---|---|---|---|
| 7 | `correr_harness` repite las tres líneas de `sistema_multimodal` (`armar_relato`) en vez de llamarla. | Necesita capturar lo que devolvió `ver()` para calificar `campos` y `valvula`. Si Santiago cambia `sistema_multimodal`, hay que cambiar `armar_relato` igual: hay un test que fija la fórmula. | Celda 12 del notebook. |
| 8 | Cada imagen se carga **una vez** y ese mismo objeto va a `ver()` y al juez. | Así el juez mira lo que miró el extractor (decisión 4). | Test `test_juez_mira_el_mismo_objeto_que_ver`. |
| 9 | `segundos` mide el **sistema**, es decir `ver()` más M3. Quedan fuera la carga de la imagen y la llamada del juez. | La llamada del juez la hace el evaluador, no el sistema. En el notebook la imagen ya llega cargada a `sistema_multimodal`. | Test del orden del cronómetro. |
| 10 | Antes de gastar GPU se valida todo: el CSV (`validar_casos`) y que haya `preguntar_fn` si algún caso es `juez_vlm`. Si `ver()` o M3 lanzan una excepción, la corrida se detiene y no se convierte en nota 0. | Un caso mal escrito no debe descubrirse a mitad de una corrida en Colab. Y una caída de infraestructura (por ejemplo memoria de GPU) no es una respuesta del sistema: disfrazarla de nota 0 falsearía el scorecard. | Tests `test_*_antes_de_correr`. |
| 11 | `scorecard_m4.csv` lleva exactamente las columnas del plan (`id, criterio, tipo, nota, segundos, salida`). La traza va aparte, en `trazas_m4.json`, y la tabla en `delta_m4.json`. | Las columnas las fija el plan. La traza es la evidencia para explicar el peor caso. Las sesiones de Colab se caen, así que los números quedan guardados en disco antes de escribir el README. Si `results/` llega después de la corrida, `tabla_desde_disco()` arma la tabla con lo guardado, sin GPU. | README_PLAN T6. |
| 12 | Cada caso lleva una **etapa** calculada a partir de su traza: `ver() no produjo JSON`, `valvula: invento ...`, `campos: leyo mal ...`, `M3 decidio ...`, `juez: ...`. | Dice en qué parte de la cadena falló, no solo cuánto. Es un punto de partida: la explicación del peor caso en el README (T8) se escribe a mano leyendo la traza. Para `exacto` la etiqueta no puede distinguir "el VLM leyó mal" de "el motor de reglas decidió mal", y lo dice así. | `diagnosticar()`. |
| 13 | La fila de M3 es **la del brazo que se enchufó en T7**, sin promediar. `sistema_m3` es obligatorio y no tiene valor por defecto. | M3 compara cuatro arquitecturas. Un promedio no corresponde a ningún sistema real. | `results/m3_scorecard.csv` de `origin/main`: una fila por brazo (`1 · fine-tuned solo (M1)` … `4 · agente + reglas`). |
| 14 | Cada fila de la tabla nombra su métrica. La única pareja que se compara directamente es el acierto de mecanismo: casos `exacto` de M4 contra `acc_mecanismo` de M3, mostrando el `n` de M4. | La nota de M4 mezcla criterios y no mide lo mismo que `acierto_juridico`. Con 5 o 6 casos no se puede hablar de significancia. | Columnas verificadas en el artefacto real y en `harness.a_csv` (`src/harness.py:724`). |
| 15 | La latencia de M3 sale de `m3_costos.json` (`datos[].latencia_media` del brazo). Si es `null` se reporta "no disponible", no 0. | El brazo 1 tiene `latencia_media` en null con la nota "sin instrumentar en este modulo". Ojo: costos y scorecard no miden el mismo conjunto. En la corrida `m3/20261022T105449Z`, costos tiene `casos: 130` y el scorecard `n=120` en los brazos 2 a 4. El README debe decirlo. | `results/m3_costos.json` de `origin/main`. |
| 16 | El peor caso es el de **nota mínima**. Si hay empate se listan todos. | El criterio se fija antes de ver los resultados (principio de M2), no se elige a mano después. | `construir_tabla_delta()`. |
| 17 | **`results/` no se trae a `m4` por ahora.** La ruta es un parámetro. | `m4` sale de `f0328fe`. Al 2026-10-22, `origin/main` va 16 commits por delante: trae `results/` (la corrida vigente de M3 es `m3/20261022T105449Z`), cambios en 11 archivos de `src/` y un sello nuevo. Copiar solo `results/` dejaría a `m4` con números de un código que la rama no contiene. Cómo se sincroniza `m4` con `main` (merge o rebase) lo deciden Tomás y Martín (T7). El harness no cambia: lee la ruta que se le pase. | `git diff --stat m4 origin/main -- src`. Antes, la misma situación con `origin/3.5` (`31a7ef8`). |
| 18 | La corrida en Colab es una sola llamada, `correr_t6(...)`, con las funciones del notebook. La celda se agrega al notebook cuando llegue `casos_m4.csv`, coordinándolo con Santiago. | El notebook es de Santiago (T1). Una celda de cinco líneas evita conflictos al fusionar el `.ipynb`. | — |

## Pendiente fuera de T5 y T6

- **Tomás/Martín (T7):** qué brazo se enchufa (su `sistema` tal como aparece en `m3_scorecard.csv`) y cómo se sincroniza `m4` con `origin/main`, que trae `results/` y el `src/` vigente.
- **Lucas (T3/T4):** `casos_m4.csv` e `imagenes/`. Hasta entonces el harness se ensaya con `casos_m4.ejemplo.csv` y funciones falsas.

## T7 · El enchufe real y lo que cambió al conectarlo

| # | Decisión | Por qué | Evidencia |
|---|---|---|---|
| 19 | Se enchufa el brazo **`4 · agente + reglas`** (`m4/pipeline/enchufe_m3.py`), armado como en `M3_rag.ipynb`: `estrategia="reranked"`, `k=4`, reescritura simple de consulta y el chunking que eligió M3 (`results/m3_chunking.json`). | Es el mismo patrón que M4 (extraer hechos, que el motor decida), cabe en una T4 junto al VLM porque razona por la API de Groq, y es el que mejor aguanta las trampas en M3 (adversarial 0.7381, alucinación 0). No es el mejor en el agregado: ese es el brazo 1, que necesita el LoRA de 7B en GPU. | `results/m3_scorecard.csv`; `test_enchufe.py`. |
| 20 | La decisión 17 queda resuelta: `m4` se fusionó con `3.5` en `main` (commit `aaa7a93`), que trae `results/` y el `src/` con el que corrió M3. El notebook clona `main`. | Ya no hay que elegir entre traer `results/` sin su código o esperar. | `git merge-base --is-ancestor origin/m4 origin/main`. |
| 21 | **Corrige la decisión 15.** `latencia_media` de `m3_costos.json` es por **llamada**, no por caso. Para el brazo 4 son 548 llamadas en 130 casos: 3.24 s por llamada, **13.65 s por caso**. `leer_latencia_m3` ahora divide `latencia_total_s` entre `casos` cuando el artefacto los trae. | Con la lectura anterior, M4 parecía unas cuatro veces más lento que M3 de lo que es. | `test_latencia_m3_es_por_caso_y_no_por_llamada`. |
| 22 | Se añade **`delta_con_sin_imagen`**: para cada caso `exacto`, la nota con la imagen y la nota con la misma pregunta sin imagen, sobre el mismo M3. | La tabla de delta compara 3 casos de M4 contra 120 de M3: casos distintos, así que no dice si la imagen ayudó. Quitar la imagen y dejar todo lo demás igual sí lo dice, incluido el caso en que no aporta (lo pide la rúbrica). No gasta GPU: la condición con imagen sale de las trazas. | `test_delta_con_sin_imagen_separa_lo_que_aporta_de_lo_que_no`. |
