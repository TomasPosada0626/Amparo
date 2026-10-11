"""Manifiesto de una corrida de M1.

M1 era el unico modulo que no escribia manifiesto: el de results/m1_2026-10-06
se escribio a mano. Y es justo el modulo que produce el adaptador, el artefacto
cuya perdida dejo las corridas del 2026-09-27 sin forma de reproducirse -- se
sobrescribio el 6 de octubre y el historial de versiones de Drive no llega atras.

Se arma desde el repo y la carpeta del adaptador, sin depender de las variables
de la sesion de entrenamiento: asi se puede correr despues, si la sesion de
Colab ya se cerro.

Lo que NO se puede reconstruir despues se marca como tal. El hardware y las
versiones de librerias describen la maquina donde corre este script, que no
tiene por que ser la del entrenamiento; cuando se llama desde el notebook al
terminar, se pasan los de verdad con --hardware.

    # al final del notebook, con los valores reales
    python -m tools.manifiesto_m1 --adaptador "$ADAPTER_DIR" --salida "$SALIDA_DIR" \
        --hardware "$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"

    # despues, con la sesion cerrada: marca lo que no pudo observar
    python -m tools.manifiesto_m1 --adaptador /content/drive/.../amparo-lora-adapter
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from tools.evaluation import config, eval_set

# No se importan de tools.evaluation.pipeline aunque esten ahi: ese modulo trae
# metrics_classic, que importa sacrebleu, y el manifiesto quedaria necesitando
# el stack de evaluacion entero. Se genera despues de la corrida, en un runtime
# CPU sin nada instalado, y ahi fallaba con ModuleNotFoundError. Un manifiesto
# tiene que poder armarse con la libreria estandar, igual que tools/rag/config.py
# es importable sin GPU ni faiss.
# Todo el stack con que se entrena, no solo lo que mide. v1 no registro ninguna
# version y no hubo forma de reproducirlo; trl, bitsandbytes, accelerate y
# datasets tampoco se registraban en las corridas posteriores.
LIBRERIAS = ["transformers", "peft", "trl", "accelerate", "bitsandbytes", "datasets",
             "torch", "wandb", "sacrebleu", "rouge-score", "bert-score"]


def _git_commit() -> str:
    import subprocess

    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=config.PROJECT_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def _library_versions() -> dict[str, str]:
    from importlib import metadata

    versiones = {}
    for lib in LIBRERIAS:
        try:
            versiones[lib] = metadata.version(lib)
        except metadata.PackageNotFoundError:
            versiones[lib] = "not-installed"
    return versiones

# El dataset unico. Antes el default era dataset_m1_v2.jsonl, que ya no existe:
# cualquier uso sin --dataset fallaba.
DATASET_ENTRENAMIENTO = config.DATASET_PATH


def construir(
    adaptador: str | Path,
    *,
    hardware: str | None = None,
    dataset: Path = DATASET_ENTRENAMIENTO,
    hiperparametros: dict | None = None,
) -> dict:
    """El manifiesto como diccionario.

    hardware None = no se observo (la sesion ya cerro); se marca en el archivo
    en vez de poner el de la maquina que corre esto, que seria mentir.
    """
    from tools.rag.manifiesto import huella_archivo

    registros = [json.loads(l) for l in dataset.read_text(encoding="utf-8").splitlines() if l.strip()]
    por_split = Counter(r["split"] for r in registros)
    observado = hardware is not None

    manifiesto = {
        "modulo": "m1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "base_model_id": config.BASE_MODEL_ID,
        "random_seed": config.RANDOM_SEED,
        "val_fraction": config.VAL_FRACTION,

        "adapter_dir": str(adaptador),
        "hash_adaptador": huella_archivo(Path(adaptador) / "adapter_model.safetensors"),

        "dataset_entrenamiento": dataset.relative_to(config.PROJECT_ROOT).as_posix(),
        "hash_dataset_entrenamiento": huella_archivo(dataset),
        "hash_eval_set": huella_archivo(eval_set.EVAL_SET_PATH),

        "n_total": len(registros),
        "n_train": por_split["train"],
        "n_val": por_split["val"],
        "origenes": dict(Counter(r["origen"] for r in registros)),
        "val_por_origen": dict(Counter(r["origen"] for r in registros if r["split"] == "val")),
        "modos_con_contexto": dict(Counter(r.get("modo") for r in registros
                                           if r["origen"] != "v1")),

        "hiperparametros": hiperparametros,

        "hardware": hardware,
        "library_versions": _library_versions() if observado else None,
    }

    if not observado:
        manifiesto["reconstruido"] = (
            "Generado despues de la corrida, con la sesion ya cerrada. Los hashes "
            "y los conteos SI son los de la corrida (ni el adaptador, ni el dataset, "
            "ni el eval set cambiaron desde entonces). El hardware y las versiones "
            "de librerias no se pudieron observar y quedan en None en vez de poner "
            "los de la maquina que genero este archivo."
        )
    return manifiesto


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--adaptador", required=True, help="carpeta del adaptador LoRA")
    p.add_argument("--dataset", default=None,
                   help="dataset de entrenamiento (por defecto el de v1: "
                        "data/dataset_m1_v2.jsonl). v2 entrena con "
                        "data/dataset_m1_v3.jsonl y tiene que firmar ESE, o el "
                        "manifiesto diria que entreno con otro archivo.")
    p.add_argument("--hiperparametros", default=None,
                   help="JSON con la configuracion de la corrida (LoRA, epocas, "
                        "lr, batch, max_seq_length). Sin esto el manifiesto no "
                        "dice con que se entreno y la corrida no se reproduce.")
    p.add_argument("--salida", default=None, help="carpeta donde escribir run_manifest.json")
    p.add_argument("--hardware", default=None,
                   help="salida de nvidia-smi; omitirlo marca el manifiesto como reconstruido")
    args = p.parse_args(argv)

    hiper = json.loads(Path(args.hiperparametros).read_text(encoding="utf-8"))         if args.hiperparametros else None
    m = construir(args.adaptador, hardware=args.hardware,
                  dataset=Path(args.dataset) if args.dataset else DATASET_ENTRENAMIENTO,
                  hiperparametros=hiper)

    if m["hash_adaptador"] is None:
        print(f"AVISO: no se encontro adapter_model.safetensors en {args.adaptador}")
        print("  El hash del adaptador es el campo que da sentido al manifiesto.")

    if args.salida:
        ruta = Path(args.salida) / "run_manifest.json"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Escrito {ruta}")
    else:
        print(json.dumps(m, ensure_ascii=False, indent=2))

    print(f"  adaptador {m['hash_adaptador']} | dataset {m['hash_dataset_entrenamiento']}")
    print(f"  train {m['n_train']} / val {m['n_val']} | {m['origenes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
