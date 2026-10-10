"""Recalcula `rutas_incorrectas` por respuesta, desde las corridas guardadas.

Por que: `tools/evaluation/rutas.py` tiene `rutas_incorrectas()` desde hace
tiempo, pero `metricas_por_registro.csv` de las corridas de M1 solo guarda
`nombra_mecanismo`, `cita_no_verificable`, `entidad_inventada` y `palabras`. Por
eso una regresion de rutas en v2 -- de 5 marcas en el modelo base a 9 -- no
aparecio en ningun scorecard: nadie la estaba midiendo.

Esto NO modifica el pipeline ni ninguna corrida: lee los `*_results.jsonl` ya
guardados y escribe en un directorio nuevo.

La distincion que importa, y que una tasa agregada esconde: una marca de la
heuristica no es un error confirmado. De las 9 de v2, **8 se confirmaron
leyendo la respuesta y 1 es falso positivo** -- el caso 1530, donde la
respuesta dice *"La conciliacion NO protege tu seguridad: llama a la Linea
123"*, o sea que esta rechazando la conciliacion y la regla la marca por
nombrarla. Las revisiones estan en `REVISADAS`, con su veredicto y el porque.

    python -m tools.metricas_rutas --salida results/m1_rutas_<fecha>
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from tools.evaluation import config as eval_config
from tools.evaluation.rutas import rutas_incorrectas

RAIZ = eval_config.PROJECT_ROOT

CORRIDAS = {
    "base": "results/m1_v2_2026-10-09/baseline_results.jsonl",
    "v1": "results/m1_2026-10-09/finetuned_results.jsonl",
    "v2": "results/m1_v2_2026-10-09/finetuned_results.jsonl",
}

# Veredicto de la revision manual de cada marca, leyendo la respuesta completa.
# "confirmado" = la ruta que da la respuesta es juridicamente incorrecta.
# "falso_positivo" = la regla acerto al detectar el patron pero la respuesta no
#                    comete el error (p. ej. nombra la via para RECHAZARLA).
# "requiere_revision" = el fragmento no permite decidir sin criterio juridico.
REVISADAS: dict[tuple[str, str], tuple[str, str]] = {
    # --- base: inventa instituciones que no existen
    ("base", "493"): ("confirmado", "'Juez de Control de Proteccion' no existe"),
    ("base", "249"): ("confirmado", "'Juez de Paz o Juez de Control' para un canon"),
    ("base", "820"): ("confirmado", "'Juez de Control de Garantias' es penal, no cabe "
                                    "en una peticion de informacion"),
    ("base", "2112"): ("confirmado", "'Juez de Control de Convivencia' no existe"),
    ("base", "1428"): ("requiere_revision", "el fragmento no muestra la ruta errada; "
                                            "el exequatur es de la Corte Suprema"),
    # --- v1: institucion real, competencia errada
    ("v1", "1110"): ("confirmado", "'demandar ante el comisario de justicia'"),
    ("v1", "3606"): ("confirmado", "'demandar ante el comisario de policia'"),
    ("v1", "1435"): ("confirmado", "'demandar ante el comisario de policia'"),
    ("v1", "555"): ("confirmado", "'juez de control de transito' no existe"),
    ("v1", "3106"): ("confirmado", "la querella es policiva, no civil"),
    ("v1", "1428"): ("confirmado", "el exequatur va a la Corte Suprema, Sala Civil, "
                                   "no a 'el juez civil competente'"),
    # --- v2: institucion real y pertinente, vehiculo procesal errado
    ("v2", "1002"): ("confirmado", "ante la Procuraduria se presenta queja "
                                   "disciplinaria, no demanda"),
    ("v2", "607"): ("confirmado", "idem, Personeria y Procuraduria"),
    ("v2", "681"): ("confirmado", "idem, Procuraduria y Contraloria"),
    ("v2", "698"): ("confirmado", "idem, Procuraduria"),
    ("v2", "798"): ("confirmado", "idem, Procuraduria"),
    ("v2", "803"): ("confirmado", "idem, Personeria y Procuraduria"),
    ("v2", "3822"): ("confirmado", "idem, Personeria y Defensoria del Pueblo"),
    ("v2", "751"): ("confirmado", "'querella de cobro ante el juzgado de familia' no "
                                  "es una figura del ordenamiento"),
    ("v2", "1530"): ("falso_positivo", "la respuesta RECHAZA la conciliacion: 'La "
                                       "conciliacion no protege tu seguridad: llama a "
                                       "la Linea 123'. La regla la marca por nombrarla"),
}

COLUMNAS = ["modelo", "case_id", "categoria", "modo", "regla", "veredicto",
            "justificacion", "respuesta"]


def _pregunta(r: dict) -> str:
    return r.get("pregunta") or next(
        (m["content"] for m in r.get("messages", []) if m["role"] == "user"), "")


def analizar() -> tuple[list[dict], dict]:
    filas, resumen = [], {}
    for modelo, ruta in CORRIDAS.items():
        registros = [json.loads(x) for x in (RAIZ / ruta).read_text(
            encoding="utf-8").splitlines() if x.strip()]
        n = len(registros)
        con_respuesta = sum(1 for r in registros if (r.get("generated") or "").strip())
        marcas = 0
        for r in registros:
            resp = r.get("generated") or ""
            reglas = rutas_incorrectas(resp, _pregunta(r))
            if not reglas:
                continue
            marcas += 1
            cid = str(r.get("id"))
            veredicto, just = REVISADAS.get(
                (modelo, cid), ("sin_revisar", "marca de la heuristica, sin revision"))
            filas.append({
                "modelo": modelo, "case_id": cid,
                "categoria": r.get("category", ""),
                "modo": r.get("modo") or "sin_contexto",
                "regla": ";".join(reglas), "veredicto": veredicto,
                "justificacion": just, "respuesta": resp,
            })
        del_modelo = [f for f in filas if f["modelo"] == modelo]
        resumen[modelo] = {
            "registros": n,
            "con_respuesta_no_vacia": con_respuesta,
            "marcas": marcas,
            "tasa_marcas": round(marcas / n, 4),
            "confirmados": sum(1 for f in del_modelo if f["veredicto"] == "confirmado"),
            "falsos_positivos": sum(1 for f in del_modelo
                                    if f["veredicto"] == "falso_positivo"),
            "requieren_revision": sum(1 for f in del_modelo
                                      if f["veredicto"] == "requiere_revision"),
            "sin_revisar": sum(1 for f in del_modelo if f["veredicto"] == "sin_revisar"),
        }
        resumen[modelo]["tasa_confirmados"] = round(
            resumen[modelo]["confirmados"] / n, 4)
    return filas, resumen


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--salida", type=Path, required=True,
                   help="directorio nuevo; no sobrescribe corridas anteriores")
    args = p.parse_args(argv)

    filas, resumen = analizar()
    args.salida.mkdir(parents=True, exist_ok=False)   # no sobrescribe
    with (args.salida / "rutas_por_registro.csv").open(
            "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)
    (args.salida / "resumen.json").write_text(
        json.dumps({"corridas": CORRIDAS, "resumen": resumen},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{'modelo':6s} {'n':>4s} {'resp':>5s} {'marcas':>7s} {'tasa':>7s} "
          f"{'confirm':>8s} {'tasa_c':>7s} {'falso+':>7s} {'revisar':>8s}")
    for m, r in resumen.items():
        print(f"{m:6s} {r['registros']:4d} {r['con_respuesta_no_vacia']:5d} "
              f"{r['marcas']:7d} {r['tasa_marcas']:7.3f} {r['confirmados']:8d} "
              f"{r['tasa_confirmados']:7.3f} {r['falsos_positivos']:7d} "
              f"{r['requieren_revision']:8d}")
    print(f"\nEscrito {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
