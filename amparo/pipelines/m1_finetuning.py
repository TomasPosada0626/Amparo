"""M1 · Fine-tuning con LoRA, como funciones por etapa (antes:
notebooks/M1_finetuning.ipynb).

Produce el adaptador LoRA en `models/m1-adaptador-<id>`, los scorecards base
vs ajustado y `results/m1_predicciones.json`, que es lo que consumen M2 y M3.
Requiere GPU (A100) desde `cargar_modelo`.

Cada etapa recibe y devuelve el mismo `Contexto`: el notebook llama una por
celda para ver la salida de cada una, y `correr()` las encadena todas. El
orden importa (ver los comentarios de cada etapa): el baseline de formato,
por ejemplo, tiene que ir ANTES de `aplicar_lora`, porque desde ahi `model`
es el modelo adaptado.

    from amparo.pipelines import m1_finetuning as m1
    ctx = m1.preparar()
    m1.correr(ctx)
"""
from __future__ import annotations

import collections
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

from amparo.config import DATA, MODELS, RAIZ
from amparo.evaluacion import metricas
from amparo.finetuning import datos, entrenamiento, generacion
from amparo.nucleo import schema

MODEL_ID = generacion.MODELO_BASE

# Fertilidad del tokenizador (antes: celda 12). NO es `tokenizadores.medir()`:
# esa mide otros candidatos (Llama, Mistral) sobre tres registros del corpus y
# devuelve otro esquema. El artefacto `fertilidad_tokenizadores` que publica M1
# es ESTE, asi que se conserva tal cual.
CANDIDATOS_FERTILIDAD = {
    "Qwen/Qwen2.5-7B-Instruct":            {"params": "7.6B", "licencia": "Apache-2.0"},
    "Qwen/Qwen2.5-0.5B":                   {"params": "0.5B", "licencia": "Apache-2.0"},
    "BSC-LT/salamandra-2b-instruct":        {"params": "2.3B", "licencia": "Apache-2.0"},
    "HuggingFaceTB/SmolLM2-1.7B-Instruct":  {"params": "1.7B", "licencia": "Apache-2.0"},
    "dccuchile/bert-base-spanish-wwm-cased": {"params": "0.1B", "licencia": "CC-BY-4.0"},
}
TERMINOS_FERTILIDAD = [
    "accion de tutela", "derecho fundamental de peticion", "perjuicio irremediable",
    "subsidiariedad", "accionado", "estabilidad laboral reforzada", "habeas data",
    "Decreto 2591 de 1991", "minimo vital", "sujeto de especial proteccion",
    "inexequible", "carencia actual de objeto", "dano consumado",
]

SONDA = 10      # casos con los que se prueba el adaptador como extractor
CORTE = 10      # casos tras los que el brazo hibrido comprueba si vale seguir
UMBRAL_FALLOS_EXTRACCION = 0.1


@dataclass
class Contexto:
    """El estado que en el notebook eran variables globales."""
    c: Any = None                       # la corrida (corridas.Corrida)
    model: Any = None
    tokenizer: Any = None
    parada: list | None = None          # ids de parada de la generacion
    train_raw: list = field(default_factory=list)
    val_raw: list = field(default_factory=list)
    eval_raw: list = field(default_factory=list)
    max_len: int | None = None
    ds_train: Any = None
    ds_val: Any = None
    demos: list = field(default_factory=list)
    lora_config: Any = None
    trainer: Any = None
    hp: dict = field(default_factory=dict)
    salidas: dict = field(default_factory=dict)      # base, base_few_shot, finetuned, hibrido
    deg: dict = field(default_factory=dict)          # base, base_few_shot, finetuned
    sc: dict = field(default_factory=dict)           # base, base_few_shot, finetuned, hibrido
    extractor: dict = field(default_factory=dict)
    redaccion: dict | None = None
    estabilidad: dict | None = None


# --------------------------------------------------------------------------
# 0 · Proyecto y corrida
# --------------------------------------------------------------------------
def preparar() -> Contexto:
    """Corrida nueva, sello de Drive, clave de Groq y `arranque.celda("m1")`.

    La clave NO se pide por teclado en M1: la redaccion (seccion 7) es
    opcional y una corrida de 30 minutos no puede quedarse esperando a que
    alguien escriba. Sin clave, esa seccion queda registrada como no medida.
    """
    from amparo.ejecucion import entorno
    return Contexto(c=entorno.preparar("m1", pedir_clave=False))


def validar_extractor(ctx: Contexto) -> int:
    """0.1 · Antes de la GPU: ¿sirvio el arreglo del extractor? (celda 8)

    No es de M1. Esta aqui porque es lo unico que puede ahorrar el ciclo
    entero: comprobar el extractor corriendo M1 -> M2 -> M3 cuesta ~80 minutos
    de A100 y la extraccion no usa GPU (son llamadas a la API). No aborta a
    proposito: M1 no depende del extractor del agente y decidir es tuyo.

    `GROQ_API_KEY` ya esta en el entorno (`preparar`), y el subproceso la
    hereda de ahi.
    """
    v = subprocess.run([sys.executable, "-I", str(DATA / "validar_extractor.py")],
                       capture_output=True, text=True, cwd=str(RAIZ))
    print(v.stdout.strip() or (v.stderr or "")[-600:])
    print()
    if v.returncode == 0:
        print(">>> El arreglo del extractor funciona. El ciclo tiene sentido:")
        print(">>> sigue con el notebook.")
    else:
        print("=" * 70)
        print(">>> EL ARREGLO NO ESTA COMPLETO (arriba estan los casos).")
        print(">>> M1 corre igual --- no usa el extractor del agente --- pero")
        print(">>> llegar a M3 con esto roto gasta ~80 minutos de A100 para")
        print(">>> confirmar lo que ya sabes aqui. Decide antes de seguir.")
        print("=" * 70)
    return v.returncode


# --------------------------------------------------------------------------
# 1 · Por que un decoder y no un clasificador
# --------------------------------------------------------------------------
def cobertura_clasificador(ctx: Contexto) -> dict:
    """Nivel 1 de la justificacion del modelo base: un clasificador no puede
    producir la salida que el sistema necesita (celda 10)."""
    from amparo.finetuning import tokenizadores
    cc = tokenizadores.cobertura_clasificador()
    print(f"campos de vocabulario cerrado : {', '.join(cc['campos_de_vocabulario_cerrado'])}")
    print(f"campos de texto libre         : {', '.join(cc['campos_de_texto_libre'])}")
    print()
    print(f"De los {cc['chars_que_un_clasificador_podria_emitir'] + cc['chars_de_texto_libre']} "
          f"caracteres de la salida gold, un clasificador podria emitir "
          f"{cc['chars_que_un_clasificador_podria_emitir']} ({cc['cobertura_clasificador']:.1%}).")
    print("Ninguna cita normativa entra en esa fraccion: el sistema quedaria sin")
    print("`fundamento`, que es justo el campo que permite verificar la respuesta.")
    ctx.c.guardar_json("cobertura_clasificador", cc)
    return cc


# --------------------------------------------------------------------------
# 2 · Que decoder: fertilidad del tokenizador
# --------------------------------------------------------------------------
def medir_fertilidad(corpus: list[str], candidatos: dict, cargar_tokenizer) -> list[dict]:
    """Tokens por palabra de cada candidato sobre `corpus`.

    Un tokenizador que parte "inexequible" en seis piezas gasta mas contexto y
    aprende peor el vocabulario juridico. `cargar_tokenizer(id)` es
    `AutoTokenizer.from_pretrained` en la corrida y un doble en los tests.
    """
    palabras = sum(len(t.split()) for t in corpus)
    filas = []
    for mid, info in candidatos.items():
        try:
            tok = cargar_tokenizer(mid)
            n = sum(len(tok(t)["input_ids"]) for t in corpus)
            filas.append({"modelo": mid, **info, "vocab": tok.vocab_size,
                          "fertilidad": round(n / palabras, 3),
                          "genera": "no" if "bert" in mid.lower() else "si"})
        except Exception as ex:                              # noqa: BLE001
            filas.append({"modelo": mid, **info, "vocab": None, "fertilidad": None,
                          "error": str(ex)[:60]})
    filas.sort(key=lambda r: (r["fertilidad"] is None, r["fertilidad"]))
    return filas


def fertilidad_tokenizadores(ctx: Contexto, cargar_tokenizer=None) -> list[dict]:
    """Nivel 2: por que este decoder (celda 12). Corpus: nuestros relatos mas
    el vocabulario tecnico del dominio."""
    if cargar_tokenizer is None:
        from transformers import AutoTokenizer
        cargar_tokenizer = AutoTokenizer.from_pretrained
    corpus = [e["relato"] for e in schema.cargar()] + TERMINOS_FERTILIDAD
    palabras = sum(len(t.split()) for t in corpus)
    filas = medir_fertilidad(corpus, CANDIDATOS_FERTILIDAD, cargar_tokenizer)
    print(f"Corpus de medicion: {len(corpus)} textos, {palabras} palabras\n")
    print(f"{'modelo':<40}{'params':>8}{'vocab':>9}{'tok/palabra':>13}{'genera':>8}")
    print("-" * 80)
    for r in filas:
        f = f"{r['fertilidad']:.3f}" if r["fertilidad"] else "error"
        v = f"{r['vocab']:,}" if r.get("vocab") else "-"
        print(f"{r['modelo']:<40}{r['params']:>8}{v:>9}{f:>13}{r.get('genera', '-'):>8}")
    print()
    print("BETO puede tener fertilidad competitiva en espanol y queda descartado")
    print("igual: no genera, y por el Nivel 1 el sistema necesita generar.")
    ctx.c.guardar_json("fertilidad_tokenizadores", filas)
    return filas


# --------------------------------------------------------------------------
# Modelo base (celda 13) y dataset v3.5.0 (celdas 15-16)
# --------------------------------------------------------------------------
def cargar_modelo(ctx: Contexto) -> Contexto:
    """Siembra y carga Qwen2.5-7B en bf16 (celda 13).

    SEMBRAR NO BASTA, Y LA CORRIDA ANTERIOR LO MIDIO. `random`/`numpy`/`torch`
    fijan de donde salen los numeros aleatorios, no el ORDEN en que la GPU los
    suma: cuBLAS elige su reduccion segun el workspace y cuDNN autotunea, asi
    que la misma operacion en bf16 puede acumular en dos ordenes y dar otro
    numero; sobre 7B eso llega a cambiar un token. `corridas.sembrar()` anade
    los interruptores de kernel y DEVUELVE lo que consiguio, que se registra
    para leer `estabilidad` sabiendo si el determinismo se pidio de verdad.
    No cubre dos corridas en GPUs distintas.
    """
    import torch
    from amparo.ejecucion import corridas
    determinismo = corridas.sembrar(corridas.SEMILLA)
    ctx.c.registrar("determinismo", determinismo)
    for k, v in determinismo.items():
        if k != "lectura":
            print(f"  {k:<32}{v}")
    print()
    print(determinismo["lectura"])
    print()
    ctx.model, ctx.tokenizer = generacion.cargar_modelo(MODEL_ID, entrenable=True)
    # Tokens de parada explicitos (ver `generacion.ids_parada`): en 4 de 46
    # casos el modelo abria un turno '<|im_start|>user' tras el cuarto campo.
    ctx.parada = generacion.ids_parada(ctx.tokenizer)
    print(f"{MODEL_ID} · {sum(p.numel() for p in ctx.model.parameters())/1e9:.1f}B parametros")
    print(f"VRAM ocupada: {torch.cuda.memory_allocated()/1e9:.1f} GB")
    print("tokens de parada:", ctx.parada)
    return ctx


def cargar_datos(ctx: Contexto) -> Contexto:
    """Splits y eval set, validados y sin fuga entre ellos (celda 15)."""
    ctx.train_raw = schema.cargar("train")
    ctx.val_raw = schema.cargar("validation")
    ctx.eval_raw = schema.cargar(archivo="eval_set_v3.json")
    comprobar_splits(ctx.train_raw, ctx.val_raw, ctx.eval_raw)
    train_val = ctx.train_raw + ctx.val_raw
    print(f"train {len(ctx.train_raw)} · validation {len(ctx.val_raw)} · eval {len(ctx.eval_raw)}")
    print()
    print(f"{'mecanismo':<24}{'train':>7}{'val':>6}")
    print("-" * 37)
    for m, n in collections.Counter(str(e["mecanismo"]) for e in train_val).most_common():
        t = sum(1 for e in ctx.train_raw if str(e["mecanismo"]) == m)
        print(f"{m:<24}{t:>7}{n - t:>6}")
    print()
    print("fuentes:", dict(collections.Counter(e.get("tipo_fuente", "?") for e in train_val)))
    print("verificados por el motor de reglas:",
          sum(e.get("verificado_con_reglas", False) for e in train_val))
    real = next((e for e in train_val if e.get("tipo_fuente") == "real"), None)
    if real:
        print("\n--- un caso de fuente real ---")
        print(real["procedencia"][:260])
    ab = next((e for e in train_val if e.get("tipo") == "abstencion"), None)
    if ab:
        print("\n--- un caso de abstencion ---")
        print(schema.render_salida(ab))
    return ctx


def comprobar_splits(train: list[dict], val: list[dict], eval_set: list[dict]) -> None:
    """Esquema valido y NINGUNA fuga del eval set al entrenamiento, ni por id
    ni por relato repetido."""
    errores = schema.validar(train + val + eval_set)
    assert not errores, errores[:10]
    ids = {e["id"] for e in train} | {e["id"] for e in val}
    assert not (ids & {e["id"] for e in eval_set}), "FUGA: el eval set toca el entrenamiento"
    relatos = {e["relato"] for e in train + val}
    assert not (relatos & {e["relato"] for e in eval_set}), "FUGA: relato repetido"


def preparar_dataset(ctx: Contexto) -> Contexto:
    """Tokeniza train/validation con el prompt enmascarado (celda 16).

    `MAX_LEN` se MIDE sobre train+validation sin truncar (ver
    `datos.medir_max_len`) y `datos.comprobar_truncados` para la corrida si
    algo toca el techo: lo que se truncaria es la RESPUESTA que el modelo
    tiene que aprender.
    """
    ctx.max_len, crudos = datos.medir_max_len(ctx.train_raw + ctx.val_raw, ctx.tokenizer)
    print(f"MAX_LEN medido: {ctx.max_len} tokens "
          f"(el ejemplo mas largo pide {max(crudos)}, la media es "
          f"{sum(crudos)/len(crudos):.0f})")
    ctx.ds_train, ctx.ds_val = datos.construir_datasets(ctx.train_raw, ctx.val_raw,
                                                        ctx.tokenizer, ctx.max_len)
    datos.comprobar_truncados(ctx.ds_train, ctx.tokenizer, ctx.max_len, ctx.train_raw[0])
    print(f"train {len(ctx.ds_train)} · val {len(ctx.ds_val)} listos")
    return ctx


# --------------------------------------------------------------------------
# 4 · Baselines: el modelo sin ajustar
# --------------------------------------------------------------------------
def _generar_y_puntuar(ctx: Contexto, clave: str, etiqueta: str, construir_mensajes,
                       lote: int) -> dict:
    """Genera sobre el eval set, mide la degeneracion SOBRE LO CRUDO y despues
    recorta. En ese orden: recortar primero dejaria el contador en cero y el
    defecto invisible."""
    crudo = generacion.generar_lote(ctx.model, ctx.tokenizer, ctx.eval_raw, construir_mensajes,
                                    parada=ctx.parada, lote=lote)
    ctx.deg[clave] = metricas.degeneracion(crudo, ctx.eval_raw)
    ctx.salidas[clave] = [schema.recortar_al_bloque(s)[0] for s in crudo]
    print(f"degeneracion ({etiqueta}): {ctx.deg[clave]['n']}/{ctx.deg[clave]['de']} "
          "salidas con cola")
    for caso in ctx.deg[clave]["casos"]:
        print(f"   {caso['id']} ({caso['categoria']}): {caso['chars_cola']} chars de cola")
    ctx.sc[clave] = metricas.scorecard(ctx.salidas[clave], ctx.eval_raw, etiqueta)
    metricas.imprimir(ctx.sc[clave])
    return ctx.sc[clave]


def baseline(ctx: Contexto) -> dict:
    """El modelo base con la instruccion sola (celda 18)."""
    print("Generando baseline sobre el eval set...")
    sc = _generar_y_puntuar(ctx, "base", "base (sin fine-tuning)", datos.mensajes, lote=8)
    print("\n--- muestra cruda del modelo base ---")
    print(ctx.salidas["base"][0][:400])
    return sc


def legibles(salidas: list[str]) -> int:
    """Cuantas salidas tienen un mecanismo que el parser puede leer."""
    return sum(1 for s in salidas if schema.parse_salida(s).get("mecanismo"))


def baseline_few_shot(ctx: Contexto) -> dict:
    """4.1 · El baseline de FORMATO: al base se le DEMUESTRA el esquema (celda 20).

    EL BRAZO VA AQUI Y NO DESPUES: a partir de `aplicar_lora`, `model` es el
    modelo ADAPTADO y un brazo "base" generado mas abajo mediria el afinado con
    otro prompt, con un numero plausible y falso. Las tres demostraciones salen
    del TRAIN (nunca del eval; lo fija la prueba 74). El lote baja a 4 porque
    el prompt es unas tres veces mas largo; no cambia la salida, solo el tiempo.

    La descomposicion: base -> base+few-shot es cuanto del hueco era FORMATO;
    base+few-shot -> afinado es cuanto es RAZONAMIENTO, ya sin la excusa.
    """
    train = json.loads((DATA / "dataset.json").read_text(encoding="utf-8"))["ejemplos"]
    ctx.demos = schema.demostraciones_few_shot(train, {e["id"] for e in ctx.eval_raw})
    print("demostraciones del few-shot (del train, nunca del eval):")
    for d in ctx.demos:
        print(f"   {d['id']:<6} {d['mecanismo']}")
    print("\nGenerando el baseline con few-shot de formato...")
    sc = _generar_y_puntuar(
        ctx, "base_few_shot", "base + few-shot de formato",
        lambda e: schema.mensajes_few_shot(datos.SISTEMA, e, ctx.demos), lote=4)
    print()
    print("=" * 72)
    print("  DE QUE ERA EL HUECO · tres brazos, mismo modelo base en dos de ellos")
    print("=" * 72)
    print(f"  {'brazo':<26}{'mec. legible':>14}{'acierto jur.':>14}")
    for nombre, clave in (("base (solo instruccion)", "base"),
                          ("base + few-shot", "base_few_shot"),
                          ("afinado (LoRA)", None)):
        if clave is None or clave not in ctx.salidas:
            print(f"  {nombre:<26}{'--- se mide en la seccion 6 ---':>28}")
            continue
        sal = ctx.salidas[clave]
        print(f"  {nombre:<26}{legibles(sal)}/{len(sal):<13}"
              f"{ctx.sc[clave]['acierto_juridico']:>14.4f}")
    print()
    print("  Lo que esto NO dice: que el few-shot sea el techo del base. Es UN")
    print("  prompt con tres demostraciones, no una busqueda de prompts.")
    print("=" * 72)
    return sc


# --------------------------------------------------------------------------
# 5 · Fine-tuning con LoRA (celdas 22-25)
# --------------------------------------------------------------------------
def aplicar_lora(ctx: Contexto) -> Contexto:
    ctx.model, ctx.lora_config = entrenamiento.aplicar_lora(ctx.model)
    return ctx


def configurar_entrenamiento(ctx: Contexto) -> dict:
    """Trainer, receta filtrada contra la version instalada y el artefacto
    `hiperparametros` con lo EJECUTADO (celda 23)."""
    from amparo.ejecucion import corridas
    hp = entrenamiento.hiperparametros(corridas.SEMILLA)
    ctx.trainer, ctx.hp, omitidos, traducidos, parada = entrenamiento.crear_trainer(
        ctx.model, ctx.ds_train, ctx.ds_val, datos.collate_para(ctx.tokenizer), hp)
    registro = entrenamiento.registro_hiperparametros(
        modelo_base=MODEL_ID, semilla=corridas.SEMILLA, max_len=ctx.max_len,
        lora_config=ctx.lora_config, hp=ctx.hp, omitidos=omitidos, traducidos=traducidos,
        parada=parada, splits={"train": len(ctx.ds_train), "validation": len(ctx.ds_val),
                               "eval": len(ctx.eval_raw)})
    ctx.c.guardar_json("hiperparametros", registro)
    print(json.dumps(registro, ensure_ascii=False, indent=2))
    return registro


def entrenar(ctx: Contexto) -> dict:
    """Entrena, comprueba que lora_B se movio y documenta que epoca gano (celda 24)."""
    hist = ctx.trainer.train()
    ctx.model.config.use_cache = True
    print(f"\nEntrenamiento terminado · train_loss final {hist.training_loss:.4f}")
    entrenamiento.comprobar_lora_b(ctx.model)
    seleccion = entrenamiento.seleccionar_checkpoint(ctx.trainer.state.log_history,
                                                     ctx.hp.get("num_train_epochs"))
    ctx.c.guardar_json("seleccion_checkpoint", seleccion)
    return seleccion


def curva_de_perdida(ctx: Contexto, mostrar: bool = True):
    """`runs/m1/<id>/loss.png` (celda 25)."""
    return entrenamiento.graficar_perdida(ctx.trainer.state.log_history,
                                          ctx.c.dir / "loss.png", mostrar=mostrar)


# --------------------------------------------------------------------------
# 6 · ¿Mejoro? (celdas 27-28)
# --------------------------------------------------------------------------
def evaluar_ajustado(ctx: Contexto) -> dict:
    """El ajustado sobre el eval set, con la misma generacion que el baseline.

    La cola se recorta ANTES de puntuar y antes de guardar, para que no
    contamine las metricas ni lo que M2 le pasa al juez. El recorte no inventa
    el campo que falte: si no escribio Pretension, sigue faltando.
    """
    print("Generando con el modelo ajustado...")
    sc = _generar_y_puntuar(ctx, "finetuned", "fine-tuned LoRA", datos.mensajes, lote=8)
    print("\n--- muestra cruda del modelo ajustado ---")
    print(ctx.salidas["finetuned"][0][:400])
    return sc


def comparar_con_base(ctx: Contexto) -> None:
    """El liston real: si no le gana a 'responde siempre tutela', el
    fine-tuning no aporto nada en ese campo."""
    metricas.comparar(ctx.sc["base"], ctx.sc["finetuned"])
    base_may = ctx.sc["finetuned"]["campos"]["mecanismo"]["baseline_mayoritaria"]
    acc = ctx.sc["finetuned"]["campos"]["mecanismo"]["accuracy"]
    print()
    print(f"acc_mecanismo {acc:.1%} contra una clase mayoritaria de {base_may:.1%} "
          f"(delta {acc - base_may:+.1%})")


def abstencion_validation(ctx: Contexto) -> dict | None:
    """6.1 · Abstencion, en VALIDATION, que trae una de cada familia (celda 30).

    Las dos cifras juntas o ninguna: un sistema que se abstiene siempre saca
    100% en `acierto_abstencion` y una indebida enorme en la otra.
    """
    if not any(e.get("tipo") == "abstencion" for e in ctx.val_raw):
        return None
    sal_val = generacion.generar_lote(ctx.model, ctx.tokenizer, ctx.val_raw, datos.mensajes,
                                      parada=ctx.parada, lote=8)
    ab = metricas.scorecard(sal_val, ctx.val_raw, "fine-tuned · validation")["abstencion"]
    print(f"casos sin respuesta correcta: {ab['n_sin_respuesta_correcta']}")
    print(f"  se abstuvo en      : {ab['acierto_abstencion']:.0%}")
    print(f"  forzo una etiqueta : {ab['forzo_etiqueta']}")
    print(f"  abstencion indebida: {ab['abstenciones_indebidas']}/{ab['n_con_respuesta_correcta']}"
          f" ({ab['abstencion_indebida']:.0%})")
    print("\npor familia (validation trae una de cada una, por eso se puede leer CUAL falla):")
    for familia, callo in sorted(ab.get("por_familia", {}).items()):
        print(f"  {'se abstuvo' if callo else 'FORZO     '}  {familia}")
    for caso in ab.get("indebidas_en", []):
        print(f"  se abstuvo donde SI habia mecanismo: {caso['id']} "
              f"({caso['categoria']}, gold {caso['mecanismo_gold']})")
    ctx.c.guardar_json("abstencion_validation", ab)
    return ab


# --------------------------------------------------------------------------
# 6.3 · Quien decide el mecanismo: el base extrae, las reglas deciden (celda 32)
# --------------------------------------------------------------------------
_LECTURA_EXTRACTOR = (
    "El adaptador NO colapsa sobre el bloque de cinco lineas: "
    "emite JSON bien formado, con las doce claves booleanas "
    "correctas, que abre y cierra y no esta truncado. Lo que "
    "falla es que los valores de CADENA van sin comillas "
    "(`\"derecho\": salud`), y `json.loads` muere en esa linea. "
    "Mirar `muestra` y `cierran` antes de creerle a esta frase. "
    "Por eso la extraccion del brazo hibrido se hace con "
    "`model.disable_adapter()` --- con el adaptador apagado el "
    "mismo extractor falla 1 de 69 --- y por eso el brazo ya no "
    "se llama 'el mismo modelo con otro decisor'.")


def resumen_sonda(fallos: list[dict], casos: int) -> dict:
    """`cierra` y `chars` SON EL DATO QUE ZANJA POR QUE NO PARSEA: con
    `cierra=False` la causa es truncamiento por `max_new`; con `cierra=True`
    es malformacion. La `muestra` se guarda larga porque la respuesta esta al
    final."""
    f0 = fallos[0] if fallos else None
    return {
        "casos": casos, "sin_json": len(fallos),
        "muestra": f0["salida"][:700] if f0 else None,
        "chars": f0["chars"] if f0 else None,
        "empieza": f0["empieza"] if f0 else None,
        "cierra": f0["cierra"] if f0 else None,
        "cierran": sum(1 for f in fallos if f["cierra"]) if fallos else None,
        "chars_max": max(f["chars"] for f in fallos) if fallos else None,
    }


def brazo_hibrido(ctx: Contexto) -> dict:
    """Sonda del adaptador como extractor y brazo `base extrae + reglas deciden`.

    FASE 1 · SONDA. La primera version del brazo extraia con el adaptador y en
    m1/20261016T174233Z dio 42.9% --- exactamente la base mayoritaria --- porque
    `_json_de` devolvia `{}` en 62 de 63 casos y el default pro homine mandaba
    todo a tutela. Se mide con pocos casos porque el resultado es categorico.

    FASE 2 · EL BRAZO, con el adaptador APAGADO (`con_adaptador=False`): mismos
    pesos base, mismo prompt, y la pregunta pasa a ser si el trabajo lo hace el
    adaptador o el motor de reglas. Va sin RAG para que lo que lo separe del
    brazo 4 de M3 sea solo la recuperacion. Lote 1 a proposito, para no
    falsear la latencia.

    LA GUARDA: sin ella, 62 de 63 fallos de parseo se publicaron como un 42.9%
    con `alucinacion_normativa` 0.0 y `adherencia_estructural` 1.0, ciertas y
    vacias. Por encima del 10% de fallos el brazo mide el default, no al
    extractor. Y el veredicto de los intervalos MIRA EL SIGNO.
    """
    from amparo.sistemas import sistema
    generar = generacion.generador_hf(ctx.model, ctx.tokenizer, parada=ctx.parada, max_new=320)
    generar_base = generacion.generador_hf(ctx.model, ctx.tokenizer, parada=ctx.parada,
                                           max_new=320, con_adaptador=False)
    eval_raw = ctx.eval_raw

    print(f"SONDA - el modelo AJUSTADO como extractor ({SONDA} casos)")
    fallos_sonda: list[dict] = []
    for e in eval_raw[:SONDA]:
        sistema.extraer_hechos(generar, e["relato"], fallos_sonda)
    print(f"  salidas sin JSON utilizable: {len(fallos_sonda)}/{SONDA}")
    if fallos_sonda:
        print("  lo que emitio en vez de JSON:")
        print("    " + fallos_sonda[0]["salida"][:140].replace("\n", " | "))
    else:
        print("  El ajustado SI emite JSON. Eso contradice la corrida que motivo")
        print("  este cambio: revisa si cambio el prompt, el formato o las epocas.")
    ctx.extractor = {"sonda_ajustado": resumen_sonda(fallos_sonda, SONDA),
                     "lectura": _LECTURA_EXTRACTOR}

    print(f"\nBRAZO - extraccion con el adaptador APAGADO ({len(eval_raw)} casos)")
    hib = sistema.SistemaHibrido(generar_base, etiqueta="base extrae + reglas deciden")
    sal_hib = []
    for i, e in enumerate(eval_raw, 1):
        sal_hib.append(hib(e["relato"]))
        # CORTE TEMPRANO: el assert de abajo solo salta al acabar, y a lote 1
        # son ~13 minutos para enterarse de que el extractor es mudo.
        if i == CORTE and len(hib.fallos_extraccion) > CORTE // 2:
            m = hib.fallos_extraccion[0]["salida"][:160]
            raise AssertionError(
                f"{len(hib.fallos_extraccion)}/{CORTE} sin JSON ya en los primeros "
                f"casos: el modelo BASE tampoco emite JSON con este prompt, asi "
                f"que este brazo iba a dar la base mayoritaria otra vez. Se corta "
                f"aqui en vez de gastar los ~13 minutos que faltan. "
                f"Emitio: " + " | ".join(m.splitlines()))
        print(f"  {i}/{len(eval_raw)}", end="\r")
    print()
    n_fallos = len(hib.fallos_extraccion)
    ctx.extractor["brazo_base"] = {"casos": len(eval_raw), "sin_json": n_fallos}
    print(f"  fallos de extraccion: {n_fallos}/{len(eval_raw)}")
    assert n_fallos <= UMBRAL_FALLOS_EXTRACCION * len(eval_raw), (
        f"{n_fallos} de {len(eval_raw)} salidas sin JSON utilizable.\n"
        "Los doce booleanos quedan en False por defecto, el motor no encuentra\n"
        "ninguna causal y falla a tutela: este brazo estaria midiendo el default\n"
        "pro homine y no al extractor. Lo que se emitio en vez de JSON:\n  "
        + "\n  ".join(f["salida"][:110].replace("\n", " | ")
                      for f in hib.fallos_extraccion[:3]))

    ctx.salidas["hibrido"] = sal_hib
    sc_hib = metricas.scorecard(sal_hib, eval_raw, "base extrae + reglas deciden")
    ctx.sc["hibrido"] = sc_hib
    metricas.imprimir(sc_hib)
    _imprimir_quien_decide(ctx.sc["finetuned"], sc_hib)

    ctx.c.guardar_json("scorecard_hibrido", sc_hib)
    ctx.c.guardar_json("trazas_hibrido", hib.trazas)
    ctx.c.guardar_json("extractor", ctx.extractor)
    return sc_hib


def veredicto_adversarial(a: dict, b: dict) -> str:
    """ROADMAP #14 con signo: 'solapan', 'gana_reglas' o 'gana_ajustado'.

    La version anterior afirmaba "la conclusion es arquitectonica" en cuanto
    los intervalos no se solapaban, sin mirar cual era el mayor: con el brazo
    roto al 16.7% contra 88.9% imprimia una vindicacion junto a un error.
    """
    if metricas.ic_se_solapan(a, b):
        return "solapan"
    return "gana_reglas" if b["punto"] > a["punto"] else "gana_ajustado"


def _imprimir_quien_decide(sc_ft: dict, sc_hib: dict) -> None:
    print()
    print("=" * 62)
    print("  ROADMAP #15 - quien decide el mecanismo")
    print("=" * 62)
    print(f"  {'sistema':<30}{'global':>9}{'gold':>9}{'advers.':>9}")
    print("  " + "-" * 57)
    for etq, sc in (("ajustado solo (decide el LLM)", sc_ft),
                    ("base extrae + reglas deciden", sc_hib)):
        pt = sc.get("por_tipo", {})
        print(f"  {etq:<30}{sc['acierto_juridico']:>9.1%}"
              f"{pt.get('gold', {}).get('acierto_juridico', 0):>9.1%}"
              f"{pt.get('adversarial', {}).get('acierto_juridico', 0):>9.1%}")
    a = sc_ft["ic"]["por_tipo"].get("adversarial")
    b = sc_hib["ic"]["por_tipo"].get("adversarial")
    if a and b:
        print("\n  adversarial, con intervalo al 95%:")
        print(f"    ajustado solo        {a['punto']:.3f}  [{a['ic_bajo']:.3f}, {a['ic_alto']:.3f}]")
        print(f"    base + reglas        {b['punto']:.3f}  [{b['ic_bajo']:.3f}, {b['ic_alto']:.3f}]")
        print()
        v = veredicto_adversarial(a, b)
        if v == "solapan":
            print("    Los intervalos SE SOLAPAN: con n=18 la diferencia no se")
            print("    sostiene en NINGUNA direccion. Hace falta un estrato")
            print("    adversarial mas grande.")
        elif v == "gana_reglas":
            print("    NO se solapan y gana EL BRAZO CON REGLAS: quien decide el")
            print("    mecanismo importa, y la conclusion es arquitectonica, no de escala.")
        else:
            print("    NO se solapan y gana EL AJUSTADO SOLO. Antes de leerlo como")
            print("    resultado, comprueba que los fallos de extraccion sean 0: un")
            print("    extractor mudo manda el brazo entero a 'tutela'.")
    # CERO AQUI NO ES UNA BUENA NOTICIA POR SI SOLO: el brazo roto tambien daba
    # 0.0%. Solo significa algo junto a los fallos de extraccion y a la
    # pertinencia de las citas, que distingue 'no invento' de 'acerto'.
    alu = sc_hib["alucinacion_normativa"]["tasa_alucinacion"]
    print()
    print(f"  alucinacion normativa: {alu:.1%}", end="")
    print("  (cero por construccion: el fundamento lo pone la regla)"
          if alu == 0 else "  <-- DEFECTO: deberia ser 0, revisa el armado del campo")
    print(f"  pertinencia de esas citas: "
          f"{sc_hib['pertinencia_citas']['precision_citas']:.1%}")


# --------------------------------------------------------------------------
# 7 · La capa de redaccion (celda 34)
# --------------------------------------------------------------------------
def redaccion(ctx: Contexto, generar=None) -> dict:
    """Del bloque al lenguaje natural, sin anadir normas ni hechos.

    El generador es Groq, no el adaptador: el adaptador DECIDE y no sabe
    redactar. Sin clave la seccion se salta y queda registrada como no medida,
    que NO es un cero. Se redacta sobre las predicciones del AJUSTADO, que es
    lo que un usuario recibiria. LAS DOS COBERTURAS (via y procedencia) SE
    COMPRUEBAN: en 20261018T074101Z la consola afirmo que todos los textos
    decian la procedencia con un 0.9855 en el artefacto.
    """
    from amparo.finetuning import redaccion as red
    if generar is None and os.environ.get("GROQ_API_KEY"):
        try:
            import groq
            from amparo.sistemas import sistema
            generar = sistema.generador_groq(groq.Groq(api_key=os.environ["GROQ_API_KEY"]),
                                             cache_path=ctx.c.ruta_cache("redaccion.json"))
        except Exception as ex:                              # noqa: BLE001
            print(f"no pude crear el generador de redaccion: {str(ex)[:90]}")

    if generar is None:
        print("sin GROQ_API_KEY: la capa de redaccion no se mide en esta corrida.")
        print("Eso NO es un cero: es que no se ejecuto, y asi queda registrado.")
        medida = {"n": 0, "concluyente": False, "motivo": "sin GROQ_API_KEY en esta corrida"}
    else:
        resultados, fallos = [], []
        for i, (e, sal) in enumerate(zip(ctx.eval_raw, ctx.salidas["finetuned"]), 1):
            bloque = schema.parse_salida(sal)
            # La condicion que cambiaria la via sale del motor cuando el gold
            # trae hechos codificados; si no, no se dice nada.
            pivota = e.get("etiqueta_pivota_en") or None
            try:
                r = red.redactar(generar, bloque, pivota, registro="ciudadano", estricto=False)
                resultados.append(r)
                if not r["verificacion"]["valido"]:
                    fallos.append((e["id"], r["verificacion"]))
            except Exception as ex:                          # noqa: BLE001
                fallos.append((e["id"], {"error": str(ex)[:120]}))
            print(f"  {i}/{len(ctx.eval_raw)}", end="\r")
        print()
        medida = red.medir(resultados)
        _imprimir_redaccion(medida, resultados)
    ctx.redaccion = medida
    ctx.c.guardar_json("redaccion", medida)
    return medida


def _imprimir_redaccion(m: dict, resultados: list[dict]) -> None:
    print(f"{'textos redactados':<28}{m['n']}")
    print(f"{'con normas inventadas':<28}{m['textos_con_citas_intrusas']}  "
          f"(tasa {m['tasa_citas_intrusas']:.1%})")
    print(f"{'dicen el mecanismo':<28}{m['dicen_el_mecanismo']:.1%}")
    print(f"{'dicen la procedencia':<28}{m['dicen_la_procedencia']:.1%}")
    print(f"{'palabras de media':<28}{m['palabras_media']}")
    print()
    if m["textos_con_citas_intrusas"]:
        print("HAY NORMAS INVENTADAS EN LA REDACCION. La cita que ve el lector ya")
        print(f"no es la que se midio. Ejemplos: {m['ejemplos_intrusas']}")
    elif m["dicen_el_mecanismo"] < 1.0 or m["dicen_la_procedencia"] < 1.0:
        falta = []
        if m["dicen_el_mecanismo"] < 1.0:
            falta.append(f"la VIA en {1 - m['dicen_el_mecanismo']:.1%}")
        if m["dicen_la_procedencia"] < 1.0:
            falta.append(f"la PROCEDENCIA en {1 - m['dicen_la_procedencia']:.1%}")
        print(f"Hay texto(s) que callan {' y '.join(falta)} de los casos.")
        print("Callar la via o la procedencia deja un error del triaje indetectable.")
    else:
        print("La capa respeta el bloque: 0 normas introducidas, y todos los")
        print("textos dicen la via y la procedencia.")
    print()
    print("--- una muestra, registro ciudadano ---")
    print(resultados[0]["texto"] if resultados else "(sin textos)")


# --------------------------------------------------------------------------
# 8 · Artefactos (celda 36)
# --------------------------------------------------------------------------
def predicciones(eval_raw: list[dict], sal_base: list[str], sal_ft: list[str]) -> list[dict]:
    """Lo que consumen M2 y M3 (`results/m1_predicciones.json`)."""
    return [{"id": e["id"], "tipo": e.get("tipo"), "categoria": e["categoria"],
             "gold_mecanismo": e["mecanismo"], "base": sb, "finetuned": sf}
            for e, sb, sf in zip(eval_raw, sal_base, sal_ft)]


def publicar_artefactos(ctx: Contexto) -> dict:
    """Guarda lo que falta, publica en `results/` y versiona el adaptador.

    Lo que se guarda en la carpeta de la corrida NO esta entregado hasta que
    se copia a `results/` con su sello: si uno falta, `verificar_entrega.py`
    lo cuenta como ausente. M2 y M3 leen de `results/`, que es estable, no de
    la carpeta de una corrida concreta.
    """
    c = ctx.c
    c.guardar_json("scorecard_base", ctx.sc["base"])
    # El brazo de formato es una de las tres patas de la descomposicion: sin
    # artefacto, la cifra vive en la consola y el reporte no la puede citar.
    c.guardar_json("scorecard_base_few_shot", ctx.sc["base_few_shot"])
    c.guardar_json("scorecard_finetuned", ctx.sc["finetuned"])
    c.guardar_json("degeneracion", {"base": ctx.deg["base"],
                                    "base_few_shot": ctx.deg["base_few_shot"],
                                    "finetuned": ctx.deg["finetuned"]})
    c.guardar_json("predicciones", predicciones(ctx.eval_raw, ctx.salidas["base"],
                                                ctx.salidas["finetuned"]))

    # La evidencia del tokenizador sobre el dominio sostiene la eleccion del modelo base.
    c.publicar("fertilidad_tokenizadores", "results/m1_fertilidad_tokenizadores.json")
    c.publicar("cobertura_clasificador", "results/m1_cobertura_clasificador.json")
    c.publicar("predicciones", "results/m1_predicciones.json")
    c.publicar("scorecard_base", "results/m1_scorecard_base.json")
    c.publicar("scorecard_base_few_shot", "results/m1_scorecard_base_few_shot.json")
    c.publicar("scorecard_finetuned", "results/m1_scorecard_finetuned.json")
    c.publicar("hiperparametros", "results/m1_hiperparametros.json")
    # ROADMAP #16: la curva de `eval_loss` y la epoca que gano permiten
    # DEFENDER la eleccion del checkpoint en vez de afirmarla.
    c.publicar("seleccion_checkpoint", "results/m1_seleccion_checkpoint.json")
    # La evidencia del ROADMAP #15 se quedaba en runs/ y `verificar_entrega.py`
    # no la echaba de menos porque `arranque.ORDEN` no la declaraba.
    c.publicar("scorecard_hibrido", "results/m1_scorecard_hibrido.json")
    # Que el adaptador no pueda extraer JSON es un hallazgo, no un diagnostico.
    c.publicar("extractor", "results/m1_extractor.json")
    # Una capa de presentacion puede degradar sin que nadie lo note: se lee
    # bien y dice otra cosa. Sin artefacto no se veria entre corridas.
    c.publicar("redaccion", "results/m1_redaccion.json")
    # La degeneracion es un hallazgo: un 0 de 69 fue suerte, no cura, y solo
    # se sabe comparando corridas.
    c.publicar("degeneracion", "results/m1_degeneracion.json")

    ficha = entrenamiento.guardar_adaptador(ctx.model, ctx.tokenizer, MODELS, c.id, RAIZ)
    c.meta["adaptador"] = ficha
    c._escribir_meta()
    return ficha


# --------------------------------------------------------------------------
# 8.1 · Estabilidad entre corridas (celda 38)
# --------------------------------------------------------------------------
ARTEFACTOS_ESTABILIDAD = ("scorecard_base", "scorecard_base_few_shot", "scorecard_finetuned",
                          "predicciones", "abstencion_validation")


def comparar_con_previa(c, previa, comparar) -> dict:
    """La comparacion con la corrida previa, con las tres causas posibles de
    un `identicas: False` separadas (hardware, previa sin flags, residual).

    `scorecard_base_few_shot` entra porque aisla el origen de la varianza: no
    pasa por el entrenamiento. `identicas` ERA False CUANDO NO HABIA NADA QUE
    COMPARAR (m1/20261017T022209Z): ahora es None y `concluyente` lo dice.
    """
    meta_previa = json.loads((previa / "corrida.json").read_text(encoding="utf-8"))
    datos_previa = (meta_previa.get("datos") or {}).get("dataset.json")
    datos_ahora = c.meta["datos"]["dataset.json"]
    cod_previa = (meta_previa.get("codigo") or {}).get("_conjunto")
    cod_ahora = (c.meta.get("codigo") or {}).get("_conjunto")
    est = {"corrida_previa": previa.name, "corrida_actual": c.id,
           "mismos_datos": datos_previa == datos_ahora,
           "mismo_codigo": cod_previa is not None and cod_previa == cod_ahora,
           "codigo_previa": cod_previa, "codigo_actual": cod_ahora,
           "determinismo_previa": meta_previa.get("determinismo"),
           "determinismo_actual": c.meta.get("determinismo"),
           "mismo_hardware": ((meta_previa.get("hardware") or {}).get("gpu")
                              == (c.meta.get("hardware") or {}).get("gpu")),
           "artefactos": {}}
    print(f"corrida previa : {previa.name} · dataset {datos_previa} · codigo {cod_previa}")
    print(f"corrida actual : {c.id} · dataset {datos_ahora} · codigo {cod_ahora}")
    print(f"mismos datos   : {est['mismos_datos']}   mismo codigo: {est['mismo_codigo']}")
    for art in ARTEFACTOS_ESTABILIDAD:
        try:
            est["artefactos"][art] = comparar(previa, c.dir, art)
        except FileNotFoundError:
            print(f"estabilidad · {art}: no esta en la corrida previa, se omite")
    comparados = est["artefactos"]
    iguales = [a for a, v in comparados.items() if v["identicas"]]
    est["concluyente"] = bool(comparados)
    est["identicas"] = (len(iguales) == len(comparados)) if comparados else None
    if not comparados:
        print("artefactos comparados: 0 --- `identicas` queda en null: no hay comparacion.")
    else:
        print(f"artefactos identicos: {len(iguales)}/{len(comparados)}")
    if est["mismos_datos"] and est["mismo_codigo"] and est["identicas"] is False:
        if not est["mismo_hardware"]:
            print("Mismos datos y codigo pero OTRA GPU: los flags fijan el algoritmo,")
            print("no el hardware. Esta diferencia no prueba no-determinismo.")
        elif not est["determinismo_previa"]:
            print("La corrida previa NO registra `determinismo` (anterior a los flags):")
            print("hacen falta DOS corridas con `determinismo` registrado.")
        else:
            print("Mismo hardware y flags en las dos: no-determinismo residual,")
            print("esperable con `warn_only=True`.")
    elif est["mismos_datos"] and not est["mismo_codigo"] and not est["identicas"]:
        print("Mismos datos pero el codigo cambio: la causa es el codigo, no el hardware.")
    return est


def estabilidad(ctx: Contexto) -> dict | None:
    """Compara con la corrida previa de m1 (buscada sola, sin ids a mano).

    Se publica AQUI y no en `publicar_artefactos`: ahi el artefacto todavia no
    existe, y publicarlo antes de generarlo corto la celda a mitad dejando el
    adaptador sin guardar.
    """
    from amparo.ejecucion import corridas
    c = ctx.c
    carpeta = corridas.RAIZ / "runs" / "m1"
    previas = sorted(p for p in carpeta.iterdir()
                     if p.is_dir() and p.name != c.id and (p / "corrida.json").exists()) \
        if carpeta.is_dir() else []
    if not previas:
        print("primera corrida de m1: todavia no hay con que comparar")
        ctx.estabilidad = None
        return None
    ctx.estabilidad = comparar_con_previa(c, previas[-1], corridas.comparar)
    c.guardar_json("estabilidad", ctx.estabilidad)
    c.publicar("estabilidad", "results/m1_estabilidad.json")
    return ctx.estabilidad


def notas_de_cierre(sc_ft: dict, deg_ft: dict, est: dict | None) -> list[str]:
    notas = [
        f"acc_mecanismo {sc_ft['campos']['mecanismo']['accuracy']:.4f} contra "
        f"mayoritaria {sc_ft['campos']['mecanismo']['baseline_mayoritaria']:.4f}",
        f"acierto juridico {sc_ft['acierto_juridico']:.4f} "
        f"(gold {sc_ft['por_tipo'].get('gold', {}).get('acierto_juridico', 0):.4f}, "
        f"adversarial {sc_ft['por_tipo'].get('adversarial', {}).get('acierto_juridico', 0):.4f})",
        f"alucinacion {sc_ft['alucinacion_normativa']['tasa_alucinacion']:.4f} en fundamento, "
        f"{sc_ft['alucinacion_normativa']['tasa_alucinacion_salida']:.4f} en toda la salida",
        f"degeneracion {deg_ft['n']}/{deg_ft['de']} salidas con cola recortada",
    ]
    if est:
        ident = ("no concluyente (0 artefactos comparables)" if not est.get("concluyente")
                 else est.get("identicas"))
        notas.append(f"estabilidad contra {est['corrida_previa']}: identicas={ident} "
                     f"(mismos datos: {est['mismos_datos']}, "
                     f"mismo codigo: {est['mismo_codigo']})")
    return notas


def cerrar(ctx: Contexto) -> dict:
    return ctx.c.cerrar(valida=True, notas=notas_de_cierre(ctx.sc["finetuned"],
                                                           ctx.deg["finetuned"],
                                                           ctx.estabilidad))


# --------------------------------------------------------------------------
ETAPAS = (validar_extractor, cobertura_clasificador, fertilidad_tokenizadores, cargar_modelo,
          cargar_datos, preparar_dataset, baseline, baseline_few_shot, aplicar_lora,
          configurar_entrenamiento, entrenar, curva_de_perdida, evaluar_ajustado,
          comparar_con_base, abstencion_validation, brazo_hibrido, redaccion,
          publicar_artefactos, estabilidad, cerrar)


def correr(ctx: Contexto | None = None) -> Contexto:
    """M1 de punta a punta, en el orden del notebook."""
    ctx = ctx or preparar()
    for etapa in ETAPAS:
        print(f"\n===== {etapa.__name__} =====")
        etapa(ctx)
    return ctx


if __name__ == "__main__":
    correr()
