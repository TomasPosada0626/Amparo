"""Similitud lexica entre preguntas (TF-IDF + coseno, puro Python).

La usan dos guardias:
- rutas.py, para saber de que tema es una pregunta (sus vecinas en train).
- eval_set.py, para detectar preguntas del eval set que son casi copia de una
  de train (fuga que la coincidencia exacta no ve).

Es lexica: "Como escondo mi carro para que no me lo embarguen?" y "como puedo
esconder mis bienes para que no me los quiten?" son la misma pregunta y aqui
se parecen poco. Las parafrasis de sentido se revisan a mano.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Sequence

_STOP = frozenset(
    "a al algo ante como con contra cual cuando de del donde el ella ellos en entre es esa ese eso esta "
    "este esto fue ha hay la las le les lo los mas me mi mis muy no nos o para pero por porque que se "
    "si sin sobre su sus te tengo tiene tu tus un una uno y ya yo puedo puede debo hacer hago".split()
)


def normalizar(texto: str) -> str:
    """minusculas, sin tildes y con espacios simples."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", (texto or "").lower())
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", sin_tildes).strip()


def tokens(texto: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", normalizar(texto)) if t not in _STOP and len(t) > 2]


class IndiceTfidf:
    """Indice de un corpus fijo de textos; .parecidos(texto) da los mas cercanos."""

    def __init__(self, textos: Sequence[str]):
        df: Counter = Counter()
        tokenizados = [tokens(t) for t in textos]
        for toks in tokenizados:
            df.update(set(toks))
        n = len(textos) or 1
        self._idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self._vectores = [self._vector_de(toks) for toks in tokenizados]

    def _vector_de(self, toks: list[str]) -> dict[str, float]:
        v = {t: c * self._idf.get(t, 0.0) for t, c in Counter(toks).items()}
        norma = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norma for t, x in v.items()}

    def similitudes(self, texto: str) -> list[float]:
        q = self._vector_de(tokens(texto))
        return [sum(q.get(t, 0.0) * x for t, x in vec.items()) for vec in self._vectores]

    def parecidos(self, texto: str, k: int = 5) -> list[tuple[int, float]]:
        """(indice en el corpus, coseno) de los k textos mas parecidos con coseno > 0."""
        puntajes = sorted(enumerate(self.similitudes(texto)), key=lambda s: -s[1])
        return [(i, round(s, 4)) for i, s in puntajes[:k] if s > 0]
