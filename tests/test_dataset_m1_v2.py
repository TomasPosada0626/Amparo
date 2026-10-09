"""El archivo con el que entrena M1: v1 + v2 sin mover el split de nadie.

Lo que se protege aca no es el formato, es la validez de la medicion. Si un
ejemplo de v2 cuya pregunta base quedo en la validacion de M1 se cuela a train,
la validacion deja de medir generalizacion y mide memoria -- y no hay forma de
notarlo mirando las cifras, porque salen mejores.
"""
from __future__ import annotations

from tools import dataset_m1_v2
from tools.evaluation import dataset


def _datos():
    v1 = dataset.load_records()
    v2 = dataset_m1_v2.cargar_v2()
    return v1, v2, dataset_m1_v2.construir(v1, v2)


def test_estan_todos_los_ejemplos_de_las_dos_fuentes():
    v1, v2, combinado = _datos()

    assert len(combinado) == len(v1) + len(v2)


def test_cada_ejemplo_dice_de_donde_viene_y_a_que_lado_cae():
    _, _, combinado = _datos()

    assert {r["origen"] for r in combinado} == {"v1", "v2"}
    assert {r["split"] for r in combinado} == {"train", "val"}


def test_los_ids_de_v1_y_v2_no_chocan():
    """v1 va de 1 a 1536 y v2 arranca en 2001. Un id repetido haria que dos
    ejemplos distintos se pisaran al indexar por id."""
    _, _, combinado = _datos()
    ids = [r["id"] for r in combinado]

    assert len(ids) == len(set(ids))


def test_ningun_ejemplo_de_v2_entrena_con_una_pregunta_que_esta_en_la_validacion():
    """La fuga que importa: la misma pregunta sin contexto en train y con
    contexto en val haria que val midiera memoria."""
    v1, _, combinado = _datos()
    _, val_v1 = dataset.stratified_split(v1)
    ids_val = {r["id"] for r in val_v1}

    fuga = [r["id"] for r in combinado
            if r["origen"] == "v2" and r["split"] == "train" and r.get("base_id") in ids_val]

    assert fuga == []


def test_el_split_de_v1_queda_intacto():
    """Si v1 cambia de lado, las cifras dejan de ser comparables con la corrida
    de M2 del 2026-10-06, que es la linea base."""
    v1, _, combinado = _datos()
    _, val_v1 = dataset.stratified_split(v1)
    esperado = {r["id"] for r in val_v1}

    quedaron = {r["id"] for r in combinado if r["origen"] == "v1" and r["split"] == "val"}

    assert quedaron == esperado


def test_revisar_detecta_un_ejemplo_sin_split():
    v1, v2, combinado = _datos()
    roto = [dict(r) for r in combinado]
    roto[0].pop("split")

    assert any("sin split" in f for f in dataset_m1_v2.revisar(roto, v1, v2))


def test_revisar_detecta_ids_repetidos():
    v1, v2, combinado = _datos()
    roto = [dict(r) for r in combinado]
    roto[-1] = {**roto[-1], "id": roto[0]["id"]}

    assert any("repetidos" in f for f in dataset_m1_v2.revisar(roto, v1, v2))
