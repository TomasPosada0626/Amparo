import hashlib

from tools.evaluation import dataset

# Hash dorado del split de validacion de M1 (RANDOM_SEED=42, VAL_FRACTION=0.15),
# recalculado y verificado de forma independiente contra data/dataset_legal.jsonl
# antes de escribir este test. Si este test falla, el split dejo de ser
# reproducible respecto al baseline ya publicado en la wiki -- no "arreglar"
# el hash sin entender por que cambio.
GOLDEN_VAL_IDS_SHA256 = (
    "a37d95349b71adf6b5a439e29d899af782ae7404b4c531145bf0ae3c923cfabb"
)


def test_stratified_split_matches_m1_golden_split():
    records = dataset.load_records()
    train, val = dataset.stratified_split(records)

    assert len(train) == 1119
    assert len(val) == 201

    val_ids = sorted(r["id"] for r in val)
    digest = hashlib.sha256(",".join(str(i) for i in val_ids).encode()).hexdigest()
    assert digest == GOLDEN_VAL_IDS_SHA256


def test_stratified_split_is_deterministic_across_calls():
    records = dataset.load_records()
    _, val_a = dataset.stratified_split(records)
    _, val_b = dataset.stratified_split(records)
    assert [r["id"] for r in val_a] == [r["id"] for r in val_b]


def test_stratified_split_covers_every_record_exactly_once():
    records = dataset.load_records()
    train, val = dataset.stratified_split(records)

    train_ids = {r["id"] for r in train}
    val_ids = {r["id"] for r in val}
    all_ids = {r["id"] for r in records}

    assert train_ids.isdisjoint(val_ids)
    assert train_ids | val_ids == all_ids
    assert len(train) + len(val) == len(records)


def test_system_prompt_matches_first_record():
    records = dataset.load_records()
    assert dataset.system_prompt(records) == records[0]["messages"][0]["content"]
