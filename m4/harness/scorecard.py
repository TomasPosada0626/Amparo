"""T6: correr el harness sobre casos_m4.csv, escribir scorecard_m4.csv y la
tabla de delta M3 vs M4.

Vive junto a criterios.py. Las decisiones, con su justificacion, estan en
m4/harness/DECISIONES.md (7 a 18).

DONDE CORRE: el bucle necesita el VLM y M3 cargados (GPU), asi que corre en
Colab con una sola llamada:

    import sys; sys.path.insert(0, "m4/harness")
    from scorecard import correr_t6
    res = correr_t6(cargar, ver, preguntar, responder_m3, sistema_m3="<brazo de T7>")

`cargar`, `ver` y `preguntar` son las del notebook de M4 (celdas 3, 7 y 8),
sin envoltorio, y `responder_m3` es el enchufe de T7 (o el sustituto). En
local solo se desarrolla y se prueba con funciones falsas: ver __main__ y
m4/tests/test_scorecard.py.

COMPOSICION DEL PIPELINE: `correr_harness` repite las 3 lineas de
`sistema_multimodal` (celda 12 del notebook: ver -> relato -> responder_m3)
en vez de llamarla, porque necesita capturar lo que devolvio ver() para
calificar `campos` y `valvula`. Si Santiago cambia `sistema_multimodal`,
cambia tambien `armar_relato` aqui: son la misma logica y no pueden diverger.
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path

try:
    import criterios
except ImportError:  # al importarlo como paquete: from m4.harness import scorecard
    from . import criterios

RAIZ = criterios.RAIZ
RUTA_CASOS = RAIZ / "m4" / "eval_set" / "casos_m4.csv"
CARPETA_IMAGENES = RAIZ / "m4" / "eval_set" / "imagenes"
RUTA_SCORECARD = RAIZ / "m4" / "scorecard_m4.csv"
RUTA_TRAZAS = RAIZ / "m4" / "trazas_m4.json"
RUTA_DELTA = RAIZ / "m4" / "delta_m4.json"
# Artefactos publicados de M3. Hoy estan en origin/main, no en m4
# (DECISIONES.md, 17): por eso son parametros y no se leen a ciegas.
RUTA_M3_SCORECARD = RAIZ / "results" / "m3_scorecard.csv"
RUTA_M3_COSTOS = RAIZ / "results" / "m3_costos.json"

COLUMNAS_SCORECARD = ["id", "criterio", "tipo", "nota", "segundos", "salida"]  # fijas por el plan (T6)


def armar_relato(pregunta: str, js, crudo: str) -> str:
    """Identico a sistema_multimodal del notebook (celda 12)."""
    contexto = json.dumps(js, ensure_ascii=False) if js else crudo
    return pregunta + "\n\nDATOS DEL DOCUMENTO ADJUNTO:\n" + contexto


# --------------------------------------------------------------------------
# Diagnostico por etapa: en que parte de la cadena fallo, no solo cuanto
# --------------------------------------------------------------------------
def diagnosticar(caso: dict, traza: dict, nota: float) -> str:
    """Etiqueta preliminar y determinista, derivada de la traza.

    Es el punto de partida para explicar el peor caso en el README (T8), no
    la explicacion: esa se escribe leyendo la traza. Usa las mismas reglas de
    lectura de `esperado` que las notas (criterios._esperado_*).
    """
    if nota == 1.0:
        return "ok"
    criterio, js, salida = caso["criterio"], traza.get("js"), traza.get("salida") or ""
    sin_json = not isinstance(js, dict)

    if criterio == "exacto":
        schema = criterios._schema()
        if schema.se_abstuvo(salida):
            decision = "abstencion"
        else:
            decision = schema.parse_salida(salida).get("mecanismo") or "sin mecanismo legible"
        esperado = criterios._esperado_exacto(caso)
        if sin_json:
            return f"ver() no produjo JSON; M3 recibio el texto crudo y respondio {decision} (esperado {esperado})"
        # Sin gold del JSON en un caso `exacto`, la traza no distingue si el
        # VLM leyo mal o si el motor de reglas decidio mal: se dice asi.
        return (f"M3 respondio {decision} (esperado {esperado}) con JSON valido de ver(): "
                "revisar en la traza si los hechos leidos eran correctos o si fallo el motor de reglas")

    if criterio == "campos":
        if sin_json:
            return "ver() no produjo JSON"
        esperado = criterios._esperado_campos(caso)
        mal = [f"{c} (esperado {v!r}, leyo {js.get(c)!r})"
               for c, v in esperado.items() if not criterios._acierta_campo(c, v, js.get(c))]
        return "campos: leyo mal " + "; ".join(mal)

    if criterio == "valvula":
        if sin_json:
            return "ver() no produjo JSON"
        inventados = [f"{c}={js.get(c)!r}" for c in criterios._esperado_valvula(caso)
                      if not criterios._es_nulo(js.get(c))]
        return "valvula: invento " + ", ".join(inventados)

    if criterio == "juez_vlm":
        respuesta = traza.get("respuesta_juez")
        if criterios._norm(criterios._texto(respuesta)).strip(" .!¡¿?") == "no":
            return "juez: respondio NO, la salida no se sostiene en la imagen"
        return f"juez: respuesta no valida {respuesta!r} (solo SI/NO cuentan; vale 0)"

    raise ValueError(f"caso {caso.get('id')}: criterio {criterio!r} no existe")


# --------------------------------------------------------------------------
# El bucle
# --------------------------------------------------------------------------
def correr_harness(casos, ver_fn, responder_m3, cargar_fn, *, preguntar_fn=None,
                   carpeta_imagenes: Path = CARPETA_IMAGENES):
    """Corre cada caso, mide latencia y califica. Devuelve (filas, trazas).

    Las funciones son las del notebook de M4, sin envoltorio:
      cargar_fn(ruta)         -> imagen PIL RGB   `cargar` (celda 3)
      ver_fn(imagen)          -> (crudo, js)      `ver` (celda 8): recibe la IMAGEN, no la ruta
      preguntar_fn(img, txt)  -> str              `preguntar` (celda 7); obligatoria si hay `juez_vlm`
      responder_m3(relato)    -> str              el enchufe de T7 (o el sustituto)

    La imagen se carga UNA vez por caso y ese mismo objeto va a ver() y al
    juez_vlm: garantiza que el juez mira lo que miro el extractor.

    `segundos` mide el SISTEMA (ver + M3). Quedan fuera del cronometro la carga
    de la imagen (en el notebook las imagenes ya vienen cargadas antes de
    llamar a sistema_multimodal) y la llamada extra del juez_vlm, que es del
    evaluador y no del sistema.

    Todo lo que puede fallar por el CSV o la configuracion se revisa ANTES del
    primer caso, para no descubrirlo a mitad de una corrida en GPU. Una
    excepcion de ver() o de M3 detiene la corrida: no se disfraza de nota 0.
    """
    problemas = criterios.validar_casos(casos, carpeta_imagenes)
    if problemas:
        raise ValueError("eval set invalido, no se corre nada:\n  - " + "\n  - ".join(problemas))
    if preguntar_fn is None and any(c["criterio"] == "juez_vlm" for c in casos):
        raise ValueError("hay casos `juez_vlm` y falta preguntar_fn (la `preguntar` del notebook): no se corre nada")

    filas, trazas = [], {}
    for caso in casos:
        imagen = cargar_fn(str(Path(carpeta_imagenes) / caso["imagen"]))

        t0 = time.perf_counter()
        crudo, js = ver_fn(imagen)
        salida = responder_m3(armar_relato(caso["pregunta"], js, crudo))
        segundos = time.perf_counter() - t0

        traza = {"crudo": crudo, "js": js, "salida": salida}
        kw = {}
        if caso["criterio"] == "juez_vlm":
            # Se guarda la respuesta cruda del juez: un NO y un "probablemente"
            # valen lo mismo (0) pero no significan lo mismo al explicar el caso.
            def juez(img, texto, _traza=traza):
                _traza["respuesta_juez"] = preguntar_fn(img, texto)
                return _traza["respuesta_juez"]
            kw = {"preguntar_fn": juez, "imagen": imagen}
        nota = criterios.calificar(caso, traza, **kw)
        traza["etapa"] = diagnosticar(caso, traza, nota)

        filas.append({"id": caso["id"], "criterio": caso["criterio"], "tipo": caso["tipo"],
                      "nota": round(nota, 3), "segundos": round(segundos, 3), "salida": salida})
        trazas[caso["id"]] = traza
    return filas, trazas


def guardar(filas, trazas, ruta_scorecard: Path = RUTA_SCORECARD, ruta_trazas: Path = RUTA_TRAZAS) -> None:
    ruta_scorecard = Path(ruta_scorecard)
    ruta_scorecard.parent.mkdir(parents=True, exist_ok=True)
    with ruta_scorecard.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS_SCORECARD, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    # La traza NO va en el scorecard (sus columnas son fijas); va aparte porque
    # es la evidencia del "peor caso explicado": que etapa fallo, no solo cuanto.
    Path(ruta_trazas).write_text(json.dumps(trazas, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8", newline="\n")


def cargar_guardado(ruta_scorecard: Path = RUTA_SCORECARD, ruta_trazas: Path = RUTA_TRAZAS):
    """Lee lo que escribio `guardar` con los tipos de vuelta (el CSV trae texto).
    Sirve para armar la tabla de delta sin volver a correr en GPU."""
    with Path(ruta_scorecard).open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    for fila in filas:
        fila["nota"], fila["segundos"] = float(fila["nota"]), float(fila["segundos"])
    trazas = json.loads(Path(ruta_trazas).read_text(encoding="utf-8"))
    return filas, trazas


# --------------------------------------------------------------------------
# Numeros de M3: del artefacto REAL, nunca del 0.74 del notebook de S13
# --------------------------------------------------------------------------
_SIN_RESULTS = (
    "{ruta} no existe. Los artefactos publicados de M3 (results/) estan en "
    "origin/main, que va por delante de la base de m4: ver m4/harness/DECISIONES.md, 17. "
    "Sin ese archivo la tabla de delta NO tiene numeros reales de M3 (no uses el 0.74).")


def leer_fila_m3(sistema: str | None, ruta: Path = RUTA_M3_SCORECARD) -> dict:
    """Devuelve la fila de m3_scorecard.csv del brazo enchufado.

    El CSV trae UNA FILA POR SISTEMA (M3 compara 4 arquitecturas), asi que NO
    se promedia: la comparacion honesta es contra el brazo que T7 realmente
    enchufo. Si no se dice cual, se listan los disponibles y se para.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(_SIN_RESULTS.format(ruta=ruta))
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f))
    brazos = ", ".join(repr(r["sistema"]) for r in filas)
    if not sistema:
        raise ValueError(f"Falta `sistema_m3`. Brazos en {ruta.name}: {brazos}. Usa el que T7 (Martin/Tomas) enchufo.")
    for r in filas:
        if r["sistema"] == sistema:
            return r
    raise KeyError(f"sistema {sistema!r} no esta en {ruta.name}: {brazos}")


def leer_latencia_m3(sistema: str, ruta: Path = RUTA_M3_COSTOS) -> float | None:
    """Segundos POR CASO del brazo en m3_costos.json.

    `latencia_media` de m3_costos.json es por LLAMADA a la API, no por caso.
    Para los brazos 2 y 3 coincide (una llamada por caso), pero el brazo 4 —el
    que se enchufa en T7— hace varias por caso: en m3/20261022T105449Z son 548
    llamadas en 130 casos, 3.24 s por llamada y 13.6 s por caso. Leer
    `latencia_media` comparaba los segundos por caso de M4 con los segundos por
    llamada de M3, y M4 salia unas cuatro veces mas lento de lo que es frente a
    M3. Por eso, cuando el artefacto trae el total y el numero de casos, se
    divide; si no, se usa `latencia_media` como antes.

    None cuando el brazo no se instrumento (el 1 trae null y la nota "sin
    instrumentar en este modulo"): se reporta como no disponible, nunca como 0.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(_SIN_RESULTS.format(ruta=ruta))
    datos = json.loads(ruta.read_text(encoding="utf-8"))["datos"]
    for d in datos:
        if d.get("etiqueta") == sistema:
            total, casos = d.get("latencia_total_s"), d.get("casos")
            if total is not None and casos:
                return round(total / casos, 3)
            return d.get("latencia_media")
    raise KeyError(f"sistema {sistema!r} no esta en {ruta.name}: "
                   + ", ".join(repr(d.get("etiqueta")) for d in datos))


# --------------------------------------------------------------------------
# Tabla de delta
# --------------------------------------------------------------------------
def _media(xs):
    return round(sum(xs) / len(xs), 3) if xs else None


def construir_tabla_delta(filas, trazas, fila_m3: dict, *, latencia_m3: float | None = None) -> dict:
    """Las 5 filas del plan (T6), cada una con la METRICA nombrada.

    Ojo de honestidad: la nota de M4 mezcla criterios (exacto/campos/valvula/
    juez_vlm) y `acierto_juridico` de M3 es otra cosa. Poner los dos numeros
    en una tabla sin nombrar la metrica sugiere una comparacion que no existe.
    Por eso cada fila declara su metrica, y `comparacion_directa` da la unica
    pareja de numeros que SI es la misma magnitud: acierto de mecanismo.
    """
    con_imagen = [f for f in filas if f["tipo"] != "adversarial"]
    adversarial = [f for f in filas if f["tipo"] == "adversarial"]
    exactos = [f for f in filas if f["criterio"] == "exacto"]

    peor_nota = min(f["nota"] for f in filas)
    peores = [f for f in filas if f["nota"] == peor_nota]
    brazo = fila_m3["sistema"]

    tabla = [
        {"fila": "Casos sin imagen (M3)",
         "metrica": f"acierto_juridico, brazo {brazo!r} (n={fila_m3['n']})",
         "valor": float(fila_m3["acierto_juridico"]), "latencia": latencia_m3},
        {"fila": "Casos con imagen (M4)", "metrica": f"nota media, criterios mixtos (n={len(con_imagen)})",
         "valor": _media([f["nota"] for f in con_imagen]),
         "latencia": _media([f["segundos"] for f in con_imagen])},
        {"fila": "Adversarial (valvula)", "metrica": f"nota_valvula (n={len(adversarial)})",
         "valor": _media([f["nota"] for f in adversarial]),
         "latencia": _media([f["segundos"] for f in adversarial])},
        {"fila": "Latencia media", "metrica": f"ver() + M3 por caso, todos los casos de M4 (n={len(filas)})",
         "valor": None, "latencia": _media([f["segundos"] for f in filas])},
        {"fila": "Peor caso", "metrica": "nota minima (empates: todos)",
         "valor": ", ".join(f"{p['id']} ({p['nota']})" for p in peores), "latencia": None},
    ]
    return {
        "sistema_m3": brazo,
        "tabla": tabla,
        "comparacion_directa": {
            "metrica": "acierto de mecanismo (misma magnitud en ambos)",
            "m4_casos_exacto": _media([f["nota"] for f in exactos]),
            "n_m4": len(exactos),
            "m3_acc_mecanismo": float(fila_m3["acc_mecanismo"]),
            "n_m3": int(fila_m3["n"]),
        },
        "peores": [{"id": p["id"], "criterio": p["criterio"], "nota": p["nota"],
                    "etapa": (trazas.get(p["id"]) or {}).get("etapa"),
                    "traza": trazas.get(p["id"])} for p in peores],
    }


def tabla_markdown(res: dict) -> str:
    """La tabla con la forma de la plantilla del README de entrega (T8)."""
    def celda(v):
        if v is None:
            return "—"
        return v if isinstance(v, str) else f"{v:.3f}"

    lineas = ["| | Métrica | Valor | Latencia (s) |", "|---|---|---:|---:|"]
    for r in res["tabla"]:
        lat = celda(r["latencia"])
        if r["fila"].startswith("Casos sin imagen") and r["latencia"] is None:
            lat = "no disponible"
        lineas.append(f"| {r['fila']} | {r['metrica']} | {celda(r['valor'])} | {lat} |")
    cd = res["comparacion_directa"]
    lineas += ["", (f"**Comparación directa** ({cd['metrica']}): casos `exacto` de M4 = "
                    f"{celda(cd['m4_casos_exacto'])} (n = {cd['n_m4']}) frente a `acc_mecanismo` de M3 = "
                    f"{celda(cd['m3_acc_mecanismo'])} (n = {cd['n_m3']}). Con un n tan chico no se "
                    "afirma significancia.")]
    lineas += ["", "**Peor caso:**"] + [f"- {p['id']} ({p['criterio']}, nota {p['nota']}): {p['etapa']}"
                                        for p in res["peores"]]
    return "\n".join(lineas)


# --------------------------------------------------------------------------
# Punto de entrada para Colab
# --------------------------------------------------------------------------
def correr_t6(cargar_fn, ver_fn, preguntar_fn, responder_m3, *, sistema_m3: str,
              ruta_casos: Path = RUTA_CASOS, carpeta_imagenes: Path = CARPETA_IMAGENES,
              ruta_scorecard: Path = RUTA_SCORECARD, ruta_trazas: Path = RUTA_TRAZAS,
              ruta_delta: Path = RUTA_DELTA, ruta_m3_scorecard: Path = RUTA_M3_SCORECARD,
              ruta_m3_costos: Path = RUTA_M3_COSTOS) -> dict:
    """Todo T6 en una llamada: validar -> correr -> guardar -> tabla de delta.

    El scorecard y las trazas se guardan ANTES de leer M3: si falta results/,
    el trabajo en GPU no se pierde y la tabla se arma despues, sin GPU, con
    `tabla_desde_disco(sistema_m3)`.
    """
    if not sistema_m3:
        raise ValueError("Falta `sistema_m3`: el brazo de M3 que T7 enchufo, tal como aparece en m3_scorecard.csv.")
    casos = criterios.cargar_casos(ruta_casos)
    filas, trazas = correr_harness(casos, ver_fn, responder_m3, cargar_fn,
                                   preguntar_fn=preguntar_fn, carpeta_imagenes=carpeta_imagenes)
    guardar(filas, trazas, ruta_scorecard, ruta_trazas)
    print(f"{ruta_scorecard} · {len(filas)} filas · trazas en {ruta_trazas}")
    return _tabla_y_guardar(filas, trazas, sistema_m3, ruta_delta, ruta_m3_scorecard, ruta_m3_costos)


def tabla_desde_disco(sistema_m3: str, *, ruta_scorecard: Path = RUTA_SCORECARD,
                      ruta_trazas: Path = RUTA_TRAZAS, ruta_delta: Path = RUTA_DELTA,
                      ruta_m3_scorecard: Path = RUTA_M3_SCORECARD,
                      ruta_m3_costos: Path = RUTA_M3_COSTOS) -> dict:
    """La tabla de delta a partir de lo que ya guardo `correr_t6`. Sin GPU:
    para cuando results/ (o el brazo de T7) llega despues de la corrida."""
    if not sistema_m3:
        raise ValueError("Falta `sistema_m3`: el brazo de M3 que T7 enchufo, tal como aparece en m3_scorecard.csv.")
    filas, trazas = cargar_guardado(ruta_scorecard, ruta_trazas)
    return _tabla_y_guardar(filas, trazas, sistema_m3, ruta_delta, ruta_m3_scorecard, ruta_m3_costos)


def _tabla_y_guardar(filas, trazas, sistema_m3, ruta_delta, ruta_m3_scorecard, ruta_m3_costos) -> dict:
    fila_m3 = leer_fila_m3(sistema_m3, ruta_m3_scorecard)
    res = construir_tabla_delta(filas, trazas, fila_m3,
                                latencia_m3=leer_latencia_m3(sistema_m3, ruta_m3_costos))
    Path(ruta_delta).write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8", newline="\n")
    print(tabla_markdown(res))
    return res


if __name__ == "__main__":
    # Ensayo local, sin GPU, sobre casos_m4.ejemplo.csv. Todo lo que no es el
    # harness es FALSO: imagenes vacias, un ver() que devuelve JSON fijo por
    # caso, un M3 que responde con el formato real de schema.render_salida y un
    # m3_scorecard.csv con las columnas reales pero numeros inventados.
    import tempfile

    schema = criterios._schema()
    tmp = Path(tempfile.mkdtemp(prefix="ensayo_t6_"))
    casos_ej = RAIZ / "m4" / "eval_set" / "casos_m4.ejemplo.csv"
    (tmp / "imagenes").mkdir()
    for c in criterios.cargar_casos(casos_ej):
        (tmp / "imagenes" / c["imagen"]).write_bytes(b"")

    lecturas = {  # lo que "lee" el VLM falso, por imagen
        "ej02_oficio_alcaldia.png": {"tipo_documento": "oficio", "plazo_dias": 10,
                                     "entidad": "Alcaldía de Medellín"},
        "ej03_documento_incompleto.png": None,  # JSON roto
        "ej04_respuesta_peticion.png": {"tipo_documento": "respuesta_peticion",
                                        "fecha": "Bogotá, 3 de marzo de 2026"},
        "ej06_notificacion_borrosa.png": {"tipo_documento": "notificacion", "fecha": None,
                                          "plazo_dias": "No se aprecia en la imagen."},
    }
    cargar = lambda ruta: ("img-falsa", Path(ruta).name)  # objeto opaco: el harness solo lo reenvia
    ver = lambda img: (("texto suelto, sin JSON", None) if lecturas.get(img[1], {}) is None
                       else ('{"..."}', lecturas.get(img[1], {"tipo_documento": "otro"})))
    tutela = schema.render_salida({"derecho": "salud", "accionado": "EPS", "mecanismo": "tutela",
                                   "procede": True, "razon": "sin otro medio", "pretension": "x"})
    preguntar = lambda img, texto: "Probablemente sí"

    m3_csv = tmp / "m3_scorecard.csv"
    m3_csv.write_text("sistema,n,acc_mecanismo,acierto_juridico\n"
                      "ENSAYO · brazo falso,80,0.500,0.500\n", encoding="utf-8")
    m3_costos = tmp / "m3_costos.json"
    m3_costos.write_text(json.dumps({"datos": [{"etiqueta": "ENSAYO · brazo falso", "latencia_media": 1.0}]}),
                         encoding="utf-8")

    res = correr_t6(cargar, ver, preguntar, lambda relato: tutela, sistema_m3="ENSAYO · brazo falso",
                    ruta_casos=casos_ej, carpeta_imagenes=tmp / "imagenes",
                    ruta_scorecard=tmp / "scorecard_m4.csv", ruta_trazas=tmp / "trazas_m4.json",
                    ruta_delta=tmp / "delta_m4.json", ruta_m3_scorecard=m3_csv, ruta_m3_costos=m3_costos)
    print("\n(ENSAYO: los numeros de M3 de arriba son inventados; en Colab salen de results/)")


# --------------------------------------------------------------------------
# El delta del COMPONENTE: la misma pregunta con imagen y sin ella
# --------------------------------------------------------------------------
RUTA_DELTA_IMAGEN = RAIZ / "m4" / "delta_imagen_m4.json"


def delta_con_sin_imagen(responder_m3, *, ruta_casos: Path = RUTA_CASOS,
                         ruta_trazas: Path = RUTA_TRAZAS,
                         ruta_salida: Path = RUTA_DELTA_IMAGEN) -> dict:
    """Para cada caso `exacto`: la nota CON la imagen y la nota SIN ella.

    POR QUE ESTA COMPARACION Y NO SOLO LA TABLA DE DELTA

    La tabla de `construir_tabla_delta` pone los casos `exacto` de M4 junto a
    `acc_mecanismo` de M3. Son casos distintos —3 de M4 contra 120 de M3—, asi
    que la diferencia mezcla el componente con la dificultad de cada conjunto y
    no dice si la imagen ayudo. La pregunta de la rubrica ("mide el delta ...
    incluido el caso en que el componente no aporto") se responde quitando la
    imagen y dejando todo lo demas igual: misma pregunta, mismo M3.

    No gasta GPU. La condicion CON imagen sale de la corrida guardada: su
    `salida` y la lectura de `ver()` estan en las trazas. La condicion SIN
    imagen es `responder_m3(pregunta)`, que es lo que haria M3 sin ojos.

    Lo que NO es: una prueba de significancia. Con 3 casos `exacto` es una
    lectura caso por caso, y se publica asi.
    """
    casos = [c for c in criterios.cargar_casos(ruta_casos) if c.get("criterio") == "exacto"]
    trazas = json.loads(Path(ruta_trazas).read_text(encoding="utf-8"))
    filas = []
    for c in casos:
        t = trazas[c["id"]]
        con = criterios.nota_exacto(c, t)
        sin_salida = responder_m3(c["pregunta"])
        sin = criterios.nota_exacto(c, {"salida": sin_salida, "js": None})
        efecto = ("aporta" if con > sin else "empeora" if con < sin
                  else "no aporta (acierta igual)" if con else "no aporta (falla igual)")
        filas.append({"id": c["id"], "esperado": c["esperado"],
                      "nota_con_imagen": con, "nota_sin_imagen": sin, "efecto": efecto,
                      "salida_sin_imagen": sin_salida})
    n = len(filas)
    res = {"_que_es": ("la misma pregunta con la imagen y sin ella, sobre el mismo M3: "
                       "lo unico que cambia es el componente visual"),
           "n": n,
           "acierto_con_imagen": round(sum(f["nota_con_imagen"] for f in filas) / n, 4) if n else None,
           "acierto_sin_imagen": round(sum(f["nota_sin_imagen"] for f in filas) / n, 4) if n else None,
           "casos": filas}
    Path(ruta_salida).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res
