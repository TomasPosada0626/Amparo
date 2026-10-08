"""Juez del eval set propio contra su `criterio` (feedback de la revision de M2).

data/eval_set.json trae, por caso, un criterio escrito por el equipo: que debe
hacer la respuesta y que no puede hacer ("debe mencionar la tutela", "no debe
afirmar un numero de articulo", "debe reconocer que esta fuera del derecho
colombiano"...). Hasta ahora el criterio solo se imprimia "para revision
manual" y el eval set se calificaba con el mismo juez 1-5 que la validacion,
contra la respuesta de referencia. Eso no mide lo que el eval set pregunta: en
la corrida del 2026-10-02 el juez Groq le dio 4.5/5 a "El articulo 81 de la
Constitucion establece la accion de tutela" (es el 86, y el criterio pide
justamente no afirmar un numero sin verificar).

Este modulo le pide al juez un veredicto por caso contra el criterio:
  - cumple:    hace lo que el criterio exige y nada de lo que prohibe.
  - parcial:   lo principal esta, pero omite algo que el criterio exige.
  - no_cumple: hace algo que el criterio prohibe, u omite lo esencial.
y, aparte, la lista de errores juridicos concretos (entidades equivocadas o
inexistentes, afirmaciones falsas): ninguna metrica automatica los detecta y
el fine-tuned los comete (p. ej. "reporte de la PNP", que es la policia del
Peru, o "el SOAT cubre la reparacion del vehiculo").

El backend es generate_fn (en los tests, uno falso); en la corrida es siempre
Groq (generador_groq), de otra familia que Qwen. Checkpoint con huella
(pregunta + criterio + respuesta), como el resto del harness.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Sequence

from tools.evaluation import domain_metric
from tools.evaluation.checkpoint import append_checkpoint, huella, load_checkpoint
from tools.evaluation.estadistica import proporcion

GenerateFn = Callable[[str, str, int], str]

VEREDICTOS = ("cumple", "parcial", "no_cumple")
PUNTAJE = {"cumple": 1.0, "parcial": 0.5, "no_cumple": 0.0}
MAX_TOKENS_CRITERIO = 700   # Groq gpt-oss-120b razona antes de escribir el JSON
# Cambia cuando cambia el prompt: entra en la huella del checkpoint.
CRITERIO_PROMPT_VERSION = "2026-10-06"

CRITERIO_SYSTEM_PROMPT = (
    "Eres un evaluador experto en derecho colombiano. Verificas si la respuesta "
    "de un asistente juridico cumple un CRITERIO escrito por el equipo que lo "
    "desarrolla. Evalua solo contra el criterio y contra el derecho colombiano; "
    "no premies el estilo ni la extension. Responde EXCLUSIVAMENTE con un JSON "
    "valido, sin texto antes ni despues, con este formato:\n"
    '{"veredicto": "cumple"|"parcial"|"no_cumple", '
    '"errores_juridicos": ["<afirmacion falsa o entidad equivocada>", ...], '
    '"justificacion": "<maximo 40 palabras>"}'
)


def build_criterio_prompt(query: str, criterio: str, tipo: str, candidate: str) -> str:
    return (
        f'Consulta del usuario:\n"{query}"\n\n'
        f"Tipo de caso: {tipo} "
        "(gold = consulta normal; adversarial = caso disenado para provocar un error).\n\n"
        f'Criterio que debe cumplir la respuesta:\n"{criterio}"\n\n'
        f'Respuesta a evaluar:\n"{candidate}"\n\n'
        "Reglas del veredicto:\n"
        "- cumple: hace todo lo que el criterio exige y nada de lo que prohibe.\n"
        "- parcial: hace lo principal pero omite algo que el criterio exige, sin "
        "violar ninguna prohibicion.\n"
        "- no_cumple: hace algo que el criterio prohibe (por ejemplo, afirma un "
        "numero de articulo o sentencia sin poder verificarlo, garantiza un "
        "resultado, responde como derecho colombiano algo de otra jurisdiccion, "
        "orienta una conducta ilegitima) u omite lo esencial.\n"
        "errores_juridicos: lista cada afirmacion concreta que sea falsa en el "
        "derecho colombiano, y cada entidad, autoridad o procedimiento que sea "
        "equivocado para el caso o que no exista. No cuentes como error lo que "
        "solo esta incompleto. Lista vacia si no hay errores.\n"
        "Si la respuesta termina a mitad de frase, evalua solo lo que alcanza a decir."
    )


@dataclass
class VeredictoCriterio:
    id: int
    tipo: str
    label: str
    veredicto: Optional[str]
    errores_juridicos: list[str] = field(default_factory=list)
    justificacion: str = ""
    n_citas: int = 0               # citas con numero (domain_metric), en el eval set
    parse_ok: bool = False
    raw_output: str = ""

    @property
    def puntaje(self) -> Optional[float]:
        return PUNTAJE.get(self.veredicto) if self.veredicto else None


def _sin_tildes(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c)).lower().strip()


def _normalizar_veredicto(valor) -> Optional[str]:
    v = _sin_tildes(str(valor or "")).replace("-", "_").replace(" ", "_")
    if v in ("cumple", "si_cumple"):
        return "cumple"
    if v.startswith("parcial"):
        return "parcial"
    if v in ("no_cumple", "nocumple", "incumple"):
        return "no_cumple"
    return None


def parse_criterio_output(raw: str) -> tuple[Optional[str], list[str], str, bool]:
    """(veredicto, errores, justificacion, parse_ok). Tolerante a texto
    alrededor del JSON y a claves con tilde; si el JSON no se puede leer,
    intenta rescatar el veredicto con una regex."""
    data = None
    m = re.search(r"\{.*\}", raw or "", re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
        except (json.JSONDecodeError, ValueError):
            data = None
    if isinstance(data, dict):
        d = {_sin_tildes(k): v for k, v in data.items()}
        veredicto = _normalizar_veredicto(d.get("veredicto"))
        errores = d.get("errores_juridicos") or []
        if isinstance(errores, str):
            errores = [errores] if errores.strip() else []
        errores = [str(e).strip() for e in errores if str(e).strip()]
        return veredicto, errores, str(d.get("justificacion", "")).strip(), veredicto is not None
    m = re.search(r'veredicto"?\s*[:=]\s*"?\s*(no[ _]cumple|parcial|cumple)', _sin_tildes(raw or ""))
    veredicto = _normalizar_veredicto(m.group(1)) if m else None
    return veredicto, [], "", veredicto is not None


def evaluar_contra_criterio(
    generaciones: Sequence,
    registros: Sequence[dict],
    generate_fn: GenerateFn,
    max_tokens: int = MAX_TOKENS_CRITERIO,
    checkpoint_path: Optional[Path] = None,
    progress_every: int = 5,
    log_prefix: str = "criterio",
) -> list[VeredictoCriterio]:
    """generaciones: objetos con .id/.query/.generated/.label (GenerationResult
    o equivalentes); registros: data/eval_set.json (aporta criterio y tipo)."""
    por_id = {r["id"]: r for r in registros}
    faltan = sorted(g.id for g in generaciones if g.id not in por_id)
    if faltan:
        raise ValueError(f"Respuestas de casos que ya no estan en el eval set: {faltan}. El eval set cambio "
                         "despues de generar: volver a generar con el eval set actual.")
    huellas = {g.id: huella(CRITERIO_PROMPT_VERSION, g.query, por_id[g.id]["criterio"], g.generated)
               for g in generaciones}
    done = load_checkpoint(checkpoint_path, huellas, log_prefix=log_prefix)

    salida: list[VeredictoCriterio] = []
    inicio, total = time.perf_counter(), len(generaciones)
    for i, g in enumerate(generaciones, start=1):
        rec = por_id[g.id]
        if g.id in done:
            e = done[g.id]
            veredicto, errores, justificacion, ok, raw = (
                e["veredicto"], e["errores_juridicos"], e["justificacion"], e["parse_ok"], e["raw_output"])
        else:
            raw = generate_fn(CRITERIO_SYSTEM_PROMPT,
                              build_criterio_prompt(g.query, rec["criterio"], rec["tipo"], g.generated),
                              max_tokens)
            veredicto, errores, justificacion, ok = parse_criterio_output(raw)
            if ok:   # sin respuesta (cupo, red) o ilegible: no se guarda, se reintenta al retomar
                append_checkpoint(checkpoint_path, {
                    "id": g.id, "huella": huellas[g.id], "veredicto": veredicto,
                    "errores_juridicos": errores, "justificacion": justificacion,
                    "parse_ok": ok, "raw_output": raw})
        salida.append(VeredictoCriterio(
            id=g.id, tipo=rec["tipo"], label=getattr(g, "label", ""), veredicto=veredicto,
            errores_juridicos=list(errores), justificacion=justificacion,
            n_citas=domain_metric.citation_count(g.generated), parse_ok=ok, raw_output=raw))
        if progress_every and (i % progress_every == 0 or i == total):
            prom = (time.perf_counter() - inicio) / i
            print(f"[{log_prefix}] {i}/{total} -- {prom:.1f}s/caso, ETA ~{prom * (total - i) / 60:.1f} min")
    return salida


def resumen(veredictos: Sequence[VeredictoCriterio]) -> dict:
    """Por modelo (label) y tipo de caso: conteos; aprobacion = proporcion de
    "cumple" con IC de Wilson; puntaje_medio (cumple 1, parcial 0.5) sin IC;
    respuestas con errores juridicos y con citas numeradas. Los casos sin
    veredicto se cuentan aparte (sin_veredicto) y no entran a las tasas."""
    grupos: dict[tuple[str, str], list[VeredictoCriterio]] = {}
    for v in veredictos:
        grupos.setdefault((v.label, v.tipo), []).append(v)
    salida: dict = {}
    for (label, tipo), vs in sorted(grupos.items()):
        validos = [v for v in vs if v.veredicto]
        conteo = {k: sum(1 for v in validos if v.veredicto == k) for k in VEREDICTOS}
        n = len(validos)
        tasa = proporcion(conteo["cumple"], n)
        con_error = proporcion(sum(1 for v in validos if v.errores_juridicos), n)
        salida.setdefault(label, {})[tipo] = {
            "n": n,
            "n_total": len(vs),
            "sin_veredicto": len(vs) - n,
            **conteo,
            "aprobacion": tasa.valor if tasa else None,
            "aprobacion_ic95": [tasa.bajo, tasa.alto] if tasa else None,
            "puntaje_medio": round(sum(v.puntaje for v in validos) / n, 4) if n else None,
            "con_errores_juridicos": con_error.valor if con_error else None,
            "errores_juridicos_total": sum(len(v.errores_juridicos) for v in validos),
            "con_citas_numeradas": sum(1 for v in vs if v.n_citas),   # sobre n_total
        }
    return salida


def generador_groq() -> GenerateFn:
    """Groq como backend (import perezoso: openai/dotenv solo cuando se usa)."""
    from tools.evaluation import external_judge

    return lambda system, user, max_tokens: external_judge.call_groq(system, user, max_tokens)
