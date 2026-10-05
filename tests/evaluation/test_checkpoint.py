from tools.evaluation.checkpoint import append_checkpoint, load_checkpoint


def test_load_checkpoint_missing_file_returns_empty(tmp_path):
    assert load_checkpoint(tmp_path / "no_existe.jsonl") == {}


def test_load_checkpoint_none_path_returns_empty():
    assert load_checkpoint(None) == {}


def test_append_then_load_roundtrip(tmp_path):
    path = tmp_path / "ckpt.jsonl"
    append_checkpoint(path, {"id": 1, "verdict_normal": "baseline"})
    append_checkpoint(path, {"id": 2, "verdict_normal": "fine_tuned"})

    done = load_checkpoint(path)
    assert set(done.keys()) == {1, 2}
    assert done[1]["verdict_normal"] == "baseline"
    assert done[2]["verdict_normal"] == "fine_tuned"


def test_append_checkpoint_none_path_is_noop(tmp_path):
    # No debe lanzar ni crear nada si no se paso ruta.
    append_checkpoint(None, {"id": 1})


def test_append_checkpoint_creates_parent_dirs(tmp_path):
    path = tmp_path / "nested" / "dir" / "ckpt.jsonl"
    append_checkpoint(path, {"id": 1, "x": "y"})
    assert path.exists()
    assert load_checkpoint(path) == {1: {"id": 1, "x": "y"}}


def test_skips_already_done_pairs_in_position_bias_probe(tmp_path):
    from tools.evaluation.bias import _run_position_bias_probe_core

    checkpoint_path = tmp_path / "ckpt.jsonl"
    calls = []

    def fake_generate_fn(system_prompt, user_content, max_tokens):
        calls.append(user_content)
        return '{"veredicto": "A", "confianza": 5}'

    pairs = [
        (1, "q1", "base1", "ft1"),
        (2, "q2", "base2", "ft2"),
    ]

    # Primera corrida: procesa los 2 pares y los guarda en el checkpoint.
    report1 = _run_position_bias_probe_core(
        fake_generate_fn, pairs, sample_size=2, seed=42, progress_every=0,
        max_tokens=50, log_prefix="test", checkpoint_path=checkpoint_path,
    )
    assert report1.n_pairs == 2
    assert len(calls) == 4  # 2 pares x 2 ordenes

    # Segunda corrida con el mismo checkpoint: no debe volver a llamar a generate_fn.
    calls.clear()
    report2 = _run_position_bias_probe_core(
        fake_generate_fn, pairs, sample_size=2, seed=42, progress_every=0,
        max_tokens=50, log_prefix="test", checkpoint_path=checkpoint_path,
    )
    assert len(calls) == 0
    assert report2.details == report1.details


# --- Huella de contenido (corrida M2 del 2026-10-02) -----------------------------
# El checkpoint se reusaba por id: el sondeo de Groq y los puntajes del eval set
# salieron de una corrida anterior, con otros textos. Ahora solo se reusa si el
# contenido calificado es exactamente el mismo.

from dataclasses import dataclass

from tools.evaluation.checkpoint import huella


@dataclass
class _Fila:
    id: int
    query: str
    expected: str
    generated: str


def test_huella_cambia_con_cualquier_texto_y_con_el_orden():
    base = huella("q", "ref", "resp")
    assert base == huella("q", "ref", "resp")
    assert base != huella("q", "ref", "resp distinta")
    assert base != huella("q", "resp", "ref")


def test_load_checkpoint_con_huellas_descarta_otro_texto_y_entradas_viejas(tmp_path):
    path = tmp_path / "ckpt.jsonl"
    append_checkpoint(path, {"id": 1, "huella": huella("a"), "x": 1})
    append_checkpoint(path, {"id": 2, "huella": huella("viejo"), "x": 2})
    append_checkpoint(path, {"id": 3, "x": 3})            # formato anterior, sin huella

    done = load_checkpoint(path, {1: huella("a"), 2: huella("nuevo"), 3: huella("c")})
    assert set(done) == {1}


def test_juez_local_recalifica_si_la_respuesta_cambio(tmp_path, monkeypatch):
    from tools.evaluation import judge

    llamadas = []

    def fake_score(model, tokenizer, query, reference, candidate, max_new_tokens=0):
        llamadas.append(candidate)
        return judge.parse_judge_output(
            '{"correccion_juridica": 4, "prudencia": 4, "claridad_utilidad": 4, "concision": 4}')

    monkeypatch.setattr(judge, "score_response", fake_score)
    path = tmp_path / "juez.jsonl"
    judge.score_batch(None, None, [_Fila(1, "q", "ref", "resp A"), _Fila(2, "q2", "ref2", "resp B")],
                      progress_every=0, checkpoint_path=path)
    assert llamadas == ["resp A", "resp B"]

    llamadas.clear()
    puntajes = judge.score_batch(None, None, [_Fila(1, "q", "ref", "resp A"), _Fila(2, "q2", "ref2", "OTRA")],
                                 progress_every=0, checkpoint_path=path)
    assert llamadas == ["OTRA"]                          # la 1 se reusa, la 2 se vuelve a calificar
    assert [p.composite for p in puntajes] == [4.0, 4.0]


def test_juez_externo_no_reusa_checkpoint_de_otra_corrida(tmp_path, monkeypatch):
    from tools.evaluation import external_judge, judge

    path = tmp_path / "groq.jsonl"
    append_checkpoint(path, {"id": 1, "correccion_juridica": 1, "prudencia": 1, "claridad_utilidad": 1,
                             "concision": 1, "justificacion": "", "composite": 1.0, "parse_ok": True,
                             "raw_output": ""})        # entrada vieja, sin huella
    monkeypatch.setattr(external_judge, "score_response", lambda q, r, c: judge.parse_judge_output(
        '{"correccion_juridica": 5, "prudencia": 5, "claridad_utilidad": 5, "concision": 5}'))

    puntajes = external_judge.score_batch([_Fila(1, "q", "ref", "resp")], progress_every=0, checkpoint_path=path)
    assert puntajes[0].composite == 5.0


def test_sondeo_de_posicion_vuelve_a_juzgar_si_cambian_los_textos(tmp_path):
    from tools.evaluation.bias import _run_position_bias_probe_core

    path = tmp_path / "pos.jsonl"
    llamadas = []

    def fake(system_prompt, user_content, max_tokens):
        llamadas.append(user_content)
        return '{"veredicto": "A", "confianza": 5}'

    kw = dict(sample_size=1, seed=42, progress_every=0, max_tokens=50, log_prefix="t", checkpoint_path=path)
    _run_position_bias_probe_core(fake, [(1, "q", "base", "ft")], **kw)
    llamadas.clear()
    _run_position_bias_probe_core(fake, [(1, "q", "base", "ft NUEVO")], **kw)
    assert len(llamadas) == 2


def test_juez_externo_no_guarda_las_llamadas_sin_respuesta(tmp_path, monkeypatch):
    """Sin respuesta de Groq (cupo agotado) no se guarda: si se guardara, el
    fallo quedaria 'resuelto' para siempre y nunca se reintentaria."""
    from tools.evaluation import external_judge

    path = tmp_path / "groq.jsonl"
    monkeypatch.setattr(external_judge, "call_groq", lambda s, u, m: "")
    external_judge.score_batch([_Fila(1, "q", "ref", "resp")], progress_every=0, checkpoint_path=path)
    assert not path.exists()
