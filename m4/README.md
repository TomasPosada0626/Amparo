# M4 · Amparo ya ve

> Entrega de M4. La versión larga, con cada decisión y su evidencia, está en la
> wiki: [M4 · Componente visual — decisiones](https://github.com/TomasPosada0626/Amparo/wiki/M4-%E2%80%90-Componente-visual-%E2%80%94-decisiones).
> Lo que se cambió tras la revisión docente está en [la última sección](#revisión-docente-pr-15-y-16).

## La pregunta que necesita ojos

> *"Somos cuatro veredas que tomamos agua de esa quebrada y la curtiembre sigue
> vertiendo. Esta es la respuesta que nos dio la corporación ambiental. ¿Qué
> mecanismo constitucional nos corresponde?"*

Sin la imagen, Amparo puede ver solo una curtiembre contaminando y un perjuicio
que corre, y responder **tutela contra la curtiembre**. Con la imagen lee que la
corporación **archivó la queja**, reconoce un interés colectivo y responde
**acción popular**, que es lo correcto. El dato que cambia la respuesta está en
el papel, no en lo que la persona escribe. **Cuántas veces cambia** es justo lo
que hubo que medir con repeticiones: ver el delta.

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
  es lo que de verdad decidió.
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
| **Tiempo de respuesta con imagen** | **mediana 8.7 s por caso** (VLM + M3, 11 casos, T4); 8.4 s sin el caso que cargó los modelos | `scorecard_m4.csv` de la corrida oficial |

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

Contando esas tres corridas, la imagen aportó en m06 en **2 de 3**. Para poder
afirmarlo en la demo, la corrida de demo repite cada caso **3 veces con imagen y
3 sin ella, con la caché de M3 vacía** (`delta_imagen_repetido_m4.json`). Sus
tasas van aquí cuando esté hecha.

| | métrica | valor | latencia por caso |
|---|---|---|---|
| M3 sin imagen | `acierto_juridico`, brazo 4 (n=120) | 0.675 | 13.65 s |
| M4 con imagen | casos `exacto` (n=3) | 1.0 | mediana 8.7 s |

Esta segunda tabla compara conjuntos de casos distintos (3 contra 120); se
publica porque el plan la pide, pero el delta que mide el componente es el de
arriba.

## El peor caso

**m10, el adversarial, pasa el criterio y aun así inventa.** `fecha` y
`plazo_dias` vienen vacíos, así que `valvula` = 1.0. Pero el VLM escribió en
otro campo *"Usted cuenta con un plazo de **dos semanas** hábiles"*, y debajo
de la mancha no hay número. Lo hizo en las dos GPU en que se corrió. El
criterio solo mira los campos que nombra y no lo ve; no se cambió, porque se
fijó antes de correr. M3 se abstuvo y el plazo inventado no llegó a una
decisión, pero una persona que lea esa lectura se lo cree, y en derecho un plazo
vencido no se recupera. **Por eso ahora la respuesta lo marca**: el bloque
«Leído del documento · no verificado» trae el aviso *"plazo en texto libre sin
plazo_dias: verificar en la imagen"*. Es el caso de seguridad de la demo.

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
m05.

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

**La corrida de evaluación**, en Colab con GPU T4 y el secreto `GROQ_API_KEY`:
[`pipeline/M4_pipeline.ipynb`](https://colab.research.google.com/github/TomasPosada0626/Amparo/blob/m4-demo/m4/pipeline/M4_pipeline.ipynb)
→ **Entorno → Reiniciar y ejecutar todo** (unos 30 min). Clona el tag
`m4-demo` y escribe todo en `corridas/<id>/`: manifiesto, scorecard, trazas,
los dos deltas y el plan B de la demo. Al final descarga un `.zip` con esa
carpeta.

**La demo**:
[`pipeline/M4_demo.ipynb`](https://colab.research.google.com/github/TomasPosada0626/Amparo/blob/m4-demo/m4/pipeline/M4_demo.ipynb),
mismas condiciones; deja un enlace público mientras la sesión esté abierta.

**Sin GPU**: `python -m pytest m4/tests` (186 pruebas).

## Revisión docente (PR #15 y #16)

Las dos se fusionaron con su autoría. Qué se hizo con cada punto:

| punto | qué se hizo | estado |
|---|---|---|
| **H1** · el delta no medía latencia; los 30.8 s eran de m02 | atribución corregida; latencia sin arranque publicada; las trazas registran `segundos_ver` aparte; el delta mide la latencia de las dos condiciones (PR #16 y `delta_repetido`) | hecho · cifras de la corrida de demo, pendientes |
| **H2** · la lectura del VLM entra como un hecho | bloque «Leído del documento · no verificado» con el aviso de plazo (PR #16); el relato de M3 no se toca | hecho |
| **H3** · la corrida oficial es poco trazable | el notebook clona el tag `m4-demo` y escribe `corrida_m4.json` desde la propia corrida; para la del 25, manifiesto reconstruido y rotulado | hecho · manifiesto de la corrida de demo, pendiente |
| **H4** · el aporte en m06 varía entre corridas | `delta_repetido`: 3 repeticiones con la caché vacía antes de cada llamada | código hecho · tasas, pendientes de la corrida |
| **P1** · una sola llamada, con el fundamento a la vista | `multimodal.py` con `Amparo`, la salida en tres bloques y la interfaz `M4_demo.ipynb` | hecho |
| **P2** · la confianza como característica | m10 muestra el aviso y la abstención; es el caso de seguridad del guion | hecho |
| **P3** · tres cifras sobre una versión fija | las tres cifras de arriba; tag `m4-demo`; plan B grabado de m01, m06 y m10 | hecho · plan B, pendiente de la corrida |

**Equipo:** Santiago (pipeline y `ver()`) · Lucas (documentos, eval set y
corrida del harness) · Nico (harness y tabla de delta) · Tomás y Martín (enchufe
del M3 real).
