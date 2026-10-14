"""Paso 7 de M3: ¿un modelo de embeddings mas fuerte trae el articulo correcto?

Una sola variable: el modelo que embebe. Todo lo demas es el camino de
produccion: los mismos fragmentos del indice evaluado (`artifacts/`), el mismo
texto indexable (cita + capitulo + texto, `chunk.texto_indexable`), el mismo
pooling de e5 (`embed_store._embed_with_prefix`), el mismo enrutador y el mismo
`retrieve`. El indice experimental se guarda aparte, en
`artifacts/experimentos/<modelo>/`: el de produccion no se toca.

La medida es la de `results/m3_busqueda_cpu_2026-10-13/puestos_gold.json`:
puesto del primer articulo gold aprobado (`auditoria_61.gold_aprobado`) en el
top-10, sobre las 45 gold. El conjunto de confirmacion NO se mira aqui
(`docs/m3_protocolo_aceptacion.md`, 2): se usa al final, una vez.

    python -m tools.rag.experimento_embeddings --construir intfloat/multilingual-e5-large
    python -m tools.rag.experimento_embeddings --medir intfloat/multilingual-e5-large
    python -m tools.rag.experimento_embeddings --medir produccion             # control sin piso: 20/45 en el top-5
    python -m tools.rag.experimento_embeddings --medir produccion --piso 0.81 # como en produccion: 21/45
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from types import SimpleNamespace

from tools.rag import config

DIR_EXPERIMENTOS = config.ARTIFACTS_DIR / "experimentos"
KS = (1, 3, 5, 10)
LOTE = 256   # fragmentos por parte guardada: si se corta, se retoma desde la ultima


def _carpeta(model_id: str) -> Path:
    return DIR_EXPERIMENTOS / model_id.replace("/", "__")


def fragmentos(metadata_path: Path = config.FAISS_METADATA_PATH) -> list[dict]:
    with Path(metadata_path).open(encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def texto(meta: dict) -> str:
    """El texto que produccion embebio para ese fragmento."""
    from tools.rag.chunk import texto_indexable

    return texto_indexable(SimpleNamespace(
        fuente=meta.get("fuente", ""), articulos_incluidos=meta.get("articulos_incluidos") or [],
        capitulo=meta.get("capitulo", ""), text=meta.get("text", "")))


def construir(model_id: str, batch_size: int = 16) -> Path:
    """Embebe todos los fragmentos con model_id y guarda el indice FAISS aparte."""
    import numpy as np
    import faiss
    from tools.rag.embed_store import _embed_with_prefix

    metas = fragmentos()
    carpeta = _carpeta(model_id)
    partes = carpeta / "partes"
    partes.mkdir(parents=True, exist_ok=True)
    inicio = time.perf_counter()
    hechos_al_empezar = None
    for n, desde in enumerate(range(0, len(metas), LOTE)):
        destino = partes / f"{n:04d}.npy"
        if destino.exists():
            continue
        if hechos_al_empezar is None:
            hechos_al_empezar = desde
        vecs = _embed_with_prefix([texto(m) for m in metas[desde:desde + LOTE]], config.E5_PASSAGE_PREFIX,
                                  model_id=model_id, batch_size=batch_size)
        np.save(destino, np.asarray(vecs, dtype="float32"))
        hechos = min(desde + LOTE, len(metas))
        ritmo = (time.perf_counter() - inicio) / max(hechos - hechos_al_empezar, 1)
        print(f"[{model_id}] {hechos}/{len(metas)} -- ETA ~{ritmo * (len(metas) - hechos) / 60:.0f} min", flush=True)
    vecs = np.concatenate([np.load(p) for p in sorted(partes.glob("*.npy"))])
    if len(vecs) != len(metas):
        raise ValueError(f"{len(vecs)} vectores para {len(metas)} fragmentos: faltan partes")
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    faiss.write_index(index, str(carpeta / "rag_index.faiss"))
    (carpeta / "construccion.json").write_text(json.dumps({
        "modelo": model_id, "fragmentos": len(metas), "dim": int(vecs.shape[1]),
        "metadata": str(config.FAISS_METADATA_PATH)}, indent=2) + "\n", encoding="utf-8")
    print(f"[{model_id}] indice -> {carpeta / 'rag_index.faiss'}")
    return carpeta


def _store_y_consulta(model_id: str):
    """(store, funcion de embedding de la consulta) para ese modelo."""
    from tools.rag.embed_store import FaissStore, _embed_with_prefix

    if model_id == "produccion":
        return FaissStore.load(), None
    import faiss
    index = faiss.read_index(str(_carpeta(model_id) / "rag_index.faiss"))
    store = FaissStore(dim=index.d, index=index, metadata=fragmentos())
    return store, lambda q: _embed_with_prefix([q], config.E5_QUERY_PREFIX, model_id=model_id)[0]


def medir(model_id: str, top_k: int = 10, min_score: float | None = None,
          borradores: dict[str, str] | None = None, **opciones) -> dict:
    """Puesto del articulo gold en el top-10 de cada una de las 45 gold.

    Sin piso por defecto: el piso (0.81) esta calibrado sobre la escala de e5-base
    y otro modelo tiene otra. Con el enrutador el piso si cambia el orden (quita
    fragmentos flojos de las normas priorizadas): produccion da 20/45 en el top-5
    sin piso y 21/45 con 0.81. Se comparan modelos sin piso y el piso se calibra
    aparte, solo para el que gane.

    opciones: lo que se le pasa a `retrieve` (voto_denso, use_rerank, reranker_id,
    rerank_con_cita, use_hybrid). Asi R1 y R2 del paso 7 se miden con la misma vara."""
    from tools import auditoria_61
    from tools.rag import retrieve as retrieve_mod
    from tools.rag.benchmark_busqueda import acierta
    from tools.evaluation import eval_set

    store, embed = _store_y_consulta(model_id)
    etiquetas, _ = auditoria_61.gold_aprobado()
    preguntas = {str(r["id"]): r["messages"][1]["content"] for r in eval_set.load_eval_set()}
    # Los vectores de las preguntas se calculan primero y el encoder se libera:
    # en un PC de 8 GB no caben a la vez e5 y un cross-encoder grande.
    import gc
    from tools.rag import embed_store
    embed = embed or retrieve_mod.embed_query
    # borradores (R4): la busqueda densa embebe la pregunta MAS un borrador de
    # respuesta del modelo, que ya habla en lenguaje juridico; el enrutador sigue
    # leyendo solo la pregunta.
    vectores = {preguntas[cid]: embed(preguntas[cid] + (" " + borradores[cid] if borradores else ""))
                for cid in etiquetas}
    embed_store._MODELO_CACHE.clear()
    gc.collect()
    original = retrieve_mod.embed_query
    retrieve_mod.embed_query = lambda q: vectores[q]
    try:
        puestos = {}
        for cid, etiqueta in sorted(etiquetas.items()):
            res = retrieve_mod.retrieve(preguntas[cid], store, top_k=top_k, min_score=min_score, **opciones)
            puestos[cid] = next((n for n in range(1, len(res) + 1) if acierta(res[n - 1:n], etiqueta)), None)
    finally:
        retrieve_mod.embed_query = original
    acierto = {f"@{k}": sum(1 for p in puestos.values() if p is not None and p <= k) for k in KS}
    return {"modelo": model_id, "piso": min_score, "opciones": opciones, "n": len(puestos),
            "acierto": acierto, "puestos": puestos}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--construir", metavar="MODELO")
    g.add_argument("--medir", metavar="MODELO", help="un modelo ya construido, o 'produccion'")
    ap.add_argument("--piso", type=float, default=None, help="piso de coseno (por defecto, sin piso)")
    ap.add_argument("--voto-denso", type=int, default=None, help="R1: normas de los N primeros densos (0 = apagado)")
    ap.add_argument("--rerank", metavar="MODELO", help="R2: reordenar con ese cross-encoder")
    ap.add_argument("--con-cita", action="store_true", help="R2: el cross-encoder lee la cita y el capitulo")
    ap.add_argument("--hybrid", action="store_true")
    ap.add_argument("--borradores", type=Path, help="R4: jsonl con id y generated (respuestas sin RAG de M2)")
    ap.add_argument("--salida", type=Path, help="json donde guardar la medicion")
    a = ap.parse_args(argv)
    if a.construir:
        construir(a.construir)
        return 0
    opciones = {}
    if a.voto_denso is not None:
        opciones["voto_denso"] = a.voto_denso
    if a.rerank:
        opciones.update(use_rerank=True, reranker_id=a.rerank, rerank_con_cita=a.con_cita)
    if a.hybrid:
        opciones["use_hybrid"] = True
    borradores = None
    if a.borradores:
        borradores = {str(json.loads(l)["id"]): json.loads(l)["generated"]
                      for l in a.borradores.read_text(encoding="utf-8").splitlines() if l.strip()}
    r = medir(a.medir, min_score=a.piso, borradores=borradores, **opciones)
    r["borradores"] = str(a.borradores) if a.borradores else None
    print(f"{r['modelo']} (piso {a.piso}, {opciones}): " + "  ".join(f"{k} {v}/{r['n']}" for k, v in r["acierto"].items()))
    if a.salida:
        a.salida.parent.mkdir(parents=True, exist_ok=True)
        a.salida.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
