"""Construye `eval_set_v3.json` como SUPERCONJUNTO ESTRICTO de v2.

POR QUE HACE FALTA
    `m1_scorecard_finetuned.json` reporta seis clases del campo `derecho` con
    soporte <= 3 --- `minimo_vital` con 1, `trabajo` con 2, y `educacion`,
    `seguridad_social`, `estabilidad_laboral_reforzada` y `habeas_data` con 3
    cada una --- y `clases_con_soporte_minimo` las nombra en cada scorecard.
    Un F1 de 0.000 con soporte 1 no es un hallazgo sobre el sistema: es la
    ausencia de muestra. El estrato `adversarial` tiene n=18, y con ese tamano
    los brazos 1 y 4 empatan sin que se pueda decir nada (T-3).

POR QUE SUPERCONJUNTO ESTRICTO Y NO UN EVAL SET NUEVO
    v2 ya se construyo asi sobre v1 --- `meta.relacion_con_v1` lo dice --- y
    por eso existe el puente `subconjunto_v1` que cada scorecard publica. Si
    v3 incluye los 69 de v2 sin tocar ni una coma, el mismo puente permite
    comparar contra las doce corridas anteriores sobre el subconjunto comun.
    Ampliar en sitio, en cambio, destruiria esa comparabilidad.

QUE SE AFIRMA Y QUE SE DERIVA --- esta es la parte que importa
    Yo NO escribo la etiqueta. Por cada caso nuevo se afirman solo los campos
    irreducibles --- el relato sintetico, los `hechos` codificados a mano, el
    derecho, las normas del derecho, el accionado y la pretension --- y el
    MECANISMO lo DERIVA `reglas.decidir()` del arbol del art. 6 del Decreto
    2591. Ademas cada caso declara `mecanismo_esperado`: si el motor no
    coincide con lo que yo esperaba, el caso SE RECHAZA. Unos `hechos` mal
    codificados producirian una etiqueta plausible y equivocada sin que nada
    lo delatara, y esa comprobacion es lo que lo impide.

    Tambien se rechaza cualquier cita que no este en `data/normas.json`. El
    proyecto mide alucinacion normativa contra ese archivo, asi que una norma
    inventada en el gold envenenaria la metrica desde los datos.

    Uso:  python -I data/ampliar_eval_set.py            (solo informa)
          python -I data/ampliar_eval_set.py --escribir (escribe v3)
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
import reglas  # noqa: E402

V2 = RAIZ / "data" / "eval_set_v2.json"
V3 = RAIZ / "data" / "eval_set_v3.json"
NORMAS = RAIZ / "data" / "normas.json"
DATASET = RAIZ / "data" / "dataset.json"

# Normas del PLANO PROCESAL por mecanismo. No se escriben en cada caso: se
# derivan del mecanismo que emite el motor, para que no puedan discrepar.
DEL_MECANISMO = {
    "tutela": ["art. 86 CP"],
    "accion_cumplimiento": ["Ley 393 de 1997", "art. 87 CP"],
    "accion_popular": ["Ley 472 de 1998", "art. 88 CP"],
    "habeas_corpus": ["Ley 1095 de 2006", "art. 30 CP"],
    "via_ordinaria": [],
}
# Los tres estratos que emite `reglas.estrato_verificacion()` y la escalera de
# fiabilidad que les corresponde. NO se adivinan: salen de cruzar los 63 casos
# juzgables de v2, donde la correspondencia es exacta y sin una sola
# discrepancia entre el estrato guardado y el que emite el motor.
#
# `juicio` es el nivel MAS DEBIL --- `equipo_ponderacion_afirmada`, nivel 4,
# la ponderacion la afirmo el equipo --- y v2 solo tiene 3 casos asi. Los
# casos nuevos se disenan para caer en `plano` o `derivado` siempre que se
# pueda, porque una etiqueta de nivel 4 pesa menos en la lectura.
FIABILIDAD = {"plano": ("motor_de_reglas_plano", 2),
              "derivado": ("motor_de_reglas_ponderado", 3),
              "juicio": ("equipo_ponderacion_afirmada", 4)}


def normas_declaradas() -> set[str]:
    n = json.loads(NORMAS.read_text(encoding="utf-8"))
    out = set()
    for seccion in ("constitucion", "decreto_2591_1991", "leyes",
                    "jurisprudencia_referencia"):
        out |= {k for k in n.get(seccion, {}) if not k.startswith("_")}
    return out


def derivar(a: dict) -> dict:
    """Un caso completo a partir de los campos irreducibles.

    Todo lo que esta funcion calcula NO se escribe a mano en ningun sitio:
    `mecanismo`, `procede`, `regla_que_cierra`, `estrato_verificacion`,
    `etiqueta_pivota_en`, `fiabilidad_etiqueta`, `nivel_fiabilidad` y el
    plano procesal del fundamento.
    """
    h = reglas.Hechos(**a["hechos"])
    d = reglas.decidir(h)
    estrato, pivota = reglas.estrato_verificacion(h)
    etiqueta, nivel = FIABILIDAD.get(estrato, ("equipo_afirmado", 4))
    del_mec = DEL_MECANISMO[d.mecanismo]
    del_der = list(a.get("fundamento_del_derecho") or [])
    # `fundamento` lleva el plano sustantivo si existe y el procesal si no,
    # que es como estan los 69 de v2 (E07 cita solo el derecho; E29, que no
    # tiene derecho, cita solo el mecanismo).
    fundamento = "; ".join(del_der) if del_der else "; ".join(sorted(del_mec))
    return {
        "id": a["id"],
        "split": "eval",
        "tipo": a["tipo"],
        "categoria": a["categoria"],
        "relato": a["relato"],
        "derecho": a["derecho"],
        "fundamento": fundamento,
        "accionado": a["accionado"],
        "mecanismo": d.mecanismo,
        "procede": d.procede_tutela,
        "razon": a["razon"],
        "pretension": a["pretension"],
        "hechos": dict(a["hechos"]),
        "verificado_con_reglas": True,
        "regla_que_cierra": d.regla,
        "dificultad": a["dificultad"],
        "etiqueta_pivota_en": pivota,
        "estrato_verificacion": estrato,
        "fundamento_del_derecho": del_der,
        "fundamento_del_mecanismo": list(del_mec),
        "origen_etiqueta": "motor_de_reglas",
        "fiabilidad_etiqueta": etiqueta,
        "nivel_fiabilidad": nivel,
        "fundamento_del_mecanismo_derivado": list(del_mec),
    }


def validar(a: dict, caso: dict, declaradas: set[str], ids: set[str],
            relatos: set[str]) -> list[str]:
    """Todo lo que descalifica un caso. Vacio = entra."""
    p = []
    # 1 · EL MOTOR TIENE QUE COINCIDIR CON LO QUE YO ESPERABA.
    if caso["mecanismo"] != a["mecanismo_esperado"]:
        p.append(f"el motor emite {caso['mecanismo']} y yo esperaba "
                 f"{a['mecanismo_esperado']}: los `hechos` estan mal "
                 "codificados (y la etiqueta habria salido plausible y falsa)")
    # 2 · NINGUNA NORMA INVENTADA.
    for cita in caso["fundamento_del_derecho"]:
        if cita not in declaradas:
            p.append(f"`{cita}` no esta en data/normas.json")
    # 3 · IDENTIDAD Y DISJUNCION.
    if a["id"] in ids:
        p.append(f"el id {a['id']} ya existe")
    rel = " ".join(a["relato"].split()).lower()
    if rel in relatos:
        p.append("el relato ya esta en v2 o en dataset.json")
    if len(rel) < 90:
        p.append(f"relato de {len(rel)} chars: demasiado corto para ser un "
                 "caso de triaje realista")
    # 4 · CAMPOS QUE NO PUEDEN QUEDAR VACIOS.
    for k in ("accionado", "pretension", "razon", "categoria"):
        if not str(a.get(k) or "").strip():
            p.append(f"`{k}` vacio")
    if a["tipo"] not in ("gold", "adversarial", "abstencion"):
        p.append(f"tipo desconocido: {a['tipo']}")
    if a["dificultad"] not in ("rutinario", "frontera", "trampa"):
        p.append(f"dificultad desconocida: {a['dificultad']}")
    return p


# ==========================================================================
# LOS CASOS NUEVOS. Solo campos irreducibles; el resto lo deriva `derivar()`.
#
# RECETARIO DE `hechos`, medido contra el motor y no supuesto:
#
#   tutela llana        afectacion_individual + continua_vulneracion
#                       -> tutela · estrato PLANO · nivel 2
#   tutela transitoria  otro_medio_judicial + medio_eficaz=False
#                       + perjuicio_irremediable con los CUATRO pi_* en True
#                       -> tutela · estrato PLANO · nivel 2
#   trampa de subsidiariedad
#                       otro_medio_judicial + medio_eficaz=True con los TRES
#                       me_* declarados y los pi_* desglosados
#                       -> via_ordinaria · estrato DERIVADO · nivel 3
#   cumplimiento        incumplimiento_normativo + afectacion_individual=False
#                       -> accion_cumplimiento · estrato PLANO · nivel 2
#
# DOS COSAS QUE EL MOTOR IMPIDE, Y ESTA BIEN QUE LAS IMPIDA:
#   - `Hechos.__post_init__` rechaza un `perjuicio_irremediable` que no se siga
#     del desglose: el test es conjuntivo. No se puede afirmar lo que los
#     subfactores niegan.
#   - Declarar los subfactores en vez de afirmar la ponderacion mueve el caso
#     de `juicio` (nivel 4, "lo afirmo el equipo") a `derivado` (nivel 3). Por
#     eso todos los casos nuevos los declaran.
#
# `trabajo` va entero a `via_ordinaria` a proposito: es lo que dice el derecho
# laboral colombiano --- el proceso ordinario suele ser idoneo --- y es por eso
# que los dos casos de `trabajo` que ya tenia v2 tambien son trampas.
# ==========================================================================
_PI_CONCURRE = dict(perjuicio_irremediable=True, pi_inminencia=True,
                    pi_gravedad=True, pi_urgencia=True,
                    pi_impostergabilidad=True)
_ME_FALLA = dict(medio_eficaz=False, me_idoneo=True, me_oportuno=False,
                 me_accesible=True)
_ME_SIRVE = dict(medio_eficaz=True, me_idoneo=True, me_oportuno=True,
                 me_accesible=True)
_PI_NO_CONCURRE = dict(perjuicio_irremediable=False, pi_inminencia=False,
                       pi_gravedad=True, pi_urgencia=False,
                       pi_impostergabilidad=False)

NUEVOS: list[dict] = [
    # ---------------- minimo_vital · 1 -> 8 ---------------------------
    {
        "id": "E46", "tipo": "gold", "dificultad": "frontera",
        "categoria": "mv_mesada_pensional_suspendida",
        "derecho": "minimo_vital", "mecanismo_esperado": "tutela",
        "relato": (
            "Tengo 78 años y vivo sola. Colpensiones me dejó de pagar la "
            "mesada desde hace cuatro meses y cada vez que llamo me dicen "
            "que el expediente está en revisión. Esa mesada es lo único con "
            "lo que cuento: ya debo dos meses de arriendo y la droga para la "
            "diabetes la estoy comprando a crédito en la farmacia del "
            "barrio."),
        "accionado": "Colpensiones",
        "razon": (
            "suspender la única fuente de ingreso de una persona de 78 años "
            "sin decidir nada deja sin sustento a un sujeto de especial "
            "protección, y el proceso ordinario no llega en el tiempo en que "
            "se necesita comer y tomar la droga"),
        "pretension": (
            "ordenar el pago inmediato de las mesadas suspendidas y el "
            "restablecimiento del pago mensual mientras se decide la revisión"),
        "fundamento_del_derecho": ["art. 11 CP", "art. 46 CP", "art. 53 CP"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       sujeto_especial_proteccion=True,
                       otro_medio_judicial=True, **_ME_FALLA,
                       **_PI_CONCURRE),
    },
    {
        "id": "E47", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "mv_licencia_paternidad_no_pagada",
        "derecho": "minimo_vital", "mecanismo_esperado": "tutela",
        "relato": (
            "Mi hijo nació hace dos meses y pedí la licencia de paternidad. "
            "La EPS dice que el pago está radicado pero no me ha llegado "
            "nada. Me tocó pedir permiso sin sueldo en el trabajo para "
            "acompañar a mi esposa, que tuvo cesárea, y en la casa no está "
            "entrando plata desde entonces."),
        "accionado": "la EPS",
        "razon": (
            "la licencia de paternidad es la prestación que reemplaza el "
            "salario durante el cuidado del recién nacido; no pagarla deja "
            "sin ingreso al hogar justo en el periodo que la norma quiso "
            "proteger"),
        "pretension": (
            "ordenar el pago de la licencia de paternidad reconocida y no "
            "desembolsada"),
        "fundamento_del_derecho": ["art. 42 CP", "art. 44 CP", "art. 53 CP"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       sujeto_especial_proteccion=True),
    },
    {
        "id": "E48", "tipo": "gold", "dificultad": "frontera",
        "categoria": "mv_pension_invalidez_suspendida",
        "derecho": "minimo_vital", "mecanismo_esperado": "tutela",
        "relato": (
            "Me reconocieron pensión de invalidez por una lesión de columna "
            "que me dejó sin poder cargar peso. El fondo me citó a revisión, "
            "no fui porque estaba hospitalizado, y me suspendieron el pago "
            "sin volver a citarme. Llevo tres meses sin un peso y no puedo "
            "trabajar en lo único que sé hacer, que es construcción."),
        "accionado": "el fondo de pensiones",
        "razon": (
            "suspender la pensión de invalidez por una inasistencia "
            "justificada, sin reprogramar la revisión, corta el ingreso de "
            "quien no puede sustituirlo con trabajo"),
        "pretension": (
            "ordenar el restablecimiento del pago de la mesada y la "
            "reprogramación de la revisión con notificación previa"),
        "fundamento_del_derecho": ["art. 11 CP", "art. 13 CP", "art. 48 CP"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       sujeto_especial_proteccion=True,
                       otro_medio_judicial=True, **_ME_FALLA,
                       **_PI_CONCURRE),
    },
    {
        "id": "A19", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "mv_salarios_proceso_laboral",
        "derecho": "minimo_vital", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "La empresa donde trabajé me quedó debiendo tres meses de "
            "sueldo. Ya conseguí otro empleo y estoy al día con mis cosas, "
            "pero quiero que me paguen lo que me deben. La empresa sigue "
            "funcionando y tiene con qué pagar."),
        "accionado": "la empresa empleadora",
        "razon": (
            "el proceso laboral ordinario es idóneo y oportuno para cobrar "
            "salarios a un empleador solvente, y no concurren los cuatro "
            "elementos del perjuicio irremediable: hay un ingreso actual y "
            "nada que sea impostergable"),
        "pretension": (
            "acudir a la jurisdicción ordinaria laboral para el cobro de los "
            "salarios adeudados"),
        "fundamento_del_derecho": ["art. 53 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A20", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "mv_cesantias_retenidas",
        "derecho": "minimo_vital", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Renuncié hace cinco meses y el empleador no ha consignado mis "
            "cesantías en el fondo. Las quiero para terminar el estudio de "
            "mi hija el año entrante. Tengo trabajo nuevo y salario "
            "completo, pero ese dinero es mío y lo están reteniendo."),
        "accionado": "el empleador anterior",
        "razon": (
            "la reclamación de cesantías tiene proceso laboral propio y "
            "efectivo; el destino previsto del dinero es futuro, así que no "
            "hay urgencia ni impostergabilidad que desplace la vía ordinaria"),
        "pretension": (
            "acudir a la jurisdicción ordinaria laboral para que se ordene la "
            "consignación de las cesantías"),
        "fundamento_del_derecho": ["art. 53 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A21", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "mv_embargo_sobre_salario",
        "derecho": "minimo_vital", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Un juzgado ordenó embargar parte de mi salario por una deuda de "
            "un crédito que no pude pagar. Me están descontando y me queda "
            "muy poco para el mes. Yo creo que están descontando más de lo "
            "que la ley permite y quiero que eso se revise."),
        "accionado": "el juzgado que decretó la medida y el banco acreedor",
        "razon": (
            "el límite legal del embargo sobre el salario se discute ante el "
            "mismo juez del proceso ejecutivo, por los recursos previstos; "
            "existe medio idóneo, oportuno y accesible y no se alega un daño "
            "inminente e impostergable"),
        "pretension": (
            "solicitar ante el juez del proceso ejecutivo la reducción del "
            "embargo al límite legal"),
        "fundamento_del_derecho": ["art. 53 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A22", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "mv_factura_contratista",
        "derecho": "minimo_vital", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Soy contratista independiente y le hice una obra a una "
            "constructora. Me firmaron el acta pero no me han pagado la "
            "última factura, que son ocho millones. Vivo de eso. Ellos dicen "
            "que hay que esperar el cierre del proyecto."),
        "accionado": "la constructora contratante",
        "razon": (
            "el cobro de una factura entre particulares se tramita por el "
            "proceso ejecutivo, que es idóneo y accesible con el acta "
            "firmada como título; no se acredita un perjuicio irremediable "
            "en sus cuatro elementos"),
        "pretension": (
            "acudir al proceso ejecutivo con el acta y la factura como título "
            "para el cobro"),
        "fundamento_del_derecho": ["art. 25 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    # ---------------- trabajo · 2 -> 8 --------------------------------
    {
        "id": "A23", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "tr_despido_sin_justa_causa",
        "derecho": "trabajo", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Me despidieron de un día para otro después de seis años en la "
            "empresa. Me dieron la liquidación pero no me dijeron ninguna "
            "razón. Quiero que me reintegren porque siento que fue por "
            "haberme quejado del jefe de área."),
        "accionado": "la empresa empleadora",
        "razon": (
            "el despido sin justa causa se discute en el proceso laboral "
            "ordinario, que puede ordenar la indemnización o el reintegro; "
            "no se invoca fuero alguno ni una condición que haga ineficaz esa "
            "vía"),
        "pretension": (
            "acudir a la jurisdicción ordinaria laboral para discutir el "
            "despido y sus consecuencias"),
        "fundamento_del_derecho": ["art. 25 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A24", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "tr_horas_extras_no_pagadas",
        "derecho": "trabajo", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Llevo dos años trabajando turnos de doce horas y nunca me han "
            "pagado las extras ni los dominicales. Tengo las planillas de "
            "entrada y salida firmadas por el supervisor. Sigo trabajando "
            "ahí y me pagan el sueldo normal cumplido."),
        "accionado": "la empresa empleadora",
        "razon": (
            "el reconocimiento y pago de horas extras es una pretensión "
            "típicamente laboral con prueba documental disponible, y el "
            "salario ordinario se sigue pagando: la vía ordinaria es idónea "
            "y oportuna"),
        "pretension": (
            "acudir a la jurisdicción ordinaria laboral para el "
            "reconocimiento y pago del trabajo suplementario"),
        "fundamento_del_derecho": ["art. 25 CP", "art. 53 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A25", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "tr_contrato_realidad",
        "derecho": "trabajo", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Durante cuatro años me hicieron firmar contratos de prestación "
            "de servicios pero yo cumplía horario, tenía jefe y usaba el "
            "uniforme de la entidad. Quiero que reconozcan que eso era un "
            "contrato de trabajo y me paguen las prestaciones."),
        "accionado": "la entidad contratante",
        "razon": (
            "la declaratoria de contrato realidad exige valoración "
            "probatoria de la subordinación y tiene vía propia ante la "
            "jurisdicción competente; no hay urgencia que la desplace"),
        "pretension": (
            "acudir a la jurisdicción competente para que se declare la "
            "existencia del contrato de trabajo y se paguen las prestaciones"),
        "fundamento_del_derecho": ["art. 25 CP", "art. 53 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A26", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "tr_vacaciones_no_concedidas",
        "derecho": "trabajo", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Tengo acumuladas las vacaciones de tres años y cada vez que las "
            "pido me dicen que no hay quién me reemplace. Nunca me las han "
            "negado por escrito, simplemente las aplazan. Quiero que me las "
            "den o que me las paguen."),
        "accionado": "la empresa empleadora",
        "razon": (
            "la concesión o compensación de vacaciones acumuladas es una "
            "pretensión laboral ordinaria; no se alega una afectación de "
            "salud o un daño que la haga impostergable"),
        "pretension": (
            "acudir a la jurisdicción ordinaria laboral para que se ordene "
            "conceder o compensar las vacaciones acumuladas"),
        "fundamento_del_derecho": ["art. 25 CP", "art. 53 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A27", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "tr_acoso_laboral_sin_agotar_comite",
        "derecho": "trabajo", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Mi jefe me grita delante de los compañeros y me cambió de "
            "puesto a uno sin funciones claras. En la empresa hay comité de "
            "convivencia pero no he puesto la queja ahí porque no creo que "
            "sirva. Quiero que paren eso ya."),
        "accionado": "la empresa empleadora y el jefe inmediato",
        "razon": (
            "la ley previó el comité de convivencia y el procedimiento ante "
            "el inspector de trabajo como mecanismos propios y accesibles "
            "para el acoso laboral, y no se han intentado; no se acredita un "
            "riesgo inminente que justifique saltarlos"),
        "pretension": (
            "presentar la queja ante el comité de convivencia laboral y, si "
            "procede, ante el inspector de trabajo"),
        "fundamento_del_derecho": ["art. 25 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A28", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "tr_reintegro_tras_renuncia",
        "derecho": "trabajo", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Renuncié porque el ambiente estaba muy pesado, pero firmé la "
            "carta el mismo día que me la pidieron y no me dejaron pensarlo. "
            "Ahora quiero volver a mi puesto porque creo que esa renuncia no "
            "fue voluntaria."),
        "accionado": "la empresa empleadora",
        "razon": (
            "alegar que una renuncia fue forzada exige debate probatorio "
            "sobre el consentimiento y se tramita en el proceso laboral "
            "ordinario; no hay sujeto de especial protección ni perjuicio "
            "irremediable acreditado"),
        "pretension": (
            "acudir a la jurisdicción ordinaria laboral para que se declare "
            "la ineficacia de la renuncia y se ordene el reintegro"),
        "fundamento_del_derecho": ["art. 25 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    # ---------------- educacion · 3 -> 8 ------------------------------
    {
        "id": "E49", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "educacion_transporte_rural",
        "derecho": "educacion", "mecanismo_esperado": "tutela",
        "relato": (
            "Mi hijo tiene nueve años y la escuela más cercana queda a hora "
            "y media caminando por trocha. El municipio tenía ruta escolar y "
            "este año la quitó sin avisar. Desde febrero el niño no ha "
            "podido ir y ya perdió el primer periodo."),
        "accionado": "la alcaldía municipal y la Secretaría de Educación",
        "razon": (
            "suprimir el transporte escolar que hacía posible la asistencia "
            "de un menor en zona rural interrumpe de hecho su acceso a la "
            "educación, que el Estado debe garantizar"),
        "pretension": (
            "ordenar el restablecimiento de la ruta escolar o una "
            "alternativa de transporte que permita la asistencia del menor"),
        "fundamento_del_derecho": ["art. 44 CP", "art. 67 CP"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       sujeto_especial_proteccion=True),
    },
    {
        "id": "E50", "tipo": "gold", "dificultad": "frontera",
        "categoria": "educacion_matricula_sin_documentos",
        "derecho": "educacion", "mecanismo_esperado": "tutela",
        "relato": (
            "Llegamos de Venezuela hace ocho meses. En el colegio me dicen "
            "que no pueden matricular a mis dos hijas porque no tienen "
            "documento colombiano ni los certificados de notas apostillados. "
            "Las niñas tienen 7 y 11 años y llevan todo el año sin estudiar."),
        "accionado": "la institución educativa y la Secretaría de Educación",
        "razon": (
            "exigir documentos de imposible consecución para matricular a "
            "menores migrantes convierte un requisito administrativo en una "
            "barrera de acceso a la educación, que es un derecho fundamental "
            "de los niños sin distinción de nacionalidad"),
        "pretension": (
            "ordenar la matrícula de las menores con los documentos "
            "disponibles y la aplicación del modelo de nivelación que "
            "corresponda"),
        "fundamento_del_derecho": ["art. 13 CP", "art. 44 CP", "art. 67 CP"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       sujeto_especial_proteccion=True),
    },
    {
        "id": "E51", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "educacion_cancelacion_por_embarazo",
        "derecho": "educacion", "mecanismo_esperado": "tutela",
        "relato": (
            "Tengo 16 años y estoy en once. Cuando se supo que estoy "
            "embarazada la coordinadora me dijo que me cambiara a validación "
            "los sábados para no afectar a las otras niñas. Yo quiero "
            "terminar con mi curso, no he perdido ninguna materia."),
        "accionado": "la institución educativa",
        "razon": (
            "trasladar a una estudiante a otra jornada por su embarazo, sin "
            "razón académica, es una discriminación que afecta la "
            "continuidad de su educación"),
        "pretension": (
            "ordenar la permanencia de la estudiante en su jornada y curso, "
            "con los apoyos académicos que requiera"),
        "fundamento_del_derecho": ["art. 13 CP", "art. 43 CP", "art. 67 CP"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       sujeto_especial_proteccion=True),
    },
    {
        "id": "A29", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "educacion_cartera_universidad_privada",
        "derecho": "educacion", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Estudio en una universidad privada y quedé debiendo media "
            "matrícula del semestre pasado. No me dejan inscribir materias "
            "hasta que pague. Yo firmé un acuerdo de pago pero me atrasé dos "
            "cuotas porque perdí el trabajo."),
        "accionado": "la universidad privada",
        "razon": (
            "el incumplimiento de un acuerdo de pago en educación superior "
            "privada es una controversia contractual con vía ordinaria "
            "idónea; no se trata de educación básica obligatoria ni de un "
            "menor de edad"),
        "pretension": (
            "acudir a la jurisdicción ordinaria para discutir el acuerdo de "
            "pago y sus condiciones"),
        "fundamento_del_derecho": ["art. 67 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A30", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "educacion_perdida_de_ano_academica",
        "derecho": "educacion", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "A mi hijo lo dejaron repitiendo quinto. Perdió cuatro materias "
            "y faltó mucho, eso es verdad, pero yo creo que los profesores "
            "le tenían bronca. Quiero que lo pasen a sexto porque ya está "
            "grande para repetir."),
        "accionado": "la institución educativa",
        "razon": (
            "la promoción escolar es una valoración académica reglada que se "
            "discute por los conductos del establecimiento y de la secretaría "
            "de educación; el relato reconoce las causales objetivas y no "
            "alega discriminación acreditable"),
        "pretension": (
            "agotar la reclamación académica ante el establecimiento y la "
            "Secretaría de Educación"),
        "fundamento_del_derecho": ["art. 67 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    # ---------------- seguridad_social · 3 -> 8 -----------------------
    {
        "id": "E52", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "ss_incapacidades_no_pagadas",
        "derecho": "seguridad_social", "mecanismo_esperado": "tutela",
        "relato": (
            "Tuve un accidente y llevo siete meses incapacitado. La EPS dice "
            "que después del día 180 le corresponde al fondo de pensiones, y "
            "el fondo dice que a la EPS. Llevo cuatro meses sin que nadie me "
            "pague la incapacidad y no puedo trabajar porque sigo con el "
            "brazo inmovilizado."),
        "accionado": "la EPS y el fondo de pensiones",
        "razon": (
            "el desacuerdo entre las entidades sobre quién paga a partir del "
            "día 181 no puede trasladarse al afiliado, que queda sin el pago "
            "que sustituye su salario mientras no puede trabajar"),
        "pretension": (
            "ordenar el pago de las incapacidades causadas y definir la "
            "entidad obligada a continuar el pago"),
        "fundamento_del_derecho": ["art. 48 CP", "Ley 100 de 1993"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True),
    },
    {
        "id": "E53", "tipo": "gold", "dificultad": "frontera",
        "categoria": "ss_sobrevivientes_menores",
        "derecho": "seguridad_social", "mecanismo_esperado": "tutela",
        "relato": (
            "Mi esposo murió en un accidente de trabajo hace diez meses. "
            "Pedí la pensión de sobrevivientes para mí y mis dos hijos de 6 "
            "y 9 años. El fondo dice que falta una declaración de "
            "convivencia que ya mandé dos veces. Mientras tanto vivimos de "
            "lo que me da mi mamá."),
        "accionado": "el fondo de pensiones",
        "razon": (
            "exigir reiteradamente un documento ya aportado prolonga sin "
            "causa el reconocimiento de la prestación que sustituye el "
            "ingreso del hogar, con dos menores de edad dependientes"),
        "pretension": (
            "ordenar la decisión de fondo sobre el reconocimiento de la "
            "pensión de sobrevivientes"),
        "fundamento_del_derecho": ["art. 44 CP", "art. 48 CP",
                                   "Ley 100 de 1993"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       sujeto_especial_proteccion=True),
    },
    {
        "id": "E54", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "ss_afiliacion_negada_discapacidad",
        "derecho": "seguridad_social", "mecanismo_esperado": "tutela",
        "relato": (
            "Mi hermano tiene parálisis cerebral y 31 años. Siempre estuvo "
            "como beneficiario de mi papá, que murió. La EPS lo retiró "
            "diciendo que ya es mayor de edad y que debe afiliarse como "
            "cotizante. Él no puede trabajar y lleva dos meses sin servicio "
            "ni terapias."),
        "accionado": "la EPS",
        "razon": (
            "retirar del sistema a una persona en situación de discapacidad "
            "dependiente, por un criterio de edad que no atiende su "
            "condición, interrumpe su acceso a la seguridad social y a las "
            "terapias que recibía"),
        "pretension": (
            "ordenar la reactivación de la afiliación en calidad de "
            "beneficiario y la continuidad de las terapias"),
        "fundamento_del_derecho": ["art. 13 CP", "art. 48 CP"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       sujeto_especial_proteccion=True),
    },
    {
        "id": "A31", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "ss_reliquidacion_pensional",
        "derecho": "seguridad_social", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Me pensionaron hace tres años pero creo que me liquidaron mal "
            "la mesada porque no tuvieron en cuenta unas primas. Cobro "
            "cumplidamente todos los meses. Quiero que me recalculen y me "
            "paguen el retroactivo."),
        "accionado": "Colpensiones",
        "razon": (
            "la reliquidación de una mesada que se viene pagando es una "
            "controversia de cálculo con proceso ordinario idóneo; no hay "
            "interrupción del ingreso ni urgencia que desplace esa vía"),
        "pretension": (
            "acudir a la jurisdicción competente para la reliquidación de la "
            "mesada y el retroactivo"),
        "fundamento_del_derecho": ["art. 48 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A32", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "ss_traslado_de_regimen",
        "derecho": "seguridad_social", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Quiero devolverme del fondo privado a Colpensiones porque me "
            "conviene más, pero me dicen que ya no puedo porque me faltan "
            "menos de diez años para la edad de pensión. Yo digo que me "
            "asesoraron mal cuando me trasladé en el 2005."),
        "accionado": "el fondo privado de pensiones y Colpensiones",
        "razon": (
            "la nulidad del traslado por asesoría deficiente exige debate "
            "probatorio y tiene vía ordinaria propia; el afiliado sigue "
            "cotizando y no hay prestación interrumpida"),
        "pretension": (
            "acudir a la jurisdicción ordinaria laboral para discutir la "
            "validez del traslado de régimen"),
        "fundamento_del_derecho": ["art. 48 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    # ---------- estabilidad_laboral_reforzada · 3 -> 8 ----------------
    {
        "id": "E55", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "elr_despido_con_restricciones_medicas",
        "derecho": "estabilidad_laboral_reforzada",
        "mecanismo_esperado": "tutela",
        "relato": (
            "Me operaron del hombro por una lesión que me dio cargando en la "
            "bodega. Volví con restricciones médicas de no levantar más de "
            "cinco kilos. A las tres semanas me liquidaron diciendo que "
            "reestructuraron el área. Nunca pidieron permiso al Ministerio."),
        "accionado": "la empresa empleadora",
        "razon": (
            "despedir a un trabajador con restricciones médicas conocidas, "
            "sin la autorización del inspector de trabajo, activa la "
            "presunción de despido discriminatorio que la estabilidad "
            "laboral reforzada protege"),
        "pretension": (
            "ordenar el reintegro con reubicación acorde a las restricciones "
            "médicas y el pago de lo dejado de percibir"),
        "fundamento_del_derecho": ["art. 13 CP", "art. 53 CP",
                                   "Ley 361 de 1997"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       sujeto_especial_proteccion=True),
    },
    {
        "id": "E56", "tipo": "gold", "dificultad": "frontera",
        "categoria": "elr_no_reubicacion",
        "derecho": "estabilidad_laboral_reforzada",
        "mecanismo_esperado": "tutela",
        "relato": (
            "Tengo una enfermedad en la columna calificada con pérdida de "
            "capacidad del 32%. Salud ocupacional dijo por escrito que me "
            "reubicaran en un puesto sin bipedestación prolongada. Llevo "
            "cinco meses en el mismo puesto de pie ocho horas y el dolor "
            "empeoró. Me dicen que no hay otro cargo."),
        "accionado": "la empresa empleadora",
        "razon": (
            "incumplir una recomendación de reubicación escrita, sosteniendo "
            "al trabajador en el puesto que agrava su condición, vulnera la "
            "estabilidad laboral reforzada sin necesidad de que haya despido"),
        "pretension": (
            "ordenar la reubicación en un puesto compatible con las "
            "recomendaciones de salud ocupacional"),
        "fundamento_del_derecho": ["art. 13 CP", "art. 25 CP",
                                   "Ley 361 de 1997"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       sujeto_especial_proteccion=True),
    },
    {
        "id": "E57", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "elr_despido_en_incapacidad",
        "derecho": "estabilidad_laboral_reforzada",
        "mecanismo_esperado": "tutela",
        "relato": (
            "Estaba incapacitada por una cirugía de tiroides y me llegó la "
            "carta de terminación del contrato al correo mientras seguía "
            "incapacitada. El contrato era a término fijo y dicen que "
            "simplemente se venció, pero llevaba cuatro renovaciones "
            "seguidas."),
        "accionado": "la empresa empleadora",
        "razon": (
            "terminar el vínculo durante una incapacidad vigente, en un "
            "contrato renovado cuatro veces, traslada al trabajador el "
            "riesgo de su estado de salud y desconoce la protección "
            "reforzada"),
        "pretension": (
            "ordenar el reintegro y el pago de los aportes y salarios "
            "causados desde la terminación"),
        "fundamento_del_derecho": ["art. 13 CP", "art. 53 CP",
                                   "Ley 361 de 1997"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       sujeto_especial_proteccion=True),
    },
    {
        "id": "A33", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "elr_despido_con_autorizacion",
        "derecho": "estabilidad_laboral_reforzada",
        "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Me despidieron y yo tengo una discapacidad auditiva "
            "certificada. Pero la empresa pidió permiso al inspector de "
            "trabajo, el inspector lo autorizó porque hubo cierre total de "
            "la planta, y a todos los de mi turno los liquidaron igual. Yo "
            "quiero que me reintegren."),
        "accionado": "la empresa empleadora",
        "razon": (
            "con autorización previa del inspector y cierre que afectó a "
            "todo el turno, no hay presunción de despido discriminatorio; la "
            "discusión sobre la indemnización corresponde al proceso laboral "
            "ordinario"),
        "pretension": (
            "acudir a la jurisdicción ordinaria laboral para discutir la "
            "indemnización derivada de la terminación"),
        "fundamento_del_derecho": ["Ley 361 de 1997"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       sujeto_especial_proteccion=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A34", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "elr_prepensionado_sin_condicion_de_salud",
        "derecho": "estabilidad_laboral_reforzada",
        "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Me faltan dos años para pensionarme y me despidieron sin justa "
            "causa. Estoy sano, nunca he tenido incapacidades. Dicen que me "
            "pagan la indemnización completa, pero yo quiero el reintegro "
            "porque soy prepensionado."),
        "accionado": "la empresa empleadora",
        "razon": (
            "sin condición de salud ni fuero legal invocable, la "
            "proximidad a la pensión se discute como pretensión laboral "
            "ordinaria; la indemnización ofrecida y la ausencia de "
            "afectación actual descartan el perjuicio irremediable"),
        "pretension": (
            "acudir a la jurisdicción ordinaria laboral para discutir el "
            "reintegro o la indemnización"),
        "fundamento_del_derecho": ["art. 53 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    # ---------------- habeas_data · 3 -> 8 ----------------------------
    {
        "id": "E58", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "hd_reporte_tras_pagar",
        "derecho": "habeas_data", "mecanismo_esperado": "tutela",
        "relato": (
            "Pagué toda la deuda de la tarjeta en enero y tengo el paz y "
            "salvo del banco. En las centrales sigo apareciendo en mora "
            "nueve meses después. Pedí la actualización por escrito dos "
            "veces y no me responden. Por eso me negaron el crédito de "
            "vivienda."),
        "accionado": "el banco y la central de riesgo",
        "razon": (
            "mantener un reporte de mora después del pago, con paz y salvo "
            "en mano y solicitudes de actualización sin respuesta, es un "
            "dato inexacto cuya corrección el habeas data protege"),
        "pretension": (
            "ordenar la actualización del reporte para que refleje el pago "
            "efectuado"),
        "fundamento_del_derecho": ["art. 15 CP", "Ley 1266 de 2008"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True),
    },
    {
        "id": "E59", "tipo": "gold", "dificultad": "frontera",
        "categoria": "hd_termino_legal_excedido",
        "derecho": "habeas_data", "mecanismo_esperado": "tutela",
        "relato": (
            "Tuve una mora con una cooperativa que pagué hace seis años. El "
            "reporte negativo sigue publicado. Cuando reclamo me dicen que "
            "el dato permanece por política interna de la entidad. A mí me "
            "explicaron que eso solo podía quedarse cuatro años."),
        "accionado": "la cooperativa y la central de riesgo",
        "razon": (
            "la permanencia del dato negativo tiene un término legal máximo "
            "y una política interna no puede extenderlo; conservarlo vencido "
            "el término vulnera el habeas data"),
        "pretension": (
            "ordenar la eliminación del reporte negativo por haberse "
            "cumplido el término legal de permanencia"),
        "fundamento_del_derecho": ["art. 15 CP", "Ley 1266 de 2008",
                                   "Ley 2157 de 2021"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True),
    },
    {
        "id": "E60", "tipo": "gold", "dificultad": "frontera",
        "categoria": "hd_dato_de_salud_compartido",
        "derecho": "habeas_data", "mecanismo_esperado": "tutela",
        "relato": (
            "En la empresa donde me postulé me preguntaron por mi "
            "tratamiento psiquiátrico. Yo nunca lo conté: resulta que la "
            "EPS le entregó mi historia clínica a la empresa cuando pidieron "
            "el examen de ingreso. No firmé ninguna autorización para eso."),
        "accionado": "la EPS y la empresa",
        "razon": (
            "la historia clínica es un dato sensible y su entrega a un "
            "tercero sin autorización del titular vulnera el habeas data, con "
            "independencia de que el proceso de selección continúe"),
        "pretension": (
            "ordenar la supresión del dato en poder de la empresa y "
            "establecer la prohibición de nuevos traslados sin autorización"),
        "fundamento_del_derecho": ["art. 15 CP", "Ley 1581 de 2012"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True),
    },
    {
        "id": "A35", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "hd_reporte_veraz_vigente",
        "derecho": "habeas_data", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Aparezco reportado en las centrales por un crédito que "
            "efectivamente no he pagado. Sí me notificaron antes de "
            "reportarme. Pero el reporte me está cerrando puertas y quiero "
            "que lo quiten mientras me organizo para pagar."),
        "accionado": "el banco y la central de riesgo",
        "razon": (
            "el habeas data protege la veracidad y la actualización del "
            "dato, no su supresión cuando es cierto, vigente y fue "
            "notificado; la renegociación de la deuda es un asunto "
            "contractual con vía propia"),
        "pretension": (
            "acudir a la entidad para un acuerdo de pago y, en su caso, a la "
            "jurisdicción ordinaria por la controversia contractual"),
        "fundamento_del_derecho": ["art. 15 CP", "Ley 1266 de 2008"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A36", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "hd_rectificacion_en_tramite",
        "derecho": "habeas_data", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Radiqué hace cuatro días un reclamo en la central de riesgo "
            "para que corrijan mi segundo apellido, que está mal escrito. "
            "Todavía no me contestan. Quiero que un juez les ordene "
            "corregirlo ya."),
        "accionado": "la central de riesgo",
        "razon": (
            "la ley fija un término para resolver el reclamo y aún no ha "
            "transcurrido: el mecanismo propio está en curso y es idóneo, "
            "así que no hay vulneración consumada ni urgencia que lo "
            "desplace"),
        "pretension": (
            "esperar la respuesta al reclamo dentro del término legal y, si "
            "se incumple, reclamar ante la autoridad de protección de datos"),
        "fundamento_del_derecho": ["art. 15 CP", "Ley 1581 de 2012"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    # ---------------- debido_proceso · 4 -> 8 -------------------------
    # No estaban por debajo del umbral de `clases_con_soporte_minimo` (<= 3),
    # asi que la bandera no las nombraba. Se suben igual al piso de 8 que usa
    # el resto del eval set: una clase con n=4 pasa la comprobacion y sigue
    # dando un F1 que se mueve 25 puntos por caso.
    {
        "id": "E61", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "dp_sancion_sin_descargos",
        "derecho": "debido_proceso", "mecanismo_esperado": "tutela",
        "relato": (
            "Vivo en un conjunto residencial. La administración me puso una "
            "multa de dos millones por un daño en el ascensor que dicen que "
            "causó mi hijo. Nunca me citaron a ninguna reunión, no me "
            "dejaron explicar y ya me la están cobrando en la cuota de "
            "administración."),
        "accionado": "la administración del conjunto residencial",
        "razon": (
            "imponer una sanción económica sin citación previa ni "
            "oportunidad de ser oído desconoce el debido proceso que "
            "también rige las actuaciones de los particulares que ejercen "
            "funciones de autoridad en la copropiedad"),
        "pretension": (
            "ordenar dejar sin efecto la sanción y, si se insiste en ella, "
            "adelantar el procedimiento con citación y descargos"),
        "fundamento_del_derecho": ["art. 29 CP"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True),
    },
    {
        "id": "E62", "tipo": "gold", "dificultad": "frontera",
        "categoria": "dp_notificacion_por_aviso_indebida",
        "derecho": "debido_proceso", "mecanismo_esperado": "tutela",
        "relato": (
            "Me enteré por un amigo de que una entidad me había sancionado "
            "con una inhabilidad. Dicen que me notificaron por aviso en la "
            "cartelera, pero yo tengo registrada mi dirección y mi correo "
            "en esa misma entidad desde hace años y nunca me escribieron. "
            "Ya se me pasó el plazo para los recursos."),
        "accionado": "la entidad que impuso la sanción",
        "razon": (
            "acudir a la notificación por aviso cuando se conoce la "
            "dirección del interesado impide de hecho el ejercicio de los "
            "recursos, y el plazo vencido convierte el defecto en "
            "irreparable por la vía ordinaria"),
        "pretension": (
            "ordenar la notificación personal del acto sancionatorio y la "
            "reapertura del término para interponer recursos"),
        "fundamento_del_derecho": ["art. 29 CP", "Ley 1437 de 2011"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True,
                       otro_medio_judicial=True, **_ME_FALLA, **_PI_CONCURRE),
    },
    {
        "id": "A37", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "dp_recursos_sin_agotar",
        "derecho": "debido_proceso", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Una entidad me negó un permiso. Me notificaron bien, en mi "
            "casa, y me dijeron que tenía diez días para el recurso de "
            "reposición. No lo puse porque me pareció que no iba a servir. "
            "Quiero que un juez revise la decisión."),
        "accionado": "la entidad que negó el permiso",
        "razon": (
            "el recurso de reposición estaba disponible, era accesible y se "
            "notificó en forma; no agotarlo por desconfianza no habilita el "
            "amparo, y la nulidad del acto tiene vía ordinaria propia"),
        "pretension": (
            "agotar los recursos administrativos y, en su caso, acudir al "
            "medio de control de nulidad"),
        "fundamento_del_derecho": ["art. 29 CP", "Ley 1437 de 2011"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    {
        "id": "A38", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "dp_desacuerdo_con_la_prueba",
        "derecho": "debido_proceso", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "En un proceso civil el juez le creyó al testigo de la otra "
            "parte y no al mío. A mí me citaron, fui, presenté mis pruebas y "
            "me dejaron alegar. Pero la sentencia me pareció injusta y "
            "quiero que la revisen."),
        "accionado": "el juzgado civil",
        "razon": (
            "el relato describe un proceso con citación, pruebas y alegatos: "
            "el desacuerdo con la valoración probatoria se ataca por los "
            "recursos del propio proceso, no por el amparo"),
        "pretension": (
            "interponer los recursos previstos contra la sentencia dentro "
            "del mismo proceso"),
        "fundamento_del_derecho": ["art. 29 CP"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
    # ---------------- peticion · 5 -> 8 -------------------------------
    {
        "id": "E63", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "peticion_a_privado_servicio_publico",
        "derecho": "peticion", "mecanismo_esperado": "tutela",
        "relato": (
            "Le escribí a la empresa de energía hace dos meses pidiendo que "
            "me expliquen un cobro de reconexión que nunca me hicieron. "
            "Radiqué con sello, tengo el número. No me han contestado nada y "
            "el cobro sigue apareciendo cada mes."),
        "accionado": "la empresa de servicios públicos",
        "razon": (
            "el derecho de petición también se ejerce ante particulares que "
            "prestan servicios públicos, y dos meses sin respuesta a una "
            "solicitud radicada excede cualquier término legal"),
        "pretension": (
            "ordenar la respuesta de fondo a la petición radicada sobre el "
            "cobro de reconexión"),
        "fundamento_del_derecho": ["art. 23 CP", "Ley 1755 de 2015"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True),
    },
    {
        "id": "E64", "tipo": "gold", "dificultad": "frontera",
        "categoria": "peticion_remitida_sin_competencia",
        "derecho": "peticion", "mecanismo_esperado": "tutela",
        "relato": (
            "Pedí una certificación a una entidad y me contestaron que no "
            "eran competentes y que la remitían. Eso fue hace tres meses. "
            "Nunca me dijeron a quién se la mandaron ni me llegó respuesta "
            "de nadie. Cada vez que pregunto me repiten que ya la "
            "remitieron."),
        "accionado": "la entidad que recibió la petición",
        "razon": (
            "remitir por falta de competencia solo cumple el derecho de "
            "petición si se informa al peticionario a quién se remitió y la "
            "entidad competente responde; sin eso la petición queda sin "
            "respuesta de fondo"),
        "pretension": (
            "ordenar que se informe el destinatario de la remisión y que la "
            "entidad competente resuelva de fondo"),
        "fundamento_del_derecho": ["art. 23 CP", "Ley 1755 de 2015"],
        "hechos": dict(afectacion_individual=True, continua_vulneracion=True),
    },
    {
        "id": "A39", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "peticion_dentro_del_termino",
        "derecho": "peticion", "mecanismo_esperado": "via_ordinaria",
        "relato": (
            "Radiqué una petición hace seis días hábiles pidiendo copias de "
            "un expediente. Todavía no me responden y necesito esas copias. "
            "Quiero que un juez les ordene contestarme de una vez."),
        "accionado": "la entidad ante la que se radicó la petición",
        "razon": (
            "el término legal para resolver una petición de documentos no ha "
            "transcurrido, así que no hay omisión que amparar: el mecanismo "
            "propio está corriendo y es idóneo"),
        "pretension": (
            "esperar el vencimiento del término legal y, si se incumple, "
            "reclamar la respuesta"),
        "fundamento_del_derecho": ["art. 23 CP", "Ley 1755 de 2015"],
        "hechos": dict(afectacion_individual=True, otro_medio_judicial=True,
                       **_ME_SIRVE, **_PI_NO_CONCURRE),
    },
]


def main() -> int:
    escribir = "--escribir" in sys.argv
    v2 = json.loads(V2.read_text(encoding="utf-8"))
    viejos = v2["ejemplos"]
    declaradas = normas_declaradas()
    ids = {c["id"] for c in viejos}
    relatos = {" ".join(c["relato"].split()).lower() for c in viejos}
    if DATASET.exists():
        _ds = json.loads(DATASET.read_text(encoding="utf-8"))
        for parte in ("train", "validation", "ejemplos"):
            for c in (_ds.get(parte) or []):
                if isinstance(c, dict) and c.get("relato"):
                    relatos.add(" ".join(c["relato"].split()).lower())

    print("=" * 78)
    print("  AMPLIACION DEL EVAL SET · v2 -> v3 (superconjunto estricto)")
    print("=" * 78)
    print(f"  v2: {len(viejos)} casos · normas declaradas: {len(declaradas)}")
    print(f"  casos nuevos propuestos: {len(NUEVOS)}")
    print()

    aceptados, rechazados = [], []
    for a in NUEVOS:
        try:
            caso = derivar(a)
        except Exception as ex:                               # noqa: BLE001
            rechazados.append((a.get("id", "?"), [f"no se pudo derivar: {ex}"]))
            continue
        problemas = validar(a, caso, declaradas, ids, relatos)
        if problemas:
            rechazados.append((a["id"], problemas))
            continue
        ids.add(a["id"])
        relatos.add(" ".join(a["relato"].split()).lower())
        aceptados.append(caso)

    if rechazados:
        print(f"  {len(rechazados)} RECHAZADO(S) --- no entran al eval set:")
        for cid, ps in rechazados:
            print(f"    {cid}")
            for x in ps:
                print(f"       - {x}")
        print()

    if not aceptados:
        print("  Sin casos aceptados: v3 no se escribe.")
        print("=" * 78)
        return 1 if rechazados else 0

    import collections
    todos = viejos + aceptados
    print(f"  {len(aceptados)} aceptado(s) · v3 tendria {len(todos)} casos")
    print()
    for campo in ("derecho", "mecanismo", "tipo"):
        antes = collections.Counter(c.get(campo) for c in viejos)
        ahora = collections.Counter(c.get(campo) for c in todos)
        print(f"  {campo}:")
        for k in sorted(ahora, key=lambda x: (-ahora[x], str(x))):
            a_, b_ = antes.get(k, 0), ahora[k]
            marca = "  <-- sube" if b_ > a_ else ""
            print(f"     {str(k):34s} {a_:>3} -> {b_:>3}{marca}")
        print()

    flacas = [k for k, v in collections.Counter(
        c.get("derecho") for c in todos).items()
        if v <= 3 and k not in (None, "no_determinable")]
    print(f"  clases de `derecho` con soporte <= 3: "
          f"{', '.join(flacas) if flacas else 'ninguna'}")

    if not escribir:
        print()
        print("  (solo informe; corre con --escribir para generar v3)")
        print("=" * 78)
        return 0

    meta = dict(v2["meta"])
    meta.update({
        "nombre": "tutela-co-triage-eval-v3",
        "version": "3.0.0",
        "derivado_de": "data/eval_set_v2.json v2.0.0",
        "relacion_con_v2": (
            "SUPERCONJUNTO ESTRICTO. Los 69 casos de v2 estan incluidos sin "
            "ninguna modificacion, asi que el puente `subconjunto_v1` y la "
            "comparacion contra las corridas anteriores siguen valiendo sobre "
            "el subconjunto comun."),
        "composicion": dict(collections.Counter(c["tipo"] for c in todos)),
        "balance_mecanismo": dict(collections.Counter(
            c["mecanismo"] for c in todos if c.get("mecanismo"))),
        "por_dificultad": dict(collections.Counter(
            c["dificultad"] for c in todos)),
        # SE RECALCULA, no se arrastra. `baseline_clase_mayoritaria` es el
        # liston contra el que se lee `acc_mecanismo`: dejar el 0.4286 de v2
        # en un conjunto con otra composicion haria que todos los scorecards
        # se comparasen contra un liston que ya no existe. Es el mismo defecto
        # --- una cifra afirmada que no se entera de que el dato cambio ---
        # que obligo a derivar la seccion 7 del reporte.
        "baseline_clase_mayoritaria": round(
            max(collections.Counter(
                c["mecanismo"] for c in todos if c.get("mecanismo")).values())
            / sum(1 for c in todos if c.get("mecanismo")), 4),
        "baseline_clase_mayoritaria_v2": v2["meta"].get(
            "baseline_clase_mayoritaria"),
        "motivo_v3": [
            "M1-4: seis clases de `derecho` tenian soporte <= 3 y "
            "`clases_con_soporte_minimo` las nombraba en cada scorecard.",
            "T-3: el estrato adversarial tenia n=18 y los brazos 1 y 4 "
            "empataban sin que se pudiera concluir nada.",
        ],
        "verificacion_v3": (
            "Los casos nuevos declaran `mecanismo_esperado` y el mecanismo lo "
            "DERIVA `reglas.decidir()`: si no coinciden, el caso se rechaza. "
            "Las citas se comprueban contra `data/normas.json`. Lo hace "
            "`data/ampliar_eval_set.py`."),
    })
    V3.write_text(json.dumps({"meta": meta, "ejemplos": todos},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print()
    print(f"  escrito: data/eval_set_v3.json · {len(todos)} casos")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
