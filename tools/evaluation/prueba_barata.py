"""La prueba barata de un candidato, juzgada contra el protocolo.

`docs/m1_protocolo_aceptacion.md`, "La prueba barata de un candidato nuevo"
(fijada el 2026-10-13, antes de v4): seis filas automaticas, sin adjudicacion,
que el candidato tiene que cumplir TODAS antes de pagar la evaluacion completa.
Los umbrales viven aqui y en el protocolo; `tests/evaluation/test_prueba_barata.py`
comprueba que digan lo mismo.

Lee lo que escriben las dos herramientas que ya existen:

    tools/evaluation/escenarios.py --correr          -> <dir>/resumen.json
    tools/evaluation/sobreabstencion_gold.py --correr -> <dir>/resumen.json

Antes de juzgar comprueba que la medicion sea la que fija el protocolo: el
archivo de escenarios congelado, la revision del modelo base y el mismo
adaptador en las dos mediciones. Si se pasa el control (v1 medido en la misma
sesion), compara ademas con el buscador y la referencia del 2026-10-12.

    python -m tools.evaluation.prueba_barata --escenarios <dir> --gold <dir>
        [--control-escenarios <dir> --control-gold <dir>]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.evaluation import config

HUELLA_ESCENARIOS = "d51365fbc779d1ce"

# (fila, campo en el resumen, operador, umbral, referencia de v1 2026-10-12)
CRITERIOS = (
    ("suficiente: se abstiene", "escenarios", "suficiente_se_abstiene", "<=", 6, 4),
    ("suficiente: cita el articulo que responde", "escenarios", "suficiente_cita_el_oraculo", ">=", 39, 41),
    ("parcial: dice que falta", "escenarios", "parcial_dice_que_falta", ">=", 11, 11),
    ("irrelevante: se abstiene", "escenarios", "irrelevante_se_abstiene", ">=", 25, 19),
    ("irrelevante: cita sin respaldo", "escenarios", "irrelevante_cita_sin_respaldo", "<=", 0, 1),
    ("gold con RAG real: abstencion pura", "gold", "abstencion_pura", "<=", 10, 10),
)

# Cuanto puede separarse el control (v1 medido hoy) de su referencia antes de
# sospechar que el entorno cambio. Es un aviso, no una condicion: la deriva
# numerica existe (control de reproduccion de la fase B: 3 de 10 identicas).
TOLERANCIA_CONTROL = 3


def _resumen(directorio) -> dict:
    """El resumen.json de una medicion. Acepta el directorio de la corrida o el
    padre si tiene una sola corrida dentro (asi escriben las dos herramientas)."""
    d = Path(directorio)
    if (d / "resumen.json").exists():
        return json.loads((d / "resumen.json").read_text(encoding="utf-8"))
    hijos = [h for h in d.iterdir() if (h / "resumen.json").exists()] if d.is_dir() else []
    if len(hijos) != 1:
        raise SystemExit(f"{d}: se esperaba un resumen.json (o una sola corrida dentro), hay {len(hijos)}")
    return json.loads((hijos[0] / "resumen.json").read_text(encoding="utf-8"))


def _numero(valor) -> int:
    """'22/55' -> 22; 1 -> 1."""
    return int(str(valor).split("/")[0])


def _cumple(valor: int, op: str, umbral: int) -> bool:
    return valor <= umbral if op == "<=" else valor >= umbral


def problemas_de_identidad(esc: dict, gold: dict, revision_corrida: dict | None = None) -> list[str]:
    """Lo que haria que la medicion no fuera la del protocolo."""
    p = []
    if esc.get("huella_escenarios") != HUELLA_ESCENARIOS:
        p.append(f"escenarios {esc.get('huella_escenarios')} y no el archivo congelado {HUELLA_ESCENARIOS}")
    if esc.get("huella_adaptador") != gold.get("huella_adaptador"):
        p.append(f"adaptadores distintos: escenarios {esc.get('huella_adaptador')}, "
                 f"gold {gold.get('huella_adaptador')}")
    rev = gold.get("revision_base")
    if rev is not None and rev != config.BASE_MODEL_REVISION:
        p.append(f"gold con la revision {rev}, no {config.BASE_MODEL_REVISION}")
    if revision_corrida is not None and revision_corrida != config.BASE_MODEL_REVISION:
        p.append(f"escenarios con la revision {revision_corrida}, no {config.BASE_MODEL_REVISION}")
    return p


def juzgar(esc: dict, gold: dict) -> dict:
    fuentes = {"escenarios": esc, "gold": gold}
    filas = []
    for nombre, fuente, campo, op, umbral, ref in CRITERIOS:
        valor = _numero(fuentes[fuente][campo])
        filas.append({"fila": nombre, "valor": fuentes[fuente][campo], "umbral": f"{op} {umbral}",
                      "v1_ref": ref, "cumple": _cumple(valor, op, umbral)})
    return {"pasa": all(f["cumple"] for f in filas), "filas": filas}


def comparar_control(esc: dict, gold: dict) -> list[str]:
    """Avisos si v1 medido hoy se separa de su referencia mas de la tolerancia."""
    fuentes = {"escenarios": esc, "gold": gold}
    avisos = []
    for nombre, fuente, campo, _, _, ref in CRITERIOS:
        hoy = _numero(fuentes[fuente][campo])
        if abs(hoy - ref) > TOLERANCIA_CONTROL:
            avisos.append(f"control v1, {nombre}: {hoy} hoy frente a {ref} el 2026-10-12")
    if esc.get("huella_adaptador") != "8ce3cc2bc9306974":
        avisos.append(f"el control no es v1: adaptador {esc.get('huella_adaptador')}")
    return avisos


def _revision_de(directorio) -> str | None:
    d = Path(directorio)
    for c in [d / "corrida.json", *[h / "corrida.json" for h in d.iterdir() if h.is_dir()]] if d.is_dir() else []:
        if c.exists():
            return json.loads(c.read_text(encoding="utf-8")).get("revision_base")
    return None


def informe(dir_esc, dir_gold, ctrl_esc=None, ctrl_gold=None) -> dict:
    esc, gold = _resumen(dir_esc), _resumen(dir_gold)
    problemas = problemas_de_identidad(esc, gold, _revision_de(dir_esc))
    salida = {"problemas": problemas, **juzgar(esc, gold), "avisos_control": []}
    if ctrl_esc and ctrl_gold:
        c_esc, c_gold = _resumen(ctrl_esc), _resumen(ctrl_gold)
        salida["avisos_control"] = comparar_control(c_esc, c_gold)
        bg, bc = gold.get("buscador"), c_gold.get("buscador")
        if bg != bc:
            problemas.append(f"buscador distinto entre candidato y control: {bg} frente a {bc}")
    if problemas:
        salida["pasa"] = False
    return salida


def imprimir(r: dict) -> None:
    print(f"{'fila':44}{'valor':>8}{'umbral':>9}{'v1':>6}  ")
    for f in r["filas"]:
        print(f"{f['fila']:44}{str(f['valor']):>8}{f['umbral']:>9}{f['v1_ref']:>6}  "
              f"{'cumple' if f['cumple'] else 'NO CUMPLE'}")
    for p in r["problemas"]:
        print(f"MEDICION NO VALIDA: {p}")
    for a in r["avisos_control"]:
        print(f"AVISO: {a}")
    print()
    if r["problemas"]:
        print("NO SE JUZGA: la medicion no es la que fija el protocolo.")
    elif r["pasa"]:
        print("PASA la prueba barata. Autoriza la evaluacion completa (fases C y D), no la aceptacion.")
    else:
        print("NO PASA la prueba barata. Se descarta sin evaluacion completa; anotar por que.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--escenarios", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--control-escenarios")
    ap.add_argument("--control-gold")
    a = ap.parse_args(argv)
    r = informe(a.escenarios, a.gold, a.control_escenarios, a.control_gold)
    imprimir(r)
    return 0 if r["pasa"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
