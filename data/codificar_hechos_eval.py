"""
Codifica los `hechos` de los 46 casos del eval set y los verifica contra el
motor de reglas.

Por que existe este script. El dataset tiene 95 de 143 casos cuyo mecanismo NO
se afirma: se DERIVA de hechos codificados a mano pasados por
`reglas.decidir()`. Ese control es el que encontro el error de A09 (estaba
etiquetado `accion_cumplimiento` y el art. 9 de la Ley 393 lo reencauza a
tutela). El eval set nunca paso por ese control, y es la vara con la que se
miden los tres modulos.

Los hechos son cuestiones de HECHO leidas del relato, nunca conclusiones
juridicas. La codificacion es esparcida: solo se escriben los campos que se
desvian del default del dataclass `Hechos`. `medio_eficaz` tiene default True,
asi que negarlo hay que hacerlo explicito.

El script es idempotente: se puede correr dos veces y el resultado es el mismo.
Si el motor no deriva la etiqueta, FALLA y no escribe nada.
"""
from __future__ import annotations
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.reglas import Hechos, decidir, estrato_verificacion  # noqa: E402

# --------------------------------------------------------------------------
# Los hechos, caso por caso.
#
# Cada entrada se lee del relato. El comentario dice que regla del art. 6
# cierra el caso, para que la codificacion sea auditable sin correr nada.
# --------------------------------------------------------------------------
HECHOS: dict[str, dict] = {
    # --- salud: no hay otro proceso judicial idoneo, entra por el art. 86 ---
    "E01": {"afectacion_individual": True},
    "E02": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "E11": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "E12": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "E13": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "E14": {"afectacion_individual": True},
    # A02 es relato mixto: la entrega del resultado de patologia (tutelable) y
    # el ruido del vecino. El ruido NO es `derecho_colectivo`: la lista del
    # art. 4 de la Ley 472 es cerrada y la perturbacion por ruido entre
    # vecinos es un asunto policivo de convivencia. Marcarlo colectivo
    # desviaria el caso a accion_popular, que es justo el error que el caso
    # busca provocar.
    "A02": {"afectacion_individual": True},

    # --- peticion: el mecanismo propio es la tutela (art. 23 CP) ---
    "E03": {"afectacion_individual": True},
    "E15": {"afectacion_individual": True},
    "E16": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "E17": {"afectacion_individual": True},

    # --- pensional: hay via laboral, la salva el perjuicio irremediable ---
    # La regla 6 no cierra porque concurre perjuicio => tutela TRANSITORIA.
    "E04": {"afectacion_individual": True, "otro_medio_judicial": True,
            "perjuicio_irremediable": True, "sujeto_especial_proteccion": True},
    "E26": {"afectacion_individual": True, "otro_medio_judicial": True,
            "perjuicio_irremediable": True, "sujeto_especial_proteccion": True},
    # A11: el medio ADEMAS es ineficaz en concreto (expectativa de vida menor
    # que la duracion del proceso), que es el supuesto del art. 6.1 leido en
    # concreto y no en abstracto.
    "A11": {"afectacion_individual": True, "otro_medio_judicial": True,
            "medio_eficaz": False, "perjuicio_irremediable": True,
            "sujeto_especial_proteccion": True},

    # --- habeas data: no hay otro proceso judicial, art. 15 CP ---
    "E05": {"afectacion_individual": True},
    "E19": {"afectacion_individual": True},
    "E20": {"afectacion_individual": True},

    # --- debido proceso ---
    # E06: contra un particular que presta el servicio publico de educacion;
    # la nulidad y restablecimiento no alcanza a un particular.
    "E06": {"afectacion_individual": True},
    # E25: no hubo acto administrativo notificado, luego no hay nada que
    # demandar en nulidad: el otro medio no existe materialmente.
    "E25": {"afectacion_individual": True, "sujeto_especial_proteccion": True},

    # --- educacion ---
    "E07": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "E21": {"afectacion_individual": True},
    "E22": {"afectacion_individual": True, "sujeto_especial_proteccion": True},

    # --- estabilidad laboral reforzada: hay via laboral pero ineficaz ---
    "E08": {"afectacion_individual": True, "otro_medio_judicial": True,
            "medio_eficaz": False, "sujeto_especial_proteccion": True},
    "E23": {"afectacion_individual": True, "otro_medio_judicial": True,
            "medio_eficaz": False, "sujeto_especial_proteccion": True},
    "E24": {"afectacion_individual": True, "otro_medio_judicial": True,
            "medio_eficaz": False, "sujeto_especial_proteccion": True},

    # --- minimo vital: la mora del empleador no es oponible a la madre ---
    "E18": {"afectacion_individual": True, "otro_medio_judicial": True,
            "medio_eficaz": False, "sujeto_especial_proteccion": True},

    # --- art. 6.3: derechos colectivos (art. 4 Ley 472) ---
    "E09": {"derecho_colectivo": True},
    "E27": {"derecho_colectivo": True},
    "E28": {"derecho_colectivo": True},

    # --- art. 9 Ley 393: cumplimiento, sin afectacion individual concreta ---
    "E29": {"incumplimiento_normativo": True},
    "E30": {"incumplimiento_normativo": True},
    # A09 es la trampa: MISMA estructura que E29/E30 pero CON afectado
    # concreto. El art. 9 hace improcedente el cumplimiento y reencauza a
    # tutela. Este es el caso que el control encontro mal etiquetado.
    "A09": {"incumplimiento_normativo": True, "afectacion_individual": True,
            "sujeto_especial_proteccion": True},

    # --- art. 6.2: libertad personal ---
    "E31": {"privacion_libertad": True, "afectacion_individual": True},
    "A10": {"privacion_libertad": True, "afectacion_individual": True},

    # --- art. 6.1: subsidiariedad, el otro medio es eficaz en concreto ---
    "E10": {"otro_medio_judicial": True},
    "E32": {"otro_medio_judicial": True},
    "E33": {"otro_medio_judicial": True},
    "E34": {"otro_medio_judicial": True},
    "A05": {"otro_medio_judicial": True},
    "A06": {"otro_medio_judicial": True, "sujeto_especial_proteccion": True},
    # A03: finalidad estetica, sin orden del medico tratante adscrito ni
    # afectacion funcional => no hay derecho fundamental comprometido.
    "A03": {"otro_medio_judicial": True},

    # --- art. 6.4: dano consumado, sin vulneracion que continue ---
    "A01": {"dano_consumado": True},
    "A07": {"dano_consumado": True},
    # A12: la situacion ya fue superada (termino bachillerato en otro colegio
    # y esta en la universidad); no hay amenaza actual que proteger.
    "A12": {"dano_consumado": True},

    # --- los dos que el arbol del art. 6 no modela (ver NO_MODELADOS) ---
    "A04": {"otro_medio_judicial": True},
    "A08": {"otro_medio_judicial": True},
}

# --------------------------------------------------------------------------
# Desglose de los dos juicios, caso por caso.
#
# El analisis de sensibilidad midio que 19 de 63 etiquetas pivotaban en
# `medio_eficaz` o `perjuicio_irremediable` AFIRMADOS, y ahi la verificacion
# por reglas valia poco: quien codifica conoce la etiqueta.
#
# Estos desgloses mueven la discrecion del booleano a elementos que se leen
# del relato. El motor re-deriva el booleano con el test conjuntivo y FALLA si
# no coincide, asi que ya no se puede "elegir" el resultado sin dejar rastro.
#
#   perjuicio irremediable: inminencia + gravedad + urgencia +
#   impostergabilidad, los cuatro elementos que la jurisprudencia
#   constitucional exige de forma concurrente desde la T-225 de 1993.
#
#   eficacia del otro medio: idoneidad (sirve para lo pedido) + oportunidad
#   (alcanza en el tiempo de ESTA persona) + accesibilidad. El art. 6.1 manda
#   apreciarla "atendiendo las circunstancias en que se encuentre el
#   solicitante", no en abstracto.
#
# Los tres casos que pivotan en `continua_vulneracion` (A01, A07, A12) NO se
# desglosan: ese campo pregunta un hecho del mundo --- si la accion u omision
# subsiste --- y los tres relatos lo responden directamente (la cirugia ya se
# hizo, la persona murio, el bachillerato se termino en otro colegio). No se
# reclasifican a `plano` para mejorar el conteo: siguen contando como juicio.
# --------------------------------------------------------------------------
PI = ("pi_inminencia", "pi_gravedad", "pi_urgencia", "pi_impostergabilidad")
ME = ("me_idoneo", "me_oportuno", "me_accesible")


def _pi(i, g, u, p) -> dict:
    return dict(zip(PI, (i, g, u, p)))


def _me(i, o, a) -> dict:
    return dict(zip(ME, (i, o, a)))


DESGLOSE: dict[str, dict] = {
    # --- pensionales: los cuatro elementos concurren ---
    # 71 anos, sin ingresos ni red de apoyo, ocho meses sin resolver.
    "E04": _pi(True, True, True, True),
    # 68 anos, dependencia economica total del causante, el fondo pide esperar
    # dos anos.
    "E26": _pi(True, True, True, True),

    # --- estabilidad laboral y minimo vital: el medio no es OPORTUNO ---
    # La jurisdiccion laboral es idonea y accesible, pero si pierde el
    # contrato pierde la afiliacion y con ella la quimioterapia: el proceso no
    # alcanza en el tiempo del que dispone.
    "E08": _me(True, False, True),
    # La licencia de maternidad cubre un periodo determinado; un proceso
    # ordinario lo desborda y mientras tanto no hay con que vivir.
    "E18": _me(True, False, True),
    # El fuero de maternidad protege un periodo acotado.
    "E23": _me(True, False, True),
    # Igual que E08: perder el empleo es perder el tratamiento.
    "E24": _me(True, False, True),

    # --- subsidiariedad: el medio SI es eficaz y no hay perjuicio ---
    # Consumidor: la accion ante la SIC sirve para lo pedido y llega a tiempo.
    "E10": {**_me(True, True, True), **_pi(False, False, False, False)},
    # Estetica sin orden del medico tratante adscrito ni afectacion funcional.
    "A03": {**_me(True, True, True), **_pi(False, False, False, False)},
    # Los recursos ordinarios ERAN el medio idoneo y se agotaron. Ver
    # NO_MODELADOS: el fundamento que emite el motor no es el que un juez
    # usaria, pero el mecanismo si.
    "A04": {**_me(True, True, True), **_pi(False, False, False, False)},
    # Cobro de prestaciones con ejecutivo laboral disponible; renuncio hace
    # seis meses y no alega afectacion actual del minimo vital.
    "E32": {**_me(True, True, True), **_pi(False, False, False, False)},
    # Acto administrativo particular: nulidad y restablecimiento, con medidas
    # cautelares del art. 230 de la Ley 1437 disponibles.
    "E33": {**_me(True, True, True), **_pi(False, False, False, False)},
    # Titulo ejecutivo entre particulares.
    "E34": {**_me(True, True, True), **_pi(False, False, False, False)},
    # Honorarios pactados; el accionante es abogado en ejercicio, luego el
    # medio le es plenamente accesible.
    "A05": {**_me(True, True, True), **_pi(False, False, False, False)},
    # Alimentos y visitas: la comisaria y el juez de familia son los medios
    # idoneos. La subsistencia de dos menores SI es un bien grave --- se deja
    # marcado --- pero el test es conjuntivo y no concurren los otros tres.
    "A06": {**_me(True, True, True), **_pi(False, True, False, False)},
    # El derecho de peticion fue satisfecho; la inconformidad con el contenido
    # se controvierte por los medios ordinarios.
    "A08": {**_me(True, True, True), **_pi(False, False, False, False)},
}

# --------------------------------------------------------------------------
# Honestidad sobre los limites del motor.
#
# Estos dos casos llegan al mecanismo correcto por la regla 6, pero la razon
# juridica real NO es la del art. 6.1. Se deja escrito para no afirmar una
# cobertura que el motor no tiene.
# --------------------------------------------------------------------------
NO_MODELADOS = {
    "A04": "tutela contra providencia judicial. Su procedencia se rige por las "
           "causales especificas de la C-590 de 2005 (defecto factico, "
           "sustantivo, procedimental), que el motor no implementa. Aqui la "
           "regla 6 llega a via_ordinaria porque el medio idoneo existio y se "
           "agoto, pero el fundamento que emite el motor (art. 6.1) no es el "
           "que un juez usaria.",
    "A08": "el derecho de peticion FUE satisfecho (respuesta oportuna, de fondo "
           "y congruente). El motor no tiene una regla 'no hay vulneracion que "
           "amparar': llega a via_ordinaria por subsidiariedad, que es el "
           "mecanismo correcto, con un fundamento que no es el preciso.",
}


# --------------------------------------------------------------------------
# Que prueba, y que NO prueba, el "46/46 verificados".
#
# Prueba que cada etiqueta es EXPRESABLE en el arbol del art. 6: existe una
# codificacion de hechos, leida del relato, de la que el motor deriva ese
# mecanismo. Eso descarta etiquetas incoherentes con el ordenamiento, y es lo
# que encontro el error de A09.
#
# NO prueba que la etiqueta sea correcta. Quien codifico los hechos conocia la
# etiqueta, asi que en los casos donde un hecho admite dos valores defendibles
# la codificacion pudo elegirse hacia atras, y el motor la confirma sin
# pestanear. Esto distingue los dos grupos, en vez de dejar el 46/46 solo.
# --------------------------------------------------------------------------
def main() -> int:
    ruta = RAIZ / "data" / "eval_set.json"
    d = json.loads(ruta.read_text(encoding="utf-8"))
    casos = d["ejemplos"]

    ids = {c["id"] for c in casos}
    faltan = ids - HECHOS.keys()
    sobran = HECHOS.keys() - ids
    if faltan:
        print(f"FALLA: sin hechos codificados: {sorted(faltan)}")
        return 1
    if sobran:
        print(f"FALLA: hechos para ids que no existen: {sorted(sobran)}")
        return 1

    errores: list[str] = []
    ok = 0
    for c in casos:
        h = {**HECHOS[c["id"]], **DESGLOSE.get(c["id"], {})}
        try:
            dec = decidir(Hechos(**h))
        except (TypeError, ValueError) as ex:
            errores.append(f"{c['id']}: hechos invalidos -> {ex}")
            continue
        if dec.mecanismo != c["mecanismo"]:
            errores.append(
                f"{c['id']} ({c['categoria']}): etiqueta={c['mecanismo']} "
                f"pero el motor deriva {dec.mecanismo} (regla: {dec.regla})")
            continue
        if dec.procede_tutela != c["procede"]:
            errores.append(
                f"{c['id']}: procede={c['procede']} pero el motor deriva "
                f"{dec.procede_tutela}")
            continue
        ok += 1
        c["hechos"] = h
        c["verificado_con_reglas"] = True
        c["regla_que_cierra"] = dec.regla
        est, campos = estrato_verificacion(Hechos(**h))
        c["estrato_verificacion"] = est         # plano | derivado | juicio
        c["etiqueta_pivota_en"] = campos
        if c["id"] in NO_MODELADOS:
            c["limite_del_motor"] = NO_MODELADOS[c["id"]]

    if errores:
        print(f"FALLA: el motor no deriva la etiqueta en {len(errores)} casos.")
        print("No se escribio nada.\n")
        for e in errores:
            print(f"  - {e}")
        return 1

    estratos = Counter(c["estrato_verificacion"] for c in casos)
    d["meta"]["verificacion"] = {
        "casos_con_hechos": ok,
        "casos_totales": len(casos),
        "metodo": "los `hechos` se codificaron leyendo cada relato y se pasaron "
                  "por src/reglas.decidir(). El mecanismo y la procedencia NO se "
                  "afirman: el motor los deriva y tienen que coincidir con la "
                  "etiqueta. Si no coinciden, data/codificar_hechos_eval.py "
                  "falla y no escribe nada.",
        "que_prueba": "que cada etiqueta es EXPRESABLE en el arbol del art. 6: "
                      "existe una codificacion de hechos leida del relato de la "
                      "que el motor deriva ese mecanismo. Eso descarta etiquetas "
                      "incoherentes con el ordenamiento, y es lo que encontro el "
                      "error de A09.",
        "estratos": {
            "plano": estratos["plano"],
            "derivado": estratos["derivado"],
            "juicio": estratos["juicio"],
            "lectura":
                "`plano`: el mecanismo lo fuerzan hechos que se leen del relato. "
                "`derivado`: depende de una ponderacion, pero esa ponderacion "
                "esta desglosada en elementos leibles y el motor la re-deriva "
                "con el test conjuntivo, fallando si el booleano afirmado no "
                "coincide --- el perjuicio irremediable por los cuatro elementos "
                "exigidos de forma concurrente desde la T-225 de 1993, y la "
                "eficacia del otro medio por idoneidad, oportunidad y "
                "accesibilidad, que es la apreciacion en concreto que ordena el "
                "art. 6.1. `juicio`: depende de una ponderacion afirmada sin "
                "desglose, y ahi la verificacion vale menos.",
            "sin_desglosar":
                "los casos que quedan en `juicio` pivotan en "
                "`continua_vulneracion`, que pregunta un hecho del mundo (si la "
                "accion u omision subsiste) y que los relatos responden "
                "directamente. NO se reclasificaron a `plano` para mejorar el "
                "conteo.",
        },
        "limites_conocidos": NO_MODELADOS,
    }
    ruta.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"OK: {ok}/{len(casos)} casos verificados con el motor de reglas.")
    print("\nestrato de verificacion:")
    for e in ("plano", "derivado", "juicio"):
        print(f"  {e:10s} {estratos[e]}")
    print("\nregla que cierra cada caso:")
    for r, n in Counter(c["regla_que_cierra"] for c in casos).most_common():
        print(f"  {r:24s} {n}")
    print(f"\nlimites del motor documentados: {sorted(NO_MODELADOS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
