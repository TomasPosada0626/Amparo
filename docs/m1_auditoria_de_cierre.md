# Auditoria formal de cierre de M1

Solo lectura: no se modifico ningun archivo, no se entreno, no se uso GPU ni
credito externo.

| | |
|---|---|
| HEAD | **`0be2a89e8aec3a2c1209f02b134bb6b1fab58e12`** |
| Rama | `m3.5` |
| `git status` | **limpio** |
| Commits locales sin empujar | 17 |
| Suite **ejecutada en este HEAD** | **658 passed, 4 skipped** |

La suite se corrio ahora, no se infirio de corridas anteriores.

---

## Dictamen por punto

### 1. Fuentes de `data/dataset_src_v2/` — **APROBADO**

| | |
|---|---|
| Archivos | **27 de 27** categorias objetivo, ninguna falta y ninguna sobra |
| Conciliacion prejudicial | **presente**, 10 268 bytes, con ejemplos B1 que citan `LEY-2220-2022:67` y `:68` |
| Artefacto | `data/dataset_src_v2/*.md`; comprobado contra `corpus.CATEGORIAS_OBJETIVO` |

**Revision juridica documentada: SIN EVIDENCIA.** No hay ningun documento que
registre una revision juridica de **estas 27 fuentes**. Lo que si esta
documentado y aprobado por Leonardo Galeano es otra cosa: las etiquetas B2 de
los 35 casos (`docs/m1_b2_*`) y las clases A y B' del gold del eval set
(`docs/m3_articulos_gold_*`). Las respuestas de referencia de las 755 fuentes
de v2 **no tienen revision juridica registrada**.

### 2. Muestra 4010 — **APROBADO (corregida)**

Verificada una por una, no por inferencia de que la suite pase:

```
revisar(4010) -> SIN PROBLEMAS
modo B1 · fuentes ['LEY-599-2000:220', 'LEY-599-2000:222']
contexto_origen busqueda+oraculo · 5 fragmentos
```

Y el analisis completo de las 755: **0 problemas, 0 repetidos, 0 fuga del eval
set**. Artefacto: `tools/dataset_v2_quality.analizar`.

### 3. `data/dataset_v2.jsonl` — **no existe**

No es ni piloto ni completo: **el archivo no esta**. La consolidacion lo
sustituyo por un unico `data/dataset.jsonl`.

| | |
|---|---|
| Registros | **2 709** |
| Huella | `db0b6e65126cab25` = `config.DATASET_SHA1` |
| Por origen | v1 **1 536** · v2 **755** · contrastivo **418** |
| v2 por modo | B1 **391** · B3 **101** · B2 **263** |
| Con las contrastivas | B2 total **681** |
| Categorias en v2 | **27** |

**Es el completo, no un piloto**: las 755 que construye `dataset_v2.construir`
ahora coinciden exactamente con las 755 de origen `v2` en el combinado.

### 4. Puertas de calidad y dataset combinado — **APROBADO**

| | |
|---|---|
| `tests/test_dataset_v2.py` | **15 passed**, ejecutado ahora |
| `analizar(755)` | 0 problemas · 0 repetidos · 0 fuga |
| Dataset combinado generado | **si**, `data/dataset.jsonl`, huella verificada |

Incluye las puertas que importan: que cada B1/B3 tenga en su contexto el
articulo que cita, que ningun ejemplo quede con contexto vacio, que B2 empiece
con la frase de escape y no cite, que B3 diga lo que falta, y que ninguna
pregunta del eval set este en el train de v2.

### 5. El notebook — **APROBADO**

`colab/m1_finetune.ipynb` carga `data/dataset.jsonl`, verifica su huella con
`_cfg.verificar_dataset`, y **no conserva el hardcode de 1536**. El numero
aparece, pero como **asercion de composicion**:

```python
assert _origenes == {'v1': 1536, 'v2': 755, 'contrastivo': 418}
assert all(r['origen'] != 'contrastivo' for r in val_records)
```

Es lo contrario de un hardcode del tamaño de entrenamiento: una guarda que
falla si la mezcla cambia. El split **viene resuelto en el archivo y no se
recalcula**. `ADAPTADOR = 'v3'`.

### 6. Corrida final con manifiesto y hashes — **APROBADO, con un defecto de trazabilidad**

`results/m1_v2_2026-10-09/`: manifiesto, hiperparametros, historial de
entrenamiento, resultados base y afinados, metricas por registro y por
categoria, y scorecard.

| | |
|---|---|
| `n_train` + `n_val` | 2 375 + 334 = **2 709**, el combinado completo |
| Adaptador | `amparo-lora-adapter-v2`, `hash_adaptador 82089e4a0d9612a7` |
| Commit | `de7c4cc` · A100 · QLoRA 4-bit, 3 epocas, seed 42 |
| Hiperparametros | **identicos a v1**, verificado clave por clave: 0 diferencias |

**El defecto:** el manifiesto registra
`hash_dataset_entrenamiento = 68974d0b31a1e26c` y
`config.huella_dataset()` da `db0b6e65126cab25`. Parece un desajuste y **no lo
es**: son dos funciones distintas sobre el mismo contenido.

```
sha1  de bytes LF  -> db0b6e65126cab25   (config.huella_dataset)
sha256 de bytes LF -> 68974d0b31a1e26c   (el del manifiesto)
```

Comprobado. La corrida **si entreno con este dataset**; solo cambio el nombre
del archivo (`dataset_m1_v3.jsonl` -> `dataset.jsonl`) en la consolidacion.
Pero **dos funciones de hash para el mismo artefacto hacen que una verificacion
honesta parezca un fallo**. Es el tercer defecto de portabilidad de huellas de
este proyecto, despues del CRLF y del orden de `Path` en Windows.

### 7. Abstencion, B1 y B3 — **FALLIDO en lo central, con un matiz que corrige mi propio diagnostico**

**Sobre la validacion de M1 (334 registros), adaptador v1 y v2:**

| modo | n | abstencion pura | lectura |
|---|---|---|---|
| sin contexto | 231 | **0** | — |
| B1 | 55 | **0** | correcto: no debe abstenerse |
| B3 | 13 | **0** | correcto |
| **B2** | **35** | **0** | **FALLIDO: deberia abstenerse** |

**Sobre el eval set via S10 (75 casos, adaptador v1):**

| conjunto | `es_valvula_de_escape` | `es_abstencion_pura` |
|---|---|---|
| gold (45) | 27 (60 %) | **8 (18 %)** |
| adversarial (30) | 24 (80 %) | **20 (67 %)** |

**Correccion a lo que afirme en el informe de auditoria integral.** Dije que
"la abstencion no funciona, 0/35 en v1 y en v2". Es exacto para B2 y **demasiado
amplio como afirmacion general**: el modelo **si produce la frase de
abstencion**, en 20 de 30 adversariales con la definicion estricta.

El diagnostico preciso es otro: **el modelo abstiene cuando la PREGUNTA señala
que no se puede responder, y no abstiene cuando la pregunta parece respondible
pero el CONTEXTO no sirve.**

Y descarte la explicacion mas plausible: **no es el prompt**. El `system` de la
validacion de M1 y el del pipeline RAG son **identicos**, 1 350 caracteres,
comparados byte a byte.

**Por subtipo adversarial (abstencion pura, adaptador v1):**

| subtipo | n | abstiene |
|---|---|---|
| cita exacta requerida | 5 | 4 |
| fuera de jurisdiccion | 5 | 4 |
| solicitud de conducta ilegitima | 5 | 4 |
| garantia de resultado | 5 | 3 |
| pregunta ambigua | 5 | 3 |
| **urgencia fuera de alcance** | 5 | **2** |

`prudencia_en_adversariales = 1.0` (30/30): incluso cuando no emite la frase,
las 30 son prudentes. **Urgencia fuera de alcance es la mas debil**, y para un
asistente dirigido a personas sin formacion juridica es la categoria de mayor
riesgo.

**B1 y B3 — APROBADO:** B1 citan 54/55, B3 citan **13/13** (v1: 12/13).

### 8. Errores juridicos, citas, rutas, entidades — **mezcla**

| propiedad | base | v1 | v2 | estado |
|---|---|---|---|---|
| Cita de memoria (231 sin contexto) | 29/231 (12.6 %) | **0/231** | **0/231** | **APROBADO** |
| Cita sin respaldo (103 con contexto) | 2/103 | 3/103 | 3/103 | aprobado, sin mejora |
| Entidades inventadas | 11.4 % | 3.0 % | **2.7 %** | **APROBADO** |
| Integridad (idioma / formato) | 4/334 | 0/334 | **0/334** | **APROBADO** |
| Truncamiento | — | sin registrar | `motivo_fin = {termino: 334}` | **APROBADO** |
| Nombra ruta legal | 94.9 % | 96.7 % | 95.2 % | **regresion leve en v2** |
| **Rutas incorrectas** | **5/334** | **6/334** | **9/334** | **FALLIDO en v2** |
| Abstenciones indebidas (B1+B3) | — | **0/68** | **0/68** | **APROBADO** |

**Las rutas incorrectas no estaban medidas.** `tools/evaluation/rutas.py` tiene
`rutas_incorrectas()`, pero `metricas_por_registro.csv` solo guarda
`nombra_mecanismo`, `cita_no_verificable`, `entidad_inventada` y `palabras`.
Las calcule ahora sobre las respuestas guardadas: base 5, v1 6, **v2 9**.
Ejemplos en v2: `querella_ante_juez`, `conciliacion_familiar_fuera_de_familia`,
`demanda_ante_autoridad_no_judicial`.

**Con la cautela que corresponde:** 6 frente a 9 son tres casos sobre 334 y
puede ser ruido. Pero apunta en la **misma direccion** que el `ruta legal
96.7 -> 95.2 %` del scorecard, que es un indicador independiente. Dos señales
coincidentes.

**Errores juridicos de fondo: SIN EVIDENCIA.** No hay revision juridica de las
334 respuestas de validacion. Lo que existe es la de los 35 casos B2, aprobada
por Leonardo, y de ahi salieron **cinco errores de atribucion con el fragmento
correcto delante** (2917, 3328, 3729, 4226, 3327). Eso no se detecta con
ninguna metrica mecanica y no esta medido en el resto.

### 9. ¿Cierra M1? — **NO con el criterio actual**

---

## El bloqueo, y es uno solo

**B2 = 0/35 sigue sin resolverse, y es el objetivo declarado de M1.**

Todo lo demas esta aprobado o es menor. El scorecard de v2 lo dice sin
adornos: *"La hipotesis no se confirma. B2 sigue en 0 de 35"*, y su veredicto
es **no adoptar v2**: v1 sigue siendo el baseline y
`amparo-lora-adapter` no se toca.

Lo que la evidencia nueva de esta auditoria añade es que **el bloqueo esta mal
planteado**, y eso cambia qué hay que hacer:

1. El modelo **si sabe abstenerse** (20/30 adversariales estricto). No es una
   capacidad ausente.
2. Lo que no hace es abstenerse ante **contexto inutil con pregunta
   respondible**, que es precisamente el caso B2.
3. **No es el prompt**: es identico en los dos arneses.
4. Y las 755 respuestas de referencia de v2 **no tienen revision juridica
   registrada**, asi que el target que se le pide imitar no esta validado.

## Las pruebas minimas que faltan

En orden de coste, y ninguna necesita GPU salvo la ultima:

| # | prueba | coste | resuelve |
|---|---|---|---|
| 1 | **Decidir si la frase exacta es requisito de producto o artefacto de la metrica.** Si lo que importa es no afirmar sin fundamento, *"No te puedo decir cuanto cuesta porque depende de la entidad"* cumple, y entonces la metrica debe medir eso y no la cadena literal | cero | puede cerrar el bloqueo sin tocar el modelo |
| 2 | **Medir B2 a traves del pipeline RAG**, no del arnes de M1. El modelo emite la frase en S10 y no en la validacion de M1 con el mismo prompt: hay que saber si el `0/35` mide el modelo o el arnes | cero GPU, solo inferencia | decide si el fallo es real |
| 3 | **Registrar `rutas_incorrectas` y `fuera_de_contexto`** en `metricas_por_registro.csv` | cero | cierra el punto 8, hoy medido a mano |
| 4 | **Unificar la funcion de huella del dataset** (sha1-LF frente a sha256-LF) | cero | cierra el defecto del punto 6 |
| 5 | **Revision juridica de una muestra de las 755 respuestas de referencia de v2** | horas de abogado | cierra el "sin evidencia" del punto 1 |
| 6 | **Reforzar urgencia fuera de alcance** (2/5) antes de exponer el sistema | dataset + GPU | el riesgo mas alto para el usuario final |

## Lo que NO bloquea

- Las 9 rutas incorrectas de v2: **v2 no se adopta**, asi que no llega a
  produccion. Pero si alguna vez se adopta, esto es condicion previa.
- El defecto de las dos funciones de hash: no invalida la corrida, que se
  verifico.
- `escape_por_codigo` sin dispararse nunca: es una red de seguridad para
  contexto vacio, y el contexto vacio no ocurre porque la busqueda siempre
  devuelve algo. Esta bien que no se dispare.

## Veredicto

**M1 no se cierra todavia**, y el unico bloqueo estricto es B2. Pero antes de
gastar otra corrida de GPU hay que hacer las pruebas **1 y 2**, que cuestan
cero: una decide si el criterio esta bien definido y la otra si la medicion
mide lo que dice medir. Hay evidencia concreta de que **el criterio actual
puede estar midiendo el arnes y no el modelo**, y reentrenar sin resolver eso
es repetir la corrida de v2 con otro dataset.
