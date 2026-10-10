"""Auditoria 6.1: ¿en que puesto aparece el articulo gold, hasta el 100?

La pregunta que decide si hay que tocar el chunker. Hoy sabemos que 34 de los
45 articulos gold aparecen en el top-10 de alguna configuracion y que **11 no
aparecen en ninguna**. De esos 11 no sabemos si estan en el puesto 11 o si no
estan: `results/busqueda_v2/` se midio con `top_k=10` (ver
`benchmark_busqueda.py:_indice`, que llama a `retrieve(..., top_k=10,
min_score=None)`), y su `puesto_por_caso` vale `None` para todo lo que quede
mas abajo.

  - Si el articulo esta entre los 100 primeros -> el problema es de **ranking**
    y el chunker no se toca en esta reconstruccion.
  - Si no esta -> el problema es de **representacion**, y ahi si entra el
    encabezado de los chunks de continuacion.

Esto NO reconstruye ni modifica el indice: solo consulta. Corre en CPU -- el
embedding de 45 consultas con e5-base no necesita GPU -- y no escribe sobre
ningun resultado historico.

    # en Colab, con Drive montado
    pip install faiss-cpu "torch --index-url https://download.pytorch.org/whl/cpu"
    python -m tools.auditoria_61 --verificar          # solo comprueba huellas
    python -m tools.auditoria_61 --salida results/m3_61_<fecha>

Se detiene antes de medir si alguna huella no coincide con la del indice
evaluado en S08 y S10. Medir sobre otro indice daria un numero que no se puede
comparar con nada.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from tools.evaluation import config as eval_config
from tools.rag import config as rag_config

RAIZ = eval_config.PROJECT_ROOT

# Las huellas del indice evaluado en S08, S10 y busqueda_v2. Los tres
# manifiestos coinciden, y es lo que permite afirmar que midieron sobre lo mismo.
HUELLAS = {
    "hash_indice": "19657d22583f93d0",
    "hash_metadata_indice": "8cd72136235d6dfe",
    "hash_corpus": "1c552822959e2932",
    "hash_eval_set": "a5151999c2095d00",
}
N_CHUNKS = 11975

# El gold aprobado: se leen los veredictos del CSV, no se edita el archivo de
# referencia. Solo cuentan las etiquetas registradas que responden.
CSV_GOLD = RAIZ / "docs" / "m3_articulos_gold_validacion.csv"
GOLD = RAIZ / "data" / "eval_set_articulos.json"
EVAL_SET = RAIZ / "data" / "eval_set.json"

PROFUNDIDADES = (5, 10, 30, 100)


def _huella(path: Path) -> str | None:
    from tools.rag.manifiesto import huella_archivo

    return huella_archivo(path)


def versiones() -> dict[str, str]:
    """Las versiones de lo que hace falta, para que la corrida sea repetible."""
    import importlib.metadata as md
    import sys

    salida = {"python": sys.version.split()[0]}
    for paquete in ("torch", "faiss-cpu", "faiss", "transformers", "numpy", "rank-bm25"):
        try:
            salida[paquete] = md.version(paquete)
        except Exception:
            salida[paquete] = "ausente"
    return salida


def huella_corpus_portable() -> str:
    """`hash_corpus` calculado de forma que coincida en Windows y en Linux.

    `manifiesto.huella_directorio` no sirve para comprobar desde Windows, y por
    DOS razones independientes -- no por una, como decia el informe integral:

      1. No normaliza el fin de linea. En disco los .md estan en CRLF y en git
         en LF.
      2. Ordena con `sorted(p.glob(...))`, o sea comparando objetos Path, y en
         Windows la comparacion de PurePath es INSENSIBLE A MAYUSCULAS. Eso
         manda README.md de la posicion 0 a la 30, y el hash cambia aunque el
         contenido sea identico.

    Corregir solo lo primero da 67ac5eebada5d2b9, que sigue sin coincidir.
    Corrigiendo las dos sale 1c552822959e2932, el valor de los manifiestos.

    Esto vive aqui y no en manifiesto.py a proposito: arreglar la funcion del
    pipeline cambiaria el valor que registran las corridas futuras y necesita
    su propia autorizacion.
    """
    import hashlib

    directorio = Path(rag_config.RAW_CORPUS_DIR)
    h = hashlib.sha256()
    for nombre in sorted(p.name for p in directorio.glob("*.md")):
        h.update(nombre.encode("utf-8"))
        crudo = (directorio / nombre).read_bytes()
        h.update(crudo.replace(bytes([13, 10]), bytes([10])))
    return h.hexdigest()[:16]


def verificar(indice: Path, metadata: Path) -> list[str]:
    """Lista vacia = se puede medir. Cualquier problema detiene la corrida."""
    problemas = []

    if not indice.is_file():
        problemas.append(f"no esta el indice FAISS en {indice}")
    else:
        h = _huella(indice)
        if h != HUELLAS["hash_indice"]:
            problemas.append(f"hash_indice {h} != {HUELLAS['hash_indice']} esperado: "
                             "NO es el indice evaluado")
    if not metadata.is_file():
        problemas.append(f"no esta la metadata en {metadata}")
    else:
        h = _huella(metadata)
        if h != HUELLAS["hash_metadata_indice"]:
            problemas.append(f"hash_metadata_indice {h} != "
                             f"{HUELLAS['hash_metadata_indice']} esperado")

    h = huella_corpus_portable()
    if h != HUELLAS["hash_corpus"]:
        problemas.append(f"hash_corpus {h} != {HUELLAS['hash_corpus']} esperado")

    h = _huella(EVAL_SET)
    if h != HUELLAS["hash_eval_set"]:
        problemas.append(f"hash_eval_set {h} != {HUELLAS['hash_eval_set']} esperado")

    if not CSV_GOLD.is_file():
        problemas.append(f"no esta el gold adjudicado en {CSV_GOLD}")
    return problemas


def gold_aprobado() -> tuple[dict[str, dict[str, set[str]]], dict[str, int]]:
    """Las etiquetas que cuentan, y el recuento de lo que quedo fuera.

    Se parte del gold original y se aplican los veredictos **registrados**:
    se quitan los `no_responde` y se añaden las omisiones de B' que responden.
    Las 128 filas de B y C siguen sin registro individual, asi que sus etiquetas
    se conservan tal como estan en el archivo de referencia.
    """
    import csv

    base = json.loads(GOLD.read_text(encoding="utf-8"))["casos"]
    filas = list(csv.DictReader(CSV_GOLD.open(encoding="utf-8", newline="")))

    quitar = {(f["case_id"], f["doc_id"], f["articulo"]) for f in filas
              if f["origen"] == "etiqueta" and f["veredicto"] == "no_responde"}
    sumar = {(f["case_id"], f["doc_id"], f["articulo"]) for f in filas
             if f["origen"] == "candidato_omision" and f["veredicto"] == "responde"}

    etiquetas: dict[str, dict[str, set[str]]] = {}
    for cid, normas in base.items():
        d: dict[str, set[str]] = {}
        for doc, arts in normas.items():
            quedan = {str(a) for a in arts if (cid, doc, str(a)) not in quitar}
            if quedan:
                d[doc] = quedan
        for c, doc, art in sumar:
            if c == cid:
                d.setdefault(doc, set()).add(art)
        etiquetas[cid] = d

    cuenta = {
        "quitadas_no_responde": len(quitar),
        "anadidas_omision": len(sumar),
        "sin_registro_individual": sum(
            1 for f in filas if f["veredicto"] == "pendiente"),
    }
    return etiquetas, cuenta


def _es_continuacion(chunk_meta: dict, articulo: str) -> bool:
    """¿Este chunk trae el articulo SIN su encabezado?

    Es el hallazgo del anexo de chunking: 2 060 de 2 069 chunks de continuacion
    empiezan a mitad de frase. Importa aqui porque un acierto que solo llega por
    un chunk de continuacion es un acierto fragil.
    """
    texto = chunk_meta.get("text", "")[:160]
    patron = rf"[Aa]rt[ií]culo\s+{re.escape(articulo)}\b"
    return not re.search(patron, texto)


def medir(indice: Path, metadata: Path, salida: Path) -> int:
    # FaissStore.load directamente y no pipeline.load_index(): este ultimo no
    # acepta rutas y cargaria el indice de artifacts/, que aqui no existe.
    from tools.rag.embed_store import FaissStore
    from tools.rag.enrutador import enrutador_por_defecto
    from tools.rag.retrieve import retrieve

    etiquetas, cuenta = gold_aprobado()
    casos = {str(c["id"]): c for c in json.loads(EVAL_SET.read_text(encoding="utf-8"))}
    store = FaissStore.load(index_path=indice, metadata_path=metadata)
    if len(store.metadata) != N_CHUNKS:
        raise SystemExit(f"el indice tiene {len(store.metadata)} chunks, no {N_CHUNKS}")
    por_chunk = {m["chunk_id"]: m for m in store.metadata}
    enrutador_por_defecto()  # entrena antes de medir, para no contar su tiempo

    filas = []
    for cid, etiqueta in etiquetas.items():
        caso = casos.get(cid)
        if not caso or not etiqueta:
            continue
        pregunta = next((m["content"] for m in caso["messages"]
                         if m["role"] == "user"), "")
        # top_k=100 y SIN piso: aqui se mide donde cae el articulo, no que
        # fragmentos sobrevivirian al filtro de produccion.
        resultados = retrieve(pregunta, store, top_k=100, min_score=None,
                              use_router=True)
        puesto = None
        por_continuacion = None
        for i, r in enumerate(resultados, start=1):
            arts = etiqueta.get(getattr(r, "doc_id", ""), set())
            hallado = next((a for a in arts
                            if a in {str(x) for x in (r.articulos_incluidos or ())}), None)
            if hallado:
                puesto = i
                meta = por_chunk.get(getattr(r, "chunk_id", ""), {})
                por_continuacion = _es_continuacion(meta, hallado)
                break
        filas.append({
            "case_id": cid,
            "categoria": caso.get("category"),
            "pregunta": pregunta,
            "gold": {d: sorted(a) for d, a in etiqueta.items()},
            "puesto": puesto,
            "solo_por_chunk_de_continuacion": por_continuacion,
            "normas_del_top_100": sorted({getattr(r, "doc_id", "") for r in resultados}),
        })

    n = len(filas)
    agregado = {f"acierto@{k}": f"{sum(1 for f in filas if f['puesto'] and f['puesto'] <= k)}/{n}"
                for k in PROFUNDIDADES}
    agregado["ausente_en_top_100"] = f"{sum(1 for f in filas if f['puesto'] is None)}/{n}"
    agregado["acierto_solo_por_continuacion"] = (
        f"{sum(1 for f in filas if f['solo_por_chunk_de_continuacion'])}/{n}")

    salida.mkdir(parents=True, exist_ok=False)   # exist_ok=False: no sobrescribe
    (salida / "auditoria_61_por_caso.json").write_text(
        json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
    manifiesto = {
        "modulo": "auditoria_61",
        "top_k": 100,
        "min_score": None,
        "use_router": True,
        "huellas_verificadas": HUELLAS,
        "n_chunks": len(store.metadata),
        "gold": {"archivo": str(GOLD.relative_to(RAIZ)),
                 "csv_veredictos": str(CSV_GOLD.relative_to(RAIZ)),
                 "huella_csv": _huella(CSV_GOLD), **cuenta},
        "dependencias": versiones(),
        "agregado": agregado,
    }
    (salida / "run_manifest.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps(agregado, ensure_ascii=False, indent=1))
    print(f"\nEscrito {salida}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--indice", type=Path, default=rag_config.FAISS_INDEX_PATH)
    p.add_argument("--metadata", type=Path, default=rag_config.FAISS_METADATA_PATH)
    p.add_argument("--salida", type=Path, help="directorio nuevo donde escribir")
    p.add_argument("--verificar", action="store_true",
                   help="solo comprueba huellas y dependencias, no mide")
    args = p.parse_args(argv)

    print("dependencias:")
    for k, v in versiones().items():
        print(f"  {k:14s} {v}")
    etiquetas, cuenta = gold_aprobado()
    print(f"\ngold aprobado: {cuenta}")

    problemas = verificar(args.indice, args.metadata)
    print()
    if problemas:
        print(f"{len(problemas)} problemas: NO se mide nada")
        for s in problemas:
            print(f"  - {s}")
        return 1
    print("Huellas verificadas: es el indice evaluado en S08 y S10.")

    if args.verificar:
        return 0
    if not args.salida:
        raise SystemExit("falta --salida: hay que decir donde escribir")
    return medir(args.indice, args.metadata, args.salida)


if __name__ == "__main__":
    raise SystemExit(main())
