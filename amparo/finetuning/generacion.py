"""Generacion local con Hugging Face (Qwen2.5-7B, con o sin el LoRA de M1).

Unifica tres copias que vivian en los notebooks: `generar` y
`generar_few_shot` de M1 (celdas 18 y 20, casi identicas: solo cambiaba el
prompt) y `generar_texto` de M1 (celda 32) con `generar_qwen` de M3 (celda 27),
que adaptaban el modelo a la interfaz `generar(sistema, usuario) -> str` que
usan los sistemas de `amparo.sistemas`.

torch y transformers se importan dentro de las funciones: el modulo se puede
importar (y probar con dobles) sin el stack pesado.
"""
from __future__ import annotations

import contextlib

from amparo.nucleo import schema

MODELO_BASE = "Qwen/Qwen2.5-7B-Instruct"
# Marcas de turno del chat de Qwen. `metricas.degeneracion` usa las mismas para
# detectar la cola degenerada.
MARCAS_TURNO = ("<|im_end|>", "<|im_start|>")


def ids_parada(tok) -> list[int]:
    """Tokens de parada explicitos: eos mas las marcas de turno.

    El modelo NO debe abrir un turno nuevo del chat, y en 4 de 46 casos lo
    hizo: tras el cuarto campo se desviaba al chino y escribia
    '<|im_start|>user'. Pasar el inicio de turno como parada lo corta en el
    origen. Defensivo porque no todos los tokenizadores traen estas marcas.
    """
    ids = set()
    e = tok.eos_token_id
    if isinstance(e, int):
        ids.add(e)
    elif isinstance(e, (list, tuple)):
        ids.update(i for i in e if isinstance(i, int))
    for marca in MARCAS_TURNO:
        i = tok.convert_tokens_to_ids(marca)
        if isinstance(i, int) and i >= 0 and i != tok.unk_token_id:
            ids.add(i)
    return sorted(ids)


def cargar_modelo(modelo_id: str = MODELO_BASE, *, adaptador=None, entrenable: bool = False):
    """`(model, tokenizer)` en bf16 sobre CUDA.

    Con `adaptador` (ruta) carga el LoRA encima en modo evaluacion (M3).
    `entrenable=True` deja `use_cache=False`, como lo necesita el Trainer con
    gradient checkpointing (M1).
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(modelo_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        modelo_id, torch_dtype=torch.bfloat16, device_map="cuda", attn_implementation="sdpa")
    if entrenable:
        model.config.use_cache = False
    if adaptador is not None:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(adaptador)).eval()
    return model, tokenizer


def generar_lote(model, tokenizer, ejemplos: list[dict], construir_mensajes, *,
                 parada: list[int], lote: int = 8, max_new: int = 200) -> list[str]:
    """Generacion greedy por lotes. `construir_mensajes(ej) -> [mensajes]`.

    Antes eran dos funciones (`generar` y `generar_few_shot`) que solo
    diferian en el prompt; si algo mas cambiara entre los dos brazos, la
    diferencia medida no seria el formato. Ahora el prompt es el unico
    argumento que cambia.

    Padding a la IZQUIERDA para generar: en decoder-only, padear a la derecha
    mete los tokens de relleno dentro del contexto. max_new=200 basta: la
    salida mas larga de la corrida anterior eran unos 150 tokens; el limite
    nunca fue el problema, lo fue la degeneracion.
    """
    import torch
    model.eval()
    prev, tokenizer.padding_side = tokenizer.padding_side, "left"
    salidas = []
    try:
        for i in range(0, len(ejemplos), lote):
            trozo = ejemplos[i:i + lote]
            prompts = [tokenizer.apply_chat_template(construir_mensajes(e), tokenize=False,
                                                     add_generation_prompt=True) for e in trozo]
            enc = tokenizer(prompts, return_tensors="pt", padding=True,
                            add_special_tokens=False).to(model.device)
            with torch.no_grad():
                out = model.generate(**enc, max_new_tokens=max_new, do_sample=False,
                                     eos_token_id=parada,
                                     pad_token_id=tokenizer.pad_token_id, use_cache=True)
            for j in range(len(trozo)):
                salidas.append(tokenizer.decode(out[j][enc["input_ids"].shape[1]:],
                                                skip_special_tokens=True).strip())
            print(f"  {min(i + lote, len(ejemplos))}/{len(ejemplos)}", end="\r")
    finally:
        tokenizer.padding_side = prev
    return salidas


def generador_hf(model, tokenizer, *, parada: list[int] | None = None, max_new: int = 220,
                 con_adaptador: bool = True, recortar: bool = False,
                 recortes: list[str] | None = None):
    """Adapta el modelo a la interfaz `generar(sistema, usuario) -> str`.

    - `max_new`: 320 para la extraccion de hechos de M1 (el JSON es mas largo
      que las cinco lineas), 220 para los brazos de M3.
    - `con_adaptador=False` apaga el LoRA y deja el modelo BASE: es lo unico
      que hace ejecutable el brazo hibrido de M1 (ver
      `sistemas.sistema.SistemaHibrido`).
    - `recortar=True` aplica `schema.recortar_al_bloque` (M3): el adaptador se
      descarrila en una fraccion de los casos y la cola contamina el
      retrieval y las metricas RAGAS. Si se pasa `recortes`, se anota ahi el
      comienzo del usuario de cada caso recortado.

    La funcion devuelta publica `ultimos_tokens = (entrada, salida)` despues
    de cada llamada. `model.generate()` no devuelve `usage`, y por eso los
    brazos 2 y 3 salieron con `tokens_por_caso: null` en m3/20261019T173316Z;
    el tokenizador si los cuenta, exactos, y cada brazo los lee despues de SU
    llamada, asi que compartir el generador no mezcla su contabilidad.
    """
    parada = parada if parada is not None else ids_parada(tokenizer)

    def generar(sistema_txt: str, usuario: str) -> str:
        import torch
        msgs = [{"role": "system", "content": sistema_txt},
                {"role": "user", "content": usuario}]
        p = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        enc = tokenizer(p, return_tensors="pt", add_special_tokens=False).to(model.device)
        if con_adaptador:
            ctx = contextlib.nullcontext()
        else:
            assert hasattr(model, "disable_adapter"), (
                "esta version de peft no trae `disable_adapter()`: sin eso no se "
                "puede extraer con el base y este brazo no es ejecutable")
            ctx = model.disable_adapter()
        with ctx, torch.no_grad():
            out = model.generate(**enc, max_new_tokens=max_new, do_sample=False,
                                 eos_token_id=parada, pad_token_id=tokenizer.pad_token_id,
                                 use_cache=True)
        n_entrada = int(enc["input_ids"].shape[1])
        generar.ultimos_tokens = (n_entrada, int(out.shape[1]) - n_entrada)
        texto = tokenizer.decode(out[0][n_entrada:], skip_special_tokens=True).strip()
        if recortar:
            texto, recortado = schema.recortar_al_bloque(texto)
            if recortado and recortes is not None:
                recortes.append(usuario[:60])
        return texto

    generar.ultimos_tokens = None
    return generar
