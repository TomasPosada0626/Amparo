"""
Bloque C: dieciocho ejemplos de ABSTENCION para el entrenamiento.

POR QUE HACEN FALTA
    La valvula de escape se anadio al PROMPT (`Mecanismo: no determinable`),
    pero un prompt no ensena un comportamiento: si el modelo nunca vio un
    ejemplo de abstencion en el fine-tuning, no la va a usar y la metrica
    saldra en cero. Al grupo de referencia les paso exactamente eso: sus cinco
    casos sin respuesta correcta salieron todos etiquetados con una clase, y lo
    documentaron como limitacion. Aqui se entrena el comportamiento y despues
    se mide en los dos sentidos.

POR QUE SON DIECIOCHO Y NO SEIS
    La v1 de este bloque tenia seis ejemplos y NO ALCANZO. Medido, no supuesto:
    en la corrida m1/20261015T182115Z, con 6 ejemplos repartidos en 4 de train
    y 2 de validation, `acierto_abstencion` salio 0.0 — el modelo forzo una
    etiqueta en los dos casos de validacion cuya respuesta correcta era "no
    determinable". En la direccion contraria salio perfecto
    (`abstencion_indebida` 0.0 sobre 31 casos): no abstiene de mas, no abstiene
    nunca. Cuatro ejemplos contra noventa y cuatro que si emiten mecanismo no
    son senal suficiente en ocho epocas.

    El numero 18 no es a ojo. En esa misma corrida las tres clases mas chicas
    (`habeas_corpus`, `accion_cumplimiento`, `accion_popular`) tenian DOCE
    ejemplos de entrenamiento cada una y el modelo las acerto: el macro F1 de
    mecanismo subio a 0.844, asi que doce es un piso que en este montaje ya se
    demostro suficiente. Dieciocho ejemplos dan catorce de train con el split
    de 0.25, por encima de ese piso, y suben la validacion de dos casos a
    cuatro — que tambien importa, porque una metrica medida sobre n=2 no
    distingue un sistema roto de uno con mala suerte.

POR QUE NO LOS VERIFICA EL MOTOR DE REGLAS
    Porque el motor siempre llega a un mecanismo: dados unos hechos, el art. 6
    del Decreto 2591 resuelve. La abstencion no es una conclusion del arbol de
    decision, es el reconocimiento de que NO HAY HECHOS SUFICIENTES para
    entrar al arbol. Pedirle al motor que la derive seria pedirle que concluya
    sin premisas.

LAS SEIS FAMILIAS, TRES EJEMPLOS CADA UNA
    Cada familia es una razon distinta para no responder, y la distincion
    importa: "no entiendo tu caso" y "tu caso no es de mi competencia" son
    respuestas diferentes para el usuario. Los tres ejemplares de cada familia
    varian el registro y la materia a proposito — con uno solo el modelo puede
    memorizar el relato en vez de aprender la razon.
"""

ABSTENCION = [
    # --- familia 1: consulta de conveniencia, sin derecho comprometido ----
    {
        "categoria": "ab_consulta_comercial",
        "relato": "Quiero arrendar mi apartamento y no sé en cuánto ponerlo. Está en un segundo piso, tiene dos habitaciones y parqueadero. ¿Cuánto cree que puedo pedir de arriendo en este sector?",
        "razon": "la consulta es sobre el precio de mercado de un arriendo, no sobre la vulneración o amenaza de un derecho: no hay materia para un triaje de acciones constitucionales",
        "pretension": "derivar la consulta a una fuente de información inmobiliaria",
        "accionado": "no aplica",
    },
    {
        "categoria": "ab_consulta_comercial",
        "relato": "Quiero montar una tienda de barrio y estoy entre matricularme como persona natural o abrir una SAS. ¿Qué me sale más barato en impuestos?",
        "razon": "se pide una comparación de conveniencia tributaria y societaria para un negocio que todavía no existe: no hay actuación de una autoridad ni de un particular que haya vulnerado o amenazado un derecho",
        "pretension": "derivar la consulta a asesoría contable y tributaria",
        "accionado": "no aplica",
    },
    {
        "categoria": "ab_consulta_comercial",
        "relato": "Mi hijo entra a la universidad el otro año y estamos comparando los programas de derecho en Medellín. ¿Cuál me recomienda por costo y por calidad?",
        "razon": "la consulta es una recomendación de consumo entre ofertas educativas y no la denuncia de un acceso negado: no hay derecho afectado del cual derivar un mecanismo",
        "pretension": "derivar la consulta a información comparada de programas académicos",
        "accionado": "no aplica",
    },

    # --- familia 2: pregunta conceptual, sin caso ------------------------
    {
        "categoria": "ab_pregunta_academica",
        "relato": "Estoy haciendo un trabajo para la universidad y necesito que me explique en qué se diferencia la acción de tutela de la acción de cumplimiento, con ejemplos de cada una.",
        "razon": "se pide una explicación conceptual y no el triaje de un caso concreto: no hay hechos de los cuales derivar un mecanismo",
        "pretension": "atender la solicitud como consulta académica, por fuera del triaje",
        "accionado": "no aplica",
    },
    {
        "categoria": "ab_pregunta_academica",
        "relato": "Para un parcial necesito los requisitos de procedibilidad de la tutela contra providencias judiciales tal como los fijó la Corte Constitucional.",
        "razon": "se pide la exposición de una regla jurisprudencial en abstracto y no el triaje de un caso: no hay hechos de los cuales derivar un mecanismo",
        "pretension": "atender la solicitud como consulta académica, por fuera del triaje",
        "accionado": "no aplica",
    },
    {
        "categoria": "ab_pregunta_academica",
        "relato": "¿Me puede armar un cuadro comparativo entre la acción popular y la acción de grupo para una exposición de la clase?",
        "razon": "se pide material didáctico sobre dos mecanismos en abstracto y no la determinación del mecanismo idóneo para un caso concreto",
        "pretension": "atender la solicitud como consulta académica, por fuera del triaje",
        "accionado": "no aplica",
    },

    # --- familia 3: hechos insuficientes --------------------------------
    {
        "categoria": "ab_hechos_insuficientes",
        "relato": "Fui a una oficina pública y me trataron muy mal, con muy mala actitud. Salí de ahí furioso. Quiero saber qué puedo hacer con eso.",
        "razon": "no se identifica el derecho afectado, la entidad accionada, la actuación concreta ni si existe otro medio de defensa: los hechos no alcanzan para determinar un mecanismo",
        "pretension": "solicitar al usuario la entidad, la fecha y la actuación concreta antes de orientar",
        "accionado": "indeterminado",
    },
    {
        "categoria": "ab_hechos_insuficientes",
        "relato": "Tengo un problema con una entidad desde hace rato y ya estoy cansado de la situación. Dígame qué me recomienda hacer.",
        "razon": "no se identifica la entidad, el derecho comprometido, la actuación concreta ni la fecha: no hay premisas para determinar un mecanismo",
        "pretension": "solicitar al usuario la entidad, la actuación y la fecha antes de orientar",
        "accionado": "indeterminado",
    },
    {
        "categoria": "ab_hechos_insuficientes",
        "relato": "Me dijeron que no a una solicitud que presenté y quiero que eso se revise. No recuerdo en qué entidad fue ni cuándo la radiqué.",
        "razon": "sin la entidad ni la fecha no se puede establecer el derecho invocado, la idoneidad de otro medio de defensa ni la inmediatez: los hechos no alcanzan para entrar al análisis de procedencia",
        "pretension": "solicitar al usuario la entidad, la fecha de radicación y copia de la respuesta",
        "accionado": "indeterminado",
    },

    # --- familia 4: materia fuera del corpus ----------------------------
    {
        "categoria": "ab_materia_no_cubierta",
        "relato": "Mi empresa es una sociedad extranjera y entró en un proceso de insolvencia en dos países a la vez. Necesito saber cómo se coordina eso y qué norma aplica aquí.",
        "razon": "la materia de insolvencia transfronteriza no está cubierta por el corpus normativo del sistema, y citar el artículo más parecido sería fundamentar el caso con una norma ajena",
        "pretension": "derivar la consulta a una fuente especializada en insolvencia transfronteriza",
        "accionado": "no determinable",
    },
    {
        "categoria": "ab_materia_no_cubierta",
        "relato": "Trabajo en una plataforma de criptoactivos y la Superintendencia nos pidió un reporte de las operaciones hechas con billeteras en el exterior. Necesito saber qué régimen nos obliga a eso.",
        "razon": "el régimen de supervisión de criptoactivos no está en el corpus normativo del sistema, y citar la disposición más parecida sería fundamentar la respuesta con una norma ajena a la materia",
        "pretension": "derivar la consulta a la regulación financiera especializada",
        "accionado": "no determinable",
    },
    {
        "categoria": "ab_materia_no_cubierta",
        "relato": "Mi hermano está detenido en Panamá desde hace un mes y queremos saber cómo funciona el proceso para traerlo y qué tratado aplica.",
        "razon": "la privación de la libertad la ejerce una autoridad extranjera, de modo que queda por fuera del habeas corpus colombiano, y el régimen de extradición y de asistencia consular no está en el corpus del sistema",
        "pretension": "derivar la consulta al Ministerio de Relaciones Exteriores y a defensa penal internacional",
        "accionado": "no determinable",
    },

    # --- familia 5: relato internamente contradictorio ------------------
    {
        "categoria": "ab_relato_contradictorio",
        "relato": "La EPS no me ha autorizado nada y llevo meses esperando. De hecho ya me hicieron el procedimiento el mes pasado y quedé bien, pero sigo sin autorización y por eso no me lo han hecho.",
        "razon": "el relato afirma a la vez que el procedimiento se realizó y que no se ha realizado, de modo que no hay un cuadro de hechos coherente del cual derivar un mecanismo",
        "pretension": "solicitar al usuario que aclare si el procedimiento ya se practicó",
        "accionado": "indeterminado",
    },
    {
        "categoria": "ab_relato_contradictorio",
        "relato": "Nunca me notificaron del proceso y por eso no pude defenderme. Yo asistí a la audiencia y allá expuse mis argumentos, pero como no me notificaron no me dejaron hablar.",
        "razon": "el relato afirma a la vez que no hubo notificación ni oportunidad de defensa y que el interesado asistió a la audiencia y expuso sus argumentos: los hechos se excluyen entre sí",
        "pretension": "solicitar al usuario que aclare si fue notificado y si intervino en la audiencia",
        "accionado": "indeterminado",
    },
    {
        "categoria": "ab_relato_contradictorio",
        "relato": "El colegio ya le dio el cupo a mi hija y está estudiando desde febrero. Necesito que ordenen el cupo porque se lo negaron y lleva todo el año sin estudiar.",
        "razon": "el relato afirma a la vez que la niña está matriculada y asistiendo desde febrero y que lleva todo el año sin estudiar por un cupo negado: no hay un cuadro de hechos coherente del cual derivar un mecanismo",
        "pretension": "solicitar al usuario que aclare si la niña está matriculada y asistiendo",
        "accionado": "indeterminado",
    },

    # --- familia 6: se pide un pronostico, no un mecanismo --------------
    {
        "categoria": "ab_pide_pronostico",
        "relato": "Ya radiqué la tutela contra el fondo de pensiones la semana pasada. Lo que quiero saber es qué probabilidad tengo de ganarla y cuánto me van a dar si gano.",
        "razon": "se pide un pronóstico sobre el resultado de un proceso ya iniciado, no la determinación del mecanismo idóneo: está por fuera de lo que el sistema puede responder",
        "pretension": "informar al usuario que el sistema no estima resultados de procesos en curso",
        "accionado": "no aplica",
    },
    {
        "categoria": "ab_pide_pronostico",
        "relato": "El juez ya me falló la tutela y me la negó. Quiero saber si vale la pena impugnar y qué posibilidades tengo de que me la cambien en segunda instancia.",
        "razon": "se pide un pronóstico sobre el resultado de la impugnación de un fallo ya proferido, no la determinación del mecanismo idóneo para un caso sin tramitar",
        "pretension": "informar al usuario que el sistema no estima resultados de procesos en curso",
        "accionado": "no aplica",
    },
    {
        "categoria": "ab_pide_pronostico",
        "relato": "Ya presenté la acción popular por el humedal del barrio y llevo ocho meses esperando. ¿Cuánto se demora normalmente un proceso de estos?",
        "razon": "se pide una estimación de la duración de un trámite ya iniciado, que no es una cuestión de procedencia ni de elección de mecanismo",
        "pretension": "informar al usuario que el sistema no estima tiempos de trámite",
        "accionado": "no aplica",
    },
]


def bloque_c() -> list[dict]:
    """Los dieciocho casos de abstencion. `mecanismo: None` y sin `hechos`: el
    motor de reglas no los verifica porque no son una conclusion del arbol."""
    out = []
    for c in ABSTENCION:
        out.append({
            **c,
            # `no_determinable`, no `ninguno`: la abstencion no afirma que
            # no haya derecho fundamental, afirma que no se puede determinar.
            # Es el valor de schema.DERECHO_ESCAPE.
            "derecho": "no_determinable",
            "fundamento": "",
            "mecanismo": None,
            "procede": False,
            "tipo": "abstencion",
        })
    return out
