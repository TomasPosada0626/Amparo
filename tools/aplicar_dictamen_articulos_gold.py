"""Registra en el CSV de validacion el dictamen aprobado, por clase.

El instrumento (`tools/validacion_articulos_gold.py`) tiene 217 filas en cuatro
clases de impacto. Se adjudican por clase, y este script escribe solo la que se
le pida: asi la aprobacion de una no arrastra a las demas.

La clase A -- las 27 etiquetas que sostienen un acierto -- la aprobo Leonardo
Galeano el 2026-10-10, con dos comprobaciones que pidio expresamente y que
estan hechas (ver `docs/m3_articulos_gold_dictamen_claseA.md`):

  Ley 769 arts. 144 y 149   No son duplicado. 56 % de similitud literal y
                            ambitos distintos: el 144 aplica cuando no hay
                            conciliacion tras daños materiales (viene del
                            143), y el 149 remite al "articulo anterior", que
                            es el 148, Funciones de Policia Judicial, para
                            hechos que puedan constituir infraccion penal.
                            Por eso el 149 pasa de responde_parcial a
                            no_responde en el caso 9054, que es un choque sin
                            lesiones.
  CGP arts. 291 y 292       No son intercambiables. El 291 regula la practica
                            de la notificacion personal e incluye el regimen
                            de la direccion electronica ("las personas
                            naturales que hayan suministrado al juez su
                            direccion de correo electronico"), que es la
                            consulta del caso 9069. El 292 es el aviso por
                            servicio postal autorizado cuando la personal no
                            se pudo hacer. Se confirma no_responde.

Por defecto SIMULA. Escribir exige --escribir.

    python -m tools.aplicar_dictamen_articulos_gold --clase A
    python -m tools.aplicar_dictamen_articulos_gold --clase A --escribir
"""
from __future__ import annotations

import argparse
import csv

from tools.validacion_articulos_gold import (
    COLUMNAS,
    HASH_METADATA,
    SALIDA,
    revisar,
)

# (case_id, doc_id, articulo) -> (veredicto, confianza, justificacion)
CLASE_A = {
    ("9001", "arrendamiento_vivienda_urbana_ley_820_2003", "20"): (
        "responde", "alta",
        "Fija el reajuste del canon con tope del 100 % del IPC del año anterior: "
        "responde directamente si el arrendador puede duplicarlo."),
    ("9002", "codigo_sustantivo_trabajo_decreto_2663_1950", "62"): (
        "responde_parcial", "media",
        "El literal B) da las justas causas del trabajador, base de la renuncia "
        "motivada. Pero la reclamacion economica se resuelve con el articulo 64, "
        "que no esta etiquetado."),
    ("9005", "estatuto_consumidor_ley_1480_2011", "8"): (
        "responde", "alta",
        "El termino de garantia es de un año para productos nuevos: resuelve el "
        "caso de un celular de ocho meses."),
    ("9005", "estatuto_consumidor_ley_1480_2011", "11"): (
        "responde", "alta",
        "Enumera lo que cubre la garantia legal: reparacion gratuita, reposicion "
        "o devolucion del dinero."),
    ("9005", "estatuto_consumidor_ley_1480_2011", "58"): (
        "responde_parcial", "media",
        "Es la via procesal ante la SIC, no si la garantia cubre el defecto."),
    ("9031", "seguridad_social_ley_100_1993", "168"): (
        "responde", "alta",
        "La atencion inicial de urgencias es obligatoria 'independientemente de la "
        "capacidad de pago' y 'no requiere contrato ni orden previa'. Exacto."),
    ("9032", "estatutaria_salud_ley_1751_2015", "10"): (
        "responde_parcial", "media",
        "Reconoce el derecho de acceso integral, pero lo que decide si un "
        "tratamiento esta excluido es el articulo 15, que no esta etiquetado."),
    ("9034", "arrendamiento_vivienda_urbana_ley_820_2003", "22"): (
        "responde", "alta",
        "Lista las causales de terminacion por el arrendador, y querer el "
        "inmueble no esta entre ellas: responde por exclusion."),
    ("9036", "codigo_sustantivo_trabajo_decreto_2663_1950", "168"): (
        "responde_parcial", "media",
        "Da los recargos de hora extra (25 % diurna, 75 % nocturna), o sea cuanto "
        "se debe. No cubre el 'que puedo hacer'."),
    ("9037", "acoso_laboral_ley_1010_2006", "2"): (
        "responde", "alta",
        "Definicion de acoso laboral: conducta persistente y demostrable dirigida "
        "a causar perjuicio o desmotivacion. Es la pregunta literal."),
    ("9037", "acoso_laboral_ley_1010_2006", "7"): (
        "responde", "alta",
        "Presume acoso ante la ocurrencia repetida y publica de expresiones "
        "injuriosas o ultrajantes, que es el hecho descrito."),
    ("9040", "codigo_nacional_transito_ley_769_2002", "42"): (
        "no_responde", "media",
        "Establece que el SOAT es obligatorio y remite a 'las normas actualmente "
        "vigentes' para su contenido. No define que cubre, que es lo que se "
        "pregunta. ACIERTO FALSO: era el unico punto de acierto del caso."),
    ("9044", "codigo_infancia_adolescencia_ley_1098_2006", "111"): (
        "responde_parcial", "media",
        "Reglas de fijacion de la cuota y citacion a conciliacion. El aumento por "
        "cambio de circunstancias es una revision posterior."),
    ("9044", "codigo_infancia_adolescencia_ley_1098_2006", "129"): (
        "responde_parcial", "media",
        "Cuota provisional en el auto de traslado: pieza del procedimiento, no la "
        "respuesta a si se puede aumentar."),
    ("9045", "constitucion_politica_1991", "86"): (
        "responde_parcial", "alta",
        "Funda la tutela, pero el texto destaca 'cualquier autoridad publica' y el "
        "inciso que la abre a particulares va al final. Por si solo no resuelve si "
        "procede contra un banco privado."),
    ("9045", "tutela_decreto_2591_1991", "42"): (
        "responde", "alta",
        "'Procedencia: la accion de tutela procedera contra acciones u omisiones de "
        "particulares en los siguientes casos'. Es exactamente la consulta."),
    ("9051", "codigo_sustantivo_trabajo_decreto_2663_1950", "161"): (
        "no_responde", "media",
        "Regula la duracion maxima de la jornada (42 horas semanales). La consulta "
        "es el cambio unilateral de turno y los limites del ius variandi con un "
        "hijo de dos años. ACIERTO FALSO: era el unico punto de acierto."),
    ("9052", "habeas_data_financiero_ley_1266_2008", "13"): (
        "responde", "alta",
        "Permanencia de la informacion y termino maximo del dato negativo: es el "
        "nucleo de una deuda pagada que se reporta de nuevo."),
    ("9053", "habeas_data_financiero_ley_1266_2008", "16"): (
        "responde_parcial", "media",
        "Da el tramite de peticiones, consultas y reclamos, o sea el camino. No "
        "resuelve a quien se atribuye la deuda."),
    ("9054", "codigo_nacional_transito_ley_769_2002", "144"): (
        "responde_parcial", "media",
        "Informe policial cuando no fue posible la conciliacion tras daños "
        "materiales. Aplica al caso, pero el que resuelve es el 143: en daños "
        "materiales el material probatorio de las partes reemplaza el informe."),
    ("9054", "codigo_nacional_transito_ley_769_2002", "149"): (
        "no_responde", "media",
        "Comprobado a peticion del abogado: NO es duplicado del 144. Remite al "
        "'articulo anterior', que es el 148 (Funciones de Policia Judicial), para "
        "hechos que puedan constituir infraccion penal. El caso es un choque sin "
        "lesiones, asi que ese supuesto no aplica. Corrige el responde_parcial que "
        "propuso el borrador."),
    ("9059", "estatuto_consumidor_ley_1480_2011", "43"): (
        "responde", "alta",
        "Clausulas abusivas ineficaces de pleno derecho: encaja con una penalidad "
        "que no estaba en lo que se mostro."),
    ("9061", "codigo_policia_convivencia_ley_1801_2016", "33"): (
        "responde", "alta",
        "Prohibe perturbar el sosiego con ruidos en el vecindario, y el permiso "
        "ambiental no excusa ese comportamiento."),
    ("9064", "cpaca_ley_1437_2011", "21"): (
        "no_responde", "media",
        "Es 'funcionario sin competencia': que hacer cuando la peticion se dirige a "
        "quien no es competente. La consulta es una respuesta incongruente de la "
        "autoridad competente, supuesto distinto. ACIERTO FALSO: era el unico punto "
        "de acierto del caso."),
    ("9065", "propiedad_industrial_decision_486_2000", "136"): (
        "responde", "alta",
        "Irregistrabilidad de signos semejantes con riesgo de confusion: responde "
        "el registro de un nombre casi igual."),
    ("9067", "codigo_comercio_decreto_410_1971", "1318"): (
        "responde", "alta",
        "'El empresario no podra servirse de varios agentes en una misma zona y "
        "para el mismo ramo'. Exacto."),
    ("9069", "codigo_general_proceso_ley_1564_2012", "292"): (
        "no_responde", "media",
        "Comprobado a peticion del abogado: no es intercambiable con el 291. El 292 "
        "es el aviso por servicio postal autorizado cuando la notificacion personal "
        "no se pudo hacer. El regimen del correo electronico esta en el 291, que "
        "exige que la persona natural 'haya suministrado al juez' su direccion, que "
        "es justo lo que se discute. ACIERTO FALSO: era el unico punto de acierto."),
}


# Clase B' -- los 62 candidatos a omision. Copia del documento
# docs/m3_articulos_gold_dictamen_claseB.md, que los lista por caso.
# Formato compacto: (caso, doc, articulo) -> (veredicto, confianza).
# La justificacion comun de cada grupo esta en _JUST_B.
_L1751 = "estatutaria_salud_ley_1751_2015"
_D2591 = "tutela_decreto_2591_1991"
_CC = "codigo_civil_ley_84_1873"
_CCO = "codigo_comercio_decreto_410_1971"
_CPACA = "cpaca_ley_1437_2011"
_L1712 = "ley_transparencia_acceso_info_ley_1712_2014"
_CGP = "codigo_general_proceso_ley_1564_2012"
_L820 = "arrendamiento_vivienda_urbana_ley_820_2003"
_CST = "codigo_sustantivo_trabajo_decreto_2663_1950"
_L1266 = "habeas_data_financiero_ley_1266_2008"
_L1480 = "estatuto_consumidor_ley_1480_2011"
_L1620 = "convivencia_escolar_ley_1620_2013"
_L115 = "ley_general_educacion_ley_115_1994"
_L80 = "contratacion_estatal_ley_80_1993"
_L100 = "seguridad_social_ley_100_1993"
_L1801 = "codigo_policia_convivencia_ley_1801_2016"

_JUST_B = {
    "responde": "El sistema lo trajo y responde la consulta: es una omision del gold, y el fallo del caso era falso.",
    "responde_parcial": "Aporta una pieza real de la respuesta pero no la resuelve; no basta para dar el caso por acertado.",
    "no_responde": "El sistema lo trajo pero es de otra materia o no toca la pregunta: el fallo del caso es correcto.",
}

CLASE_B_PRIMA_COMPACTA = {
    # las tres omisiones reales
    ("9004", _L1751, "10"): ("responde", "alta"),
    ("9009", _L1712, "21"): ("responde", "alta"),
    ("9066", _L1801, "79"): ("responde", "alta"),
    # aportan una pieza, no resuelven
    ("9007", _CCO, "1163"): ("responde_parcial", "media"),
    ("9009", _L1712, "9"): ("responde_parcial", "media"),
    ("9038", _CST, "43"): ("responde_parcial", "media"),
    ("9039", _L1266, "16"): ("responde_parcial", "media"),
    ("9043", _L1480, "51"): ("responde_parcial", "media"),
    ("9043", _L1480, "50"): ("responde_parcial", "baja"),
    ("9043", _L1480, "58"): ("responde_parcial", "baja"),
    ("9050", _CCO, "714"): ("responde_parcial", "media"),
    ("9050", _CCO, "720"): ("responde_parcial", "media"),
    ("9050", _CCO, "721"): ("responde_parcial", "media"),
    ("9056", _CGP, "593"): ("responde_parcial", "media"),
    ("9057", _CGP, "593"): ("responde_parcial", "media"),
    ("9063", _L100, "33"): ("responde_parcial", "media"),
    ("9063", _L100, "35"): ("responde_parcial", "media"),
    ("9063", _L100, "117"): ("responde_parcial", "media"),
    ("9068", _CGP, "321"): ("responde_parcial", "media"),
    ("9068", _CGP, "352"): ("responde_parcial", "media"),
}

# Los 43 que no responden, por caso. Confianza alta salvo las anotadas.
_NO_RESPONDE_B = {
    ("9004", _D2591, "17"): "alta",
    ("9007", _CC, "2172"): "alta", ("9007", _CC, "2234"): "alta",
    ("9007", _CC, "2309"): "alta",
    ("9009", _CPACA, "141"): "alta", ("9009", _CPACA, "217"): "alta",
    ("9010", _CGP, "526"): "alta",
    ("9035", _L820, "8"): "media", ("9035", _L820, "15"): "alta",
    ("9035", _L820, "22"): "alta", ("9035", _L820, "23"): "alta",
    ("9035", _L820, "25"): "alta",
    ("9038", _CST, "48"): "alta", ("9038", _CST, "140"): "alta",
    ("9039", _L1266, "14"): "media", ("9039", _L1266, "19-A"): "media",
    ("9041", _CST, "65"): "alta", ("9041", _CST, "290"): "alta",
    ("9041", _CST, "393"): "alta", ("9041", _CST, "433"): "alta",
    ("9043", _L1480, "18"): "alta",
    ("9046", _CPACA, "16"): "media", ("9046", _CPACA, "21"): "alta",
    ("9046", _CPACA, "225"): "alta",
    ("9050", _CCO, "724"): "alta", ("9050", _CCO, "728"): "alta",
    ("9056", _CGP, "468"): "alta", ("9056", _CGP, "598"): "alta",
    ("9056", _CGP, "599"): "media",
    ("9057", _CGP, "468"): "alta", ("9057", _CGP, "470"): "media",
    ("9058", _L1620, "2"): "media", ("9058", _L115, "82"): "alta",
    ("9058", _L115, "134"): "alta", ("9058", _L115, "149"): "alta",
    ("9058", _L115, "172"): "alta",
    ("9060", _L80, "4"): "media", ("9060", _L80, "25"): "alta",
    ("9060", _L80, "32"): "alta",
    ("9063", _L100, "14"): "media", ("9063", _L100, "27"): "alta",
    ("9068", _CGP, "159"): "alta",
}

CLASE_B_PRIMA = {
    **{k: (v[0], v[1], _JUST_B[v[0]]) for k, v in CLASE_B_PRIMA_COMPACTA.items()},
    **{k: ("no_responde", c, _JUST_B["no_responde"]) for k, c in _NO_RESPONDE_B.items()},
}


# Clases B y C: SOLO las tres filas que el dictamen nombro individualmente.
# Las otras 125 no se registran porque su dictamen fue agregado (64/15/3 en B,
# 38/8/0 en C) y no hay constancia de que veredicto corresponde a cada fila.
# El instrumento docs/m3_articulos_gold_pendientes_BC.md esta generado con la
# casilla vacia para esas 125; mientras no vuelva con los veredictos, asignarlos
# seria deducirlos de la distribucion, o sea inventarlos.
from tools.pendientes_bc import NOMBRADAS as _NOMBRADAS

# Las tres son de clase B. La clase C no tiene ninguna fila con veredicto
# individual, coherente con su agregado 38/8/0, que no nombro excepciones: la
# comprobacion de completitud del verificador lo destapo cuando intente
# registrar la de 9004 como clase C.
CLASE_B_NOMBRADAS = dict(_NOMBRADAS)

DICTAMENES = {"A": ("A_sostiene_acierto", CLASE_A),
              "B_prima": ("B_candidato_omision", CLASE_B_PRIMA),
              "B_parcial": ("B_caso_fallido", CLASE_B_NOMBRADAS)}

# Las clases que se registran de forma PARCIAL: el verificador no exige que el
# dictamen cubra la clase entera, pero si informa cuantas quedan pendientes.
PARCIALES = {"B_parcial"}

FIRMAS = {
    "A": ("primera pasada por Claude sobre el texto de la metadata del indice "
          "evaluado. Clase A aprobada el 2026-10-10 por Leonardo Galeano (abogado), "
          "con la comprobacion expresa de Ley 769 arts. 144/149 y CGP arts. 291/292. "
          "La aprobacion cubre solo la clase A"),
    "B_prima": ("primera pasada por Claude sobre el texto de la metadata del indice "
                "evaluado. Clase B' (candidatos a omision) aprobada el 2026-10-10 por "
                "Leonardo Galeano (abogado) como dictamen completo, incluidas las tres "
                "omisiones (9004 art. 10, 9009 art. 21, 9066 art. 79) y las consultas "
                "de 9043, 9038 y 9068, que quedan como estaban redactadas. La "
                "aprobacion cubre solo la clase B'"),
    "B_parcial": ("primera pasada por Claude. Las tres filas de clase B que el "
                  "dictamen nombro individualmente, aprobadas el 2026-10-10 por "
                  "Leonardo Galeano (abogado). Las otras 79 de la clase siguen sin "
                  "veredicto individual documentado"),
}
FECHA = "2026-10-10"

EDITABLES = {"veredicto", "confianza", "justificacion", "revisor", "fecha_revision"}


def aplicar(filas: list[dict], clase: str) -> tuple[list[dict], list[str]]:
    etiqueta, dictamen = DICTAMENES[clase]
    nuevas, cambios = [], []
    for f in filas:
        g = dict(f)
        clave = (f["case_id"], f["doc_id"], f["articulo"])
        if f["clase_impacto"] == etiqueta:
            if clave not in dictamen:
                if clase in PARCIALES:
                    nuevas.append(g)
                    continue
                raise SystemExit(f"sin dictamen para {clave}")
            veredicto, conf, just = dictamen[clave]
            g.update({"veredicto": veredicto, "confianza": conf,
                      "justificacion": just, "revisor": FIRMAS[clase],
                      "fecha_revision": FECHA})
            cambios += [f"{'/'.join(clave)}: {f[c]!r} -> {g[c]!r}"
                        for c in ("veredicto",) if f[c] != g[c]]
        nuevas.append(g)
    return nuevas, cambios


def verificar(antes: list[dict], despues: list[dict], clase: str) -> list[str]:
    etiqueta, dictamen = DICTAMENES[clase]
    problemas = []

    tocadas = {c for a, b in zip(antes, despues) for c in COLUMNAS if a[c] != b[c]}
    de_mas = tocadas - EDITABLES
    if de_mas:
        problemas.append(f"columnas no autorizadas: {sorted(de_mas)}")

    # solo la clase pedida
    for a, b in zip(antes, despues):
        if a != b and a["clase_impacto"] != etiqueta:
            problemas.append(f"{a['case_id']}/art {a['articulo']}: es clase "
                             f"{a['clase_impacto']}, no {etiqueta}")

    de_la_clase = [f for f in despues if f["clase_impacto"] == etiqueta]
    if clase in PARCIALES:
        # registro parcial: solo se exige que lo dictaminado quede escrito
        for k in dictamen:
            fila = next((f for f in despues if (f["case_id"], f["doc_id"],
                                                f["articulo"]) == k), None)
            if fila is None:
                problemas.append(f"{k}: no hay fila en el CSV para esa clave")
            elif fila["veredicto"] == "pendiente":
                problemas.append(f"{k}: quedo pendiente")
    else:
        if len(de_la_clase) != len(dictamen):
            problemas.append(f"la clase tiene {len(de_la_clase)} filas y el "
                             f"dictamen {len(dictamen)}")
        for f in de_la_clase:
            if f["veredicto"] == "pendiente":
                problemas.append(f"{f['case_id']}/art {f['articulo']}: quedo pendiente")
        if f["huella_metadata"] != HASH_METADATA:
            problemas.append(f"{f['case_id']}/art {f['articulo']}: huella distinta")

    # las otras clases, intactas. Se compara el CAMBIO, no el estado: una clase
    # adjudicada en una corrida anterior debe quedar como esta, no volver a
    # pendiente ni figurar como problema de esta.
    for a, b in zip(antes, despues):
        if a["clase_impacto"] != etiqueta and a != b:
            tocadas = [c for c in COLUMNAS if a[c] != b[c]]
            problemas.append(f"{a['case_id']}/art {a['articulo']}: clase "
                             f"{a['clase_impacto']} modificada en {tocadas}")
    return problemas


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--clase", required=True, choices=sorted(DICTAMENES))
    p.add_argument("--escribir", action="store_true")
    args = p.parse_args(argv)

    with SALIDA.open(encoding="utf-8", newline="") as f:
        antes = list(csv.DictReader(f))
    despues, cambios = aplicar(antes, args.clase)

    for c in cambios:
        print(f"  {c}")
    from collections import Counter
    print(f"\nfilas modificadas: {sum(1 for a, b in zip(antes, despues) if a != b)}"
          f" de {len(antes)}")
    print(f"veredicto: {dict(Counter(f['veredicto'] for f in despues))}")
    de_clase = [f for f in despues if f['clase_impacto'] == DICTAMENES[args.clase][0]]
    print(f"clase {args.clase}: {dict(Counter(f['veredicto'] for f in de_clase))}")

    problemas = verificar(antes, despues, args.clase) + revisar(despues)
    if problemas:
        print(f"\n{len(problemas)} problemas: no se escribe nada")
        for s in problemas[:15]:
            print(f"  - {s}")
        return 1
    print("\nVerificacion: sin problemas.")

    if not args.escribir:
        print("Simulacion: no se escribio nada. Con --escribir se aplica.")
        return 0
    with SALIDA.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(despues)
    print(f"Escrito {SALIDA.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
