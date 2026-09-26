"""RAG agentico (S10, Lab B): un mini-agente ReAct sobre el corpus de Amparo.

ReAct encadena pasos: el modelo escribe un PENSAMIENTO, elige una ACCION (una
herramienta), lee la OBSERVACION y repite hasta poder responder. Es la
diferencia con las otras dos rutas de M3:

  - RAG de una pasada (pipeline.answer_query): recupera SIEMPRE, una vez, y
    responde. Sirve para la pregunta simple ("¿cuanto tiene la EPS para
    responderme?").
  - Tool use (tools.responder_con_tools): el modelo decide SI busca y con que
    consulta, pero el flujo es buscar -> responder.
  - ReAct (este modulo): el modelo puede encadenar varias acciones distintas.
    Hace falta en la pregunta COMPUESTA, la que necesita una norma y ademas
    una operacion sobre ella. En Amparo el caso tipico es el laboral:
    "me despidieron sin justa causa despues de 3 años ganando 2.000.000,
    ¿cuanto me deben?" -> buscar el articulo 64 del CST (la regla de la
    indemnizacion) -> calcular con los datos del usuario -> responder citando
    la norma. El RAG de una pasada trae la norma pero deja la cuenta a la
    memoria del modelo, que es justo donde se equivoca.

Herramientas:
  - buscar_normas[consulta]: el mismo retrieval avanzado del tool use (hybrid +
    rerank). No se abre una segunda ruta de recuperacion.
  - calculadora[expresion]: aritmetica exacta. Se evalua con un parser de AST
    restringido (numeros y + - * / // % ** y parentesis), NO con eval(): la
    expresion la escribe el modelo, y eval() sobre texto generado es ejecutar
    codigo arbitrario.
  - Responder[respuesta final]: termina el bucle.

Por que se agrega una segunda herramienta cuando tools.py argumenta que Amparo
solo necesita una: esa decision es sobre ACCIONES EN EL MUNDO (radicar, pagar),
que Amparo no hace. La calculadora no actua sobre el mundo; es una herramienta
de razonamiento que evita que el modelo haga aritmetica "de memoria".

No todo necesita un agente. Cada paso es una generacion mas (latencia), y un
modelo que da vueltas puede empeorar una respuesta simple. Por eso esta ruta se
evalua sobre el mismo eval set que las demas (mismo contrato de salida,
pipeline.to_eval_record) y solo se justifica si las metricas mejoran.

La generacion es inyectable (_generar), asi que el bucle, el parser y las
herramientas se prueban sin GPU (tests/rag/test_agentico.py).
"""
from __future__ import annotations

import ast
import operator
import re

from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO
from tools.rag.tools import (
    TOOL_TOP_K,
    _generar_por_defecto,
    ejecutar_tool_con_resultados,
    resultado_para_evaluacion,
)

MAX_PASOS = 5

ACCIONES = ("buscar_normas", "calculadora", "Responder")

SYSTEM_REACT = (
    "Eres Amparo, un asistente juridico de derecho colombiano. Resuelve la "
    "pregunta razonando por pasos. En cada paso escribe EXACTAMENTE dos lineas:\n"
    "Pensamiento: <que necesitas averiguar o calcular>\n"
    "Accion: <una de estas>\n"
    "  buscar_normas[<consulta>]   -> busca articulos en el corpus de normas colombianas verificadas\n"
    "  calculadora[<expresion>]    -> calcula una expresion aritmetica (solo numeros y + - * / y parentesis)\n"
    "  Responder[<respuesta final>] -> termina con la respuesta para el usuario\n\n"
    "Reglas:\n"
    "- Toda afirmacion legal debe salir de una observacion de buscar_normas; "
    "cita la norma y el articulo tal como aparecen ahi. Nunca cites de memoria.\n"
    "- Si hay que hacer una cuenta (dias, salarios, porcentajes), usa calculadora; "
    "no la hagas de cabeza.\n"
    "- Si buscar_normas no encuentra normas que respalden la respuesta, termina con: "
    f'Responder[{RESPUESTA_SIN_CONTEXTO}.]\n'
    "- Usa lenguaje comprensible para alguien sin formacion juridica."
)

# Accion[argumento]. Para Responder el argumento puede tener varias lineas y
# corchetes internos (una cita "[1]"), asi que se toma hasta el ULTIMO ']'.
_PATRON_ACCION = re.compile(r"(buscar_normas|calculadora|Responder)\s*\[", re.IGNORECASE)
_PATRON_PENSAMIENTO = re.compile(r"Pensamiento:\s*(.*)", re.IGNORECASE)


def parsear_paso(salida: str) -> tuple[str, tuple[str, str] | None]:
    """Extrae (pensamiento, (accion, argumento)) de una salida del modelo.

    Toma la PRIMERA accion que aparece: un modelo pequeño a veces sigue
    escribiendo pasos inventados (con observaciones que el mismo se imagina)
    despues de la accion; esos no se ejecutaron y no deben contar.

    Devuelve accion None si no hay una accion con formato valido. El bucle lo
    trata como respuesta directa: degradar, no romper.
    """
    m_pens = _PATRON_PENSAMIENTO.search(salida or "")
    pensamiento = m_pens.group(1).strip() if m_pens else ""

    m = _PATRON_ACCION.search(salida or "")
    if not m:
        return pensamiento, None
    nombre = next(a for a in ACCIONES if a.lower() == m.group(1).lower())
    resto = salida[m.end():]

    if nombre == "Responder":
        fin = resto.rfind("]")
        argumento = resto[:fin] if fin != -1 else resto
    else:
        # Las herramientas llevan un argumento de una linea: hasta el primer ']'.
        fin = resto.find("]")
        if fin == -1:
            return pensamiento, None
        argumento = resto[:fin]
    return pensamiento, (nombre, argumento.strip())


# --- Calculadora segura -------------------------------------------------------

_OPERADORES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARIOS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _evaluar_nodo(nodo):
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)) and not isinstance(nodo.value, bool):
        return nodo.value
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in _OPERADORES:
        izq, der = _evaluar_nodo(nodo.left), _evaluar_nodo(nodo.right)
        if isinstance(nodo.op, ast.Pow) and abs(der) > 100:
            raise ValueError("exponente demasiado grande")
        return _OPERADORES[type(nodo.op)](izq, der)
    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in _UNARIOS:
        return _UNARIOS[type(nodo.op)](_evaluar_nodo(nodo.operand))
    raise ValueError("solo se permiten numeros y operadores aritmeticos")


def calculadora(expresion: str) -> str:
    """Evalua una expresion aritmetica y devuelve el resultado como texto.

    Acepta los formatos que escribe un modelo al hablar de pesos colombianos:
    separador de miles con punto ("2.000.000") y "x" como multiplicacion. Un
    error se devuelve como texto ("error: ..."), igual que en el dispatcher de
    tools.py: el modelo lo lee como observacion y puede corregir.
    """
    texto = (expresion or "").strip().replace("$", "").replace(" ", "")
    texto = texto.replace("x", "*").replace("×", "*").replace("÷", "/")
    # "2.000.000" (miles con punto) -> 2000000; "1.5" se deja como decimal.
    texto = re.sub(r"\d{1,3}(?:\.\d{3})+(?!\d)", lambda m: m.group(0).replace(".", ""), texto)
    texto = texto.replace(",", ".")
    if not texto:
        return "error: la expresion esta vacia."
    try:
        valor = _evaluar_nodo(ast.parse(texto, mode="eval").body)
    except ZeroDivisionError:
        return "error: division por cero."
    except (SyntaxError, ValueError, TypeError) as e:
        return f"error: expresion invalida ({e})."
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    if isinstance(valor, float):
        valor = round(valor, 4)
    return str(valor)


# --- Bucle ReAct -------------------------------------------------------------

def agente_react(
    query: str,
    store,
    *,
    max_pasos: int = MAX_PASOS,
    use_hybrid: bool = True,
    use_rerank: bool = True,
    use_lora: bool = False,
    top_k: int = TOOL_TOP_K,
    bm25=None,
    model_bundle=None,
    _generar=None,
) -> dict:
    """Bucle ReAct: pensamiento -> accion -> observacion, hasta Responder.

    Devuelve el mismo contrato que pipeline.answer_query (para que
    to_eval_record lo lleve al formato RAGAS) mas `traza`: una fila por paso con
    pensamiento, accion, argumento y observacion. La traza es la evidencia de
    auditoria (y lo que se registra en W&B): si una respuesta sale mal, dice en
    que paso se torcio.

    `contexts` son todos los chunks que el agente vio en sus busquedas: es
    contra eso que RAGAS mide si la respuesta se apoyo en el contexto.

    Si se agotan los pasos sin Responder, se pide una respuesta final forzada; si
    tampoco llega en formato, se devuelve la frase de la valvula de escape: es
    preferible admitir que no se pudo resolver que improvisar.
    """
    generar = _generar if _generar is not None else _generar_por_defecto(model_bundle, use_lora)

    historial = f"Pregunta: {query}"
    traza: list[dict] = []
    vistos: list = []

    def _salida(respuesta: str) -> dict:
        return resultado_para_evaluacion(
            query, respuesta, vistos, sistema="react", use_lora=use_lora,
            use_hybrid=use_hybrid, use_rerank=use_rerank, top_k=top_k, traza=traza,
        )

    for paso in range(1, max_pasos + 1):
        salida = generar(SYSTEM_REACT, historial)
        pensamiento, accion = parsear_paso(salida)

        if accion is None:
            # Sin accion con formato: el modelo contesto en prosa. Se toma como
            # respuesta directa, igual que el tool use ante un JSON invalido.
            traza.append({"paso": paso, "pensamiento": pensamiento, "accion": "respuesta_directa",
                          "argumento": "", "observacion": ""})
            return _salida(salida.strip())

        nombre, argumento = accion
        if nombre == "Responder":
            traza.append({"paso": paso, "pensamiento": pensamiento, "accion": "Responder",
                          "argumento": argumento, "observacion": ""})
            return _salida(argumento)

        if nombre == "buscar_normas":
            observacion, resultados = ejecutar_tool_con_resultados(
                {"tool": "buscar_normas", "args": {"consulta": argumento}},
                store, top_k=top_k, use_hybrid=use_hybrid, use_rerank=use_rerank, bm25=bm25,
            )
            vistos.extend(resultados)
        else:
            observacion = calculadora(argumento)

        traza.append({"paso": paso, "pensamiento": pensamiento, "accion": nombre,
                      "argumento": argumento, "observacion": observacion})
        historial += (
            f"\nPensamiento: {pensamiento}\nAccion: {nombre}[{argumento}]\n"
            f"Observacion: {observacion}"
        )

    # Pasos agotados: una ultima generacion que solo puede responder.
    salida = generar(SYSTEM_REACT, historial + "\nYa no puedes usar herramientas. Accion: Responder[...]")
    pensamiento, accion = parsear_paso(salida)
    if accion and accion[0] == "Responder" and accion[1]:
        respuesta = accion[1]
    else:
        respuesta = f"{RESPUESTA_SIN_CONTEXTO}."
    traza.append({"paso": max_pasos + 1, "pensamiento": pensamiento, "accion": "Responder (forzado)",
                  "argumento": respuesta, "observacion": ""})
    return _salida(respuesta)
