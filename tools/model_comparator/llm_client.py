"""Cliente para llamar modelos locales de Ollama via su API compatible con OpenAI.

Se reutiliza el SDK de OpenAI apuntando a la base_url local de Ollama.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI, APIConnectionError, APIError, APITimeoutError

from . import config


_clients: dict[str, OpenAI] = {}


def _get_client(provider: str) -> OpenAI:
    if provider in _clients:
        return _clients[provider]

    if provider == "ollama":
        client = OpenAI(api_key="ollama", base_url=config.OLLAMA_BASE_URL)
    else:
        raise ValueError(f"Proveedor desconocido: {provider!r}")

    _clients[provider] = client
    return client


def estimate_cost_usd(provider: str, slug: str, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
    return 0.0  # unico proveedor (Ollama local) es siempre gratis


@dataclass
class CallResult:
    text: str = ""
    latency_s: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: Optional[float] = None
    error: Optional[str] = None

    @property
    def tokens_per_s(self) -> float:
        if self.latency_s <= 0 or self.completion_tokens <= 0:
            return 0.0
        return self.completion_tokens / self.latency_s


def call_model(provider: str, slug: str, query: str, timeout_s: float = 180.0) -> CallResult:
    """Llama a un modelo con la consulta dada y devuelve metricas de la llamada.

    Nunca lanza: cualquier fallo (auth, red, modelo no descargado/inexistente,
    timeout) queda registrado en CallResult.error para que el orquestador siga
    con las demas llamadas en vez de abortar toda la corrida. timeout_s es mas
    generoso que para APIs en la nube porque un modelo local sin GPU puede
    tardar bastante en responder.
    """
    start = time.perf_counter()
    try:
        client = _get_client(provider)
        response = client.chat.completions.create(
            model=slug,
            messages=[
                {"role": "system", "content": config.SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            timeout=timeout_s,
        )
        latency = time.perf_counter() - start
        choice = response.choices[0]
        text = (choice.message.content or "").strip()
        usage = response.usage
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        cost = estimate_cost_usd(provider, slug, prompt_tokens, completion_tokens)
        return CallResult(
            text=text,
            latency_s=latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
        )
    except (APIConnectionError, APITimeoutError) as exc:
        hint = " (verifica que Ollama este corriendo: abre la app o ejecuta 'ollama serve')"
        return CallResult(latency_s=time.perf_counter() - start, error=f"Error de conexion{hint}: {exc}")
    except APIError as exc:
        hint = f" (verifica que el modelo este descargado: 'ollama pull {slug}')"
        return CallResult(latency_s=time.perf_counter() - start, error=f"Error de la API{hint}: {exc}")
    except Exception as exc:  # noqa: BLE001 - cualquier fallo del proveedor debe quedar registrado, no propagarse
        return CallResult(latency_s=time.perf_counter() - start, error=f"Error inesperado: {exc}")
