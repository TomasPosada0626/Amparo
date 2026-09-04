import pytest

from tools.evaluation import metrics_classic as mc


def test_normalize_text_strips_accents_and_lowercases():
    assert mc.normalize_text("Acción de Tutela") == "accion de tutela"
    assert mc.normalize_text("  Ñoño   con   espacios  ") == "nono con espacios"


def test_exact_match_ignores_accents_and_case():
    assert mc.exact_match("Acción de tutela", "accion DE TUTELA") == 1.0
    assert mc.exact_match("Acción de tutela", "otra respuesta") == 0.0


def test_token_f1_perfect_and_zero_overlap():
    assert mc.token_f1("hola mundo legal", "hola mundo legal") == pytest.approx(1.0)
    assert mc.token_f1("hola mundo", "algo distinto") == 0.0


def test_token_f1_partial_overlap():
    score = mc.token_f1("puedes presentar accion de tutela", "puedes presentar una queja")
    assert 0.0 < score < 1.0


def test_token_f1_empty_strings_return_zero():
    assert mc.token_f1("", "algo") == 0.0
    assert mc.token_f1("algo", "") == 0.0


def test_bleu_identical_strings_scores_high():
    score = mc.bleu("puedes presentar accion de tutela", "puedes presentar accion de tutela")
    assert score > 90.0


def test_bleu_empty_strings_return_zero():
    assert mc.bleu("", "algo") == 0.0


def test_rouge_l_identical_strings_scores_one():
    scores = mc.rouge_l("respuesta identica", "respuesta identica")
    assert scores["fmeasure"] == pytest.approx(1.0)


def test_rouge_l_empty_strings_return_zero():
    scores = mc.rouge_l("", "algo")
    assert scores == {"precision": 0.0, "recall": 0.0, "fmeasure": 0.0}
