"""M5 · S14 · Destilar un componente de Amparo, etapa por etapa.

Sigue el lab de la profe (`sesiones/s14/S14_Lab_Destilacion_RESUELTO.ipynb`),
**Parte B: datos sinteticos + LoRA**, que es la que corresponde cuando el
cuello de botella es el generador. El notebook `m5/S14_destilacion.ipynb`
solo llama a estas funciones.

Por que la Parte B y no la A
----------------------------
La Parte A destila un CLASIFICADOR por logits (ViT -> CNN chica). Amparo no
tiene un clasificador de imagenes: el VLM de M4 lee campos de un documento.
El scorecard de M4 dice donde se va el tiempo (`latencia_por_componente`):
la mayor parte de cada respuesta es M3, el brazo `4 · agente + reglas`, que
llama a gpt-oss-120b por Groq de 3 a 7 veces por caso. Es el "agente ReAct
con 3 tools" de la slide 9 ("es lo que mas tarda"). La slide 15 lo dice:
"B (datos sinteticos + LoRA) si es el generador". Y la slide 12 dice por que
la A no se puede aqui: el profesor es una API y no da logits; la B "sirve
con una API cerrada".

Que se destila exactamente
--------------------------
En el brazo 4 el modelo NO decide el mecanismo: extrae hechos en JSON y el
motor del art. 6 del Decreto 2591 decide (`reglas.decidir`). El estudiante
aprende SOLO esa pieza: relato -> el mismo JSON de hechos que escribe el
profesor, en UNA llamada y sin herramientas. Despues todo es igual: el mismo
`Agente.__call__`, el mismo `decidir`, el mismo `render_salida`. Por eso la
salida del estudiante entra al harness de M2 sin adaptar nada, y por eso el
riesgo es bajo: un estudiante de 0.5 B no tiene que saber derecho, tiene que
marcar 13 booleanos y tres frases cortas. La ley la sigue poniendo el motor,
asi que no puede inventar normas.

Etapas (secciones del lab de la profe entre parentesis):

    preparar                (0)  raiz, carpeta de trabajo, clave de Groq, contrato
    latencia_por_componente (1)  el scorecard de M4: donde se va el tiempo
    armar_profesor          (B1) el brazo 4 real de M3, igual que en M4
    escribir_relatos        (B1) el profesor escribe relatos nuevos por tema
    etiquetar_con_profesor  (B1) el profesor responde: el JSON de hechos
    entrenar_estudiante     (B2) Qwen2.5-0.5B + LoRA, la receta de S04
    medir                   (B3) harness de M2 + latencia p50/p95, los dos
    tabla                   (5)  la tabla antes/despues y el contrato
    casos_perdidos          (5)  donde el profesor acierta y el estudiante no
    guardar                      lo que va al repo (m5/)

Corre en Colab con GPU (T4) y `GROQ_API_KEY`. Lo caro es Groq: cada relato
que etiqueta el profesor cuesta ~5 k tokens. Todo se guarda caso a caso y se
retoma donde quedo: si se acaba el cupo diario, se vuelve a correr la celda.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from amparo.config import RAIZ
from amparo.nucleo import schema
from amparo.nucleo.reglas import HECHOS_EXTRAIBLES, Hechos

# ---------------------------------------------------------------------------
# 1 · El contrato (TODO 1 de la profe). Se escribe ANTES de entrenar y se
# copia al README de M5. "Si no lo escriben antes, despues cualquier
# resultado parece bueno."
# ---------------------------------------------------------------------------
CONTRATO = {
    "componente": "extractor de hechos de M3 (brazo 4: agente gpt-oss-120b por Groq)",
    "metrica": "acierto juridico del harness de M2 sobre los 130 casos de M3 "
               "(eval_set_v3 + eval_set_m3)",
    # La slide 12: "-2 puntos suele ser aceptable; -15 no". Se fija en 5 y no
    # en 2 porque el profesor mismo no es determinista: en M4 el mismo caso
    # cambio de via entre repeticiones (13/18 en las dos condiciones). Un
    # contrato mas estrecho que el ruido del profesor no se puede verificar.
    # PUNTOS, no porcentaje relativo: 67.5 % -> 62.5 % es perder 5.
    "acepto_perder_puntos": 5,
    # Innegociable y verificable: la norma la pone el motor, no el modelo.
    "alucinacion_maxima": 0.0,
    # Los adversariales son la fortaleza del brazo 4 (73.8 % en M3) y lo
    # primero que un estudiante pierde o hereda mal (slide 19). Con 42 casos,
    # 8 puntos son 3 casos: perder 4 ya incumple.
    "acepto_perder_puntos_adversarial": 8,
    "quiero_ganar": "M3 al menos 3x mas rapido (mediana por caso) y el 95 % de "
                    "los casos en 5 s o menos, sin depender de la API",
    "quiero_ganar_x": 3.0,
    # Solo M3: el VLM (~3.7 s) no se destila; se ataca en S15 (cuantizar).
    "p95_maximo_s": 5.0,
}

PROFESOR = "openai/gpt-oss-120b"          # el del brazo 4 (agente.MODELO)
# gpt-oss-120b: 117 B parametros, 5.1 B activos por token (mezcla de expertos).
# Licencia Apache 2.0: permite usar sus salidas para entrenar otro modelo
# (slide 19: con OpenAI/Anthropic/Google cerrados NO se puede).
PARAMETROS_PROFESOR = 117e9
LICENCIA_PROFESOR = "Apache 2.0 (gpt-oss-120b)"
ESTUDIANTE = "Qwen/Qwen2.5-0.5B-Instruct"  # el de la Parte B del lab
LICENCIA_ESTUDIANTE = "Apache 2.0 (Qwen2.5-0.5B-Instruct)"

# Temperatura. En la Parte B no hay temperatura de destilacion (eso es la
# T de la KL de la Parte A, que necesita logits). Hay dos temperaturas de
# GENERACION, y se eligen para bajar el riesgo:
T_RELATOS = 0.7    # el profesor escribe relatos: 0.7 como en el lab -> variedad
T_RESPUESTA = 0.0  # el profesor responde: 0, seed 42 (ya es asi en agente.py)
#                    -> la etiqueta es reproducible y no se le enseña ruido
N_POR_TEMA = 2     # relatos nuevos por categoria del dataset (131 categorias)
UMBRAL_FUGA = 0.5  # coseno TF-IDF maximo contra el eval set; arriba se descarta
SEMILLA = 42

# La receta de S04 (lab de la profe), con lo que M1 aprendio a la mala:
# perdida solo en la respuesta y el mejor checkpoint por eval_loss.
LORA = dict(r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05, task_type="CAUSAL_LM")
EPOCAS = 3          # "2-3 epocas" (lab, B2)
LR = 2e-4           # S04
MAX_NUEVOS = 160    # tokens de la respuesta del estudiante

CARPETA_REPO = RAIZ / "m5"


# ---------------------------------------------------------------------------
# El prompt del estudiante. Corto a proposito: el prompt se procesa en cada
# llamada y la latencia es justo lo que se quiere bajar.
# ---------------------------------------------------------------------------
_CAMPOS = {
    "privacion_libertad": "alguien detenido sin orden, sin ver a un juez a tiempo o despues de cumplir la pena",
    "derecho_colectivo": "dano o amenaza actual a un bien colectivo (ambiente, espacio publico, recursos publicos)",
    "titular_pide_lo_suyo": "dentro de lo colectivo, el solicitante reclama SU propio derecho",
    "acto_general": "ATACA una norma o acto general para anularlo (pedir que se cumpla NO es esto)",
    "dano_consumado": "el dano ya ocurrio del todo",
    "continua_vulneracion": "la vulneracion sigue ocurriendo",
    "incumplimiento_normativo": "pide que una autoridad cumpla una norma o acto que no ejecuta",
    "afectacion_individual": "un derecho fundamental DEL SOLICITANTE afectado en concreto",
    "otro_medio_judicial": "existe otro proceso judicial para el asunto",
    "perjuicio_irremediable": "esperar el proceso ordinario haria inutil la proteccion",
    "sujeto_especial_proteccion": "menor, adulto mayor, discapacidad, embarazo, desplazado o debilidad manifiesta",
}


def sistema_estudiante() -> str:
    campos = "\n".join(f"- {k}: {v}" for k, v in _CAMPOS.items())
    return (
        "Lees el relato de un ciudadano colombiano y devuelves SOLO un JSON con "
        "cuestiones de hecho. No decides el mecanismo.\n"
        "Incluye como true solo los hechos que se cumplen:\n" + campos + "\n"
        "Incluye \"medio_eficaz\": false solo si el otro medio NO sirve en concreto.\n"
        "Siempre: \"derecho\" (una de: " + ", ".join(sorted(schema.DERECHOS)) + "), "
        "\"accionado\" y \"pretension\" (una frase que empieza por un verbo).\n"
        "Si no hay caso que triar: \"caso_triable\": false y \"motivo_no_triable\"."
    )


def mensajes_estudiante(relato: str) -> list[dict]:
    return [{"role": "system", "content": sistema_estudiante()},
            {"role": "user", "content": relato}]


def objetivo(hechos: Hechos, libres: dict) -> dict:
    """La respuesta del profesor, en el JSON que aprende el estudiante.

    COMPACTO: solo los hechos que se apartan del valor por defecto. Es el
    mismo JSON que lee `Agente._hechos` (lo que falta es False, y
    `medio_eficaz` que falta es True), con ~60 tokens en vez de ~170. Cada
    token que el estudiante no tiene que escribir es latencia que no se paga.
    """
    base = Hechos()
    d = {k: getattr(hechos, k) for k in HECHOS_EXTRAIBLES
         if getattr(hechos, k) != getattr(base, k)}
    d.update(derecho=libres["derecho"], accionado=libres["accionado"],
             pretension=libres["pretension"])
    if libres.get("no_triable"):
        d.update(caso_triable=False, motivo_no_triable=libres.get("motivo_no_triable", ""))
    return d


def a_texto(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------------------
# El estudiante, con la misma interfaz que el profesor
# ---------------------------------------------------------------------------
class _Respuesta:
    """Lo minimo de una respuesta de Groq que lee `Agente._hechos`."""
    def __init__(self, texto: str):
        mensaje = type("M", (), {"content": texto})()
        self.choices = [type("C", (), {"message": mensaje})()]
        self.usage = None


class ClienteEstudiante:
    """El estudiante "habla como Groq": `chat.completions.create(...)`.

    Asi `Agente._hechos` corre SIN CAMBIOS sobre el estudiante: mismo parseo,
    mismos valores por defecto, misma valvula de abstencion. Lo unico que
    cambia es quien escribe el JSON. El prompt largo del profesor se ignora:
    el estudiante se entreno con el suyo.
    """
    def __init__(self, generar):
        self.generar = generar
        self.chat = type("Chat", (), {})()
        self.chat.completions = type("Comp", (), {"create": self._create})()

    def _create(self, *, messages, **_kw):
        usuario = messages[-1]["content"]
        m = re.search(r"RELATO:\n(.*?)\n\nOBSERVACIONES", usuario, re.DOTALL)
        return _Respuesta(self.generar(m.group(1) if m else usuario))


def agente_estudiante(generar, etiqueta: str = "estudiante · Qwen2.5-0.5B + LoRA"):
    """Un `Agente` cuyo bucle de herramientas no existe y cuyo extractor es
    el estudiante. `__call__`, `decidir` y `render_salida` son los de M3."""
    from amparo.sistemas.agente import Agente

    class AgenteEstudiante(Agente):
        def _bucle(self, relato):
            info = {"pasos": 0, "agotado": False, "registros": [],
                    "cierre": "estudiante: una llamada, sin herramientas"}
            return [{"role": "system", "content": ""},
                    {"role": "user", "content": relato}], info

    return AgenteEstudiante(ClienteEstudiante(generar), indice=None, etiqueta=etiqueta)


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------
@dataclass
class Contexto:
    carpeta: Path = RAIZ / "runs" / "m5"
    contrato: dict = field(default_factory=lambda: dict(CONTRATO))
    profesor: object = None          # responder_m3 (relato -> salida)
    agente_profesor: object = None
    relatos: list = field(default_factory=list)
    pares: list = field(default_factory=list)
    tokenizer: object = None
    estudiante: object = None        # el modelo, ya fusionado
    generar: object = None           # relato -> JSON (texto)
    sistema_estudiante: object = None
    n_parametros_estudiante: int = 0
    eval_set: list = field(default_factory=list)
    medidas: dict = field(default_factory=dict)
    entrenamiento: dict = field(default_factory=dict)

    def ruta(self, nombre: str) -> Path:
        self.carpeta.mkdir(parents=True, exist_ok=True)
        return self.carpeta / nombre


def _leer(ruta: Path, defecto):
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else defecto


def _escribir(ruta: Path, datos) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1),
                    encoding="utf-8", newline="\n")


def _es_cupo(ex) -> bool:
    t = f"{type(ex).__name__} {ex}".lower()
    return "ratelimit" in t or "rate limit" in t or "429" in t


class CupoAgotado(RuntimeError):
    """Groq dijo que no hay mas cupo. Lo hecho ya esta en disco."""


# ---------------------------------------------------------------------------
# 0 · Setup
# ---------------------------------------------------------------------------
def preparar(carpeta: str | Path | None = None, *, exigir_clave: bool = True) -> Contexto:
    """`carpeta` es donde viven los intermedios caros (relatos, pares, cache
    del profesor, adaptador). En Colab conviene una carpeta de Drive para que
    sobrevivan al reinicio; por defecto, `runs/m5/` (ignorada por git)."""
    from amparo.ejecucion import entorno
    os.chdir(RAIZ)
    ctx = Contexto(carpeta=Path(carpeta) if carpeta else RAIZ / "runs" / "m5")
    ctx.carpeta.mkdir(parents=True, exist_ok=True)
    print("raiz:", RAIZ)
    print("carpeta de trabajo:", ctx.carpeta)
    if not entorno.cargar_clave_groq() and exigir_clave:
        raise RuntimeError("Falta GROQ_API_KEY: el profesor es el brazo 4 de M3, por Groq.")
    try:
        import torch
        print("device:", "cuda · " + torch.cuda.get_device_name(0)
              if torch.cuda.is_available() else "cpu (el estudiante necesita GPU)")
    except ImportError:
        print("torch no esta instalado")
    print("CONTRATO:", json.dumps(ctx.contrato, ensure_ascii=False, indent=1))
    return ctx


# ---------------------------------------------------------------------------
# 1 · Que componente: el scorecard de M4 (slide 15, paso 1)
# ---------------------------------------------------------------------------
def _pct(v: list[float], q: float) -> float:
    s = sorted(v)
    if not s:
        return float("nan")
    i = min(len(s) - 1, max(0, round(q * (len(s) - 1))))
    return s[i]


def corrida_m4_con_tiempos(raiz: Path = RAIZ) -> tuple[Path, Path]:
    """La corrida de M4 mas reciente cuyas trazas traen `segundos_ver`.

    La corrida oficial del 25 de octubre (`m4/trazas_m4.json`) no medía el
    VLM aparte; las del 1 de noviembre (`m4/corridas/*_demo/`, en `main`) si.
    """
    candidatas = sorted((raiz / "m4" / "corridas").glob("*/trazas_m4.json"), reverse=True)
    candidatas.append(raiz / "m4" / "trazas_m4.json")
    for tr in candidatas:
        if not tr.exists():
            continue
        d = json.loads(tr.read_text(encoding="utf-8"))
        if any(isinstance(v, dict) and "segundos_ver" in v for v in d.values()):
            return tr.parent / "scorecard_m4.csv", tr
    raise FileNotFoundError(
        "Ninguna corrida de M4 trae `segundos_ver` en sus trazas. Las de la demo "
        "(m4/corridas/20261101T*_demo/) estan en `main`: fusionen main en esta rama.")


def latencia_por_componente(scorecard: str | Path | None = None,
                            trazas: str | Path | None = None) -> dict:
    """La columna `segundos` del scorecard de M4, partida en sus dos piezas.

    `segundos` es VLM + M3 por caso; `segundos_ver` (trazas) es solo el VLM.
    La resta es M3. Devuelve mediana, p95, minimo y maximo de cada pieza y la
    parte de la mediana total que se lleva cada una. Sin rutas, usa la corrida
    de M4 mas reciente que midio el VLM aparte.
    """
    import csv
    if scorecard is None or trazas is None:
        scorecard, trazas = corrida_m4_con_tiempos()
        print("corrida de M4:", Path(trazas).parent.relative_to(RAIZ))
    filas = list(csv.DictReader(Path(scorecard).open(encoding="utf-8", newline="")))
    tr = json.loads(Path(trazas).read_text(encoding="utf-8"))
    total, ver, m3 = [], [], []
    for f in filas:
        t = float(f["segundos"])
        v = (tr.get(f["id"]) or {}).get("segundos_ver")
        if v is None:
            continue
        total.append(t); ver.append(v); m3.append(t - v)
    med = _pct(total, 0.5)
    out = {"n": len(total), "componentes": {}, "fuente": str(trazas)}
    for nombre, v in (("VLM Qwen2-VL-2B (lectura del documento)", ver),
                      ("M3 brazo 4 (agente gpt-oss-120b + reglas)", m3),
                      ("total por caso", total)):
        out["componentes"][nombre] = {
            "mediana_s": round(_pct(v, 0.5), 2), "p95_s": round(_pct(v, 0.95), 2),
            "min_s": round(min(v), 2), "max_s": round(max(v), 2),
            "parte_de_la_mediana": round(_pct(v, 0.5) / med, 2) if med else None}
    piezas = {k: c for k, c in out["componentes"].items() if k != "total por caso"}
    out["mas_lento"] = max(piezas, key=lambda k: piezas[k]["mediana_s"])
    out["mas_variable"] = max(piezas, key=lambda k: piezas[k]["max_s"] - piezas[k]["min_s"])
    print(f"{'componente':45s} {'mediana':>8s} {'p95':>6s} {'min':>6s} {'max':>6s} {'parte':>6s}")
    for k, c in out["componentes"].items():
        print(f"{k:45s} {c['mediana_s']:8.2f} {c['p95_s']:6.2f} {c['min_s']:6.2f} "
              f"{c['max_s']:6.2f} {c['parte_de_la_mediana'] or 0:6.0%}")
    print(f"\nmas lento: {out['mas_lento']}\nmas variable: {out['mas_variable']}")
    return out


# ---------------------------------------------------------------------------
# B1 · El profesor
# ---------------------------------------------------------------------------
def armar_profesor(ctx: Contexto, **kwargs) -> Contexto:
    """El brazo 4 real de M3, armado igual que en M4 (`enchufe`), con su
    cache en la carpeta de trabajo para poder retomar."""
    from amparo.multimodal import enchufe
    ctx.profesor, ctx.agente_profesor = enchufe.construir_responder_m3(
        cache_dir=ctx.carpeta / "cache_profesor", **kwargs)
    print("profesor listo:", enchufe.SISTEMA_M3, "·", PROFESOR)
    return ctx


def _cliente_groq():
    from groq import Groq
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def _prompt_relato(referencia: str) -> str:
    return ("Escribes casos para entrenar un sistema de triaje de acciones "
            "constitucionales en Colombia.\n\nSituacion de referencia (NO la copies: "
            "cambia personas, lugares, cifras y detalles, y conserva el mismo tipo de "
            f"problema):\n{referencia}\n\nEscribe UN relato nuevo, en primera persona, de "
            "2 a 5 frases, como lo contaria un ciudadano colombiano sin formacion "
            "juridica. No cites leyes ni articulos. Solo el relato.")


def fuga_contra_eval(textos: list[str], eval_set: list[dict]) -> list[float]:
    """El coseno TF-IDF maximo de cada texto contra los relatos del eval set.

    Un relato sintetico que se parece demasiado a un caso del eval set es
    fuga: el estudiante lo veria en el entrenamiento y la tabla mediria
    memoria. Entre train y eval de M1 el maximo era 0.35.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    ev = [e["relato"] for e in eval_set]
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1).fit(ev + textos)
    sim = cosine_similarity(vec.transform(textos), vec.transform(ev))
    return [float(f.max()) if f.size else 0.0 for f in sim]


def cargar_eval() -> list[dict]:
    """Los mismos casos con los que se midio el brazo 4 en M3 (`casos_todos`)."""
    return (schema.cargar(archivo="eval_set_v3.json")
            + schema.cargar(archivo="eval_set_m3.json"))


def escribir_relatos(ctx: Contexto, n_por_tema: int = N_POR_TEMA, cliente=None,
                     temperatura: float = T_RELATOS) -> list[dict]:
    """El profesor escribe relatos nuevos, `n_por_tema` por cada categoria
    del dataset de M1 (la celda B1 de la profe con TEMAS = categorias).

    La referencia de cada tema es un relato de train o validation, nunca del
    eval set. Al final se descartan los que se parecen demasiado al eval set
    (`UMBRAL_FUGA`). Se guarda en disco tras cada relato.
    """
    ruta = ctx.ruta("relatos_sinteticos.json")
    hechos = {r["id"]: r for r in _leer(ruta, [])}
    cliente = cliente or _cliente_groq()
    por_tema: dict[str, dict] = {}
    for e in schema.cargar():                       # train + validation
        por_tema.setdefault(e["categoria"], e)
    pendientes = [(t, i) for t in sorted(por_tema) for i in range(n_por_tema)
                  if f"S_{t}_{i}" not in hechos]
    print(f"{len(por_tema)} temas · {n_por_tema} por tema · ya hechos {len(hechos)} · "
          f"faltan {len(pendientes)}")
    for k, (tema, i) in enumerate(pendientes, 1):
        ref = por_tema[tema]
        try:
            r = cliente.chat.completions.create(
                model=PROFESOR, temperature=temperatura, max_tokens=900,
                seed=SEMILLA + i, reasoning_effort="low",
                messages=[{"role": "user", "content": _prompt_relato(ref["relato"])}])
        except Exception as ex:                           # noqa: BLE001
            _escribir(ruta, list(hechos.values()))
            if _es_cupo(ex):
                raise CupoAgotado(f"Groq sin cupo tras {len(hechos)} relatos. "
                                  "Vuelve a correr la celda: retoma aqui.") from ex
            print(f"  fallo {tema}/{i}: {type(ex).__name__}: {str(ex)[:120]}")
            continue
        texto = (r.choices[0].message.content or "").strip().strip('"').strip()
        if len(texto) < 40:
            continue
        hechos[f"S_{tema}_{i}"] = {"id": f"S_{tema}_{i}", "categoria": tema,
                                   "referencia": ref["id"], "relato": texto,
                                   "split": "train", "origen": "sintetico_profesor"}
        _escribir(ruta, list(hechos.values()))
        print(f"  {k}/{len(pendientes)} relatos", end="\r", flush=True)

    rel = list(hechos.values())
    ctx.eval_set = ctx.eval_set or cargar_eval()
    if rel:
        sims = fuga_contra_eval([r["relato"] for r in rel], ctx.eval_set)
        for r, s in zip(rel, sims):
            r["coseno_max_eval"] = round(s, 3)
        fuera = [r for r in rel if r["coseno_max_eval"] >= UMBRAL_FUGA]
        rel = [r for r in rel if r["coseno_max_eval"] < UMBRAL_FUGA]
        print(f"\n{len(rel)} relatos sinteticos · {len(fuera)} descartados por "
              f"parecerse al eval set (coseno >= {UMBRAL_FUGA}) · "
              f"coseno maximo que queda: {max(sims) if sims else 0:.2f}")
    ctx.relatos = rel
    return rel


def etiquetar_con_profesor(ctx: Contexto, incluir_dataset: bool = True,
                           guardar_cada: int = 1) -> list[dict]:
    """El profesor responde cada relato: su JSON de hechos.

    Los relatos son los sinteticos de `escribir_relatos` mas, si
    `incluir_dataset`, los 160 de train/validation de M1 (validation se queda
    como validation: con ellos se elige el checkpoint). La etiqueta es la del
    PROFESOR, no la gold: esto es destilacion, el estudiante imita al grande.

    Se llama a las dos mitades del agente (`_bucle` y `_hechos`) y no a
    `__call__`, porque lo que se aprende es el JSON, no las cinco lineas. Si
    la extraccion fallo por dentro (el agente la cuenta y sigue con valores
    por defecto), el par se DESCARTA: un par con hechos por defecto le
    enseñaria al estudiante a no ver nada.
    """
    assert ctx.agente_profesor is not None, "falta armar_profesor(ctx)"
    ag = ctx.agente_profesor
    ruta = ctx.ruta("pares_profesor.json")
    pares = {p["id"]: p for p in _leer(ruta, [])}
    relatos = list(ctx.relatos)
    if incluir_dataset:
        relatos += [{"id": e["id"], "categoria": e["categoria"], "relato": e["relato"],
                     "split": e["split"], "origen": "dataset_m1"} for e in schema.cargar()]
    pendientes = [r for r in relatos if r["id"] not in pares]
    print(f"{len(relatos)} relatos · etiquetados {len(pares)} · faltan {len(pendientes)}")
    descartados, t0 = [], time.perf_counter()
    for k, r in enumerate(pendientes, 1):
        n_fallos = len(ag.fallos_extraccion)
        n_mal = ag.contadores.get("hechos_no_parseados", 0)
        try:
            mensajes, info = ag._bucle(r["relato"])
            hechos, libres = ag._hechos(mensajes, r["relato"])
        except Exception as ex:                           # noqa: BLE001
            ag.guardar_cache(); _escribir(ruta, list(pares.values()))
            if _es_cupo(ex):
                raise CupoAgotado(f"Groq sin cupo tras {len(pares)} pares. "
                                  "Vuelve a correr la celda: retoma aqui.") from ex
            descartados.append({"id": r["id"], "por": f"{type(ex).__name__}: {str(ex)[:100]}"})
            continue
        nuevos = ag.fallos_extraccion[n_fallos:]
        if any(_es_cupo(f.get("error", "") + " " + f.get("detalle", "")) for f in nuevos):
            ag.guardar_cache(); _escribir(ruta, list(pares.values()))
            raise CupoAgotado(f"Groq sin cupo tras {len(pares)} pares. Vuelve a correr la celda.")
        if nuevos or ag.contadores.get("hechos_no_parseados", 0) > n_mal:
            descartados.append({"id": r["id"], "por": "la extraccion del profesor fallo"})
            continue
        pares[r["id"]] = {**r, "objetivo": objetivo(hechos, libres),
                          "pasos_profesor": info.get("pasos")}
        if k % guardar_cada == 0 or k == len(pendientes):
            ag.guardar_cache(); _escribir(ruta, list(pares.values()))
        dt = (time.perf_counter() - t0) / k
        print(f"  {k}/{len(pendientes)} · {dt:.1f} s/relato · ETA "
              f"{dt * (len(pendientes) - k) / 60:.0f} min", end="\r", flush=True)
    ag.guardar_cache(); _escribir(ruta, list(pares.values()))
    if descartados:
        _escribir(ctx.ruta("pares_descartados.json"), descartados)
    ctx.pares = list(pares.values())
    n_tr = sum(p["split"] == "train" for p in ctx.pares)
    print(f"\n{len(ctx.pares)} pares ({n_tr} train · {len(ctx.pares) - n_tr} validation) · "
          f"{len(descartados)} descartados")
    return ctx.pares


def acuerdo_profesor_gold(ctx: Contexto) -> dict:
    """Etiqueta del profesor contra la etiqueta del dataset (la "dura").

    Es la celda de la profe que compara la etiqueta dura con la del
    profesor, en version Amparo: sobre los relatos de M1, ¿cuantas veces el
    motor, con los hechos del PROFESOR, llega al mecanismo gold? Lo que el
    profesor falla aqui es ruido que el estudiante va a heredar (slide 19:
    "los sesgos se heredan").
    """
    from amparo.nucleo.reglas import decidir
    gold = {e["id"]: e for e in schema.cargar()}
    pares = [p for p in (ctx.pares or []) if p["id"] in gold and gold[p["id"]].get("mecanismo")]
    if not pares:
        print("no hay pares del dataset etiquetados todavia")
        return {}
    acierta, por_mec = 0, {}
    for p in pares:
        o = p["objetivo"]
        h = Hechos(**{k: o.get(k, getattr(Hechos(), k)) for k in HECHOS_EXTRAIBLES})
        g = gold[p["id"]]["mecanismo"]
        ok = bool(o.get("caso_triable", True)) and decidir(h).mecanismo == g
        acierta += ok
        t = por_mec.setdefault(g, [0, 0]); t[0] += ok; t[1] += 1
    out = {"n": len(pares), "acierto": round(acierta / len(pares), 3),
           "por_mecanismo": {k: f"{a}/{n}" for k, (a, n) in sorted(por_mec.items())}}
    print(f"el profesor (con el motor) acierta el mecanismo gold en {acierta}/{len(pares)} "
          f"relatos de M1 ({out['acierto']:.0%}). Por mecanismo: {out['por_mecanismo']}")
    return out


# ---------------------------------------------------------------------------
# B2 · El estudiante: Qwen2.5-0.5B + LoRA, la receta de S04
# ---------------------------------------------------------------------------
def _construir(par: dict, tokenizer, max_len: int) -> dict:
    """Perdida SOLO en la respuesta (el prompt va enmascarado con -100),
    igual que `finetuning.datos.construir` de M1."""
    prompt = tokenizer.apply_chat_template(mensajes_estudiante(par["relato"]),
                                           tokenize=False, add_generation_prompt=True)
    full = prompt + a_texto(par["objetivo"]) + tokenizer.eos_token
    ids_p = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    ids_f = tokenizer(full, add_special_tokens=False, truncation=True,
                      max_length=max_len)["input_ids"]
    labels = ([-100] * len(ids_p) + ids_f[len(ids_p):])[:len(ids_f)]
    return {"input_ids": ids_f, "attention_mask": [1] * len(ids_f), "labels": labels}


def entrenar_estudiante(ctx: Contexto, modelo: str = ESTUDIANTE, epocas: int = EPOCAS,
                        lora: dict | None = None) -> Contexto:
    """B2 del lab: el estudiante se fine-tunea con LoRA sobre los pares.

    De la receta de S04 (`r=8`, `q_proj`/`v_proj`, `lr=2e-4`) se cambia solo
    lo que M1 ya pago: la perdida va solo en la respuesta, se evalua por
    epoca contra validation y se carga el mejor checkpoint. Se carga en fp32
    y se entrena con fp16 mixto: la T4 no tiene bf16, y con los pesos en fp16
    el escalador de gradientes falla.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from datasets import Dataset
    from amparo.finetuning import datos, entrenamiento

    pares = ctx.pares or _leer(ctx.ruta("pares_profesor.json"), [])
    tr = [p for p in pares if p["split"] == "train"]
    va = [p for p in pares if p["split"] != "train"]
    assert tr and va, "faltan pares: corre etiquetar_con_profesor(ctx)"
    torch.manual_seed(SEMILLA)
    tok = AutoTokenizer.from_pretrained(modelo)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(modelo, torch_dtype=torch.float32)
    if torch.cuda.is_available():
        model = model.to("cuda")
    model, lora_cfg = entrenamiento.aplicar_lora(model, lora or LORA)

    largos = [len(_construir(p, tok, 10_000)["input_ids"]) for p in pares]
    max_len = max(largos) + 8                       # se MIDE (ver datos.medir_max_len)
    ds_tr = Dataset.from_list([_construir(p, tok, max_len) for p in tr])
    ds_va = Dataset.from_list([_construir(p, tok, max_len) for p in va])
    print(f"train {len(ds_tr)} · validation {len(ds_va)} · max_len {max_len}")

    hp = entrenamiento.hiperparametros(SEMILLA, salida=str(ctx.carpeta / "entrenamiento"))
    hp.update(learning_rate=LR, num_train_epochs=epocas, per_device_train_batch_size=8,
              gradient_accumulation_steps=1, per_device_eval_batch_size=8,
              logging_steps=5, gradient_checkpointing=False,
              bf16=False, fp16=torch.cuda.is_available())
    hp.pop("gradient_checkpointing_kwargs", None)
    trainer, hp, omitidos, _trad, _parada = entrenamiento.crear_trainer(
        model, ds_tr, ds_va, datos.collate_para(tok), hp)
    t0 = time.perf_counter()
    trainer.train()
    seg = time.perf_counter() - t0
    sel = entrenamiento.seleccionar_checkpoint(trainer.state.log_history, epocas)

    carpeta_lora = ctx.carpeta / "estudiante_lora"
    model.save_pretrained(str(carpeta_lora)); tok.save_pretrained(str(carpeta_lora))
    model = model.merge_and_unload()                # inferencia sin la capa LoRA
    if torch.cuda.is_available():
        model = model.half()
    model.eval()
    ctx.tokenizer, ctx.estudiante = tok, model
    ctx.n_parametros_estudiante = sum(p.numel() for p in model.parameters())
    ctx.generar = generador(model, tok)
    ctx.sistema_estudiante = agente_estudiante(ctx.generar)
    ctx.entrenamiento = {
        "modelo_base": modelo, "licencia": LICENCIA_ESTUDIANTE,
        "lora": {k: v for k, v in (lora or LORA).items()},
        "epocas": epocas, "lr": LR, "max_len": max_len,
        "n_train": len(ds_tr), "n_validation": len(ds_va),
        "segundos_entrenamiento": round(seg, 1), "seleccion": sel,
        "omitidos": list(omitidos), "adaptador": str(carpeta_lora)}
    _escribir(ctx.ruta("entrenamiento.json"), ctx.entrenamiento)
    print(f"estudiante: {ctx.n_parametros_estudiante / 1e6:.0f} M parametros · "
          f"entrenado en {seg / 60:.1f} min")
    return ctx


def cargar_estudiante(ctx: Contexto, modelo: str = ESTUDIANTE) -> Contexto:
    """Para retomar sin reentrenar: base + el adaptador guardado."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    carpeta_lora = ctx.carpeta / "estudiante_lora"
    tok = AutoTokenizer.from_pretrained(str(carpeta_lora))
    base = AutoModelForCausalLM.from_pretrained(
        modelo, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32)
    if torch.cuda.is_available():
        base = base.to("cuda")
    model = PeftModel.from_pretrained(base, str(carpeta_lora)).merge_and_unload().eval()
    ctx.tokenizer, ctx.estudiante = tok, model
    ctx.n_parametros_estudiante = sum(p.numel() for p in model.parameters())
    ctx.generar = generador(model, tok)
    ctx.sistema_estudiante = agente_estudiante(ctx.generar)
    ctx.entrenamiento = _leer(ctx.ruta("entrenamiento.json"), {})
    print(f"estudiante cargado de {carpeta_lora}")
    return ctx


def generador(model, tokenizer, max_nuevos: int = MAX_NUEVOS):
    """relato -> el JSON del estudiante. Codicioso (`do_sample=False`), como
    el `preguntar` de S04: en produccion la temperatura vuelve a 0."""
    import torch

    @torch.no_grad()
    def generar(relato: str) -> str:
        texto = tokenizer.apply_chat_template(mensajes_estudiante(relato),
                                              tokenize=False, add_generation_prompt=True)
        ent = tokenizer(texto, return_tensors="pt").to(model.device)
        out = model.generate(**ent, max_new_tokens=max_nuevos, do_sample=False,
                             pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)
        return tokenizer.decode(out[0][ent["input_ids"].shape[1]:], skip_special_tokens=True)
    return generar


# ---------------------------------------------------------------------------
# B3 · Medir con el harness de M2, en la misma maquina
# ---------------------------------------------------------------------------
def correr_con_reloj(sistema, casos: list[dict], ruta: Path, nombre: str,
                     agente=None) -> dict:
    """Corre `sistema(relato)` caso a caso, con su latencia, y guarda tras
    cada caso para poder retomar. Un caso que falla queda con salida vacia
    (como `brazos.correr_brazo`): no se le inventa una respuesta.

    `agente`: el `Agente` detras de `sistema`, si lo hay. Hace falta porque
    `Agente._hechos` NO lanza el error cuando Groq falla en la extraccion: lo
    cuenta en `fallos_extraccion` y sigue con los hechos por defecto, que el
    motor convierte en tutela. Sin mirar ese contador, un caso sin cupo se
    guardaria como si el profesor hubiera respondido tutela. Si fue el cupo,
    el caso NO se guarda y se para; si fue otro error, el caso queda vacio y
    marcado, como cualquier fallo.
    """
    hecho = _leer(ruta, {})
    pend = [e for e in casos if e["id"] not in hecho]
    print(f"{nombre}: {len(casos) - len(pend)} ya medidos · faltan {len(pend)}")
    for k, e in enumerate(pend, 1):
        n_fallos = len(getattr(agente, "fallos_extraccion", []) or [])
        t0 = time.perf_counter()
        try:
            salida, error = sistema(e["relato"]), None
        except Exception as ex:                           # noqa: BLE001
            if _es_cupo(ex):
                _escribir(ruta, hecho)
                raise CupoAgotado(f"Groq sin cupo midiendo {nombre}. Vuelve a correr.") from ex
            salida, error = "", f"{type(ex).__name__}: {str(ex)[:120]}"
        nuevos = (getattr(agente, "fallos_extraccion", []) or [])[n_fallos:]
        if any(_es_cupo(f.get("error", "") + " " + f.get("detalle", "")) for f in nuevos):
            _escribir(ruta, hecho)
            raise CupoAgotado(f"Groq sin cupo midiendo {nombre} (en la extraccion de "
                              f"{e['id']}, que no se guarda). Vuelve a correr.")
        if nuevos and error is None:
            salida, error = "", "la extraccion fallo: " + nuevos[-1].get("error", "")
        hecho[e["id"]] = {"salida": salida, "segundos": round(time.perf_counter() - t0, 3),
                          "error": error}
        _escribir(ruta, hecho)
        print(f"  {nombre}: {k}/{len(pend)}", end="\r", flush=True)
    print()
    return hecho


def medir(ctx: Contexto, n: int | None = None, juez=None) -> dict:
    """B3 del lab: `harness(eval_set, sistema)` para el profesor y para el
    estudiante, mas latencia p50/p95 por caso.

    El profesor se mide con un agente NUEVO y la cache vacia: con la cache de
    los pares, una respuesta repetida tardaria cero y la latencia mediria la
    cache, no el sistema (la misma trampa que encontro la revision de M4).
    `n` recorta el eval set para una prueba rapida; la tabla del README va
    con los 130.
    """
    from amparo.evaluacion import harness
    from amparo.multimodal import enchufe
    assert ctx.sistema_estudiante is not None, "falta entrenar_estudiante o cargar_estudiante"
    ctx.eval_set = ctx.eval_set or cargar_eval()
    casos = ctx.eval_set[:n] if n else ctx.eval_set

    profesor_eval, ag_eval = enchufe.construir_responder_m3(
        indice=getattr(ctx.agente_profesor, "indice", None),
        cache_dir=ctx.carpeta / "cache_eval_sin_usar")
    enchufe.vaciar_caches(ag_eval)
    sufijo = f"_{n}" if n else ""
    n_mal = ctx.sistema_estudiante.contadores.get("hechos_no_parseados", 0)
    medidos = {
        "profesor": correr_con_reloj(profesor_eval, casos,
                                     ctx.ruta(f"eval_profesor{sufijo}.json"), "profesor",
                                     agente=ag_eval),
        "estudiante": correr_con_reloj(ctx.sistema_estudiante, casos,
                                       ctx.ruta(f"eval_estudiante{sufijo}.json"), "estudiante"),
    }
    ctx.medidas = {}
    for quien, hecho in medidos.items():
        salidas = [hecho[e["id"]]["salida"] for e in casos]
        seg = [hecho[e["id"]]["segundos"] for e in casos]
        sc = harness.harness(casos, salidas, quien, juez=juez)
        ctx.medidas[quien] = {
            "salidas": salidas, "segundos": seg, "scorecard": sc,
            "aciertos": harness.acierto_por_item(salidas, casos),
            "fallos": sum(1 for e in casos if hecho[e["id"]]["error"])}
    # Un JSON que no parsea NO es una abstencion: `_hechos` sigue con los
    # valores por defecto y el motor dice tutela. Se cuenta para no confundir
    # "el estudiante decidio tutela" con "el estudiante no escribio nada legible".
    ctx.medidas["estudiante"]["json_invalido"] = (
        ctx.sistema_estudiante.contadores.get("hechos_no_parseados", 0) - n_mal)
    ctx.medidas["profesor"]["json_invalido"] = ag_eval.contadores.get("hechos_no_parseados", 0)
    return ctx.medidas


# ---------------------------------------------------------------------------
# 5 · La tabla antes/despues y el contrato
# ---------------------------------------------------------------------------
def _fila(sc: dict, seg: list[float]) -> dict:
    return {
        "acierto_juridico": round(sc["acierto_juridico"], 3),
        "acc_mecanismo": round(sc["campos"]["mecanismo"]["accuracy"], 3),
        "acierto_gold": round(sc["por_tipo"].get("gold", {}).get("acierto_juridico", 0), 3),
        "acierto_adversarial": round(sc["por_tipo"].get("adversarial", {}).get("acierto_juridico", 0), 3),
        "acierto_abstencion": sc["abstencion"].get("acierto_abstencion"),
        "abstencion_indebida": sc["abstencion"].get("abstencion_indebida"),
        "tasa_alucinacion": sc["alucinacion_normativa"]["tasa_alucinacion"],
        "s_p50": round(_pct(seg, 0.5), 2), "s_p95": round(_pct(seg, 0.95), 2),
    }


def tabla(ctx: Contexto):
    """La tabla que va al README de M5 y a la demo, y el veredicto del
    contrato. Calidad, latencia y tamaño, profesor contra estudiante."""
    import pandas as pd
    m = ctx.medidas
    prof = _fila(m["profesor"]["scorecard"], m["profesor"]["segundos"])
    est = _fila(m["estudiante"]["scorecard"], m["estudiante"]["segundos"])
    prof["json_invalido"] = m["profesor"].get("json_invalido", 0)
    est["json_invalido"] = m["estudiante"].get("json_invalido", 0)
    prof.update(modelo=f"profesor · {PROFESOR} (agente + reglas)",
                parametros=f"{PARAMETROS_PROFESOR / 1e9:.0f} B (5.1 B activos)",
                donde_corre="API de Groq", llamadas_por_caso="3-7")
    est.update(modelo=f"estudiante · {ESTUDIANTE} + LoRA (+ reglas)",
               parametros=f"{ctx.n_parametros_estudiante / 1e6:.0f} M",
               donde_corre="la GPU del sistema (T4)", llamadas_por_caso="1")
    df = pd.DataFrame([prof, est]).set_index("modelo")

    c = ctx.contrato
    perdio = (prof["acierto_juridico"] - est["acierto_juridico"]) * 100
    perdio_adv = (prof["acierto_adversarial"] - est["acierto_adversarial"]) * 100
    gano = prof["s_p50"] / est["s_p50"] if est["s_p50"] else float("inf")
    # Las cinco clausulas, cada una con lo pedido, lo medido y si se cumple.
    clausulas = {
        "acierto juridico": {
            "pedido": f"baja <= {c['acepto_perder_puntos']} puntos",
            "medido": f"{prof['acierto_juridico']:.1%} -> {est['acierto_juridico']:.1%} "
                      f"({perdio:+.1f} puntos perdidos)",
            "cumple": perdio <= c["acepto_perder_puntos"]},
        "alucinacion normativa": {
            "pedido": f"<= {c['alucinacion_maxima']}",
            "medido": f"{est['tasa_alucinacion']}",
            "cumple": est["tasa_alucinacion"] <= c["alucinacion_maxima"]},
        "adversariales": {
            "pedido": f"baja <= {c['acepto_perder_puntos_adversarial']} puntos",
            "medido": f"{prof['acierto_adversarial']:.1%} -> {est['acierto_adversarial']:.1%} "
                      f"({perdio_adv:+.1f} puntos perdidos)",
            "cumple": perdio_adv <= c["acepto_perder_puntos_adversarial"]},
        "velocidad (mediana)": {
            "pedido": f">= {c['quiero_ganar_x']:.0f}x mas rapido",
            "medido": f"{prof['s_p50']} s -> {est['s_p50']} s ({gano:.1f}x)",
            "cumple": gano >= c["quiero_ganar_x"]},
        "estabilidad (p95)": {
            "pedido": f"p95 <= {c['p95_maximo_s']} s",
            "medido": f"{est['s_p95']} s (profesor {prof['s_p95']} s)",
            "cumple": est["s_p95"] <= c["p95_maximo_s"]},
    }
    ok = all(v["cumple"] for v in clausulas.values())
    veredicto = {
        "clausulas": clausulas,
        "perdio_puntos": round(perdio, 1), "perdio_puntos_adversarial": round(perdio_adv, 1),
        "gano_latencia_x": round(gano, 1), "p95_estudiante_s": est["s_p95"],
        "gano_tamano_x": round(PARAMETROS_PROFESOR / max(ctx.n_parametros_estudiante, 1)),
        "alucinacion_estudiante": est["tasa_alucinacion"],
        "cumple": ok,
        "si_no_cumple": ("" if ok else
                         "lab: suban T (aqui: mas variedad de relatos), mas datos "
                         "(N_POR_TEMA), o un estudiante mas grande (Qwen2.5-1.5B-Instruct)"),
    }
    print("CONTRATO")
    for nombre, v in clausulas.items():
        print(f"  {'OK ' if v['cumple'] else 'NO '} {nombre:22s} pedido: {v['pedido']:24s} "
              f"medido: {v['medido']}")
    print(f"  tamaño: {veredicto['gano_tamano_x']}x menos parametros -> "
          + ("CUMPLIDO" if ok else "NO cumplido: " + veredicto["si_no_cumple"]))
    ctx.medidas["tabla"] = {"filas": [prof, est], "veredicto": veredicto}
    return df


def casos_perdidos(ctx: Contexto, mostrar: int = 5) -> list[dict]:
    """TODO 4 del lab: donde el profesor acierta y el estudiante no. Ahi esta
    lo que la destilacion no pudo copiar (slide 19: lo raro se pierde primero,
    la valvula puede desaparecer, los sesgos se heredan)."""
    m, casos = ctx.medidas, ctx.eval_set[:len(ctx.medidas["profesor"]["salidas"])]
    out = []
    for i, e in enumerate(casos):
        if m["profesor"]["aciertos"][i] and not m["estudiante"]["aciertos"][i]:
            p = schema.parse_salida(m["estudiante"]["salidas"][i])
            out.append({"id": e["id"], "tipo": e.get("tipo"), "categoria": e.get("categoria"),
                        "gold": e.get("mecanismo"), "estudiante": p.get("mecanismo"),
                        "relato": e["relato"][:160]})
    al_reves = sum(1 for a, b in zip(m["profesor"]["aciertos"], m["estudiante"]["aciertos"])
                   if b and not a)
    print(f"{len(out)} casos donde el profesor acierta y el estudiante no "
          f"({al_reves} al reves). Por tipo: "
          + str({t: sum(o['tipo'] == t for o in out) for t in {o['tipo'] for o in out}}))
    for o in out[:mostrar]:
        print(f"  {o['id']} [{o['tipo']}] gold {o['gold']} -> estudiante {o['estudiante']}: "
              f"{o['relato']}")
    ctx.medidas["casos_perdidos"] = out
    return out


# ---------------------------------------------------------------------------
# Lo que va al repo
# ---------------------------------------------------------------------------
def guardar(ctx: Contexto, carpeta: Path = CARPETA_REPO) -> list[str]:
    """`m5/destilacion.json` (contrato, entrenamiento, tabla, casos perdidos
    y el resumen de M4) y `m5/pares_profesor.json` (los datos con los que se
    entreno, para que la destilacion sea reproducible sin volver a pagar
    Groq). El adaptador NO va a git (`models/` y `runs/` estan ignorados):
    en S15 se sube al Hub."""
    rutas = []
    t = ctx.medidas.get("tabla", {})
    resumen = {
        "contrato": ctx.contrato,
        "profesor": {"modelo": PROFESOR, "licencia": LICENCIA_PROFESOR,
                     "temperatura_relatos": T_RELATOS, "temperatura_respuesta": T_RESPUESTA},
        "estudiante": ctx.entrenamiento,
        "eval": {"archivos": ["eval_set_v3.json", "eval_set_m3.json"],
                 "n": len(ctx.medidas.get("profesor", {}).get("salidas", []))},
        "tabla": t.get("filas"), "veredicto": t.get("veredicto"),
        "casos_perdidos": ctx.medidas.get("casos_perdidos"),
        "latencias": {q: ctx.medidas[q]["segundos"] for q in ("profesor", "estudiante")
                      if q in ctx.medidas},
    }
    _escribir(carpeta / "destilacion.json", resumen); rutas.append(str(carpeta / "destilacion.json"))
    pares = ctx.pares or _leer(ctx.ruta("pares_profesor.json"), [])
    if pares:
        _escribir(carpeta / "pares_profesor.json", pares)
        rutas.append(str(carpeta / "pares_profesor.json"))
    print("guardado:", *rutas, sep="\n  ")
    return rutas


def correr(carpeta=None, n_por_tema: int = N_POR_TEMA) -> Contexto:
    """Todo de punta a punta (lo que hace el notebook celda por celda)."""
    ctx = preparar(carpeta)
    latencia_por_componente()
    armar_profesor(ctx)
    escribir_relatos(ctx, n_por_tema)
    etiquetar_con_profesor(ctx)
    entrenar_estudiante(ctx)
    medir(ctx)
    print(tabla(ctx).to_string())
    casos_perdidos(ctx)
    guardar(ctx)
    return ctx
