import pytest

from tools.evaluation import bias


def test_length_bias_correlation_perfect_positive():
    scores = [1, 2, 3, 4, 5]
    lengths = [10, 20, 30, 40, 50]
    result = bias.length_bias_correlation(scores, lengths)
    assert result["pearson_r"] == pytest.approx(1.0)
    assert result["n"] == 5


def test_length_bias_correlation_no_relationship_or_short_input():
    assert bias.length_bias_correlation([1.0], [10]) == {"pearson_r": None, "n": 1}
    assert bias.length_bias_correlation([1, 2], [10]) == {"pearson_r": None, "n": 2}


def test_normalize_judge_score_and_similarity():
    assert bias.normalize_judge_score(1) == 0.0
    assert bias.normalize_judge_score(5) == 1.0
    assert bias.normalize_judge_score(3) == pytest.approx(0.5)
    assert bias.normalize_similarity(0) == 0.0
    assert bias.normalize_similarity(100) == 1.0
    assert bias.normalize_similarity(50) == pytest.approx(0.5)


def test_self_preference_gap_no_divergence_when_signals_agree():
    # El juez y la similitud ven exactamente la misma mejora normalizada.
    report = bias.self_preference_gap(
        judge_baseline=[2, 2, 2],
        judge_finetuned=[4, 4, 4],
        sim_baseline=[25, 25, 25],
        sim_finetuned=[75, 75, 75],
    )
    # judge_gap = (4-1)/4 - (2-1)/4 = 0.75 - 0.25 = 0.5
    # similarity_gap = 0.75 - 0.25 = 0.5
    assert report.judge_gap == pytest.approx(0.5)
    assert report.similarity_gap == pytest.approx(0.5)
    assert report.divergence == pytest.approx(0.0)
    assert report.flagged is False


def test_self_preference_gap_flags_large_divergence():
    report = bias.self_preference_gap(
        judge_baseline=[1, 1, 1],
        judge_finetuned=[5, 5, 5],
        sim_baseline=[50, 50, 50],
        sim_finetuned=[52, 52, 52],
    )
    # judge_gap = 1.0 - 0.0 = 1.0 ; similarity_gap = 0.52 - 0.50 = 0.02
    assert report.judge_gap == pytest.approx(1.0)
    assert report.similarity_gap == pytest.approx(0.02)
    assert report.divergence == pytest.approx(0.98)
    assert report.flagged is True


def test_judge_vs_similarity_correlation():
    result = bias.judge_vs_similarity_correlation([1, 2, 3], [10, 20, 30])
    assert result["pearson_r"] == pytest.approx(1.0)


def test_build_pairwise_prompt_contains_both_responses():
    prompt = bias.build_pairwise_prompt("mi consulta", "respuesta A", "respuesta B")
    assert "mi consulta" in prompt
    assert "respuesta A" in prompt
    assert "respuesta B" in prompt
