"""Seguimiento de corridas en Weights & Biases (M3 · S10, extra de W&B).

Los numeros de RAGAS, la tasa de escape y la latencia se pierden si solo se
miran en pantalla. Cada sistema del RAG (una pasada, una pasada con el prompt de
DSPy, las busquedas A/B/C de S08) se registra como una corrida de W&B en el mismo
proyecto, con:

  - sus promedios (las cuatro metricas RAGAS, tasas de escape, latencia, tokens
    del juez) como escalares comparables entre corridas;
  - una tabla por caso (pregunta, respuesta, metricas), para ver DONDE falla;
  - la traza paso a paso, si el registro la trae (la traian las rutas agenticas,
    retiradas el 2026-10-08 por C11; se conserva para leer corridas viejas).

Y una corrida "comparativa" con los sistemas lado a lado.

Credenciales: la API key NUNCA va en el codigo ni en el repo. Se lee de la
variable de entorno WANDB_API_KEY (en Colab, de los secretos del notebook). Si
no hay key, se corre en modo offline: las corridas se guardan en disco y se
suben despues con `wandb sync`, sin romper la evaluacion.

La entidad (cuenta o equipo) y el proyecto se pasan como parametros desde el
notebook, no quedan fijos aca: el mismo codigo sirve para cualquier miembro.

El modulo `wandb` se inyecta (parametro `wb`), asi que el registro se prueba
sin red (tests/evaluation/test_tracking.py).
"""
from __future__ import annotations

import os
from typing import Optional, Sequence

PROYECTO_POR_DEFECTO = "amparo-rag"
MAX_TEXTO_TABLA = 1500  # recorte de textos largos en las tablas de W&B


def modo_de_ejecucion(api_key: Optional[str] = None) -> str:
    """'online' si hay API key, 'offline' si no. Deja WANDB_MODE seteado.

    No imprime ni devuelve la key: solo decide el modo."""
    key = (api_key if api_key is not None else os.environ.get("WANDB_API_KEY", "")).strip()
    if key:
        os.environ["WANDB_API_KEY"] = key
        os.environ.pop("WANDB_MODE", None)
        return "online"
    os.environ["WANDB_MODE"] = "offline"
    return "offline"


def _recortar(texto, n: int = MAX_TEXTO_TABLA) -> str:
    texto = "" if texto is None else str(texto)
    return texto if len(texto) <= n else texto[:n] + " [...]"


def registrar_ruta(
    wb,
    *,
    sistema: str,
    resumen_ragas: dict,
    escape: dict,
    latencia_s: Optional[float],
    filas_ragas: Sequence[dict],
    records: Sequence[dict],
    config: dict,
    entity: Optional[str] = None,
    project: str = PROYECTO_POR_DEFECTO,
    grupo: Optional[str] = None,
) -> Optional[str]:
    """Registra UNA ruta como una corrida. Devuelve la URL (None en offline).

    resumen_ragas: ragas_metrics.resumen(...)[sistema]
    escape: ragas_metrics.tasas_de_escape(...)[sistema]
    filas_ragas: filas de ragas_metrics.evaluar_corrida de esta ruta
    records: registros de pipeline.to_eval_record de esta ruta (con la traza)
    """
    run = wb.init(entity=entity, project=project, name=sistema, group=grupo,
                  job_type="evaluacion-rag", config={**config, "sistema": sistema}, reinit=True)

    escalares = {k: v for k, v in (resumen_ragas or {}).items() if isinstance(v, (int, float)) and v is not None}
    escalares.update({k: v for k, v in (escape or {}).items() if isinstance(v, (int, float)) and v is not None})
    if latencia_s is not None:
        escalares["latencia_s_por_consulta"] = latencia_s
    wb.log(escalares)

    metricas_por_id = {f["registro_id"]: f for f in filas_ragas}
    cols = ["id", "tipo", "categoria", "pregunta", "respuesta", "escape", "n_contextos",
            "faithfulness", "context_precision", "context_recall", "answer_relevancy"]
    tabla = wb.Table(columns=cols)
    for r in records:
        m = metricas_por_id.get(r["id"], {})
        tabla.add_data(r["id"], r.get("tipo"), r.get("category"), _recortar(r.get("question")),
                       _recortar(r.get("answer")), m.get("escape"), len(r.get("contexts") or []),
                       m.get("faithfulness"), m.get("context_precision"), m.get("context_recall"),
                       m.get("answer_relevancy"))
    datos = {"casos": tabla}

    filas_traza = [(r["id"], p) for r in records for p in (r.get("traza") or [])]
    if filas_traza:
        traza = wb.Table(columns=["id", "paso", "pensamiento", "accion", "argumento", "observacion"])
        for rid, p in filas_traza:
            traza.add_data(rid, p.get("paso"), _recortar(p.get("pensamiento"), 500), p.get("accion"),
                           _recortar(p.get("argumento"), 500), _recortar(p.get("observacion"), 800))
        datos["traza_agente"] = traza
    wb.log(datos)

    url = getattr(run, "url", None)
    wb.finish()
    return url


def registrar_comparativa(
    wb,
    *,
    resumenes: dict,
    escapes: dict,
    latencias: dict,
    config: dict,
    entity: Optional[str] = None,
    project: str = PROYECTO_POR_DEFECTO,
    grupo: Optional[str] = None,
) -> Optional[str]:
    """Una corrida con las rutas lado a lado: la tabla que va al informe."""
    run = wb.init(entity=entity, project=project, name="comparativa", group=grupo,
                  job_type="comparativa", config=config, reinit=True)
    cols = ["sistema", "faithfulness", "context_precision", "context_recall", "answer_relevancy",
            "prudencia_en_adversariales", "escape_en_gold", "citas_no_respaldadas_en_gold",
            "latencia_s_por_consulta", "casos", "fallos_parseo"]
    tabla = wb.Table(columns=cols)
    for sistema in resumenes:
        r, e = resumenes[sistema], escapes.get(sistema, {})
        tabla.add_data(sistema, r.get("faithfulness"), r.get("context_precision"), r.get("context_recall"),
                       r.get("answer_relevancy"), e.get("prudencia_en_adversariales"), e.get("escape_en_gold"),
                       e.get("citas_no_respaldadas_en_gold"), latencias.get(sistema), r.get("casos"),
                       r.get("fallos_parseo"))
    wb.log({"comparativa": tabla})
    url = getattr(run, "url", None)
    wb.finish()
    return url
