"""Tests de los modulos que salieron de los notebooks y comparten varios
pipelines: publicacion, predicciones, entorno, datos y generacion de M1.

Sin GPU y sin modelos: tokenizer y modelo son dobles. La generacion usa
tensores reales de torch (CPU) porque es lo que manipula el codigo.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from amparo.ejecucion import entorno, publicacion
from amparo.evaluacion import predicciones
from amparo.finetuning import datos, generacion
from amparo.nucleo import schema


# --------------------------------------------------------------------------
# publicacion
# --------------------------------------------------------------------------
class CorridaFalsa:
    def __init__(self, carpeta: Path):
        self.dir = carpeta
        self.artefactos = {}
        self.publicados = []

    def publicar(self, nombre, destino):
        self.publicados.append((nombre, destino))


def test_publicar_todo_publica_solo_si_estan_todos(tmp_path, capsys):
    c = CorridaFalsa(tmp_path)
    (tmp_path / "a.json").write_text("{}")
    c.artefactos["b"] = "b.csv"
    (tmp_path / "b.csv").write_text("x")
    publicacion.publicar_todo(c, [("a", "results/a.json"), ("b", "results/b.csv")])
    assert c.publicados == [("a", "results/a.json"), ("b", "results/b.csv")]


def test_publicar_todo_no_publica_nada_si_falta_uno_y_dice_quien_lo_genera(tmp_path, capsys):
    c = CorridaFalsa(tmp_path)
    (tmp_path / "a.json").write_text("{}")
    with pytest.raises(RuntimeError, match="faltan 1 artefactos: b"):
        publicacion.publicar_todo(c, [("a", "results/a.json"), ("b", "results/b.json")],
                                  {"b": "la seccion 7"})
    assert c.publicados == []
    assert "lo genera -> la seccion 7" in capsys.readouterr().out


# --------------------------------------------------------------------------
# predicciones
# --------------------------------------------------------------------------
def _salida(mec="tutela"):
    return schema.render_salida({"derecho": "salud", "accionado": "EPS", "mecanismo": mec,
                                 "procede": True, "razon": "r", "pretension": "p"})


def test_cargar_m1_desenvuelve_datos_y_conserva_la_corrida(tmp_path):
    ruta = tmp_path / "m1_predicciones.json"
    preds = [{"id": "a", "base": _salida(), "finetuned": _salida()}]
    ruta.write_text(json.dumps({"_corrida": "20261018T000000Z", "datos": preds}), encoding="utf-8")
    got, corrida = predicciones.cargar_m1(ruta, eval_set=[{"id": "a"}])
    assert got == preds and corrida == "20261018T000000Z"


def test_cargar_m1_exige_el_mismo_orden_que_el_eval_set(tmp_path):
    ruta = tmp_path / "p.json"
    ruta.write_text(json.dumps([{"id": "a"}, {"id": "b"}]), encoding="utf-8")
    with pytest.raises(AssertionError, match="orden"):
        predicciones.cargar_m1(ruta, eval_set=[{"id": "b"}, {"id": "a"}])


def test_recortar_quita_la_cola_degenerada():
    sucia = _salida() + "\n<|im_start|>user\n锟斤拷"
    base, ft = predicciones.recortar([{"base": sucia, "finetuned": _salida()}])
    assert base == [schema.recortar_al_bloque(sucia)[0]] and ft == [_salida()]


# --------------------------------------------------------------------------
# entorno
# --------------------------------------------------------------------------
def test_cargar_clave_groq_respeta_la_del_entorno(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "ya-estaba")
    assert entorno.cargar_clave_groq() is True


def test_cargar_clave_groq_fuera_de_colab_y_sin_pedir_devuelve_false(monkeypatch, capsys):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert entorno.cargar_clave_groq(pedir_por_teclado=False) is False


# --------------------------------------------------------------------------
# datos (M1)
# --------------------------------------------------------------------------
class TokFalso:
    """Tokenizer de juguete: un id por caracter, plantilla de chat textual."""
    eos_token = "<eos>"
    eos_token_id = 0
    pad_token_id = 1
    unk_token_id = 2
    padding_side = "right"

    def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=True):
        t = "".join(f"[{m['role']}]{m['content']}" for m in msgs) + "[assistant]"
        return list(range(len(t))) if tokenize else t

    def __call__(self, texto, add_special_tokens=False, truncation=False, max_length=None,
                 return_tensors=None, padding=False):
        if isinstance(texto, list):
            import torch
            ids = [[10 + (ord(ch) % 50) for ch in t] for t in texto]
            m = max(map(len, ids))
            ids = [[self.pad_token_id] * (m - len(x)) + x for x in ids]
            return _Enc({"input_ids": torch.tensor(ids)})
        ids = [10 + (ord(ch) % 50) for ch in texto]
        if truncation and max_length:
            ids = ids[:max_length]
        if return_tensors == "pt":
            import torch
            return _Enc({"input_ids": torch.tensor([ids])})
        return {"input_ids": ids}

    def convert_tokens_to_ids(self, marca):
        return {"<|im_end|>": 5, "<|im_start|>": 6}.get(marca, self.unk_token_id)

    def decode(self, ids, skip_special_tokens=True):
        return "".join(chr(97 + (int(i) % 26)) for i in ids)


class _Enc(dict):
    def to(self, _device):
        return self


EJ = {"id": "x1", "relato": "Me niegan un medicamento", "derecho": "salud", "accionado": "EPS",
      "mecanismo": "tutela", "procede": True, "razon": "r", "pretension": "p"}


def test_sistema_trae_la_guia_de_derechos_vecinos():
    assert schema.GUIA_DERECHOS_VECINOS in datos.SISTEMA


def test_construir_enmascara_el_prompt_y_no_trunca_con_max_len_medido():
    tok = TokFalso()
    max_len, largos = datos.medir_max_len([EJ], tok)
    assert max_len == max(largos) + 8
    ej = datos.construir(EJ, tok, max_len)
    prompt = tok.apply_chat_template(datos.mensajes(EJ), tokenize=False)
    n_prompt = len(tok(prompt)["input_ids"])
    assert ej["labels"][:n_prompt] == [-100] * n_prompt
    assert all(l != -100 for l in ej["labels"][n_prompt:])
    assert len(ej["input_ids"]) == largos[0]          # nada truncado


def test_collate_rellena_a_la_derecha_con_pad_0_y_menos_100():
    collate = datos.collate_para(TokFalso())
    out = collate([{"input_ids": [7, 8], "attention_mask": [1, 1], "labels": [-100, 8]},
                   {"input_ids": [9], "attention_mask": [1], "labels": [9]}])
    assert out["input_ids"].tolist() == [[7, 8], [9, 1]]
    assert out["attention_mask"].tolist() == [[1, 1], [1, 0]]
    assert out["labels"].tolist() == [[-100, 8], [9, -100]]


# --------------------------------------------------------------------------
# generacion (M1 y M3)
# --------------------------------------------------------------------------
def test_ids_parada_incluye_eos_y_marcas_de_turno():
    assert generacion.ids_parada(TokFalso()) == [0, 5, 6]


class ModeloFalso:
    """`generate` devuelve la entrada mas 3 tokens fijos; registra kwargs."""
    device = "cpu"

    def __init__(self):
        self.llamadas, self.adaptador_apagado = [], False

    def eval(self):
        return self

    def generate(self, input_ids, max_new_tokens, do_sample, eos_token_id, pad_token_id, use_cache):
        import torch
        self.llamadas.append({"max_new_tokens": max_new_tokens, "do_sample": do_sample,
                              "eos": eos_token_id, "apagado": self.adaptador_apagado})
        cola = torch.tensor([[11, 12, 13]] * input_ids.shape[0])
        return torch.cat([input_ids, cola], dim=1)

    def disable_adapter(self):
        import contextlib
        modelo = self

        @contextlib.contextmanager
        def ctx():
            modelo.adaptador_apagado = True
            try:
                yield
            finally:
                modelo.adaptador_apagado = False
        return ctx()


def test_generar_lote_es_greedy_con_padding_izquierdo_y_lo_restaura():
    tok, mdl = TokFalso(), ModeloFalso()
    sal = generacion.generar_lote(mdl, tok, [EJ, EJ, EJ], datos.mensajes,
                                  parada=[0, 5], lote=2, max_new=50)
    assert len(sal) == 3 and all(s == "lmn" for s in sal)   # solo los tokens nuevos
    assert [l["max_new_tokens"] for l in mdl.llamadas] == [50, 50]
    assert all(l["do_sample"] is False and l["eos"] == [0, 5] for l in mdl.llamadas)
    assert tok.padding_side == "right"


def test_generador_hf_cuenta_tokens_y_apaga_el_adaptador_si_se_pide():
    tok, mdl = TokFalso(), ModeloFalso()
    gen = generacion.generador_hf(mdl, tok, max_new=320, con_adaptador=False)
    assert gen("sistema", "usuario") == "lmn"
    assert mdl.llamadas[0]["apagado"] is True and mdl.llamadas[0]["max_new_tokens"] == 320
    entrada, salida = gen.ultimos_tokens
    assert salida == 3 and entrada > 0


def test_generador_hf_recorta_la_cola_y_anota_el_caso(monkeypatch):
    tok, mdl = TokFalso(), ModeloFalso()
    monkeypatch.setattr(schema, "recortar_al_bloque", lambda t: ("recortado", True))
    recortes = []
    gen = generacion.generador_hf(mdl, tok, recortar=True, recortes=recortes)
    assert gen("s", "un relato largo") == "recortado"
    assert recortes == ["un relato largo"]
