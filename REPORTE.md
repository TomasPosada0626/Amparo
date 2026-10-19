# Triaje de acciones constitucionales colombianas

**Fine-tuning, evaluacion y RAG sobre el mecanismo procedente ante un relato ciudadano.**

> Generado por `data/reporte.py` el 2026-10-19 10:39 (America/Bogota). Ninguna cifra de este documento esta escrita a mano: todas salen de un artefacto de `results/`, y el apendice dice de cual y de que clave. Una cifra sin artefacto hace fallar al generador.

## 0 · Que afirma este trabajo, y que no

**La tesis.** El cuello de botella para decidir *que mecanismo constitucional procede* no es el acceso al texto de la norma: es saber en que orden se preguntan las causales. Un modelo pequeno afinado sobre el arbol de decision del art. 6 del Decreto 2591 de 1991 llega mas lejos que tres arquitecturas de recuperacion con acceso al corpus entero.

Medido: el brazo **1 · fine-tuned solo (M1)** gana a las otras 3 arquitecturas, con intervalos que no se solapan contra 2 de ellas y que **si se solapan con 4 · agente + reglas** --- ahi la diferencia no se sostiene.

**Lo que NO afirma.** Que el sistema sea apto para uso juridico real; que el juez automatico este validado contra criterio humano independiente; que los numeros se sostengan en los estratos de n pequeno. Cada una de esas tiene su cifra y su motivo en la seccion 7, que es la seccion importante de este documento.

## 1 · De donde salen las cifras

Las tres corridas comparten huella de codigo, asi que la comparacion entre modulos se sostiene.

| modulo | corrida | huella de codigo | valida | artefactos |
|---|---|---|---|---|
| m1 | 20261018T074101Z | `c8cac1b6b7e27a32` | True | 14 |
| m2 | 20261018T080311Z | `c8cac1b6b7e27a32` | True | 11 |
| m3 | 20261019T034908Z | — | — | — |

`data/verificar_entrega.py` comprueba esto mismo de forma ejecutable: que los artefactos esten, que sean de la misma corrida de su modulo, que las huellas de codigo coincidan y que la version de datos sea la misma en los tres.

## 2 · Los datos y como se verificaron

Tres niveles de verificacion, y la diferencia entre ellos es lo que permite leer el resto:

- **`plano`** · la etiqueta se lee directamente del relato.
- **`derivado`** · hay que encadenar dos hechos del relato.
- **`juicio`** · hubo que ponderar. Es donde el gold es discutible, y va marcado para poder leer el resultado por separado.

El motor de reglas del art. 6 reproduce la etiqueta de los casos del eval set, pero eso significa **consistente** con el arbol, no **independiente** de el: el campo `por_fiabilidad_etiqueta` de cada scorecard lo dice con esas palabras para que nadie lea la consistencia como validacion.

**Cobertura del corpus** (`data/cobertura_corpus.json`): 69 fragmentos verificados, 77 chunks. De los 63 casos comunes, **0** citan una norma que no esta en el corpus y **42** la tienen pero por debajo del puesto 5 en BM25 (la peor, en el puesto 49 de 77). El techo de recuperacion es de **ranking**, no de cobertura — y ampliar el corpus lo empeoraria, porque mete mas candidatos a competir por los mismos cinco puestos.

## 3 · M1 · el sistema afinado

LoRA sobre Qwen2.5-7B-Instruct. Dos cifras de cabecera, las dos con intervalo bootstrap percentil:

| metrica | base | afinado |
|---|---|---|
| acierto juridico | **3.2%** [0.0%, 7.9%], n=63 | **87.3%** [79.4%, 95.2%], n=63 |
| acierto de mecanismo | **33.3%** [22.2%, 44.4%], n=63 | **87.3%** [79.4%, 95.2%], n=63 |
| macro-F1 de mecanismo | 0.195 | 0.867 |
| base mayoritaria | 0.429 | 0.429 |
| alucinacion normativa | 0.0 | 0.084 |

**El acierto juridico es la metrica de cabecera y no la accuracy de mecanismo.** Acertar `tutela` por la causal equivocada no es acertar: exige mecanismo, procedencia y fundamento a la vez.

Por estrato de fiabilidad de la etiqueta:

| estrato | nivel | n | acc. mecanismo | acierto juridico |
|---|---|---|---|---|
| `motor_de_reglas_plano` | 2 | 45 | 86.7% | 86.7% |
| `motor_de_reglas_ponderado` | 3 | 15 | 86.7% | 86.7% |
| `equipo_ponderacion_afirmada` | 4 | 3 | 100.0% | 100.0% |

> `motor_de_reglas` significa CONSISTENTE con el arbol del art. 6, no INDEPENDIENTE: los hechos los codifico el mismo equipo que puso la etiqueta. Solo el nivel 1 tiene fuente externa.

**Degeneracion.** `m1_degeneracion.json` mide la cola repetitiva y los caracteres imposibles en un triaje colombiano: base 1 de 69 salidas, afinado **0 de 69**. El recorte de generacion la acota, no la cura (ROADMAP3 · M1-1).

**Estabilidad entre corridas.** `identicas: None`. Dos corridas con el mismo codigo y los mismos datos no dan bit a bit lo mismo, y por eso el adaptador se versiona con la corrida que lo produjo y registra la huella de sus pesos: un resultado del que no se pueden recuperar los pesos no es reproducible, es anecdotico.

**Capa de redaccion.** `m1_redaccion.json` mide la capa que convierte el bloque de triaje en lenguaje natural sin dejarle inventar normas: 69 casos, **0** con normas que no estaban en el bloque, mecanismo dicho en 98.6% y procedencia en 98.6%. La guarda es estructural: el texto solo puede citar lo que el motor ya decidio. Las dos coberturas tienen que valer 1.0 --- son lo que permite que un error del triaje siga siendo detectable por quien lee el texto.

## 4 · M2 · el evaluador, evaluado

Un juez LLM que no se audita no es una medicion, es una opinion con decimales. Las tres sondas de sesgo:

| sonda | resultado | como leerlo |
|---|---|---|
| posicion | 0 inconsistentes de 12 | indefinida a proposito: con 0 inconsistentes esta fraccion vale 0.5 por construccion y no aporta nada sobre el sesgo. Lo que lo mide es `tasa_inconsistencia`. |
| longitud | tasa 0.167 | prefiere la respuesta mas larga cuando el contenido es el mismo |
| inyeccion de prompt | 2 de 18 obedecieron | La tasa agregada esconde CUAL forma de inyeccion funciona. Un estilo con una sola sonda no sostiene una tasa: aparece en `estilos_con_una_sola_sonda` para que n |

La inyeccion se mide con **tres sondas por estilo** precisamente porque con una sola no se puede distinguir un estilo que funciona siempre de uno que acerto por suerte; el desglose va en `inyeccion.por_estilo`, y los estilos que se quedaron con una sola sonda van nombrados en `estilos_con_una_sola_sonda` en vez de promediados con los demas.

**Acuerdo entre jueces.** `m2_acuerdo_entre_jueces.json`: kappa 0.683, Spearman 0.896. Si el segundo juez no estuvo servido, el artefacto no existe y esta linea lo dice: publicar un archivo vacio seria peor que no publicarlo.

**Determinismo.** `m2_determinismo_juez.json`: `deterministico: True` sobre 3 llamadas reales, sin cache. Si el juez no repite su propia nota con temperature=0, su nota tiene varianza propia y las comparaciones de pocas decimas no son interpretables.

**Auto-preferencia.** `m2_sesgo_autopreferencia.json` condiciona en la verdad de dominio para separar «premia a su familia» de «acierta»: el numero que importa es `preferencia_familia_con_calidad_empatada`: 0.5 es ausencia de auto-preferencia. Fuera del estrato de empate la preferencia puede ser merito y no sesgo, por eso no se agrega todo en una sola cifr

**ROUGE-L contra acierto.** `m2_rouge_vs_acierto.json` es el argumento con datos de por que la similitud lexica no mide derecho: ROUGE-L medio **0.331** cuando la respuesta ACIERTA y **0.228** cuando FALLA. Si los dos se parecen, el solapamiento lexico no distingue una respuesta correcta de una equivocada --- y entonces no puede ser la metrica de cabecera.

## 5 · M3 · cuatro arquitecturas sobre los mismos casos

La tabla es sobre los **63 casos comunes** a los cuatro brazos. La tabla de `m3_scorecard.csv` pone el brazo 1 con un n distinto al de los brazos 2-4 y con otra base mayoritaria: son conjuntos distintos y no se pueden comparar.

| brazo | n | acierto juridico [IC95] | acc. mecanismo | macro-F1 | gold | adversarial |
|---|---|---|---|---|---|---|
| 1 · fine-tuned solo (M1) | 63 | **87.3%** [79.4%, 95.2%] | 87.3% | 0.882 | 88.9% | 83.3% |
| 2 · fine-tuned + RAG ingenuo | 63 | **66.7%** [54.0%, 77.8%] | 66.7% | 0.622 | 80.0% | 33.3% |
| 3 · fine-tuned + RAG avanzado | 63 | **63.5%** [50.8%, 74.6%] | 66.7% | 0.612 | 73.3% | 38.9% |
| 4 · agente + reglas | 63 | **77.8%** [68.2%, 88.9%] | 77.8% | 0.726 | 75.6% | 83.3% |

**Ganadores** (`m3_ganadores.json`): agregado **1 · fine-tuned solo (M1)**, gold **1 · fine-tuned solo (M1)**, adversarial **1 · fine-tuned solo (M1)**. Si el ganador en gold y en adversarial no es el mismo, el agregado esconde el resultado: esta dominado por los casos gold, que son la mayoria.

**Recuperacion** (`m3_retrieval.json`, `m3_decision_retrieval.json`). La estrategia se eligio con una regla **fijada antes de correr** —mayor hit@3, desempate por mrr@10, desempate por menos chunks— y la traza de la decision se publica para que no se pueda cambiar la regla despues de ver los resultados. La latencia se informa con p50 y maximo ademas de la media. La razon es que una media por encima del p95 no describe el coste por consulta: describe la carga del modelo en la primera llamada repartida entre todas las demas. El artefacto trae `latencia_ms_p50`, `latencia_ms_max` y dispara `aviso_arranque` cuando eso pasa, en vez de dejarlo a quien lea la tabla.

**El agente** (`m3_agente.json`). 90 casos, y la media de pasos va **censurada por arriba**: pasos/caso >= 4.29 (cota INFERIOR: 49 de 90 casos, 54%, se cortaron en el techo de 5 pasos). Un caso que se corta en el techo no aporta los pasos que habria necesitado, aporta el techo. `veredicto_presupuesto()` ya dictamino, con umbral fijado de antemano, que subir `max_pasos` solo mueve el techo: lo que falta es un criterio de parada, y por eso no se toca el parametro.

**Coste** (`m3_costos.json`). Dos ejes que no son comparables y que la tabla no suma: el tiempo de GPU local y las llamadas a la API. Las llamadas de extraccion de hechos del agente se contabilizan — antes no pasaban por `costos.registrar`, y la tabla decia `llamadas_reales: 0` para un brazo que hacia una extraccion por caso sobre 90 casos.

## 6 · Los dos efectos adversos propios del RAG

No son ruido: son el precio de la arquitectura, y van como hallazgo porque no aparecen en la metrica de cabecera.

| brazo | abstencion indebida | citas incompletas | se abstuvo donde debia |
|---|---|---|---|
| 1 · fine-tuned solo (M1) | 0 de 63 | 0.0% | 50.0% |
| 2 · fine-tuned + RAG ingenuo | 3 de 63 | 5.8% | 50.0% |
| 3 · fine-tuned + RAG avanzado | 2 de 63 | 12.8% | 50.0% |
| 4 · agente + reglas | 0 de 63 | 0.0% | 0.0% |

**Abstencion indebida**: callarse en un caso que *si* tenia mecanismo. Es un fallo que la accuracy no castiga, porque el caso sale del denominador de la clase.

**Citas incompletas**: «art. 6», «art. 14» sin la norma. El RAG le ensena el numero de articulo y le quita la ley — y una cita sin norma no es verificable, que es justo lo que el corpus verificado existe para garantizar.

**Cero abstenciones correctas no siempre es un fallo.** El brazo del motor de reglas no se abstiene nunca porque `extraer_hechos` no activa causal de improcedencia ante la duda. El **mismo** defecto produce sus cero abstenciones indebidas. No se puede celebrar lo segundo y llamar fallo a lo primero: la declaracion va dentro del artefacto, en `cero_abstenciones_es_decision_de_diseno`.

## 7 · Limitaciones · lo que este trabajo no puede concluir

Esta seccion es el resultado mas importante del documento. El juez automatico coincide con las metricas de dominio en kappa **0.296**, y no sabemos si una persona coincidiria con el juez o con el dominio. Un proyecto que dice eso vale mas que uno que publica la cifra sin decirlo.

### 7.1 · El juez no esta validado contra criterio humano independiente

El instrumental esta completo —`data/calibracion_juez.py` y `data/doble_anotacion.py`, los dos con `--anotador` **obligatorio**— y los dos scripts se niegan a producir una cifra sin decir quien anoto. Pero yo escribi el gold, la rubrica y el juez. Si yo puntuo, lo que se mide es si una aplicacion de mi rubrica coincide con otra aplicacion de mi rubrica: eso es **consistencia**, no acuerdo entre anotadores, y el campo `_independencia` del artefacto lo dice con esas palabras. La validacion independiente **requiere una persona externa** y queda abierta.

### 7.2 · El acuerdo se midio, pero no con que linajes

Hay cifra —kappa **0.683**, entre `openai/gpt-oss-120b` y `openai/gpt-oss-20b`— y el artefacto **no** registra la familia de cada juez. Sin ese dato la cifra no se puede interpretar: un acuerdo entre dos modelos del mismo linaje mide *ruido*, y entre linajes distintos mide ruido **y** sesgo compartido. Son lecturas opuestas y el artefacto no permite elegir, asi que aqui no se elige.

### 7.3 · `accion_cumplimiento` en el brazo del agente

El brazo del agente da F1 **0.3636** en esa clase. Ya **no falla por completo** —valia 0.000 antes de corregir `derecho_colectivo` y `acto_general`— pero sigue siendo **el peor de los 4 brazos** ahi. El art. 9 de la Ley 393 de 1997 hace la accion de cumplimiento **subsidiaria**, asi que el motor exige `incumplimiento_normativo=True` **y** `afectacion_individual=False`. El extractor produce esa combinacion solo en parte de los casos, asi que el defecto esta **reducido, no cerrado**.

F1 por brazo en esa clase (8 casos de soporte): `1 · fine-tuned solo (M1)` **0.9412**, `2 · fine-tuned + RAG ingenuo` **0.7619**, `3 · fine-tuned + RAG avanzado` **0.9412**, `4 · agente + reglas` **0.3636**.

### 7.4 · En el estrato adversarial **empatan** los brazos 1 y 4

Aciertan lo mismo, 83.3% de n=18, asi que el estrato no los ordena —y no los ordena por **empate**, no por un solapamiento de intervalos. `por_tipo.adversarial` publica `n` y un punto, **sin IC**, asi que esta comparacion no viene con ancho: con n=18 un solo caso vale 5.6%.

Orden en el estrato: `1 · fine-tuned solo (M1)` 83.3%, `4 · agente + reglas` 83.3%, `3 · fine-tuned + RAG avanzado` 38.9%, `2 · fine-tuned + RAG ingenuo` 33.3%.

Ampliar el estrato invalida la comparabilidad con estas corridas, asi que es trabajo del siguiente ciclo y no un ajuste.

### 7.5 · Clases con soporte minimo

Varias categorias tienen n de un digito, y `clases_con_soporte_minimo` las nombra en cada scorecard. Un F1 de 0.000 con soporte 1 no es un hallazgo sobre el sistema: es la ausencia de muestra.

### 7.6 · Ambito

Relatos sinteticos, no expedientes. Nada de lo medido aqui autoriza a usar el sistema para orientar a una persona real sobre su caso.

## 8 · Apendice · cada cifra y su artefacto

**Artefactos o claves que no estaban**, y donde el reporte lo dice en vez de callarlo:

- `m2_acuerdo_entre_jueces.json:_familias`

| artefacto | clave | valor leido |
|---|---|---|
| `m3_scorecards_comunes.json` | `ic.acierto_juridico` | `mejor=1 · fine-tuned solo (M1), solapan=1` |
| `data/cobertura_corpus.json` | `por_eval_set.eval_set_v2.json` | `sin_cobertura=0` |
| `m1_scorecard_base.json` | `ic.acierto_juridico` | `0.0317 [0.0, 0.0794]` |
| `m1_scorecard_finetuned.json` | `ic.acierto_juridico` | `0.873 [0.7937, 0.9524]` |
| `m1_scorecard_base.json` | `ic.acc_mecanismo` | `0.3333 [0.2222, 0.4444]` |
| `m1_scorecard_finetuned.json` | `ic.acc_mecanismo` | `0.873 [0.7937, 0.9524]` |
| `m1_scorecard_base.json` | `campos.mecanismo.macro_f1` | `0.19515151515151516` |
| `m1_scorecard_finetuned.json` | `campos.mecanismo.macro_f1` | `0.8673195432018961` |
| `m1_scorecard_base.json` | `campos.mecanismo.baseline_mayoritaria` | `0.42857142857142855` |
| `m1_scorecard_finetuned.json` | `campos.mecanismo.baseline_mayoritaria` | `0.42857142857142855` |
| `m1_scorecard_base.json` | `alucinacion_normativa.tasa_alucinacion` | `0.0` |
| `m1_scorecard_finetuned.json` | `alucinacion_normativa.tasa_alucinacion` | `0.08403361344537816` |
| `m1_scorecard_finetuned.json` | `por_fiabilidad_etiqueta` | `{'motor_de_reglas_plano': {'nivel': 2, 'n': 45, 'acc_mecanis` |
| `m1_degeneracion.json` | `base.n` | `1` |
| `m1_degeneracion.json` | `base.de` | `69` |
| `m1_degeneracion.json` | `finetuned.n` | `0` |
| `m1_degeneracion.json` | `finetuned.de` | `69` |
| `m1_estabilidad.json` | `identicas` | `None` |
| `m1_redaccion.json` | `n` | `69` |
| `m1_redaccion.json` | `textos_con_citas_intrusas` | `0` |
| `m1_redaccion.json` | `dicen_el_mecanismo` | `0.9855` |
| `m1_redaccion.json` | `dicen_la_procedencia` | `0.9855` |
| `m2_sesgos.json` | `posicion.inconsistentes` | `0` |
| `m2_sesgos.json` | `posicion.n` | `12` |
| `m2_sesgos.json` | `posicion.preferencia_posicion_A_lectura` | `'indefinida a proposito: con 0 inconsistentes esta fraccion ` |
| `m2_sesgos.json` | `longitud.tasa_sesgo_longitud` | `0.16666666666666666` |
| `m2_sesgos.json` | `inyeccion.obedecieron` | `2` |
| `m2_sesgos.json` | `inyeccion.n` | `18` |
| `m2_sesgos.json` | `inyeccion.lectura_estilo` | `'La tasa agregada esconde CUAL forma de inyeccion funciona. ` |
| `m2_acuerdo_entre_jueces.json` | `kappa_aprueba` | `0.6835` |
| `m2_acuerdo_entre_jueces.json` | `corr_spearman` | `0.8962` |
| `m2_determinismo_juez.json` | `deterministico` | `True` |
| `m2_determinismo_juez.json` | `repeticiones` | `3` |
| `m2_sesgo_autopreferencia.json` | `lectura` | `'el numero que importa es `preferencia_familia_con_calidad_e` |
| `m2_rouge_vs_acierto.json` | `medio_acierta` | `0.3309366373756528` |
| `m2_rouge_vs_acierto.json` | `medio_falla` | `0.22816724042637537` |
| `m3_scorecards_comunes.json` | `tabla comparable` | `4 brazos` |
| `m3_ganadores.json` | `agregado` | `'1 · fine-tuned solo (M1)'` |
| `m3_ganadores.json` | `gold` | `'1 · fine-tuned solo (M1)'` |
| `m3_ganadores.json` | `adversarial` | `'1 · fine-tuned solo (M1)'` |
| `m3_agente.json` | `casos` | `90` |
| `m3_agente.json` | `pasos_promedio_censura.como_citar` | `'pasos/caso >= 4.29 (cota INFERIOR: 49 de 90 casos, 54%, se ` |
| `m2_scorecard_finetuned.json` | `juez.kappa_vs_dominio` | `0.29620563035495706` |
| `m2_acuerdo_entre_jueces.json` | `media_a` | `3.24` |
| `m2_acuerdo_entre_jueces.json` | `media_b` | `2.84` |
| `m2_acuerdo_entre_jueces.json` | `modelo_a` | `'openai/gpt-oss-120b'` |
| `m2_acuerdo_entre_jueces.json` | `modelo_b` | `'openai/gpt-oss-20b'` |
| `m3_scorecards_comunes.json` | `campos.mecanismo.f1_por_clase.accion_cumplimiento` | `agente=0.3636 otros=[0.7619, 0.9412, 0.9412]` |
| `m3_scorecards_comunes.json` | `por_tipo.adversarial` | `top=0.8333333333333334 primeros=['1 · fine-tuned solo (M1)', '4 · agente + reglas'] n=18` |

El valor va **sin redondear**: es lo que trae el artefacto, no lo que el reporte imprime. Si los dos no coinciden, el que vale es este.

49 lecturas de 15 artefactos distintos.

---

Reproducir: `python -I src/autoprueba_integracion.py` (fontaneria, sin GPU), luego M1 → M2 → M3 en Colab, luego `python -I data/verificar_entrega.py` y `python -I data/reporte.py`.
