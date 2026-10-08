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
    # Vacia desde el 2026-10-06. Eran 20 gold copiadas de la validacion de M1
    # (9011-9030): no eran fuga, porque estaban en val y no en train, pero
    # tampoco eran casos propios. Se reemplazaron por 19 preguntas nuevas con
    # ids desde 9051. Si esta lista vuelve a tener algo, alguien copio una
    # pregunta de la validacion en vez de escribir un caso nuevo.
    assert sol["en_val"] == []


def _train():
    from tools.evaluation import dataset

    return dataset.stratified_split(dataset.load_records())[0]


def test_toda_pregunta_parecida_a_train_esta_revisada():
    """La coincidencia exacta no ve las casi copias: 9028 ("El vendedor no
    cumplio la promesa de compraventa") y 622 de train ("El comprador no
    cumplio...") pasaban como distintas. Toda pregunta con coseno TF-IDF >=
    UMBRAL_PARECIDO contra train tiene que estar leida y en PENDIENTES (se
    quita) o en REVISADAS_DISTINTAS (pregunta otra cosa, con el motivo)."""
    sin_revisar = eval_set.fuga_por_parecido(eval_set.load_eval_set(), _train())["sin_revisar"]
    assert sin_revisar == [], (
        "Preguntas del eval set muy parecidas a una de train, sin revisar. Leer cada par: si es el "
        "mismo caso, quitarla; si pregunta otra cosa, agregarla a REVISADAS_DISTINTAS con el motivo:\n"
        + "\n".join(f"  {p['id']} ~ train {p['train_id']} ({p['similitud']}): {p['pregunta']!r} / "
                    f"{p['pregunta_train']!r}" for p in sin_revisar))


def test_las_revisadas_siguen_siendo_parecidas():
    """Una entrada de REVISADAS_DISTINTAS cuya pregunta ya no existe o ya no se
    parece es una excepcion vieja: se borra, para que no tape un caso nuevo con
    el mismo id."""
    parecidas = {p["id"] for p in eval_set.parecidas_en_train(eval_set.load_eval_set(), _train())}
    viejas = sorted(set(eval_set.REVISADAS_DISTINTAS) - parecidas)
    assert viejas == [], f"Borrar de REVISADAS_DISTINTAS: {viejas}"


def test_los_adversariales_usan_una_categoria_de_abstencion():
    for r in eval_set.adversarial_examples(eval_set.load_eval_set()):
        assert r["category"] in eval_set.CATEGORIAS_ADVERSARIALES, (
            f"{r['id']}: categoria {r['category']!r}; usar una de CATEGORIAS_ADVERSARIALES "
            "para que el scorecard lo cuente en su tipo de abstencion")
