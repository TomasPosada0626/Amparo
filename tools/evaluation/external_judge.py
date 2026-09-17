"""Juez externo (Groq) para LLM-as-a-Judge -- familia de modelo distinta a
Qwen2.5 (el modelo evaluado y el juez local de judge.py). Reutiliza el mismo
prompt/rubrica/parseo que judge.py y bias.py; solo cambia el backend de
generacion: llamada HTTP a la API de Groq (compatible con OpenAI) en vez de
generacion local con GPU.

Motivo: el sondeo de position bias con el juez local (misma familia que el
modelo evaluado) mostro que, en los 30 pares probados, el juez prefirio la
respuesta baseline las 60 veces (ver bias.PositionBiasReport.winner_counts) --
evidencia de auto-preferencia. Este modulo permite repetir la misma
evaluacion con un juez independiente para ver si el patron se sostiene.

Requiere GROQ_API_KEY en el .env (ver .env.example) -- capa gratuita de
Groq, sin costo. No requiere GPU ni torch: es HTTP puro, corre igual en
Colab o en local.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional, Sequence

from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APIError, APITimeoutError

from tools.evaluation import config
from tools.evaluation.bias import (
    PositionBiasReport,
    _run_position_bias_probe_core,
)
from tools.evaluation.checkpoint import append_checkpoint, load_checkpoint
from tools.evaluation.judge import JUDGE_SYSTEM_PROMPT, JudgeScore, build_judge_prompt, parse_judge_output

load_dotenv(config.PROJECT_ROOT / ".env")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_JUDGE_MODEL = os.environ.get("GROQ_JUDGE_MODEL", "openai/gpt-oss-120b").strip()

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Falta GROQ_API_KEY en el .env (ver .env.example) -- genera "
                "una gratis en https://console.groq.com/keys"
            )
        _client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
    return _client


def call_groq(
    system_prompt: str, user_content: str, max_tokens: int, timeout_s: float = 60.0
) -> str:
    """Resiliente ante fallos POR LLAMADA (red, rate limit, timeout): esos
    devuelven un string vacio en vez de propagar la excepcion, igual que el
    patron 'never raise' de tools/model_comparator/llm_client.py, para que
    un lote largo siga corriendo aunque falle un llamado puntual.

    NO resiliente ante GROQ_API_KEY ausente/invalida: eso es un error de
    configuracion, no un fallo transitorio -- se deja que _get_client()
    propague el RuntimeError de inmediato (falla rapido en la primera
    llamada) en vez de tragarselo y devolver "" 200+ veces seguidas sin que
    el usuario se entere de por que todo el lote fallo."""
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=GROQ_JUDGE_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=max_tokens,
            timeout=timeout_s,
        )
        return (response.choices[0].message.content or "").strip()
    except (APIConnectionError, APITimeoutError, APIError) as exc:
        print(f"[external_judge] error de API Groq: {exc}")
        return ""
    except Exception as exc:  # noqa: BLE001 - nunca debe abortar un lote
        print(f"[external_judge] error inesperado: {exc}")
        return ""


def score_response(
    query: str,
    reference: str,
    candidate: str,
    max_tokens: int = config.MAX_NEW_TOKENS_JUDGE,
) -> JudgeScore:
    prompt = build_judge_prompt(query, reference, candidate)
    raw = call_groq(JUDGE_SYSTEM_PROMPT, prompt, max_tokens)
    return parse_judge_output(raw)


def score_batch(
    rows: Sequence,
    progress_every: int = 5,
    checkpoint_path: Optional[Path] = None,
) -> list[JudgeScore]:
    """rows: cualquier secuencia de objetos con .id/.query/.expected/.generated
    (generation.GenerationResult o LoadedResult de run_external_judge_local.py).

    checkpoint_path (opcional): JSONL donde se guarda cada resultado a
    medida que se calcula. Si el archivo ya existe (de una corrida
    interrumpida por un rate limit, por ejemplo), las filas cuyo id ya
    este ahi se saltan en vez de volver a gastar cupo calificandolas."""
    done = load_checkpoint(checkpoint_path)
    if done:
        print(f"[external_judge] checkpoint: {len(done)} filas ya resueltas, se saltan.")

    total = len(rows)
    scores: list[JudgeScore] = []
    start_batch = time.perf_counter()
    for i, row in enumerate(rows, start=1):
        if row.id in done:
            entry = dict(done[row.id])
            entry.pop("id")
            score = JudgeScore(**entry)
        else:
            score = score_response(row.query, row.expected, row.generated)
            append_checkpoint(checkpoint_path, {"id": row.id, **score.__dict__})
        scores.append(score)
        if progress_every and (i % progress_every == 0 or i == total):
            elapsed = time.perf_counter() - start_batch
            avg = elapsed / i
            eta_min = avg * (total - i) / 60
            print(
                f"[external_judge] {i}/{total} ({100 * i / total:.0f}%) -- "
                f"{avg:.1f}s/ejemplo, ETA ~{eta_min:.1f} min"
            )
    return scores


def run_position_bias_probe(
    pairs: list[tuple[int, str, str, str]],
    sample_size: int = config.POSITION_BIAS_SAMPLE_SIZE,
    seed: int = config.RANDOM_SEED,
    progress_every: int = 5,
    checkpoint_path: Optional[Path] = None,
) -> PositionBiasReport:
    """Mismo metodo que bias.run_position_bias_probe (nucleo compartido,
    ver bias._run_position_bias_probe_core) pero con Groq como backend en
    vez de un modelo local -- para contrastar si el patron de preferencia
    observado con el juez Qwen (misma familia) se sostiene con un juez de
    familia distinta.

    checkpoint_path (opcional): ver _run_position_bias_probe_core -- evita
    repetir pares ya resueltos si una corrida anterior se corto (p. ej. por
    rate limit de Groq)."""

    def generate_fn(system_prompt: str, user_content: str, max_tokens: int) -> str:
        return call_groq(system_prompt, user_content, max_tokens)

    return _run_position_bias_probe_core(
        generate_fn,
        pairs,
        sample_size,
        seed,
        progress_every,
        max_tokens=100,
        log_prefix="external_judge position_bias",
        checkpoint_path=checkpoint_path,
    )
