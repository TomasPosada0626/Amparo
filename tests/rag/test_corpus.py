import json

import pytest

from tools.rag import config, corpus


def test_las_categorias_objetivo_existen_tal_cual_en_el_dataset_de_m1():
    """El corpus se prioriza por las categorias reales del dataset, no por una
    lista escrita de memoria: un nombre mal escrito aca romperia el mapeo
    norma -> categoria sin que nada fallara."""
    with open(config.PROJECT_ROOT / "data" / "dataset_legal.jsonl", encoding="utf-8") as f:
        categorias_reales = {json.loads(linea)["category"] for linea in f if linea.strip()}

    for categoria in corpus.CATEGORIAS_OBJETIVO:
        assert categoria in categorias_reales, categoria


def test_las_categorias_objetivo_son_las_nueve_mas_frecuentes_del_dataset():
    """Es el criterio de alcance declarado en docs/m3_decisiones_rag.md: las 9
    categorias cotidianas de mayor frecuencia, el mismo criterio con el que se
    priorizo el dataset de fine-tuning en M1."""
    conteo: dict[str, int] = {}
    with open(config.PROJECT_ROOT / "data" / "dataset_legal.jsonl", encoding="utf-8") as f:
        for linea in f:
            if linea.strip():
                categoria = json.loads(linea)["category"]
                conteo[categoria] = conteo.get(categoria, 0) + 1

    nueve_mas_frecuentes = {c for c, _ in sorted(conteo.items(), key=lambda kv: -kv[1])[:9]}

    assert set(corpus.CATEGORIAS_OBJETIVO) == nueve_mas_frecuentes


def test_cada_categoria_objetivo_esta_cubierta_por_al_menos_una_norma():
    """Si una categoria queda sin norma, el RAG no puede responder nada de ese
    tema con fuente -- y la valvula de escape se activaria siempre para ahi."""
    sin_cubrir = set(corpus.CATEGORIAS_OBJETIVO) - corpus.categorias_cubiertas()

    assert not sin_cubrir, f"categorias sin norma en el corpus: {sin_cubrir}"


def test_toda_norma_descargada_esta_o_en_alcance_o_excluida_con_razon():
    """El alcance de M3 son 10 de las 17 normas descargadas. Excluir en silencio
    es indistinguible de un olvido: quien retome el trabajo necesita ver que la
    norma ya esta disponible y por que no se indexo."""
    en_alcance = {n.filename for n in corpus.NORMAS_EN_ALCANCE}
    descargadas = set(corpus.archivos_del_corpus())

    sin_clasificar = descargadas - en_alcance - set(corpus.FUERA_DE_ALCANCE)
    assert not sin_clasificar, f"normas sin declarar en alcance ni exclusion: {sin_clasificar}"

    fantasma = (en_alcance | set(corpus.FUERA_DE_ALCANCE)) - descargadas
    assert not fantasma, f"normas declaradas que no existen en el corpus: {fantasma}"


def test_la_exclusion_de_la_ley_1581_explica_que_es_por_calidad_no_por_alcance():
    """No es una norma fuera de tema: se excluye porque el archivo del espejo
    intercala articulado de otros instrumentos, que se citaria como si fuera de
    la Ley 1581. La razon tiene que quedar visible para que se pueda revisar."""
    razon = corpus.FUERA_DE_ALCANCE["habeas_data_datos_personales_ley_1581_2012.md"]

    assert "CALIDAD" in razon
    assert "1266" in razon, "debe decir que norma cubre la categoria en su lugar"


def test_ninguna_norma_esta_declarada_dos_veces():
    nombres = [n.filename for n in corpus.NORMAS_EN_ALCANCE]

    assert len(nombres) == len(set(nombres))


def test_cada_norma_en_alcance_declara_al_menos_una_categoria():
    for norma in corpus.NORMAS_EN_ALCANCE:
        assert norma.categorias, norma.filename


# --- derivacion de la cita desde el identifier -------------------------------

@pytest.mark.parametrize(
    "identifier, esperado",
    [
        ("LEY-820-2003", "Ley 820 de 2003"),
        ("LEY-1564-2012", "Ley 1564 de 2012"),
        ("DECRETO-2663-1950", "Decreto 2663 de 1950"),
        ("CONSTITUCION-POLITICA-1991", "Constitucion Politica de 1991"),
    ],
)
def test_la_cita_se_deriva_del_identifier_del_frontmatter(identifier, esperado):
    """El numero y el ano de la norma salen del archivo, no de una cadena escrita
    a mano: asi no pueden divergir de la fuente."""
    assert corpus.fuente_desde_identifier(identifier) == esperado


def test_el_nombre_comun_se_agrega_entre_parentesis():
    assert (
        corpus.fuente_desde_identifier("DECRETO-2663-1950", "Codigo Sustantivo del Trabajo")
        == "Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo)"
    )


def test_un_identifier_inesperado_no_revienta_y_se_usa_tal_cual():
    assert corpus.fuente_desde_identifier("ALGO-RARO") == "ALGO-RARO"


# --- validacion del manifiesto -----------------------------------------------

def test_validate_manifest_rechaza_una_norma_que_no_existe():
    inexistente = corpus.NormaEnAlcance(filename="ley_inventada.md", categorias=("Arriendo",))

    with pytest.raises(corpus.ManifestError, match="no esta en"):
        corpus.validate_manifest([inexistente])


def test_validate_manifest_rechaza_un_alcance_que_deja_categorias_sin_cubrir():
    solo_arriendo = [
        n for n in corpus.NORMAS_EN_ALCANCE if "Arriendo" in n.categorias
    ]

    with pytest.raises(corpus.ManifestError, match="categorias objetivo sin ninguna norma"):
        corpus.validate_manifest(solo_arriendo)


def test_el_manifiesto_real_es_valido():
    """Sobre el corpus versionado en el repo, no sobre datos de prueba."""
    corpus.validate_manifest()


def test_to_ingest_manifest_produce_metadata_citable_para_cada_norma():
    entradas = corpus.to_ingest_manifest()

    assert len(entradas) == len(corpus.NORMAS_EN_ALCANCE)
    for entrada in entradas:
        assert set(entrada) == {"filename", "fuente", "tipo", "url_fuente", "vigente"}
        assert entrada["fuente"].strip()
        assert entrada["url_fuente"].strip()
        assert entrada["tipo"] in corpus.TIPOS_VALIDOS


def test_todas_las_normas_indexadas_estan_vigentes():
    """`status: in_force` en el frontmatter. Si alguna dejara de estarlo, hay que
    decidir explicitamente si se indexa marcada como no vigente o se saca."""
    assert all(e["vigente"] for e in corpus.to_ingest_manifest())


def test_las_urls_apuntan_a_suin_juriscol_salvo_la_constitucion():
    """El resto del corpus viene del espejo de SUIN-Juriscol; la Constitucion
    viene de un PDF aportado por el usuario y su procedencia es una descripcion,
    no una URL (ver data/corpus/normas/README.md y la decision 1)."""
    for entrada in corpus.to_ingest_manifest():
        if entrada["filename"] == "constitucion_politica_1991.md":
            assert "Georgetown" in entrada["url_fuente"]
        else:
            assert "suin-juriscol.gov.co" in entrada["url_fuente"], entrada["filename"]
