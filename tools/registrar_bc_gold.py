"""Registra en el CSV del gold las 125 filas de clase B y C, en una pasada.

## Donde esta el hueco, exactamente

El dictamen de clases B y C (`docs/m3_articulos_gold_dictamen_claseBC.md`) esta
aprobado y da los totales **por clase**:

    B (82)   64 responde   15 responde_parcial   3 no_responde
    C (46)   38 responde    8 responde_parcial   0 no_responde

Las 3 `no_responde` **ya estan registradas** (9033 Ley 361 art. 26, 9060 C.P.
art. 286, 9004 D. 2591 art. 1), porque el dictamen las nombro una por una.
Quedan **125 filas**: 102 `responde` y 23 `responde_parcial`.

**El dictamen nombra 9 de esas 23**, como ejemplos del patron "el articulo da el
derecho o la via, pero no las dos":

    9004  CPACA 13, 14          terminos del derecho de peticion, no el derecho a la cita
    9010  CGP 90                admision de la demanda
    9010  Ley 2220 67, 68, 70, 71   requisito de procedibilidad
    9036  CST 159, 160          definen el trabajo suplementario; el 168 pone las tasas

**Faltan 14.** No se pueden deducir: poner `responde` en todo lo no nombrado
daria 116 `responde` contra las 102 que el dictamen aprobo, y elegir 14 filas
para completar el cupo seria inventar el veredicto de cada una. Es lo que dice
`tools/pendientes_bc.py` y sigue siendo cierto.

## Que hace este modulo

    --propuesta   escribe docs/m3_articulos_gold_bc_para_marcar.md: las 125
                  filas con `responde` propuesto y las 9 nombradas ya marcadas
                  como `responde_parcial`. Solo hay que marcar 14 casillas.
    --registrar   lee ese archivo ya marcado y escribe el CSV. Comprueba que los
                  totales cuadren con el dictamen aprobado ANTES de escribir: si
                  no cuadran, no escribe.

Sin `--escribir`, `--registrar` simula.

    python -m tools.registrar_bc_gold --propuesta
    python -m tools.registrar_bc_gold --registrar
    python -m tools.registrar_bc_gold --registrar --escribir
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter

from tools.validacion_articulos_gold import SALIDA

RAIZ = SALIDA.parent
PARA_MARCAR = RAIZ / "m3_articulos_gold_bc_para_marcar.md"

# Totales que el dictamen aprobado fija por clase. El registro no puede
# desviarse de esto: si se desvia, o el marcado esta mal o el dictamen cambio,
# y en los dos casos hay que parar y mirarlo.
TOTALES = {
    "B_caso_fallido": {"responde": 64, "responde_parcial": 15, "no_responde": 3},
    "C_redundante": {"responde": 38, "responde_parcial": 8, "no_responde": 0},
}

# Las 9 filas que el dictamen nombro como `responde_parcial`.
PARCIALES_NOMBRADAS = {
    ("9004", "cpaca_ley_1437_2011", "13"),
    ("9004", "cpaca_ley_1437_2011", "14"),
    ("9010", "codigo_general_proceso_ley_1564_2012", "90"),
    ("9010", "conciliacion_ley_2220_2022", "67"),
    ("9010", "conciliacion_ley_2220_2022", "68"),
    ("9010", "conciliacion_ley_2220_2022", "70"),
    ("9010", "conciliacion_ley_2220_2022", "71"),
    ("9036", "codigo_sustantivo_trabajo_decreto_2663_1950", "159"),
    ("9036", "codigo_sustantivo_trabajo_decreto_2663_1950", "160"),
}

JUSTIFICACION = {
    "responde": ("Clase {clase} del dictamen aprobado el 2026-10-10: el articulo "
                 "responde la consulta. El caso no acerto por un fallo de "
                 "recuperacion, no de etiquetado."),
    "responde_parcial": ("Clase {clase} del dictamen aprobado el 2026-10-10: el "
                         "articulo da el derecho o la via, no las dos. El gold "
                         "etiqueta las dos piezas por separado y basta traer una."),
}
REVISOR = ("dictamen de clases B y C redactado por Claude y aprobado el 2026-10-10 "
           "por Leonardo Galeano (abogado). Veredicto por fila marcado sobre "
           "docs/m3_articulos_gold_bc_para_marcar.md")
FECHA = "2026-10-10"
EDITABLES = {"veredicto", "confianza", "justificacion", "revisor", "fecha_revision"}

_LINEA = re.compile(r"^\|\s*(\d+)\s*\|\s*([\w.\-]+)\s*\|\s*([\w\-]+)\s*\|"
                    r"\s*(responde|responde_parcial|no_responde|pendiente)\s*\|")


def filas_pendientes() -> list[dict]:
    rows = list(csv.DictReader(SALIDA.open(encoding="utf-8", newline="")))
    return [r for r in rows if r["veredicto"] == "pendiente"]


def propuesta() -> str:
    filas = filas_pendientes()
    partes = [
        "# Clases B y C: marcar el veredicto de cada fila",
        "",
        "El dictamen esta **aprobado**. Lo que falta es por fila, y son **14",
        "casillas**: el dictamen nombro 9 de las 23 `responde_parcial` y las demas",
        "no quedaron registradas una por una.",
        "",
        "Ya viene propuesto `responde` en todas y `responde_parcial` en las 9",
        "nombradas. **Cambia a `responde_parcial` las 14 que falten** y guarda.",
        "",
        "Cupo que tiene que cuadrar al terminar:",
        "",
        "| clase | responde | responde_parcial | no_responde |",
        "|---|---|---|---|",
        "| B (82) | 64 | 15 | 3 ya registradas |",
        "| C (46) | 38 | 8 | 0 |",
        "",
        "`responde_parcial` = el articulo da **el derecho o la via, no las dos**.",
        "",
        "| caso | norma | art. | veredicto | pregunta |",
        "|---|---|---|---|---|",
    ]
    for f in sorted(filas, key=lambda r: (r["case_id"], r["doc_id"], r["articulo"])):
        clave = (f["case_id"], f["doc_id"], f["articulo"])
        v = "responde_parcial" if clave in PARCIALES_NOMBRADAS else "responde"
        partes.append(f"| {f['case_id']} | {f['doc_id']} | {f['articulo']} | {v} | "
                      f"{(f.get('pregunta') or '')[:70]} |")
    marcadas = sum(1 for f in filas
                   if (f["case_id"], f["doc_id"], f["articulo"]) in PARCIALES_NOMBRADAS)
    por_clase = Counter(f["clase_impacto"] for f in filas
                        if (f["case_id"], f["doc_id"], f["articulo"]) in PARCIALES_NOMBRADAS)
    faltan = {c: TOTALES[c]["responde_parcial"] - por_clase[c] for c in TOTALES}
    partes += ["", f"Filas: {len(filas)}. Ya marcadas como parcial: {marcadas}.",
               f"**Faltan {sum(faltan.values())} por marcar**: "
               f"{faltan[chr(66)+chr(95)+chr(99)+chr(97)+chr(115)+chr(111)+chr(95)+chr(102)+chr(97)+chr(108)+chr(108)+chr(105)+chr(100)+chr(111)]} de clase B "
               f"y {faltan[chr(67)+chr(95)+chr(114)+chr(101)+chr(100)+chr(117)+chr(110)+chr(100)+chr(97)+chr(110)+chr(116)+chr(101)]} de clase C.", ""]
    return "\n".join(partes)


def leer_marcado() -> dict:
    """{(caso, doc, art): veredicto} del archivo marcado."""
    if not PARA_MARCAR.exists():
        raise SystemExit(f"no existe {PARA_MARCAR.name}: corre primero --propuesta")
    salida = {}
    for linea in PARA_MARCAR.read_text(encoding="utf-8").splitlines():
        m = _LINEA.match(linea)
        if m:
            salida[(m.group(1), m.group(2), m.group(3))] = m.group(4)
    return salida


def verificar(marcado: dict, filas: list[dict]) -> list[str]:
    """Lo que tiene que cumplirse antes de escribir. Vacio = se puede."""
    problemas = []
    claves = {(f["case_id"], f["doc_id"], f["articulo"]) for f in filas}
    faltan = claves - set(marcado)
    if faltan:
        problemas.append(f"{len(faltan)} filas sin marcar: {sorted(faltan)[:5]}")
    sobran = set(marcado) - claves
    if sobran:
        problemas.append(f"{len(sobran)} filas marcadas que no estan pendientes: "
                         f"{sorted(sobran)[:5]}")
    if "pendiente" in marcado.values():
        n = sum(1 for v in marcado.values() if v == "pendiente")
        problemas.append(f"{n} filas siguen en 'pendiente'")

    # El cupo del dictamen. Se suman las 3 no_responde ya registradas.
    por_clase = {f["case_id"] + f["doc_id"] + f["articulo"]: f["clase_impacto"] for f in filas}
    cuenta: dict = {c: Counter() for c in TOTALES}
    for (caso, doc, art), v in marcado.items():
        clase = por_clase.get(caso + doc + art)
        if clase in cuenta:
            cuenta[clase][v] += 1
    for clase, esperado in TOTALES.items():
        for veredicto, n in esperado.items():
            if veredicto == "no_responde":
                continue           # ya registradas, no estan entre las pendientes
            visto = cuenta[clase][veredicto]
            if visto != n:
                problemas.append(f"{clase}: {veredicto} marcadas {visto}, "
                                 f"el dictamen aprobo {n}")
    return problemas


def registrar(marcado: dict, escribir: bool) -> int:
    rows = list(csv.DictReader(SALIDA.open(encoding="utf-8", newline="")))
    campos = list(rows[0].keys())
    filas = [r for r in rows if r["veredicto"] == "pendiente"]

    problemas = verificar(marcado, filas)
    if problemas:
        print("NO se registra. Hay que resolver esto primero:")
        for p in problemas:
            print(f"  - {p}")
        return 1

    cambios = 0
    for r in rows:
        clave = (r["case_id"], r["doc_id"], r["articulo"])
        if r["veredicto"] != "pendiente" or clave not in marcado:
            continue
        v = marcado[clave]
        antes = {k: r[k] for k in r}
        r["veredicto"] = v
        r["confianza"] = "media" if v == "responde_parcial" else "alta"
        r["justificacion"] = JUSTIFICACION[v].format(
            clase="B" if r["clase_impacto"] == "B_caso_fallido" else "C")
        r["revisor"] = REVISOR
        r["fecha_revision"] = FECHA
        # Ninguna columna fuera de EDITABLES se toca: el instrumento no se altera.
        tocadas = {k for k in r if r[k] != antes[k]}
        if tocadas - EDITABLES:
            raise SystemExit(f"se iba a tocar una columna no editable: {tocadas - EDITABLES}")
        cambios += 1

    print(f"{cambios} filas a registrar  {dict(Counter(marcado.values()))}")
    if not escribir:
        print("SIMULACION. Con --escribir se guarda.")
        return 0
    with SALIDA.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"Escrito {SALIDA.name}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--propuesta", action="store_true")
    p.add_argument("--registrar", action="store_true")
    p.add_argument("--escribir", action="store_true")
    args = p.parse_args(argv)

    if args.propuesta:
        PARA_MARCAR.write_text(propuesta(), encoding="utf-8", newline="\n")
        print(f"Escrito {PARA_MARCAR}")
        fs = filas_pendientes()
        marcadas = sum(1 for f in fs if (f["case_id"], f["doc_id"], f["articulo"])
                       in PARCIALES_NOMBRADAS)
        total_parcial = sum(t["responde_parcial"] for t in TOTALES.values())
        print(f"  {len(fs)} filas, {marcadas} ya marcadas como parcial, "
              f"faltan {total_parcial - marcadas} por marcar.")
        return 0
    if args.registrar:
        return registrar(leer_marcado(), args.escribir)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
