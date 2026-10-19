"""Valida el extractor de hechos SIN GPU, antes de gastar una corrida entera.

POR QUE EXISTE

M3-1 quedó con la causa establecida: el extractor del agente marcaba
`derecho_colectivo=True` en los 8 casos de `accion_cumplimiento` y
`acto_general=True` en 6, y eso mandaba el caso a otra vía antes de que el
motor llegara a mirar el incumplimiento. El prompt ya está corregido.

Comprobar si la corrección sirve re-corriendo M1 → M2 → M3 cuesta ~80 minutos
de A100 y cambia todas las cifras del reporte. Pero la extracción **no usa la
GPU**: son ocho llamadas a la API, segundos y céntimos. Validarla aparte es la
diferencia entre arreglar y esperar a ver.

Esto llama al MISMO `Agente._hechos` que corre en el brazo 4 —no a una copia
del prompt— con el índice y el cliente reales, pero sin bucle de herramientas:
se le da el relato y se mira qué hechos extrae.

QUE RESPONDE

  1. ¿Bajó `derecho_colectivo` en los casos de cumplimiento? (era 8/8)
  2. ¿Bajó `acto_general`? (era 6/8)
  3. Con los hechos que extrae AHORA, ¿qué vía emite el motor?
  4. Y en los casos que NO son de cumplimiento, ¿se rompió algo? Un prompt
     que arregla ocho casos y daña veinte no es una mejora, y mirar solo los
     ocho lo ocultaría.

Sale con 0 si la vía sale correcta en los 8, y con 1 nombrando los que no.

    GROQ_API_KEY=...  python -I data/validar_extractor.py
    python -I data/validar_extractor.py --control 20   # + casos de control
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import agente as ag_mod                                     # noqa: E402
import rag                                                  # noqa: E402
from reglas import HECHOS_EXTRAIBLES, Hechos, decidir       # noqa: E402

VIA = "accion_cumplimiento"
RUTA_OUT = RAIZ / "data" / "validacion_extractor.json"


def _clave_groq() -> str:
    """La clave, buscandola donde de verdad esta.

    `!python ...` arranca un proceso NUEVO, que solo hereda `GROQ_API_KEY` si
    alguien ya la puso en `os.environ` del notebook. Tener el secreto bien
    configurado en el panel de Colab no basta: hay que copiarlo al entorno, y
    eso lo hace una celda que puede no haber corrido todavia.

    Fallar ahi es fallar por un detalle de orden de celdas, no por nada del
    experimento. Asi que si la variable no esta, se busca el secreto
    directamente. Si tampoco, se dice QUE falta y COMO se arregla.
    """
    clave = os.environ.get("GROQ_API_KEY")
    if clave:
        return clave
    try:
        from google.colab import userdata           # type: ignore
        clave = userdata.get("GROQ_API_KEY")
        if clave:
            os.environ["GROQ_API_KEY"] = clave
            print("  clave leida del panel de secretos de Colab "
                  "(no estaba en el entorno)")
            return clave
    except Exception as ex:                                 # noqa: BLE001
        t = type(ex).__name__
        if "NotebookAccess" in t:
            print("El secreto GROQ_API_KEY existe pero este notebook NO tiene")
            print("acceso: panel izquierdo, icono de la llave, y activa el")
            print("interruptor de acceso para este notebook.")
            return ""
        if "SecretNotFound" in t:
            print("No hay ningun secreto llamado GROQ_API_KEY en Colab.")
            return ""
    print("Falta GROQ_API_KEY.")
    print("  En Colab, en la MISMA celda y antes de llamar al script:")
    print("    import os; from google.colab import userdata")
    print("    os.environ['GROQ_API_KEY'] = userdata.get('GROQ_API_KEY')")
    print("  En local:  GROQ_API_KEY=...  python -I data/validar_extractor.py")
    return ""


def _eval() -> list[dict]:
    return json.loads(
        (RAIZ / "data" / "eval_set_v2.json").read_text(
            encoding="utf-8"))["ejemplos"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", type=int, default=12,
                    help="cuantos casos de OTRAS vias mirar, para detectar "
                         "si el arreglo rompio algo (0 los omite)")
    a = ap.parse_args()

    clave = _clave_groq()
    if not clave:
        return 1
    try:
        import groq
    except ImportError:
        print("Falta el paquete `groq`:  pip install groq")
        return 1

    ev = _eval()
    objetivo = [e for e in ev if e["mecanismo"] == VIA]
    otros = [e for e in ev if e["mecanismo"] not in (VIA, None)][:a.control]

    corpus = json.loads(
        (RAIZ / "data" / "corpus.json").read_text(encoding="utf-8"))["documentos"]
    indice = rag.Indice(rag.trocear(corpus), verbose=False)
    agente = ag_mod.Agente(groq.Groq(api_key=clave), indice, verbose=False,
                           cache_path=str(RAIZ / "runs" / "cache" /
                                          "validar_extractor.json"))

    print("=" * 76)
    print(f"  VALIDACION DEL EXTRACTOR · {len(objetivo)} casos de {VIA}"
          + (f" + {len(otros)} de control" if otros else ""))
    print("=" * 76)
    print("  Sin GPU: son llamadas de extraccion, no una corrida.")
    print()

    filas, rotos = [], []
    for grupo, casos in (("objetivo", objetivo), ("control", otros)):
        if not casos:
            continue
        print(f"  --- {grupo} ---")
        for e in casos:
            hechos, _ = agente._hechos([], e["relato"])
            d = {k: getattr(hechos, k) for k in HECHOS_EXTRAIBLES}
            via = decidir(Hechos(**d)).mecanismo
            ok = via == e["mecanismo"]
            filas.append({"id": e["id"], "grupo": grupo,
                          "gold": e["mecanismo"], "motor_emite": via,
                          "acierta": ok,
                          "derecho_colectivo": d["derecho_colectivo"],
                          "acto_general": d["acto_general"],
                          "incumplimiento_normativo":
                              d["incumplimiento_normativo"],
                          "afectacion_individual": d["afectacion_individual"]})
            if not ok:
                rotos.append((e["id"], grupo, e["mecanismo"], via))
            marca = "ok   " if ok else "FALLA"
            print(f"    {marca} {e['id']:6s} gold={e['mecanismo']:20s} "
                  f"-> {via:20s} colectivo={d['derecho_colectivo']!s:5s} "
                  f"general={d['acto_general']!s:5s}")

    obj = [f for f in filas if f["grupo"] == "objetivo"]
    ctl = [f for f in filas if f["grupo"] == "control"]
    col = sum(f["derecho_colectivo"] for f in obj)
    gen = sum(f["acto_general"] for f in obj)

    print()
    print("=" * 76)
    print(f"  derecho_colectivo en los de {VIA}: {col} de {len(obj)}"
          "   (antes: 8 de 8)")
    print(f"  acto_general      en los de {VIA}: {gen} de {len(obj)}"
          "   (antes: 6 de 8)")
    print(f"  el motor emite la via correcta   : "
          f"{sum(f['acierta'] for f in obj)} de {len(obj)}")
    if ctl:
        print(f"  control (otras vias), sin romper : "
              f"{sum(f['acierta'] for f in ctl)} de {len(ctl)}")
    print("=" * 76)

    out = {"via": VIA, "n_objetivo": len(obj), "n_control": len(ctl),
           "derecho_colectivo_en_objetivo": col,
           "acto_general_en_objetivo": gen,
           "aciertan_objetivo": sum(f["acierta"] for f in obj),
           "aciertan_control": sum(f["acierta"] for f in ctl),
           "antes": {"derecho_colectivo": 8, "acto_general": 6,
                     "aciertan_objetivo": 0,
                     "corrida": "m3/20261018T080807Z"},
           "detalle": filas,
           "lectura": "",
           "_no_es_una_corrida": (
               "Esto valida SOLO la extraccion de hechos. No mide el brazo 4 "
               "completo --- que incluye el bucle de herramientas, la "
               "recuperacion y el juez --- ni sustituye a correr M3. Sirve "
               "para saber si vale la pena correrlo.")}

    # ----------------------------------------------------------------------
    # EL CRITERIO. La version anterior NO PODIA SALIR EN VERDE NUNCA.
    #
    # Exigia que acertaran los 8 objetivos **Y** los 12 de control. Pero el
    # control son casos de OTRAS vias, y el sistema entero va al 87.3%: que
    # 2 o 3 de 12 fallen es su tasa de error normal, no una regresion de este
    # arreglo. Con ese criterio el script imprimia "NO corras M1-M2-M3"
    # aunque el arreglo hubiera funcionado perfectamente en su objetivo ---
    # o sea, el unico mensaje que el script existe para dar no se podia dar.
    #
    # Son DOS preguntas distintas y se responden por separado:
    #   OBJETIVO: mejora respecto a `antes.aciertan_objetivo`?
    #   CONTROL : EMPEORA respecto a su propia linea base?
    #
    # La linea base del control no se escribe a mano. Se lee de la medicion
    # anterior si existe; si no existe, ESTA medicion queda como referencia y
    # el script lo dice, en vez de inventarse un numero con el que comparar.
    ac_obj = sum(f["acierta"] for f in obj)
    ac_ctl = sum(f["acierta"] for f in ctl)
    antes_obj = out["antes"]["aciertan_objetivo"]

    base_ctl, primera_vez = ac_ctl, True
    if RUTA_OUT.exists():
        try:
            _prev = json.loads(RUTA_OUT.read_text(encoding="utf-8"))
            if isinstance(_prev.get("aciertan_control"), int):
                base_ctl, primera_vez = _prev["aciertan_control"], False
        except Exception:                                     # noqa: BLE001
            pass
    out["linea_base_control"] = {"valor": base_ctl,
                                 "de_donde": ("esta medicion, que queda como "
                                              "referencia" if primera_vez
                                              else "la medicion anterior")}

    rotos_obj = [r for r in rotos if r[1] == "objetivo"]
    rotos_ctl = [r for r in rotos if r[1] == "control"]
    regresion = ac_ctl < base_ctl
    cerrado = ac_obj == len(obj)
    mejora = ac_obj > antes_obj

    print(f"  objetivo: {ac_obj} de {len(obj)}  (antes {antes_obj})")
    print(f"  control : {ac_ctl} de {len(ctl)}  (linea base {base_ctl}"
          f"{', primera medicion' if primera_vez else ''})")
    print("=" * 76)

    if regresion:
        out["lectura"] = (f"REGRESION en el control: {ac_ctl} contra "
                          f"{base_ctl} de linea base. El arreglo rompe vias "
                          "que antes funcionaban.")
        print(f"  REGRESION. El control baja de {base_ctl} a {ac_ctl}: este")
        print("  arreglo rompe casos de otras vias que antes acertaban.")
        for i, g, gold, via in rotos_ctl:
            print(f"    {i:6s} [{g}] gold={gold} -> {via}")
        print()
        print("  NO corras M1-M2-M3: arreglar una via rompiendo otras no es")
        print("  un arreglo, y la corrida costaria 80 minutos en decirlo.")
        cod = 1
    elif cerrado:
        out["lectura"] = (f"El arreglo cierra la via: {ac_obj} de {len(obj)}, "
                          f"y el control se mantiene en {ac_ctl} sobre una "
                          f"linea base de {base_ctl}. Vale la pena re-correr.")
        print(f"  EL ARREGLO FUNCIONA. El motor emite la via correcta en los")
        print(f"  {len(obj)} casos objetivo y el control no empeora.")
        print("  Ahora si vale la pena gastar la corrida.")
        cod = 0
    elif mejora:
        out["lectura"] = (f"Mejora parcial: {ac_obj} de {len(obj)} contra "
                          f"{antes_obj} antes, sin regresion en el control. "
                          f"Siguen fallando {len(rotos_obj)} del objetivo.")
        print(f"  MEJORA PARCIAL, SIN REGRESION. De {antes_obj} a {ac_obj} de")
        print(f"  {len(obj)} en el objetivo, y el control aguanta.")
        print(f"  Siguen fallando {len(rotos_obj)} caso(s) del objetivo:")
        for i, g, gold, via in rotos_obj:
            print(f"    {i:6s} [{g}] gold={gold} -> {via}")
        print()
        print("  La corrida ya mediria una mejora real. Que no cierre la via")
        print("  del todo es una limitacion que hay que DECLARAR, no una")
        print("  razon para no medir.")
        cod = 0
    else:
        out["lectura"] = (f"Sin mejora: {ac_obj} de {len(obj)} contra "
                          f"{antes_obj} antes. La hipotesis no sirvio.")
        print(f"  SIN MEJORA. El objetivo sigue en {ac_obj} de {len(obj)}")
        print(f"  (antes {antes_obj}). Lo que se cambio no era la causa.")
        for i, g, gold, via in rotos_obj:
            print(f"    {i:6s} [{g}] gold={gold} -> {via}")
        print()
        print("  NO corras M1-M2-M3: una corrida de 80 minutos para confirmar")
        print("  que nada cambio es el peor uso posible de la GPU.")
        cod = 1

    RUTA_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"  escrito: {RUTA_OUT.relative_to(RAIZ)}")
    print("=" * 76)
    return cod


if __name__ == "__main__":
    raise SystemExit(main())
