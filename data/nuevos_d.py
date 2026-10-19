"""
Bloque D: cinco casos de FUENTE REAL, de sentencias de la Corte Constitucional.

DE DONDE SALEN
    De cinco expedientes de cuatro sentencias de revision de tutela de 2024,
    descargadas de la relatoria oficial (corteconstitucional.gov.co) y
    procesadas con `scratchpad/cosechar_sentencias.py`, que extrae de cada
    documento solo dos tramos: los HECHOS de los antecedentes y la parte
    RESOLUTIVA. Cada caso cita su sentencia y su numero de expediente, asi que
    cualquiera puede verificar la etiqueta leyendo el fallo.

QUE ES REAL Y QUE NO, SIN ADORNOS
    El CASO es real y la ETIQUETA es la que decidio la Corte. El RELATO no es
    texto literal: los hechos de una sentencia estan escritos en registro
    judicial, en tercera persona y con remisiones, y el sistema en produccion
    recibe el relato de un ciudadano. Asi que los hechos se condensaron a
    primera persona conservando los datos que determinan el mecanismo.

    Es la misma limitacion que tiene cualquier dataset construido sobre
    documentos judiciales y hay que declararla, no esconderla: la fuente da la
    ETIQUETA verificada y la casuistica real, no el registro de entrada.

POR QUE IMPORTA MAS DE LO QUE PARECE
    Tres de los cinco son CARENCIA ACTUAL DE OBJETO: la Corte no entra al
    fondo porque entre la presentacion y el fallo la situacion cambio. Esa
    categoria no estaba en el dataset escrito por el equipo, y no por descuido:
    a nadie se le ocurre inventar un caso en el que la accionante se muere
    durante el proceso, o en el que el colegio asigna la ruta escolar justo
    antes del fallo. La realidad produce supuestos que la imaginacion no.

    En el vocabulario cerrado del proyecto, el hecho superado y la situacion
    sobreviniente se etiquetan `via_ordinaria` con fundamento en el art. 6.4
    del Decreto 2591 de 1991, igual que los casos A01, A07 y A12 del eval set:
    no hay derecho fundamental actual que amparar.
"""

FUENTE = "https://www.corteconstitucional.gov.co/relatoria/2024"

REALES = [
    {
        "categoria": "real_transporte_escolar_hecho_superado",
        "sentencia": "T-200 de 2024",
        "expediente": "tutela de Rosa contra la Secretaria de Educacion Distrital de Bogota",
        "fuente": f"{FUENTE}/T-200-24.htm",
        "relato": "Soy madre cabeza de familia y vivo en Ciudad Bolívar con mis tres hijos. Están matriculados en el mismo colegio distrital pero en jornadas distintas, uno en la mañana y dos en la tarde, así que me toca pagar nueve pasajes de bus al día y no me alcanza. Pedí que los pasaran a la misma jornada o que les dieran la ruta.",
        "derecho": "educacion",
        "fundamento": "art. 44 CP; art. 67 CP; art. 6.4 Decreto 2591 de 1991",
        "accionado": "Secretaría de Educación Distrital",
        "mecanismo": "via_ordinaria",
        "razon": "entre la presentación de la solicitud y el fallo la entidad resolvió la situación de los menores, de modo que se configuró una carencia actual de objeto por situación sobreviniente y no hay orden que impartir",
        "pretension": "no hay orden que impartir: la situación que motivó la solicitud fue resuelta antes del fallo",
        "hechos": {"dano_consumado": True, "continua_vulneracion": False,
                   "sujeto_especial_proteccion": True},
        "nota_fallo": "La Corte MODIFICO PARCIALMENTE el fallo de instancia y DECLARO la carencia actual de objeto por situacion sobreviniente.",
    },
    {
        "categoria": "real_cuidador_hecho_sobreviniente",
        "sentencia": "T-075 de 2024",
        "expediente": "T-9.580.096, accionante Clara",
        "fuente": f"{FUENTE}/T-075-24.htm",
        "relato": "Mi mamá tiene 84 años, está en cama y no puede bañarse ni comer sola. Pedimos a la EPS que le asignaran un cuidador para las actividades básicas del día porque nosotros trabajamos y no podemos estar con ella todo el tiempo. La EPS dijo que eso le corresponde a la familia.",
        "derecho": "salud",
        "fundamento": "art. 46 CP; art. 49 CP; art. 6.4 Decreto 2591 de 1991",
        "accionado": "EPS",
        "mecanismo": "via_ordinaria",
        "razon": "la accionante falleció después de presentar la solicitud y antes del fallo, de modo que el servicio pedido ya no puede prestarse y se configura una carencia actual de objeto por hecho sobreviniente",
        "pretension": "no hay orden que impartir: la pretensión se tornó imposible antes del fallo",
        "hechos": {"dano_consumado": True, "continua_vulneracion": False,
                   "sujeto_especial_proteccion": True},
        "nota_fallo": "La Corte DECLARO la carencia actual de objeto por hecho sobreviniente: la accionante fallecio durante el tramite y la pretension era un servicio de acompanamiento, no evitar la muerte.",
    },
    {
        "categoria": "real_cuidador_faceta_diagnostico",
        "sentencia": "T-075 de 2024",
        "expediente": "T-9.580.096, accionante Plinio",
        "fuente": f"{FUENTE}/T-075-24.htm",
        "relato": "Soy adulto mayor y vivo solo. Le pedí a la EPS que me asignara un cuidador porque ya no me puedo valer para bañarme ni para la comida. La EPS me contestó que no está cubierto y que lo vea con mi familia, pero nunca me han valorado para establecer si de verdad lo necesito.",
        "derecho": "salud",
        "fundamento": "art. 46 CP; art. 49 CP; Ley 1751 de 2015",
        "accionado": "EPS",
        "mecanismo": "tutela",
        "razon": "negar el servicio sin haber practicado una valoración médica vulnera la faceta de diagnóstico del derecho a la salud: la entidad no puede descartar una necesidad que no ha evaluado",
        "pretension": "ordenar la valoración médica para determinar la necesidad del servicio de cuidador",
        "hechos": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
        "nota_fallo": "La Corte TUTELO el derecho a la salud en su faceta de diagnostico y ORDENO a la EPS practicar la valoracion en 3 dias para determinar la necesidad del cuidador.",
    },
    {
        "categoria": "real_traslado_subsidiariedad",
        "sentencia": "T-001 de 2024",
        "expediente": "T-9.536.128, accionante Diego Armando Martinez Hernandez",
        "fuente": f"{FUENTE}/T-001-24.htm",
        "relato": "Soy uniformado de la Policía y llevaba ocho años en la misma unidad en Boyacá. Me notificaron un traslado a Antioquia por necesidades del servicio, dentro de una propuesta de 192 traslados. Me ofrecieron prima de instalación y me dijeron que mi familia conserva los servicios médicos allá, pero yo no me quiero ir y creo que es una persecución.",
        "derecho": "ninguno",
        "fundamento": "art. 6.1 Decreto 2591 de 1991; Ley 1437 de 2011",
        "accionado": "Policía Nacional",
        "mecanismo": "via_ordinaria",
        "razon": "el traslado es un acto administrativo controvertible por el medio de control de nulidad y restablecimiento del derecho, con posibilidad de pedir suspensión provisional, y no se acredita que haya sido arbitrario ni que afecte de forma grave y directa los derechos del accionante o de su familia",
        "pretension": "acudir a la jurisdicción contencioso administrativa mediante nulidad y restablecimiento del derecho",
        "hechos": {"otro_medio_judicial": True, "medio_eficaz": True,
                   "perjuicio_irremediable": False},
        "nota_fallo": "La Corte DECLARO IMPROCEDENTE la tutela y DISPUSO que el accionante podia presentar la nulidad y restablecimiento del derecho, citando el art. 138 de la Ley 1437 de 2011 y la posibilidad de medidas cautelares del art. 230.",
    },
    {
        "categoria": "real_traslado_sin_motivacion",
        "sentencia": "T-001 de 2024",
        "expediente": "T-9.511.992, accionante Haider Alfonso Avendano Yepes",
        "fuente": f"{FUENTE}/T-001-24.htm",
        "relato": "Soy soldado y pedí traslado a una unidad cerca de Santa Marta, donde vive mi familia. Me negaron la solicitud con un oficio que no explica nada: dicen que los motivos están cubiertos por el secreto profesional y que no me los pueden dar. Así no tengo cómo saber por qué me la negaron ni cómo discutirlo.",
        "derecho": "debido_proceso",
        "fundamento": "art. 29 CP; art. 42 CP",
        "accionado": "Ejército Nacional",
        "mecanismo": "tutela",
        "razon": "invocar el secreto profesional para no motivar el acto que resuelve una solicitud de traslado deja al interesado sin forma de conocer ni controvertir la decisión, y la falta de motivación afecta además la unidad familiar",
        "pretension": "ordenar que se adelanten los trámites para el traslado a una unidad cercana a la familia del accionante",
        "hechos": {"afectacion_individual": True},
        "nota_fallo": "La Corte AMPARO el derecho a la unidad familiar, ORDENO al Ejercito adelantar el traslado en 15 dias y ADVIRTIO que se abstenga de aducir el secreto profesional como justificacion de la falta de motivacion.",
    },
]


def bloque_d() -> list[dict]:
    """Los cinco casos reales, con su procedencia en cada registro."""
    out = []
    for c in REALES:
        d = {k: v for k, v in c.items() if k != "nota_fallo"}
        d["procede"] = d["mecanismo"] == "tutela"
        d["tipo_fuente"] = "real"
        d["procedencia"] = (
            f"Sentencia {c['sentencia']} de la Corte Constitucional de Colombia, "
            f"expediente {c['expediente']}. {c['nota_fallo']} "
            "Hechos condensados a registro de ciudadano por el equipo; la etiqueta "
            "es la que decidio la Corte.")
        out.append(d)
    return out
