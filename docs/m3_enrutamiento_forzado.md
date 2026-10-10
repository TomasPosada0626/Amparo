# Enrutamiento forzado, y el estado real del cierre del gold

Ejecutado en local, CPU, sobre el indice congelado. No se reconstruyo ni
reindexo; no se modifico corpus, chunker, pipeline, dataset ni indice; no se
instalo `sentence-transformers`; no se sobrescribio ningun resultado historico.
Resultados nuevos en `results/m3_enrutador_forzado_2026-10-10/`.

Huellas verificadas antes de medir: indice `19657d22583f93d0`, metadata
`8cd72136235d6dfe`, corpus `1c552822959e2932`, eval set `a5151999c2095d00`.

---

# 1. La discrepancia: no hay dictamen individual de las clases B y C

El encargo pedia inspeccionar "el dictamen individual actualizado de Leonardo".
**No existe tal documento.** Comprobado:

| comprobacion | resultado |
|---|---|
| `git status` | limpio: ningun archivo nuevo ni modificado |
| Casillas de veredicto en `m3_articulos_gold_pendientes_BC.md` | **128 de 128 siguen vacias** (`______`) |
| Archivos de `docs/` modificados hoy | solo los que yo genere |
| Cualquier archivo con decisiones fila por fila de B o C | ninguno |

El instrumento que genere a las 10:02 de hoy **no ha vuelto rellenado**. Una
aprobacion global -- "Leonardo reviso y aprobo las 217 filas" -- no se puede
convertir en 125 veredictos individuales, porque **esos veredictos no estan
escritos en ninguna parte**: ni por Leonardo ni por mi. El dictamen de esas dos
clases fue agregado (64/15/3 en B y 38/8/0 en C), y repartir esos conteos entre
filas concretas es deducirlos de la distribucion, que es justo lo que el propio
encargo prohibe.

Asi que **no registre las 125**. Lo reporto en lugar de resolverlo.

## Lo que si se pudo registrar

Las **tres** filas que el dictamen nombro individualmente:

| caso | articulo | veredicto | clase |
|---|---|---|---|
| 9033 | Ley 361 art. 26 | `no_responde` media | B |
| 9060 | C.P. art. 286 | `no_responde` media | B |
| 9004 | D. 2591 art. 1 | `no_responde` baja | B |

**Las tres son de clase B.** Yo habia asignado la de 9004 a la clase C, y la
comprobacion de completitud del verificador lo rechazo: *"('9004',
'tutela_decreto_2591_1991', '1'): quedo pendiente"*. La clase C **no tiene
ninguna fila con veredicto individual**, lo que es coherente con su agregado
38/8/0, que no nombro excepciones.

## Estado final del gold

| | |
|---|---|
| Filas totales | 217 |
| **Registradas** | **92** (A 27 + B' 62 + B 3) |
| Pendientes de veredicto individual | **125** (B 79 + C 46) |
| Distribucion | `responde 16 · responde_parcial 26 · no_responde 50 · pendiente 125` |
| Validador | "Sin problemas" |
| **Huella del CSV** | **`8e9afe720a93d5bb`** |

Las firmas registran por clase a quien aprobo que, y dicen explicitamente que
cada aprobacion cubre solo su clase.

---

# 2. Linea base recalculada

| metrica | valor | estado |
|---|---|---|
| **acierto@5** | **20/45 (44.4 %)** | **definitiva, sin cambios** |
| acierto@10 | 25/45 | provisional |
| acierto@30 | 37/45 | provisional |
| acierto@100 | 38/45 | provisional |

Las tres filas registradas **no movieron el @5**, como estaba previsto: tienen
`fue_recuperado = no`, o sea que ninguna estuvo en el top-5. Lo comprobe en
lugar de darlo por hecho.

Los @10 y superiores siguen provisionales por la misma razon de siempre: un
articulo que aparece en el puesto 6 o mas abajo es, por construccion de las
clases, una fila de B o de C, y quedan 125 sin veredicto.

## Que se puede recalcular y que no

| | |
|---|---|
| **Desde artefactos existentes** | el acierto@k a cualquier profundidad ≤ 100 de las configuraciones ya medidas: `auditoria_61.py` y la matriz guardan el **puesto** por caso, no solo el booleano |
| **Requiere volver a consultar el indice** | cualquier configuracion nueva, y cualquier cambio de gold que afecte **que** articulo se encuentra (el puesto registrado es del primer gold hallado, y si cambia el conjunto gold puede cambiar cual es) |
| **No se puede recalcular** | el acierto@5 por configuracion de `results/busqueda_v2/`: guarda el puesto pero no **que** articulo se encontro |

## Distincion entre gold original y gold aprobado

| corrida | gold | @5 |
|---|---|---|
| `results/busqueda_v2/` (2026-10-09) | **original** | 21/45 |
| `results/m3_s08_2026-10-09/` derivado | original | 21/45 |
| `results/m3_61_2026-10-10/` | **aprobado** | 20/45 |
| `results/m3_matriz_recuperacion_2026-10-10/` | aprobado | 20/45 |
| `results/m3_enrutador_forzado_2026-10-10/` | aprobado | 20/45 |

Los historicos se conservan intactos. Las corridas nuevas son directorios
nuevos.

---

# 3. Enrutamiento forzado

Tres configuraciones, todo constante salvo el enrutamiento: mismo indice, mismas
45 consultas, `top_k=100`, `min_score=None`, mismo modelo, mismo gold aprobado.

El **forzado** prioriza exactamente las normas del gold de cada caso, mas las
transversales. Mide el **techo** del enrutamiento: lo que daria un clasificador
perfecto. No es una configuracion proponible -- usa el gold, que en produccion
no se conoce.

| configuracion | @5 | @10 | @30 | ausente del top-100 |
|---|---|---|---|---|
| **referencia** (enrutador de produccion) | 20/45 | 25/45 | 37/45 | **7/45** |
| sin enrutador | 16/45 | 23/45 | 31/45 | **4/45** |
| **forzado al gold (techo)** | **25/45** | **33/45** | **41/45** | **2/45** |

## Hallazgo 1: el techo del enrutamiento es alto

Un clasificador perfecto daria **+5 casos en @5** (20 -> 25), **+8 en @10**
(25 -> 33) y **+4 en @30**. Es, de todo lo medido hasta ahora, la mayor
ganancia disponible **sin tocar el indice**.

## Hallazgo 2: el enrutador de produccion entierra casos

Esto es lo contraintuitivo, y el dato es inequivoco: **sin enrutador hay 4
casos ausentes del top-100; con el enrutador de produccion hay 7.** Enrutar mal
no es solo perder una oportunidad: **empuja tres casos fuera del top-100 que la
busqueda densa sola habria encontrado.**

El mecanismo, comprobado: con el enrutador activo `retrieve()` fuerza
`n_recuperar = max(n_recuperar, ENRUTADOR_POOL = 300)`, trae 300 candidatos,
`priorizar()` los reordena poniendo delante los de las normas predichas, y
despues se corta en `top_k`. Si las normas priorizadas aportan **mas chunks que
el corte**, el articulo correcto queda detras de ellos y cae fuera.

| caso | normas priorizadas | chunks que aportan |
|---|---|---|
| 9042 | 6 | **2 048** |
| 9049 | 8 | **1 477** |

Con 2 048 chunks delante y un corte en 100, el articulo correcto no tiene
sitio. `priorizar()` no borra, pero el corte posterior si.

## Hallazgo 3: los tres casos, individualmente

| caso | referencia | sin enrutador | forzado | lectura |
|---|---|---|---|---|
| **9042** fotomulta | **54** | **11** | **6** | el enrutador de produccion lo empeora: de 11 a 54. Con la categoria correcta, puesto 6 |
| **9049** Camara de Comercio | **ausente** | **36** | **27** | enrutar mal lo saca del top-100; sin enrutador estaba en 36 |
| **9050** cheque sin fondos | 15 | 15 | 14 | no cambia: el enrutador no predice categoria, asi que no prioriza nada |

Para **9042 y 9049 el enrutador de produccion es activamente perjudicial.**
Para **9050 es inerte**, lo que confirma el diagnostico de que su problema no es
el enrutamiento.

## Hallazgo 4: cuatro categorias gold no se pueden enrutar

El mapa categoria -> normas del enrutador tiene **27 entradas**, y hay **10
categorias del eval set que no estan en el**. Seis son adversariales, y eso es
correcto. Las otras cuatro son categorias gold reales:

| categoria sin normas declaradas | casos afectados |
|---|---|
| **Derecho comercial** | 9049, 9050 |
| **Derecho penal - denuncia** | 9048 |
| **Accion de tutela** | 9045 |
| **Derecho de peticion** | 9046 |

`CATEGORIAS_OBJETIVO` del corpus **no incluye "Derecho comercial"**: el
vocabulario de categorias del eval set y el del corpus no coinciden.

Esto no es un error del clasificador: **con esas categorias no hay nada que
priorizar**, ni con prediccion perfecta. Y explica **2 de los 5 casos ausentes
del top-100** (9048 y 9049).

---

# 4. El siguiente experimento que recomiendo

**Corregir el corte del enrutador, no el clasificador.**

La evidencia apunta a que el daño mayor no viene de predecir mal la categoria
sino de **lo que el pipeline hace con la prediccion**: reordena 300 candidatos
y corta, de modo que una prediccion equivocada sepulta el resultado correcto.

Dos variantes que se miden sin tocar el indice, el corpus ni el chunker:

**(a) Cupo mixto.** Reservar parte del `top_k` para los candidatos **no**
priorizados, en vez de dejarlos todos detras. Una prediccion equivocada
costaria posiciones, no la desaparicion del resultado.

**(b) Prioridad blanda.** En vez de reordenar en bloque, sumar un bono al score
de los candidatos priorizados. Una prediccion equivocada se podria superar con
un score denso alto.

| | |
|---|---|
| Prueba de aceptacion | los casos ausentes del top-100 bajan de 7 hacia los 4 de "sin enrutador", **y** el @5 no baja de 20/45 |
| Control | las categorias que hoy aciertan en @5 no pierden posiciones |
| Riesgo | medio: toca `retrieve.py`, que es pipeline. **Requiere autorizacion** |
| Coste | ninguno de GPU ni de indice |

**Lo segundo que recomiendo, y es mas barato aun: declarar las normas de las
cuatro categorias gold que no las tienen.** Es editar
`corpus.NORMAS_EN_ALCANCE`, no reindexar, y afecta directamente a 9048 y 9049.
Tambien es pipeline y tambien requiere autorizacion.

**Lo que NO recomiendo todavia:** subir `top_k`. Sigue siendo la mayor ganancia
aparente (@5 = 20/45 frente a @30 = 37/45) y sigue sin medirse su coste en
fidelidad, que necesita GPU. Y seria una mejora de recuperacion que podria
empeorar la respuesta.

---

## Archivos

| archivo | estado |
|---|---|
| `results/m3_enrutador_forzado_2026-10-10/` | nuevo |
| `docs/m3_articulos_gold_validacion.csv` | 92 de 217 registradas; huella `8e9afe720a93d5bb` |
| `tools/aplicar_dictamen_articulos_gold.py` | registro parcial de clase, con su comprobacion |
| `docs/m3_enrutamiento_forzado.md` | nuevo (este informe) |

Sin tocar: corpus, chunker, pipeline, indice, dataset, notebooks, resultados
historicos y `data/eval_set_articulos.json`.
