# Experimentos de recuperacion y cierre pendiente del gold

Ejecutado en local, CPU, sobre el indice congelado. No se reconstruyo ni
reindexo, no se modifico el corpus, los chunks, el indice ni las etiquetas
aprobadas. Resultados nuevos en `results/m3_matriz_recuperacion_2026-10-10/`,
sin sobrescribir nada.

Huellas verificadas antes de medir: indice `19657d22583f93d0`, metadata
`8cd72136235d6dfe`, corpus `1c552822959e2932`, eval set `a5151999c2095d00`.

---

# 1. Estado del gold

| clase | filas | registradas |
|---|---|---|
| A | 27 | si |
| B' | 62 | si |
| B | 82 | **no** |
| C | 46 | **no** |
| **total** | **217** | **89** |

El CSV sigue en `responde 16 · responde_parcial 26 · no_responde 47 ·
pendiente 128`. **No se toco.**

## Que metricas son definitivas y cuales no

| metrica | estado | por que |
|---|---|---|
| **acierto@5 = 20/45** | **definitiva** | Las 128 filas pendientes tienen `fue_recuperado = no`: ninguna estuvo en el top-5, asi que su veredicto no entra en el calculo. Demostrado, no supuesto. |
| acierto@10, @30, @100 | **provisionales** | Un articulo en el puesto 6 o mas abajo es, por construccion de las clases, una fila de B o de C. Cerrarlas puede moverlos en las dos direcciones. |
| Posiciones por caso | firmes | Son del recuperador, no dependen del veredicto |
| Comparacion entre configuraciones | **valida** | Todas usan el mismo gold, el mismo indice y las mismas consultas: el sesgo pendiente es identico en las cuatro y no altera el orden entre ellas |

## Lo que se le pide a Leonardo

`docs/m3_articulos_gold_pendientes_BC.md` (257 KB, **128 filas**). Por cada
fila: la consulta, el texto completo del articulo, en cuantos chunks esta
partido y una casilla de veredicto.

**La casilla va vacia en 125 de las 128.** Solo tres llevan propuesta, que son
las unicas que el dictamen nombro individualmente:

| caso | articulo | propuesta | por que |
|---|---|---|---|
| 9033 | Ley 361 art. 26 | `no_responde` media | prohibe que **la discapacidad** obstaculice una vinculacion; una incapacidad temporal por cirugia no es lo mismo |
| 9060 | C.P. art. 286 | `no_responde` media | la falsedad ideologica es del **servidor publico** que extiende el documento, no del contratista al que se lo piden firmar |
| 9004 | D. 2591 art. 1 | `no_responde` baja | repite el art. 86 de la Constitucion; redundancia, no error |

Las otras 125 van **sin propuesta**: su dictamen fue agregado (64/15/3 en B,
38/8/0 en C) y deducir de la distribucion el veredicto de cada fila seria
inventarlo.

---

# 2. La matriz experimental

## Dos hallazgos de diseño que la simplifican

**La "profundidad de recuperacion" no es una variable libre en produccion.**
`retrieve()` deriva internamente cuantos candidatos trae:

```
use_rerank -> RERANK_INPUT_N (30)
use_hybrid -> HYBRID_TOP_N   (30)
ninguno    -> top_k
y si el enrutador esta activo: n_recuperar = max(n_recuperar, ENRUTADOR_POOL=300)
```

Con el enrutador encendido -- que es produccion -- **siempre se traen 300
candidatos**. Barrer 5/10/20/30 como dimension A mediria algo que la
configuracion real ya fija en 300. La variable que si se controla es `top_k`,
los fragmentos devueltos.

**Y la dimension A se deriva sin volver a consultar.** Midiendo con
`top_k=100` y registrando el **puesto** del articulo gold, el acierto@k para
cualquier k ≤ 100 sale de los mismos datos. Eso evita 4 corridas redundantes.

## Lo ejecutado

Cuatro configuraciones, `top_k=100`, `min_score=None`, mismas 45 consultas,
mismo indice, mismo gold. La unica variable es la configuracion del
recuperador.

| configuracion | @1 | @5 | @10 | @30 | MRR | latencia mediana |
|---|---|---|---|---|---|---|
| A denso | — | 16/45 | 23/45 | 31/45 | 0.295 | — |
| **A denso + enrutador** | — | **20/45** | **25/45** | **37/45** | 0.290 | — |
| B hybrid | — | 16/45 | 19/45 | 30/45 | 0.267 | — |
| B hybrid + enrutador | — | **20/45** | **25/45** | 34/45 | **0.339** | — |

El `37/45` de `A denso+enrutador` reproduce exactamente el @30 de la auditoria
6.1, que se corrio por separado. Consistencia confirmada.

### Lo que dice

**El enrutador es la ganancia clara y consistente.** +4 casos en @5 en las dos
familias (16 -> 20, un 25 % relativo), +2 en @10 y +6 en @30 en la densa. Es el
unico cambio con efecto inequivoco, y **no toca el indice**.

**El hybrid no ayuda, y a veces estorba.** Mismo @5 que la densa (16 y 20),
peor @10 sin enrutador (19 frente a 23) y peor @30 en los dos casos (30 frente
a 31, 34 frente a 37).

**Con una excepcion honesta: el MRR.** `hybrid+enrutador` da 0.339 frente a
0.290 de la densa. Encuentra **menos** articulos pero los coloca **mas
arriba**. Es un intercambio real, no ruido, y qué preferir depende de si el
prompt recibe 5 fragmentos o 30. No se elige ganador con este dato.

## Lo que NO se pudo ejecutar

| dimension | bloqueo |
|---|---|
| **C. Reranking** | `tools/rag/rerank.py` usa `CrossEncoder` de **`sentence-transformers`**, que no esta instalado. Instalarlo es una dependencia nueva mas (arrastra su propio stack) y no se hizo sin autorizacion. |
| **B. Fragmentos al generador** (5 / 10 / 30) | Medir el efecto de meter mas fragmentos en el prompt exige **generar**: faithfulness, pertinencia de la respuesta, tokens. Eso necesita el modelo de 7B (GPU) y el juez Groq (clave en secretos de Colab). **No es medible aqui.** |

Y eso importa para la lectura del resultado: **el salto de @5 = 20/45 a @30 =
37/45 mide cuanto mejora la RECUPERACION, no cuanto mejora el producto.**
Entregar 30 fragmentos en vez de 5 es mas contexto, mas ruido y mas tokens, y
el riesgo es que la fidelidad de la respuesta baje. Ese experimento esta
diseñado y sin correr.

---

# 3. El enrutador, caso por caso

Medido con el enrutador de **produccion** (`enrutador_por_defecto`), no inferido
de las posiciones.

| caso | predice | gold | ¿prioriza el gold? | puesto real (con enrutador) |
|---|---|---|---|---|
| **9042** fotomulta | Arriendo, Embargos | C. de Transito | **no** | 54 |
| **9049** Camara de Comercio | Prop. intelectual, Garantias | C. de Comercio | **no** | **ausente** |
| **9050** cheque sin fondos | *(ninguna categoria)* | C. Comercio, CGP | **no filtra** | 15 |
| **9058** expulsion del colegio | Educacion, Familia | Ley 1620, Ley 115 | **si, las dos** | **ausente** |

**9058 es el control y sale limpio**: el enrutador acierta sus dos normas gold,
asi que su fallo **no es de enrutamiento**. Es el caso de las derogatorias --
cuatro de sus cinco fragmentos recuperados eran la palabra "Derogado" --, y eso
queda confirmado por descarte.

**La distincion que pedia el encargo, explicita:** que el articulo de 9042
aparezca en el puesto 54 **no significa que el enrutador acertara**. No
acerto: lo relego. Aparece porque `priorizar()` reordena y **no borra** -- los
candidatos de las normas no priorizadas quedan detras, no fuera --, asi que el
articulo sobrevive muy abajo. Son dos hechos compatibles y distintos.

**9050 no es un fallo de enrutamiento sino de ausencia de el**: sin categoria
predicha no hay priorizacion, y su puesto 15 es el que da la busqueda densa
cruda.

## La prueba para medir el enrutador aislado

Ya esta hecha y es la tabla de la seccion 2: **misma consulta, mismo indice,
mismo gold, y la unica variable es `use_router`**. Da +4 casos en @5. Lo que
falta para cerrar estos tres casos concretos es un experimento mas fino, que
no toca indice ni ranking:

1. Forzar la categoria correcta en 9042, 9049 y 9050 (inyectando un enrutador
   fijo por el parametro `enrutador=` que `retrieve()` ya acepta) y volver a
   medir solo esos tres.
2. Si sus puestos mejoran, el techo del enrutador esta medido: es lo que se
   ganaria con un clasificador perfecto.
3. Si 9049 sigue ausente del top-100 con su categoria forzada, su problema
   **no es el enrutador** y hay que buscarlo en la representacion.

Es barato y no necesita autorizacion de indice. No se ejecuto en esta fase
para no mezclarlo con la matriz.

---

# 4. Metricas: lo medido y lo que falta

| metrica | estado |
|---|---|
| Acierto por articulo @5 / @10 / @30 | **medido**, cuatro configuraciones |
| Posicion del articulo gold | **medido**, por caso, hasta 100 |
| Latencia | **medido** (mediana por consulta, registrada en el JSON) |
| Fragmentos / tokens al generador | no medido: requiere generar |
| `context_recall` | no medido: requiere el juez Groq |
| Faithfulness | no medido: requiere generacion con el 7B |
| Pertinencia de la respuesta | no medido: idem |

**Ninguna mejora de recuperacion de este informe es prueba de mejora
juridica.** Que el articulo correcto llegue al contexto es condicion necesaria
y no suficiente: los dictamenes de B2 ya mostraron cinco casos donde el
fragmento correcto estaba delante del modelo y la respuesta lo atribuyo mal.

---

# 5. Plan de reconstruccion unica

## Grupo 1 — no necesitan reconstruir el indice

| cambio | evidencia | prueba de aceptacion | riesgo de regresion |
|---|---|---|---|
| **Mantener el enrutador encendido** | +4 casos en @5 en las dos familias | ya cumplida | ninguno: es el estado actual |
| **Corregir el enrutador en los 3 casos** | 9042 y 9049 mal enrutados, 9050 sin categoria | los tres mejoran de puesto con la categoria forzada, y las categorias que hoy aciertan no empeoran | medio: reentrenar el clasificador puede romper lo que funciona. Medir las 27 categorias, no las 3 |
| **Subir `top_k`** | @5 = 20/45 frente a @30 = 37/45 | acierto **y** faithfulness en la misma corrida; la fidelidad no baja | **alto y no medido**: 30 fragmentos son mas ruido en el prompt |
| **No activar hybrid** | peor @10 y @30; mejor MRR | — | ninguno: es el estado actual |
| `USE_RERANK` | **sin medir**: falta `sentence-transformers` | que suba acierto@5 sin bajar faithfulness | desconocido |
| Arreglar `huella_directorio` | ordena comparando `Path`, insensible a mayusculas en Windows; mas el CRLF | el hash coincide en Windows y en Linux para el mismo contenido | ninguno sobre mediciones; cambia el valor registrado, hay que publicar la equivalencia |
| Registrar enrutador y piso efectivo en el manifiesto | el de `busqueda_v2` dice `min_score 0.82` y se midio con `None` | el manifiesto permite reconstruir la configuracion sin leer el codigo | ninguno |

## Grupo 2 — requieren reconstruir

| cambio | evidencia | prueba de aceptacion | riesgo |
|---|---|---|---|
| **Filtro de derogatorias puras** | 107 chunks, control en cero; 9058 recibio cuatro de cinco fragmentos "Derogado" | `n_chunks` 11 975 -> 11 868; 0 chunks-derogatoria; 9058 mejora; ninguna categoria hoy en 0.83-1.00 baja | **bajo**. El art. 380 de la Constitucion se conserva; 0 exclusiones de articulos sin la palabra |
| Actualizar el art. 57 del CST | version anterior a la reforma de 2025; afecta a 4630 y 9051 | una consulta por licencia por citacion judicial recupera el articulo reformado | bajo en lo tecnico; **exige fuente oficial y validacion profesional** |
| Separar fecha de conversion de version del texto | `status: in_force`, `last_updated: 2026-10-08` sobre texto de 2021 | el front matter declara la version | ninguno funcional |
| Poblar o retirar `vigente` | `True` en los 11 975 chunks | el art. 57 preexistente no figura como `vigente: True` | ninguno |

## Grupo 3 — no justifican tocar nada todavia

**Encabezado en los chunks de continuacion.** Se mantiene aqui por la evidencia
de 6.1: **24 de los 38 aciertos llegan por fragmentos sin ese encabezado**, y
en 24 de 25 el articulo esta genuinamente partido. Tocar su texto cambiaria los
fragmentos que hoy producen casi dos tercios de los aciertos. La hipotesis no
esta refutada, pero **no tiene respaldo y si tiene riesgo**.

**`MAX_TOKENS_PER_CHUNK` mayor.** Nadie ha medido que pasaria.

**Otro modelo de embeddings.** No medido.

## Orden recomendado

1. **Cerrar B y C** con el instrumento ya generado. Desbloquea los @10/@30.
2. **El experimento del enrutador forzado** sobre 9042, 9049 y 9050. Barato,
   sin indice, y dice cuanto techo tiene esa via.
3. **Medir `top_k` con generacion**, que es el unico cambio de alto impacto y
   alto riesgo sin medir. Necesita GPU.
4. **Decidir `USE_RERANK`**, lo que exige instalar `sentence-transformers`.
5. Solo entonces, **una reconstruccion** con el filtro de derogatorias, el
   art. 57 y los metadatos, y recorrer S07, S08 y S10 publicando la tabla de
   equivalencia de hashes.

Antes de cualquier corrida experimental reproducible conviene hacer primero lo
de `huella_directorio` y el registro del enrutador en el manifiesto: las dos
son baratas y las dos ya produjeron diagnosticos equivocados en esta auditoria.

---

## Archivos

| archivo | estado |
|---|---|
| `results/m3_matriz_recuperacion_2026-10-10/` | nuevo |
| `docs/m3_articulos_gold_pendientes_BC.md` | nuevo, 257 KB, 128 filas |
| `tools/pendientes_bc.py` | nuevo |
| `docs/m3_experimentos_recuperacion.md` | nuevo (este informe) |

Sin tocar: corpus, chunker, pipeline, indice, dataset, notebooks, resultados
historicos, `data/eval_set_articulos.json` y
`docs/m3_articulos_gold_validacion.csv` (sigue en 89/217).
