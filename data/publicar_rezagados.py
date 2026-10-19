"""Copia a `results/` dos artefactos que la corrida produjo y no publicó.

QUÉ HACE Y QUÉ NO

`fertilidad_tokenizadores.json` y `cobertura_clasificador.json` son la
evidencia empírica del comportamiento del tokenizador sobre el dominio: lo que
sostiene la elección del modelo base. La corrida m1/20261018T074101Z los
generó, pero `arranque.ORDEN` no los declaraba, así que se quedaron en
`runs/` y nunca llegaron a `results/`. Medir algo y no publicarlo cuesta lo
mismo que no medirlo.

Esto **copia**, no calcula. Es la misma operación que `Corrida.publicar()`
hace dentro del notebook —leer el artefacto de la carpeta de la corrida y
escribirlo en `results/` con su sello `_corrida`/`_modulo`/`_artefacto`—
aplicada después. El sello dice la corrida que de verdad los produjo, así que
`verificar_entrega.py` sigue viendo un solo id en M1.

LA LÍNEA QUE NO SE CRUZA

Copiar un artefacto que la corrida produjo es legítimo. *Calcular* uno fuera
de la corrida y dejarlo con el sello de esa corrida no lo es: eso es
fabricar procedencia. Por eso este script solo copia, se niega si el archivo
de origen no está, y comprueba que el `corrida.json` de la carpeta coincida
con el id que va a sellar.

`arranque.ORDEN` ya los declara, así que la próxima corrida de M1 los publica
sola y este script deja de hacer falta.

    python -I data/publicar_rezagados.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

CORRIDA_M1 = "20261018T074101Z"
REZAGADOS = [
    ("fertilidad_tokenizadores", "m1_fertilidad_tokenizadores.json"),
    ("cobertura_clasificador", "m1_cobertura_clasificador.json"),
]


def main() -> int:
    origen_dir = RAIZ / "runs" / "m1" / CORRIDA_M1
    destino_dir = RAIZ / "results"

    print("=" * 74)
    print(f"  Publicar rezagados de m1/{CORRIDA_M1}")
    print("=" * 74)

    if not origen_dir.is_dir():
        print(f"  No esta {origen_dir.relative_to(RAIZ)}.")
        print("  Trae esa carpeta de Drive (o al menos estos archivos):")
        for nombre, _ in REZAGADOS:
            print(f"    runs/m1/{CORRIDA_M1}/{nombre}.json")
        print(f"    runs/m1/{CORRIDA_M1}/corrida.json")
        return 1

    # El id que se va a sellar tiene que ser el de la corrida de esa carpeta,
    # no el del nombre del directorio: si alguien renombro la carpeta, el
    # sello mentiria.
    cj = origen_dir / "corrida.json"
    if cj.exists():
        real = json.loads(cj.read_text(encoding="utf-8")).get("id")
        if real != CORRIDA_M1:
            print(f"  La carpeta se llama {CORRIDA_M1} pero su corrida.json "
                  f"dice `{real}`. No se sella nada: el id del sello tiene "
                  "que ser el de la corrida que produjo el artefacto.")
            return 1
    else:
        print(f"  aviso: no esta corrida.json en {origen_dir.name}, no se "
              "pudo confirmar que el id de la carpeta sea el de la corrida.")

    hechos, faltan = [], []
    for nombre, destino in REZAGADOS:
        o = origen_dir / f"{nombre}.json"
        if not o.exists():
            faltan.append(f"runs/m1/{CORRIDA_M1}/{nombre}.json")
            continue
        obj = json.loads(o.read_text(encoding="utf-8"))
        sello = {"_corrida": CORRIDA_M1, "_modulo": "m1",
                 "_artefacto": o.name,
                 "_publicado_despues_de_la_corrida": (
                     "lo genero la corrida y `arranque.ORDEN` no lo "
                     "declaraba, asi que se quedo en runs/. Copiado con "
                     "data/publicar_rezagados.py; no se recalculo nada.")}
        cuerpo = ({**sello, **obj} if isinstance(obj, dict)
                  else {**sello, "datos": obj})
        d = destino_dir / destino
        d.write_text(json.dumps(cuerpo, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8", newline="\n")
        hechos.append(destino)
        print(f"  publicado -> results/{destino}")

    for f in faltan:
        print(f"  FALTA {f}")
    print("=" * 74)
    if faltan:
        print(f"  {len(hechos)} publicado(s), {len(faltan)} sin traer.")
        return 1
    print(f"  {len(hechos)} artefactos publicados, sellados con "
          f"m1/{CORRIDA_M1}.")
    print("  Ahora `python reproducir.py` deberia salir con 0.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
