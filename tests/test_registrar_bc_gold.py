"""Registro de las filas B y C del gold (tools/registrar_bc_gold.py)."""
from __future__ import annotations

import csv
from collections import Counter

from tools import registrar_bc_gold as R
from tools.validacion_articulos_gold import SALIDA


def _filas():
    with SALIDA.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_las_parciales_nombradas_existen_en_el_gold():
    """Una clave mal escrita no falla: simplemente no marca la fila. Paso con
    los cuatro articulos de la Ley 2220 de 9010 (`conciliacion_...` en vez de
    `estatuto_conciliacion_...`), y la planilla pedia 18 casillas en vez de 14."""
    claves = {(f["case_id"], f["doc_id"], f["articulo"]) for f in _filas()}
    faltan = sorted(R.PARCIALES_NOMBRADAS - claves)
    assert not faltan, f"parciales nombradas que no estan en el gold: {faltan}"


def test_las_parciales_nombradas_son_de_las_clases_b_y_c_pendientes():
    clase = {(f["case_id"], f["doc_id"], f["articulo"]): (f["clase_impacto"], f["veredicto"])
             for f in _filas()}
    for k in R.PARCIALES_NOMBRADAS:
        c, v = clase[k]
        assert c in R.TOTALES, (k, c)
        assert v == "pendiente", (k, v)


def test_el_cupo_que_falta_marcar_es_14():
    """Con las 9 nombradas marcadas, faltan 8 de B y 6 de C."""
    clase = {(f["case_id"], f["doc_id"], f["articulo"]): f["clase_impacto"] for f in _filas()}
    marcadas = Counter(clase[k] for k in R.PARCIALES_NOMBRADAS)
    faltan = {c: R.TOTALES[c]["responde_parcial"] - marcadas[c] for c in R.TOTALES}
    assert faltan == {"B_caso_fallido": 8, "C_redundante": 6}
