"""Guardia deterministica de citas legales inventadas.

El dataset gold (data/dataset_legal.jsonl) nunca cita normas por numero -- se
verifico por conteo directo sobre los 1536 registros del dataset reconstruido (cero coincidencias de
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
    """Toda cita es inventada: el modelo no tenia de donde sacarla.

    Vale cuando la respuesta se genero SIN contexto, que era el unico caso de
    M1 hasta el 2026-10-08. Desde que el dataset trae ejemplos con contexto
    (data/dataset_v2.jsonl), usar esta funcion ahi marca como invencion cada
    acierto: en la corrida del 2026-10-09 reporto 27.5 % de citas inventadas
    cuando el 96.7 % de las citas estaban respaldadas por el contexto.
    Para esos casos, cita_no_respaldada().
    """
    return citation_count(text) > 0


def articulos_del_contexto(contexto) -> set[str]:
    """Numeros de articulo presentes en el contexto de un ejemplo.

    contexto: lista de fragmentos como los guarda dataset_v2 (cada uno con
    'articulos'), o una lista de SearchResult del retrieval.
    """
    from tools.rag.chunk import normalizar_numero

    vistos: set[str] = set()
    for fragmento in contexto or ():
        articulos = (fragmento.get("articulos") if isinstance(fragmento, dict)
                     else getattr(fragmento, "articulos_incluidos", None))
        for a in (articulos or ()):
            vistos.add(normalizar_numero(str(a)).upper())
    return vistos


def cita_no_respaldada(text: str, contexto=None) -> bool:
    """Cita algo que no estaba en el contexto que recibio.

    Sin contexto es equivalente a has_invented_citation: cualquier cita salio
    de la memoria del modelo. Con contexto, solo cuenta lo que no estaba ahi.

    OJO al leerla: respaldada no quiere decir correcta. Comprueba procedencia,
    no pertinencia. En la corrida del 2026-10-09, los 25 casos B2 en que el
    modelo cito teniendo un contexto que NO respondia la pregunta dieron todos
    "respaldada", porque el articulo si estaba ahi; las respuestas no servian.
    Esa diferencia se mide por modo, no por registro: ver resumen_por_modo().
    """
    from tools.rag.verificacion import articulos_citados

    citados = articulos_citados(text)
    if not citados:
        return False
    if not contexto:
        return True
    return bool(citados - articulos_del_contexto(contexto))


def resumen_por_modo(registros: Sequence[dict]) -> dict[str, dict]:
    """Por modo de dataset_v2: cuantos citan y cuantos usan la frase de escape.

    Es lo que separa "cito" de "cito cuando debia". En B2 el contexto no
    responde y lo correcto es escapar: si ahi la tasa de escape es baja y la de
    citas alta, el modelo aprendio a citar pero no a abstenerse, que es como
    salio el 2026-10-09 (0 de 35 escapes, 25 de 35 citando).
    """
    from tools.evaluation.ragas_metrics import es_valvula_de_escape
    from tools.rag.verificacion import articulos_citados

    salida: dict[str, dict] = {}
    for r in registros:
        modo = r.get("modo")
        if not modo:
            continue
        d = salida.setdefault(modo, {"n": 0, "citan": 0, "escapan": 0, "no_respaldadas": 0})
        d["n"] += 1
        if articulos_citados(r.get("generated", "")):
            d["citan"] += 1
        if es_valvula_de_escape(r.get("generated", "")):
            d["escapan"] += 1
        if cita_no_respaldada(r.get("generated", ""), r.get("contexto")):
            d["no_respaldadas"] += 1
    return salida


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
