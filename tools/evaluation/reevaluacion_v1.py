"""Reevaluacion del adaptador v1 con el prompt correcto. **Solo inferencia.**

## Por que existe

Las corridas del 2026-10-09 generaron las 334 respuestas de validacion con el
system prompt de `records[0]`, el de sin contexto. Los 103 registros con
contexto -- 55 B1, **35 B2**, 13 B3 -- se evaluaron sin la orden de abstenerse
con la que se entrenaron. El 0/35 de abstencion literal y el 1/35 de
`B2_funcional` se midieron asi (docs/m1_auditoria_preentrenamiento.md).

Antes de gastar GPU en un candidato hay que saber cuanto de ese fallo era del
prompt. Esto vuelve a generar con el adaptador v1 que ya existe, sin entrenar,
dandole a cada registro **su propio** prompt.

## Que se fija y por que

**Revision del modelo base: `a09a35458c702b33eeacc393d103063234e8bc28`.** El
codigo de v1 no fijaba `revision` y bajo `main`. El historial del repo
`Qwen/Qwen2.5-7B-Instruct` en Hugging Face dice que el ultimo commit a `main`
es ese, del **2025-01-12**, y v1 se entreno el **2026-10-09**: entre las dos
fechas no hubo ningun commit, asi que `main` era ese. Ademas ese commit solo
toca el README; los pesos no cambian desde el 2024-09-19. La cache local de HF
tiene el mismo snapshot.

**Adaptador: huella `8ce3cc2bc9306974`.** La del `run_manifest.json` de v1,
calculada con `huella_archivo` sobre `adapter_model.safetensors`. Si el
adaptador que se carga no la tiene, no se genera nada.

**Decodificacion:** la de `generation.run_messages_generation`, identica a la del
notebook historico -- greedy, `max_new_tokens=900`, decode sin tokens especiales.

## De donde salen los registros: de la corrida historica, no del dataset

Los 103 registros se leen de `results/m1_2026-10-09/finetuned_results.jsonl`,
que guarda los `messages` **exactos** que vio v1 -- identicos a la base
`9c9f5a9` en los 103. NO del dataset actual: en v3 se reconstruyo el contexto de
los 35 B2 de validacion (defecto del commit 33cc019, ver la auditoria), asi que
leer del dataset cambiaria **prompt y contexto a la vez**.

Asi la unica variable que cambia es la que se quiere medir: con que system
prompt se genera. El contexto, la pregunta y el adaptador son los de entonces.
Y las adjudicaciones de contexto de `m1_b2_adjudicacion.csv`
(`pertinencia_contexto`, `fragmentos_relevantes`) siguen valiendo, porque el
contexto es el mismo; solo hay que adjudicar las respuestas nuevas.

## Lo que NO se pudo recuperar, y como se compensa

Las versiones de librerias de v1 (`library_versions: None` en su manifiesto).
Distintas versiones de transformers, peft o bitsandbytes pueden cambiar la
salida aun con los mismos pesos. Por eso hay un **control de reproduccion**:
se regeneran registros SIN contexto -- que v1 si evaluo con su prompt correcto
-- y se comparan con lo que salio en la corrida historica. La regla, fijada
antes de correr:

    control identico en todos los casos  -> REPRODUCCION
    cualquier diferencia                 -> DIAGNOSTICO

Con DIAGNOSTICO los resultados indican, pero no reproducen la corrida
historica: algo del stack cambio.

## Lo que esta corrida NO decide sola

`B2_funcional` necesita **adjudicacion**: `calibracion` y `fundamentacion` no se
calculan solos (ver `b2_funcional.py`). Lo que si sale al momento es la
abstencion literal y los fallos criticos mecanicos. El resto pasa por
`tools/adjudicacion_b2.py`.

    python -m tools.evaluation.reevaluacion_v1 --adaptador <dir> --dry-run
    python -m tools.evaluation.reevaluacion_v1 --adaptador <dir> --salida <dir>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.evaluation import config

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
REVISION_V1 = "a09a35458c702b33eeacc393d103063234e8bc28"
HUELLA_ADAPTADOR_V1 = "8ce3cc2bc9306974"
MAX_NEW_TOKENS = 900            # MAX_NEW_TOKENS_EVAL del notebook historico
N_CONTROL = 10

RESULTADOS_V1 = config.PROJECT_ROOT / "results" / "m1_2026-10-09" / "finetuned_results.jsonl"
ALCANCES = ("b2", "contexto")


def leer(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in Path(ruta).read_text(encoding="utf-8").splitlines()
            if l.strip()]


def fuente() -> list[dict]:
    """Las 334 filas de la corrida historica de v1, con sus `messages` exactos."""
    if not RESULTADOS_V1.exists():
        raise SystemExit(f"no esta {RESULTADOS_V1}: es la fuente de los registros")
    return leer(RESULTADOS_V1)


def huella_fuente() -> str:
    from tools.rag.manifiesto import huella_archivo

    return huella_archivo(RESULTADOS_V1)


def seleccionar(filas: list[dict], alcance: str = "contexto") -> list[dict]:
    """Los registros con contexto a regenerar con el prompt correcto."""
    if alcance not in ALCANCES:
        raise SystemExit(f"alcance {alcance!r} no esta en {ALCANCES}")
    con = [r for r in filas if r.get("modo") is not None]
    if alcance == "b2":
        con = [r for r in con if r["modo"] == "B2"]
    return sorted(con, key=lambda r: r["id"])


def seleccionar_control(filas: list[dict], n: int = N_CONTROL) -> list[dict]:
    """Los primeros `n` registros SIN contexto, por id. Para ellos el prompt de
    v1 ya era el correcto, asi que regenerarlos tiene que dar la misma cadena
    que en la corrida historica si el stack es el mismo."""
    return sorted((r for r in filas if r.get("modo") is None),
                  key=lambda r: r["id"])[:n]


def clasificar(control: list[dict]) -> str:
    """La regla, fijada antes de correr. Exacto o nada: con decodificacion greedy
    el mismo stack da la misma cadena."""
    if not control:
        return "SIN_CONTROL"
    return "REPRODUCCION" if all(c["coincide"] for c in control) else "DIAGNOSTICO"


def verificar_adaptador(adaptador) -> str:
    """La huella del adaptador, o se detiene si no es v1."""
    from tools.rag.manifiesto import huella_archivo

    h = huella_archivo(Path(adaptador) / "adapter_model.safetensors")
    if h is None:
        raise SystemExit(f"no hay adapter_model.safetensors en {adaptador}")
    if h != HUELLA_ADAPTADOR_V1:
        raise SystemExit(
            f"el adaptador de {adaptador} tiene huella {h} y v1 es "
            f"{HUELLA_ADAPTADOR_V1}. Esta reevaluacion es de v1: no se genera nada.")
    return h


def plan(adaptador, alcance: str = "contexto", n_control: int = N_CONTROL,
         revision: str = REVISION_V1) -> dict:
    """Todo lo que se va a hacer, comprobado, sin cargar ningun modelo."""
    from collections import Counter

    from tools.evaluation.dataset import huella_prompt

    filas = fuente()
    objetivo = seleccionar(filas, alcance)
    control = seleccionar_control(filas, n_control)
    return {
        "modelo": MODEL_ID,
        "revision_base": revision,
        "revision_es_la_de_v1": revision == REVISION_V1,
        "adaptador": str(adaptador),
        "huella_adaptador": verificar_adaptador(adaptador),
        "fuente": RESULTADOS_V1.relative_to(config.PROJECT_ROOT).as_posix(),
        "huella_fuente": huella_fuente(),
        "alcance": alcance,
        "n_objetivo": len(objetivo),
        "por_modo": dict(Counter(r["modo"] for r in objetivo)),
        "prompts_objetivo": sorted({huella_prompt(r) for r in objetivo}),
        "n_control": len(control),
        "prompts_control": sorted({huella_prompt(r) for r in control}),
        "ids_control": [r["id"] for r in control],
        "max_new_tokens": MAX_NEW_TOKENS,
    }


# --- Lo que corre en Colab, con GPU ------------------------------------------

def cargar(adaptador, revision: str = REVISION_V1):
    """Modelo base 4-bit, la misma configuracion que el notebook, mas v1."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_use_double_quant=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=revision)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(MODEL_ID, revision=revision,
                                                quantization_config=bnb,
                                                device_map="auto")
    model = PeftModel.from_pretrained(base, str(adaptador))
    model.eval()
    return model, tokenizer


def generar(model, tokenizer, registro: dict) -> tuple[str, int]:
    from tools.evaluation.dataset import prompt_de
    from tools.evaluation.generation import run_messages_generation

    return run_messages_generation(model, tokenizer, prompt_de(registro),
                                   MAX_NEW_TOKENS, return_n_tokens=True)


def correr(adaptador, salida, alcance: str = "contexto", n_control: int = N_CONTROL,
           revision: str = REVISION_V1) -> dict:
    from tools.evaluation import corrida
    from tools.evaluation.dataset import huella_prompt
    from tools.evaluation.ragas_metrics import es_abstencion_pura

    p = plan(adaptador, alcance, n_control, revision)
    filas = fuente()

    # La identidad de los datos de entrada es la del archivo historico: de ahi
    # salen los registros, no del dataset.
    firma = corrida.firma(huella_dataset=p["huella_fuente"], model_id=MODEL_ID,
                          adaptador="v1-reevaluacion-prompt-correcto",
                          revision_base=corrida.exigir_revision(revision),
                          raiz=config.PROJECT_ROOT)
    directorio = Path(salida) / firma["corrida_id"]
    corrida.escribir(directorio, firma)

    model, tokenizer = cargar(adaptador, revision)

    # 1. Control de reproduccion, ANTES: si falla, se sabe desde el principio.
    control = []
    for r in seleccionar_control(filas, n_control):
        texto, n = generar(model, tokenizer, r)
        control.append({"id": r["id"], "coincide": texto == (r.get("generated") or ""),
                        "generated": texto, "historico": r.get("generated") or "",
                        "n_tokens": int(n)})
    veredicto = clasificar(control)
    (directorio / "control_reproduccion.json").write_text(
        json.dumps({"veredicto": veredicto, "casos": control}, ensure_ascii=False,
                   indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"control de reproduccion: {sum(c['coincide'] for c in control)}/"
          f"{len(control)} identicos -> {veredicto}", flush=True)

    # 2. Los registros con contexto, con SU prompt. Reanudable.
    previos = corrida.verificar_checkpoint(directorio, firma, "afinado",
                                           n_esperado=p["n_objetivo"],
                                           huella_adaptador=p["huella_adaptador"])
    hechos = {str(x["id"]) for x in previos}
    ruta = directorio / "afinado_results.jsonl"
    for i, r in enumerate(seleccionar(filas, alcance), start=1):
        if str(r["id"]) in hechos:
            continue
        texto, n = generar(model, tokenizer, r)
        fila = {"id": r["id"], "category": r["category"], "modo": r["modo"],
                "generated": texto, "n_tokens": int(n),
                "presupuesto_agotado": bool(n >= MAX_NEW_TOKENS),
                "prompt_sistema": huella_prompt(r), "con_contexto": True,
                "generated_historico_prompt_equivocado": r.get("generated") or ""}
        with ruta.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")
        print(f"[{i}/{p['n_objetivo']}] {r['id']} {r['modo']}", flush=True)

    filas = leer(ruta)
    b2 = [f for f in filas if f["modo"] == "B2"]
    resumen = {
        **p, "corrida_id": firma["corrida_id"], "commit": firma["commit"],
        "control": veredicto,
        "abstencion_literal_b2": {
            "prompt_correcto": sum(1 for f in b2 if es_abstencion_pura(f["generated"])),
            "prompt_equivocado_2026_10_09": sum(
                1 for f in b2 if es_abstencion_pura(f["generated_historico_prompt_equivocado"])),
            "n": len(b2),
        },
        "comparable_con_el_1_de_35": False,
        "nota": ("B2_funcional exige adjudicacion. Esta cifra es la abstencion "
                 "literal (metrica A); la funcional sale de tools/adjudicacion_b2.py."),
    }
    (directorio / "resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    return resumen


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adaptador", required=True)
    ap.add_argument("--salida", default=None)
    ap.add_argument("--alcance", default="contexto", choices=ALCANCES)
    ap.add_argument("--control", type=int, default=N_CONTROL)
    ap.add_argument("--revision", default=REVISION_V1)
    ap.add_argument("--dry-run", action="store_true",
                    help="comprueba todo sin cargar el modelo")
    a = ap.parse_args(argv)

    if a.dry_run:
        p = plan(a.adaptador, a.alcance, a.control, a.revision)
        print("PLAN DE REEVALUACION DE v1 (no se cargo ningun modelo)")
        for k, v in p.items():
            print(f"  {k:22} {v}")
        if not p["revision_es_la_de_v1"]:
            print("\n  AVISO: revision distinta de la de v1 -> el resultado sera DIAGNOSTICO")
        return 0
    if not a.salida:
        raise SystemExit("--salida es obligatorio fuera de --dry-run")
    r = correr(a.adaptador, a.salida, a.alcance, a.control, a.revision)
    print(json.dumps(r["abstencion_literal_b2"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
