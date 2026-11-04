"""M5 · S15 · Parte B: lo que necesita `m5/space/app.py` para servir Amparo.

Sigue el `app.py` del lab de la profe (S15, Parte B) y la tabla de despliegue
que recomendo para Amparo ("Space en CPU para la app y Groq para el LLM; para
la demo en vivo con fotos, la misma app en Kaggle T4"). Aqui vive la logica;
`app.py` solo arma la interfaz, para que se pueda probar sin Gradio ni GPU.

Lo que pide la tabla de la profe, y donde esta:

  - modelos cargados UNA vez al iniciar ............ `armar_amparo`
  - indice de embeddings precalculado, no al arrancar  `precalcular_indice`, `cargar_indice`
  - limitar la resolucion en CPU (`max_pixels`) ...... `config_desde_entorno`
  - cache de Groq de los casos ensayados ............ cache en disco del agente (`guardar_cache`)
  - mensaje claro si la API no responde ............. `consultar`
  - health check y un log JSON por consulta ......... `health`, `registro`
  - version con tag de git visible .................. `version`
  - claves en Secrets, nunca en el codigo ........... solo se leen de os.environ

Y una cosa que la tabla no dice pero el codigo de M3 obliga: `Agente._hechos`
NO lanza el error cuando Groq falla en la extraccion; sigue con los hechos
por defecto y el motor responde **tutela**. En produccion eso seria una
respuesta juridica falsa con cara de verdadera. `consultar` lo detecta y
muestra el error en vez de la tutela.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

from amparo.config import RAIZ

RUTA_INDICE = RAIZ / "m5" / "space" / "indice_m3.npz"
CARPETA_CACHE = RAIZ / "runs" / "cache" / "space"
MAX_PIXELS_CPU = 256 * 28 * 28        # ~450 x 450: el VLM en CPU tarda decenas de s con mas

MENSAJE_API = ("**Amparo no pudo consultar su modelo de lenguaje (Groq) en este momento.** "
               "No se muestra una respuesta para no darte una que no se verificó. "
               "Intenta de nuevo en un minuto. Si sigue fallando, el plan gratuito pudo "
               "agotar su cupo por hoy.")


# ---------------------------------------------------------------------------
# Version y configuracion
# ---------------------------------------------------------------------------
def version(raiz: Path = RAIZ) -> dict:
    """El tag/commit del codigo que corre, para mostrarlo en la app."""
    def git(*a):
        try:
            r = subprocess.run(["git", *a], cwd=raiz, capture_output=True, text=True, timeout=10)
            return r.stdout.strip() or None
        except Exception:                                  # noqa: BLE001
            return None
    return {"describe": git("describe", "--tags", "--always", "--dirty"),
            "commit": git("rev-parse", "--short", "HEAD")}


def config_desde_entorno(env=None, cuda: bool | None = None) -> dict:
    """La misma app para el Space (CPU) y para Kaggle (T4), segun variables:

    AMPARO_VLM         'auto' (defecto), 'fp16', 'int4' o 'off' (solo texto).
                       'auto' = 'fp16' con GPU y 'cpu' sin ella. NO es int4: la
                       cuantizacion no cumplio su contrato (m5/cuantizacion.json:
                       3/5 clausulas). int4 sigue disponible pidiendolo.
    AMPARO_MAX_PIXELS  tope de resolucion; en CPU vale MAX_PIXELS_CPU por defecto.
    AMPARO_SHARE       '1' para el enlace publico de Gradio (Kaggle).
    """
    env = os.environ if env is None else env
    if cuda is None:
        try:
            import torch
            cuda = torch.cuda.is_available()
        except ImportError:
            cuda = False
    vlm = env.get("AMPARO_VLM", "auto").lower()
    if vlm == "auto":
        vlm = "fp16" if cuda else "cpu"
    if vlm in ("int4", "fp16") and not cuda:
        vlm = "cpu"                                         # bitsandbytes y fp16 piden GPU
    if vlm not in ("int4", "fp16", "cpu", "off"):
        raise ValueError(f"AMPARO_VLM={vlm!r}: use auto, fp16, int4 u off")
    mp = env.get("AMPARO_MAX_PIXELS")
    max_pixels = int(mp) if mp else (MAX_PIXELS_CPU if vlm == "cpu" else None)
    return {"vlm": vlm, "max_pixels": max_pixels, "cuda": bool(cuda),
            "share": env.get("AMPARO_SHARE", "0") == "1"}


# ---------------------------------------------------------------------------
# Indice precalculado
# ---------------------------------------------------------------------------
def _huella(textos: list[str]) -> str:
    return hashlib.sha256("\n\x00".join(textos).encode("utf-8")).hexdigest()[:16]


def _chunks_de_m3():
    from amparo.multimodal import enchufe
    from amparo.rag import recuperacion as rag
    _nombre, trocear = enchufe.chunking_de_m3()
    return trocear(rag.cargar_corpus())


def precalcular_indice(ruta: Path = RUTA_INDICE, chunks=None) -> Path:
    """Calcula los embeddings del corpus de M3 UNA vez y los guarda.

    Se corre en Colab y el archivo va al repo; el Space solo lo carga. La
    huella de los textos dice si el corpus cambio desde que se calculo.
    """
    import numpy as np
    from amparo.rag import recuperacion as rag
    chunks = chunks if chunks is not None else _chunks_de_m3()
    ind = rag.Indice(chunks, verbose=False).construir()
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    np.savez(ruta, emb=np.asarray(ind._emb, dtype="float32"),
             modelo=np.array(ind.modelo), huella=np.array(_huella(ind.textos)))
    print(f"indice precalculado: {len(chunks)} fragmentos · {ind.modelo} -> {ruta}")
    return ruta


def cargar_indice(ruta: Path = RUTA_INDICE, chunks=None):
    """El indice de M3 con los embeddings del archivo. Si falta o no coincide
    con el corpus, lo construye y lo dice: arranca mas lento, pero no
    responde con un indice de otro corpus."""
    import numpy as np
    from amparo.rag import recuperacion as rag
    chunks = chunks if chunks is not None else _chunks_de_m3()
    ind = rag.Indice(chunks, verbose=False)
    ruta = Path(ruta)
    if ruta.exists():
        d = np.load(ruta, allow_pickle=False)
        if str(d["huella"]) == _huella(ind.textos) and len(d["emb"]) == len(chunks):
            ind.modelo = str(d["modelo"])
            ind._emb = d["emb"]
            return ind, "precalculado"
        print("ATENCION · el indice precalculado no coincide con el corpus: se reconstruye")
    else:
        print(f"ATENCION · no existe {ruta}: se construye al arrancar")
    return ind.construir(), "construido al arrancar"


# ---------------------------------------------------------------------------
# Armar el sistema (una vez)
# ---------------------------------------------------------------------------
def armar_amparo(cfg: dict, *, cache_dir: Path = CARPETA_CACHE, ruta_indice: Path = RUTA_INDICE):
    """`(amparo, estado)`. Carga el VLM segun `cfg` y el brazo 4 de M3 con el
    indice precalculado y su cache en disco (los casos ensayados no vuelven a
    gastar Groq)."""
    from amparo.multimodal import enchufe
    from amparo.multimodal.sistema_visual import Amparo, LectorVisual
    t0 = time.perf_counter()
    indice, origen_indice = cargar_indice(ruta_indice)
    responder_m3, agente = enchufe.construir_responder_m3(indice=indice, cache_dir=cache_dir)
    lector = None
    if cfg["vlm"] != "off":
        lector = LectorVisual(
            device="cuda" if cfg["vlm"] in ("int4", "fp16") else "cpu",
            cuantizacion="int4" if cfg["vlm"] == "int4" else None,
            max_pixels=cfg["max_pixels"])
    amparo = Amparo(lector=lector or _SinVision(), responder_m3=responder_m3, agente=agente)
    estado = {"vlm": cfg["vlm"], "max_pixels": cfg["max_pixels"], "indice": origen_indice,
              "m3": enchufe.SISTEMA_M3, "modelo_m3": getattr(agente, "modelo", None),
              "carga_s": round(time.perf_counter() - t0, 1)}
    return amparo, estado


class _SinVision:
    """Cuando el VLM esta apagado (`AMPARO_VLM=off`), una foto no se lee:
    se dice, en vez de fingir una lectura."""
    def ver(self, imagen):
        raise SinVision("Esta versión de Amparo no lee fotos: escribe los datos del documento "
                        "en tu pregunta (fecha, entidad y qué te responden).")


class SinVision(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Una consulta, con su registro
# ---------------------------------------------------------------------------
def anonimizar(texto: str) -> str:
    """Como el lab: sin numeros largos (cedulas, radicados) y recortado."""
    return re.sub(r"\d{6,}", "[num]", texto or "")[:120]


def consultar(amparo, pregunta: str, imagen=None, *, ver_version: str = "") -> tuple[str, dict]:
    """`(markdown, registro)`. Nunca lanza: un fallo se convierte en un
    mensaje claro y en un registro con `ok=False`."""
    from amparo.multimodal.sistema_visual import formatear
    t0 = time.perf_counter()
    agente = getattr(amparo, "agente", None)
    n_fallos = len(getattr(agente, "fallos_extraccion", []) or [])
    reg = {"ts": round(time.time(), 3), "pregunta": anonimizar(pregunta),
           "ruta": "con_imagen" if imagen is not None else "sin_imagen",
           "version": ver_version, "ok": True, "error": None,
           "mecanismo": None, "regla": None, "se_abstuvo": None,
           "lectura_ms": None, "m3_ms": None}
    try:
        res = amparo.responder(pregunta, imagen)
        nuevos = (getattr(agente, "fallos_extraccion", []) or [])[n_fallos:]
        if nuevos:                         # Groq fallo por dentro: el motor diria tutela
            raise ErrorAPI(nuevos[-1].get("error", "fallo de extraccion"))
        md = formatear(res)
        pq = res.get("por_que") or {}
        from amparo.nucleo import schema
        reg.update(mecanismo=schema.parse_salida(res["respuesta"]).get("mecanismo"),
                   regla=pq.get("regla"), se_abstuvo=pq.get("se_abstuvo"))
        seg = res.get("segundos") or {}
        for k, campo in (("lectura del documento", "lectura_ms"), ("decisión (M3)", "m3_ms")):
            if seg.get(k) is not None:
                reg[campo] = int(seg[k] * 1000)
        if agente is not None and hasattr(agente, "guardar_cache"):
            agente.guardar_cache()         # el caso ensayado ya no gasta Groq
    except SinVision as ex:
        md, reg["ok"], reg["error"] = f"**{ex}**", False, "sin_vision"
    except ErrorAPI as ex:
        md, reg["ok"], reg["error"] = MENSAJE_API, False, f"api: {ex}"
    except Exception as ex:                                 # noqa: BLE001
        texto = f"{type(ex).__name__}: {ex}"
        es_api = any(s in texto.lower() for s in ("groq", "rate", "429", "connection", "timeout",
                                                   "api"))
        md = MENSAJE_API if es_api else ("**Algo falló al responder.** Intenta de nuevo; "
                                         "si se repite, avísale al equipo.")
        reg["ok"], reg["error"] = False, texto[:200]
    reg["latencia_ms"] = int((time.perf_counter() - t0) * 1000)
    return md, reg


class ErrorAPI(RuntimeError):
    pass


def registrar(reg: dict, log=None, wandb_mod=None) -> str:
    """Una linea JSON por consulta (al log) y, si W&B esta activo, sus metricas."""
    linea = json.dumps(reg, ensure_ascii=False)
    if log is not None:
        log.info(linea)
    if wandb_mod is not None and getattr(wandb_mod, "run", None):
        m = {"latencia_ms": reg["latencia_ms"], "ok": int(reg["ok"]),
             f"ruta_{reg['ruta']}": 1}
        if reg.get("mecanismo"):
            m[f"mecanismo_{reg['mecanismo']}"] = 1
        if reg.get("se_abstuvo"):
            m["abstencion"] = 1
        for k in ("lectura_ms", "m3_ms"):
            if reg.get(k) is not None:
                m[k] = reg[k]
        wandb_mod.log(m)
    return linea


def health(estado: dict, t0: float, ruta_log: Path, ver: dict) -> dict:
    """El health check visible en la pestaña Estado."""
    n = 0
    ok = 0
    if Path(ruta_log).exists():
        for linea in Path(ruta_log).read_text(encoding="utf-8").splitlines():
            try:
                n += 1
                ok += bool(json.loads(linea).get("ok"))
            except json.JSONDecodeError:
                pass
    return {"status": "ok", "version": ver.get("describe"), "commit": ver.get("commit"),
            **estado, "uptime_s": int(time.time() - t0), "consultas": n,
            "consultas_ok": ok, "groq_clave": bool(os.environ.get("GROQ_API_KEY")),
            "wandb": bool(os.environ.get("WANDB_API_KEY"))}
