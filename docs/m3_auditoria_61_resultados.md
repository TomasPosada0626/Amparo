# Auditoria 6.1: resultados

**Ejecutada** el 2026-10-10 en local, Windows, CPU. Resultados en
`results/m3_61_2026-10-10/`.

No se reconstruyo ni reindexo. El indice solo se leyo. No se modifico corpus,
chunker, pipeline, dataset ni resultados historicos.

## Procedencia, verificada contra los archivos

| artefacto | huella | estado |
|---|---|---|
| `rag_index.faiss` | `19657d22583f93d0` | **verificado contra el archivo** |
| `rag_index_metadata.jsonl` | `8cd72136235d6dfe` | verificado |
| corpus (37 `.md`) | `1c552822959e2932` | verificado |
| `eval_set.json` | `a5151999c2095d00` | verificado |

Las cuatro coinciden con lo que declaran los manifiestos de S08, S10 y
busqueda_v2. **Es la primera vez que `hash_indice` se comprueba contra el
archivo** y no solo se lee de un manifiesto: el `.faiss` estaba en
`Downloads/busqueda_v2-20261009T012132Z-1-001/`, de la descarga del 2026-10-09,
y no habia que volver a bajarlo.

Indice cargado: **11 975 vectores, 768 dimensiones**, alineado con su metadata.

Entorno: python 3.13.5, `torch 2.14.1+cpu`, `faiss-cpu 1.15.1`,
`transformers 5.15.0`, `numpy 2.5.2`, `rank-bm25 0.2.2`. Configuracion de la
medicion: `top_k=100`, `min_score=None`, `use_router=True`.

Gold: se aplicaron los veredictos **registrados** del CSV -- 5 `no_responde`
quitadas y 3 omisiones añadidas -- y se conservaron tal cual las **128** filas
sin registro individual. `eval_set_articulos.json` no se modifico.

---

## El resultado

| profundidad | acierto por articulo |
|---|---|
| **@5** | **20 / 45 — 44.4 %** |
| @10 | 25 / 45 — 55.6 % |
| **@30** | **37 / 45 — 82.2 %** |
| @100 | 38 / 45 — 84.4 % |
| **ausente del top-100** | **7 / 45** |

El **@5 = 20/45 coincide exactamente** con la linea base que calcule desde los
registros de S08 con el gold aprobado. Tercera validacion cruzada del mismo
numero, ahora consultando el indice.

### Donde cae el articulo gold

| puesto | casos |
|---|---|
| 1 | 7 |
| 2-5 | 13 |
| 6-10 | 5 |
| **11-30** | **12** |
| 31-100 | 1 |
| ausente | 7 |

## El veredicto: el ranking domina

**17 de los 45 casos tienen el articulo recuperable pero por debajo del corte
de 5** (5 entre los puestos 6-10 y 12 entre 11-30). Solo **7 estan ausentes del
top-100**.

Dicho de otro modo: el sistema **encuentra** el articulo correcto en 38 de 45
casos. Lo que falla es **ordenarlo arriba**. Y la ganancia se agota en 30: de
@30 a @100 solo se suma un caso.

Eso responde la pregunta central de 6.1 y **no justifica tocar el chunker por
este motivo**.

---

## Los 11 casos criticos

| caso | categoria | puesto real | diagnostico |
|---|---|---|---|
| **9066** antejardin invadido | Licencias urbanisticas | **1** | **era error del gold**: el art. 79 de la Ley 1801 que añadi en B' estaba en el primer puesto |
| **9004** EPS, 3 meses esperando | Salud / EPS | **2** | **era error del gold**: el art. 10 de la Ley 1751 estaba segundo |
| **9050** cheque sin fondos | Derecho comercial | 15 | ranking |
| **9057** codeudor embargado | Embargos | 21 | ranking |
| **9035** deposito no devuelto | Arriendo | 23 | ranking |
| **9042** fotomulta de hace un año | Comparendos de transito | **54** | ranking, agravado por el enrutador (predice Arriendo y Embargos) |
| **9010** antes de demandar al ex-socio | Conciliacion prejudicial | **ausente** | representacion u otra causa |
| **9038** contratista con horario y jefe | Relaciones laborales | **ausente** | idem |
| **9048** estafa en compra por internet | Derecho penal - denuncia | **ausente** | idem |
| **9049** registro en Camara de Comercio | Derecho comercial | **ausente** | el enrutador predice Propiedad intelectual |
| **9058** expulsion del colegio | Educacion | **ausente** | las derogatorias: 4 de 5 fragmentos eran "Derogado" |

**Dos de los 11 no eran fallos del sistema sino del gold.** 9066 y 9004 tienen
el articulo en los puestos 1 y 2: los artículos que faltaban eran justamente
las omisiones de clase B' que se registraron. Corregir el gold los convirtio en
los aciertos mas limpios del benchmark.

## El umbral, aplicado como se fijo

La regla, fijada **antes** de ver el resultado: de los 7 casos sin causa
identificada (9004, 9010, 9035, 9038, 9048, 9057, 9066), si 4 o mas tienen el
articulo en el top-100 el diagnostico dominante es ranking; si 3 o mas no
aparecen, hay representacion que corregir.

| | |
|---|---|
| En el top-100 | **4**: 9066 (1), 9004 (2), 9057 (21), 9035 (23) |
| Ausentes | **3**: 9010, 9038, 9048 |

**Los dos criterios se cumplen.** Era el escenario que anticipe como posible y
legitimo: el ranking domina **y** queda un nucleo de representacion. No se
eligio el resultado despues de verlo.

---

## El hallazgo que invierte un supuesto mio

De los **38 aciertos**, **24 llegan por un chunk que no lleva el encabezado del
articulo**, y en **24 de 25** de esos casos el articulo esta genuinamente
partido en 2 o mas chunks.

En el informe integral (H9) presente los 2 060 chunks de continuacion sin
encabezado como un **pasivo**: fragmentos huerfanos que no se pueden encontrar.
La medicion dice lo contrario: **son el vehiculo de la mayoria de los aciertos.**

Eso no demuestra que añadirles el encabezado haria daño. Lo que si hace es
matar la historia simple -- "los chunks huerfanos no se encuentran, por eso
fallamos" -- y convertir la correccion **2** del plan en un cambio de **riesgo
real**: tocaria el texto de los fragmentos que hoy producen casi dos tercios de
los aciertos.

**Limite de la medicion:** el indicador comprueba si "Articulo N" aparece en
los primeros 160 caracteres del chunk, asi que tambien marca un chunk que
empieza por otro articulo o por un encabezado de division. Los 24 de 25 con
articulo partido son la evidencia de que mide mayormente lo que pretende, no
una prueba de que lo mida siempre.

---

## Que cambia en el plan de reconstruccion

### Sube de prioridad

**Subir el corte de recuperacion.** Es lo que la evidencia respalda con mas
fuerza: @5 = 20/45 frente a @30 = 37/45. Pasar de 5 a 30 fragmentos casi
duplicaria el acierto por articulo.

Pero **no es gratis y no se mide con esta auditoria**: 30 fragmentos en el
prompt son mas contexto, mas ruido y mas tokens, y lo que hay que vigilar es la
**fidelidad** de la respuesta. La prueba correcta mide acierto **y**
faithfulness en la misma corrida. No mueve el indice.

**El enrutador.** Explica 9042 (puesto 54) y 9049 (ausente), y en 9050 no
predice categoria. Tres de los siete casos peores. Tambien es independiente del
indice.

### Baja de prioridad

**El encabezado en los chunks de continuacion.** Los articulos partidos no son
el obstaculo que supuse: son por donde llegan 24 de los 38 aciertos. La
correccion sigue siendo defendible en teoria, pero ya no tiene el respaldo que
le atribui y su riesgo es mayor.

### Se mantiene

**El filtro de derogatorias puras.** 9058, el unico de los 11 con causa
demostrada, sigue ausente del top-100 y es el caso donde cuatro de los cinco
fragmentos eran la palabra "Derogado". Riesgo bajo, control en cero.

### Lo que queda sin explicar

**9010, 9038 y 9048**: ausentes del top-100 sin causa identificada. Sus
articulos gold **si estan en el indice** -- se verifico en el anexo de chunking
que ninguno de los 155 falta --, asi que no es cobertura. Son el nucleo de
representacion de verdad, y son tres casos, no once.

Lo que no se midio y haria falta para cerrarlos: con que puntaje quedan sus
chunks frente a los 100 que si entraron. Eso distingue "el embedding no los
acerca a esta pregunta" de "el enrutador los relego".

---

## Resumen de lo que esta auditoria deja establecido

| | |
|---|---|
| Linea base acierto@5 | **20/45 (44.4 %)**, con el gold registrado y triple validacion cruzada |
| Causa dominante de los fallos | **ranking**: 17 de 45 tienen el articulo entre los puestos 6 y 30 |
| Nucleo de representacion | **3 casos** (9010, 9038, 9048), no 11 |
| Causa demostrada aparte | **1 caso** (9058, derogatorias) |
| Fallos del gold, ya corregidos | **2 casos** (9066, 9004), que ahora aciertan en los puestos 1 y 2 |
| Enrutador implicado | **3 casos** (9042, 9049, 9050) |
| Profundidad util | se agota en 30: de @30 a @100 se suma un caso |

El gold sigue **parcialmente registrado: 89 de 217 filas**. Las 128 de B y C no
mueven el @5 -- demostrado -- pero **si determinan el @10 y mas alla**, asi que
los numeros de @10, @30 y @100 de este informe quedan sujetos a cerrarlas.
