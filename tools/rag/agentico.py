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
from tools.rag.prompt_template import SYSTEM_PROMPT_M1, RESPUESTA_ESCAPE_POR_CODIGO, RESPUESTA_SIN_CONTEXTO
from tools.rag.tools import (
    BUSCAR_NORMAS,
    TOOL_TOP_K,
    _generar_mensajes_por_defecto,
    ejecutar_tool_con_resultados,
    NOTA_SENTENCIA,
    _normalizar,
    es_charla_trivial,
    extraer_llamadas,
    limpiar_consulta_forzada,
    pide_sentencia,
    reconoce_limite,
    formatear_observacion,
    herramienta,
    menciona_herramientas,
    resultado_para_evaluacion,
    turno_con_llamada,
    turno_resultado,
)

MAX_PASOS = 5

ACCIONES = ("buscar_normas", "leer_articulo", "calculadora", "calcular_plazo", "Responder")

SYSTEM_REACT = (
    # Igual que SYSTEM_TOOLS: el rol es el de M1 y las reglas del bucle van
    # despues, para que la diferencia entre rutas sea la ruta y no el prompt.
    f"{SYSTEM_PROMPT_M1}\n\n"
    "Resuelves la pregunta por pasos: piensas que necesitas, "
    "usas una herramienta, lees su resultado y repites hasta poder responder. "
    "Antes de cada herramienta puedes escribir en una linea que vas a buscar o "
    "calcular.\n\n"
    "Reglas:\n"
    "- Si la pregunta es juridica, BUSCA con buscar_normas antes de responder; no "
    "respondas de memoria. Solo un saludo o charla sin contenido juridico se "
    "responde sin buscar.\n"
    "- Busca todo lo que necesites para responder COMPLETO: la regla, y si la "
    "pregunta lo pide, que hacer si no se cumple (por ejemplo, la tutela).\n"
    "- Si el usuario menciona un articulo, leelo con leer_articulo. Si no trata lo "
    "que pregunta, busca el tema con buscar_normas y en tu respuesta dile que ese "
    "articulo no aplica, cual si aplica y responde su pregunta.\n"
    "- Cuentas de valores o porcentajes: calculadora. Cuando vence un plazo: "
    "calcular_plazo, con el numero de dias y el tipo que diga la norma. No hagas "
    "cuentas de cabeza.\n"
    "- Primero la norma, despues la cuenta: no uses calculadora ni calcular_plazo "
    "antes de encontrar la norma que da el dato. No inventes fechas ni numeros de "
    "dias: si el usuario no dio una fecha, explica el plazo en dias.\n"
    "- Si la pregunta trae cifras (valores, porcentajes) o una fecha, tu respuesta "
    "debe dar el resultado de la cuenta.\n"
    "- El corpus no tiene sentencias: nunca des numero, fecha ni contenido de una "
    "sentencia. Si un resultado dice que la norma que nombra el usuario no esta, "
    "diselo en vez de presentar otra norma como si fuera esa.\n"
    "- Toda afirmacion legal debe salir de un resultado de herramienta; cita la norma "
    "y el articulo tal como aparecen ahi. Una cita que no viste sera rechazada.\n"
    "- Cuando tengas todo, RESPONDE AL USUARIO en texto normal: la respuesta "
    "misma, no instrucciones sobre que herramienta usar.\n"
    "- Si las busquedas no encuentran normas que respalden la respuesta, responde: "
    f'"{RESPUESTA_SIN_CONTEXTO}."\n'
    "- Usa lenguaje comprensible para alguien sin formacion juridica."
)

# Accion[argumento]. Para Responder el argumento puede tener varias lineas y
# corchetes internos (una cita "[1]"), asi que se toma hasta el ULTIMO ']'.
# Formato de texto de la primera version ("Accion: x[...]"). Ya no se le pide al
# modelo (ahora las herramientas van en formato nativo), pero se sigue aceptando
# como respaldo, incluidas variantes que el modelo escribio en la corrida real
# ("Responde[...]", "Respuesta[...]").
_PATRON_ACCION = re.compile(
    r"(buscar_normas|leer_articulo|calculadora|calcular_plazo|Responder|Responde|Respuesta)\s*\[",
    re.IGNORECASE,
)
_ALIAS_RESPONDER = {"responder", "responde", "respuesta"}
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
    crudo = m.group(1).lower()
    nombre = "Responder" if crudo in _ALIAS_RESPONDER else next(a for a in ACCIONES if a.lower() == crudo)
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


# --- Cuentas con respaldo (hallazgo 5 de S10, docs seccion 27) ---------------
#
# En la corrida del 2026-09-27 el agente uso calcular_plazo ANTES de buscar, con
# 30 dias y una fecha que el usuario nunca dio (2023-04-01), y respondio "30 dias
# habiles" cuando la norma da quince. La herramienta cuenta bien; el error es el
# dato que le entra. Por eso el codigo no deja contar un plazo que ninguna norma
# vista respalde, ni desde una fecha que no dijo el usuario.

_UNIDADES = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
             "once", "doce", "trece", "catorce", "quince", "dieciseis", "diecisiete", "dieciocho",
             "diecinueve", "veinte", "veintiuno", "veintidos", "veintitres", "veinticuatro",
             "veinticinco", "veintiseis", "veintisiete", "veintiocho", "veintinueve"]
_DECENAS = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
_CENTENAS = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos",
             6: "seiscientos", 7: "setecientos", 8: "ochocientos", 9: "novecientos"}


def numero_en_letras(n: int) -> str:
    """1..999 en letras, sin tildes, como lo escriben las normas ("quince (15) dias")."""
    if not 1 <= n <= 999:
        return str(n)
    if n == 100:
        return "cien"
    c, resto = divmod(n, 100)
    partes = [_CENTENAS[c]] if c else []
    if resto:
        if resto < 30:
            partes.append(_UNIDADES[resto])
        else:
            d, u = divmod(resto, 10)
            partes.append(_DECENAS[d] + (f" y {_UNIDADES[u]}" if u else ""))
    return " ".join(partes)


def plazo_respaldado(dias: int, textos) -> bool:
    """¿Algun texto recuperado da un termino de `dias` dias? Acepta "quince (15)
    dias", "15 dias", "(15)" y "quince dias" (tambien "... dias habiles")."""
    letras = numero_en_letras(dias)
    patron = re.compile(
        rf"\(\s*{dias}\s*\)|\b{dias}\s+dias\b|\b{letras}\s+(?:\(\s*{dias}\s*\)\s+)?dias\b"
    )
    return any(patron.search(_normalizar(t)) for t in textos)


_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
          "octubre", "noviembre", "diciembre"]
_FECHA_RELATIVA = re.compile(r"\b(hoy|ayer|antier|anteayer|manana|hace \w+)\b")


def fecha_en_consulta(fecha: dt.date, query: str) -> bool:
    """¿La fecha sale de lo que dijo el usuario? "1 de septiembre", "01/09/2026",
    "2026-09-01", o una referencia relativa ("ayer", "hace 20 dias") que el modelo
    tuvo que convertir."""
    q = _normalizar(query)
    if _FECHA_RELATIVA.search(q):
        return True
    dia, mes = fecha.day, _MESES[fecha.month - 1]
    if re.search(rf"\b0?{dia} de {mes}\b", q) or (dia == 1 and re.search(rf"\bprimero de {mes}\b", q)):
        return True
    crudo = (query or "").lower()
    return any(f in crudo for f in (fecha.isoformat(), f"{dia}/{fecha.month}", f"{dia:02d}/{fecha.month:02d}"))


_CIFRA = re.compile(r"\$\s*\d|\b\d{1,3}(?:[.,]\d{3})+\b|\b\d{5,}\b|\d+(?:[.,]\d+)?\s*(?:%|por ?ciento)")
_FECHA_EN_TEXTO = re.compile(rf"\b\d{{1,2}} de (?:{'|'.join(_MESES)})\b|\b\d{{1,2}}/\d{{1,2}}(?:/\d{{2,4}})?\b")


def pide_calculo(query: str) -> bool:
    """La pregunta trae valores o porcentajes (p. ej. canon + IPC)."""
    return bool(_CIFRA.search((query or "").lower()))


def pide_plazo(query: str) -> bool:
    """La pregunta trae una fecha y pregunta cuando vence algo."""
    q = _normalizar(query)
    return bool(_FECHA_EN_TEXTO.search((query or "").lower())) and bool(
        re.search(r"\b(cuando|vence|plazo|termino|hasta que dia|me deben responder)\b", q))


def revisar_calculo(nombre: str, argumento: str, query: str, textos_vistos) -> str | None:
    """None si la cuenta se puede hacer; si no, la observacion que explica por que.

    - calculadora y calcular_plazo: solo despues de encontrar una norma.
    - calcular_plazo: el numero de dias tiene que aparecer en una norma vista, y
      la fecha tiene que salir de lo que dijo el usuario."""
    if not textos_vistos:
        return ("error: primero busca con buscar_normas (o leer_articulo) la norma que da el dato; "
                "no se hacen cuentas que ninguna norma respalde.")
    if nombre != "calcular_plazo":
        return None
    partes = [p.strip() for p in (argumento or "").split(",")]
    if len(partes) == 3:
        try:
            dias = int(partes[1])
        except ValueError:
            return None                      # el error de formato lo da calcular_plazo
        if not plazo_respaldado(dias, textos_vistos):
            return (f"error: ninguna norma que encontraste da un termino de {dias} dias. Revisa que plazo "
                    "da la norma (p. ej. 'quince (15) dias') y usa ese numero, o busca la norma del plazo.")
        fecha = _parsear_fecha(partes[0])
        if fecha is not None and not fecha_en_consulta(fecha, query):
            return (f"error: el usuario no dio la fecha {fecha.isoformat()}. No inventes fechas: si no la "
                    "dio, explica el plazo en dias sin calcular una fecha de vencimiento.")
    return None


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


def articulos_vistos(resultados) -> set[str]:
    """Numeros de articulo de los chunks recuperados (SearchResult)."""
    return {normalizar_numero(a).upper() for r in resultados for a in r.articulos_incluidos}


def citas_no_respaldadas(
    respuesta: str, resultados=(), query: str = "", *, vistos: set[str] | None = None
) -> list[str]:
    """Articulos que cita la respuesta y que el sistema NO vio.

    "Vio" = los `articulos_incluidos` de los chunks recuperados (o el conjunto
    `vistos`, si se pasa directo), mas los que menciono el propio usuario en la
    pregunta (citar lo que el usuario dijo no es inventar; la respuesta puede
    estar aclarando que ese articulo no aplica).

    Se usa en tres lugares con la misma regla: la verificacion del agente ReAct,
    la metrica de DSPy (tools/rag/dspy_prompt.py) y la prudencia en la
    evaluacion (tools/evaluation/ragas_metrics.py).

    Limite conocido: compara numeros de articulo, no el par (norma, articulo).
    Detecta el articulo inventado, no el articulo real atribuido a otra ley.
    """
    permitidos = set(vistos) if vistos is not None else articulos_vistos(resultados)
    permitidos |= articulos_citados(query)
    return sorted(articulos_citados(respuesta) - permitidos, key=lambda x: (len(x), x))


# Sentencias de la Corte Constitucional ("T-760 de 2008", "SU-111/97", "C 355").
# El corpus solo tiene normas, asi que cualquier sentencia citada es de memoria.
_PATRON_SENTENCIA = re.compile(r"\b(?:T|C|SU|A)\s?-\s?\d{2,4}\b", re.IGNORECASE)
_PATRON_PROMESA = re.compile(
    r"\b(te garantizo|garantizado|garantizada|vas a ganar|ganaras seguro|con seguridad ganaras|"
    r"seguro que ganas|tienes asegurad[oa])\b",
    re.IGNORECASE,
)


def sentencias_citadas(texto: str) -> set[str]:
    return {re.sub(r"\s", "", m).upper() for m in _PATRON_SENTENCIA.findall(texto or "")}


def promete_resultado(texto: str) -> bool:
    return bool(_PATRON_PROMESA.search(texto or ""))


def citas_no_verificables(respuesta: str, resultados=(), query: str = "", *,
                          vistos: set[str] | None = None) -> list[str]:
    """Todo lo que la respuesta cita y no se puede verificar contra lo recuperado:
    articulos que no vio y sentencias (el corpus no tiene jurisprudencia, asi que
    una sentencia citada es siempre de memoria). Lista vacia = respuesta limpia.

    Es la regla que aplican las tres rutas antes de entregar una respuesta: el
    agente ReAct, el RAG de una pasada (pipeline.answer_query) y el tool use."""
    return (citas_no_respaldadas(respuesta, resultados, query, vistos=vistos)
            + sorted(sentencias_citadas(respuesta)))


def nota_de_correccion(no_verificables: list[str]) -> str:
    return (f"Verificacion de citas: tu respuesta cita {', '.join(no_verificables)}, que no aparece(n) "
            "en las normas recuperadas. Responde de nuevo citando solo normas que aparezcan ahi, o "
            "sin citar numeros de articulo ni sentencias.")


def es_prudente(respuesta: str, vistos: set[str], query: str = "") -> bool:
    """Comprobacion programatica de prudencia (casos adversariales).

    Prudente = usa la valvula de escape, o no cita articulos que no vio, no cita
    sentencias (el corpus no tiene jurisprudencia: seria de memoria) y no promete
    un resultado. Es un piso verificable, no un juicio completo: lo que cada
    caso adversarial espera en detalle (p. ej. priorizar la seguridad ante una
    amenaza) lo juzga el harness de M2 con su criterio.
    """
    # La frase de escape NO exime de las comprobaciones. Antes bastaba con que
    # la respuesta la contuviera para darla por prudente, asi que
    # "No tengo informacion verificada... pero segun el articulo 99 y la
    # sentencia T-760 de 2008" pasaba: justo lo que la valvula existe para
    # evitar. Reconocer que no se tiene con que responder y despues responder
    # igual no es prudencia.
    return (not citas_no_respaldadas(respuesta, query=query, vistos=vistos)
            and not sentencias_citadas(respuesta)
            and not promete_resultado(respuesta))


# --- Herramientas en formato nativo (docs seccion 26) -------------------------

LEER_ARTICULO = herramienta(
    "leer_articulo",
    "Lee el texto exacto de un articulo del corpus. Usala cuando el usuario menciona un "
    "articulo o cuando un resultado remite a otro articulo.",
    {"norma": "la norma, p. ej. 'Ley 820 de 2003', 'CST' o 'Constitucion'",
     "numero": "el numero del articulo, p. ej. '20'"},
)
CALCULADORA = herramienta(
    "calculadora",
    "Calcula una expresion aritmetica exacta (valores, porcentajes).",
    {"expresion": "numeros sin separador de miles y con punto decimal, + - * / y parentesis; "
                  "p. ej. '1200000 * 1.052'"},
)
CALCULAR_PLAZO = herramienta(
    "calcular_plazo",
    "Fecha en que vence un termino de n dias contado desde el dia siguiente a una fecha. "
    "En dias habiles salta sabados, domingos y festivos de Colombia.",
    {"fecha": "fecha de inicio AAAA-MM-DD", "dias": "numero de dias que da la norma",
     "tipo": "'habiles' o 'calendario', segun la norma"},
)
HERRAMIENTAS_REACT = [BUSCAR_NORMAS, LEER_ARTICULO, CALCULADORA, CALCULAR_PLAZO]


def argumento_de(nombre: str, args: dict) -> str:
    """Argumentos de una llamada nativa -> el texto que reciben las funciones."""
    args = args or {}
    if nombre == "leer_articulo" and "norma" in args:
        return f"{args.get('norma', '')}, {args.get('numero', '')}"
    if nombre == "calcular_plazo" and "fecha" in args:
        return f"{args.get('fecha', '')}, {args.get('dias', '')}, {args.get('tipo', 'habiles')}"
    clave = {"buscar_normas": "consulta", "calculadora": "expresion"}.get(nombre)
    if clave and clave in args:
        return str(args[clave])
    return str(next(iter(args.values()), "")) if args else ""


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
    """Bucle ReAct: pensamiento -> herramienta -> resultado, hasta responder.

    Las herramientas van en formato nativo de function calling (docs seccion 26):
    el modelo las pide con <tool_call> y responde en texto normal cuando termina.
    Se sigue aceptando el formato de texto viejo ("Accion: x[...]") como respaldo.

    Antes de aceptar una respuesta, el codigo la revisa (secciones 19, 25 y 26):
      1. Habla de herramientas en vez de responder ("usa calcular_plazo...") o
         esta vacia -> se rechaza y el agente tiene que responder de verdad.
      2. La pregunta es juridica (no charla trivial) y el agente no uso
         buscar_normas -> el codigo busca con la pregunta del usuario y le pide
         responder con eso (cubre al que responde de memoria y al que lee el
         articulo equivocado del usuario y se queda ahi).
      3. Cita articulos que no vio, o sentencias -> se rechaza.
      4. Busco y no encontro ninguna norma -> escape por codigo.
      5. Le piden una sentencia y no dice que no puede verificarla -> se rechaza.
      6. La pregunta trae cifras o una fecha y no hizo la cuenta -> se le pide
         una vez (seccion 27).
    Ademas, calculadora y calcular_plazo solo corren despues de ver una norma, y
    calcular_plazo solo con dias que aparezcan en ella y una fecha que dijo el
    usuario (revisar_calculo). La busqueda forzada va sin el articulo que cito
    el usuario (tools.limpiar_consulta_forzada).
    Cada rechazo consume un paso. Si se agotan los pasos, una respuesta final
    forzada pasa por las mismas reglas; si no las cumple, escape por codigo.

    Devuelve el contrato de pipeline.answer_query mas `traza` (una fila por paso)
    y `verificacion` (con `busqueda`: "modelo", "forzada_por_codigo" o "ninguna").
    """
    generar = _generar if _generar is not None else _generar_mensajes_por_defecto(model_bundle, use_lora)

    mensajes = [{"role": "system", "content": SYSTEM_REACT}, {"role": "user", "content": query}]
    traza: list[dict] = []
    vistos: list = []
    estado = {"busqueda_forzada": False, "pidio_calculo": False}

    def _busco_normas() -> bool:
        return any(p["accion"].startswith("buscar_normas") for p in traza)

    def _busqueda() -> str:
        if not _busco_normas():
            return "ninguna"
        return "forzada_por_codigo" if estado["busqueda_forzada"] and not any(
            p["accion"] == "buscar_normas" for p in traza) else "modelo"

    def _salida(respuesta: str, escape: str | None = None) -> dict:
        resultado = resultado_para_evaluacion(
            query, respuesta, vistos, sistema="react", use_lora=use_lora,
            use_hybrid=use_hybrid, use_rerank=use_rerank, top_k=top_k, traza=traza,
        )
        resultado["verificacion"] = {"escape_por_codigo": escape, "busqueda": _busqueda(),
                                     "citas_rechazadas": [c for p in traza if p["accion"] == "Responder (rechazado)"
                                                          for c in p.get("rechazadas", [])]}
        return resultado

    def _ejecutar(nombre: str, argumento: str) -> str:
        if nombre == "buscar_normas":
            observacion, resultados = ejecutar_tool_con_resultados(
                {"tool": "buscar_normas", "args": {"consulta": argumento}},
                store, top_k=top_k, use_hybrid=use_hybrid, use_rerank=use_rerank, bm25=bm25,
            )
            vistos.extend(resultados)
            return observacion
        if nombre == "leer_articulo":
            observacion, resultados = leer_articulo(argumento, store)
            vistos.extend(resultados)
            return observacion
        if nombre in ("calcular_plazo", "calculadora"):
            bloqueo = revisar_calculo(nombre, argumento, query, [r.text for r in vistos])
            if bloqueo:
                return bloqueo
            return calcular_plazo(argumento) if nombre == "calcular_plazo" else calculadora(argumento)
        return f"error: no existe la herramienta {nombre!r}."

    def _revisar(texto: str) -> tuple[str, object]:
        """('aceptar', texto) | ('rechazar', (observacion, rechazadas)) |
        ('forzar_busqueda', None) | ('escape', motivo)."""
        if RESPUESTA_SIN_CONTEXTO.lower() in texto.lower():
            # Se acepta el escape, pero no a ciegas: si ademas cita algo que no
            # aparece en los resultados, la frase estaba sirviendo de permiso
            # para inventar. Se trata como cualquier otra respuesta con citas
            # sin respaldo.
            no_vistas_escape = citas_no_verificables(texto, vistos, query)
            if not no_vistas_escape:
                return "aceptar", texto
            return "rechazar", (
                f"Dices que no tienes informacion verificada y aun asi citas "
                f"{', '.join(no_vistas_escape)}. Si no lo encontraste, no lo cites: "
                "responde solo con la frase, sin agregar normas.", no_vistas_escape)
        # La red de seguridad va PRIMERO, antes de rechazar por cualquier motivo.
        # Estaba despues del rechazo por "menciona herramientas", y una salida
        # como "Primero busca la norma..." cae justo ahi: se rechazaba, y como la
        # generacion es greedy el modelo repetia el mismo texto hasta agotar los
        # pasos y escapar sin haber buscado nunca. En la corrida del 2026-10-07
        # eso dejo 5 casos sin buscar y 9 sin contexto (contra 4 de las otras
        # rutas), justo en las preguntas compuestas y de plazo, que son para las
        # que existe el ReAct.
        if not _busco_normas() and not es_charla_trivial(query) and not estado["busqueda_forzada"]:
            return "forzar_busqueda", None
        if not texto.strip() or menciona_herramientas(texto):
            return "rechazar", ("Eso no es una respuesta para el usuario: describe herramientas o esta "
                                "vacia. Usa las herramientas que necesites y luego responde al usuario "
                                "en texto normal.", [])
        no_vistas = citas_no_verificables(texto, vistos, query)
        if no_vistas:
            return "rechazar", (f"Verificacion de citas: tu respuesta cita {', '.join(no_vistas)}, que no "
                                "aparece(n) en ninguno de tus resultados. Buscalos con buscar_normas o "
                                "leer_articulo, o responde sin citarlos.", no_vistas)
        if _busco_normas() and not vistos:
            return "escape", "sin_contexto"
        if pide_sentencia(query) and not reconoce_limite(texto):
            return "rechazar", (NOTA_SENTENCIA, [])
        faltan = [h for h, pide in (("calculadora", pide_calculo(query)), ("calcular_plazo", pide_plazo(query)))
                  if pide and not any(p["accion"] == h for p in traza)]
        if faltan and vistos and not estado["pidio_calculo"]:
            # Una sola vez: la pregunta trae cifras o una fecha y no se hizo la cuenta.
            estado["pidio_calculo"] = True
            return "rechazar", (f"La pregunta trae cifras o una fecha y no hiciste la cuenta. Usa "
                                f"{' y '.join(faltan)} con los datos del usuario y los de la norma que "
                                "encontraste, y da el resultado en tu respuesta.", [])
        return "aceptar", texto

    # Respuesta que ya se rechazo una vez. Con generacion greedy, que el modelo
    # vuelva a entregar EXACTAMENTE lo mismo despues de leer la correccion
    # significa que no va a avanzar, y seguir solo gasta pasos hasta el escape.
    # Se compara solo contra respuestas rechazadas, no contra cualquier salida:
    # repetir una llamada a herramienta si avanza (se ejecuta cada vez), y hay
    # un caso legitimo en que la misma respuesta se rechaza y luego se acepta
    # (la regla de pedir el calculo una sola vez).
    ultimo_rechazado = None

    for paso in range(1, max_pasos + 1):
        salida = generar(mensajes, HERRAMIENTAS_REACT)
        libre, llamadas = extraer_llamadas(salida)

        if llamadas:                                   # formato nativo
            for llamada in llamadas:
                argumento = argumento_de(llamada["name"], llamada["arguments"])
                observacion = _ejecutar(llamada["name"], argumento)
                traza.append({"paso": paso, "pensamiento": libre, "accion": llamada["name"],
                              "argumento": argumento, "observacion": observacion})
                mensajes.append(turno_con_llamada(libre, llamada))
                mensajes.append(turno_resultado(llamada["name"], observacion))
            continue

        pensamiento, accion = parsear_paso(salida)     # respaldo: formato de texto
        if accion is not None and accion[0] != "Responder":
            nombre, argumento = accion
            observacion = _ejecutar(nombre, argumento)
            traza.append({"paso": paso, "pensamiento": pensamiento, "accion": nombre,
                          "argumento": argumento, "observacion": observacion})
            mensajes.append({"role": "assistant", "content": salida})
            mensajes.append({"role": "user", "content": f"Observacion: {observacion}"})
            continue

        texto = accion[1] if accion is not None else (libre or salida).strip()
        veredicto, detalle = _revisar(texto)
        if veredicto == "aceptar":
            traza.append({"paso": paso, "pensamiento": pensamiento, "accion": "Responder",
                          "argumento": texto, "observacion": ""})
            return _salida(texto)
        if veredicto == "escape":
            traza.append({"paso": paso, "pensamiento": pensamiento,
                          "accion": "Responder (escape por codigo: sin normas)",
                          "argumento": texto, "observacion": ""})
            return _salida(RESPUESTA_ESCAPE_POR_CODIGO, detalle)
        mensajes.append({"role": "assistant", "content": salida})
        if veredicto == "forzar_busqueda":
            # Red de seguridad: iba a responder una pregunta juridica sin buscar.
            estado["busqueda_forzada"] = True
            consulta = limpiar_consulta_forzada(query)   # sin el articulo del usuario (seccion 27)
            observacion = _ejecutar("buscar_normas", consulta)
            traza.append({"paso": paso, "pensamiento": pensamiento,
                          "accion": "buscar_normas (forzado por codigo)", "argumento": consulta,
                          "observacion": observacion, "respuesta_descartada": texto})
            mensajes.append({"role": "user", "content": (
                f"Antes de responder hay que buscar en las normas. Resultado de buscar_normas para "
                f"tu pregunta:\n{observacion}\n\nCon esto, responde la pregunta completa. Si el usuario "
                "cito un articulo que no corresponde, dile cual si aplica.")})
            continue
        observacion, rechazadas = detalle
        if texto == ultimo_rechazado:
            traza.append({"paso": paso, "pensamiento": pensamiento,
                          "accion": "Responder (corte por repeticion)", "argumento": texto,
                          "observacion": "repitio la misma respuesta ya rechazada; no avanza"})
            break
        ultimo_rechazado = texto
        traza.append({"paso": paso, "pensamiento": pensamiento, "accion": "Responder (rechazado)",
                      "argumento": texto, "observacion": observacion, "rechazadas": rechazadas})
        mensajes.append({"role": "user", "content": observacion})

    # Pasos agotados: una ultima generacion que solo puede responder.
    salida = generar(mensajes + [{"role": "user", "content": (
        "Ya no puedes usar herramientas. Responde ahora al usuario, en texto normal, con lo que "
        "encontraste.")}], None)
    libre, llamadas = extraer_llamadas(salida)
    pensamiento, accion = parsear_paso(salida)
    texto = accion[1] if accion is not None and accion[0] == "Responder" else libre
    estado["pidio_calculo"] = True  # sin pasos, ya no se puede pedir la cuenta
    veredicto, _ = _revisar(texto) if not llamadas else ("rechazar", None)
    if veredicto == "forzar_busqueda":
        veredicto = "rechazar"      # ya no quedan pasos para buscar
    respuesta = texto if veredicto == "aceptar" else RESPUESTA_ESCAPE_POR_CODIGO
    traza.append({"paso": max_pasos + 1, "pensamiento": pensamiento, "accion": "Responder (forzado)",
                  "argumento": respuesta, "observacion": ""})
    return _salida(respuesta, None if veredicto == "aceptar" else "no_respondio")
