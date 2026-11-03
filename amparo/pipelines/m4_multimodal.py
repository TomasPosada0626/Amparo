"""M4 · El sistema ya ve: el pipeline multimodal, etapa por etapa.

Sigue el notebook de evaluacion de M4 tal como quedo tras la revision docente
(PR #15 y #16) en el tag `demo-final`, sobre los mismos modulos que ese
notebook importaba y que ahora viven en el paquete:

    m4/pipeline/multimodal.py  ->  amparo/multimodal/sistema_visual.py
    m4/pipeline/corrida.py     ->  amparo/multimodal/corrida_m4.py
    m4/pipeline/enchufe_m3.py  ->  amparo/multimodal/enchufe.py
    m4/harness/*.py            ->  amparo/multimodal/criterios.py, scorecard.py

Patron input: la foto de un documento -> Qwen2-VL-2B extrae hechos en JSON ->
se suman al relato -> el M3 real (brazo `4 · agente + reglas`) decide el
mecanismo. M3 no se reescribe: `ver()` es un traductor en la puerta.

LOS NOTEBOOKS DE M4 NO LLAMAN A ESTE MODULO. `M4_pipeline.ipynb` y
`M4_demo.ipynb` clonan el tag fijo `demo-final` (revision docente, H3): lo que
corre en ellos es lo que se evaluo, con la estructura de entonces. Este
pipeline es la misma secuencia sobre el paquete, para correrla desde `main`.

Etapas (celdas del notebook de evaluacion entre parentesis):

    preparar            (4-6)   raiz, version, clave de Groq, carpeta de la corrida
    cargar_imagenes     (8)     patron, pregunta del usuario, 3 documentos de T3
    cargar_lector       (10)    LectorVisual: Qwen2-VL-2B con `ver`/`preguntar`
    probar_ver          (12)    ver() sola sobre 3 imagenes, con latencia
    enchufar_m3         (14)    el M3 real, la respuesta en tres bloques y el manifiesto
    validar_eval_set    (16)    casos_m4.csv pasa `validar_casos`
    miniaturas          (17)    las imagenes del eval set (demo de T3)
    correr_harness      (18)    correr_t6: scorecard, trazas y tabla de delta
    delta_imagen        (20)    misma pregunta con y sin imagen, mismo M3
    delta_repetido      (22)    el delta 3 veces con la cache vacia (H4)
    resumen             (23)    lo que quedo en disco, caso por caso
    plan_b              (25)    la salida grabada de m01, m06 y m10 para la demo
    cerrar              (27)    el manifiesto con las cifras de la corrida
    descargar           (28)    un .zip con la carpeta de la corrida

Corre con GPU y `GROQ_API_KEY` (el brazo 4 razona por la API de Groq). M4 no
es uno de los modulos de `arranque.ORDEN` (m1-m3), asi que no usa
`entorno.preparar()`: solo la clave de Groq de `entorno`.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from amparo.config import RAIZ
from amparo.multimodal import corrida_m4, criterios, enchufe, scorecard, sistema_visual

PATRON = "input"   # M4 de Amparo: el usuario manda una foto de un documento, el VLM la lee
# La pregunta del usuario que necesita ojos (una frase):
PREGUNTA_USUARIO = "Adjunto este documento que me llegó, ¿qué mecanismo constitucional me corresponde?"
# Documentos sinteticos de T3 (Lucas), relativos a la raiz del repo.
IMAGENES = {
    "oficio_planeacion":      "m4/eval_set/imagenes/doc02_oficio_planeacion.png",       # plazo de 15 dias
    "notificacion_acueducto": "m4/eval_set/imagenes/doc05_notificacion_acueducto.jpg",  # foto de celular legible
    "notificacion_borrosa":   "m4/eval_set/imagenes/doc06_notificacion_borrosa.jpg",    # ADVERSARIAL: sin fecha ni plazo
}
RUTA_CASOS = Path("m4/eval_set/casos_m4.csv")
CARPETA_IMAGENES = Path("m4/eval_set/imagenes")
REPETICIONES = 3
# Los tres casos del guion de la demo: se graban por si la demo en vivo falla.
PLAN_B = ("m01", "m06", "m10")


@dataclass
class Contexto:
    corrida_id: str | None = None
    carpeta: Path | None = None
    imgs: dict = field(default_factory=dict)
    lector: object = None
    ver: object = None
    preguntar: object = None
    responder_m3: object = None
    agente_m3: object = None
    amparo: object = None
    manifiesto: dict | None = None
    casos: list = field(default_factory=list)
    resultado: dict | None = None
    delta: dict | None = None
    delta_rep: dict | None = None


def cargar(src):
    """Carga una imagen desde URL o ruta local y la normaliza a RGB."""
    from PIL import Image
    if str(src).startswith("http"):
        import io
        import requests
        return Image.open(io.BytesIO(requests.get(src, timeout=30).content)).convert("RGB")
    return Image.open(src).convert("RGB")


def cronometrar(f, *a, **k):
    t0 = time.time()
    r = f(*a, **k)
    return r, round(time.time() - t0, 2)


def _git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=RAIZ).stdout.strip()


# --------------------------------------------------------------------------
# Etapas
# --------------------------------------------------------------------------
def preparar(*, exigir_clave: bool = True, etiqueta: str = "demo") -> Contexto:
    """Raiz, version, clave de Groq y la carpeta de la corrida (celdas 4-6).

    La clave va antes del enchufe porque el brazo 4 de M3 la necesita. Cada
    corrida escribe en `m4/corridas/<id>/`, con el id en UTC: no pisa la
    corrida oficial del 2026-10-25 (`m4/scorecard_m4.csv` y compania), que la
    revision docente pidio conservar como historica (H3).
    """
    from amparo.ejecucion import entorno
    os.chdir(RAIZ)
    print("repo:", RAIZ, "· version", _git("describe", "--tags", "--always"),
          "· commit", _git("rev-parse", "--short", "HEAD"))
    if not entorno.cargar_clave_groq() and exigir_clave:
        raise SystemExit("Falta GROQ_API_KEY: panel izquierdo -> icono de la llave -> "
                         "GROQ_API_KEY, con acceso para este notebook.")
    ctx = Contexto()
    ctx.corrida_id, ctx.carpeta = corrida_m4.nueva(etiqueta)
    print("corrida:", ctx.corrida_id, "->", ctx.carpeta)
    return ctx


def cargar_imagenes(ctx: Contexto, cargar_fn=cargar) -> dict:
    assert PATRON == "input", "Para Amparo el patron es input (ver README_PLAN.md)."
    ctx.imgs = {k: cargar_fn(str(RAIZ / v)) for k, v in IMAGENES.items()}
    print("patron:", PATRON, "· imagenes:", list(ctx.imgs))
    return ctx.imgs


def cargar_lector(ctx: Contexto, lector=None):
    """El VLM, cargado una vez (celda 10). `lector` se inyecta en las pruebas."""
    ctx.lector = lector if lector is not None else sistema_visual.LectorVisual()
    ctx.ver, ctx.preguntar = ctx.lector.ver, ctx.lector.preguntar
    print("VLM listo:", sistema_visual.VLM_ID, "·", getattr(ctx.lector, "dtype", None),
          "·", getattr(ctx.lector, "device", None))
    print("\nválvula:", sistema_visual.VALVULA)
    return ctx.lector


def probar_ver(ctx: Contexto) -> list[dict]:
    """ver() sola sobre las 3 imagenes, con latencia (T2): ¿JSON parseable?
    ¿cuantos segundos? ¿donde alucino un dato que no se ve?"""
    filas = []
    for nombre, im in ctx.imgs.items():
        (crudo, js), seg = cronometrar(ctx.ver, im)
        print(f"[{nombre}] {seg}s")
        print("  JSON :", js)
        if js is None:
            print("  CRUDO:", crudo[:200], "   <- no parseo (cuenta como fallo, regla 2)")
        print()
        filas.append({"imagen": nombre, "segundos": seg, "js": js})
    return filas


def enchufar_m3(ctx: Contexto, **kwargs) -> str:
    """El M3 real, la respuesta en tres bloques y el manifiesto (celda 14).

    `kwargs` (cliente, indice, transformador) se pasan a
    `construir_responder_m3` para probar sin red. El reranker se carga en la
    primera busqueda: despues del ejemplo ya se sabe cual es, y va al manifiesto.
    """
    ctx.responder_m3, ctx.agente_m3 = enchufe.construir_responder_m3(
        cache_dir=ctx.carpeta / "cache", verbose=True, **kwargs)
    ctx.amparo = sistema_visual.Amparo(lector=ctx.lector, responder_m3=ctx.responder_m3,
                                       agente=ctx.agente_m3)
    print("M3 enchufado:", enchufe.SISTEMA_M3)
    ejemplo = ctx.amparo.responder_markdown(PREGUNTA_USUARIO, next(iter(ctx.imgs.values())))
    print(ejemplo)
    indice = getattr(ctx.agente_m3, "indice", None)
    print("reranker de M3:", getattr(indice, "reranker_usado", None))
    ctx.manifiesto = corrida_m4.manifiesto(ctx.corrida_id, vlm_id=sistema_visual.VLM_ID,
                                           vlm_dtype=str(getattr(ctx.lector, "dtype", None)),
                                           agente=ctx.agente_m3)
    print("manifiesto ->", corrida_m4.guardar(ctx.manifiesto, ctx.carpeta))
    return ejemplo


def validar_eval_set(ctx: Contexto, ruta_casos=RUTA_CASOS,
                     carpeta_imagenes=CARPETA_IMAGENES) -> list[dict]:
    casos = criterios.cargar_casos(RAIZ / ruta_casos)
    problemas = criterios.validar_casos(casos, carpeta_imagenes=RAIZ / carpeta_imagenes)
    assert not problemas, "casos_m4.csv no pasa la validacion:\n" + "\n".join(problemas)
    ctx.casos = casos
    print(f"{len(casos)} casos · validar_casos -> [] · adversariales:",
          sum(c["tipo"] == "adversarial" for c in casos))
    return casos


def tabla_casos(casos: list[dict]):
    """Los casos como DataFrame, para mostrarlos (pandas solo hace falta aqui)."""
    import pandas as pd
    return pd.DataFrame(casos)[["id", "criterio", "tipo", "imagen", "esperado", "pregunta"]]


def miniaturas(ctx: Contexto, cargar_fn=cargar) -> None:
    """Las imagenes del eval set (demo de T3). Sin matplotlib no se corta la corrida."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no esta instalado: se omiten las miniaturas.")
        return
    nombres = sorted({c["imagen"] for c in ctx.casos})
    fig, ejes = plt.subplots(1, len(nombres), figsize=(3 * len(nombres), 4.4))
    for eje, nombre in zip(ejes, nombres):
        eje.imshow(cargar_fn(str(RAIZ / CARPETA_IMAGENES / nombre)))
        eje.set_title(nombre.replace("_", " ").rsplit(".", 1)[0], fontsize=8)
        eje.axis("off")
    plt.tight_layout()
    plt.show()


def correr_harness(ctx: Contexto, cargar_fn=cargar, **kwargs) -> dict:
    """correr_t6 con las salidas en la carpeta de la corrida (celda 18).
    `kwargs` sobrescribe rutas (por ejemplo `ruta_m3_scorecard` en las pruebas)."""
    rutas = {"ruta_scorecard": ctx.carpeta / "scorecard_m4.csv",
             "ruta_trazas": ctx.carpeta / "trazas_m4.json",
             "ruta_delta": ctx.carpeta / "delta_m4.json"}
    rutas.update(kwargs)
    ctx.resultado = scorecard.correr_t6(cargar_fn, ctx.ver, ctx.preguntar, ctx.responder_m3,
                                        sistema_m3=enchufe.SISTEMA_M3, **rutas)
    ctx.agente_m3.guardar_cache()
    return ctx.resultado


def delta_imagen(ctx: Contexto, **kwargs) -> dict:
    """El delta del componente: con imagen y sin ella, mismo M3 (celda 20).
    Las caches se vacian antes: si no, la segunda condicion repetiria respuestas."""
    enchufe.vaciar_caches(ctx.agente_m3)
    rutas = {"ruta_trazas": ctx.carpeta / "trazas_m4.json",
             "ruta_salida": ctx.carpeta / "delta_imagen_m4.json",
             "ruta_scorecard": ctx.carpeta / "scorecard_m4.csv"}
    rutas.update(kwargs)
    di = scorecard.delta_con_sin_imagen(ctx.responder_m3, **rutas)
    print(f"acierto CON imagen: {di['acierto_con_imagen']} · SIN imagen: {di['acierto_sin_imagen']} (n = {di['n']})")
    print(f"latencia media  CON imagen (ver + M3): {di['latencia_con_imagen']} s · "
          f"SIN imagen (M3): {di['latencia_sin_imagen']} s")
    for f in di["casos"]:
        print(f"  {f['id']}  esperado {f['esperado']:<20} con {f['nota_con_imagen']}  sin {f['nota_sin_imagen']}"
              f"  -> {f['efecto']}  ({f['segundos_con_imagen']} s / {f['segundos_sin_imagen']} s)")
    ctx.delta = di
    return di


def delta_repetido(ctx: Contexto, repeticiones: int = REPETICIONES, **kwargs) -> dict:
    """El delta repetido con la cache vacia antes de cada llamada (H4): en una
    sola pasada el aporte de la imagen en m06 variaba entre corridas."""
    rutas = {"ruta_trazas": ctx.carpeta / "trazas_m4.json",
             "ruta_salida": ctx.carpeta / "delta_imagen_repetido_m4.json"}
    rutas.update(kwargs)
    dr = scorecard.delta_repetido(ctx.responder_m3, repeticiones=repeticiones,
                                  vaciar_cache=lambda: enchufe.vaciar_caches(ctx.agente_m3), **rutas)
    print(f"aciertos CON imagen: {dr['aciertos_con_imagen']} · SIN imagen: {dr['aciertos_sin_imagen']}"
          f"  ({repeticiones} repeticiones x {dr['n_casos']} casos, caché vacía)")
    print(f"mediana por caso  CON imagen (ver + M3): {dr['mediana_segundos_con_imagen']} s · "
          f"SIN imagen (M3): {dr['mediana_segundos_sin_imagen']} s · ver(): {dr['mediana_segundos_ver']} s")
    for f in dr["casos"]:
        print(f"  {f['id']}  {f['esperado']:<20} con {f['aciertos_con_imagen']:g}/{repeticiones}  "
              f"sin {f['aciertos_sin_imagen']:g}/{repeticiones}  -> {f['lectura']}")
    ctx.delta_rep = dr
    return dr


def resumen(ctx: Contexto):
    """Lo que quedo en disco: una fila por caso, y lo que leyo el VLM en cada uno."""
    import pandas as pd
    sc = pd.read_csv(ctx.carpeta / "scorecard_m4.csv")
    trazas = json.loads((ctx.carpeta / "trazas_m4.json").read_text(encoding="utf-8"))
    sc["etapa"] = sc.id.map(lambda i: trazas[i]["etapa"])
    sc["segundos_ver"] = sc.id.map(lambda i: trazas[i].get("segundos_ver"))
    sc["lectura_vlm"] = sc.id.map(lambda i: json.dumps(trazas[i]["js"], ensure_ascii=False))
    print("nota media:", round(sc.nota.mean(), 3),
          "· latencia por caso: mediana", round(sc.segundos.median(), 2), "s,",
          "media", round(sc.segundos.mean(), 2), "s")
    return sc[["id", "criterio", "tipo", "nota", "segundos", "segundos_ver", "etapa", "lectura_vlm"]]


def plan_b(ctx: Contexto, casos_plan=PLAN_B, cargar_fn=cargar) -> Path:
    """La salida GRABADA de los casos del guion, por si la demo en vivo falla.
    No es una ejecucion en vivo, y el archivo lo dice con su commit y su GPU."""
    gpu = (ctx.manifiesto or {}).get("entorno", {}).get("gpu", {}) or {}
    partes = [f"# Plan B · salida GRABADA de la corrida {ctx.corrida_id}", "",
              "> No es una ejecución en vivo. Es la salida que dio Amparo en esta corrida, con el "
              f"commit `{(ctx.manifiesto or {}).get('codigo', {}).get('commit')}` y la GPU "
              f"`{gpu.get('nombre')}`.", ""]
    for cid in casos_plan:
        caso = next(c for c in ctx.casos if c["id"] == cid)
        enchufe.vaciar_caches(ctx.agente_m3)
        md_caso = ctx.amparo.responder_markdown(
            caso["pregunta"], cargar_fn(str(RAIZ / CARPETA_IMAGENES / caso["imagen"])))
        partes += [f"## {cid} · {caso['imagen']}", "", f"**Pregunta:** {caso['pregunta']}", "",
                   md_caso, "", "---", ""]
    ruta = ctx.carpeta / "plan_b_demo.md"
    ruta.write_text("\n".join(partes), encoding="utf-8")
    ctx.agente_m3.guardar_cache()
    print("plan B ->", ruta)
    return ruta


def cerrar(ctx: Contexto) -> Path:
    """El manifiesto se completa con lo que solo se sabe al final, y con las
    cifras de la corrida (celda 27)."""
    import pandas as pd
    sc = pd.read_csv(ctx.carpeta / "scorecard_m4.csv")
    exacto = sc[sc.criterio == "exacto"]
    resumen_ = {
        "notas_por_criterio": sc.groupby("criterio").nota.mean().round(3).to_dict(),
        "exacto_aciertos": f"{int(exacto.nota.sum())}/{len(exacto)}",
        "latencia_por_caso_s": {"mediana": round(float(sc.segundos.median()), 2),
                                "media": round(float(sc.segundos.mean()), 2),
                                "max": round(float(sc.segundos.max()), 2)},
        "delta_una_pasada": {"con_imagen": ctx.delta["acierto_con_imagen"],
                             "sin_imagen": ctx.delta["acierto_sin_imagen"]},
        "delta_repetido": {"repeticiones": REPETICIONES,
                           "con_imagen": ctx.delta_rep["aciertos_con_imagen"],
                           "sin_imagen": ctx.delta_rep["aciertos_sin_imagen"],
                           "por_caso": {f["id"]: f["lectura"] for f in ctx.delta_rep["casos"]}},
    }
    ruta = corrida_m4.cerrar(ctx.manifiesto, ctx.carpeta, agente=ctx.agente_m3, resumen=resumen_)
    print(json.dumps(json.loads(Path(ruta).read_text(encoding="utf-8"))["resumen"],
                     ensure_ascii=False, indent=1))
    return ruta


def descargar(ctx: Contexto) -> str:
    """Un .zip con toda la carpeta de la corrida; en Colab se descarga. Hay que
    guardar tambien el notebook ejecutado dentro de esa carpeta: la revision
    pidio conservar las salidas de las celdas."""
    import shutil
    zip_ = shutil.make_archive(str(ctx.carpeta), "zip", root_dir=ctx.carpeta.parent,
                               base_dir=ctx.carpeta.name)
    print("zip:", zip_)
    try:
        from google.colab import files
        files.download(zip_)
    except ImportError:
        print("Fuera de Colab: el zip quedo en", zip_)
    return zip_


def correr() -> Contexto:
    """Todas las etapas, en el orden del notebook de evaluacion."""
    ctx = preparar()
    cargar_imagenes(ctx)
    cargar_lector(ctx)
    probar_ver(ctx)
    enchufar_m3(ctx)
    validar_eval_set(ctx)
    miniaturas(ctx)
    correr_harness(ctx)
    delta_imagen(ctx)
    delta_repetido(ctx)
    resumen(ctx)
    plan_b(ctx)
    cerrar(ctx)
    descargar(ctx)
    return ctx
