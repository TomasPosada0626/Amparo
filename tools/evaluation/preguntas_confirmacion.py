"""El conjunto de confirmacion de M3: preguntas nuevas que no se usan para elegir.

Las 45 gold del eval set son las mismas con que se ajusta la busqueda: si algo
sube ahi, puede estar ajustado a esas 45. `data/preguntas_confirmacion_m3.json`
trae preguntas escritas despues de la corrida del 2026-10-14 y antes de
cualquier experimento de busqueda (`docs/m3_protocolo_aceptacion.md`, 2). Solo
sirven para confirmar al final.

Mismo formato que data/eval_set.json (id, category, tipo, criterio, messages)
mas `articulos_gold` ({doc_id: [articulos]}, como `auditoria_61.gold_aprobado`),
asi que las herramientas de medicion las leen sin cambios.

    python -m tools.evaluation.preguntas_confirmacion --verificar
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUTA = RAIZ / "data" / "preguntas_confirmacion_m3.json"
EVAL_SET = RAIZ / "data" / "eval_set.json"
DATASET = RAIZ / "data" / "dataset.jsonl"

# Dos preguntas con esta proporcion de palabras en comun (Jaccard) o mas se
# consideran la misma pregunta: el conjunto dejaria de ser nuevo.
UMBRAL_PARECIDO = 0.5


def cargar(ruta: Path = RUTA) -> list[dict]:
    return json.loads(ruta.read_text(encoding="utf-8"))["casos"]


def huella_archivo(ruta: Path = RUTA) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:16]


def gold(casos: list[dict] | None = None) -> dict[str, dict[str, set[str]]]:
    """{'9501': {doc_id: {'158'}}}: la forma de `auditoria_61.gold_aprobado`."""
    casos = cargar() if casos is None else casos
    return {str(c["id"]): {d: {str(a) for a in arts} for d, arts in c["articulos_gold"].items()}
            for c in casos}


def pregunta(caso: dict) -> str:
    return next(m["content"] for m in caso["messages"] if m["role"] == "user")


def _palabras(texto: str) -> set[str]:
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return {w for w in re.findall(r"[a-z0-9]+", t) if len(w) > 2}


def parecido(a: str, b: str) -> float:
    pa, pb = _palabras(a), _palabras(b)
    return len(pa & pb) / len(pa | pb) if pa | pb else 0.0


def _preguntas_existentes() -> list[tuple[str, str]]:
    """(origen, pregunta) del eval set y del dataset de entrenamiento."""
    salida = [(f"eval_set:{r['id']}", pregunta(r)) for r in json.loads(EVAL_SET.read_text(encoding="utf-8"))]
    if DATASET.exists():
        for linea in DATASET.read_text(encoding="utf-8").splitlines():
            if linea.strip():
                r = json.loads(linea)
                salida.append((f"dataset:{r.get('id')}", pregunta(r)))
    return salida


def _articulos_del_indice(metadata: Path) -> dict[str, set[str]]:
    por_doc: dict[str, set[str]] = {}
    for linea in metadata.read_text(encoding="utf-8").splitlines():
        m = json.loads(linea)
        por_doc.setdefault(m["doc_id"], set()).update(str(a) for a in m.get("articulos_incluidos") or ())
    return por_doc


def problemas(casos: list[dict], metadata: Path | None = None) -> list[str]:
    """Lo que haria que el conjunto no sirviera para confirmar."""
    p = []
    ids = [c["id"] for c in casos]
    if len(ids) != len(set(ids)):
        p.append("ids repetidos")
    usados = {r["id"] for r in json.loads(EVAL_SET.read_text(encoding="utf-8"))}
    if usados & set(ids):
        p.append(f"ids que ya usa el eval set: {sorted(usados & set(ids))}")
    for c in casos:
        if c.get("tipo") != "gold" or not c.get("criterio") or not c.get("articulos_gold"):
            p.append(f"{c['id']}: le falta tipo gold, criterio o articulos_gold")
    existentes = _preguntas_existentes()
    for c in casos:
        q = pregunta(c)
        origen, s = max(((o, parecido(q, e)) for o, e in existentes), key=lambda x: x[1])
        if s >= UMBRAL_PARECIDO:
            p.append(f"{c['id']}: se parece a {origen} (Jaccard {s:.2f})")
    if metadata is not None and metadata.exists():
        indice = _articulos_del_indice(metadata)
        for c in casos:
            for doc, arts in c["articulos_gold"].items():
                faltan = {str(a) for a in arts} - indice.get(doc, set())
                if faltan:
                    p.append(f"{c['id']}: {doc} no tiene en el indice los articulos {sorted(faltan)}")
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--metadata", type=Path, default=None,
                    help="metadata del indice (por defecto la de tools.rag.config, si existe)")
    a = ap.parse_args(argv)
    metadata = a.metadata
    if metadata is None:
        try:
            from tools.rag import config as rag_config
            metadata = Path(rag_config.FAISS_METADATA_PATH)
        except Exception:
            metadata = None
    casos = cargar()
    p = problemas(casos, metadata)
    for x in p:
        print("PROBLEMA:", x)
    revisado = "con" if metadata is not None and metadata.exists() else "SIN"
    print(f"{len(casos)} preguntas, {revisado} comprobacion de articulos contra el indice; "
          f"huella {huella_archivo()}: {'OK' if not p else 'NO SIRVE'}")
    return 0 if not p else 1


if __name__ == "__main__":
    raise SystemExit(main())
