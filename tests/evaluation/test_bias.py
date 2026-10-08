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


def _reporte(*pares):
    detalles = [{"id": i, "verdict_normal": a, "verdict_swapped": b} for i, (a, b) in enumerate(pares)]
    return bias.PositionBiasReport(n_pairs=len(pares), n_flipped=0, n_tied_or_unparsed=0,
                                   flip_rate_pct=0.0, details=detalles)


def test_veredicto_consistente_solo_cuenta_victorias_en_los_dos_ordenes():
    rep = _reporte(
        ("fine_tuned", "fine_tuned"),   # gana en los dos ordenes
        ("baseline", "baseline"),
        ("fine_tuned", "baseline"),     # cambia con el orden: sesgo de posicion
        ("empate", "fine_tuned"),       # el juez no se decide
        ("empate", "empate"),
        (None, "fine_tuned"),           # sin respuesta en una pasada
    )
    assert rep.veredicto_consistente() == {
        "fine_tuned": 1, "baseline": 1, "empate": 2, "inconsistente": 1, "sin_veredicto": 1}


def test_tasa_de_victoria_sobre_pares_decididos():
    rep = _reporte(*([("fine_tuned", "fine_tuned")] * 3 + [("baseline", "baseline")] + [("a", "b")]))
    t = rep.tasa_victoria()
    assert t["fine_tuned"] == 3 and t["decididos"] == 4
    assert t["tasa"] == pytest.approx(0.75)
    assert t["ic95"][0] < 0.75 < t["ic95"][1]


def test_tasa_de_victoria_sin_pares_decididos():
    assert _reporte(("empate", "empate")).tasa_victoria()["tasa"] is None


def test_todos_los_pares_cuando_no_hay_muestra():
    """sample_size=None juzga los 231 pares, no una muestra de 30."""
    llamadas = []

    def fake(system, user, max_tokens):
        llamadas.append(user)
        return '{"veredicto": "A", "confianza": 3}'

    pares = [(i, f"q{i}", f"b{i}", f"f{i}") for i in range(50)]
    rep = bias._run_position_bias_probe_core(fake, pares, sample_size=None, seed=42, progress_every=0,
                                             max_tokens=10, log_prefix="t")
    assert rep.n_pairs == 50 and len(llamadas) == 100
    # "A" en los dos ordenes = baseline primero y fine-tuned despues: gana distinto -> inconsistente.
    assert rep.veredicto_consistente()["inconsistente"] == 50


def test_el_prompt_comparativo_pide_ignorar_orden_y_largo():
    p = bias.PAIRWISE_JUDGE_SYSTEM_PROMPT.lower()
    assert "orden" in p and "larga" in p


def test_build_pairwise_prompt_contains_both_responses():
    prompt = bias.build_pairwise_prompt("mi consulta", "respuesta A", "respuesta B")
    assert "mi consulta" in prompt
    assert "respuesta A" in prompt
    assert "respuesta B" in prompt
