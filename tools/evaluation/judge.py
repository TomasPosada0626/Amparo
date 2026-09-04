"""LLM-as-a-Judge: usa el mismo modelo base (sin adaptador) ya cargado en la
sesion de Colab para calificar las respuestas generadas contra la respuesta
de referencia del dataset. Nunca lanza excepcion por un fallo de parseo --
toda falla queda registrada en JudgeScore.parse_ok/raw_output, igual que el
patron de tools/model_comparator/llm_client.py (CallResult.error).

Requiere torch/transformers (via generation.run_chat_generation) -- solo
importable/ejecutable dentro de Colab, igual que generation.py.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional, Sequence

from tools.evaluation import config, generation

JUDGE_SYSTEM_PROMPT = (
    "Eres un evaluador experto en derecho colombiano. Tu tarea es calificar, "
    "de forma objetiva y consistente, la calidad de una respuesta generada "
    "por un asistente juridico, comparandola con una respuesta de referencia "
    "aceptable. No generes texto juridico nuevo ni cites normas: solo evalua. "
    "Responde EXCLUSIVAMENTE con un objeto JSON valido, sin texto adicional "
    "antes o despues, siguiendo exactamente este formato:\n"
    '{"correccion_juridica": <entero 1-5>, "prudencia": <entero 1-5>, '
    '"claridad_utilidad": <entero 1-5>, "concision": <entero 1-5>, '
    '"justificacion": "<maximo 40 palabras>"}'
)

CRITERIA = ("correccion_juridica", "prudencia", "claridad_utilidad", "concision")

_FIELD_RE = {name: re.compile(rf'"?{name}"?\s*[:=]\s*(\d)') for name in CRITERIA}


def build_judge_prompt(query: str, reference: str, candidate: str) -> str:
    return (
        f'Consulta del usuario:\n"{query}"\n\n'
        "Respuesta de referencia (aceptable, no es la unica respuesta "
        f'valida):\n"{reference}"\n\n'
        f'Respuesta generada a evaluar:\n"{candidate}"\n\n'
        "Califica la respuesta generada en cada criterio usando una escala "
        "de 1 (muy deficiente) a 5 (excelente):\n"
        "- correccion_juridica: identifica el mecanismo o figura legal "
        "correcta y es consistente con la respuesta de referencia (no "
        "necesariamente identica en redaccion).\n"
        "- prudencia: no inventa leyes, articulos, decretos o sentencias "
        "especificas por numero; si hay incertidumbre, lo reconoce en vez "
        "de afirmar con falsa seguridad.\n"
        "- claridad_utilidad: es comprensible para alguien sin formacion "
        "juridica y orienta sobre que hacer.\n"
        "- concision: es breve, sin relleno innecesario.\n\n"
        "Responde solo con el JSON, sin explicaciones adicionales fuera del "
        "campo 'justificacion'."
    )


@dataclass
class JudgeScore:
    correccion_juridica: Optional[int]
    prudencia: Optional[int]
    claridad_utilidad: Optional[int]
    concision: Optional[int]
    justificacion: str
    composite: Optional[float]
    parse_ok: bool
    raw_output: str


def _extract_json_block(raw: str) -> Optional[dict]:
    stripped = re.sub(r"^```(?:json)?", "", raw.strip()).strip()
    stripped = re.sub(r"```$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def parse_judge_output(raw: str) -> JudgeScore:
    """Parseo en 3 niveles de fallback: (1) bloque ```json fenced -> json.loads
    directo, (2) primer {...} encontrado por regex -> json.loads, (3) regex
    por campo individual. Si ninguno produce los 4 campos validos (enteros
    1-5), parse_ok=False y composite=None -- la fila se excluye de los
    promedios pero se cuenta aparte (ver scorecard.py)."""
    data = _extract_json_block(raw) or {}

    values: dict[str, Optional[int]] = {}
    for name in CRITERIA:
        v = data.get(name)
        if v is None:
            m = _FIELD_RE[name].search(raw)
            v = m.group(1) if m else None
        try:
            v = int(v)
        except (TypeError, ValueError):
            v = None
        if v is not None and not (1 <= v <= 5):
            v = None
        values[name] = v

    justificacion = str(data.get("justificacion", "")).strip()

    if all(values[name] is not None for name in CRITERIA):
        composite = sum(values[name] for name in CRITERIA) / len(CRITERIA)
        parse_ok = True
    else:
        composite = None
        parse_ok = False

    return JudgeScore(
        correccion_juridica=values["correccion_juridica"],
        prudencia=values["prudencia"],
        claridad_utilidad=values["claridad_utilidad"],
        concision=values["concision"],
        justificacion=justificacion,
        composite=composite,
        parse_ok=parse_ok,
        raw_output=raw,
    )


def score_response(
    model,
    tokenizer,
    query: str,
    reference: str,
    candidate: str,
    max_new_tokens: int = config.MAX_NEW_TOKENS_JUDGE,
) -> JudgeScore:
    prompt = build_judge_prompt(query, reference, candidate)
    raw = generation.run_chat_generation(
        model, tokenizer, JUDGE_SYSTEM_PROMPT, prompt, max_new_tokens
    )
    return parse_judge_output(raw)


def score_batch(
    model,
    tokenizer,
    rows: Sequence["generation.GenerationResult"],
    progress_every: int = 20,
) -> list[JudgeScore]:
    import time

    total = len(rows)
    scores: list[JudgeScore] = []
    start_batch = time.perf_counter()
    for i, row in enumerate(rows, start=1):
        scores.append(
            score_response(model, tokenizer, row.query, row.expected, row.generated)
        )
        if progress_every and (i % progress_every == 0 or i == total):
            elapsed = time.perf_counter() - start_batch
            avg = elapsed / i
            eta_min = avg * (total - i) / 60
            print(
                f"[judge] {i}/{total} ({100 * i / total:.0f}%) -- "
                f"{avg:.1f}s/ejemplo, ETA ~{eta_min:.1f} min"
            )
    return scores
