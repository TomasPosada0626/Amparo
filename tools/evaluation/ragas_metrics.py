"""Metricas RAGAS (M3 · S10, Lab C) con juez externo: evaluar el RAG por dentro.

RAGAS no mira solo la respuesta final, como el harness de M2: toma un caso ya
resuelto (pregunta, contextos recuperados, respuesta, referencia) y le calcula
cuatro notas de 0 a 1, cada una comparando dos piezas distintas. Por eso
diagnostica DONDE falla el sistema:

  faithfulness       respuesta  vs contextos  ¿lo que afirma sale del contexto?
                     (baja -> el generador inventa o completa de memoria)
  context_precision  contextos  vs pregunta   ¿los chunks relevantes quedaron arriba?
                     (baja -> el retrieval trae ruido; S08: rerank)
  context_recall     referencia vs contextos  ¿el contexto trae lo necesario?
                     (baja -> el retrieval no encuentra; S08: hybrid, corpus)
  answer_relevancy   respuesta  vs pregunta   ¿la respuesta contesta lo que se pregunto?
                     (baja -> divaga, o se niega a responder)

DECISION: implementacion propia, como en el Lab C, y no la libreria `ragas`.
  1. El juez es Groq (openai/gpt-oss-120b, el mismo de external_judge.py): otra
     familia que Qwen, el modelo evaluado. El M2 midio que el juez Qwen se
     prefirio a si mismo 60 de 60 veces; usar Qwen como juez de RAGAS repetiria
     ese sesgo. La libreria se puede conectar a Groq, pero exige wrappers de
     LangChain y su API cambio mucho entre versiones.
  2. Cupo: la capa gratuita de Groq tiene un limite diario de tokens. La
     libreria hace varias llamadas por metrica y reenvia el contexto en cada
     una. Aca las tres metricas que dependen del contexto (faithfulness,
     context_precision, context_recall) salen de UNA sola llamada que devuelve
     los veredictos de las tres en JSON; answer_relevancy es una llamada corta
     sin contexto. Dos llamadas por caso, con checkpoint para retomar si el
     cupo se acaba (tools/evaluation/checkpoint.py, el mismo de M2).
  3. Mismo patron del repo: el juez y los embeddings se inyectan, asi que el
     calculo de las metricas se prueba sin red ni GPU
     (tests/evaluation/test_ragas_metrics.py).

Las formulas siguen a RAGAS:
  - faithfulness = afirmaciones respaldadas / afirmaciones de la respuesta.
  - context_precision = precision promedio ponderada por rango (average
    precision): un chunk relevante en la posicion 1 vale mas que en la 5.
  - context_recall = oraciones de la referencia atribuibles al contexto / total.
  - answer_relevancy = coseno medio entre la pregunta original y N preguntas que
    el juez genera a partir de la respuesta (embeddings e5). Una respuesta que
    no se compromete (la valvula de escape) vale 0, como en RAGAS.

Los casos adversariales se evaluan aparte: ahi la respuesta correcta suele ser
reconocer un limite (la valvula de escape, o negarse a garantizar un resultado,
o priorizar la seguridad), y RAGAS la castigaria. Por eso las metricas RAGAS se
reportan sobre los casos gold, y los adversariales se miden con la prudencia
(tasas_de_escape): escapa, o no cita lo que no vio, no inventa sentencias y no
promete resultados. Lo especifico de cada adversarial lo juzga el harness de M2
con su criterio.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
import time
from pathlib import Path
from typing import Callable, Optional, Sequence

from tools.evaluation.checkpoint import append_checkpoint, load_checkpoint

METRICAS = ("faithfulness", "context_precision", "context_recall", "answer_relevancy")

# Cuantas preguntas genera el juez para answer_relevancy (RAGAS usa 3).
N_PREGUNTAS_RELEVANCIA = 3
MAX_TOKENS_CONTEXTO = 2000
MAX_TOKENS_RELEVANCIA = 600

# Juez: (system, user, max_tokens) -> (texto, tokens_usados). Embeddings:
# (lista de textos) -> lista de vectores.
Juez = Callable[[str, str, int], "tuple[str, int]"]
Embedder = Callable[[list], list]

FRASES_DE_ESCAPE = (
    "no tengo informacion verificada",
    "no tengo información verificada",
)


def es_valvula_de_escape(respuesta: str) -> bool:
    """¿La respuesta CONTIENE la frase de escape de Amparo (prompt_template)?

    Es busqueda de subcadena, asi que da True tambien cuando la respuesta
    orienta y solo acota una duda ("el articulo 62 permite X. No tengo
    informacion verificada sobre como se valora Y. Reune el acta..."). Para
    contar abstenciones hay que usar `es_abstencion_pura`: con esta funcion, la
    tasa de escape en gold de la corrida del 2026-10-09 salia 0.60 cuando las
    abstenciones de verdad eran 8 de 45 (0.18).

    Se conserva tal cual porque es la que define `respuestas_escape` y el
    denominador de faithfulness en los scorecards ya publicados.
    """
    r = (respuesta or "").lower()
    return any(f in r for f in FRASES_DE_ESCAPE)


def es_abstencion_pura(respuesta: str) -> bool:
    """¿La respuesta se abstiene DE VERDAD: la frase y nada de fondo?

    Una abstencion es negarse a orientar. Si la respuesta cita un articulo,
    esta orientando, y la frase solo esta acotando lo que no puede afirmar --
    que es el comportamiento que se le pidio en los ejemplos B3, no un fallo.

    Distinguirlas cambia el diagnostico: en gold, 27 de 45 respuestas contienen
    la frase, pero solo 8 se abstienen; en adversariales la abstencion pura
    sube a 20 de 30. El modelo si discrimina, 3.7 veces mas abstencion donde
    corresponde, y medirlo por subcadena lo escondia.
    """
    if not es_valvula_de_escape(respuesta):
        return False
    from tools.rag.verificacion import articulos_citados   # perezoso: tools.rag es opcional aqui

    return not articulos_citados(respuesta or "")


# --- Prompts del juez --------------------------------------------------------

SYSTEM_JUEZ = (
    "Eres un evaluador estricto de sistemas RAG juridicos. Juzgas solo con el "
    "texto que se te da, sin conocimiento propio sobre derecho. Respondes "
    "unicamente con un objeto JSON valido, sin texto antes ni despues."
)


def prompt_contexto(pregunta: str, respuesta: str, referencia: str, contextos: list[str]) -> str:
    if contextos:
        bloque = "\n\n".join(f"[{i}] {c}" for i, c in enumerate(contextos, start=1))
    else:
        bloque = "(no se recupero ningun contexto)"
    return f"""PREGUNTA:
{pregunta}

CONTEXTOS RECUPERADOS (en orden de ranking):
{bloque}

RESPUESTA DEL SISTEMA:
{respuesta}

RESPUESTA DE REFERENCIA:
{referencia}

Tareas:
1. Divide la RESPUESTA DEL SISTEMA en afirmaciones atomicas (hechos o reglas
   que afirma). Para cada una indica si los CONTEXTOS la respaldan.
2. Para cada contexto, en orden, indica si es util para responder la PREGUNTA
   segun la RESPUESTA DE REFERENCIA. Debe haber exactamente {len(contextos)} valores.
3. Divide la RESPUESTA DE REFERENCIA en oraciones. Para cada una indica si su
   contenido se puede atribuir a los CONTEXTOS.

Devuelve este JSON:
{{"afirmaciones": [{{"texto": "...", "respaldada": true}}],
 "contextos_utiles": [true, false],
 "referencia": [{{"oracion": "...", "en_contexto": true}}]}}"""


def prompt_relevancia(respuesta: str) -> str:
    return f"""RESPUESTA:
{respuesta}

Escribe {N_PREGUNTAS_RELEVANCIA} preguntas distintas, en español, que esta
respuesta contesta directamente. Devuelve este JSON:
{{"preguntas": ["...", "...", "..."]}}"""


# --- Parseo y formulas (puras, testeables) -----------------------------------

def extraer_json(texto: str) -> Optional[dict]:
    """Primer '{' al ultimo '}'; None si no es JSON valido (no lanza)."""
    if not texto:
        return None
    i, j = texto.find("{"), texto.rfind("}")
    if i == -1 or j <= i:
        return None
    try:
        obj = json.loads(texto[i : j + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return obj if isinstance(obj, dict) else None


def _bools(lista, clave: Optional[str] = None) -> Optional[list[bool]]:
    if not isinstance(lista, list):
        return None
    salida = []
    for item in lista:
        valor = item.get(clave) if (clave and isinstance(item, dict)) else item
        if not isinstance(valor, bool):
            return None
        salida.append(valor)
    return salida


def average_precision(relevantes: Sequence[bool]) -> Optional[float]:
    """Context precision de RAGAS: sum_k (precision@k * rel_k) / #relevantes.

    Premia que los chunks utiles esten arriba del ranking. 0 si ninguno es
    util; None si no hay contextos (no hay ranking que medir)."""
    if not relevantes:
        return None
    aciertos, suma = 0, 0.0
    for k, rel in enumerate(relevantes, start=1):
        if rel:
            aciertos += 1
            suma += aciertos / k
    return suma / aciertos if aciertos else 0.0


def metricas_de_contexto(veredicto: Optional[dict], n_contextos: int) -> dict:
    """Convierte el JSON del juez en faithfulness / context_precision / recall.

    Un veredicto mal formado deja la metrica en None (no se inventa un 0): se
    reporta como fallo de parseo y no entra al promedio."""
    salida = {"faithfulness": None, "context_precision": None, "context_recall": None,
              "n_afirmaciones": None, "parse_ok": False}
    if veredicto is None:
        return salida

    afirmaciones = _bools(veredicto.get("afirmaciones"), "respaldada")
    utiles = _bools(veredicto.get("contextos_utiles"))
    referencia = _bools(veredicto.get("referencia"), "en_contexto")

    if afirmaciones is not None:
        salida["n_afirmaciones"] = len(afirmaciones)
        salida["faithfulness"] = sum(afirmaciones) / len(afirmaciones) if afirmaciones else None
    if n_contextos == 0:
        salida["context_precision"] = None
        salida["context_recall"] = 0.0 if referencia else None
    else:
        if utiles is not None and len(utiles) == n_contextos:
            salida["context_precision"] = average_precision(utiles)
        if referencia:
            salida["context_recall"] = sum(referencia) / len(referencia)
    salida["parse_ok"] = afirmaciones is not None and referencia is not None and (
        n_contextos == 0 or salida["context_precision"] is not None
    )
    return salida


def coseno(a, b) -> float:
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


def answer_relevancy(pregunta: str, preguntas_generadas: list[str], embed: Embedder) -> Optional[float]:
    preguntas = [p for p in preguntas_generadas if isinstance(p, str) and p.strip()]
    if not preguntas:
        return None
    vectores = embed([pregunta] + preguntas)
    return statistics.mean(coseno(vectores[0], v) for v in vectores[1:])


# --- Evaluacion de un caso y de una corrida ----------------------------------

def evaluar_caso(record: dict, *, juez: Juez, embed: Embedder) -> dict:
    """Calcula las cuatro metricas de un registro de pipeline.to_eval_record.

    Dos llamadas al juez: una con el contexto (tres metricas) y una corta para
    answer_relevancy. Si la respuesta es la valvula de escape, no hay nada que
    verificar: faithfulness queda None y answer_relevancy vale 0 (no contesto),
    y el contexto se sigue evaluando (el retrieval pudo traer lo necesario y el
    generador no lo uso)."""
    t0 = time.perf_counter()
    respuesta = record.get("answer", "")
    contextos = list(record.get("contexts") or [])
    escape = es_valvula_de_escape(respuesta)
    tokens = 0

    texto, usados = juez(
        SYSTEM_JUEZ,
        prompt_contexto(record["question"], respuesta, record.get("ground_truth", ""), contextos),
        MAX_TOKENS_CONTEXTO,
    )
    tokens += usados
    error_juez = not texto          # sin respuesta del juez: red, cupo agotado...
    fila = metricas_de_contexto(extraer_json(texto), len(contextos))
    if escape:
        fila["faithfulness"] = None

    if escape:
        fila["answer_relevancy"] = 0.0
    elif error_juez:
        fila["answer_relevancy"] = None   # el juez no respondio: no gastar otra llamada
    else:
        texto, usados = juez(SYSTEM_JUEZ, prompt_relevancia(respuesta), MAX_TOKENS_RELEVANCIA)
        tokens += usados
        error_juez = error_juez or not texto
        obj = extraer_json(texto) or {}
        fila["answer_relevancy"] = answer_relevancy(record["question"], obj.get("preguntas") or [], embed)

    fila.update({
        "id": clave_de(record),
        "registro_id": record["id"],
        "sistema": record.get("sistema", "una_pasada"),
        "tipo": record.get("tipo", ""),
        "category": record.get("category", ""),
        "escape": escape,
        "n_contextos": len(contextos),
        "huella": huella_de(record),
        "error_juez": error_juez,
        "tokens_juez": tokens,
        "segundos": round(time.perf_counter() - t0, 2),
    })
    return fila


def huella_de(record: dict) -> str:
    """Identifica el CONTENIDO evaluado (pregunta, respuesta, contextos,
    referencia). Dos registros con la misma huella reciben las mismas notas, asi
    que no hace falta pagarle al juez dos veces (ver `reusar` en evaluar_corrida)."""
    contenido = json.dumps([record.get("question"), record.get("answer"), list(record.get("contexts") or []),
                            record.get("ground_truth")], ensure_ascii=False)
    return hashlib.md5(contenido.encode("utf-8")).hexdigest()


def clave_de(record: dict) -> str:
    """Id unico para el checkpoint: el mismo registro se evalua en varias rutas."""
    return f"{record.get('sistema', 'una_pasada')}:{record['id']}"


MAX_ERRORES_SEGUIDOS = 3


def evaluar_corrida(
    records: Sequence[dict],
    *,
    juez: Juez,
    embed: Embedder,
    checkpoint_path: Optional[Path] = None,
    solo_gold: bool = True,
    progress_every: int = 5,
    reusar: Sequence[dict] = (),
) -> list[dict]:
    """Evalua una lista de registros, con checkpoint para retomar.

    solo_gold: los adversariales se miden con tasas_de_escape, no con RAGAS
    (ver docstring del modulo).

    Cupo del juez: un caso en el que el juez no respondio (red, limite de Groq)
    NO se guarda en el checkpoint -- si se guardara, al retomar se saltaria como
    "ya evaluado" sin haberlo evaluado nunca. Tras MAX_ERRORES_SEGUIDOS errores
    seguidos (tipicamente, cupo diario agotado) la corrida se detiene y devuelve
    lo que alcanzo a evaluar; volver a llamar con el mismo checkpoint_path sigue
    desde ahi.

    reusar: filas ya evaluadas en otra corrida. Un registro con la misma huella
    (misma pregunta, respuesta, contextos y referencia) toma esas notas sin
    llamar al juez. Caso tipico: la ruta "una_pasada" de S10 y la configuracion C
    de S08 son el mismo sistema."""
    pendientes = [r for r in records if not solo_gold or r.get("tipo") == "gold"]
    # Con huella: una entrada del checkpoint solo se reusa si el contenido
    # evaluado es el mismo (pregunta, respuesta, contextos y referencia). Sin
    # esto se reusaba por id, y en la corrida del 2026-10-07 unos 29 de 45 casos
    # por ruta heredaron notas de respuestas anteriores -- de otro adaptador y
    # otro indice. La clave es "sistema:id" porque el mismo registro se evalua en
    # varias rutas.
    huellas = {clave_de(r): huella_de(r) for r in pendientes}
    hechos = load_checkpoint(checkpoint_path, huellas, log_prefix="ragas")
    previas = {(f.get("registro_id"), f.get("huella")): f for f in reusar
               if f.get("huella") and not f.get("error_juez")}
    filas, tokens, errores_seguidos, reusadas = [], 0, 0, 0
    for i, record in enumerate(pendientes, start=1):
        clave = clave_de(record)
        if clave in hechos:
            filas.append(hechos[clave])
            continue
        previa = previas.get((record["id"], huella_de(record)))
        if previa is not None:
            fila = {**previa, "id": clave, "sistema": record.get("sistema", "una_pasada"),
                    "reusada_de": previa.get("id"), "tokens_juez": 0}
            append_checkpoint(checkpoint_path, fila)
            filas.append(fila)
            reusadas += 1
            continue
        fila = evaluar_caso(record, juez=juez, embed=embed)
        tokens += fila["tokens_juez"]
        if fila["error_juez"]:
            errores_seguidos += 1
            if errores_seguidos >= MAX_ERRORES_SEGUIDOS:
                faltan = len(pendientes) - i + errores_seguidos
                print(f"[ragas] el juez fallo {errores_seguidos} veces seguidas (cupo de Groq agotado o red). "
                      f"Se detiene aqui: faltan ~{faltan} casos. Vuelve a correr la celda mas tarde "
                      "(o con otra GROQ_API_KEY) y sigue desde este punto.")
                break
            continue
        errores_seguidos = 0
        append_checkpoint(checkpoint_path, fila)
        filas.append(fila)
        if progress_every and (i % progress_every == 0 or i == len(pendientes)):
            print(f"[ragas] {i}/{len(pendientes)} -- tokens del juez en esta sesion: {tokens}")
    if reusadas:
        print(f"[ragas] {reusadas} casos reusados de una evaluacion identica (sin gastar juez).")
    evaluados = len(filas)
    if evaluados < len(pendientes):
        print(f"[ragas] evaluados {evaluados}/{len(pendientes)}: el resumen es PARCIAL hasta completar.")
    return filas


def resumen(filas: Sequence[dict]) -> dict:
    """Promedio de cada metrica por ruta (sistema), ignorando los None.

    Reporta tambien cuantos casos entraron a cada promedio (n_<metrica>) y los
    fallos de parseo: un promedio sobre 10 casos no se lee igual que sobre 50."""
    por_sistema: dict[str, list[dict]] = {}
    for f in filas:
        por_sistema.setdefault(f["sistema"], []).append(f)
    salida = {}
    for sistema, fs in por_sistema.items():
        r = {"casos": len(fs), "fallos_parseo": sum(1 for f in fs if not f.get("parse_ok")),
             "respuestas_escape": sum(1 for f in fs if f.get("escape")),
             "tokens_juez": sum(f.get("tokens_juez", 0) for f in fs)}
        for m in METRICAS:
            valores = [f[m] for f in fs if f.get(m) is not None]
            r[m] = round(statistics.mean(valores), 4) if valores else None
            r[f"n_{m}"] = len(valores)
        salida[sistema] = r
    return salida


def articulos_de_record(record: dict) -> set[str]:
    """Articulos que el sistema vio, desde las citas de retrieved_chunks."""
    from tools.rag.verificacion import articulos_citados

    return articulos_citados(" ".join(c.get("cita", "") for c in record.get("retrieved_chunks") or []))


def tasas_de_escape(records: Sequence[dict]) -> dict:
    """Valvula de escape y prudencia por ruta, separadas por tipo de caso.

    - prudencia_en_adversariales: escapa, o no cita articulos que no vio, no
      cita sentencias y no promete resultados (verificacion.es_prudente). Alta = bien.
      Es la medida principal en adversariales: no todos esperan la frase de
      escape (una amenaza espera que se priorice la seguridad, p. ej.).
    - escape_en_adversariales: cuantos usaron literalmente la frase de escape.
    - escape_en_gold: deberia responder. Alta = el sistema se niega de mas.
    - citas_no_respaldadas_en_gold: respuestas gold que citan un articulo que el
      sistema no recupero. Deberia ser 0: es el principio de Amparo."""
    from tools.rag.verificacion import citas_no_respaldadas, es_prudente

    salida: dict[str, dict] = {}
    for r in records:
        s = salida.setdefault(r.get("sistema", "una_pasada"),
                              {"adversarial": [0, 0, 0], "gold": [0, 0, 0]})
        tipo = r.get("tipo") if r.get("tipo") in ("adversarial", "gold") else None
        if not tipo:
            continue
        respuesta, vistos = r.get("answer", ""), articulos_de_record(r)
        s[tipo][0] += int(es_valvula_de_escape(respuesta))
        s[tipo][1] += 1
        if tipo == "adversarial":
            s[tipo][2] += int(es_prudente(respuesta, vistos, r.get("question", "")))
        else:
            s[tipo][2] += int(bool(citas_no_respaldadas(respuesta, query=r.get("question", ""), vistos=vistos)))

    def tasa(a, b):
        return round(a / b, 4) if b else None

    return {
        sistema: {
            "prudencia_en_adversariales": tasa(v["adversarial"][2], v["adversarial"][1]),
            "escape_en_adversariales": tasa(v["adversarial"][0], v["adversarial"][1]),
            "escape_en_gold": tasa(v["gold"][0], v["gold"][1]),
            "citas_no_respaldadas_en_gold": tasa(v["gold"][2], v["gold"][1]),
            "n_adversariales": v["adversarial"][1],
            "n_gold": v["gold"][1],
        }
        for sistema, v in salida.items()
    }


# --- Implementaciones por defecto (red / GPU, import perezoso) ----------------

REINTENTOS_LIMITE_MINUTO = 3
ESPERA_LIMITE_MINUTO_S = 20


def es_limite_por_minuto(exc: Exception) -> bool:
    """Un 429 de Groq por limite POR MINUTO se resuelve esperando; uno por
    limite DIARIO (tokens/requests per day) no, y no vale la pena reintentar."""
    texto = str(exc).lower()
    es_429 = getattr(exc, "status_code", None) == 429 or "429" in texto or "rate limit" in texto
    diario = "per day" in texto or "tpd" in texto or "rpd" in texto
    return es_429 and not diario


def juez_groq() -> Juez:
    """Juez real: Groq con el modelo de external_judge (GROQ_JUDGE_MODEL).

    Nunca lanza ante un fallo puntual: si Groq pide esperar (limite por
    minuto), espera y reintenta; si el fallo persiste o es el cupo diario,
    devuelve ("", 0) y evaluar_corrida no guarda ese caso en el checkpoint (se
    reintenta al retomar). Si la clave falta, si falla de inmediato (error de
    configuracion)."""
    from tools.evaluation import external_judge as ej

    cliente = ej._get_client()

    def juez(system: str, user: str, max_tokens: int):
        kwargs = dict(
            model=ej.GROQ_JUDGE_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=max_tokens,
            timeout=90.0,
        )
        if ej.GROQ_REASONING_EFFORT:
            kwargs["reasoning_effort"] = ej.GROQ_REASONING_EFFORT
        for intento in range(REINTENTOS_LIMITE_MINUTO + 1):
            try:
                resp = cliente.chat.completions.create(**kwargs)
            except Exception as exc:  # noqa: BLE001 - un fallo puntual no aborta el lote
                if es_limite_por_minuto(exc) and intento < REINTENTOS_LIMITE_MINUTO:
                    espera = ESPERA_LIMITE_MINUTO_S * (intento + 1)
                    print(f"[ragas] limite por minuto de Groq; espero {espera}s y reintento...")
                    time.sleep(espera)
                    continue
                print(f"[ragas] error del juez: {str(exc)[:300]}")
                return "", 0
            usados = getattr(getattr(resp, "usage", None), "total_tokens", 0) or 0
            return (resp.choices[0].message.content or "").strip(), usados
        return "", 0

    return juez


def embedder_e5() -> Embedder:
    """Embeddings e5 del propio RAG (prefijo "query: " para las preguntas)."""
    from tools.rag.embed_store import embed_query

    return lambda textos: [embed_query(t) for t in textos]
