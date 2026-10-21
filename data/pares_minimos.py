"""
Pares MÍNIMOS para las dos fronteras que el entrenamiento no hacía aprendibles.

QUÉ PROBLEMA RESUELVE, CON LAS CIFRAS QUE LO MOTIVAN

Dos defectos de `m1/20261021T115654Z`, los dos con causa establecida en
`data/causas_abiertas.json`:

  1. ABSTENCIÓN INDEBIDA 8.7% (9 de 103), y **8 de las 9 con gold
     `via_ordinaria`**. El modelo confunde «no hay mecanismo constitucional,
     vaya al juez ordinario» con «no se puede determinar nada». Medido: los
     relatos de las dos clases en el train comparten los marcadores de
     superficie —12 puntos porcentuales de diferencia media—, así que la
     frontera **no es aprendible de ellos**.

  2. 5 errores `tutela → via_ordinaria` y 10 de los 13 fallos del recall de
     clase crítica en esa misma dirección: el sistema manda a la ordinaria
     casos donde la tutela sí procede. El dataset empuja a «no hay mecanismo»
     desde que se ampliaron las abstenciones.

POR QUÉ PARES Y NO MÁS EJEMPLOS

Añadir ejemplos sueltos de abstención movería la cifra sin enseñar la
distinción, porque lo que falta no es volumen: es **contraste**. Cada par aquí
son dos relatos que se parecen por fuera y difieren en **una sola cosa** —la
que decide—. Es el mismo criterio que `ampliar_categorias.py` ya aplica
(«cada par es un contraste»), llevado a estas dos fronteras.

PROCEDENCIA, Y ESTO IMPORTA LEERLO

Estos casos **no los escribió un abogado**. Los redactó el asistente bajo
autorización expresa del profesor, porque el abogado del proyecto no tuvo
tiempo. Eso **no** los hace equivalentes a `data/revision_abogado_v3.json`,
donde un abogado revisó 40 casos y firmó 40/40.

Así que llevan su propia procedencia —`tipo_fuente: "redactado por el
asistente (autorizado por el profesor)"` y `nivel_fiabilidad` sin subir— y el
reporte lo declara. Confundir las dos cosas sería blanquear una autoría como
una revisión profesional, que es exactamente el tipo de afirmación que este
proyecto está construido para no hacer.

Lo que SÍ garantiza el motor: `decidir(hechos).mecanismo` tiene que coincidir
con el mecanismo declarado, o el caso se rechaza y no entra. Una codificación
mal hecha no pasa, venga de quien venga.

    python -I data/pares_minimos.py              # dice qué añadiría
    python -I data/pares_minimos.py --escribir   # lo añade al dataset
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from reglas import Hechos, decidir, estrato_verificacion   # noqa: E402

RUTA = RAIZ / "data" / "dataset.json"
RUTA_OUT = RAIZ / "data" / "pares_minimos_propuestos.json"

FUENTE = "redactado por el asistente (autorizado por el profesor)"

# --------------------------------------------------------------------------
# RECETAS DE HECHOS, para no repetir el desglose en cada caso
# --------------------------------------------------------------------------
# El medio es eficaz EN CONCRETO: idóneo, oportuno y accesible para ESTA
# persona. Es el juicio del art. 6.1, y por eso va desglosado: declararlo
# mueve el caso al estrato `derivado`, donde la etiqueta no depende de una
# ponderación opaca.
ME_SIRVE = {"otro_medio_judicial": True, "medio_eficaz": True,
            "me_idoneo": True, "me_oportuno": True, "me_accesible": True}

# El medio existe y NO alcanza para esta persona. El elemento que falla se
# dice en cada caso, porque es lo que el juez tendría que apreciar.
def me_falla(idoneo=True, oportuno=True, accesible=True):
    return {"otro_medio_judicial": True, "medio_eficaz": False,
            "me_idoneo": idoneo, "me_oportuno": oportuno,
            "me_accesible": accesible}


# El test del perjuicio irremediable es CONJUNTIVO: los cuatro elementos
# tienen que concurrir (jurisprudencia constante de la Corte).
PI_CONCURRE = {"perjuicio_irremediable": True, "pi_inminencia": True,
               "pi_gravedad": True, "pi_urgencia": True,
               "pi_impostergabilidad": True}


def pi_no(inminencia=False, gravedad=True, urgencia=False,
          impostergabilidad=False):
    return {"perjuicio_irremediable": False, "pi_inminencia": inminencia,
            "pi_gravedad": gravedad, "pi_urgencia": urgencia,
            "pi_impostergabilidad": impostergabilidad}


# --------------------------------------------------------------------------
# ENCARGO 1 · la frontera abstención / vía ordinaria
# --------------------------------------------------------------------------
# Cada par: (a) hay un problema jurídico accionable aunque NO sea
# constitucional; (b) el mismo escenario sin hechos, sin pretensión o con una
# contradicción que impide decidir. La diferencia no está en el tema: está en
# si hay algo que un juez pueda resolver.
PARES_ABSTENCION = [
    # ---- par 1 · deuda civil -------------------------------------------
    dict(id="PM01", categoria="pm_deuda_civil", mecanismo="via_ordinaria",
         derecho="ninguno",
         relato="Le presté veinte millones a un socio y firmamos un pagaré "
                "con fecha de vencimiento en marzo. No me ha pagado nada y "
                "ya le escribí dos veces. Quiero que me devuelva la plata.",
         accionado="el socio deudor",
         pretension="acudir al juez civil para iniciar el proceso ejecutivo "
                    "con el pagaré como título",
         razon="hay un título ejecutivo y la jurisdicción civil es el medio "
               "idóneo y oportuno para cobrarlo; no se alega la vulneración "
               "de un derecho fundamental",
         hechos={**ME_SIRVE, **pi_no(), "afectacion_individual": False,
                 "continua_vulneracion": True}),
    dict(id="PM02", categoria="pm_deuda_sin_hechos", mecanismo=None,
         derecho="no_determinable",
         relato="Le presté plata a un socio y no me ha pagado. Todavía no "
                "tengo el pagaré a mano y no me acuerdo bien de las fechas "
                "ni de cuánto fue exactamente, pero quiero ir adelantando.",
         accionado="no aplica", pretension="no aplica",
         razon="el propio relato dice que no se tienen los hechos: sin monto, "
               "sin fecha y sin el título no hay nada que un juez pueda "
               "resolver todavía"),

    # ---- par 2 · despido -----------------------------------------------
    dict(id="PM03", categoria="pm_despido_ordinario", mecanismo="via_ordinaria",
         derecho="trabajo",
         relato="Me despidieron sin justa causa después de cuatro años. Tengo "
                "38 años, estoy sano y ya encontré otro trabajo, pero quiero "
                "que me paguen la indemnización que me corresponde.",
         accionado="el empleador",
         pretension="demandar ante el juez laboral el pago de la "
                    "indemnización por despido sin justa causa",
         razon="la jurisdicción laboral es idónea y oportuna para la "
               "indemnización, y no concurre perjuicio irremediable: hay "
               "ingresos y no hay riesgo para la subsistencia",
         hechos={**ME_SIRVE, **pi_no(), "afectacion_individual": False,
                 "continua_vulneracion": False}),
    dict(id="PM04", categoria="pm_despido_pronostico", mecanismo=None,
         derecho="no_determinable",
         relato="Me despidieron el mes pasado. Lo que quiero saber es si la "
                "empresa va a terminar pagándome o si se va a hacer la loca, "
                "y qué tan probable es que yo gane si demando.",
         accionado="no aplica", pretension="no aplica",
         razon="lo que se pide es un pronóstico sobre la conducta de un "
               "tercero y sobre el resultado de un proceso, no el triaje de "
               "una situación propia"),

    # ---- par 3 · arriendo ----------------------------------------------
    dict(id="PM05", categoria="pm_arriendo_restitucion",
         mecanismo="via_ordinaria", derecho="ninguno",
         relato="Tengo un local arrendado y el inquilino lleva cinco meses "
                "sin pagar. El contrato está firmado y vencido desde junio. "
                "Quiero que me devuelvan el local.",
         accionado="el arrendatario",
         pretension="promover el proceso de restitución de inmueble "
                    "arrendado ante el juez civil",
         razon="existe el proceso de restitución como medio idóneo y "
               "oportuno; no hay derecho fundamental del solicitante en juego",
         hechos={**ME_SIRVE, **pi_no(), "afectacion_individual": False,
                 "continua_vulneracion": True}),
    dict(id="PM06", categoria="pm_arriendo_consulta", mecanismo=None,
         derecho="no_determinable",
         relato="Estoy pensando en arrendar un local y quiero saber qué me "
                "conviene más, firmar a un año o a tres, y cómo me protejo "
                "mejor si el inquilino no paga.",
         accionado="no aplica", pretension="no aplica",
         razon="es una consulta de negocio sobre una situación futura: no hay "
               "accionado, no hay hecho ocurrido y no hay orden que pedir"),

    # ---- par 4 · tránsito ----------------------------------------------
    dict(id="PM07", categoria="pm_transito_perjuicios",
         mecanismo="via_ordinaria", derecho="ninguno",
         relato="Un bus me chocó el carro en noviembre. El conductor aceptó "
                "la culpa en el croquis y la empresa no me responde por los "
                "arreglos, que fueron ocho millones. Quiero que me paguen.",
         accionado="la empresa de transporte",
         pretension="demandar la reparación de perjuicios ante el juez civil",
         razon="la acción de responsabilidad civil es el medio idóneo para "
               "los perjuicios materiales, y no se alega afectación de un "
               "derecho fundamental",
         hechos={**ME_SIRVE, **pi_no(), "afectacion_individual": False,
                 "continua_vulneracion": False}),
    dict(id="PM08", categoria="pm_transito_contradictorio", mecanismo=None,
         derecho="no_determinable",
         relato="Un bus me chocó y la empresa nunca me ha respondido nada. "
                "La carta en que me negaron el pago me llegó en octubre y no "
                "la contesté porque ya me habían pagado todo.",
         accionado="no aplica", pretension="no aplica",
         razon="el relato afirma a la vez que nunca hubo respuesta, que hubo "
               "una negativa escrita y que ya le pagaron: tres hechos "
               "esenciales que no pueden ser ciertos al mismo tiempo"),

    # ---- par 5 · impuesto predial --------------------------------------
    dict(id="PM09", categoria="pm_predial_contencioso",
         mecanismo="via_ordinaria", derecho="debido_proceso",
         relato="La secretaría de hacienda me liquidó el predial sobre un "
                "área mayor de la que tiene el lote. Me notificaron en "
                "agosto, presenté el recurso de reconsideración y me lo "
                "negaron. Tengo 50 años y un negocio estable.",
         accionado="Secretaría de Hacienda municipal",
         pretension="demandar la nulidad del acto de liquidación ante la "
                    "jurisdicción de lo contencioso administrativo",
         razon="agotada la vía gubernativa, el medio de control de nulidad y "
               "restablecimiento del derecho es idóneo y oportuno; no "
               "concurre perjuicio irremediable",
         hechos={**ME_SIRVE, **pi_no(), "afectacion_individual": False,
                 "continua_vulneracion": True}),
    dict(id="PM10", categoria="pm_predial_academica", mecanismo=None,
         derecho="no_determinable",
         relato="Estoy preparando el examen de la especialización y necesito "
                "que me explique la diferencia entre el recurso de "
                "reconsideración y el medio de control de nulidad, con "
                "ejemplos de predial.",
         accionado="no aplica", pretension="no aplica",
         razon="se pide una explicación de doctrina para un examen, no el "
                "triaje de un caso propio"),

    # ---- par 6 · servicios públicos ------------------------------------
    dict(id="PM11", categoria="pm_servicios_reclamo",
         mecanismo="via_ordinaria", derecho="ninguno",
         relato="La empresa de energía me cobró el triple en el recibo de "
                "septiembre. Puse el reclamo, me lo negaron y la "
                "Superintendencia confirmó la negativa. Tengo 41 años y "
                "trabajo formal.",
         accionado="la empresa de energía",
         pretension="demandar ante la jurisdicción contenciosa el acto que "
                    "resolvió el recurso",
         razon="la vía contenciosa es idónea y oportuna tras el silencio "
               "administrativo resuelto, y no hay riesgo para la "
               "subsistencia que habilite la tutela",
         hechos={**ME_SIRVE, **pi_no(), "afectacion_individual": False,
                 "continua_vulneracion": True}),
    # OJO: la primera version de este caso reproducia LITERALMENTE el relato
    # de `AB54` del eval set --- la investigacion arancelaria de la DIAN --- y
    # la prueba 3 lo cazo como FUGA de entrenamiento a evaluacion. Es el peor
    # error posible aqui: un caso del eval dentro del train infla la cifra sin
    # que nada lo delate, y por eso esa prueba existe.
    #
    # Se mantiene el criterio juridico --- materia ajena al triaje
    # constitucional, se piden terminos y procedimiento --- y se cambia el
    # escenario entero.
    dict(id="PM12", categoria="pm_societario_materia_ajena", mecanismo=None,
         derecho="no_determinable",
         relato="Somos tres socios de una SAS y uno quiere vender su parte a "
                "un tercero. Queremos saber cómo se hace eso, si hay derecho "
                "de preferencia y qué plazos corren para los demás socios.",
         accionado="no aplica", pretension="no aplica",
         razon="se pide información societaria sobre procedimiento y plazos, "
               "no el triaje de una afectación a un derecho fundamental del "
               "solicitante"),
]

# --------------------------------------------------------------------------
# ENCARGO 2 · la frontera tutela / vía ordinaria
# --------------------------------------------------------------------------
# El criterio es el del art. 6.1 leído EN CONCRETO: el mismo medio judicial
# puede ser eficaz para una persona e ineficaz para otra, atendiendo su edad,
# su salud y su urgencia. Cada par mantiene el escenario y cambia solo eso.
PARES_TUTELA = [
    # ---- par 7 · pensión de sobrevivientes ------------------------------
    dict(id="PM13", categoria="pm_pension_medio_sirve",
         mecanismo="via_ordinaria", derecho="seguridad_social",
         relato="Mi esposo murió en enero y pedí la pensión de "
                "sobrevivientes. El fondo me la negó porque dice que faltan "
                "semanas. Tengo 44 años, trabajo como contadora y no dependo "
                "de ese ingreso.",
         accionado="Fondo de pensiones",
         pretension="demandar ante el juez laboral el reconocimiento de la "
                    "pensión de sobrevivientes",
         razon="la jurisdicción laboral es idónea y oportuna para esta "
               "persona: tiene ingresos propios, no es sujeto de especial "
               "protección y la espera del proceso no hace inútil la "
               "protección",
         hechos={**ME_SIRVE, **pi_no(), "afectacion_individual": True,
                 "continua_vulneracion": True}),
    dict(id="PM14", categoria="pm_pension_medio_no_sirve",
         mecanismo="tutela", derecho="seguridad_social",
         relato="Mi esposo murió en enero y pedí la pensión de "
                "sobrevivientes. El fondo me la negó porque dice que faltan "
                "semanas. Tengo 79 años, no tengo ingresos, vivo de lo que "
                "me dan mis vecinos y estoy en tratamiento por un cáncer.",
         accionado="Fondo de pensiones",
         pretension="amparar el mínimo vital y ordenar el reconocimiento de "
                    "la pensión de sobrevivientes",
         razon="el proceso laboral existe pero no es eficaz en concreto: a "
               "los 79 años, sin ingresos y con enfermedad en curso, la "
               "espera haría inútil la protección y concurren los cuatro "
               "elementos del perjuicio irremediable",
         hechos={**me_falla(oportuno=False), **PI_CONCURRE,
                 "afectacion_individual": True, "continua_vulneracion": True,
                 "sujeto_especial_proteccion": True}),

    # ---- par 8 · reintegro laboral --------------------------------------
    dict(id="PM15", categoria="pm_reintegro_medio_sirve",
         mecanismo="via_ordinaria", derecho="trabajo",
         relato="Me despidieron hace dos meses y creo que fue por haberme "
                "afiliado al sindicato. Tengo 35 años, buena salud y estoy "
                "trabajando por contrato en otra parte.",
         accionado="el antiguo empleador",
         pretension="demandar el reintegro ante el juez laboral",
         razon="el proceso laboral ordinario es idóneo y oportuno para "
               "discutir el despido, y no se acredita perjuicio irremediable",
         hechos={**ME_SIRVE, **pi_no(), "afectacion_individual": True,
                 "continua_vulneracion": False}),
    dict(id="PM16", categoria="pm_reintegro_medio_no_sirve",
         mecanismo="tutela", derecho="estabilidad_laboral_reforzada",
         relato="Me despidieron hace dos meses, estando yo en tratamiento de "
                "quimioterapia y con la EPS afiliada por la empresa. Al "
                "salir perdí el servicio y el oncólogo dice que no puedo "
                "interrumpir los ciclos. No tengo otra forma de pagarlos.",
         accionado="el antiguo empleador",
         pretension="amparar la estabilidad laboral reforzada y ordenar el "
                    "reintegro con la afiliación al sistema de salud",
         razon="el proceso laboral no es oportuno frente a un tratamiento que "
               "no admite interrupción: concurren inminencia, gravedad, "
               "urgencia e impostergabilidad, y hay debilidad manifiesta",
         hechos={**me_falla(oportuno=False), **PI_CONCURRE,
                 "afectacion_individual": True, "continua_vulneracion": True,
                 "sujeto_especial_proteccion": True}),

    # ---- par 9 · cupo escolar -------------------------------------------
    dict(id="PM17", categoria="pm_educacion_medio_sirve",
         mecanismo="via_ordinaria", derecho="educacion",
         relato="A mi hijo de 16 años le negaron el traslado al colegio que "
                "queda más cerca de la casa porque no había cupo. Sigue "
                "estudiando en el que estaba, a veinte minutos en bus.",
         accionado="Secretaría de Educación",
         pretension="demandar ante la jurisdicción contenciosa la negativa "
                    "del traslado",
         razon="el menor conserva el servicio educativo y la negativa no "
               "interrumpe su derecho: la vía contenciosa es idónea y no hay "
               "perjuicio irremediable",
         hechos={**ME_SIRVE, **pi_no(), "afectacion_individual": True,
                 "continua_vulneracion": False}),
    dict(id="PM18", categoria="pm_educacion_medio_no_sirve",
         mecanismo="tutela", derecho="educacion",
         relato="Nos desplazamos del campo por amenazas y llegamos en "
                "febrero. Mi hija de 8 años no ha podido entrar a ningún "
                "colegio porque dicen que el año ya empezó y no hay cupo. "
                "Lleva dos meses sin estudiar.",
         accionado="Secretaría de Educación",
         pretension="amparar el derecho a la educación y ordenar la "
                    "asignación inmediata de cupo escolar",
         razon="hay interrupción actual del servicio educativo de una menor "
               "en situación de desplazamiento: ningún medio ordinario "
               "resuelve en el tiempo del año escolar y concurren los cuatro "
               "elementos del perjuicio irremediable",
         hechos={**me_falla(oportuno=False), **PI_CONCURRE,
                 "afectacion_individual": True, "continua_vulneracion": True,
                 "sujeto_especial_proteccion": True}),

    # ---- par 10 · incapacidades no pagadas ------------------------------
    dict(id="PM19", categoria="pm_incapacidad_medio_sirve",
         mecanismo="via_ordinaria", derecho="seguridad_social",
         relato="La EPS me debe dos incapacidades de hace tres meses. Son "
                "ochocientos mil pesos en total. Tengo 33 años, sigo "
                "trabajando y recibo mi sueldo normal.",
         accionado="EPS",
         pretension="reclamar el pago de las incapacidades ante el juez "
                    "laboral",
         razon="hay un medio laboral idóneo y oportuno y el salario cubre la "
               "subsistencia: no concurre perjuicio irremediable",
         hechos={**ME_SIRVE, **pi_no(), "afectacion_individual": True,
                 "continua_vulneracion": True}),
    dict(id="PM20", categoria="pm_incapacidad_medio_no_sirve",
         mecanismo="tutela", derecho="minimo_vital",
         relato="Llevo siete meses incapacitado por un accidente y la EPS no "
                "me ha pagado ninguna incapacidad. Es mi único ingreso, vivo "
                "con mis dos hijos menores y ya me atrasé dos meses del "
                "arriendo.",
         accionado="EPS",
         pretension="amparar el mínimo vital y ordenar el pago de las "
                    "incapacidades causadas",
         razon="siete meses sin el único ingreso, con menores a cargo, hacen "
               "que el proceso laboral no sea oportuno: concurren los cuatro "
               "elementos del perjuicio irremediable",
         hechos={**me_falla(oportuno=False), **PI_CONCURRE,
                 "afectacion_individual": True, "continua_vulneracion": True,
                 "sujeto_especial_proteccion": True}),
]

# --------------------------------------------------------------------------
# ENCARGO 3a · huecos de cobertura de citas
# --------------------------------------------------------------------------
# El eval set pide la Ley 1581 de 2012 (datos personales, incluidos los
# sensibles) y el train enseña SOLO la Ley 1266 de 2008 (información
# financiera y crediticia). Son dos regímenes distintos y el eval evalúa la
# distinción, así que estos casos la CONTRASTAN en vez de añadir volumen.
PARES_COBERTURA = [
    dict(id="PM21", categoria="pm_hd_credito_1266", mecanismo="tutela",
         derecho="habeas_data",
         relato="Aparezco reportado en una central de riesgo por una deuda "
                "de tarjeta que pagué hace dos años. Llevo tres meses "
                "pidiéndole al banco que actualice el dato y no lo hace, y "
                "por eso me negaron un crédito de vivienda.",
         accionado="el banco y la central de riesgo",
         pretension="amparar el habeas data y ordenar la actualización del "
                    "reporte negativo",
         razon="el dato financiero es inexacto y sigue publicado: no existe "
               "otro medio judicial idóneo para la corrección y la "
               "vulneración continúa",
         fundamento_del_derecho=["art. 15 CP", "Ley 1266 de 2008"],
         hechos={"afectacion_individual": True, "continua_vulneracion": True,
                 "otro_medio_judicial": False, **pi_no()}),
    dict(id="PM22", categoria="pm_hd_sensible_1581", mecanismo="tutela",
         derecho="habeas_data",
         relato="En la empresa donde me postulé me pidieron el examen y "
                "después le mandaron mi diagnóstico de VIH al jefe del área "
                "y a dos compañeros. Nunca autoricé que compartieran eso y "
                "sigue circulando por el chat del equipo.",
         accionado="la empresa y el área de recursos humanos",
         pretension="amparar el habeas data y ordenar la supresión del dato "
                    "sensible y el cese de su circulación",
         razon="se trata de un dato sensible de salud divulgado sin "
               "autorización, cuyo tratamiento la ley prohíbe salvo "
               "excepciones; la divulgación continúa y no hay otro medio "
               "judicial idóneo",
         fundamento_del_derecho=["art. 15 CP", "Ley 1581 de 2012"],
         hechos={"afectacion_individual": True, "continua_vulneracion": True,
                 "otro_medio_judicial": False, **pi_no()}),
    dict(id="PM23", categoria="pm_hd_caducidad_2157", mecanismo="tutela",
         derecho="habeas_data",
         relato="Tuve una deuda que dejé de pagar en 2016 y la pagué toda en "
                "2021. La central me sigue mostrando el reporte negativo "
                "ahora, más de cuatro años después de haberla pagado, y ya "
                "pedí por escrito que lo quiten.",
         accionado="la central de información crediticia",
         pretension="amparar el habeas data y ordenar la eliminación del "
                    "reporte por haber caducado el término de permanencia",
         razon="el término máximo de permanencia del dato negativo ya venció "
               "y el reporte sigue publicado: la vulneración es actual y no "
               "hay otro medio idóneo",
         fundamento_del_derecho=["art. 15 CP", "Ley 2157 de 2021"],
         hechos={"afectacion_individual": True, "continua_vulneracion": True,
                 "otro_medio_judicial": False, **pi_no()}),
]

TODOS = PARES_ABSTENCION + PARES_TUTELA + PARES_COBERTURA


def _completar(c: dict) -> dict:
    """Deriva lo que el motor puede derivar y deja lo irreducible como vino."""
    if c["mecanismo"] is None:                       # abstención: sin hechos
        return {
            "id": c["id"], "split": "train", "categoria": c["categoria"],
            "relato": c["relato"], "derecho": c["derecho"],
            "fundamento": "", "accionado": c["accionado"],
            "mecanismo": None, "procede": False, "razon": c["razon"],
            "pretension": c["pretension"], "tipo": "abstencion",
            "verificado_con_reglas": False, "tipo_fuente": FUENTE,
            "fundamento_del_derecho": [], "fundamento_del_mecanismo": [],
            "origen_etiqueta": "redaccion_del_asistente",
            "fiabilidad_etiqueta": "sin_verificacion_del_motor",
            "nivel_fiabilidad": 1,
            "por_que_no_se_verifica": (
                "un caso de abstención no tiene hechos que codificar: su "
                "etiqueta afirma que no hay nada que decidir, así que el motor "
                "no puede confirmarla. Es el mismo tratamiento que los 18 de "
                "abstención que ya estaban."),
        }

    h = Hechos(**c["hechos"])
    dec = decidir(h)
    # `estrato_verificacion` devuelve (estrato, pivotes), no una cadena: el
    # estrato dice que tan solida es la verificacion y los pivotes NOMBRAN los
    # hechos de los que depende la etiqueta. Los dos van al caso, porque
    # `etiqueta_pivota_en` es lo que permite revisar la codificacion despues.
    estrato, pivotes = estrato_verificacion(h)
    fd = c.get("fundamento_del_derecho") or list(
        ARTICULO_POR_DERECHO_SEGURO(c["derecho"]))
    fm = [x.strip() for x in dec.fundamento.split(";") if x.strip()]
    return {
        "id": c["id"], "split": "train", "categoria": c["categoria"],
        "relato": c["relato"], "derecho": c["derecho"],
        "fundamento": "; ".join(dict.fromkeys(fd)),
        "accionado": c["accionado"], "mecanismo": dec.mecanismo,
        "procede": dec.procede_tutela, "razon": c["razon"],
        "pretension": c["pretension"],
        "verificado_con_reglas": True, "tipo_fuente": FUENTE,
        "fundamento_del_derecho": fd, "fundamento_del_mecanismo": fm,
        "origen_etiqueta": "motor_de_reglas",
        "fiabilidad_etiqueta": f"motor_de_reglas_{estrato}",
        "nivel_fiabilidad": {"plano": 2, "derivado": 3, "juicio": 4}[estrato],
        "fundamento_del_mecanismo_derivado": fm,
        "hechos": {k: v for k, v in c["hechos"].items() if v is not None},
        "regla_que_cierra": dec.regla,
        "estrato_verificacion": estrato,
        "etiqueta_pivota_en": pivotes,
    }


def ARTICULO_POR_DERECHO_SEGURO(derecho: str) -> list[str]:
    """El artículo del derecho, del mapa cerrado que ya usa el sistema."""
    from sistema import ARTICULO_POR_DERECHO
    a = ARTICULO_POR_DERECHO.get(derecho)
    return [a] if a else []


def main() -> int:
    escribir = "--escribir" in sys.argv
    d = json.loads(RUTA.read_text(encoding="utf-8"))
    ya = {e["id"] for e in d["ejemplos"]}

    nuevos, rechazados = [], []
    for c in TODOS:
        if c["id"] in ya:
            rechazados.append((c["id"], "el id ya existe en el dataset"))
            continue
        try:
            e = _completar(c)
        except Exception as ex:                                # noqa: BLE001
            rechazados.append((c["id"], f"{type(ex).__name__}: {ex}"))
            continue
        # LA COMPROBACIÓN QUE NO SE PUEDE SALTAR: el motor tiene que emitir
        # el mecanismo declarado. Si no, la codificación está mal y el caso
        # no entra --- venga de quien venga.
        if e["mecanismo"] != c["mecanismo"]:
            rechazados.append((
                c["id"],
                f"el motor emite `{e['mecanismo']}` y se declaró "
                f"`{c['mecanismo']}`: la codificación de hechos está mal"))
            continue
        nuevos.append(e)

    print("=" * 78)
    print("  PARES MÍNIMOS · las dos fronteras que el train no hacía aprendibles")
    print("=" * 78)
    print(f"  propuestos {len(TODOS)} · aceptados {len(nuevos)} · "
          f"rechazados {len(rechazados)}")
    print()
    for i, e in enumerate(nuevos):
        if i % 2 == 0:
            print()
        print(f"  {e['id']:<6} {str(e['mecanismo'] or 'ABSTENCIÓN'):<20}"
              f"{e['categoria']:<34}{e.get('estrato_verificacion', '—')}")
    if rechazados:
        print()
        print("  RECHAZADOS:")
        for i, m in rechazados:
            print(f"    {i:<6} {m}")

    print()
    print("  PROCEDENCIA: estos casos NO los escribió un abogado. Los redactó")
    print("  el asistente con autorización del profesor, y llevan")
    print(f"  `tipo_fuente: {FUENTE!r}`.")
    print("  No equivalen a `revision_abogado_v3.json`, donde un abogado")
    print("  revisó 40 casos y firmó 40/40.")

    if not escribir:
        print()
        print("  (en seco: corre con `--escribir` para añadirlos)")
        print("=" * 78)
        return 1 if rechazados else 0

    if rechazados:
        print()
        print("  NO SE ESCRIBE NADA: hay casos rechazados. Un dataset a medias")
        print("  es peor que uno sin ampliar.")
        print("=" * 78)
        return 1

    # NO SE INYECTAN EN `dataset.json`, Y LA RAZON ES CONCRETA.
    #
    # Se probo, y rompio dos cosas:
    #
    #   1. La prueba 3 cazo una FUGA: `PM12` reproducia literalmente el relato
    #      de `AB54` del eval set. Es el peor error posible aqui --- un caso
    #      del eval dentro del train infla la cifra sin que nada lo delate ---
    #      y se corrigio reescribiendo el caso entero.
    #   2. La prueba 59 dejo de pasar: `construir_eval_v2.py` LEE
    #      `dataset.json`, asi que ampliar el entrenamiento hace que el
    #      pipeline de constructores no converja en una pasada. Y
    #      `eval_set_v2.json` es un archivo CONGELADO byte a byte: el puente
    #      de comparacion de doce corridas depende de que no se mueva.
    #
    # Estos casos solo cambian una cifra cuando el modelo los VEA, asi que
    # meterlos hoy --- antes de una entrega certificada --- toca un archivo de
    # la huella a cambio de nada. Van a su propio archivo, verificados por el
    # motor y con su procedencia, y el entrenamiento los recoge cuando toque.
    salida = {
        "_que_es": ("casos de entrenamiento PROPUESTOS para la proxima "
                    "corrida. Todavia NO estan en `dataset.json`."),
        "_como_incorporarlos": (
            "anadir `ejemplos` a `dataset.json`, recalcular el meta con "
            "`data/reparar_meta.py --escribir`, y volver a correr el pipeline "
            "de constructores COMPLETO para que `construir_eval_v2.py` "
            "converja --- lee el dataset. Despues reentrenar."),
        "_procedencia": (
            "redactados por el asistente con autorizacion expresa del "
            "profesor, porque el abogado del proyecto no tuvo tiempo. NO "
            "equivalen a `revision_abogado_v3.json`, donde un abogado reviso "
            "40 casos y firmo 40/40. Lo que SI garantiza el motor: "
            "`decidir(hechos).mecanismo` coincide con el mecanismo declarado "
            "en los 20 casos juzgables, o no habrian entrado."),
        "_que_fronteras_ataca": {
            "abstencion_vs_via_ordinaria": (
                "6 pares. El modelo se abstenia en 9 casos CON respuesta, 8 "
                "de ellos con gold `via_ordinaria`. Los relatos de las dos "
                "clases en el train compartian los marcadores de superficie "
                "--- 12 puntos porcentuales de diferencia media ---, asi que "
                "la frontera no era aprendible. Cada par se parece por fuera "
                "y difiere en si hay un problema juridico accionable."),
            "tutela_vs_via_ordinaria": (
                "4 pares. 10 de los 13 fallos del recall de clase critica van "
                "de tutela a via_ordinaria. Cada par mantiene el escenario y "
                "cambia solo el criterio del art. 6.1 leido EN CONCRETO: si "
                "el otro medio es eficaz para ESA persona, atendiendo su "
                "edad, su salud y su urgencia."),
            "cobertura_de_citas": (
                "3 casos. El eval pide la Ley 1581 de 2012 (datos sensibles) "
                "y la Ley 2157 de 2021 (caducidad del dato negativo), y el "
                "train ensenaba SOLO la Ley 1266 de 2008 (dato crediticio). "
                "Los tres CONTRASTAN los tres regimenes en vez de anadir "
                "volumen: el modelo no puede acertar una norma que nunca vio."),
        },
        "n": len(nuevos),
        "ejemplos": nuevos,
    }
    RUTA_OUT.write_text(json.dumps(salida, ensure_ascii=False, indent=1),
                        encoding="utf-8", newline="\n")
    print()
    print(f"  escrito: data/{RUTA_OUT.name} con {len(nuevos)} casos")
    print()
    print("  NO se inyectan en `dataset.json`, y es deliberado:")
    print("   - `construir_eval_v2.py` lee el dataset, asi que ampliarlo hace")
    print("     que el pipeline de constructores no converja (prueba 59), y")
    print("     `eval_set_v2` es un archivo CONGELADO del que depende el")
    print("     puente de comparacion de doce corridas.")
    print("   - estos casos no mueven ninguna cifra hasta que el modelo los")
    print("     vea, asi que no hay nada que ganar metiendolos hoy.")
    print()
    print("  Se incorporan al reentrenar. Ver `_como_incorporarlos`.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
