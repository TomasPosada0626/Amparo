# M3 — Lo medido en CPU y lo que falta correr en Colab (2026-10-13)

## Lo que M3 tiene que lograr

Con la decisión del 2026-10-13 (`docs/m1_protocolo_aceptacion.md`), el objetivo es
que **el sistema responda bien lo que se le pregunta**, medido con RAGAS (con la
abstención estricta de H5) y las rutas. Cuánto se abstiene ya no es criterio.

El generador es **v1**, el adaptador con que se cerraron M1 y M2. S08 y S10 lo
comprueban por huella antes de cargarlo (`pipeline.verificar_adaptador`), y las
dos corridas que hay en el repo (`results/m3_s08_2026-10-09/`,
`results/m3_s10_2026-10-09/`) ya se hicieron con él y con el índice actual.

## La palanca: el orden de la búsqueda

Medido en CPU sobre las 45 consultas gold, con el gold de artículos aprobado y el
índice evaluado (`19657d22583f93d0`). Cuántas consultas tienen el artículo que
responde entre los primeros *k* fragmentos:

| configuración | @1 | @3 | **@5** | @10 |
|---|---|---|---|---|
| **A** — producción: denso + enrutador | 7 | 17 | **21** | 26 |
| enrutador + reranker | 11 | 19 | 23 | 27 |
| **C** — enrutador + híbrido + reranker | **11** | **21** | **25** | **29** |
| C con 50 candidatos al reranker | 9 | 18 | 25 | 29 |

El modelo recibe 5 fragmentos, así que @5 es lo que importa. C sube de 21 a 25 y
pone primero el artículo correcto en 11 casos en vez de 7.

**No está demostrado.** Frente a A, C gana 8 casos (9007, 9040, 9043, 9046, 9060,
9063, 9068, 9069) y pierde 4 (9004, 9053, 9061, 9067). Con 12 casos que cambian,
una prueba de signos no lo distingue del azar (p ≈ 0,4). Darle 50 candidatos en
vez de 30 no mejora. El detalle por caso está en
`results/m3_busqueda_cpu_2026-10-13/puestos_gold.json`.

Lo que **no** sirve, también medido: quitar el enrutador (16/45 en @5) y el
filtro de derogatorias (21/45 con y sin él; queda implementado y apagado, H12).

## La decisión, fijada antes de correr

**Se adopta C como configuración de producción si**, en el RAGAS de las 45 gold:

1. la **media de las cuatro métricas** (faithfulness, answer relevancy, context
   precision y context recall) es **mayor que la de A**, y
2. **ninguna de las cuatro baja más de 0,03** frente a A.

Si no se cumplen las dos, o falta algún dato, se queda A. La latencia se reporta
y no decide. La regla la aplica `tools/evaluation/decision_busqueda.py` dentro
de S10 (fase 5d), no una lectura a ojo; sus pruebas fijan la tolerancia en 0,03.

**Lo que hay que saber antes**: aplicada a la corrida A/B/C del 2026-10-09, la
regla habría dejado A, porque C bajaba context recall en 0,04. Aquella corrida
usaba la regla vieja de abstención (H5) y otro código, así que se vuelve a medir;
pero que gane A es un resultado posible y válido.

## Cómo se reparte el trabajo entre S08 y S10

- **S08** genera las respuestas de A, B y C (75 consultas cada una) y las guarda
  en `rag/corridas_abc/`. **No tiene juez.**
- **S10** genera la corrida de una pasada (configuración de `config.py`, hoy A),
  calcula su RAGAS y, en la fase 5b, el RAGAS de A, B y C a partir de lo que
  guardó S08. En la fase 5d **aplica la decisión** y pasa el **juez contra el
  criterio** de cada caso por el sistema elegido (la cifra de "responde bien",
  hoy 1/45 gold). En la 5c mide las rutas, también del sistema elegido.

Con una corrida de S08 y una de S10 queda todo: no hace falta repetir S10.

## Qué correr en Colab, en orden

1. **`colab/m3_s08_rag_avanzado.ipynb`, completo, con GPU** (A100 o L4). Unos 30
   minutos de generación en A100 (7,3 s por consulta en la corrida anterior).
2. **`colab/m3_s10_rag_agentico.ipynb` hasta la celda que guarda las respuestas
   (Fase 4), con GPU.** Unos 10 minutos.
3. **Desconectar la GPU.** Abrir un entorno **sin GPU** (no gasta unidades) y
   correr de S10: las de instalación, la del índice (Fase 1, sin la del modelo) y
   de la Fase 5 en adelante. Las respuestas se cargan de Drive. Lo que queda es
   Groq y e5 en CPU.
4. Me avisas: leo los resultados de Drive y aplico la decisión en
   `tools/rag/config.py`.

**Total de GPU: unos 40-50 minutos de A100**, unas 5-6 unidades.

**Lo que necesitan los secretos de Colab:**
- `GROQ_API_KEY`: obligatorio para la Fase 5 de S10.
- `WANDB_API_KEY`: **opcional**. Sin él, W&B queda sin conexión; con una key
  inválida, también (no tumba la celda).

**El cupo de Groq.** RAGAS son unos 110 mil tokens del juez por sistema: una
pasada, A, B y C. A toma las notas de una pasada sin gastar juez solo en los
casos en que las dos sesiones generaron exactamente el mismo texto, y entre
sesiones puede haber deriva numérica. Con el juez de criterio (75 llamadas), en
torno a 450-560 mil tokens. Si el cupo diario se agota, la celda se detiene
sola; al volver a correrla otro día, sigue desde el checkpoint sin repetir
llamadas. Por eso esa parte va en el entorno sin GPU.

## Antes de correr: la prueba de humo

`.venv/Scripts/python.exe -m tools.humo_m3` ejecuta S08 y S10 completos en CPU
con 5 casos, sustituyendo solo Qwen, el juez de Groq y Drive, y después repite
S10 en una sesión nueva sin generar. El 2026-10-13 dio "TODO OK" por los dos
caminos de la decisión (gana A y, con `HUMO_FORZAR_C=1`, gana C).

## Lo que queda abierto y no bloquea

- **Artículo 57 del CST** (H11): el índice tiene la versión anterior a la reforma
  de 2025. Corregirlo exige el texto oficial y reconstruir el índice, lo que
  cambia todas las huellas (gold, auditoría, dataset). Toca un caso gold (9051).
  Se hace una sola vez, si se decide, al final.
- **Enrutamiento** (H13): sin diseño de corrección; quitarlo empeora (arriba).
- **El artículo correcto no está ni en el top-30 en 10 consultas** (9010, 9033,
  9038, 9042, 9048, 9049, 9051, 9055, 9058, 9064). Ningún reordenamiento las
  arregla: son de cómo se escribe la consulta frente al texto de la norma.
