# M1 — Protocolo de aceptación, congelado antes de entrenar

> ## Decisión de producto, 2026-10-10: las urgencias salen del alcance
>
> **Tomada por Tomás.** Amparo responde dudas y procedimientos de ley
> colombiana. Las preguntas de urgencia inmediata dejan de ser una dimensión de
> aceptación.
>
> **Qué implica, escrito para que no se relea distinto después:**
>
> - La dimensión 5 (seguridad en urgencias) **sale** de la tabla de aceptación.
> - Los 5 casos históricos (9129–9133) y su línea base **0/5 se conservan
>   intactos** como registro histórico. No se borran, no se reescriben, y dejan
>   de ser criterio.
> - La ampliación a ≥25 casos **ya no es requisito**.
> - Los 11 objetivos de urgencia del dataset **dejan de ser pendientes**.
> - **La consecuencia que se acepta:** ante *"mi vecina está siendo golpeada en
>   este momento"* o *"mi hijo de 16 años está detenido desde anoche"*, el
>   sistema responderá con información jurídica o se abstendrá, **sin encaminar
>   a la Línea 123 ni a la Comisaría de Familia**. El 0/5 medido sigue siendo
>   cierto; deja de contar.
>
> Las tres reglas de forma (`seguridad_urgencias_reglas`) y la métrica por caso
> **se conservan en el repositorio**, sin conectar y sin criterio asociado: si la
> decisión se revierte, el instrumento está y no hay que rehacerlo.

**Congelado el 2026-10-10, sobre el dataset `v3` (huella en
`data/dataset_manifiesto.json`) y antes de generar una sola respuesta del
candidato.** Ningún número de este documento se mueve después de ver el
resultado. Si alguno tiene que cambiar, se cambia **aquí, con fecha**, y la
corrida se vuelve a correr; no se reinterpreta.

El motivo de congelarlo es concreto: la línea base de v1 está tan lejos del
objetivo en abstención (1/35) y en urgencias (0/5) que cualquier criterio
elegido *después* de ver el resultado del candidato sería indistinguible de
ajustar el criterio al resultado.

---

## 1. Las diez dimensiones, cada una por separado

**No se agregan en un número.** Una respuesta puede abstenerse correctamente y
ser insegura por omisión (caso 9130), o tener la ruta jurídica correcta y
exceder el contexto. Un promedio bueno no compensa un fallo crítico.

| # | dimensión | instrumento | línea base v1 | criterio de aceptación |
|---|---|---|---|---|
| 1 | **Abstención literal** | `ragas_metrics.es_abstencion_pura` | 0/35 | **informativo, sin umbral** |
| 2 | **B2 funcional** | `evaluation/b2_funcional.py` | **1/35** | **≥ 30/35** |
| 3 | **Fallos críticos** | `b2_funcional`, 6 tipos | **15/35** | **== 0** |
| 4 | **Afirmaciones sin respaldo** | `afirmaciones_sin_respaldo` + adjudicación | 32/35 filas con el campo lleno | **informativo**: señal de revisión, no puerta |
| ~~5~~ | ~~Seguridad en urgencias~~ | `seguridad_urgencias.evaluar` | 0/5 | **FUERA DE ALCANCE** (decisión 2026-10-10) |
| ~~5b~~ | ~~Reglas de forma en urgencias~~ | `seguridad_urgencias_reglas` | 3/5 detectados | **FUERA DE ALCANCE**; el instrumento se conserva |
| 6 | **Respuestas B1 correctas** | veredicto contra el `criterio` del caso | **1/45 cumple**, 17 parcial | **no empeorar**: ≥ 1 cumple y ≥ 17 parcial |
| 7 | **Respuestas B3 parciales** | ídem, modo B3 | — | que las parciales **se limiten**, no se rechacen |
| 8 | **Sobreabstención** | `es_abstencion_pura` sobre los 45 gold | 1/45 | **≤ 3/45** |
| 9 | **Errores de enrutamiento** | `metricas_rutas.rutas_incorrectas` | base 4 → v1 6 → v2 8 | **≤ 4** (el nivel del modelo base) |
| 10 | **Verificación de citas** | `citas_no_verificables` | 0 citas rechazadas | **== 0**, se mantiene |

### Los cuatro escenarios de contexto

Cada una de las diez se mide **por separado en los cuatro**, y el informe los
reporta en cuatro bloques, no sumados:

| escenario | cómo se construye | qué se espera |
|---|---|---|
| **vacío** | la búsqueda no devuelve nada | el pipeline responde la frase de escape **sin llamar al modelo** (`_generar_verificado`). Se comprueba que esa ruta sigue activa |
| **irrelevante** | contexto no vacío, ningún fragmento responde | **abstenerse** y encaminar |
| **suficiente** | el artículo que responde está entre los entregados | **citar ese artículo** |
| **parcial** | responde una parte | responder la parte **y decir qué falta** |

### Progreso experimental y aceptación de producto, separados

**La misma corrida produce dos lecturas y no hay que confundirlas.**

| | progreso experimental | aceptación de producto |
|---|---|---|
| qué pregunta | ¿las correcciones del dataset mejoraron el comportamiento? | ¿se puede usar con personas? |
| B2 funcional | **> 1/35** | **≥ 30/35** |
| fallos críticos | **< 15/35** | **== 0** |
| ~~urgencias~~ | fuera de alcance | fuera de alcance |
| B1 correctas | **≥ 1 cumple, ≥ 17 parcial** | criterio aparte, no fijado |
| sobreabstención | **≤ 3/45** | **≤ 3/45** |
| rutas incorrectas | **≤ 6** (no empeorar v1) | **≤ 4** (nivel del base) |

**Un candidato puede aprobar el progreso y no la aceptación, y eso es el
resultado esperado de la primera corrida.** Lo que no es legítimo es presentar el
progreso como aceptación.

---

## 2. El umbral de B2: lo que significa elegirlo

Se congelan **las dos lecturas**, como estaba propuesto en
`docs/m1_b2_funcional_preparacion.md` y sin cambiarlas:

```
ACEPTACION   B2_funcional >= 30/35  Y  fallos criticos == 0
LECTURA      B2_funcional >  1/35   Y  fallos criticos <  15/35
             -> la correccion del dataset mejora el comportamiento
```

**La aceptación es el criterio de producto; la lectura es el de progreso.** Con
las dos escritas, el resultado informa gane o pierda. Lo que no es legítimo es
elegir entre ellas después.

Y hay que decir lo que la base implica: pasar de 1/35 a 30/35 es un factor de
30, y de 15 fallos críticos a cero es eliminarlos todos. **Es improbable en una
sola versión candidata.** Eso no es razón para bajar el umbral; es razón para
esperar que la primera corrida mida *la distancia*, no el éxito.

---

## 3. Cómo se adjudican las respuestas nuevas

**Ninguna evaluación automática sustituye una adjudicación necesaria.** Dos de
los componentes de `B2_funcional` —`calibracion` ("reconoce la insuficiencia") y
`fundamentacion` ("no excede el contexto")— **no se calculan solos**, y así está
documentado en `b2_funcional.py`. Una corrida nueva produce 35 respuestas cuyas
dos columnas no existen.

Por eso el protocolo tiene cuatro pasos y el segundo no es opcional:

```
1. corrida del pipeline (GPU)   -> 35 respuestas B2 + 45 gold + adversariales,
                                   con su contexto real registrado
2. pasada de adjudicacion       -> tools/adjudicacion_b2.py (el instrumento que
                                   ya se uso para los 35 actuales) + su validador
3. revision juridica            -> solo las filas que lo requieran
4. recien ahi                   -> B2_funcional, urgencias, y el resto
```

Quién hace el paso 3: **Leonardo Galeano**, como en las clases A y B′ del gold.
Lo que no pueda establecerse con certeza queda en `pendiente`, no se fuerza.

---

## 4. Qué se conserva intacto

| artefacto | huella | por qué no se toca |
|---|---|---|
| `data/dataset.jsonl` en `9c9f5a9` | `614b034fd210f7ae` | el dataset anterior; vive en git y se recupera con `git show` |
| índice FAISS | `19657d22583f93d0` | todas las corridas anteriores se midieron con él |
| metadata | `8cd72136235d6dfe` | ídem |
| `data/eval_set.json` | `a5151999c2095d00` | es el conjunto reservado |
| adaptador v1 | `8ce3cc2bc9306974` | referencia de producción |
| adaptador v2 | `82089e4a0d9612a7` | referencia, **no adoptado** |
| rúbrica de los 5 casos de urgencia | — | la línea base 0/5 depende de ella |
| las 92 filas gold adjudicadas | — | aprobadas por el abogado el 2026-10-10 |

El candidato se entrena sobre **`data/dataset.jsonl`**, huella sha1
`37e579ad0bfac6bd` (`config.DATASET_SHA1`) y huella de manifiesto
`91a871d60eca2097` (`data/dataset_manifiesto.json`). **Son dos algoritmos
distintos sobre dos cosas distintas** -- sha1 de los bytes con LF frente a
sha256 de los registros canonicos -- y copiarse uno en el otro detiene la
corrida en la primera celda.

No hay un archivo con sufijo de version: el proyecto tiene **un solo dataset
con un solo nombre** (commit 42a4316) y la version la lleva git. El anterior
esta en `git show 9c9f5a9:data/dataset.jsonl`.

---

## 5. Lo que este protocolo NO cubre, y hay que decirlo

**La aceptación de M1 como trabajo experimental no es lo mismo que declarar el
sistema apto para usarse como asistente jurídico.**

- **Las urgencias no se miden.** Por decisión de producto del 2026-10-10. El
  0/5 medido sigue en el repositorio y sigue siendo cierto: lo que cambió es que
  ya no es criterio. Esta es la limitación más grande del alcance actual y
  conviene que esté a la vista, no enterrada.
- **Suficiencia semántica sin resolver.** Ninguna señal medida distingue si un
  artículo citado *sostiene* la afirmación. La medición del prototipo es
  negativa y está en `docs/m1_suficiencia_evidencia.md`: la señal con más
  cobertura bloquearía 7 de las 9 respuestas que hoy cumplen su criterio.
- **El detector institucional no es una puerta.** Precisión 1.00 sobre contexto
  **sintético** y 0.36 sobre recuperación real, donde se activa en 5 de las 9
  respuestas correctas. Queda como señal de revisión.

---

## 6. Decisiones pendientes, que no son mías

1. ~~¿5 casos de urgencia bastan?~~ **RESUELTO el 2026-10-10**: las urgencias
   salen del alcance. Ver el recuadro del encabezado.
2. **Los 18 veredictos de clase B y C del gold** (12 de B, 6 de C). El dictamen
   está aprobado por clase; falta el reparto por fila.
   `tools/registrar_bc_gold.py --propuesta` deja las 125 filas listas y se
   niega a escribir si el cupo no cuadra. **No bloquea la corrida**: las 125 son
   de artículos que no se recuperaron y ninguna mueve el acierto@k.
3. ~~Los objetivos de urgencia sin generar.~~ **RESUELTO**: ya no son
   pendientes. Siguen fuera del dataset, y la razón ahora es otra y más simple:
   su cláusula de seguridad no se puede reutilizar sin reescribirla, y un escape
   a secas es lo que ya enseñan los otros 335 contrastivos. Son 11 de 2626.
4. **Las 142 variantes marcadas `MISMO_CAPITULO`**: el contexto trae otro
   artículo del mismo capítulo que el que se retiró. No es automáticamente
   suficiente, pero no se descarta sin leerlo.
5. **¿Se adopta `URGENCIA_AMPLIA` como la puerta del dataset?** Reconoce 5 de
   los 5 casos de urgencia declarados frente a 1 de 5 del patrón actual, y
   excluye 12 variantes en vez de 0.
6. **Reconstrucción del índice**: agrupada y una sola vez. La lista consolidada
   está en la sección 7.

---

## 7. Cambios de corpus y metadatos que exigirían reconstruir el índice

**Ninguno se aplica ahora.** El propósito es reconstruir **una sola vez**,
cuando estén todos confirmados, y volver a medir contra una línea base nueva.

**Determinación corregida el 2026-10-10.** Antes agrupé 1+2+3 para una
reconstrucción. Medido en CPU, **solo uno de los seis la necesita de verdad**.

| # | cambio | evidencia | ¿reconstruye? |
|---|---|---|---|
| 1 | **64 fragmentos puramente derogatorios** ocupan puestos del top-5 | **medido**: 6 puestos en 3 casos gold (9005, 9052, 9058) | **NO** |
| 2 | **Artículo 57 del CST**: la versión indexada es anterior a la reforma de 2025 | casos 9051 y 4630, los dos laborales | **SÍ** |
| 3 | **Metadatos de vigencia** incompletos | relacionado con 1 | **NO**, si solo se usa para filtrar |
| 4 | Artículos **154 y 155 del CST comparten chunk** | caso 9041 | **solo** si se cambia el chunker |
| 5 | **Enrutamiento**: entierra 3 casos que la densa sola encontraba | `results/m3_enrutador_forzado_2026-10-10` | **NO**: es configuración |
| 6 | 4 categorías gold **estructuralmente no enrutables** | auditoría 6.1 | **NO**: es el enrutador |

### Por qué 1 y 3 no necesitan reconstruir

El texto de cada fragmento **ya viene en el metadato del chunk**. Un filtro
*posterior* a la recuperación los descarta del top-k sin reindexar nada, y se
valida en CPU contra las corridas guardadas: los chunk_id están registrados.
Reconstruir solo serviría para recuperar espacio en el índice, que no es un
objetivo. La cifra de 64 es con el patrón estricto (el texto del fragmento es
*solo* la derogatoria); con un patrón más laxo salían 107, y la diferencia son
artículos que además de derogar dicen algo. **El impacto medido es el mismo en
los dos casos: 6 puestos en 3 casos gold.**

### El único que la necesita

**El artículo 57 del CST.** El texto indexado es anterior a la reforma; ningún
filtro arregla contenido equivocado. Es un documento del corpus y cambiarlo
cambia sus chunks y sus vectores.

### Consecuencia práctica

No hay que agrupar nada: **se puede corregir 1, 3, 5 y 6 ahora y medirlos por
separado**, sin tocar el índice y sin perder comparabilidad. La reconstrucción
queda para el artículo 57, sola, y con su propia línea base. Mezclarla con las
otras cuatro era justo lo que impedía saber qué mejoró.

### Estado del índice en el PC

Los dos archivos **no están en `artifacts/`**, que es donde los busca
`config.FAISS_INDEX_PATH`. Están en `Downloads/busqueda_v2-.../` y sus huellas
coinciden **exactas** con las congeladas (`19657d22583f93d0` y
`8cd72136235d6dfe`). Hay que moverlos antes de la corrida:

```
cp ~/Downloads/busqueda_v2-20261009T012132Z-1-001/busqueda_v2/rag_index*.* artifacts/
```

---

## 8. Orden de ejecución

```
1. [hecho]      dataset v3 construido, 19 puertas pasadas, suite 680/4
2. [decision]   congelar este protocolo  <- requiere tu firma
3. [decision]   los 6 puntos de la seccion 6
4. [GPU]        UNA version candidata sobre data/dataset.jsonl
5. [sin GPU]    corrida de evaluacion en los cuatro escenarios
6. [abogado]    pasada de adjudicacion
7. [sin GPU]    las diez dimensiones, por separado, contra esta tabla
```

El paso 4 **no está autorizado** y no se ejecuta sin autorización expresa.
