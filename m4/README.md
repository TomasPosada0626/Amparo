# M4 · Amparo ya ve

> Entrega de M4. La versión larga, con cada decisión y su evidencia, está en la
> wiki: [M4 · Componente visual — decisiones](https://github.com/TomasPosada0626/Amparo/wiki/M4-%E2%80%90-Componente-visual-%E2%80%94-decisiones).
> Lo que se cambió tras la revisión docente está en [la última sección](#revisión-docente-pr-15-y-16).

## La pregunta que necesita ojos

> *"Somos cuatro veredas que tomamos agua de esa quebrada y la curtiembre sigue
> vertiendo. Esta es la respuesta que nos dio la corporación ambiental. ¿Qué
> mecanismo constitucional nos corresponde?"*

El dato que debería cambiar la respuesta está en el papel, no en lo que la
persona escribe: la corporación **archivó la queja**. Sin ese dato, Amparo puede
ver solo una curtiembre contaminando y un perjuicio que corre, y responder
**tutela contra la curtiembre**; con él, lo correcto es **acción popular**.

El VLM lee ese dato en las tres GPU en que se ha corrido. Que M3 lo convierta en
acción popular, **no siempre**: en las dos corridas con repeticiones y la caché
vacía, acertó 2 de 6 veces con la imagen y 3 de 6 sin ella. La imagen lleva el
hecho al relato; la decisión depende de hechos de juicio que el agente pondera
distinto en cada corrida. Ver
[el delta](#delta-la-misma-pregunta-con-imagen-y-sin-ella).

## Patrón y modelo

**Patrón input, con Qwen2-VL-2B-Instruct.** El VLM lee la foto del documento y
devuelve hechos en JSON (`tipo_documento`, `entidad`, `fecha`, `plazo_dias`,
`pretension_visible`). Esos hechos se suman al relato y entran a M3. **El VLM
extrae hechos; no decide derecho.** Es el mismo principio de Amparo desde M1.

Qué se habría perdido con los otros dos patrones:

- **tool (CLIP o un clasificador):** diría el **tipo** de documento, pero el
  motor de reglas necesita los **hechos**: que la corporación **archivó** la
  queja, que la EPS **niega** un procedimiento **ordenado por el médico**.
- **output (difusión):** generar documentos jurídicos no sirve para el triaje y
  es riesgoso. Documentos, firmas y sellos no se generan como si fueran reales.

Qwen2-VL-2B corre en una T4, es el VLM visto en clase y es de la misma familia
que el generador de M1. Su debilidad conocida —fechas, números y plazos— es
justo lo que trae un documento jurídico, y por eso el caso adversarial apunta
ahí.

## Dónde se enchufa, y dónde queda M1

```python
from amparo.multimodal.sistema_visual import Amparo   # amparo/multimodal/sistema_visual.py
amparo = Amparo()                             # carga el VLM y enchufa M3
amparo.responder(pregunta, imagen)            # -> respuesta, por qué y lo leído
```

Por dentro: `ver(imagen)` lee el documento, la lectura se suma a la pregunta
como *"DATOS DEL DOCUMENTO ADJUNTO"* y el relato entra a `responder_m3`, que es
el brazo **4 · agente + reglas** de M3
([`amparo/multimodal/enchufe.py`](../amparo/multimodal/enchufe.py)): busca en el corpus de
normas, extrae hechos y el motor del art. 6 del Decreto 2591 decide. El código
de M3 no se modifica: se importa.

**Dónde queda M1.** El modelo ajustado de M1 fue el mejor clasificador de M3 en
el agregado. Para el producto con imagen se eligió el agente con reglas por dos
razones: **nunca inventa la norma** —el fundamento lo pone la regla, con 0
normas inventadas en 120 respuestas— y **cabe junto al lector visual** en una
sola T4, porque razona por API. El modelo de 7B y el VLM no caben juntos.

## La respuesta, en tres bloques

`Amparo.responder()` devuelve, además de las cinco líneas:

- **«Por qué»**: la regla del art. 6 que cerró el caso, los hechos que la
  activaron y las normas que consultó el agente. Sale de la traza del agente:
  es lo que de verdad decidió. Si Amparo se abstiene, dice que ninguna regla
  cerró el caso y muestra los hechos que anotó el agente como lo que son, sin
  decisión. *(Hasta el tag `m4-demo` mostraba igual la regla que el motor
  calcula por debajo: en m10 salía `incumplimiento_normativo` justo después de
  «prefirió no decidir».)*
- **«Leído del documento · no verificado»**: lo que extrajo el VLM, rotulado
  como lectura de un modelo, con un **aviso** cuando el texto libre trae un plazo
  que el campo `plazo_dias` no respalda. Es el caso m10.

El rótulo y el aviso son solo de presentación: el relato que recibe M3 es el
mismo que se evaluó. La demo es [`pipeline/M4_demo.ipynb`](pipeline/M4_demo.ipynb):
una interfaz donde se sube la foto y se escribe la pregunta, con los tres casos
del guion como ejemplos.

## Eval set

11 casos sobre 6 documentos **sintéticos** generados por código
([`eval_set/`](eval_set/)), con el criterio de cada caso escrito **antes** de
correr el sistema (`casos_m4.csv` entra en el commit `9fb9b59`; el primer
scorecard, en `f01bb0e`):

| criterio | casos | qué califica |
|---|---|---|
| `exacto` | 3 | el mecanismo que decide M3 |
| `campos` | 5 | lo que leyó el VLM |
| `juez_vlm` | 2 | que la respuesta se sostenga en la imagen |
| `valvula` | 1 **adversarial** | un aviso mojado sin fecha y con el plazo bajo una mancha: no hay dato que leer |

## Tres cifras, con su denominador

| | cifra | de dónde sale |
|---|---|---|
| **Calidad frente a la base** | acierta la vía en **81 de 120** casos de M3, frente a **55 de 120** de la regla trivial (decir siempre la clase más frecuente) | `results/m3_scorecard.csv`, brazo 4 |
| **Seguridad** | **0 normas inventadas en 120 respuestas** | `results/m3_scorecard.csv`, `tasa_alucinacion` del brazo 4 |
| **Tiempo de respuesta con imagen** | **mediana 10.8 s por caso** (VLM + M3, 11 casos, con los modelos ya cargados); la lectura del documento, mediana 3.7 s, y M3, 6.4 s | `scorecard_m4.csv` y `trazas_m4.json` de la [corrida de demo](#corrida-de-demo--tag-demo-final-colab-l4-2026-11-01) |

## Corrida de demo · tag `demo-final` (Colab, L4, 2026-11-01)

La corrida que respalda las cifras de la demo está en
[`corridas/20261101T203828Z_demo/`](corridas/20261101T203828Z_demo/). Su
manifiesto (`corrida_m4.json`) lo escribió la propia corrida: commit `231c4db`
(tag `demo-final`, el mismo que clona la demo), GPU NVIDIA L4, VLM en fp16, brazo
4 de M3 y el eval set con las mismas huellas del 25. Al lado está el notebook
ejecutado con sus salidas (`M4_pipeline_ejecutado.ipynb`), que la corrida del 25
no guardó.

- **Las notas son idénticas a las del 25**, caso por caso: `exacto` 3/3,
  `juez_vlm` 1.0, `campos` 0.553, `valvula` 1.0. m02, m05 y m11 cambian de vía
  frente a la corrida anterior sin cambiar su nota, porque su criterio no
  califica el mecanismo.
- **El VLM leyó exactamente lo mismo en los 11 casos** en la L4 que en la T4 del
  25.
- **Latencia por caso:** mediana **10.8 s**, media 10.9 s, máximo 17.8 s (m03).
  No hay arranque en frío: los modelos se cargan antes, en la prueba de la
  sección 3. La lectura del documento tarda una mediana de 3.7 s (entre 2.7 y
  4.4) y M3, de 6.4 s. Lo que más pesa y más varía es M3, que depende de la API
  de Groq y de cuántos pasos da el agente (entre 1 y 5 en esta corrida).
- **Reranker:** `jinaai/jina-reranker-v2` falló al importarse con transformers
  5.21 y entró `BAAI/bge-reranker-base`. Es el mismo con el que corrió
  `notebooks/M3_rag.ipynb`, que falló por el mismo error.
- **Plan B** ([`plan_b_demo.md`](corridas/20261101T203828Z_demo/plan_b_demo.md)):
  m01 responde tutela; m06, **acción popular**; m10 trae el aviso, se abstiene y
  su «Por qué» ya está corregido. Que m06 acierte aquí es una muestra, no la
  tasa: con imagen acierta 2 de 6 (ver el delta). Se deja como salió, igual que
  la corrida anterior, donde grabó tutela.

## Corrida anterior · tag `m4-demo` (Colab, L4, 2026-11-01)

En [`corridas/20261101T194319Z_demo/`](corridas/20261101T194319Z_demo/), commit
`21158cb`. Mismas notas y mismas lecturas; latencia mediana de 10.9 s. Su plan B
grabó m06 con tutela y m10 con el «Por qué» anterior al arreglo. No es la versión
de la demo, pero el sistema que decide es el mismo, y sus repeticiones se suman
en el delta.

## Resultados de la corrida oficial (Colab, T4, 2026-10-25)

| criterio | n | nota | lo que dice |
|---|---|---|---|
| `exacto` | 3 | **1.0** | M3 decide el mecanismo correcto en los 3 (tutela, cumplimiento, popular) |
| `juez_vlm` | 2 | **1.0** | las dos respuestas se sostienen en la imagen, según el propio VLM |
| `campos` | 5 | **0.553** | m02 0.50 · m03 0.60 · m05 0.75 · m07 0.67 · m09 0.25 |
| `valvula` | 1 | **1.0** | pero inventa en otro campo: ver el peor caso |

**Latencia por caso (VLM + M3):** mediana **8.7 s**, media 10.9 s. El caso más
lento es **m02, con 30.8 s**: es el que pagó la carga de los modelos. Sin él, la
mediana es 8.4 s y la media 8.9 s. *(Antes este README atribuía los 30.8 s al
primer caso, m01, que tardó 7.6 s: era un error.)*

Esa corrida no registró su commit, su GPU ni su reranker. Lo que se sabe de ella
está en [`corrida_20261025.json`](corrida_20261025.json), marcado campo por campo
como registrado, inferido o desconocido.

## Delta: la misma pregunta con imagen y sin ella

Lo único que cambia es el componente visual; M3 es el mismo. Corrida oficial,
una pasada:

| caso | esperado | con imagen | sin imagen | efecto |
|---|---|---|---|---|
| m01 · EPS | tutela | tutela | tutela | no aporta |
| m04 · alcaldía | acción de cumplimiento | cumplimiento | cumplimiento | no aporta |
| m06 · corporación ambiental | acción popular | **acción popular** | tutela | **aporta** |
| **acierto de mecanismo** | | **3/3** | 2/3 | |

**Una pasada no basta para decir dónde aporta la imagen.** El extractor de
hechos de M3 no es determinista:

- en m01, una verificación anterior hizo que M3 se abstuviera sin imagen (y ahí
  la imagen aportaba);
- en m06, la re-ejecución de la revisión docente acertó **también sin imagen**.

Contando esas tres corridas, la imagen aportó en m06 en 2 de 3. Para poder
afirmarlo había que repetir. Las dos corridas del 1 de noviembre repiten cada
caso **3 veces con imagen y 3 sin ella, con la caché de M3 vacía antes de cada
llamada**
([anterior](corridas/20261101T194319Z_demo/delta_imagen_repetido_m4.json),
[demo](corridas/20261101T203828Z_demo/delta_imagen_repetido_m4.json)):

| caso | esperado | con imagen (anterior + demo) | sin imagen (anterior + demo) |
|---|---|---|---|
| m01 · EPS | tutela | 3/3 + 3/3 = **6/6** | 3/3 + 3/3 = **6/6** |
| m04 · alcaldía | acción de cumplimiento | 3/3 + 2/3 = **5/6** | 2/3 + 2/3 = **4/6** |
| m06 · corporación ambiental | acción popular | 1/3 + 1/3 = **2/6** | 1/3 + 2/3 = **3/6** |
| **total** | | 7/9 + 6/9 = **13/18** | 6/9 + 7/9 = **13/18** |

**No se sostiene que la imagen mejore la decisión: 13 de 18 en las dos
condiciones.** Se pueden sumar porque el sistema que decide es el mismo: entre
los dos tags solo cambia `formatear()`, y el VLM leyó igual los 11 casos. En
m06, la imagen cambió la vía a la correcta en 2 de 6 repeticiones y la empeoró
en 3. Con 3 casos esto describe lo que pasó; no es una prueba.

**Una sola pasada engaña.** La de la corrida de demo dio 3/3 con imagen y 1/3
sin ella, con aporte en m04 y en m06. Al repetir, esa ventaja desaparece.

**Por qué varía m06 con la imagen bien leída.** Los planes B de las dos corridas
tienen la misma lectura y casi los mismos hechos; solo cambia
`perjuicio_irremediable`. Con él, el art. 6.3 abre su excepción y la regla cierra
en tutela (corrida anterior); sin él, cierra en acción popular (corrida de demo).
Es uno de los hechos que `amparo/nucleo/reglas.py` declara de juicio (`HECHOS_DE_JUICIO`):
no se lee del relato, se pondera. Son dos ejemplos, no una medición, pero apuntan
a M3 y no al VLM. Corregirlo sería cambiar M3, y con ello sus cifras sobre 120
casos: no se hace antes de la demo, y el criterio del caso, fijado antes de
correr, tampoco se cambia.

**Lo que cuesta la imagen:** en la corrida de demo, mediana de 10.8 s por llamada
con imagen (lectura + M3) frente a 4.5 s sin ella; la lectura sola, 3.9 s. En la
anterior, 9.6 s frente a 5.7 s.

| | métrica | valor | latencia por caso |
|---|---|---|---|
| M3 sin imagen | `acierto_juridico`, brazo 4 (n=120) | 0.675 | 13.65 s |
| M4 con imagen | casos `exacto` (n=3) | 1.0 | mediana 10.8 s |

Esta segunda tabla compara conjuntos de casos distintos (3 contra 120); se
publica porque el plan la pide, pero el delta que mide el componente es el de
arriba.

## El peor caso

**m10, el adversarial, pasa el criterio y aun así inventa.** `fecha` y
`plazo_dias` vienen vacíos, así que `valvula` = 1.0. Pero el VLM escribió en
otro campo *"Usted cuenta con un plazo de **dos semanas** hábiles"*, y debajo
de la mancha no hay número. Lo hizo en las tres GPU en que se ha corrido (T4,
RTX 5060 y L4). El criterio solo mira los campos que nombra y no lo ve; no se
cambió, porque se fijó antes de correr.

M3 se abstuvo y el plazo inventado no llegó a una decisión, **pero sí entró a
M3**, que lo da por cierto. En la corrida anterior, el agente escribió *"Existe
un mandato normativo claro: la notificación indica que el destinatario tiene dos
(2) semanas hábiles"* y anotó `incumplimiento_normativo`. En la de demo no anotó
ese hecho, pero escribió que con la fecha de recibo *"se podrá aplicar el término
de dos semanas hábiles"*. Las dos quedan en `cache/agente.json` de cada corrida.
Y se abstuvo porque la pregunta es una consulta (*"¿de qué fecha es y en cuántos días se me vence el plazo?"*), no
porque detectara el plazo dudoso. Con una pregunta que pidiera un mecanismo,
nada asegura la abstención; eso no se ha probado.

Una persona que lea esa lectura se cree el plazo, y en derecho un plazo vencido
no se recupera. **Por eso ahora la respuesta lo marca**: el bloque «Leído del
documento · no verificado» trae el aviso *"plazo en texto libre sin
plazo_dias: verificar en la imagen"*, y el «Por qué» ya no presenta como «regla
que cerró el caso» la que el motor calculó con ese hecho. Es el caso de
seguridad de la demo.

**Por la nota mínima, el peor es m09** (`campos` 0.25): la foto del acueducto
es legible y el VLM solo acierta el tipo; pierde la entidad, la fecha y el
plazo de 5 días.

También: en **m04** el VLM lee el documento al revés (*"La Alcaldía cumplirá
con el deber de publicar los contratos"*, cuando dice que **no**), y M3 acierta
solo porque la pregunta trae los hechos. Ningún aviso automático detecta esa
inversión: en la demo, la imagen se muestra junto a lo leído. **`entidad` sale
vacía en los 6 documentos**; puede ser que la válvula haga abstenerse de más al
modelo de 2B, y eso no está comprobado. Y **el VLM no lee igual en todas las
GPU**: entre la T4 y una RTX 5060, 9 de 11 lecturas coinciden y cambian m04 y
m05; entre la T4 y la L4 de las corridas del 1 de noviembre coinciden las 11.

## Límites y ética

- Los 6 documentos son **sintéticos** y llevan la etiqueta visible
  **"DOCUMENTO SINTÉTICO / GENERADO"**. No hay datos personales, firmas, sellos
  ni logos ([checklist por imagen](eval_set/imagenes/ANONIMIZACION.md)).
- **El VLM describe, no diagnostica.** La conclusión jurídica la pone el motor
  de reglas, con el artículo que la soporta.
- Un VLM pequeño que rellena un plazo o invierte una negativa puede convencer a
  alguien de que sigue a tiempo, o de que la entidad le dio la razón. Por eso su
  lectura se muestra rotulada como **no verificada**.
- El juez visual (`juez_vlm`) es el mismo VLM que leyó: no es una validación
  independiente.
- Nada de esto autoriza el uso con personas reales ni sustituye la asesoría de
  un abogado.

## Reproducir

**La corrida de evaluación**, en Colab con GPU (el notebook pide una T4; las
del 1 de noviembre se hicieron en una L4) y el secreto `GROQ_API_KEY`:
[`pipeline/M4_pipeline.ipynb`](https://colab.research.google.com/github/TomasPosada0626/Amparo/blob/demo-final/m4/pipeline/M4_pipeline.ipynb)
→ **Entorno → Reiniciar y ejecutar todo** (unos 30 min). Clona el tag
`demo-final` y escribe todo en `corridas/<id>/`: manifiesto, scorecard, trazas,
los dos deltas y el plan B de la demo. Al final descarga un `.zip` con esa
carpeta.

**La demo**:
[`pipeline/M4_demo.ipynb`](https://colab.research.google.com/github/TomasPosada0626/Amparo/blob/demo-final/m4/pipeline/M4_demo.ipynb),
mismas condiciones; deja un enlace público mientras la sesión esté abierta.

Los dos notebooks clonan **el mismo tag, `demo-final`**: lo que ve el público es
lo que se evaluó, y el manifiesto de la corrida lo prueba con su SHA (`231c4db`).
`m4-demo` es el tag de la corrida anterior. Entre los dos, en código, solo
cambia `formatear()` en `multimodal.py` (el «Por qué» al abstenerse), que no
usan el scorecard ni los deltas:
`git diff m4-demo demo-final -- src m4/harness/*.py m4/pipeline/*.py`.

**Sin GPU**: `python -m pytest tests/m4`.

**Dónde vive el código.** En `main` el código de M4 está en el paquete
`amparo/` (`amparo/multimodal/`: `sistema_visual.py`, `corrida_m4.py`,
`criterios.py`, `scorecard.py`, `enchufe.py`; la orquestación por etapas en
`amparo/pipelines/m4_multimodal.py`), tras la migración de los notebooks a
`.py` ([`docs/MIGRACION.md`](../docs/MIGRACION.md)). Los dos notebooks clonan
`demo-final`, donde ese mismo código vivía en `m4/pipeline/` y `m4/harness/`:
reproducen lo evaluado, no la estructura nueva.

## Revisión docente (PR #15 y #16)

Las dos se fusionaron con su autoría. Qué se hizo con cada punto:

| punto | qué se hizo | estado |
|---|---|---|
| **H1** · el delta no medía latencia; los 30.8 s eran de m02 | atribución corregida; las trazas registran `segundos_ver` aparte; el delta mide la latencia de las dos condiciones (PR #16 y `delta_repetido`) | hecho · corrida de demo: mediana 10.8 s por caso sin arranque en frío; con imagen 10.8 s frente a 4.5 s sin ella |
| **H2** · la lectura del VLM entra como un hecho | bloque «Leído del documento · no verificado» con el aviso de plazo (PR #16); el relato de M3 no se toca | hecho · y el plazo inventado de m10 sí entra a M3 como hecho: ver el peor caso |
| **H3** · la corrida oficial es poco trazable | el notebook clona un tag fijo y escribe `corrida_m4.json` desde la propia corrida; para la del 25, manifiesto reconstruido y rotulado | hecho · `corridas/20261101T203828Z_demo/`, commit `231c4db`, L4, con el notebook ejecutado |
| **H4** · el aporte en m06 varía entre corridas | `delta_repetido`: 3 repeticiones con la caché vacía antes de cada llamada | hecho · dos corridas: 13/18 con imagen y 13/18 sin ella; en m06, 2/6 y 3/6: no se sostiene que la imagen mejore la decisión |
| **P1** · una sola llamada, con el fundamento a la vista | `multimodal.py` con `Amparo`, la salida en tres bloques y la interfaz `M4_demo.ipynb` | hecho |
| **P2** · la confianza como característica | m10 muestra el aviso y la abstención; es el caso de seguridad del guion. El «Por qué» ya no muestra una regla cuando Amparo se abstiene | hecho |
| **P3** · tres cifras sobre una versión fija | las tres cifras de arriba; un solo tag, `demo-final`, para la evaluación y la interfaz; plan B grabado de m01, m06 y m10 | hecho · el manifiesto trae el SHA de la demo (`231c4db`) y el plan B, el «Por qué» corregido |

**Equipo:** Santiago (pipeline y `ver()`) · Lucas (documentos, eval set y
corrida del harness) · Nico (harness y tabla de delta) · Tomás y Martín (enchufe
del M3 real).
