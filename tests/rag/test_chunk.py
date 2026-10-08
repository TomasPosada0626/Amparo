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


def test_los_articulos_bis_conservan_su_sufijo():
    """RAG-3: el patron solo recogia el sufijo si iba pegado ("14A").

    El corpus los escribe de tres formas y las tres se perdian: la Ley 100 usa
    "151-A", la Ley 1266 usa "19 A" y el Codigo Penal usa "185 a". Resultado:
    los siete articulos 151 de la Ley 100 quedaban todos como "151" y el prompt
    citaba "Articulo 151" con el texto de otro.
    """
    texto = ("Articulo 151. Texto del permanente.\n\n"
             "Articulo 151-A. Pension familiar.\n\n"
             "Articulo 19 A. Responsabilidad demostrada.\n\n"
             "Articulo 185 a. Intimidacion con arma.\n\n"
             "Articulo 14A. Pegado sin separador.")
    assert [s.numero for s in chunk.split_by_article(texto)] == [
        "151", "151-A", "19-A", "185-A", "14-A"]


def test_una_referencia_interna_no_abre_un_articulo_nuevo():
    """RAG-4: en la Constitucion, una referencia que cae al inicio de linea al
    reflowear el texto partia el articulo anterior por la mitad. Pasaba con los
    articulos 74, 155, 156, 179 y 357."""
    texto = ("Articulo 155. El Congreso debatira el proyecto en la forma prevista en el\n"
             "articulo 156, o por iniciativa popular en los casos previstos.\n\n"
             "Articulo 157. Ningun proyecto sera ley sin los requisitos.")
    numeros = [s.numero for s in chunk.split_by_article(texto)]
    assert numeros == ["155", "157"], f"abrio un articulo de mas: {numeros}"
    assert "articulo 156" in chunk.split_by_article(texto)[0].texto


def test_un_encabezado_en_minuscula_tras_linea_en_blanco_si_cuenta():
    """El criterio no puede ser la mayuscula: el Codigo de Procedimiento Penal
    escribe "articulo 287." en minuscula y es un encabezado real."""
    texto = ("Articulo 286. Concepto de la formulacion.\n\n"
             "articulo 287. situaciones que determinan la imputacion.\n\n"
             "Articulo 288. Contenido.")
    assert [s.numero for s in chunk.split_by_article(texto)] == ["286", "287", "288"]


def test_lo_que_se_indexa_lleva_la_norma_y_el_articulo():
    """RAG-6: se embebia el texto pelado, sin decir de que norma venia.

    Para el embedding denso "64" no significa nada y el nombre de la norma no
    estaba en el vector, asi que "que dice el articulo 64 del Codigo Sustantivo
    del Trabajo" no tenia contra que empatar. En la demo de S08, A y B devolvian
    los articulos 46, 158, 165 y 468, y solo C lo encontraba, por BM25.
    """
    c = chunk.Chunk(
        chunk_id="cst::chunk1", doc_id="cst",
        text="Articulo 64. Son justas causas para dar por terminado el contrato.",
        fuente="Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo)",
        tipo="ley", url_fuente="http://x", articulos_incluidos=["64"],
    )
    indexable = chunk.texto_indexable(c)

    assert indexable.startswith("Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo), Articulo 64")
    assert c.text in indexable
    # El text del chunk no cambia: el prompt lo arma format_context, que ya pone
    # la cita arriba, asi que duplicarla ahi la repetiria.
    assert not c.text.startswith("Decreto 2663")


def test_el_texto_indexable_usa_plural_con_varios_articulos():
    c = chunk.Chunk(
        chunk_id="x::1", doc_id="x", text="Texto agrupado.", fuente="Ley 820 de 2003",
        tipo="ley", url_fuente="http://x", articulos_incluidos=["18", "19"],
    )
    assert chunk.texto_indexable(c).startswith("Ley 820 de 2003, Articulos 18, 19")
