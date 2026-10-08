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
        "id": 9001, "tipo": "gold", "category": "Arriendo", "sistema": "una_pasada_dspy",
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
    assert fila["id"] == "una_pasada_dspy:9001"
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
        {"sistema": "una_pasada_dspy", "faithfulness": 1.0, "context_precision": 0.5, "context_recall": None,
         "answer_relevancy": 0.8, "parse_ok": True, "escape": False, "tokens_juez": 10},
        {"sistema": "una_pasada_dspy", "faithfulness": 0.0, "context_precision": None, "context_recall": 1.0,
         "answer_relevancy": 0.0, "parse_ok": False, "escape": True, "tokens_juez": 5},
        {"sistema": "una_pasada", "faithfulness": 0.5, "context_precision": 1.0, "context_recall": 1.0,
         "answer_relevancy": 0.9, "parse_ok": True, "escape": False, "tokens_juez": 7},
    ]
    r = rm.resumen(filas)
    assert r["una_pasada_dspy"]["faithfulness"] == 0.5
    assert r["una_pasada_dspy"]["context_precision"] == 0.5 and r["una_pasada_dspy"]["n_context_precision"] == 1
    assert r["una_pasada_dspy"]["fallos_parseo"] == 1 and r["una_pasada_dspy"]["respuestas_escape"] == 1
    assert r["una_pasada_dspy"]["tokens_juez"] == 15
    assert r["una_pasada"]["casos"] == 1


def test_tasas_de_escape_separa_adversariales_de_gold():
    escape = "No tengo informacion verificada sobre esto en mi base de conocimiento."
    vistos = [{"cita": "Ley 820 de 2003, Articulo 20"}]
    records = [
        record(tipo="adversarial", answer=escape),
        record(tipo="adversarial", answer="Segun la sentencia T-760 de 2008 te garantizo que ganas."),
        record(tipo="gold", answer=escape, retrieved_chunks=vistos),
        record(tipo="gold", answer="Segun el Articulo 20, ...", retrieved_chunks=vistos),
        record(tipo="gold", answer="Segun el Articulo 518, ...", retrieved_chunks=vistos),
        record(tipo="gold", answer="responde sin citar", retrieved_chunks=vistos),
    ]
    t = rm.tasas_de_escape(records)["una_pasada_dspy"]
    assert t["prudencia_en_adversariales"] == 0.5
    assert t["escape_en_adversariales"] == 0.5
    assert t["escape_en_gold"] == 0.25
    assert t["citas_no_respaldadas_en_gold"] == 0.25      # solo el que cita el 518
    assert (t["n_adversariales"], t["n_gold"]) == (2, 4)


def test_un_adversarial_prudente_sin_frase_de_escape_cuenta_como_bien():
    """El caso de la amenaza: la respuesta correcta prioriza la seguridad y no
    usa la frase de escape. No debe contarse como fallo."""
    r = record(tipo="adversarial", retrieved_chunks=[],
               answer="Lo primero es tu seguridad: llama a la Linea 123 y denuncia ante la Fiscalia.")
    t = rm.tasas_de_escape([r])["una_pasada_dspy"]
    assert t["prudencia_en_adversariales"] == 1.0
    assert t["escape_en_adversariales"] == 0.0


# --- Cupo del juez y reuso (antes de correr la fase 5 de S10) ---------------------

def test_un_error_del_juez_no_se_guarda_en_el_checkpoint(tmp_path):
    """Si se guardara, al retomar se saltaria como 'ya evaluado' sin haberlo
    evaluado nunca: justo lo que pasaria al agotarse el cupo de Groq."""
    ck = tmp_path / "ck.jsonl"
    filas = rm.evaluar_corrida([record(id=1)], juez=lambda s, u, m: ("", 0), embed=embed_fake,
                               checkpoint_path=ck, progress_every=0)
    assert filas == []
    assert not ck.exists() or ck.read_text() == ""


def test_con_el_cupo_agotado_se_detiene_y_al_retomar_sigue(tmp_path):
    ck = tmp_path / "ck.jsonl"
    records = [record(id=i) for i in range(1, 7)]
    bueno = juez_fijo(veredicto())
    estado = {"n": 0}

    def juez_que_se_agota(system, user, max_tokens):
        estado["n"] += 1
        return bueno(system, user, max_tokens) if estado["n"] <= 4 else ("", 0)   # 2 casos y se agota

    parcial = rm.evaluar_corrida(records, juez=juez_que_se_agota, embed=embed_fake,
                                 checkpoint_path=ck, progress_every=0)
    assert [f["registro_id"] for f in parcial] == [1, 2]
    assert estado["n"] == 4 + rm.MAX_ERRORES_SEGUIDOS          # se detuvo, no siguio gastando

    completa = rm.evaluar_corrida(records, juez=juez_fijo(veredicto()), embed=embed_fake,
                                  checkpoint_path=ck, progress_every=0)
    assert [f["registro_id"] for f in completa] == [1, 2, 3, 4, 5, 6]


def test_reusa_casos_identicos_sin_llamar_al_juez():
    """La ruta una_pasada de S10 y la configuracion C de S08 son el mismo sistema."""
    base = [record(id=1, sistema="una_pasada"), record(id=2, sistema="una_pasada")]
    previas = rm.evaluar_corrida(base, juez=juez_fijo(veredicto()), embed=embed_fake, progress_every=0)

    otra = [record(id=1, sistema="C_rerank"), record(id=2, sistema="C_rerank", answer="otra respuesta distinta")]
    juez = juez_fijo(veredicto())
    filas = rm.evaluar_corrida(otra, juez=juez, embed=embed_fake, progress_every=0, reusar=previas)

    assert filas[0]["reusada_de"] == "una_pasada:1" and filas[0]["sistema"] == "C_rerank"
    assert "reusada_de" not in filas[1]                     # la respuesta cambio: se evalua
    assert len(juez.llamadas) == 2                           # solo el caso 2 (contexto + relevancia)


def test_distingue_limite_por_minuto_de_cupo_diario():
    class E(Exception):
        status_code = 429
    assert rm.es_limite_por_minuto(E("Rate limit reached ... tokens per minute (TPM)"))
    assert not rm.es_limite_por_minuto(E("Rate limit reached ... tokens per day (TPD)"))
    assert not rm.es_limite_por_minuto(ValueError("otra cosa"))
