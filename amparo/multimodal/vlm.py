"""El componente visual de M4: el VLM que lee la foto de un documento y
devuelve HECHOS en JSON (antes: celdas 3, 9, 10, 12 y 14 de M4_pipeline.ipynb).

Patron input: lo que ve el VLM se suma al relato y entra a M3 como texto. El
VLM extrae hechos del documento, NO decide derecho: esa decision la toma el
motor de reglas de Amparo. Es el mismo principio del proyecto ("el LLM extrae,
las reglas deciden"), ahora con una imagen en la entrada.

torch, transformers, PIL y requests se importan dentro de las funciones: el
modulo se importa (y se prueba con dobles) sin el stack pesado.
"""
from __future__ import annotations

import io
import json
import time

VLM_ID = "Qwen/Qwen2-VL-2B-Instruct"

# Regla 1 del patron input: la valvula de escape va en el system prompt. Un VLM
# pequeno alucina fechas y numeros (S11); si un dato no se aprecia, que lo deje
# en null en vez de inventarlo.
VALVULA = ("Responde SOLO con lo que se ve en la imagen. Si un dato no se aprecia, "
           "ponlo en null. No inventes fechas, números, entidades ni plazos. "
           "No des opiniones jurídicas: solo describe lo que el documento dice.")

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


def cargar(src):
    """Carga una imagen desde URL o ruta local y la normaliza a RGB."""
    from PIL import Image
    if str(src).startswith("http"):
        import requests
        return Image.open(io.BytesIO(requests.get(src, timeout=30).content)).convert("RGB")
    return Image.open(src).convert("RGB")


def dispositivo() -> str:
    """'cuda' si hay GPU. Sin GPU el VLM corre, pero lentisimo."""
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def cargar_vlm(vlm_id: str = VLM_ID, device: str | None = None):
    """`(vlm, vproc)`: fp16 en GPU, fp32 en CPU, `device_map="auto"`."""
    import torch
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
    device = device or dispositivo()
    vlm = Qwen2VLForConditionalGeneration.from_pretrained(
        vlm_id,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto")
    vproc = AutoProcessor.from_pretrained(vlm_id)
    print("VLM listo:", vlm_id)
    return vlm, vproc


def preguntador(vlm, vproc):
    """Devuelve `preguntar(imagen, pregunta, system=None, max_new_tokens=256) -> str`.

    Una llamada al VLM con una instruccion libre. `ver()` la usa con la
    instruccion de extraccion y la valvula en `system`; el juez de M4
    (`criterios.nota_juez_vlm`) la usa con su propia pregunta y sin `system`.
    Recibe el OBJETO imagen ya cargado, no la ruta.
    """
    def preguntar(imagen, pregunta, system=None, max_new_tokens=256):
        import torch
        msgs = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": pregunta}]}]
        texto = vproc.apply_chat_template(msgs, add_generation_prompt=True)
        ent = vproc(text=[texto], images=[imagen], return_tensors="pt").to(vlm.device)
        with torch.no_grad():
            out = vlm.generate(**ent, max_new_tokens=max_new_tokens, do_sample=False)
        return vproc.batch_decode(out[:, ent["input_ids"].shape[1]:],
                                  skip_special_tokens=True)[0].strip()
    return preguntar


def parsear_json(t: str):
    """Regla 2: extrae el primer objeto JSON del texto. None si no hay o no parsea.
    Un JSON que no parsea cuenta como fallo del caso: no se disimula."""
    i, j = t.find("{"), t.rfind("}")
    if i == -1 or j == -1:
        return None
    try:
        return json.loads(t[i:j + 1])
    except Exception:                                          # noqa: BLE001
        return None


def ver(imagen, instruccion: str | None = None, *, preguntar):
    """imagen -> (texto_crudo, json_o_None).

    El JSON son hechos del documento; NO es una decision juridica. Lo que sale
    de aqui entra al sistema de M3 como texto (`sistema_multimodal`).
    """
    salida = preguntar(imagen, instruccion or INSTRUCCION_DOMINIO, system=VALVULA)
    return salida, parsear_json(salida)


def lector(preguntar):
    """`ver(imagen, instruccion=None)` ligada a un `preguntar`: la firma que
    esperan `scorecard.correr_t6` y `sistema_multimodal`."""
    def ver_ligada(imagen, instruccion=None):
        return ver(imagen, instruccion, preguntar=preguntar)
    return ver_ligada


def cronometrar(f, *a, **k):
    """`(resultado, segundos)` de una llamada, redondeado a centesimas."""
    t0 = time.time()
    r = f(*a, **k)
    return r, round(time.time() - t0, 2)


def armar_relato(pregunta: str, js, crudo: str) -> str:
    """Patron input: lo visto se suma al relato. Si no hubo JSON, va el crudo.
    Es la misma formula que `scorecard.armar_relato` (las dos no pueden divergir)."""
    contexto = json.dumps(js, ensure_ascii=False) if js else crudo
    return pregunta + "\n\nDATOS DEL DOCUMENTO ADJUNTO:\n" + contexto


def sistema_multimodal(pregunta: str, imagen=None, *, ver, responder_m3) -> str:
    """pregunta (+ imagen) -> respuesta de M3. Sin imagen, M3 responde solo."""
    if imagen is None:
        return responder_m3(pregunta)
    crudo, js = ver(imagen)
    return responder_m3(armar_relato(pregunta, js, crudo))
