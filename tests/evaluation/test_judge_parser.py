from tools.evaluation import judge


def test_parses_clean_json():
    raw = (
        '{"correccion_juridica": 4, "prudencia": 5, "claridad_utilidad": 3, '
        '"concision": 4, "justificacion": "Buena respuesta, breve y prudente."}'
    )
    score = judge.parse_judge_output(raw)

    assert score.parse_ok is True
    assert score.correccion_juridica == 4
    assert score.prudencia == 5
    assert score.claridad_utilidad == 3
    assert score.concision == 4
    assert score.composite == (4 + 5 + 3 + 4) / 4
    assert "prudente" in score.justificacion


def test_parses_json_inside_markdown_fence():
    raw = (
        "```json\n"
        '{"correccion_juridica": 3, "prudencia": 3, "claridad_utilidad": 3, '
        '"concision": 3, "justificacion": "ok"}\n'
        "```"
    )
    score = judge.parse_judge_output(raw)
    assert score.parse_ok is True
    assert score.composite == 3.0


def test_parses_json_embedded_in_extra_text():
    raw = (
        "Claro, aqui esta mi evaluacion:\n"
        '{"correccion_juridica": 2, "prudencia": 4, "claridad_utilidad": 3, '
        '"concision": 5, "justificacion": "Correcto pero verboso."}\n'
        "Espero que ayude."
    )
    score = judge.parse_judge_output(raw)
    assert score.parse_ok is True
    assert score.correccion_juridica == 2
    assert score.concision == 5


def test_falls_back_to_field_regex_on_malformed_json():
    raw = (
        'correccion_juridica: 3, prudencia: 4, claridad_utilidad: 2, '
        'concision: 3 (sin json valido)'
    )
    score = judge.parse_judge_output(raw)
    assert score.parse_ok is True
    assert score.correccion_juridica == 3
    assert score.prudencia == 4


def test_missing_field_marks_parse_failure():
    raw = '{"correccion_juridica": 4, "prudencia": 5, "claridad_utilidad": 3}'
    score = judge.parse_judge_output(raw)
    assert score.parse_ok is False
    assert score.composite is None
    assert score.concision is None


def test_out_of_range_value_marks_that_field_invalid():
    raw = (
        '{"correccion_juridica": 9, "prudencia": 5, "claridad_utilidad": 3, '
        '"concision": 4, "justificacion": "fuera de rango"}'
    )
    score = judge.parse_judge_output(raw)
    assert score.correccion_juridica is None
    assert score.parse_ok is False


def test_completely_unparseable_output_never_raises():
    raw = "esto no tiene ningun formato reconocible ni numeros utiles"
    score = judge.parse_judge_output(raw)
    assert score.parse_ok is False
    assert score.composite is None
    assert score.raw_output == raw
