"""M5 · S15 · Parte A: cuantizar el VLM de Amparo, etapa por etapa.

Sigue el lab de la profe (`sesiones/s15/S15_Lab_Despliegue_RESUELTO.ipynb`,
Parte A): dos cargas del mismo modelo, fp16 y int4 con bitsandbytes (nf4),
y una tabla antes/despues con memoria, latencia p50/p95 y calidad, con
temperatura 0. El notebook `m5/S15_cuantizacion.ipynb` solo llama a esto.

Por que el VLM
--------------
Es el unico modelo que corre en la GPU del sistema que se despliega (M4):
M3 razona por Groq. La destilacion de S14 no cumplio su contrato y el
sistema se quedo con el profesor (ver `m5/README.md`, "Decision").

Como se aisla el efecto de cuantizar
------------------------------------
- **Calidad: el harness de M4**, los 11 casos de `m4/eval_set/casos_m4.csv`
  (`campos`, `valvula`, `exacto`, `juez_vlm`), corrido igual que en M4.
- **El juez es siempre el VLM en fp16.** En M4 el VLM se juzga a si mismo
  (`juez_vlm`); si el juez tambien se cuantizara, un cambio en la nota no
  diria si cambio la lectura o el juez.
- **M3 comparte cache entre las dos cargas.** M3 no es determinista: el mismo
  relato puede cambiar de via entre corridas (13/18 en el delta de M4). Si el
  VLM int4 lee EXACTAMENTE lo mismo que el fp16, el relato es identico y M3
  responde desde la cache lo mismo; asi un cambio en `exacto` solo puede
  venir de una lectura distinta, no del ruido de M3.
- **Latencia: solo la lectura** (`ver`), que es lo que cambia. M3 corre en
  Groq y no depende de los bits del VLM.

Etapas (secciones del lab entre parentesis):

    preparar         (0)  raiz, carpeta, clave de Groq, contrato y manifiesto
    armar_m3         (A)  el brazo 4 de M3, con una cache para las dos cargas
    medir            (A)  fp16 y despues int4: memoria, latencias y harness M4
    tabla            (A)  la tabla antes/despues y las clausulas del contrato
    lecturas_distintas    los documentos que el int4 leyo distinto, campo a campo
    guardar               m5/cuantizacion.json (y una copia en Drive)
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from amparo.config import RAIZ

# ---------------------------------------------------------------------------
# El contrato, ANTES de medir (igual que en S14)
# ---------------------------------------------------------------------------
CONTRATO = {
    "componente": "VLM Qwen2-VL-2B-Instruct (lee el documento, M4)",
    "tecnica": "cuantizacion int4 (bitsandbytes nf4, computo fp16), la del lab de S15",
    "metrica": "harness de M4: 11 casos de m4/eval_set/casos_m4.csv",
    # Memoria: lo que la cuantizacion promete (slide 10 de S14: "4x menos").
    "memoria_x_min": 2.5,
    # `campos` es la nota de lectura (0.553 en la corrida de M4). Fechas,
    # numeros y plazos son la debilidad conocida del VLM: es donde int4 puede
    # pegar primero.
    "campos_baja_max": 0.05,
    # m10: no inventar la fecha ni el plazo que no se ven. Innegociable.
    "valvula_min": 1.0,
    # El mecanismo final (3 casos): no puede quedar peor que en fp16.
    "exacto_no_peor": True,
    # Latencia: en GPU, int4 con bitsandbytes suele ir IGUAL O MAS LENTO
    # (descomprime en cada paso). Lo que se gana es memoria, asi que solo se
    # pide que no empeore mas de un 30 %.
    "latencia_peor_max": 0.30,
}

VLM_ID = "Qwen/Qwen2-VL-2B-Instruct"
LICENCIA_VLM = "Apache 2.0 (Qwen2-VL-2B-Instruct)"
CASO_LATENCIA = "m01"      # la imagen de la medicion de latencia (la EPS)
N_LATENCIA = 5             # repeticiones, como `latencias()` del lab

CARPETA_REPO = RAIZ / "m5"


@dataclass
class Contexto:
    carpeta: Path = RAIZ / "runs" / "m5_cuantizacion"
    contrato: dict = field(default_factory=lambda: dict(CONTRATO))
    corrida: dict = field(default_factory=dict)
    responder_m3: object = None
    agente_m3: object = None
    juez: object = None                  # el lector fp16: juez fijo de juez_vlm
    medidas: dict = field(default_factory=dict)

    def ruta(self, nombre: str) -> Path:
        self.carpeta.mkdir(parents=True, exist_ok=True)
        return self.carpeta / nombre


def _escribir(ruta: Path, datos) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1, default=str),
                    encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# 0 · Setup
# ---------------------------------------------------------------------------
def preparar(carpeta: str | Path | None = None) -> Contexto:
    from amparo.ejecucion import entorno
    os.chdir(RAIZ)
    ctx = Contexto(carpeta=Path(carpeta) if carpeta else RAIZ / "runs" / "m5_cuantizacion")
    ctx.carpeta.mkdir(parents=True, exist_ok=True)
    print("raiz:", RAIZ, "· carpeta de trabajo:", ctx.carpeta)
    if not entorno.cargar_clave_groq():
        raise RuntimeError("Falta GROQ_API_KEY: M3 (brazo 4) razona por Groq.")
    ctx.corrida = manifiesto(ctx)
    _escribir(ctx.ruta("corrida_cuantizacion.json"), ctx.corrida)
    print("corrida:", ctx.corrida["codigo"]["describe"], "·",
          ctx.corrida["entorno"]["gpu"].get("nombre"))
    print("CONTRATO:", json.dumps(ctx.contrato, ensure_ascii=False, indent=1))
    return ctx


def manifiesto(ctx: Contexto) -> dict:
    """Que codigo, que GPU y que versiones (H3 de la profe en M4)."""
    from datetime import datetime, timezone
    from amparo.multimodal import corrida_m4 as c4
    return {
        "inicio_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "codigo": {"commit": c4._git("rev-parse", "HEAD"),
                   "rama": c4._git("rev-parse", "--abbrev-ref", "HEAD"),
                   "describe": c4._git("describe", "--tags", "--always", "--dirty")},
        "entorno": {"gpu": c4.gpu(),
                    "versiones": {m: _version(m) for m in (
                        "torch", "transformers", "accelerate", "bitsandbytes",
                        "qwen-vl-utils", "pillow", "groq", "sentence-transformers")}},
        "vlm": VLM_ID, "eval_set": c4.huella_eval_set(),
        "carpeta_de_trabajo": str(ctx.carpeta),
    }


def _version(modulo: str):
    try:
        from importlib.metadata import version
        return version(modulo)
    except Exception:                                      # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# A · M3, una sola vez para las dos cargas
# ---------------------------------------------------------------------------
def armar_m3(ctx: Contexto, **kwargs) -> Contexto:
    """El brazo 4 real, igual que en M4. Su cache vive en memoria durante
    toda la medicion: es lo que permite que una lectura identica de fp16 y de
    int4 reciba la misma respuesta de M3 (ver el docstring del modulo)."""
    from amparo.multimodal import enchufe
    ctx.responder_m3, ctx.agente_m3 = enchufe.construir_responder_m3(
        cache_dir=ctx.carpeta / "cache_m3", **kwargs)
    enchufe.vaciar_caches(ctx.agente_m3)       # nada de corridas anteriores
    print("M3 listo:", enchufe.SISTEMA_M3)
    return ctx


# ---------------------------------------------------------------------------
# A · Cargar, cronometrar y medir (las funciones del lab)
# ---------------------------------------------------------------------------
def cargar(cuantizar: bool, *, lector_cls=None):
    """`(lector, memoria_GB)`. La memoria es la GPU que reservo ESTA carga
    (`memory_allocated` antes y despues), como `cargar()` del lab."""
    import torch
    from amparo.multimodal.sistema_visual import LectorVisual
    lector_cls = lector_cls or LectorVisual
    cuda = torch.cuda.is_available()
    if cuda:
        torch.cuda.empty_cache()
    m0 = torch.cuda.memory_allocated() if cuda else 0
    lector = lector_cls(VLM_ID, cuantizacion="int4" if cuantizar else None)
    mem = ((torch.cuda.memory_allocated() - m0) / 1e9) if cuda else float("nan")
    return lector, mem


def latencias(ver_fn, imagen, n: int = N_LATENCIA, reloj=time.perf_counter):
    """`(p50, p95)` de `ver(imagen)`: un calentamiento que no cuenta y `n`
    repeticiones. Con n=5 el p95 es casi el maximo, como en el lab."""
    ver_fn(imagen)
    ts = []
    for _ in range(n):
        t0 = reloj()
        ver_fn(imagen)
        ts.append(reloj() - t0)
    ts.sort()
    return ts[len(ts) // 2], ts[-1]


def _cargar_imagen(ruta):
    from PIL import Image
    return Image.open(ruta).convert("RGB")


def notas_por_criterio(filas: list[dict]) -> dict:
    por: dict[str, list[float]] = {}
    for f in filas:
        por.setdefault(f["criterio"], []).append(float(f["nota"]))
    return {c: {"n": len(v), "nota": round(sum(v) / len(v), 3), "suma": round(sum(v), 3)}
            for c, v in sorted(por.items())}


def medir_una(ctx: Contexto, nombre: str, lector, memoria_gb: float, *,
              casos=None, cargar_fn=_cargar_imagen) -> dict:
    """Latencia de la lectura y harness de M4 para UNA carga del VLM."""
    from amparo.multimodal import criterios, scorecard
    casos = casos or criterios.cargar_casos(scorecard.RUTA_CASOS)
    caso_lat = next(c for c in casos if c["id"] == CASO_LATENCIA)
    img = cargar_fn(str(scorecard.CARPETA_IMAGENES / caso_lat["imagen"]))
    p50, p95 = latencias(lector.ver, img)
    juez = ctx.juez or lector
    filas, trazas = scorecard.correr_harness(
        casos, lector.ver, ctx.responder_m3, cargar_fn, preguntar_fn=juez.preguntar)
    out = {"modelo": nombre, "memoria_gb": round(memoria_gb, 2),
           "lectura_p50_s": round(p50, 2), "lectura_p95_s": round(p95, 2),
           "notas": notas_por_criterio(filas), "filas": filas, "trazas": trazas,
           "lecturas": {c["imagen"]: trazas[c["id"]]["js"] for c in casos}}
    _escribir(ctx.ruta(f"medida_{nombre}.json"), out)
    print(f"{nombre}: {out['memoria_gb']} GB · lectura p50 {out['lectura_p50_s']} s · "
          f"p95 {out['lectura_p95_s']} s · "
          + " · ".join(f"{c} {v['nota']}" for c, v in out["notas"].items()))
    return out


def medir(ctx: Contexto, *, lector_cls=None, casos=None, cargar_fn=_cargar_imagen) -> dict:
    """fp16 primero (y se queda cargado: es el juez fijo de `juez_vlm`),
    despues int4. Las dos con el MISMO M3 y su cache."""
    assert ctx.responder_m3 is not None, "falta armar_m3(ctx)"
    fp16, mem16 = cargar(False, lector_cls=lector_cls)
    ctx.juez = fp16
    ctx.medidas["fp16"] = medir_una(ctx, "fp16", fp16, mem16, casos=casos, cargar_fn=cargar_fn)
    int4, mem4 = cargar(True, lector_cls=lector_cls)
    ctx.medidas["int4"] = medir_una(ctx, "int4", int4, mem4, casos=casos, cargar_fn=cargar_fn)
    return ctx.medidas


# ---------------------------------------------------------------------------
# La tabla antes/despues y el contrato
# ---------------------------------------------------------------------------
def _nota(m: dict, criterio: str):
    v = m["notas"].get(criterio)
    return None if v is None else v["nota"]


def lecturas_distintas(ctx: Contexto) -> list[dict]:
    """Los documentos que int4 leyo distinto de fp16, campo por campo."""
    a, b = ctx.medidas["fp16"]["lecturas"], ctx.medidas["int4"]["lecturas"]
    out = []
    for img in a:
        ja, jb = a[img] or {}, b.get(img) or {}
        if ja != jb:
            campos = sorted(set(ja) | set(jb))
            out.append({"imagen": img, "campos": {
                k: {"fp16": ja.get(k), "int4": jb.get(k)} for k in campos if ja.get(k) != jb.get(k)}})
    ctx.medidas["lecturas_distintas"] = out
    print(f"{len(a) - len(out)} de {len(a)} documentos leidos igual en int4 que en fp16")
    for d in out:
        print(f"  {d['imagen']}: " + "; ".join(
            f"{k} {v['fp16']!r} -> {v['int4']!r}" for k, v in d["campos"].items()))
    return out


def tabla(ctx: Contexto):
    import pandas as pd
    a, b, c = ctx.medidas["fp16"], ctx.medidas["int4"], ctx.contrato
    filas = []
    for m in (a, b):
        filas.append({"modelo": f"Qwen2-VL-2B · {m['modelo']}", "memoria_GB": m["memoria_gb"],
                      "lectura_p50_s": m["lectura_p50_s"], "lectura_p95_s": m["lectura_p95_s"],
                      **{k: _nota(m, k) for k in ("campos", "valvula", "exacto", "juez_vlm")}})
    df = pd.DataFrame(filas).set_index("modelo")

    x_mem = a["memoria_gb"] / b["memoria_gb"] if b["memoria_gb"] else float("inf")
    baja_campos = (_nota(a, "campos") or 0) - (_nota(b, "campos") or 0)
    peor_lat = b["lectura_p50_s"] / a["lectura_p50_s"] - 1 if a["lectura_p50_s"] else 0.0
    ex_a = a["notas"].get("exacto", {}).get("suma", 0)
    ex_b = b["notas"].get("exacto", {}).get("suma", 0)
    n_ex = a["notas"].get("exacto", {}).get("n", 0)
    clausulas = {
        "memoria": {"pedido": f">= {c['memoria_x_min']}x menos",
                    "medido": f"{a['memoria_gb']} GB -> {b['memoria_gb']} GB ({x_mem:.1f}x)",
                    "cumple": x_mem >= c["memoria_x_min"]},
        "lectura (campos)": {"pedido": f"baja <= {c['campos_baja_max']}",
                             "medido": f"{_nota(a, 'campos')} -> {_nota(b, 'campos')} "
                                       f"({'baja' if baja_campos > 0 else 'sube'} {abs(baja_campos):.3f})",
                             "cumple": baja_campos <= c["campos_baja_max"]},
        "valvula (m10)": {"pedido": f">= {c['valvula_min']}",
                          "medido": f"{_nota(a, 'valvula')} -> {_nota(b, 'valvula')}",
                          "cumple": (_nota(b, "valvula") or 0) >= c["valvula_min"]},
        "mecanismo (exacto)": {"pedido": "no peor que fp16",
                               "medido": f"{ex_a:.0f}/{n_ex} -> {ex_b:.0f}/{n_ex}",
                               "cumple": ex_b >= ex_a},
        "latencia de la lectura": {"pedido": f"p50 no mas de {c['latencia_peor_max']:.0%} peor",
                                   "medido": f"{a['lectura_p50_s']} s -> {b['lectura_p50_s']} s "
                                             f"({peor_lat:+.0%})",
                                   "cumple": peor_lat <= c["latencia_peor_max"]},
    }
    ok = all(v["cumple"] for v in clausulas.values())
    print("CONTRATO")
    for nombre, v in clausulas.items():
        print(f"  {'OK ' if v['cumple'] else 'NO '} {nombre:24s} pedido: {v['pedido']:26s} "
              f"medido: {v['medido']}")
    print("  -> " + ("CUMPLIDO: la demo en GPU usa el VLM en int4" if ok else
                     "NO cumplido: la demo sigue con el VLM en fp16"))
    if b["notas"].get("juez_vlm") and a["notas"].get("juez_vlm"):
        print("  (juez_vlm: el juez es el VLM en fp16 en las dos filas)")
    ctx.medidas["tabla"] = {"filas": filas, "clausulas": clausulas, "cumple": ok,
                            "memoria_x": round(x_mem, 2)}
    return df


def guardar(ctx: Contexto, carpeta: Path = CARPETA_REPO) -> list[str]:
    """`m5/cuantizacion.json`: manifiesto, contrato, tabla, notas por caso y
    lecturas distintas. Copia en `<carpeta de trabajo>/entrega/` porque en
    Colab la copia del repo se borra al cerrar."""
    from datetime import datetime, timezone
    corrida = dict(ctx.corrida)
    corrida["fin_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    resumen = {
        "corrida": corrida, "contrato": ctx.contrato,
        "vlm": {"modelo": VLM_ID, "licencia": LICENCIA_VLM,
                "juez_vlm": "el VLM en fp16 para las dos cargas"},
        "tabla": ctx.medidas.get("tabla"),
        "lecturas_distintas": ctx.medidas.get("lecturas_distintas"),
        "por_caso": {q: [{k: f[k] for k in ("id", "criterio", "tipo", "nota", "segundos")}
                         for f in ctx.medidas[q]["filas"]]
                     for q in ("fp16", "int4") if q in ctx.medidas},
        "lecturas": {q: ctx.medidas[q]["lecturas"] for q in ("fp16", "int4") if q in ctx.medidas},
    }
    rutas = []
    for destino in (Path(carpeta), ctx.carpeta / "entrega"):
        _escribir(destino / "cuantizacion.json", resumen)
        rutas.append(str(destino / "cuantizacion.json"))
    print("guardado:", *rutas, sep="\n  ")
    return rutas


def descargar(ctx: Contexto) -> list[str]:
    a = ctx.carpeta / "entrega" / "cuantizacion.json"
    try:
        from google.colab import files
    except ImportError:
        print("no es Colab: el archivo ya esta en m5/")
        return [str(a)]
    files.download(str(a))
    return [str(a)]
