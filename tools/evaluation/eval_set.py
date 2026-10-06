"""Carga del eval set propio de M2 (data/eval_set.json): ejemplos gold
escritos a mano (no sacados del dataset de entrenamiento/validacion de M1)
mas casos adversariales, cada uno con un campo 'criterio' explicito que
describe que debe/no debe hacer la respuesta -- no solo que tan parecida es
al texto de referencia. Mismo esquema que data/dataset_legal.jsonl
(messages: system/user/assistant) para poder reusar
generation.generate_batch sin cambios.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.evaluation import config

EVAL_SET_PATH = config.PROJECT_ROOT / "data" / "eval_set.json"

REQUIRED_FIELDS = ("id", "category", "tipo", "criterio", "messages")
VALID_TIPOS = ("gold", "adversarial")

# Categorias de los adversariales: una por cada tipo de abstencion que el
# dataset ensena (ids 1411-1536), para leer el resultado por tipo.
CATEGORIAS_ADVERSARIALES = (
    "Adversarial - fuera de jurisdiccion",
    "Adversarial - cita exacta requerida",
    "Adversarial - garantia de resultado",
    "Adversarial - solicitud de conducta ilegitima",
    "Adversarial - pregunta ambigua",
    "Adversarial - urgencia fuera de alcance",
)

# --- Fuga por parecido (no solo por coincidencia exacta) ---------------------
#
# solapamiento() solo ve preguntas identicas. El 2026-10-06, con los 126
# ejemplos de abstencion ya en train, se comparo cada pregunta del eval set con
# las de train por TF-IDF (similitud.py) y se revisaron a mano todas las de
# coseno >= UMBRAL_PARECIDO. Cada caso queda en una de dos listas; un caso
# nuevo por encima del umbral que no este en ninguna rompe
# tests/evaluation/test_eval_set.py, y el notebook de M2 no corre mientras
# quede alguno de PENDIENTES en el eval set.
UMBRAL_PARECIDO = 0.55

# Mismo caso que una pregunta de train, con otras palabras: miden memoria, no
# generalizacion. Hay que quitarlas (no reescribirlas con el mismo id).
# id del eval set -> (id en train, por que)
PENDIENTES: dict[int, tuple[int, str]] = {
    # Vacia desde el 2026-10-06: los ocho casos que habia (9003, 9006, 9008,
    # 9028, 9047, 9103, 9105, 9106) se quitaron del eval set. Se vuelve a
    # llenar si aparece otra pregunta que repita un caso de train, como paso
    # intermedio antes de borrarla.
}

# Por encima del umbral, pero revisadas: preguntan otra cosa.
REVISADAS_DISTINTAS: dict[int, str] = {
    9017: "el Estado paga tarde un contrato; 970 es una pension que llega tarde",
    9020: "acto administrativo sin notificar; 22 es una notificacion fuera de tiempo",
    9027: "pregunta abierta por la muerte de un familiar; 369 pregunta solo si el SOAT cubre el funeral",
    9029: "desistir de una demanda; 1293 es reformarla",
    9041: "embargo de la cuenta de nomina propia; 490 es la cuenta de nomina de una empresa",
    9101: "en ingles; el parecido con 1496 ('Eso es legal?') es solo la palabra 'legal'",
}


def load_eval_set(path: Path = EVAL_SET_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        records: list[dict] = json.load(f)
    return records


def gold_examples(records: list[dict]) -> list[dict]:
    return [r for r in records if r["tipo"] == "gold"]


def adversarial_examples(records: list[dict]) -> list[dict]:
    return [r for r in records if r["tipo"] == "adversarial"]


def _normalizar_pregunta(texto: str) -> str:
    import re
    import unicodedata

    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


def solapamiento(eval_records: list[dict], train_records: list[dict], val_records: list[dict]) -> dict:
    """Ids del eval set cuya pregunta (normalizada) aparece en train o en val.

    En train seria fuga: el modelo habria visto la pregunta con su respuesta.
    En val no es fuga, pero esos casos no son "propios": repiten preguntas de
    la validacion de M1. Al 2026-10-04, 20 de las 50 gold (9011-9030) son copia
    literal de preguntas de validacion y ninguna esta en train."""
    def preguntas(rs):
        return {_normalizar_pregunta(r["messages"][1]["content"]) for r in rs}

    en_train, en_val = preguntas(train_records), preguntas(val_records)
    salida = {"en_train": [], "en_val": []}
    for r in eval_records:
        q = _normalizar_pregunta(r["messages"][1]["content"])
        if q in en_train:
            salida["en_train"].append(r["id"])
        elif q in en_val:
            salida["en_val"].append(r["id"])
    return salida


def parecidas_en_train(
    eval_records: list[dict], train_records: list[dict], umbral: float = UMBRAL_PARECIDO
) -> list[dict]:
    """Preguntas del eval set cuya pregunta mas parecida de train supera el
    umbral (coseno TF-IDF), de mayor a menor parecido."""
    from tools.evaluation.similitud import IndiceTfidf

    indice = IndiceTfidf([r["messages"][1]["content"] for r in train_records])
    salida = []
    for r in eval_records:
        pregunta = r["messages"][1]["content"]
        mejor = indice.parecidos(pregunta, 1)
        if mejor and mejor[0][1] >= umbral:
            t = train_records[mejor[0][0]]
            salida.append({"id": r["id"], "train_id": t["id"], "similitud": mejor[0][1],
                           "pregunta": pregunta, "pregunta_train": t["messages"][1]["content"]})
    return sorted(salida, key=lambda d: -d["similitud"])


def fuga_por_parecido(eval_records: list[dict], train_records: list[dict]) -> dict:
    """Lo que impide correr M2 con este eval set:
    - pendientes: ids de PENDIENTES que siguen en el eval set.
    - sin_revisar: preguntas sobre el umbral que no estan en ninguna lista
      (hay que leerlas y decidir: quitarla o agregarla a REVISADAS_DISTINTAS)."""
    ids = {r["id"] for r in eval_records}
    parecidas = parecidas_en_train(eval_records, train_records)
    return {
        "pendientes": sorted(i for i in PENDIENTES if i in ids),
        "sin_revisar": [p for p in parecidas if p["id"] not in PENDIENTES and p["id"] not in REVISADAS_DISTINTAS],
    }
