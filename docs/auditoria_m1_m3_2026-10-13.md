# Auditoría de M1, M2 y M3 antes de correr M3 en Colab — 2026-10-13

**Pregunta:** ¿M1 y M2 están cerrados, M3 está completo en código y se puede
correr sin gastar unidades de cómputo en vano? **Respuesta corta:** M1 y M2 sí;
M3 está completo en código **después de esta auditoría**, que encontró y
corrigió cinco fallos que habrían costado unidades o resultados. Lo que queda es
ejecutar, y lo que no se puede probar en CPU está acotado abajo.

## Cómo se verificó

- `pytest -q`: **915 passed, 4 skipped**.
- **Prueba de humo** (`tools/humo_m3.py`): S08 y S10 ejecutados **completos en
  CPU**, celda por celda en un solo espacio de nombres como un kernel de Colab,
  sustituyendo solo Qwen, el juez de Groq, Drive y nvidia-smi. Corren de verdad
  la búsqueda (e5 + FAISS + enrutador + BM25 + cross-encoder), la verificación de
  citas, RAGAS con los embeddings de e5, la decisión de búsqueda, el juez de
  criterio, las rutas y los manifiestos. Después repite S10 en una sesión
  nueva sin generar. **"TODO OK" por los dos caminos de la decisión** (gana A, y
  gana C forzado).
- Comprobaciones cruzadas de huellas, ids, contenido y prompts entre módulos.

## M1 — cerrado

| | estado |
|---|---|
| adaptador adoptado | v1 `8ce3cc2bc9306974`, el `main` de Hugging Face (`docs/m1_cierre.md`) |
| por qué | con el protocolo del 2026-10-13 (responder bien), es el que mejor responde |
| limitaciones escritas | 1 cita no verificable en 103 (el verificador del RAG la intercepta), 6 rutas incorrectas |
| notebook | listo si se reentrena: revisión fijada, prueba barata, etiqueta `v5` (v3 y v4 descartados) |

Corregido hoy: el notebook todavía nombraba `v4` al próximo entrenamiento.

## M2 — cerrado

| debe coincidir con M1 | resultado |
|---|---|
| adaptador evaluado | v1 `8ce3cc2bc9306974` ✓ |
| las 231 preguntas de validación | mismas ids **y mismo contenido** que en M1 ✓ |
| el prompt con que se pregunta | idéntico al de entrenamiento de M1 ✓ |
| eval set | `a5151999c2095d00`, el mismo que usa M3 ✓ |

El desacuerdo entre jueces está explicado (`docs/m2_desacuerdo_jueces.md`).
Limitación: la corrida es anterior a la fijación de la revisión (H6).

## M3 — completo en código, falta ejecutar

**Enlaces con M1 y M2**, verificados: S08 y S10 comprueban por huella que el
adaptador sea v1 antes de cargarlo (una sola constante,
`config.HUELLA_ADAPTADOR_PRODUCCION`, que también lee M2); el prompt del RAG es el
de entrenamiento (prueba `test_system_prompt_coherencia`); revisión del modelo
base fijada; índice verificado por huella antes de medir; mismo eval set; S10
compara contra la corrida de M2 que está en el repo.

**Lo que la auditoría encontró y corrigió:**

| # | fallo | qué habría pasado en Colab |
|---|---|---|
| 1 | El plan decía que S08 calculaba RAGAS y decidía. **S08 no tiene juez**: lo calcula S10 | correr S08 y esperar una decisión que no llega |
| 2 | Nadie medía "responde bien" (el juez contra el criterio de cada caso) en el RAG | sin la cifra que importa; ahora S10 la mide sola (fase 5d) |
| 3 | La decisión A/C iba a leerse a ojo | ahora la aplica `decision_busqueda.py`, con la regla escrita antes |
| 4 | Una key de W&B inválida tumbaba la celda de registro | W&B se quitó del proyecto (no aportaba resultados) |
| 5 | RAGAS en una sesión nueva fallaba (`registros` no existía) | obligaba a hacer RAGAS con la GPU encendida, esperando el cupo de Groq |

Además: un texto de S10 todavía decía que las abstenciones se excluían de las
rutas, y ya no es así (H22).

## Lo que no se puede probar en CPU, y por qué no preocupa

- **Qwen real en GPU** (carga en 4-bit, generación). Es el mismo camino de código
  y las mismas versiones (`colab/requirements-m3.txt`) con que S08 y S10 ya
  corrieron el 2026-10-09; la carga se probó con dobles (revisión fijada, H6).
- **Groq real.** El juez se probó con su formato; ante cupo agotado, la celda se
  detiene y retoma desde el checkpoint (probado: la sesión nueva reusa el
  checkpoint sin repetir llamadas).
- **Deriva numérica entre sesiones**: A (de S08) y una pasada (de S10) pueden no
  ser idénticas, y entonces A cuesta su propio RAGAS. Más cupo de Groq, no un
  error.

## Lo que M3 no va a resolver con esta corrida

- La búsqueda trae el artículo correcto en 21 de 45 (25 con C, medido en CPU).
  Hay 10 consultas cuyo artículo no está ni en el top-30: el criterio "gold que
  cumplen" va a seguir lejos de 45 aunque el modelo responda bien con lo que
  recibe.
- Artículo 57 del CST (H11) y enrutamiento (H13): abiertos, no bloquean.

## Para correr

El orden y los costos están en `docs/m3_plan_colab_2026-10-13.md`: S08 con GPU,
S10 hasta la Fase 4 con GPU, el resto de S10 en un entorno sin GPU. Unos 40-50
minutos de A100.
