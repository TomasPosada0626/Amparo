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
#   - 1305/231, c60fdd30...: seis categorias nuevas de abstencion (126
#     ejemplos, ids 1411-1536) para que el modelo aprenda a decir "no puedo
#     verificarlo" en vez de inventar. Antes ninguna de las 1410 respuestas
#     se abstenia explicitamente, y esa brecha era justo la que median los
#     casos adversariales del eval set de M2. Otra vez: cambiaron los datos,
#     no la logica de particion.
GOLDEN_VAL_IDS_SHA256 = (
    "c60fdd3022ef369d9145217fdf1f9c51208263d9a5e92619d8a127f731a317e5"
)


def test_stratified_split_matches_m1_golden_split():
    records = dataset.load_records()
    train, val = dataset.stratified_split(records)

    assert len(train) == 1305
    assert len(val) == 231

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
