"""M4 · El sistema ya ve: el pipeline multimodal, etapa por etapa.

Antes vivia en m4/pipeline/M4_pipeline.ipynb; el notebook ahora solo llama a
estas funciones. Patron input: la foto de un documento -> Qwen2-VL-2B extrae
hechos en JSON -> se suman al relato -> el M3 real (brazo `4 · agente +
reglas`) decide el mecanismo. M3 no se reescribe: `ver()` es un traductor en
la puerta.

Etapas (celdas del notebook original entre parentesis):

    preparar            (3-5)   raiz, rama y commit, clave de Groq
    cargar_imagenes     (7)     patron, pregunta del usuario, 3 documentos de T3
    cargar_modelo       (9)     Qwen2-VL-2B y `preguntar`/`ver`
    probar_ver          (12)    ver() sola sobre 3 imagenes, con latencia
    enchufar_m3         (14)    el M3 real y un ejemplo de punta a punta
    validar_eval_set    (17)    casos_m4.csv pasa `validar_casos`
    miniaturas          (18)    las imagenes del eval set (demo de T3)
    correr_harness      (19)    correr_t6: scorecard, trazas y tabla de delta
    delta_imagen        (20)    misma pregunta con y sin imagen, mismo M3
    resumen             (21)    lo que quedo en disco, caso por caso
    descargar           (22)    bajar las salidas desde Colab

Corre en Colab con GPU T4 y `GROQ_API_KEY` (el brazo 4 razona por la API de
Groq). M4 no es uno de los modulos de `arranque.ORDEN` (m1-m3), asi que no usa
`entorno.preparar()`: solo la clave de Groq de `entorno`.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from amparo.config import RAIZ
from amparo.multimodal import vlm

PATRON = "input"   # M4 de Amparo: el usuario manda una foto de un documento, el VLM la lee
# La pregunta del usuario que necesita ojos (una frase):
PREGUNTA_USUARIO = "Adjunto este documento que me llegó, ¿qué mecanismo constitucional me corresponde?"
# Documentos sinteticos de T3 (Lucas), relativos a la raiz del repo.
IMAGENES = {
    "oficio_planeacion": "m4/eval_set/imagenes/doc02_oficio_planeacion.png",            # plazo de 15 dias
    "notificacion_acueducto": "m4/eval_set/imagenes/doc05_notificacion_acueducto.jpg",  # foto de celular legible
    "notificacion_borrosa": "m4/eval_set/imagenes/doc06_notificacion_borrosa.jpg",      # ADVERSARIAL: sin fecha ni plazo
}
RUTA_CASOS = Path("m4/eval_set/casos_m4.csv")
CARPETA_IMAGENES = Path("m4/eval_set/imagenes")
SALIDAS = ("m4/scorecard_m4.csv", "m4/trazas_m4.json", "m4/delta_m4.json", "m4/delta_imagen_m4.json")


@dataclass
class Contexto:
    """El estado que en el notebook eran variables globales entre celdas."""
    raiz: Path = RAIZ
    imgs: dict = field(default_factory=dict)
    preguntar: object = None
    ver: object = None
    responder_m3: object = None
    agente_m3: object = None
    sistema_m3: str | None = None
    casos: list = field(default_factory=list)
    res: dict | None = None
    delta_imagen: dict | None = None


def _git(raiz: Path, *args) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              cwd=str(raiz)).stdout.strip()
    except OSError:
        return ""


def preparar(*, exigir_clave: bool = True) -> Contexto:
    """Raiz como directorio de trabajo, rama/commit y la clave de Groq.

    La rama y el commit van al README de entrega: de que codigo salio la
    corrida. La clave va antes del enchufe porque el brazo 4 de M3 la
    necesita; sin ella M4 no tiene M3 y la corrida no sirve, asi que para.
    """
    from amparo.ejecucion import entorno
    os.chdir(RAIZ)
    print("repo:", RAIZ, "· rama", _git(RAIZ, "rev-parse", "--abbrev-ref", "HEAD"),
          "· commit", _git(RAIZ, "rev-parse", "--short", "HEAD"))
    if not entorno.cargar_clave_groq(pedir_por_teclado=False) and exigir_clave:
        raise SystemExit("Falta GROQ_API_KEY: panel izquierdo -> icono de la llave -> "
                         "GROQ_API_KEY, con acceso para este notebook.")
    return Contexto(raiz=RAIZ)


def cargar_imagenes(ctx: Contexto, imagenes: dict = IMAGENES, cargar_fn=vlm.cargar) -> Contexto:
    """Tres documentos sinteticos para probar `ver()`; los del eval set entran
    al harness despues."""
    assert PATRON == "input", "Para Amparo el patron es input (ver README_PLAN.md)."
    ctx.imgs = {k: cargar_fn(v) for k, v in imagenes.items()}
    print("patron:", PATRON, "· imagenes:", list(ctx.imgs))
    return ctx


def cargar_modelo(ctx: Contexto) -> Contexto:
    """Carga Qwen2-VL-2B y deja listos `preguntar` (para el juez) y `ver`."""
    modelo, vproc = vlm.cargar_vlm()
    ctx.preguntar = vlm.preguntador(modelo, vproc)
    ctx.ver = vlm.lector(ctx.preguntar)
    return ctx


def probar_ver(ctx: Contexto) -> list[dict]:
    """`ver()` sola, antes de enchufar nada: ¿JSON parseable? ¿cuanto tarda?
    ¿donde alucina un dato que no se ve? Un JSON que no parsea cuenta como
    fallo (regla 2)."""
    filas = []
    for nombre, im in ctx.imgs.items():
        (crudo, js), seg = vlm.cronometrar(ctx.ver, im)
        print(f"[{nombre}] {seg}s")
        print("  JSON :", js)
        if js is None:
            print("  CRUDO:", crudo[:200], "   <- no parseo (cuenta como fallo, regla 2)")
        print()
        filas.append({"imagen": nombre, "segundos": seg, "js": js, "crudo": crudo})
    return filas


def enchufar_m3(ctx: Contexto, **kwargs) -> str:
    """El M3 REAL: brazo `4 · agente + reglas`, armado como en M3_rag.ipynb.

    El chunking y el nombre del brazo salen de los artefactos publicados de M3
    (`results/m3_chunking.json`, `results/m3_scorecard.csv`), no de constantes
    de aqui. `kwargs` va a `enchufe.construir_responder_m3` (cliente, indice y
    transformador se pueden inyectar para probar sin red). Devuelve la
    respuesta de un ejemplo de punta a punta.
    """
    from amparo.multimodal.enchufe import SISTEMA_M3, construir_responder_m3
    kwargs.setdefault("verbose", True)
    ctx.responder_m3, ctx.agente_m3 = construir_responder_m3(**kwargs)
    ctx.sistema_m3 = SISTEMA_M3
    print("M3 enchufado:", SISTEMA_M3)

    ejemplo = vlm.sistema_multimodal(PREGUNTA_USUARIO, next(iter(ctx.imgs.values())),
                                     ver=ctx.ver, responder_m3=ctx.responder_m3)
    print(ejemplo)
    if getattr(ctx.agente_m3, "trazas", None):
        t = ctx.agente_m3.trazas[-1]
        print("\nregla que cerro:", t.get("regla"), "· herramientas:", t.get("herramientas"))
    # Que reranker cargo el indice (jina si Colab trae einops; si no, bge): va al
    # README. M4 no instala einops a proposito, para usar el mismo que M3.
    print("reranker de M3:", getattr(getattr(ctx.agente_m3, "indice", None), "reranker_usado",
                                     "no se cargo en este caso"))
    return ejemplo


def validar_eval_set(ctx: Contexto, ruta_casos: Path = RUTA_CASOS,
                     carpeta_imagenes: Path = CARPETA_IMAGENES) -> list[dict]:
    """`casos_m4.csv` (T4) pasa `validar_casos` antes de gastar GPU."""
    from collections import Counter
    from amparo.multimodal.criterios import cargar_casos, validar_casos
    ctx.casos = cargar_casos(ruta_casos)
    problemas = validar_casos(ctx.casos, carpeta_imagenes=Path(carpeta_imagenes))
    assert not problemas, "casos_m4.csv no pasa la validacion:\n" + "\n".join(problemas)
    print(f"{len(ctx.casos)} casos · validar_casos -> [] ·",
          dict(Counter(c["criterio"] for c in ctx.casos)),
          "· adversariales:", sum(c["tipo"] == "adversarial" for c in ctx.casos))
    return ctx.casos


def tabla_casos(ctx: Contexto):
    """Los casos como DataFrame, para mostrarlos en el notebook."""
    import pandas as pd
    return pd.DataFrame(ctx.casos)[["id", "criterio", "tipo", "imagen", "esperado", "pregunta"]]


def miniaturas(ctx: Contexto, carpeta_imagenes: Path = CARPETA_IMAGENES, cargar_fn=vlm.cargar):
    """Las imagenes del eval set (demo de T3). Sin matplotlib se omiten: en
    una maquina local puede faltar y no debe cortar la corrida."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no esta instalado: se omiten las miniaturas.")
        return None
    nombres = sorted({c["imagen"] for c in ctx.casos})
    fig, ejes = plt.subplots(1, len(nombres), figsize=(3 * len(nombres), 4.4))
    for eje, nombre in zip(ejes, nombres):
        eje.imshow(cargar_fn(str(Path(carpeta_imagenes) / nombre)))
        eje.set_title(nombre.replace("_", " ").rsplit(".", 1)[0], fontsize=8)
        eje.axis("off")
    plt.tight_layout()
    plt.show()
    return fig


def correr_harness(ctx: Contexto, cargar_fn=vlm.cargar, **kwargs) -> dict:
    """T6: `correr_t6` contra el M3 real. `sistema_m3` es el nombre TAL CUAL de
    la fila en `results/m3_scorecard.csv`, contra la que se arma la tabla de
    delta. Valida el CSV y las imagenes ANTES del primer caso."""
    from amparo.multimodal.scorecard import correr_t6
    ctx.res = correr_t6(cargar_fn, ctx.ver, ctx.preguntar, ctx.responder_m3,
                        sistema_m3=ctx.sistema_m3, **kwargs)
    if hasattr(ctx.agente_m3, "guardar_cache"):
        ctx.agente_m3.guardar_cache()
    return ctx.res


def delta_imagen(ctx: Contexto, **kwargs) -> dict:
    """El delta del COMPONENTE: la misma pregunta con imagen y sin ella, sobre
    el mismo M3. La tabla de delta compara casos de M4 contra los de M3, que no
    son los mismos; esta no. Sin GPU: la condicion CON imagen sale de las
    trazas, la SIN imagen es `responder_m3(pregunta)`. Con 3 casos es una
    lectura caso por caso, no una prueba."""
    from amparo.multimodal.scorecard import delta_con_sin_imagen
    ctx.delta_imagen = di = delta_con_sin_imagen(ctx.responder_m3, **kwargs)
    if hasattr(ctx.agente_m3, "guardar_cache"):
        ctx.agente_m3.guardar_cache()
    print(f"acierto de mecanismo CON imagen: {di['acierto_con_imagen']}  ·  "
          f"SIN imagen: {di['acierto_sin_imagen']}  (n = {di['n']})")
    for f in di["casos"]:
        print(f"  {f['id']}  esperado {f['esperado']:<20} con {f['nota_con_imagen']}  "
              f"sin {f['nota_sin_imagen']}  -> {f['efecto']}")
    return di


def resumen(ruta_scorecard="m4/scorecard_m4.csv", ruta_trazas="m4/trazas_m4.json"):
    """Lo que quedo en disco: una fila por caso, con la etapa y lo que leyo el VLM."""
    import pandas as pd
    sc = pd.read_csv(ruta_scorecard)
    trazas = json.loads(Path(ruta_trazas).read_text(encoding="utf-8"))
    sc["etapa"] = sc.id.map(lambda i: trazas[i]["etapa"])
    sc["lectura_vlm"] = sc.id.map(lambda i: json.dumps(trazas[i]["js"], ensure_ascii=False))
    print("nota media:", round(sc.nota.mean(), 3), "· latencia media (s):", round(sc.segundos.mean(), 2))
    return sc[["id", "criterio", "tipo", "nota", "segundos", "etapa", "lectura_vlm"]]


def descargar(salidas=SALIDAS) -> list[str]:
    """Bajar lo que genero la corrida (en Colab) para subirlo al repo."""
    existentes = [p for p in salidas if os.path.exists(p)]
    try:
        from google.colab import files
        for p in existentes:
            files.download(p)
    except ImportError:
        print("Fuera de Colab: los archivos quedaron en", existentes)
    return existentes


def correr() -> Contexto:
    """M4 de punta a punta (Colab, GPU, GROQ_API_KEY)."""
    ctx = preparar()
    cargar_imagenes(ctx)
    cargar_modelo(ctx)
    probar_ver(ctx)
    enchufar_m3(ctx)
    validar_eval_set(ctx)
    miniaturas(ctx)
    correr_harness(ctx)
    delta_imagen(ctx)
    resumen()
    descargar()
    return ctx


if __name__ == "__main__":
    correr()
