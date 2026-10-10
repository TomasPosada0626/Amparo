"""Pares contrastivos: la misma pregunta con un contexto que responde y con uno que no.

El diagnostico. En la corrida del 2026-10-09 el modelo se abstuvo en 0 de 35
casos B2, donde el contexto no responde la pregunta. La primera hipotesis era
falta de ejemplos, y es falsa: hay 228 B2 en entrenamiento, el 35 % de los
ejemplos con contexto, con el target correcto y sin truncarse (el ejemplo mas
largo son ~2750 tokens contra un MAX_SEQ_LENGTH de 3072).

Lo que si encontramos, contando las preguntas base de los 652 ejemplos con
contexto en entrenamiento:

    solo B1: 331 preguntas    solo B2: 193    solo B3: 76    en varios: 1

El modelo **nunca ve la misma pregunta con un contexto suficiente y con uno
insuficiente**. El modo es predecible desde la pregunta sola, asi que puede
bajar la perdida memorizando que preguntas llevan abstencion -- un atajo que no
generaliza. En validacion las preguntas son nuevas, el atajo no sirve, y queda
el comportamiento dominante: responder.

Y ese comportamiento domina por mucho. La perdida de un LM causal se promedia
por token, asi que lo que pesa es la masa de tokens del target, no el conteo de
ejemplos:

    v1 (responder sin contexto)   66.7 % de ejemplos   60.8 % de los tokens
    B1 (citar del contexto)       17.2 %               24.3 %
    B2 (ABSTENERSE)               11.7 %                8.3 %
    B3 (parcial)                   4.5 %                6.5 %

85 % de la senal ensena "produce una respuesta de fondo" y 8.3 % ensena
"niegate". Diez a uno. Y el target de B2 mide la mitad que el de B1 (216 contra
427 caracteres), asi que cada ejemplo B2 aporta la mitad del gradiente.

La correccion. Para cada pregunta de entrenamiento que hoy solo tiene contexto
suficiente (B1 o B3), se genera una variante B2: **la misma pregunta**, un
contexto construido con la regla de B2, y la frase de escape. Eso rompe el
atajo -- el modo deja de ser predecible desde la pregunta -- y sube la masa de
tokens de abstencion.

No hace falta escribir derecho nuevo: la pregunta ya existe, el contexto se
arma mecanicamente con la misma funcion que usan los B2 escritos a mano, y el
target es la frase fija mas un puntero de donde consultar.

Lo que NO se puede hacer en la otra direccion: una variante B1 de una pregunta
que hoy es B2 necesitaria el articulo que la responde, y los B2 no tienen
`fuentes` por construccion. Eso si exige trabajo juridico.

Riesgo a medir, no a suponer: esto empuja hacia abstenerse, y la sobre-
abstencion con retrieval real hoy es de 1 caso en 45 (ver docs/m3_abstencion.md).
Si sube, se nota en `es_abstencion_pura` sobre los gold del eval set.

    python -m tools.dataset_contrastivo              # escribe y revisa
    python -m tools.dataset_contrastivo --revisar    # solo revisa lo escrito
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.evaluation import config as config_eval
from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

# Lee el dataset unico y toma de ahi los ejemplos con contexto. Antes leia
# data/dataset_m1_v2.jsonl, que se borro al unificar los cinco archivos.
DATASET = config_eval.DATASET_PATH
SALIDA = config_eval.PROJECT_ROOT / "data" / "dataset_contrastivo_revision.jsonl"

# Los ids de v2 van de 2001 a 4724 y RANGO_IDS llega a 8999; 9000+ es el eval
# set. Las variantes arrancan en 6001 para que se distingan de un golpe.
PRIMER_ID = 6001

# A donde mandar a la persona cuando el contexto no alcanza. No es contenido
# juridico: es un puntero. Se deriva de la categoria para no escribir una frase
# a mano por ejemplo, y los B2 originales (263, cada uno con su propia frase)
# no se tocan.
DONDE_CONSULTAR: dict[str, str] = {
    "Salud / EPS": "Puedes pedir orientacion en la Supersalud o en un consultorio juridico universitario.",
    "Pensiones y seguridad social": "Pide orientacion en tu fondo de pensiones o en un consultorio juridico universitario.",
    "Despido": "Pide orientacion en el Ministerio del Trabajo o en un consultorio juridico universitario.",
    "Relaciones laborales": "Pide orientacion en el Ministerio del Trabajo o en un consultorio juridico universitario.",
    "Arriendo": "Puedes consultar en una oficina de conciliacion o en un consultorio juridico universitario.",
    "Embargos": "Lleva el caso a un consultorio juridico universitario o pregunta en el juzgado del proceso.",
    "Reporte en centrales de riesgo": "Puedes reclamar ante la entidad que reporto y consultar en la Superintendencia Financiera.",
    "Garantias de consumo": "Puedes consultar en la Superintendencia de Industria y Comercio.",
    "Comparendos de transito": "Pregunta en la Secretaria de Transito de tu municipio.",
    "Accidentes de transito": "Pregunta en la Secretaria de Transito o en un consultorio juridico universitario.",
    "Violencia intrafamiliar": "Acude a la Comisaria de Familia; si hay riesgo inmediato, llama a la linea 155.",
    "Conciliacion prejudicial": "Pregunta en un centro de conciliacion o en un consultorio juridico universitario.",
}
_DEFECTO = "Te sugiero consultar un consultorio juridico universitario."


def donde_consultar(categoria: str) -> str:
    return DONDE_CONSULTAR.get(categoria, _DEFECTO)


def respuesta_de_escape(categoria: str) -> str:
    """La frase exacta mas el puntero. El prefijo tiene que ser identico al de
    los B2 escritos a mano: `es_valvula_de_escape` y el juez lo buscan tal cual."""
    return f"{RESPUESTA_SIN_CONTEXTO}. {donde_consultar(categoria)}"


def candidatas(registros: list[dict]) -> list[dict]:
    """Ejemplos de entrenamiento que merecen una variante B2.

    Solo B1 y B3 de `train`: son las preguntas que hoy el modelo solo ve con un
    contexto que responde. No se tocan los B2 (ya ensenan a abstenerse) ni nada
    de `val` (seria entrenar sobre la medicion).
    """
    en_val = {r.get("base_id") for r in registros if r.get("split") == "val"}
    salida = []
    for r in registros:
        if r.get("split") != "train" or r.get("modo") not in ("B1", "B3"):
            continue
        # Una variante de una pregunta cuya base esta en validacion metaria esa
        # pregunta en entrenamiento por la puerta de atras.
        if r.get("base_id") is not None and r["base_id"] in en_val:
            continue
        salida.append(r)
    return salida


def construir(registros: list[dict] | None = None, store=None) -> list[dict]:
    """Las variantes B2, con el contexto armado por la misma via que los B2 a mano."""
    from tools.dataset_v2 import Buscador, Especificacion, cargar_corpus, fragmentos_para
    from tools.rag.prompt_template import build_messages

    registros = registros if registros is not None else _leer(DATASET)
    c = cargar_corpus()
    buscador = Buscador(c, store)

    salida = []
    descartadas: list[tuple[int, str]] = []
    for i, r in enumerate(candidatas(registros)):
        e = Especificacion(
            id=PRIMER_ID + i,
            categoria=r["category"],
            modo="B2",
            respuesta=respuesta_de_escape(r["category"]),
            base=r.get("base_id"),
            pregunta=r["pregunta"],
            fuentes=[],           # B2 no lleva: ningun fragmento debe servir
        )
        fragmentos, origen = fragmentos_para(e, e.pregunta, c, buscador)

        # La regla de B2 excluye las normas de la categoria, las transversales,
        # las de las 3 categorias probables y los codigos generales. No basta:
        # el 2026-10-09 una variante trajo el articulo 34 del Codigo de Policia,
        # que era justo el que respondia el original, porque ese codigo no esta
        # clasificado en esa categoria. Suficiencia indirecta: se descarta la
        # variante en vez de ensenar a abstenerse con la respuesta delante.
        fuentes_doc = _fuentes_como_doc(r.get("fuentes") or (), c)
        traidos = {f"{f.doc_id}:{a}" for f in fragmentos for a in (f.articulos_incluidos or ())}
        choque = sorted(set(fuentes_doc) & traidos)
        if choque:
            descartadas.append((r["id"], f"trae el articulo que responde: {choque}"))
            continue

        # Tampoco puede tomar fragmentos de una norma que aparecia en el
        # contexto SUFICIENTE del original. Si la busqueda la puso en el top-5
        # de ese caso, otro articulo suyo esta lo bastante cerca del tema como
        # para que no se pueda descartar que resuelva por via indirecta sin
        # mirarlo con criterio juridico. Caso 4006: el original responde con los
        # articulos 139 y 142 del Codigo de la Infancia y la variante traia el
        # 143 y el 149, del mismo capitulo sobre responsabilidad penal
        # adolescente.
        docs_original = {ch.get("doc_id") for ch in (r.get("contexto") or ())}
        compartidos = sorted({f.doc_id for f in fragmentos} & docs_original)
        if compartidos:
            descartadas.append(
                (r["id"], f"toma fragmentos de normas del contexto original: {compartidos}"))
            continue

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
            # Las fuentes del original resueltas a (doc_id, articulo). Se
            # guardan aqui para que revisar() pueda comparar PARES sin cargar
            # el corpus: comparar numeros sueltos da falsos positivos, porque
            # el articulo 18 de otra ley no es el articulo 18 de esta.
            "fuentes_originales": fuentes_doc,
            # De que ejemplo es el contraste. Sirve para comprobar que el par
            # existe y para armar lotes que lleven los dos juntos.
            "par_de": r["id"],
        })
    if descartadas:
        print(f"Descartadas {len(descartadas)} variantes por suficiencia indirecta:")
        for ident, razon in descartadas:
            print(f"  original {ident}: {razon}")
    return salida


def _fuentes_como_doc(fuentes, c) -> list[str]:
    """["LEY-820-2003:20"] -> ["arrendamiento_...:20"], via el corpus.

    `fuentes` usa el IDENTIFIER de la norma y el contexto usa el nombre del
    archivo. Sin traducir, la unica comparacion posible es por numero de
    articulo, y eso marca como conflicto el articulo 18 de cualquier otra ley.
    """
    salida = []
    for f in fuentes:
        if ":" not in f:
            continue
        ident, art = f.rsplit(":", 1)
        idx = c.por_articulo.get((ident, art)) or []
        for i in idx:
            doc = c.resultados[i].doc_id
            if f"{doc}:{art}" not in salida:
                salida.append(f"{doc}:{art}")
    return salida


def revisar(variantes: list[dict], registros: list[dict]) -> list[str]:
    """Lo que tiene que cumplirse para que esto no empeore el dataset."""
    problemas = []
    por_id = {r["id"]: r for r in registros}
    ids_previos = set(por_id)
    en_val = {r.get("base_id") for r in registros if r.get("split") == "val"}

    repetidos = [v["id"] for v in variantes if v["id"] in ids_previos]
    if repetidos:
        problemas.append(f"ids que ya existen en el dataset: {repetidos[:10]}")

    propios = [v["id"] for v in variantes]
    if len(set(propios)) != len(propios):
        problemas.append("ids repetidos entre las variantes")

    fuera = [v["id"] for v in variantes if v["split"] != "train"]
    if fuera:
        problemas.append(f"variantes que no son de train: {fuera[:10]}")

    fuga = [v["id"] for v in variantes
            if v.get("base_id") is not None and v["base_id"] in en_val]
    if fuga:
        problemas.append(f"variantes de una pregunta que esta en validacion: {fuga[:10]}")

    sin_par = [v["id"] for v in variantes if v.get("par_de") not in ids_previos]
    if sin_par:
        problemas.append(f"variantes sin el ejemplo original: {sin_par[:10]}")

    # El contexto de la variante NO puede traer el articulo que responde en el
    # original. Si lo trae, el ejemplo ensena a abstenerse teniendo la respuesta
    # delante, que es peor que no tener el ejemplo.
    malas = []
    for v in variantes:
        esperados = set(v.get("fuentes_originales") or ())
        if not esperados:
            continue
        traidos = {f"{ch.get('doc_id')}:{a}"
                   for ch in (v.get("contexto") or ()) for a in (ch.get("articulos") or ())}
        comunes = esperados & traidos
        if comunes:
            malas.append((v["id"], sorted(comunes)))
    if malas:
        problemas.append(
            "variantes cuyo contexto trae el articulo que responde en el original: "
            f"{malas[:5]}")

    vacias = [v["id"] for v in variantes if not v.get("contexto")]
    if vacias:
        problemas.append(f"variantes sin contexto: {vacias[:10]}")

    mal_target = [v["id"] for v in variantes
                  if not v["messages"][-1]["content"].startswith(RESPUESTA_SIN_CONTEXTO)]
    if mal_target:
        problemas.append(f"variantes cuyo target no empieza con la frase exacta: {mal_target[:10]}")

    return problemas


def _leer(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def imprimir(variantes: list[dict], registros: list[dict]) -> None:
    from collections import Counter

    tr = [r for r in registros if r.get("split") == "train" and r.get("modo")]
    antes = Counter(r["modo"] for r in tr)
    despues = Counter(antes)
    despues["B2"] += len(variantes)

    print(f"{'modo':6}{'antes':>8}{'despues':>10}")
    print("-" * 24)
    for m in ("B1", "B2", "B3"):
        print(f"{m:6}{antes[m]:>8}{despues[m]:>10}")
    print()

    def chars(r):
        return len(r["messages"][-1]["content"])

    masa_antes = sum(chars(r) for r in tr) + sum(
        chars(r) for r in registros if r.get("split") == "train" and not r.get("modo"))
    b2_antes = sum(chars(r) for r in tr if r["modo"] == "B2")
    b2_nuevo = b2_antes + sum(chars(v) for v in variantes)
    masa_despues = masa_antes + sum(chars(v) for v in variantes)
    print(f"masa de tokens de abstencion: {b2_antes / masa_antes:.1%} -> {b2_nuevo / masa_despues:.1%}")

    por_base = {}
    for r in tr:
        por_base.setdefault(r["base_id"], set()).add(r["modo"])
    for v in variantes:
        por_base.setdefault(v["base_id"], set()).add("B2")
    multi = sum(1 for v in por_base.values() if len(v) > 1)
    print(f"preguntas que el modelo ve en mas de un modo: 1 -> {multi}")


def informe(variantes: list[dict], registros: list[dict]) -> None:
    """Lo que hay que comprobar antes de entrenar con esto.

    Se imprime en vez de devolverse: es una revision para leer, no una metrica
    para promediar. Cada bloque responde una pregunta concreta sobre si las
    variantes sirven.
    """
    from collections import Counter

    from tools.rag import corpus as corpus_mod
    from tools.rag.corpus import TRANSVERSAL

    cats_doc = {n.path.stem: set(n.categorias) for n in corpus_mod.NORMAS_EN_ALCANCE}
    por_id = {r["id"]: r for r in registros}
    cand = candidatas(registros)
    tr = [r for r in registros if r.get("split") == "train" and r.get("modo")]
    en_val = {r.get("base_id") for r in registros if r.get("split") == "val"}

    print("=" * 72)
    print("1. CUANTAS SE GENERARON Y QUE SE DESCARTO")
    print("=" * 72)
    print(f"  candidatas (B1/B3 de train)                            {len(cand):5}")
    print(f"  variantes generadas                                    {len(variantes):5}")
    print(f"  descartadas por suficiencia indirecta                  "
          f"{len(cand) - len(variantes):5}")
    print()
    print("  no eran candidatas, y por que:")
    for etiqueta, n in (
        ("B2 de train: ya ensenan a abstenerse",
         sum(1 for r in tr if r["modo"] == "B2")),
        ("todo lo de val: seria entrenar sobre la medicion",
         sum(1 for r in registros if r.get("split") == "val" and r.get("modo"))),
        ("v1 sin contexto: no hay contexto que contrastar",
         sum(1 for r in registros if r.get("split") == "train" and not r.get("modo"))),
        ("B1/B3 cuya pregunta base esta en validacion",
         sum(1 for r in tr if r["modo"] in ("B1", "B3")
             and r.get("base_id") is not None and r["base_id"] in en_val)),
    ):
        print(f"    {etiqueta:54}{n:5}")
    print()
    orig = Counter(r["category"] for r in tr)
    nuevas = Counter(v["category"] for v in variantes)
    print(f"  {'categoria':44}{'orig':>6}{'nuevas':>8}")
    print("  " + "-" * 58)
    for cat in sorted(set(orig) | set(nuevas)):
        print(f"  {cat[:42]:44}{orig[cat]:>6}{nuevas[cat]:>8}")
    print()

    print("=" * 72)
    print("2. CADA VARIANTE CONTRASTA DE VERDAD CON SU ORIGINAL")
    print("=" * 72)
    n = len(variantes)
    misma = sum(1 for v in variantes
                if por_id.get(v["par_de"], {}).get("pregunta") == v["pregunta"])
    print(f"  misma pregunta, caracter por caracter                  {misma}/{n}")

    comparte = [(v["id"], sorted({ch.get("doc_id") for ch in (v.get("contexto") or ())}
                                 & {ch.get("doc_id") for ch in
                                    ((por_id.get(v["par_de"]) or {}).get("contexto") or ())}))
                for v in variantes]
    comparte = [(i, d) for i, d in comparte if d]
    print(f"  ningun documento en comun con el contexto original     {n - len(comparte)}/{n}")
    if comparte:
        print(f"      comparten: {comparte[:5]}")

    trae = [v["id"] for v in variantes
            if set(v.get("fuentes_originales") or ())
            & {f"{ch.get('doc_id')}:{a}" for ch in (v.get("contexto") or ())
               for a in (ch.get("articulos") or ())}]
    print(f"  no trae el articulo que responde la consulta           {n - len(trae)}/{n}")
    if trae:
        print(f"      lo traen: {trae[:10]}")

    # Suficiencia indirecta: ninguna norma del contexto puede cubrir la
    # categoria del ejemplo ni ser transversal. Es la regla con que se
    # construyo; aqui se comprueba sobre lo que quedo escrito.
    indirecta = []
    for v in variantes:
        for ch in v.get("contexto") or ():
            cats = cats_doc.get(ch.get("doc_id"), set())
            if v["category"] in cats or TRANSVERSAL in cats:
                indirecta.append((v["id"], ch.get("doc_id")))
                break
    print(f"  ninguna norma cubre la categoria ni es transversal     {n - len(indirecta)}/{n}")
    if indirecta:
        print(f"      podrian resolver indirectamente: {indirecta[:5]}")
    fuera = [v["id"] for v in variantes if len(v.get("contexto") or ()) != 5]
    print(f"  los 5 fragmentos completos                            {n - len(fuera)}/{n}")
    print()

    print("=" * 72)
    print("3 y 4. DUPLICADOS, FUGAS Y PARTICION")
    print("=" * 72)
    problemas = revisar(variantes, registros)
    print(f"  revisar(): {'sin problemas' if not problemas else f'{len(problemas)} problemas'}")
    for s in problemas:
        print(f"      - {s}")
    print(f"  ids que choquen con el dataset                         "
          f"{len([v for v in variantes if v['id'] in por_id])}")
    print(f"  ids repetidos entre variantes                          "
          f"{len(variantes) - len({v['id'] for v in variantes})}")
    print(f"  variantes fuera de train                               "
          f"{len([v for v in variantes if v['split'] != 'train'])}")
    print(f"  ids en el rango del eval set (9000+)                   "
          f"{len([v for v in variantes if 9000 <= v['id'] < 10000])}")
    mismo = sum(1 for v in variantes
                if por_id.get(v["par_de"], {}).get("split") == v["split"])
    print(f"  variante en la misma particion que su original         {mismo}/{n}")
    preg_val = {r.get("pregunta") for r in registros if r.get("split") == "val"}
    print(f"  variantes cuya pregunta aparece en validacion          "
          f"{len([v for v in variantes if v['pregunta'] in preg_val])}")
    print()

    print("=" * 72)
    print("5. CUANTO SUBE LA SENAL DE ABSTENCION")
    print("=" * 72)
    v1 = [r for r in registros if r.get("split") == "train" and not r.get("modo")]

    def ch_(r):
        return len(r["messages"][-1]["content"])

    antes = {"v1": v1, "B1": [r for r in tr if r["modo"] == "B1"],
             "B2": [r for r in tr if r["modo"] == "B2"],
             "B3": [r for r in tr if r["modo"] == "B3"]}
    despues = dict(antes, B2=antes["B2"] + variantes)
    for etiqueta, grupos in (("ANTES", antes), ("DESPUES", despues)):
        n_tot = sum(len(g) for g in grupos.values())
        c_tot = sum(ch_(r) for g in grupos.values() for r in g)
        print(f"  {etiqueta}  ({n_tot} ejemplos de entrenamiento)")
        print(f"    {'grupo':6}{'n':>7}{'% ejemplos':>13}{'% senal':>10}")
        for k in ("v1", "B1", "B2", "B3"):
            g = grupos[k]
            print(f"    {k:6}{len(g):>7}{len(g) / n_tot:>12.1%}"
                  f"{sum(ch_(r) for r in g) / c_tot:>10.1%}")
        print()
    por_base: dict = {}
    for r in tr:
        por_base.setdefault(r["base_id"], set()).add(r["modo"])
    multi_antes = sum(1 for s in por_base.values() if len(s) > 1)
    for v in variantes:
        por_base.setdefault(v["base_id"], set()).add("B2")
    print(f"  preguntas que el modelo ve en MAS DE UN modo: {multi_antes} -> "
          f"{sum(1 for s in por_base.values() if len(s) > 1)}")
    print("  Es lo que rompe el atajo: el modo deja de ser predecible desde la pregunta.")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--revisar", action="store_true", help="solo revisar lo ya escrito")
    args = p.parse_args(argv)

    registros = _leer(DATASET)
    variantes = _leer(SALIDA) if args.revisar else construir(registros)

    problemas = revisar(variantes, registros)
    if problemas:
        for s in problemas:
            print(f"  - {s}")
        raise SystemExit(f"{len(problemas)} problemas: no se escribe nada")

    if not args.revisar:
        SALIDA.write_text(
            "\n".join(json.dumps(v, ensure_ascii=False) for v in variantes) + "\n",
            encoding="utf-8")
        print(f"Escrito {SALIDA} ({len(variantes)} variantes)")
    else:
        print(f"{len(variantes)} variantes, sin problemas")
    print()
    informe(variantes, registros)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
