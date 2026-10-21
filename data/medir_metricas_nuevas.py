"""
Recalcula, sobre los artefactos de la corrida, las métricas añadidas DESPUÉS.

POR QUÉ ESTO NO ES UNA CORRIDA

`recall_clase_critica` y `pertinencia_citas_depurada` se escribieron después
de `m1/20261021T115654Z`, así que su scorecard no las trae. Pero ninguna de las
dos necesita el modelo: necesitan las **predicciones**, que están publicadas en
`results/m1_predicciones.json`, y el gold. Recalcularlas es leer artefactos, no
volver a generar nada — lo mismo que hace `data/descomponer_baseline.py`.

Lo que **no** se hace: escribirlas dentro de `m1_scorecard_finetuned.json`. Ese
archivo es el artefacto de una corrida y lleva su `_corrida`; meterle cifras
calculadas después lo convertiría en un registro falso de lo que esa corrida
produjo. Van a `data/`, excluidas de la huella, y el reporte las lee de ahí
declarando su procedencia.

    python -I data/medir_metricas_nuevas.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import metricas                                            # noqa: E402
import schema                                              # noqa: E402

RUTA_OUT = RAIZ / "data" / "metricas_posteriores.json"
PREDS = RAIZ / "results" / "m1_predicciones.json"


def main() -> int:
    d = json.loads(PREDS.read_text(encoding="utf-8"))
    corrida = d.get("_corrida") if isinstance(d, dict) else None
    filas = d.get("datos", d) if isinstance(d, dict) else d

    ev = {e["id"]: e for e in schema.cargar(archivo="eval_set_v3.json")}
    faltan = [p["id"] for p in filas if p["id"] not in ev]
    if faltan:
        raise SystemExit(
            f"{len(faltan)} predicciones no están en el eval set vigente "
            f"({', '.join(faltan[:5])}): las predicciones y el gold son de "
            "versiones distintas y nada de lo que saliera de aquí valdría.")

    golds = [ev[p["id"]] for p in filas]
    out = {"_que_es": ("metricas anadidas DESPUES de la corrida, recalculadas "
                       "de sus artefactos. No es una corrida: no toca el "
                       "modelo, solo lee las predicciones publicadas."),
           "_corrida_de_las_predicciones": corrida,
           "_por_que_no_va_en_el_scorecard": (
               "`m1_scorecard_finetuned.json` es el artefacto de una corrida y "
               "lleva su `_corrida`. Meterle cifras calculadas despues lo "
               "convertiria en un registro falso de lo que esa corrida "
               "produjo."),
           "brazos": {}}

    for nombre, campo in (("finetuned", "finetuned"), ("base", "base")):
        sal = [p[campo] for p in filas]
        pred = [schema.parse_salida(x) for x in sal]
        pm = [p.get("mecanismo") for p in pred]
        gm = [g.get("mecanismo") for g in golds]

        dep, quit_ = [], []
        for x in sal:
            y, q = schema.depurar_citas(x)
            dep.append(y)
            quit_ += q
        cruda = metricas.pertinencia_citas(sal, golds)
        depu = metricas.pertinencia_citas(dep, golds)

        # LA COMPROBACION QUE LIMITA LA CAPA, aqui tambien y no solo en la
        # prueba: si depurar movio el acierto, la capa toco algo mas que las
        # citas y la cifra no se puede publicar.
        aj_a = metricas.acierto_juridico(pred, golds)
        aj_b = metricas.acierto_juridico(
            [schema.parse_salida(x) for x in dep], golds)
        if aj_a != aj_b:
            raise SystemExit(
                f"depurar movio el acierto juridico de {aj_a} a {aj_b} en el "
                f"brazo {nombre}. La capa solo puede quitar citas.")

        out["brazos"][nombre] = {
            "n": len(filas),
            "recall_clase_critica": metricas.recall_clase_critica(pm, gm),
            "pertinencia_citas": {
                k: v for k, v in cruda.items() if k != "por_plano"},
            "pertinencia_citas_depurada": {
                **{k: v for k, v in depu.items() if k != "por_plano"},
                "citas_quitadas": len(quit_),
            },
            "acierto_juridico_sin_depurar": round(aj_a, 4),
            "acierto_juridico_depurado": round(aj_b, 4),
        }

    RUTA_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                        encoding="utf-8", newline="\n")

    ft = out["brazos"]["finetuned"]
    rc = ft["recall_clase_critica"]
    print("=" * 78)
    print("  METRICAS POSTERIORES · recalculadas de los artefactos, sin correr")
    print("=" * 78)
    print(f"  predicciones de m1/{corrida} · n={ft['n']}")
    print()
    print("  RECALL DE CLASE CRITICA (el falso negativo que cuesta)")
    for c, v in rc["por_clase"].items():
        if v.get("recall") is None:
            print(f"    {c:<16} {v['motivo']}")
            continue
        ic = v["ic"]
        print(f"    {c:<16} {v['aciertos']}/{v['soporte']} = {v['recall']}"
              f"  IC [{ic['ic_bajo']}, {ic['ic_alto']}]")
        if v["a_que_fueron"]:
            print(f"    {'':<16} los fallos fueron a {v['a_que_fueron']}")
    ica = rc["ic_agregado"]
    print(f"    {'AGREGADO':<16} {rc['recall_agregado']}  "
          f"IC [{ica['ic_bajo']}, {ica['ic_alto']}]  soporte {rc['soporte_total']}")
    print()
    print("  PERTINENCIA DE CITAS")
    a, b = ft["pertinencia_citas"], ft["pertinencia_citas_depurada"]
    print(f"    {'':<22}{'citas':>7}{'impert.':>9}{'precision':>11}{'recall':>9}")
    print(f"    {'tal como responde':<22}{a['citas_emitidas']:>7}"
          f"{a['impertinentes']:>9}{a['precision_citas']:>11.4f}"
          f"{a['recall_citas']:>9.4f}")
    print(f"    {'depurada':<22}{b['citas_emitidas']:>7}"
          f"{b['impertinentes']:>9}{b['precision_citas']:>11.4f}"
          f"{b['recall_citas']:>9.4f}")
    print(f"    quita {b['citas_quitadas']} citas · acierto juridico "
          f"{ft['acierto_juridico_sin_depurar']} -> "
          f"{ft['acierto_juridico_depurado']} (tiene que ser igual)")
    print()
    print(f"  escrito: data/{RUTA_OUT.name}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
