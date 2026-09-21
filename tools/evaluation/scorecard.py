"""Scorecard de M2: EvalRow junta generacion + metricas clasicas + juez +
metrica de dominio en una fila por registro, y estas funciones arman el
reporte comparativo baseline vs. fine-tuned. Mismo patron
dataclass -> summarize() -> build_narrative() -> export_markdown() que
tools/model_comparator/report.py, sin libreria de templating.
"""
from __future__ import annotations

import csv
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass
class EvalRow:
    id: int
    category: str
    label: str  # "baseline" | "fine_tuned"
    query: str
    expected: str
    generated: str
    similarity_pct: Optional[float]
    exact_match: float
    token_f1: float
    bleu: float
    rouge_l_f: float
    bertscore_f1: float
    citation_count: int
    judge_correccion: Optional[int]
    judge_prudencia: Optional[int]
    judge_claridad: Optional[int]
    judge_concision: Optional[int]
    judge_composite: Optional[float]
    judge_parse_ok: bool
    latency_s: float


@dataclass
class MetricSummary:
    label: str
    n: int
    exact_match_pct: float
    avg_token_f1: float
    avg_bleu: float
    avg_rouge_l_f: float
    avg_bertscore_f1: float
    avg_similarity_pct: Optional[float]
    avg_judge_composite: Optional[float]
    stdev_judge_composite: Optional[float]
    n_judge_parse_failures: int
    citation_compliance_pct: float
    avg_latency_s: float


@dataclass
class CategorySummary:
    category: str
    label: str
    n: int
    avg_similarity_pct: Optional[float]
    avg_judge_composite: Optional[float]
    citation_compliance_pct: float


def _mean(values: list[float]) -> float:
    return round(statistics.fmean(values), 3) if values else 0.0


def summarize_by_label(rows: list[EvalRow]) -> list[MetricSummary]:
    by_label: dict[str, list[EvalRow]] = {}
    for row in rows:
        by_label.setdefault(row.label, []).append(row)

    summaries = []
    for label, label_rows in by_label.items():
        n = len(label_rows)
        similarities = [
            r.similarity_pct for r in label_rows if r.similarity_pct is not None
        ]
        judge_scores = [
            r.judge_composite for r in label_rows if r.judge_composite is not None
        ]
        n_compliant = sum(1 for r in label_rows if r.citation_count == 0)
        n_parse_failures = sum(1 for r in label_rows if not r.judge_parse_ok)

        summaries.append(MetricSummary(
            label=label,
            n=n,
            exact_match_pct=round(100.0 * _mean([r.exact_match for r in label_rows]), 1),
            avg_token_f1=_mean([r.token_f1 for r in label_rows]),
            avg_bleu=_mean([r.bleu for r in label_rows]),
            avg_rouge_l_f=_mean([r.rouge_l_f for r in label_rows]),
            avg_bertscore_f1=_mean([r.bertscore_f1 for r in label_rows]),
            avg_similarity_pct=_mean(similarities) if similarities else None,
            avg_judge_composite=_mean(judge_scores) if judge_scores else None,
            stdev_judge_composite=(
                round(statistics.pstdev(judge_scores), 3)
                if len(judge_scores) > 1 else None
            ),
            n_judge_parse_failures=n_parse_failures,
            citation_compliance_pct=round(100.0 * n_compliant / n, 1) if n else 0.0,
            avg_latency_s=_mean([r.latency_s for r in label_rows]),
        ))
    return sorted(summaries, key=lambda s: s.label)


def summarize_by_category(rows: list[EvalRow], label: str) -> list[CategorySummary]:
    by_category: dict[str, list[EvalRow]] = {}
    for row in rows:
        if row.label != label:
            continue
        by_category.setdefault(row.category, []).append(row)

    summaries = []
    for category, cat_rows in sorted(by_category.items()):
        n = len(cat_rows)
        similarities = [
            r.similarity_pct for r in cat_rows if r.similarity_pct is not None
        ]
        judge_scores = [
            r.judge_composite for r in cat_rows if r.judge_composite is not None
        ]
        n_compliant = sum(1 for r in cat_rows if r.citation_count == 0)
        summaries.append(CategorySummary(
            category=category,
            label=label,
            n=n,
            avg_similarity_pct=_mean(similarities) if similarities else None,
            avg_judge_composite=_mean(judge_scores) if judge_scores else None,
            citation_compliance_pct=round(100.0 * n_compliant / n, 1) if n else 0.0,
        ))
    return summaries


def build_narrative(
    summaries: list[MetricSummary], bias_summary: dict, n_val: int
) -> str:
    lines = [
        f"Se evaluaron {n_val} ejemplos de validacion (mismo split de M1, "
        f"seed=42, val_fraction=0.15)."
    ]
    by_label = {s.label: s for s in summaries}
    if "baseline" in by_label and "fine_tuned" in by_label:
        base, ft = by_label["baseline"], by_label["fine_tuned"]
        lines.append(
            f"Juez (compuesto 1-5): baseline {base.avg_judge_composite}, "
            f"fine-tuned {ft.avg_judge_composite}. "
            f"Similitud lexica: baseline {base.avg_similarity_pct}%, "
            f"fine-tuned {ft.avg_similarity_pct}%. "
            f"Cumplimiento de no-inventar-citas: baseline "
            f"{base.citation_compliance_pct}%, fine-tuned "
            f"{ft.citation_compliance_pct}%."
        )
        if base.n_judge_parse_failures or ft.n_judge_parse_failures:
            lines.append(
                f"Fallos de parseo del juez: baseline "
                f"{base.n_judge_parse_failures}/{base.n}, fine-tuned "
                f"{ft.n_judge_parse_failures}/{ft.n} (excluidos de los "
                f"promedios de judge_composite)."
            )
    if bias_summary:
        lines.append(
            "Sesgos: " + "; ".join(f"{k}={v}" for k, v in bias_summary.items())
        )
    return "\n\n".join(lines)


def export_markdown(
    path: Path,
    summaries: list[MetricSummary],
    category_summaries: dict[str, list[CategorySummary]],
    narrative: str,
    bias_summary: dict,
    manifest: dict,
) -> None:
    lines: list[str] = []
    lines.append("# Scorecard M2 — Evaluación del Modelo")
    lines.append("")
    lines.append(
        f"Generado: {manifest.get('timestamp', '')} · commit "
        f"`{manifest.get('git_commit', '')}` · seed "
        f"{manifest.get('random_seed', '')} · hardware: "
        f"{manifest.get('hardware', '')}"
    )
    lines.append("")
    lines.append("## Resumen por modelo")
    lines.append("")
    lines.append(
        "| Modelo | N | Exact Match | F1 | BLEU | ROUGE-L | BERTScore | "
        "Similitud (%) | Juez (1-5) | Cumplimiento citas (%) | Latencia (s) |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for s in summaries:
        lines.append(
            f"| {s.label} | {s.n} | {s.exact_match_pct}% | {s.avg_token_f1} | "
            f"{s.avg_bleu} | {s.avg_rouge_l_f} | {s.avg_bertscore_f1} | "
            f"{s.avg_similarity_pct} | {s.avg_judge_composite} | "
            f"{s.citation_compliance_pct}% | {s.avg_latency_s} |"
        )
    lines.append("")
    lines.append("## Resumen por categoría")
    lines.append("")
    for label, cats in category_summaries.items():
        lines.append(f"### {label}")
        lines.append("")
        lines.append(
            "| Categoría | N | Similitud (%) | Juez (1-5) | "
            "Cumplimiento citas (%) |"
        )
        lines.append("|---|---|---|---|---|")
        for c in cats:
            lines.append(
                f"| {c.category} | {c.n} | {c.avg_similarity_pct} | "
                f"{c.avg_judge_composite} | {c.citation_compliance_pct}% |"
            )
        lines.append("")
    lines.append("## Sesgos")
    lines.append("")
    for k, v in bias_summary.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## Conclusión")
    lines.append("")
    lines.append(narrative)
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def export_csv(path: Path, rows: list[EvalRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
