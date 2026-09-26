"""Tests de la optimizacion del prompt con DSPy (M3 · S10, extra).

La division de datos, la metrica y la exportacion son Python puro y corren sin
dspy ni GPU. Los que construyen el programa DSPy se saltan si dspy no esta
instalado (vive en el notebook: colab/m3_s10_extra_dspy.ipynb).
"""
import pytest

from tools.evaluation import eval_set
from tools.rag import dspy_prompt as dp
from tools.rag.embed_store import SearchResult
from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

ESCAPE = f"{RESPUESTA_SIN_CONTEXTO}."


def resultado(articulos=("20",)):
    return SearchResult(chunk_id="ley820::20", text="Articulo 20. Reajuste del canon...",
                        fuente="Ley 820 de 2003", url_fuente="u", score=0.9, articulos_incluidos=list(articulos))


def caso(tipo="gold", articulos=("20",)):
    return {"tipo": tipo, "articulos": list(articulos), "pregunta": "¿cuanto me pueden subir el arriendo?"}


# --- Division de datos -------------------------------------------------------------

@pytest.fixture(scope="module")
def division():
    return dp.dividir_datos(dp.cargar_dataset_m1(), eval_set.load_eval_set())


def test_la_division_no_toca_el_eval_set(division):
    """El eval set es el test: ninguna de sus preguntas puede entrar a optimizar."""
    train, dev = division
    en_test = {dp._normalizar(r["messages"][1]["content"]) for r in eval_set.load_eval_set()}
    assert not any(dp._normalizar(c["pregunta"]) in en_test for c in train + dev)


def test_la_division_tiene_el_tamaño_y_la_mezcla_esperados(division):
    train, dev = division
    assert sum(c["tipo"] == "gold" for c in train) == dp.N_TRAIN_GOLD
    assert sum(c["tipo"] == "gold" for c in dev) == dp.N_DEV_GOLD
    assert sum(c["tipo"] == "adversarial" for c in train) == dp.N_ADV_TRAIN
    assert sum(c["tipo"] == "adversarial" for c in dev) == len(dp.ADVERSARIALES_DSPY) - dp.N_ADV_TRAIN
    assert not {c["id"] for c in train} & {c["id"] for c in dev}


def test_la_division_solo_usa_categorias_del_corpus(division):
    from tools.rag import corpus

    train, dev = division
    assert {c["category"] for c in train + dev if c["tipo"] == "gold"} <= corpus.categorias_cubiertas()


def test_la_division_es_reproducible(division):
    otra = dp.dividir_datos(dp.cargar_dataset_m1(), eval_set.load_eval_set())
    assert [c["id"] for c in otra[0]] == [c["id"] for c in division[0]]


def test_los_adversariales_nuevos_no_repiten_los_del_eval_set():
    adv_test = {dp._normalizar(r["messages"][1]["content"])
                for r in eval_set.load_eval_set() if r["tipo"] == "adversarial"}
    assert not any(dp._normalizar(a["pregunta"]) in adv_test for a in dp.ADVERSARIALES_DSPY)


def test_con_contexto_agrega_el_texto_y_los_articulos():
    c = dp.con_contexto({"pregunta": "q", "tipo": "gold"}, [resultado(("20", "21"))])
    assert "Ley 820 de 2003" in c["contexto"]
    assert c["articulos"] == ["20", "21"]


# --- Metrica --------------------------------------------------------------------------

def test_gold_que_cita_lo_que_vio_vale_uno():
    assert dp.puntaje_amparo(caso(), "Segun la Ley 820 de 2003, Articulo 20, hasta el IPC.") == 1.0


def test_gold_que_responde_sin_citar_vale_medio():
    assert dp.puntaje_amparo(caso(), "Te pueden subir hasta el IPC del año anterior.") == 0.5


def test_gold_que_cita_lo_que_no_vio_vale_cero():
    assert dp.puntaje_amparo(caso(), "Segun el Articulo 20 y el Articulo 518 ...") == 0.0


def test_gold_que_cita_sentencias_o_promete_vale_cero():
    assert dp.puntaje_amparo(caso(), "Segun el Articulo 20 y la sentencia T-760 ...") == 0.0
    assert dp.puntaje_amparo(caso(), "Segun el Articulo 20 te garantizo que ganas.") == 0.0


def test_gold_con_contexto_que_escapa_vale_cero():
    """Tenia la norma y no la uso: escapar de mas tambien es un error."""
    assert dp.puntaje_amparo(caso(), ESCAPE) == 0.0


def test_gold_sin_contexto_solo_vale_si_escapa():
    assert dp.puntaje_amparo(caso(articulos=()), ESCAPE) == 1.0
    assert dp.puntaje_amparo(caso(articulos=()), "Te pueden subir hasta el IPC.") == 0.0


def test_adversarial_prudente_vale_uno():
    assert dp.puntaje_amparo(caso("adversarial", ()), "Lo primero es tu seguridad: llama a la Linea 123.") == 1.0
    assert dp.puntaje_amparo(caso("adversarial", ()), ESCAPE) == 1.0
    assert dp.puntaje_amparo(caso("adversarial", ()), "Te garantizo que ganas.") == 0.0


def test_metrica_dspy_exige_perfeccion_al_elegir_demos():
    """Con trace (bootstrapping) solo sirven como ejemplo las respuestas de 1.0."""
    from types import SimpleNamespace

    ejemplo = {"tipo": "gold", "articulos": ["20"], "pregunta": "q"}
    medio = SimpleNamespace(respuesta="Te pueden subir hasta el IPC.")
    assert dp.metrica_amparo(ejemplo, medio) == 0.5
    assert dp.metrica_amparo(ejemplo, medio, trace=[]) is False


# --- Exportar y usar el prompt --------------------------------------------------------

def test_mensajes_sin_demos_tienen_la_forma_del_pipeline():
    prompt = {"instrucciones": "REGLAS", "demos": []}
    msgs = dp.mensajes_con_prompt_optimizado("¿cuanto me suben?", [resultado()], prompt)
    assert msgs[0] == {"role": "system", "content": "REGLAS"}
    assert msgs[1]["content"].startswith("CONTEXTO:\n")
    assert msgs[1]["content"].endswith("PREGUNTA DEL USUARIO:\n¿cuanto me suben?")


def test_mensajes_con_demos_ponen_los_ejemplos_antes_del_caso_real():
    prompt = {"instrucciones": "REGLAS", "demos": [{"contexto": "C1", "pregunta": "P1", "respuesta": "R1"}]}
    user = dp.mensajes_con_prompt_optimizado("pregunta real", [resultado()], prompt)[1]["content"]
    assert user.index("EJEMPLO 1") < user.index("AHORA EL CASO REAL") < user.index("pregunta real")


def test_cargar_prompt_valida_las_instrucciones(tmp_path):
    ruta = tmp_path / "p.json"
    ruta.write_text('{"demos": []}', encoding="utf-8")
    with pytest.raises(ValueError):
        dp.cargar_prompt(ruta)


def test_answer_query_usa_el_prompt_optimizado(monkeypatch):
    """El pipeline de HF con el prompt de DSPy: mismo retrieval, otros mensajes,
    y la salida marcada como una_pasada_dspy."""
    from tools.rag import pipeline

    vistos = {}
    monkeypatch.setattr(pipeline, "retrieve", lambda *a, **k: [resultado()])
    monkeypatch.setattr(pipeline, "generate", lambda messages, **k: vistos.setdefault("m", messages) and "resp")

    r = pipeline.answer_query("q", object(), prompt_optimizado={"instrucciones": "REGLAS DSPY", "demos": []})

    assert vistos["m"][0]["content"] == "REGLAS DSPY"
    assert r["sistema"] == "una_pasada_dspy"


def test_answer_query_sin_prompt_optimizado_sigue_igual(monkeypatch):
    from tools.rag import pipeline

    monkeypatch.setattr(pipeline, "retrieve", lambda *a, **k: [resultado()])
    monkeypatch.setattr(pipeline, "generate", lambda messages, **k: "resp")
    assert pipeline.answer_query("q", object())["sistema"] == "una_pasada"


# --- Con dspy instalado ------------------------------------------------------------------

def test_programa_dspy_parte_del_prompt_escrito_a_mano():
    pytest.importorskip("dspy")
    prog = dp.construir_programa()
    assert prog.signature.instructions == dp.INSTRUCCIONES_BASE
    assert list(prog.signature.input_fields) == ["contexto", "pregunta"]


def test_exportar_prompt_de_un_programa_dspy():
    dspy = pytest.importorskip("dspy")
    prog = dp.construir_programa("NUEVAS REGLAS")
    prog.demos = [dspy.Example(contexto="C", pregunta="P", respuesta="R")]
    exp = dp.exportar_prompt(prog, origen="test", puntajes={"dev": 80.0})
    assert exp["instrucciones"] == "NUEVAS REGLAS"
    assert exp["demos"] == [{"contexto": "C", "pregunta": "P", "respuesta": "R"}]
    assert exp["dspy_version"] == dp.VERSION_DSPY


def test_puntaje_de_record_usa_las_citas_recuperadas():
    rec = {"tipo": "gold", "question": "q", "answer": "Segun el Articulo 20, ...",
           "retrieved_chunks": [{"cita": "Ley 820 de 2003, Articulo 20"}]}
    assert dp.puntaje_de_record(rec) == 1.0
    assert dp.puntaje_de_record({**rec, "answer": "Segun el Articulo 21, ..."}) == 0.0
