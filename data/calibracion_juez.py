"""
Kit de calibracion humana del juez (ROADMAP #23).

EL HUECO QUE CIERRA

M2 reporta `juez_kappa_vs_dominio`, que compara al juez automatico contra las
METRICAS DE DOMINIO: si el juez aprueba, el mecanismo estaba bien? Eso mide
una cosa util pero no la que hace falta. El juez no esta ahi para detectar si
el mecanismo coincide con el gold --- para eso basta `acc_mecanismo`, que es
exacta y gratis. Esta ahi para calificar el RAZONAMIENTO, que es justo lo que
una metrica exacta no puede medir.

Asi que la pregunta pendiente es otra: **cuando el juez da un 4, una persona
tambien lo daria?** Nadie lo ha comprobado. Y con `kappa_vs_dominio = 0.258`
--- un acuerdo pobre --- lo unico que se puede decir hoy es que el juez no se
puede usar solo. Falta saber si el problema es que el juez califica mal o que
lo estamos comparando contra la cosa equivocada.

DOS MODOS

    python -I data/calibracion_juez.py --preparar
        Escoge 10 casos estratificados por la nota del juez (semilla 42) y
        escribe data/calibracion_1.csv con el relato, la referencia y la
        respuesta del sistema. **Sin la nota del juez**: si el humano la ve,
        la medicion no vale nada.

    python -I data/calibracion_juez.py --medir --anotador persona-externa
        Lee el csv diligenciado y compara humano contra juez: acuerdo exacto,
        acuerdo a un punto, kappa en la decision binaria y Spearman.

NECESITA UNA CORRIDA. Las respuestas del sistema salen de
`results/m1_predicciones.json` y las notas del juez de
`results/m2_scorecard_por_caso.csv`. Sin esos dos archivos el script dice que
falta correr M1 y M2, en vez de inventar nada.

La estratificacion por nota del juez es deliberada: una muestra aleatoria se
va entera a las notas centrales, y donde interesa saber si el juez acierta es
en los extremos --- los 5 que puede estar regalando y los 1 que puede estar
castigando de mas.
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
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "src"))
# `-I` no pone el directorio del script en sys.path, asi que el modulo
# vecino se declara igual que los de `src/`.
sys.path.insert(0, str(RAIZ / "data"))

import formularios                                # noqa: E402
import schema                                     # noqa: E402
from harness import acuerdo_entre_jueces          # noqa: E402

RUTA_CSV = RAIZ / "data" / "calibracion_1.csv"
RUTA_OUT = RAIZ / "data" / "calibracion_juez.json"
RUTA_PREDS = RAIZ / "results" / "m1_predicciones.json"
RUTA_NOTAS = RAIZ / "results" / "m2_scorecard_por_caso.csv"

N_MUESTRA = 10
SEMILLA = 42
COLUMNAS_PERSONA = ("nota_humana", "notas")
"""Lo que rellena quien califica."""

ESCALA = [
    "# CALIBRACION DEL JUEZ - agenteAmparo",
    "#",
    "# Califique la RESPUESTA DEL SISTEMA con un entero de 1 a 5, usando la",
    "# MISMA escala que usa el juez automatico. Califique SOLO la calidad del",
    "# razonamiento juridico, no la redaccion ni la extension:",
    "#",
    "#   5 = mecanismo correcto, razonamiento solido y fundamento pertinente",
    "#   4 = mecanismo correcto y razonamiento solido, con imprecisiones menores",
    "#   3 = mecanismo correcto pero el razonamiento es debil, generico o circular",
    "#   2 = mecanismo equivocado, aunque el razonamiento sea parcialmente defendible",
    "#   1 = mecanismo equivocado y razonamiento insuficiente o contradictorio",
    "#",
    "# La columna `notas` es opcional, para dejar por que dudo.",
    "#",
    "# NO consulte la nota del juez ni el gold completo mientras califica. El",
    "# valor de esta medicion depende de que las dos lecturas sean",
    "# independientes.",
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


def _faltantes() -> list[str]:
    falta = []
    if not RUTA_PREDS.exists():
        falta.append(f"{corta(RUTA_PREDS)} (corre M1)")
    if not RUTA_NOTAS.exists():
        falta.append(f"{corta(RUTA_NOTAS)} (corre M2)")
    return falta


def _cargar_corrida() -> tuple[dict, dict]:
    """(respuesta del sistema por id, nota del juez por id)."""
    bruto = json.loads(RUTA_PREDS.read_text(encoding="utf-8"))
    preds = bruto["datos"] if isinstance(bruto, dict) and "datos" in bruto else bruto
    salida = {p["id"]: schema.recortar_al_bloque(p["finetuned"])[0] for p in preds}

    notas = {}
    filas = list(csv.DictReader(
        RUTA_NOTAS.read_text(encoding="utf-8").splitlines()))
    for f in filas:
        v = (f.get("nota_juez") or "").strip()
        if v and v.lower() not in ("none", ""):
            try:
                notas[f["id"]] = int(float(v))
            except ValueError:
                pass
    return salida, notas


def muestra(ids_por_nota: dict[int, list[str]]) -> list[str]:
    """10 casos repartidos por la nota del juez, cubriendo los extremos.

    Una muestra aleatoria sobre una distribucion concentrada en 3 y 4 deja los
    extremos sin probar, y los extremos son donde mas importa: un 5 regalado o
    un 1 injusto son los errores que mas distorsionan la comparacion entre
    sistemas.
    """
    rnd = random.Random(SEMILLA)
    sel: list[str] = []
    # al menos uno de cada nota presente
    for nota in sorted(ids_por_nota):
        sel.append(rnd.choice(sorted(ids_por_nota[nota])))
    resto = sorted(i for v in ids_por_nota.values() for i in v if i not in sel)
    rnd.shuffle(resto)
    sel += resto[:max(0, N_MUESTRA - len(sel))]
    return sorted(sel[:N_MUESTRA])


def preparar() -> int:
    falta = _faltantes()
    if falta:
        print("Falta una corrida antes de poder calibrar:")
        for f in falta:
            print(f"  - {f}")
        return 1

    salida, notas = _cargar_corrida()
    if not notas:
        print(f"{RUTA_NOTAS.name} no tiene notas del juez legibles.")
        return 1

    casos = {c["id"]: c for c in schema.cargar(archivo="eval_set_v2.json")}
    por_nota: dict[int, list[str]] = defaultdict(list)
    for cid, n in notas.items():
        if cid in casos and cid in salida:
            por_nota[n].append(cid)
    sel = muestra(por_nota)

    if RUTA_CSV.exists():
        # Las dos columnas, no solo `nota_humana`: quien empiece anotando sus
        # dudas en `notas` tambien tiene trabajo que no se puede perder.
        previo = formularios.leer(RUTA_CSV, COLUMNAS_PERSONA)
        if previo["diligenciadas"]:
            print(f"NO se sobreescribe: {RUTA_CSV.name} ya tiene "
                  f"{previo['diligenciadas']} fila(s) con algo escrito.")
            print("Borrelo a mano si quiere empezar de nuevo.")
            return 1

    with RUTA_CSV.open("w", encoding="utf-8", newline="") as fh:
        for l in ESCALA:
            fh.write(l + "\n")
        w = csv.writer(fh)
        w.writerow(["id", "relato", "respuesta_del_sistema",
                    "respuesta_de_referencia", "nota_humana", "notas"])
        for cid in sel:
            c = casos[cid]
            w.writerow([cid, c["relato"], salida[cid],
                        schema.render_salida(c), "", ""])

    print(f"escrito {corta(RUTA_CSV)} con {len(sel)} casos.")
    print("\nreparto por nota del juez (oculta en el formulario):")
    for n, k in sorted(Counter(notas[i] for i in sel).items()):
        print(f"  nota {n}: {k}")
    print(f"\nids: {', '.join(sel)}")
    # El comando va completo A PROPOSITO. `--medir` sin `--anotador` sale con
    # error desde que el anotador es obligatorio, y una instruccion impresa
    # que falla al copiarla hace dudar de la herramienta, no del comando.
    print("\nDiligencielo y despues, segun QUIEN lo diligencio:")
    print("  python -I data/calibracion_juez.py --medir "
          "--anotador persona-externa")
    print("     (persona ajena al proyecto: la unica que mide ACUERDO)")
    print("  python -I data/calibracion_juez.py --medir --anotador equipo")
    print("  python -I data/calibracion_juez.py --medir --anotador asistente")
    print("     (estas dos miden CONSISTENCIA de la rubrica, no acuerdo, y "
          "el artefacto lo dice con esas palabras)")
    return 0


ANOTADORES = {
    "persona-externa": {
        "independiente": True,
        "nota": "Persona que no participo en escribir el gold, la rubrica ni "
                "el juez. Es la unica combinacion que responde la pregunta "
                "original: cuando el juez da un 4, una persona tambien lo "
                "daria?",
    },
    "equipo": {
        "independiente": False,
        "nota": "Alguien del mismo equipo que escribio el gold y la rubrica. "
                "Mide CONSISTENCIA de la rubrica, no acuerdo con un tercero: "
                "sabe de antemano que respuesta espera el gold.",
    },
    "asistente": {
        "independiente": False,
        "nota": "El mismo sistema que escribio el gold, la rubrica y el juez. "
                "NO mide si una persona coincide con el juez --- mide si una "
                "aplicacion independiente de la rubrica coincide con la del "
                "juez, que es una pregunta distinta y mas debil. Vale, pero "
                "solo si se llama por su nombre.",
    },
}
"""Quien puntuo, y que puede concluirse de eso.

POR QUE ESTO ES UN CAMPO OBLIGATORIO Y NO UNA NOTA AL PIE

Lo que hace util esta medicion es exactamente lo que la puede invalidar. Si
quien puntua escribio el gold, la rubrica y el juez, un acuerdo alto no dice
que el juez este bien calibrado: dice que el sistema es consistente consigo
mismo. Presentar eso como "validacion humana" seria el error que el resto del
proyecto lleva midiendo con cuidado --- el mismo que ya corregimos en
`por_fiabilidad_etiqueta`, donde `motor_de_reglas` significa CONSISTENTE con
el arbol del art. 6 y no INDEPENDIENTE de el.

Por eso `--medir` exige `--anotador` y el artefacto lo lleva dentro. No se
puede producir una calibracion sin decir quien la hizo.
"""


def medir(anotador: str = "persona-externa") -> int:
    if not RUTA_CSV.exists():
        print(f"no existe {RUTA_CSV.name}. Corre primero --preparar.")
        return 1
    falta = _faltantes()
    if falta:
        print("Falta la corrida para recuperar las notas del juez:")
        for f in falta:
            print(f"  - {f}")
        return 1

    _, notas_juez = _cargar_corrida()
    r = formularios.exigir(RUTA_CSV, COLUMNAS_PERSONA)
    if not r["cabecera_valida"]:
        return 1
    filas = [f for f in r["filas"] if (f.get("nota_humana") or "").strip()]
    if not filas:
        print(f"{RUTA_CSV.name} no tiene ninguna nota diligenciada.")
        return 1

    errores, hum, jue, ids = [], [], [], []
    for f in filas:
        cid = f["id"].strip()
        try:
            n = int(float(f["nota_humana"]))
        except ValueError:
            errores.append(f"{cid}: nota '{f['nota_humana']}' no es un entero")
            continue
        if not 1 <= n <= 5:
            errores.append(f"{cid}: nota {n} fuera de la escala 1-5")
            continue
        if cid not in notas_juez:
            errores.append(f"{cid}: el juez no dejo nota para este caso")
            continue
        ids.append(cid)
        hum.append(n)
        jue.append(notas_juez[cid])

    if errores:
        print(f"{len(errores)} filas con problemas:")
        for e in errores:
            print(f"  - {e}")
        if not hum:
            return 1
        print()

    r = acuerdo_entre_jueces([{"nota": x} for x in hum],
                             [{"nota": y} for y in jue],
                             "humano", "juez automatico")
    desac = [{"id": i, "humano": h, "juez": j, "delta": j - h}
             for i, h, j in zip(ids, hum, jue) if h != j]
    r["desacuerdos"] = desac
    r["sesgo_medio_del_juez"] = round(
        sum(j - h for h, j in zip(hum, jue)) / len(hum), 3)
    meta_anot = ANOTADORES[anotador]
    r["_anotador"] = anotador
    r["_independencia"] = {
        "independiente": meta_anot["independiente"],
        "nota": meta_anot["nota"],
        "que_mide": (
            "cuando el juez da un 4, una persona ajena tambien lo daria"
            if meta_anot["independiente"] else
            "si una aplicacion de la rubrica por quien la conoce coincide con "
            "la del juez --- NO es validacion externa"),
    }
    # LA LECTURA SE DERIVA DE LAS CIFRAS, NO SE ESCRIBE PARA UN ESCENARIO.
    #
    # El texto anterior describia UN caso --- "si Spearman es alta y el sesgo
    # es grande, el juez ordena bien y calibra mal" --- y se adjuntaba
    # siempre. Medido con `persona-externa`: Spearman 0.4388 y sesgo -0.3, es
    # decir el caso CONTRARIO. Un lector que viera "sesgo pequeno" junto a esa
    # frase concluiria que el juez esta bien, cuando el problema es que la
    # correlacion es baja. Una interpretacion enlatada que no cuadra con sus
    # propios datos es peor que no tenerla.
    #
    # Con la correlacion baja el sesgo es IRRELEVANTE: no hay un orden que
    # corregir desplazando las notas.
    _sp = r.get("corr_spearman")
    _sesgo = r.get("sesgo_medio_del_juez")
    _signo = ("MAS GENEROSO" if (_sesgo or 0) > 0 else "MAS SEVERO")
    if _sp is None:
        _lec = ("Spearman no esta definida (alguno de los dos puntuo con una "
                "sola categoria), asi que no se puede decir si el juez "
                "preserva el orden.")
    elif _sp < 0.6:
        _lec = (
            f"Spearman {_sp:.4f}: el juez NO preserva el orden de la persona. "
            "Esto NO es un problema de calibracion que se arregle desplazando "
            "las notas --- el sesgo medio es irrelevante cuando el orden no se "
            "mantiene, porque no hay nada que desplazar. La nota del juez esta "
            "debilmente relacionada con la de una persona ajena, asi que no "
            "sostiene ni una nota absoluta ni una comparacion entre sistemas. "
            "Lo que SI sostiene el proyecto son las metricas de dominio "
            "(`acierto_juridico`, `acc_mecanismo`, `macro_f1`), que las "
            "calcula `metricas.py` contra el gold y no pasan por el juez."
        )
    elif abs(_sesgo or 0) >= 0.5:
        _lec = (
            f"Spearman {_sp:.4f} con sesgo {_sesgo:+.2f} ({_signo} que la "
            "persona): el juez ORDENA bien pero CALIBRA mal. Sirve para "
            "comparar sistemas entre si y no para reportar una nota absoluta. "
            "Eso es una conclusion util, no un fallo del juez."
        )
    else:
        _lec = (
            f"Spearman {_sp:.4f} con sesgo {_sesgo:+.2f}: el juez ordena y "
            "calibra como la persona en esta muestra. Con n="
            f"{r.get('n')} es un indicio, no una validacion: el intervalo de "
            "una kappa con esta n es ancho."
        )
    r["lectura_calibracion"] = _lec
    r["_aviso_n"] = (
        f"n={r.get('n')}. Con esta muestra el intervalo de `kappa_aprueba` es "
        "ancho: lo que se establece es que el juez NO queda validado, no que "
        "quede refutado. Son cosas distintas y la segunda necesitaria mas n."
    )
    RUTA_OUT.write_text(json.dumps(r, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    if not meta_anot["independiente"]:
        print("=" * 70)
        print(f"  ANOTADOR: {anotador} --- NO INDEPENDIENTE")
        print(f"  {meta_anot['nota']}")
        print("  Esta cifra NO es validacion externa del juez. Lo que mide")
        print(f"  es: {r['_independencia']['que_mide']}.")
        print("=" * 70)
        print()
    print(f"n calibrados: {r['n']}\n")
    print(f"  media humano        : {r['media_a']}")
    print(f"  media juez          : {r['media_b']}")
    print(f"  sesgo medio del juez: {r['sesgo_medio_del_juez']:+}")
    print(f"  acuerdo exacto      : {r['acuerdo_exacto']:.1%}")
    print(f"  acuerdo a 1 punto   : {r['acuerdo_a_un_punto']:.1%}")
    print(f"  kappa (aprueba >=4) : {r['kappa_aprueba']}")
    print(f"  Spearman            : {r['corr_spearman']}")
    if desac:
        print(f"\n{len(desac)} desacuerdos:")
        for d in desac:
            print(f"  {d['id']}: humano {d['humano']} · juez {d['juez']} "
                  f"({d['delta']:+})")
    print(f"\nescrito {corta(RUTA_OUT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--preparar", action="store_true")
    g.add_argument("--medir", action="store_true")
    # Sin default a proposito: producir una calibracion sin decir quien la
    # hizo es justo lo que no puede pasar.
    ap.add_argument("--anotador", choices=sorted(ANOTADORES),
                    help="quien puntuo el csv. Obligatorio con --medir.")
    a = ap.parse_args()
    if a.preparar:
        return preparar()
    if not a.anotador:
        ap.error("--medir exige --anotador: " + ", ".join(sorted(ANOTADORES))
                 + ". Una calibracion sin saber quien la hizo no se puede "
                   "interpretar.")
    return medir(a.anotador)


if __name__ == "__main__":
    raise SystemExit(main())
