"""El manifiesto de M1.

Lo que protege: que el manifiesto registre el adaptador y el dataset con los
que se entreno, y que cuando se genere despues de la corrida lo diga en vez de
inventar el hardware de la maquina que lo genero.
"""
from __future__ import annotations

from tools import manifiesto_m1


def test_registra_el_dataset_con_el_que_m1_entrena():
    """No dataset_legal.jsonl: desde el 2026-10-08 M1 entrena con el combinado,
    y el hash que importa es el de lo que de verdad entro al SFT."""
    m = manifiesto_m1.construir("/no/existe")

    assert m["dataset_entrenamiento"] == "data/dataset.jsonl"
    assert m["hash_dataset_entrenamiento"] is not None
    # Ya no hay un hash aparte para v1: hay un solo dataset, y los ejemplos sin
    # contexto se sacan filtrandolo por origen. Antes eran dos archivos y habia
    # que poder distinguirlos.
    assert "hash_dataset_v1" not in m


def test_los_conteos_salen_del_archivo_y_no_de_la_sesion():
    """Asi se puede generar con la sesion de Colab ya cerrada."""
    m = manifiesto_m1.construir("/no/existe")

    assert m["n_total"] == m["n_train"] + m["n_val"]
    assert set(m["origenes"]) == {"v1", "v2", "contrastivo"}
    assert set(m["val_por_origen"]) == {"v1", "v2"}


def test_sin_hardware_se_marca_reconstruido():
    """Poner el hardware de la maquina que genera el archivo seria decir que la
    corrida ocurrio ahi. Mejor None y una nota."""
    m = manifiesto_m1.construir("/no/existe")

    assert m["hardware"] is None
    assert m["library_versions"] is None
    assert "reconstruido" in m


def test_con_hardware_no_se_marca():
    m = manifiesto_m1.construir("/no/existe", hardware="NVIDIA A100-SXM4-40GB, 40960 MiB")

    assert m["hardware"].startswith("NVIDIA A100")
    assert m["library_versions"]
    assert "reconstruido" not in m


def test_un_adaptador_que_no_esta_deja_el_hash_en_none_sin_lanzar():
    """El manifiesto describe la corrida, no puede tumbarla; y un None dice
    'no se pudo registrar', que es informacion."""
    m = manifiesto_m1.construir("/ruta/inexistente")

    assert m["hash_adaptador"] is None


def test_se_puede_armar_sin_el_stack_de_evaluacion(monkeypatch):
    """El manifiesto se genera despues de la corrida, en un runtime CPU sin nada
    instalado. Importarlo desde tools.evaluation.pipeline lo ataba a sacrebleu
    via metrics_classic y fallaba con ModuleNotFoundError justo ahi."""
    import importlib
    import sys

    for pesado in ("sacrebleu", "rouge_score", "bert_score", "torch", "transformers"):
        monkeypatch.setitem(sys.modules, pesado, None)
    for modulo in [m for m in list(sys.modules) if m.startswith("tools.")]:
        monkeypatch.delitem(sys.modules, modulo, raising=False)

    modulo = importlib.import_module("tools.manifiesto_m1")
    m = modulo.construir("/no/existe")

    # El conteo va fijo a proposito: es la guardia contra un cambio accidental
    # del dataset. Si cambia, hay que venir aqui y decir por que.
    #
    # 2709 -> 2626 el 2026-10-10, al reconstruir el contexto de los B2 con
    # `tools.dataset_v3` (REGLA_B2_V3). Salen 83 ejemplos: 78 variantes
    # contrastivas cuyo contexto traia un articulo contiguo al que se retiro
    # -- ensenaban a abstenerse con la respuesta delante -- y 11 cuya pregunta
    # es una urgencia y habrian recibido un escape sin encaminar. Seis variantes
    # nuevas se pudieron generar donde la regla vieja las descartaba.
    assert m["n_total"] == 2626
