"""Descompone la ganancia del fine-tuning en FORMATO y RAZONAMIENTO.

EL PROBLEMA QUE ESTO MIDE

    La cifra de cabecera de M1 es el salto del `acierto_juridico`: 1.9% en el
    modelo base contra 74.8% en el afinado. Una auditoria externa (Lucas
    Higuita, 2026-10-20) senalo que esa cifra esta inflada, y al medirlo tiene
    razon:

        base        mecanismo 33.3%   procedencia 57.1%   los dos 3.2%
        afinado     mecanismo 87.3%   procedencia 87.3%   los dos 87.3%

    El base ACIERTA el mecanismo una de cada tres veces. Lo que no hace es
    responder en el formato: donde el esquema pide `Procedencia: si|no`
    escribe prosa --- «Procedencia: La EPS debe garantizar el acceso a...» ---
    y el parser lo lee `False`, correctamente. En 22 de 63 salidas ni el
    mecanismo se puede leer.

    Asi que el salto de cabecera suma dos cosas distintas:

      · CUMPLIMIENTO DE FORMATO, que el fine-tuning ensena y que es real y
        util --- sin bloque parseable no hay sistema --- pero NO es
        razonamiento juridico.
      · CORRECCION JURIDICA dado un formato legible, que es lo que el trabajo
        afirma haber mejorado.

    Publicar las dos juntas como una sola cifra es exactamente el tipo de
    numero que este proyecto existe para no publicar. Esto las separa.

POR QUE UNA AUDITORIA DERIVADA Y NO UNA METRICA DE `src/`
    Porque se puede correr HOY, sobre los artefactos que ya existen, sin GPU
    ni API. Una metrica en `src/metricas.py` cambiaria la huella de codigo y
    habria que esperar la siguiente corrida para tener la cifra. Mismo patron
    que `auditar_cobertura.py` y `diagnostico_cumplimiento.py`.

    Uso: python -I data/descomponer_baseline.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
import schema  # noqa: E402

PRED = RAIZ / "results" / "m1_predicciones.json"
RUTA_OUT = RAIZ / "data" / "descomposicion_baseline.json"


def _gold() -> dict:
    g = {}
    for arch in ("eval_set_v2.json", "eval_set_v3.json"):
        try:
            for c in schema.cargar(archivo=arch):
                g[c["id"]] = c
        except Exception:                                     # noqa: BLE001
            pass
    return g


def medir(filas: list[dict], gold: dict) -> dict:
    """Por brazo: mecanismo, procedencia, los dos, y cuanto no se pudo leer."""
    brazos = [k for k in ("base", "hibrido", "finetuned") if filas
              and k in filas[0]]
    out = {}
    for quien in brazos:
        n = mec = proc = ambos = ileg_mec = ileg_proc = 0
        mec_ok_proc_mal = []
        for f in filas:
            g = gold.get(f["id"])
            if not g or not g.get("mecanismo"):
                continue
            n += 1
            d = schema.parse_salida(f[quien]) or {}
            if d.get("mecanismo") is None:
                ileg_mec += 1
            if d.get("procede") is None:
                ileg_proc += 1
            ok_m = d.get("mecanismo") == g["mecanismo"]
            ok_p = d.get("procede") == g.get("procede")
            mec += ok_m
            proc += ok_p
            ambos += ok_m and ok_p
            if ok_m and not ok_p and len(mec_ok_proc_mal) < 6:
                mec_ok_proc_mal.append({
                    "id": f["id"], "procede_gold": g.get("procede"),
                    "procede_leido": d.get("procede"),
                    "salida": f[quien][:220]})
        if not n:
            continue
        out[quien] = {
            "n": n,
            "acc_mecanismo": round(mec / n, 4),
            "acc_procedencia": round(proc / n, 4),
            "acierto_juridico_parcial": round(ambos / n, 4),
            "mecanismo_ilegible": ileg_mec,
            "procedencia_ilegible": ileg_proc,
            # La brecha ES el efecto del formato: casos en que acierta el
            # mecanismo y pierde el acierto conjunto.
            "brecha_formato": round(mec / n - ambos / n, 4),
            "ejemplos_mecanismo_ok_procedencia_mal": mec_ok_proc_mal,
        }
    return out


def main() -> int:
    if not PRED.exists():
        print(f"no esta {PRED.relative_to(RAIZ)}: hace falta una corrida de M1")
        return 1
    pred = json.loads(PRED.read_text(encoding="utf-8"))
    filas, gold = pred["datos"], _gold()
    por_brazo = medir(filas, gold)

    base = por_brazo.get("base", {})
    ft = por_brazo.get("finetuned", {})
    salto_cabecera = (round(ft.get("acierto_juridico_parcial", 0)
                            - base.get("acierto_juridico_parcial", 0), 4)
                      if base and ft else None)
    # Cuanto del salto se explica porque el base NO PUEDE ser leido. Es la
    # parte que mide formato y no derecho.
    de_formato = base.get("brecha_formato")
    # Y cuanto queda como diferencia de mecanismo, que si es razonamiento.
    de_razonamiento = (round(ft.get("acc_mecanismo", 0)
                             - base.get("acc_mecanismo", 0), 4)
                       if base and ft else None)

    out = {
        "_artefacto": "descomposicion_baseline.json",
        "_corrida_de_las_predicciones": pred.get("_corrida"),
        "por_brazo": por_brazo,
        "salto_de_cabecera_acierto_juridico": salto_cabecera,
        "atribuible_a_formato_del_base": de_formato,
        "diferencia_de_mecanismo": de_razonamiento,
        "lectura": (
            "`salto_de_cabecera_acierto_juridico` es la cifra que el reporte "
            "publica. `diferencia_de_mecanismo` es la parte que SI es "
            "razonamiento juridico: cuanto mas acierta el afinado la via "
            "procesal. `atribuible_a_formato_del_base` es lo que el base "
            "pierde por no responder en el formato que el esquema pide, con "
            "el mecanismo ya acertado. Las dos son ganancias reales del "
            "fine-tuning --- sin bloque parseable no hay sistema --- pero "
            "solo la segunda es una afirmacion sobre derecho, y presentarlas "
            "sumadas exagera lo que el trabajo demuestra."),
        "por_que_importa": (
            "Un baseline que falla por formato es un hombre de paja: hace que "
            "cualquier modelo que respete el esquema parezca enormemente "
            "mejor. La comparacion justa contra el base es el brazo HIBRIDO "
            "--- el base extrae los hechos y el motor de reglas decide ---, "
            "que ya se publica en `m1_scorecard_hibrido.json` y que aisla el "
            "razonamiento del formato."),
        "lo_que_no_mide": (
            "No da el baseline justo, solo lo cuantifica. Un baseline de "
            "formato --- el base con few-shot del bloque de cinco lineas --- "
            "exige una corrida y queda pendiente."),
    }
    RUTA_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    print("=" * 78)
    print("  DESCOMPOSICION DE LA GANANCIA DEL FINE-TUNING")
    print("=" * 78)
    print(f"  predicciones de la corrida {pred.get('_corrida')}")
    print()
    print(f"  {'brazo':12s}{'mecanismo':>11s}{'procedencia':>13s}"
          f"{'los dos':>10s}{'mec. ilegible':>15s}")
    for quien, d in por_brazo.items():
        print(f"  {quien:12s}{d['acc_mecanismo']:>10.1%}"
              f"{d['acc_procedencia']:>13.1%}"
              f"{d['acierto_juridico_parcial']:>10.1%}"
              f"{d['mecanismo_ilegible']:>10} de {d['n']}")
    print()
    if salto_cabecera is not None:
        print(f"  salto de cabecera publicado        : {salto_cabecera:+.1%}")
        print(f"  de eso, diferencia de MECANISMO    : {de_razonamiento:+.1%}"
              "   <- razonamiento juridico")
        print(f"  y el base pierde por FORMATO       : {de_formato:+.1%}"
              "   <- con el mecanismo ya acertado")
    print()
    print(f"  escrito: data/{RUTA_OUT.name}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
