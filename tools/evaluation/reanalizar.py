"""Vuelve a analizar una corrida de M2 ya guardada (carpeta de Drive), sin GPU
ni juez: recalcula el scorecard con la version actual (criterios del juez por
separado, IC, respuestas cortadas, notas de cada metrica, ejemplos textuales)
y deja en `--out` los archivos para comitear en results/.

No reusa puntajes que no se puedan atribuir a esta corrida: los puntajes del
eval set y el sondeo de Groq de corridas anteriores a la huella de checkpoint
(tools/evaluation/checkpoint.py) pueden venir de otra corrida, asi que no se
copian salvo que se pida con --incluir-groq.

Uso:
    python -m tools.evaluation.reanalizar <carpeta_de_la_corrida> --out results/m2_<fecha>
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

from tools.evaluation import eval_set as eval_set_module
from tools.evaluation import scorecard


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _ganadores(path: Path) -> dict:
    detalles = json.loads(path.read_text(encoding="utf-8"))["details"]
    conteo: dict[str, int] = {}
    for d in detalles:
        for k in ("verdict_normal", "verdict_swapped"):
            w = d.get(k) or "sin_veredicto"
            conteo[w] = conteo.get(w, 0) + 1
    return conteo


def reanalizar(run_dir: Path, out: Path, incluir_groq: bool = False, notas_extra: list[str] | None = None) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    rows = scorecard.load_csv(run_dir / "metricas_por_registro.csv")
    if not scorecard.csv_tiene_columna(run_dir / "metricas_por_registro.csv", "cortada"):
        # Corrida anterior al conteo de tokens: se estima por puntuacion final.
        # El scorecard lo dice en sus notas; en las corridas nuevas se usa el dato real.
        for r in rows:
            r.cortada = scorecard.parece_cortada(r.generated)
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))

    summaries = scorecard.summarize_by_label(rows)
    comparacion = scorecard.comparar(rows)
    ganadores = {"Qwen2.5-7B (juez local, mismo modelo que el baseline)": _ganadores(run_dir / "position_bias_probe.json")}
    groq = run_dir / "groq_position_bias_probe.json"
    if incluir_groq and groq.exists():
        ganadores["Groq gpt-oss-120b"] = _ganadores(groq)

    ejemplos = None
    if (run_dir / "eval_set_baseline_results.jsonl").exists():
        registros = eval_set_module.load_eval_set()
        base = [SimpleNamespace(**d) for d in _jsonl(run_dir / "eval_set_baseline_results.jsonl")]
        ft = [SimpleNamespace(**d) for d in _jsonl(run_dir / "eval_set_finetuned_results.jsonl")]
        ejemplos = scorecard.elegir_ejemplos(registros, base, ft)
        por_id = {r["id"]: r for r in registros}
        fb = {g.id: g.generated for g in base}
        (out / "eval_set_respuestas.jsonl").write_text("\n".join(json.dumps({
            "id": g.id, "tipo": por_id[g.id]["tipo"], "category": por_id[g.id]["category"],
            "criterio": por_id[g.id]["criterio"], "query": g.query,
            "baseline": fb[g.id], "fine_tuned": g.generated}, ensure_ascii=False) for g in ft) + "\n",
            encoding="utf-8")

    bias = {
        "position_bias_flip_rate_pct": json.loads((run_dir / "position_bias_probe.json").read_text())["flip_rate_pct"],
        "position_bias_n_pairs": json.loads((run_dir / "position_bias_probe.json").read_text())["n_pairs"],
    }
    narrativa = scorecard.build_narrative(summaries, bias, n_val=manifest.get("n_val", 0),
                                          comparacion=comparacion, ganadores=ganadores)
    if notas_extra:
        narrativa += "\n\n" + "\n\n".join(notas_extra)
    categorias = {lab: scorecard.summarize_by_category(rows, lab) for lab in ("baseline", "fine_tuned")}
    scorecard.export_markdown(out / "scorecard.md", summaries, categorias, narrativa, bias, manifest,
                              comparacion=comparacion, ganadores=ganadores, ejemplos=ejemplos)
    scorecard.export_csv(out / "metricas_por_registro.csv", rows)
    for nombre in ("run_manifest.json", "position_bias_probe.json"):
        shutil.copy(run_dir / nombre, out / nombre)
    return out / "scorecard.md"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_dir", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--incluir-groq", action="store_true",
                   help="copiar el sondeo de Groq (solo si se sabe que es de esta corrida)")
    a = p.parse_args()
    print(f"Scorecard: {reanalizar(a.run_dir, a.out, a.incluir_groq)}")


if __name__ == "__main__":
    main()
