"""Dataset v3: las dos correcciones de construccion que v2 no tiene.

Lee la base del commit `BASE_REV` -- no del disco, para ser idempotente -- y
escribe `data/dataset.jsonl`. El dataset anterior se conserva en git
(`git show 9c9f5a9:data/dataset.jsonl`), que es donde vive la version: el
proyecto tiene un solo dataset con un solo nombre (commit 42a4316).

Lee `data/dataset.jsonl` de ese commit (v1 + v2 + contrastivo, el
historico) y escribe `data/dataset.jsonl` con su manifiesto. El split
de cada ejemplo se hereda del historico: ninguna pregunta cambia de lado.

## Las dos causas confirmadas que corrige

**1. El contexto de B2 delataba el modo.** Medido sobre `data/dataset.jsonl`:

    B1  391 ejemplos   385 con >=1 fragmento de su propia categoria   98 %
    B3  101 ejemplos   100                                            99 %
    B2  681 ejemplos     0                                             0 %

La regla historica de B2 retira las normas de la categoria, las transversales,
las de las 3 categorias probables y los codigos generales. El resultado es que
**el modo es predecible desde el contexto sin leerlo**: si no hay nada de tu
categoria, abstente. El enrutador real nunca produce eso -- ante una pregunta de
arriendo devuelve la Ley 820, con los articulos equivocados --, asi que el atajo
no sirve en servicio y queda el comportamiento dominante: responder.

v3 usa `REGLA_B2_V3`: se conserva lo que devuelve el buscador, misma categoria
incluida, y se retira unicamente el articulo que SI responderia.

**2. Los 418 contrastivos tenian 11 objetivos distintos y 250 identicos.** El
puntero salia de un diccionario de 12 categorias con un texto por defecto, y las
15 categorias que no estaban en el diccionario cayeron todas en la misma frase.
Un objetivo repetido 250 veces ensena esa cadena, no la conducta.

v3 reparte los **263 punteros escritos a mano** de los B2 originales, que ya
pasaron las puertas de calidad, entre las variantes de su misma categoria. No se
redacta derecho nuevo: se reutiliza texto ya revisado, y cada categoria tiene
entre 8 y 11 punteros propios.

**3. Los 263 B2 escritos a mano tambien se recontextualizan**, y no hace falta
declararles `excluir`. Una version anterior de este docstring decia lo
contrario -- que quedaban con la regla historica a la espera de que alguien
declarara el articulo oraculo caso por caso -- y era un razonamiento equivocado:

Un B2 a mano es una pregunta cuya **respuesta correcta es la frase de escape**,
o sea que el corpus no la responde. Se comprueba en el propio dataset: los 263
tienen `fuentes` vacio y ninguno cita un articulo, y el generador rechaza un B2
que traiga `fuentes`. Si **nada** del corpus responde, **ningun** contexto es
suficiente, y entonces no existe el articulo oraculo que habria que retirar: la
regla v3 se reduce a usar lo que devuelve el buscador.

Medido sobre los ejemplos construidos: los 263 salen con
`contexto_origen = busqueda-sin-el-articulo` y el **84 %** trae un fragmento de
su propia categoria.

## Lo que v3 NO resuelve

El riesgo de que alguna de esas 263 preguntas **si** tenga respuesta en su
categoria y el autor no la viera. No se da por bueno a ciegas: se mide la
afinidad lexica con el mejor fragmento de la propia categoria y las que pasan
de `AFINIDAD_PARA_REVISION` quedan marcadas (28 casos). Es un triaje para
ordenar una cola de revision, no un dictamen: decidir si ese articulo responde
es juicio juridico.

    python -m tools.dataset_v3 --check    # construye y mide, no escribe
    python -m tools.dataset_v3            # escribe data/dataset.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from tools.evaluation import config as config_eval

RAIZ = config_eval.PROJECT_ROOT

# **La base se lee de git, no del archivo en disco.** Es la unica forma de que
# esto sea idempotente: el resultado se escribe en `data/dataset.jsonl`, que es
# tambien el archivo de partida, asi que leer el disco significaria reconstruir
# los contrastivos encima de unos ya reconstruidos. Anclado a un commit, correrlo
# dos veces da el mismo resultado.
#
# Es ademas la convencion del proyecto -- "un solo dataset, un solo nombre, el
# hash en un solo lugar" (commit 42a4316): la version la lleva git, no el nombre
# del archivo. El dataset anterior vive en `git show 9c9f5a9:data/dataset.jsonl`.
BASE_REV = "9c9f5a9"
BASE_PATH = "data/dataset.jsonl"

SALIDA = config_eval.DATASET_PATH
MANIFIESTO = RAIZ / "data" / "dataset_manifiesto.json"

VERSION = "v3"

# Afinidad lexica a partir de la cual un B2 a mano se marca para revision: el
# contexto trae un articulo de su propia categoria muy parecido a la pregunta,
# y conviene que un abogado confirme que no la responde. No esta calibrado --
# es un punto de corte para ordenar una cola de revision, no un dictamen.
AFINIDAD_PARA_REVISION = 0.30


def leer_base() -> list[dict]:
    """El dataset de partida, leido del commit `BASE_REV`.

    Falla ruidosamente si git no responde: construir sobre el archivo en disco
    produciria un dataset distinto cada vez que se corre, y eso es peor que no
    poder construirlo.
    """
    import subprocess

    r = subprocess.run(["git", "show", f"{BASE_REV}:{BASE_PATH}"], cwd=RAIZ,
                       capture_output=True)
    if r.returncode != 0:
        raise SystemExit(
            f"no se pudo leer {BASE_PATH} en {BASE_REV}: {r.stderr.decode(errors='replace')[:200]}")
    return [json.loads(l) for l in r.stdout.decode("utf-8").splitlines() if l.strip()]


def leer(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


# --------------------------------------------------------------------------
# Punteros: de donde sale cada objetivo
# --------------------------------------------------------------------------

def punteros_por_categoria(registros: list[dict]) -> dict[str, list[str]]:
    """Los punteros escritos a mano de los B2 de v2, agrupados por categoria.

    Son el texto que sigue a la frase de escape ("Te sugiero consultar..."). Ya
    pasaron `dataset_v2_quality`: ni rutas incorrectas, ni entidades inventadas,
    ni promesas. Reutilizarlos es preferible a generar frases nuevas, que serian
    derecho sin revisar.
    """
    from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

    pool: dict[str, set[str]] = defaultdict(set)
    for r in registros:
        if r.get("modo") != "B2" or r.get("origen") != "v2":
            continue
        texto = r["messages"][-1]["content"]
        resto = texto[len(RESPUESTA_SIN_CONTEXTO):].lstrip(". ").strip()
        if resto:
            pool[r["category"]].add(resto)
    return {c: sorted(v) for c, v in pool.items()}


def objetivo(categoria: str, orden: int, pool: dict[str, list[str]],
             pregunta: str = "") -> tuple[str, str]:
    """(objetivo, nota): la frase de escape exacta mas un puntero de la categoria.

    `orden` es la posicion de la variante dentro de su categoria, asi que el
    reparto es round-robin y deterministico: misma entrada, mismo dataset.
    El prefijo tiene que ser identico al de los B2 a mano --
    `es_valvula_de_escape` y el juez lo buscan tal cual.

    **Una pregunta de urgencia no recibe objetivo mecanico.** Se devuelve
    `("", "URGENCIA_REQUIERE_OBJETIVO_A_MANO")` y el llamador la excluye.

    Por que, habiendo una via mecanica que pasa la puerta. Restringir el puntero
    a los que cumplen `AYUDA_INMEDIATA` hace pasar la puerta `urgencia sin ayuda
    inmediata` en los 11 casos, y aun asi los objetivos salen mal. Medido sobre
    esos 11: a *"estoy en una situacion de violencia intrafamiliar y necesito
    salir del contrato de arriendo"* le toca *"toma fotos del dano, avisa por
    escrito al arrendador y a la administracion del edificio"*; a *"necesito que
    valoren mis golpes"*, *"pregunta en la Fiscalia como reactivar tu caso".* El
    puntero es institucionalmente real y de la categoria correcta -- por eso el
    regex lo acepta -- pero es ajeno a la situacion.

    Un objetivo que se abstiene y encamina a donde no corresponde, en los casos
    donde la linea base de seguridad es **0/5**, ensena la abstencion peligrosa
    con una capa de ayuda aparente. Es peor que no tener el ejemplo, por la misma
    razon que `verificacion.py` documenta al retirar la heuristica lexica de
    atribucion: dar falsa tranquilidad es peor que no tener la comprobacion.

    Son 16 ejemplos de 435 candidatos. El coste en masa de entrenamiento es
    despreciable y el riesgo que se evita es el peor del dataset. Los 16 quedan
    listados en el manifiesto para que se les escriba el objetivo a mano, que es
    trabajo juridico: decidir cual es la orientacion segura en cada situacion.

    **Que patron reconoce la urgencia.** Se usa `URGENCIA_AMPLIA`, no el
    `URGENCIA` de `dataset_quality`, porque ese reconoce **1 de los 5** casos de
    urgencia declarados en el eval set: le escapan "esta detenido", "no dejan
    salir a mi mama", "estoy en la audiencia ahora mismo" y "el carro se esta
    yendo". Con el estrecho se excluian 11 variantes y con el ampliado 16.

    El patron estrecho **no se toca**: lo usa la puerta del dataset historico y
    cambiarlo moveria un criterio ya aplicado. Y `URGENCIA_AMPLIA` se escribio
    mirando esos 5 casos, asi que su 5/5 es **por construccion** y no evidencia
    de que reconozca una urgencia nueva.
    """
    from tools.evaluation.seguridad_urgencias_reglas import URGENCIA_AMPLIA
    from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

    opciones = pool.get(categoria)
    if not opciones:
        raise SystemExit(f"sin punteros para la categoria {categoria!r}")
    if URGENCIA_AMPLIA.search(pregunta or ""):
        return "", "URGENCIA_REQUIERE_OBJETIVO_A_MANO"
    return f"{RESPUESTA_SIN_CONTEXTO}. {opciones[orden % len(opciones)]}", ""


# --------------------------------------------------------------------------
# Construccion
# --------------------------------------------------------------------------

def rehacer_contrastivos(registros: list[dict], store=None) -> tuple[list[dict], list[dict]]:
    """Las variantes B2 de nuevo: regla v3 para el contexto y puntero propio.

    El oraculo que hay que retirar no se inventa: es el campo `fuentes` del
    ejemplo B1/B3 original, el articulo que de verdad responde esa pregunta.
    Por eso los contrastivos SI se pueden corregir hoy y los B2 a mano no.
    """
    from tools.dataset_contrastivo import _fuentes_como_doc, candidatas
    from tools.dataset_v2 import (REGLA_B2_V3, Buscador, Especificacion, _oraculos_de,
                                  capitulos_de, cargar_corpus, fragmentos_para,
                                  riesgo_de_suficiencia_indirecta)
    from tools.rag.prompt_template import build_messages

    c = cargar_corpus()
    buscador = Buscador(c, store)
    pool = punteros_por_categoria(registros)
    por_id = {r["id"]: r for r in registros}

    # El id de cada variante se conserva: una variante nueva del mismo original
    # mantiene su identidad entre versiones y el diff es legible.
    previas = {r["par_de"]: r["id"] for r in registros
               if r.get("origen") == "contrastivo" and r.get("par_de") in por_id}
    siguiente = max([r["id"] for r in registros if r.get("origen") == "contrastivo"] or [6000]) + 1

    salida: list[dict] = []
    descartadas: list[dict] = []
    orden_cat: Counter = Counter()
    for r in candidatas(registros):
        fuentes = [tuple(f.rsplit(":", 1)) for f in (r.get("fuentes") or ()) if ":" in f]
        if not fuentes:
            descartadas.append({"original": r["id"], "razon": "SIN_FUENTES_EN_EL_ORIGINAL",
                                "categoria": r["category"], "pregunta": r["pregunta"]})
            continue
        e = Especificacion(
            id=previas.get(r["id"]) or siguiente,
            categoria=r["category"], modo="B2", respuesta="",
            base=r.get("base_id"), pregunta=r["pregunta"],
            fuentes=[], excluir=[(i.strip(), a.strip()) for i, a in fuentes],
        )
        if e.id == siguiente:
            siguiente += 1
        fragmentos, origen = fragmentos_para(e, e.pregunta, c, buscador, regla_b2=REGLA_B2_V3)

        # Comprobacion de que no se cuela evidencia suficiente por otro
        # fragmento. FUGA_DIRECTA descarta; MISMA_NORMA se registra para
        # revision -- una ley larga regula muchas cosas y no es automaticamente
        # suficiente, pero tampoco descartable sin leerlo.
        excluidos = set(_fuentes_como_doc(r.get("fuentes") or (), c))
        caps = capitulos_de(_oraculos_de(e.excluir, c, "excluir", e.id), c)
        avisos = riesgo_de_suficiencia_indirecta(fragmentos, excluidos, caps)
        # FUGA_DIRECTA: el contexto trae el articulo que responde. Descarta.
        # CONTIGUO_AL_ORACULO: trae un articulo vecino de la misma norma, que en
        # los dos casos documentados del dictamen del gold responde lo mismo que
        # el retirado (Ley 769 143/144; Ley 2220 67/68/70/71). Tambien descarta:
        # no se puede resolver sin criterio juridico, y retirar la variante
        # cuesta un ejemplo mientras dejarla ensena a abstenerse con la
        # respuesta delante.
        grave = [a for a in avisos
                 if a.startswith(("FUGA_DIRECTA", "CONTIGUO_AL_ORACULO"))]
        if grave:
            descartadas.append({"original": r["id"], "razon": grave[0].split()[0],
                                "categoria": r["category"], "pregunta": r["pregunta"],
                                "detalle": grave})
            continue

        e.respuesta, nota = objetivo(e.categoria, orden_cat[e.categoria], pool, e.pregunta)
        if not e.respuesta:
            descartadas.append({"original": r["id"], "razon": nota,
                                "categoria": r["category"], "pregunta": r["pregunta"]})
            continue
        orden_cat[e.categoria] += 1
        mensajes = build_messages(e.pregunta, fragmentos)
        mensajes.append({"role": "assistant", "content": e.respuesta})
        salida.append({
            "id": e.id, "category": e.categoria, "modo": "B2", "base_id": e.base,
            "pregunta": e.pregunta, "fuentes": [],
            "contexto": [{"cita": f.cita, "doc_id": f.doc_id,
                          "articulos": f.articulos_incluidos, "chunk_id": f.chunk_id}
                         for f in fragmentos],
            "contexto_origen": origen, "buscador": buscador.nombre,
            "messages": mensajes,
            "origen": "contrastivo", "split": "train",
            "fuentes_originales": sorted(excluidos),
            "par_de": r["id"],
            "revision_suficiencia": avisos,
            "nota_objetivo": nota,
            "version_contexto": VERSION,
        })
    return salida, descartadas


def rehacer_b2_a_mano(registros: list[dict], store=None) -> tuple[list[dict], list[dict]]:
    """Los 263 B2 escritos a mano, con contexto de su propia categoria.

    **Por que no hace falta declarar `excluir` en estos.** Un B2 a mano es una
    pregunta cuya respuesta correcta *es* la frase de escape: el corpus no la
    responde. Se comprueba en el dataset -- los 263 tienen `fuentes` vacio y
    ninguno cita un articulo -- y lo impone el generador, que rechaza un B2 con
    `fuentes`. Si **nada** del corpus responde, **ningun** contexto es
    suficiente, y entonces no hay articulo oraculo que retirar: la regla v3 se
    reduce a usar lo que devuelve el buscador.

    Eso vuelve el ejemplo mucho mas realista. El enrutador, ante una pregunta de
    arriendo, devuelve la Ley 820: articulos de la materia correcta que no
    responden *esa* pregunta. Es exactamente la situacion en la que el modelo
    tiene que abstenerse, y es la que el contexto historico -- normas de otras
    categorias -- nunca le mostro.

    **El riesgo que queda, y como se acota.** Que alguna de esas 263 preguntas si
    tenga respuesta en su categoria y el autor no la viera. No se da por bueno a
    ciegas: se mide la afinidad lexica del mejor fragmento de la propia categoria
    y las que pasan de `AFINIDAD_PARA_REVISION` quedan marcadas. Es un triaje,
    no un dictamen: decidir si ese articulo responde es juicio juridico.
    """
    from tools.dataset_v2 import REGLA_B2_V3, Buscador, Especificacion, cargar_corpus, fragmentos_para
    from tools.evaluation.seguridad_urgencias_reglas import URGENCIA_AMPLIA
    from tools.evaluation.similitud import IndiceTfidf
    from tools.rag.corpus import TRANSVERSAL
    from tools.rag.prompt_template import build_messages

    c = cargar_corpus()
    buscador = Buscador(c, store)
    from tools.rag.corpus import NORMAS_EN_ALCANCE
    cats_de_doc = {n.path.stem: set(n.categorias) for n in NORMAS_EN_ALCANCE}

    salida, descartadas = [], []
    for r in registros:
        if r.get("modo") != "B2" or r.get("origen") != "v2":
            continue
        # Un B2 cuya pregunta es una urgencia no puede quedarse con un objetivo
        # que solo se abstiene: es la abstencion peligrosa. Se revisa aparte.
        if URGENCIA_AMPLIA.search(r.get("pregunta") or ""):
            from tools.dataset_quality import AYUDA_INMEDIATA

            if not AYUDA_INMEDIATA.search(r["messages"][-1]["content"]):
                descartadas.append({"original": r["id"],
                                    "razon": "B2_URGENCIA_SIN_AYUDA_INMEDIATA",
                                    "categoria": r["category"], "pregunta": r["pregunta"]})
                continue
        e = Especificacion(id=r["id"], categoria=r["category"], modo="B2",
                           respuesta=r["messages"][-1]["content"],
                           base=r.get("base_id"), pregunta=r["pregunta"],
                           fuentes=[], excluir=[])
        fragmentos, origen = fragmentos_para(e, e.pregunta, c, buscador, regla_b2=REGLA_B2_V3)

        # Triaje: ¿algun fragmento de la PROPIA categoria se parece mucho a la
        # pregunta? Si si, conviene que un abogado confirme que no la responde.
        propios = [f for f in fragmentos
                   if (cats_de_doc.get(f.doc_id, set()) - {TRANSVERSAL}) & {e.categoria}]
        afinidad = 0.0
        if propios:
            textos = [(f.cita or "") + " " + (f.text or "") for f in propios]
            afinidad = max(IndiceTfidf(textos).similitudes(e.pregunta) or [0.0])
        nuevo = dict(r)
        nuevo.update({
            "contexto": [{"cita": f.cita, "doc_id": f.doc_id,
                          "articulos": f.articulos_incluidos, "chunk_id": f.chunk_id}
                         for f in fragmentos],
            "contexto_origen": origen,
            "buscador": buscador.nombre,
            "messages": build_messages(e.pregunta, fragmentos) + [
                {"role": "assistant", "content": e.respuesta}],
            "afinidad_propia_categoria": round(afinidad, 3),
            "revision_suficiencia": (["AFINIDAD_ALTA_REVISAR"]
                                     if afinidad >= AFINIDAD_PARA_REVISION else []),
            "version_contexto": VERSION,
        })
        salida.append(nuevo)
    return salida, descartadas


def construir(store=None) -> tuple[list[dict], list[dict]]:
    """El dataset v3 completo: contrastivos rehechos y B2 a mano recontextualizados."""
    historico = leer_base()
    contrastivos, desc_c = rehacer_contrastivos(historico, store)
    b2, desc_b2 = rehacer_b2_a_mano(historico, store)
    rehechos = {r["id"] for r in b2}
    conservados = [r for r in historico
                   if r.get("origen") != "contrastivo" and r["id"] not in rehechos
                   and not (r.get("modo") == "B2" and r.get("origen") == "v2"
                            and r["id"] in {d["original"] for d in desc_b2})]
    todo = conservados + b2 + sorted(contrastivos, key=lambda r: r["id"])
    return sorted(todo, key=lambda r: r["id"]), desc_c + desc_b2


# --------------------------------------------------------------------------
# Manifiesto, huellas y controles de fuga
# --------------------------------------------------------------------------

def huella(registros: list[dict]) -> str:
    """sha256 del contenido canonico, con salto LF. Portable entre sistemas."""
    h = hashlib.sha256()
    for r in registros:
        h.update(json.dumps(r, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()[:16]


def composicion(registros: list[dict]) -> dict:
    tr = [r for r in registros if r.get("split") == "train"]
    val = [r for r in registros if r.get("split") == "val"]

    def masa(rs):
        return sum(len(r["messages"][-1]["content"]) for r in rs)

    total_masa = masa(tr) or 1
    por_modo = {}
    for m in ("B1", "B2", "B3", None):
        sub = [r for r in tr if r.get("modo") == m]
        if sub:
            por_modo[m or "sin contexto (v1)"] = {
                "ejemplos": len(sub),
                "pct_ejemplos": round(100 * len(sub) / len(tr), 1),
                "pct_masa_tokens": round(100 * masa(sub) / total_masa, 1),
            }
    objetivos = Counter(r["messages"][-1]["content"]
                        for r in registros if r.get("origen") == "contrastivo")
    riesgo = Counter(a.split()[0] for r in registros
                     for a in (r.get("revision_suficiencia") or []))
    return {
        "riesgo_suficiencia_indirecta": dict(riesgo),
        "total": len(registros),
        "train": len(tr), "val": len(val),
        "por_origen": dict(Counter(r.get("origen") for r in registros)),
        "por_modo_en_train": por_modo,
        "contrastivos": {
            "n": sum(objetivos.values()),
            "objetivos_distintos": len(objetivos),
            "objetivo_mas_repetido": objetivos.most_common(1)[0][1] if objetivos else 0,
        },
    }


def control_de_fuga(registros: list[dict]) -> dict:
    """Las tres fugas que importan, cada una medida aparte.

    1. Una pregunta de `val` que aparezca tambien en `train`.
    2. Una pregunta de entrenamiento igual o parecida a una del eval set
       reservado. Es la fuga grave: contamina la medicion final.
    3. Una variante contrastiva cuyo original este en `val`.
    """
    from tools.evaluation import eval_set

    def preg(r):
        return (r.get("pregunta") or "").strip()

    tr = [r for r in registros if r.get("split") == "train"]
    val = [r for r in registros if r.get("split") == "val"]
    preguntas_val = {preg(r) for r in val if preg(r)}
    cruce = sorted({r["id"] for r in tr if preg(r) and preg(r) in preguntas_val})

    ev = eval_set.load_eval_set()
    solo = [{"messages": [{}, {"content": preg(r)}]} for r in tr if preg(r)]
    iguales = eval_set.solapamiento(ev, solo, [])["en_train"]

    bases_val = {r.get("base_id") for r in val}
    variantes = sorted({r["id"] for r in registros
                        if r.get("origen") == "contrastivo" and r.get("base_id") in bases_val
                        and r.get("base_id") is not None})
    return {
        "train_val_misma_pregunta": cruce,
        "train_igual_a_eval_set": sorted(iguales),
        "contrastivo_de_una_base_en_val": variantes,
    }


def manifiesto(registros: list[dict], descartadas: list[dict]) -> dict:
    import subprocess

    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ,
                                capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        commit = "desconocido"
    return {
        "version": VERSION,
        "derivado_de": {"archivo": BASE_PATH, "revision": BASE_REV,
                        "huella": huella(leer_base())},
        "commit": commit,
        "correcciones": [
            "contexto B2 de los contrastivos con REGLA_B2_V3 (misma categoria, sin el articulo oraculo)",
            "contexto de los 263 B2 escritos a mano con REGLA_B2_V3, sin `excluir`: su respuesta "
            "correcta ES la frase de escape, o sea que el corpus no los responde, y entonces "
            "ningun contexto es suficiente y no hay articulo oraculo que retirar",
            "objetivos de los contrastivos repartidos entre los punteros escritos a mano de su categoria",
            "variantes descartadas cuando el contexto traia un articulo contiguo al retirado",
            "variantes de urgencia no generadas: un escape sin encaminar es una abstencion peligrosa",
        ],
        "sin_corregir": [
            "28 B2 a mano con afinidad alta a un fragmento de su propia categoria: marcados "
            "AFINIDAD_ALTA_REVISAR por si alguno si tiene respuesta en el corpus",
            "71 variantes con un articulo del mismo capitulo que el retirado, no contiguo: "
            "riesgo residual documentado",
        ],
        "huella": huella(registros),
        "composicion": composicion(registros),
        "control_de_fuga": control_de_fuga(registros),
        "variantes_descartadas": descartadas,
    }


# --------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", action="store_true", help="construye y mide, no escribe")
    p.add_argument("--indice", action="store_true", help="contexto con FAISS + e5 (Colab)")
    args = p.parse_args(argv)

    store = None
    if args.indice:
        from tools.rag import pipeline

        store = pipeline.load_index()

    registros, descartadas = construir(store)
    m = manifiesto(registros, descartadas)

    print(f"DATASET v3   huella {m['huella']}   derivado de {m['derivado_de']['huella']}")
    print()
    c = m["composicion"]
    print(f"  total {c['total']}   train {c['train']}   val {c['val']}")
    print(f"  por origen: {c['por_origen']}")
    print()
    print(f"  {'modo':22}{'ejemplos':>10}{'% ejem':>9}{'% masa':>9}")
    for k, v in c["por_modo_en_train"].items():
        print(f"  {k:22}{v['ejemplos']:>10}{v['pct_ejemplos']:>9}{v['pct_masa_tokens']:>9}")
    print()
    ct = c["contrastivos"]
    print(f"  contrastivos: {ct['n']}   objetivos distintos: {ct['objetivos_distintos']}"
          f"   el mas repetido: {ct['objetivo_mas_repetido']}")
    if descartadas:
        from collections import Counter as _C
        print(f"  variantes NO generadas: {len(descartadas)}  "
              f"{dict(_C(d[chr(114)+chr(97)+chr(122)+chr(111)+chr(110)].split()[0] for d in descartadas))}")
    print(f"  riesgo de suficiencia indirecta: {c['riesgo_suficiencia_indirecta']}")
    print("     MISMO_CAPITULO exige revision juridica; MISMA_NORMA es el caso esperado")
    print()
    print("CONTROL DE FUGA")
    fallo = False
    for k, v in m["control_de_fuga"].items():
        print(f"  [{'OK  ' if not v else 'FALLA'}] {k}: {len(v)}")
        if v:
            fallo = True
            print(f"        {v[:10]}")
    if args.check:
        print("\n--check: no se escribio nada.")
        return 1 if fallo else 0
    if fallo:
        print("\nNO se escribe: hay fuga.")
        return 1
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    MANIFIESTO.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
    print(f"\nEscrito {SALIDA.name} ({len(registros)}) y {MANIFIESTO.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
