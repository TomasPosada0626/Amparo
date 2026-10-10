"""Atribuir un articulo a la norma equivocada.

`citas_no_respaldadas` compara numeros de articulo sueltos, asi que da por
respaldado "el articulo 20 de la Ley 100" cuando el contexto solo trae el
articulo 20 de la Ley 820. Con 36 normas indexadas y articulos de numeracion
baja, el numero coincide seguido y el fallo pasa inadvertido: la respuesta cita
un articulo que existe, atribuido a una ley que no es la suya.
"""
from __future__ import annotations

from types import SimpleNamespace

from tools.rag.verificacion import (
    citas_atribuidas,
    citas_mal_atribuidas,
    citas_no_respaldadas,
    pares_vistos,
)

LEY_820 = "Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana)"
CST = "Codigo Sustantivo del Trabajo"
CGP = "Ley 1564 de 2012 (Codigo General del Proceso)"


def chunk(fuente: str, *articulos: str) -> SimpleNamespace:
    return SimpleNamespace(fuente=fuente, articulos_incluidos=list(articulos))


CONTEXTO = [chunk(LEY_820, "20", "18"), chunk(CST, "62", "342")]


# --- el fallo que motiva todo esto -------------------------------------------

def test_atribuir_un_articulo_a_otra_norma_se_detecta():
    """El articulo 20 existe en el contexto, pero en la Ley 820, no en el CST."""
    respuesta = "El articulo 20 del Codigo Sustantivo del Trabajo limita el reajuste."

    assert citas_mal_atribuidas(respuesta, CONTEXTO) == ["20 (atribuido a Codigo Sustantivo del Trabajo)"]


def test_la_metrica_vieja_no_ve_ese_fallo():
    """Por eso hacia falta la nueva: el numero 20 si estaba entre los vistos."""
    respuesta = "El articulo 20 del Codigo Sustantivo del Trabajo limita el reajuste."

    assert citas_no_respaldadas(respuesta, CONTEXTO) == []


def test_atribuir_bien_no_es_un_fallo():
    respuesta = f"El articulo 20 de la {LEY_820.split(' (')[0]} limita el reajuste."

    assert citas_mal_atribuidas(respuesta, CONTEXTO) == []


# --- lo que NO debe contar como mala atribucion ------------------------------

def test_un_articulo_que_el_sistema_no_vio_no_es_mala_atribucion():
    """Es una cita no respaldada, y se reporta aparte. Contarla aqui tambien
    duplicaria el mismo error en dos metricas."""
    respuesta = "El articulo 99 de la Ley 820 de 2003 dice otra cosa."

    assert citas_mal_atribuidas(respuesta, CONTEXTO) == []
    assert citas_no_respaldadas(respuesta, CONTEXTO) == ["99"]


def test_sin_poder_resolver_la_norma_no_se_acusa():
    """Si la respuesta cita una ley que no se recupero, la atribucion queda
    vacia y no hay con que comparar."""
    respuesta = "El articulo 20 de la Ley 100 de 1993 dice otra cosa."

    assert citas_mal_atribuidas(respuesta, CONTEXTO) == []


def test_lo_que_el_usuario_menciono_no_se_acusa():
    respuesta = "El articulo 71 de la Ley 820 de 2003 no aplica a tu caso."

    assert citas_no_respaldadas(respuesta, CONTEXTO, query="¿que dice el articulo 71?") == []


# --- resolver a que norma apunta cada cita -----------------------------------

def test_la_sigla_se_expande():
    assert citas_atribuidas("El articulo 314 del CGP regula el desistimiento.", [CGP]) == [(CGP, "314")]


def test_la_anafora_hereda_la_norma_de_la_cita_anterior():
    """"y el articulo 342 del mismo codigo": sin esto la segunda cita queda sin
    norma y no se puede comprobar."""
    respuesta = ("El articulo 62 del Codigo Sustantivo del Trabajo lo permite, "
                 "y el articulo 342 del mismo codigo tambien.")

    assert citas_atribuidas(respuesta, [CST, LEY_820]) == [(CST, "62"), (CST, "342")]


def test_una_cita_multiple_reparte_la_misma_norma():
    respuesta = "Los articulos 13 y 14 de la Ley 820 de 2003 aplican."

    assert citas_atribuidas(respuesta, [LEY_820]) == [(LEY_820, "13"), (LEY_820, "14")]


def test_la_anafora_no_arrastra_una_norma_que_nunca_se_resolvio():
    assert citas_atribuidas("El articulo 5 del mismo codigo.", [CST]) == [("", "5")]


# --- sufijos -----------------------------------------------------------------

def test_un_sufijo_numerico_se_une_si_el_contexto_lo_tiene():
    """"391-1" no lo captura _PATRON_CITA; se resuelve contra los numeros que
    el contexto dice que existen."""
    salida = citas_atribuidas("El articulo 391-1 del Estatuto Tributario.",
                              ["Estatuto Tributario"], {"391-1"})

    assert salida == [("Estatuto Tributario", "391-1")]


def test_un_rango_no_se_confunde_con_un_sufijo():
    """"articulos 13-14" es un rango: unirlo daria el articulo inexistente
    "13-14". Por eso _PATRON_CITA no se amplio."""
    salida = citas_atribuidas("Los articulos 13-14 del Estatuto Tributario.",
                              ["Estatuto Tributario"], {"13", "14"})

    assert salida == [("Estatuto Tributario", "13")]


def test_un_sufijo_de_letra_sigue_funcionando():
    assert citas_atribuidas("El articulo 14A de la Ley 820 de 2003.", [LEY_820]) == [(LEY_820, "14-A")]


# --- los pares del contexto --------------------------------------------------

def test_los_pares_del_contexto_llevan_norma_y_articulo():
    assert pares_vistos(CONTEXTO) == {(LEY_820, "20"), (LEY_820, "18"), (CST, "62"), (CST, "342")}


def test_un_chunk_sin_articulos_no_rompe():
    assert pares_vistos([chunk(LEY_820)]) == set()


# El caso 9045 de la corrida del 2026-10-09, que era el unico falso positivo:
# la respuesta esta bien y el verificador la acusaba.

CONTEXTO_TUTELA = [chunk("Constitucion Politica de 1991", "86"),
                   chunk("Decreto 2591 de 1991 (Reglamentacion de la accion de tutela)", "42")]
RESPUESTA_9045 = (
    "Si: el articulo 86 de la Constitucion permite la accion de tutela contra "
    "particulares encargados de prestar un servicio publico, y el articulo 42 del "
    "Decreto 2591 de 1991 la permite contra una entidad privada."
)


def test_dos_citas_seguidas_no_se_roban_la_norma():
    """La ventana del articulo 86 alcanzaba "Decreto 2591 de 1991", que comparte
    dos numeros con ella mientras la Constitucion comparte uno."""
    assert citas_atribuidas(RESPUESTA_9045, [f.fuente for f in CONTEXTO_TUTELA]) == [
        ("Constitucion Politica de 1991", "86"),
        ("Decreto 2591 de 1991 (Reglamentacion de la accion de tutela)", "42"),
    ]


def test_la_respuesta_del_9045_no_tiene_mala_atribucion():
    assert citas_mal_atribuidas(RESPUESTA_9045, CONTEXTO_TUTELA) == []


def test_el_nombre_largo_de_una_norma_no_gana_por_palabras_genericas():
    """"Reglamentacion de la accion de tutela" empataba con "accion" y "tutela"
    del texto corrido. Solo cuenta la frase pegada al articulo."""
    from tools.rag.verificacion import _frase_de_norma

    assert _frase_de_norma("de la Constitucion permite la accion de tutela") == "la Constitucion"


# El caso 3729: "Ley 2222 de 2022" donde el contexto trae la Ley 2220 de 2022.
# Comparten el año y ninguna palabra util, asi que puntaje_norma les daba lo
# mismo y la cita equivocada se resolvia a la norma del contexto. Una norma se
# identifica por su NUMERO.

LEY_2220 = "Ley 2220 de 2022 (Estatuto de Conciliacion)"


def test_una_ley_con_otro_numero_pero_el_mismo_ano_no_se_resuelve():
    salida = citas_atribuidas("El articulo 5 de la Ley 2222 de 2022 habilita la conciliacion.",
                              [LEY_2220])

    assert salida == [("", "5")]


def test_la_ley_correcta_si_se_resuelve():
    salida = citas_atribuidas("El articulo 5 de la Ley 2220 de 2022 habilita la conciliacion.",
                              [LEY_2220])

    assert salida == [(LEY_2220, "5")]


def test_una_norma_nombrada_sin_numero_sigue_resolviendo():
    """"del Codigo General del Proceso" no nombra numero: no hay nada que
    contradecir."""
    salida = citas_atribuidas("El articulo 314 del Codigo General del Proceso.", [CGP])

    assert salida == [(CGP, "314")]


def test_un_decreto_con_otro_numero_tampoco_se_resuelve():
    salida = citas_atribuidas("El articulo 62 del Decreto 2664 de 1950 lo permite.", [CST])

    assert salida == [("", "62")]


def test_la_anafora_funciona_con_tildes():
    """El patron esta escrito sin tildes y el texto las trae: "del mismo
    codigo" empataba y "del mismo código" no, asi que toda anafora con esa
    palabra se perdia. Lo destapo el barrido sobre las 70 respuestas, en el
    caso 4226."""
    respuesta = ("El artículo 67 del Código de Procedimiento Penal obliga a denunciar, "
                 "y el artículo 68 del mismo código exime de hacerlo contra la familia.")
    cpp = "Ley 906 de 2004 (Codigo de Procedimiento Penal)"

    assert citas_atribuidas(respuesta, [cpp]) == [(cpp, "67"), (cpp, "68")]
