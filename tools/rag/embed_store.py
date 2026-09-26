"""Embed + Store: convierte chunks en vectores y los indexa en FAISS.

Etapas 3 y 4 de 7 del pipeline RAG (S07). Offline / indexacion.

Backend: FAISS (decision 2 de docs/m3_decisiones_rag.md). pgvector queda para
cuando exista el backend FastAPI+Postgres; get_store() lo dice explicitamente en
vez de dejar una implementacion sin uso ni pruebas.

torch/transformers se importan de forma perezosa (dentro de la funcion que los
usa) y faiss tambien, siguiendo el patron de tools/evaluation/generation.py: asi
este modulo es importable y testeable sin GPU y sin el stack pesado instalado.
Llamar a las funciones de embedding fuera de Colab sin torch instalado falla, y
eso es lo esperado.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

import numpy as np

from tools.rag import config

# Campos de metadata que viajan junto al vector. Son los que permiten citar de
# forma verificable: sin fuente/articulo/url, el chunk recuperado no se puede
# convertir en una cita comprobable, que es el punto de todo el sistema.
METADATA_FIELDS = (
    "chunk_id",
    "doc_id",
    "text",
    "fuente",
    "tipo",
    "url_fuente",
    "articulos_incluidos",
    "capitulo",
    "vigente",
)


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    fuente: str
    url_fuente: str
    score: float
    doc_id: str = ""
    tipo: str = ""
    articulos_incluidos: list[str] = None  # type: ignore[assignment]
    capitulo: str = ""
    vigente: bool = True
    # Score del recuperador denso (coseno e5), preservado aparte porque `score`
    # cambia de significado a lo largo del pipeline avanzado: en el retrieval
    # ingenuo `score` ES el coseno, pero tras la fusion RRF pasa a ser el puntaje
    # RRF y tras el reranking el del cross-encoder -- escalas distintas. La
    # valvula de escape (RETRIEVAL_MIN_SCORE) esta calibrada sobre el coseno de
    # e5, asi que necesita seguir leyendo ese numero y no el que quedo en `score`
    # despues de reordenar. Ver docs/m3_decisiones_rag.md (valvula de
    # escape). None cuando el chunk no vino por la via densa (p. ej. solo BM25).
    dense_score: float | None = None

    def __post_init__(self) -> None:
        if self.articulos_incluidos is None:
            self.articulos_incluidos = []
        # Por defecto, el score denso ES el score inicial (caso S07): asi el
        # codigo que ya existia sigue viendo el coseno en `dense_score` sin tener
        # que setearlo a mano.
        if self.dense_score is None:
            self.dense_score = self.score

    @property
    def cita(self) -> str:
        """Cita corta y verificable del chunk, como se muestra en el prompt."""
        if not self.articulos_incluidos:
            return self.fuente
        etiqueta = "Articulo" if len(self.articulos_incluidos) == 1 else "Articulos"
        return f"{self.fuente}, {etiqueta} {', '.join(self.articulos_incluidos)}"


class VectorStore(Protocol):
    def add(self, chunks: list, embeddings: list[list[float]]) -> None: ...
    def search(self, query_embedding, top_k: int) -> list[SearchResult]: ...


# --- Helpers puros (sin dependencias pesadas, testeables) --------------------

def chunk_to_metadata(chunk) -> dict:
    """Serializa un Chunk a la metadata que se guarda junto al vector."""
    return {campo: getattr(chunk, campo) for campo in METADATA_FIELDS}


def metadata_to_result(meta: dict, score: float) -> SearchResult:
    return SearchResult(
        chunk_id=meta["chunk_id"],
        text=meta["text"],
        fuente=meta["fuente"],
        url_fuente=meta.get("url_fuente", ""),
        score=score,
        doc_id=meta.get("doc_id", ""),
        tipo=meta.get("tipo", ""),
        articulos_incluidos=list(meta.get("articulos_incluidos") or []),
        capitulo=meta.get("capitulo", ""),
        vigente=bool(meta.get("vigente", True)),
    )


def normalize(vectors) -> "np.ndarray":
    """Normaliza L2 cada fila, para que el producto interno sea coseno.

    FAISS no tiene un indice de coseno: se usa IndexFlatIP sobre vectores
    normalizados, que es equivalente. Vectores de norma cero se dejan en cero en
    vez de producir NaN (un NaN en el indice envenena todas las busquedas).
    """
    matriz = np.asarray(vectors, dtype="float32")
    if matriz.ndim == 1:
        matriz = matriz.reshape(1, -1)
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    return np.divide(matriz, normas, out=np.zeros_like(matriz), where=normas > 0)


# --- Embeddings -------------------------------------------------------------

_MODELO_CACHE: dict[str, tuple] = {}


def load_embedding_model(model_id: str = config.EMBEDDING_MODEL_ID):
    """Carga (una sola vez) el encoder de embeddings y lo deja en GPU si hay.

    Se cachea a proposito: sin esto, cada llamada recargaria ~1 GB de pesos, y la
    corrida sobre el eval set (una consulta por registro) pagaria esa carga una
    vez por consulta. Y sin el .to(cuda) el encoder se queda en CPU aunque Colab
    tenga GPU: indexar 3.400 chunks pasa de minutos a bastante mas.
    """
    import torch
    from transformers import AutoModel, AutoTokenizer

    if model_id not in _MODELO_CACHE:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModel.from_pretrained(model_id)
        model.to("cuda" if torch.cuda.is_available() else "cpu")
        model.eval()
        _MODELO_CACHE[model_id] = (model, tokenizer)
    return _MODELO_CACHE[model_id]


def _embed_with_prefix(
    texts: Iterable[str],
    prefix: str,
    *,
    model_id: str = config.EMBEDDING_MODEL_ID,
    batch_size: int = config.EMBEDDING_BATCH_SIZE,
) -> list[list[float]]:
    """Mean pooling enmascarado + normalizacion L2, como espera e5.

    Los prefijos "query: " / "passage: " no son opcionales en e5: el modelo fue
    entrenado con ellos y omitirlos degrada el retrieval en silencio. Por eso
    esta funcion es privada y se expone via embed_query/embed_passages.
    """
    import torch  # import perezoso: stack pesado, vive en el notebook de Colab

    textos = [f"{prefix}{t}" for t in texts]
    if not textos:
        return []

    model, tokenizer = load_embedding_model(model_id)

    salidas: list[list[float]] = []
    with torch.no_grad():
        for inicio in range(0, len(textos), batch_size):
            lote = textos[inicio : inicio + batch_size]
            inputs = tokenizer(
                lote,
                return_tensors="pt",
                truncation=True,
                max_length=config.EMBEDDING_MAX_LENGTH,
                padding=True,
            ).to(model.device)
            hidden = model(**inputs).last_hidden_state
            mask = inputs["attention_mask"].unsqueeze(-1).float()
            pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            salidas.extend(pooled.cpu().tolist())
    return salidas


def embed_passages(texts: list[str], **kwargs) -> list[list[float]]:
    """Embeddings de los chunks del corpus (lado 'documento' del retrieval)."""
    return _embed_with_prefix(texts, config.E5_PASSAGE_PREFIX, **kwargs)


def embed_query(text: str, **kwargs) -> list[float]:
    """Embedding de la consulta del usuario (lado 'pregunta' del retrieval)."""
    [vector] = _embed_with_prefix([text], config.E5_QUERY_PREFIX, **kwargs)
    return vector


# --- Backend: FAISS ---------------------------------------------------------

class FaissStore:
    """Indice FAISS plano + metadata paralela en memoria.

    IndexFlatIP sobre vectores normalizados = similitud de coseno exacta. A la
    escala del corpus de M3 (cientos-pocos miles de chunks) un indice plano es
    exacto y de sobra rapido; no hay razon para IVF/HNSW todavia.
    """

    def __init__(self, dim: int = config.EMBEDDING_DIM, index=None, metadata=None):
        self.dim = dim
        self._metadata: list[dict] = list(metadata or [])
        if index is not None:
            self.index = index
        else:
            import faiss  # import perezoso

            self.index = faiss.IndexFlatIP(dim)

    def __len__(self) -> int:
        return len(self._metadata)

    @property
    def metadata(self) -> list[dict]:
        return self._metadata

    def add(self, chunks: list, embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"chunks ({len(chunks)}) y embeddings ({len(embeddings)}) no coinciden: "
                "el indice y la metadata quedarian desalineados y cada busqueda "
                "devolveria la cita de otro chunk."
            )
        if not chunks:
            return
        self.index.add(normalize(embeddings))
        self._metadata.extend(chunk_to_metadata(c) for c in chunks)

    def search(self, query_embedding, top_k: int = config.TOP_K) -> list[SearchResult]:
        """Top-k por coseno, descartando chunks no vigentes.

        FAISS no filtra antes de buscar (esa es la ventaja concreta que se cedio
        al no usar pgvector, ver decision 2): se sobre-muestrea y se filtra en
        Python. A esta escala el costo es irrelevante.
        """
        if len(self._metadata) == 0:
            return []

        sobremuestreo = min(max(top_k * 4, top_k), len(self._metadata))
        scores, indices = self.index.search(normalize(query_embedding), sobremuestreo)

        resultados: list[SearchResult] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            meta = self._metadata[int(idx)]
            if not meta.get("vigente", True):
                continue
            resultados.append(metadata_to_result(meta, float(score)))
            if len(resultados) == top_k:
                break
        return resultados

    def save(
        self,
        index_path: Path = config.FAISS_INDEX_PATH,
        metadata_path: Path = config.FAISS_METADATA_PATH,
    ) -> None:
        import faiss

        index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_path))
        with Path(metadata_path).open("w", encoding="utf-8") as f:
            for meta in self._metadata:
                f.write(json.dumps(meta, ensure_ascii=False) + "\n")

    @classmethod
    def load(
        cls,
        index_path: Path = config.FAISS_INDEX_PATH,
        metadata_path: Path = config.FAISS_METADATA_PATH,
    ) -> "FaissStore":
        """Carga un indice ya construido (el caso de la consulta online).

        Verifica que indice y metadata tengan el mismo numero de filas: si se
        desincronizan, cada resultado vendria con la cita de otro chunk -- un
        fallo silencioso y exactamente del tipo que este proyecto no puede
        permitirse.
        """
        # La comprobacion va ANTES de importar faiss: si no, en un entorno sin
        # faiss (todo lo que no sea Colab) el mensaje util queda inalcanzable y
        # el error que se ve es un ModuleNotFoundError que no dice que hacer.
        index_path, metadata_path = Path(index_path), Path(metadata_path)
        if not index_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(
                f"No hay indice construido en {index_path} / {metadata_path}. "
                "Corre pipeline.build_index() primero (ver docs/m3_decisiones_rag.md)."
            )

        import faiss

        index = faiss.read_index(str(index_path))
        with metadata_path.open(encoding="utf-8") as f:
            metadata = [json.loads(line) for line in f if line.strip()]

        if index.ntotal != len(metadata):
            raise ValueError(
                f"Indice y metadata desalineados: {index.ntotal} vectores vs. "
                f"{len(metadata)} registros de metadata. Reconstruye el indice."
            )
        return cls(dim=index.d, index=index, metadata=metadata)


def get_store(backend: str = config.VECTOR_STORE_BACKEND, **kwargs) -> VectorStore:
    """Factory del backend configurado en config.py."""
    if backend == "faiss":
        return FaissStore(**kwargs)
    if backend == "pgvector":
        raise NotImplementedError(
            "pgvector no esta implementado en M3 a proposito: el repo todavia no "
            "tiene Postgres ni el backend FastAPI, y Colab (donde corren los "
            "embeddings) no alcanza un Postgres local. Ver la decision 2 en "
            "docs/m3_decisiones_rag.md -- se migra cuando el backend exista."
        )
    raise ValueError(f"Backend desconocido: {backend!r} (usa 'faiss')")
