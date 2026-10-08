"""Intervalos de confianza para las comparaciones de M2 (puro Python).

Por que existe. El scorecard reportaba promedios sin incertidumbre, y la
diferencia que se leia como "mejora del fine-tuning" era menor que la
variacion entre dos corridas del mismo modelo: el juez dio al fine-tuned
3.769 en una corrida (A100) y 3.716 en otra (L4), mientras la ventaja sobre
el baseline fue 0.095 en una y 0.028 en la otra. Sin intervalo no se puede
distinguir una mejora de ruido.

- diferencia_pareada: bootstrap pareado (se remuestrean ejemplos, no
  respuestas sueltas: baseline y fine-tuned responden la misma pregunta).
- proporcion: intervalo de Wilson, para tasas (aprobados, sin citas...).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass
class Intervalo:
    valor: float
    bajo: float
    alto: float
    n: int

    @property
    def significativo(self) -> bool:
        """El intervalo no contiene el 0 (para diferencias)."""
        return self.bajo > 0 or self.alto < 0

    def texto(self, decimales: int = 3) -> str:
        return (f"{self.valor:+.{decimales}f} [{self.bajo:+.{decimales}f}, "
                f"{self.alto:+.{decimales}f}]")


def diferencia_pareada(
    a: Sequence[Optional[float]],
    b: Sequence[Optional[float]],
    n_remuestreos: int = 2000,
    semilla: int = 42,
    confianza: float = 0.95,
) -> Optional[Intervalo]:
    """Media de (b - a) con IC por bootstrap pareado. Se descartan los pares
    donde falta alguno de los dos valores (p. ej. fallo de parseo del juez)."""
    pares = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pares) < 2:
        return None
    difs = [y - x for x, y in pares]
    rng = random.Random(semilla)
    n = len(difs)
    medias = sorted(sum(difs[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_remuestreos))
    cola = (1 - confianza) / 2
    return Intervalo(
        valor=round(sum(difs) / n, 4),
        bajo=round(medias[int(cola * n_remuestreos)], 4),
        alto=round(medias[int((1 - cola) * n_remuestreos) - 1], 4),
        n=n,
    )


def proporcion(exitos: float, n: int, z: float = 1.96) -> Optional[Intervalo]:
    """Proporcion con IC de Wilson (se comporta bien con n chico y con tasas
    cercanas a 0 o 1, donde el intervalo normal se sale de [0, 1])."""
    if n <= 0:
        return None
    p = exitos / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    margen = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return Intervalo(valor=round(p, 4), bajo=round(max(0.0, centro - margen), 4),
                     alto=round(min(1.0, centro + margen), 4), n=n)
