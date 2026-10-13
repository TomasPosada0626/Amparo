"""H6: el cargador compartido de M2 y M3 fija la revision del modelo base.

Sin GPU ni descarga: `torch` y `transformers` se sustituyen por dobles que
registran con que argumentos se les llamo.
"""
from __future__ import annotations

import sys
import types

import pytest

from tools.evaluation import config, generation


@pytest.fixture
def llamadas(monkeypatch):
    registro = {}

    class _Tok:
        pad_token = None
        eos_token = "<eos>"

        @classmethod
        def from_pretrained(cls, model_id, **kw):
            registro["tokenizer"] = (model_id, kw)
            return cls()

    class _Modelo:
        def eval(self):
            return self

        @classmethod
        def from_pretrained(cls, model_id, **kw):
            registro["modelo"] = (model_id, kw)
            return cls()

    tr = types.ModuleType("transformers")
    tr.AutoTokenizer = _Tok
    tr.AutoModelForCausalLM = _Modelo
    tr.BitsAndBytesConfig = lambda **kw: kw
    torch = types.ModuleType("torch")
    torch.bfloat16 = "bfloat16"
    monkeypatch.setitem(sys.modules, "transformers", tr)
    monkeypatch.setitem(sys.modules, "torch", torch)
    return registro


def test_la_revision_es_la_de_v1():
    from tools.evaluation.reevaluacion_v1 import REVISION_V1

    assert config.BASE_MODEL_REVISION == REVISION_V1 == "a09a35458c702b33eeacc393d103063234e8bc28"


def test_por_defecto_fija_la_revision_en_tokenizer_y_modelo(llamadas):
    generation.load_base_model()
    for parte in ("tokenizer", "modelo"):
        model_id, kw = llamadas[parte]
        assert model_id == config.BASE_MODEL_ID
        assert kw["revision"] == config.BASE_MODEL_REVISION, parte


def test_el_rag_carga_con_la_misma_revision(llamadas):
    """S08 y S10 cargan por `pipeline.load_model`, que reusa este cargador."""
    from tools.rag import pipeline

    pipeline.load_model(use_lora=False)
    assert llamadas["modelo"][1]["revision"] == config.BASE_MODEL_REVISION


def test_otro_modelo_no_hereda_la_revision_de_qwen(llamadas):
    with pytest.raises(ValueError, match="pasa la suya"):
        generation.load_base_model("otro/modelo")
    generation.load_base_model("otro/modelo", revision=None)
    assert llamadas["modelo"][1]["revision"] is None
