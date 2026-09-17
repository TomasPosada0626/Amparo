from tools.evaluation import eval_set


def test_eval_set_has_at_least_10_gold_and_3_adversarial():
    records = eval_set.load_eval_set()
    gold = eval_set.gold_examples(records)
    adversarial = eval_set.adversarial_examples(records)

    assert len(gold) >= 10
    assert len(adversarial) >= 3


def test_every_record_has_required_fields_and_valid_tipo():
    records = eval_set.load_eval_set()
    for r in records:
        for field in eval_set.REQUIRED_FIELDS:
            assert field in r, f"falta '{field}' en el registro {r.get('id')}"
        assert r["tipo"] in eval_set.VALID_TIPOS
        assert r["criterio"].strip() != "", f"criterio vacio en {r['id']}"


def test_every_record_has_well_formed_messages():
    records = eval_set.load_eval_set()
    for r in records:
        roles = [m["role"] for m in r["messages"]]
        assert roles == ["system", "user", "assistant"]
        for m in r["messages"]:
            assert m["content"].strip() != ""


def test_ids_are_unique_and_do_not_collide_with_m1_dataset_ids():
    records = eval_set.load_eval_set()
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids)), "hay ids duplicados en eval_set.json"
    # data/dataset_legal.jsonl usa ids 1..1320 -- eval_set.json usa un rango
    # aparte (9000+) para que nunca se puedan confundir con un id de M1.
    assert all(i >= 9000 for i in ids)
