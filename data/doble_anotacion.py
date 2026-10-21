"""
Kit de doble anotacion (ROADMAP #4).

El problema que resuelve. Las etiquetas del eval set tienen UNA sola fuente.
El motor de reglas verifica que sean CONSISTENTES con el arbol del art. 6
(ROADMAP #1, 63/63), pero consistencia no es fiabilidad: si quien codifico los
hechos leyo mal un relato, el motor confirma el error sin pestanear. La kappa
que ya se reporta (`juez_kappa_vs_dominio`) compara al juez automatico contra
las metricas de dominio, no a dos personas.

Esto mide lo que falta: cuanto coinciden DOS personas leyendo los mismos
relatos sin verse las etiquetas.

Dos modos:

    python -I data/doble_anotacion.py --preparar
        Escoge 10 casos estratificados (semilla 42, reproducible) y escribe
        data/anotacion_2.csv con SOLO el relato. Sin etiqueta, sin razon, sin
        categoria: si el anotador ve el gold, la medicion no vale nada.

    python -I data/doble_anotacion.py --medir --anotador persona-externa
        Lee el csv diligenciado, calcula la kappa de Cohen contra el gold y
        lista los desacuerdos caso por caso.

Un desacuerdo no significa que el gold este mal: significa que el caso es
discutible, y eso es informacion sobre el eval set que hoy no se tiene.
"""
from __future__ import annotations
import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# `src/harness.py` importa `metricas` plano, como lo hacen los notebooks, asi
# que src/ tiene que estar en el path y no solo la raiz.
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "src"))
# `-I` no pone el directorio del script en sys.path, asi que el modulo
# vecino se declara igual que los de `src/`.
sys.path.insert(0, str(RAIZ / "data"))

import formularios  # noqa: E402
from harness import cohen_kappa  # noqa: E402
from reglas import Hechos, estrato_verificacion  # noqa: E402

# Se anota sobre v3, no sobre v2: tiene 36 casos `derivado` frente a 15,
# asi que permite la cuota de 30 sin repetir. v3 CONTIENE a v2 byte a
# byte (lo fija `t_superconjunto`), asi que los casos de la anotacion
# anterior siguen siendo los mismos casos.
RUTA_EVAL = RAIZ / "data" / "eval_set_v3.json"
# CADA ANOTADOR TIENE SU ARCHIVO, Y ESO NO ES BUROCRACIA.
#
# Con un solo archivo, preparar el formulario para una segunda persona exige
# borrar o mover el de la primera --- y la guarda que protege su trabajo es
# justo la que impide generarlo. Peor: si se saltara la guarda, la segunda
# persona abriria un formulario CON LAS RESPUESTAS DE LA PRIMERA delante, que
# destruye la independencia que esta medicion existe para conseguir.
#
# Con un archivo por anotador no hay nada que mover, nada que se pueda
# sobreescribir y nada que se pueda ver por error.
#
# `anotacion_2.*` se conserva como nombre historico: es donde esta la primera
# anotacion, hecha antes de este cambio, y renombrarsela a alguien por detras
# seria peor que admitir la excepcion.
HISTORICO = "anotacion_2"


def rutas(anotador: str) -> tuple:  # noqa: D401
    """(xlsx, csv) de ESE anotador. Sin adivinar de quien es un archivo.

    EL FALLBACK ANTERIOR FABRICABA VALIDACION EXTERNA. ESTE ES EL CASO.

    Caia al nombre historico `anotacion_2.*` cuando el anotador no tenia
    archivo propio. Consecuencia medida: con el formulario de la persona
    externa todavia sin colocar, `--medir --anotador persona-externa`
    encontraba `anotacion_2.xlsx` --- la anotacion del PROPIO equipo --- y
    habria publicado un artefacto con `_anotador: persona-externa` e
    `independiente: True` sobre las respuestas de quien escribio el gold.

    Es el peor fallo posible en este proyecto: no produce una cifra mala, que
    se nota, sino la cifra que mas se desea con la etiqueta que la vuelve
    falsa. Y nada en la salida lo delataria.

    Ahora no se adivina de quien es un archivo. El historico solo se acepta
    para el anotador que el artefacto ya existente le atribuye --- una
    atribucion establecida, no supuesta --- y para nadie mas.
    """
    base = RAIZ / "data" / f"anotacion_{anotador}"
    x, c = base.with_suffix(".xlsx"), base.with_suffix(".csv")
    if x.exists() or c.exists():
        return x, c
    vx = RAIZ / "data" / f"{HISTORICO}.xlsx"
    vc = RAIZ / "data" / f"{HISTORICO}.csv"
    # Y el historico NO se atribuye a nadie por descarte. Quien quiera
    # medirlo pasa `--archivo data/anotacion_2.xlsx` y asi queda dicho de
    # donde salio. Un archivo sin dueno declarado no tiene dueno.
    del vx, vc
    return x, c


RUTA_CSV = RAIZ / "data" / f"{HISTORICO}.csv"
RUTA_XLSX = RAIZ / "data" / f"{HISTORICO}.xlsx"
RUTA_OUT = RAIZ / "data" / "acuerdo_anotadores.json"
"""El ultimo medido. El que vale para citar es el de cada anotador.

UN ARTEFACTO POR ANOTADOR, Y NO ES REDUNDANCIA.

Con un solo archivo, medir la anotacion externa BORRO la del equipo: la kappa
de 0.8056 que ROADMAP3 cita dejo de existir en el momento de medir la de
0.9014. Las dos son resultados distintos sobre preguntas distintas --- una mide
consistencia de la rubrica, la otra acuerdo entre anotadores --- y la segunda
no sustituye a la primera, la complementa.
"""


def ruta_out(anotador: str):
    return RAIZ / "data" / f"acuerdo_anotadores_{anotador}.json"

N_MUESTRA = 30          # total; el reparto por estrato esta en `muestra`
COLUMNAS_PERSONA = ("mecanismo", "procede", "notas")
"""Lo que rellena quien anota. `notas` entra a proposito: alguien que solo
haya escrito dudas ya tiene trabajo que no se puede sobreescribir."""
SEMILLA = 42

VOCABULARIO = ("tutela", "accion_popular", "accion_cumplimiento",
               "habeas_corpus", "via_ordinaria", "no_determinable")

def normalizar_convencion(mecanismo: str, procede: bool) -> tuple[str, bool]:
    """Aplica las DOS reglas de codificacion que el formulario enuncia.

    POR QUE ESTO NO ES MAQUILLAR LA KAPPA

    La kappa bruta es la que se reporta. Esta segunda cifra existe porque sin
    ella la bruta no se puede interpretar: mide a la vez dos cosas distintas
    --- si dos juristas leen el mismo caso igual, y si quien anota siguio una
    regla de codificacion --- y solo la primera dice algo del eval set.

    Lo que la hace legitima, y lo que habria que exigirle a cualquier ajuste
    de este tipo:

      - las dos reglas estan ESCRITAS EN EL FORMULARIO que recibio quien anoto
        (`INSTRUCCIONES`, el bloque "QUE SIGNIFICA `mecanismo`"), no se
        inventan despues de ver los numeros;
      - la transformacion es MECANICA: no decide quien tiene razon en derecho,
        reescribe una codificacion en la que el formulario pedia otra;
      - es CIEGA al gold. Se aplica a las 30 filas antes de comparar, no a los
        desacuerdos. Si subiera la kappa solo porque corrige en la direccion
        del gold, seria circular; aqui las filas que ya cumplian la convencion
        no se tocan y las que no, se tocan sin mirar con que se comparan.

    Las dos reglas, literales del formulario:

      1. «Si la persona pide tutela y usted cree que la tutela NO procede
         porque el asunto corresponde a la justicia ordinaria, ponga
         `via_ordinaria` --- NO ponga `tutela` con procede=false.»
      2. «Si mecanismo no es `tutela`, procede va en false.»

    Y lo que la regla 1 NO hace: `tutela` con procede=false se conserva cuando
    el gold tambien dice `tutela` ---el caso que el formulario reserva: la
    tutela es la via y aun asi no procede por una causal propia---. Esa
    comprobacion no se puede hacer aqui sin mirar el gold, asi que se hace
    fuera, en `medir`, y por eso esta funcion devuelve la lectura literal de la
    convencion y no la definitiva.
    """
    if mecanismo == "tutela" and not procede:
        # Regla 1. La convencion manda la via alternativa, no `tutela/false`.
        mecanismo = "via_ordinaria"
    if mecanismo != "tutela":
        # Regla 2.
        procede = False
    return mecanismo, procede


INSTRUCCIONES = [
    "# DOBLE ANOTACION - eval set de agenteAmparo",
    "#",
    "# Lea cada relato y diligencie DOS columnas:",
    "#",
    "#   mecanismo : uno de -> " + " | ".join(VOCABULARIO),
    "#   procede   : true si procede la TUTELA, false si no.",
    "#               Si mecanismo no es `tutela`, procede va en false.",
    "#               Si mecanismo es `no_determinable`, procede va en false.",
    "#",
    "# QUE SIGNIFICA `mecanismo` --- LEA ESTO, ES LA UNICA PARTE AMBIGUA",
    "#",
    "# Ponga la VIA QUE DE VERDAD CORRESPONDE al caso, no la que la persona",
    "# invoca o menciona. Son cosas distintas y se confunden facil:",
    "#",
    "#   Si la persona pide tutela y usted cree que la tutela NO procede",
    "#   porque el asunto corresponde a la justicia ordinaria, ponga",
    "#   `via_ordinaria` --- NO ponga `tutela` con procede=false.",
    "#",
    "#   `tutela` con procede=false se reserva para cuando la tutela ES la",
    "#   via correcta del caso y aun asi no procede por una causal propia",
    "#   (por ejemplo, dano ya consumado sobre un derecho fundamental).",
    "#",
    "# Por que se aclara: medido con la primera anotacion, los DOS unicos",
    "# desacuerdos de 14 venian de aqui y no de una diferencia juridica --- en",
    "# los dos, la nota del anotador razonaba lo mismo que la etiqueta. Un",
    "# desacuerdo que mide la redaccion del formulario, y no el criterio de",
    "# quien lee, es un desacuerdo que no sirve para nada.",
    "#",
    "# `no_determinable` es para cuando el relato NO permite decidir: faltan",
    "# hechos, se contradice, es una consulta academica o comercial, o pide un",
    "# pronostico. No es una opcion de descarte: usela cuando corresponda.",
    "#",
    "# La columna `notas` es opcional, para dejar por que dudo.",
    "#",
    "# NO consulte el eval set mientras anota. El valor de esta medicion",
    "# depende de que las dos lecturas sean independientes.",
    "#",
]


def corta(p) -> str:
    """La ruta relativa al proyecto, o la absoluta si cae fuera.

    `Path.relative_to` LANZA cuando la ruta no esta dentro, y aqui solo se usa
    para imprimir bonito. Reventar en un `print` --- despues de haber escrito
    el archivo, que es lo que importa --- es el peor sitio posible para fallar:
    parece que la operacion fallo cuando habia terminado bien. Paso dos veces
    al apuntar estos scripts a un directorio temporal.
    """
    try:
        return str(Path(p).relative_to(RAIZ))
    except ValueError:
        return str(p)


def estrato(caso: dict) -> str:
    """`plano`, `derivado` o `juicio`. Lo calcula src.reglas, no este script.

    Es lo que mide la fiabilidad, y el primer muestreo no lo tenia en cuenta:
    estratificaba por mecanismo, que no es donde esta el riesgo.
    """
    h = caso.get("hechos")
    if not h or caso["mecanismo"] is None:
        return "plano"
    return estrato_verificacion(Hechos(**h))[0]


def muestra(casos: list[dict]) -> list[dict]:
    """30 casos repartidos por estrato de verificacion, no proporcional.

    Sobrerrepresenta los estratos dificiles a proposito, porque el objetivo no
    es estimar una kappa global representativa sino responder una pregunta
    concreta: **el desacuerdo se concentra en los casos donde hubo
    discrecion?** Una muestra proporcional de 30 sobre `eval_set_v3` daria
    ~19 `plano`, ~10 `derivado` y 1 `juicio`, y con eso la pregunta no se
    puede responder.

    `medir` reporta la kappa global y la de cada estrato por separado. La
    global queda sesgada A LA BAJA respecto de la poblacion, y eso hay que
    leerlo asi, no como la fiabilidad del eval set completo.

    LA CIFRA DE POBLACION QUE ESTO DECIA ERA FALSA. Decia «los de juicio son
    19 de 63». Medido sobre los tres eval sets, `juicio` son **3** en todas
    las versiones ---v1 n=46, v2 n=69, v3 n=109--- y el campo guardado
    `estrato_verificacion` coincide con el calculado en las 178 filas. El 19
    no describe estos datos, y `nota_estratos` lo publicaba en el artefacto
    que cita el informe. Ahora el reparto se calcula y se publica medido, que
    es lo que impide que vuelva a pasar.

    Dentro de cada estrato se cubre el maximo de mecanismos distintos, para que
    la muestra no se vaya toda a `tutela`, que es el 39% del eval set.
    """
    rnd = random.Random(SEMILLA)
    por_estrato: dict[str, list[dict]] = defaultdict(list)
    for c in casos:
        por_estrato[estrato(c)].append(c)

    # Cuota por estrato, no proporcional: TODOS los de `juicio`, porque son
    # los unicos cuya ponderacion sigue afirmada a pelo; varios `derivado`
    # para comprobar que la lectura de los elementos del test coincide; y unos
    # `plano` de control --- si ahi hay desacuerdo el problema es de lectura de
    # los relatos, que es mas grave.
    # LAS CUOTAS SUBEN DE 14 A 30, Y EL ESTRATO `juicio` NO PUEDE SUBIR.
    #
    # La primera anotacion independiente salio con n=14: kappa 0.9014 en
    # mecanismo y 1.0 en procedencia, que es fuerte, pero con un intervalo
    # ancho. Subir `derivado` y `plano` lo estrecha.
    #
    # `juicio` se queda en 3 y su kappa seguira saliendo `indefinido`, y eso
    # NO es un defecto del muestreo: el eval set entero tiene **3 casos de
    # juicio** --- lo mismo en v2 que en v3 ---, asi que la cuota ya los toma
    # todos. Ampliar ese estrato exigiria tocar el eval set, que es el puente
    # de comparacion congelado byte a byte de doce corridas. Es un limite de
    # la POBLACION y se declara; no se disimula muestreando distinto.
    cuota = {"juicio": len(por_estrato["juicio"]), "derivado": 12, "plano": 15}

    elegidos: list[dict] = []
    for est in ("juicio", "derivado", "plano"):
        pool = por_estrato[est]
        por_mec: dict[str, list[dict]] = defaultdict(list)
        for c in pool:
            por_mec[c["mecanismo"] or "abstencion"].append(c)
        sel: list[dict] = []
        for mec in sorted(por_mec):                 # cubre el maximo de clases
            sel.append(rnd.choice(sorted(por_mec[mec], key=lambda x: x["id"])))
        resto = sorted((c for c in pool if c not in sel), key=lambda x: x["id"])
        rnd.shuffle(resto)
        sel += resto[:max(0, cuota[est] - len(sel))]
        elegidos += sel[:cuota[est]]

    return sorted(elegidos, key=lambda c: c["id"])


def preparar(anotador: str = HISTORICO) -> int:
    global RUTA_XLSX, RUTA_CSV
    if anotador != HISTORICO:
        # Para un anotador nuevo se escribe SU archivo, en blanco, sin tocar
        # el de nadie mas.
        RUTA_XLSX = RAIZ / "data" / f"anotacion_{anotador}.xlsx"
        RUTA_CSV = RAIZ / "data" / f"anotacion_{anotador}.csv"
    casos = json.loads(RUTA_EVAL.read_text(encoding="utf-8"))["ejemplos"]
    sel = muestra(casos)

    # LA GUARDA MIRA LOS DOS ARCHIVOS Y LAS TRES COLUMNAS.
    #
    # Dos correcciones, las dos por lo mismo: el coste de equivocarse aqui es
    # el trabajo entero de una persona.
    #
    #   · Miraba solo `mecanismo`. Quien empiece dejando dudas en `notas`, o
    #     rellenando `procede` primero, tenia un formulario que `--preparar`
    #     borraba sin avisar.
    #   · Miraba solo el CSV. Pero lo que se rellena es el XLSX, y en cuanto
    #     el CSV desaparece --- Excel lo reemplaza al guardar, o se borra a
    #     mano --- la guarda daba paso y `--preparar` machacaba el xlsx con
    #     las respuestas dentro. Medido: 14 respuestas a un `--preparar` de
    #     distancia.
    for ruta in (RUTA_XLSX, RUTA_CSV):
        if not ruta.exists():
            continue
        previo = formularios.leer(ruta, COLUMNAS_PERSONA)
        if previo["diligenciadas"]:
            print(f"NO se sobreescribe: {ruta.name} ya tiene "
                  f"{previo['diligenciadas']} fila(s) con algo escrito.")
            print("Si quiere empezar de nuevo, muevalo o borrelo a mano.")
            return 1

    # EL CSV VA CON BOM A PROPOSITO.
    #
    # Sin BOM, Excel en un Windows en espanol lo decodifica con la pagina 1252
    # y TODOS los acentos del relato salen como simbolos raros. El relato es
    # exactamente lo que hay que leer para poder anotar, asi que eso no es un
    # defecto cosmetico: deja el formulario inservible. Con BOM, Excel y
    # Google Sheets detectan UTF-8 solos, y `formularios.leer()` lo quita al
    # leer, asi que la ida y la vuelta funcionan.
    CABECERA = ["id", "relato", "mecanismo", "procede", "notas"]
    filas = [[c["id"], c["relato"], "", "", ""] for c in sel]
    with RUTA_CSV.open("w", encoding="utf-8-sig", newline="") as fh:
        for linea in INSTRUCCIONES:
            fh.write(linea + "\n")
        w = csv.writer(fh)
        w.writerow(CABECERA)
        w.writerows(filas)

    # Y un .xlsx, que es el unico que se abre con doble clic sin que Excel se
    # equivoque ni con la codificacion ni con el separador de columnas. El
    # desplegable de `mecanismo` evita que un valor mal escrito se cuente como
    # desacuerdo: la kappa no puede empeorar por un error de teclado.
    hay_xlsx = formularios.escribir_xlsx(
        RUTA_XLSX, INSTRUCCIONES, CABECERA, filas, COLUMNAS_PERSONA,
        opciones={"mecanismo": list(VOCABULARIO),
                  "procede": ["true", "false"]})

    print(f"escrito {corta(RUTA_CSV)} con {len(sel)} casos.")
    if hay_xlsx:
        print(f"escrito {corta(RUTA_XLSX)}   <-- RELLENA ESTE: "
              "se abre bien con doble clic")
    else:
        print("  (sin openpyxl no se escribio el .xlsx; usa el csv)")
    print("\npor estrato (lo que mide la fiabilidad):")
    for k, n in Counter(estrato(c) for c in sel).most_common():
        print(f"  {k:22s} {n}")
    print("\npor mecanismo:")
    for k, n in Counter(c["mecanismo"] or "abstencion" for c in sel).most_common():
        print(f"  {k:22s} {n}")
    print(f"\nids: {', '.join(c['id'] for c in sel)}")
    # Completo a proposito: `--medir` solo ya no corre, y una instruccion
    # impresa que falla al copiarla hace dudar de la herramienta.
    print("\nDiligencielo y despues, segun QUIEN lo diligencio:")
    print("  python -I data/doble_anotacion.py --medir "
          "--anotador persona-externa")
    print("     (persona ajena al proyecto: la unica que mide ACUERDO ENTRE "
          "ANOTADORES)")
    print("  python -I data/doble_anotacion.py --medir --anotador equipo")
    print("  python -I data/doble_anotacion.py --medir --anotador asistente")
    print("     (estas dos miden CONSISTENCIA de la rubrica, no acuerdo)")
    return 0


ANOTADORES = {
    "persona-externa": (True,
        "Persona que no participo en escribir el gold. Es la unica "
        "combinacion que mide ACUERDO ENTRE ANOTADORES."),
    # Segunda ranura independiente. Hace falta porque la guarda protege el
    # trabajo de `persona-externa` --- con razon --- y preparar un formulario
    # nuevo para otra persona no puede exigir borrar el de la primera. Cada
    # anotador tiene su archivo y `--medir` los lee por separado.
    "persona-externa-2": (True,
        "Segunda persona que no participo en escribir el gold. Independiente "
        "igual que `persona-externa`, y su anotacion se mide aparte: dos "
        "muestras independientes no se promedian, se comparan."),
    "equipo": (False,
        "Alguien del mismo equipo que escribio el gold: sabe de antemano que "
        "espera cada caso. Mide consistencia, no acuerdo."),
    "asistente": (False,
        "El mismo sistema que escribio el gold y las reglas. Mide si la "
        "RUBRICA es aplicable de forma reproducible, no si otra persona "
        "llegaria al mismo sitio. Es una pregunta mas debil, y hay que "
        "llamarla por su nombre."),
}
"""Quien anoto, y que puede concluirse de eso.

La kappa de acuerdo entre anotadores solo significa lo que su nombre dice si
los dos anotadores son independientes. Con el mismo equipo --- o el mismo
sistema --- a los dos lados, una kappa alta mide que la rubrica es clara, no
que el gold sea correcto.

Es el mismo cuidado que `por_fiabilidad_etiqueta` tiene con
`motor_de_reglas`: CONSISTENTE con el arbol del art. 6 no es lo mismo que
INDEPENDIENTE de el. Por eso el anotador es un campo obligatorio y no una
nota al pie: no se puede producir una kappa sin decir quien la genero.
"""


def _formulario(anotador: str = HISTORICO) -> "Path | None":
    """El formulario a medir: el .xlsx si existe, si no el .csv.

    Se prefiere el .xlsx porque es el que se le pide rellenar. Si estan los
    dos y solo uno tiene respuestas, se coge el que las tenga --- asi nadie
    pierde su trabajo por haber rellenado "el otro".
    """
    candidatos = [p for p in rutas(anotador) if p.exists()]
    if not candidatos:
        return None
    con_datos = [p for p in candidatos
                 if formularios.leer(p, COLUMNAS_PERSONA)["diligenciadas"]]
    return con_datos[0] if con_datos else candidatos[0]


def medir(anotador: str = "persona-externa", archivo: str = "") -> int:
    # `--archivo` existe para medir un formulario que esta en otro sitio ---
    # tipicamente recien descargado --- sin tener que copiarlo a ciegas a
    # `data/`. La ruta se pasa a proposito: asi queda dicho de donde salio en
    # vez de que el script lo deduzca.
    ruta = Path(archivo) if archivo else _formulario(anotador)
    if archivo and not ruta.exists():
        print(f"no existe {archivo}")
        return 1
    if ruta is None:
        x, c = rutas(anotador)
        print(f"no existe {x.name} ni {c.name}.")
        print(f"Corra primero: --preparar --anotador {anotador}")
        return 1
    print(f"formulario: {ruta.name}")

    # Via `formularios`, que tolera lo que Excel hace al guardar. Leerlo con
    # `encoding="utf-8"` a pelo moria con un CSV cp1252, y con uno con BOM
    # tomaba la primera linea de instrucciones como cabecera e informaba cero
    # filas diligenciadas sobre un formulario entero relleno.
    r = formularios.exigir(ruta, COLUMNAS_PERSONA)
    if not r["cabecera_valida"]:
        return 1
    filas = [f for f in r["filas"] if (f.get("mecanismo") or "").strip()]
    if not filas:
        print(f"{ruta.name} no tiene ninguna fila diligenciada.")
        return 1

    casos = {c["id"]: c
             for c in json.loads(RUTA_EVAL.read_text(encoding="utf-8"))["ejemplos"]}

    errores = []
    mec_a, mec_b, proc_a, proc_b, desacuerdos, est = [], [], [], [], [], []
    mec_bn, proc_bn = [], []      # la anotacion bajo la convencion
    for f in filas:
        cid = f["id"].strip()
        if cid not in casos:
            errores.append(f"{cid}: no existe en el eval set")
            continue
        m2 = f["mecanismo"].strip()
        if m2 not in VOCABULARIO:
            errores.append(f"{cid}: mecanismo '{m2}' fuera del vocabulario")
            continue
        p2 = f.get("procede", "").strip().lower()
        if p2 not in ("true", "false", "si", "no", "1", "0"):
            errores.append(f"{cid}: procede '{p2}' no es booleano")
            continue

        c = casos[cid]
        m1 = c["mecanismo"] or "no_determinable"
        p1 = bool(c["procede"])
        p2b = p2 in ("true", "si", "1")

        mec_a.append(m1); mec_b.append(m2)
        proc_a.append(p1); proc_b.append(p2b)
        est.append(estrato(c))

        # La misma anotacion leida bajo la convencion que el formulario enuncia.
        # Se aplica a TODAS las filas, antes de comparar con el gold, para que
        # el ajuste no pueda ir en la direccion del gold por construccion.
        m2n, p2n = normalizar_convencion(m2, p2b)
        if m1 == "tutela" and m2 == "tutela" and not p2b:
            # La excepcion que la funcion no puede ver: cuando el gold tambien
            # dice `tutela`, el `tutela/false` del anotador es precisamente el
            # caso que el formulario reserva y no hay nada que normalizar.
            m2n, p2n = m2, p2b
        mec_bn.append(m2n); proc_bn.append(p2n)

        if m1 != m2 or p1 != p2b:
            # DE QUE TIPO ES EL DESACUERDO. Sin esto, la lista mezcla a quien
            # leyo otro derecho con quien leyo lo mismo y lo escribio en otra
            # casilla, y la cifra no se puede interpretar.
            tipo = ("convencion" if (m1 == m2n and p1 == p2n) else "juridico")
            desacuerdos.append({
                "id": cid, "categoria": c.get("categoria"),
                "dificultad": c.get("dificultad"), "estrato": estrato(c),
                "tipo": tipo,
                "gold": {"mecanismo": m1, "procede": p1},
                "anotador_2": {"mecanismo": m2, "procede": p2b},
                "anotador_2_normalizado": {"mecanismo": m2n, "procede": p2n},
                "nota_anotador_2": f.get("notas", "").strip(),
                "relato": c["relato"],
            })

    if errores:
        print(f"{len(errores)} filas con problemas:\n")
        for e in errores:
            print(f"  - {e}")
        if not mec_a:
            return 1
        print()

    n = len(mec_a)
    k_mec = cohen_kappa(mec_a, mec_b)
    k_proc = cohen_kappa(proc_a, proc_b)
    acuerdo_mec = sum(x == y for x, y in zip(mec_a, mec_b)) / n
    acuerdo_proc = sum(x == y for x, y in zip(proc_a, proc_b)) / n

    # Por estrato: es la pregunta que de verdad importa. Si el desacuerdo se
    # concentra en `juicio`, el eval set es fiable donde los hechos se leen y
    # discutible donde hubo que ponderar --- que es un resultado util y
    # esperable. Si tambien hay desacuerdo en `plano`, el problema es de
    # lectura de los relatos y es mas grave.
    por_estrato = {}
    for e in ("juicio", "derivado", "plano"):
        idx = [i for i, x in enumerate(est) if x == e]
        if not idx:
            continue
        ma = [mec_a[i] for i in idx]
        mb = [mec_b[i] for i in idx]
        k = cohen_kappa(ma, mb)
        por_estrato[e] = {
            "n": len(idx),
            "acuerdo_bruto": round(sum(x == y for x, y in zip(ma, mb)) / len(idx), 4),
            "kappa": round(k, 4) if k is not None else "indefinido",
            "desacuerdos": sum(x != y for x, y in zip(ma, mb)),
        }

    # El reparto real, de los datos, para que la nota no pueda mentir.
    from collections import Counter as _C
    poblacion = dict(_C(estrato(c) for c in casos.values()))
    reparto_muestra = " ".join(
        f"{k} {v}" for k, v in sorted(_C(est).items()))
    reparto_poblacion = " ".join(
        f"{k} {v}" for k, v in sorted(poblacion.items()))

    k_mec_n = cohen_kappa(mec_a, mec_bn)
    k_proc_n = cohen_kappa(proc_a, proc_bn)
    n_conv = sum(1 for d in desacuerdos if d["tipo"] == "convencion")
    n_jur = sum(1 for d in desacuerdos if d["tipo"] == "juridico")

    out = {
        "n_anotados": n,
        "acuerdo_bruto_mecanismo": round(acuerdo_mec, 4),
        "acuerdo_bruto_procede": round(acuerdo_proc, 4),
        "kappa_mecanismo": round(k_mec, 4) if k_mec is not None else "indefinido",
        "kappa_procede": round(k_proc, 4) if k_proc is not None else "indefinido",
        "por_estrato": por_estrato,
        # EL REPARTO DE LA POBLACION SE MIDE, NO SE ESCRIBE A MANO.
        #
        # Esta nota decia "en la poblacion los de `juicio` son 19 de 63". Es
        # falso: son 3, y lo han sido en las tres versiones del eval set. Una
        # cifra fija en un texto no se revisa cuando los datos cambian ---y
        # esta llego al artefacto que cita el informe---, asi que se calcula.
        "poblacion_por_estrato": poblacion,
        "nota_estratos":
            "la muestra sobrerrepresenta los estratos dificiles a proposito: "
            f"{reparto_muestra} frente a una poblacion de {reparto_poblacion}. "
            "La kappa global de aqui esta por tanto sesgada A LA BAJA respecto "
            "del eval set completo: no se debe reportar como la fiabilidad del "
            "eval set, sino leerse junto con la de cada estrato. `juicio` no "
            "se puede ampliar --- la cuota ya toma los 3 que existen ---.",
        "nota_kappa":
            "`indefinido` significa que alguno de los dos anotadores uso una "
            "sola categoria en la muestra. La kappa entonces vale 0.0 "
            "mecanicamente y no distingue acuerdo de desacuerdo: informarla "
            "seria inventar una medicion. Mismo criterio que harness.cohen_kappa.",
        "lectura":
            "la kappa aqui NO mide si el gold esta bien. Mide si el eval set es "
            "reproducible por otra persona. Un desacuerdo marca un caso "
            "discutible, que es informacion que hoy no se tiene.",
        "bajo_la_convencion_del_formulario": {
            "_que_es": (
                "la misma anotacion, releida con las dos reglas de codificacion "
                "que el formulario enuncia. La cifra que se reporta es la "
                "bruta; esta separa el desacuerdo juridico del incumplimiento "
                "de una regla de codificacion, que es lo unico que permite "
                "interpretar la bruta."),
            "_por_que_no_es_circular": (
                "la normalizacion se aplica a las 30 filas antes de comparar "
                "con el gold y las dos reglas estan escritas en el formulario "
                "que recibio quien anoto, no se eligieron viendo los numeros. "
                "Ver `normalizar_convencion`."),
            "acuerdo_bruto_mecanismo": round(
                sum(x == y for x, y in zip(mec_a, mec_bn)) / n, 4),
            "acuerdo_bruto_procede": round(
                sum(x == y for x, y in zip(proc_a, proc_bn)) / n, 4),
            "kappa_mecanismo": (round(k_mec_n, 4) if k_mec_n is not None
                                else "indefinido"),
            "kappa_procede": (round(k_proc_n, 4) if k_proc_n is not None
                              else "indefinido"),
            "desacuerdos_de_convencion": n_conv,
            "desacuerdos_juridicos": n_jur,
            "nota": (
                "que la aclaracion siga sin bastar es en si un resultado: el "
                "bloque \"QUE SIGNIFICA `mecanismo`\" se anadio al formulario "
                "DESPUES de que los 2 desacuerdos de la primera anotacion "
                f"(n=14) salieran de ahi, y con n=30 volvieron a salir {n_conv}. "
                "La distincion entre la via que corresponde y la via que se "
                "invoca no se comunica con una instruccion; habria que separar "
                "la pregunta en dos columnas."),
        },
        "desacuerdos": desacuerdos,
        "_anotador": anotador,
        "_independencia": {
            "independiente": ANOTADORES[anotador][0],
            "nota": ANOTADORES[anotador][1],
            "que_mide": ("acuerdo entre anotadores independientes"
                         if ANOTADORES[anotador][0] else
                         "consistencia de la rubrica --- NO acuerdo entre "
                         "anotadores"),
        },
    }
    # Los dos: el de este anotador, que es el que se cita, y el generico como
    # "el ultimo medido", para no romper a quien ya lo leia por ese nombre.
    ruta_out(anotador).write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    RUTA_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    print(f"n anotados: {n}\n")
    if not ANOTADORES[anotador][0]:
        print("=" * 70)
        print(f"  ANOTADOR: {anotador} --- NO INDEPENDIENTE")
        print(f"  {ANOTADORES[anotador][1]}")
        print("  Esta kappa NO es acuerdo entre anotadores: es la")
        print("  CONSISTENCIA de la rubrica entre dos pasadas.")
        print("=" * 70)
        print()
    print(f"  acuerdo bruto mecanismo : {acuerdo_mec:.1%}")
    print(f"  acuerdo bruto procede   : {acuerdo_proc:.1%}")
    print(f"  kappa mecanismo         : {out['kappa_mecanismo']}")
    print(f"  kappa procede           : {out['kappa_procede']}")
    if por_estrato:
        print("\n  por estrato (mecanismo):")
        for e, v in por_estrato.items():
            print(f"    {e:7s} n={v['n']:<3} acuerdo {v['acuerdo_bruto']:.0%}  "
                  f"kappa {v['kappa']}  desacuerdos {v['desacuerdos']}")
    cv = out["bajo_la_convencion_del_formulario"]
    print()
    print("  bajo la convencion que el formulario enuncia "
          f"({n_conv} de {len(desacuerdos)} desacuerdos la incumplian):")
    print(f"    acuerdo mecanismo       : {cv['acuerdo_bruto_mecanismo']:.1%}"
          f"      kappa : {cv['kappa_mecanismo']}")
    print(f"    acuerdo procede         : {cv['acuerdo_bruto_procede']:.1%}"
          f"      kappa : {cv['kappa_procede']}")
    print(f"    desacuerdos juridicos   : {n_jur}")
    if desacuerdos:
        print(f"\n{len(desacuerdos)} desacuerdos:\n")
        for d in desacuerdos:
            # SE IMPRIME EL CAMPO QUE DE VERDAD DIFIERE.
            #
            # La lista recoge desacuerdos de `mecanismo` O de `procede`
            # (`m1 != m2 or p1 != p2b`), y antes se imprimia solo el
            # mecanismo. Resultado medido: `E31` salia como desacuerdo con
            # `gold: habeas_corpus / anotador: habeas_corpus` --- dos valores
            # identicos --- porque lo que diferia era `procede`. Un desacuerdo
            # que se imprime sin el campo que lo causa no se puede
            # interpretar, y quien lo lea concluye que el informe esta roto.
            g, a = d["gold"], d["anotador_2"]
            difieren = [c for c in ("mecanismo", "procede") if g[c] != a[c]]
            print(f"  {d['id']} ({d['categoria']}, {d['dificultad']}) "
                  f"- difiere en {' y '.join(difieren)} "
                  f"[{d['tipo']}]")
            for c in ("mecanismo", "procede"):
                marca = "  <-- " if g[c] != a[c] else "      "
                print(f"    {c:<10} gold {str(g[c]):<22}"
                      f"anotador {str(a[c]):<22}{marca}")
            if d["nota_anotador_2"]:
                print(f"    nota       : {d['nota_anotador_2']}")
    else:
        print("\nsin desacuerdos.")
    print(f"\nescrito {corta(ruta_out(anotador))}")
    print(f"        y {corta(RUTA_OUT)} (el ultimo medido)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--preparar", action="store_true",
                   help="escribe el formulario ciego")
    g.add_argument("--medir", action="store_true",
                   help="lee el formulario y calcula la kappa")
    # Sin default a proposito: producir una kappa de acuerdo sin decir quien
    # anoto es justo lo que no puede pasar.
    ap.add_argument("--anotador", choices=sorted(ANOTADORES),
                    help="quien anoto el formulario. Obligatorio con --medir.")
    ap.add_argument("--archivo", default="",
                    help="ruta del formulario, si no esta en data/")
    a = ap.parse_args()
    if a.preparar:
        # Sin --anotador se prepara el historico, que es el comportamiento de
        # antes. Con --anotador se prepara el de esa persona, en blanco.
        return preparar(a.anotador or HISTORICO)
    if not a.anotador:
        ap.error("--medir exige --anotador: " + ", ".join(sorted(ANOTADORES))
                 + ". Una kappa de acuerdo sin saber quien anoto no se puede "
                   "interpretar.")
    return medir(a.anotador, a.archivo)


if __name__ == "__main__":
    raise SystemExit(main())
