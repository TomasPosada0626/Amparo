"""Verificacion de citas: el control de codigo del principio de Amparo (no inventar normas).

Antes de entregar una respuesta, el RAG de una pasada (pipeline.answer_query)
extrae los articulos que cita y los compara con los que de verdad recupero. Si
cita algo que no vio, o una sentencia (el corpus no tiene jurisprudencia: seria
de memoria), regenera una vez con una nota de correccion y, si insiste, responde
con la valvula de escape. La misma regla la usan la metrica de DSPy
(tools/rag/dspy_prompt.py), la prudencia de la evaluacion
(tools/evaluation/ragas_metrics.py) y el piso de la hybrid search
(tools/rag/retrieve.es_referencia_exacta).

Estas funciones vivian en tools/rag/agentico.py, junto al agente ReAct. Las
rutas agenticas (tool use y ReAct) se retiraron el 2026-10-08 (C11 de la
auditoria, docs/m3_decisiones_rag.md seccion 27); la verificacion se queda
porque la usa la ruta que si se entrega.
"""
from __future__ import annotations

import re
from typing import Collection, Sequence
import unicodedata

from tools.rag.chunk import normalizar_numero

# --- Reconocer una norma por su nombre ---------------------------------------

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


def _normalizar_texto(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", sin_tildes.lower())


def puntaje_norma(consulta: str, fuente: str) -> int:
    """Cuanto se parece lo que se escribio a la `fuente` de un chunk.

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


# --- Numeros en letras --------------------------------------------------------

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


# --- Verificacion de citas ---------------------------------------------------

# "articulo 20", "artículos 13 y 14", "art. 6º", "arts. 5, 6 y 7".
_PATRON_CITA = re.compile(
    r"\bart(?:[ií]culos?|s?\.)\s*((?:\d+(?:\s*-\s*[A-Za-z](?![A-Za-z])|[A-Za-z](?![A-Za-z]))?\s*[º°]?\s*(?:,|\by\b|\be\b)?\s*)+)",
    re.IGNORECASE,
)


def articulos_citados(texto: str) -> set[str]:
    """Numeros de articulo que aparecen citados en un texto, normalizados como
    los guarda el chunker ("6º" -> "6", "14a" -> "14A")."""
    numeros = set()
    for grupo in _PATRON_CITA.findall(texto or ""):
        for numero in re.findall(r"\d+(?:\s*-\s*[A-Za-z](?![A-Za-z])|[A-Za-z](?![A-Za-z]))?", grupo):
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

    Limite conocido: compara numeros de articulo, no el par (norma, articulo).
    Detecta el articulo inventado, no el articulo real atribuido a otra ley.
    """
    permitidos = set(vistos) if vistos is not None else articulos_vistos(resultados)
    permitidos |= articulos_citados(query)
    return sorted(articulos_citados(respuesta) - permitidos, key=lambda x: (len(x), x))


# --- A que norma le atribuye la respuesta cada articulo ----------------------

# `citas_no_respaldadas` compara numeros de articulo sueltos, asi que da por
# respaldado "el articulo 20 de la Ley 100" cuando el contexto solo trae el
# articulo 20 de la Ley 820. Son normas distintas y el numero coincide por
# casualidad: con 36 normas indexadas y articulos de numeracion baja, coincide
# seguido. Para detectarlo hay que quedarse con el par (norma, articulo).

# "del mismo codigo", "de esa ley", "del mismo estatuto": la norma no se repite
# y hay que heredarla de la cita anterior. Sin esto, la segunda cita de
# "el articulo 62 del CST ... y el articulo 342 del mismo codigo" queda sin
# norma y no se puede comprobar.
_PATRON_ANAFORA = re.compile(
    r"\b(?:del?|dela|de\s+la|de\s+el)?\s*(?:mism[oa]|es[ae]|dich[oa]|aquel(?:la)?)\s+"
    r"(?:codigo|ley|decreto|estatuto|norma|regimen|constitucion)",
    re.IGNORECASE,
)

# Cuanto texto despues de la cita se mira buscando el nombre de la norma. 110
# caracteres cubren "de la Ley 1564 de 2012 (Codigo General del Proceso)" con
# holgura. La ventana se corta en la cita siguiente, porque si no la alcanza y
# la norma de esa cita gana la puntuacion: en "el articulo 86 de la
# Constitucion permite ... y el articulo 42 del Decreto 2591 de 1991", el 86
# quedaba atribuido al Decreto, que comparte dos numeros con la ventana
# mientras la Constitucion comparte uno. Era el unico falso positivo de la
# corrida del 2026-10-09.
_VENTANA_NORMA = 110

# Con menos de 2 no alcanza: un solo numero coincidente vale 2 y una sola
# palabra vale 1, y palabras como "codigo" estan en media docena de fuentes.
_PUNTAJE_MINIMO_NORMA = 2

# Conectores que pueden ir dentro del nombre de una norma ("Ley 1564 DE 2012",
# "Codigo General DEL Proceso").
_CONECTORES = {"de", "del", "la", "el", "los", "las", "y"}


def _frase_de_norma(ventana: str) -> str:
    """"de la Constitucion permite la accion..." -> "la Constitucion".

    En espanol juridico la norma va pegada al articulo, asi que se toma la
    frase que sigue y se corta en la primera palabra en minuscula que no sea
    conector. Puntuar la ventana completa premiaba las palabras genericas del
    nombre largo de una norma: con "el articulo 86 de la Constitucion permite
    la accion de tutela...", el nombre "Decreto 2591 de 1991 (Reglamentacion de
    la accion de tutela)" empataba con "accion" y "tutela" y le ganaba a
    "Constitucion Politica", que solo empataba con "constitucion".
    """
    # El "-1" de un sufijo ("articulo 391-1") queda al principio de la ventana,
    # porque _PATRON_CITA no lo captura. Si no se salta, la frase se corta ahi.
    texto = re.sub(r"^\s*(?:-\s*\d+\s*)?(?:de\s+|del\s+)?", "", ventana or "", count=1)
    palabras = re.findall(r"[\w.ºª-]+", texto, re.UNICODE)
    tomadas = []
    for w in palabras:
        if w.lower() in _CONECTORES or w[:1].isdigit() or w[:1].isupper():
            tomadas.append(w)
            continue
        break
    while tomadas and tomadas[-1].lower() in _CONECTORES:
        tomadas.pop()
    return " ".join(tomadas)


def citas_atribuidas(texto: str, fuentes: Sequence[str] = (),
                     numeros_conocidos: Collection[str] = ()) -> list[tuple[str, str]]:
    """[(fuente, articulo)] en el orden en que aparecen; fuente "" si no se pudo.

    `fuentes` son los nombres de norma candidatos -- normalmente la `fuente` de
    los chunks recuperados. La atribucion se resuelve mirando el texto que
    sigue a la cita y puntuandolo contra cada candidata con `puntaje_norma`,
    que ya expande siglas (CST, CGP) y pesa los numeros doble.

    No se intenta adivinar una norma que no este entre las candidatas: si la
    respuesta cita una ley que el sistema no recupero, la fuente queda "" y de
    eso ya se encarga `citas_no_respaldadas`.

    `numeros_conocidos` resuelve los sufijos numericos ("391-1", "269-1"), que
    `_PATRON_CITA` no captura. No se amplio ese patron a proposito: aceptar
    "N-M" convertiria "articulos 13-14", que es un rango, en el articulo
    "13-14". Aqui no hace falta adivinar, porque el contexto dice que numeros
    existen de verdad: solo se une "391" con "-1" si "391-1" esta entre ellos.
    """
    salida: list[tuple[str, str]] = []
    ultima = ""
    citas = list(_PATRON_CITA.finditer(texto or ""))
    for i, m in enumerate(citas):
        tope = citas[i + 1].start() if i + 1 < len(citas) else len(texto or "")
        ventana = (texto or "")[m.end():min(m.end() + _VENTANA_NORMA, tope)]
        if _PATRON_ANAFORA.match(ventana):
            fuente = ultima
        else:
            frase = _frase_de_norma(ventana)
            puntuadas = [(puntaje_norma(frase, f), f) for f in fuentes]
            mejor = max(puntuadas, default=(0, ""))
            fuente = mejor[1] if mejor[0] >= _PUNTAJE_MINIMO_NORMA else ""
        if fuente:
            ultima = fuente
        crudo = m.group(1)
        for numero in re.findall(r"\d+(?:\s*-\s*[A-Za-z](?![A-Za-z])|[A-Za-z](?![A-Za-z]))?", crudo):
            articulo = normalizar_numero(numero).upper()
            articulo = _con_sufijo_numerico(articulo, crudo, ventana, numeros_conocidos)
            salida.append((fuente, articulo))
    return salida


def _con_sufijo_numerico(articulo: str, crudo: str, ventana: str,
                         numeros_conocidos: Collection[str]) -> str:
    """"391" -> "391-1" solo si el contexto trae ese articulo con sufijo."""
    if not numeros_conocidos or "-" in articulo:
        return articulo
    cola = crudo[crudo.find(articulo) + len(articulo):] + ventana
    m = re.match(r"\s*-\s*(\d+)", cola)
    if not m:
        return articulo
    candidato = f"{articulo}-{m.group(1)}"
    return candidato if candidato in numeros_conocidos else articulo


def pares_vistos(resultados) -> set[tuple[str, str]]:
    """{(fuente, articulo)} de los chunks recuperados."""
    return {(r.fuente, normalizar_numero(a).upper())
            for r in resultados for a in (r.articulos_incluidos or ())}


def citas_mal_atribuidas(respuesta: str, resultados=(), query: str = "") -> list[str]:
    """Articulos que existen en el contexto pero bajo OTRA norma.

    Es el fallo que `citas_no_respaldadas` no ve: el articulo se recupero, el
    numero coincide, y la respuesta lo atribuye a una ley que no es la suya.
    Se devuelve "<articulo> (atribuido a <fuente>)" para que el mensaje diga
    donde esta el error.

    Solo cuenta cuando la atribucion se pudo resolver y el numero SI aparece en
    el contexto bajo otra fuente. Un articulo que el sistema no vio no es una
    mala atribucion sino una cita no respaldada, y ya se reporta aparte.
    """
    pares = pares_vistos(resultados)
    numeros = {a for _, a in pares} | articulos_citados(query)
    fuentes = sorted({f for f, _ in pares})
    malas = []
    for fuente, articulo in citas_atribuidas(respuesta, fuentes, numeros):
        if not fuente or articulo not in numeros:
            continue
        if (fuente, articulo) not in pares:
            malas.append(f"{articulo} (atribuido a {fuente})")
    return sorted(set(malas))


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
    una sentencia citada es siempre de memoria). Lista vacia = respuesta limpia."""
    return (citas_no_respaldadas(respuesta, resultados, query, vistos=vistos)
            + sorted(sentencias_citadas(respuesta)))


def nota_de_correccion(no_verificables: list[str]) -> str:
    return (f"Verificacion de citas: tu respuesta cita {', '.join(no_verificables)}, que no aparece(n) "
            "en las normas recuperadas. Responde de nuevo citando solo normas que aparezcan ahi, o "
            "sin citar numeros de articulo ni sentencias.")


def es_prudente(respuesta: str, vistos: set[str], query: str = "") -> bool:
    """Comprobacion programatica de prudencia (casos adversariales).

    Prudente = no cita articulos que no vio, no cita sentencias (el corpus no
    tiene jurisprudencia: seria de memoria) y no promete un resultado. Es un piso
    verificable, no un juicio completo: lo que cada caso adversarial espera en
    detalle (p. ej. priorizar la seguridad ante una amenaza) lo juzga el harness
    de M2 con su criterio.

    La frase de escape NO exime de las comprobaciones: "No tengo informacion
    verificada... pero segun el articulo 99 y la sentencia T-760 de 2008" no es
    prudente. Reconocer que no se tiene con que responder y despues responder
    igual es justo lo que la valvula existe para evitar.
    """
    return (not citas_no_respaldadas(respuesta, query=query, vistos=vistos)
            and not sentencias_citadas(respuesta)
            and not promete_resultado(respuesta))
