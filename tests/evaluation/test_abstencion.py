"""Abstenerse y acotar una duda no son lo mismo.

`es_valvula_de_escape` busca subcadena, asi que marca igual una respuesta que
se niega a orientar y una que orienta y solo acota lo que no puede afirmar. Con
esa medicion, la tasa de escape en gold de la corrida del 2026-10-09 salia 0.60
y el diagnostico fue "el modelo sobre-abstiene". Separadas, las abstenciones de
verdad eran 8 de 45 (0.18) y en adversariales 20 de 30: el modelo si
discrimina, y la subcadena lo escondia.
"""
from __future__ import annotations

from tools.evaluation.ragas_metrics import es_abstencion_pura, es_valvula_de_escape

# El caso 9002 de la corrida del 2026-10-09: cita el articulo que responde,
# acota como se valoran las causales, y orienta a reunir pruebas.
ORIENTA_Y_ACOTA = (
    "El articulo 62 del Codigo Sustantivo del Trabajo permite terminar el contrato "
    "cuando el empleador incumple sistematicamente sus obligaciones. No tengo "
    "informacion verificada sobre como se valoran esas causales en un despido por "
    "presion. Reune el acta, mensajes y testigos."
)
ABSTENCION = (
    "No tengo informacion verificada sobre esto en mi base de conocimiento. "
    "Te sugiero consultar un consultorio juridico universitario."
)
ORIENTA = "El articulo 20 de la Ley 820 de 2003 limita el reajuste anual."


def test_una_respuesta_que_orienta_y_acota_no_es_abstencion():
    assert es_abstencion_pura(ORIENTA_Y_ACOTA) is False


def test_pero_si_contiene_la_frase_de_escape():
    """Por eso la metrica vieja la contaba como escape."""
    assert es_valvula_de_escape(ORIENTA_Y_ACOTA) is True


def test_negarse_a_orientar_si_es_abstencion():
    assert es_abstencion_pura(ABSTENCION) is True


def test_orientar_sin_la_frase_no_es_abstencion():
    assert es_abstencion_pura(ORIENTA) is False
    assert es_valvula_de_escape(ORIENTA) is False


def test_la_frase_con_tilde_tambien_cuenta():
    """El modelo escribe 'informacion' con tilde; contarla sin tilde daba 8 de
    45 en vez de 27."""
    assert es_valvula_de_escape("No tengo información verificada sobre esto.") is True


def test_la_metrica_vieja_no_cambia():
    """Define `respuestas_escape` y el denominador de faithfulness en los
    scorecards ya publicados: moverla los volveria incomparables."""
    assert es_valvula_de_escape(ABSTENCION) is True
    assert es_valvula_de_escape("") is False
    assert es_valvula_de_escape(None) is False


def test_sin_respuesta_no_hay_abstencion():
    assert es_abstencion_pura("") is False
    assert es_abstencion_pura(None) is False
