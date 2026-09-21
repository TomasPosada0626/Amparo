"""Guardia deterministica de citas legales inventadas.

El dataset gold (data/dataset_legal.jsonl) nunca cita normas por numero -- se
verifico por conteo directo sobre los 1320 registros (cero coincidencias de
los patrones de abajo; los casi-aciertos como "decreto" -- solo aparece como
el verbo "decreto la medida", nunca como "Decreto 1076" -- ya estan cubiertos
por el \\d+ obligatorio). Esto convierte cualquier coincidencia en una
respuesta GENERADA en una senal directa de norma inventada, lo cual viola el
principio duro de PRODUCT.md ("nunca debe inventar normas ni citar fuentes
inexistentes"). No verifica si la cita es real -- eso requeriria el corpus de
M3/RAG -- solo si el modelo fabrico algo con forma de cita especifica.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from tools.evaluation.generation import GenerationResult

CITATION_PATTERNS: dict[str, re.Pattern] = {
    "ley": re.compile(r"\bLey\s+\d+", re.IGNORECASE),
    "decreto": re.compile(r"\bDecreto\s+\d+", re.IGNORECASE),
    "articulo": re.compile(r"\bArt(?:i|í)culo\s+\d+", re.IGNORECASE),
    "articulo_abrev": re.compile(r"\bArt\.\s*\d+", re.IGNORECASE),
    "sentencia": re.compile(r"\bSentencia\s+(?:T|C|SU)[\s\-]?\d+", re.IGNORECASE),
    "resolucion": re.compile(r"\bResoluci(?:o|ó)n\s+\d+", re.IGNORECASE),
}


def find_citations(text: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for name, pattern in CITATION_PATTERNS.items():
        matches = [m.group(0) for m in pattern.finditer(text or "")]
        if matches:
            found[name] = matches
    return found


def citation_count(text: str) -> int:
    return sum(len(v) for v in find_citations(text).values())


def has_invented_citation(text: str) -> bool:
    return citation_count(text) > 0


@dataclass
class DomainMetricReport:
    n_total: int
    n_compliant: int
    compliance_rate_pct: float
    total_flagged_citations: int
    flagged_examples: list[tuple[int, str]] = field(default_factory=list)


def citation_report(
    rows: Sequence["GenerationResult"], max_examples: int = 20
) -> DomainMetricReport:
    n_total = len(rows)
    n_compliant = 0
    total_flagged = 0
    flagged_examples: list[tuple[int, str]] = []

    for row in rows:
        citations = find_citations(row.generated)
        count = sum(len(v) for v in citations.values())
        if count == 0:
            n_compliant += 1
        else:
            total_flagged += count
            for spans in citations.values():
                for span in spans:
                    if len(flagged_examples) < max_examples:
                        flagged_examples.append((row.id, span))

    compliance_rate_pct = (
        round(100.0 * n_compliant / n_total, 1) if n_total else 0.0
    )
    return DomainMetricReport(
        n_total=n_total,
        n_compliant=n_compliant,
        compliance_rate_pct=compliance_rate_pct,
        total_flagged_citations=total_flagged,
        flagged_examples=flagged_examples,
    )
