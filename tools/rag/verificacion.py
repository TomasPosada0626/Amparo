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
