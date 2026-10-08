"""Construye data/dataset_legal.jsonl desde fuentes versionadas y revisables.

Por que existe este modulo. La primera version del dataset se generaba con
tools/dataset_to_jsonl.py a partir de private/dataset_legal_30_ejemplos.md, un
archivo que esta en .gitignore y que ya no existe: el dataset quedo como un
artefacto congelado, imposible de regenerar y sin procedencia auditable. Peor
para un proyecto juridico: no habia forma de que un revisor (el estudiante y el
profesor de derecho que lo avalaron) revisara los cambios ejemplo por ejemplo en
un diff.

Aqui la fuente de verdad son archivos Markdown por categoria en data/dataset_src/,
versionados en el repo. Son legibles y revisables por alguien sin Python, el
build es determinista, y cualquier cambio en una respuesta aparece como una
linea en un diff de pull request.

    python -m tools.dataset_build --check   # valida las fuentes, no escribe
    python -m tools.dataset_build           # escribe data/dataset_legal.jsonl

El build NO pasa si las fuentes no cumplen las puertas de calidad de
tools/dataset_quality.py: no se entrena con un dataset que no las pase.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "data" / "dataset_src"
OUTPUT_JSONL = PROJECT_ROOT / "data" / "dataset_legal.jsonl"

# El system prompt del producto: unica fuente de verdad, de aqui lo toman el
# dataset, el comparador y el prompt aumentado de M3. Codifica los cuatro
# principios de PRODUCT.md (antes solo codificaba dos: faltaban el anclaje al
# mecanismo legal y el lenguaje accesible).
SYSTEM_PROMPT = (
    "Eres un asistente jurídico que responde consultas de derecho colombiano a personas "
    "sin formación jurídica. Responde de forma breve y en lenguaje claro y cotidiano. "
    "Señala el mecanismo legal aplicable (tutela, derecho de petición, habeas data, "
    "conciliación, restitución de inmueble, etc.) y qué evidencia debe reunir la persona. "
    "Sé prudente: no inventes normas ni cites artículos o plazos que no puedas verificar; "
    "si no estás seguro, dilo explícitamente. Si hay riesgo para la integridad o la salud "
    "de alguien, lo primero es orientar a la ayuda inmediata."
)

CABECERA = re.compile(r"^#\s*Categoria:\s*(?P<nombre>.+?)\s*$", re.MULTILINE)
EJEMPLO = re.compile(
    r"^##\s*(?P<id>\d+)\s*$\n+^P:\s*(?P<pregunta>.+?)$\n+^R:\s*(?P<respuesta>.+?)$",
    re.MULTILINE | re.DOTALL,
)


def es_fuente(path: Path) -> bool:
    """Solo son fuentes los .md cuya PRIMERA linea declara la categoria.

    Se exige en la primera linea y no en cualquier parte del archivo porque
    GUIA.md muestra el formato dentro de un bloque de codigo, y buscar la
    cabecera en todo el texto la tomaba como si fuera una categoria real.
    """
    primera = path.read_text(encoding="utf-8").lstrip().splitlines()[:1]
    return bool(primera and CABECERA.match(primera[0]))


def parsear_fuente(path: Path) -> tuple[str, list[dict]]:
    texto = path.read_text(encoding="utf-8")
    cabecera = CABECERA.search(texto)
    if not cabecera:
        raise SystemExit(f"{path.name}: falta la linea '# Categoria: <nombre>'")
    categoria = cabecera.group("nombre").strip()

    ejemplos = []
    for m in EJEMPLO.finditer(texto):
        pregunta = " ".join(m.group("pregunta").split())
        respuesta = " ".join(m.group("respuesta").split())
        ejemplos.append({"id": int(m.group("id")), "category": categoria,
                         "query": pregunta, "response": respuesta})
    if not ejemplos:
        raise SystemExit(f"{path.name}: no se encontro ningun ejemplo con el formato '## <id>' / 'P:' / 'R:'")
    return categoria, ejemplos


def construir(registros: list[dict]) -> list[dict]:
    return [
        {
            "id": e["id"],
            "category": e["category"],
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": e["query"]},
                {"role": "assistant", "content": e["response"]},
            ],
        }
        for e in registros
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="valida sin escribir el JSONL")
    args = parser.parse_args()

    if not SOURCE_DIR.exists():
        raise SystemExit(f"No existe {SOURCE_DIR}. Las fuentes por categoria viven ahi.")

    fuentes = [p for p in sorted(SOURCE_DIR.glob("*.md")) if es_fuente(p)]
    todos: list[dict] = []
    for fuente in fuentes:
        _categoria, ejemplos = parsear_fuente(fuente)
        todos.extend(ejemplos)

    ids = [e["id"] for e in todos]
    repetidos = {i for i in ids if ids.count(i) > 1}
    if repetidos:
        raise SystemExit(f"IDs repetidos entre fuentes: {sorted(repetidos)[:10]}")

    todos.sort(key=lambda e: e["id"])
    registros = construir(todos)

    # Puerta de calidad: no se escribe un dataset que no la pase.
    from tools.dataset_quality import analizar, reportar

    print(f"Fuentes: {len(fuentes)} archivos de categoria\n")
    fallos = reportar(analizar(registros))
    if fallos:
        print(f"\nNO se escribe el dataset: {len(fallos)} puerta(s) sin pasar -> {', '.join(fallos)}")
        sys.exit(1)

    if args.check:
        print("\n--check: las fuentes pasan todas las puertas. No se escribio nada.")
        return

    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSONL.open("w", encoding="utf-8") as f:
        for registro in registros:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    print(f"\n{len(registros)} ejemplos escritos en {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()
