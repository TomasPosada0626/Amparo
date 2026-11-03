"""Tests del pipeline de M1 (amparo/pipelines/m1_finetuning.py) y de
amparo/finetuning/entrenamiento.py.

LO QUE NO SE EJECUTA AQUI, y queda sin probar hasta correr en Colab con GPU:
cargar Qwen2.5-7B (`cargar_modelo`), aplicar LoRA de verdad
(`aplicar_lora`), el `Trainer` y el entrenamiento (`configurar_entrenamiento`,
`entrenar`), la generacion real (`baseline`, `evaluar_ajustado` con el modelo),
la sonda y el brazo hibrido con el modelo, y la redaccion contra Groq.

Lo que SI se prueba: todo lo que no necesita GPU ni red, con dobles cuando la
etapa toca el modelo (generacion falsa con salidas reales de
`schema.render_salida`, corrida falsa, modelo falso que guarda pesos).
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import re
from pathlib import Path

import pytest

from amparo.config import RAIZ
from amparo.ejecucion import arranque
from amparo.finetuning import entrenamiento
from amparo.nucleo import schema
from amparo.pipelines import m1_finetuning as m1


# --------------------------------------------------------------------------
# Dobles
# --------------------------------------------------------------------------
class CorridaFalsa:
    def __init__(self, carpeta: Path, ident="20261101T000000Z"):
        self.dir = carpeta
        self.id = ident
        self.meta = {"datos": {"dataset.json": "v3.5.0"}, "codigo": {"_conjunto": "abc"},
                     "hardware": {"gpu": "A100"}, "determinismo": {"x": 1}}
        self.guardados, self.publicados, self.registrados = {}, [], {}
        self.meta_escrita = 0

    def guardar_json(self, nombre, obj):
        self.guardados[nombre] = obj
        (self.dir / f"{nombre}.json").write_text(json.dumps(obj, default=str), encoding="utf-8")

    def publicar(self, nombre, destino):
        assert nombre in self.guardados, f"publica {nombre} sin haberlo guardado"
        self.publicados.append((nombre, destino))

    def registrar(self, clave, valor):
        self.registrados[clave] = valor

    def ruta_cache(self, nombre):
        return str(self.dir / nombre)

    def _escribir_meta(self):
        self.meta_escrita += 1

    def cerrar(self, valida, notas=None):
        return {"valida": valida, "notas": notas}


def _salida(mec="tutela", procede=True):
    return schema.render_salida({"derecho": "salud", "accionado": "EPS", "mecanismo": mec,
                                 "procede": procede, "razon": "r", "pretension": "p"})


@pytest.fixture
def ctx(tmp_path):
    return m1.Contexto(c=CorridaFalsa(tmp_path))


# --------------------------------------------------------------------------
# Datos y splits (celda 15): con los datos REALES del repo
# --------------------------------------------------------------------------
def test_cargar_datos_reales_sin_fuga(ctx, capsys):
    m1.cargar_datos(ctx)
    assert ctx.train_raw and ctx.val_raw and ctx.eval_raw
    assert "train" in capsys.readouterr().out


def test_comprobar_splits_detecta_fuga_por_id_y_por_relato():
    train = schema.cargar("train")
    val = schema.cargar("validation")
    evals = schema.cargar(archivo="eval_set_v3.json")
    # Un id del train repetido en el eval lo caza ya `schema.validar` (id
    # duplicado), antes que la comprobacion de fuga: las dos paran la corrida.
    fuga_id = [dict(evals[0], id=train[0]["id"])] + evals[1:]
    with pytest.raises(AssertionError, match="FUGA: el eval set|id duplicado"):
        m1.comprobar_splits(train, val, fuga_id)
    fuga_relato = [dict(evals[0], relato=train[0]["relato"])] + evals[1:]
    with pytest.raises(AssertionError, match="FUGA: relato"):
        m1.comprobar_splits(train, val, fuga_relato)


# --------------------------------------------------------------------------
# Nivel 1 y 2 (celdas 10 y 12)
# --------------------------------------------------------------------------
def test_cobertura_clasificador_se_guarda(ctx):
    cc = m1.cobertura_clasificador(ctx)
    assert ctx.c.guardados["cobertura_clasificador"] == cc
    assert 0 < cc["cobertura_clasificador"] < 1


class TokFert:
    vocab_size = 1000

    def __call__(self, texto):
        return {"input_ids": list(range(len(texto.split()) * 2))}


def test_medir_fertilidad_ordena_y_registra_errores():
    def cargar(mid):
        if "bert" in mid:
            raise OSError("sin red")
        return TokFert()
    filas = m1.medir_fertilidad(["uno dos", "tres"], m1.CANDIDATOS_FERTILIDAD, cargar)
    ok = [f for f in filas if f["fertilidad"] is not None]
    assert all(f["fertilidad"] == 2.0 for f in ok)
    assert filas[-1]["fertilidad"] is None and "sin red" in filas[-1]["error"]
    assert all(f["genera"] == "si" for f in ok)


def test_fertilidad_tokenizadores_guarda_el_artefacto(ctx):
    filas = m1.fertilidad_tokenizadores(ctx, cargar_tokenizer=lambda mid: TokFert())
    assert ctx.c.guardados["fertilidad_tokenizadores"] == filas
    assert {f["modelo"] for f in filas} == set(m1.CANDIDATOS_FERTILIDAD)
    bert = next(f for f in filas if "bert" in f["modelo"])
    assert bert["genera"] == "no"


# --------------------------------------------------------------------------
# Dataset (celda 16) con un tokenizer falso
# --------------------------------------------------------------------------
class TokChar:
    eos_token = "<eos>"
    pad_token_id = 1

    def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=True):
        t = "".join(f"[{m['role']}]{m['content']}" for m in msgs) + "[assistant]"
        return list(range(len(t))) if tokenize else t

    def __call__(self, texto, add_special_tokens=False, truncation=False, max_length=None):
        ids = [10 + (ord(ch) % 50) for ch in texto]
        return {"input_ids": ids[:max_length] if truncation and max_length else ids}


def test_preparar_dataset_mide_max_len_y_no_trunca(ctx):
    pytest.importorskip("datasets")
    m1.cargar_datos(ctx)
    ctx.tokenizer = TokChar()
    m1.preparar_dataset(ctx)
    assert len(ctx.ds_train) == len(ctx.train_raw) and len(ctx.ds_val) == len(ctx.val_raw)
    assert max(len(x) for x in ctx.ds_train["input_ids"]) < ctx.max_len


# --------------------------------------------------------------------------
# Baselines y ajustado con la generacion simulada (celdas 18, 20, 27)
# --------------------------------------------------------------------------
def test_baselines_y_ajustado_con_generacion_falsa(ctx, monkeypatch):
    m1.cargar_datos(ctx)
    ctx.eval_raw = ctx.eval_raw[:12]
    vistos = []

    def generar_lote(model, tok, ejemplos, construir_mensajes, *, parada, lote, max_new=200):
        vistos.append((lote, construir_mensajes(ejemplos[0])))
        # Una salida con cola degenerada: la degeneracion se mide sobre lo crudo.
        return [_salida(e["mecanismo"] or "tutela") + ("\n<|im_start|>user\n" if i == 0 else "")
                for i, e in enumerate(ejemplos)]

    monkeypatch.setattr(m1.generacion, "generar_lote", generar_lote)
    m1.baseline(ctx)
    m1.baseline_few_shot(ctx)
    m1.evaluar_ajustado(ctx)
    assert set(ctx.sc) == {"base", "base_few_shot", "finetuned"}
    assert ctx.deg["base"]["n"] >= 1                     # medida ANTES de recortar
    assert all("<|im_start|>" not in s for s in ctx.salidas["base"])   # y recortada despues
    lotes = [l for l, _ in vistos]
    assert lotes == [8, 4, 8]                              # el few-shot baja el lote a 4
    assert vistos[0][1][0]["content"] == m1.datos.SISTEMA
    assert len(vistos[1][1]) > 2                           # el few-shot lleva las demostraciones
    assert ctx.demos and not ({d["id"] for d in ctx.demos} & {e["id"] for e in ctx.eval_raw})


def test_legibles_cuenta_mecanismos_parseables():
    assert m1.legibles([_salida(), "texto sin formato", _salida("habeas_corpus")]) == 2


# --------------------------------------------------------------------------
# Entrenamiento (celdas 22-25), sin GPU
# --------------------------------------------------------------------------
def test_receta_lora_y_hiperparametros():
    assert entrenamiento.LORA["r"] == 16 and entrenamiento.LORA["lora_alpha"] == 32
    assert entrenamiento.LORA["lora_dropout"] == 0.05 and entrenamiento.LORA["bias"] == "none"
    assert entrenamiento.LORA["target_modules"] == ["q_proj", "k_proj", "v_proj", "o_proj",
                                                    "gate_proj", "up_proj", "down_proj"]
    hp = entrenamiento.hiperparametros(42)
    assert hp["learning_rate"] == 1e-4 and hp["num_train_epochs"] == 8
    assert hp["per_device_train_batch_size"] * hp["gradient_accumulation_steps"] == 8
    assert hp["gradient_checkpointing_kwargs"] == {"use_reentrant": False}
    assert hp["output_dir"] == "runs/m1-lora" and hp["seed"] == hp["data_seed"] == 42


def test_filtrar_traduce_warmup_ratio_a_pasos_y_registra_lo_omitido():
    hp = entrenamiento.hiperparametros(42)
    firma = (set(hp) - {"warmup_ratio", "data_seed"}) | {"warmup_steps", "eval_strategy"}
    filtrado, omitidos, traducidos = entrenamiento.filtrar_hiperparametros(hp, firma, n_train=123)
    assert filtrado["eval_strategy"] == "epoch" and "evaluation_strategy" not in filtrado
    por_epoca = 123 // 8
    assert filtrado["warmup_steps"] == max(1, round(por_epoca * 8 * 0.05))
    assert traducidos["warmup_ratio->warmup_steps"]["ratio"] == 0.05
    assert omitidos == {"data_seed": 42}                  # warmup_ratio no queda como omitido


def test_filtrar_usa_evaluation_strategy_en_versiones_viejas():
    hp = entrenamiento.hiperparametros(42)
    firma = set(hp) | {"evaluation_strategy"}
    filtrado, omitidos, traducidos = entrenamiento.filtrar_hiperparametros(hp, firma, 123)
    assert filtrado["evaluation_strategy"] == "epoch" and not traducidos and not omitidos


def test_seleccionar_checkpoint_documenta_la_mejor_epoca():
    log = [{"epoch": 1, "loss": 2.0}, {"epoch": 1, "eval_loss": 0.9},
           {"epoch": 2, "eval_loss": 0.694}, {"epoch": 3, "eval_loss": 0.8}]
    s = entrenamiento.seleccionar_checkpoint(log, 8)
    assert s["mejor_epoca"] == 2 and s["ultima_epoca"] == 3 and s["las_epocas_sobraban"] is True
    assert [c["epoca"] for c in s["curva_eval_loss"]] == [1, 2, 3]
    assert entrenamiento.seleccionar_checkpoint([{"loss": 1}], 8) == {
        "epocas_configuradas": 8, "curva_eval_loss": []}


class _Param:
    def __init__(self, v):
        import torch
        self.t = torch.full((2, 2), float(v))

    def detach(self):
        return self.t


class ModeloLora:
    def __init__(self, valores):
        self.valores = valores

    def named_parameters(self):
        return [(f"capa{i}.lora_B.weight", _Param(v)) for i, v in enumerate(self.valores)] + \
               [("capa0.lora_A.weight", _Param(1.0))]


def test_comprobar_lora_b():
    pytest.importorskip("torch")
    assert entrenamiento.comprobar_lora_b(ModeloLora([0.0, 0.5])) == (1, 2)
    with pytest.raises(AssertionError, match="siguen en CERO"):
        entrenamiento.comprobar_lora_b(ModeloLora([0.0, 0.0]))
    with pytest.raises(AssertionError, match="no hay tensores lora_B"):
        entrenamiento.comprobar_lora_b(_SinLora())


class _SinLora:
    def named_parameters(self):
        return [("x.weight", _Param(1.0))]


def test_graficar_perdida_guarda_la_imagen(tmp_path):
    pytest.importorskip("matplotlib")
    log = [{"epoch": 1, "loss": 2.0}, {"epoch": 1, "eval_loss": 0.9}, {"epoch": 2, "eval_loss": 0.7}]
    mejor = entrenamiento.graficar_perdida(log, tmp_path / "loss.png", mostrar=False)
    assert (tmp_path / "loss.png").exists() and mejor == (2, 0.7)


class LoraConfigFalsa:
    r, lora_alpha, lora_dropout = 16, 32, 0.05
    target_modules = {"q_proj"}


def test_registro_hiperparametros_no_incluye_output_dir():
    reg = entrenamiento.registro_hiperparametros(
        modelo_base="Qwen", semilla=42, max_len=700, lora_config=LoraConfigFalsa(),
        hp={"output_dir": "runs/m1-lora", "num_train_epochs": 8, "metric_for_best_model": "eval_loss"},
        omitidos={}, traducidos={}, parada=["cb"], splits={"train": 1}, versiones={"torch": "x"})
    assert "output_dir" not in reg["entrenamiento"]
    assert reg["early_stopping"] == {"activo": True, "paciencia": 2, "metrica": "eval_loss",
                                     "techo_epocas": 8}
    assert reg["lora"]["target_modules"] == ["q_proj"]


class ModeloQueGuarda:
    def save_pretrained(self, ruta):
        (Path(ruta) / "adapter_model.safetensors").write_bytes(b"pesos-de-prueba")


class TokQueGuarda:
    def save_pretrained(self, ruta):
        (Path(ruta) / "tokenizer.json").write_text("{}")


def test_guardar_adaptador_versiona_y_apunta_cual_es(tmp_path):
    ficha = entrenamiento.guardar_adaptador(ModeloQueGuarda(), TokQueGuarda(), tmp_path / "models",
                                            "20261101T000000Z", tmp_path)
    assert ficha["ruta"] == "models/m1-adaptador-20261101T000000Z"
    assert ficha["huella_pesos"] == hashlib.sha256(b"pesos-de-prueba").hexdigest()[:16]
    assert ficha["bytes"] == len(b"pesos-de-prueba")
    cual = (tmp_path / "models" / "m1-adaptador" / "CUAL_ES.txt").read_text(encoding="utf-8")
    assert "m1-adaptador-20261101T000000Z" in cual and ficha["huella_pesos"] in cual


# --------------------------------------------------------------------------
# Brazo hibrido (celda 32): guardas con un sistema falso
# --------------------------------------------------------------------------
def test_resumen_sonda():
    fallos = [{"salida": "x" * 900, "chars": 900, "empieza": "{", "cierra": True},
              {"salida": "y", "chars": 1, "empieza": "y", "cierra": False}]
    r = m1.resumen_sonda(fallos, 10)
    assert r["sin_json"] == 2 and len(r["muestra"]) == 700 and r["cierran"] == 1 and r["chars_max"] == 900
    assert m1.resumen_sonda([], 10)["muestra"] is None


def _ic(p, lo, hi):
    return {"punto": p, "ic_bajo": lo, "ic_alto": hi}


def test_veredicto_adversarial_mira_el_signo():
    assert m1.veredicto_adversarial(_ic(.5, .3, .7), _ic(.6, .4, .8)) == "solapan"
    assert m1.veredicto_adversarial(_ic(.2, .1, .3), _ic(.9, .8, 1.)) == "gana_reglas"
    assert m1.veredicto_adversarial(_ic(.9, .8, 1.), _ic(.2, .1, .3)) == "gana_ajustado"


class HibridoFalso:
    """SistemaHibrido falso: falla la extraccion en los casos marcados."""
    fallar = set()

    def __init__(self, generar, etiqueta):
        self.fallos_extraccion, self.trazas, self.n = [], [], 0

    def __call__(self, relato):
        self.n += 1
        if self.n in self.fallar:
            self.fallos_extraccion.append({"salida": "no es json"})
        self.trazas.append({"relato": relato[:10]})
        return _salida()


def _preparar_hibrido(ctx, monkeypatch, fallar):
    from amparo.sistemas import sistema
    m1.cargar_datos(ctx)
    ctx.sc["finetuned"] = None
    monkeypatch.setattr(m1.generacion, "generador_hf", lambda *a, **k: (lambda s, u: "{}"))
    monkeypatch.setattr(sistema, "extraer_hechos", lambda gen, relato, fallos: None)
    HibridoFalso.fallar = fallar
    monkeypatch.setattr(sistema, "SistemaHibrido", HibridoFalso)
    monkeypatch.setattr(m1, "_imprimir_quien_decide", lambda a, b: None)


def test_brazo_hibrido_corta_temprano_si_el_extractor_es_mudo(ctx, monkeypatch):
    _preparar_hibrido(ctx, monkeypatch, fallar=set(range(1, 11)))
    with pytest.raises(AssertionError, match="ya en los primeros casos"):
        m1.brazo_hibrido(ctx)


def test_brazo_hibrido_guarda_por_encima_del_10_por_ciento(ctx, monkeypatch):
    m1.cargar_datos(ctx)
    n = len(ctx.eval_raw)
    _preparar_hibrido(ctx, monkeypatch, fallar=set(range(11, 11 + int(0.1 * n) + 1)))
    with pytest.raises(AssertionError, match="sin JSON utilizable"):
        m1.brazo_hibrido(ctx)


def test_brazo_hibrido_guarda_sus_tres_artefactos(ctx, monkeypatch):
    _preparar_hibrido(ctx, monkeypatch, fallar={3})
    m1.brazo_hibrido(ctx)
    assert {"scorecard_hibrido", "trazas_hibrido", "extractor"} <= set(ctx.c.guardados)
    assert ctx.extractor["brazo_base"]["sin_json"] == 1
    assert "lectura" in ctx.extractor and "sonda_ajustado" in ctx.extractor


# --------------------------------------------------------------------------
# Redaccion (celda 34)
# --------------------------------------------------------------------------
def test_redaccion_sin_clave_queda_registrada_como_no_medida(ctx, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    medida = m1.redaccion(ctx)
    assert medida == {"n": 0, "concluyente": False, "motivo": "sin GROQ_API_KEY en esta corrida"}
    assert ctx.c.guardados["redaccion"] == medida


def test_redaccion_con_generador_redacta_sobre_el_ajustado(ctx, monkeypatch):
    from amparo.finetuning import redaccion as red
    ctx.eval_raw = [{"id": "a", "etiqueta_pivota_en": None}, {"id": "b"}]
    ctx.salidas["finetuned"] = [_salida(), _salida("habeas_corpus")]
    vistos = []

    def redactar(gen, bloque, pivota, registro, estricto):
        vistos.append(bloque["mecanismo"])
        return {"texto": "t", "verificacion": {"valido": True}}

    monkeypatch.setattr(red, "redactar", redactar)
    monkeypatch.setattr(red, "medir", lambda rs: {"n": len(rs), "textos_con_citas_intrusas": 0,
                                                 "tasa_citas_intrusas": 0.0,
                                                 "dicen_el_mecanismo": 1.0,
                                                 "dicen_la_procedencia": 1.0,
                                                 "palabras_media": 10})
    medida = m1.redaccion(ctx, generar=lambda s, u: "x")
    assert vistos == ["tutela", "habeas_corpus"] and medida["n"] == 2


# --------------------------------------------------------------------------
# Artefactos y publicacion (celda 36)
# --------------------------------------------------------------------------
def test_predicciones_tiene_lo_que_consumen_m2_y_m3():
    p = m1.predicciones([{"id": "a", "tipo": "gold", "categoria": "c", "mecanismo": "tutela"}],
                        ["b"], ["f"])
    assert p == [{"id": "a", "tipo": "gold", "categoria": "c", "gold_mecanismo": "tutela",
                  "base": "b", "finetuned": "f"}]


def test_publicar_artefactos_publica_todo_y_versiona_el_adaptador(ctx, tmp_path, monkeypatch):
    monkeypatch.setattr(m1, "MODELS", tmp_path / "models")
    monkeypatch.setattr(m1, "RAIZ", tmp_path)
    for n in ("fertilidad_tokenizadores", "cobertura_clasificador", "hiperparametros",
              "seleccion_checkpoint", "scorecard_hibrido", "extractor", "redaccion"):
        ctx.c.guardar_json(n, {})
    ctx.sc = {"base": {}, "base_few_shot": {}, "finetuned": {}}
    ctx.deg = {"base": {}, "base_few_shot": {}, "finetuned": {}}
    ctx.eval_raw = [{"id": "a", "categoria": "c", "mecanismo": "tutela"}]
    ctx.salidas = {"base": ["b"], "finetuned": ["f"]}
    ctx.model, ctx.tokenizer = ModeloQueGuarda(), TokQueGuarda()
    ficha = m1.publicar_artefactos(ctx)
    destinos = dict(ctx.c.publicados)
    assert destinos["predicciones"] == "results/m1_predicciones.json"
    assert len(ctx.c.publicados) == 12
    assert ctx.c.meta["adaptador"] == ficha and ctx.c.meta_escrita == 1


def _publicaciones_literales():
    src = inspect.getsource(m1)
    return src, re.findall(r'publicar\(\s*"([^"]+)"\s*,\s*"(results/[^"]+)"', src)


def test_destinos_literales_coinciden_con_lo_declarado_en_arranque():
    _, pubs = _publicaciones_literales()
    declarados = set(arranque.ORDEN["m1"]["produce"])
    assert {d for _, d in pubs} == declarados


def test_cada_artefacto_se_guarda_en_el_codigo_antes_de_publicarse():
    src, pubs = _publicaciones_literales()
    for nombre, _ in pubs:
        g = src.find(f'guardar_json("{nombre}"')
        p = src.find(f'publicar("{nombre}"')
        assert g != -1 and g < p, f"{nombre}: se publica antes de guardarse en el codigo"


# --------------------------------------------------------------------------
# Estabilidad (celda 38) y cierre (39)
# --------------------------------------------------------------------------
def _previa(tmp_path, **meta):
    previa = tmp_path / "runs" / "m1" / "20261001T000000Z"
    previa.mkdir(parents=True)
    base = {"datos": {"dataset.json": "v3.5.0"}, "codigo": {"_conjunto": "abc"},
            "hardware": {"gpu": "A100"}, "determinismo": {"x": 1}}
    base.update(meta)
    (previa / "corrida.json").write_text(json.dumps(base), encoding="utf-8")
    return previa


def test_comparar_con_previa_sin_artefactos_no_es_concluyente(tmp_path):
    c = CorridaFalsa(tmp_path)

    def comparar(a, b, art):
        raise FileNotFoundError

    est = m1.comparar_con_previa(c, _previa(tmp_path), comparar)
    assert est["concluyente"] is False and est["identicas"] is None
    assert est["mismos_datos"] and est["mismo_codigo"] and est["mismo_hardware"]


def test_comparar_con_previa_identicas_y_codigo_distinto(tmp_path):
    c = CorridaFalsa(tmp_path)
    est = m1.comparar_con_previa(c, _previa(tmp_path, codigo={"_conjunto": "otro"}),
                                 lambda a, b, art: {"identicas": True})
    assert est["identicas"] is True and est["mismo_codigo"] is False
    assert set(est["artefactos"]) == set(m1.ARTEFACTOS_ESTABILIDAD)


def test_estabilidad_en_la_primera_corrida_no_publica(ctx, tmp_path, monkeypatch):
    from amparo.ejecucion import corridas
    monkeypatch.setattr(corridas, "RAIZ", tmp_path)
    assert m1.estabilidad(ctx) is None and ctx.c.publicados == []


def test_estabilidad_con_previa_guarda_y_publica(ctx, tmp_path, monkeypatch):
    from amparo.ejecucion import corridas
    monkeypatch.setattr(corridas, "RAIZ", tmp_path)
    monkeypatch.setattr(corridas, "comparar", lambda a, b, art: {"identicas": True})
    _previa(tmp_path)
    est = m1.estabilidad(ctx)
    assert est["identicas"] is True
    assert ctx.c.publicados == [("estabilidad", "results/m1_estabilidad.json")]


def test_notas_de_cierre():
    sc = {"campos": {"mecanismo": {"accuracy": .9, "baseline_mayoritaria": .5}},
          "acierto_juridico": .87, "por_tipo": {"gold": {"acierto_juridico": .9}},
          "alucinacion_normativa": {"tasa_alucinacion": 0.0, "tasa_alucinacion_salida": 0.01}}
    notas = m1.notas_de_cierre(sc, {"n": 1, "de": 69}, None)
    assert len(notas) == 4 and "degeneracion 1/69" in notas[-1]
    est = {"corrida_previa": "p", "concluyente": False, "mismos_datos": True, "mismo_codigo": True}
    assert "no concluyente" in m1.notas_de_cierre(sc, {"n": 0, "de": 69}, est)[-1]


# --------------------------------------------------------------------------
# El notebook es un envoltorio delgado de estas etapas
# --------------------------------------------------------------------------
def _celdas_codigo():
    nb = json.loads((RAIZ / "notebooks" / "M1_finetuning.ipynb").read_text(encoding="utf-8"))
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


def test_el_notebook_llama_todas_las_etapas_en_orden_y_compila():
    codigo = _celdas_codigo()
    for s in codigo:
        ast.parse("\n".join("" if l.lstrip().startswith(("!", "%")) else l for l in s.splitlines()))
    llamadas = [m for s in codigo for m in re.findall(r"m1\.(\w+)\(ctx\)", s)]
    assert llamadas == [e.__name__ for e in m1.ETAPAS]
    assert any("m1.preparar()" in s for s in codigo)


def test_el_notebook_conserva_los_pins_de_instalacion():
    s = _celdas_codigo()[0]
    assert "transformers==5.20.1 peft==0.21.2 accelerate==1.15.0 datasets==5.1.0 groq==1.7.0" in s
    assert "pip uninstall -y -q torchao" in s
