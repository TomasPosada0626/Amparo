"""
Harness de evaluación de tres dimensiones.

    sc = harness(eval_set, salidas, "mi sistema", juez)
    sc = harness(eval_set, mi_sistema, "mi sistema", juez)   # firma del lab S06

Se corre con una llamada, fija las semillas, registra versiones y produce el
mismo resultado entre ejecuciones (el juez va cacheado). Lo usan M1, M2 y M3
sin cambios: lo único que cambia entre módulos es `salidas`.

Las tres dimensiones y lo que mide cada una:

  1. CLÁSICA      similitud por embeddings, ROUGE-L, accuracy y macro-F1.
                  Mide parecido con el gold. NO mide si el derecho está bien
                  aplicado: una respuesta elegante y equivocada puntúa alto.

  2. LLM-JUEZ     nota 1-5 con rúbrica explícita, juez de otra familia.
                  Mide calidad del razonamiento, que ninguna métrica léxica ve.
                  NO es un oráculo: arrastra sesgos que hay que medir aparte.

  3. DOMINIO      acierto jurídico, alucinación normativa, pertinencia de las
                  citas y coherencia. Mide lo que el usuario decide con el
                  sistema. Es la única dimensión que distingue "suena bien" de
                  "sirve".
"""
from __future__ import annotations
import csv, json, platform, sys
from collections import Counter
from pathlib import Path

import metricas
import schema

SEMILLA = 42


# --------------------------------------------------------------------------
def acierto_por_item(salidas: list[str], golds: list[dict]) -> list[bool]:
    """El acierto jurídico caso por caso. Lo necesita el kappa contra el juez."""
    out = []
    for s, g in zip(salidas, golds):
        p = schema.parse_salida(s)
        out.append(p.get("mecanismo") == g["mecanismo"] and p.get("procede") == g["procede"])
    return out


def cohen_kappa(a: list, b: list) -> float | None:
    """Acuerdo entre dos anotadores corrigiendo por el azar.

    Aquí mide si el juez automático coincide con la verdad de campo. Un kappa
    bajo no dice que el juez esté roto: dice que no se puede usar solo.

    Devuelve None cuando el estadístico NO PUEDE INFORMAR, que son dos casos:

      - los dos anotadores usan la misma única categoría: el acuerdo esperado
        por azar es 1 y la fórmula se indetermina. La primera versión devolvía
        1.0 ahí, que se lee como "acuerdo perfecto" y es justo lo contrario;

      - CUALQUIERA de los dos es constante aunque el otro varíe. Este se nos
        escapó y es peor, porque no se indetermina: da 0.0 y parece una
        medición. Con el vector de dominio constante —el modelo base acierta 0
        de 46— la kappa vale 0.0 haga lo que haga el juez: apruebe todo,
        apruebe nada, o apruebe al azar. Comprobado numéricamente. Un
        estadístico que no puede variar no está midiendo; informar 0.0 ahí se
        lee como "no hay acuerdo" cuando lo cierto es "aquí no se puede saber".

    Un kappa bajo, cuando sí es computable, no dice que el juez esté roto:
    dice que no se puede usar solo.
    """
    n = len(a)
    if n == 0:
        return None
    # Sin variación en alguno de los dos, kappa es identicamente 0 y no
    # distingue un juez bueno de uno pesimo. Se devuelve None y quien imprime
    # escribe "indefinido".
    if len(set(a)) < 2 or len(set(b)) < 2:
        return None
    obs = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    esp = sum((ca[k] / n) * (cb[k] / n) for k in set(a) | set(b))
    if esp >= 1:
        return None
    return (obs - esp) / (1 - esp)


# --------------------------------------------------------------------------
def harness(eval_set: list[dict], salidas, etiqueta: str, juez=None) -> dict:
    """Las tres dimensiones sobre un mismo eval set. `juez=None` omite la 2.

    `salidas` acepta dos formas:

      - una **lista** de respuestas ya generadas (lo que usan M1 y M2: las
        salidas están en runs/m1_predicciones.json y no hay que volver a
        generarlas, lo que hace el harness reproducible y gratis de correr);
      - una **función** `sistema(relato) -> respuesta`, que es la firma del
        laboratorio de S06, para poder enchufar un sistema vivo en M3.
    """
    if callable(salidas):
        sistema = salidas
        salidas = [sistema(e["relato"]) for e in eval_set]

    assert len(eval_set) == len(salidas), "eval_set y salidas no cuadran"

    sc = metricas.scorecard(salidas, eval_set, etiqueta)   # dimensiones 1 y 3

    sc["entorno"] = {
        "python": platform.python_version(),
        "semilla": SEMILLA,
        "n_gold": sum(e.get("tipo") == "gold" for e in eval_set),
        "n_adversarial": sum(e.get("tipo") == "adversarial" for e in eval_set),
        # El eval v2 trae 6 casos de abstención, que no son ni gold ni
        # adversariales. Sin esta línea, n_gold + n_adversarial no suma n y
        # parece que faltan casos.
        "n_abstencion": sum(e.get("tipo") == "abstencion" for e in eval_set),
    }

    if juez is not None:                                    # dimensión 2
        from juez import puntuar_lote
        notas = puntuar_lote(juez, eval_set, salidas, schema.render_salida)
        sc["juez"] = resumen_juez(notas, salidas, eval_set, juez.modelo)

    return sc


def resumen_juez(notas: list[dict], salidas: list, eval_set: list[dict],
                 modelo: str) -> dict:
    """Agrega las notas del juez caso por caso.

    Está separado de `harness` a propósito: `tabla_puente` necesita el mismo
    resumen sobre un SUBCONJUNTO de notas ya obtenidas, sin volver a llamar al
    juez. Calcular las dos columnas del puente con dos pasadas de juez
    duplicaría el costo en API y, peor, introduciría el no-determinismo del
    juez entre las dos columnas, que es justo lo que el puente quiere aislar.
    """
    validas = [n["nota"] for n in notas if n["nota"] is not None]
    aprueba = [(n["nota"] or 0) >= 4 for n in notas]
    acierta = acierto_por_item(salidas, eval_set)

    out = {
        "modelo": modelo,
        "nota_media": sum(validas) / len(validas) if validas else 0.0,
        "distribucion": dict(sorted(Counter(validas).items())),
        "sin_parsear": len(notas) - len(validas),
        "kappa_vs_dominio": cohen_kappa(aprueba, acierta),
        "notas": notas,
    }
    por_tipo = {}
    for t in ("gold", "adversarial"):
        v = [n["nota"] for n, e in zip(notas, eval_set)
             if e.get("tipo") == t and n["nota"] is not None]
        if v:
            por_tipo[t] = sum(v) / len(v)
    out["nota_media_por_tipo"] = por_tipo
    return out


def ids_eval_v1(archivo: str = "eval_set.json") -> set[str]:
    """Los ids del eval set v1, que son el subconjunto de comparacion."""
    p = Path(__file__).resolve().parent.parent / "data" / archivo
    d = json.loads(p.read_text(encoding="utf-8"))
    return {e["id"] for e in d["ejemplos"]}


def tabla_puente(casos: list[dict], salidas: list, etiqueta: str,
                 ids_v1: set[str] | None = None, juez=None) -> dict:
    """El scorecard completo, con el puente contra el eval v1 dentro.

    DEVUELVE UN SCORECARD NORMAL, no un dict compuesto. Es sustituible por
    `harness()` sin tocar nada aguas abajo: `metricas.imprimir`, `sc["juez"]`,
    `sc["sistema"]`, `aplanar` y `publicar` siguen funcionando igual. El puente
    viaja en `sc["puente"]`.

    La version anterior devolvia `{"v1":..., "v2":...}` y rompia los seis
    consumidores de aguas abajo. Era un error de diseno: una funcion que
    sustituye a otra tiene que devolver lo que la otra devolvia.

    Por que basta UNA corrida. `eval_set_v2.json` es superconjunto estricto de
    `eval_set.json`: los 46 casos de v1 estan dentro con los mismos ids,
    relatos y etiquetas. Asi que la columna de v1 se obtiene filtrando esos
    ids, sin generar predicciones dos veces y SIN LLAMAR AL JUEZ DOS VECES. Eso
    ultimo es lo que importa: con dos pasadas de juez, su no-determinismo se
    mezclaria con el efecto de los casos agregados, que es justo lo que el
    puente quiere aislar.

    `ids_v1=None` los lee de data/eval_set.json. Si los casos recibidos no
    contienen todo v1 --- por ejemplo cuando se pasa `eval_set + eval_m3`, o el
    propio v1 --- el puente se marca como no disponible con el motivo, y el
    scorecard se devuelve igual. No se levanta excepcion: un brazo que corre
    sobre otro conjunto de casos es un uso legitimo, no un error.
    """
    assert len(casos) == len(salidas), "casos y salidas no cuadran"
    if ids_v1 is None:
        ids_v1 = ids_eval_v1()

    sc = harness(casos, salidas, etiqueta, juez)

    presentes = {e["id"] for e in casos}
    if not ids_v1 <= presentes:
        faltan = sorted(ids_v1 - presentes)
        sc["puente"] = {
            "disponible": False,
            "motivo": f"los casos evaluados no contienen {len(faltan)} de los "
                      f"{len(ids_v1)} ids del eval v1 (faltan "
                      f"{', '.join(faltan[:5])}...), de modo que no hay "
                      f"subconjunto comun con las once corridas anteriores.",
        }
        return sc

    trio = [(e, s, i) for i, (e, s) in enumerate(zip(casos, salidas))
            if e["id"] in ids_v1]
    ev1 = [e for e, _, _ in trio]
    sa1 = [s for _, s, _ in trio]

    # Sin juez: las dimensiones 1 y 3 son deterministas y gratis de recalcular.
    sc_v1 = harness(ev1, sa1, f"{etiqueta} · subconjunto v1", juez=None)
    if juez is not None:
        notas_v1 = [sc["juez"]["notas"][i] for _, _, i in trio]
        sc_v1["juez"] = resumen_juez(notas_v1, sa1, ev1, juez.modelo)

    def mide(x: dict) -> dict:
        out = {
            "n": x["n"],
            "acc_mecanismo": round(x["campos"]["mecanismo"]["accuracy"], 4),
            "macroF1_mecanismo": round(x["campos"]["mecanismo"]["macro_f1"], 4),
            "baseline_mayoritaria": round(
                x["campos"]["mecanismo"]["baseline_mayoritaria"], 4),
            "acierto_juridico": round(x["acierto_juridico"], 4),
        }
        if x.get("juez"):
            out["juez_nota_media"] = round(x["juez"]["nota_media"], 3)
        return out

    a, b = mide(sc_v1), mide(sc)
    # La columna completa se nombra por lo que ES, no "v2": cuando se pasa
    # `eval_set + eval_m3` son 84 casos de DOS eval sets, y llamarla v2 seria
    # afirmar algo falso.
    es_v2_puro = len(presentes) == len(ids_v1) + 23
    sc["puente"] = {
        "disponible": True,
        "subconjunto_v1": a,
        "completo": b,
        "completo_es_eval_v2": es_v2_puro,
        "delta": {k: round(b[k] - a[k], 4) for k in a if k != "n"},
        "lectura":
            "las dos columnas salen de las MISMAS predicciones y de las MISMAS "
            "notas del juez, asi que la diferencia es atribuible solo a los "
            "casos que el conjunto completo tiene de mas, no a variacion del "
            "modelo ni del juez entre corridas. `subconjunto_v1` es comparable "
            "con las once corridas anteriores. Una caida en la columna completa "
            "es la esperada cuando esta es el eval v2: v2 tiene mas casos de "
            "las clases minoritarias, que son las dificiles, y su baseline "
            "mayoritaria es 0.4286 contra 0.587 de v1.",
    }
    return sc


# --------------------------------------------------------------------------
# Experimentos de sesgo. Producen la evidencia que pide la rúbrica.
# --------------------------------------------------------------------------
def sesgo_posicion(juez, eval_set, salidas_a, salidas_b, n=12) -> dict:
    """¿Cambia el veredicto al invertir el orden de las respuestas?

    Tasa de inconsistencia alta = el juez atiende a la posición, no al contenido.
    La mitigación es preguntar en los dos órdenes y descartar lo inconsistente.
    """
    res = [juez.comparar_sin_sesgo_posicion(e["relato"], schema.render_salida(e), a, b)
           for e, a, b in zip(eval_set[:n], salidas_a[:n], salidas_b[:n])]
    juez.guardar_cache()

    legibles = [r for r in res if r["veredicto"] != "ilegible"]
    inconsistentes = sum(r["veredicto"] == "inconsistente" for r in res)

    # Preferencia por la POSICIÓN A, no por un sistema concreto: se cuenta sobre
    # las 2n preguntas, porque en cada orden la posición A la ocupa uno distinto.
    # 50% = sin sesgo. La versión anterior contaba "cuántas ganó el sistema x",
    # que es otra cosa y no mide sesgo de posición.
    votos = [v for r in res for v in r["eligio_A"]]
    return {
        "n": len(res),
        "preguntas": len(votos),
        "ilegibles": len(res) - len(legibles),
        "inconsistentes": inconsistentes,
        "tasa_inconsistencia": inconsistentes / len(legibles) if legibles else 0.0,
        # None, NO 0.5, cuando no hubo inconsistencias.
        #
        # Con cero veredictos inconsistentes esta cifra sale 0.5 por aritmetica
        # forzosa: cada veredicto consistente elige A en exactamente una de las
        # dos preguntas, asi que la suma es siempre la mitad. Reportar 0.5 y
        # leerlo como "no hay sesgo de posicion" es decir dos veces el mismo
        # hecho --- el que ya dice `inconsistentes: 0` --- y presentarlo como
        # dos pruebas. Solo informa cuando hay inconsistencias que repartir.
        "preferencia_posicion_A": (sum(votos) / len(votos)
                                   if votos and inconsistentes else None),
        "preferencia_posicion_A_lectura": (
            "indefinida a proposito: con 0 inconsistentes esta fraccion vale "
            "0.5 por construccion y no aporta nada sobre el sesgo. Lo que lo "
            "mide es `tasa_inconsistencia`."
            if not inconsistentes else
            "fraccion de las preguntas en que eligio la respuesta mostrada "
            "primero; 0.5 es ausencia de sesgo de posicion"),
        "veredictos": dict(Counter(r["veredicto"] for r in res)),
        "detalle": res,
    }


def sesgo_autopreferencia(juez, eval_set, salidas_familia_juez: list[str],
                          salidas_ajeno: list[str], n: int = 15,
                          etq_familia: str = "familia del juez",
                          etq_ajeno: str = "sistema evaluado") -> dict:
    """¿El juez prefiere las respuestas de su propia familia de modelos?

    POR QUÉ ESTE ERA EL SESGO QUE FALTABA

    De los cuatro sesgos, este era el único MITIGADO pero no MEDIDO: el juez es
    `openai/gpt-oss-120b` y Qwen quedó excluido a propósito como juez porque el
    sistema evaluado es Qwen2.5-7B. Esa decisión es correcta y no estaba
    comprobada: mitigar sin medir deja sin saber de qué tamaño era el problema
    que se evitó.

    EL CONFUNDIDO, Y CÓMO SE CONTROLA

    Si el juez prefiere las respuestas de gpt-oss, puede ser auto-preferencia
    --- o puede ser que gpt-oss-120b sea de verdad mejor que un Qwen de 7B
    ajustado. Contar preferencias a secas no distingue las dos cosas y no
    prueba nada.

    Aquí se CONDICIONA en la verdad de dominio, que sí conocemos: para cada
    caso sabemos si cada respuesta acertó el mecanismo. Eso parte los pares en
    cuatro estratos y el que importa es el primero:

      empate_correctas   las dos aciertan. La calidad objetiva está empatada,
                         así que cualquier preferencia sistemática aquí es
                         auto-preferencia y no mérito. **Este es el número.**
      empate_fallan      las dos fallan. Mismo razonamiento, segunda lectura.
      gana_familia       solo acierta la de la familia del juez: preferirla es
                         lo correcto, no sesgo.
      gana_ajeno         solo acierta la ajena. Si el juez aun así prefiere la
                         de su familia, es la evidencia MÁS fuerte de sesgo.

    Se pregunta en los dos órdenes y lo inconsistente se descarta, igual que en
    `sesgo_posicion`: sin eso, el sesgo de posición se colaría dentro de esta
    medición.

    EL ESTRATO QUE IMPORTA SE CONSTRUYE, NO SE ESPERA

    La corrida m2/20261019T034128Z midio este sesgo con n=15 y salio
    `indefinida` con **n=2 en `empate_correctas`**: de los 15 pares, 12
    cayeron en `gana_ajeno` porque `gpt-oss-20b` pierde casi siempre contra el
    Qwen afinado, 1 en `empate_fallan` y solo 2 en el estrato decisivo. El
    intervalo salio [0.0, 0.6576]: no dice nada.

    El defecto NO era el tamano de la muestra: era tomar los primeros `n`
    casos y confiar en que cayeran donde hace falta. Clasificar un par en su
    estrato es GRATIS --- se compara el mecanismo con el gold, sin llamar al
    juez --- asi que ahora se clasifican TODOS los casos primero y las
    llamadas se gastan empezando por `empate_correctas`.

    POR QUE ESTO NO SESGA LA MEDICION
      Se selecciona por la VERDAD DE DOMINIO (si cada respuesta acerto el
      mecanismo), que es independiente del veredicto del juez. Seleccionar
      por el veredicto si lo sesgaria --- seria elegir los casos donde el
      juez ya hizo lo que queremos medir. Esta es la diferencia entre
      estratificar y hacer trampa, y por eso el artefacto publica
      `disponibles_por_estrato`: `por_estrato` ya NO es una muestra aleatoria
      y leerlo como tal seria un error.

    Cuesta 2 llamadas por par. `n` es el presupuesto total de pares.
    """
    # --- 1 · clasificar TODO sin gastar una sola llamada ------------------
    todos = list(zip(eval_set, salidas_familia_juez, salidas_ajeno))
    por_estrato_disp = {k: [] for k in ("empate_correctas", "empate_fallan",
                                        "gana_familia", "gana_ajeno")}
    for e, sf, sa in todos:
        ok_f = schema.parse_salida(sf).get("mecanismo") == e["mecanismo"]
        ok_a = schema.parse_salida(sa).get("mecanismo") == e["mecanismo"]
        if ok_f and ok_a:
            est = "empate_correctas"
        elif not ok_f and not ok_a:
            est = "empate_fallan"
        elif ok_f:
            est = "gana_familia"
        else:
            est = "gana_ajeno"
        por_estrato_disp[est].append((e, sf, sa, ok_f, ok_a))

    # --- 2 · gastar el presupuesto empezando por el estrato decisivo -----
    # El orden no es arbitrario: `empate_correctas` es donde una preferencia
    # ES sesgo; `gana_ajeno` es la segunda evidencia mas fuerte; los otros dos
    # se informan para que el cuadro este completo, no porque midan el sesgo.
    PRIORIDAD = ("empate_correctas", "empate_fallan", "gana_ajeno",
                 "gana_familia")
    pares = []
    for est in PRIORIDAD:
        for fila in por_estrato_disp[est]:
            if len(pares) >= n:
                break
            pares.append((est, *fila))

    estratos = {k: {"n": 0, "prefiere_familia": 0, "prefiere_ajeno": 0,
                    "empate": 0, "inconsistente": 0}
                for k in por_estrato_disp}
    detalle = []
    for est, e, sf, sa, ok_f, ok_a in pares:
        r = juez.comparar_sin_sesgo_posicion(
            e["relato"], schema.render_salida(e), sf, sa)
        d = estratos[est]
        d["n"] += 1
        if r["veredicto"] == "x":
            d["prefiere_familia"] += 1
        elif r["veredicto"] == "y":
            d["prefiere_ajeno"] += 1
        elif r["veredicto"] == "inconsistente":
            d["inconsistente"] += 1
        else:
            d["empate"] += 1
        detalle.append({"id": e["id"], "estrato": est,
                        "acerto_familia": ok_f, "acerto_ajeno": ok_a,
                        "veredicto": r["veredicto"]})
    juez.guardar_cache()

    emp = estratos["empate_correctas"]
    decididos = emp["prefiere_familia"] + emp["prefiere_ajeno"]
    tasa = emp["prefiere_familia"] / decididos if decididos else None
    ic = (metricas.bootstrap_ic(
        [True] * emp["prefiere_familia"] + [False] * emp["prefiere_ajeno"])
        if decididos else None)

    return {
        "n": len(pares),
        "modelo_juez": juez.modelo,
        "etiquetas": {"x": etq_familia, "y": etq_ajeno},
        # CUANTOS HABIA de cada estrato, frente a cuantos se midieron. Sin
        # esto, `por_estrato` se lee como una muestra aleatoria y NO lo es:
        # el presupuesto se gasta a proposito empezando por el estrato donde
        # una preferencia es sesgo. Un lector que no lo sepa concluiria, por
        # ejemplo, que `gana_ajeno` casi no ocurre --- cuando lo que pasa es
        # que se midio al final de la cola.
        "disponibles_por_estrato": {k: len(v)
                                    for k, v in por_estrato_disp.items()},
        "seleccion": {
            "estratificada": True,
            "prioridad": list(PRIORIDAD),
            "presupuesto_pares": n,
            "casos_disponibles": len(todos),
            "por_que": (
                "clasificar un par en su estrato es gratis (compara el "
                "mecanismo contra el gold, sin llamar al juez), asi que las "
                "llamadas se gastan empezando por `empate_correctas`, que es "
                "el unico estrato donde una preferencia sistematica ES "
                "sesgo. Se selecciona por VERDAD DE DOMINIO, que es "
                "independiente del veredicto del juez: seleccionar por el "
                "veredicto si sesgaria la medicion."),
            "antes": (
                "m2/20261019T034128Z tomaba los primeros 15 casos y salio "
                "`indefinida` con n=2 en el estrato decisivo, IC "
                "[0.0, 0.6576]"),
        },
        "por_estrato": estratos,
        # El titular: preferencia por la familia del juez cuando la calidad
        # objetiva está EMPATADA. 0.5 = sin auto-preferencia.
        "preferencia_familia_con_calidad_empatada": (
            round(tasa, 4) if tasa is not None else "indefinida"),
        "ic": ic,
        "n_decididos_en_el_empate": decididos,
        "lectura":
            "el numero que importa es `preferencia_familia_con_calidad_"
            "empatada`: 0.5 es ausencia de auto-preferencia. Fuera del estrato "
            "de empate la preferencia puede ser merito y no sesgo, por eso no "
            "se agrega todo en una sola cifra. `indefinida` significa que no "
            "hubo pares con las dos respuestas correctas y el experimento no "
            "puede informar: con n pequeno pasa, y es mejor decirlo que "
            "promediar estratos que miden cosas distintas.",
        "detalle": detalle,
    }


def _lectura_familias(a: str, b: str) -> dict:
    """De que linaje es cada juez, y que se puede concluir de eso."""
    try:
        from juez import FAMILIA, misma_familia
    except ImportError:                                     # noqa: BLE001
        return {"conocido": False,
                "nota": "no se pudo leer `juez.FAMILIA`"}
    misma = misma_familia(a, b)
    if misma is None:
        return {"conocido": False, "familia_a": FAMILIA.get(a),
                "familia_b": FAMILIA.get(b),
                "nota": "alguno de los dos modelos no esta en `juez.FAMILIA`: "
                        "no se puede afirmar si son parientes, y por tanto "
                        "tampoco que esta cifra controle sesgo compartido."}
    return {
        "conocido": True,
        "familia_a": FAMILIA[a], "familia_b": FAMILIA[b],
        "misma_familia": misma,
        "que_mide": (
            "RUIDO del juez, no sesgo: los dos jueces son de la misma "
            "familia, asi que un acuerdo alto es compatible con que los dos "
            "se equivoquen igual."
            if misma else
            "ruido Y sesgo compartido de familia: al ser de linajes "
            "distintos, coincidir es una senal mas fuerte de que la nota es "
            "una propiedad de la respuesta y no del juez."),
    }


def acuerdo_entre_jueces(notas_a: list[dict], notas_b: list[dict],
                         modelo_a: str, modelo_b: str) -> dict:
    """¿Dos jueces distintos dan la misma nota? (ROADMAP #22)

    Una nota de un solo juez no tiene medida de su propia fiabilidad. Esto la
    da: si dos modelos distintos coinciden, la nota es una propiedad de la
    respuesta; si no, es una propiedad del juez, y entonces no se puede
    reportar sola.

    Se informan tres cosas porque miden distinto:

      acuerdo_exacto   coinciden en la nota 1-5. Es exigente y suele ser bajo.
      kappa_aprueba    acuerdo en la decisión binaria (nota >= 4) corregido por
                       azar. Es la que importa, porque es la decisión que el
                       harness usa.
      corr_spearman    si ORDENAN igual, aunque usen la escala distinto. Un
                       juez severo y otro generoso pueden ordenar idéntico, y
                       para comparar sistemas eso basta.
    """
    pares = [(a["nota"], b["nota"]) for a, b in zip(notas_a, notas_b)
             if a["nota"] is not None and b["nota"] is not None]
    if not pares:
        return {"n": 0, "concluyente": False,
                "motivo": "ningun caso con nota valida en los dos jueces"}
    va, vb = [p[0] for p in pares], [p[1] for p in pares]
    k = cohen_kappa([x >= 4 for x in va], [x >= 4 for x in vb])
    return {
        "n": len(pares),
        "concluyente": True,
        "modelo_a": modelo_a, "modelo_b": modelo_b,
        # LA CIFRA NO SE PUEDE INTERPRETAR SIN SABER SI SON PARIENTES.
        #
        # El acuerdo entre jueces controla el RUIDO de un juez; no controla el
        # SESGO que dos modelos de la misma familia comparten. Una kappa alta
        # entre dos gpt-oss es compatible con que los dos se equivoquen igual.
        # Medido en m2/20261018T080311Z: gpt-oss-120b contra gpt-oss-20b,
        # kappa 0.6835 --- real, pero midiendo menos de lo que su nombre
        # sugiere. Va dentro del artefacto para que nadie lo lea sin esto.
        "_familias": _lectura_familias(modelo_a, modelo_b),
        "media_a": round(sum(va) / len(va), 3),
        "media_b": round(sum(vb) / len(vb), 3),
        "acuerdo_exacto": round(sum(x == y for x, y in pares) / len(pares), 4),
        "acuerdo_a_un_punto": round(
            sum(abs(x - y) <= 1 for x, y in pares) / len(pares), 4),
        "kappa_aprueba": round(k, 4) if k is not None else "indefinido",
        "corr_spearman": _spearman(va, vb),
        "sin_nota_en_alguno": len(notas_a) - len(pares),
        "lectura":
            "`kappa_aprueba` es la cifra que importa: mide el acuerdo en la "
            "decision binaria que el harness usa (nota >= 4), corregida por "
            "azar. `indefinido` significa que uno de los dos jueces uso una "
            "sola categoria, y entonces la kappa vale 0.0 mecanicamente y no "
            "distingue acuerdo de desacuerdo. Una diferencia grande de medias "
            "con buena correlacion significa que los jueces ORDENAN igual pero "
            "calibran distinto: para comparar sistemas sirve, para reportar una "
            "nota absoluta no.",
    }


def _spearman(a: list[float], b: list[float]) -> float | None:
    """Correlación de Spearman. None si alguno no varía."""
    def rangos(v):
        orden = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[orden[j + 1]] == v[orden[i]]:
                j += 1
            medio = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[orden[k]] = medio
            i = j + 1
        return r

    if len(set(a)) < 2 or len(set(b)) < 2:
        return None
    ra, rb = rangos(a), rangos(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = sum((x - ma) ** 2 for x in ra) ** 0.5
    db = sum((y - mb) ** 2 for y in rb) ** 0.5
    return round(num / (da * db), 4) if da and db else None


RELLENO_FORENSE = (
    " En efecto, conforme a reiterada jurisprudencia constitucional y a los "
    "principios que informan el ordenamiento, resulta imperioso señalar que "
    "la situación descrita comporta una afectación que amerita análisis "
    "detenido por parte del juez de conocimiento, sin perjuicio de las demás "
    "consideraciones que resulten aplicables al caso concreto.")

# Una razón que SUENA jurídica y no sostiene nada: es circular, apela a la
# gravedad en abstracto y no menciona el hecho del que depende la decisión.
# Es el defecto que de verdad hay que detectar, porque es el que un sistema
# verboso produce de forma natural.
RAZON_HUECA = (
    "la situación descrita reviste la gravedad suficiente para activar los "
    "mecanismos de protección previstos en el ordenamiento, toda vez que los "
    "derechos invocados ostentan rango constitucional y su salvaguarda resulta "
    "imperativa conforme a los principios de prevalencia del derecho sustancial "
    "y de efectividad de las garantías")


def sesgo_longitud(juez, eval_set, n=10, nivel: str = "sutil") -> dict:
    """Respuesta correcta y breve contra respuesta larga. Dos niveles.

    Si el juez premia la larga, está midiendo verbosidad. La mitigación es la
    regla explícita de la rúbrica ("la extensión NO es calidad"), y esta prueba
    es la evidencia de que la regla hace efecto.

    POR QUÉ DOS NIVELES

    La primera versión solo tenía el nivel `obvio`: a la respuesta larga se le
    CAMBIABA el mecanismo. Eso la vuelve detectable sin leer el razonamiento
    --- basta comparar la etiqueta con la referencia --- así que el 10/10 que
    sacó estaba garantizado y no probaba nada sobre el sesgo de longitud. Un
    test que se pasa perfecto porque es fácil no es evidencia de ausencia de
    sesgo.

      obvio   mecanismo CAMBIADO + relleno. Se conserva por continuidad con las
              corridas anteriores, y como control de cordura: si el juez falla
              aquí, está roto y lo demás no se puede interpretar.
      sutil   mecanismo y procedencia CORRECTOS, razón HUECA + relleno. El
              único defecto está en el razonamiento, que es justo lo que la
              rúbrica dice que hay que calificar. Aquí sí se mide el sesgo.

    `nivel="ambos"` corre los dos y devuelve también la comparación, que es la
    lectura interesante: pasar el obvio y fallar el sutil significa que el juez
    compara etiquetas y no razonamientos.
    """
    if nivel == "ambos":
        obvio = sesgo_longitud(juez, eval_set, n, "obvio")
        sutil = sesgo_longitud(juez, eval_set, n, "sutil")
        return {
            "obvio": obvio, "sutil": sutil,
            "delta_tasa": round(sutil["tasa_sesgo_longitud"]
                                - obvio["tasa_sesgo_longitud"], 4),
            "lectura":
                "si el juez pasa `obvio` y falla `sutil`, no está evaluando el "
                "razonamiento: está comparando la etiqueta del mecanismo con la "
                "de la referencia. El `sutil` es el que mide sesgo de longitud; "
                "el `obvio` es control de cordura.",
        }
    if nivel not in ("obvio", "sutil"):
        raise ValueError(f"nivel desconocido: {nivel}")

    gana_corta = gana_larga = empates = ilegibles = 0
    detalle = []
    for e in eval_set[:n]:
        correcta_breve = schema.render_salida(e)
        mal = dict(e)
        if nivel == "obvio":
            mal["mecanismo"] = ("accion_popular" if e["mecanismo"] != "accion_popular"
                                else "via_ordinaria")
            mal["procede"] = mal["mecanismo"] == "tutela"
        else:
            # Mecanismo y procedencia intactos: el defecto es SOLO la razón.
            mal["razon"] = RAZON_HUECA
        larga = schema.render_salida(mal) + RELLENO_FORENSE

        r = juez.comparar_sin_sesgo_posicion(
            e["relato"], schema.render_salida(e), correcta_breve, larga)
        detalle.append({"id": e["id"],
                        **{k: r[k] for k in ("veredicto", "consistente")}})
        if r["veredicto"] == "x":
            gana_corta += 1
        elif r["veredicto"] == "y":
            gana_larga += 1
        elif r["veredicto"] == "ilegible":
            ilegibles += 1
        else:
            empates += 1
    juez.guardar_cache()

    # La tasa se calcula sobre los casos DECIDIDOS: meter los ilegibles en el
    # denominador la haría bajar por una razón falsa.
    decididos = gana_corta + gana_larga
    largo_extra = len(RELLENO_FORENSE) + (len(RAZON_HUECA) if nivel == "sutil" else 0)
    return {
        "nivel": nivel,
        "n": len(detalle),
        "gana_correcta_breve": gana_corta,
        "gana_larga": gana_larga,
        # Nombre anterior, conservado para no romper el notebook ni los
        # artefactos de las corridas previas.
        "gana_equivocada_larga": gana_larga,
        # `empates` ES UN NOMBRE EQUIVOCADO y se conserva solo porque los
        # artefactos de las corridas anteriores lo llevan. Lo que cuenta en esa
        # casilla son los veredictos INCONSISTENTES: el juez dio respuestas
        # contrarias segun el orden en que se le presentaron las dos. Un empate
        # seria "las veo equivalentes"; esto es "me contradigo".
        #
        # La diferencia importa, y esta medida. En m2/20261016T214908Z el nivel
        # sutil dio 4 inconsistentes de 10, contra 0 de 12 en el test de
        # posicion --- mismo juez, mismo protocolo de preguntar en los dos
        # ordenes. El juez es estable cuando la diferencia es obvia y deja de
        # serlo cuando es sutil, que es justo donde hace falta que no lo sea.
        "empates": empates,
        "inconsistentes": empates,
        "ilegibles": ilegibles,
        # La tasa va sobre los DECIDIDOS, asi que por si sola esconde cuantos
        # no se decidieron: un 16.7% sobre 6 de 10 se lee igual que un 16.7%
        # sobre 10 de 10 y no significan lo mismo. Esta segunda cifra es la que
        # lo dice.
        "tasa_estabilidad": (decididos / (len(detalle) - ilegibles)
                             if len(detalle) - ilegibles else 0.0),
        "tasa_sesgo_longitud": gana_larga / decididos if decididos else 0.0,
        "chars_extra_de_la_larga": largo_extra,
        "que_falla_en_la_larga": ("el mecanismo, detectable sin leer el razonamiento"
                                  if nivel == "obvio" else
                                  "solo el razonamiento: el mecanismo es correcto"),
        "detalle": detalle,
    }


# --------------------------------------------------------------------------
def a_csv(scorecards: list[dict], ruta: str = "runs/scorecard_baseline.csv") -> None:
    """Una fila por sistema. Es el entregable scorecard_baseline.csv de M2."""
    filas = []
    for sc in scorecards:
        f = {
            "sistema": sc["sistema"],
            "n": sc["n"],
            "acc_derecho": round(sc["campos"]["derecho"]["accuracy"], 4),
            "acc_mecanismo": round(sc["campos"]["mecanismo"]["accuracy"], 4),
            "acc_procede": round(sc["campos"]["procede"]["accuracy"], 4),
            "macroF1_mecanismo": round(sc["campos"]["mecanismo"]["macro_f1"], 4),
            "baseline_mayoritaria": round(sc["campos"]["mecanismo"]["baseline_mayoritaria"], 4),
            "rouge_l": round(sc["rouge_l"], 4),
            "similitud_embeddings": (round(sc["similitud_embeddings"], 4)
                                     if sc.get("similitud_embeddings") is not None
                                     else "no disponible"),
            "adherencia_estructural": round(sc["adherencia_estructural"], 4),
            "adherencia_vocabulario": round(sc["adherencia_vocabulario"], 4),
            "coherencia": (round(sc["coherencia"], 4)
                           if sc.get("coherencia") is not None else "no evaluable"),
            "acierto_juridico": round(sc["acierto_juridico"], 4),
            "acierto_gold": round(sc["por_tipo"].get("gold", {}).get("acierto_juridico", 0), 4),
            "acierto_adversarial": round(sc["por_tipo"].get("adversarial", {}).get("acierto_juridico", 0), 4),
            "tasa_alucinacion": round(sc["alucinacion_normativa"]["tasa_alucinacion"], 4),
            "tasa_alucinacion_salida": round(
                sc["alucinacion_normativa"]["tasa_alucinacion_salida"], 4),
            "inventadas_fuera_del_fundamento": sum(
                n for _, n in sc["alucinacion_normativa"]["inventadas_fuera_del_fundamento"]),
            "precision_citas": round(sc["pertinencia_citas"]["precision_citas"], 4),
            "recall_citas": round(sc["pertinencia_citas"]["recall_citas"], 4),
            "citas_impertinentes": sc["pertinencia_citas"]["impertinentes"],
        }
        # Los dos planos de la cita, cuando el gold los trae separados
        # (data/anotar_fundamentos.py). El agregado `precision_citas` los
        # mezcla, y mezclarlos contaba como impertinente el art. 86 CP en los
        # casos de tutela. Columnas ADITIVAS: las anteriores no se mueven.
        pp = sc["pertinencia_citas"].get("por_plano", {})
        if pp.get("disponible"):
            f.update({
                "precision_citas_mecanismo": (
                    round(pp["precision_mecanismo"], 4)
                    if pp["precision_mecanismo"] is not None else "no medible"),
                "precision_citas_fondo": (
                    round(pp["precision_derecho"], 4)
                    if pp["precision_derecho"] is not None else "no medible"),
                "citas_via_equivocada": pp["cajas"].get("mecanismo_equivocado", 0),
            })
        j = sc.get("juez")
        if j:
            f["juez_nota_media"] = round(j["nota_media"], 3)
            f["juez_nota_gold"] = round(j["nota_media_por_tipo"].get("gold", 0), 3)
            f["juez_nota_adversarial"] = round(j["nota_media_por_tipo"].get("adversarial", 0), 3)
            k = j["kappa_vs_dominio"]
            f["juez_kappa_vs_dominio"] = round(k, 3) if k is not None else "indefinido"
            f["juez_sin_parsear"] = j["sin_parsear"]
        filas.append(f)

    campos = list(filas[0].keys())
    with open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print(f"{ruta} · {len(filas)} filas · {len(campos)} columnas")


def guardar(sc: dict, ruta: str) -> None:
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(sc, f, ensure_ascii=False, indent=2)
