"""Agregacion de resultados por modelo y generacion del informe de conclusion."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .run_manager import RunResult


@dataclass
class ModelSummary:
    model_id: str
    model_label: str
    n_calls: int
    n_errors: int
    avg_latency_s: float
    avg_tokens_per_s: float
    avg_similarity: Optional[float]
    stdev_similarity: Optional[float]
    total_cost_usd: Optional[float]


def summarize(results: list[RunResult]) -> list[ModelSummary]:
    by_model: dict[str, list[RunResult]] = {}
    for r in results:
        by_model.setdefault(r.model_id, []).append(r)

    summaries: list[ModelSummary] = []
    for model_id, rows in by_model.items():
        label = rows[0].model_label
        ok_rows = [r for r in rows if not r.error]
        errors = [r for r in rows if r.error]
        sims = [r.similarity for r in ok_rows if r.similarity is not None]
        costs = [r.cost_usd for r in ok_rows if r.cost_usd is not None]
        summaries.append(
            ModelSummary(
                model_id=model_id,
                model_label=label,
                n_calls=len(rows),
                n_errors=len(errors),
                avg_latency_s=statistics.fmean(r.latency_s for r in ok_rows) if ok_rows else 0.0,
                avg_tokens_per_s=statistics.fmean(r.tokens_per_s for r in ok_rows) if ok_rows else 0.0,
                avg_similarity=statistics.fmean(sims) if sims else None,
                stdev_similarity=statistics.pstdev(sims) if len(sims) > 1 else None,
                total_cost_usd=sum(costs) if costs else None,
            )
        )

    # Orden: primero por similitud promedio (si existe) desc, luego por velocidad desc.
    summaries.sort(
        key=lambda s: (
            -(s.avg_similarity if s.avg_similarity is not None else -1),
            -s.avg_tokens_per_s,
        )
    )
    return summaries


def build_narrative(summaries: list[ModelSummary], source_desc: str, passes: int, n_queries: int) -> str:
    if not summaries:
        return "No hay resultados para resumir."

    has_quality = any(s.avg_similarity is not None for s in summaries)
    lines = [
        f"Se compararon {len(summaries)} modelo(s) sobre {n_queries} consulta(s) "
        f"({source_desc}), con {passes} pasada(s) por consulta."
    ]

    if has_quality:
        best_quality = max(
            (s for s in summaries if s.avg_similarity is not None), key=lambda s: s.avg_similarity
        )
        lines.append(
            f"Mejor similitud promedio con la respuesta esperada: {best_quality.model_label} "
            f"({best_quality.avg_similarity:.1f}%)."
        )

    if any(s.avg_tokens_per_s > 0 for s in summaries):
        fastest = max(summaries, key=lambda s: s.avg_tokens_per_s)
        lines.append(
            f"Modelo mas rapido (tokens/s promedio): {fastest.model_label} "
            f"({fastest.avg_tokens_per_s:.1f} tok/s)."
        )

    consistent_candidates = [s for s in summaries if s.stdev_similarity is not None]
    if consistent_candidates:
        most_consistent = min(consistent_candidates, key=lambda s: s.stdev_similarity)
        lines.append(
            f"Modelo con respuestas mas consistentes en calidad (menor dispersion de similitud "
            f"entre las respuestas evaluadas): {most_consistent.model_label} "
            f"(desviacion {most_consistent.stdev_similarity:.1f} pp)."
        )

    priced = [s for s in summaries if s.total_cost_usd is not None]
    if priced:
        cheapest = min(priced, key=lambda s: s.total_cost_usd)
        lines.append(
            f"Menor costo total estimado en esta corrida: {cheapest.model_label} "
            f"(${cheapest.total_cost_usd:.4f} USD)."
        )

    errored = [s for s in summaries if s.n_errors > 0]
    if errored:
        detail = ", ".join(f"{s.model_label} ({s.n_errors}/{s.n_calls})" for s in errored)
        lines.append(f"Modelos con errores en algunas llamadas: {detail}. Revisa el detalle exportado.")

    top = summaries[0]
    if has_quality:
        lines.append(
            f"Recomendacion preliminar segun este estudio: {top.model_label} combina la mejor "
            "similitud con la respuesta esperada y buen desempeno. Esta similitud es una heuristica "
            "lexica (no una evaluacion juridica rigurosa); contrastala con licencia, tamano y "
            "requisitos computacionales antes de confirmar un modelo base (ver M1 en la wiki)."
        )
    else:
        lines.append(
            f"No se cargaron respuestas esperadas, asi que esta corrida solo mide desempeno: "
            f"{top.model_label} quedo primero segun velocidad/consistencia. Para evaluar calidad "
            "de contenido juridico, revisa las respuestas manualmente o vuelve a correr con un "
            "dataset que incluya 'Salida esperada'."
        )

    return "\n\n".join(lines)


def export_markdown(
    path: Path,
    summaries: list[ModelSummary],
    narrative: str,
    source_desc: str,
    passes: int,
    n_queries: int,
) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Informe de comparacion de modelos - Amparo",
        "",
        f"Generado: {ts}",
        f"Fuente de consultas: {source_desc}",
        f"Consultas: {n_queries} | Pasadas por consulta: {passes}",
        "",
        "## Resumen por modelo",
        "",
        "| Modelo | Llamadas | Errores | Similitud prom. (%) | Desv. similitud | Tokens/s prom. | Costo total (USD) |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in summaries:
        lines.append(
            "| {label} | {n} | {err} | {sim} | {dev} | {tps:.1f} | {cost} |".format(
                label=s.model_label,
                n=s.n_calls,
                err=s.n_errors,
                sim=f"{s.avg_similarity:.1f}" if s.avg_similarity is not None else "N/A",
                dev=f"{s.stdev_similarity:.1f}" if s.stdev_similarity is not None else "N/A",
                tps=s.avg_tokens_per_s,
                cost=f"{s.total_cost_usd:.4f}" if s.total_cost_usd is not None else "N/A",
            )
        )
    lines += ["", "## Conclusion", "", narrative, ""]
    path.write_text("\n".join(lines), encoding="utf-8")
