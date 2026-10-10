# Matriz de validacion: articulos gold del eval set

Material de consulta para validar `data/eval_set_articulos.json`. El
dictamen se registra en `docs/m3_articulos_gold_validacion.csv`.

Texto de los articulos tomado de la metadata del indice evaluado en S08 y
S10 (`hash_metadata_indice = 8cd72136235d6dfe`), uniendo los chunks de cada
articulo en orden. Los chunks de continuacion no traen encabezado, asi que
unirlos es la unica forma de leer el articulo entero.

La regla del etiquetado: **un caso cuenta como acierto si la busqueda trae
al menos uno de sus articulos.**


---

# Clase A -- sostienen un acierto (si estan mal, el acierto es falso)

27 filas en 21 casos.

## 9001 · Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana) · articulo 20

**Categoria:** Arriendo

**Pregunta:** Mi arrendador me subio el canon de arrendamiento el doble de lo que pagaba el año pasado, ¿puede hacer eso?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 20. Reajuste del canon de arrendamiento. Cada doce (12) meses de ejecución del contrato bajo un mismo precio, el arrendador podrá incrementar el canon hasta en una proporción que no sea superior al ciento por ciento (100%) del incremento que haya tenido el índice de precios al consumidor en el año calendario inmediatamente anterior a aquél en que deba efectuarse el reajuste del canon, siempre y cuando el nuevo canon no exceda lo previsto en el artículo 18 de la presente ley. El arrendador que opte por incrementar el canon de arrendamiento, deberá informarle al arrendatario el monto del incremento y la fecha en que se hará efectivo, a través del servicio postal autorizado o mediante el mecanismo de notificación personal expresamente establecido en el contrato, so pena de ser inoponible al arrendatario. El pago por parte del arrendatario de un reajuste del canon, no le dará derecho a solicitar el reintegro, alegando la falta de la comunicación. CAPITULO VII Terminación del Contrato de Arrendamiento

## 9002 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 62

**Categoria:** Despido

**Pregunta:** Renuncie a mi trabajo por presion de mi jefe, pero en el papel dice que fue voluntaria, ¿puedo reclamar algo?

**Estado:** recuperado=si · partido en 5 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> ARTICULO 62. TERMINACION DEL CONTRATO POR JUSTA CAUSA. Son justas causas para dar por terminado unilateralmente el contrato de trabajo: A). Por parte del {empleador}: El haber sufrido engaño por parte del trabajador, mediante la presentación de certificados falsos para su admisión o tendientes a obtener un provecho indebido. Todo acto de violencia, injuria, malos tratamientos o grave indisciplina en que incurra el trabajador en sus labores, contra el {empleador}, los miembros de su familia, el personal directivo o los compañeros de trabajo. Todo acto grave de violencia, injuria o malos tratamientos en que incurra el trabajador fuera del servicio, en contra del {empleador}, de los miembros de su familia o de sus representantes y socios, jefes de taller, vigilantes o celadores. (Numeral 3 declarado EXEQUIBLE por la Corte Constitucional mediante Sentencia C-299-98) Todo daño material causado intencionalmente a los edificios, obras, maquinarias y materias primas, instrumentos y demás objetos relacionados con el trabajo, y toda grave negligencia que ponga en peligro la seguridad de las personas o de las cosas. Todo acto inmoral o delictuoso que el trabajador cometa en el taller, establecimiento o lugar de trabajo o en el desempeño de sus labores. (Aparte subrayado declarado EXEQUIBLE, por los cargos analizados, por la Corte Constitucional mediante Sentencia C-931-14) Cualquier violación grave de las obligaciones o prohibiciones especiales que incumben al trabajador de acuerdo con los artículos 58 y 60 del Código Sustantivo del Trabajo, o cualquier falta grave calificada como tal en pactos o convenciones colectivas, fallos arbitrales, contratos individuales o reglamentos. (La Corte Constitucional se declaró INHIBIDA de fallar sobre este numeral (parcial) por ineptitud de la demanda, mediante Sentencia C-148-18) La detención preventiva del trabajador por más de treinta (30) días, a menos que posteriormente sea absuelto; o el arresto correccional que exceda de ocho (8) días, o aun por tiempo menor, cuando la causa de la sanción sea suficiente por sí misma para justificar la extinción del contrato. (Mediante Sentencia C-079-96 del 29 la Corte Constitucional se declaró INHIBIDA de fallar sobre el aparte subrayado. Dentro de los considerandos la Corte dice: ''el arresto correccional”, fue eliminado al expedirse el Decreto 522 de 1971. En consecuencia, la alusión que del mismo hace la causal 7.(sic) carece de aplicabilidad en el momento) El que el trabajador revele los secretos técnicos o comerciales o dé a conocer asuntos de carácter reservado, con perjuicio de la empresa. El deficiente rendimiento en el trabajo en relación con la capacidad del trabajador y con el rendimiento promedio en labores análogas, cuando no se corrija en un plazo razonable a pesar del requerimiento del {empleador}. La sistemática inejecución, sin razones válidas, por parte del trabajador, de las obligaciones convencionales o legales. Todo vicio del trabajador que perturbe la disciplina del establecimiento. La renuencia sistemática del trabajador a aceptar las medidas preventivas, profilácticas o curativas, prescritas por el médico del {empleador} o por las autoridades para evitar enfermedades o accidentes. La ineptitud del trabajador para realizar la labor encomendada. El reconocimiento al trabajador de la pensión de la jubilación oinvalidez estando al servicio de la empresa. (Aparte subrayado CONDICIONALMENTE EXEQUIBLE, ver Sentencia C-1443-00) La enfermedad contagiosa o crónica del trabajador, que no tenga carácter de profesional, así como cualquiera otra enfermedad o lesión que lo incapacite para el trabajo, cuya curación no haya sido posible durante ciento ochenta (180) días. El despido por esta causa no podrá efectuarse sino al vencimiento de dicho lapso y no exime al {empleador} de las prestaciones e indemnizaciones legales y convencionales derivadas de la enfermedad. (Numeral declarado CONDICIONALMENTE EXEQUIBLE, por la Corte Constitucional mediante Sentencia C-200-19) En los casos de los numerales 9 a 15 de este artículo, para la terminación del contrato, el {empleador} deberá dar aviso al trabajador con anticipación no menor de quince (15) días. B). Por parte del trabajador: El haber sufrido engaño por parte del {empleador}, respecto de las condiciones de trabajo. Todo acto de violencia, malos tratamientos o amenazas graves inferidas por el {empleador} contra el trabajador o los miembros de su familia, dentro o fuera del servicio, o inferidas dentro del servicio por los parientes, representantes o dependientes del {empleador} con el consentimiento o la tolerancia de éste. Cualquier acto del {empleador} o de sus representantes que induzca al trabajador a cometer un acto ilícito o contrario a sus convicciones políticas o religiosas. Todas las circunstancias que el trabajador no pueda prever al celebrar el contrato, y que pongan en peligro su seguridad o su salud, y que el {empleador} no se allane a modificar. Todo perjuicio causado maliciosamente por el {empleador} al trabajador en la prestación del servicio. El incumplimiento sistemático sin razones válidas por parte del {empleador}, de sus obligaciones convencionales o legales. La exigencia del {empleador}, sin razones válidas, de la prestación de un servicio distinto, o en lugares diversos de aquél para el cual se le contrató, y Cualquier violación grave de las obligaciones o prohibiciones que incumben al empleador, de acuerdo con los artículos 57 y 59 del Código Sustantivo del Trabajo, o cualquier falta grave calificada como tal en pactos o convenciones colectivas, fallos arbitrales, contratos individuales o reglamentos. PARAGRAFO. La parte que termina unilateralmente el contrato de trabajo debe manifestar a la otra, en el momento de la extinción, la causal o motivo de esa determinación. Posteriormente no pueden alegarse válidamente causales o motivos distintos. (Modificado por el Art. 7 del Decreto 2351 de 1965)

## 9005 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 8

**Categoria:** Garantias de consumo

**Pregunta:** Compre un celular hace 8 meses y ya se daño, la tienda dice que la garantia ya no cubre eso, ¿es cierto?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 8°. Término de la garantía legal. El término de la garantía legal será el dispuesto por la ley o por la autoridad competente. A falta de disposición de obligatorio cumplimiento, será el anunciado por el productor y/o proveedor. El término de la garantía legal empezará a correr a partir de la entrega del producto al consumidor. De no indicarse el término de garantía, el término será de un año para productos nuevos. Tratándose de productos perecederos, el término de la garantía legal será el de la fecha de vencimiento o expiración. Los productos usados en los que haya expirado el término de la garantía legal podrán ser vendidos sin garantía, circunstancia que debe ser informada y aceptada por escrito claramente por el consumidor. En caso contrario se entenderá que el producto tiene garantía de tres (3) meses. La prestación de servicios que suponen la entrega del bien para la reparación del mismo podrá ser prestada sin garantía, circunstancia que debe ser informada y aceptada por escrito claramente por el consumidor. En caso contrario se entenderá que el servicio tiene garantía de tres (3) meses, contados a partir de la entrega del bien a quien solicitó el servicio. Para los bienes inmuebles la garantía legal comprende la estabilidad de la obra por diez (10) años, y para los acabados un (1) año.

## 9005 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 11

**Categoria:** Garantias de consumo

**Pregunta:** Compre un celular hace 8 meses y ya se daño, la tienda dice que la garantia ya no cubre eso, ¿es cierto?

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 11. Aspectos incluidos en la garantía legal. Corresponden a la garantía legal las siguientes obligaciones: - 1. Como regla general, reparación totalmente gratuita de los defectos del bien, así como su transporte, de ser necesario, y el suministro oportuno de los repuestos. Si el bien no admite reparación, se procederá a su reposición o a la devolución del dinero. - 2. En caso de repetirse la falla y atendiendo a la naturaleza del bien y a las características del defecto, a elección del consumidor, se procederá a una nueva reparación, la devolución total o parcial del precio pagado o al cambio parcial o total del bien por otro de la misma especie, similares características o especificaciones técnicas, las cuales en ningún caso podrán ser inferiores a las del producto que dio lugar a la garantía. - 3. En los casos de prestación de servicios, cuando haya incumplimiento se procederá, a elección del consumidor, a la prestación del servicio en las condiciones en que fue contratado o a la devolución del precio pagado. - 4. Suministrar las instrucciones para la instalación, mantenimiento y utilización de los productos de acuerdo con la naturaleza de estos. - 5. Disponer de asistencia técnica para la instalación, mantenimiento de los productos y su utilización, de acuerdo con la naturaleza de estos. La asistencia técnica podrá tener un costo adicional al precio. - 6. La entrega material del producto y, de ser el caso, el registro correspondiente en forma oportuna. - 7. Contar con la disponibilidad de repuestos, partes, insumos, y mano de obra capacitada, aun después de vencida la garantía, por el término establecido por la autoridad competente, y a falta de este, el anunciado por el productor. En caso de que no se haya anunciado el término de disponibilidad de repuestos, partes, insumos y mano de obra capacitada, sin perjuicio de las sanciones correspondientes por información insuficiente, será el de las condiciones ordinarias y habituales del mercado para productos similares. Los costos a los que se refiere este numeral serán asumidos por el consumidor, sin perjuicio de lo señalado en el numeral 1 del presente artículo. - 8. Las partes, insumos, accesorios o componentes adheridos a los bienes inmuebles que deban ser cambiados por efectividad de garantía, podrán ser de igual o mejor calidad, sin embargo, no necesariamente idénticos a los originalmente instalados. - 9. En los casos de prestación de servicios que suponen la entrega de un bien, repararlo, sustituirlo por otro de las mismas características, o pagar su equivalente en dinero en caso de destrucción parcial o total causada con ocasión del servicio defectuoso. Para los efectos de este numeral, el valor del bien se determinará según sus características, estado y uso. Parágrafo. El Gobierno Nacional, dentro de los seis meses siguientes a la expedición de esta ley, se encargará de reglamentar la forma de operar de la garantía legal. La reglamentación del Gobierno, no suspende la aplicación de lo dispuesto en la presente ley.

## 9005 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 58

**Categoria:** Garantias de consumo

**Pregunta:** Compre un celular hace 8 meses y ya se daño, la tienda dice que la garantia ya no cubre eso, ¿es cierto?

**Estado:** recuperado=si · partido en 9 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 58. Procedimiento. Los procesos que versen sobre violación a los derechos de los consumidores establecidos en normas generales o especiales en todos los sectores de la economía, a excepción de la responsabilidad por producto defectuoso y de las acciones de grupo o las populares, se tramitarán por el procedimiento verbal sumario, con observancia de las siguientes reglas especiales: - 1. La Superintendencia de Industria y Comercio o el Juez competente conocerán a prevención. La Superintendencia de Industria y Comercio tiene competencia en todo el territorio nacional y reemplaza al juez de primera o única instancia competente por razón de la cuantía y el territorio. - 2. Será también competente el juez del lugar donde se haya comercializado o adquirido el producto, o realizado la relación de consumo. Cuando la Superintendencia de Industria y Comercio deba conocer de un asunto en un lugar donde no tenga oficina, podrá delegar a un funcionario de la entidad, utilizar medios técnicos para la realización de las diligencias y audiencias o comisionar a un juez. - 3. Las demandas para efectividad de garantía, deberán presentarse a más tardar dentro del año siguiente a la expiración de la garantía y las controversias netamente contractuales, a más tardar dentro del año siguiente a la terminación del contrato, En los demás casos, deberán presentarse a más tardar dentro del año siguiente a que el consumidor tenga conocimiento de los hechos que motivaron la reclamación. En cualquier caso deberá aportarse prueba de que la reclamación fue efectuada durante la vigencia de la garantía. - 4. No se requerirá actuar por intermedio de abogado. Las ligas y asociaciones de consumidores constituidas de acuerdo con la ley podrán representar a los consumidores. Por razones de economía procesal, la Superintendencia de Industria y Comercio podrá decidir varios procesos en una sola audiencia. - 5. A la demanda deberá acompañarse la reclamación directa hecha por el demandante al productor y/o proveedor, reclamación que podrá ser presentada por escrito, telefónica o verbalmente, con observancia de las siguientes reglas: - a) Cuando la pretensión principal sea que se cumpla con la garantía, se repare el bien o servicio, se cambie por uno nuevo de similares características, se devuelva el dinero pagado o en los casos de prestación de servicios que suponen la entrega de un bien, cuando el bien sufra deterioro o pérdida, la reposición del mismo por uno de similares características o su equivalente en dinero, se deberá identificar el producto, la fecha de adquisición o prestación del servicio y las pruebas del defecto. Cuando la reclamación sea por protección contractual o por información o publicidad engañosa, deberá anexarse la prueba documental e indicarse las razones de inconformidad. - b) La reclamación se entenderá presentada por escrito cuando se utilicen medios electrónicos. Quien disponga de la vía telefónica para recibir reclamaciones, deberá garantizar que queden grabadas. En caso de que la reclamación sea verbal, el productor o proveedor deberá expedir constancia escrita del recibo de la misma, con la fecha de presentación y el objeto de reclamo. El consumidor también podrá remitir la reclamación mediante correo con constancia de envío a la dirección del establecimiento de comercio donde adquirió el producto y/o a la dirección del productor del bien o servicio. - c) El productor o el proveedor deberá dar respuesta dentro de los quince (15) días hábiles siguientes a la recepción de la reclamación. La respuesta deberá contener todas las pruebas en que se basa. Cuando el proveedor y/o productor no hubiera expedido la constancia, o se haya negado a recibir la reclamación, el consumidor así lo declarará bajo juramento, con copia del envío por correo, - d) Las partes podrán practicar pruebas periciales anticipadas ante los peritos debidamente inscritos en el listado que para estos efectos organizará y reglamentará la Superintendencia de Industria y Comercio, los que deberán ser de las más altas calidades morales y profesionales. El dictamen, junto con la constancia de pago de los gastos y honorarios, se aportarán en la demanda o en la contestación. En estos casos, la Superintendencia de Industria y Comercio debe valorar el dictamen de acuerdo a las normas de la sana crítica, en conjunto con las demás pruebas que obren en el proceso y solo en caso de que carezca de firmeza y precisión podrá decretar uno nuevo. - e) Derogado. - f) Si la respuesta es negativa, o si la atención, la reparación, o la prestación realizada a título de efectividad de la garantía no es satisfactoria, el consumidor podrá acudir ante el juez competente o la Superintendencia. Si dentro del término señalado por la ley el productor o proveedor no da respuesta, se tendrá como indicio grave en su contra. La negativa comprobada del productor o proveedor a recibir una reclamación dará lugar a la imposición de las sanciones previstas en la presente ley y será apreciada como indicio grave en su contra. - g) Se dará por cumplido el requisito de procedibilidad de reclamación directa en todos los casos en que se presente un acta de audiencia de conciliación emitida por cualquier centro de conciliación legalmente establecido. - 6. La demanda deberá identificar plenamente al productor o proveedor. En caso de que el consumidor no cuente con dicha información, deberá indicar el sitio donde se adquirió el producto o se suministró el servicio, o el medio por el cual se adquirió y cualquier otra información adicional que permita a la Superintendencia de Industria y Comercio individualizar y vincular al proceso al productor o proveedor, tales como direcciones, teléfonos, correos electrónicos, entre otros. La Superintendencia de Industria y Comercio adelantará las gestiones pertinentes para individualizar y vincular al proveedor o productor. Si transcurridos dos meses desde la interposición de la demanda, y habiéndose realizado las gestiones pertinentes, no es posible su individualización y vinculación, se archivará el proceso, sin perjuicio de que el demandante pueda presentar, antes de que opere la prescripción de la acción, una nueva demanda con los requisitos establecidos en la presente ley y además deberá contener información nueva sobre la identidad del productor y/o expendedor. - 7. Las comunicaciones y notificaciones que deba hacer la Superintendencia de Industria y Comercio podrán realizarse por un medio eficaz que deje constancia del acto de notificación, ya sea de manera verbal, telefónica o por escrito, dirigidas al lugar donde se expendió el producto o se celebró el contrato, o a la que aparezca en las etiquetas del producto o en las páginas web del expendedor y el productor, o a las que obren en los certificados de existencia y representación legal, o a las direcciones electrónicas reportadas a la Superintendencia de Industria y Comercio, o a las que aparezcan en el registro mercantil o a las anunciadas en la publicidad del productor o proveedor. - 8. Derogado. - 9. Al adoptar la decisión definitiva, el Juez de conocimiento o la Superintendencia de Industria y Comercio resolverá sobre las pretensiones de la forma que considere más justa para las partes según lo probado en el proceso, con plenas facultades para fallar infra, extra y ultrapetita, y emitirá las órdenes a que haya lugar con indicación de la forma y términos en que se deberán cumplir. - 10. Si la decisión final es favorable al consumidor, la Superintendencia de Industria y Comercio y los Jueces podrán imponer al productor o proveedor que no haya cumplido con sus obligaciones contractuales o legales, además de la condena que corresponda, una multa de hasta ciento cincuenta (150) salarios mínimos legajes mensuales vigentes a favor de la Superintendencia de Industria y Comercio, que se fijará teniendo en cuenta circunstancias de agravación debidamente probadas, tales como la gravedad del hecho, la reiteración en el incumplimiento de garantías o del contrato, la renuencia a cumplir con sus obligaciones legales, inclusive la de expedir la factura y las demás circunstancias. No procederá esta multa si el proceso termina por conciliación, transacción, desistimiento o cuando el demandado se allana a los hechos en la contestación de la demanda. La misma multa podrá imponerse al consumidor que actúe en forma temeraria. - 11. En caso de incumplimiento de la orden impartida en la sentencia o de una conciliación o transacción realizadas en legal forma, la Superintendencia Industria y Comercio podrá: - a) Sancionar con una multa sucesiva a favor de la Superintendencia de Industria y Comercio, equivalente a la séptima parte de un salario mínimo legal mensual vigente por cada día de retardo en el incumplimiento. - b) Decretar el cierre temporal del establecimiento comercial, si persiste el incumplimiento y mientras se acredite el cumplimiento de la orden. Cuando lo considere necesario la Superintendencia de Industria y Comercio podrá solicitar la colaboración de la fuerza pública para hacer efectiva la medida adoptada. La misma sanción podrá imponer la Superintendencia de Industria y Comercio, la Superintendencia Financiera o el juez competente, cuando se incumpla con una conciliación o transacción que haya sido realizada en legal forma. Parágrafo. Para efectos de lo previsto en el presente artículo, la Superintendencia Financiera de Colombia tendrá competencia exclusiva respecto de los asuntos a los que se refiere el artículo 57 de esta ley. Parágrafo 2º. En el sector turismo, las acciones de protección al consumidor permitirán el llamamiento en garantía entre agencias de viajes y aerolíneas, conforme al artículo 64 de la Ley 1564 de 2012 o normas que la modifiquen, sustituyan y adicionen. Este procedimiento se llevará a cabo a petición de parte, facilitando que los consumidores puedan reclamar indemnizaciones o reembolsos por perjuicios sufridos durante su experiencia de viaje. La demanda por medio de la cual se llame en garantía deberá cumplir con los mismos requisitos exigidos en el presente artículo. Si se halla procedente el llamamiento, se ordenará notificar personalmente al convocado y correrle traslado del escrito por el término de la demanda inicial. Si la notificación no se logra dentro de los dos meses siguientes, el llamamiento será ineficaz. El llamado en garantía podrá contestar en la demanda y el llamamiento en un solo escrito, solicitando las pruebas que pretenda hacer valer. En la sentencia se resolverá la relación sustancial aducida y emitirá pronunciamiento sobre las indemnizaciones o restituciones a cargo del llamado en garantía. No será necesario notificar personalmente el auto que admite el llamamiento cuando el llamado actúe en el proceso como parte o como representante de alguna de las partes. CAPÍTULO IV Otras actuaciones administrativas Denominación Corregida por: Art. 3 Decreto 2184 de 2012

## 9031 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 168

**Categoria:** Salud / EPS

**Pregunta:** Me pidieron dinero adelantado en urgencias de una clinica para atenderme, ¿pueden hacer eso?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> ARTICULO 168. Atención Inicial de Urgencias. La atención inicial de urgencias debe ser prestada en forma obligatoria por todas las entidades públicas y privadas que presten servicios de salud, a todas las personas independientemente de la capacidad de pago. Su prestación no requiere contrato ni orden previa. El costo de estos servicios será pagado por el Fondo de Solidaridad y Garantía, en los casos previstos en el artículo anterior, o por la entidad promotora de salud al cual este afiliado en cualquier otro evento. PARAGRAFO. Los procedimientos de cobro y pago, así como las tarifas de estos servicios serán definidos por el Gobierno Nacional, de acuerdo con las recomendaciones del Consejo Nacional de Seguridad Social en Salud.

## 9032 · Ley 1751 de 2015 (Ley Estatutaria de Salud) · articulo 10

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS dice que el tratamiento que me ordeno el medico no esta cubierto por el plan, ¿ya no hay nada que hacer?

**Estado:** recuperado=si · partido en 4 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 10. Derechos y deberes de las personas, relacionados con la prestación del servicio de salud. Las personas tienen los siguientes derechos relacionados con la prestación del servicio de salud: a) A acceder a los servicios y tecnologías de salud, que le garanticen una atención integral, oportuna y de alta calidad; b) Recibir la atención de urgencias que sea requerida con la oportunidad que su condición amerite sin que sea exigible documento o cancelación de pago previo alguno; c) A mantener una comunicación plena, permanente, expresa y clara con el profesional de la salud tratante; d) A obtener una información clara, apropiada y suficiente por parte del profesional de la salud tratante que le permita tomar decisiones libres, conscientes e informadas respecto de los procedimientos que le vayan a practicar y riesgos de los mismos. Ninguna persona podrá ser obligada, contra su voluntad, a recibir tratamiento de salud; e) A recibir prestaciones de salud en las condiciones y términos consagrados en la ley; f) A recibir un trato digno, respetando sus creencias y costumbres, así como las opiniones personales que tengan sobre los procedimientos; g) A que la historia clínica sea tratada de manera confidencial y reservada y que únicamente pueda ser conocida por terceros, previa autorización del paciente o en los casos previstos en la ley, y a poder consultar la totalidad de su historia clínica en forma gratuita y a obtener copia de la misma; h) A que se le preste durante todo el proceso de la enfermedad, asistencia de calidad por trabajadores de la salud debidamente capacitados y autorizados para ejercer; i) A la provisión y acceso oportuno a las tecnologías y a los medicamentos requeridos; j) A recibir los servicios de salud en condiciones de higiene, seguridad y respeto a su intimidad; k) A la intimidad. Se garantiza la confidencialidad de toda información que sea suministrada en el ámbito del acceso a los servicios de salud y de las condiciones de salud y enfermedad de la persona, sin perjuicio de la posibilidad de acceso a la misma por los familiares en los eventos autorizados por la ley o las autoridades en las condiciones que esta determine; l) A recibir información sobre los canales formales para presentar reclamaciones, quejas, sugerencias y en general, para comunicarse con la administración de las instituciones, así como a recibir una respuesta por escrito; m) A solicitar y recibir explicaciones o rendición de cuentas acerca de los costos por los tratamientos de salud recibidos; n) A que se le respete la voluntad de aceptación o negación de la donación de sus órganos de conformidad con la ley; o) A no ser sometido en ningún caso a tratos crueles o inhumanos que afecten su dignidad, ni a ser obligados a soportar sufrimiento evitable, ni obligados a padecer enfermedades que pueden recibir tratamiento; p) A que no se trasladen las cargas administrativas y burocráticas que les corresponde asumir a los encargados o intervinientes en la prestación del servicio; q) Agotar las posibilidades de tratamiento para la superación de su enfermedad. Son deberes de las personas relacionados con el servicio de salud, los siguientes: a) Propender por su autocuidado, el de su familia y el de su comunidad; b) Atender oportunamente las recomendaciones formuladas en los programas de promoción y prevención; c) Actuar de manera solidaria ante las situaciones que pongan en peligro la vida o la salud de las personas; d) Respetar al personal responsable de la prestación y administración de los servicios salud; e) Usar adecuada y racionalmente las prestaciones ofrecidas, así como los recursos del sistema; f) Cumplir las normas del sistema de salud; g) Actuar de buena fe frente al sistema de salud; h) Suministrar de manera oportuna y suficiente la información que se requiera para efectos del servicio; i) Contribuir solidariamente al financiamiento de los gastos que demande la atención en salud y la seguridad social en salud, de acuerdo con su capacidad de pago Parágrafo 1°. Los efectos del incumplimiento de estos deberes solo podrán ser determinados por el legislador. En ningún caso su incumplimiento podrá ser invocado para impedir o restringir el acceso oportuno a servicios de salud requeridos. En ningún caso su incumplimiento podrá ser invocado para impedir o restringir el acceso oportuno a servicios de salud requeridos. Parágrafo 2°. El Estado deberá definir las políticas necesarias para promover el cumplimiento de los deberes de las personas, sin perjuicio de lo establecido en el parágrafo 1°.

## 9034 · Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana) · articulo 22

**Categoria:** Arriendo

**Pregunta:** Mi arrendador me dijo que tengo que irme en una semana porque quiere el apartamento, ¿tengo que hacerlo?

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 22. Terminación por parte del arrendador. Son causales para que el arrendador pueda pedir unilateralmente la terminación del contrato, las siguientes: - 1. La no cancelación por parte del arrendatario de las rentas y reajustes dentro del término estipulado en el contrato. - 2. La no cancelación de los servicios públicos, que cause la desconexión o pérdida del servicio, o el pago de las expensas comunes cuando su pago estuviere a cargo del arrendatario. - 3. El subarriendo total o parcial del inmueble, la cesión del contrato o del goce del inmueble o el cambio de destinación del mismo por parte del arrendatario, sin expresa autorización del arrendador. - 4. La incursión reiterada del arrendatario en procederes que afecten la tranquilidad ciudadana de los vecinos, o la destinación del inmueble para actos delictivos o que impliquen contravención, debidamente comprobados ante la autoridad policiva. - 5. La realización de mejoras, cambios o ampliaciones del inmueble, sin expresa autorización del arrendador o la destrucción total o parcial del inmueble o área arrendada por parte del arrendatario. - 6. La violación por el arrendatario a las normas del respectivo reglamento de propiedad horizontal cuando se trate de viviendas sometidas a ese régimen. - 7. El arrendador podrá dar por terminado unilateralmente el contrato de arrendamiento durante las prórrogas, previo aviso escrito dirigido al arrendatario a través del servicio postal autorizado, con una antelación no menor de tres (3) meses y el pago de una indemnización equivalente al precio de tres (3) meses de arrendamiento. Cumplidas estas condiciones el arrendatario estará obligado a restituir el inmueble. - 8. El arrendador podrá dar por terminado unilateralmente el contrato de arrendamiento a la fecha de vencimiento del término inicial o de sus prórrogas invocando cualquiera de las siguientes causales especiales de restitución, previo aviso escrito al arrendatario a través del servicio postal autorizado con una antelación no menor a tres (3) meses a la referida fecha de vencimiento: - a) Cuando el propietario o poseedor del inmueble necesitare ocuparlo para su propia habitación, por un término no menor de un (1) año; - b) Cuando el inmueble haya de demolerse para efectuar una nueva construcción, o cuando se requiere desocuparlo con el fin de ejecutar obras independientes para su reparación; - c) Cuando haya de entregarse en cumplimiento de las obligaciones originadas en un contrato de compraventa; - d) La plena voluntad de dar por terminado el contrato, siempre y cuando, el contrato de arrendamiento cumpliere como mínimo cuatro (4) años de ejecución. El arrendador deberá indemnizar al arrendatario con una suma equivalente al precio de uno punto cinco (1.5) meses de arrendamiento. Cuando se trate de las causales previstas en los literales a), b) y c), el arrendador acompañará al aviso escrito la constancia de haber constituido una caución en dinero, bancaria u otorgada por compañía de seguros legalmente reconocida, constituida a favor del arrendatario por un valor equivalente a seis (6) meses del precio del arrendamiento vigente, para garantizar el cumplimiento de la causal invocada dentro de los seis (6) meses siguientes a la fecha de la restitución. Cuando se trate de la causal prevista en el literal d), el pago de la indemnización se realizará mediante el mismo procedimiento establecido en el artículo 23 de esta ley. De no mediar constancia por escrito del preaviso, el contrato de arrendamiento se entenderá renovado automáticamente por un término igual al inicialmente pactado.

## 9036 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 168

**Categoria:** Relaciones laborales

**Pregunta:** Trabajo muchas horas extra y nunca me las han pagado, ¿que puedo hacer?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> ARTICULO 168. TASAS Y LIQUIDACION DE RECARGOS. El trabajo nocturno por el solo hecho de ser nocturno se remunera con un recargo del treinta y cinco por ciento (35%) sobre el valor del trabajo diurno, con excepción del caso de la jornada de treinta y seis (36) horas semanales previstas en el artículo 20 literal c) de esta ley. El trabajo extra diurno se remunera con un recargo del veinticinco por ciento (25%) sobre el valor del trabajo ordinario diurno. El trabajo extra nocturno se remunera con un recargo del setenta y cinco por ciento (75%) sobre el valor del trabajo ordinario diurno. Cada uno de los recargos antedichos se produce de manera exclusiva, es decir, sin acumularlo con algún otro. (Modificado por el Art. 24 de la Ley 50 de 1990)

## 9037 · Ley 1010 de 2006 (Ley de Acoso Laboral) · articulo 2

**Categoria:** Relaciones laborales

**Pregunta:** Mi jefe me grita y me humilla delante de mis compañeros todos los dias, ¿es acoso laboral?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> ARTÍCULO 2. Definición y modalidades de acoso laboral. Para efectos de la presente ley se entenderá por acoso laboral toda conducta persistente y demostrable, ejercida sobre un empleado, trabajador por parte de un empleador, un jefe o superior jerárquico inmediato o mediato, un compañero de trabajo o un subalterno, encaminada a infundir miedo, intimidación, terror y angustia, a causar perjuicio laboral, generar desmotivación en el trabajo, o inducir la renuncia del mismo. En el contexto del inciso primero de este artículo, el acoso laboral puede darse, entre otras, bajo las siguientes modalidades generales: 1. Maltrato laboral. Todo acto de violencia contra la integridad física o moral, la libertad física o sexual y los bienes de quien se desempeñe como empleado o trabajador; toda expresión verbal injuriosa o ultrajante que lesione la integridad moral o los derechos a la intimidad y al buen nombre de quienes participen en una relación de trabajo de tipo laboral o todo comportamiento tendiente a menoscabar la autoestima y la dignidad de quien participe en una relación de trabajo de tipo laboral. 2. Persecución laboral: toda conducta cuyas características de reiteración o evidente arbitrariedad permitan inferir el propósito de inducir la renuncia del empleado o trabajador, mediante la descalificación, la carga excesiva de trabajo y cambios permanentes de horario que puedan producir desmotivación laboral. (Ver Sentencia de Octubre 16 de 2014, Rad. 2014-01359 del Consejo de Estado.) 3. Discriminación laboral: (Modificado por el art. 74, Ley 1622 de 2013), todo trato diferenciado por razones de raza, género, origen familiar o nacional, credo religioso, preferencia política o situación social o que carezca de toda razonabilidad desde el punto de vista laboral. 4. Entorpecimiento laboral: toda acción tendiente a obstaculizar el cumplimiento de la labor o hacerla más gravosa o retardarla con perjuicio para el trabajador o empleado constituyen acciones de entorpecimiento laboral, entre otras, la privación, ocultación o inutilización de los insumos, documentos o instrumentos para la labor, la destrucción o pérdida de información, el ocultamiento de correspondencia o mensajes electrónicos. 5. Inequidad laboral: Asignación de funciones a menosprecio del trabajador. 6. Desprotección laboral: Toda conducta tendiente a poner en riesgo la integridad y la seguridad del trabajador mediante órdenes o asignación de funciones sin el cumplimiento de los requisitos mínimos de protección y seguridad para el trabajador. (Ver Sentencias T-882 de 2006)

## 9037 · Ley 1010 de 2006 (Ley de Acoso Laboral) · articulo 7

**Categoria:** Relaciones laborales

**Pregunta:** Mi jefe me grita y me humilla delante de mis compañeros todos los dias, ¿es acoso laboral?

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> ARTÍCULO 7. Conductas que constituyen acoso laboral. Se presumirá que hay acoso laboral si se acredita la ocurrencia repetida y pública de cualquiera de las siguientes conductas: Nota: (Texto subrayado declarado EXEQUIBLE por la Corte Constitucional, mediante Sentencia C-780 de 2007.) a) Los actos de agresión física, independientemente de sus consecuencias; b) Las expresiones injuriosas o ultrajantes sobre la persona, con utilización de palabras soeces o con alusión a la raza, el género, el origen familiar o nacional, la preferencia política o el estatus social; c) Los comentarios hostiles y humillantes de descalificación profesional expresados en presencia de los compañeros de trabajo; d) Las injustificadas amenazas de despido expresadas en presencia de los compañeros de trabajo; e) Las múltiples denuncias disciplinarias de cualquiera de los sujetos activos del acoso, cuya temeridad quede demostrada por el resultado de los respectivos procesos disciplinarios; f) La descalificación humillante y en presencia de los compañeros de trabajo de las propuestas u opiniones de trabajo; g) las burlas sobre la apariencia física o la forma de vestir, formuladas en público; h) La alusión pública a hechos pertenecientes a la intimidad de la persona; i) La imposición de deberes ostensiblemente extraños a las obligaciones laborales, las exigencias abiertamente desproporcionadas sobre el cumplimiento de la labor encomendada y el brusco cambio del lugar de trabajo o de la labor contratada sin ningún fundamento objetivo referente a la necesidad técnica de la empresa; j) La exigencia de laborar en horarios excesivos respecto a la jornada laboral contratada o legalmente establecida, los cambios sorpresivos del turno laboral y la exigencia permanente de laborar en dominicales y días festivos sin ningún fundamento objetivo en las necesidades de la empresa, o en forma discriminatoria respecto a los demás trabajadores o empleados; k) El trato notoriamente discriminatorio respecto a los demás empleados en cuanto al otorgamiento de derechos y prerrogativas laborales y la imposición de deberes laborales; l) La negativa a suministrar materiales e información absolutamente indispensables para el cumplimiento de la labor; m) La negativa claramente injustificada a otorgar permisos, licencias por enfermedad, licencias ordinarias y vacaciones, cuando se dan las condiciones legales, reglamentarias o convencionales para pedirlos; n) El envío de anónimos, llamadas telefónicas y mensajes virtuales con contenido injurioso, ofensivo o intimidatorio o el sometimiento a una situación de aislamiento social. En los demás casos no enumerados en este artículo, la autoridad competente valorará, según las circunstancias del caso y la gravedad de las conductas denunciadas, la ocurrencia del acoso laboral descrito en el artículo 2. Excepcionalmente un sólo acto hostil bastará para acreditar el acoso laboral. La autoridad competente apreciará tal circunstancia, según la gravedad de la conducta denunciada y su capacidad de ofender por sí sola la dignidad humana, la vida e integridad física, la libertad sexual y demás derechos fundamentales. Cuando las conductas descritas en este artículo tengan ocurrencias en privado, deberán ser demostradas por los medios de prueba reconocidos en la ley procesal civil.

## 9040 · Ley 769 de 2002 (Codigo Nacional de Transito) · articulo 42

**Categoria:** Accidentes de transito

**Pregunta:** Tuve un accidente de moto y el hospital dice que el SOAT no cubre mis gastos, ¿es cierto?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 42.Seguros obligatorios. Para poder transitar en el territorio nacional todos los vehículos deben estar amparados por un seguro obligatorio vigente. El Seguro Obligatorio de Accidentes de Tránsito, SOAT, se regirá por las normas actualmente vigentes o aquellas que la modifiquen o sustituyan. Parágrafo 1° Los propietarios de los vehículos que registren un buen comportamiento vial por no reportar siniestro que afecten la póliza del Seguro Obligatorio de Accidentes de Tránsito (SOAT), y haber renovado su póliza de manera oportuna, definida como la renovación de la póliza antes de su vencimiento, tendrán derecho a la disminución en el valor del Seguro Obligatorio de Accidentes de Tránsito (SOAT) así: Si en los dos años inmediatamente anteriores al vencimiento de la póliza, registra un buen comportamiento vial; tendrán derecho él un descuento, por única vez, del diez por ciento (10%) sobre el valor de la prima emitida del Seguro Obligatorio de Accidentes de Tránsito (SOAT). Esta medida será aplicable para aquellos propietarios de vehículos que hayan tenido un buen comportamiento durante los años 2020 y 2021, con lo cual se aplicará el descuento a la prima que aplique durante 2022, y de ninguna manera afectará el valor de la contribución a la ADRES, que se calculará sobre el valor de la prima fijado por la Superintendencia Financiera de Colombia. El descuento por única vez a que se refiere el presente parágrafo se otorgará a la combinación entre el vehículo y el tomador del seguro. En ningún caso, el tomador del seguro podrá hacerse acreedor del beneficio más de una vez por el mismo vehículo. Parágrafo 2°. El Gobierno Nacional, en un plazo de tres meses contados a partir de la vigencia de la presente Ley, definirá el procedimiento para la verificación de las condiciones exigidas para acceder al descuento. En ·caso de cambio de propietario de vehículo deberá proceder el cambio de tomador, de manera tal que los beneficios no sean conmutables entre el antiguo y el nuevo propietario. Parágrafo 3°.A partir del 2022, las compañías aseguradoras reconocerán un máximo del 5% de las primas mensuales emitidas por cargos de intermediación por venta del SOAT. Nota: La sentencia C-395 de 2022. Declaró inexequible la expresión “del diez por ciento (10%)” contenida en el parágrafo 1° y todo el parágrafo 3°, adición que fue introducida por el artículo 2 de la ley 2161 del 2021, al artículo 42 de la Ley 769 de 2002.

## 9044 · Ley 1098 de 2006 (Codigo de la Infancia y la Adolescencia) · articulo 111

**Categoria:** Derecho de familia - alimentos

**Pregunta:** Mi ex pareja paga una cuota de alimentos muy baja y ahora mi hija necesita mas, ¿se puede aumentar?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 111.Alimentos. Para la fijación de cuota alimentaria se observarán las siguientes reglas: - 1. La mujer grávida podrá reclamar alimentos a favor del hijo que está por nacer, respecto del padre legítimo o del extramatrimonial que haya reconocido la paternidad. - 2. Siempre que se conozca la dirección donde puede recibir notificaciones el obligado a suministrar alimentos, el defensor o comisario de familia lo citará a audiencia de conciliación. En caso contrario, elaborará informe que suplirá la demanda y lo remitirá al Juez de Familia para que inicie el respectivo proceso. Cuando habiendo sido debidamente citado a la audiencia el obligado no haya concurrido, o habiendo concurrido no se haya logrado la conciliación, fijará cuota provisional de alimentos, pero sólo se remitirá el informe al juez si alguna de las partes lo solicita dentro de los cinco días hábiles siguientes. - 3. Cuando se logre conciliación se levantará acta en la que se indicará: el monto de la cuota alimentaria y la fórmula para su reajuste periódico; el lugar y la forma de su cumplimento; la persona a quien debe hacerse el pago, los descuentos salariales, las garantías que ofrece el obligado y demás aspectos que se estimen necesarios para asegurar el cabal cumplimiento de la obligación alimentaria. De ser el caso, la autoridad promoverá la conciliación sobre custodia, régimen de visitas y demás aspectos conexos. - 4. Lo dispuesto en este artículo se aplicará también al ofrecimiento de alimentos a niños, las niñas o los adolescentes.

## 9044 · Ley 1098 de 2006 (Codigo de la Infancia y la Adolescencia) · articulo 129

**Categoria:** Derecho de familia - alimentos

**Pregunta:** Mi ex pareja paga una cuota de alimentos muy baja y ahora mi hija necesita mas, ¿se puede aumentar?

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 129.Alimentos. En el auto que corre traslado de la demanda o del informe del Defensor de Familia, el juez fijará cuota provisional de alimentos, siempre que haya prueba del vínculo que origina la obligación alimentaria. Si no tiene la prueba sobre la solvencia económica del alimentante, el juez podrá establecerlo tomando en cuenta su patrimonio, posición social, costumbres y en general todos los antecedentes y circunstancias que sirvan para evaluar su capacidad económica. En todo caso se presumirá que devenga al menos el salario mínimo legal. La sentencia podrá disponer que los alimentos se paguen y aseguren mediante la constitución de un capital cuya renta los satisfaga. En tal caso, si el obligado no cumple la orden dentro de los diez días hábiles siguientes, el juez procederá en la forma indicada en el inciso siguiente. El juez deberá adoptar las medidas necesarias para que el obligado cumpla lo dispuesto en el auto que fije la cuota provisional de alimentos, en la conciliación o en la sentencia que los señale. Con dicho fin decretará embargo, secuestro, avalúo y remate de los bienes o derechos de aquél, los cuales se practicarán con sujeción a las reglas del proceso ejecutivo. El embargo se levantará si el obligado paga las cuotas atrasadas y presta caución que garantice el pago de las cuotas correspondientes a los dos años siguientes. Cuando se trate de arreglo privado o de conciliación extrajudicial, con la copia de aquél o del acta de la diligencia el interesado podrá adelantar proceso ejecutivo ante el juez de familia para el cobro de las cuotas vencidas y las que en lo sucesivo se causen. Cuando se tenga información de que el obligado a suministrar alimentos ha incurrido en mora de pagar la cuota alimentaria por más de un mes, el juez que conozca o haya conocido del proceso de alimentos o el que adelante el ejecutivo dará aviso al Departamento Administrativo de Seguridad ordenando impedirle la salida del país hasta tanto preste garantía suficiente del cumplimiento de la obligación alimentaría y será reportado a las centrales de riesgo. La cuota alimentaria fijada en providencia judicial, en audiencia de conciliación o en acuerdo privado se entenderá reajustada a partir de l 1º de enero siguiente y anualmente en la misma fecha, en porcentaje igual al índice de precios al consumidor, sin perjuicio de que el juez, o las partes de común acuerdo, establezcan otra fórmula de reajuste periódico. Con todo, cuando haya variado la capacidad económica del alimentante o las necesidades del alimentario, las partes de común acuerdo podrán modificar la cuota alimentaria, y cualquiera de ellas podrá pedirle al juez su modificación. En este último caso el interesado deberá aportar con la demanda por lo menos una copia informal de la providencia, del acta de conciliación o del acuerdo privado en que haya sido señalada. Mientras el deudor no cumpla o se allane a cumplir la obligación alimentaria que tenga respecto del niño, niña o adolescente, no será escuchado en la reclamación de su custodia y cuidado personal ni en ejercicio de otros derechos sobre él o ella. Lo dispuesto en este artículo se aplicará también al ofrecimiento de alimentos a niños, niñas o adolescentes. El incumplimiento de la obligación alimentaria genera responsabilidad penal.

## 9045 · Constitucion Politica de 1991 · articulo 86

**Categoria:** Accion de tutela

**Pregunta:** Un banco me bloqueo la cuenta sin explicacion, ¿puedo poner una tutela contra un banco aunque sea una empresa privada?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 86. Toda persona tendrá acción de tutela para reclamar ante los jueces, en todo momento y lugar, mediante un procedimiento preferente y sumario, por sí misma o por quien actúe a su nombre, la protección inmediata de sus derechos constitucionales fundamentales, cuando quiera que éstos resulten vulnerados o amenazados por la acción o la omisión de cualquier autoridad pública. La protección consistirá en una orden para que aquél respecto de quien se solicita la tutela, actúe o se abstenga de hacerlo. El fallo, que será de inmediato cumplimiento, podrá impugnarse ante el juez competente y, en todo caso, éste lo remitirá a la Corte Constitucional para su eventual revisión. Esta acción sólo procederá cuando el afectado no disponga de otro medio de defensa judicial, salvo que aquella se utilice como mecanismo transitorio para evitar un perjuicio irremediable. En ningún caso podrán transcurrir más de diez días entre la solicitud de tutela y su resolución. La ley establecerá los casos en los que la acción de tutela procede Contra particulares encargados de la prestación de un servicio público o cuya conducta afecte grave y directamente el interés colectivo, o respecto de quienes el solicitante se halle en estado de subordinación o indefensión.

## 9045 · Decreto 2591 de 1991 (Reglamentacion de la accion de tutela) · articulo 42

**Categoria:** Accion de tutela

**Pregunta:** Un banco me bloqueo la cuenta sin explicacion, ¿puedo poner una tutela contra un banco aunque sea una empresa privada?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 42. Procedencia. La acción de tutela procederá contra acciones u omisiones de particulares en los siguientes casos: - 1. Cuando aquel contra quien se hubiere hecho la solicitud esté encargado de la prestación del servicio público de educación para proteger los derechos consagrados en los artículos 13, 15, 16,18,19, 20, 23, 27, 29, 37 y 38 de la Constitución. - 2. Cuando aquel contra quien se hubiere hecho la solicitud esté encargado de la prestación del servicio público de salud para proteger los derechos a la vida, a la intimidad, a la Igualdad y a la autonomía. - 3. Cuando aquel contra quien se hubiere hecho la solicitud esté encargado de la prestación de servicios públicos domiciliarios. - 4. Cuando la solicitud fuere dirigida contra una organización privada, contra quien la controle efectivamente o fuere el beneficiario real de la situación que motivó la acción, siempre y cuando el solicitante tenga una relación de subordinación o indefensión con tal organización. - 5. Cuando aquel contra quien se hubiere hecho la solicitud viole o amenace violar el artículo 17 de la Constitución. - 6. Cuando la entidad privada sea aquella contra quien se hubiere hecho la solicitud en ejercicio del hábeas data, de conformidad con lo establecido en el artículo 15 de la Constitución. - 7. Cuando se solicite rectificación de informaciones inexactas o erróneas. En este caso se deberá anexar la transcripción de la información o la copia de la publicación y de la rectificación solicitada que no fue publicada en condiciones que aseguren la eficacia de la misma. - 8. Cuando el particular actúe o deba actuar en ejercicio de funciones públicas, en cuyo caso se aplicará el mismo régimen que a las autoridades públicas. - 9. Cuando la solicitud sea para tutelar la vida o la integridad de quien se encuentre en situación de subordinación o indefensión respecto del particular contra el cual se interpuso la acción. Se presume la indefensión del menor que solicite la tutela.

## 9051 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 161

**Categoria:** Relaciones laborales

**Pregunta:** Mi jefe me paso a turnos de noche de un dia para otro y yo tengo un hijo de dos anos.

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> ARTICULO 161. DURACION. La duración máxima de la jornada ordinaria de trabajo es de cuarenta y dos (42) horas a la semana, que podrán ser distribuidas, de común acuerdo, entre empleador y trabajador, en 5 o 6 días a la semana, garantizando siempre el día de descanso, salvo las siguientes excepciones: a) En las labores que sean especialmente insalubres o peligrosas, el Gobierno puede ordenar la reducción de la jornada de trabajo de acuerdo con dictámenes al respecto. b) La duración máxima de la jornada laboral de los adolescentes autorizados para trabajar, se sujetará a las siguientes reglas: (Literal b) Modificado por el Art. 114 de la Ley 1098 de 2006) 1. Los adolescentes mayores de 15 y menores de 17 años, sólo podrán trabajar en jornada diurna máxima de seis horas diarias y treinta horas a la semana y hasta las 6:00 de la tarde. 2. Los adolescentes mayores de diecisiete (17) años, sólo podrán trabajar en una jornada máxima de ocho horas diarias y 40 horas a la semana y hasta las 8:00 de la noche. c) El empleador y el trabajador pueden acordar, temporal o indefinidamente, la organización de turnos de trabajo sucesivos, que permitan operar a la empresa o secciones de la misma sin solución de continuidad durante todos los días de la semana, siempre y cuando el respectivo turno no exceda de seis (6) horas al día y treinta y seis (36) a la semana. En este caso no habrá lugar a recargo nocturno ni al previsto para el trabajo dominical o festivo, pero el trabajador devengará el salario correspondiente a la jornada ordinaria de trabajo, respetando siempre el mínimo legal o convencional y tendrá derecho a un día de descanso remunerado. d) El empleador y el trabajador podrán acordar que la jornada semanal de cuarenta y dos (42) horas se realice mediante jornadas diarias flexibles de trabajo, distribuidas en máximo seis días a la semana con un día de descanso obligatorio, que podrá coincidir con el día domingo. (Literal d) modificado por el Art. 2 de la Ley 1846 de 2017) Así, el número de horas de trabajo diario podrá distribuirse de manera variable durante la respectiva semana, teniendo como mínimo cuatro (4) horas continuas y máximo hasta nueve (9) horas diarias sin lugar a ningún recargo por trabajo suplementario, cuando el número de horas de trabajo no exceda el promedio de cuarenta y dos (42) horas semanales dentro de la Jornada Ordinaria, de conformidad con el artículo 160 de Código Sustantivo del Trabajo. PARÁGRAFO. El empleador no podrá aún con el consentimiento del trabajador, contratarlo para la ejecución de dos turnos en el mismo día, salvo en labores de supervisión, dirección, confianza o manejo. (Modificado por el Art. 2 de la Ley 2101 de 2021) (Modificado por el Art. 20 de la Ley 50 de 1990) (Modificado por el Art. 1 de la Ley 6 de 1981)

## 9052 · Ley 1266 de 2008 (Habeas data financiero) · articulo 13

**Categoria:** Reporte en centrales de riesgo

**Pregunta:** Pague una deuda hace anos y ahora me la volvieron a reportar como si fuera nueva.

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 13. Permanencia de la información. La información de carácter positivo permanecerá de manera indefinida en los bancos de datos de los operadores de información. Los datos cuyo contenido haga referencia al tiempo de mora, tipo de cobro, estado de la tartera y, en general, aquellos datos referentes a una situación de incumplimiento de obligaciones, SD regirán por un término máximo de permanencia, vencido el cual deberá ser retirada de los bancos de datos por el operador, de forma que los usuarios no puedan acceder o consultar dicha información. El término de permanencia de ésta información será el doble del tiempo de la mora, máximo cuatro (4) años contados a partir de la fecha en que sean pagadas las cuotas vencidas o sea extinguida la obligación. Parágrafo 1°. El dato negativo y los datos cuyo contenido haga referencia al tiempo de mora, tipo de cobro, estado de la cartera y, en general aquellos datos referentes a una situación de incumplimiento ele obligaciones caducarán una vez cumplido el término de ocho (8) años, contados a partir del momento en que entre en mora la obligación; cumplido este término deberán ser eliminados de la base de datos. Parágrafo 2°. En las obligaciones inferiores o iguales al (15 %) ce un (1) salario mínimo legal mensual vigente, el dato negativo por obligaciones que se han constituido en mora solo será reportado después de cumplirse con al menos dos comunicaciones, ambas en días diferentes. Y debe mediar entre la última comunicación y reporte, 20 días calendario. Parágrafo 3°. Toda información negativa o desfavorable que se encuentre en bases de datos y se relacione con calificaciones, récord (scorings-score), o cualquier tipo de medición financiera, comercial o crediticia, deberá ser actualizada de manera simultánea con el retiro del dato negativo o con la cesación del hecho que generó la disminución de la medición.

## 9053 · Ley 1266 de 2008 (Habeas data financiero) · articulo 16

**Categoria:** Reporte en centrales de riesgo

**Pregunta:** Me reportaron por una deuda de la empresa donde fui representante legal, no es mia.

**Estado:** recuperado=si · partido en 8 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 16.Peticiones, Consultas y Reclamos. - I. Trámite de consultas. Los titulares de la información o sus causahabientes podrán consultar lainformación personal del titular, que repose en cualquier banco de datos, sea este del sector público o privado. El operador deberá suministrar a estos, debidamente identificados, toda la información contenida en el registro individual o que esté vinculada con la identificación del titular. La petición, consulta de información se formulará verbalmente, por escrito, o por cualquier canal de comunicación, siempre y cuando se mantenga evidencia de la consulta por medios técnicos. La petición o consulta será atendida en un término máximo de diez (10) días hábiles contados a partir de la fecha de recibo de la misma. Cuando no fuere posible atender la petición o consulta dentro de dicho término, se informará al interesado, expresando los motivos de la demora y señalando la fecha en que se atenderá su petición, la cual en ningún caso podrá superar los cinco (5) días hábiles siguientes al vencimiento del primer término. Parágrafo. La petición o consulta se deberá atender de fondo, suministrando integralmente toda la información solicitada. - II. Trámite de reclamos. Los titulares de la información o sus causahabientes que consideren que la información contenida en su registro individual en un banco de datos debe ser objeto de corrección o actualización podrán presentar un reclamo ante el operador, el cual será tramitado bajo las siguientes reglas: - 1. La petición o reclamo se formulará mediante escrito dirigido al operador del banco de datos, con la identificación del titular, la descripción de los hechos que dan lugar al reclamo, la dirección, y si fuere el caso, acompañando los documentos de soporte que se quieran hacer valer. En caso de que el escrito resulte incompleto, se deberá oficiar al interesado para que subsane las fallas. Transcurrido un mes desde la fecha del requerimiento, sin que el solicitante presente la información requerida, se entenderá que ha desistido de la reclamación o petición. - 2. Una vez recibido la petición o reclamo completo el operador incluirá en el registro individual en un término no mayor a dos (2) días hábiles una leyenda que diga "reclamo en trámite" y la naturaleza del mismo. Dicha información deberá mantenerse hasta que el reclamo sea decidido y deberá incluirse en la información que se suministra a los usuarios. - 3. El término máximo para atender la petición o reclamo será de quince (15) días hábiles contados a partir del día siguiente a la fecha de su recibo. Cuando no fuere posible atender la petición dentro de dicho término, se informará al interesado, expresando los motivos de la demora y señalando la fecha en que se atenderá su petición, la cual en ningún caso podrá superar los ocho (8) días hábiles siguientes al vencimiento del primer término. - 4. En los casos en que exista una fuente de información independiente del operador, este último deberá dar traslado del reclamo a la fuente en un término máximo de dos (2) días hábiles, la cual deberá resolver e informar la respuesta al operador en un plazo máximo de diez (10) días hábiles. En todo caso, la respuesta deberá darse al titular por el operador en el término máximo de quince (15) días hábiles contados a partir del día siguiente a la fecha de presentación de la reclamación, prorrogables por ocho (8) días hábiles más, según lo indicado en el numeral anterior. Si el reclamo es presentado ante la fuente, esta procederá a resolver directamente el reclamo, pero deberá informar al operador sobre la recepción del reclamo dentro de los dos (2) días hábiles siguientes a su recibo, de forma que se pueda dar cumplimiento a la obligación de incluir la leyenda que diga "reclamo en trámite" y la naturaleza del mismo dentro del registro individual, lo cual deberá hacer el operador dentro de los dos (2) días hábiles siguientes a haber recibido la información de la fuente. - 5. Para dar respuesta a la petición o reclamo, el operador o la fuente, según sea el caso, deberá realizar una verificación completa de las observaciones o planteamientos del titular, asegurándose de revisar toda la información pertinente para poder dar una respuesta completa al titular. - 6. Sin perjuicio del ejercido de la acción de tutela para amparar el derecho fundamental del habeas data, en caso que el titular no se encuentre satisfecho con la respuesta a la petición, podrá recurrir al proceso judicial correspondiente dentro de los términos legales pertinentes para debatir lo relacionado con la obligación reportada como incumplida. La demanda deberá ser interpuesta contra la fuente de la información la cual, una vez notificada de la misma, procederá a informar al operador dentro de los dos (2) días hábiles siguientes, de forma que se pueda dar cumplimiento a la obligación de incluir la leyenda que diga "información en discusión judicial" y la naturaleza de la misma dentro del registro individual, lo cual deberá hacer el operador dentro de los dos (2) días hábiles siguientes a haber recibido la información de la fuente y por todo el tiempo que tome obtener un fallo en firme. Igual procedimiento deberá seguirse en caso que la fuente inicie un proceso judicial contra el titular de la información, referente a la obligación reportada como incumplida, y éste proponga excepciones de mérito. - 7. De los casos de suplantación. En el caso que el titular de la información manifieste ser víctima del delito de falsedad personal contemplado en el Código Penal, y le sea exigido el pago de obligaciones como resultado de la conducta punible de la que es víctima, deberá presentar petición de corrección ante la fuente adjuntando los soportes correspondientes. La fuente una vez reciba la solicitud, deberá dentro de los diez (10) días siguientes cotejar los documentos utilizados para adquirir la obligación que se disputa, con los documentos allegados por el titular en la petición, los cuales se tendrán como prueba sumaria para probar la falsedad, la fuente, si así lo considera, deberá denunciar el delito de estafa del que haya podido ser víctima. Con la solicitud presentada por el titular, el dato negativo, récord del (scorings-score) y cualquier otro dato que refleje el comportamiento del titular, deberán ser modificados por la fuente reflejando que la víctima de falsedad no es quien adquirió las obligaciones, y se incluirá una leyenda dentro del registro personal que diga -Víctima de Falsedad Personal-. - 8. Silencio. Las peticiones o reclamos deberán resolverse dentro de los quince (15) días hábiles siguientes a la fecha de su recibo. Prorrogables por ocho (8) días hábiles más, según lo indicado en el numeral 3, parte 11, artículo 16 de la presente ley. Si en ese lapso no se ha dado pronta resolución, se entenderá, para todos los efectos legales, que la respectiva solicitud ha sido aceptada. Si no lo hiciere, el peticionario podrá solicitar a la Superintendencia de Industria y Comercio y a la Superintendencia Financiera de Colombia, según el caso, la imposición de las sanciones a que haya lugar conforme a la presente ley, sin perjuicio de que ellas adopten las decisiones que resulten pertinentes para hacer efectivo el derecho al habeas data de los titulares. TITULO VI VIGILANCIA DE LOS DESTINATARIOS DE LA LEY

## 9054 · Ley 769 de 2002 (Codigo Nacional de Transito) · articulo 144

**Categoria:** Accidentes de transito

**Pregunta:** Me chocaron el carro estando parqueado y el otro conductor dejo una nota con su numero.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 144.Informe policial. En los casos en que no fuere posible la conciliación entre los conductores, el agente de tránsito que conozca el hecho levantará un informe descriptivo de sus pormenores, con copia inmediata a los conductores, quienes deberán suscribirlas, y si éstos se negaren a hacerlo bastará la firma de un testigo mayor de edad. El informe contendrá por lo menos: Lugar, fecha y hora en que ocurrió el hecho. Clase de vehículo, número de la placa y demás características. Nombre del conductor o conductores, documento de identidad, número de la licencia o licencias de conducción, lugar y fecha de expedición, dirección, teléfono, domicilio o residencia de los involucrados. Nombre del propietario o tenedor del vehículo o de los propietarios o tenedores de los vehículos. Nombre, documento de identidad y dirección de los testigos. Estado de seguridad, en general, del vehículo o de los vehículos, de los frenos, de la dirección, de las luces, bocinas y llantas. Estado de la vía, huella de frenada, grado de visibilidad, colocación de los vehículos y distancia, entre otros, la cual constará en el croquis levantado. Descripción de los daños y lesiones. Relación de los medios de prueba aportados por las partes. Descripción de las compañías de seguros y números de las pólizas de los seguros obligatorios exigidos por este código.

## 9054 · Ley 769 de 2002 (Codigo Nacional de Transito) · articulo 149

**Categoria:** Accidentes de transito

**Pregunta:** Me chocaron el carro estando parqueado y el otro conductor dejo una nota con su numero.

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 149.Descripción. En los casos a que se refiere el artículo anterior, el agente de tránsito que conozca el hecho levantará un informe descriptivo de sus pormenores, con copia inmediata a los conductores, quienes deberán firmarlas y en su defecto, la firmará un testigo. El informe contendrá por lo menos: Lugar, fecha y hora en que ocurrió el hecho. Clase de vehículo, número de la placa y demás características. Nombre del conductor o conductores, documentos de identidad, número de la licencia o licencias de conducción, lugar y fecha de su expedición y número de la póliza de seguro y compañía aseguradora, dirección o residencia de los involucrados. Nombre del propietario o tenedor del vehículo o de los propietarios o tenedores de los vehículos. Nombre, documentos de identidad y dirección de los testigos. Estado de seguridad, en general, del vehículo o de los vehículos, de los frenos, de la dirección, de las luces, bocinas y llantas. Estado de la vía, huella de frenada, grado de visibilidad, colocación de los vehículos y distancia, la cual constará en el croquis levantado. Descripción de los daños y lesiones. Relación de los medios de prueba aportados por las partes. Descripción de las compañías de seguros y números de las pólizas de los seguros obligatorios exigidos por este código. En todo caso en que produzca lesiones personales u homicidio en accidente de tránsito, la autoridad de tránsito deberá enviar a los conductores implicados a la práctica de la prueba de embriaguez, so pena de considerarse falta disciplinaria grave para el funcionario que no dé cumplimiento a esta norma. El informe o el croquis, o los dos, serán entregados inmediatamente a los interesados y a la autoridad instructora competente en materia penal. El funcionario de tránsito que no entregue copia de estos documentos a los interesados o a las autoridades instructoras, incurrirá en causal de mala conducta. Para efectos de determinar la responsabilidad, en cuanto al tránsito, las autoridades instructoras podrán solicitar pronunciamiento sobre el particular a las autoridades de tránsito competentes. CAPITULO VIII Actuación en caso de embriaguez

## 9059 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 43

**Categoria:** Derecho contractual general

**Pregunta:** Firme un contrato de servicios y ahora me cobran una penalidad que no estaba en lo que me mostraron.

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 43. Cláusulas abusivas ineficaces de pleno derecho. Son ineficaces de pleno derecho las cláusulas que: - 1. Limiten la responsabilidad del productor o proveedor de las obligaciones que por ley les corresponden; - 2. Impliquen renuncia de los derechos del consumidor que por ley les corresponden; - 3. Inviertan la carga de la prueba en perjuicio del consumidor; - 4. Trasladen al consumidor o un tercero que no sea parte del contrato la responsabilidad del productor o proveedor; - 5. Establezcan que el productor o proveedor no reintegre lo pagado si no se ejecuta en todo o en parte el objeto contratado; - 6. Vinculen al consumidor al contrato, aun cuando el productor o proveedor no cumpla sus obligaciones; - 7. Concedan al productor o proveedor la facultad de determinar unilateralmente si el objeto y la ejecución del contrato se ajusta a lo estipulado en el mismo; - 8. Impidan al consumidor resolver el contrato en caso que resulte procedente excepcionar el incumplimiento del productor o proveedor, salvo en el caso del arrendamiento financiero; - 9. Presuman cualquier manifestación de voluntad del consumidor, cuando de esta se deriven erogaciones u obligaciones a su cargo; - 10. Incluyan el pago de intereses no autorizados legalmente, sin perjuicio de la eventual responsabilidad penal. - 11. Para la terminación del contrato impongan al consumidor mayores requisitos a los solicitados al momento de la celebración del mismo, o que impongan mayores cargas a las legalmente establecidas cuando estas existan; - 12. Derogado. - 13. Restrinjan o eliminen la facultad del usuario del bien para hacer efectivas directamente ante el productor y/o proveedor las garantías a que hace referencia la presente ley, en los contratos de arrendamiento financiero y arrendamiento de bienes muebles. - 14. Cláusulas de renovación automática que impidan al consumidor dar por terminado el contrato en cualquier momento o que imponga sanciones por la terminación anticipada, a excepción de lo contemplado en el artículo 41 de la presente ley.

## 9061 · Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana) · articulo 33

**Categoria:** Derecho ambiental sancionatorio

**Pregunta:** La empresa vecina hace ruido toda la noche y dice que tiene permiso ambiental.

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> ARTÍCULO 33. Comportamientos que afectan la -tranquilidad y relaciones respetuosas de las personas. Los siguientes comportamientos afectan la tranquilidad y relaciones respetuosas de las personas y por lo tanto no deben efectuarse: 1. En el vecindario o lugar de habitación urbana o rural: Perturbar o permitir que se afecte el sosiego con: a) Sonidos o ruidos en actividades, fiestas, reuniones o eventos similares que afecten la convivencia del vecindario, cuando generen molestia por su impacto auditivo, en cuyo caso podrán las autoridades de Policía desactivar temporalmente la fuente del ruido, en caso de que el residente se niegue a desactivarlo; ((Declarado EXEQUIBLE, con excepción de la expresion subrayada, que fue declarada condicionalmente exequible, mediante Sentencia de la Corte Constitucional C-308 de 2019) b) Cualquier medio de producción de sonidos o dispositivos o accesorios o maquinaria que produzcan ruidos, desde bienes muebles o inmuebles, en cuyo caso podrán las autoridades identificar, registrar y desactivar temporalmente la fuente del ruido, salvo sean originados en construcciones o reparaciones en horas permitidas; (Declarado condicionalmente exequible, mediante Sentencia de la Corte Constitucional C-308 de 2019) c) Actividades diferentes a las aquí señaladas en vía pública o en privado, cuando trascienda a lo público, y perturben o afecten la tranquilidad de las personas. 2. En espacio público, lugares abiertos al público, o que siendo privados trasciendan a lo público: a) Irrespetar las normas propias de los lugares públicos tales como salas de velación, cementerios, clínicas, hospitales, bibliotecas y museos, entre otros. b) Realizar actos sexuales o de exhibicionismo que generen molestia a la comunidad. c) Consumir sustancias alcohólicas, psicoactivas o prohibidas, no autorizados para su consumo. (Declarado INEXEQUIBLE, expresión subrayada, mediante Sentencia de la Corte Consitucional C-253 de 2019) d) Fumar en lugares prohibidos. e) Limitar u obstruir las manifestaciones de afecto y cariño que no configuren actos sexuales o de exhibicionismo en razón a la raza, origen nacional o familiar, orientación sexual, identidad de género u otra condición similar. PARÁGRAFO 1. Quien incurra en uno o más de los comportamientos antes señalados, será objeto de la aplicación de las siguientes medidas correctivas: COMPORTAMIENTOS Y MEDIDA CORRECTIVA A APLICAR: Numeral 1: Multa General tipo 3; Disolución de reunión o actividad que involucra aglomeraciones de público no complejas. Numeral 2, literal a: Multa General tipo 3 Numeral 2, literal b: Multa General tipo 3 Numeral 2, literal c: Multa General tipo 2; Disolución de reunión o actividad que involucra aglomeraciones de público no complejas. Numeral 2, literal d: Amonestación. Numeral 2, literal e: Multa general tipo 1. PARÁGRAFO 2. No constituyen actos sexuales o de exhibicionismo los besos o caricias que las personas, sin importar su género, color de piel, orientación sexual o identidad de género, manifiesten como expresiones de cariño, en ejercicio de su derecho al libre desarrollo de la personalidad.” (Corregido por el Art. 2 del Decreto 555 de 2017) CAPÍTULO II DE LOS ESTABLECIMIENTOS EDUCATIVOS

## 9064 · Ley 1437 de 2011 (CPACA) · articulo 21

**Categoria:** Derecho administrativo general

**Pregunta:** Le pedi una informacion a la alcaldia y me respondieron algo que no tiene nada que ver con lo que pregunte.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 21. Funcionario sin competencia. Si la autoridad a quien se dirige la petición no es la competente, se informará de inmediato al interesado si este actúa verbalmente, o dentro de los cinco (5) días siguientes al de la recepción, si obró por escrito. Dentro del término señalado remitirá la petición al competente y enviará copia del oficio remisorio al peticionario o en caso de no existir funcionario competente así se lo comunicará. Los términos para decidir o responder se contarán a partir del día siguiente a la recepción de la Petición por la autoridad competente.

## 9065 · Decision 486 de 2000 (Regimen Comun sobre Propiedad Industrial, CAN) · articulo 136

**Categoria:** Propiedad intelectual - marcas

**Pregunta:** Un competidor registro un nombre casi igual al mio y yo llevo anos usandolo sin registrar.

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 136.- No podrán registrarse como marcas aquellos signos cuyo uso en el comercio afectara indebidamente un derecho de tercero, en particular cuando: a) sean idénticos o se asemejen, a una marca anteriormente solicitada para registro o registrada por un tercero, para los mismos productos o servicios, o para productos o servicios respecto de los cuales el uso de la marca pueda causar un riesgo de confusión o de asociación; b) sean idénticos o se asemejen a un nombre comercial protegido, o, de ser el caso, a un rótulo o enseña, siempre que dadas las circunstancias, su uso pudiera originar un riesgo de confusión o de asociación; c) sean idénticos o se asemejen a un lema comercial solicitado o registrado, siempre que dadas las circunstancias, su uso pudiera originar un riesgo de confusión o de asociación; d) sean idénticos o se asemejen a un signo distintivo de un tercero, siempre que dadas las circunstancias su uso pudiera originar un riesgo de confusión o de asociación, cuando el solicitante sea o haya sido un representante, un distribuidor o una persona expresamente autorizada por el titular del signo protegido en el País Miembro o en el extranjero; e) consistan en un signo que afecte la identidad o prestigio de personas jurídicas con o sin fines de lucro, o personas naturales, en especial, tratándose del nombre, apellido, firma, título, hipocorístico, seudónimo, imagen, retrato o caricatura de una persona distinta del solicitante o identificada por el sector pertinente del público como una persona distinta del solicitante, salvo que se acredite el consentimiento de esa persona o, si hubiese fallecido, el de quienes fueran declarados sus herederos; f) consistan en un signo que infrinja el derecho de propiedad industrial o el derecho de autor de un tercero, salvo que medie el consentimiento de éste; g) consistan en el nombre de las comunidades indígenas, afroamericanas o locales, o las denominaciones, las palabras, letras, caracteres o signos utilizados para distinguir sus productos, servicios o la forma de procesarlos, o que constituyan la expresión de su cultura o práctica, salvo que la solicitud sea presentada por la propia comunidad o con su consentimiento expreso; y, h) constituyan una reproducción, imitación, traducción, transliteración o transcripción, total o parcial, de un signo distintivo notoriamente conocido cuyo titular sea un tercero, cualesquiera que sean los productos o servicios a los que se aplique el signo, cuando su uso fuese susceptible de causar un riesgo de confusión o de asociación con ese tercero o con sus productos o servicios; un aprovechamiento injusto del prestigio del signo; o la dilución de su fuerza distintiva o de su valor comercial o publicitario.

## 9067 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 1318

**Categoria:** Contratos empresariales (B2B)

**Pregunta:** El distribuidor esta vendiendo mi producto en una ciudad donde yo le di la exclusividad a otro.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 1318. EXCLUSIVIDAD A FAVOR DEL AGENTE Salvo pacto en contrario, el empresario no podrá servirse de varios agentes en una misma zona y para el mismo ramo de actividades o productos.

## 9069 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 292

**Categoria:** Procedimiento civil - recursos

**Pregunta:** Me notificaron por un correo electronico que yo nunca autorice para eso.

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo y por eso el caso cuenta como acierto. ¿Responde de verdad la consulta?

**Texto del articulo:**

> Artículo 292. Notificación por aviso. Cuando no se pueda hacer la notificación personal del auto admisorio de la demanda o del mandamiento ejecutivo al demandado, o la del auto que ordena citar a un tercero, o la de cualquiera otra providencia que se debe realizar personalmente, se hará por medio de aviso que deberá expresar su fecha y la de la providencia que se notifica, el juzgado que conoce del proceso, su naturaleza, el nombre de las partes y la advertencia de que la notificación se considerará surtida al finalizar el día siguiente al de la entrega del aviso en el lugar de destino. Cuando se trate de auto admisorio de la demanda o mandamiento ejecutivo, el aviso deberá ir acompañado de copia informal de la providencia que se notifica. El aviso será elaborado por el interesado, quien lo remitirá a través de servicio postal autorizado a la misma dirección a la que haya sido enviada la comunicación a que se refiere el numeral 3 del artículo anterior. La empresa de servicio postal autorizado expedirá constancia de haber sido entregado el aviso en la respectiva dirección, la cual se incorporará al expediente, junto con la copia del aviso debidamente cotejada y sellada. En lo pertinente se aplicará lo previsto en el artículo anterior. Cuando se conozca la dirección electrónica de quien deba ser notificado, el aviso y la providencia que se notifica podrán remitirse por el Secretario o el interesado por medio de correo electrónico. Se presumirá que el destinatario ha recibido el aviso cuando el iniciador recepcione acuse de recibo. En este caso, se dejará constancia de ello en el expediente y adjuntará una impresión del mensaje de datos.


---

# Clase B' -- candidatos a omision (si responden, el fallo es falso)

62 filas en 18 casos.

## 9004 · Ley 1751 de 2015 (Ley Estatutaria de Salud) · articulo 10

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS me autorizo una cirugia pero llevo 3 meses esperando la cita sin que me den fecha, ¿que hago?

**Estado:** recuperado=si · partido en 4 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 10. Derechos y deberes de las personas, relacionados con la prestación del servicio de salud. Las personas tienen los siguientes derechos relacionados con la prestación del servicio de salud: a) A acceder a los servicios y tecnologías de salud, que le garanticen una atención integral, oportuna y de alta calidad; b) Recibir la atención de urgencias que sea requerida con la oportunidad que su condición amerite sin que sea exigible documento o cancelación de pago previo alguno; c) A mantener una comunicación plena, permanente, expresa y clara con el profesional de la salud tratante; d) A obtener una información clara, apropiada y suficiente por parte del profesional de la salud tratante que le permita tomar decisiones libres, conscientes e informadas respecto de los procedimientos que le vayan a practicar y riesgos de los mismos. Ninguna persona podrá ser obligada, contra su voluntad, a recibir tratamiento de salud; e) A recibir prestaciones de salud en las condiciones y términos consagrados en la ley; f) A recibir un trato digno, respetando sus creencias y costumbres, así como las opiniones personales que tengan sobre los procedimientos; g) A que la historia clínica sea tratada de manera confidencial y reservada y que únicamente pueda ser conocida por terceros, previa autorización del paciente o en los casos previstos en la ley, y a poder consultar la totalidad de su historia clínica en forma gratuita y a obtener copia de la misma; h) A que se le preste durante todo el proceso de la enfermedad, asistencia de calidad por trabajadores de la salud debidamente capacitados y autorizados para ejercer; i) A la provisión y acceso oportuno a las tecnologías y a los medicamentos requeridos; j) A recibir los servicios de salud en condiciones de higiene, seguridad y respeto a su intimidad; k) A la intimidad. Se garantiza la confidencialidad de toda información que sea suministrada en el ámbito del acceso a los servicios de salud y de las condiciones de salud y enfermedad de la persona, sin perjuicio de la posibilidad de acceso a la misma por los familiares en los eventos autorizados por la ley o las autoridades en las condiciones que esta determine; l) A recibir información sobre los canales formales para presentar reclamaciones, quejas, sugerencias y en general, para comunicarse con la administración de las instituciones, así como a recibir una respuesta por escrito; m) A solicitar y recibir explicaciones o rendición de cuentas acerca de los costos por los tratamientos de salud recibidos; n) A que se le respete la voluntad de aceptación o negación de la donación de sus órganos de conformidad con la ley; o) A no ser sometido en ningún caso a tratos crueles o inhumanos que afecten su dignidad, ni a ser obligados a soportar sufrimiento evitable, ni obligados a padecer enfermedades que pueden recibir tratamiento; p) A que no se trasladen las cargas administrativas y burocráticas que les corresponde asumir a los encargados o intervinientes en la prestación del servicio; q) Agotar las posibilidades de tratamiento para la superación de su enfermedad. Son deberes de las personas relacionados con el servicio de salud, los siguientes: a) Propender por su autocuidado, el de su familia y el de su comunidad; b) Atender oportunamente las recomendaciones formuladas en los programas de promoción y prevención; c) Actuar de manera solidaria ante las situaciones que pongan en peligro la vida o la salud de las personas; d) Respetar al personal responsable de la prestación y administración de los servicios salud; e) Usar adecuada y racionalmente las prestaciones ofrecidas, así como los recursos del sistema; f) Cumplir las normas del sistema de salud; g) Actuar de buena fe frente al sistema de salud; h) Suministrar de manera oportuna y suficiente la información que se requiera para efectos del servicio; i) Contribuir solidariamente al financiamiento de los gastos que demande la atención en salud y la seguridad social en salud, de acuerdo con su capacidad de pago Parágrafo 1°. Los efectos del incumplimiento de estos deberes solo podrán ser determinados por el legislador. En ningún caso su incumplimiento podrá ser invocado para impedir o restringir el acceso oportuno a servicios de salud requeridos. En ningún caso su incumplimiento podrá ser invocado para impedir o restringir el acceso oportuno a servicios de salud requeridos. Parágrafo 2°. El Estado deberá definir las políticas necesarias para promover el cumplimiento de los deberes de las personas, sin perjuicio de lo establecido en el parágrafo 1°.

## 9004 · Decreto 2591 de 1991 (Reglamentacion de la accion de tutela) · articulo 17

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS me autorizo una cirugia pero llevo 3 meses esperando la cita sin que me den fecha, ¿que hago?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 17. Corrección de la solicitud. Si no pudiere determinarse el hecho o la razón que motiva la solicitud de tutela se prevendrá al solicitante para que la corrija en el término de tres días los cuales deberán señalarse concretamente en la correspondiente providencia. Si no las corrigiere, la solicitud podrá ser rechazada de plano. Si la solicitud fuere verbal, el juez procederá a corregirla en el acto, con la información adicional que le proporcione el solicitante.

## 9007 · Ley 84 de 1873 (Codigo Civil) · articulo 2172

**Categoria:** Prestamos informales y usura

**Pregunta:** Un conocido me presto dinero y me esta cobrando un interes que me parece exagerado, ¿como se si es usura?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 2172. No podrá el mandatario colocar a interés dineros del mandante sin su espresa autorizacion. Colocándolos a mayor interés que el designado por el mandante, deberá abonárselo íntegramente, salvo que se la haya autorizado para apropiarse el exceso.

## 9007 · Ley 84 de 1873 (Codigo Civil) · articulo 2234

**Categoria:** Prestamos informales y usura

**Pregunta:** Un conocido me presto dinero y me esta cobrando un interes que me parece exagerado, ¿como se si es usura?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Art. 2234. Si se han estipulado intereses, i el mutuante ha dado carta de pago por el capital, sin reservar expresamente los intereses, se presumirán pagados.

## 9007 · Ley 84 de 1873 (Codigo Civil) · articulo 2309

**Categoria:** Prestamos informales y usura

**Pregunta:** Un conocido me presto dinero y me esta cobrando un interes que me parece exagerado, ¿como se si es usura?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Art. 2309. El que administra un negocio ajeno contra la espresa prohibición del interesado no tiene demanda contra él, sino en cuanto esa jestion le hubiere sido efectivamente útil, i existiere la utilidad al tiempo de la demanda, por ejemplo, si de la jestion ha resultado la estinción de una deuda que, sin ella, hubiere debido pagar el interesado. El Juez, sin embargo, concederá en este caso al interesado el plazo que pida para el pago de la demanda, i que por las circunstancias del demandado parezca equitativo.

## 9007 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 1163

**Categoria:** Prestamos informales y usura

**Pregunta:** Un conocido me presto dinero y me esta cobrando un interes que me parece exagerado, ¿como se si es usura?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 1163. PRESUNCIÓN Y PAGO DE INTERESES. Salvo pacto expreso en contrario, el mutuario deberá pagar al mutuante los intereses legales comerciales de las sumas de dinero o del valor de las cosas recibidas en mutuo. Salvo reserva expresa, el documento de recibo de los intereses correspondientes a un período de pago hará presumir que se han pagado los anteriores.

## 9009 · Ley 1437 de 2011 (CPACA) · articulo 141

**Categoria:** Acceso a informacion publica

**Pregunta:** Le pedi a la alcaldia informacion sobre un contrato publico y me dijeron que es confidencial, ¿pueden negarse asi como asi?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 141.Controversias contractuales. Cualquiera de las partes de un contrato del Estado podrá pedir que se declare su existencia o su nulidad, que se ordene su revisión, que se declare su incumplimiento, que se declare la nulidad de los actos administrativos contractuales, que se condene al responsable a indemnizar los perjuicios, y que se hagan otras declaraciones y condenas. Así mismo, el interesado podrá solicitar la liquidación judicial del contrato cuando esta no se haya logrado de mutuo acuerdo y la entidad estatal no lo haya liquidado unilateralmente dentro de los dos (2) meses siguientes al vencimiento del plazo convenido para liquidar de mutuo acuerdo o, en su defecto, del término establecido por la ley. Los actos proferidos antes de la celebración del contrato, con ocasión de la actividad contractual, podrán demandarse en los términos de los artículos 137 y 138 de este Código, según el caso. El Ministerio Público o un tercero que acredite un interés directo podrán pedir que se declare la nulidad absoluta del contrato. El juez administrativo podrá declararla de oficio cuando esté plenamente demostrada en el proceso, siempre y cuando en él hayan intervenido las partes contratantes o sus causahabientes.

## 9009 · Ley 1437 de 2011 (CPACA) · articulo 217

**Categoria:** Acceso a informacion publica

**Pregunta:** Le pedi a la alcaldia informacion sobre un contrato publico y me dijeron que es confidencial, ¿pueden negarse asi como asi?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 217.Declaración de representantes de las entidades públicas. No valdrá la confesión de los representantes de las entidades públicas cualquiera que sea el orden al que pertenezcan o el régimen jurídico al que estén sometidas. Sin embargo, podrá pedirse que el representante administrativo de la entidad rinda informe escrito bajo juramento, sobre los hechos debatidos que a ella conciernan, determinados en la solicitud. El Juez ordenará rendir informe dentro del término que señale, con la advertencia de que si no se remite en oportunidad sin motivo justificado o no se rinde en forma explícita, se impondrá al responsable una multa de cinco (5) a diez (10) salarios mínimos mensuales legales vigentes.

## 9009 · Ley 1712 de 2014 (Ley de Transparencia) · articulo 9

**Categoria:** Acceso a informacion publica

**Pregunta:** Le pedi a la alcaldia informacion sobre un contrato publico y me dijeron que es confidencial, ¿pueden negarse asi como asi?

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 9°.Información mínima obligatoria respecto a la estructura del sujeto obligado. Todo sujeto obligado deberá publicar la siguiente información mínima obligatoria de manera proactiva en los sistemas de información del Estado o herramientas que lo sustituyan: - a) La descripción de su estructura orgánica, funciones y deberes, la ubicación de sus sedes y áreas, divisiones o departamentos, y sus horas de atención al público; - b) Su presupuesto general, ejecución presupuestal histórica anual y planes de gasto público para cada año fiscal, de conformidad con el artículo 74 de la Ley 1474 de 2011; - c) Un directorio que incluya el cargo, direcciones de correo electrónico y teléfono del despacho de los empleados y funcionarios y las escalas salariales correspondientes a las categorías de todos los servidores que trabajan en el sujeto obligado, de conformidad con el formato de información de servidores públicos y contratistas; - d) Todas las normas generales y reglamentarias, políticas, lineamientos o manuales, las metas y objetivos de las unidades administrativas de conformidad con sus programas operativos y los resultados de las auditorías al ejercicio presupuestal e indicadores de desempeño; - e) Su respectivo plan de compras anual, así como las contrataciones adjudicadas para la correspondiente vigencia en lo relacionado con funcionamiento e inversión, las obras públicas, los bienes adquiridos, arrendados y en caso de los servicios de estudios o investigaciones deberá señalarse el tema específico, de conformidad con el artículo 74 de la Ley 1474 de 2011. En el caso de las personas naturales con contratos de prestación de servicios, deberá publicarse el objeto del contrato, monto de los honorarios y direcciones de correo electrónico, de conformidad con el formato de información de servidores públicos y contratistas; - f) Los plazos de cumplimiento de los contratos; - g) Publicar el Plan Anticorrupción y de Atención al Ciudadano, de conformidad con el artículo 73 de la Ley 1474 de 2011. Parágrafo 1°. La información a que se refiere este artículo deberá publicarse de tal forma que facilite su uso y comprensión por las personas, y que permita asegurar su calidad, veracidad, oportunidad y confiabilidad. Parágrafo 2°. En relación a los literales c) y e) del presente artículo, el Departamento Administrativo de la Función Pública establecerá un formato de información de los servidores públicos y de personas naturales con contratos de prestación de servicios, el cual contendrá los nombres y apellidos completos, ciudad de nacimiento, formación académica, experiencia laboral y profesional de los funcionarios y de los contratistas. Se omitirá cualquier información que afecte la privacidad y el buen nombre de los servidores públicos y contratistas, en los términos definidos por la Constitución y la ley. Parágrafo 3°. Sin perjuicio a lo establecido en el presente artículo, los sujetos obligados deberán observar lo establecido por la estrategia de gobierno en línea, o la que haga sus veces, en cuanto a la publicación y divulgación de la información.

## 9009 · Ley 1712 de 2014 (Ley de Transparencia) · articulo 21

**Categoria:** Acceso a informacion publica

**Pregunta:** Le pedi a la alcaldia informacion sobre un contrato publico y me dijeron que es confidencial, ¿pueden negarse asi como asi?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 21. Divulgación parcial y otras reglas. En aquellas circunstancias en que la totalidad de la información contenida en un documento no esté protegida por una excepción contenida en la presente ley, debe hacerse una versión pública que mantenga la reserva únicamente de la parte indispensable. La información pública que no cae en ningún supuesto de excepción deberá ser entregada a la parte solicitante, así como ser de conocimiento público. La reserva de acceso a la información opera respecto del contenido de un documento público pero no de su existencia. Ninguna autoridad pública puede negarse a indicar si un documento obra o no en su poder o negar la divulgación de un documento, salvo que el daño causado al interés protegido sea mayor al interés público de obtener acceso a la información. Las excepciones de acceso a la información contenidas en la presente ley no aplican en casos de violación de derechos humanos o delitos de lesa humanidad, y en todo caso deberán protegerse los derechos de las víctimas de dichas violaciones.

## 9010 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 526

**Categoria:** Conciliacion prejudicial

**Pregunta:** Quiero demandar a mi ex-socio de negocio por un dinero que me debe, ¿tengo que hacer algo antes de ir directo a la demanda?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 526. Vinculación de la sociedad y los socios. Antes del traslado de la demanda el Juez ordenará al representante legal de la sociedad que de manera inmediata informe a todos los socios la existencia del proceso.

## 9035 · Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana) · articulo 8

**Categoria:** Arriendo

**Pregunta:** Ya entregue el apartamento y el arrendador no me devuelve el deposito, ¿que hago?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 8º. Obligaciones del arrendador. Son obligaciones del arrendador, las siguientes: - 1. Entregar al arrendatario en la fecha convenida, o en el momento de la celebración del contrato, el inmueble dado en arrendamiento en buen estado de servicio, seguridad y sanidad y poner a su disposición los servicios, cosas o usos conexos y los adicionales convenidos. - 2. Mantener en el inmueble los servicios, las cosas y los usos conexos y adicionales en buen estado de servir para el fin convenido en el contrato. - 3. Cuando el contrato de arrendamiento de vivienda urbana conste por escrito, el arrendador deberá suministrar tanto al arrendatario como al codeudor, cuando sea el caso, copia del mismo con firmas originales. Esta obligación deberá ser satisfecha en el plazo máximo de diez (10) días contados a partir de la fecha de celebración del contrato. - 4. Cuando se trate de viviendas sometidas a régimen de propiedad horizontal, el arrendador deberá entregar al arrendatario una copia de la parte normativa del mismo. En el caso de vivienda compartida, el arrendador tiene además, la obligación de mantener en adecuadas condiciones de funcionamiento, de seguridad y de sanidad las zonas o servicios de uso común y de efectuar por su cuenta las reparaciones y sustituciones necesarias, cuando no sean atribuibles a los arrendatarios, y de garantizar el mantenimiento del orden interno de la vivienda; - 5. Las demás obligaciones consagradas para los arrendadores en el Capítulo II, Título XXVI, Libro 4 del Código Civil. Parágrafo. El incumplimiento del numeral tercero del presente artículo será sancionado, a petición de parte, por la autoridad competente, con multas equivalentes a tres (3) mensualidades de arrendamiento.

## 9035 · Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana) · articulo 15

**Categoria:** Arriendo

**Pregunta:** Ya entregue el apartamento y el arrendador no me devuelve el deposito, ¿que hago?

**Estado:** recuperado=si · partido en 5 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 15. Reglas sobre los servicios públicos domiciliarios y otros. Cuando un inmueble sea entregado en arriendo, a través de contrato verbal o escrito, y el pago de los servicios públicos corresponda al arrendatario, se deberá proceder de la siguiente manera, con la finalidad de que el inmueble entregado a título de arrendamiento no quede afecto al pago de los servicios públicos domiciliarios: - 1. Al momento de la celebración del contrato, el arrendador podrá exigir al arrendatario la prestación de garantías o fianzas con el fin de garantizar a cada empresa prestadora de servicios públicos domiciliarios el pago de las facturas correspondientes. La garantía o depósito, en ningún caso, podrá exceder el valor de los servicios públicos correspondientes al cargo fijo, al cargo por aportes de conexión y al cargo por unidad de consumo, correspondiente a dos (2) períodos consecutivos de facturación, de conformidad con lo establecido en el artículo 18 de la Ley 689 de 2001. El cargo fijo por unidad de consumo se establecerá por el promedio de los tres (3) últimos períodos de facturación, aumentado en un cincuenta por ciento (50%). - 2. Prestadas las garantías o depósitos a favor de la respectiva empresa de servicios públicos domiciliarios, el arrendador denunciará ante la respectiva empresa, la existencia del contrato de arrendamiento y remitirá las garantías o depósitos constituidos. El arrendador no será responsable y su inmueble dejará de estar afecto al pago de los servicios públicos, a partir del vencimiento del período de facturación correspondiente a aquél en el que se efectúa la denuncia del contrato y se remitan las garantías o depósitos constituidos. - 3. El arrendador podrá abstenerse de cumplir las obligaciones derivadas del contrato de arrendamiento hasta tanto el arrendatario no le haga entrega de las garantías o fianzas constituidas. El arrendador podrá dar por terminado de pleno derecho el contrato de arrendamiento, si el arrendatario no cumple con esta obligación dentro de un plazo de quince (15) días hábiles contados a partir de la fecha de celebración del contrato. - 4. Una vez notificada la empresa y acaecido el vencimiento del período de facturación, la responsabilidad sobre el pago de los servicios públicos recaerá única y exclusivamente en el arrendatario. En caso de no pago, la empresa de servicios públicos domiciliarios podrá hacer exigibles las garantías o depósitos constituidos, y si éstas no fueren suficientes, podrá ejercer las acciones a que hubiere lugar contra el arrendatario. - 5. En cualquier momento de ejecución del contrato de arrendamiento o a la terminación del mismo, el arrendador, propietario, arrendatario o poseedor del inmueble podrá solicitar a la empresa de servicios públicos domiciliarios, la reconexión de los servicios en el evento en que hayan sido suspendidos. A partir de este momento, quien lo solicite asumirá la obligación de pagar el servicio y el inmueble quedará afecto para tales fines, en el caso que lo solicite el arrendador o propietario. La existencia de facturas no canceladas por la prestación de servicios públicos durante el término de denuncio del contrato de arrendamiento, no podrán, en ningún caso, ser motivo para que la empresa se niegue a la reconexión, cuando dicha reconexión sea solicitada en los términos del inciso anterior. - 6. Cuando las empresas de servicios públicos domiciliarios instalen un nuevo servicio a un inmueble, el valor del mismo será responsabilidad exclusiva de quién solicite el servicio. Para garantizar su pago, la empresa de servicios públicos podrá exigir directamente las garantías previstas en este artículo, a menos que el solicitante sea el mismo propietario o poseedor del inmueble, evento en el cual el inmueble quedará afecto al pago. En este caso, la empresa de servicios públicos determinará la cuantía y la forma de dichas garantías o depósitos de conformidad con la reglamentación expedida en los términos del parágrafo 1º de este artículo. Parágrafo 1º. Dentro de los tres (3) meses siguientes a la promulgación de la presente ley, el Gobierno Nacional reglamentará lo relacionado con los formatos para la denuncia del arriendo y su terminación, la prestación de garantías o depósitos, el procedimiento correspondiente y las sanciones por el incumplimiento de lo establecido en este artículo. Parágrafo 2º. La Superintendencia de Servicios Públicos Domiciliarios velará por el cumplimiento de lo anterior. Parágrafo 3º. Les reglas sobre los servicios públicos establecidas en este artículo entrarán en vigencia en el término de un (1) año, contado a partir de la promulgación de la presente ley, con el fin de que las empresas prestadoras de los servicios públicos domiciliarios realicen los ajustes de carácter técnico y las inversiones a que hubiere lugar. CAPITULO IV Prohibición de garantías y depósitos

## 9035 · Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana) · articulo 22

**Categoria:** Arriendo

**Pregunta:** Ya entregue el apartamento y el arrendador no me devuelve el deposito, ¿que hago?

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 22. Terminación por parte del arrendador. Son causales para que el arrendador pueda pedir unilateralmente la terminación del contrato, las siguientes: - 1. La no cancelación por parte del arrendatario de las rentas y reajustes dentro del término estipulado en el contrato. - 2. La no cancelación de los servicios públicos, que cause la desconexión o pérdida del servicio, o el pago de las expensas comunes cuando su pago estuviere a cargo del arrendatario. - 3. El subarriendo total o parcial del inmueble, la cesión del contrato o del goce del inmueble o el cambio de destinación del mismo por parte del arrendatario, sin expresa autorización del arrendador. - 4. La incursión reiterada del arrendatario en procederes que afecten la tranquilidad ciudadana de los vecinos, o la destinación del inmueble para actos delictivos o que impliquen contravención, debidamente comprobados ante la autoridad policiva. - 5. La realización de mejoras, cambios o ampliaciones del inmueble, sin expresa autorización del arrendador o la destrucción total o parcial del inmueble o área arrendada por parte del arrendatario. - 6. La violación por el arrendatario a las normas del respectivo reglamento de propiedad horizontal cuando se trate de viviendas sometidas a ese régimen. - 7. El arrendador podrá dar por terminado unilateralmente el contrato de arrendamiento durante las prórrogas, previo aviso escrito dirigido al arrendatario a través del servicio postal autorizado, con una antelación no menor de tres (3) meses y el pago de una indemnización equivalente al precio de tres (3) meses de arrendamiento. Cumplidas estas condiciones el arrendatario estará obligado a restituir el inmueble. - 8. El arrendador podrá dar por terminado unilateralmente el contrato de arrendamiento a la fecha de vencimiento del término inicial o de sus prórrogas invocando cualquiera de las siguientes causales especiales de restitución, previo aviso escrito al arrendatario a través del servicio postal autorizado con una antelación no menor a tres (3) meses a la referida fecha de vencimiento: - a) Cuando el propietario o poseedor del inmueble necesitare ocuparlo para su propia habitación, por un término no menor de un (1) año; - b) Cuando el inmueble haya de demolerse para efectuar una nueva construcción, o cuando se requiere desocuparlo con el fin de ejecutar obras independientes para su reparación; - c) Cuando haya de entregarse en cumplimiento de las obligaciones originadas en un contrato de compraventa; - d) La plena voluntad de dar por terminado el contrato, siempre y cuando, el contrato de arrendamiento cumpliere como mínimo cuatro (4) años de ejecución. El arrendador deberá indemnizar al arrendatario con una suma equivalente al precio de uno punto cinco (1.5) meses de arrendamiento. Cuando se trate de las causales previstas en los literales a), b) y c), el arrendador acompañará al aviso escrito la constancia de haber constituido una caución en dinero, bancaria u otorgada por compañía de seguros legalmente reconocida, constituida a favor del arrendatario por un valor equivalente a seis (6) meses del precio del arrendamiento vigente, para garantizar el cumplimiento de la causal invocada dentro de los seis (6) meses siguientes a la fecha de la restitución. Cuando se trate de la causal prevista en el literal d), el pago de la indemnización se realizará mediante el mismo procedimiento establecido en el artículo 23 de esta ley. De no mediar constancia por escrito del preaviso, el contrato de arrendamiento se entenderá renovado automáticamente por un término igual al inicialmente pactado.

## 9035 · Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana) · articulo 23

**Categoria:** Arriendo

**Pregunta:** Ya entregue el apartamento y el arrendador no me devuelve el deposito, ¿que hago?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 23. Requisitos para la terminación unilateral por parte del arrendador mediante preaviso con indemnización. Para que el arrendador pueda dar por terminado unilateralmente el contrato de arrendamiento en el evento previsto en el numeral 7 del artículo anterior, deberá cumplir con los siguientes requisitos: - a) Comunicar a través del servicio postal autorizado al arrendatario o a su representante legal, con la antelación allí prevista, indicando la fecha para la terminación del contrato y, manifestando que se pagará la indemnización de ley; - b) Consignar a favor del arrendatario y a órdenes de la autoridad competente, la indemnización de que trata el artículo anterior de la presente ley, dentro de los tres (3) meses anteriores a la fecha señalada para la terminación unilateral del contrato. La consignación se efectuará en las entidades autorizadas por el Gobierno Nacional para tal efecto y la autoridad competente allegará copia del título respectivo cl arrendatario o le enviará comunicación en que se haga constar tal circunstancia, inmediatamente tenga conocimiento de la misma. El valor de la indemnización se hará con base en la renta vigente a la fecha del preaviso; - c) Al momento de efectuar la consignación se dejará constancia en los respectivos títulos de las causas de la misma como también el nombre y dirección precisa del arrendatario o su representante; - d) Si el arrendatario cumple con la obligación de entregar el inmueble en la fecha señalada, recibirá el pago de la indemnización, de conformidad con la autorización que expida la autoridad competente. Parágrafo 1º. En caso de que el arrendatario no entregue el inmueble, el arrendador tendrá derecho a que se le devuelva la indemnización consignada, sin perjuicio de que pueda iniciar el correspondiente proceso de restitución del inmueble. Parágrafo 2º. Si el arrendador con la aceptación del arrendatario desiste de dar por terminado el contrato de arrendamiento, podrá solicitar a la autoridad competente, la autorización para la devolución de la suma consignada.

## 9035 · Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana) · articulo 25

**Categoria:** Arriendo

**Pregunta:** Ya entregue el apartamento y el arrendador no me devuelve el deposito, ¿que hago?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 25. Requisitos para la terminación unilateral por parte del arrendatario mediante preaviso con indemnización. Para que el arrendatario pueda dar por terminado unilateralmente el contrato de arrendamiento en el evento previsto en el numeral 4 del artículo anterior, deberá cumplir con los siguientes requisitos: - a) Comunicar a través del servicio postal autorizado al arrendador o a su representante legal, con la antelación allí prevista, indicando la fecha para la terminación del contrato y, manifestando que se pagará la indemnización de ley. - b) Consignar a favor del arrendador y a órdenes de la autoridad competente, la indemnización de que trata el artículo anterior de la presente ley, dentro de los tres (3) meses anteriores a la fecha señalada para la terminación unilateral del contrato. La consignación se efectuará en las entidades autorizadas por el Gobierno Nacional para tal efecto y la autoridad competente allegará copia del título respectivo al arrendador o le enviará comunicación en que se haga constar tal circunstancia, inmediatamente tenga conocimiento de la misma. El valor de la indemnización se hará con base en la renta vigente a la fecha del preaviso; - c) Al momento de efectuar la consignación se dejará constancia en los respectivos títulos de las causas de la misma como también el nombre y dirección precisa del arrendatario o su representante; - d) Si el arrendador cumple con la obligación de entregar el inmueble en la fecha señalada, recibirá el pago de la indemnización, de conformidad con la autorización que expida la autoridad competente. Parágrafo 1º. En caso de que el arrendador no reciba el inmueble, el arrendatario tendrá derecho a que se le devuelva la indemnización consignada, sin perjuicio de que pueda realizar la entrega provisional del inmueble de conformidad con lo previsto en el artículo anterior. Parágrafo 2º. Si el arrendatario con la aceptación del arrendador desiste de dar por terminado el contrato de arrendamiento, podrá solicitar a la autoridad competente, la autorización para la devolución de la suma consignada.

## 9038 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 43

**Categoria:** Relaciones laborales

**Pregunta:** Llevo dos años como contratista, con horario fijo y jefe directo, pero sin prestaciones, ¿puedo reclamar algo?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 43. CLAUSULAS INEFICACES. En los contratos de trabajo no producen ningún efecto las estipulaciones o condiciones que desmejoren la situación del trabajador en relación con lo que establezcan la legislación del trabajo, los respectivos fallos arbitrales, pactos, convenciones colectivas y reglamentos de trabajo y las que sean ilícitas o ilegales por cualquier aspecto; pero a pesar de la ineficacia de esas estipulaciones, todo trabajo ejecutado en virtud de ellas, que constituya por si mismo una actividad lícita, da derecho al trabajador para reclamar el pago de sus salarios y prestaciones legales por el tiempo que haya durado el servicio hasta que esa ineficacia se haya reconocido o declarado judicialmente.

## 9038 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 48

**Categoria:** Relaciones laborales

**Pregunta:** Llevo dos años como contratista, con horario fijo y jefe directo, pero sin prestaciones, ¿puedo reclamar algo?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 48. CLAUSULA DE RESERVA. En los contratos de duración indeterminada o sin fijación de término, las partes pueden reservarse la facultad de darlos por terminados en cualquier tiempo, mediante preaviso o desahucio notificado por escrito a la otra parte con un término no inferior a cuarenta y cinco (45) días, previa cancelación de todas las deudas, prestaciones e indemnizaciones a que haya lugar. El patrono puede prescindir del preaviso pagando los salarios correspondientes a cuarenta y cinco (45) días. La reserva de que se trata sólo es válida cuando se consigne por escrito en el contrato de trabajo. (Derogado por el Decreto 2351 de 1965)

## 9038 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 140

**Categoria:** Relaciones laborales

**Pregunta:** Llevo dos años como contratista, con horario fijo y jefe directo, pero sin prestaciones, ¿puedo reclamar algo?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 140. SALARIO SIN PRESTACION DEL SERVICIO. Durante la vigencia del contrato el trabajador tiene derecho a percibir el salario aun cuando no haya prestación del servicio por disposición o culpa del {empleador}.

## 9039 · Ley 1266 de 2008 (Habeas data financiero) · articulo 14

**Categoria:** Reporte en centrales de riesgo

**Pregunta:** Pague una deuda hace seis años y todavia aparezco reportado en las centrales de riesgo, ¿eso es legal?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 14.Contenido de la información. El Gobierno Nacional establecerá la forma en la cual los bancos de datos de información financiera, crediticia, comercial, deservicios y la proveniente de terceros países, deberán presentar la información de los titulares de la información. Para tal efecto, deberá señalar un formato que permita identificar, entre otros aspectos, el nombre completo del deudor, la condición en que actúa, esto es, como deudor principal, deudor solidario, avalista o fiador, el monto de la obligación o cuota vencida, el tiempo de mora y la fecha del pago, si es del caso. El Gobierno Nacional al ejercer la facultad prevista en el inciso anterior deberá tener en cuenta que en el formato de reporte deberá establecer que: - a) Se presenta reporte negativo cuando la(s) persona(s) naturales o jurídicas efectivamente se encuentran en mora en sus cuotas u obligaciones. - b) se presenta reporte positivo cuando la(s) persona(s) naturales y jurídicas están al día en sus obligaciones. El incumplimiento de la obligación aquí prevista dará lugar a la imposición de las máximas sanciones previstas en la presente ley. Parágrafo 1º. Para los efectos de la presente ley se entiende que una obligación ha sido voluntariamente pagada, cuando su pago se ha producido sin que medie sentencia judicial que así lo ordene. Parágrafo 2º. Las consecuencias previstas en el presente artículo para el pago voluntario de las obligaciones vencidas, será predicable para cualquier otro modo de extinción de las obligaciones, que no sea resultado de una sentencia judicial. Parágrafo 3º. Cuando un usuario consulte el estado de un titular en las bases de datos de información financiera, crediticia, comercial, de servicios y la proveniente de terceros países, estas tendrán que dar información exacta sobre su estado actual, es decir, dar un reporte positivo de los usuarios que en el momento de la consulta están al día en sus obligaciones y uno negativo de los que al momento de la consulta se encuentren en mora en una cuota u obligaciones. El resto de la información contenida en las bases de datos financieros, crediticios, comercial, de servidos y la proveniente de terceros países hará parte del historial crediticio de cada usuario, el cual podrá ser consultado por el usuario, siempre y cuando hubiere sido informado sobre el estado actual. Parágrafo 4º. Se prohíbe la administración de datos personales con información exclusivamente desfavorable.

## 9039 · Ley 1266 de 2008 (Habeas data financiero) · articulo 16

**Categoria:** Reporte en centrales de riesgo

**Pregunta:** Pague una deuda hace seis años y todavia aparezco reportado en las centrales de riesgo, ¿eso es legal?

**Estado:** recuperado=si · partido en 8 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 16.Peticiones, Consultas y Reclamos. - I. Trámite de consultas. Los titulares de la información o sus causahabientes podrán consultar lainformación personal del titular, que repose en cualquier banco de datos, sea este del sector público o privado. El operador deberá suministrar a estos, debidamente identificados, toda la información contenida en el registro individual o que esté vinculada con la identificación del titular. La petición, consulta de información se formulará verbalmente, por escrito, o por cualquier canal de comunicación, siempre y cuando se mantenga evidencia de la consulta por medios técnicos. La petición o consulta será atendida en un término máximo de diez (10) días hábiles contados a partir de la fecha de recibo de la misma. Cuando no fuere posible atender la petición o consulta dentro de dicho término, se informará al interesado, expresando los motivos de la demora y señalando la fecha en que se atenderá su petición, la cual en ningún caso podrá superar los cinco (5) días hábiles siguientes al vencimiento del primer término. Parágrafo. La petición o consulta se deberá atender de fondo, suministrando integralmente toda la información solicitada. - II. Trámite de reclamos. Los titulares de la información o sus causahabientes que consideren que la información contenida en su registro individual en un banco de datos debe ser objeto de corrección o actualización podrán presentar un reclamo ante el operador, el cual será tramitado bajo las siguientes reglas: - 1. La petición o reclamo se formulará mediante escrito dirigido al operador del banco de datos, con la identificación del titular, la descripción de los hechos que dan lugar al reclamo, la dirección, y si fuere el caso, acompañando los documentos de soporte que se quieran hacer valer. En caso de que el escrito resulte incompleto, se deberá oficiar al interesado para que subsane las fallas. Transcurrido un mes desde la fecha del requerimiento, sin que el solicitante presente la información requerida, se entenderá que ha desistido de la reclamación o petición. - 2. Una vez recibido la petición o reclamo completo el operador incluirá en el registro individual en un término no mayor a dos (2) días hábiles una leyenda que diga "reclamo en trámite" y la naturaleza del mismo. Dicha información deberá mantenerse hasta que el reclamo sea decidido y deberá incluirse en la información que se suministra a los usuarios. - 3. El término máximo para atender la petición o reclamo será de quince (15) días hábiles contados a partir del día siguiente a la fecha de su recibo. Cuando no fuere posible atender la petición dentro de dicho término, se informará al interesado, expresando los motivos de la demora y señalando la fecha en que se atenderá su petición, la cual en ningún caso podrá superar los ocho (8) días hábiles siguientes al vencimiento del primer término. - 4. En los casos en que exista una fuente de información independiente del operador, este último deberá dar traslado del reclamo a la fuente en un término máximo de dos (2) días hábiles, la cual deberá resolver e informar la respuesta al operador en un plazo máximo de diez (10) días hábiles. En todo caso, la respuesta deberá darse al titular por el operador en el término máximo de quince (15) días hábiles contados a partir del día siguiente a la fecha de presentación de la reclamación, prorrogables por ocho (8) días hábiles más, según lo indicado en el numeral anterior. Si el reclamo es presentado ante la fuente, esta procederá a resolver directamente el reclamo, pero deberá informar al operador sobre la recepción del reclamo dentro de los dos (2) días hábiles siguientes a su recibo, de forma que se pueda dar cumplimiento a la obligación de incluir la leyenda que diga "reclamo en trámite" y la naturaleza del mismo dentro del registro individual, lo cual deberá hacer el operador dentro de los dos (2) días hábiles siguientes a haber recibido la información de la fuente. - 5. Para dar respuesta a la petición o reclamo, el operador o la fuente, según sea el caso, deberá realizar una verificación completa de las observaciones o planteamientos del titular, asegurándose de revisar toda la información pertinente para poder dar una respuesta completa al titular. - 6. Sin perjuicio del ejercido de la acción de tutela para amparar el derecho fundamental del habeas data, en caso que el titular no se encuentre satisfecho con la respuesta a la petición, podrá recurrir al proceso judicial correspondiente dentro de los términos legales pertinentes para debatir lo relacionado con la obligación reportada como incumplida. La demanda deberá ser interpuesta contra la fuente de la información la cual, una vez notificada de la misma, procederá a informar al operador dentro de los dos (2) días hábiles siguientes, de forma que se pueda dar cumplimiento a la obligación de incluir la leyenda que diga "información en discusión judicial" y la naturaleza de la misma dentro del registro individual, lo cual deberá hacer el operador dentro de los dos (2) días hábiles siguientes a haber recibido la información de la fuente y por todo el tiempo que tome obtener un fallo en firme. Igual procedimiento deberá seguirse en caso que la fuente inicie un proceso judicial contra el titular de la información, referente a la obligación reportada como incumplida, y éste proponga excepciones de mérito. - 7. De los casos de suplantación. En el caso que el titular de la información manifieste ser víctima del delito de falsedad personal contemplado en el Código Penal, y le sea exigido el pago de obligaciones como resultado de la conducta punible de la que es víctima, deberá presentar petición de corrección ante la fuente adjuntando los soportes correspondientes. La fuente una vez reciba la solicitud, deberá dentro de los diez (10) días siguientes cotejar los documentos utilizados para adquirir la obligación que se disputa, con los documentos allegados por el titular en la petición, los cuales se tendrán como prueba sumaria para probar la falsedad, la fuente, si así lo considera, deberá denunciar el delito de estafa del que haya podido ser víctima. Con la solicitud presentada por el titular, el dato negativo, récord del (scorings-score) y cualquier otro dato que refleje el comportamiento del titular, deberán ser modificados por la fuente reflejando que la víctima de falsedad no es quien adquirió las obligaciones, y se incluirá una leyenda dentro del registro personal que diga -Víctima de Falsedad Personal-. - 8. Silencio. Las peticiones o reclamos deberán resolverse dentro de los quince (15) días hábiles siguientes a la fecha de su recibo. Prorrogables por ocho (8) días hábiles más, según lo indicado en el numeral 3, parte 11, artículo 16 de la presente ley. Si en ese lapso no se ha dado pronta resolución, se entenderá, para todos los efectos legales, que la respectiva solicitud ha sido aceptada. Si no lo hiciere, el peticionario podrá solicitar a la Superintendencia de Industria y Comercio y a la Superintendencia Financiera de Colombia, según el caso, la imposición de las sanciones a que haya lugar conforme a la presente ley, sin perjuicio de que ellas adopten las decisiones que resulten pertinentes para hacer efectivo el derecho al habeas data de los titulares. TITULO VI VIGILANCIA DE LOS DESTINATARIOS DE LA LEY

## 9039 · Ley 1266 de 2008 (Habeas data financiero) · articulo 19-A

**Categoria:** Reporte en centrales de riesgo

**Pregunta:** Pague una deuda hace seis años y todavia aparezco reportado en las centrales de riesgo, ¿eso es legal?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 19 A. Responsabilidad demostrada. Los operadores, fuentes y usuarios de información financiera, crediticia, comercial y de servicios deben ser capaces de demostrar que han implementado medidas apropiadas, efectivas y verificables para cumplir con las obligaciones establecidas en la Ley 1266 de 2008 Y sus normas reglamentarias, en una manera que sea proporcional a lo siguiente: - 1. La naturaleza jurídica del operador, fuente y usuario de información y, cuando sea del caso, su tamaño empresarial, teniendo en cuenta si se trata de una micro, pequeña, mediana o gran empresa, de acuerdo con la normativa vigente. - 2. La naturaleza de los datos personales objeto del tratamiento. - 3. El tipo de tratamiento. - 4. Los riesgos potenciales que el referido tratamiento podrían causar sobre los derechos de los titulares. Quienes efectúen el tratamiento de los datos personales deberán suministrar evidencia sobre la implementación efectiva de las medidas útiles y pertinentes para cumplir la presente ley.

## 9041 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 65

**Categoria:** Embargos

**Pregunta:** Me embargaron la cuenta de nomina y era mi salario del mes, ¿eso se puede?

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 65. INDEMNIZACION POR FALTA DE PAGO. Si a la terminación del contrato, el empleador no paga al trabajador los salarios y prestaciones debidas, salvo los casos de retención autorizados por la ley o convenidos por las partes, debe pagar al asalariado, como indemnización, una suma igual al último salario diario por cada día de retardo, hasta por veinticuatro (24) meses, o hasta cuando el pago se verifique si el período es menor. Si transcurridos veinticuatro (24) meses contados desde la fecha de terminación del contrato, el trabajador no ha iniciado su reclamación por la vía ordinaria o si presentara la demanda, no ha habido pronunciamiento judicial, el empleador deberá pagar al trabajador intereses moratorios a la tasa máxima de créditos de libre asignación certificados por la Superintendencia Bancaria, a partir de la iniciación del mes veinticinco (25) hasta cuando el pago se verifique. (Inciso declarado EXEQUIBLE, salvo el aparte tachado que se declara INEXEQUIBLE, por la Corte Constitucional mediante Sentencia C-781-03) Dichos intereses los pagará el empleador sobre las sumas adeudadas al trabajador por concepto de salarios y prestaciones en dinero. (Aparte subrayado declarado EXEQUIBLE, por los cargos estudiados, por la Corte Constitucional mediante Sentencia C-892-09) Si no hay acuerdo respecto del monto de la deuda, o si el trabajador se niega a recibir, el empleador cumple con sus obligaciones consignando ante el juez de trabajo y, en su defecto, ante la primera autoridad política del lugar, la suma que confiese deber, mientras la justicia de trabajo decide la controversia. PARÁGRAFO 1. Para proceder a la terminación del contrato de trabajo establecido en el artículo 64 del Código Sustantivo del Trabajo, el empleador le deberá informar por escrito al trabajador, a la última dirección registrada, dentro de los sesenta (60) días siguientes a la terminación del contrato, el estado de pago de las cotizaciones de Seguridad Social y parafiscalidad sobre los salarios de los últimos tres meses anteriores a la terminación del contrato, adjuntando los comprobantes de pago que los certifiquen. Si el empleador no demuestra el pago de dichas cotizaciones, la terminación del contrato no producirá efecto. Sin embargo, el empleador podrá pagar las cotizaciones durante los sesenta (60) días siguientes, con los intereses de mora. PARÁGRAFO 2. Lo dispuesto en el inciso 1o. de este artículo solo se aplicará a los trabajadores que devenguen más de un (1) salario mínimo mensual vigente. Para los demás seguirá en plena vigencia lo dispuesto en el artículo 65 del Código Sustantivo de Trabajo vigente. (Modificado por el artículo 29 de la Ley 789 de 2002)

## 9041 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 290

**Categoria:** Embargos

**Pregunta:** Me embargaron la cuenta de nomina y era mi salario del mes, ¿eso se puede?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 290. NOMINA. Para los efectos del artículo anterior, se toma en cuenta el promedio mensual de la nómina de salarios en el año anterior al fallecimiento del trabajador, y en caso de lapso menor de actividades de la empresa, el promedio mensual de salarios en ese tiempo. (Seguro colectivo derogado como consecuencia de la regulación integral de la seguridad social efectuada por la Ley 100 de 1993. Ver Sentencia de la Corte Constitucional C-823-06)

## 9041 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 393

**Categoria:** Embargos

**Pregunta:** Me embargaron la cuenta de nomina y era mi salario del mes, ¿eso se puede?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 393. LIBROS. Todo sindicato debe abrir, tan pronto como se haya suscrito el acta de fundación y se haya suscrito el acta de fundación y se haya posesionado la Junta Directiva provisional, por lo menos los siguientes libros: de afiliación; de actas de la asamblea general; de actas de la junta directiva; de inventarios y balances; y de ingresos y de egresos. Estos libros serán previamente registrados por el Inspector del Trabajo respectivo y foliados y rubricados por el mismo en cada una de sus páginas. En todos los libros que deben llevar los sindicatos se prohíbe arrancar, sustituir o adicionar hojas, hacer enmendaduras, entre renglonaduras, raspaduras o tachaduras; cualquier omisión o error debe enmendarse mediante anotación posterior. Toda infracción a estas normas acarreará al responsable una multa por un monto equivalente al de un (1) día hasta un (1) mes de salario mínimo mensual más alto, que impondrá el Inspector de Trabajo en favor del sindicato y además, la mitad de la misma sanción, también en favor del sindicato, a cada uno de los directores y funcionarios sindicales que habiendo conocido la infracción no la hayan castigado sindicalmente o no la hayan denunciado al Inspector del Trabajo, sin perjuicio de las sanciones penales a que haya lugar. (Modificado por el Art. 18 de la Ley 11 de 1984)

## 9041 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 433

**Categoria:** Embargos

**Pregunta:** Me embargaron la cuenta de nomina y era mi salario del mes, ¿eso se puede?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 433. INICIACION DE CONVERSACIONES. El {empleador} o la representante, están en la obligación de recibir a los delegados de los trabajadores dentro de las veinticuatro horas siguientes a la presentación oportuna del pliego de peticiones para iniciar conversaciones. Si la persona a quién se presentare el pliego considerare que no está autorizada para resolver sobre él debe hacerse autorizar o dar traslado al {empleador} dentro de las veinticuatro horas siguientes a la presentación del pliego, avisándolo así a los trabajadores. En todo caso, la iniciación de las conversaciones en la etapa de arreglo directo no puede diferirse por más de cinco (5) días hábiles a partir de la presentación del pliego. El {empleador} que se niegue o eluda iniciar las conversaciones de arreglo directo dentro del término señalado será sancionado por las autoridades del trabajo con multas equivalentes al monto de cinco (5) a diez (10) veces el salario mínimo mensual más alto por cada día de mora, a favor del Servicio Nacional de Aprendizaje SENA. Para interponer los recursos legales contra las resoluciones de multa, el interesado deberá consignar previamente su valor a órdenes de dicho establecimiento. (Numeral 2 modificado por el Art. 21 de la Ley 11 de 1984) (Aparte subrayado declarado EXEQUIBLE por la Corte Constitucional mediante Sentencia C-741-13 ) (Modificado por el Art. 27 del Decreto 2351 de 1965)

## 9043 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 18

**Categoria:** Garantias de consumo

**Pregunta:** Compre unos zapatos por internet y no me gustaron, ¿puedo devolverlos y que me devuelvan la plata?

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 18. Prestación de servicios que suponen la entrega de un bien. Cuando se exija la entrega de un bien respecto del cual se desarrollará una prestación de servicios, estará sometido a las siguientes reglas: - 1. Quien preste el servicio debe expedir un recibo del bien en el cual se mencione la fecha de la recepción, y el nombre del propietario o de quien hace entrega, su dirección y teléfono, la identificación del bien, la clase de servicio, las sumas que se abonan como parte del precio, el término de la garantía que otorga, y si es posible determinarlos en ese momento, el valor del servicio y la fecha de devolución. Cuando en el momento de la recepción no sea posible determinar el valor del servicio y el plazo de devolución del bien, el prestador del servicio deberá informarlo al consumidor en el término que acuerden para ello, para que el consumidor acepte o rechace de forma expresa la prestación del servicio. De dicha aceptación o rechazo se dejará constancia, de tal forma que pueda ser verificada por la autoridad competente; si no se hubiere hecho salvedad alguna al momento de entrega del bien, se entenderá que el consumidor lo entregó en buen estado. - 2. Quien preste el servicio asume la custodia y conservación adecuada del bien y, por lo tanto, de la integridad de los elementos que lo componen, así como la de sus equipos anexos o complementarios, si los tuviere. - 3. En la prestación del servicio de parqueadero la persona natural o jurídica que preste el servicio deberá expedir un recibo del bien en el cual se mencione la fecha y hora de la recepción, la identificación del bien, el estado en que se encuentra y el valor del servicio en la modalidad en que se preste. Para la identificación y el estado en que se recibe el bien al momento del ingreso, podrá utilizarse medios tecnológicos que garanticen el cumplimiento de esta obligación. Cuando se trate de zonas de parqueo gratuito, el prestador del servicio responderá por los daños causados cuando medie dolo o culpa grave. Parágrafo. Pasado un (1) mes a partir de la fecha prevista para la devolución o a la fecha en que el consumidor debía aceptar o rechazar expresamente el servicio, de conformidad con lo previsto en el numeral 1 anterior sin que el consumidor acuda a retirar el bien, el prestador del servicio lo requerirá para que lo retire dentro de los dos (2) meses siguientes a la remisión de la comunicación. Si el consumidor no lo retira se entenderá por ley que abandona el bien y el prestador del servicio deberá disponer del mismo conforme con la reglamentación que expida el Gobierno Nacional para el efecto. Sin perjuicio del derecho de retención, el prestador del servicio no podrá lucrarse económicamente del bien, explotarlo, transferir el dominio o conservarlo para sí mismo. No obstante lo anterior, el consumidor deberá asumir los costos asociados al abandono del bien, tales como costos de almacenamiento bodegaje y mantenimiento. TÍTULO IV RESPONSABILIDAD POR DAÑOS POR PRODUCTO DEFECTUOSO CAPÍTULO ÚNICO De la responsabilidad por daños por producto defectuoso

## 9043 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 50

**Categoria:** Garantias de consumo

**Pregunta:** Compre unos zapatos por internet y no me gustaron, ¿puedo devolverlos y que me devuelvan la plata?

**Estado:** recuperado=si · partido en 8 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 50. Sin perjuicio de las demás obligaciones establecidas en la presente ley, los proveedores y expendedores ubicados en el territorio nacional que ofrezcan productos utilizando medios electrónicos, deberán: - a) Informar en todo momento de forma cierta, fidedigna, suficiente, clara, accesible y actualizada su identidad especificando su nombre o razón social, Número de Identificación Tributaria (NIT), dirección de notificación judicial, teléfono, correo electrónico y demás datos de contacto. - b) Suministrar en todo momento información cierta, fidedigna, su­ficiente, clara y actualizada respecto de los productos y/o servi­cios que ofrezcan conforme a su naturaleza y destino. En espe­cial, deberán indicar sus características y propiedades tales como el tamaño, el peso, la medida, el material del que está fabricado, su naturaleza, el origen, el modo de fabricación, los componen­tes, los usos, la forma de empleo restricciones de uso y cuidado relevantes, las propiedades, la calidad, la idoneidad, la cantidad o cualquier otro factor pertinente, independientemente que se acompañen de imágenes, de tal forma que el consumidor pueda hacerse una representación lo más aproximada a la realidad del producto. Tratándose de servicios, la descripción adecuada de las prestaciones incluidas. Cuando la información mínima de los productos esté regulada en una norma de carácter especial, deberá garantizarse que dicha información se suministre en el medio electrónico respectivo, a excepción de productos alimenticios, los cuales no estarán obligados a informar en el medio electrónico los siguientes datos específicos de los productos ofrecidos: Lote de fabricación y fecha de vencimiento. La vigilancia de la citada obligación corresponderá a las entidades encargadas de ejercer control sobre la norma especial. Sin embargo, para el caso de los alimentos y, en general, para productos perecederos, los productos deben entregarse antes de su fecha de vencimiento, con el fin de garantizar la calidad, idoneidad y seguridad de estos. También se deberá indicar el plazo de validez de la oferta y la disponibilidad del producto. En los contratos de tracto sucesivo, se deberá informar su duración mínima. Cuando la publicidad del bien incluya imágenes o gráficos del mismo, se deberá indicar en qué escala está elaborada dicha representación. - c) Informar, en el medio de comercio electrónico utilizado, los medios de que disponen para realizar los pagos, el tiempo de entrega del bien o la prestación del servicio, el derecho de retracto que le asiste al consumidor y el procedimiento para ejercerlo, y cualquier otra información relevante para que el consumidor pueda adoptar una decisión de compra libremente y sin ser inducido en error. Igualmente deberá informar el precio total del producto incluyendo todos los impuestos, costos y gastos que deba pagar el consumidor para adquirirlo. En caso de ser procedente, se debe informar adecuadamente y por separado los gastos de envío. - d) Publicar en el mismo medio y en todo momento, las condiciones generales de sus contratos, que sean fácilmente accesibles y disponibles para su consulta, impresión y descarga, antes y después de realizada la transacción, así no se haya expresado la intención de contratar. Previamente a la finalización o terminación de cualquier transacción de comercio electrónico, el proveedor o expendedor deberá presentar al consumidor un resumen del pedido de todos los bienes que pretende adquirir con su descripción completa, el precio individual de cada uno de ellos, el precio total de los bienes o servicios y, de ser aplicable, los costos y gastos adicionales que deba pagar por envío o por cualquier otro concepto y la sumatoria total que deba cancelar. Este resumen tiene como fin que el consumidor pueda verificar que la operación refleje su intención de adquisición de los productos o servicios ofrecidos y las demás condiciones, y de ser su deseo, hacer las correcciones que considere necesarias o la cancelación de la transacción. Este resumen deberá estar disponible para su impresión y/o descarga. La aceptación de la transacción por parte del consumidor deberá ser expresa, inequívoca y verificable por la autoridad competente. El consumidor debe tener el derecho de cancelar la transacción hasta antes de concluirla. Concluida la transacción, el proveedor y expendedor deberá remitir, a más tardar el día calendario siguiente de efectuado el pedido, un acuse de recibo del mismo, con información precisa del tiempo de entrega, precio exacto, incluyendo los impuestos, gastos de envío y la forma en que se realizó el pago. Queda prohibida cualquier disposición contractual en la que se presuma la voluntad del consumidor o que su silencio se considere como consentimiento, cuando de esta se deriven erogaciones u obligaciones a su cargo. - e) Mantener en mecanismos de soporte duradero la prueba de la relación comercial, en especial de la identidad plena del consumidor, su voluntad expresa de contratar, de la forma en que se realizó el pago y la entrega real y efectiva de los bienes o servicios adquiridos, de tal forma que garantice la integridad y autenticidad de la información y que sea verificable por la autoridad competente, por el mismo tiempo que se deben guardar los documentos de comercio. - f) Adoptar mecanismos de seguridad apropiados y confiables que garanticen la protección de la información personal del consumidor y de la transacción misma. El proveedor será responsable por las fallas en la seguridad de las transacciones realizadas por los medios por él dispuestos, sean propios o ajenos. Cuando el proveedor o expendedor dé a conocer su membrecía o afiliación en algún esquema relevante de autorregulación, asociación empresarial, organización para resolución de disputas u otro organismo de certificación, deberá proporcionar a los consumidores un método sencillo para verificar dicha información, así como detalles apropiados para contactar con dichos organismos, y en su caso, tener acceso a los códigos y prácticas relevantes aplicados por el organismo de certificación. - g) Disponer en el mismo medio en que realiza comercio electró­nico de canales de fácil acceso y de atención que garanticen la orientación y asistencia a los consumidores y la trazabilidad de las reclamaciones por ellos presentadas, con el fin de que estos puedan resolver dudas y radicar sus peticiones, quejas o recla­mos. De tal forma que les quede, constancia de la atención me­diante la generación de un número de registro o radicado, junto con la fecha y hora de radicación de sus peticiones, quejas o reclamos, incluyendo un mecanismo para su posterior segui­miento. - h) El proveedor deberá entregar el pedido dentro del plazo acep­tado por el consumidor, el cual deberá ser informado de ma­nera previa a la finalización o terminación de cualquier tran­sacción de comercio electrónico. Si no se estableciere dicho término, se entenderá que el proveedor se obliga a entregarlo a más tardar en el plazo de treinta (30) días calendario a partir del día siguiente en que el consumidor haya comunicado su pedido. En caso de no encontrarse disponible el producto objeto del pedido, el consumidor deberá ser informado de esta falta de disponibilidad de forma inmediata por parte del proveedor y del portal de contacto. En dicho caso, el proveedor podrá establecer una segunda fecha de entrega solicitud del consumidor. Si la entrega del pedido supera el tiempo pactado por las partes o los treinta (30) días calendario, o que no haya disponible el producto adquirido, el consumidor podrá resolver o terminar, según el caso, el contrato unilateralmente y obtener la devolución en dinero de todas las sumas pagarlas sin que haya lugar a retención o descuento alguno. La devolución deberá hacerse efectiva en un plazo máximo de quince (15) días calendario. Parágrafo. El proveedor deberá establecer en el medio de comercio electrónico utilizado, un enlace visible, fácilmente identificable, que le permita al consumidor ingresar a la página de la autoridad de protección al consumidor de Colombia.

## 9043 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 51

**Categoria:** Garantias de consumo

**Pregunta:** Compre unos zapatos por internet y no me gustaron, ¿puedo devolverlos y que me devuelvan la plata?

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 51. Reversión del pago. Cuando las ventas de bienes se realicen mediante mecanismos de comercio electrónico, tales como Internet, PSE y/o call center y/o cualquier otro mecanismo de televenta o tienda virtual, y se haya utilizado para realizar el pago una tarjeta de crédito, débito o cualquier otro instrumento de pago electrónico, los participantes del proceso de pago deberán reversar los pagos que solicite el consumidor cuando sea objeto de fraude, o corresponda a una operación no solicitada, o el producto adquirido no sea recibido, o el producto entregado no corresponda a lo solicitado o sea defectuoso. Para que proceda la reversión del pago, dentro los cinco (5) días hábiles siguientes a la fecha en que el consumidor tuvo noticia de la operación fraudulenta o no solicitada o que debió haber recibido el producto o lo recibió defectuoso o sin que correspondiera a lo solicitado, el consumidor deberá presentar queja ante el proveedor y devolver el producto, cuando sea procedente, y notificar de la reclamación al emisor del instrumento de pago electrónico utilizado para realizar la compra, el cual, en conjunto con los demás participantes del proceso de pago, procederán a reversar la transacción al comprador. En el evento que existiere controversia entre proveedor y consumidor derivada de una queja y esta fuere resuelta por autoridad judicial o administrativa a favor del proveedor, el emisor del instrumento de pago, en conjunto con los demás participantes del proceso de pago, una vez haya sido notificado de la decisión, y siempre que ello fuere posible, cargará definitivamente la transacción reclamada al depósito bancario o instrumento de pago correspondiente o la debitará de la cuenta corriente o de ahorros del consumidor, y el dinero será puesto a disposición del proveedor. De no existir fondos suficientes o no resultar posible realizar lo anterior por cualquier otro motivo, los participantes del proceso de pago informarán de ello al proveedor, para que este inicie las acciones que considere pertinentes contra el consumidor. Si la controversia se resuelve a favor del consumidor, la reversión se entenderá como definitiva. Lo anterior, sin perjuicio del deber del proveedor de cumplir con sus obligaciones legales y contractuales frente al consumidor y de las sanciones administrativas a que haya lugar. En caso de que la autoridad judicial o administrativa determine que hubo mala fe por parte del consumidor, la Superintendencia podrá imponerle sanciones de hasta cincuenta (50) salarios mínimos legales mensuales vigentes. El Gobierno Nacional reglamentará el presente artículo. Parágrafo 1°. Para los efectos del presente artículo, se entienden por participantes en el proceso de pago, los emisores de los instrumentos de pago, las entidades administradoras de los Sistemas de Pago de Bajo Valor, los bancos que manejan las cuentas y/o depósitos bancarios del consumidor y/o del proveedor, entre otros. Parágrafo 2°. El consumidor tendrá derecho a reversar los pagos correspondientes a cualquier servicio u obligación de cumplimiento periódico, por cualquier motivo y aún sin que medie justificación alguna, siempre que el pago se haya realizado a través de una operación de débito automático autorizada previamente por dicho consumidor, en los términos que señale el gobierno Nacional para el efecto.

## 9043 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 58

**Categoria:** Garantias de consumo

**Pregunta:** Compre unos zapatos por internet y no me gustaron, ¿puedo devolverlos y que me devuelvan la plata?

**Estado:** recuperado=si · partido en 9 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 58. Procedimiento. Los procesos que versen sobre violación a los derechos de los consumidores establecidos en normas generales o especiales en todos los sectores de la economía, a excepción de la responsabilidad por producto defectuoso y de las acciones de grupo o las populares, se tramitarán por el procedimiento verbal sumario, con observancia de las siguientes reglas especiales: - 1. La Superintendencia de Industria y Comercio o el Juez competente conocerán a prevención. La Superintendencia de Industria y Comercio tiene competencia en todo el territorio nacional y reemplaza al juez de primera o única instancia competente por razón de la cuantía y el territorio. - 2. Será también competente el juez del lugar donde se haya comercializado o adquirido el producto, o realizado la relación de consumo. Cuando la Superintendencia de Industria y Comercio deba conocer de un asunto en un lugar donde no tenga oficina, podrá delegar a un funcionario de la entidad, utilizar medios técnicos para la realización de las diligencias y audiencias o comisionar a un juez. - 3. Las demandas para efectividad de garantía, deberán presentarse a más tardar dentro del año siguiente a la expiración de la garantía y las controversias netamente contractuales, a más tardar dentro del año siguiente a la terminación del contrato, En los demás casos, deberán presentarse a más tardar dentro del año siguiente a que el consumidor tenga conocimiento de los hechos que motivaron la reclamación. En cualquier caso deberá aportarse prueba de que la reclamación fue efectuada durante la vigencia de la garantía. - 4. No se requerirá actuar por intermedio de abogado. Las ligas y asociaciones de consumidores constituidas de acuerdo con la ley podrán representar a los consumidores. Por razones de economía procesal, la Superintendencia de Industria y Comercio podrá decidir varios procesos en una sola audiencia. - 5. A la demanda deberá acompañarse la reclamación directa hecha por el demandante al productor y/o proveedor, reclamación que podrá ser presentada por escrito, telefónica o verbalmente, con observancia de las siguientes reglas: - a) Cuando la pretensión principal sea que se cumpla con la garantía, se repare el bien o servicio, se cambie por uno nuevo de similares características, se devuelva el dinero pagado o en los casos de prestación de servicios que suponen la entrega de un bien, cuando el bien sufra deterioro o pérdida, la reposición del mismo por uno de similares características o su equivalente en dinero, se deberá identificar el producto, la fecha de adquisición o prestación del servicio y las pruebas del defecto. Cuando la reclamación sea por protección contractual o por información o publicidad engañosa, deberá anexarse la prueba documental e indicarse las razones de inconformidad. - b) La reclamación se entenderá presentada por escrito cuando se utilicen medios electrónicos. Quien disponga de la vía telefónica para recibir reclamaciones, deberá garantizar que queden grabadas. En caso de que la reclamación sea verbal, el productor o proveedor deberá expedir constancia escrita del recibo de la misma, con la fecha de presentación y el objeto de reclamo. El consumidor también podrá remitir la reclamación mediante correo con constancia de envío a la dirección del establecimiento de comercio donde adquirió el producto y/o a la dirección del productor del bien o servicio. - c) El productor o el proveedor deberá dar respuesta dentro de los quince (15) días hábiles siguientes a la recepción de la reclamación. La respuesta deberá contener todas las pruebas en que se basa. Cuando el proveedor y/o productor no hubiera expedido la constancia, o se haya negado a recibir la reclamación, el consumidor así lo declarará bajo juramento, con copia del envío por correo, - d) Las partes podrán practicar pruebas periciales anticipadas ante los peritos debidamente inscritos en el listado que para estos efectos organizará y reglamentará la Superintendencia de Industria y Comercio, los que deberán ser de las más altas calidades morales y profesionales. El dictamen, junto con la constancia de pago de los gastos y honorarios, se aportarán en la demanda o en la contestación. En estos casos, la Superintendencia de Industria y Comercio debe valorar el dictamen de acuerdo a las normas de la sana crítica, en conjunto con las demás pruebas que obren en el proceso y solo en caso de que carezca de firmeza y precisión podrá decretar uno nuevo. - e) Derogado. - f) Si la respuesta es negativa, o si la atención, la reparación, o la prestación realizada a título de efectividad de la garantía no es satisfactoria, el consumidor podrá acudir ante el juez competente o la Superintendencia. Si dentro del término señalado por la ley el productor o proveedor no da respuesta, se tendrá como indicio grave en su contra. La negativa comprobada del productor o proveedor a recibir una reclamación dará lugar a la imposición de las sanciones previstas en la presente ley y será apreciada como indicio grave en su contra. - g) Se dará por cumplido el requisito de procedibilidad de reclamación directa en todos los casos en que se presente un acta de audiencia de conciliación emitida por cualquier centro de conciliación legalmente establecido. - 6. La demanda deberá identificar plenamente al productor o proveedor. En caso de que el consumidor no cuente con dicha información, deberá indicar el sitio donde se adquirió el producto o se suministró el servicio, o el medio por el cual se adquirió y cualquier otra información adicional que permita a la Superintendencia de Industria y Comercio individualizar y vincular al proceso al productor o proveedor, tales como direcciones, teléfonos, correos electrónicos, entre otros. La Superintendencia de Industria y Comercio adelantará las gestiones pertinentes para individualizar y vincular al proveedor o productor. Si transcurridos dos meses desde la interposición de la demanda, y habiéndose realizado las gestiones pertinentes, no es posible su individualización y vinculación, se archivará el proceso, sin perjuicio de que el demandante pueda presentar, antes de que opere la prescripción de la acción, una nueva demanda con los requisitos establecidos en la presente ley y además deberá contener información nueva sobre la identidad del productor y/o expendedor. - 7. Las comunicaciones y notificaciones que deba hacer la Superintendencia de Industria y Comercio podrán realizarse por un medio eficaz que deje constancia del acto de notificación, ya sea de manera verbal, telefónica o por escrito, dirigidas al lugar donde se expendió el producto o se celebró el contrato, o a la que aparezca en las etiquetas del producto o en las páginas web del expendedor y el productor, o a las que obren en los certificados de existencia y representación legal, o a las direcciones electrónicas reportadas a la Superintendencia de Industria y Comercio, o a las que aparezcan en el registro mercantil o a las anunciadas en la publicidad del productor o proveedor. - 8. Derogado. - 9. Al adoptar la decisión definitiva, el Juez de conocimiento o la Superintendencia de Industria y Comercio resolverá sobre las pretensiones de la forma que considere más justa para las partes según lo probado en el proceso, con plenas facultades para fallar infra, extra y ultrapetita, y emitirá las órdenes a que haya lugar con indicación de la forma y términos en que se deberán cumplir. - 10. Si la decisión final es favorable al consumidor, la Superintendencia de Industria y Comercio y los Jueces podrán imponer al productor o proveedor que no haya cumplido con sus obligaciones contractuales o legales, además de la condena que corresponda, una multa de hasta ciento cincuenta (150) salarios mínimos legajes mensuales vigentes a favor de la Superintendencia de Industria y Comercio, que se fijará teniendo en cuenta circunstancias de agravación debidamente probadas, tales como la gravedad del hecho, la reiteración en el incumplimiento de garantías o del contrato, la renuencia a cumplir con sus obligaciones legales, inclusive la de expedir la factura y las demás circunstancias. No procederá esta multa si el proceso termina por conciliación, transacción, desistimiento o cuando el demandado se allana a los hechos en la contestación de la demanda. La misma multa podrá imponerse al consumidor que actúe en forma temeraria. - 11. En caso de incumplimiento de la orden impartida en la sentencia o de una conciliación o transacción realizadas en legal forma, la Superintendencia Industria y Comercio podrá: - a) Sancionar con una multa sucesiva a favor de la Superintendencia de Industria y Comercio, equivalente a la séptima parte de un salario mínimo legal mensual vigente por cada día de retardo en el incumplimiento. - b) Decretar el cierre temporal del establecimiento comercial, si persiste el incumplimiento y mientras se acredite el cumplimiento de la orden. Cuando lo considere necesario la Superintendencia de Industria y Comercio podrá solicitar la colaboración de la fuerza pública para hacer efectiva la medida adoptada. La misma sanción podrá imponer la Superintendencia de Industria y Comercio, la Superintendencia Financiera o el juez competente, cuando se incumpla con una conciliación o transacción que haya sido realizada en legal forma. Parágrafo. Para efectos de lo previsto en el presente artículo, la Superintendencia Financiera de Colombia tendrá competencia exclusiva respecto de los asuntos a los que se refiere el artículo 57 de esta ley. Parágrafo 2º. En el sector turismo, las acciones de protección al consumidor permitirán el llamamiento en garantía entre agencias de viajes y aerolíneas, conforme al artículo 64 de la Ley 1564 de 2012 o normas que la modifiquen, sustituyan y adicionen. Este procedimiento se llevará a cabo a petición de parte, facilitando que los consumidores puedan reclamar indemnizaciones o reembolsos por perjuicios sufridos durante su experiencia de viaje. La demanda por medio de la cual se llame en garantía deberá cumplir con los mismos requisitos exigidos en el presente artículo. Si se halla procedente el llamamiento, se ordenará notificar personalmente al convocado y correrle traslado del escrito por el término de la demanda inicial. Si la notificación no se logra dentro de los dos meses siguientes, el llamamiento será ineficaz. El llamado en garantía podrá contestar en la demanda y el llamamiento en un solo escrito, solicitando las pruebas que pretenda hacer valer. En la sentencia se resolverá la relación sustancial aducida y emitirá pronunciamiento sobre las indemnizaciones o restituciones a cargo del llamado en garantía. No será necesario notificar personalmente el auto que admite el llamamiento cuando el llamado actúe en el proceso como parte o como representante de alguna de las partes. CAPÍTULO IV Otras actuaciones administrativas Denominación Corregida por: Art. 3 Decreto 2184 de 2012

## 9046 · Ley 1437 de 2011 (CPACA) · articulo 16

**Categoria:** Derecho de peticion

**Pregunta:** Le mande un derecho de peticion a una empresa de telefonia y no me responden, ¿que hago?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 16.Contenido de las peticiones. Toda petición deberá contener, por lo menos: - l. La designación de la autoridad a la que se dirige. - 2. Los nombres y apellidos completos del solicitante y de su representante y o apoderado, si es el caso, con indicación de su documento de identidad y de la dirección donde recibirá correspondencia. El peticionario podrá agregar el número de fax o la dirección electrónica. Si el peticionario es una persona privada que deba estar inscrita en el registro mercantil, estará obligada a indicar su dirección electrónica. - 3. El objeto de la petición. - 4. Las razones en las que fundamenta su petición. - 5. La relación de los documentos que desee presentar para iniciar el trámite. - 6. La firma del peticionario cuando fuere el caso. Parágrafo 1°. La autoridad tiene la obligación de examinar integralmente la petición, y en ningún caso la estimará incompleta por falta de requisitos o documentos que no se encuentren dentro del marco jurídico vigente, que no sean necesarios para resolverla o que se encuentren dentro de sus archivos. Parágrafo 2°. En ningún caso podrá ser rechazada la petición por motivos de fundamentación inadecuada o incompleta.

## 9046 · Ley 1437 de 2011 (CPACA) · articulo 21

**Categoria:** Derecho de peticion

**Pregunta:** Le mande un derecho de peticion a una empresa de telefonia y no me responden, ¿que hago?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 21. Funcionario sin competencia. Si la autoridad a quien se dirige la petición no es la competente, se informará de inmediato al interesado si este actúa verbalmente, o dentro de los cinco (5) días siguientes al de la recepción, si obró por escrito. Dentro del término señalado remitirá la petición al competente y enviará copia del oficio remisorio al peticionario o en caso de no existir funcionario competente así se lo comunicará. Los términos para decidir o responder se contarán a partir del día siguiente a la recepción de la Petición por la autoridad competente.

## 9046 · Ley 1437 de 2011 (CPACA) · articulo 225

**Categoria:** Derecho de peticion

**Pregunta:** Le mande un derecho de peticion a una empresa de telefonia y no me responden, ¿que hago?

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 225.Llamamiento en garantía. Quien afirme tener derecho legal o contractual de exigir a un tercero la reparación integral del perjuicio que llegare a sufrir, o el reembolso total o parcial del pago que tuviere que hacer como resultado de la sentencia, podrá pedir la citación de aquel, para que en el mismo proceso se resuelva sobre tal relación. El llamado, dentro del término de que disponga para responder el llamamiento que será de quince (15) días, podrá, a su vez, pedir la citación de un tercero en la misma forma que el demandante o el demandado. El escrito de llamamiento deberá contener los siguientes requisitos: - 1. El nombre del llamado y el de su representante si aquel no puede comparecer por sí al proceso. - 2. La indicación del domicilio del llamado, o en su defecto, de su residencia, y la de su habitación u oficina y los de su representante, según fuere el caso, o la manifestación de que se ignoran, lo último bajo juramento, que se entiende prestado por la sola presentación del escrito. - 3. Los hechos en que se basa el llamamiento y los fundamentos de derecho que se invoquen. - 4. La dirección de la oficina o habitación donde quien hace el llamamiento y su apoderado recibirán notificaciones personales. El llamamiento en garantía con fines de repetición se regirá por las normas de la Ley 678 de 2001 o por aquellas que la reformen o adicionen.

## 9050 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 714

**Categoria:** Derecho comercial

**Pregunta:** Recibi un cheque como pago y el banco lo devolvio por falta de fondos, ¿que puedo hacer?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 714. El librador debe tener provisión de fondos disponibles en el banco librado y haber recibido de éste autorización para librar cheques a su cargo. La autorización se entenderá concedida por el hecho de que el banco entregue los formularios de cheques o chequeras al librador.

## 9050 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 720

**Categoria:** Derecho comercial

**Pregunta:** Recibi un cheque como pago y el banco lo devolvio por falta de fondos, ¿que puedo hacer?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 720. El banco estará obligado en sus relaciones con el librador a cubrir el cheque hasta el importe del saldo disponible, salvo disposición legal que lo libere de tal obligación. Si los fondos disponibles no fueren suficientes para cubrir el importe total del cheque, el librado deberá ofrecer al tenedor el pago parcial, hasta el saldo disponible.

## 9050 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 721

**Categoria:** Derecho comercial

**Pregunta:** Recibi un cheque como pago y el banco lo devolvio por falta de fondos, ¿que puedo hacer?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 721. Aún cuando el cheque no hubiere sido presentado en tiempo, el librado deberá pagarlo si tiene fondos suficientes del librador o hacer la oferta de pago parcial, siempre que se presente dentro de los seis meses que sigan a su fecha.

## 9050 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 724

**Categoria:** Derecho comercial

**Pregunta:** Recibi un cheque como pago y el banco lo devolvio por falta de fondos, ¿que puedo hacer?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 724. El librador podrá revocar el cheque, bajo su responsabilidad, aunque no hayan transcurrido los plazos para su presentación, sin perjuicio de lo dispuesto en el artículo 742. Notificada la revocación al banco, éste no podrá pagar el cheque.

## 9050 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 728

**Categoria:** Derecho comercial

**Pregunta:** Recibi un cheque como pago y el banco lo devolvio por falta de fondos, ¿que puedo hacer?

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 728. Todo banco estará obligado a devolver al librador, junto con el extracto de su cuenta, los cheques originales que haya pagado.

## 9056 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 468

**Categoria:** Embargos

**Pregunta:** Me llego un embargo del juzgado pero el nombre y la cedula no son los mios, solo se parecen.

**Estado:** recuperado=si · partido en 9 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 468. Disposiciones especiales para la efectividad de la garantía real. Cuando el acreedor persiga el pago de una obligación en dinero, exclusivamente con el producto de los bienes gravados con hipoteca o prenda, se observarán las siguientes reglas: - 1. Requisitos de la demanda. La demanda, además de cumplir los requisitos de toda demanda ejecutiva, deberá indicar los bienes objeto de gravamen. A la demanda se acompañará título que preste mérito ejecutivo, así como el de la hipoteca o prenda, y si se trata de aquella un certificado del registrador respecto de la propiedad del demandado sobre el bien inmueble perseguido y los gravámenes que lo afecten, en un período de diez (10) años si fuere posible. Cuando se trate de prenda sin tenencia, el certificado deberá versar sobre la vigencia del gravamen. El certificado que debe anexarse a la demanda debe haber sido expedido con una antelación no superior a un (1) mes. La demanda deberá dirigirse contra el actual propietario del inmueble, la nave o la aeronave materia de la hipoteca o de la prenda. Si el pago de la obligación a cargo del deudor se hubiere pactado en diversos instalamentos, en la demanda podrá pedirse el valor de todos ellos, en cuyo caso se harán exigibles los no vencidos. Si del certificado del registrador aparece que sobre los bienes gravados con prenda o hipoteca existe algún embargo ordenado en proceso ejecutivo, en la demanda deberá informarse, bajo juramento, si en aquel ha sido citado el acreedor, y de haberlo sido, la fecha de la notificación. - 2. Embargo y secuestro. Simultáneamente con el mandamiento ejecutivo y sin necesidad de caución, el juez decretará el embargo y secuestro del bien hipotecado o dado en prenda, que se persiga en la demanda. El registrador deberá inscribir el embargo, aunque el demandado haya dejado de ser propietario del bien. Acreditado el embargo, si el bien ya no pertenece al demandado, el juez de oficio tendrá como sustituto al actual propietario a quien se le notificará el mandamiento de pago. En este proceso no habrá lugar a reducción de embargos ni al beneficio de competencia. - 3. Orden de seguir adelante la ejecución. Si no se proponen excepciones y se hubiere practicado el embargo de los bienes gravados con hipoteca o prenda, o el ejecutado hubiere prestado caución para evitarlo o levantarlo, se ordenará seguir adelante la ejecución para que con el producto de ellos se pague al demandante el crédito y las costas. El secuestro de los bienes inmuebles no será necesario para ordenar seguir adelante la ejecución, pero sí para practicar el avalúo y señalar la fecha del remate. Cuando no se pueda efectuar el secuestro por oposición de poseedor, o se levante por el mismo motivo, se aplicará lo dispuesto en el numeral 3 del artículo 596, sin que sea necesario reformar la demanda. - 4. Intervención de terceros acreedores. En el mandamiento ejecutivo se ordenará la citación de los terceros acreedores que conforme a los certificados del registrador acompañados a la demanda, aparezca que tienen a su favor hipoteca o prenda sobre los mismos bienes, para que en el término de diez (10) días contados desde su respectiva notificación hagan valer sus créditos, sean o no exigibles. La citación se hará mediante notificación personal y si se designa curador ad litem el plazo para que esté presente la demanda será de diez (10) días a partir de su notificación. Citados los terceros acreedores, todas las demandas presentadas en tiempo se tramitarán conjuntamente con la inicial, y el juez librará un solo mandamiento ejecutivo para las que cumplan los requisitos necesarios para ello; respecto de las que no los cumplan se proferirán por separado los correspondientes autos. En la providencia que ordene seguir adelante la ejecución se fijará el orden de preferencia de los distintos créditos y se condenará al deudor en las costas causadas en interés general de los acreedores y en las propias de cada uno, que se liquidarán conjuntamente. Vencido el término para que concurran los acreedores citados, se adelantará el proceso hasta su terminación. Si hecho el pago al demandante y a los acreedores que concurrieron sobrare dinero, se retendrá el saldo a fin de que sobre él puedan hacer valer sus créditos los que no hubieren concurrido, mediante proceso ejecutivo que se tramitará a continuación, en el mismo expediente, y deberá iniciarse dentro de los treinta (30) días siguientes al mencionado pago, vencidos los cuales se entregará al ejecutado dicho saldo. - 5. Remate de bienes. El acreedor con hipoteca de primer grado, podrá hacer postura con base en la liquidación de su crédito; si quien lo hace es un acreedor hipotecario de segundo grado, requerirá la autorización de aquel y así sucesivamente los demás acreedores hipotecarios. Si el precio del bien fuere inferior al valor del crédito y las costas, se adjudicará el bien por dicha suma; si fuere superior, el juez dispondrá que el acreedor consigne a orden del juzgado la diferencia con la última liquidación aprobada del crédito, y de las costas si las hubiere, en el término de tres (3) días, caso en el cual aprobará el remate. Si el acreedor no realiza oportunamente la consignación se procederá como lo dispone el inciso final del artículo 453. Si son varios los acreedores y se han liquidado costas a favor de todos, se aplicará lo preceptuado en el numeral 7 artículo 365. Cuando el proceso verse sobre la efectividad de la prenda y esta se justiprecie en suma no mayor a un salario mínimo mensual, en firme el avalúo el acreedor podrá pedir su adjudicación dentro de los cinco (5) días siguientes, para lo cual en lo pertinente se aplicarán las reglas de este artículo. Cuando a pesar del remate o de la adjudicación del bien la obligación no se extinga, el acreedor podrá perseguir otros bienes del ejecutado, sin necesidad de prestar caución, siempre y cuando este sea el deudor de la obligación. - 6. Concurrencia de embargos. El embargo decretado con base en título hipotecario o prendario sujeto a registro, se inscribirá aunque se halle vigente otro practicado sobre el mismo bien en proceso ejecutivo seguido para el cobro de un crédito sin garantía real. Recibida la comunicación del nuevo embargo, simultáneamente con su inscripción el registrador deberá cancelar el anterior, dando inmediatamente informe escrito de ello al juez que lo decretó, quien, en caso de haberse practicado el secuestro, remitirá copia de la diligencia al juez que adelanta el proceso con base en garantía real para que tenga efectos en este y le oficie al secuestre dándole cuenta de ello. En tratándose de bienes no sujetos a registro, cuando el juez del proceso con garantía prendaria, antes de llevar a cabo el secuestro, tenga conocimiento de que en otro ejecutivo sin dicha garantía ya se practicó, librará oficio al juez de este proceso para que proceda como se dispone en el inciso anterior. Si en el proceso con base en garantía real se practica secuestro sobre los bienes prendados que hubieren sido secuestrados en proceso ejecutivo sin garantía real, el juez de aquel librará oficio al de este, para que cancele tal medida y comunique dicha decisión al secuestre. En todo caso, el remanente se considerará embargado a favor del proceso en el que se canceló el embargo o el secuestro a que se refieren los dos incisos anteriores. Cuando en diferentes procesos ejecutivos se decrete el embargo del mismo bien con base en garantías reales, prevalecerá el embargo que corresponda al gravamen que primero se registró. El demandante del proceso cuyo embargo se cancela, podrá hacer valer su derecho en el otro proceso dentro de la oportunidad señalada en el inciso primero del numeral 4. En tal caso, si en el primero se persiguen más bienes, se suspenderá su trámite hasta la terminación del segundo, una vez que en aquel se presente copia de la demanda y del mandamiento de pago. Si el producto de los bienes rematados en el proceso cuyo embargo prevaleció, no alcanzare a cubrir el crédito cobrado por el demandante del otro proceso, este se reanudará a fin de que se le pague la parte insoluta. Si en el proceso cuyo embargo se cancela intervienen otros acreedores, el trámite continuará respecto de estos, pero al distribuir el producto del remate se reservará lo que corresponda al acreedor hipotecario o prendario que hubiere comparecido al proceso cuyo embargo prevaleció. Satisfecho a dicho acreedor total o parcialmente su crédito en el otro proceso, la suma reservada o lo que restare de ella se distribuirá entre los demás acreedores cuyos créditos no hubieren sido cancelados; si quedare remanente y no estuviere embargado, se entregará al ejecutado. Cuando el embargo se cancele después de dictada sentencia de excepciones no podrá el demandado proponerlas de nuevo en el otro proceso. - 7. Obligaciones distintas de pagar sumas de dinero. Si la obligación garantizada con hipoteca o prenda es de entregar un cuerpo cierto o bienes de género, de hacer o de no hacer, el demandante procederá de conformidad con lo dispuesto en el artículo 428. Parágrafo. En los procesos de que trata este artículo no se aplicarán los artículos 462, 463 y 600. CAPÍTULO VII Ejecución para el Cobro de Deudas Fiscales

## 9056 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 593

**Categoria:** Embargos

**Pregunta:** Me llego un embargo del juzgado pero el nombre y la cedula no son los mios, solo se parecen.

**Estado:** recuperado=si · partido en 7 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 593.Embargos. Para efectuar embargos se procederá así: - 1. El de bienes sujetos a registro se comunicará a la autoridad competente de llevar el registro con los datos necesarios para la inscripción: si aquellos pertenecieren al afectado con la medida, lo inscribirá y expedirá a costa del solicitante un certificado sobre su situación jurídica en un período equivalente a diez (10) años, si fuere posible. Una vez inscrito el embargo, el certificado sobre la situación jurídica del bien se remitirá por el registrador directamente al juez. Si algún bien no pertenece al afectado, el registrador se abstendrá de inscribir el embargo y lo comunicará al juez; si lo registra, este de oficio o a petición de parte ordenará la cancelación del embargo. Cuando el bien esté siendo perseguido para hacer efectiva la garantía real, deberá aplicarse lo dispuesto en el numeral 2 del artículo 468. - 2. El de los derechos que por razón de mejoras o cosechas tenga una persona que ocupa un predio de propiedad de otra, se perfeccionará previniendo a aquella y al obligado al respectivo pago, que se entiendan con el secuestre para todo lo relacionado con las mejoras y sus productos o beneficios.101 Para el embargo de mejoras plantadas por una persona en terrenos baldíos, se notificará a esta para que se abstenga de enajenarlas o gravarlas. - 3. El de bienes muebles no sujetos a registro y el de la posesión sobre bienes muebles o inmuebles se consumará mediante el secuestro de estos, excepto en los casos contemplados en los numerales siguientes. - 4. El de un crédito u otro derecho semejante se perfeccionará con la notificación al deudor mediante entrega del correspondiente oficio, en el que se le prevendrá que para hacer el pago deberá constituir certificado de depósito a órdenes del juzgado. Si el deudor se negare a firmar el recibo del oficio, lo hará por él cualquiera persona que presencie el hecho. Al recibir el deudor la notificación deberá informar acerca de la existencia del crédito, de cuándo se hace exigible, de su valor, de cualquier embargo que con anterioridad se le hubiere comunicado y si se le notificó antes alguna cesión o si la aceptó, con indicación del nombre del cesionario y la fecha de aquella, so pena de responder por el correspondiente pago, de todo lo cual se le prevendrá en el oficio de embargo. La notificación al deudor interrumpe el término para la prescripción del crédito, y si aquel no lo paga oportunamente, el juez designará secuestre quien podrá adelantar proceso judicial para tal efecto. Si fuere hallado el título del crédito, se entregará al secuestre; en caso contrario, se le expedirán las copias que solicite para que inicie el proceso. El embargo del crédito de percepción sucesiva comprende los vencimientos posteriores a la fecha en que se decretó y los anteriores que no hubieren sido cancelados. - 5. El de derechos o créditos que la persona contra quien se decrete el embargo persiga o tenga en otro proceso se comunicará al juez que conozca de él para los fines consiguientes, y se considerará perfeccionado desde la fecha de recibo de la comunicación en el respectivo despacho judicial. - 6. El de acciones en sociedades anónimas o en comandita por acciones, bonos, certificados nominativos de depósito, unidades de fondos mutuos, títulos similares, efectos públicos nominativos y en general títulos valores a la orden, se comunicará al gerente, administrador o liquidador de la respectiva sociedad o empresa emisora o al representante administrativo de la entidad pública o a la entidad administradora, según sea el caso, para que tome nota de él, de lo cual deberá dar cuenta al juzgado dentro de los tres (3) días siguientes, so pena de incurrir en multa de dos (2) a cinco (5) salarios mínimos legales mensuales. El embargo se considerará perfeccionado desde la fecha de recibo del oficio y a partir de esta no podrá aceptarse ni autorizarse transferencia ni gravamen alguno. El de acciones, títulos, bonos y efectos públicos, títulos valores y efectos negociables a la orden y al portador, se perfeccionará con la entrega del respectivo título al secuestre. Los embargos previstos en este numeral se extienden a los dividendos, utilidades, intereses y demás beneficios que al derecho embargado correspondan, con los cuales deberá constituirse certificado de depósito a órdenes del juzgado, so pena de hacerse responsable de dichos valores. El secuestre podrá adelantar el cobro judicial, exigir rendición de cuentas y promover cualesquiera otras medidas autorizadas por la ley con dicho fin. - 7. El del interés de un socio en sociedad colectiva y de gestores de la en comandita, o de cuotas en una de responsabilidad limitada, o en cualquier otro tipo de sociedad, se comunicará a la autoridad encargada de la matrícula y registro de sociedades, la que no podrá registrar ninguna transferencia o gravamen de dicho interés, ni reforma de la sociedad que implique la exclusión del mencionado socio o la disminución de sus derechos en ella. A este embargo se aplicará lo dispuesto en el inciso tercero del numeral anterior y se comunicará al representante de la sociedad en la forma establecida en el inciso primero del numeral 4, a efecto de que cumpla lo dispuesto en tal inciso. - 8. Si el deudor o la persona contra quien se decreta el embargo fuere socio comanditario, se comunicará al socio o socios gestores o al liquidador, según fuere el caso. El embargo se considerará perfeccionado desde la fecha de recibo del oficio. - 9. El de salarios devengados o por devengar se comunicará al pagador o empleador en la forma indicada en el inciso primero del numeral 4 para que de las sumas respectivas retenga la proporción determinada por la ley y constituya certificado de depósito, previniéndole que de lo contrario responderá por dichos valores. Si no se hicieren las consignaciones el juez designará secuestre que deberá adelantar el cobro judicial, si fuere necesario. - 10. El de sumas de dinero depositadas en establecimientos bancarios y similares, se comunicará a la correspondiente entidad como lo dispone el inciso primero del numeral 4, debiéndose señalar la cuantía máxima de la medida, que no podrá exceder del valor del crédito y las costas más un cincuenta por ciento (50%). Aquellos deberán constituir certificado del depósito y ponerlo a disposición del juez dentro de los tres (3) días siguientes al recibo de la comunicación; con la recepción del oficio queda consumado el embargo. - 11. El de derechos proindiviso en bienes muebles se comunicará a los otros copartícipes, advirtiéndoles que en todo lo relacionado con aquellos deben entenderse con el secuestre. Parágrafo 1°. En todos los casos en que se utilicen mensajes de datos los emisores dejarán constancia de su envío y los destinatarios, sean oficinas públicas o particulares, tendrán el deber de revisarlos diariamente y tramitarlos de manera inmediata. Parágrafo 2°. La inobservancia de la orden impartida por el juez, en todos los caso previstos en este artículo, hará incurrir al destinatario del oficio respectivo en multas sucesivas de dos (2) a cinco (5) salarios mínimos mensuales.

## 9056 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 598

**Categoria:** Embargos

**Pregunta:** Me llego un embargo del juzgado pero el nombre y la cedula no son los mios, solo se parecen.

**Estado:** recuperado=si · partido en 4 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 598.Medidas cautelares en procesos de familia. En los procesos de nulidad de matrimonio, divorcio, cesación de efectos civiles de matrimonio religioso, separación de cuerpos y de bienes, liquidación de sociedades conyugales, disolución y liquidación de sociedades patrimoniales entre compañeros permanentes, se aplicarán las siguientes reglas: - 1. Cualquiera de las partes podrá pedir embargo y secuestro de los bienes que puedan ser objeto de gananciales y que estuvieran en cabeza de la otra. - 2. El embargo y secuestro practicados en estos procesos no impedirán perfeccionar los que se decreten sobre los mismos bienes en trámite de ejecución, antes de quedar en firme la sentencia favorable al demandante que en aquellos se dicte; con tal objeto, recibida la comunicación del nuevo embargo, simultáneamente con su inscripción, el registrador cancelará el anterior e informará de inmediato y por escrito al juez que adelanta el proceso de familia, quien, en caso de haberse practicado el secuestro, remitirá al juzgado donde se sigue el ejecutivo copia de la diligencia a fin de que tenga efecto en este, y oficiará al secuestre para darle cuenta de lo sucedido. El remanente no embargado en otras ejecuciones y los bienes que en estas se desembarguen, se considerarán embargados para los fines del asunto familiar. Ejecutoriada la sentencia que se dicte en los procesos nulidad, divorcio, cesación de los efectos civiles del matrimonio religioso, separación de cuerpos y de bienes, cesará la prelación, por lo que el juez lo comunicará de inmediato al registrador, para que se abstenga de inscribir nuevos embargos, salvo el hipotecario. - 3. Las anteriores medidas se mantendrán hasta la ejecutoria de la sentencia; pero si a consecuencia de esta fuere necesario liquidar la sociedad conyugal o patrimonial, continuarán vigentes en el proceso de liquidación. Si dentro de los dos (2) meses siguientes a la ejecutoria de la sentencia que disuelva la sociedad conyugal o patrimonial, no se hubiere promovido la liquidación de esta, se levantarán aun de oficio las medidas cautelares. - 4. Cualquiera de los cónyuges o compañeros permanentes podrá promover incidente con el propósito de que se levanten las medidas que afecten sus bienes propios. - 5. Si el juez lo considera conveniente, también podrá adoptar, según el caso, las siguientes medidas: - a) Autorizar la residencia separada de los cónyuges, y si estos fueren menores, disponer el depósito en casa de sus padres o de sus parientes más próximos o en la de un tercero. - b) Dejar a los hijos al cuidado de uno de los cónyuges o de ambos, o de un tercero. - c) Señalar la cantidad con que cada cónyuge deba contribuir, según su capacidad económica, para gastos de habitación y sostenimiento del otro cónyuge y de los hijos comunes, y la educación de estos. - d) Decretar, en caso de que la mujer esté embarazada, las medidas previstas por la ley para evitar suposición de parto. - e) Decretar, a petición de parte, el embargo y secuestro de los bienes sociales y los propios, con el fin de garantizar el pago de alimentos a que el cónyuge y los hijos tuvieren derecho, si fuere el caso. - f) A criterio del juez cualquier otra medida necesaria para evitar que se produzcan nuevos actos de violencia intrafamiliar o para hacer cesar sus efectos y, en general, en los asuntos de familia, podrá actuar de oficio en la adopción de las medidas personales de protección que requiera la pareja, el niño, niña o adolescente, el discapacitado mental y la persona de la tercera edad; para tal fin, podrá decretar y practicar las pruebas que estime pertinentes, incluyendo las declaraciones del niño, niña o adolescente. - 6. En el proceso de alimentos se decretará la medida cautelar prevista en el literal c) del numeral 5 y se dará aviso a las autoridades de emigración para que el demandado no pueda ausentarse del país sin prestar garantía suficiente que respalde el cumplimiento de la obligación hasta por dos (2) años. CAPÍTULO II Medidas cautelares en procesos ejecutivos

## 9056 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 599

**Categoria:** Embargos

**Pregunta:** Me llego un embargo del juzgado pero el nombre y la cedula no son los mios, solo se parecen.

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 599. Embargo y secuestro. Desde la presentación de la demanda el ejecutante podrá solicitar el embargo y secuestro de bienes del ejecutado.104 Cuando se ejecute por obligaciones de una persona fallecida, antes de liquidarse la sucesión, sólo podrán embargarse y secuestrarse bienes del causante. El juez, al decretar los embargos y secuestros, podrá limitarlos a lo necesario; el valor de los bienes no podrá exceder del doble del crédito cobrado, sus intereses y las costas prudencialmente calculadas, salvo que se trate de un solo bien o de bienes afectados por hipoteca o prenda que garanticen aquel crédito, o cuando la división disminuya su valor o su venalidad. En el momento de practicar el secuestro el juez deberá de oficio limitarlo en la forma indicada en el inciso anterior, si el valor de los bienes excede ostensiblemente del límite mencionado, o aparece de las facturas de compra, libros de contabilidad, certificados de catastro o recibos de pago de impuesto predial, o de otros documentos oficiales, siempre que se le exhiban tales pruebas en la diligencia. En los procesos ejecutivos, el ejecutado que proponga excepciones de mérito o el tercer afectado con la medida cautelar, podrán solicitarle al juez que ordene al ejecutante prestar caución hasta por el diez por ciento (10%) del valor actual de la ejecución para responder por los perjuicios que se causen con su práctica, so pena de levantamiento. La caución deberá prestarse dentro de los quince (15) días siguientes a la notificación del auto que la ordene. Contra la providencia anterior, no procede recurso de apelación. Para establecer el monto de la caución, el juez deberá tener en cuenta la clase de bienes sobre los que recae la medida cautelar practicada y la apariencia de buen derecho de las excepciones de mérito. La caución a que se refiere el artículo anterior, no procede cuando el ejecutante sea una entidad financiera o vigilada por la Superintendencia Financiera de Colombia o una entidad de derecho público. Cuando se trate de caución expedida por compañía de seguros, su efectividad podrá reclamarse también por el asegurado o beneficiario directamente ante la aseguradora, de acuerdo con las normas del Código de Comercio. Parágrafo. El ejecutado podrá solicitar que de la relación de bienes de su propiedad e ingresos, el juez ordene el embargo y secuestro de los que señale con el fin de evitar que se embarguen otros, salvo cuando el embargo se funde en garantía real. El juez, previo traslado al ejecutante por dos (2) días, accederá a la solicitud siempre que sean suficientes, con sujeción a los criterios establecidos en los dos incisos anteriores.

## 9057 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 468

**Categoria:** Embargos

**Pregunta:** Soy codeudor de un credito y me embargaron sin avisarme nada antes.

**Estado:** recuperado=si · partido en 9 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 468. Disposiciones especiales para la efectividad de la garantía real. Cuando el acreedor persiga el pago de una obligación en dinero, exclusivamente con el producto de los bienes gravados con hipoteca o prenda, se observarán las siguientes reglas: - 1. Requisitos de la demanda. La demanda, además de cumplir los requisitos de toda demanda ejecutiva, deberá indicar los bienes objeto de gravamen. A la demanda se acompañará título que preste mérito ejecutivo, así como el de la hipoteca o prenda, y si se trata de aquella un certificado del registrador respecto de la propiedad del demandado sobre el bien inmueble perseguido y los gravámenes que lo afecten, en un período de diez (10) años si fuere posible. Cuando se trate de prenda sin tenencia, el certificado deberá versar sobre la vigencia del gravamen. El certificado que debe anexarse a la demanda debe haber sido expedido con una antelación no superior a un (1) mes. La demanda deberá dirigirse contra el actual propietario del inmueble, la nave o la aeronave materia de la hipoteca o de la prenda. Si el pago de la obligación a cargo del deudor se hubiere pactado en diversos instalamentos, en la demanda podrá pedirse el valor de todos ellos, en cuyo caso se harán exigibles los no vencidos. Si del certificado del registrador aparece que sobre los bienes gravados con prenda o hipoteca existe algún embargo ordenado en proceso ejecutivo, en la demanda deberá informarse, bajo juramento, si en aquel ha sido citado el acreedor, y de haberlo sido, la fecha de la notificación. - 2. Embargo y secuestro. Simultáneamente con el mandamiento ejecutivo y sin necesidad de caución, el juez decretará el embargo y secuestro del bien hipotecado o dado en prenda, que se persiga en la demanda. El registrador deberá inscribir el embargo, aunque el demandado haya dejado de ser propietario del bien. Acreditado el embargo, si el bien ya no pertenece al demandado, el juez de oficio tendrá como sustituto al actual propietario a quien se le notificará el mandamiento de pago. En este proceso no habrá lugar a reducción de embargos ni al beneficio de competencia. - 3. Orden de seguir adelante la ejecución. Si no se proponen excepciones y se hubiere practicado el embargo de los bienes gravados con hipoteca o prenda, o el ejecutado hubiere prestado caución para evitarlo o levantarlo, se ordenará seguir adelante la ejecución para que con el producto de ellos se pague al demandante el crédito y las costas. El secuestro de los bienes inmuebles no será necesario para ordenar seguir adelante la ejecución, pero sí para practicar el avalúo y señalar la fecha del remate. Cuando no se pueda efectuar el secuestro por oposición de poseedor, o se levante por el mismo motivo, se aplicará lo dispuesto en el numeral 3 del artículo 596, sin que sea necesario reformar la demanda. - 4. Intervención de terceros acreedores. En el mandamiento ejecutivo se ordenará la citación de los terceros acreedores que conforme a los certificados del registrador acompañados a la demanda, aparezca que tienen a su favor hipoteca o prenda sobre los mismos bienes, para que en el término de diez (10) días contados desde su respectiva notificación hagan valer sus créditos, sean o no exigibles. La citación se hará mediante notificación personal y si se designa curador ad litem el plazo para que esté presente la demanda será de diez (10) días a partir de su notificación. Citados los terceros acreedores, todas las demandas presentadas en tiempo se tramitarán conjuntamente con la inicial, y el juez librará un solo mandamiento ejecutivo para las que cumplan los requisitos necesarios para ello; respecto de las que no los cumplan se proferirán por separado los correspondientes autos. En la providencia que ordene seguir adelante la ejecución se fijará el orden de preferencia de los distintos créditos y se condenará al deudor en las costas causadas en interés general de los acreedores y en las propias de cada uno, que se liquidarán conjuntamente. Vencido el término para que concurran los acreedores citados, se adelantará el proceso hasta su terminación. Si hecho el pago al demandante y a los acreedores que concurrieron sobrare dinero, se retendrá el saldo a fin de que sobre él puedan hacer valer sus créditos los que no hubieren concurrido, mediante proceso ejecutivo que se tramitará a continuación, en el mismo expediente, y deberá iniciarse dentro de los treinta (30) días siguientes al mencionado pago, vencidos los cuales se entregará al ejecutado dicho saldo. - 5. Remate de bienes. El acreedor con hipoteca de primer grado, podrá hacer postura con base en la liquidación de su crédito; si quien lo hace es un acreedor hipotecario de segundo grado, requerirá la autorización de aquel y así sucesivamente los demás acreedores hipotecarios. Si el precio del bien fuere inferior al valor del crédito y las costas, se adjudicará el bien por dicha suma; si fuere superior, el juez dispondrá que el acreedor consigne a orden del juzgado la diferencia con la última liquidación aprobada del crédito, y de las costas si las hubiere, en el término de tres (3) días, caso en el cual aprobará el remate. Si el acreedor no realiza oportunamente la consignación se procederá como lo dispone el inciso final del artículo 453. Si son varios los acreedores y se han liquidado costas a favor de todos, se aplicará lo preceptuado en el numeral 7 artículo 365. Cuando el proceso verse sobre la efectividad de la prenda y esta se justiprecie en suma no mayor a un salario mínimo mensual, en firme el avalúo el acreedor podrá pedir su adjudicación dentro de los cinco (5) días siguientes, para lo cual en lo pertinente se aplicarán las reglas de este artículo. Cuando a pesar del remate o de la adjudicación del bien la obligación no se extinga, el acreedor podrá perseguir otros bienes del ejecutado, sin necesidad de prestar caución, siempre y cuando este sea el deudor de la obligación. - 6. Concurrencia de embargos. El embargo decretado con base en título hipotecario o prendario sujeto a registro, se inscribirá aunque se halle vigente otro practicado sobre el mismo bien en proceso ejecutivo seguido para el cobro de un crédito sin garantía real. Recibida la comunicación del nuevo embargo, simultáneamente con su inscripción el registrador deberá cancelar el anterior, dando inmediatamente informe escrito de ello al juez que lo decretó, quien, en caso de haberse practicado el secuestro, remitirá copia de la diligencia al juez que adelanta el proceso con base en garantía real para que tenga efectos en este y le oficie al secuestre dándole cuenta de ello. En tratándose de bienes no sujetos a registro, cuando el juez del proceso con garantía prendaria, antes de llevar a cabo el secuestro, tenga conocimiento de que en otro ejecutivo sin dicha garantía ya se practicó, librará oficio al juez de este proceso para que proceda como se dispone en el inciso anterior. Si en el proceso con base en garantía real se practica secuestro sobre los bienes prendados que hubieren sido secuestrados en proceso ejecutivo sin garantía real, el juez de aquel librará oficio al de este, para que cancele tal medida y comunique dicha decisión al secuestre. En todo caso, el remanente se considerará embargado a favor del proceso en el que se canceló el embargo o el secuestro a que se refieren los dos incisos anteriores. Cuando en diferentes procesos ejecutivos se decrete el embargo del mismo bien con base en garantías reales, prevalecerá el embargo que corresponda al gravamen que primero se registró. El demandante del proceso cuyo embargo se cancela, podrá hacer valer su derecho en el otro proceso dentro de la oportunidad señalada en el inciso primero del numeral 4. En tal caso, si en el primero se persiguen más bienes, se suspenderá su trámite hasta la terminación del segundo, una vez que en aquel se presente copia de la demanda y del mandamiento de pago. Si el producto de los bienes rematados en el proceso cuyo embargo prevaleció, no alcanzare a cubrir el crédito cobrado por el demandante del otro proceso, este se reanudará a fin de que se le pague la parte insoluta. Si en el proceso cuyo embargo se cancela intervienen otros acreedores, el trámite continuará respecto de estos, pero al distribuir el producto del remate se reservará lo que corresponda al acreedor hipotecario o prendario que hubiere comparecido al proceso cuyo embargo prevaleció. Satisfecho a dicho acreedor total o parcialmente su crédito en el otro proceso, la suma reservada o lo que restare de ella se distribuirá entre los demás acreedores cuyos créditos no hubieren sido cancelados; si quedare remanente y no estuviere embargado, se entregará al ejecutado. Cuando el embargo se cancele después de dictada sentencia de excepciones no podrá el demandado proponerlas de nuevo en el otro proceso. - 7. Obligaciones distintas de pagar sumas de dinero. Si la obligación garantizada con hipoteca o prenda es de entregar un cuerpo cierto o bienes de género, de hacer o de no hacer, el demandante procederá de conformidad con lo dispuesto en el artículo 428. Parágrafo. En los procesos de que trata este artículo no se aplicarán los artículos 462, 463 y 600. CAPÍTULO VII Ejecución para el Cobro de Deudas Fiscales

## 9057 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 470

**Categoria:** Embargos

**Pregunta:** Soy codeudor de un credito y me embargaron sin avisarme nada antes.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 470. Embargos. Si el deudor no denuncia bienes para el pago o los denunciados no fueren suficientes, el funcionario ejecutor solicitará toda clase de datos sobre los que a aquel pertenezcan, y las entidades o personas a quienes se les soliciten deberán suministrarlos, so pena de que se les impongan multas sucesivas de cinco (5) a diez (10) salarios mínimos mensuales (smlmv), salvo que exista reserva legal En caso de concurrencia de embargos, se aplicará lo dispuesto en el artículo 465.

## 9057 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 593

**Categoria:** Embargos

**Pregunta:** Soy codeudor de un credito y me embargaron sin avisarme nada antes.

**Estado:** recuperado=si · partido en 7 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 593.Embargos. Para efectuar embargos se procederá así: - 1. El de bienes sujetos a registro se comunicará a la autoridad competente de llevar el registro con los datos necesarios para la inscripción: si aquellos pertenecieren al afectado con la medida, lo inscribirá y expedirá a costa del solicitante un certificado sobre su situación jurídica en un período equivalente a diez (10) años, si fuere posible. Una vez inscrito el embargo, el certificado sobre la situación jurídica del bien se remitirá por el registrador directamente al juez. Si algún bien no pertenece al afectado, el registrador se abstendrá de inscribir el embargo y lo comunicará al juez; si lo registra, este de oficio o a petición de parte ordenará la cancelación del embargo. Cuando el bien esté siendo perseguido para hacer efectiva la garantía real, deberá aplicarse lo dispuesto en el numeral 2 del artículo 468. - 2. El de los derechos que por razón de mejoras o cosechas tenga una persona que ocupa un predio de propiedad de otra, se perfeccionará previniendo a aquella y al obligado al respectivo pago, que se entiendan con el secuestre para todo lo relacionado con las mejoras y sus productos o beneficios.101 Para el embargo de mejoras plantadas por una persona en terrenos baldíos, se notificará a esta para que se abstenga de enajenarlas o gravarlas. - 3. El de bienes muebles no sujetos a registro y el de la posesión sobre bienes muebles o inmuebles se consumará mediante el secuestro de estos, excepto en los casos contemplados en los numerales siguientes. - 4. El de un crédito u otro derecho semejante se perfeccionará con la notificación al deudor mediante entrega del correspondiente oficio, en el que se le prevendrá que para hacer el pago deberá constituir certificado de depósito a órdenes del juzgado. Si el deudor se negare a firmar el recibo del oficio, lo hará por él cualquiera persona que presencie el hecho. Al recibir el deudor la notificación deberá informar acerca de la existencia del crédito, de cuándo se hace exigible, de su valor, de cualquier embargo que con anterioridad se le hubiere comunicado y si se le notificó antes alguna cesión o si la aceptó, con indicación del nombre del cesionario y la fecha de aquella, so pena de responder por el correspondiente pago, de todo lo cual se le prevendrá en el oficio de embargo. La notificación al deudor interrumpe el término para la prescripción del crédito, y si aquel no lo paga oportunamente, el juez designará secuestre quien podrá adelantar proceso judicial para tal efecto. Si fuere hallado el título del crédito, se entregará al secuestre; en caso contrario, se le expedirán las copias que solicite para que inicie el proceso. El embargo del crédito de percepción sucesiva comprende los vencimientos posteriores a la fecha en que se decretó y los anteriores que no hubieren sido cancelados. - 5. El de derechos o créditos que la persona contra quien se decrete el embargo persiga o tenga en otro proceso se comunicará al juez que conozca de él para los fines consiguientes, y se considerará perfeccionado desde la fecha de recibo de la comunicación en el respectivo despacho judicial. - 6. El de acciones en sociedades anónimas o en comandita por acciones, bonos, certificados nominativos de depósito, unidades de fondos mutuos, títulos similares, efectos públicos nominativos y en general títulos valores a la orden, se comunicará al gerente, administrador o liquidador de la respectiva sociedad o empresa emisora o al representante administrativo de la entidad pública o a la entidad administradora, según sea el caso, para que tome nota de él, de lo cual deberá dar cuenta al juzgado dentro de los tres (3) días siguientes, so pena de incurrir en multa de dos (2) a cinco (5) salarios mínimos legales mensuales. El embargo se considerará perfeccionado desde la fecha de recibo del oficio y a partir de esta no podrá aceptarse ni autorizarse transferencia ni gravamen alguno. El de acciones, títulos, bonos y efectos públicos, títulos valores y efectos negociables a la orden y al portador, se perfeccionará con la entrega del respectivo título al secuestre. Los embargos previstos en este numeral se extienden a los dividendos, utilidades, intereses y demás beneficios que al derecho embargado correspondan, con los cuales deberá constituirse certificado de depósito a órdenes del juzgado, so pena de hacerse responsable de dichos valores. El secuestre podrá adelantar el cobro judicial, exigir rendición de cuentas y promover cualesquiera otras medidas autorizadas por la ley con dicho fin. - 7. El del interés de un socio en sociedad colectiva y de gestores de la en comandita, o de cuotas en una de responsabilidad limitada, o en cualquier otro tipo de sociedad, se comunicará a la autoridad encargada de la matrícula y registro de sociedades, la que no podrá registrar ninguna transferencia o gravamen de dicho interés, ni reforma de la sociedad que implique la exclusión del mencionado socio o la disminución de sus derechos en ella. A este embargo se aplicará lo dispuesto en el inciso tercero del numeral anterior y se comunicará al representante de la sociedad en la forma establecida en el inciso primero del numeral 4, a efecto de que cumpla lo dispuesto en tal inciso. - 8. Si el deudor o la persona contra quien se decreta el embargo fuere socio comanditario, se comunicará al socio o socios gestores o al liquidador, según fuere el caso. El embargo se considerará perfeccionado desde la fecha de recibo del oficio. - 9. El de salarios devengados o por devengar se comunicará al pagador o empleador en la forma indicada en el inciso primero del numeral 4 para que de las sumas respectivas retenga la proporción determinada por la ley y constituya certificado de depósito, previniéndole que de lo contrario responderá por dichos valores. Si no se hicieren las consignaciones el juez designará secuestre que deberá adelantar el cobro judicial, si fuere necesario. - 10. El de sumas de dinero depositadas en establecimientos bancarios y similares, se comunicará a la correspondiente entidad como lo dispone el inciso primero del numeral 4, debiéndose señalar la cuantía máxima de la medida, que no podrá exceder del valor del crédito y las costas más un cincuenta por ciento (50%). Aquellos deberán constituir certificado del depósito y ponerlo a disposición del juez dentro de los tres (3) días siguientes al recibo de la comunicación; con la recepción del oficio queda consumado el embargo. - 11. El de derechos proindiviso en bienes muebles se comunicará a los otros copartícipes, advirtiéndoles que en todo lo relacionado con aquellos deben entenderse con el secuestre. Parágrafo 1°. En todos los casos en que se utilicen mensajes de datos los emisores dejarán constancia de su envío y los destinatarios, sean oficinas públicas o particulares, tendrán el deber de revisarlos diariamente y tramitarlos de manera inmediata. Parágrafo 2°. La inobservancia de la orden impartida por el juez, en todos los caso previstos en este artículo, hará incurrir al destinatario del oficio respectivo en multas sucesivas de dos (2) a cinco (5) salarios mínimos mensuales.

## 9058 · Ley 1620 de 2013 (Sistema Nacional de Convivencia Escolar) · articulo 2

**Categoria:** Educacion / debido proceso disciplinario

**Pregunta:** Expulsaron a mi hijo del colegio por un video que circulo, sin llamarnos a nosotros antes.

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 2°. En el marco de la presente ley se entiende por: - Competencias ciudadanas: Es una de las competencias básicas que se define como el conjunto de conocimientos y de habilidades cognitivas, emocionales y comunicativas que, articulados entre sí, hacen posible que el ciudadano actúe de manera constructiva en una sociedad democrática. - Educación para el ejercicio de los derechos humanos, sexuales y reproductivos: Es aquella orientada a formar personas capaces de reconocerse como sujetos activos titulares de derechos humanos, sexuales y reproductivos con la cual desarrollarán competencias para relacionarse consigo mismo y con los demás, con criterios de respeto por sí mismo, por el otro y por el entorno, con el fin de poder alcanzar un estado de bienestar físico, mental y social que les posibilite tomar decisiones asertivas, informadas y autónomas para ejercer una sexualidad libre, satisfactoria, responsable y sana en torno a la construcción de su proyecto de vida y a la transformación de las dinámicas sociales, hacia el establecimiento de relaciones más justas, democráticas y responsables. - Acoso escolar obullying: Conducta negativa, intencional metódica y sistemática de agresión, intimidación, humillación, ridiculización, difamación, coacción, aislamiento deliberado, amenaza o incitación a la violencia o cualquier forma de maltrato psicológico, verbal, físico o por medios electrónicos contra un niño, niña, o adolescente, por parte de un estudiante o varios de sus pares con quienes mantiene una relación de poder asimétrica, que se presenta de forma reiterada o a lo largo de un tiempo determinado. También puede ocurrir por parte de docentes contra estudiantes, o por parte de estudiantes contra docentes, ante la indiferencia o complicidad de su entorno. El acoso escolar tiene consecuencias sobre la salud, el bienestar emocional y el rendimiento escolar de los estudiantes y sobre el ambiente de aprendizaje y el clima escolar del establecimiento educativo. - Ciberbullying o ciberacoso escolar: Forma de intimidación con uso deliberado de tecnologías de información (internet, redes sociales virtuales, telefonía móvil y videojuegos online) para ejercer maltrato psicológico y continuado. CAPÍTULO II Sistema Nacional de Convivencia Escolar y Formación para los Derechos Humanos, la Educación para la Sexualidad y la Prevención y Mitigación de la Violencia Escolar

## 9058 · Ley 115 de 1994 (Ley General de Educacion) · articulo 82

**Categoria:** Educacion / debido proceso disciplinario

**Pregunta:** Expulsaron a mi hijo del colegio por un video que circulo, sin llamarnos a nosotros antes.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 82.Derogado.

## 9058 · Ley 115 de 1994 (Ley General de Educacion) · articulo 134

**Categoria:** Educacion / debido proceso disciplinario

**Pregunta:** Expulsaron a mi hijo del colegio por un video que circulo, sin llamarnos a nosotros antes.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 134. Derogado.

## 9058 · Ley 115 de 1994 (Ley General de Educacion) · articulo 149

**Categoria:** Educacion / debido proceso disciplinario

**Pregunta:** Expulsaron a mi hijo del colegio por un video que circulo, sin llamarnos a nosotros antes.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 149. Derogado.

## 9058 · Ley 115 de 1994 (Ley General de Educacion) · articulo 172

**Categoria:** Educacion / debido proceso disciplinario

**Pregunta:** Expulsaron a mi hijo del colegio por un video que circulo, sin llamarnos a nosotros antes.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 172. Derogado

## 9060 · Ley 80 de 1993 (Estatuto General de Contratacion de la Administracion Publica) · articulo 4

**Categoria:** Contratacion estatal y facturacion

**Pregunta:** Soy contratista del municipio y me piden firmar actas de recibo de obras que todavia no se han hecho.

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 4o. DE LOS DERECHOS Y DEBERES DE LAS ENTIDADES ESTATALES. Para la consecución de los fines de que trata el artículo anterior, las entidades estatales: 1o. Exigirán del contratista la ejecución idónea y oportuna del objeto contratado. Igual exigencia podrán hacer al garante. 2o. Adelantarán las gestiones necesarias para el reconocimiento y cobro de las sanciones pecuniarias y garantías a que hubiere lugar. 3o. Solicitarán la actualización o la revisión de los precios cuando se produzcan fenómenos que alteren en su contra el equilibrio económico o financiero del contrato. 4o. Adelantarán revisiones periódicas de las obras ejecutadas, servicios prestados o bienes sumistrados, para verificar que ellos cumplan con las condiciones de calidad ofrecidas por los contratistas, y promoverán las acciones de responsabilidad contra éstos y sus garantes cuando dichas condiciones no se cumplan. Las revisiones periódicas a que se refiere el presente numeral deberán llevarse a cabo por lo menos una vez cada seis (6) meses durante el término de vigencia de las garantías. 5o. Exigirán que la calidad de los bienes y servicios adquiridos por las entidades estatales se ajuste a los requisitos mínimos previstos en las normas técnicas obligatorias, sin perjuicio de la facultad de exigir que tales bienes o servicios cumplan con las normas técnicas colombianas o, en su defecto, con normas internacionales elaboradas por organismos reconocidos a nivel mundial o con normas extranjeras aceptadas en los acuerdos internacionales suscritos por Colombia. 6o. Adelantarán las acciones conducentes a obtener la indemnización de los daños que sufran en desarrollo o con ocasión del contrato celebrado. 7o. Sin perjuicio del llamamiento en garantía, repetirán contra los servidores públicos, contra el contratista o los terceros responsables, según el caso, por las indemnizaciones que deban pagar como consecuencia de la actividad contractual. 8o. Adoptarán las medidas necesarias para mantener durante el desarrollo y ejecución del contrato las condiciones técnicas, económicas y financieras existentes al momento de proponer en los casos en que se hubiere realizado licitación o concurso, o de contratar en los casos de contratación directa. Para ello utilizarán los mecanismos de ajuste y revisión de precios, acudirán a los procedimientos de revisión y corrección de tales mecanismos si fracasan los supuestos o hipótesis para la ejecución y pactarán intereses moratorios. Sin perjuicio de la actualización o revisión de precios, en caso de no haberse pactado intereses moratorios, se aplicará la tasa equivalente al doble del interés legal civil sobre el valor histórico actualizado. 9o. Actuarán de tal modo que por causas a ellas imputables, no sobrevenga una mayor onerosidad en el cumplimiento de las obligaciones a cargo del contratista. Con este fin, en el menor tiempo posible, corregirán los desajustes que pudieren presentarse y acordarán los mecanismos y procedimientos pertinentes para precaver o solucionar rápida y eficazmente las diferencias o situaciones litigiosas que llegaren a presentarse. 10°. Respetarán el orden de presentación de los pagos por parte de los contratistas. Sólo por razones de interés público, el jefe de la entidad podrá modificar dicho orden dejando constancia de tal actuación. Para el efecto, las entidades deben llevar un registro de presentación por parte de los contratistas, de los documentos requeridos para hacer efectivos los pagos derivados de los contratos, de tal manera que estos puedan verificar el estricto respeto al derecho de turno. Dicho registro será público. Lo dispuesto en este numeral no se aplicará respecto de aquellos pagos cuyos soportes hayan sido presentados en forma incompleta o se encuentren pendientes del cumplimiento de requisitos previstos en el contrato del cual se derivan.

## 9060 · Ley 80 de 1993 (Estatuto General de Contratacion de la Administracion Publica) · articulo 25

**Categoria:** Contratacion estatal y facturacion

**Pregunta:** Soy contratista del municipio y me piden firmar actas de recibo de obras que todavia no se han hecho.

**Estado:** recuperado=si · partido en 9 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 25. DEL PRINCIPIO DE ECONOMIA. En virtud de este principio: 1o. En las normas de selección y en los pliegos de condiciones o términos de referencia para la escogencia de contratistas, se cumplirán y establecerán los procedimientos y etapas estrictamente necesarios para asegurar la selección objetiva de la propuesta más favorable. Para este propósito, se señalarán términos preclusivos y perentorios para las diferentes etapas de la selección y las autoridades darán impulso oficioso a las actuaciones. 2o. Las normas de los procedimientos contractuales se interpretarán de tal manera que no den ocasión a seguir trámites distintos y adicionales a los expresamente previstos o que permitan valerse de los defectos de forma o de la inobservancia de requisitos para no decidir o proferir providencias inhibitorias. 3o. Se tendrá en consideración que las reglas y procedimientos constituyen mecanismos de la actividad contractual que buscan servir a los fines estatales, a la adecuada, continua y eficiente prestación de los servicios públicos y a la protección y garantía de los derechos de los administrados. 4o. Los trámites se adelantarán con austeridad de tiempo, medios y gastos y se impedirán las dilaciones y los retardos en la ejecución del contrato. 5o. Se adoptarán procedimientos que garanticen la pronta solución de las diferencias y controversias que con motivo de la celebración y ejecución del contrato se presenten. 6o. Las entidades estatales abrirán licitaciones o concursos e iniciarán procesos de suscripción de contratos, cuando existan las respectivas partidas o disponibilidades presupuestales. 7o. La conveniencia o inconveniencia del objeto a contratar y las autorizaciones y aprobaciones para ello, se analizarán o impartirán con antelación al inicio del proceso de selección del contratista o al de la firma del contrato, según el caso. 8o. El acto de adjudicación y el contrato no se someterán a aprobaciones o revisiones administrativas posteriores, ni a cualquier otra clase de exigencias o requisitos, diferentes de los previstos en este estatuto. 9o. En los procesos de contratación intervendrán el jefe y las unidades asesoras y ejecutoras de la entidad que se señalen en las correspondientes normas sobre su organización y funcionamiento. - 10. Los jefes o representantes de las entidades a las que se aplica la presente ley, podrán delegar la facultad para celebrar contratos en los términos previstos en el artículo 12 de esta ley y con sujeción a las cuantías que señalen sus respectivas juntas o consejos directivos. En los demás casos, dichas cuantías las fijará el reglamento. - 11. Las corporaciones de elección popular y los organismos de control y vigilancia no intervendrán en los procesos de contratación, salvo en lo relacionado con la solicitud de audiencia pública para la adjudicación en caso de licitación. De conformidad con lo previsto en los artículos 300, numeral 9o., y 313, numeral 3o., de la Constitución Política, las asambleas departamentales y los concejos municipales autorizarán a los gobernadores y alcaldes, respectivamente, para la celebración de contratos. - 12. Previo a la apertura de un proceso de selección, o a la firma del contrato en el caso en que la modalidad de selección sea contratación directa, deberán elaborarse los estudios, diseños y proyectos requeridos, y los pliegos de condiciones, según corresponda. Cuando el objeto de la contratación incluya la realización de una obra, en la misma oportunidad señalada en el inciso primero, la entidad contratante deberá contar con los estudios y diseños que permitan establecer la viabilidad del proyecto y su impacto social, económico y ambiental. Esta condición será aplicable incluso para los contratos que incluyan dentro del objeto el diseño. Parágrafo 1°. Para efectos de decretar su expropiación, además de los motivos determinados en otras leyes vigentes, declárese de utilidad pública o interés social los bienes inmuebles necesarios para la ejecución de proyectos de infraestructura de transporte. Para estos efectos, el procedimiento para cada proyecto de infraestructura de transporte diseñado será el siguiente: - 1. La entidad responsable expedirá una resolución mediante la cual determine de forma precisa las coordenadas del proyecto. - 2. El Instituto Geográfico Agustín Codazzi - IGAC o la entidad competente según el caso, en los dos (2) meses siguientes a la publicación de la resolución de que trata el numeral anterior, procederá a identificar los predios que se ven afectados por el proyecto y ordenará registrar la calidad de predios de utilidad pública o interés social en los respectivos registros catastrales y en los folios de matrícula inmobiliaria, quedando dichos predios fuera del comercio a partir del mencionado registro. - 3. Efectuado el Registro de que trata el numeral anterior, en un término de seis (6) meses el IGAC o la entidad competente, con cargo a recursos de la entidad responsable del proyecto, realizará el avalúo comercial del inmueble y lo notificará a esta y al propietario y demás interesados acreditados. - 4. El avalúo de que trata el numeral anterior deberá incluir el valor de las posesiones si las hubiera y de las otras indemnizaciones o compensaciones que fuera del caso realizar por afectar dicha declaratoria el patrimonio de los particulares. - 5. El Gobierno Nacional reglamentará las condiciones para determinar el valor del precio de adquisición o precio indemnizatorio que se reconocerá a los propietarios en los procesos de enajenación voluntaria y expropiación judicial y administrativa, teniendo en cuenta la localización, las condiciones físicas y jurídicas y la destinación económica de los inmuebles. - 6. Los interesados acreditados podrán interponer los recursos de ley en los términos del Código Contencioso Administrativo contra el avalúo del IGAC o de la entidad competente. - 7. En firme el avalúo, la entidad responsable del proyecto o el contratista si así se hubiere pactado, pagará dentro de los tres (3) meses siguientes, las indemnizaciones o compensaciones a que hubiere lugar. Al recibir el pago el particular, se entiende que existe mutuo acuerdo en la negociación y transacción de posibles indemnizaciones futuras. - 8. Efectuado el pago por mutuo acuerdo, se procederá a realizar el registro del predio a nombre del responsable del proyecto ratificando la naturaleza de bien como de uso público e interés social, el cual gozará de los beneficios del artículo 63 de la Constitución Política. - 9. De no ser posible el pago directo de la indemnización o compensación, se expedirá un acto administrativo de expropiación por parte de la entidad responsable del proyecto y se realizará el pago por consignación a órdenes del Juez o Tribunal Contencioso Administrativo competente, acto con el cual quedará cancelada la obligación. - 10. La resolución de expropiación será el título con fundamento en el cual se procederá al registro del predio a nombre de la entidad responsable del proyecto y que, como bien de uso público e interés social, gozará de los beneficios del artículo 63 de la Constitución Política. Lo anterior, sin perjuicio del derecho de las personas objeto de indemnización o compensación a recurrir ante los Jueces Contencioso Administrativos el valor de las mismas en cada caso particular. - 11. La entidad responsable del proyecto deberá notificar a las personas objeto de la indemnización o compensación que el pago de la misma se realizó. Una vez efectuada la notificación, dichos sujetos deberán entregar el inmueble dentro de los quince (15) días hábiles siguientes. - 12. En el evento en que las personas objeto de indemnización o compensación no entreguen el inmueble dentro del término señalado, la entidad responsable del proyecto y las autoridades locales competentes deberán efectuar el desalojo dentro del mes siguiente al vencimiento del plazo para entrega del inmueble. - 13. El presente parágrafo también será aplicable para proyectos de infraestructura de transporte que estén contratados o en ejecución al momento de expedición de la presente ley. Parágrafo 2°. El avalúo comercial del inmueble requerido para la ejecución de proyectos de infraestructura de transporte, en la medida en que supere en un 50% el valor del avalúo catastral, podrá ser utilizado como criterio para actualizar el avalúo catastral de los inmuebles que fueren desenglobados como consecuencia del proceso de enajenación voluntaria o expropiación judicial o administrativa. - 13. Las autoridades constituirán las reservas y compromisos presupuestales necesarios, tomando como base el valor de las prestaciones al momento de celebrar el contrato y el estimativo de los ajustes resultantes de la aplicación de la cláusula de actualización de precios. - 14. Las entidades incluirán en sus presupuestos anuales una apropiación global destinada a cubrir los costos imprevistos ocasionados por los retardos en los pagos, así como los que se originen en la revisión de los precios pactados por razón de los cambios o alteraciones en las condiciones iniciales de los contratos por ellas celebrados. - 15. Las autoridades no exigirán sellos, autenticaciones, documentos originales o autenticados, reconocimientos de firmas, traducciones oficiales, ni cualquier otra clase de formalidades o exigencias rituales, salvo cuando en forma perentoria y expresa lo exijan leyes especiales. - 16. En las solicitudes que se presenten en el curso de la ejecución del contrato, si la entidad estatal no se pronuncia dentro del término de tres (3) meses siguientes, se entenderá que la decisión es favorable a las pretensiones del solicitante en virtud del silencio administrativo positivo. Pero el funcionario o funcionarios competentes para dar respuesta serán responsables en los términos de esta ley. - 17. Las entidades no rechazarán las solicitudes que se les formulen por escrito aduciendo la inobservancia por parte del peticionario de las formalidades establecidas por la entidad para su tramitación y oficiosamente procederán a corregirlas y a subsanar los defectos que se adviertan en ellas. Igualmente, estarán obligadas a radicar las actas o cuentas de cobro en la fecha en que sean presentadas por el contratista, procederán a corregirlas o ajustarlas oficiosamente si a ello hubiere lugar y, si esto no fuere posible, las devolverán a la mayor brevedad explicando por escrito los motivos en que se fundamente tal determinación. - 18. La declaratoria de desierta de la licitación o concurso únicamente procederá por motivos o causas que impidan la escogencia objetiva y se declarará en acto administrativo en el que se señalarán en forma expresa y detallada las razones que han conducido a esa decisión. - 20. Los fondos destinados a la cancelación de obligaciones derivadas de contratos estatales podrán ser entregados en administración fiduciaria o bajo cualquier otra forma de manejo que permita la obtención de beneficios y ventajas financieras y el pago oportuno de lo adeudado.

## 9060 · Ley 80 de 1993 (Estatuto General de Contratacion de la Administracion Publica) · articulo 32

**Categoria:** Contratacion estatal y facturacion

**Pregunta:** Soy contratista del municipio y me piden firmar actas de recibo de obras que todavia no se han hecho.

**Estado:** recuperado=si · partido en 6 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 32. DE LOS CONTRATOS ESTATALES. Son contratos estatales todos los actos jurídicos generadores de obligaciones que celebren las entidades a que se refiere el presente estatuto, previstos en el derecho privado o en disposiciones especiales, o derivados del ejercicio de la autonomía de la voluntad, así como los que, a título enunciativo, se definen a continuación: 1o. Contrato de obra. Son contratos de obra los que celebren las entidades estatales para la construcción, mantenimiento, instalación y, en general, para la realización de cualquier otro trabajo material sobre bienes inmuebles, cualquiera que sea la modalidad de ejecución y pago. En los contratos de obra que hayan sido celebrados como resultado de un proceso de licitación o concurso públicos, la interventoría deberá ser contratada con una persona independiente de la entidad contratante y del contratista, quien responderá por los hechos y omisiones que le fueren imputables en los términos previstos en el artículo 53 del presente estatuto. 2o. Contrato de Consultoría Son contratos de consultoría los que celebren las entidades estatales referidos a los estudios necesarios para la ejecución de proyectos de inversión, estudios de diagnóstico, prefactibilidad o factibilidad para programas o proyectos específicos, así como a las asesorías técnicas de coordinación, control y supervisión. Son también contratos de consultoría los que tienen por objeto la interventoría, asesoría, gerencia de obra o de proyectos, dirección, programación y la ejecución de diseños, planos, anteproyectos y proyectos. Ninguna orden del interventor de una obra podrá darse verbalmente. Es obligatorio para el interventor entregar por escrito sus órdenes o sugerencias y ellas deben enmarcarse dentro de los términos del respectivo contrato. - 3. Contrato de prestación de servicios. Son contratos de prestación de servicios los que celebren las entidades estatales para desarrollar actividades relacionadas con la administración o funcionamiento de la entidad. Estos contratos sólo podrán celebrarse con personas naturales o jurídicas cuando dichas actividades no puedan realizarse con personal de planta o requieran conocimientos especializados. Estos contratos no generan en ningún caso relación laboral ni prestaciones sociales. Los contratos a que se refiere este ordinal, se celebrarán por el término estrictamente indispensable. 4o. Contrato de concesión Son contratos de concesión los que celebran las entidades estatales con el objeto de otorgar a una persona llamada concesionario la prestación, operación, explotación, organización o gestión, total o parcial, de un servicio público, o la construcción, explotación o conservación total o parcial, de una obra o bien destinados al servicio o uso público, así como todas aquellas actividades necesarias para la adecuada prestación o funcionamiento de la obra o servicio por cuenta y riesgo del concesionario y bajo la vigilancia y control de la entidad concedente, a cambio de una remuneración que puede consistir en derechos, tarifas, tasas, valorización, o en la participación que se le otorgue en la explotación del bien, o en una suma periódica, única o porcentual y, en general, en cualquier otra modalidad de contraprestación que las partes acuerden. 5o. Encargos Fiduciarios y Fiducia Pública. Las entidades estatales sólo podrán celebrar contratos de fiducia pública, cuando así lo autorice la ley, la Asamblea Departamental o el Concejo Municipal, según el caso. Los encargos fiduciarios que celebren las entidades estatales con las sociedades fiduciarias autorizadas por la Superintendencia Bancaria, tendrán por objeto la administración o el manejo de los recursos vinculados a los contratos que tales entidades celebren. Lo anterior sin perjuicio de lo previsto en el numeral 20 del artículo 25 de esta ley. Los encargos fiduciarios y los contratos de fiducia pública sólo podrán celebrarse por las entidades estatales con estricta sujeción a lo dispuesto en el presente estatuto, únicamente para objetos y con plazos precisamente determinados En ningún caso las entidades públicas fideicomitentes podrán delegar en las sociedades fiduciarias la adjudicación de los contratos que se celebren en desarrollo del encargo o de la fiducia pública, ni pactar su remuneración con cargo a los rendimientos del fideicomiso, salvo que éstos se encuentren presupuestados. La selección de las sociedades fiduciarias a contratar, sea pública o privada, se hará con rigurosa observancia del procedimiento de licitación o concurso previsto en esta ley. No obstante, los excedentes de tesorería de las entidades estatales, se podrán invertir directamente en fondos comunes ordinarios administrados por sociedades fiduciarias, sin necesidad de acudir a un proceso de licitación pública. Los actos y contratos que se realicen en desarrollo de un contrato de fiducia pública o encargo fiduciario cumplirán estrictamente con las normas previstas en este estatuto, así como con las disposiciones fiscales, presupuestales, de interventoría y de control a las cuales esté sujeta la entidad estatal fideicomitente. Sin perjuicio de la inspección y vigilancia que sobre las sociedades fiduciarias corresponde ejercer a la Superintendencia Bancaria y del control posterior que deben realizar la Contraloría General de la República y las Contralorías Departamentales, Distritales y Municipales sobre la administración de los recursos públicos por tales sociedades, las entidades estatales ejercerán un control sobre la actuación de la sociedad fiduciaria en desarrollo de los encargos fiduciarios o contratos de fiducia, de acuerdo con la Constitución Política y las normas vigentes sobre la materia. La fiducia que se autoriza para el sector público en esta ley, nunca implicará transferencia de dominio sobre bienes o recursos estatales, ni constituirá patrimonio autónomo del propio de la respectiva entidad oficial, sin perjuicio de las responsabilidades propias del ordenador del gasto. A la fiducia pública le serán aplicables las normas del Código de Comercio sobre fiducia mercantil, en cuanto sean compatibles con lo dispuesto en esta ley. So pena de nulidad no podrán celebrarse contratos de fiducia o subcontratos en contravención del artículo 355 de la Constitución Política. Si tal evento se diese, la entidad fideicomitente deberá repetir contra la persona, natural o jurídica, adjudicataria del respectivo contrato. PARAGRAFO 1o. Los Contratos que celebren los Establecimientos de Crédito, las compañías de seguros y las demás entidades financieras de carácter estatal, no estarán sujetos a las disposiciones del Estatuto General de Contratación de la Administración Pública y se regirán por las disposiciones legales y reglamentarias aplicables a dichas actividades. En todo caso, su actividad contractual se someterá a lo dispuesto en el artículo 13 de la presente ley PARAGRAFO 2o. derogado

## 9063 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 14

**Categoria:** Pensiones y seguridad social

**Pregunta:** Me pensionaron por un valor mucho menor al que yo calculaba y no me explican el calculo.

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 14. Reajuste de Pensiones. Con el objeto de que las pensiones de vejez o de jubilación, de invalidez y de sustitución o sobrevivientes, en cualquiera de los dos regímenes del sistema general de pensiones, mantengan su poder adquisitivo constante, se reajustarán anualmente de oficio, el 1o. de enero de cada año, según la variación porcentual del Indice de Precios al Consumidor, certificado por el DANE para el año inmediatamente anterior. No obstante, las pensiones cuyo monto mensual sea igual al salario mínimo legal mensual vigente, serán reajustadas de oficio cada vez y con el mismo porcentaje en que se incremente dicho salario por el Gobierno. Parágrafo. El Gobierno nacional podrá establecer mecanismos de cobertura que permitan a las aseguradoras cubrir el riesgo del incremento que podrían tener las pensiones de renta vitalicia inmediata y renta vitalicia diferida de que tratan los artículos 80 y 82 de esta ley cuando el aumento del salario mínimo mensual legal vigente sea superior a la variación porcentual del Índice de Precios al Consumidor certificada por el Departamento Administrativo Nacional de Estadística para el respectivo año. El Gobierno nacional determinará los costos que resulten procedentes en la aplicación de estos mecanismos de cobertura. El Consejo Superior de Política Fiscal (Confis) otorgará aval fiscal para estas coberturas CAPITULO II AFILIACION AL SISTEMA GENERAL DE PENSIONES

## 9063 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 27

**Categoria:** Pensiones y seguridad social

**Pregunta:** Me pensionaron por un valor mucho menor al que yo calculaba y no me explican el calculo.

**Estado:** recuperado=si · partido en 3 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 27. Recursos. El fondo de solidaridad pensional tendrá las siguientes fuentes de recursos: - 1. Subcuenta de solidaridad - a) El cincuenta por ciento (50%) de la cotización adicional del 1% sobre la base de cotización, a cargo de los afiliados al sistema general de pensiones cuya base de cotización sea igual o superior a cuatro (4) salarios mínimos legales mensuales vigentes; - b) Los recursos que aporten las entidades territoriales para planes de extensión de cobertura en sus respectivos territorios, o de agremiaciones o federaciones para sus afiliados; - c) Las donaciones que reciba, los rendimientos financieros de sus recursos, y en general los demás recursos que reciba a cualquier título, y - d) Las multas a que se refieren los artículos 111 y 271 de la Ley 100 de 1993. - 2. Subcuenta de Subsistencia - a) Los afiliados con ingreso igual o superior a 16 salarios mínimos mensuales legales vigentes, tendrán un aporte adicional sobre su ingreso base de cotización, así: de 16 a 17 smlmv de un 0.2%, de 17 a 18 smlmv de un 0.4%, de 18 a 19 smlmv de un 0.6%, de 19 a 20 smlmv de un 0.8% y superiores a 20 smlmv de 1% destinado exclusivamente a la subcuenta de subsistencia del Fondo de Solidaridad Pensional de que trata la presente ley; - b) El cincuenta (50%) de la cotización adicional del 1% sobre la base de cotización, a cargo de los afiliados al sistema general de pensiones cuya base de cotización sea igual o superior a cuatro (4) salarios mínimos legales mensuales vigentes; - c) Los aportes del presupuesto nacional. Estos no podrán ser inferiores a los recaudados anualmente por los conceptos enumerados en los literales a) y b) anteriores, y se liquidarán con base en lo reportado por el fondo en la vigencia del año inmediatamente anterior, actualizados con base en la variación del índice de precios al consumidor, certificado por el DANE; - d) Los pensionados que devenguen una mesada superior a diez (10) salarios mínimos legales mensuales vigentes y hasta veinte (20) contribuirán para el Fondo de Solidaridad Pensional para la subcuenta de subsistencia en un 1%, y los que devenguen más de veinte (20) salarios mínimos contribuirán en un 2% para la misma cuenta. Parágrafo 1º. Para ser beneficiario del subsidio a los aportes, los afiliados al ISS, deberán ser mayores de 55 años y los vinculados a los fondos de pensiones deberán ser mayores de 58, siempre y cuando no tengan un capital suficiente para financiar una pensión mínima. Parágrafo 2º. Cuando quiera que los recursos que se asignan a la subcuenta de solidaridad no sean suficientes para atender los subsidios que hayan sido otorgados a la entrada en vigencia de esta ley, se destinará el porcentaje adicional que sea necesario de la cotización del uno por ciento que deben realizar quienes tengan ingresos iguales o superiores a cuatro (4) salarios mínimos legales mensuales.

## 9063 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 33

**Categoria:** Pensiones y seguridad social

**Pregunta:** Me pensionaron por un valor mucho menor al que yo calculaba y no me explican el calculo.

**Estado:** recuperado=si · partido en 4 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 33. Requisitos para Obtener la Pensión de Vejez. Para tener el derecho a la Pensión de Vejez, el afiliado deberá reunir las siguientes condiciones: - 1. Haber cumplido cincuenta y cinco (55) años de edad si es mujer o sesenta (60) años si es hombre. A partir del 1º de enero del año 2014 la edad se incrementará a cincuenta y siete (57) años de edad para la mujer, y sesenta y dos (62) años para el hombre. - 2. Haber cotizado un mínimo de mil (1000) semanas en cualquier tiempo. A partir del 1º de enero del año 2005 el número de semanas se incrementará en 50 y a partir del 1º de enero de 2006 se incrementará en 25 cada año hasta llegar a 1.300 semanas en el año 2015. Parágrafo 1º. Para efectos del cómputo de las semanas a que se refiere el presente artículo, se tendrá en cuenta: - a) El número de semanas cotizadas en cualquiera de los dos regímenes del sistema general de pensiones; - b) El tiempo de servicio como servidores públicos remunerados, incluyendo los tiempos servidos en regímenes exceptuados; - c) El tiempo de servicio como trabajadores vinculados con empleadores que antes de la vigencia de la Ley 100 de 1993 tenían a su cargo el reconocimiento y pago de la pensión, siempre y cuando la vinculación laboral se encontrara vigente o se haya iniciado con posterioridad a la vigencia de la Ley 100 de 1993. - d) El tiempo de servicios como trabajadores vinculados con aquellos empleadores que por omisión no hubieren afiliado al trabajador. - e) El número de semanas cotizadas a cajas previsionales del sector privado que antes de la Ley 100 de 1993 tuviesen a su cargo el reconocimiento y pago de la pensión. En los casos previstos en los literales b), c), d) y e), el cómputo será procedente siempre y cuando el empleador o la caja, según el caso, trasladen, con base en el cálculo actuarial, la suma correspondiente del trabajador que se afilie, a satisfacción de la entidad administradora, el cual estará representado por un bono o título pensional. Los fondos encargados reconocerán la pensión en un tiempo no superior a cuatro (4) meses después de radicada la solicitud por el peticionario, con la correspondiente documentación que acredite su derecho. Los Fondos no podrán aducir que las diferentes cajas no les han expedido el bono pensional o la cuota parte. Parágrafo 2º. Para los efectos de las disposiciones contenidas en la presente ley, se entiende por semana cotizada el periodo de siete (7) días calendario. La facturación y el cobro de los aportes se harán sobre el número de días cotizados en cada período. Parágrafo 3º. Se considera justa causa para dar por terminado el contrato de trabajo o la relación legal o reglamentaria, que el trabajador del sector privado o servidor público cumpla con los requisitos establecidos en este artículo para tener derecho a la pensión. El empleador podrá dar por terminado el contrato de trabajo o la relación legal o reglamentaria, cuando sea reconocida o notificada la pensión por parte de las administradoras del sistema general de pensiones. Transcurridos treinta (30) días después de que el trabajador o servidor público cumpla con los requisitos establecidos en este artículo para tener derecho a la pensión, si este no la solicita, el empleador podrá solicitar el reconocimiento de la misma en nombre de aquel. Lo dispuesto en este artículo rige para todos los trabajadores o servidores públicos afiliados al sistema general de pensiones. Parágrafo 4º. Se exceptúan de los requisitos establecidos en los numerales 1 y 2 del presente artículo, las personas que padezcan una deficiencia física, síquica o sensorial del 50% o más, que cumplan 55 años de edad y que hayan cotizado en forma continua o discontinua 1000 o más semanas al régimen de seguridad social establecido en la Ley 100 de 1993. La madre trabajadora cuyo hijomenor de 18 años padezca invalidez física o mental, debidamente calificada y hasta tanto permanezca en este estado y continúe como dependiente de la madre, tendrá derecho a recibir la pensión especial de vejez a cualquier edad, siempre que haya cotizado al Sistema General de Pensiones cuando menos el mínimo de semanas exigido en el régimen de prima media para acceder a la pensión de vejez. Este beneficio se suspenderá si la trabajadora se reincorpora a la fuerza laboral. Si la madre ha fallecido y el padre tiene la patria potestad del menor inválido, podrá pensionarse con los requisitos y en las condiciones establecidas en este artículo.

## 9063 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 35

**Categoria:** Pensiones y seguridad social

**Pregunta:** Me pensionaron por un valor mucho menor al que yo calculaba y no me explican el calculo.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 35. Pensión Mínima de Vejez o jubilación. El monto mensual de la pensión mínima de vejez o jubilación no podrá ser inferior al valor del salario mínimo legal mensual vigente. PARAGRAFO. Las pensiones de jubilación reconocidas con posterioridad a la vigencia de la Ley 4º. de 1992 no estarán sujetas al limite establecido por el artículo 2º. de la Ley 71 de 1988, que por esta Ley se modifica, salvo en los regímenes e instituciones excepcionadas en el artículo 279 de esta Ley.

## 9063 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 117

**Categoria:** Pensiones y seguridad social

**Pregunta:** Me pensionaron por un valor mucho menor al que yo calculaba y no me explican el calculo.

**Estado:** recuperado=si · partido en 4 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTICULO 117. Valor de los Bonos Pensionales. Para determinar el valor de los bonos, se establecerá una pensión de vejez de referencia para cada afiliado, que se calculará así: - a) Se calcula el salario que el afiliado tendría a los sesenta (60) años si es mujer o sesenta y dos (62) si es hombre, como el resultado de multiplicar la base de cotización del afiliado a 30 de junio de 1992, o en su defecto, el último salario devengado antes de dicha fecha si para la misma se encontrase cesante, actualizado a la fecha de su ingreso al Sistema según la variación porcentual del índice de precios al consumidor del DANE, por la relación que exista entre el salario medio nacional a los sesenta (60) años si es mujer o sesenta y dos (62) si es hombre, y el salario medio nacional a la edad que hubiere tenido el afiliado en dicha fecha. Dichos salarios medios nacionales serán establecidos por el DANE: - b) El resultado obtenido en el literal anterior, se multiplica por el porcentaje que resulte de sumar los siguientes porcentajes: Cuarenta y cinco por ciento, más un 3% por cada año que exceda de los primeros 10 años de cotización, empleo o servicio público, más otro 3% por cada año que faltaré para alcanzar la edad de sesenta (60) años si es mujer o sesenta y dos (62) si es hombre, contado desde el momento de su vinculación al sistema. La pensión de referencia así calculada, no podrá exceder el 90 % del salario que tendría el afiliado al momento de tener acceso a la pensión, ni de 15 salarios mínimos legales mensuales. Una vez determinada la pensión de referencia, los bonos pensionales se expedirán por un valor equivalente al que el afiliado hubiera debido acumular en una cuenta de ahorro, durante el período que haya efectuado cotizaciones al Instituto de Seguros Sociales, o haya sido servidor publico o haya estado empleado en una empresa que deba asumir el pago de pensiones, hasta el momento de ingreso al sistema de ahorro, para que a ese ritmo de acumulación, hubiera completado el capital necesario para financiar una pensión de vejez y para sobrevivientes, a los 62 años si son hombres y 60 años si son mujeres por un monto igual a la pensión de referencia. En todo caso, el valor nominal del bono no podrá ser inferior a las sumas aportadas obligatoriamente para la futura pensión con anterioridad a la fecha en la cual se afilie al régimen de Ahorro Individual con Solidaridad. El Gobierno establecerá la metodología, procedimiento y plazos para la expedición de los bonos pensionales. PARAGRAFO 1º. El porcentaje del 90% a que se refiere el inciso quinto, será del 75% en el caso de las empresas que hayan asumido el reconocimiento de pensiones a favor de sus trabajadores. PARAGRAFO 2º. Cuando el bono a emitir corresponda a un afiliado que no provenga inmediatamente del Instituto de Seguros Sociales, ni de caja o fondo de previsión del sector público, ni de empresa que tuviese a su cargo exclusivo el pago de pensiones de sus trabajadores, el cálculo del salario que tendría a los 62 años si son hombres y 60 años si son mujeres, parte de la última base de cotización sobre la cual haya cotizado o del último salario que haya devengado en una de dichas entidades, actualizado a la fecha de ingreso al Sistema, según la variación porcentual del índice de precios al consumidor del DANE. PARAGRAFO 3º. Para las personas que ingresen por primera vez a la fuerza laboral con posterioridad al 30 de junio de 1992, el bono pensional se calculará como el valor de las cotizaciones efectuadas más los rendimientos obtenidos hasta la fecha de traslado.

## 9066 · Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana) · articulo 79

**Categoria:** Licencias urbanisticas

**Pregunta:** Mi vecino amplio su casa invadiendo el antejardin y la alcaldia no responde mis quejas.

**Estado:** recuperado=si · partido en 2 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> ARTÍCULO 79. Ejercicio de las acciones de protección de los bienes inmuebles. Para el ejercicio de la acción de Policía en el caso de la perturbación de los derechos de que trata este título, las siguientes personas, podrán instaurar querella ante el inspector de Policía, mediante el procedimiento único estipulado en este Código: 1. El titular de la posesión o la mera tenencia de los inmuebles particulares o de las servidumbres. 2. Las entidades de derecho público. 3. Los apoderados o representantes legales de los antes mencionados. PARÁGRAFO 1. En el procedimiento de perturbación por ocupación de hecho, se ordenará el desalojo del ocupante de hecho si fuere necesario o que las cosas vuelvan al estado que antes tenía. El desalojo se deberá efectuar dentro de las veinticuatro (24) horas siguientes a la orden. PARÁGRAFO 2. En estos procedimientos se deberá comunicar al propietario inscrito la iniciación de ellos sin perjuicio de que se lleve a cabo la diligencia prevista. PARÁGRAFO 3. La Superintendencia de Notariado y Registro, el Instituto Agustín Codazzi y las administraciones municipales, deberán suministrar la información solicitada, de manera inmediata y gratuita a las autoridades de Policía. El recurso de apelación se concederá en efecto devolutivo. PARÁGRAFO 4. Cuando por caso fortuito o fuerza mayor demostrados, excepcionalmente deba suspenderse la audiencia pública, la autoridad competente decretará el statu quo sobre los bienes objeto de la misma, dejando constancia y registro documental, fijando fecha y hora para su reanudación.

## 9068 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 159

**Categoria:** Procedimiento civil - recursos

**Pregunta:** Perdi en primera instancia y mi abogado no apelo dentro del tiempo.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 159. Causales de interrupción. El proceso o la actuación posterior a la sentencia se interrumpirá: - 1. Por muerte, enfermedad grave o privación de la libertad de la parte que no haya estado actuando por conducto de apoderado judicial, representante o curador ad lítem. - 2. Por muerte, enfermedad grave o privación de la libertad del apoderado judicial de alguna de las partes, o por inhabilidad, exclusión o suspensión en el ejercicio de la profesión de abogado. Cuando la parte tenga varios apoderados para el mismo proceso, la interrupción solo se producirá si el motivo afecta a todos los apoderados constituidos. - 3. Por muerte, enfermedad grave o privación de la libertad del representante o curador ad lítem que esté actuando en el proceso y que carezca de apoderado judicial. La interrupción se producirá a partir del hecho que la origine, pero si este sucede estando el expediente al despacho, surtirá efectos a partir de la notificación de la providencia que se pronuncie seguidamente. Durante la interrupción no correrán los términos y no podrá ejecutarse ningún acto procesal, con excepción de las medidas urgentes y de aseguramiento.

## 9068 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 321

**Categoria:** Procedimiento civil - recursos

**Pregunta:** Perdi en primera instancia y mi abogado no apelo dentro del tiempo.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 321. Procedencia. Son apelables las sentencias de primera instancia, salvo las que se dicten en equidad. También son apelables los siguientes autos proferidos en primera instancia: - 1. El que rechace la demanda, su reforma o la contestación a cualquiera de ellas. - 2. El que niegue la intervención de sucesores procesales o de terceros. - 3. El que niegue el decreto o la práctica de pruebas. - 4. El que niegue total o parcialmente el mandamiento de pago y el que rechace de plano las excepciones de mérito en el proceso ejecutivo. - 5. El que rechace de plano un incidente y el que lo resuelva. - 6. El que niegue el trámite de una nulidad procesal y el que la resuelva. - 7. El que por cualquier causa le ponga fin al proceso. - 8. El que resuelva sobre una medida cautelar, o fije el monto de la caución para decretarla, impedirla o levantarla. - 9. El que resuelva sobre la oposición a la entrega de bienes, y el que la rechace de plano. - 10. Los demás expresamente señalados en este código.

## 9068 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 352

**Categoria:** Procedimiento civil - recursos

**Pregunta:** Perdi en primera instancia y mi abogado no apelo dentro del tiempo.

**Estado:** recuperado=si · partido en 1 chunk(s)

**Lo que hay que decidir:** El sistema trajo este articulo, que NO esta etiquetado, y el caso figura como fallo. ¿Tambien responde la consulta? Si si, el fallo es falso y hay que agregarlo al gold.

**Texto del articulo:**

> Artículo 352. Procedencia. Cuando el juez de primera instancia deniegue el recurso de apelación, el recurrente podrá interponer el de queja para que el superior lo conceda si fuere procedente. El mismo recurso procede cuando se deniegue el de casación.


---

# Clase B -- etiquetas de casos fallidos

82 filas en 24 casos.

## 9004 · Constitucion Politica de 1991 · articulo 49

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS me autorizo una cirugia pero llevo 3 meses esperando la cita sin que me den fecha, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 49. La atención de la salud y el saneamiento ambiental son servicios públicos a cargo del Estado. Se garantiza a todas las personas el acceso a los servicios de promoción, protección y recuperación de la salud. Corresponde al Estado organizar, dirigir y reglamentar la prestación de servicios de salud a los habitantes y de saneamiento ambiental conforme a los principios de eficiencia, universalidad y solidaridad. También, establecer las políticas para la prestación de servicios de salud por entidades privadas, y ejercer su vigilancia y control. Así mismo, establecer las competencias de la Nación, las entidades territoriales y los particulares y determinar los aportes a su cargo en los términos y condiciones señalados en la ley. Los servicios de salud se organizarán en forma descentralizada, por niveles de atención y con participación de la comunidad. La ley señalará los términos en los cuales la atención básica para todos los habitantes será gratuita y obligatoria. Toda persona tiene el deber de procurar el cuidado integral de su salud y la de su comunidad.

## 9004 · Constitucion Politica de 1991 · articulo 86

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS me autorizo una cirugia pero llevo 3 meses esperando la cita sin que me den fecha, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 86. Toda persona tendrá acción de tutela para reclamar ante los jueces, en todo momento y lugar, mediante un procedimiento preferente y sumario, por sí misma o por quien actúe a su nombre, la protección inmediata de sus derechos constitucionales fundamentales, cuando quiera que éstos resulten vulnerados o amenazados por la acción o la omisión de cualquier autoridad pública. La protección consistirá en una orden para que aquél respecto de quien se solicita la tutela, actúe o se abstenga de hacerlo. El fallo, que será de inmediato cumplimiento, podrá impugnarse ante el juez competente y, en todo caso, éste lo remitirá a la Corte Constitucional para su eventual revisión. Esta acción sólo procederá cuando el afectado no disponga de otro medio de defensa judicial, salvo que aquella se utilice como mecanismo transitorio para evitar un perjuicio irremediable. En ningún caso podrán transcurrir más de diez días entre la solicitud de tutela y su resolución. La ley establecerá los casos en los que la acción de tutela procede Contra particulares encargados de la prestación de un servicio público o cuya conducta afecte grave y directamente el interés colectivo, o respecto de quienes el solicitante se halle en estado de subordinación o indefensión.

## 9004 · Ley 1437 de 2011 (CPACA) · articulo 13

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS me autorizo una cirugia pero llevo 3 meses esperando la cita sin que me den fecha, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 13.Objeto y modalidades del derecho de petición ante autoridades. Toda persona tiene derecho a presentar peticiones respetuosas a las autoridades, en los términos señalados en este código, por motivos de interés general o particular, y a obtener pronta resolución completa y de fondo sobre la misma. Toda actuación que inicie cualquier persona ante las autoridades implica el ejercicio del derecho de petición consagrado en el artículo 23 de la Constitución Política, sin que sea necesario invocarlo. Mediante él, entre otras actuaciones, se podrá solicitar: el reconocimiento de un derecho, la intervención de una entidad o funcionario, la resolución de una situación jurídica, la prestación de un servicio, requerir información, consultar, examinar y requerir copias de documentos, formular consultas, quejas, denuncias y reclamos e interponer recursos. El ejercicio del derecho de petición es gratuito y puede realizarse sin necesidad de representación a través de abogado, o de persona mayor cuando se trate de menores en relación a las entidades dedicadas a su protección o formación.

## 9004 · Ley 1437 de 2011 (CPACA) · articulo 14

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS me autorizo una cirugia pero llevo 3 meses esperando la cita sin que me den fecha, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 14.Términos para resolver las distintas modalidades de peticiones. Salvo norma legal especial y so pena de sanción disciplinaria, toda petición deberá resolverse dentro de los quince (15) días siguientes a su recepción. Estará sometida a término especial la resolución de las siguientes peticiones: 1.Las peticiones de documentos y de información deberán resolverse dentro de los diez (10) días siguientes a su recepción. Si en ese lapso no se ha dado respuesta al peticionario, se entenderá, para todos los efectos legales, que la respectiva solicitud ha sido aceptada y, por consiguiente, la administración ya no podrá negar la entrega de dichos documentos al peticionario, y como consecuencia las copias se entregarán dentro de los tres (3) días siguientes. - 2. Las peticiones mediante las cuales se eleva una consulta a las autoridades en relación con las materias a su cargo deberán resolverse dentro de los treinta (30) días siguientes a su recepción. Parágrafo. Cuando excepcionalmente no fuere posible resolver la petición en los plazos aquí señalados, la autoridad debe informar esta circunstancia al interesado, antes del vencimiento del término señalado en la ley expresando los motivos de la demora y señalando a la vez el plazo razonable en que se resolverá o dará respuesta, que no podrá exceder del doble del inicialmente previsto.

## 9004 · Ley 1751 de 2015 (Ley Estatutaria de Salud) · articulo 2

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS me autorizo una cirugia pero llevo 3 meses esperando la cita sin que me den fecha, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 2°. Naturaleza y contenido del derecho fundamental a la salud. El derecho fundamental a la salud es autónomo e irrenunciable en lo individual y en lo colectivo. Comprende el acceso a los servicios de salud de manera oportuna, eficaz y con calidad para la preservación, el mejoramiento y la promoción de la salud. El Estado adoptará políticas para asegurar la igualdad de trato y oportunidades en el acceso a las actividades de promoción, prevención, diagnóstico, tratamiento, rehabilitación y paliación para todas las personas. De conformidad con el artículo 49 de la Constitución Política, su prestación como servicio público esencial obligatorio, se ejecuta bajo la indelegable dirección, supervisión, organización, regulación, coordinación y control del Estado.

## 9004 · Ley 1751 de 2015 (Ley Estatutaria de Salud) · articulo 6

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS me autorizo una cirugia pero llevo 3 meses esperando la cita sin que me den fecha, ¿que hago?

**Estado:** recuperado=no · partido en 5 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 6°. Elementos y principios del derecho fundamental a la salud. El derecho fundamental a la salud incluye los siguientes elementos esenciales e interrelacionados: a) Disponibilidad. El Estado deberá garantizar la existencia de servicios y tecnologías e instituciones de salud, así como de programas de salud y personal médico y profesional competente; b) Aceptabilidad. Los diferentes agentes del sistema deberán ser respetuosos de la ética médica así como de las diversas culturas de las personas, minorías étnicas, pueblos y comunidades, respetando sus particularidades socioculturales y cosmovisión de la salud, permitiendo su participación en las decisiones del sistema de salud que le afecten, de conformidad con el artículo 12 de la presente ley y responder adecuadamente a las necesidades de salud relacionadas con el género y el ciclo de vida. Los establecimientos deberán prestar los servicios para mejorar el estado de salud de las personas dentro del respeto a la confidencialidad; c) Accesibilidad. Los servicios y tecnologías de salud deben ser accesibles a todos, en condiciones de igualdad, dentro del respeto a las especificidades de los diversos grupos vulnerables y al pluralismo cultural. La accesibilidad comprende la no discriminación, la accesibilidad física, la asequibilidad económica y el acceso a la información; d) Calidad e idoneidad profesional. Los establecimientos, servicios y tecnologías de salud deberán estar centrados en el usuario, ser apropiados desde el punto de vista médico y técnico y responder a estándares de calidad aceptados por las comunidades científicas. Ello requiere, entre otros, personal de la salud adecuadamente competente, enriquecida con educación continua e investigación científica y una evaluación oportuna de la calidad de los servicios y tecnologías ofrecidos. Así mismo, el derecho fundamental a la salud comporta los siguientes principios: a) Universalidad. Los residentes en el territorio colombiano gozarán efectivamente del derecho fundamental a la salud en todas las etapas de la vida; b) Pro homine. Las autoridades y demás actores del sistema de salud, adoptarán la interpretación de las normas vigentes que sea más favorable a la protección del derecho fundamental a la salud de las personas; c) Equidad. El Estado debe adoptar políticas públicas dirigidas específicamente al mejoramiento de la salud de personas de escasos recursos, de los grupos vulnerables y de los sujetos de especial protección; d) Continuidad. Las personas tienen derecho a recibir los servicios de salud de manera continua. Una vez la provisión de un servicio ha sido iniciada, este no podrá ser interrumpido por razones administrativas o económicas; e) Oportunidad. La prestación de los servicios y tecnologías de salud deben proveerse sin dilaciones; f) Prevalencia de derechos. El Estado debe implementar medidas concretas y específicas para garantizar la atención integral a niñas, niños y adolescentes. En cumplimiento de sus derechos prevalentes establecidos por la Constitución Política. Dichas medidas se formularán por ciclos vitales: prenatal hasta seis (6) años, de los (7) a los catorce (14) años, y de los quince (15) a los dieciocho (18) años; g) Progresividad del derecho. El Estado promoverá la correspondiente ampliación gradual y continua del acceso a los servicios y tecnologías de salud, la mejora en su prestación, la ampliación de capacidad instalada del sistema de salud y el mejoramiento del talento humano, así como la reducción gradual y continua de barreras culturales, económicas, geográficas, administrativas y tecnológicas que impidan el goce efectivo del derecho fundamental a la salud; h) Libre elección. Las personas tienen la libertad de elegir sus entidades de salud dentro de la oferta disponible según las normas de habilitación; i) Sostenibilidad. El Estado dispondrá, por los medios que la ley estime apropiados, los recursos necesarios y suficientes para asegurar progresivamente el goce efectivo del derecho fundamental a la salud, de conformidad con las normas constitucionales de sostenibilidad fiscal; j) Solidaridad. El sistema está basado en el mutuo apoyo entre las personas, generaciones, los sectores económicos, las regiones y las comunidades; k) Eficiencia. El sistema de salud debe procurar por la mejor utilización social y económica de los recursos, servicios y tecnologías disponibles para garantizar el derecho a la salud de toda la población; l) Interculturalidad. Es el respeto por las diferencias culturales existentes en el país y en el ámbito global, así como el esfuerzo deliberado por construir mecanismos que integren tales diferencias en la salud, en las condiciones de vida y en los servicios de atención integral de las enfermedades, a partir del reconocimiento de los saberes, prácticas y medios tradicionales, alternativos y complementarios para la recuperación de la salud en el ámbito global; m) Protección a los pueblos indígenas. Para los pueblos indígenas el Estado reconoce y garantiza el derecho fundamental a la salud integral, entendida según sus propias cosmovisiones y conceptos, que se desarrolla en el Sistema Indígena de Salud Propio e Intercultural (SISPI); n) Protección pueblos y comunidades indígenas, ROM y negras, afrocolombianas, raizales y palanqueras. Para los pueblos y comunidades indígenas, ROM y negras, afrocolombianas, raizales y palanqueras, se garantizará el derecho a la salud como fundamental y se aplicará de manera concertada con ellos, respetando sus costumbres. Parágrafo. Los principios enunciados en este artículo se deberán interpretar de manera armónica sin privilegiar alguno de ellos sobre los demás. Lo anterior no obsta para que sean adoptadas acciones afirmativas en beneficio de sujetos de especial protección constitucional como la promoción del interés superior de las niñas, niños y mujeres en estado de embarazo y personas de escasos recursos, grupos vulnerables y sujetos de especial protección.

## 9004 · Decreto 2591 de 1991 (Reglamentacion de la accion de tutela) · articulo 1

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS me autorizo una cirugia pero llevo 3 meses esperando la cita sin que me den fecha, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 1º Objeto. Toda persona tendrá acción de tutela para reclamar ante los jueces, en todo momento y lugar, mediante un procedimiento preferente y sumario, por sí misma o por quien actúe a su nombre, la protección inmediata de sus derechos constitucionales fundamentales, cuando quiera que éstos resulten vulnerados o amenazados por la acción o la omisión de cualquier autoridad pública o de los particulares en los casos que señala este Decreto. Todos los días y horas son hábiles para interponer la acción de tutela. La acción de tutela procederá aún bajo los estados de excepción. Cuando la medida excepcional se refiera a derechos, la tutela se podrá ejercer por los menos para defender su contenido esencial, sin perjuicio de las limitaciones que la Constitución autorice y de lo que establezca la correspondiente ley estatutaria de los estados de excepción.

## 9007 · Ley 84 de 1873 (Codigo Civil) · articulo 2231

**Categoria:** Prestamos informales y usura

**Pregunta:** Un conocido me presto dinero y me esta cobrando un interes que me parece exagerado, ¿como se si es usura?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Art. 2231. El interés convencional que exceda de una mitad al que se probare haber sido interés corriente al tiempo de la convención, será reducido por el juez a dicho interés corriente, si lo solicitare el deudor.

## 9007 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 884

**Categoria:** Prestamos informales y usura

**Pregunta:** Un conocido me presto dinero y me esta cobrando un interes que me parece exagerado, ¿como se si es usura?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 884. LIMITE DE INTERESES Y SANCIÓN POR EXCESO. Cuando en los negocios mercantiles haya de pagarse réditos de un capital, sin que se especifique por convenio el interés, éste será el bancario corriente; si las partes no han estipulado el interés moratorio, será equivalente a una y media veces del bancario corriente y en cuanto sobrepase cualquiera de estos montos el acreedor perderá todos los intereses, sin perjuicio de lo dispuesto en el artículo 72 de la Ley 45 de 1990. Se probará el interés bancario corriente con certificado expedido por la Superintendencia Bancaria.» Parágrafo. El inciso primero del artículo 1080 del Código de Comercio quedará así: El asegurador estará obligado a efectuar el pago del siniestro dentro del mes siguiente a la fecha en que el asegurado o beneficiario acredite, aún extrajudicialmente, su derecho ante el asegurador de acuerdo con el artículo 1077. Vencido este plazo, el asegurador reconocerá y pagará al asegurado o beneficiario, además de la obligación a su cargo y sobre el importe de ella, un interés moratorio igual al certificado como bancario corriente por la Superintendencia Bancaria aumentado en la mitad. El contrato de reaseguro no varía el contrato de seguro celebrado entre tomador y asegurador, y la oportunidad en el pago de éste, en caso de siniestro, no podrá diferirse a pretexto del reaseguro.

## 9007 · Ley 599 de 2000 (Codigo Penal) · articulo 305

**Categoria:** Prestamos informales y usura

**Pregunta:** Un conocido me presto dinero y me esta cobrando un interes que me parece exagerado, ¿como se si es usura?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 305. Usura. El que reciba o cobre, directa o indirectamente, a cambio de préstamo de dinero o por concepto de venta de bienes o servicios a plazo, utilidad o ventaja que exceda en la mitad del interés bancario corriente que para el período correspondiente estén cobrando los bancos, según certificación de la Superintendencia Bancaria, cualquiera sea la forma utilizada para hacer constar la operación, ocultarla o disimularla, incurrirá en prisión de treinta y dos (32) a noventa (90) meses y multa de sesenta y seis punto sesenta y seis (66.66) a trescientos (300) salarios mínimos legales mensuales vigentes. El que compre cheque, sueldo, salario o prestación social en los términos y condiciones previstos en este artículo, incurrirá en prisión de cuarenta y ocho (48) a ciento veintiséis (126) meses y multa de ciento treinta y tres punto treinta y tres (133.33) a seiscientos (600) salarios mínimos legales mensuales vigentes. Cuando la utilidad o ventaja triplique el interés bancario corriente que para el período correspondiente estén cobrando los bancos, según certificación de la Superintendencia Financiera o quien haga sus veces, la pena se aumentará de la mitad a las tres cuartas partes En caso de que cualquiera de las conductas a que se refiere el inciso 1º de este artículo se efectúe utilizando la figura de la venta con Pacto de Retroventa o del mecanismo de Cobros Periódicos que se defina en el reglamento, se aumentará la pena de cuarenta y ocho (48) a ciento veintiséis meses (126) y multa de ciento treinta y tres punto treinta y tres (133.33) a seiscientos (600) salarios mínimos legales mensuales vigentes.

## 9009 · Constitucion Politica de 1991 · articulo 74

**Categoria:** Acceso a informacion publica

**Pregunta:** Le pedi a la alcaldia informacion sobre un contrato publico y me dijeron que es confidencial, ¿pueden negarse asi como asi?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 74. Todas las personas tienen derecho a acceder a los documentos públicos salvo los casos que establezca la ley. El secreto profesional es inviolable.

## 9009 · Ley 1437 de 2011 (CPACA) · articulo 24

**Categoria:** Acceso a informacion publica

**Pregunta:** Le pedi a la alcaldia informacion sobre un contrato publico y me dijeron que es confidencial, ¿pueden negarse asi como asi?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 24. Informaciones y documentos reservados. Solo tendrán carácter reservado las informaciones y documentos expresamente sometidos a reserva por la Constitución Política o la ley, y en especial: - 1. Los relacionados con la defensa o seguridad nacionales. - 2. Las instrucciones en materia diplomática o sobre negociaciones reservadas. - 3. Los que involucren derechos a la privacidad e intimidad de las personas, incluidas en las hojas de vida, la historia laboral y los expedientes pensionales y demás registros de personal que obren en los archivos de las instituciones públicas o privadas, así como la historia clínica. - 4. Los relativos a las condiciones financieras de las operaciones de crédito público y tesorería que realice la nación, así como a los estudios técnicos de valoración de los activos de la nación. Estos documentos e informaciones estarán sometidos a reserva por un término de seis (6) meses contados a partir de la realización de la respectiva operación. S. Los datos referentes a la información financiera y comercial, en los términos de la Ley Estatutaria 1266 de 2008. - 6. Los protegidos por el secreto comercial o industrial, así como los planes estratégicos de las empresas públicas de servicios públicos. - 7. Los amparados por el secreto profesional. - 8. Los datos genéticos humanos. Parágrafo. Para efecto de la solicitud de información de carácter reservado, enunciada en los numerales 3, 5, 6 y 7 solo podrá ser solicitada por el titular de la información, por sus apoderados o por personas autorizadas con facultad expresa para acceder a esa información.

## 9009 · Ley 1437 de 2011 (CPACA) · articulo 25

**Categoria:** Acceso a informacion publica

**Pregunta:** Le pedi a la alcaldia informacion sobre un contrato publico y me dijeron que es confidencial, ¿pueden negarse asi como asi?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 25. Rechazo de las peticiones de información por motivo de reserva. Toda decisión que rechace la petición de informaciones o documentos será motivada, indicará en forma precisa las disposiciones legales que impiden la entrega de información o documentos pertinentes y deberá notificarse al peticionario. Contra la decisión que rechace la petición de informaciones o documentos por motivos de reserva legal, no procede recurso alguno, salvo lo previsto en el artículo siguiente. La restricción por reserva legal no se extenderá a otras piezas del respectivo expediente o actuación que no estén cubiertas por ella.

## 9009 · Ley 1712 de 2014 (Ley de Transparencia) · articulo 18

**Categoria:** Acceso a informacion publica

**Pregunta:** Le pedi a la alcaldia informacion sobre un contrato publico y me dijeron que es confidencial, ¿pueden negarse asi como asi?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 18. Información exceptuada por daño de derechos a personas naturales o jurídicas. Es toda aquella información pública clasificada, cuyo acceso podrá ser rechazado o denegado de manera motivada y por escrito, siempre que el acceso pudiere causar un daño a los siguientes derechos: - a) El derecho de toda persona a la intimidad, bajo las limitaciones propias que impone la condición de servidor público, en concordancia con lo estipulado por el artículo 24 de la Ley 1437 de 2011 - b) El derecho de toda persona a la vida, la salud o la seguridad. - c) Los secretos comerciales, industriales y profesionales. Parágrafo. Estas excepciones tienen una duración ilimitada y no deberán aplicarse cuando la persona natural o jurídica ha consentido en la revelación de sus datos personales o privados o bien cuando es claro que la información fue entregada como parte de aquella información que debe estar bajo el régimen de publicidad aplicable.

## 9009 · Ley 1712 de 2014 (Ley de Transparencia) · articulo 19

**Categoria:** Acceso a informacion publica

**Pregunta:** Le pedi a la alcaldia informacion sobre un contrato publico y me dijeron que es confidencial, ¿pueden negarse asi como asi?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 19.Información exceptuada por daño a los intereses públicos. Es toda aquella información pública reservada, cuyo acceso podrá ser rechazado o denegado de manera motivada y por escrito en las siguientes circunstancias, siempre que dicho acceso estuviere expresamente prohibido por una norma legal o constitucional: - a) La defensa y seguridad nacional; - b) La seguridad pública; - c) Las relaciones internacionales; - d) La prevención, investigación y persecución de los delitos y las faltas disciplinarias, mientras que no se haga efectiva la medida de aseguramiento o se formule pliego de cargos, según el caso; - e) El debido proceso y la igualdad de las partes en los procesos judiciales; - f) La administración efectiva de la justicia; - g) Los derechos de la infancia y la adolescencia; - h) La estabilidad macroeconómica y financiera del país; - i) La salud pública. Parágrafo. Se exceptúan también los documentos que contengan las opiniones o puntos de vista que formen parte del proceso deliberativo de los servidores públicos.

## 9009 · Ley 1712 de 2014 (Ley de Transparencia) · articulo 28

**Categoria:** Acceso a informacion publica

**Pregunta:** Le pedi a la alcaldia informacion sobre un contrato publico y me dijeron que es confidencial, ¿pueden negarse asi como asi?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 28.Carga de la prueba. Le corresponde al sujeto obligado aportar las razones y pruebas que fundamenten y evidencien que la información solicitada debe permanecer reservada o confidencial. En particular, el sujeto obligado debe demostrar que la información debe relacionarse con un objetivo legítimo establecido legal o constitucionalmente. Además, deberá establecer si se trata de una excepción contenida en los artículos 18 y 19 de esta ley y si la revelación de la información causaría un daño presente, probable y específico que excede el interés público que representa el acceso a la información.

## 9010 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 90

**Categoria:** Conciliacion prejudicial

**Pregunta:** Quiero demandar a mi ex-socio de negocio por un dinero que me debe, ¿tengo que hacer algo antes de ir directo a la demanda?

**Estado:** recuperado=no · partido en 3 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 90. Admisión, inadmisión y rechazo de la demanda. El juez admitirá la demanda que reúna los requisitos de ley, y le dará el trámite que legalmente le corresponda aunque el demandante haya indicado una vía procesal inadecuada. En la misma providencia el juez deberá integrar el litisconsorcio necesario y ordenarle al demandado que aporte, durante el traslado de la demanda, los documentos que estén en su poder y que hayan sido solicitados por el demandante. El juez rechazará la demanda cuando carezca de jurisdicción o de competencia o cuando esté vencido el término de caducidad para instaurarla. En los dos primeros casos ordenará enviarla con sus anexos al que considere competente; en el último, ordenará devolver los anexos sin necesidad de desglose. Mediante auto no susceptible de recursos el juez declarará inadmisible la demanda solo en los siguientes casos: - 1. Cuando no reúna los requisitos formales. - 2. Cuando no se acompañen los anexos ordenados por la ley. - 3. Cuando las pretensiones acumuladas no reúnan los requisitos legales. - 4. Cuando el demandante sea incapaz y no actúe por conducto de su representante. - 5. Cuando quien formule la demanda carezca de derecho de postulación para adelantar el respectivo proceso. - 6. Cuando no contenga el juramento estimatorio, siendo necesario. - 7. Cuando no se acredite que se agotó la conciliación prejudicial como requisito de procedibilidad. En estos casos el juez señalará con precisión los defectos de que adolezca la demanda, para que el demandante los subsane en el término de cinco (5) días, so pena de rechazo. Vencido el término para subsanarla el juez decidirá si la admite o la rechaza. Los recursos contra el auto que rechace la demanda comprenderán el que negó su admisión. La apelación se concederá en el efecto suspensivo y se resolverá de plano. En todo caso, dentro de los treinta (30) días siguientes a la fecha de la presentación de la demanda, deberá notificarse al demandante o ejecutante el auto admisorio o el mandamiento de pago, según fuere el caso, o el auto que rechace la demanda. Si vencido dicho término no ha sido notificado el auto respectivo, el término señalado en el artículo 121 para efectos de la pérdida de competencia se computará desde el día siguiente a la fecha de presentación de la demanda. Las demandas que sean rechazadas no se tendrán en cuenta como ingresos al juzgado, ni como egresos para efectos de la calificación de desempeño del juez. Semanalmente el juez remitirá a la oficina de reparto una relación de las demandas rechazadas, para su respectiva compensación en el reparto siguiente. Parágrafo primero. La existencia de pacto arbitral no da lugar a inadmisión o rechazo de la demanda, pero provocará la terminación del proceso cuando se declare probada la excepción previa respectiva. Parágrafo segundo. Cuando se trate de la causa prevista por el numeral 4 el juez lo remitirá al defensor de incapaces, para que le brinden la asesoría; si esta entidad comprueba que la persona no está en condiciones de sufragar un abogado, le nombrará uno de oficio.

## 9010 · Ley 2220 de 2022 (Estatuto de Conciliacion) · articulo 67

**Categoria:** Conciliacion prejudicial

**Pregunta:** Quiero demandar a mi ex-socio de negocio por un dinero que me debe, ¿tengo que hacer algo antes de ir directo a la demanda?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTÍCULO 67. La conciliación como requisito de procedibilidad. En los asuntos susceptibles de conciliación, se tendrá como regla general que la conciliación extrajudicial en derecho es requisito de procedibilidad para acudir ante las jurisdicciones que por norma así lo exijan, salvo cuando la ley lo excepcione. PARÁGRAFO 1. La conciliación en asuntos laborales no constituye requisito de procedibilidad. PARÁGRAFO 2. Podrá interponerse la demanda sin agotar el requisito de procedibilidad de la conciliación en los eventos en que el demandante bajo juramento declare que no conoce el domicilio, el lugar de habitación o el lugar de trabajo del demandado o este se encuentra ausente y no se conozca su paradero, o cuando quien demande sea una entidad pública. Igualmente, cuando la administración demande un acto administrativo que ocurrió por medios ilegales o fraudulentos. PARÁGRAFO 3. En todo proceso y ante cualquier jurisdicción, cuando se solicite la práctica de medidas cautelares se podrá acudir directamente al juez, sin necesidad de agotar la conciliación prejudicial como requisito de procedibilidad. Lo anterior, sin perjuicio de lo previsto al respecto para los asuntos Contencioso Administrativo.

## 9010 · Ley 2220 de 2022 (Estatuto de Conciliacion) · articulo 68

**Categoria:** Conciliacion prejudicial

**Pregunta:** Quiero demandar a mi ex-socio de negocio por un dinero que me debe, ¿tengo que hacer algo antes de ir directo a la demanda?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTÍCULO 68. La conciliación como requisito de procedibilidad en materia civil. La conciliación como requisito de procedibilidad en materia civil se regirá por lo normado en la Ley 1564 de 2012 Código General del Proceso o la norma que lo modifique, sustituya o complemente, conforme el cual si la materia de que trate es conciliable, la conciliación extrajudicial en derecho como requisito de procedibilidad deberá intentarse antes de acudir a la especialidad jurisdiccional civil en los procesos declarativos, con excepción de los divisorios, los de expropiación, los monitorios que se adelanten en cualquier jurisdicción y aquellos en donde se demande o sea obligatoria la citación de indeterminados. Igualmente en la restitución de bien arrendado de que trata el articulo 384 y en la cancelación, reposición y reivindicación de títulos valores de que trata el artículo 398 de la Ley 1564 de 2012, el demandante no estará obligado a solicitar y tramitar la audiencia de conciliación extrajudicial como requisito de procedibilidad de la demanda, ni del trámite correspondiente, casos en los cuales el interesado podrá presentar la demanda directamente ante el juez.

## 9010 · Ley 2220 de 2022 (Estatuto de Conciliacion) · articulo 70

**Categoria:** Conciliacion prejudicial

**Pregunta:** Quiero demandar a mi ex-socio de negocio por un dinero que me debe, ¿tengo que hacer algo antes de ir directo a la demanda?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTÍCULO 70. Cumplimiento del requisito de procedibilidad. El requisito de procedibilidad se entenderá cumplido en los siguientes eventos: 1. Cuando se efectúe la audiencia de conciliación sin que se logre acuerdo. 2. Cuando las partes o una de ellas no comparezca a la audiencia. En este evento deberán indicarse expresamente las excusas presentadas por la inasistencia, si las hubiere. 3. Cuando vencido el término de tres (3) meses a partir de la presentación de la solicitud de conciliación extrajudicial o su prorroga, la audiencia no se hubiere celebrado por cualquier causa; en este último evento se podrá acudir directamente a la Jurisdicción ordinaria con la sola presentación de la solicitud de conciliación. Para los eventos indicados en los numerales 1 y 2 del presente artículo el requisito de procedibilidad deberá acreditarse mediante las constancias de que trata la presente Iey. Realizada la audiencia sin que se haya logrado acuerdo conciliatorio total o parcial, se prescindirá de la conciliación prevista en el artículo 372 del Código General del Proceso, 180 de la Ley 1437 de 2011 y de la oportunidad de conciliación que las normas aplicables contemplen como obligatoria en el trámite del proceso. Sin embargo, en cualquier estado del proceso las partes de común acuerdo, o el Ministerio Público, podrán solicitar la realización de una audiencia de conciliación, o el Juez podrá acudir a ella, conforme a lo previsto en el artículo 131 de la presente ley. Si la conciliación recae sobre la totalidad del litigio no habrá lugar al proceso respectivo; si el acuerdo fuere parcial, se expedirá constancia de ello y las partes quedarán en libertad de discutir en juicio solamente las diferencias no conciliadas.

## 9010 · Ley 2220 de 2022 (Estatuto de Conciliacion) · articulo 71

**Categoria:** Conciliacion prejudicial

**Pregunta:** Quiero demandar a mi ex-socio de negocio por un dinero que me debe, ¿tengo que hacer algo antes de ir directo a la demanda?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTÍCULO 71. Inadmisión de la demanda judicial. Además de las causales establecidas en la Iey, el juez de conocimiento inadmitirá la demanda cuando no se acredite que se agotó la conciliación extrajudicial como requisito de procedibilidad, requisito que podrá ser aportado dentro del término para subsanar la demanda, so pena de rechazo. TÍTULO III NORMAS ESPECIALES RELATIVAS A LA CONCILIACIÓN EXTRAJUDICIAL EN MATERIA POLICIVA CAPÍTULO ÚNICO MODIFICACIÓN DE LA LEY 1801 DE 2016

## 9033 · Ley 361 de 1997 (Integracion social de personas con discapacidad) · articulo 26

**Categoria:** Despido

**Pregunta:** Estoy incapacitado por una cirugia y mi empresa me acaba de despedir, ¿es valido?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 26. En ningún caso la discapacidad de una persona, podrá ser motivo para obstaculizar una vinculación laboral, a menos que dicha discapacidad sea claramente demostrada como incompatible e insuperable en el cargo que se va a desempeñar. Así mismo, ninguna persona en situación de discapacidad podrá ser despedida o su contrato terminado por razón de su discapacidad, salvo que medie autorización del Ministerio del Trabajo. No obstante, quienes fueren despedidos o su contrato terminado por razón de su discapacidad, sin el cumplimiento del requisito previsto en el inciso primero del presente artículo, tendrán derecho a una indemnización equivalente a ciento ochenta (180) días del salario, sin perjuicio de las demás prestaciones e indemnizaciones a que hubiere lugar de acuerdo con el Código Sustantivo del Trabajo y demás normas que lo modifiquen, adicionen, complementen o aclaren.

## 9035 · Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana) · articulo 16

**Categoria:** Arriendo

**Pregunta:** Ya entregue el apartamento y el arrendador no me devuelve el deposito, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 16. Prohibición de depósitos y cauciones reales. En los contratos de arrendamiento para vivienda urbana no se podrán exigir depósitos en dinero efectivo u otra clase de cauciones reales, para garantizar el cumplimiento de las obligaciones que conforme a dichos contratos haya asumido el arrendatario. Tales garantías tampoco podrán estipularse indirectamente ni por interpuesta persona o pactarse en documentos distintos de aquel en que se haya consignado el contrato de arrendamiento, o sustituirse por otras bajo denominaciones diferentes de las indicadas en el inciso anterior. CAPITULO V Subarriendo y cesión del Contrato

## 9038 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 23

**Categoria:** Relaciones laborales

**Pregunta:** Llevo dos años como contratista, con horario fijo y jefe directo, pero sin prestaciones, ¿puedo reclamar algo?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 23. ELEMENTOS ESENCIALES. 1. Para que haya contrato de trabajo se requiere que concurran estos tres elementos esenciales: (Aparte subrayado declarado EXEQUIBLE por los cargos examinados, por la Corte Constitucional mediante Sentencia C-397-06 de 24 de mayo de 2006) a) La actividad personal del trabajador, es decir, realizada por sí mismo; b) La continuada subordinación o dependencia del trabajador respecto del empleador, que faculta a éste para exigirle el cumplimiento de órdenes, en cualquier momento, en cuanto al modo, tiempo o cantidad de trabajo, e imponerle reglamentos, la cual debe mantenerse por todo el tiempo de duración del contrato. Todo ello sin que afecte el honor, la dignidad y los derechos mínimos del trabajador en concordancia con los tratados o convenios internacionales que sobre derechos humanos relativos a la materia obliguen al país; y ( Literal b) declarado EXEQUIBLE por los cargos examinados, por la Corte Constitucional mediante Sentencia C-397-06) (Aparte subrayado declarado EXEQUIBLE por la Corte Constitucional mediante Sentencia C-386-00) c) Un salario como retribución del servicio. (Mediante Sentencia C-1549-00 del 20 de noviembre de 2000, Magistrado Ponente Dra. Martha Victoria Sáchica Méndez, la Corte Constitucional se declaró INHIBIDA de fallar sobre este literal c. por demanda sobre omisión legislativa.) 2. Una vez reunidos los tres elementos de que trata este artículo, se entiende que existe contrato de trabajo y no deja de serlo por razón del nombre que se le dé ni de otras condiciones o modalidades que se le agreguen. (Aparte subrayado declarado EXEQUIBLE por los cargos examinados, por la Corte Constitucional mediante Sentencia C-397-06) (Subrogado por el Art. 1 de la Ley 50 de 1990)

## 9038 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 24

**Categoria:** Relaciones laborales

**Pregunta:** Llevo dos años como contratista, con horario fijo y jefe directo, pero sin prestaciones, ¿puedo reclamar algo?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 24. PRESUNCION. Se presume que toda relación de trabajo personal está regida por un contrato de trabajo. (Modificado por el Art. 2 de la Ley 50 de 1990)

## 9039 · Ley 1266 de 2008 (Habeas data financiero) · articulo 13

**Categoria:** Reporte en centrales de riesgo

**Pregunta:** Pague una deuda hace seis años y todavia aparezco reportado en las centrales de riesgo, ¿eso es legal?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 13. Permanencia de la información. La información de carácter positivo permanecerá de manera indefinida en los bancos de datos de los operadores de información. Los datos cuyo contenido haga referencia al tiempo de mora, tipo de cobro, estado de la tartera y, en general, aquellos datos referentes a una situación de incumplimiento de obligaciones, SD regirán por un término máximo de permanencia, vencido el cual deberá ser retirada de los bancos de datos por el operador, de forma que los usuarios no puedan acceder o consultar dicha información. El término de permanencia de ésta información será el doble del tiempo de la mora, máximo cuatro (4) años contados a partir de la fecha en que sean pagadas las cuotas vencidas o sea extinguida la obligación. Parágrafo 1°. El dato negativo y los datos cuyo contenido haga referencia al tiempo de mora, tipo de cobro, estado de la cartera y, en general aquellos datos referentes a una situación de incumplimiento ele obligaciones caducarán una vez cumplido el término de ocho (8) años, contados a partir del momento en que entre en mora la obligación; cumplido este término deberán ser eliminados de la base de datos. Parágrafo 2°. En las obligaciones inferiores o iguales al (15 %) ce un (1) salario mínimo legal mensual vigente, el dato negativo por obligaciones que se han constituido en mora solo será reportado después de cumplirse con al menos dos comunicaciones, ambas en días diferentes. Y debe mediar entre la última comunicación y reporte, 20 días calendario. Parágrafo 3°. Toda información negativa o desfavorable que se encuentre en bases de datos y se relacione con calificaciones, récord (scorings-score), o cualquier tipo de medición financiera, comercial o crediticia, deberá ser actualizada de manera simultánea con el retiro del dato negativo o con la cesación del hecho que generó la disminución de la medición.

## 9041 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 594

**Categoria:** Embargos

**Pregunta:** Me embargaron la cuenta de nomina y era mi salario del mes, ¿eso se puede?

**Estado:** recuperado=no · partido en 5 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 594.Bienes inembargables. Además de los bienes inembargables señalados en la Constitución Política o en leyes especiales, no se podrán embargar: - 1. Los bienes, las rentas y recursos incorporados en el presupuesto general de la Nación o de las entidades territoriales, las cuentas del sistema general de participación, regalías y recursos de la seguridad social. - 2. Los depósitos de ahorro constituidos en los establecimientos de crédito, en el monto señalado por la autoridad competente, salvo para el pago de créditos alimentarios. - 3. Los bienes de uso público y los destinados a un servicio público cuando este se preste directamente por una entidad descentralizada de cualquier orden, o por medio de concesionario de estas; pero es embargable hasta la tercera parte de los ingresos brutos del respectivo servicio, sin que el total de embargos que se decreten exceda de dicho porcentaje. Cuando el servicio público lo presten particulares, podrán embargarse los bienes destinados a él, así como los ingresos brutos que se produzca y el secuestro se practicará como el de empresas industriales. - 4. Los recursos municipales originados en transferencias de la Nación, salvo para el cobro de obligaciones derivadas de los contratos celebrados en desarrollo de las mismas. - 5. Las sumas que para la construcción de obras públicas se hayan anticipado o deben anticiparse por las entidades de derecho público a los contratistas de ellas, mientras no hubiere concluido su construcción, excepto cuando se trate de obligaciones en favor de los trabajadores de dichas obras, por salarios, prestaciones sociales e indemnizaciones. - 6. Los salarios y las prestaciones sociales en la proporción prevista en las leyes respectivas. La inembargabilidad no se extiende a los salarios y prestaciones legalmente enajenados. - 7. Las condecoraciones y pergaminos recibidos por actos meritorios. - 8. Los uniformes y equipos de los militares. - 9. Los terrenos o lugares utilizados como cementerios o enterramientos. - 10. Los bienes destinados al culto religioso de cualquier confesión o iglesia que haya suscrito concordato o tratado de derecho internacional o convenio de derecho público interno con el Estado colombiano. - 11. El televisor, el radio, el computador personal o el equipo que haga sus veces, y los elementos indispensables para la comunicación personal, los utensilios de cocina, la nevera y los demás muebles necesarios para la subsistencia del afectado y de su familia, o para el trabajo individual, salvo que se trate del cobro del crédito otorgado para la adquisición del respectivo bien. Se exceptúan los bienes suntuarios de alto valor. - 12. El combustible y los artículos alimenticios para el sostenimiento de la persona contra quien se decretó el secuestro y de su familia durante un (1) mes, a criterio del juez. - 13. Los derechos personalísimos e intransferibles. - 14. Los derechos de uso y habitación. - 15. Las mercancías incorporadas en un título-valor que las represente, a menos que la medida comprenda la aprehensión del título. - 16. Las dos terceras partes de las rentas brutas de las entidades territoriales. - 17. Los anímales domésticos de compañía y de soporte emocional de los que trata el artículo 687 del Código Civil. Parágrafo. Los funcionarios judiciales o administrativos se abstendrán de decretar órdenes de embargo sobre recursos inembargables. En el evento en que por ley fuere procedente decretar la medida no obstante su carácter de inembargable, deberán invocar en la orden de embargo el fundamento legal para su procedencia. Recibida una orden de embargo que afecte recursos de naturaleza inembargable, en la cual no se indicare el fundamento legal para la procedencia de la excepción, el destinatario de la orden de embargo, se podrá abstener de cumplir la orden judicial o administrativa, dada la naturaleza de inembargable de los recursos. En tal evento, la entidad destinataria de la medida, deberá informar al día hábil siguiente a la autoridad que decretó la medida, sobre el hecho del no acatamiento de la medida por cuanto dichos recursos ostentan la calidad de inembargables. La autoridad que decretó la medida deberá pronunciarse dentro de los tres (3) días hábiles siguientes a la fecha de envío de la comunicación, acerca de si procede alguna excepción legal a la regla de inembargabilidad. Si pasados tres (3) días hábiles el destinatario no se recibe oficio alguno, se entenderá revocada la medida cautelar. En el evento de que la autoridad judicial o administrativa insista en la medida de embargo, la entidad destinataria cumplirá la orden, pero congelando los recursos en una cuenta especial que devengue intereses en las mismas condiciones de la cuenta o producto de la cual se produce el débito por cuenta del embargo. En todo caso, las sumas retenidas solamente se pondrán a disposición del juzgado, cuando cobre ejecutoria la sentencia o la providencia que le ponga fin al proceso que así lo ordene.

## 9041 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 154

**Categoria:** Embargos

**Pregunta:** Me embargaron la cuenta de nomina y era mi salario del mes, ¿eso se puede?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 154. REGLA GENERAL. No es embargable el salario mínimo legal o convencional. (Modificado por el Art. 3 de la Ley 11 de 1984) ARTICULO 155. EMBARGO PARCIAL DEL EXCEDENTE. El excedente del salario mínimo mensual solo es embargable en una quinta parte.

## 9041 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 155

**Categoria:** Embargos

**Pregunta:** Me embargaron la cuenta de nomina y era mi salario del mes, ¿eso se puede?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 154. REGLA GENERAL. No es embargable el salario mínimo legal o convencional. (Modificado por el Art. 3 de la Ley 11 de 1984) ARTICULO 155. EMBARGO PARCIAL DEL EXCEDENTE. El excedente del salario mínimo mensual solo es embargable en una quinta parte.

## 9041 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 156

**Categoria:** Embargos

**Pregunta:** Me embargaron la cuenta de nomina y era mi salario del mes, ¿eso se puede?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 156. EXCEPCION A FAVOR DE COOPERATIVAS Y PENSIONES ALIMENTICIAS. Todo salario puede ser embargado hasta en un cincuenta por ciento (50%) en favor de cooperativas legalmente autorizadas, o para cubrir pensiones alimenticias que se deban de conformidad con los artículos 411 y concordantes del Código Civil. (Aparte subrayado declarado EXEQUIBLE por la Corte Constitucional mediante Sentencia C-589-95) (Modificado por el Art. 4 de la Ley 11 de 1984) CAPITULO V. PRELACION DE LOS CREDITOS POR SALARIOS.

## 9042 · Ley 769 de 2002 (Codigo Nacional de Transito) · articulo 135

**Categoria:** Comparendos de transito

**Pregunta:** Me llego una fotomulta de una infraccion de hace casi un ano y nunca me notificaron antes, ¿tengo que pagarla?

**Estado:** recuperado=no · partido en 3 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 135. Procedimiento. Ante la comisión de una contravención, la autoridad de tránsito debe seguir el procedimiento siguiente para imponer el comparendo: Ordenará detener la marcha del vehículo y le extenderá al conductor la orden de comparendo en la que ordenará al infractor presentarse ante la autoridad de tránsito competente dentro de los cinco (5) días hábiles siguientes. Al conductor se le entregará copia de la orden de comparendo. Para el servicio además se enviará por correo dentro de los tres (3) días hábiles siguientes copia del comparendo al propietario del vehículo, a la empresa a la cual se encuentra vinculado y a la Superintendencia de Puertos y Transporte para lo de su competencia. La orden de comparendo deberá estar firmada por el conductor, siempre y cuando ello sea posible. Si el conductor se negara a firmar o a presentar la licencia, firmará por él un testigo, el cual deberá identificarse plenamente con el número de su cédula de ciudadanía o pasaporte, dirección de domicilio y teléfono, si lo tuviere. No obstante lo anterior, las autoridades competentes podrán contratar el servicio de medios técnicos y tecnológicos que permitan evidenciar la comisión de infracciones o contravenciones, el vehículo, la fecha, el lugar y la hora. En tal caso se enviará por correo dentro de los tres (3) días hábiles siguientes la infracción y sus soportes al propietario, quien estará obligado al pago de la multa. Para el servicio público además se enviará por correo dentro de este mismo término copia del comparendo y sus soportes a la empresa a la cual se encuentre vinculado y a la Superintendencia de Puertos y Transporte para lo de su competencia. El Ministerio de Transporte determinará las características técnicas del formulario de comparendo único nacional, así como su sistema de reparto. En este se indicará al conductor que tendrá derecho a nombrar un apoderado si así lo desea y que en la audiencia, para la que se le cite, se decretarán o practicarán las pruebas que solicite. El comparendo deberá además proveer el espacio para consignar la dirección del inculpado o del testigo que lo haya suscrito por este. Parágrafo 1°. La autoridad de tránsito entregará al funcionario competente o a la entidad que aquella encargue para su recaudo, dentro de las doce (12) horas siguientes, la copia de la orden de comparendo, so pena de incurrir en causal de mala conducta. Cuando se trate de agentes de policía de carreteras, la entrega de esta copia se hará por conducto del comandante de la ruta o del comandante director del servicio. Parágrafo 2°. Los organismos de tránsito podrán suscribir contratos o convenios con entes públicos o privados con el fin de dar aplicación a los principios de celeridad y eficiencia en el cobro de las multas. CAPÍTULO IV Actuación en caso de imposición de comparendo CAPITULO IV Actuación en caso de imposición de comparendo al conductor para el transporte público

## 9042 · Ley 769 de 2002 (Codigo Nacional de Transito) · articulo 161

**Categoria:** Comparendos de transito

**Pregunta:** Me llego una fotomulta de una infraccion de hace casi un ano y nunca me notificaron antes, ¿tengo que pagarla?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 161. Caducidad. La acción por contravención de las normas de tránsito, caduca al año (1), contado a partir de la ocurrencia de los hechos que dieron origen a ella. En consecuencia, durante este término se deberá decidir sobre la imposición de la sanción, en tal momento se entenderá realizada efectivamente la audiencia e interrumpida la caducidad. La decisión que resuelve los recursos, de ser procedentes, deberá ser expedida en un término de un (1) año contado a partir de su debida y oportuna interposición, si los recursos no se deciden en el término fijado en esta disposición, se entenderán fallados a favor del recurrente. La revocación directa solo podrá proceder en forma supletiva al proceso contravencional y en el evento de ser resuelta a favor de los intereses del presunto infractor sus efectos serán a futuro, iniciando la contabilización de la caducidad a partir de la notificación de la aceptación de su solicitud o su declaratoria de oficio, permitiendo al presunto infractor contar con los términos establecidos en la ley para la obtención de los descuentos establecidos en la ley o la realización de la audiencia contemplados en el Código Nacional de Tránsito. CAPITULO XI Aplicaciones de otros códigos y disposiciones finales

## 9043 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 47

**Categoria:** Garantias de consumo

**Pregunta:** Compre unos zapatos por internet y no me gustaron, ¿puedo devolverlos y que me devuelvan la plata?

**Estado:** recuperado=no · partido en 3 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 47. Retracto. En todos los contratos para la venta de bienes y prestación de servicios mediante sistemas de financiación otorgada por el productor o proveedor, venta de tiempos compartidos o ventas que utilizan métodos no tradicionales o a distancia, que por su naturaleza no deban consumirse o no hayan comenzado a ejecutarse antes de cinco (5) días, se entenderá pactado el derecho de retracto por parte del consumidor En el evento en que se haga uso de la facultad de retracto, se resolverá el contrato y se deberá reintegrar el dinero que el consumidor hubiese pagado. El consumidor deberá devolver el producto al productor o proveedor por los mismos medios y en las mismas condiciones en que lo recibió. Los costos de transporte y los demás que conlleve la devolución del bien serán cubiertos por el consumidor. El término máximo para ejercer el derecho de retracto será de cinco (5) días hábiles contados a partir de la entrega del bien o de la celebración del contrato en caso de la prestación de servicios. Se exceptúan del derecho de retracto, los siguientes casos: - 1. En los contratos de prestación de servicios cuya prestación haya comenzado con el acuerdo del consumidor; - 2. En los contratos de suministro de bienes o servicios cuyo precio esté sujeto a fluctuaciones de coeficientes del mercado financiero que el productor no pueda controlar; - 3. En los contratos de suministro de bienes confeccionados conforme a las especificaciones del consumidor o claramente personalizados; - 4. En los contratos de suministro de bienes que, por su naturaleza, no puedan ser devueltos o puedan deteriorarse o caducar con rapidez; - 5. En los contratos de servicios de apuestas y loterías; - 6. En los contratos de adquisición de bienes perecederos; - 7. En los contratos de adquisición de bienes de uso personal. En los casos de comercio electrónico la devolución del dinero a favor del consumidor no podrá exceder de quince (15) días calendario desde el momento en que ejerció el derecho y haya cumplido con las obligaciones: i) suministrar los datos correctos y completos requeridos por el proveedor para efectuar el proceso, ii) la devolución del producto en los términos del presente artículo; la suma será aplicada directamente sobre el instrumento de pago o medio de pago correspondiente o a través del medio acordado entre las partes, para tal fin el proveedor deberá informar de manera clara, detallada y específica al consumidor las opciones de las cuales dispone. Parágrafo 1°. Todos los actores, incluida la entidad financiera, deberán cumplir con el término establecido en el presente artículo.

## 9046 · Constitucion Politica de 1991 · articulo 23

**Categoria:** Derecho de peticion

**Pregunta:** Le mande un derecho de peticion a una empresa de telefonia y no me responden, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 23. Toda persona tiene derecho a presentar peticiones respetuosas a las autoridades por motivos de interés general o particular y a obtener pronta resolución. El legislador podrá reglamentar su ejercicio ante organizaciones privadas para garantizar los derechos fundamentales.

## 9046 · Ley 1437 de 2011 (CPACA) · articulo 14

**Categoria:** Derecho de peticion

**Pregunta:** Le mande un derecho de peticion a una empresa de telefonia y no me responden, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 14.Términos para resolver las distintas modalidades de peticiones. Salvo norma legal especial y so pena de sanción disciplinaria, toda petición deberá resolverse dentro de los quince (15) días siguientes a su recepción. Estará sometida a término especial la resolución de las siguientes peticiones: 1.Las peticiones de documentos y de información deberán resolverse dentro de los diez (10) días siguientes a su recepción. Si en ese lapso no se ha dado respuesta al peticionario, se entenderá, para todos los efectos legales, que la respectiva solicitud ha sido aceptada y, por consiguiente, la administración ya no podrá negar la entrega de dichos documentos al peticionario, y como consecuencia las copias se entregarán dentro de los tres (3) días siguientes. - 2. Las peticiones mediante las cuales se eleva una consulta a las autoridades en relación con las materias a su cargo deberán resolverse dentro de los treinta (30) días siguientes a su recepción. Parágrafo. Cuando excepcionalmente no fuere posible resolver la petición en los plazos aquí señalados, la autoridad debe informar esta circunstancia al interesado, antes del vencimiento del término señalado en la ley expresando los motivos de la demora y señalando a la vez el plazo razonable en que se resolverá o dará respuesta, que no podrá exceder del doble del inicialmente previsto.

## 9046 · Ley 1437 de 2011 (CPACA) · articulo 32

**Categoria:** Derecho de peticion

**Pregunta:** Le mande un derecho de peticion a una empresa de telefonia y no me responden, ¿que hago?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 32. Derecho de petición ante organizaciones privadas para garantizar los derechos fundamentales. Toda persona podrá ejercer el derecho de petición para garantizar sus derechos fundamentales ante organizaciones privadas con o sin personería jurídica, tales como sociedades, corporaciones, fundaciones, asociaciones, organizaciones religiosas, cooperativas, instituciones financieras o clubes. Salvo norma legal especial, el trámite y resolución de estas peticiones estarán sometidos a los principios y reglas establecidos en el Capítulo I de este título. Las organizaciones privadas solo podrán invocar la reserva de la información solicitada en los casos expresamente establecidos en la Constitución Política y la ley. Las peticiones ante las empresas o personas que administran archivos y bases de datos de carácter financiero, crediticio, comercial, de servicios y las provenientes de terceros países se regirán por lo dispuesto en la Ley Estatutaria del Hábeas Data. Parágrafo 1°. Este derecho también podrá ejercerse ante personas naturales cuando frente a ellas el solicitante se encuentre en situaciones de indefensión, subordinación o la persona natural se encuentre ejerciendo una función o posición dominante frente al peticionario. Parágrafo 2°. Los personeros municipales y distritales y la Defensoría del Pueblo prestarán asistencia eficaz e inmediata a toda persona que la solicite, para garantizarle el ejercicio del derecho constitucional de petición que hubiere ejercido o desee ejercer ante organizaciones o instituciones privadas. Parágrafo 3°. Ninguna entidad privada podrá negarse a la recepción y radicación de solicitudes y peticiones respetuosas, so pena de incurrir en sanciones y/o multas por parte de las autoridades competentes.

## 9048 · Ley 599 de 2000 (Codigo Penal) · articulo 246

**Categoria:** Derecho penal - denuncia

**Pregunta:** Me estafaron: hice una transferencia por una compra en internet y el vendedor desaparecio, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 246. Estafa. El que obtenga provecho ilícito para sí o para un tercero, con perjuicio ajeno, induciendo o manteniendo a otro en error por medio de artificios o engaños, incurrirá en prisión de treinta y dos (32) a ciento cuarenta y cuatro (144) meses y multa de sesenta y seis punto sesenta y seis (66.66) a mil quinientos (1.500) salarios mínimos legales mensuales vigentes. En la misma pena incurrirá el que en lotería, rifa o juego, obtenga provecho para sí o para otros, valiéndose de cualquier medio fraudulento para asegurar un determinado resultado. La pena será de prisión de dieciséis (16) a treinta y seis (36) meses y multa hasta de quince (15) salarios mínimos legales mensuales vigentes, cuando la cuantía no exceda de diez (10) salarios mínimos legales mensuales vigentes. Nota: Penas aumentadas por el artículo 33 Ley 1474 de 2011: …Los tipos penales de que tratan los artículos 246… de la Ley 599 de 2000 les será aumentada la pena de una sexta parte a la mitad cuando la conducta sea cometida por servidor público que ejerza como funcionario de alguno de los organismos de control del Estado. (vigencia a partir del 12 de julio de 2011)

## 9048 · Ley 599 de 2000 (Codigo Penal) · articulo 269-J

**Categoria:** Derecho penal - denuncia

**Pregunta:** Me estafaron: hice una transferencia por una compra en internet y el vendedor desaparecio, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Articulo 269J.Transferencia no consentida de activos. El que, con ánimo de lucro y valiéndose de alguna manipulación informática o artificio semejante, consiga la transferencia no consentida de cualquier activo en perjuicio de un tercero, siempre que la conducta no constituya delito sancionado con pena más grave, incurrirá en pena de prisión de cuarenta y ocho (48) a ciento veinte (120) meses y en multa de 200 a 1.500 salarios mínimos legales mensuales vigentes. La misma sanción se le impondrá a quien fabrique, introduzca, posea o facilite programa de computador destinado a la comisión del delito descrito en el inciso anterior, o de una estafa. Si la conducta descrita en los dos incisos anteriores tuviere una cuantía superior a 200 salarios mínimos legales mensuales, la sanción allí señalada se incrementará en la mitad. TITULO VIII DE LOS DELITOS CONTRA LOS DERECHOS DE AUTOR CAPITULO UNICO

## 9048 · Ley 906 de 2004 (Codigo de Procedimiento Penal) · articulo 67

**Categoria:** Derecho penal - denuncia

**Pregunta:** Me estafaron: hice una transferencia por una compra en internet y el vendedor desaparecio, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 67.Deber de denunciar. Toda persona debe denunciar a la autoridad los delitos de cuya comisión tenga conocimiento y que deban investigarse de oficio. El servidor público que conozca de la comisión de un delito que deba investigarse de oficio, iniciará sin tardanza la investigación si tuviere competencia para ello; en caso contrario, pondrá inmediatamente el hecho en conocimiento ante la autoridad competente.

## 9048 · Ley 906 de 2004 (Codigo de Procedimiento Penal) · articulo 69

**Categoria:** Derecho penal - denuncia

**Pregunta:** Me estafaron: hice una transferencia por una compra en internet y el vendedor desaparecio, ¿que hago?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 69.Requisitos de la denuncia, de la querella o de la petición. La denuncia, querella o petición se hará verbalmente, o por escrito, o por cualquier medio técnico que permita la identificación del autor, dejando constancia del día y hora de su presentación y contendrá una relación detallada de los hechos que conozca el denunciante. Este deberá manifestar, si le consta, que los mismos hechos ya han sido puestos en conocimiento de otro funcionario. Quien la reciba advertirá al denunciante que la falsa denuncia implica responsabilidad penal. En todo caso se inadmitirán las denuncias sin fundamento. La denuncia solo podrá ampliarse por una sola vez a instancia del denunciante, o del funcionario competente, sobre aspectos de importancia para la investigación. Los escritos anónimos que no suministren evidencias o datos concretos que permitan encauzar la investigación se archivarán por el fiscal correspondiente.

## 9049 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 10

**Categoria:** Derecho comercial

**Pregunta:** Vendo ropa por Instagram desde mi casa, ¿tengo que registrar mi negocio en la Camara de Comercio?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 10. Son comerciantes las personas que profesionalmente se ocupan en alguna de las actividades que la ley considera mercantiles. La calidad de comerciante se adquiere aunque la actividad mercantil se ejerza por medio de apoderado, intermediario o interpuesta persona.

## 9049 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 13

**Categoria:** Derecho comercial

**Pregunta:** Vendo ropa por Instagram desde mi casa, ¿tengo que registrar mi negocio en la Camara de Comercio?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 13. Para todos los efectos legales se presume que una persona ejerce el comercio en los siguientes casos: 1) Cuando se halle inscrita en el registro mercantil; 2) Cuando tenga establecimiento de comercio abierto, y 3) Cuando se anuncie al público como comerciante por cualquier medio.

## 9049 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 19

**Categoria:** Derecho comercial

**Pregunta:** Vendo ropa por Instagram desde mi casa, ¿tengo que registrar mi negocio en la Camara de Comercio?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 19. Es obligación de todo comerciante: 1) Matricularse en el registro mercantil; 2) Inscribir en el registro mercantil todos los actos, libros y documentos respecto de los cuales la ley exija esa formalidad; 3) Llevar contabilidad regular de sus negocios conforme a las prescripciones legales; 4) Conservar, con arreglo a la ley, la correspondencia y demás documentos relacionados con sus negocios o actividades; 5) Denunciar ante el juez competente la cesación en el pago corriente de sus obligaciones mercantiles, y 6) Abstenerse de ejecutar actos de competencia desleal. TITUTLO II. DE LOS ACTOS, OPERACIONES Y EMPRESAS MERCANTILES

## 9049 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 26

**Categoria:** Derecho comercial

**Pregunta:** Vendo ropa por Instagram desde mi casa, ¿tengo que registrar mi negocio en la Camara de Comercio?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 26. El registro mercantil tendrá por objeto llevar la matrícula de los comerciantes y de los establecimientos de comercio, así como la inscripción de todos los actos, libros y documentos respecto de los cuales la ley exigiere esa formalidad. El registro mercantil será público. Cualquier persona podrá examinar los libros y archivos en que fuere llevado, tomar anotaciones de sus asientos o actos y obtener copias de los mismos.

## 9049 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 28

**Categoria:** Derecho comercial

**Pregunta:** Vendo ropa por Instagram desde mi casa, ¿tengo que registrar mi negocio en la Camara de Comercio?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 28. Deberán inscribirse en el registro mercantil: 1) Las personas que ejerzan profesionalmente el comercio y sus auxiliares, tales como los comisionistas, corredores, agentes, representantes de firmas nacionales o extranjeras, quienes lo harán dentro del mes siguiente a la fecha en que inicien actividades; 2) Las capitulaciones matrimoniales y las liquidaciones de sociedades conyugales, cuando el marido y la mujer o alguno de ellos sea comerciante; 3) La interdicción judicial pronunciada contra comerciantes; las providencias en que se imponga a estos la prohibición de ejercer el comercio; los concordatos preventivos y los celebrados dentro del proceso de quiebra; la declaración de quiebra y el nombramiento de síndico de ésta y su remoción; la posesión de cargos públicos que inhabiliten para el ejercicio del comercio, y en general, las incapacidades o inhabilidades previstas en la ley para ser comerciante; 4) Las autorizaciones que, conforme a la ley, se otorguen a los menores para ejercer el comercio, y la revocación de las mismas; 5) Todo acto en virtud del cual se confiera, modifique o revoque la administración parcial o general de bienes o negocios del comerciante: 6) La apertura de establecimientos de comercio y de sucursales, y los actos que modifiquen o afecten la propiedad de los mismos o su administración; 7) Los libros de contabilidad, los de registro de accionistas, los de actas de asambleas y juntas de socios, así como los de juntas directivas de sociedades mercantiles; 8) Los embargos y demandas civiles relacionados con derechos cuya mutación esté sujeta a registro mercantil; 9) La constitución, adiciones o reformas estatutarias y la liquidación de sociedades comerciales, así como la designación de representantes legales y liquidadores, y su remoción. Las compañías vigiladas por la Superintendencia de Sociedades deberán cumplir, además de la formalidad del registro, los requisitos previstos en las disposiciones legales que regulan dicha vigilancia, y 10) Los demás actos y documentos cuyo registro mercantil ordene la ley.

## 9050 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 712

**Categoria:** Derecho comercial

**Pregunta:** Recibi un cheque como pago y el banco lo devolvio por falta de fondos, ¿que puedo hacer?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 712. EXPEDICIÓN DEL CHEQUE. El cheque sólo puede ser expedido en formularios impresos de cheques o chequeras y a cargo de un banco. El título que en forma de cheque se expida en contravención a éste artículo no producirá efectos de título-valor.

## 9050 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 730

**Categoria:** Derecho comercial

**Pregunta:** Recibi un cheque como pago y el banco lo devolvio por falta de fondos, ¿que puedo hacer?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 730. Las acciones cambiarias derivadas del cheque prescriben: Las del último tenedor, en seis meses, contados desde la presentación; las de los endosantes y avalistas, en el mismo término, contado desde el día siguiente a aquel en que paguen el cheque.

## 9050 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 731

**Categoria:** Derecho comercial

**Pregunta:** Recibi un cheque como pago y el banco lo devolvio por falta de fondos, ¿que puedo hacer?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 731. El librador de un cheque presentado en tiempo y no pagado por su culpa abonará al tenedor, como sanción, el 20% del importe del cheque, sin perjuicio de que dicho tenedor persiga por las vías comunes la indemnización de los daños que le ocasione.

## 9050 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 784

**Categoria:** Derecho comercial

**Pregunta:** Recibi un cheque como pago y el banco lo devolvio por falta de fondos, ¿que puedo hacer?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 784. Contra la acción cambiaria sólo podrán oponerse las siguientes excepciones: 1) Las que se funden en el hecho de no haber sido el demandado quien suscribió el título; 2) La incapacidad del demandado al suscribir el título; 3) Las de falta de representación o de poder bastante de quien haya suscrito el título a nombre del demandado; 4) Las fundadas en la omisión de los requisitos que el título deba contener y que la ley no supla expresamente; 5) La alteración del texto del título, sin perjuicio de lo dispuesto respecto de los signatarios posteriores a la alteración; 6) Las relativas a la no negociabilidad del título; 7) Las que se funden en quitas o en pago total o parcial, siempre que consten en el título; 8) Las que se funden en la consignación del importe del título conforme a la ley o en el depósito del mismo importe hecho en los términos de este Título; 9) Las que se funden en la cancelación judicial del título o en orden judicial de suspender su pago, proferida como se prevé en este Título; 10) Las de prescripción o caducidad, y las que se basen en la falta de requisitos necesarios para el ejercicio de la acción; 11) Las que se deriven de la falta de entrega del título o de la entrega sin intención de hacerlo negociable, contra quien no sea tenedor de buena fe; 12) Las derivadas del negocio jurídico que dio origen a la creación o transferencia del título, contra el demandante que haya sido parte en el respectivo negocio o contra cualquier otro demandante que no sea tenedor de buena fe exenta de culpa, y 13) Las demás personales que pudiere oponer el demandado contra el actor.

## 9050 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 793

**Categoria:** Derecho comercial

**Pregunta:** Recibi un cheque como pago y el banco lo devolvio por falta de fondos, ¿que puedo hacer?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 793. El cobro de un título-valor dará lugar al procedimiento ejecutivo, sin necesidad de reconocimiento de firmas. Sección II. Cobro del bono de prenda

## 9050 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 422

**Categoria:** Derecho comercial

**Pregunta:** Recibi un cheque como pago y el banco lo devolvio por falta de fondos, ¿que puedo hacer?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 422. Título ejecutivo. Pueden demandarse ejecutivamente las obligaciones expresas, claras y exigibles que consten en documentos que provengan del deudor o de su causante, y constituyan plena prueba contra él, o las que emanen de una sentencia de condena proferida por juez o tribunal de cualquier jurisdicción, o de otra providencia judicial, o de las providencias que en procesos de policía aprueben liquidación de costas o señalen honorarios de auxiliares de la justicia, y los demás documentos que señale la ley. La confesión hecha en el curso de un proceso no constituye título ejecutivo, pero sí la que conste en el interrogatorio previsto en el artículo 184.

## 9055 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 982

**Categoria:** Accidentes de transito

**Pregunta:** Iba de pasajero en un taxi que se accidento y quede lesionado, a quien le reclamo?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 982.OBLIGACIONES DEL TRANSPORTADOR. El transportador estará obligado a conducir a las personas o a las cosas sanas y salvas al lugar o sitio convenido, dentro del término, por el medio y clase de vehículos previstos en el contrato y, en defecto de estipulación, conforme a los horarios, itinerarios y demás normas contenidas en los reglamentos oficiales, en un término prudencial y por una vía razonablemente directa.

## 9055 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 1003

**Categoria:** Accidentes de transito

**Pregunta:** Iba de pasajero en un taxi que se accidento y quede lesionado, a quien le reclamo?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 1003. El transportador responderá de todos los daños que sobrevengan al pasajero desde el momento en que se haga cargo de éste. Su responsabilidad comprenderá, además, los daños causados por los vehículos utilizados por él y los que ocurran en los sitios de embarque y desembarque, estacionamiento o espera, o en instalaciones de cualquier índole que utilice el transportador para la ejecución del contrato. Dicha responsabilidad sólo cesará cuando el viaje haya concluido; y también en cualquiera de los siguientes casos: 1) Cuando los daños ocurran por obra exclusiva de terceras personas; 2) Cuando los daños ocurran por fuerza mayor, pero ésta no podrá alegarse cuando haya mediado culpa imputable al transportador, que en alguna forma sea causa del daño; 3) Cuando los daños ocurran por culpa exclusiva del pasajero, o por lesiones orgánicas o enfermedad anterior del mismo que no hayan sido agravadas a consecuencia de hechos imputables al transportador, y 4) Cuando ocurra la pérdida o avería de cosas que conforme a los reglamentos de la empresa puedan llevarse "a la mano" y no hayan sido confiadas a la custodia del transportador.

## 9056 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 597

**Categoria:** Embargos

**Pregunta:** Me llego un embargo del juzgado pero el nombre y la cedula no son los mios, solo se parecen.

**Estado:** recuperado=no · partido en 4 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 597. Levantamiento del embargo y secuestro. Se levantarán el embargo y secuestro en los siguientes casos: - 1. Si se pide por quien solicitó la medida, cuando no haya litisconsortes o terceristas; si los hubiere, por aquel y estos, y si se tratare de proceso de sucesión por todos los herederos reconocidos y el cónyuge o compañero permanente. - 2. Si se desiste de la demanda que originó el proceso, en los mismos casos del numeral anterior. - 3. Si el demandado presta caución para garantizar lo que se pretende, y el pago de las costas. - 4. Si se ordena la terminación del proceso ejecutivo por la revocatoria del mandamiento de pago o por cualquier otra causa. - 5. Si se absuelve al demandado en proceso declarativo, o este termina por cualquier otra causa. - 6. Si el demandante en proceso declarativo no formula la solicitud de que trata el inciso primero del artículo 306 dentro de los treinta (30) días siguientes a la ejecutoria de la sentencia que contenga la condena. - 7. Si se trata de embargo sujeto a registro, cuando del certificado del registrador aparezca que la parte contra quien se profirió la medida no es la titular del dominio del respectivo bien, sin perjuicio de lo establecido para la efectividad de la garantía hipotecaria o prendaria. - 8. Si un tercero poseedor que no estuvo presente en la diligencia de secuestro solicita al juez del conocimiento, dentro de los veinte (20) días siguientes a la práctica de la diligencia, si lo hizo el juez de conocimiento o a la notificación del auto que ordena agregar el despacho comisorio, que se declare que tenía la posesión material del bien al tiempo en que aquella se practicó, y obtiene decisión favorable. La solicitud se tramitará como incidente, en el cual el solicitante deberá probar su posesión. También podrá promover el incidente el tercero poseedor que haya estado presente en la diligencia sin la representación de apoderado judicial, pero el término para hacerlo será de cinco (5) días. Si el incidente se decide desfavorablemente a quien lo promueve, se impondrá a este una multa de cinco (5) a veinte (20) salarios mínimos mensuales. - 9. Cuando exista otro embargo o secuestro anterior. - 10. Cuando pasados cinco (5) años a partir de la inscripción de la medida, no se halle el expediente en que ella se decretó. Con este propósito, el respectivo juez fijará aviso en la secretaría del juzgado por el término de veinte (20) días, para que los interesados puedan ejercer sus derechos. Vencido este plazo, el juez resolverá lo pertinente. En los casos de los numerales 1, 2, 9 y 10 para resolver la respectiva solicitud no será necesario que se haya notificado el auto admisorio de la demanda o el mandamiento ejecutivo. Siempre que se levante el embargo o secuestro en los casos de los numerales 1, 2, 4, 5 y 8 del presente artículo, se condenará de oficio o a solicitud de parte en costas y perjuicios a quienes pidieron tal medida, salvo que las partes convengan otra cosa. En todo momento cualquier interesado podrá pedir que se repita el oficio de cancelación de medidas cautelares. - 11. Cuando el embargo recaiga contra uno de los recursos públicos señalados en el artículo 594, y este produzca insostenibilidad fiscal o presupuestal del ente demandado, el Procurador General de la Nación, el Ministro del respectivo ramo, el Alcalde, el Gobernador o el Director de la Agencia Nacional de Defensa Jurídica del Estado, podrán solicitar su levantamiento. Parágrafo. Lo previsto en los numerales 1, 2, 5, 7 y 10 de este artículo también se aplicará para levantar la inscripción de la demanda.

## 9057 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 133

**Categoria:** Embargos

**Pregunta:** Soy codeudor de un credito y me embargaron sin avisarme nada antes.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 133. Causales de nulidad. El proceso es nulo, en todo o en parte, solamente en los siguientes casos: - 1. Cuando el juez actúe en el proceso después de declarar la falta de jurisdicción o de competencia. - 2. Cuando el juez procede contra providencia ejecutoriada del superior, revive un proceso legalmente concluido o pretermite íntegramente la respectiva instancia. - 3. Cuando se adelanta después de ocurrida cualquiera de las causales legales de interrupción o de suspensión, o si, en estos casos, se reanuda antes de la oportunidad debida. - 4. Cuando es indebida la representación de alguna de las partes, o cuando quien actúa como su apoderado judicial carece íntegramente de poder. - 5. Cuando se omiten las oportunidades para solicitar, decretar o practicar pruebas, o cuando se omite la práctica de una prueba que de acuerdo con la ley sea obligatoria. - 6. Cuando se omita la oportunidad para alegar de conclusión o para sustentar un recurso o descorrer su traslado. - 7. Cuando la sentencia se profiera por un juez distinto del que escuchó los alegatos de conclusión o la sustentación del recurso de apelación. - 8. Cuando no se practica en legal forma la notificación del auto admisorio de la demanda a personas determinadas, o el emplazamiento de las demás personas aunque sean indeterminadas, que deban ser citadas como partes, o de aquellas que deban suceder en el proceso a cualquiera de las partes, cuando la ley así lo ordena, o no se cita en debida forma al Ministerio Público o a cualquier otra persona o entidad que de acuerdo con la ley debió ser citado. Cuando en el curso del proceso se advierta que se ha dejado de notificar una providencia distinta del auto admisorio de la demanda o del mandamiento de pago, el defecto se corregirá practicando la notificación omitida, pero será nula la actuación posterior que dependa de dicha providencia, salvo que se haya saneado en la forma establecida en este código. Parágrafo. Las demás irregularidades del proceso se tendrán por subsanadas si no se impugnan oportunamente por los mecanismos que este código establece.

## 9057 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 290

**Categoria:** Embargos

**Pregunta:** Soy codeudor de un credito y me embargaron sin avisarme nada antes.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 290. Procedencia de la notificación personal. Deberán hacerse personalmente las siguientes notificaciones: - 1. Al demandado o a su representante o apoderado judicial, la del auto admisorio de la demanda y la del mandamiento ejecutivo. - 2. A los terceros y a los funcionarios públicos en su carácter de tales, la del auto que ordene citarlos. - 3. Las que ordene la ley para casos especiales.

## 9057 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 291

**Categoria:** Embargos

**Pregunta:** Soy codeudor de un credito y me embargaron sin avisarme nada antes.

**Estado:** recuperado=no · partido en 5 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 291. Práctica de la notificación personal. Para la práctica de la notificación personal se procederá así: - 1. Las entidades públicas se notificarán personalmente en la forma prevista en el artículo 612 de este código. Las entidades públicas se notificarán de las sentencias que se profieran por fuera de audiencia de acuerdo con lo dispuesto en el artículo 203 de la Ley 1437 de 2011. De las que se profieran en audiencia se notificarán en estrados. - 2. Las personas jurídicas de derecho privado y los comerciantes inscritos en el registro mercantil deberán registrar en la Cámara de Comercio o en la oficina de registro correspondiente del lugar donde funcione su sede principal, sucursal o agencia, la dirección donde recibirán notificaciones judiciales. Con el mismo propósito deberán registrar, además, una dirección electrónica. Esta disposición también se aplicará a las personas naturales que hayan suministrado al juez su dirección de correo electrónico. Si se registran varias direcciones, la notificación podrá surtirse en cualquiera de ellas. - 3. La parte interesada remitirá una comunicación a quien deba ser notificado, a su representante o apoderado, por medio de servicio postal autorizado por el Ministerio de Tecnologías de la Información y las Comunicaciones, en la que le informará sobre la existencia del proceso, su naturaleza y la fecha de la providencia que debe ser notificada, previniéndolo para que comparezca al juzgado a recibir notificación dentro de los cinco (5) días siguientes a la fecha de su entrega en el lugar de destino. Cuando la comunicación deba ser entregada en municipio distinto al de la sede del juzgado, el término para comparecer será de diez (10) días; y si fuere en el exterior el término será de treinta (30) días. La comunicación deberá ser enviada a cualquiera de las direcciones que le hubieren sido informadas al juez de conocimiento como correspondientes a quien deba ser notificado. Cuando se trate de persona jurídica de derecho privado la comunicación deberá remitirse a la dirección que aparezca registrada en la Cámara de Comercio o en la oficina de registro correspondiente. Cuando la dirección del destinatario se encuentre en una unidad inmobiliaria cerrada, la entrega podrá realizarse a quien atienda la recepción. La empresa de servicio postal deberá cotejar y sellar una copia de la comunicación, y expedir constancia sobre la entrega de esta en la dirección correspondiente. Ambos documentos deberán ser incorporados al expediente. Cuando se conozca la dirección electrónica de quien deba ser notificado, la comunicación podrá remitirse por el Secretario o el interesado por medio de correo electrónico. Se presumirá que el destinatario ha recibido la comunicación cuando el iniciador recepcione acuse de recibo. En este caso, se dejará constancia de ello en el expediente y adjuntará una impresión del mensaje de datos. - 4. Si la comunicación es devuelta con la anotación de que la dirección no existe o que la persona no reside o no trabaja en el lugar, a petición del interesado se procederá a su emplazamiento en la forma prevista en este código. Cuando en el lugar de destino rehusaren recibir la comunicación, la empresa de servicio postal la dejará en el lugar y emitirá constancia de ello. Para todos los efectos legales, la comunicación se entenderá entregada. - 5. Si la persona por notificar comparece al juzgado, se le pondrá en conocimiento la providencia previa su identificación mediante cualquier documento idóneo, de lo cual se extenderá acta en la que se expresará la fecha en que se practique, el nombre del notificado y la providencia que se notifica, acta que deberá firmarse por aquel y el empleado que haga la notificación. Al notificado no se le admitirán otras manifestaciones que la de asentimiento a lo resuelto, la convalidación de lo actuado, el nombramiento prevenido en la providencia y la interposición de los recursos de apelación y casación. Si el notificado no sabe, no quiere o no puede firmar, el notificador expresará esa circunstancia en el acta. - 6. Cuando el citado no comparezca dentro de la oportunidad señalada, el interesado procederá a practicar la notificación por aviso. Parágrafo 1°. La notificación personal podrá hacerse por un empleado del juzgado cuando en el lugar no haya empresa de servicio postal autorizado o el juez lo estime aconsejable para agilizar o viabilizar el trámite de notificación. Si la persona no fuere encontrada, el empleado dejará la comunicación de que trata este artículo y, en su caso, el aviso previsto en el artículo 292. Parágrafo 2°. El interesado podrá solicitar al juez que se oficie a determinadas entidades públicas o privadas que cuenten con bases de datos para que suministren la información que sirva para localizar al demandado.

## 9057 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 292

**Categoria:** Embargos

**Pregunta:** Soy codeudor de un credito y me embargaron sin avisarme nada antes.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 292. Notificación por aviso. Cuando no se pueda hacer la notificación personal del auto admisorio de la demanda o del mandamiento ejecutivo al demandado, o la del auto que ordena citar a un tercero, o la de cualquiera otra providencia que se debe realizar personalmente, se hará por medio de aviso que deberá expresar su fecha y la de la providencia que se notifica, el juzgado que conoce del proceso, su naturaleza, el nombre de las partes y la advertencia de que la notificación se considerará surtida al finalizar el día siguiente al de la entrega del aviso en el lugar de destino. Cuando se trate de auto admisorio de la demanda o mandamiento ejecutivo, el aviso deberá ir acompañado de copia informal de la providencia que se notifica. El aviso será elaborado por el interesado, quien lo remitirá a través de servicio postal autorizado a la misma dirección a la que haya sido enviada la comunicación a que se refiere el numeral 3 del artículo anterior. La empresa de servicio postal autorizado expedirá constancia de haber sido entregado el aviso en la respectiva dirección, la cual se incorporará al expediente, junto con la copia del aviso debidamente cotejada y sellada. En lo pertinente se aplicará lo previsto en el artículo anterior. Cuando se conozca la dirección electrónica de quien deba ser notificado, el aviso y la providencia que se notifica podrán remitirse por el Secretario o el interesado por medio de correo electrónico. Se presumirá que el destinatario ha recibido el aviso cuando el iniciador recepcione acuse de recibo. En este caso, se dejará constancia de ello en el expediente y adjuntará una impresión del mensaje de datos.

## 9058 · Ley 1620 de 2013 (Sistema Nacional de Convivencia Escolar) · articulo 21

**Categoria:** Educacion / debido proceso disciplinario

**Pregunta:** Expulsaron a mi hijo del colegio por un video que circulo, sin llamarnos a nosotros antes.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 21. Manual de convivencia. En el marco del Sistema Nacional de Convivencia Escolar y Formación para los Derechos Humanos, la Educación para la Sexualidad y la Prevención y Mitigación de la Violencia Escolar, y además de lo establecido en el artículo 87 de la Ley 115 de 1994, los manuales de convivencia deben identificar nuevas formas y alternativas para incentivar y fortalecer la convivencia escolar y el ejercicio de los derechos humanos, sexuales y reproductivos de los estudiantes, que permitan aprender del error, respetar la diversidad y dirimir los conflictos de manera pacífica, así como de posibles situaciones y conductas que atenten contra el ejercicio de sus derechos. El manual concederá al educador el rol de orientador y mediador en situaciones que atenten contra la convivencia escolar y el ejercicio de los derechos humanos, sexuales y reproductivos, así como funciones en la detección temprana de estas mismas situaciones, a los estudiantes, el manual les concederá un rol activo para participar en la definición de acciones para el manejo de estas situaciones, en el marco de la ruta de atención integral. El manual de convivencia deberá incluir la ruta de atención integral y los protocolos de que trata la presente ley. Acorde con el artículo 87 de la Ley 115 de 1994, el manual de convivencia define los derechos y obligaciones de los estudiantes de cada uno de los miembros de la comunidad educativa, a través de los cuales se rigen las características y condiciones de interacción y convivencia entre los mismos y señala el debido proceso que debe seguir el establecimiento educativo ante el incumplimiento del mismo. Es una herramienta construida, evaluada y ajustada por la comunidad educativa, con la participación activa de los estudiantes y padres de familia, de obligatorio cumplimiento en los establecimientos educativos públicos y privados y es un componente esencial del proyecto educativo institucional. El manual de que trata el presente artículo debe incorporar, además de lo anterior, las definiciones, principios y responsabilidades que establece la presente ley, sobre los cuales se desarrollarán los factores de promoción y prevención y atención de la Ruta de Atención Integral para la Convivencia Escolar. El Ministerio de Educación Nacional reglamentará lo relacionado con el manual de convivencia y dará los lineamientos necesarios para que allí se incorporen las disposiciones necesarias para el manejo de conflictos y conductas que afectan la convivencia escolar, y los derechos humanos, sexuales y reproductivos, y para la participación de la familia, de conformidad con el artículo 22 de la presente ley.

## 9058 · Ley 115 de 1994 (Ley General de Educacion) · articulo 87

**Categoria:** Educacion / debido proceso disciplinario

**Pregunta:** Expulsaron a mi hijo del colegio por un video que circulo, sin llamarnos a nosotros antes.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 87. Reglamento o manual de convivencia. Los establecimientos educativos tendrán un reglamento o manual de convivencia, en el cual se definan los derechos y obligaciones, de los estudiantes. Los padres o tutores y los educandos al firmar la matrícula correspondiente en representación de sus hijos, estarán aceptando el mismo.

## 9058 · Ley 115 de 1994 (Ley General de Educacion) · articulo 96

**Categoria:** Educacion / debido proceso disciplinario

**Pregunta:** Expulsaron a mi hijo del colegio por un video que circulo, sin llamarnos a nosotros antes.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 96. Permanencia en el establecimiento educativo. El reglamento interno de la institución educativa establecerá las condiciones de permanencia del alumno en el plantel y el procedimiento en caso de exclusión. La reprobación por primera vez de un determinado grado por parte del alumno, no será causal de exclusión del respectivo establecimiento, cuando no esté asociada a otra causal expresamente contemplada en el reglamento institucional o manual de convivencia.

## 9058 · Ley 115 de 1994 (Ley General de Educacion) · articulo 132

**Categoria:** Educacion / debido proceso disciplinario

**Pregunta:** Expulsaron a mi hijo del colegio por un video que circulo, sin llamarnos a nosotros antes.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 132. Facultades del rector para sancionar y otorgar distinciones. El rector o director del establecimiento educativo podrá otorgar distinciones o imponer sanciones a los estudiantes según el reglamento o manual de convivencia de éste, en concordancia con lo que al respecto disponga el Ministerio de Educación Nacional. CAPITULO 6º. Estímulos para docentes

## 9060 · Ley 599 de 2000 (Codigo Penal) · articulo 286

**Categoria:** Contratacion estatal y facturacion

**Pregunta:** Soy contratista del municipio y me piden firmar actas de recibo de obras que todavia no se han hecho.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 286.Falsedad ideológica en documento público. El servidor público que en ejercicio de sus funciones, al extender documento público que pueda servir de prueba, consigne una falsedad o calle total o parcialmente la verdad, incurrirá en prisión de sesenta y cuatro (64) a ciento cuarenta y cuatro (144) meses e inhabilitación para el ejercicio de derechos y funciones públicas de ochenta (80) a ciento ochenta (180) meses. NOTA: Penas aumentadas por el artículo 14 de la ley 890 de 2004. (Vigencia desde el 1° de enero de 2005)

## 9060 · Ley 599 de 2000 (Codigo Penal) · articulo 287

**Categoria:** Contratacion estatal y facturacion

**Pregunta:** Soy contratista del municipio y me piden firmar actas de recibo de obras que todavia no se han hecho.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 287.Falsedad material en documento público. El que falsifique documento público que pueda servir de prueba, incurrirá en prisión de cuarenta y ocho (48) a ciento ocho (108) meses. Si la conducta fuere realizada por un servidor público en ejercicio de sus funciones, la pena será de sesenta y cuatro (64) a ciento cuarenta y cuatro (144) meses e inhabilitación para el ejercicio de derechos y funciones públicas de ochenta (80) a ciento ochenta (180) meses. NOTA: Penas aumentadas por el artículo 14 de la ley 890 de 2004. (Vigencia desde el 1° de enero de 2005)

## 9060 · Ley 80 de 1993 (Estatuto General de Contratacion de la Administracion Publica) · articulo 5

**Categoria:** Contratacion estatal y facturacion

**Pregunta:** Soy contratista del municipio y me piden firmar actas de recibo de obras que todavia no se han hecho.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 5o. DE LOS DERECHOS Y DEBERES DE LOS CONTRATISTAS. Para la realización de los fines de que trata el artículo 3o. de esta ley, los contratistas: 1o. Tendrán derecho a recibir oportunamente la remuneración pactada y a que el valor intrínseco de la misma no se altere o modifique durante la vigencia del contrato. En consecuencia tendrán derecho, previa solicitud, a que la administración les restablezca el equilibrio de la ecuación económica del contrato a un punto de no pérdida por la ocurrencia de situaciones imprevistas que no sean imputables a los contratistas. Si dicho equilibrio se rompe por incumplimiento de la entidad estatal contratante, tendrá que restablecerse la ecuación surgida al momento del nacimiento del contrato. 2o. Colaborarán con las entidades contratantes en lo que sea necesario para que el objeto contratado se cumpla y que éste sea de la mejor calidad; acatarán las ordenes que durante el desarrollo del contrato ellas les impartan y, de manera general, obrarán con lealtad y buena fe en las distintas etapas contractuales, evitando las dilaciones y entrabamientos que pudieran presentarse. 3o. Podrán acudir a las autoridades con el fin de obtener la protección de los derechos derivados del contrato y la sanción para quienes los desconozcan o vulneren. Las autoridades no podrán condicionar la participación en licitaciones o concursos ni la adjudicación, adición o modificación de contratos, como tampoco la cancelación de las sumas adeudadas al contratista, a la renuncia, desistimiento o abandono de peticiones, acciones, demandas y reclamaciones por parte de éste. 4o. Garantizarán la calidad de los bienes y servicios contratados y responderán por ello. 5o. No accederán a peticiones o amenazas de quienes actúen por fuera de la ley con el fin de obligarlos a hacer u omitir algún acto o hecho. Cuando se presenten tales peticiones o amenazas, los contratistas deberán informar inmediatamente de su ocurrencia a la entidad contratante y a las demás autoridades competentes para que ellas adopten las medidas y correctivos que fueren necesarios. El incumplimiento de esta obligación y la celebración de los pactos o acuerdos prohibidos, dará lugar a la declaratoria de caducidad del contrato.

## 9060 · Ley 80 de 1993 (Estatuto General de Contratacion de la Administracion Publica) · articulo 26

**Categoria:** Contratacion estatal y facturacion

**Pregunta:** Soy contratista del municipio y me piden firmar actas de recibo de obras que todavia no se han hecho.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 26. DEL PRINCIPIO DE RESPONSABILIDAD. En virtud de este principio: 1o. Los servidores públicos están obligados a buscar el cumplimiento de los fines de la contratación, a vigilar la correcta ejecución del objeto contratado y a proteger los derechos de la entidad, del contratista y de los terceros que puedan verse afectados por la ejecución del contrato. 2o. Los servidores públicos responderán por sus actuaciones y omisiones antijurídicas y deberán indemnizar los daños que se causen por razón de ellas. 3o. Las entidades y los servidores públicos, responderán cuando hubieren abierto licitaciones o concursos sin haber elaborado previamente los correspondientes pliegos de condiciones, términos de referencia, diseños, estudios, planos y evaluaciones que fueren necesarios, o cuando los pliegos de condiciones o términos de referencia hayan sido elaborados en forma incompleta, ambigua o confusa que conduzcan a interpretaciones o decisiones de carácter subjetivo por parte de aquellos. 4o. Las actuaciones de los servidores públicos estarán presididas por las reglas sobre administración de bienes ajenos y por los mandatos y postulados que gobiernan una conducta ajustada a la ética y a la justicia. 5o. La responsabilidad de la dirección y manejo de la actividad contractual y la de los procesos de selección será del j efe o representante de la entidad estatal quien no podrá trasladarla a las juntas o consejos directivos de la entidad, ni a las corporaciones de elección popular, a los comités asesores, ni a los organismos de control y vigilancia de la misma. 6o. Los contratistas responderán cuando formulen propuestas en las que se fijen condiciones económicas y de contratación artificialmente bajas con el propósito de obtener la adjudicación del contrato. 7o. Los contratistas responderán por haber ocultado al contratar, inhabilidades, incompatibilidades o prohibiciones, o por haber suministrado información falsa. 8o. Los contratistas responderán y la entidad velará por la buena calidad del objeto contratado.

## 9060 · Ley 80 de 1993 (Estatuto General de Contratacion de la Administracion Publica) · articulo 52

**Categoria:** Contratacion estatal y facturacion

**Pregunta:** Soy contratista del municipio y me piden firmar actas de recibo de obras que todavia no se han hecho.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 52. DE LA RESPONSABILIDAD DE LOS CONTRATISTAS. Los contratistas responderán civil y penalmente por sus acciones y omisiones en la actuación contractual en los términos de la ley. Los consorcios y uniones temporales responderán por las acciones y omisiones de sus integrantes, en los términos del artículo 7o. de esta ley.

## 9062 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 17

**Categoria:** Pensiones y seguridad social

**Pregunta:** Trabaje quince anos con varios empleadores y en mi historia laboral faltan semanas.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 17. Obligatoriedad de las Cotizaciones. Durante la vigencia de la relación laboral y del contrato de prestación de servicios, deberán efectuarse cotizaciones obligatorias a los regímenes del sistema general de pensiones por parte de los afiliados, los empleadores y contratistas con base en el salario o ingresos por prestación de servicios que aquellos devenguen. La obligación de cotizar cesa al momento en que el afiliado reúna los requisitos para acceder a la pensión mínima de vejez, o cuando el afiliado se pensione por invalidez o anticipadamente. Lo anterior sin perjuicio de los aportes voluntarios que decida continuar efectuando el afiliado o el empleador en los dos regímenes. Parágrafo. La Unidad Administrativa Especial de Gestión Pensional y Contribuciones Parafiscales de la Protección Social (UGPP), y la Administradora Colombiana de Pensiones (Colpensiones), suprimirán los trámites y procedimientos de cobro de las deudas a cargo de las entidades públicas del orden nacional que formen parte del Presupuesto General de la Nación, obligadas a pagar aportes patronales al Sistema de Seguridad Social en Pensiones, originadas en reliquidaciones y ajustes pensionales derivados de fallos ejecutoriados, que hayan ordenado la inclusión de factores salariales no contemplados en el ingreso base de cotización previsto en la normatividad vigente al momento del reconocimiento de la pensión. En todo caso las entidades de que trata esta disposición, efectuarán los respectivos reconocimientos contables y las correspondientes anotaciones en sus estados financieros. Los demás cobros que deban realizarse en materia de reliquidación pensional como consecuencia de una sentencia judicial, deberá efectuarse con base en la metodología actuarial que se establezca para el efecto por parte del Ministerio de Hacienda y Crédito Público.

## 9062 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 22

**Categoria:** Pensiones y seguridad social

**Pregunta:** Trabaje quince anos con varios empleadores y en mi historia laboral faltan semanas.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 22. Obligaciones del Empleador. El empleador será responsable del pago de su aporte y del aporte de los trabajadores a su servicio. Para tal efecto, descontará del salario de cada afiliado, al momento de su pago, el monto de las cotizaciones obligatorias y el de las voluntarias que expresamente haya autorizado por escrito el afiliado, y trasladará estas sumas a la entidad elegida por el trabajador, junto con las correspondientes a su aporte, dentro de los plazos que para el efecto determine el Gobierno. El empleador responderá por la totalidad del aporte aun en el evento de que no hubiere efectuado el descuento al trabajador.

## 9062 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 23

**Categoria:** Pensiones y seguridad social

**Pregunta:** Trabaje quince anos con varios empleadores y en mi historia laboral faltan semanas.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 23. Sanción Moratoria. Los aportes que no se consignen dentro de los plazos señalados para el efecto, generarán un interés moratorio a cargo del empleador, igual al que rige para el impuesto sobre la renta y complementarios. Estos intereses se abonarán en el fondo de reparto correspondiente o en las cuentas individuales de ahorro pensional de los respectivos afiliados, según sea el caso. Los ordenadores del gasto de las entidades del sector público que sin justa causa no dispongan la consignación oportuna de los aportes, incurrirán en causal de mala conducta, que será sancionada con arreglo al régimen disciplinario vigente. En todas las entidades del sector público será obligatorio incluir en el presupuesto las partidas necesarias para el pago del aporte patronal a la Seguridad Social, como requisito para la presentación, trámite y estudio por parte de la autoridad correspondiente.

## 9062 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 24

**Categoria:** Pensiones y seguridad social

**Pregunta:** Trabaje quince anos con varios empleadores y en mi historia laboral faltan semanas.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 24. Acciones de Cobro. Corresponde a las entidades administradoras de los diferentes regímenes adelantar las acciones de cobro con motivo del incumplimiento de las obligaciones del empleador de conformidad con la reglamentación que expida el Gobierno Nacional. Para tal efecto, la liquidación mediante la cual la administradora determine el valor adeudado, prestará mérito ejecutivo. CAPITULO IV FONDO DE SOLIDARIDAD PENSIONAL

## 9062 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 33

**Categoria:** Pensiones y seguridad social

**Pregunta:** Trabaje quince anos con varios empleadores y en mi historia laboral faltan semanas.

**Estado:** recuperado=no · partido en 4 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 33. Requisitos para Obtener la Pensión de Vejez. Para tener el derecho a la Pensión de Vejez, el afiliado deberá reunir las siguientes condiciones: - 1. Haber cumplido cincuenta y cinco (55) años de edad si es mujer o sesenta (60) años si es hombre. A partir del 1º de enero del año 2014 la edad se incrementará a cincuenta y siete (57) años de edad para la mujer, y sesenta y dos (62) años para el hombre. - 2. Haber cotizado un mínimo de mil (1000) semanas en cualquier tiempo. A partir del 1º de enero del año 2005 el número de semanas se incrementará en 50 y a partir del 1º de enero de 2006 se incrementará en 25 cada año hasta llegar a 1.300 semanas en el año 2015. Parágrafo 1º. Para efectos del cómputo de las semanas a que se refiere el presente artículo, se tendrá en cuenta: - a) El número de semanas cotizadas en cualquiera de los dos regímenes del sistema general de pensiones; - b) El tiempo de servicio como servidores públicos remunerados, incluyendo los tiempos servidos en regímenes exceptuados; - c) El tiempo de servicio como trabajadores vinculados con empleadores que antes de la vigencia de la Ley 100 de 1993 tenían a su cargo el reconocimiento y pago de la pensión, siempre y cuando la vinculación laboral se encontrara vigente o se haya iniciado con posterioridad a la vigencia de la Ley 100 de 1993. - d) El tiempo de servicios como trabajadores vinculados con aquellos empleadores que por omisión no hubieren afiliado al trabajador. - e) El número de semanas cotizadas a cajas previsionales del sector privado que antes de la Ley 100 de 1993 tuviesen a su cargo el reconocimiento y pago de la pensión. En los casos previstos en los literales b), c), d) y e), el cómputo será procedente siempre y cuando el empleador o la caja, según el caso, trasladen, con base en el cálculo actuarial, la suma correspondiente del trabajador que se afilie, a satisfacción de la entidad administradora, el cual estará representado por un bono o título pensional. Los fondos encargados reconocerán la pensión en un tiempo no superior a cuatro (4) meses después de radicada la solicitud por el peticionario, con la correspondiente documentación que acredite su derecho. Los Fondos no podrán aducir que las diferentes cajas no les han expedido el bono pensional o la cuota parte. Parágrafo 2º. Para los efectos de las disposiciones contenidas en la presente ley, se entiende por semana cotizada el periodo de siete (7) días calendario. La facturación y el cobro de los aportes se harán sobre el número de días cotizados en cada período. Parágrafo 3º. Se considera justa causa para dar por terminado el contrato de trabajo o la relación legal o reglamentaria, que el trabajador del sector privado o servidor público cumpla con los requisitos establecidos en este artículo para tener derecho a la pensión. El empleador podrá dar por terminado el contrato de trabajo o la relación legal o reglamentaria, cuando sea reconocida o notificada la pensión por parte de las administradoras del sistema general de pensiones. Transcurridos treinta (30) días después de que el trabajador o servidor público cumpla con los requisitos establecidos en este artículo para tener derecho a la pensión, si este no la solicita, el empleador podrá solicitar el reconocimiento de la misma en nombre de aquel. Lo dispuesto en este artículo rige para todos los trabajadores o servidores públicos afiliados al sistema general de pensiones. Parágrafo 4º. Se exceptúan de los requisitos establecidos en los numerales 1 y 2 del presente artículo, las personas que padezcan una deficiencia física, síquica o sensorial del 50% o más, que cumplan 55 años de edad y que hayan cotizado en forma continua o discontinua 1000 o más semanas al régimen de seguridad social establecido en la Ley 100 de 1993. La madre trabajadora cuyo hijomenor de 18 años padezca invalidez física o mental, debidamente calificada y hasta tanto permanezca en este estado y continúe como dependiente de la madre, tendrá derecho a recibir la pensión especial de vejez a cualquier edad, siempre que haya cotizado al Sistema General de Pensiones cuando menos el mínimo de semanas exigido en el régimen de prima media para acceder a la pensión de vejez. Este beneficio se suspenderá si la trabajadora se reincorpora a la fuerza laboral. Si la madre ha fallecido y el padre tiene la patria potestad del menor inválido, podrá pensionarse con los requisitos y en las condiciones establecidas en este artículo.

## 9063 · Ley 1437 de 2011 (CPACA) · articulo 74

**Categoria:** Pensiones y seguridad social

**Pregunta:** Me pensionaron por un valor mucho menor al que yo calculaba y no me explican el calculo.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 74.Recursos contra los actos administrativos. Por regla general, contra los actos definitivos procederán los siguientes recursos: - 1. El de reposición, ante quien expidió la decisión para que la aclare, modifique, adicione o revoque. - 2. El de apelación, para ante el inmediato superior administrativo o funcional con el mismo propósito. No habrá apelación de las decisiones de los Ministros, Directores de Departamento Administrativo, superintendentes y representantes legales de las entidades descentralizadas ni de los directores u organismos superiores de los órganos constitucionales autónomos. Tampoco serán apelables aquellas decisiones proferidas por los representantes legales y jefes superiores de las entidades y organismos del nivel territorial. - 3. El de queja, cuando se rechace el de apelación. El recurso de queja es facultativo y podrá interponerse directamente ante el superior del funcionario que dictó la decisión, mediante escrito al que deberá acompañarse copia de la providencia que haya negado el recurso. De este recurso se podrá hacer uso dentro de los cinco (5) días siguientes a la notificación de la decisión. Recibido el escrito, el superior ordenará inmediatamente la remisión del expediente, y decidirá lo que sea del caso.

## 9063 · Ley 1437 de 2011 (CPACA) · articulo 76

**Categoria:** Pensiones y seguridad social

**Pregunta:** Me pensionaron por un valor mucho menor al que yo calculaba y no me explican el calculo.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 76.Oportunidad y presentación. Los recursos de reposición y apelación deberán interponerse por escrito en la diligencia de notificación personal, o dentro de los diez (10) días siguientes a ella, o a la notificación por aviso, o al vencimiento del término de publicación, según el caso. Los recursos contra los actos presuntos podrán interponerse en cualquier tiempo, salvo en el evento en que se haya acudido ante el juez. Los recursos se presentarán ante el funcionario que dictó la decisión, salvo lo dispuesto para el de queja, y si quien fuere competente no quisiere recibirlos podrán presentarse ante el procurador regional o ante el personero municipal, para que ordene recibirlos y tramitarlos, e imponga las sanciones correspondientes, si a ello hubiere lugar. El recurso de apelación podrá interponerse directamente, o como subsidiario del de reposición y cuando proceda será obligatorio para acceder a la jurisdicción. Los recursos de reposición y de queja no serán obligatorios.

## 9063 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 21

**Categoria:** Pensiones y seguridad social

**Pregunta:** Me pensionaron por un valor mucho menor al que yo calculaba y no me explican el calculo.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 21. Ingreso Base de Liquidación. Se entiende por ingreso base para liquidar las pensiones previstas en esta Ley, el promedio de los salarios o rentas sobre los cuales ha cotizado el afiliado durante los 10 años anteriores al reconocimiento de la pensión, o en todo el tiempo si éste fuere inferior para el caso de las pensiones de invalidez o sobrevivencia, actualizados anualmente con base en la variación del índice de precios al consumidor, según certificación que expida el DANE. Cuando el promedio del ingreso base, ajustado por inflación, calculado sobre los ingresos de toda la vida laboral del trabajador, resulte superior al previsto en el inciso anterior, el trabajador podrá optar por este sistema, siempre y cuando haya cotizado 1250 semanas como mínimo.

## 9063 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 34

**Categoria:** Pensiones y seguridad social

**Pregunta:** Me pensionaron por un valor mucho menor al que yo calculaba y no me explican el calculo.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 34. Monto de la Pensión de Vejez. El monto mensual de la pensión de vejez, correspondiente a las primeras 1.000 semanas de cotización, será equivalente al 65% del ingreso base de liquidación. Por cada 50 semanas adicionales a las 1.000 hasta las 1.200 semanas, este porcentaje se incrementará en un 2%, llegando a este tiempo de cotización al 73% del ingreso base de liquidación. Por cada 50 semanas adicionales a las 1.200 hasta las 1.400, este porcentaje se incrementará en 3% en lugar del 2%, hasta completar un monto máximo del 85% del ingreso base de liquidación. El valor total de la pensión no podrá ser superior al 85% del ingreso base de liquidación, ni inferior a la pensión mínima de que trata el artículo siguiente. A partir del 1º de enero del año 2004 se aplicarán las siguientes reglas: El monto mensual de la pensión correspondiente al número de semanas mínimas de cotización requeridas, será del equivalente al 65%, del ingreso base de liquidación de los afiliados. Dicho porcentaje se calculará de acuerdo con la fórmula siguiente: r = 65.50 - 0.50 s, donde: r =porcentaje del ingreso de liquidación. s = número de salarios mínimos legales mensuales vigentes. A partir del 2004, el monto mensual de la pensión de vejez será un porcentaje que oscilará entre el 65 y el 55% del ingreso base de liquidación de los afiliados, en forma decreciente en función de su nivel de ingresos calculado con base en la fórmula señalada. El 1º de enero del año 2005 el número de semanas se incrementará en 50 semanas. Adicionalmente, el 1º de enero de 2006 se incrementarán en 25 semanas cada año hasta llegar a 1.300 semanas en el año 2015. A partir del 2005, por cada cincuenta (50) semanas adicionales a las mínimas requeridas, el porcentaje se incrementará en un 1.5% del ingreso base de liquidación, llegando a un monto máximo de pensión entre el 80 y el 70.5% de dicho ingreso, en forma decreciente en función del nivel de ingresos de cotización, calculado con base en la fórmula establecida en el presente artículo. El valor total de la pensión no podrá ser superior al ochenta (80%) del ingreso base de liquidación, ni inferior a la pensión mínima.

## 9066 · Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana) · articulo 135

**Categoria:** Licencias urbanisticas

**Pregunta:** Mi vecino amplio su casa invadiendo el antejardin y la alcaldia no responde mis quejas.

**Estado:** recuperado=no · partido en 7 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTÍCULO 135. Comportamientos contrarios a la integridad urbanística. Los siguientes comportamientos, relacionados con bienes inmuebles de particulares, bienes fiscales, bienes de uso público y el espacio público, son contrarios a la convivencia pues afectan la integridad urbanística y por lo tanto no deben realizarse, según la modalidad señalada: A) Parcelar, urbanizar, demoler, intervenir o construir: 1. En áreas protegidas o afectadas por el plan vial o de infraestructura de servicios públicos domiciliarios, y las destinadas a equipamientos públicos. 2. Con desconocimiento a lo preceptuado en la licencia. 3. En bienes de uso público y terrenos afectados al espacio público. 4. En terrenos aptos para estas actuaciones, sin licencia o cuando esta hubiere caducado B) Actuaciones en los inmuebles declarados de conservación e interés cultural, histórico, urbanístico, paisajístico y arquitectónico. 5. Demoler sin previa autorización o licencia. 6. Intervenir o modificar sin la licencia 7. Incumplir las obligaciones para su adecuada conservación. 8. Realizar acciones que puedan generar impactos negativos en el bien de interés cultural, tales como intervenciones estructurales, arquitectónicas, adecuaciones funcionales, intervenciones en las zonas de influencia y/o en los contextos del inmueble que puedan afectar las características y los valores culturales por los cuales los inmuebles se declararon como bien de interés cultural. C) Usar o destinar un inmueble a: 9. Uso diferente al señalado en la licencia de construcción. 10. Ubicación diferente a la señalada en la licencia de construcción. 11. Contravenir los usos específicos del suelo. 12. Facilitar, en cualquier clase de inmueble, el desarrollo de usos o destinaciones del suelo no autorizados en licencia de construcción o con desconocimiento de las normas urbanísticas sobre usos específicos. D) Incumplir cualquiera de las siguientes obligaciones: 13. Destinar un lugar al interior de la construcción para guardar materiales, maquinaria, escombros o residuos y no ocupar con ellos, ni siquiera de manera temporal, el andén, las vías o espacios públicos circundantes. 14. Proveer de unidades sanitarias provisionales para el personal que labora y visita la obra y adoptar las medidas requeridas para mantenerlas aseadas, salvo que exista una solución viable, cómoda e higiénica en el área. 15. Instalar protecciones o elementos especiales en los frentes y costados de la obra y señalización, semáforos o luces nocturnas para la seguridad de quienes se movilizan por el lugar y evitar accidentes o incomodidades. 16. Limpiar las llantas de los vehículos que salen de la obra para evitar que se arroje barro o cemento en el espacio público. 17. Limpiar el material, cemento y los residuos de la obra, de manera inmediata, cuando caigan en el espacio público. 18. Retirar los andamios, barreras, escombros y residuos de cualquier clase una vez terminada fa obra, cuando esta se suspenda por más de dos (2) meses, o cuando sea necesario por seguridad de la misma. 19. Exigir a quienes trabajan y visitan la obra, el uso de cascos e implementos de seguridad industrial y contar con el equipo necesario para prevenir y controlar incendios o atender emergencias de acuerdo con esta ley. 20. Tomar las medidas necesarias para evitar la emisión de partículas en suspensión, provenientes de materiales de construcción, demolición o desecho, de conformidad con las leyes vigentes. 21. Aislar completamente las obras de construcción que se desarrollen aledañas a canales o fuentes de agua, para evitar la contaminación del agua con materiales e implementar las acciones de prevención y mitigación que disponga la autoridad ambiental respectiva 22. Reparar los daños o averías que en razón de la obra se realicen en el andén, las vías, espacios y redes de servicios públicos. 23. Reparar los daños, averías o perjuicios causados a bienes colindantes o cercanos. 24. Demoler, construir o reparar obras en el horario comprendido entre las 6 de la tarde y las 8 de la mañana, como también los días festivos, en zonas residenciales. PARÁGRAFO 1. Cuando se trate de construcciones en terrenos no aptos o sin previa licencia se impondrán de inmediato la medida de suspensión de construcción o demolición, y se solicitará a las empresas de servicios públicos domiciliarios la suspensión de los servicios correspondientes si no hubiese habitación. PARÁGRAFO 2. Cuando se realice actuación urbanística sin previa licencia en predios aptos para estos menesteres, sin perjuicio de la medida de multa y de la suspensión temporal de la obra, se concederá un término de sesenta (60) días para que el infractor solicite el reconocimiento de la construcción ante la autoridad competente del distrito o municipio; si pasado este término no presenta licencia de reconocimiento, no podrá reanudar la obra y se duplicará el valor de la multa impuesta. PARÁGRAFO 3. Las reparaciones locativas no requieren licencia o autorización; en el caso de bienes de interés cultural las reparaciones locativas no requieren licencia o autorización siempre y cuando estas correspondan a las enunciadas en el artículo 26 de la Resolución número 0983 de 2010 emanada por el Ministerio de Cultura o la norma que la modifique o sustituya. PARÁGRAFO 4. En el caso de demolición o intervención de los bienes de interés cultural, de uno colindante, uno ubicado en su área de influencia o un bien arqueológico, previo a la expedición de la licencia, se deberá solicitar la autorización de intervención de la autoridad competente. PARÁGRAFO 5. Cuando el infractor incumple la orden de demolición, mantenimiento o reconstrucción, una vez agotados todos los medios de ejecución posibles, la administración realizará la actuación urbanística omitida a costa del infractor. PARÁGRAFO 6. Para los casos que se generen con base en los numerales 5 al 8, la autoridad de policía deberá tomar las medidas correctivas necesarias para hacer cesar la afectación al bien de Interés Cultural y remitir el caso a la autoridad cultural que lo declaró como tal, para que esta tome y ejecute las medidas correctivas pertinentes de acuerdo al procedimiento y medidas establecidas en la Ley 397 de 1997 modificada por la Ley 1185 de 2008. La medida correctiva aplicada por la autoridad de policía se mantendrá hasta tanto la autoridad cultural competente resuelva de fondo el asunto. PARÁGRAFO 7. Quien incurra en uno o más de los comportamientos antes señalados, será objeto de la aplicación de las siguientes medidas correctivas: COMPORTAMIENTOS Y MEDIDA CORRECTIVA A APLICAR: Numeral 1: Multa especial por infracción urbanística; Demolición de obra; Construcción, cerramiento, reparación o mantenimiento de inmueble; Remoción de bienes. Numeral 2: Multa especial por infracción urbanística; Demolición de obra; Construcción, cerramiento, reparación o mantenimiento de inmueble, Remoción de bienes. Numeral 3: Multa especial por infracción urbanística; Demolición de obra; Construcción, cerramiento, reparación o mantenimiento de inmueble; Remoción de bienes. Numeral 4: Multa especial por infracción urbanística; Demolición de obra; Construcción, cerramiento, reparación o mantenimiento de inmueble; Remoción de bienes. Numeral 5: Multa especial por infracción urbanística; Suspensión temporal de actividad. Numeral 6: Multa especial por infracción urbanística; Suspensión temporal de actividad. Numeral 7: Multa especial por infracción urbanística; Suspensión temporal de actividad. Numeral 8: Multa especial por infracción urbanística; Suspensión temporal de la actividad. Numeral 9: Multa especial por infracción urbanística; Suspensión definitiva de la actividad. Numeral 10: Multa especial por infracción urbanística; Suspensión definitiva de la actividad. Numeral 11: Multa especial por infracción urbanística; Suspensión definitiva de la actividad. Numeral 12: Multa especial por infracción urbanística; Demolición de obra; Construcción, cerramiento, reparación o mantenimiento de inmueble. Numeral 13: Suspensión de construcción o demolición. Numeral 14: Suspensión de construcción o demolición. Numeral 15: Suspensión de construcción o demolición. Numeral 16: Suspensión de construcción o demolición. Numeral 17: Suspensión de construcción o demolición. Numeral 18: Suspensión de construcción o demolición; Remoción de bienes. Numeral 19: Suspensión de construcción o demolición. Numeral 20: Suspensión de construcción o demolición. Numeral 21: Suspensión de construcción o demolición. Numeral 22: Suspensión de construcción o demolición; Reparación de daños materiales de muebles o inmuebles; Reparación de daños materiales por perturbación a la posesión Numeral 23: y tenencia de inmuebles o muebles Suspensión de construcción o demolición; Reparación de daños materiales de muebles o inmuebles; Reparación de daños materiales por perturbación a la posesión Numeral 24: y tenencia de inmuebles o muebles. Suspensión de construcción o demolición. (Corregido por el Art. 10 del Decreto 555 de 2017)

## 9066 · Ley 1801 de 2016 (Codigo Nacional de Seguridad y Convivencia Ciudadana) · articulo 140

**Categoria:** Licencias urbanisticas

**Pregunta:** Mi vecino amplio su casa invadiendo el antejardin y la alcaldia no responde mis quejas.

**Estado:** recuperado=no · partido en 6 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTÍCULO 140. Comportamientos contrarios al cuidado e integridad del espacio público. Los siguientes comportamientos son contrarios al cuidado e integridad del espacio público y por lo tanto no deben efectuarse. 1. Omitir el cuidado y mejoramiento de las áreas públicas mediante el mantenimiento, aseo y enlucimiento de las fachadas, jardines y antejardines de las viviendas y edificaciones de uso privado. 2. Realizar obras de construcción o remodelación en las vías vehiculares o peatonales, en parques, espacios públicos, corredores de transporte público, o similares, sin la debida autorización de la autoridad competente. 3. Alterar, remover, dañar o destruir el mobiliario urbano o rural tales como semáforos, señalización vial, teléfonos públicos, hidrantes, estaciones de transporte, faroles o elementos de iluminación, bancas o cestas de basura. (Declarado EXEQUIBLE mediante Sentencia de la Corte Constitucional C-211 de 2017) 4. Ocupar el espacio público en violación de las normas vigentes (Declarado EXEQUIBLE mediante Sentencia de la Corte Constitucional C-211 de 2017) (Ver Sentencia de la Corte Constitucional C-472 de 2019) 5. Ensuciar, dañar o hacer un uso indebido o abusivo de los bienes fiscales o de uso público o contrariar los reglamentos o manuales pertinentes. 6. Promover o facilitar el uso u ocupación del espacio público en violación de las normas y jurisprudencia constitucional vigente. (Expresión subrayada, declarada EXEQUIBLE mediante Sentencia de la Corte Constitucional C-489 de 2019) 7. Consumir bebidas alcohólicas, sustancias psicoactivas o prohibidas en estadios, coliseos, centros deportivos, parques, hospitales, centros de salud y en general, en el espacio público, excepto en las actividades autorizadas por la autoridad competente. (Expresiones subrayadas, declaradas INEXEQUIBLES mediante Sentencia de la Corte Constitucional C-253 de 2019) (Expresiones subrayadas, declaradas INHIBIDAS para emitir un pronunciamiento, mediante Sentencia de la Corte Constitucional C-489 de 2019) 8. Portar sustancias prohibidas en el espacio público. 9. Escribir o fijar en lugar público o abierto al público, postes, fachadas, antejardines, muros, paredes, elementos físicos naturales, tales como piedras y troncos de árbol, de propiedades públicas o privadas, leyendas, dibujos, grafitis, sin el debido permiso, cuando éste se requiera o incumpliendo la normatividad vigente. 10. Drenar o verter aguas residuales al espacio público, en sectores que cuentan con el servicio de alcantarillado de aguas servidas y en caso de no contar con este, hacerlo incumpliendo la indicación de las autoridades. 11. Realizar necesidades fisiológicas en el espacio público. 12. Fijar en espacio público propaganda, avisos o pasacalles, pancartas, pendones, vallas o banderolas, sin el debido permiso o incumpliendo las condiciones establecidas en la normatividad vigente. 13. Consumir, portar, distribuir, ofrecer o comercializar sustancias psicoactivas, inclusive la dosis personal, en el perímetro de centros educativos; además al interior de centros deportivos, y en parques. También, corresponderá a la Asamblea o Consejo de Administración regular la prohibición del consumo de sustancias psicoactivas en determinadas áreas de las zonas comunes en conjuntos residenciales o las unidades de propiedad horizontal de propiedades horizontales, en los términos de la Ley 675 de 2001. (Numeral 13, adicionado por el Art. 3 de la Ley 2000 de 2019) 14. Consumir, portar, distribuir, ofrecer o comercializar sustancias psicoactivas, incluso la dosis personal, en áreas o zonas del espacio público, tales como zonas históricas o declaradas de interés cultural, u otras establecidas por motivos de interés público, que sean definidas por el alcalde del municipio. La delimitación de estas áreas o zonas debe obedecer a principios de razonabilidad y proporcionalidad. (Numeral 14, adicionado por el Art. 3 de la Ley 2000 de 2019) PARÁGRAFO 1. Las empresas de servicios públicos pueden ocupar de manera temporal el espacio público para la instalación o mantenimiento de redes y equipamientos, con el respeto de las calidades ambientales y paisajísticas del lugar, y la respectiva licencia de intervención expedida por la autoridad competente. PARÁGRAFO 2. Quien incurra en uno o más de los comportamientos señalados será objeto de la aplicación de las siguientes medidas, sin perjuicio de la responsabilidad penal que se genere bajo el Título XIII del Código Penal. COMPORTAMIENTOS Y MEDIDA CORRECTIVA A APLICAR: Numeral 1: Construcción, cerramiento, reparación o mantenimiento de inmueble. Numeral 2: Multa General tipo 3 Numeral 3: Multa General tipo 4; Reparación de daños materiales de muebles o inmuebles; Construcción, cerramiento, reparación o mantenimiento de inmuebles. Numeral 4: Multa General tipo 1 (Declarado EXEQUIBLE mediante Sentencia de la Corte Constitucional C-211 de 2017) Numeral 5: Multa General tipo 3; Reparación de daños materiales de muebles o inmuebles; Construcción, cerramiento, reparación o mantenimiento de inmueble. Numeral 6: Multa General tipo 4; Remoción de bienes. Numeral 7: Multa General tipo 2; Destrucción de bien. Participación en programa comunitario o actividad pedagógica de convivencia y remisión a los Centros de Atención en Drogadicción (CAD) y Servicios de Farmacodependencia a que se refiere la Ley 1566 Numeral 8: de 2012 Multa General tipo 2; Destrucción de bien. Numeral 9: Multa General tipo 2, Reparación de daños materiales de muebles o inmuebles; Construcción, cerramiento, reparación o mantenimiento de inmueble. Numeral 10: Multa General tipo 4. Numeral 11: Multa General tipo 4; Participación en programa comunitario o actividad pedagógica de convivencia. Numeral 12: Multa especial por contaminación visual; Reparación de daños materiales de muebles o inmuebles; Construcción, cerramiento, reparación o mantenimiento de Numeral 13: inmueble; Remoción de bienes; Destrucción de bien. Multa General tipo 4; Destrucción del bien. Numeral 14: Multa General tipo 4; Destrucción del bien. (Parágrafo 2, modificado por el Art. 3 de la Ley 2000 de 2019) (Declarado EXEQUIBLE mediante Sentencia de la Corte Constitucional C-211 de 2017) PARÁGRAFO 3. Cuando el comportamiento de ocupación indebida del espacio público a que se i refiere el numeral 4 del presente artículo, se realice dos (2) veces o más, se impondrá, además de la medida correctiva prevista en el parágrafo anterior, el decomiso o la destrucción del bien con que se incurra en tal ocupación. PARÁGRAFO 4. En relación con el numeral 9 del presente artículo bajo ninguna circunstancia el ejercicio del grafiti, justificará por sí solo, el uso de la fuerza, ni la incautación de los instrumentos para su realización.” (Corregido por el Art. 11 del Decreto 555 de 2017) DE LA LIBERTAD DE MOVILIDAD Y CIRCULACIÓN CAPÍTULO I CIRCULACIÓN Y DERECHO DE VÍA

## 9066 · Ley 388 de 1997 (Ley de Ordenamiento Territorial) · articulo 99

**Categoria:** Licencias urbanisticas

**Pregunta:** Mi vecino amplio su casa invadiendo el antejardin y la alcaldia no responde mis quejas.

**Estado:** recuperado=no · partido en 5 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 99. Licencias. Se introducen las siguientes modificaciones y adiciones a las normas contenidas en la Ley 9º de 1989 y en el Decreto-ley 2150 de 1995 en materia de licencias urbanísticas: - 1. Para adelantar obras de construcción, ampliación, modificación, adecuación, reforzamiento estructural, restauración, reconstrucción, cerramiento y demolición de edificaciones, y de urbanización, parcelación, loteo o subdivisión de predios localizados en terrenos urbanos, de expansión urbana y rurales, se requiere de manera previa a su ejecución la obtención de la licencia urbanística correspondiente. Igualmente se requerirá licencia para la ocupación del espacio público con cualquier clase de amoblamiento. La licencia urbanística es el acto administrativo de carácter particular y concreto, expedido por el curador urbano o la autoridad municipal o distrital competente, por medio del cual se autoriza específicamente a adelantar obras de urbanización y parcelación de predios, de construcción, ampliación, modificación, adecuación, reforzamiento estructural, restauración, reconstrucción, cerramiento y demolición de edificaciones, de intervención y ocupación del espacio público, y realizar el loteo o subdivisión de predios. El otorgamiento de la licencia urbanística implica la adquisición de derechos de desarrollo y construcción en los términos y condiciones contenidos en el acto administrativo respectivo, así como la certificación del cumplimiento de las normas y demás reglamentaciones en que se fundamenta, y conlleva la autorización específica sobre uso y aprovechamiento del suelo en tanto esté vigente o cuando se haya cumplido con todas las obligaciones establecidas en la misma. Las modificaciones de licencias vigentes se resolverán con fundamento en las normas urbanísticas y demás reglamentaciones que sirvieron de base para su expedición. - 2. Dichas licencias se otorgarán con sujeción al Plan de Ordenamiento Territorial, planes parciales y a las normas urbanísticas que los desarrollan y complementan y de acuerdo con lo dispuesto en la Ley 99 de 1993 y en su reglamento, no se requerirá licencia o plan de manejo ambiental, cuando el plan haya sido expedido de conformidad con lo dispuesto en esta ley. - 3. Las entidades competentes y los curadores urbanos, según sea del caso, tendrán un término de cuarenta y cinco (45) días hábiles para pronunciarse sobre las solicitudes de licencia, contados desde la fecha de la solicitud. Vencidos los plazos sin que las autoridades se hubieren pronunciado, las solicitudes de licencia se entenderán aprobadas en los términos solicitados, quedando obligados el curador y los funcionarios responsables a expedir oportunamente las constancias y certificaciones que se requieran para evidenciar la aprobación del proyecto presentado mediante la aplicación del silencio administrativo positivo. El plazo podrá prorrogarse hasta en la mitad del mismo, mediante resolución motivada, por una sola vez, cuando el tamaño o la complejidad del proyecto lo ameriten. - 4. La invocación del silencio administrativo positivo se someterá al procedimiento previsto en el Código Contencioso Administrativo. - 5. El urbanizador, el constructor, los arquitectos que firman los planos urbanísticos y arquitectónicos y los ingenieros que suscriban los planos técnicos y memorias son responsables de cualquier contravención y violación a las normas urbanísticas, sin perjuicio de la responsabilidad administrativa que se deriven para los funcionarios y curadores urbanos que expidan las licencias sin concordancia o en contravención o violación de las normas correspondientes. - 6. Al acto administrativo que otorga la respectiva licencia le son aplicables en su totalidad las disposiciones sobre revocatoria directa establecidas en el Código Contencioso Administrativo. - 7. El Gobierno Nacional establecerá los documentos que deben acompañar las solicitudes de licencia y la vigencia de las licencias, según su clase. En todo caso, las licencias urbanísticas deberán resolverse exclusivamente con los requisitos fijados por las normas nacionales que reglamentan su trámite, y los municipios y distritos no podrán establecer ni exigir requisitos adicionales a los allí señalados. Parágrafo 1°. Sin perjuicio de los requisitos establecidos para tal efecto, las entidades públicas del municipio o distrito no requerirán licencia para construir, ampliar, modificar, adecuar o reparar inmuebles destinados a usos institucionales, como tampoco para la intervención u ocupación del espacio público, siempre que observen las normas de urbanismo que les sean aplicables. La inobservancia de este último precepto hará disciplinariamente responsable al jefe de la entidad, sin perjuicio de la responsabilidad penal a que haya lugar. Los curadores urbanos o en su defecto la autoridad de planeación, deberán certificar al respecto en forma gratuita, cuando lo soliciten las autoridades encargadas de verificar el cumplimiento de las normas urbanísticas. Parágrafo 2°.Con el fin de evitar los asentamientos humanos en zonas no previstas para tal fin por los planes de ordenamiento territorial, los notarios se abstendrán de correr escrituras de parcelación, subdivisión y loteo, hasta tanto no se allegue por parte del interesado el Certificado de Conformidad con Normas Urbanísticas expedido por la autoridad con jurisdicción en la zona donde se halle ubicado el predio, el cual debe protocolizarse dentro de la escritura. El Gobierno Nacional establecerá las características y condiciones del Certificado de Conformidad con Normas Urbanísticas, el cual tendrá un costo único para cualquier actuación.

## 9066 · Ley 388 de 1997 (Ley de Ordenamiento Territorial) · articulo 103

**Categoria:** Licencias urbanisticas

**Pregunta:** Mi vecino amplio su casa invadiendo el antejardin y la alcaldia no responde mis quejas.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 103. Infracciones urbanísticas. Toda actuación de construcción, ampliación, modificación, adecuación y demolición de edificaciones, de urbanización y parcelación, que contravenga los planes de ordenamiento territorial y las normas urbanísticas que los desarrollan y complementan incluyendo los planes parciales, dará lugar a la imposición de sanciones urbanísticas a los responsables, incluyendo la demolición de las obras, según sea el caso, sin perjuicio de la eventual responsabilidad civil y penal de los infractores. Para efectos de la aplicación de las sanciones estas infracciones se considerarán graves o leves, según se afecte el interés tutelado por dichas normas. Se considera igualmente infracción urbanística, la localización de establecimientos comerciales, industriales, institucionales y de servicios en contravención a las normas de usos del suelo, lo mismo que el encerramiento, la intervención o la ocupación temporal o permanente del espacio público con cualquier tipo de amoblamiento, instalaciones o construcciones, sin la respectiva licencia. "Los municipios y distritos establecerán qué tipo de amoblamiento sobre el espacio público requiere de la licencia a que se refiere este artículo, así como los procedimientos y condiciones para su expedición. En los casos de actuaciones urbanísticas, respecto de las cuales no se acredite la existencia de la licencia correspondiente o que no se ajuste a ella, el alcalde o su delegado, de oficio o a petición de parte, dispondrá la medida policiva de suspensión inmediata de todas las obras respectivas, hasta cuando se acredite plenamente que han cesado las causas que hubieren dado lugar a la medida. En el caso del Distrito Capital, la competencia para adelantar la suspensión de obras a que se refiere este artículo, corresponde a los alcaldes locales, de conformidad con lo dispuesto en el Estatuto Orgánico del Distrito Capital.

## 9068 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 302

**Categoria:** Procedimiento civil - recursos

**Pregunta:** Perdi en primera instancia y mi abogado no apelo dentro del tiempo.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 302. Ejecutoria. Las providencias proferidas en audiencia adquieren ejecutoria una vez notificadas, cuando no sean impugnadas o no admitan recursos. No obstante, cuando se pida aclaración o complementación de una providencia, solo quedará ejecutoriada una vez resuelta la solicitud. Las que sean proferidas por fuera de audiencia quedan ejecutoriadas tres (3) días después de notificadas, cuando carecen de recursos o han vencido los términos sin haberse interpuesto los recursos que fueren procedentes, o cuando queda ejecutoriada la providencia que resuelva los interpuestos.

## 9068 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 322

**Categoria:** Procedimiento civil - recursos

**Pregunta:** Perdi en primera instancia y mi abogado no apelo dentro del tiempo.

**Estado:** recuperado=no · partido en 3 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 322. Oportunidad y requisitos. El recurso de apelación se propondrá de acuerdo con las siguientes reglas: - 1. El recurso de apelación contra cualquier providencia que se emita en el curso de una audiencia o diligencia, deberá interponerse en forma verbal inmediatamente después de pronunciada. El juez resolverá sobre la procedencia de todas las apelaciones al finalizar la audiencia inicial o la de instrucción y juzgamiento, según corresponda, así no hayan sido sustentados los recursos. La apelación contra la providencia que se dicte fuera de audiencia deberá interponerse ante el juez que la dictó, en el acto de su notificación personal o por escrito dentro de los tres (3) días siguientes a su notificación por estado. - 2. La apelación contra autos podrá interponerse directamente o en subsidio de la reposición. Cuando se acceda a la reposición interpuesta por una de las partes, la otra podrá apelar del nuevo auto si fuere susceptible de este recurso. Proferida una providencia complementaria o que niegue la adición solicitada, dentro del término de ejecutoria de esta también se podrá apelar de la principal. La apelación contra una providencia comprende la de aquella que resolvió sobre la complementación. Si antes de resolverse sobre la adición o aclaración de una providencia se hubiere interpuesto apelación contra esta, en el auto que decida aquella se resolverá sobre la concesión de dicha apelación. - 3. En el caso de la apelación de autos, el apelante deberá sustentar el recurso ante el juez que dictó la providencia, dentro de los tres (3) días siguientes a su notificación, o a la del auto que niega la reposición. Sin embargo, cuando la decisión apelada haya sido pronunciada en una audiencia o diligencia, el recurso podrá sustentarse al momento de su interposición. Resuelta la reposición y concedida la apelación, el apelante, si lo considera necesario, podrá agregar nuevos argumentos a su impugnación, dentro del plazo señalado en este numeral. Cuando se apele una sentencia, el apelante, al momento de interponer el recurso en la audiencia, si hubiere sido proferida en ella, o dentro de los tres (3) días siguientes a su finalización o a la notificación de la que hubiere sido dictada por fuera de audiencia, deberá precisar, de manera breve, los reparos concretos que le hace a la decisión, sobre los cuales versará la sustentación que hará ante el superior. Para la sustentación del recurso será suficiente que el recurrente exprese las razones de su inconformidad con la providencia apelada. Si el apelante de un auto no sustenta el recurso en debida forma y de manera oportuna, el juez de primera instancia lo declarará desierto. La misma decisión adoptará cuando no se precisen los reparos a la sentencia apelada, en la forma prevista en este numeral. El juez de segunda instancia declarara desierto el recurso de apelación contra una sentencia que no hubiere sido sustentado. Parágrafo. La parte que no apeló podrá adherir al recurso interpuesto por otra de las partes, en lo que la providencia apelada le fuere desfavorable. El escrito de adhesión podrá presentarse ante el juez que lo profirió mientras el expediente se encuentre en su despacho, o ante el superior hasta el vencimiento del término de ejecutoria del auto que admite apelación de la sentencia. El escrito de adhesión deberá sujetarse a lo previsto en el numeral 3 de este artículo. La adhesión quedará sin efecto si se produce el desistimiento del apelante principal.


---

# Clase C -- redundantes (el caso ya acerto por otro articulo)

46 filas en 19 casos.

## 9002 · Ley 1010 de 2006 (Ley de Acoso Laboral) · articulo 2

**Categoria:** Despido

**Pregunta:** Renuncie a mi trabajo por presion de mi jefe, pero en el papel dice que fue voluntaria, ¿puedo reclamar algo?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTÍCULO 2. Definición y modalidades de acoso laboral. Para efectos de la presente ley se entenderá por acoso laboral toda conducta persistente y demostrable, ejercida sobre un empleado, trabajador por parte de un empleador, un jefe o superior jerárquico inmediato o mediato, un compañero de trabajo o un subalterno, encaminada a infundir miedo, intimidación, terror y angustia, a causar perjuicio laboral, generar desmotivación en el trabajo, o inducir la renuncia del mismo. En el contexto del inciso primero de este artículo, el acoso laboral puede darse, entre otras, bajo las siguientes modalidades generales: 1. Maltrato laboral. Todo acto de violencia contra la integridad física o moral, la libertad física o sexual y los bienes de quien se desempeñe como empleado o trabajador; toda expresión verbal injuriosa o ultrajante que lesione la integridad moral o los derechos a la intimidad y al buen nombre de quienes participen en una relación de trabajo de tipo laboral o todo comportamiento tendiente a menoscabar la autoestima y la dignidad de quien participe en una relación de trabajo de tipo laboral. 2. Persecución laboral: toda conducta cuyas características de reiteración o evidente arbitrariedad permitan inferir el propósito de inducir la renuncia del empleado o trabajador, mediante la descalificación, la carga excesiva de trabajo y cambios permanentes de horario que puedan producir desmotivación laboral. (Ver Sentencia de Octubre 16 de 2014, Rad. 2014-01359 del Consejo de Estado.) 3. Discriminación laboral: (Modificado por el art. 74, Ley 1622 de 2013), todo trato diferenciado por razones de raza, género, origen familiar o nacional, credo religioso, preferencia política o situación social o que carezca de toda razonabilidad desde el punto de vista laboral. 4. Entorpecimiento laboral: toda acción tendiente a obstaculizar el cumplimiento de la labor o hacerla más gravosa o retardarla con perjuicio para el trabajador o empleado constituyen acciones de entorpecimiento laboral, entre otras, la privación, ocultación o inutilización de los insumos, documentos o instrumentos para la labor, la destrucción o pérdida de información, el ocultamiento de correspondencia o mensajes electrónicos. 5. Inequidad laboral: Asignación de funciones a menosprecio del trabajador. 6. Desprotección laboral: Toda conducta tendiente a poner en riesgo la integridad y la seguridad del trabajador mediante órdenes o asignación de funciones sin el cumplimiento de los requisitos mínimos de protección y seguridad para el trabajador. (Ver Sentencias T-882 de 2006)

## 9002 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 64

**Categoria:** Despido

**Pregunta:** Renuncie a mi trabajo por presion de mi jefe, pero en el papel dice que fue voluntaria, ¿puedo reclamar algo?

**Estado:** recuperado=no · partido en 3 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 64. TERMINACION UNILATERAL DEL CONTRATO DE TRABAJO SIN JUSTA CAUSA. En todo contrato de trabajo va envuelta la condición resolutoria por incumplimiento de lo pactado, con indemnización de perjuicios a cargo de la parte responsable. Esta indemnización comprende el lucro cesante y el daño emergente. En caso de terminación unilateral del contrato de trabajo sin justa causa comprobada, por parte del empleador o si éste da lugar a la terminación unilateral por parte del trabajador por alguna de las justas causas contempladas en la ley, el primero deberá al segundo una indemnización en los términos que a continuación se señalan: En los contratos a término fijo, el valor de los salarios correspondientes al tiempo que faltare para cumplir el plazo estipulado del contrato; o el del lapso determinado por la duración de la obra o la labor contratada, caso en el cual la indemnización no será inferior a quince (15) días. En los contratos a término indefinido la indemnización se pagará así: a) Para trabajadores que devenguen un salario inferior a diez (10) salarios mínimos mensuales legales: Treinta (30) días de salario cuando el trabajador tuviere un tiempo de servicio no mayor de un (1) año. Si el trabajador tuviere más de un (1) año de servicio continuo se le pagarán veinte (20) días adicionales de salario sobre los treinta (30) básicos del numeral 1, por cada uno de los años de servicio subsiguientes al primero y proporcionalmente por fracción; b) Para trabajadores que devenguen un salario igual o superior a diez (10), salarios mínimos legales mensuales. Veinte (20) días de salario cuando el trabajador tuviere un tiempo de servicio no mayor de un (1) año. Si el trabajador tuviere más de un (1) año de servicio continuo, se le pagarán quince (15) días adicionales de salario sobre los veinte (20) días básicos del numeral 1 anterior, por cada uno de los años de servicio subsiguientes al primero y proporcionalmente por fracción. PARÁGRAFO TRANSITORIO. Los trabajadores que al momento de entrar en vigencia la presente ley, tuvieren diez (10) o más años al servicio continuo del empleador, se les aplicará la tabla de indemnización establecida en los literales b), c) y d) del artículo 6 de la Ley 50 de 1990, exceptuando el parágrafo transitorio, el cual se aplica únicamente para los trabajadores que tenían diez (10) o más años el primero de enero de 1991. (Modificado por el Art. 28 de la Ley 789 de 2002) (Subrogado por el Art. 6 de la Ley 50 de 1990) (Modificado por el Art. 8 del Decreto 2351 de 1965)

## 9005 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 7

**Categoria:** Garantias de consumo

**Pregunta:** Compre un celular hace 8 meses y ya se daño, la tienda dice que la garantia ya no cubre eso, ¿es cierto?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 7°. Garantía legal. Es la obligación, en los términos de esta ley, a cargo de todo productor y/o proveedor de responder por la calidad, idoneidad, seguridad y el buen estado y funcionamiento de los productos. En la prestación de servicios en el que el prestador tiene una obligación de medio, la garantía está dada, no por el resultado, sino por las condiciones de calidad en la prestación del servicio, según las condiciones establecidas en normas de carácter obligatorio, en las ofrecidas o en las ordinarias y habituales del mercado. Parágrafo. La entrega o distribución de productos con descuento, rebaja o con carácter promocional está sujeta a las reglas contenidas en la presente ley.

## 9031 · Ley 1751 de 2015 (Ley Estatutaria de Salud) · articulo 14

**Categoria:** Salud / EPS

**Pregunta:** Me pidieron dinero adelantado en urgencias de una clinica para atenderme, ¿pueden hacer eso?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 14. Prohibición de la negación de prestación de servicios. Para acceder a servicios y tecnologías de salud no se requerirá ningún tipo de autorización administrativa entre el prestador de servicios y la entidad que cumpla la función de gestión de servicios de salud cuando se trate de atención de urgencia. El Gobierno Nacional definirá los mecanismos idóneos para controlar el uso adecuado y racional de dichos servicios y tecnologías en salud. Parágrafo 1°. En los casos de negación de los servicios que comprenden el derecho fundamental a la salud con independencia a sus circunstancias, el Congreso de la República definirá mediante ley las sanciones penales y disciplinarias, tanto de los Representantes Legales de las entidades a cargo de la prestación del servicio como de las demás personas que contribuyeron a la misma. Parágrafo 2°. Lo anterior sin perjuicio de la tutela.

## 9032 · Constitucion Politica de 1991 · articulo 49

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS dice que el tratamiento que me ordeno el medico no esta cubierto por el plan, ¿ya no hay nada que hacer?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 49. La atención de la salud y el saneamiento ambiental son servicios públicos a cargo del Estado. Se garantiza a todas las personas el acceso a los servicios de promoción, protección y recuperación de la salud. Corresponde al Estado organizar, dirigir y reglamentar la prestación de servicios de salud a los habitantes y de saneamiento ambiental conforme a los principios de eficiencia, universalidad y solidaridad. También, establecer las políticas para la prestación de servicios de salud por entidades privadas, y ejercer su vigilancia y control. Así mismo, establecer las competencias de la Nación, las entidades territoriales y los particulares y determinar los aportes a su cargo en los términos y condiciones señalados en la ley. Los servicios de salud se organizarán en forma descentralizada, por niveles de atención y con participación de la comunidad. La ley señalará los términos en los cuales la atención básica para todos los habitantes será gratuita y obligatoria. Toda persona tiene el deber de procurar el cuidado integral de su salud y la de su comunidad.

## 9032 · Ley 1751 de 2015 (Ley Estatutaria de Salud) · articulo 15

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS dice que el tratamiento que me ordeno el medico no esta cubierto por el plan, ¿ya no hay nada que hacer?

**Estado:** recuperado=no · partido en 3 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 15. Prestaciones de salud. El Sistema garantizará el derecho fundamental a la salud a través de la prestación de servicios y tecnologías, estructurados sobre una concepción integral de la salud, que incluya su promoción, la prevención, la paliación, la atención de la enfermedad y rehabilitación de sus secuelas. En todo caso, los recursos públicos asignados a la salud no podrán destinarse a financiar servicios y tecnologías en los que se advierta alguno de los siguientes criterios: a) Que tengan como finalidad principal un propósito cosmético o suntuario no relacionado con la recuperación o mantenimiento de la capacidad funcional o vital de las personas; b) Que no exista evidencia científica sobre su seguridad y eficacia clínica; c) Que no exista evidencia científica sobre su efectividad clínica; d) Que su uso no haya sido autorizado por la autoridad competente; e) Que se encuentren en fase de experimentación; f) Que tengan que ser prestados en el exterior. Los servicios o tecnologías que cumplan con esos criterios serán explícitamente excluidos por el Ministerio de Salud y Protección Social o la autoridad competente que determine la ley ordinaria, previo un procedimiento técnico-científico, de carácter público, colectivo, participativo y transparente. En cualquier caso, se deberá evaluar y considerar el criterio de expertos independientes de alto nivel, de las asociaciones profesionales de la especialidad correspondiente y de los pacientes que serían potencialmente afectados con la decisión de exclusión. Las decisiones de exclusión no podrán resultar en el fraccionamiento de un servicio de salud previamente cubierto, y ser contrarias al principio de integralidad e interculturalidad. Para ampliar progresivamente los beneficios la ley ordinaria determinará un mecanismo técnico-científico, de carácter público, colectivo, participativo y transparente. Parágrafo 1°. El Ministerio de Salud y Protección Social tendrá hasta dos años para implementar lo señalado en el presente artículo. En este lapso el Ministerio podrá desarrollar el mecanismo técnico, participativo y transparente para excluir servicios o tecnologías de salud. Parágrafo 2°. Sin perjuicio de las acciones de tutela presentadas para proteger directamente el derecho a la salud, la acción de tutela también procederá para garantizar, entre otros, el derecho a la salud contra las providencias proferidas para decidir sobre las demandas de nulidad y otras acciones contencioso administrativas. Parágrafo 3°. Bajo ninguna circunstancia deberá entenderse que los criterios de exclusión definidos en el presente artículo, afectarán el acceso a tratamientos a las personas que sufren enfermedades raras o huérfanas.

## 9032 · Decreto 2591 de 1991 (Reglamentacion de la accion de tutela) · articulo 1

**Categoria:** Salud / EPS

**Pregunta:** Mi EPS dice que el tratamiento que me ordeno el medico no esta cubierto por el plan, ¿ya no hay nada que hacer?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 1º Objeto. Toda persona tendrá acción de tutela para reclamar ante los jueces, en todo momento y lugar, mediante un procedimiento preferente y sumario, por sí misma o por quien actúe a su nombre, la protección inmediata de sus derechos constitucionales fundamentales, cuando quiera que éstos resulten vulnerados o amenazados por la acción o la omisión de cualquier autoridad pública o de los particulares en los casos que señala este Decreto. Todos los días y horas son hábiles para interponer la acción de tutela. La acción de tutela procederá aún bajo los estados de excepción. Cuando la medida excepcional se refiera a derechos, la tutela se podrá ejercer por los menos para defender su contenido esencial, sin perjuicio de las limitaciones que la Constitución autorice y de lo que establezca la correspondiente ley estatutaria de los estados de excepción.

## 9034 · Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana) · articulo 23

**Categoria:** Arriendo

**Pregunta:** Mi arrendador me dijo que tengo que irme en una semana porque quiere el apartamento, ¿tengo que hacerlo?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 23. Requisitos para la terminación unilateral por parte del arrendador mediante preaviso con indemnización. Para que el arrendador pueda dar por terminado unilateralmente el contrato de arrendamiento en el evento previsto en el numeral 7 del artículo anterior, deberá cumplir con los siguientes requisitos: - a) Comunicar a través del servicio postal autorizado al arrendatario o a su representante legal, con la antelación allí prevista, indicando la fecha para la terminación del contrato y, manifestando que se pagará la indemnización de ley; - b) Consignar a favor del arrendatario y a órdenes de la autoridad competente, la indemnización de que trata el artículo anterior de la presente ley, dentro de los tres (3) meses anteriores a la fecha señalada para la terminación unilateral del contrato. La consignación se efectuará en las entidades autorizadas por el Gobierno Nacional para tal efecto y la autoridad competente allegará copia del título respectivo cl arrendatario o le enviará comunicación en que se haga constar tal circunstancia, inmediatamente tenga conocimiento de la misma. El valor de la indemnización se hará con base en la renta vigente a la fecha del preaviso; - c) Al momento de efectuar la consignación se dejará constancia en los respectivos títulos de las causas de la misma como también el nombre y dirección precisa del arrendatario o su representante; - d) Si el arrendatario cumple con la obligación de entregar el inmueble en la fecha señalada, recibirá el pago de la indemnización, de conformidad con la autorización que expida la autoridad competente. Parágrafo 1º. En caso de que el arrendatario no entregue el inmueble, el arrendador tendrá derecho a que se le devuelva la indemnización consignada, sin perjuicio de que pueda iniciar el correspondiente proceso de restitución del inmueble. Parágrafo 2º. Si el arrendador con la aceptación del arrendatario desiste de dar por terminado el contrato de arrendamiento, podrá solicitar a la autoridad competente, la autorización para la devolución de la suma consignada.

## 9034 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 384

**Categoria:** Arriendo

**Pregunta:** Mi arrendador me dijo que tengo que irme en una semana porque quiere el apartamento, ¿tengo que hacerlo?

**Estado:** recuperado=no · partido en 6 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 384. Restitución de inmueble arrendado. Cuando el arrendador demande para que el arrendatario le restituya el inmueble arrendado se aplicarán las siguientes reglas: - 1. Demanda. A la demanda deberá acompañarse prueba documental del contrato de arrendamiento suscrito por el arrendatario, o la confesión de este hecha en interrogatorio de parte extraprocesal, o prueba testimonial siquiera sumaria. - 2. Notificaciones. Para efectos de notificaciones, incluso la del auto admisorio de la demanda, se considerará como dirección de los arrendatarios la del inmueble arrendado, salvo que las partes hayan pactado otra cosa. - 3. Ausencia de oposición a la demanda. Si el demandado no se opone en el término de traslado de la demanda, el juez proferirá sentencia ordenando la restitución. - 4. Contestación, mejoras y consignación. Cuando el demandado alegue mejoras, deberá hacerlo en la contestación de la demanda, y se tramitará como excepción. Si la demanda se fundamenta en falta de pago de la renta o de servicios públicos, cuotas de administración u otros conceptos a que esté obligado el demandado en virtud del contrato, este no será oído en el proceso sino hasta tanto demuestre que ha consignado a órdenes del juzgado el valor total que, de acuerdo con la prueba allegada con la demanda, tienen los cánones y los demás conceptos adeudados, o en defecto de lo anterior, cuando presente los recibos de pago expedidos por el arrendador, correspondientes a los tres (3) últimos períodos, o si fuere el caso los correspondientes de las consignaciones efectuadas de acuerdo con la ley y por los mismos períodos, a favor de aquel. Cualquiera que fuere la causal invocada, el demandado también deberá consignar oportunamente a órdenes del juzgado, en la cuenta de depósitos judiciales, los cánones que se causen durante el proceso en ambas instancias, y si no lo hiciere dejará de ser oído hasta cuando presente el título de depósito respectivo, el recibo del pago hecho directamente al arrendador, o el de la consignación efectuada en proceso ejecutivo. Los cánones depositados en la cuenta de depósitos judiciales se retendrán hasta la terminación del proceso si el demandado alega no deberlos; en caso contrario se entregarán inmediatamente al demandante. Si prospera la excepción de pago propuesta por el demandado, en la sentencia se ordenará devolver a este los cánones retenidos; si no prospera se ordenará su entrega al demandante. Los depósitos de cánones causados durante el proceso se entregarán al demandante a medida que se presenten los títulos, a menos que el demandado le haya desconocido el carácter de arrendador en la contestación de la demanda, caso en el cual se retendrán hasta que en la sentencia se disponga lo procedente. Cuando se resuelva la excepción de pago o la del desconocimiento del carácter de arrendador, se condenará al vencido a pagar a su contraparte una suma igual al treinta por ciento (30%) de la cantidad depositada o debida. Cuando el arrendatario alegue como excepción que la restitución no se ha producido por la renuencia del arrendador a recibir, si el juez la halla probada, le ordenará al arrendador que reciba el bien arrendado y lo condenará en costas. - 5. Compensación de créditos. Si en la sentencia se reconoce al demandado derecho al valor de las mejoras, reparaciones o cultivos pendientes, tal crédito se compensará con lo que aquel adeude al demandante por razón de cánones o de cualquiera otra condena que se le haya impuesto en el proceso. - 6. Trámites inadmisibles. En este proceso son inadmisibles la demanda de reconvención, la intervención excluyente, la coadyuvancia y la acumulación de procesos. En caso de que se propongan el juez las rechazará de plano por auto que no admite recursos. El demandante no estará obligado a solicitar y tramitar la audiencia de conciliación extrajudicial como requisito de procedibilidad de la demanda. - 7. Embargos y secuestros. En todos los procesos de restitución de tenencia por arrendamiento, el demandante podrá pedir, desde la presentación de la demanda o en cualquier estado del proceso, la práctica de embargos y secuestros sobre bienes del demandado, con el fin de asegurar el pago de los cánones de arrendamiento adeudados o que se llegaren a adeudar, de cualquier otra prestación económica derivada del contrato, del reconocimiento de las indemnizaciones a que hubiere lugar y de las costas procesales. Los embargos y secuestros podrán decretarse y practicarse como previos a la notificación del auto admisorio de la demanda a la parte demandada. En todos los casos, el demandante deberá prestar caución en la cuantía y en la oportunidad que el juez señale para responder por los perjuicios que se causen con la práctica de dichas medidas. La parte demandada podrá impedir la práctica de medidas cautelares o solicitar la cancelación de las practicadas mediante la prestación de caución en la forma y en la cuantía que el juez le señale, para garantizar el cumplimiento de la sentencia. Las medidas cautelares se levantarán si el demandante no promueve la ejecución en el mismo expediente dentro de los treinta (30) días siguientes a la ejecutoria de la sentencia, para obtener el pago de los cánones adeudados, las costas, perjuicios, o cualquier otra suma derivada del contrato o de la sentencia. Si en esta se condena en costas el término se contará desde la ejecutoria del auto que las apruebe; y si hubiere sido apelada, desde la notificación del auto que ordene obedecer lo dispuesto por el superior. - 8. Restitución provisional. Cualquiera que fuere la causal de restitución invocada, el demandante podrá solicitar que antes de la notificación del auto admisorio o en cualquier estado del proceso, se practique una diligencia de inspección judicial al inmueble, con el fin de verificar el estado en que se encuentra. Si durante la práctica de la diligencia se llegare a establecer que el bien se encuentra desocupado o abandonado, o en estado de grave deterioro o que pudiere llegar a sufrirlo, el juez, a solicitud del demandante, podrá ordenar, en la misma diligencia, la restitución provisional del bien, el cual se le entregará físicamente al demandante, quien se abstendrá de arrendarlo hasta tanto no se encuentre en firme la sentencia que ordene la restitución del bien. Durante la vigencia de la restitución provisional, se suspenderán los derechos y obligaciones derivados del contrato de arrendamiento a cargo de las partes. - 9. Única instancia. Cuando la causal de restitución sea exclusivamente la mora en el pago del canon de arrendamiento, el proceso se tramitará en única instancia.

## 9036 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 159

**Categoria:** Relaciones laborales

**Pregunta:** Trabajo muchas horas extra y nunca me las han pagado, ¿que puedo hacer?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 159. TRABAJO SUPLEMENTARIO. Trabajo suplementario o de horas extras es el que excede de la jornada ordinaria, y en todo caso el que excede de la máxima legal.

## 9036 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 160

**Categoria:** Relaciones laborales

**Pregunta:** Trabajo muchas horas extra y nunca me las han pagado, ¿que puedo hacer?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 160. TRABAJO ORDINARIO Y NOCTURNO. Trabajo diurno es el que se realiza en el periodo comprendido entre las seis horas (6:00 a. m.) y las veintiún horas (9:00 p. m.). Trabajo nocturno es el que se realiza en el período comprendido entre las veintiún horas (9:00 p. m.) y las seis horas (6:00 a. m.). (Modificado por el Art. 1 de la Ley 1846 de 2017 CAPITULO II. JORNADA MAXIMA.

## 9036 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 179

**Categoria:** Relaciones laborales

**Pregunta:** Trabajo muchas horas extra y nunca me las han pagado, ¿que puedo hacer?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 179. TRABAJO DOMINICAL Y FESTIVO. El trabajo en domingo y festivos se remunerará con un recargo del setenta y cinco por ciento (75%) sobre el salario ordinario en proporción a las horas laboradas. Si con el domingo coincide otro día de descanso remunerado solo tendrá derecho el trabajador, si trabaja, al recargo establecido en el numeral anterior. Se exceptúa el caso de la jornada de treinta y seis (36) horas semanales previstas en el artículo 20 literal c) de la Ley 50 de 1990. PARÁGRAFO 1. El trabajador podrá convenir con el empleador su día de descanso obligatorio el día sábado o domingo, que será reconocido en todos sus aspectos como descanso dominical obligatorio institucionalizado. Interprétese la expresión dominical contenida en el régimen laboral en este sentido exclusivamente para el efecto del descanso obligatorio. Las disposiciones contenidas en los artículos 25 y 26 se aplazarán en su aplicación frente a los contratos celebrados antes de la vigencia de la presente ley hasta el 1o. de abril del año 2003. PARÁGRAFO 2. Se entiende que el trabajo dominical es ocasional cuando el trabajador labora hasta dos domingos durante el mes calendario. Se entiende que el trabajo dominical es habitual cuando el trabajador labore tres o más domingos durante el mes calendario. (Modificado por el Art. 26 de la Ley 789 de 2002) (Modificado por el Art. 29 de la Ley 50 de 1990) (Modificado por el Art. 12 del Decreto 2351 de 1965)

## 9037 · Ley 1010 de 2006 (Ley de Acoso Laboral) · articulo 9

**Categoria:** Relaciones laborales

**Pregunta:** Mi jefe me grita y me humilla delante de mis compañeros todos los dias, ¿es acoso laboral?

**Estado:** recuperado=no · partido en 3 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTÍCULO 9. Medidas preventivas y correctivas del acoso laboral. (Corregido por el Decreto Nacional 231 de 2006.) 1. Los reglamentos de trabajo de las empresas e instituciones deberán prever mecanismos de prevención de las conductas de acoso laboral y establecer un procedimiento interno, confidencial, conciliatorio y efectivo para superar las que ocurran en el lugar de trabajo. Los comités de empresa de carácter bipartito, donde existan, podrán asumir funciones relacionados con acoso laboral en los reglamentos de trabajo. 2. La víctima del acoso laboral podrá poner en conocimiento del Inspector de Trabajo con competencia en el lugar de los hechos, de los Inspectores Municipales de Policía, de los Personeros Municipales o de la Defensoría del Pueblo, a prevención, la ocurrencia de una situación continuada y ostensible de acoso laboral. La denuncia deberá dirigirse por escrito en que se detallen los hechos denunciados y al que se anexa prueba sumaria de los mismos. La autoridad que reciba la denuncia en tales términos conminará preventivamente al empleador para que ponga en marcha los procedimientos confidenciales referidos en el numeral 1 de este artículo y programe actividades pedagógicas o terapias grupales de mejoramiento de las relaciones entre quienes comparten una relación laboral dentro de una empresa. Para adoptar esta medida se escuchará a la parte denunciada. 3. Quien se considere víctima de una conducta de acoso laboral bajo alguna de las modalidades descritas en el artículo 2 de la presente ley podrá solicitar la intervención de una institución de conciliación autorizada legalmente a fin de que amigablemente se supere la situación de acoso laboral. PARÁGRAFO 1. Los empleadores deberán adaptar el reglamento de trabajo a los requerimientos de la presente ley, dentro de los tres (4) meses siguientes a su promulgación, y su incumplimiento será sancionado administrativamente por el Código Sustantivo del Trabajo. El empleador deberá abrir un escenario para escuchar las opiniones de los trabajadores en la adaptación de que trata este parágrafo, sin que tales opiniones sean obligatorias y sin que eliminen el poder de subordinación laboral. Nota: (Textos subrayados Declarados EXEQUIBLES mediante sentencia C-282 de 2007) PARÁGRAFO 2. La omisión en la adopción de medidas preventivas y correctivas de la situación de acoso laboral por parte del empleador o jefes superiores de la administración, se entenderá como tolerancia de la misma. PARÁGRAFO 3. La denuncia a que se refiere el numeral 2 de este artículo podrá acompañarse de la solicitud de traslado a otra dependencia de la misma empresa, si existiera una opción clara en ese sentido, y será sugerida por la autoridad competente como medida correctiva cuando ello fuere posible. (Ver Art. 14, Resolución Min. Protección 2646 de 2008)

## 9040 · Ley 100 de 1993 (Sistema de Seguridad Social Integral) · articulo 167

**Categoria:** Accidentes de transito

**Pregunta:** Tuve un accidente de moto y el hospital dice que el SOAT no cubre mis gastos, ¿es cierto?

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 167. Riesgos Catastróficos y Accidentes de Tránsito. En los casos de urgencias generadas en accidentes de tránsito, en acciones terroristas ocasionadas por bombas o artefactos explosivos, en catástrofes naturales u otros eventos expresamente aprobados por el Consejo Nacional de Seguridad Social en Salud, los afiliados al Sistema General de Seguridad Social en Salud tendrán derecho al cubrimiento de los servicios médico-quirúrgicos, indemnización por incapacidad permanente y por muerte, gastos funerarios y gastos de transporte al centro asistencial. El Fondo de Solidaridad y Garantía pagara directamente a la institución que haya prestado el servicio a las tarifas que establezca el Gobierno Nacional de acuerdo con los criterios del Consejo Nacional de Seguridad Social en Salud. PARAGRAFO 1º. En los casos de accidentes de tránsito, el cubrimiento de los servicios médico-quirúrgicas y demás prestaciones continuara a cargo de las aseguradoras autorizadas para administrar los recursos del Seguro Obligatorio de Accidentes de Tránsito con las modificaciones de esta Ley. PARAGRAFO 2º. Los demás riesgos aquí previstos serán atendidos con cargo a la subcuenta del Fondo de Solidaridad y Garantía, de acuerdo con la reglamentación que establezca el Gobierno Nacional. PARAGRAFO 3º. El Gobierno Nacional reglamentará los procedimientos de cobro y pago de estos servicios. PARAGRAFO 4º. El Sistema General de Seguridad Social en Salud podrá establecer un sistema de reaseguros para el cubrimiento de los riesgos catastróficos.

## 9044 · Ley 84 de 1873 (Codigo Civil) · articulo 411

**Categoria:** Derecho de familia - alimentos

**Pregunta:** Mi ex pareja paga una cuota de alimentos muy baja y ahora mi hija necesita mas, ¿se puede aumentar?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 411. Se deben alimentos: 1) Al cónyuge. 2) A los descendientes legítimos. 3) A los ascendientes legítimos. 4) A cargo del cónyuge culpable, al cónyuge divorciado o separado de cuerpo sin su culpa. 5) A los hijos naturales, su posteridad legítima y a los nietos naturales. 6) A los Ascendientes Naturales. 7) A los hijos adoptivos. 8) A los padres adoptantes. 9) A los hermanos legítimos. 10) Al que hizo una donación cuantiosa si no hubiere sido rescindida o revocada. La acción del donante se dirigirá contra el donatario. No se deben alimentos a las personas aquí designadas en los casos en que una ley se los niegue. 11) A los hijos de crianza. 12) A los padres de crianza. 13) Al cónyuge al que por ocasión de divorcio tramitado bajo la causal 10°, carezca de medios para la subsistencia, siempre y cuando no contraiga un nuevo vínculo matrimonial o una nueva unión marital de hecho. Parágrafo. Los hijos e hijas de crianza deberán alimentos a sus padres o madres de crianza, siempre y cuando, nunca hayan padecido ningún tipo de maltrato físico o psicológico por parte de estos.

## 9044 · Ley 84 de 1873 (Codigo Civil) · articulo 422

**Categoria:** Derecho de familia - alimentos

**Pregunta:** Mi ex pareja paga una cuota de alimentos muy baja y ahora mi hija necesita mas, ¿se puede aumentar?

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Art. 422. Los alimentos que se deben por ley, se entienden concedidos para toda la vida del alimentario, continuando las circunstancias que lejitimaron la demanda. Con todo, ningún varón de aquéllos a quienes sólo se deben alimentos necesarios, podrá pedirlos después que haya cumplido veintiún años, salvo que por algún impedimento corporal o mental, se halle inhabilitado para subsistir de su trabajo; pero si posteriormente se inhabilitare, revivirá la obligación de alimentarle

## 9051 · Ley 1010 de 2006 (Ley de Acoso Laboral) · articulo 7

**Categoria:** Relaciones laborales

**Pregunta:** Mi jefe me paso a turnos de noche de un dia para otro y yo tengo un hijo de dos anos.

**Estado:** recuperado=no · partido en 3 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTÍCULO 7. Conductas que constituyen acoso laboral. Se presumirá que hay acoso laboral si se acredita la ocurrencia repetida y pública de cualquiera de las siguientes conductas: Nota: (Texto subrayado declarado EXEQUIBLE por la Corte Constitucional, mediante Sentencia C-780 de 2007.) a) Los actos de agresión física, independientemente de sus consecuencias; b) Las expresiones injuriosas o ultrajantes sobre la persona, con utilización de palabras soeces o con alusión a la raza, el género, el origen familiar o nacional, la preferencia política o el estatus social; c) Los comentarios hostiles y humillantes de descalificación profesional expresados en presencia de los compañeros de trabajo; d) Las injustificadas amenazas de despido expresadas en presencia de los compañeros de trabajo; e) Las múltiples denuncias disciplinarias de cualquiera de los sujetos activos del acoso, cuya temeridad quede demostrada por el resultado de los respectivos procesos disciplinarios; f) La descalificación humillante y en presencia de los compañeros de trabajo de las propuestas u opiniones de trabajo; g) las burlas sobre la apariencia física o la forma de vestir, formuladas en público; h) La alusión pública a hechos pertenecientes a la intimidad de la persona; i) La imposición de deberes ostensiblemente extraños a las obligaciones laborales, las exigencias abiertamente desproporcionadas sobre el cumplimiento de la labor encomendada y el brusco cambio del lugar de trabajo o de la labor contratada sin ningún fundamento objetivo referente a la necesidad técnica de la empresa; j) La exigencia de laborar en horarios excesivos respecto a la jornada laboral contratada o legalmente establecida, los cambios sorpresivos del turno laboral y la exigencia permanente de laborar en dominicales y días festivos sin ningún fundamento objetivo en las necesidades de la empresa, o en forma discriminatoria respecto a los demás trabajadores o empleados; k) El trato notoriamente discriminatorio respecto a los demás empleados en cuanto al otorgamiento de derechos y prerrogativas laborales y la imposición de deberes laborales; l) La negativa a suministrar materiales e información absolutamente indispensables para el cumplimiento de la labor; m) La negativa claramente injustificada a otorgar permisos, licencias por enfermedad, licencias ordinarias y vacaciones, cuando se dan las condiciones legales, reglamentarias o convencionales para pedirlos; n) El envío de anónimos, llamadas telefónicas y mensajes virtuales con contenido injurioso, ofensivo o intimidatorio o el sometimiento a una situación de aislamiento social. En los demás casos no enumerados en este artículo, la autoridad competente valorará, según las circunstancias del caso y la gravedad de las conductas denunciadas, la ocurrencia del acoso laboral descrito en el artículo 2. Excepcionalmente un sólo acto hostil bastará para acreditar el acoso laboral. La autoridad competente apreciará tal circunstancia, según la gravedad de la conducta denunciada y su capacidad de ofender por sí sola la dignidad humana, la vida e integridad física, la libertad sexual y demás derechos fundamentales. Cuando las conductas descritas en este artículo tengan ocurrencias en privado, deberán ser demostradas por los medios de prueba reconocidos en la ley procesal civil.

## 9051 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 57

**Categoria:** Relaciones laborales

**Pregunta:** Mi jefe me paso a turnos de noche de un dia para otro y yo tengo un hijo de dos anos.

**Estado:** recuperado=no · partido en 5 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 57. OBLIGACIONES ESPECIALES DEL {EMPLEADOR}. Son obligaciones especiales del {empleador}: Poner a disposición de los trabajadores, salvo estipulación en contrario, los instrumentos adecuados y las materias primas necesarias para la realización de las labores. Procurar a los trabajadores locales apropiados y elementos adecuados de protección contra los accidentes y enfermedades profesionales en forma que se garanticen razonablemente la seguridad y la salud. Prestar inmediatamente los primeros auxilios en caso de accidente o de enfermedad. A este efecto en todo establecimiento, taller o fábrica que ocupe habitualmente más de diez (10) trabajadores, deberá mantenerse lo necesario, según reglamentación de las autoridades sanitarias. Pagar la remuneración pactada en las condiciones, períodos y lugares convenidos. Guardar absoluto respeto a la dignidad personal del trabajador, a sus creencias y sentimientos. Conceder al trabajador las licencias necesarias para el ejercicio del sufragio; para el desempeño de cargos oficiales transitorios de forzosa aceptación; en caso de grave calamidad doméstica debidamente comprobada; para desempeñar comisiones sindicales inherentes a la organización o para asistir al entierro de sus compañeros, siempre que avise con la debida oportunidad al {empleador} o a su representante y que, en los dos (2) últimos casos, el número de los que se ausenten no sea tal que perjudique el funcionamiento de la empresa. En el reglamento de trabajo se señalarán las condiciones para las licencias antedichas. Salvo convención en contrario, el tiempo empleado en estas licencias puede descontarse al trabajador o compensarse con tiempo igual de trabajo efectivo en horas distintas de su jornada ordinaria, a opción del {empleador}. (Aparte tachado INEXEQUIBLE, el resto del numeral CONDICIONALMENTE EXEQUIBLE) Dar al trabajador que lo solicite, a la expiración de contrato, una certificación en que consten el tiempo de servicio, la índole de la labor y el salario devengado; e igualmente, si el trabajador lo solicita, hacerle practicar examen sanitario y darle certificación sobre el particular, si al ingreso o durante la permanencia en el trabajo hubiere sido sometido a examen médico. Se considera que el trabajador, por su culpa, elude, dificulta o dilata el examen, cuando transcurrido cinco (5) días a partir de su retiro no se presenta donde el médico respectivo para la práctica del examen, a pesar de haber recibido la orden correspondiente. Pagar al trabajador los gastos razonables de venida y de regreso, si para prestar sus servicios lo hizo cambiar de residencia, salvo si la terminación del contrato se origina por culpa o voluntad del trabajador. Si el trabajador prefiere radicarse en otro lugar, el {empleador} le debe costear su traslado hasta la concurrencia de los gastos que demandaría su regreso al lugar donde residía anteriormente. En los gastos de traslado del trabajador, se entienden comprendidos los de los familiares que con el convivieren; y Cumplir el reglamento y mantener el orden, la moralidad y el respeto a las leyes. al trabajador en caso de fallecimiento de su cónyuge, compañero o compañera permanente o de un familiar hasta el grado segundo de consanguinidad, primero de afinidad y primero civil, una licencia remunerada por luto de cinco (5) días hábiles, cualquiera sea su modalidad de contratación o de vinculación laboral. La grave calamidad doméstica no incluye la Licencia por Luto que trata este numeral. Este hecho deberá demostrarse mediante documento expedido por la autoridad competente, dentro de los treinta (30) días siguientes a su ocurrencia. (Aparte subrayado declarado EXEQUIBLE, en el entendido que también incluye a los parientes del trabajador en el segundo grado civil, por la Corte Constitucional mediante Sentencia C-892-12) (Numeral 10 adicionado por el Art. 1 de la Ley 1280 de 2009) PARÁGRAFO. Las EPS tendrán la obligación de prestar la asesoría psicológica a la familia. Conceder en forma oportuna a la trabajadora en estado de embarazo, la licencia remunerada consagrada en el numeral 1 del artículo 236, de forma tal que empiece a disfrutarla de manera obligatoria una (1) semana antes o dos (2) semanas antes de la fecha probable del parto, según decisión de la futura madre conforme al certificado médico a que se refiere el numeral 3 del citado artículo 236. (Numeral 11 adicionado por el Art. 3 de la Ley 1468 de 2011) Conceder la licencia de 10 días hábiles para el cuidado de la niñez, al padre, madre o quien detente la custodia y cuidado personal de los menores de edad que padezcan una enfermedad terminal o cuadro clínico severo derivado de un accidente grave y requieran un cuidado permanente; o requiera cuidados paliativos para el control del dolor y otros síntomas. (Numeral 12 adicionado por el Art. 4 de la Ley 2174 de 2021)

## 9051 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 158

**Categoria:** Relaciones laborales

**Pregunta:** Mi jefe me paso a turnos de noche de un dia para otro y yo tengo un hijo de dos anos.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 158. JORNADA ORDINARIA. La jornada ordinaria de trabajo es la que convengan a las partes, o a falta de convenio, la máxima legal.

## 9051 · Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo) · articulo 160

**Categoria:** Relaciones laborales

**Pregunta:** Mi jefe me paso a turnos de noche de un dia para otro y yo tengo un hijo de dos anos.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> ARTICULO 160. TRABAJO ORDINARIO Y NOCTURNO. Trabajo diurno es el que se realiza en el periodo comprendido entre las seis horas (6:00 a. m.) y las veintiún horas (9:00 p. m.). Trabajo nocturno es el que se realiza en el período comprendido entre las veintiún horas (9:00 p. m.) y las seis horas (6:00 a. m.). (Modificado por el Art. 1 de la Ley 1846 de 2017 CAPITULO II. JORNADA MAXIMA.

## 9052 · Ley 1266 de 2008 (Habeas data financiero) · articulo 8

**Categoria:** Reporte en centrales de riesgo

**Pregunta:** Pague una deuda hace anos y ahora me la volvieron a reportar como si fuera nueva.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 8º.Deberes de las fuentes de la información. Las fuentes de la información deberán cumplir las siguientes obligaciones, sin perjuicio del cumplimiento de las demás disposiciones previstas en la presente ley y en otras que rijan su actividad: - 1. Garantizar que la información que se suministre a los operadores de los bancos de datos o a los usuarios sea veraz, completa, exacta, actualizada y comprobable. - 2. Reportar, de forma periódica y oportuna al operador, todas las novedades respecto de los datos que previamente le haya suministrado y adoptar las demás medidas necesarias para que la información suministrada a este se mantenga actualizada. - 3. Rectificar la información cuando sea incorrecta e informar lo pertinente a los operadores. - 4. Diseñar e implementar mecanismos eficaces para reportar oportunamente la información al operador. - 5. Solicitar, cuando sea del caso, y conservar copia o evidencia de la respectiva autorización otorgada por los titulares de la información, y asegurarse de no suministrar a los operadores ningún dato cuyo suministro no esté previamente autorizado, cuando dicha autorización sea necesaria, de conformidad con lo previsto en la presente ley. - 6. Certificar, semestralmente al operador, que la información suministrada cuenta con la autorización de conformidad con lo previsto en la presente ley. - 7. Resolver los reclamos y peticiones del titular en la forma en que se regula en la presente ley. - 8. Informar al operador que determinada información se encuentra en discusión por parte de su titular, cuando se haya presentado la solicitud de rectificación o actualización de la misma, con el fin de que el operador incluya en el banco de datos una mención en ese sentido hasta que se haya finalizado dicho trámite. - 9. Cumplir con las instrucciones que imparta la autoridad de control en relación con el cumplimiento de la presente ley. - 10. Los demás que se deriven de la Constitución o de la presente ley. - 11. Reportar la información negativa de los titulares, máximo (18) meses después de la constitución en mora del titular."

## 9052 · Ley 1266 de 2008 (Habeas data financiero) · articulo 16

**Categoria:** Reporte en centrales de riesgo

**Pregunta:** Pague una deuda hace anos y ahora me la volvieron a reportar como si fuera nueva.

**Estado:** recuperado=no · partido en 8 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 16.Peticiones, Consultas y Reclamos. - I. Trámite de consultas. Los titulares de la información o sus causahabientes podrán consultar lainformación personal del titular, que repose en cualquier banco de datos, sea este del sector público o privado. El operador deberá suministrar a estos, debidamente identificados, toda la información contenida en el registro individual o que esté vinculada con la identificación del titular. La petición, consulta de información se formulará verbalmente, por escrito, o por cualquier canal de comunicación, siempre y cuando se mantenga evidencia de la consulta por medios técnicos. La petición o consulta será atendida en un término máximo de diez (10) días hábiles contados a partir de la fecha de recibo de la misma. Cuando no fuere posible atender la petición o consulta dentro de dicho término, se informará al interesado, expresando los motivos de la demora y señalando la fecha en que se atenderá su petición, la cual en ningún caso podrá superar los cinco (5) días hábiles siguientes al vencimiento del primer término. Parágrafo. La petición o consulta se deberá atender de fondo, suministrando integralmente toda la información solicitada. - II. Trámite de reclamos. Los titulares de la información o sus causahabientes que consideren que la información contenida en su registro individual en un banco de datos debe ser objeto de corrección o actualización podrán presentar un reclamo ante el operador, el cual será tramitado bajo las siguientes reglas: - 1. La petición o reclamo se formulará mediante escrito dirigido al operador del banco de datos, con la identificación del titular, la descripción de los hechos que dan lugar al reclamo, la dirección, y si fuere el caso, acompañando los documentos de soporte que se quieran hacer valer. En caso de que el escrito resulte incompleto, se deberá oficiar al interesado para que subsane las fallas. Transcurrido un mes desde la fecha del requerimiento, sin que el solicitante presente la información requerida, se entenderá que ha desistido de la reclamación o petición. - 2. Una vez recibido la petición o reclamo completo el operador incluirá en el registro individual en un término no mayor a dos (2) días hábiles una leyenda que diga "reclamo en trámite" y la naturaleza del mismo. Dicha información deberá mantenerse hasta que el reclamo sea decidido y deberá incluirse en la información que se suministra a los usuarios. - 3. El término máximo para atender la petición o reclamo será de quince (15) días hábiles contados a partir del día siguiente a la fecha de su recibo. Cuando no fuere posible atender la petición dentro de dicho término, se informará al interesado, expresando los motivos de la demora y señalando la fecha en que se atenderá su petición, la cual en ningún caso podrá superar los ocho (8) días hábiles siguientes al vencimiento del primer término. - 4. En los casos en que exista una fuente de información independiente del operador, este último deberá dar traslado del reclamo a la fuente en un término máximo de dos (2) días hábiles, la cual deberá resolver e informar la respuesta al operador en un plazo máximo de diez (10) días hábiles. En todo caso, la respuesta deberá darse al titular por el operador en el término máximo de quince (15) días hábiles contados a partir del día siguiente a la fecha de presentación de la reclamación, prorrogables por ocho (8) días hábiles más, según lo indicado en el numeral anterior. Si el reclamo es presentado ante la fuente, esta procederá a resolver directamente el reclamo, pero deberá informar al operador sobre la recepción del reclamo dentro de los dos (2) días hábiles siguientes a su recibo, de forma que se pueda dar cumplimiento a la obligación de incluir la leyenda que diga "reclamo en trámite" y la naturaleza del mismo dentro del registro individual, lo cual deberá hacer el operador dentro de los dos (2) días hábiles siguientes a haber recibido la información de la fuente. - 5. Para dar respuesta a la petición o reclamo, el operador o la fuente, según sea el caso, deberá realizar una verificación completa de las observaciones o planteamientos del titular, asegurándose de revisar toda la información pertinente para poder dar una respuesta completa al titular. - 6. Sin perjuicio del ejercido de la acción de tutela para amparar el derecho fundamental del habeas data, en caso que el titular no se encuentre satisfecho con la respuesta a la petición, podrá recurrir al proceso judicial correspondiente dentro de los términos legales pertinentes para debatir lo relacionado con la obligación reportada como incumplida. La demanda deberá ser interpuesta contra la fuente de la información la cual, una vez notificada de la misma, procederá a informar al operador dentro de los dos (2) días hábiles siguientes, de forma que se pueda dar cumplimiento a la obligación de incluir la leyenda que diga "información en discusión judicial" y la naturaleza de la misma dentro del registro individual, lo cual deberá hacer el operador dentro de los dos (2) días hábiles siguientes a haber recibido la información de la fuente y por todo el tiempo que tome obtener un fallo en firme. Igual procedimiento deberá seguirse en caso que la fuente inicie un proceso judicial contra el titular de la información, referente a la obligación reportada como incumplida, y éste proponga excepciones de mérito. - 7. De los casos de suplantación. En el caso que el titular de la información manifieste ser víctima del delito de falsedad personal contemplado en el Código Penal, y le sea exigido el pago de obligaciones como resultado de la conducta punible de la que es víctima, deberá presentar petición de corrección ante la fuente adjuntando los soportes correspondientes. La fuente una vez reciba la solicitud, deberá dentro de los diez (10) días siguientes cotejar los documentos utilizados para adquirir la obligación que se disputa, con los documentos allegados por el titular en la petición, los cuales se tendrán como prueba sumaria para probar la falsedad, la fuente, si así lo considera, deberá denunciar el delito de estafa del que haya podido ser víctima. Con la solicitud presentada por el titular, el dato negativo, récord del (scorings-score) y cualquier otro dato que refleje el comportamiento del titular, deberán ser modificados por la fuente reflejando que la víctima de falsedad no es quien adquirió las obligaciones, y se incluirá una leyenda dentro del registro personal que diga -Víctima de Falsedad Personal-. - 8. Silencio. Las peticiones o reclamos deberán resolverse dentro de los quince (15) días hábiles siguientes a la fecha de su recibo. Prorrogables por ocho (8) días hábiles más, según lo indicado en el numeral 3, parte 11, artículo 16 de la presente ley. Si en ese lapso no se ha dado pronta resolución, se entenderá, para todos los efectos legales, que la respectiva solicitud ha sido aceptada. Si no lo hiciere, el peticionario podrá solicitar a la Superintendencia de Industria y Comercio y a la Superintendencia Financiera de Colombia, según el caso, la imposición de las sanciones a que haya lugar conforme a la presente ley, sin perjuicio de que ellas adopten las decisiones que resulten pertinentes para hacer efectivo el derecho al habeas data de los titulares. TITULO VI VIGILANCIA DE LOS DESTINATARIOS DE LA LEY

## 9053 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 98

**Categoria:** Reporte en centrales de riesgo

**Pregunta:** Me reportaron por una deuda de la empresa donde fui representante legal, no es mia.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 98.CONTRATO DE SOCIEDAD - CONCEPTO - PERSONA JURÍDICA DISTINTA. Por el contrato de sociedad dos o más personas se obligan a hacer un aporte en dinero, en trabajo o en otros bienes apreciables en dinero, con el fin de repartirse entre sí las utilidades obtenidas en la empresa o actividad social. La sociedad, una vez constituida legalmente, forma una persona jurídica distinta de los socios individualmente considerados.

## 9053 · Ley 1266 de 2008 (Habeas data financiero) · articulo 7

**Categoria:** Reporte en centrales de riesgo

**Pregunta:** Me reportaron por una deuda de la empresa donde fui representante legal, no es mia.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 7º.Deberes de los operadores de los bancos de datos. Sin perjuicio del cumplimiento de las demás disposiciones contenidas en la presente leyyotras que rijan su actividad, los operadores de los bancos de datos están obligados a: - 1. Garantizar, en todo tiempo al titular de la información, el pleno y efectivo ejercicio del derecho de hábeas datayde petición, es decir, la posibilidad de conocer la información que sobre él exista o repose en el banco de datos, y solicitar la actualización o corrección de datos, todo lo cual se realizará por conducto de los mecanismos de consultas o reclamos, conforme lo previsto en la presente ley. - 2. Garantizar, que en la recolección, tratamiento y circulación de datos, se respetarán los demás derechos consagrados en la ley. - 3. Permitir el acceso a la información únicamente a las personas que, de conformidad con lo previsto en esta ley, pueden tener acceso a ella. - 4. Adoptar un manual interno de políticas y procedimientos para garantizar el adecuado cumplimiento de la presente ley y, en especial, para la atención de consultas y reclamos por parte de los titulares. - 5. Solicitar la certificación a la fuente de la existencia de la autorización otorgada por el titular, cuando dicha autorización sea necesaria, conforme lo previsto en la presente ley. - 6. Conservar con las debidas seguridades los registros almacenados para impedir su deterioro, pérdida, alteración, uso no autorizado o fraudulento. - 7. Realizar periódica y oportunamente la actualización y rectificación de los datos, cada vez que le reporten novedades las fuentes, en los términos de la presente ley. - 8. Tramitar las peticiones, consultas y los reclamos formulados por los titulares de la información, en los términos señalados en la presente ley. - 9. Indicar en el respectivo registro individual que determinada información se encuentra en discusión por parte de su titular, cuando se haya presentado la solicitud de rectificación o actualización de la misma y no haya finalizado dicho trámite, en la forma en que se regula en la presente ley. - 10. Circular la información a los usuarios dentro de los parámetros de la presente ley. - 11. Cumplir las instrucciones y requerimientos que la autoridad de vigilancia imparta en relación con el cumplimiento de la presente ley. - 12. Los demás que se deriven de la Constitución o de la presente ley.

## 9053 · Ley 1266 de 2008 (Habeas data financiero) · articulo 8

**Categoria:** Reporte en centrales de riesgo

**Pregunta:** Me reportaron por una deuda de la empresa donde fui representante legal, no es mia.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 8º.Deberes de las fuentes de la información. Las fuentes de la información deberán cumplir las siguientes obligaciones, sin perjuicio del cumplimiento de las demás disposiciones previstas en la presente ley y en otras que rijan su actividad: - 1. Garantizar que la información que se suministre a los operadores de los bancos de datos o a los usuarios sea veraz, completa, exacta, actualizada y comprobable. - 2. Reportar, de forma periódica y oportuna al operador, todas las novedades respecto de los datos que previamente le haya suministrado y adoptar las demás medidas necesarias para que la información suministrada a este se mantenga actualizada. - 3. Rectificar la información cuando sea incorrecta e informar lo pertinente a los operadores. - 4. Diseñar e implementar mecanismos eficaces para reportar oportunamente la información al operador. - 5. Solicitar, cuando sea del caso, y conservar copia o evidencia de la respectiva autorización otorgada por los titulares de la información, y asegurarse de no suministrar a los operadores ningún dato cuyo suministro no esté previamente autorizado, cuando dicha autorización sea necesaria, de conformidad con lo previsto en la presente ley. - 6. Certificar, semestralmente al operador, que la información suministrada cuenta con la autorización de conformidad con lo previsto en la presente ley. - 7. Resolver los reclamos y peticiones del titular en la forma en que se regula en la presente ley. - 8. Informar al operador que determinada información se encuentra en discusión por parte de su titular, cuando se haya presentado la solicitud de rectificación o actualización de la misma, con el fin de que el operador incluya en el banco de datos una mención en ese sentido hasta que se haya finalizado dicho trámite. - 9. Cumplir con las instrucciones que imparta la autoridad de control en relación con el cumplimiento de la presente ley. - 10. Los demás que se deriven de la Constitución o de la presente ley. - 11. Reportar la información negativa de los titulares, máximo (18) meses después de la constitución en mora del titular."

## 9054 · Ley 84 de 1873 (Codigo Civil) · articulo 2341

**Categoria:** Accidentes de transito

**Pregunta:** Me chocaron el carro estando parqueado y el otro conductor dejo una nota con su numero.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 2341. El que ha cometido un delito o culpa, que ha inferido daño a otro, es obligado a la indemnizacion, sin perjuicio de la pena principal que la lei imponga por la culpa o el delito cometido.

## 9054 · Ley 84 de 1873 (Codigo Civil) · articulo 2356

**Categoria:** Accidentes de transito

**Pregunta:** Me chocaron el carro estando parqueado y el otro conductor dejo una nota con su numero.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 2356. Por regla general todo daño que pueda imputarse a malicia o negligencia de otra persona, debe ser reparado por ésta. Son especialmente obligados a esta reparacion: 1.º El que dispara imprudentemente una arma de fuego. 2.º El que remueve las losas de una acequia o cañería, o las descubre en calle o camino, sin las precauciones necesarias para que no caigan los que por allí transiten de dia o de noche. 3.º El que obligado a la construcción o reparación de un acueducto o fuente, que atraviesa un camino, lo tiene en estado de causar daño a los que transitan por el camino.

## 9054 · Ley 769 de 2002 (Codigo Nacional de Transito) · articulo 143

**Categoria:** Accidentes de transito

**Pregunta:** Me chocaron el carro estando parqueado y el otro conductor dejo una nota con su numero.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 143. Daños materiales. En todo accidente de tránsito donde sólo se causen daños materiales en los que resulten afectados vehículos asegurados no asegurados, inmuebles, cosas o animales y no sé produzcan lesiones personales, los conductores, entidades asegura­doras y demás interesados en el accidente recaudarán todas las pruebas relativas a la colisión mediante la utilización de herramientas técnicas y tecnológicas, que permitan la atención del mismo en forma oportu­na, segura y que garantice la autenticidad, integridad, conservación y posterior consulta y uso probatorio de la información. Para tal efecto, el material probatorio recaudado con estas condiciones reemplazará el informe de accidente de tránsito que expide la autoridad competente. Independientemente de que los vehículos involucrados en un acci­dente de este tipo estén asegurados o no, los conductores deben retirar inmediatamente los vehículos colisionados y todo elemento que pueda interrumpir el tránsito y acudir a los centros de conciliación debidamen­te autorizados por el Ministerio de Justicia y del Derecho. Si fracasa la conciliación, cualquiera de las partes puede acudir a los demás meca­nismos de acceso a la justicia. Para tal efecto, no será necesaria la expe­dición del informe de accidente de tránsito, ni la presencia de autoridad de tránsito en la respectiva audiencia de conciliación.

## 9059 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 37

**Categoria:** Derecho contractual general

**Pregunta:** Firme un contrato de servicios y ahora me cobran una penalidad que no estaba en lo que me mostraron.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 37. Condiciones negociales generales y de los contratos de adhesión. Las Condiciones Negociales Generales y de los contratos de adhesión deberán cumplir como mínimo los siguientes requisitos: - 1. Haber informado suficiente, anticipada y expresamente al adherente sobre la existencia efectos y alcance de las condiciones generales. En los contratos se utilizará el idioma castellano. - 2. Las condiciones generales del contrato deben ser concretas, claras y completas. - 3. En los contratos escritos, los caracteres deberán ser legibles a simple vista y no incluir espacios en blanco, En los contratos de seguros, el asegurador hará entrega anticipada del clausulado al tomador, explicándole el contenido de la cobertura, de las exclusiones y de las garantías. Serán ineficaces y se tendrán por no escritas las condiciones generales de los contratos de adhesión que no reúnan los requisitos señalados en este artículo.

## 9059 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 38

**Categoria:** Derecho contractual general

**Pregunta:** Firme un contrato de servicios y ahora me cobran una penalidad que no estaba en lo que me mostraron.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 38. Cláusulas prohibidas. En los contratos de adhesión, no se podrán incluir cláusulas que permitan al productor y/o proveedor modificar unilateralmente el contrato o sustraerse de sus obligaciones.

## 9059 · Ley 1480 de 2011 (Estatuto del Consumidor) · articulo 42

**Categoria:** Derecho contractual general

**Pregunta:** Firme un contrato de servicios y ahora me cobran una penalidad que no estaba en lo que me mostraron.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 42. Concepto y prohibición. Son cláusulas abusivas aquellas que producen un desequilibrio injustificado en perjuicio del consumidor y las que, en las mismas condiciones, afecten el tiempo, modo o lugar en que el consumidor puede ejercer sus derechos. Para establecer la naturaleza y magnitud del desequilibrio, serán relevantes todas las condiciones particulares de la transacción particular que se analiza. Los productores y proveedores no podrán incluir cláusulas abusivas en los contratos celebrados con los consumidores, En caso de ser incluidas serán ineficaces de pleno derecho.

## 9061 · Ley 1333 de 2009 (Procedimiento sancionatorio ambiental) · articulo 1

**Categoria:** Derecho ambiental sancionatorio

**Pregunta:** La empresa vecina hace ruido toda la noche y dice que tiene permiso ambiental.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 1. Titularidad de la potestad sancionatoria en materia ambiental. El Estado es el titular de la potestad sancionatoria en materia ambiental y lo ejerce sin perjuicio de las competencias legales de otras autoridades a través del Ministerio de Ambiente y Desarrollo sostenible, la Autoridad Nacional de Licencias Ambientales, las Corporaciones Autónomas Regionales, las de Desarrollo Sostenible, las Unidades Ambientales de los grandes centros urbanos a que se refiere el artículo 55 y 66 de la Ley 99 de 1993, los establecimientos públicos ambientales a que se refiere el artículo 13 de la Ley 768 de 2002 y Parques Nacionales Naturales de Colombia, de conformidad con las competencias establecidas por la ley y los reglamentos. Parágrafo. En materia ambiental, se presume la culpa o el dolo del infractor, lo cual dará lugar a las medidas preventivas y sancionatorias. El infractor será sancionado definitivamente si no desvirtúa, en los términos establecidos en la presente Ley, la presunción de culpa o dolo para lo cual tendrá la carga de la prueba y podrá utilizar todos los medios probatorios legales

## 9061 · Ley 1333 de 2009 (Procedimiento sancionatorio ambiental) · articulo 5

**Categoria:** Derecho ambiental sancionatorio

**Pregunta:** La empresa vecina hace ruido toda la noche y dice que tiene permiso ambiental.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 5. Infracciones. Se considera infracción en materia ambiental toda acción u omisión que constituya violación de las normas contenidas en el Código de Recursos Naturales Renovables, Decreto Ley 2811 de 1974, en la Ley 99 de 1993, en la Ley 165 de 1994, las demás normas ambientales vigentes y en los actos administrativos con contenido ambiental expedidos por la autoridad ambiental competente. Será también constitutivo de infracción ambiental la comisión de un daño al medio ambiente, con las mismas condiciones que para configurar la responsabilidad civil extracontractual establece el Código Civil y la legislación complementaria, a saber: El daño, el hecho generador con culpa o dolo y el vínculo causal entre los dos. Cuando estos elementos se configuren darán lugar a una sanción administrativa ambiental, sin perjuicio de la responsabilidad que para terceros pueda generar el hecho en materia civil. Parágrafo 1. En las infracciones ambientales se presume la culpa o dolo del infractor, quien tendrá a su cargo desvirtuarla, en los términos establecidos en la presente Ley. Parágrafo 2. El infractor será responsable ante terceros de la reparación de los daños y perjuicios causados por su acción u omisión. Parágrafo 3. Será también constitutivo de infracción ambiental el tráfico ilegal, maltrato, introducción y trasplante ilegal de animales silvestres, entre otras conductas que causen un darlo al medio ambiente. Parágrafo 4. El incumplimiento de las obligaciones o condiciones previstas en actos administrativos sin contenido ambiental expedidos por la autoridad ambiental competente será objeto de aplicación del artículo 90 de la Ley 1437 de 2011. Se entenderá por obligaciones o condiciones sin contenido ambiental, aquellas cuyo incumplimiento no afecten conocimiento, educación, seguimiento, planificación y control ambiental, las que no hayan sido emitidas para evitar el daño o afectación ambiental, y/o aquellas que no hayan sido impuestas para mitigarlos, compensarlos y restaurarlos. Parágrafo 5. Los actos administrativos con contenido ambiental expedidos por la autoridad ambiental competente como las licencias ambientales, o permisos ambientales, incluye también los planes de contingencia para la mitigación del riesgo y el control de las contingencias ambientales.

## 9064 · Constitucion Politica de 1991 · articulo 23

**Categoria:** Derecho administrativo general

**Pregunta:** Le pedi una informacion a la alcaldia y me respondieron algo que no tiene nada que ver con lo que pregunte.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 23. Toda persona tiene derecho a presentar peticiones respetuosas a las autoridades por motivos de interés general o particular y a obtener pronta resolución. El legislador podrá reglamentar su ejercicio ante organizaciones privadas para garantizar los derechos fundamentales.

## 9064 · Ley 1437 de 2011 (CPACA) · articulo 13

**Categoria:** Derecho administrativo general

**Pregunta:** Le pedi una informacion a la alcaldia y me respondieron algo que no tiene nada que ver con lo que pregunte.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 13.Objeto y modalidades del derecho de petición ante autoridades. Toda persona tiene derecho a presentar peticiones respetuosas a las autoridades, en los términos señalados en este código, por motivos de interés general o particular, y a obtener pronta resolución completa y de fondo sobre la misma. Toda actuación que inicie cualquier persona ante las autoridades implica el ejercicio del derecho de petición consagrado en el artículo 23 de la Constitución Política, sin que sea necesario invocarlo. Mediante él, entre otras actuaciones, se podrá solicitar: el reconocimiento de un derecho, la intervención de una entidad o funcionario, la resolución de una situación jurídica, la prestación de un servicio, requerir información, consultar, examinar y requerir copias de documentos, formular consultas, quejas, denuncias y reclamos e interponer recursos. El ejercicio del derecho de petición es gratuito y puede realizarse sin necesidad de representación a través de abogado, o de persona mayor cuando se trate de menores en relación a las entidades dedicadas a su protección o formación.

## 9064 · Ley 1437 de 2011 (CPACA) · articulo 14

**Categoria:** Derecho administrativo general

**Pregunta:** Le pedi una informacion a la alcaldia y me respondieron algo que no tiene nada que ver con lo que pregunte.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 14.Términos para resolver las distintas modalidades de peticiones. Salvo norma legal especial y so pena de sanción disciplinaria, toda petición deberá resolverse dentro de los quince (15) días siguientes a su recepción. Estará sometida a término especial la resolución de las siguientes peticiones: 1.Las peticiones de documentos y de información deberán resolverse dentro de los diez (10) días siguientes a su recepción. Si en ese lapso no se ha dado respuesta al peticionario, se entenderá, para todos los efectos legales, que la respectiva solicitud ha sido aceptada y, por consiguiente, la administración ya no podrá negar la entrega de dichos documentos al peticionario, y como consecuencia las copias se entregarán dentro de los tres (3) días siguientes. - 2. Las peticiones mediante las cuales se eleva una consulta a las autoridades en relación con las materias a su cargo deberán resolverse dentro de los treinta (30) días siguientes a su recepción. Parágrafo. Cuando excepcionalmente no fuere posible resolver la petición en los plazos aquí señalados, la autoridad debe informar esta circunstancia al interesado, antes del vencimiento del término señalado en la ley expresando los motivos de la demora y señalando a la vez el plazo razonable en que se resolverá o dará respuesta, que no podrá exceder del doble del inicialmente previsto.

## 9065 · Decision 486 de 2000 (Regimen Comun sobre Propiedad Industrial, CAN) · articulo 146

**Categoria:** Propiedad intelectual - marcas

**Pregunta:** Un competidor registro un nombre casi igual al mio y yo llevo anos usandolo sin registrar.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 146.- Dentro del plazo de treinta días siguientes a la fecha de la publicación, quien tenga legítimo interés, podrá presentar, por una sola vez, oposición fundamentada que pueda desvirtuar el registro de la marca. A solicitud de parte, la oficina nacional competente otorgará, por una sola vez un plazo adicional de treinta días para presentar las pruebas que sustenten la oposición. Las oposiciones temerarias podrán ser sancionadas si así lo disponen las normas nacionales. No procederán oposiciones contra la solicitud presentada, dentro de los seis meses posteriores al vencimiento del plazo de gracia a que se refiere el artículo 153, si tales oposiciones se basan en marcas que hubieren coexistido con la solicitada.

## 9065 · Decision 486 de 2000 (Regimen Comun sobre Propiedad Industrial, CAN) · articulo 154

**Categoria:** Propiedad intelectual - marcas

**Pregunta:** Un competidor registro un nombre casi igual al mio y yo llevo anos usandolo sin registrar.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 154.- El derecho al uso exclusivo de una marca se adquirirá por el registro de la misma ante la respectiva oficina nacional competente.

## 9065 · Decision 486 de 2000 (Regimen Comun sobre Propiedad Industrial, CAN) · articulo 172

**Categoria:** Propiedad intelectual - marcas

**Pregunta:** Un competidor registro un nombre casi igual al mio y yo llevo anos usandolo sin registrar.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 172.- La autoridad nacional competente decretará de oficio o a solicitud de cualquier persona y en cualquier momento, la nulidad absoluta de un registro de marca cuando se hubiese concedido en contravención con lo dispuesto en los artículos 134 primer párrafo y 135. La autoridad nacional competente decretará de oficio o a solicitud de cualquier persona, la nulidad relativa de un registro de marca cuando se hubiese concedido en contravención de lo dispuesto en el artículo 136 o cuando éste se hubiera efectuado de mala fe. Esta acción prescribirá a los cinco años contados desde la fecha de concesión del registro impugnado. Las acciones precedentes no afectarán las que pudieran corresponder por daños y perjuicios conforme a la legislación interna. No podrá declararse la nulidad del registro de una marca por causales que hubiesen dejado de ser aplicables al tiempo de resolverse la nulidad. Cuando una causal de nulidad sólo se aplicara a uno o a algunos de los productos o servicios para los cuales la marca fue registrada, se declarará la nulidad únicamente para esos productos o servicios, y se eliminarán del registro de la marca.

## 9067 · Ley 84 de 1873 (Codigo Civil) · articulo 1546

**Categoria:** Contratos empresariales (B2B)

**Pregunta:** El distribuidor esta vendiendo mi producto en una ciudad donde yo le di la exclusividad a otro.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Art. 1546. En los contratos bilaterales va envuelta la condición resolutoria en caso de no cumplirse por uno de los contratantes lo pactado. Pero en tal caso podrá el otro contratante pedir a su arbitrio, o la resolución o el cumplimiento del contrato con indemnización de perjuicios.

## 9067 · Ley 84 de 1873 (Codigo Civil) · articulo 1602

**Categoria:** Contratos empresariales (B2B)

**Pregunta:** El distribuidor esta vendiendo mi producto en una ciudad donde yo le di la exclusividad a otro.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Art. 1602. Todo contrato legalmente celebrado es una lei para los contratantes, i no puede ser invalidado sino por su consentimiento mutuo o por causas legales.

## 9067 · Ley 84 de 1873 (Codigo Civil) · articulo 1613

**Categoria:** Contratos empresariales (B2B)

**Pregunta:** El distribuidor esta vendiendo mi producto en una ciudad donde yo le di la exclusividad a otro.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 1613. La indemnización de perjuicios comprende el daño emergente i lucro cesante, ya provenga de no haberse cumplido la obligación, o de haberse cumplido imperfectamente, o de haberse retardado el cumplimiento. Esceptúanse los casos en que la lei la limita expresamente al daño emergente.

## 9067 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 1317

**Categoria:** Contratos empresariales (B2B)

**Pregunta:** El distribuidor esta vendiendo mi producto en una ciudad donde yo le di la exclusividad a otro.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 1317. AGENCIA COMERCIAL Por medio del contrato de agencia, un comerciante asume en forma independiente y de manera estable el encargo de promover o explotar negocios en un determinado ramo y dentro de una zona prefijada en el territorio nacional, como representante o agente de un empresario nacional o extranjero o como fabricante o distribuidor de uno o varios productos del mismo. La persona que recibe dicho encargo se denomina genéricamente agente.

## 9067 · Decreto 410 de 1971 (Codigo de Comercio) · articulo 1319

**Categoria:** Contratos empresariales (B2B)

**Pregunta:** El distribuidor esta vendiendo mi producto en una ciudad donde yo le di la exclusividad a otro.

**Estado:** recuperado=no · partido en 1 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 1319. EXCLUSIVIDAD A FAVOR DEL AGENCIADO En el contrato de agencia comercial podrá pactarse la prohibición para el agente de promover o explotar, en la misma zona y en el mismo ramo, los negocios de dos o más empresarios competidores.

## 9069 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 133

**Categoria:** Procedimiento civil - recursos

**Pregunta:** Me notificaron por un correo electronico que yo nunca autorice para eso.

**Estado:** recuperado=no · partido en 2 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 133. Causales de nulidad. El proceso es nulo, en todo o en parte, solamente en los siguientes casos: - 1. Cuando el juez actúe en el proceso después de declarar la falta de jurisdicción o de competencia. - 2. Cuando el juez procede contra providencia ejecutoriada del superior, revive un proceso legalmente concluido o pretermite íntegramente la respectiva instancia. - 3. Cuando se adelanta después de ocurrida cualquiera de las causales legales de interrupción o de suspensión, o si, en estos casos, se reanuda antes de la oportunidad debida. - 4. Cuando es indebida la representación de alguna de las partes, o cuando quien actúa como su apoderado judicial carece íntegramente de poder. - 5. Cuando se omiten las oportunidades para solicitar, decretar o practicar pruebas, o cuando se omite la práctica de una prueba que de acuerdo con la ley sea obligatoria. - 6. Cuando se omita la oportunidad para alegar de conclusión o para sustentar un recurso o descorrer su traslado. - 7. Cuando la sentencia se profiera por un juez distinto del que escuchó los alegatos de conclusión o la sustentación del recurso de apelación. - 8. Cuando no se practica en legal forma la notificación del auto admisorio de la demanda a personas determinadas, o el emplazamiento de las demás personas aunque sean indeterminadas, que deban ser citadas como partes, o de aquellas que deban suceder en el proceso a cualquiera de las partes, cuando la ley así lo ordena, o no se cita en debida forma al Ministerio Público o a cualquier otra persona o entidad que de acuerdo con la ley debió ser citado. Cuando en el curso del proceso se advierta que se ha dejado de notificar una providencia distinta del auto admisorio de la demanda o del mandamiento de pago, el defecto se corregirá practicando la notificación omitida, pero será nula la actuación posterior que dependa de dicha providencia, salvo que se haya saneado en la forma establecida en este código. Parágrafo. Las demás irregularidades del proceso se tendrán por subsanadas si no se impugnan oportunamente por los mecanismos que este código establece.

## 9069 · Ley 1564 de 2012 (Codigo General del Proceso) · articulo 291

**Categoria:** Procedimiento civil - recursos

**Pregunta:** Me notificaron por un correo electronico que yo nunca autorice para eso.

**Estado:** recuperado=no · partido en 5 chunk(s)

**Lo que hay que decidir:** ¿Este articulo responde la consulta?

**Texto del articulo:**

> Artículo 291. Práctica de la notificación personal. Para la práctica de la notificación personal se procederá así: - 1. Las entidades públicas se notificarán personalmente en la forma prevista en el artículo 612 de este código. Las entidades públicas se notificarán de las sentencias que se profieran por fuera de audiencia de acuerdo con lo dispuesto en el artículo 203 de la Ley 1437 de 2011. De las que se profieran en audiencia se notificarán en estrados. - 2. Las personas jurídicas de derecho privado y los comerciantes inscritos en el registro mercantil deberán registrar en la Cámara de Comercio o en la oficina de registro correspondiente del lugar donde funcione su sede principal, sucursal o agencia, la dirección donde recibirán notificaciones judiciales. Con el mismo propósito deberán registrar, además, una dirección electrónica. Esta disposición también se aplicará a las personas naturales que hayan suministrado al juez su dirección de correo electrónico. Si se registran varias direcciones, la notificación podrá surtirse en cualquiera de ellas. - 3. La parte interesada remitirá una comunicación a quien deba ser notificado, a su representante o apoderado, por medio de servicio postal autorizado por el Ministerio de Tecnologías de la Información y las Comunicaciones, en la que le informará sobre la existencia del proceso, su naturaleza y la fecha de la providencia que debe ser notificada, previniéndolo para que comparezca al juzgado a recibir notificación dentro de los cinco (5) días siguientes a la fecha de su entrega en el lugar de destino. Cuando la comunicación deba ser entregada en municipio distinto al de la sede del juzgado, el término para comparecer será de diez (10) días; y si fuere en el exterior el término será de treinta (30) días. La comunicación deberá ser enviada a cualquiera de las direcciones que le hubieren sido informadas al juez de conocimiento como correspondientes a quien deba ser notificado. Cuando se trate de persona jurídica de derecho privado la comunicación deberá remitirse a la dirección que aparezca registrada en la Cámara de Comercio o en la oficina de registro correspondiente. Cuando la dirección del destinatario se encuentre en una unidad inmobiliaria cerrada, la entrega podrá realizarse a quien atienda la recepción. La empresa de servicio postal deberá cotejar y sellar una copia de la comunicación, y expedir constancia sobre la entrega de esta en la dirección correspondiente. Ambos documentos deberán ser incorporados al expediente. Cuando se conozca la dirección electrónica de quien deba ser notificado, la comunicación podrá remitirse por el Secretario o el interesado por medio de correo electrónico. Se presumirá que el destinatario ha recibido la comunicación cuando el iniciador recepcione acuse de recibo. En este caso, se dejará constancia de ello en el expediente y adjuntará una impresión del mensaje de datos. - 4. Si la comunicación es devuelta con la anotación de que la dirección no existe o que la persona no reside o no trabaja en el lugar, a petición del interesado se procederá a su emplazamiento en la forma prevista en este código. Cuando en el lugar de destino rehusaren recibir la comunicación, la empresa de servicio postal la dejará en el lugar y emitirá constancia de ello. Para todos los efectos legales, la comunicación se entenderá entregada. - 5. Si la persona por notificar comparece al juzgado, se le pondrá en conocimiento la providencia previa su identificación mediante cualquier documento idóneo, de lo cual se extenderá acta en la que se expresará la fecha en que se practique, el nombre del notificado y la providencia que se notifica, acta que deberá firmarse por aquel y el empleado que haga la notificación. Al notificado no se le admitirán otras manifestaciones que la de asentimiento a lo resuelto, la convalidación de lo actuado, el nombramiento prevenido en la providencia y la interposición de los recursos de apelación y casación. Si el notificado no sabe, no quiere o no puede firmar, el notificador expresará esa circunstancia en el acta. - 6. Cuando el citado no comparezca dentro de la oportunidad señalada, el interesado procederá a practicar la notificación por aviso. Parágrafo 1°. La notificación personal podrá hacerse por un empleado del juzgado cuando en el lugar no haya empresa de servicio postal autorizado o el juez lo estime aconsejable para agilizar o viabilizar el trámite de notificación. Si la persona no fuere encontrada, el empleado dejará la comunicación de que trata este artículo y, en su caso, el aviso previsto en el artículo 292. Parágrafo 2°. El interesado podrá solicitar al juez que se oficie a determinadas entidades públicas o privadas que cuenten con bases de datos para que suministren la información que sirva para localizar al demandado.

