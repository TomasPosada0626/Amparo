"""Manifiesto de una corrida de M3: con que se corrio, exactamente.

Ninguna corrida de M3 registraba nada: ni el commit, ni las versiones de las
librerias, ni que adaptador ni que indice se usaron. El problema dejo de ser
teorico el 6 de octubre, cuando el adaptador de Drive se sobrescribio: desde
entonces no hay forma de saber con que modelo salio ninguna cifra de M3 anterior
a esa fecha, y por lo tanto ninguna de esas cifras se puede reproducir ni
comparar con las nuevas.

El manifiesto de M2 (tools/evaluation/pipeline.build_manifest) resuelve la mitad
-- commit, semilla, versiones -- pero no sabe de las piezas propias de M3: el
indice FAISS, el corpus que lo origino y el eval set. Aqui se reusa lo suyo y se
agregan las huellas de esas piezas.

Por que huellas y no fechas: una fecha no dice si el archivo cambio. Si dos
corridas declaran el mismo hash de indice, midieron sobre el mismo indice; si
declaran distinto, no son comparables aunque las dos digan "2026-10-07".

El hash del adaptador se calcula sobre adapter_model.safetensors, que es donde
estan los pesos: adapter_config.json es identico entre reentrenamientos y no
distingue nada.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from tools.evaluation import config as eval_config
from tools.rag import config

# Librerias que importan para reproducir una corrida de M3. Las de M2 mas las
# propias del RAG: dspy para el extra, faiss y rank_bm25 para el retrieval.
LIBRERIAS = (
    "transformers", "peft", "torch", "accelerate", "bitsandbytes",
    "sentence-transformers", "faiss-cpu", "rank_bm25", "dspy",
)

# Cuanto se lee de un archivo grande por vez al hashear (el adaptador son ~40 MB).
_BLOQUE = 1 << 20


def huella_archivo(path: Path | str, *, bloque: int = _BLOQUE) -> Optional[str]:
    """sha256 corto de un archivo, o None si no existe.

    Devuelve None en vez de lanzar porque el manifiesto se arma tambien fuera de
    Colab (en los tests, por ejemplo), donde las rutas de Drive no existen. Un
    campo en None dice "no se pudo registrar", que es informacion; una excepcion
    tumbaria la corrida por un dato accesorio.
    """
    p = Path(path)
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for trozo in iter(lambda: f.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()[:16]


def huella_directorio(path: Path | str, *, patron: str = "*") -> Optional[str]:
    """sha256 corto del contenido de un directorio (nombres y bytes)."""
    p = Path(path)
    if not p.is_dir():
        return None
    h = hashlib.sha256()
    for archivo in sorted(p.glob(patron)):
        if not archivo.is_file():
            continue
        h.update(archivo.name.encode("utf-8"))
        with archivo.open("rb") as f:
            for trozo in iter(lambda: f.read(_BLOQUE), b""):
                h.update(trozo)
    return h.hexdigest()[:16]


@dataclass
class ManifiestoM3:
    git_commit: str
    timestamp: str
    modulo: str                        # "s07" | "s08" | "s10" | "dspy"
    use_lora: bool
    base_model_id: str
    adapter_dir: str
    # Huellas: lo que permite saber si dos corridas midieron sobre lo mismo.
    hash_adaptador: Optional[str] = None
    hash_indice: Optional[str] = None
    hash_metadata_indice: Optional[str] = None
    hash_corpus: Optional[str] = None
    hash_dataset: Optional[str] = None
    hash_eval_set: Optional[str] = None
    n_chunks: Optional[int] = None
    n_eval_set: Optional[int] = None
    # Config que cambia los resultados sin cambiar el codigo.
    retrieval: dict = field(default_factory=dict)
    library_versions: dict = field(default_factory=dict)
    hardware: str = ""

    def guardar(self, destino: Path | str, nombre: str = "run_manifest.json") -> Path:
        d = Path(destino)
        d.mkdir(parents=True, exist_ok=True)
        ruta = d / nombre
        ruta.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        return ruta


def construir(
    modulo: str,
    *,
    use_lora: bool,
    n_chunks: Optional[int] = None,
    n_eval_set: Optional[int] = None,
    hardware: str = "",
    adapter_dir: Optional[str] = None,
    index_path: Optional[Path] = None,
    metadata_path: Optional[Path] = None,
) -> ManifiestoM3:
    """Arma el manifiesto de una corrida de M3.

    Las rutas por defecto son las de tools/rag/config.py; se pueden pasar otras
    para una corrida que use un indice distinto del de siempre.
    """
    from tools.evaluation.pipeline import _git_commit  # reusa el de M2

    try:
        from importlib import metadata as importlib_metadata
        versiones = {}
        for lib in LIBRERIAS:
            try:
                versiones[lib] = importlib_metadata.version(lib)
            except importlib_metadata.PackageNotFoundError:
                versiones[lib] = "not-installed"
    except Exception:                                   # pragma: no cover
        versiones = {}

    adapter = adapter_dir or config.LORA_ADAPTER_PATH or ''
    indice = Path(index_path) if index_path else config.FAISS_INDEX_PATH
    meta = Path(metadata_path) if metadata_path else config.FAISS_METADATA_PATH

    return ManifiestoM3(
        git_commit=_git_commit(),
        timestamp=datetime.now(timezone.utc).isoformat(),
        modulo=modulo,
        use_lora=use_lora,
        base_model_id=config.BASE_MODEL_ID,
        adapter_dir=adapter,
        # Los pesos, no el config: adapter_config.json es identico entre
        # reentrenamientos y no distinguiria dos adaptadores distintos.
        hash_adaptador=huella_archivo(Path(adapter) / "adapter_model.safetensors"),
        hash_indice=huella_archivo(indice),
        hash_metadata_indice=huella_archivo(meta),
        hash_corpus=huella_directorio(config.RAW_CORPUS_DIR, patron="*.md"),
        hash_dataset=huella_archivo(
            eval_config.DATASET_PATH),
        hash_eval_set=huella_archivo(config.PROJECT_ROOT / "data" / "eval_set.json"),
        n_chunks=n_chunks,
        n_eval_set=n_eval_set,
        retrieval={
            "embedding_model_id": config.EMBEDDING_MODEL_ID,
            "top_k": config.TOP_K,
            "retrieval_min_score": config.RETRIEVAL_MIN_SCORE,
            "max_tokens_per_chunk": config.MAX_TOKENS_PER_CHUNK,
            "min_tokens_per_chunk": config.MIN_TOKENS_PER_CHUNK,
            "max_new_tokens_generation": config.MAX_NEW_TOKENS_GENERATION,
        },
        library_versions=versiones,
        hardware=hardware,
    )
