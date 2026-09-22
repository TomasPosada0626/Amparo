"""Chunk: divide texto legal respetando la unidad normativa.

Etapa 2 de 7 del pipeline RAG (S07). Offline / indexacion.

Decision de diseno (docs/m3_decisiones_rag.md, seccion 4): NO usar chunking de
tamano fijo ciego. La unidad natural de una norma es el articulo, y cortar un
articulo a la mitad suele partir justo la condicion o la excepcion -- en dominio
legal eso no degrada la respuesta, la invierte.

Estrategia jerarquica:
  1. Dividir por articulo (patron anclado a inicio de linea).
  2. Articulo que excede el presupuesto -> subdividir por parrafo, y si el HTML
     venia en una sola linea, por oracion. Nunca a mitad de oracion.
  3. Articulos muy cortos -> agrupar los consecutivos, conservando cada numero
     de articulo en `articulos_incluidos` para no perder trazabilidad.
  4. El capitulo/titulo vigente se arrastra como metadata (`capitulo`), no se
     fusiona con el texto.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from tools.rag import config

# Arranque de articulo en normas colombianas: "Articulo 14.", "ARTÍCULO 14o.",
# "Art. 14 -".
#
# El ancla a inicio de linea NO es cosmetica: los textos legales se
# referencian a si mismos todo el tiempo ("de conformidad con el articulo 23 de
# la Ley 1755 de 2015"), y sin el ancla cada una de esas menciones abriria un
# chunk nuevo a mitad de un articulo. Por eso ingest.extract_html_text()
# preserva los saltos de parrafo: si se colapsa el espacio en blanco, este
# patron no encuentra nada y la norma entera queda como un solo chunk.
#
# El corpus llega ya sin sintaxis de Markdown (ingest.extract_markdown_text lo
# limpia), asi que el encabezado del articulo queda al inicio de la linea. Se
# aceptan tambien "Articulo" sin tilde -- media docena de normas del corpus lo
# escriben asi -- y los articulos transitorios de la Constitucion.
ARTICLE_PATTERN = re.compile(
    r"^[ \t]*(?:art[íi]culo|art[íi]c\.|art\.)[ \t]*"
    r"(?P<transitorio>transitorio[ \t]+)?"
    r"(?P<numero>\d+[a-zA-Z]?)[ \t]*(?:[°ºo]\b)?[ \t]*[\.\-–:)]?",
    re.IGNORECASE | re.MULTILINE,
)

# Encabezados de jerarquia superior, que se arrastran como metadata.
HEADING_PATTERN = re.compile(
    r"^[ \t]*((?:libro|parte|t[íi]tulo|cap[íi]tulo|secci[óo]n)"
    r"[ \t]+[^\n]{0,80})$",
    re.IGNORECASE | re.MULTILINE,
)

# Fin de oracion, para el fallback de articulos largos sin saltos de linea.
SENTENCE_END_PATTERN = re.compile(r"(?<=[\.;:])\s+")

# Relacion palabras -> tokens en espanol medida en M1 (~1.6 tokens/palabra).
TOKENS_PER_WORD = 1.6


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    fuente: str
    tipo: str
    url_fuente: str
    articulos_incluidos: list[str] = field(default_factory=list)
    capitulo: str = ""
    vigente: bool = True


@dataclass
class ArticleSpan:
    """Un articulo localizado dentro del texto de un documento."""

    numero: str  # "" si el fragmento no tiene estructura de articulo
    texto: str
    capitulo: str = ""


def estimate_tokens(text: str) -> int:
    """Estimacion rapida sin cargar un tokenizador real.

    Suficiente para decidir donde cortar; no usar para presupuestos criticos de
    ventana de contexto -- para eso hay que tokenizar de verdad con el
    tokenizador de Qwen2.5.
    """
    return int(len(text.split()) * TOKENS_PER_WORD)


def normalizar_numero(numero: str) -> str:
    """Quita la marca de ordinal de la forma "5o" -> "5".

    Las normas colombianas mas antiguas (el Codigo Sustantivo del Trabajo, entre
    otras) escriben "ARTICULO 5o." por "5º". Sin normalizar, ese articulo se
    citaria como "Articulo 5o" y no coincidiria con el "Articulo 5" del resto del
    corpus. La letra final SI se conserva cuando no es la marca de ordinal, para
    no romper los articulos bis del tipo "Articulo 14A".
    """
    if len(numero) > 1 and numero[-1] in "oO" and numero[:-1].isdigit():
        return numero[:-1]
    return numero


def split_by_article(text: str) -> list[ArticleSpan]:
    """Divide el texto en articulos, arrastrando el capitulo vigente.

    Si no hay ningun patron de articulo (p. ej. un fragmento de sentencia sin
    esa estructura), devuelve todo el texto como un unico span con numero "".
    Lo que aparece antes del primer articulo (titulo de la norma,
    considerandos) se descarta: no es texto normativo citable por articulo.
    """
    matches = list(ARTICLE_PATTERN.finditer(text))
    if not matches:
        limpio = text.strip()
        return [ArticleSpan(numero="", texto=limpio)] if limpio else []

    encabezados = [(m.start(), m.group(1).strip()) for m in HEADING_PATTERN.finditer(text)]

    spans: list[ArticleSpan] = []
    for i, match in enumerate(matches):
        inicio = match.start()
        fin = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        capitulo = ""
        for pos, titulo in encabezados:
            if pos < inicio:
                capitulo = titulo
            else:
                break
        cuerpo = text[inicio:fin].strip()
        if cuerpo:
            numero = normalizar_numero(match.group("numero"))
            if match.group("transitorio"):
                # La cita correcta es "Articulo transitorio 19", no "Articulo 19":
                # la Constitucion tiene ambos y son normas distintas.
                numero = f"transitorio {numero}"
            spans.append(ArticleSpan(numero=numero, texto=cuerpo, capitulo=capitulo))
    return spans


def split_long_text(texto: str, max_tokens: int) -> list[str]:
    """Subdivide un articulo que excede el presupuesto, sin partir oraciones.

    Primero por parrafo. Si el articulo no tiene saltos de linea internos
    (pasa con HTML de una sola linea), cae a division por oracion -- sin este
    fallback el articulo se pasaria del presupuesto igual, y el "max_tokens" no
    seria mas que decorativo.
    """
    if estimate_tokens(texto) <= max_tokens:
        return [texto]

    unidades: list[str] = []
    for parrafo in (p.strip() for p in texto.split("\n")):
        if not parrafo:
            continue
        # Un parrafo que por si solo excede el presupuesto se parte en oraciones.
        # Sin esto, un articulo de varios parrafos donde UNO es enorme seguia
        # produciendo un chunk gigante, y el modelo de embeddings lo truncaria en
        # silencio a sus 512 tokens: la cola del articulo quedaria fuera del
        # indice sin que nada lo indique.
        if estimate_tokens(parrafo) > max_tokens:
            unidades.extend(s.strip() for s in SENTENCE_END_PATTERN.split(parrafo) if s.strip())
        else:
            unidades.append(parrafo)

    piezas: list[str] = []
    buffer = ""
    for unidad in unidades:
        candidato = f"{buffer}\n{unidad}".strip() if buffer else unidad
        if buffer and estimate_tokens(candidato) > max_tokens:
            piezas.append(buffer)
            buffer = unidad
        else:
            buffer = candidato
    if buffer:
        piezas.append(buffer)
    return piezas or [texto]


def chunk_document(
    doc: dict,
    *,
    max_tokens: int = config.MAX_TOKENS_PER_CHUNK,
    min_tokens: int = config.MIN_TOKENS_PER_CHUNK,
) -> list[Chunk]:
    """Convierte un documento ingerido (ver ingest.py) en una lista de Chunk.

    doc debe traer doc_id, text, fuente, tipo, url_fuente y (opcional) vigente
    -- los mismos campos que produce ingest.RawDocument.
    """
    chunks: list[Chunk] = []
    pendientes: list[ArticleSpan] = []  # articulos cortos acumulados
    contador = 0

    def nuevo_chunk(texto: str, articulos: list[str], capitulo: str) -> None:
        nonlocal contador
        contador += 1
        chunks.append(
            Chunk(
                chunk_id=f"{doc['doc_id']}::chunk{contador}",
                doc_id=doc["doc_id"],
                text=texto,
                fuente=doc["fuente"],
                tipo=doc["tipo"],
                url_fuente=doc["url_fuente"],
                articulos_incluidos=articulos,
                capitulo=capitulo,
                vigente=doc.get("vigente", True),
            )
        )

    def cerrar_pendientes() -> None:
        if not pendientes:
            return
        nuevo_chunk(
            texto="\n\n".join(s.texto for s in pendientes),
            articulos=[s.numero for s in pendientes if s.numero],
            capitulo=pendientes[0].capitulo,
        )
        pendientes.clear()

    for span in split_by_article(doc["text"]):
        if estimate_tokens(span.texto) < min_tokens:
            # Articulo corto: se agrupa con los cortos contiguos, no se descarta.
            # Si el grupo acumulado ya llega al presupuesto, se cierra antes de
            # seguir sumando.
            pendientes.append(span)
            if estimate_tokens("\n\n".join(s.texto for s in pendientes)) >= max_tokens:
                cerrar_pendientes()
            continue

        cerrar_pendientes()
        for pieza in split_long_text(span.texto, max_tokens):
            nuevo_chunk(
                texto=pieza,
                articulos=[span.numero] if span.numero else [],
                capitulo=span.capitulo,
            )

    cerrar_pendientes()
    return chunks


def chunk_corpus(docs: list[dict]) -> list[Chunk]:
    todos: list[Chunk] = []
    for doc in docs:
        todos.extend(chunk_document(doc))
    return todos


if __name__ == "__main__":
    from dataclasses import asdict

    from tools.rag import ingest

    documentos = ingest.load_processed()
    resultado = chunk_corpus(documentos)
    print(f"{len(documentos)} documentos -> {len(resultado)} chunks")
    if resultado:
        print("Ejemplo:", asdict(resultado[0]))
