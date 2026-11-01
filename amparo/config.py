"""Rutas del proyecto: un solo lugar en vez de `Path(__file__).parent.parent`
repetido en cada modulo.

La raiz es la carpeta que contiene `amparo/` y `data/`. Con el paquete
instalado en modo editable (`pip install -e .`) se deduce sola. `AMPARO_RAIZ`
la sobrescribe, por ejemplo en Colab cuando el repo vive en Drive.
"""
from __future__ import annotations

import os
from pathlib import Path


def _raiz() -> Path:
    if os.environ.get("AMPARO_RAIZ"):
        return Path(os.environ["AMPARO_RAIZ"]).resolve()
    return Path(__file__).resolve().parent.parent


RAIZ = _raiz()
PAQUETE = RAIZ / "amparo"
DATA = RAIZ / "data"
RESULTS = RAIZ / "results"
RUNS = RAIZ / "runs"
MODELS = RAIZ / "models"
