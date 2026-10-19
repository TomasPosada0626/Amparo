"""
Un segundo caso en las categorias que el eval set SI evalua (ROADMAP #29).

POR QUE NO SE SUBE LA MEDIA A 2 Y SE HACE ESTO

El item pedia "subir de 1.13 a ~2 casos por categoria, priorizando las que
tambien estan en el eval set". Con 147 casos en 131 categorias, llevar la
MEDIA a 2 exige unos 130 casos nuevos, y la media uniforme no mide nada:
anadir un segundo caso a una categoria que el eval set nunca evalua no mejora
ninguna cifra ni ninguna generalizacion.

Lo que si importa son las categorias COMPARTIDAS. De las 21 que estan en el
eval v2 y en entrenamiento, **13 tenian un solo caso**: el modelo se evalua en
esas familias habiendo visto un unico ejemplo. Ahi un segundo caso cambia
algo, y son 13, no 130.

Se deja dicho para que la decision sea visible y revocable: si lo que se quiere
es la media, falta trabajo; si lo que se quiere es generalizacion medible,
esto es el item.

CADA PAR ES UN CONTRASTE, NO UNA REPETICION

Un segundo caso identico al primero no ensena nada. Cada uno cambia el
accionado, el sujeto o la circunstancia, manteniendo la categoria: la familia
juridica es la misma y los hechos no.

Verificados por el motor de reglas antes de escribir. Idempotente.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.reglas import Hechos, decidir, estrato_verificacion  # noqa: E402

PI = ("pi_inminencia", "pi_gravedad", "pi_urgencia", "pi_impostergabilidad")
ME = ("me_idoneo", "me_oportuno", "me_accesible")
VIA_LIMPIA = {**dict(zip(ME, (True, True, True))),
              **dict(zip(PI, (False, False, False, False)))}

CASOS = [
    {
        "id": "CT01", "categoria": "salud_no_pbs",
        "relato": "Mi hija tiene epilepsia refractaria y el neurólogo le "
                  "cambió a un anticonvulsivante que no está en el plan. La "
                  "EPS dice que hay otro equivalente, pero ya probamos tres y "
                  "con ninguno se le controlaron las crisis.",
        "derecho": "salud", "fundamento": "art. 49 CP; Ley 1751 de 2015",
        "accionado": "EPS", "mecanismo": "tutela", "procede": True,
        "razon": "el criterio del médico tratante sobre la idoneidad del "
                 "medicamento prevalece sobre la equivalencia administrativa "
                 "cuando las alternativas ya fallaron",
        "pretension": "autorizar y entregar el anticonvulsivante ordenado",
        "hechos": {"afectacion_individual": True,
                   "sujeto_especial_proteccion": True},
    },
    {
        "id": "CT02", "categoria": "salud_demora",
        "relato": "Tengo una catarata en los dos ojos y el oftalmólogo ordenó "
                  "la cirugía hace ocho meses. Ya casi no veo, vivo solo y me "
                  "he caído dos veces en la casa. En la EPS me dicen que la "
                  "agenda está cerrada.",
        "derecho": "salud", "fundamento": "art. 49 CP; Ley 1751 de 2015",
        "accionado": "EPS", "mecanismo": "tutela", "procede": True,
        "razon": "la dilación de un procedimiento ordenado agrava la condición "
                 "del paciente y desconoce el principio de oportunidad",
        "pretension": "programar y practicar la cirugía ordenada",
        "hechos": {"afectacion_individual": True,
                   "sujeto_especial_proteccion": True},
    },
    {
        "id": "CT03", "categoria": "salud_insumo",
        "relato": "A mi hijo le hicieron una traqueostomía y necesita las "
                  "cánulas y los filtros cada semana. La EPS entregó los "
                  "primeros dos meses y ahora dice que eso es un dispositivo y "
                  "que lo compremos en una tienda médica.",
        "derecho": "salud", "fundamento": "art. 49 CP; Ley 1751 de 2015",
        "accionado": "EPS", "mecanismo": "tutela", "procede": True,
        "razon": "el insumo es parte inseparable del tratamiento ordenado y "
                 "suspenderlo interrumpe un servicio ya iniciado",
        "pretension": "ordenar la entrega continua de las cánulas y filtros",
        "hechos": {"afectacion_individual": True,
                   "sujeto_especial_proteccion": True},
    },
    {
        "id": "CT04", "categoria": "habeas_data_sin_notificacion",
        "relato": "Me enteré de que estoy reportado cuando fui a arrendar un "
                  "apartamento y me pidieron el historial. Es por un plan de "
                  "celular que cancelé hace tres años y que la empresa dice "
                  "que quedó con saldo. Nunca me mandaron ninguna carta.",
        "derecho": "habeas_data",
        "fundamento": "art. 15 CP; Ley 1266 de 2008",
        "accionado": "Operador de telefonía y central de riesgo",
        "mecanismo": "tutela", "procede": True,
        "razon": "el reporte negativo exige comunicación previa al titular, y "
                 "su omisión vulnera el habeas data y el buen nombre",
        "pretension": "ordenar el retiro del reporte hasta que se cumpla el "
                      "deber de notificación previa",
        "hechos": {"afectacion_individual": True},
    },
    {
        "id": "CT05", "categoria": "debido_proceso_disciplinario",
        "relato": "Soy vigilante y la empresa me despidió por un faltante en "
                  "el inventario del turno mío. No me llamaron a ninguna "
                  "diligencia de descargos, no me mostraron el video, me "
                  "entregaron la carta y listo.",
        "derecho": "debido_proceso",
        "fundamento": "art. 29 CP; art. 25 CP",
        "accionado": "Empresa de vigilancia",
        "mecanismo": "tutela", "procede": True,
        "razon": "la sanción disciplinaria se adoptó sin diligencia de "
                 "descargos ni acceso a la prueba, desconociendo el debido "
                 "proceso que rige también en el ámbito privado",
        "pretension": "dejar sin efecto la sanción y adelantar el proceso "
                      "disciplinario con garantías",
        "hechos": {"afectacion_individual": True},
    },
    {
        "id": "CT06", "categoria": "educacion_cupo",
        "relato": "Mi nieto de siete años vive conmigo desde que su mamá se "
                  "fue. No lo aceptan en ningún colegio porque no tengo la "
                  "custodia formalizada y me piden el registro con los dos "
                  "papás. Lleva todo el año sin estudiar.",
        "derecho": "educacion",
        "fundamento": "art. 44 CP; art. 67 CP; Ley 1098 de 2006",
        "accionado": "Secretaría de Educación",
        "mecanismo": "tutela", "procede": True,
        "razon": "un requisito documental no previsto como condición de acceso "
                 "no puede excluir del sistema educativo a un menor, cuyos "
                 "derechos prevalecen",
        "pretension": "ordenar la asignación inmediata de cupo escolar",
        "hechos": {"afectacion_individual": True,
                   "sujeto_especial_proteccion": True},
    },
    {
        "id": "CT07", "categoria": "fuero_maternidad",
        "relato": "Trabajo en una cooperativa por horas y hace dos semanas "
                  "avisé que estoy embarazada. Desde entonces no me asignan "
                  "turnos: no me despidieron formalmente pero no me están "
                  "dando trabajo ni me pagan.",
        "derecho": "estabilidad_laboral_reforzada",
        "fundamento": "art. 43 CP; art. 53 CP",
        "accionado": "Cooperativa de trabajo",
        "mecanismo": "tutela", "procede": True,
        "razon": "dejar de asignar turnos tras el aviso del embarazo es un "
                 "despido material encubierto que activa la protección "
                 "reforzada a la maternidad",
        "pretension": "ordenar el restablecimiento de los turnos y el pago de "
                      "lo dejado de percibir",
        "hechos": {"afectacion_individual": True, "otro_medio_judicial": True,
                   "medio_eficaz": False, "sujeto_especial_proteccion": True,
                   **dict(zip(ME, (True, False, True)))},
    },
    {
        "id": "CT08", "categoria": "fuero_salud",
        "relato": "Me operaron de la columna y quedé con restricción para "
                  "cargar peso. El médico laboral recomendó reubicarme y la "
                  "empresa dijo que no tiene otro puesto y me liquidó esa misma "
                  "semana, sin pedir permiso a nadie.",
        "derecho": "estabilidad_laboral_reforzada",
        "fundamento": "art. 13 CP; art. 25 CP; Ley 361 de 1997",
        "accionado": "Empresa empleadora",
        "mecanismo": "tutela", "procede": True,
        "razon": "el despido de un trabajador con restricción médica conocida "
                 "requiere autorización previa de la autoridad de trabajo, y "
                 "sin ella carece de efecto jurídico",
        "pretension": "ordenar el reintegro con reubicación acorde a la "
                      "restricción médica",
        "hechos": {"afectacion_individual": True, "otro_medio_judicial": True,
                   "medio_eficaz": False, "sujeto_especial_proteccion": True,
                   **dict(zip(ME, (True, False, True)))},
    },
    {
        "id": "CT09", "categoria": "pension_perjuicio_irremediable",
        "relato": "Tengo 79 años y una insuficiencia cardíaca. Pedí la pensión "
                  "de sobrevivientes de mi esposa, que era la que cotizaba, y "
                  "el fondo lleva un año pidiéndome documentos que ya entregué. "
                  "No tengo ingresos ni quién me ayude.",
        "derecho": "seguridad_social",
        "fundamento": "art. 48 CP; art. 46 CP; art. 8 Decreto 2591 de 1991",
        "accionado": "Fondo de pensiones",
        "mecanismo": "tutela", "procede": True,
        "razon": "la edad avanzada, la enfermedad y la carencia total de "
                 "ingresos configuran un perjuicio irremediable que habilita "
                 "la tutela pese a existir la vía ordinaria",
        "pretension": "ordenar el reconocimiento y pago de la pensión de "
                      "sobrevivientes",
        "hechos": {"afectacion_individual": True, "otro_medio_judicial": True,
                   "perjuicio_irremediable": True,
                   "sujeto_especial_proteccion": True,
                   **dict(zip(PI, (True, True, True, True)))},
    },
    {
        "id": "CT10", "categoria": "libertad_personal",
        "relato": "A mi papá lo detuvieron en un retén porque el sistema "
                  "mostraba una orden a nombre suyo. Ya llevamos cuatro días y "
                  "en la fiscalía dicen que la orden es de un homónimo de otra "
                  "ciudad, pero no lo sueltan mientras verifican.",
        "derecho": "libertad_personal",
        "fundamento": "art. 28 CP; art. 30 CP; Ley 1095 de 2006; "
                      "art. 6.2 Decreto 2591 de 1991",
        "accionado": "Fiscalía y Policía Nacional",
        "mecanismo": "habeas_corpus", "procede": False,
        "razon": "la privación de la libertad se sostiene sobre una orden que "
                 "no corresponde al capturado, supuesto propio del habeas "
                 "corpus",
        "pretension": "interponer habeas corpus para que se verifique la "
                      "identidad y se ordene la libertad inmediata",
        "hechos": {"privacion_libertad": True, "afectacion_individual": True},
    },
    {
        "id": "CT11", "categoria": "incumplimiento_norma",
        "relato": "Una resolución nacional obliga a los municipios a tener "
                  "ruta de atención para violencia intrafamiliar y a "
                  "publicarla. En el mío no existe ni la ruta ni la "
                  "publicación. No es que a mí me hayan negado algo: es que no "
                  "está implementada.",
        "derecho": "ninguno", "fundamento": "art. 87 CP; Ley 393 de 1997",
        "accionado": "Alcaldía municipal",
        "mecanismo": "accion_cumplimiento", "procede": False,
        "razon": "se reclama el acatamiento de un deber impuesto por una norma "
                 "vigente, sin que se alegue la vulneración concreta de un "
                 "derecho fundamental individual",
        "pretension": "ordenar la implementación y publicación de la ruta de "
                      "atención",
        "hechos": {"incumplimiento_normativo": True},
    },
    {
        "id": "CT12", "categoria": "laboral_ordinario",
        "relato": "Trabajé dos años como mensajero y me liquidaron mal: no me "
                  "pagaron las horas extra que quedaron registradas en la "
                  "plataforma. Son como seis millones. Ya reclamé por escrito "
                  "y la empresa dice que esas horas no estaban autorizadas.",
        "derecho": "trabajo",
        "fundamento": "art. 6.1 Decreto 2591 de 1991",
        "accionado": "Empresa empleadora",
        "mecanismo": "via_ordinaria", "procede": False,
        "razon": "es un cobro de acreencias laborales con proceso propio ante "
                 "la jurisdicción laboral, y no se alega afectación actual del "
                 "mínimo vital",
        "pretension": "demandar el pago ante la jurisdicción laboral ordinaria",
        "hechos": {"otro_medio_judicial": True, **VIA_LIMPIA},
    },
    {
        "id": "CT13", "categoria": "contractual_ordinario",
        "relato": "Contraté una remodelación y pagué el 70% por adelantado. El "
                  "maestro dejó la obra a medias y no contesta. Tengo el "
                  "contrato firmado y los comprobantes de las "
                  "transferencias.",
        "derecho": "ninguno",
        "fundamento": "art. 6.1 Decreto 2591 de 1991",
        "accionado": "Contratista particular",
        "mecanismo": "via_ordinaria", "procede": False,
        "razon": "se trata del incumplimiento de un contrato entre "
                 "particulares, con acción propia ante la jurisdicción civil y "
                 "sin derecho fundamental comprometido",
        "pretension": "demandar el incumplimiento ante la jurisdicción civil",
        "hechos": {"otro_medio_judicial": True, **VIA_LIMPIA},
    },
]
for c in CASOS:
    c.update(tipo_fuente="redactado por el equipo", split="train",
             verificado_con_reglas=True)

GENERADO = re.compile(r"CT\d{2}$")



def subir_version(meta: dict, propia: str) -> None:
    """Sube `meta["version"]` solo si `propia` es mayor.

    Tres scripts escriben el dataset y cada uno fijaba su version a pelo, asi
    que la final dependia del ORDEN en que se corrieran: `casos_reales.py`
    ponia 2.2.0 y despues `codificar_hechos_dataset.py` la bajaba a 2.1.0. Con
    esto la version del artefacto es la misma corra lo que corra primero.
    """
    def t(v):
        return tuple(int(x) for x in str(v or "0").split("."))
    if t(propia) > t(meta.get("version")):
        meta["version"] = propia

def main() -> int:
    ruta = RAIZ / "data" / "dataset.json"
    d = json.loads(ruta.read_text(encoding="utf-8"))
    casos = [c for c in d["ejemplos"] if not GENERADO.fullmatch(c["id"])]

    from collections import Counter
    cat_antes = Counter(c["categoria"] for c in casos)
    ev = json.loads((RAIZ / "data" / "eval_set_v2.json").read_text(encoding="utf-8"))
    cat_eval = {e["categoria"] for e in ev["ejemplos"]}
    relatos = {c["relato"] for c in casos} | {e["relato"] for e in ev["ejemplos"]}

    errores = []
    for c in CASOS:
        if c["relato"] in relatos:
            errores.append(f"{c['id']}: relato repetido")
        if c["categoria"] not in cat_eval:
            errores.append(f"{c['id']}: la categoria `{c['categoria']}` no esta "
                           f"en el eval set, asi que el caso no mejora ninguna "
                           f"medicion")
        try:
            dec = decidir(Hechos(**c["hechos"]))
        except (TypeError, ValueError) as ex:
            errores.append(f"{c['id']}: hechos invalidos -> {ex}")
            continue
        if dec.mecanismo != c["mecanismo"] or dec.procede_tutela != c["procede"]:
            errores.append(f"{c['id']}: etiqueta={c['mecanismo']}/{c['procede']} "
                           f"pero el motor deriva {dec.mecanismo}/"
                           f"{dec.procede_tutela}")
            continue
        c["regla_que_cierra"] = dec.regla
        est, campos = estrato_verificacion(Hechos(**c["hechos"]))
        c["estrato_verificacion"] = est
        c["etiqueta_pivota_en"] = campos
        c["hechos"] = {k: c["hechos"][k] for k in sorted(c["hechos"])}

    if errores:
        print(f"FALLA en {len(errores)} casos. No se escribio nada.")
        for e in errores:
            print(f"  - {e}")
        return 1

    casos += CASOS
    cat_despues = Counter(c["categoria"] for c in casos)
    compartidas = set(cat_despues) & cat_eval
    singles = [k for k in compartidas if cat_despues[k] == 1]

    d["ejemplos"] = casos
    subir_version(d["meta"], "3.5.0")
    d["meta"]["cobertura_por_categoria"] = {
        "casos": len(casos),
        "categorias": len(cat_despues),
        "media": round(len(casos) / len(cat_despues), 3),
        "compartidas_con_el_eval": len(compartidas),
        "compartidas_con_un_solo_caso": len(singles),
        "ids_compartidas_con_un_solo_caso": sorted(singles),
        "por_que_no_se_subio_la_media":
            "El item pedia llevar la media de 1.13 a ~2, lo que exige unos 130 "
            "casos nuevos. La media uniforme no mide nada: un segundo caso en "
            "una categoria que el eval set nunca evalua no mejora ninguna cifra "
            "ni ninguna generalizacion. Se priorizaron las CATEGORIAS "
            "COMPARTIDAS con el eval set que tenian un solo ejemplo de "
            "entrenamiento, que eran 13 --- ahi el modelo se evalua en una "
            "familia habiendo visto un unico caso. Queda dicho para que la "
            "decision sea visible y revocable: si lo que se quiere es la media, "
            "falta trabajo.",
        "cada_par_es_un_contraste":
            "Un segundo caso identico al primero no ensena nada. Cada uno "
            "cambia el accionado, el sujeto o la circunstancia manteniendo la "
            "categoria: la familia juridica es la misma y los hechos no.",
    }
    ruta.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                    encoding="utf-8")

    print(f"OK: dataset v3.5.0 con {len(casos)} casos")
    print(f"  categorias compartidas con el eval : {len(compartidas)}")
    print(f"  de esas, con UN solo caso          : "
          f"{len(singles)}  (antes 13)")
    if singles:
        print(f"    quedan: {sorted(singles)}")
    print(f"\n  media global: {len(casos) / len(cat_despues):.3f} "
          f"(no es el objetivo, ver el meta)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
