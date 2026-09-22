from tools.rag import prompt_template
from tools.rag.embed_store import SearchResult


def resultado(**overrides) -> SearchResult:
    base = dict(
        chunk_id="ley_1755_2015::chunk3",
        text="ARTÍCULO 14. Toda peticion debera resolverse dentro de los quince (15) dias.",
        fuente="Ley 1755 de 2015 (Derecho de peticion)",
        url_fuente="https://www.funcionpublica.gov.co/eva/gestornormativo/ejemplo",
        articulos_incluidos=["14"],
        score=0.87,
    )
    base.update(overrides)
    return SearchResult(**base)


def test_el_prompt_tiene_las_cuatro_partes_en_orden():
    prompt = prompt_template.build_augmented_prompt("¿Cuanto tardan en responder?", [resultado()])

    pos_instruccion = prompt.index("Eres un asistente juridico")
    pos_contexto = prompt.index("CONTEXTO:")
    pos_valvula = prompt.index(prompt_template.RESPUESTA_SIN_CONTEXTO)
    pos_pregunta = prompt.index("PREGUNTA DEL USUARIO:")

    assert pos_instruccion < pos_contexto < pos_valvula < pos_pregunta


def test_la_instruccion_arranca_del_system_prompt_real_de_m1():
    """Si el prompt del RAG cambiara el rol con el que el modelo fue
    fine-tuneado, el delta contra el scorecard de M2 dejaria de ser atribuible
    al RAG."""
    assert prompt_template.SYSTEM_PROMPT_M1 in prompt_template.INSTRUCCION
    assert "No inventes normas" in prompt_template.INSTRUCCION


def test_la_valvula_de_escape_esta_presente_incluso_cuando_si_hay_contexto():
    """La valvula no es un caso especial del prompt vacio: el contexto puede
    traer 5 chunks y ninguno responder la pregunta. Ese es justo el caso donde
    el M2 midio que el modelo cede y cita de memoria."""
    prompt = prompt_template.build_augmented_prompt("pregunta", [resultado()])

    assert prompt_template.RESPUESTA_SIN_CONTEXTO in prompt


def test_sin_resultados_el_contexto_lo_dice_explicitamente():
    prompt = prompt_template.build_augmented_prompt("¿Que dice la ley de patentes mineras?", [])

    assert prompt_template.SIN_CONTEXTO_RELEVANTE in prompt
    assert prompt_template.RESPUESTA_SIN_CONTEXTO in prompt


def test_la_cita_va_antes_del_texto_del_chunk():
    """No es cosmetico: si el texto llega anonimo, el modelo no tiene de donde
    derivar una cita verificable y la completa de memoria."""
    contexto = prompt_template.format_context([resultado()])

    assert contexto.index("Ley 1755 de 2015") < contexto.index("quince (15) dias")


def test_la_cita_incluye_ley_y_articulo():
    contexto = prompt_template.format_context([resultado()])

    assert "Ley 1755 de 2015 (Derecho de peticion), Articulo 14" in contexto


def test_la_cita_usa_plural_cuando_el_chunk_agrupa_varios_articulos():
    r = resultado(articulos_incluidos=["1", "2", "3"])

    assert r.cita.endswith("Articulos 1, 2, 3")


def test_la_cita_cae_a_solo_la_fuente_si_el_chunk_no_tiene_articulo():
    """Pasa con fragmentos de sentencia o preambulos: se cita la norma, no un
    numero de articulo inexistente."""
    r = resultado(articulos_incluidos=[])

    assert r.cita == "Ley 1755 de 2015 (Derecho de peticion)"
    assert "Articulo" not in prompt_template.format_context([r])


def test_el_capitulo_aparece_en_el_encabezado_si_esta_disponible():
    contexto = prompt_template.format_context(
        [resultado(capitulo="CAPITULO I Derecho de peticion ante autoridades")]
    )

    assert "(CAPITULO I Derecho de peticion ante autoridades)" in contexto


def test_varios_chunks_quedan_numerados_y_separados():
    contexto = prompt_template.format_context(
        [resultado(), resultado(chunk_id="otro", articulos_incluidos=["15"])]
    )

    assert "[1] Fuente:" in contexto
    assert "[2] Fuente:" in contexto
    assert "---" in contexto


def test_build_messages_separa_reglas_en_system_y_caso_en_user():
    messages = prompt_template.build_messages("¿Cuanto tardan?", [resultado()])

    assert [m["role"] for m in messages] == ["system", "user"]
    assert prompt_template.RESPUESTA_SIN_CONTEXTO in messages[0]["content"]
    assert "Ley 1755 de 2015" in messages[1]["content"]
    assert "¿Cuanto tardan?" in messages[1]["content"]


def test_la_pregunta_del_usuario_va_tal_cual_sin_reformular():
    query = "me despidieron sin pagarme la liquidacion, que hago???"
    prompt = prompt_template.build_augmented_prompt(query, [])

    assert query in prompt
