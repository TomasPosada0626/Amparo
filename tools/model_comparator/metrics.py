"""Metricas para comparar respuestas de modelos."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Optional


def similarity_pct(expected: Optional[str], actual: str) -> Optional[float]:
    """Similitud textual aproximada (0-100) entre la respuesta esperada y la generada.

    Es una heuristica lexica (difflib), no una metrica semantica/juridica: sirve
    para ordenar y comparar modelos rapidamente, no como evaluacion rigurosa de
    correccion legal (eso queda para el harness LLM-as-a-Judge de M2).
    """
    if not expected or not actual:
        return None
    ratio = SequenceMatcher(None, expected.strip().lower(), actual.strip().lower()).ratio()
    return round(ratio * 100, 1)
