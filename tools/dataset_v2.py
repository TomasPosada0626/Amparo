"""Dataset de M1 v2: los ejemplos que ensenan a usar el contexto.

Por que existe. M1 entrenaba con una sola forma de conversacion: prompt de M1,
pregunta y respuesta sin citas (los 1536 sin contexto de data/dataset.jsonl: 0 con
contexto, 0 de 1536 respuestas con un articulo). En M3 el modelo recibe
fragmentos de normas y se le pide citar de ahi; nunca vio un ejemplo asi y cito
en 0 de 9 casos aun con el contexto perfecto (results/m3_s08_2026-10-07). Este
modulo construye los ejemplos CON contexto de data/dataset.jsonl, en tres modos:

  B1  el contexto trae el articulo que responde, entre fragmentos que no sirven:
      la respuesta cita ese articulo (norma y numero) tal como aparece.
  B2  ningun fragmento sirve: la respuesta es la frase de escape exacta y donde
      consultar, sin afirmar nada de fondo.
  B3  el contexto responde una parte: se responde esa parte con su cita y se
      dice que la otra no esta respaldada.

No hay ejemplos sin contexto (el modo A del piloto se quito el 2026-10-08):
cuando la busqueda no trae nada, el sistema responde la frase de escape SIN
llamar al modelo (pipeline._generar_verificado), asi que un ejemplo sin contexto
le ensenaria al modelo una situacion que en servicio nunca ve. Para eso ya esta
los ejemplos sin contexto de data/dataset.jsonl.

De donde sale el contexto. De la MISMA busqueda que usa el sistema al
responder (Buscador): en Colab, retrieve() con e5 + FAISS + enrutador
(python -m tools.dataset_v2 --indice); en local, BM25 + enrutador, que no
necesita descargar modelos. Si la busqueda trae el articulo que responde entre
los 5 primeros, el contexto es exactamente lo que trajo (contexto_origen
"busqueda"); si no, el articulo se mete en el lugar de uno de los fragmentos
que si trajo ("busqueda+oraculo"). Asi nunca se entrena a citar sobre un
contexto que no tiene con que responder, y los fragmentos que acompanan son los
que de verdad devuelve el buscador.

data/dataset_legal.jsonl NO se toca: su split es el de M1/M2 y cambiarlo rompe
la comparacion con la corrida de M2 del 2026-10-06. Este archivo va aparte y
cada ejemplo cae en el mismo lado (train o val) que su pregunta base
(tools/evaluation/dataset.split_v2).

Los mensajes se arman con las MISMAS funciones que usa el sistema al responder
(prompt_template.build_messages): un ejemplo con un formato distinto del de
inferencia ensena otra cosa (fue el fallo del extra de DSPy).

Fuentes: data/dataset_src_v2/*.md, una por categoria, con el formato

    # Categoria: Arriendo

    ## 2001
    modo: B1
    base: 60
    fuentes: LEY-820-2003:20
    P: <solo si no hay base; si hay base se toma la pregunta del dataset>
    R: <respuesta>

`fuentes` son articulos del corpus como IDENTIFIER:articulo, separados por
punto y coma. En B1 y B3 son los que responden; en B2 se omite.

    python -m tools.dataset_v2 --check    # valida sin escribir
    python -m tools.dataset_v2            # escribe data/dataset_v2.jsonl (BM25)
    python -m tools.dataset_v2 --indice   # en Colab: contexto de e5 + FAISS
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "data" / "dataset_src_v2"
# Los ejemplos con contexto ya no viven en un archivo propio: entran a
# data/dataset.jsonl con origen "v2". Esta ruta queda para --solo-v2, que
# sirve para revisar la construccion sin tocar el dataset.
OUTPUT_JSONL = PROJECT_ROOT / "data" / "dataset_v2_revision.jsonl"

MODOS = ("B1", "B2", "B3")
NORMAS_GENERALES = {"codigo_civil_ley_84_1873", "codigo_comercio_decreto_410_1971",
                    "codigo_general_proceso_ley_1564_2012", "cpaca_ley_1437_2011"}
CANDIDATOS = 30                     # cuantos pide al buscador antes de armar el contexto
FRAGMENTOS_POR_EJEMPLO = 5          # = config.TOP_K del RAG
RANGO_IDS = (2001, 8999)            # 1-1536 es dataset_legal; 9000+ es el eval set

CABECERA = re.compile(r"^#\s*Categoria:\s*(?P<nombre>.+?)\s*$", re.MULTILINE)
BLOQUE = re.compile(r"^##\s*(?P<id>\d+)\s*$(?P<cuerpo>.*?)(?=^##\s*\d+\s*$|\Z)", re.MULTILINE | re.DOTALL)


@dataclass
class Especificacion:
    id: int
    categoria: str
    modo: str
    respuesta: str
    base: int | None = None
    pregunta: str = ""
    fuentes: list[tuple[str, str]] = field(default_factory=list)   # (IDENTIFIER, articulo)
    # Solo B2 con REGLA_B2_V3: los articulos que SI responderian la pregunta y
    # que por eso hay que retirar del contexto. Sin esta declaracion no se
    # puede comprobar que no se cuele evidencia suficiente, porque no se sabe
    # cual seria. Ver `fragmentos_para`.
    excluir: list[tuple[str, str]] = field(default_factory=list)   # (IDENTIFIER, articulo)


# --------------------------------------------------------------------------
# Lectura de las fuentes
# --------------------------------------------------------------------------

def _campos(cuerpo: str) -> dict[str, str]:
    """Campos `clave: valor` de un bloque. P y R pueden ocupar varias lineas:
    van hasta el siguiente campo."""
    claves = list(re.finditer(r"^(modo|base|fuentes|excluir|P|R):", cuerpo, re.MULTILINE))
    salida = {}
    for i, m in enumerate(claves):
        fin = claves[i + 1].start() if i + 1 < len(claves) else len(cuerpo)
        salida[m.group(1)] = " ".join(cuerpo[m.end():fin].split())
    return salida


def parsear_fuente(path: Path) -> list[Especificacion]:
    texto = path.read_text(encoding="utf-8")
    cabecera = CABECERA.search(texto)
    if not cabecera:
        raise SystemExit(f"{path.name}: falta la linea '# Categoria: <nombre>'")
    categoria = cabecera.group("nombre").strip()
    salida = []
    for m in BLOQUE.finditer(texto):
        c = _campos(m.group("cuerpo"))
        id_ = int(m.group("id"))
        if c.get("modo") not in MODOS:
            raise SystemExit(f"{path.name} {id_}: modo {c.get('modo')!r} no esta en {MODOS}")
        if not c.get("R"):
            raise SystemExit(f"{path.name} {id_}: falta R")
        def _articulos(campo: str) -> list[tuple[str, str]]:
            salida = []
            for parte in filter(None, (p.strip() for p in c.get(campo, "").split(";"))):
                if ":" not in parte:
                    raise SystemExit(f"{path.name} {id_}: {campo} {parte!r} sin ':articulo'")
                ident, art = parte.rsplit(":", 1)
                salida.append((ident.strip(), art.strip()))
            return salida

        salida.append(Especificacion(
            id=id_, categoria=categoria, modo=c["modo"], respuesta=c["R"],
            base=int(c["base"]) if c.get("base") else None, pregunta=c.get("P", ""),
            fuentes=_articulos("fuentes"), excluir=_articulos("excluir"),
        ))
    if not salida:
        raise SystemExit(f"{path.name}: no hay ningun ejemplo '## <id>'")
    return salida


def cargar_especificaciones(directorio: Path = SOURCE_DIR) -> list[Especificacion]:
    todas = []
    for p in sorted(directorio.glob("*.md")):
        primera = p.read_text(encoding="utf-8").lstrip().splitlines()[:1]
        if primera and CABECERA.match(primera[0]):
            todas.extend(parsear_fuente(p))
    return todas


# --------------------------------------------------------------------------
# Corpus: fragmentos tal como los vera el modelo
# --------------------------------------------------------------------------

@dataclass
class Corpus:
    resultados: list           # SearchResult, uno por chunk, en orden
    por_articulo: dict         # (IDENTIFIER, articulo) -> [indices]
    doc_de_identifier: dict    # IDENTIFIER -> doc_id
    categorias_de_doc: dict    # doc_id -> set de categorias (TRANSVERSAL incluido)
    bm25: object


@lru_cache(maxsize=1)
def cargar_corpus() -> Corpus:
    """Ingesta y chunkea el corpus en alcance (sin embeddings) y arma el BM25."""
    from tools.rag import chunk, corpus, ingest
    from tools.rag.embed_store import chunk_to_metadata, metadata_to_result
    from tools.rag.hybrid import BM25Index

    manifiesto = corpus.to_ingest_manifest()
    docs = ingest.ingest_corpus(manifiesto)
    chunks = chunk.chunk_corpus([d.__dict__ for d in docs])
    metadata = [chunk_to_metadata(c) for c in chunks]
    resultados = [metadata_to_result(m, 0.0) for m in metadata]

    doc_de_identifier = {}
    for norma in corpus.NORMAS_EN_ALCANCE:
        ident = ingest.read_frontmatter(norma.path)["identifier"]
        doc_de_identifier[ident] = norma.path.stem
    ident_de_doc = {v: k for k, v in doc_de_identifier.items()}
    categorias_de_doc = {n.path.stem: set(n.categorias) for n in corpus.NORMAS_EN_ALCANCE}

    por_articulo: dict = {}
    for i, r in enumerate(resultados):
        ident = ident_de_doc[r.doc_id]
        for art in r.articulos_incluidos:
            por_articulo.setdefault((ident, art), []).append(i)
    return Corpus(resultados, por_articulo, doc_de_identifier, categorias_de_doc, BM25Index(metadata))


class Buscador:
    """La busqueda del sistema, para armar contextos: candidatos(pregunta, n)
    devuelve SearchResult en orden. Por defecto BM25 + enrutador sobre el corpus
    chunkeado (local, sin modelos); con un store FAISS, retrieve() de produccion."""

    def __init__(self, c: "Corpus", store=None):
        self.c = c
        self.store = store
        from tools.rag import config as _c
        _enr = "+enrutador" if _c.USE_ENRUTADOR else ""
        self.nombre = ("e5+faiss" if store is not None else "bm25") + _enr

    def candidatos(self, pregunta: str, n: int) -> list:
        from tools.rag import config
        from tools.rag.enrutador import enrutador_por_defecto, priorizar

        if self.store is not None:
            from tools.rag.retrieve import retrieve

            # La bandera, no True fijo: con el enrutador fijo aqui el dataset se
            # construia siempre con el, aunque produccion lo tuviera apagado, y
            # se entrenaria sobre un contexto que el sistema nunca arma.
            return retrieve(pregunta, self.store, top_k=n, min_score=None,
                            use_router=config.USE_ENRUTADOR)
        res = self.c.bm25.search(pregunta, config.ENRUTADOR_POOL)
        return priorizar(res, enrutador_por_defecto().normas(pregunta))[:n]


# Distancia de numero de articulo, dentro de la misma norma, a partir de la cual
# un articulo deja de considerarse continuacion del que se retiro. El 2 no es
# arbitrario: viene de dos casos documentados en el dictamen del gold aprobado
# el 2026-10-10. El art. 144 de la Ley 769 "aplica cuando no hay conciliacion
# tras danos materiales (viene del 143)", y de la Ley 2220 "los arts. 67, 68, 70
# y 71 son los que resuelven el requisito de procedibilidad". En los dos, un
# articulo vecino responde lo que responde el retirado.
CONTIGUO_MAX = 2

REGLA_B2_V2 = "v2"   # historica: fuera la categoria entera. Se conserva para reproducir.
REGLA_B2_V3 = "v3"   # corregida: misma categoria, sin el articulo oraculo.
REGLAS_B2 = (REGLA_B2_V2, REGLA_B2_V3)


def _oraculos_de(pares, c: Corpus, quien: str, id_: int) -> list[str]:
    """chunk_ids de los articulos declarados en `pares`, en orden."""
    chunks: list[str] = []
    for ident, art in pares:
        idx = c.por_articulo.get((ident, art))
        if not idx:
            raise SystemExit(f"{id_}: el corpus no tiene {ident} articulo {art} ({quien})")
        for i in idx:
            cid = c.resultados[i].chunk_id
            if cid not in chunks:
                chunks.append(cid)
    return chunks


def riesgo_de_suficiencia_indirecta(fragmentos, excluidos_doc_art: set[str],
                                    capitulos_oraculo: dict | None = None) -> list[str]:
    """Fragmentos que pueden responder aunque no sean el articulo retirado.

    **Tres niveles, y la diferencia decide que se hace con el ejemplo:**

    - `FUGA_DIRECTA`: el contexto trae uno de los articulos declarados como los
      que SI responden. Eso no es un B2: es ensenar a abstenerse con la
      respuesta delante. **Descarta el ejemplo.**
    - `MISMO_CAPITULO`: otro articulo de la misma norma y del **mismo capitulo**
      que el oraculo. Es el riesgo real de suficiencia indirecta: los articulos
      de un capitulo regulan la misma materia. Paso en el caso 4006, donde se
      retiraron los articulos 139 y 142 del Codigo de la Infancia y el contexto
      trajo el 143 y el 149, del mismo capitulo sobre responsabilidad penal
      adolescente. **Exige revision juridica.**
    - `MISMA_NORMA`: otro articulo de la misma norma, en **otro capitulo**. Una
      ley larga regula muchas cosas: el Codigo Civil trae arriendo, sucesiones y
      servidumbres. Es el caso esperado y deseado -- es lo que el enrutador real
      devuelve -- y se registra sin bloquear.

    Sin `capitulos_oraculo` no se puede distinguir los dos ultimos y todo lo de
    la misma norma se reporta como `MISMA_NORMA`, que es el nivel conservador
    para leer pero el optimista para bloquear: por eso el llamador debe pasarlo.
    """
    capitulos_oraculo = capitulos_oraculo or {}
    docs_excluidos = {p.split(":", 1)[0] for p in excluidos_doc_art}
    nums_oraculo = {}
    for par in excluidos_doc_art:
        doc, art = par.split(":", 1)
        m = re.match(r"\d+", art)
        if m:
            nums_oraculo.setdefault(doc, set()).add(int(m.group()))
    avisos = []
    for f in fragmentos:
        for art in (f.articulos_incluidos or ()):
            if f"{f.doc_id}:{art}" in excluidos_doc_art:
                avisos.append(f"FUGA_DIRECTA {f.doc_id}:{art}")
    if avisos:
        return sorted(set(avisos))
    for f in fragmentos:
        if f.doc_id not in docs_excluidos:
            continue
        cap = (getattr(f, "capitulo", "") or "").strip()
        esperados = capitulos_oraculo.get(f.doc_id) or set()
        contiguo = False
        for a in (f.articulos_incluidos or ()):
            m = re.match(r"\d+", str(a))
            if m and any(abs(int(m.group()) - n) <= CONTIGUO_MAX
                         for n in nums_oraculo.get(f.doc_id, ())):
                contiguo = True
        if contiguo:
            avisos.append(f"CONTIGUO_AL_ORACULO {f.doc_id}")
        elif cap and esperados and cap in esperados:
            avisos.append(f"MISMO_CAPITULO {f.doc_id} :: {cap}")
        else:
            avisos.append(f"MISMA_NORMA {f.doc_id}")
    return sorted(set(avisos))


def capitulos_de(chunk_ids, c: Corpus) -> dict:
    """doc_id -> {capitulos} de los chunks dados. Para el triaje de riesgo."""
    por_id = {r.chunk_id: r for r in c.resultados}
    salida: dict = {}
    for cid in chunk_ids:
        r = por_id.get(cid)
        if r is None:
            continue
        cap = (getattr(r, "capitulo", "") or "").strip()
        if cap:
            salida.setdefault(r.doc_id, set()).add(cap)
    return salida


def fragmentos_para(e: Especificacion, pregunta: str, c: Corpus,
                    buscador: "Buscador | None" = None, regla_b2: str = REGLA_B2_V2):
    """(fragmentos, origen): los FRAGMENTOS_POR_EJEMPLO del contexto, en el orden
    en que los vera el modelo, y de donde salieron.

    B1/B3: lo que trae el buscador. Si el articulo que responde no esta entre los
    primeros, entra en el lugar de uno de ellos, en una posicion sorteada con el
    id como semilla ("busqueda+oraculo"); si esta, el contexto es exactamente el
    de la busqueda ("busqueda").

    B2, y aqui estan las dos reglas:

    `REGLA_B2_V2` (historica). Se retiran las normas de la categoria, las
    transversales, las de las 3 categorias que el enrutador ve probables y los
    codigos generales. **Mide 0 % de contexto de la propia categoria en los 681
    ejemplos B2 del dataset, frente al 98 % de B1.** El modo queda predecible
    desde el contexto -- si no hay nada de tu categoria, abstente -- y eso es un
    atajo que el enrutador real nunca reproduce: ante una pregunta de arriendo el
    enrutador devuelve la Ley 820, articulos equivocados incluidos.

    `REGLA_B2_V3` (corregida). Se conserva lo que devuelve el buscador -- misma
    categoria incluida -- y se retira unicamente el articulo que SI responderia,
    declarado en `excluir`, con todos sus chunks. El contexto se parece entonces
    al contexto irrelevante que puede devolver el enrutador real. Exige la
    declaracion: sin saber que articulo responde no se puede comprobar que no se
    cuele evidencia suficiente.
    """
    from tools.rag.corpus import TRANSVERSAL

    if regla_b2 not in REGLAS_B2:
        raise SystemExit(f"regla_b2 {regla_b2!r} no esta en {REGLAS_B2}")
    buscador = buscador or Buscador(c)
    oraculos: list[str] = []
    for ident, art in e.fuentes:
        idx = c.por_articulo.get((ident, art))
        if not idx:
            raise SystemExit(f"{e.id}: el corpus no tiene {ident} articulo {art}")
        for i in idx:
            cid = c.resultados[i].chunk_id
            if cid not in oraculos:
                oraculos.append(cid)
    if len(oraculos) > FRAGMENTOS_POR_EJEMPLO:
        raise SystemExit(f"{e.id}: las fuentes ocupan {len(oraculos)} fragmentos, mas que el contexto")

    candidatos = buscador.candidatos(pregunta, CANDIDATOS)
    if e.modo == "B2" and regla_b2 == REGLA_B2_V3:
        # Se conserva lo que devuelve el buscador y se retira SOLO el articulo
        # que responde (todos sus chunks). Nada de categorias enteras.
        retirados = set(_oraculos_de(e.excluir, c, "excluir", e.id))
        por_id = {r.chunk_id: r for r in c.resultados}
        arts_retirados = {(por_id[cid].doc_id, a)
                          for cid in retirados for a in (por_id[cid].articulos_incluidos or ())}

        def admisible(r) -> bool:
            if r.chunk_id in retirados:
                return False
            # Otro chunk del MISMO articulo trae el mismo texto partido en dos.
            return not any((r.doc_id, a) in arts_retirados for a in (r.articulos_incluidos or ()))

        elegidos = [r for r in candidatos if admisible(r)][:FRAGMENTOS_POR_EJEMPLO]
        if len(elegidos) < FRAGMENTOS_POR_EJEMPLO:
            vistos = {r.chunk_id for r in elegidos}
            for r in c.bm25.search(pregunta, 300):
                if admisible(r) and r.chunk_id not in vistos:
                    elegidos.append(r)
                    vistos.add(r.chunk_id)
                if len(elegidos) == FRAGMENTOS_POR_EJEMPLO:
                    break
        return elegidos, "busqueda-sin-el-articulo"

    if e.modo == "B2":
        # Ningun fragmento puede responder: fuera las normas de la categoria, las
        # transversales, las de las 3 categorias que el enrutador ve probables
        # y los codigos generales (que regulan de todo: el Civil trae el arriendo
        # de fincas, el CGP cualquier proceso).
        from tools.rag.enrutador import enrutador_por_defecto

        probables = {cat for cat, _ in enrutador_por_defecto().probabilidades(pregunta)[:3]}
        prohibidos = {doc for doc, cats in c.categorias_de_doc.items()
                      if e.categoria in cats or TRANSVERSAL in cats or cats & probables}
        prohibidos |= NORMAS_GENERALES
        elegidos = [r for r in candidatos if r.doc_id not in prohibidos][:FRAGMENTOS_POR_EJEMPLO]
        if len(elegidos) < FRAGMENTOS_POR_EJEMPLO:
            vistos = {r.chunk_id for r in elegidos}
            for r in c.bm25.search(pregunta, 300):
                if r.doc_id not in prohibidos and r.chunk_id not in vistos:
                    elegidos.append(r)
                    vistos.add(r.chunk_id)
                if len(elegidos) == FRAGMENTOS_POR_EJEMPLO:
                    break
        return elegidos, "busqueda-otras-normas"

    por_id = {r.chunk_id: r for r in c.resultados}
    articulos_oraculo = {(por_id[cid].doc_id, a) for cid in oraculos for a in por_id[cid].articulos_incluidos}
    top = candidatos[:FRAGMENTOS_POR_EJEMPLO]
    if all(any(r.chunk_id == cid for r in top) for cid in oraculos):
        return top, "busqueda"
    # Sin el oraculo: los mejores candidatos que no son el oraculo (ni otro chunk
    # del mismo articulo), y el oraculo en una posicion sorteada.
    distractores = [r for r in candidatos
                    if r.chunk_id not in oraculos
                    and not any((r.doc_id, a) in articulos_oraculo for a in r.articulos_incluidos)]
    orden = distractores[: FRAGMENTOS_POR_EJEMPLO - len(oraculos)]
    rng = random.Random(e.id)
    for cid in oraculos:
        orden.insert(rng.randint(0, len(orden)), por_id[cid])
    return orden, "busqueda+oraculo"


# --------------------------------------------------------------------------
# Construccion
# --------------------------------------------------------------------------

def construir(especificaciones: list[Especificacion], registros_m1: list[dict], store=None) -> list[dict]:
    from tools.rag.prompt_template import build_messages

    preguntas_m1 = {r["id"]: r["messages"][1]["content"] for r in registros_m1}
    categorias_m1 = {r["id"]: r["category"] for r in registros_m1}
    c = cargar_corpus()
    buscador = Buscador(c, store)

    salida = []
    for e in especificaciones:
        if e.base is not None:
            if e.base not in preguntas_m1:
                raise SystemExit(f"{e.id}: base {e.base} no existe en dataset_legal.jsonl")
            if categorias_m1[e.base] != e.categoria:
                raise SystemExit(f"{e.id}: base {e.base} es de {categorias_m1[e.base]!r}, no de {e.categoria!r}")
            pregunta = e.pregunta or preguntas_m1[e.base]
        elif e.pregunta:
            pregunta = e.pregunta
        else:
            raise SystemExit(f"{e.id}: sin base ni P")

        if e.modo in ("B1", "B3") and not e.fuentes:
            raise SystemExit(f"{e.id}: {e.modo} sin fuentes")
        if e.modo == "B2" and e.fuentes:
            raise SystemExit(f"{e.id}: B2 no lleva fuentes (ningun fragmento debe servir)")
        fragmentos, origen = fragmentos_para(e, pregunta, c, buscador)
        mensajes = build_messages(pregunta, fragmentos)
        mensajes.append({"role": "assistant", "content": e.respuesta})
        salida.append({
            "id": e.id, "category": e.categoria, "modo": e.modo, "base_id": e.base,
            "pregunta": pregunta,
            "fuentes": [f"{i}:{a}" for i, a in e.fuentes],
            "contexto": [{"cita": f.cita, "doc_id": f.doc_id, "articulos": f.articulos_incluidos,
                          "chunk_id": f.chunk_id} for f in fragmentos],
            "contexto_origen": origen, "buscador": buscador.nombre,
            "messages": mensajes,
        })
    return salida


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="valida sin escribir el JSONL")
    parser.add_argument("--archivo", help="valida solo data/dataset_src_v2/<archivo> (no escribe)")
    parser.add_argument("--indice", action="store_true",
                        help="contexto con el indice FAISS + e5 de artifacts/ (Colab), no con BM25")
    args = parser.parse_args()

    from tools.dataset_v2_quality import analizar, reportar
    from tools.evaluation import dataset

    especificaciones = cargar_especificaciones()
    if args.archivo:
        nombre = Path(args.archivo).name
        especificaciones = parsear_fuente(SOURCE_DIR / nombre)
        args.check = True
    ids = [e.id for e in especificaciones]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        raise SystemExit(f"IDs repetidos: {repetidos[:10]}")
    fuera = [i for i in ids if not RANGO_IDS[0] <= i <= RANGO_IDS[1]]
    if fuera:
        raise SystemExit(f"IDs fuera de {RANGO_IDS}: {fuera[:10]}")

    store = None
    if args.indice:
        from tools.rag import pipeline

        store = pipeline.load_index()
    registros = construir(sorted(especificaciones, key=lambda e: e.id), dataset.load_records(), store)
    fallos = reportar(analizar(registros))
    if fallos:
        print(f"\nNO se escribe el dataset: {len(fallos)} puerta(s) sin pasar -> {', '.join(fallos)}")
        sys.exit(1)
    if args.check:
        print("\n--check: todas las puertas pasan, no se escribio nada.")
        return
    with open(OUTPUT_JSONL, "w", encoding="utf-8", newline="\n") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nEscrito {OUTPUT_JSONL} ({len(registros)} ejemplos)")


if __name__ == "__main__":
    main()
