"""Saber si una respuesta termino o se corto.

El caso que motiva estas pruebas: en Qwen2.5-Instruct el token que cierra el
turno es `<|im_end|>`, y `tokenizer.eos_token_id` apunta a `<|endoftext|>`, que
el modelo instruido casi nunca emite. Si se mira solo el eos del tokenizer,
practicamente todas las respuestas salen marcadas como cortadas y la metrica
miente en silencio.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from tools.evaluation.fin_de_generacion import ids_de_fin, resumen, se_corto

IM_END = 151645
ENDOFTEXT = 151643
UNK = 0


class TokenizerFalso:
    """Como Qwen2.5-Instruct: el eos es <|endoftext|>, no <|im_end|>."""

    eos_token_id = ENDOFTEXT
    unk_token_id = UNK

    def __init__(self, conocidos=None):
        self._conocidos = conocidos if conocidos is not None else {
            "<|im_end|>": IM_END, "<|endoftext|>": ENDOFTEXT}

    def convert_tokens_to_ids(self, nombre):
        return self._conocidos.get(nombre, UNK)


def modelo(eos):
    return SimpleNamespace(generation_config=SimpleNamespace(eos_token_id=eos))


# --- de donde salen los ids de fin -------------------------------------------

def test_encuentra_im_end_aunque_el_eos_del_tokenizer_sea_otro():
    """El fallo que estas pruebas existen para impedir."""
    ids = ids_de_fin(TokenizerFalso(), modelo([ENDOFTEXT, IM_END]))

    assert IM_END in ids
    assert ENDOFTEXT in ids


def test_lo_encuentra_por_nombre_si_la_configuracion_no_lo_trae():
    """Sin generation_config, el nombre <|im_end|> sigue resolviendo."""
    ids = ids_de_fin(TokenizerFalso(), None)

    assert IM_END in ids


def test_la_configuracion_puede_traer_un_solo_id_en_vez_de_una_lista():
    assert IM_END in ids_de_fin(TokenizerFalso({}), modelo(IM_END))


def test_un_token_desconocido_no_se_toma_como_fin():
    """convert_tokens_to_ids devuelve el id de <unk> para lo que no conoce;
    tomarlo como fin marcaria respuestas terminadas donde no lo estan."""
    ids = ids_de_fin(TokenizerFalso({}), None)

    assert UNK not in ids


def test_sin_nada_de_donde_sacarlo_el_conjunto_queda_vacio():
    """Y quien llama tiene que comprobarlo: un conjunto vacio haria que todas
    las respuestas salieran cortadas."""
    vacio = SimpleNamespace(eos_token_id=None, unk_token_id=None)

    assert ids_de_fin(vacio, None) == set()


# --- la deteccion ------------------------------------------------------------

def test_una_respuesta_que_termina_normal_no_esta_cortada():
    assert se_corto([100, 200, 300, IM_END], {IM_END, ENDOFTEXT}) is False


def test_una_respuesta_que_agota_el_presupuesto_si_esta_cortada():
    """900 tokens y ninguno de fin: el modelo nunca cerro el turno."""
    tokens = list(range(1000, 1900))

    assert len(tokens) == 900
    assert se_corto(tokens, {IM_END, ENDOFTEXT}) is True


def test_terminar_exactamente_en_el_tope_no_es_truncamiento():
    """El falso positivo de contar tokens: n == max pero el ultimo es de fin."""
    tokens = [*range(1000, 1899), IM_END]

    assert len(tokens) == 900
    assert se_corto(tokens, {IM_END, ENDOFTEXT}) is False


def test_una_respuesta_vacia_cuenta_como_cortada():
    """El modelo no produjo nada, y desde luego no cerro el turno."""
    assert se_corto([], {IM_END}) is True


def test_sin_ids_de_fin_falla_en_vez_de_mentir():
    with pytest.raises(ValueError, match="tokens de fin"):
        se_corto([1, 2, 3], set())


def test_solo_cuenta_el_ultimo_token():
    """Un <|im_end|> en el medio no cierra la respuesta."""
    assert se_corto([IM_END, 200, 300], {IM_END}) is True


# --- el resumen --------------------------------------------------------------

def test_el_resumen_separa_cortada_de_presupuesto_agotado():
    """Las dos cifras no son la misma, y cuando difieren la diferencia informa."""
    registros = [
        {"id": 1, "cortada": False, "presupuesto_agotado": False},
        {"id": 2, "cortada": True, "presupuesto_agotado": True},
        {"id": 3, "cortada": True, "presupuesto_agotado": False},
        {"id": 4, "cortada": False, "presupuesto_agotado": True},
    ]

    r = resumen(registros)

    assert r["n"] == 4
    assert r["cortadas"] == 2
    assert r["presupuesto_agotado"] == 2
    assert r["cortadas_sin_agotar"] == 1
    assert r["agotadas_sin_cortarse"] == 1
    assert r["ids_cortadas"] == [2, 3]


def test_sin_cortadas_el_resumen_conserva_el_denominador():
    r = resumen([{"id": i, "cortada": False, "presupuesto_agotado": False}
                 for i in range(334)])

    assert (r["n"], r["cortadas"]) == (334, 0)


# --- por que paro, cuando se puede determinar --------------------------------
#
# `se_corto` responde si/no, que es lo que necesita la metrica, pero una salida
# vacia y una que agoto el presupuesto se arreglan distinto -- la primera es un
# fallo de generacion, la segunda un techo mal puesto -- y las dos dan True.

from tools.evaluation.fin_de_generacion import (  # noqa: E402
    PARO_SIN_CERRAR,
    PRESUPUESTO_AGOTADO,
    SIN_SALIDA,
    TERMINO,
    motivo,
)


def test_una_respuesta_completa_dice_que_termino():
    assert motivo([1, 2, IM_END], {IM_END}, 900) == TERMINO


def test_una_salida_vacia_no_se_confunde_con_truncamiento():
    """El modelo no produjo nada: no llego al limite, fallo en otra parte."""
    assert motivo([], {IM_END}, 900) == SIN_SALIDA


def test_agotar_el_presupuesto_se_distingue():
    assert motivo(list(range(900)), {IM_END}, 900) == PRESUPUESTO_AGOTADO


def test_parar_sin_cerrar_ni_agotar_es_un_motivo_propio():
    """Paro por otra razon: un stop, un error del backend."""
    assert motivo([1, 2, 3], {IM_END}, 900) == PARO_SIN_CERRAR


def test_sin_saber_el_presupuesto_no_se_inventa_que_se_agoto():
    assert motivo([1, 2, 3], {IM_END}, None) == PARO_SIN_CERRAR


def test_terminar_en_el_tope_exacto_dice_que_termino_no_que_se_agoto():
    assert motivo([*range(899), IM_END], {IM_END}, 900) == TERMINO


def test_sin_ids_de_fin_falla_en_vez_de_inventar_un_motivo():
    with pytest.raises(ValueError, match="tokens de fin"):
        motivo([1, 2, 3], set(), 900)


def test_el_resumen_reparte_por_motivo():
    registros = [
        {"id": 1, "cortada": False, "presupuesto_agotado": False, "motivo": TERMINO},
        {"id": 2, "cortada": True, "presupuesto_agotado": True, "motivo": PRESUPUESTO_AGOTADO},
        {"id": 3, "cortada": True, "presupuesto_agotado": False, "motivo": SIN_SALIDA},
    ]

    r = resumen(registros)

    assert r["por_motivo"] == {TERMINO: 1, SIN_SALIDA: 1, PRESUPUESTO_AGOTADO: 1}


def test_los_registros_sin_motivo_no_inventan_categorias():
    """Los de v1 no lo traen: el reparto sale vacio en vez de fabricarlo."""
    r = resumen([{"id": 1, "cortada": False, "presupuesto_agotado": False}])

    assert r["por_motivo"] == {}
