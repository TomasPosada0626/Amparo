"""Ingest: fuentes crudas -> texto plano con metadata de procedencia.

Etapa 1 de 7 del pipeline RAG (S07). Offline / indexacion.

El corpus real de M3 vive en data/corpus/normas/ como Markdown con frontmatter
YAML (ver docs/m3_decisiones_rag.md, decision 1). Ese frontmatter trae la
metadata citable ya verificada por quien armo el corpus -- `source` (URL de
SUIN-Juriscol), `identifier`, `rank`, `status` -- asi que no hay que declararla
a mano: se lee del archivo. Se mantienen HTML y PDF por si en algun momento se
vuelve a descargar de la fuente oficial directamente.

fuente / tipo / url_fuente siguen sin inferirse del nombre del archivo: salen
del frontmatter o los declara corpus.py, porque son exactamente los campos que
permiten citar de forma verificable.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from tools.rag import config

# Tags de bloque que en HTML implican un salto de linea visual. Se convierten en
# "\n" ANTES de quitar los tags porque la estructura de parrafo es lo unico que
# le queda al chunker para detectar donde empieza un articulo: si se colapsa
# todo a un solo espacio, una norma entera queda como un unico chunk gigante.
_BLOCK_TAGS = r"p|div|br|tr|li|h[1-6]|table|section|article|blockquote"
_BLOCK_TAG_RE = re.compile(rf"</?\s*(?:{_BLOCK_TAGS})\b[^>]*>", re.IGNORECASE)
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
_ANY_TAG_RE = re.compile(r"<[^>]+>")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)

# Entidades HTML mas comunes en los portales normativos colombianos. Se usa
# html.unescape (stdlib) para el resto; esta tabla solo cubre el no-break space,
# que conviene tratar como espacio normal y no como caracter invisible.
_NBSP = " "

# --- Markdown ---------------------------------------------------------------
# El corpus viene con el articulado envuelto en sintaxis de Markdown:
#   ##### **Artículo 1º.** *Objeto*. La presente ley...
#   ### **CAPITULO I**
# Esa envoltura se quita aca, en ingest, y no en el chunker: es un problema de
# formato de la fuente, no de estructura normativa. Al limpiarla, el encabezado
# del articulo vuelve a quedar al inicio de la linea, que es lo que el patron
# anclado de chunk.py necesita -- y ese anclaje es justo lo que evita que cada
# referencia cruzada ("...segun el articulo 23 de esta ley") parta un chunk.
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
_CAMPO_FRONTMATTER_RE = re.compile(r'^(\w+):\s*"?(.*?)"?\s*$', re.M)
_ENCABEZADO_MD_RE = re.compile(r"^[ \t]*#{1,6}[ \t]*", re.M)
_ENFASIS_MD_RE = re.compile(r"\*+")


@dataclass
class RawDocument:
    doc_id: str
    text: str
    fuente: str
    tipo: str
    url_fuente: str
    fecha_consulta: str
    vigente: bool = True


def extract_pdf_text(path: Path) -> str:
    """Extrae texto de un PDF. Requiere pypdf (ya esta en requirements.txt)."""
    from pypdf import PdfReader  # import perezoso: solo se necesita aqui

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_html_text(raw: str) -> str:
    """HTML -> texto plano preservando los saltos de parrafo.

    Deliberadamente sin beautifulsoup4: el HTML de los portales normativos es
    simple (texto de la norma en parrafos) y no justifica una dependencia nueva.
    Si en algun momento hace falta (tablas anidadas, texto en atributos),
    documentar el cambio como decision explicita en docs/m3_decisiones_rag.md.
    """
    import html as html_module

    text = _HTML_COMMENT_RE.sub(" ", raw)
    text = _SCRIPT_STYLE_RE.sub(" ", text)
    text = _BLOCK_TAG_RE.sub("\n", text)  # antes de borrar los tags, no despues
    text = _ANY_TAG_RE.sub(" ", text)
    text = html_module.unescape(text).replace(_NBSP, " ")

    # Normaliza espacios dentro de cada linea, pero conserva los saltos.
    lineas = [re.sub(r"[ \t]+", " ", linea).strip() for linea in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(l for l in lineas if l))


def split_frontmatter(raw: str) -> tuple[dict, str]:
    """Separa el frontmatter YAML del cuerpo del documento.

    Parser deliberadamente minimo (clave: valor de primer nivel), sin PyYAML:
    es lo unico que trae el corpus y no justifica una dependencia nueva. Si
    alguna vez hace falta YAML anidado, documentar el cambio como decision.
    """
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    campos = dict(_CAMPO_FRONTMATTER_RE.findall(match.group(1)))
    return campos, raw[match.end():]


def extract_markdown_text(raw: str) -> str:
    """Markdown del corpus -> texto plano, sin frontmatter ni sintaxis.

    Quita los `#` de encabezado y los `*` de enfasis. Sin esto, el articulado
    llega al chunker como "##### **Artículo 1º.**" y el patron anclado a inicio
    de linea no reconoce ni un solo articulo: la norma entera se indexa sin
    numero de articulo y el sistema puede citar la ley pero nunca el articulo.
    """
    _, cuerpo = split_frontmatter(raw)
    cuerpo = _ENCABEZADO_MD_RE.sub("", cuerpo)
    cuerpo = _ENFASIS_MD_RE.sub("", cuerpo)
    lineas = [re.sub(r"[ \t]+", " ", linea).rstrip() for linea in cuerpo.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lineas)).strip()


def read_frontmatter(path: Path) -> dict:
    """Lee solo el frontmatter de un archivo del corpus, sin procesar el cuerpo."""
    with path.open(encoding="utf-8", errors="ignore") as f:
        cabecera = f.read(8192)  # el frontmatter mas largo del corpus no llega a 4 KB
    campos, _ = split_frontmatter(cabecera)
    return campos


def extract_text(path: Path) -> str:
    """Despacha por extension del archivo."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix in (".html", ".htm"):
        return extract_html_text(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix in (".md", ".markdown"):
        return extract_markdown_text(path.read_text(encoding="utf-8", errors="ignore"))
    return path.read_text(encoding="utf-8", errors="ignore")


def ingest_document(
    path: Path,
    *,
    fuente: str,
    tipo: str,
    url_fuente: str,
    vigente: bool = True,
) -> RawDocument:
    """Ingesta un documento individual con su metadata de procedencia."""
    if not url_fuente.strip():
        raise ValueError(
            f"{path.name}: no se ingiere un documento sin url_fuente verificada "
            f"(ver tools/rag/corpus.py y docs/m3_decisiones_rag.md, decision 1)."
        )

    return RawDocument(
        doc_id=path.stem,
        text=extract_text(path),
        fuente=fuente,
        tipo=tipo,
        url_fuente=url_fuente,
        fecha_consulta=date.today().isoformat(),
        vigente=vigente,
    )


def ingest_corpus(
    manifest: list[dict], *, raw_dir: Path = config.RAW_CORPUS_DIR
) -> list[RawDocument]:
    """Ingesta el corpus completo a partir del manifiesto.

    manifest: la salida de corpus.to_ingest_manifest() -- lista de dicts con
    filename / fuente / tipo / url_fuente / vigente.
    """
    docs: list[RawDocument] = []
    faltantes: list[str] = []
    for entry in manifest:
        path = raw_dir / entry["filename"]
        if not path.exists():
            faltantes.append(entry["filename"])
            continue
        docs.append(
            ingest_document(
                path,
                fuente=entry["fuente"],
                tipo=entry["tipo"],
                url_fuente=entry["url_fuente"],
                vigente=entry.get("vigente", True),
            )
        )

    if faltantes:
        raise FileNotFoundError(
            f"Faltan {len(faltantes)} archivos del corpus en {raw_dir}:\n  - "
            + "\n  - ".join(faltantes)
            + "\nDescargalos de los portales oficiales (ver corpus.PORTALES_OFICIALES)."
        )
    return docs


def save_processed(
    docs: list[RawDocument], path: Path = config.PROCESSED_CORPUS_PATH
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(asdict(doc), ensure_ascii=False) + "\n")


def load_processed(path: Path = config.PROCESSED_CORPUS_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


if __name__ == "__main__":
    from tools.rag import corpus

    documents = ingest_corpus(corpus.to_ingest_manifest())
    save_processed(documents)
    print(f"Ingestados {len(documents)} documentos -> {config.PROCESSED_CORPUS_PATH}")
