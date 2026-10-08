"""Fase Groq de M2 fuera de Colab, sin GPU.

La forma actual es fase_groq.py, que trabaja sobre la carpeta completa de la
corrida (la que el notebook deja en Drive) y escribe el scorecard final:

    python -m tools.evaluation.run_external_judge_local <carpeta_de_la_corrida> [--out results/m2_<fecha>]

es lo mismo que `python -m tools.evaluation.fase_groq`. Sirve para retomar al
dia siguiente cuando se acaba el cupo de Groq, desde el computador de
cualquiera del equipo: bajar la carpeta de la corrida de Drive y correr esto.

Requiere GROQ_API_KEY en tu .env local (ver .env.example). Solo necesita las
dependencias de requirements.txt -- nada de torch/transformers/peft.

load_results, build_pairs y run_eval_set_judging quedan para leer archivos de
corridas anteriores.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path



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
) -> dict:
    """Califica el eval set contra su criterio con Groq (criterio.py), igual
    que la Fase 5 del notebook. Devuelve el resumen por modelo y tipo."""
    from tools.evaluation import criterio
    from tools.evaluation import eval_set as eval_set_module

    registros = eval_set_module.load_eval_set()
    eval_baseline = load_results(eval_baseline_path)
    eval_finetuned = load_results(eval_finetuned_path)
    juez = criterio.generador_groq()
    vb = criterio.evaluar_contra_criterio(
        eval_baseline, registros, juez, checkpoint_path=out_dir / "checkpoint_criterio_baseline.jsonl")
    vf = criterio.evaluar_contra_criterio(
        eval_finetuned, registros, juez, checkpoint_path=out_dir / "checkpoint_criterio_finetuned.jsonl")

    por_id = {r["id"]: r for r in registros}
    rows = []
    for b, f, xb, xf in zip(eval_baseline, eval_finetuned, vb, vf):
        rec = por_id.get(b.id, {})
        rows.append({
            "id": b.id, "tipo": rec.get("tipo"), "category": b.category, "criterio": rec.get("criterio"),
            "query": b.query,
            "baseline": b.generated, "baseline_veredicto": xb.veredicto,
            "baseline_errores": xb.errores_juridicos, "baseline_citas": xb.n_citas,
            "fine_tuned": f.generated, "fine_tuned_veredicto": xf.veredicto,
            "fine_tuned_errores": xf.errores_juridicos, "fine_tuned_citas": xf.n_citas,
        })
        print(f"\n--- id {b.id} ({rec.get('tipo')}) {b.category} ---")
        print(f"Criterio: {rec.get('criterio')}")
        print(f"[baseline]   {b.generated}\n  -> {xb.veredicto} | errores: {xb.errores_juridicos}")
        print(f"[fine-tuned] {f.generated}\n  -> {xf.veredicto} | errores: {xf.errores_juridicos}")

    (out_dir / "groq_eval_set_resultados.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8"
    )
    resumen = criterio.resumen(vb + vf)
    (out_dir / "groq_eval_set_resumen.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nEval set (Groq, contra criterio) guardado en: {out_dir}")
    return resumen


def main() -> None:
    from tools.evaluation import fase_groq

    fase_groq.main()


if __name__ == "__main__":
    main()
