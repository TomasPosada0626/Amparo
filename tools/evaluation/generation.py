"""Carga del modelo, manejo del adaptador LoRA y generacion de texto.

Requiere GPU + torch/transformers/peft/bitsandbytes (instalados solo dentro
del notebook de Colab -- ver colab/evaluacion.ipynb -- no en requirements.txt
del repo, para no arriesgar romper el build de PyTorch con CUDA que Colab ya
trae preinstalado). Las importaciones pesadas son perezosas (dentro de cada
funcion) a proposito: asi este modulo SI es importable fuera de Colab (p. ej.
por judge.py/bias.py para sus partes puras), aunque llamar a estas funciones
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
    baseline_finetune.ipynb / la de "Modo rapido"."""
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


def detach_adapter(model):
    """Quita las capas LoRA SIN fusionarlas (model.unload()) y devuelve el
    modelo base original -- para reutilizarlo como juez independiente. NO usar
    merge_and_unload(): eso horneria el fine-tuning en los pesos y arruinaria
    la independencia del juez."""
    model = model.unload()
    model.eval()
    return model


def run_chat_generation(
    model,
    tokenizer,
    system_prompt: str,
    user_content: str,
    max_new_tokens: int,
) -> str:
    """Boilerplate compartido de generacion: apply_chat_template -> tokenize
    -> generate (greedy) -> decode. Usado tanto para generar respuestas del
    asistente como para las llamadas del juez (judge.py, bias.py)."""
    import torch

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
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
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


def generate_response(
    model,
    tokenizer,
    system_prompt: str,
    query: str,
    max_new_tokens: int = config.MAX_NEW_TOKENS_GENERATION,
) -> str:
    return run_chat_generation(model, tokenizer, system_prompt, query, max_new_tokens)


@dataclass
class GenerationResult:
    id: int
    category: str
    query: str
    expected: str
    generated: str
    label: str  # "baseline" | "fine_tuned"
    latency_s: float


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
        generated = generate_response(
            model, tokenizer, system_prompt, query, max_new_tokens
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
