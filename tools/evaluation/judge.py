"""LLM-as-a-Judge: rubrica 1-5, prompt y parseo del juez de M2.

Quien llama al juez es external_judge.py (Groq, openai/gpt-oss-120b). Antes
habia aqui un juez local con el mismo Qwen2.5-7B que se evalua, y se quito: es
de la misma familia que el modelo evaluado y prefirio las respuestas del
baseline en 60 de 60 veredictos cara a cara con el adaptador anterior (50 de 60
en la corrida del 2026-10-02). Ese sesgo ya quedo documentado; seguir
corriendolo solo gastaba GPU.

Nunca lanza excepcion por un fallo de parseo: toda falla queda registrada en
JudgeScore.parse_ok/raw_output.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

# Cambia cuando cambia el prompt: entra en la huella del checkpoint, para que un
# puntaje dado con un prompt anterior nunca se reuse con el nuevo.
JUDGE_PROMPT_VERSION = "2026-10-06"

JUDGE_SYSTEM_PROMPT = (
    "Eres un evaluador experto en derecho colombiano. Tu tarea es calificar, "
    "de forma objetiva y consistente, la calidad de una respuesta generada "
    "por un asistente juridico, comparandola con una respuesta de referencia "
    "aceptable. No generes texto juridico nuevo ni cites normas: solo evalua. "
    "La extension no es merito: una respuesta mas larga no es mejor por serlo. "
    "Responde EXCLUSIVAMENTE con un objeto JSON valido, sin texto adicional "
    "antes o despues, siguiendo exactamente este formato:\n"
    '{"correccion_juridica": <entero 1-5>, "prudencia": <entero 1-5>, '
    '"claridad_utilidad": <entero 1-5>, "concision": <entero 1-5>, '
    '"errores_juridicos": ["<afirmacion falsa o entidad equivocada>", ...], '
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
        "correcta, la dirige a la entidad o autoridad que de verdad tramita ese "
        "caso, y es consistente con la respuesta de referencia (no "
        "necesariamente identica en redaccion). Una entidad que existe pero no "
        "tramita ese caso, o una figura de otra rama del derecho (por ejemplo, "
        "una querella ante la Procuraduria, una demanda ante un comisario o un "
        "inspector, el juez de control de garantias fuera del proceso penal, una "
        "conciliacion de deudas en la Comisaria de Familia), es un error "
        "juridico grave: correccion_juridica 1 o 2, aunque el resto sea bueno. "
        "Una entidad que no existe, igual.\n"
        "- prudencia: no inventa leyes, articulos, decretos o sentencias "
        "especificas por numero; si hay incertidumbre, lo reconoce en vez "
        "de afirmar con falsa seguridad.\n"
        "- claridad_utilidad: es comprensible para alguien sin formacion "
        "juridica y orienta sobre que hacer.\n"
        "- concision: es breve, sin relleno innecesario. Es el unico criterio "
        "donde cuenta la extension: en los otros tres, no premies ni castigues "
        "el largo.\n\n"
        "errores_juridicos: lista cada afirmacion concreta que sea falsa en el "
        "derecho colombiano y cada entidad, autoridad o procedimiento equivocado "
        "para el caso o inexistente. No cuentes como error lo que solo esta "
        "incompleto. Lista vacia si no hay errores.\n\n"
        "Responde solo con el JSON, sin explicaciones adicionales fuera de los "
        "campos 'errores_juridicos' y 'justificacion'."
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
    errores_juridicos: list[str] = field(default_factory=list)


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


def _normalize_key(s: str) -> str:
    """NFKD + quitar diacriticos + minusculas -- para que 'concisión' (el
    modelo a veces usa ortografia correcta con tilde) coincida con la
    clave pedida en el prompt, 'concision' (sin tilde). Confirmado en una
    corrida real contra Groq (openai/gpt-oss-120b): el JSON llegaba
    completo y valido, pero con esa unica clave tildada, y por eso se
    perdia el 100% de las filas antes de este fix."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower().strip()


def parse_judge_output(raw: str) -> JudgeScore:
    """Parseo en 3 niveles de fallback: (1) bloque ```json fenced -> json.loads
    directo, (2) primer {...} encontrado por regex -> json.loads, (3) regex
    por campo individual. Si ninguno produce los 4 campos validos (enteros
    1-5), parse_ok=False y composite=None -- la fila se excluye de los
    promedios pero se cuenta aparte (ver scorecard.py). Las claves del JSON
    (y el texto crudo, para el fallback por regex) se normalizan sin
    acentos antes de buscarlas."""
    raw_data = _extract_json_block(raw) or {}
    data = {_normalize_key(k): v for k, v in raw_data.items()}
    normalized_raw = _normalize_key(raw)

    values: dict[str, Optional[int]] = {}
    for name in CRITERIA:
        v = data.get(name)
        if v is None:
            m = _FIELD_RE[name].search(normalized_raw)
            v = m.group(1) if m else None
        try:
            v = int(v)
        except (TypeError, ValueError):
            v = None
        if v is not None and not (1 <= v <= 5):
            v = None
        values[name] = v

    justificacion = str(data.get("justificacion", "")).strip()
    errores = data.get("errores_juridicos") or []
    if isinstance(errores, str):
        errores = [errores] if errores.strip() else []
    errores = [str(e).strip() for e in errores if str(e).strip()] if isinstance(errores, list) else []

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
        errores_juridicos=errores,
    )
