from tools.rag import chunk

# Fragmento con la forma real del texto normativo colombiano una vez pasa por
# ingest.extract_html_text(): un articulo por parrafo, encabezados de capitulo
# en su propia linea.
TEXTO_LEGAL = """\
LEY 1755 DE 2015

CAPITULO I
Derecho de peticion ante autoridades

ARTÍCULO 13. Objeto y modalidades del derecho de peticion ante autoridades.
Toda persona tiene derecho a presentar peticiones respetuosas a las autoridades,
en los terminos senalados en este codigo, por motivos de interes general o
particular, y a obtener pronta resolucion completa y de fondo sobre la misma.

ARTÍCULO 14. Terminos para resolver las distintas modalidades de peticiones.
Salvo norma legal especial y so pena de sancion disciplinaria, toda peticion
debera resolverse dentro de los quince (15) dias siguientes a su recepcion.
"""


def doc(text: str, **overrides) -> dict:
    base = {
        "doc_id": "ley_1755_2015",
        "text": text,
        "fuente": "Ley 1755 de 2015 (Derecho de peticion)",
        "tipo": "ley",
        "url_fuente": "https://www.funcionpublica.gov.co/eva/gestornormativo/ejemplo",
        "vigente": True,
    }
    base.update(overrides)
    return base


def test_divide_por_articulo_y_no_parte_el_texto_del_articulo():
    spans = chunk.split_by_article(TEXTO_LEGAL)

    assert [s.numero for s in spans] == ["13", "14"]
    # El texto de cada articulo llega completo: si el chunker cortara aqui,
    # cortaria justo la condicion o la excepcion de la norma.
    assert "quince (15) dias" in spans[1].texto
    assert "pronta resolucion completa" in spans[0].texto


def test_arrastra_el_capitulo_como_metadata_sin_fusionarlo_en_el_texto():
    spans = chunk.split_by_article(TEXTO_LEGAL)

    assert all(s.capitulo.upper().startswith("CAPITULO I") for s in spans)
    assert "CAPITULO I" not in spans[0].texto


def test_las_referencias_cruzadas_no_abren_un_chunk_nuevo():
    """Los textos legales se citan a si mismos todo el tiempo ("de conformidad
    con el articulo 23..."). Sin el ancla a inicio de linea, cada una de esas
    menciones partiria un articulo a la mitad."""
    texto = (
        "ARTÍCULO 30. Peticiones entre autoridades. Cuando una autoridad formule "
        "una peticion de informacion de conformidad con el articulo 23 de esta "
        "ley, debera resolverse en los terminos del articulo 14."
    )
    spans = chunk.split_by_article(texto)

    assert len(spans) == 1
    assert spans[0].numero == "30"


def test_reconoce_las_variantes_de_escritura_del_encabezado():
    variantes = [
        "Artículo 5. Contenido.",
        "ARTICULO 5o. Contenido.",
        "Art. 5 - Contenido.",
        "ARTÍCULO 5°. Contenido.",
    ]
    for texto in variantes:
        spans = chunk.split_by_article(texto)
        assert [s.numero for s in spans] == ["5"], texto


def test_texto_sin_estructura_de_articulo_queda_como_un_solo_span():
    """Pasa con fragmentos de sentencias, que se numeran por numeral y no por
    articulo -- no se descartan, quedan con numero vacio."""
    spans = chunk.split_by_article("La Sala considera que el derecho fundamental...")

    assert len(spans) == 1
    assert spans[0].numero == ""


def test_articulo_largo_se_divide_por_parrafo_sin_partir_oraciones():
    parrafos = "\n".join(f"Parrafo {i} de la norma con contenido suficiente." * 12 for i in range(6))
    texto = f"ARTÍCULO 20. Encabezado del articulo.\n{parrafos}"

    piezas = chunk.split_long_text(texto, max_tokens=200)

    assert len(piezas) > 1
    for pieza in piezas:
        assert chunk.estimate_tokens(pieza) <= 200 or "\n" not in pieza
        assert pieza.strip().endswith(".")


def test_articulo_largo_en_una_sola_linea_cae_a_division_por_oracion():
    """Sin este fallback, un articulo que viene del HTML en una sola linea no se
    puede dividir por parrafo y se pasaria del presupuesto igual -- max_tokens
    quedaria siendo decorativo."""
    una_linea = " ".join(
        f"Esta es la oracion numero {i} del articulo y describe una obligacion." for i in range(40)
    )

    piezas = chunk.split_long_text(una_linea, max_tokens=120)

    assert len(piezas) > 1
    assert all(chunk.estimate_tokens(p) <= 200 for p in piezas)


def test_texto_corto_no_se_subdivide():
    assert chunk.split_long_text("ARTÍCULO 1. Objeto de la ley.", max_tokens=350) == [
        "ARTÍCULO 1. Objeto de la ley."
    ]


def test_articulos_cortos_consecutivos_se_agrupan_conservando_cada_numero():
    texto = (
        "ARTÍCULO 1. Objeto.\n"
        "ARTÍCULO 2. Ambito.\n"
        "ARTÍCULO 3. Vigencia.\n"
    )
    chunks = chunk.chunk_document(doc(texto), min_tokens=40)

    assert len(chunks) == 1, "tres articulos cortos deberian quedar en un solo chunk"
    # Agrupar no puede costar trazabilidad: cada articulo sigue citable.
    assert chunks[0].articulos_incluidos == ["1", "2", "3"]


def test_cada_chunk_lleva_la_metadata_que_permite_citarlo():
    """Es la condicion dura del producto: un chunk sin fuente/articulo/url no se
    puede convertir en una cita verificable (ver PRODUCT.md, principio 1)."""
    chunks = chunk.chunk_document(doc(TEXTO_LEGAL))

    assert chunks
    for c in chunks:
        assert c.fuente == "Ley 1755 de 2015 (Derecho de peticion)"
        assert c.url_fuente.startswith("https://")
        assert c.doc_id == "ley_1755_2015"
        assert c.tipo == "ley"
        assert c.vigente is True
        assert c.text.strip() != ""
    assert [c.articulos_incluidos for c in chunks] == [["13"], ["14"]]


def test_los_chunk_id_son_unicos_dentro_del_documento():
    chunks = chunk.chunk_document(doc(TEXTO_LEGAL))
    ids = [c.chunk_id for c in chunks]

    assert len(ids) == len(set(ids))
    assert all(i.startswith("ley_1755_2015::chunk") for i in ids)


def test_la_vigencia_del_documento_se_propaga_a_sus_chunks():
    """Una norma derogada no se borra del corpus, se marca -- y el retrieval la
    filtra. Si la marca no se propagara al chunk, el filtro no veria nada."""
    chunks = chunk.chunk_document(doc(TEXTO_LEGAL, vigente=False))

    assert chunks and all(c.vigente is False for c in chunks)


def test_chunk_corpus_procesa_varios_documentos():
    docs = [doc(TEXTO_LEGAL), doc(TEXTO_LEGAL, doc_id="ley_820_2003")]
    chunks = chunk.chunk_corpus(docs)

    assert len({c.doc_id for c in chunks}) == 2
    assert len(chunks) == 4


def test_distingue_los_articulos_transitorios_de_los_permanentes():
    """La Constitucion tiene un articulo 1 permanente y un articulo transitorio 1,
    y son normas distintas: citarlos igual seria una cita equivocada."""
    texto = "Artículo 1. Colombia es un Estado social de derecho.\nArtículo transitorio 1. Convócase a elecciones."
    spans = chunk.split_by_article(texto)

    assert [s.numero for s in spans] == ["1", "transitorio 1"]


def test_un_parrafo_gigante_dentro_de_un_articulo_largo_tambien_se_divide():
    """Antes se dividia solo por parrafo: un articulo de varios parrafos donde UNO
    era enorme seguia produciendo un chunk fuera de presupuesto, que el modelo de
    embeddings truncaria en silencio a sus 512 tokens."""
    corto = "Parrafo corto del articulo."
    gigante = " ".join(f"Esta es la oracion {i} de un inciso larguisimo." for i in range(60))
    piezas = chunk.split_long_text(f"{corto}\n{gigante}", max_tokens=120)

    assert len(piezas) > 2
    assert all(chunk.estimate_tokens(p) <= 200 for p in piezas)
