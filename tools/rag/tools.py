"""Tool use: el modelo decide cuando buscar en el corpus (S10).

Patron agentic de function calling: en vez de recuperar SIEMPRE (RAG de una
pasada), se le describe al modelo una herramienta -- buscar_normas -- y el
modelo decide si la necesita. Si la necesita, responde con un JSON
{"tool": "buscar_normas", "args": {"consulta": "..."}}; nosotros lo parseamos,
ejecutamos la busqueda (el retrieval AVANZADO de S08: hybrid + rerank) y le
devolvemos los chunks como observacion para que redacte la respuesta final.

POR QUE una herramienta y no el RAG de una pasada (justificacion de diseño, ver
docs/m3_decisiones_rag.md):

1. El retrieval-as-tool deja que el modelo REFORMULE la consulta antes de buscar.
   La consulta del usuario en Amparo es coloquial y a veces ambigua ("me estan
   cobrando algo raro en el banco"); dejar que el modelo la convierta en una
   consulta de busqueda ("reporte negativo central de riesgo cobro no
   reconocido") es query transformation implicita, gratis.
2. El modelo puede DECIDIR no buscar cuando la pregunta no lo amerita (un saludo,
   una aclaracion sobre su propia respuesta anterior), ahorrando una recuperacion
   inutil. El RAG de una pasada busca siempre.
3. Conecta S08 con S10 sin agregar superficie nueva: la tool ES el retrieval
   avanzado, envuelto. No hay una segunda ruta de recuperacion que mantener.

Se expone UNA sola herramienta a proposito. Amparo no puede "actuar" sobre el
mundo (radicar una tutela, pagar una multa): su unica accion legitima es
consultar fuentes verificadas. Darle una calculadora o herramientas de dominio
sin un caso de uso real seria superficie sin justificacion -- justo lo que el
estandar del proyecto rechaza.

La generacion (el modelo) es stack pesado: se importa de forma perezosa y se
inyecta como parametro en los tests, para que el bucle se pruebe sin GPU.
"""
from __future__ import annotations

import json

from tools.rag import config
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

# El texto que el modelo ve como instruccion de sistema del bucle de tools. Se
# arma con el esquema serializado, igual que en el lab de S10.
SYSTEM_TOOLS = (
    "Eres Amparo, un asistente juridico de derecho colombiano. Tienes una "
    "herramienta disponible:\n"
    + json.dumps([TOOL_SCHEMA], ensure_ascii=False, indent=2)
    + "\n\nSi necesitas fundamentar en una norma, responde SOLO con un JSON: "
    '{"tool": "buscar_normas", "args": {"consulta": "<que buscar>"}}. '
    "Si ya puedes responder con fundamento (o la pregunta no requiere una norma), "
    "responde en texto normal, sin JSON. Nunca cites una norma que no haya "
    "aparecido en una observacion de la herramienta."
)


class ToolError(ValueError):
    """La llamada a herramienta no se pudo ejecutar (tool inexistente, args mal)."""


def extraer_tool_call(texto: str) -> dict | None:
    """Extrae un {"tool":..., "args":{...}} del texto del modelo, o None.

    Robusto a proposito (mismo espiritu que el lab de S10): busca el primer '{' y
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
    if not isinstance(pedido, dict) or "tool" not in pedido:
        return None
    return pedido


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
    """Despacha una llamada a herramienta validada y devuelve su observacion.

    Valida que la herramienta exista y que traiga los args que declara el
    esquema. La busqueda usa el retrieval AVANZADO (hybrid + rerank por defecto):
    es el punto de conectar S08 con S10 -- la tool no reimplementa la busqueda,
    invoca la que ya se construyo y midio.

    Se devuelve un string (la observacion) porque es lo que se le concatena al
    historial del modelo. Un error de validacion tambien se devuelve como string
    de observacion, no se lanza: asi el modelo lo lee ("no existe la herramienta
    X") y puede corregir en la siguiente vuelta, en vez de tumbar el bucle.
    """
    nombre = pedido.get("tool")
    if nombre != TOOL_SCHEMA["name"]:
        return f"error: no existe la herramienta {nombre!r}. La unica disponible es 'buscar_normas'."

    args = pedido.get("args") or {}
    consulta = args.get("consulta")
    if not isinstance(consulta, str) or not consulta.strip():
        return "error: buscar_normas requiere un arg 'consulta' de tipo texto no vacio."

    resultados = retrieve(
        consulta,
        store,
        top_k=top_k,
        use_hybrid=use_hybrid,
        use_rerank=use_rerank,
        bm25=bm25,
    )
    return formatear_observacion(resultados)


def responder_con_tools(
    query: str,
    store,
    *,
    max_llamadas: int = 3,
    use_hybrid: bool = True,
    use_rerank: bool = True,
    bm25=None,
    model_bundle=None,
    _generar=None,
) -> dict:
    """Bucle agentic: propone -> ejecuta -> observa -> responde.

    El modelo ve la pregunta y el esquema de la herramienta. Mientras pida la
    herramienta (emita un tool-call JSON valido), se ejecuta la busqueda y se le
    devuelve la observacion; cuando responde en texto plano, esa es la respuesta
    final. max_llamadas acota el bucle para que un modelo que insiste en pedir la
    herramienta no lo deje corriendo indefinidamente.

    _generar: funcion (system, user) -> str, inyectable para tests. Por defecto
    usa el generador real (Qwen, GPU) via import perezoso. Devuelve un dict con
    la respuesta y la traza de herramientas usadas -- esa traza es la evidencia
    de auditoria de que la respuesta se fundamento en el corpus y no de memoria.
    """
    generar = _generar if _generar is not None else _generar_por_defecto(model_bundle)

    historial = f"Pregunta del usuario: {query}"
    traza: list[dict] = []

    for _ in range(max_llamadas):
        salida = generar(SYSTEM_TOOLS, historial)
        pedido = extraer_tool_call(salida)
        if pedido is None:
            # El modelo respondio directo: fin del bucle.
            return {"query": query, "response": salida, "tool_calls": traza}

        observacion = ejecutar_tool(
            pedido, store, use_hybrid=use_hybrid, use_rerank=use_rerank, bm25=bm25
        )
        traza.append({"tool": pedido.get("tool"), "args": pedido.get("args", {}), "observacion": observacion})
        historial += (
            f"\n\nUsaste {pedido.get('tool')} con {pedido.get('args', {})} y obtuviste:\n"
            f"{observacion}\n\nAhora responde la pregunta del usuario fundamentandote en eso."
        )

    # Se agotaron las llamadas: se fuerza una respuesta final sin mas herramientas.
    respuesta = generar(
        SYSTEM_TOOLS, historial + "\n\nResponde ya con lo que tienes, sin pedir mas herramientas."
    )
    return {"query": query, "response": respuesta, "tool_calls": traza}


def _generar_por_defecto(model_bundle):
    """Envuelve el generador real (Qwen) como una funcion (system, user) -> str.

    Import perezoso de la generacion: stack pesado, vive en Colab. Se aisla aca
    para que el resto del modulo (esquema, dispatcher, parser) sea importable y
    testeable sin GPU.
    """
    from tools.evaluation import generation

    from tools.rag.pipeline import load_model

    model, tokenizer = model_bundle if model_bundle else load_model(use_lora=False)

    def generar(system: str, user: str) -> str:
        return generation.run_chat_generation(
            model, tokenizer, system, user, config.MAX_NEW_TOKENS_GENERATION
        )

    return generar
