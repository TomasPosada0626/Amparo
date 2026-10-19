"""
Codifica los `hechos` de los 30 casos originales y desglosa los juicios
afirmados del dataset (ROADMAP #28).

DOS PARTES

1. Los 30 originales (T01-T20, V01-V10) nunca pasaron por el motor de reglas:
   su mecanismo se AFIRMABA. Eran los unicos del dataset sin `hechos`, y son
   justo los primeros que se escribieron, cuando el motor todavia no existia.

2. **25 de los 95 verificados pivotaban en una ponderacion AFIRMADA** --- la
   misma debilidad que tenia el eval set antes del analisis de sensibilidad.
   Se desglosan los que tienen test doctrinal, igual que alli.

LAS TRES FAMILIAS DE LOS 25, Y QUE SE HACE CON CADA UNA

  A. `via_ordinaria` con medio eficaz y sin perjuicio (18 casos: VO01-VO06,
     VO08-VO17, VO20, RE04). Se desglosan los dos juicios: el medio es idoneo,
     oportuno y accesible; y ninguno de los cuatro elementos del perjuicio
     concurre. Son cobros, controversias contractuales y actos administrativos
     con proceso propio, y varios lo dicen en el relato --- VO15 dice "la
     mesada me alcanza, vivo bien".

  B. `continua_vulneracion` (5 casos: VO07, VO18, VO19, RE01, RE02). **NO se
     desglosan.** Ese campo pregunta un hecho del mundo --- si la accion u
     omision subsiste --- y no tiene test doctrinal de elementos. Los cinco
     relatos lo responden directamente: ya la operaron de nuevo, el semestre
     se perdio en 2024, el local ya no existe. Se quedan en `juicio`, igual
     que A01, A07 y A12 del eval set, y por la misma razon: no se
     reclasifican para mejorar un conteo.

  C. La excepcion del art. 6.3 (TU25, TU26). Pivotan en
     `perjuicio_irremediable` Y en `titular_pide_lo_suyo`. El primero SI se
     desglosa, y al derivarlo el pivote se MUEVE al segundo --- que tampoco
     tiene test de elementos y que los dos relatos responden con esas
     palabras: "mi caso es distinto: yo soy paciente renal", "lo mio es que mi
     hijo de cuatro anos tiene asma severa". Asi que los dos siguen en
     `juicio` por otro campo, y quedan declarados igual que los de la familia
     B. El resultado honesto es 7 en `juicio`, no 5: el desglose no los saca,
     los mueve.

El desglose sigue el test de la T-225 de 1993, cuyo texto esta en el corpus
(`J-T225-93`) desde el ROADMAP #27: inminencia, gravedad, urgencia e
impostergabilidad, los cuatro CONCURRENTES. El motor re-deriva el booleano y
FALLA si el afirmado no se sigue del desglose.

Idempotente. Falla sin escribir si el motor no deriva alguna etiqueta.
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
# PARTE 1: los hechos de los 30 originales.
# Codificacion esparcida: solo lo que se desvia del default del dataclass.
# --------------------------------------------------------------------------
HECHOS = {
    # --- salud: no hay otro proceso judicial idoneo, entra por el art. 86 ---
    "T01": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "T02": {"afectacion_individual": True},
    "T03": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "T04": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "T05": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "T06": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "V01": {"afectacion_individual": True},
    "V07": {"afectacion_individual": True},

    # --- peticion: el mecanismo propio es la tutela (art. 23 CP) ---
    "T07": {"afectacion_individual": True},
    "T08": {"afectacion_individual": True},
    # T09 y V08 son contra PARTICULARES que prestan servicio publico: la
    # nulidad y restablecimiento no alcanza a un particular, luego no hay otro
    # medio judicial.
    "T09": {"afectacion_individual": True},
    "V02": {"afectacion_individual": True},
    "V08": {"afectacion_individual": True},

    # --- pensional ---
    # T10: 74 anos, sin ningun ingreso. Hay via laboral pero la salva el
    # perjuicio irremediable => tutela TRANSITORIA.
    "T10": {"afectacion_individual": True, "otro_medio_judicial": True,
            "perjuicio_irremediable": True, "sujeto_especial_proteccion": True},
    # T11 es el contraste deliberado: 55 anos, trabajando, la diferencia son
    # 200 mil pesos. Mismo campo juridico, resultado opuesto.
    "T11": {"otro_medio_judicial": True},

    # --- habeas data: no hay otro proceso judicial, art. 15 CP ---
    "T12": {"afectacion_individual": True},
    "T13": {"afectacion_individual": True},
    "V03": {"afectacion_individual": True},

    # --- estabilidad laboral reforzada: hay via laboral pero NO es oportuna ---
    "T14": {"afectacion_individual": True, "otro_medio_judicial": True,
            "medio_eficaz": False, "sujeto_especial_proteccion": True},
    "T15": {"afectacion_individual": True, "otro_medio_judicial": True,
            "medio_eficaz": False, "sujeto_especial_proteccion": True},
    "V06": {"afectacion_individual": True, "otro_medio_judicial": True,
            "medio_eficaz": False, "sujeto_especial_proteccion": True},

    # --- educacion y debido proceso ---
    "T16": {"afectacion_individual": True, "sujeto_especial_proteccion": True},
    "T17": {"afectacion_individual": True, "sujeto_especial_proteccion": True},

    # --- art. 6.3: derechos colectivos (art. 4 Ley 472) ---
    "T18": {"derecho_colectivo": True},
    "V05": {"derecho_colectivo": True},
    "V09": {"derecho_colectivo": True},

    # --- art. 9 Ley 393: cumplimiento sin afectacion individual concreta ---
    "T19": {"incumplimiento_normativo": True},

    # --- art. 6.2: libertad personal ---
    "T20": {"privacion_libertad": True, "afectacion_individual": True},

    # --- art. 6.1: subsidiariedad, el otro medio es eficaz en concreto ---
    "V04": {"otro_medio_judicial": True},
    "V10": {"otro_medio_judicial": True},
}

# --------------------------------------------------------------------------
# PARTE 2: el desglose de los dos juicios.
# --------------------------------------------------------------------------
PI = ("pi_inminencia", "pi_gravedad", "pi_urgencia", "pi_impostergabilidad")
ME = ("me_idoneo", "me_oportuno", "me_accesible")


def _pi(i, g, u, p):
    return dict(zip(PI, (i, g, u, p)))


def _me(i, o, a):
    return dict(zip(ME, (i, o, a)))


# El medio ordinario sirve, llega a tiempo y la persona puede usarlo; y
# ninguno de los cuatro elementos del perjuicio concurre. Es la forma de todos
# los casos de la familia A: cobros, controversias contractuales y actos
# administrativos con proceso propio.
VIA_ORDINARIA_LIMPIA = {**_me(True, True, True), **_pi(False, False, False, False)}

DESGLOSE = {
    # --- familia A: 18 casos de via ordinaria, forma uniforme ---
    **{i: dict(VIA_ORDINARIA_LIMPIA) for i in (
        "VO01", "VO02", "VO03", "VO04", "VO05", "VO06", "VO08", "VO09",
        "VO10", "VO11", "VO12", "VO13", "VO14", "VO15", "VO16", "VO17",
        "VO20", "RE04")},

    # --- los tres de via ordinaria entre los 30 originales ---
    "T11": dict(VIA_ORDINARIA_LIMPIA),
    "V04": dict(VIA_ORDINARIA_LIMPIA),
    "V10": dict(VIA_ORDINARIA_LIMPIA),

    # --- pensional: los cuatro elementos concurren ---
    # 74 anos, sin ningun ingreso, sosteniendose de lo que le dan los vecinos.
    "T10": _pi(True, True, True, True),

    # --- estabilidad laboral: el medio es idoneo pero NO oportuno ---
    # Perder el empleo es perder la afiliacion, y el fuero cubre un periodo
    # acotado que un proceso ordinario desborda.
    "T14": _me(True, False, True),
    "T15": _me(True, False, True),
    "V06": _me(True, False, True),

    # --- familia C: la excepcion del art. 6.3 ---
    # TU25: paciente renal que hace dialisis en casa con agua sin tratar.
    # TU26: nino de cuatro anos con asma severa y tres hospitalizaciones.
    # En los dos el bien en riesgo es la vida y esperar la accion popular
    # haria inutil la proteccion.
    "TU25": _pi(True, True, True, True),
    "TU26": _pi(True, True, True, True),
}

# --------------------------------------------------------------------------
# Lo que NO se desglosa, y por que. Va al meta para que el hueco quede
# declarado y no solo pendiente.
# --------------------------------------------------------------------------
SIN_DESGLOSAR = {
    "continua_vulneracion": {
        "casos": ["VO07", "VO18", "VO19", "RE01", "RE02"],
        "por_que":
            "Ese campo pregunta un hecho del mundo --- si la accion u omision "
            "que vulnera el derecho subsiste --- y no tiene un test doctrinal "
            "de elementos como el perjuicio irremediable (T-225 de 1993) o la "
            "eficacia del otro medio (art. 6.1). Los cinco relatos lo "
            "responden directamente: a la esposa ya la operaron de nuevo y "
            "esta estable, el semestre se perdio en 2024 y la carrera ya "
            "termino, el local ya no existe y el solicitante se reubico.",
    },
    "continua_vulneracion_casos_reales": {
        "casos": ["RE06"],
        "por_que":
            "Mismo campo y misma razon que VO07/VO18/VO19/RE01/RE02, pero el "
            "caso lo escribe `data/casos_reales.py`, no este script. Es la "
            "Sentencia T-002 de 2024: la Corte declaro la carencia actual de "
            "objeto porque la EPS autorizo durante el tramite, y eso el relato "
            "lo dice directamente.",
    },
    "titular_pide_lo_suyo": {
        "casos": ["TU25", "TU26"],
        "por_que":
            "Estos dos pivotaban en `perjuicio_irremediable` ANTES del "
            "desglose; al derivarlo, el pivote se movio al otro juicio de la "
            "excepcion del art. 6.3. Tampoco tiene test de elementos: "
            "pregunta si el solicitante reclama la afectacion concreta de SU "
            "propio derecho, y los dos relatos lo dicen con esas palabras --- "
            "'mi caso es distinto: yo soy paciente renal', 'lo mio es que mi "
            "hijo de cuatro anos tiene asma severa'.",
    },
    "criterio": "NO se reclasifican a `plano` para mejorar el conteo. Siguen "
                "contando como el punto debil, igual que A01, A07 y A12 del "
                "eval set, y por la misma razon.",
}



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
    casos = d["ejemplos"]
    por_id = {c["id"]: c for c in casos}

    faltan = HECHOS.keys() - por_id.keys()
    if faltan:
        print(f"FALLA: ids que no existen: {sorted(faltan)}")
        return 1
    faltan = DESGLOSE.keys() - por_id.keys()
    if faltan:
        print(f"FALLA: desglose de ids que no existen: {sorted(faltan)}")
        return 1

    errores: list[str] = []
    for c in casos:
        if c.get("tipo") == "abstencion":
            continue
        base = HECHOS.get(c["id"], c.get("hechos"))
        if base is None:
            errores.append(f"{c['id']}: sin hechos y sin codificar")
            continue
        # El desglose NO sobreescribe los hechos: los completa.
        #
        # Y solo se reconstruye para los casos que este script POSEE. Quitar
        # los `pi_`/`me_` de todos y reponerlos solo desde `DESGLOSE` borraba
        # el desglose de los casos que escriben otros scripts --- RE08, CT07,
        # CT08, CT09, CT12 y CT13 volvian a `juicio` cada vez que este corria
        # despues de `casos_reales.py` o `ampliar_categorias.py`. Lo cazo el
        # guardia de consistencia del final: declaraba 7 sin desglosar y habia
        # 14 en `juicio`.
        mio = c["id"] in HECHOS or c["id"] in DESGLOSE
        if mio:
            h = {k: v for k, v in base.items()
                 if not k.startswith(("pi_", "me_"))}
            h.update(DESGLOSE.get(c["id"], {}))
        else:
            h = dict(base)
        try:
            dec = decidir(Hechos(**h))
        except (TypeError, ValueError) as ex:
            errores.append(f"{c['id']}: hechos invalidos -> {ex}")
            continue
        if dec.mecanismo != c["mecanismo"]:
            errores.append(
                f"{c['id']} ({c['categoria']}): etiqueta={c['mecanismo']} pero "
                f"el motor deriva {dec.mecanismo} (regla: {dec.regla})")
            continue
        if dec.procede_tutela != c["procede"]:
            errores.append(f"{c['id']}: procede={c['procede']} pero el motor "
                           f"deriva {dec.procede_tutela}")
            continue
        # Orden determinista. Sin esto el script no es idempotente: en la
        # segunda corrida `base` sale del JSON ya escrito, con su propio orden
        # de claves, y el archivo cambia aunque el contenido sea el mismo.
        c["hechos"] = {k: h[k] for k in sorted(h)}
        c["verificado_con_reglas"] = True
        c["regla_que_cierra"] = dec.regla
        est, campos = estrato_verificacion(Hechos(**h))
        c["estrato_verificacion"] = est
        c["etiqueta_pivota_en"] = campos

    if errores:
        print(f"FALLA: el motor no deriva la etiqueta en {len(errores)} casos.")
        print("No se escribio nada.\n")
        for e in errores:
            print(f"  - {e}")
        return 1

    con = [c for c in casos if c.get("hechos")]
    estratos = Counter(c["estrato_verificacion"] for c in con)
    subir_version(d["meta"], "3.3.0")
    d["meta"]["verificacion_de_hechos"] = {
        "casos_con_hechos": len(con),
        "casos_totales": len(casos),
        "abstencion_sin_hechos": sum(1 for c in casos
                                     if c.get("tipo") == "abstencion"),
        # Propiedades del ARTEFACTO, no de la ejecucion. Contar "cuantos
        # cambiaron en esta corrida" daba 30 la primera vez y 0 la segunda, y
        # eso rompia la idempotencia del script.
        "codificados_por_este_script": len(HECHOS),
        "con_desglose_de_juicios": len(DESGLOSE),
        "estratos": dict(estratos),
        "que_prueba": "que cada etiqueta es EXPRESABLE en el arbol del art. 6: "
                      "existe una codificacion de hechos leida del relato de la "
                      "que el motor deriva ese mecanismo.",
        "que_no_prueba": "que la etiqueta sea CORRECTA. Quien codifico los "
                         "hechos conocia la etiqueta, asi que donde un hecho "
                         "admite dos valores defendibles la codificacion pudo "
                         "elegirse hacia atras. Por eso cada caso lleva "
                         "`estrato_verificacion`.",
        "desglose":
            "los juicios se desglosan con el test de la T-225 de 1993 "
            "(inminencia + gravedad + urgencia + impostergabilidad, los cuatro "
            "CONCURRENTES) y con la apreciacion en concreto del art. 6.1 "
            "(idoneidad + oportunidad + accesibilidad). El texto de la T-225 "
            "esta en el corpus como J-T225-93, asi que la cita es verificable. "
            "El motor re-deriva el booleano y falla si el afirmado no se sigue.",
        "sin_desglosar": SIN_DESGLOSAR,
    }
    ruta.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                    encoding="utf-8")

    print(f"OK: dataset v3.3.0")
    print(f"  {len(con)}/{len(casos)} casos con hechos verificados por el motor")
    print(f"  codificados por este script : {len(HECHOS)}  (los originales)")
    print(f"  con desglose de juicios     : {len(DESGLOSE)}")
    print(f"\nestrato de verificacion:")
    for e in ("plano", "derivado", "juicio"):
        print(f"  {e:10s} {estratos[e]}")
    print("\nsin desglosar a proposito, por campo:")
    total_sin = 0
    for campo, info in SIN_DESGLOSAR.items():
        if not isinstance(info, dict):
            continue
        total_sin += len(info["casos"])
        print(f"  {campo:24s} {info['casos']}")
    # Si la documentacion y los datos no cuadran, se dice. Paso de verdad: el
    # desglose movio el pivote de TU25 y TU26 de `perjuicio_irremediable` a
    # `titular_pide_lo_suyo`, y la lista decia 5 cuando los datos daban 7.
    if total_sin != estratos["juicio"]:
        print(f"\n  ATENCION: la lista declara {total_sin} casos sin desglosar "
              f"pero hay {estratos['juicio']} en `juicio`. Revisa "
              f"SIN_DESGLOSAR.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
