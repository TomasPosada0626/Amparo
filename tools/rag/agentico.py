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
    una operacion sobre ella. Dos casos tipicos de Amparo:
      * Arriendo: "pago 1.200.000 y el IPC del año pasado fue 5,2 %, ¿hasta
        cuanto me pueden subir?" -> buscar el articulo 20 de la Ley 820 de
        2003 (tope: 100 % del IPC) -> calcular -> responder citando la norma.
      * Plazos: "radique un derecho de peticion el 1 de septiembre, ¿cuando me
        deben responder y si no, que hago?" -> buscar el termino (CPACA,
        articulo 14) -> contar los dias habiles -> buscar la tutela -> responder.
    El RAG de una pasada trae la norma pero deja la cuenta a la memoria del
    modelo, que es justo donde se equivoca.

Herramientas:
  - buscar_normas[consulta]: el mismo retrieval avanzado del tool use (hybrid +
    rerank). No se abre una segunda ruta de recuperacion.
  - calculadora[expresion]: aritmetica exacta. Se evalua con un parser de AST
    restringido (numeros y + - * / // % ** y parentesis), NO con eval(): la
    expresion la escribe el modelo, y eval() sobre texto generado es ejecutar
    codigo arbitrario.
  - leer_articulo[norma, numero]: lee un articulo EXACTO del corpus por su
    numero, sin busqueda semantica. Sirve cuando el usuario menciona un articulo
    ("segun el articulo 20 de la Ley 820...") o cuando una observacion remite a
    otro ("en los terminos del articulo 13"). Si el usuario se equivoco de
    articulo, el agente lo lee, ve que no trata lo que pregunta y se lo dice, en
    vez de fundamentar en el numero que le dieron. Si el articulo no esta en el
    corpus, la observacion lo dice: tampoco se inventa.
  - calcular_plazo[fecha, n, habiles|calendario]: fecha de vencimiento de un
    termino, contando desde el dia siguiente y, en dias habiles, sin sabados,
    domingos ni festivos de Colombia (libreria `holidays`). Contar dias habiles
    con festivos trasladados (Ley Emiliani) es otra cuenta en la que un modelo
    de 7B falla. El NUMERO de dias y si son habiles lo dice la norma: la
    herramienta solo cuenta.
  - Responder[respuesta final]: termina el bucle, si pasa la verificacion de
    citas (abajo).

Verificacion de citas (el principio de Amparo: no inventar normas): antes de
aceptar un Responder, se extraen los articulos que cita la respuesta y se
comparan con los que el agente vio de verdad (los `articulos_incluidos` de los
chunks de sus busquedas, mas los que menciono el propio usuario). Si cita un
articulo que no vio, la respuesta NO se acepta: se le devuelve como
observacion y tiene que corregir. Si al final sigue citando algo que no vio, se
responde con la valvula de escape. Es un control programatico, no una
instruccion del prompt que el modelo puede ignorar.

Por que se agregan herramientas cuando tools.py argumenta que Amparo solo
necesita una: esa decision es sobre ACCIONES EN EL MUNDO (radicar, pagar), que
Amparo no hace. La calculadora y calcular_plazo no actuan sobre el mundo; son
herramientas de razonamiento que evitan que el modelo haga cuentas "de memoria".
Ninguna contiene reglas legales: la regla sale siempre del corpus.

No todo necesita un agente. Cada paso es una generacion mas (latencia), y un
modelo que da vueltas puede empeorar una respuesta simple. Por eso esta ruta se
evalua sobre el mismo eval set que las demas (mismo contrato de salida,
pipeline.to_eval_record) y solo se justifica si las metricas mejoran.

La generacion es inyectable (_generar), asi que el bucle, el parser y las
herramientas se prueban sin GPU (tests/rag/test_agentico.py).
"""
from __future__ import annotations

import ast
import datetime as dt
import operator
import re
import unicodedata

from tools.rag.chunk import normalizar_numero
from tools.rag.embed_store import metadata_to_result
from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO
from tools.rag.tools import (
    TOOL_TOP_K,
    _generar_por_defecto,
    ejecutar_tool_con_resultados,
    formatear_observacion,
    resultado_para_evaluacion,
)

MAX_PASOS = 5

ACCIONES = ("buscar_normas", "leer_articulo", "calculadora", "calcular_plazo", "Responder")

SYSTEM_REACT = (
    "Eres Amparo, un asistente juridico de derecho colombiano. Resuelve la "
    "pregunta razonando por pasos. En cada paso escribe EXACTAMENTE dos lineas:\n"
    "Pensamiento: <que necesitas averiguar o calcular>\n"
    "Accion: <una de estas>\n"
    "  buscar_normas[<consulta>]   -> busca articulos en el corpus de normas colombianas verificadas\n"
    "  leer_articulo[<norma>, <numero>] -> lee un articulo exacto (ej. leer_articulo[Ley 820 de 2003, 20])\n"
    "  calculadora[<expresion>]    -> calcula una expresion aritmetica: numeros sin separador de miles y con punto decimal, + - * / y parentesis (ej. 1200000 * 1.052)\n"
    "  calcular_plazo[<AAAA-MM-DD>, <n>, <habiles|calendario>] -> fecha en que vence un termino de n dias contado desde el dia siguiente\n"
    "  Responder[<respuesta final>] -> termina con la respuesta para el usuario\n\n"
    "Reglas:\n"
    "- Toda afirmacion legal debe salir de una observacion de buscar_normas; "
    "cita la norma y el articulo tal como aparecen ahi. Nunca cites de memoria.\n"
    "- Si hay que hacer una cuenta (valores, porcentajes), usa calculadora; si hay "
    "que saber cuando vence un plazo, usa calcular_plazo con el numero de dias y el "
    "tipo que diga la norma. No hagas cuentas de cabeza.\n"
    "- Solo puedes citar articulos que aparecieron en tus observaciones: una cita "
    "que no viste sera rechazada.\n"
    "- Si el usuario menciona un articulo concreto, leelo con leer_articulo y "
    "comprueba que trate lo que pregunta. Si no lo trata o no existe, diselo con "
    "claridad y busca el tema con buscar_normas.\n"
    "- Si buscar_normas no encuentra normas que respalden la respuesta, termina con: "
    f'Responder[{RESPUESTA_SIN_CONTEXTO}.]\n'
    "- Usa lenguaje comprensible para alguien sin formacion juridica."
)

# Accion[argumento]. Para Responder el argumento puede tener varias lineas y
# corchetes internos (una cita "[1]"), asi que se toma hasta el ULTIMO ']'.
_PATRON_ACCION = re.compile(
    r"(buscar_normas|leer_articulo|calculadora|calcular_plazo|Responder)\s*\[", re.IGNORECASE
)
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

    Convencion (la misma que pide el prompt): numeros sin separador de miles y
    punto decimal ("1200000 * 1.052"). Por robustez tambien acepta el formato de
    pesos con varios grupos de miles ("2.000.000", que no es ambiguo) y "x" como
    multiplicacion. Un solo punto ("1.052") siempre es DECIMAL: es el caso del
    IPC, y leerlo como miles daria un resultado 1000 veces mayor sin avisar.
    Un error se devuelve como texto ("error: ..."), igual que en el dispatcher
    de tools.py: el modelo lo lee como observacion y puede corregir.
    """
    texto = (expresion or "").strip().replace("$", "").replace(" ", "")
    texto = texto.replace("x", "*").replace("×", "*").replace("÷", "/")
    # "2.000.000" (dos o mas grupos de miles) -> 2000000. "1.052" se deja: decimal.
    texto = re.sub(r"(?<![\d.])\d{1,3}(?:\.\d{3}){2,}(?![\d.])",
                   lambda m: m.group(0).replace(".", ""), texto)
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


# --- Leer un articulo exacto -------------------------------------------------

# Siglas y nombres cortos con que la gente se refiere a las normas del corpus.
# Se expanden antes de comparar con la `fuente` de cada chunk.
ALIAS_NORMAS = {
    "cst": "codigo sustantivo del trabajo",
    "cgp": "codigo general del proceso",
    "cpaca": "cpaca",
    "constitucion nacional": "constitucion politica",
    "constitucion": "constitucion politica",
    "estatuto del consumidor": "estatuto del consumidor",
    "codigo de transito": "codigo nacional de transito",
    "ley de arrendamiento": "arrendamiento de vivienda urbana",
    "habeas data": "habeas data financiero",
}
_PALABRAS_VACIAS = {"de", "del", "la", "el", "los", "las", "y", "ley", "decreto", "codigo", "numero", "no"}
MAX_CHUNKS_POR_ARTICULO = 3


def _normalizar_texto(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", sin_tildes.lower())


def _puntaje_norma(consulta: str, fuente: str) -> int:
    """Cuanto se parece lo que escribio el modelo a la `fuente` de un chunk.

    Los numeros pesan doble ("820", "1437": identifican la norma casi solos);
    las palabras suman de a uno. Las siglas se expanden con ALIAS_NORMAS."""
    q = _normalizar_texto(consulta)
    for alias, expansion in ALIAS_NORMAS.items():
        q = re.sub(rf"\b{alias}\b", expansion, q)
    f = _normalizar_texto(fuente)
    nums_q, nums_f = set(re.findall(r"\d+", q)), set(re.findall(r"\d+", f))
    pal_q = {w for w in q.split() if not w.isdigit() and w not in _PALABRAS_VACIAS and len(w) > 2}
    pal_f = {w for w in f.split() if not w.isdigit()}
    return 2 * len(nums_q & nums_f) + len(pal_q & pal_f)


def leer_articulo(argumento: str, store) -> tuple[str, list]:
    """Lee un articulo exacto del corpus: (observacion, resultados).

    argumento: "<norma>, <numero>" (p. ej. "Ley 820 de 2003, 20" o "CST, 64").
    Recorre la metadata del indice (no hay busqueda semantica: es una lectura
    por numero) y devuelve los chunks de esa norma que contienen ese articulo,
    con su cita, en el mismo formato que buscar_normas. Los resultados entran a
    los `contexts` y a la verificacion de citas igual que los de una busqueda.

    Si la norma no se reconoce o el articulo no esta en el corpus, lo dice en la
    observacion (sin resultados): el agente debe decirle al usuario que ese
    articulo no esta o no trata el tema, no suponer su contenido.
    """
    if "," not in (argumento or ""):
        return "error: usa leer_articulo[<norma>, <numero>], p. ej. leer_articulo[Ley 820 de 2003, 20].", []
    norma, numero = (p.strip() for p in argumento.rsplit(",", 1))
    numero = re.sub(r"(?i)^art(?:[ií]culo|\.)?\s*", "", numero).strip(" º°.")
    if not re.fullmatch(r"\d+[A-Za-z]?", numero):
        return f"error: {numero!r} no es un numero de articulo.", []
    numero = normalizar_numero(numero).upper()

    metadata = list(getattr(store, "metadata", []) or [])
    fuentes = list(dict.fromkeys(m["fuente"] for m in metadata))
    if not fuentes:
        return "error: el indice no tiene metadata cargada.", []

    puntajes = {f: _puntaje_norma(norma, f) for f in fuentes}
    mejor = max(puntajes.values())
    candidatas = [f for f, p in puntajes.items() if p == mejor]
    if mejor == 0:
        return (f"No reconozco la norma {norma!r} en el corpus. Normas disponibles: "
                f"{'; '.join(fuentes)}."), []
    if len(candidatas) > 1:
        return (f"La norma {norma!r} es ambigua; puede ser: {'; '.join(candidatas)}. "
                "Escribela con su numero y año."), []
    fuente = candidatas[0]

    encontrados = [
        m for m in metadata
        if m["fuente"] == fuente
        and numero in {normalizar_numero(a).upper() for a in (m.get("articulos_incluidos") or [])}
    ][:MAX_CHUNKS_POR_ARTICULO]
    if not encontrados:
        return (f"El articulo {numero} de {fuente} no esta en el corpus. Si el usuario lo "
                "menciono, puede estar equivocado de numero: diselo y busca el tema con "
                "buscar_normas."), []

    resultados = []
    for m in encontrados:
        r = metadata_to_result(m, score=1.0)
        # Lectura exacta, no vino por la via densa: sin coseno de e5 que auditar.
        r.dense_score = None
        resultados.append(r)
    return f"Lectura exacta de {fuente}, articulo {numero}:\n\n" + formatear_observacion(resultados), resultados


# --- Calcular plazos ----------------------------------------------------------

_FORMATOS_FECHA = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")


def _parsear_fecha(texto: str) -> dt.date | None:
    for formato in _FORMATOS_FECHA:
        try:
            return dt.datetime.strptime(texto.strip(), formato).date()
        except ValueError:
            continue
    return None


def _festivos_colombia(años):
    """Festivos de Colombia (incluye los trasladados a lunes por la Ley Emiliani).

    Import perezoso: `holidays` es liviano (Python puro) pero solo lo necesita
    esta herramienta."""
    import holidays

    return holidays.country_holidays("CO", years=años)


def calcular_plazo(argumento: str) -> str:
    """Calcula la fecha en que vence un termino de n dias.

    argumento: "AAAA-MM-DD, n, habiles|calendario" (tambien acepta DD/MM/AAAA).
    El conteo empieza el dia SIGUIENTE a la fecha dada (la regla general de los
    terminos: "dentro de los quince dias siguientes a su recepcion"). En dias
    habiles se saltan sabados, domingos y festivos de Colombia.

    La herramienta no sabe CUANTOS dias da la ley ni si son habiles: eso lo dice
    la norma que el agente encontro con buscar_normas. Errores -> "error: ...".
    """
    partes = [p.strip() for p in (argumento or "").split(",")]
    if len(partes) != 3:
        return "error: usa calcular_plazo[AAAA-MM-DD, n, habiles|calendario]."
    fecha = _parsear_fecha(partes[0])
    if fecha is None:
        return f"error: fecha invalida {partes[0]!r}; usa AAAA-MM-DD."
    try:
        n = int(partes[1])
    except ValueError:
        return f"error: el numero de dias {partes[1]!r} no es un entero."
    if not 1 <= n <= 3650:
        return "error: el numero de dias debe estar entre 1 y 3650."
    tipo = partes[2].lower().replace("á", "a")
    if tipo not in ("habiles", "calendario"):
        return "error: el tipo debe ser 'habiles' o 'calendario'."

    if tipo == "calendario":
        vence = fecha + dt.timedelta(days=n)
        return (f"Contando {n} dias calendario desde el dia siguiente a {fecha.isoformat()}, "
                f"el plazo vence el {vence.isoformat()}.")

    festivos = _festivos_colombia(range(fecha.year, fecha.year + n // 200 + 2))
    dia, contados, saltados = fecha, 0, []
    while contados < n:
        dia += dt.timedelta(days=1)
        if dia.weekday() >= 5:
            continue
        if dia in festivos:
            saltados.append(f"{dia.isoformat()} ({festivos.get(dia)})")
            continue
        contados += 1
    nota = f" Festivos excluidos: {'; '.join(saltados)}." if saltados else ""
    return (f"Contando {n} dias habiles desde el dia siguiente a {fecha.isoformat()} "
            f"(sin sabados, domingos ni festivos de Colombia), el plazo vence el "
            f"{dia.isoformat()}.{nota}")


# --- Verificacion de citas ---------------------------------------------------

# "articulo 20", "artículos 13 y 14", "art. 6º", "arts. 5, 6 y 7".
_PATRON_CITA = re.compile(
    r"\bart(?:[ií]culos?|s?\.)\s*((?:\d+[A-Za-z]?\s*[º°]?\s*(?:,|\by\b|\be\b)?\s*)+)",
    re.IGNORECASE,
)


def articulos_citados(texto: str) -> set[str]:
    """Numeros de articulo que aparecen citados en un texto, normalizados como
    los guarda el chunker ("6º" -> "6", "14a" -> "14A")."""
    numeros = set()
    for grupo in _PATRON_CITA.findall(texto or ""):
        for numero in re.findall(r"\d+[A-Za-z]?", grupo):
            numeros.add(normalizar_numero(numero).upper())
    return numeros


def citas_no_respaldadas(respuesta: str, resultados, query: str = "") -> list[str]:
    """Articulos que cita la respuesta y que el agente NO vio.

    "Vio" = los `articulos_incluidos` de los chunks que devolvieron sus
    busquedas, mas los que menciono el propio usuario en la pregunta (citar lo
    que el usuario dijo no es inventar; la respuesta puede estar aclarando que
    ese articulo no aplica).

    Limite conocido: compara numeros de articulo, no el par (norma, articulo).
    Detecta el articulo inventado, no el articulo real atribuido a otra ley.
    """
    vistos = {normalizar_numero(a).upper() for r in resultados for a in r.articulos_incluidos}
    vistos |= articulos_citados(query)
    return sorted(articulos_citados(respuesta) - vistos, key=lambda x: (len(x), x))


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

    Un Responder que cita articulos que el agente no vio se rechaza y vuelve como
    observacion (verificacion de citas); el rechazo consume un paso.

    Si se agotan los pasos sin Responder, se pide una respuesta final forzada; si
    tampoco llega en formato, o sigue citando algo que no vio, se devuelve la
    frase de la valvula de escape: es preferible admitir que no se pudo resolver
    que improvisar.
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
            no_vistas = citas_no_respaldadas(argumento, vistos, query)
            if not no_vistas:
                traza.append({"paso": paso, "pensamiento": pensamiento, "accion": "Responder",
                              "argumento": argumento, "observacion": ""})
                return _salida(argumento)
            # Cita algo que no vio: no se acepta. Se le devuelve como observacion
            # y el bucle sigue (consume un paso).
            observacion = (
                f"Verificacion de citas: tu respuesta cita el/los articulo(s) "
                f"{', '.join(no_vistas)}, que no aparecen en ninguna de tus observaciones. "
                "Buscalos con buscar_normas o responde sin citarlos."
            )
            traza.append({"paso": paso, "pensamiento": pensamiento, "accion": "Responder (rechazado)",
                          "argumento": argumento, "observacion": observacion})
            historial += f"\nAccion: Responder[{argumento}]\nObservacion: {observacion}"
            continue

        if nombre == "buscar_normas":
            observacion, resultados = ejecutar_tool_con_resultados(
                {"tool": "buscar_normas", "args": {"consulta": argumento}},
                store, top_k=top_k, use_hybrid=use_hybrid, use_rerank=use_rerank, bm25=bm25,
            )
            vistos.extend(resultados)
        elif nombre == "leer_articulo":
            observacion, resultados = leer_articulo(argumento, store)
            vistos.extend(resultados)
        elif nombre == "calcular_plazo":
            observacion = calcular_plazo(argumento)
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
    if (accion and accion[0] == "Responder" and accion[1]
            and not citas_no_respaldadas(accion[1], vistos, query)):
        respuesta = accion[1]
    else:
        # Sin respuesta en formato, o sigue citando algo que no vio.
        respuesta = f"{RESPUESTA_SIN_CONTEXTO}."
    traza.append({"paso": max_pasos + 1, "pensamiento": pensamiento, "accion": "Responder (forzado)",
                  "argumento": respuesta, "observacion": ""})
    return _salida(respuesta)
