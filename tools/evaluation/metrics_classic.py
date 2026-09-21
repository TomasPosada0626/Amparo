"""Metricas clasicas de evaluacion: Exact Match, F1 tipo SQuAD, BLEU,
ROUGE-L y BERTScore.

Exact Match, F1, BLEU y ROUGE-L se calculan sobre texto normalizado
(normalize_text): el dataset gold es casi enteramente sin tildes, mientras
que el modelo base (sin fine-tuning) va a responder con ortografia espanola
normal -- sin normalizar, estas metricas penalizarian al baseline por forma
superficial, no por contenido juridico. BERTScore se calcula sobre texto
crudo porque el embedding es menos sensible a diacriticos.
"""
from __future__ import annotations

import unicodedata
from collections import Counter

import sacrebleu
from rouge_score import rouge_scorer

from tools.evaluation import config

_rouge_scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().split())


def exact_match(expected: str, actual: str) -> float:
    return 1.0 if normalize_text(expected) == normalize_text(actual) else 0.0


def token_f1(expected: str, actual: str) -> float:
    exp_tokens = normalize_text(expected).split()
    act_tokens = normalize_text(actual).split()
    if not exp_tokens or not act_tokens:
        return 0.0
    common = Counter(exp_tokens) & Counter(act_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = num_same / len(act_tokens)
    recall = num_same / len(exp_tokens)
    return 2 * precision * recall / (precision + recall)


def bleu(expected: str, actual: str) -> float:
    exp_norm = normalize_text(expected)
    act_norm = normalize_text(actual)
    if not exp_norm or not act_norm:
        return 0.0
    return sacrebleu.sentence_bleu(act_norm, [exp_norm]).score


def rouge_l(expected: str, actual: str) -> dict[str, float]:
    exp_norm = normalize_text(expected)
    act_norm = normalize_text(actual)
    if not exp_norm or not act_norm:
        return {"precision": 0.0, "recall": 0.0, "fmeasure": 0.0}
    scores = _rouge_scorer.score(exp_norm, act_norm)["rougeL"]
    return {
        "precision": scores.precision,
        "recall": scores.recall,
        "fmeasure": scores.fmeasure,
    }


def bertscore_f1_batch(
    expected: list[str],
    actual: list[str],
    model_type: str = config.BERTSCORE_MODEL,
    batch_size: int = 32,
) -> list[float]:
    """Requiere el paquete bert-score (pesado, solo se importa aqui adentro
    para no forzar la dependencia en modulos que no la necesitan)."""
    from bert_score import score as bert_score_fn

    try:
        _, _, f1 = bert_score_fn(
            actual,
            expected,
            model_type=model_type,
            num_layers=config.BERTSCORE_NUM_LAYERS,
            lang="es",
            rescale_with_baseline=False,
            batch_size=batch_size,
            verbose=False,
        )
    except Exception:
        # Respaldo si el backbone no esta en la tabla model2layers de la
        # libreria: usa el default multilingue de bert-score para "es".
        _, _, f1 = bert_score_fn(
            actual,
            expected,
            lang="es",
            rescale_with_baseline=False,
            batch_size=batch_size,
            verbose=False,
        )
    return [round(float(v) * 100, 2) for v in f1]
