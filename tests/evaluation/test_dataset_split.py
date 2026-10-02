import hashlib

from tools.evaluation import dataset

# Hash dorado del split de validacion de M1 (RANDOM_SEED=42, VAL_FRACTION=0.15),
# recalculado y verificado de forma independiente contra data/dataset_legal.jsonl.
# Si este test falla, el split dejo de ser reproducible respecto a la corrida
# publicada -- no "arreglar" el hash sin entender por que cambio.
#
# Historial de cambios del dorado (cada entrada necesita una razon, justamente
# para que actualizarlo no se vuelva un reflejo):
#   - 1119/201, a37d9534...: dataset original de 1320 ejemplos en 24 categorias.
#   - 1197/213, 0c4963b9...: reconstruccion del dataset (1410 ejemplos, 27
#     categorias) documentada en data/dataset_src/GUIA.md. El split cambio
#     porque cambiaron los datos, no la logica: stratified_split no se toco.
GOLDEN_VAL_IDS_SHA256 = (
    "0c4963b9f56170a244e2ff7d405742694cc7ae0abc168af1bb57a8fa4f831e1b"
)


def test_stratified_split_matches_m1_golden_split():
    records = dataset.load_records()
    train, val = dataset.stratified_split(records)

    assert len(train) == 1197
    assert len(val) == 213

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
