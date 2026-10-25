# T4 · `casos_m4.csv`: qué mide cada caso y por qué ese `esperado`

11 casos sobre 6 imágenes ([`imagenes/ANONIMIZACION.md`](imagenes/ANONIMIZACION.md)).
Formato: [`FORMATO_CASOS.md`](FORMATO_CASOS.md). `validar_casos()` da `[]`.

**El `criterio` y el `esperado` de cada caso se escribieron ANTES de correr el
sistema** (regla de M2). Ni el VLM ni M3 se han corrido sobre estas imágenes:
no hay GPU en local y la corrida de T6 es en Colab. El commit que sube este
archivo es anterior a cualquier `scorecard_m4.csv`, y así lo puede comprobar
T9 en el historial de git.

| Criterio | Casos | Qué califica |
|---|---|---|
| `exacto` | m01, m04, m06 | El mecanismo final de M3: tutela, cumplimiento y popular, uno de cada uno, para ver si las reglas enrutan bien o todo colapsa a tutela |
| `campos` | m02, m03, m05, m07, m09 | Lo que leyó el VLM (su JSON) |
| `juez_vlm` | m08, m11 | Que la respuesta final se sostenga en la imagen |
| `valvula` | m10 (**adversarial**) | Que el VLM deje en null lo que no se ve |

## Diseño: `exacto` y `campos` sobre la misma imagen

`ver(imagen)` no recibe la pregunta y genera con `do_sample=False`, así que **la
lectura del VLM es la misma** en todos los casos de una imagen. Por eso cada
documento de un caso `exacto` tiene también un caso `campos`:

| Imagen | `exacto` | `campos` de la misma lectura |
|---|---|---|
| doc01 (EPS) | m01 → `tutela` | m02 |
| doc03 (alcaldía, contratos) | m04 → `accion_cumplimiento` | m05 |
| doc04 (corporación ambiental) | m06 → `accion_popular` | m07 |

Así, si un `exacto` falla, la traza separa las dos causas que `diagnosticar()`
no puede separar sola (DECISIONES.md, 12). Si el `campos` de esa imagen sacó
1.0, el VLM leyó bien y el error está en M3. Si sacó poco, el error empezó en
la lectura.

## Caso por caso

| id | Imagen | Criterio | `esperado` | Por qué |
|---|---|---|---|---|
| m01 | doc01 | exacto | `tutela` | La EPS niega una cirugía ordenada por el médico tratante a una persona de 68 años. Hay un derecho fundamental (salud) con afectación individual concreta y un sujeto de especial protección. Ninguna causal del art. 6 D.2591 cierra el paso. Mismo patrón que E01 del eval set de M3. |
| m02 | doc01 | campos | tipo, entidad, fecha, pretensión | `cadera` es el dato que M3 necesita para saber qué se negó. |
| m03 | doc02 | campos | tipo, entidad, fecha, `plazo_dias: 15`, pretensión | Es el único plazo del documento ("quince (15) días hábiles"). |
| m04 | doc03 | exacto | `accion_cumplimiento` | Se pide que la autoridad cumpla una norma (art. 10 Ley 1712 de 2014) y el usuario dice que no lo afecta en lo personal. Es incumplimiento normativo sin afectación individual (art. 9 L.393), y la petición previa con la negativa constituye la renuencia. Mismo patrón que E30. |
| m05 | doc03 | campos | tipo, entidad, fecha, pretensión | `contratos` es el objeto de la negativa. |
| m06 | doc04 | exacto | `accion_popular` | Cuatro veredas, una fuente de agua contaminada: es un interés colectivo (ambiente sano, salubridad) y nadie pide lo suyo ante un perjuicio irremediable. Aplica el art. 6.3 D.2591 sin su excepción. Mismo patrón que E09. |
| m07 | doc04 | campos | tipo, `entidad: "claro"`, fecha | El documento nombra al emisor de dos formas correctas: "Corporación Autónoma Regional del Río Claro" y "CORPORIOCLARO". El fragmento tiene que estar en las dos, y por eso es `claro` y no `rio claro`. |
| m08 | doc05 | juez_vlm | vacío | Notificación de corte de agua. El juez mira si lo que afirma M3 (accionado, pretensión) coincide con el documento. |
| m09 | doc05 | campos | tipo, entidad, fecha, `plazo_dias: 5` | Foto de celular legible, girada. Es el único plazo del documento. |
| m10 | doc06 | **valvula** | `fecha\|plazo_dias` | **Adversarial.** La fecha y el número del plazo no existen en la imagen (esquina arrancada y mancha de tinta, sin nada debajo). La pregunta pide justo esos dos datos. |
| m11 | doc01 | juez_vlm | vacío | Mismo documento que m01 con otra pregunta: el juez revisa si la respuesta final habla de la cirugía y la EPS que aparecen en la carta. |

## Regla de los fragmentos (`entidad`, `fecha`, `pretension_visible`)

Para cada fragmento elegí la parte que **tiene que estar en cualquier lectura
correcta** y que no aparecería por casualidad. Las entidades llevan el nombre
del municipio también en la dependencia ("Secretaría de Planeación Municipal
de Puerto Almendro"), para que leer la dependencia en vez del encabezado no
cuente como error. Las fechas van tal como aparecen en la imagen.

## Con el sustituto de M3

Mientras T7 no enchufe el M3 real, `exacto` (m01, m04, m06) y `juez_vlm` (m08,
m11) **no significan nada**: el sustituto no responde en el formato de Amparo.
`campos` y `valvula` sí valen, porque califican al VLM. Esos números no se
reportan como resultado de M4.
