"""Adjudicacion del escenario irrelevante (fase C, paso C5).

Los 4 escenarios (`tools/evaluation/escenarios.py`) miden lo automatico: si el
modelo se abstiene, si cita el articulo que responde. Lo que no miden es si la
respuesta al contexto irrelevante es *funcionalmente* correcta, que es el
criterio B2_funcional: reconocer que el contexto no alcanza Y no afirmar como
cierto lo que el contexto no respalda. Eso es juicio juridico, igual que en los
35 B2 de validacion (`tools/adjudicacion_b2.py`), y por eso esta planilla usa el
mismo vocabulario y los mismos controles.

Diferencias con la planilla B2:
  - el contexto lo construyo el buscador de produccion sin el articulo que
    responde ni sus contiguos; aun asi puede traer algo util de la misma
    materia. `pertinencia_contexto` se adjudica UNA vez y vale para los dos
    modelos, que vieron exactamente lo mismo;
  - v1 y v3 van lado a lado en la misma fila, las dos corridas del 2026-10-12
    en la misma maquina.

    python -m tools.adjudicacion_escenarios --crear
    python -m tools.adjudicacion_escenarios --revisar
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from tools.adjudicacion_b2 import VOCABULARIO
from tools.evaluation import config

RAIZ = config.PROJECT_ROOT
ESCENARIOS = RAIZ / "data" / "escenarios_m1.jsonl"
SALIDA = RAIZ / "docs" / "m1_escenarios_irrelevante_adjudicacion.csv"
CORRIDAS = {
    "v1": RAIZ / "results" / "m1_escenarios_2026-10-12" / "v1_20261012-686e5bca"
          / "escenarios_resultados.jsonl",
    "v3": RAIZ / "results" / "m1_escenarios_2026-10-12" / "v3_20261012-9a8096d7"
          / "escenarios_resultados.jsonl",
}
MODELOS = tuple(CORRIDAS)


def _por_modelo(m: str) -> list[str]:
    return [f"respuesta_{m}", f"{m}_fundamentacion", f"{m}_calibracion",
            f"{m}_orientacion_segura", f"{m}_afirmaciones_sin_respaldo", f"{m}_riesgo"]


COLUMNAS = [
    "case_id", "categoria", "pregunta", "fuentes_que_responden", "fuentes_entregadas",
    "pertinencia_contexto", "justificacion_contexto",
    *[c for m in MODELOS for c in _por_modelo(m)],
    "revision_juridica", "confianza", "justificacion_final",
    "revisor", "fecha_revision", "origen",
]

VOCAB = {
    "pertinencia_contexto": VOCABULARIO["pertinencia_contexto"],
    "revision_juridica": VOCABULARIO["revision_juridica"],
    "confianza": VOCABULARIO["confianza"],
    **{f"{m}_fundamentacion": VOCABULARIO["v1_fundamentacion"] for m in MODELOS},
    **{f"{m}_calibracion": VOCABULARIO["v1_calibracion"] for m in MODELOS},
    **{f"{m}_orientacion_segura": VOCABULARIO["v1_orientacion_segura"] for m in MODELOS},
    **{f"{m}_riesgo": VOCABULARIO["v1_riesgo"] for m in MODELOS},
}

OBLIGATORIAS = [
    "pertinencia_contexto", "justificacion_contexto",
    *[f"{m}_{c}" for m in MODELOS
      for c in ("fundamentacion", "calibracion", "orientacion_segura", "riesgo")],
    "revision_juridica", "confianza", "justificacion_final", "revisor",
    "fecha_revision", "origen",
]


def _leer(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def _normalizar(t: str) -> str:
    t = re.sub(r"[\"'“”‘’«»]", "", t or "")
    return re.sub(r"\s+", " ", t).strip().lower()


def casos_irrelevantes() -> list[dict]:
    return [c for c in _leer(ESCENARIOS) if c["escenario"] == "irrelevante"]


def contexto_texto(caso: dict) -> str:
    """El bloque CONTEXTO que vio el modelo, tal cual."""
    return next(m["content"] for m in caso["messages"] if m["role"] == "user")


def respuestas(modelo: str) -> dict[str, str]:
    return {str(r["id"]): r.get("generated") or ""
            for r in _leer(CORRIDAS[modelo]) if r["escenario"] == "irrelevante"}


def crear(ruta: Path = SALIDA) -> int:
    textos = {m: respuestas(m) for m in MODELOS}
    filas = []
    for c in casos_irrelevantes():
        cid = str(c["id"])
        fila = {k: "" for k in COLUMNAS}
        fila.update({
            "case_id": cid, "categoria": c["category"], "pregunta": c["pregunta"],
            "fuentes_que_responden": "; ".join(c["fuentes"]),
            "fuentes_entregadas": "; ".join(x["cita"] for x in c["contexto"]),
            "origen": ("data/escenarios_m1.jsonl (d51365fbc779d1ce); corridas "
                       "v1 20261012-686e5bca y v3 20261012-9a8096d7"),
        })
        for m in MODELOS:
            fila[f"respuesta_{m}"] = textos[m][cid]
        filas.append(fila)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    return len(filas)


def revisar(filas: list[dict], textos: dict[str, dict[str, str]] | None = None,
            ids_esperados: set[str] | None = None) -> list[str]:
    ids_esperados = ids_esperados or {str(c["id"]) for c in casos_irrelevantes()}
    problemas = []
    ids = [f.get("case_id", "") for f in filas]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        problemas.append(f"case_id repetidos: {repetidos}")
    if set(ids) != ids_esperados:
        problemas.append(f"no son los {len(ids_esperados)} irrelevantes: faltan "
                         f"{sorted(ids_esperados - set(ids))}, sobran {sorted(set(ids) - ids_esperados)}")
    for f in filas:
        cid = f.get("case_id", "?")
        vacias = [c for c in OBLIGATORIAS if not (f.get(c) or "").strip()]
        if vacias:
            problemas.append(f"{cid}: sin llenar {vacias}")
        for col, validos in VOCAB.items():
            v = (f.get(col) or "").strip()
            if v and v not in validos:
                problemas.append(f"{cid}: {col}={v!r} no esta en {sorted(validos)}")
        for m in MODELOS:
            real = (textos or {}).get(m, {}).get(cid)
            if textos is not None and (real is None or
                                       _normalizar(f.get(f"respuesta_{m}")) != _normalizar(real)):
                problemas.append(f"{cid}: respuesta_{m} no es la de la corrida")
            if (f.get(f"{m}_fundamentacion") or "").strip() == "excede":
                cita = (f.get(f"{m}_afirmaciones_sin_respaldo") or "").strip()
                if not cita:
                    problemas.append(f"{cid}: {m} marcado 'excede' sin citar la afirmacion")
                elif _normalizar(cita) not in _normalizar(f.get(f"respuesta_{m}")):
                    problemas.append(f"{cid}: la cita de {m} no aparece en su respuesta: {cita[:60]!r}")
        if (f.get("revision_juridica") or "").strip() == "cumplida" and \
                "Galeano" not in (f.get("revisor") or ""):
            problemas.append(f"{cid}: revision_juridica=cumplida sin el abogado en 'revisor'")
    return problemas


def analizar(filas: list[dict]) -> dict:
    """B2_funcional y fallos criticos por modelo, con los chequeos mecanicos
    contra el contexto que de verdad se entrego."""
    from tools.evaluation import b2_funcional

    casos = {str(c["id"]): c for c in casos_irrelevantes()}
    # B2_funcional solo tiene sentido donde el contexto de verdad no alcanza:
    # si la adjudicacion encontro que el "irrelevante" responde en parte o del
    # todo, responder ahi no es un fallo. Se reporta aparte.
    insuficientes = {f["case_id"] for f in filas if f.get("pertinencia_contexto") == "insuficiente"}
    out = {}
    for m in MODELOS:
        ev = [b2_funcional.evaluar(f, f.get(f"respuesta_{m}") or "",
                                   contexto_texto(casos[f["case_id"]]), modelo=m) for f in filas]
        sub = [x for x in ev if x["case_id"] in insuficientes]
        out[m] = {
            "n": len(ev),
            "pasan_b2_funcional": sum(x["pasa_b2_funcional"] for x in ev),
            "con_fallo_critico": sum(x["tiene_fallo_critico"] for x in ev),
            "n_insuficiente": len(sub),
            "pasan_en_insuficiente": sum(x["pasa_b2_funcional"] for x in sub),
            "por_caso": {x["case_id"]: x for x in ev},
        }
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--crear", action="store_true")
    g.add_argument("--revisar", action="store_true")
    a = p.parse_args(argv)
    if a.crear:
        if SALIDA.exists():
            raise SystemExit(f"{SALIDA.name} ya existe: no se sobrescribe una revision en curso.")
        print(f"Escrito {SALIDA} con {crear()} casos.")
        return 0
    with SALIDA.open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    problemas = revisar(filas, {m: respuestas(m) for m in MODELOS})
    if problemas:
        for s in problemas[:40]:
            print(f"  - {s}")
        raise SystemExit(f"{len(problemas)} problemas: la adjudicacion no esta cerrada.")
    a = analizar(filas)
    for m in MODELOS:
        print(f"{m}: B2_funcional {a[m]['pasan_en_insuficiente']}/{a[m]['n_insuficiente']} "
              f"donde el contexto no alcanza ({a[m]['pasan_b2_funcional']}/{a[m]['n']} en todos), "
              f"con fallo critico {a[m]['con_fallo_critico']}/{a[m]['n']}")
    print("Sin problemas: los casos adjudicados y trazables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
