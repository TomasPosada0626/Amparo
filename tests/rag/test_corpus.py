import json

import pytest

from tools.rag import config, corpus, ingest


def test_las_categorias_objetivo_existen_tal_cual_en_el_dataset_de_m1():
    """El corpus se prioriza por las categorias reales del dataset, no por una
    lista escrita de memoria: un nombre mal escrito aca romperia el mapeo
    norma -> categoria sin que nada fallara."""
    with open(config.PROJECT_ROOT / "data" / "dataset_legal.jsonl", encoding="utf-8") as f:
        categorias_reales = {json.loads(linea)["category"] for linea in f if linea.strip()}

    for categoria in corpus.CATEGORIAS_OBJETIVO:
        assert categoria in categorias_reales, categoria


# Categorias del dataset que no son un tema juridico sino un tipo de pregunta
# (ejemplos de abstencion, ids 1411-1536): no tienen norma que las cubra.
CATEGORIAS_DE_ABSTENCION = {
    "Fuera del derecho colombiano",
    "Peticiones de cita o plazo exacto",
    "Peticiones de garantia de resultado",
    "Peticiones de conducta ilegitima",
    "Preguntas ambiguas",
    "Urgencia con ayuda inmediata",
}


def _categorias_del_dataset() -> set[str]:
    with open(config.PROJECT_ROOT / "data" / "dataset_legal.jsonl", encoding="utf-8") as f:
        return {json.loads(linea)["category"] for linea in f if linea.strip()}


def test_toda_categoria_tematica_del_dataset_tiene_norma_o_dice_cual_le_falta():
    """Desde el 2026-10-08 el alcance es todo el dataset, no las 9 categorias mas
    frecuentes: el dataset de M1 v2 necesita contexto real para cada tema, y el
    eval set pregunta por 27. Una categoria sin norma tiene que decir cual le
    falta, para que no se confunda con un olvido."""
    tematicas = _categorias_del_dataset() - CATEGORIAS_DE_ABSTENCION

    sin_decidir = tematicas - set(corpus.CATEGORIAS_OBJETIVO) - set(corpus.CATEGORIAS_SIN_NORMA)
    assert not sin_decidir, f"categorias sin norma y sin explicacion: {sorted(sin_decidir)}"
    assert not set(corpus.CATEGORIAS_OBJETIVO) & set(corpus.CATEGORIAS_SIN_NORMA)


def test_las_categorias_del_eval_set_estan_cubiertas():
    """El eval set de M2 tiene cuatro categorias que no estan en el dataset; cada
    una se mapea a la categoria o al bloque transversal que la cubre."""
    from tools.evaluation import eval_set

    cubiertas = corpus.categorias_cubiertas() | {corpus.TRANSVERSAL}
    sin_norma = set(corpus.CATEGORIAS_SIN_NORMA)
    for r in eval_set.gold_examples(eval_set.load_eval_set()):
        categoria = corpus.EQUIVALENCIAS_EVAL_SET.get(r["category"], r["category"])
        assert categoria in cubiertas or categoria in sin_norma, (r["id"], r["category"])


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


def test_la_ley_1581_entra_solo_con_su_articulado_propio():
    """El archivo del espejo transcribe, despues de los 30 articulos de la ley, el
    proyecto que reviso la Corte con otra numeracion. Antes se excluia la norma
    entera por eso; ahora entra recortada a sus 30 articulos."""
    norma = next(n for n in corpus.NORMAS_EN_ALCANCE
                 if n.filename == "habeas_data_datos_personales_ley_1581_2012.md")
    assert norma.articulos_propios == 30


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
        assert set(entrada) == {"filename", "fuente", "tipo", "url_fuente", "vigente",
                                "articulos_propios", "fragmentos_ajenos"}
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


# --- limpieza de texto ajeno ----------------------------------------------------

def test_recortar_al_articulado_propio_quita_lo_que_sigue_a_la_ley():
    texto = ("Artículo 1. Objeto.\nArtículo 2. Ambito.\nPROYECTO DE LEY\n"
             "Artículo 1. Otro objeto.\nArtículo 2. Otro ambito.")
    recortado = ingest.recortar_al_articulado_propio(texto, 2)
    assert "Otro objeto" not in recortado and "Ambito" in recortado


def test_recortar_falla_si_la_ley_tiene_menos_articulos_de_los_declarados():
    with pytest.raises(ValueError):
        ingest.recortar_al_articulado_propio("Artículo 1. Objeto.", 5)


def test_quitar_fragmentos_ajenos_y_fallar_si_el_marcador_no_esta():
    texto = "Artículo 751. Prescripcion.\nArtículo 1°. Cheques fiscales.\nSección IV. Bonos\nArtículo 752."
    limpio = ingest.quitar_fragmentos_ajenos(texto, [("Artículo 1°. Cheques", "Sección IV")])
    assert "Cheques fiscales" not in limpio and "Artículo 752" in limpio
    with pytest.raises(ValueError):
        ingest.quitar_fragmentos_ajenos(texto, [("no existe", "Sección IV")])


def test_ninguna_norma_del_corpus_repite_su_primer_articulo():
    """El sintoma de texto ajeno intercalado es un segundo "Articulo 1" dentro
    de la misma norma (Ley 1712, Ley 1581, cheques fiscales en el Codigo de
    Comercio, un decreto de estado de sitio en el Codigo Civil)."""
    from tools.rag import chunk

    repetidas = []
    for doc in ingest.ingest_corpus(corpus.to_ingest_manifest()):
        numeros = [s.numero for s in chunk.split_by_article(doc.text)]
        if numeros.count("1") > 1:
            repetidas.append(doc.doc_id)
    assert repetidas == []
