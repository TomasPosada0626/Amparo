"""
Validación humana del JUEZ: un abogado puntúa lo mismo que puntuó el modelo.

QUÉ CIERRA, Y POR QUÉ NINGUNA OTRA SONDA LO CIERRA

M2 tiene cinco sondas sobre el juez. Cuatro miden si se le puede **engañar**
—posición, longitud, familia, inyección— y la quinta, `experimento_validez`,
mide si **responde al defecto**: si le baja la nota a un gold degradado. Las
cinco se pueden pasar sin que la nota se parezca al criterio de un abogado.
`experimento_validez` lo dice en su propia salida: es validez de construcción,
no acuerdo con un humano.

Esto es el acuerdo con un humano. Es M2-1b y es lo único que lo cierra.

NO CONFUNDIR CON `revision_abogado_v3.py`. Aquel validó el **gold**: si los 40
casos nuevos del eval set están bien codificados (`hechos_ok`, `derecho_ok`,
`normas_ok`, `realista`). Salió 40/40 y una nota global de 4.9/5, y eso es un
resultado sobre los DATOS. No dice nada sobre el juez, que es otro
instrumento: un eval set impecable puntuado por un juez ciego da cifras
inservibles igual.

CÓMO SE USA

    # después de correr M2, con `results/` al día
    python -I data/validacion_juez.py            # escribe el formulario
    #   ... el abogado rellena la columna `nota` y lo devuelve ...
    python -I data/validacion_juez.py --leer     # publica el acuerdo

LA MUESTRA ESTÁ SESGADA A PROPÓSITO, Y ESO CAMBIA LO QUE LA CIFRA DICE

Las notas del juez se concentran en 4 y 5. Una muestra proporcional serían 25
casos con casi toda la varianza en un punto, y una correlación sobre eso no
distingue un juez bueno de uno que siempre dice 5. Así que se toman hasta 5
casos de CADA nota, lo que sobre-representa las notas bajas entre 5 y 20 veces.

Consecuencia, que viaja en el artefacto: el acuerdo resultante **no estima el
acuerdo sobre el eval set entero**. Estima el acuerdo condicionado a los
estratos muestreados, que es la pregunta útil —¿cuando el juez dice 2, un
abogado también?— y no la que parece. Es la misma disciplina que `censurado` en
la media de pasos del agente: la cifra se publica con lo que la limita.
"""
from __future__ import annotations
import csv
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "data"))

import corridas                                            # noqa: E402
import formularios                                         # noqa: E402
import harness                                             # noqa: E402
import juez                                                # noqa: E402
import schema                                              # noqa: E402

NOTAS = RAIZ / "results" / "m2_scorecard_por_caso.csv"
PREDS = RAIZ / "results" / "m1_predicciones.json"
SALIDA = RAIZ / "data" / "validacion_juez"
# `RUTA_OUT` no es un nombre cualquiera: la prueba 33 busca ese patron en
# `data/*.py` para comprobar que la salida este en `manifiesto.EXCLUIR`.
# Llamarla de otro modo la dejaria fuera del guardian --- y `data/*.json`
# esta en la huella, asi que leer este formulario entre M2 y M3 les daria
# huellas de codigo distintas.
RUTA_OUT = RAIZ / "data" / "validacion_juez.json"

N_POR_NOTA = 5
"""Hasta 5 casos de cada nota del juez. Ver la nota de cabecera: es un sesgo
declarado, no un descuido."""

COLUMNAS_PERSONA = ("nota", "comentario")
# `nota` Y `comentario` VAN SEGUNDA Y TERCERA, NO AL FINAL.
#
# Estaban al final, detras de `caso`, `respuesta_de_referencia` y
# `respuesta_del_sistema`, que son textos largos y suman ~160 de ancho: la
# columna donde hay que ESCRIBIR quedaba fuera de la pantalla, y quien
# rellenaba tenia que buscarla veinticinco veces. Con `congelar_columnas=3`
# ademas se quedan fijas al desplazarse a la derecha para leer.
#
# El orden de lectura se pierde un poco --- primero ves el hueco y luego el
# caso --- y vale la pena: `_leer_xlsx` empareja por NOMBRE de cabecera, asi
# que reordenar no rompe `--leer`, y lo que se gana es que la casilla no se
# pueda perder de vista.
CABECERA = ["id", *COLUMNAS_PERSONA, "tipo", "categoria", "caso",
            "respuesta_de_referencia", "respuesta_del_sistema"]

# La escala tiene que ser LA MISMA que la del juez, palabra por palabra. Si el
# abogado puntúa con otra definición de "3", el desacuerdo que se mida es el de
# las dos escalas, no el de los dos criterios --- y la cifra no diría nada
# sobre el juez. Se extrae de `juez.RUBRICA` en vez de copiarse para que no
# puedan separarse en silencio.
def _escala() -> list[str]:
    lineas = juez.RUBRICA.splitlines()
    i = next(k for k, l in enumerate(lineas) if l.startswith("Escala"))
    j = next(k for k, l in enumerate(lineas[i:], i) if l.startswith("Reglas"))
    return [l for l in lineas[i:j] if l.strip()]


INSTRUCCIONES = [
    "VALIDACION DEL JUEZ AUTOMATICO · proyecto Amparo (M2-1b)",
    "",
    "Que hay aqui: casos que un modelo-juez ya califico de 1 a 5. Su nota NO",
    "aparece en esta hoja, a proposito: verla anclaria la suya y el acuerdo",
    "que midieramos despues no significaria nada.",
    "",
    "Que hay que hacer: por cada fila, leer el CASO, la RESPUESTA DE",
    "REFERENCIA (la que el equipo considera correcta) y la RESPUESTA DEL",
    "SISTEMA, y poner en `nota` un entero de 1 a 5 con esta escala ---",
    "que es, palabra por palabra, la que se le dio al modelo-juez:",
    "",
    *["   " + l for l in _escala()],
    "",
    "Dos reglas que tambien se le dieron al modelo, para que el criterio sea",
    "el mismo:",
    "   - La extension NO es calidad. Una respuesta corta y correcta vale mas",
    "     que una larga y equivocada.",
    "   - Si la respuesta cita una norma que no viene al caso, baja la nota.",
    "",
    "`comentario` es opcional y solo hace falta donde la nota le parezca",
    "discutible: es lo que permite entender un desacuerdo en vez de contarlo.",
    "",
    "Lo que se hace con esto: se compara su columna con la del modelo. Si",
    "coinciden, las notas del juez se pueden reportar; si no, no --- y en ese",
    "caso lo que se publica es que no se pueden reportar.",
]


def _eval_set_de(ids: set[str]) -> tuple[list[dict], str]:
    """El eval set que contiene esos ids. NO se codifica el nombre a mano.

    `eval_set_v2.json` estuvo escrito a mano en `reporte.py` y siguió ahí
    cuando el eval set pasó a v3: la cobertura se leyó del archivo viejo
    durante una corrida entera. El nombre del eval set vigente se deriva, no
    se recuerda.
    """
    candidatos = sorted((RAIZ / "data").glob("eval_set*.json"))
    mejor, nombre, cubre = [], None, -1.0
    for p in candidatos:
        try:
            ej = json.loads(p.read_text(encoding="utf-8"))["ejemplos"]
        except Exception:                                  # noqa: BLE001
            continue
        prop = len(ids & {e["id"] for e in ej}) / (len(ids) or 1)
        if prop > cubre:
            mejor, nombre, cubre = ej, p.name, prop
    if cubre < 1.0:
        raise SystemExit(
            f"ningun eval set de data/ contiene los {len(ids)} ids de "
            f"{NOTAS.name} (el mejor, {nombre}, cubre {cubre:.0%}). "
            "Las notas y el eval set son de corridas distintas.")
    return mejor, nombre


def _filas_del_juez() -> list[dict]:
    if not NOTAS.exists():
        raise SystemExit(
            f"falta {NOTAS.relative_to(RAIZ)}. Lo publica M2; hay que correrlo "
            "y bajar `results/` antes de pedirle nada a una persona.")
    with NOTAS.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _respuestas() -> dict[str, str]:
    d = json.loads(PREDS.read_text(encoding="utf-8"))
    filas = d.get("datos", d) if isinstance(d, dict) else d
    return {p["id"]: p["finetuned"] for p in filas}


def _muestra(filas: list[dict]) -> tuple[list[dict], dict]:
    """Hasta `N_POR_NOTA` por nota del juez, con semilla fija."""
    por_nota: dict[str, list[dict]] = {}
    for f in filas:
        por_nota.setdefault((f.get("nota_juez") or "").strip() or "sin nota",
                            []).append(f)
    rnd = random.Random(corridas.SEMILLA)
    sel, tomados = [], {}
    for nota in sorted(por_nota):
        grupo = sorted(por_nota[nota], key=lambda f: f["id"])
        rnd.shuffle(grupo)
        tomados[nota] = grupo[:N_POR_NOTA]
        sel += tomados[nota]
    # La sobre-representación se calcula CON LA MUESTRA YA CERRADA. Hacerlo
    # dentro del bucle la dividía por el total parcial, así que el primer
    # estrato salía con el 100% de la muestra y la cifra no significaba nada.
    plan = {
        nota: {"disponibles": len(por_nota[nota]), "tomados": len(t),
               "peso_en_la_muestra": round(len(t) / len(sel), 3),
               "peso_en_el_eval": round(len(por_nota[nota]) / len(filas), 3),
               "sobre_representado_x": round(
                   (len(t) / len(sel)) / (len(por_nota[nota]) / len(filas)), 2)}
        for nota, t in tomados.items()
    }
    sel.sort(key=lambda f: f["id"])
    return sel, plan


def escribir() -> int:
    filas_juez = _filas_del_juez()
    ids = {f["id"] for f in filas_juez}
    ejemplos, nombre_eval = _eval_set_de(ids)
    gold = {e["id"]: e for e in ejemplos}
    respuestas = _respuestas()

    faltan = [i for i in ids if i not in respuestas]
    if faltan:
        raise SystemExit(
            f"{len(faltan)} de {len(ids)} casos no están en "
            f"{PREDS.name} ({', '.join(faltan[:5])}...): las notas y las "
            "respuestas son de corridas distintas y el formulario mostraría "
            "una respuesta que el juez no vio.")

    sel, plan = _muestra(filas_juez)
    filas = []
    for f in sel:
        e = gold[f["id"]]
        # El orden sigue a CABECERA: los dos huecos de la persona van
        # detras del id, no al final.
        filas.append([f["id"], "", "", f.get("tipo"), f.get("categoria"),
                      e["relato"], schema.render_salida(e),
                      respuestas[f["id"]]])

    print("=" * 76)
    print("  VALIDACION DEL JUEZ · formulario para el abogado (M2-1b)")
    print("=" * 76)
    print(f"  notas del juez : {NOTAS.name} · {len(filas_juez)} casos")
    print(f"  eval set       : {nombre_eval} (derivado de los ids)")
    print(f"  respuestas     : {PREDS.name} · brazo `finetuned`")
    print()
    print(f"  {'nota del juez':<16}{'disponibles':>12}{'en la muestra':>15}")
    print("  " + "-" * 43)
    for nota, d in plan.items():
        print(f"  {nota:<16}{d['disponibles']:>12}{d['tomados']:>15}")
    print("  " + "-" * 43)
    print(f"  {'TOTAL':<16}{len(filas_juez):>12}{len(filas):>15}")
    print()
    print("  La muestra NO es proporcional: toma hasta "
          f"{N_POR_NOTA} de cada nota para que")
    print("  haya varianza en los extremos. El acuerdo que salga estima el")
    print("  acuerdo CONDICIONADO a estos estratos, no el del eval set entero,")
    print("  y el artefacto lo dice.")
    print()

    hizo = formularios.escribir_xlsx(
        SALIDA.with_suffix(".xlsx"), INSTRUCCIONES, CABECERA, filas,
        COLUMNAS_PERSONA, opciones={"nota": ["1", "2", "3", "4", "5"]},
        congelar_columnas=3)
    print(f"  escrito: data/{SALIDA.name}.xlsx  "
          + ("(con desplegable de 1 a 5)" if hizo else "NO (falta openpyxl)"))

    # El CSV va siempre: es el que se puede leer sin Excel. Con BOM, porque
    # sin él Excel abre un UTF-8 con los acentos partidos.
    with SALIDA.with_suffix(".csv").open("w", encoding="utf-8-sig",
                                         newline="") as f:
        w = csv.writer(f)
        w.writerow(CABECERA)
        w.writerows(filas)
    print(f"  escrito: data/{SALIDA.name}.csv   (utf-8 con BOM, para Excel)")
    print()
    print("  Que haga el abogado: rellenar `nota` (1 a 5) en las "
          f"{len(filas)} filas.")
    print("  `comentario` solo donde la nota le parezca discutible.")
    print("  Su nota del juez NO esta en la hoja: verla anclaria la suya.")
    print("=" * 76)
    return 0


def _casos_que_se_movieron(filas: list[dict]) -> list[dict]:
    """Que casos del formulario ya no describen la corrida vigente.

    Compara lo que el abogado TENIA DELANTE --- la columna
    `respuesta_del_sistema` del formulario que devolvio --- con lo que
    `results/` publica hoy. Si no coinciden, su nota puntua una salida que ya
    no existe.

    Se normalizan los finales de linea y los espacios de los extremos: Excel
    los reescribe al guardar y eso no es un cambio de la respuesta. Nada mas.
    """
    try:
        respuestas = _respuestas()
    except Exception:                                          # noqa: BLE001
        # Sin predicciones no se puede comparar; `escribir` ya tiene su propia
        # guarda para eso y `leer` no debe inventarse una conclusion.
        return []
    por_id_juez = {f["id"]: f for f in _filas_del_juez()}

    def norm(x) -> str:
        return "\n".join(l.rstrip() for l in str(x or "")
                          .replace("\r\n", "\n").split("\n")).strip()

    movidas = []
    for f in filas:
        if not (f.get("nota") or "").strip():
            continue        # sin nota no hay nada que invalidar
        cid = f["id"]
        vista = norm(f.get("respuesta_del_sistema"))
        ahora = norm(respuestas.get(cid))
        if not vista:
            # Formulario antiguo sin la columna: no se puede comprobar, y
            # decirlo es mejor que dar por bueno lo que no se miro.
            movidas.append({"id": cid, "que_cambio":
                            "el formulario no trae `respuesta_del_sistema`, "
                            "asi que no se puede comprobar contra que puntuo"})
            continue
        if vista != ahora:
            movidas.append({"id": cid, "que_cambio":
                            f"la respuesta del sistema cambio "
                            f"({len(vista)} -> {len(ahora)} caracteres)"})
            continue
        if cid not in por_id_juez:
            movidas.append({"id": cid, "que_cambio":
                            "el juez vigente no puntuo este caso"})
    return movidas


def leer() -> int:
    ruta = next((p for p in (SALIDA.with_suffix(".xlsx"),
                             SALIDA.with_suffix(".csv")) if p.exists()), None)
    if ruta is None:
        raise SystemExit(f"no está ni {SALIDA.name}.xlsx ni .csv. "
                         "Corre el script sin `--leer` para escribirlo.")
    leido = formularios.leer(ruta, COLUMNAS_PERSONA)
    filas = leido["filas"]
    por_id_juez = {f["id"]: f for f in _filas_del_juez()}
    movidas = _casos_que_se_movieron(filas)

    pares, invalidas, sin_nota = [], [], []
    for f in filas:
        bruto = (f.get("nota") or "").strip()
        if not bruto:
            sin_nota.append(f["id"])
            continue
        try:
            n_ab = int(float(bruto))
        except ValueError:
            invalidas.append({"id": f["id"], "valor": bruto[:30]})
            continue
        if not 1 <= n_ab <= 5:
            invalidas.append({"id": f["id"], "valor": bruto[:30]})
            continue
        fj = por_id_juez.get(f["id"])
        n_ju = (fj or {}).get("nota_juez", "")
        try:
            n_ju = int(float(str(n_ju).strip()))
        except ValueError:
            n_ju = None
        pares.append({"id": f["id"], "nota_juez": n_ju, "nota_abogado": n_ab,
                      "comentario": (f.get("comentario") or "").strip()})

    print("=" * 76)
    print("  VALIDACION DEL JUEZ · lectura (M2-1b)")
    print("=" * 76)
    print(f"  archivo        : {ruta.name} ({leido['codificacion']})")
    print(f"  filas          : {len(filas)}")
    print(f"  con nota       : {len(pares)}")
    if sin_nota:
        print(f"  SIN nota       : {len(sin_nota)}  ({', '.join(sin_nota[:8])})")
    if invalidas:
        print(f"  NO numericas   : {len(invalidas)}  {invalidas[:4]}")
    print()

    if movidas:
        # NO SE PUBLICA LA KAPPA. No es un aviso: es que la cifra no existe.
        print("=" * 76)
        print(f"  LAS NOTAS SON DE OTRA CORRIDA · {len(movidas)} de "
              f"{len(filas)} casos")
        print("=" * 76)
        for m in movidas[:6]:
            print(f"  {m['id']:<6} {m['que_cambio']}")
        if len(movidas) > 6:
            print(f"  ... y {len(movidas) - 6} mas")
        print()
        print("  El abogado puntuo la respuesta que tenia delante. Si la")
        print("  respuesta del sistema cambio, su nota no es una lectura de")
        print("  la salida que el juez puntuo, y la kappa entre las dos no")
        print("  mide el acuerdo de dos criterios: mide dos corridas.")
        print()
        print("  Las dos salidas honestas:")
        print("    1. conservar la medicion vieja Y los artefactos de la")
        print("       corrida con la que se hizo, y citarla con su corrida;")
        print("    2. volver a escribir el formulario con las respuestas")
        print("       nuevas y pedir que se puntue otra vez.")
        print()
        print("  Lo que NO es una opcion es recalcular la kappa con las notas")
        print("  viejas sobre las respuestas nuevas.")
        print("=" * 76)
        return 1

    if not pares:
        # El fallo que `formularios` existe para no repetir: informar "cero
        # respuestas" sobre un formulario entero relleno.
        print("  NINGUNA fila trae nota. Si el abogado lo rellenó, esto es un")
        print("  fallo de lectura y no una respuesta: mirar la cabecera.")
        print(f"  cabecera leida : {leido.get('cabecera')}")
        print(f"  columnas que faltan: {leido.get('columnas_que_faltan')}")
        print("=" * 76)
        return 1

    # EL ACUERDO SE CALCULA CON `harness.acuerdo_entre_jueces`, NO CON UNA
    # COPIA. Un abogado es otro juez: misma aritmética, misma kappa sobre la
    # decisión binaria (nota >= 4), misma Spearman. Escribirla aparte haría
    # que M2-1b y el acuerdo entre modelos dejaran de ser comparables, que es
    # justo lo que esta medición existe para permitir.
    ac = harness.acuerdo_entre_jueces(
        [{"nota": p["nota_juez"]} for p in pares],
        [{"nota": p["nota_abogado"]} for p in pares],
        juez.MODELO, juez.JUEZ_HUMANO)

    desacuerdos = sorted(
        (p for p in pares
         if p["nota_juez"] is not None
         and abs(p["nota_juez"] - p["nota_abogado"]) >= 2),
        key=lambda p: -abs(p["nota_juez"] - p["nota_abogado"]))

    # DE QUE CORRIDA SON LAS RESPUESTAS QUE SE CALIFICARON.
    #
    # Sin esto el artefacto no se puede interpretar despues de una corrida
    # nueva: las 25 notas se pusieron sobre las respuestas de UNA corrida de
    # M1, y si M1 vuelve a entrenar, `m1_predicciones.json` se reemplaza y el
    # par (caso, respuesta) que el abogado juzgo deja de existir. El acuerdo
    # sigue siendo una propiedad del JUEZ --- es lo que se validaba --- pero
    # solo si se puede decir sobre que lo fue.
    #
    # Se registran las dos procedencias porque son dos corridas distintas: las
    # respuestas salen de M1 y las notas del juez de M2.
    _pred = json.loads(PREDS.read_text(encoding="utf-8"))
    _c_m1 = _pred.get("_corrida") if isinstance(_pred, dict) else None
    _lado = NOTAS.with_suffix(".corrida.txt")
    _c_m2 = (_lado.read_text(encoding="utf-8").strip()
             if _lado.exists() else None)

    # SI LAS RESPUESTAS YA NO SON LAS QUE SE CALIFICARON, ESTO SE PARA.
    #
    # Registrar la procedencia no basta. Si M1 vuelve a entrenar,
    # `m1_predicciones.json` se reemplaza y M2 re-puntua las respuestas
    # NUEVAS; las 25 notas del abogado son sobre las VIEJAS. Emparejar por
    # `id` daria una kappa sobre pares que no se corresponden, y saldria sin
    # una queja --- el peor tipo de fallo de este proyecto: una cifra
    # plausible e inservible que nada delata.
    #
    # La comparacion correcta es contra la procedencia que el artefacto
    # anterior guardo, no contra una constante: asi el guardian vale para
    # cualquier corrida futura y no hay nada que acordarse de actualizar.
    if RUTA_OUT.exists():
        try:
            _ant = json.loads(RUTA_OUT.read_text(encoding="utf-8"))
        except Exception:                                  # noqa: BLE001
            _ant = {}
        _antes_m1 = _ant.get("corrida_de_las_respuestas")
        if _antes_m1 and _c_m1 and _antes_m1 != _c_m1:
            raise SystemExit(
                "\n" + "=" * 72 + "\n"
                "  NO SE RECALCULA: las respuestas cambiaron de corrida.\n"
                + "=" * 72 + "\n"
                f"  el abogado califico las respuestas de m1/{_antes_m1}\n"
                f"  y `results/m1_predicciones.json` ahora es de m1/{_c_m1}\n\n"
                "  Emparejar por `id` daria una kappa sobre pares que no se\n"
                "  corresponden, y saldria sin avisar. Dos salidas:\n\n"
                "   1. Conservar la medicion anterior. Sigue siendo valida:\n"
                "      el JUEZ es lo que se validaba y no cambio. Queda\n"
                f"      anclada a m1/{_antes_m1}, y el artefacto lo dice.\n"
                "   2. Volver a pedirle al abogado que califique, sobre las\n"
                "      respuestas nuevas:\n"
                "         python -I data/validacion_juez.py --html\n"
                "      y despues `--leer` con el formulario nuevo.\n\n"
                "  Lo que NO hay es una tercera: recalcular con estas notas\n"
                "  sobre esas respuestas no mide nada.\n" + "=" * 72)

    out = {
        "corrida_de_las_respuestas": _c_m1,
        "corrida_de_las_notas_del_juez": _c_m2,
        "procedencia": (
            "las 25 respuestas calificadas son las del brazo `finetuned` de "
            f"m1/{_c_m1}, y las notas del juez con las que se comparan son de "
            f"{_c_m2}. Si M1 vuelve a entrenar, esas respuestas se reemplazan: "
            "el acuerdo medido aqui sigue siendo una propiedad del juez, que "
            "no cambio, pero queda referido a ESTAS respuestas y no a las "
            "nuevas. Volver a correr M1 no invalida la cifra; la deja anclada "
            "a una corrida anterior, y eso hay que poder decirlo."),
        "que_mide": ("acuerdo entre el juez automático y un abogado sobre las "
                     "MISMAS respuestas y con la MISMA rúbrica (M2-1b)"),
        "no_confundir_con": (
            "`revision_abogado_v3.json`, que validó el GOLD (40/40, 4.9/5). "
            "Eso es un resultado sobre los datos; esto es sobre el "
            "instrumento que los puntúa."),
        "acuerdo": ac,
        "muestra_no_proporcional": (
            f"la muestra tomó hasta {N_POR_NOTA} casos por nota del juez, así "
            "que sobre-representa las notas bajas. El acuerdo estima el "
            "acuerdo CONDICIONADO a esos estratos, no el del eval set "
            "entero."),
        "n_sin_nota": len(sin_nota), "sin_nota": sin_nota,
        "n_no_numericas": len(invalidas), "no_numericas": invalidas,
        "desacuerdos_de_2_o_mas": desacuerdos,
        "pares": pares,
    }
    RUTA_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                       encoding="utf-8", newline="\n")

    print(f"  n                 : {ac['n']}")
    print(f"  media juez        : {ac.get('media_a')}")
    print(f"  media abogado     : {ac.get('media_b')}")
    print(f"  acuerdo exacto    : {ac.get('acuerdo_exacto')}")
    print(f"  acuerdo a 1 punto : {ac.get('acuerdo_a_un_punto')}")
    print(f"  kappa (nota >= 4) : {ac.get('kappa_aprueba')}")
    print(f"  Spearman          : {ac.get('corr_spearman')}")
    print()
    if desacuerdos:
        print(f"  {len(desacuerdos)} desacuerdo(s) de 2 puntos o más --- son los")
        print("  que hay que leer, no el promedio:")
        for p in desacuerdos[:8]:
            print(f"    {p['id']:<8} juez {p['nota_juez']} · abogado "
                  f"{p['nota_abogado']}  {p['comentario'][:48]}")
    else:
        print("  ningún desacuerdo de 2 puntos o más.")
    print()
    print(f"  escrito: data/{RUTA_OUT.name}")
    print("  Lo que ESTO no dice: que el juez tenga razón donde el abogado y")
    print("  él coinciden en una nota equivocada. Mide acuerdo, no verdad.")
    print("=" * 76)
    return 0


CSS = """
  :root { --tinta:#1a1a1a; --suave:#6b6b6b; --linea:#dcd9d4; --caja:#faf9f7;
          --acento:#8a5a00; --fondo:#ffffff; }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) { --tinta:#e9e7e3; --suave:#a39e97;
      --linea:#383838; --caja:#1d1d1d; --acento:#e0a948; --fondo:#131313; } }
  :root[data-theme="dark"] { --tinta:#e9e7e3; --suave:#a39e97;
    --linea:#383838; --caja:#1d1d1d; --acento:#e0a948; --fondo:#131313; }
  * { box-sizing:border-box }
  body { background:var(--fondo); color:var(--tinta); margin:0;
    font:17px/1.65 Georgia,"Times New Roman",serif;
    -webkit-text-size-adjust:100%; }
  .env { max-width:58rem; margin:0 auto; padding:2.5rem 16px 5rem }
  h1 { font:600 1.75rem/1.25 system-ui,sans-serif; margin:0 0 .4rem }
  .sub { color:var(--suave); margin:0 0 2.5rem; font:.95rem system-ui,sans-serif }
  .instr { background:var(--caja); border:1px solid var(--linea);
    border-radius:8px; padding:1.4rem 1.5rem; margin-bottom:3rem }
  .instr h2 { font:600 1.1rem system-ui,sans-serif; margin:0 0 .8rem }
  .instr p, .instr li { font-size:.97rem }
  .instr ol, .instr ul { margin:.5rem 0 1rem 1.3rem; padding:0 }
  .instr li { margin:.3rem 0 }
  .escala { list-style:none; margin-left:0 }
  .escala li { font:.93rem/1.5 ui-monospace,Menlo,Consolas,monospace;
    padding:.3rem .6rem; border-left:3px solid var(--linea) }
  .escala li.frontera { border-left-color:var(--acento) }
  .ojo { border-left:3px solid var(--acento); padding-left:1rem;
    margin:1.2rem 0 0 }
  article { border-top:2px solid var(--linea); padding:1.8rem 0 1.4rem;
    page-break-inside:avoid }
  article h2 { font:600 1.1rem system-ui,sans-serif; margin:0 0 .9rem }
  .n { color:var(--suave); font-weight:400; font-size:.82rem; margin-right:.5rem }
  .tag { font:.68rem system-ui,sans-serif; text-transform:uppercase;
    letter-spacing:.09em; color:var(--suave); border:1px solid var(--linea);
    border-radius:3px; padding:.18rem .5rem; margin-left:.5rem }
  h3 { font:600 .72rem system-ui,sans-serif; text-transform:uppercase;
    letter-spacing:.08em; color:var(--suave); margin:1.2rem 0 .4rem }
  h3 em { text-transform:none; letter-spacing:0; font-weight:400 }
  .caso { margin:0 }
  .dos { display:grid; grid-template-columns:1fr 1fr; gap:1.5rem }
  @media (max-width:46rem) { .dos { grid-template-columns:1fr } }
  pre { background:var(--caja); border:1px solid var(--linea);
    border-radius:6px; padding:.85rem .95rem; margin:0; white-space:pre-wrap;
    overflow-wrap:anywhere;
    font:13.5px/1.6 ui-monospace,Menlo,Consolas,monospace }
  pre.sis { border-left:3px solid var(--acento) }
  .resp { margin:1.5rem 0 0; font:.92rem system-ui,sans-serif }
  .hueco { display:inline-block; border-bottom:1.5px solid var(--tinta);
    min-width:3.5rem; margin:0 .3rem }
  .hueco.ancho { min-width:14rem }
  code { font:.9em ui-monospace,Menlo,Consolas,monospace }
  @media print { body { background:#fff; color:#000 }
    .env { max-width:none; padding:0 } article { border-top-color:#999 } }
"""


RUTA_SIM = RAIZ / "data" / "validacion_juez_simulacion.json"
"""La simulacion va a OTRO archivo, y eso es lo que la hace segura.

`reporte.juez_vs_humano()` lee `validacion_juez.json` --- el de verdad --- y
mientras no exista, §7.1 dice que la validacion humana falta. Si la
simulacion escribiera ahi, el reporte publicaria un acuerdo con un abogado
que nadie ha consultado, en la seccion que el propio documento llama el
resultado mas importante. Dos nombres distintos es lo que impide que un
despiste lo convierta en un dato."""


def simular() -> int:
    """Corre la tuberia con notas DERIVADAS DE LA RUBRICA, no de una persona.

    PARA QUE SIRVE, Y PARA QUE NO

    SIRVE para comprobar que la tuberia entera funciona antes de gastar el
    tiempo de un abogado: que el formulario se lee, que los ids se emparejan,
    que `harness.acuerdo_entre_jueces` acepta el par y que el artefacto sale
    completo. Eso es fontaneria y se puede probar sin nadie.

    NO SIRVE como validacion, y no por prudencia sino por aritmetica: las
    notas se derivan de la MISMA rubrica que aplica el juez, asi que el
    acuerdo sale alto por construccion. Mide que dos aplicaciones de la misma
    regla coinciden --- que es una tautologia --- y no si el criterio del juez
    se parece al de un abogado, que es lo unico que M2-1b pregunta.

    COMO SE CONSTRUYEN LAS NOTAS

    La rubrica define la frontera entre 2 y 3 como «mecanismo correcto», y eso
    es comprobable contra el gold. Asi que:

        mecanismo equivocado -> 1 o 2
        mecanismo correcto   -> 3, 4 o 5

    y dentro de cada banda se reparte con semilla fija, para que la
    simulacion sea reproducible y no una tirada distinta cada vez.
    """
    import csv as _csv
    import random as _random

    filas_j = {f["id"]: f for f in _filas_del_juez()}
    ruta = next((p for p in (SALIDA.with_suffix(".xlsx"),
                             SALIDA.with_suffix(".csv")) if p.exists()), None)
    if ruta is None:
        raise SystemExit(f"falta {SALIDA.name}.xlsx/.csv: corre el script sin "
                         "argumentos para escribirlo primero")
    leido = formularios.leer(ruta, COLUMNAS_PERSONA)

    rnd = _random.Random(corridas.SEMILLA)
    pares = []
    for f in leido["filas"]:
        fj = filas_j.get(f["id"])
        if not fj:
            continue
        acierta = str(fj.get("acierto", "")).strip().lower() == "true"
        nota_sim = rnd.choice([3, 4, 5]) if acierta else rnd.choice([1, 2])
        try:
            n_ju = int(float(str(fj.get("nota_juez", "")).strip()))
        except ValueError:
            n_ju = None
        pares.append({"id": f["id"], "nota_juez": n_ju,
                      "nota_simulada": nota_sim,
                      "mecanismo_correcto": acierta})

    ac = harness.acuerdo_entre_jueces(
        [{"nota": p["nota_juez"]} for p in pares],
        [{"nota": p["nota_simulada"]} for p in pares],
        juez.MODELO, "simulacion derivada de la rubrica")

    out = {
        "ESTO_NO_ES_UNA_VALIDACION": (
            "Las notas de la columna B las DERIVO un script de la misma "
            "rubrica que aplica el juez, a partir de si el mecanismo coincide "
            "con el gold. NINGUNA persona las puso, y por tanto esto no mide "
            "acuerdo con un criterio independiente. M2-1b sigue ABIERTO."),
        "por_que_no_mide_nada": (
            "Lo circular es el ORDEN, no el nivel. Las dos columnas se "
            "derivan de la misma senal --- si el mecanismo coincide con el "
            "gold --- asi que la Spearman sale alta por construccion y no "
            "dice nada. El `acuerdo_exacto` y la `kappa_aprueba`, en cambio, "
            "salen BAJOS, porque dentro de cada banda la nota simulada se "
            "sortea y no imita como el juez reparte el 3, el 4 y el 5. Una "
            "primera version de esta nota decia que el acuerdo saldria alto "
            "en bloque: la propia simulacion lo desmintio y queda corregido "
            "aqui en vez de borrado."),
        "para_que_sirve": (
            "para comprobar que la tuberia funciona antes de gastar el tiempo "
            "de una persona: que el formulario se lee, que los ids se "
            "emparejan, que `acuerdo_entre_jueces` acepta el par y que el "
            "artefacto sale completo"),
        "simulacion": True,
        "semilla": corridas.SEMILLA,
        "acuerdo": ac,
        "pares": pares,
    }
    RUTA_SIM.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8", newline="\n")

    print("=" * 76)
    print("  SIMULACION · NO es la validacion humana (M2-1b sigue abierto)")
    print("=" * 76)
    print(f"  n                 : {ac['n']}")
    print(f"  media juez        : {ac.get('media_a')}")
    print(f"  media simulada    : {ac.get('media_b')}")
    print(f"  acuerdo exacto    : {ac.get('acuerdo_exacto')}")
    print(f"  acuerdo a 1 punto : {ac.get('acuerdo_a_un_punto')}")
    print(f"  kappa (nota >= 4) : {ac.get('kappa_aprueba')}")
    print(f"  Spearman          : {ac.get('corr_spearman')}")
    print()
    print("  LA TUBERIA FUNCIONA: el formulario se lee, los 25 ids se")
    print("  emparejan con las notas del juez y el acuerdo se calcula con la")
    print("  misma funcion que el acuerdo entre modelos.")
    print()
    print("  Y ESTAS CIFRAS NO VALEN COMO VALIDACION. Lo circular es el")
    print("  ORDEN: las dos columnas salen de la misma senal (si el mecanismo")
    print("  coincide con el gold), asi que la Spearman es alta por")
    print("  construccion. El acuerdo exacto sale bajo porque dentro de cada")
    print("  banda la nota se sortea. `REPORTE.md` §7.1 NO las lee: sigue")
    print("  leyendo")
    print(f"  `{RUTA_OUT.name}`, que no existe hasta que una persona rellene")
    print("  el formulario.")
    print()
    print(f"  escrito: data/{RUTA_SIM.name}")
    print("=" * 76)
    return 0


def html() -> int:
    """El formulario como documento LEGIBLE, un caso por bloque.

    POR QUE HACE FALTA ADEMAS DEL .xlsx

    El .xlsx es una tabla de ocho columnas en la que tres --- el caso, la
    referencia y la respuesta --- son textos largos. Con `caso` a 20 de ancho
    y las otras dos a 70, la columna `nota` queda a unos 160 caracteres a la
    derecha: **fuera de la pantalla**. Quien rellena tiene que leer tres
    textos largos y luego desplazarse para escribir un numero, veinticinco
    veces.

    Eso no es un detalle de presentacion. Lo que se mide aqui es el criterio
    de una persona, y un formulario incomodo no mide peor el criterio: mide
    la paciencia con Excel. La primera version de este formulario volvio con
    notas que no podian ser juicios --- 4 y 5 en ocho casos cuyo mecanismo
    esta objetivamente mal contra el gold --- y la hoja ilegible es parte de
    la explicacion.

    Este documento pone un caso por bloque, en orden de lectura, con el hueco
    de la nota al final de cada uno. Se abre en cualquier navegador y se
    imprime.

    NO sustituye al .xlsx: aquel es el que `--leer` vuelve a leer. Este es
    por donde se LEE, y las notas se pasan al .xlsx o se dictan.
    """
    import html as _h
    filas_j = _filas_del_juez()
    ids = {f["id"] for f in filas_j}
    ejemplos, nombre_eval = _eval_set_de(ids)
    gold = {e["id"]: e for e in ejemplos}
    respuestas = _respuestas()
    sel, _plan = _muestra(filas_j)

    def esc(t):
        return _h.escape(str(t or "")).replace("\n", "<br>")

    bloques = []
    for k, f in enumerate(sel, 1):
        e = gold[f["id"]]
        bloques.append(
            "<article>\n"
            f'  <h2><span class="n">{k} de {len(sel)}</span>{esc(f["id"])}'
            f'<span class="tag">{esc(f.get("tipo"))}</span></h2>\n'
            "  <h3>El caso</h3>\n"
            f'  <p class="caso">{esc(e["relato"])}</p>\n'
            '  <div class="dos">\n'
            "    <div><h3>Respuesta de referencia "
            "<em>(la que el equipo considera correcta)</em></h3>\n"
            f"      <pre>{esc(schema.render_salida(e))}</pre></div>\n"
            "    <div><h3>Respuesta del sistema "
            "<em>(esto es lo que se califica)</em></h3>\n"
            f'      <pre class="sis">{esc(respuestas[f["id"]])}</pre></div>\n'
            "  </div>\n"
            '  <p class="resp"><strong>Nota (1 a 5):</strong>'
            '<span class="hueco">&nbsp;</span>'
            "&nbsp;&nbsp;Comentario, solo si la nota le parece discutible:"
            '<span class="hueco ancho">&nbsp;</span></p>\n'
            "</article>")

    esc_items = []
    for l in _escala()[1:]:
        clase = ' class="frontera"' if l.strip().startswith(("3 =", "2 =")) else ""
        esc_items.append(f"<li{clase}>{esc(l)}</li>")

    doc = (
        "<!doctype html>\n<html lang=\"es\"><head><meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>Validación del juez · {len(sel)} casos</title>\n"
        "<style>" + CSS + "</style></head><body><div class=\"env\">\n"
        "<h1>Validación del juez automático</h1>\n"
        f'<p class="sub">Proyecto Amparo · {len(sel)} casos · unos '
        f'{max(20, len(sel) * 2)} minutos · eval set <code>{nombre_eval}</code></p>\n'
        '<div class="instr">\n<h2>Qué hay que hacer</h2>\n<ol>\n'
        "<li>Lea <strong>el caso</strong>.</li>\n"
        "<li>Lea la <strong>respuesta de referencia</strong>: es la que el "
        "equipo considera correcta.</li>\n"
        "<li>Lea la <strong>respuesta del sistema</strong>. "
        "<strong>Esto es lo que se califica.</strong></li>\n"
        "<li>Escriba una <strong>nota de 1 a 5</strong>:</li>\n</ol>\n"
        '<ul class="escala">' + "".join(esc_items) + "</ul>\n"
        "<p>La frontera que más importa está <strong>entre el 2 y el 3</strong>: "
        "del 3 hacia arriba el mecanismo es correcto; del 2 hacia abajo está "
        "equivocado. Esa es la decisión principal, el resto es afinar.</p>\n"
        "<p>Dos reglas, las mismas que se le dieron al modelo:</p>\n<ul>\n"
        "<li>La extensión <strong>no</strong> es calidad. Una respuesta corta "
        "y correcta vale más que una larga y equivocada.</li>\n"
        "<li>Si cita una norma que no viene al caso, <strong>baje</strong> la "
        "nota.</li>\n</ul>\n"
        '<p class="ojo">Algunos casos son de <strong>abstención</strong> (los '
        "que empiezan por <code>AB</code>). Ahí lo correcto es <em>no</em> dar "
        "un mecanismo: la respuesta debida es «no determinable». Si el sistema "
        "lo dice, acierta; si fuerza una vía, se equivoca.</p>\n"
        '<p class="ojo">La nota que puso el modelo <strong>no aparece '
        "aquí</strong>, a propósito: verla anclaría la suya y el acuerdo que "
        "midiéramos después no significaría nada.</p>\n</div>\n"
        + "\n".join(bloques) +
        '\n<article><h3>Cuando termine</h3>\n'
        f"<p>Devuelva las {len(sel)} notas en orden. Se comparan con las del "
        "modelo: si coinciden, sus notas se pueden reportar; si no, lo que se "
        "publica es que <em>no</em> se pueden reportar.</p></article>\n"
        "</div></body></html>\n")

    ruta = SALIDA.with_suffix(".html")
    ruta.write_text(doc, encoding="utf-8", newline="\n")
    print("=" * 76)
    print("  VALIDACION DEL JUEZ · documento legible")
    print("=" * 76)
    print(f"  escrito: data/{ruta.name}  ·  {len(sel)} casos, uno por bloque")
    print(f"  tiempo estimado para quien lo rellena: ~{max(20, len(sel)*2)} min")
    print()
    print("  Se abre en cualquier navegador y se puede imprimir. Es por donde")
    print("  se LEE; el .xlsx sigue siendo el que `--leer` vuelve a leer.")
    print()
    print("  ids en orden:")
    print("   ", ", ".join(f["id"] for f in sel))
    print("=" * 76)
    return 0


def main() -> int:
    # `--por-nota N` baja el tamano de la muestra. Un formulario de 10 casos
    # que SE RELLENA vale mas que uno de 25 que no, y el coste --- un n mas
    # pequeno, o sea un intervalo mas ancho --- queda en el artefacto.
    global N_POR_NOTA
    if "--por-nota" in sys.argv:
        N_POR_NOTA = int(sys.argv[sys.argv.index("--por-nota") + 1])
    if "--leer" in sys.argv:
        return leer()
    if "--simular" in sys.argv:
        return simular()
    if "--html" in sys.argv:
        return html()
    return escribir()


if __name__ == "__main__":
    raise SystemExit(main())
