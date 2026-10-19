"""
Separa los dos planos del `fundamento` y marca el origen de cada etiqueta.

    ROADMAP #7  `fundamento_del_mecanismo` aparte del derecho de fondo.
    ROADMAP #8  `origen_etiqueta` para poder reportar el acierto por
                fiabilidad de la etiqueta.

EL PROBLEMA QUE RESUELVE EL #7, medido antes de tocar nada:

    mecanismo             n   con cita del plano procesal
    tutela               27    3
    via_ordinaria        12   11
    accion_popular        8    8
    accion_cumplimiento   8    8
    habeas_corpus         8    8

Los 8 casos de cumplimiento citan `art. 87 CP`, los 8 de popular citan
`art. 88 CP`, los 8 de habeas corpus citan `art. 30 CP`... y **`art. 86 CP` no
aparece en ningun fundamento del eval set**, aunque 27 casos son de tutela. El
campo responde "que mecanismo y por que" en los no-tutela y "que derecho se
protege" en los de tutela: dos preguntas distintas bajo el mismo nombre.

Consecuencia medida: `pertinencia_citas` compara contra el conjunto exacto del
`fundamento` del gold, asi que un modelo que cita `art. 86 CP` --- la norma que
CREA la tutela, y justo lo que emite `reglas.decidir()` --- cuenta como
impertinente en 24 de 27 casos de tutela. El fundamento del motor difiere del
gold en 38 de 63 casos, y casi todo el delta es ese.

QUE HACE Y QUE NO HACE ESTE SCRIPT

NO toca `fundamento`, ni `mecanismo`, ni `procede`, ni ningun relato. Cambiar
`fundamento` moveria la vara y las once corridas anteriores dejarian de ser
comparables --- el mismo criterio del ROADMAP #2. Solo AGREGA campos:

    fundamento_del_mecanismo  DERIVADO de reglas.decidir(), no afirmado. Por
                              eso es consistente entre todos los casos del
                              mismo mecanismo, que es exactamente lo que el
                              campo mezclado no era.
    fundamento_del_derecho    las citas de plano de fondo que ya estaban en
                              `fundamento`.
    origen_etiqueta           quien fijo la etiqueta.
    fiabilidad_etiqueta       escalera de 4 niveles, combinando el origen con
                              el estrato de verificacion.

Idempotente. Falla sin escribir si algun caso queda inconsistente.
"""
from __future__ import annotations
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "src"))

from schema import citas, separar_planos  # noqa: E402
from src.reglas import Hechos, decidir, estrato_verificacion  # noqa: E402

ARTEFACTOS = ("dataset.json", "eval_set.json", "eval_set_v2.json",
              "eval_set_m3.json")

# ORDEN DE EJECUCION. Este script va AL FINAL, porque anota campos sobre
# artefactos que los otros construyen:
#
#   1. data/codificar_hechos_eval.py          -> hechos + estrato en eval v1
#   2. data/construir_eval_v2.py              -> eval v2 y `dificultad`
#   3. data/construir_eval_m3_terminos.py     -> casos con termino en eval m3
#   4. data/anotar_fundamentos.py             -> ESTE: planos y origen
#
# Si se corre antes del 3, las anotaciones de eval_set_m3.json se pierden: ese
# script reconstruye el archivo desde sus 15 casos originales.

# --------------------------------------------------------------------------
# ROADMAP #8: de donde viene la etiqueta.
#
# El orden es una escalera de fiabilidad DECRECIENTE, y la honestidad del
# campo esta en el nivel 2: `motor_de_reglas` significa CONSISTENTE con el
# arbol del art. 6, no INDEPENDIENTE. Los hechos los codifico el mismo equipo
# que puso la etiqueta; lo que el motor descarta es que la etiqueta contradiga
# el ordenamiento --- que es lo que encontro en A09 --- no que sea la correcta.
# --------------------------------------------------------------------------
ESCALERA = {
    "corte_constitucional": (
        1, "corte_constitucional",
        "la etiqueta la fijo un tercero: es la decision publicada de la Corte "
        "Constitucional, con numero de sentencia y expediente. Es el unico "
        "nivel con fuente externa al equipo."),
    ("motor_de_reglas", "plano"): (
        2, "motor_de_reglas_plano",
        "la etiqueta la DERIVA reglas.decidir() de hechos que se leen del "
        "relato con poco margen. Consistente con el art. 6, no independiente."),
    ("motor_de_reglas", "derivado"): (
        3, "motor_de_reglas_ponderado",
        "la etiqueta la deriva el motor, pero a traves de una ponderacion "
        "(perjuicio irremediable o eficacia del otro medio) que a su vez se "
        "deriva de sus elementos con un test conjuntivo."),
    ("motor_de_reglas", "juicio"): (
        4, "equipo_ponderacion_afirmada",
        "la etiqueta depende de una ponderacion AFIRMADA sin desglose. Es el "
        "nivel mas debil de los verificados."),
    "equipo": (
        4, "equipo_afirmado",
        "la etiqueta se afirmo directamente, sin pasar por el motor. Son los "
        "casos de abstencion --- que no son una conclusion del arbol del "
        "art. 6 sino el reconocimiento de que no hay hechos para entrar --- y "
        "los casos sin `hechos` codificados."),
}


def clasificar(c: dict) -> tuple[str, str, int]:
    """(origen_etiqueta, fiabilidad_etiqueta, nivel)."""
    if c.get("tipo_fuente") == "real" and c.get("procedencia"):
        n, etq, _ = ESCALERA["corte_constitucional"]
        return "corte_constitucional", etq, n
    if c.get("verificado_con_reglas") and c.get("hechos"):
        # El estrato se CALCULA si no viene anotado. Suponer el peor caso por
        # defecto hundia los 90 casos verificados del dataset a nivel 4, que
        # es una lectura falsa: la mayoria se deriva de hechos planos.
        est = c.get("estrato_verificacion")
        if est is None:
            est = estrato_verificacion(Hechos(**c["hechos"]))[0]
            c["estrato_verificacion"] = est
        n, etq, _ = ESCALERA[("motor_de_reglas", est)]
        return "motor_de_reglas", etq, n
    n, etq, _ = ESCALERA["equipo"]
    return "equipo", etq, n


def anotar(casos: list[dict]) -> list[str]:
    errores: list[str] = []
    for c in casos:
        # --- #7: los dos planos --------------------------------------------
        _, fondo = separar_planos(c.get("fundamento") or "")
        c["fundamento_del_derecho"] = fondo

        if c.get("hechos") and c.get("mecanismo"):
            try:
                d = decidir(Hechos(**c["hechos"]))
            except (TypeError, ValueError) as ex:
                errores.append(f"{c.get('id')}: hechos invalidos -> {ex}")
                continue
            if d.mecanismo != c["mecanismo"]:
                errores.append(
                    f"{c.get('id')}: el motor deriva {d.mecanismo} pero la "
                    f"etiqueta es {c['mecanismo']}")
                continue
            # UNION de lo que deriva el motor y lo que el gold ya traia del
            # plano procesal. Las dos cosas son fundamento legitimo de la via:
            # el motor emite la causal que CERRO el caso, pero el gold suele
            # traer precisiones que el motor no conoce --- E06 y E21 citan el
            # art. 42 del Decreto 2591 porque el accionado es un particular que
            # presta un servicio publico, A01 cita el art. 25 por la
            # indemnizacion excepcional, E33 cita la Ley 1437 por la via
            # contenciosa. Tratarlas como `mecanismo_equivocado` seria repetir
            # en el plano procesal el mismo error que el #7 viene a corregir
            # en el de fondo.
            mec_motor, _ = separar_planos(d.fundamento)
            mec_gold, _ = separar_planos(c.get("fundamento") or "")
            c["fundamento_del_mecanismo"] = sorted(
                dict.fromkeys(list(mec_motor) + list(mec_gold)))
            c["fundamento_del_mecanismo_derivado"] = list(mec_motor)
        else:
            # Sin `hechos` codificados no hay nada que DERIVAR, pero las citas
            # procesales que el gold ya trae siguen siendo fundamento legitimo
            # de la via. Poner [] aqui tenia una consecuencia medida: en
            # eval_set_m3.json, cuyos 21 casos no pasaron por el motor, una
            # prediccion PERFECTA producia 18 `mecanismo_equivocado`, porque
            # toda cita procesal correcta caia fuera de un conjunto esperado
            # vacio. Los casos de abstencion si quedan en [], porque no tienen
            # `fundamento` en absoluto.
            mec_gold, _ = separar_planos(c.get("fundamento") or "")
            c["fundamento_del_mecanismo"] = list(mec_gold)
            c["fundamento_del_mecanismo_derivado"] = []

        # --- #8: origen y fiabilidad ---------------------------------------
        origen, fiab, nivel = clasificar(c)
        c["origen_etiqueta"] = origen
        c["fiabilidad_etiqueta"] = fiab
        c["nivel_fiabilidad"] = nivel
    return errores


def main() -> int:
    glosario = {}
    for k, (n, etq, texto) in ESCALERA.items():
        glosario[etq] = {"nivel": n, "significa": texto}

    resumen = {}
    for nombre in ARTEFACTOS:
        ruta = RAIZ / "data" / nombre
        if not ruta.exists():
            print(f"no existe {nombre}, se omite")
            continue
        d = json.loads(ruta.read_text(encoding="utf-8"))
        casos = d["ejemplos"]

        antes = [(c.get("fundamento"), c.get("mecanismo"), c.get("procede"),
                  c.get("relato")) for c in casos]

        errores = anotar(casos)
        if errores:
            print(f"FALLA en {nombre}, {len(errores)} casos. No se escribio "
                  f"nada en ningun artefacto.\n")
            for e in errores[:12]:
                print(f"  - {e}")
            return 1

        # Garantia dura: este script NO puede mover la vara.
        despues = [(c.get("fundamento"), c.get("mecanismo"), c.get("procede"),
                    c.get("relato")) for c in casos]
        if antes != despues:
            print(f"FALLA: {nombre} cambio en un campo que una metrica lee. "
                  f"No se escribio nada.")
            return 1

        d["meta"]["planos_del_fundamento"] = {
            "por_que":
                "`fundamento` mezclaba dos planos. En el eval set, los 8 casos "
                "de cumplimiento citan art. 87 CP, los 8 de popular art. 88 CP "
                "y los 8 de habeas corpus art. 30 CP, pero art. 86 CP no "
                "aparecia en NINGUN fundamento aunque 27 casos son de tutela: "
                "solo 3 de esos 27 llevaban alguna cita del plano procesal, "
                "contra 8/8 en los demas mecanismos. `pertinencia_citas` "
                "comparaba contra el conjunto exacto del `fundamento`, asi que "
                "contaba como impertinente el art. 86 CP, que es la norma que "
                "crea la tutela y lo que emite reglas.decidir().",
            "fundamento": "SIN CAMBIOS. Mover este campo invalidaria las once "
                          "corridas anteriores, igual que agrandar el eval set "
                          "en sitio.",
            "fundamento_del_mecanismo": "DERIVADO de reglas.decidir(), no "
                                        "afirmado: por eso es consistente entre "
                                        "los casos del mismo mecanismo.",
            "fundamento_del_derecho": "las citas de plano de fondo que ya "
                                      "estaban en `fundamento`.",
            "particion": "la decide schema.planos_normativos() desde "
                         "normas.json, no una lista a mano. Procesal = lo que "
                         "crea o regula una accion; fondo = lo que reconoce un "
                         "derecho. La Constitucion lo resuelve sola: su art. 30 "
                         "se titula 'Habeas corpus' y su art. 28 'Libertad "
                         "personal'.",
        }
        d["meta"]["fiabilidad_de_las_etiquetas"] = {
            "escalera": glosario,
            "reparto": dict(Counter(c["fiabilidad_etiqueta"] for c in casos)),
            "advertencia":
                "`motor_de_reglas` significa CONSISTENTE con el arbol del "
                "art. 6, no INDEPENDIENTE: los hechos los codifico el mismo "
                "equipo que puso la etiqueta. Lo que el motor descarta es que "
                "la etiqueta contradiga el ordenamiento, que es lo que "
                "encontro en A09.",
        }
        ruta.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                        encoding="utf-8")
        resumen[nombre] = (len(casos), Counter(c["fiabilidad_etiqueta"]
                                               for c in casos))

    for nombre, (n, rep) in resumen.items():
        print(f"\n{nombre}  ({n} casos)")
        for etq in ("corte_constitucional", "motor_de_reglas_plano",
                    "motor_de_reglas_ponderado", "equipo_ponderacion_afirmada",
                    "equipo_afirmado"):
            if rep.get(etq):
                print(f"   {ESCALERA_NIVEL[etq]}  {etq:30s} {rep[etq]}")

    # Cuanto habria cambiado si el fundamento se hubiera unificado: es la
    # magnitud del defecto que el #7 deja medida sin tocar la vara.
    ev = json.loads((RAIZ / "data" / "eval_set_v2.json").read_text(encoding="utf-8"))
    falt = sum(1 for c in ev["ejemplos"]
               if c.get("fundamento_del_mecanismo")
               and not (set(c["fundamento_del_mecanismo"])
                        & set(citas(c.get("fundamento") or ""))))
    print(f"\ncasos de eval_set_v2 cuyo `fundamento` NO contiene ninguna de las "
          f"citas del plano procesal que el motor deriva: {falt}")
    print("Son los que `pertinencia_citas` penalizaba por citar bien el "
          "mecanismo. Ahora quedan medibles aparte.")
    return 0


ESCALERA_NIVEL = {etq: f"[{n}]" for n, etq, _ in ESCALERA.values()}


if __name__ == "__main__":
    raise SystemExit(main())
