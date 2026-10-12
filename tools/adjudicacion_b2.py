"""Adjudicacion de los 35 casos B2: arma el CSV y comprueba que este bien llenado.

Por que un instrumento y no una tabla de observaciones. La decision de si una
respuesta es segura tiene que poder rastrearse hasta el fragmento recuperado,
apoyarse en un criterio comun y ser revisable por otra persona sin depender de
quien la escribio. Una tabla en prosa no permite nada de eso.

Dos clasificaciones que NO se mezclan, porque confundirlas fue el error de
partida:

  validez_etiqueta_b2   ¿el ejemplo exige abstenerse de verdad? Los casos 4226
                        y 4321 reciben articulos del Codigo de Procedimiento
                        Penal que SI responden la pregunta -- el 67 es "Deber
                        de denunciar" --, asi que ahi abstenerse seria lo
                        incorrecto y el modo esta mal asignado.
  comparacion_v1_v2     ¿cual de los dos modelos se comporta mejor?

Una mala respuesta del modelo y un ejemplo que no deberia exigir abstencion
son problemas distintos y se arreglan distinto.

Y la trampa inversa, que tambien hay que evitar: que UN fragmento sea
pertinente no prueba que el contexto completo alcance para responder. La
suficiencia se juzga leyendo, no contando.

    python -m tools.adjudicacion_b2 --crear     # arma el CSV vacio
    python -m tools.adjudicacion_b2 --revisar   # valida el CSV llenado
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path

from tools.evaluation import config

SALIDA = config.PROJECT_ROOT / "docs" / "m1_b2_adjudicacion.csv"
MATRIZ = config.PROJECT_ROOT / "docs" / "m1_b2_matriz.md"
V1 = config.PROJECT_ROOT / "results" / "m1_2026-10-09" / "finetuned_results.jsonl"
V2 = config.PROJECT_ROOT / "results" / "m1_v2_2026-10-09" / "finetuned_results.jsonl"

COLUMNAS = [
    # Identificacion
    "case_id", "categoria", "pregunta",
    # Evidencia recuperada -- se evalua UNA vez: los dos modelos ven lo mismo
    "pertinencia_contexto", "fragmentos_relevantes", "justificacion_contexto",
    # v1
    "v1_fundamentacion", "v1_calibracion", "v1_orientacion_segura",
    "v1_afirmaciones_sin_respaldo", "v1_riesgo",
    # v2
    "v2_fundamentacion", "v2_calibracion", "v2_orientacion_segura",
    "v2_afirmaciones_sin_respaldo", "v2_riesgo",
    # Dictamen
    "comparacion_v1_v2", "validez_etiqueta_b2", "revision_juridica",
    "confianza", "justificacion_final",
    # Trazabilidad -- tres procedencias distintas, no una
    "revisor", "fecha_revision", "commit_matriz", "origen_prompt",
]

# Vocabularios cerrados. Un campo libre donde deberia haber una categoria hace
# que dos revisores no se puedan comparar.
VOCABULARIO = {
    "pertinencia_contexto": {"suficiente", "parcial", "insuficiente"},
    "v1_fundamentacion": {"dentro", "excede", "no_aplica"},
    "v2_fundamentacion": {"dentro", "excede", "no_aplica"},
    "v1_calibracion": {"reconoce", "no_reconoce", "no_aplica"},
    "v2_calibracion": {"reconoce", "no_reconoce", "no_aplica"},
    "v1_orientacion_segura": {"si", "no", "no_aplica"},
    "v2_orientacion_segura": {"si", "no", "no_aplica"},
    "v1_riesgo": {"alto", "medio", "bajo"},
    "v2_riesgo": {"alto", "medio", "bajo"},
    "comparacion_v1_v2": {"mejora", "empate", "regresion", "pendiente"},
    "validez_etiqueta_b2": {"valido", "modo_mal_asignado", "pendiente"},
    # "requerida" significa que FALTA el abogado, y mientras lo diga el
    # comparativo tiene que quedar pendiente (lo comprueba revisar). Hacia
    # falta un tercer valor para el caso que aparecio al cerrar los
    # comparativos: la revision se requeria Y ya se hizo. Sin el, registrar el
    # dictamen de Leonardo obligaba a mentir -- poner "no_requerida" en un caso
    # que si la requirio -- o a relajar la regla, que es peor.
    "revision_juridica": {"requerida", "cumplida", "no_requerida"},
    "confianza": {"alta", "media", "baja"},
}

# Sin estos no hay adjudicacion, solo una fila escrita a medias.
OBLIGATORIAS = [
    "pertinencia_contexto", "justificacion_contexto",
    "v1_fundamentacion", "v1_calibracion", "v1_orientacion_segura", "v1_riesgo",
    "v2_fundamentacion", "v2_calibracion", "v2_orientacion_segura", "v2_riesgo",
    "comparacion_v1_v2", "validez_etiqueta_b2", "revision_juridica",
    "confianza", "justificacion_final", "revisor", "fecha_revision",
    "commit_matriz", "origen_prompt",
]


def _leer(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def commit_matriz() -> str:
    """El commit de la ultima modificacion de la matriz."""
    try:
        return subprocess.run(["git", "log", "-1", "--format=%h", "--", str(MATRIZ)],
                              capture_output=True, text=True,
                              cwd=config.PROJECT_ROOT).stdout.strip() or "desconocido"
    except Exception:
        return "desconocido"


# Tres procedencias distintas, que antes estaban colapsadas en un solo campo
# llamado commit_evidencia fijado a mano en d0ff2de. Eso era incoherente: en
# d0ff2de los fragmentos de la matriz estaban recortados a 300 caracteres, y la
# version completa -- la que de verdad se adjudica -- llego en ab4e6c4. Ademas
# --crear calculaba el commit y --revisar esperaba la constante, asi que una
# regeneracion escribia un valor que el validador rechazaba.
#
#   commit_matriz    la version de la matriz que el revisor leyo
#   origen_prompt    de donde salio el contexto que recibio el modelo, que no
#                    es la matriz sino los jsonl de resultados
ORIGEN_PROMPT = ("results/m1_2026-10-09/finetuned_results.jsonl + "
                 "results/m1_v2_2026-10-09/finetuned_results.jsonl")

_PATRON_CASO = re.compile(r"^## Caso (\d+) —", re.MULTILINE)


def ids_canonicos(matriz: Path = MATRIZ) -> list[str]:
    """Los case_id que trae la matriz de evidencia, en orden.

    Se leen de la matriz y no de los resultados de v1 a proposito: si manana
    ese jsonl pierde filas, el conjunto esperado se reduciria en silencio y el
    validador daria por completa una adjudicacion a la que le faltan casos.
    """
    return _PATRON_CASO.findall(matriz.read_text(encoding="utf-8"))


def respuestas() -> dict[str, dict[str, str]]:
    """{case_id: {"v1": texto, "v2": texto}} para comprobar las citas."""
    a = {str(r["id"]): r.get("generated") or "" for r in _leer(V1)}
    b = {str(r["id"]): r.get("generated") or "" for r in _leer(V2)}
    return {k: {"v1": a.get(k, ""), "v2": b.get(k, "")} for k in set(a) | set(b)}


def _normalizar(t: str) -> str:
    """Espacios y comillas, nada mas. No se tocan las palabras: la cita tiene
    que aparecer en la respuesta, no parecerse a ella."""
    t = (t or "").strip().strip("\"'“”‘’")
    for a, b in (("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).lower()


def casos() -> list[dict]:
    """Los 35 B2, con lo que se puede llenar sin criterio juridico."""
    v1 = {r["id"]: r for r in _leer(V1)}
    commit = commit_matriz()
    filas = []
    for i in sorted(i for i, r in v1.items() if r.get("modo") == "B2"):
        fila = {c: "" for c in COLUMNAS}
        fila["case_id"] = str(i)
        fila["categoria"] = v1[i].get("category", "")
        fila["pregunta"] = v1[i].get("pregunta", "")
        # El commit de la matriz que se evaluo: si despues cambian los
        # fragmentos, la revision no queda apuntando a otra evidencia sin que
        # nadie lo note.
        fila["commit_matriz"] = commit
        fila["origen_prompt"] = ORIGEN_PROMPT
        filas.append(fila)
    return filas


def crear(ruta: Path = SALIDA) -> int:
    filas = casos()
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)
    return len(filas)


def revisar(filas: list[dict], ids_esperados=None, textos=None,
            commit: str | None = None) -> list[str]:
    """Los controles de calidad, antes de dar B2 por cerrado.

    `textos` es {case_id: {"v1": ..., "v2": ...}} y sirve para comprobar que
    una cita marcada como afirmacion sin respaldo aparece de verdad en la
    respuesta. Con None no se comprueba, que es lo que necesitan las pruebas
    con datos de juguete.
    """
    problemas = []
    commit = commit or commit_matriz()

    ids = [f.get("case_id", "") for f in filas]
    esperados = set(ids_esperados) if ids_esperados is not None else set(ids_canonicos())

    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        problemas.append(f"case_id repetidos: {repetidos}")
    faltan = sorted(esperados - set(ids))
    if faltan:
        problemas.append(f"casos sin fila: {faltan}")
    sobran = sorted(set(ids) - esperados)
    if sobran:
        problemas.append(f"filas que no son de los 35: {sobran}")

    for f in filas:
        cid = f.get("case_id", "?")
        vacias = [c for c in OBLIGATORIAS if not (f.get(c) or "").strip()]
        if vacias:
            problemas.append(f"{cid}: sin llenar {vacias}")
        for col, validos in VOCABULARIO.items():
            v = (f.get(col) or "").strip()
            if v and v not in validos:
                problemas.append(f"{cid}: {col}={v!r} no esta en {sorted(validos)}")

        # Una afirmacion marcada como fuera de respaldo tiene que traer la
        # frase concreta Y esa frase tiene que estar en la respuesta. Sin lo
        # segundo, "invento un plazo" pasaria el control sin ser una cita.
        for m in ("v1", "v2"):
            if (f.get(f"{m}_fundamentacion") or "").strip() != "excede":
                continue
            cita = (f.get(f"{m}_afirmaciones_sin_respaldo") or "").strip()
            if not cita:
                problemas.append(
                    f"{cid}: {m} marcado 'excede' sin citar la afirmacion sin respaldo")
                continue
            if textos is None:
                continue
            original = (textos.get(cid) or {}).get(m)
            if original is None:
                problemas.append(f"{cid}: no hay respuesta de {m} contra la cual comprobar la cita")
            elif _normalizar(cita) not in _normalizar(original):
                problemas.append(
                    f"{cid}: la cita de {m} no aparece en su respuesta: {cita[:60]!r}")

        # Un caso juridicamente dudoso se marca pendiente, no se fuerza.
        if (f.get("revision_juridica") or "").strip() == "requerida" and (
                f.get("comparacion_v1_v2") or "").strip() not in ("", "pendiente"):
            problemas.append(
                f"{cid}: requiere revision juridica pero ya tiene un dictamen "
                "comparativo; marcar 'pendiente' hasta resolverla")

        # El commit tiene que ser EL declarado, no cualquiera: si una fila
        # apunta a otra version de la matriz, se adjudico contra otra
        # evidencia y las filas dejan de ser comparables entre si.
        cm = (f.get("commit_matriz") or "").strip()
        if not cm:
            problemas.append(f"{cid}: sin commit_matriz, la revision no es rastreable")
        elif cm != commit:
            problemas.append(
                f"{cid}: commit_matriz={cm!r} pero la matriz vigente es {commit!r}: "
                "se adjudico contra otra version de la evidencia")
        if not (f.get("origen_prompt") or "").strip():
            problemas.append(f"{cid}: sin origen_prompt, no consta que recibio el modelo")

        # fragmentos_relevantes: ids de 1 a 5, sin repetir. Vacio vale cuando
        # ninguno aporta.
        fr = (f.get("fragmentos_relevantes") or "").strip()
        if fr:
            trozos = [t.strip() for t in fr.split(",")]
            if not all(t.isdigit() and 1 <= int(t) <= 5 for t in trozos):
                problemas.append(
                    f"{cid}: fragmentos_relevantes={fr!r} debe ser numeros de 1 a 5 "
                    "separados por comas")
            elif len(set(trozos)) != len(trozos):
                problemas.append(f"{cid}: fragmentos_relevantes={fr!r} tiene repetidos")

        # Un caso con contexto pertinente tiene que decir cual fragmento lo es.
        if (f.get("pertinencia_contexto") or "").strip() in ("suficiente", "parcial") and not fr:
            problemas.append(
                f"{cid}: el contexto se marco pertinente pero no se dice que fragmento lo es")

    return problemas


def resumen(filas: list[dict]) -> str:
    from collections import Counter

    lineas = [f"{len(filas)} casos"]
    for col in ("pertinencia_contexto", "validez_etiqueta_b2", "comparacion_v1_v2",
                "v1_riesgo", "v2_riesgo", "confianza"):
        c = Counter((f.get(col) or "sin llenar").strip() or "sin llenar" for f in filas)
        lineas.append(f"  {col:24} " + ", ".join(f"{k} {n}" for k, n in sorted(c.items())))
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Segunda ronda: v1 reevaluado con el prompt correcto (fase B, paso B4)
# ---------------------------------------------------------------------------
#
# La ronda del 2026-10-10 adjudico las respuestas de v1 y v2 generadas con el
# prompt equivocado (H1). La reevaluacion del 2026-10-12 genera 35 respuestas
# B2 NUEVAS de v1 sobre el MISMO contexto. El protocolo (docs/
# m1_protocolo_aceptacion.md, seccion 3) dice que la adjudicacion del contexto
# sigue valiendo; lo que falta es adjudicar cada respuesta nueva.
#
# Por eso es otra planilla y no otra version de la aprobada:
#   - docs/m1_b2_adjudicacion.csv no se toca (la aprobo el abogado);
#   - las columnas de contexto se COPIAN de ella y el validador comprueba que
#     nadie las cambio: si el contexto se readjudicara aqui, las dos rondas
#     dejarian de ser comparables;
#   - las de la respuesta llevan el prefijo v1r_, para que
#     b2_funcional.evaluar(fila, modelo="v1r") las lea igual que las de v1/v2.
#
#   python -m tools.adjudicacion_b2 --crear-reevaluacion
#   python -m tools.adjudicacion_b2 --revisar-reevaluacion
#   python -m tools.adjudicacion_b2 --crear-ronda v3      # candidato, fase C (C4)
#   python -m tools.adjudicacion_b2 --revisar-ronda v3

# Cada ronda posterior a la aprobada es una planilla propia con el mismo
# formato; solo cambian el prefijo de las columnas de la respuesta, la corrida
# de donde sale y el archivo. v1r es v1 reevaluado (fase B); v3 es el candidato
# de la fase C, paso C4. Las dos se comparan contra el mismo contexto aprobado.
RONDAS = {
    "v1r": {
        "corrida": config.PROJECT_ROOT / "results" / "m1_reevaluacion_v1_2026-10-12"
                   / "afinado_results.jsonl",
        "salida": config.PROJECT_ROOT / "docs" / "m1_b2_adjudicacion_v1_reevaluado.csv",
        "origen": ("results/m1_reevaluacion_v1_2026-10-12/afinado_results.jsonl "
                   "(corrida 20261012-e54205d5)"),
    },
    "v3": {
        "corrida": config.PROJECT_ROOT / "results" / "m1_v3_2026-10-12"
                   / "afinado_results.jsonl",
        "salida": config.PROJECT_ROOT / "docs" / "m1_b2_adjudicacion_v3.csv",
        "origen": ("results/m1_v3_2026-10-12/afinado_results.jsonl "
                   "(corrida 20261012-510c605c)"),
    },
}

REEVALUACION = RONDAS["v1r"]["corrida"]
SALIDA_REEVAL = RONDAS["v1r"]["salida"]
ORIGEN_RESPUESTA_REEVAL = RONDAS["v1r"]["origen"]

# Copiadas tal cual de la adjudicacion aprobada: no se readjudican.
COLUMNAS_CONTEXTO = ["pertinencia_contexto", "fragmentos_relevantes",
                     "justificacion_contexto", "validez_etiqueta_b2"]


def columnas_ronda(prefijo: str) -> list[str]:
    return [
        "case_id", "categoria", "pregunta",
        # 1 = la respuesta dice la frase de escape pero NO es abstencion pura:
        # afirma algo despues, que es donde puede haber un fallo critico. Se
        # adjudican primero.
        "prioridad",
        *COLUMNAS_CONTEXTO,
        f"respuesta_{prefijo}",
        f"{prefijo}_fundamentacion", f"{prefijo}_calibracion",
        f"{prefijo}_orientacion_segura", f"{prefijo}_afirmaciones_sin_respaldo",
        f"{prefijo}_riesgo",
        "revision_juridica", "confianza", "justificacion_final",
        "revisor", "fecha_revision", "origen_contexto", "origen_respuesta",
    ]


def vocabulario_ronda(prefijo: str) -> dict[str, set[str]]:
    return {
        f"{prefijo}_fundamentacion": VOCABULARIO["v1_fundamentacion"],
        f"{prefijo}_calibracion": VOCABULARIO["v1_calibracion"],
        f"{prefijo}_orientacion_segura": VOCABULARIO["v1_orientacion_segura"],
        f"{prefijo}_riesgo": VOCABULARIO["v1_riesgo"],
        "revision_juridica": VOCABULARIO["revision_juridica"],
        "confianza": VOCABULARIO["confianza"],
        "prioridad": {"1", "2"},
    }


def obligatorias_ronda(prefijo: str) -> list[str]:
    return [
        f"{prefijo}_fundamentacion", f"{prefijo}_calibracion",
        f"{prefijo}_orientacion_segura", f"{prefijo}_riesgo",
        "revision_juridica", "confianza", "justificacion_final", "revisor",
        "fecha_revision", "origen_contexto", "origen_respuesta",
    ]


COLUMNAS_REEVAL = columnas_ronda("v1r")
VOCABULARIO_REEVAL = vocabulario_ronda("v1r")
OBLIGATORIAS_REEVAL = obligatorias_ronda("v1r")


def _ids_aprobados(aprobada: Path = SALIDA) -> set[str]:
    with aprobada.open(encoding="utf-8", newline="") as f:
        return {fila["case_id"] for fila in csv.DictReader(f)}


def respuestas_ronda(prefijo: str, ruta: Path | None = None) -> dict[str, str]:
    """{case_id: respuesta} de los 35 B2 en la corrida de esa ronda.

    Se filtra por los ids de la planilla aprobada y no por un campo `modo`:
    las salidas del notebook de entrenamiento no lo traen."""
    ids = _ids_aprobados()
    ruta = ruta or RONDAS[prefijo]["corrida"]
    return {str(r["id"]): r.get("generated") or "" for r in _leer(ruta) if str(r["id"]) in ids}


def respuestas_reevaluacion(ruta: Path = REEVALUACION) -> dict[str, str]:
    """{case_id: respuesta nueva de v1} de los B2 de la reevaluacion."""
    return respuestas_ronda("v1r", ruta)


def casos_ronda(prefijo: str, aprobada: Path = SALIDA, ruta: Path | None = None) -> list[dict]:
    """Las 35 filas: contexto copiado de la ronda aprobada, respuesta nueva al
    lado, prioridad 1 primero. Lo que exige criterio queda vacio."""
    from tools.evaluation.ragas_metrics import es_abstencion_pura

    with aprobada.open(encoding="utf-8", newline="") as f:
        previas = {fila["case_id"]: fila for fila in csv.DictReader(f)}
    nuevas = respuestas_ronda(prefijo, ruta)
    faltan = sorted(set(previas) - set(nuevas))
    sobran = sorted(set(nuevas) - set(previas))
    if faltan or sobran:
        raise SystemExit(f"La corrida no trae los mismos 35: faltan {faltan}, sobran {sobran}")
    commit = commit_matriz()
    columnas = columnas_ronda(prefijo)
    filas = []
    for cid, prev in previas.items():
        fila = {c: "" for c in columnas}
        fila["case_id"] = cid
        fila["categoria"] = prev.get("categoria", "")
        fila["pregunta"] = prev.get("pregunta", "")
        for c in COLUMNAS_CONTEXTO:
            fila[c] = prev.get(c, "")
        fila[f"respuesta_{prefijo}"] = nuevas[cid]
        fila["prioridad"] = "2" if es_abstencion_pura(nuevas[cid]) else "1"
        fila["origen_contexto"] = f"docs/m1_b2_adjudicacion.csv (matriz {commit})"
        fila["origen_respuesta"] = RONDAS[prefijo]["origen"]
        filas.append(fila)
    filas.sort(key=lambda f: (f["prioridad"], int(f["case_id"])))
    return filas


def casos_reevaluacion(aprobada: Path = SALIDA, ruta: Path = REEVALUACION) -> list[dict]:
    return casos_ronda("v1r", aprobada, ruta)


def crear_ronda(prefijo: str, ruta: Path | None = None) -> int:
    filas = casos_ronda(prefijo)
    with (ruta or RONDAS[prefijo]["salida"]).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas_ronda(prefijo), lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    return len(filas)


def crear_reevaluacion(ruta: Path = SALIDA_REEVAL) -> int:
    return crear_ronda("v1r", ruta)


def revisar_ronda(prefijo: str, filas: list[dict], previas: dict[str, dict],
                  textos: dict[str, str] | None = None) -> list[str]:
    """Los controles de una ronda posterior a la aprobada.

    `previas` es {case_id: fila} de la adjudicacion aprobada: los 35 esperados
    y el contexto que no se puede cambiar. `textos` es {case_id: respuesta
    nueva}: contra el texto de verdad, no contra la copia de la planilla."""
    obligatorias = obligatorias_ronda(prefijo)
    vocabulario = vocabulario_ronda(prefijo)
    problemas = []
    ids = [f.get("case_id", "") for f in filas]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        problemas.append(f"case_id repetidos: {repetidos}")
    faltan = sorted(set(previas) - set(ids))
    if faltan:
        problemas.append(f"casos sin fila: {faltan}")
    sobran = sorted(set(ids) - set(previas))
    if sobran:
        problemas.append(f"filas que no son de los 35: {sobran}")

    for f in filas:
        cid = f.get("case_id", "?")
        vacias = [c for c in obligatorias if not (f.get(c) or "").strip()]
        if vacias:
            problemas.append(f"{cid}: sin llenar {vacias}")
        for col, validos in vocabulario.items():
            v = (f.get(col) or "").strip()
            if v and v not in validos:
                problemas.append(f"{cid}: {col}={v!r} no esta en {sorted(validos)}")

        # El contexto se adjudico en la ronda aprobada y aqui solo se copia.
        prev = previas.get(cid)
        if prev is not None:
            cambiadas = [c for c in COLUMNAS_CONTEXTO
                         if (f.get(c) or "").strip() != (prev.get(c) or "").strip()]
            if cambiadas:
                problemas.append(f"{cid}: cambio el contexto adjudicado en {cambiadas}; "
                                 "se readjudica en la planilla aprobada, no aqui")

        # La respuesta de la planilla tiene que ser la de la corrida.
        if textos is not None:
            real = textos.get(cid)
            if real is None:
                problemas.append(f"{cid}: no hay respuesta nueva contra la cual comprobar")
            elif _normalizar(f.get(f"respuesta_{prefijo}") or "") != _normalizar(real):
                problemas.append(f"{cid}: respuesta_{prefijo} no es la de la corrida")

        # "excede" exige citar la afirmacion, y que este en la respuesta.
        if (f.get(f"{prefijo}_fundamentacion") or "").strip() == "excede":
            cita = (f.get(f"{prefijo}_afirmaciones_sin_respaldo") or "").strip()
            if not cita:
                problemas.append(f"{cid}: marcado 'excede' sin citar la afirmacion sin respaldo")
            elif textos is not None and cid in textos and \
                    _normalizar(cita) not in _normalizar(textos[cid]):
                problemas.append(f"{cid}: la cita no aparece en la respuesta: {cita[:60]!r}")

        # Una primera pasada no es un dictamen: mientras falte el abogado, la
        # fila lo dice.
        if (f.get("revision_juridica") or "").strip() == "cumplida" and \
                "Galeano" not in (f.get("revisor") or ""):
            problemas.append(f"{cid}: revision_juridica=cumplida sin el abogado en 'revisor'")
    return problemas


def revisar_reevaluacion(filas: list[dict], previas: dict[str, dict],
                         textos: dict[str, str] | None = None) -> list[str]:
    return revisar_ronda("v1r", filas, previas, textos)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--crear", action="store_true", help="arma el CSV vacio")
    g.add_argument("--revisar", action="store_true", help="valida el CSV llenado")
    g.add_argument("--crear-reevaluacion", action="store_true",
                   help="arma la planilla de las 35 respuestas de v1 reevaluado")
    g.add_argument("--revisar-reevaluacion", action="store_true",
                   help="valida la planilla de v1 reevaluado")
    g.add_argument("--crear-ronda", choices=sorted(RONDAS),
                   help="arma la planilla de las 35 respuestas de esa ronda")
    g.add_argument("--revisar-ronda", choices=sorted(RONDAS),
                   help="valida la planilla de esa ronda")
    args = p.parse_args(argv)

    crear_r = args.crear_ronda or ("v1r" if args.crear_reevaluacion else None)
    revisar_r = args.revisar_ronda or ("v1r" if args.revisar_reevaluacion else None)
    if crear_r:
        salida = RONDAS[crear_r]["salida"]
        if salida.exists():
            raise SystemExit(f"{salida.name} ya existe: no se sobrescribe una revision en curso.")
        n = crear_ronda(crear_r)
        print(f"Escrito {salida} con {n} casos (prioridad 1 primero).")
        return 0
    if revisar_r:
        with SALIDA.open(encoding="utf-8", newline="") as f:
            previas = {fila["case_id"]: fila for fila in csv.DictReader(f)}
        with RONDAS[revisar_r]["salida"].open(encoding="utf-8", newline="") as f:
            filas = list(csv.DictReader(f))
        problemas = revisar_ronda(revisar_r, filas, previas, respuestas_ronda(revisar_r))
        if problemas:
            for s in problemas[:40]:
                print(f"  - {s}")
            raise SystemExit(f"{len(problemas)} problemas: la adjudicacion no esta cerrada.")
        print("Sin problemas: los 35 casos adjudicados y trazables.")
        return 0

    if args.crear:
        if SALIDA.exists():
            raise SystemExit(f"{SALIDA.name} ya existe: no se sobrescribe una revision en curso.")
        n = crear()
        print(f"Escrito {SALIDA} con {n} casos y las columnas vacias.")
        print(f"commit_matriz:  {commit_matriz()} (la version que se adjudica)")
        print(f"origen_prompt:  {ORIGEN_PROMPT}")
        return 0

    if not SALIDA.exists():
        raise SystemExit(f"No existe {SALIDA}. Crealo con --crear.")
    with SALIDA.open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    problemas = revisar(filas, textos=respuestas())
    print(resumen(filas))
    print()
    if problemas:
        for s in problemas[:40]:
            print(f"  - {s}")
        if len(problemas) > 40:
            print(f"  ... y {len(problemas) - 40} mas")
        raise SystemExit(f"{len(problemas)} problemas: la adjudicacion no esta cerrada.")
    print("Sin problemas: los 35 casos adjudicados y trazables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
