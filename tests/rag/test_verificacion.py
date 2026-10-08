"""Tests de la verificacion de citas (tools/rag/verificacion.py).

Son los tests de tools/rag/agentico.py que cubrian las funciones compartidas
con el RAG de una pasada, DSPy y la evaluacion. El agente y el tool use se
retiraron el 2026-10-08 (C11); estas funciones se quedan.
"""
from tools.rag import verificacion as v
from tools.rag.embed_store import SearchResult
from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO


def make_result(chunk_id, *, articulos=None):
    return SearchResult(chunk_id=chunk_id, text=f"texto de {chunk_id}", fuente="Ley 820 de 2003",
                        url_fuente="u", score=0.9, articulos_incluidos=articulos or ["20"], dense_score=0.9)


def test_extrae_los_articulos_citados():
    texto = "Segun el artículo 20 de la Ley 820 de 2003, los arts. 5, 6 y 7 y el art. 6º"
    assert v.articulos_citados(texto) == {"20", "5", "6", "7"}


def test_una_cita_recuperada_esta_respaldada():
    assert v.citas_no_respaldadas("Segun el articulo 20 ...", [make_result("ley820::20")]) == []


def test_una_cita_no_recuperada_se_detecta():
    assert v.citas_no_respaldadas("Segun los articulos 20 y 518 ...", [make_result("ley820::20")]) == ["518"]


def test_citar_el_articulo_que_menciono_el_usuario_no_es_inventar():
    """La respuesta puede aclarar que el articulo que dijo el usuario no aplica."""
    assert v.citas_no_respaldadas(
        "El articulo 64 que mencionas no trata ese tema.", [], query="que dice el articulo 64"
    ) == []


def test_citas_no_respaldadas_acepta_el_conjunto_de_vistos():
    assert v.citas_no_respaldadas("articulos 20 y 21", vistos={"20"}) == ["21"]


def test_citas_no_verificables_suma_articulos_y_sentencias():
    r = v.citas_no_verificables("Segun el articulo 518 y la T-760 de 2008", [make_result("ley820::20")])
    assert r == ["518", "T-760"]


def test_detecta_sentencias_citadas():
    assert v.sentencias_citadas("segun la T-760 de 2008 y la SU-111/97") == {"T-760", "SU-111"}
    assert v.sentencias_citadas("segun el articulo 20") == set()


def test_detecta_promesas_de_resultado():
    assert v.promete_resultado("Te garantizo que vas a ganar la tutela")
    assert not v.promete_resultado("El resultado depende de las pruebas y del juez")


def test_es_prudente():
    assert v.es_prudente(f"{RESPUESTA_SIN_CONTEXTO}.", set())
    assert v.es_prudente("Lo primero es tu seguridad: llama a la Linea 123.", set())
    assert v.es_prudente("Segun el Articulo 20, ...", {"20"})
    assert not v.es_prudente("Segun el Articulo 518, ...", {"20"})
    assert not v.es_prudente("La sentencia T-760 de 2008 te protege.", set())
    assert not v.es_prudente("Te garantizo que la ganas.", set())


def test_la_frase_de_escape_no_exime_de_las_comprobaciones():
    """S10-5: "No tengo informacion verificada... pero segun el articulo 99 y la
    sentencia T-760" pasaba por prudente solo por contener la frase."""
    con_cita = f"{RESPUESTA_SIN_CONTEXTO}, pero segun el articulo 99 y la sentencia T-760 de 2008 tienes derecho."
    assert not v.es_prudente(con_cita, vistos=set(), query="tengo derecho?")
    assert v.es_prudente(RESPUESTA_SIN_CONTEXTO, vistos=set(), query="tengo derecho?")


def test_numero_en_letras():
    assert v.numero_en_letras(15) == "quince"
    assert v.numero_en_letras(45) == "cuarenta y cinco"
    assert v.numero_en_letras(100) == "cien"
    assert v.numero_en_letras(1000) == "1000"


def test_puntaje_norma_reconoce_siglas_y_numeros():
    assert v.puntaje_norma("CST", "Codigo Sustantivo del Trabajo") > 0
    assert v.puntaje_norma("ley 820", "Ley 820 de 2003") > v.puntaje_norma("ley 820", "Ley 100 de 1993")
    assert v.puntaje_norma("CGP", "Codigo Sustantivo del Trabajo") == 0
