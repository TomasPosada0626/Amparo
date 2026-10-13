"""Fragmentos cuyo unico contenido es una derogatoria (H12).

*"Articulo 226. Derogado por el articulo 39 de la Ley 1955 de 2019."* no puede
responder nada, y en la auditoria 6.1 ocupaba puestos del top-5: en 9058, 4 de
los 5 fragmentos recuperados eran "Derogado". Los `.md` registran bien que el
articulo se derogo; lo que no tiene sentido es entregarlo como contexto.

La regla es la del dictamen de clase B' (`docs/m3_articulos_gold_dictamen_claseB.md`),
probada sobre la metadata del indice sin regenerarlo:

    exige que el texto contenga "derogad"   <- sin esto se colarian los
                                               chunks que solo son rotulo
    quita los encabezados de division (TITULO, CAPITULO, LIBRO...)
    quita los encabezados de articulo ("Articulo 226.")
    quita las declaraciones de derogatoria ("Derogado por el articulo X de...")
    quita la rubrica en mayusculas ("ENGANCHE PARA EL EXTERIOR")
    -> es derogatoria pura si no queda ni un caracter alfanumerico

El orden importa: la derogatoria se quita ANTES que la rubrica, para no borrar
la rubrica de un articulo vigente y dejarlo pareciendo vacio. El sesgo elegido
es sub-excluir antes que sobre-excluir: un articulo parcialmente derogado tiene
texto util y se conserva.

Se aplica como filtro POSTERIOR a la recuperacion (`retrieve`, con
`config.FILTRAR_DEROGATORIAS`), sin reconstruir el indice. **Apagado por
defecto**: cambia lo que ve el modelo, y mientras se compara un candidato de M1
con v1 el buscador tiene que ser el mismo (regla de una sola variable).
"""
from __future__ import annotations

import re

_TIENE_DEROGAD = re.compile(r"derogad", re.IGNORECASE)
_DIVISION = re.compile(
    r"^\s*(?:T[IÍ]TULO|CAP[IÍ]TULO|LIBRO|PARTE|SECCI[OÓ]N|SUBSECCI[OÓ]N)\b[^\n]*$",
    re.IGNORECASE | re.MULTILINE)
_ENCABEZADO_ARTICULO = re.compile(
    r"\b(?:ART[IÍ]CULO|ART\.)\s*\d+[A-Za-z\-º°o]*\s*[.:\-–]?", re.IGNORECASE)
_DECLARACION = re.compile(
    r"\(?\s*(?:art[ií]culo\s+)?(?:derogad[oa]s?|fue\s+derogad[oa])\b[^.\n)]*[.)]?",
    re.IGNORECASE)
_RUBRICA = re.compile(r"\b[A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ0-9 ,;:\-–()/]*[A-ZÁÉÍÓÚÑÜ)]\b\.?")
_ALFANUMERICO = re.compile(r"[0-9A-Za-zÁÉÍÓÚÑÜáéíóúñü]")


def es_solo_derogatoria(texto: str) -> bool:
    """True si el fragmento no dice nada mas que una derogatoria."""
    if not texto or not _TIENE_DEROGAD.search(texto):
        return False
    t = _DIVISION.sub(" ", texto)
    t = _ENCABEZADO_ARTICULO.sub(" ", t)
    t = _DECLARACION.sub(" ", t)
    t = _RUBRICA.sub(" ", t)
    return not _ALFANUMERICO.search(t)


def filtrar(resultados: list) -> list:
    """Los resultados sin los fragmentos que son solo una derogatoria."""
    return [r for r in resultados if not es_solo_derogatoria(getattr(r, "text", "") or "")]
