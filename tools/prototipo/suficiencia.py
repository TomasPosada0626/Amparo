"""Prototipo de comprobacion de suficiencia de evidencia. **NO conectado.**

Nada de aqui se llama desde el pipeline. Es un banco de medicion para decidir si
existe una senal util, no una puerta.

## El hueco que se intenta cubrir

`verificacion.citas_no_verificables` responde *"¿el articulo citado se
recupero?"*. No responde *"¿ese articulo sostiene lo que la respuesta afirma?"*,
y tampoco ve una afirmacion hecha sin citar nada. Los dos casos de referencia:

    2229  "Pide por escrito la reparacion y, si no la hacen, acude a la
           Superintendencia de Servicios Publicos Domiciliarios."
          Compraventa entre particulares. Ninguna cita inventada, ninguna
          entidad inexistente, una competencia institucional sin respaldo.

    2823  "El articulo 65 del Codigo Sustantivo del Trabajo obliga al empleador
           a pagar la indemnizacion por falta de pago..."
          La pregunta es por el embargo de una cuenta sin saldo. El articulo 65
          **si se recupero** y **si es del CST**: la cita es correcta en los dos
          ejes que el codigo sabe comprobar, y es ajena a la pregunta.

`citas_no_verificables` aprueba las dos.

## Las cuatro situaciones que hay que distinguir

    SUFICIENTE    el contexto trae el articulo que responde
    IRRELEVANTE   contexto no vacio, nada de el responde              (2823)
    PARCIAL       responde una parte                                   (B3)
    SIN_RESPALDO  afirmacion juridica sustantiva sin respaldo          (2229)

No son excluyentes y **no se fusionan en un booleano**: una puerta unica
esconderia cual se activo, y cada una pide una reaccion distinta -- abstenerse,
responder solo la parte, o quitar la afirmacion.

## Lo que estas senales NO hacen

Ninguna comprueba **suficiencia semantica**: si ESE articulo sostiene ESA
afirmacion. Eso es juicio juridico y asi esta marcado en `verificacion.py`, que
ya retiro una heuristica lexica de atribucion por fallar en un caso positivo
conocido (3328). Lo que estas senales miden es mas pobre y mas honesto: si la
evidencia entregada es del **tema** de la pregunta, y si lo que la respuesta
afirma esta **en** esa evidencia.

    python -m tools.prototipo.suficiencia        # la matriz por senal
"""
from __future__ import annotations

import re

from tools.rag.chunk import normalizar_numero

# --------------------------------------------------------------------------
# Conjuntos: que se uso para disenar y que se reserva
# --------------------------------------------------------------------------
#
# Honestidad sobre la procedencia, porque cambia como se leen los numeros:
#
#   DISENO     casos mirados al escribir estas senales. Su resultado es
#              optimista por construccion y NO es evidencia de generalizacion.
#              2229 y 2823 estan aqui porque el encargo los nombro: pedir que
#              una senal los resuelva y luego medirla en ellos es ajustar.
#   RESERVADO  el resto. Tampoco son datos virgenes -- los 45 gold pasaron por
#              la auditoria 6.1 y los 35 B2 por la adjudicacion --, pero no se
#              miraron **para elegir estas senales**. Es la mejor evidencia
#              disponible, y no equivale a un conjunto nuevo.
CASOS_DISENO_B2 = {"2229", "2823", "2126", "2221", "2424", "3517", "3920", "4324"}
CASOS_DISENO_GOLD = {"9001", "9004"}


# --------------------------------------------------------------------------
# Senales
# --------------------------------------------------------------------------

_ARTICULO = re.compile(r"\bart(?:[ií]culos?|s?\.)\s*(\d+(?:\s*-\s*\d+)?[A-Za-z]?)", re.IGNORECASE)


def articulos_del_contexto(chunks) -> set[str]:
    """Numeros de articulo presentes en el contexto entregado."""
    salida = set()
    for ch in chunks or ():
        for a in (ch.get("articulos") or ch.get("articulos_incluidos") or ()):
            salida.add(normalizar_numero(str(a)).upper())
        m = re.search(r"Articulo\s+([\w-]+)", ch.get("cita") or "", re.IGNORECASE)
        if m:
            salida.add(normalizar_numero(m.group(1)).upper())
    return salida


def articulos_citados(respuesta: str) -> set[str]:
    return {normalizar_numero(re.sub(r"\s+", "", m.group(1))).upper()
            for m in _ARTICULO.finditer(respuesta or "")}


def s1_sin_ninguna_cita(respuesta: str, chunks=()) -> bool:
    """La respuesta no cita ningun articulo. Senal de base, no de fallo:
    muchas respuestas correctas de orientacion no citan."""
    return not articulos_citados(respuesta)


def s2_sin_cita_respaldada(respuesta: str, chunks=()) -> bool:
    """Cita articulos y **ninguno** esta en el contexto entregado."""
    citados = articulos_citados(respuesta)
    return bool(citados) and not (citados & articulos_del_contexto(chunks))


def normas_del_contexto(chunks) -> set[str]:
    return {ch.get("doc_id") or "" for ch in (chunks or ()) if ch.get("doc_id")}


def _categorias_de_doc() -> dict:
    from tools.rag import corpus

    return {n.path.stem: set(n.categorias) for n in corpus.NORMAS_EN_ALCANCE}


def s3_contexto_de_otra_materia(pregunta: str, chunks, categoria_real: str = "",
                                usar_enrutador: bool = True) -> bool:
    """Ninguna norma del contexto cubre la categoria de la pregunta.

    Es la senal del caso 2823: la pregunta es de embargos y lo recuperado es
    laboral. **Con `usar_enrutador=True` la categoria la predice el enrutador**,
    que es lo que el sistema tiene en produccion; con `False` se usa la etiqueta
    verdadera, que en servicio no existe. La diferencia entre las dos mide
    cuanto de la senal depende de un dato que no se tiene.

    Las normas transversales no cuentan como cobertura: la Constitucion aparece
    en casi todo y haria que la senal nunca se active.

    **Un contexto vacio no es un contexto de otra materia.** Son dos de las
    cuatro situaciones que hay que distinguir, y ademas el pipeline nunca llega
    aqui con contexto vacio: cuando la busqueda no trae nada responde la frase de
    escape sin llamar al modelo (`pipeline._generar_verificado`). Devolver True
    con contexto vacio confundiria "no se recupero nada" con "se recupero algo
    ajeno", que piden reacciones distintas.
    """
    from tools.rag.corpus import TRANSVERSAL
    from tools.rag.enrutador import enrutador_por_defecto

    if not (chunks or ()):
        return False
    if usar_enrutador:
        cats = set(enrutador_por_defecto().categorias(pregunta) or ())
    else:
        cats = {categoria_real} if categoria_real else set()
    if not cats:
        return False
    de_doc = _categorias_de_doc()
    for doc in normas_del_contexto(chunks):
        propias = de_doc.get(doc, set()) - {TRANSVERSAL}
        if propias & cats:
            return False
    return True


def s4_afinidad_lexica_baja(pregunta: str, chunks, umbral: float = 0.10) -> bool:
    """El mejor fragmento comparte poco vocabulario con la pregunta.

    El umbral **no esta calibrado**: 0.10 es un punto de lectura para ver la
    forma de la distribucion, no un valor elegido por su rendimiento. Ajustarlo
    sobre estos mismos casos seria exactamente el error que el encargo prohibe.
    """
    from tools.evaluation.similitud import IndiceTfidf

    textos = [(ch.get("cita") or "") + " " + (ch.get("text") or ch.get("texto") or "")
              for ch in (chunks or ())]
    if not textos:
        return False
    return max(IndiceTfidf(textos).similitudes(pregunta) or [0.0]) < umbral


def s5_competencias_sin_respaldo(respuesta: str, contexto_texto: str) -> bool:
    """Entidades reales nombradas que el contexto entregado no menciona.

    Reutiliza el detector del commit 9c9f5a9 tal cual. Alli se midio: precision
    1.00 y recall 0.46 sobre los reservados. **Es senal de revision, no puerta**,
    y aqui no cambia de estatuto.
    """
    from tools.evaluation.afirmaciones_sin_respaldo import competencias_sin_respaldo

    return bool(competencias_sin_respaldo(respuesta, contexto_texto))


def s6_plazo_sin_respaldo(respuesta: str, contexto_texto: str) -> bool:
    """Un plazo en numeros que el contexto no trae. Mismo criterio que la puerta
    del dataset, para no tener dos definiciones."""
    from tools.rag.verificacion import numero_en_letras

    ctx = re.sub(r"\s+", " ", (contexto_texto or "")).lower()
    for m in re.finditer(r"\b(\d{1,3})\s*(?:d[ií]as?|meses?|a[nñ]os?|horas?)\b",
                         respuesta or "", re.IGNORECASE):
        n = int(m.group(1))
        if str(n) not in ctx and numero_en_letras(n).lower() not in ctx:
            return True
    return False


SENALES = {
    "S1 sin ninguna cita": lambda c: s1_sin_ninguna_cita(c["respuesta"], c["chunks"]),
    "S2 cita sin respaldo en el contexto": lambda c: s2_sin_cita_respaldada(c["respuesta"], c["chunks"]),
    "S3 contexto de otra materia (enrutador)": lambda c: s3_contexto_de_otra_materia(
        c["pregunta"], c["chunks"], c["categoria"], usar_enrutador=True),
    "S3b contexto de otra materia (categoria real)": lambda c: s3_contexto_de_otra_materia(
        c["pregunta"], c["chunks"], c["categoria"], usar_enrutador=False),
    "S4 afinidad lexica baja": lambda c: s4_afinidad_lexica_baja(c["pregunta"], c["chunks"]),
    "S5 competencia institucional sin respaldo": lambda c: s5_competencias_sin_respaldo(
        c["respuesta"], c["contexto_texto"]),
    "S6 plazo sin respaldo": lambda c: s6_plazo_sin_respaldo(c["respuesta"], c["contexto_texto"]),
    "C1 = S3 y no S1 (cita algo, de otra materia)": lambda c: (
        s3_contexto_de_otra_materia(c["pregunta"], c["chunks"], c["categoria"], usar_enrutador=True)
        and not s1_sin_ninguna_cita(c["respuesta"], c["chunks"])),
    "C2 = S3 o S5": lambda c: (
        s3_contexto_de_otra_materia(c["pregunta"], c["chunks"], c["categoria"], usar_enrutador=True)
        or s5_competencias_sin_respaldo(c["respuesta"], c["contexto_texto"])),
}


def clasificar(caso: dict) -> str:
    """La clasificacion en cuatro, derivada de las senales. Prototipo.

    El orden importa: una respuesta puede disparar varias y lo que se devuelve
    es la situacion mas grave, porque es la que decide que hacer.
    """
    if s3_contexto_de_otra_materia(caso["pregunta"], caso["chunks"], caso["categoria"]):
        return "IRRELEVANTE"
    if s2_sin_cita_respaldada(caso["respuesta"], caso["chunks"]):
        return "SIN_RESPALDO"
    if s5_competencias_sin_respaldo(caso["respuesta"], caso["contexto_texto"]):
        return "SIN_RESPALDO"
    if s1_sin_ninguna_cita(caso["respuesta"], caso["chunks"]):
        return "PARCIAL"
    return "SUFICIENTE"
