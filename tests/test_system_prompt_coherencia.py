"""El SYSTEM_PROMPT de M1 es el contrato que une los tres milestones.

El modelo de M1 se fine-tuneo con un system prompt exacto; M2 lo reusa para
generar las respuestas que evalua y M3 lo usa como primera parte del prompt
aumentado (prompt_template.SYSTEM_PROMPT_M1). Si alguna copia se edita sin las
otras, las cifras de los tres milestones dejan de ser comparables y nada falla
de forma visible: el modelo simplemente responde con un rol distinto del que
se entreno.

Hoy el texto vive duplicado en dos modulos (decision existente, con un
comentario que pide sincronizarlos a mano). Este test convierte ese "acuerdense
de sincronizarlo" en una verificacion automatica, anclada a la unica fuente de
verdad real: lo que quedo escrito en el dataset con el que se entreno.
"""
from __future__ import annotations

import json

from tools.evaluation import dataset as _dataset
from tools.evaluation import config as eval_config
from tools.model_comparator import config as mc_config
from tools.rag import prompt_template


def _system_prompt_del_dataset() -> str:
    """El system prompt tal como quedo en data/dataset_legal.jsonl."""
    return _dataset.load_records()[0]["messages"][0]["content"]


def test_el_prompt_del_comparador_es_el_que_se_entreno():
    assert mc_config.SYSTEM_PROMPT == _system_prompt_del_dataset()


def test_el_prompt_del_rag_es_el_que_se_entreno():
    # Si esto falla, el RAG de M3 esta generando con un rol distinto del que
    # aprendio el adaptador de M1: el delta deja de ser atribuible al RAG.
    assert prompt_template.SYSTEM_PROMPT_M1 == _system_prompt_del_dataset()


def test_todo_el_dataset_usa_el_mismo_system_prompt():
    # Un prompt para los ejemplos sin contexto y otro para los que lo llevan.
    # Son dos a proposito: el segundo agrega las reglas de uso del CONTEXTO. Lo
    # que no puede pasar es que haya mas de uno DENTRO de cada grupo, porque
    # entonces el modelo recibiria instrucciones distintas para la misma tarea.
    sin_contexto = {r["messages"][0]["content"] for r in _dataset.load_records()}
    assert len(sin_contexto) == 1, (
        f"los ejemplos sin contexto mezclan {len(sin_contexto)} system prompts")

    con_contexto = {r["messages"][0]["content"] for r in _dataset.load_records_v2()}
    assert len(con_contexto) == 1, (
        f"los ejemplos con contexto mezclan {len(con_contexto)} system prompts")
    assert sin_contexto != con_contexto, (
        "el prompt con contexto deberia agregar las reglas de uso del CONTEXTO")


def test_el_eval_set_de_m2_usa_el_prompt_que_se_entreno():
    # M2 genera con el prompt del dataset (no con el del eval set), pero el
    # eval set traia el prompt anterior a la reconstruccion del dataset: un
    # registro que no describe como se evaluo. Se mantienen iguales.
    with open(eval_config.PROJECT_ROOT / "data" / "eval_set.json", encoding="utf-8") as f:
        eval_set = json.load(f)
    assert {r["messages"][0]["content"] for r in eval_set} == {_system_prompt_del_dataset()}
