# M2 — Por qué los dos jueces no coinciden (H14)

**Medido el 2026-10-13 sobre `results/m2_2026-10-09/`**, la corrida de M2 con v1
(`hash_adaptador` `8ce3cc2bc9306974`). Sin GPU ni llamadas nuevas al juez: se
cruzan, par por par, las notas de la rúbrica (`groq_validacion.jsonl`), los
veredictos del cara a cara (`groq_cara_a_cara.json`) y la longitud de cada
respuesta.

## El desacuerdo

| | baseline | afinado (v1) |
|---|---|---|
| rúbrica, compuesto 1–5 | 3,47 | **4,12** |
| cara a cara, pares ganados en los dos órdenes | **106** | 73 |

## La explicación: no se contradicen, pesan cosas distintas

**1. La concisión decide el compuesto, y el cara a cara no la mira.** El
compuesto promedia cuatro dimensiones, una de ellas la concisión; el prompt del
cara a cara ordena corrección jurídica, prudencia y utilidad, sin concisión. Las
medias por dimensión:

| dimensión | baseline | afinado |
|---|---|---|
| corrección jurídica | 2,87 | 3,37 |
| prudencia | 3,99 | 4,43 |
| claridad y utilidad | 4,21 | 4,23 |
| **concisión** | **2,81** | **4,45** |

El afinado responde con 46 palabras de mediana y el baseline con 220-236. En los
106 pares que gana el baseline en el cara a cara, la rúbrica le da al afinado
mejor concisión en **94**: es la dimensión que más separa a los dos jueces.

**2. En el fondo, los jueces están de acuerdo.** Comparando solo la corrección
jurídica, la rúbrica y el cara a cara eligen al mismo modelo en **109 de 130**
pares decididos (84 %). Sin la concisión (media de las otras tres), en 122 de 149.

| la rúbrica prefiere, en corrección jurídica | gana en el cara a cara el afinado | gana el baseline |
|---|---|---|
| afinado | 64 | 20 |
| baseline | 1 | 45 |
| empate | 8 | 41 |

**3. Lo que el cara a cara premia de más es la completitud, no el largo.** En
los pares que gana el baseline, la rúbrica también lo ve mejor en el fondo
(corrección 3,50 frente a 3,02; claridad y utilidad 4,47 frente a 4,02): cuando
los dos aciertan, el baseline orienta más (pasos, pruebas, alternativas). No es
un sesgo de longitud: la tasa de victoria del baseline **no sube** con la razón
de longitudes (39/59 en el tercio de razón baja, 34/59 en el medio, 33/61 en el
alto).

**4. El cara a cara tiene un sesgo de posición apreciable**: 42 de 231 pares
(19 %) cambian de ganador al invertir el orden. Por eso se cuenta solo lo que
gana en los dos órdenes.

## La lectura para M2

- **El afinado es más correcto y más prudente en promedio**, y mucho más breve:
  la rúbrica lo muestra con diferencia demostrable en corrección, prudencia y
  concisión, y comete menos errores graves (entidades inventadas: baseline
  10,8 %).
- **El baseline es más completo** cuando los dos aciertan, y por eso gana más
  pares en el cara a cara.
- **¿Cuál es mejor? Depende de cuánto pese la brevedad**, y eso lo define el
  producto: el prompt del sistema pide *"responde de forma breve y en lenguaje
  claro"*. Con esa definición, la del compuesto, el afinado es mejor. Lo que no
  se puede afirmar es que sea mejor en todo: en completitud de la orientación no
  lo es.

## Limitación

La corrida del 2026-10-09 es anterior a la fijación de la revisión del modelo
base (H6), así que no la registró. Usó las versiones que hoy están fijadas en
`colab/requirements-m2.txt` (transformers 5.19.0, peft 0.21.2).
