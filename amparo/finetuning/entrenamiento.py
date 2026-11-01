"""Entrenamiento LoRA de M1 (antes: celdas 22 a 25 y el guardado del
adaptador de la 36 del notebook).

Las constantes de la receta viven aqui como valores por omision; lo que en
el notebook eran variables globales (`model`, `ds_train`, `HP`...) entra por
parametro. torch, transformers, peft y matplotlib se importan dentro de las
funciones: el modulo se importa (y se prueba con dobles) sin el stack pesado.
"""
from __future__ import annotations

import hashlib
import inspect
import os
from pathlib import Path

LORA = dict(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
PACIENCIA = 2
SALIDA_ENTRENAMIENTO = "runs/m1-lora"


def aplicar_lora(model, config: dict | None = None):
    """`(model_peft, lora_config)`: envuelve el modelo con LoRA.

    ESTO ES LO QUE EVITA QUE EL ENTRENAMIENTO SALGA VACIO. Con
    `gradient_checkpointing` cada bloque se recalcula en el backward, y para
    que torch sepa que hay que recalcularlo ALGUNA entrada del bloque tiene
    que pedir gradiente. Aqui ninguna lo pide: el base esta congelado y los
    embeddings no son objetivo de LoRA. El resultado no es un error: es un
    backward que se SALTA esos bloques en silencio, con todos los pesos de
    LoRA intactos. `_hf_peft_config_loaded` hace que transformers llame a
    `enable_input_require_grads` solo con `add_adapter()`; con
    `get_peft_model()` ---la ruta de aqui--- nadie lo llama.
    """
    from peft import LoraConfig, get_peft_model
    lora_config = LoraConfig(**(config or LORA))
    model = get_peft_model(model, lora_config)
    if hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()
    else:                                    # peft/transformers antiguos
        model.get_input_embeddings().register_forward_hook(
            lambda _mod, _ent, sal: sal.requires_grad_(True))
    model.print_trainable_parameters()
    return model, lora_config


def hiperparametros(semilla: int, salida: str = SALIDA_ENTRENAMIENTO) -> dict:
    """La receta, antes de filtrarla contra la version instalada."""
    return dict(
        output_dir=salida, seed=semilla, data_seed=semilla,
        learning_rate=1e-4, lr_scheduler_type="cosine", warmup_ratio=0.05,
        num_train_epochs=8,
        # LOTE 2 CON ACUMULACION 4, no 4 con 2. El lote EFECTIVO es el mismo
        # (8), asi que el entrenamiento es equivalente, pero el pico de memoria
        # se parte por dos: con 4x768 la perdida reventaba la A100 de 40 GB
        # (`cross_entropy` materializa `batch x seq x vocab`, ~1.87 GB en fp32).
        per_device_train_batch_size=2, gradient_accumulation_steps=4,
        per_device_eval_batch_size=2, logging_steps=1,
        # Recalcular activaciones en el backward: ~30% de tiempo a cambio de
        # mucha memoria; la A100 ya revento una vez. `use_reentrant=False` no es
        # un detalle: la ruta reentrante EXIGE que alguna entrada pida gradiente
        # y con el base congelado se salta el backward en silencio. Es el
        # segundo cinturon, junto a `enable_input_require_grads()`, y
        # `comprobar_lora_b` avisa si los dos fallaran.
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        # ROADMAP #16. Eran 8 epocas fijas con `save_strategy="no"`: se evaluaba
        # la ULTIMA epoca sin saber si el minimo de `eval_loss` estaba en la 5.
        # Ahora se guarda por epoca y se carga el mejor; `save_total_limit=2`
        # deja vivos solo el mejor y el ultimo, para no llenar el disco.
        save_strategy="epoch", save_total_limit=2,
        load_best_model_at_end=True, metric_for_best_model="eval_loss",
        greater_is_better=False,
        bf16=True, report_to="none",
    )


def filtrar_hiperparametros(hp: dict, firma: set[str], n_train: int):
    """`(hp_filtrado, omitidos, traducidos)` contra la firma REAL de
    `TrainingArguments`.

    transformers renombra y retira parametros entre versiones
    (`evaluation_strategy` -> `eval_strategy`; en 5.x `warmup_ratio` ya no
    existe). En vez de fijar una version se filtra y se deja constancia de lo
    que se cayo: un hiperparametro que desaparece en silencio cambia el
    entrenamiento sin que nadie lo sepa.

    UN HIPERPARAMETRO QUE SE CAE NO SE SUSTITUYE SOLO. La corrida
    20261018T200907Z dejo `warmup_ratio` en `entrenamiento_omitido` ---honesto---
    pero entreno SIN warmup. `warmup_steps` si existe y la proporcion se
    traduce (pasos por epoca x epocas x proporcion), con constancia de la
    traduccion para que no parezca que `warmup_ratio` funciono.
    """
    hp = dict(hp)
    clave_eval = "eval_strategy" if "eval_strategy" in firma else "evaluation_strategy"
    hp[clave_eval] = "epoch"
    omitidos = {k: v for k, v in hp.items() if k not in firma}
    hp = {k: v for k, v in hp.items() if k in firma}
    traducidos = {}
    if "warmup_ratio" in omitidos and "warmup_steps" in firma:
        por_epoca = max(1, n_train // (hp["per_device_train_batch_size"]
                                       * hp["gradient_accumulation_steps"]))
        total = por_epoca * hp["num_train_epochs"]
        pasos = max(1, round(total * omitidos["warmup_ratio"]))
        hp["warmup_steps"] = pasos
        traducidos["warmup_ratio->warmup_steps"] = {
            "ratio": omitidos.pop("warmup_ratio"), "pasos": pasos,
            "pasos_totales_estimados": total}
    return hp, omitidos, traducidos


def callbacks_parada(paciencia: int = PACIENCIA) -> list:
    """PARAR CUANDO `eval_loss` DEJA DE BAJAR.

    La corrida anterior configuro 8 epocas y el minimo estaba en la TERCERA
    (0.694 contra 0.932 en la 8): cinco epocas de mas, ~45 minutos de A100.
    `load_best_model_at_end` ya cargaba la mejor, asi que el MODELO no cambia
    por parar antes; solo el tiempo. El techo se queda en 8 para que una receta
    futura que mueva el minimo lo pueda encontrar.
    """
    try:
        from transformers import EarlyStoppingCallback
    except ImportError:
        return []
    return [EarlyStoppingCallback(early_stopping_patience=paciencia)]


def crear_trainer(model, ds_train, ds_val, collate, hp: dict, *, paciencia: int = PACIENCIA):
    """`(trainer, hp, omitidos, traducidos, parada)`.

    `PYTORCH_CUDA_ALLOC_CONF` va ANTES de que torch reserve: lo dice el propio
    error de CUDA ("1.58 GiB is reserved but unallocated"), memoria perdida
    por fragmentacion que los segmentos expandibles recuperan.
    """
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    from transformers import Trainer, TrainingArguments
    firma = set(inspect.signature(TrainingArguments.__init__).parameters)
    hp, omitidos, traducidos = filtrar_hiperparametros(hp, firma, len(ds_train))
    if omitidos:
        print("ATENCION · hiperparametros que esta version de transformers no acepta:")
        for k, v in omitidos.items():
            print(f"   {k} = {v}  (omitido)")
    if traducidos:
        print("Traducidos a un parametro que esta version SI acepta:")
        for k, v in traducidos.items():
            print(f"   {k}: {v}")
    parada = callbacks_parada(paciencia)
    if parada:
        print(f"early stopping activo: para tras {paciencia} epocas sin mejorar "
              f"`{hp.get('metric_for_best_model')}` (techo {hp['num_train_epochs']})")
    else:
        print("ATENCION · esta version no trae EarlyStoppingCallback: se corren "
              f"las {hp['num_train_epochs']} epocas completas.")
    trainer = Trainer(model=model, args=TrainingArguments(**hp), train_dataset=ds_train,
                      eval_dataset=ds_val, data_collator=collate, callbacks=parada)
    return trainer, hp, omitidos, traducidos, parada


def registro_hiperparametros(*, modelo_base: str, semilla: int, max_len: int, lora_config,
                             hp: dict, omitidos: dict, traducidos: dict, parada: list,
                             paciencia: int = PACIENCIA, splits: dict,
                             versiones: dict | None = None) -> dict:
    """El artefacto `hiperparametros`: la receta EJECUTADA, no la escrita."""
    if versiones is None:
        import datasets as hfds
        import peft
        import torch
        import transformers
        versiones = {"torch": torch.__version__, "transformers": transformers.__version__,
                     "peft": peft.__version__, "datasets": hfds.__version__}
    return {
        "modelo_base": modelo_base, "semilla": semilla, "max_len": max_len,
        "lora": {"r": lora_config.r, "alpha": lora_config.lora_alpha,
                 "dropout": lora_config.lora_dropout,
                 "target_modules": list(lora_config.target_modules)},
        "entrenamiento": {k: v for k, v in hp.items() if k != "output_dir"},
        "entrenamiento_omitido": omitidos,
        "entrenamiento_traducido": traducidos,
        "early_stopping": {"activo": bool(parada), "paciencia": paciencia,
                           "metrica": hp.get("metric_for_best_model"),
                           "techo_epocas": hp["num_train_epochs"]},
        "versiones": versiones,
        "splits": splits,
    }


def comprobar_lora_b(model) -> tuple[int, int]:
    """¿ENTRENO DE VERDAD? Devuelve `(vivos, total)` de los tensores lora_B.

    `lora_B` nace en CERO a proposito: el adaptador arranca siendo la
    identidad. Eso lo vuelve el testigo perfecto: si el gradiente nunca llego,
    sigue en cero, el "afinado" se comporta como el base, y M2 y M3 medirian el
    base creyendo medir el afinado. Un solo tensor distinto de cero demuestra
    que el backward paso. No comprueba que haya aprendido BIEN; comprueba que
    haya aprendido ALGO.
    """
    b = [p for n, p in model.named_parameters() if "lora_B" in n]
    assert b, "no hay tensores lora_B: este modelo no lleva adaptador LoRA"
    vivos = sum(1 for p in b if p.detach().abs().sum().item() > 0)
    print(f"  lora_B con peso aprendido: {vivos}/{len(b)}")
    assert vivos, (
        "TODOS los lora_B siguen en CERO: el entrenamiento no movio un solo peso.\n"
        "El adaptador es la identidad, asi que evaluarlo mide el modelo BASE.\n"
        "Causa tipica: gradient_checkpointing sin `enable_input_require_grads()`\n"
        "ni `use_reentrant=False`. Revisa `aplicar_lora` y `hiperparametros`.")
    if vivos < len(b):
        print(f"  AVISO · {len(b) - vivos} tensor(es) lora_B sin mover. Con lr 1e-4")
        print("  deberian haberse movido todos: mirar si alguna capa quedo fuera.")
    return vivos, len(b)


def seleccionar_checkpoint(log_history: list[dict], epocas_configuradas) -> dict:
    """ROADMAP #16: que epoca gano, y si las epocas configuradas sobraban.

    `load_best_model_at_end` ya cargo el mejor; aqui se DOCUMENTA cual fue,
    que es lo que permite defender la eleccion en vez de afirmarla.
    """
    evals = [(h.get("epoch"), h["eval_loss"]) for h in log_history if "eval_loss" in h]
    seleccion = {"epocas_configuradas": epocas_configuradas,
                 "curva_eval_loss": [{"epoca": e, "eval_loss": round(v, 5)} for e, v in evals]}
    if not evals:
        print("  sin eval_loss en el historial: revisa que eval_strategy sea 'epoch'")
        return seleccion
    mejor_ep, mejor_loss = min(evals, key=lambda x: x[1])
    ultima_ep, ultima_loss = evals[-1]
    seleccion.update({
        "mejor_epoca": mejor_ep, "mejor_eval_loss": round(mejor_loss, 5),
        "ultima_epoca": ultima_ep, "ultima_eval_loss": round(ultima_loss, 5),
        "las_epocas_sobraban": mejor_ep < ultima_ep,
        "cargado": "el mejor checkpoint (load_best_model_at_end=True)"})
    print("\n  eval_loss por epoca: " + "  ".join(f"{e:.0f}:{v:.4f}" for e, v in evals))
    print(f"  minimo en la epoca {mejor_ep:.0f} ({mejor_loss:.4f})"
          f"  ultima {ultima_ep:.0f} ({ultima_loss:.4f})")
    if mejor_ep < ultima_ep:
        print(f"  Las {epocas_configuradas} epocas SOBRABAN: el minimo estaba en la "
              f"{mejor_ep:.0f} y de ahi en adelante el modelo empeoraba en validacion.")
        print("  Se cargo el mejor, no el ultimo.")
    else:
        print("  El minimo esta en la ultima epoca: el presupuesto no sobraba,")
        print("  y puede que falte. Vale la pena probar con mas.")
    return seleccion


def graficar_perdida(log_history: list[dict], ruta, mostrar: bool = True):
    """Curva de perdida (train y eval) guardada en `ruta`. Devuelve el mejor
    `(epoca, eval_loss)` o None."""
    import matplotlib
    if not mostrar:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    tr = [(h["epoch"], h["loss"]) for h in log_history if "loss" in h]
    ev = [(h["epoch"], h["eval_loss"]) for h in log_history if "eval_loss" in h]
    plt.figure(figsize=(8, 4))
    if tr:
        plt.plot(*zip(*tr), label="training loss", lw=1.2)
    if ev:
        plt.plot(*zip(*ev), "o-", label="eval loss (validation)", lw=1.6)
    plt.xlabel("epoca"); plt.ylabel("loss"); plt.legend()
    plt.title("M1 · curva de perdida"); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(str(ruta), dpi=140)
    if mostrar:
        plt.show()
    plt.close()
    if not ev:
        return None
    mejor = min(ev, key=lambda x: x[1])
    print(f"mejor eval_loss: {mejor[1]:.4f} en epoca {mejor[0]:.0f} de {len(ev)}")
    if mejor[0] < len(ev) - 1:
        print("El eval_loss toco su minimo antes del final: a partir de ahi memoriza.")
        print("Es el numero que decide si 8 epocas son demasiadas, no la intuicion.")
    return mejor


def guardar_adaptador(model, tokenizer, carpeta_modelos, corrida_id: str, raiz) -> dict:
    """Guarda el adaptador en `models/m1-adaptador-<id>` y devuelve su ficha
    (`ruta`, `huella_pesos`, `bytes`) para `corrida.json`.

    EL ADAPTADOR SE VERSIONA POR CORRIDA, Y NO ES BUROCRACIA. Dos corridas con
    el mismo codigo y datos dieron 0.889 y 0.873 de acierto juridico: con un
    solo directorio sobrescrito no habria forma de volver al adaptador que dio
    el numero reportado. `models/m1-adaptador/CUAL_ES.txt` apunta al vigente;
    lo que se cita en el reporte es la ruta con el id. La huella de los pesos
    permite cotejar que el adaptador que se carga es el que produjo las cifras.
    """
    carpeta_modelos, raiz = Path(carpeta_modelos), Path(raiz)
    destino = carpeta_modelos / f"m1-adaptador-{corrida_id}"
    destino.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(destino))
    tokenizer.save_pretrained(str(destino))
    pesos = sorted(destino.glob("adapter_model*"))
    huella = hashlib.sha256(pesos[0].read_bytes()).hexdigest()[:16] if pesos else None
    ficha = {"ruta": str(destino.relative_to(raiz)).replace("\\", "/"),
             "huella_pesos": huella,
             "bytes": pesos[0].stat().st_size if pesos else None}
    ultimo = carpeta_modelos / "m1-adaptador"
    ultimo.mkdir(parents=True, exist_ok=True)
    (ultimo / "CUAL_ES.txt").write_text(
        f"El adaptador vigente es {destino.name}\n"
        f"huella de los pesos: {huella}\n"
        f"corrida: {corrida_id}\n", encoding="utf-8")
    print(f"adaptador -> {ficha['ruta']}")
    print(f"   huella de los pesos: {huella}")
    print("   models/m1-adaptador/CUAL_ES.txt apunta a este")
    return ficha
