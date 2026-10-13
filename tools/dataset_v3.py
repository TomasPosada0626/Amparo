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

v3 repartia los punteros escritos a mano de los B2 de entrenamiento entre las
variantes de su categoria. **Era un defecto (H22, 2026-10-13)**: cada puntero se
escribio para OTRA pregunta (0 de 289 propios, 113 con una autoridad concreta), y
a *"me cortaron el agua sin avisarme"* le tocaba *"pide la cancelacion por
escrito al operador... queja ante la Superintendencia de Industria y Comercio"*.
6 de los 9 fallos criticos de v1 reevaluado estan en ese puntero.

**v4 usa punteros que valen para cualquier pregunta** (`PUNTEROS_GENERICOS`): un
consultorio juridico universitario o la Personeria, que orientan en cualquier
materia. La unica excepcion es violencia intrafamiliar, que conserva el puntero
de categoria que ya estaba en el repo (`dataset_contrastivo.DONDE_CONSULTAR`):
la Comisaria de Familia es la via de toda esa categoria, y dejarla sin la linea
de emergencia seria la abstencion peligrosa que `objetivo` documenta.

**3. Los B2 escritos a mano de ENTRENAMIENTO tambien se recontextualizan** (228
de los 263; los 35 de validacion no se tocan), y no hace falta
declararles `excluir`. Una version anterior de este docstring decia lo
contrario -- que quedaban con la regla historica a la espera de que alguien
declarara el articulo oraculo caso por caso -- y era un razonamiento equivocado:

Un B2 a mano es una pregunta cuya **respuesta correcta es la frase de escape**,
o sea que el corpus no la responde. Se comprueba en el propio dataset: los 263
tienen `fuentes` vacio y ninguno cita un articulo, y el generador rechaza un B2
que traiga `fuentes`. Si **nada** del corpus responde, **ningun** contexto es
suficiente, y entonces no existe el articulo oraculo que habria que retirar: la
regla v3 se reduce a usar lo que devuelve el buscador.

**4. Los B2 de validacion no se reconstruyen.** Conservan el contenido de la
base `9c9f5a9`, el mismo sobre el que se evaluaron v1 y v2 y se adjudicaron. Una
version anterior los reconstruia (defecto H3).

**5. Todo contexto sale del buscador de produccion: e5 + FAISS + enrutador.**
Una version anterior se construyo en local con BM25 (defecto H4): todos los B2
quedaron con BM25 y todos los B1/B3 con e5, y el estilo del contexto podia
delatar el modo. Por eso **escribir exige `--indice`**.

Medido sobre los ejemplos construidos: la ventaja del atajo "si no hay nada de
mi categoria, abstente" es de **-3,6 puntos en entrenamiento** (antes +39,2).
En validacion es +32,0, porque los 35 B2 conservan su contexto historico, de
otras categorias: por eso la validacion no puede detectar el atajo y hace falta
la prueba de los 4 escenarios.

## Lo que v3 NO resuelve

El riesgo de que alguna de esas preguntas **si** tenga respuesta en su
categoria y el autor no la viera. No se da por bueno a ciegas: se mide la
afinidad lexica con el mejor fragmento de la propia categoria y las que pasan
de `AFINIDAD_PARA_REVISION` quedan marcadas (ver el manifiesto). Es un triaje para
ordenar una cola de revision, no un dictamen: decidir si ese articulo responde
es juicio juridico.

    python -m tools.dataset_v3 --check --indice   # construye y mide, no escribe
    python -m tools.dataset_v3 --indice           # escribe data/dataset.jsonl

`--indice` necesita el indice FAISS en `artifacts/` y e5; en local corre con el
`.venv` del repo, que tiene faiss.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
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

VERSION = "v3"            # version del CONTEXTO: los contextos no cambian en v4
VERSION_DATASET = "v4"    # H22 (punteros de los contrastivos) y H25 (4 B2 a mano)

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

# A donde mandar a la persona cuando el contexto no alcanza, en una variante
# contrastiva. Tiene que valer para CUALQUIER pregunta: la variante no tiene un
# puntero escrito para ella, y prestarle el de otra pregunta fue el defecto H22.
# Un consultorio juridico universitario y la Personeria orientan en cualquier
# materia; ninguno de los dos es una autoridad que pueda ser la equivocada.
PUNTEROS_GENERICOS = (
    "Te sugiero consultar un consultorio jurídico universitario.",
    "Puedes pedir orientación gratuita en un consultorio jurídico universitario o "
    "en la Personería de tu municipio.",
)

# Categorias cuya via es la misma para todas sus preguntas, y en las que un
# puntero generico seria peor. Texto tomado de `dataset_contrastivo.DONDE_CONSULTAR`.
PUNTERO_POR_CATEGORIA = {
    "Violencia intrafamiliar y medidas de proteccion":
        "Acude a la Comisaría de Familia; si hay riesgo inmediato, llama a la Línea 155.",
}


def objetivo(categoria: str, orden: int, pregunta: str = "") -> tuple[str, str]:
    """(objetivo, nota): la frase de escape exacta mas un puntero que vale para
    ESA pregunta, sea cual sea (H22).

    `orden` es la posicion de la variante dentro de su categoria: alterna los
    punteros genericos de forma deterministica, misma entrada, mismo dataset.
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

    if URGENCIA_AMPLIA.search(pregunta or ""):
        return "", "URGENCIA_REQUIERE_OBJETIVO_A_MANO"
    puntero = PUNTERO_POR_CATEGORIA.get(
        categoria, PUNTEROS_GENERICOS[orden % len(PUNTEROS_GENERICOS)])
    return f"{RESPUESTA_SIN_CONTEXTO}. {puntero}", ""


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

        e.respuesta, nota = objetivo(e.categoria, orden_cat[e.categoria], e.pregunta)
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


# Punteros de B2 escritos a mano que mandaban a una autoridad fuera de su
# competencia (H25, 2026-10-13). De los 36 que nombran una Superintendencia o una
# Secretaria, 32 son correctos para su pregunta y se conservan: orientar con
# conocimiento general es parte del diseno de B2. Estos cuatro reproducen el
# patron de los fallos criticos de v1 reevaluado:
#   4718, 4719  internet: la SIC es correcta, pero en la categoria "servicios
#               publicos" ensenaban "servicios publicos -> SIC", y v1 mando un
#               corte de energia a la SIC (caso 4724). Se dice el alcance.
#   3319        exclusividad entre empresas: el incumplimiento no se reclama ante
#               la SIC (es el patron del caso 3328, regimen de consumo en B2B).
#   2725        la Superintendencia Financiera vigila a la aseguradora, no a la
#               empresa de alquiler.
# Solo cambia el puntero; el prefijo es la frase de escape exacta.
CORRECCIONES_B2 = {
    4718: "Presenta un reclamo escrito al operador y, si no responde, acude a la "
          "Superintendencia de Industria y Comercio, que atiende las quejas de internet "
          "y telefonia; las de agua, luz y gas van a la Superintendencia de Servicios "
          "Publicos Domiciliarios.",
    4719: "Pide la cancelacion por escrito al operador, guarda el numero de radicado y, "
          "si insisten en las trabas, queja ante la Superintendencia de Industria y "
          "Comercio, que atiende internet y telefonia (no agua, luz ni gas).",
    3319: "Guarda el contrato y las pruebas de las ventas en tu zona, requiere por "
          "escrito y, si sigue, acude a un centro de conciliacion; si no hay acuerdo, el "
          "incumplimiento se reclama ante el juez civil o el arbitraje que haya pactado "
          "el contrato.",
    2725: "Revisa el contrato de alquiler y la poliza. Si la aseguradora te niega el "
          "pago o te cobra algo indebido, puedes quejarte ante la Superintendencia "
          "Financiera, que la vigila; por lo que te cobre la empresa de alquiler, un "
          "consultorio juridico universitario puede orientarte.",
}


def respuesta_b2(registro: dict) -> str:
    """El objetivo de un B2 escrito a mano, con la correccion de H25 si la tiene."""
    from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

    puntero = CORRECCIONES_B2.get(registro["id"])
    if puntero is None:
        return registro["messages"][-1]["content"]
    return f"{RESPUESTA_SIN_CONTEXTO}. {puntero}"


def rehacer_b2_a_mano(registros: list[dict], store=None) -> tuple[list[dict], list[dict]]:
    """Los B2 escritos a mano de ENTRENAMIENTO, con contexto de su propia categoria.

    Los de validacion se saltan y se conservan tal cual (defecto H3).

    **Por que no hace falta declarar `excluir` en estos.** Un B2 a mano es una
    pregunta cuya respuesta correcta *es* la frase de escape: el corpus no la
    responde. Se comprueba en el dataset -- los 263 B2 a mano tienen `fuentes` vacio y
    ninguno cita un articulo -- y lo impone el generador, que rechaza un B2 con
    `fuentes`. Si **nada** del corpus responde, **ningun** contexto es
    suficiente, y entonces no hay articulo oraculo que retirar: la regla v3 se
    reduce a usar lo que devuelve el buscador.

    Eso vuelve el ejemplo mucho mas realista. El enrutador, ante una pregunta de
    arriendo, devuelve la Ley 820: articulos de la materia correcta que no
    responden *esa* pregunta. Es exactamente la situacion en la que el modelo
    tiene que abstenerse, y es la que el contexto historico -- normas de otras
    categorias -- nunca le mostro.

    **El riesgo que queda, y como se acota.** Que alguna de esas preguntas si
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
        # **La validacion no se toca.** Los 35 B2 de validacion son los que miden
        # la abstencion, y su contexto tiene que ser el mismo con que se evaluaron
        # v1 y v2 y sobre el que se adjudicaron. Una version anterior los
        # reconstruia junto con los de entrenamiento (defecto H3, commit
        # 33cc019): la validacion conservaba los ids y cambiaba el contenido. Se
        # quedan como estan en la base, y construir() los conserva de alli.
        if r.get("split") == "val":
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
                           respuesta=respuesta_b2(r),
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
    _riesgo = composicion(registros)["riesgo_suficiencia_indirecta"]
    return {
        "version": VERSION_DATASET,
        "version_contexto": VERSION,
        "derivado_de": {"archivo": BASE_PATH, "revision": BASE_REV,
                        "huella": huella(leer_base())},
        "commit": commit,
        "buscador": sorted({r.get("buscador") for r in registros if r.get("buscador")}),
        "correcciones": [
            "contexto B2 de los contrastivos con REGLA_B2_V3 (misma categoria, sin el articulo oraculo)",
            "contexto de los B2 escritos a mano DE ENTRENAMIENTO con REGLA_B2_V3, sin `excluir`: su "
            "respuesta correcta ES la frase de escape, el corpus no los responde, y entonces "
            "ningun contexto es suficiente y no hay articulo oraculo que retirar",
            "los B2 de VALIDACION no se reconstruyen: conservan el contenido de la base (H3)",
            "todos los contextos con el buscador de produccion, e5 + FAISS + enrutador (H4)",
            "objetivos de los contrastivos con punteros que valen para cualquier pregunta (H22); "
            "violencia intrafamiliar conserva la Comisaria de Familia y la linea 155",
            "4 punteros de B2 escritos a mano corregidos: autoridad fuera de su competencia (H25)",
            "variantes descartadas cuando el contexto traia un articulo contiguo al retirado",
            "variantes de urgencia no generadas: un escape sin encaminar es una abstencion peligrosa",
        ],
        # Se cuentan, no se escriben: dos cifras escritas a mano en este bloque
        # quedaron falsas en cuanto cambio el buscador.
        "sin_corregir": [
            f"{_riesgo.get('AFINIDAD_ALTA_REVISAR', 0)} B2 a mano con afinidad alta a un fragmento "
            "de su propia categoria: marcados AFINIDAD_ALTA_REVISAR por si alguno si tiene "
            "respuesta en el corpus",
            f"{_riesgo.get('MISMO_CAPITULO', 0)} variantes con un articulo del mismo capitulo que "
            "el retirado, no contiguo: riesgo residual documentado",
            "los 35 B2 de validacion tienen 0 fragmentos de su propia categoria (contexto "
            "historico): no detectan el atajo. Lo detecta la prueba de los 4 escenarios",
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
    p.add_argument("--indice", action="store_true",
                   help="contexto con el buscador de PRODUCCION: e5 + FAISS + enrutador. "
                        "Obligatorio para escribir")
    p.add_argument("--permitir-bm25", action="store_true",
                   help="escribir con BM25 aunque no sea el buscador de produccion. "
                        "Solo para pruebas: reintroduce el defecto H4")
    args = p.parse_args(argv)

    store = None
    if args.indice:
        from tools.rag import pipeline

        store = pipeline.load_index()

    # **Escribir exige el buscador de produccion.** Sin --indice los contextos
    # salen de BM25, y el RAG responde con e5 + FAISS: el modelo se entrenaria con
    # un tipo de contexto que en servicio no ve. Paso al construir v3 en local
    # (defecto H4): los B2 escritos a mano quedaron con BM25 y todos los
    # B1/B3 con e5, y el estilo del contexto podia delatar el modo. --check puede
    # correr sin indice para revisar; escribir no.
    if not args.check and store is None and not args.permitir_bm25:
        raise SystemExit(
            "Para escribir el dataset hace falta --indice (e5 + FAISS, el buscador "
            "de produccion). Sin el, los contextos salen de BM25: es el defecto H4. "
            "Si es solo una prueba, --permitir-bm25.")

    registros, descartadas = construir(store)
    m = manifiesto(registros, descartadas)

    print(f"DATASET {VERSION_DATASET}   huella {m['huella']}   derivado de {m['derivado_de']['huella']}")
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
