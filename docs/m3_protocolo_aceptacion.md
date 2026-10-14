# M3 — Protocolo de aceptación, fijado antes de medir

Cómo se decide que M3 está cerrado. Cada regla se escribe **antes** de ver la
cifra que juzga, como en M1 (`docs/m1_protocolo_aceptacion.md`).

## 1. El juez del RAG (fijado el 2026-10-14, antes de volver a juzgar)

**Por qué cambia.** S10 juzgaba el RAG con el juez de M2, diseñado para el
modelo sin contexto: no veía los fragmentos que recibió el modelo y su regla era
"no cumple si afirma un número de artículo sin poder verificarlo". Así castigaba
justo lo que se le pide al RAG. En la corrida del 2026-10-14, 19 de los 22 "no
cumple" en gold culpaban a las citas, mientras que el verificador, que sí ve el
contexto, encontró 0 citas sin respaldo (`docs/m3_resultados_colab_2026-10-14.md`).

**La regla vigente** (`tools/evaluation/juez_rag.py`, versión `rag-2026-10-14b`).
Decisión de Tomás: darle libertad al sistema; lo que importa es que responda lo
que se le pregunta.

- El juez **ve los fragmentos** que recibió el modelo, con su norma y artículo.
- El criterio de cada caso es una **guía** de lo que una buena respuesta debería
  orientar, no una lista que haya que cumplir palabra por palabra.
- **cumple**: responde lo central de la consulta, de forma útil y correcta. No
  tiene que mencionar todo lo de la guía, pero sí lo esencial (la protección, el
  plazo o la entidad que es la clave del caso).
- **parcial**: va en la dirección correcta, pero omite algo esencial, se apoya en
  un artículo que no aplica, o tiene una imprecisión menor.
- **no cumple**: no responde (se niega o solo remite sin orientar), responde
  otra cosa, o tiene un error jurídico que llevaría al usuario a actuar mal.
- **Citar artículos de los fragmentos que aplican está bien**, aunque el
  criterio diga "sin citar el número de ley": esos criterios se escribieron para
  el modelo sin RAG.
- **Citar un artículo que no aplica es error aunque esté en los fragmentos**:
  estar en los fragmentos no lo hace pertinente.
- En los adversariales, la guía describe la trampa: cumple si no cae en ella.

**Por qué hay una versión b.** La primera (`rag-2026-10-14`) solo castigaba la
cita que no estaba en los fragmentos y además no aplicaba, y daba "cumple" con
orientar "en lo principal". Al revisar su línea base (17 cumple), unos 7 u 8
eran generosos: 9063 citaba bonos pensionales para una pregunta por el valor de
la pensión, 9033 no mencionaba la estabilidad reforzada, 9039 no decía que el
reporte tiene un límite de tiempo. Es el error de procedencia frente a
pertinencia que `criterio_contexto.py` ya documentaba. Tomás aprobó corregirlo
el 2026-10-14, **antes de medir con el juez ningún cambio de búsqueda**; la meta
no cambió. Con la versión b, 7 de 10 casos generosos bajaron a parcial o no
cumple y los 7 claramente buenos se mantuvieron. No es perfecto: 9063 sigue
saliendo "cumple".

**Los criterios que prohíben citar no se borran de `data/eval_set.json`.** La
regla de arriba ya los deja sin efecto en el RAG, y el archivo se queda como
está por dos razones: su huella (`a5151999c2095d00`) liga M2 con M3, y para el
modelo sin contexto (M2) esos criterios siguen siendo correctos. Son los gold
9001 y 9031 ("sin citar el número de ley"), además de dos adversariales (9102 y
9104) que prohíben *inventar* un número, cosa que la regla nueva sigue
castigando.

**El techo del juez** (medido el 2026-10-14, `results/m3_juez_rag_2026-10-14b/referencia/`):
las respuestas de referencia del eval set, juzgadas con los mismos fragmentos que
recibió A, sacan **43 de 45 gold** (2 parcial) y 29 de 30 adversariales. El juez
no es inalcanzable: una respuesta buena pasa. Es un techo optimista, porque esas
respuestas se escribieron junto con los criterios.

**Lo que mide y lo que no.** El juez es un modelo (Groq), no el abogado: es una
medida automática para comparar sistemas entre sí con la misma vara, no un
veredicto jurídico. Volver a juzgar las mismas respuestas mueve las cifras unos
pocos casos. Medido el 2026-10-14 con la versión b, repitiendo el juicio entero:
39 de 45 veredictos gold iguales, y el total de "cumple" pasó de 13 a 14
(`results/m3_juez_rag_2026-10-14b/repeticion/`). Una diferencia de 1 a 3 casos
no se lee como mejora.

## 2. La meta de M3 (FIJADA el 2026-10-14 por Tomás)

Fijada antes de volver a juzgar las respuestas guardadas: ninguna cifra del juez
del RAG se había visto. No se cambia después de ver resultados.

| | hoy | meta |
|---|---|---|
| **Búsqueda**: artículo correcto en el top-5, 45 gold | 21 | **≥ 28** |
| **Respuesta**: gold que "cumplen" con el juez del RAG | por medir (línea base) | **línea base + 5 o más** |
| **Validación**: las preguntas nuevas | — | la configuración final no queda peor que la de hoy en ellas |

- La línea base de respuesta es la corrida del 2026-10-14 vuelta a juzgar con el
  juez del RAG. La meta es relativa a ella, y "+5" es mayor que el ruido medido
  del juez.
- **Línea base vigente** (`results/m3_juez_rag_2026-10-14b/`, juez
  `rag-2026-10-14b`): gold **13 cumple**, 22 parcial, 10 no cumple;
  adversariales 10, 8 y 12. **La meta de respuesta es ≥ 18 de 45.** (Con la
  versión a, ya retirada, la línea base era 17: `results/m3_juez_rag_2026-10-14/`.)
- Las preguntas nuevas las escribe el equipo (Leonardo lo delegó el
  2026-10-14). Se escriben antes de los experimentos de búsqueda y no se usan
  para elegir nada: solo para confirmar al final que la mejora no es de las 45
  con que se ajustó.
- **Escritas el 2026-10-14**: `data/preguntas_confirmacion_m3.json`, 26
  preguntas gold, huella `2661a9f3bb16c9b9`
  (`python -m tools.evaluation.preguntas_confirmacion --verificar`). Cada
  artículo gold se comprobó contra el texto del índice `19657d22583f93d0`, y
  ninguna se parece a las 45 gold ni a las 2580 del entrenamiento (Jaccard
  < 0,5). Tres borradores que repetían la situación de una gold (9037, 9032 y
  9046) se reemplazaron antes de congelar. Quedan congeladas: no se editan
  después de ver resultados.

## 3. Cómo se elige la búsqueda que va a GPU (fijado el 2026-10-14, antes de ver R2)

Los candidatos se miden en CPU sobre las 45 gold, sin piso, con la vara de
`docs/m3_paso7_busqueda_2026-10-14.md`. Producción da 20 en el top-5.

1. Pasa a GPU el candidato con **más aciertos en el top-5**, solo si supera a
   producción por **3 o más** (menos que eso se confunde con elegir al azar
   entre variantes medidas sobre las mismas 45).
2. Empate en el top-5: el de más aciertos en el top-3; si sigue el empate, el
   que cambia menos cosas frente a producción.
3. Antes de escribirlo, se mide el elegido **con el piso de producción** (0,81):
   si con piso pierde la ventaja, se anota y se decide con esa cifra.
4. Queda en `results/m3_paso7_2026-10-14/busqueda_elegida.json`, que es lo que
   lee el notebook `colab/m3_paso7_corrida_final.ipynb`.

Elegir para GPU no es adoptar. Se adopta en producción solo si, con las
respuestas generadas, cumple la regla de búsqueda de
`docs/m3_plan_colab_2026-10-13.md` (media de RAGAS mayor que A, ninguna métrica
baja más de 0,03), no empeora en las preguntas nuevas y el juez del RAG no lo
da peor que A.

## 3b. Cuándo se adopta el bloque de servicio v2 (fijado el 2026-10-14, antes de generarlo)

R quedó en producción; el bloque v1 no (casi duplicó las abstenciones). El v2
(`prompt_template.INSTRUCCIONES_DE_SERVICIO_V2`) se compara contra R, una sola
variable, y se adopta solo si cumple las tres:

1. **Eval set: ≥ 18 de 45 gold bien respondidas** con el juez del RAG (la meta;
   R da 16).
2. **Preguntas nuevas: no menos que R** (11 de 26).
3. **Abstención pura en gold: no más de 10** (R: 8; tolerancia de 2).

Si no cumple, se queda R sin bloque y M3 se cierra con la meta no alcanzada y
documentada.

## 4. Lo que no cambia

- El sistema que se entrega sigue siendo A mientras ninguna configuración nueva
  pase la regla de búsqueda de `docs/m3_plan_colab_2026-10-13.md`.
- Nada se corre en GPU ni gasta Groq sin autorización de Tomás.
