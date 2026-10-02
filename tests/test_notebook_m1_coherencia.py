"""El notebook de M1 lleva copiado el catalogo de rutas legales; este test lo ancla.

El notebook corre en Colab, donde no puede importar `tools/`, asi que el catalogo
de `tools.dataset_quality.MECANISMOS` va embebido en sus celdas. Esa copia ya se
desincronizo una vez con consecuencias reales: la version del notebook estaba
recortada (le faltaban "Secretaria de Transito", "apelar", SIMIT, Colpensiones...)
y marcaba como "no nombra ruta legal" respuestas que si la nombraban, subestimando
al modelo en la comparacion baseline vs. afinado.

El fallo era silencioso -- el notebook corria sin errores y producia una cifra
creible pero equivocada -- asi que se vigila con una prueba en vez de con
disciplina al editar.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tools.dataset_quality import MECANISMOS

NOTEBOOK = Path(__file__).resolve().parents[1] / "colab" / "m1_finetune.ipynb"


def _celdas_con_catalogo() -> list[str]:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return [
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code" and "MECANISMO = re.compile(" in "".join(c["source"])
    ]


def _patron_embebido(fuente: str) -> str:
    m = re.search(r'MECANISMO = re\.compile\(\s*r"""(.*?)"""', fuente, re.S)
    assert m, "no se pudo extraer el patron MECANISMO de la celda"
    return m.group(1)


def test_el_notebook_lleva_el_catalogo_embebido():
    assert _celdas_con_catalogo(), (
        "ninguna celda del notebook define MECANISMO: si se renombro, actualiza este test"
    )


@pytest.mark.parametrize("fuente", _celdas_con_catalogo())
def test_el_catalogo_del_notebook_no_se_desincroniza_del_repo(fuente):
    esperado = "|".join(sorted(set(MECANISMOS.values())))
    assert _patron_embebido(fuente) == esperado, (
        "El catalogo embebido en el notebook ya no coincide con "
        "tools.dataset_quality.MECANISMOS. Regeneralo desde el catalogo en vez de "
        "editarlo a mano, o la medicion del notebook dejara de ser comparable."
    )


@pytest.mark.parametrize("fuente", _celdas_con_catalogo())
def test_el_patron_del_notebook_compila_y_reconoce_rutas_reales(fuente):
    patron = re.compile(_patron_embebido(fuente), re.I)
    # Casos que la version recortada fallaba, por los que existe este test.
    for texto in ("puedes apelar la sancion ante la Secretaria de Transito",
                  "consulta tus comparendos en el SIMIT",
                  "reclama ante Colpensiones"):
        assert patron.search(texto), f"el patron no reconoce una ruta real: {texto!r}"
    # Consejo generico sin destino: no debe contar como ruta.
    for texto in ("revisa el contrato con calma", "reune toda la evidencia disponible"):
        assert not patron.search(texto), f"el patron cuenta como ruta un consejo generico: {texto!r}"
