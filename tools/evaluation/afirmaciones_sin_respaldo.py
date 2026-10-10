"""Afirmaciones juridicas sustantivas que el contexto entregado no respalda.

El hueco que cubre. `verificacion.citas_no_verificables` acepta una cita si el
articulo **se recupero**, no si **responde**. Y una respuesta puede afirmar una
competencia institucional sin citar nada, con lo que no hay nada que verificar.
Las dos rutas dejan pasar una afirmacion sin respaldo:

    caso 2229: "Pide por escrito la reparacion y, si no la hacen, acude a la
               Superintendencia de Servicios Publicos Domiciliarios."

Ninguna cita inventada, ninguna entidad inexistente -- la Superintendencia
existe --, y una competencia institucional afirmada que el contexto no
sostiene. `B` la aprueba; la adjudicacion la marco como afirmacion sin
respaldo.

Que detecta esto, y que no. Detecta **el complemento de
`entity_metric.find_fabricated_entities`**: aquella busca entidades que no
existen; esta busca entidades que **si existen** y que el contexto entregado
**no menciona**. Se reutiliza el mismo extractor -- cabezas, nexos y lista
blanca -- para no tener dos definiciones de "forma institucional".

No detecta: que un articulo citado correctamente no sostenga la afirmacion
(caso 2917), ni la atribucion entre articulos vecinos de la misma ley (3328).
Eso es juicio juridico y asi esta documentado en `verificacion.py`.

**Es una señal de revision, no una puerta automatica.** Una entidad puede ser
la correcta aunque el contexto no la nombre -- el contexto trae normas, no
directorios de competencias --, asi que una marca significa "esto no se puede
verificar con lo que se le dio al modelo", no "esto es falso".

    python -m tools.evaluation.afirmaciones_sin_respaldo
"""
from __future__ import annotations

import re

from tools.evaluation.entity_metric import (
    CABEZAS,
    ENTIDADES_REALES,
    NEXOS,
    _MAX_PALABRAS,
    _PALABRA,
    _normalizar,
)


def entidades_mencionadas(texto: str) -> list[tuple[str, bool]]:
    """[(nombre, esta_en_la_lista_blanca)] de cada mencion con forma institucional.

    Mismo criterio que `entity_metric._marcar`: una cabeza ("Superintendencia",
    "Ministerio"...) seguida de un nexo ("de", "del", "nacional"...). Sin nexo
    es uso generico -- "la Procuraduria" -- y no hay nombre propio que
    verificar.
    """
    salida: list[tuple[str, bool]] = []
    norm = _normalizar(texto or "")
    for m in re.finditer(rf"\b({'|'.join(CABEZAS)})\b", norm):
        palabras = re.findall(_PALABRA, norm[m.start():])[: _MAX_PALABRAS + 1]
        if len(palabras) < 2 or palabras[1] not in NEXOS:
            continue
        canonica = None
        for n in range(len(palabras), 0, -1):
            if " ".join(palabras[:n]) in ENTIDADES_REALES:
                canonica = " ".join(palabras[:n])
                break
        salida.append((canonica or " ".join(palabras[:4]), canonica is not None))
    return salida


def competencias_sin_respaldo(respuesta: str, contexto_texto: str) -> list[str]:
    """Entidades REALES que la respuesta nombra y el contexto entregado no.

    `contexto_texto` es el texto que de verdad se le paso al modelo, no un
    resumen ni la lista de citas: lo que importa es si la persona podria
    verificar la competencia con lo que el sistema tenia delante.
    """
    ctx = _normalizar(contexto_texto or "")
    return sorted({nombre for nombre, es_real in entidades_mencionadas(respuesta)
                   if es_real and nombre not in ctx})


def revisar(respuesta: str, contexto_texto: str, resultados=()) -> dict:
    """Las tres señales juntas, cada una por separado.

    No se fusionan en un booleano: miden cosas distintas y una puerta unica
    esconderia cual se activo.
    """
    from tools.evaluation import entity_metric
    from tools.rag.verificacion import citas_no_verificables, promete_resultado

    return {
        "competencias_sin_respaldo": competencias_sin_respaldo(respuesta, contexto_texto),
        "entidades_inventadas": entity_metric.find_fabricated_entities(respuesta),
        "citas_no_verificables": (citas_no_verificables(respuesta, resultados)
                                  if resultados else []),
        "promete_resultado": promete_resultado(respuesta),
    }


def main(argv=None) -> int:
    """Evaluacion contra la adjudicacion aprobada, con los conjuntos separados.

    DESARROLLO: los 7 casos que se inspeccionaron al diseñar el detector.
    RESERVADO A: los otros 28 de v1, no vistos durante el diseño.
    RESERVADO B: los 35 de v2, con adjudicacion independiente.
    """
    import csv
    import json
    from pathlib import Path

    from tools.evaluation import config as eval_config

    RAIZ = eval_config.PROJECT_ROOT
    DESARROLLO = {"2229", "2126", "2221", "2424", "3517", "3920", "4324"}

    filas = {x["case_id"]: x for x in csv.DictReader(
        (RAIZ / "docs" / "m1_b2_adjudicacion.csv").open(encoding="utf-8", newline=""))}
    corridas = {
        "v1": RAIZ / "results" / "m1_2026-10-09" / "finetuned_results.jsonl",
        "v2": RAIZ / "results" / "m1_v2_2026-10-09" / "finetuned_results.jsonl",
    }

    def evaluar(modelo: str, solo: set[str] | None, excluir: set[str] | None):
        regs = {str(r["id"]): r for r in (json.loads(x) for x in
                corridas[modelo].read_text(encoding="utf-8").splitlines() if x.strip())}
        vp = fp = vn = fn = 0
        fallos = []
        for cid, fila in filas.items():
            if solo and cid not in solo:
                continue
            if excluir and cid in excluir:
                continue
            r = regs.get(cid)
            if not r:
                continue
            ctx = next(m["content"] for m in r["messages"] if m["role"] == "user")
            marcas = competencias_sin_respaldo(r.get("generated") or "", ctx)
            # Verdad: la adjudicacion aprobada marco una afirmacion sin respaldo
            esperado = bool(fila[f"{modelo}_afirmaciones_sin_respaldo"].strip())
            if esperado and marcas:
                vp += 1
            elif esperado and not marcas:
                fn += 1
                fallos.append(("FN", cid, fila[f"{modelo}_afirmaciones_sin_respaldo"][:90]))
            elif not esperado and marcas:
                fp += 1
                fallos.append(("FP", cid, str(marcas)))
            else:
                vn += 1
        return vp, fp, vn, fn, fallos

    print("DETECTOR DE COMPETENCIAS INSTITUCIONALES SIN RESPALDO")
    print("Verdad: el campo <modelo>_afirmaciones_sin_respaldo de la adjudicacion")
    print()
    conjuntos = [
        ("DESARROLLO  (7 de v1, vistos al diseñar)", "v1", DESARROLLO, None),
        ("RESERVADO A (28 de v1, no vistos)", "v1", None, DESARROLLO),
        ("RESERVADO B (35 de v2, adjudicacion propia)", "v2", None, None),
    ]
    for nombre, modelo, solo, excluir in conjuntos:
        vp, fp, vn, fn, fallos = evaluar(modelo, solo, excluir)
        n = vp + fp + vn + fn
        prec = vp / (vp + fp) if vp + fp else float("nan")
        rec = vp / (vp + fn) if vp + fn else float("nan")
        print(f"{nombre}   n={n}")
        print(f"   VP={vp}  FP={fp}  VN={vn}  FN={fn}   "
              f"precision={prec:.2f}  recall={rec:.2f}")
        for tipo, cid, det in fallos[:6]:
            print(f"     {tipo} {cid}: {det}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
