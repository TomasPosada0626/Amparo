"""Regresion del pipeline de indexacion sobre el corpus real del repo.

Estos son los tests que faltaban cuando el chunker se escribio contra texto
legal sintetico: el corpus llego en Markdown y el patron de articulos, anclado a
inicio de linea, no reconocia NI UNO solo en 9 de las 10 normas -- y no fallaba,
simplemente indexaba chunks sin numero de articulo. El sistema habria podido
citar la ley pero nunca el articulo, que es la mitad de lo que el producto
promete. Cada assert de aca corresponde a algo que se rompio de verdad.

Corren sin GPU: solo ingest + chunk, nada de embeddings.
"""
import re

import pytest

from tools.rag import chunk, corpus, ingest

# Minimo de articulos que cada norma debe producir. Son cotas holgadas contra el
# articulado real de cada norma, no el numero exacto: la idea es detectar un
# derrumbe del patron (0, o una fraccion), no fijar el resultado a un numero que
# cambie con cualquier ajuste legitimo del chunker.
MINIMO_ARTICULOS = {
    "constitucion_politica_1991.md": 380,
    "cpaca_ley_1437_2011.md": 250,
    "tutela_decreto_2591_1991.md": 45,
    "seguridad_social_ley_100_1993.md": 250,
    "codigo_sustantivo_trabajo_decreto_2663_1950.md": 400,
    "arrendamiento_vivienda_urbana_ley_820_2003.md": 35,
    "habeas_data_financiero_ley_1266_2008.md": 18,
    "estatuto_consumidor_ley_1480_2011.md": 60,
    "codigo_nacional_transito_ley_769_2002.md": 140,
    "codigo_general_proceso_ley_1564_2012.md": 500,
}

_cache: dict[str, list] = {}


def chunks_de(filename: str) -> list:
    """Ingesta y chunkea una norma del corpus real, memoizando el resultado."""
    if filename not in _cache:
        entrada = next(
            e for e in corpus.to_ingest_manifest() if e["filename"] == filename
        )
        doc = ingest.ingest_document(
            ingest.config.RAW_CORPUS_DIR / filename,
            fuente=entrada["fuente"],
            tipo=entrada["tipo"],
            url_fuente=entrada["url_fuente"],
            vigente=entrada["vigente"],
        )
        _cache[filename] = chunk.chunk_document(
            {
                "doc_id": doc.doc_id,
                "text": doc.text,
                "fuente": doc.fuente,
                "tipo": doc.tipo,
                "url_fuente": doc.url_fuente,
                "vigente": doc.vigente,
            }
        )
    return _cache[filename]


@pytest.mark.parametrize("filename, minimo", sorted(MINIMO_ARTICULOS.items()))
def test_cada_norma_produce_suficientes_articulos_distintos(filename, minimo):
    """El test que habria atrapado el fallo: el Codigo Sustantivo del Trabajo
    tiene 620 menciones de articulo y el chunker detectaba 0."""
    articulos = {a for c in chunks_de(filename) for a in c.articulos_incluidos}

    assert len(articulos) >= minimo, (
        f"{filename}: solo {len(articulos)} articulos distintos (minimo {minimo}). "
        "Sintoma tipico: el patron de articulos dejo de reconocer el formato de la "
        "fuente -- revisa ingest.extract_markdown_text y chunk.ARTICLE_PATTERN."
    )


@pytest.mark.parametrize("filename", sorted(MINIMO_ARTICULOS))
def test_todo_chunk_del_corpus_real_es_citable(filename):
    """Un chunk sin numero de articulo solo se puede citar como "Ley 820 de
    2003", sin decir donde: es media cita, y el producto promete trazabilidad."""
    chunks = chunks_de(filename)

    sin_articulo = [c.chunk_id for c in chunks if not c.articulos_incluidos]
    assert not sin_articulo, f"{filename}: {len(sin_articulo)} chunks sin articulo"
    for c in chunks:
        assert c.fuente.strip() and c.url_fuente.strip()
        assert c.vigente is True


@pytest.mark.parametrize("filename", sorted(MINIMO_ARTICULOS))
def test_ningun_chunk_excede_el_presupuesto_de_tokens(filename):
    """El modelo de embeddings trunca en 512 tokens sin avisar: un chunk que se
    pasa del presupuesto queda indexado a medias y su cola es invisible para el
    retrieval."""
    excedidos = [
        (c.chunk_id, chunk.estimate_tokens(c.text))
        for c in chunks_de(filename)
        if chunk.estimate_tokens(c.text) > 350
    ]

    assert not excedidos, f"{filename}: chunks fuera de presupuesto: {excedidos[:3]}"


def test_el_markdown_no_se_cuela_en_el_texto_indexado():
    """Los `#` y `*` de la fuente llegarian al prompt del modelo como ruido."""
    for c in chunks_de("arrendamiento_vivienda_urbana_ley_820_2003.md"):
        assert "**" not in c.text
        assert not c.text.lstrip().startswith("#")


def test_el_frontmatter_no_se_indexa():
    """El frontmatter trae `modification_summary` con decenas de referencias a
    otras normas. Si se indexara, el retrieval devolveria ese bloque como si
    fuera articulado y el modelo citaria normas que no vienen al caso."""
    for c in chunks_de("arrendamiento_vivienda_urbana_ley_820_2003.md"):
        assert "modification_summary" not in c.text
        assert "gazette_reference" not in c.text


def test_recupera_el_articulo_correcto_de_una_consulta_tipica_del_dataset():
    """Chequeo de contenido, no solo de forma: el articulo que responde "me
    quieren sacar del arriendo" tiene que estar indexado y citable."""
    art22 = [
        c for c in chunks_de("arrendamiento_vivienda_urbana_ley_820_2003.md")
        if "22" in c.articulos_incluidos
    ]

    assert art22, "no se indexo el articulo 22 de la Ley 820 (causales de terminacion)"
    assert "terminaci" in art22[0].text.lower()


def test_la_constitucion_distingue_articulos_transitorios():
    """La Constitucion tiene un articulo 1 permanente y un articulo transitorio
    1, y son normas distintas: citarlos igual seria una cita equivocada."""
    articulos = {a for c in chunks_de("constitucion_politica_1991.md") for a in c.articulos_incluidos}

    assert "1" in articulos
    assert any(a.startswith("transitorio") for a in articulos)


def test_el_capitulo_se_captura_en_la_mayoria_de_los_chunks():
    """No es obligatorio (hay articulado antes del primer capitulo), pero si casi
    ninguno lo trae es que el patron de encabezados dejo de reconocer el formato."""
    chunks = chunks_de("codigo_general_proceso_ley_1564_2012.md")

    con_capitulo = sum(1 for c in chunks if c.capitulo)
    assert con_capitulo > len(chunks) * 0.5


def test_el_corpus_completo_en_alcance_se_indexa_sin_errores():
    """Camino completo de la mitad offline, salvo el embedding: si esto falla,
    build_index() falla en Colab despues de haber cargado el modelo."""
    docs = ingest.ingest_corpus(corpus.to_ingest_manifest())
    assert len(docs) == len(corpus.NORMAS_EN_ALCANCE)

    total = sum(len(chunks_de(n.filename)) for n in corpus.NORMAS_EN_ALCANCE)
    assert total > 2000, f"solo {total} chunks para 10 normas: el chunker esta perdiendo texto"


def test_no_hay_chunk_ids_repetidos_en_todo_el_corpus():
    """Un chunk_id repetido hace que dos chunks distintos compartan identidad, y
    en pgvector (cuando se migre) el segundo pisaria al primero."""
    ids = [c.chunk_id for n in corpus.NORMAS_EN_ALCANCE for c in chunks_de(n.filename)]

    assert len(ids) == len(set(ids))


def test_los_numeros_de_articulo_tienen_forma_de_numero_de_articulo():
    """Detecta falsos positivos del patron: si empezara a capturar fechas o
    montos, apareceria un "articulo 45244" (el numero del Diario Oficial)."""
    patron = re.compile(r"^(transitorio )?\d{1,4}[a-zA-Z]?$")

    for filename in MINIMO_ARTICULOS:
        for c in chunks_de(filename):
            for articulo in c.articulos_incluidos:
                assert patron.match(articulo), f"{filename}: articulo raro {articulo!r}"
