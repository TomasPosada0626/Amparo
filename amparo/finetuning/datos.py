"""Del dataset al formato de entrenamiento de M1 (antes: celda 16 del notebook).

El tokenizer y `max_len` son parametros, no variables globales del notebook.
`SISTEMA` vive aqui y no en el notebook porque el prompt de entrenamiento
tiene que ser el mismo con el que despues se genera.
"""
from __future__ import annotations

from amparo.nucleo import schema

# ROADMAP #18. Los 16 errores del campo `derecho` de la corrida anterior no
# estaban repartidos: se concentraban en cuatro pares de derechos vecinos
# (seguridad_social/minimo_vital, trabajo/minimo_vital,
# salud/estabilidad_laboral_reforzada, peticion/habeas_data). Una guia
# enumerable sirve para eso; un 'clasifica bien el derecho' no. Vive en
# schema.GUIA_DERECHOS_VECINOS para que M1 y M3 usen la misma.
#
# OJO: esto entra en el prompt de ENTRENAMIENTO, asi que un adaptador
# entrenado con otro SISTEMA no es el mismo sistema medido.
SISTEMA = (
    "Eres un asistente de triaje de acciones constitucionales en Colombia. "
    "Clasificas el caso y respondes SIEMPRE con exactamente cinco lineas, en este orden: "
    "Derecho, Accionado, Mecanismo, Procedencia, Pretension. Sin texto adicional.\n\n"
    + schema.GUIA_DERECHOS_VECINOS
)


def mensajes(ej: dict, sistema: str = SISTEMA) -> list[dict]:
    return [{"role": "system", "content": sistema},
            {"role": "user", "content": schema.render_entrada(ej)}]


def _texto_completo(ej, tokenizer, sistema):
    prompt = tokenizer.apply_chat_template(mensajes(ej, sistema), tokenize=False,
                                           add_generation_prompt=True)
    return prompt, prompt + schema.render_salida(ej) + tokenizer.eos_token


def medir_max_len(ejemplos: list[dict], tokenizer, sistema: str = SISTEMA,
                  respiro: int = 8) -> tuple[int, list[int]]:
    """`MAX_LEN` se MIDE, no se adivina. Devuelve `(max_len, largos_crudos)`.

    Las dos veces que se fijo a mano salio mal: con 640 la guia del #18
    truncaba los 110 ejemplos, y con 768 el tensor de logits de la perdida se
    fue de memoria (vocabulario de ~152k: `batch x seq x vocab` en fp32 son
    1.87 GB por lote a 768, mas otro tanto del gradiente). Se tokeniza una vez
    SIN truncar y el limite es el maximo observado mas un respiro: no hay
    truncamiento por construccion y no se paga relleno de mas.
    """
    largos = [len(tokenizer(_texto_completo(e, tokenizer, sistema)[1],
                            add_special_tokens=False)["input_ids"]) for e in ejemplos]
    return max(largos) + respiro, largos


def construir(ej: dict, tokenizer, max_len: int, sistema: str = SISTEMA) -> dict:
    """Un ejemplo tokenizado con la perdida SOLO en la respuesta: el prompt va
    enmascarado con -100."""
    prompt, full = _texto_completo(ej, tokenizer, sistema)
    ids_p = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    ids_f = tokenizer(full, add_special_tokens=False, truncation=True,
                      max_length=max_len)["input_ids"]
    labels = [-100] * len(ids_p) + ids_f[len(ids_p):]
    return {"input_ids": ids_f, "attention_mask": [1] * len(ids_f),
            "labels": labels[:len(ids_f)]}


def construir_datasets(train: list[dict], val: list[dict], tokenizer, max_len: int,
                       sistema: str = SISTEMA):
    """`(ds_train, ds_val)` como `datasets.Dataset`."""
    from datasets import Dataset
    return (Dataset.from_list([construir(e, tokenizer, max_len, sistema) for e in train]),
            Dataset.from_list([construir(e, tokenizer, max_len, sistema) for e in val]))


def comprobar_truncados(ds_train, tokenizer, max_len: int, ejemplo: dict,
                        sistema: str = SISTEMA) -> None:
    """Para si algun ejemplo toca el techo, y dice QUE parte se pierde.

    "sube MAX_LEN" invitaba al arreglo equivocado: cuando TODOS tocan el techo
    el problema no es el limite, es que el prompt de sistema se comio el
    presupuesto, y lo que se trunca es la RESPUESTA que el modelo tiene que
    aprender, no el relato.
    """
    largos = [len(x) for x in ds_train["input_ids"]]
    print(f"longitud: media {sum(largos)/len(largos):.0f} · max {max(largos)} "
          f"tokens (limite {max_len})")
    truncados = [i for i, n in enumerate(largos) if n >= max_len]
    if truncados:
        sin_prompt = len(tokenizer.apply_chat_template(
            mensajes(ejemplo, sistema), tokenize=True, add_generation_prompt=True))
        print(f"\n  {len(truncados)} de {len(largos)} ejemplos TRUNCADOS")
        print(f"  el prompt de sistema+entrada ya ocupa ~{sin_prompt} tokens")
        if len(truncados) == len(largos):
            print("  TODOS tocan el techo: el problema no es el limite, es que el")
            print("  prompt de sistema se comio el presupuesto. Acorta la guia de")
            print("  schema.GUIA_DERECHOS_VECINOS antes de subir MAX_LEN.")
        else:
            print(f"  Sube MAX_LEN a {max(largos) + 64} y vuelve a correr.")
    assert not truncados, (
        f"{len(truncados)} ejemplos truncados: se esta cortando la respuesta que "
        f"el modelo debe aprender")


def collate_para(tokenizer):
    """El `collate` del Trainer: padding a la derecha con pad / 0 / -100."""
    def collate(batch):
        import torch
        m = max(len(b["input_ids"]) for b in batch)
        pad = tokenizer.pad_token_id
        out = {"input_ids": [], "attention_mask": [], "labels": []}
        for b in batch:
            d = m - len(b["input_ids"])
            out["input_ids"].append(b["input_ids"] + [pad] * d)
            out["attention_mask"].append(b["attention_mask"] + [0] * d)
            out["labels"].append(b["labels"] + [-100] * d)
        return {k: torch.tensor(v) for k, v in out.items()}
    return collate
