"""
Las cuatro métricas de RAGAS, implementadas aquí.

Por qué no se usa la librería directamente: `ragas` cambia de API con frecuencia
y exige envoltorios de LangChain para apuntar a un proveedor que no sea OpenAI.
Implementarlas tiene tres ventajas para un trabajo que se va a defender:

  - se puede explicar exactamente qué calcula cada número;
  - no se cae cuando la librería rompe compatibilidad;
  - y sobre todo, **dos de las cuatro se pueden calcular de forma determinista**
    con la verdad de campo que ya tenemos.

Ese último punto importa. RAGAS estima context precision y context recall
preguntándole a un LLM si el contexto es relevante. Nosotros sabemos qué
artículos debían recuperarse, porque el campo `fundamento` del gold lo dice.
Una medida exacta es mejor que una estimada, así que se reportan las dos y se
contrastan: si divergen mucho, el problema es del juez, no del sistema.

    faithfulness        ¿lo que afirma la respuesta se sostiene en el contexto?
    context_precision   de lo recuperado, ¿cuánto servía?
    context_recall      de lo que hacía falta, ¿cuánto se recuperó?
    answer_relevancy    ¿la respuesta contesta lo que se preguntó?

El notebook incluye además una celda opcional que corre la librería real sobre
una muestra, para contrastar.
"""
from __future__ import annotations
import json
import re

import schema

# --------------------------------------------------------------------------
# Versiones deterministas: usan el gold, no un juez
# --------------------------------------------------------------------------
from rag import _cita_de, cubre   # una sola definicion de "esta cita la cubre este fragmento"


def context_precision_exacta(contextos: list[list[dict]], golds: list[dict]) -> float:
    """De los fragmentos recuperados, qué fracción aparece en el `fundamento` del gold.

    Ponderada por rango: un acierto en la primera posición vale más que en la
    quinta, porque es lo que el generador lee primero y con más peso. Es la
    *average precision* clásica: se promedia la precisión en cada rango donde
    cae un fragmento relevante.

    ARREGLO DE UN DEFECTO QUE DABA VALORES IMPOSIBLES

    La versión anterior normalizaba por `min(len(esperadas), len(frags))`, o
    sea por el número de CITAS esperadas. Pero el numerador cuenta FRAGMENTOS
    relevantes, y una misma cita puede estar cubierta por varios fragmentos
    --- el corpus está troceado, así que `art. 49 CP` puede caer en dos
    pedazos. Cuando eso pasa, el numerador supera al denominador y la métrica
    se va por encima de 1.

    Lo destapó el brazo oráculo del ROADMAP #10, que recupera a propósito todo
    fragmento que cubra cada cita: **35 de los 69 casos del eval set daban
    `context_precision > 1.0`, con un máximo de 2.6667**. Una precisión mayor
    que uno no es un número alto: es un número sin significado.

    Ahora se normaliza por el número de fragmentos relevantes RECUPERADOS, que
    es la cantidad que el numerador suma. Queda acotada en [0, 1] y vale 1
    cuando todos los relevantes vienen primero. La cobertura la mide
    `context_recall_exacto`, que es su complemento: esta dice si lo recuperado
    está bien ordenado, aquélla si estaba todo.

    CONSECUENCIA PARA LAS CORRIDAS ANTERIORES: el `context_precision` de
    `results/m3_ragas.json` anterior a este arreglo NO es comparable con el de
    aquí. Las demás métricas de RAGAS no se tocan.
    """
    # Los casos SIN citas esperadas --- los de abstención, que no tienen
    # `fundamento` --- se excluyen del promedio en vez de entrar como 0. No hay
    # contexto que recuperar ahí, así que contarlos como fallo de retrieval
    # hundía la métrica por una razón ajena al retrieval: con los 6 casos de
    # abstención del eval v2, el oráculo (que tiene el contexto perfecto por
    # construcción) daba 0.9130 en vez de 1.0. Es el mismo criterio que ya
    # usaba `context_recall_exacto`, cuyo denominador es la suma de esperadas.
    total, n = 0.0, 0
    for frags, g in zip(contextos, golds):
        esperadas = set(schema.citas(g["fundamento"]))
        if not esperadas:
            continue
        n += 1
        if not frags:
            continue                          # se recuperó nada: aporta 0
        aciertos, suma = 0, 0.0
        for i, f in enumerate(frags, 1):
            if any(cubre(f, e) for e in esperadas):
                aciertos += 1
                suma += aciertos / i          # precisión en el rango i
        if aciertos:
            total += suma / aciertos
    return total / n if n else 0.0


def context_recall_exacto(contextos: list[list[dict]], golds: list[dict]) -> float:
    """De los artículos que el gold cita, qué fracción se recuperó."""
    num = den = 0
    for frags, g in zip(contextos, golds):
        esperadas = set(schema.citas(g["fundamento"]))
        den += len(esperadas)
        num += sum(any(cubre(f, e) for f in frags) for e in esperadas)
    return num / den if den else 0.0


def faithfulness_exacta(salidas: list[str], contextos: list[list[dict]]) -> float:
    """Fracción de citas de la respuesta que están respaldadas por el contexto.

    Es la versión estricta de faithfulness para este dominio: afirmar un
    artículo que no se recuperó es exactamente lo que el RAG debía impedir.
    """
    num = den = 0
    for s, frags in zip(salidas, contextos):
        emitidas = schema.citas(schema.parse_salida(s).get("fundamento"))
        den += len(emitidas)
        num += sum(any(cubre(f, c) for f in frags) for c in emitidas)
    return num / den if den else 0.0


# --------------------------------------------------------------------------
# Versiones con juez, como las define RAGAS
# --------------------------------------------------------------------------
P_FAITHFULNESS = """Eres un verificador. Vas a recibir un CONTEXTO (artículos de la ley colombiana)
y una RESPUESTA de un sistema.

Descompón la respuesta en afirmaciones verificables y di, para cada una, si el CONTEXTO
la sostiene. Una afirmación que el contexto no menciona NO está sostenida, aunque sea
verdadera en el mundo.

Responde SOLO con JSON: {"total": <n>, "sostenidas": <n>}"""

P_RELEVANCIA_CTX = """Eres un verificador. Vas a recibir una CONSULTA y un FRAGMENTO de ley colombiana.

¿El fragmento aporta algo para resolver esa consulta?

Responde SOLO con JSON: {"relevante": true|false}"""

P_PREGUNTAS = """Vas a recibir la RESPUESTA de un sistema de triaje jurídico.

Escribe las 3 preguntas de un ciudadano que esta respuesta contestaría. No inventes
contexto que no esté en la respuesta.

Responde SOLO con JSON: {"preguntas": ["...", "...", "..."]}"""


# Revisión docente: protocolo explícito para las nuevas mediciones del main
# migrado. No cambia las métricas exactas ni los resultados históricos de M3.
PROTOCOLO_JUEZ = "amparo-juez-validado-v1"


def _validar_largos(*listas) -> None:
    if len({len(xs) for xs in listas}) > 1:
        raise ValueError("Las entradas de evaluación deben tener igual longitud.")


def _json(t: str) -> dict:
    if not isinstance(t, str):
        return {}
    m = re.search(r"\{.*\}", t, re.DOTALL)
    try:
        obj = json.loads(m.group(0)) if m else {}
    except (json.JSONDecodeError, ValueError):
        return {}
    return obj if isinstance(obj, dict) else {}


def _cobertura(diagnostico, nombre, estados, denominador, unidad):
    """Índices de entrada (base cero); no guarda relatos ni datos personales."""
    if diagnostico is None:
        return
    validos = [i for i, e in enumerate(estados) if e in ("valido", "sin_contexto")]
    no_aplica = [i for i, e in enumerate(estados) if e == "sin_afirmaciones"]
    invalidos = [i for i, e in enumerate(estados) if e == "veredicto_invalido"]
    diagnostico[nombre] = {
        "casos_totales": len(estados), "casos_validos": len(validos),
        "indices_validos": validos, "indices_invalidos": invalidos,
        "indices_no_aplicables": no_aplica,
        "estados_por_caso": estados, "denominador": denominador,
        "unidad_denominador": unidad,
    }


def faithfulness_juez(juez, salidas, contextos, *, diagnostico=None) -> float | None:
    """Conserva la razón por afirmaciones; sin medición válida devuelve None.

    Un conteo inválido no se recorta ni se convierte en cero. Las excepciones
    operativas de _llamar siguen propagándose: no son puntajes del sistema.
    """
    _validar_largos(salidas, contextos)
    num = den = 0
    estados = []
    for s, frags in zip(salidas, contextos):
        ctx = "\n\n".join(f"[{f['articulo']} {f['norma']}] {f['texto']}" for f in frags)
        d = _json(juez._llamar(P_FAITHFULNESS, f"CONTEXTO:\n{ctx}\n\nRESPUESTA:\n{s}"))
        t, ok = d.get("total"), d.get("sostenidas")
        # bool es subtipo de int en Python, pero no es un conteo del juez.
        if type(t) is not int or type(ok) is not int or not 0 <= ok <= t:
            estados.append("veredicto_invalido")
        elif t == 0:
            estados.append("sin_afirmaciones")
        else:
            estados.append("valido")
            num += ok
            den += t
    juez.guardar_cache()
    _cobertura(diagnostico, "faithfulness", estados, den, "afirmaciones")
    return num / den if den else None


def context_precision_juez(juez, consultas, contextos, *, diagnostico=None) -> float | None:
    """Average precision por consulta, solo con rankings completamente medidos.

    Se conserva la convención existente: no recuperar fragmentos aporta cero.
    Un JSON inválido o un string "false" NO es un booleano medido. Si un
    fragmento falla, se excluye esa consulta, sin comprimir su ranking.
    """
    _validar_largos(consultas, contextos)
    total, n = 0.0, 0
    estados = []
    for q, frags in zip(consultas, contextos):
        if not frags:
            estados.append("sin_contexto")
            n += 1
            continue
        rel = []
        for f in frags:
            d = _json(juez._llamar(
                P_RELEVANCIA_CTX,
                f"CONSULTA:\n{q}\n\nFRAGMENTO:\n[{f['articulo']} {f['norma']}] {f['texto']}"))
            rel.append(d.get("relevante"))
        if any(type(r) is not bool for r in rel):
            estados.append("veredicto_invalido")
            continue
        aciertos, suma = 0, 0.0
        for i, r in enumerate(rel, 1):
            if r:
                aciertos += 1
                suma += aciertos / i
        total += suma / max(1, sum(rel))
        n += 1
        estados.append("valido")
    juez.guardar_cache()
    _cobertura(diagnostico, "context_precision", estados, n, "consultas")
    return total / n if n else None


def answer_relevancy(juez, relatos, salidas, encoder=None, *, diagnostico=None) -> float | None:
    """Preserva el coseno medio; no trata strings como listas de preguntas."""
    import numpy as np
    _validar_largos(relatos, salidas)
    sims, estados = [], []
    for relato, s in zip(relatos, salidas):
        d = _json(juez._llamar(P_PREGUNTAS, s))
        qs = d.get("preguntas")
        if not isinstance(qs, list) or not qs or not all(
                isinstance(q, str) and q.strip() for q in qs):
            estados.append("veredicto_invalido")
            continue
        if encoder is None:
            from metricas import _encoder
            encoder = _encoder()
        e = np.asarray(encoder.encode([relato] + qs, normalize_embeddings=True), dtype=float)
        if (e.ndim != 2 or e.shape[0] != len(qs) + 1 or e.shape[1] == 0
                or not np.isfinite(e).all()):
            raise ValueError("El encoder debe devolver un vector finito por texto.")
        valor = float(np.mean(e[1:] @ e[0]))
        if not np.isfinite(valor):
            raise ValueError("El encoder produjo una similitud no finita.")
        sims.append(valor)
        estados.append("valido")
    juez.guardar_cache()
    _cobertura(diagnostico, "answer_relevancy", estados, len(sims), "respuestas")
    return sum(sims) / len(sims) if sims else None


# --------------------------------------------------------------------------
def evaluar(nombre: str, salidas, contextos, golds, relatos=None,
            juez=None, consultas=None) -> dict:
    """Mantiene claves/escala válidas; añade protocolo y cobertura del juez.

    None se serializa como null. Un promedio parcial debe leerse junto con
    cobertura_juez; no es una medición completa de todos los casos.
    """
    _validar_largos(salidas, contextos, golds)
    if relatos is not None:
        _validar_largos(salidas, relatos)
    if consultas is not None:
        _validar_largos(salidas, consultas)
    out = {
        "sistema": nombre,
        "n": len(golds),
        "exactas": {
            "faithfulness": faithfulness_exacta(salidas, contextos),
            "context_precision": context_precision_exacta(contextos, golds),
            "context_recall": context_recall_exacto(contextos, golds),
        },
    }
    if juez is not None:
        diagnostico = {}
        textos = relatos if relatos is not None else [g["relato"] for g in golds]
        preguntas = consultas if consultas is not None else textos
        out["juez"] = {
            "faithfulness": faithfulness_juez(juez, salidas, contextos, diagnostico=diagnostico),
            "context_precision": context_precision_juez(
                juez, preguntas, contextos, diagnostico=diagnostico),
            "answer_relevancy": answer_relevancy(
                juez, textos, salidas, diagnostico=diagnostico),
        }
        out["protocolo_juez"] = PROTOCOLO_JUEZ
        out["cobertura_juez"] = diagnostico
    return out


def _porcentaje(valor, ancho):
    return f"{'N/D':>{ancho}}" if valor is None else f"{valor:>{ancho}.1%}"


def imprimir(rs: list[dict]) -> None:
    print(f"\n{'='*78}\n  RAGAS · exacto (contra el gold) vs estimado (juez)\n{'='*78}")
    print(f"{'sistema':<26}{'faithf.':>9}{'ctx prec':>10}{'ctx rec':>9}"
          f"{'| faithf.':>11}{'ctx prec':>10}{'ans rel':>9}")
    print("-" * 78)
    for r in rs:
        e, j = r["exactas"], r.get("juez", {})
        fila = (f"{r['sistema']:<26}{e['faithfulness']:>8.1%}"
                f"{e['context_precision']:>10.1%}{e['context_recall']:>9.1%}")
        if j:
            fila += (_porcentaje(j['faithfulness'], 10)
                     + _porcentaje(j['context_precision'], 10)
                     + _porcentaje(j['answer_relevancy'], 9))
        print(fila)
        for metrica, d in r.get("cobertura_juez", {}).items():
            print(f"  {metrica}: {d['casos_validos']}/{d['casos_totales']} casos válidos; "
                  f"denominador={d['denominador']} {d['unidad_denominador']}")
    print("=" * 78)
    print("  exacto = contra el `fundamento` del gold · estimado = lo que juzga el LLM")
    print("  Si divergen mucho, el sospechoso es el juez, no el sistema.")
    print("  N/D = sin medición válida; no es cero. Revisar cobertura_juez.")
