"""Sesgos del LLM-as-judge y como se controlan en M2.

- Familia (auto-preferencia): el juez es Groq (openai/gpt-oss-120b), de otra
  familia que el Qwen2.5 evaluado y que no escribio ninguna respuesta. El juez
  local Qwen se quito (ver judge.py).
- Posicion: solo existe cuando el juez compara dos respuestas lado a lado. Cada
  par se juzga en los dos ordenes y solo cuenta como victoria si el mismo modelo
  gana en ambos (veredicto_consistente); si el ganador cambia con el orden, el
  par es "inconsistente" y no se le suma a nadie. El flip rate queda como
  diagnostico. La rubrica 1-5 y el criterio califican una respuesta a la vez:
  no tienen posicion.
- Longitud: los prompts piden no premiar la extension y length_bias_correlation
  mide si el puntaje sube con el largo. El scorecard reporta el juez sin el
  criterio de concision, que es el unico que mira el largo a proposito.

El nucleo de la comparacion (_run_position_bias_probe_core) depende solo de
generate_fn: se prueba sin red ni GPU.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from typing import Callable, Optional

import numpy as np

from tools.evaluation.checkpoint import append_checkpoint, huella, load_checkpoint
from tools.evaluation.estadistica import proporcion

# Cambia cuando cambia el prompt (entra en la huella del checkpoint).
PAIRWISE_PROMPT_VERSION = "2026-10-06"

PAIRWISE_JUDGE_SYSTEM_PROMPT = (
    "Eres un evaluador experto en derecho colombiano. Se te daran dos "
    "respuestas (A y B) a la misma consulta legal. Decide cual es mejor, o "
    "si estan empatadas, en este orden de importancia: (1) correccion "
    "juridica: el mecanismo correcto y la entidad o autoridad que de verdad "
    "tramita ese caso; una entidad equivocada o inexistente es un error grave; "
    "(2) prudencia: no inventa normas, articulos, plazos ni garantiza "
    "resultados; (3) utilidad para alguien sin formacion juridica. El orden en "
    "que aparecen las respuestas no importa, y la mas larga no es mejor por "
    "serlo. Responde EXCLUSIVAMENTE con un JSON valido: "
    '{"veredicto": "A"|"B"|"empate", "confianza": <entero 1-5>}'
)


def build_pairwise_prompt(query: str, response_a: str, response_b: str) -> str:
    return (
        f'Consulta del usuario:\n"{query}"\n\n'
        f'Respuesta A:\n"{response_a}"\n\n'
        f'Respuesta B:\n"{response_b}"\n\n'
        "¿Cual respuesta es mejor? Responde solo con el JSON."
    )


def parse_pairwise_verdict(raw: str) -> Optional[str]:
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

    def veredicto_consistente(self) -> dict[str, int]:
        """Un veredicto por par, con el sesgo de posicion neutralizado: gana un
        modelo solo si gana en los DOS ordenes. Si el ganador cambia con el
        orden, el par es "inconsistente"; empate en los dos ordenes, o empate en
        uno y victoria en el otro, es "empate" (el juez no se decide); sin
        respuesta o ilegible en alguno, "sin_veredicto"."""
        conteo = {"fine_tuned": 0, "baseline": 0, "empate": 0, "inconsistente": 0, "sin_veredicto": 0}
        for d in self.details:
            a, b = d.get("verdict_normal"), d.get("verdict_swapped")
            if a is None or b is None:
                conteo["sin_veredicto"] += 1
            elif a == b:
                conteo[a if a in conteo else "sin_veredicto"] += 1
            elif "empate" in (a, b):
                conteo["empate"] += 1
            else:
                conteo["inconsistente"] += 1
        return conteo

    def tasa_victoria(self) -> dict:
        """Proporcion de pares que gana el fine-tuned sobre los pares con
        ganador consistente (sin empates, inconsistentes ni sin veredicto),
        con IC de Wilson. 0.5 = empate tecnico."""
        c = self.veredicto_consistente()
        decididos = c["fine_tuned"] + c["baseline"]
        iv = proporcion(c["fine_tuned"], decididos)
        return {"fine_tuned": c["fine_tuned"], "decididos": decididos,
                "tasa": iv.valor if iv else None, "ic95": [iv.bajo, iv.alto] if iv else None}

    def winner_counts(self) -> dict[str, int]:
        """Cuenta cuantas veces gano cada opcion en cada orden -- IMPORTANTE:
        flip_rate_pct=0 NO significa "sin sesgo". Si el mismo lado gana
        siempre en las dos pasadas (ej. 'baseline' 30/30), el flip rate
        tambien da 0%, pero eso es evidencia de preferencia sistematica, no
        de neutralidad. Revisar siempre este conteo, no solo flip_rate_pct."""
        counts: dict[str, int] = {}
        for d in self.details:
            for key in ("verdict_normal", "verdict_swapped"):
                w = d.get(key) or "sin_veredicto"   # sin respuesta o ilegible: se cuenta, no se esconde
                counts[w] = counts.get(w, 0) + 1
        return counts


GenerateFn = Callable[[str, str, int], str]
"""Firma comun para el backend de generacion del sondeo de position bias:
(system_prompt, user_content, max_new_tokens) -> texto crudo del modelo."""


def _run_position_bias_probe_core(
    generate_fn: GenerateFn,
    pairs: list[tuple[int, str, str, str]],
    sample_size: Optional[int],
    seed: int,
    progress_every: int,
    max_tokens: int,
    log_prefix: str,
    checkpoint_path: Optional[Path] = None,
) -> PositionBiasReport:
    """Nucleo compartido del sondeo de position bias: agnostico de si el
    modelo corre local (GPU) o via una API externa -- solo depende de
    generate_fn. pairs: lista de (id, query, respuesta_baseline,
    respuesta_fine_tuned). Para cada par muestreado, el juez decide dos
    veces -- orden normal (A=baseline, B=fine_tuned) y orden invertido
    (A=fine_tuned, B=baseline). flip_rate_pct = % de pares comparables (sin
    empate/sin parseo en ninguna de las dos pasadas) donde el veredicto
    cambia solo por el orden. sample_size=None juzga todos los pares.

    checkpoint_path (opcional): JSONL donde se guarda cada par resuelto a
    medida que se procesa. Si el archivo ya existe (de una corrida
    interrumpida), los pares cuyo id ya este ahi se saltan en vez de
    volver a gastar cupo/tiempo resolviendolos -- siempre que los textos
    sean los mismos (huella); si cambiaron, el par se vuelve a juzgar."""
    rng = Random(seed)
    if sample_size is None or len(pairs) <= sample_size:
        sample = list(pairs)
    else:
        sample = rng.sample(pairs, sample_size)

    # Se reusa un par solo si los textos y el prompt son los mismos (checkpoint.py).
    huellas = {pid: huella(PAIRWISE_PROMPT_VERSION, q, b, f) for pid, q, b, f in sample}
    done = load_checkpoint(checkpoint_path, huellas, log_prefix=log_prefix)

    n_flipped = 0
    n_tied_or_unparsed = 0
    details: list[dict] = []
    total = len(sample)
    start_probe = time.perf_counter()

    for i, (record_id, query, baseline_resp, finetuned_resp) in enumerate(sample, start=1):
        if record_id in done:
            entry = done[record_id]
            winner_normal = entry["verdict_normal"]
            winner_swapped = entry["verdict_swapped"]
        else:
            raw_normal = generate_fn(
                PAIRWISE_JUDGE_SYSTEM_PROMPT,
                build_pairwise_prompt(query, baseline_resp, finetuned_resp),
                max_tokens,
            )
            verdict_normal = parse_pairwise_verdict(raw_normal)

            raw_swapped = generate_fn(
                PAIRWISE_JUDGE_SYSTEM_PROMPT,
                build_pairwise_prompt(query, finetuned_resp, baseline_resp),
                max_tokens,
            )
            verdict_swapped = parse_pairwise_verdict(raw_swapped)

            winner_normal = {"a": "baseline", "b": "fine_tuned"}.get(
                verdict_normal, verdict_normal
            )
            winner_swapped = {"a": "fine_tuned", "b": "baseline"}.get(
                verdict_swapped, verdict_swapped
            )
            entry = {
                "id": record_id,
                "huella": huellas[record_id],
                "verdict_normal": winner_normal,
                "verdict_swapped": winner_swapped,
            }
            if winner_normal is not None and winner_swapped is not None:
                # Sin respuesta del juez (cupo, red) o ilegible no se guarda: se
                # reintenta al retomar. Si se guardara, el par quedaria "sin
                # veredicto" para siempre.
                append_checkpoint(checkpoint_path, entry)

        if (
            winner_normal in (None, "empate")
            or winner_swapped in (None, "empate")
        ):
            n_tied_or_unparsed += 1
        elif winner_normal != winner_swapped:
            n_flipped += 1

        details.append(entry)

        if progress_every and (i % progress_every == 0 or i == total):
            elapsed = time.perf_counter() - start_probe
            avg = elapsed / i
            eta_min = avg * (total - i) / 60
            print(
                f"[{log_prefix}] {i}/{total} ({100 * i / total:.0f}%) -- "
                f"{avg:.1f}s/par, ETA ~{eta_min:.1f} min"
            )

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
    with np.errstate(invalid="ignore", divide="ignore"):   # puntajes constantes: r indefinido
        r = float(np.corrcoef(scores, lengths)[0, 1])
    return {"pearson_r": round(r, 3) if not np.isnan(r) else None, "n": len(scores)}
