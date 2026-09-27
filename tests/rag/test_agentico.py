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


def make_result(chunk_id, *, fuente="Ley 820 de 2003", articulos=None):
    return SearchResult(
        chunk_id=chunk_id,
        text=f"texto normativo de {chunk_id}",
        fuente=fuente,
        url_fuente=f"https://suin/{chunk_id}",
        score=0.9,
        articulos_incluidos=articulos or ["20"],
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
    # Reajuste maximo de un canon de 1.200.000 con IPC de 5,2 %.
    assert agentico.calculadora("1200000 * 1.052") == "1262400"
    assert agentico.calculadora("2000000 / 30 * 7") == "466666.6667"


def test_calculadora_entiende_miles_con_punto_y_x():
    assert agentico.calculadora("2.000.000 x 3") == "6000000"


def test_un_solo_punto_es_decimal_no_miles():
    """El caso del IPC: 1.052 es 1,052 y no mil cincuenta y dos. Leerlo como
    miles daria un canon 1000 veces mayor sin ningun error visible."""
    assert agentico.calculadora("1200000 * 1.052") == "1262400"
    assert agentico.calculadora("1.200.000 * 1.052") == "1262400"


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
    busquedas = stub_retrieve(monkeypatch, [make_result("ley820::20")])
    generar = generador(
        "Pensamiento: necesito el tope del reajuste\nAccion: buscar_normas[reajuste canon arrendamiento IPC]",
        "Pensamiento: calculo el tope\nAccion: calculadora[1200000 * 1.052]",
        "Pensamiento: ya tengo todo\nAccion: Responder[Segun la Ley 820 de 2003, Articulo 20, el canon puede subir hasta 1262400.]",
    )

    r = agentico.agente_react("pago 1.200.000 de arriendo y el IPC fue 5,2 %, hasta cuanto me suben",
                              object(), _generar=generar)

    assert r["response"] == "Segun la Ley 820 de 2003, Articulo 20, el canon puede subir hasta 1262400."
    assert busquedas == ["reajuste canon arrendamiento IPC"]
    assert [p["accion"] for p in r["traza"]] == ["buscar_normas", "calculadora", "Responder"]
    assert r["traza"][1]["observacion"] == "1262400"


def test_la_salida_trae_los_contexts_que_vio_el_agente(monkeypatch):
    """Sin contexts no hay RAGAS: deben ser los chunks de sus busquedas, sin
    duplicados aunque busque dos veces lo mismo."""
    stub_retrieve(monkeypatch, [make_result("ley820::20")])
    generar = generador(
        "Accion: buscar_normas[reajuste canon]",
        "Accion: buscar_normas[incremento arriendo IPC]",
        "Accion: Responder[listo]",
    )

    r = agentico.agente_react("consulta", object(), _generar=generar)

    assert r["contexts"] == ["texto normativo de ley820::20"]
    assert r["n_retrieved"] == 1
    assert r["sistema"] == "react"


def test_la_salida_se_convierte_al_registro_de_evaluacion(monkeypatch):
    """Mismo contrato que answer_query: to_eval_record la acepta sin casos
    especiales, con la ruta y la traza para auditar."""
    stub_retrieve(monkeypatch, [make_result("ley820::20")])
    generar = generador("Accion: buscar_normas[reajuste canon]", "Accion: Responder[respuesta]")
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


# --- calcular_plazo ------------------------------------------------------------

def test_plazo_en_dias_habiles_cuenta_desde_el_dia_siguiente():
    """15 dias habiles de un derecho de peticion radicado el martes 1 de
    septiembre de 2026 (sin festivos en el medio): vence el martes 22."""
    obs = agentico.calcular_plazo("2026-09-01, 15, habiles")
    assert "2026-09-22" in obs


def test_plazo_en_dias_habiles_salta_los_festivos_de_colombia():
    """El lunes 12 de octubre de 2026 es festivo (Dia de la Raza): un dia habil
    despues del viernes 9 es el martes 13, y la observacion dice que se salto."""
    obs = agentico.calcular_plazo("2026-10-09, 1, habiles")
    assert "2026-10-13" in obs
    assert "2026-10-12" in obs


def test_plazo_en_dias_calendario():
    assert "2026-09-11" in agentico.calcular_plazo("01/09/2026, 10, calendario")


def test_plazo_con_argumentos_invalidos_devuelve_error():
    assert agentico.calcular_plazo("mañana, 15, habiles").startswith("error:")
    assert agentico.calcular_plazo("2026-09-01, quince, habiles").startswith("error:")
    assert agentico.calcular_plazo("2026-09-01, 15, semanas").startswith("error:")
    assert agentico.calcular_plazo("2026-09-01").startswith("error:")


def test_el_agente_encadena_busqueda_plazo_y_respuesta(monkeypatch):
    """Derecho de peticion: buscar el termino, contar los dias, responder."""
    stub_retrieve(monkeypatch, [make_result("cpaca::14", fuente="Ley 1437 de 2011", articulos=["14"])])
    generar = generador(
        "Accion: buscar_normas[termino para responder derecho de peticion]",
        "Accion: calcular_plazo[2026-09-01, 15, habiles]",
        "Accion: Responder[Segun la Ley 1437 de 2011, Articulo 14, te deben responder a mas tardar el 2026-09-22.]",
    )

    r = agentico.agente_react("radique un derecho de peticion el 1 de septiembre", object(), _generar=generar)

    assert [p["accion"] for p in r["traza"]] == ["buscar_normas", "calcular_plazo", "Responder"]
    assert "2026-09-22" in r["traza"][1]["observacion"]


# --- Verificacion de citas -----------------------------------------------------

def test_extrae_los_articulos_citados():
    texto = "Segun el artículo 20 de la Ley 820 de 2003, los arts. 5, 6 y 7 y el art. 6º"
    assert agentico.articulos_citados(texto) == {"20", "5", "6", "7"}


def test_una_cita_que_el_agente_vio_esta_respaldada():
    vistos = [make_result("ley820::20", articulos=["20"])]
    assert agentico.citas_no_respaldadas("Segun el articulo 20 ...", vistos) == []


def test_una_cita_que_el_agente_no_vio_se_detecta():
    vistos = [make_result("ley820::20", articulos=["20"])]
    assert agentico.citas_no_respaldadas("Segun los articulos 20 y 518 ...", vistos) == ["518"]


def test_citar_el_articulo_que_menciono_el_usuario_no_es_inventar():
    """La respuesta puede aclarar que el articulo que dijo el usuario no aplica."""
    assert agentico.citas_no_respaldadas(
        "El articulo 64 que mencionas no trata ese tema.", [], query="que dice el articulo 64"
    ) == []


def test_una_respuesta_con_cita_inventada_se_rechaza_y_el_agente_corrige(monkeypatch):
    """El control de 'no inventar normas': la primera respuesta cita un articulo
    que no vio, se le devuelve como observacion y la segunda se acepta."""
    stub_retrieve(monkeypatch, [make_result("ley820::20", articulos=["20"])])
    generar = generador(
        "Accion: buscar_normas[reajuste canon]",
        "Accion: Responder[Segun el Articulo 20 y el Articulo 518, puede subir hasta el IPC.]",
        "Accion: Responder[Segun el Articulo 20 de la Ley 820 de 2003, puede subir hasta el IPC.]",
    )

    r = agentico.agente_react("cuanto me pueden subir el arriendo", object(), _generar=generar)

    assert r["response"] == "Segun el Articulo 20 de la Ley 820 de 2003, puede subir hasta el IPC."
    rechazo = r["traza"][1]
    assert rechazo["accion"] == "Responder (rechazado)"
    assert "518" in rechazo["observacion"]


def test_si_insiste_en_citar_lo_que_no_vio_responde_con_la_valvula_de_escape(monkeypatch):
    stub_retrieve(monkeypatch, [])
    generar = lambda system, user: "Accion: Responder[Segun el Articulo 999, si.]"

    r = agentico.agente_react("consulta", object(), max_pasos=2, _generar=generar)

    assert RESPUESTA_SIN_CONTEXTO in r["response"]
    assert all(p["accion"] != "Responder" for p in r["traza"])


# --- leer_articulo -------------------------------------------------------------

def meta(chunk_id, fuente, articulos, text=None):
    return {"chunk_id": chunk_id, "doc_id": chunk_id.split("::")[0], "text": text or f"texto de {chunk_id}",
            "fuente": fuente, "tipo": "ley", "url_fuente": f"https://suin/{chunk_id}",
            "articulos_incluidos": articulos, "capitulo": "", "vigente": True}


class StoreConMetadata:
    """Solo la metadata: leer_articulo no hace busqueda semantica."""
    def __init__(self):
        self.metadata = [
            meta("ley820::19", "Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana)", ["19"]),
            meta("ley820::20", "Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana)", ["20"],
                 "Articulo 20. Reajuste del canon de arrendamiento..."),
            meta("ley820::21", "Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana)", ["21", "22"],
                 "Articulo 21. Incumplimiento de las obligaciones..."),
            meta("cst::64", "Decreto 2663 de 1950 (Codigo Sustantivo del Trabajo)", ["64"]),
            meta("cgp::64", "Ley 1564 de 2012 (Codigo General del Proceso)", ["64"]),
        ]


def test_lee_el_articulo_exacto_con_su_cita():
    obs, res = agentico.leer_articulo("Ley 820 de 2003, 20", StoreConMetadata())

    assert [r.chunk_id for r in res] == ["ley820::20"]
    assert "Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana), Articulo 20" in obs
    assert "Reajuste del canon" in obs
    assert res[0].dense_score is None   # lectura exacta, no vino por la via densa


def test_encuentra_el_articulo_dentro_de_un_chunk_agrupado():
    """Los articulos cortos se agrupan en un chunk: el 22 vive en el chunk del 21."""
    _, res = agentico.leer_articulo("Ley 820, articulo 22", StoreConMetadata())
    assert [r.chunk_id for r in res] == ["ley820::21"]


def test_entiende_siglas_de_la_norma():
    _, res = agentico.leer_articulo("CST, 64", StoreConMetadata())
    assert [r.chunk_id for r in res] == ["cst::64"]
    _, res = agentico.leer_articulo("CGP, art. 64", StoreConMetadata())
    assert [r.chunk_id for r in res] == ["cgp::64"]


def test_articulo_que_no_esta_lo_dice_y_no_trae_resultados():
    """El caso del usuario equivocado de numero: no se inventa el contenido."""
    obs, res = agentico.leer_articulo("Ley 820 de 2003, 999", StoreConMetadata())
    assert res == []
    assert "no esta en el corpus" in obs
    assert "equivocado" in obs


def test_norma_que_no_esta_en_el_corpus_lo_dice():
    obs, res = agentico.leer_articulo("Codigo Civil, 1", StoreConMetadata())
    assert res == []
    assert "No reconozco la norma" in obs


def test_norma_ambigua_pide_precisar():
    """'La de 1991' puede ser la Constitucion o el Decreto 2591 de 1991: no se
    elige al azar, se pide la norma con su numero."""
    store = StoreConMetadata()
    store.metadata += [meta("cp::1", "Constitucion Politica de 1991", ["1"]),
                       meta("d2591::1", "Decreto 2591 de 1991 (Reglamentacion de la accion de tutela)", ["1"])]
    obs, res = agentico.leer_articulo("la norma de 1991, 1", store)
    assert res == []
    assert "ambigua" in obs


def test_argumentos_invalidos_devuelven_error():
    assert agentico.leer_articulo("Ley 820 de 2003", StoreConMetadata())[0].startswith("error:")
    assert agentico.leer_articulo("Ley 820 de 2003, veinte", StoreConMetadata())[0].startswith("error:")


def test_usuario_equivocado_de_articulo_el_agente_lo_lee_y_busca_el_tema(monkeypatch):
    """El usuario cree que el articulo 21 de la Ley 820 habla del reajuste. El
    agente lo lee, ve que no, busca el tema y responde citando el correcto (el
    20), que si vio -- asi que la verificacion de citas lo acepta."""
    busquedas = stub_retrieve(monkeypatch, [make_result("ley820::20", articulos=["20"])])
    generar = generador(
        "Pensamiento: el usuario menciona el 21, lo leo\nAccion: leer_articulo[Ley 820 de 2003, 21]",
        "Pensamiento: el 21 no trata del reajuste, busco el tema\nAccion: buscar_normas[reajuste del canon]",
        "Accion: Responder[El articulo 21 que mencionas trata del incumplimiento; el reajuste esta en el Articulo 20.]",
    )

    r = agentico.agente_react("segun el articulo 21 de la ley 820 cuanto me pueden subir el arriendo",
                              StoreConMetadata(), _generar=generar)

    assert [p["accion"] for p in r["traza"]] == ["leer_articulo", "buscar_normas", "Responder"]
    assert "Incumplimiento" in r["traza"][0]["observacion"]
    assert busquedas == ["reajuste del canon"]
    assert set(r["contexts"]) == {"Articulo 21. Incumplimiento de las obligaciones...", "texto normativo de ley820::20"}


# --- Prudencia (comprobaciones compartidas con DSPy y la evaluacion) --------------

def test_detecta_sentencias_citadas():
    assert agentico.sentencias_citadas("segun la T-760 de 2008 y la SU-111/97") == {"T-760", "SU-111"}
    assert agentico.sentencias_citadas("segun el articulo 20") == set()


def test_detecta_promesas_de_resultado():
    assert agentico.promete_resultado("Te garantizo que vas a ganar la tutela")
    assert not agentico.promete_resultado("El resultado depende de las pruebas y del juez")


def test_es_prudente():
    assert agentico.es_prudente(f"{RESPUESTA_SIN_CONTEXTO}.", set())
    assert agentico.es_prudente("Lo primero es tu seguridad: llama a la Linea 123.", set())
    assert agentico.es_prudente("Segun el Articulo 20, ...", {"20"})
    assert not agentico.es_prudente("Segun el Articulo 518, ...", {"20"})
    assert not agentico.es_prudente("La sentencia T-760 de 2008 te protege.", set())
    assert not agentico.es_prudente("Te garantizo que la ganas.", set())


def test_citas_no_respaldadas_acepta_el_conjunto_de_vistos():
    assert agentico.citas_no_respaldadas("articulos 20 y 21", vistos={"20"}) == ["21"]


def test_react_que_busca_y_no_encuentra_escapa_por_codigo(monkeypatch):
    """Si busco y no encontro ninguna norma, responder igual es responder de
    memoria (hallazgo de S08, docs seccion 25)."""
    from tools.rag.prompt_template import RESPUESTA_ESCAPE_POR_CODIGO

    stub_retrieve(monkeypatch, [])
    generar = generador("Accion: buscar_normas[robo de celular]", "Accion: Responder[Debes denunciar ante la Fiscalia.]")

    r = agentico.agente_react("me robaron el celular", object(), _generar=generar)

    assert r["response"] == RESPUESTA_ESCAPE_POR_CODIGO
    assert r["traza"][-1]["accion"].startswith("Responder (escape por codigo")


def test_react_rechaza_sentencias_citadas(monkeypatch):
    stub_retrieve(monkeypatch, [make_result("ley820::20")])
    generar = generador("Accion: buscar_normas[x]", "Accion: Responder[Segun la T-760 de 2008, si.]",
                        "Accion: Responder[Segun el Articulo 20, si.]")

    r = agentico.agente_react("q", object(), _generar=generar)

    assert r["traza"][1]["accion"] == "Responder (rechazado)"
    assert r["response"] == "Segun el Articulo 20, si."
