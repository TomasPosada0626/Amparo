"""Configuracion central del RAG ingenuo de Amparo (M3, alcance S07).

Mismo patron que tools/evaluation/config.py: constantes puras, sin imports
pesados a nivel de modulo, para que sea importable sin GPU, sin faiss y sin
conexion a base de datos (p. ej. desde los tests).

Las decisiones que sustentan estos valores estan documentadas en
docs/m3_decisiones_rag.md -- si cambias uno, actualiza tambien esa seccion.
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# --- Corpus -----------------------------------------------------------------
# Decision 1 (docs/m3_decisiones_rag.md): de las 17 normas descargadas se
# indexan las 10 que cubren las 9 categorias cotidianas de mayor frecuencia del
# dataset de M1. El corpus esta versionado en el repo, en Markdown con
# frontmatter YAML. Las normas concretas, su mapeo a categorias y las
# exclusiones viven en corpus.py, no aqui.
RAW_CORPUS_DIR = PROJECT_ROOT / "data" / "corpus" / "normas"
PROCESSED_CORPUS_PATH = PROJECT_ROOT / "data" / "rag_corpus_processed.jsonl"

# --- Chunking ---------------------------------------------------------------
# Presupuesto de tokens por chunk. Si un articulo excede esto se subdivide por
# parrafo (y, en HTML sin saltos de linea, por oracion) -- nunca a mitad de
# oracion: en una norma, la mitad cortada suele ser la condicion o la excepcion.
MAX_TOKENS_PER_CHUNK = 350
MIN_TOKENS_PER_CHUNK = 40  # articulos mas cortos se agrupan entre si

# --- Embeddings -------------------------------------------------------------
# Decision 3: e5 multilingue, elegido por ser un modelo entrenado para retrieval
# asimetrico (consulta coloquial -> texto normativo), que es el caso de Amparo.
EMBEDDING_MODEL_ID = "intfloat/multilingual-e5-base"
EMBEDDING_DIM = 768

# e5 NO es opcional en esto: fue entrenado con estos prefijos y omitirlos (o
# intercambiarlos) degrada el retrieval en silencio -- no falla, solo recupera
# peor. embed_store.py expone embed_query()/embed_passages() por separado para
# que el prefijo no dependa de que quien llame se acuerde.
E5_QUERY_PREFIX = "query: "
E5_PASSAGE_PREFIX = "passage: "

EMBEDDING_MAX_LENGTH = 512  # limite de tokens del encoder
EMBEDDING_BATCH_SIZE = 16

# --- Vector store -----------------------------------------------------------
# Decision 2: FAISS ahora, pgvector cuando exista el backend FastAPI+Postgres.
# La razon completa (Colab no alcanza un Postgres local; Postgres todavia no
# existe en el repo) esta en docs/m3_decisiones_rag.md, seccion 2.
VECTOR_STORE_BACKEND = "faiss"

# artifacts/ ya esta en .gitignore: el indice es salida generada, no fuente.
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
FAISS_INDEX_PATH = ARTIFACTS_DIR / "rag_index.faiss"
FAISS_METADATA_PATH = ARTIFACTS_DIR / "rag_index_metadata.jsonl"

# --- Retrieval --------------------------------------------------------------
TOP_K = 5

# Umbral de la valvula de escape: por debajo de esto, el chunk NO entra al
# prompt y el sistema responde "no tengo informacion verificada".
#
# OJO -- SIN CALIBRAR (ver docs/m3_decisiones_rag.md, seccion 5). Los cosenos de
# e5 son poco dispersos: dos textos sin relacion alguna suelen dar ~0.70-0.75,
# asi que un piso bajo (como el 0.3 tipico de otros modelos) dejaria pasar
# cualquier cosa y la valvula de escape nunca se activaria. 0.80 es un punto de
# partida derivado de ese rango, no una medicion: hay que correr consultas con y
# sin cobertura en el corpus, mirar la distribucion de scores y anotar el
# resultado en la seccion 5 de ese documento.
RETRIEVAL_MIN_SCORE = 0.80

# --- Generacion -------------------------------------------------------------
BASE_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"  # mismo que tools/evaluation/config.py
MAX_NEW_TOKENS_GENERATION = 300

# Ruta al adaptador LoRA de M1. Igual que en tools/evaluation/config.py, las
# rutas de Drive son simples strings: no se tocan fuera de Colab, asi que este
# modulo sigue siendo seguro de importar en cualquier parte.
DRIVE_ROOT = "/content/drive/MyDrive/Colab Notebooks/Amparo"
LORA_ADAPTER_PATH: str | None = f"{DRIVE_ROOT}/amparo-lora-adapter"
