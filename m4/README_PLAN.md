# M4 · Plan de trabajo — "Su sistema ya ve"

> Este archivo es el **plan interno del equipo**, no la entrega. Si lees esto,
> sabes hacia dónde vamos y qué te toca. La entrega final lleva su propio
> `m4/README.md` de **una página** (eso lo escribe Lucas/Nico, ver T8).
>
> Rama de trabajo: **`m4`**. Todo lo de M4 vive en la carpeta `m4/`.

---

## 0 · En una frase

Al sistema de triaje constitucional de M3 (Amparo) le enchufamos **un
componente visual (patrón _input_, un VLM)**: el usuario adjunta la **foto de
un documento jurídico**, el VLM lee la imagen y extrae hechos en JSON, y esos
hechos entran al sistema de M3 que ya teníamos — **sin reescribir M3**. Luego
lo medimos con el mismo harness de M2 y llenamos una tabla que dice si mejoró,
si no empeoró lo viejo y cuánto cuesta.

**Vale 10% · cierra domingo 25 OCT 23:59 · entrega tardía −2%/día (máx 7 días).**
Es una pieza del proyecto final (demo day S16 · 5 NOV).

---

## 1 · Contexto que NO puedes saltarte

### 1.1 · Qué es Amparo (nuestro sistema de M3)

Amparo lee el relato de una persona y decide **qué mecanismo constitucional le
corresponde**: tutela, acción popular, acción de cumplimiento, hábeas corpus o
vía ordinaria. La decisión de diseño que lo define todo:

- **El LLM NO decide el mecanismo.** El LLM solo **extrae hechos** del relato
  (booleanos: ¿hay privación de libertad? ¿derecho colectivo? ¿otro medio
  judicial?...).
- El **motor de reglas** (`src/reglas.py`) recorre las causales del art. 6 del
  Decreto 2591/1991 **en orden** y **deriva** el mecanismo de forma
  determinista. El fundamento normativo lo pone la regla, no la memoria del
  modelo → alucinación normativa cero por construcción.

Esto importa para M4 porque nuestro componente visual encaja **perfecto** con
esa arquitectura: **el VLM extrae hechos del documento, no decide derecho.**
Es el mismo patrón "extraer → reglas deciden", ahora con una imagen en la
entrada en vez de solo texto.

### 1.2 · Los tres módulos previos

- **M1** — fine-tuning LoRA de Qwen2.5-7B-Instruct (el generador).
- **M2** — harness de evaluación en 3 dimensiones (clásica, LLM-juez, dominio)
  + sondas de sesgo del juez. **La función `calificar`/`harness` de M2 es la
  que reusamos en M4 sin cambiarla**, solo le agregamos criterios que miran.
- **M3** — 4 arquitecturas comparadas. La que enchufamos es el sistema M3
  (RAG o agente). Expone la firma `sistema(relato: str) -> str`.

### 1.3 · Los relatos son sintéticos

Todos los casos de Amparo son **relatos sintéticos**, no expedientes reales.
Coherente con eso, **nuestras imágenes de M4 también serán documentos
sintéticos** (ver T3). Nada autoriza a usar esto con una persona real.

---

## 2 · El patrón elegido y por qué (patrón INPUT · VLM)

**Decisión tomada:** patrón **input** con **Qwen2-VL-2B-Instruct**.

- **La pregunta del usuario que necesita ojos:** _"Adjunto este documento que
  me llegó / que conseguí, ¿qué mecanismo constitucional me corresponde?"_
  (ej.: una notificación, un oficio, una respuesta a un derecho de petición).
- **Por qué input y no tool/output:** la pregunta necesita **leer el contenido**
  del documento, no clasificarlo (tool) ni dibujarlo (output). Es el patrón que
  responde con menos piezas nuevas y encaja en el flujo "extraer hechos →
  reglas deciden" de Amparo.
- **Por qué Qwen2-VL-2B:** es el VLM visto en S11/S13, corre en Colab T4, y es
  de la misma familia Qwen que nuestro generador de M1 (coherencia).
- **Alternativas descartadas:**
  - _tool / CLIP_: clasificar el **tipo** de documento no da los **hechos**
    que el motor de reglas necesita.
  - _output / difusión_: generar imágenes en un dominio jurídico es inútil y
    **éticamente riesgoso** — el curso es explícito: "documentos, firmas o
    sellos: nunca" generados como reales, y "el VLM describe, no diagnostica".

### 2.1 · Debilidad conocida del VLM (tenerla presente)

Según S11, un VLM pequeño **falla al leer números pequeños, fechas y al
contar**. Justo lo que un documento jurídico tiene (fechas, plazos). Por eso:

1. El **caso adversarial** del eval set debe explotar esto (un documento donde
   la fecha no se aprecia bien).
2. La **válvula de escape** es obligatoria: si el dato no se ve, el VLM debe
   responder _"No se aprecia en la imagen."_ en vez de inventarlo.

---

## 3 · La arquitectura del enchufe (cómo se conecta, verificado en el código)

El sistema de M3 expone `sistema(relato: str) -> str` (en `src/sistema.py`
`SistemaRAG.__call__` y en `src/agente.py` `Agente.__call__`). El patrón input
mete lo que ve el VLM **como texto, antes del RAG**:

```python
def sistema_multimodal(pregunta, imagen):
    crudo, js = ver(imagen)                       # Qwen2-VL extrae del documento
    contexto = json.dumps(js, ensure_ascii=False) if js else crudo
    relato = pregunta + "\n\nDATOS DEL DOCUMENTO ADJUNTO:\n" + contexto
    return responder_m3(relato)                   # ← M3 INTACTO, no se reescribe
```

Las **tres reglas** del patrón input (PDF S13):

1. **Válvula de escape** en la instrucción del VLM — si no se aprecia, lo dice.
2. **Salida JSON validada** — se pide JSON con campos fijos y se parsea con
   cuidado; si el parseo falla, **el caso cuenta como fallo** (no se disimula).
3. **"Describir antes de preguntar"** (opcional) — dos llamadas (describe →
   responde) reducen alucinación pero **cuestan el doble**; si se usa, hay que
   medir si vale la latencia extra.

### 3.1 · Qué extrae el VLM (los campos JSON del dominio)

`INSTRUCCION_DOMINIO` le pide al VLM devolver SOLO este JSON:

```json
{
  "tipo_documento": "notificacion | oficio | respuesta_peticion | sentencia | otro",
  "entidad": "quién emite el documento, o null",
  "fecha": "fecha visible en el documento, o null",
  "plazo_dias": "número de días de plazo mencionado, o null",
  "pretension_visible": "qué se le exige/responde al ciudadano, una frase, o null"
}
```

Cualquier campo que no se aprecie va `null` (es la válvula aplicada al JSON).
Estos campos son **hechos legibles del documento**, nunca una conclusión
jurídica — la conclusión la saca el motor de reglas de M3.

### 3.2 · El "sustituto" (andamio temporal) y el enchufe real

- El **sustituto** es una función falsa de `responder_m3` que viene en el
  notebook de S13: devuelve texto de relleno para que el pipeline corra de
  punta a punta **mientras M3 real no esté conectado**. Permite que P2/P3
  trabajen el eval set y el harness sin depender de levantar Amparo en Colab.
- El **enchufe real** (T7, Martín/Tomás) reemplaza ese sustituto por un wrapper
  sobre `SistemaRAG`/`Agente` de Amparo (importado desde `src/`), **misma
  firma**. La rúbrica exige componente visual REAL; para los 3.0 completos la
  entrega final debe usar M3 real, no el sustituto.
- **Plan B:** si M3 real no logra levantarse en Colab a tiempo, se deja el
  sustituto pero **declarado explícitamente en el README de entrega**.

---

## 4 · Qué se entrega (carpeta `m4/`)

```
m4/
  README_PLAN.md        ← este archivo (plan interno, NO es la entrega)
  pipeline/             el notebook de S13 terminado (ver() + sistema_multimodal + enchufe)
  eval_set/
    casos_m4.csv        ≥5 casos con imagen, 1 adversarial, criterio por caso
    imagenes/           documentos sintéticos anonimizados (generados → etiquetados)
  scorecard_m4.csv      salida del harness, caso por caso, con latencia
  README.md             ← LA ENTREGA · una página (T8)
```

El `README.md` de entrega (una página) debe contener, según rúbrica: la
pregunta del usuario · el patrón y el modelo · dónde se enchufó · la tabla de
delta M3 vs M4 (con latencia) · el peor caso · los límites y la ética. **Si
alguien lee solo esa página, entiende M4.**

---

## 5 · La rúbrica (10 puntos) y dónde se cubre cada punto

| Criterio | Peso | Qué se mira | Tareas |
|---|---|---|---|
| Pipeline multimodal funcionando | **3.0** | `sistema_multimodal` responde de punta a punta con UN componente visual REAL (no mock), reproducible desde el repo | T1, T2, T7 |
| Harness, scorecard y delta | **2.5** | la misma función de M2 califica los casos nuevos; tabla M3 vs M4 con latencia; peor caso analizado | T5, T6 |
| Eval set con imagen | **2.0** | ≥5 casos, criterio declarado por caso, al menos uno adversarial, imágenes anonimizadas | T3, T4 |
| Justificación del patrón | **1.5** | la pregunta del usuario, por qué ese patrón y ese modelo, qué alternativa descartaron | T8 |
| Límites y ética | **1.0** | etiqueta "generada" si aplica, válvula, datos personales fuera del repo, "describe no diagnostica" | T3, T8 |

> Lo que va más allá de lo visto en clase (SAM como tool, ColPali, ViT con
> LoRA) **se valora en la nota**. Candidato realista para nosotros: SAM para
> recortar el documento antes de leerlo, o ColPali por ser corpus de escaneos.
> Opcional, solo si sobra tiempo.

---

## 6 · Reparto por persona

| Persona | Responsable de | Tareas | Puntos que defiende |
|---|---|---|---|
| **P1 · Santiago** | Pipeline: `ver()` y el esqueleto | **T1, T2** | 3.0 (parte visual) |
| **P2 · Lucas** | Eval set + imágenes sintéticas | **T3, T4** | 2.0 |
| **P3 · Nico** | Harness + scorecard + delta + README entrega | **T5, T6, T8** | 2.5 + 1.0 |
| **P4 · Martín / Tomás** | Reemplazar el sustituto por M3 real | **T7** | 3.0 (enchufe real) |
| **Todos** | Verificación final contra el checklist | **T9** | — |

> Lucas (P2) y Nico (P3) se coordinan: comparten el formato del eval set
> (columnas e IDs de casos) porque el harness de Nico lee los casos de Lucas.
> Mientras tanto ambos trabajan con el **sustituto** y las imágenes de ejemplo
> hasta que Santiago (T2) y Martín/Tomás (T7) tengan listo lo real.

### Orden de dependencias

```
T1 (Santiago) ─► T2 (Santiago) ─┐
                                 ├─► T7 (Martín/Tomás) ─► T9 (todos)
T3 (Lucas) ─► T4 (Lucas) ───────┤
                                 │
T5 (Nico) ─► T6 (Nico) ─► T8 (Nico)
```

Santiago y Lucas/Nico pueden arrancar **en paralelo desde ya** (Nico con el
sustituto). Martín/Tomás (T7) necesita que Santiago termine T2 para enchufar
el VLM real al M3 real.

---

## 7 · Las tareas en detalle

Cada tarea dice su objetivo, su prueba de que quedó bien, y su demo.

### T1 · [Santiago] Esqueleto del pipeline reproducible
- **Objetivo:** copiar el notebook resuelto de S13
  (`EAFIT-SI4006/sesiones/s13/S13_Lab_Integracion_Visual_RESUELTO.ipynb`) a
  `m4/pipeline/`, fijar `PATRON = 'input'`, dejar el setup (instalación,
  imports, `cargar()`) corriendo desde cero en Colab T4. Definir
  `PREGUNTA_USUARIO` del dominio de Amparo.
- **Prueba:** las celdas 0-1 corren en un Colab limpio sin error y cargan 3
  imágenes de ejemplo.
- **Demo:** notebook en Colab que imprime el device y la lista de imágenes.

### T2 · [Santiago] La función `ver()` con el VLM + válvula
- **Objetivo:** `ver(imagen) -> (texto_crudo, json)` con Qwen2-VL-2B. Escribir
  `INSTRUCCION_DOMINIO` con los 5 campos de la sección 3.1, la `VALVULA`
  ("responde solo con lo que se ve; si no, 'No se aprecia en la imagen.'") y
  `parsear_json`.
- **Prueba:** celda 2D corre `ver()` sobre 3 imágenes imprimiendo salida +
  latencia; una imagen sin el dato pedido dispara la válvula (JSON con `null`).
- **Demo:** tabla de 3 imágenes con su JSON extraído y los segundos que tardó.

### T3 · [Lucas] Imágenes sintéticas anonimizadas
- **Objetivo:** crear 5-6 **documentos jurídicos falsos** (plantillas:
  notificación, oficio, respuesta de petición) sin ningún nombre/cédula real,
  guardados en `m4/eval_set/imagenes/`. Las generadas por IA llevan **etiqueta
  visible** ("documento sintético / generado"). Uno diseñado para ser
  **adversarial** (ilegible, o sin el dato que la pregunta pide).
- **Prueba:** checklist de anonimización (sin caras, sin datos personales
  reales, sin firmas/sellos reales); todas cargan con `cargar()`.
- **Demo:** la carpeta de imágenes + una lista que dice, por imagen, por qué
  es anónima y cuál es la adversarial.

### T4 · [Lucas] Eval set CSV con criterio por caso
- **Objetivo:** `m4/eval_set/casos_m4.csv` con ≥5 filas y columnas
  `id, pregunta, imagen, esperado, criterio, tipo`. Criterios variados
  (`exacto`, `campos`, `valvula`, `juez_vlm`), **exactamente 1 adversarial**
  con criterio `valvula`. **Cada criterio se escribe ANTES de correr el
  sistema** (regla de M2: elegir el criterio después de ver la respuesta no es
  evaluación).
- **Prueba:** el CSV carga en pandas; cada `imagen` referencia un archivo que
  existe en `imagenes/`; hay exactamente 1 fila `tipo == 'adversarial'`.
- **Demo:** la tabla `CASOS` renderizada con los 5+ casos y sus criterios.

### T5 · [Nico] Harness con criterios que miran
- **Objetivo:** reusar la función `calificar`/`harness` de M2 y agregar los
  criterios nuevos: `nota_exacto`, `nota_campos`, `nota_valvula`,
  `nota_juez_vlm` (faithfulness visual: le pregunta al mismo Qwen2-VL si lo que
  dijo el sistema se sostiene en la imagen, SI/NO).
- **Prueba:** cada función de nota devuelve un valor en [0,1] sobre casos de
  prueba fabricados; `calificar` enruta por el criterio correcto.
- **Demo:** correr `calificar` sobre 2-3 casos mock y mostrar las notas.

### T6 · [Nico] Correr harness, scorecard y tabla de delta
- **Objetivo:** bucle que corre `sistema_multimodal` sobre cada caso, produce
  `m4/scorecard_m4.csv` (`id, criterio, tipo, nota, segundos, salida`), y la
  **tabla de delta** con 5 filas: casos sin imagen (M2) · casos con imagen
  (nuevos) · adversarial (válvula) · latencia media · peor caso. Los números
  de M3 salen del **scorecard real que ya entregamos** (leer de `results/`),
  NO del placeholder `0.74` del notebook.
- **Prueba:** `scorecard_m4.csv` tiene tantas filas como casos; la tabla de
  delta trae los números reales de M3.
- **Demo:** el CSV + la tabla de delta impresa con el peor caso identificado.

### T7 · [Martín / Tomás] Enchufar el M3 real (reemplazar el sustituto)
- **Objetivo:** reemplazar la función `responder_m3` **sustituto** por un
  wrapper real sobre `SistemaRAG` o `Agente` de Amparo, importado desde `src/`,
  con la **misma firma** `responder_m3(relato: str) -> str`. Documentar en el
  notebook qué brazo de M3 se usó y cómo se cargó (pesos LoRA, índice, corpus).
- **Prueba:** `sistema_multimodal(pregunta, imagen)` devuelve una respuesta del
  motor de reglas de M3 usando los datos del documento; el notebook corre
  entero con "Entorno → Reiniciar y ejecutar todo".
- **Plan B:** si no levanta en Colab, dejar el sustituto y **declararlo en el
  README de entrega** (lo coordina con Nico/T8).
- **Demo:** un caso real con imagen → documento leído por el VLM → mecanismo
  decidido por el motor de reglas de Amparo.

### T8 · [Nico] README de entrega (una página)
- **Objetivo:** `m4/README.md` (una página) con: la pregunta del usuario · el
  patrón y el modelo y por qué (+ alternativas descartadas) · dónde se enchufó
  · la tabla de delta M3 vs M4 · el **peor caso explicado** · límites y ética
  (VLM describe ≠ diagnostica, válvula, datos personales fuera del repo, un
  caso donde el sesgo del modelo podría importar en el dominio legal).
- **Prueba:** una persona que lee **solo** el README entiende M4 (pasa el
  checklist de la rúbrica).
- **Demo:** el README renderizado cubriendo los 6 puntos.

### T9 · [Todos] Verificación final
- **Objetivo:** pasar los 5 checks de "Antes de entregar" del curso:
  1. El notebook corre desde cero en un Colab limpio (Reiniciar y ejecutar
     todo).
  2. Hay ≥5 casos con imagen, uno adversarial, cada uno con su criterio escrito
     ANTES de correr.
  3. La tabla de delta tiene números de M3 (del scorecard entregado) y de M4,
     con latencia.
  4. El peor caso está identificado y explicado en el README.
  5. Las imágenes están anonimizadas; las generadas llevan etiqueta.
- **Prueba:** ejecución completa en un runtime Colab nuevo sin fallos.

---

## 8 · Reglas de trabajo del equipo

- **Rama:** todos trabajamos sobre `m4`. Commits pequeños y descriptivos.
- **NO ejecutar los notebooks en la terminal local.** No hay GPU; los notebooks
  (VLM, M3) corren en **Colab T4**. En local solo se edita código, se arma el
  CSV, se escribe el README y se revisa. Ejecutar un notebook de VLM aquí nos
  cuelga.
- **El sistema de M3 NO se reescribe.** El VLM se enchufa antes del RAG; `src/`
  de Amparo se toca lo mínimo (idealmente nada, solo se importa).
- **Honestidad de Amparo:** la tabla de delta debe decir si **empeoró** lo
  viejo, no solo presumir mejoras. El peor caso es la fila más valiosa — el
  equipo que no encontró fallos no buscó.
- **Ética (vale 1.0 y es borrador del criterio de ética del proyecto final):**
  cero documentos reales, cero firmas/sellos, cero datos personales en el repo.
  Imágenes sintéticas y etiquetadas. "El VLM describe, no diagnostica" va
  escrito en el README.

---

## 9 · Material de referencia (para quien quiera el fundamento)

- `EAFIT-SI4006/sesiones/s11/` — ViT, CLIP, VLM (Qwen2-VL). PDF + notebook
  resuelto. De aquí sale `ver()` para input.
- `EAFIT-SI4006/sesiones/s12/` — difusión (solo relevante si fuéramos output;
  no es nuestro caso).
- `EAFIT-SI4006/sesiones/s13/` — integración y entrega M4. **El notebook
  resuelto `S13_Lab_Integracion_Visual_RESUELTO.ipynb` es la plantilla base**
  de nuestro pipeline. El PDF trae la rúbrica exacta.
- Código de Amparo que se enchufa: `src/sistema.py` (`SistemaRAG`),
  `src/agente.py` (`Agente`), `src/reglas.py` (el motor), `src/schema.py`
  (el formato de salida), `src/harness.py` (el harness de M2 que reusamos).
