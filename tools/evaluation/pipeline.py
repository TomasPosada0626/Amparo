"""Orquestador: junta generacion + metricas clasicas + juez + metrica de
dominio en filas EvalRow, y construye el manifiesto de reproducibilidad de
la corrida. El notebook de Colab llama estas funciones fase por fase (ver
colab/evaluacion.ipynb) despues de generar y calificar cada lote.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from typing import Sequence

from tools.evaluation import config, domain_metric, metrics_classic
from tools.evaluation.generation import GenerationResult
from tools.evaluation.judge import JudgeScore
from tools.evaluation.scorecard import EvalRow

try:
    from tools.model_comparator.metrics import similarity_pct
except ImportError:  # pragma: no cover - model_comparator siempre deberia existir
    similarity_pct = None  # type: ignore


LIBRARIES_TO_TRACK = [
    "transformers", "peft", "torch", "sacrebleu", "rouge-score", "bert-score",
]


@dataclass
class RunManifest:
    git_commit: str
    random_seed: int
    val_fraction: float
    n_val: int
    base_model_id: str
    adapter_dir: str
    library_versions: dict[str, str] = field(default_factory=dict)
    hardware: str = ""
    timestamp: str = ""


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=config.PROJECT_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def _library_versions() -> dict[str, str]:
    versions = {}
    for lib in LIBRARIES_TO_TRACK:
        try:
            versions[lib] = importlib_metadata.version(lib)
        except importlib_metadata.PackageNotFoundError:
            versions[lib] = "not-installed"
    return versions


def build_manifest(
    n_val: int, hardware: str = "", adapter_dir: str = config.DRIVE_ADAPTER_DIR
) -> RunManifest:
    return RunManifest(
        git_commit=_git_commit(),
        random_seed=config.RANDOM_SEED,
        val_fraction=config.VAL_FRACTION,
        n_val=n_val,
        base_model_id=config.BASE_MODEL_ID,
        adapter_dir=adapter_dir,
        library_versions=_library_versions(),
        hardware=hardware,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def build_eval_rows(
    generations: Sequence[GenerationResult],
    judge_scores: Sequence[JudgeScore],
) -> list[EvalRow]:
    """Junta, en el mismo orden, las respuestas generadas con sus
    puntuaciones del juez, y calcula ahi mismo las metricas clasicas (salvo
    BERTScore, que se completa despues en batch via fill_bertscore -- es mas
    eficiente calcularlo por lotes que fila por fila)."""
    if len(generations) != len(judge_scores):
        raise ValueError(
            "generations y judge_scores deben tener el mismo largo y orden"
        )

    rows: list[EvalRow] = []
    for gen, jscore in zip(generations, judge_scores):
        sim = similarity_pct(gen.expected, gen.generated) if similarity_pct else None
        rouge = metrics_classic.rouge_l(gen.expected, gen.generated)
        rows.append(EvalRow(
            id=gen.id,
            category=gen.category,
            label=gen.label,
            query=gen.query,
            expected=gen.expected,
            generated=gen.generated,
            similarity_pct=sim,
            exact_match=metrics_classic.exact_match(gen.expected, gen.generated),
            token_f1=metrics_classic.token_f1(gen.expected, gen.generated),
            bleu=metrics_classic.bleu(gen.expected, gen.generated),
            rouge_l_f=rouge["fmeasure"],
            bertscore_f1=0.0,
            citation_count=domain_metric.citation_count(gen.generated),
            judge_correccion=jscore.correccion_juridica,
            judge_prudencia=jscore.prudencia,
            judge_claridad=jscore.claridad_utilidad,
            judge_concision=jscore.concision,
            judge_composite=jscore.composite,
            judge_parse_ok=jscore.parse_ok,
            latency_s=gen.latency_s,
        ))
    return rows


def fill_bertscore(rows: list[EvalRow]) -> None:
    """Completa EvalRow.bertscore_f1 en batch (mucho mas eficiente que
    llamarlo fila por fila). Modifica rows en el lugar."""
    if not rows:
        return
    expected = [r.expected for r in rows]
    actual = [r.generated for r in rows]
    scores = metrics_classic.bertscore_f1_batch(expected, actual)
    for row, score in zip(rows, scores):
        row.bertscore_f1 = score
