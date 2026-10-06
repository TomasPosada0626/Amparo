"""Scorecard de M2: EvalRow junta generacion + metricas clasicas + juez +
metrica de dominio en una fila por registro, y estas funciones arman el
reporte comparativo baseline vs. fine-tuned. Mismo patron
dataclass -> summarize() -> build_narrative() -> export_markdown() que
tools/model_comparator/report.py, sin libreria de templating.
"""
from __future__ import annotations

import csv
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass
class EvalRow:
    id: int
    category: str
    label: str  # "baseline" | "fine_tuned"
    query: str
    expected: str
    generated: str
    similarity_pct: Optional[float]
    exact_match: float
    token_f1: float
    bleu: float
    rouge_l_f: float
    bertscore_f1: float
    citation_count: int
    judge_correccion: Optional[int]
    judge_prudencia: Optional[int]
    judge_claridad: Optional[int]
    judge_concision: Optional[int]
    judge_composite: Optional[float]
    judge_parse_ok: bool
    latency_s: float
    # Si la respuesta se corto por max_new_tokens (generation.GenerationResult).
    cortada: bool = False
    # Guardias sin juez (entity_metric.py, rutas.py), separadas por ", ".
    entidades_inventadas: str = ""
    rutas_incorrectas: str = ""
    fuera_de_contexto: str = ""
    # Errores juridicos que lista el juez Groq, separados por " | ".
    errores_juridicos: str = ""
    # El juez de esta fila pidio la lista de errores (rubrica de m3.5). En
    # corridas anteriores no la pedia: ahi "sin errores" no significa nada.
    juez_lista_errores: bool = False

    @property
    def n_palabras(self) -> int:
        return len((self.generated or "").split())

    @property
    def judge_sin_concision(self) -> Optional[float]:
        """Promedio del juez SIN el criterio de concision. El compuesto incluye
        concision, que premia por diseno la respuesta corta (la del fine-tuned)
        y en la corrida del 2026-10-02 escondia que los otros tres criterios
        bajaban."""
        vals = (self.judge_correccion, self.judge_prudencia, self.judge_claridad)
        return round(sum(vals) / 3, 4) if all(v is not None for v in vals) else None

    @property
    def marca_entidad(self) -> int:
        return int(bool(self.entidades_inventadas))

    @property
    def marca_ruta(self) -> int:
        return int(bool(self.rutas_incorrectas))

    @property
    def marca_contexto(self) -> int:
        return int(bool(self.fuera_de_contexto))

    @property
    def con_error_juridico(self) -> Optional[int]:
        """1 si el juez listo al menos un error juridico; None sin juez o con
        un juez que no pedia la lista."""
        if not (self.judge_parse_ok and self.juez_lista_errores):
            return None
        return int(bool(self.errores_juridicos))


@dataclass
class MetricSummary:
    label: str
    n: int
    exact_match_pct: float
    avg_token_f1: float
    avg_bleu: float
    avg_rouge_l_f: float
    avg_bertscore_f1: float
    avg_similarity_pct: Optional[float]
    avg_judge_composite: Optional[float]
    stdev_judge_composite: Optional[float]
    n_judge_parse_failures: int
    citation_compliance_pct: float
    avg_latency_s: float
    avg_judge_correccion: Optional[float] = None
    avg_judge_prudencia: Optional[float] = None
    avg_judge_claridad: Optional[float] = None
    avg_judge_concision: Optional[float] = None
    avg_judge_sin_concision: Optional[float] = None
    avg_palabras: float = 0.0
    pct_cortadas: float = 0.0
    pct_entidad_inventada: float = 0.0
    pct_ruta_incorrecta: float = 0.0
    pct_fuera_de_contexto: float = 0.0
    pct_con_error_juridico: Optional[float] = None


@dataclass
class CategorySummary:
    category: str
    label: str
    n: int
    avg_similarity_pct: Optional[float]
    avg_judge_composite: Optional[float]
    citation_compliance_pct: float


def _mean(values: list[float]) -> float:
    return round(statistics.fmean(values), 3) if values else 0.0


def summarize_by_label(rows: list[EvalRow]) -> list[MetricSummary]:
    by_label: dict[str, list[EvalRow]] = {}
    for row in rows:
        by_label.setdefault(row.label, []).append(row)

    summaries = []
    for label, label_rows in by_label.items():
        n = len(label_rows)
        similarities = [
            r.similarity_pct for r in label_rows if r.similarity_pct is not None
        ]
        judge_scores = [
            r.judge_composite for r in label_rows if r.judge_composite is not None
        ]
        n_compliant = sum(1 for r in label_rows if r.citation_count == 0)
        n_parse_failures = sum(1 for r in label_rows if not r.judge_parse_ok)

        summaries.append(MetricSummary(
            label=label,
            n=n,
            exact_match_pct=round(100.0 * _mean([r.exact_match for r in label_rows]), 1),
            avg_token_f1=_mean([r.token_f1 for r in label_rows]),
            avg_bleu=_mean([r.bleu for r in label_rows]),
            avg_rouge_l_f=_mean([r.rouge_l_f for r in label_rows]),
            avg_bertscore_f1=_mean([r.bertscore_f1 for r in label_rows]),
            avg_similarity_pct=_mean(similarities) if similarities else None,
            avg_judge_composite=_mean(judge_scores) if judge_scores else None,
            stdev_judge_composite=(
                round(statistics.pstdev(judge_scores), 3)
                if len(judge_scores) > 1 else None
            ),
            n_judge_parse_failures=n_parse_failures,
            citation_compliance_pct=round(100.0 * n_compliant / n, 1) if n else 0.0,
            avg_latency_s=_mean([r.latency_s for r in label_rows]),
            avg_judge_correccion=_mean_o_none([r.judge_correccion for r in label_rows]),
            avg_judge_prudencia=_mean_o_none([r.judge_prudencia for r in label_rows]),
            avg_judge_claridad=_mean_o_none([r.judge_claridad for r in label_rows]),
            avg_judge_concision=_mean_o_none([r.judge_concision for r in label_rows]),
            avg_judge_sin_concision=_mean_o_none([r.judge_sin_concision for r in label_rows]),
            avg_palabras=round(statistics.fmean([r.n_palabras for r in label_rows]), 1) if n else 0.0,
            pct_cortadas=round(100.0 * sum(1 for r in label_rows if r.cortada) / n, 1) if n else 0.0,
            pct_entidad_inventada=_pct([r.marca_entidad for r in label_rows]),
            pct_ruta_incorrecta=_pct([r.marca_ruta for r in label_rows]),
            pct_fuera_de_contexto=_pct([r.marca_contexto for r in label_rows]),
            pct_con_error_juridico=(_pct([r.con_error_juridico for r in label_rows
                                          if r.con_error_juridico is not None])
                                    if any(r.con_error_juridico is not None for r in label_rows) else None),
        ))
    return sorted(summaries, key=lambda s: s.label)


def _pct(valores: list) -> float:
    return round(100.0 * sum(valores) / len(valores), 1) if valores else 0.0


def _mean_o_none(values: list) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return _mean(vals) if vals else None


# Diferencias fine_tuned - baseline que se reportan con intervalo de confianza.
METRICAS_COMPARADAS = (
    ("judge_composite", "Juez compuesto (1-5)"),
    ("judge_sin_concision", "Juez sin concision (1-5)"),
    ("judge_correccion", "Juez: correccion juridica"),
    ("judge_prudencia", "Juez: prudencia"),
    ("judge_claridad", "Juez: claridad y utilidad"),
    ("judge_concision", "Juez: concision"),
    ("con_error_juridico", "Juez: respuestas con error juridico (proporcion)"),
    ("marca_entidad", "Guardia: entidad inventada (proporcion)"),
    ("marca_ruta", "Guardia: ruta incorrecta (proporcion)"),
    ("marca_contexto", "Guardia: concepto fuera de contexto (proporcion)"),
    ("bertscore_f1", "BERTScore"),
    ("token_f1", "F1 de tokens"),
)

# En estas, que el fine-tuned SUBA es empeorar.
MENOR_ES_MEJOR = frozenset({"con_error_juridico", "marca_entidad", "marca_ruta", "marca_contexto"})


def comparar(rows: list[EvalRow]) -> dict[str, "Intervalo"]:
    """Diferencia fine_tuned - baseline por metrica, pareada por id, con IC 95 %
    por bootstrap (estadistica.diferencia_pareada). Una diferencia cuyo
    intervalo contiene el 0 no es una mejora ni un empeoramiento demostrado."""
    from tools.evaluation.estadistica import diferencia_pareada

    base = {r.id: r for r in rows if r.label == "baseline"}
    ft = {r.id: r for r in rows if r.label == "fine_tuned"}
    ids = [i for i in base if i in ft]
    salida = {}
    for clave, _ in METRICAS_COMPARADAS:
        iv = diferencia_pareada([getattr(base[i], clave) for i in ids], [getattr(ft[i], clave) for i in ids])
        if iv is not None:
            salida[clave] = iv
    return salida


def summarize_by_category(rows: list[EvalRow], label: str) -> list[CategorySummary]:
    by_category: dict[str, list[EvalRow]] = {}
    for row in rows:
        if row.label != label:
            continue
        by_category.setdefault(row.category, []).append(row)

    summaries = []
    for category, cat_rows in sorted(by_category.items()):
        n = len(cat_rows)
        similarities = [
            r.similarity_pct for r in cat_rows if r.similarity_pct is not None
        ]
        judge_scores = [
            r.judge_composite for r in cat_rows if r.judge_composite is not None
        ]
        n_compliant = sum(1 for r in cat_rows if r.citation_count == 0)
        summaries.append(CategorySummary(
            category=category,
            label=label,
            n=n,
            avg_similarity_pct=_mean(similarities) if similarities else None,
            avg_judge_composite=_mean(judge_scores) if judge_scores else None,
            citation_compliance_pct=round(100.0 * n_compliant / n, 1) if n else 0.0,
        ))
    return summaries


def build_narrative(
    summaries: list[MetricSummary],
    bias_summary: dict,
    n_val: int,
    comparacion: Optional[dict] = None,
    ganadores: Optional[dict] = None,
    eval_set: Optional[dict] = None,
    cara_a_cara: Optional[dict] = None,
    rutas: Optional[dict] = None,
) -> str:
    """Conclusion en texto, derivada de los datos: dice que diferencias son
    significativas y cuales no, en vez de solo listar promedios."""
    lines = [
        f"Se evaluaron {n_val} ejemplos de validacion (mismo split de M1, "
        f"seed=42, val_fraction=0.15)."
    ]
    by_label = {s.label: s for s in summaries}
    if "baseline" in by_label and "fine_tuned" in by_label:
        base, ft = by_label["baseline"], by_label["fine_tuned"]
        hay_juez = base.avg_judge_composite is not None or ft.avg_judge_composite is not None
        juez = (f"Juez (compuesto 1-5): baseline {base.avg_judge_composite}, "
                f"fine-tuned {ft.avg_judge_composite}. " if hay_juez else "Juez: pendiente. ")
        lines.append(
            juez +
            f"Respuestas sin citas numeradas: baseline "
            f"{base.citation_compliance_pct}%, fine-tuned "
            f"{ft.citation_compliance_pct}%. Longitud media: "
            f"{base.avg_palabras} vs {ft.avg_palabras} palabras."
        )
        if base.pct_cortadas or ft.pct_cortadas:
            lines.append(
                f"Respuestas cortadas por max_new_tokens: baseline {base.pct_cortadas}%, "
                f"fine-tuned {ft.pct_cortadas}%. Una respuesta cortada se califica incompleta: "
                "si el porcentaje es alto, la comparacion esta sesgada contra ese modelo."
            )
        if hay_juez and (base.n_judge_parse_failures or ft.n_judge_parse_failures):
            lines.append(
                f"Fallos de parseo del juez: baseline "
                f"{base.n_judge_parse_failures}/{base.n}, fine-tuned "
                f"{ft.n_judge_parse_failures}/{ft.n} (excluidos de los "
                f"promedios de judge_composite)."
            )
    if comparacion:
        nombres = dict(METRICAS_COMPARADAS)

        def sentido(k, iv):   # +1 mejora, -1 empeora
            return (-1 if k in MENOR_ES_MEJOR else 1) * (1 if iv.valor > 0 else -1)

        mejor = [nombres[k] for k, iv in comparacion.items() if iv.significativo and sentido(k, iv) > 0]
        peor = [nombres[k] for k, iv in comparacion.items() if iv.significativo and sentido(k, iv) < 0]
        empate = [nombres[k] for k, iv in comparacion.items() if not iv.significativo]
        partes = []
        if mejor:
            partes.append("mejora con significancia en: " + ", ".join(mejor))
        if peor:
            partes.append("EMPEORA con significancia en: " + ", ".join(peor))
        if empate:
            partes.append("sin diferencia demostrable en: " + ", ".join(empate))
        lines.append("Fine-tuned frente a baseline (IC 95 % por bootstrap pareado) -- "
                     + "; ".join(partes) + ".")
    if ganadores:
        textos = []
        for juez, conteo in ganadores.items():
            total = sum(conteo.values()) or 1
            textos.append(f"{juez}: baseline {conteo.get('baseline', 0)}, fine-tuned "
                          f"{conteo.get('fine_tuned', 0)}, empate {conteo.get('empate', 0)} "
                          f"(de {total} veredictos)")
        lines.append("Comparacion cara a cara (cada par en los dos ordenes) -- " + "; ".join(textos) + ".")
    if cara_a_cara:
        c, t = cara_a_cara["consistente"], cara_a_cara["tasa_victoria"]
        texto = (f"Cara a cara ({cara_a_cara['juez']}, {cara_a_cara['n_pares']} pares, cada uno en los dos "
                 f"ordenes; gana solo quien gana en ambos): fine-tuned {c['fine_tuned']}, baseline "
                 f"{c['baseline']}, empate {c['empate']}, inconsistente {c['inconsistente']}, sin veredicto "
                 f"{c['sin_veredicto']}.")
        if t.get("tasa") is not None:
            texto += (f" El fine-tuned gana el {round(100 * t['tasa'])} % de los pares decididos "
                      f"[IC 95 % {round(100 * t['ic95'][0])}-{round(100 * t['ic95'][1])}]")
            texto += (": diferencia demostrable." if (t["ic95"][0] > 0.5 or t["ic95"][1] < 0.5)
                      else ": no se distingue de un empate.")
        lines.append(texto)
    if rutas:
        partes = [f"{r['etiqueta']} {r['pct_ruta_incorrecta']} % ruta incorrecta, "
                  f"{r['pct_fuera_de_contexto']} % fuera de contexto, {r['pct_entidad_inventada']} % "
                  "entidad inventada" for r in rutas["reportes"]]
        lines.append("Guardia de rutas y entidades (sin juez; marcas para revisar, no errores confirmados) -- "
                     + "; ".join(partes) + ". Las referencias de validacion son la calibracion: lo que la "
                     "guardia marca ahi es ruido.")
    if eval_set:
        textos = []
        for label, por_tipo in eval_set.items():
            for tipo, r in por_tipo.items():
                if r.get("aprobacion") is not None:
                    textos.append(f"{label}/{tipo}: cumple {round(100 * r['aprobacion'])}% "
                                  f"(n={r['n']}, con errores juridicos {round(100 * (r['con_errores_juridicos'] or 0))}%)")
        if textos:
            lines.append("Eval set contra su criterio -- " + "; ".join(textos) + ".")
    if bias_summary:
        lines.append(
            "Sesgos: " + "; ".join(f"{k}={v}" for k, v in bias_summary.items())
        )
    return "\n\n".join(lines)


# Lo que cada metrica mide y lo que NO. Va en todo scorecard: la revision de M2
# marco que el "100 % sin citas" se presentaba como logro sin decir que es
# trivial, y que las metricas lexicas se leian como calidad juridica.
NOTAS_METRICAS = (
    "**Sin citas numeradas.** Cuenta respuestas sin \"Ley N\", \"Articulo N\", "
    "\"Sentencia T-N\"... El dataset de entrenamiento no cita ninguna norma, asi "
    "que el 100 % del fine-tuned es lo esperable: el modelo aprendio a no citar, "
    "no a citar bien. Tampoco distingue una cita real de una inventada: al "
    "baseline le cuenta como falla citar el articulo 86 (correcto).",
    "**F1, BLEU, ROUGE-L, BERTScore y similitud.** Miden parecido con la respuesta "
    "de referencia, no correccion juridica. El fine-tuned imita el estilo y el "
    "largo de las referencias del dataset (~46 palabras), y por eso sube en todas.",
    "**Juez (Groq, openai/gpt-oss-120b).** De otra familia que el Qwen2.5 evaluado y "
    "no escribio ninguna respuesta: no tiene auto-preferencia. El juez local Qwen se "
    "quito (preferia al baseline, el mismo modelo, en 50-60 de 60 veredictos). "
    "temperature=0 y seed fija. El compuesto 1-5 incluye concision, que premia por "
    "diseno la respuesta corta: leer los criterios por separado y el juez sin "
    "concision. Compara contra la referencia del dataset, que tiene el estilo del "
    "fine-tuned.",
    "**Errores juridicos (juez).** Proporcion de respuestas en las que el juez lista "
    "al menos una afirmacion falsa o una entidad equivocada o inexistente para el "
    "caso. Es el control principal de la correccion juridica; el juez tambien se "
    "equivoca, por eso se revisa a mano una muestra.",
    "**Guardia de rutas y entidades (sin juez).** Entidad inventada: nombre con forma "
    "de institucion que no existe (lista blanca). Ruta incorrecta: entidad real para "
    "un tramite que no le toca (reglas escritas a mano, validadas contra las 1536 "
    "referencias del dataset, que no marcan ninguna). Fuera de contexto: concepto que "
    "las referencias de train nunca usan para ese tema; tiene ruido, y su tasa base es "
    "la de las referencias de validacion. Son marcas para revisar, no errores "
    "confirmados; detectan solo lo que reconocen, no reemplazan al juez.",
    "**Cara a cara.** Cada par se juzga en los dos ordenes y gana un modelo solo si "
    "gana en ambos: asi el sesgo de posicion no le suma a nadie. El flip rate (pares "
    "cuyo ganador cambia con el orden) mide cuanto sesgo de posicion tiene el juez.",
    "**Longitud.** Los prompts del juez piden no premiar la extension, y la correlacion "
    "entre puntaje y largo se reporta en Sesgos.",
)


def export_markdown(
    path: Path,
    summaries: list[MetricSummary],
    category_summaries: dict[str, list[CategorySummary]],
    narrative: str,
    bias_summary: dict,
    manifest: dict,
    comparacion: Optional[dict] = None,
    ganadores: Optional[dict] = None,
    eval_set: Optional[dict] = None,
    ejemplos: Optional[list[dict]] = None,
    juez_externo: Optional[tuple[str, list[MetricSummary], dict]] = None,
    cara_a_cara: Optional[dict] = None,
    rutas: Optional[dict] = None,
    abstencion: Optional[dict] = None,
    titulo_juez: str = "Juez por criterio",
) -> None:
    """ejemplos: [{id, query, baseline, fine_tuned, nota?}] -- respuestas
    textuales que se imprimen tal cual (la revision de M2 marco que no habia
    ni una respuesta textual en los resultados).

    juez_externo: (nombre, summaries, comparacion) del mismo analisis con un
    juez de otra familia (Groq) sobre la validacion, si se corrio (corridas
    anteriores a m3.5, con juez local).

    cara_a_cara, rutas, abstencion: ver fase_groq.informe()."""
    lines: list[str] = []
    lines.append("# Scorecard M2 — Evaluación del Modelo")
    lines.append("")
    lines.append(
        f"Generado: {manifest.get('timestamp', '')} · commit "
        f"`{manifest.get('git_commit', '')}` · seed "
        f"{manifest.get('random_seed', '')} · hardware: "
        f"{manifest.get('hardware', '')}"
    )
    lines.append("")
    lines.append("## Conclusión")
    lines.append("")
    lines.append(narrative)
    lines.append("")
    lines.append("## Resumen por modelo")
    lines.append("")
    lines.append(
        "| Modelo | N | Exact Match | F1 | BLEU | ROUGE-L | BERTScore | "
        "Similitud (%) | Juez (1-5) | Con error jurídico (%) | Sin citas numeradas (%) | "
        "Entidad inventada (%) | Ruta incorrecta (%) | Fuera de contexto (%) | Palabras | "
        "Cortadas (%) | Latencia (s) |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in summaries:
        err = f"{s.pct_con_error_juridico}%" if s.pct_con_error_juridico is not None else "—"
        lines.append(
            f"| {s.label} | {s.n} | {s.exact_match_pct}% | {s.avg_token_f1} | "
            f"{s.avg_bleu} | {s.avg_rouge_l_f} | {s.avg_bertscore_f1} | "
            f"{s.avg_similarity_pct} | {_o_raya(s.avg_judge_composite)} | {err} | "
            f"{s.citation_compliance_pct}% | {s.pct_entidad_inventada}% | {s.pct_ruta_incorrecta}% | "
            f"{s.pct_fuera_de_contexto}% | {s.avg_palabras} | {s.pct_cortadas}% | "
            f"{s.avg_latency_s} |"
        )
    lines.append("")
    jueces = [(titulo_juez, summaries, comparacion)] if any(x.avg_judge_composite for x in summaries) else []
    if juez_externo:
        jueces.append((f"Juez por criterio — {juez_externo[0]}", juez_externo[1], juez_externo[2]))
    for titulo, sums, comp in jueces:
        lines.extend(_tabla_criterios(titulo, sums, comp))
    if comparacion:
        otras = [(k, n) for k, n in METRICAS_COMPARADAS
                 if k in comparacion and k not in {c for _, _, c in _FILAS_JUEZ}]
        if otras:
            lines.append("## Otras diferencias fine-tuned − baseline")
            lines.append("")
            lines.append("Pareadas por pregunta, IC 95 % por bootstrap. En las proporciones "
                         "(errores, marcas de la guardia) bajar es mejorar.")
            lines.append("")
            lines.append("| Métrica | Diferencia [IC 95 %] |")
            lines.append("|---|---|")
            for k, nombre in otras:
                iv = comparacion[k]
                lines.append(f"| {nombre} | {iv.texto()}{' *' if iv.significativo else ''} |")
            lines.append("")
    if cara_a_cara:
        c, t = cara_a_cara["consistente"], cara_a_cara["tasa_victoria"]
        lines.append("## Comparación cara a cara (sesgo de posición neutralizado)")
        lines.append("")
        lines.append(f"Juez: {cara_a_cara['juez']}. {cara_a_cara['n_pares']} pares, cada uno juzgado en los "
                     "dos órdenes. Gana un modelo solo si gana en ambos; si el ganador cambia con el orden, "
                     "el par es inconsistente y no cuenta para nadie.")
        lines.append("")
        lines.append("| Gana fine-tuned | Gana baseline | Empate | Inconsistente | Sin veredicto | "
                     "Fine-tuned gana (de los decididos) [IC 95 %] | Flip rate |")
        lines.append("|---|---|---|---|---|---|---|")
        tasa = (f"{round(100 * t['tasa'])}% [{round(100 * t['ic95'][0])}, {round(100 * t['ic95'][1])}]"
                if t.get("tasa") is not None else "—")
        lines.append(f"| {c['fine_tuned']} | {c['baseline']} | {c['empate']} | {c['inconsistente']} | "
                     f"{c['sin_veredicto']} | {tasa} | {cara_a_cara.get('flip_rate_pct', '—')}% |")
        lines.append("")
    if rutas:
        lines.extend(_seccion_rutas(rutas))
    if abstencion:
        lines.extend(_seccion_abstencion(abstencion))
    if ganadores:
        lines.append("## Comparación cara a cara")
        lines.append("")
        lines.append("Cada par se juzga dos veces, cambiando el orden. Se cuentan los veredictos.")
        lines.append("")
        lines.append("| Juez | Gana baseline | Gana fine-tuned | Empate | Sin veredicto |")
        lines.append("|---|---|---|---|---|")
        for juez, conteo in ganadores.items():
            lines.append(f"| {juez} | {conteo.get('baseline', 0)} | {conteo.get('fine_tuned', 0)} | "
                         f"{conteo.get('empate', 0)} | {conteo.get('sin_veredicto', 0)} |")
        lines.append("")
    if eval_set:
        lines.append("## Eval set propio, contra su criterio")
        lines.append("")
        lines.append("Aprobación = proporción de casos que cumplen el criterio completo (IC de Wilson). "
                     "Puntaje medio: cumple 1, parcial 0.5. Los casos sin veredicto del juez no entran.")
        lines.append("")
        lines.append("| Modelo | Tipo | N | Cumple | Parcial | No cumple | Sin veredicto | "
                     "Aprobación [IC 95 %] | Puntaje medio | Con errores jurídicos | Con citas numeradas |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for label, por_tipo in eval_set.items():
            for tipo, r in por_tipo.items():
                ic = r.get("aprobacion_ic95")
                apr = (f"{round(100 * r['aprobacion'])}% [{round(100 * ic[0])}, {round(100 * ic[1])}]"
                       if r.get("aprobacion") is not None else "—")
                err = (f"{round(100 * r['con_errores_juridicos'])}%"
                       if r.get("con_errores_juridicos") is not None else "—")
                lines.append(f"| {label} | {tipo} | {r['n']} | {r['cumple']} | {r['parcial']} | "
                             f"{r['no_cumple']} | {r.get('sin_veredicto', 0)} | {apr} | "
                             f"{r.get('puntaje_medio', '—')} | {err} | {r['con_citas_numeradas']} |")
        lines.append("")
    lines.append("## Resumen por categoría")
    lines.append("")
    for label, cats in category_summaries.items():
        lines.append(f"### {label}")
        lines.append("")
        lines.append(
            "| Categoría | N | Similitud (%) | Juez (1-5) | "
            "Sin citas numeradas (%) |"
        )
        lines.append("|---|---|---|---|---|")
        for c in cats:
            lines.append(
                f"| {c.category} | {c.n} | {c.avg_similarity_pct} | "
                f"{c.avg_judge_composite} | {c.citation_compliance_pct}% |"
            )
        lines.append("")
    lines.append("## Sesgos")
    lines.append("")
    for k, v in bias_summary.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## Qué mide cada métrica (y qué no)")
    lines.append("")
    for nota in NOTAS_METRICAS:
        lines.append(f"- {nota}")
    lines.append("")
    if ejemplos:
        lines.append("## Respuestas textuales")
        lines.append("")
        for e in ejemplos:
            lines.append(f"### id {e['id']}" + (f" — {e['nota']}" if e.get("nota") else ""))
            lines.append("")
            lines.append(f"**Pregunta:** {e['query']}")
            lines.append("")
            lines.append(f"**Baseline:** {_una_linea(e['baseline'])}")
            lines.append("")
            lines.append(f"**Fine-tuned:** {_una_linea(e['fine_tuned'])}")
            lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


_FILAS_JUEZ = (("Corrección jurídica", "avg_judge_correccion", "judge_correccion"),
               ("Prudencia", "avg_judge_prudencia", "judge_prudencia"),
               ("Claridad y utilidad", "avg_judge_claridad", "judge_claridad"),
               ("Concisión", "avg_judge_concision", "judge_concision"),
               ("**Sin concisión**", "avg_judge_sin_concision", "judge_sin_concision"),
               ("**Compuesto**", "avg_judge_composite", "judge_composite"))


def _seccion_rutas(rutas: dict) -> list[str]:
    lines = ["## Guardia de rutas y entidades (sin juez)", "",
             "Marcas para revisar, no errores confirmados. La fila de referencias de validación es la "
             "calibración: esas respuestas son correctas por construcción, así que lo que la guardia marca "
             "ahí es ruido.", "",
             "| Respuestas | N | Entidad inventada (%) | Ruta incorrecta (%) | Fuera de contexto (%) | "
             "Reglas violadas | Conceptos fuera de contexto |",
             "|---|---|---|---|---|---|---|"]
    for r in rutas["reportes"]:
        reglas = ", ".join(f"{k} ({v})" for k, v in r["por_regla"].items()) or "—"
        conceptos = ", ".join(f"{k} ({v})" for k, v in list(r["por_concepto"].items())[:8]) or "—"
        lines.append(f"| {r['etiqueta']} | {r['n']} | {r['pct_entidad_inventada']} | {r['pct_ruta_incorrecta']} | "
                     f"{r['pct_fuera_de_contexto']} | {reglas} | {conceptos} |")
    lines.append("")
    if rutas.get("marcadas"):
        lines.append("### Respuestas del fine-tuned marcadas (para revisión a mano)")
        lines.append("")
        lines.append("| id | Categoría | Marcas | Errores según el juez | Respuesta |")
        lines.append("|---|---|---|---|---|")
        for m in rutas["marcadas"]:
            lines.append(f"| {m['id']} | {m['category']} | {_celda(m['marcas'])} | "
                         f"{_celda(m.get('errores_juez')) or '—'} | {_celda(m['respuesta'])} |")
        lines.append("")
    return lines


def _seccion_abstencion(ab: dict) -> list[str]:
    lines = ["## Abstención por categoría", "",
             "Validación: las 6 categorías de abstención (pocos casos por categoría: leer como señal, no "
             "como medición). Eval set: los adversariales contra su criterio, por tipo.", ""]
    if ab.get("validacion"):
        lines.append("| Categoría | Modelo | N | Juez sin concisión | Prudencia | Con error jurídico | "
                     "Marcas de la guardia |")
        lines.append("|---|---|---|---|---|---|---|")
        for f in ab["validacion"]:
            lines.append(f"| {f['categoria']} | {f['label']} | {f['n']} | {_o_raya(f['juez_sin_concision'])} | "
                         f"{_o_raya(f['prudencia'])} | {_o_raya(f['con_error_juridico'])} | {f['marcadas']} |")
        lines.append("")
    if ab.get("eval_set"):
        lines.append("| Tipo de adversarial | Modelo | N | Cumple | Parcial | No cumple | Sin veredicto |")
        lines.append("|---|---|---|---|---|---|---|")
        for f in ab["eval_set"]:
            lines.append(f"| {f['categoria']} | {f['label']} | {f['n']} | {f['cumple']} | {f['parcial']} | "
                         f"{f['no_cumple']} | {f['sin_veredicto']} |")
        lines.append("")
    return lines


def _o_raya(v) -> str:
    return "—" if v is None else str(v)


def resumen_abstencion(rows: list[EvalRow]) -> list[dict]:
    """Filas de validacion de las categorias de abstencion, por categoria y modelo."""
    from tools.evaluation.rutas import CATEGORIAS_ABSTENCION

    grupos: dict[tuple[str, str], list[EvalRow]] = {}
    for r in rows:
        if r.category in CATEGORIAS_ABSTENCION:
            grupos.setdefault((r.category, r.label), []).append(r)
    salida = []
    for (cat, label), rs in sorted(grupos.items()):
        errores = [r.con_error_juridico for r in rs if r.con_error_juridico is not None]
        salida.append({
            "categoria": cat, "label": label, "n": len(rs),
            "juez_sin_concision": _mean_o_none([r.judge_sin_concision for r in rs]),
            "prudencia": _mean_o_none([r.judge_prudencia for r in rs]),
            "con_error_juridico": f"{sum(errores)}/{len(errores)}" if errores else None,
            "marcadas": sum(1 for r in rs if r.marca_entidad or r.marca_ruta or r.marca_contexto),
        })
    return salida


def _tabla_criterios(titulo: str, summaries: list[MetricSummary], comparacion: Optional[dict]) -> list[str]:
    lines = [f"## {titulo}", ""]
    lines.append("| Criterio | " + " | ".join(s.label for s in summaries)
                 + " | Diferencia fine-tuned − baseline [IC 95 %] |")
    lines.append("|---|" + "---|" * len(summaries) + "---|")
    for nombre, attr, clave in _FILAS_JUEZ:
        iv = (comparacion or {}).get(clave)
        dif = (iv.texto() + (" *" if iv.significativo else "")) if iv else "—"
        lines.append(f"| {nombre} | " + " | ".join(str(getattr(s, attr)) for s in summaries)
                     + f" | {dif} |")
    lines += ["", "\\* intervalo que no contiene el 0 (diferencia demostrable).", ""]
    return lines


def _una_linea(texto: str) -> str:
    return " ".join((texto or "").split())


def _celda(texto: Optional[str]) -> str:
    """Texto para una celda de tabla markdown: una linea y sin "|" (los errores
    del juez vienen separados por " | " y rompian la tabla)."""
    return _una_linea(texto or "").replace("|", "/")


def export_csv(path: Path, rows: list[EvalRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    extras = ("n_palabras", "judge_sin_concision")   # propiedades calculadas, utiles en el CSV
    fieldnames = (list(asdict(rows[0]).keys()) + list(extras)) if rows else []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({**asdict(row), **{k: getattr(row, k) for k in extras}})


def csv_tiene_columna(path: Path, columna: str) -> bool:
    with open(path, encoding="utf-8") as f:
        return columna in next(csv.reader(f), [])


def load_csv(path: Path) -> list[EvalRow]:
    """Lee un metricas_por_registro.csv (de esta version o de una anterior, sin
    la columna `cortada`) para volver a analizar una corrida sin GPU."""
    def num(v, tipo=float):
        return None if v in ("", "None", None) else tipo(float(v))

    rows = []
    with open(path, encoding="utf-8") as f:
        for d in csv.DictReader(f):
            rows.append(EvalRow(
                id=int(d["id"]), category=d["category"], label=d["label"], query=d["query"],
                expected=d["expected"], generated=d["generated"],
                similarity_pct=num(d["similarity_pct"]), exact_match=float(d["exact_match"]),
                token_f1=float(d["token_f1"]), bleu=float(d["bleu"]), rouge_l_f=float(d["rouge_l_f"]),
                bertscore_f1=float(d["bertscore_f1"]), citation_count=int(float(d["citation_count"])),
                judge_correccion=num(d["judge_correccion"], int), judge_prudencia=num(d["judge_prudencia"], int),
                judge_claridad=num(d["judge_claridad"], int), judge_concision=num(d["judge_concision"], int),
                judge_composite=num(d["judge_composite"]), judge_parse_ok=d["judge_parse_ok"] == "True",
                latency_s=float(d["latency_s"]), cortada=d.get("cortada") == "True",
                entidades_inventadas=d.get("entidades_inventadas") or "",
                rutas_incorrectas=d.get("rutas_incorrectas") or "",
                fuera_de_contexto=d.get("fuera_de_contexto") or "",
                errores_juridicos=d.get("errores_juridicos") or "",
                juez_lista_errores=d.get("juez_lista_errores") == "True",
            ))
    return rows


_FIN_DE_FRASE = (".", "!", "?", ")", '"', "»", ":")


def parece_cortada(texto: str) -> bool:
    """Heuristica para corridas anteriores a la columna `cortada`: la respuesta
    no termina en un signo de fin de frase. En las corridas nuevas se usa el
    conteo real de tokens (generation.GenerationResult.cortada)."""
    return not (texto or "").rstrip().endswith(_FIN_DE_FRASE)


def elegir_ejemplos(
    eval_records: list[dict],
    baseline: list,
    fine_tuned: list,
    n_gold: int = 4,
    semilla: int = 42,
) -> list[dict]:
    """Respuestas textuales para el scorecard: TODOS los adversariales y n_gold
    gold elegidos al azar con semilla fija. Regla fija a proposito: elegir a
    mano los ejemplos es la forma mas facil de mostrar solo lo que conviene."""
    import random

    b = {g.id: g.generated for g in baseline}
    f = {g.id: g.generated for g in fine_tuned}
    gold = [r for r in eval_records if r["tipo"] == "gold" and r["id"] in b and r["id"] in f]
    adv = [r for r in eval_records if r["tipo"] == "adversarial" and r["id"] in b and r["id"] in f]
    elegidos = adv + random.Random(semilla).sample(gold, min(n_gold, len(gold)))
    return [{"id": r["id"], "query": r["messages"][1]["content"], "baseline": b[r["id"]],
             "fine_tuned": f[r["id"]], "nota": f"{r['tipo']} -- criterio: {r['criterio']}"}
            for r in elegidos]
