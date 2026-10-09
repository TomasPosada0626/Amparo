"""v1 + v2 + las variantes contrastivas, sin mover nada de lo que ya estaba.

Lo que protege: la comparacion entre el adaptador v1 y el v2. Si la validacion
cambia aunque sea en un registro, los numeros de v2 no se pueden poner al lado
de los de v1 y la unica forma de saber si la correccion sirvio se pierde.
"""
from __future__ import annotations

from tools.dataset_m1_v3 import construir, revisar


def reg(id_, origen, split, modo=None, base_id=None, par_de=None):
    r = {"id": id_, "origen": origen, "split": split, "modo": modo,
         "base_id": base_id, "messages": [{"role": "assistant", "content": "x" * 10}]}
    if par_de is not None:
        r["par_de"] = par_de
    return r


BASE = [reg(1, "v1", "train"), reg(2, "v1", "val"),
        reg(2001, "v2", "train", "B1", base_id=1), reg(2002, "v2", "val", "B2", base_id=2)]
VAR = [reg(6001, "contrastivo", "train", "B2", base_id=1, par_de=2001)]


def test_une_sin_recalcular_splits():
    """Recalcular el split con otra version del dataset moveria ejemplos de
    lado y la validacion dejaria de ser la de v1."""
    c = construir(BASE, VAR)

    assert len(c) == 5
    assert {r["id"]: r["split"] for r in c}[2] == "val"


def test_una_combinacion_valida_no_da_fallos():
    assert revisar(construir(BASE, VAR), BASE, VAR, n_val=None) == []


def test_atrapa_que_la_validacion_cambie():
    """El fallo que invalidaria la comparacion con v1."""
    var = [reg(6001, "contrastivo", "val", "B2", base_id=1, par_de=2001)]

    fallos = revisar(construir(BASE, var), BASE, var)

    assert any("fuera de train" in f for f in fallos)
    assert any("validacion" in f for f in fallos)


def test_atrapa_un_id_repetido():
    var = [reg(2001, "contrastivo", "train", "B2", base_id=1, par_de=2001)]

    assert any("repetidos" in f for f in revisar(construir(BASE, var), BASE, var, n_val=None))


def test_atrapa_una_variante_de_una_pregunta_en_la_validacion_de_M1():
    """base_id=2 esta en la validacion de v1: entrenarla seria medir sobre lo
    que el modelo ya vio."""
    var = [reg(6001, "contrastivo", "train", "B2", base_id=2, par_de=2001)]

    assert any("base en la validacion" in f for f in revisar(construir(BASE, var), BASE, var, n_val=None))


def test_atrapa_una_variante_sin_su_original():
    var = [reg(6001, "contrastivo", "train", "B2", base_id=1, par_de=9999)]

    assert any("sin su ejemplo original" in f for f in revisar(construir(BASE, var), BASE, var, n_val=None))


def test_atrapa_un_ejemplo_que_cambio_de_split():
    base = [reg(1, "v1", "train"), reg(2, "v1", "val"),
            reg(2001, "v2", "train", "B1", base_id=1), reg(2002, "v2", "val", "B2", base_id=2)]
    combinado = construir(base, VAR)
    combinado[0] = {**combinado[0], "split": "val"}

    assert any("cambiaron de split" in f for f in revisar(combinado, base, VAR, n_val=None))


def test_atrapa_un_ejemplo_sin_split():
    var = [reg(6001, "contrastivo", None, "B2", base_id=1, par_de=2001)]

    assert any("sin split" in f for f in revisar(construir(BASE, var), BASE, var, n_val=None))
