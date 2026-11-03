"""
El manifiesto de una corrida de M4: que codigo, que GPU, que modelos y cuando.

Hasta el tag `demo-final` era `m4/pipeline/corrida.py`; desde la migracion al
paquete vive aqui (docs/MIGRACION.md). La logica no cambio.

POR QUE (revision docente, PR #15, H3)

La corrida oficial del 2026-10-25 clono `main`, que es una referencia movil, y
ningun artefacto registro commit, GPU, versiones ni reranker. Sus cifras son
correctas —se recalculan sin discrepancias desde las trazas— pero no se puede
decir con certeza QUE sistema las produjo. Este modulo lo deja escrito DESDE
la propia corrida, que es lo unico que lo hace verificable: un manifiesto
reconstruido despues siempre es una inferencia.

QUE GUARDA, Y DONDE

Cada corrida escribe en `m4/corridas/<id>/`, con `<id>` en UTC. No pisa los
resultados de corridas anteriores ni los de la oficial del 25, que se quedan
en `m4/` como historicos.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from amparo.config import RAIZ
CARPETA_CORRIDAS = RAIZ / "m4" / "corridas"


def _git(*args: str) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, timeout=20)
        if r.returncode != 0:
            return None
        return r.stdout.strip() or None
    except Exception:                                      # noqa: BLE001
        return None


def _version(modulo: str) -> str | None:
    try:
        from importlib.metadata import version
        return version(modulo)
    except Exception:                                      # noqa: BLE001
        return None


def _sha(ruta: Path) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()[:16]


def huella_eval_set(carpeta: Path = RAIZ / "m4" / "eval_set") -> dict:
    """SHA-256 del CSV de casos y de cada imagen: el eval set que se uso."""
    out = {"casos_m4.csv": _sha(carpeta / "casos_m4.csv")}
    for p in sorted((carpeta / "imagenes").glob("*")):
        if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
            out[f"imagenes/{p.name}"] = _sha(p)
    return out


def nueva(etiqueta: str = "m4", base: Path = CARPETA_CORRIDAS) -> tuple[str, Path]:
    """Id en UTC y carpeta vacia de la corrida."""
    cid = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    carpeta = Path(base) / f"{cid}_{etiqueta}"
    carpeta.mkdir(parents=True, exist_ok=False)
    return cid, carpeta


def gpu() -> dict:
    try:
        import torch
        if torch.cuda.is_available():
            return {"cuda": True, "nombre": torch.cuda.get_device_name(0),
                    "memoria_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)}
        return {"cuda": False, "nombre": None}
    except Exception:                                      # noqa: BLE001
        return {"cuda": None, "nombre": None}


def manifiesto(cid: str, *, vlm_id: str | None = None, vlm_dtype: str | None = None,
               agente=None, extra: dict | None = None) -> dict:
    """Lo que hay que saber para atribuir las cifras a un sistema concreto."""
    indice = getattr(agente, "indice", None)
    return {
        "id": cid,
        "inicio_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "codigo": {
            "commit": _git("rev-parse", "HEAD"),
            "tag": _git("describe", "--tags", "--exact-match"),
            "describe": _git("describe", "--tags", "--always", "--dirty"),
        },
        "entorno": {
            "python": platform.python_version(),
            "plataforma": platform.platform(),
            "gpu": gpu(),
            "versiones": {m: _version(m) for m in (
                "torch", "transformers", "accelerate", "sentence-transformers",
                "groq", "qwen-vl-utils", "pillow")},
        },
        "vlm": {"modelo": vlm_id, "dtype": vlm_dtype, "generacion": "voraz (do_sample=False)"},
        "m3": {
            "brazo": getattr(agente, "etiqueta", None),
            "modelo": getattr(agente, "modelo", None),
            "estrategia": getattr(agente, "estrategia", None),
            "k": getattr(agente, "k", None),
            "denso": getattr(indice, "modelo", None),
            # El reranker se carga en la primera busqueda: hasta entonces es None.
            "reranker": getattr(indice, "reranker_usado", None),
            "n_fragmentos": len(getattr(indice, "chunks", []) or []),
        },
        "eval_set": huella_eval_set(),
        **(extra or {}),
    }


def guardar(man: dict, carpeta: Path) -> Path:
    ruta = Path(carpeta) / "corrida_m4.json"
    ruta.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return ruta


def cerrar(man: dict, carpeta: Path, *, agente=None, resumen: dict | None = None) -> Path:
    """Completa lo que solo se sabe al final (reranker, hora de cierre, cifras)."""
    indice = getattr(agente, "indice", None)
    if indice is not None:
        man["m3"]["reranker"] = getattr(indice, "reranker_usado", None)
    man["fin_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if resumen:
        man["resumen"] = resumen
    man["archivos"] = {p.name: _sha(p) for p in sorted(Path(carpeta).glob("*"))
                       if p.is_file() and p.name != "corrida_m4.json"}
    return guardar(man, carpeta)
