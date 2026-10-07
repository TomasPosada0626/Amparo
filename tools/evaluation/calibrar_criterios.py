"""Calibracion de los criterios del eval set: el juez contra las referencias.

El problema que resuelve. La corrida del 2026-10-06 reporta que el eval set
"cumple" entre el 11 % y el 33 % segun el modelo y el tipo de caso. Esa cifra
no se puede interpretar: un 20 % puede significar que el modelo falla, que los
criterios estan mal escritos (exigen cosas que ni una respuesta correcta hace),
o que el juez es demasiado duro. Con los datos de esa corrida no hay forma de
distinguir cual de las tres.

La calibracion. Cada caso del eval set trae su propia respuesta de referencia,
escrita por el equipo y correcta por construccion. Si se la pasamos al MISMO
juez contra el MISMO criterio, su veredicto mide el techo: lo mejor que se
puede sacar. Si las referencias cumplen casi siempre, la vara esta bien puesta
y el 11-33 % habla de los modelos. Si las referencias tambien suspenden, el
problema son los criterios y hay que reescribirlos antes de sacar conclusiones.

Es la misma disciplina con la que se calibro la guardia de rutas, que se corre
sobre las referencias de validacion y marca 0.0 % ahi: sin esa fila, lo que la
guardia marca en los modelos no se sabria leer.

Uso (no necesita GPU ni Colab, solo GROQ_API_KEY en el .env):

    python -m tools.evaluation.calibrar_criterios
    python -m tools.evaluation.calibrar_criterios --salida results/m2_2026-10-06

Son 75 llamadas, una por caso del eval set. Con checkpoint: si se corta por
cupo, se vuelve a correr y sigue donde quedo.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from tools.evaluation import criterio, eval_set as eval_set_module

# label propio: no es un modelo, es el techo contra el que se comparan.
LABEL = "referencia"


def generaciones_de_referencia(registros: list[dict]) -> list[SimpleNamespace]:
    """La respuesta de referencia de cada caso, con la forma que espera
    evaluar_contra_criterio (.id/.query/.generated/.label)."""
    return [
        SimpleNamespace(
            id=r["id"],
            query=r["messages"][1]["content"],
            generated=r["messages"][2]["content"],
            label=LABEL,
        )
        for r in registros
    ]


def calibrar(salida: Path | None = None, checkpoint: Path | None = None) -> dict:
    registros = eval_set_module.load_eval_set()
    refs = generaciones_de_referencia(registros)
    juez = criterio.generador_groq()
    veredictos = criterio.evaluar_contra_criterio(
        refs, registros, juez, checkpoint_path=checkpoint, log_prefix="calibracion"
    )
    resumen = criterio.resumen(veredictos)

    if salida is not None:
        salida.mkdir(parents=True, exist_ok=True)
        (salida / "calibracion_criterios.json").write_text(
            json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with (salida / "calibracion_criterios.jsonl").open("w", encoding="utf-8") as f:
            for v in veredictos:
                f.write(json.dumps(v.__dict__, ensure_ascii=False) + "\n")
    return {"resumen": resumen, "veredictos": veredictos}


def informe(resumen: dict, veredictos: list) -> str:
    """Lectura directa: la vara esta bien puesta o no lo esta."""
    lineas = ["# Calibracion de los criterios del eval set", "",
              "El juez (Groq) contra las RESPUESTAS DE REFERENCIA, que son correctas por",
              "construccion. Mide el techo: lo mejor que un modelo podria sacar.", ""]
    por_tipo = resumen.get(LABEL, {})
    for tipo, d in sorted(por_tipo.items()):
        ic = d.get("aprobacion_ic95") or [None, None]
        lineas.append(
            f"- **{tipo}**: cumple {100 * (d['aprobacion'] or 0):.0f} % "
            f"[{100 * (ic[0] or 0):.0f}-{100 * (ic[1] or 0):.0f}] "
            f"(cumple {d['cumple']}, parcial {d['parcial']}, no cumple {d['no_cumple']}; n={d['n']}), "
            f"con errores juridicos {100 * (d['con_errores_juridicos'] or 0):.0f} %")
    lineas += ["", "## Como leerlo", "",
               "Si las referencias cumplen casi siempre, la vara esta bien y las cifras de los",
               "modelos se pueden interpretar tal cual. Si las referencias tambien suspenden, el",
               "criterio pide algo que ni una respuesta correcta hace: hay que reescribirlo antes",
               "de concluir nada sobre el modelo.", ""]

    fallos = [v for v in veredictos if v.veredicto != "cumple"]
    if fallos:
        lineas += [f"## Criterios a revisar ({len(fallos)} referencias que no cumplen su propio criterio)", ""]
        for v in fallos[:20]:
            lineas.append(f"- **{v.id}** ({v.tipo}) -> {v.veredicto}: {v.justificacion[:200]}")
    return "\n".join(lineas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--salida", type=Path, default=None,
                        help="carpeta donde escribir calibracion_criterios.json/.jsonl")
    parser.add_argument("--checkpoint", type=Path, default=None,
                        help="jsonl de checkpoint, para retomar si se corta por cupo")
    args = parser.parse_args()

    r = calibrar(salida=args.salida, checkpoint=args.checkpoint)
    print()
    print(informe(r["resumen"], r["veredictos"]))
    if args.salida:
        print(f"\nEscrito en {args.salida}")


if __name__ == "__main__":
    main()
