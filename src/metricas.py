"""
Metricas del dominio. Las comparten M1 (baseline vs fine-tuned), M2 (harness)
y M3 (RAG), para que el delta entre modulos sea comparable.

Unica dependencia externa: `sentence-transformers`, y es OPCIONAL - solo la usa
la similitud por embeddings, que devuelve None si no esta instalada. El resto
corre con la libreria estandar en Colab, en local y en la maquina de otro equipo.
"""
from __future__ import annotations
import json
import math
import random
import re
from collections import Counter, defaultdict
from functools import lru_cache

from schema import (CAMPOS_SALIDA, DERECHO_ESCAPE, DERECHOS, MECANISMOS,
                    cargar_normas, citas, etiquetas_presentes, parse_salida,
                    planos_normativos)

CAMPOS_CATEGORICOS = ["derecho", "mecanismo", "procede"]


# --------------------------------------------------------------------------
# Métricas base
# --------------------------------------------------------------------------
def accuracy(pred: list, gold: list) -> float:
    if not gold:
        return 0.0
    return sum(p == g for p, g in zip(pred, gold)) / len(gold)


def bootstrap_ic(aciertos: list[bool], nivel: float = 0.95,
                 remuestreos: int = 2000, semilla: int = 42) -> dict:
    """Intervalo de confianza de una proporción, por bootstrap percentil.

    POR QUÉ HACE FALTA

    El eval set tiene n=63 juzgables y el estrato adversarial n=18. Con esos
    tamaños, una diferencia de uno o dos casos entre dos brazos mueve la
    accuracy entre 1.6 y 5.6 puntos, y la tabla la presentaba como si fuera un
    resultado. No lo es: está dentro del ruido del muestreo.

    Un IC no convierte una diferencia pequeña en significativa ni al contrario;
    sirve para no leer como hallazgo lo que es azar. Si los intervalos de dos
    brazos se solapan ampliamente, la tabla no sostiene que uno sea mejor.

    Bootstrap y no la normal de Wald porque con proporciones cerca de 0 o de 1
    --- que aquí pasa: `acierto_gold` da 1.000 en varios brazos --- Wald da
    intervalos que se salen de [0, 1]. El percentil del bootstrap no puede.

    `semilla` fija hace el IC reproducible, que es condición para publicarlo.
    """
    n = len(aciertos)
    if n == 0:
        return {"n": 0, "punto": 0.0, "ic_bajo": 0.0, "ic_alto": 0.0,
                "amplitud": 0.0}
    punto = sum(aciertos) / n
    if n == 1:
        return {"n": 1, "punto": punto, "ic_bajo": 0.0, "ic_alto": 1.0,
                "amplitud": 1.0,
                "nota": "n=1: el intervalo es todo el rango, no hay informacion"}

    # El bootstrap DEGENERA cuando todas las observaciones son iguales: cada
    # remuestreo devuelve la misma proporción, la varianza es cero y el
    # intervalo sale [1.0, 1.0] o [0.0, 0.0]. Eso se lee como "certeza
    # absoluta" y es lo contrario: con 45 aciertos de 45 el intervalo real
    # ronda [0.92, 1.0]. Publicar [1.0, 1.0] ahí sería inventar precisión,
    # igual que informar kappa 0.0 cuando el estadístico no puede variar.
    # En ese caso se usa Wilson, que está bien definido en los extremos.
    if len(set(aciertos)) < 2:
        # WILSON SOLO ESTA DEFINIDO PARA UNA PROPORCION: `k` exitos de `n`.
        #
        # Esta función se escribió para proporciones y se acabó usando con
        # valores que no lo son: los MARGENES de `juez.experimento_validez`
        # son diferencias de nota (2, 3, -1...). Con ellos
        # `_wilson(sum(aciertos), n)` recibe k > n --- 20 "exitos" de 10 ---
        # y revienta con `ValueError: math domain error`. Medido al integrar
        # la sonda de validez.
        #
        # La aritmética de arriba (media y percentiles del bootstrap) sí vale
        # para cualquier lista numérica, así que la función se queda; lo que
        # se separa es el caso degenerado, que es el único que necesita saber
        # de qué tipo son los datos.
        if set(aciertos) <= {0, 1, True, False}:
            return {**_wilson(sum(aciertos), n, nivel), "n": n,
                    "punto": round(punto, 4), "metodo": "wilson",
                    "nota": "todas las observaciones son iguales, asi que el "
                            "bootstrap no puede variar y daria un intervalo "
                            "de amplitud cero. Se informa Wilson, que si esta "
                            "definido en los extremos."}
        # No es una proporción y no varía: no hay intervalo que estimar. Se
        # dice, en vez de inventar [v, v] --- que se leería como certeza
        # absoluta y es lo contrario --- o de reventar.
        return {"n": n, "punto": round(punto, 4),
                "ic_bajo": None, "ic_alto": None, "amplitud": None,
                "metodo": "sin estimar",
                "nota": "los valores son todos iguales y NO son una "
                        "proporcion, asi que el bootstrap no puede variar y "
                        "Wilson no aplica. El punto es exacto; el intervalo "
                        "no se estima."}

    rnd = random.Random(semilla)
    medias = []
    for _ in range(remuestreos):
        s = sum(aciertos[rnd.randrange(n)] for _ in range(n))
        medias.append(s / n)
    medias.sort()
    a = (1 - nivel) / 2
    bajo = medias[int(a * (remuestreos - 1))]
    alto = medias[int((1 - a) * (remuestreos - 1))]
    return {"n": n, "punto": round(punto, 4),
            "ic_bajo": round(bajo, 4), "ic_alto": round(alto, 4),
            "amplitud": round(alto - bajo, 4), "nivel": nivel,
            "metodo": "bootstrap_percentil",
            "remuestreos": remuestreos, "semilla": semilla}


def _wilson(k: int, n: int, nivel: float = 0.95) -> dict:
    """Intervalo de Wilson para una proporción. Siempre dentro de [0, 1]."""
    z = 2.5758 if nivel >= 0.99 else (1.9600 if nivel >= 0.95 else 1.6449)
    centro = (k + z * z / 2) / (n + z * z)
    medio = (z / (n + z * z)) * math.sqrt(k * (n - k) / n + z * z / 4)
    return {"ic_bajo": round(max(0.0, centro - medio), 4),
            "ic_alto": round(min(1.0, centro + medio), 4),
            "amplitud": round(min(1.0, centro + medio) - max(0.0, centro - medio), 4),
            "nivel": nivel}


def ic_se_solapan(a: dict, b: dict) -> bool:
    """¿Los dos intervalos se solapan? Si sí, la diferencia no se sostiene.

    No es una prueba de hipótesis --- para eso haría falta el bootstrap de la
    DIFERENCIA, no comparar dos intervalos marginales --- pero es la lectura
    conservadora y suficiente para no sobreinterpretar la tabla.
    """
    return not (a["ic_alto"] < b["ic_bajo"] or b["ic_alto"] < a["ic_bajo"])


def f1_por_clase(pred: list, gold: list) -> dict[str, dict]:
    """F1 por clase. Una clase sin soporte ni predicciones se omite."""
    clases = set(gold) | {p for p in pred if p is not None}
    out = {}
    for c in clases:
        tp = sum(p == c and g == c for p, g in zip(pred, gold))
        fp = sum(p == c and g != c for p, g in zip(pred, gold))
        fn = sum(p != c and g == c for p, g in zip(pred, gold))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        out[str(c)] = {"precision": prec, "recall": rec, "f1": f1,
                       "soporte": sum(g == c for g in gold)}
    return out


# --------------------------------------------------------------------------
# EL FALSO NEGATIVO QUE DE VERDAD CUESTA
#
# La accuracy y el macro-F1 tratan los seis mecanismos como si equivocarse en
# cualquiera costara lo mismo. No cuesta lo mismo.
#
# Decirle "vaya a la justicia ordinaria" a alguien que esta DETENIDO sin orden
# judicial, o a alguien con un derecho fundamental vulnerado y sin otro medio,
# es cerrarle la puerta al unico mecanismo que lo protegia. El error inverso
# --- sugerir una tutela donde procedia la via ordinaria --- cuesta un trámite
# y un auto de rechazo.
#
# Esa asimetria es la misma que `sistema.DEFECTO_PRO_HOMINE` ya declara en el
# motor de reglas, y hasta ahora no estaba en NINGUNA metrica: el scorecard
# publicaba F1 por clase, donde el recall de habeas corpus pesa igual que la
# precision de accion popular.
#
# El equipo de comparacion si reporta su clase critica (recall de urgentes
# 0.70, por debajo de su propia meta de 0.85). Aqui el equivalente son dos
# clases y se publica con intervalo, porque es una proporcion sobre un soporte
# pequeno y un caso vale varios puntos.
CLASES_CRITICAS = ("habeas_corpus", "tutela")
"""Las clases donde un FALSO NEGATIVO le niega proteccion a alguien.

`habeas_corpus`: art. 30 CP, privacion de la libertad. Es el error mas caro
del sistema y no admite comparacion con los demas.

`tutela`: art. 86 CP. Un falso negativo manda a la via ordinaria a quien no
tenia otro medio eficaz, que es justo el supuesto que la tutela cubre.

NO estan `accion_popular` ni `accion_cumplimiento`: su falso negativo manda a
alguien a otra accion constitucional, no lo deja sin ninguna. Y no esta
`via_ordinaria`, cuyo falso negativo es el error BARATO --- una tutela de mas.
"""


def recall_clase_critica(pred: list, gold: list, nivel: float = 0.95) -> dict:
    """Recall de las clases cuyo falso negativo le niega proteccion a alguien.

    POR QUE RECALL Y NO F1

    El F1 promedia precision y recall, y aqui no son intercambiables. Un falso
    negativo en habeas corpus deja a una persona detenida sin la unica via que
    la amparaba; un falso positivo le hace perder un trámite. Promediarlos
    oculta la asimetria que el proyecto declara en todas partes menos en sus
    cifras.

    Devuelve el recall POR CLASE y el agregado sobre la union, los dos con
    intervalo: son proporciones sobre soportes de dos digitos, asi que un caso
    vale varios puntos y publicar el punto solo invita a sobreleerlo.

    `fallos` nombra los casos, porque un recall de 0.93 sobre soporte 15 son
    exactamente dos personas y el objetivo es poder leerlos, no contarlos.
    """
    porc = f1_por_clase(pred, gold)
    detalle, tp_tot, n_tot = {}, 0, 0
    for c in CLASES_CRITICAS:
        d = porc.get(c)
        if not d or not d["soporte"]:
            detalle[c] = {"soporte": 0, "recall": None,
                          "motivo": "la clase no tiene soporte en este "
                                    "conjunto: no hay nada que medir"}
            continue
        tp = sum(p == c and g == c for p, g in zip(pred, gold))
        detalle[c] = {
            "soporte": d["soporte"], "aciertos": tp,
            "recall": round(d["recall"], 4),
            "ic": bootstrap_ic([p == c for p, g in zip(pred, gold) if g == c],
                               nivel=nivel),
            "fallos": [i for i, (p, g) in enumerate(zip(pred, gold))
                       if g == c and p != c],
            "a_que_fueron": dict(Counter(
                str(p) for p, g in zip(pred, gold) if g == c and p != c)),
        }
        tp_tot += tp
        n_tot += d["soporte"]

    aciertos = [p == g for p, g in zip(pred, gold) if g in CLASES_CRITICAS]
    return {
        "clases": list(CLASES_CRITICAS),
        "por_que_estas": (
            "un falso negativo en `habeas_corpus` o `tutela` le niega "
            "proteccion a alguien: lo manda a la via ordinaria cuando no tenia "
            "otro medio eficaz. El error inverso cuesta un trámite. Las demas "
            "clases no entran: su falso negativo manda a otra accion "
            "constitucional, no deja sin ninguna."),
        "por_clase": detalle,
        "soporte_total": n_tot,
        "recall_agregado": round(tp_tot / n_tot, 4) if n_tot else None,
        "ic_agregado": bootstrap_ic(aciertos, nivel=nivel) if aciertos else None,
        "lectura": (
            "es la cifra que hay que mirar antes de la accuracy. Con soportes "
            "de dos digitos un caso vale varios puntos, asi que se publica con "
            "intervalo; y `a_que_fueron` dice a donde se desvio cada fallo, "
            "porque mandar un habeas corpus a tutela no es lo mismo que "
            "mandarlo a la via ordinaria."),
    }


def macro_f1(pred: list, gold: list) -> float:
    """Macro sobre las clases CON soporte: una clase que nunca aparece en el
    gold no debe premiar ni castigar al modelo."""
    por_clase = f1_por_clase(pred, gold)
    conf = [v["f1"] for v in por_clase.values() if v["soporte"] > 0]
    return sum(conf) / len(conf) if conf else 0.0


def baseline_clase_mayoritaria(gold: list) -> float:
    """El número que hay que batir. Sin esto, una accuracy alta no dice nada."""
    if not gold:
        return 0.0
    return Counter(gold).most_common(1)[0][1] / len(gold)


# --------------------------------------------------------------------------
# Métricas propias del dominio
# --------------------------------------------------------------------------
def adherencia_estructural(salidas: list[str]) -> float:
    """¿Aparecen las 5 etiquetas? No mira si el valor es válido.

    El modelo base de M1 puntúa alto aquí: imita la forma. Reportar solo la
    métrica de vocabulario exageraría el mérito del fine-tuning.
    """
    if not salidas:
        return 0.0
    return sum(len(etiquetas_presentes(s)) == 5 for s in salidas) / len(salidas)


def adherencia_vocabulario(salidas: list[str]) -> float:
    """¿`derecho` y `mecanismo` pertenecen al vocabulario cerrado?

    Aquí el base saca 0: inventa mecanismos que no existen en Colombia
    ("Petición de Amparo", "Control de convencionalidad"). Esto es lo que el
    fine-tuning enseñó de verdad.
    """
    if not salidas:
        return 0.0
    ok = 0
    for s in salidas:
        p = parse_salida(s)
        ok += p.get("derecho") in DERECHOS and p.get("mecanismo") in MECANISMOS
    return ok / len(salidas)


def coherencia(salidas: list[str]) -> float | None:
    """`procede` debe ser verdadero si y solo si el mecanismo es la tutela.

    El modelo ajustado llega a decir "Procedencia: no / Mecanismo: acción de
    tutela", que es una contradicción lógica. Ninguna métrica de acierto la
    detecta, porque cada campo por separado puede ser plausible.

    Devuelve None cuando NO HAY NADA QUE EVALUAR: si ninguna salida produce un
    mecanismo parseable, no existen casos sobre los que medir coherencia. Es lo
    que pasa con el modelo base, y devolver 0.0 ahí se lee como "es incoherente"
    cuando lo cierto es "no se puede saber". Mismo criterio que `cohen_kappa`.
    """
    evaluables = ok = 0
    for s in salidas:
        p = parse_salida(s)
        if p.get("mecanismo") is None or p.get("procede") is None:
            continue
        evaluables += 1
        # Segunda contradicción posible desde que `derecho` tiene válvula de
        # escape: afirmar un mecanismo del vocabulario cerrado y a la vez
        # decir que el derecho no se puede determinar. Si se determinó el
        # mecanismo, el derecho no quedó indeterminado.
        ok += (p["procede"] == (p["mecanismo"] == "tutela")
               and p.get("derecho") != DERECHO_ESCAPE)
    return ok / evaluables if evaluables else None


# --------------------------------------------------------------------------
# Métrica clásica de solapamiento léxico. Se incluye para mostrar su límite:
# puntúa alto en respuestas jurídicamente equivocadas pero bien redactadas.
# --------------------------------------------------------------------------
def _lcs(a: list[str], b: list[str]) -> int:
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(cur[j], prev[j + 1]))
        prev = cur
    return prev[-1]


def rouge_l(pred: str, ref: str) -> float:
    """F1 sobre la subsecuencia común más larga, a nivel de palabra."""
    p, r = (pred or "").lower().split(), (ref or "").lower().split()
    if not p or not r:
        return 0.0
    l = _lcs(p, r)
    if not l:
        return 0.0
    prec, rec = l / len(p), l / len(r)
    return 2 * prec * rec / (prec + rec)


# --------------------------------------------------------------------------
# Similitud por embeddings: la métrica clásica que usa el laboratorio de S05/S06.
# Capta significado y no coincidencia de palabras, así que premia la paráfrasis
# válida donde ROUGE-L la castiga. Se incluye para tener las dos y poder
# contrastarlas: ninguna de las dos sabe si el derecho está bien aplicado.
#
# `sentence-transformers` es la única dependencia externa del módulo y es
# opcional: si no está instalada, la métrica devuelve None y el resto del
# scorecard sigue funcionando.
# --------------------------------------------------------------------------
MODELO_EMB = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_st = None


def _encoder():
    global _st
    if _st is None:
        from sentence_transformers import SentenceTransformer
        _st = SentenceTransformer(MODELO_EMB)
    return _st


def similitud_embeddings(salidas: list[str], referencias: list[str]) -> float | None:
    """Coseno medio entre cada salida y su referencia. None si falta la librería."""
    if not salidas:
        return 0.0
    try:
        st = _encoder()
    except Exception:
        return None
    import numpy as np
    a = st.encode(list(salidas), normalize_embeddings=True)
    b = st.encode(list(referencias), normalize_embeddings=True)
    return float(np.mean(np.sum(a * b, axis=1)))


# Normas mencionables en texto libre, no solo en el campo `fundamento`.
_RE_LEY = re.compile(r"\b((?:Ley|Decreto(?:-Ley)?|Acto Legislativo)\s+\d{1,4}\s+de\s+\d{4})\b")
_RE_ART_CP = re.compile(
    r"\bart(?:\.|ículo|iculo)?\s*(\d{1,3}(?:\.\d)?)\s*(?:CP\b|de\s+la\s+Constituci[óo]n)",
    re.IGNORECASE)


def citas_en_texto(texto: str) -> list[str]:
    """Extrae menciones normativas de texto libre, normalizadas al formato del
    whitelist. Encuentra `Ley 1755 de 2015`, `Decreto 2591 de 1991` y
    `art. 86 CP` / `artículo 86 de la Constitución`.
    """
    out = []
    for m in _RE_LEY.finditer(texto or ""):
        out.append(re.sub(r"\s+", " ", m.group(1)).strip())
    for m in _RE_ART_CP.finditer(texto or ""):
        out.append(f"art. {m.group(1)} CP")
    return out


def _limpiar_cita(c: str) -> str:
    """Quita de la cita lo que no identifica la norma.

    Dos cosas que el modelo pega dentro de la cita cuando trabaja con RAG: la
    anotación de vigencia del corpus ("art. 11 — DEROGADO") y el título
    descriptivo del artículo ("Ley 472 de 1998 — derechos colectivos").
    Ninguna cambia QUÉ norma se está citando.
    """
    s = re.sub(r"\s*[\u2014\u2013]\s*.*$", "", c.strip())   # tras guion largo
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,;:")


def clasificar_cita(c: str, validas: set, sueltas: set, leyes: list) -> str:
    """`valida`, `incompleta`, `inventada` o una de las dos `sin_verificar`.

    Es el corazón de la métrica, y la ÚNICA definición de "esta norma existe":
    `pertinencia_citas` y `pertinencia_por_plano` preguntaban por su cuenta con
    `c in validas`, que es más estrecho, así que la misma cita podía salir
    inventada en una métrica y buena en la otra. Ahora las tres pasan por aquí.

    La versión anterior comparaba la cadena contra el whitelist y nada más, y
    eso castigaba a RAG por citar con MÁS precisión: el whitelist guarda las
    leyes a nivel de ley y RAG le enseña al modelo el artículo concreto, así
    que `art. 4 Ley 1751 de 2015` --- correcto, y más útil que `Ley 1751 de
    2015` --- contaba como inventado. Medido sobre la corrida
    m3/20261016T031746Z: dos tercios de la "alucinación" de los brazos con RAG
    era esto.

    `incompleta` es categoría propia a propósito. `art. 13` a secas no se puede
    verificar, pero tampoco es una invención: mezclarlas confunde "se lo
    inventó" con "no dijo de qué ley habla", que son fallos distintos y se
    corrigen distinto.
    """
    bruto = re.sub(r"\s+", " ", c.strip()).strip(" .,;:")
    if not bruto:
        return "incompleta"

    # El guion largo es SEPARADOR en "art. 4 — Ley 1751 de 2015" y ANOTACIÓN
    # en "Ley 472 de 1998 — derechos colectivos". No hace falta desambiguarlo:
    # se prueban las variantes de la más fiel a la más podada y vale la
    # primera que case. Podar siempre, que es lo que hacía la primera versión,
    # destruía la ley del primer caso.
    variantes = [
        bruto,
        re.sub(r"\s*[\u2014\u2013]\s*", " ", bruto).strip(),   # guion -> espacio
        _limpiar_cita(bruto),                                    # guion -> corte
    ]
    for s in variantes:
        if not s:
            continue
        if s in validas or s in sueltas:
            return "valida"
        # Subdivisión de un artículo real: art. 2.3 -> art. 2. Mismo caso que
        # el `art. 6.1` contra `art. 6` que ya corregimos una vez.
        if re.sub(r"(\d+)\.\d+", r"\1", s) in validas | sueltas:
            return "valida"
        # Artículo de una ley que SÍ está en el whitelist.
        if any(ley in s for ley in leyes):
            return "valida"

    # Artículo sin norma en ninguna variante: no verificable, pero no inventado.
    for s in variantes:
        if re.fullmatch(r"art\.?\s*[\d.]+(\s*(y|a)\s*[\d.]+)*", s, re.IGNORECASE):
            return "incompleta"

    # JURISPRUDENCIA: categoría propia, ni `valida` ni `inventada`.
    #
    # `data/normas.json` declara desde el principio que la cita jurisprudencial
    # NO entra al chequeo de alucinación normativa, "porque la cita
    # jurisprudencial es mas volatil". La implementación no lo honraba: una
    # referencia bien formada a una sentencia real caía en `inventada`, así que
    # un modelo que cita la C-531 de 2000 --- que es el fundamento de la
    # estabilidad laboral reforzada y está en el corpus --- quedaba penalizado
    # por acertar.
    #
    # Importa ahora más que antes: el corpus v1.5.0 incluye fragmentos de
    # jurisprudencia, así que el RAG puede ponerle una sentencia delante al
    # modelo y entonces citarla es lo correcto.
    #
    # Se separa en vez de aprobarse en bloque. No tenemos un whitelist completo
    # de la jurisprudencia colombiana y fingir que sí sería peor: una sentencia
    # que no podemos comprobar se cuenta aparte y se dice que no se comprobó.
    for s in variantes:
        if RE_SENTENCIA.fullmatch(s):
            return ("jurisprudencia" if _jurisprudencia_conocida(s)
                    else "jurisprudencia_sin_verificar")

    # CONSTITUCION: el mismo problema que la jurisprudencia, y peor fundado.
    #
    # `normas.json` declara 20 articulos de los 380 de la Constitucion de 1991,
    # porque declara los que el proyecto usa. Pero la metrica leia esa lista
    # como si fuera la Constitucion entera: un modelo que cita el art. 12 CP
    # --- prohibicion de tortura y desaparicion forzada --- o el art. 68 CP
    # --- establecimientos educativos --- citaba una norma REAL y se contaba
    # como invencion. Medido sobre la corrida m1/20261016T174233Z: 2 de las 6
    # "alucinaciones" del modelo ajustado eran esto.
    #
    # A diferencia de la jurisprudencia, la Constitucion SI es enumerable: son
    # 380 articulos. Asi que aqui se comprueba algo de verdad --- que el numero
    # exista --- y lo que queda sin comprobar es la PERTINENCIA, que es lo que
    # mide `pertinencia_citas` y nunca fue trabajo de esta metrica.
    for s in variantes:
        m = RE_ART_CP.fullmatch(s)
        if m and 1 <= int(m.group(1)) <= ARTICULOS_CP:
            return "constitucional_sin_verificar"
    return "inventada"


ARTICULOS_CP = 380
"""Articulos de la Constitucion de 1991, sin contar los transitorios."""

RE_ART_CP = re.compile(
    r"art(?:[íi]culo)?\.?\s*(\d{1,3})(?:\.\d+)?\s*"
    r"(?:C\.?\s*P\.?|de\s+la\s+Constituci[óo]n(?:\s+Pol[íi]tica)?)",
    re.IGNORECASE)
"""`art. 12 CP`, `art. 86 C.P.`, `articulo 49 de la Constitucion Politica`."""

EXISTE = frozenset({"valida", "jurisprudencia", "jurisprudencia_sin_verificar",
                    "constitucional_sin_verificar"})
"""Clasificaciones que significan "la norma existe", sea o no pertinente.

`incompleta` queda fuera a proposito: `art. 13` a secas no se puede verificar,
asi que no se puede afirmar ni que exista ni que no.
"""


def _vocabulario_normas(validas: set | None = None) -> tuple[set, set, list]:
    """`(validas, sueltas, leyes)` para `clasificar_cita`, construido una vez.

    Se construia aqui y en `alucinacion_normativa`, y las otras dos metricas no
    lo construian: preguntaban `c in validas` a secas. Una sola fuente evita
    que las dos definiciones de "existe" vuelvan a separarse.
    """
    if validas is None:
        validas = cargar_normas()
    # Una norma mencionada sin articulo (p. ej. "Decreto 2591 de 1991") es real
    # aunque el whitelist la indexe por articulo.
    sueltas = {c.split(" ", 2)[-1] for c in validas if " Decreto " in c}
    leyes = sorted((w for w in validas if w.startswith("Ley")),
                   key=len, reverse=True)
    return validas, sueltas, leyes


RE_SENTENCIA = re.compile(
    r"(?:Sentencia\s+)?(?:SU|[TCA])-?\s*\d{1,4}\s*(?:de\s*\d{4}|[-/]\s*\d{2,4})",
    re.IGNORECASE)
"""`Sentencia T-225 de 1993`, `C-531 de 2000`, `T-760-08`, `SU-111 de 1997`."""


def _clave_sentencia(s: str) -> str:
    """Normaliza una referencia a sentencia para comparar: `t22593`."""
    m = re.search(r"([TCSA]U?)-?\s*(\d{1,4})\s*(?:de\s*(\d{4})|[-/]\s*(\d{2,4}))",
                  s, re.IGNORECASE)
    if not m:
        return ""
    sala, num = m.group(1).upper(), m.group(2)
    anio = m.group(3) or m.group(4) or ""
    anio = anio[-2:]                      # 1993 y 93 son el mismo ano
    return f"{sala}{num}{anio}"


def _jurisprudencia_conocida(s: str) -> set | bool:
    """¿Esta sentencia está en el proyecto (normas.json o el corpus)?"""
    clave = _clave_sentencia(s)
    return bool(clave) and clave in _claves_jurisprudencia()


@lru_cache(maxsize=1)
def _claves_jurisprudencia() -> frozenset:
    """Las sentencias que el proyecto declara: `jurisprudencia_referencia` de
    normas.json mas los fragmentos `tipo: jurisprudencia` del corpus."""
    from pathlib import Path
    data = Path(__file__).resolve().parent.parent / "data"
    claves = set()
    try:
        d = json.loads((data / "normas.json").read_text(encoding="utf-8"))
        for k in d.get("jurisprudencia_referencia", {}):
            if not k.startswith("_"):
                claves.add(_clave_sentencia(k))
    except Exception:                                  # noqa: BLE001
        pass
    try:
        c = json.loads((data / "corpus.json").read_text(encoding="utf-8"))
        for f in c["documentos"]:
            if f.get("tipo") == "jurisprudencia":
                claves.add(_clave_sentencia(f.get("norma", "")))
    except Exception:                                  # noqa: BLE001
        pass
    return frozenset(k for k in claves if k)


def alucinacion_normativa(salidas: list[str]) -> dict:
    """Toda cita que el modelo produzca debe existir en data/normas.json.

    Es la métrica que más importa en lo jurídico: una norma inventada que suena
    plausible es peor que no citar nada. Se reusa en M3 como proxy de
    faithfulness sobre el corpus.

    SE MIDE EN DOS ÁMBITOS, y la diferencia entre ambos es un hallazgo en sí:

      - `fundamento`: el campo del esquema. Es la cifra histórica, la que M1 y
        M2 reportaron, y se conserva para que los números sigan comparables.
      - toda la salida: incluye lo que el modelo escriba en la línea de
        Procedencia. La versión anterior no mirába ahí, y ahí es justamente
        donde un modelo generativo suelta normas sin que nadie las revise.

    Lo que NO cubre, y hay que decirlo: una afirmación jurídica equivocada sin
    cita (`"el término legal es de cinco años"`) no la detecta ninguna de las
    dos. Para eso está el juez y el acierto jurídico.
    """
    validas, normas_sueltas, leyes = _vocabulario_normas()

    tot_f = inv_f = tot_t = inv_t = 0
    const_f = const_t = 0
    incompletas_f = incompletas_t = 0
    # Jurisprudencia, contada APARTE. normas.json declara que la cita
    # jurisprudencial no entra al chequeo de alucinacion, y sumarla a
    # `inventada` penalizaba al modelo por citar una sentencia real.
    juris_f = juris_sin_ver_f = juris_t = juris_sin_ver_t = 0
    malas_f, malas_t, solo_en_razon, sin_norma = [], [], [], []
    juris_vistas, juris_dudosas, const_vistas = [], [], []

    for s in salidas:
        del_campo = citas(parse_salida(s).get("fundamento"))
        for c in del_campo:
            tot_f += 1
            cl = clasificar_cita(c, validas, normas_sueltas, leyes)
            if cl == "incompleta":
                incompletas_f += 1
                sin_norma.append(c)
            elif cl == "inventada":
                inv_f += 1
                malas_f.append(c)
            elif cl == "jurisprudencia":
                juris_f += 1
                juris_vistas.append(c)
            elif cl == "jurisprudencia_sin_verificar":
                juris_sin_ver_f += 1
                juris_dudosas.append(c)
            elif cl == "constitucional_sin_verificar":
                const_f += 1
                const_vistas.append(c)

        en_todo = citas_en_texto(s)
        for c in en_todo:
            tot_t += 1
            cl = clasificar_cita(c, validas, normas_sueltas, leyes)
            if cl == "incompleta":
                incompletas_t += 1
            elif cl == "inventada":
                inv_t += 1
                malas_t.append(c)
                if c not in del_campo:
                    solo_en_razon.append(c)
            elif cl == "jurisprudencia":
                juris_t += 1
            elif cl == "jurisprudencia_sin_verificar":
                juris_sin_ver_t += 1
            elif cl == "constitucional_sin_verificar":
                const_t += 1

    return {
        "jurisprudencia": {
            "en_fundamento": juris_f,
            "en_fundamento_sin_verificar": juris_sin_ver_f,
            "en_toda_la_salida": juris_t,
            "en_toda_la_salida_sin_verificar": juris_sin_ver_t,
            "ejemplos": Counter(juris_vistas).most_common(5),
            "ejemplos_sin_verificar": Counter(juris_dudosas).most_common(5),
            "lectura":
                "`data/normas.json` declara que la cita jurisprudencial NO "
                "entra al chequeo de alucinacion normativa porque es mas "
                "volatil. Se cuenta aqui y no en `inventada`: un modelo que "
                "cita la C-531 de 2000 --- el fundamento de la estabilidad "
                "laboral reforzada, que esta en el corpus --- estaba siendo "
                "penalizado por acertar. `sin_verificar` son referencias bien "
                "formadas a sentencias que el proyecto no declara: no se "
                "aprueban en bloque, porque no hay whitelist completo de la "
                "jurisprudencia colombiana y fingir que si seria peor.",
        },
        "constitucional_sin_verificar": {
            "en_fundamento": const_f,
            "en_toda_la_salida": const_t,
            "ejemplos": Counter(const_vistas).most_common(5),
            "lectura":
                "Articulos de la Constitucion con numero existente (1-380) que "
                "`normas.json` no declara, porque declara los 20 que el "
                "proyecto usa. Antes caian en `inventada` y la tasa de "
                "alucinacion los contaba: en m1/20261016T174233Z eran 2 de 6. "
                "Que el articulo exista NO dice que venga al caso --- eso lo "
                "mide `pertinencia_citas`, donde siguen contando como "
                "impertinentes si no corresponden. Las tasas de alucinacion de "
                "las corridas anteriores a este cambio NO son comparables con "
                "las de ahora: median otra cosa.",
        },
        "citas_totales": tot_f,
        "citas_inventadas": inv_f,
        "tasa_alucinacion": inv_f / tot_f if tot_f else 0.0,
        "ejemplos": Counter(malas_f).most_common(5),
        # Citas sin norma ("art. 13" a secas). No son invenciones y por eso
        # salen de la tasa de alucinación, pero son un defecto real: una cita
        # que no se puede verificar no fundamenta nada. Se reportan aparte
        # porque se corrigen de otra forma --- con formato, no con contenido.
        "citas_incompletas": incompletas_f,
        "tasa_incompletas": incompletas_f / tot_f if tot_f else 0.0,
        "ejemplos_incompletas": Counter(sin_norma).most_common(5),
        # Ámbito completo: incluye la línea de Procedencia.
        "citas_totales_salida": tot_t,
        "citas_inventadas_salida": inv_t,
        "tasa_alucinacion_salida": inv_t / tot_t if tot_t else 0.0,
        "citas_incompletas_salida": incompletas_t,
        "ejemplos_salida": Counter(malas_t).most_common(5),
        "inventadas_fuera_del_fundamento": Counter(solo_en_razon).most_common(5),
    }


def pertinencia_citas(salidas: list[str], golds: list[dict]) -> dict:
    """¿Las normas citadas vienen al caso? Es el complemento de la alucinación.

    Una cita puede fallar de dos maneras y solo medíamos una:

      - INVENTADA      la norma no existe        -> `alucinacion_normativa`
      - IMPERTINENTE   existe pero no aplica     -> esto

    Se detectó construyendo el brazo con reglas: en un caso de derecho de
    petición el sistema citó el art. 28 CP (libertad personal). La norma existe,
    así que la tasa de alucinación daba 0%, y la cita era inservible. Una cita
    real y fuera de lugar engaña igual que una inventada, y además esquiva el
    control: por eso hace falta medirla aparte.

    La verdad de campo es el `fundamento` del gold, que ya dice qué artículos
    debían citarse.
    """
    validas, sueltas, leyes = _vocabulario_normas()
    correctas = impertinentes = inventadas = incompletas = 0
    recall_num = recall_den = 0
    ejemplos = []
    for s, g in zip(salidas, golds):
        esperadas = set(citas(g["fundamento"]))
        emitidas = citas(parse_salida(s).get("fundamento"))
        recall_den += len(esperadas)
        recall_num += len(esperadas & set(emitidas))
        for c in emitidas:
            if c in esperadas:
                correctas += 1
            else:
                # `c in validas` era mas estrecho que `clasificar_cita`, asi
                # que un art. CP real y no declarado salia inventado aqui
                # mientras la metrica de alucinacion lo daba por bueno.
                cl = clasificar_cita(c, validas, sueltas, leyes)
                if cl in EXISTE:
                    impertinentes += 1
                    ejemplos.append((g["id"], c))
                elif cl == "incompleta":
                    incompletas += 1
                else:
                    inventadas += 1
    total = correctas + impertinentes + inventadas
    out = {
        "citas_emitidas": total,
        "correctas": correctas,
        "impertinentes": impertinentes,
        "inventadas": inventadas,
        # Fuera de `total`, igual que en `alucinacion_normativa`: una cita sin
        # norma no se puede juzgar pertinente ni impertinente.
        "incompletas": incompletas,
        "precision_citas": correctas / total if total else 0.0,
        "recall_citas": recall_num / recall_den if recall_den else 0.0,
        "ejemplos_impertinentes": Counter(c for _, c in ejemplos).most_common(5),
    }
    out["por_plano"] = pertinencia_por_plano(salidas, golds, validas)
    return out


def pertinencia_por_plano(salidas: list[str], golds: list[dict],
                          validas: set[str] | None = None) -> dict:
    """La misma pertinencia, pero separando los dos planos de la cita.

    La metrica de arriba compara contra el conjunto EXACTO del `fundamento`
    del gold, y ese campo mezclaba dos preguntas distintas. En el eval set los
    8 casos de cumplimiento citan art. 87 CP, los 8 de popular art. 88 CP y los
    8 de habeas corpus art. 30 CP, pero `art. 86 CP` no aparece en NINGUN
    fundamento aunque 27 casos son de tutela. Resultado: un modelo que cita el
    art. 86 CP --- la norma que crea la tutela, y lo que emite
    `reglas.decidir()` --- contaba como impertinente en 24 de esos 27 casos.

    Aqui una cita emitida cae en una de cinco cajas, y la diferencia importa:

      mecanismo_correcto      acerto el plano procesal
      mecanismo_equivocado    cito OTRO mecanismo: es un error de
                              razonamiento sobre la via, el mas grave
      derecho_correcto        acerto el derecho de fondo
      derecho_impertinente    cito un derecho que no viene al caso
      inventada               la norma no existe

    Mezclar `mecanismo_equivocado` con `derecho_impertinente` en un solo
    numero esconde cual de los dos razonamientos falla.

    Necesita `fundamento_del_mecanismo` y `fundamento_del_derecho` en el gold
    (los pone data/anotar_fundamentos.py). Si no estan, devuelve
    `{"disponible": False}` y no inventa nada.
    """
    validas, _sueltas, _leyes = _vocabulario_normas(validas)
    if not any("fundamento_del_mecanismo" in g for g in golds):
        return {"disponible": False,
                "motivo": "el gold no trae los planos separados; corre "
                          "data/anotar_fundamentos.py"}

    plano_mec, _ = planos_normativos()
    caja = Counter()
    ej_mec_mal, ej_der_mal = [], []
    rec = {"mecanismo": [0, 0], "derecho": [0, 0]}   # [acertadas, esperadas]

    for s, g in zip(salidas, golds):
        esp_mec = set(g.get("fundamento_del_mecanismo") or [])
        esp_der = set(g.get("fundamento_del_derecho") or [])
        emitidas = citas(parse_salida(s).get("fundamento"))

        rec["mecanismo"][1] += len(esp_mec)
        rec["derecho"][1] += len(esp_der)
        rec["mecanismo"][0] += len(esp_mec & set(emitidas))
        rec["derecho"][0] += len(esp_der & set(emitidas))

        for c in emitidas:
            cl = (None if c in validas
                  else clasificar_cita(c, validas, _sueltas, _leyes))
            if cl is not None and cl not in EXISTE:
                caja["incompleta" if cl == "incompleta" else "inventada"] += 1
            elif c in esp_mec:
                caja["mecanismo_correcto"] += 1
            elif c in esp_der:
                caja["derecho_correcto"] += 1
            elif c in plano_mec:
                caja["mecanismo_equivocado"] += 1
                ej_mec_mal.append(c)
            else:
                caja["derecho_impertinente"] += 1
                ej_der_mal.append(c)

    n = sum(caja.values())

    def _prec(ok: str, mal: str) -> float | None:
        """None, no 0.0, cuando no se emitio ninguna cita de ese plano.

        Un 0.0 ahi se lee como "fallo todas" y lo cierto es "no emitio
        ninguna, no hay nada que medir". Es el mismo criterio con el que
        `harness.cohen_kappa` devuelve None en vez de un 0.0 que parece
        medicion.
        """
        d = caja[ok] + caja[mal]
        return caja[ok] / d if d else None

    return {
        "disponible": True,
        "cajas": dict(caja),
        "precision_mecanismo": _prec("mecanismo_correcto", "mecanismo_equivocado"),
        "precision_derecho": _prec("derecho_correcto", "derecho_impertinente"),
        "recall_mecanismo": rec["mecanismo"][0] / rec["mecanismo"][1] if rec["mecanismo"][1] else 0.0,
        "recall_derecho": rec["derecho"][0] / rec["derecho"][1] if rec["derecho"][1] else 0.0,
        "citas_clasificadas": n,
        "ejemplos_mecanismo_equivocado": Counter(ej_mec_mal).most_common(5),
        "ejemplos_derecho_impertinente": Counter(ej_der_mal).most_common(5),
        "lectura":
            "`precision_citas` de arriba sigue siendo el numero comparable con "
            "las once corridas anteriores. Esta particion dice ADEMAS cual de "
            "los dos razonamientos falla: equivocar el mecanismo es un error "
            "sobre la via procesal; citar un derecho impertinente es un error "
            "sobre el fondo.",
    }


def acierto_juridico(preds: list[dict], golds: list[dict]) -> float:
    """Métrica propia: acierta solo si enruta bien Y resuelve bien la procedencia.

    Es la decisión que el usuario toma con el sistema. Acertar el derecho pero
    mandar a la persona por el mecanismo equivocado no sirve de nada, así que
    aquí no hay crédito parcial.
    """
    if not golds:
        return 0.0
    return sum(acierto_por_caso(preds, golds)) / len(golds)


def acierto_por_caso(preds: list[dict], golds: list[dict]) -> list[bool]:
    """El acierto jurídico caso por caso. Lo necesita el bootstrap del IC.

    Está separado de `acierto_juridico` para que la definición de "acierta"
    viva en un solo sitio: el promedio y el intervalo tienen que medir
    exactamente lo mismo.
    """
    return [p.get("mecanismo") == g["mecanismo"] and p.get("procede") == g["procede"]
            for p, g in zip(preds, golds)]


# --------------------------------------------------------------------------
# Scorecard
# --------------------------------------------------------------------------
def abstencion(sal_ab: list[str], sal_ev: list[str],
               golds_ab: list[dict] | None = None,
               golds_ev: list[dict] | None = None) -> dict | None:
    """¿El sistema sabe callarse, y sabe NO callarse cuando sí hay respuesta?

    Se mide en los dos sentidos a propósito. Un sistema que se abstiene siempre
    tendría abstención perfecta y seria inútil, así que la cifra sola no dice
    nada: hace falta saber cuántas veces se abstuvo donde sí había mecanismo.

        acierto_abstencion   de los casos SIN respuesta correcta, cuántos
                             reconoció como tales en vez de forzar una etiqueta
        abstencion_indebida  de los casos CON respuesta correcta, cuántos
                             dejó sin responder

    La mitad de `abstencion_indebida` se mide SIEMPRE, incluso en conjuntos sin
    casos de abstención. Hace falta: ahí es donde una abstención es un error
    puro, porque todos los casos tienen respuesta correcta. La primera versión
    devolvía None en ese caso y la cifra no se calculaba --- en la corrida
    m1/20261015T192223Z el caso A05 se abstuvo en el eval set y ninguna métrica
    lo reportó; solo aparecía, disfrazado, como un error de mecanismo.

    `acierto_abstencion` sí queda en None cuando no hay casos sin respuesta
    correcta: un 0.0 se leería como "nunca se abstuvo donde debía", que es un
    fallo, y lo cierto es que no había nada que medir. Mismo criterio que
    `cohen_kappa` y `coherencia`.

    Con `golds_ab` y `golds_ev` devuelve además el desglose POR FAMILIA. Hace
    falta: el split de validation trae una abstención de cada una de las seis
    familias justamente para que la cifra diga CUÁL falla, y sin el desglose un
    "4 de 6" no es diagnosticable —la sub-estratificación por familia no serviría
    de nada. Lo mismo con las abstenciones indebidas: saber que hubo una no dice
    en qué caso, y es el caso lo que se revisa.
    """
    from schema import se_abstuvo
    if not sal_ab and not sal_ev:
        return None
    ok = sum(se_abstuvo(s) for s in sal_ab)
    indebidas = sum(se_abstuvo(s) for s in sal_ev)
    out = {
        "n_sin_respuesta_correcta": len(sal_ab),
        "acierto_abstencion": (ok / len(sal_ab)) if sal_ab else None,
        "forzo_etiqueta": len(sal_ab) - ok,
        "n_con_respuesta_correcta": len(sal_ev),
        "abstencion_indebida": indebidas / len(sal_ev) if sal_ev else 0.0,
        "abstenciones_indebidas": indebidas,
    }

    # CERO ABSTENCIONES NO SIEMPRE ES UN FALLO, Y LA CIFRA SOLA NO LO DISTINGUE.
    #
    # En m3/20261017T143205Z el brazo 4 dio `acierto_abstencion: 0.0` con 6
    # casos de abstencion y `abstencion_indebida: 0.0` con 57. Leido suelto,
    # el 0.0 parece decir "nunca supo callarse". Lo que de verdad dice es que
    # se le pidio no callarse: el defecto pro homine de `extraer_hechos` no
    # activa causal de improcedencia ante la duda, asi que el motor siempre
    # encuentra una via. La declaracion viaja con el numero.
    if sal_ab and out["acierto_abstencion"] == 0.0:
        try:
            from sistema import DEFECTO_PRO_HOMINE
            out["cero_abstenciones_es_decision_de_diseno"] = DEFECTO_PRO_HOMINE
        except ImportError:                       # metricas se usa sin sistema
            out["cero_abstenciones_es_decision_de_diseno"] = (
                "ver sistema.DEFECTO_PRO_HOMINE")
        out["lectura_abstencion"] = (
            f"0 de {len(sal_ab)} abstenciones correctas y "
            f"{indebidas} de {len(sal_ev)} indebidas. Los dos numeros salen "
            "del mismo defecto: ante la duda no se activa causal de "
            "improcedencia. No se puede celebrar el segundo y llamar fallo al "
            "primero.")

    if golds_ab:
        out["por_familia"] = {
            g.get("categoria") or g.get("id") or f"caso_{i}": bool(se_abstuvo(s))
            for i, (s, g) in enumerate(zip(sal_ab, golds_ab))
        }
        out["forzo_en"] = [
            {"id": g.get("id"), "familia": g.get("categoria")}
            for s, g in zip(sal_ab, golds_ab) if not se_abstuvo(s)
        ]
    if golds_ev:
        out["indebidas_en"] = [
            {"id": g.get("id"), "categoria": g.get("categoria"),
             "mecanismo_gold": g.get("mecanismo") or g.get("gold_mecanismo")}
            for s, g in zip(sal_ev, golds_ev) if se_abstuvo(s)
        ]
    return out


def degeneracion(salidas: list[str], golds: list[dict] | None = None) -> dict:
    """Cuantas salidas se descarrilaron, y en que casos.

    Se mide sobre las salidas CRUDAS, antes de recortar. Si se midiera despues
    el numero seria siempre cero y el defecto quedaria invisible --- el modelo
    seguiria descarrilandose igual.
    """
    from schema import recortar_al_bloque
    casos = []
    no_cortadas = []
    for i, s in enumerate(salidas):
        texto, recortado = recortar_al_bloque(s)
        g = (golds or [{}] * len(salidas))[i]
        if recortado:
            cola = s[len(texto):]
            casos.append({"id": g.get("id", f"#{i}"),
                          "categoria": g.get("categoria"),
                          "chars_cola": len(cola),
                          "recortada": True,
                          **_anatomia_de_la_cola(cola)})
            continue
        # Cola que el recortador NO ve. `recortar_al_bloque` solo corta en CJK
        # y en marcas de turno del chat, asi que una salida que repite la
        # ultima linea o sigue con prosa en el MISMO turno pasaba entera: no se
        # contaba como degeneracion y no se cortaba, aunque contamina ROUGE-L,
        # el conteo de citas y lo que M2 le pasa al juez igual que las otras.
        # Aqui se CUENTA. No se corta, para no mover la vara de las corridas
        # anteriores; el arreglo del recortador es una decision aparte.
        cola = _cola_tras_el_bloque(s)
        if cola:
            no_cortadas.append({"id": g.get("id", f"#{i}"),
                                "categoria": g.get("categoria"),
                                "chars_cola": len(cola),
                                "recortada": False,
                                **_anatomia_de_la_cola(cola)})
    todas = casos + no_cortadas
    return {
        "n": len(casos),
        "de": len(salidas),
        "tasa": len(casos) / len(salidas) if salidas else 0.0,
        "casos": casos,
        "n_no_cortadas": len(no_cortadas),
        "casos_no_cortados": no_cortadas,
        "n_total_con_cola": len(todas),
        "tasa_total": len(todas) / len(salidas) if salidas else 0.0,
        "nota_no_cortadas":
            "`n` cuenta las que el recortador corta (CJK o marca de turno). "
            "`n_no_cortadas` son colas que el recortador NO ve --- repeticion o "
            "prosa extra en el mismo turno --- y que por tanto llegan enteras a "
            "las metricas y al juez de M2. Se cuentan aqui para que el defecto "
            "sea visible; cortarlas cambiaria lo que miden las once corridas "
            "anteriores y es una decision aparte.",
        "por_sintoma": dict(Counter(c["sintoma"] for c in todas)),
        "lectura":
            "`sintoma` dice QUE hizo el modelo en vez de parar, que es lo que "
            "senala el arreglo. `abrio_turno` significa que emitio la marca de "
            "fin y siguio: el adaptador no aprendio a parar, y la cura esta en "
            "el entrenamiento (reforzar EOS) o en los tokens de parada de la "
            "generacion. `repitio` es degeneracion clasica por falta de senal "
            "de fin. `otro_idioma` suele acompanar a las dos. `prosa_extra` es "
            "el caso leve: el modelo siguio hablando en el mismo turno, y eso "
            "se corrige con el prompt, no con el entrenamiento.",
    }


_ETIQUETA_FINAL = re.compile(r"^\s*(Pretensi[oó]n)\s*:", re.IGNORECASE)


def _cola_tras_el_bloque(salida: str) -> str:
    """Lo que viene despues de la ultima linea canonica del esquema.

    El bloque son exactamente cinco lineas y la ultima es `Pretension:`.
    Cualquier contenido sustantivo posterior es cola, la corte el recortador o
    no. Devuelve "" si no hay cola o si la linea final no aparece --- en ese
    caso lo que falla es la adherencia estructural, que ya se mide aparte.
    """
    lineas = salida.splitlines()
    idx = next((i for i, l in enumerate(lineas) if _ETIQUETA_FINAL.match(l)), None)
    if idx is None:
        return ""
    resto = "\n".join(lineas[idx + 1:]).strip()
    return resto


def _anatomia_de_la_cola(cola: str) -> dict:
    """Clasifica POR QUE se descarrilo, no solo cuanto.

    La version anterior contaba caracteres de cola. Con eso se sabe que pasa
    pero no que arreglar: una cola de 200 caracteres porque el modelo abrio un
    turno nuevo del chat y una de 200 porque se puso a repetir la ultima linea
    piden arreglos distintos. Esto mira la cola y lo dice.
    """
    marcas = [m for m in ("<|im_start|>", "<|im_end|>", "<|endoftext|>",
                          "</s>", "[INST]") if m in cola]
    # Un bloque CJK en la cola: el sintoma que se observo en la corrida de M1.
    cjk = sum(1 for ch in cola if "一" <= ch <= "鿿"
              or "぀" <= ch <= "ヿ")
    lineas = [l.strip() for l in cola.splitlines() if l.strip()]
    # Repeticion = alguna linea aparece mas de una vez. El umbral anterior
    # (`len(set) < len//2`) no disparaba con tres lineas identicas, que es el
    # caso tipico: set=1, len//2=1, y 1 < 1 es falso.
    repetida = len(lineas) >= 2 and len(set(lineas)) < len(lineas)

    if marcas:
        sintoma = "abrio_turno"
    elif repetida:
        sintoma = "repitio"
    elif cjk > 8:
        sintoma = "otro_idioma"
    else:
        sintoma = "prosa_extra"
    return {
        "sintoma": sintoma,
        "marcas_de_chat": marcas,
        "chars_cjk": cjk,
        "muestra_cola": cola[:120].replace("\n", "\\n"),
    }


def scorecard(salidas: list[str], golds: list[dict], etiqueta: str = "sistema") -> dict:
    """salidas = texto crudo generado; golds = ejemplos del eval set.

    Los casos `tipo: "abstencion"` no tienen mecanismo correcto, así que salen
    de la accuracy por campo —compararlos contra None daría un número sin
    sentido— y entran en su propia métrica.
    """
    ab = [s for s, g in zip(salidas, golds) if g.get("tipo") == "abstencion"]
    # Los gold de abstencion se capturan ANTES de reasignar `golds`, para poder
    # desglosar el resultado por familia.
    golds_ab = [g for g in golds if g.get("tipo") == "abstencion"]
    pares_ev = [(s, g) for s, g in zip(salidas, golds)
                if g.get("tipo") != "abstencion"]
    salidas_todas = list(salidas)
    salidas = [s for s, _ in pares_ev]
    golds = [g for _, g in pares_ev]

    preds = [parse_salida(s) for s in salidas]

    sc = {"sistema": etiqueta, "n": len(golds), "campos": {}}
    if ab:
        sc["n_abstencion"] = len(ab)
    sc["abstencion"] = abstencion(ab, salidas, golds_ab, golds)
    sc["adherencia_estructural_total"] = adherencia_estructural(salidas_todas)

    for campo in CAMPOS_CATEGORICOS:
        p = [x.get(campo) for x in preds]
        g = [x[campo] for x in golds]
        # Soporte por clase junto al macro F1. Sin esto el numero esconde su
        # propia fragilidad: en el eval set hay clases con 2 casos, y el macro
        # promedia las cinco por igual, asi que un solo caso de habeas_corpus
        # mueve el macro F1 global unos 10 puntos.
        _clases = f1_por_clase(p, g)
        sc["campos"][campo] = {
            "accuracy": accuracy(p, g),
            "macro_f1": macro_f1(p, g),
            "baseline_mayoritaria": baseline_clase_mayoritaria(g),
            "soporte_por_clase": {k: v["soporte"] for k, v in _clases.items()
                                  if v["soporte"] > 0},
            "f1_por_clase": {k: round(v["f1"], 4) for k, v in _clases.items()
                             if v["soporte"] > 0},
            "clases_con_soporte_minimo": sorted(
                k for k, v in _clases.items() if 0 < v["soporte"] <= 3),
        }

    sc["adherencia_estructural"] = adherencia_estructural(salidas)
    sc["adherencia_vocabulario"] = adherencia_vocabulario(salidas)
    sc["coherencia"] = coherencia(salidas)
    sc["acierto_juridico"] = acierto_juridico(preds, golds)
    sc["alucinacion_normativa"] = alucinacion_normativa(salidas)
    sc["pertinencia_citas"] = pertinencia_citas(salidas, golds)

    # Intervalos de confianza de las dos métricas de cabecera (ROADMAP #14).
    #
    # Con n=63 juzgables y adversarial n=18, una diferencia de uno o dos casos
    # mueve la accuracy entre 1.6 y 5.6 puntos. La tabla la presentaba como un
    # resultado y no lo es. El IC no vuelve significativa una diferencia
    # pequeña: sirve para no leer como hallazgo lo que es ruido de muestreo.
    acierta_mec = [p.get("mecanismo") == g["mecanismo"]
                   for p, g in zip(preds, golds) if g["mecanismo"] is not None]
    acierta_jur = acierto_por_caso(preds, golds)
    sc["ic"] = {
        "acc_mecanismo": bootstrap_ic(acierta_mec),
        "acierto_juridico": bootstrap_ic(acierta_jur),
        "por_tipo": {
            t: bootstrap_ic([a for a, g in zip(acierta_jur, golds)
                             if g.get("tipo") == t])
            for t in ("gold", "adversarial")
            if any(g.get("tipo") == t for g in golds)
        },
        "lectura":
            "si los intervalos de dos brazos se solapan, la tabla no sostiene "
            "que uno sea mejor que el otro. `metricas.ic_se_solapan()` lo "
            "comprueba. El estrato adversarial es el mas pequeño y por eso el "
            "de intervalo mas ancho: es justo donde no hay que sobreleer.",
    }

    # ROUGE-L contra la prosa del gold (razon + pretension). Va aquí para poder
    # contrastarlo con acierto_juridico: cuando suben juntos no aporta nada, y
    # cuando divergen es la prueba de que el solapamiento léxico no mide derecho.
    pares = [(parse_salida(s), g) for s, g in zip(salidas, golds)]
    sc["rouge_l"] = sum(
        rouge_l(" ".join(filter(None, [p.get("razon"), p.get("pretension")])),
                g["razon"] + " " + g["pretension"])
        for p, g in pares
    ) / len(golds) if golds else 0.0

    # Similitud por embeddings contra la referencia completa: es la métrica
    # clásica del laboratorio de S05/S06. Se reporta junto a ROUGE-L porque
    # miden cosas distintas (significado contra solapamiento literal).
    from schema import render_salida
    sc["similitud_embeddings"] = similitud_embeddings(
        salidas, [render_salida(g) for g in golds])

    # Desglose por tipo: los adversariales se reportan aparte porque promediarlos
    # con los gold esconde justo lo que interesa ver.
    por_tipo = defaultdict(lambda: {"preds": [], "golds": []})
    for pr, go in zip(preds, golds):
        t = go.get("tipo", "gold")
        por_tipo[t]["preds"].append(pr)
        por_tipo[t]["golds"].append(go)
    sc["por_tipo"] = {
        t: {"n": len(v["golds"]), "acierto_juridico": acierto_juridico(v["preds"], v["golds"])}
        for t, v in por_tipo.items()
    }

    # EL FALSO NEGATIVO QUE CUESTA, como cifra de cabecera.
    #
    # El scorecard publicaba F1 por clase, donde el recall de habeas corpus
    # pesa igual que la precision de accion popular. No pesan igual: un falso
    # negativo en habeas corpus o en tutela le niega proteccion a alguien, y
    # el error inverso cuesta un trámite. La asimetria estaba declarada en
    # `sistema.DEFECTO_PRO_HOMINE` y en ninguna metrica. Ver
    # `recall_clase_critica`.
    _pm = [p.get("mecanismo") for p in preds]
    _gm = [g.get("mecanismo") for g in golds]
    sc["recall_clase_critica"] = recall_clase_critica(_pm, _gm)

    # LA MISMA PERTINENCIA, DEPURANDO LAS CITAS QUE NO PUEDEN SER CORRECTAS.
    #
    # Se publican LAS DOS a proposito. La de arriba es la del sistema tal como
    # responde y es la comparable con las corridas anteriores; esta dice
    # cuanto de la impertinencia es un error de CATEGORIA --- citar la causal
    # de un mecanismo en un caso de otro --- que una capa de salida puede
    # quitar sin inventar nada.
    #
    # Publicar solo la depurada seria presentar como mejora del modelo lo que
    # es una capa de limpieza. Publicar solo la cruda seria cargarle al modelo
    # un error que el formato del dataset le ensena (59 de 123 ejemplos; ver
    # `data/causas_abiertas.json`).
    #
    # `acierto_juridico` NO se mueve al depurar, y esa es la comprobacion de
    # que esto no maquilla la cifra que importa: la prueba 72 la fija.
    # El modulo importa de `schema` por nombre (ver la cabecera), no el
    # modulo entero: se sigue el mismo patron que `se_abstuvo` y
    # `recortar_al_bloque` mas arriba.
    from schema import depurar_citas
    _dep, _quitadas = [], []
    for _s in salidas:
        _d, _q = depurar_citas(_s)
        _dep.append(_d)
        _quitadas += _q
    _pd = pertinencia_citas(_dep, golds)
    sc["pertinencia_citas_depurada"] = {
        **{k: v for k, v in _pd.items() if k != "por_plano"},
        "citas_quitadas": len(_quitadas),
        "quitadas_por_norma": dict(Counter(_quitadas).most_common()),
        "que_se_quito": (
            "normas puramente procesales citadas en el slot del DERECHO de un "
            "caso cuyo mecanismo NO es el suyo --- el art. 6.1, que es "
            "subsidiariedad, sobre una tutela que procede. No se quita la que "
            "si corresponde al mecanismo emitido: el gold tiene un solo slot "
            "de fundamento, asi que para un caso de `via_ordinaria` el art. "
            "6.1 es lo que pide."),
        "no_anade_nada": (
            "la capa solo QUITA. Poner la cita correcta seria que el motor "
            "decidiera el fundamento, y eso ya lo hacen los brazos hibrido y "
            "agente: seria otro brazo, no una depuracion."),
        "comprobacion": (
            "`acierto_juridico` tiene que salir IDENTICO con y sin depurar. "
            "Si cambia, la capa toco algo mas que las citas."),
    }

    # Acierto segmentado por FIABILIDAD DE LA ETIQUETA (ROADMAP #8).
    #
    # Es la razon de ser del campo: un acierto alto sobre etiquetas que fijo un
    # tercero vale mas que el mismo numero sobre etiquetas que el equipo
    # afirmo. Y si el acierto cae justo en los niveles debiles, puede que lo
    # que falle sea la etiqueta y no el modelo --- que es una hipotesis que hay
    # que poder mirar, no descartar de antemano.
    #
    # Niveles: 1 corte_constitucional · 2 motor_de_reglas_plano ·
    # 3 motor_de_reglas_ponderado · 4 equipo_*
    por_fiab = defaultdict(lambda: {"preds": [], "golds": []})
    for pr, go in zip(preds, golds):
        f = go.get("fiabilidad_etiqueta")
        if f is None:
            continue
        por_fiab[f]["preds"].append(pr)
        por_fiab[f]["golds"].append(go)
    if por_fiab:
        sc["por_fiabilidad_etiqueta"] = {
            f: {"nivel": v["golds"][0].get("nivel_fiabilidad"),
                "n": len(v["golds"]),
                "acc_mecanismo": accuracy([p.get("mecanismo") for p in v["preds"]],
                                          [g["mecanismo"] for g in v["golds"]]),
                "acierto_juridico": acierto_juridico(v["preds"], v["golds"])}
            for f, v in sorted(por_fiab.items(),
                               key=lambda kv: kv[1]["golds"][0].get(
                                   "nivel_fiabilidad", 9))
        }
        sc["por_fiabilidad_etiqueta"]["_lectura"] = (
            "`motor_de_reglas` significa CONSISTENTE con el arbol del art. 6, "
            "no INDEPENDIENTE: los hechos los codifico el mismo equipo que puso "
            "la etiqueta. Solo el nivel 1 tiene fuente externa.")

    # Dónde falla: categorías con al menos un error.
    fallos = defaultdict(lambda: [0, 0])
    for pr, go in zip(preds, golds):
        cat = go.get("categoria", "?")
        fallos[cat][1] += 1
        if pr.get("mecanismo") != go["mecanismo"]:
            fallos[cat][0] += 1
    sc["errores_por_categoria"] = {
        k: f"{v[0]}/{v[1]}" for k, v in sorted(fallos.items()) if v[0]
    }
    return sc


def imprimir(sc: dict) -> None:
    print(f"\n{'='*62}\n  SCORECARD · {sc['sistema']}  (n={sc['n']})\n{'='*62}")
    print(f"{'campo':<14}{'accuracy':>10}{'macro-F1':>10}{'mayorit.':>10}{'delta':>10}")
    print("-" * 62)
    for campo, m in sc["campos"].items():
        d = m["accuracy"] - m["baseline_mayoritaria"]
        print(f"{campo:<14}{m['accuracy']:>9.1%}{m['macro_f1']:>10.1%}"
              f"{m['baseline_mayoritaria']:>10.1%}{d:>+10.1%}")
    print("-" * 62)
    print(f"{'adherencia estructural (5 etiquetas)':<36}{sc['adherencia_estructural']:>7.1%}")
    print(f"{'adherencia de vocabulario':<36}{sc['adherencia_vocabulario']:>7.1%}")
    co = sc.get("coherencia")
    print(f"{'coherencia procede<->mecanismo':<36}"
          + (f"{co:>7.1%}" if co is not None else f"{'no evaluable':>7}"))
    print(f"{'ROUGE-L (prosa)':<36}{sc['rouge_l']:>7.1%}")
    se = sc.get("similitud_embeddings")
    print(f"{'similitud embeddings':<36}"
          + (f"{se:>7.1%}" if se is not None else f"{'(sin libreria)':>7}"))
    print(f"{'acierto jurídico (mecanismo+procede)':<36}{sc['acierto_juridico']:>7.1%}")

    # La abstención indebida se imprime SIEMPRE que exista, también en
    # conjuntos sin casos de abstención: ahí es un error puro, porque todos
    # los casos tienen respuesta correcta. Antes se calculaba y no se mostraba,
    # y eso es tan invisible como no calcularla: en la corrida
    # m1/20261015T192223Z el caso A05 se abstuvo en el eval set y solo
    # aparecía disfrazado de error de mecanismo.
    ab = sc.get("abstencion")
    if ab:
        ac = ab.get("acierto_abstencion")
        if ac is not None:
            print(f"{'se abstuvo donde debía':<36}{ac:>7.1%}"
                  f"   ({ab['n_sin_respuesta_correcta'] - ab['forzo_etiqueta']}"
                  f"/{ab['n_sin_respuesta_correcta']})")
        if ab.get("abstenciones_indebidas"):
            print(f"{'ABSTENCIÓN INDEBIDA':<36}"
                  f"{ab['abstencion_indebida']:>7.1%}"
                  f"   ({ab['abstenciones_indebidas']}"
                  f"/{ab['n_con_respuesta_correcta']} casos CON respuesta)")
            for caso in ab.get("indebidas_en") or []:
                print(f"   se callo en {caso.get('id')} "
                      f"({caso.get('categoria')}, gold "
                      f"{caso.get('mecanismo_gold')})")

    a = sc["alucinacion_normativa"]
    print(f"{'alucinación normativa':<34}{a['tasa_alucinacion']:>9.1%}"
          f"   ({a['citas_inventadas']}/{a['citas_totales']} citas)")
    if a["ejemplos"]:
        print(f"   inventadas: {', '.join(c for c, _ in a['ejemplos'])}")
    # Ámbito completo: incluye las normas que el modelo escribe en la línea de
    # Procedencia, donde la versión anterior no miraba.
    print(f"{'  ...en toda la salida':<34}{a['tasa_alucinacion_salida']:>9.1%}"
          f"   ({a['citas_inventadas_salida']}/{a['citas_totales_salida']} citas)")
    fuera = a.get("inventadas_fuera_del_fundamento")
    if fuera:
        print(f"   inventadas FUERA del campo fundamento: "
              f"{', '.join(c for c, _ in fuera)}")
    pc = sc.get("pertinencia_citas")
    if pc:
        print(f"{'precisión de citas (pertinencia)':<34}{pc['precision_citas']:>9.1%}"
              f"   ({pc['correctas']} ok / {pc['impertinentes']} impertinentes"
              f" / {pc['inventadas']} inventadas)")
        print(f"{'recall de citas':<34}{pc['recall_citas']:>9.1%}")
        if pc["ejemplos_impertinentes"]:
            print(f"   impertinentes: {', '.join(c for c, _ in pc['ejemplos_impertinentes'])}")
        # Los dos planos de la cita. El agregado de arriba los mezcla y por eso
        # contaba como impertinente el art. 86 CP en los casos de tutela.
        pp = pc.get("por_plano", {})
        if pp.get("disponible"):
            cj = pp["cajas"]
            def _pc(x):
                return "     n/d" if x is None else f"{x:>9.1%}"
            print(f"{'  precisión por plano · mecanismo':<34}"
                  f"{_pc(pp['precision_mecanismo'])}"
                  f"   ({cj.get('mecanismo_correcto', 0)} ok /"
                  f" {cj.get('mecanismo_equivocado', 0)} otra vía)")
            print(f"{'  precisión por plano · fondo':<34}"
                  f"{_pc(pp['precision_derecho'])}"
                  f"   ({cj.get('derecho_correcto', 0)} ok /"
                  f" {cj.get('derecho_impertinente', 0)} impertinentes)")
            if pp["ejemplos_mecanismo_equivocado"]:
                print("   vía equivocada: "
                      + ", ".join(c for c, _ in pp["ejemplos_mecanismo_equivocado"]))
    ic = sc.get("ic")
    if ic:
        print("-" * 62)
        print("   intervalos de confianza al 95% (bootstrap, semilla 42):")
        for etq, k in (("acc_mecanismo", "acc_mecanismo"),
                       ("acierto jurídico", "acierto_juridico")):
            v = ic[k]
            print(f"     {etq:<22} {v['punto']:.3f}  "
                  f"[{v['ic_bajo']:.3f}, {v['ic_alto']:.3f}]  "
                  f"±{v['amplitud'] / 2:.3f}  n={v['n']}")
        for t, v in ic.get("por_tipo", {}).items():
            print(f"     {'  · ' + t:<22} {v['punto']:.3f}  "
                  f"[{v['ic_bajo']:.3f}, {v['ic_alto']:.3f}]  "
                  f"±{v['amplitud'] / 2:.3f}  n={v['n']}"
                  + ("  (wilson)" if v.get("metodo") == "wilson" else ""))
    print("-" * 62)
    for t, v in sc["por_tipo"].items():
        print(f"   {t:<12} n={v['n']:<4} acierto jurídico {v['acierto_juridico']:.1%}")
    pf = sc.get("por_fiabilidad_etiqueta")
    if pf:
        print("-" * 62)
        print("   acierto por fiabilidad de la ETIQUETA (1 = fuente externa):")
        for f, v in pf.items():
            if f.startswith("_"):
                continue
            print(f"     [{v['nivel']}] {f:<30} n={v['n']:<4} "
                  f"acc {v['acc_mecanismo']:.1%}  jurídico {v['acierto_juridico']:.1%}")
    if sc["errores_por_categoria"]:
        print("-" * 62)
        print("   errores de mecanismo por categoría:")
        for k, v in sc["errores_por_categoria"].items():
            print(f"     {k:<34} {v}")
    print("=" * 62)


def comparar(a: dict, b: dict) -> None:
    """Lectura honesta del delta: incluye lo que empeoró."""
    print(f"\n{'='*62}\n  {a['sistema']}  ->  {b['sistema']}\n{'='*62}")
    filas = [(f"{c} (acc)", a["campos"][c]["accuracy"], b["campos"][c]["accuracy"])
             for c in CAMPOS_CATEGORICOS]
    filas += [
        ("adherencia estructural", a["adherencia_estructural"], b["adherencia_estructural"]),
        ("adherencia vocabulario", a["adherencia_vocabulario"], b["adherencia_vocabulario"]),
        ("ROUGE-L (prosa)", a["rouge_l"], b["rouge_l"]),
        ("acierto jurídico", a["acierto_juridico"], b["acierto_juridico"]),
        ("alucinación norm.", a["alucinacion_normativa"]["tasa_alucinacion"],
         b["alucinacion_normativa"]["tasa_alucinacion"]),
        ("alucinación (salida)", a["alucinacion_normativa"]["tasa_alucinacion_salida"],
         b["alucinacion_normativa"]["tasa_alucinacion_salida"]),
    ]
    if a.get("pertinencia_citas") and b.get("pertinencia_citas"):
        filas.insert(-1, ("precisión de citas",
                          a["pertinencia_citas"]["precision_citas"],
                          b["pertinencia_citas"]["precision_citas"]))
    if a.get("coherencia") is not None and b.get("coherencia") is not None:
        filas.insert(-2, ("coherencia", a["coherencia"], b["coherencia"]))
    if a.get("similitud_embeddings") is not None and b.get("similitud_embeddings") is not None:
        filas.insert(-2, ("similitud embeddings",
                          a["similitud_embeddings"], b["similitud_embeddings"]))

    print(f"{'métrica':<24}{'antes':>10}{'después':>10}{'delta':>10}")
    print("-" * 62)
    for nombre, x, y in filas:
        signo = "  " if abs(y - x) < 1e-9 else ("+ " if y > x else "- ")
        print(f"{nombre:<24}{x:>9.1%}{y:>10.1%}{signo}{y-x:>+8.1%}")
    print("=" * 62)
    peor = [n for n, x, y in filas if y < x - 1e-9]
    if peor:
        print(f"EMPEORÓ en: {', '.join(peor)}  <- reportar esto, no esconderlo")
    else:
        print("No empeoró en ninguna métrica medida.")


def guardar(sc: dict, ruta: str) -> None:
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(sc, f, ensure_ascii=False, indent=2)
