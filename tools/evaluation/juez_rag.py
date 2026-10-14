"""Juez de las respuestas del RAG (M3): ¿le sirve la respuesta al usuario?

Por que existe. S10 juzgaba el RAG con el juez de M2 (criterio.py), que se
diseno para el modelo SIN contexto. Ese juez no ve los fragmentos que recibio el
modelo y su regla dice "no_cumple si afirma un numero de articulo sin poder
verificarlo": sin los fragmentos no puede verificar ninguno, asi que castiga
justo lo que se le pide al RAG, citar el articulo recuperado. En la corrida del
2026-10-14, 19 de los 22 "no cumple" en gold culpaban a las citas, y el
verificador (que si ve el contexto) encontro 0 citas sin respaldo. Ademas,
cuatro criterios gold piden "no citar el numero de ley": se escribieron para el
modelo sin RAG.

Regla de este juez (decision de Tomas, 2026-10-14: darle libertad, que responda
lo que se le pregunta):
  - ve los fragmentos que recibio el modelo;
  - el criterio del caso es una GUIA de lo que deberia orientar, no una lista
    que haya que cumplir palabra por palabra;
  - cumple = responde lo central de la consulta, de forma util y correcta;
  - citar articulos de los fragmentos que aplican esta bien, aunque el
    criterio diga no citar numeros;
  - citar un articulo que no aplica a la pregunta es un error AUNQUE este en
    los fragmentos (pertinencia, no solo procedencia);
  - abstenerse en una consulta normal es no responder.

Version rag-2026-10-14b. La primera (rag-2026-10-14) solo castigaba la cita que
no estaba en los fragmentos y ademas no aplicaba: una cita de los fragmentos que
no aplicaba pasaba como buena, y "basta con orientar en lo principal" dejaba
pasar respuestas que omitian lo esencial. Al revisar su linea base, unos 7 u 8
de los 17 "cumple" eran asi (9063 citaba bonos pensionales para una pregunta por
el valor de la pension; 9033 no mencionaba la estabilidad reforzada). Se
corrigio antes de medir ningun cambio de busqueda con el juez.

data/eval_set.json no se toca (su huella a5151999 liga M2 y M3, y para el
modelo sin contexto esos criterios siguen siendo correctos): la libertad de
citar la da esta regla, no un eval set editado.

Se reusa el motor de criterio.py entero (checkpoint, parseo, resumen con IC de
Wilson). Lo propio es el prompt y la huella, que incluye los fragmentos.

    python -m tools.evaluation.juez_rag --registros <eval_records.json> \
        --label A_denso --salida <dir>            # llama a Groq: requiere autorizacion
    python -m tools.evaluation.juez_rag --registros <eval_records.json> --ver 9001
        # imprime el prompt de un caso, sin llamar a nadie
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, Sequence

from tools.evaluation import criterio
from tools.evaluation.checkpoint import huella

# Cambia cuando cambia el prompt: entra en la huella del checkpoint.
JUEZ_RAG_PROMPT_VERSION = "rag-2026-10-14b"
MAX_CHARS_FRAGMENTO = 2000   # un fragmento tiene como mucho 350 tokens: no se recorta en la practica

JUEZ_RAG_SYSTEM_PROMPT = (
    "Eres un evaluador experto en derecho colombiano. Evaluas si un asistente "
    "juridico respondio bien la consulta de un usuario, con los fragmentos de "
    "normas que el asistente recibio para responder. Responde EXCLUSIVAMENTE con "
    "un JSON valido, sin texto antes ni despues, con este formato:\n"
    '{"veredicto": "cumple"|"parcial"|"no_cumple", '
    '"errores_juridicos": ["<afirmacion falsa o entidad equivocada>", ...], '
    '"justificacion": "<maximo 40 palabras>"}'
)


def formatear_fragmentos(record: dict) -> str:
    """'[1] Ley 820 de 2003 (...), Articulo 20\\n<texto>' por fragmento recibido."""
    textos = record.get("contexts") or []
    citas = [c.get("cita", "") for c in record.get("retrieved_chunks") or []]
    if not textos:
        return "(el asistente no recibio ningun fragmento)"
    partes = []
    for i, texto in enumerate(textos, start=1):
        cita = citas[i - 1] if i - 1 < len(citas) and citas[i - 1] else "fuente sin nombre"
        partes.append(f"[{i}] {cita}\n{(texto or '')[:MAX_CHARS_FRAGMENTO]}")
    return "\n\n".join(partes)


def build_prompt(query: str, guia: str, tipo: str, fragmentos: str, respuesta: str) -> str:
    return (
        f'Consulta del usuario:\n"{query}"\n\n'
        f"Tipo de caso: {tipo} "
        "(gold = consulta normal; adversarial = caso disenado para provocar un error).\n\n"
        f"Fragmentos de normas que recibio el asistente:\n{fragmentos}\n\n"
        "Guia del equipo: lo que una buena respuesta deberia orientar. No es una "
        f'lista que haya que cumplir palabra por palabra:\n"{guia}"\n\n'
        f'Respuesta a evaluar:\n"{respuesta}"\n\n'
        "Como juzgar. La pregunta es si la respuesta le sirve al usuario: responde lo "
        "que pregunto, con informacion correcta en derecho colombiano, y le dice que "
        "puede hacer.\n"
        "- cumple: responde lo central de la consulta, de forma util y correcta, y le "
        "dice al usuario que puede hacer. No hace falta que mencione todo lo de la "
        "guia, pero si lo esencial: si la guia senala algo como la clave del caso (una "
        "proteccion, un plazo, la entidad correcta) y la respuesta lo omite, no es "
        "cumple.\n"
        "- parcial: va en la direccion correcta, pero omite algo esencial, se apoya en "
        "un articulo que no aplica, o tiene una imprecision menor.\n"
        "- no_cumple: no responde (se niega, o solo remite a otro lado sin orientar), "
        "responde otra cosa, o contiene un error juridico que llevaria al usuario a "
        "actuar mal.\n"
        "- Citar articulos de los fragmentos que aplican a la pregunta esta bien y es "
        "lo que se espera, aunque la guia diga que no cite numeros de norma: esa "
        "indicacion se escribio para un asistente sin fragmentos.\n"
        "- Pero citar un articulo que NO aplica a la pregunta es un error AUNQUE "
        "aparezca en los fragmentos: estar en los fragmentos no lo hace pertinente. "
        "Si la respuesta se apoya en un articulo que no responde la pregunta, no es "
        "cumple.\n"
        "- En un caso adversarial, la guia describe la trampa: cumple si no cae en ella.\n"
        "- No premies ni castigues el estilo o la extension.\n"
        "errores_juridicos: lista cada afirmacion concreta que sea falsa en el derecho "
        "colombiano, cada entidad, autoridad o procedimiento equivocado para el caso o "
        "que no exista, y cada articulo citado que no aplica a la pregunta. No cuentes "
        "como error lo que solo esta incompleto. Lista vacia si no hay errores.\n"
        "Si la respuesta termina a mitad de frase, evalua solo lo que alcanza a decir."
    )


def generaciones(records: Sequence[dict], label: str) -> list[SimpleNamespace]:
    """Registros de `pipeline.to_eval_record` -> lo que espera el motor, con los fragmentos."""
    return [SimpleNamespace(id=r["id"], query=r["question"], generated=r["answer"], label=label,
                            fragmentos=formatear_fragmentos(r))
            for r in records]


def _prompt(g, rec: dict) -> str:
    return build_prompt(g.query, rec["criterio"], rec["tipo"], g.fragmentos, g.generated)


def _huella(g, rec: dict) -> str:
    return huella(JUEZ_RAG_PROMPT_VERSION, g.query, rec["criterio"], g.generated, g.fragmentos)


def evaluar(records: Sequence[dict], registros: Sequence[dict], generate_fn, label: str,
            checkpoint_path: Optional[Path] = None, progress_every: int = 5):
    """Veredictos (criterio.VeredictoCriterio) de las respuestas del RAG."""
    return criterio.evaluar_contra_criterio(
        generaciones(records, label), registros, generate_fn,
        checkpoint_path=checkpoint_path, progress_every=progress_every, log_prefix="juez_rag",
        system_prompt=JUEZ_RAG_SYSTEM_PROMPT, construir_prompt=_prompt, huella_fn=_huella)


def main(argv=None) -> int:
    from tools.evaluation import eval_set as eval_set_module

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registros", required=True, help="eval_records_*.json de S08 o S10")
    ap.add_argument("--label", default="rag")
    ap.add_argument("--salida", help="directorio del checkpoint y el resumen")
    ap.add_argument("--ver", type=int, help="imprime el prompt de ese caso y sale, sin llamar a Groq")
    a = ap.parse_args(argv)

    records = json.loads(Path(a.registros).read_text(encoding="utf-8"))
    registros = eval_set_module.load_eval_set()
    if a.ver is not None:
        por_id = {r["id"]: r for r in registros}
        g = next(x for x in generaciones(records, a.label) if x.id == a.ver)
        print(JUEZ_RAG_SYSTEM_PROMPT, "\n\n---\n", _prompt(g, por_id[g.id]))
        return 0
    if not a.salida:
        ap.error("--salida es obligatorio para juzgar")
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    veredictos = evaluar(records, registros, criterio.generador_groq(), a.label,
                         checkpoint_path=salida / f"juez_rag_checkpoint_{a.label}.jsonl")
    res = criterio.resumen(veredictos)
    (salida / f"juez_rag_resumen_{a.label}.json").write_text(
        json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for tipo, r in res.get(a.label, {}).items():
        print(f"{tipo:12} cumple {r['cumple']:2} | parcial {r['parcial']:2} | no cumple {r['no_cumple']:2}"
              f" | sin veredicto {r['sin_veredicto']} (de {r['n_total']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
