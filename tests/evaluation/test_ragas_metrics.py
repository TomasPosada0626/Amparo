"""Tests de las metricas RAGAS (M3 · S10, Lab C).

Corren sin red ni GPU: el juez (Groq) y los embeddings (e5) se inyectan como
fakes. Se prueban las formulas, el parseo del veredicto del juez, el trato de
la valvula de escape y el checkpoint -- no la calidad del juez.
"""
import json

import pytest

from tools.evaluation import ragas_metrics as rm


def record(**over):
    base = {
        "id": 9001, "tipo": "gold", "category": "Arriendo", "sistema": "react",
        "question": "¿cuanto me pueden subir el arriendo?",
        "answer": "Segun la Ley 820 de 2003, Articulo 20, hasta el 100% del IPC.",
        "contexts": ["Articulo 20. Reajuste del canon...", "Articulo 21. Incumplimiento..."],
        "ground_truth": "El reajuste anual no puede superar el IPC del año anterior.",
    }
    base.update(over)
    return base


def veredicto(afirmaciones=(True,), utiles=(True, False), referencia=(True,)):
    return json.dumps({
        "afirmaciones": [{"texto": f"a{i}", "respaldada": v} for i, v in enumerate(afirmaciones)],
        "contextos_utiles": list(utiles),
        "referencia": [{"oracion": f"o{i}", "en_contexto": v} for i, v in enumerate(referencia)],
    })


def juez_fijo(contexto_json, preguntas=("¿cuanto me pueden subir el arriendo?",) * 3, tokens=100):
    """Primera llamada: veredicto de contexto. Segunda: preguntas generadas."""
    llamadas = []

    def juez(system, user, max_tokens):
        llamadas.append(user)
        if "CONTEXTOS RECUPERADOS" in user:
            return contexto_json, tokens
        return json.dumps({"preguntas": list(preguntas)}), tokens

    juez.llamadas = llamadas
    return juez


def embed_fake(textos):
    """Vector por palabras clave: preguntas iguales -> coseno 1."""
    return [[t.count("arriendo"), t.count("subir"), t.count("tutela") + 0.001] for t in textos]


# --- Formulas ------------------------------------------------------------------

def test_average_precision_premia_los_relevantes_arriba():
    assert rm.average_precision([True, False, False]) == 1.0
    assert rm.average_precision([False, False, True]) == pytest.approx(1 / 3)
    assert rm.average_precision([True, False, True]) == pytest.approx((1 + 2 / 3) / 2)
    assert rm.average_precision([False, False]) == 0.0
    assert rm.average_precision([]) is None


def test_metricas_de_contexto_desde_el_veredicto():
    m = rm.metricas_de_contexto(json.loads(veredicto((True, False), (True, False), (True, True, False))), 2)
    assert m["faithfulness"] == 0.5
    assert m["context_precision"] == 1.0
    assert m["context_recall"] == pytest.approx(2 / 3)
    assert m["n_afirmaciones"] == 2
    assert m["parse_ok"]


def test_veredicto_mal_formado_deja_none_y_no_un_cero():
    """Un fallo del juez no puede pasar por un mal puntaje del sistema."""
    m = rm.metricas_de_contexto(None, 2)
    assert m["faithfulness"] is None and m["context_precision"] is None
    assert not m["parse_ok"]


def test_numero_de_contextos_que_no_cuadra_invalida_la_precision():
    m = rm.metricas_de_contexto(json.loads(veredicto(utiles=(True,))), 2)
    assert m["context_precision"] is None
    assert not m["parse_ok"]


def test_sin_contextos_el_recall_es_cero():
    m = rm.metricas_de_contexto(json.loads(veredicto(utiles=())), 0)
    assert m["context_recall"] == 0.0
    assert m["context_precision"] is None


def test_extraer_json_tolera_texto_alrededor():
    assert rm.extraer_json('Claro: {"a": 1} listo') == {"a": 1}
    assert rm.extraer_json("sin json") is None
    assert rm.extraer_json('{"a": ') is None


# --- Un caso completo -------------------------------------------------------------

def test_evaluar_caso_calcula_las_cuatro_metricas():
    juez = juez_fijo(veredicto((True, True), (True, False), (True,)))
    fila = rm.evaluar_caso(record(), juez=juez, embed=embed_fake)

    assert fila["faithfulness"] == 1.0
    assert fila["context_precision"] == 1.0
    assert fila["context_recall"] == 1.0
    assert fila["answer_relevancy"] == pytest.approx(1.0, abs=1e-3)
    assert fila["id"] == "react:9001"
    assert fila["tokens_juez"] == 200
    assert len(juez.llamadas) == 2


def test_el_contexto_viaja_en_una_sola_llamada():
    """Tres metricas de contexto, una llamada: es lo que hace alcanzar el cupo."""
    juez = juez_fijo(veredicto())
    rm.evaluar_caso(record(), juez=juez, embed=embed_fake)
    assert sum("CONTEXTOS RECUPERADOS" in u for u in juez.llamadas) == 1


def test_la_valvula_de_escape_no_se_juzga_como_respuesta():
    """Escapar no es afirmar nada: faithfulness no aplica y answer_relevancy es
    0 (no contesto), sin gastar la llamada de relevancia."""
    juez = juez_fijo(veredicto(afirmaciones=()))
    fila = rm.evaluar_caso(
        record(answer="No tengo informacion verificada sobre esto en mi base de conocimiento."),
        juez=juez, embed=embed_fake,
    )
    assert fila["escape"]
    assert fila["faithfulness"] is None
    assert fila["answer_relevancy"] == 0.0
    assert len(juez.llamadas) == 1


def test_un_juez_caido_no_tumba_la_evaluacion():
    fila = rm.evaluar_caso(record(), juez=lambda s, u, m: ("", 0), embed=embed_fake)
    assert not fila["parse_ok"]
    assert fila["faithfulness"] is None
    assert fila["answer_relevancy"] is None


# --- Corrida, checkpoint y resumen ----------------------------------------------

def test_evaluar_corrida_usa_solo_gold_y_retoma_desde_el_checkpoint(tmp_path):
    ck = tmp_path / "ragas.jsonl"
    records = [record(id=1), record(id=2), record(id=3, tipo="adversarial")]
    juez = juez_fijo(veredicto())

    primera = rm.evaluar_corrida(records[:1], juez=juez, embed=embed_fake, checkpoint_path=ck, progress_every=0)
    llamadas_primera = len(juez.llamadas)
    todas = rm.evaluar_corrida(records, juez=juez, embed=embed_fake, checkpoint_path=ck, progress_every=0)

    assert len(primera) == 1
    assert [f["registro_id"] for f in todas] == [1, 2]          # el adversarial no entra
    assert len(juez.llamadas) - llamadas_primera == 2           # solo se evaluo el id 2


def test_resumen_promedia_por_ruta_ignorando_none():
    filas = [
        {"sistema": "react", "faithfulness": 1.0, "context_precision": 0.5, "context_recall": None,
         "answer_relevancy": 0.8, "parse_ok": True, "escape": False, "tokens_juez": 10},
        {"sistema": "react", "faithfulness": 0.0, "context_precision": None, "context_recall": 1.0,
         "answer_relevancy": 0.0, "parse_ok": False, "escape": True, "tokens_juez": 5},
        {"sistema": "una_pasada", "faithfulness": 0.5, "context_precision": 1.0, "context_recall": 1.0,
         "answer_relevancy": 0.9, "parse_ok": True, "escape": False, "tokens_juez": 7},
    ]
    r = rm.resumen(filas)
    assert r["react"]["faithfulness"] == 0.5
    assert r["react"]["context_precision"] == 0.5 and r["react"]["n_context_precision"] == 1
    assert r["react"]["fallos_parseo"] == 1 and r["react"]["respuestas_escape"] == 1
    assert r["react"]["tokens_juez"] == 15
    assert r["una_pasada"]["casos"] == 1


def test_tasas_de_escape_separa_adversariales_de_gold():
    escape = "No tengo informacion verificada sobre esto en mi base de conocimiento."
    records = [
        record(tipo="adversarial", answer=escape), record(tipo="adversarial", answer="inventa algo"),
        record(tipo="gold", answer=escape), record(tipo="gold", answer="responde"),
        record(tipo="gold", answer="responde"), record(tipo="gold", answer="responde"),
    ]
    t = rm.tasas_de_escape(records)["react"]
    assert t["escape_en_adversariales"] == 0.5
    assert t["escape_en_gold"] == 0.25
    assert (t["n_adversariales"], t["n_gold"]) == (2, 4)
