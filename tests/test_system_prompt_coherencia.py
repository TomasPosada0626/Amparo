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

from tools.evaluation import config as eval_config
from tools.model_comparator import config as mc_config
from tools.rag import prompt_template


def _system_prompt_del_dataset() -> str:
    """El system prompt tal como quedo en data/dataset_legal.jsonl."""
    with open(eval_config.LOCAL_DATASET_PATH, encoding="utf-8") as f:
        primer_registro = json.loads(f.readline())
    return primer_registro["messages"][0]["content"]


def test_el_prompt_del_comparador_es_el_que_se_entreno():
    assert mc_config.SYSTEM_PROMPT == _system_prompt_del_dataset()


def test_el_prompt_del_rag_es_el_que_se_entreno():
    # Si esto falla, el RAG de M3 esta generando con un rol distinto del que
    # aprendio el adaptador de M1: el delta deja de ser atribuible al RAG.
    assert prompt_template.SYSTEM_PROMPT_M1 == _system_prompt_del_dataset()


def test_todo_el_dataset_usa_el_mismo_system_prompt():
    with open(eval_config.LOCAL_DATASET_PATH, encoding="utf-8") as f:
        prompts = {json.loads(linea)["messages"][0]["content"] for linea in f if linea.strip()}
    assert len(prompts) == 1, f"el dataset mezcla {len(prompts)} system prompts distintos"
