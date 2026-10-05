"""Checkpoint/resume compartido para lotes de llamadas a un juez (local o
externo): cada resultado se guarda en un JSONL a medida que se procesa
(append + flush inmediato), y al reiniciar se saltan los items ya resueltos
-- para no volver a gastar cupo/tiempo en llamadas que ya habian
funcionado antes de un corte (rate limit, desconexion de Colab, etc.).

Formato del archivo: una linea JSON por item, con "id" y "huella".

Por que la huella. La primera version reusaba por id solamente, y la
carpeta de checkpoints es una sola para todas las corridas. En la corrida de
M2 del 2026-10-02 (L4), el sondeo de Groq y los puntajes del eval set se
tomaron enteros del checkpoint de una corrida anterior del mismo modelo: el
notebook imprimio esos puntajes junto a respuestas que el juez nunca leyo
(p. ej. id 9001: Groq critica que la respuesta nombra la SIC, y la respuesta
impresa no la nombra). La huella es un hash del contenido calificado
(pregunta, referencia, respuesta...): un resultado solo se reusa si el texto
es exactamente el mismo. Las entradas viejas, sin huella, no se reusan.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, Optional


def huella(*textos: Optional[str]) -> str:
    """Hash corto del contenido que se califica. Cambia si cambia cualquier
    texto (o su orden), asi que un checkpoint nunca se aplica a otro texto."""
    contenido = "\x1f".join(t or "" for t in textos)
    return hashlib.sha1(contenido.encode("utf-8")).hexdigest()[:16]


def load_checkpoint(
    path: Optional[Path],
    huellas: Optional[Mapping[int, str]] = None,
    log_prefix: str = "checkpoint",
) -> dict[int, dict]:
    """Items ya resueltos, por id.

    huellas: {id: huella del contenido actual}. Si se pasa, solo se devuelven
    las entradas cuya huella coincide; las demas (otro texto, u entradas
    viejas sin huella) se descartan y se informa cuantas. Todos los lotes del
    harness la pasan; sin ella se reusa por id (solo para compatibilidad)."""
    if not path or not Path(path).exists():
        return {}
    done: dict[int, dict] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            done[entry["id"]] = entry
    if huellas is None:
        return done
    vigentes = {i: e for i, e in done.items() if i in huellas and e.get("huella") == huellas[i]}
    descartadas = sum(1 for i in done if i in huellas and i not in vigentes)
    if vigentes or descartadas:
        print(f"[{log_prefix}] checkpoint: {len(vigentes)} reusadas (mismo texto); "
              f"{descartadas} descartadas porque el texto cambio (otra corrida) -- se recalculan.")
    return vigentes


def append_checkpoint(path: Optional[Path], entry: dict) -> None:
    if not path:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        f.flush()


def sin_metadatos(entry: dict) -> dict:
    """La entrada del checkpoint sin los campos propios del checkpoint."""
    return {k: v for k, v in entry.items() if k not in ("id", "huella")}
