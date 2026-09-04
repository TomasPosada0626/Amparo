"""Mitigacion y medicion de sesgos del LLM-as-judge (wiki-drafts/M2.md,
seccion 5): position bias, length bias y self-preference bias.

Las funciones de sondeo (run_position_bias_probe) requieren GPU/modelo
cargado, igual que generation.py/judge.py. Las funciones de analisis
estadistico (length_bias_correlation, self_preference_gap,
judge_vs_similarity_correlation) son puro Python/numpy y si son testeables
sin GPU.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from random import Random
from typing import Optional

import numpy as np

from tools.evaluation import config, generation

PAIRWISE_JUDGE_SYSTEM_PROMPT = (
    "Eres un evaluador experto en derecho colombiano. Se te daran dos "
    "respuestas (A y B) a la misma consulta legal. Decide cual es mejor, o "
    "si estan empatadas. Responde EXCLUSIVAMENTE con un JSON valido: "
    '{"veredicto": "A"|"B"|"empate", "confianza": <entero 1-5>}'
)


def build_pairwise_prompt(query: str, response_a: str, response_b: str) -> str:
    return (
        f'Consulta del usuario:\n"{query}"\n\n'
        f'Respuesta A:\n"{response_a}"\n\n'
        f'Respuesta B:\n"{response_b}"\n\n'
        "¿Cual respuesta es mejor? Responde solo con el JSON."
    )


def _parse_pairwise_verdict(raw: str) -> Optional[str]:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return None
    veredicto = str(data.get("veredicto", "")).strip().lower()
    return veredicto if veredicto in ("a", "b", "empate") else None


@dataclass
class PositionBiasReport:
    n_pairs: int
    n_flipped: int
    n_tied_or_unparsed: int
    flip_rate_pct: float
    details: list[dict] = field(default_factory=list)


def run_position_bias_probe(
    model,
    tokenizer,
    pairs: list[tuple[int, str, str, str]],
    sample_size: int = config.POSITION_BIAS_SAMPLE_SIZE,
    seed: int = config.RANDOM_SEED,
) -> PositionBiasReport:
    """pairs: lista de (id, query, respuesta_baseline, respuesta_fine_tuned).
    Para cada par muestreado, el juez decide dos veces -- orden normal
    (A=baseline, B=fine_tuned) y orden invertido (A=fine_tuned, B=baseline).
    flip_rate_pct = % de pares comparables (sin empate/sin parseo en ninguna
    de las dos pasadas) donde el veredicto cambia solo por el orden."""
    rng = Random(seed)
    sample = pairs if len(pairs) <= sample_size else rng.sample(pairs, sample_size)

    n_flipped = 0
    n_tied_or_unparsed = 0
    details: list[dict] = []

    for record_id, query, baseline_resp, finetuned_resp in sample:
        raw_normal = generation.run_chat_generation(
            model,
            tokenizer,
            PAIRWISE_JUDGE_SYSTEM_PROMPT,
            build_pairwise_prompt(query, baseline_resp, finetuned_resp),
            config.MAX_NEW_TOKENS_PAIRWISE_JUDGE,
        )
        verdict_normal = _parse_pairwise_verdict(raw_normal)

        raw_swapped = generation.run_chat_generation(
            model,
            tokenizer,
            PAIRWISE_JUDGE_SYSTEM_PROMPT,
            build_pairwise_prompt(query, finetuned_resp, baseline_resp),
            config.MAX_NEW_TOKENS_PAIRWISE_JUDGE,
        )
        verdict_swapped = _parse_pairwise_verdict(raw_swapped)

        winner_normal = {"a": "baseline", "b": "fine_tuned"}.get(
            verdict_normal, verdict_normal
        )
        winner_swapped = {"a": "fine_tuned", "b": "baseline"}.get(
            verdict_swapped, verdict_swapped
        )

        if (
            winner_normal in (None, "empate")
            or winner_swapped in (None, "empate")
        ):
            n_tied_or_unparsed += 1
        elif winner_normal != winner_swapped:
            n_flipped += 1

        details.append({
            "id": record_id,
            "verdict_normal": winner_normal,
            "verdict_swapped": winner_swapped,
        })

    n_pairs = len(sample)
    comparable = n_pairs - n_tied_or_unparsed
    flip_rate_pct = round(100.0 * n_flipped / comparable, 1) if comparable else 0.0

    return PositionBiasReport(
        n_pairs=n_pairs,
        n_flipped=n_flipped,
        n_tied_or_unparsed=n_tied_or_unparsed,
        flip_rate_pct=flip_rate_pct,
        details=details,
    )


def length_bias_correlation(scores: list[float], lengths: list[int]) -> dict:
    """Correlacion de Pearson entre el score del juez y la longitud (en
    caracteres) de la respuesta -- un |r| alto sugiere que el juez premia
    verbosidad en vez de calidad."""
    if len(scores) < 2 or len(scores) != len(lengths):
        return {"pearson_r": None, "n": len(scores)}
    r = float(np.corrcoef(scores, lengths)[0, 1])
    return {"pearson_r": round(r, 3) if not np.isnan(r) else None, "n": len(scores)}


def normalize_judge_score(composite_1_5: float) -> float:
    return (composite_1_5 - 1) / 4


def normalize_similarity(similarity_pct: float) -> float:
    return similarity_pct / 100


@dataclass
class SelfPreferenceReport:
    judge_gap: float
    similarity_gap: float
    divergence: float
    flagged: bool


def self_preference_gap(
    judge_baseline: list[float],
    judge_finetuned: list[float],
    sim_baseline: list[float],
    sim_finetuned: list[float],
) -> SelfPreferenceReport:
    """Compara la mejora fine-tuned-vs-baseline que ve el juez (misma familia
    de modelo que el fine-tuned) contra la que ve la heuristica lexica
    independiente similarity_pct. Una divergencia grande entre ambas senales
    es evidencia de que el juez podria estar favoreciendo/penalizando por
    compartir familia de modelo, no por calidad real."""
    judge_gap = float(
        np.mean([normalize_judge_score(s) for s in judge_finetuned])
        - np.mean([normalize_judge_score(s) for s in judge_baseline])
    )
    similarity_gap = float(
        np.mean([normalize_similarity(s) for s in sim_finetuned])
        - np.mean([normalize_similarity(s) for s in sim_baseline])
    )
    divergence = judge_gap - similarity_gap
    flagged = abs(divergence) > config.SELF_PREF_DIVERGENCE_THRESHOLD
    return SelfPreferenceReport(
        judge_gap=round(judge_gap, 3),
        similarity_gap=round(similarity_gap, 3),
        divergence=round(divergence, 3),
        flagged=flagged,
    )


def judge_vs_similarity_correlation(
    judge_scores: list[float], similarity_scores: list[float]
) -> dict:
    if len(judge_scores) < 2 or len(judge_scores) != len(similarity_scores):
        return {"pearson_r": None, "n": len(judge_scores)}
    r = float(np.corrcoef(judge_scores, similarity_scores)[0, 1])
    return {
        "pearson_r": round(r, 3) if not np.isnan(r) else None,
        "n": len(judge_scores),
    }
