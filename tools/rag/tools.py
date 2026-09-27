"""Tool use: el modelo decide cuando buscar en el corpus.

Patron agentic de function calling: en vez de recuperar SIEMPRE (RAG de una
pasada), se le describe al modelo una herramienta -- buscar_normas -- y el
modelo decide si la necesita. Si la necesita, responde con un JSON
{"tool": "buscar_normas", "args": {"consulta": "..."}}; el sistema lo parsea,
ejecuta la busqueda (el retrieval avanzado: hybrid + rerank) y le devuelve los
chunks como observacion para que redacte la respuesta final.

Exponer el retrieval como herramienta le da al modelo dos capacidades que el RAG
de una pasada no tiene:

1. REFORMULAR la consulta antes de buscar. La consulta del usuario en Amparo es
   coloquial y a veces ambigua ("me estan cobrando algo raro en el banco");
   dejar que el modelo la convierta en una consulta de busqueda ("reporte
   negativo central de riesgo cobro no reconocido") es una transformacion
   acotada, con proposito.
2. DECIDIR no buscar cuando la pregunta no lo amerita (un saludo, una aclaracion
   sobre su propia respuesta anterior), ahorrando una recuperacion inutil. El RAG
   de una pasada busca siempre.

La herramienta envuelve el mismo retrieval avanzado, sin abrir una segunda ruta
de recuperacion que mantener.

Se expone UNA sola herramienta. Amparo consulta fuentes verificadas; no ejecuta
acciones sobre el mundo (radicar una tutela, pagar una multa). Consultar el
corpus es su unica accion legitima, y buscar_normas la cubre.

La generacion (el modelo) es stack pesado: se importa de forma perezosa y se
inyecta como parametro en los tests, para que el bucle se pruebe sin GPU.
"""
from __future__ import annotations

import json
import re
import unicodedata

from tools.rag import config
from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO
from tools.rag.retrieve import retrieve

# Numero de chunks que la herramienta devuelve como observacion. Igual que el
# TOP_K del RAG de una pasada: la tool no cambia cuanto contexto ve el modelo,
# solo QUIEN decide cuando recuperarlo.
TOOL_TOP_K = config.TOP_K

# Esquema de la herramienta, en el formato que espera un modelo con function
# calling: nombre + descripcion (para que el modelo sepa CUANDO usarla) + args.
# La descripcion es en español y orientada al dominio a proposito: es lo que el
# modelo lee para decidir, y un modelo pequeño decide mejor con una descripcion
# concreta ("normas colombianas") que con una generica ("busca informacion").
TOOL_SCHEMA = {
    "name": "buscar_normas",
    "description": (
        "Busca en el corpus de normas colombianas verificadas (leyes, decretos, "
        "codigos, la Constitucion) y devuelve los articulos mas relevantes con su "
        "cita. Usala siempre que la respuesta requiera fundamentar en una norma, "
        "un articulo o un plazo legal. No la uses para saludos ni aclaraciones."
    ),
    "args": {"consulta": "string"},
}

# Instruccion de sistema del bucle de tools. El esquema de la herramienta NO va
# aqui: se pasa aparte, en el formato nativo (BUSCAR_NORMAS, mas abajo).
SYSTEM_TOOLS = (
    "Eres Amparo, un asistente juridico de derecho colombiano para personas sin "
    "formacion juridica. Tienes la herramienta buscar_normas, que consulta un "
    "corpus de normas colombianas verificadas. Usala SIEMPRE que la pregunta sea "
    "juridica (derechos, plazos, tramites, obligaciones): no respondas de memoria. "
    "Solo un saludo o una charla sin contenido juridico se responde sin buscar. "
    "Cuando tengas las normas, responde al usuario en texto normal, citando la "
    "norma y el articulo tal como aparecen en el resultado de la herramienta. Nunca "
    "cites una norma que no haya aparecido en un resultado. Si la herramienta no "
    "encuentra normas que respalden la respuesta, responde exactamente: "
    f'"{RESPUESTA_SIN_CONTEXTO}." -- la misma valvula de escape del RAG de una '
    "pasada, para que el harness la detecte igual en las dos rutas."
)


class ToolError(ValueError):
    """La llamada a herramienta no se pudo ejecutar (tool inexistente, args mal)."""


def extraer_tool_call(texto: str) -> dict | None:
    """Extrae un {"tool":..., "args":{...}} del texto del modelo, o None.

    Robusto a proposito: busca el primer '{' y
    el ultimo '}' y trata de parsear. Si no hay JSON, o esta mal formado, o no
    tiene la forma esperada, devuelve None -- y el bucle interpreta ese None como
    "el modelo respondio directo, sin pedir herramienta". Un JSON malformado NO
    es un error fatal: es el caso normal de un modelo pequeño que a veces no
    emite JSON valido, y el sistema debe degradar a responder directo, no romper.
    """
    if not texto:
        return None
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fin == -1 or fin <= inicio:
        return None
    try:
        pedido = json.loads(texto[inicio : fin + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(pedido, dict):
        return None
    if "tool" not in pedido and "name" in pedido:          # {"name", "arguments"}
        pedido = {"tool": pedido["name"], "args": pedido.get("arguments") or {}}
    if "tool" not in pedido:
        return None
    return pedido


# --- Formato nativo de herramientas (hallazgo 4 de S10, docs seccion 26) ------
#
# La primera version le pedia al modelo un JSON inventado ({"tool": ..., "args":
# ...}) descrito en el prompt. Con LoRA, Qwen casi nunca lo emitia: en la
# corrida de S10 del 2026-09-27 el tool use no busco en 53 de 56 preguntas. Ahora
# las herramientas van en el formato estandar de function calling, que la
# plantilla de chat de Qwen2.5 presenta en el formato con el que el modelo fue
# entrenado para pedir herramientas: <tool_call>{"name": ..., "arguments": ...}
# </tool_call>. El parser sigue aceptando el JSON viejo como respaldo.

def herramienta(nombre: str, descripcion: str, parametros: dict[str, str]) -> dict:
    """Esquema de una herramienta en el formato estandar de function calling."""
    return {
        "type": "function",
        "function": {
            "name": nombre,
            "description": descripcion,
            "parameters": {
                "type": "object",
                "properties": {k: {"type": "string", "description": v} for k, v in parametros.items()},
                "required": list(parametros),
            },
        },
    }


BUSCAR_NORMAS = herramienta(
    "buscar_normas", TOOL_SCHEMA["description"],
    {"consulta": "que buscar, en terminos juridicos (p. ej. 'reajuste canon arrendamiento IPC')"},
)

_BLOQUE_TOOL_CALL = re.compile(r"<tool_call>\s*(.*?)\s*(?:</tool_call>|$)", re.DOTALL)


def _json_de(texto: str):
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fin <= inicio:
        return None
    try:
        return json.loads(texto[inicio : fin + 1])
    except (json.JSONDecodeError, ValueError):
        return None


def extraer_llamadas(texto: str) -> tuple[str, list[dict]]:
    """(texto libre, llamadas) de una salida del modelo.

    Llamadas en formato nativo (<tool_call>{"name", "arguments"}</tool_call>,
    una o varias) y, como respaldo, el JSON viejo {"tool", "args"}. Cada llamada
    queda como {"name": str, "arguments": dict}. El texto libre es lo que el
    modelo escribio fuera de las llamadas: su razonamiento, o la respuesta final
    si no pidio ninguna herramienta."""
    texto = texto or ""
    llamadas = []
    for bloque in _BLOQUE_TOOL_CALL.findall(texto):
        obj = _json_de(bloque)
        if not isinstance(obj, dict):
            continue
        nombre = obj.get("name") or obj.get("tool")
        args = obj.get("arguments", obj.get("args", {}))
        if isinstance(args, str):
            args = _json_de(args) or {}
        if nombre:
            llamadas.append({"name": nombre, "arguments": args if isinstance(args, dict) else {}})
    libre = _BLOQUE_TOOL_CALL.sub("", texto).strip()
    if not llamadas and "<tool_call>" not in texto:
        viejo = extraer_tool_call(texto)
        if viejo is not None:
            llamadas.append({"name": viejo["tool"], "arguments": viejo.get("args") or {}})
            libre = texto[: texto.find("{")].strip()
    return libre, llamadas


def turno_con_llamada(texto_libre: str, llamada: dict) -> dict:
    """Mensaje del asistente que pide una herramienta (formato estandar)."""
    return {"role": "assistant", "content": texto_libre or "",
            "tool_calls": [{"type": "function",
                            "function": {"name": llamada["name"], "arguments": llamada["arguments"]}}]}


def turno_resultado(nombre: str, observacion: str) -> dict:
    return {"role": "tool", "name": nombre, "content": observacion}


_CHARLA_TRIVIAL = re.compile(
    r"^(hola|holi|buen[oa]s?( dias| tardes| noches)?|saludos|gracias|muchas gracias|mil gracias|"
    r"ok|okay|listo|vale|perfecto|chao|adios|hasta luego|hasta pronto|quien eres|que eres|"
    r"que puedes hacer|como estas|como te llamas)"
    r"([ ,.!?]+(hola|buen[oa]s?( dias| tardes| noches)?|gracias|amparo|como estas|que tal))*[ ,.!?]*$"
)


def es_charla_trivial(query: str) -> bool:
    """¿La consulta es un saludo o charla sin contenido juridico?

    Es la UNICA excepcion a "toda pregunta se responde con normas buscadas": la
    red de seguridad (buscar por codigo si el modelo no busco) no se aplica aqui.
    Conservadora a proposito: ante la duda, no es trivial y se busca."""
    q = unicodedata.normalize("NFKD", query or "").encode("ascii", "ignore").decode().lower()
    q = re.sub(r"[¿¡]", "", q).strip()
    return len(q.split()) <= 6 and bool(_CHARLA_TRIVIAL.match(q))


_NOMBRES_HERRAMIENTAS = re.compile(
    r"\b(buscar_normas|leer_articulo|calcular_plazo|calculadora)\b|\bRespond(?:er|e)\s*\[", re.IGNORECASE
)


def menciona_herramientas(texto: str) -> bool:
    """La 'respuesta' habla de las herramientas en vez de usarlas ("calcula el
    plazo con calcular_plazo..."): no es una respuesta para el usuario."""
    return bool(_NOMBRES_HERRAMIENTAS.search(texto or ""))


def formatear_observacion(resultados) -> str:
    """Convierte los chunks recuperados en la observacion que ve el modelo.

    Cada chunk va con su CITA visible, igual que en el prompt aumentado de S07:
    es lo que permite que el modelo, al redactar, cite algo que efectivamente
    aparecio en la observacion, y no de memoria. Sin la cita, la tool le daria
    texto anonimo y volveria el fallo que todo el RAG viene a cerrar.
    """
    if not resultados:
        return "La busqueda no encontro normas relevantes para esa consulta."
    bloques = []
    for i, r in enumerate(resultados, start=1):
        bloques.append(f"[{i}] {r.cita}\n{r.text}")
    return "\n\n".join(bloques)


def ejecutar_tool(
    pedido: dict,
    store,
    *,
    top_k: int = TOOL_TOP_K,
    use_hybrid: bool = True,
    use_rerank: bool = True,
    bm25=None,
) -> str:
    """Despacha una llamada a herramienta y devuelve solo su observacion.

    Envoltura de ejecutar_tool_con_resultados para quien solo necesita el texto
    que ve el modelo.
    """
    observacion, _ = ejecutar_tool_con_resultados(
        pedido, store, top_k=top_k, use_hybrid=use_hybrid, use_rerank=use_rerank, bm25=bm25
    )
    return observacion


def ejecutar_tool_con_resultados(
    pedido: dict,
    store,
    *,
    top_k: int = TOOL_TOP_K,
    use_hybrid: bool = True,
    use_rerank: bool = True,
    bm25=None,
) -> tuple[str, list]:
    """Despacha una llamada a herramienta validada: (observacion, resultados).

    Valida que la herramienta exista y que traiga los args que declara el
    esquema. La busqueda usa el retrieval avanzado (hybrid + rerank por defecto):
    la tool no reimplementa la busqueda, invoca la que ya existe.

    Un error de validacion se devuelve como observacion (string), no se lanza:
    asi el modelo lo lee ("no existe la herramienta X") y puede corregir en la
    siguiente vuelta, en vez de tumbar el bucle. En ese caso no hay resultados.

    Los resultados (SearchResult) van aparte de la observacion porque son la
    evidencia que consume la evaluacion: sin ellos no hay `contexts`, y RAGAS no
    puede medir context precision/recall ni faithfulness de esta ruta.
    """
    nombre = pedido.get("tool")
    if nombre != TOOL_SCHEMA["name"]:
        return (
            f"error: no existe la herramienta {nombre!r}. La unica disponible es 'buscar_normas'.",
            [],
        )

    args = pedido.get("args") or {}
    consulta = args.get("consulta")
    if not isinstance(consulta, str) or not consulta.strip():
        return "error: buscar_normas requiere un arg 'consulta' de tipo texto no vacio.", []

    resultados = retrieve(
        consulta,
        store,
        top_k=top_k,
        use_hybrid=use_hybrid,
        use_rerank=use_rerank,
        bm25=bm25,
    )
    return formatear_observacion(resultados), resultados


def resultado_para_evaluacion(
    query: str,
    response: str,
    resultados,
    *,
    sistema: str,
    use_lora: bool,
    use_hybrid: bool,
    use_rerank: bool,
    top_k: int = TOOL_TOP_K,
    traza: list | None = None,
) -> dict:
    """Arma la salida de una ruta agentica con el mismo contrato que answer_query.

    Asi pipeline.to_eval_record() la convierte al formato RAGAS sin casos
    especiales, y las rutas (una pasada, tool use, ReAct) quedan comparables
    sobre el mismo eval set. `resultados` son todos los chunks que el agente vio
    en sus observaciones, sin duplicados, en el orden en que aparecieron.
    """
    unicos, vistos = [], set()
    for r in resultados:
        if r.chunk_id not in vistos:
            vistos.add(r.chunk_id)
            unicos.append(r)
    return {
        "query": query,
        "response": response,
        "contexts": [r.text for r in unicos],
        "retrieved_chunks": [
            {
                "chunk_id": r.chunk_id,
                "cita": r.cita,
                "url_fuente": r.url_fuente,
                "score": round(r.score, 4),
                "dense_score": round(r.dense_score, 4) if r.dense_score is not None else None,
            }
            for r in unicos
        ],
        "n_retrieved": len(unicos),
        "used_lora": use_lora,
        "used_hybrid": use_hybrid,
        "used_rerank": use_rerank,
        "top_k": top_k,
        "min_score": config.RETRIEVAL_MIN_SCORE,
        "sistema": sistema,
        "traza": traza or [],
    }


def responder_con_tools(
    query: str,
    store,
    *,
    max_llamadas: int = 3,
    use_hybrid: bool = True,
    use_rerank: bool = True,
    use_lora: bool = False,
    bm25=None,
    model_bundle=None,
    _generar=None,
) -> dict:
    """Bucle agentic: propone -> ejecuta -> observa -> responde.

    El modelo recibe la herramienta buscar_normas en el formato nativo de
    function calling (ver arriba) y decide si la pide y con que consulta. Cada
    llamada se ejecuta y su resultado vuelve como mensaje "tool"; cuando el
    modelo responde en texto, esa es la respuesta.

    Red de seguridad (hallazgo 4 de S10, docs seccion 26): si el modelo responde
    sin haber buscado y la consulta NO es charla trivial (es_charla_trivial), el
    codigo busca con la consulta del usuario y le devuelve el resultado para que
    responda con eso. Asi la decision de "no buscar" solo vale para un saludo.

    _generar: funcion (mensajes, herramientas) -> str, inyectable para tests. Por
    defecto usa el generador real (Qwen, GPU) via import perezoso.

    Devuelve el mismo contrato que pipeline.answer_query (query, response,
    contexts, retrieved_chunks, ...) mas `tool_calls` (la traza, con
    `forzado_por_codigo` en cada llamada) y `verificacion` (incluye `busqueda`:
    "modelo", "forzada_por_codigo" o "ninguna").
    """
    generar = _generar if _generar is not None else _generar_mensajes_por_defecto(model_bundle, use_lora)

    mensajes = [{"role": "system", "content": SYSTEM_TOOLS}, {"role": "user", "content": query}]
    traza: list[dict] = []
    vistos: list = []

    def _ejecutar(llamada: dict, texto_libre: str = "", por_codigo: bool = False) -> None:
        observacion, resultados = ejecutar_tool_con_resultados(
            {"tool": llamada["name"], "args": llamada["arguments"]}, store,
            use_hybrid=use_hybrid, use_rerank=use_rerank, bm25=bm25,
        )
        vistos.extend(resultados)
        traza.append({"tool": llamada["name"], "args": llamada["arguments"], "observacion": observacion,
                      "forzado_por_codigo": por_codigo})
        mensajes.append(turno_con_llamada(texto_libre, llamada))
        mensajes.append(turno_resultado(llamada["name"], observacion))

    def _busqueda() -> str:
        if not traza:
            return "ninguna"
        return "forzada_por_codigo" if all(c["forzado_por_codigo"] for c in traza) else "modelo"

    def _salida(respuesta: str) -> dict:
        respuesta, verificacion = _verificar(respuesta)
        verificacion["busqueda"] = _busqueda()
        resultado = resultado_para_evaluacion(
            query, respuesta, vistos, sistema="tool_use", use_lora=use_lora,
            use_hybrid=use_hybrid, use_rerank=use_rerank, traza=traza,
        )
        resultado["tool_calls"] = traza
        resultado["verificacion"] = verificacion
        return resultado

    def _verificar(respuesta: str) -> tuple[str, dict]:
        """Salvaguardas de codigo antes de entregar (secciones 25 y 26 de docs):
        - uso la herramienta y no encontro ninguna norma -> escape por codigo;
        - cita articulos que no trajo la herramienta, o sentencias, o habla de las
          herramientas en vez de responder -> una correccion; si insiste, escape.
        Un saludo sin busqueda y sin citas pasa tal cual."""
        from tools.rag.agentico import citas_no_verificables, nota_de_correccion
        from tools.rag.prompt_template import RESPUESTA_ESCAPE_POR_CODIGO

        if RESPUESTA_SIN_CONTEXTO.lower() in respuesta.lower():
            return respuesta, {"escape_por_codigo": None, "citas_rechazadas": []}
        if traza and not vistos:
            return RESPUESTA_ESCAPE_POR_CODIGO, {"escape_por_codigo": "sin_contexto", "citas_rechazadas": []}
        rechazadas = citas_no_verificables(respuesta, vistos, query)
        meta = menciona_herramientas(respuesta)
        if not rechazadas and not meta:
            return respuesta, {"escape_por_codigo": None, "citas_rechazadas": []}
        nota = nota_de_correccion(rechazadas) if rechazadas else (
            "Tu respuesta describe herramientas en vez de responder al usuario.")
        corregida = generar(mensajes + [{"role": "user", "content": nota + " Responde ahora al usuario, "
                                          "en texto normal y sin pedir mas herramientas."}], None)
        libre, llamadas = extraer_llamadas(corregida)
        if llamadas or citas_no_verificables(libre, vistos, query) or menciona_herramientas(libre) or not libre:
            return RESPUESTA_ESCAPE_POR_CODIGO, {"escape_por_codigo": "citas_no_verificables",
                                                 "citas_rechazadas": rechazadas}
        return libre, {"escape_por_codigo": None, "citas_rechazadas": rechazadas}

    for _ in range(max_llamadas):
        salida = generar(mensajes, [BUSCAR_NORMAS])
        libre, llamadas = extraer_llamadas(salida)
        if not llamadas:
            if not traza and not es_charla_trivial(query):
                # Red de seguridad: respondio sin buscar una pregunta juridica.
                _ejecutar({"name": "buscar_normas", "arguments": {"consulta": query}}, por_codigo=True)
                continue
            return _salida(libre or salida)
        for llamada in llamadas:
            _ejecutar(llamada, libre)

    # Se agotaron las llamadas: se fuerza una respuesta final sin mas herramientas.
    salida = generar(mensajes + [{"role": "user", "content": "Responde ya al usuario con lo que tienes, "
                                  "sin pedir mas herramientas."}], None)
    libre, llamadas = extraer_llamadas(salida)
    if llamadas or not libre:
        # Sigue pidiendo herramientas: no respondio. Escape por codigo.
        from tools.rag.prompt_template import RESPUESTA_ESCAPE_POR_CODIGO

        resultado = resultado_para_evaluacion(
            query, RESPUESTA_ESCAPE_POR_CODIGO, vistos, sistema="tool_use", use_lora=use_lora,
            use_hybrid=use_hybrid, use_rerank=use_rerank, traza=traza,
        )
        resultado["tool_calls"] = traza
        resultado["verificacion"] = {"escape_por_codigo": "no_respondio", "citas_rechazadas": [],
                                     "busqueda": _busqueda()}
        return resultado
    return _salida(libre)


def _generar_mensajes_por_defecto(model_bundle, use_lora: bool = False):
    """Generador real (Qwen) como funcion (mensajes, herramientas) -> str.

    Pasa las herramientas a la plantilla de chat (formato nativo). Import
    perezoso: stack pesado, vive en Colab. Tambien lo usa el agente ReAct."""
    from tools.evaluation import generation

    from tools.rag.pipeline import load_model

    model, tokenizer = model_bundle if model_bundle else load_model(use_lora=use_lora)

    def generar(mensajes: list[dict], herramientas: list[dict] | None = None) -> str:
        return generation.run_messages_generation(
            model, tokenizer, mensajes, config.MAX_NEW_TOKENS_GENERATION, tools=herramientas or None
        )

    return generar


def _generar_por_defecto(model_bundle, use_lora: bool = False):
    """Envuelve el generador real (Qwen) como una funcion (system, user) -> str.

    Import perezoso de la generacion: stack pesado, vive en Colab. Se aisla aca
    para que el resto del modulo (esquema, dispatcher, parser) sea importable y
    testeable sin GPU. Tambien lo reusa el agente ReAct (tools/rag/agentico.py).
    """
    from tools.evaluation import generation

    from tools.rag.pipeline import load_model

    model, tokenizer = model_bundle if model_bundle else load_model(use_lora=use_lora)

    def generar(system: str, user: str) -> str:
        return generation.run_chat_generation(
            model, tokenizer, system, user, config.MAX_NEW_TOKENS_GENERATION
        )

    return generar
