"""Corre el juez externo (Groq) fuera de Colab, sin GPU -- usa los archivos
de resultados que ya genera colab/evaluacion.ipynb en Drive (Fase 7):
`resultados_baseline.jsonl`, `resultados_finetuned.jsonl`, y opcionalmente
`eval_set_baseline_results.jsonl` / `eval_set_finetuned_results.jsonl`.

Motivo de este script: la generacion (GPU) y el juez externo (HTTP puro)
son pasos independientes. Si Groq falla o se acaba el cupo gratuito
mientras el notebook de Colab corre, no hace falta reintentar todo desde
cero en una sesion de GPU nueva -- basta con bajar esos archivos de Drive
a la maquina local y correr esto, en cualquier momento, sin GPU.

Uso:
    python -m tools.evaluation.run_external_judge_local \\
        --baseline resultados_baseline.jsonl \\
        --finetuned resultados_finetuned.jsonl \\
        --eval-set-baseline eval_set_baseline_results.jsonl \\
        --eval-set-finetuned eval_set_finetuned_results.jsonl \\
        --out results/groq_local

Requiere GROQ_API_KEY en tu .env local (ver .env.example). Solo necesita
las dependencias de requirements.txt -- nada de torch/transformers/peft.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from tools.evaluation import external_judge


@dataclass
class LoadedResult:
    id: int
    category: str
    query: str
    expected: str
    generated: str
    label: str


def load_results(path: Path) -> list[LoadedResult]:
    results: list[LoadedResult] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            results.append(LoadedResult(
                id=d["id"],
                category=d["category"],
                query=d["query"],
                expected=d["expected"],
                generated=d["generated"],
                label=d["label"],
            ))
    return results


def build_pairs(
    baseline: list[LoadedResult], finetuned: list[LoadedResult]
) -> list[tuple[int, str, str, str]]:
    """Empareja por id -- misma forma que 'pairs' en el notebook (id, query,
    respuesta_baseline, respuesta_fine_tuned). Ignora ids sin contraparte en
    ambos lados en vez de fallar, por si algun archivo quedo parcial."""
    finetuned_by_id = {r.id: r for r in finetuned}
    pairs = []
    for b in baseline:
        f = finetuned_by_id.get(b.id)
        if f is None:
            continue
        pairs.append((b.id, b.query, b.generated, f.generated))
    return pairs


def run_eval_set_judging(
    eval_baseline_path: Path, eval_finetuned_path: Path, out_dir: Path
) -> None:
    from tools.evaluation import eval_set as eval_set_module

    eval_baseline = load_results(eval_baseline_path)
    eval_finetuned = load_results(eval_finetuned_path)
    groq_eval_baseline = external_judge.score_batch(
        eval_baseline, checkpoint_path=out_dir / "checkpoint_eval_set_baseline.jsonl"
    )
    groq_eval_finetuned = external_judge.score_batch(
        eval_finetuned, checkpoint_path=out_dir / "checkpoint_eval_set_finetuned.jsonl"
    )

    criterios = {r["id"]: r for r in eval_set_module.load_eval_set()}

    rows = []
    for b, f, gb, gf in zip(eval_baseline, eval_finetuned, groq_eval_baseline, groq_eval_finetuned):
        rec = criterios.get(b.id, {})
        rows.append({
            "id": b.id,
            "tipo": rec.get("tipo"),
            "category": b.category,
            "criterio": rec.get("criterio"),
            "query": b.query,
            "baseline_generated": b.generated,
            "finetuned_generated": f.generated,
            "groq_judge_baseline": gb.composite,
            "groq_judge_finetuned": gf.composite,
        })
        print(f"\n--- id {b.id} ({rec.get('tipo')}) {b.category} ---")
        print(f"Criterio: {rec.get('criterio')}")
        print(f"[baseline]   {b.generated}\n  Groq: {gb.composite}")
        print(f"[fine-tuned] {f.generated}\n  Groq: {gf.composite}")

    (out_dir / "groq_eval_set_resultados.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8"
    )
    print(f"\nEval set (Groq) guardado en: {out_dir / 'groq_eval_set_resultados.jsonl'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--baseline", type=Path, required=True, help="resultados_baseline.jsonl")
    parser.add_argument("--finetuned", type=Path, required=True, help="resultados_finetuned.jsonl")
    parser.add_argument("--eval-set-baseline", type=Path, help="eval_set_baseline_results.jsonl (opcional)")
    parser.add_argument("--eval-set-finetuned", type=Path, help="eval_set_finetuned_results.jsonl (opcional)")
    parser.add_argument("--out", type=Path, default=Path("results/groq_local"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    baseline = load_results(args.baseline)
    finetuned = load_results(args.finetuned)
    pairs = build_pairs(baseline, finetuned)
    print(f"{len(pairs)} pares cargados para el sondeo de position bias.")

    report = external_judge.run_position_bias_probe(
        pairs, checkpoint_path=args.out / "checkpoint_position_bias.jsonl"
    )
    print(report)
    print("Conteo de veredictos:", report.winner_counts())
    (args.out / "groq_position_bias_probe.json").write_text(
        json.dumps(report.__dict__, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Guardado en: {args.out / 'groq_position_bias_probe.json'}")

    if args.eval_set_baseline and args.eval_set_finetuned:
        run_eval_set_judging(args.eval_set_baseline, args.eval_set_finetuned, args.out)


if __name__ == "__main__":
    main()
