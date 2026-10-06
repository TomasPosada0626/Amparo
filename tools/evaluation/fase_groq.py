"""Fase Groq de M2 y scorecard final, a partir de la carpeta de una corrida.

El notebook de M2 usa la GPU solo para generar. Guarda en la carpeta de la
corrida (Drive) las respuestas y las metricas sin juez, y desde ahi todo lo que
falta es HTTP y Python puro:

    calificar(run_dir)  juez Groq: eval set contra su criterio, rubrica 1-5 de
                        la validacion (ambos modelos) y cara a cara en los dos
                        ordenes. ~1 000 llamadas: con el cupo gratuito toma
                        ~5-7 dias (external_judge.py). Si el cupo se acaba,
                        devuelve estado incompleto; volver a llamarla retoma
                        (checkpoint con huella en run_dir/checkpoints).
    informe(run_dir)    scorecard.md y metricas_por_registro.csv finales, con
                        lo que haya: lo que falte de Groq aparece como
                        pendiente, nunca como cero.

Se puede correr en Colab (sin GPU) o en local:

    python -m tools.evaluation.fase_groq <carpeta_de_la_corrida> [--solo-informe] [--out results/m2_<fecha>]

Archivos que espera en run_dir (los escribe el notebook, Fase 3):
    run_manifest.json, metricas_por_registro.csv,
    resultados_baseline.jsonl, resultados_finetuned.jsonl,
    eval_set_baseline_results.jsonl, eval_set_finetuned_results.jsonl
"""
from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from tools.evaluation import bias, criterio, dataset, entity_metric, pipeline, rutas, scorecard
from tools.evaluation import eval_set as eval_set_module
from tools.evaluation.judge import JUDGE_PROMPT_VERSION, JudgeScore

JUEZ = "Groq openai/gpt-oss-120b"
ETAPAS = ("eval_set", "validacion", "cara_a_cara")


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _escribir_jsonl(path: Path, filas: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(f, ensure_ascii=False) for f in filas) + "\n", encoding="utf-8")


def _generaciones(path: Path) -> list[SimpleNamespace]:
    return [SimpleNamespace(**d) for d in _jsonl(path)]


def _pares(base: list, ft: list) -> list[tuple[int, str, str, str]]:
    por_id = {f.id: f for f in ft}
    return [(b.id, b.query, b.generated, por_id[b.id].generated) for b in base if b.id in por_id]


# --------------------------------------------------------------------------
# calificar
# --------------------------------------------------------------------------

def calificar(run_dir: Path, etapas: tuple[str, ...] = ETAPAS) -> dict:
    """Corre las etapas de Groq que falten. Devuelve {etapa: "completa" |
    "incompleta (...)" | "pendiente"}. Orden: primero lo mas importante por
    llamada (eval set contra criterio, 2 por caso), despues la rubrica con
    errores juridicos sobre toda la validacion (462) y al final el cara a cara
    (462)."""
    from tools.evaluation import external_judge

    run_dir = Path(run_dir)
    ck = run_dir / "checkpoints"
    estado = {e: "pendiente" for e in etapas}
    try:
        if "eval_set" in etapas:
            estado["eval_set"] = _etapa_eval_set(run_dir, ck)
        if "validacion" in etapas:
            estado["validacion"] = _etapa_validacion(run_dir, ck, external_judge)
        if "cara_a_cara" in etapas:
            estado["cara_a_cara"] = _etapa_cara_a_cara(run_dir, ck, external_judge)
    except external_judge.CupoAgotado as exc:
        print(f"\n*** {exc}\n*** Lo calificado quedo en {ck}. Volver a correr calificar() cuando "
              "se reinicie el cupo: sigue donde quedo.")
    print("Estado de la fase Groq:", json.dumps(estado, ensure_ascii=False))
    return estado


def _etapa_eval_set(run_dir: Path, ck: Path) -> str:
    registros = eval_set_module.load_eval_set()
    por_id = {r["id"]: r for r in registros}
    base = _generaciones(run_dir / "eval_set_baseline_results.jsonl")
    ft = _generaciones(run_dir / "eval_set_finetuned_results.jsonl")
    juez = criterio.generador_groq()
    vb = criterio.evaluar_contra_criterio(base, registros, juez,
                                          checkpoint_path=ck / "groq_criterio_eval_set_baseline.jsonl")
    vf = criterio.evaluar_contra_criterio(ft, registros, juez,
                                          checkpoint_path=ck / "groq_criterio_eval_set_finetuned.jsonl")
    filas = []
    for gb, gf, xb, xf in zip(base, ft, vb, vf):
        rec = por_id[gb.id]
        filas.append({
            "id": gb.id, "tipo": rec["tipo"], "category": rec["category"], "criterio": rec["criterio"],
            "query": gb.query,
            "baseline": gb.generated, "baseline_cortada": getattr(gb, "cortada", False),
            "baseline_veredicto": xb.veredicto, "baseline_errores": xb.errores_juridicos,
            "baseline_citas": xb.n_citas, "baseline_justificacion": xb.justificacion,
            "fine_tuned": gf.generated, "fine_tuned_cortada": getattr(gf, "cortada", False),
            "fine_tuned_veredicto": xf.veredicto, "fine_tuned_errores": xf.errores_juridicos,
            "fine_tuned_citas": xf.n_citas, "fine_tuned_justificacion": xf.justificacion,
        })
    _escribir_jsonl(run_dir / "eval_set_resultados.jsonl", filas)
    (run_dir / "groq_eval_set_resumen.json").write_text(
        json.dumps(criterio.resumen(vb + vf), indent=2, ensure_ascii=False), encoding="utf-8")
    sin = sum(1 for v in vb + vf if not v.veredicto)
    return "completa" if sin == 0 else f"incompleta ({sin} sin veredicto: volver a correr)"


def _etapa_validacion(run_dir: Path, ck: Path, external_judge) -> str:
    salida, sin = [], 0
    # El fine-tuned primero: si el cupo alcanza para uno solo, es el que importa.
    # El archivo se escribe al terminar cada modelo, para que el informe ya lo use.
    for label, archivo in (("fine_tuned", "resultados_finetuned.jsonl"), ("baseline", "resultados_baseline.jsonl")):
        gens = _generaciones(run_dir / archivo)
        puntajes = external_judge.score_batch(gens, checkpoint_path=ck / f"groq_validacion_{label}.jsonl")
        for g, p in zip(gens, puntajes):
            salida.append({"label": label, "id": g.id, "prompt_version": JUDGE_PROMPT_VERSION, **asdict(p)})
            sin += 0 if p.parse_ok else 1
        _escribir_jsonl(run_dir / "groq_validacion.jsonl", salida)
    return "completa" if sin == 0 else f"incompleta ({sin} sin puntaje: volver a correr)"


def _etapa_cara_a_cara(run_dir: Path, ck: Path, external_judge) -> str:
    base = _generaciones(run_dir / "resultados_baseline.jsonl")
    ft = _generaciones(run_dir / "resultados_finetuned.jsonl")
    rep = external_judge.comparar_cara_a_cara(_pares(base, ft), checkpoint_path=ck / "groq_cara_a_cara.jsonl")
    (run_dir / "groq_cara_a_cara.json").write_text(json.dumps({
        **rep.__dict__, "veredicto_consistente": rep.veredicto_consistente(),
        "tasa_victoria": rep.tasa_victoria()}, indent=2, ensure_ascii=False), encoding="utf-8")
    sin = rep.veredicto_consistente()["sin_veredicto"]
    return "completa" if sin == 0 else f"incompleta ({sin} pares sin veredicto: volver a correr)"


# --------------------------------------------------------------------------
# informe
# --------------------------------------------------------------------------

def _cargar_juez(run_dir: Path) -> Optional[dict[tuple[str, int], JudgeScore]]:
    path = run_dir / "groq_validacion.jsonl"
    if not path.exists():
        return None
    campos = set(JudgeScore.__dataclass_fields__)
    # Solo puntajes de la rubrica actual: uno de un prompt anterior no es comparable.
    puntajes = {(d["label"], d["id"]): JudgeScore(**{k: v for k, v in d.items() if k in campos})
                for d in _jsonl(path) if d.get("prompt_version") == JUDGE_PROMPT_VERSION}
    return puntajes or None


def _guardias(rows: list, mapa: rutas.MapaContexto) -> None:
    """Recalcula las guardias con el codigo actual (el mismo que escribe el informe)."""
    for r in rows:
        rev = rutas.revisar(r.generated, r.query, r.category, mapa)
        r.entidades_inventadas = ", ".join(entity_metric.find_fabricated_entities(r.generated))
        r.rutas_incorrectas = ", ".join(rev.rutas_incorrectas)
        r.fuera_de_contexto = ", ".join(rev.fuera_de_contexto)


def _reporte_rutas(etiqueta: str, filas: list[dict], mapa: rutas.MapaContexto) -> dict:
    rep = rutas.reporte(etiqueta, filas, mapa)
    n_ent = sum(1 for f in filas if entity_metric.find_fabricated_entities(f["generated"]))
    return {"etiqueta": etiqueta, "n": rep.n,
            "pct_entidad_inventada": round(100 * n_ent / rep.n, 1) if rep.n else 0.0,
            "pct_ruta_incorrecta": rep.pct_ruta_incorrecta, "pct_fuera_de_contexto": rep.pct_fuera_de_contexto,
            "por_regla": rep.por_regla, "por_concepto": rep.por_concepto}


def _seccion_rutas(rows: list, val_records: list[dict], mapa: rutas.MapaContexto) -> dict:
    def filas(label):
        return [{"id": r.id, "query": r.query, "category": r.category, "generated": r.generated}
                for r in rows if r.label == label]

    reportes = [_reporte_rutas("referencias de validación (calibración)",
                               rutas.referencias_como_filas(val_records), mapa),
                _reporte_rutas("baseline", filas("baseline"), mapa),
                _reporte_rutas("fine_tuned", filas("fine_tuned"), mapa)]
    marcadas = [{
        "id": r.id, "category": r.category,
        "marcas": "; ".join(x for x in (
            r.entidades_inventadas and f"entidad: {r.entidades_inventadas}",
            r.rutas_incorrectas and f"ruta: {r.rutas_incorrectas}",
            r.fuera_de_contexto and f"contexto: {r.fuera_de_contexto}") if x),
        "errores_juez": r.errores_juridicos, "respuesta": r.generated,
    } for r in rows if r.label == "fine_tuned" and (r.marca_entidad or r.marca_ruta or r.marca_contexto)]
    return {"reportes": reportes, "marcadas": marcadas}


def _abstencion_eval_set(filas: list[dict]) -> list[dict]:
    salida = []
    adversariales = [f for f in filas if f["tipo"] == "adversarial"]
    for cat in sorted({f["category"] for f in adversariales}):
        for label in ("baseline", "fine_tuned"):
            vs = [f[f"{label}_veredicto"] for f in adversariales if f["category"] == cat]
            salida.append({"categoria": cat, "label": label, "n": len(vs),
                           "cumple": vs.count("cumple"), "parcial": vs.count("parcial"),
                           "no_cumple": vs.count("no_cumple"), "sin_veredicto": vs.count(None)})
    return salida


def informe(run_dir: Path, out: Optional[Path] = None) -> str:
    """Scorecard final con lo que haya en run_dir. Devuelve el texto."""
    run_dir = Path(run_dir)
    out = Path(out) if out else run_dir
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    rows = scorecard.load_csv(run_dir / "metricas_por_registro.csv")

    registros = dataset.load_records()
    train, val = dataset.stratified_split(registros)
    if manifest.get("n_val") and manifest["n_val"] != len(val):
        raise ValueError(f"La corrida evaluo {manifest['n_val']} ejemplos de validacion y el dataset de esta "
                         f"rama da {len(val)}: el informe tiene que hacerse con el mismo dataset.")
    mapa = rutas.construir_mapa(train)
    _guardias(rows, mapa)

    pendiente = []
    juez = _cargar_juez(run_dir)
    if juez is None:
        pendiente.append("rubrica 1-5 de la validacion")
    else:
        faltan = pipeline.aplicar_juez(rows, juez)
        if faltan:
            pendiente.append(f"rubrica 1-5 de la validacion ({faltan} filas sin puntaje)")

    summaries = scorecard.summarize_by_label(rows)
    comparacion = scorecard.comparar(rows)
    categorias = {lab: scorecard.summarize_by_category(rows, lab) for lab in ("baseline", "fine_tuned")}

    cara = None
    if (run_dir / "groq_cara_a_cara.json").exists():
        d = json.loads((run_dir / "groq_cara_a_cara.json").read_text(encoding="utf-8"))
        rep = bias.PositionBiasReport(**{k: d[k] for k in ("n_pairs", "n_flipped", "n_tied_or_unparsed",
                                                           "flip_rate_pct", "details")})
        cara = {"juez": JUEZ, "n_pares": rep.n_pairs, "consistente": rep.veredicto_consistente(),
                "tasa_victoria": rep.tasa_victoria(), "flip_rate_pct": rep.flip_rate_pct}
        if cara["consistente"]["sin_veredicto"]:
            pendiente.append(f"cara a cara ({cara['consistente']['sin_veredicto']} pares sin veredicto)")
    else:
        pendiente.append("cara a cara")

    eval_resumen, ab_eval = None, []
    if (run_dir / "eval_set_resultados.jsonl").exists():
        filas_eval = _jsonl(run_dir / "eval_set_resultados.jsonl")
        eval_resumen = json.loads((run_dir / "groq_eval_set_resumen.json").read_text(encoding="utf-8"))
        ab_eval = _abstencion_eval_set(filas_eval)
    else:
        pendiente.append("eval set contra su criterio")

    sesgos = {}
    for lab in ("baseline", "fine_tuned"):
        # Sin concision: ese criterio premia lo corto a proposito; lo que se busca
        # es si los otros tres suben con el largo.
        con = [r for r in rows if r.label == lab and r.judge_sin_concision is not None]
        if con:
            sesgos[f"correlacion_puntaje_sin_concision_largo_{lab}"] = bias.length_bias_correlation(
                [r.judge_sin_concision for r in con], [len(r.generated) for r in con])["pearson_r"]
    if cara:
        sesgos["flip_rate_pct_cara_a_cara"] = cara["flip_rate_pct"]

    seccion_rutas = _seccion_rutas(rows, val, mapa)
    narrativa = scorecard.build_narrative(summaries, sesgos, n_val=manifest.get("n_val", 0),
                                          comparacion=comparacion if juez else None, eval_set=eval_resumen,
                                          cara_a_cara=cara, rutas=seccion_rutas)
    if pendiente:
        narrativa = ("**PENDIENTE (Groq sin terminar):** " + "; ".join(pendiente)
                     + ". Volver a correr fase_groq.calificar() y despues el informe.\n\n" + narrativa)

    ejemplos = None
    if (run_dir / "eval_set_baseline_results.jsonl").exists():
        ejemplos = scorecard.elegir_ejemplos(
            eval_set_module.load_eval_set(),
            _generaciones(run_dir / "eval_set_baseline_results.jsonl"),
            _generaciones(run_dir / "eval_set_finetuned_results.jsonl"))

    scorecard.export_markdown(
        out / "scorecard.md", summaries, categorias, narrativa, sesgos, manifest,
        comparacion=comparacion, eval_set=eval_resumen, ejemplos=ejemplos,
        cara_a_cara=cara, rutas=seccion_rutas,
        abstencion={"validacion": scorecard.resumen_abstencion(rows), "eval_set": ab_eval},
        titulo_juez=f"Juez {JUEZ} (rúbrica 1-5 contra la referencia)")
    scorecard.export_csv(out / "metricas_por_registro.csv", rows)
    if out != run_dir:
        for nombre in ("run_manifest.json", "eval_set_resultados.jsonl", "groq_eval_set_resumen.json",
                       "groq_validacion.jsonl", "groq_cara_a_cara.json"):
            if (run_dir / nombre).exists():
                shutil.copy(run_dir / nombre, out / nombre)
    return (out / "scorecard.md").read_text(encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_dir", type=Path)
    p.add_argument("--solo-informe", action="store_true", help="no llamar a Groq; solo rehacer el scorecard")
    p.add_argument("--out", type=Path, help="carpeta de salida del informe (por defecto, la de la corrida)")
    a = p.parse_args()
    if not a.solo_informe:
        calificar(a.run_dir)
    informe(a.run_dir, a.out)
    print(f"Scorecard: {(a.out or a.run_dir) / 'scorecard.md'}")


if __name__ == "__main__":
    main()
