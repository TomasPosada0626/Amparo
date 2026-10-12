"""Sobreabstencion en gold (C6): el resumen y la comparacion, en CPU."""
from tools.evaluation import sobreabstencion_gold as sg
from tools.evaluation.ragas_metrics import es_abstencion_pura
from tools.rag.prompt_template import RESPUESTA_ESCAPE_POR_CODIGO


def _f(i, abst, escape=None):
    return {"id": i, "abstencion_pura": abst, "verificacion": {"escape_por_codigo": escape}}


def test_el_escape_por_codigo_cuenta_como_abstencion():
    assert es_abstencion_pura(RESPUESTA_ESCAPE_POR_CODIGO)


def test_separa_el_origen_de_cada_abstencion():
    filas = [_f(1, True, "sin_contexto"), _f(2, True, "citas_no_verificables"),
             _f(3, True), _f(4, False), _f(5, False)]
    r = sg.resumir(filas)
    assert r["abstencion_pura"] == "3/5"
    assert r["por_origen"] == {"sin_contexto": 1, "citas_no_verificables": 1, "modelo": 1}
    assert r["ids_abstencion"] == [1, 2, 3]


def test_el_umbral_d3_es_tres_de_45():
    assert sg.resumir([_f(i, i < 3) for i in range(45)])["cumple_d3"]
    assert not sg.resumir([_f(i, i < 4) for i in range(45)])["cumple_d3"]


def test_una_respuesta_no_tiene_origen():
    assert sg.origen_abstencion(_f(1, False, "sin_contexto")) is None


def test_comparar_es_pareado_por_id():
    a = [_f(1, True), _f(2, False), _f(3, True)]
    b = [_f(1, True), _f(2, True), _f(3, False), _f(9, True)]
    c = sg.comparar(a, b)
    assert c == {"n_comunes": 3, "solo_a": [3], "solo_b": [2], "ambos": [1]}
