"""
El sistema completo de Amparo en una llamada: una foto y una pregunta.

POR QUE ESTE MODULO EXISTE

Hasta la corrida del 2026-10-25, `ver()` y `sistema_multimodal()` vivian en
celdas del notebook de M4. Dos razones para sacarlos:

  1. La rubrica de M4 pide un componente "integrado al sistema, no un notebook
     aparte", y la revision docente (PR #15, prioridad P1) lo senala.
  2. La demo y el despliegue tienen que correr EL MISMO codigo que se evaluo.
     Si la interfaz copia las celdas, la version que ve el publico y la que
     se midio pueden divergir sin que nadie lo note.

LO QUE NO CAMBIA

La logica es la de la corrida oficial, copiada literalmente del notebook en
`d158742` (celdas 9, 10 y 14): el mismo modelo, la misma valvula, la misma
instruccion, los mismos parametros de generacion y la misma forma de armar el
relato. `m4/tests/test_multimodal.py` fija las dos cadenas del prompt por su
huella SHA-256, de modo que cualquier cambio en ellas rompe una prueba en vez
de pasar en silencio.

LO QUE SE ANADE: LA RESPUESTA EN TRES BLOQUES

`Amparo.responder()` devuelve, ademas de las cinco lineas de siempre:

  - "Por que": la regla del art. 6 del Decreto 2591 que cerro el caso, los
    hechos que la activaron y las normas que el agente consulto. Sale de la
    traza del agente, no de un texto escrito despues: es lo que de verdad
    decidio.
  - "Leido del documento": lo que extrajo el VLM, rotulado como lectura de un
    modelo NO verificada, con los avisos de `criterios.advertencias_lectura`
    (PR #16). En m10, el plazo de "dos semanas" que no esta en el documento
    aparece con su aviso.

El rotulo y los avisos son solo de PRESENTACION: el relato que recibe M3 es
exactamente el de la corrida evaluada. Ponerle "no verificado" dentro del
relato cambiaria la entrada de M3 y con ello el sistema que se midio.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
for _p in (RAIZ / "src", RAIZ / "m4" / "harness", RAIZ / "m4" / "pipeline"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VLM_ID = "Qwen/Qwen2-VL-2B-Instruct"

# Regla 1: la valvula de escape va en el system prompt.
VALVULA = ('Responde SOLO con lo que se ve en la imagen. Si un dato no se aprecia, '
           'ponlo en null. No inventes fechas, números, entidades ni plazos. '
           'No des opiniones jurídicas: solo describe lo que el documento dice.')

# Instruccion del dominio de Amparo: que extraer del documento y en que formato.
# Son HECHOS legibles del documento, nunca una conclusion juridica.
INSTRUCCION_DOMINIO = (
    'Eres un asistente que lee documentos jurídicos colombianos. Mira la imagen del '
    'documento y devuelve SOLO un JSON (sin texto antes ni después) con estos campos:\n'
    '{\n'
    '  "tipo_documento": uno de "notificacion" | "oficio" | "respuesta_peticion" | "sentencia" | "otro",\n'
    '  "entidad": quién emite el documento (texto corto) o null,\n'
    '  "fecha": la fecha visible en el documento (texto) o null,\n'
    '  "plazo_dias": el número de días de plazo que menciona el documento (entero) o null,\n'
    '  "pretension_visible": qué se le exige o responde al ciudadano, en una frase, o null\n'
    '}\n'
    'Si un campo no se aprecia en la imagen, su valor es null.')

ROTULO_LECTURA = "Leído del documento por un modelo de visión · no verificado"


def parsear_json(t):
    """Regla 2: extrae el primer objeto JSON del texto. None si no hay o no parsea."""
    i, j = t.find('{'), t.rfind('}')
    if i == -1 or j == -1:
        return None
    try:
        return json.loads(t[i:j+1])
    except Exception:
        return None


def armar_relato(pregunta: str, js, crudo: str) -> str:
    """Lo que ve el VLM entra a M3 como texto, despues de la pregunta.

    Identico a `scorecard.armar_relato` (el harness lo repite para capturar la
    lectura); `test_multimodal.py` comprueba que los dos dan lo mismo.
    """
    contexto = json.dumps(js, ensure_ascii=False) if js else crudo
    return pregunta + "\n\nDATOS DEL DOCUMENTO ADJUNTO:\n" + contexto


class LectorVisual:
    """Qwen2-VL-2B cargado una vez, con `preguntar()` y `ver()`.

    Mismos argumentos que la celda 9 de la corrida oficial: fp16 en GPU, fp32
    en CPU, `device_map='auto'`, generacion voraz (`do_sample=False`).
    """

    def __init__(self, modelo_id: str = VLM_ID, device: str | None = None):
        import torch
        from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.modelo_id = modelo_id
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.vlm = Qwen2VLForConditionalGeneration.from_pretrained(
            modelo_id, torch_dtype=self.dtype, device_map="auto")
        self.vproc = AutoProcessor.from_pretrained(modelo_id)

    def preguntar(self, imagen, pregunta, system=None, max_new_tokens=256):
        """Una llamada al VLM: (imagen, pregunta) -> texto. `system` lleva la valvula."""
        with self.torch.no_grad():
            msgs = ([{'role': 'system', 'content': system}] if system else []) + \
                   [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': pregunta}]}]
            texto = self.vproc.apply_chat_template(msgs, add_generation_prompt=True)
            ent = self.vproc(text=[texto], images=[imagen], return_tensors='pt').to(self.vlm.device)
            out = self.vlm.generate(**ent, max_new_tokens=max_new_tokens, do_sample=False)
            return self.vproc.batch_decode(out[:, ent['input_ids'].shape[1]:],
                                           skip_special_tokens=True)[0].strip()

    def ver(self, imagen, instruccion=None):
        """imagen -> (texto_crudo, json_o_None).

        El JSON son hechos del documento; NO es una decision juridica: esa la
        toma el motor de reglas de Amparo.
        """
        salida = self.preguntar(imagen, instruccion or INSTRUCCION_DOMINIO, system=VALVULA)
        return salida, parsear_json(salida)


def sistema_multimodal(pregunta, imagen=None, *, ver_fn, responder_m3):
    """pregunta (+ imagen) -> respuesta de M3. Patron input: lo visto se suma al relato."""
    if imagen is None:
        return responder_m3(pregunta)
    crudo, js = ver_fn(imagen)
    return responder_m3(armar_relato(pregunta, js, crudo))


# --------------------------------------------------------------------------
# La respuesta en tres bloques
# --------------------------------------------------------------------------
def normas_por_id(agente) -> dict[str, str]:
    """id del fragmento -> "art. X · Norma", del indice que usa el agente."""
    chunks = getattr(getattr(agente, "indice", None), "chunks", None) or []

    def etiqueta(c):
        art, norma = c.get("articulo", "").strip(), c.get("norma", "").strip()
        # "art. 49 CP" ya nombra la Constitucion: repetirla no informa nada.
        return art if art.endswith(" CP") else f"{art} · {norma}".strip(" ·")
    return {c["id"]: etiqueta(c) for c in chunks if isinstance(c, dict) and "id" in c}


def por_que(traza: dict, normas: dict[str, str] | None = None) -> dict:
    """El fundamento visible, tomado de la traza del agente y nada mas."""
    normas = normas or {}
    consultadas = list(dict.fromkeys(normas.get(i, i) for i in traza.get("recuperados") or []))
    return {
        "regla": traza.get("regla"),
        "mecanismo_del_motor": traza.get("mecanismo_del_motor"),
        "se_abstuvo": bool(traza.get("no_triable")),
        "motivo_abstencion": traza.get("motivo_no_triable") or "",
        "hechos": sorted(k for k, v in (traza.get("hechos") or {}).items() if v),
        "normas_consultadas": consultadas,
        "herramientas": traza.get("herramientas") or [],
    }


def formatear(res: dict) -> str:
    """Markdown con los tres bloques, para el notebook y para la interfaz."""
    lineas = ["### Respuesta", "", "```", res["respuesta"].strip(), "```", ""]

    pq = res.get("por_que")
    lineas += ["### Por qué", ""]
    if pq is None:
        lineas += ["_Sin traza del agente: no se puede mostrar el fundamento._", ""]
    else:
        if pq["se_abstuvo"]:
            lineas.append("- **Amparo prefirió no decidir**: "
                          + (pq["motivo_abstencion"] or "los hechos no alcanzan para triar el caso."))
        lineas.append(f"- **Regla del art. 6 (Decreto 2591) que cerró el caso:** `{pq['regla']}`")
        if pq["hechos"]:
            lineas.append("- **Hechos que la activaron:** " + ", ".join(f"`{h}`" for h in pq["hechos"]))
        if pq["normas_consultadas"]:
            lineas.append("- **Normas que consultó el agente:** " + "; ".join(pq["normas_consultadas"]))
        lineas.append("- El mecanismo lo decide la regla, no el modelo de lenguaje.")
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
                lineas.append(f"- `{k}`: {v if v is not None else '_no se aprecia_'}")
        else:
            lineas.append("_El modelo no devolvió un JSON legible; esto es lo que escribió:_")
            lineas.append("")
            lineas.append(f"> {leido['crudo']}")
        lineas.append("")

    seg = res.get("segundos") or {}
    if seg:
        lineas.append("_" + " · ".join(f"{k}: {v:.1f} s" for k, v in seg.items() if v is not None) + "_")
    return "\n".join(lineas)


class Amparo:
    """El producto: `Amparo().responder(pregunta, imagen)`.

    Sin argumentos carga el VLM y enchufa el brazo 4 de M3 (necesita GPU y
    `GROQ_API_KEY`). Las pruebas inyectan un lector y un M3 falsos.
    """

    def __init__(self, lector=None, responder_m3=None, agente=None):
        if responder_m3 is None:
            from enchufe_m3 import construir_responder_m3
            responder_m3, agente = construir_responder_m3()
        self.lector = lector if lector is not None else LectorVisual()
        self.responder_m3 = responder_m3
        self.agente = agente
        self._normas = None

    def responder(self, pregunta: str, imagen=None) -> dict:
        import criterios
        crudo = js = None
        seg_ver = None
        if imagen is not None:
            t0 = time.perf_counter()
            crudo, js = self.lector.ver(imagen)
            seg_ver = time.perf_counter() - t0
            relato = armar_relato(pregunta, js, crudo)
        else:
            relato = pregunta
        t1 = time.perf_counter()
        salida = self.responder_m3(relato)
        seg_m3 = time.perf_counter() - t1

        traza = None
        if self.agente is not None and getattr(self.agente, "trazas", None):
            traza = self.agente.trazas[-1]
        if self._normas is None:
            self._normas = normas_por_id(self.agente)
        return {
            "respuesta": salida,
            "por_que": por_que(traza, self._normas) if traza is not None else None,
            "leido": None if imagen is None else {
                "rotulo": ROTULO_LECTURA,
                "campos": js,
                "crudo": crudo,
                "advertencias": criterios.advertencias_lectura(js),
            },
            "segundos": {"lectura del documento": seg_ver, "decisión (M3)": seg_m3},
        }

    def responder_markdown(self, pregunta: str, imagen=None) -> str:
        return formatear(self.responder(pregunta, imagen))
