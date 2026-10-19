# Amparo · triaje de acciones constitucionales en Colombia

Un sistema que lee el relato de una persona y decide **qué mecanismo
constitucional le corresponde** —tutela, acción popular, acción de
cumplimiento, hábeas corpus o la vía ordinaria— con el fundamento normativo
que sostiene esa decisión.

El trabajo no está en el modelo. Está en **poder creer la cifra**.

---

## Lo que hace distinto a este repositorio

Tres decisiones que vale la pena mirar antes que cualquier resultado.

### 1 · La etiqueta no se afirma: se deriva

El art. 6 del Decreto 2591 de 1991 es un **árbol de decisión escrito en la
ley**. Así que no se le pide a nadie —ni a una persona ni a un modelo— que
adivine el mecanismo correcto: se codifican los **hechos** del caso y
`src/reglas.py` deriva el mecanismo recorriendo el árbol.

Cada caso del set de evaluación declara además qué mecanismo se esperaba. Si
el motor no coincide, **el caso se rechaza y no entra**. Unos hechos mal
codificados producirían una etiqueta plausible y equivocada sin que nada lo
delatara, y esa comprobación es lo único que lo impide.

El motor también rechaza codificaciones incoherentes: no se puede afirmar
`perjuicio_irremediable=False` si los cuatro elementos del test concurren.

### 2 · Las etiquetas vienen con su fiabilidad

No todas valen lo mismo, y el set lo dice caso por caso en una escalera de
cuatro niveles (`nivel_fiabilidad`). `motor_de_reglas` significa
**CONSISTENTE** con el árbol del art. 6, no **INDEPENDIENTE**: los hechos los
codificó el mismo equipo que puso la etiqueta. Cada scorecard reporta las
métricas **partidas por ese estrato**, para que no se lea como independiente
lo que no lo es.

### 3 · Lo que no se puede concluir está escrito con su cifra

`REPORTE.md` lo genera `data/reporte.py` leyendo los artefactos publicados, y
su apéndice lista **cada cifra con el archivo del que salió**. La tesis
central —«este brazo gana a los demás»— no está escrita a mano: la dicta
`metricas.ic_se_solapan()` comparando intervalos, así que **se retracta sola**
si una corrida los mueve.

Eso ya pasó: una corrida hizo que dos brazos dejaran de separarse y el reporte
lo dijo, en lugar de seguir afirmando una ventaja que los datos ya no
sostenían.

---

## Los tres módulos

| | qué hace | entorno |
|---|---|---|
| **M1** `notebooks/M1_finetuning.ipynb` | Fine-tuning LoRA de Qwen2.5-7B-Instruct contra un baseline sin ajustar, con intervalos de confianza bootstrap | GPU (A100) |
| **M2** `notebooks/M2_harness.ipynb` | Harness de evaluación en tres dimensiones, con LLM-as-a-judge y **cuatro sondas de sesgo** del juez: posición, longitud, auto-preferencia e inyección de prompt | API |
| **M3** `notebooks/M3_rag.ipynb` | Cuatro arquitecturas comparadas sobre los mismos casos: solo fine-tuned, RAG ingenuo, RAG avanzado y agente con motor de reglas | API |

Corren **en ese orden**. M2 necesita las predicciones de M1 y M3 necesita los
artefactos de M2; `src/arranque.py` lo declara y lo comprueba antes de gastar
GPU o llamadas.

---

## Cómo leer los resultados

**`REPORTE.md`** es la entrada. No está escrito a mano: lo genera
`data/reporte.py` a partir de los artefactos de `results/`, y si un artefacto
falta lo dice en el lugar donde iría la cifra en vez de callarlo o escribir un
cero.

Las cifras no se repiten en este README a propósito. Un README con números
clavados queda obsoleto en la siguiente corrida y nadie se entera —que es
justo el defecto que el resto del proyecto está construido para evitar.

---

## Reproducir

```bash
pip install -r requirements.txt
python -I reproducir.py
```

`reproducir.py` separa **lo que se reproduce sin GPU ni API** —el motor de
reglas, las métricas, los intervalos, la validación de los datos— de lo que
necesita una corrida completa, y lo dice en la salida en vez de dejarlo
implícito.

### Las comprobaciones, por separado

```bash
python -I src/autoprueba_integracion.py   # 68 pruebas: toda la fontanería, sin GPU ni API
python -I data/auditar_notebooks.py       # orden de celdas, numeración y enganche entre notebooks
python -I data/autoprueba_reporte.py      # que la prosa del reporte siga a sus artefactos
python -I data/verificar_entrega.py       # que los artefactos sean del mismo experimento
python -I data/ampliar_eval_set.py        # que cada etiqueta la respalde el motor de reglas
```

`auditar_notebooks.py` comprueba con `ast` que **ninguna celda use un nombre
que ninguna anterior defina**. Es la única comprobación que detecta de verdad
un notebook en mal orden: una celda que necesita algo definido doce celdas más
abajo funciona en la sesión donde se escribió —el kernel ya tenía la
variable— y falla en la primera ejecución limpia, que es la del lector.

---

## Procedencia

**El corpus normativo** cita únicamente normas declaradas en
`data/normas.json` (20 artículos de la Constitución, 22 del Decreto 2591 de
1991 y 12 leyes). Es contra ese conjunto que se mide la alucinación
normativa, así que una norma inventada en el gold envenenaría la métrica
desde los datos: `data/ampliar_eval_set.py` rechaza cualquier cita que no
esté ahí.

**El responsable del corpus** es Leonardo Galeano, abogado.

**El set de evaluación** es `data/eval_set_v3.json`, y cada versión contiene
a la anterior **sin tocar un byte** —lo fija una prueba—. Por eso cada
scorecard publica un puente `subconjunto_v1` que permite comparar contra las
corridas anteriores sobre los casos comunes. Ampliar en sitio habría
destruido esa comparabilidad en silencio.

**La revisión humana del gold** está en `data/revision_abogado_v3.json`: los
40 casos nuevos revisados por el abogado responsable, con el resultado por
caso y la declaración explícita de qué **no** se le pidió revisar.

---

## Los relatos son sintéticos

Los casos del set de evaluación son **relatos sintéticos**, no expedientes.
Se redactaron para la prueba y el proyecto lo declara en el `meta` de cada
archivo de datos.

**Nada de lo medido aquí autoriza a usar el sistema para orientar a una
persona real sobre su caso.**

---

## Lo que NO está establecido

Esta sección existe porque es la más útil del repositorio.

- **El juez automático no está validado contra criterio humano
  independiente.** El instrumental está completo y exige declarar quién
  anotó, pero el gold, la rúbrica y el juez los escribió el mismo equipo: si
  ese equipo puntúa, lo que mide es si una aplicación de su propia rúbrica
  coincide con otra aplicación de su propia rúbrica. Eso es **consistencia**,
  no acuerdo entre anotadores. Solo lo cierra una persona externa, y el
  artefacto lo dice con esas palabras.
- **La revisión del abogado valida las etiquetas, no al juez.** Son dos
  validaciones distintas y la segunda no se cubre con la primera.
- **El acuerdo entre los dos jueces** se mide entre modelos de familias
  distintas a propósito, y su cifra dice si la nota es una propiedad de la
  respuesta o del juez. Cuando es baja, la nota sirve para **ordenar
  sistemas** y no para publicarse como nota absoluta.
- **Varias clases tienen soporte de un dígito.** Un F1 de 0.000 con soporte 1
  no es un hallazgo sobre el sistema: es la ausencia de muestra, y
  `clases_con_soporte_minimo` las nombra en cada scorecard.

---

## Estructura

```
src/          motor de reglas, métricas, harness, juez, agente, autopruebas
data/          sets de datos, corpus normativo y los scripts que los auditan
notebooks/     M1, M2 y M3
results/       artefactos publicados de la corrida vigente, con su sello
REPORTE.md     el reporte, generado a partir de results/
reproducir.py  la entrada única
```

Cada corrida queda sellada con una **huella del código** (`src/*.py`) y una
**versión de los datos**, y `data/verificar_entrega.py` comprueba que todos
los artefactos de la entrega vengan del mismo experimento. No es hipotético:
una corrida comparó contra la anterior con los mismos datos, salió distinta, y
la celda de estabilidad avisó de no-determinismo del hardware cuando la causa
era que se había cambiado el código en medio. Una advertencia falsa es peor
que no avisar, porque manda a buscar donde no hay nada.
