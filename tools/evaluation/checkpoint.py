"""Checkpoint/resume compartido para lotes de llamadas a un juez (local o
externo): cada resultado se guarda en un JSONL a medida que se procesa
(append + flush inmediato), y al reiniciar se saltan los ids ya resueltos
-- para no volver a gastar cupo/tiempo en llamadas que ya habian
funcionado antes de un corte (rate limit, desconexion de Colab, etc.).

Formato del archivo: una linea JSON por item, siempre con un campo "id".
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def load_checkpoint(path: Optional[Path]) -> dict[int, dict]:
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
    return done


def append_checkpoint(path: Optional[Path], entry: dict) -> None:
    if not path:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        f.flush()
