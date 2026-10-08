"""Puertas de calidad de data/dataset_v2.jsonl (ver tools/dataset_v2.py).

Las mismas ideas que tools/dataset_quality.py, por modo:

  todos  contexto no vacio; sin rutas incorrectas ni entidades inventadas (las
         guardias de M2), sin promesas de resultado, urgencia -> ayuda
         inmediata, ids unicos, respuestas que no se repiten dentro de una
         categoria; NINGUNA pregunta (nueva o tomada del dataset de M1) igual a
         una del eval set (eval_set.solapamiento) ni parecida (TF-IDF >= 0.55).
  B1     cita al menos un articulo de las fuentes declaradas, como "articulo N de
         <norma>"; TODO articulo citado esta en el contexto, de esa misma norma
         (no basta el numero: el articulo 20 de la Ley 100 no respalda el 20 de
         la Ley 820); un plazo solo si su numero esta en el contexto; 30-90 palabras.
  B2     empieza con la frase de escape exacta y no cita nada; hasta 45 palabras.
  B3     como B1, y ademas dice que una parte no esta respaldada.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict

from tools.dataset_quality import (
    AYUDA_INMEDIATA,
    CITA_NORMATIVA,
    PLAZO_EXACTO,
    PROMESA,
    SOLAPAMIENTO_MAX,
    URGENCIA,
    _shingles,
    menciona_mecanismo,
)

PALABRAS = {"B1": (30, 90), "B2": (10, 45), "B3": (30, 90)}
MAX_USOS_ARTICULO = 3            # un articulo es fuente de a lo sumo 3 ejemplos
PARECIDO_MAX_V2 = 0.8            # TF-IDF entre dos preguntas de v2
PROPORCION_MIN_ESCAPE = 1 / 3    # regla de Tomas: 1 de cada 3 con contexto que no responde

_ARTICULO = re.compile(r"\bart(?:[ií]culos?|s?\.)\s*(\d+(?:\s*-\s*[A-Za-z]|[A-Za-z](?![a-z]))?)", re.IGNORECASE)
_NORMA_CON_NUMERO = re.compile(r"\b(ley|decreto)\s+(\d+)\s+de\s+(\d{4})\b", re.IGNORECASE)
_FALTA_PARTE = re.compile(
    r"no tengo informaci[oó]n verificada sobre|no (?:aparece|est[aá]) en (?:los fragmentos|el contexto|lo que tengo)"
    r"|no tengo (?:una )?norma (?:verificada )?(?:que|para)", re.IGNORECASE)


def _norm(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t)


def _claves_de_norma(cita: str) -> set[str]:
    """Formas con las que una respuesta puede nombrar la norma de un fragmento.
    "Ley 820 de 2003 (Regimen de arrendamiento...), Articulo 20" ->
    {"ley 820 de 2003", "regimen de arrendamiento..."}."""
    fuente = cita.split("), Articulo")[0].split(", Articulo")[0]
    claves = set()
    m = re.match(r"\s*(.*?)\s*\((.*)\)?\s*$", fuente)
    base, comun = (m.group(1), m.group(2).rstrip(")")) if m and "(" in fuente else (fuente, "")
    for c in (base, comun):
        c = _norm(c).strip()
        if c:
            claves.add(c)
    if "constitucion" in _norm(base):
        claves.add("constitucion")
    return claves


def _articulo_normalizado(numero: str) -> str:
    from tools.rag.chunk import normalizar_numero

    return normalizar_numero(re.sub(r"\s+", "", numero)).upper()


# "del mismo codigo" no entraba: en "del", el "el" va pegado y el  no engancha,
# mientras que "de la misma ley" si pasa porque ahi el "la" queda suelto. La
# anafora mas natural en espanol juridico es justo la que fallaba.
_MISMA_NORMA = re.compile(r"\b(?:la misma (?:ley|norma)|esa (?:ley|norma)|(?:el|del) mismo (?:codigo|decreto)|ese (?:codigo|decreto))\b")


# Ejemplo de v2 -> caso del eval set que el TF-IDF marca parecido, revisado a mano:
# preguntan otra cosa.
REVISADAS_DISTINTAS_V2: dict[tuple[int, int], str] = {
    (2006, 9108): "subarriendo sin permiso; 9108 es 'Eso lo puedo pasar a nombre mio?', ambigua de 6 "
                  "palabras: el parecido es solo 'puede pasar'",
}


def citas(respuesta: str, contexto: list[dict]) -> tuple[list[str], list[str], list[str]]:
    """(respaldadas, no_respaldadas, normas_ajenas).

    Una cita "articulo N" esta respaldada si algun fragmento del contexto trae el
    articulo N y la respuesta nombra la norma de ESE fragmento cerca de la cita
    (80 caracteres despues o 60 antes), o dice "la misma ley" y la norma citada
    justo antes trae ese articulo. normas_ajenas: "Ley N de AAAA" nombradas en la
    respuesta que no estan en el contexto."""
    texto = respuesta or ""
    respaldadas, no_respaldadas = [], []
    ultima: set[str] = set()
    for m in _ARTICULO.finditer(texto):
        numero = _articulo_normalizado(m.group(1))
        ventana = _norm(texto[max(0, m.start() - 60): m.end() + 80])
        candidatos = [f for f in contexto if numero in {_articulo_normalizado(a) for a in f["articulos"]}]
        nombradas = [f for f in candidatos if any(c in ventana for c in _claves_de_norma(f["cita"]))]
        if not nombradas and _MISMA_NORMA.search(ventana):
            nombradas = [f for f in candidatos if _claves_de_norma(f["cita"]) & ultima]
        if nombradas:
            respaldadas.append(f"articulo {numero}")
            ultima = _claves_de_norma(nombradas[0]["cita"])
        else:
            no_respaldadas.append(f"articulo {numero}")
    claves_contexto = set().union(*[_claves_de_norma(f["cita"]) for f in contexto]) if contexto else set()
    ajenas = [m.group(0) for m in _NORMA_CON_NUMERO.finditer(texto)
              if _norm(m.group(0)) not in claves_contexto]
    return respaldadas, no_respaldadas, ajenas


def _cita_oraculo(r: dict, respaldadas: list[str]) -> bool:
    """¿Cita al menos uno de los articulos declarados en `fuentes`?"""
    declarados = {_articulo_normalizado(f.rsplit(":", 1)[1]) for f in r["fuentes"]}
    return any(c.split()[-1] in declarados for c in respaldadas)


def _plazo_sin_respaldo(r: dict) -> bool:
    from tools.rag.verificacion import numero_en_letras

    respuesta = r["messages"][-1]["content"]
    contexto = _norm(r["messages"][1]["content"])
    for m in PLAZO_EXACTO.finditer(respuesta):
        n = int(re.match(r"\d+", m.group(0)).group())
        if str(n) not in contexto and _norm(numero_en_letras(n)) not in contexto:
            return True
    return False


def revisar(r: dict, mapa=None) -> list[str]:
    """Problemas de un ejemplo, como etiquetas de puerta."""
    from tools.evaluation import entity_metric, rutas
    from tools.evaluation.ragas_metrics import es_valvula_de_escape
    from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

    modo = r["modo"]
    pregunta = r.get("pregunta") or r["messages"][1]["content"].split("PREGUNTA DEL USUARIO:", 1)[-1].strip()
    respuesta = r["messages"][-1]["content"]
    problemas = []
    if not r.get("contexto") or "CONTEXTO" not in r["messages"][1]["content"]:
        problemas.append("contexto vacio")

    lo, hi = PALABRAS[modo]
    if not lo <= len(respuesta.split()) <= hi:
        problemas.append("longitud")
    if PROMESA.search(respuesta):
        problemas.append("promesas de resultado")
    if URGENCIA.search(pregunta) and not AYUDA_INMEDIATA.search(respuesta):
        problemas.append("urgencia sin ayuda inmediata")
    if rutas.rutas_incorrectas(respuesta, pregunta):
        problemas.append("ruta incorrecta")
    if entity_metric.find_fabricated_entities(respuesta):
        problemas.append("entidad inventada")

    if modo == "B2":
        if not (es_valvula_de_escape(respuesta)
                and _norm(respuesta).startswith(_norm(RESPUESTA_SIN_CONTEXTO))):
            problemas.append("escape")
        if CITA_NORMATIVA.search(respuesta) or _ARTICULO.search(respuesta):
            problemas.append("cita en escape")
    else:
        respaldadas, no_respaldadas, ajenas = citas(respuesta, r["contexto"])
        if no_respaldadas or ajenas:
            problemas.append("cita no respaldada")
        if not _cita_oraculo(r, respaldadas):
            problemas.append("no cita la fuente")
        if _plazo_sin_respaldo(r):
            problemas.append("plazo sin respaldo")
        if not menciona_mecanismo(respuesta):
            problemas.append("mecanismo legal")
        if modo == "B3" and not _FALTA_PARTE.search(respuesta):
            problemas.append("B3 sin la parte que falta")
    return problemas


def analizar(registros: list[dict]) -> dict:
    from tools.evaluation import eval_set
    from tools.evaluation.similitud import IndiceTfidf

    por_ejemplo = {r["id"]: revisar(r) for r in registros}

    por_categoria = defaultdict(list)
    for r in registros:
        por_categoria[r["category"]].append(r)
    repetidos = []
    for cat, items in por_categoria.items():
        firmas = [(r["id"], _shingles(r["messages"][-1]["content"])) for r in items if r["modo"] != "B2"]
        for i in range(len(firmas)):
            for j in range(i + 1, len(firmas)):
                a, b = firmas[i][1], firmas[j][1]
                if a and b and len(a & b) / len(a | b) >= SOLAPAMIENTO_MAX:
                    repetidos.append((cat, firmas[i][0], firmas[j][0]))

    # TODAS las preguntas contra el eval set (tambien las tomadas del dataset de
    # M1: entrar al train de v2 las haria fuga aunque en M1 estuvieran en val).
    # Igual normalizada -> eval_set.solapamiento; parecida -> TF-IDF, salvo los
    # pares que eval_set.REVISADAS_DISTINTAS ya dio por distintos.
    ev = eval_set.load_eval_set()
    def _pregunta(r):
        return r.get("pregunta") or r["messages"][1]["content"].split("PREGUNTA DEL USUARIO:", 1)[-1].strip()
    solo_preguntas = [{"messages": [{}, {"content": _pregunta(r)}]} for r in registros]
    # Solo es fuga si el ejemplo cae en el train de v2 (split_v2 lo manda al lado
    # de su pregunta base): uno que cae en val no se entrena.
    from tools.evaluation import dataset as m1_dataset

    _, val_v2 = m1_dataset.split_v2(registros, m1_dataset.load_records())
    en_val = {r["id"] for r in val_v2}
    en_train = [r for r in registros if r["id"] not in en_val]
    solo_preguntas = [{"messages": [{}, {"content": _pregunta(r)}]} for r in en_train]
    iguales = eval_set.solapamiento(ev, solo_preguntas, [])["en_train"]
    fuga = [(None, i, 1.0) for i in iguales]
    indice = IndiceTfidf([e["messages"][1]["content"] for e in ev])
    for r in en_train:
        mejor = indice.parecidos(_pregunta(r), 1)
        if mejor and mejor[0][1] >= eval_set.UMBRAL_PARECIDO:
            eid = ev[mejor[0][0]]["id"]
            if eid not in eval_set.REVISADAS_DISTINTAS and (r["id"], eid) not in REVISADAS_DISTINTAS_V2:
                fuga.append((r["id"], eid, mejor[0][1]))

    # Variedad: un mismo articulo como fuente de muchos ejemplos ensena a
    # recitar ese articulo, no a leer el contexto; y dos preguntas casi iguales
    # son el mismo ejemplo dos veces.
    usos = Counter(f for r in registros for f in r.get("fuentes", []))
    sobreusados = sorted(f for f, n in usos.items() if n > MAX_USOS_ARTICULO)
    preguntas = [_pregunta(r) for r in registros]
    indice_v2 = IndiceTfidf(preguntas) if len(preguntas) > 1 else None
    casi_iguales = []
    for i, q in enumerate(preguntas):
        for j, s in (indice_v2.parecidos(q, 3) if indice_v2 else []):
            if j > i and s >= PARECIDO_MAX_V2:
                casi_iguales.append((registros[i]["id"], registros[j]["id"], round(s, 2)))
    # Regla de Tomas: de cada 3 ejemplos, 1 con contexto que no responde (B2).
    n_b2 = sum(1 for r in registros if r["modo"] == "B2")
    escape_corto = len(registros) >= 20 and n_b2 / len(registros) < PROPORCION_MIN_ESCAPE

    ids = [r["id"] for r in registros]
    return {
        "articulos_sobreusados": sobreusados,
        "preguntas_casi_iguales": casi_iguales,
        "proporcion_escape": (n_b2, len(registros), escape_corto),
        "total": len(registros),
        "por_modo": Counter(r["modo"] for r in registros),
        "por_categoria": {c: len(v) for c, v in sorted(por_categoria.items())},
        "problemas": {i: p for i, p in por_ejemplo.items() if p},
        "repetidos": repetidos,
        "fuga_eval_set": fuga,
        "ids_duplicados": [i for i, n in Counter(ids).items() if n > 1],
    }


def reportar(a: dict) -> list[str]:
    fallos = []
    for clave in ("articulos_sobreusados", "preguntas_casi_iguales"):
        if a[clave]:
            print(f"{clave}: {a[clave][:20]}")
    print(f"Dataset v2: {a['total']} ejemplos | por modo: {dict(sorted(a['por_modo'].items()))}")
    print(f"Categorias: {len(a['por_categoria'])}\n")
    conteo = Counter(p for ps in a["problemas"].values() for p in ps)
    print("PUERTAS DE CALIDAD")
    for puerta in ("contexto vacio", "longitud", "promesas de resultado", "urgencia sin ayuda inmediata",
                   "ruta incorrecta", "entidad inventada", "mecanismo legal",
                   "escape", "cita en escape", "cita no respaldada", "no cita la fuente",
                   "plazo sin respaldo", "B3 sin la parte que falta"):
        n = conteo.get(puerta, 0)
        print(f"  [{'OK  ' if not n else 'FALLA'}] {puerta}: {n}")
        if n:
            fallos.append(puerta)
    n_b2, total, corto = a["proporcion_escape"]
    print(f"  [{'FALLA' if corto else 'OK  '}] escapes (B2) >= 1 de cada 3: {n_b2}/{total}")
    if corto:
        fallos.append("proporcion de escapes")
    for etiqueta, lista in (("repeticion", a["repetidos"]), ("fuga al eval set", a["fuga_eval_set"]),
                            (f"articulo fuente de mas de {MAX_USOS_ARTICULO} ejemplos", a["articulos_sobreusados"]),
                            ("preguntas casi iguales", a["preguntas_casi_iguales"]),
                            ("ids duplicados", a["ids_duplicados"])):
        print(f"  [{'OK  ' if not lista else 'FALLA'}] {etiqueta}: {len(lista)}")
        if lista:
            fallos.append(etiqueta)
    if a["problemas"]:
        print("\n  Ejemplos con problemas (primeros 15):")
        for i, ps in list(a["problemas"].items())[:15]:
            print(f"    {i}: {', '.join(ps)}")
    return fallos
