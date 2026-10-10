"""Registra en el CSV el dictamen aprobado de las 8 etiquetas B2.

Las ocho estaban en `pendiente` desde la preadjudicacion. El dictamen esta en
`docs/m1_b2_dictamen_8_etiquetas.md` y se aprobo el 2026-10-10.

Dos validaciones distintas, y se registran por separado porque no son lo mismo:

  Leonardo Galeano   abogado. Valida la clasificacion.
  ChatGPT            validacion metodologica asistida. Pidio expresamente que
                     su firma NO diga "abogado", porque no lo es y su
                     aprobacion no sustituye la validacion profesional.

Solo toca dos columnas de ocho filas, mas la firma. Todo lo demas queda igual
-- en particular los 35 `comparacion_v1_v2`, que siguen en `pendiente` -- y el
script lo comprueba antes de escribir: si algun otro campo cambiaria, no
escribe nada.

    python -m tools.aplicar_dictamen_b2 --check   # muestra el diff, no escribe
    python -m tools.aplicar_dictamen_b2
"""
from __future__ import annotations

import argparse
import csv

from tools.adjudicacion_b2 import COLUMNAS, SALIDA, respuestas, revisar

# caso -> (validez, confianza). Del dictamen aprobado sin cambios.
DICTAMEN = {
    "3328": ("valido", "baja"),
    "3517": ("modo_mal_asignado", "media"),
    "3822": ("valido", "media"),
    "3920": ("valido", "alta"),
    "4226": ("modo_mal_asignado", "alta"),
    "4321": ("modo_mal_asignado", "alta"),
    "4324": ("valido", "baja"),
    "4724": ("valido", "baja"),
}

FIRMA = ("primera pasada: pertinencia por ChatGPT, verificacion mecanica por Claude. "
         "Dictamen de las 8 etiquetas aprobado el 2026-10-10 por Leonardo Galeano "
         "(abogado) y por ChatGPT (validacion metodologica asistida por IA, "
         "no sustituye la validacion juridica profesional)")

# Lo unico que esta corrida puede tocar.
EDITABLES = {"validez_etiqueta_b2", "confianza", "revisor"}


def aplicar(filas: list[dict]) -> tuple[list[dict], list[str]]:
    """(filas nuevas, descripcion de los cambios)."""
    nuevas, cambios = [], []
    for f in filas:
        g = dict(f)
        cid = f["case_id"]
        if cid in DICTAMEN:
            validez, conf = DICTAMEN[cid]
            if f["validez_etiqueta_b2"] != validez:
                cambios.append(f"{cid} validez: {f['validez_etiqueta_b2']} -> {validez}")
                g["validez_etiqueta_b2"] = validez
            if f["confianza"] != conf:
                cambios.append(f"{cid} confianza: {f['confianza']} -> {conf}")
                g["confianza"] = conf
            g["revisor"] = FIRMA
        nuevas.append(g)
    return nuevas, cambios


def campos_tocados(antes: list[dict], despues: list[dict]) -> set[str]:
    tocados = set()
    for a, b in zip(antes, despues):
        tocados |= {c for c in COLUMNAS if a.get(c) != b.get(c)}
    return tocados


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="muestra el diff sin escribir")
    args = p.parse_args(argv)

    with SALIDA.open(encoding="utf-8", newline="") as f:
        antes = list(csv.DictReader(f))
    despues, cambios = aplicar(antes)

    tocados = campos_tocados(antes, despues)
    de_mas = tocados - EDITABLES
    if de_mas:
        raise SystemExit(f"Se tocarian campos que no corresponden: {sorted(de_mas)}")

    for c in cambios:
        print(f"  {c}")
    print()
    print(f"campos tocados: {sorted(tocados)}")
    pend = sum(1 for f in despues if f["comparacion_v1_v2"] == "pendiente")
    print(f"comparativos en pendiente: {pend}/35")

    problemas = revisar(despues, textos=respuestas())
    if problemas:
        for s in problemas[:10]:
            print(f"  - {s}")
        raise SystemExit(f"{len(problemas)} problemas: no se escribe nada")

    if args.check:
        print("\n--check: no se escribio nada.")
        return 0

    with SALIDA.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(despues)
    print(f"\nEscrito {SALIDA.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
