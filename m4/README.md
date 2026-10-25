# M4 · Amparo ya ve

> Entrega de M4. La versión larga, con cada decisión y su evidencia, está en la
> wiki: [M4 · Componente visual — decisiones](https://github.com/TomasPosada0626/Amparo/wiki/M4-%E2%80%90-Componente-visual-%E2%80%94-decisiones).

## La pregunta que necesita ojos

> *"Me llegó esta respuesta de mi EPS. Tengo 68 años y el ortopedista me ordenó
> esa cirugía. ¿Qué mecanismo constitucional me corresponde?"*

Sin la imagen no se puede triar: la pregunta no dice qué negó la EPS ni por
qué. El dato está en el papel que la persona tiene en la mano.

## Patrón y modelo

**Patrón input, con Qwen2-VL-2B-Instruct.** El VLM lee la foto del documento y
devuelve hechos en JSON (`tipo_documento`, `entidad`, `fecha`, `plazo_dias`,
`pretension_visible`). Esos hechos se suman al relato y entran a M3. **El VLM
extrae hechos; no decide derecho.** Es el mismo principio de Amparo desde M1.

Qué se habría perdido con los otros dos patrones:

- **tool (CLIP o un clasificador):** diría el **tipo** de documento, pero el
  motor de reglas necesita los **hechos**: que se **niega** un procedimiento
  **ordenado por el médico** a un **sujeto de especial protección**.
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

## Delta: la misma pregunta con imagen y sin ella

Lo único que cambia es el componente visual; M3 es el mismo.

| caso | esperado | **con imagen** | sin imagen | efecto |
|---|---|---|---|---|
| m01 · EPS | tutela | **tutela** | se abstiene | aporta |
| m04 · alcaldía | acción de cumplimiento | **cumplimiento** | cumplimiento | **no aporta** |
| m06 · corporación ambiental | acción popular | **acción popular** | tutela | aporta |
| **acierto de mecanismo** | | **3/3** | 1/3 | |

| | métrica | valor | latencia por caso |
|---|---|---|---|
| M3 sin imagen | `acierto_juridico`, brazo 4 (n=120) | 0.675 | 13.65 s |
| M4: lo que leyó el VLM | `campos` (n=5) | 0.553 | 4.67 s de `ver()` |
| M4: adversarial | `valvula` (n=1) | 1.0 | 5.27 s |

La primera tabla es la que mide el componente; la segunda compara conjuntos de
casos distintos y no dice, por sí sola, si la imagen ayuda. Con 3 casos
`exacto` no se afirma significancia.

**Procedencia.** Lo que leyó el VLM sale de la corrida del 2026-10-25 en una
RTX 5060 (no una T4). El "con imagen / sin imagen" es el M3 real aplicado a esas
lecturas grabadas: `ver()` genera con `do_sample=False` y no recibe la
pregunta, así que su lectura es la misma que daría hoy. **La corrida oficial
de punta a punta es la de [`pipeline/M4_pipeline.ipynb`](pipeline/M4_pipeline.ipynb)
en Colab, y es la única que califica `juez_vlm`.** Si sus cifras difieren de
estas, mandan las suyas.

## El peor caso

**m10, el adversarial, pasa el criterio y aun así inventa.** `fecha` y
`plazo_dias` vienen vacíos, así que `valvula` = 1.0. Pero el VLM escribió en
otro campo *"Usted cuenta con un plazo de **dos semanas** hábiles"*, y debajo
de la mancha no hay número. El criterio solo mira los campos que nombra y no lo
ve. No se cambió, porque se fijó antes de correr. M3 se abstuvo y el plazo
inventado no llegó a una decisión, pero una persona que lea esa lectura se lo
cree, y en derecho un plazo vencido no se recupera.

También: en **m04** el VLM leyó el documento al revés ("publicará los
contratos" cuando dice que **no**) y M3 acertó solo porque la pregunta traía
los hechos. **`entidad` sale vacía en los 6 documentos** y `plazo_dias` en los
2 que lo traen; puede ser que la válvula haga abstenerse de más al modelo de
2B, y eso no está comprobado.

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

Colab con GPU T4 y el secreto `GROQ_API_KEY`: abrir
`pipeline/M4_pipeline.ipynb` y **Entorno → Reiniciar y ejecutar todo**. Clona
`main` y deja `scorecard_m4.csv`, `trazas_m4.json`, `delta_m4.json` y
`delta_imagen_m4.json`. Sin GPU: `python -m pytest m4/tests` (166 pruebas).

**Equipo:** Santiago (pipeline y `ver()`) · Lucas (documentos, eval set y
corrida del harness) · Nico (harness y tabla de delta) · Tomás y Martín (enchufe
del M3 real).
