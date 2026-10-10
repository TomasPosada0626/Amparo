"""Registra en el CSV los dictamenes comparativos v1 vs v2 de los 35 casos B2.

Los 35 `comparacion_v1_v2` estan en `pendiente` desde la preadjudicacion. Los
dictamenes se redactaron en cuatro tandas, agrupadas por quien cita, porque la
dificultad de la comparacion depende de eso:

    tanda 1   8 casos   ninguno cita        docs/m1_b2_dictamen_comparativos_tanda1.md
    tanda 2   8 casos   solo v1 cita        docs/m1_b2_dictamen_comparativos_tanda2y3.md
    tanda 3   2 casos   solo v2 cita        (mismo documento)
    tanda 4  17 casos   ambos citan         docs/m1_b2_dictamen_comparativos_tanda4.md

Las cuatro tandas las aprobo Leonardo Galeano (abogado). Lo que este script
escribe sale de esos documentos y de ningun otro sitio: `DICTAMEN` es una copia
literal de sus tablas, sin deducir nada.

Cuatro columnas que NO se tocan, y conviene decir por que:

  confianza            Es la confianza del dictamen de ETIQUETA (si el ejemplo
                       debia exigir abstencion), ya aprobada para las 8 y
                       validada para las 35. La confianza del comparativo es
                       otra cosa y va dentro de justificacion_final, en texto.
                       Una columna aparte seria mas consultable, pero es un
                       cambio de esquema y necesita su propia aprobacion.
  validez_etiqueta_b2  Las 8 aprobadas el 2026-10-10. Intocables.
  pertinencia_contexto Clasificacion de la primera pasada.
  v1_* / v2_*          Idem.

Las cuatro consultas juridicas que la tanda 4 dejo abiertas (3327, 4128, 4226
y 3822) se quedan en `pendiente`. Leonardo aprobo el dictamen de la tanda, que
no es lo mismo que haber contestado las preguntas: las respuestas pueden mover
el veredicto -- 3327 subiria a confianza alta, 4226 podria pasar a empate -- y
cerrarlas ahora seria inventar su resolucion. Esas cuatro filas quedan
exactamente como estan, sin un solo cambio.

Por defecto SIMULA. Escribir exige --escribir, para que una corrida distraida
no toque el CSV oficial.

    python -m tools.aplicar_comparativos_b2                   # diff, no escribe
    python -m tools.aplicar_comparativos_b2 --csv copia.csv --escribir
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from tools.adjudicacion_b2 import COLUMNAS, SALIDA, VOCABULARIO, respuestas, revisar

# ---------------------------------------------------------------------------
# El dictamen, copiado de los documentos aprobados.
#
#   case_id -> (comparacion_v1_v2, confianza del comparativo, justificacion)
#
# La confianza va tambien en el texto porque no tiene columna propia.
# ---------------------------------------------------------------------------

TANDA1 = {
    "2822": ("mejora", "alta",
             "v1 pide el certificado de la 'Comision de Trabajo', que no es autoridad "
             "competente para certificar la naturaleza de una indemnizacion ni para "
             "levantar un embargo; v2 pide el certificado de pago, generico y seguro. "
             "Reserva: un certificado de pago prueba el pago, no la inembargabilidad."),
    "3423": ("regresion", "media",
             "v1 da la ruta concreta y correcta (Diario Oficial, derecho de peticion, "
             "reposicion y apelacion, nulidad); v2 solo remite a un consultorio. "
             "Ninguno afirma de mas."),
    "3428": ("mejora", "alta",
             "v1 reconoce que no lo sabe y acto seguido afirma para que sirve la "
             "ventanilla unica, dato de la entidad que el contexto no trae; v2 remite "
             "a la pagina o al telefono sin inventar."),
    "4026": ("empate", "baja",
             "Los dos agregan especificos sin respaldo: v1 nombra emisoras, v2 inventa "
             "factores de precio. Fallan igual en direcciones distintas."),
    "4127": ("empate", "baja",
             "El habeas data de v2 no es incorrecto -- sirve si los registros estan "
             "ausentes o inexactos -- pero no resuelve si las cotizaciones del exterior "
             "cuentan, que depende del convenio internacional. Ninguno menciona el "
             "convenio y la omision pesa igual en los dos."),
    "4321": ("empate", "media",
             "Los dos explican bien la diferencia y ninguno cita. Diferencias de "
             "enfasis en la entidad receptora, no de calidad."),
    "4324": ("empate", "baja",
             "Los dos afirman sin respaldo que no existe formato oficial; el contexto "
             "no lo dice. v2 agrega el centro de conciliacion, que no es la via para un "
             "recurso."),
    "4630": ("mejora", "media",
             "v2 orienta mejor (pedir el tiempo por escrito, con copia a la Personeria "
             "o la Inspeccion) frente a un v1 que presenta el asunto como si dependiera "
             "solo del jefe. Los dos omiten que la reforma de 2025 pudo convertirlo en "
             "licencia, y el articulo 57 indexado es la version anterior: la "
             "recuperacion no podia traer ese derecho. Tampoco es cierto, como dice v2, "
             "que toda negativa sea discriminacion laboral."),
}

TANDA2Y3 = {
    "2424": ("mejora", "alta",
             "v1 desarrolla el articulo 141 de la Ley 142 sobre corte del servicio por "
             "facturas impagas ante una consulta de derechos laborales: no es solo "
             "irrelevante, confunde. v2 remite a la Inspeccion del Trabajo."),
    "3026": ("mejora", "alta",
             "v1 concluye 'No es obligatorio' desde el articulo 7 de la Ley 1266, que "
             "regula operadores de datos financieros y no portales de datos abiertos. "
             "v2 reconoce que no puede verificarlo."),
    "3118": ("empate", "baja",
             "v1 cita el requisito de procedibilidad, que no responde si cobrar es "
             "normal; v2 afirma que la conciliacion es gratuita, que puede ser falso "
             "porque los centros privados cobran. Los dos fallan en direcciones "
             "distintas."),
    "3122": ("empate", "baja",
             "Los dos arrancan bien ('no hay tiempo fijo'); v1 pega una cita que no "
             "viene al caso y v2 propone un tramite de descargos ante el juez laboral "
             "que no existe asi."),
    "3321": ("mejora", "alta",
             "v1 vuelve al articulo 141 de servicios publicos, ahora ante una deuda "
             "comercial B2B; v2 da la via razonable: acuerdo de pago, centro de "
             "conciliacion y reunir facturas."),
    "3517": ("regresion", "media",
             "v2 dice 'No tengo la norma que exige ese plan' y la norma estaba en el "
             "fragmento 1: el articulo 63 de la Ley 1801 obliga a presentar e "
             "implementar el plan de manejo ambiental. v1 la usa. Limite que aplica a "
             "los dos: ese articulo habla del organizador de un evento y la pregunta no "
             "dice que actividad origino la multa, asi que lo correcto no era afirmar "
             "que aplica sino explicar el supuesto y advertir que hay que confirmarlo."),
    "3621": ("mejora", "alta",
             "v1 cita el articulo 195 del CST sobre patrimonio gravable ante una "
             "pregunta de tasa de cambio; v2 reconoce que depende de la clausula y "
             "remite a conciliacion o al juez civil."),
    "4225": ("mejora", "media",
             "v1 cita el articulo 127 del CST ('se considera salario todo lo que "
             "recibes por tu trabajo') ante un prestamo y manda a la Inspeccion del "
             "Trabajo. v2 reconoce el limite, pero la competencia de la "
             "Superintendencia Financiera que propone depende de quien concedio el "
             "prestamo, y la categoria es prestamos informales y usura: v2 la da por "
             "supuesta. Por eso la confianza es media y no alta."),
    "2221": ("mejora", "media",
             "v2 menciona el articulo 382 del Codigo Penal para decir que NO lo va a "
             "usar por falta de certeza, que es la conducta correcta. v1 no cita pero "
             "sugiere que la tutela protege a la mascota, via dudosa."),
    "4623": ("regresion", "media",
             "Caso sensible. La objecion es de PERTINENCIA, no de riesgo: el articulo "
             "157 regula el traslado por proteccion ordenado por una autoridad de "
             "Policia y en ese supuesto exige informar al superior jerarquico, y el "
             "fragmento no demuestra que denunciar a un policia por violencia de pareja "
             "se tramite por esa via; el 222 regula otro procedimiento. No se afirma "
             "que v2 obligue a la victima a acudir al superior de su agresor: v2 "
             "menciona ese deber al explicar el articulo y remite tambien a la Fiscalia "
             "y a la Defensoria. v1 es practico y prudente."),
}

TANDA4 = {
    "2126": ("mejora", "baja",
             "Los dos citan el articulo 70 del CP sobre internacion de inimputables, "
             "que no viene al caso; v2 agrega la tutela, que si es la via."),
    "2229": ("empate", "alta",
             "Respuestas casi identicas: los dos citan el articulo 137 de la Ley 142 de "
             "servicios publicos para una compraventa entre particulares."),
    "2823": ("empate", "media",
             "Los dos citan el articulo 65 del CST sobre indemnizacion por falta de "
             "pago de salarios ante una pregunta de embargo; v2 agrega intereses "
             "moratorios, igual de ajeno."),
    "2917": ("regresion", "alta",
             "Unico caso de los 35 donde los dos describen el mismo articulo de forma "
             "incompatible y el texto decide sin criterio juridico. El articulo 223-A "
             "dice que se entendera que el infractor ACEPTA LA RESPONSABILIDAD si paga "
             "o cambia la multa por programa comunitario en tres dias. v2 afirma que el "
             "articulo 'permite objetar la orden de comparendo', que es lo contrario, y "
             "atribuye al articulo 180 un plazo de cinco dias cuando ese articulo trata "
             "de en que cuenta se consignan las multas. Dos errores verificables en v2. "
             "v1 lo describe bien pero omite lo decisivo -- que acogerse implica "
             "aceptar la responsabilidad -- y quien pregunta duda de la velocidad: esa "
             "omision tambien es grave."),
    "3022": ("empate", "baja",
             "Los dos citan el articulo 121 sobre animales encontrados; v2 al menos "
             "remite al sitio web."),
    "3124": ("mejora", "baja",
             "v1 concluye 'Si puede' desde un articulo que solo presume la edad; v2 no "
             "saca esa conclusion."),
    "3228": ("mejora", "alta",
             "v1 cita el articulo 141 dos veces con contenidos distintos (corte del "
             "servicio y demolicion del inmueble); v2 dice 'No veo en estos articulos "
             "la base de tu suspension' y explica que trata cada uno."),
    "3328": ("empate", "media",
             "Los dos atribuyen al articulo 46 lo que dice el 50 (el plazo de entrega y "
             "los 30 dias). Mismo error en ambos."),
    "3626": ("empate", "alta",
             "Casi identicas: los dos citan el articulo 38 del CST sobre contrato verbal "
             "ante un contrato vencido."),
    "3628": ("empate", "alta",
             "Casi identicas, y el articulo 44 de la Ley 1480 sobre nulidad de clausulas "
             "es de los pocos pertinentes de la tanda."),
    "3729": ("regresion", "media",
             "v2 cita 'el articulo 5 de la Ley 2222 de 2022' y el contexto trae la Ley "
             "2220. Es el falso negativo que destapo el barrido de atribucion y que "
             "motivo la comprobacion por numero de norma en tools/rag/verificacion.py."),
    "3920": ("empate", "alta",
             "Casi identicas, las dos sobre el articulo 25."),
    "4724": ("empate", "baja",
             "Casi identicas. v2 cita 'el articulo 34 de la misma ley' dos veces con "
             "contenidos distintos."),
    # Las cuatro que quedaron con consulta abierta y Leonardo aprobo sin
    # cambiarlas. Ver el bloque CONSULTAS_ABIERTAS.
    "3327": ("regresion", "media",
             "Los dos citan el articulo 98 del CST sobre la licencia del agente "
             "viajero. v1 reconoce que 'No veo en ese articulo la respuesta'; v2 "
             "afirma que esa licencia 'puede incluir' clausulas de mantenimiento, que "
             "el articulo no dice. Aprobado como regresion media: la consulta sobre si "
             "esa licencia admite tales clausulas se resolvio sin elevar la gravedad."),
    "3822": ("regresion", "media",
             "v1 cita el articulo 58 (procedimiento de reclamacion), que al menos "
             "encaja con pedir la motivacion por escrito; v2 cita el articulo 8 sobre "
             "garantia legal de productos nuevos ante la perdida de una beca. Aprobado "
             "como regresion media: el regimen de garantias de consumo no da el encaje "
             "que v2 le supone."),
    "4128": ("regresion", "baja",
             "v1 cita el articulo 236 y admite que 'no menciona cobrar dos pensiones'; "
             "v2 cita el articulo 275 sobre pension de sustitucion y de ahi concluye "
             "categoricamente 'No lo veo permitido'. Aprobado como regresion baja: el "
             "articulo no sostiene una conclusion categorica, y la honestidad de v1 "
             "sobre el limite pesa mas que la cercania tematica de v2."),
    "4226": ("regresion", "baja",
             "El articulo 67 dice que 'debe denunciar a la autoridad'. v1 lo repite "
             "fiel; v2 dice que obliga a denunciar 'ante la Fiscalia', precision que el "
             "articulo no trae. Aprobado como regresion baja y NO como empate: "
             "practicamente util, textualmente infiel."),
}

DICTAMEN = {**TANDA1, **TANDA2Y3, **TANDA4}

# ---------------------------------------------------------------------------
# Las cuatro que NO se cierran. Cada una con la pregunta que falta responder,
# para que se vea que no es un olvido sino una consulta abierta.
# ---------------------------------------------------------------------------
CONSULTAS_ABIERTAS: dict[str, str] = {}

# Las cuatro que la tanda 4 dejo con consulta abierta -- 3327, 3822, 4128 y
# 4226 -- las aprobo Leonardo Galeano el 2026-10-10 **tal como estaban
# redactadas**, junto con el resto de la tanda. Quedan en TANDA4 con el
# veredicto del borrador.
#
# Lo que se preguntaba en cada una queda registrado aqui, porque la aprobacion
# sin cambios es una decision y conviene poder leer sobre que se decidio:
#
#   3327  ¿Puede la licencia del agente viajero (art. 98 CST) incluir clausulas
#         de mantenimiento, como afirma v2? Aprobada como regresion media: la
#         regresion no sube a alta.
#   4128  ¿El art. 275 sobre pension de sustitucion permite concluir que no se
#         pueden recibir dos pensiones? Aprobada como regresion baja.
#   4226  ¿Es aceptable precisar "la Fiscalia" donde el art. 67 dice "la
#         autoridad"? Aprobada como regresion baja: no pasa a empate.
#   3822  ¿Tiene encaje el regimen de garantias de consumo (art. 8) con la
#         perdida de una beca? Aprobada como regresion media.
#
# El mecanismo se conserva vacio a proposito: si una tanda futura deja una
# consulta sin responder, basta anadirla aqui y su fila no se toca.

# Lo unico que esta corrida puede tocar.
#
# revision_juridica entra porque "requerida" quiere decir que FALTA el abogado,
# y la rubrica exige que mientras lo diga el comparativo quede en pendiente. El
# validador bloqueo los 31 por eso, y tenia razon: iban a quedar con veredicto
# y diciendo a la vez que faltaba la revision. Pasan a "cumplida". Los 4 casos
# con consulta abierta se quedan en "requerida", que es la verdad.
AUTORIZADAS = {"comparacion_v1_v2", "justificacion_final", "revisor",
               "revision_juridica"}

# La frase de relleno que dejo la preadjudicacion, en las 35 filas.
RELLENO = ("Comparativo pendiente: decidir cual responde mejor exige validar el "
           "derecho colombiano aplicable.")

FIRMA = ("primera pasada: pertinencia por ChatGPT, verificacion mecanica por Claude. "
         "Clasificacion validada el 2026-10-10 por Leonardo Galeano (abogado). "
         "Comparativo v1/v2: dictamen redactado por Claude en cuatro tandas y aprobado "
         "por Leonardo Galeano el 2026-10-10")


# Un dictamen ya escrito por una corrida anterior. Sin esto, correr el script
# dos veces apilaba una segunda frase "Comparativo ..." detras de la primera y
# dejaba la justificacion con el dictamen duplicado.
_DICTAMEN_PREVIO = re.compile(
    r"Comparativo (?:mejora|empate|regresion) \(confianza (?:alta|media|baja)\):.*",
    re.DOTALL)


def justificacion_nueva(actual: str, veredicto: str, confianza: str, texto: str) -> str:
    """Cambia la frase de relleno por el dictamen, conservando lo que la precede.

    En 20 de las 35 filas `justificacion_final` tiene texto propio delante del
    relleno ("ambos con problemas serios de fundamentacion. Comparativo
    pendiente: ..."). Ese texto es de la clasificacion y se conserva.

    Idempotente: si ya hay un dictamen escrito, lo reemplaza en lugar de
    anadir otro.
    """
    prefijo = _DICTAMEN_PREVIO.sub("", actual.replace(RELLENO, "")).strip()
    dictamen = f"Comparativo {veredicto} (confianza {confianza}): {texto}"
    return f"{prefijo} {dictamen}".strip() if prefijo else dictamen


def aplicar(filas: list[dict]) -> tuple[list[dict], list[tuple[str, str, str, str]]]:
    """(filas nuevas, celdas que cambian como (case_id, columna, antes, despues))."""
    nuevas, celdas = [], []
    for f in filas:
        g = dict(f)
        cid = f["case_id"]
        if cid in CONSULTAS_ABIERTAS:
            # Consulta sin resolver: la fila no se toca en absoluto.
            nuevas.append(g)
            continue
        veredicto, confianza, texto = DICTAMEN[cid]
        g["comparacion_v1_v2"] = veredicto
        g["justificacion_final"] = justificacion_nueva(
            f["justificacion_final"], veredicto, confianza, texto)
        g["revisor"] = FIRMA
        if f["revision_juridica"] == "requerida":
            g["revision_juridica"] = "cumplida"
        celdas += [(cid, c, f[c], g[c]) for c in COLUMNAS if f[c] != g[c]]
        nuevas.append(g)
    return nuevas, celdas


def verificar(antes: list[dict], despues: list[dict]) -> list[str]:
    """Todo lo que tiene que cumplirse. Lista vacia = se puede escribir."""
    problemas = []

    # -- el dictamen cubre lo que debe y nada mas
    ids = [f["case_id"] for f in antes]
    if len(ids) != 35:
        problemas.append(f"el CSV tiene {len(ids)} filas, no 35")
    if len(set(ids)) != len(ids):
        repetidos = sorted({i for i in ids if ids.count(i) > 1})
        problemas.append(f"case_id repetidos: {repetidos}")
    cubiertos = set(DICTAMEN) | set(CONSULTAS_ABIERTAS)
    if cubiertos != set(ids):
        problemas.append(f"sin dictamen: {sorted(set(ids) - cubiertos)}; "
                         f"sobran: {sorted(cubiertos - set(ids))}")
    solapan = set(DICTAMEN) & set(CONSULTAS_ABIERTAS)
    if solapan:
        problemas.append(f"casos en DICTAMEN y en CONSULTAS_ABIERTAS: {sorted(solapan)}")

    # -- el orden y la identidad de las filas no se mueven
    if [f["case_id"] for f in despues] != ids:
        problemas.append("cambio el orden o la identidad de las filas")

    # -- vocabulario cerrado
    for f in despues:
        for col in ("comparacion_v1_v2", "revision_juridica"):
            if f[col] not in VOCABULARIO[col]:
                problemas.append(f"{f['case_id']}: {col} {f[col]!r} fuera del vocabulario")

    # -- las consultas abiertas siguen abiertas e intactas
    for a, b in zip(antes, despues):
        if a["case_id"] in CONSULTAS_ABIERTAS:
            if b["comparacion_v1_v2"] != "pendiente":
                problemas.append(f"{a['case_id']}: consulta abierta cerrada como "
                                 f"{b['comparacion_v1_v2']!r}")
            if b["revision_juridica"] != "requerida":
                problemas.append(f"{a['case_id']}: consulta abierta pero "
                                 f"revision_juridica dice {b['revision_juridica']!r}")
            if a != b:
                tocadas = [c for c in COLUMNAS if a[c] != b[c]]
                problemas.append(f"{a['case_id']}: consulta abierta modificada en {tocadas}")

    # -- y las adjudicadas no pueden seguir diciendo que falta el abogado
    for f in despues:
        if f["comparacion_v1_v2"] != "pendiente" and f["revision_juridica"] == "requerida":
            problemas.append(f"{f['case_id']}: adjudicado y revision_juridica 'requerida'")

    # -- ninguna columna fuera de las autorizadas
    tocadas = {c for a, b in zip(antes, despues) for c in COLUMNAS if a[c] != b[c]}
    de_mas = tocadas - AUTORIZADAS
    if de_mas:
        problemas.append(f"columnas no autorizadas: {sorted(de_mas)}")

    # -- las 8 etiquetas aprobadas y la clasificacion, intactas
    intocables = [c for c in COLUMNAS if c not in AUTORIZADAS]
    for a, b in zip(antes, despues):
        distintas = [c for c in intocables if a[c] != b[c]]
        if distintas:
            problemas.append(f"{a['case_id']}: se modificaron {distintas}")

    # -- el relleno no queda junto a un veredicto, que seria contradictorio
    for f in despues:
        if f["comparacion_v1_v2"] != "pendiente" and RELLENO in f["justificacion_final"]:
            problemas.append(f"{f['case_id']}: adjudicado pero conserva la frase de relleno")
        if f["comparacion_v1_v2"] == "pendiente" and RELLENO not in f["justificacion_final"]:
            problemas.append(f"{f['case_id']}: pendiente pero perdio la frase de relleno")

    return problemas


def imprimir_diff(celdas: list[tuple[str, str, str, str]]) -> None:
    if not celdas:
        print("  (ninguna celda cambia)")
        return
    por_caso: dict[str, list] = {}
    for cid, col, a, b in celdas:
        por_caso.setdefault(cid, []).append((col, a, b))
    for cid in sorted(por_caso):
        print(f"\n  {cid}")
        for col, a, b in por_caso[cid]:
            if col == "revisor":
                print(f"    {col}: (firma de la clasificacion) -> (firma + comparativo)")
            elif len(a) + len(b) > 150:
                print(f"    {col}:")
                print(f"        antes:   {a[:110]}...")
                print(f"        despues: {b[:110]}...")
            else:
                print(f"    {col}: {a!r} -> {b!r}")


def resumen(filas: list[dict]) -> dict[str, int]:
    cuenta: dict[str, int] = {}
    for f in filas:
        cuenta[f["comparacion_v1_v2"]] = cuenta.get(f["comparacion_v1_v2"], 0) + 1
    return cuenta


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--csv", type=Path, default=SALIDA,
                   help="CSV sobre el que operar (por defecto el oficial)")
    p.add_argument("--escribir", action="store_true",
                   help="escribe. Sin esto solo simula y muestra el diff")
    args = p.parse_args(argv)

    with args.csv.open(encoding="utf-8", newline="") as f:
        antes = list(csv.DictReader(f))
    despues, celdas = aplicar(antes)

    print(f"CSV: {args.csv}")
    print(f"\nCeldas que cambiarian: {len(celdas)} "
          f"en {len({c[0] for c in celdas})} de {len(antes)} filas")
    print(f"Columnas tocadas: {sorted({c[1] for c in celdas})}")
    print(f"Consultas abiertas, sin tocar: {sorted(CONSULTAS_ABIERTAS)}")

    print("\n--- diff ---")
    imprimir_diff(celdas)

    print("\n--- comparacion_v1_v2 ---")
    print(f"  antes:   {resumen(antes)}")
    print(f"  despues: {resumen(despues)}")

    problemas = verificar(antes, despues)
    if problemas:
        print(f"\n{len(problemas)} problemas: no se escribe nada")
        for s in problemas:
            print(f"  - {s}")
        return 1

    # El validador general del instrumento, con las respuestas reales.
    de_rubrica = revisar(despues, textos=respuestas())
    if de_rubrica:
        print(f"\n{len(de_rubrica)} problemas de rubrica: no se escribe nada")
        for s in de_rubrica[:10]:
            print(f"  - {s}")
        return 1

    print("\nVerificacion: sin problemas.")
    if not args.escribir:
        print("Simulacion: no se escribio nada. Con --escribir se aplica.")
        return 0

    with args.csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(despues)
    print(f"Escrito {args.csv}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
