"""El presupuesto de tokens del juez no es un detalle de rendimiento.

Con MAX_NEW_TOKENS_JUDGE=200 el juez se quedaba sin espacio a mitad del JSON y
la fila se descartaba por no parsear. Como las filas sin parsear se excluyen de
los promedios, la comparacion baseline vs. fine-tuned terminaba calculada sobre
muestras distintas (177 contra 188 de 213) y exageraba la ventaja del modelo
afinado: +0.127 sobre la interseccion contra +0.028 con los 213 casos completos.

El fallo era silencioso -- ninguna excepcion, solo un N mas chico en el
scorecard -- asi que se vigila con una prueba en vez de con memoria.
"""
from __future__ import annotations

from tools.evaluation.judge import parse_judge_output

# El juez es Groq (gpt-oss-120b), que ademas razona antes de escribir el JSON
# y ahora tambien lista los errores juridicos: necesita mas que los 512 del
# juez local que se quito. 700 es lo que usa el juez del criterio, que pide el
# mismo JSON con lista de errores.
MINIMO_SEGURO = 700


def test_el_presupuesto_del_juez_alcanza_para_cerrar_el_json():
    from tools.evaluation import external_judge

    assert external_judge.GROQ_MAX_TOKENS_JUDGE >= MINIMO_SEGURO, (
        f"GROQ_MAX_TOKENS_JUDGE={external_judge.GROQ_MAX_TOKENS_JUDGE} es menor que "
        f"{MINIMO_SEGURO}. Con 200 el juez truncaba el JSON y se perdia el "
        "17% de las filas del baseline, sesgando la comparacion."
    )


def test_los_errores_juridicos_se_leen():
    salida = (
        '{"correccion_juridica": 2, "prudencia": 4, "claridad_utilidad": 4, "concision": 5, '
        '"errores_juridicos": ["querella ante la Procuraduria: alli se presenta queja disciplinaria"], '
        '"justificacion": "ruta equivocada"}'
    )
    score = parse_judge_output(salida)
    assert score.parse_ok
    assert score.errores_juridicos == ["querella ante la Procuraduria: alli se presenta queja disciplinaria"]
    assert parse_judge_output(salida.replace('["querella', '["').replace(
        ' ante la Procuraduria: alli se presenta queja disciplinaria"]', '"]')).errores_juridicos == []


def test_una_salida_truncada_no_se_cuenta_como_valida():
    """El caso real que producia el sesgo: el juez corta a media justificacion."""
    truncada = '{"correccion_juridica": 3, "prudencia": 4, "claridad_utilidad": 3, "concision": '
    score = parse_judge_output(truncada)
    assert not score.parse_ok
    assert score.composite is None


def test_faltar_un_criterio_invalida_la_fila():
    """Otro caso observado: el juez devuelve solo parte de la rubrica.

    No se puede promediar sobre los criterios presentes, porque entonces unas
    filas se calcularian sobre 4 criterios y otras sobre 2, y dejarian de ser
    comparables entre si.
    """
    incompleta = '{"correccion_juridica": 4, "claridad_utilidad": 3}'
    score = parse_judge_output(incompleta)
    assert not score.parse_ok
    assert score.composite is None


def test_una_salida_completa_si_parsea():
    completa = (
        '{"correccion_juridica": 4, "prudencia": 5, "claridad_utilidad": 3, '
        '"concision": 4, "justificacion": "Responde con la ruta correcta."}'
    )
    score = parse_judge_output(completa)
    assert score.parse_ok
    assert score.composite == 4.0


def test_las_claves_con_tilde_siguen_reconociendose():
    """El juez a veces escribe 'concisión' con tilde aunque el prompt la pida sin."""
    con_tilde = (
        '{"correccion_juridica": 4, "prudencia": 4, "claridad_utilidad": 4, '
        '"concisión": 4, "justificacion": "ok"}'
    )
    assert parse_judge_output(con_tilde).parse_ok
