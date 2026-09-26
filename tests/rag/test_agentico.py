"""Tests del RAG agentico (S10, Lab B): el mini-agente ReAct.

Corren sin GPU: la generacion se inyecta como _generar fake (una secuencia de
salidas del modelo) y el retrieval se reemplaza por uno fijo. Se prueba el
parser de pasos, la calculadora segura y el bucle pensamiento -> accion ->
observacion -- no el modelo.
"""
from tools.evaluation import eval_set
from tools.rag import agentico, pipeline, tools
from tools.rag.embed_store import SearchResult
from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO


def make_result(chunk_id, *, fuente="Decreto 2663 de 1950 (CST)", articulos=None):
    return SearchResult(
        chunk_id=chunk_id,
        text=f"texto normativo de {chunk_id}",
        fuente=fuente,
        url_fuente=f"https://suin/{chunk_id}",
        score=0.9,
        articulos_incluidos=articulos or ["64"],
        dense_score=0.9,
    )


def stub_retrieve(monkeypatch, resultados):
    """El agente busca a traves de tools.ejecutar_tool_con_resultados, que llama
    tools.retrieve: se reemplaza ahi para aislar el bucle del retrieval."""
    llamadas = []

    def _retrieve(consulta, store, **kwargs):
        llamadas.append(consulta)
        return resultados

    monkeypatch.setattr(tools, "retrieve", _retrieve)
    return llamadas


def generador(*salidas):
    it = iter(salidas)
    return lambda system, user: next(it)


# --- Parser de pasos ---------------------------------------------------------

def test_parsea_pensamiento_y_accion():
    pens, accion = agentico.parsear_paso(
        "Pensamiento: necesito la regla del despido\nAccion: buscar_normas[indemnizacion despido sin justa causa]"
    )
    assert pens == "necesito la regla del despido"
    assert accion == ("buscar_normas", "indemnizacion despido sin justa causa")


def test_responder_admite_varias_lineas_y_corchetes_internos():
    """La respuesta final puede citar "[1]" y tener saltos de linea: se toma hasta
    el ULTIMO corchete, no hasta el primero."""
    _, accion = agentico.parsear_paso(
        "Pensamiento: ya puedo responder\nAccion: Responder[Segun la norma [1], te deben:\n- 30 dias]"
    )
    assert accion == ("Responder", "Segun la norma [1], te deben:\n- 30 dias")


def test_solo_cuenta_la_primera_accion():
    """Un modelo pequeño a veces se inventa pasos y observaciones despues de su
    accion. Solo la primera se ejecuto de verdad."""
    _, accion = agentico.parsear_paso(
        "Pensamiento: busco\nAccion: calculadora[2+2]\nObservacion: 4\nAccion: Responder[son 4]"
    )
    assert accion == ("calculadora", "2+2")


def test_salida_sin_accion_devuelve_none():
    assert agentico.parsear_paso("Te recomiendo acudir a un abogado.")[1] is None


# --- Calculadora ------------------------------------------------------------

def test_calculadora_hace_la_cuenta_exacta():
    # Indemnizacion de ejemplo: 30 dias por el primer año + 20 por cada uno de
    # los 2 siguientes, sobre un salario diario de 2.000.000 / 30.
    assert agentico.calculadora("2000000 / 30 * (30 + 20 * 2)") == "4666666.6667"


def test_calculadora_entiende_miles_con_punto_y_x():
    assert agentico.calculadora("2.000.000 x 3") == "6000000"


def test_calculadora_no_ejecuta_codigo():
    """La expresion la escribe el modelo: nada que no sea aritmetica se evalua."""
    obs = agentico.calculadora('__import__("os").system("echo hola")')
    assert obs.startswith("error:")


def test_calculadora_devuelve_error_como_observacion():
    assert agentico.calculadora("1/0").startswith("error:")
    assert agentico.calculadora("").startswith("error:")


# --- Bucle ReAct -------------------------------------------------------------

def test_pregunta_compuesta_encadena_busqueda_calculo_y_respuesta(monkeypatch):
    """El caso para el que existe el agente: norma + cuenta + respuesta."""
    busquedas = stub_retrieve(monkeypatch, [make_result("cst::64")])
    generar = generador(
        "Pensamiento: necesito la regla\nAccion: buscar_normas[indemnizacion despido sin justa causa]",
        "Pensamiento: calculo con su salario\nAccion: calculadora[2000000 / 30 * 70]",
        "Pensamiento: ya tengo todo\nAccion: Responder[Segun el CST, Articulo 64, te deben 4666666.67 pesos.]",
    )

    r = agentico.agente_react("me despidieron tras 3 años ganando 2 millones", object(), _generar=generar)

    assert r["response"] == "Segun el CST, Articulo 64, te deben 4666666.67 pesos."
    assert busquedas == ["indemnizacion despido sin justa causa"]
    assert [p["accion"] for p in r["traza"]] == ["buscar_normas", "calculadora", "Responder"]
    assert r["traza"][1]["observacion"] == "4666666.6667"


def test_la_salida_trae_los_contexts_que_vio_el_agente(monkeypatch):
    """Sin contexts no hay RAGAS: deben ser los chunks de sus busquedas, sin
    duplicados aunque busque dos veces lo mismo."""
    stub_retrieve(monkeypatch, [make_result("cst::64")])
    generar = generador(
        "Accion: buscar_normas[despido]",
        "Accion: buscar_normas[despido sin justa causa]",
        "Accion: Responder[listo]",
    )

    r = agentico.agente_react("consulta", object(), _generar=generar)

    assert r["contexts"] == ["texto normativo de cst::64"]
    assert r["n_retrieved"] == 1
    assert r["sistema"] == "react"


def test_la_salida_se_convierte_al_registro_de_evaluacion(monkeypatch):
    """Mismo contrato que answer_query: to_eval_record la acepta sin casos
    especiales, con la ruta y la traza para auditar."""
    stub_retrieve(monkeypatch, [make_result("cst::64")])
    generar = generador("Accion: buscar_normas[despido]", "Accion: Responder[respuesta]")
    registro = eval_set.load_eval_set()[0]

    r = agentico.agente_react(registro["messages"][1]["content"], object(), _generar=generar)
    record = pipeline.to_eval_record(r, registro)

    for campo in ("question", "answer", "contexts", "ground_truth", "sistema", "traza"):
        assert campo in record, campo
    assert record["sistema"] == "react"
    assert len(record["traza"]) == 2


def test_sin_accion_valida_toma_la_salida_como_respuesta_directa(monkeypatch):
    stub_retrieve(monkeypatch, [])
    generar = generador("Hola, cuentame tu caso y te oriento.")

    r = agentico.agente_react("hola", object(), _generar=generar)

    assert r["response"] == "Hola, cuentame tu caso y te oriento."
    assert r["contexts"] == []
    assert r["traza"][0]["accion"] == "respuesta_directa"


def test_el_bucle_no_corre_para_siempre(monkeypatch):
    """Si el modelo nunca responde, max_pasos acota el bucle y se fuerza el final."""
    stub_retrieve(monkeypatch, [make_result("c1")])
    llamadas = {"n": 0}

    def generar(system, user):
        llamadas["n"] += 1
        return "Accion: buscar_normas[x]"

    r = agentico.agente_react("consulta", object(), max_pasos=3, _generar=generar)

    # 3 pasos + 1 generacion forzada final.
    assert llamadas["n"] == 4
    assert r["traza"][-1]["accion"] == "Responder (forzado)"


def test_si_no_logra_responder_usa_la_valvula_de_escape(monkeypatch):
    """Pasos agotados y sin Responder en el ultimo intento: admitir que no se
    pudo, con la misma frase que detecta el harness, en vez de improvisar."""
    stub_retrieve(monkeypatch, [])
    generar = lambda system, user: "Accion: buscar_normas[x]"

    r = agentico.agente_react("consulta", object(), max_pasos=2, _generar=generar)

    assert RESPUESTA_SIN_CONTEXTO in r["response"]


def test_el_prompt_incluye_la_valvula_de_escape():
    assert RESPUESTA_SIN_CONTEXTO in agentico.SYSTEM_REACT
