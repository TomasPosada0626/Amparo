"""
Bloque B de la expansion del dataset (v2.0.0): improcedencia por
subsidiariedad / dano consumado / acto general, y los casos en que la tutela
si procede.

Los 21 de `via_ordinaria` cubren las TRES rutas distintas por las que el
art. 6 del Decreto 2591 de 1991 cierra el paso, no solo la subsidiariedad:

    art. 6.1  existe otro medio judicial idoneo y eficaz en concreto
    art. 6.4  el dano esta consumado y la vulneracion no continua
    art. 6.5  se impugna un acto general, impersonal y abstracto

Y los dos ultimos casos de tutela son la EXCEPCION del art. 6.3: dentro de una
situacion que compromete derechos colectivos, el titular si puede tutelar su
propio derecho cuando se trata de impedir un perjuicio irremediable. Es una de
las siete correcciones que salieron de leer la norma oficial, y el dataset
tiene que ensenarla con ejemplos o el modelo nunca la va a distinguir de una
accion popular.
"""

# --------------------------------------------------------------------------
# VIA ORDINARIA (21 nuevos)
# --------------------------------------------------------------------------
FUND_61 = "art. 6.1 Decreto 2591 de 1991"
FUND_61_CPACA = "art. 6.1 Decreto 2591 de 1991; Ley 1437 de 2011"
FUND_64 = "art. 6.4 Decreto 2591 de 1991"
FUND_65 = "art. 6.5 Decreto 2591 de 1991; Ley 1437 de 2011"

# art. 6.1: hay otro medio, es eficaz en concreto, no hay perjuicio irremediable
H_SUB = {"otro_medio_judicial": True, "medio_eficaz": True,
         "perjuicio_irremediable": False, "afectacion_individual": False}
# art. 6.4: dano consumado que no continua
H_DANO = {"dano_consumado": True, "continua_vulneracion": False}
# art. 6.5: acto general sin acto de aplicacion concreto
H_GRAL = {"acto_general": True, "afectacion_individual": False}

VIA_ORDINARIA = [
    {
        "categoria": "vo_restitucion_arrendamiento",
        "relato": "Le arrendé el apartamento a una señora y lleva siete meses sin pagar. No se quiere ir y me dice que la saque si puedo. Yo necesito el apartamento o al menos el arriendo, vivo de eso.",
        "derecho": "ninguno", "fundamento": FUND_61,
        "accionado": "Arrendataria",
        "razon": "existe el proceso de restitución de inmueble arrendado ante el juez civil, medio específico e idóneo, y no se acredita un perjuicio irremediable",
        "pretension": "acudir a la jurisdicción civil mediante proceso de restitución de inmueble arrendado",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_servidumbre_paso",
        "relato": "El dueño del lote de al lado cerró con alambre el camino por el que yo entraba a mi finca desde hace veinte años. Ahora tengo que dar una vuelta de hora y media para sacar la leche.",
        "derecho": "ninguno", "fundamento": FUND_61,
        "accionado": "Propietario del predio vecino",
        "razon": "la constitución de la servidumbre de tránsito se tramita ante el juez civil, que es el medio idóneo para resolver la controversia entre particulares",
        "pretension": "acudir a la jurisdicción civil para la imposición de servidumbre de tránsito",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_sucesion_herencia",
        "relato": "Mi papá murió hace tres años y dejó una casa y un lote. Somos cinco hermanos y dos no quieren firmar nada ni dejar vender. La casa se está cayendo y nadie puede hacer nada.",
        "derecho": "ninguno", "fundamento": FUND_61,
        "accionado": "Coherederos",
        "razon": "la partición de la herencia se resuelve por el proceso de sucesión, medio judicial específico para ese efecto",
        "pretension": "acudir a la jurisdicción de familia mediante proceso de sucesión",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_union_marital",
        "relato": "Viví con mi compañero dieciocho años sin casarnos. Él murió y su familia dice que yo no tengo derecho a nada de lo que compramos juntos, porque todo quedó a nombre de él.",
        "derecho": "ninguno", "fundamento": FUND_61,
        "accionado": "Familia del causante",
        "razon": "la declaración de la unión marital de hecho y la liquidación de la sociedad patrimonial tienen proceso propio ante el juez de familia",
        "pretension": "acudir a la jurisdicción de familia para la declaración de unión marital de hecho",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_despido_sin_justa_causa",
        "relato": "Me despidieron después de nueve años sin decirme por qué y me pagaron la indemnización de ley. Yo creo que fue por un problema que tuve con el jefe nuevo. No tengo ninguna enfermedad ni fuero.",
        "derecho": "trabajo", "fundamento": "art. 25 CP; " + FUND_61,
        "accionado": "Empleador",
        "razon": "el despido sin justa causa de un trabajador sin fuero se controvierte ante la jurisdicción ordinaria laboral, que es el medio idóneo",
        "pretension": "acudir a la jurisdicción ordinaria laboral mediante proceso ordinario",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_insolvencia_persona_natural",
        "relato": "Quedé debiendo cinco tarjetas y dos créditos de libranza. Me están llamando todos los días y ya me embargaron una cuenta. Tengo trabajo pero no me alcanza para pagar todas las cuotas.",
        "derecho": "ninguno", "fundamento": FUND_61,
        "accionado": "Entidades acreedoras",
        "razon": "para reorganizar las obligaciones existe el procedimiento de insolvencia de persona natural no comerciante, mecanismo específico y eficaz",
        "pretension": "acudir al procedimiento de insolvencia de persona natural no comerciante ante centro de conciliación o notaría",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_responsabilidad_medica",
        "relato": "En la cirugía de mi esposa le cortaron un conducto por error y quedó con una bolsa de por vida. Ya la operaron de nuevo y está estable. Queremos que la clínica responda por lo que le hicieron.",
        "derecho": "ninguno", "fundamento": FUND_64,
        "accionado": "Institución prestadora de salud",
        "razon": "el daño está consumado y lo pretendido es la declaratoria de responsabilidad y la reparación, que no es la finalidad de la tutela",
        "pretension": "acudir a la jurisdicción competente para la declaratoria de responsabilidad y la reparación del daño",
        "hechos": H_DANO,
    },
    {
        "categoria": "vo_contrato_estatal",
        "relato": "Le hice una obra a la alcaldía, está recibida y firmada el acta, y llevan catorce meses sin pagarme los últimos cuarenta millones. Tengo una empresa pequeña pero sigo operando con otros contratos.",
        "derecho": "ninguno", "fundamento": FUND_61_CPACA,
        "accionado": "Alcaldía municipal",
        "razon": "el incumplimiento de un contrato estatal se controvierte por el medio de control de controversias contractuales, y no se acredita afectación del mínimo vital",
        "pretension": "acudir a la jurisdicción contencioso administrativa mediante controversias contractuales",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_impuesto_vehiculo",
        "relato": "La gobernación me está cobrando el impuesto de un carro que vendí hace seis años con traspaso y todo. Metí el recurso, me lo negaron y ahora me llegó cobro coactivo con intereses.",
        "derecho": "ninguno", "fundamento": FUND_61_CPACA,
        "accionado": "Gobernación departamental",
        "razon": "se controvierte la legalidad de un acto administrativo particular, para lo cual existe el medio de control de nulidad y restablecimiento del derecho",
        "pretension": "acudir a la jurisdicción contencioso administrativa mediante nulidad y restablecimiento del derecho",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_comparendo_transito",
        "relato": "Me llegó un comparendo por pasarme un semáforo en una ciudad donde yo no estaba ese día. Fui a la audiencia, el inspector lo confirmó y ahora me toca pagar o no puedo renovar la licencia.",
        "derecho": "ninguno", "fundamento": FUND_61_CPACA,
        "accionado": "Secretaría de Tránsito municipal",
        "razon": "la decisión sancionatoria de tránsito es un acto administrativo controvertible ante la jurisdicción contenciosa por el medio de control correspondiente",
        "pretension": "acudir a la jurisdicción contencioso administrativa mediante nulidad y restablecimiento del derecho",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_periodo_de_prueba",
        "relato": "Me contrataron y a los dos meses, en pleno período de prueba, me dijeron que no seguía. Yo creo que fue injusto porque estaba cumpliendo las metas. No tengo ningún fuero ni problema de salud.",
        "derecho": "trabajo", "fundamento": "art. 25 CP; " + FUND_61,
        "accionado": "Empleador",
        "razon": "la terminación en período de prueba se controvierte ante el juez laboral ordinario, sin que se invoque fuero ni afectación del mínimo vital",
        "pretension": "acudir a la jurisdicción ordinaria laboral mediante proceso ordinario",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_cuotas_copropiedad",
        "relato": "La administración del conjunto me está cobrando cuotas extraordinarias que yo no aprobé y que no aparecen en ninguna acta de asamblea. Me suspendieron el parqueadero hasta que pague.",
        "derecho": "ninguno", "fundamento": FUND_61,
        "accionado": "Administración de la copropiedad",
        "razon": "las controversias de propiedad horizontal tienen trámite propio ante el juez civil, incluida la impugnación de decisiones de la asamblea",
        "pretension": "acudir a la jurisdicción civil para impugnar las decisiones de la copropiedad",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_deslinde_linderos",
        "relato": "El vecino movió la cerca y se metió como diez metros en mi lote. Tengo la escritura con las medidas y él dice que esa cerca siempre estuvo ahí. Ya hablamos y no hay forma de arreglarlo.",
        "derecho": "ninguno", "fundamento": FUND_61,
        "accionado": "Propietario del predio vecino",
        "razon": "la fijación de linderos corresponde al proceso de deslinde y amojonamiento ante el juez civil, medio específico para esta controversia",
        "pretension": "acudir a la jurisdicción civil mediante proceso de deslinde y amojonamiento",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_seguro_no_pagado",
        "relato": "Mi carro se incendió y la aseguradora no me paga porque dice que no declaré una modificación del motor. Yo tengo la póliza al día y el peritaje. Tengo otro carro y puedo esperar un proceso.",
        "derecho": "ninguno", "fundamento": FUND_61,
        "accionado": "Compañía de seguros",
        "razon": "la objeción de la aseguradora se controvierte ante el juez civil o ante la Superintendencia Financiera, medios idóneos y eficaces en este caso",
        "pretension": "acudir a la jurisdicción civil o a la Superintendencia Financiera para el pago de la indemnización",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_reliquidacion_pension",
        "relato": "Me pensionaron hace cuatro años pero no me contaron unos factores salariales que yo creo que cuentan. La mesada me alcanza, vivo bien, pero quiero que me la reliquiden como debe ser.",
        "derecho": "seguridad_social", "fundamento": "art. 48 CP; " + FUND_61,
        "accionado": "Administradora de pensiones",
        "razon": "la reliquidación de una pensión ya reconocida se discute ante la jurisdicción ordinaria laboral y no se acredita un perjuicio irremediable que habilite la tutela",
        "pretension": "acudir a la jurisdicción ordinaria laboral para la reliquidación de la mesada",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_cheque_sin_fondos",
        "relato": "Me pagaron un trabajo con un cheque de doce millones y el banco lo devolvió por fondos insuficientes. El que lo giró no contesta el teléfono. Yo tengo el cheque original con el sello de devolución.",
        "derecho": "ninguno", "fundamento": FUND_61,
        "accionado": "Girador del título valor",
        "razon": "el cheque devuelto presta mérito ejecutivo, de modo que existe un proceso ejecutivo específico e idóneo para el cobro",
        "pretension": "acudir a la jurisdicción civil mediante proceso ejecutivo con base en el título valor",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_nulidad_eleccion",
        "relato": "El concejal que quedó elegido en mi municipio tenía una inhabilidad por un contrato con la alcaldía el año anterior. Quiero que se le quite la elección porque no podía ser candidato.",
        "derecho": "ninguno", "fundamento": FUND_61_CPACA,
        "accionado": "Concejal electo y autoridad electoral",
        "razon": "la elección se controvierte por el medio de control de nulidad electoral ante la jurisdicción contenciosa, mecanismo específico para ese efecto",
        "pretension": "acudir a la jurisdicción contencioso administrativa mediante nulidad electoral",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_dano_consumado_semestre",
        "relato": "La universidad no me dejó presentar los exámenes finales por un problema con el pago y perdí el semestre completo. Eso fue en 2024. Ya terminé la carrera en otra universidad y me gradué este año.",
        "derecho": "ninguno", "fundamento": FUND_64,
        "accionado": "Universidad",
        "razon": "el daño está consumado, la situación ya fue superada y no subsiste ninguna acción u omisión violatoria que amparar",
        "pretension": "acudir a la jurisdicción competente para reclamar la reparación del perjuicio, si a ello hubiere lugar",
        "hechos": H_DANO,
    },
    {
        "categoria": "vo_dano_consumado_demolicion",
        "relato": "La alcaldía me demolió el local sin avisarme, alegando que estaba en espacio público. Eso pasó el año pasado, ya no queda nada y yo me reubiqué en otro lado. Quiero que me paguen lo que perdí.",
        "derecho": "ninguno", "fundamento": FUND_64,
        "accionado": "Alcaldía municipal",
        "razon": "el daño está consumado y lo pretendido es una reparación patrimonial, finalidad ajena a la tutela",
        "pretension": "acudir a la jurisdicción contencioso administrativa mediante reparación directa",
        "hechos": H_DANO,
    },
    {
        "categoria": "vo_prescripcion_deuda",
        "relato": "Me llegó una demanda ejecutiva por un crédito de 2009 que nunca pagué. El abogado dice que eso ya prescribió hace años. Yo quiero que no me puedan cobrar eso ni embargarme.",
        "derecho": "ninguno", "fundamento": FUND_61,
        "accionado": "Entidad acreedora",
        "razon": "la prescripción debe alegarse como excepción dentro del propio proceso ejecutivo, que es el medio judicial idóneo y está en curso",
        "pretension": "proponer la excepción de prescripción dentro del proceso ejecutivo en curso",
        "hechos": H_SUB,
    },
    {
        "categoria": "vo_acto_general_tarifas",
        "relato": "El municipio sacó un decreto que subió las tarifas del impuesto de industria y comercio para todos los comerciantes. No me han liquidado nada todavía a mí, pero quiero que tumben ese decreto.",
        "derecho": "ninguno", "fundamento": FUND_65,
        "accionado": "Alcaldía municipal",
        "razon": "se impugna un acto de carácter general, impersonal y abstracto sin que exista aún un acto de aplicación concreto al solicitante",
        "pretension": "acudir a la jurisdicción contencioso administrativa mediante el medio de control de nulidad",
        "hechos": H_GRAL,
    },
]

# --------------------------------------------------------------------------
# TUTELA (26 nuevos)
# --------------------------------------------------------------------------
# Caso base: hay una persona concreta con un derecho fundamental afectado y
# ninguna causal del art. 6 cierra el paso.
H_TU = {"afectacion_individual": True}
# Sujeto de especial proteccion constitucional (menor, adulto mayor,
# discapacidad, embarazo, desplazamiento, debilidad manifiesta).
H_TU_ESP = {"afectacion_individual": True, "sujeto_especial_proteccion": True}
# Transitoria (art. 8 D.2591): existe otro medio pero no es eficaz en concreto
# y/o concurre un perjuicio irremediable.
H_TU_TRANS = {"afectacion_individual": True, "otro_medio_judicial": True,
              "medio_eficaz": False, "perjuicio_irremediable": True,
              "sujeto_especial_proteccion": True}
# Excepcion del art. 6.3: situacion colectiva, pero el titular pide lo suyo
# para impedir un perjuicio irremediable.
H_TU_COL = {"derecho_colectivo": True, "titular_pide_lo_suyo": True,
            "perjuicio_irremediable": True, "afectacion_individual": True}

TUTELA = [
    # --- salud ---------------------------------------------------------
    {
        "categoria": "tu_salud_cita_especialista",
        "relato": "El médico general me remitió a neurocirugía por una hernia que me tiene con dolor todo el día y sin poder cargar nada. La EPS me dio la cita para dentro de ocho meses y dice que es la primera que hay.",
        "derecho": "salud", "fundamento": "art. 49 CP; Ley 1751 de 2015",
        "accionado": "EPS",
        "razon": "la asignación de una cita a ocho meses frente a una remisión por dolor incapacitante desconoce la oportunidad que exige el derecho a la salud",
        "pretension": "ordenar la asignación de la cita de neurocirugía en un término perentorio",
        "hechos": H_TU,
    },
    {
        "categoria": "tu_salud_paliativos",
        "relato": "A mi esposo le dijeron que el cáncer ya no tiene tratamiento y que lo manejen con cuidados paliativos. La EPS no ha asignado el equipo de paliativos y él está en la casa con dolor, sin morfina y sin que nadie lo valore.",
        "derecho": "salud", "fundamento": "art. 49 CP; Ley 1751 de 2015",
        "accionado": "EPS",
        "razon": "los cuidados paliativos son parte del tratamiento integral y su omisión somete al paciente a un sufrimiento evitable en fase terminal",
        "pretension": "ordenar la asignación del equipo de cuidados paliativos y el suministro del manejo del dolor",
        "hechos": H_TU_ESP,
    },
    {
        "categoria": "tu_salud_traslado_rural",
        "relato": "Vivimos en una vereda a cuatro horas del casco urbano. Mi mamá necesita diálisis tres veces por semana y la EPS dice que el transporte no está cubierto. Nos está saliendo más caro el viaje que todo lo demás.",
        "derecho": "salud", "fundamento": "art. 46 CP; art. 49 CP; Ley 1751 de 2015",
        "accionado": "EPS",
        "razon": "cuando la familia no tiene capacidad económica para costearlo, el transporte hace parte del acceso efectivo al servicio y condiciona la continuidad de la diálisis",
        "pretension": "ordenar el suministro del transporte para la asistencia al tratamiento de diálisis",
        "hechos": H_TU_ESP,
    },
    {
        "categoria": "tu_salud_protesis",
        "relato": "Perdí la pierna en un accidente y el especialista ordenó una prótesis para poder caminar y volver a trabajar. La EPS la niega porque dice que ese modelo no está financiado y que me dan unas muletas.",
        "derecho": "salud", "fundamento": "art. 13 CP; art. 49 CP; Ley 1751 de 2015",
        "accionado": "EPS",
        "razon": "la prótesis ordenada por el médico tratante es el medio para recuperar la funcionalidad, y negarla deja al paciente en condición de discapacidad evitable",
        "pretension": "ordenar la autorización y entrega de la prótesis ordenada por el médico tratante",
        "hechos": H_TU_ESP,
    },
    {
        "categoria": "tu_salud_cirugia_comorbilidad",
        "relato": "Tengo obesidad severa, diabetes y apnea del sueño, y el cirujano ordenó una cirugía bariátrica porque los tratamientos no han funcionado. La EPS la niega diciendo que es estética y que baje de peso con dieta.",
        "derecho": "salud", "fundamento": "art. 49 CP; Ley 1751 de 2015",
        "accionado": "EPS",
        "razon": "el procedimiento fue ordenado por el médico tratante con base en comorbilidades documentadas, de modo que no tiene finalidad estética sino funcional",
        "pretension": "ordenar la autorización de la cirugía ordenada por el médico tratante",
        "hechos": H_TU,
    },
    {
        "categoria": "tu_salud_terapias_menor",
        "relato": "Mi hijo de cinco años tiene parálisis cerebral y venía con terapia física, ocupacional y de lenguaje. La EPS las suspendió diciendo que ya cumplió el número de sesiones del año y que espere a enero.",
        "derecho": "salud", "fundamento": "art. 44 CP; art. 49 CP; Ley 1751 de 2015",
        "accionado": "EPS",
        "razon": "el tope de sesiones no puede interrumpir un tratamiento de rehabilitación ordenado a un menor, cuyos derechos prevalecen sobre los demás",
        "pretension": "ordenar la continuidad de las terapias de rehabilitación sin topes de sesiones",
        "hechos": H_TU_ESP,
    },
    # --- peticion ------------------------------------------------------
    {
        "categoria": "tu_peticion_historia_clinica",
        "relato": "Pedí por escrito la historia clínica completa de mi mamá, que falleció en esa clínica, para saber qué pasó. Llevan dos meses y medio y solo me entregaron la epicrisis de un día. Soy la hija y llevé el registro civil.",
        "derecho": "peticion", "fundamento": "art. 23 CP; Ley 1755 de 2015; art. 42 Decreto 2591 de 1991",
        "accionado": "Institución prestadora de salud",
        "razon": "el término legal está vencido y la entrega parcial no satisface el derecho de petición de quien acredita interés legítimo sobre la información",
        "pretension": "ordenar la entrega completa de la historia clínica solicitada",
        "hechos": H_TU,
    },
    {
        "categoria": "tu_peticion_concurso",
        "relato": "Participé en un concurso de méritos y pedí por escrito el puntaje detallado de la prueba y los criterios con que me calificaron. Van tres meses, la lista ya salió y a mí nunca me respondieron nada.",
        "derecho": "peticion", "fundamento": "art. 23 CP; Ley 1755 de 2015",
        "accionado": "Entidad que adelanta el concurso",
        "razon": "el término para resolver está ampliamente vencido y la falta de respuesta impide al interesado conocer y controvertir su propia calificación",
        "pretension": "ordenar respuesta de fondo con el detalle del puntaje y los criterios de calificación",
        "hechos": H_TU,
    },
    {
        "categoria": "tu_peticion_colegio_privado",
        "relato": "Le radiqué al colegio de mi hija una petición pidiendo el soporte del cobro de unos materiales que nos facturaron dos veces. Llevan cuarenta días, no han contestado y en la secretaría dicen que eso lo ve el rector cuando pueda.",
        "derecho": "peticion", "fundamento": "art. 23 CP; Ley 1755 de 2015; art. 42 Decreto 2591 de 1991",
        "accionado": "Institución educativa privada",
        "razon": "la tutela procede contra el particular encargado del servicio público de educación y el término para responder la petición está vencido",
        "pretension": "ordenar respuesta de fondo a la petición radicada",
        "hechos": H_TU,
    },
    # --- seguridad social ----------------------------------------------
    {
        "categoria": "tu_ss_mora_patronal",
        "relato": "Cumplí la edad y las semanas, pero el fondo me niega la pensión porque tres empleadores viejos no pagaron unos meses de aportes. Yo sí tengo los desprendibles con los descuentos que me hicieron del sueldo.",
        "derecho": "seguridad_social", "fundamento": "art. 48 CP; Ley 100 de 1993",
        "accionado": "Administradora de pensiones",
        "razon": "la mora del empleador no es oponible al afiliado a quien se le descontaron los aportes, y la administradora cuenta con la facultad de cobro",
        "pretension": "ordenar el reconocimiento de la pensión computando los períodos en mora",
        "hechos": H_TU_ESP,
    },
    {
        "categoria": "tu_ss_auxilio_funerario",
        "relato": "Mi hermano murió, él era el que cotizaba, y yo pagué el entierro con un préstamo gota a gota porque no teníamos nada. Pedí el auxilio funerario y el fondo lo niega diciendo que los recibos no están a nombre de un familiar directo.",
        "derecho": "seguridad_social", "fundamento": "art. 48 CP; Ley 100 de 1993",
        "accionado": "Administradora de pensiones",
        "razon": "exigir un requisito formal que la ley no impone para reconocer el auxilio a quien efectivamente sufragó los gastos desconoce la finalidad de la prestación",
        "pretension": "ordenar el reconocimiento y pago del auxilio funerario",
        "hechos": H_TU,
    },
    {
        "categoria": "tu_ss_calificacion_invalidez",
        "relato": "Quedé en silla de ruedas después de un accidente y llevo once meses esperando que la junta me califique la pérdida de capacidad laboral. Sin eso no puedo pedir la pensión de invalidez. No tengo ingresos y vivo de lo que me dan en la casa.",
        "derecho": "seguridad_social", "fundamento": "art. 48 CP; art. 13 CP; art. 8 Decreto 2591 de 1991",
        "accionado": "Junta de calificación de invalidez y administradora de pensiones",
        "razon": "la demora indefinida en la calificación bloquea el acceso a la prestación y, ante la carencia total de ingresos, el medio ordinario no resulta eficaz en concreto",
        "pretension": "ordenar la realización de la calificación de pérdida de capacidad laboral en un término perentorio",
        "hechos": H_TU_TRANS,
    },
    # --- habeas data ---------------------------------------------------
    {
        "categoria": "tu_hd_dato_pagado",
        "relato": "Pagué toda la deuda de la tarjeta en marzo y tengo el paz y salvo del banco. Estamos en octubre y sigo reportado como moroso en las dos centrales. Mandé el paz y salvo dos veces y no han corregido nada.",
        "derecho": "habeas_data", "fundamento": "art. 15 CP; Ley 1266 de 2008",
        "accionado": "Entidad financiera y central de riesgo",
        "razon": "extinguida la obligación, mantener el reporte como moroso hace que el dato sea inexacto y desactualizado, lo que vulnera el habeas data",
        "pretension": "ordenar la actualización del reporte conforme al pago acreditado",
        "hechos": H_TU,
    },
    {
        "categoria": "tu_hd_datos_salud_laboral",
        "relato": "En la empresa pasaron por el grupo de WhatsApp del área la lista de incapacidades con el nombre y el diagnóstico de cada uno. Ahí aparece mi diagnóstico psiquiátrico y ahora todo el mundo lo sabe.",
        "derecho": "habeas_data", "fundamento": "art. 15 CP; Ley 1581 de 2012",
        "accionado": "Empleador",
        "razon": "el diagnóstico de salud es un dato sensible cuya divulgación sin autorización del titular vulnera la intimidad y el habeas data",
        "pretension": "ordenar la supresión de la información divulgada y la adopción de medidas que impidan nuevas divulgaciones",
        "hechos": H_TU,
    },
    # --- debido proceso ------------------------------------------------
    {
        "categoria": "tu_dp_insubsistencia_sin_motivar",
        "relato": "Llevaba seis años en la entidad en carrera administrativa y me llegó una resolución de insubsistencia de un párrafo, sin decir por qué. No hubo proceso, ni descargos, ni evaluación mala.",
        "derecho": "debido_proceso", "fundamento": "art. 29 CP",
        "accionado": "Entidad pública empleadora",
        "razon": "la declaratoria de insubsistencia de un empleado de carrera exige acto motivado y procedimiento previo, cuya ausencia impide toda defensa",
        "pretension": "dejar sin efecto la insubsistencia y ordenar que la decisión se adopte con motivación y procedimiento previo",
        "hechos": H_TU,
    },
    {
        "categoria": "tu_dp_sancion_federacion",
        "relato": "La federación me suspendió dos años por un supuesto fraude en la inscripción de un torneo. Me enteré por la página web. Nunca me notificaron ningún proceso ni me pidieron explicaciones.",
        "derecho": "debido_proceso", "fundamento": "art. 29 CP; art. 42 Decreto 2591 de 1991",
        "accionado": "Federación deportiva",
        "razon": "la sanción se impuso sin traslado de cargos ni oportunidad de defensa, y la tutela procede frente al particular respecto de quien el afectado está en situación de subordinación",
        "pretension": "dejar sin efecto la sanción y ordenar que el proceso disciplinario se rehaga con garantías",
        "hechos": H_TU,
    },
    {
        "categoria": "tu_dp_sin_notificacion",
        "relato": "Me enteré de que tenía un proceso administrativo sancionatorio cuando me llegó el cobro coactivo. Nunca recibí ninguna citación en mi dirección, que es la misma de hace quince años y la que figura en el RUT.",
        "derecho": "debido_proceso", "fundamento": "art. 29 CP",
        "accionado": "Entidad pública sancionadora",
        "razon": "la omisión de la notificación personal impidió al administrado ejercer su defensa en el procedimiento que concluyó con la sanción",
        "pretension": "ordenar la notificación en debida forma y la reposición del término para ejercer la defensa",
        "hechos": H_TU,
    },
    # --- educacion -----------------------------------------------------
    {
        "categoria": "tu_edu_estudiante_embarazada",
        "relato": "Mi hija tiene diecisiete años y está embarazada de seis meses. En el colegio la mandaron a estudiar desde la casa y le dijeron que mejor se retire este año para no incomodar a las otras niñas.",
        "derecho": "educacion", "fundamento": "art. 43 CP; art. 44 CP; art. 67 CP; art. 42 Decreto 2591 de 1991",
        "accionado": "Institución educativa",
        "razon": "el embarazo no puede ser causa de exclusión del sistema educativo, y la medida discrimina a una menor en estado de gestación",
        "pretension": "ordenar la reincorporación de la estudiante a la jornada regular con los apoyos que requiera",
        "hechos": H_TU_ESP,
    },
    {
        "categoria": "tu_edu_transporte_rural",
        "relato": "Mis dos hijos, de ocho y diez años, caminan dos horas y media para llegar a la escuela porque quitaron la ruta escolar de la vereda. En invierno el camino se vuelve un barrial y han dejado de ir muchos días.",
        "derecho": "educacion", "fundamento": "art. 44 CP; art. 67 CP",
        "accionado": "Secretaría de Educación y alcaldía municipal",
        "razon": "sin el transporte escolar el acceso efectivo a la educación de menores en zona rural queda materialmente anulado",
        "pretension": "ordenar el restablecimiento del transporte escolar para los menores de la vereda",
        "hechos": H_TU_ESP,
    },
    {
        "categoria": "tu_edu_separacion_hermanos",
        "relato": "En la asignación de cupos nos dieron a mi hijo de seis años en un colegio y a su hermana de nueve en otro, a cuarenta minutos el uno del otro. Yo trabajo y no tengo cómo llevarlos a dos sitios a la misma hora.",
        "derecho": "educacion", "fundamento": "art. 44 CP; art. 67 CP",
        "accionado": "Secretaría de Educación",
        "razon": "la asignación desconoce la unidad familiar y la capacidad real de la madre para garantizar la asistencia de los dos menores",
        "pretension": "ordenar la reasignación de cupos de los dos menores en una misma institución",
        "hechos": H_TU_ESP,
    },
    # --- estabilidad laboral reforzada ---------------------------------
    {
        "categoria": "tu_elr_accidente_trabajo",
        "relato": "Me fracturé la columna en un accidente de trabajo y llevo cinco meses en tratamiento con incapacidades. La empresa me terminó el contrato diciendo que ya no hay obra ni labor, pero el proyecto sigue y contrataron a dos personas más.",
        "derecho": "estabilidad_laboral_reforzada", "fundamento": "art. 13 CP; art. 25 CP; Ley 361 de 1997",
        "accionado": "Empleador",
        "razon": "el empleador conocía la condición de salud derivada del accidente laboral y terminó el vínculo sin autorización del inspector de trabajo, subsistiendo la labor contratada",
        "pretension": "ordenar el reintegro, el pago de los salarios dejados de percibir y la reubicación acorde con la condición de salud",
        "hechos": H_TU_ESP,
    },
    {
        "categoria": "tu_elr_lactancia",
        "relato": "Volví de la licencia de maternidad y a las tres semanas me despidieron por reestructuración. Mi bebé tiene cuatro meses y la estoy lactando. No pidieron permiso a ninguna autoridad para despedirme.",
        "derecho": "estabilidad_laboral_reforzada", "fundamento": "art. 43 CP; art. 53 CP",
        "accionado": "Empleador",
        "razon": "el despido dentro del período de lactancia requiere autorización previa del inspector de trabajo, cuya ausencia hace ineficaz la terminación",
        "pretension": "ordenar el reintegro y el pago de los salarios y prestaciones dejados de percibir",
        "hechos": H_TU_ESP,
    },
    # --- minimo vital --------------------------------------------------
    {
        "categoria": "tu_mv_salarios_madre_cabeza",
        "relato": "Soy madre cabeza de familia con tres hijos y la empresa me debe cuatro meses de sueldo. Nos quitaron el almuerzo del colegio porque no pude pagar y ya me notificaron el desalojo por los arriendos atrasados.",
        "derecho": "minimo_vital", "fundamento": "art. 43 CP; art. 53 CP",
        "accionado": "Empleador",
        "razon": "el no pago prolongado del salario a una madre cabeza de familia compromete de forma actual el mínimo vital de ella y de los menores a su cargo",
        "pretension": "ordenar el pago de los salarios adeudados",
        "hechos": H_TU_ESP,
    },
    {
        "categoria": "tu_mv_embargo_salario",
        "relato": "Me embargaron el sueldo por un crédito y me están descontando casi todo. Yo gano el mínimo y me están dejando con menos de trescientos mil pesos al mes para vivir con mis dos hijos.",
        "derecho": "minimo_vital", "fundamento": "art. 53 CP",
        "accionado": "Empleador y entidad acreedora",
        "razon": "el salario mínimo es inembargable salvo las excepciones legales, y el descuento practicado deja al trabajador sin lo indispensable para subsistir",
        "pretension": "ordenar el ajuste del descuento a los límites legales de embargabilidad del salario",
        "hechos": H_TU,
    },
    # --- excepcion del art. 6.3: situacion colectiva, derecho propio ----
    {
        "categoria": "tu_excepcion_colectiva_agua",
        "relato": "El acueducto del barrio entrega agua sin tratar y todo el sector está afectado. Pero mi caso es distinto: yo soy paciente renal y hago diálisis en casa, y con esa agua no puedo hacer el procedimiento. El nefrólogo lo dejó por escrito.",
        "derecho": "salud", "fundamento": "art. 49 CP; art. 6.3 Decreto 2591 de 1991; Ley 1751 de 2015",
        "accionado": "Empresa prestadora del servicio de acueducto",
        "razon": "aunque la situación compromete derechos colectivos, el titular reclama la afectación concreta de su propio derecho a la salud y se trata de impedir un perjuicio irremediable, excepción expresa del artículo 6.3",
        "pretension": "ordenar el suministro de agua apta para el procedimiento de diálisis domiciliaria del accionante",
        "hechos": H_TU_COL,
    },
    {
        "categoria": "tu_excepcion_colectiva_aire",
        "relato": "La ladrillera que está arriba del barrio quema con llantas y el humo nos cae a todos. Lo mío es que mi hijo de cuatro años tiene asma severa y ya lleva tres hospitalizaciones en urgencias este año; el neumólogo dice que tiene que salir de esa exposición.",
        "derecho": "salud", "fundamento": "art. 44 CP; art. 49 CP; art. 6.3 Decreto 2591 de 1991",
        "accionado": "Empresa ladrillera y autoridad ambiental",
        "razon": "dentro de una situación que compromete el ambiente sano, el titular pide la protección de la salud de su hijo menor frente a un riesgo documentado, supuesto de la excepción del artículo 6.3",
        "pretension": "ordenar las medidas necesarias para cesar la exposición del menor a las emisiones",
        "hechos": H_TU_COL,
    },
]


def bloque_b() -> list[dict]:
    """Los 47 casos del bloque, con mecanismo y procede ya resueltos."""
    out = []
    for c in VIA_ORDINARIA:
        out.append({**c, "mecanismo": "via_ordinaria"})
    for c in TUTELA:
        out.append({**c, "mecanismo": "tutela"})
    for c in out:
        c["procede"] = c["mecanismo"] == "tutela"
        c["hechos"] = dict(c["hechos"])
    return out
