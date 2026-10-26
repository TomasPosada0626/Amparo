# M4 · Amparo ya ve

> Entrega de M4. La versión larga, con cada decisión y su evidencia, está en la
> wiki: [M4 · Componente visual — decisiones](https://github.com/TomasPosada0626/Amparo/wiki/M4-%E2%80%90-Componente-visual-%E2%80%94-decisiones).

## La pregunta que necesita ojos

> *"Somos cuatro veredas que tomamos agua de esa quebrada y la curtiembre sigue
> vertiendo. Esta es la respuesta que nos dio la corporación ambiental. ¿Qué
> mecanismo constitucional nos corresponde?"*

Sin la imagen, Amparo ve una curtiembre contaminando y un perjuicio que corre,
y responde **tutela contra la curtiembre**. Con la imagen lee que la
corporación **archivó la queja**, reconoce un interés colectivo y responde
**acción popular**, que es lo correcto. El dato que cambia la respuesta está en
el papel, no en lo que la persona escribe.

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

## Dónde se enchufa

```python
crudo, js = ver(imagen)                                   # el VLM lee el documento
relato = pregunta + "\n\nDATOS DEL DOCUMENTO ADJUNTO:\n" + json.dumps(js)
return responder_m3(relato)                               # M3 real, sin reescribir
```

`responder_m3` es el brazo **4 · agente + reglas** de M3
([`pipeline/enchufe_m3.py`](pipeline/enchufe_m3.py)): busca en el corpus de
normas, extrae hechos y el motor del art. 6 del Decreto 2591 decide. Se eligió
porque sigue el mismo patrón que M4 y cabe en una T4 junto al VLM (razona por
la API de Groq). No es el mejor brazo de M3 en el agregado —ese es el 1—, y
toda comparación es contra la fila del brazo 4. `src/` no se modifica: se
importa.

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

## Resultados — corrida oficial en Colab (T4)

| criterio | n | nota | lo que dice |
|---|---|---|---|
| `exacto` | 3 | **1.0** | M3 decide el mecanismo correcto en los 3 (tutela, cumplimiento, popular) |
| `juez_vlm` | 2 | **1.0** | las dos respuestas se sostienen en la imagen, según el propio VLM |
| `campos` | 5 | **0.553** | m02 0.50 · m03 0.60 · m05 0.75 · m07 0.67 · m09 0.25 |
| `valvula` | 1 | **1.0** | pero inventa en otro campo: ver el peor caso |

**Latencia: 10.9 s por caso** (VLM + M3), de 7.1 a 12.2 s; el primero tarda
30.8 s porque carga los modelos.

## Delta: la misma pregunta con imagen y sin ella

Lo único que cambia es el componente visual; M3 es el mismo.

| caso | esperado | con imagen | sin imagen | efecto |
|---|---|---|---|---|
| m01 · EPS | tutela | tutela | tutela | **no aporta** |
| m04 · alcaldía | acción de cumplimiento | cumplimiento | cumplimiento | **no aporta** |
| m06 · corporación ambiental | acción popular | **acción popular** | tutela | **aporta** |
| **acierto de mecanismo** | | **3/3** | 2/3 | |

**La imagen aporta en 1 de 3 casos.** En m01 y m04 la pregunta ya trae los
hechos y M3 acierta sin el documento. Con 3 casos no se afirma significancia.

**Y m01 no es estable.** En una verificación anterior, con las mismas lecturas
del VLM, M3 se abstenía en m01 sin imagen y la imagen sí aportaba. El
extractor de hechos de M3 no es determinista (ya medido en M3), así que con una
sola corrida no se puede afirmar si la imagen aporta en m01. En m06 aportó las
dos veces.

| | métrica | valor | latencia por caso |
|---|---|---|---|
| M3 sin imagen | `acierto_juridico`, brazo 4 (n=120) | 0.675 | 13.65 s |
| M4 con imagen | casos `exacto` (n=3) | 1.0 | 10.9 s |

Esta segunda tabla compara conjuntos de casos distintos (3 contra 120); se
publica porque el plan la pide, pero el delta que mide el componente es el de
arriba.

## El peor caso

**m10, el adversarial, pasa el criterio y aun así inventa.** `fecha` y
`plazo_dias` vienen vacíos, así que `valvula` = 1.0. Pero el VLM escribió en
otro campo *"Usted cuenta con un plazo de **dos semanas** hábiles"*, y debajo
de la mancha no hay número. Lo hizo en las dos corridas. El criterio solo mira
los campos que nombra y no lo ve; no se cambió, porque se fijó antes de correr.
M3 se abstuvo y el plazo inventado no llegó a una decisión, pero una persona
que lea esa lectura se lo cree, y en derecho un plazo vencido no se recupera.

**Por la nota mínima, el peor es m09** (`campos` 0.25): la foto del acueducto
es legible y el VLM solo acierta el tipo; pierde la entidad, la fecha y el
plazo de 5 días.

También: en **m04** el VLM lee el documento al revés (*"La Alcaldía cumplirá
con el deber de publicar los contratos"*, cuando dice que **no**), y M3 acierta
solo porque la pregunta trae los hechos. **`entidad` sale vacía en los 6
documentos**; puede ser que la válvula haga abstenerse de más al modelo de 2B,
y eso no está comprobado. Y **el VLM no lee igual en todas las GPU**: entre la
T4 y una RTX 5060, 9 de 11 lecturas coinciden y cambian m04 y m05.

## Límites y ética

- Los 6 documentos son **sintéticos** y llevan la etiqueta visible
  **"DOCUMENTO SINTÉTICO / GENERADO"**. No hay datos personales, firmas, sellos
  ni logos ([checklist por imagen](eval_set/imagenes/ANONIMIZACION.md)).
- **El VLM describe, no diagnostica.** La conclusión jurídica la pone el motor
  de reglas, con el artículo que la soporta.
- Un VLM pequeño que rellena un plazo o invierte una negativa puede convencer a
  alguien de que sigue a tiempo, o de que la entidad le dio la razón. Por eso su
  lectura no se presenta como un hecho comprobado.
- Nada de esto autoriza el uso con personas reales.

## Reproducir

Abrir en Colab con GPU T4 y el secreto `GROQ_API_KEY`:
[`pipeline/M4_pipeline.ipynb`](https://colab.research.google.com/github/TomasPosada0626/Amparo/blob/main/m4/pipeline/M4_pipeline.ipynb)
→ **Entorno → Reiniciar y ejecutar todo** (unos 20 min). Clona `main` y deja
[`scorecard_m4.csv`](scorecard_m4.csv), [`trazas_m4.json`](trazas_m4.json),
[`delta_m4.json`](delta_m4.json) y [`delta_imagen_m4.json`](delta_imagen_m4.json),
que son los de esta entrega. Sin GPU: `python -m pytest m4/tests` (166 pruebas).

**Equipo:** Santiago (pipeline y `ver()`) · Lucas (documentos, eval set y
corrida del harness) · Nico (harness y tabla de delta) · Tomás y Martín (enchufe
del M3 real).
