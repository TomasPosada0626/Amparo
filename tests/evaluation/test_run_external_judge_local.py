import json

from tools.evaluation.run_external_judge_local import build_pairs, load_results


def _write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


def _row(id_, generated, label):
    return {
        "id": id_, "category": "Arriendo", "query": "q", "expected": "e",
        "generated": generated, "label": label, "latency_s": 1.0,
    }


def test_load_results_parses_jsonl(tmp_path):
    path = tmp_path / "baseline.jsonl"
    _write_jsonl(path, [_row(1, "resp1", "baseline"), _row(2, "resp2", "baseline")])
    results = load_results(path)
    assert len(results) == 2
    assert results[0].id == 1
    assert results[0].generated == "resp1"


def test_load_results_skips_blank_lines(tmp_path):
    path = tmp_path / "baseline.jsonl"
    path.write_text(json.dumps(_row(1, "resp1", "baseline")) + "\n\n", encoding="utf-8")
    results = load_results(path)
    assert len(results) == 1


def test_build_pairs_matches_by_id():
    baseline = load_results_from_dicts([_row(1, "b1", "baseline"), _row(2, "b2", "baseline")])
    finetuned = load_results_from_dicts([_row(2, "f2", "fine_tuned"), _row(1, "f1", "fine_tuned")])
    pairs = build_pairs(baseline, finetuned)
    assert (1, "q", "b1", "f1") in pairs
    assert (2, "q", "b2", "f2") in pairs
    assert len(pairs) == 2


def test_build_pairs_skips_ids_without_counterpart():
    baseline = load_results_from_dicts([_row(1, "b1", "baseline"), _row(3, "b3", "baseline")])
    finetuned = load_results_from_dicts([_row(1, "f1", "fine_tuned")])
    pairs = build_pairs(baseline, finetuned)
    assert len(pairs) == 1
    assert pairs[0][0] == 1


def load_results_from_dicts(rows):
    from tools.evaluation.run_external_judge_local import LoadedResult
    return [LoadedResult(**{k: v for k, v in r.items() if k != "latency_s"}) for r in rows]
