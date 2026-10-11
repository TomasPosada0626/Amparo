"""Prompt de evaluacion y dev de eleccion de epoca (tools/evaluation/dataset.py).

Los dos fallos que cierran estas pruebas se encontraron en la auditoria previa al
entrenamiento candidato (docs/m1_auditoria_preentrenamiento.md):

1. `evaluate()` generaba las 334 respuestas con el system prompt de `records[0]`,
   el de sin contexto. Los 103 registros con contexto -- los 35 B2 entre ellos --
   se evaluaron sin la orden de abstenerse con la que se entrenaron.
2. El dev que elige la epoca compartia el 63 % de sus preguntas con fit.

Se prueban sobre el dataset real, no sobre registros armados a mano: el fallo 1
solo existe porque el dataset real tiene dos prompts.
"""
from __future__ import annotations

import json
from collections import Counter

import pytest

from tools.evaluation import config
from tools.evaluation import dataset as D

ORDEN_DE_ABSTENERSE = "Si el CONTEXTO no contiene informacion suficiente"


@pytest.fixture(scope="module")
def registros() -> list[dict]:
    if not config.DATASET_PATH.exists():
        pytest.skip("sin dataset")
    return [json.loads(l) for l in
            config.DATASET_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]


@pytest.fixture(scope="module")
def val(registros):
    return [r for r in registros if r["split"] == "val"]


@pytest.fixture(scope="module")
def train(registros):
    return [r for r in registros if r["split"] == "train"]


# --- 1. El prompt con que se genera ------------------------------------------

class TestPromptDeEvaluacion:
    def test_los_b2_de_validacion_se_generan_con_la_orden_de_abstenerse(self, val):
        """**La prueba central.** Son los 35 que miden la abstencion. Con el
        prompt de records[0] no recibian la orden; con prompt_de si."""
        b2 = [r for r in val if r.get("modo") == "B2"]
        assert len(b2) == 35
        for r in b2:
            assert ORDEN_DE_ABSTENERSE in D.prompt_de(r)[0]["content"], r["id"]

    def test_todos_los_de_contexto_reciben_el_prompt_de_contexto(self, val):
        con = [r for r in val if r.get("modo") is not None]
        assert Counter(r["modo"] for r in con) == {"B1": 55, "B2": 35, "B3": 13}
        for r in con:
            assert ORDEN_DE_ABSTENERSE in D.prompt_de(r)[0]["content"]

    def test_los_sin_contexto_reciben_el_prompt_sin_contexto(self, val):
        """El otro lado: un registro sin contexto no puede recibir reglas sobre
        un CONTEXTO que no tiene."""
        sin = [r for r in val if r.get("modo") is None]
        assert len(sin) == 231
        for r in sin:
            assert ORDEN_DE_ABSTENERSE not in D.prompt_de(r)[0]["content"]

    def test_el_prompt_de_evaluacion_es_el_de_entrenamiento(self, val):
        """Entrenar y evaluar con el mismo prompt, registro por registro. El
        entrenamiento usa messages[:2]; la evaluacion tiene que usar eso."""
        for r in val:
            assert D.prompt_de(r) == r["messages"][:2]

    def test_el_prompt_de_records_0_NO_sirve_para_los_de_contexto(self, registros, val):
        """Documenta el fallo: lo que hacia el notebook antes. Si esto empezara
        a pasar, el dataset dejo de tener dos prompts y conviene saberlo."""
        el_de_records_0 = registros[0]["messages"][0]["content"]
        b2 = next(r for r in val if r.get("modo") == "B2")
        assert el_de_records_0 != D.prompt_de(b2)[0]["content"]
        assert ORDEN_DE_ABSTENERSE not in el_de_records_0

    def test_las_dos_huellas_de_prompt_son_distintas(self, val):
        """La huella se guarda en cada respuesta: permite comprobar despues con
        que prompt se genero, que es lo que las corridas viejas no permitian."""
        huellas = {r.get("modo") is None: D.huella_prompt(r) for r in val}
        assert len(set(huellas.values())) == 2

    def test_system_prompt_falla_con_prompts_mezclados(self, val):
        """Devolver el primero en silencio fue la trampa. Ahora se niega."""
        with pytest.raises(ValueError, match="system prompts distintos"):
            D.system_prompt(val)

    def test_system_prompt_sigue_sirviendo_con_un_solo_prompt(self, val):
        """M2 lo llama con los registros sin contexto, que tienen uno."""
        sin = [r for r in val if r.get("modo") is None]
        assert D.system_prompt(sin) == sin[0]["messages"][0]["content"]

    def test_un_registro_mal_formado_no_pasa_en_silencio(self):
        with pytest.raises(ValueError):
            D.prompt_de({"id": 1, "messages": [{"role": "user", "content": "x"}]})


# --- 2. El dev que elige la epoca --------------------------------------------

class TestSplitDev:
    def test_ningun_grupo_de_pregunta_queda_a_los_dos_lados(self, train):
        """**La prueba central.** Antes: 113 de 179 ejemplos de dev tenian su
        pregunta exacta en fit, y 51 pares contrastivos quedaban partidos."""
        fit, dev = D.split_dev(train)
        grupo = D.grupos_de_pregunta(train)
        g_fit = {grupo[r["id"]] for r in fit}
        g_dev = {grupo[r["id"]] for r in dev}
        assert not (g_fit & g_dev)

    def test_ninguna_pregunta_normalizada_queda_a_los_dos_lados(self, train):
        fit, dev = D.split_dev(train)
        q_fit = {D._pregunta_normalizada(r) for r in fit}
        assert not [r["id"] for r in dev if D._pregunta_normalizada(r) in q_fit]

    def test_ningun_par_contrastivo_ni_base_queda_partido(self, train):
        fit, dev = D.split_dev(train)
        lado = {r["id"]: "fit" for r in fit} | {r["id"]: "dev" for r in dev}
        for r in train:
            for campo in ("par_de", "base_id"):
                otro = r.get(campo)
                if otro in lado:
                    assert lado[r["id"]] == lado[otro], (r["id"], campo, otro)

    def test_la_validacion_no_se_toca(self, train, val):
        """split_dev solo recibe entrenamiento. Los 334 siguen fuera."""
        fit, dev = D.split_dev(train)
        ids_val = {r["id"] for r in val}
        assert not ids_val & {r["id"] for r in fit + dev}
        assert len(val) == 334

    def test_fit_y_dev_reparten_todo_el_entrenamiento(self, train):
        fit, dev = D.split_dev(train)
        assert len(fit) + len(dev) == len(train)
        assert {r["id"] for r in fit} | {r["id"] for r in dev} == {r["id"] for r in train}

    def test_el_tamano_ronda_la_fraccion_pedida(self, train):
        """Se reparten grupos enteros, asi que no es exacto: se exige estar
        cerca, no igual."""
        _, dev = D.split_dev(train, 0.08)
        assert 0.06 <= len(dev) / len(train) <= 0.11

    def test_es_determinista_y_no_depende_del_orden(self, train):
        a = D.split_dev(train, seed=42)
        b = D.split_dev(list(reversed(train)), seed=42)
        assert [r["id"] for r in a[1]] == [r["id"] for r in b[1]]

    def test_el_dev_trae_los_cuatro_modos(self, train):
        """Si el dev perdiera los B2, elegiria la epoca sin mirar la abstencion."""
        _, dev = D.split_dev(train)
        assert {r.get("modo") for r in dev} >= {None, "B1", "B2", "B3"}

    def test_grupos_une_por_pregunta_base_y_par(self):
        regs = [
            {"id": 1, "category": "A", "messages": [{}, {"content": "Me echaron del trabajo"}]},
            {"id": 2001, "category": "A", "base_id": 1, "pregunta": "otra forma de decirlo",
             "messages": [{}, {"content": "x"}]},
            {"id": 6001, "category": "A", "par_de": 2001, "pregunta": "otra forma de decirlo",
             "messages": [{}, {"content": "x"}]},
            {"id": 7, "category": "A", "messages": [{}, {"content": "me echaron del trabajo!"}]},
            {"id": 9, "category": "A", "messages": [{}, {"content": "Algo sin relacion"}]},
        ]
        g = D.grupos_de_pregunta(regs)
        assert g[1] == g[2001] == g[6001] == g[7]
        assert g[9] != g[1]
