"""Orquesta la ejecucion de una comparacion de modelos en un hilo de fondo.

La GUI (Tkinter, hilo principal) nunca debe bloquearse esperando respuestas de
red, y tampoco es seguro tocar widgets desde otro hilo. Por eso ComparisonRun
corre en un threading.Thread aparte y publica eventos en una queue.Queue, que
la GUI vacia periodicamente con root.after().
"""

from __future__ import annotations

import csv
import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import llm_client
from .config import ModelSpec
from .dataset_loader import DatasetItem
from .metrics import similarity_pct


@dataclass
class RunResult:
    model_id: str
    model_label: str
    query_index: int
    pass_index: int
    query: str
    expected: Optional[str]
    response: str
    latency_s: float
    prompt_tokens: int
    completion_tokens: int
    tokens_per_s: float
    similarity: Optional[float]
    cost_usd: Optional[float]
    error: Optional[str]


@dataclass
class RunEvent:
    kind: str  # "result" | "done"
    completed: int = 0
    total: int = 0
    result: Optional[RunResult] = None
    current_label: str = ""


class ComparisonRun:
    """Ejecuta (modelos x consultas x pasadas) en un hilo aparte y publica eventos."""

    def __init__(self, models: list[ModelSpec], items: list[DatasetItem], passes: int) -> None:
        self.models = models
        self.items = items
        self.passes = max(1, passes)
        self.total = len(models) * len(items) * self.passes
        self.events: "queue.Queue[RunEvent]" = queue.Queue()
        self.results: list[RunResult] = []
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        self._stop.set()

    @property
    def cancelled(self) -> bool:
        return self._stop.is_set()

    def _run(self) -> None:
        completed = 0
        for model in self.models:
            if self._stop.is_set():
                break
            for q_idx, item in enumerate(self.items):
                if self._stop.is_set():
                    break
                for p_idx in range(self.passes):
                    if self._stop.is_set():
                        break
                    call = llm_client.call_model(model.provider, model.slug, item.query)
                    result = RunResult(
                        model_id=model.id,
                        model_label=model.label,
                        query_index=q_idx,
                        pass_index=p_idx,
                        query=item.query,
                        expected=item.expected,
                        response=call.text,
                        latency_s=call.latency_s,
                        prompt_tokens=call.prompt_tokens,
                        completion_tokens=call.completion_tokens,
                        tokens_per_s=call.tokens_per_s,
                        similarity=similarity_pct(item.expected, call.text) if not call.error else None,
                        cost_usd=call.cost_usd,
                        error=call.error,
                    )
                    self.results.append(result)
                    completed += 1
                    self.events.put(
                        RunEvent(
                            kind="result",
                            completed=completed,
                            total=self.total,
                            result=result,
                            current_label=model.label,
                        )
                    )
        self.events.put(RunEvent(kind="done", completed=completed, total=self.total))

    def export_csv(self, path: Path) -> None:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "modelo", "consulta_idx", "pasada", "consulta", "esperado", "respuesta",
                    "tiempo_s", "tokens_prompt", "tokens_completion", "tokens_por_s",
                    "similitud_pct", "costo_usd", "error",
                ]
            )
            for r in self.results:
                writer.writerow(
                    [
                        r.model_label,
                        r.query_index + 1,
                        r.pass_index + 1,
                        r.query,
                        r.expected or "",
                        r.response,
                        f"{r.latency_s:.2f}",
                        r.prompt_tokens,
                        r.completion_tokens,
                        f"{r.tokens_per_s:.1f}",
                        r.similarity if r.similarity is not None else "",
                        f"{r.cost_usd:.6f}" if r.cost_usd is not None else "",
                        r.error or "",
                    ]
                )
