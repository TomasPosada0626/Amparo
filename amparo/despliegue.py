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
    AMPARO_ZEROGPU     '1' en un Space con hardware ZeroGPU (tambien se detecta
                       por `SPACES_ZERO_GPU`, que pone Hugging Face). Ahi la GPU
                       existe solo dentro de `@spaces.GPU`, asi que el VLM se
                       carga sin `device_map` y en fp16.
    """
    env = os.environ if env is None else env
    zerogpu = (env.get("AMPARO_ZEROGPU", "0") == "1"
               or str(env.get("SPACES_ZERO_GPU", "")).lower() in ("1", "true"))
    if zerogpu:
        cuda = True                          # fuera de @spaces.GPU, CUDA emulada
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
            "share": env.get("AMPARO_SHARE", "0") == "1", "zerogpu": zerogpu}


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
    if cfg.get("zerogpu"):
        # En ZeroGPU los modelos se cargan AL ARRANCAR, a nivel de modulo: el
        # codificador de consultas y el reranker de M3 se crean perezosamente
        # en la primera busqueda, que ya estaria dentro de @spaces.GPU.
        indice._encoder()
        indice._reranker()
    responder_m3, agente = enchufe.construir_responder_m3(indice=indice, cache_dir=cache_dir)
    lector = None
    if cfg["vlm"] != "off":
        lector = LectorVisual(
            device="cuda" if cfg["vlm"] in ("int4", "fp16") else "cpu",
            cuantizacion="int4" if cfg["vlm"] == "int4" else None,
            max_pixels=cfg["max_pixels"],
            device_map=None if cfg.get("zerogpu") else "auto")
    amparo = Amparo(lector=lector or _SinVision(), responder_m3=responder_m3, agente=agente)
    estado = {"vlm": cfg["vlm"], "max_pixels": cfg["max_pixels"], "indice": origen_indice,
              "hardware": "ZeroGPU" if cfg.get("zerogpu") else ("GPU" if cfg["cuda"] else "CPU"),
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


def consultar_res(amparo, pregunta: str, imagen=None, *, ver_version: str = ""):
    """`(res, mensaje_error, registro)`: la decision, sin presentarla.

    Es lo que corre dentro de `@spaces.GPU` en ZeroGPU. La redaccion va
    afuera (`presentar`): es una llamada a la API y no necesita GPU.
    Nunca lanza: un fallo deja `res=None`, un mensaje claro y `ok=False`.
    """
    t0 = time.perf_counter()
    agente = getattr(amparo, "agente", None)
    n_fallos = len(getattr(agente, "fallos_extraccion", []) or [])
    reg = {"ts": round(time.time(), 3), "pregunta": anonimizar(pregunta),
           "ruta": "con_imagen" if imagen is not None else "sin_imagen",
           "version": ver_version, "ok": True, "error": None,
           "mecanismo": None, "regla": None, "se_abstuvo": None,
           "lectura_ms": None, "m3_ms": None,
           "redaccion": None, "redaccion_valida": None, "redaccion_ms": None}
    res, md = None, None
    try:
        res = amparo.responder(pregunta, imagen)
        nuevos = (getattr(agente, "fallos_extraccion", []) or [])[n_fallos:]
        if nuevos:                         # Groq fallo por dentro: el motor diria tutela
            raise ErrorAPI(nuevos[-1].get("error", "fallo de extraccion"))
        pq = res.get("por_que") or {}
        from amparo.nucleo import schema
        reg.update(mecanismo=schema.parse_salida(res["respuesta"]).get("mecanismo"),
                   regla=pq.get("regla"), se_abstuvo=pq.get("se_abstuvo"))
        seg = res.get("segundos") or {}
        for k, campo in (("lectura del documento", "lectura_ms"), ("decisión (M3)", "m3_ms")):
            if seg.get(k) is not None:
                reg[campo] = int(seg[k] * 1000)
        guardar_caches(agente)             # el caso ensayado ya no gasta Groq
    except SinVision as ex:
        res, md, reg["ok"], reg["error"] = None, f"**{ex}**", False, "sin_vision"
    except ErrorAPI as ex:
        res, md, reg["ok"], reg["error"] = None, MENSAJE_API, False, f"api: {ex}"
    except Exception as ex:                                 # noqa: BLE001
        texto = f"{type(ex).__name__}: {ex}"
        es_api = any(s in texto.lower() for s in ("groq", "rate", "429", "connection", "timeout",
                                                   "api"))
        md = MENSAJE_API if es_api else ("**Algo falló al responder.** Intenta de nuevo; "
                                         "si se repite, avísale al equipo.")
        res, reg["ok"], reg["error"] = None, False, texto[:200]
    reg["latencia_ms"] = int((time.perf_counter() - t0) * 1000)
    return res, md, reg


def presentar(res, md_error, reg: dict, generar=None) -> str:
    """El markdown para la persona, y el registro con como se redacto."""
    if res is None:
        return md_error
    t0 = time.perf_counter()
    red = redactar_respuesta(res, generar)
    reg.update(redaccion=red["fuente"], redaccion_valida=red["valido"], redaccion_ms=red["ms"])
    md = formatear_para_usuario(res, red)
    reg["latencia_ms"] = (reg.get("latencia_ms") or 0) + int((time.perf_counter() - t0) * 1000)
    return md


def consultar(amparo, pregunta: str, imagen=None, *, ver_version: str = "",
              generar=None) -> tuple[str, dict]:
    """`(markdown, registro)`: decidir y presentar en una llamada (fuera de
    ZeroGPU). Nunca lanza."""
    res, md, reg = consultar_res(amparo, pregunta, imagen, ver_version=ver_version)
    return presentar(res, md, reg, generar), reg


class ErrorAPI(RuntimeError):
    pass


def guardar_caches(agente) -> None:
    """Las dos caches de M3 a disco: la del agente y la de la reescritura de
    consultas (que tambien llama a Groq)."""
    if agente is None:
        return
    if hasattr(agente, "guardar_cache"):
        agente.guardar_cache()
    tr = getattr(agente, "transformador", None)
    if tr is not None and hasattr(tr, "guardar"):
        tr.guardar()


def recargar_caches(agente) -> None:
    """Las caches de M3 desde disco, encima de lo que haya en memoria.

    En ZeroGPU la funcion `@spaces.GPU` corre en otro proceso: lo que guarda
    en la cache en memoria no vuelve al proceso principal, pero lo que escribe
    a disco si. Sin recargar, un caso ensayado volveria a gastar Groq.
    """
    if agente is None:
        return
    for obj, attr, ruta in ((agente, "_cache", getattr(agente, "_ruta_cache", None)),
                            (getattr(agente, "transformador", None), "cache",
                             getattr(getattr(agente, "transformador", None), "ruta", None))):
        cache = getattr(obj, attr, None)
        if isinstance(cache, dict) and ruta is not None and Path(ruta).exists():
            try:
                cache.update(json.loads(Path(ruta).read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
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
        if reg.get("redaccion"):
            m[f"redaccion_{reg['redaccion']}"] = 1
        for k in ("lectura_ms", "m3_ms", "redaccion_ms"):
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


# ---------------------------------------------------------------------------
# La respuesta en lenguaje natural (solo presentacion)
# ---------------------------------------------------------------------------
# La decision es el bloque de cinco lineas de M3 y no se toca. Encima se pone
# un parrafo legible:
#
#   - con mecanismo: la capa de redaccion de M1 (`finetuning/redaccion.py`),
#     medida en M1 sobre 109 casos (0 normas inventadas; dice el mecanismo en
#     el 99 % y la procedencia en el 100 %; results/m1_redaccion.json), con el
#     MISMO prompt y el mismo generador que se midieron. Si falla Groq, si el
#     candado encuentra una norma intrusa o si `verificacion["valido"]` es
#     False (por ejemplo, el texto no dice el mecanismo), se usa la plantilla.
#   - sin mecanismo (Amparo se abstiene): plantilla fija, sin llamar al
#     redactor. Su prompt obliga a nombrar un mecanismo, y con un "hola"
#     escribiria 100 palabras sobre un caso que no existe.
#
# Lo medido en M1 no es exactamente lo que corre aqui: alla los bloques venian
# del modelo de M1 y la condicion que cambiaria el mecanismo salia del gold;
# aqui vienen del agente de M3 y esa condicion va en None. El candado de normas
# protege igual venga de donde venga el bloque. Se presenta como "medida en M1".

NOMBRES_DERECHO = {
    "salud": "la salud", "peticion": "petición", "seguridad_social": "la seguridad social",
    "habeas_data": "habeas data (tus datos personales)", "debido_proceso": "el debido proceso",
    "educacion": "la educación", "estabilidad_laboral_reforzada": "la estabilidad laboral reforzada",
    "trabajo": "el trabajo", "minimo_vital": "el mínimo vital",
    "libertad_personal": "la libertad personal", "colectivos": "derechos colectivos",
}

HECHOS_LEGIBLES = {
    "privacion_libertad": "hay una persona privada de la libertad",
    "derecho_colectivo": "se afecta un bien colectivo",
    "titular_pide_lo_suyo": "pides la protección de tu propio derecho",
    "acto_general": "se ataca una norma general",
    "dano_consumado": "el daño ya ocurrió",
    "continua_vulneracion": "la vulneración sigue",
    "incumplimiento_normativo": "una autoridad no cumple una norma",
    "afectacion_individual": "hay un derecho tuyo afectado en concreto",
    "otro_medio_judicial": "existe otro proceso judicial para esto",
    "medio_eficaz": "ese otro proceso sirve en tu caso",
    "perjuicio_irremediable": "esperar haría inútil la protección",
    "sujeto_especial_proteccion": "eres sujeto de especial protección",
}

CAMPOS_LEIDOS = {"tipo_documento": "Tipo de documento", "entidad": "Quién lo emite",
                 "fecha": "Fecha", "plazo_dias": "Plazo (días)",
                 "pretension_visible": "Lo que dice el documento"}

AVISO_ABOGADO = "_Orientación automática: no reemplaza la asesoría de un abogado o de un consultorio jurídico._"


def bloque_para_redaccion(bloque: dict) -> dict:
    """El bloque que ve el redactor. En via ordinaria el derecho llega como
    no determinado y sin su articulo: el extractor a veces lo etiqueta mal (el
    "peticion" de un cobro de arriendos), y en prosa fluida ese error convence
    mas que en la ficha. El art. 6.1 del Decreto 2591 se queda."""
    from amparo.sistemas.sistema import ARTICULO_POR_DERECHO
    b = dict(bloque)
    if b.get("mecanismo") == "via_ordinaria":
        art = ARTICULO_POR_DERECHO.get(b.get("derecho") or "")
        b["derecho"] = None
        if art and b.get("fundamento"):
            citas = [c.strip() for c in b["fundamento"].split(";") if c.strip() != art]
            b["fundamento"] = "; ".join(citas) or None
    return b


def plantilla(bloque: dict) -> str:
    """El parrafo fijo, por mecanismo (plan de Tomas). Solo usa los campos del
    bloque. El derecho se nombra solo en tutela."""
    mec = bloque.get("mecanismo")
    acc = bloque.get("accionado") or "quien vulnera tu derecho"
    pret = bloque.get("pretension")
    if mec is None:
        motivo = (bloque.get("razon") or "").split(". ", 1)
        motivo = motivo[1] if len(motivo) > 1 else ""
        texto = ("Con lo que me cuentas no puedo orientarte todavía"
                 + (f": {motivo[0].lower() + motivo[1:]}" if motivo else ".")
                 + ("" if motivo.endswith(".") or not motivo else ".")
                 + " Si tienes un problema concreto con alguien que vulnera un derecho tuyo, "
                   "cuéntame qué pasó, quién lo hizo, desde cuándo y qué quieres lograr.")
        return texto
    if mec == "tutela":
        der = NOMBRES_DERECHO.get(bloque.get("derecho") or "")
        texto = (f"Por lo que cuentas, puedes presentar una **acción de tutela** contra {acc}"
                 + (f" para proteger tu derecho a {der}." if der else "."))
    elif mec == "via_ordinaria":
        razon = bloque.get("razon") or ""
        texto = ("Por lo que cuentas, esto **no se resuelve con una tutela**"
                 + (f": {razon}." if razon else ".")
                 + " El camino es un proceso ante el juez que corresponda (**vía judicial ordinaria**).")
    elif mec == "accion_popular":
        texto = ("Lo que describes afecta un derecho colectivo; el camino es la **acción popular** "
                 f"contra {acc}.")
    elif mec == "accion_cumplimiento":
        texto = ("Lo que pides es que se cumpla una norma; el camino es la **acción de cumplimiento** "
                 f"contra {acc}.")
    elif mec == "habeas_corpus":
        texto = ("Si alguien está privado de la libertad ilegalmente, el camino urgente es el "
                 "**hábeas corpus**: se presenta ante cualquier juez y debe resolverse en 36 horas.")
    else:
        texto = f"El mecanismo que corresponde es: {mec}."
    if pret and pret != "no aplica":
        texto += f" Lo que pedirías: {pret[0].lower() + pret[1:]}."
    return texto


def redactar_respuesta(res: dict, generar=None) -> dict:
    """`{"texto", "fuente", "valido", "ms"}`. Nunca lanza.

    fuente: "modelo" (capa de redaccion de M1, verificada), "plantilla"
    (respaldo) o "plantilla_abstencion" (Amparo no propone mecanismo).
    """
    from amparo.nucleo import schema
    t0 = time.perf_counter()
    bloque = schema.parse_salida(res.get("respuesta") or "")
    if not bloque.get("mecanismo"):
        return {"texto": plantilla(bloque), "fuente": "plantilla_abstencion",
                "valido": None, "ms": 0}
    b = bloque_para_redaccion(bloque)
    if generar is not None:
        try:
            from amparo.finetuning import redaccion as red
            r = red.redactar(generar, b, None, registro="ciudadano", estricto=False)
            if r["verificacion"]["valido"] and r["texto"]:
                return {"texto": r["texto"], "fuente": "modelo", "valido": True,
                        "ms": int((time.perf_counter() - t0) * 1000)}
            valido = False
        except Exception:                                   # noqa: BLE001
            valido = None                                   # Groq no respondio
    else:
        valido = None
    return {"texto": plantilla(b), "fuente": "plantilla", "valido": valido,
            "ms": int((time.perf_counter() - t0) * 1000)}


def formatear_para_usuario(res: dict, redaccion: dict) -> str:
    """Lo que ve la persona: el parrafo, el porque, lo leido del documento y,
    plegada, la ficha tecnica (las cinco lineas evaluadas). `formatear()` de
    M4 no se toca: es la que usan el notebook y el plan B de M4."""
    lineas = ["### Respuesta", "", redaccion["texto"].strip(), "", AVISO_ABOGADO, ""]

    pq = res.get("por_que")
    if pq is not None:
        lineas += ["### Por qué", ""]
        if pq.get("se_abstuvo"):
            lineas.append("- Amparo prefirió **no proponer un mecanismo**: no encontró una situación "
                          "concreta, con alguien a quien dirigir la acción y algo que un juez pudiera ordenar.")
        else:
            hechos = [HECHOS_LEGIBLES.get(h, h) for h in pq.get("hechos") or []]
            if hechos:
                lineas.append("- **Lo que Amparo entendió de tu caso:** " + "; ".join(hechos) + ".")
            lineas.append("- El mecanismo lo decide una regla fija (art. 6 del Decreto 2591 de 1991), "
                          "no el modelo de lenguaje.")
        lineas.append("")

    leido = res.get("leido")
    if leido is not None:
        lineas += [f"### {leido['rotulo']}", ""]
        for aviso in leido["advertencias"]:
            lineas.append(f"> ⚠️ **{aviso}**")
        if leido["advertencias"]:
            lineas.append("")
        if leido["campos"] is not None:
            for k, v in leido["campos"].items():
                lineas.append(f"- **{CAMPOS_LEIDOS.get(k, k)}:** "
                              + (str(v) if v is not None else "_no se aprecia_"))
        else:
            lineas.append(f"_No se pudo leer el documento como datos; el modelo escribió:_ {leido['crudo']}")
        lineas.append("")

    ficha = [f"- {linea.strip()}" for linea in (res.get("respuesta") or "").splitlines() if linea.strip()]
    if pq is not None and not pq.get("se_abstuvo"):
        ficha.append(f"- Regla que cerró el caso: `{pq.get('regla')}`")
        if pq.get("hechos"):
            ficha.append("- Hechos: " + ", ".join(f"`{h}`" for h in pq["hechos"]))
        if pq.get("normas_consultadas"):
            ficha.append("- Normas que consultó el agente: " + "; ".join(pq["normas_consultadas"]))
    fuente = {"modelo": "capa de redacción de M1 (gpt-oss-120b), verificada",
              "plantilla": "plantilla fija", "plantilla_abstencion": "plantilla fija"}
    ficha.append(f"- Texto de arriba: {fuente.get(redaccion['fuente'], redaccion['fuente'])}")
    seg = res.get("segundos") or {}
    tiempos = [f"{k}: {v:.1f} s" for k, v in seg.items() if v is not None]
    if redaccion.get("fuente") == "modelo" and redaccion.get("ms"):
        tiempos.append(f"redacción: {redaccion['ms'] / 1000:.1f} s")
    if tiempos:
        ficha.append("- Tiempos: " + " · ".join(tiempos))
    lineas += ["<details><summary><b>Ficha técnica</b> (la decisión evaluada, tal cual)</summary>", "",
               *ficha, "", "</details>"]
    return "\n".join(lineas)
