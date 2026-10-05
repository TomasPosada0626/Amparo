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


def test_ninguna_pregunta_del_eval_set_esta_en_train():
    """Fuga: si una pregunta del eval set esta en train, el modelo ya vio su
    respuesta y el eval set deja de medir generalizacion. Nada lo impedia: si
    el dataset cambia de nuevo, el split puede mover preguntas a train."""
    from tools.evaluation import dataset

    records = dataset.load_records()
    train, val = dataset.stratified_split(records)
    sol = eval_set.solapamiento(eval_set.load_eval_set(), train, val)
    assert sol["en_train"] == []


def test_las_gold_repetidas_de_validacion_estan_identificadas():
    """20 de las 50 gold repiten preguntas de validacion (no son fuga, pero
    tampoco son casos propios). Si cambia este conteo, revisar el eval set."""
    from tools.evaluation import dataset

    records = dataset.load_records()
    train, val = dataset.stratified_split(records)
    sol = eval_set.solapamiento(eval_set.load_eval_set(), train, val)
    assert sol["en_val"] == list(range(9011, 9031))
