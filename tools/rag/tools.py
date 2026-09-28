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

# Marca de llamada danada (hallazgo 5 de S10, docs seccion 27). En la corrida del
# 2026-09-27, en dos preguntas del ReAct (9039, 9044) el modelo escribio "urnal"
# en vez de <tool_call> antes de cada JSON, a veces varias llamadas seguidas y
# con una comilla simple cerrando un valor ('...'}}). El parser anterior no
# reconocia nada de eso como llamada, lo tomaba como respuesta, la rechazaba por
# describir herramientas y la pregunta terminaba en escape sin haber buscado.
_MARCA_ROTA = re.compile(r"^\s*(?:</?tool_call>|tool_call|urnal)\s*$", re.MULTILINE | re.IGNORECASE)


def _json_de(texto: str):
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fin <= inicio:
        return None
    return _cargar_json(texto[inicio : fin + 1])


def _cargar_json(fragmento: str):
    """json.loads tolerante a comillas simples mal cerradas ('valor'} o "valor'})."""
    try:
        return json.loads(fragmento)
    except (json.JSONDecodeError, ValueError):
        pass
    reparado = re.sub(r"'(\s*[},:])", r'"\1', fragmento)
    reparado = re.sub(r"([{,:]\s*)'", r'\1"', reparado)
    try:
        return json.loads(reparado)
    except (json.JSONDecodeError, ValueError):
        return None


def _objetos_json(texto: str) -> list[tuple[int, int, object]]:
    """(inicio, fin, objeto) de cada JSON de nivel superior del texto, en orden.
    Recorre llaves balanceadas: separa varias llamadas seguidas, que el truco de
    "primer '{' y ultimo '}'" juntaria en un JSON invalido."""
    objetos, profundidad, inicio = [], 0, -1
    for i, c in enumerate(texto):
        if c == "{":
            if profundidad == 0:
                inicio = i
            profundidad += 1
        elif c == "}" and profundidad:
            profundidad -= 1
            if profundidad == 0:
                obj = _cargar_json(texto[inicio : i + 1])
                if obj is not None:
                    objetos.append((inicio, i + 1, obj))
    return objetos


def _como_llamada(obj) -> dict | None:
    if not isinstance(obj, dict):
        return None
    nombre = obj.get("name") or obj.get("tool")
    if not isinstance(nombre, str) or not nombre:
        return None
    args = obj.get("arguments", obj.get("args", {}))
    if isinstance(args, str):
        args = _cargar_json(args) or {}
    return {"name": nombre, "arguments": args if isinstance(args, dict) else {}}


def extraer_llamadas(texto: str) -> tuple[str, list[dict]]:
    """(texto libre, llamadas) de una salida del modelo.

    Llamadas en formato nativo (<tool_call>{"name", "arguments"}</tool_call>,
    una o varias) y, como respaldo, JSON sueltos con "name"/"arguments" o el
    JSON viejo {"tool", "args"} -- tambien con la marca danada "urnal" o con
    comillas simples mal cerradas (seccion 27). Cada llamada queda como
    {"name": str, "arguments": dict}. El texto libre es lo que el modelo
    escribio fuera de las llamadas: su razonamiento, o la respuesta final si no
    pidio ninguna herramienta."""
    texto = texto or ""
    llamadas = []
    if "<tool_call>" in texto:
        for bloque in _BLOQUE_TOOL_CALL.findall(texto):
            llamada = _como_llamada(_json_de(bloque))
            if llamada:
                llamadas.append(llamada)
        libre = _BLOQUE_TOOL_CALL.sub("", texto)
    else:
        libre, fin_anterior = [], 0
        for inicio, fin, obj in _objetos_json(texto):
            llamada = _como_llamada(obj)
            if llamada:
                llamadas.append(llamada)
                libre.append(texto[fin_anterior:inicio])
                fin_anterior = fin
        libre = "".join(libre) + texto[fin_anterior:]
    libre = _MARCA_ROTA.sub("", libre).strip()
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


# --- Alcance de la busqueda (hallazgo 5 de S10, docs seccion 27) -------------

def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", sin_tildes.lower())).strip()


# "segun el articulo 21 de la ley 820" -> "de la ley 820": se quita el numero de
# articulo que dio el usuario y se conserva el nombre de la norma.
_CITA_DEL_USUARIO = re.compile(
    r"(?:\b(?:segun|según|de acuerdo (?:con|a)|conforme (?:a|con)|por|como dice|dice)\s+)?"
    r"(?:\b(?:el|lo que dice el|lo que dice)\s+)?\bart(?:[ií]culos?|s?\.)\s*\d+[A-Za-z]?\s*[º°]?,?",
    re.IGNORECASE,
)


def limpiar_consulta_forzada(query: str) -> str:
    """Consulta para la busqueda que hace el codigo cuando el modelo no busco.

    Se buscaba con la pregunta tal cual. En la consulta EQUIVOCADO de la corrida
    del 2026-09-27 ("segun el articulo 21 de la ley 820 me pueden subir...") el
    numero "21" arrastro la busqueda a Ley 100, articulo 34 (pensiones) y la
    respuesta hablo de pensiones. El numero que dio el usuario puede estar mal
    (por eso se le pregunta al corpus), asi que no debe guiar la busqueda: se
    quita y queda el tema y el nombre de la norma."""
    limpia = re.sub(r"\s{2,}", " ", _CITA_DEL_USUARIO.sub(" ", query or "")).strip(" ,")
    return limpia or query


# Normas que el usuario puede nombrar: alias -> texto que aparece en la fuente.
_ALIAS_FUENTE = {
    "constitucion": "constitucion politica",
    "cst": "codigo sustantivo del trabajo",
    "codigo sustantivo del trabajo": "codigo sustantivo del trabajo",
    "codigo laboral": "codigo sustantivo del trabajo",
    "cgp": "codigo general del proceso",
    "codigo general del proceso": "codigo general del proceso",
    "cpaca": "cpaca",
    "ley 1755": "cpaca",
    "estatuto del consumidor": "estatuto del consumidor",
    "codigo de transito": "codigo nacional de transito",
    "codigo nacional de transito": "codigo nacional de transito",
    "habeas data": "habeas data financiero",
    "ley de arrendamiento": "arrendamiento de vivienda urbana",
    "ley 100": "ley 100",
}
# Otras normas que la gente nombra. Hoy no estan indexadas (sus archivos estan en
# data/corpus/normas pero no en NORMAS_EN_ALCANCE); si el equipo las indexa, su
# fuente aparece en el indice y dejan de marcarse como fuera del corpus.
_OTRAS_NORMAS = {
    "codigo penal": "el Codigo Penal",
    "codigo civil": "el Codigo Civil",
    "codigo de comercio": "el Codigo de Comercio",
    "codigo de policia": "el Codigo de Policia",
    "codigo de infancia": "el Codigo de Infancia y Adolescencia",
}
_LEY_O_DECRETO = re.compile(r"\b(ley|decreto)\s+(?:no\s+)?(\d+)\b")


def normas_mencionadas(texto: str, fuentes) -> tuple[list[str], list[str]]:
    """(fuentes del corpus que el texto nombra, normas nombradas que el corpus
    no tiene). Solo nombres explicitos ("Constitucion", "ley 820", "codigo
    penal"); un tema ("tutela") no cuenta como norma nombrada."""
    t = _normalizar(texto)
    fuentes = list(dict.fromkeys(fuentes or []))
    norm = {f: _normalizar(f) for f in fuentes}
    en_corpus, fuera = [], []
    for alias, clave in _ALIAS_FUENTE.items():
        if re.search(rf"\b{alias}\b", t):
            en_corpus += [f for f in fuentes if clave in norm[f]]
    for tipo, numero in _LEY_O_DECRETO.findall(t):
        propias = [f for f in fuentes if norm[f].startswith(f"{tipo} {numero} ")]
        if propias:
            en_corpus += propias
        elif fuentes and f"ley {numero}" not in _ALIAS_FUENTE:
            fuera.append(f"{tipo.capitalize()} {numero}")
    for clave, nombre in _OTRAS_NORMAS.items():
        if re.search(rf"\b{clave}\b", t):
            propias = [f for f in fuentes if clave in norm[f]]
            if propias:
                en_corpus += propias
            elif fuentes:
                fuera.append(nombre)
    return list(dict.fromkeys(en_corpus)), list(dict.fromkeys(fuera))


_PIDE_SENTENCIA = re.compile(r"\b(sentencia|jurisprudencia|fallo de la corte|radicado)\b")


def pide_sentencia(query: str) -> bool:
    """La pregunta pide una sentencia (numero, fecha o contenido). El corpus no
    tiene jurisprudencia: cualquier cosa que diga el modelo sobre ella seria de
    memoria (adversarial 9104: el tool use dijo que la sentencia "se encuentra
    derogada por la Ley 1437", sin ningun respaldo)."""
    return bool(_PIDE_SENTENCIA.search(_normalizar(query)))


_RECONOCE_LIMITE = re.compile(
    r"no (?:tengo|puedo|cuento|encontre|encuentro|aparece|esta)|relatoria|no (?:se|la|lo) (?:puede|pude|puedo) verificar"
)


def reconoce_limite(texto: str) -> bool:
    """La respuesta dice que no tiene o no puede verificar lo que se pide."""
    return RESPUESTA_SIN_CONTEXTO.lower() in (texto or "").lower() or bool(_RECONOCE_LIMITE.search(_normalizar(texto)))


NOTA_SENTENCIA = (
    "Nota del sistema: el corpus no tiene sentencias (jurisprudencia). No des numero, fecha ni "
    "contenido de ninguna sentencia: dile al usuario que no puedes verificarla y que la busque en la "
    "relatoria de la Corte Constitucional o en un consultorio juridico universitario."
)


def nota_de_alcance(consulta: str, resultados, fuentes) -> str:
    """Aviso que se agrega a la observacion cuando lo recuperado no es lo que se
    pidio: la norma nombrada no esta en el corpus, ninguno de los resultados es
    de la norma nombrada, o se pide una sentencia. Sin aviso, el modelo presenta
    lo que encontro como si fuera lo pedido (adversarial 9102: pregunta por el
    articulo de la Constitucion y se le respondio con articulos del Decreto 2591
    como si fueran la respuesta)."""
    notas = []
    en_corpus, fuera = normas_mencionadas(consulta, fuentes)
    if fuera:
        notas.append(f"Nota del sistema: {', '.join(fuera)} no esta(n) en el corpus verificado de Amparo. "
                     "No cites ni describas su contenido: dile al usuario que no lo tienes verificado y "
                     "responde solo con lo que si aparece en los resultados.")
    if en_corpus and resultados and not any(r.fuente in en_corpus for r in resultados):
        notas.append(f"Nota del sistema: ninguno de estos resultados es de {', '.join(en_corpus)}, la "
                     "norma que se nombra. No presentes otra norma como si fuera esa: si no encuentras lo "
                     "pedido en esa norma, dilo.")
    if pide_sentencia(consulta):
        notas.append(NOTA_SENTENCIA)
    return "\n\n".join(notas)


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
    observacion = formatear_observacion(resultados)
    fuentes = [m.get("fuente", "") for m in (getattr(store, "metadata", None) or []) if isinstance(m, dict)]
    nota = nota_de_alcance(consulta, resultados, fuentes)
    return (f"{observacion}\n\n{nota}" if nota else observacion), resultados


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
          herramientas en vez de responder, o le piden una sentencia y no dice que
          no puede verificarla (seccion 27) -> una correccion; si insiste, escape.
        Un saludo sin busqueda y sin citas pasa tal cual."""
        from tools.rag.agentico import citas_no_verificables, nota_de_correccion
        from tools.rag.prompt_template import RESPUESTA_ESCAPE_POR_CODIGO

        if RESPUESTA_SIN_CONTEXTO.lower() in respuesta.lower():
            return respuesta, {"escape_por_codigo": None, "citas_rechazadas": []}
        if traza and not vistos:
            return RESPUESTA_ESCAPE_POR_CODIGO, {"escape_por_codigo": "sin_contexto", "citas_rechazadas": []}
        rechazadas = citas_no_verificables(respuesta, vistos, query)
        meta = menciona_herramientas(respuesta)
        sentencia = pide_sentencia(query) and not reconoce_limite(respuesta)
        if not rechazadas and not meta and not sentencia:
            return respuesta, {"escape_por_codigo": None, "citas_rechazadas": []}
        nota = (nota_de_correccion(rechazadas) if rechazadas else
                "Tu respuesta describe herramientas en vez de responder al usuario." if meta else NOTA_SENTENCIA)
        corregida = generar(mensajes + [{"role": "user", "content": nota + " Responde ahora al usuario, "
                                          "en texto normal y sin pedir mas herramientas."}], None)
        libre, llamadas = extraer_llamadas(corregida)
        if (llamadas or citas_no_verificables(libre, vistos, query) or menciona_herramientas(libre) or not libre
                or (pide_sentencia(query) and not reconoce_limite(libre))):
            motivo = "sentencia_no_verificable" if sentencia and not rechazadas else "citas_no_verificables"
            return RESPUESTA_ESCAPE_POR_CODIGO, {"escape_por_codigo": motivo,
                                                 "citas_rechazadas": rechazadas}
        return libre, {"escape_por_codigo": None, "citas_rechazadas": rechazadas}

    for _ in range(max_llamadas):
        salida = generar(mensajes, [BUSCAR_NORMAS])
        libre, llamadas = extraer_llamadas(salida)
        if not llamadas:
            if not traza and not es_charla_trivial(query):
                # Red de seguridad: respondio sin buscar una pregunta juridica.
                # La consulta va sin el numero de articulo que dio el usuario (seccion 27).
                _ejecutar({"name": "buscar_normas", "arguments": {"consulta": limpiar_consulta_forzada(query)}},
                          por_codigo=True)
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


