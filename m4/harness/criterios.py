"""T5: criterios nuevos del harness multimodal de M4.

VIVE EN m4/harness/ (NO en src/: la huella del codigo,
`corridas.version_codigo()`, hashea src/*.py, y cualquier cambio ahi
invalida el sello que revisa data/verificar_entrega.py). src/ solo se importa.

QUE ES Y QUE NO ES
  - `harness()` de src/harness.py NO se toca ni se envuelve para los casos
    con imagen: sigue siendo la fuente de los numeros de M3 (casos sin imagen).
  - `calificar()` de aqui es NUEVO. No existe una funcion con ese nombre en
    src/harness.py (el plan dice "calificar/harness"; la real es harness()).
    Califica los casos con imagen y se apoya en el parser de M3
    (`schema.parse_salida`, `schema.se_abstuvo`) para no reinventar como se
    lee una salida de Amparo.

CONTRATO DE ENTRADA
  caso  : dict con las columnas de casos_m4.csv (id, pregunta, imagen,
          esperado, criterio, tipo).
  traza : dict con lo que paso en el pipeline para ese caso:
            {"crudo": str, "js": dict | None, "salida": str}
          `js` es el JSON que devolvio ver() (None si no se pudo parsear);
          `salida` es la respuesta FINAL de M3. Los criterios `campos` y
          `valvula` califican la lectura del VLM (js), no la salida de M3,
          por eso necesitan la traza completa y no solo el texto final.

FORMATO DE `esperado` POR CRITERIO
  Lo define T5 y T4 (Lucas) escribe casos_m4.csv sobre el. El contrato
  completo, con la justificacion, esta en m4/eval_set/FORMATO_CASOS.md. Aqui
  lo implementan las funciones `_esperado_*`: validar_casos() y las notas leen
  el formato de ahi, asi no pueden discrepar.
  exacto   : clave de mecanismo (tutela | accion_popular |
             accion_cumplimiento | habeas_corpus | via_ordinaria) o
             `no_determinable` si el caso debe terminar en abstencion.
  campos   : objeto JSON con los campos que se exigen, p. ej.
             {"tipo_documento": "oficio", "plazo_dias": 15}. Los campos que
             no aparecen en `esperado` no se califican. Comparacion por campo:
             tipo_documento igual (y del vocabulario del VLM), plazo_dias
             entero igual, entidad/fecha/pretension_visible como fragmento
             contenido en lo que leyo el VLM. null no se admite (eso es valvula).
  valvula  : campos que DEBEN venir null, separados por `|`, p. ej.
             `fecha|plazo_dias`.
  juez_vlm : vacio (se juzga la salida final contra la imagen).
  tipo     : normal | adversarial (cerrado).

Un `esperado` mal formado no es nota 0: es error de autoria y lanza
ValueError. validar_casos() lo detecta antes de correr.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]  # m4/harness/criterios.py -> raiz del repo

# Los campos que INSTRUCCION_DOMINIO le pide al VLM (README_PLAN 3.1, celda 8
# del notebook de M4).
CAMPOS_VLM = ("tipo_documento", "entidad", "fecha", "plazo_dias", "pretension_visible")
TIPOS_DOCUMENTO = ("notificacion", "oficio", "respuesta_peticion", "sentencia", "otro")
# Campos de texto libre: el VLM los parafrasea o les agrega texto, asi que
# `esperado` es un fragmento que debe aparecer en lo leido, no el valor entero.
CAMPOS_FRAGMENTO = ("entidad", "fecha", "pretension_visible")
CRITERIOS_VALIDOS = ("exacto", "campos", "valvula", "juez_vlm")
TIPOS_CASO = ("normal", "adversarial")
COLUMNAS = ("id", "pregunta", "imagen", "esperado", "criterio", "tipo")
VALVULA_TEXTO = "no se aprecia en la imagen"
ESPERADO_ABSTENCION = "no_determinable"
MIN_CASOS = 5


def _asegurar_src() -> None:
    """src/ no es un paquete (no hay __init__.py): sus modulos se importan
    planos (`import schema`), asi que hay que poner src/ en sys.path."""
    src = str(RAIZ / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _schema():
    _asegurar_src()
    import schema  # puro Python (json, re, unicodedata, pathlib): importable sin GPU
    return schema


def _reglas_mecanismos() -> tuple[str, ...]:
    _asegurar_src()
    from reglas import MECANISMOS  # vocabulario cerrado de mecanismos (tupla)
    return MECANISMOS


def _texto(valor) -> str:
    """Celda del CSV como texto. None (csv) y NaN (pandas) son celda vacia."""
    if valor is None or valor != valor:  # NaN != NaN
        return ""
    return str(valor)


def _norm(texto) -> str:
    """Minusculas + sin tildes, mismo criterio de normalizacion del proyecto.
    Ademas junta los espacios: el VLM puede partir un nombre en dos lineas."""
    s = unicodedata.normalize("NFKD", str(texto).strip().lower())
    return " ".join("".join(c for c in s if not unicodedata.combining(c)).split())


def _entero(valor) -> int | None:
    """15, "15", 15.0 y "15.0" -> 15. Cualquier otra cosa (bool, "15 dias",
    15.5, null) -> None: la instruccion del VLM pide plazo_dias como entero."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    try:
        f = float(str(valor).strip())
    except ValueError:
        return None
    return int(f) if f.is_integer() else None


def _es_nulo(valor) -> bool:
    """null de JSON, o la valvula escrita como texto en vez de null."""
    if valor is None:
        return True
    v = _norm(valor)
    return v in ("", "null", "none") or VALVULA_TEXTO in v


# --------------------------------------------------------------------------
# Lectura de `esperado`. Un solo sitio define que es "bien formado": las notas
# y validar_casos() llaman a estas funciones, asi no pueden discrepar.
# Contrato: m4/eval_set/FORMATO_CASOS.md.
# --------------------------------------------------------------------------
def _esperado_exacto(caso: dict) -> str:
    esperado = _norm(_texto(caso.get("esperado")))
    validos = set(_reglas_mecanismos()) | {ESPERADO_ABSTENCION}
    if esperado not in validos:
        raise ValueError(f"caso {caso.get('id')}: `exacto` espera una de {sorted(validos)}, "
                         f"no {_texto(caso.get('esperado'))!r}")
    return esperado


def _esperado_campos(caso: dict) -> dict:
    cid = caso.get("id")
    try:
        esperado = json.loads(_texto(caso.get("esperado")))
    except json.JSONDecodeError:
        raise ValueError(f"caso {cid}: `campos` espera un objeto JSON en `esperado`") from None
    if not isinstance(esperado, dict) or not esperado:
        raise ValueError(f"caso {cid}: `campos` espera un objeto JSON no vacio en `esperado`")
    desconocidos = sorted(set(esperado) - set(CAMPOS_VLM))
    if desconocidos:
        # Un campo mal escrito no se calificaria nunca y el caso pasaria por
        # bueno con menos exigencia de la que su autor quiso.
        raise ValueError(f"caso {cid}: `campos` trae campos que el VLM no extrae: {desconocidos}")
    for campo, valor in esperado.items():
        if valor is None:
            raise ValueError(f"caso {cid}: `campos` no admite null en {campo!r}; "
                             "si el dato no debe inventarse, el caso es `valvula`")
        if campo == "tipo_documento" and valor not in TIPOS_DOCUMENTO:
            raise ValueError(f"caso {cid}: `tipo_documento` debe ser una de {TIPOS_DOCUMENTO}, no {valor!r}")
        if campo == "plazo_dias" and (_entero(valor) is None or _entero(valor) < 0):
            raise ValueError(f"caso {cid}: `plazo_dias` debe ser un entero, no {valor!r}")
        if campo in CAMPOS_FRAGMENTO and (not isinstance(valor, str) or not _norm(valor)):
            # Un fragmento vacio estaria contenido en cualquier cosa.
            raise ValueError(f"caso {cid}: {campo!r} espera un fragmento de texto no vacio, no {valor!r}")
    return esperado


def _esperado_valvula(caso: dict) -> list[str]:
    cid = caso.get("id")
    campos = [c.strip() for c in _texto(caso.get("esperado")).split("|") if c.strip()]
    if not campos:
        raise ValueError(f"caso {cid}: `valvula` lista campos separados por |, p. ej. fecha|plazo_dias")
    desconocidos = sorted(set(campos) - set(CAMPOS_VLM))
    if desconocidos:
        # Sin esta revision, un campo mal escrito ("fecah") daria js.get() ->
        # None, contaria como null y regalaria la nota.
        raise ValueError(f"caso {cid}: `valvula` nombra campos que el VLM no extrae: {desconocidos}")
    return campos


def _esperado_juez_vlm(caso: dict) -> None:
    if _texto(caso.get("esperado")).strip():
        raise ValueError(f"caso {caso.get('id')}: `juez_vlm` lleva `esperado` vacio (se ignoraria)")


_ESPERADO = {
    "exacto": _esperado_exacto,
    "campos": _esperado_campos,
    "valvula": _esperado_valvula,
    "juez_vlm": _esperado_juez_vlm,
}


# --------------------------------------------------------------------------
# Las cuatro notas. Todas devuelven float en [0, 1].
# --------------------------------------------------------------------------
def nota_exacto(caso: dict, traza: dict) -> float:
    """El mecanismo FINAL de M3 coincide con el esperado.

    Usa schema.parse_salida: lee la linea `Mecanismo:` del bloque de 5 lineas
    de Amparo, en vez de buscar una subcadena en texto libre (que daria
    falsos positivos con 'tutela' mencionada de pasada). Es la misma
    comparacion de mecanismo que hace metricas.acierto_por_caso en M3, asi la
    comparacion directa de T6 mide lo mismo en los dos lados.
    """
    schema = _schema()
    esperado = _esperado_exacto(caso)
    salida = traza.get("salida") or ""

    if esperado == ESPERADO_ABSTENCION:
        return 1.0 if schema.se_abstuvo(salida) else 0.0

    pred = schema.parse_salida(salida).get("mecanismo")
    return 1.0 if pred == esperado else 0.0


def _acierta_campo(campo: str, esperado, leido) -> bool:
    """Un campo exigido contra lo que leyo el VLM (ver FORMATO_CASOS.md)."""
    if _es_nulo(leido):
        return False  # esperado nunca es null: un null o la valvula es no haberlo leido
    if campo == "plazo_dias":
        return _entero(leido) == _entero(esperado)
    if campo in CAMPOS_FRAGMENTO:
        return _norm(esperado) in _norm(leido)
    return _norm(leido) == _norm(esperado)


def nota_campos(caso: dict, traza: dict) -> float:
    """Fraccion de campos exigidos que el VLM extrajo bien.

    Si ver() no produjo JSON parseable, el caso es fallo (nota 0): regla 2
    del patron input, no se disimula.
    """
    esperado = _esperado_campos(caso)
    js = traza.get("js")
    if not isinstance(js, dict):
        return 0.0
    aciertos = sum(_acierta_campo(c, v, js.get(c)) for c, v in esperado.items())
    return aciertos / len(esperado)


def nota_valvula(caso: dict, traza: dict) -> float:
    """El VLM dejo en null lo que no se ve, en vez de inventarlo.

    `esperado` lista los campos que DEBEN ser null. Un campo con valor
    inventado cuenta 0 para ese campo. JSON no parseable = fallo.
    """
    debe_ser_nulo = _esperado_valvula(caso)
    js = traza.get("js")
    if not isinstance(js, dict):
        return 0.0
    return sum(_es_nulo(js.get(c)) for c in debe_ser_nulo) / len(debe_ser_nulo)


_RE_SI_NO = re.compile(r"^\W*(si|no)\W*$")


def nota_juez_vlm(caso: dict, traza: dict, *, preguntar_fn=None, imagen=None) -> float:
    """Faithfulness visual: se vuelve a mirar la imagen con el mismo VLM.

    preguntar_fn(imagen, texto) -> str  es la `preguntar(imagen, pregunta)` del
    notebook de M4 (celda 7), tal cual: `preguntar_fn=preguntar`, sin envoltorio.
    `imagen` es el OBJETO ya cargado (PIL, RGB), el mismo que se le paso a ver():
    asi el juez mira exactamente lo que miro el extractor, sin riesgo de otra
    carpeta, otro archivo u otra conversion de color. Este modulo solo la
    reenvia: no importa PIL ni sabe donde estan las imagenes, y en los tests
    sirve cualquier cosa (p. ej. "img-falsa") con una preguntar_fn falsa.

    Regla dura (igual que el parseo del juez de M2): si la respuesta no es
    exactamente SI o NO (tolerando puntuacion y tilde), nota 0. Nunca se
    interpreta un "probablemente" a favor del sistema.
    """
    _esperado_juez_vlm(caso)
    if preguntar_fn is None or imagen is None:
        raise ValueError("juez_vlm necesita preguntar_fn e imagen: sin volver a mirar la imagen no hay faithfulness")

    afirmacion = (traza.get("salida") or "")[:1200]
    pregunta = (
        "Esta es la respuesta de un sistema sobre el documento de la imagen:\n"
        f"\"\"\"{afirmacion}\"\"\"\n"
        "¿Lo que la respuesta afirma sobre el documento se sostiene en lo que ves "
        "en la imagen? Responde SOLO con SI o NO."
    )
    # Acordado con Santiago (T2): se llama preguntar(imagen, texto) SIN
    # system=VALVULA (esa instruccion es para extraer, no para juzgar) y con
    # su max_new_tokens por defecto.
    respuesta = preguntar_fn(imagen, pregunta)
    m = _RE_SI_NO.match(_norm(_texto(respuesta)))
    return 1.0 if (m and m.group(1) == "si") else 0.0


CRITERIOS = {
    "exacto": nota_exacto,
    "campos": nota_campos,
    "valvula": nota_valvula,
    "juez_vlm": nota_juez_vlm,
}


def calificar(caso: dict, traza: dict, **kwargs) -> float:
    """Enruta por la columna `criterio` del caso. kwargs solo los usa juez_vlm
    (preguntar_fn, imagen); los demas criterios los ignoran, asi el bucle de
    T6 puede pasarlos siempre."""
    criterio = caso.get("criterio")
    fn = CRITERIOS.get(criterio)
    if fn is None:
        raise ValueError(f"caso {caso.get('id')}: criterio {criterio!r} no existe (validos: {CRITERIOS_VALIDOS})")
    return fn(caso, traza, **kwargs) if criterio == "juez_vlm" else fn(caso, traza)


# --------------------------------------------------------------------------
# Validacion del CSV de Lucas (prueba de T4, verificable por Nico antes de correr)
# --------------------------------------------------------------------------
def cargar_casos(ruta: Path | str) -> list[dict]:
    """casos_m4.csv -> lista de dicts con las celdas como texto (utf-8, con o
    sin BOM: Excel lo agrega al guardar como CSV UTF-8)."""
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def validar_casos(casos: list[dict], carpeta_imagenes: Path | None = None) -> list[str]:
    """Devuelve la lista de problemas del eval set. Lista vacia = listo para correr.

    Un `esperado` mal formado se detecta AQUI, no como nota 0 durante la
    corrida: seria un error de quien escribio el caso, no del sistema, y
    contarlo como fallo del sistema falsearia el scorecard.
    """
    problemas: list[str] = []
    faltan = sorted({c for c in COLUMNAS if any(c not in caso for caso in casos)})
    if faltan:
        problemas.append(f"faltan columnas: {faltan}")
        return problemas
    if len(casos) < MIN_CASOS:
        problemas.append(f"hay {len(casos)} casos; la rubrica pide al menos {MIN_CASOS}")

    adversariales = [c for c in casos if _texto(c["tipo"]).strip() == "adversarial"]
    if len(adversariales) != 1:
        problemas.append(f"debe haber exactamente 1 caso adversarial, hay {len(adversariales)}")
    elif _texto(adversariales[0]["criterio"]).strip() != "valvula":
        problemas.append("el caso adversarial debe tener criterio `valvula`")

    ids = [_texto(c["id"]).strip() for c in casos]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        problemas.append(f"hay ids repetidos: {repetidos}")

    for c in casos:
        cid, crit = _texto(c["id"]).strip(), _texto(c["criterio"]).strip()
        tipo = _texto(c["tipo"]).strip()
        if tipo not in TIPOS_CASO:
            # Cerrado a proposito: un "Adversarial" o "adversarail" haria
            # desaparecer el caso adversarial sin aviso.
            problemas.append(f"{cid}: tipo {tipo!r} no existe (validos: {TIPOS_CASO})")
        if crit not in CRITERIOS_VALIDOS:
            problemas.append(f"{cid}: criterio {crit!r} no existe (validos: {CRITERIOS_VALIDOS})")
        else:
            try:
                _ESPERADO[crit](c)
            except ValueError as e:
                problemas.append(str(e))
        if carpeta_imagenes is not None and not (Path(carpeta_imagenes) / _texto(c["imagen"])).is_file():
            problemas.append(f"{cid}: la imagen {_texto(c['imagen'])!r} no existe en {carpeta_imagenes}")
    return problemas


if __name__ == "__main__":
    # Prueba de aceptacion de T5: casos fabricados a mano, sin GPU ni VLM.
    # Las salidas de M3 se generan con schema.render_salida (formato real).
    schema = _schema()
    ok = schema.render_salida({
        "derecho": "salud", "accionado": "EPS Sura", "mecanismo": "tutela",
        "procede": True, "razon": "no hay otro medio judicial",
        "pretension": "ordenar el medicamento", "fundamento": "",
    })
    abst = schema.render_salida({
        "derecho": schema.DERECHO_ESCAPE, "accionado": "no aplica", "mecanismo": None,
        "procede": False, "razon": "hechos insuficientes", "pretension": "ninguna",
    })
    casos = [
        ({"id": "t1", "criterio": "exacto", "esperado": "tutela"}, {"salida": ok}),
        ({"id": "t2", "criterio": "exacto", "esperado": "habeas_corpus"}, {"salida": ok}),
        ({"id": "t3", "criterio": "exacto", "esperado": "no_determinable"}, {"salida": abst}),
        ({"id": "t4", "criterio": "campos",
          "esperado": '{"tipo_documento": "oficio", "plazo_dias": 15, "entidad": "alcaldia de medellin"}'},
         {"js": {"tipo_documento": "Oficio", "plazo_dias": "15",
                 "entidad": "Alcaldía de Medellín - Secretaría de Salud"}}),
        ({"id": "t5", "criterio": "campos", "esperado": '{"tipo_documento": "oficio"}'}, {"js": None}),
        ({"id": "t6", "criterio": "valvula", "esperado": "fecha|plazo_dias"},
         {"js": {"fecha": None, "plazo_dias": "No se aprecia en la imagen."}}),
        ({"id": "t7", "criterio": "valvula", "esperado": "fecha"}, {"js": {"fecha": "2026-01-15"}}),
    ]
    for caso, traza in casos:
        print(caso["id"], caso["criterio"], "->", round(calificar(caso, traza), 3))
    sim = lambda img, txt: "Sí."
    print("t8 juez_vlm SI ->", calificar({"id": "t8", "criterio": "juez_vlm", "esperado": ""},
                                         {"salida": ok}, preguntar_fn=sim, imagen="img-falsa"))
    sim = lambda img, txt: "Probablemente sí, aunque no estoy seguro."
    print("t9 juez_vlm ambiguo ->", calificar({"id": "t9", "criterio": "juez_vlm", "esperado": ""},
                                              {"salida": ok}, preguntar_fn=sim, imagen="img-falsa"))
