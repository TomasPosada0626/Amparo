"""El juez de M2: Groq (openai/gpt-oss-120b), de otra familia que el Qwen2.5
evaluado. Califica TODO: la rubrica 1-5 de la validacion (judge.py), la
comparacion cara a cara en los dos ordenes (bias.py) y el eval set contra su
criterio (criterio.py). El juez local Qwen se quito: prefirio las respuestas
del baseline en 60 de 60 veredictos con el adaptador anterior (50 de 60 en la
corrida del 2026-10-02), y ese sesgo ya quedo documentado.

Reproducibilidad: temperature=0 y seed fija. gpt-oss es un modelo de
razonamiento y Groq no garantiza determinismo total ni con temperature=0, asi
que los resultados se guardan (checkpoint con huella) en vez de confiar en
poder regenerarlos identicos.

Cupo. La capa gratuita de gpt-oss-120b da 1 000 solicitudes y 200 000 tokens
al dia (8 000 por minuto). Lo que limita son los tokens: cada llamada gasta
~1 000-1 500 (prompt, razonamiento y JSON), asi que entran ~150-200 llamadas al
dia y una corrida completa (~1 000 llamadas) toma ~5-7 dias con una sola key.
Ante un 429 por minuto se espera lo que Groq indica y se reintenta; ante el
limite diario se lanza CupoAgotado, con todo lo hecho ya guardado en el
checkpoint, y la corrida se retoma otro dia (desde Colab o con fase_groq.py,
sin GPU).

Requiere GROQ_API_KEY (secreto de Colab, o .env local). No requiere GPU ni
torch: es HTTP puro.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Optional, Sequence

from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APIError, APITimeoutError, RateLimitError

from tools.evaluation import config
from tools.evaluation.bias import (
    PositionBiasReport,
    _run_position_bias_probe_core,
)
from tools.evaluation.checkpoint import append_checkpoint, huella, load_checkpoint, sin_metadatos
from tools.evaluation.judge import (
    JUDGE_PROMPT_VERSION,
    JUDGE_SYSTEM_PROMPT,
    JudgeScore,
    build_judge_prompt,
    parse_judge_output,
)

load_dotenv(config.PROJECT_ROOT / ".env")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_JUDGE_MODEL = os.environ.get("GROQ_JUDGE_MODEL", "openai/gpt-oss-120b").strip()

# openai/gpt-oss-120b es un modelo de RAZONAMIENTO: antes de escribir la
# respuesta final gasta una parte del presupuesto de tokens "pensando". Con
# los mismos max_tokens que usa el juez local (100-200) se quedaba sin
# tokens ANTES de llegar a escribir el JSON -- confirmado en una corrida
# real: 100% de las respuestas (position bias y eval set) volvieron
# composite=None, sin ningun error de API de por medio (la llamada
# "tenia exito", solo que el contenido nunca llegaba a la parte util).
# reasoning_effort="low" reduce cuanto "piensa"; los limites de abajo dan
# margen de sobra incluso con reasoning_effort="low". Si mas adelante se
# usa un modelo que NO sea de razonamiento, reasoning_effort se ignora sin
# problema (Groq lo acepta como no-op para modelos que no lo soportan).
GROQ_REASONING_EFFORT = os.environ.get("GROQ_REASONING_EFFORT", "low").strip() or None
# 800 y no 600: la rubrica ahora tambien pide la lista de errores juridicos,
# igual que el juez del criterio (criterio.MAX_TOKENS_CRITERIO = 700).
GROQ_MAX_TOKENS_JUDGE = int(os.environ.get("GROQ_MAX_TOKENS_JUDGE", "800"))
GROQ_MAX_TOKENS_PAIRWISE = int(os.environ.get("GROQ_MAX_TOKENS_PAIRWISE", "400"))
GROQ_TEMPERATURE = float(os.environ.get("GROQ_TEMPERATURE", "0"))
GROQ_SEED = int(os.environ.get("GROQ_SEED", str(config.RANDOM_SEED)))

# Un 429 que pide esperar mas que esto es el limite diario: no se espera.
MAX_ESPERA_RATE_LIMIT_S = 90.0
MAX_REINTENTOS_RATE_LIMIT = 8
ESPERA_SIN_RETRY_AFTER_S = 20.0
# gpt-oss gasta parte de max_tokens razonando; si se los acaba antes de escribir
# la respuesta, el contenido llega vacio (finish_reason="length"). Se reintenta
# una vez con este multiplo, en vez de volver a pagar el mismo fallo en cada
# reanudacion.
FACTOR_REINTENTO_SIN_CONTENIDO = 2

_client: Optional[OpenAI] = None


class CupoAgotado(RuntimeError):
    """Groq agoto el cupo diario. Lo ya calificado esta en el checkpoint:
    volver a correr la misma celda (o run_external_judge_local.py) despues del
    reinicio del cupo retoma donde quedo."""


def _espera_sugerida(exc: RateLimitError) -> Optional[float]:
    try:
        valor = exc.response.headers.get("retry-after")
        return float(valor) if valor is not None else None
    except (AttributeError, TypeError, ValueError):
        return None


_LIMITE_DIARIO = re.compile(r"per day|\((?:tpd|rpd)\)")


def _es_limite_diario(exc: RateLimitError) -> bool:
    # Groq: "... on tokens per day (TPD): Limit 200000, Used ..."
    return bool(_LIMITE_DIARIO.search(str(exc).lower()))


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Falta GROQ_API_KEY en el .env (ver .env.example) -- genera "
                "una gratis en https://console.groq.com/keys"
            )
        # max_retries=0: los 429 se manejan aqui (call_groq), distinguiendo el
        # limite por minuto (se espera) del diario (se para).
        _client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL, max_retries=0)
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
    el usuario se entere de por que todo el lote fallo.

    Tampoco ante el limite diario de Groq: lanza CupoAgotado. Seguir
    llamando solo devolveria "" en cada fila restante. El limite por minuto
    se espera y se reintenta."""
    client = _get_client()
    kwargs = dict(
        model=GROQ_JUDGE_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_tokens=max_tokens,
        timeout=timeout_s,
        temperature=GROQ_TEMPERATURE,
        seed=GROQ_SEED,
    )
    if GROQ_REASONING_EFFORT:
        kwargs["reasoning_effort"] = GROQ_REASONING_EFFORT
    ampliado = False
    for _ in range(MAX_REINTENTOS_RATE_LIMIT):
        try:
            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            contenido = (choice.message.content or "").strip()
            if not contenido and getattr(choice, "finish_reason", None) == "length" and not ampliado:
                ampliado = True
                kwargs["max_tokens"] = max_tokens * FACTOR_REINTENTO_SIN_CONTENIDO
                print(f"[external_judge] sin contenido (razonamiento agoto {max_tokens} tokens): "
                      f"reintento con {kwargs['max_tokens']}")
                continue
            return contenido
        except RateLimitError as exc:
            espera = _espera_sugerida(exc)
            if _es_limite_diario(exc) or (espera is not None and espera > MAX_ESPERA_RATE_LIMIT_S):
                raise CupoAgotado(
                    f"Groq agoto el cupo (espera sugerida: {espera} s). Lo calificado ya esta en el "
                    f"checkpoint; vuelve a correr cuando se reinicie el cupo. Detalle: {exc}"
                ) from exc
            espera = ESPERA_SIN_RETRY_AFTER_S if espera is None else espera
            print(f"[external_judge] limite por minuto: espero {espera:.0f} s")
            time.sleep(espera + 1)
        except (APIConnectionError, APITimeoutError, APIError) as exc:
            print(f"[external_judge] error de API Groq: {exc}")
            return ""
        except Exception as exc:  # noqa: BLE001 - nunca debe abortar un lote
            print(f"[external_judge] error inesperado: {exc}")
            return ""
    # 429 tras 429 sin que Groq diga que es el diario: igual es cupo, no ruido.
    raise CupoAgotado(f"Groq siguio respondiendo 429 tras {MAX_REINTENTOS_RATE_LIMIT} intentos. Lo "
                      "calificado ya esta en el checkpoint; vuelve a correr mas tarde.")


def score_response(
    query: str,
    reference: str,
    candidate: str,
    max_tokens: int = GROQ_MAX_TOKENS_JUDGE,
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
    interrumpida por un rate limit, por ejemplo), se reusan solo las filas
    con el MISMO texto (huella, ver checkpoint.py), sin volver a gastar cupo."""
    huellas = {row.id: huella(JUDGE_PROMPT_VERSION, row.query, row.expected, row.generated) for row in rows}
    done = load_checkpoint(checkpoint_path, huellas, log_prefix="external_judge")

    total = len(rows)
    scores: list[JudgeScore] = []
    start_batch = time.perf_counter()
    for i, row in enumerate(rows, start=1):
        if row.id in done:
            score = JudgeScore(**sin_metadatos(done[row.id]))
        else:
            score = score_response(row.query, row.expected, row.generated)
            if score.parse_ok:   # sin respuesta de Groq (cupo, red) o ilegible: se reintenta al retomar
                append_checkpoint(checkpoint_path, {"id": row.id, "huella": huellas[row.id], **score.__dict__})
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


def comparar_cara_a_cara(
    pairs: list[tuple[int, str, str, str]],
    sample_size: Optional[int] = config.PAIRWISE_SAMPLE_SIZE,
    seed: int = config.RANDOM_SEED,
    progress_every: int = 10,
    checkpoint_path: Optional[Path] = None,
) -> PositionBiasReport:
    """Comparacion cara a cara baseline vs. fine-tuned, cada par en los dos
    ordenes (bias._run_position_bias_probe_core). La cifra oficial es
    report.veredicto_consistente(): gana un modelo solo si gana en ambos
    ordenes. sample_size=None (por defecto) juzga todos los pares.

    checkpoint_path: evita repetir pares ya resueltos si la corrida se corto
    (cupo de Groq, desconexion)."""

    def generate_fn(system_prompt: str, user_content: str, max_tokens: int) -> str:
        return call_groq(system_prompt, user_content, max_tokens)

    return _run_position_bias_probe_core(
        generate_fn,
        pairs,
        sample_size,
        seed,
        progress_every,
        max_tokens=GROQ_MAX_TOKENS_PAIRWISE,
        log_prefix="external_judge cara_a_cara",
        checkpoint_path=checkpoint_path,
    )


# Nombre anterior, para el script local y corridas viejas.
run_position_bias_probe = comparar_cara_a_cara
