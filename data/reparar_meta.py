"""
Recalcula el `meta` de los sets de datos a partir de sus propios `ejemplos`.

EL DEFECTO QUE LO MOTIVA, MEDIDO

`data/ampliar_categorias.py` anadio 17 casos al dataset (143 -> 160) y subio
la version a 3.5.0, y **no toco `meta`**. Resultado:

    meta.splits            {"train": 106, "validation": 37}   suma 143
    real                   {"train": 123, "validation": 37}   suma 160
    meta.balance_mecanismo suma 143

Un `meta` que contradice a sus propios `ejemplos` es peor que no tenerlo:
parece verificado. Y no se queda en el archivo --- la cabecera de M1 citaba
«143 ejemplos, 106 de train», que es lo que el meta decia.

`eval_set_v3.json` tiene una version mas leve del mismo problema:
`balance_mecanismo` omite los 6 casos de abstencion mientras el de v2 si los
incluye, y v3 es superconjunto estricto de v2. Las cuentas de los cinco
mecanismos son correctas; lo que falla es que comparar los dos balances
sugiere que v3 perdio las abstenciones.

QUE NO SE TOCA, Y POR QUE

`eval_set.json` --- el v1 --- declara `{"tutela": 27, "no_tutela": 19,
"baseline_clase_mayoritaria": 0.587}`: es el esquema BINARIO de antes de que
el vocabulario fuera de cinco mecanismos, con una proporcion dentro del mismo
dict. No esta mal: esta en otro formato. Y v1 es el puente de comparacion ---
una prueba fija que cada version contiene a la anterior **sin tocar un
byte** --- asi que reescribirlo rompe justo la propiedad que lo hace util.

    python -I data/reparar_meta.py            # dice que cambiaria
    python -I data/reparar_meta.py --escribir # lo escribe
"""
from __future__ import annotations
import collections
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import schema                                              # noqa: E402

# El v1 va fuera a proposito: otro esquema y, sobre todo, el puente de
# comparacion que una prueba exige intacto byte a byte.
INTOCABLES = {"eval_set.json"}

CLAVE_ABSTENCION = "abstencion"


def balance(ejemplos: list[dict]) -> dict:
    """Cuantos casos por mecanismo, con la abstencion contada por su nombre.

    `mecanismo: None` es la abstencion y se cuenta: omitirla hace que el
    balance no sume el total y que comparar dos versiones sugiera que una
    perdio casos. El orden es por frecuencia, como el que ya escribian los
    constructores.
    """
    c = collections.Counter(e.get("mecanismo") or CLAVE_ABSTENCION
                            for e in ejemplos)
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))


def splits(ejemplos: list[dict]) -> dict:
    c = collections.Counter(e["split"] for e in ejemplos if e.get("split"))
    return dict(sorted(c.items()))


def _es_vocabulario_de_mecanismos(declarado: dict | None) -> bool:
    """¿El balance declarado usa el vocabulario de cinco mecanismos?

    Es lo que separa «esta mal» de «esta en otro formato». Sin esta pregunta,
    el v1 sale marcado como defectuoso y el arreglo seria reescribir el
    puente de comparacion, que es lo contrario de lo que hay que hacer.
    """
    if not isinstance(declarado, dict) or not declarado:
        return False
    permitidas = set(schema.MECANISMOS) | {CLAVE_ABSTENCION}
    return set(declarado) <= permitidas


def revisar(ruta: Path) -> list[tuple[str, object, object]]:
    """Las claves de `meta` que no cuadran con los `ejemplos`."""
    d = json.loads(ruta.read_text(encoding="utf-8"))
    ej, meta = d.get("ejemplos") or [], d.get("meta") or {}
    fuera = []
    if "splits" in meta and dict(meta["splits"]) != splits(ej):
        fuera.append(("splits", meta["splits"], splits(ej)))
    dec = meta.get("balance_mecanismo")
    if _es_vocabulario_de_mecanismos(dec) and dict(dec) != balance(ej):
        fuera.append(("balance_mecanismo", dec, balance(ej)))
    return fuera


def main() -> int:
    escribir = "--escribir" in sys.argv
    print("=" * 76)
    print("  META CONTRA SUS PROPIOS EJEMPLOS")
    print("=" * 76)
    tocados = 0
    for ruta in sorted((RAIZ / "data").glob("*.json")):
        d = json.loads(ruta.read_text(encoding="utf-8"))
        if not isinstance(d, dict) or "ejemplos" not in d:
            continue
        if ruta.name in INTOCABLES:
            print(f"  {ruta.name:<22} INTOCABLE (otro esquema y puente de "
                  "comparacion)")
            continue
        fuera = revisar(ruta)
        if not fuera:
            print(f"  {ruta.name:<22} ok · {len(d['ejemplos'])} ejemplos")
            continue
        tocados += 1
        print(f"  {ruta.name:<22} {len(fuera)} clave(s) DISCREPAN "
              f"· {len(d['ejemplos'])} ejemplos")
        for clave, antes, ahora in fuera:
            print(f"      {clave}")
            print(f"        declara : {json.dumps(antes, ensure_ascii=False)}")
            print(f"        real    : {json.dumps(ahora, ensure_ascii=False)}")
            if escribir:
                d["meta"][clave] = ahora
        if escribir:
            ruta.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                            encoding="utf-8", newline="\n")
    print()
    if not tocados:
        print("  todos los meta cuadran con sus ejemplos.")
    elif escribir:
        print(f"  {tocados} archivo(s) reescritos. OJO: `data/*.json` esta en")
        print("  la huella del manifiesto, asi que hay que volver a sellar")
        print("  (`python -I data/preparar_subida.py --sellar`) y subir.")
    else:
        print(f"  {tocados} archivo(s) discrepan. Corre con `--escribir`.")
    print("=" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
