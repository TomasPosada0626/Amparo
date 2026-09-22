import pytest

from tools.rag import chunk, ingest

# HTML con la forma en que los portales normativos publican el texto: cada
# articulo en su propio <p>, mas menu y scripts alrededor.
HTML_NORMA = """\
<html><head><title>Ley 1755 de 2015</title>
<style>.menu{color:red}</style>
<script>var x = 1;</script></head>
<body>
<div class="menu">Inicio | Normativa</div>
<p>ARTÍCULO 13. Objeto y modalidades del derecho de petici&oacute;n.</p>
<p>Toda persona tiene derecho a presentar peticiones respetuosas.</p>
<p>ARTÍCULO 14. T&eacute;rminos para resolver.&nbsp;Toda petici&oacute;n deber&aacute;
resolverse dentro de los quince (15) d&iacute;as siguientes.</p>
</body></html>
"""


def test_la_extraccion_preserva_los_saltos_de_parrafo():
    """Es la condicion que hace funcionar al chunker: si el HTML se colapsa a un
    solo espacio (como hacia la plantilla original), el patron de articulos no
    encuentra nada y la norma entera queda como un unico chunk gigante."""
    texto = ingest.extract_html_text(HTML_NORMA)

    assert "\n" in texto
    lineas_de_articulo = [l for l in texto.split("\n") if l.startswith("ARTÍCULO")]
    assert len(lineas_de_articulo) == 2


def test_el_texto_extraido_es_chunkeable_por_articulo():
    """El test que de verdad importa: la salida de ingest tiene que servirle de
    entrada al chunker. Se prueban juntos a proposito."""
    texto = ingest.extract_html_text(HTML_NORMA)
    spans = chunk.split_by_article(texto)

    assert [s.numero for s in spans] == ["13", "14"]
    assert "quince (15) dias" in spans[1].texto.replace("í", "i")


def test_quita_scripts_estilos_y_tags():
    texto = ingest.extract_html_text(HTML_NORMA)

    assert "var x = 1" not in texto
    assert "color:red" not in texto
    assert "<p>" not in texto


def test_resuelve_las_entidades_html():
    texto = ingest.extract_html_text(HTML_NORMA)

    assert "petición" in texto
    assert "&oacute;" not in texto
    assert "días" in texto


def test_el_no_break_space_queda_como_espacio_normal():
    """El &nbsp; de los portales, si se deja tal cual, se cuela en los chunks y
    despues en las citas como un caracter invisible."""
    texto = ingest.extract_html_text(HTML_NORMA)

    assert " " not in texto
    assert "resolver. Toda" in texto


def test_no_deja_lineas_vacias_de_mas():
    texto = ingest.extract_html_text("<p>uno</p><br><br><br><p>dos</p>")

    assert "\n\n\n" not in texto
    assert texto.split("\n") == ["uno", "dos"]


def test_no_ingiere_un_documento_sin_url_verificada(tmp_path):
    """Una fuente cuya URL nadie comprobo no es una fuente verificada. Preferimos
    fallar en la indexacion que indexar un chunk que produce respuestas que
    *parecen* trazables (PRODUCT.md, principio 1)."""
    archivo = tmp_path / "ley_1755_2015.html"
    archivo.write_text(HTML_NORMA, encoding="utf-8")

    with pytest.raises(ValueError, match="url_fuente"):
        ingest.ingest_document(archivo, fuente="Ley 1755 de 2015", tipo="ley", url_fuente="  ")


def test_ingest_document_adjunta_la_metadata_de_procedencia(tmp_path):
    archivo = tmp_path / "ley_1755_2015.html"
    archivo.write_text(HTML_NORMA, encoding="utf-8")

    doc = ingest.ingest_document(
        archivo,
        fuente="Ley 1755 de 2015 (Derecho de peticion)",
        tipo="ley",
        url_fuente="https://www.funcionpublica.gov.co/eva/gestornormativo/ejemplo",
    )

    assert doc.doc_id == "ley_1755_2015"
    assert doc.tipo == "ley"
    assert doc.vigente is True
    # La fecha de consulta es la fecha de corte del corpus: una derogatoria
    # posterior no se refleja en el indice, asi que hay que saber cuando se bajo.
    assert len(doc.fecha_consulta) == 10 and doc.fecha_consulta.count("-") == 2


def test_ingest_corpus_dice_que_archivos_faltan(tmp_path):
    manifest = [
        {
            "filename": "ley_820_2003.html",
            "fuente": "Ley 820 de 2003",
            "tipo": "ley",
            "url_fuente": "https://ejemplo.gov.co/820",
        }
    ]

    with pytest.raises(FileNotFoundError, match="ley_820_2003.html"):
        ingest.ingest_corpus(manifest, raw_dir=tmp_path)


def test_save_y_load_processed_hacen_ida_y_vuelta(tmp_path):
    archivo = tmp_path / "ley_1755_2015.html"
    archivo.write_text(HTML_NORMA, encoding="utf-8")
    doc = ingest.ingest_document(
        archivo,
        fuente="Ley 1755 de 2015",
        tipo="ley",
        url_fuente="https://ejemplo.gov.co/1755",
    )
    destino = tmp_path / "procesado.jsonl"

    ingest.save_processed([doc], path=destino)
    recargados = ingest.load_processed(path=destino)

    assert len(recargados) == 1
    assert recargados[0]["fuente"] == "Ley 1755 de 2015"
    assert recargados[0]["url_fuente"] == "https://ejemplo.gov.co/1755"


# --- Markdown con frontmatter (el formato real del corpus de M3) -------------

MD_NORMA = '''---
title: "por la cual se expide el regimen de arrendamiento de vivienda urbana"
identifier: "LEY-820-2003"
rank: "ley"
status: "in_force"
source: "https://www.suin-juriscol.gov.co/viewDocument.asp?id=1669010"
modification_summary: "Derogado [Articulo 626 LEY 1564 de 2012](https://ejemplo)"
---
# por la cual se expide el regimen de arrendamiento de vivienda urbana

### **CAPITULO I**

##### **Artículo 1º.** *Objeto*. La presente ley tiene como objeto fijar los criterios.

##### **Artículo 2** º.***Definición***. El contrato de arrendamiento de vivienda urbana es aquel.
'''


def test_el_frontmatter_se_separa_del_cuerpo():
    campos, cuerpo = ingest.split_frontmatter(MD_NORMA)

    assert campos["identifier"] == "LEY-820-2003"
    assert campos["status"] == "in_force"
    assert campos["source"].startswith("https://www.suin-juriscol.gov.co/")
    assert not cuerpo.startswith("---")


def test_un_documento_sin_frontmatter_no_pierde_su_texto():
    campos, cuerpo = ingest.split_frontmatter("Texto suelto sin cabecera.")

    assert campos == {}
    assert cuerpo == "Texto suelto sin cabecera."


def test_la_extraccion_de_markdown_quita_encabezados_y_enfasis():
    """Sin esto el articulado llega al chunker como '##### **Artículo 1º.**' y el
    patron anclado a inicio de linea no reconoce ni un solo articulo: la norma
    entera se indexa sin numero de articulo. Paso de verdad con 9 de las 10
    normas del corpus."""
    texto = ingest.extract_markdown_text(MD_NORMA)

    assert "#" not in texto
    assert "*" not in texto
    assert texto.count("Artículo") == 2


def test_el_texto_extraido_del_markdown_es_chunkeable_por_articulo():
    texto = ingest.extract_markdown_text(MD_NORMA)
    spans = chunk.split_by_article(texto)

    assert [s.numero for s in spans] == ["1", "2"]
    assert all(s.capitulo.upper().startswith("CAPITULO I") for s in spans)


def test_el_frontmatter_no_llega_al_texto_indexado():
    """modification_summary trae decenas de referencias a otras normas; indexarlo
    haria que el retrieval devuelva ese bloque como si fuera articulado."""
    texto = ingest.extract_markdown_text(MD_NORMA)

    assert "modification_summary" not in texto
    assert "LEY-820-2003" not in texto


def test_read_frontmatter_lee_solo_la_cabecera(tmp_path):
    archivo = tmp_path / "ley_820_2003.md"
    archivo.write_text(MD_NORMA, encoding="utf-8")

    campos = ingest.read_frontmatter(archivo)

    assert campos["rank"] == "ley"
    assert "title" in campos


def test_extract_text_despacha_markdown_por_extension(tmp_path):
    archivo = tmp_path / "ley_820_2003.md"
    archivo.write_text(MD_NORMA, encoding="utf-8")

    texto = ingest.extract_text(archivo)

    assert texto.startswith("por la cual se expide")
    assert "**" not in texto
