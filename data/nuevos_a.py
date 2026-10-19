"""
Bloque A de la expansion del dataset (v2.0.0): las tres clases que estaban
en 1, 1 y 3 ejemplos.

Cada caso trae su dict `hechos`, que son las cuestiones DE HECHO del relato
codificadas a mano. `construir_dataset.py` corre el motor de reglas sobre esos
hechos y exige que llegue al mismo mecanismo que dice la etiqueta. Si no
coincide, el caso no entra al dataset.

Es el mismo control que descubrio el error de A09 en el eval set, aplicado
ahora como filtro de calidad antes de entrenar: una etiqueta que el motor no
puede derivar del relato es una etiqueta sospechosa.
"""

# --------------------------------------------------------------------------
# HABEAS CORPUS (15 nuevos) -- art. 6.2 D.2591 excluye la tutela
# --------------------------------------------------------------------------
FUND_HC = "art. 28 CP; art. 30 CP; Ley 1095 de 2006; art. 6.2 Decreto 2591 de 1991"
H_HC = {"privacion_libertad": True, "afectacion_individual": True}

HABEAS_CORPUS = [
    {
        "categoria": "hc_captura_sin_orden",
        "relato": "Anoche entraron a la casa y se llevaron a mi hijo. No le mostraron ninguna orden, no estaba haciendo nada, estaba durmiendo. En la estación nos dicen que esperemos a que llegue el investigador del caso.",
        "accionado": "Policía Nacional y Fiscalía",
        "razon": "la captura se hizo sin mandamiento escrito de autoridad judicial competente y sin situación de flagrancia",
        "pretension": "interponer habeas corpus para que se declare ilegal la captura y se ordene la libertad inmediata",
    },
    {
        "categoria": "hc_termino_36_horas",
        "relato": "A mi compañero de trabajo lo cogieron el martes a las seis de la mañana. Ya es jueves al mediodía y no lo han llevado ante ningún juez. En la URI dicen que no hay salas disponibles para la audiencia.",
        "accionado": "Fiscalía General de la Nación",
        "razon": "se superó el término de treinta y seis horas para poner al capturado a disposición del juez competente",
        "pretension": "interponer habeas corpus para que un juez resuelva de inmediato la legalidad de la privación de la libertad",
    },
    {
        "categoria": "hc_redencion_no_aplicada",
        "relato": "El juez ya le reconoció a mi esposo los días de estudio y de trabajo que redimen pena, y con eso la condena se cumplió en agosto. Estamos en octubre y sigue adentro porque dicen que el cómputo no ha bajado del juzgado.",
        "accionado": "Establecimiento penitenciario y juzgado de ejecución de penas",
        "razon": "reconocida la redención, la pena está cumplida y la permanencia en reclusión es una prolongación ilícita de la privación de la libertad",
        "pretension": "interponer habeas corpus para obtener la libertad inmediata",
    },
    {
        "categoria": "hc_libertad_condicional_no_ejecutada",
        "relato": "Hace dos semanas el juez le concedió la libertad condicional a mi hermano y nos dieron copia del auto. La cárcel no lo suelta porque dice que falta un oficio y que eso lo manda el juzgado cuando pueda.",
        "accionado": "Establecimiento penitenciario",
        "razon": "existiendo decisión judicial que concede la libertad, mantener la reclusión por un trámite administrativo prolonga ilícitamente la privación de la libertad",
        "pretension": "interponer habeas corpus para que se materialice la libertad concedida por el juez",
    },
    {
        "categoria": "hc_homonimo",
        "relato": "Capturaron a mi papá por una orden que es de otra persona con el mismo nombre. La cédula no coincide, se lo dijimos en el momento y llevamos los papeles, y de todas formas lleva cuatro días detenido mientras verifican.",
        "accionado": "Policía Nacional y despacho que libró la orden",
        "razon": "la privación de la libertad recae sobre quien no es el destinatario de la orden judicial, de modo que carece de fundamento legal",
        "pretension": "interponer habeas corpus para que se verifique la identidad y se ordene la libertad inmediata",
    },
    {
        "categoria": "hc_detencion_por_deuda",
        "relato": "En el pueblo el inspector mandó encerrar a un señor en el calabozo hasta que pagara una multa de la alcaldía. Lleva dos noches ahí y le dicen que sale cuando aparezca la plata.",
        "accionado": "Inspección de Policía municipal",
        "razon": "la Constitución prohíbe de forma expresa la detención, prisión o arresto por deudas, y la privación la ordenó una autoridad que no es judicial",
        "pretension": "interponer habeas corpus para obtener la libertad inmediata",
    },
    {
        "categoria": "hc_batida_militar",
        "relato": "A mi sobrino lo bajaron de un bus en un retén y se lo llevaron al batallón para definir la situación militar. Lleva ahí desde ayer y no nos dejan verlo ni nos dicen bajo qué orden lo tienen.",
        "accionado": "Unidad militar",
        "razon": "la retención con fines de incorporación al servicio militar no proviene de orden judicial y constituye privación ilegal de la libertad",
        "pretension": "interponer habeas corpus para obtener la libertad inmediata",
    },
    {
        "categoria": "hc_vencimiento_terminos",
        "relato": "Mi hijo lleva dieciocho meses en detención preventiva y la Fiscalía todavía no ha presentado el escrito de acusación. Cada audiencia la aplazan y el abogado dice que ya se vencieron todos los términos.",
        "accionado": "Fiscalía General de la Nación y juzgado de control de garantías",
        "razon": "vencidos los términos legales de la detención preventiva sin que se formule acusación, la privación de la libertad se torna ilegal por prolongación",
        "pretension": "interponer habeas corpus para que se resuelva la libertad por vencimiento de términos",
    },
    {
        "categoria": "hc_adolescente_en_estacion",
        "relato": "A mi hija de dieciséis años la tienen en la estación de policía desde el sábado en la tarde. Es lunes y no la han llevado al juez de infancia. Dicen que el defensor de familia no ha llegado.",
        "accionado": "Policía Nacional y autoridad de infancia y adolescencia",
        "razon": "se superó el término para poner a la adolescente a disposición del juez competente, y su condición de menor refuerza la urgencia del control judicial",
        "pretension": "interponer habeas corpus para que se resuelva de inmediato la legalidad de la privación de la libertad",
    },
    {
        "categoria": "hc_incomunicado",
        "relato": "A mi hermano se lo llevó una patrulla el viernes y nadie nos dice dónde está. Fuimos a tres estaciones y en el sistema no aparece registrado. Ya van tres días sin saber nada de él.",
        "accionado": "Policía Nacional",
        "razon": "la privación de la libertad no está registrada ni sometida a control judicial, lo que la hace ilegal y exige verificación inmediata del paradero",
        "pretension": "interponer habeas corpus para que se establezca el paradero y se verifique la legalidad de la privación de la libertad",
    },
    {
        "categoria": "hc_orden_revocada",
        "relato": "El tribunal revocó la orden de captura contra mi papá en septiembre, tenemos la decisión. Lo cogieron el mes pasado con esa misma orden que ya no existe y sigue detenido mientras confirman.",
        "accionado": "Policía Nacional y despacho judicial",
        "razon": "la orden que sirvió de fundamento a la captura fue revocada, de modo que la privación de la libertad carece de título legal",
        "pretension": "interponer habeas corpus para obtener la libertad inmediata",
    },
    {
        "categoria": "hc_detencion_administrativa",
        "relato": "El secretario de gobierno del municipio ordenó que dejaran encerrado a un vendedor en una celda de la alcaldía por desacatar un operativo. Lleva dos días y ningún juez ha visto el caso.",
        "accionado": "Secretaría de Gobierno municipal",
        "razon": "la privación de la libertad fue ordenada por una autoridad administrativa sin mandamiento judicial, supuesto expreso de privación ilegal",
        "pretension": "interponer habeas corpus para obtener la libertad inmediata",
    },
    {
        "categoria": "hc_sin_flagrancia",
        "relato": "A mi vecino lo capturaron tres días después del robo del que lo acusan, sin orden de nadie, porque alguien dijo que él había sido. No lo cogieron en el momento ni cerca del lugar.",
        "accionado": "Policía Nacional",
        "razon": "no hubo flagrancia ni orden judicial previa, por lo que la captura se realizó sin ninguno de los dos títulos que la Constitución exige",
        "pretension": "interponer habeas corpus para que se declare ilegal la captura y se ordene la libertad",
    },
    {
        "categoria": "hc_boleta_no_tramitada",
        "relato": "El juez firmó la boleta de libertad de mi hijo el jueves. Hoy es miércoles de la semana siguiente y en la cárcel dicen que la boleta no ha entrado al sistema y que no pueden hacer nada hasta que entre.",
        "accionado": "Establecimiento penitenciario",
        "razon": "expedida la orden judicial de libertad, toda permanencia posterior en reclusión constituye prolongación ilícita de la privación de la libertad",
        "pretension": "interponer habeas corpus para que se ejecute de inmediato la orden de libertad",
    },
    {
        "categoria": "hc_retencion_migratoria",
        "relato": "A mi cuñada, que es venezolana, la retuvo Migración en el terminal el lunes por no tener los papeles al día. Es miércoles, sigue en una oficina cerrada con llave y ningún juez ha revisado eso.",
        "accionado": "Migración Colombia",
        "razon": "la retención se extendió más allá de todo término razonable sin control judicial, y la situación migratoria no autoriza una privación de la libertad indefinida",
        "pretension": "interponer habeas corpus para que se verifique la legalidad de la retención y se ordene la libertad",
    },
]

# --------------------------------------------------------------------------
# ACCION DE CUMPLIMIENTO (15 nuevos) -- art. 9 L.393: solo si NO hay
# afectacion individual concreta, porque frente a la tutela es subsidiaria
# --------------------------------------------------------------------------
FUND_AC = "art. 87 CP; Ley 393 de 1997"
H_AC = {"incumplimiento_normativo": True, "afectacion_individual": False}

ACCION_CUMPLIMIENTO = [
    {
        "categoria": "ac_plan_residuos",
        "relato": "Hay un decreto nacional que obliga a cada municipio a adoptar y actualizar su plan de gestión de residuos sólidos. El mío nunca lo adoptó. No es que me hayan negado algo a mí, es que el plan no existe.",
        "accionado": "Alcaldía municipal",
        "razon": "se reclama el acatamiento de un deber impuesto por una norma vigente, sin que se alegue la vulneración concreta de un derecho fundamental de una persona determinada",
        "pretension": "promover acción de cumplimiento para que se adopte el plan de gestión de residuos sólidos",
    },
    {
        "categoria": "ac_comite_etica_hospital",
        "relato": "La norma ordena que todo hospital público tenga conformado un comité de ética hospitalaria. En el hospital del municipio ese comité no se ha conformado nunca. Lo pregunté por escrito y me contestaron que está en proceso.",
        "accionado": "Hospital público municipal",
        "razon": "lo pretendido es la ejecución de una obligación legal de organización institucional, no la protección de un derecho fundamental individual",
        "pretension": "promover acción de cumplimiento para que se conforme el comité de ética hospitalaria",
    },
    {
        "categoria": "ac_senalizacion_vial",
        "relato": "Una resolución del ministerio obliga a las secretarías de tránsito a señalizar las zonas escolares con demarcación y señales verticales. En mi municipio no hay ni una sola zona escolar señalizada, pese a que la resolución es de hace cuatro años.",
        "accionado": "Secretaría de Tránsito municipal",
        "razon": "se persigue el cumplimiento de un mandato normativo de carácter general que la autoridad no ha ejecutado, sin afectación individual concreta",
        "pretension": "promover acción de cumplimiento para que se ejecute la señalización ordenada por la resolución",
    },
    {
        "categoria": "ac_plan_movilidad",
        "relato": "La ley obliga a los municipios de cierto tamaño a formular un plan de movilidad. El mío ya pasó ese tamaño en el censo y sigue sin formularlo. Pedí copia del plan y la respuesta fue que no existe.",
        "accionado": "Alcaldía municipal",
        "razon": "el deber de formular el plan nace de la ley y su incumplimiento es general, sin que se invoque un derecho fundamental propio vulnerado",
        "pretension": "promover acción de cumplimiento para que se formule y adopte el plan de movilidad",
    },
    {
        "categoria": "ac_rendicion_cuentas",
        "relato": "Un decreto obliga a las entidades públicas a hacer una audiencia pública de rendición de cuentas al año. La entidad de mi municipio no ha hecho ninguna en tres años. Ya se lo reclamé por escrito y se ratificaron en que no la van a hacer.",
        "accionado": "Entidad pública municipal",
        "razon": "se reclama el acatamiento de un deber legal de rendición de cuentas, cuya omisión no lesiona de forma concreta un derecho fundamental individual",
        "pretension": "promover acción de cumplimiento para que se realice la audiencia pública de rendición de cuentas",
    },
    {
        "categoria": "ac_banco_leche",
        "relato": "Hay una ley que ordena crear bancos de leche humana en las regiones del país. En mi departamento no se ha creado ninguno y la secretaría de salud responde que no está en el plan de este año.",
        "accionado": "Secretaría de Salud departamental",
        "razon": "lo pretendido es la ejecución de un mandato legal de creación institucional, sin que se alegue la afectación actual de un derecho fundamental de una persona identificable",
        "pretension": "promover acción de cumplimiento para que se dé cumplimiento al mandato de creación del banco de leche humana",
    },
    {
        "categoria": "ac_enlace_victimas",
        "relato": "La ley de víctimas obliga a cada municipio a tener un enlace municipal de víctimas en funcionamiento. En el mío el cargo está en el papel pero nunca se proveyó. Reclamé y respondieron que no hay presupuesto.",
        "accionado": "Alcaldía municipal",
        "razon": "se reclama el cumplimiento de una obligación legal de organización administrativa, no la protección concreta de un derecho fundamental propio",
        "pretension": "promover acción de cumplimiento para que se provea y ponga en funcionamiento el enlace municipal de víctimas",
    },
    {
        "categoria": "ac_politica_discapacidad",
        "relato": "La ley ordena que cada municipio adopte su política pública de discapacidad mediante acuerdo. El mío no la ha adoptado y en el concejo dicen que no se ha radicado el proyecto. No estoy reclamando un servicio para mí, es que la política no se adoptó.",
        "accionado": "Alcaldía municipal y concejo municipal",
        "razon": "el deber de adoptar la política pública es un mandato normativo de alcance general cuyo incumplimiento no se concreta en la vulneración de un derecho individual",
        "pretension": "promover acción de cumplimiento para que se adopte la política pública de discapacidad",
    },
    {
        "categoria": "ac_acto_reubicacion_plaza",
        "relato": "Hay una resolución de la alcaldía, en firme desde el año pasado, que ordena reubicar la plaza de mercado al nuevo lote. La resolución nunca se ejecutó y la administración no ha dicho que la vaya a revocar, simplemente no la cumple.",
        "accionado": "Alcaldía municipal",
        "razon": "existe un acto administrativo en firme que impone un deber concreto a la autoridad y que esta no ejecuta, supuesto propio de la acción de cumplimiento",
        "pretension": "promover acción de cumplimiento para que se ejecute el acto administrativo de reubicación",
    },
    {
        "categoria": "ac_dotacion_bibliotecas",
        "relato": "Una norma fija la dotación mínima que debe tener toda biblioteca pública municipal. La de mi municipio no cumple ni la mitad de esos mínimos. Lo reclamé por escrito y me contestaron ratificando que seguirán así.",
        "accionado": "Alcaldía municipal y secretaría de cultura",
        "razon": "lo que se persigue es el acatamiento de un estándar fijado en una norma vigente, sin que se alegue un derecho fundamental individual vulnerado",
        "pretension": "promover acción de cumplimiento para que se dote la biblioteca conforme a la norma",
    },
    {
        "categoria": "ac_estampilla_destino",
        "relato": "La ordenanza departamental dice que lo recaudado por una estampilla se gira a los hospitales de la red pública. La gobernación lleva dos años recaudando y no ha girado nada. Ya constituí la renuencia por escrito.",
        "accionado": "Gobernación departamental",
        "razon": "se reclama el cumplimiento de un mandato normativo sobre el destino del recaudo, sin que se invoque la vulneración concreta de un derecho fundamental individual",
        "pretension": "promover acción de cumplimiento para que se giren los recursos al destino que fija la ordenanza",
    },
    {
        "categoria": "ac_capacitacion_funcionarios",
        "relato": "Un decreto obliga a las entidades a capacitar cada año a sus funcionarios de atención al ciudadano en lenguaje claro y atención preferente. En la entidad de mi municipio no se ha dictado ninguna capacitación desde que salió el decreto.",
        "accionado": "Entidad pública municipal",
        "razon": "el deber de capacitación proviene de una norma vigente y su omisión es general, sin concretarse en la vulneración de un derecho fundamental de una persona determinada",
        "pretension": "promover acción de cumplimiento para que se realicen las capacitaciones que ordena el decreto",
    },
    {
        "categoria": "ac_reporte_sistema_salud",
        "relato": "Una resolución obliga a las entidades territoriales a reportar mensualmente sus indicadores al sistema de información en salud. Mi departamento no reporta desde hace un año y medio, y cuando se le pidió se ratificó en el incumplimiento.",
        "accionado": "Secretaría de Salud departamental",
        "razon": "se persigue el acatamiento de una obligación legal de reporte, cuya omisión no lesiona de forma concreta un derecho fundamental individual",
        "pretension": "promover acción de cumplimiento para que se efectúen los reportes que ordena la resolución",
    },
    {
        "categoria": "ac_consejo_juventud",
        "relato": "La ley ordena que los municipios convoquen e instalen el consejo municipal de juventud. En el mío nunca se convocó. No es que me hayan excluido a mí, es que el consejo no se ha instalado en ningún momento.",
        "accionado": "Alcaldía municipal",
        "razon": "lo pretendido es la ejecución de un mandato legal de convocatoria e instalación, de alcance general y sin afectación individual concreta",
        "pretension": "promover acción de cumplimiento para que se convoque e instale el consejo municipal de juventud",
    },
    {
        "categoria": "ac_archivo_general",
        "relato": "La ley de archivos obliga a cada entidad a tener su tabla de retención documental convalidada. La alcaldía de mi municipio no la tiene y responde que el archivo está como lo dejaron las administraciones anteriores.",
        "accionado": "Alcaldía municipal",
        "razon": "se reclama el cumplimiento de un deber legal de gestión documental, sin que se alegue la vulneración concreta de un derecho fundamental propio",
        "pretension": "promover acción de cumplimiento para que se elabore y convalide la tabla de retención documental",
    },
]

# --------------------------------------------------------------------------
# ACCION POPULAR (13 nuevos) -- art. 6.3 D.2591 excluye la tutela
# --------------------------------------------------------------------------
H_AP = {"derecho_colectivo": True}

ACCION_POPULAR = [
    {
        "categoria": "ap_espacio_publico_andenes",
        "relato": "En la calle del comercio los almacenes sacaron la mercancía a todo el andén y no queda por dónde pasar. La gente, los coches de bebé y las sillas de ruedas tienen que bajarse a la vía con los carros.",
        "accionado": "Comerciantes y alcaldía municipal",
        "fundamento": "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "lo que se busca proteger es el goce del espacio público y la seguridad de una comunidad indeterminada, derechos colectivos del artículo 4 de la Ley 472",
        "pretension": "promover acción popular para la recuperación del espacio público y el restablecimiento del paso peatonal",
    },
    {
        "categoria": "ap_agua_no_potable",
        "relato": "El acueducto de la vereda entrega el agua sin tratar. Sale turbia y con olor, y en el último año se han enfermado del estómago muchos niños del sector. Somos unas ochenta familias conectadas a esa red.",
        "accionado": "Empresa prestadora del servicio de acueducto y alcaldía municipal",
        "fundamento": "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "la pretensión protege la salubridad pública y el acceso a servicios públicos eficientes de una comunidad indeterminada, excluidos del ámbito de la tutela",
        "pretension": "promover acción popular para que se garantice la potabilidad del agua suministrada",
    },
    {
        "categoria": "ap_moralidad_nomina_paralela",
        "relato": "En la alcaldía hay más de cien contratos de prestación de servicios firmados para hacer el trabajo de los cargos de planta que están vacantes. Los contratos se repartieron entre gente de las campañas y se renuevan cada año.",
        "accionado": "Alcaldía municipal",
        "fundamento": "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "la moralidad administrativa y el patrimonio público son derechos colectivos expresamente protegidos por la acción popular",
        "pretension": "promover acción popular en defensa de la moralidad administrativa y el patrimonio público",
    },
    {
        "categoria": "ap_patrimonio_cultural",
        "relato": "Un constructor está tumbando la casa de la esquina del parque, que está declarada bien de interés cultural del municipio. Ya le quitó el techo y la fachada de bahareque. La secretaría de planeación dice que está revisando.",
        "accionado": "Constructor y secretaría de planeación municipal",
        "fundamento": "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "la defensa del patrimonio cultural de la Nación es un derecho colectivo del artículo 4 de la Ley 472, ajeno al ámbito de la tutela",
        "pretension": "promover acción popular para que cese la demolición y se proteja el bien de interés cultural",
    },
    {
        "categoria": "ap_seguridad_puente",
        "relato": "El puente peatonal por donde cruzan los niños al colegio tiene las vigas con el hierro a la vista y ya se hundió un tramo. Por ahí pasan cientos de personas todos los días y la secretaría de obras solo le puso una cinta.",
        "accionado": "Secretaría de Obras municipal",
        "fundamento": "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "se busca proteger la seguridad pública y la prevención de desastres técnicamente previsibles, derechos colectivos de una comunidad indeterminada",
        "pretension": "promover acción popular para que se intervenga la estructura y se garantice la seguridad del paso peatonal",
    },
    {
        "categoria": "ap_ruido_zona_bares",
        "relato": "En el barrio dejaron funcionar quince bares en tres cuadras. El ruido va hasta las cinco de la mañana los fines de semana y la medición que hizo la autoridad ambiental dio muy por encima del límite. Nadie en el sector duerme.",
        "accionado": "Establecimientos de comercio y alcaldía municipal",
        "fundamento": "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "la afectación recae sobre la salubridad y la tranquilidad públicas de un conjunto indeterminado de habitantes, materia propia de la acción popular",
        "pretension": "promover acción popular para que se haga cumplir la norma de ruido en el sector",
    },
    {
        "categoria": "ap_emisiones_fabrica",
        "relato": "La fábrica de ladrillos que queda arriba del barrio quema con llantas y el humo baja sobre las casas todas las tardes. Los techos y la ropa quedan negros y hay muchos niños con problemas respiratorios en el sector.",
        "accionado": "Empresa ladrillera y autoridad ambiental",
        "fundamento": "art. 79 CP; art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "la pretensión protege el ambiente sano y la salubridad pública de una comunidad indeterminada, derechos colectivos excluidos de la tutela",
        "pretension": "promover acción popular para que cesen las emisiones y se restablezca la calidad del aire",
    },
    {
        "categoria": "ap_mineria_ilegal_rio",
        "relato": "Entraron retroexcavadoras al río y están sacando oro con mercurio. El agua bajó de color, se murieron los peces y de ese río toman agua tres veredas. La corporación ambiental hizo una visita hace ocho meses y no volvió.",
        "accionado": "Explotadores mineros y corporación autónoma regional",
        "fundamento": "art. 79 CP; art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "se protege el ambiente sano, el equilibrio ecológico y la salubridad pública de una comunidad indeterminada, derechos colectivos del artículo 4 de la Ley 472",
        "pretension": "promover acción popular para el cese de la explotación y la recuperación de la fuente hídrica",
    },
    {
        "categoria": "ap_servicio_energia_deficiente",
        "relato": "En el municipio la luz se va todos los días, a veces cuatro y cinco horas. Se han quemado neveras y equipos en muchas casas y los puestos de salud se quedan sin refrigeración para las vacunas. Llevamos dos años así.",
        "accionado": "Empresa prestadora del servicio de energía",
        "fundamento": "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "el acceso a los servicios públicos y a que su prestación sea eficiente y oportuna es un derecho colectivo expresamente enumerado en la Ley 472",
        "pretension": "promover acción popular para que se garantice la prestación continua y eficiente del servicio",
    },
    {
        "categoria": "ap_obra_inconclusa",
        "relato": "El coliseo del municipio se contrató por ocho mil millones, se giraron los anticipos y la obra lleva tres años abandonada con las columnas a medio hacer. El contratista desapareció y la administración no ha ejecutado la póliza.",
        "accionado": "Alcaldía municipal y contratista",
        "fundamento": "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "la defensa del patrimonio público y la moralidad administrativa son derechos colectivos protegidos por la acción popular",
        "pretension": "promover acción popular en defensa del patrimonio público y para que se haga efectiva la garantía contractual",
    },
    {
        "categoria": "ap_salubridad_plaza_mercado",
        "relato": "La plaza de mercado no tiene manejo de residuos. Las canastas de desechos se quedan días en el corredor, hay roedores entre los puestos de carne y el olor llega a las casas de alrededor. Por ahí pasa todo el municipio a comprar.",
        "accionado": "Administración de la plaza de mercado y alcaldía municipal",
        "fundamento": "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "la seguridad y salubridad públicas de una comunidad indeterminada son derechos colectivos, lo que excluye el trámite por tutela",
        "pretension": "promover acción popular para que se implemente el manejo de residuos y se restablezcan las condiciones sanitarias",
    },
    {
        "categoria": "ap_riesgo_ladera",
        "relato": "El barrio está en una ladera que ya se movió dos veces y el estudio de riesgo del municipio lo clasificó como de riesgo alto hace cuatro años. No han hecho ni un muro de contención ni han reubicado a nadie. Son como doscientas casas.",
        "accionado": "Alcaldía municipal y oficina de gestión del riesgo",
        "fundamento": "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "el derecho a la seguridad y a la prevención de desastres previsibles técnicamente es un derecho colectivo de la comunidad asentada en la zona",
        "pretension": "promover acción popular para que se ejecuten las obras de mitigación y el plan de reasentamiento",
    },
    {
        "categoria": "ap_acceso_playa_cerrado",
        "relato": "Un hotel cerró con malla y vigilantes el único camino por el que la gente del pueblo bajaba a la playa. Ahora hay que dar la vuelta por la carretera. Ese camino siempre fue público y lo usaban los pescadores.",
        "accionado": "Hotel y alcaldía municipal",
        "fundamento": "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
        "razon": "el goce del espacio público y la defensa de los bienes de uso público son derechos colectivos del artículo 4 de la Ley 472",
        "pretension": "promover acción popular para la restitución del acceso al bien de uso público",
    },
]


def bloque_a() -> list[dict]:
    """Los 43 casos del bloque, ya con mecanismo, derecho, fundamento y hechos."""
    out = []
    for c in HABEAS_CORPUS:
        out.append({**c, "derecho": "libertad_personal", "mecanismo": "habeas_corpus",
                    "fundamento": c.get("fundamento", FUND_HC), "hechos": dict(H_HC)})
    for c in ACCION_CUMPLIMIENTO:
        out.append({**c, "derecho": "ninguno", "mecanismo": "accion_cumplimiento",
                    "fundamento": c.get("fundamento", FUND_AC), "hechos": dict(H_AC)})
    for c in ACCION_POPULAR:
        out.append({**c, "derecho": "colectivos", "mecanismo": "accion_popular",
                    "hechos": dict(H_AP)})
    for c in out:
        c["procede"] = c["mecanismo"] == "tutela"
    return out
