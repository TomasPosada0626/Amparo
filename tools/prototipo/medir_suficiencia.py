"""Mide las senales de `suficiencia.py` contra las adjudicaciones existentes.

No genera respuestas ni consume GPU: lee lo guardado.

## Las tres fuentes, que miden cosas distintas y no se promedian

| fuente | n | contexto | verdad |
|---|---|---|---|
| `s10` corrida real | 75 (45 gold + 30 adv) | **recuperacion real** | veredicto por criterio (M2) + puesto del articulo gold (auditoria 6.1) |
| `b2` adjudicacion | 35 | **sintetico del dataset** | `v1_afirmaciones_sin_respaldo` y `pertinencia_contexto` |

Las respuestas de `s10` son **identicas** a las de la config A de S08
(verificado: 75 de 75), asi que los veredictos de esa corrida aplican a estos
textos.

**La tasa de `b2` no es una estimacion de produccion**: su contexto lo armo el
generador del dataset, no el enrutador. Se usa para ver si una senal distingue,
no para predecir cuanto se activaria en servicio.

    python -m tools.prototipo.medir_suficiencia
"""
from __future__ import annotations

import csv
import json
import re

from tools.evaluation import config as eval_config
from tools.prototipo import suficiencia

RAIZ = eval_config.PROJECT_ROOT
S10 = RAIZ / "results" / "m3_s10_2026-10-09" / "eval_records_una_pasada_lora.json"
VEREDICTOS = RAIZ / "results" / "m2_2026-10-09" / "contexto_s08_retrieval_real_resultados.jsonl"
AUDITORIA_61 = RAIZ / "results" / "m3_61_2026-10-10" / "auditoria_61_por_caso.json"
CSV_B2 = RAIZ / "docs" / "m1_b2_adjudicacion.csv"
V1 = RAIZ / "results" / "m1_2026-10-09" / "finetuned_results.jsonl"

TOP_K = 5   # tools/rag/config.TOP_K: cuantos fragmentos se entregan de verdad


def _chunk_normalizado(ch: dict) -> dict:
    """Los chunks guardados traen `cita` y `chunk_id`, no `doc_id` ni articulos.
    Se derivan: el doc_id es el prefijo del chunk_id y el articulo sale de la cita."""
    cid = ch.get("chunk_id") or ""
    doc = cid.split("::", 1)[0] if "::" in cid else (ch.get("doc_id") or "")
    arts = []
    m = re.search(r"Articulo\s+([\w-]+)", ch.get("cita") or "", re.IGNORECASE)
    if m:
        arts.append(m.group(1))
    return {"chunk_id": cid, "doc_id": doc, "cita": ch.get("cita") or "",
            "articulos": arts, "text": ch.get("text") or ""}


def casos_s10() -> list[dict]:
    """Los 75 de la corrida real, con su veredicto y el puesto del articulo gold."""
    recs = json.loads(S10.read_text(encoding="utf-8"))
    ver = {str(r["id"]): r for r in (json.loads(l) for l in
           VEREDICTOS.read_text(encoding="utf-8").splitlines() if l.strip())}
    aud = {str(r["case_id"]): r for r in json.loads(AUDITORIA_61.read_text(encoding="utf-8"))}

    salida = []
    for r in recs:
        cid = str(r["id"])
        chunks = [_chunk_normalizado(c) for c in (r.get("retrieved_chunks") or ())][:TOP_K]
        contexto_texto = "\n".join(
            (c.get("cita") or "") + " " + (c.get("text") or "") for c in chunks)
        if not contexto_texto.strip():
            contexto_texto = "\n".join(r.get("contexts") or ())
        puesto = (aud.get(cid) or {}).get("puesto")
        salida.append({
            "case_id": cid, "tipo": r.get("tipo"), "categoria": r.get("category") or "",
            "pregunta": r.get("question") or "", "respuesta": r.get("answer") or "",
            "chunks": chunks, "contexto_texto": contexto_texto,
            "veredicto": (ver.get(cid) or {}).get("veredicto"),
            "puesto_gold": puesto,
            # El articulo que responde SI se entrego (esta en los TOP_K).
            "evidencia_suficiente": bool(puesto) and puesto <= TOP_K,
            "fuente": "s10",
        })
    return salida


def casos_b2() -> list[dict]:
    """Los 35 B2 adjudicados, con el contexto SINTETICO que vio el modelo."""
    filas = {x["case_id"]: x for x in csv.DictReader(
        CSV_B2.open(encoding="utf-8", newline=""))}
    regs = {str(r["id"]): r for r in (json.loads(l) for l in
            V1.read_text(encoding="utf-8").splitlines() if l.strip())}
    salida = []
    for cid, fila in filas.items():
        r = regs.get(cid)
        if not r:
            continue
        ctx = next(m["content"] for m in r["messages"] if m["role"] == "user")
        salida.append({
            "case_id": cid, "tipo": "b2", "categoria": fila.get("categoria", ""),
            "pregunta": fila.get("pregunta", ""), "respuesta": r.get("generated") or "",
            # El contexto sintetico no viene como chunks; se pasa el texto y las
            # senales que necesitan chunks quedan sin aplicar (se marca aparte).
            "chunks": [], "contexto_texto": ctx,
            "afirmacion_sin_respaldo": bool(fila["v1_afirmaciones_sin_respaldo"].strip()),
            "pertinencia": fila.get("pertinencia_contexto", ""),
            "fuente": "b2",
        })
    return salida


def matriz(casos: list[dict], verdad, nombre_verdad: str,
           senales=None) -> list[tuple]:
    """[(senal, VP, FP, VN, FN, precision, recall)] contra `verdad(caso) -> bool`."""
    senales = senales or suficiencia.SENALES
    salida = []
    for nombre, fn in senales.items():
        vp = fp = vn = neg = 0
        for c in casos:
            try:
                marca = bool(fn(c))
            except Exception:
                marca = False
            real = bool(verdad(c))
            if real and marca:
                vp += 1
            elif real and not marca:
                neg += 1
            elif not real and marca:
                fp += 1
            else:
                vn += 1
        prec = vp / (vp + fp) if vp + fp else float("nan")
        rec = vp / (vp + neg) if vp + neg else float("nan")
        salida.append((nombre, vp, fp, vn, neg, prec, rec))
    return salida


def _imprimir(titulo: str, filas: list[tuple], n: int, nota: str = "") -> None:
    print(f"\n{titulo}   n={n}")
    if nota:
        print(f"  {nota}")
    print(f"  {'senal':46}{'VP':>4}{'FP':>4}{'VN':>4}{'FN':>4}{'prec':>7}{'rec':>7}")
    sin_negativos = all(fp + vn == 0 for _, _, fp, vn, _, _, _ in filas)
    if sin_negativos:
        print("  AVISO: el conjunto no tiene ni un caso negativo, asi que la "
              "precision es 1.00 por construccion y no mide nada.")
    for nombre, vp, fp, vn, fn, prec, rec in filas:
        p = "  n/a" if prec != prec else f"{prec:5.2f}"
        r = "  n/a" if rec != rec else f"{rec:5.2f}"
        print(f"  {nombre:46}{vp:>4}{fp:>4}{vn:>4}{fn:>4}{p:>7}{r:>7}")


def main(argv=None) -> int:
    s10 = casos_s10()
    b2 = casos_b2()
    gold = [c for c in s10 if c["tipo"] == "gold"]
    reservados_b2 = [c for c in b2 if c["case_id"] not in suficiencia.CASOS_DISENO_B2]
    diseno_b2 = [c for c in b2 if c["case_id"] in suficiencia.CASOS_DISENO_B2]

    print("=" * 78)
    print("SENALES DE SUFICIENCIA DE EVIDENCIA -- prototipo, NO conectado")
    print("=" * 78)
    print(f"Conjuntos de diseno declarados: B2 {sorted(suficiencia.CASOS_DISENO_B2)}")
    print(f"                                gold {sorted(suficiencia.CASOS_DISENO_GOLD)}")

    # 1. Contexto entregado insuficiente, con recuperacion REAL.
    _imprimir("1) RECUPERACION REAL -- verdad: el articulo que responde NO se entrego",
              matriz(gold, lambda c: not c["evidencia_suficiente"], "insuficiente"),
              len(gold),
              "etiqueta de la auditoria 6.1 (puesto del articulo gold). No es sintetica.")

    # 2. Lo que cada senal bloquearia de las respuestas que SI cumplen.
    cumplen = [c for c in s10 if c["veredicto"] == "cumple"]
    parciales = [c for c in s10 if c["veredicto"] == "parcial"]
    _imprimir("2) RIESGO DE BLOQUEO -- verdad: la respuesta CUMPLE su criterio",
              matriz(cumplen, lambda c: True, "cumple"), len(cumplen),
              "aqui VP = bloqueo de una respuesta correcta. Interesa que sea BAJO.")
    _imprimir("3) RIESGO DE BLOQUEO -- verdad: la respuesta es PARCIAL",
              matriz(parciales, lambda c: True, "parcial"), len(parciales),
              "parcial debe limitarse, no rechazarse: un bloqueo total aqui es exceso.")

    # 4. Afirmaciones sin respaldo, contexto SINTETICO.
    _imprimir("4) CONTEXTO SINTETICO -- verdad: la adjudicacion marco afirmacion sin respaldo",
              matriz(reservados_b2, lambda c: c["afirmacion_sin_respaldo"], "sin respaldo"),
              len(reservados_b2),
              "RESERVADOS (sin los de diseno). NO es una tasa de produccion.")
    _imprimir("5) los mismos, CONJUNTO DE DISENO",
              matriz(diseno_b2, lambda c: c["afirmacion_sin_respaldo"], "sin respaldo"),
              len(diseno_b2),
              "optimista por construccion: estos casos se miraron al escribir las senales.")

    # 6. Los dos casos nombrados en el encargo.
    print("\n6) LOS DOS CASOS DE REFERENCIA")
    for cid in ("2229", "2823"):
        c = next((x for x in b2 if x["case_id"] == cid), None)
        if not c:
            print(f"  {cid}: no esta en la adjudicacion")
            continue
        activas = [n for n, fn in suficiencia.SENALES.items() if _seguro(fn, c)]
        print(f"  {cid} [{c['categoria']}] adjudicado sin respaldo="
              f"{c['afirmacion_sin_respaldo']}")
        print(f"       senales activas: {activas or 'NINGUNA'}")

    # 7. Clasificacion en cuatro sobre la corrida real.
    from collections import Counter
    print("\n7) CLASIFICACION EN CUATRO, RECUPERACION REAL (45 gold)")
    rep = Counter((suficiencia.clasificar(c), c["evidencia_suficiente"]) for c in gold)
    print(f"  {'clase del prototipo':18}{'evidencia SI':>14}{'evidencia NO':>14}")
    for clase in ("SUFICIENTE", "IRRELEVANTE", "PARCIAL", "SIN_RESPALDO"):
        print(f"  {clase:18}{rep.get((clase, True), 0):>14}{rep.get((clase, False), 0):>14}")
    return 0


def _seguro(fn, c) -> bool:
    try:
        return bool(fn(c))
    except Exception:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
