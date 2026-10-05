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
        ))
    return sorted(summaries, key=lambda s: s.label)


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
    ("bertscore_f1", "BERTScore"),
    ("token_f1", "F1 de tokens"),
)


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
        lines.append(
            f"Juez (compuesto 1-5): baseline {base.avg_judge_composite}, "
            f"fine-tuned {ft.avg_judge_composite}. "
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
        if base.n_judge_parse_failures or ft.n_judge_parse_failures:
            lines.append(
                f"Fallos de parseo del juez: baseline "
                f"{base.n_judge_parse_failures}/{base.n}, fine-tuned "
                f"{ft.n_judge_parse_failures}/{ft.n} (excluidos de los "
                f"promedios de judge_composite)."
            )
    if comparacion:
        nombres = dict(METRICAS_COMPARADAS)
        mejor = [nombres[k] for k, iv in comparacion.items() if iv.significativo and iv.valor > 0]
        peor = [nombres[k] for k, iv in comparacion.items() if iv.significativo and iv.valor < 0]
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
    if eval_set:
        textos = []
        for label, por_tipo in eval_set.items():
            for tipo, r in por_tipo.items():
                if r.get("aprobacion") is not None:
                    textos.append(f"{label}/{tipo}: {round(100 * r['aprobacion'])}% "
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
    "\"Sentencia T-N\"... El dataset de entrenamiento no cita ninguna norma (0 de "
    "1410 respuestas), asi que el 100 % del fine-tuned es lo esperable: el modelo "
    "aprendio a no citar, no a citar bien. Tampoco distingue una cita real de una "
    "inventada: al baseline le cuenta como falla citar el articulo 86 (correcto). "
    "Bajo presion el fine-tuned si inventa (eval set, caso 9102: \"articulo 81\").",
    "**F1, BLEU, ROUGE-L, BERTScore y similitud.** Miden parecido con la respuesta "
    "de referencia, no correccion juridica. El fine-tuned imita el estilo y el "
    "largo de las referencias del dataset (~46 palabras), y por eso sube en todas.",
    "**Juez compuesto.** Promedia cuatro criterios e incluye concision, que premia "
    "por diseno la respuesta corta. Leer los criterios por separado y el juez sin "
    "concision. El juez compara contra la referencia del dataset, que tiene el "
    "mismo estilo del fine-tuned.",
    "**Juez local (Qwen2.5-7B base).** Es el mismo modelo que escribio las "
    "respuestas del baseline: puede preferirlas por auto-preferencia. Por eso se "
    "contrasta con un juez de otra familia (Groq) en la comparacion cara a cara y "
    "en el eval set. El indicador self_preference_flagged compara contra difflib y "
    "no puede detectar auto-preferencia: no leerlo como evidencia de que no la hay.",
    "**Flip rate.** Mide cuantas veces cambia el veredicto al invertir el orden. "
    "0 % no significa \"sin sesgo\": si un modelo gana siempre en los dos ordenes, "
    "el flip rate tambien es 0. Leer el conteo de ganadores.",
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
) -> None:
    """ejemplos: [{id, query, baseline, fine_tuned, nota?}] -- respuestas
    textuales que se imprimen tal cual (la revision de M2 marco que no habia
    ni una respuesta textual en los resultados)."""
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
        "Similitud (%) | Juez (1-5) | Sin citas numeradas (%) | Palabras | "
        "Cortadas (%) | Latencia (s) |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in summaries:
        lines.append(
            f"| {s.label} | {s.n} | {s.exact_match_pct}% | {s.avg_token_f1} | "
            f"{s.avg_bleu} | {s.avg_rouge_l_f} | {s.avg_bertscore_f1} | "
            f"{s.avg_similarity_pct} | {s.avg_judge_composite} | "
            f"{s.citation_compliance_pct}% | {s.avg_palabras} | {s.pct_cortadas}% | "
            f"{s.avg_latency_s} |"
        )
    lines.append("")
    lines.append("## Juez por criterio")
    lines.append("")
    lines.append("| Criterio | " + " | ".join(s.label for s in summaries)
                 + " | Diferencia fine-tuned − baseline [IC 95 %] |")
    lines.append("|---|" + "---|" * len(summaries) + "---|")
    filas = (("Corrección jurídica", "avg_judge_correccion", "judge_correccion"),
             ("Prudencia", "avg_judge_prudencia", "judge_prudencia"),
             ("Claridad y utilidad", "avg_judge_claridad", "judge_claridad"),
             ("Concisión", "avg_judge_concision", "judge_concision"),
             ("**Sin concisión**", "avg_judge_sin_concision", "judge_sin_concision"),
             ("**Compuesto**", "avg_judge_composite", "judge_composite"))
    for nombre, attr, clave in filas:
        iv = (comparacion or {}).get(clave)
        dif = (iv.texto() + (" *" if iv.significativo else "")) if iv else "—"
        lines.append(f"| {nombre} | " + " | ".join(str(getattr(s, attr)) for s in summaries)
                     + f" | {dif} |")
    lines.append("")
    lines.append("\\* intervalo que no contiene el 0 (diferencia demostrable).")
    lines.append("")
    if ganadores:
        lines.append("## Comparación cara a cara")
        lines.append("")
        lines.append("Cada par se juzga dos veces, cambiando el orden. Se cuentan los veredictos.")
        lines.append("")
        lines.append("| Juez | Gana baseline | Gana fine-tuned | Empate |")
        lines.append("|---|---|---|---|")
        for juez, conteo in ganadores.items():
            lines.append(f"| {juez} | {conteo.get('baseline', 0)} | {conteo.get('fine_tuned', 0)} | "
                         f"{conteo.get('empate', 0)} |")
        lines.append("")
    if eval_set:
        lines.append("## Eval set propio, contra su criterio")
        lines.append("")
        lines.append("| Modelo | Tipo | N | Cumple | Parcial | No cumple | Aprobación [IC 95 %] | "
                     "Con errores jurídicos | Con citas numeradas |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for label, por_tipo in eval_set.items():
            for tipo, r in por_tipo.items():
                ic = r.get("aprobacion_ic95")
                apr = (f"{round(100 * r['aprobacion'])}% [{round(100 * ic[0])}, {round(100 * ic[1])}]"
                       if r.get("aprobacion") is not None else "—")
                err = (f"{round(100 * r['con_errores_juridicos'])}%"
                       if r.get("con_errores_juridicos") is not None else "—")
                lines.append(f"| {label} | {tipo} | {r['n']} | {r['cumple']} | {r['parcial']} | "
                             f"{r['no_cumple']} | {apr} | {err} | {r['con_citas_numeradas']} |")
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


def _una_linea(texto: str) -> str:
    return " ".join((texto or "").split())


def export_csv(path: Path, rows: list[EvalRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    extras = ("n_palabras", "judge_sin_concision")
    fieldnames = (list(asdict(rows[0]).keys()) + list(extras)) if rows else []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({**asdict(row), **{k: getattr(row, k) for k in extras}})


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
