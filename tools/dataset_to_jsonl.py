"""Convierte private/dataset_legal_30_ejemplos.md al formato JSONL de chat
(system/user/assistant) que usan trl.SFTTrainer y datasets.load_dataset.

Uso: python -m tools.dataset_to_jsonl
Genera: data/dataset_legal.jsonl
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from tools.model_comparator import config

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_MD = PROJECT_ROOT / "private" / "dataset_legal_30_ejemplos.md"
OUTPUT_JSONL = PROJECT_ROOT / "data" / "dataset_legal.jsonl"

CATEGORY_PATTERN = re.compile(r'^## Categoria:\s*(.+?)(?:\s*\(continuacion.*\))?\s*$', re.MULTILINE)
EXAMPLE_PATTERN = re.compile(
    r'### Ejemplo (?P<num>\d+)\s*\nEntrada:\s*\n"(?P<entrada>.*?)"\s*\n\s*\nSalida esperada:\s*\n"(?P<salida>.*?)"',
    re.DOTALL,
)

OUT_OF_SCOPE = "Fuera de las 9 categorias del producto"

# Los ejemplos 01-30 (los originales, antes de la ampliacion) nunca tuvieron
# encabezado "## Categoria: X" en el .md porque se escribieron antes de
# organizar el dataset por categoria. Se clasificaron manualmente aqui segun
# las 9 categorias reales de PRODUCT.md; los que no encajan en ninguna
# (propiedad intelectual, derecho de familia, derecho administrativo general,
# etc.) quedan marcados como fuera de alcance en vez de forzarlos a una
# categoria incorrecta.
LEGACY_CATEGORY_BY_ID = {
    1: "Salud / EPS",
    2: "Salud / EPS",
    3: "Despido",
    4: "Arriendo",
    5: "Reporte en centrales de riesgo",
    6: "Accidentes de transito",
    7: "Relaciones laborales",
    8: "Garantias de consumo",
    9: "Embargos",
    10: "Comparendos de transito",
    11: "Educacion / debido proceso disciplinario",
    12: "Derecho contractual general",
    13: "Contratacion estatal y facturacion",
    14: "Derecho de familia - alimentos",
    15: "Acceso a informacion publica",
    16: "Relaciones laborales",  # contrato realidad
    17: "Salud / EPS",  # mala practica medica
    18: "Garantias de consumo",  # banco sigue cobrando tras pago total
    19: "Derecho ambiental sancionatorio",
    20: "Propiedad y linderos",
    21: "Pensiones y seguridad social",
    22: "Derecho administrativo general",
    23: "Propiedad intelectual - marcas",
    24: "Prestamos informales y usura",
    25: "Garantias de consumo",  # bloqueo de cuenta digital
    26: "Conciliacion prejudicial",
    27: "Despido",  # liquidacion laboral no entregada
    28: "Licencias urbanisticas",
    29: "Contratos empresariales (B2B)",
    30: "Procedimiento civil - recursos",
}


def parse_examples(md_text: str) -> list[dict]:
    # Mapea cada offset de "## Categoria: X" a su nombre, para asignarle a cada
    # ejemplo la categoria vigente en ese punto del archivo.
    category_marks = [(m.start(), m.group(1).strip()) for m in CATEGORY_PATTERN.finditer(md_text)]

    def category_at(num: int, offset: int) -> str:
        if num in LEGACY_CATEGORY_BY_ID:
            return LEGACY_CATEGORY_BY_ID[num]
        current = OUT_OF_SCOPE
        for mark_offset, name in category_marks:
            if mark_offset > offset:
                break
            current = name
        return current

    examples = []
    for match in EXAMPLE_PATTERN.finditer(md_text):
        num = int(match.group("num"))
        entrada = match.group("entrada").strip()
        salida = match.group("salida").strip()
        examples.append(
            {
                "num": num,
                "category": category_at(num, match.start()),
                "query": entrada,
                "response": salida,
            }
        )
    return examples


def to_chat_record(example: dict) -> dict:
    return {
        "id": example["num"],
        "category": example["category"],
        "messages": [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": example["query"]},
            {"role": "assistant", "content": example["response"]},
        ],
    }


def main() -> None:
    md_text = SOURCE_MD.read_text(encoding="utf-8")
    examples = parse_examples(md_text)
    if not examples:
        raise SystemExit(f"No se encontraron ejemplos en {SOURCE_MD}")

    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSONL.open("w", encoding="utf-8") as f:
        for example in examples:
            record = to_chat_record(example)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"{len(examples)} ejemplos escritos en {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()
