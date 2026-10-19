"""Genera REPORTE.md leyendo los artefactos. No escribe ninguna cifra a mano.

ROADMAP3 · T-5. Habia 31 artefactos y ningun documento que los leyera, y sin
el, el proyecto es un conjunto de mediciones sin tesis.

POR QUE SE GENERA Y NO SE ESCRIBE

El criterio de cierre G-4 pide que cada afirmacion del reporte apunte a un
artefacto publicado, con su `n` y su intervalo. Un documento escrito a mano lo
cumple el dia que se escribe y deja de cumplirlo en la siguiente corrida, en
silencio. Ya paso en este proyecto: `verificar_entrega.py` existe porque en
`runs/` habia nueve artefactos de una corrida vieja, y uno de ellos daba
`acc_mecanismo` 58.7% donde el vigente daba 82.6%.

Asi que el reporte no se escribe: se genera. Toda cifra pasa por `d()`, que
registra de que archivo y de que ruta de claves salio, y el apendice imprime
esa lista. Una cifra que no este en un artefacto no se puede poner en el
reporte --- el script falla antes de escribirlo --- y una afirmacion que
dependa de un artefacto ausente se reporta como ausente en vez de desaparecer.

LA PROSA SI ES MIA

Lo que no se puede generar es la tesis, la lectura de cada numero y las
limitaciones. Eso va escrito, y va en el codigo para que viaje con las cifras
que interpreta. Donde un texto depende de un numero, lo interpola: si el
numero cambia de signo en la proxima corrida, la frase cambia con el.

    python -I data/reporte.py            # exige los tres modulos
    python -I data/reporte.py --parcial  # escribe con lo que haya
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RESULTS = RAIZ / "results"
SALIDA = RAIZ / "REPORTE.md"
BOGOTA = timezone(timedelta(hours=-5), "America/Bogota")

# --------------------------------------------------------------------------
# Lectura con procedencia
# --------------------------------------------------------------------------
_CITAS: list[tuple[str, str, str]] = []
_FALTAN: set[str] = set()
_CACHE: dict[str, object] = {}


class Ausente:
    """Un artefacto que no esta. No es None: None es un valor medido.

    La diferencia importa. `acierto_abstencion: None` significa "no habia
    casos que medir" y es una medicion. Un artefacto ausente significa "esta
    corrida no produjo esto", y el reporte tiene que decirlo donde iria la
    cifra en vez de escribir un cero o callarse.
    """

    def __init__(self, motivo: str):
        self.motivo = motivo

    def __repr__(self) -> str:
        return f"<sin medir: {self.motivo}>"


def _cargar(archivo: str):
    if archivo in _CACHE:
        return _CACHE[archivo]
    p = RESULTS / archivo
    if not p.exists():
        _FALTAN.add(archivo)
        _CACHE[archivo] = Ausente(f"{archivo} no esta en results/")
        return _CACHE[archivo]
    if p.suffix == ".csv":
        with p.open(encoding="utf-8", newline="") as f:
            v = list(csv.DictReader(f))
    else:
        v = json.loads(p.read_text(encoding="utf-8"))
    _CACHE[archivo] = v
    return v


def d(archivo: str, *claves, dec: int = 3):
    """Un dato del artefacto, registrado. `claves` es la ruta dentro del JSON."""
    v = _cargar(archivo)
    if isinstance(v, Ausente):
        return v
    ruta = []
    for k in claves:
        ruta.append(str(k))
        try:
            v = v[k]
        except (KeyError, IndexError, TypeError):
            _FALTAN.add(f"{archivo}:{'.'.join(ruta)}")
            return Ausente(f"{archivo} no trae {'.'.join(ruta)}")
    _CITAS.append((archivo, ".".join(str(k) for k in claves), repr(v)[:60]))
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return round(v, dec)
    return v


def ic(archivo: str, *claves) -> str:
    """Un intervalo escrito como el reporte lo necesita: punto [bajo, alto]."""
    v = _cargar(archivo)
    if isinstance(v, Ausente):
        return str(v)
    for k in claves:
        try:
            v = v[k]
        except (KeyError, IndexError, TypeError):
            _FALTAN.add(f"{archivo}:{'.'.join(str(x) for x in claves)}")
            return f"<sin medir: {archivo} no trae el intervalo>"
    if not isinstance(v, dict) or "ic_bajo" not in v:
        _FALTAN.add(f"{archivo}:{'.'.join(str(x) for x in claves)} sin ic_bajo")
        return "<sin intervalo>"
    _CITAS.append((archivo, ".".join(str(k) for k in claves),
                   f"{v['punto']} [{v['ic_bajo']}, {v['ic_alto']}]"))
    met = v.get("metodo", "")
    marca = " (Wilson)" if met == "wilson" else ""
    return (f"**{v['punto']:.1%}** [{v['ic_bajo']:.1%}, {v['ic_alto']:.1%}]"
            f"{marca}, n={v.get('n', '?')}")




# --------------------------------------------------------------------------
# Procedencia: de que corrida sale cada cosa
# --------------------------------------------------------------------------
def _corrida_de(archivo: str):
    """El id de corrida que `publicar()` sella dentro del artefacto."""
    v = _cargar(archivo)
    if isinstance(v, Ausente):
        return None
    if isinstance(v, dict):
        return v.get("_corrida")
    # Un CSV no lleva sello dentro: `publicar()` deja el hermano .corrida.txt.
    h = RESULTS / (Path(archivo).stem + ".corrida.txt")
    return h.read_text(encoding="utf-8").strip().split("/")[-1] if h.exists() else None


def _meta_corrida(modulo: str, cid: str) -> dict:
    p = RAIZ / "runs" / modulo / cid / "corrida.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:                                   # noqa: BLE001
        return {}


ANCLAS = {"m1": "m1_scorecard_finetuned.json",
          "m2": "m2_sesgos.json",
          "m3": "m3_ganadores.json"}


def procedencia() -> dict:
    """Las tres corridas, su huella de codigo y si son el mismo experimento.

    Esto va PRIMERO en el reporte y no al final. Comparar M1 sobre un `src/`
    y M3 sobre otro no es un delta del sistema: es un cambio de vara. Si las
    huellas no coinciden, el reporte lo dice en su primera seccion en vez de
    presentar una tabla que no se sostiene.
    """
    out = {}
    for mod, anc in ANCLAS.items():
        cid = _corrida_de(anc)
        m = _meta_corrida(mod, cid) if cid else {}
        out[mod] = {
            "corrida": cid,
            # `corrida.json` la guarda en `codigo._conjunto`. Antes se
            # buscaba en `huella.codigo` y `huella_codigo`, que no existen, y
            # la seccion 1 salia "SIN COMPROBAR" con los tres corrida.json
            # delante: el reporte no mentia --- decia que no se leyo --- pero
            # no comprobaba lo unico que esa seccion existe para comprobar.
            "huella_codigo": (m.get("codigo") or {}).get("_conjunto"),
            "version_datos": (m.get("huella") or {}).get("datos")
            or m.get("datos"),
            "valida": m.get("valida"),
            "inicio_bogota": m.get("inicio_bogota"),
            "artefactos": len(m.get("artefactos") or {}) or None,
        }
    huellas = {v["huella_codigo"] for v in out.values() if v["huella_codigo"]}
    # NO LEIDO Y DISTINTO NO SON LO MISMO, y el reporte no puede confundirlos.
    #
    # La huella vive en `runs/<modulo>/<id>/corrida.json`, no en el artefacto
    # publicado. Si `runs/` no viajo --- porque solo se sincronizo `results/`,
    # que es el caso normal --- el conjunto sale vacio. Decir entonces "no
    # comparten huella" seria afirmar un hallazgo a partir de un archivo que
    # no se leyo. `None` significa "no se pudo comprobar", y el reporte lo
    # escribe como tal.
    out["_mismo_experimento"] = None if not huellas else len(huellas) == 1
    out["_huellas_distintas"] = sorted(x for x in huellas if x)
    out["_huellas_leidas"] = len(huellas)
    return out


# --------------------------------------------------------------------------
# El reporte
# --------------------------------------------------------------------------
NL = chr(10)


def _celda(x) -> str:
    """Una celda de Markdown no sobrevive a un salto de linea ni a una barra.

    Varios campos que van a estas tablas son prosa de los artefactos
    (`lectura`, `lectura_estilo`, `preferencia_posicion_A_lectura`). Si alguno
    trae un salto de linea, la tabla se parte por la mitad y el reporte sale
    roto sin que nada falle. Mas valioso aun: si trae una `|`, las columnas se
    desplazan y las cifras quedan bajo la cabecera equivocada --- un error
    silencioso que cambia lo que el documento dice.
    """
    t = " ".join(str(x).split())
    return t.replace("|", "\\|")


def _tabla(cabeceras: list[str], filas: list[list]) -> list[str]:
    out = ["| " + " | ".join(_celda(c) for c in cabeceras) + " |",
           "|" + "|".join("---" for _ in cabeceras) + "|"]
    for f in filas:
        out.append("| " + " | ".join(_celda(x) for x in f) + " |")
    return out


def _pct(x) -> str:
    """Un porcentaje, y `—` donde no hubo medicion.

    `0.0%` y «no se midio» no son lo mismo, y es el error que este proyecto
    corrige en todas partes: un cero tranquilizador donde falta el dato.
    """
    return f"{x:.1%}" if isinstance(x, (int, float)) and not isinstance(x, bool)         else "—"


def _brazos_comunes() -> list[dict]:
    v = _cargar("m3_scorecards_comunes.json")
    if isinstance(v, Ausente):
        return []
    # `publicar()` envuelve una lista en {"datos": [...]}.
    return v.get("datos", []) if isinstance(v, dict) else v


def separacion() -> dict:
    """La tesis no se escribe: se lee de los intervalos.

    «Gana con intervalos que no se solapan» es la afirmacion central de este
    trabajo, y es la ULTIMA que deberia estar escrita a mano. Si la proxima
    corrida mueve un intervalo y los brazos dejan de separarse, una frase
    escrita sigue diciendo que separan. Asi que se compara aqui, con el mismo
    `metricas.ic_se_solapan()` que usa el notebook, y la frase cambia con el
    dato.

    `ic_se_solapan` no es una prueba de hipotesis --- para eso haria falta el
    bootstrap de la DIFERENCIA, no comparar dos intervalos marginales --- pero
    es la lectura conservadora, y para no sobreinterpretar una tabla es la que
    hace falta.
    """
    brazos = _brazos_comunes()
    if len(brazos) < 2:
        return {"frase": "no se pudo comparar con las demas arquitecturas: "
                         "`m3_scorecards_comunes.json` no esta en `results/`.",
                "concluyente": False}
    try:
        sys.path.insert(0, str(RAIZ / "src"))
        from metricas import ic_se_solapan
    except ImportError:
        return {"frase": "se comparo con las demas arquitecturas; la "
                         "separacion de intervalos no se pudo evaluar aqui.",
                "concluyente": False}

    mejor = max(brazos, key=lambda s_: s_["acierto_juridico"])
    otros = [b for b in brazos if b is not mejor]
    solapan = [b["sistema"] for b in otros
               if ic_se_solapan(mejor["ic"]["acierto_juridico"],
                                b["ic"]["acierto_juridico"])]
    _CITAS.append(("m3_scorecards_comunes.json", "ic.acierto_juridico",
                   f"mejor={mejor['sistema']}, solapan={len(solapan)}"))
    if not solapan:
        frase = (f"el brazo **{mejor['sistema']}** gana a las otras "
                 f"{len(otros)} arquitecturas que se le comparan, con "
                 "intervalos que **no se solapan** con ninguna.")
    elif len(solapan) == len(otros):
        frase = (f"el brazo **{mejor['sistema']}** queda primero en el "
                 f"agregado, pero su intervalo **se solapa con los "
                 f"{len(otros)}** restantes: la tabla no sostiene que sea "
                 "mejor que ninguno de ellos, y la tesis de arriba queda sin "
                 "respaldo en estas corridas.")
    else:
        frase = (f"el brazo **{mejor['sistema']}** gana a las otras "
                 f"{len(otros)} arquitecturas, con intervalos que no se "
                 f"solapan contra {len(otros) - len(solapan)} de ellas y que "
                 f"**si se solapan con {', '.join(solapan)}** --- ahi la "
                 "diferencia no se sostiene.")
    return {"frase": frase, "mejor": mejor["sistema"],
            "solapan_con": solapan, "concluyente": not solapan}


# ---------------------------------------------------------------------------
# Las tres secciones de abajo estaban ESCRITAS A MANO y las tres habian
# caducado en la misma corrida. Es el defecto que este reporte existe para no
# cometer, cometido dentro del reporte: una frase afirmada no se entera de que
# el dato que la sostenia se movio. Ahora salen del artefacto, como
# `separacion()`, y cambian solas o dicen que no pueden concluir.
# ---------------------------------------------------------------------------
def jueces_de_familia() -> list[str]:
    """7.2 · el artefacto dice si los dos jueces son parientes.

    Decia «los dos jueces son de la misma familia». La corrida
    20261019T034128Z emparejo `gpt-oss` con `allam`, que no lo son, y el
    propio `_familias.misma_familia` valia `false` en `results/`. Una seccion
    que contradice un artefacto guardado al lado es peor que no tenerla:
    parece verificada.
    """
    # TRES estados, no dos. Confundir el segundo con el primero fue el bug de
    # la primera version de esta funcion: la corrida 20261018T... trae
    # `_familias: null` y kappa 0.6835, o sea que el acuerdo SI se midio y lo
    # que falta es el linaje. Decir "no se midio" ahi es tan falso como la
    # frase escrita a mano que esto vino a reemplazar.
    if isinstance(_cargar("m2_acuerdo_entre_jueces.json"), Ausente):
        return ["### 7.2 · El acuerdo entre jueces no se midio", "",
                "Sin segundo juez la nota se reporta sin medida de su propia "
                "fiabilidad. Eso **no** es un acuerdo bajo: es una medicion "
                "que no se hizo, y son cosas distintas."]
    fam = d("m2_acuerdo_entre_jueces.json", "_familias")
    kap = d("m2_acuerdo_entre_jueces.json", "kappa_aprueba")
    m_a = d("m2_acuerdo_entre_jueces.json", "media_a")
    m_b = d("m2_acuerdo_entre_jueces.json", "media_b")
    if not isinstance(fam, dict) or not fam.get("conocido"):
        return ["### 7.2 · El acuerdo se midio, pero no con que linajes", "",
                f"Hay cifra —kappa **{kap}**, entre "
                f"`{d('m2_acuerdo_entre_jueces.json', 'modelo_a')}` y "
                f"`{d('m2_acuerdo_entre_jueces.json', 'modelo_b')}`— y el "
                "artefacto **no** registra la familia de cada juez. Sin ese "
                "dato la cifra no se puede interpretar: un acuerdo entre dos "
                "modelos del mismo linaje mide *ruido*, y entre linajes "
                "distintos mide ruido **y** sesgo compartido. Son lecturas "
                "opuestas y el artefacto no permite elegir, asi que aqui no "
                "se elige."]
    f_a, f_b = fam.get("familia_a", "?"), fam.get("familia_b", "?")
    if fam.get("misma_familia"):
        return [f"### 7.2 · Los dos jueces son de la misma familia (`{f_a}`)",
                "",
                "El acuerdo controla el *ruido* de un juez, no el *sesgo* que "
                "dos modelos del mismo linaje comparten: un acuerdo alto "
                f"—kappa **{kap}**— es compatible con que los dos se "
                "equivoquen igual. Por que no se uso otra familia: "
                f"{fam.get('por_que_no_otra_familia') or '(no lo dice)'}."]
    return [f"### 7.2 · Los jueces son de familias distintas (`{f_a}` y "
            f"`{f_b}`), y coinciden poco", "",
            "El emparejamiento es el bueno: al ser de linajes distintos, "
            "coincidir no se explicaria por sesgo compartido. El resultado es "
            f"incomodo —kappa **{kap}**, con medias de **{m_a}** y **{m_b}** "
            "sobre 5—: ordenan parecido y **calibran distinto**. Para "
            "comparar sistemas entre si la nota sirve; para publicarse como "
            "nota absoluta, no. Un acuerdo medido entre familias distintas es "
            "la version conservadora de esta cifra: no hay parentesco que la "
            "infle."]


def cumplimiento_en_el_agente() -> list[str]:
    """7.3 · sale del F1 por clase, porque la version escrita caduco.

    Decia «falla esa via por completo mientras los otros tres la aciertan».
    Era cierto con F1 0.000. Corregir `derecho_colectivo` y `acto_general` en
    `src/sistema.py` movio la cifra; la frase no se movio con ella.
    """
    clase, titulo = "accion_cumplimiento", "### 7.3 · `accion_cumplimiento` "
    titulo += "en el brazo del agente"
    base = ("El art. 9 de la Ley 393 de 1997 hace la accion de cumplimiento "
            "**subsidiaria**, asi que el motor exige "
            "`incumplimiento_normativo=True` **y** "
            "`afectacion_individual=False`.")
    f1, soporte = {}, None
    for b in _brazos_comunes():
        mec = ((b.get("campos") or {}).get("mecanismo") or {})
        if clase in (mec.get("f1_por_clase") or {}):
            f1[str(b.get("sistema", "?"))] = mec["f1_por_clase"][clase]
            soporte = (mec.get("soporte_por_clase") or {}).get(clase, soporte)
    agente = next((k for k in f1 if k.lstrip().startswith("4")), None)
    if agente is None:
        return [titulo, "",
                "El F1 por clase del brazo del agente no esta en "
                "`m3_scorecards_comunes.json`, asi que esta seccion no se "
                "puede sostener con un dato y no se afirma."]
    v = f1[agente]
    otros = [x for k, x in f1.items() if k != agente]
    _CITAS.append(("m3_scorecards_comunes.json",
                   f"campos.mecanismo.f1_por_clase.{clase}",
                   f"agente={v} otros={sorted(otros)}"))
    if v == 0:
        cuerpo = (f"El brazo del agente **falla esa via por completo** (F1 "
                  f"**{v}**) mientras los otros la aciertan. {base} El "
                  "extractor del agente no produce esa combinacion.")
    elif otros and v <= min(otros):
        cuerpo = (f"El brazo del agente da F1 **{v}** en esa clase. Ya **no "
                  "falla por completo** —valia 0.000 antes de corregir "
                  "`derecho_colectivo` y `acto_general`— pero sigue siendo "
                  f"**el peor de los {len(f1)} brazos** ahi. {base} El "
                  "extractor produce esa combinacion solo en parte de los "
                  "casos, asi que el defecto esta **reducido, no cerrado**.")
    else:
        cuerpo = (f"El brazo del agente da F1 **{v}** en esa clase y ya no es "
                  f"el peor de los {len(f1)} brazos. {base}")
    orden = ", ".join(f"`{k}` **{x}**" for k, x in sorted(f1.items()))
    return [titulo, "", cuerpo, "",
            f"F1 por brazo en esa clase ({soporte or '?'} casos de soporte): "
            f"{orden}."]


def adversarial_separa() -> list[str]:
    """7.4 · compara el estrato adversarial con lo que el artefacto trae.

    Decia «los intervalos se solapan». `por_tipo.adversarial` trae `n` y un
    punto, **sin IC**: afirmar un solapamiento entre intervalos que no se
    publican es una cifra inventada con forma de cautela.
    """
    adv = {}
    for b in _brazos_comunes():
        t = (b.get("por_tipo") or {}).get("adversarial") or {}
        if "acierto_juridico" in t:
            adv[str(b.get("sistema", "?"))] = (t["acierto_juridico"],
                                               t.get("n"))
    if len(adv) < 2:
        return ["### 7.4 · El estrato adversarial", "",
                "`por_tipo.adversarial` no esta en la tabla comparable, asi "
                "que este estrato no se compara aqui."]
    n = next((x[1] for x in adv.values() if x[1]), None)
    top = max(x[0] for x in adv.values())
    primeros = sorted(k for k, x in adv.items() if x[0] == top)
    paso = f"{1 / n:.1%}" if n else "—"
    _CITAS.append(("m3_scorecards_comunes.json", "por_tipo.adversarial",
                   f"top={top} primeros={primeros} n={n}"))
    sin_ic = ("`por_tipo.adversarial` publica `n` y un punto, **sin IC**, asi "
              f"que esta comparacion no viene con ancho: con n={n} un solo "
              f"caso vale {paso}.")
    if len(primeros) > 1:
        titulo = ("### 7.4 · En el estrato adversarial **empatan** los brazos "
                  + " y ".join(k.split(" ")[0] for k in primeros))
        cuerpo = (f"Aciertan lo mismo, {_pct(top)} de n={n}, asi que el "
                  "estrato no los ordena —y no los ordena por **empate**, no "
                  f"por un solapamiento de intervalos. {sin_ic}")
    else:
        titulo = (f"### 7.4 · En el estrato adversarial gana el brazo "
                  f"{primeros[0].split(' ')[0]}")
        cuerpo = (f"Queda primero con {_pct(top)} de n={n}. {sin_ic}")
    orden = ", ".join(f"`{k}` {_pct(x[0])}" for k, x in
                      sorted(adv.items(), key=lambda p: -p[1][0]))
    return [titulo, "", cuerpo, "", f"Orden en el estrato: {orden}.", "",
            "Ampliar el estrato invalida la comparabilidad con estas "
            "corridas, asi que es trabajo del siguiente ciclo y no un ajuste."]


def construir() -> list[str]:
    L: list[str] = []
    a = L.append
    hoy = datetime.now(BOGOTA).strftime("%Y-%m-%d %H:%M")
    pr = procedencia()

    # ---- cabecera -------------------------------------------------------
    a("# Triaje de acciones constitucionales colombianas")
    a("")
    a("**Fine-tuning, evaluacion y RAG sobre el mecanismo procedente ante un "
      "relato ciudadano.**")
    a("")
    a(f"> Generado por `data/reporte.py` el {hoy} (America/Bogota). Ninguna "
      "cifra de este documento esta escrita a mano: todas salen de un "
      "artefacto de `results/`, y el apendice dice de cual y de que clave. "
      "Una cifra sin artefacto hace fallar al generador.")
    a("")

    # ---- 0 · tesis ------------------------------------------------------
    a("## 0 · Que afirma este trabajo, y que no")
    a("")
    sep = separacion()
    a("**La tesis.** El cuello de botella para decidir *que mecanismo "
      "constitucional procede* no es el acceso al texto de la norma: es saber "
      "en que orden se preguntan las causales. Un modelo pequeno afinado "
      "sobre el arbol de decision del art. 6 del Decreto 2591 de 1991 llega "
      "mas lejos que tres arquitecturas de recuperacion con acceso al corpus "
      "entero.")
    a("")
    a(f"Medido: {sep['frase']}")
    a("")
    a("**Lo que NO afirma.** Que el sistema sea apto para uso juridico real; "
      "que el juez automatico este validado contra criterio humano "
      "independiente; que los numeros se sostengan en los estratos de n "
      "pequeno. Cada una de esas tiene su cifra y su motivo en la seccion 7, "
      "que es la seccion importante de este documento.")
    a("")

    # ---- 1 · procedencia ------------------------------------------------
    a("## 1 · De donde salen las cifras")
    a("")
    if pr["_mismo_experimento"] is None:
        a("> **SIN COMPROBAR.** La huella de codigo vive en "
          "`runs/<modulo>/<id>/corrida.json` y esa carpeta no esta aqui, asi "
          "que no se pudo verificar que los tres modulos corrieran con el "
          "mismo `src/`. No es lo mismo que decir que difieren: es que no se "
          "leyo. `data/verificar_entrega.py` lo comprueba donde si estan.")
    elif pr["_mismo_experimento"]:
        a("Las tres corridas comparten huella de codigo, asi que la "
          "comparacion entre modulos se sostiene.")
    else:
        a("> **ADVERTENCIA.** Las tres corridas **no** comparten huella de "
          f"codigo: {pr['_huellas_distintas']}. Comparar M1 sobre un `src/` y "
          "M3 sobre otro no es un delta del sistema, es un cambio de vara. "
          "Las tablas de abajo no se pueden leer como comparacion hasta "
          "re-correr los tres (ROADMAP3 · T-1).")
    a("")
    L += _tabla(["modulo", "corrida", "huella de codigo", "valida",
                 "artefactos"],
                [[m, pr[m]["corrida"] or "—",
                  f"`{pr[m]['huella_codigo']}`" if pr[m]["huella_codigo"]
                  else "—",
                  pr[m]["valida"] if pr[m]["valida"] is not None else "—",
                  pr[m]["artefactos"] or "—"] for m in ("m1", "m2", "m3")])
    a("")
    a("`data/verificar_entrega.py` comprueba esto mismo de forma ejecutable: "
      "que los artefactos esten, que sean de la misma corrida de su modulo, "
      "que las huellas de codigo coincidan y que la version de datos sea la "
      "misma en los tres.")
    a("")

    # ---- 2 · datos ------------------------------------------------------
    a("## 2 · Los datos y como se verificaron")
    a("")
    a("Tres niveles de verificacion, y la diferencia entre ellos es lo que "
      "permite leer el resto:")
    a("")
    a("- **`plano`** · la etiqueta se lee directamente del relato.")
    a("- **`derivado`** · hay que encadenar dos hechos del relato.")
    a("- **`juicio`** · hubo que ponderar. Es donde el gold es discutible, y "
      "va marcado para poder leer el resultado por separado.")
    a("")
    a("El motor de reglas del art. 6 reproduce la etiqueta de los casos del "
      "eval set, pero eso significa **consistente** con el arbol, no "
      "**independiente** de el: el campo `por_fiabilidad_etiqueta` de cada "
      "scorecard lo dice con esas palabras para que nadie lea la consistencia "
      "como validacion.")
    a("")
    cob = RAIZ / "data" / "cobertura_corpus.json"
    if cob.exists():
        c = json.loads(cob.read_text(encoding="utf-8"))
        # UN ARTEFACTO DERIVADO SE COMPRUEBA ANTES DE CITARLO.
        #
        # `cobertura_corpus.json` lo produce `data/auditar_cobertura.py` a
        # partir del corpus y los dos eval sets. Si alguno cambio despues, el
        # archivo sigue en su sitio diciendo lo de antes --- y seria un numero
        # viejo con aspecto de vigente. Se comprueban las huellas que el
        # propio artefacto declara.
        import hashlib
        caducadas = [f for f, h in (c.get("_fuentes") or {}).items()
                     if hashlib.sha256((RAIZ / "data" / f).read_bytes())
                     .hexdigest()[:16] != h]
        if caducadas:
            a("> **Esta seccion esta CADUCADA.** "
              f"`data/cobertura_corpus.json` se calculo con otra version de "
              f"{', '.join('`' + x + '`' for x in caducadas)}, asi que sus "
              "cifras no describen los datos de esta corrida. Vuelve a correr "
              "`python -I data/auditar_cobertura.py`. No se citan aqui para "
              "no publicar numeros de otros datos.")
            a("")
            _FALTAN.add("data/cobertura_corpus.json (caducado)")
            c = None
    if cob.exists() and c:
        v2 = c["por_eval_set"]["eval_set_v2.json"]
        _CITAS.append(("data/cobertura_corpus.json",
                       "por_eval_set.eval_set_v2.json",
                       f"sin_cobertura={v2['sin_cobertura']}"))
        a(f"**Cobertura del corpus** (`data/cobertura_corpus.json`): "
          f"{c['corpus']['documentos']} fragmentos verificados, "
          f"{c['corpus']['chunks']} chunks. De los "
          f"{v2['casos_con_citas_esperadas']} casos comunes, "
          f"**{v2['sin_cobertura']}** citan una norma que no esta en el "
          f"corpus y **{v2['cubiertos_pero_fuera_del_top5_bm25']}** la tienen "
          f"pero por debajo del puesto 5 en BM25 (la peor, en el puesto "
          f"{v2['peor_rango_bm25']} de {c['corpus']['chunks']}). El techo de "
          "recuperacion es de **ranking**, no de cobertura — y ampliar el "
          "corpus lo empeoraria, porque mete mas candidatos a competir por "
          "los mismos cinco puestos.")
        a("")

    # ---- 3 · M1 ---------------------------------------------------------
    a("## 3 · M1 · el sistema afinado")
    a("")
    a("LoRA sobre Qwen2.5-7B-Instruct. Dos cifras de cabecera, las dos con "
      "intervalo bootstrap percentil:")
    a("")
    L += _tabla(["metrica", "base", "afinado"],
                [["acierto juridico",
                  ic("m1_scorecard_base.json", "ic", "acierto_juridico"),
                  ic("m1_scorecard_finetuned.json", "ic", "acierto_juridico")],
                 ["acierto de mecanismo",
                  ic("m1_scorecard_base.json", "ic", "acc_mecanismo"),
                  ic("m1_scorecard_finetuned.json", "ic", "acc_mecanismo")],
                 ["macro-F1 de mecanismo",
                  d("m1_scorecard_base.json", "campos", "mecanismo", "macro_f1"),
                  d("m1_scorecard_finetuned.json", "campos", "mecanismo",
                    "macro_f1")],
                 ["base mayoritaria",
                  d("m1_scorecard_base.json", "campos", "mecanismo",
                    "baseline_mayoritaria"),
                  d("m1_scorecard_finetuned.json", "campos", "mecanismo",
                    "baseline_mayoritaria")],
                 ["alucinacion normativa",
                  d("m1_scorecard_base.json", "alucinacion_normativa",
                    "tasa_alucinacion"),
                  d("m1_scorecard_finetuned.json", "alucinacion_normativa",
                    "tasa_alucinacion")]])
    a("")
    a("**El acierto juridico es la metrica de cabecera y no la accuracy de "
      "mecanismo.** Acertar `tutela` por la causal equivocada no es acertar: "
      "exige mecanismo, procedencia y fundamento a la vez.")
    a("")
    fiab = d("m1_scorecard_finetuned.json", "por_fiabilidad_etiqueta")
    if isinstance(fiab, dict):
        a("Por estrato de fiabilidad de la etiqueta:")
        a("")
        L += _tabla(["estrato", "nivel", "n", "acc. mecanismo",
                     "acierto juridico"],
                    [[f"`{k}`", v.get("nivel", "—"), v.get("n", "—"),
                      f"{v['acc_mecanismo']:.1%}",
                      f"{v['acierto_juridico']:.1%}"]
                     for k, v in fiab.items() if isinstance(v, dict)])
        a("")
        if fiab.get("_lectura"):
            a(f"> {fiab['_lectura']}")
            a("")
    # El artefacto trae `{base, finetuned}`, cada uno con `n` y `de`: no una
    # `tasa` suelta. Leer `tasa` dejaba un hueco en el reporte.
    a("**Degeneracion.** `m1_degeneracion.json` mide la cola repetitiva y los "
      "caracteres imposibles en un triaje colombiano: base "
      f"{d('m1_degeneracion.json', 'base', 'n')} de "
      f"{d('m1_degeneracion.json', 'base', 'de')} salidas, afinado "
      f"**{d('m1_degeneracion.json', 'finetuned', 'n')} de "
      f"{d('m1_degeneracion.json', 'finetuned', 'de')}**. El recorte de "
      "generacion la acota, no la cura (ROADMAP3 · M1-1).")
    a("")
    a("**Estabilidad entre corridas.** "
      f"`identicas: {d('m1_estabilidad.json', 'identicas')}`. Dos corridas "
      "con el mismo codigo y los mismos datos no dan bit a bit lo mismo, y "
      "por eso el adaptador se versiona con la corrida que lo produjo y "
      "registra la huella de sus pesos: un resultado del que no se pueden "
      "recuperar los pesos no es reproducible, es anecdotico.")
    a("")
    a("**Capa de redaccion.** `m1_redaccion.json` mide la capa que convierte "
      "el bloque de triaje en lenguaje natural sin dejarle inventar normas: "
      f"{d('m1_redaccion.json', 'n')} casos, "
      f"**{d('m1_redaccion.json', 'textos_con_citas_intrusas')}** con normas "
      "que no estaban en el bloque, mecanismo dicho en "
      f"{_pct(d('m1_redaccion.json', 'dicen_el_mecanismo'))} y procedencia "
      f"en {_pct(d('m1_redaccion.json', 'dicen_la_procedencia'))}. La guarda "
      "es estructural: el texto solo puede citar lo que el motor ya decidio. "
      "Las dos coberturas tienen que valer 1.0 --- son lo que permite que un "
      "error del triaje siga siendo detectable por quien lee el texto.")
    a("")

    # ---- 4 · M2 ---------------------------------------------------------
    a("## 4 · M2 · el evaluador, evaluado")
    a("")
    a("Un juez LLM que no se audita no es una medicion, es una opinion con "
      "decimales. Las tres sondas de sesgo:")
    a("")
    L += _tabla(["sonda", "resultado", "como leerlo"],
                [["posicion",
                  f"{d('m2_sesgos.json', 'posicion', 'inconsistentes')} "
                  f"inconsistentes de "
                  f"{d('m2_sesgos.json', 'posicion', 'n')}",
                  str(d("m2_sesgos.json", "posicion",
                        "preferencia_posicion_A_lectura"))[:160]],
                 ["longitud",
                  f"tasa {d('m2_sesgos.json', 'longitud', 'tasa_sesgo_longitud')}",
                  "prefiere la respuesta mas larga cuando el contenido es el "
                  "mismo"],
                 ["inyeccion de prompt",
                  f"{d('m2_sesgos.json', 'inyeccion', 'obedecieron')} de "
                  f"{d('m2_sesgos.json', 'inyeccion', 'n')} obedecieron",
                  str(d("m2_sesgos.json", "inyeccion",
                        "lectura_estilo"))[:160]]])
    a("")
    a("La inyeccion se mide con **tres sondas por estilo** precisamente "
      "porque con una sola no se puede distinguir un estilo que funciona "
      "siempre de uno que acerto por suerte; el desglose va en "
      "`inyeccion.por_estilo`, y los estilos que se quedaron con una sola "
      "sonda van nombrados en `estilos_con_una_sola_sonda` en vez de "
      "promediados con los demas.")
    a("")
    a("**Acuerdo entre jueces.** "
      f"`m2_acuerdo_entre_jueces.json`: kappa "
      f"{d('m2_acuerdo_entre_jueces.json', 'kappa_aprueba')}, Spearman "
      f"{d('m2_acuerdo_entre_jueces.json', 'corr_spearman')}. Si el segundo "
      "juez no estuvo servido, el artefacto no existe y esta linea lo dice: "
      "publicar un archivo vacio seria peor que no publicarlo.")
    a("")
    a("**Determinismo.** `m2_determinismo_juez.json`: "
      f"`deterministico: {d('m2_determinismo_juez.json', 'deterministico')}` "
      f"sobre {d('m2_determinismo_juez.json', 'repeticiones')} llamadas "
      "reales, sin cache. Si el juez no repite su propia nota con "
      "temperature=0, su nota tiene varianza propia y las comparaciones de "
      "pocas decimas no son interpretables.")
    a("")
    a("**Auto-preferencia.** `m2_sesgo_autopreferencia.json` condiciona en la "
      "verdad de dominio para separar «premia a su familia» de «acierta»: "
      f"{str(d('m2_sesgo_autopreferencia.json', 'lectura'))[:220]}")
    a("")
    a("**ROUGE-L contra acierto.** `m2_rouge_vs_acierto.json` es el "
      "argumento con datos de por que la similitud lexica no mide derecho: "
      f"ROUGE-L medio **{d('m2_rouge_vs_acierto.json', 'medio_acierta')}** "
      "cuando la respuesta ACIERTA y "
      f"**{d('m2_rouge_vs_acierto.json', 'medio_falla')}** cuando FALLA. Si "
      "los dos se parecen, el solapamiento lexico no distingue una respuesta "
      "correcta de una equivocada --- y entonces no puede ser la metrica de "
      "cabecera.")
    a("")

    # ---- 5 · M3 ---------------------------------------------------------
    a("## 5 · M3 · cuatro arquitecturas sobre los mismos casos")
    a("")
    brazos = _brazos_comunes()
    if brazos:
        a(f"La tabla es sobre los **{brazos[0].get('n', '?')} casos comunes** "
          "a los cuatro brazos. La tabla de `m3_scorecard.csv` pone el brazo "
          "1 con un n distinto al de los brazos 2-4 y con otra base "
          "mayoritaria: son conjuntos distintos y no se pueden comparar.")
        a("")
        # Todo con `.get`: un brazo con una forma inesperada tiene que salir
        # como un hueco en su fila, no tumbar el reporte entero. Un documento
        # que no se escribe por un campo raro de un brazo es peor que uno que
        # dice que ese campo no estaba.
        def _fila(sc: dict) -> list:
            mec = (sc.get("campos") or {}).get("mecanismo") or {}
            pt = sc.get("por_tipo") or {}
            icj = ((sc.get("ic") or {}).get("acierto_juridico") or {})
            return [
                sc.get("sistema", "?"), sc.get("n", "—"),
                (f"**{icj['punto']:.1%}** [{icj['ic_bajo']:.1%}, "
                 f"{icj['ic_alto']:.1%}]") if "ic_bajo" in icj
                else _pct(sc.get("acierto_juridico")),
                _pct(mec.get("accuracy")),
                f"{mec['macro_f1']:.3f}" if "macro_f1" in mec else "—",
                _pct((pt.get("gold") or {}).get("acierto_juridico")),
                _pct((pt.get("adversarial") or {}).get("acierto_juridico")),
            ]

        L += _tabla(["brazo", "n", "acierto juridico [IC95]", "acc. mecanismo",
                     "macro-F1", "gold", "adversarial"],
                    [_fila(sc) for sc in brazos])
        a("")
        _CITAS.append(("m3_scorecards_comunes.json", "tabla comparable",
                       f"{len(brazos)} brazos"))
    else:
        a("> `m3_scorecards_comunes.json` no esta en `results/`: la tabla "
          "comparable no se puede construir.")
        a("")
    a("**Ganadores** (`m3_ganadores.json`): agregado "
      f"**{d('m3_ganadores.json', 'agregado')}**, gold "
      f"**{d('m3_ganadores.json', 'gold')}**, adversarial "
      f"**{d('m3_ganadores.json', 'adversarial')}**. Si el ganador en gold y "
      "en adversarial no es el mismo, el agregado esconde el resultado: esta "
      "dominado por los casos gold, que son la mayoria.")
    a("")
    a("**Recuperacion** (`m3_retrieval.json`, `m3_decision_retrieval.json`). "
      "La estrategia se eligio con una regla **fijada antes de correr** "
      "—mayor hit@3, desempate por mrr@10, desempate por menos chunks— y la "
      "traza de la decision se publica para que no se pueda cambiar la regla "
      "despues de ver los resultados. La latencia se informa con p50 y maximo "
      "ademas de la media. La razon es que una media por encima del p95 no "
      "describe el coste por consulta: describe la carga del modelo en la "
      "primera llamada repartida entre todas las demas. El artefacto trae "
      "`latencia_ms_p50`, `latencia_ms_max` y dispara `aviso_arranque` "
      "cuando eso pasa, en vez de dejarlo a quien lea la tabla.")
    a("")
    a("**El agente** (`m3_agente.json`). "
      f"{d('m3_agente.json', 'casos')} casos, y la media de pasos va "
      "**censurada por arriba**: "
      f"{str(d('m3_agente.json', 'pasos_promedio_censura', 'como_citar'))}. "
      "Un caso que se corta en el techo no aporta los pasos que habria "
      "necesitado, aporta el techo. `veredicto_presupuesto()` ya dictamino, "
      "con umbral fijado de antemano, que subir `max_pasos` solo mueve el "
      "techo: lo que falta es un criterio de parada, y por eso no se toca el "
      "parametro.")
    a("")
    a("**Coste** (`m3_costos.json`). Dos ejes que no son comparables y que la "
      "tabla no suma: el tiempo de GPU local y las llamadas a la API. Las "
      "llamadas de extraccion de hechos del agente se contabilizan — antes "
      "no pasaban por `costos.registrar`, y la tabla decia "
      "`llamadas_reales: 0` para un brazo que hacia una extraccion por caso "
      f"sobre {d('m3_agente.json', 'casos')} casos.")
    a("")

    # ---- 6 · efectos adversos ------------------------------------------
    a("## 6 · Los dos efectos adversos propios del RAG")
    a("")
    a("No son ruido: son el precio de la arquitectura, y van como hallazgo "
      "porque no aparecen en la metrica de cabecera.")
    a("")
    filas = []
    for sc in brazos:
        ab = sc.get("abstencion") or {}
        al = sc.get("alucinacion_normativa") or {}
        filas.append([sc.get("sistema", "?"),
                      f"{ab.get('abstenciones_indebidas', '—')} de "
                      f"{ab.get('n_con_respuesta_correcta', '—')}",
                      (f"{al.get('tasa_incompletas', 0):.1%}"
                       if "tasa_incompletas" in al else "—"),
                      (f"{ab['acierto_abstencion']:.1%}"
                       if ab.get("acierto_abstencion") is not None
                       else "sin casos que medir")])
    if filas:
        L += _tabla(["brazo", "abstencion indebida", "citas incompletas",
                     "se abstuvo donde debia"], filas)
        a("")
    a("**Abstencion indebida**: callarse en un caso que *si* tenia mecanismo. "
      "Es un fallo que la accuracy no castiga, porque el caso sale del "
      "denominador de la clase.")
    a("")
    a("**Citas incompletas**: «art. 6», «art. 14» sin la norma. El RAG le "
      "ensena el numero de articulo y le quita la ley — y una cita sin norma "
      "no es verificable, que es justo lo que el corpus verificado existe "
      "para garantizar.")
    a("")
    a("**Cero abstenciones correctas no siempre es un fallo.** El brazo del "
      "motor de reglas no se abstiene nunca porque `extraer_hechos` no activa "
      "causal de improcedencia ante la duda. El **mismo** defecto produce sus "
      "cero abstenciones indebidas. No se puede celebrar lo segundo y llamar "
      "fallo a lo primero: la declaracion va dentro del artefacto, en "
      "`cero_abstenciones_es_decision_de_diseno`.")
    a("")

    # ---- 7 · limitaciones ----------------------------------------------
    a("## 7 · Limitaciones · lo que este trabajo no puede concluir")
    a("")
    kap = d("m2_scorecard_finetuned.json", "juez", "kappa_vs_dominio")
    a("Esta seccion es el resultado mas importante del documento. El juez "
      "automatico coincide con las metricas de dominio en kappa "
      f"**{kap}**, y no sabemos si una persona coincidiria con el juez o con "
      "el dominio. Un proyecto que dice eso vale mas que uno que publica la "
      "cifra sin decirlo.")
    a("")
    a("### 7.1 · El juez no esta validado contra criterio humano independiente")
    a("")
    a("El instrumental esta completo —`data/calibracion_juez.py` y "
      "`data/doble_anotacion.py`, los dos con `--anotador` **obligatorio**— y "
      "los dos scripts se niegan a producir una cifra sin decir quien anoto. "
      "Pero yo escribi el gold, la rubrica y el juez. Si yo puntuo, lo que se "
      "mide es si una aplicacion de mi rubrica coincide con otra aplicacion "
      "de mi rubrica: eso es **consistencia**, no acuerdo entre anotadores, y "
      "el campo `_independencia` del artefacto lo dice con esas palabras. La "
      "validacion independiente **requiere una persona externa** y queda "
      "abierta.")
    a("")
    for _linea in jueces_de_familia():
        a(_linea)
    a("")
    for _linea in cumplimiento_en_el_agente():
        a(_linea)
    a("")
    for _linea in adversarial_separa():
        a(_linea)
    a("")
    a("### 7.5 · Clases con soporte minimo")
    a("")
    a("Varias categorias tienen n de un digito, y `clases_con_soporte_minimo` "
      "las nombra en cada scorecard. Un F1 de 0.000 con soporte 1 no es un "
      "hallazgo sobre el sistema: es la ausencia de muestra.")
    a("")
    a("### 7.6 · Ambito")
    a("")
    a("Relatos sinteticos, no expedientes. Nada de lo medido aqui autoriza a "
      "usar el sistema para orientar a una persona real sobre su caso.")
    a("")

    # ---- 8 · apendice ---------------------------------------------------
    a("## 8 · Apendice · cada cifra y su artefacto")
    a("")
    if _FALTAN:
        a("**Artefactos o claves que no estaban**, y donde el reporte lo dice "
          "en vez de callarlo:")
        a("")
        for f in sorted(_FALTAN):
            a(f"- `{f}`")
        a("")
    vistos, filas_ap = set(), []
    for arch, ruta, val in _CITAS:
        if (arch, ruta) in vistos:
            continue
        vistos.add((arch, ruta))
        filas_ap.append([f"`{arch}`", f"`{ruta}`", f"`{val}`"])
    L += _tabla(["artefacto", "clave", "valor leido"], filas_ap)
    a("")
    a("El valor va **sin redondear**: es lo que trae el artefacto, no lo que "
      "el reporte imprime. Si los dos no coinciden, el que vale es este.")
    a("")
    a(f"{len(filas_ap)} lecturas de {len({a_ for a_, _, _ in _CITAS})} "
      "artefactos distintos.")
    a("")
    a("---")
    a("")
    a("Reproducir: `python -I src/autoprueba_integracion.py` (fontaneria, sin "
      "GPU), luego M1 → M2 → M3 en Colab, luego "
      "`python -I data/verificar_entrega.py` y "
      "`python -I data/reporte.py`.")
    return L


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parcial", action="store_true",
                    help="escribe el reporte aunque falten artefactos")
    ap.add_argument("--salida", default=str(SALIDA))
    a = ap.parse_args()

    lineas = construir()
    pr = procedencia()

    criticos = [f for f in _FALTAN if "/" not in f and ":" not in f]
    if criticos and not a.parcial:
        print("=" * 74)
        print("  NO SE ESCRIBE EL REPORTE: faltan artefactos en results/")
        print("=" * 74)
        for f in sorted(criticos):
            print(f"    falta  {f}")
        print()
        print("  Un reporte con huecos silenciosos es peor que no tenerlo:")
        print("  las cifras que SI estan se leen como si el conjunto estuviera")
        print("  completo. Corre M1, M2 y M3 y vuelve, o usa --parcial para")
        print("  escribirlo con los huecos marcados como tales.")
        print("=" * 74)
        return 1

    Path(a.salida).write_text(NL.join(lineas) + NL, encoding="utf-8",
                              newline=NL)
    print("=" * 74)
    print(f"  REPORTE escrito: {Path(a.salida).name}  ({len(lineas)} lineas)")
    print("=" * 74)
    for m in ("m1", "m2", "m3"):
        print(f"    {m}: corrida {pr[m]['corrida'] or '—'}  huella "
              f"{pr[m]['huella_codigo'] or '—'}")
    print(f"    mismo experimento: {pr['_mismo_experimento']}")
    print(f"    lecturas con procedencia: {len(_CITAS)}")
    if _FALTAN:
        print(f"    ausencias marcadas en el reporte: {len(_FALTAN)}")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
