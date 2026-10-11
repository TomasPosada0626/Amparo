"""Preparacion de la reevaluacion de v1 (tools/evaluation/reevaluacion_v1.py).

Solo la parte de CPU: que registros, con que prompt, contra que adaptador y con
que regla se decide si es reproduccion o diagnostico. Cargar el modelo y generar
corre en Colab y no se prueba aqui.

La propiedad que importa: **la reevaluacion cambia UNA variable**, el system
prompt con que se genera. El contexto, la pregunta y el adaptador tienen que ser
los de la corrida del 2026-10-09; si no, no se sabe que explico la diferencia.
"""
from __future__ import annotations

import csv
import subprocess

import pytest

from tools.evaluation import config
from tools.evaluation import reevaluacion_v1 as R
from tools.evaluation.dataset import prompt_de

ORDEN = "Si el CONTEXTO no contiene informacion suficiente"
ADAPTADOR_V1 = config.PROJECT_ROOT / "artifacts" / "amparo-lora-adapter"
ADAPTADOR_V2 = config.PROJECT_ROOT / "artifacts" / "amparo-lora-adapter-v2"

pytestmark = pytest.mark.skipif(not R.RESULTADOS_V1.exists(),
                                reason="sin los resultados historicos de v1")


@pytest.fixture(scope="module")
def filas():
    return R.fuente()


class TestQueSeRegenera:
    def test_los_103_con_contexto(self, filas):
        sel = R.seleccionar(filas, "contexto")
        assert len(sel) == 103
        assert {r["modo"] for r in sel} == {"B1", "B2", "B3"}

    def test_los_35_b2(self, filas):
        assert len(R.seleccionar(filas, "b2")) == 35

    def test_los_35_b2_son_los_adjudicados(self, filas):
        """Las adjudicaciones de contexto siguen valiendo solo si los casos son
        los mismos."""
        ruta = config.PROJECT_ROOT / "docs" / "m1_b2_adjudicacion.csv"
        adjudicados = {r["case_id"] for r in csv.DictReader(
            ruta.open(encoding="utf-8", newline=""))}
        assert {str(r["id"]) for r in R.seleccionar(filas, "b2")} == adjudicados

    def test_todos_reciben_la_orden_de_abstenerse(self, filas):
        """**La variable que se mide.** En la corrida historica se generaron sin
        ella; aqui cada uno recibe su propio prompt, que la trae."""
        for r in R.seleccionar(filas, "contexto"):
            assert ORDEN in prompt_de(r)[0]["content"], r["id"]

    def test_el_contexto_es_exactamente_el_de_la_corrida_historica(self, filas):
        """**Lo que se mantiene fijo.** El contexto que se le da a v1 tiene que
        ser el que vio el 2026-10-09, comparado con la base 9c9f5a9. Si viniera
        del dataset actual cambiaria tambien el contexto de los 35 B2, que v3
        reconstruyo."""
        r = subprocess.run(["git", "show", "9c9f5a9:data/dataset.jsonl"],
                           cwd=config.PROJECT_ROOT, capture_output=True)
        if r.returncode != 0:
            pytest.skip("sin git")
        import json

        base = {x["id"]: x for x in (json.loads(l) for l in
                r.stdout.decode("utf-8").splitlines() if l.strip())}
        for f in R.seleccionar(filas, "contexto"):
            assert prompt_de(f)[1] == base[f["id"]]["messages"][1], f["id"]

    def test_un_alcance_desconocido_no_pasa(self, filas):
        with pytest.raises(SystemExit):
            R.seleccionar(filas, "todo")


class TestControlDeReproduccion:
    def test_son_registros_sin_contexto_con_respuesta_historica(self, filas):
        ctl = R.seleccionar_control(filas, 10)
        assert len(ctl) == 10
        for r in ctl:
            assert r.get("modo") is None
            assert r.get("generated"), "sin respuesta historica no hay contra que comparar"
            # para estos el prompt de v1 ya era el correcto
            assert ORDEN not in prompt_de(r)[0]["content"]

    def test_es_determinista(self, filas):
        assert ([r["id"] for r in R.seleccionar_control(filas, 10)]
                == [r["id"] for r in R.seleccionar_control(list(reversed(filas)), 10)])

    @pytest.mark.parametrize("coincidencias,esperado", [
        ([True] * 10, "REPRODUCCION"),
        ([True] * 9 + [False], "DIAGNOSTICO"),
        ([False] * 10, "DIAGNOSTICO"),
        ([], "SIN_CONTROL"),
    ])
    def test_la_regla_esta_fijada_antes_de_correr(self, coincidencias, esperado):
        """Exacto o nada. Con greedy, el mismo stack da la misma cadena: una sola
        diferencia ya dice que algo cambio."""
        assert R.clasificar([{"coincide": c} for c in coincidencias]) == esperado


class TestAdaptadorYRevision:
    @pytest.mark.skipif(not ADAPTADOR_V1.exists(), reason="sin el adaptador v1 local")
    def test_acepta_v1(self):
        assert R.verificar_adaptador(ADAPTADOR_V1) == R.HUELLA_ADAPTADOR_V1

    @pytest.mark.skipif(not ADAPTADOR_V2.exists(), reason="sin el adaptador v2 local")
    def test_rechaza_otro_adaptador(self):
        """Si se cargara v2 por error, la cifra se atribuiria a v1."""
        with pytest.raises(SystemExit, match="no se genera nada"):
            R.verificar_adaptador(ADAPTADOR_V2)

    def test_la_revision_por_defecto_es_la_recuperada_de_v1(self):
        """El ultimo commit a main del repo de Qwen es del 2025-01-12 y v1 se
        entreno el 2026-10-09: era ese. Si alguien la cambia, que se note."""
        assert R.REVISION_V1 == "a09a35458c702b33eeacc393d103063234e8bc28"

    @pytest.mark.skipif(not ADAPTADOR_V1.exists(), reason="sin el adaptador v1 local")
    def test_otra_revision_queda_marcada(self):
        p = R.plan(ADAPTADOR_V1, revision="otra")
        assert p["revision_es_la_de_v1"] is False

    @pytest.mark.skipif(not ADAPTADOR_V1.exists(), reason="sin el adaptador v1 local")
    def test_el_plan_no_carga_ningun_modelo(self):
        """--dry-run tiene que poder correr en CPU sin transformers pesados."""
        p = R.plan(ADAPTADOR_V1)
        assert p["n_objetivo"] == 103 and p["n_control"] == 10
        assert len(p["prompts_objetivo"]) == 1 and len(p["prompts_control"]) == 1
        assert p["prompts_objetivo"] != p["prompts_control"]
