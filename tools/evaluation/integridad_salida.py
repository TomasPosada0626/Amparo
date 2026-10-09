"""Integridad de la salida: que la respuesta sea legible y siga siendo una respuesta.

Esto NO mide si el derecho es correcto ni si el modelo se abstuvo cuando debia.
Mide algo anterior: que el texto este en el idioma de la consulta y que el
modelo no se haya salido de su turno. Una respuesta puede ser juridicamente
impecable y aun asi inservible si la mitad esta en otro alfabeto.

Hace falta porque Qwen2.5-7B es un modelo multilingue cuyo pre-entrenamiento es
mayormente chino e ingles. En la corrida del 2026-10-09, el modelo base produjo
4 de 334 respuestas con caracteres chinos y el afinado 0 de 334. Se midio
despues de que la revision externa preguntara por tres respuestas del baseline
que no terminaban en punto: no estaban cortadas, habian cambiado de idioma.

Tres fallos distintos, y un caso puede tener varios:

  deriva_de_idioma   el texto cambia a otro sistema de escritura
  rompe_el_rol       aparece un marcador de turno de chat en la salida
  turno_ficticio     ademas, el modelo escribe el turno del usuario

El cero observado en el afinado NO es riesgo cero: son 334 ejemplos de una
sola corrida. Sirve como prueba de regresion, no como garantia.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Sequence

# Han, kana, bopomofo y formas de ancho completo. El espanol juridico no los usa
# nunca, asi que un solo caracter ya es senal; no hace falta umbral.
_PATRON_CJK = re.compile(
    r"[　-〿぀-ヿㇰ-ㇿ㐀-䶿一-鿿＀-￯]")

# Cirilico, griego, arabe, hebreo, devanagari, hangul y tailandes. Se listan por
# rango y no por "todo lo que no sea latino" para no marcar simbolos sueltos
# (º, §, €) que si aparecen en texto juridico.
_PATRON_OTRO_ALFABETO = re.compile(
    r"[Ѐ-ӿͰ-Ͽ؀-ۿ֐-׿ऀ-ॿ가-힯฀-๿]")

# Un marcador de turno en su propia linea. Se exige la linea completa porque
# "user" o "system" pueden aparecer dentro de una frase normal ("el sistema de
# salud"); lo que delata el fallo es que el modelo emita la etiqueta sola.
_PATRON_ROL = re.compile(r"^\s*(user|assistant|system|usuario|asistente)\s*:?\s*$",
                         re.IGNORECASE | re.MULTILINE)


def deriva_de_idioma(texto: str) -> bool:
    """¿La respuesta cambia a otro sistema de escritura?

    En el caso 4527 el cambio ocurre a mitad de frase ("no se requieren un
    numero especifico de anos de" + chino), asi que no basta con mirar el
    final: se busca en todo el texto.
    """
    t = texto or ""
    return bool(_PATRON_CJK.search(t) or _PATRON_OTRO_ALFABETO.search(t))


def rompe_el_rol(texto: str) -> bool:
    """¿Aparece un marcador de turno de chat dentro de la respuesta?"""
    return bool(_PATRON_ROL.search(texto or ""))


def turno_ficticio(texto: str) -> bool:
    """¿El modelo escribio el turno del usuario, y ademas le puso contenido?

    Es el fallo del caso 910: tras irse al chino, emite "user" y a continuacion
    una pregunta inventada. Mas grave que el marcador suelto, porque el modelo
    dejo de responder y se puso a simular la conversacion.
    """
    for m in _PATRON_ROL.finditer(texto or ""):
        if (texto or "")[m.end():].strip():
            return True
    return False


def fallos(texto: str) -> list[str]:
    """Las etiquetas que aplican a una respuesta, en orden de gravedad."""
    marcas = []
    if deriva_de_idioma(texto):
        marcas.append("deriva_de_idioma")
    if rompe_el_rol(texto):
        marcas.append("rompe_el_rol")
    if turno_ficticio(texto):
        marcas.append("turno_ficticio")
    return marcas


def resumen(registros: Sequence[dict], campo: str = "generated") -> dict:
    """Conteos con su denominador.

    El denominador va explicito porque esta metrica se calcula sobre los 334 de
    validacion, no sobre el subconjunto de 231 sin contexto que usan las
    metricas de citas. Mezclarlos fue un error real el 2026-10-09.
    """
    total = len(registros)
    salida = {"n": total, "deriva_de_idioma": 0, "rompe_el_rol": 0,
              "turno_ficticio": 0, "alguno": 0, "ids": []}
    for r in registros:
        marcas = fallos(r.get(campo) or "")
        if not marcas:
            continue
        salida["alguno"] += 1
        salida["ids"].append(r.get("id"))
        for m in marcas:
            salida[m] += 1
    return salida


def caracteres_no_latinos(texto: str) -> int:
    """Cuantos caracteres estan fuera del alfabeto latino, para ordenar casos."""
    return sum(1 for c in (texto or "")
               if not c.isascii() and "LATIN" not in unicodedata.name(c, ""))
