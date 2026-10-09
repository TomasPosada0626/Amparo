"""Juez sobre los ejemplos CON contexto: mide pertinencia, no solo procedencia.

Por que existe. M2 evalua los 231 de validacion de v1, que no traen contexto, y
los 75 del eval set. Los 103 ejemplos de validacion que SI traen contexto (los
de data/dataset_v2.jsonl) no los mira nadie con juez. Eso llevo a una revision
externa a concluir que "el modelo dejo de citar", porque sobre los 231 cita 0 %
-- que es lo correcto: ahi no hay de donde citar.

Y hay algo que las reglas no pueden medir. `cita_no_respaldada` comprueba que el
articulo citado estuviera en el contexto: PROCEDENCIA. No comprueba que ese
articulo responda la pregunta: PERTINENCIA. En la corrida del 2026-10-09, los 25
casos B2 en que el modelo cito teniendo un contexto que NO respondia dieron
todos "respaldada" -- el articulo si estaba ahi -- y las respuestas no servian:
a "me embargaron una cuenta en cero" respondio indemnizacion laboral. Ese fallo
hubo que encontrarlo leyendo respuestas una por una.

El criterio sale del modo, que es lo que el ejemplo pedia:

  B1  el contexto trae el articulo que responde -> debe citarlo y responder.
  B2  ningun fragmento sirve -> debe responder la frase de escape, sin citar.
  B3  el contexto responde una parte -> debe responder esa y decir cual falta.

Se reusa tools/evaluation/criterio.py entero (mismo juez, mismo prompt, mismos
checkpoints, mismo resumen con IC de Wilson): lo unico propio es redactar el
criterio a partir del modo.

    python -m tools.evaluation.criterio_contexto \
        --registros results/m1_2026-10-09/finetuned_results.jsonl \
        --salida results/m1_2026-10-09/
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, Sequence

from tools.evaluation import criterio

# La frase exacta que B2 debe producir. Se nombra en el criterio para que el
# juez no tenga que adivinar que cuenta como abstenerse.
from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO


# Masculinas por el tipo de norma; el resto van con "la".
_MASCULINAS = ("DECRETO", "ACUERDO", "CODIGO", "ESTATUTO")


def _nombres_comunes() -> dict[str, str]:
    """'LEY-1564-2012' -> 'Codigo General del Proceso', del catalogo del corpus.

    El catalogo lleva el identificador en el nombre de archivo
    (codigo_general_proceso_ley_1564_2012.md), asi que el slug se busca ahi.
    Import perezoso y tolerante: si tools.rag no esta disponible, el criterio
    sale sin el nombre comun en vez de romper la corrida del juez.
    """
    try:
        from tools.rag import corpus
    except Exception:
        return {}
    return {n.filename: n.nombre_comun for n in corpus.NORMAS_EN_ALCANCE if n.nombre_comun}


def _norma_legible(slug: str) -> str:
    """'LEY-820-2003' -> 'la Ley 820 de 2003 (Regimen de arrendamiento...)'.

    Esto no es cosmetica. El 2026-10-09 el criterio nombraba la norma por su
    slug y el juez marco 22 de 32 fallos de B1 con la forma "cita el articulo
    314 del Codigo General del Proceso EN LUGAR DE la Ley 1564 de 2012" -- que
    son la misma norma. El modelo habia citado bien. Nombrando las dos formas,
    el juez no puede fallar por comparacion de cadenas.
    """
    partes = slug.split("-")
    anio = partes[-1] if partes[-1].isdigit() and len(partes[-1]) == 4 else ""
    medio = partes[1:-1] if anio else partes[1:]
    tipo = partes[0]
    articulo = "el" if tipo.upper().startswith(_MASCULINAS) else "la"
    cuerpo = " ".join(w if w.isdigit() else w.capitalize() for w in [tipo, *medio])
    texto = f"{articulo} {cuerpo} de {anio}" if anio else f"{articulo} {cuerpo}"

    comun = next((v for k, v in _nombres_comunes().items()
                  if slug.lower().replace("-", "_") in k), "")
    return f"{texto} ({comun})" if comun else texto


def _fuentes_legibles(registro: dict) -> str:
    """'LEY-820-2003:20' -> 'el articulo 20 de la Ley 820 de 2003 (...)'."""
    partes = []
    for f in registro.get("fuentes") or ():
        texto = f if isinstance(f, str) else ":".join(map(str, f))
        if ":" in texto:
            norma, art = texto.rsplit(":", 1)
            partes.append(f"el articulo {art} de {_norma_legible(norma)}")
        else:
            partes.append(texto)
    return " y ".join(partes) if partes else "el articulo que responde"


# Se le dice al juez, explicitamente, que las dos formas valen. Sin esta frase
# el nombre comun en el criterio no basta: el juez sigue exigiendo la que leyo.
_FORMAS_VALIDAS = (
    " Nombrar la norma por su nombre comun o por su numero y anio es lo mismo: "
    "no es un error citar \"el Codigo General del Proceso\" donde el criterio "
    "dice \"la Ley 1564 de 2012\". Lo que importa es el numero del articulo."
)


def criterio_de_modo(registro: dict) -> str:
    """El criterio que el juez aplica, derivado del modo del ejemplo.

    En B2 se dice explicitamente que citar es un error grave y no un acierto
    parcial: es el caso donde la metrica por reglas se queda corta, porque el
    articulo citado SI estaba en el contexto.
    """
    modo = registro.get("modo")
    if modo == "B2":
        return (
            "El CONTEXTO que recibio NO contiene informacion que responda la pregunta. "
            f'Debe responder exactamente "{RESPUESTA_SIN_CONTEXTO}" y, si acaso, sugerir '
            "donde consultar. NO debe citar ningun articulo ni afirmar nada de fondo "
            "sobre el caso, aunque el contexto traiga articulos de otras materias: "
            "citarlos aqui es un error grave, no un acierto parcial."
        )
    if modo == "B3":
        return (
            f"El CONTEXTO respalda solo una parte de la respuesta: {_fuentes_legibles(registro)}. "
            "Debe responder esa parte citando esa norma, y decir explicitamente que la otra "
            "parte no esta respaldada por el contexto. Omitir esa advertencia es incumplir."
            + _FORMAS_VALIDAS
        )
    return (
        f"El CONTEXTO trae {_fuentes_legibles(registro)}, que es lo que responde la pregunta. "
        "Debe usarlo y citarlo (norma y numero) tal como aparece en el contexto. Citar un "
        "articulo distinto, que no responda la pregunta, es un error: no basta con que el "
        "articulo estuviera en el contexto."
        + _FORMAS_VALIDAS
    )


def preparar(registros: Sequence[dict], label: str = "fine_tuned") -> tuple[list, list[dict]]:
    """(generaciones, registros_con_criterio) para evaluar_contra_criterio.

    Solo los ejemplos con `modo`: los de v1 no traen contexto y los evalua M2.
    """
    generaciones, con_criterio = [], []
    for r in registros:
        # Dos formas de entrada. Los registros de dataset_v2 traen 'modo' y el
        # criterio se redacta a partir de el. Los de S08/S10 (pipeline.to_eval_record)
        # ya traen el 'criterio' del eval set y el contexto es el del retrieval
        # REAL: esos miden lo mismo pero en produccion, que es lo que de verdad
        # decide. Se aceptan los dos para no tener dos modulos que hagan lo mismo.
        propio = r.get("criterio") if not r.get("modo") else None
        if not r.get("modo") and not propio:
            continue
        generaciones.append(SimpleNamespace(
            id=r["id"],
            query=r.get("pregunta") or r.get("question") or r.get("query", ""),
            generated=r.get("generated") or r.get("answer", ""),
            label=label,
        ))
        con_criterio.append({
            "id": r["id"],
            # El "tipo" parte la tabla del resumen. Con 'modo' es B1/B2/B3, que
            # es el corte donde se ve si aprendio a abstenerse; con el criterio
            # propio es gold/adversarial, el corte del eval set.
            "tipo": r.get("modo") or r.get("tipo", "caso"),
            "category": r.get("category", ""),
            "criterio": propio or criterio_de_modo(r),
        })
    return generaciones, con_criterio


def evaluar(
    registros: Sequence[dict],
    generate_fn,
    *,
    label: str = "fine_tuned",
    checkpoint_path: Optional[Path] = None,
) -> list:
    generaciones, con_criterio = preparar(registros, label=label)
    if not generaciones:
        raise SystemExit(
            "Ningun registro trae 'modo': estos no son los ejemplos con contexto. "
            "Se esperan las respuestas sobre la validacion de data/dataset_v2.jsonl."
        )
    return criterio.evaluar_contra_criterio(
        generaciones, con_criterio, generate_fn,
        checkpoint_path=checkpoint_path, log_prefix="contexto")


def imprimir(resumen: dict, label: str) -> None:
    cabecera = "modo".ljust(6) + "n".rjust(5) + "cumple".rjust(9) + "parcial".rjust(9) + "no cumple".rjust(11)
    print()
    print(cabecera)
    print("-" * len(cabecera))
    for modo, d in sorted(resumen.get(label, {}).items()):
        fila = (modo.ljust(6) + str(d["n"]).rjust(5) + str(d["cumple"]).rjust(9)
                + str(d["parcial"]).rjust(9) + str(d["no_cumple"]).rjust(11))
        print(fila)

    # B2 es el corte que importa: ahi el contexto no responde y lo correcto es
    # abstenerse. Si la tasa es baja, aprendio a citar pero no a callarse.
    b2 = resumen.get(label, {}).get("B2")
    if b2 and b2["n"] and b2["cumple"] / b2["n"] < 0.5:
        print()
        print(f"AVISO: solo {b2['cumple']} de {b2['n']} casos B2 se abstuvieron como debian.")
        print("       El modelo responde usando contexto que no responde la pregunta.")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registros", required=True,
                   help="jsonl con las respuestas (p. ej. finetuned_results.jsonl)")
    p.add_argument("--salida", required=True, help="carpeta donde escribir el resumen")
    p.add_argument("--label", default="fine_tuned")
    args = p.parse_args(argv)

    texto = Path(args.registros).read_text(encoding="utf-8")
    registros = [json.loads(l) for l in texto.splitlines() if l.strip()]
    salida = Path(args.salida)
    (salida / "checkpoints").mkdir(parents=True, exist_ok=True)

    veredictos = evaluar(registros, criterio.generador_groq(), label=args.label,
                         checkpoint_path=salida / "checkpoints" / "groq_criterio_contexto.jsonl")

    resumen = criterio.resumen(veredictos)
    (salida / "groq_contexto_resumen.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")

    detalle = [{"id": v.id, "modo": v.tipo, "veredicto": v.veredicto,
                "errores": v.errores_juridicos, "justificacion": v.justificacion}
               for v in veredictos]
    (salida / "contexto_resultados.jsonl").write_text(
        "\n".join(json.dumps(d, ensure_ascii=False) for d in detalle) + "\n", encoding="utf-8")

    imprimir(resumen, args.label)
    print()
    print(f"Escrito {salida / 'groq_contexto_resumen.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
