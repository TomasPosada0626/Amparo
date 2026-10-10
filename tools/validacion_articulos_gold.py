"""Instrumento para validar `data/eval_set_articulos.json` con un abogado.

Ese archivo dice que articulos responden cada una de las 45 preguntas gold del
eval set, y su propia nota avisa que esta **pendiente de revision juridica**.
Importa porque es la referencia contra la que se va a medir el acierto@k de la
recuperacion (prueba 6.1): si un articulo gold esta mal asignado, el
diagnostico del sistema sale mal.

La regla que define el etiquetado, del propio archivo: *"un caso cuenta como
acierto si la busqueda trae al menos uno de sus articulos"*. De ahi sale la
priorizacion, porque no todas las etiquetas mueven la medicion por igual:

  A  sostiene el acierto   El sistema SI trajo ese articulo y por eso el caso
                           cuenta como acierto. Si la etiqueta esta mal, el
                           acierto es falso y estariamos midiendo mejoras
                           contra una linea base inflada. 27 etiquetas.
  B' candidato a omision   El caso fallo, pero el sistema trajo OTROS
                           articulos de la norma correcta que nadie etiqueto.
                           Si alguno responde, el fallo es falso. 62 articulos.
  B  caso fallido          Etiquetas de casos que fallaron. Si estan mal, el
                           fallo puede ser falso, pero solo importa si el
                           sistema trajo la alternativa (eso ya es B'). 82.
  C  redundante            El caso ya acerto por otro articulo, asi que esta
                           etiqueta no cambia el resultado. 46.

A y B' son el camino critico: 89 juicios, cada uno con el texto del articulo
delante. B y C se revisan si queda tiempo.

    python -m tools.validacion_articulos_gold --crear     # arma el CSV
    python -m tools.validacion_articulos_gold --revisar   # valida el llenado
    python -m tools.validacion_articulos_gold --matriz     # el .md de consulta
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from tools.evaluation import config as eval_config

RAIZ = eval_config.PROJECT_ROOT
GOLD = RAIZ / "data" / "eval_set_articulos.json"
EVAL_SET = RAIZ / "data" / "eval_set.json"
# La metadata del indice evaluado en S08/S10. No esta versionada (48 MB entre
# ella y el .faiss): se baja de Drive a results/<corrida>/ y se comprueba
# contra hash_metadata_indice del manifiesto antes de usarla.
METADATA = RAIZ / "results" / "m3_s08_2026-10-09" / "rag_index_metadata.jsonl"
HASH_METADATA = "8cd72136235d6dfe"
REGISTROS = RAIZ / "results" / "m3_s08_2026-10-09" / "eval_records_config_a.json"

SALIDA = RAIZ / "docs" / "m3_articulos_gold_validacion.csv"
MATRIZ = RAIZ / "docs" / "m3_articulos_gold_matriz.md"

COLUMNAS = [
    "case_id", "categoria", "pregunta",
    "doc_id", "norma", "articulo",
    "origen", "clase_impacto", "prioridad",
    "fue_recuperado", "esta_partido", "n_chunks",
    "pregunta_al_abogado",
    # lo que el abogado llena
    "veredicto", "confianza", "justificacion",
    # trazabilidad
    "revisor", "fecha_revision", "huella_metadata",
]

VOCABULARIO = {
    # Para origen=etiqueta: ¿este articulo responde la pregunta?
    # Para origen=candidato_omision: ¿este articulo tambien la responde?
    "veredicto": {"responde", "responde_parcial", "no_responde", "pendiente"},
    "confianza": {"alta", "media", "baja"},
    "origen": {"etiqueta", "candidato_omision"},
    "clase_impacto": {"A_sostiene_acierto", "B_caso_fallido",
                      "B_candidato_omision", "C_redundante"},
}

OBLIGATORIAS = ["veredicto", "confianza", "justificacion", "revisor", "fecha_revision"]


def _normalizar(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "")).strip()


def huella_metadata() -> str:
    from tools.rag.manifiesto import huella_archivo

    return huella_archivo(METADATA) or ""


def exigir_metadata() -> None:
    """Sin la metadata correcta no hay texto de articulo que leer."""
    if not METADATA.is_file():
        raise SystemExit(
            f"Falta {METADATA.relative_to(RAIZ)}.\n"
            "Se baja de Drive (el .jsonl, no el .faiss) y queda ignorado por git."
        )
    h = huella_metadata()
    if h != HASH_METADATA:
        raise SystemExit(
            f"La metadata no es la del indice evaluado.\n"
            f"  calculada: {h}\n  esperada:  {HASH_METADATA}\n"
            "Si copiaste el archivo con un editor, puede haber cambiado los fines "
            "de linea. Copialo en binario."
        )


def cargar_articulos() -> dict[str, dict[str, list[dict]]]:
    """doc_id -> articulo -> [chunks en orden], desde la metadata del indice."""
    exigir_metadata()
    por_doc: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    with METADATA.open(encoding="utf-8") as f:
        for linea in f:
            if not linea.strip():
                continue
            c = json.loads(linea)
            for a in (c.get("articulos_incluidos") or []):
                por_doc[c["doc_id"]][str(a)].append(c)
    return por_doc


def texto_articulo(chunks: list[dict]) -> str:
    """El articulo completo, uniendo sus chunks en el orden del indice.

    Los chunks de continuacion no traen el encabezado "Articulo N" -- es el
    hallazgo del anexo de chunking -- asi que unirlos es la unica forma de
    leer el articulo entero.
    """
    def orden(c):
        m = re.search(r"chunk(\d+)$", c["chunk_id"])
        return int(m.group(1)) if m else 0

    return _normalizar(" ".join(c.get("text", "") for c in sorted(chunks, key=orden)))


def _articulos_recuperados() -> dict[str, dict[str, set[str]]]:
    """caso -> doc_id -> articulos que la busqueda trajo, de las citas."""
    registros = json.loads(REGISTROS.read_text(encoding="utf-8"))
    fuera: dict[str, dict[str, set[str]]] = {}
    for x in registros:
        d: dict[str, set[str]] = defaultdict(set)
        for c in (x.get("retrieved_chunks") or []):
            doc = c["chunk_id"].split("::")[0]
            d[doc] |= set(re.findall(r"[Aa]rt[ií]culo\s+([0-9]+[A-Za-z-]*)", c.get("cita") or ""))
        fuera[str(x.get("id"))] = dict(d)
    return fuera


def _pregunta(caso: dict) -> str:
    return next((m.get("content", "") for m in caso.get("messages", [])
                 if m.get("role") == "user"), "")


def filas() -> list[dict]:
    gold = json.loads(GOLD.read_text(encoding="utf-8"))["casos"]
    casos = {str(c["id"]): c for c in json.loads(EVAL_SET.read_text(encoding="utf-8"))}
    traido = _articulos_recuperados()
    por_doc = cargar_articulos()
    h = huella_metadata()

    salida: list[dict] = []
    for cid, normas in gold.items():
        caso = casos.get(cid, {})
        q = _pregunta(caso)
        t = traido.get(cid, {})
        acerto = any(set(arts) & t.get(doc, set()) for doc, arts in normas.items())

        for doc, arts in normas.items():
            chunks_doc = por_doc.get(doc, {})
            nombre = next((c.get("fuente", "") for a in arts
                           for c in chunks_doc.get(str(a), [])), doc)

            for a in arts:
                chunks = chunks_doc.get(str(a), [])
                recuperado = str(a) in t.get(doc, set())
                if recuperado:
                    clase, prio = "A_sostiene_acierto", 1
                    pregunta_ab = ("El sistema trajo este articulo y por eso el caso "
                                   "cuenta como acierto. ¿Responde de verdad la consulta?")
                elif not acerto:
                    clase, prio = "B_caso_fallido", 3
                    pregunta_ab = "¿Este articulo responde la consulta?"
                else:
                    clase, prio = "C_redundante", 4
                    pregunta_ab = "¿Este articulo responde la consulta?"
                salida.append({
                    "case_id": cid, "categoria": caso.get("category", ""), "pregunta": q,
                    "doc_id": doc, "norma": nombre, "articulo": str(a),
                    "origen": "etiqueta", "clase_impacto": clase, "prioridad": str(prio),
                    "fue_recuperado": "si" if recuperado else "no",
                    "esta_partido": "si" if len(chunks) > 1 else "no",
                    "n_chunks": str(len(chunks)),
                    "pregunta_al_abogado": pregunta_ab,
                    "veredicto": "pendiente", "confianza": "", "justificacion": "",
                    "revisor": "", "fecha_revision": "", "huella_metadata": h,
                })

            # candidatos a omision: lo que el sistema trajo de esta norma y
            # nadie etiqueto, solo cuando el caso fallo.
            if not acerto:
                for extra in sorted(t.get(doc, set()) - set(map(str, arts))):
                    chunks = chunks_doc.get(extra, [])
                    salida.append({
                        "case_id": cid, "categoria": caso.get("category", ""), "pregunta": q,
                        "doc_id": doc, "norma": nombre, "articulo": extra,
                        "origen": "candidato_omision",
                        "clase_impacto": "B_candidato_omision", "prioridad": "2",
                        "fue_recuperado": "si", "esta_partido": "si" if len(chunks) > 1 else "no",
                        "n_chunks": str(len(chunks)),
                        "pregunta_al_abogado": (
                            "El sistema trajo este articulo, que NO esta etiquetado, y el "
                            "caso figura como fallo. ¿Tambien responde la consulta? Si si, "
                            "el fallo es falso y hay que agregarlo al gold."),
                        "veredicto": "pendiente", "confianza": "", "justificacion": "",
                        "revisor": "", "fecha_revision": "", "huella_metadata": h,
                    })
    salida.sort(key=lambda f: (f["prioridad"], f["case_id"], f["doc_id"],
                               int(re.sub(r"\D", "", f["articulo"]) or 0)))
    return salida


def revisar(fs: list[dict]) -> list[str]:
    problemas: list[str] = []
    vistos: set[tuple] = set()
    for f in fs:
        ref = f"{f['case_id']}/{f['doc_id']}/art {f['articulo']}"
        clave = (f["case_id"], f["doc_id"], f["articulo"], f["origen"])
        if clave in vistos:
            problemas.append(f"{ref}: fila repetida")
        vistos.add(clave)

        for col, vocab in VOCABULARIO.items():
            v = (f.get(col) or "").strip()
            if v and v not in vocab:
                problemas.append(f"{ref}: {col} {v!r} fuera del vocabulario")

        if (f.get("veredicto") or "").strip() == "pendiente":
            continue  # sin adjudicar todavia: no se le exige lo demas
        for col in OBLIGATORIAS:
            if not (f.get(col) or "").strip():
                problemas.append(f"{ref}: falta {col}")
        if f.get("huella_metadata") != HASH_METADATA:
            problemas.append(f"{ref}: huella_metadata no es la del indice evaluado")
    return problemas


def resumen(fs: list[dict]) -> None:
    from collections import Counter

    print(f"filas: {len(fs)}  ({len({f['case_id'] for f in fs})} casos)")
    for col in ("clase_impacto", "origen", "veredicto", "esta_partido"):
        print(f"  {col:20s} {dict(Counter(f[col] for f in fs))}")


def escribir_matriz(fs: list[dict]) -> None:
    """El .md de consulta: cada fila con el texto completo del articulo."""
    por_doc = cargar_articulos()
    partes = [
        "# Matriz de validacion: articulos gold del eval set",
        "",
        "Material de consulta para validar `data/eval_set_articulos.json`. El",
        "dictamen se registra en `docs/m3_articulos_gold_validacion.csv`.",
        "",
        f"Texto de los articulos tomado de la metadata del indice evaluado en S08 y",
        f"S10 (`hash_metadata_indice = {HASH_METADATA}`), uniendo los chunks de cada",
        "articulo en orden. Los chunks de continuacion no traen encabezado, asi que",
        "unirlos es la unica forma de leer el articulo entero.",
        "",
        "La regla del etiquetado: **un caso cuenta como acierto si la busqueda trae",
        "al menos uno de sus articulos.**",
        "",
    ]
    orden_clase = ["A_sostiene_acierto", "B_candidato_omision",
                   "B_caso_fallido", "C_redundante"]
    titulos = {
        "A_sostiene_acierto": "Clase A -- sostienen un acierto (si estan mal, el acierto es falso)",
        "B_candidato_omision": "Clase B' -- candidatos a omision (si responden, el fallo es falso)",
        "B_caso_fallido": "Clase B -- etiquetas de casos fallidos",
        "C_redundante": "Clase C -- redundantes (el caso ya acerto por otro articulo)",
    }
    for clase in orden_clase:
        grupo = [f for f in fs if f["clase_impacto"] == clase]
        if not grupo:
            continue
        partes += ["", "---", "", f"# {titulos[clase]}", "",
                   f"{len(grupo)} filas en {len({f['case_id'] for f in grupo})} casos.", ""]
        for f in grupo:
            texto = texto_articulo(por_doc.get(f["doc_id"], {}).get(f["articulo"], []))
            partes += [
                f"## {f['case_id']} · {f['norma'] or f['doc_id']} · articulo {f['articulo']}",
                "",
                f"**Categoria:** {f['categoria']}",
                "",
                f"**Pregunta:** {f['pregunta']}",
                "",
                f"**Estado:** recuperado={f['fue_recuperado']} · "
                f"partido en {f['n_chunks']} chunk(s)",
                "",
                f"**Lo que hay que decidir:** {f['pregunta_al_abogado']}",
                "",
                "**Texto del articulo:**",
                "",
                f"> {texto if texto else '(sin texto en el indice)'}",
                "",
            ]
    MATRIZ.write_text("\n".join(partes) + "\n", encoding="utf-8")
    print(f"Escrito {MATRIZ.relative_to(RAIZ)} ({MATRIZ.stat().st_size/1000:.0f} KB)")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--crear", action="store_true", help="arma el CSV vacio")
    p.add_argument("--revisar", action="store_true", help="valida el CSV llenado")
    p.add_argument("--matriz", action="store_true", help="arma el .md de consulta")
    args = p.parse_args(argv)

    if args.revisar:
        with SALIDA.open(encoding="utf-8", newline="") as f:
            fs = list(csv.DictReader(f))
        resumen(fs)
        problemas = revisar(fs)
        if problemas:
            print(f"\n{len(problemas)} problemas:")
            for s in problemas[:25]:
                print(f"  - {s}")
            return 1
        print("\nSin problemas.")
        return 0

    fs = filas()
    if args.matriz:
        escribir_matriz(fs)
        return 0
    if args.crear:
        with SALIDA.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNAS)
            w.writeheader()
            w.writerows(fs)
        print(f"Escrito {SALIDA.relative_to(RAIZ)}")
    resumen(fs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
