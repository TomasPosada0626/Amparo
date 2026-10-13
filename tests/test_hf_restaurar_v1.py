"""Restauracion de v1 en Hugging Face (tools/hf_restaurar_v1.py).

Solo la parte que no necesita red: la comprobacion de huella, que es la que
impide subir a `main` otra cosa creyendo que es v1.
"""
from __future__ import annotations

import pytest

from tools import hf_restaurar_v1 as H
from tools.evaluation import config

ADAPTADOR_V1 = config.PROJECT_ROOT / "artifacts" / "amparo-lora-adapter"
ADAPTADOR_V2 = config.PROJECT_ROOT / "artifacts" / "amparo-lora-adapter-v2"


def test_la_huella_de_v1_es_la_de_produccion():
    """Las dos herramientas tienen que hablar del mismo v1."""
    from tools.evaluation.reevaluacion_v1 import HUELLA_ADAPTADOR_V1

    assert H.HUELLA_V1 == HUELLA_ADAPTADOR_V1 == "8ce3cc2bc9306974"


def test_rechaza_un_adaptador_que_no_es_v1(tmp_path):
    (tmp_path / "adapter_model.safetensors").write_bytes(b"otros pesos")
    with pytest.raises(SystemExit, match="No se sube nada"):
        H.verificar_v1(tmp_path)


def test_rechaza_una_carpeta_sin_adaptador(tmp_path):
    with pytest.raises(SystemExit, match="no hay adapter_model.safetensors"):
        H.verificar_v1(tmp_path)


@pytest.mark.skipif(not ADAPTADOR_V1.exists(), reason="sin el adaptador v1 local")
def test_acepta_v1():
    assert H.verificar_v1(ADAPTADOR_V1) == H.HUELLA_V1


@pytest.mark.skipif(not ADAPTADOR_V2.exists(), reason="sin el adaptador v2 local")
def test_rechaza_v2():
    """v2 estuvo en `main` del 10 al 12 de octubre sin que nadie lo adoptara."""
    with pytest.raises(SystemExit, match="v2"):
        H.verificar_v1(ADAPTADOR_V2)
