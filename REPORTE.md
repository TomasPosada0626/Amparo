# Triaje de acciones constitucionales colombianas

**Fine-tuning, evaluacion y RAG sobre el mecanismo procedente ante un relato ciudadano.**

> Generado por `data/reporte.py` el 2026-10-21 13:40 (America/Bogota). Ninguna cifra de este documento esta escrita a mano: todas salen de un artefacto de `results/`, y el apendice dice de cual y de que clave. Una cifra sin artefacto hace fallar al generador.

## 0 · Que afirma este trabajo, y que no

**La tesis.** El cuello de botella para decidir *que mecanismo constitucional procede* no es el acceso al texto de la norma: es saber en que orden se preguntan las causales. Un modelo pequeno afinado sobre el arbol de decision del art. 6 del Decreto 2591 de 1991 llega mas lejos que tres arquitecturas de recuperacion con acceso al corpus entero.

Medido: el brazo **4 · agente + reglas** queda primero en el agregado, pero su intervalo **se solapa con los 3** restantes: la tabla no sostiene que sea mejor que ninguno de ellos, y la tesis de arriba queda sin respaldo en estas corridas.

**Lo que NO afirma.** Que el sistema sea apto para uso juridico real; que el juez automatico este validado contra criterio humano independiente; que los numeros se sostengan en los estratos de n pequeno. Cada una de esas tiene su cifra y su motivo en la seccion 7, que es la seccion importante de este documento.

## 1 · De donde salen las cifras

Las tres corridas comparten huella de codigo, asi que la comparacion entre modulos se sostiene.

| modulo | corrida | huella de codigo | valida | artefactos |
|---|---|---|---|---|
| m1 | 20261021T115654Z | `41ad18abecff8b82` | True | 14 |
| m2 | 20261021T124137Z | `41ad18abecff8b82` | True | 12 |
| m3 | 20261021T140413Z | `41ad18abecff8b82` | True | 17 |

`data/verificar_entrega.py` comprueba esto mismo de forma ejecutable: que los artefactos esten, que sean de la misma corrida de su modulo, que las huellas de codigo coincidan y que la version de datos sea la misma en los tres.

## 2 · Los datos y como se verificaron

Tres niveles de verificacion, y la diferencia entre ellos es lo que permite leer el resto:

- **`plano`** · la etiqueta se lee directamente del relato.
- **`derivado`** · hay que encadenar dos hechos del relato.
- **`juicio`** · hubo que ponderar. Es donde el gold es discutible, y va marcado para poder leer el resultado por separado.

El motor de reglas del art. 6 reproduce la etiqueta de los casos del eval set, pero eso significa **consistente** con el arbol, no **independiente** de el: el campo `por_fiabilidad_etiqueta` de cada scorecard lo dice con esas palabras para que nadie lea la consistencia como validacion.

**Cobertura del corpus** (`data/cobertura_corpus.json`): 69 fragmentos verificados, 77 chunks. De los 103 casos comunes, **0** citan una norma que no esta en el corpus y **69** la tienen pero por debajo del puesto 5 en BM25 (la peor, en el puesto 69 de 77). El techo de recuperacion es de **ranking**, no de cobertura — y ampliar el corpus lo empeoraria, porque mete mas candidatos a competir por los mismos cinco puestos.

## 3 · M1 · el sistema afinado

LoRA sobre Qwen2.5-7B-Instruct. Las cifras de cabecera, con intervalo bootstrap percentil, y **las tres columnas que hacen falta para leerlas**:

| metrica | base | hibrido (base + reglas) | afinado |
|---|---|---|---|
| acierto juridico | **1.9%** [0.0%, 4.9%], n=103 | **64.1%** [54.4%, 73.8%], n=103 | **71.8%** [63.1%, 80.6%], n=103 |
| acierto de mecanismo | **32.0%** [23.3%, 40.8%], n=103 | **64.1%** [54.4%, 73.8%], n=103 | **71.8%** [63.1%, 80.6%], n=103 |
| macro-F1 de mecanismo | 0.192 | 0.747 | 0.792 |
| base mayoritaria | 0.447 | 0.447 | 0.447 |
| alucinacion normativa | 0.0 | 0.0 | 0.0 |

**El acierto juridico es la metrica de cabecera y no la accuracy de mecanismo.** Acertar `tutela` por la causal equivocada no es acertar: exige mecanismo, procedencia y fundamento a la vez.

### 3.1 · Cuanto del salto es razonamiento y cuanto es formato

El salto de cabecera es **69.9%** de acierto juridico. No todo es razonamiento, y el propio dato lo dice:

- **39.8%** es diferencia de **mecanismo**: el afinado acierta mas veces la via procesal. Esto si es una afirmacion sobre derecho.
- **30.1%** es lo que el base pierde por **formato** con el mecanismo YA acertado: escribe prosa donde el esquema pide `si|no` y el parser la lee `False`, correctamente. En 36 de 103 salidas ni el mecanismo se puede leer.

Las dos son ganancias reales del fine-tuning --- sin bloque parseable no hay sistema --- pero **solo la primera es una afirmacion sobre derecho**, y sumarlas en una sola cifra exagera lo que este trabajo demuestra. Por eso la tabla de arriba lleva la columna del **hibrido**, que es el base con el motor de reglas decidiendo: aisla el razonamiento del formato.

> Lo senalo una auditoria externa, y al medirlo tenia razon. Queda pendiente el baseline de formato --- el base con few-shot del bloque de cinco lineas --- que exige una corrida.

Por estrato de fiabilidad de la etiqueta:

| estrato | nivel | n | acc. mecanismo | acierto juridico |
|---|---|---|---|---|
| `motor_de_reglas_plano` | 2 | 64 | 76.6% | 76.6% |
| `motor_de_reglas_ponderado` | 3 | 36 | 66.7% | 66.7% |
| `equipo_ponderacion_afirmada` | 4 | 3 | 33.3% | 33.3% |

> `motor_de_reglas` significa CONSISTENTE con el arbol del art. 6, no INDEPENDIENTE: los hechos los codifico el mismo equipo que puso la etiqueta. Solo el nivel 1 tiene fuente externa.

**Degeneracion.** `m1_degeneracion.json` mide la cola repetitiva y los caracteres imposibles en un triaje colombiano: base 2 de 109 salidas, afinado **0 de 109**. El recorte de generacion la acota, no la cura (ROADMAP3 · M1-1).

**Estabilidad entre corridas.** `identicas: False`. Dos corridas con el mismo codigo y los mismos datos no dan bit a bit lo mismo, y por eso el adaptador se versiona con la corrida que lo produjo y registra la huella de sus pesos: un resultado del que no se pueden recuperar los pesos no es reproducible, es anecdotico.

**Capa de redaccion.** `m1_redaccion.json` mide la capa que convierte el bloque de triaje en lenguaje natural sin dejarle inventar normas: 109 casos, **0** con normas que no estaban en el bloque, mecanismo dicho en 99.1% y procedencia en 100.0%. La guarda es estructural: el texto solo puede citar lo que el motor ya decidio. Las dos coberturas tienen que valer 1.0 --- son lo que permite que un error del triaje siga siendo detectable por quien lee el texto.

## 4 · M2 · el evaluador, evaluado

Un juez LLM que no se audita no es una medicion, es una opinion con decimales. Las tres sondas de sesgo:

| sonda | resultado | como leerlo |
|---|---|---|
| posicion | 2 inconsistentes de 12 | fraccion de las preguntas en que eligio la respuesta mostrada primero; 0.5 es ausencia de sesgo de posicion |
| longitud | tasa 0.0 | prefiere la respuesta mas larga cuando el contenido es el mismo |
| inyeccion de prompt | 0 de 18 obedecieron | La tasa agregada esconde CUAL forma de inyeccion funciona. Un estilo con una sola sonda no sostiene una tasa: aparece en `estilos_con_una_sola_sonda` para que n |

La inyeccion se mide con **tres sondas por estilo** precisamente porque con una sola no se puede distinguir un estilo que funciona siempre de uno que acerto por suerte; el desglose va en `inyeccion.por_estilo`, y los estilos que se quedaron con una sola sonda van nombrados en `estilos_con_una_sola_sonda` en vez de promediados con los demas.

**Acuerdo entre jueces.** `m2_acuerdo_entre_jueces.json`: kappa 0.444, Spearman 0.785. Si el segundo juez no estuvo servido, el artefacto no existe y esta linea lo dice: publicar un archivo vacio seria peor que no publicarlo.

**Determinismo.** `m2_determinismo_juez.json`: `deterministico: False` sobre 3 llamadas reales, sin cache. Si el juez no repite su propia nota con temperature=0, su nota tiene varianza propia y las comparaciones de pocas decimas no son interpretables.

**Auto-preferencia.** `m2_sesgo_autopreferencia.json` condiciona en la verdad de dominio para separar «premia a su familia» de «acierta»: el numero que importa es `preferencia_familia_con_calidad_empatada`: 0.5 es ausencia de auto-preferencia. Fuera del estrato de empate la preferencia puede ser merito y no sesgo, por eso no se agrega todo en una sola cifr

**ROUGE-L contra acierto.** `m2_rouge_vs_acierto.json` es el argumento con datos de por que la similitud lexica no mide derecho: ROUGE-L medio **0.324** cuando la respuesta ACIERTA y **0.219** cuando FALLA. Si los dos se parecen, el solapamiento lexico no distingue una respuesta correcta de una equivocada --- y entonces no puede ser la metrica de cabecera.

## 5 · M3 · cuatro arquitecturas sobre los mismos casos

La tabla es sobre los **103 casos comunes** a los cuatro brazos. La tabla de `m3_scorecard.csv` pone el brazo 1 con un n distinto al de los brazos 2-4 y con otra base mayoritaria: son conjuntos distintos y no se pueden comparar.

| brazo | n | acierto juridico [IC95] | acc. mecanismo | macro-F1 | gold | adversarial |
|---|---|---|---|---|---|---|
| 1 · fine-tuned solo (M1) | 103 | **71.8%** [63.1%, 80.6%] | 71.8% | 0.792 | 78.1% | 61.5% |
| 2 · fine-tuned + RAG ingenuo | 103 | **59.2%** [49.5%, 68.9%] | 60.2% | 0.577 | 78.1% | 28.2% |
| 3 · fine-tuned + RAG avanzado | 103 | **60.2%** [51.5%, 68.9%] | 63.1% | 0.605 | 68.8% | 46.2% |
| 4 · agente + reglas | 103 | **72.8%** [64.1%, 81.5%] | 72.8% | 0.686 | 68.8% | 79.5% |

**Ganadores** (`m3_ganadores.json`): agregado **4 · agente + reglas**, gold **1 · fine-tuned solo (M1)**, adversarial **4 · agente + reglas**. Si el ganador en gold y en adversarial no es el mismo, el agregado esconde el resultado: esta dominado por los casos gold, que son la mayoria.

**Recuperacion** (`m3_retrieval.json`, `m3_decision_retrieval.json`). La estrategia se eligio con una regla **fijada antes de correr** —mayor hit@3, desempate por mrr@10, desempate por menos chunks— y la traza de la decision se publica para que no se pueda cambiar la regla despues de ver los resultados. La latencia se informa con p50 y maximo ademas de la media. La razon es que una media por encima del p95 no describe el coste por consulta: describe la carga del modelo en la primera llamada repartida entre todas las demas. El artefacto trae `latencia_ms_p50`, `latencia_ms_max` y dispara `aviso_arranque` cuando eso pasa, en vez de dejarlo a quien lea la tabla.

**El agente** (`m3_agente.json`). 130 casos, y la media de pasos va **censurada por arriba**: pasos/caso >= 4.15 (cota INFERIOR: 65 de 130 casos, 50%, se cortaron en el techo de 5 pasos). Un caso que se corta en el techo no aporta los pasos que habria necesitado, aporta el techo. `veredicto_presupuesto()` ya dictamino, con umbral fijado de antemano, que subir `max_pasos` solo mueve el techo: lo que falta es un criterio de parada, y por eso no se toca el parametro.

**Coste** (`m3_costos.json`). Dos ejes que no son comparables y que la tabla no suma: el tiempo de GPU local y las llamadas a la API. Las llamadas de extraccion de hechos del agente se contabilizan — antes no pasaban por `costos.registrar`, y la tabla decia `llamadas_reales: 0` para un brazo que hacia una extraccion por caso sobre 130 casos.

## 6 · Los dos efectos adversos propios del RAG

No son ruido: son el precio de la arquitectura, y van como hallazgo porque no aparecen en la metrica de cabecera.

| brazo | abstencion indebida | citas incompletas | se abstuvo donde debia |
|---|---|---|---|
| 1 · fine-tuned solo (M1) | 9 de 103 | 0.0% | 100.0% |
| 2 · fine-tuned + RAG ingenuo | 5 de 103 | 0.0% | 50.0% |
| 3 · fine-tuned + RAG avanzado | 3 de 103 | 0.0% | 50.0% |
| 4 · agente + reglas | 3 de 103 | 0.0% | 50.0% |

**Abstencion indebida**: callarse en un caso que *si* tenia mecanismo. Es un fallo que la accuracy no castiga, porque el caso sale del denominador de la clase.

**Citas incompletas**: «art. 6», «art. 14» sin la norma. El RAG le ensena el numero de articulo y le quita la ley — y una cita sin norma no es verificable, que es justo lo que el corpus verificado existe para garantizar.

**Cero abstenciones correctas no siempre es un fallo.** El brazo del motor de reglas no se abstiene nunca porque `extraer_hechos` no activa causal de improcedencia ante la duda. El **mismo** defecto produce sus cero abstenciones indebidas. No se puede celebrar lo segundo y llamar fallo a lo primero: la declaracion va dentro del artefacto, en `cero_abstenciones_es_decision_de_diseno`.

### 4.4 · Las citas existen (0.0 de alucinacion) y no siempre vienen al caso

De **178** citas emitidas por el brazo ajustado, **98** vienen al caso y **80** no. Ninguna esta inventada (**0**) y ninguna queda incompleta (**0**).

| | precision | recall |
|---|---|---|
| agregado (`precision_citas`) | **0.5506** | 0.4135 |
| plano del MECANISMO | 0.5682 | 0.3876 |
| plano del DERECHO | 0.5556 | 0.3185 |

**El agregado esta sesgado, y por una asimetria del gold que no se puede corregir.** El campo `fundamento` del eval set incluye las normas procesales del mecanismo —`art. 6.1` para `via_ordinaria`, `art. 6.2` y la Ley 1095 para habeas corpus— y **omite `art. 86 CP`** en los casos de tutela. Asi que un modelo que cita el art. 86 —la norma que crea la tutela, y justo lo que emite `reglas.decidir()`— cuenta como impertinente.

No se arregla porque `fundamento` es uno de los campos que el puente de comparacion congela: v2 contiene a v1 y v3 a v2 byte a byte, y cambiarlo destruiria doce corridas de comparabilidad. El agregado se publica **por comparabilidad**; la particion por planos, **por lectura**.

Donde cae cada cita:

| caja | citas | que significa |
|---|---|---|
| `mecanismo_correcto` | 50 | acerto el plano procesal |
| `mecanismo_equivocado` | 38 | cito OTRO mecanismo — error de razonamiento sobre la via |
| `derecho_correcto` | 50 | acerto el derecho de fondo |
| `derecho_impertinente` | 40 | cito un derecho que no viene al caso |
| `inventada` | 0 | la norma no existe |

La cita que mas se equivoca de plano es `art. 6.1 Decreto 2591 de 1991` (26 veces), `Ley 1095 de 2006` (4 veces), `art. 6.3 Decreto 2591 de 1991` (2 veces). `data/causas_abiertas.json` establece de donde sale: **59 de 123 ejemplos de train** ensenan al modelo a citar una norma PROCESAL en la linea del derecho, porque el objetivo de entrenamiento fusiona `fundamento_del_derecho` con `fundamento_del_mecanismo`. Los dos campos ya existen separados en el dataset: es un cambio de formato, no de anotacion.

**Corroborado por una via independiente.** El abogado que valido al juez (§7.1) senalo citas que no corresponden en **5 de sus 10** comentarios, sin haber visto ninguna de estas cifras. Dos mediciones independientes apuntando al mismo defecto es la evidencia mas fuerte de este reporte.

## 7 · Limitaciones · lo que este trabajo no puede concluir

Esta seccion es el resultado mas importante del documento. El juez automatico coincide con las metricas de dominio en kappa **0.431**, y no sabemos si una persona coincidiria con el juez o con el dominio. Un proyecto que dice eso vale mas que uno que publica la cifra sin decirlo.

### 7.1 · El juez contra un abogado: kappa **0.5763** sobre 25 casos

Es la unica cifra del proyecto en la que uno de los dos evaluadores **no es un modelo**, asi que es la unica de la que se puede afirmar que no comparte linaje con el juez. Mide *validez de criterio*: acuerdo exacto **0.68**, a un punto **0.92**, Spearman **0.8339**, con 2 desacuerdo(s) de dos puntos o mas.

**Lo que esta cifra no dice, en dos cosas.** Primero, la muestra la pone una persona a mano y esta **sesgada a proposito**: se tomaron hasta cinco casos de *cada* nota del juez, porque una muestra proporcional serian 25 casos con casi toda la varianza en un punto. Asi que estima el acuerdo condicionado a esos estratos, no el del eval set entero. Segundo, mide **acuerdo, no verdad**: donde el juez y el abogado coinciden en una nota equivocada, esto no lo ve.

#### 7.1.1 · El juez respeta su propia escala en **0.8058** de 103 notas

La kappa contra el dominio vale **0.431**, y subirla **no seria una mejora**: un juez que coincidiera con `acierto_juridico` seria una copia ruidosa de esa metrica y no aportaria el razonamiento, que es lo que la accuracy no ve. La pregunta que si tiene respuesta correcta es otra: la rubrica define `nota >= 3` como «mecanismo correcto», asi que el juez se puede auditar **contra su propia definicion** sin preguntarle a nadie.

Resultado: **0** notas generosas —`nota >= 3` con el mecanismo equivocado— y **20** severas. Las generosas son las graves: inflan la dimension 2. Las dos direcciones se cuentan por separado porque cuestan distinto.

Leidas juntas, las dos cifras se interpretan asi: kappa baja con adherencia **alta** significa que el juez mide algo que la accuracy no ve, que es para lo que existe; kappa baja con adherencia **baja** significaria que sus notas no quieren decir lo que la rubrica dice, y entonces la dimension 2 entera no se puede leer con esa escala.

### 7.2 · Los dos jueces son de la misma familia (`gpt-oss`)

El acuerdo controla el *ruido* de un juez, no el *sesgo* que dos modelos del mismo linaje comparten: un acuerdo alto —kappa **0.444**— es compatible con que los dos se equivoquen igual. Por que no se uso otra familia: ninguno de los modelos de otra familia servidos en esta cuenta sostuvo la rubrica sobre los 25 casos.

### 7.3 · `accion_cumplimiento` en el brazo del agente

El brazo del agente da F1 **0.5455** en esa clase. Ya **no falla por completo** —valia 0.000 antes de corregir `derecho_colectivo` y `acto_general`— pero sigue siendo **el peor de los 4 brazos** ahi. El art. 9 de la Ley 393 de 1997 hace la accion de cumplimiento **subsidiaria**, asi que el motor exige `incumplimiento_normativo=True` **y** `afectacion_individual=False`. El extractor produce esa combinacion solo en parte de los casos, asi que el defecto esta **reducido, no cerrado**.

F1 por brazo en esa clase (8 casos de soporte): `1 · fine-tuned solo (M1)` **0.8235**, `2 · fine-tuned + RAG ingenuo` **0.7619**, `3 · fine-tuned + RAG avanzado` **0.8421**, `4 · agente + reglas` **0.5455**.

### 7.4 · En el estrato adversarial gana el brazo 4

Queda primero con 79.5% de n=39. `por_tipo.adversarial` publica `n` y un punto, **sin IC**, asi que esta comparacion no viene con ancho: con n=39 un solo caso vale 2.6%.

Orden en el estrato: `4 · agente + reglas` 79.5%, `1 · fine-tuned solo (M1)` 61.5%, `3 · fine-tuned + RAG avanzado` 46.2%, `2 · fine-tuned + RAG ingenuo` 28.2%.

Ampliar el estrato invalida la comparabilidad con estas corridas, asi que es trabajo del siguiente ciclo y no un ajuste.

### 7.5 · Clases con soporte minimo

Varias categorias tienen n de un digito, y `clases_con_soporte_minimo` las nombra en cada scorecard. Un F1 de 0.000 con soporte 1 no es un hallazgo sobre el sistema: es la ausencia de muestra.

### 7.6 · Ambito

Relatos sinteticos, no expedientes. Nada de lo medido aqui autoriza a usar el sistema para orientar a una persona real sobre su caso.

## 8 · Apendice · cada cifra y su artefacto

| artefacto | clave | valor leido |
|---|---|---|
| `m3_scorecards_comunes.json` | `ic.acierto_juridico` | `mejor=4 · agente + reglas, solapan=3` |
| `data/cobertura_corpus.json` | `por_eval_set.eval_set_v3.json` | `sin_cobertura=0` |
| `m1_scorecard_base.json` | `ic.acierto_juridico` | `0.0194 [0.0, 0.0485]` |
| `m1_scorecard_hibrido.json` | `ic.acierto_juridico` | `0.6408 [0.5437, 0.7379]` |
| `m1_scorecard_finetuned.json` | `ic.acierto_juridico` | `0.7184 [0.6311, 0.8058]` |
| `m1_scorecard_base.json` | `ic.acc_mecanismo` | `0.3204 [0.233, 0.4078]` |
| `m1_scorecard_hibrido.json` | `ic.acc_mecanismo` | `0.6408 [0.5437, 0.7379]` |
| `m1_scorecard_finetuned.json` | `ic.acc_mecanismo` | `0.7184 [0.6311, 0.8058]` |
| `m1_scorecard_base.json` | `campos.mecanismo.macro_f1` | `0.19171171171171172` |
| `m1_scorecard_hibrido.json` | `campos.mecanismo.macro_f1` | `0.746697045644414` |
| `m1_scorecard_finetuned.json` | `campos.mecanismo.macro_f1` | `0.7918505229807279` |
| `m1_scorecard_base.json` | `campos.mecanismo.baseline_mayoritaria` | `0.44660194174757284` |
| `m1_scorecard_hibrido.json` | `campos.mecanismo.baseline_mayoritaria` | `0.44660194174757284` |
| `m1_scorecard_finetuned.json` | `campos.mecanismo.baseline_mayoritaria` | `0.44660194174757284` |
| `m1_scorecard_base.json` | `alucinacion_normativa.tasa_alucinacion` | `0.0` |
| `m1_scorecard_hibrido.json` | `alucinacion_normativa.tasa_alucinacion` | `0.0` |
| `m1_scorecard_finetuned.json` | `alucinacion_normativa.tasa_alucinacion` | `0.0` |
| `data/descomposicion_baseline.json` | `salto_de_cabecera_acierto_juridico` | `0.699 = mecanismo 0.398 + formato 0.301` |
| `m1_scorecard_finetuned.json` | `por_fiabilidad_etiqueta` | `{'motor_de_reglas_plano': {'nivel': 2, 'n': 64, 'acc_mecanis` |
| `m1_degeneracion.json` | `base.n` | `2` |
| `m1_degeneracion.json` | `base.de` | `109` |
| `m1_degeneracion.json` | `finetuned.n` | `0` |
| `m1_degeneracion.json` | `finetuned.de` | `109` |
| `m1_estabilidad.json` | `identicas` | `False` |
| `m1_redaccion.json` | `n` | `109` |
| `m1_redaccion.json` | `textos_con_citas_intrusas` | `0` |
| `m1_redaccion.json` | `dicen_el_mecanismo` | `0.9908` |
| `m1_redaccion.json` | `dicen_la_procedencia` | `1.0` |
| `m2_sesgos.json` | `posicion.inconsistentes` | `2` |
| `m2_sesgos.json` | `posicion.n` | `12` |
| `m2_sesgos.json` | `posicion.preferencia_posicion_A_lectura` | `'fraccion de las preguntas en que eligio la respuesta mostra` |
| `m2_sesgos.json` | `longitud.tasa_sesgo_longitud` | `0.0` |
| `m2_sesgos.json` | `inyeccion.obedecieron` | `0` |
| `m2_sesgos.json` | `inyeccion.n` | `18` |
| `m2_sesgos.json` | `inyeccion.lectura_estilo` | `'La tasa agregada esconde CUAL forma de inyeccion funciona. ` |
| `m2_acuerdo_entre_jueces.json` | `kappa_aprueba` | `0.4444` |
| `m2_acuerdo_entre_jueces.json` | `corr_spearman` | `0.7853` |
| `m2_determinismo_juez.json` | `deterministico` | `False` |
| `m2_determinismo_juez.json` | `repeticiones` | `3` |
| `m2_sesgo_autopreferencia.json` | `lectura` | `'el numero que importa es `preferencia_familia_con_calidad_e` |
| `m2_rouge_vs_acierto.json` | `medio_acierta` | `0.32368426518903565` |
| `m2_rouge_vs_acierto.json` | `medio_falla` | `0.21893178771147512` |
| `m3_scorecards_comunes.json` | `tabla comparable` | `4 brazos` |
| `m3_ganadores.json` | `agregado` | `'4 · agente + reglas'` |
| `m3_ganadores.json` | `gold` | `'1 · fine-tuned solo (M1)'` |
| `m3_ganadores.json` | `adversarial` | `'4 · agente + reglas'` |
| `m3_agente.json` | `casos` | `130` |
| `m3_agente.json` | `pasos_promedio_censura.como_citar` | `'pasos/caso >= 4.15 (cota INFERIOR: 65 de 130 casos, 50%, se` |
| `m1_scorecard_finetuned.json` | `pertinencia_citas` | `{'citas_emitidas': 178, 'correctas': 98, 'impertinentes': 80` |
| `m2_scorecard_finetuned.json` | `juez.kappa_vs_dominio` | `0.4311244662343824` |
| `m2_scorecard_finetuned.json` | `juez.adherencia_a_la_rubrica` | `{'n': 103, 'concluyente': True, 'excluidos_por_abstencion': ` |
| `m2_acuerdo_entre_jueces.json` | `_familias` | `{'conocido': True, 'familia_a': 'gpt-oss', 'familia_b': 'gpt` |
| `m2_acuerdo_entre_jueces.json` | `media_a` | `3.28` |
| `m2_acuerdo_entre_jueces.json` | `media_b` | `3.0` |
| `m3_scorecards_comunes.json` | `campos.mecanismo.f1_por_clase.accion_cumplimiento` | `agente=0.5455 otros=[0.7619, 0.8235, 0.8421]` |
| `m3_scorecards_comunes.json` | `por_tipo.adversarial` | `top=0.7948717948717948 primeros=['4 · agente + reglas'] n=39` |

El valor va **sin redondear**: es lo que trae el artefacto, no lo que el reporte imprime. Si los dos no coinciden, el que vale es este.

56 lecturas de 17 artefactos distintos.

---

Reproducir: `python -I src/autoprueba_integracion.py` (fontaneria, sin GPU), luego M1 → M2 → M3 en Colab, luego `python -I data/verificar_entrega.py` y `python -I data/reporte.py`.
