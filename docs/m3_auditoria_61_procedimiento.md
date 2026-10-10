# Auditoria 6.1: procedimiento, comparabilidad y bloqueo restante

Complementa `docs/m3_cierre_gold_y_auditoria_61.md`. Solo lo nuevo.

No se reconstruyo ni reindexo. No se modifico corpus, chunker, pipeline,
dataset ni indice. No se uso GPU ni Colab. Rama `m3.5`, desde `0bf797d`, arbol
limpio al empezar.

---

## 1. Lo que corrige esta fase

Tres cosas que esta verificacion deja sin efecto, y las tres son mias.

### 1.1 "Ninguna de las 128 filas de B y C mueve el acierto@k"

**Verdadero solo para @5.** Demostrado con el mecanismo de calculo, no por
suposicion:

| clase | filas | `fue_recuperado` |
|---|---|---|
| A | 27 | **si** las 27 |
| B' | 62 | **si** las 62 |
| B | 82 | **no** las 82 |
| C | 46 | **no** las 46 |

`fue_recuperado` significa "estuvo en el top-5 de S08". Como ninguna fila de B
ni de C estuvo, ninguna puede crear ni quitar un acierto **@5**: su veredicto
no entra en el calculo.

**Pero a profundidad mayor si entran, y de forma decisiva.** Un articulo que
aparece en el puesto 6-10 no estuvo en el top-5, asi que **por construccion de
las clases** es una fila de B o de C. Comprobado caso por caso:

| configuracion | casos en puesto 6-10 | clases de sus etiquetas |
|---|---|---|
| A denso + enrutador | 9007 (9), 9009 (10), 9056 (10), 9063 (9) | **las cuatro, solo clase B** |
| C rerank + enrutador | 9032 (6), 9061 (8), 9064 (8) | A y C |
| C rerank + enrutador | 9039 (9), 9062 (8) | solo clase B |

En la configuracion de produccion, **4 de los 25 aciertos@10 dependen
enteramente de filas sin registro individual**. Asi que el acierto@10 tampoco
se puede declarar definitivo, y 6.1 -- que mide hasta 100 -- dependera de
cerrar B y C mas de lo que yo habia dicho.

### 1.2 "El piso de 0.81 casi no discrimina"

**Cierto por debajo de 0.81 y falso justo encima.** El artefacto trae un
barrido de pisos que no habiamos leido:

| piso | gold @5 (denso+enrutador) | casos gold sin contexto |
|---|---|---|
| sin piso · 0.78 · 0.79 · 0.80 · **0.81** | **21/45** | 0/45 |
| **0.82** | **17/45** | **4/45** |
| 0.83 | 12/45 | 12/45 |

El piso es una funcion escalon con el salto **entre 0.81 y 0.82**. Produccion
usa `RETRIEVAL_MIN_SCORE = 0.81`, que esta **inmediatamente debajo del
acantilado**: un paso mas y se pierde el 19 % de los aciertos y cuatro casos
quedan sin contexto ninguno. Dije que el piso era "casi inoperante"; lo es
hacia abajo, y subirlo no es inocuo.

### 1.3 El manifiesto de `busqueda_v2` no describe lo que se midio

Dice `retrieval_min_score: 0.82`. Pero `benchmark_busqueda.py:_indice` llama a
`retrieve(q, store, top_k=10, min_score=None, ...)`: el bloque
`configuraciones` se midio **sin piso** y a **profundidad 10**.

El manifiesto registra la **constante del commit**, no el parametro efectivo de
esa medicion. Es un defecto de trazabilidad del mismo tipo que H14 -- el
enrutador sin registrar -- y me llevo a declarar una incomparabilidad que no
existia: el `0.82` del manifiesto no se aplico.

---

## 2. Comparabilidad de las cuatro configuraciones

### Lo que si es comparable

Las cuatro configuraciones de `results/busqueda_v2/` **son comparables entre
si**: mismo indice (`hash_indice 19657d22583f93d0`), mismo corpus, mismo eval
set, `min_score=None`, `top_k=10` y el mismo gold. La unica variable es la
configuracion de recuperacion.

Y el **21/45** de `A denso+enrutador` coincide con el 21/45 que dan los
registros de S08 con el gold original, pese a que S08 corrio con piso 0.81.
Coinciden porque el piso 0.81 es inerte (1.2).

### Lo que NO se puede recalcular, y por que

**No se puede recalcular el acierto@5 de cada configuracion con el gold
aprobado.** El artefacto guarda `puesto_por_caso` -- el puesto -- pero
**no que articulo se encontro**. `benchmark_busqueda.acierta()` devuelve un
booleano y se descarta cual de las etiquetas produjo el acierto.

Sin ese dato no se puede saber si el acierto de un caso venia de una etiqueta
hoy anulada (9040, 9051, 9064, 9069) ni si las tres omisiones añadidas entran
dentro del top-5. **Recalcularlo exige volver a consultar el indice**, que es
justamente 6.1.

### Las cuatro metricas, separadas

| metrica | que mide | quien la produce | limitacion |
|---|---|---|---|
| Acierto mecanico por articulo | si el articulo gold esta en el top-k | codigo, sin juez | depende del gold, que estaba mal en 7 de 217 filas |
| Puesto en el ranking | donde cae el articulo gold | codigo, sin juez | profundidad 10; no dice **que** articulo fue |
| `context_recall` RAGAS | cuanto del contexto necesario llego | **juez Groq** | 42 comparaciones pareadas inconsistentes sin explicar en M2 |
| Juicios del evaluador Groq | calidad de la respuesta | **juez Groq** | misma reserva, y mide generacion, no recuperacion |

**No se elige configuracion ganadora.** La evidencia que hay:

| configuracion | acierto@5 (sin piso, @10) | `context_recall` (piso 0.81, top_k 5) |
|---|---|---|
| A denso | 0.333 | 0.394 |
| A denso + enrutador | 0.467 | — |
| B hybrid + enrutador | 0.489 | 0.382 |
| C rerank + enrutador | **0.533** | 0.352 |

Las dos columnas **no son la misma corrida** -- distinto piso, distinto top_k y
una pasa por un juez -- asi que la contradiccion no esta resuelta, solo mejor
descrita. Decidir sobre `USE_RERANK` exige medir las dos cosas en la misma
corrida, con el gold aprobado, y mirar tambien la fidelidad de la respuesta.

---

## 3. El procedimiento de 6.1, listo y sin ejecutar

`tools/auditoria_61.py`. Consulta el indice, no lo modifica. CPU.

Que hace, en orden:

1. **Registra las versiones** de python, torch, faiss-cpu, transformers, numpy
   y rank-bm25.
2. **Verifica cuatro huellas** contra las del indice evaluado:
   `hash_indice 19657d22583f93d0`, `hash_metadata_indice 8cd72136235d6dfe`,
   `hash_corpus 1c552822959e2932`, `hash_eval_set a5151999c2095d00`, y que el
   indice tenga **11 975** chunks. **Si alguna falla, no mide nada.**
3. **Arma el gold aprobado** leyendo los veredictos del CSV: quita las 5
   `no_responde` registradas, añade las 3 omisiones, y **conserva tal cual** las
   etiquetas de las 128 filas sin registro individual. No edita
   `eval_set_articulos.json`.
4. **Consulta con `top_k=100` y `min_score=None`**, con el enrutador encendido.
   Sin piso a proposito: aqui se mide donde cae el articulo, no que fragmentos
   sobrevivirian al filtro de produccion.
5. **Registra por caso**: el puesto del primer articulo gold, **si ese acierto
   llego solo por un chunk de continuacion** (sin encabezado, el hallazgo del
   anexo de chunking) y las normas presentes en el top-100.
6. **Escribe en un directorio nuevo** con `mkdir(exist_ok=False)`: no puede
   sobrescribir un resultado historico ni por accidente.

Agrega acierto@5, @10, @30, @100, los ausentes del top-100 y los aciertos que
solo llegan por continuacion, todos con denominador explicito.

### Donde se detiene hoy, ejecutado de verdad

```
$ python -m tools.auditoria_61 --verificar
dependencias:
  python         3.13.5
  torch          ausente
  faiss-cpu      ausente
  ...
gold aprobado: {'quitadas_no_responde': 5, 'anadidas_omision': 3,
                'sin_registro_individual': 128}

3 problemas: NO se mide nada
  - no esta el indice FAISS en .../artifacts/rag_index.faiss
  - no esta la metadata en .../artifacts/rag_index_metadata.jsonl
  - hash_corpus 1bd16dcc1baccc6b != 1c552822959e2932 esperado (CRLF, ver H13)
```

**Dos de los tres bloqueos se resuelven ya aqui:**

```
$ python -m tools.auditoria_61 --verificar \
      --metadata results/m3_s08_2026-10-09/rag_index_metadata.jsonl
2 problemas: NO se mide nada
  - no esta el indice FAISS en .../artifacts/rag_index.faiss
  - hash_corpus 1bd16dcc1baccc6b != ... (CRLF, ver H13)
```

| bloqueo | estado |
|---|---|
| Metadata del indice | **resuelto**: esta en `results/m3_s08_2026-10-09/`, huella verificada |
| `hash_corpus` | **falso positivo conocido**: es el CRLF de Windows (H13). En Colab, que clona con LF, coincide |
| **`rag_index.faiss`** | **bloqueo real**: 48 MB, solo en Drive |
| `torch`, `faiss-cpu` | **bloqueo real**: no instalados aqui |

### Los comandos exactos, para Colab CPU

```bash
# 1. entorno CPU. No hace falta GPU: son 45 consultas con e5-base.
pip install faiss-cpu
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 2. el repo en el commit de esta fase
git clone <repo> && cd Amparo && git checkout 0bf797d

# 3. Drive montado, y la metadata al lado del indice
#    (o se pasan las dos rutas con --indice y --metadata)
mkdir -p artifacts
cp "/content/drive/MyDrive/Colab Notebooks/Amparo/rag_index.faiss" artifacts/
cp "/content/drive/MyDrive/Colab Notebooks/Amparo/rag_index_metadata.jsonl" artifacts/

# 4. PRIMERO verificar. Si una huella no coincide, detenerse y reportar.
python -m tools.auditoria_61 --verificar

# 5. solo si el paso 4 dice "Huellas verificadas"
python -m tools.auditoria_61 --salida results/m3_61_2026-10-10
```

Si el paso 4 dice que `hash_indice` no coincide, **el archivo de Drive no es el
indice que se evaluo** y hay que parar: medir sobre otro indice daria un numero
incomparable con todo lo anterior. Esa es la unica forma de verificar
`hash_indice`, que hasta ahora solo esta **declarado** en los manifiestos.

---

## 4. La tabla de los 11 casos, con lo que ya se sabe

Los 11 que no aparecen en el top-10 de ninguna configuracion. Las dos columnas
de puesto **quedan vacias hasta ejecutar 6.1**: no se inventan.

| caso | consulta | gold que no llega | puesto en top-100 | configs donde aparece | estado de sus chunks | causa | confianza |
|---|---|---|---|---|---|---|---|
| 9004 | EPS, 3 meses esperando cirugia | Ley 1751 arts. 2 y 6 | **pendiente 6.1** | ninguna (@10) | art. 6 **partido en 5** | fragmentacion, por confirmar | media |
| 9010 | ¿algo antes de demandar al ex-socio? | Ley 2220 arts. 67, 68, 70, 71 | pendiente | ninguna | CGP art. 90 **partido en 3** | sin determinar | baja |
| 9035 | no me devuelve el deposito | Ley 820 art. 16 | pendiente | ninguna | chunk propio, con encabezado | **ranking** | media |
| 9038 | contratista con horario y jefe | CST arts. 23 y 24 | pendiente | ninguna | art. 23 **partido en 2** | fragmentacion o ranking | baja |
| 9042 | fotomulta de hace casi un año | Ley 769 art. 161 | pendiente | ninguna | — | el **enrutador falla**: predice Arriendo y Embargos | media |
| 9048 | me estafaron en una compra | C.P. arts. 246, 269-J | pendiente | ninguna | — | sin determinar | baja |
| 9049 | ¿registro en Camara de Comercio? | C.Co arts. 10, 13, 19, 26, 28 | pendiente | ninguna | — | el **enrutador falla**: predice Propiedad intelectual | media |
| 9050 | cheque devuelto sin fondos | C.Co arts. 712, 730, 731, 784, 793 | pendiente | ninguna | art. 784 **partido en 2** | el enrutador **no predice categoria** | media |
| 9057 | codeudor embargado sin aviso | CGP arts. 133, 290, 291, 292 | pendiente | ninguna | arts. 133, 291, 292 **partidos en 2, 5 y 2** | fragmentacion, por confirmar | media |
| 9058 | expulsion del colegio | Ley 1620 art. 21, Ley 115 arts. 87, 96, 132 | pendiente | ninguna | art. 21 **partido en 2**; y **4 de 5 fragmentos recuperados eran "Derogado"** | **demostrada**: derogatorias ocupando el top-5 | **alta** |
| 9066 | antejardin invadido | Ley 388 arts. 99, 103; Ley 1801 arts. 135, 140 | pendiente | ninguna | arts. 135 y 140 **partidos en 7 y 6** -- los peores del indice | fragmentacion | media-alta |

Lo que ya se puede afirmar sin 6.1: **9058 tiene causa demostrada** (las
derogatorias), **9042 y 9049 fallan por el enrutador** y en **9050** el
enrutador no predice categoria. De los 11, al menos 4 no se arreglan tocando el
chunker.

### El umbral de los seis, reconsiderado

El informe anterior fijo: *"si en 6 o mas de los 11 el articulo aparece entre
los 100 primeros, el diagnostico es ranking y el chunker no se toca"*. Hay que
matizarlo antes de usarlo, y es mejor hacerlo ahora que despues de ver el
resultado:

1. **No es sustituto del analisis caso por caso.** Los 11 ya tienen tres causas
   distintas identificadas, y un umbral agregado las aplanaria.
2. **Los 4 de enrutador y derogatorias deben salir del denominador.** Si 9058,
   9042, 9049 y 9050 fallan por causas ya identificadas, el umbral debe
   aplicarse a los **7 restantes**, no a los 11.
3. **La regla revisada**: de los 7 sin causa identificada, si **4 o mas** tienen
   el articulo entre los 100 primeros, el diagnostico dominante es ranking. Si
   **3 o mas** no aparecen en el top-100, hay representacion que corregir.
4. Los dos criterios pueden cumplirse a la vez, y eso seria un resultado
   legitimo: **las dos cosas**.

---

## 5. Correcciones candidatas

### Demostradas

| | evidencia | mueve el indice |
|---|---|---|
| Excluir las derogatorias puras | 107 chunks, control en cero; en 9058 cuatro de cinco fragmentos | si |
| 4 aciertos falsos y 3 omisiones en el gold | clases A y B' registradas | no |
| El verificador dejaba pasar la ley nombrada ausente | corregido en `9a0e6bb` | no |
| `huella_directorio` sin normalizar CRLF | da un falso positivo en cada verificacion desde Windows, incluido el de 6.1 | no |
| El manifiesto no registra el enrutador ni el piso efectivo | H14, y 1.3 de este informe | no |
| El piso 0.81 esta al borde del acantilado | 21/45 a 17/45 entre 0.81 y 0.82 | no |

### Hipotesis

| | que falta para decidir |
|---|---|
| Encabezado en los chunks de continuacion | 6.1: si los 7 casos sin causa tienen el articulo en el top-100 |
| `USE_RERANK = True` | una corrida con el gold aprobado, el mismo piso y la fidelidad medida a la vez |
| Subir `TOP_K` | mide 4-5 casos ganados contra el ruido añadido en el prompt |
| `MAX_TOKENS_PER_CHUNK` mayor | nadie ha medido que pasaria |

### Recomendacion

**Conseguir el `.faiss` y correr 6.1 es lo unico que desbloquea la decision de
reconstruccion.** Todo lo demas de P0 ya esta hecho o es independiente.

En paralelo, y sin tocar el indice: enumerar fila por fila las clases B y C --
que ahora sabemos que **determinan el acierto@10**, no solo lo acompañan --,
arreglar `huella_directorio` antes de la siguiente verificacion de huellas, y
registrar en el manifiesto el enrutador y el piso efectivo.

**No se modifico ningun artefacto del corpus, chunker, pipeline ni indice.**

---

## Archivos

| archivo | estado |
|---|---|
| `tools/auditoria_61.py` | nuevo. Ejecutado solo en modo `--verificar` |
| `docs/m3_auditoria_61_procedimiento.md` | nuevo (este informe) |

Sin tocar: corpus, chunker, pipeline, dataset, indice, notebooks, resultados
historicos, `data/eval_set_articulos.json` y
`docs/m3_articulos_gold_validacion.csv` (sigue en 89/217).
