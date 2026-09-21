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
