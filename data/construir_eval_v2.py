"""
Construye `eval_set_v2.json` y anota `dificultad` en el eval set v1.

Tres cosas, porque las tres tocan el mismo artefacto:

  ROADMAP #2  eval_set_v2.json con las clases minoritarias a 8 casos.
  ROADMAP #3  casos de `no_determinable` en el eval, hoy solo en eval_m3.
  ROADMAP #5  campo `dificultad` (rutinario / frontera / trampa).

Por que v2 es un SUPERCONJUNTO y no un reemplazo. El eval set v1 es la vara
con la que se midieron once corridas de tres modulos. Agrandarlo en sitio
invalida esa comparacion en silencio. v2 contiene los 46 casos de v1 SIN TOCAR
(mismos ids, mismos relatos, mismas etiquetas) mas 23 nuevos, de modo que
cualquier diferencia entre las dos columnas es atribuible UNICAMENTE a los
casos agregados. Eso es lo que hace legible la tabla puente.

Por que `dificultad` SI se escribe en v1. Es metadato: ninguna metrica lo lee,
ningun relato cambia, ninguna etiqueta cambia. `n` sigue siendo 46, que es la
senal que `corridas.version_datos()` registra. Permite releer las once
corridas existentes por nivel de dificultad sin volver a correr nada.

El script es idempotente y falla sin escribir si el motor de reglas no deriva
la etiqueta de algun caso nuevo, o si algun relato se repite.
"""
from __future__ import annotations
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.reglas import Hechos, decidir, estrato_verificacion  # noqa: E402

FUND_HC = ("art. 28 CP; art. 30 CP; Ley 1095 de 2006; "
           "art. 6.2 Decreto 2591 de 1991")
FUND_AC = "art. 87 CP; Ley 393 de 1997"
FUND_AP = "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991"

RAZON_AC = ("se reclama el acatamiento de un deber impuesto por una norma "
            "vigente, sin que se alegue la vulneración concreta de un derecho "
            "fundamental individual")
RAZON_AP = ("lo que se busca proteger son derechos e intereses colectivos del "
            "artículo 4 de la Ley 472, excluidos del ámbito de la tutela")

# --------------------------------------------------------------------------
# +6 habeas corpus (hoy 2: E31 y A10). Ninguno repite un escenario del
# dataset (HC01-HC15) ni del eval v1.
# --------------------------------------------------------------------------
HABEAS_CORPUS = [
    {
        "id": "E35", "tipo": "gold", "dificultad": "frontera",
        "categoria": "hc_traslado_por_proteccion_prolongado",
        "relato": "A mi hijo lo subieron a una patrulla el sábado en la noche "
                  "a la salida de un bar, dijeron que era un traslado por "
                  "protección porque estaba tomado. Ya es lunes en la mañana y "
                  "sigue en la estación. No lo han dejado salir ni hay ninguna "
                  "denuncia contra él.",
        "accionado": "Policía Nacional",
        "razon": "el traslado por protección tiene un límite máximo de doce "
                 "horas y su prolongación más allá de ese término convierte una "
                 "medida que empezó siendo legal en privación ilegal de la "
                 "libertad",
        "pretension": "interponer habeas corpus para que se ordene la libertad "
                      "inmediata por haberse superado el término máximo del "
                      "traslado por protección",
    },
    {
        "id": "E36", "tipo": "gold", "dificultad": "frontera",
        "categoria": "hc_medida_seguridad_vencida",
        "relato": "A mi hermano el juez le impuso una medida de seguridad en un "
                  "hospital psiquiátrico por dos años, en un proceso en el que "
                  "lo declararon inimputable. Los dos años se cumplieron en "
                  "julio y la clínica dice que no lo puede dar de alta hasta "
                  "que el juzgado mande un oficio. Ya van cuatro meses.",
        "accionado": "Juzgado de ejecución de penas y clínica psiquiátrica",
        "razon": "cumplido el término de la medida de seguridad fijado por el "
                 "juez, la permanencia en internamiento constituye prolongación "
                 "ilícita de la privación de la libertad",
        "pretension": "interponer habeas corpus para que se ordene el egreso "
                      "inmediato por cumplimiento del término de la medida",
    },
    {
        "id": "E37", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "hc_domiciliaria_no_ejecutada",
        "relato": "El juez le concedió a mi mamá la detención domiciliaria por "
                  "ser madre cabeza de familia, y tenemos la decisión "
                  "notificada desde hace tres semanas. El establecimiento no la "
                  "traslada y dice que está esperando la cartilla biográfica. "
                  "Ella sigue allá adentro.",
        "accionado": "INPEC y establecimiento de reclusión",
        "razon": "existiendo decisión judicial que sustituye la privación "
                 "intramural, su no ejecución prolonga ilícitamente la "
                 "detención en el establecimiento",
        "pretension": "interponer habeas corpus para que se materialice de "
                      "inmediato la detención domiciliaria concedida",
    },
    {
        "id": "E38", "tipo": "gold", "dificultad": "frontera",
        "categoria": "hc_retencion_por_multa",
        "relato": "Mi primo cumplió los catorce meses de la condena el 28 del "
                  "mes pasado. No lo sueltan porque dicen que debe la multa que "
                  "le pusieron en la sentencia y que hasta que no pague no sale.",
        "accionado": "Establecimiento de reclusión y juzgado de ejecución de penas",
        "razon": "la multa es una pena pecuniaria que no se convierte en "
                 "privación de la libertad, de modo que retener al condenado por "
                 "su impago prolonga ilícitamente la detención",
        "pretension": "interponer habeas corpus para que se ordene la libertad "
                      "por cumplimiento de la pena privativa",
    },
    {
        "id": "A13", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "hc_menor_en_establecimiento_adultos",
        "trampa": "El relato describe condiciones indignas de reclusión, lo que "
                  "empuja a responder 'tutela' por dignidad humana. Pero el "
                  "hecho determinante es que hay un adolescente privado de la "
                  "libertad al margen del sistema que le corresponde: el "
                  "supuesto es de libertad personal y el art. 6.2 excluye la "
                  "tutela.",
        "relato": "Mi hijo tiene 17 años y lo tienen en el patio de adultos de "
                  "la cárcel del municipio desde hace nueve días, por un proceso "
                  "que debería ir al sistema de responsabilidad penal para "
                  "adolescentes. Allá adentro duerme en el piso y lo han "
                  "amenazado.",
        "accionado": "Establecimiento de reclusión y Fiscalía",
        "razon": "la reclusión de un adolescente en establecimiento para "
                 "adultos, al margen del sistema de responsabilidad penal para "
                 "adolescentes, es una privación irregular de la libertad cuyo "
                 "mecanismo propio es el habeas corpus",
        "pretension": "interponer habeas corpus para que se ordene la libertad "
                      "o el traslado inmediato al sistema que corresponde",
    },
    {
        "id": "A14", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "hc_internamiento_involuntario_particular",
        "trampa": "El accionado es un particular y el relato habla de una "
                  "clínica de reposo, lo que empuja a responder 'tutela' por "
                  "salud o 'vía ordinaria' por ser un asunto de familia. Pero "
                  "hay una persona retenida contra su voluntad sin orden "
                  "judicial, y el habeas corpus procede también frente a "
                  "particulares.",
        "relato": "Mi hermana mayor internó a mi mamá en una clínica de reposo y "
                  "no la deja salir ni recibir visitas. Mi mamá está lúcida, nos "
                  "llamó a escondidas pidiendo que la saquemos, y no hay ninguna "
                  "interdicción ni orden de un juez. Llevamos tres semanas así.",
        "accionado": "Clínica de reposo y familiar",
        "razon": "hay una persona retenida contra su voluntad sin orden de "
                 "autoridad judicial competente, y el habeas corpus procede "
                 "también frente a la privación de la libertad ejercida por "
                 "particulares",
        "pretension": "interponer habeas corpus para que se verifique la "
                      "voluntad de la paciente y se ordene su egreso",
    },
]
for c in HABEAS_CORPUS:
    c.update(derecho="libertad_personal", mecanismo="habeas_corpus",
             procede=False, fundamento=FUND_HC,
             hechos={"privacion_libertad": True, "afectacion_individual": True})

# --------------------------------------------------------------------------
# +6 accion de cumplimiento (hoy 2: E29 y E30).
# La clave de todos: NO hay afectacion individual concreta. Con ella, el
# art. 9 de la Ley 393 reencauza a tutela, que es lo que pasa en A09.
# --------------------------------------------------------------------------
CUMPLIMIENTO = [
    {
        "id": "E39", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "ac_comisaria_de_familia",
        "relato": "La ley dice que todo municipio debe tener comisaría de "
                  "familia. El mío no tiene y a la gente le toca irse hasta la "
                  "cabecera, a dos horas. No es que a mí me hayan negado un "
                  "trámite puntual: la comisaría simplemente no existe.",
        "accionado": "Alcaldía municipal",
        "pretension": "ordenar al municipio crear y poner en funcionamiento la "
                      "comisaría de familia",
    },
    {
        "id": "E40", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "ac_plan_gestion_riesgo",
        "relato": "Hay una ley que obliga a cada municipio a adoptar su plan de "
                  "gestión del riesgo de desastres y a tener el consejo "
                  "municipal funcionando. En el mío nunca se adoptó el plan y el "
                  "consejo no se reúne desde 2019.",
        "accionado": "Alcaldía municipal",
        "pretension": "ordenar la adopción del plan municipal de gestión del "
                      "riesgo y la instalación del consejo",
    },
    {
        "id": "E41", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "ac_cuerpo_de_bomberos",
        "relato": "La ley dice que la prestación del servicio de bomberos es "
                  "obligación de los municipios, sea con cuerpo propio o por "
                  "convenio. Mi municipio no tiene ni lo uno ni lo otro: cuando "
                  "hay un incendio hay que llamar al municipio vecino.",
        "accionado": "Alcaldía municipal",
        "pretension": "ordenar al municipio garantizar el servicio de bomberos "
                      "mediante cuerpo propio o convenio",
    },
    {
        "id": "E42", "tipo": "gold", "dificultad": "frontera",
        "categoria": "ac_acuerdo_sin_reglamentar",
        "relato": "El concejo aprobó hace dos años un acuerdo que creó el "
                  "programa de apoyo a la primera infancia y le dio a la "
                  "alcaldía seis meses para reglamentarlo por decreto. El "
                  "decreto nunca salió y el programa no arrancó.",
        "accionado": "Alcaldía municipal",
        "razon": "lo pretendido es el cumplimiento de un deber de reglamentación "
                 "impuesto por un acto administrativo vigente, sin que se alegue "
                 "la vulneración concreta de un derecho fundamental individual",
        "pretension": "ordenar a la alcaldía expedir el decreto reglamentario "
                      "del acuerdo municipal",
    },
    {
        "id": "A15", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "ac_tarifa_adulto_mayor",
        "trampa": "El relato menciona adultos mayores, sujetos de especial "
                  "protección constitucional, lo que empuja a responder "
                  "'tutela'. Pero quien solicita dice expresamente que no es el "
                  "afectado: sin afectación individual concreta no opera la "
                  "regla del art. 9 de la Ley 393 que reencauza a tutela.",
        "relato": "Una ordenanza del departamento ordena que el transporte "
                  "intermunicipal dé tarifa preferencial a los adultos mayores. "
                  "Ninguna empresa la aplica y la secretaría de transporte no ha "
                  "hecho nada. Yo todavía no tengo la edad, lo pedimos por "
                  "escrito desde la veeduría del municipio.",
        "accionado": "Secretaría de transporte departamental",
        "razon": "quien solicita no alega la afectación concreta de su propio "
                 "derecho sino el acatamiento general de una norma vigente, de "
                 "modo que no opera la regla del artículo 9 de la Ley 393 que "
                 "reencauza el asunto a tutela",
        "pretension": "ordenar a la autoridad hacer cumplir la tarifa "
                      "preferencial fijada en la ordenanza",
    },
    {
        "id": "A16", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "ac_norma_salud_sin_afectado",
        "trampa": "ESPEJO EXACTO de A09. Misma estructura de superficie (una "
                  "norma de salud incumplida de forma general) pero SIN afectado "
                  "concreto: el solicitante dice que a él no le afecta. A09 va a "
                  "tutela por el art. 9 de la Ley 393 porque hay una persona a "
                  "la que la omisión le impide el acceso; este va a cumplimiento. "
                  "El par mide si el sistema aplica la regla o una heurística de "
                  "superficie del tipo 'ley de salud incumplida => tutela'.",
        "relato": "Salió una resolución que obliga a los hospitales públicos a "
                  "tener una sala de lactancia. En mi departamento ninguno la "
                  "tiene. Yo soy enfermero jubilado y lo vengo pidiendo desde la "
                  "asociación de usuarios, pero a mí personalmente no me afecta.",
        "accionado": "Secretaría de Salud departamental y hospitales públicos",
        "razon": "hay una norma incumplida de forma general y el solicitante no "
                 "alega la afectación concreta de un derecho fundamental propio, "
                 "de modo que el mecanismo idóneo es la acción de cumplimiento y "
                 "no la tutela",
        "pretension": "ordenar a los hospitales públicos habilitar la sala de "
                      "lactancia que exige la resolución",
    },
]
for c in CUMPLIMIENTO:
    c.update(derecho="ninguno", mecanismo="accion_cumplimiento", procede=False,
             fundamento=FUND_AC, hechos={"incumplimiento_normativo": True})
    c.setdefault("razon", RAZON_AC)

# --------------------------------------------------------------------------
# +5 accion popular (hoy 3: E09, E27, E28).
# A17 es el unico caso de todo el eval set que ejercita
# `titular_pide_lo_suyo`: la excepcion del art. 6.3 exige ADEMAS perjuicio
# irremediable, y sin el la competencia sigue siendo de la accion popular.
# --------------------------------------------------------------------------
POPULAR = [
    {
        "id": "E43", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "ap_humedal_rellenado",
        "relato": "Están metiendo volquetadas de tierra al humedal que queda al "
                  "borde del barrio para urbanizarlo. Ese humedal es área "
                  "protegida, ahí anidan los patos y es lo que absorbe el agua "
                  "cuando llueve fuerte. La autoridad ambiental dice que ya "
                  "mandó un requerimiento y ahí quedó.",
        "accionado": "Constructor y autoridad ambiental regional",
        "pretension": "interponer acción popular para que se suspenda el relleno "
                      "y se ordene la restauración del humedal",
        "hechos": {"derecho_colectivo": True},
    },
    {
        "id": "E44", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "ap_vertimiento_zona_banio",
        "relato": "El emisario del alcantarillado descarga a doscientos metros "
                  "de la playa donde se baña todo el mundo, incluidos los niños. "
                  "El agua sale con espuma y ya hubo dos casos de infección en "
                  "el puesto de salud. La empresa dice que la planta de "
                  "tratamiento está en diseño.",
        "accionado": "Empresa de servicios públicos y alcaldía",
        "pretension": "interponer acción popular para que cesen los "
                      "vertimientos y se construya el tratamiento",
        "hechos": {"derecho_colectivo": True},
    },
    {
        "id": "E45", "tipo": "gold", "dificultad": "frontera",
        "categoria": "ap_predio_publico_cedido",
        "relato": "El municipio le entregó a una fundación privada, por cuarenta "
                  "años y sin ningún proceso, el lote donde estaba la cancha del "
                  "barrio. Ya la cerraron con reja y cobran por entrar. Ese lote "
                  "es un bien de uso público.",
        "accionado": "Alcaldía municipal y fundación",
        "razon": "la defensa del patrimonio público y del espacio público son "
                 "derechos colectivos del artículo 4 de la Ley 472, excluidos "
                 "del ámbito de la tutela",
        "pretension": "interponer acción popular para que se restituya el bien "
                      "de uso público y se deje sin efecto la entrega",
        "hechos": {"derecho_colectivo": True},
    },
    {
        "id": "A17", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "ap_colectivo_con_afectado_sin_perjuicio",
        "trampa": "El relato identifica una afectación propia y concreta (la "
                  "pared humedecida de su casa), lo que empuja a responder "
                  "'tutela' por la excepción del art. 6.3. Pero esa excepción "
                  "exige DOS cosas: que el titular reclame lo suyo Y un "
                  "perjuicio irremediable. Aquí falta el segundo, así que el "
                  "asunto sigue siendo colectivo. Es el único caso del eval set "
                  "que ejercita `titular_pide_lo_suyo`.",
        "relato": "La tubería madre del acueducto está rota debajo de la calle y "
                  "lleva ocho meses botando agua. Toda la cuadra está sin "
                  "presión y a mí además se me humedeció la pared de la sala y "
                  "se me está cayendo el estuco. La empresa dice que está en el "
                  "plan de obras del año entrante.",
        "accionado": "Empresa de acueducto",
        "razon": "la afectación principal recae sobre el acceso a los servicios "
                 "públicos y el espacio público, que son derechos colectivos; la "
                 "excepción del artículo 6.3 exige que el titular reclame lo "
                 "suyo ante un perjuicio irremediable, que aquí no se acredita",
        "pretension": "interponer acción popular para que se repare la red y se "
                      "restablezca el servicio a la comunidad",
        # La excepcion del art. 6.3 exige titular + perjuicio irremediable.
        # El desglose deja ver POR QUE no hay perjuicio: el estuco que se cae
        # es inminente, pero no es un bien grave, no exige medidas inmediatas
        # y puede esperar. El test es conjuntivo.
        "hechos": {"derecho_colectivo": True, "titular_pide_lo_suyo": True,
                   "perjuicio_irremediable": False,
                   "pi_inminencia": True, "pi_gravedad": False,
                   "pi_urgencia": False, "pi_impostergabilidad": False},
    },
    {
        "id": "A18", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "ap_moralidad_sobrecosto",
        "trampa": "El relato da cifras de un contrato y menciona el perjuicio "
                  "al solicitante como usuario que pagará la tarifa, lo que "
                  "empuja a responder 'vía ordinaria' por tratarse de una "
                  "controversia contractual o tarifaria. Pero lo que se invoca "
                  "es la moralidad administrativa y el patrimonio público, que "
                  "tienen acción propia.",
        "relato": "La empresa de servicios del municipio compró los medidores a "
                  "cuatro veces el precio del mercado, está en la factura "
                  "publicada. Eso lo vamos a pagar todos en la tarifa. Lo "
                  "pusimos en conocimiento del concejo y nadie ha hecho nada.",
        "accionado": "Empresa de servicios públicos municipal",
        "razon": "la moralidad administrativa y la defensa del patrimonio "
                 "público son derechos colectivos expresamente protegidos por la "
                 "acción popular",
        "pretension": "interponer acción popular para que se investigue el "
                      "sobrecosto y se proteja el patrimonio público",
        "hechos": {"derecho_colectivo": True},
    },
]
for c in POPULAR:
    c.update(derecho="colectivos", mecanismo="accion_popular", procede=False,
             fundamento=FUND_AP)
    c.setdefault("razon", RAZON_AP)

# --------------------------------------------------------------------------
# +6 abstencion (ROADMAP #3). Hoy el eval principal no ejercita
# `no_determinable`: es el unico valor del vocabulario sin probar.
#
# Uno por cada una de las seis familias del dataset (AB01-AB18), con relatos
# nuevos. No pasan por el motor de reglas: la abstencion no es una conclusion
# del arbol del art. 6, es el reconocimiento de que no hay hechos para entrar.
# --------------------------------------------------------------------------
ABSTENCION = [
    {
        "id": "AB51", "dificultad": "rutinario",
        "categoria": "ab_consulta_comercial",
        "relato": "Tengo ahorrados veinte millones y estoy entre meterlos a un "
                  "CDT o comprar dólares. ¿Qué me rinde más este año?",
        "razon": "la consulta es sobre rentabilidad de alternativas de "
                 "inversión, no sobre la vulneración o amenaza de un derecho: no "
                 "hay materia para un triaje de acciones constitucionales",
        "pretension": "derivar la consulta a una fuente de información financiera",
    },
    {
        "id": "AB52", "dificultad": "rutinario",
        "categoria": "ab_pregunta_academica",
        "relato": "Estoy preparando el examen de judicatura y necesito que me "
                  "explique cuál es la diferencia entre el control de "
                  "constitucionalidad abstracto y el concreto, con ejemplos.",
        "razon": "es una pregunta conceptual con fines de estudio y no el relato "
                 "de una situación concreta que requiera determinar un mecanismo",
        "pretension": "responder como explicación académica, sin emitir un triaje",
    },
    {
        "id": "AB53", "dificultad": "frontera",
        "categoria": "ab_hechos_insuficientes",
        "relato": "Me pasó algo con una entidad del Estado y quiero poner una "
                  "acción. Todavía no tengo los papeles a mano y no me acuerdo "
                  "bien de las fechas, pero quiero ir adelantando.",
        "razon": "no se identifica la entidad, el derecho invocado, la actuación "
                 "reprochada ni las fechas: faltan los hechos mínimos para "
                 "determinar un mecanismo",
        "pretension": "solicitar los hechos faltantes antes de orientar",
    },
    {
        "id": "AB54", "dificultad": "frontera",
        "categoria": "ab_materia_no_cubierta",
        "relato": "Mi empresa importa repuestos y la DIAN nos abrió una "
                  "investigación por la clasificación arancelaria de unas "
                  "partidas. Queremos saber cómo se discute eso y qué términos "
                  "tenemos.",
        "razon": "es un asunto aduanero y tributario de una persona jurídica, "
                 "ajeno al dominio de las acciones constitucionales de este "
                 "sistema",
        "pretension": "derivar a asesoría especializada en materia aduanera",
    },
    {
        "id": "AB55", "dificultad": "trampa",
        "categoria": "ab_relato_contradictorio",
        "relato": "El fondo de pensiones nunca me ha resuelto la solicitud y por "
                  "eso quiero actuar. La resolución que me negó la pensión me "
                  "llegó en agosto y no la impugné.",
        "razon": "el relato se contradice: afirma que no hubo respuesta y acto "
                 "seguido que la negativa llegó en agosto; sin aclarar cuál de "
                 "las dos situaciones ocurrió no se puede determinar el mecanismo",
        "pretension": "pedir que se aclare la contradicción antes de orientar",
    },
    {
        "id": "AB56", "dificultad": "rutinario",
        "categoria": "ab_pide_pronostico",
        "relato": "Puse la tutela por la cirugía y el juez ya ordenó que me la "
                  "hagan. Lo que quiero saber es si la EPS va a cumplir o si se "
                  "va a hacer la loca, y qué tan probable es que me toque "
                  "incidente de desacato.",
        "razon": "lo que se pide es un pronóstico sobre la conducta futura de la "
                 "accionada y sobre el resultado de un trámite, no la "
                 "determinación del mecanismo procedente, que ya fue ejercido",
        "pretension": "explicar el trámite de desacato sin emitir un pronóstico",
    },
]
for c in ABSTENCION:
    c.update(tipo="abstencion", derecho="no_determinable", mecanismo=None,
             procede=False, fundamento="", accionado="no aplica",
             verificado_con_reglas=False)

NUEVOS = HABEAS_CORPUS + CUMPLIMIENTO + POPULAR + ABSTENCION

# --------------------------------------------------------------------------
# ROADMAP #5: dificultad de los 46 casos de v1.
#
#   rutinario  el mecanismo se sigue directamente de los hechos
#   frontera   hay que ponderar algo (eficacia del medio, perjuicio
#              irremediable, si la respuesta fue de fondo)
#   trampa     el caso esta construido para inducir el error
#
# Los 12 adversariales de v1 son trampa por construccion. El valor del campo
# esta en partir los 34 gold: permite ver si el modelo falla en los casos de
# frontera dentro de lo que hoy se reporta como un solo numero.
# --------------------------------------------------------------------------
DIFICULTAD_V1 = {
    "E01": "rutinario", "E02": "frontera",  "E03": "frontera",
    "E04": "frontera",  "E05": "rutinario", "E06": "frontera",
    "E07": "rutinario", "E08": "frontera",  "E09": "rutinario",
    "E10": "rutinario", "E11": "frontera",  "E12": "frontera",
    "E13": "rutinario", "E14": "rutinario", "E15": "frontera",
    "E16": "rutinario", "E17": "frontera",  "E18": "frontera",
    "E19": "rutinario", "E20": "rutinario", "E21": "rutinario",
    "E22": "rutinario", "E23": "frontera",  "E24": "rutinario",
    "E25": "rutinario", "E26": "frontera",  "E27": "rutinario",
    "E28": "rutinario", "E29": "rutinario", "E30": "rutinario",
    "E31": "rutinario", "E32": "rutinario", "E33": "rutinario",
    "E34": "rutinario",
    "A01": "trampa", "A02": "trampa", "A03": "trampa", "A04": "trampa",
    "A05": "trampa", "A06": "trampa", "A07": "trampa", "A08": "trampa",
    "A09": "trampa", "A10": "trampa", "A11": "trampa", "A12": "trampa",
}


def normalizar(t: str) -> str:
    """Para comparar relatos: sin acentos, sin puntuacion, sin may/min."""
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9ñ ]+", " ", t).strip()


def main() -> int:
    ruta_v1 = RAIZ / "data" / "eval_set.json"
    ruta_v2 = RAIZ / "data" / "eval_set_v2.json"

    v1 = json.loads(ruta_v1.read_text(encoding="utf-8"))
    casos_v1 = v1["ejemplos"]

    if not all(c.get("verificado_con_reglas") is not None for c in casos_v1):
        print("FALLA: corre primero data/codificar_hechos_eval.py (ROADMAP #1)")
        return 1

    # ---- ROADMAP #5: dificultad en v1 -----------------------------------
    faltan = {c["id"] for c in casos_v1} - DIFICULTAD_V1.keys()
    if faltan:
        print(f"FALLA: sin dificultad asignada: {sorted(faltan)}")
        return 1
    for c in casos_v1:
        c["dificultad"] = DIFICULTAD_V1[c["id"]]

    # ---- el motor tiene que derivar la etiqueta de cada caso nuevo -------
    errores: list[str] = []
    for c in NUEVOS:
        if c["tipo"] == "abstencion":
            continue
        try:
            dec = decidir(Hechos(**c["hechos"]))
        except (TypeError, ValueError) as ex:
            errores.append(f"{c['id']}: hechos invalidos -> {ex}")
            continue
        if dec.mecanismo != c["mecanismo"]:
            errores.append(f"{c['id']} ({c['categoria']}): etiqueta="
                           f"{c['mecanismo']} pero el motor deriva "
                           f"{dec.mecanismo} (regla: {dec.regla})")
            continue
        if dec.procede_tutela != c["procede"]:
            errores.append(f"{c['id']}: procede={c['procede']} pero el motor "
                           f"deriva {dec.procede_tutela}")
            continue
        c["verificado_con_reglas"] = True
        c["regla_que_cierra"] = dec.regla
        # Mismo calificador que los 46 de v1: si el mecanismo pivota en un
        # hecho de ponderacion, la verificacion por reglas vale menos ahi.
        est, campos = estrato_verificacion(Hechos(**c["hechos"]))
        c["estrato_verificacion"] = est
        c["etiqueta_pivota_en"] = campos

    # ---- ningun relato se puede repetir ---------------------------------
    ds = json.loads((RAIZ / "data" / "dataset.json").read_text(encoding="utf-8"))
    vistos: dict[str, str] = {}
    for c in ds["ejemplos"]:
        vistos[normalizar(c["relato"])] = f"dataset:{c['id']}"
    for c in casos_v1:
        vistos[normalizar(c["relato"])] = f"eval_v1:{c['id']}"
    for c in NUEVOS:
        k = normalizar(c["relato"])
        if k in vistos:
            errores.append(f"{c['id']}: relato repetido de {vistos[k]}")
        vistos[k] = f"nuevo:{c['id']}"

    ids_v1 = {c["id"] for c in casos_v1}
    for c in NUEVOS:
        if c["id"] in ids_v1:
            errores.append(f"{c['id']}: el id ya existe en v1")

    if errores:
        print(f"FALLA en {len(errores)} casos. No se escribio nada.\n")
        for e in errores:
            print(f"  - {e}")
        return 1

    # ---- v1: solo se le anota dificultad --------------------------------
    v1["meta"]["version"] = "1.2.0"
    cambios = v1["meta"].setdefault("cambios", [])
    nota_1 = ("1.2.0 (2026-10-16): se anaden los campos `hechos`, "
              "`verificado_con_reglas`, `regla_que_cierra` y `dificultad` a los "
              "46 casos. NINGUN relato, etiqueta ni razon cambia: `n` sigue "
              "siendo 46 y las once corridas anteriores siguen siendo "
              "comparables. Los `hechos` los verifica "
              "data/codificar_hechos_eval.py contra src/reglas.decidir(); "
              "`dificultad` la asigna data/construir_eval_v2.py. El tamano en "
              "bytes del archivo si cambia, y eso aparecera en "
              "corridas.version_datos().")
    if nota_1 not in cambios:
        cambios.append(nota_1)
    ruta_v1.write_text(json.dumps(v1, ensure_ascii=False, indent=1),
                       encoding="utf-8")

    # ---- v2: superconjunto ----------------------------------------------
    casos_v2 = [dict(c) for c in casos_v1] + NUEVOS
    for c in casos_v2:
        c["split"] = "eval"
    mec = Counter(c["mecanismo"] for c in casos_v2)
    n_juzgables = sum(1 for c in casos_v2 if c["mecanismo"] is not None)

    v2 = {
        "meta": {
            "nombre": "tutela-co-triage-eval-v2",
            "version": "2.0.0",
            "semilla": 42,
            "derivado_de": "data/eval_set.json v1.2.0",
            "relacion_con_v1":
                "SUPERCONJUNTO ESTRICTO. Los 46 casos de v1 estan incluidos sin "
                "ninguna modificacion: mismos ids, mismos relatos, mismas "
                "etiquetas. Cualquier diferencia entre las metricas de v1 y v2 "
                "es atribuible UNICAMENTE a los 23 casos agregados. v1 NO se "
                "retira: se sigue corriendo para no invalidar las once corridas "
                "previas, y las dos columnas se publican juntas.",
            "composicion": dict(Counter(c["tipo"] for c in casos_v2)),
            "balance_mecanismo": {k if k else "abstencion": v
                                  for k, v in mec.items()},
            "baseline_clase_mayoritaria": round(
                max(v for k, v in mec.items() if k) / n_juzgables, 4),
            "baseline_v1": 0.587,
            "por_dificultad": dict(Counter(c["dificultad"] for c in casos_v2)),
            "motivo": [
                "ROADMAP #2: en v1 el macro F1 promediaba cinco clases por "
                "igual con `accion_cumplimiento` en 2 casos y `habeas_corpus` "
                "en 2. Un solo caso movia el macro F1 global cerca de 10 "
                "puntos. Las tres clases minoritarias quedan en 8.",
                "ROADMAP #3: v1 no ejercitaba `no_determinable`, el unico valor "
                "del vocabulario sin probar en el eval principal. Se anaden 6 "
                "casos de abstencion, uno por cada familia del dataset.",
                "ROADMAP #5: `dificultad` permite leer los resultados por nivel "
                "y no solo por tipo. Parte los gold en `rutinario` y "
                "`frontera`, que hoy se reportan como un solo numero.",
            ],
            "disjunto_de":
                "data/dataset.json (train + validation) y entre si. El solape de "
                "RELATOS es cero, verificado por normalizacion (sin acentos, sin "
                "puntuacion, sin may/min) en data/construir_eval_v2.py. Las "
                "CATEGORIAS si reaparecen entre entrenamiento y evaluacion, y es "
                "deliberado: mide generalizacion dentro de las mismas familias "
                "juridicas, no en familias nuevas.",
            "verificacion":
                "los 63 casos juzgables tienen `hechos` codificados a mano y el "
                "mecanismo lo DERIVA src/reglas.decidir(); si no coincide con la "
                "etiqueta, este script falla y no escribe. Los 6 de abstencion "
                "no pasan por el motor: la abstencion no es una conclusion del "
                "arbol del art. 6 sino el reconocimiento de que no hay hechos "
                "para entrar.",
            "limites_conocidos": v1["meta"]["verificacion"]["limites_conocidos"],
        },
        "ejemplos": casos_v2,
    }
    ruta_v2.write_text(json.dumps(v2, ensure_ascii=False, indent=1),
                       encoding="utf-8")

    print(f"OK  v1: 46 casos, solo se anoto `dificultad` (version 1.2.0)")
    print(f"OK  v2: {len(casos_v2)} casos = 46 de v1 + {len(NUEVOS)} nuevos")
    print("\nmecanismo            v1    v2")
    mec_v1 = Counter(c["mecanismo"] for c in casos_v1)
    for k in ("tutela", "via_ordinaria", "accion_popular",
              "accion_cumplimiento", "habeas_corpus", None):
        etq = k if k else "abstencion"
        print(f"  {etq:20s} {mec_v1.get(k, 0):3d}   {mec[k]:3d}")
    print(f"\nbaseline mayoritaria  0.587 -> "
          f"{v2['meta']['baseline_clase_mayoritaria']}")
    print("\ndificultad:")
    for k, n in Counter(c["dificultad"] for c in casos_v2).most_common():
        print(f"  {k:12s} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
