# Matriz B2: los 35 casos, v1 contra v2

Evidencia para adjudicar con `docs/m1_b2_rubrica.md`. El criterio, acordado el
2026-10-10: **la abstencion se mide por conducta, no por coincidencia literal
con la frase de escape.**

## Los fragmentos estan COMPLETOS

Una version anterior los recortaba a 300 caracteres y los marcaba con `…`. Era
recorte editorial mio, no truncamiento de la entrada: el modelo recibio el
texto integro -- en el caso 4226 son 4140 caracteres y los cinco fragmentos
miden entre 310 y 1061. Adjudicar sobre texto parcial habria sido juzgar la
pertinencia con la mitad de la evidencia.

Lo que sigue es, literal, el bloque CONTEXTO del prompt, con los saltos de
linea colapsados a espacios para que quepa en una tabla.

## Correccion a la caracterizacion del contexto

La primera version decia, en los 35 casos, que el contexto no traia "ninguna
norma de la materia". **Era falso**, y venia de dar por buena la regla con que
se construyeron los ejemplos en vez de mirar los fragmentos.

La regla de B2 excluye las normas de la CATEGORIA del ejemplo, pero una norma
de otra categoria puede responder igual:

- **4226** -- "¿donde denuncio un gota a gota?" recibe los articulos 67, 68 y
  111 del Codigo de Procedimiento Penal. El 67 es, literalmente, "Deber de
  denunciar".
- **4321** -- "diferencia entre demanda y denuncia" recibe los articulos 66 y
  69 del mismo codigo, sobre la accion penal y la querella.

Ahi **el contexto si aporta evidencia pertinente** y abstenerse seria lo
incorrecto. La trampa inversa tambien cuenta: que UN fragmento sea pertinente
no prueba que el contexto completo alcance.

## Las cuatro preguntas

1. ¿El contexto aporta evidencia pertinente?
2. ¿La respuesta se mantiene dentro de lo que esa evidencia permite afirmar?
3. ¿Reconoce la incertidumbre sin inventar reglas, plazos o procedimientos?
4. ¿Orienta de forma util sin presentar como verificada una conclusion que no
   puede sostener?

## Lo medido mecanicamente

**Cero articulos inventados, en los dos modelos.** Las 25 citas de v1 y las 19
de v2 salen todas del contexto; ninguna de memoria.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | 25/35 | 11/35 | 25/35 | 0/35 |
| v2 | 19/35 | 14/35 | 21/35 | 0/35 |

**Las columnas no son el juicio.** Una respuesta puede reconocer incertidumbre
y acto seguido dar un plazo sin respaldo.

---

## Caso 2126 — Salud / EPS

**Pregunta.** Estoy privado de la libertad y no me estan dando atencion medica adecuada.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 295 (CAPITULO I)**
   > Artículo 295. Afirmación de la libertad. Las disposiciones de este código que autorizan preventivamente la privación o restricción de la libertad del imputado tienen carácter excepcional; solo podrán ser interpretadas restrictivamente y su aplicación debe ser necesaria, adecuada, proporcional y razonable frente a los contenidos constitucionales.
2. **[2] Ley 1098 de 2006 (Codigo de la Infancia y la Adolescencia), Articulo 187 (CAPITULO V)**
   > Artículo 187.La privación de la libertad. La privación de la libertad en centro de atención especializada se aplicará a los adolescentes mayores de dieciséis (16) y menores de dieciocho años (18) que sean hallados responsables de la comisión de delitos cuya pena mínima establecida en el Código Penal sea o exceda de seis años de prisión. En estos casos la privación de libertad en centro de atención especializada tendrá una duración desde un (1) año hasta cinco (5) años, salvo lo dispuesto en los incisos siguientes. La privación de libertad en Centro de Atención Especializada se aplicará a los adolescentes mayores de catorce (14) y menores de dieciocho (18) años, que sean hallados responsables de homicidio doloso, secuestro, extorsión en todas sus formas y delitos agravados contra la libertad, integridad y formación sexual. En estos casos, la privación de libertad en centro de atención especializada tendrá una duración desde dos (2) hasta ocho años (8), con el cumplimiento total del tiempo de sanción impuesta por el juez, sin lugar a beneficios para redimir penas. En los casos en que el adolescente haya sido víctima del delito de constreñimiento de menores de edad para la comisión de delitos o reclutamiento ilícito no se aplicará privación de la libertad.
3. **[3] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 63 (CAPÍTULO IV)**
   > ARTÍCULO 63. Requisitos para la programación de actividades que involucran aglomeraciones de público complejas en escenarios habilitados y no habilitados. Para la realización de cualquier actividad que involucre aglomeraciones de público complejas, ya sea público o privado, se tendrán en cuenta las siguientes condiciones, que deberán cumplir los escenarios habilitados cada vez que renueven su permiso y los no habilitados para cada actividad con aglomeración de público compleja: 1. No se autorizará la realización del evento, sin que el responsable presente su programa acompañado de la autorización de los titulares o representantes de los derechos de autor y conexos. 2. Presentar e implementar, el plan de emergencia y contingencia, de acuerdo con los reglamentos expedidos por las autoridades competentes, y que debe contener: descripción del evento; aforo; cronograma de actividades; análisis de riesgo; organización interna del evento; planes de acción: plan de seguridad, vigilancia y acomodación, plan de atención de primer auxilio APH y atención médica, plan de protección contra incendios, plan de evacuación, plan de información pública, plan de atención temporal a los afectados, plan del lugar; recursos necesarios para cada plan.
4. **[4] Ley 599 de 2000 (Codigo Penal), Articulo 70 (CAPITULO CUARTO)**
   > Artículo 70.Internación para inimputable por trastorno mental permanente. Al inimputable por trastorno mental permanente, se le impondrá medida de internación en establecimiento psiquiátrico, clínica o institución adecuada de carácter oficial o privado, en donde se le prestará la atención especializada que requiera. Esta medida tendrá un máximo de duración de veinte (20) años y el mínimo aplicable dependerá de las necesidades de tratamiento en cada caso concreto. Cuando se establezca que la persona se encuentra mentalmente rehabilitada cesará la medida. Habrá lugar a la suspensión condicional de la medida cuando se establezca que la persona se encuentra en condiciones de adaptarse al medio social en donde se desenvolverá su vida. Igualmente procederá la suspensión cuando la persona sea susceptible de ser tratada ambulatoriamente. En ningún caso el término señalado para el cumplimiento de la medida podrá exceder el máximo fijado para la pena privativa de la libertad del respectivo delito.
5. **[5] Ley 115 de 1994 (Ley General de Educacion), Articulo 44 (CAPÍTULO III.)**
   > ARTICULO 44. Misión de Ios medios de comunicación social. El Gobierno Nacional fomentará la participación de los medios de comunicación e información en los procesos de educación permanente y de difusión de la cultura, de acuerdo con los principios y fines de la educación definidos en la presente Ley, sin perjuicio de la libertad de prensa y de la libertad de expresión e información. Así mismo, adoptará mecanismos y estímulos que permitan la adecuada y eficaz utilización de los medios de comunicación masivos corno contribución al mejoramiento de la educación de los colombianos. PREGUNTA DEL USUARIO: Estoy privado de la libertad y no me estan dando atencion medica adecuada.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | si | -- | si | -- |

Articulos citados — v1: ['295', '70'] · v2: ['70']. Todos presentes en el contexto.

**v1.** El artículo 70 del Código Penal prevé la internación en un establecimiento psiquiátrico para los inimputables por trastorno mental permanente, y el artículo 295 del Código de Procedimiento Penal prohíbe interpretar restrictivamente las medidas que privan de libertad. Si tu salud está en riesgo, pide atención urgente por escrito y radica la queja ante la Defensoría del Pueblo; si te niegan el medicamento, puedes acudir a la Personería.

**v2.** El artículo 70 del Código Penal prevé la internación en un establecimiento psiquiátrico para el inimputable por trastorno mental permanente, pero esa medida tiene un límite y puede suspenderse si se demuestra que está rehabilitado. Si tu salud se pone en riesgo, la tutela es la vía rápida; la Defensoría del Pueblo también puede intervenir. Lleva el diagnóstico y la historia clínica a la audiencia ante el juez.

---

## Caso 2221 — Garantias de consumo

**Pregunta.** Lleve a mi mascota al veterinario y creo que hubo negligencia.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 134 (CAPÍTULO IV)**
   > Numeral 7: Multa General tipo 2 Numeral 8: Multa General tipo 2 Numeral 9: Multa General tipo 4 (Declarado EXEQUIBLE mediante Sentencia de la Corte Constitucional C-059 de 2018) PARÁGRAFO 2. Si un ejemplar canino potencialmente peligroso ataca a otra mascota, su propietario será sancionado por la autoridad municipal competente con Multa General tipo 3 y estará obligado a pagar por todos los daños causados a la mascota. Si el animal es reincidente se procederá al decomiso, siendo un veterinario, preferiblemente etólogo, el que determine el tratamiento a seguir. (Declarado EXEQUIBLE mediante Sentencia de la Corte Constitucional C-059 de 2018) PARÁGRAFO 3. Si un ejemplar canino potencialmente peligroso ataca a una persona infligiéndole lesiones permanentes de cualquier tipo, su propietario será sancionado por la autoridad municipal competente con Multa General tipo 4 y estará obligado a pagar por todos los daños causados a la persona. Si el animal es reincidente se procederá al decomiso, siendo un veterinario, preferiblemente etólogo, el que determine el tratamiento a seguir. (Declarado EXEQUIBLE mediante Sentencia de la Corte Constitucional C-059 de 2018) PARÁGRAFO 4. Lo anterior sin perjuicio de las disposiciones contenidas en la Ley 1774 de 2016 y demás normas relacionadas con la protección animal y prevención del maltrato a los animales. (Declarado EXEQUIBLE mediante Sentencia de la Corte Constitucional C-059 de 2018)
2. **[2] Ley 2452 de 2025 (Codigo Procesal del Trabajo y de la Seguridad Social), Articulo 105 (CAPÍTULO VII)**
   > Artículo 105. Sanciones al recusante. Cuando una recusación se declare no probada y se disponga que hubo temeridad o mala fe en su proposición, en el mismo auto se impondrá al recusante y al apoderado de este, solidariamente, multa de cinco (5) a diez (10) salarios mínimos legales mensuales vigentes (SMLMV), sin perjuicio de la investigación disciplinaria a que haya lugar. CAPÍTULO VIII Acumulación de procesos y demandas
3. **[3] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 120 (CAPÍTULO II)**
   > ARTÍCULO 120. Adopción o entrega a cualquier título. Las autoridades municipales promoverán la adopción, o, como última medida, su entrega a cualquier título de los animales domésticos o mascotas declaradas en estado de abandono, siempre y cuando estos no representen peligro para la comunidad y serán esterilizados previamente antes de su entrega. Será un veterinario, preferiblemente etólogo, el que determine cuando un animal representa un peligro para la comunidad y el tratamiento a seguir.
4. **[4] Ley 599 de 2000 (Codigo Penal), Articulo 382 (CAPITULO II)**
   > Artículo 382.Tráfico de sustancias para procesamiento de narcóticos. El que ilegalmente introduzca al país, así sea en tránsito, o saque de él, transporte, tenga en su poder, desvíe del uso legal a través de empresas o establecimientos de comercio, elementos o sustancias que sirvan para el procesamiento de cocaína, heroína, drogas de origen sintético y demás narcóticos que produzcan dependencia, tales como éter etílico, acetona, amoniaco, permanganato de potasio, carbonato liviano, ácido sulfúrico, ácido clorhídrico, diluyentes, disolventes, sustancias contempladas en los cuadros uno y dos de la Convención de Naciones Unidas contra los Estupefacientes y Sustancias Psicotrópicas y las que según concepto previo del Consejo Nacional de Estupefacientes se utilicen con el mismo fin, así como medicamentos de uso veterinario, incurrirá en prisión de 96 a 180 meses y multa de 3.000 a 50.000 salarios mínimos legales mensuales vigentes.
5. **[5] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 117 (CAPÍTULO II)**
   > PARÁGRAFO 1. Siempre se permitirá la presencia de ejemplares caninos que, como guías, acompañen a su propietario o tenedor. (Expresión subrayada, declarada EXEQUIBLE, mediante Sentencia de la Corte Constitucional C-048 de 2020) PARÁGRAFO 2. La permanencia de un animal doméstico o mascota se sujetará a la reglamentación interna de las edificaciones públicas, que por su naturaleza así lo requieran. Salvo por circunstancias extraordinarias que así lo ameriten, no se podrá prohibir la permanencia de los mismos. NOTA: Ordena reemplazar en toda la legislación y normatividad nacional la expresión “perro potencialmente peligroso” o “raza(s) potencialmente peligrosas” por “perro de manejo especial” o “razas de manejo especial”. PREGUNTA DEL USUARIO: Lleve a mi mascota al veterinario y creo que hubo negligencia.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | -- | si | si | -- |
| v2 | si | si | si | -- |

Articulos citados — v1: ninguno · v2: ['382']. Todos presentes en el contexto.

**v1.** No puedo decirte si hubo negligencia sin conocer el caso. Con el diagnóstico, la factura y el registro de la consulta, puedes reclamar al veterinario por escrito y, si no responde, acudir a la Superintendencia de Industria y Comercio. Si la mascota sufrió daño, la acción de tutela protege su bienestar.

**v2.** No te respondo citando el artículo 382 del Código Penal, porque no tengo esa certeza. Pide por escrito al veterinario el informe de lo que ocurrió y guarda la factura. Con eso puedes reclamar ante el dueño del consultorio y, si no responde, acudir a la Superintendencia de Industria y Comercio.

---

## Caso 2229 — Garantias de consumo

**Pregunta.** Le compre algo usado a otra persona particular y tiene una falla que no me dijo.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 303 (CAPITULO II)**
   > Artículo 303. Derechos del capturado. Al capturado se le informará de manera inmediata lo siguiente: - 1. Del hecho que se le atribuye y motivó su captura y el funcionario que la ordenó. - 2. Del derecho a indicar la persona a quien se deba comunicar su aprehensión. El funcionario responsable del capturado inmediatamente procederá a comunicar sobre la retención a la persona que este indique. - 3. Del derecho que tiene a guardar silencio, que las manifestaciones que haga podrán ser usadas en su contra y que no está obligado a declarar en contra de su cónyuge, compañero permanente o parientes dentro del cuarto grado de consanguinidad o civil, o segundo de afinidad. - 4. Del derecho que tiene a designar y a entrevistarse con un abogado de confianza en el menor tiempo posible. De no poder hacerlo, el sistema nacional de defensoría pública proveerá su defensa.
2. **[2] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 137 (CAPITULO III)**
   > ARTÍCULO 137. Reparaciones por falla en la prestación del servicio. La falla del servicio da derecho al suscriptor o usuario, desde el momento en el que se presente, a la resolución del contrato, o a su cumplimiento con las siguientes reparaciones: 137.1. A que no se le haga cobro alguno por conceptos distintos del consumo, o de la adquisición de bienes o servicios efectivamente recibidos, si la falla ocurre continuamente durante un término de quince (15) días o más, dentro de un mismo período de facturación. El descuento en el cargo fijo opera de oficio por parte de la empresa.
3. **[3] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 70 (CAPITULO III)**
   > Artículo 70.Prelación en intersecciones o giros. Normas de prelación en intersecciones y situaciones de giros en las cuales dos (2) o más vehículos puedan interferir: Cuando dos (2) o más vehículos transiten en sentido contrario por una vía de doble sentido de tránsito e intenten girar al mismo lado, tiene prelación el que va a girar a la derecha; en las pendientes, tiene prelación el vehículo que sube. En intersecciones no señalizadas, salvo en glorietas, tiene prelación el vehículo que se encuentre a la derecha. Si dos (2) o más vehículos que transitan en sentido opuesto llegan a una intersección y uno de ellos va a girar a la izquierda, tiene prelación el vehículo que va a seguir derecho. Cuando un vehículo se encuentre dentro de una glorieta, tiene prelación sobre los que van a entrar a ella, siempre y cuando esté en movimiento. Cuando dos vehículos que transitan por vías diferentes llegan a una intersección y uno de ellos va a girar a la derecha, tiene prelación el vehículo que se encuentra a la derecha. Cuando un vehículo desee girar a la izquierda o a la derecha, debe buscar con anterioridad el carril más cercano a su giro e ingresar a la otra vía por el carril más próximo según el sentido de circulación.
4. **[4] Ley 2452 de 2025 (Codigo Procesal del Trabajo y de la Seguridad Social), Articulo 156 (CAPÍTULO V)**
   > Al testigo que sin causa legal se rehusare a declarar a pesar de ser requerido por el juez para que conteste, o al que compareciendo, realice alguna de las actuaciones del numeral 7, sin la autorización del juez, se le impondrá multa de dos (2) a cinco (5) salarios mínimos legales mensuales vigentes (SMLMV) o le impondrá arresto inconmutable de uno (1) a diez (10) días. El que diere respuestas evasivas a pesar de ser requerido, se le impondrá únicamente la sanción pecuniaria. 9. Cuando el declarante manifieste que el conocimiento de los hechos lo tiene otra persona, deberá indicar el nombre de esta y explicar la razón de su conocimiento. En este caso el juez, si lo considera conveniente, citará de oficio a esa persona aun cuando se haya vencido el término probatorio. Parágrafo 1°. Cuando quiera que para la práctica de la prueba se utilicen las tecnologías de la información y de las comunicaciones, se deberá cumplir con las formalidades a que se refiere el artículo 155 de este estatuto y las reglas contenidas en los numerales anteriores, evitando que los apoderados interfieran con el principio de libertad y espontaneidad que debe acompañar la declaración, cuando se encuentren presentes en el mismo recinto.
5. **[5] Ley 599 de 2000 (Codigo Penal), Articulo 169 (CAPITULO SEGUNDO)**
   > Artículo 169. Secuestro extorsivo. El que arrebate, sustraiga, retenga u oculte a una persona, con el propósito de exigir por su libertad un provecho o cualquier utilidad, o para que se haga u omita algo, o con fines publicitarios o de carácter político, incurrirá en prisión de trescientos veinte (320) a quinientos cuatro (504) meses y multa de dos mil seiscientos sesenta y seis punto sesenta y seis (2.666.66) a seis mil (6.000) salarios mínimos legales mensuales vigentes. Igual pena se aplicará cuando la conducta se realice temporalmente en medio de transporte con el propósito de obtener provecho económico bajo amenaza. PREGUNTA DEL USUARIO: Le compre algo usado a otra persona particular y tiene una falla que no me dijo.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | si | -- | si | -- |

Articulos citados — v1: ['137'] · v2: ['137']. Todos presentes en el contexto.

**v1.** El artículo 137 de la Ley 142 de 1994 te da derecho a la reparación o a rescindir el contrato si la falla ocurre continuamente durante quince días o más. Pide por escrito la reparación y, si no la hacen, acude a la Superintendencia de Servicios Públicos Domiciliarios. Guarda la factura, el registro de la falla y los mensajes donde te confirmaron la venta.

**v2.** El artículo 137 de la Ley 142 de 1994 te da derecho a la reparación o a rescindir el contrato si la falla ocurre continuamente durante quince días o más. Pide por escrito la reparación y, si no la dan, presenta la reclamación ante la Superintendencia de Servicios Públicos Domiciliarios. Guarda el comprobante de compra, fotos de la falla y mensajes donde confirmes la venta.

---

## Caso 2424 — Relaciones laborales

**Pregunta.** Trabajo en mision para una empresa a traves de una empresa de servicios temporales, que derechos tengo?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 180 (TITULO X)**
   > ARTÍCULO 180. Transformación de empresas existentes. Las entidades descentralizadas que estuvieren prestando los servicios a los que esta Ley se refiere, se transformarán de acuerdo a lo establecido en el artículo 17 de esta Ley, en un plazo de dos años a partir de su vigencia. Cuando se transforme una entidad descentralizada existente en una empresa de servicios públicos, en el acto que así lo disponga se preverán todas las operaciones indispensables para garantizar la continuidad del servicio así como para regular la asunción por la nueva empresa en los derechos y obligaciones de la entidad transformada. No se requerirá para ello pago de impuesto alguno por los actos y contratos necesarios para la transformación, o por su registro o protocolización. PARÁGRAFO . Se aplicará igualmente lo dispuesto en este artículo cuando la transformación y la creación de una empresa de servicios públicos se produzca por escisión de una entidad descentralizada existente.
2. **[2] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 51 (Capítulo I)**
   > ARTÍCULO 51. Auditoría Externa. Modificado por el art. 6 de la Ley 689 de 2001. Independientemente de los controles interno y fiscal, todas las empresas de servicios públicos están obligadas a contratar una auditoría externa de gestión y resultados con personas privadas especializadas. Cuando una empresa de servicios públicos quiera cambiar a sus auditores externos, deberá solicitar permiso a la Superintendencia, informándole sobre las causas que la llevaron a esa decisión. La Superintendencia podrá negar la solicitud mediante resolución motivada. La Auditoría externa obrará en función tanto de los intereses de la empresa y de sus socios como del beneficio que efectivamente reciben los usuarios y, en consecuencia, está obligada a informar a la Superintendencia las situaciones que pongan en peligro la viabilidad financiera de una empresa, las fallas que encuentren en el control interno, y en general, las apreciaciones de evaluación sobre el manejo de la empresa. En todo caso, deberán elaborar además, al menos una vez al año, una evaluación del manejo de la empresa. PARÁGRAFO . A criterio de la Superintendencia, las entidades oficiales que presten los servicios públicos de que trata la presente Ley quedarán eximidas de contratar este control si demuestran que el control fiscal e intenso de que son objeto satisface a cabalidad los requerimientos de un control eficiente.
3. **[3] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 133 (CAPITULO I)**
   > a) Se dé al suscriptor o usuario un plazo prudencial para manifestarse en forma explícita, y b) Se imponga a la empresa la obligación de hacer saber al suscriptor o usuario el significado que se atribuiría a su silencio, cuando comience el plazo aludido; 133.15. Las que permiten presumir que la empresa ha realizado un acto que la ley o el contrato consideren indispensable para determinar el alcance o la exigibilidad de las obligaciones y derechos del suscriptor o usuario; y las que la eximan de realizar tal acto; salvo en cuanto esta Ley autorice lo contrario; 133.16. Las que permiten a la empresa, en el evento de terminación anticipada del contrato por parte del suscriptor o usuario, exigir a éste: a) Una compensación excesivamente alta por el uso de una cosa o de un derecho recibido en desarrollo del contrato, o b) Una compensación excesivamente alta por los gastos realizados por la empresa para adelantar el contrato; o c) Que asuma la carga de la prueba respecto al monto real de los daños que ha podido sufrir la empresa, si la compensación pactada resulta excesiva; 133.17. Las que limitan el derecho del suscriptor o usuario a pedir la resolución del contrato, o perjuicios, en caso de incumplimiento total o parcial de la empresa;
4. **[4] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 61 (Capítulo V)**
   > La autoridad competente procederá a celebrar los contratos que sean necesarios con otras empresas de servicios públicos para que sustituyan a la empresa en proceso de liquidación o a asumir directamente en forma total o parcial las actividades que sean indispensables para asegurar la continuidad en la prestación del servicio, en concordancia con la entidad fiduciaria designada en desarrollo del proceso de toma de posesión de la empresa en liquidación. Tales contratos y acciones no se afectarán como consecuencia de las nulidades que, eventualmente, puedan declararse respecto de los demás actos relacionados con la toma de posesión o liquidación de la empresa; ni los nuevos contratistas responderán, en ningún caso, más allá de los términos de su relación contractual, por las obligaciones de la empresa en liquidación. Título V REGULACION, CONTROL Y VIGILANCIA DEL ESTADO EN LOS SERVICIOS PUBLICOS Capítulo I CONTROL SOCIAL DE LOS SERVICIOS PUBLICOS DOMICILIARIOS
5. **[5] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 141 (CAPITULO III)**
   > ARTÍCULO 141. Incumplimiento, terminación y corte del servicio. El incumplimiento del contrato por un período de varios meses, o en forma repetida, o en materias que afecten gravemente a la empresa o a terceros, permite a la empresa tener por resuelto el contrato y proceder al corte del servicio. En las condiciones uniformes se precisarán las causales de incumplimiento que dan lugar a tener por resuelto el contrato. Se presume que el atraso en el pago de tres facturas de servicios y la reincidencia en una causal de suspensión dentro de un período de dos años, es materia que afecta gravemente a la empresa, que permite resolver el contrato y proceder al corte del servicio. La entidad prestadora podrá proceder igualmente al corte en el caso de acometidas fraudulentas. Adicionalmente, y tratándose del servicio de energía eléctrica, se entenderá que para efectos penales, la energía eléctrica es un bien mueble; en consecuencia, la obtención del servicio mediante acometida fraudulenta constituirá para todos los efectos, un hurto. La demolición del inmueble en el cual se prestaba el servicio permite a la empresa dar por terminado el contrato, sin perjuicio de sus derechos. PREGUNTA DEL USUARIO: Trabajo en mision para una empresa a traves de una empresa de servicios temporales, que derechos tengo?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | -- | -- | si | -- |

Articulos citados — v1: ['141', '180'] · v2: ninguno. Todos presentes en el contexto.

**v1.** El artículo 141 de la Ley 142 de 1994 permite a la empresa cortar el servicio si hay atraso en tres facturas y reincidencia en una causal de suspensión dentro de dos años, y el artículo 180 de la misma ley obliga a las entidades descentralizadas a transformarse en empresas de servicios públicos en un plazo de dos años desde su vigencia. Pide por escrito el estado de tu cuenta y, si te cortan sin razón, presenta reclamación ante la Superintendencia de Servicios Públicos.

**v2.** No veo en estos artículos reglas para ese tipo de trabajo temporal ni para el cobro de facturas. Pide por escrito el contrato y el concepto de tu remuneración, y guarda tus horas trabajadas. Si te lo niegan, puedes acudir a la Inspección del Trabajo o a la Personería.

---

## Caso 2822 — Embargos

**Pregunta.** Me embargaron el dinero de una indemnizacion que recibi por un accidente.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 173 (CAPITULO I.)**
   > ARTICULO 173. REMUNERACION. El empleador debe remunerar el descanso dominical con el salario ordinario de un día, a los trabajadores que habiéndose obligado a prestar sus servicios en todos los días laborales de la semana, no falten al trabajo, o que, si faltan, lo hayan hecho por justa causa o por culpa o por disposición del empleador. Se entiende por justa causa el accidente, la enfermedad, la calamidad doméstica, la fuerza mayor y el caso fortuito. No tiene derecho a la remuneración del descanso dominical el trabajador que deba recibir por eso mismo día un auxilio o indemnización en dinero por enfermedad o accidente de trabajo. Para los efectos de este artículo, los días de fiesta no interrumpen la continuidad y se computan como si en ellos se hubiera prestado el servicio por el trabajador. Cuando la jornada de trabajo convenida por las partes, en días u horas, no implique la prestación de servicios en todos los días laborales de la semana, el trabajador tendrá derecho a la remuneración del descanso dominical en proporción al tiempo laborado. (Modificado por el Art. 26 de la Ley 50 de 1990) (Declarado EXEQUIBLE por la Corte Constitucional mediante Sentencia C-568-93)
2. **[2] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 216 (CAPITULO II.)**
   > ARTICULO 216. CULPA DEL EMPLEADOR. Cuando exista culpa suficiente comprobada del {empleador} en la ocurrencia del accidente de trabajo o de la enfermedad profesional, está obligado a la indemnización total y ordinaria por perjuicios pero del monto de ella debe descontarse el valor de las prestaciones en dinero pagadas en razón de las normas consagradas en este Capítulo.
3. **[3] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 218 (CAPITULO II.)**
   > ARTICULO 218. SALARIO BASE PARA LAS PRESTACIONES. Para el pago de las prestaciones en dinero establecido en este Capítulo, debe tomarse en cuenta el salario que tenga asignado el trabajador en el momento de realizarse el accidente o de diagnosticarse la enfermedad. Si el salario no fuere fijo, se toma en cuenta el promedio de lo devengado por el trabajador en el año de servicios anterior al accidente o la enfermedad, o todo el tiempo de trabajo si fuere menor.
4. **[4] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 213 (CAPITULO II.)**
   > ARTICULO 213. MUERTE POSTERIOR AL ACCIDENTE O ENFERMEDAD. Cuando la muerte del trabajador ocurriere como consecuencia y efecto natural del accidente de trabajo o de la enfermedad profesional, dentro de los dos (2) años siguientes a la ocurrencia del accidente o al diagnóstico de la enfermedad, el {empleador} a cuyo servicio se realizó el riesgo debe pagar la prestación por muerte, pero las sumas que se hubieren pagado por razón de la incapacidad permanente, total o parcial, se descontarán de la prestación por muerte. Cuando el trabajador hubiere recibido indemnización por gran invalidez, no habrá lugar al pago de la prestación por muerte. No se aplica el inciso 1o., cuando el trabajador falleciere estando asegurado por cuenta de otra empresa.
5. **[5] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 220 (CAPITULO II.)**
   > ARTICULO 220. AVISO AL JUEZ SOBRE LA OCURRENCIA DEL ACCIDENTE. Para los efectos de información en la controversia a que pueda dar lugar el accidente, cualquiera que sean sus consecuencias, el {empleador} debe dar un aviso suscrito por él o quien lo represente, al juez del trabajo del lugar, o en su defecto al juez municipal, donde conste el día, hora y lugar del accidente, como se produjo, quienes lo presenciaron, el nombre de la víctima, el salario que devengaba el día del accidente y la descripción de la lesión o perturbación, firmada por el facultativo que asista al trabajador. La información de que se trata este artículo debe darse dentro de los ocho (8) días siguientes al de la ocurrencia del accidente. PREGUNTA DEL USUARIO: Me embargaron el dinero de una indemnizacion que recibi por un accidente.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | -- | si | -- | -- |
| v2 | -- | si | -- | -- |

**v1.** No puedo decirte si ese dinero es exento: eso depende de tu situación personal y de la norma vigente sobre exenciones de ejecución. Lo que sí te digo es que puedes pedir al juez del proceso ejecutivo que se declare la exención y que se suspenda el cobro mientras se decide. Reúne la sentencia o el acuerdo, el certificado de la Comisión de Trabajo y tus actas de incapacidad.

**v2.** No puedo decirte si ese dinero es exento: eso depende de tu situación personal y de la norma vigente sobre exenciones de ejecución. Lo que sí te digo es que puedes pedirle al juez del proceso ejecutivo que revise el embargo y que, si no lo hace, puedes apelar la decisión. Reúne la sentencia o el acuerdo, el certificado de pago y tus datos personales.

---

## Caso 2823 — Embargos

**Pregunta.** Me embargaron una cuenta que ya tenia saldo en cero.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 599 de 2000 (Codigo Penal), Articulo 325-A (CAPITULO QUINTO)**
   > Articulo 325A.Omisión de Reportes Sobre Transacciones en efectivo, Movilización o Almacenamiento de Dinero en Efectivo. Aquellos sujetos sometidos a control de laUnidad de Información y Análisis Financiero (UIAF)que deliberadamente omitan el cumplimiento de los reportes aesta entidadpara las transacciones en efectivo o para la movilización o para el almacenamiento de dinero en efectivo, incurrirán, por esa sola conducta, en prisión de treinta y ocho (38) a ciento veintiocho (128) meses y multa de ciento treinta y tres punto treinta y tres (133.33) a quince mil (15.000) salarios mínimos legales mensuales vigentes. Se exceptúan de lo dispuesto en el presente artículo quienes tengan el carácterde miembro de junta directiva,representante legal, administrador o empleado de instituciones financieras o de cooperativas que ejerzan actividades de ahorro y crédito, a quienes se aplicará lo dispuesto en el artículo 325 del presente Capítulo
2. **[2] Ley 599 de 2000 (Codigo Penal), Articulo 38-A (CAPITULO PRIMERO)**
   > Artículo 38 A. Derogado
3. **[3] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 65 (CAPITULO VI.)**
   > ARTICULO 65. INDEMNIZACION POR FALTA DE PAGO. Si a la terminación del contrato, el empleador no paga al trabajador los salarios y prestaciones debidas, salvo los casos de retención autorizados por la ley o convenidos por las partes, debe pagar al asalariado, como indemnización, una suma igual al último salario diario por cada día de retardo, hasta por veinticuatro (24) meses, o hasta cuando el pago se verifique si el período es menor. Si transcurridos veinticuatro (24) meses contados desde la fecha de terminación del contrato, el trabajador no ha iniciado su reclamación por la vía ordinaria o si presentara la demanda, no ha habido pronunciamiento judicial, el empleador deberá pagar al trabajador intereses moratorios a la tasa máxima de créditos de libre asignación certificados por la Superintendencia Bancaria, a partir de la iniciación del mes veinticinco (25) hasta cuando el pago se verifique. (Inciso declarado EXEQUIBLE, salvo el aparte tachado que se declara INEXEQUIBLE, por la Corte Constitucional mediante Sentencia C-781-03) Dichos intereses los pagará el empleador sobre las sumas adeudadas al trabajador por concepto de salarios y prestaciones en dinero.
4. **[4] Ley 599 de 2000 (Codigo Penal), Articulo 429-B (CAPITULO DECIMO)**
   > Artículo 429B.Declarado Inexequible.
5. **[5] Ley 256 de 1996 (Competencia desleal), Articulo 32 (CAPITULO CUARTO)**
   > Artículo 32. Derogado. PREGUNTA DEL USUARIO: Me embargaron una cuenta que ya tenia saldo en cero.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | -- | -- |
| v2 | si | -- | -- | -- |

Articulos citados — v1: ['65'] · v2: ['65']. Todos presentes en el contexto.

**v1.** El artículo 65 del Código Sustantivo del Trabajo obliga al empleador a pagar la indemnización por falta de pago con un valor igual al último salario diario por cada día de retardo, hasta por veinticuatro meses, o hasta que se verifique el pago. Pide por escrito el pago de ese valor a la empresa y, si no lo hace, presenta la demanda ante el juez laboral.

**v2.** El artículo 65 del Código Sustantivo del Trabajo obliga al empleador a pagar una indemnización igual al último salario diario por cada día de retardo, hasta por 24 meses, y luego intereses moratorios a la tasa máxima de créditos de libre asignación. Reclama ante la Inspección del Trabajo con la liquidación y el acta de despido; si no pagan, presenta acción de tutela.

---

## Caso 2917 — Comparendos de transito

**Pregunta.** Me llego un comparendo por foto-multa y dudo que la velocidad sea correcta.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 223-A (CAPÍTULO III)**
   > 3. Aceptación ficta de responsabilidad. Expedida la orden de comparendo en la que se señala multa general, se entenderá que el infractor acepta la responsabilidad cuando, dentro de los tres (3) días siguientes a la imposición de la orden de comparendo, cancela el valor de la misma o decide cambiar el pago de las multas tipo 1 y 2 por la participación en programa comunitario o actividad comunitaria de convivencia. 4. Recibida esta información, el inspector de policía deberá abstenerse de iniciar proceso único de policía y actualizar el estado de cumplimiento de la medida correctiva en el Registro Nacional de Medidas Correctivas. 5. Firmeza de la multa señalada en orden de comparendo. No objetada, una vez vencidos los cinco (5) días posteriores a la expedición de la orden, la multa queda en firme, pudiéndose iniciar el cobro coactivo, entendiéndose que pierde los beneficios de reducción del valor de la misma establecidos en el Artículo 180 de la Ley 1801 de 2016. 6. Pérdida de beneficios. Cuando se objete la multa general señalada por el uniformado en la orden de comparendo, se pierde el derecho a los descuentos por pronto pago.
2. **[2] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 180 (CAPÍTULO II)**
   > PARÁGRAFO . Las multas serán consignadas en la cuenta que para el efecto dispongan las administraciones distritales y municipales, y se destinarán a proyectos pedagógicos y de prevención en materia de seguridad, así como al cumplimiento de aquellas medidas correctivas impuestas por las autoridades de policía cuando su materialización deba ser inmediata, sin perjuicio de las acciones que deban adelantarse contra el infractor, para el cobro de la misma. En todo caso, mínimo el sesenta por ciento (60%) del Fondo deberá ser destinado a la cultura ciudadana, pedagogía y prevención en materia de seguridad. Cuando los Uniformados de la Policía Nacional tengan conocimiento de la ocurrencia de un comportamiento, que admita la imposición de multa general, impondrán orden de comparendo al infractor, evidenciando el hecho. Es deber de toda persona natural o jurídica, sin perjuicio de su condición económica y social, pagar las multas, salvo que cumpla la medida a través de la participación en programa comunitario o actividad pedagógica de convivencia, de ser aplicable. A la persona que pague la multa durante los cinco (5) días hábiles siguientes a la expedición del comparendo, se le disminuirá el valor de la multa en un cincuenta (50%) por ciento, lo cual constituye un descuento por pronto pago.
3. **[3] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 223-A (CAPÍTULO III)**
   > ARTÍCULO 223A. Sin perjuicio del procedimiento contenido en el Artículo 223 de la Ley 1801 de 2016, para las multas por infracción a la convivencia y seguridad ciudadanas que tengan como sanción multa tipo 1 a 4, se aplicará el siguiente procedimiento: 1. Criterios para la dosificación de la medida. Será obligatorio para las autoridades de policía tener en cuenta al momento de expedir la orden de comparendo y de aplicar o imponer una medida correctiva, los principios de proporcionalidad, razonabilidad y necesidad frente al bien jurídico tutelado. 2. Término perentorio para objetar la orden de comparendo. Vencidos los 3 días hábiles posteriores a la expedición de la orden de comparendo en la que se señale Multa General, sin que se haya objetado; de conformidad con el principio de celeridad, no podrá iniciarse el proceso verbal abreviado, por cuanto se pierde la oportunidad legal establecida en el inciso quinto parágrafo del Artículo 180 de la Ley 1801 de 2016.
4. **[4] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 180 (CAPÍTULO II)**
   > A cambio del pago de la Multa General tipos 1 y 2 la persona podrá, dentro de un plazo máximo de cinco (5) días hábiles siguientes a la expedición del comparendo, solicitar a la autoridad de policía que se conmute la multa por la participación en programa comunitario o actividad pedagógica de convivencia. Si la persona no está de acuerdo con la aplicación de la multa señalada en la orden de comparendo o con el cumplimiento de la medida de participación en programa comunitario o actividad pedagógica de convivencia, cuando este aplique, podrá presentarse dentro de los tres (3) días hábiles siguientes ante la autoridad competente, para objetar la medida mediante el procedimiento establecido en este Código. La administración distrital o municipal podrá reglamentar la imposición de la medida correctiva de participación en programa comunitario o actividad pedagógica de convivencia para los comportamientos contrarios a la convivencia que admitan Multa tipos 1 y 2, en reemplazo de la multa.
5. **[5] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 180 (CAPÍTULO II)**
   > PARÁGRAFO TRANSITORIO. Durante el primer año de vigencia de la presente ley, las personas a las que se les imponga una Multa General tipos 3 o 4 podrán obtener un descuento adicional al previsto por el pronto pago de )a multa, en un porcentaje del veinticinco por ciento (25%) de su valor total, siempre y cuando soliciten a la autoridad de policía competente que se les permita participar en programa comunitario o actividad pedagógica de convivencia;? dentro de los cinco (5) días siguientes a la expedición del comparendo . (Modificado por el Art. 42 de la Ley 2197 de 2022). jurisprudencia PREGUNTA DEL USUARIO: Me llego un comparendo por foto-multa y dudo que la velocidad sea correcta.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | -- | -- |
| v2 | si | -- | si | -- |

Articulos citados — v1: ['180', '223-A'] · v2: ['180', '223-A']. Todos presentes en el contexto.

**v1.** El artículo 223A de la Ley 1801 de 2016 permite que, dentro de los tres días hábiles siguientes a la expedición del comparendo, puedes pedir que te cambien la multa por participación en un programa comunitario o actividad pedagógica de convivencia. Si no estás de acuerdo con la multa, el artículo 180 de la misma ley te da el derecho de objeción dentro de los tres días hábiles siguientes. Reúne la prueba de tu velocidad y presenta la solicitud.

**v2.** El artículo 223A de la Ley 1801 de 2016 permite objetar la orden de comparendo dentro de los tres días hábiles siguientes a su expedición, y el artículo 180 de la misma ley te da cinco días hábiles para pedir que te cambien la multa por participación en un programa comunitario. Revisa la fecha de tu comparendo, guarda la captura y presenta la objeción por escrito ante la Secretaría de Transito.

---

## Caso 3022 — Acceso a informacion publica

**Pregunta.** Cual es el correo para radicar solicitudes de informacion en la Alcaldia de Medellin?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 205 (CAPÍTULO I)**
   > 20. Crear el sistema de información que permita el registro de las personas trasladadas por protección, el cual debe contener como mínimo los nombres, identificación de la persona trasladada y circunstancias de tiempo, modo y lugar en que se materializo el traslado, dejando registro fílmico o fotográfico, mediante el uso de las tecnologías de la información y comunicación, en garantía de la protección de los derechos humanos y la dignidad humana. Este sistema e información podrá ser cofinanciado con el Gobierno Nacional. 21. Cualquier equipamiento necesario para la seguridad, convivencia y establecimientos de reclusión, constituye un determinante de superior jerarquía en los términos del Artículo 10 de la Ley 388 de 1997 y por lo tanto el respectivo alcalde distrital o municipal podrá establecer su construcción en el lugar que para el efecto determine. (Numeral 18, adicionado por el Art. 2 de la Ley 2030 de 2020) (Numerales 19, 20 y 21 adicionados por el Art. 41 de la Ley 2197 de 2022). PARÁGRAFO 1. En el departamento Archipiélago de San Andrés, Providencia y Santa Catalina conoce de la apelación, el gobernador o las autoridades administrativas, con competencias especiales de convivencia, según la materia.
2. **[2] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 121 (CAPÍTULO II)**
   > ARTÍCULO 121. Información. Es deber de la Alcaldía Distrital o Municipal establecer un mecanismo para informar de manera suficiente a la ciudadanía el lugar a donde se llevan los animales que sean sorprendidos en predios ajenos o vagando en el espacio público y establecer un sistema donde se pueda solicitar información y buscar los animales en caso de extravío. La administración distrital o municipal podrá establecer una tarifa diaria de público conocimiento, correspondiente al costo del cuidado y alimentación temporal del animal. En las ciudades capitales y en municipios con población mayor a cien mil habitantes deberá además establecerse un vínculo o un sitio en la página web de la Alcaldía en donde se registre la fotografía de cada animal encontrado para facilitar su búsqueda. La entrega de dichos animales será reglamentada por la Administración Municipal correspondiente. La información publicada en la página web cumplirá con el estándar dispuesto por el Ministerio de Tecnología de la Información y las Comunicaciones, de datos abiertos y de lenguaje para el intercambio de la misma.
3. **[3] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 205 (CAPÍTULO I)**
   > PARÁGRAFO 2. La Dirección General Marítima coadyuvará a la autoridad local competente en las medidas administrativas necesarias para la recuperación de playas y terrenos de baja mar. PARÁGRAFO TRANSITORIO. Las alcaldías tendrán un plazo de doce (12) meses a partir de la expedición de la presente Ley para crear el sistema de información que permita el registro de las personas trasladadas por protección, a que hace referencia el presente Artículo. (Parágrafo adicionado por el Art. 41 de la Ley 2197 de 2022).
4. **[4] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 183 (CAPÍTULO II)**
   > ARTÍCULO 183. Consecuencias por el no pago de multas. Si transcurridos seis meses desde la fecha de imposición de la multa, esta no ha sido pagada con sus debidos intereses, hasta tanto no se ponga al día, la persona no podrá: 1. Obtener o renovar permiso de tenencia o porte de armas. 2. Ser nombrado o ascendido en cargo público. (Declarado EXEQUIBLE mediante Sentencia de la Corte Constitucional C-093 de 2020) 3. Ingresar a las escuelas de formación de la Fuerza Pública. 4. Contratar o renovar contrato con cualquier entidad del Estado. (Declarado EXEQUIBLE mediante Sentencia de la Corte Constitucional C-054 de 2019) 5. Obtener o renovar el registro mercantil en las cámaras de comercio. (Declarado EXEQUIBLE mediante Sentencia de la Corte Constitucional C-054 de 2019) 6. Inscribirse a los concursos que apertura la Comisión Nacional del Servicio Civil. (Numeral Adicionado por el Art. 43 de la Ley 2197 de 2022) 7. Acceder a permisos que otorguen las alcaldías distritales o municipales para la venta de bienes. (Numeral Adicionado por el Art. 43 de la Ley 2197 de 2022) 8. Realizar trámites de las oficinas de tránsito y transporte. (Numeral Adicionado por el Art. 43 de la Ley 2197 de 2022) 9. Acceder al mecanismo temporal de regularización que defina el Gobierno Nacional.
5. **[5] Ley 2220 de 2022 (Estatuto de Conciliacion), Articulo 31 (CAPITULO V)**
   > ARTÍCULO 31. Deberes y Obligaciones especiales de los servidores públicos facultados para conciliar. La facultad para conciliar otorgada por la Iey a los servidores públicos es indelegable. Los servidores públicos facultados para conciliar deberán entregar a la entidad correspondiente las actas o las constancias y demás documentos aportados por las partes en el procedimiento de conciliación para su archivo, en la forma dispuesta en la Ley General de Archivo vigente. Igualmente, deberán registrar la información correspondiente a las solicitudes, procedimientos, actas y constancias de conciliación, en el sistema de información dispuesto para esos efectos, por el Ministerio de Justicia y del Derecho. También deberán proporcionar la información adicional que el Ministerio de Justicia y del Derecho, les solicite en cualquier momento. PARÁGRAFO. Para el caso de las conciliaciones extrajudiciales en materia contencioso administrativa, la información que sea requerida por el Ministerio de Justicia y del Derecho será aportada por la Procuraduría General de la Nación mediante los mecanismos que, en virtud del principio de colaboración armónica, acuerden previamente las entidades. PREGUNTA DEL USUARIO: Cual es el correo para radicar solicitudes de informacion en la Alcaldia de Medellin?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | si | si | -- |
| v2 | si | -- | si | -- |

Articulos citados — v1: ['121', '31'] · v2: ['121']. Todos presentes en el contexto.

**v1.** El artículo 121 de la Ley 1801 de 2016 obliga a la alcaldía a tener un mecanismo para informar sobre animales encontrados y extravíos, y el artículo 31 de la Ley 2220 de 2022 dice que los servidores públicos que concilian deben archivar las actas y constancias. No te digo cómo radicas porque eso depende de la alcaldía; busca su canal de atención o su página web. Si te niegan la información, puedes acudir a la Personería o a la Defensoría del Pueblo.

**v2.** El artículo 121 de la Ley 1801 de 2016 obliga a la alcaldía a tener un mecanismo para informar sobre los animales encontrados y a publicar esa información en su sitio web. Pide por derecho de petición el número de teléfono y la dirección de la guardería canina, y consulta en la página oficial de la alcaldía de Medellín.

---

## Caso 3026 — Acceso a informacion publica

**Pregunta.** En el portal de datos abiertos del gobierno esta la base de datos de los colegios publicos de mi ciudad con su presupuesto?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1266 de 2008 (Habeas data financiero), Articulo 6 (TITULO II)**
   > La administración de datos semiprivados y privados requiere el consentimiento previo y expreso del titular de los datos, salvo en el caso del dato financiero, crediticio, comercial, de servicios y el proveniente de terceros países el cual no requiere autorización del titular. En todo caso, la administración de datos semiprivados y privados se sujeta al cumplimiento de los principios de la administración de datos personales y a las demás disposiciones de la presente ley. - 2. Frente a las fuentes de la información: 2.1 Ejercer los derechos fundamentales al hábeas data y de petición, cuyo cumplimiento se podrá realizar a través de los operadores, conforme lo previsto en los procedimientos de consultas y reclamos de esta ley, sin perjuicio de los demás mecanismos constitucionales o legales. 2.2 Solicitar información o pedir la actualización o rectificación de los datos contenidos en la base de datos, lo cual realizará el operador, con base en la información aportada por la fuente, conforme se establece en el procedimiento para consultas, reclamos y peticiones. 2.3 Solicitar prueba de la autorización, cuando dicha autorización sea requerida conforme lo previsto en la presente ley. - 3. Frente a los usuarios: 3.1 Solicitar información sobre la utilización que el usuario le está dando a la información, cuando dicha información no hubiere sido suministrada por el operador.
2. **[2] Ley 1266 de 2008 (Habeas data financiero), Articulo 13 (TITULO IV)**
   > Artículo 13. Permanencia de la información. La información de carácter positivo permanecerá de manera indefinida en los bancos de datos de los operadores de información. Los datos cuyo contenido haga referencia al tiempo de mora, tipo de cobro, estado de la tartera y, en general, aquellos datos referentes a una situación de incumplimiento de obligaciones, SD regirán por un término máximo de permanencia, vencido el cual deberá ser retirada de los bancos de datos por el operador, de forma que los usuarios no puedan acceder o consultar dicha información. El término de permanencia de ésta información será el doble del tiempo de la mora, máximo cuatro (4) años contados a partir de la fecha en que sean pagadas las cuotas vencidas o sea extinguida la obligación. Parágrafo 1°. El dato negativo y los datos cuyo contenido haga referencia al tiempo de mora, tipo de cobro, estado de la cartera y, en general aquellos datos referentes a una situación de incumplimiento ele obligaciones caducarán una vez cumplido el término de ocho (8) años, contados a partir del momento en que entre en mora la obligación; cumplido este término deberán ser eliminados de la base de datos.
3. **[3] Ley 1266 de 2008 (Habeas data financiero), Articulo 4**
   > Artículo 4º. Principios de la administración de datos. En el desarrollo, interpretación y aplicación de la presente ley, se tendrán en cuenta, de manera armónica e integral, los principios que a continuación se establecen: - a) Principio de veracidad o calidad de los registros o datos. La información contenida en los bancos de datos debe ser veraz, completa, exacta, actualizada, comprobable y comprensible. Se prohíbe el registro y divulgación de datos parciales, incompletos, fraccionados o que induzcan a error; - b) Principio de finalidad. La administración de datos personales debe obedecer a una finalidad legítima de acuerdo con la Constitución y la ley. La finalidad debe informársele al titular de la información previa o concomitantemente con el otorgamiento de la autorización, cuando ella sea necesaria o en general siempre que el titular solicite información al respecto; - c) Principio de circulación restringida. La administración de datos personales se sujeta a los límites que se derivan de la naturaleza de los datos, de las disposiciones de la presente ley y de los principios de la administración de datos personales especialmente de los principios de temporalidad de la información y la finalidad del banco de datos.
4. **[4] Ley 1266 de 2008 (Habeas data financiero), Articulo 7 (TITULO III)**
   > Artículo 7º.Deberes de los operadores de los bancos de datos. Sin perjuicio del cumplimiento de las demás disposiciones contenidas en la presente leyyotras que rijan su actividad, los operadores de los bancos de datos están obligados a: - 1. Garantizar, en todo tiempo al titular de la información, el pleno y efectivo ejercicio del derecho de hábeas datayde petición, es decir, la posibilidad de conocer la información que sobre él exista o repose en el banco de datos, y solicitar la actualización o corrección de datos, todo lo cual se realizará por conducto de los mecanismos de consultas o reclamos, conforme lo previsto en la presente ley. - 2. Garantizar, que en la recolección, tratamiento y circulación de datos, se respetarán los demás derechos consagrados en la ley. - 3. Permitir el acceso a la información únicamente a las personas que, de conformidad con lo previsto en esta ley, pueden tener acceso a ella. - 4. Adoptar un manual interno de políticas y procedimientos para garantizar el adecuado cumplimiento de la presente ley y, en especial, para la atención de consultas y reclamos por parte de los titulares. - 5. Solicitar la certificación a la fuente de la existencia de la autorización otorgada por el titular, cuando dicha autorización sea necesaria, conforme lo previsto en la presente ley.
5. **[5] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 95 (CAPÍTULO IV)**
   > PARÁGRAFO 2. Corresponde a las personas naturales o jurídicas verificar que el equipo a comprar, alquilar, usar, distribuir, almacenar o vender, no se encuentre reportado como hurtado y/o extraviado en la base de datos negativa de que trata el artículo 106 de la Ley 1453 de 2011 y proceder al registro en base de datos positiva. La consulta pública de la base de datos negativa estará disponible a través del sitio web que indique la Comisión de Regulación de Comunicaciones y para el registro de los equipos terminales móviles en la base de datos positiva los proveedores deberán disponer de los medios definidos en la regulación. PARÁGRAFO 3. Quien incurra en uno o más de los comportamientos antes señalados, será objeto de la aplicación de las siguientes medidas correctivas, sin perjuicio otras medidas y sanciones establecidas en la ley: COMPORTAMIENTOS Y MEDIDA CORRECTIVA A APLICAR: Numeral 1: Multa General tipo 2; Destrucción de bien; Suspensión temporal de actividad. Numeral 2: Multa General tipo 3; Destrucción de bien; Suspensión temporal de actividad. Numeral 3: Multa General tipo 3; Destrucción debien; Suspensión definitiva de actividad. Numeral 4: Multa General tipo 3; Destrucción debien, Suspensión definitiva de actividad. Numeral 5: Multa General tipo 3; Destrucción debien, Suspensión definitiva de actividad. Numeral 6: Multa General tipo 3; Destrucción debien; Suspensión definitiva de actividad. PREGUNTA DEL USUARIO: En el portal de datos abiertos del gobierno esta la base de datos de los colegios publicos de mi ciudad con su presupuesto?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | -- | si | si | -- |

Articulos citados — v1: ['7'] · v2: ninguno. Todos presentes en el contexto.

**v1.** No es obligatorio: el artículo 7 de la Ley 1266 de 2008 dice que los operadores de los bancos de datos deben permitir el acceso a la información solo a quienes tienen derecho a ella, y el acceso a la información financiera de los entes públicos corresponde a ellos. Pide directamente al Ministerio de Educación o a la Secretaría de Educación el presupuesto del colegio, con tu derecho de petición.

**v2.** No puedo responder si esa base de datos existe: necesito verificarla antes. Lo que sí te digo es que puedes pedirla directamente al Ministerio de Educación o a la Secretaría de Educación de tu municipio, con tu nombre y número de identificación, y que la Personería puede acompañarte en la solicitud.

---

## Caso 3118 — Conciliacion prejudicial

**Pregunta.** Me piden pagar por la conciliacion, eso es normal?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 65 (CAPITULO VI.)**
   > ARTICULO 65. INDEMNIZACION POR FALTA DE PAGO. Si a la terminación del contrato, el empleador no paga al trabajador los salarios y prestaciones debidas, salvo los casos de retención autorizados por la ley o convenidos por las partes, debe pagar al asalariado, como indemnización, una suma igual al último salario diario por cada día de retardo, hasta por veinticuatro (24) meses, o hasta cuando el pago se verifique si el período es menor. Si transcurridos veinticuatro (24) meses contados desde la fecha de terminación del contrato, el trabajador no ha iniciado su reclamación por la vía ordinaria o si presentara la demanda, no ha habido pronunciamiento judicial, el empleador deberá pagar al trabajador intereses moratorios a la tasa máxima de créditos de libre asignación certificados por la Superintendencia Bancaria, a partir de la iniciación del mes veinticinco (25) hasta cuando el pago se verifique. (Inciso declarado EXEQUIBLE, salvo el aparte tachado que se declara INEXEQUIBLE, por la Corte Constitucional mediante Sentencia C-781-03) Dichos intereses los pagará el empleador sobre las sumas adeudadas al trabajador por concepto de salarios y prestaciones en dinero.
2. **[2] Ley 599 de 2000 (Codigo Penal), Articulo 125 (CAPITULO QUINTO)**
   > Artículo 125. Lesiones al feto. El que por cualquier medio causare a un feto daño en el cuerpo o en la salud que perjudique su normal desarrollo, incurrirá en prisión de treinta y dos (32) a setenta y dos (72) meses. Si la conducta fuere realizada por un profesional de la salud, se le impondrá también la inhabilitación para el ejercicio de la profesión por el mismo término. NOTA: penas aumentadas por el artículo 14 de la ley 890 de 2004 (vigencia a partir del 1° de enero de 2005)
3. **[3] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 99 (CAPITULO VII)**
   > Artículo 99.Actividades colectivas en vías públicas. La autorización de actividades colectivas en vías públicas debe ser solicitada con anticipación ante la autoridad competente. En todo caso, estas actividades no deben afectar la normal circulación de los vehículos. Para la realización de actividades deportivas en vías públicas, los responsables de ellas deben tomar las precauciones y suministrar los elementos de seguridad necesarios. El tránsito de actividades colectivas en vías públicas, será regulado por la autoridad local competente, teniendo en cuenta el señalamiento de velocidades y la utilización de vías para que no afecten la normal circulación de los vehículos. De igual manera, la autoridad regulará el tránsito durante la ocurrencia de otras actividades multitudinarias que impliquen la utilización de las vías destinadas a los vehículos.
4. **[4] Ley 2452 de 2025 (Codigo Procesal del Trabajo y de la Seguridad Social), Articulo 19 (CAPÍTULO III)**
   > Artículo 19. Conciliación. La conciliación podrá intentarse antes o después de presentada la demanda, o en cualquiera de las instancias, cuando las partes de común acuerdo lo soliciten. Por regla general, las partes deberán asistir a la audiencia de conciliación. No obstante, podrá celebrarse con la sola comparecencia de los apoderados, siempre que estos estén debidamente facultados para conciliar. La conciliación en asuntos laborales no constituye requisito de procedibilidad.
5. **[5] Ley 361 de 1997 (Integracion social de personas con discapacidad), Articulo 42 (TITULO TERCERO)**
   > Artículo 42. A partir de la vigencia de la presente ley, la Junta Directiva del Banco de la República deberá tener en cuenta que todo papel moneda y moneda metálica que se emita, deberá diferenciarse de tal manera que pueda ser fácilmente distinguible por toda persona, sea está normal o en situación de discapacidad. TITULO CUARTO DE LA ACCESIBILIDAD CAPITULO I Nociones generales PREGUNTA DEL USUARIO: Me piden pagar por la conciliacion, eso es normal?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | -- | -- | si | -- |

Articulos citados — v1: ['19'] · v2: ninguno. Todos presentes en el contexto.

**v1.** No, pagar antes de la decisión no es normal. El artículo 19 de la Ley 2452 de 2025 dice que la conciliación no es requisito de procedibilidad y que la decisión se dicta por escrito. Si te presionan, deja constancia de lo ocurrido y consulta en la Defensoría del Pueblo.

**v2.** No. La conciliación es gratuita y obligatoria solo en algunos casos, pero no impide que te cobren un consultorio o un abogado. Si te exigen pagar algo que no es de la conciliación, pídele el recibo y deja constancia de ello en la Secretaría del Trabajo o en la Personería.

---

## Caso 3122 — Conciliacion prejudicial

**Pregunta.** Cuanto dura una audiencia de conciliacion?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 2452 de 2025 (Codigo Procesal del Trabajo y de la Seguridad Social), Articulo 19 (CAPÍTULO III)**
   > Artículo 19. Conciliación. La conciliación podrá intentarse antes o después de presentada la demanda, o en cualquiera de las instancias, cuando las partes de común acuerdo lo soliciten. Por regla general, las partes deberán asistir a la audiencia de conciliación. No obstante, podrá celebrarse con la sola comparecencia de los apoderados, siempre que estos estén debidamente facultados para conciliar. La conciliación en asuntos laborales no constituye requisito de procedibilidad.
2. **[2] Ley 2452 de 2025 (Codigo Procesal del Trabajo y de la Seguridad Social), Articulo 258 (CAPÍTULO I)**
   > Artículo 258. Audiencia inicial: de conciliación, decisión de excepciones previas, saneamiento, fijación del litigio y decreto de pruebas. Contestada la demanda principal y la de reconvención si la hubiere, o cuando no hayan sido contestadas en el término legal, el juez señalará fecha y hora para que las partes comparezcan personal o virtualmente, con o sin apoderado, a audiencia pública, que será dirigida por el juez, previo el examen completo del expediente. Para efectos de esta audiencia, se observarán las siguientes reglas: A. Conciliación: Condición de incapacidad. Si alguno de los demandantes o de los demandados se encuentra en imposibilidad de ejercer su capacidad legal concurrirá quien lo represente formalmente o persona de apoyo. Excusas para no comparecer: Si antes de la hora señalada para la audiencia, alguna de las partes presenta prueba siquiera sumaria de una justa causa para no comparecer, el juez señalará nueva fecha para celebrarla, la cual será fijará dentro de los cinco (5) días siguientes a la fecha inicial, sin que pueda haber otro aplazamiento, salvo solicitud de ambas partes por tener ánimo conciliatorio.
3. **[3] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 103 (CAPITULO IV)**
   > Artículo 103.Trámite del incidente de reparación integral. Iniciada la audiencia el incidentante formulará oralmente su pretensión en contra del declarado penalmente responsable, con expresión concreta de la forma de reparación integral a la que aspira e indicación de las pruebas que hará valer. El juez examinará la pretensión y deberá rechazarla si quien la promueve no es víctima o está acreditado el pago efectivo de los perjuicios y está fuera la única pretensión formulada. La decisión negativa al reconocimiento de la condición de víctima será objeto de los recursos ordinarios en los términos de este código. Admitida la pretensión el juez la pondrá en conocimiento del condenado y acto seguido ofrecerá la posibilidad de una conciliación que de prosperar dará término al incidente. En caso contrario el juez fijará fecha para una nueva audiencia dentro de los ocho (8) días siguientes para intentar nuevamente la conciliación y de no lograrse, el sentenciado deberá ofrecer sus propios medios de prueba.
4. **[4] Ley 2452 de 2025 (Codigo Procesal del Trabajo y de la Seguridad Social), Articulo 260 (CAPÍTULO I)**
   > Parágrafo. El juez convocará a audiencia pública para tal efecto. Instalada, si concurren las partes, con o sin apoderados, los invitará para que en su presencia y bajo su vigilancia concilien sus diferencias, si fueren susceptibles de solución por este medio, de no lograrse, indicará la razón por la cual dictará sentencia anticipada y correrá traslado para alegar de conclusión. No obstante, una vez escuche los alegatos, podrá reconsiderar la decisión de proferir sentencia anticipada y se constituirá en audiencia inicial, evento en el cual se entenderá surtida la etapa de conciliación. CAPÍTULO II Segunda Instancia
5. **[5] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 522 (CAPITULO II)**
   > Artículo 522. La conciliación en los delitos querellables. La conciliación se surtirá obligatoriamente y como requisito de procedibilidad para el ejercicio de la acción penal, cuando se trate de delitos querellables, ante el fiscal que corresponda, o en un centro de conciliación o ante un conciliador reconocido como tal. En el primer evento, el fiscal citará a querellante y querellado a diligencia de conciliación. Si hubiere acuerdo procederá a archivar las diligencias. En caso contrario, ejercitará la acción penal correspondiente, sin perjuicio de que las partes acudan al mecanismo de la mediación. Si la audiencia de conciliación se realizare ante un centro o conciliador reconocidos como tales, el conciliador enviará copia del acta que así lo constate al fiscal quien procederá al archivo de las diligencias si fue exitosa o, en caso contrario, iniciará la acción penal correspondiente, si fuere procedente, sin perjuicio de que las partes acudan al mecanismo de la mediación. La inasistencia injustificada del querellante se entenderá como desistimiento de su pretensión. La del querellado motivará el ejercicio de la acción penal, si fuere procedente. En cualquier caso, si alguno de los citados fuere incapaz, concurrirá su representante legal. La conciliación se ceñirá, en lo pertinente, a lo establecido en la Ley 640 de 2001. CAPITULO III Mediación PREGUNTA DEL USUARIO: Cuanto dura una audiencia de conciliacion?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | si | -- | -- |
| v2 | -- | si | -- | -- |

Articulos citados — v1: ['19'] · v2: ninguno. Todos presentes en el contexto.

**v1.** No hay tiempo fijo: cada audiencia depende de cuántas cosas se discuten y cómo avanza. Lo que sí hay es un límite: el artículo 19 del Código Procesal del Trabajo y de la Seguridad Social dice que la conciliación no constituye requisito de procedibilidad, así que si no se logra, puedes seguir adelante sin perder tiempo.

**v2.** No hay tiempo fijo: depende de cuántas cosas quieran discutir y de cómo avance el proceso. Lo importante es que la audiencia se celebre, ya sea presencial o virtual, y que las partes estén presentes. Si te niegan la cita o te la cambian sin razón, puedes pedirlo en los descargos ante el juez procesal laboral.

---

## Caso 3124 — Conciliacion prejudicial

**Pregunta.** Puede un menor de edad participar en una conciliacion?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 599 de 2000 (Codigo Penal), Articulo 188-D (CAPITULO QUINTO)**
   > Artículo 188 D.Uso de menores de edad la comisión de delitos. El que induzca, facilite, utilice, constriña, promueva o instrumentalice a un menor de 18 años a cometer delitos o promueva dicha utilización, constreñimiento, inducción, o participe de cualquier modo en las conductas descritas, incurrirá por este solo hecho, en prisión de diez (10) a diez y veinte (20) años. El consentimiento dado por el menor de 18 años no constituirá causal de exoneración de la responsabilidad penal. La pena se aumentará de una tercera parte a la mitad si se trata de menor de 14 años de edad. La pena se aumentará de una tercera parte a la mitad en los mismos eventos agravación del artículo 188 C.
2. **[2] Ley 1098 de 2006 (Codigo de la Infancia y la Adolescencia), Articulo 149 (CAPITULO I)**
   > Artículo 149.Presunción de edad. Cuando exista duda en relación con la edad del adolescente y mientras la autoridad pericial competente lo define, se presume que es menor de 18 años. En todo caso se presumirá la edad inferior.
3. **[3] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 151 (CAPITULO II)**
   > Artículo 151. Restricciones a la publicidad por motivos de seguridad o respeto a las víctimas menores de edad. En caso de que fuere llamada a declarar una víctima menor de edad, el juez podrá limitar total o parcialmente el acceso al público o a la prensa.
4. **[4] Ley 599 de 2000 (Codigo Penal), Articulo 217-A (CAPITULO IV)**
   > Artículo 217A. Demanda de explotación sexual comercial de persona menor de 18 años de edad. El que directamente o a través de tercera persona, solicite o demande realizar acceso carnal o actos sexuales con persona menor de 18 años, mediante pago o promesa de pago en dinero, especie o retribución de cualquier naturaleza, incurrirá por este sólo hecho, en pena de prisión de catorce (14) a veinticinco (25) años. Parágrafo. El consentimiento dado por la víctima menor de 18 años, no constituirá causal de exoneración de la responsabilidad penal. La pena se agravará de una tercera parte a la mitad: - 1. Si la conducta se ejecuta por un turista o viajero nacional o extranjero. - 2. Si la conducta constituyere matrimonio o convivencia, servil o forzado. - 3. Si la conducta es cometida por un miembro de un grupo armado organizado al margen de la ley. - 4. Si la conducta se comete sobre persona menor de catorce (14) años de edad. - 5. El responsable sea integrante de la familia de la víctima.
5. **[5] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 52 (CAPÍTULO VI)**
   > Artículo 52. Protección de los niños, niñas y adolescentes en comercio electrónico. Cuando la venta se haga utilizando herramientas de comercio electrónico, el proveedor deberá tomar las medidas posibles para verificar la edad del consumidor. En caso de que el producto vaya a ser adquirido por un menor de edad, el proveedor deberá dejar constancia de la autorización expresa de los padres para realizar la transacción. PREGUNTA DEL USUARIO: Puede un menor de edad participar en una conciliacion?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | si | -- | si | -- |

Articulos citados — v1: ['149'] · v2: ['149', '151']. Todos presentes en el contexto.

**v1.** Sí puede: el artículo 149 de la Ley 1098 de 2006 dice que cuando hay duda sobre la edad del adolescente se presume que es menor de 18 años, y que en todo caso se presume la edad inferior. Si sospechas que tu hijo es menor, pide la prueba de edad en la Fiscalía y lleva a la audiencia a quien lo represente.

**v2.** El artículo 149 de la Ley 1098 de 2006 presume que quien tiene duda sobre la edad es menor de 18 años, y el artículo 151 del Código de Procedimiento Penal permite limitar el acceso al público o a la prensa cuando la víctima es menor de edad. Si sospechas que tu hijo es menor, pide la certificación de edad en la Comisaría de Familia; con esa constancia puedes pedir que te escuchen en un centro de conciliación.

---

## Caso 3228 — Contratacion estatal y facturacion

**Pregunta.** Me suspendieron el contrato con la entidad publica sin explicarme bien por que.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 388 de 1997 (Ley de Ordenamiento Territorial), Articulo 70 (CAPITULO Vlll)**
   > En caso de que se compruebe el incumplimiento de la obligación por parte de la entidad, la sentencia así lo declarará y ordenará su inscripción en la respectiva Oficina de Registro, a fin de que el demandante recupere la titularidad del bien expropiado. En la misma sentencia se determinará el valor y los documentos de deber que la persona cuyo bien fue expropiado deberá reintegrar a la entidad pública respectiva, siendo necesario para los efectos del registro de la sentencia que se acredite mediante certificación auténtica que se ha efectuado el reintegro ordenado.
2. **[2] Ley 1333 de 2009 (Procedimiento sancionatorio ambiental), Articulo 38**
   > Parágrafo 3°. El uso de los elementos decomisados se comunicará previamente a los sujetos involucrados en el trámite sancionatorio, sin que frente a esta decisión proceda recurso alguno en la vía gubernativa. El uso se suspenderá en forma inmediata en caso de que la autoridad ambiental decida levantar la medida preventiva, o por la terminación del procedimiento sancionatorio sin que se declare la responsabilidad administrativa del presunto infractor. Lo anterior, sin perjuicio de que se acuerde con el titular del bien la prolongación del uso a cualquier título en la atención de la obra o necesidad respectiva. Parágrafo 4°. A partir del momento en que se autorice el uso, la entidad pública o privada que utilice los bienes decomisados deberá hacerse cargo de los gastos de transporte, combustible, parqueadero, cuidado, impuestos y mantenimiento preventivo y correctivo que se requieran, los cuales en caso de que el procedimiento administrativo sancionatorio concluya sin la declaratoria de responsabilidad del presunto infractor, no podrán ser cobrados al titular del bien como condición para su devolución.
3. **[3] Ley 388 de 1997 (Ley de Ordenamiento Territorial), Articulo 68 (CAPITULO Vlll)**
   > Artículo 68. Decisión de la expropiación. Cuando habiéndose determinado que el procedimiento tiene el carácter de expropiación por vía administrativa, y transcurran treinta (30) días hábiles contados a partir de la ejecutoria del acto administrativo de que trata el artículo 66 de la presente ley, sin que se haya llegado a un acuerdo formal para la enajenación voluntaria contenido en un contrato de promesa de compraventa, la autoridad competente dispondrá mediante acto motivado la expropiación administrativa del bien ínmueble correspondiente, el cual contendrá lo siguiente: - 1. La identificación precisa del bien inmueble objeto de expropiación. - 2. El valor del precio indemnizatorio y la forma de pago. - 3. La destinación que se dará al inmueble expropiado, de acuerdo con los motivos de utilidad pública o de interés social que se hayan invocado y las condiciones de urgencia que se hayan declarado. - 4. La orden de inscripción del acto administrativo, una vez ejecutoriado, en la correspondiente Oficina de Registro de Instrumentos Públicos, para los efectos de que se inscriba la transferencia del derecho de dominio de su titular a la entidad que haya dispuesto la expropiación.
4. **[4] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 141 (CAPITULO III)**
   > ARTÍCULO 141. Incumplimiento, terminación y corte del servicio. El incumplimiento del contrato por un período de varios meses, o en forma repetida, o en materias que afecten gravemente a la empresa o a terceros, permite a la empresa tener por resuelto el contrato y proceder al corte del servicio. En las condiciones uniformes se precisarán las causales de incumplimiento que dan lugar a tener por resuelto el contrato. Se presume que el atraso en el pago de tres facturas de servicios y la reincidencia en una causal de suspensión dentro de un período de dos años, es materia que afecta gravemente a la empresa, que permite resolver el contrato y proceder al corte del servicio. La entidad prestadora podrá proceder igualmente al corte en el caso de acometidas fraudulentas. Adicionalmente, y tratándose del servicio de energía eléctrica, se entenderá que para efectos penales, la energía eléctrica es un bien mueble; en consecuencia, la obtención del servicio mediante acometida fraudulenta constituirá para todos los efectos, un hurto. La demolición del inmueble en el cual se prestaba el servicio permite a la empresa dar por terminado el contrato, sin perjuicio de sus derechos.
5. **[5] Ley 388 de 1997 (Ley de Ordenamiento Territorial), Articulo 61-A (CAPITULO Vll)**
   > - e) Proyectos Integrales de Desarrollo Urbano (PIDU). Los programas y/o proyectos desarrollados en función de las actuaciones de los literales a), b) y c), señalados anteriormente, deben estar localizados en municipios o distritos con población urbana superior a los quinientos mil habitantes, contar con un área superior a una (1) hectárea y cumplir con las demás condiciones que defina el Gobierno Nacional. Será procedente la concurrencia de terceros en la adquisición de inmuebles por enajenación voluntaria y expropiación, siempre que medie la celebración previa de un contrato o convenio, entre la entidad expro­piante y el tercero concurrente, en el que se prevean, por lo menos, los siguientes aspectos: - 1. El objeto del contrato o convenio contendrá la descripción y especificaciones de la actuación a ejecutar, y la determinación de los inmuebles o la parte de ellos a adquirir. - 2. La obligación clara e inequívoca de los terceros concurrentes con la entidad pública de destinar los inmuebles para los fines de utilidad pública para los que fueron adquiridos dentro de los términos previstos en la ley. - 3. La relación entre el objeto misional de la entidad competente y los motivos de utilidad pública o interés social invocados para adquirir los inmuebles. PREGUNTA DEL USUARIO: Me suspendieron el contrato con la entidad publica sin explicarme bien por que.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | -- | -- |
| v2 | si | -- | si | -- |

Articulos citados — v1: ['141'] · v2: ['68']. Todos presentes en el contexto.

**v1.** El artículo 141 de la Ley 142 de 1994 permite a la empresa cortar el servicio cuando hay incumplimiento grave, y el artículo 141 de la misma ley dice que la demolición del inmueble permite dar por terminado el contrato. Revisa tus facturas y el contrato, pide por escrito la motivación y, si no te la dan, presenta recurso de reposición y apelación.

**v2.** No veo en estos artículos la base de tu suspensión: el artículo 68 de la Ley 388 de 1997 habla de expropiación, y el 141 de la Ley 142 de 1994 de cortes por incumplimiento. Revisa el acto que te suspendió y pide copia completa; si no explica, presenta recurso de reposición y apelación. Un consultorio jurídico puede revisarlo contigo.

---

## Caso 3321 — Contratos empresariales (B2B)

**Pregunta.** Mi empresa le debe a varios proveedores y no hemos podido pagarles a tiempo.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 133 (CAPITULO I)**
   > 133.5. Las que limitan la libertad de estipulación del suscriptor o usuario en sus contratos con terceros, y las que lo obligan a comprar sólo a ciertos proveedores. Pero se podrá impedir, con permiso expreso de la comisión, que quien adquiera un bien o servicio a una empresa de servicio público a una tarifa que sólo se concede a una clase de suscriptor o usuarios, o con subsidios, lo revenda a quienes normalmente habrían recibido una tarifa o un subsidio distinto; 133.6. Las que imponen al suscriptor o usuario una renuncia anticipada a cualquiera de los derechos que el contrato le concede; 133.7. Las que autorizan a la empresa o a un delegado suyo a proceder en nombre del suscriptor o usuario para que la empresa pueda ejercer alguno de los derechos que ella tiene frente al suscriptor o usuario; 133.8. Las que obligan al suscriptor o usuario a preparar documentos de cualquier clase, con el objeto de que el suscriptor o usuario tenga que asumir la carga de una prueba que, de otra forma, no le correspondería;
2. **[2] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 148 (título valor el pago de las facturas a su cargo.)**
   > ARTÍCULO 148. Requisitos de las facturas. Modificado por el art. 38, Decreto Nacional 266 de 2000. Los requisitos formales de las facturas serán los que determinen las condiciones uniformes del contrato, pero contendrán, como mínimo, información suficiente para que el suscriptor o usuario pueda establecer con facilidad si la empresa se ciñó a la ley y al contrato al elaborarlas, cómo se determinaron y valoraron sus consumos, cómo se comparan éstos y su precio con los de períodos anteriores, y el plazo y modo en el que debe hacerse el pago. En los contratos se pactará la forma, tiempo, sitio y modo en los que la empresa hará conocer la factura a los suscriptores o usuarios, y el conocimiento se presumirá de derecho cuando la empresa cumpla lo estipulado. Corresponde a la empresa demostrar su cumplimiento. El suscriptor o usuario no estará obligado a cumplir las obligaciones que le cree la factura, sino después de conocerla. No se cobrarán servicios no prestados, tarifas, ni conceptos diferentes a los previstos en las condiciones uniformes de los contratos, ni se podrá alterar la estructura tarifaria definida para cada servicio público domiciliario. Inciso. Adicionado por el art. 75, Decreto Nacional 1122 de 1999.
3. **[3] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 39 (Capítulo II)**
   > Este contrato puede celebrarse también entre una empresa de servicios públicos y cualquiera de sus grandes proveedores o usuarios. Si las partes no se convienen, en virtud de esta Ley la comisión de regulación podrá imponer una servidumbre de acceso o de interconexión a quien tenga el uso del bien. 39.5. Contratos para la extensión de la prestación de un servicio que, en principio, sólo beneficia a una persona, en virtud del cual ésta asume el costo de las obras respectivas y se obliga a pagar a la empresa el valor definido por ella, o se obliga a ejecutar independientemente las obras requeridas conforme al proyecto aprobado por la empresa; PARÁGRAFO . Modificado por el art. 4, Ley 689 de 2001. Salvo los contratos de que trata el numeral 39.1., todos aquellos a los que se refiere este artículo se regirán por el derecho privado. Los que contemplan los numerales 39.1., 39.2. y 39.3., no podrán ser cedidos a ningún título, ni podrán darse como garantía, ni ser objeto de ningún otro contrato, sin previa y expresa aprobación de la otra parte. Cuando cualquiera de los contratos a que este capítulo se refiere permita al contratista cobrar tarifas al público, que estén sujetas a regulación, el proponente debe incluir en su oferta la fórmula tarifaria que aplicaría.
4. **[4] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 133 (CAPITULO I)**
   > a) Se dé al suscriptor o usuario un plazo prudencial para manifestarse en forma explícita, y b) Se imponga a la empresa la obligación de hacer saber al suscriptor o usuario el significado que se atribuiría a su silencio, cuando comience el plazo aludido; 133.15. Las que permiten presumir que la empresa ha realizado un acto que la ley o el contrato consideren indispensable para determinar el alcance o la exigibilidad de las obligaciones y derechos del suscriptor o usuario; y las que la eximan de realizar tal acto; salvo en cuanto esta Ley autorice lo contrario; 133.16. Las que permiten a la empresa, en el evento de terminación anticipada del contrato por parte del suscriptor o usuario, exigir a éste: a) Una compensación excesivamente alta por el uso de una cosa o de un derecho recibido en desarrollo del contrato, o b) Una compensación excesivamente alta por los gastos realizados por la empresa para adelantar el contrato; o c) Que asuma la carga de la prueba respecto al monto real de los daños que ha podido sufrir la empresa, si la compensación pactada resulta excesiva; 133.17. Las que limitan el derecho del suscriptor o usuario a pedir la resolución del contrato, o perjuicios, en caso de incumplimiento total o parcial de la empresa;
5. **[5] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 141 (CAPITULO III)**
   > ARTÍCULO 141. Incumplimiento, terminación y corte del servicio. El incumplimiento del contrato por un período de varios meses, o en forma repetida, o en materias que afecten gravemente a la empresa o a terceros, permite a la empresa tener por resuelto el contrato y proceder al corte del servicio. En las condiciones uniformes se precisarán las causales de incumplimiento que dan lugar a tener por resuelto el contrato. Se presume que el atraso en el pago de tres facturas de servicios y la reincidencia en una causal de suspensión dentro de un período de dos años, es materia que afecta gravemente a la empresa, que permite resolver el contrato y proceder al corte del servicio. La entidad prestadora podrá proceder igualmente al corte en el caso de acometidas fraudulentas. Adicionalmente, y tratándose del servicio de energía eléctrica, se entenderá que para efectos penales, la energía eléctrica es un bien mueble; en consecuencia, la obtención del servicio mediante acometida fraudulenta constituirá para todos los efectos, un hurto. La demolición del inmueble en el cual se prestaba el servicio permite a la empresa dar por terminado el contrato, sin perjuicio de sus derechos. PREGUNTA DEL USUARIO: Mi empresa le debe a varios proveedores y no hemos podido pagarles a tiempo.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | -- | si | -- | -- |

Articulos citados — v1: ['141', '148'] · v2: ninguno. Todos presentes en el contexto.

**v1.** El artículo 141 de la Ley 142 de 1994 permite a la empresa cortar el servicio si hay incumplimiento repetido o grave, y el artículo 148 de la misma ley exige que la factura indique cómo se comparan tus consumos con los anteriores. Pide por escrito el estado de cuenta y, si te cortan, interpón recurso de reposición ante la empresa y, si no lo levanta, acude a la Superintendencia de Servicios Públicos.

**v2.** No te puedo decir cuánto debes pagar a cada proveedor. Lo que sí te digo es que puedes negociar: pide a cada uno un acuerdo de pago y, si no llegas a ninguno, acude a un centro de conciliación. Si te demandan, presenta tus facturas y los pagos hechos; si hay una cláusula de mora, calcula el interés desde la fecha pactada.

---

## Caso 3327 — Contratos empresariales (B2B)

**Pregunta.** Tengo un leasing comercial y hay disputa sobre quien debe hacer el mantenimiento.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 128 (CAPITULO I)**
   > Con el objetivo de respetar el derecho de propiedad y dominio, se autoriza al organismo de tránsito correspondiente, para crear una cuenta especial, en una de las entidades financieras que existan en el lugar, donde se consignen los dineros individualizados de cada propietario o poseedor del vehículo producto de la enajenación del bien y de la cual se efectuarán las deducciones a las que esta dio lugar. Los recursos del propietario o poseedor depositados en esta cuenta, podrán ser objeto de embargo vía cobro coactivo y de existir un remanente este debe ser puesto a disposición del dueño del automotor. Los dineros no reclamados serán manejados por la entidad de carácter nacional responsable de la ejecución de la política pública de seguridad vial, su caducidad será de cinco (5) años. Cuando sobre el vehículo se haya celebrado un contrato de leasing, prenda, renting o arrendamiento sin opción de compra, se le dará al locatario, acreedor prendario o arrendatario el mismo tratamiento que al propietario para que este pueda hacer valer sus derechos en el proceso.
2. **[2] Ley 1150 de 2007 (Eficiencia y transparencia en la contratacion estatal), Articulo 2**
   > En los procesos de enajenación de los bienes del Estado se podrán utilizar instrumentos de subasta y en general de todos aquellos mecanismos autorizados por el derecho privado, siempre y cuando en desarrollo del proceso de enajenación se garantice la transparencia, la eficiencia y la selección objetiva. En todo caso, para la venta de los bienes se debe tener como base el valor del avalúo comercial y ajustar dicho avalúo de acuerdo a los gastos asociados al tiempo de comercialización esperada, administración, impuestos y mantenimiento, para determinar el precio mínimo al que se debe enajenar el bien, de conformidad con la reglamentación que para el efecto expida el Gobierno Nacional. La enajenación de los bienes que formen parte del Fondo para la Rehabilitación, Inversión Social y Lucha contra el Crimen Organizado, Frisco, se hará por la Dirección Nacional de Estupefacientes, observando los principios del artículo 209 de la Constitución Política y la reglamentación que expida el Gobierno Nacional, teniendo en cuenta las recomendaciones que para el efecto imparta el Consejo Nacional de Estupefacientes.
3. **[3] Ley 1098 de 2006 (Codigo de la Infancia y la Adolescencia), Articulo 66 (CAPITULO II)**
   > Artículo 66.Del consentimiento. El consentimiento es la manifestación informada, libre y voluntaria de dar en adopción a un hijo o hija por parte de quienes ejercen la patria potestad ante el Defensor de Familia, quien los informará ampliamente sobre sus consecuencias jurídicas y psicosociales. Este consentimiento debe ser válido civilmente e idóneo constitucionalmente. Para que el consentimiento sea válido debe cumplir con los siguientes requisitos: - 1. Que esté exento de error, fuerza y dolo y tenga causa y objeto lícitos. - 2. Que haya sido otorgado previa información y asesoría suficientes sobre las consecuencias psicosociales y jurídicas de la decisión. Es idóneo constitucionalmente cuando quien da el consentimiento ha sido debida y ampliamente informado, asesorado y tiene aptitud para otorgarlo. Se entenderá tener aptitud para otorgar el consentimiento un mes después del día del parto. A efectos del consentimiento para la adopción, se entenderá la falta del padre o la madre, no solamente cuando ha fallecido, sino también cuando lo aqueja una enfermedad mental o grave anomalía psíquica certificada por el Instituto Nacional de Medicina Legal y Ciencias Forenses.
4. **[4] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 98 (CAPITULO III.)**
   > ARTICULO 98. CONTRATO DE TRABAJO. Hay contrato de trabajo con los representantes, agentes vendedores y agentes viajeros, cuando al servicio de personas determinadas, bajo su continuada dependencia y mediante remuneración se dediquen personalmente al ejercicio de su profesión y no constituyan por si mismos una empresa comercial. Esos trabajadores deben proveerse de una licencia para ejercer su profesión, que expedirá el Ministerio de Fomento . (Subrogado por el Art. 3 del Decreto 3129 de 1956) CAPITULO IV. TRABAJADORES DE NOTARIAS PÚBLICAS Y OFICINAS DE REGISTRO DE INSTRUMENTOS PUBLICOS Y PRIVADOS.
5. **[5] Decision 486 de 2000 (Regimen Comun sobre Propiedad Industrial, CAN), Articulo 191 (TÍTULO X)**
   > Artículo 191.- El derecho exclusivo sobre un nombre comercial se adquiere por su primer uso en el comercio y termina cuando cesa el uso del nombre o cesan las actividades de la empresa o del establecimiento que lo usa. PREGUNTA DEL USUARIO: Tengo un leasing comercial y hay disputa sobre quien debe hacer el mantenimiento.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | si | -- | si | -- |

Articulos citados — v1: ['98'] · v2: ['98']. Todos presentes en el contexto.

**v1.** El artículo 98 del Código Sustantivo del Trabajo dice que el agente viajero debe proveerse de una licencia para ejercer su profesión, que expide el Ministerio de Trabajo. No veo en ese artículo la responsabilidad del mantenimiento; eso suele estar en el contrato de leasing. Revisa el contrato y el acta de entrega-recepción, y si hay divergencia, acude a un centro de conciliación o presenta demanda ante el juez civil.

**v2.** El artículo 98 del Código Sustantivo del Trabajo dice que los agentes viajeros deben proveerse de una licencia para ejercer su profesión, que expide el Ministerio de Trabajo. Esa licencia puede incluir cláusulas sobre mantenimiento. Revisa el contrato y la licencia, pide la factura del servicio y, si hay discrepancia, acude a un centro de conciliación.

---

## Caso 3328 — Contratos empresariales (B2B)

**Pregunta.** Un proveedor extranjero no cumplio una entrega internacional pactada.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 50 (CAPÍTULO VI)**
   > - h) El proveedor deberá entregar el pedido dentro del plazo acep­tado por el consumidor, el cual deberá ser informado de ma­nera previa a la finalización o terminación de cualquier tran­sacción de comercio electrónico. Si no se estableciere dicho término, se entenderá que el proveedor se obliga a entregarlo a más tardar en el plazo de treinta (30) días calendario a partir del día siguiente en que el consumidor haya comunicado su pedido. En caso de no encontrarse disponible el producto objeto del pedido, el consumidor deberá ser informado de esta falta de disponibilidad de forma inmediata por parte del proveedor y del portal de contacto. En dicho caso, el proveedor podrá establecer una segunda fecha de entrega solicitud del consumidor. Si la entrega del pedido supera el tiempo pactado por las partes o los treinta (30) días calendario, o que no haya disponible el producto adquirido, el consumidor podrá resolver o terminar, según el caso, el contrato unilateralmente y obtener la devolución en dinero de todas las sumas pagarlas sin que haya lugar a retención o descuento alguno. La devolución deberá hacerse efectiva en un plazo máximo de quince (15) días calendario.
2. **[2] Ley 599 de 2000 (Codigo Penal), Articulo 16 (CAPITULO UNICO)**
   > Artículo 16. Extraterritorialidad. La ley penal colombiana se aplicará: - 1. A la persona que cometa en el extranjero delito contra la existencia y seguridad del Estado, contra el régimen constitucional, contra el orden económico social excepto la conducta definida en el artículo 323 del presente Código, contra la administración pública, o falsifique moneda nacional o incurra en el delito de financiación de terrorismo y administración de recursos relacionados con actividades terroristas, aun cuando hubiere sido absuelta o condenada en el exterior a una pena menor que la prevista en la ley colombiana. En todo caso se tendrá como parte cumplida de la pena el tiempo que hubiere estado privada de su libertad. - 2. A la persona que esté al servicio del Estado colombiano, goce de inmunidad reconocida por el derecho internacional y cometa delito en el extranjero. - 3. A la persona que esté al servicio del Estado colombiano, no goce de inmunidad reconocida por el derecho internacional y cometa en el extranjero delito distinto de los mencionados en el numeral 1º, cuando no hubiere sido juzgada en el exterior.
3. **[3] Ley 599 de 2000 (Codigo Penal), Articulo 433 (CAPITULO ONCE)**
   > Parágrafo. Para los efectos de lo dispuesto en el presente artículo, se considera servidor público extranjero toda persona que tenga un cargo legislativo, administrativo o judicial en un Estado, sus subdivisiones políticas o autoridades locales, o una jurisdicción extranjera, sin importar si el individuo hubiere sido nombrado o elegido. También se considera servidor público extranjero toda persona que ejerza una función pública para un Estado, sus subdivisiones políticas o autoridades locales, o en una jurisdicción extranjera, sea dentro de un organismo público, o de una empresa del Estado o una entidad cuyo poder de decisión se encuentre sometido a la voluntad del Estado, sus subdivisiones políticas o autoridades locales, o de una jurisdicción extranjera. También se entenderá que ostenta la referida calidad cualquier funcionario o agente de una organización pública internacional. Nota 1: El artículo 30 de la Ley 1778 de 2016, modifico el artículo 30 de la Ley 1474 de 2011, que habia modificado el artículo 433 de la Ley 599 de 2000.
4. **[4] Ley 599 de 2000 (Codigo Penal), Articulo 457 (CAPITULO PRIMERO)**
   > Artículo 457.Traición diplomática. El que encargado por el Gobierno Colombiano de gestionar algún asunto de Estado con gobierno extranjero o con persona o con grupo de otro país o con organismo internacional, actúe en perjuicio de los intereses de la República, incurrirá en prisión de cinco (5) a quince (15) años. Si se produjere el perjuicio, la pena se aumentará hasta en una tercera parte.
5. **[5] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 46 (CAPÍTULO IV)**
   > Artículo 46. Deberes especiales del productor y proveedor El productor o proveedor que realice ventas a distancia deberá: - 1. Cerciorarse de que la entrega del bien o servicio se realice efectivamente en la dirección indicada por el consumidor y que este ha sido plena e inequívocamente identificado. - 2. Permitir que el consumidor haga reclamaciones y devoluciones en los mismos términos y por los mismos medios de la transacción original. - 3. Mantener los registros necesarios y poner en conocimiento del consumidor, el asiento de su transacción y la identidad del proveedor y del productor del bien. - 4. Informar, previo a la adquisición, la disponibilidad del producto, el derecho de retracto el término para ejercerlo, el término de duración de las condiciones comerciales y el tiempo de entrega. Parágrafo. Dentro de los seis (6) meses siguientes a la expedición de la presente ley, el Gobierno Nacional se encargará de reglamentar las ventas a distancia. PREGUNTA DEL USUARIO: Un proveedor extranjero no cumplio una entrega internacional pactada.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | si | si | -- |
| v2 | si | -- | si | -- |

Articulos citados — v1: ['46'] · v2: ['46']. Todos presentes en el contexto.

**v1.** El artículo 46 de la Ley 1480 de 2011 obliga al proveedor a entregar el pedido dentro del plazo acordado, informándote de manera previa; si no se pactó, el plazo es treinta días calendario desde que te avisaste. Pide por escrito el cumplimiento y, si no responde, presenta la queja ante la Superintendencia de Industria y Comercio.

**v2.** El artículo 46 de la Ley 1480 de 2011 exige al proveedor que entregue el pedido dentro del plazo acordado, informándolo previamente, y que permita reclamaciones y devoluciones por los mismos canales. Si no cumple, puedes terminar el contrato y pedir la devolución del dinero en un plazo de 15 días desde la notificación. Reclama por escrito y, si no responde, acude a la Superintendencia de Industria y Comercio.

---

## Caso 3423 — Derecho administrativo general

**Pregunta.** Me aplicaron una norma que creo que ya estaba derogada.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Decision 486 de 2000 (Regimen Comun sobre Propiedad Industrial, CAN), Articulo 98 (CAPÍTULO VI)**
   > Artículo 98.- El derecho exclusivo sobre un esquema de trazado registrado tendrá una duración de diez años contados a partir de la más antigua de las siguientes fechas: a) el último día del año en que se haya realizado la primera explotación comercial del esquema de trazado en cualquier lugar del mundo, o b) la fecha en que se haya presentado la solicitud de registro ante la oficina nacional competente del respectivo País Miembro. La protección de un esquema de trazado registrado caducará en todo caso al vencer un plazo de 15 años contado desde el último día del año en que se creó el esquema.
2. **[2] Ley 2220 de 2022 (Estatuto de Conciliacion), Articulo 39 (CAPÍTULO VI)**
   > ARTÍCULO 39. Actos que resuelvan de fondo el procedimiento. La decisión de no iniciar el proceso administrativo sancionatorio deberá estar debidamente motivada y se notificará en la forma establecida para el procedimiento administrativo conforme a la Ley 1437 de 2011 o la norma que lo sustituya, modifique o complemente. Las decisiones que se profieran dentro del procedimiento administrativo sancionatorio iniciado contra un centro de conciliación deberán comunicarse en la forma establecida en la Ley 1437 de 2011 o la norma que lo sustituya, modifique o complemente, para este tipo de procedimientos.
3. **[3] Decision 486 de 2000 (Regimen Comun sobre Propiedad Industrial, CAN), Articulo 97 (CAPÍTULO VI)**
   > Artículo 97.- En caso que el esquema de trazado se hubiese explotado comercialmente en cualquier lugar del mundo, la solicitud de registro deberá presentarse ante la oficina nacional competente del País Miembro dentro de un plazo de dos años contado a partir de la fecha de la primera explotación comercial del esquema. Si la solicitud se presentara después de vencido ese plazo, el registro será denegado. Un esquema de trazado que no se hubiese explotado comercialmente en ningún lugar del mundo sólo podrá registrarse si ello se solicita ante la oficina nacional competente del País Miembro dentro de un plazo de 15 años contado desde el último día del año en que se creó el esquema. Si la solicitud se presentara después de vencido ese plazo, el registro será denegado.
4. **[4] Ley 2126 de 2021 (Comisarias de Familia), Articulo 13 (CAPÍTULO III)**
   > 11. Fijar cuota provisional de alimentos de las personas adultas mayores, conforme a lo dispuesto en el Artículo 34A de la Ley 1251 de 2008 o la norma que lo adicione, sustituya, modifique o complemente. 12. Establecer las sanciones correspondientes ante el incumplimiento de cualquiera de las medidas decretadas conforme a lo establecido en el Artículo 7° de la Ley 294 de 1996 o la norma que lo adicione, sustituya, modifique o complemente. 13. Registrar en el sistema de información de Comisarías de Familia los datos requeridos y en la forma definida por el Ministerio de Justicia y del Derecho. 14. Las demás asignadas expresamente por la ley. PARÁGRAFO 1. En casos de vulneración de derecho de niños, niñas y adolescentes se preferirá el procedimiento establecido en la Ley 1098 de 2006 o la norma que la modifique o adicione, sin perjuicio de que adicionalmente se adopten las medidas de protección o las demás que sean necesarias. PARÁGRAFO 2. En los municipios donde no haya Defensor de Familia, las funciones de este serán cumplidas por el comisario o comisaria de familia, de conformidad con el Artículo 98 de la Ley 1098 de 2006 o la norma que la modifique o adicione.
5. **[5] Ley 2220 de 2022 (Estatuto de Conciliacion), Articulo 64 (CAPÍTULO II)**
   > 8. Aceptación expresa del acuerdo por las partes por cualquier mecanismo ya sea escrito, oral o virtual conforme a la normativa vigente. Cuando el acuerdo ha sido producido en una audiencia realizada por medios virtuales, la firma del acta de conciliación se aplicará lo invocado en el artículo 7 de la Ley 527 de 1999, o la norma que la modifique, sustituya o complemente. 9. Firma del conciliador. PARÁGRAFO 1. Las partes podrán solicitar copia del acta de conciliación, la cual tendrá el mismo valor probatorio. PARÁGRAFO 2. Las actas de conciliación y su contenido no requerirán ser elevadas a escritura pública, salvo expresa disposición de las partes. PREGUNTA DEL USUARIO: Me aplicaron una norma que creo que ya estaba derogada.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | -- | si | si | -- |
| v2 | -- | si | si | -- |

**v1.** No puedo decirte si esa norma sigue vigente sin verla y su estado actual. Para saberlo, consulta el Diario Oficial de Colombia y pide la respuesta por derecho de petición a la entidad que la aplicó. Si te afecta, presenta recurso de reposición y apelación y, si la aplicación sigue, demanda nulidad.

**v2.** No te respondo citando el artículo de la norma que ya no existe; eso solo lo puede decir quien la publicó. Pide por derecho de petición la actualización de la norma vigente y, mientras tanto, actúa con prudencia: guarda el documento que te citó y, si te afecta, consulta un consultorio jurídico universitario.

---

## Caso 3428 — Derecho administrativo general

**Pregunta.** Cual es el horario de atencion de la ventanilla unica de la Gobernacion de Antioquia?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 80 de 1993 (Estatuto General de Contratacion de la Administracion Publica), Articulo 81**
   > PARAGRAFO 1o. TRANSITORIO. La presente ley entrará a regir en relación con la Sociedad de Acueducto, Alcantarillado y Aseo de Barranquilla S.A., y para todo lo que tenga que ver con la prestación del servicio de agua, alcantarillado y aseo, tres (3) años después de su promulgación. PARAGRAFO 2o. TRANSITORIO. A partir de la promulgación de la presente ley, el Gobierno adelantará con la colaboración de la Escuela Superior de Administración Pública (ESAP) y de las demás entidades estatales, así como de los organismos o entidades gremiales y profesionales, actividades pedagógicas y de divulgación del presente estatuto. El Presidente del honorable Senado de la República, Jorge Ramón Elías Náder El Secretario General del honorable Senado de la República, Pedro Pumarejo Vega El Presidente de la honorable Cámara de Representantes, Francisco José Jattín Safar El Secretario General de la honorable Cámara de Representantes (E.), Humberto Zuluaga Monedero REPUBLICA DE COLOMBIA - GOBIERNO NACIONAL Publíquese y Ejecútese Santafé de Bogotá, D. C., 28 octubre de 1993 CESAR GAVIRIA TRUJILLO El Ministro de Gobierno, Fabio Villegas Ramírez El Viceministro de Hacienda y Crédito Público, encargado de las Funciones del Despacho del Ministro de Hacienda y Crédito Público, Héctor José Cadena Clavijo El Ministro de Minas y Energía, Guido Nule Amín El Ministro de Comunicaciones, William Jaramillo Gómez
2. **[2] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 490 (CAPITULO II.)**
   > ARTICULO 490. FECHA DE VIGENCIA. El presente Código principia a regir el día primero (1o) de enero del año de mil novecientos cincuenta y uno (1951).
3. **[3] Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana), Articulo 32 (CAPITULO IX)**
   > Artículo 32. Inspección, control y vigilancia de arrendamiento. La inspección, control y vigilancia, estarán a cargo de la Alcaldía Mayor de Bogotá, D. C., la Gobernación de San Andrés, Providencia y Santa Catalina y la s alcaldías municipales de los municipios del país. Parágrafo. Para los efectos previstos en la presente ley, la Alcaldía Mayor de Bogotá, D. C., establecerá la distribución funcional que considere necesaria entre la subsecretaría de control de vivienda, la secretaría general y las alcaldías locales.
4. **[4] Ley 1098 de 2006 (Codigo de la Infancia y la Adolescencia), Articulo 89 (CAPITULO III)**
   > - 16. Adelantar labores de vigilancia y control de las instituciones encargadas de ejecutar las sanciones establecidas en el presente Código, a fin de garantizar la seguridad de los niños, niñas y adolescentes y evitar su evasión. De manera excepcional, la Policía de Infancia y Adolescencia a solicitud del operador, de la autoridad judicial o administrativa podrá realizar control interno en casos de inminente riesgo en la integridad física y personal de los adolescentes o de los encargados de su cuidado personal. - 17. Prestar la logística y el recurso humano necesario para el traslado a donde haya lugar de niños, niñas y adolescentes infractores de la ley penal cuando así lo dispongan las autoridades judiciales y administrativas. El cumplimento de este numeral no excluye la corresponsabilidad de los entes territoriales. - 18. Los Comandantes de Estación de acuerdo con su competencia, podrán ordenar el cierre temporal de los establecimientos abiertos al público de acuerdo con los procedimientos señalados en el Código Nacional de Policía, en cumplimiento de las funciones establecidas en los numerales 4, 5, 6 y 7 del presente artículo, de conformidad con los principios rectores y lineamientos establecidos en este Código.
5. **[5] Ley 1150 de 2007 (Eficiencia y transparencia en la contratacion estatal), Articulo 33**
   > Artículo 33.Vigencia. La presente ley empieza a regir seis (6) meses después de su promulgación, con excepción del artículo 6° que entrará a regir a los dieciocho (18) meses de su promulgación. Parágrafo 1°. En tanto no entre en vigor el artículo 6° de la presente ley las entidades podrán verificar la información de los proponentes a que se refiere el numeral 1 del artículo 5° de la presente ley. Parágrafo 2°. Los artículos 9° y 17 entrarán a regir una vez se promulgue la presente ley. La Presidenta del honorable Senado de la República, Dilian Francisca Toro Torres. El Secretario General del honorable Senado de la República, Emilio Ramón Otero Dajud. El Presidente de la honorable Cámara de Representantes, Alfredo Ape cuello Baute. El Secretario General de la honorable Cámara de Representantes, Angelino Lizcano Rivera. REPUBLICA DE COLOMBIA – GOBIERNO NACIONAL. Publíquese y ejecútese. Dada en Bogotá, D. C., a 16 de julio de 2007. ÁLVARO URIBE VÉLEZ El Ministro del Interior y de Justicia, Carlos Holguín Sardi. El Ministro de Hacienda y Crédito Público, Oscar Iván Zuluaga Escobar. La Directora del Departamento Nacional de Planeación, Carolina Rentería. PREGUNTA DEL USUARIO: Cual es el horario de atencion de la ventanilla unica de la Gobernacion de Antioquia?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | -- | -- | si | -- |
| v2 | -- | -- | -- | -- |

**v1.** No veo en estos textos la respuesta a tu pregunta sobre horarios. La ventanilla única funciona para tramitar licencias y certificaciones ante varios entes, así que consulta directamente en ella o en la Secretaría de Gobierno de Antioquia, que suele publicar esos datos.

**v2.** No encuentro en estos textos la información sobre horarios de la Ventanilla Única de la Gobernación de Antioquia. Te sugiero consultar directamente en la página web de la entidad o llamar a su atención al ciudadano para confirmar los días y horas de atención.

---

## Caso 3517 — Derecho ambiental sancionatorio

**Pregunta.** Me multaron por no presentar un plan de manejo ambiental.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 63 (CAPÍTULO IV)**
   > 3. Presentar e implementar el plan de manejo ambiental, de acuerdo con la normatividad expedida por las autoridades competentes; de igual forma será obligación del organizador o promotor del evento retirar los materiales sobrantes, escombros, basura y mantener y/o entregar el escenario donde se realice el mismo en perfecto estado de limpieza. 4. Disponer los medios necesarios para la conformación y el funcionamiento del puesto de mando unificado, de acuerdo con lo dispuesto en la normatividad vigente. Para el inicio y desarrollo del evento, es obligatoria la presencia permanente de los organismos de prevención y atención de emergencias, desastres, o quienes hagan sus veces, y del puesto de mando unificado. Por motivos de fuerza mayor o caso fortuito, el espectáculo debe darse por terminado. 5. Ubicar el evento fuera del perímetro definido. 6. Presentar el Análisis de Riesgo de la Estructura, previa certificación de la capacidad estructural o física del lugar destinado al espectáculo, expedida por el alcalde o su delegado. 7. Disponer la venta o distribución del número de boletas que corresponda a dicho aforo. 8. Constituir las garantías bancarias o de seguros que amparen los riesgos que el evento conlleva. 9. Cumplir con las medidas sanitarias exigidas por las autoridades competentes, de acuerdo con la clase de espectáculo a desarrollar.
2. **[2] Ley 388 de 1997 (Ley de Ordenamiento Territorial), Articulo 10 (CAPITULO lll)**
   > - c) Las regulaciones sobre conservación, preservación, uso y manejo del ambiente y de los recursos naturales renovables, en especial en las zonas marinas y costeras y los ecosistemas es-tratégicos; las disposiciones producidas por la Corporación Autónoma Regional o la autoridad ambiental de la respectiva jurisdicción en cuanto a la reserva, alindamiento, administración o sustracción de los distritos de manejo integrado, los distritos de conservación de suelos, y las reservas forestales; a la reserva, alindamiento y administración de los parques naturales de carácter regional; las normas y directrices para el manejo de las cuencas hidrográficas expedidas por la Corporación Autónoma Regional o la autoridad ambiental de la respectiva jurisdicción, y las directrices y normas expedidas por las autoridades ambientales para la conservación de las áreas de especial importancia ecosistémica. - d) Las políticas, directrices y regulaciones sobre prevención de amenazas y riesgos de desastres, el señalamiento y localización de las áreas de riesgo para asentamientos humanos, así como las estrategias de manejo de zonas expuestas a amenazas y riesgos naturales, y las relacionadas con la gestión del cambio climático.
3. **[3] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 102 (CAPITULO VIII)**
   > Artículo 102. Manejo de escombros. Cada municipio determinará el lugar o lugares autorizados para la disposición final de los escombros que se produzcan en su jurisdicción, el manejo de estos materiales se hará debidamente aislado impidiendo que se disemine por las vías y de acuerdo con la normatividad ambiental vigente, bajo la responsabilidad del portador del permiso que haya otorgado la autoridad de tránsito quien será responsable del control de vigilancia del cumplimiento de la norma, sin perjuicio que se le determine la responsabilidad sobre daños en bienes de uso público. El incumplimiento de esta norma, se sancionará con multa de treinta (30) smldv. Parágrafo. Será sancionado con una multa de (30) smldv, quien transportando agregados minerales como: Arena, triturado o concretos, no aísle perfectamente la carga y permita que ella se esparza por las vías públicas, poniendo en riesgo la seguridad de otros vehículos. CAPITULO IX Protección ambiental
4. **[4] Ley 100 de 1993 (Sistema de Seguridad Social Integral), Articulo 165 (CAPITULO III)**
   > ARTICULO 165. Atención Básica. El Ministerio de Salud definirá un plan de atención básica que complemente las acciones previstas en el Plan Obligatorio de Salud de esta Ley y las acciones de saneamiento ambiental. Este plan estará constituido por aquellas intervenciones que se dirigen directamente a la colectividad o aquellas que son dirigidas a los individuos pero tienen altas externalidades, tales como la información pública, la educación y fomento de la salud, el control de consumo de tabaco, alcohol y sustancias psicoactivas, la complementación nutricional y planificación familiar, la desparasitación escolar, el control de vectores y las campañas nacionales de prevención, detección precoz y control de enfermedades transmisibles como el sida, la tuberculosis y la lepra, y de enfermedades tropicales como la malaria. La prestación del plan de atención básica será gratuita y obligatoria. La financiación de este plan será garantizada por recursos fiscales del Gobierno Nacional, complementada con recursos de los entes territoriales.
5. **[5] Ley 388 de 1997 (Ley de Ordenamiento Territorial), Articulo 99 (CAPITULO Xl)**
   > El otorgamiento de la licencia urbanística implica la adquisición de derechos de desarrollo y construcción en los términos y condiciones contenidos en el acto administrativo respectivo, así como la certificación del cumplimiento de las normas y demás reglamentaciones en que se fundamenta, y conlleva la autorización específica sobre uso y aprovechamiento del suelo en tanto esté vigente o cuando se haya cumplido con todas las obligaciones establecidas en la misma. Las modificaciones de licencias vigentes se resolverán con fundamento en las normas urbanísticas y demás reglamentaciones que sirvieron de base para su expedición. - 2. Dichas licencias se otorgarán con sujeción al Plan de Ordenamiento Territorial, planes parciales y a las normas urbanísticas que los desarrollan y complementan y de acuerdo con lo dispuesto en la Ley 99 de 1993 y en su reglamento, no se requerirá licencia o plan de manejo ambiental, cuando el plan haya sido expedido de conformidad con lo dispuesto en esta ley. PREGUNTA DEL USUARIO: Me multaron por no presentar un plan de manejo ambiental.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | -- | -- |
| v2 | -- | si | si | -- |

Articulos citados — v1: ['102', '63'] · v2: ninguno. Todos presentes en el contexto.

**v1.** El artículo 63 de la Ley 1801 de 2016 obliga al organizador a presentar el plan de manejo ambiental y a retirar los residuos, y el artículo 102 del Código Nacional de Tránsito castiga el transporte de escombros sin aislarlos. Revisa el tipo de evento y la norma aplicable: si el plan no era necesario, presenta recurso de reposición ante la autoridad que emitió la multa; si sí, concilia o demanda ante el juez administrativo.

**v2.** No tengo la norma que exige ese plan para tu actividad. Revisa en la Secretaría de Ambiente de tu municipio qué plan requiere tu actividad y cómo presentarlo; si no te lo dijeron, puedes pedirlo por derecho de petición. Con eso puedes apelar la multa ante el inspector de policía.

---

## Caso 3621 — Derecho contractual general

**Pregunta.** Mi contrato tiene el precio en dolares y con el cambio hay problemas para pagar.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 86 (CAPITULO II.)**
   > ARTICULO 86. OBLIGACIONES ESPECIALES DEL EMPLEADOR. Además de las obligaciones establecidas en el Código del Trabajo, el empleador tiene las siguientes para con el aprendiz: Facilitar todos los medios al aprendiz para que reciba formación profesional metódica y completa del arte u oficio materia del contrato. Pagar al aprendiz el salario pactado según la escala establecida en el respectivo contrato, tanto en los períodos de trabajo como en los de enseñanza, y Cumplido satisfactoriamente el término del aprendizaje, preferirlo en igualdad de condiciones para llenar las vacantes que ocurran relativas a la profesión u oficio que hubiere aprendido. (Modificado por el Art. 7 de la Ley 188 de 1959)
2. **[2] Ley 388 de 1997 (Ley de Ordenamiento Territorial), Articulo 76 (CAPITULO IX)**
   > Artículo 76. Efecto plusvalía resultado del cambio de uso. Cuando se autorice el cambio de uso a uno más rentable, el efecto plusvalía se estimará de acuerdo con el siguiente procedimiento: - 1. Se establecerá el precio comercial de los terrenos en cada una de las zonas o subzonas beneficiarias, con características geoeconómicas homogéneas, antes de la acción urbanística generadora de la plusvalía. - 2. Se determinará el nuevo precio comercial que se utilizará en cuanto base del cálculo del efecto plusvalía en cada una de las zonas o subzonas consideradas, como equivalente al precio por metro cuadrado de terrenos con características similares de uso y localización. Este precio se denominará nuevo precio de referencia. - 3. El mayor valor generado por metro cuadrado se estimará como la diferencia entre el nuevo precio de referencia y el precio comercial antes de la acción urbanística, al tenor de lo establecido en los numerales 1 y 2 de este artículo. El efecto total de la plusvalía, para cada predio individual, será igual al mayor valor por metro cuadrado multiplicado por el total de la superficie del predio objeto de la participación en la plusvalía.
3. **[3] Ley 115 de 1994 (Ley General de Educacion), Articulo 22 (SECCION TERCERA)**
   > ARTICULO 22.Objetivos específicos de la educación básica en el ciclo de secundaria. Los cuatro (4) grados subsiguientes de la educación básica que constituyen el ciclo de secundaria, tendrán como objetivos específicos los siguientes: - a) El desarrollo de la capacidad para comprender textos y expresar correctamente mensajes complejos, orales y escritos en lengua castellana, así como para entender, mediante un estudio sistemático, los diferentes elementos constitutivos de la lengua; - b) La valoración y utilización de la lengua castellana como medio de expresión literaria y el estudio de la creación literaria en el país y en el mundo; - c) El desarrollo de las capacidades para el razonamiento lógico, mediante el dominio de los sistemas numéricos, geométricos, métricos, lógicos, analíticos, de conjuntos de operaciones y relaciones, así como para su utilización en la interpretación y solución de los problemas de la ciencia, de la tecnología y los de la vida cotidiana; - d) El avance en el conocimiento científico de los fenómenos físicos, químicos y biológicos, mediante la comprensión de las leyes, el planteamiento de problemas y la observación experimental; - e) El desarrollo de actitudes favorables al conocimiento, valoración y conservación de la naturaleza y el ambiente;
4. **[4] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 195 (CAPITULO I.)**
   > ARTICULO 195. DEFINICION Y PRUEBA DEL CAPITAL DE LA EMPRESA. Para los efectos de este Código se entiende por capital de la empresa el valor del patrimonio gravable declarado en el año inmediatamente anterior según prueba que debe presentar el {empleador}. En caso de no presentarla se presume que tiene el capital necesario para pagar la totalidad de la prestación demandada. El capital que se debe tomar en cuenta es el de la empresa y no el de la persona natural o jurídica a la cual pertenezca.
5. **[5] Ley 388 de 1997 (Ley de Ordenamiento Territorial), Articulo 71 (CAPITULO Vlll)**
   > - 8. Si la sentencia decide, conforme a la demanda, sobre el precio indemnizatorio reconocido por la administración, dispondrá si hay lugar a una elevación del valor correspondiente o a una modificación de la forma de pago. En este caso, las determinaciones que se hagan en el auto de liquidación de la sentencia, tendrán en cuenta el nuevo precio indemnizatorio y la diferente modalidad de pago. PREGUNTA DEL USUARIO: Mi contrato tiene el precio en dolares y con el cambio hay problemas para pagar.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | si | -- | -- |
| v2 | -- | si | -- | -- |

Articulos citados — v1: ['195'] · v2: ninguno. Todos presentes en el contexto.

**v1.** No puedo decirte cómo se calcula el cambio. El artículo 195 del Código Sustantivo del Trabajo toma como capital el valor del patrimonio gravable del año anterior, según la prueba que presenta el empleador, y no el de la persona natural o jurídica que lo tenga. Pide por escrito al empleador esa prueba y, si no la presenta, cita a conciliación o demanda ante el juez laboral.

**v2.** No puedo decirte cómo se calcula el cambio ni si tu contrato se ajusta por él; eso depende de la cláusula específica. Lo que sí te digo es que puedes negociar la forma de pago con el otro lado y, si no hay acuerdo, acudir a un centro de conciliación o demandar ante el juez civil. Guarda el contrato, los recibos y los correos donde se discutió la forma de pago.

---

## Caso 3626 — Derecho contractual general

**Pregunta.** Mi contrato ya vencio pero seguimos actuando como si siguiera vigente.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 2452 de 2025 (Codigo Procesal del Trabajo y de la Seguridad Social), Articulo 117 (CAPÍTULO X)**
   > Artículo 117. Causales de interrupción. El proceso o la actuación posterior a la sentencia se interrumpirá: 1. Por muerte, enfermedad grave o privación de la libertad de la parte que no haya estado actuando por conducto de apoderado judicial, representante o curador ad litem. 2. Por muerte, enfermedad grave o privación de la libertad del apoderado judicial de alguna de las partes, o por inhabilidad, exclusión o suspensión en el ejercicio de la profesión de abogado. Cuando la parte tenga varios apoderados para el mismo proceso, la interrupción solo se producirá si el motivo afecta a todos los apoderados constituidos. 3. Por muerte, enfermedad grave o privación de la libertad del representante o curador ad litem que esté actuando en el proceso y que carezca de apoderado judicial. La interrupción se producirá a partir del hecho que la origine, pero si este sucede estando el expediente al despacho, surtirá efectos a partir de la notificación de la providencia que se pronuncie seguidamente. Durante la interrupción no correrán los términos y no podrá ejecutarse ningún acto procesal, con excepción de las medidas urgentes y de aseguramiento.
2. **[2] Ley 100 de 1993 (Sistema de Seguridad Social Integral), Articulo 36 (CAPITULO II)**
   > Parágrafo 2º. Para los efectos de la presente ley, se respetarán y garantizarán integralmente los derechos adquiridos a quienes tienen la calidad de pensionados de jubilación, vejez, invalidez, sustitución y sobrevivencia en los diferentes órdenes, sectores y regímenes, así como a quienes han cumplido ya con los requisitos exigidos por la ley para adquirir la pensión, pero no se les ha reconocido.
3. **[3] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 366 (CAPITULO III.)**
   > c) Cuando se trate de la inscripción de un nuevo sindicato de empresa, en una donde ya existiera organización de esta misma clase. Literal INEXEQUIBLE PARAGRAFO. El incumplimiento injustificado de los términos previstos en el presente artículo hará incurrir al funcionario responsable en causal de mala conducta sancionable con arreglo al régimen disciplinario vigente. (Modificado por el Art. 46 de la Ley 50 de 1990)
4. **[4] Ley 2452 de 2025 (Codigo Procesal del Trabajo y de la Seguridad Social), Articulo 81 (CAPÍTULO I)**
   > El incumplimiento de este deber no afecta la validez de la actuación, pero la parte afectada podrá solicitar al juez la imposición de una multa hasta por un (1) salario mínimo legal mensual vigente (SMLMV) por cada infracción.
5. **[5] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 38 (CAPITULO IV.)**
   > ARTICULO 38. CONTRATO VERBAL. Cuando el contrato sea verbal, el {empleador} y el trabajador deben ponerse de acuerdo, al menos acerca de los siguientes puntos: 1. La índole del trabajo y el sitio en donde ha de realizarse; 2. La cuantía y forma de la remuneración, ya sea por unidad de tiempo, por obra ejecutada, por tarea, a destajo u otra cualquiera, y los períodos que regulen su pago; 3. La duración del contrato. (Modificado por el Art. 1 del Decreto 617 de 1954) PREGUNTA DEL USUARIO: Mi contrato ya vencio pero seguimos actuando como si siguiera vigente.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | si | -- | -- |
| v2 | si | si | -- | -- |

Articulos citados — v1: ['38'] · v2: ['38']. Todos presentes en el contexto.

**v1.** El artículo 38 del Código Sustantivo del Trabajo exige que el contrato verbal se pacte sobre la remuneración, entre otros puntos. Si no se pactó, la remuneración se calcula según lo que realmente hiciste, con pruebas de lo que hiciste y cuándo. Puedes reclamar ante la Inspección del Trabajo o demandar ante el juez laboral.

**v2.** El artículo 38 del Código Sustantivo del Trabajo exige que el contrato verbal se pacte sobre la remuneración, entre otros puntos. Si no se acordó nada, la remuneración se calcula por unidad de tiempo, por obra o por tarea, según corresponda. Puedes pedir por escrito la liquidación y, si no responden, demandar ante el juez laboral.

---

## Caso 3628 — Derecho contractual general

**Pregunta.** Firme un contrato sin entender bien una clausula tecnica.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 41 (CAPÍTULO II)**
   > Artículo 41. Cláusula de permanencia mínima. La cláusula de permanencia mínima en los contratos de tracto sucesivo solo podrá ser pactada de forma expresa cuando el consumidor obtenga una ventaja sustancial frente a las condiciones ordinarias del contrato, tales como cuando se ofrezcan planes que subsidien algún costo o gasto que deba ser asumido por el consumidor, dividan el pago de bienes en cuotas o cuando se incluyan tarifas especiales que impliquen un descuento sustancial, y se pactarán por una sola vez, al inicio del contrato. El período de permanencia mínima no podrá ser superior a un año, a excepción de lo previsto en los parágrafos 1° y 2°. El proveedor que ofrezca a los potenciales consumidores una modalidad de contrato con cláusula de permanencia mínima, debe también ofrecer una alternativa sin condiciones de permanencia mínima, para que el consumidor pueda comparar las condiciones y tarifas de cada una de ellas y decidir libremente. En caso de que el consumidor dé por terminado el contrato estando dentro del término de Vigencia de la cláusula de permanencia mínima solo está obligado a paga el valor proporcional del subsidio otorgado por los periodos de facturación que le hagan falta para su vencimiento.
2. **[2] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 41 (CAPÍTULO II)**
   > En caso de prorrogarse automáticamente el contrato una vez vencido el término de la cláusula mínima de permanencia, el consumidor tendrá derecho a terminar el contrato en cualquier momento durante la vigencia de la prórroga sin que haya lugar al pago de sumas relacionadas con la terminación anticipada del contrato, salvo que durante dicho periodo se haya pactado una nueva cláusula de permanencia mínima en aplicación de lo previsto en el parágrafo 1° del presente artículo. Parágrafo 1°. Solo podrá pactarse una nueva cláusula de permanencia mínima, cuando el proveedor ofrezca al consumidor unas nuevas condiciones que representen una ventaja sustancial a las condiciones ordinarias del contrato. Parágrafo 2°. La Superintendencia de Industria y Comercio podrá instruir la forma en que se deberá presentar a los consumidores la información sobre las cláusulas mínimas de permanencia y las cláusulas de prórroga automática. También podrá fijar períodos de permanencia mínima diferentes a un año, cuando las condiciones del mercado así lo requieran. CAPÍTULO III Cláusulas Abusivas
3. **[3] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 44 (CAPÍTULO III)**
   > Artículo 44. Efectos de la nulidad o de la ineficacia. La nulidad o ineficacia de una cláusula no afectará la totalidad del contrato, en la medida en que este pueda subsistir sin las cláusulas nulas o ineficaces. Cuando el contrato subsista, la autoridad competente aclarará cuáles serán los derechos y obligaciones que se deriven del contrato subsistente. CAPÍTULO IV De las operaciones mediante sistemas de financiación
4. **[4] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 133 (CAPITULO I)**
   > Cuando una comisión haya rendido concepto previo sobre un contrato de condiciones uniformes, o sobre sus modificaciones, el juez que lo estudie debe dar a ese concepto el valor de una prueba pericial firme, precisa, y debidamente fundada. CAPITULO II DE LA PRESTACION DEL SERVICIO
5. **[5] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 144 (CAPITULO I)**
   > Artículo 144. Idioma. El idioma oficial en la actuación será el castellano. El imputado, el acusado o la víctima serán asistidos por un traductor debidamente acreditado o reconocido por el juez en caso de no poder entender o expresarse en el idioma oficial; o por un intérprete en caso de no poder percibir el idioma por los órganos de los sentidos o hacerse entender oralmente. Lo anterior no obsta para que pueda estar acompañado por uno designado por él. PREGUNTA DEL USUARIO: Firme un contrato sin entender bien una clausula tecnica.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | si | -- | -- | -- |

Articulos citados — v1: ['44'] · v2: ['44']. Todos presentes en el contexto.

**v1.** No te sientas solo: el artículo 44 de la Ley 1480 de 2011 dice que la nulidad de una cláusula no anula todo el contrato, y que la autoridad competente aclara qué quedó. Pide por escrito a la empresa que te explique la cláusula y, si no te la quieren explicar, presenta querella ante la Fiscalía por interpretación errónea.

**v2.** No te sientas solo: el artículo 44 de la Ley 1480 de 2011 dice que la nulidad de una cláusula no afecta toda la relación, y que la autoridad aclarará qué queda. Pide por escrito a la empresa que te explique qué significa esa cláusula técnica y cómo se aplica, y guarda el contrato con tu firma. Si no responden, acude a un centro de conciliación.

---

## Caso 3729 — Derecho de familia - alimentos

**Pregunta.** Mi hijo se independizo pero volvio a vivir con nosotros, sigue aplicando la cuota alimentaria?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 388 de 1997 (Ley de Ordenamiento Territorial), Articulo 116 (CAPITULO XIII)**
   > Artículo 116. Procedimiento de la acción de cumplimiento. Toda persona, directamente o a través de un apoderado, podrá acudir ante la autoridad judicial para hacer efectivo el cumplimiento de una ley o acto administrativo relacionado con la aplicación de los instrumentos previstos en la Ley 9º de 1989 y la presente ley. La acción de cumplimiento se dirigirá contra la autoridad administrativa que presuntamente no esté aplicando la ley o el acto administrativo. Si su no aplicación se debe a órdenes o instrucciones impartidas por un superior, la acción se entenderá dirigida contra ambos aunque podrá incoarse directamente contra el jefe o Director de la entidad pública a la que pertenezca el funcionario renuente. Esta acción se podrá ejercitar sin perjuicio de las demás acciones que la ley permita y se deberá surtir el siguiente trámite:
2. **[2] Ley 2220 de 2022 (Estatuto de Conciliacion), Articulo 5 (CAPITULO II)**
   > ARTÍCULO 5. Clases. La conciliación podrá ser judicial, si se realiza dentro de un proceso judicial, o extrajudicial, sí se realiza antes o por fuera de un proceso judicial. La conciliación extrajudicial se denominará en derecho, cuando se realice a través de centros de conciliación, ante particulares autorizados para conciliar que cumplen función pública o ante autoridades en cumplimiento de funciones conciliatorias. La conciliación extrajudicial se denominará en equidad cuando se realice ante conciliadores en equidad aplicando principios de justicia comunitaria dentro del ámbito establecido por la ley.
3. **[3] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 60 (CAPÍTULO IV)**
   > Artículo 60. Procedimiento. Las sanciones administrativas serán impuestas previa investigación, de acuerdo con el procedimiento establecido en el Código Contencioso Administrativo. Parágrafo. Las actuaciones administrativas relacionadas con el ejercicio de las facultades a las que se refiere este capítulo, podrán surtirse aplicando medios electrónicos o tecnologías de la información y la comunicación, de conformidad con las disposiciones legales vigentes.
4. **[4] Ley 1150 de 2007 (Eficiencia y transparencia en la contratacion estatal), Articulo 7**
   > Las garantías no serán obligatorias en los contratos de empréstito, en los interadministrativos, en los de seguro y en los contratos cuyo valor sea inferior al 10% de la menor cuantía a que se refiere esta ley, caso en el cual corresponderá a la entidad determinar la necesidad de exigirla, atendiendo a la naturaleza del objeto del contrato y a la forma de pago, así como en los demás que señale el reglamento. Parágrafo Transitorio. Durante el período que transcurra entre la entrada en vigencia de la reforma contenida en la presente ley y la expedición del decreto reglamentario a que se refiere este artículo, las entidades estatales continuarán aplicando las normas legales y reglamentarias vigentes.
5. **[5] Ley 1266 de 2008 (Habeas data financiero), Articulo 12 (TITULO IV)**
   > Parágrafo. El incumplimiento de la comunicación previa al titular de la información, en los casos en que la obligación o cuota ya haya sido extinguida, dará lugar al retiro inmediato del reporte negativo. En los casos en que se genere el reporte sin el cumplimiento de la comunicación y no se haya extinguido la obligación o cuota, se deberá retirar el reporte y cumplir con la comunicación antes de realizarlo nuevamente. PREGUNTA DEL USUARIO: Mi hijo se independizo pero volvio a vivir con nosotros, sigue aplicando la cuota alimentaria?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | -- | -- |
| v2 | si | -- | -- | -- |

Articulos citados — v1: ['116', '60'] · v2: ['116', '5']. Todos presentes en el contexto.

**v1.** El artículo 60 de la Ley 1480 de 2011 dice que las sanciones administrativas se imparten después de una investigación, y el artículo 116 de la Ley 388 de 1997 permite pedir el cumplimiento de una ley o acto administrativo. Reúne el certificado de independización, el registro civil y los recibos de gastos, y presenta la acción de cumplimiento ante el juez administrativo.

**v2.** El artículo 116 de la Ley 388 de 1997 permite pedir el cumplimiento de una ley o acto administrativo ante la autoridad judicial si se deja de aplicarlo, y el artículo 5 de la Ley 2222 de 2022 habilita la conciliación extrajudicial ante conciliadores autorizados. Pide por escrito al juez de familia la revisión de la cuota y, si no responden, acude a la audiencia de conciliación y luego al juez.

---

## Caso 3822 — Educacion / debido proceso disciplinario

**Pregunta.** La universidad me quito la beca sin explicarme bien por que.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 18 (CAPÍTULO II)**
   > Parágrafo. Pasado un (1) mes a partir de la fecha prevista para la devolución o a la fecha en que el consumidor debía aceptar o rechazar expresamente el servicio, de conformidad con lo previsto en el numeral 1 anterior sin que el consumidor acuda a retirar el bien, el prestador del servicio lo requerirá para que lo retire dentro de los dos (2) meses siguientes a la remisión de la comunicación. Si el consumidor no lo retira se entenderá por ley que abandona el bien y el prestador del servicio deberá disponer del mismo conforme con la reglamentación que expida el Gobierno Nacional para el efecto. Sin perjuicio del derecho de retención, el prestador del servicio no podrá lucrarse económicamente del bien, explotarlo, transferir el dominio o conservarlo para sí mismo. No obstante lo anterior, el consumidor deberá asumir los costos asociados al abandono del bien, tales como costos de almacenamiento bodegaje y mantenimiento. TÍTULO IV RESPONSABILIDAD POR DAÑOS POR PRODUCTO DEFECTUOSO CAPÍTULO ÚNICO De la responsabilidad por daños por producto defectuoso
2. **[2] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 8 (CAPÍTULO I)**
   > Artículo 8°. Término de la garantía legal. El término de la garantía legal será el dispuesto por la ley o por la autoridad competente. A falta de disposición de obligatorio cumplimiento, será el anunciado por el productor y/o proveedor. El término de la garantía legal empezará a correr a partir de la entrega del producto al consumidor. De no indicarse el término de garantía, el término será de un año para productos nuevos. Tratándose de productos perecederos, el término de la garantía legal será el de la fecha de vencimiento o expiración. Los productos usados en los que haya expirado el término de la garantía legal podrán ser vendidos sin garantía, circunstancia que debe ser informada y aceptada por escrito claramente por el consumidor. En caso contrario se entenderá que el producto tiene garantía de tres (3) meses. La prestación de servicios que suponen la entrega del bien para la reparación del mismo podrá ser prestada sin garantía, circunstancia que debe ser informada y aceptada por escrito claramente por el consumidor. En caso contrario se entenderá que el servicio tiene garantía de tres (3) meses, contados a partir de la entrega del bien a quien solicitó el servicio.
3. **[3] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 18 (CAPÍTULO II)**
   > - 2. Quien preste el servicio asume la custodia y conservación adecuada del bien y, por lo tanto, de la integridad de los elementos que lo componen, así como la de sus equipos anexos o complementarios, si los tuviere. - 3. En la prestación del servicio de parqueadero la persona natural o jurídica que preste el servicio deberá expedir un recibo del bien en el cual se mencione la fecha y hora de la recepción, la identificación del bien, el estado en que se encuentra y el valor del servicio en la modalidad en que se preste. Para la identificación y el estado en que se recibe el bien al momento del ingreso, podrá utilizarse medios tecnológicos que garanticen el cumplimiento de esta obligación. Cuando se trate de zonas de parqueo gratuito, el prestador del servicio responderá por los daños causados cuando medie dolo o culpa grave.
4. **[4] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 34 (CAPÍTULO II)**
   > 6. Facilitar o distribuir sustancias psicoactivas -incluso la dosis personal- en el área circundante a las instituciones o centros educativos, de conformidad con el perímetro establecido por el alcalde y la reglamentación de la que habla el parágrafo 3 del presente artículo. (Numeral 6, adicionado por el Art. 2 de la Ley 2000 de 2019) PARÁGRAFO 1. Los niños, niñas y adolescentes que cometan alguno de los comportamientos señalados en los numerales anteriores serán objeto de las medidas dispuestas en la Ley 1098 de 2006 y demás normas vigentes en la materia. También procederá la medida de destrucción del bien, cuando haya lugar. (Parágrafo 1, modificado por el Art. 2 de la Ley 2000 de 2019) PARÁGRAFO 2. La persona mayor de edad que incurra en uno o más de los comportamientos antes señalados, será objeto de la aplicación de las siguientes medidas correctivas, sin perjuicio de lo establecido en los reglamentos internos de cada establecimiento educativo ni de la responsabilidad penal que se genere bajo el Título XIII del Código Penal. COMPORTAMIENTOS Y MEDIDA CORRECTIVA A APLICAR: Numeral 1: Multa General tipo 3; Destrucción de bien Numeral 2: Multa General tipo 4; Destrucción de bien Numeral 3: Multa General tipo 4; Destrucción de bien Numeral 4: Multa General tipo 4; Destrucción de bien; Suspensión temporal de actividad
5. **[5] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 58 (CAPÍTULO I)**
   > - a) Cuando la pretensión principal sea que se cumpla con la garantía, se repare el bien o servicio, se cambie por uno nuevo de similares características, se devuelva el dinero pagado o en los casos de prestación de servicios que suponen la entrega de un bien, cuando el bien sufra deterioro o pérdida, la reposición del mismo por uno de similares características o su equivalente en dinero, se deberá identificar el producto, la fecha de adquisición o prestación del servicio y las pruebas del defecto. Cuando la reclamación sea por protección contractual o por información o publicidad engañosa, deberá anexarse la prueba documental e indicarse las razones de inconformidad. - b) La reclamación se entenderá presentada por escrito cuando se utilicen medios electrónicos. Quien disponga de la vía telefónica para recibir reclamaciones, deberá garantizar que queden grabadas. En caso de que la reclamación sea verbal, el productor o proveedor deberá expedir constancia escrita del recibo de la misma, con la fecha de presentación y el objeto de reclamo. El consumidor también podrá remitir la reclamación mediante correo con constancia de envío a la dirección del establecimiento de comercio donde adquirió el producto y/o a la dirección del productor del bien o servicio. PREGUNTA DEL USUARIO: La universidad me quito la beca sin explicarme bien por que.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | si | si | si | -- |

Articulos citados — v1: ['58'] · v2: ['8']. Todos presentes en el contexto.

**v1.** El artículo 58 de la Ley 1480 de 2011 exige que, cuando reclames por protección contractual, indiques las razones de inconformidad y anexes la prueba documental. Pide por escrito la motivación y, si no te la dan, presenta la reclamación ante la Secretaría de Educación o la Defensoría del Pueblo; si la decisión afecta tu derecho a estudiar, la acción de tutela es la vía.

**v2.** El artículo 8 de la Ley 1480 de 2011 dice que el término de la garantía legal es el que anuncia el productor, y que si no se indica es de un año para productos nuevos. Pide por escrito la decisión y su fundamento, con el registro de tu matrícula y los recibos de pago. Si no te la dan, puedes demandar ante la Personería o la Defensoría del Pueblo.

---

## Caso 3920 — Licencias urbanisticas

**Pregunta.** Me niegan la licencia por falta de certificado de disponibilidad de servicios publicos.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 35 (CAPITULO IV)**
   > Artículo 35.Expedición. La licencia de tránsito será expedida por cualquier organismo de tránsito o por quien él designe, previa entrega de los siguientes documentos: Factura de compra si el vehículo es de fabricación nacional. Factura de compra en el país de origen y licencia de importación. Recibo de pago de impuestos. Certificado de inscripción ante el RUNT.
2. **[2] Decision 486 de 2000 (Regimen Comun sobre Propiedad Industrial, CAN), Articulo 162 (CAPÍTULO IV)**
   > Artículo 162.- El titular de una marca registrada o en trámite de registro podrá dar licencia a uno o más terceros para la explotación de la marca respectiva. Deberá registrarse ante la oficina nacional competente toda licencia de uso de la marca. La falta de registro ocasionará que la licencia no surta efectos frente a terceros. A efectos del registro, la licencia deberá constar por escrito. Cualquier persona interesada podrá solicitar el registro de una licencia.
3. **[3] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 25 (Capítulo I)**
   > ARTÍCULO 25. Concesiones, y permisos ambientales y sanitarios. Quienes presten servicios públicos requieren contratos de concesión, con las autoridades competentes según la ley, para usar las aguas; para usar el espectro electromagnético en la prestación de servicios públicos requerirán licencia o contrato de concesión. Deberán además, obtener los permisos ambientales y sanitarios que la índole misma de sus actividades haga necesarios, de acuerdo con las normas comunes. Asimismo, es obligación de quienes presten servicios públicos, invertir en el mantenimiento y recuperación del bien público explotado, a través de contratos de concesión. Si se trata de la prestación de los servicios de agua potable o saneamiento básico, de conformidad con la distribución de competencias dispuesta por la ley, las autoridades competentes verificarán la idoneidad técnica y solvencia financiera del solicitante para efectos de los procedimientos correspondientes.
4. **[4] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 17 (CAPITULO II)**
   > La licencia de conducción digital deberá guardar el registro de las sanciones y demás anotaciones asociadas a la licencia, permitiéndole la identificación, autenticación y consulta al conductor y a las autoridades en el marco de sus competencias, sin costo alguno. El Ministerio de Transporte garantizará la interoperabilidad, firma digital y consulta con todos los sistemas de información que lo requieran. Parágrafo. Las autoridades de tránsito, organismos de tránsito y agentes de tránsito deberán dar por cumplida la obligación de portar los documentos como: documento de identidad, licencia de conduc­ción, licencia de tránsito, seguro Obligatorio de Accidentes de Tránsito (SOAT) y certificado de revisión técnico mecánica y de gases, mediante la consulta en los Sistemas de Información establecidos por la autoridad de tránsito competente, sin que sea exigible su presentación en físico.
5. **[5] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 24 (CAPITULO II)**
   > Artículo 24.Recategorización. El titular de una licencia de conducción podrá solicitar ante un organismo de tránsito o la entidad pública o privada por él autorizada, la recategorización de su licencia, para lo cual debe presentar y aprobar un nuevo examen teórico-práctico para la categoría solicitada y presentar un certificado de aptitud en conducción otorgado por el centro respectivo, y su trámite no podrá durar más de 72 horas una vez aceptada la documentación. PREGUNTA DEL USUARIO: Me niegan la licencia por falta de certificado de disponibilidad de servicios publicos.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | si | -- | -- | -- |

Articulos citados — v1: ['25'] · v2: ['25']. Todos presentes en el contexto.

**v1.** El artículo 25 de la Ley 142 de 1994 dice que quienes presten servicios públicos deben obtener los permisos ambientales y sanitarios que la naturaleza de sus actividades exigen. Pide por escrito al organismo de tránsito el motivo exacto de la negativa y, si no te lo explica, interpón recurso de reposición y apelación; la Personería puede orientarte. Reúne tu facturación, la matrícula y el registro del vehículo.

**v2.** El artículo 25 de la Ley 142 de 1994 exige que los prestadores de servicios públicos obtengan los permisos ambientales y sanitarios que la naturaleza de sus actividades requiera. Pide por escrito al organismo de tránsito el certificado de disponibilidad y, si te lo niegan, interpón recurso de reposición y apelación; si no lo entregan, presenta acción de tutela.

---

## Caso 4026 — Penal basico y derechos de las victimas

**Pregunta.** cuanto cuesta sacar el certificado de antecedentes para un trabajo

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1098 de 2006 (Codigo de la Infancia y la Adolescencia), Articulo 113 (CAPITULO IV)**
   > Artículo 113. Autorización de trabajo para los adolescentes. Corresponde al inspector de trabajo expedir por escrito la autorización para que un adolescente pueda trabajar, a solicitud de los padres, del respectivo representante legal o del Defensor de Familia. A falta del inspector del trabajo la autorización será expedida por el comisario de familia y en defecto de este por el alcalde municipal. La autorización estará sujeta a las siguientes reglas: - 1. Deberá tramitarse conjuntamente entre el empleador y el adolescente; - 2. La solicitud contendrá los datos generales de identificación del adolescente y del empleador, los términos del contrato de trabajo, la actividad que va a realizar, la jornada laboral y el salario. - 3. El funcionario que concedió el permiso deberá efectuar una visita para determinar las condiciones de trabajo y la seguridad para la salud del trabajador. - 4. Para obtener la autorización se requiere la presentación del certificado de escolaridad del adolescente y si este no ha terminado su formación básica, el empleador procederá a inscribirlo y, en todo caso, a facilitarle el tiempo necesario para continuar el proceso educativo o de formación, teniendo en cuenta su orientación vocacional. - 5. El empleador debe obtener un certificado de estado de salud del adolescente trabajador.
2. **[2] Ley 1098 de 2006 (Codigo de la Infancia y la Adolescencia), Articulo 124 (CAPITULO V)**
   > Artículo 124.Adopción. Es competente para conocer el proceso de adopción en primera instancia el juez de familia del domicilio de los adoptantes. Cuando se trate de la adopción internacional, será compe­tente cualquier juez de familia del país. La demanda solo podrá ser formulada por los interesados en ser declarados adoptantes, mediante apoderado. A la demanda se acompañarán los siguientes documentos: - 1. El consentimiento para la adopción, si fuere el caso. - 2. La copia de la declaratoria de adoptabilidad o de la autorización para la adopción, según el caso. - 3. El registro civil de nacimiento de los adoptantes y el del niño, niña o adolescente. - 4. El registro civil de matrimonio o la prueba de la convivencia extramatrimonial de los adoptantes. - 5. La certificación del Instituto Colombiano de Bienestar Familiar o de una entidad autorizada para el efecto, sobre la idoneidad física, mental, social y moral de los adoptantes, expedida con antelación no superior a seis meses, y la constancia de la entidad respectiva sobre la integración personal del niño, niña o adolescente con el adoptante o adoptantes. - 6. El certificado vigente de antecedentes penales o policivos de los adoptantes.
3. **[3] Ley 388 de 1997 (Ley de Ordenamiento Territorial), Articulo 99 (CAPITULO Xl)**
   > Parágrafo 2°.Con el fin de evitar los asentamientos humanos en zonas no previstas para tal fin por los planes de ordenamiento territorial, los notarios se abstendrán de correr escrituras de parcelación, subdivisión y loteo, hasta tanto no se allegue por parte del interesado el Certificado de Conformidad con Normas Urbanísticas expedido por la autoridad con jurisdicción en la zona donde se halle ubicado el predio, el cual debe protocolizarse dentro de la escritura. El Gobierno Nacional establecerá las características y condiciones del Certificado de Conformidad con Normas Urbanísticas, el cual tendrá un costo único para cualquier actuación.
4. **[4] Ley 100 de 1993 (Sistema de Seguridad Social Integral), Articulo 289 (LIBRO QUINTO)**
   > ARTICULO 289. Vigencia y derogatorias. La presente Ley rige a partir de la fecha de su publicación, salvaguarda los derechos adquiridos y deroga todas las disposiciones que le sean contrarías, en especial el artículos 2º. de la Ley 4º. de 1966, el artículo 5º. de la Ley 33 de 1985, el parágrafo del artículo 7º de la Ley 71 de 1988, los artículos 260, 268, 269, 270, 271 y 272 del Código Sustantivo del Trabajo y demás normas que los modifiquen o adicionen. El Presidente del honorable Senado de la República, Jorge Ramón Elías Nader El Secretario General del Honorable Senado de la República, Pedro Pumarejo Vega El Presidente de la Honorable Cámara de Representantes, Francisco José Jattín Safar El Secretario General de la Honorable Cámara de Representantes, Diego Vivas Tafur REPUBLICA DE COLOMBIA - GOBIERNO NACIONAL Publíquese y ejecútese. Dada en Santafé de Bogotá, D. C., a los 23 días de diciembre de 1993. CESAR GAVIRIA TRUJILLO El Ministro de Hacienda y Crédito Público, Rudolf Hommes Rodríguez El Ministro de Trabajo y Seguridad Social, Luis Fernando Ramírez Acuña El Ministro de Salud, Juan Luis Londoño de la Cuesta El Director del Departamento Administrativo de la Función Pública (E.), Jorge Eliécer Sabas Bedoya
5. **[5] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 24 (CAPITULO II)**
   > Artículo 24.Recategorización. El titular de una licencia de conducción podrá solicitar ante un organismo de tránsito o la entidad pública o privada por él autorizada, la recategorización de su licencia, para lo cual debe presentar y aprobar un nuevo examen teórico-práctico para la categoría solicitada y presentar un certificado de aptitud en conducción otorgado por el centro respectivo, y su trámite no podrá durar más de 72 horas una vez aceptada la documentación. PREGUNTA DEL USUARIO: cuanto cuesta sacar el certificado de antecedentes para un trabajo

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | -- | si | si | -- |
| v2 | -- | si | -- | -- |

**v1.** No te puedo decir cuánto cuesta porque depende de la entidad que lo emite y de tu situación personal. Pide el certificado directamente a la institución que te pide ese requisito, como la Policía o la Fiscalía, y guarda el recibo. Si te exigen un valor que no aparece en la norma, puedes interpelarlos por derecho de petición.

**v2.** No te puedo decir cuánto cuesta porque depende de la entidad que lo emite y de tu situación: si eres menor de edad, si tienes antecedentes penales o civiles, si ya lo has solicitado antes. Pide el formato de solicitud en la entidad que te pide el certificado y consúltalo allí mismo, porque el precio suele estar publicado en su página web.

---

## Caso 4127 — Pensiones y seguridad social

**Pregunta.** Cotice varios anos en el exterior, esas semanas cuentan para mi pension en Colombia?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 13 (CAPÍTULO I)**
   > Artículo 13. Garantías suplementarias. Los productores y proveedores podrán otorgar garantías suplementarias a la legal, cuando amplíen o mejoren la cobertura de esta, de forma gratuita u onerosa. En este último caso se deberá obtener la aceptación expresa por parte del consumidor, la cual deberá constar en el escrito que le dé soporte. También podrán otorgar este tipo de garantías terceros especializados que cuenten con la infraestructura y recursos adecuados para cumplir con la garantía. Parágrafo 1°. A este tipo de garantías le es aplicable la regla de responsabilidad solidaria, respecto de quienes hayan participado en la cadena de distribución con posterioridad a quien emitió la garantía suplementaria. Parágrafo 2°. Cuando el bien se adquiera en el exterior con garantía global o válida en Colombia, el consumidor podrá exigirla al representante de marca en Colombia y solicitar su efectividad ante las autoridades colombianas. Para hacer efectiva este tipo de garantía, se deberá demostrar que se adquirió en el exterior.
2. **[2] Ley 599 de 2000 (Codigo Penal), Articulo 16 (CAPITULO UNICO)**
   > - 4. Al nacional que fuera de los casos previstos en los numerales anteriores, se encuentre en Colombia después de haber cometido un delito en territorio extranjero, cuando la ley penal colombiana lo reprima con pena privativa de la libertad cuyo mínimo no sea inferior a dos (2) años y no hubiere sido juzgado en el exterior. Si se trata de pena inferior, no se procederá sino por querella de parte o petición del Procurador General de la Nación. - 5. Al extranjero que fuera de los casos previstos en los numerales 1, 2 y 3, se encuentre en Colombia después de haber cometido en el exterior un delito en perjuicio del Estado o de un nacional colombiano, que la ley colombiana reprima con pena privativa de la libertad cuyo mínimo no sea inferior a dos años (2) y no hubiere sido juzgado en el exterior. En este caso sólo se procederá por querella de parte o petición del Procurador General de la Nación. - 6. Al extranjero que haya cometido en el exterior un delito en perjuicio de extranjero, siempre que se reúnan estas condiciones: - a) Que se halle en territorio colombiano; - b) Que el delito tenga señalada en Colombia pena privativa de la libertad cuyo mínimo no sea inferior a tres (3) años;
3. **[3] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 23 (Capítulo I)**
   > ARTÍCULO 23. Ámbito territorial de operación. Reglamentado por el Decreto Nacional 3428 de 2003. Las empresas de servicios públicos pueden operar en igualdad de condiciones en cualquier parte del país, con sujeción a las reglas que rijan en el territorio del correspondiente departamento o municipio. Igualmente, conforme a lo dispuesto por las normas cambiarias o fiscales, las empresas podrán desarrollar su objeto en el exterior sin necesidad de permiso adicional de las autoridades colombianas. La obtención en el exterior de agua, gas combustible, energía o acceso a redes, para beneficio de usuarios en Colombia, no estará sujeta a restricciones ni a contribución alguna arancelaria o de otra naturaleza, ni a permisos administrativos distintos de los que se apliquen a actividades internas de la misma clase, pero si a las normas cambiarias y fiscales comunes. Las comisiones de regulación, sin embargo, podrán prohibir que se facilite a usuarios en el exterior el agua, el gas combustible, la energía, o el acceso a redes, cuando haya usuarios en Colombia a quienes exista la posibilidad física y financiera de atender, pero cuya demanda no hubiese sido satisfecha a las tarifas que resulten de las fórmulas aprobadas por las comisiones.
4. **[4] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 493 (CAPITULO II)**
   > Artículo 493. Requisitos para concederla u ofrecerla. Para que pueda ofrecerse o concederse la extradición se requiere, además: - 1. Que el hecho que la motiva también esté previsto como delito en Colombia y reprimido con una sanción privativa de la libertad cuyo mínimo no sea inferior a cuatro (4) años. - 2. Que por lo menos se haya dictado en el exterior resolución de acusación o su equivalente.
5. **[5] Ley 80 de 1993 (Estatuto General de Contratacion de la Administracion Publica), Articulo 13**
   > ARTICULO 13. DE LA NORMATIVIDAD APLICABLE A LOS CONTRATOS ESTATALES. Los contratos que celebren las entidades a que se refiere el artículo 2o. del presente estatuto se regirán por las disposiciones comerciales y civiles pertinentes, salvo en las materias particularmente reguladas en esta ley. Los contratos celebrados en el exterior se podrán regir en su ejecución por las reglas del país en donde se hayan suscrito, a menos que deban cumplirse en Colombia. Los contratos que se celebren en Colombia y deban ejecutarse o cumplirse en el extranjero, podrán someterse a la ley extranjera. PREGUNTA DEL USUARIO: Cotice varios anos en el exterior, esas semanas cuentan para mi pension en Colombia?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | -- | si | si | -- |
| v2 | -- | si | si | -- |

**v1.** No puedo decirte eso con certeza: cada caso depende de cómo se tramitaron tus cotizaciones en el exterior y cómo se reconoce esa experiencia en Colombia. Pide a tu fondo de pensiones el informe de tu historia laboral internacional y, si hay duda, consulta en la Superintendencia Financiera o en un consultorio jurídico universitario.

**v2.** No puedo responder sobre cotizaciones del exterior porque no tengo esa información. Pide a tu fondo de pensiones el detalle de cada periodo trabajado y, si no lo incluyen, presenta reclamación de habeas data pidiendo que se verifique la documentación. La Superintendencia Financiera puede orientarte.

---

## Caso 4128 — Pensiones y seguridad social

**Pregunta.** Tengo dudas si puedo recibir doble pension, una como madre sustituta y otra propia.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 275 (CAPITULO II.)**
   > ARTICULO 275. PENSION EN CASO DE MUERTE. Fallecido un trabajador jubilado, su cónyuge y sus hijos menores de diez y ocho (18) años tendrán derecho a recibir la mitad de la respectiva pensión durante dos (2) años contados desde la fecha del fallecimiento, cuando el trabajador haya adquirido el derecho dentro de las normas de este Código, lo esté disfrutando en el momento de la muerte, y siempre que aquellas personas no dispongan de medios suficientes para su congrua subsistencia. Esta pensión se distribuye así : en concurrencia de viuda con hijos, la primera recibe una mitad y los segundos la otra mitad; si hay hijos naturales, cada uno de éstos lleva la mitad de la cuota de uno legítimo; a falta de hijos todo corresponde al cónyuge, y en defecto de éste, todo corresponde a los hijos. A falta de cónyuge y de hijos, tienen derecho por mitades, a la pensión de que trata este artículo, los padres o los hermanos inválidos o las hermanas solteras del fallecido, siempre que no disfruten de medios suficientes para su congrua subsistencia y hayan dependido exclusivamente del jubilado. La cuota del grupo que falte pasa al otro, y el beneficiario único de un grupo lleva todo lo de éste.
2. **[2] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 236 (CAPITULO V.)**
   > PARÁGRAFO 4. Licencia parental compartida. Los padres podrán distribuir libremente entre sí las últimas seis (6) semanas de la licencia de la madre, siempre y cuando cumplan las condiciones y requisitos dispuestos en este artículo. Esta licencia, en el caso de la madre, es independiente del permiso de lactancia. La licencia parental compartida se regirá por las siguientes condiciones: El tiempo de licencia parental compartida se contará a partir de la fecha del parto. Salvo que el médico tratante haya determinado que la madre deba tomar entre una o dos (2) semanas de licencia previas a la fecha probable del parto o por determinación de la madre. La madre deberá tomar como mínimo las primeras doce (12) semanas después del parto, las cuales serán intransferibles. Las restantes seis (6) semanas podrán ser distribuidas entre la madre y el padre, de común acuerdo entre los dos. El tiempo de licencia del padre no podrá ser recortado en aplicación de esta figura. En ningún caso se podrán fragmentar, intercalar ni tomar de manera simultánea los períodos de licencia salvo por enfermedad posparto de la madre, debidamente certificada por el médico.
3. **[3] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 236 (CAPITULO V.)**
   > PARÁGRAFO 5. Licencia parental flexible de tiempo parcial. La madre y/o padre podrán optar por una licencia parental flexible de tiempo parcial, en la cual, podrán cambiar un periodo determinado de su licencia de maternidad o de paternidad por un período de trabajo de medio tiempo, equivalente al doble del tiempo correspondiente al período de tiempo seleccionado. Esta licencia, en el caso de la madre, es independiente del permiso de lactancia. La licencia parental flexible de tiempo parcial se regirá por las siguientes condiciones: Los padres podrán usar esta figura antes de la semana dos (2) de su licencia de paternidad; las madres, a no antes de la semana trece (13) de su licencia de maternidad. El tiempo de licencia parental flexible de tiempo parcial se contará a partir de la fecha del parto. Salvo que el médico tratante haya determinado que la madre deba tomar una o dos (2) semanas de licencia previas a la fecha probable del parto. Los periodos seleccionados para la licencia parental flexible no podrán interrumpirse y retomarse posteriormente. Deberán ser continuos, salvo aquellos casos en que medie acuerdo entre el empleador y el trabajador.
4. **[4] Ley 115 de 1994 (Ley General de Educacion), Articulo 211 (CAPITULO 1°)**
   > ARTICULO 211. Docentes con derecho a la pensión de jubilación. Los docentes nacionales y nacionalizados que adquirieron el derecho a la pensión de jubilación antes de la expedición de la Ley 91 de 1989 y que acreditaron este derecho, quedarán afiliados al Fondo Nacional de Prestaciones Sociales del Magisterio, siempre y cuando tal calidad no haya sido reconocida por otra entidad de previsión social.
5. **[5] Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana), Articulo 9 (CAPITULO III)**
   > Artículo 9º. Obligaciones del arrendatario. Son obligaciones del arrendatario: - 1. Pagar el precio del arrendamiento dentro del plazo estipulado en el contrato, en el inmueble arrendado o en el lugar convenido. - 2. Cuidar el inmueble y las cosas recibidas en arrendamiento. En caso de daños o deterioros distintos a los derivados del uso normal o de la acción del tiempo y que fueren imputables al mal uso del inmueble o a su propia culpa, efectuar oportunamente y por su cuenta las reparaciones o sustituciones necesarias. - 3. Pagar a tiempo los servicios, cosas o usos conexos y adicionales, así como las expensas comunes en los casos en que haya lugar, de conformidad con lo establecido en el contrato. - 4. Cumplir las normas consagradas en los reglamentos de propiedad horizontal y las que expida el gobierno en protección de los derechos de todos los vecinos. En caso de vivienda compartida y de pensión, el arrendatario está obligado además a cuidar las zonas y servicios de uso común y a efectuar por su cuenta las reparaciones o sustituciones necesarias, cuando sean atribuibles a su propia culpa o, a la de sus dependientes, y - 5. Las demás obligaciones consagradas para los arrendatarios en el Capítulo III, Título XXVI, libro 4 del Código Civil. PREGUNTA DEL USUARIO: Tengo dudas si puedo recibir doble pension, una como madre sustituta y otra propia.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | -- | -- |
| v2 | si | -- | -- | -- |

Articulos citados — v1: ['236'] · v2: ['275']. Todos presentes en el contexto.

**v1.** No lo veo permitido: el artículo 236 del Código Sustantivo del Trabajo dice que la licencia parental compartida se regula por las condiciones dispuestas en ese artículo, y no menciona cobrar dos pensiones. Consulta con tu fondo de pensiones si hay alguna excepción para tu caso.

**v2.** No lo veo permitido: el artículo 275 del Código Sustantivo del Trabajo dice que la pensión de sustitución va a mitad a la viuda y a mitad a los hijos menores, y que si faltan hijos todo corre al cónyuge. Si tu hijo es menor, pide esa mitad a la pensión de sustitución y, si te la niegan, acude a la Inspección del Trabajo.

---

## Caso 4225 — Prestamos informales y usura

**Pregunta.** Me prestaron dinero y me estan cobrando comisiones que no entiendo.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 84 (Capítulo V)**
   > ARTÍCULO 84. Régimen presupuestal. Modificado parcialmente por el Artículo 28 del Decreto 1165 de 1999. Las Comisiones y la Superintendencia están sometidas a las normas orgánicas del presupuesto general de la Nación, y a los límites anuales de crecimiento de sus gastos que señale el Consejo de Política Económica y Social. En consonancia con tales normas, las comisiones y la superintendencia prepararán su presupuesto que presentarán a la aprobación del Gobierno Nacional.
2. **[2] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 73 (Capítulo III)**
   > 73.26. Todas las demás que le asigne la ley y las facultades previstas en ella que no se hayan atribuido a una autoridad específica. Salvo cuando esta Ley diga lo contrario en forma explícita, no se requiere autorización previa de las comisiones para adelantar ninguna actividad o contrato relacionado con los servicios públicos; ni el envío rutinario de información. Pero las comisiones, tendrán facultad selectiva de pedir información amplia, exacta, veraz y oportuna a quienes prestan los servicios públicos a los que esta Ley se refiere, inclusive si sus tarifas no están sometidas a regulación. Quienes no la proporcionen, estarán sujetos a todas las sanciones que contempla el artículo 81 de la presente Ley. En todo caso, las comisiones podrán imponer por sí mismas las sanciones del caso, cuando no se atiendan en forma adecuada sus solicitudes de información.
3. **[3] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 89 (Capítulo II)**
   > 89.1. Se presume que el factor aludido nunca podrá ser superior al equivalente del 20% del valor del servicio y no podrán incluirse factores adicionales por concepto de ventas o consumo del usuario. Cuando comiencen a aplicarse las fórmulas tarifarias de que trata esta Ley, las comisiones sólo permitirán que el factor o factores que se han venido cobrando, se incluyan en las facturas de usuarios de inmuebles residenciales de los estratos 5 y 6, y en las de los usuarios industriales y comerciales. Para todos estos, el factor o factores se determinará en la forma atrás dispuesta, se discriminará en las facturas, y los recaudos que con base en ellos se hagan, recibirán el destino señalado en el artículo 89.2 de esta Ley. 89.2. Quienes presten los servicios públicos harán los recaudos de las sumas que resulten al aplicar los factores de que trata este artículo y los aplicarán al pago de subsidios, de acuerdo con las normas pertinentes, de todo lo cual llevarán contabilidad y cuentas detalladas. Al presentarse superávit, por este concepto, en empresas de servicios públicos oficiales de orden distrital, municipal o departamental se destinarán a "fondos de solidaridad y redistribución de ingresos" para empresas de la misma naturaleza y servicio que cumplan sus actividades en la misma entidad territorial al de la empresa aportante.
4. **[4] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 127 (CAPITULO I.)**
   > ARTICULO 127. ELEMENTOS INTEGRANTES. Constituye salario no sólo la remuneración ordinaria, fija o variable, sino todo lo que recibe el trabajador en dinero o en especie como contraprestación directa del servicio, sea cualquiera la forma o denominación que se adopte, como primas, sobresueldos, bonificaciones habituales, valor del trabajo suplementario o de las horas extras, valor del trabajo en días de descanso obligatorio, porcentajes sobre ventas y comisiones. (Modificado por el Art. 14 del Ley 50 de 1990)
5. **[5] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 188 (TITULO X)**
   > ARTÍCULO 188. Transitorio. Las Comisiones de Regulación seguirán operando y ejecutando su presupuesto hasta que entren en funcionamiento las comisiones de que trata esta Ley, las cuales podrán ejecutar las apropiaciones presupuestales que queden disponibles de las primeras y atenderán, hasta su pago total, las obligaciones originadas en estas. El Gobierno hará las operaciones presupuestales necesarias. PREGUNTA DEL USUARIO: Me prestaron dinero y me estan cobrando comisiones que no entiendo.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | -- | si | si | -- |

Articulos citados — v1: ['127'] · v2: ninguno. Todos presentes en el contexto.

**v1.** El artículo 127 del Código Sustantivo del Trabajo considera salario todo lo que recibes por tu trabajo, y las comisiones son parte de eso. Pide por escrito aclaración de cada concepto en tu nómina y, si no responden, presenta reclamación ante la Inspección del Trabajo. Si sospechas abuso, la Personería puede revisarlo.

**v2.** No te puedo explicar cómo se calculan esas comisiones con solo el texto de la ley de servicios públicos. Si te cobran más de lo que pactaron, pide por escrito la liquidación y, si no la dan, acude a la Superintendencia Financiera. Si te exigen pagos que no reconoces, guarda los recibos y radica un derecho de petición ante la entidad.

---

## Caso 4226 — Prestamos informales y usura

**Pregunta.** No se a donde denunciar un caso de prestamo gota a gota.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 67 (CAPITULO I)**
   > Artículo 67.Deber de denunciar. Toda persona debe denunciar a la autoridad los delitos de cuya comisión tenga conocimiento y que deban investigarse de oficio. El servidor público que conozca de la comisión de un delito que deba investigarse de oficio, iniciará sin tardanza la investigación si tuviere competencia para ello; en caso contrario, pondrá inmediatamente el hecho en conocimiento ante la autoridad competente.
2. **[2] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 68 (CAPITULO I)**
   > Artículo 68. Exoneración del deber de denunciar. Nadie está obligado a formular denuncia contra sí mismo, contra su cónyuge, compañero o compañera permanente o contra sus parientes dentro del cuarto grado de consanguinidad o civil, o segundo de afinidad, ni a denunciar cuando medie el secreto profesional.
3. **[3] Ley 2452 de 2025 (Codigo Procesal del Trabajo y de la Seguridad Social), Articulo 12 (CAPÍTULO I)**
   > Artículo 12. Competencia en los procesos en donde son parte las entidades del Sistema de Seguridad Social Integral. A) En los procesos que se sigan en contra de las entidades que conforman el Sistema de Seguridad Social Integral, será competente el juez laboral del lugar del domicilio de la entidad de seguridad social demandada o el del lugar donde se haya surtido la reclamación del derecho, a elección del demandante. En los lugares donde no haya juez laboral conocerá de estos procesos el respectivo juez del circuito en lo civil o promiscuo del circuito. En los eventos en que la reclamación se realice a través de canales digitales se tendrá surtida en el domicilio del iniciador del cual se hubiese remitido la petición. En caso de haberse presentado varias reclamaciones frente a un mismo asunto, se tendrá en cuenta la primera solicitud. B) En los procesos promovidos por las entidades del sistema de seguridad social, será competente el juez laboral del domicilio del demandado.
4. **[4] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 111 (CAPITULO IV)**
   > - b) Procurar la indemnización de perjuicios, el restablecimiento y la restauración del derecho en los eventos de agravio a los intereses colectivos, solicitar las pruebas que a ello conduzcan y las medidas cautelares que procedan; - c) Velar porque se respeten los derechos de las víctimas, testigos, jurados y demás intervinientes en el proceso, así como verificar su efectiva protección por el Estado; - d) Participar en aquellas diligencias o actuaciones donde proceda la disponibilidad del derecho por parte de la víctima individual o colectiva y en las que exista disponibilidad oficial de la acción penal, procurando que la voluntad otorgada sea real y que no se afecten los derechos de los perjudicados, así como los principios de verdad y justicia, en los eventos de aplicación del principio de oportunidad; - e) Denunciar los fraudes y colusiones procesales.
5. **[5] Ley 1333 de 2009 (Procedimiento sancionatorio ambiental), Articulo 15**
   > Artículo 15.Procedimiento para la imposición de medidas preventivas en caso de flagrancia. En los eventos de flagrancia que requieran la imposición de una medida preventiva en el lugar y ocurrencia de los hechos, se procederá a levantar un acta en la cual constarán los motivos que la justifican; la autoridad que la impone; lugar, fecha y hora de su fijación; funcionario competente, persona, proyecto, obra o actividad a la cual se impone la medida preventiva. El acta será suscrita por el presunto infractor o, si se rehusare a hacerlo, se hará firmar por un testigo. En el caso de que no sea factible la firma del acta por parte del presunto infractor o de un testigo, bastará con la sola suscripción por parte del funcionario encargado del asunto. De lo anterior deberá dejar la constancia respectiva. El acta deberá ser legalizada a través de un acto administrativo en donde se establecerán condiciones de las medidas preventivas impuestas, en un término no mayor a tres días. PREGUNTA DEL USUARIO: No se a donde denunciar un caso de prestamo gota a gota.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | si | -- | si | -- |

Articulos citados — v1: ['67', '68'] · v2: ['67', '68']. Todos presentes en el contexto.

**v1.** El artículo 67 del Código de Procedimiento Penal obliga a denunciar a la autoridad los delitos de los que tengas conocimiento y que deban investigarse de oficio, y el artículo 68 del mismo código exime de denunciar a uno mismo, a su cónyuge, a sus parientes hasta el cuarto grado y al secreto profesional. Pide copia del contrato y de los recibos, y denuncia ante la Fiscalía o la Policía.

**v2.** El artículo 67 del Código de Procedimiento Penal obliga a denunciar ante la Fiscalía los delitos que uno conoce y que deben investigarse de oficio, y el artículo 68 de la misma ley exime de denunciar contra uno mismo, contra su cónyuge o parientes cercanos. Pide copia del contrato y de los recibos, guarda mensajes y fotos de transferencias y lleva todo a la Fiscalía con tu historia completa.

---

## Caso 4321 — Procedimiento civil - recursos

**Pregunta.** Cual es la diferencia entre una demanda y una denuncia?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Decision 486 de 2000 (Regimen Comun sobre Propiedad Industrial, CAN), Articulo 30 (CAPÍTULO III)**
   > Artículo 30.- Las reivindicaciones definirán la materia que se desea proteger mediante la patente. Deben ser claras y concisas y estar enteramente sustentadas por la descripción. Las reivindicaciones podrán ser independientes o dependientes. Una reivindicación será independiente cuando defina la materia que se desea proteger sin referencia a otra reivindicación anterior. Una reivindicación será dependiente cuando defina la materia que se desea proteger refiriéndose a una reivindicación anterior. Una reivindicación que se refiera a dos o más reivindicaciones anteriores se considerará una reivindicación dependiente múltiple.
2. **[2] Ley 1098 de 2006 (Codigo de la Infancia y la Adolescencia), Articulo 61 (CAPITULO II)**
   > Artículo 61.Adopción. La adopción es, principalmente y por excelencia, una medida de protección a través de la cual, bajo la suprema vigilancia del Estado, se establece de manera irrevocable, la relación paterno-filial entre personas que no la tienen por naturaleza.
3. **[3] Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 479 (CAPITULO I.)**
   > ARTICULO 479. DENUNCIA. Para que sea válida la manifestación escrita de dar por terminada una convención colectiva de trabajo, si se hace por una de las partes, o por ambas separadamente, debe presentarse por triplicado ante el Inspector del Trabajo del lugar, y en su defecto, ante el Alcalde, funcionarios que le pondrán la nota respectiva de presentación, señalando el lugar, la fecha y la hora de la misma. El original de la denuncia será entregado al destinatario por dicho funcionario, y las copias serán destinadas para el Departamento Nacional de Trabajo y para el denunciante de la convención. Formulada así la denuncia de la convención colectiva, ésta continuará vigente hasta tanto se firme una nueva convención. (Modificado por el Art. 14 del Decreto 616 de 1954) (Artículo declarado EXEQUIBLE por la Corte Constitucional mediante Sentencia C-902-03) (Artículo declarado EXEQUIBLE por la Corte Constitucional mediante Sentencia C-1050-01)
4. **[4] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 69 (CAPITULO I)**
   > Artículo 69.Requisitos de la denuncia, de la querella o de la petición. La denuncia, querella o petición se hará verbalmente, o por escrito, o por cualquier medio técnico que permita la identificación del autor, dejando constancia del día y hora de su presentación y contendrá una relación detallada de los hechos que conozca el denunciante. Este deberá manifestar, si le consta, que los mismos hechos ya han sido puestos en conocimiento de otro funcionario. Quien la reciba advertirá al denunciante que la falsa denuncia implica responsabilidad penal. En todo caso se inadmitirán las denuncias sin fundamento. La denuncia solo podrá ampliarse por una sola vez a instancia del denunciante, o del funcionario competente, sobre aspectos de importancia para la investigación. Los escritos anónimos que no suministren evidencias o datos concretos que permitan encauzar la investigación se archivarán por el fiscal correspondiente.
5. **[5] Ley 906 de 2004 (Codigo de Procedimiento Penal), Articulo 66 (CAPITULO I)**
   > Artículo 66. Titularidad y obligatoriedad. El Estado, por intermedio de la Fiscalía General de la Nación, está obligado a ejercer la acción penal y a realizar la investigación de los hechos que revistan las características de una conducta punible, de oficio o que lleguen a su conocimiento por medio de denuncia, petición especial, querella o cualquier otro medio, salvo las excepciones contempladas en la Constitución Política y en este código. No podrá, en consecuencia, suspender, interrumpir ni renunciar a la persecución penal, salvo en los casos que establezca la ley para aplicar el principio de oportunidad regulado dentro del marco de la política criminal del Estado, el cual estará sometido al control de legalidad por parte del juez de control de garantías. Cuando se autorice la conversión de la acción penal pública a privada, y entre tanto esta perdure, la investigación y la acusación corresponderán al acusador privado en los términos de este código. PREGUNTA DEL USUARIO: Cual es la diferencia entre una demanda y una denuncia?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | -- | -- | si | -- |
| v2 | -- | -- | si | -- |

**v1.** Son conceptos distintos: la demanda es la acción judicial que presenta el demandante ante el juez civil o laboral, mientras que la denuncia es la notificación de hechos a la autoridad competente, que puede ser la Fiscalía, la Policía o la Inspección de Trabajo. Revisa en qué fuero y ante quién radicar tu caso.

**v2.** Son conceptos distintos: la denuncia es la que presenta ante la Fiscalía o la Policía para iniciar una investigación, mientras que la demanda se presenta ante el juez civil para pedirle que resuelva un conflicto. Revisa en el juzgado civil a qué proceso te diriges y, si no estás seguro, consulta en un consultorio jurídico universitario.

---

## Caso 4324 — Procedimiento civil - recursos

**Pregunta.** Hay algun formato oficial para escribir un recurso de reposicion o lo puedo hacer a mano?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 79 (CAPÍTULO II)**
   > "Transcurrido el término para resolver la petición, queja, recurso de reposición (PQR) o solicitud de indemnización sin que se hubiere resuelto de fondo y notificado dicha decisión, operará de pleno derecho el silencio administrativo positivo y se entenderá que la PQR o solicitud de indemnización ha sido resuelta en forma favorable al usuario, sin perjuicio de las sanciones a que haya lugar. "Siempre que el usuario presente ante el operador postal un recurso de reposición, este último deberá informarle en forma expresa y verificable el derecho que tiene a interponer el recurso de apelación en subsidio del de reposición, para que, en caso de que la respuesta al recurso de reposición sea desfavorable a sus pretensiones, la autoridad competente decida de fondo."
2. **[2] Ley 80 de 1993 (Estatuto General de Contratacion de la Administracion Publica), Articulo 41**
   > PARAGRAFO 3o.Salvo lo previsto en el parágrafo anterior, perfeccionado el contrato, se solicitará su publicación en el Diario Oficial o Gaceta Oficial correspondiente a la respectiva entidad territorial, o a falta de dicho medio, por algún mecanismo determinado en forma general por la autoridad administrativa territorial, que permita a los habitantes conocer su contenido. Cuando se utilice un medio de divulgación oficial, éste requisito se entiende cumplido con el pago de los derechos correspondientes.
3. **[3] Ley 2452 de 2025 (Codigo Procesal del Trabajo y de la Seguridad Social), Articulo 227 (CAPÍTULO II)**
   > Artículo 227. Recurso de reposición. Procedencia, oportunidad y decisión. El recurso de reposición procederá contra los autos interlocutorios, proferidos por el juez o salas de decisión, excepto los que resuelvan un recurso de apelación o una queja. Tampoco será procedente el recurso de reposición contra el auto que decide el recurso, salvo que contenga puntos novedosos. El recurso de reposición debe ser interpuesto, sustentado y resuelto en la misma audiencia en la que se haya proferido el auto, previo traslado a los no recurrentes. Si el auto es proferido por fuera de audiencia, el recurso de reposición debe ser interpuesto y sustentado dentro de los tres (3) días siguientes a su notificación por estado electrónico que será enviado al correo electrónico institucional del juzgado o de la secretaría de la sala correspondiente y de manera simultánea al correo electrónico de los demás sujetos procesales. Previo traslado por secretaría, se resolverá dentro de los tres (3) días siguientes. CAPÍTULO III Recurso de apelación
4. **[4] Ley 388 de 1997 (Ley de Ordenamiento Territorial), Articulo 82 (CAPITULO IX)**
   > Artículo 82. Revisión de la estimación del efecto de plusvalía. Cualquier propietario o poseedor de un inmueble objeto de la aplicación de la participación en la plusvalía, podrá solicitar, en ejercicio del recurso de reposición, que la administración revise el efecto plusvalía estimado por metro cuadrado definido para la correspondiente zona o subzona en la cual se encuentre su predio y podrá solicitar un nuevo avalúo. Para el estudio y decisión de los recursos de reposición que hayan solicitado la revisión de la estimación del mayor valor por metro cuadrado, la administración contará con un plazo de un (1) mes calendario contado a partir de la fecha del último recurso de reposición interpuesto en el cual se haya pedido dicha revisión. Los recursos de reposición que no planteen dicha revisión se decidirán en los términos previstos en el Código Contencioso Administrativo.
5. **[5] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 67 (CAPITULO III)**
   > Artículo 67.Utilización de señales. Todo conductor está obligado a utilizar las señales direccionales de su vehículo para dar un giro o para cambiar de carril. Sólo en caso de emergencia, y ante la imposibilidad de utilizar las señales direccionales, deberá utilizar las siguientes señales manuales: Para cruzar a la izquierda o cambio de carril sacará el brazo izquierdo y lo extenderá horizontalmente. Para indicar cruce a la derecha, cambio de carril, sacará el brazo izquierdo formando escuadra con la mano hacia arriba. Para indicar reducción de velocidad o detención del vehículo, sacará el brazo izquierdo formando escuadra con la mano hacia abajo. Parágrafo 1°. En carreteras o vías rápidas, la indicación intermitente de la señal direccional deberá ponerse por lo menos con sesenta (60) metros de antelación al giro, y en zonas urbanas, por lo menos con treinta (30) metros de antelación. Parágrafo 2º. El conductor deberá detener el vehículo para indicar al peatón con una señal de mano que tiene preferencia al paso de la vía, siempre y cuando esté cruzando por una zona demarcada en vías de baja velocidad. PREGUNTA DEL USUARIO: Hay algun formato oficial para escribir un recurso de reposicion o lo puedo hacer a mano?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | -- | si | si | -- |
| v2 | -- | si | -- | -- |

**v1.** No hay un modelo oficial, pero sí requisitos: el recurso debe ser escrito, con nombre y firma, y dirigido al juez o al organismo que dictó la decisión. Si te piden un formato específico, pídelo por derecho de petición. Si no te lo dan, puedes presentar la que tengas y pedir que se admita.

**v2.** No existe un formato oficial para el recurso de reposición, pero sí hay requisitos: que sea escrito, que indique claramente el recurso de reposición y el motivo, y que se entregue dentro del término legal. Puedes redactarlo tú mismo o pedir orientación gratuita en un centro de conciliación. Lleva copia del acto impugnado y de tu solicitud inicial.

---

## Caso 4623 — Violencia intrafamiliar y medidas de proteccion

**Pregunta.** Mi agresor es policia y me da miedo denunciar donde el trabaja.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 157 (CAPÍTULO I)**
   > PARÁGRAFO . La autoridad de Policía que ordena y ejecuta el traslado, deberá informar a la persona trasladada y al superior jerárquico de la unidad policial y elaborar un informe escrito donde consten los nombres e identificación de la persona trasladada por cualquier medio, de quien da la orden y quien la ejecuta, el motivo, el sitio al que se traslada, la justificación del tiempo empleado para el traslado y el nombre del allegado o a quien la persona trasladada informa para ser asistido, de ser ello posible. A la persona, sujeto de la medida, se le deberá entregar copia de dicho informe.
2. **[2] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 159 (CAPITULO X)**
   > Parágrafo 2. Las multas serán de propiedad exclusiva de los organismos de tránsito donde se cometió la infracción de acuerdo con su jurisdicción. El manto de aquellas multas que sean impuestas sobre las vías nacionales, por parte del personal de la Policía Nacional de Colombia, adscrito a la Dirección de Tránsito y Transporte, se distribuirá en un cincuenta por ciento (50%) para el municipio donde se entregue el correspondiente comparendo y el otro cincuenta por ciento (50%) para la Dirección de Tránsito y Transporte de la Policía Nacional, con destino a la capacitación de su personal adscrito, planes de educación y seguridad vial que adelante esta especialidad a lo largo de la red vial nacional, locaciones que suplan las necesidades del servicio y la construcción de la Escuela de Seguridad Vial de la Policía Nacional.
3. **[3] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 20 (CAPÍTULO II)**
   > ARTÍCULO 20. Actividad de Policía. Es el ejercicio de materialización de los medios y medidas correctivas, de acuerdo con las atribuciones constitucionales, legales y reglamentarias conferidas a los uniformados de la Policía Nacional, para concretar y hacer cumplir las decisiones dictadas en ejercicio del poder y la función de Policía, a las cuales está subordinada. La actividad de Policía es una labor estrictamente material y no jurídica, y su finalidad es la de preservar la convivencia y restablecer todos los comportamientos que la alteren.
4. **[4] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 11 (CAPÍTULO I)**
   > ARTÍCULO 11. Poder de Policía. El poder de Policía es la facultad de expedir las normas en materia de Policía, que son de carácter general, impersonal y abstracto, ejercido por el Congreso de la República para regular el ejercicio de la libertad, los derechos y los deberes constitucionales, para la convivencia y establecer los medios y las medidas correctivas en caso de su incumplimiento.
5. **[5] Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana), Articulo 222 (CAPÍTULO II)**
   > ARTÍCULO 222. Trámite del proceso verbal inmediato. Se tramitarán por el proceso verbal inmediato los comportamientos contrarios a la convivencia, de competencia del personal uniformado de la Policía Nacional, los comandantes de estación o subestación de Policía, y los comandantes del Centro de Atención Inmediata de Policía, en las etapas siguientes: 1. Se podrá iniciar de oficio o a petición de quien tenga interés directo o acuda en defensa de las normas de convivencia. 2. Una vez identificado el presunto infractor, la autoridad de Policía lo abordará en el sitio donde ocurran los hechos, si ello fuera posible o, en aquel donde lo encuentren, y le informará que su acción u omisión configura un comportamiento contrario a la convivencia. 3. El presunto infractor deberá ser oído en descargos. 4. La autoridad de Policía hará una primera ponderación de los hechos y procurará una mediación policial entre las partes en conflicto. De no lograr la mediación, impondrá la medida correctiva a través de la orden de Policía. PREGUNTA DEL USUARIO: Mi agresor es policia y me da miedo denunciar donde el trabaja.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | -- | -- | si | -- |
| v2 | si | -- | si | -- |

Articulos citados — v1: ninguno · v2: ['157', '222']. Todos presentes en el contexto.

**v1.** No te expongas: la protección de testigos y víctimas es un principio fundamental. Pide tu caso a la Fiscalía, que puede investigar a pesar de la pertenencia policial, y guarda el registro policial de la denuncia. Si temes por tu vida, llama a la Línea 123 o acude a la Comisaría de Familia.

**v2.** El artículo 222 del Código Nacional de Seguridad y Convivencia permite iniciar el proceso verbal inmediato de oficio o a petición de quien tenga interés directo, y el artículo 157 de la misma ley exige que la autoridad informe al superior jerárquico y al allegado. Denuncia ante la Fiscalía o en la Defensoría del Pueblo, y pide que te acompañe un funcionario de la Defensoría de Familia o de la Personería.

---

## Caso 4630 — Violencia intrafamiliar y medidas de proteccion

**Pregunta.** me pueden dar permiso en el trabajo para ir a las citas de la comisaria por lo de mi ex que me pegaba?

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 50 (CAPÍTULO VI)**
   > Cuando el proveedor o expendedor dé a conocer su membrecía o afiliación en algún esquema relevante de autorregulación, asociación empresarial, organización para resolución de disputas u otro organismo de certificación, deberá proporcionar a los consumidores un método sencillo para verificar dicha información, así como detalles apropiados para contactar con dichos organismos, y en su caso, tener acceso a los códigos y prácticas relevantes aplicados por el organismo de certificación. - g) Disponer en el mismo medio en que realiza comercio electró­nico de canales de fácil acceso y de atención que garanticen la orientación y asistencia a los consumidores y la trazabilidad de las reclamaciones por ellos presentadas, con el fin de que estos puedan resolver dudas y radicar sus peticiones, quejas o recla­mos. De tal forma que les quede, constancia de la atención me­diante la generación de un número de registro o radicado, junto con la fecha y hora de radicación de sus peticiones, quejas o reclamos, incluyendo un mecanismo para su posterior segui­miento.
2. **[2] Ley 115 de 1994 (Ley General de Educacion), Articulo 216 (CAPITULO 2º.)**
   > ARTICULO 216. Reestructuración de las normales. El Gobierno Nacional dentro del término de un (1) año contado a partir de la promulgación de la presente Ley, determinará los procedimientos para reestructurar las normales que, por necesidad del servicio educativo, pueden formar educadores a nivel de normalista superior. Las normales que no sean reestructuradas ajustarán sus programas para ofrecer, de acuerdo con lo dispuesto en el presente artículo, preferiblemente programas de la educación media técnica u otros de la educación por niveles y grados, según las necesidades regionales o locales. La Nación y las entidades territoriales crearán las condiciones para dar cumplimiento a lo dispuesto en el presente artículo.
3. **[3] Ley 361 de 1997 (Integracion social de personas con discapacidad), Articulo 15 (CAPITULO II)**
   > Artículo 15. El Gobierno a través de las instituciones que promueven la cultura suministrará los recursos humanos, técnicos y económicos que faciliten el desarrollo artístico y cultural de la persona en situación de discapacidad. Así mismo las bibliotecas públicas y privadas tendrán servicios especiales que garanticen el acceso para las personas en situación de discapacidad. Dichas instituciones tomarán para el efecto, las medidas pertinentes en materia de barreras arquitectónicas dentro del año siguiente a la vigencia de la presente Ley, so pena de sanciones que impondrá el Ministerio de Educación Nacional o las Secretarías de Educación en quienes delegue, que pueden ir desde multas de 50 a 100 salarios mínimos legales mensuales hasta el cierre del establecimiento. Dichos dineros ingresarán a la Tesorería Nacional, Departamental o Municipal según el caso.
4. **[4] Ley 100 de 1993 (Sistema de Seguridad Social Integral), Articulo 33 (CAPITULO II)**
   > Parágrafo 2º. Para los efectos de las disposiciones contenidas en la presente ley, se entiende por semana cotizada el periodo de siete (7) días calendario. La facturación y el cobro de los aportes se harán sobre el número de días cotizados en cada período. Parágrafo 3º. Se considera justa causa para dar por terminado el contrato de trabajo o la relación legal o reglamentaria, que el trabajador del sector privado o servidor público cumpla con los requisitos establecidos en este artículo para tener derecho a la pensión. El empleador podrá dar por terminado el contrato de trabajo o la relación legal o reglamentaria, cuando sea reconocida o notificada la pensión por parte de las administradoras del sistema general de pensiones. Transcurridos treinta (30) días después de que el trabajador o servidor público cumpla con los requisitos establecidos en este artículo para tener derecho a la pensión, si este no la solicita, el empleador podrá solicitar el reconocimiento de la misma en nombre de aquel. Lo dispuesto en este artículo rige para todos los trabajadores o servidores públicos afiliados al sistema general de pensiones.
5. **[5] Ley 142 de 1994 (Regimen de servicios publicos domiciliarios), Articulo 101 (Capítulo IV)**
   > 101.7. La Nación y los departamentos pueden dar asistencia técnica a los municipios para que asuman la responsabilidad de la estratificación; para realizar las estratificaciones, los departamentos pueden dar ayuda financiera a los municipios cuyos ingresos totales sean equivalentes o menores a los gastos de funcionamiento, con base a la ejecución presupuestal del año inmediatamente anterior. 101.8. Las estratificaciones que los municipios y distritos hayan realizado o realicen con el propósito de determinar la tarifa del impuesto predial unificado de que trata la Ley 44/90, serán admisibles para los propósitos de esta Ley, siempre y cuando se ajusten a las metodologías de estratificación definidas por el Departamento Nacional de Planeación. 101.9. Modificado parcialmente por el artículo 4 de la Ley 732 de 2002 - Modificado parcialmente por el Artículo 28 del Decreto 1165 de 1999. Cuando se trate de otorgar subsidios con recursos nacionales, la Nación podrá exigir, antes de efectuar los desembolsos, que se consiga certificado de la Superintendencia de Servicios Públicos Domiciliarios, en el sentido de que la estratificación se hizo en forma correcta. Cuando se trate de otorgar subsidios con recursos departamentales, cada Departamento establecerá sus propias normas. PREGUNTA DEL USUARIO: me pueden dar permiso en el trabajo para ir a las citas de la comisaria por lo de mi ex que me pegaba?

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | -- | -- | si | -- |
| v2 | -- | -- | si | -- |

**v1.** No es tema de permiso: el permiso te lo da tu jefe, y eso no te libera de ir. Lo que sí puedes pedir es que te cubran el tiempo de ausencia ante la entidad que te paga, y eso se tramita por derecho de petición ante la entidad. Lleva la orden de protección vigente y el registro de las denuncias.

**v2.** No es tema de permiso: el trabajo debe protegerte. Pide a tu jefe por escrito el tiempo necesario para ir a la audiencia y a la comisaría, con copia a la Personería o a la Inspección del Trabajo. Si te niegan el permiso, eso puede ser una discriminación laboral.

---

## Caso 4724 — Servicios publicos domiciliarios

**Pregunta.** Vivo en zona rural y nunca han llevado energia hasta mi vereda.

**Contexto recuperado.** Los 5 fragmentos completos, como los vio el modelo:

1. **[1] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 141 (CAPITULO IV)**
   > Artículo 141. En aquellos municipios ribereños o conurbados cuyos cascos urbanos se encuentren separados por un río y unidos por un puente, podrá prestarse el servicio público de transporte terrestre automotor individual de pasajeros entre ellos, en zona urbana o rural, por los vehículos automotores que cuenten con los permisos y autorizaciones correspondientes expedidos por las autoridades de tránsito de los municipios involucrados; únicamente para los viajes que tengan origen en el municipio donde esté matriculado el vehículo. CAPITULO V Recursos
2. **[2] Ley 388 de 1997 (Ley de Ordenamiento Territorial), Articulo 34 (CAPITULO IV)**
   > Artículo 34. Suelo suburbano. Constituyen esta categoría las áreas ubicadas dentro del suelo rural, en las que se mezclan los usos del suelo y las formas de vida del campo y la ciudad, diferentes a las clasificadas como áreas de expansión urbana, que pueden ser objeto de desarrollo con restricciones de uso, de intensidad y de densidad, garantizando el autoabastecimiento en servicios públicos domiciliarios, de conformidad con lo establecido en la Ley 99 de 1993 y en la Ley 142 de 1994. Podrán formar parte de esta categoría los suelos correspondientes a los corredores urbanos interregionales. Los municipios y distritos deberán establecer las regulaciones complementarias tendientes a impedir el desarrollo de actividades y usos urbanos en estas áreas, sin que previamente se surta el proceso de incorporación al suelo urbano, para lo cual deberán contar con la infraestructura de espacio público, de infraestructura vial y redes de energía, acueducto y alcantarillado requerida para este tipo de suelo.
3. **[3] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 76 (CAPITULO III)**
   > - 13. En zona de seguridad y de protección de la vía férrea, en la vía principal, vías secundarias, apartaderos, estaciones y anexidades férreas
4. **[4] Ley 769 de 2002 (Codigo Nacional de Transito), Articulo 2 (CAPÍTULO I)**
   > Zona escolar: Parte de la vía situada frente a un establecimiento de enseñanza y que se extiende cincuenta (50) metros al frente y a los lados del límite del establecimiento. Zona de estacionamiento restringido: Parte de la vía delimitada por autoridad competente en zonas adyacentes a instalaciones militares o de policía, teatros, bancos, hospitales, entidades oficiales y de socorro, iglesias, establecimientos industriales y comerciales, en la cual solo pueden estacionar los vehículos autorizados. CAPÍTULO II Autoridades.
5. **[5] Ley 1712 de 2014 (Ley de Transparencia), Articulo 33 (TÍTULO V)**
   > Cumplido lo anterior, mediante auto de octubre 16 de 2012, se dispuso que por la Secretaría General se procediera a la fijación en lista del proceso y se surtiera el traslado al Procurador General de la Nación, para el concepto correspondiente. Igualmente se ordenó, de conformidad con lo que establece el artículo 11 del Decreto número 2067 de 1991, comunicar la iniciación del proceso de revisión del proyecto a la Vicepresidencia de la República, los Ministros del Interior, de Relaciones Exteriores, de Justicia y del Derecho, de Defensa Nacional, al de Agricultura y Desarrollo Rural, de Salud y de la Protección Social, de Trabajo, de Minas y Energía, de Comercio, Industria y Turismo, de Educación Nacional, de Ambiente y Desarrollo Sostenible, de Vivienda, Ciudad y Territorio, de Tecnologías de la Información y las Comunicaciones, de Transporte, y de Cultura; PREGUNTA DEL USUARIO: Vivo en zona rural y nunca han llevado energia hasta mi vereda.

| | cita | limites | fuente | frase |
|---|---|---|---|---|
| v1 | si | -- | si | -- |
| v2 | si | -- | -- | -- |

Articulos citados — v1: ['33', '34'] · v2: ['34']. Todos presentes en el contexto.

**v1.** El artículo 34 de la Ley 388 de 1997 permite desarrollar suelos rurales con restricciones de uso y densidad, garantizando el autoabastecimiento en servicios públicos, y el artículo 33 de la Ley 1712 de 2014 obliga a notificar la iniciación del proceso de revisión del proyecto a varias entidades. Reúne fotos, testigos y tu constancia de residencia y presenta una solicitud de atención ante la Alcaldía municipal, que debe remitirla a la Superintendencia de Servicios Públicos.

**v2.** El artículo 34 de la Ley 388 de 1997 permite desarrollar suelos rurales con restricciones de uso y densidad, garantizando el autoabastecimiento en servicios públicos, y el artículo 34 de la misma ley obliga a los municipios a impedir el desarrollo urbano sin contar con infraestructura de espacio público, vial y redes. Pide por escrito a la empresa de servicios públicos que te conecte y, si no responden, presenta acción de tutela.

---

