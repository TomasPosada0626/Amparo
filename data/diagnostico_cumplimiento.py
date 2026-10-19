"""Por qué el brazo del agente falla `accion_cumplimiento`, acotado a 5 causas.

ROADMAP3 · M3-1. Tras corregir `derecho_colectivo` y `acto_general` el F1 de esa
clase subio a **0.3636** en la corrida 20261019T034908Z: reducido, no cerrado.
Lo que sigue describe el estado en que se escribio este script. El brazo 4 daba **F1 0.000** en esa
vía mientras los brazos 1 y 3 dan 0.941. Las ocho categorías fallan una a una.
El brazo 4 es el único que usa el motor de reglas, así que la sospecha natural
era el motor.

LO QUE ESTE SCRIPT ESTABLECE SIN NECESIDAD DE UNA CORRIDA

1. **El motor no es el defecto.** Con los hechos que el eval set declara, el
   motor emite `accion_cumplimiento` en los **8 de 8** casos. Si recibe los
   hechos correctos, acierta.

2. **Sólo seis cosas pueden romperlo.** Partiendo de la combinación mínima
   —`incumplimiento_normativo=True` y `afectacion_individual=False`, que es el
   art. 9 de la Ley 393 de 1997 haciendo la acción de cumplimiento
   subsidiaria— se activa un hecho a la vez y se mira qué vía sale. La mayoría
   no cambia nada. Las que sí, son la lista cerrada de causas posibles.

   Eso convierte «no sabemos por qué falla» en «es una de estas seis, y se
   distinguen leyendo un archivo».

3. **Cuál de las seis fue**, en cuanto exista `agente_trazas.json`. El lector
   está escrito: cuando la corrida lo publique, `--trazas` dice para cada uno
   de los ocho casos qué hechos extrajo el agente y cuál de las seis causas
   se activó. No hay que acordarse de hacer el análisis: está hecho.

LO QUE NO ESTABLECE

Por qué el extractor pone ese hecho. Eso exige las trazas, y una hipótesis ya
se refutó: cambiar la redacción de `afectacion_individual` en los dos prompts
de extracción **cambió** la extracción —el `acc_derecho` del brazo 4 se movió
de 0.698 a 0.635— y **no** arregló la vía. Así que el prompt está descartado
como causa, no sustituido por otra.

    python -I data/diagnostico_cumplimiento.py
    python -I data/diagnostico_cumplimiento.py --trazas runs/m3/<id>/agente_trazas.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from reglas import HECHOS_EXTRAIBLES, Hechos, decidir          # noqa: E402

RUTA_OUT = RAIZ / "data" / "diagnostico_cumplimiento.json"
VIA = "accion_cumplimiento"

# El art. 9 de la Ley 393 de 1997 hace la acción de cumplimiento subsidiaria:
# si lo incumplido afecta un derecho fundamental del solicitante, el camino es
# la tutela. El motor lo codifica como estas dos condiciones a la vez.
MINIMA = {"incumplimiento_normativo": True, "afectacion_individual": False}


def _casos() -> list[dict]:
    ev = json.loads(
        (RAIZ / "data" / "eval_set_v2.json").read_text(encoding="utf-8"))
    return [e for e in ev["ejemplos"] if e["mecanismo"] == VIA]


def exonerar_motor() -> dict:
    """¿Emite el motor la vía con los hechos que el eval set declara?"""
    filas = []
    for e in _casos():
        h = e.get("hechos") or {}
        r = decidir(Hechos(**h))
        filas.append({"id": e["id"], "categoria": e.get("categoria"),
                      "hechos_declarados": h,
                      "motor_emite": r.mecanismo,
                      "acierta": r.mecanismo == VIA})
    return {"n": len(filas), "aciertan": sum(f["acierta"] for f in filas),
            "detalle": filas}


def causas_posibles() -> dict:
    """Qué UN solo hecho, añadido a la combinación mínima, rompe la vía.

    Sólo se prueban los hechos de `HECHOS_EXTRAIBLES`: son los que el
    extractor puede producir. El desglose del perjuicio irremediable
    (`pi_*`) no entra porque el motor lo exige completo o vacío, y activarlo a
    medias es un error de construcción, no un modo de fallo del extractor.
    """
    rompen, inocuos = [], []
    for f in HECHOS_EXTRAIBLES:
        if f in MINIMA:
            continue
        via = decidir(Hechos(**{**MINIMA, f: True})).mecanismo
        (rompen if via != VIA else inocuos).append(
            {"hecho": f, "via_que_sale": via})
    # Y las dos condiciones de la propia combinación mínima, al revés.
    for f, v in MINIMA.items():
        via = decidir(Hechos(**{**MINIMA, f: not v})).mecanismo
        if via != VIA:
            rompen.append({"hecho": f, "valor_que_rompe": not v,
                           "via_que_sale": via})
    return {"rompen": rompen, "inocuos": inocuos,
            "n_causas_posibles": len(rompen)}


def leer_trazas(ruta: Path) -> dict:
    """Cuál de las causas se activó, caso a caso. Exige las trazas.

    Las trazas las publica la corrida de M3. Mientras no existan, esto no
    devuelve nada: inferir qué extrajo el agente sin leerlo sería justo lo que
    este proyecto no hace.
    """
    if not ruta.exists():
        return {"disponible": False,
                "motivo": f"{ruta} no existe. Lo publica la corrida de M3; "
                          "hasta entonces, cuál de las causas fue queda sin "
                          "establecer."}
    tr = json.loads(ruta.read_text(encoding="utf-8"))
    if isinstance(tr, dict):
        tr = tr.get("datos") or tr.get("trazas") or list(tr.values())
    # LAS TRAZAS NO LLEVAN `id`, LLEVAN `relato`.
    #
    # `Agente.trazas` guarda lo que el agente ve --- relato, hechos,
    # herramientas, pasos --- y el id del caso no entra porque el agente no lo
    # recibe. Emparejar por `id` daba CERO casos con traza sobre un archivo de
    # 90 trazas correctas, y el diagnostico informaba "sin establecer" con la
    # evidencia delante.
    #
    # El `relato` es exacto: es la misma cadena que el eval set, no una
    # aproximacion.
    por_id = {}
    # Y el `relato` que guardan va TRUNCADO: 80 caracteres exactos, medido
    # sobre las 90 trazas de m3/20261018T080807Z. Comparar la cadena entera
    # no empalma ni un caso. Se empalma por prefijo, que ademas es unico: los
    # 90 prefijos de 80 chars son distintos entre si, asi que no hay riesgo de
    # atribuirle a un caso la traza de otro.
    por_relato = {t.get("relato"): t for t in tr
                  if isinstance(t, dict) and t.get("relato")}

    def _por_prefijo(relato):
        if not relato:
            return None
        hallados = [t for p, t in por_relato.items()
                    if p and relato.startswith(p)]
        # Si dos trazas comparten prefijo con el mismo caso, no se adivina.
        return hallados[0] if len(hallados) == 1 else None
    for t in tr:
        if isinstance(t, dict) and t.get("id"):
            por_id[t["id"]] = t

    causas = {c["hecho"] for c in causas_posibles()["rompen"]}
    filas, sin_traza = [], []
    for e in _casos():
        t = (por_id.get(e["id"]) or por_relato.get(e.get("relato"))
             or _por_prefijo(e.get("relato")))
        if not t:
            sin_traza.append(e["id"])
            continue
        h = t.get("hechos") or t.get("hechos_extraidos") or {}
        activas = [k for k in causas
                   if (h.get(k) is True and k != "afectacion_individual"
                       and k != "incumplimiento_normativo")
                   or (k == "afectacion_individual" and h.get(k) is True)
                   or (k == "incumplimiento_normativo" and h.get(k) is False)]
        via = decidir(Hechos(**{k: v for k, v in h.items()
                                if k in HECHOS_EXTRAIBLES})).mecanismo \
            if h else None
        filas.append({"id": e["id"], "categoria": e.get("categoria"),
                      "hechos_extraidos": h, "motor_emite": via,
                      "causas_activadas": sorted(activas)})
    conteo: dict[str, int] = {}
    for f in filas:
        for c in f["causas_activadas"]:
            conteo[c] = conteo.get(c, 0) + 1
    return {"disponible": True, "n_con_traza": len(filas),
            "sin_traza": sin_traza, "detalle": filas,
            "causa_mas_frecuente": (max(conteo, key=conteo.get)
                                    if conteo else None),
            "conteo_por_causa": dict(sorted(conteo.items(),
                                            key=lambda kv: -kv[1]))}


def _trazas_por_defecto() -> Path:
    """Donde buscarlas sin que haya que pasar la ruta.

    `publicar()` las deja en `results/m3_agente_trazas.json`. Antes de que se
    publicaran solo existian dentro de la carpeta de la corrida, y las
    corridas viejas siguen asi, de modo que se buscan los dos sitios --- el
    publicado primero, y entre corridas la mas reciente. Pedir la ruta a mano
    es la clase de friccion por la que un analisis no se hace.
    """
    pub = RAIZ / "results" / "m3_agente_trazas.json"
    if pub.exists():
        return pub
    viejas = sorted((RAIZ / "runs" / "m3").glob("*/agente_trazas.json"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    return viejas[0] if viejas else pub


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trazas", default="",
                    help="ruta a agente_trazas.json de una corrida de M3")
    a = ap.parse_args()

    mot = exonerar_motor()
    cau = causas_posibles()
    tz = leer_trazas(Path(a.trazas) if a.trazas else _trazas_por_defecto())

    out = {"via": VIA, "combinacion_minima": MINIMA,
           "fundamento": "art. 9 Ley 393 de 1997: la accion de cumplimiento "
                         "es subsidiaria, asi que no procede cuando lo "
                         "incumplido afecta un derecho fundamental del "
                         "solicitante --- ahi el camino es la tutela.",
           "motor": mot, "causas": cau, "trazas": tz,
           "conclusion": ""}
    if mot["aciertan"] == mot["n"]:
        out["conclusion"] = (
            f"El motor emite `{VIA}` en {mot['n']}/{mot['n']} casos con los "
            f"hechos declarados: NO es el motor. El fallo esta en la "
            f"extraccion, y solo {cau['n_causas_posibles']} hechos pueden "
            "producirlo.")
    else:
        out["conclusion"] = (
            f"El motor falla {mot['n'] - mot['aciertan']} de {mot['n']} casos "
            "con los hechos declarados: parte del defecto SI es del motor, y "
            "eso cambia el diagnostico de M3-1.")
    RUTA_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    print("=" * 76)
    print(f"  M3-1 · por que el brazo del agente falla `{VIA}`")
    print("=" * 76)
    print(f"  1 · el motor con los hechos declarados: "
          f"{mot['aciertan']}/{mot['n']} aciertan")
    for f in mot["detalle"]:
        if not f["acierta"]:
            print(f"      FALLA {f['id']}: emite {f['motor_emite']}")
    print()
    print(f"  2 · desde la combinacion minima, {cau['n_causas_posibles']} "
          "hechos rompen la via:")
    for c in cau["rompen"]:
        v = c.get("valor_que_rompe")
        extra = f" = {v}" if v is not None else " = True"
        print(f"      {c['hecho']}{extra:8s} -> {c['via_que_sale']}")
    print(f"      ({len(cau['inocuos'])} hechos mas no la cambian)")
    print()
    print("  3 · cual de esas fue, en esta corrida:")
    if tz["disponible"]:
        print(f"      {tz['n_con_traza']} casos con traza")
        for c, n in tz["conteo_por_causa"].items():
            print(f"      {c:30s} en {n} casos")
        if tz["sin_traza"]:
            print(f"      sin traza: {tz['sin_traza']}")
    else:
        print(f"      {tz['motivo']}")
    print()
    print("  " + out["conclusion"].replace(". ", ".\n  "))
    print()
    print(f"  escrito: {RUTA_OUT.relative_to(RAIZ)}")
    print("=" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
