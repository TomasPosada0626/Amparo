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

S08 ya compara A, B y C con el enrutador encendido (`SISTEMAS` sobre
`pipeline.answer_query`), así que la corrida de Colab responde la pregunta sin
cambiar código. **Se adopta C como configuración de producción si**, en el RAGAS
de S08 sobre las 45 gold:

1. la **media de las cuatro métricas** (faithfulness, answer relevancy, context
   precision y context recall) es **mayor que la de A**, y
2. **ninguna de las cuatro baja más de 0,03** frente a A.

Si no se cumplen las dos, se queda A. La latencia se reporta y no decide: el
reranker es lento en CPU pero en GPU no pesa.

## Qué correr en Colab, en orden

1. **`colab/m3_s08_rag_avanzado.ipynb`**, completo, en GPU (A100 o L4). Necesita
   la key de Groq en los secretos de Colab (el juez de RAGAS). Corre A, B y C con
   v1 sobre las 75 consultas del eval set y calcula RAGAS.
2. Con el resultado, **yo aplico la decisión** (cambiar o no `USE_HYBRID` y
   `USE_RERANK` en `tools/rag/config.py`) y la dejo escrita.
3. **`colab/m3_s10_rag_agentico.ipynb`**, completo, con la configuración que
   quede. Es la corrida del sistema que se entrega: RAGAS, rutas y la
   comparación con M2.

Las dos verifican el adaptador y el índice por huella antes de medir, e instalan
las versiones fijadas (`colab/requirements-m3.txt`).

## Lo que queda abierto y no bloquea

- **Artículo 57 del CST** (H11): el índice tiene la versión anterior a la reforma
  de 2025. Corregirlo exige el texto oficial y reconstruir el índice, lo que
  cambia todas las huellas (gold, auditoría, dataset). Toca un caso gold (9051).
  Se hace una sola vez, si se decide, al final.
- **Enrutamiento** (H13): sin diseño de corrección; quitarlo empeora (arriba).
- **El artículo correcto no está ni en el top-30 en 10 consultas** (9010, 9033,
  9038, 9042, 9048, 9049, 9051, 9055, 9058, 9064). Ningún reordenamiento las
  arregla: son de cómo se escribe la consulta frente al texto de la norma.
