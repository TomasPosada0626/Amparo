"""
Comprueba que la entrega esta completa y coherente (ROADMAP #34b).

POR QUE EXISTE, CON EL CASO QUE LO MOTIVO

`autoprueba_integracion.py` comprueba la fontaneria ANTES de correr. Esto
comprueba los ARTEFACTOS DESPUES, que es un problema distinto y que se venia
haciendo a mano.

Y hacerlo a mano fallo: en `runs/` habia **9 copias viejas** de artefactos de
una corrida anterior al dataset v2, con los numeros de entonces. Una de ellas,
`m1_scorecard_finetuned.json`, daba `acc_mecanismo` 58.7% cuando el vigente
daba 82.6%. Alguien que abriera ese archivo --- en un sitio perfectamente
plausible --- leia las cifras equivocadas sin forma de notarlo.

LAS CINCO COSAS QUE COMPRUEBA

1. ESTAN los artefactos que cada modulo declara producir.
2. Vienen de la MISMA corrida de su modulo: cada uno lleva `_corrida`, y dos
   artefactos de M2 con corridas distintas significan que uno quedo de antes.
3. Las HUELLAS DE CODIGO coinciden entre los tres modulos. Si M3 corrio con un
   `src/` distinto del de M1, las cifras no son comparables aunque las dos
   corridas sean validas.
4. La VERSION DE DATOS es la misma en los tres. Comparar M1 sobre el eval v1 y
   M3 sobre el v2 no es un delta del sistema: es un cambio de vara.
5. No hay COPIAS SUELTAS en `runs/` fuera de su carpeta de corrida. Es el
   fallo concreto que motivo este script: nueve artefactos de una corrida
   anterior, en un sitio plausible, con las cifras de entonces.

No comprueba que las cifras sean BUENAS. Comprueba que sean del mismo
experimento, que es condicion previa para poder leerlas.

    python -I data/verificar_entrega.py
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

RESULTS = RAIZ / "results"

# Lo que cada modulo declara producir. La fuente es `arranque.ORDEN`, para que
# no haya dos listas de artefactos esperados que puedan divergir.
try:
    from arranque import ORDEN
    ESPERADOS = {m: [Path(x).name for x in c["produce"]]
                 for m, c in ORDEN.items()}
except Exception:                                      # noqa: BLE001
    ESPERADOS = {}


def _leer(p: Path):
    try:
        if p.suffix == ".json":
            return json.loads(p.read_text(encoding="utf-8"))
        return p.read_text(encoding="utf-8")
    except Exception as ex:                             # noqa: BLE001
        return {"_error": f"{type(ex).__name__}: {ex}"}


def _meta_de(p: Path) -> dict:
    """`_corrida`, `_modulo`, huella de codigo y version de datos, si estan."""
    d = _leer(p)
    if not isinstance(d, dict):
        # Un CSV no lleva el sello dentro. `publicar()` deja el hermano
        # `<nombre>.corrida.txt` justo para esto.
        hermano = p.with_suffix("").with_suffix(".corrida.txt")
        if not hermano.exists():
            hermano = p.parent / (p.stem + ".corrida.txt")
        if hermano.exists():
            # SE QUITA EL PREFIJO `modulo/`, Y NO ES COSMETICA.
            #
            # `publicar()` escribe el hermano como `m2/20261018T080311Z` y el
            # sello de un JSON como `20261018T080311Z`. La comprobacion 2
            # mete los dos en un `set` y veia DOS corridas donde hay una:
            # "M2: MEZCLA de 2 corridas" con los diez artefactos de la misma.
            #
            # Es el fallo contrario al de las huellas --- ese callaba, este
            # grita --- y los dos corroen igual: una alarma que salta donde
            # no hay nada ensena a ignorar las alarmas.
            crudo = hermano.read_text(encoding="utf-8").strip()
            return {"_corrida": crudo.split("/")[-1], "_modulo_txt": crudo}
        return {}
    return {k: v for k, v in d.items() if k.startswith("_")}


def main() -> int:
    print("=" * 74)
    print("  VERIFICACION DE LA ENTREGA")
    print("=" * 74)
    if not RESULTS.is_dir():
        print(f"  no existe {RESULTS.relative_to(RAIZ)}/: no hay nada que "
              f"verificar.")
        print("  Corre M1, M2 y M3 primero.")
        return 1

    presentes = {p.name for p in RESULTS.iterdir() if p.is_file()}
    fallos, avisos = [], []

    # --- 1. estan? ----------------------------------------------------
    print("\n  1 · artefactos esperados por modulo")
    for mod, nombres in ESPERADOS.items():
        faltan = [n for n in nombres if n not in presentes]
        hay = len(nombres) - len(faltan)
        print(f"    {mod.upper():<4} {hay}/{len(nombres)}"
              + (f"   faltan: {', '.join(faltan)}" if faltan else ""))
        if faltan:
            fallos.append(f"{mod.upper()}: faltan {len(faltan)} artefactos "
                          f"({', '.join(faltan[:3])})")
    sobran = presentes - {n for v in ESPERADOS.values() for n in v}
    sobran = {s for s in sobran if not s.endswith(".corrida.txt")}
    if sobran:
        avisos.append(f"{len(sobran)} archivo(s) en results/ que ningun modulo "
                      f"declara producir: {', '.join(sorted(sobran)[:5])}")

    # --- 2. misma corrida por modulo -----------------------------------
    print("\n  2 · coherencia de corrida dentro de cada modulo")
    por_mod = defaultdict(dict)
    for mod, nombres in ESPERADOS.items():
        for n in nombres:
            p = RESULTS / n
            if p.exists():
                corr = _meta_de(p).get("_corrida")
                if corr:
                    por_mod[mod][n] = corr
    for mod, d in por_mod.items():
        corridas = set(d.values())
        if len(corridas) <= 1:
            print(f"    {mod.upper():<4} {len(d)} artefacto(s), 1 corrida: "
                  f"{next(iter(corridas), '(sin sello)')}")
        else:
            print(f"    {mod.upper():<4} MEZCLA de {len(corridas)} corridas:")
            for n, c in sorted(d.items()):
                print(f"           {n:<36} {c}")
            fallos.append(f"{mod.upper()}: artefactos de {len(corridas)} "
                          f"corridas distintas. Alguno quedo de antes.")
    sin_sello = [n for mod, ns in ESPERADOS.items() for n in ns
                 if (RESULTS / n).exists() and n not in por_mod[mod]]
    if sin_sello:
        avisos.append(f"{len(sin_sello)} artefacto(s) sin sello `_corrida`: "
                      f"{', '.join(sin_sello[:4])}")

    # --- 3 y 4. huella de codigo y version de datos --------------------
    print("\n  3 · huella de codigo y version de datos entre modulos")
    huellas, datos = {}, {}
    for mod in ESPERADOS:
        corr = next(iter(set(por_mod[mod].values())), None)
        if not corr:
            continue
        cj = RAIZ / "runs" / mod / corr / "corrida.json"
        if not cj.exists():
            avisos.append(f"{mod.upper()}: no esta runs/{mod}/{corr}/"
                          f"corrida.json, no se puede cotejar el codigo")
            continue
        d = _leer(cj)
        if not isinstance(d, dict):
            continue
        # LAS CLAVES SON `codigo` Y `datos`, NO `version_*`.
        #
        # `corridas.Corrida` las escribe asi: `meta["codigo"] =
        # version_codigo()` y `meta["datos"] = version_datos()`. Aqui se
        # buscaban por el nombre de las FUNCIONES, no de los campos, asi que
        # los dos diccionarios salian vacios SIEMPRE y
        # `len(set(huellas.values())) > 1` era False por vacio. Las
        # comprobaciones 3 y 4 pasaban sin comparar nada: este script habria
        # dicho "la entrega es coherente" con los tres modulos corridos sobre
        # tres `src/` distintos, que es justo lo que existe para impedir.
        #
        # Se admite el nombre viejo porque las corridas que ya estan en
        # `runs/` no se van a reescribir.
        cod = d.get("codigo") or d.get("version_codigo") or {}
        h = cod.get("_conjunto")
        if h:
            huellas[mod] = h
        vd = d.get("datos") or d.get("version_datos") or {}
        ev = (vd.get("eval_set.json") or {})
        if ev:
            datos[mod] = (ev.get("version"), ev.get("n"))

    if len(set(huellas.values())) > 1:
        print("    huellas de codigo DISTINTAS:")
        for m, h in huellas.items():
            print(f"      {m.upper():<4} {h}")
        fallos.append("los modulos corrieron con versiones distintas de src/: "
                      "las cifras no son comparables entre ellos")
    elif len(huellas) == len(ESPERADOS):
        print(f"    codigo: la misma huella en {len(huellas)} modulo(s) "
              f"({next(iter(huellas.values()))})")
    else:
        # NO PODER COMPROBAR ES UN FALLO, NO UN SILENCIO.
        #
        # `elif huellas:` dejaba el caso vacio sin imprimir y sin anotar nada,
        # y la ausencia de queja se lee como aprobacion. Mismo criterio que
        # `acierto_abstencion: None` y `cohen_kappa: indefinido`: lo que no se
        # midio se dice, no se calla.
        fallos.append(
            f"solo se pudo leer la huella de codigo de {len(huellas)} de "
            f"{len(ESPERADOS)} modulos, asi que NO se comprobo que corrieran "
            "con el mismo `src/`. No es que coincidan: es que no se leyo. "
            "Hacen falta los `runs/<modulo>/<id>/corrida.json`.")

    if len(set(datos.values())) > 1:
        print("    version de datos DISTINTA:")
        for m, v in datos.items():
            print(f"      {m.upper():<4} eval_set {v[0]}, n={v[1]}")
        fallos.append("los modulos corrieron con versiones distintas del eval "
                      "set: el delta entre ellos es un cambio de vara, no del "
                      "sistema")
    elif len(datos) == len(ESPERADOS):
        v = next(iter(datos.values()))
        print(f"    datos: eval_set {v[0]}, n={v[1]} en {len(datos)} modulo(s)")
    else:
        fallos.append(
            f"solo se pudo leer la version de datos de {len(datos)} de "
            f"{len(ESPERADOS)} modulos, asi que NO se comprobo que corrieran "
            "sobre el mismo eval set.")

    # --- copias viejas en runs/, que es lo que motivo esto -------------
    print("\n  4 · copias sueltas en runs/")
    viejas = []
    rd = RAIZ / "runs"
    if rd.is_dir():
        for p in rd.iterdir():
            if p.is_file() and p.suffix in (".json", ".csv", ".png"):
                viejas.append(p.name)
    if viejas:
        print(f"    {len(viejas)} archivo(s) en la RAIZ de runs/, fuera de "
              f"cualquier carpeta de corrida:")
        for n in sorted(viejas)[:8]:
            print(f"      {n}")
        avisos.append(f"{len(viejas)} copia(s) suelta(s) en runs/. Asi "
                      f"aparecieron las 9 con los numeros del dataset v2: "
                      f"estan en un sitio plausible y no son las vigentes.")
    else:
        print("    ninguna: todo esta dentro de su carpeta de corrida")

    print("\n" + "=" * 74)
    for a in avisos:
        print(f"  AVISO  {a}")
    for f in fallos:
        print(f"  FALLA  {f}")
    if fallos:
        print(f"\n  {len(fallos)} problema(s). La entrega NO es coherente.")
    else:
        print("\n  La entrega esta completa y es coherente: los artefactos "
              "existen,")
        print("  vienen de la misma corrida de su modulo, y los tres modulos")
        print("  usaron el mismo codigo y la misma version de datos.")
    print("  Esto NO dice que las cifras sean buenas: dice que son del mismo")
    print("  experimento, que es condicion previa para poder leerlas.")
    print("=" * 74)
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
