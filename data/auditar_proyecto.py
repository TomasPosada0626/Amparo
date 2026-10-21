"""Auditoria profunda de la capa de datos: dataset, gold, eval sets, corpus,
normas y baseline. Busca ERRORES, no documentacion.

POR QUE ESTE SCRIPT Y NO LAS 68 PRUEBAS
    La suite comprueba la fontaneria: que los modulos carguen, que el motor
    derive, que los superconjuntos no se muevan. Esto comprueba otra cosa ---
    la COHERENCIA ENTRE CAPAS: que lo que el gold cita exista en el whitelist,
    que lo que el whitelist declara este en el corpus, que ningun caso se
    apoye en una norma que el propio proyecto declara inexequible, y que la
    ganancia de cabecera del baseline no sea un artefacto de formato.

    Son las uniones, que es donde un proyecto con cada pieza correcta puede
    estar equivocado igual.

    Uso: python -I data/auditar_proyecto.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
import metricas  # noqa: E402
import schema    # noqa: E402
import sistema   # noqa: E402
from reglas import Hechos, decidir, estrato_verificacion  # noqa: E402

HALLAZGOS: list[tuple[str, str, str]] = []   # (capa, gravedad, texto)


def hallar(capa: str, gravedad: str, texto: str) -> None:
    HALLAZGOS.append((capa, gravedad, texto))


def comprobar(cond, capa: str, gravedad: str, texto: str) -> bool:
    if not cond:
        hallar(capa, gravedad, texto)
    return bool(cond)


def _j(nombre: str):
    return json.loads((RAIZ / "data" / nombre).read_text(encoding="utf-8"))


# ==========================================================================
def normas_declaradas() -> set[str]:
    n = _j("normas.json")
    out = set()
    for sec in ("constitucion", "decreto_2591_1991", "leyes",
                "jurisprudencia_referencia"):
        out |= {k for k in n.get(sec, {}) if not k.startswith("_")}
    return out


def auditar_normas_y_corpus() -> None:
    """El whitelist y el corpus tienen que contarse la misma historia."""
    corpus = _j("corpus.json")["documentos"]
    declaradas = normas_declaradas()
    validas, sueltas, leyes = metricas._vocabulario_normas()

    # 1 · todo fragmento tiene que estar verificado y con fuente.
    sin_ver = [f["id"] for f in corpus if not f.get("verificado")]
    comprobar(not sin_ver, "corpus", "GRAVE",
              f"fragmentos sin `verificado: true`: {sin_ver[:6]}")
    sin_fuente = [f["id"] for f in corpus if not (f.get("fuente") or "").strip()]
    comprobar(not sin_fuente, "corpus", "GRAVE",
              f"fragmentos sin `fuente`: {sin_fuente[:6]}")

    # 2 · lo que el corpus llama LITERAL tiene que decir que lo es, y lo que
    #     no, tiene que explicar por que. El proyecto se niega a fabricar
    #     texto legal: una transcripcion que se declara literal y no lo es
    #     seria el peor fallo posible de este repositorio.
    for f in corpus:
        t = (f.get("transcripcion") or "").strip().lower()
        if t and t != "literal" and not (f.get("por_que_no_es_literal") or
                                         f.get("normalizacion")):
            hallar("corpus", "MEDIO",
                   f"{f['id']}: `transcripcion: {t}` sin decir por que no es "
                   "literal")

    # 3 · la cabecera que el RAG le ensena al modelo tiene que ser una cita
    #     que se pueda verificar. El unico que puede fallar es el inexequible,
    #     y tiene que fallar.
    for f in corpus:
        cl = metricas.clasificar_cita(sistema.cita_completa(f), validas,
                                      sueltas, leyes)
        vig = (f.get("vigencia") or "").lower().startswith("vigente")
        if vig and cl not in ("valida", "jurisprudencia"):
            hallar("corpus", "GRAVE",
                   f"{f['id']}: la cabecera del contexto clasifica como "
                   f"`{cl}` y el fragmento es vigente")
        if not vig and cl == "valida":
            hallar("corpus", "GRAVE",
                   f"{f['id']}: NO es derecho vigente y su cabecera clasifica "
                   "como `valida`: se le estaria sirviendo al modelo una cita "
                   "copiable de algo derogado")

    # 4 · toda norma del whitelist deberia poder recuperarse del corpus, o el
    #     sistema puede citar algo que no puede mostrar.
    #
    #     SE USA `rag.cubre`, NO UNA COMPARACION PROPIA. La primera version de
    #     esta comprobacion construia su propio conjunto de "lo que el corpus
    #     tiene" --- cita, articulo y norma --- y denuncio 8 normas huerfanas
    #     que estaban perfectamente cubiertas:
    #
    #       · `art. 6.1` a `art. 6.5` viven dentro del fragmento del `art. 6`
    #         completo, con sus cinco numerales en el texto.
    #       · `Ley 2157 de 2021` la respalda el fragmento del art. 13 de la
    #         Ley 1266, porque su texto vigente ES el que esa ley introdujo;
    #         el corpus lo declara en `tambien_cita` y no duplica el fragmento.
    #
    #     Es exactamente el fallo que `_vocabulario_normas` existe para
    #     evitar: dos definiciones de "existe" que se separan. Un auditor con
    #     su propia definicion denuncia lo correcto.
    #     Y las normas se toman de `_vocabulario_normas()`, no de las claves
    #     crudas del JSON: el whitelist indexa el Decreto por articulo suelto
    #     (`art. 1`) y la forma CITABLE lleva la norma pegada (`art. 1 Decreto
    #     2591 de 1991`), que es la que `cubre` compara. Pasarle las claves
    #     crudas denuncio 23 huerfanas donde no habia ninguna. Tercera vez que
    #     esta comprobacion se equivoca por definir "existe" por su cuenta.
    #
    #     La jurisprudencia queda fuera: `normas.json` la declara como
    #     REFERENCIA y el proyecto la excluye del chequeo de alucinacion a
    #     proposito, porque no hay whitelist completo de la jurisprudencia
    #     colombiana. Exigirle fragmento seria exigir lo que no se promete.
    from rag import cubre
    validas, _s, _l = metricas._vocabulario_normas()
    juris = set(_j("normas.json").get("jurisprudencia_referencia", {}))
    huerfanas = sorted(d for d in validas
                       if d not in juris
                       and not any(cubre(f, d) for f in corpus))
    if huerfanas:
        hallar("normas", "MEDIO",
               f"{len(huerfanas)} normas citables que `rag.cubre` no "
               f"encuentra en el corpus: {huerfanas[:8]}")


def auditar_gold() -> None:
    """Lo que el gold cita tiene que existir, y su etiqueta tiene que
    derivarse. Esto es lo que impide que el eval set envenene la metrica."""
    validas, sueltas, leyes = metricas._vocabulario_normas()
    inexequible = "art. 11"

    for archivo in ("eval_set.json", "eval_set_v2.json", "eval_set_v3.json",
                    "eval_set_m3.json"):
        casos = schema.cargar(archivo=archivo)
        capa = archivo.replace(".json", "")

        for c in casos:
            # 1 · ninguna cita del gold puede ser inventada ni incompleta: es
            #     el conjunto contra el que se mide la alucinacion.
            for campo in ("fundamento_del_derecho", "fundamento_del_mecanismo"):
                for cita in (c.get(campo) or []):
                    cl = metricas.clasificar_cita(cita, validas, sueltas, leyes)
                    if cl not in ("valida", "jurisprudencia"):
                        hallar(capa, "GRAVE",
                               f"{c['id']}.{campo}: `{cita}` clasifica como "
                               f"`{cl}` --- el gold no puede citar algo que el "
                               "propio medidor rechaza")

            # 2 · ningun caso puede apoyarse en el articulo inexequible.
            fund = " ".join([str(c.get("fundamento") or "")]
                            + list(c.get("fundamento_del_derecho") or [])
                            + list(c.get("fundamento_del_mecanismo") or []))
            if inexequible in fund and "2591" in fund:
                hallar(capa, "GRAVE",
                       f"{c['id']}: cita `art. 11 Decreto 2591`, que esta "
                       "INEXEQUIBLE (C-543/1992)")

            # 3 · la etiqueta la deriva el motor, y el estrato tambien.
            if c.get("mecanismo") and c.get("hechos") is not None:
                h = Hechos(**c["hechos"])
                d = decidir(h)
                if d.mecanismo != c["mecanismo"]:
                    hallar(capa, "GRAVE",
                           f"{c['id']}: archivo dice {c['mecanismo']} y el "
                           f"motor deriva {d.mecanismo}")
                if d.procede_tutela != c.get("procede"):
                    hallar(capa, "GRAVE",
                           f"{c['id']}: `procede` no lo respalda el motor")
                est, piv = estrato_verificacion(h)
                if c.get("estrato_verificacion") and est != c["estrato_verificacion"]:
                    hallar(capa, "MEDIO",
                           f"{c['id']}: estrato {c['estrato_verificacion']} "
                           f"vs {est} del motor")
                if (c.get("etiqueta_pivota_en") is not None
                        and sorted(c["etiqueta_pivota_en"]) != sorted(piv)):
                    hallar(capa, "MEDIO",
                           f"{c['id']}: `etiqueta_pivota_en` "
                           f"{c['etiqueta_pivota_en']} vs {piv} del motor")


def auditar_splits() -> None:
    """Cero fuga, cero duplicado, y los tres splits disjuntos."""
    tr = schema.cargar("train")
    va = schema.cargar("validation")
    ev = schema.cargar(archivo="eval_set_v3.json")
    m3 = schema.cargar(archivo="eval_set_m3.json")

    def norm(c):
        return " ".join((c.get("relato") or "").split()).lower()

    conj = {"train": tr, "validation": va, "eval_v3": ev, "eval_m3": m3}
    for nombre, casos in conj.items():
        rep = [r[:50] for r, k in Counter(norm(c) for c in casos).items()
               if k > 1]
        comprobar(not rep, "splits", "GRAVE",
                  f"{nombre}: relatos repetidos dentro del split: {rep[:3]}")
        ids = [c["id"] for c in casos]
        rid = [i for i, k in Counter(ids).items() if k > 1]
        comprobar(not rid, "splits", "GRAVE",
                  f"{nombre}: ids repetidos: {rid[:5]}")

    nombres = list(conj)
    for i, a in enumerate(nombres):
        for b in nombres[i + 1:]:
            ra = {norm(c) for c in conj[a]}
            rb = {norm(c) for c in conj[b]}
            inter = ra & rb
            comprobar(not inter, "splits", "GRAVE",
                      f"FUGA entre {a} y {b}: {len(inter)} relatos "
                      f"compartidos")


def auditar_baseline() -> None:
    """El hallazgo 4 de la auditoria externa, medido: la ganancia de cabecera
    no puede ser un artefacto de formato."""
    p = RAIZ / "results" / "m1_predicciones.json"
    if not p.exists():
        hallar("baseline", "AVISO",
               "no esta results/m1_predicciones.json: la descomposicion "
               "formato/razonamiento no se puede medir")
        return
    filas = json.loads(p.read_text(encoding="utf-8"))["datos"]
    gold = {c["id"]: c for c in schema.cargar(archivo="eval_set_v2.json")}
    gold.update({c["id"]: c for c in schema.cargar(archivo="eval_set_v3.json")})

    n = mec = proc = ambos = ilegible = 0
    for f in filas:
        g = gold.get(f["id"])
        if not g or not g.get("mecanismo"):
            continue
        n += 1
        d = schema.parse_salida(f["base"]) or {}
        if d.get("mecanismo") is None:
            ilegible += 1
        ok_m = d.get("mecanismo") == g["mecanismo"]
        ok_p = d.get("procede") == g.get("procede")
        mec += ok_m
        proc += ok_p
        ambos += ok_m and ok_p
    if not n:
        return
    brecha = mec / n - ambos / n
    if brecha <= 0.10:
        return

    # QUE EL BASE SEA UN HOMBRE DE PAJA ES UN HECHO MEDIDO, NO UN DEFECTO.
    # El defecto seria NO DECLARARLO. Asi que lo que se audita es la
    # declaracion: que exista el artefacto con la descomposicion y que el
    # reporte la publique. Si estan, esto es informacion; si falta alguna, la
    # cifra de cabecera se lee como ganancia de razonamiento y no lo es toda.
    art = (RAIZ / "data" / "descomposicion_baseline.json").exists()
    rep = RAIZ / "REPORTE.md"
    declarado = art and rep.exists() and "formato" in rep.read_text(
        encoding="utf-8", errors="replace").lower()
    hallar("baseline", "AVISO" if declarado else "GRAVE",
           f"el base acierta el mecanismo en {mec / n:.1%} y los dos campos "
           f"solo en {ambos / n:.1%}: {brecha:.1%} del salto de cabecera es "
           f"FORMATO, no razonamiento ({ilegible} de {n} salidas con el "
           f"mecanismo ilegible). "
           + ("DECLARADO: `descomposicion_baseline.json` lo mide y el reporte "
              "lo publica con la columna del hibrido."
              if declarado else
              "SIN DECLARAR: falta `data/descomposicion_baseline.json` o el "
              "reporte no lo menciona, y entonces el salto se lee como "
              "ganancia de razonamiento cuando no lo es todo."))


def auditar_reporte_y_readme() -> None:
    """Que los documentos no afirmen cifras que ningun artefacto respalda."""
    rep = RAIZ / "REPORTE.md"
    if rep.exists():
        t = rep.read_text(encoding="utf-8", errors="replace")
        # El reporte se genera; lo que no puede pasar es que la tabla de
        # cabecera de M1 omita el brazo HIBRIDO, que es la comparacion justa
        # y que ya esta calculada.
        if "hibrido" not in t.lower():
            hallar("reporte", "GRAVE",
                   "la tabla de cabecera de M1 no menciona el brazo HIBRIDO, "
                   "que es la comparacion justa contra el base y ya esta "
                   "publicada en m1_scorecard_hibrido.json")
    rd = RAIZ / "README.md"
    if rd.exists():
        t = rd.read_text(encoding="utf-8", errors="replace")
        import re
        cifras = re.findall(r"\b\d{1,3}[.,]\d\s?%", t)
        if cifras:
            hallar("readme", "MEDIO",
                   f"el README trae cifras escritas a mano ({cifras[:4]}): "
                   "quedan obsoletas en la siguiente corrida y nadie se "
                   "entera")


# ==========================================================================
def main() -> int:
    print("=" * 84)
    print("  AUDITORIA PROFUNDA DE LA CAPA DE DATOS")
    print("=" * 84)
    for fn in (auditar_normas_y_corpus, auditar_gold, auditar_splits,
               auditar_baseline, auditar_reporte_y_readme):
        try:
            fn()
        except Exception as ex:                               # noqa: BLE001
            hallar(fn.__name__, "ERROR",
                   f"la comprobacion revento: {type(ex).__name__}: {ex}")

    por_capa: dict[str, list] = {}
    for capa, g, t in HALLAZGOS:
        por_capa.setdefault(capa, []).append((g, t))
    for capa in sorted(por_capa):
        print()
        print(f"  {capa}  ·  {len(por_capa[capa])} hallazgo(s)")
        print("  " + "-" * 80)
        for g, t in por_capa[capa]:
            print(f"    {g:6s} {t}")
    graves = sum(1 for _c, g, _t in HALLAZGOS if g in ("GRAVE", "ERROR"))
    print()
    print("=" * 84)
    if not HALLAZGOS:
        print("  sin hallazgos: las uniones entre capas se sostienen")
    else:
        print(f"  {len(HALLAZGOS)} hallazgos · {graves} graves")
    print("=" * 84)
    return 1 if graves else 0


if __name__ == "__main__":
    raise SystemExit(main())
