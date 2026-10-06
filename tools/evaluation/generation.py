"""Carga del modelo, manejo del adaptador LoRA y generacion de texto.

Requiere GPU + torch/transformers/peft/bitsandbytes (instalados solo dentro
del notebook de Colab -- ver colab/m2_evaluacion.ipynb -- no en requirements.txt
del repo, para no arriesgar romper el build de PyTorch con CUDA que Colab ya
trae preinstalado). Las importaciones pesadas son perezosas (dentro de cada
funcion) a proposito: asi este modulo SI es importable fuera de Colab (p. ej.
por tests y por herramientas que no generan), aunque llamar a estas funciones
sin torch/peft instalados sigue fallando -- eso es esperado, solo corren
dentro de Colab.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from tools.evaluation import config


def load_base_model(model_id: str = config.BASE_MODEL_ID):
    """Carga el modelo base en 4-bit (QLoRA), igual que la celda 9 de
    m1_finetune.ipynb / la de "Modo rapido"."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_id, quantization_config=bnb_config, device_map="auto"
    )
    model.eval()
    return model, tokenizer


def attach_adapter(model, adapter_dir: str | Path):
    from peft import PeftModel

    model = PeftModel.from_pretrained(model, str(adapter_dir))
    model.eval()
    return model


# Marcas de fin de turno que quedan al decodificar SIN saltar tokens especiales.
_FINES_DE_TURNO = ("<|im_end|>", "<|endoftext|>")


def run_messages_generation(
    model,
    tokenizer,
    messages: list[dict],
    max_new_tokens: int,
    tools: list[dict] | None = None,
    return_n_tokens: bool = False,
):
    """Boilerplate compartido de generacion: apply_chat_template -> tokenize
    -> generate (greedy) -> decode, sobre una lista de mensajes ya armada
    (system + turnos previos + turno final). run_chat_generation (system +
    user) es el caso de un solo turno; el motor de DSPy (tools/rag/dspy_prompt.py)
    necesita el multi-turno completo porque los demos few-shot son turnos
    previos, no texto dentro del mismo mensaje.

    tools: esquemas de herramientas en el formato estandar de function calling
    ({"type": "function", "function": {...}}). Se pasan a la plantilla de chat
    del modelo, que los presenta en el formato con el que Qwen2.5 fue entrenado
    para pedir herramientas (<tool_call>...</tool_call>). En ese caso se decodifica
    SIN saltar tokens especiales, para no perder las etiquetas <tool_call>, y se
    limpian solo las marcas de fin de turno. Ver tools/rag/tools.py (seccion 26
    de docs/m3_decisiones_rag.md).

    return_n_tokens: devuelve (texto, tokens generados). Sirve para saber si la
    respuesta se corto por max_new_tokens (ver generate_batch)."""
    import torch

    extra = {"tools": tools} if tools else {}
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, **extra
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
        )
    generated_ids = output_ids[0][inputs["input_ids"].shape[1]:]
    if not tools:
        texto = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
    else:
        texto = tokenizer.decode(generated_ids, skip_special_tokens=False)
        for marca in _FINES_DE_TURNO:
            texto = texto.replace(marca, "")
        texto = texto.strip()
    return (texto, int(generated_ids.shape[0])) if return_n_tokens else texto


def run_chat_generation(
    model,
    tokenizer,
    system_prompt: str,
    user_content: str,
    max_new_tokens: int,
    return_n_tokens: bool = False,
):
    """Un solo turno (system + user) con el modelo cargado en la GPU."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    return run_messages_generation(model, tokenizer, messages, max_new_tokens,
                                   return_n_tokens=return_n_tokens)


def generate_response(
    model,
    tokenizer,
    system_prompt: str,
    query: str,
    max_new_tokens: int = config.MAX_NEW_TOKENS_GENERATION,
    return_n_tokens: bool = False,
):
    return run_chat_generation(model, tokenizer, system_prompt, query, max_new_tokens,
                               return_n_tokens=return_n_tokens)


@dataclass
class GenerationResult:
    id: int
    category: str
    query: str
    expected: str
    generated: str
    label: str  # "baseline" | "fine_tuned"
    latency_s: float
    # Tokens generados y si la respuesta se corto por max_new_tokens. En la
    # corrida del 2026-10-02, con 300 tokens, 159 de las 213 respuestas del
    # baseline terminaban a mitad de frase: el juez y las metricas contra la
    # referencia castigaban al baseline por incompleto, no por incorrecto.
    n_tokens: int = 0
    cortada: bool = False


def generate_batch(
    model,
    tokenizer,
    system_prompt: str,
    records: list[dict],
    label: str,
    max_new_tokens: int = config.MAX_NEW_TOKENS_GENERATION,
    on_result: Optional[Callable[[GenerationResult], None]] = None,
    progress_every: int = 10,
) -> list[GenerationResult]:
    """Genera una respuesta por cada registro de records (formato del
    dataset: {id, category, messages:[system,user,assistant]}). on_result,
    si se pasa, se llama tras cada ejemplo -- util para ir persistiendo a
    Drive de forma incremental y no perder todo si Colab se desconecta.
    Imprime progreso cada progress_every ejemplos (0 para desactivar) --
    sin esto, un lote de 200 respuestas no muestra nada en pantalla durante
    varios minutos y parece trabado aunque este avanzando."""
    total = len(records)
    results: list[GenerationResult] = []
    start_batch = time.perf_counter()
    for i, record in enumerate(records, start=1):
        query = record["messages"][1]["content"]
        expected = record["messages"][2]["content"]
        start = time.perf_counter()
        generated, n_tokens = generate_response(
            model, tokenizer, system_prompt, query, max_new_tokens, return_n_tokens=True
        )
        latency_s = time.perf_counter() - start
        result = GenerationResult(
            id=record["id"],
            category=record["category"],
            query=query,
            expected=expected,
            generated=generated,
            label=label,
            latency_s=latency_s,
            n_tokens=n_tokens,
            cortada=n_tokens >= max_new_tokens,
        )
        results.append(result)
        if on_result is not None:
            on_result(result)
        if progress_every and (i % progress_every == 0 or i == total):
            elapsed = time.perf_counter() - start_batch
            avg = elapsed / i
            eta_min = avg * (total - i) / 60
            print(
                f"[{label}] {i}/{total} ({100 * i / total:.0f}%) -- "
                f"{avg:.1f}s/ejemplo, ETA ~{eta_min:.1f} min"
            )
    return results
