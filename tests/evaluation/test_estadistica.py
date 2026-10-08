from tools.evaluation.estadistica import diferencia_pareada, proporcion


def test_diferencia_pareada_detecta_una_mejora_clara():
    a = [3.0] * 50
    b = [4.0] * 25 + [3.5] * 25
    iv = diferencia_pareada(a, b)
    assert iv.valor == 0.75 and iv.significativo and iv.n == 50


def test_diferencia_pareada_ruido_no_es_significativo():
    a = [3, 4, 3, 4, 3, 4, 3, 4, 3, 4] * 3
    b = [4, 3, 4, 3, 4, 3, 4, 3, 3, 4] * 3
    iv = diferencia_pareada(a, b)
    assert not iv.significativo and iv.bajo < 0 < iv.alto


def test_diferencia_pareada_ignora_faltantes_y_es_reproducible():
    a = [1.0, None, 2.0, 3.0]
    b = [2.0, 5.0, None, 4.0]
    iv = diferencia_pareada(a, b)
    assert iv.n == 2 and iv.valor == 1.0
    assert diferencia_pareada(a, b) == iv
    assert diferencia_pareada([1.0], [2.0]) is None


def test_proporcion_wilson_se_queda_en_0_1():
    iv = proporcion(50, 50)
    assert iv.valor == 1.0 and iv.alto == 1.0 and 0.9 < iv.bajo < 1.0
    iv = proporcion(3, 6)
    assert iv.bajo < 0.5 < iv.alto and iv.alto - iv.bajo > 0.5   # con 6 casos, casi no hay informacion
    assert proporcion(0, 0) is None
