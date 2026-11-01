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
acción popular, **no siempre**: en la corrida de demo, con 3 repeticiones y la
caché vacía, acertó 1 de 3 veces con la imagen y 1 de 3 sin ella. La imagen
lleva el hecho al relato; la decisión depende de dos hechos de juicio que el
agente pondera distinto en cada corrida. Ver
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
from multimodal import Amparo                 # m4/pipeline/multimodal.py
amparo = Amparo()                             # carga el VLM y enchufa M3
amparo.responder(pregunta, imagen)            # -> respuesta, por qué y lo leído
```

Por dentro: `ver(imagen)` lee el documento, la lectura se suma a la pregunta
como *"DATOS DEL DOCUMENTO ADJUNTO"* y el relato entra a `responder_m3`, que es
el brazo **4 · agente + reglas** de M3
([`pipeline/enchufe_m3.py`](pipeline/enchufe_m3.py)): busca en el corpus de
normas, extrae hechos y el motor del art. 6 del Decreto 2591 decide. `src/` no
se modifica: se importa.

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
  decisión. *(Hasta la corrida de demo mostraba igual la regla que el motor
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
| **Tiempo de respuesta con imagen** | **mediana 10.9 s por caso** (VLM + M3, 11 casos, con los modelos ya cargados); la lectura del documento, mediana 3.8 s, y M3, 7.0 s | `scorecard_m4.csv` y `trazas_m4.json` de la [corrida de demo](#corrida-de-demo--tag-m4-demo-colab-l4-2026-11-01) |

## Corrida de demo · tag `m4-demo` (Colab, L4, 2026-11-01)

La corrida que respalda las cifras de la demo está en
[`corridas/20261101T194319Z_demo/`](corridas/20261101T194319Z_demo/). Su
manifiesto (`corrida_m4.json`) lo escribió la propia corrida: commit `21158cb`
(tag `m4-demo`), GPU NVIDIA L4, VLM en fp16, brazo 4 de M3 y el eval set con
las mismas huellas del 25. Al lado está el notebook ejecutado con sus salidas
(`M4_pipeline_ejecutado.ipynb`), que la corrida del 25 no guardó.

- **Las notas son idénticas a las del 25**, caso por caso: `exacto` 3/3,
  `juez_vlm` 1.0, `campos` 0.553, `valvula` 1.0.
- **El VLM leyó exactamente lo mismo en los 11 casos** en la L4 que en la T4 del
  25.
- **Latencia por caso:** mediana **10.9 s**, media 10.7 s, máximo 14.1 s. No
  hay arranque en frío: los modelos se cargan antes, en la prueba de la
  sección 3. La lectura del documento tarda una mediana de 3.8 s (entre 2.8 y
  4.5) y M3, de 7.0 s. Lo que más pesa es M3, que depende de la API de Groq y
  de cuántos pasos da el agente (entre 1 y 5 en esta corrida). La del 25 no
  registró `segundos_ver`, así que su diferencia con los 8.7 s de entonces no
  se puede repartir.
- **Reranker:** `jinaai/jina-reranker-v2` falló al importarse con transformers
  5.21 y entró `BAAI/bge-reranker-base`. Es el mismo con el que corrió
  `notebooks/M3_rag.ipynb`, que falló por el mismo error.
- **Plan B** ([`plan_b_demo.md`](corridas/20261101T194319Z_demo/plan_b_demo.md)):
  m01 y m10 salen como en el scorecard; **m06 grabó «acción de tutela»**, una
  de las fallas que mide el delta repetido. Se deja como salió: repetirlo
  hasta que acierte sería escoger a mano una grabación que se presenta como
  real. Su m10 se grabó con el «Por qué» anterior al arreglo; el plan B que
  se usa en la demo es el de la corrida desde `demo-final`.

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
afirmarlo había que repetir. La pasada única de la corrida de demo dio lo
mismo que la del 25 (3/3 con imagen, 2/3 sin ella, aporta en m06), y luego
repitió cada caso **3 veces con imagen y 3 sin ella, con la caché de M3 vacía
antes de cada llamada**
([`delta_imagen_repetido_m4.json`](corridas/20261101T194319Z_demo/delta_imagen_repetido_m4.json)):

| caso | esperado | con imagen | sin imagen | lo que hizo la imagen |
|---|---|---|---|---|
| m01 · EPS | tutela | 3/3 | 3/3 | nada: acierta igual |
| m04 · alcaldía | acción de cumplimiento | 3/3 | 2/3 | evitó una abstención en 1 de 3 |
| m06 · corporación ambiental | acción popular | **1/3** | **1/3** | acertó en 1, empeoró en 1 |
| **total** | | **7/9** | **6/9** | |

**Con estas repeticiones no se sostiene que la imagen mejore la decisión.** La
diferencia del total sale de m04, y en m06 la imagen acertó una vez y empeoró
otra. Contando todas las veces que esa corrida respondió m06 con la imagen (el
scorecard, las 3 repeticiones y el plan B), acertó 2 de 5.

**Por qué falla m06 con la imagen bien leída.** En el plan B, el agente anota
`derecho_colectivo`, pero también `titular_pide_lo_suyo` y
`perjuicio_irremediable`; con esos dos, el art. 6.3 abre su excepción y la
regla cierra en tutela. Son dos de los hechos que `src/reglas.py` declara de
juicio (`HECHOS_DE_JUICIO`): no se leen del relato, se ponderan, y el agente
los pondera distinto en cada corrida. No es un error del VLM. Corregirlo
sería cambiar M3, y con ello sus cifras sobre 120 casos: no se hace antes de
la demo, y el criterio del caso, fijado antes de correr, tampoco se cambia.

**Lo que cuesta la imagen:** mediana de 9.6 s por llamada con imagen (lectura
+ M3) frente a 5.7 s sin ella; la lectura sola, 3.9 s. *(La pasada única da
10.7 s frente a 5.6 s, pero compara los tiempos del scorecard con una llamada
nueva: las repeticiones miden las dos condiciones igual.)*

| | métrica | valor | latencia por caso |
|---|---|---|---|
| M3 sin imagen | `acierto_juridico`, brazo 4 (n=120) | 0.675 | 13.65 s |
| M4 con imagen | casos `exacto` (n=3) | 1.0 | mediana 10.9 s |

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
M3 como hecho**. En la corrida de demo, el agente escribió *"Existe un mandato
normativo claro: la notificación indica que el destinatario tiene dos (2)
semanas hábiles"* y anotó `incumplimiento_normativo`; queda en
`cache/agente.json` de la corrida. Y se abstuvo porque la pregunta es una
consulta (*"¿de qué fecha es y en cuántos días se me vence el plazo?"*), no
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
m05; entre la T4 y la L4 de la corrida de demo coinciden las 11.

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

**La corrida de evaluación**, en Colab con GPU (el notebook pide una T4; la
del 1 de noviembre se hizo en una L4) y el secreto `GROQ_API_KEY`:
[`pipeline/M4_pipeline.ipynb`](https://colab.research.google.com/github/TomasPosada0626/Amparo/blob/demo-final/m4/pipeline/M4_pipeline.ipynb)
→ **Entorno → Reiniciar y ejecutar todo** (unos 30 min). Clona el tag
`demo-final` y escribe todo en `corridas/<id>/`: manifiesto, scorecard, trazas,
los dos deltas y el plan B de la demo. Al final descarga un `.zip` con esa
carpeta.

**La demo**:
[`pipeline/M4_demo.ipynb`](https://colab.research.google.com/github/TomasPosada0626/Amparo/blob/demo-final/m4/pipeline/M4_demo.ipynb),
mismas condiciones; deja un enlace público mientras la sesión esté abierta.

Los dos notebooks clonan **el mismo tag, `demo-final`**: lo que ve el público es
lo que se evaluó, y el manifiesto de la corrida lo prueba con su SHA. `m4-demo`
es el tag de la corrida del 1 de noviembre. Entre los dos, en código, solo
cambia `formatear()` en `multimodal.py` (el «Por qué» al abstenerse), que no
usan el scorecard ni los deltas:
`git diff m4-demo demo-final -- src m4/harness/*.py m4/pipeline/*.py`.

**Sin GPU**: `python -m pytest m4/tests` (187 pruebas).

## Revisión docente (PR #15 y #16)

Las dos se fusionaron con su autoría. Qué se hizo con cada punto:

| punto | qué se hizo | estado |
|---|---|---|
| **H1** · el delta no medía latencia; los 30.8 s eran de m02 | atribución corregida; las trazas registran `segundos_ver` aparte; el delta mide la latencia de las dos condiciones (PR #16 y `delta_repetido`) | hecho · corrida de demo: mediana 10.9 s por caso sin arranque en frío; con imagen 9.6 s frente a 5.7 s sin ella |
| **H2** · la lectura del VLM entra como un hecho | bloque «Leído del documento · no verificado» con el aviso de plazo (PR #16); el relato de M3 no se toca | hecho · y el plazo inventado de m10 sí entra a M3 como hecho: ver el peor caso |
| **H3** · la corrida oficial es poco trazable | el notebook clona un tag fijo y escribe `corrida_m4.json` desde la propia corrida; para la del 25, manifiesto reconstruido y rotulado | hecho · `corridas/20261101T194319Z_demo/`, commit `21158cb`, L4, con el notebook ejecutado |
| **H4** · el aporte en m06 varía entre corridas | `delta_repetido`: 3 repeticiones con la caché vacía antes de cada llamada | hecho · 7/9 con imagen frente a 6/9 sin ella; en m06, 1/3 y 1/3: no se sostiene que la imagen mejore la decisión |
| **P1** · una sola llamada, con el fundamento a la vista | `multimodal.py` con `Amparo`, la salida en tres bloques y la interfaz `M4_demo.ipynb` | hecho |
| **P2** · la confianza como característica | m10 muestra el aviso y la abstención; es el caso de seguridad del guion. El «Por qué» ya no muestra una regla cuando Amparo se abstiene | hecho |
| **P3** · tres cifras sobre una versión fija | las tres cifras de arriba; un solo tag, `demo-final`, para la evaluación y la interfaz; plan B grabado de m01, m06 y m10 | hecho · falta la corrida desde `demo-final`, que da el manifiesto con el SHA de la demo y el plan B con el «Por qué» corregido |

**Equipo:** Santiago (pipeline y `ver()`) · Lucas (documentos, eval set y
corrida del harness) · Nico (harness y tabla de delta) · Tomás y Martín (enchufe
del M3 real).
