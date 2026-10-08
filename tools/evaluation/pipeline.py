"""Orquestador: junta generacion + metricas clasicas + guardias (citas,
entidades, rutas) + juez en filas EvalRow, y construye el manifiesto de
reproducibilidad de la corrida.

Las filas se arman en dos tiempos: en Colab, apenas termina la generacion, con
todo lo que no necesita juez (build_eval_rows); despues, cuando Groq termina
(puede tomar mas de un dia por el cupo), se les agregan los puntajes del juez
(aplicar_juez, desde fase_groq.py).
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Optional, Sequence

from tools.evaluation import config, domain_metric, entity_metric, metrics_classic, rutas
from tools.evaluation.judge import JudgeScore
from tools.evaluation.scorecard import EvalRow

try:
    from tools.model_comparator.metrics import similarity_pct
except ImportError:  # pragma: no cover - model_comparator siempre deberia existir
    similarity_pct = None  # type: ignore


LIBRARIES_TO_TRACK = [
    "transformers", "peft", "torch", "sacrebleu", "rouge-score", "bert-score",
]


@dataclass
class RunManifest:
    git_commit: str
    random_seed: int
    val_fraction: float
    n_val: int
    base_model_id: str
    adapter_dir: str
    library_versions: dict[str, str] = field(default_factory=dict)
    hardware: str = ""
    timestamp: str = ""
    # Huellas de los insumos, con el mismo algoritmo que M3 (tools/rag/manifiesto).
    # Sin esto, dos corridas que dicen la misma fecha pueden haber medido sobre
    # un adaptador distinto y no hay como saberlo: el adaptador de Drive ya se
    # sobrescribio una vez (6 de octubre) y las corridas anteriores quedaron sin
    # forma de reproducirse. Opcionales: una corrida fuera de Colab no tiene el
    # adaptador a mano, y un campo en None dice "no se pudo registrar".
    hash_adaptador: Optional[str] = None
    hash_dataset: Optional[str] = None
    hash_eval_set: Optional[str] = None


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=config.PROJECT_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def _library_versions() -> dict[str, str]:
    versions = {}
    for lib in LIBRARIES_TO_TRACK:
        try:
            versions[lib] = importlib_metadata.version(lib)
        except importlib_metadata.PackageNotFoundError:
            versions[lib] = "not-installed"
    return versions


def _huellas(adapter_dir: str) -> dict:
    """Huellas del adaptador, el dataset y el eval set.

    Import perezoso de tools.rag.manifiesto: ese modulo importa _git_commit de
    aqui, asi que importarlo arriba cerraria el ciclo. Nunca lanza -- un
    manifiesto describe la corrida, no puede tumbarla.
    """
    try:
        from tools.rag.manifiesto import huella_archivo
    except Exception:                                   # pragma: no cover
        return {}
    from tools.evaluation import eval_set as _eval_set

    return {
        "hash_adaptador": huella_archivo(Path(adapter_dir) / "adapter_model.safetensors"),
        "hash_dataset": huella_archivo(config.LOCAL_DATASET_PATH),
        "hash_eval_set": huella_archivo(_eval_set.EVAL_SET_PATH),
    }


def build_manifest(
    n_val: int, hardware: str = "", adapter_dir: str = config.DRIVE_ADAPTER_DIR
) -> RunManifest:
    return RunManifest(
        git_commit=_git_commit(),
        random_seed=config.RANDOM_SEED,
        val_fraction=config.VAL_FRACTION,
        n_val=n_val,
        base_model_id=config.BASE_MODEL_ID,
        adapter_dir=adapter_dir,
        library_versions=_library_versions(),
        hardware=hardware,
        timestamp=datetime.now(timezone.utc).isoformat(),
        **_huellas(adapter_dir),
    )


def build_eval_rows(
    generations: Sequence,
    judge_scores: Optional[Sequence[JudgeScore]] = None,
    mapa: Optional["rutas.MapaContexto"] = None,
) -> list[EvalRow]:
    """Una fila por respuesta, en el mismo orden, con las metricas clasicas
    (salvo BERTScore, que se completa en batch con fill_bertscore) y las
    guardias sin juez: citas, entidades inventadas y, si se pasa mapa
    (rutas.construir_mapa(train)), rutas incorrectas y conceptos fuera de
    contexto. judge_scores (opcional): puntajes del juez en el mismo orden; sin
    ellos las columnas del juez quedan vacias hasta aplicar_juez.

    generations: GenerationResult o cualquier objeto con id, category, label,
    query, expected, generated, latency_s (y cortada, opcional)."""
    if judge_scores is not None and len(generations) != len(judge_scores):
        raise ValueError(
            "generations y judge_scores deben tener el mismo largo y orden"
        )

    rows: list[EvalRow] = []
    for k, gen in enumerate(generations):
        sim = similarity_pct(gen.expected, gen.generated) if similarity_pct else None
        rouge = metrics_classic.rouge_l(gen.expected, gen.generated)
        rev = rutas.revisar(gen.generated, gen.query, gen.category, mapa) if mapa is not None else None
        row = EvalRow(
            id=gen.id,
            category=gen.category,
            label=gen.label,
            query=gen.query,
            expected=gen.expected,
            generated=gen.generated,
            similarity_pct=sim,
            exact_match=metrics_classic.exact_match(gen.expected, gen.generated),
            token_f1=metrics_classic.token_f1(gen.expected, gen.generated),
            bleu=metrics_classic.bleu(gen.expected, gen.generated),
            rouge_l_f=rouge["fmeasure"],
            bertscore_f1=0.0,
            citation_count=domain_metric.citation_count(gen.generated),
            judge_correccion=None,
            judge_prudencia=None,
            judge_claridad=None,
            judge_concision=None,
            judge_composite=None,
            judge_parse_ok=False,
            latency_s=getattr(gen, "latency_s", 0.0),
            cortada=getattr(gen, "cortada", False),
            entidades_inventadas=", ".join(entity_metric.find_fabricated_entities(gen.generated)),
            rutas_incorrectas=", ".join(rev.rutas_incorrectas) if rev else "",
            fuera_de_contexto=", ".join(rev.fuera_de_contexto) if rev else "",
        )
        if judge_scores is not None:
            _poner_juez(row, judge_scores[k])
        rows.append(row)
    return rows


def _poner_juez(row: EvalRow, jscore: JudgeScore) -> None:
    row.judge_correccion = jscore.correccion_juridica
    row.judge_prudencia = jscore.prudencia
    row.judge_claridad = jscore.claridad_utilidad
    row.judge_concision = jscore.concision
    row.judge_composite = jscore.composite
    row.judge_parse_ok = jscore.parse_ok
    row.errores_juridicos = " | ".join(jscore.errores_juridicos) if jscore.parse_ok else ""
    row.juez_lista_errores = True


def aplicar_juez(rows: list[EvalRow], puntajes: dict[tuple[str, int], JudgeScore]) -> int:
    """Pone en cada fila el puntaje del juez de su (label, id). Devuelve
    cuantas filas quedaron sin puntaje valido. Modifica rows en el lugar."""
    faltan = 0
    for row in rows:
        js = puntajes.get((row.label, row.id))
        if js is None:
            faltan += 1
            continue
        _poner_juez(row, js)
        faltan += 0 if js.parse_ok else 1
    return faltan


def fill_bertscore(rows: list[EvalRow]) -> None:
    """Completa EvalRow.bertscore_f1 en batch (mucho mas eficiente que
    llamarlo fila por fila). Modifica rows en el lugar."""
    if not rows:
        return
    expected = [r.expected for r in rows]
    actual = [r.generated for r in rows]
    scores = metrics_classic.bertscore_f1_batch(expected, actual)
    for row, score in zip(rows, scores):
        row.bertscore_f1 = score
