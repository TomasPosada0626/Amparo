"""Tests del tool use (S10): retrieval-as-tool con function calling.

Corren sin GPU: la generacion se inyecta como _generar fake (funcion
(system, user) -> str) y el retrieval usa un FakeStore con ranking fijo. Se
prueba el parser de tool-calls, el dispatcher con su validacion, y el bucle
propone->ejecuta->observa->responde -- no el modelo.
"""
from tools.rag import tools
from tools.rag.embed_store import SearchResult


def make_result(chunk_id, *, fuente="Ley 1480 de 2011", articulos=None):
    return SearchResult(
        chunk_id=chunk_id,
        text=f"texto normativo de {chunk_id}",
        fuente=fuente,
        url_fuente=f"https://suin/{chunk_id}",
        score=0.9,
        articulos_incluidos=articulos or ["8"],
        dense_score=0.9,
    )


class FakeStore:
    def __init__(self, ranking):
        self._ranking = ranking
        self.metadata = []

    def search(self, query_embedding, top_k):
        return self._ranking[:top_k]


def stub_retrieve(resultados):
    """Reemplaza tools.retrieve por uno que ignora el store y devuelve fijo, para
    aislar el dispatcher del pipeline de retrieval (ya testeado aparte)."""
    def _retrieve(consulta, store, **kwargs):
        return resultados
    return _retrieve


# --- Parser de tool-calls ----------------------------------------------------

def test_extrae_un_tool_call_bien_formado():
    texto = 'Claro, busco eso. {"tool": "buscar_normas", "args": {"consulta": "despido"}}'
    pedido = tools.extraer_tool_call(texto)

    assert pedido["tool"] == "buscar_normas"
    assert pedido["args"]["consulta"] == "despido"


def test_json_malformado_no_es_error_sino_respuesta_directa():
    """Un modelo pequeño a veces emite JSON roto. Eso NO debe tumbar el bucle:
    devuelve None y el bucle lo interpreta como 'el modelo respondio directo'."""
    assert tools.extraer_tool_call('{"tool": "buscar_normas", "args": {') is None


def test_texto_sin_json_es_respuesta_directa():
    assert tools.extraer_tool_call("La EPS debe responderte en 15 dias habiles.") is None


def test_json_sin_campo_tool_no_es_tool_call():
    """Un JSON cualquiera que no tenga 'tool' no es una llamada a herramienta."""
    assert tools.extraer_tool_call('{"otra_cosa": 1}') is None


# --- Dispatcher con validacion ----------------------------------------------

def test_el_dispatcher_ejecuta_la_busqueda_y_formatea_con_cita(monkeypatch):
    """La observacion debe traer la cita de cada chunk: es lo que permite que el
    modelo cite algo que aparecio de verdad, no de memoria."""
    monkeypatch.setattr(tools, "retrieve", stub_retrieve([make_result("c1", fuente="CST", articulos=["64"])]))
    store = FakeStore([])

    obs = tools.ejecutar_tool({"tool": "buscar_normas", "args": {"consulta": "despido"}}, store)

    assert "CST" in obs
    assert "Articulo 64" in obs
    assert "texto normativo de c1" in obs


def test_el_dispatcher_rechaza_una_herramienta_inexistente(monkeypatch):
    """Un error de validacion se devuelve como observacion (string), no se lanza:
    el modelo lo lee y puede corregir en la siguiente vuelta."""
    monkeypatch.setattr(tools, "retrieve", stub_retrieve([]))
    store = FakeStore([])

    obs = tools.ejecutar_tool({"tool": "calculadora", "args": {"x": 1}}, store)

    assert obs.startswith("error:")
    assert "buscar_normas" in obs


def test_el_dispatcher_rechaza_args_invalidos(monkeypatch):
    monkeypatch.setattr(tools, "retrieve", stub_retrieve([]))
    store = FakeStore([])

    obs = tools.ejecutar_tool({"tool": "buscar_normas", "args": {}}, store)

    assert obs.startswith("error:")
    assert "consulta" in obs


def test_la_busqueda_sin_resultados_lo_dice(monkeypatch):
    """La valvula de escape tambien aplica dentro de la tool: si no hay normas
    relevantes, la observacion lo dice y el modelo no debe inventar."""
    monkeypatch.setattr(tools, "retrieve", stub_retrieve([]))
    store = FakeStore([])

    obs = tools.ejecutar_tool({"tool": "buscar_normas", "args": {"consulta": "patentes mineras marte"}}, store)

    assert "no encontro" in obs.lower()


# --- Bucle agentic -----------------------------------------------------------

def test_el_bucle_ejecuta_la_tool_y_luego_responde(monkeypatch):
    """Flujo tipico: 1a vuelta el modelo pide la tool, 2a vuelta responde con la
    observacion. La respuesta final es la del segundo turno."""
    monkeypatch.setattr(tools, "retrieve", stub_retrieve([make_result("c1", fuente="CST", articulos=["64"])]))
    store = FakeStore([])

    salidas = iter([
        '{"tool": "buscar_normas", "args": {"consulta": "despido sin justa causa"}}',
        "Segun el Codigo Sustantivo del Trabajo, Articulo 64, tienes derecho a...",
    ])
    generar = lambda system, user: next(salidas)

    resultado = tools.responder_con_tools("me despidieron", store, _generar=generar)

    assert "Articulo 64" in resultado["response"]
    assert len(resultado["tool_calls"]) == 1
    assert resultado["tool_calls"][0]["tool"] == "buscar_normas"


def test_el_bucle_responde_directo_si_el_modelo_no_pide_tool(monkeypatch):
    """Si el modelo decide no buscar (la pregunta no lo amerita), responde en la
    primera vuelta sin ejecutar la tool. Es la ventaja sobre el RAG de una pasada:
    no recupera cuando no hace falta."""
    monkeypatch.setattr(tools, "retrieve", stub_retrieve([]))
    store = FakeStore([])

    generar = lambda system, user: "Hola, cuentame tu situacion y te oriento."

    resultado = tools.responder_con_tools("hola", store, _generar=generar)

    assert resultado["tool_calls"] == []
    assert "Hola" in resultado["response"]


def test_el_bucle_no_corre_para_siempre(monkeypatch):
    """Si el modelo insiste en pedir la tool, max_llamadas acota el bucle y se
    fuerza una respuesta final."""
    monkeypatch.setattr(tools, "retrieve", stub_retrieve([make_result("c1")]))
    store = FakeStore([])

    # El modelo SIEMPRE pide la tool, nunca responde en texto.
    llamadas = {"n": 0}
    def generar(system, user):
        llamadas["n"] += 1
        return '{"tool": "buscar_normas", "args": {"consulta": "x"}}'

    resultado = tools.responder_con_tools("consulta", store, max_llamadas=3, _generar=generar)

    # 3 vueltas del bucle + 1 generacion forzada final = 4 llamadas al modelo.
    assert llamadas["n"] == 4
    assert len(resultado["tool_calls"]) == 3


def test_el_esquema_de_la_tool_es_json_serializable():
    """El esquema se le serializa al modelo: debe ser JSON valido con nombre,
    descripcion y args."""
    import json

    serializado = json.dumps(tools.TOOL_SCHEMA, ensure_ascii=False)
    recuperado = json.loads(serializado)

    assert recuperado["name"] == "buscar_normas"
    assert "consulta" in recuperado["args"]
    assert recuperado["description"].strip()


# --- Salida evaluable (contrato de answer_query) -----------------------------

def test_la_salida_del_tool_use_trae_contexts_para_ragas(monkeypatch):
    """Sin contexts la ruta de tool use no se puede evaluar con RAGAS: deben ser
    los chunks que devolvio la herramienta."""
    monkeypatch.setattr(tools, "retrieve", stub_retrieve([make_result("c1", fuente="CST", articulos=["64"])]))
    salidas = iter([
        '{"tool": "buscar_normas", "args": {"consulta": "despido"}}',
        "Segun el CST, Articulo 64, ...",
    ])

    r = tools.responder_con_tools("me despidieron", FakeStore([]), _generar=lambda s, u: next(salidas))

    assert r["contexts"] == ["texto normativo de c1"]
    assert r["retrieved_chunks"][0]["cita"] == "CST, Articulo 64"
    assert r["sistema"] == "tool_use"
    assert len(r["tool_calls"]) == 1


def test_la_salida_del_tool_use_se_convierte_al_registro_de_evaluacion(monkeypatch):
    from tools.evaluation import eval_set
    from tools.rag import pipeline

    monkeypatch.setattr(tools, "retrieve", stub_retrieve([make_result("c1")]))
    registro = eval_set.load_eval_set()[0]

    r = tools.responder_con_tools(registro["messages"][1]["content"], FakeStore([]),
                                  _generar=lambda s, u: "respuesta directa")
    record = pipeline.to_eval_record(r, registro)

    assert record["sistema"] == "tool_use"
    assert record["contexts"] == []


def test_un_error_de_validacion_no_trae_resultados(monkeypatch):
    monkeypatch.setattr(tools, "retrieve", stub_retrieve([make_result("c1")]))

    obs, resultados = tools.ejecutar_tool_con_resultados({"tool": "otra", "args": {}}, FakeStore([]))

    assert obs.startswith("error:")
    assert resultados == []


def test_el_prompt_del_tool_use_incluye_la_valvula_de_escape():
    """Misma frase que el RAG de una pasada, para que el harness la detecte igual
    en las dos rutas."""
    from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

    assert RESPUESTA_SIN_CONTEXTO in tools.SYSTEM_TOOLS


# --- Salvaguardas de codigo (docs seccion 25) ---------------------------------------

def test_tool_use_que_busca_y_no_encuentra_escapa_por_codigo(monkeypatch):
    from tools.rag.prompt_template import RESPUESTA_ESCAPE_POR_CODIGO

    monkeypatch.setattr(tools, "retrieve", stub_retrieve([]))
    salidas = iter(['{"tool": "buscar_normas", "args": {"consulta": "x"}}', "Te respondo de memoria..."])

    r = tools.responder_con_tools("consulta", FakeStore([]), _generar=lambda s, u: next(salidas))

    assert r["response"] == RESPUESTA_ESCAPE_POR_CODIGO
    assert r["verificacion"]["escape_por_codigo"] == "sin_contexto"


def test_tool_use_corrige_una_cita_no_recuperada(monkeypatch):
    monkeypatch.setattr(tools, "retrieve", stub_retrieve([make_result("c1", fuente="CST", articulos=["64"])]))
    salidas = iter(['{"tool": "buscar_normas", "args": {"consulta": "despido"}}',
                    "Segun el Articulo 65 ...", "Segun el Articulo 64 ..."])

    r = tools.responder_con_tools("me despidieron", FakeStore([]), _generar=lambda s, u: next(salidas))

    assert r["response"] == "Segun el Articulo 64 ..."
    assert r["verificacion"]["citas_rechazadas"] == ["65"]


def test_tool_use_saludo_sin_busqueda_pasa_tal_cual(monkeypatch):
    monkeypatch.setattr(tools, "retrieve", stub_retrieve([]))
    r = tools.responder_con_tools("hola", FakeStore([]), _generar=lambda s, u: "Hola, cuentame tu caso.")
    assert r["response"] == "Hola, cuentame tu caso."
