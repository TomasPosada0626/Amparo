"""
Audita el uso de herramientas del brazo agente: ¿las invocó cuando tocaba?

POR QUÉ ESTO NO EXISTÍA Y HACÍA FALTA

`m3_agente.json` publica `tool_termino: 5` sobre 130 casos. El número solo, sin
el denominador, no se puede leer: 5 de 5 casos elegibles sería perfecto y 5 de
50 sería un fallo grave. La auditoría externa lo señaló como «se usa 5 veces en
130» y la respuesta honesta exige saber **en cuántos tocaba**.

Lo mismo con el techo: `pasos_agotados: 65` de 130 es el 50%, y el artefacto ya
declara que por eso la media de pasos es una cota inferior. Lo que no dice es
si los casos que lo agotan son los difíciles o son todos.

QUÉ CUENTA COMO ELEGIBLE, Y POR QUÉ NO ES UNA HEURÍSTICA

Un caso es elegible para `calcular_termino` cuando la propia herramienta
podría responder: se le pasa el relato y si devuelve `calculable: True` es que
había una fecha legible. Eso no es adivinar — es preguntarle a la herramienta.
La segunda condición, que haya un término legal en juego, se lee de la
categoría del caso y del relato, y las dos se publican por separado para que
quien lea pueda discutir el criterio sin rehacer la medición.

    python -I data/auditar_tool_use.py
"""
from __future__ import annotations
import json
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import terminos                                           # noqa: E402

RUTA_OUT = RAIZ / "data" / "tool_use_auditado.json"
TRAZAS = RAIZ / "results" / "m3_agente_trazas.json"
RESUMEN = RAIZ / "results" / "m3_agente.json"

# Los dos eval sets sobre los que corre el brazo: 109 + 21 = 130.
EVAL_SETS = ("eval_set_v3.json", "eval_set_m3.json")

# La segunda condición: que haya un plazo legal en juego. Se busca en el
# relato, no en la categoría, porque la categoría es metadato del gold y el
# agente no la ve — si el criterio dependiera de ella, la auditoría mediría
# algo que el agente no puede saber.
#
# La primera versión perdía dos casos reales y lo decía mal: contaba `MT04`
# —«le pedí por escrito al municipio que cumpliera el acuerdo […] No
# contestaron»— como invocación FUERA de criterio, cuando es un caso de
# término de renuencia de libro, y dejaba `E64` —«ni me llegó respuesta de
# nadie»— fuera de los elegibles. Fallaba por detalles del verbo: exigía
# «cumplimiento» y no veía «cumpliera», y pedía el «me» de «no me
# contestaron».
#
# Una auditoría que informa de una invocación correcta como desperdiciada es
# peor que no auditar: manda a endurecer un criterio que estaba bien.
PLAZO = re.compile(
    r"(petici[oó]n|peticion|impugna|fallo de tutela|"
    r"cumpl(imiento|ir|a|iera|an)|renuencia|"
    r"respuesta|respond|contest|"
    r"t[eé]rmino|plazo)", re.I)


def _eval() -> dict[str, dict]:
    casos = {}
    for a in EVAL_SETS:
        p = RAIZ / "data" / a
        if not p.exists():
            continue
        for e in json.loads(p.read_text(encoding="utf-8"))["ejemplos"]:
            casos[e["id"]] = e
    return casos


def _trazas() -> list[dict]:
    if not TRAZAS.exists():
        raise SystemExit(
            f"falta {TRAZAS.relative_to(RAIZ)}. Lo publica M3; hay que "
            "correrlo y bajar `results/` antes de auditar nada.")
    d = json.loads(TRAZAS.read_text(encoding="utf-8"))
    return d.get("datos", d) if isinstance(d, dict) else d


def _cruzar(trazas: list[dict], casos: dict[str, dict]) -> dict[str, dict]:
    """Traza -> id del caso. Las trazas guardan el relato RECORTADO.

    `m3_agente_trazas.json` almacena los primeros ~80 caracteres del relato
    para no duplicar el eval set entero. Cruzar por igualdad exacta falla, y
    fallaba en silencio: devolvía 0 cruces y la auditoría habría concluido que
    ningún caso invocó la herramienta.
    """
    por_prefijo = {}
    for cid, e in casos.items():
        por_prefijo[e["relato"].strip()[:60]] = cid
    out, sin_cruzar = {}, 0
    for t in trazas:
        r = (t.get("relato") or "").strip()
        cid = por_prefijo.get(r[:60])
        if cid is None:
            # Por si el recorte cae antes de los 60: se prueba al revés.
            cid = next((c for p, c in por_prefijo.items()
                        if r and p.startswith(r[:40])), None)
        if cid is None:
            sin_cruzar += 1
            continue
        out[cid] = t
    if sin_cruzar:
        print(f"  AVISO {sin_cruzar} traza(s) no se pudieron cruzar con "
              "ningún caso del eval set.")
    return out


def main() -> int:
    casos = _eval()
    trazas = _cruzar(_trazas(), casos)
    hoy = date.today()

    filas = []
    for cid, t in sorted(trazas.items()):
        e = casos[cid]
        # ¿Podría la herramienta responder? Se le pregunta a ella.
        legible = terminos.leer_fecha(e["relato"], hoy=hoy) is not None
        plazo = bool(PLAZO.search(e["relato"]))
        elegible = legible and plazo
        usada = "calcular_termino" in str(t.get("herramientas") or "")
        # Y si NO se usó pero era elegible: ¿habría servido? Es la diferencia
        # entre una omisión del modelo y un límite de la herramienta.
        habria = None
        if elegible and not usada:
            r = terminos.calcular_termino("peticion_general",
                                          relato=e["relato"], hoy=hoy)
            habria = bool(r.get("calculable"))
        filas.append({
            "id": cid, "categoria": e.get("categoria"),
            "fecha_legible": legible, "plazo_en_juego": plazo,
            "elegible": elegible, "uso_la_herramienta": usada,
            "habria_calculado": habria,
            "pasos": t.get("pasos"), "cierre": t.get("cierre"),
            "n_busquedas": t.get("n_busquedas"),
        })

    elig = [f for f in filas if f["elegible"]]
    usadas_elig = [f for f in elig if f["uso_la_herramienta"]]
    perdidas = [f for f in elig if not f["uso_la_herramienta"]]
    recuperables = [f for f in perdidas if f["habria_calculado"]]
    fuera = [f for f in filas if f["uso_la_herramienta"] and not f["elegible"]]

    # El techo. `cierre` lo dice; si no está, se infiere de `pasos`.
    techo = None
    if RESUMEN.exists():
        techo = ((json.loads(RESUMEN.read_text(encoding="utf-8"))
                  .get("pasos_promedio_censura") or {}).get("techo"))
    en_el_techo = [f for f in filas
                   if f["pasos"] is not None and techo and f["pasos"] >= techo]

    out = {
        "_que_es": ("auditoria del uso de herramientas del brazo agente, "
                    "derivada de `results/m3_agente_trazas.json`. No es una "
                    "corrida: no invoca el modelo ni la API."),
        "_criterio_de_elegibilidad": (
            "`calcular_termino` es elegible cuando `terminos.leer_fecha` "
            "encuentra una fecha en el relato Y el relato menciona un plazo "
            "legal. La primera condicion la responde la propia herramienta, "
            "no una heuristica; la segunda es un regex sobre el relato y se "
            "publica aparte para que se pueda discutir sin rehacer la "
            "medicion."),
        "n": len(filas),
        "termino": {
            "elegibles": len(elig),
            "la_usaron": len(usadas_elig),
            "no_la_usaron": len(perdidas),
            "de_esas_habrian_calculado": len(recuperables),
            "usada_fuera_de_criterio": len(fuera),
            "cobertura": (round(len(usadas_elig) / len(elig), 4)
                          if elig else None),
            "ids_perdidos": [f["id"] for f in perdidas],
            "ids_fuera": [f["id"] for f in fuera],
        },
        "techo": {
            "techo": techo,
            "casos_en_el_techo": len(en_el_techo),
            "tasa": (round(len(en_el_techo) / len(filas), 4)
                     if filas and techo else None),
            "lectura": (
                "mientras una parte de la muestra se corte en el techo, la "
                "media de pasos mide el techo y no el comportamiento: hay "
                "que citarla como cota inferior. No implica perdida de "
                "informacion --- el cierre forzado con resumen existe ---, "
                "implica que no se puede medir cuantos pasos habria hecho "
                "falta."),
        },
        "casos": filas,
    }
    RUTA_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8", newline="\n")

    tm = out["termino"]
    print("=" * 78)
    print("  TOOL USE AUDITADO · derivado de las trazas, sin correr nada")
    print("=" * 78)
    print(f"  {len(filas)} casos con traza")
    print()
    print("  calcular_termino")
    print(f"    elegibles                 : {tm['elegibles']}")
    print(f"    la usaron                 : {tm['la_usaron']}"
          + (f"   cobertura {tm['cobertura']:.0%}" if tm["cobertura"] else ""))
    print(f"    NO la usaron              : {tm['no_la_usaron']}"
          f"   ({', '.join(tm['ids_perdidos']) or '-'})")
    print(f"    de esas, habrian calculado: {tm['de_esas_habrian_calculado']}"
          "   <- si es igual al anterior, el fallo es del CRITERIO DE")
    print("                                    INVOCACION, no de la herramienta")
    print(f"    usada fuera de criterio   : {tm['usada_fuera_de_criterio']}"
          f"   ({', '.join(tm['ids_fuera']) or '-'})")
    print()
    tc = out["techo"]
    print("  techo de pasos")
    print(f"    techo                     : {tc['techo']}")
    print(f"    casos que lo tocan        : {tc['casos_en_el_techo']}"
          + (f"   {tc['tasa']:.0%}" if tc["tasa"] is not None else ""))
    print()
    print(f"  escrito: data/{RUTA_OUT.name}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
