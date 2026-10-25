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

Y el motor puede **callarse**. Ante un hecho dudoso no activa causal de
improcedencia —el error caro en un triaje no es sugerir una vía de más, es
cerrarle la puerta a quien sí tenía mecanismo—, pero eso no es lo mismo que
responder cuando **no hay caso**: una consulta de inversión, una pregunta de
examen o un pronóstico sobre lo que hará una EPS no son triajes con un dato
incierto. Así que al extractor se le hace una pregunta más, y es de hecho:
¿hay una situación propia del solicitante, con accionado y con una orden que
pedir? Si no la hay, el sistema emite la abstención del formato en vez de
proponer una vía. La pregunta está definida **una vez**
(`schema.PREGUNTA_TRIABLE`) y la usan los tres brazos que deciden con el
motor: dos copias divergirían y dos brazos se abstendrían con criterios
distintos sin que nada lo dijera.

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

## Los módulos

| | qué hace | entorno |
|---|---|---|
| **M1** `notebooks/M1_finetuning.ipynb` | Fine-tuning LoRA de Qwen2.5-7B-Instruct contra un baseline sin ajustar, con intervalos de confianza bootstrap | GPU (A100) |
| **M2** `notebooks/M2_harness.ipynb` | Harness de evaluación en tres dimensiones, con LLM-as-a-judge y **cinco sondas** sobre el juez: posición, longitud, auto-preferencia, inyección de prompt y **validez** | API |
| **M3** `notebooks/M3_rag.ipynb` | Cuatro arquitecturas comparadas sobre los mismos casos: solo fine-tuned, RAG ingenuo, RAG avanzado y agente con motor de reglas | API |
| **M4** `m4/pipeline/M4_pipeline.ipynb` | Componente visual, patrón *input*: Qwen2-VL-2B lee la foto de un documento jurídico, extrae hechos y los entrega al brazo 4 de M3. Entrega en [`m4/README.md`](m4/README.md) | GPU (T4) + API |

Corren **en ese orden**. M2 necesita las predicciones de M1 y M3 necesita los
artefactos de M2; `src/arranque.py` lo declara y lo comprueba antes de gastar
GPU o llamadas.

La quinta sonda de M2 es la que faltaba, y no mide lo mismo que las otras
cuatro. Esas cuatro miden si al juez se le puede **engañar**; ninguna
comprueba lo primero, que el instrumento **mida algo**. Un juez que puntuara
al azar las pasaría todas —no tiene sesgo de posición, no premia la longitud,
no prefiere a su linaje y no obedece inyecciones— y sus notas no valdrían
nada. La sonda de validez le pone delante el gold del caso y el mismo gold con
un defecto aislado —mecanismo cambiado, norma inventada, razonamiento vacío— y
mira si la nota baja.

Hay además una comprobación del juez **contra su propia escala**. La rúbrica
define `nota >= 3` como «mecanismo correcto», y eso se verifica contra el gold
sin preguntarle a nadie: una nota de 4 sobre una respuesta con el mecanismo
equivocado no es severidad ni generosidad, es incumplir la escala que se le
dio. Es distinto de la kappa contra las métricas de dominio, que **no tiene
por qué ser alta**: un juez que coincidiera con `acierto_juridico` sería una
copia ruidosa de esa métrica y no aportaría el razonamiento, que es
exactamente lo que la accuracy no ve.

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
python -I src/autoprueba_integracion.py   # toda la fontanería, sin GPU ni API
python -I data/auditar_notebooks.py       # orden de celdas, numeración y enganche entre notebooks
python -I data/auditar_proyecto.py        # coherencia entre capas: corpus, gold, motor, reporte
python -I data/autoprueba_reporte.py      # que la prosa del reporte siga a sus artefactos
python -I data/verificar_entrega.py       # que los artefactos sean del mismo experimento
python -I data/ampliar_eval_set.py        # que cada etiqueta la respalde el motor de reglas
```

El número de pruebas no se escribe aquí por la misma razón que no se escriben
las cifras: un conteo clavado queda obsoleto en el siguiente commit y nadie se
entera. La salida de cada script lo dice.

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

- **El juez automático concuerda con el criterio humano de forma moderada, y
  eso limita lo que sus notas pueden sostener.** Un abogado externo puntuó 25
  casos con la **misma** rúbrica que se le dio al modelo y sin ver la nota del
  juez: κ **0.5763** en la decisión de aprobar, Spearman **0.8339**, acuerdo
  exacto **68%** y a un punto **92%**. Leído honestamente: el juez **ordena**
  los casos como un jurista, pero el **umbral** de aprobar no está calibrado
  con él. Las notas sirven para comparar brazos entre sí, que es para lo que se
  usan; no para afirmar que una salida concreta es jurídicamente aceptable.
  `REPORTE.md` §7.1 lo deriva del artefacto, no está escrito a mano.
- **El gold es reproducible, no verificado.** Una segunda persona que no lo
  escribió anotó a ciegas una muestra estratificada de 30 casos: κ **0.803** en
  mecanismo y **0.7945** en procedencia —**0.9021** y **0.8618** releyendo las
  3 filas que incumplían una regla de codificación del formulario—.
  Reproducible **no es correcto**: dos personas pueden coincidir y
  equivocarse. Y la κ del estrato `juicio` sale **indefinida** y seguirá
  saliendo así —el eval set tiene 3 casos de `juicio` entre 109 y la cuota ya
  los toma todos—, así que el estrato donde el gold es más discutible es el
  único sin cifra de fiabilidad. `REPORTE.md` §2.1.
- **Las dos muestras están sesgadas a propósito, y por eso ninguna de las dos
  κ es la del conjunto.** En la del juez se toman hasta cinco casos de *cada*
  nota, porque una proporcional serían 25 casos con casi toda la varianza en
  un punto; en la del gold se sobrerrepresentan los estratos difíciles, porque
  la pregunta no es la fiabilidad media sino **dónde** está el desacuerdo. Las
  dos estiman el acuerdo **condicionado a sus estratos** y los dos artefactos
  lo declaran donde va la cifra.
- **La revisión del abogado valida las etiquetas, no al juez.** Son dos
  validaciones distintas y la segunda no se cubre con la primera. La nota
  global de `data/revision_abogado_v3.json` es sobre el **gold**; leerla como
  una validación del juez sería confundir los datos con el instrumento que los
  puntúa.
- **La abstención del motor se mide con n=6.** El criterio de triabilidad se
  escribió sabiendo que esos seis casos existen, y seis casos no validan
  ningún criterio de abstención. Lo que sí se puede falsar es el otro lado, y
  ahí la muestra es diecisiete veces mayor: `abstencion_indebida` sobre los
  casos **con** respuesta correcta sube si el criterio se abstiene de más. Es
  el número que hay que mirar, no el acierto sobre los seis.
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

---

## Reproducibilidad: la semilla no basta

Sembrar `random`, `numpy` y `torch` fija de dónde salen los números
aleatorios. No fija el **orden** en que la GPU los suma: cuBLAS elige su
reducción según el workspace libre y cuDNN autotunea la convolución en la
primera llamada, así que la misma operación en bf16 puede acumular en dos
órdenes distintos —y sumar en otro orden, en coma flotante, da otro número.
Sobre 7·10⁹ parámetros eso llega a cambiar un token generado, que es un campo
distinto en el scorecard.

`corridas.sembrar()` añade los interruptores de kernel y **devuelve lo que
consiguió**, con sus límites, para que `corrida.json` lo registre.
`CUBLAS_WORKSPACE_CONFIG` se pone al **importar** el módulo, porque cuBLAS la
lee cuando crea su handle y ponerla después no da error: no hace nada.

Dos cosas quedan declaradas y no resueltas.
`torch.use_deterministic_algorithms` va con `warn_only=True` a propósito: con
`warn_only=False`, una sola operación sin kernel determinista levanta
`RuntimeError` y se lleva por delante cincuenta minutos de A100. Eso es
**menos** determinismo, y el artefacto lo dice en vez de prometerlo. Y los
flags fijan el algoritmo, **no el hardware**: dos corridas en GPUs distintas
pueden diferir igual, por lo que la celda de estabilidad compara también el
modelo de GPU y separa las tres causas posibles —hardware distinto, corrida
previa sin flags, y no-determinismo residual real— en vez de ofrecer una sola
hipótesis.
