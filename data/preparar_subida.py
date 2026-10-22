"""Qué subir, en qué orden correr, y con qué huella cuadrar. Genera SUBIR.md.

ROADMAP3 · T-4. Tres fallos de una sola sesión vinieron de pegar celdas
sueltas sobre un notebook de Drive que iba por detrás: una celda desapareció,
la del cruce no corrió, y la huella no cuadraba. El manifiesto existía para
evitar justo eso y no sirvió, porque la deriva venía del método: parchear a
mano trozos de un archivo cuyo estado remoto nadie había comprobado.

LO QUE ESTE SCRIPT HACE, Y LO QUE NO PUEDE HACER

Hace dos cosas:

  1. Dice QUÉ ARCHIVOS cambiaron desde la última subida sellada, para que cada
     cambio viaje como archivo completo y no como celda pegada.
  2. Imprime el `_TOTAL` que `manifiesto.py` tiene que dar EN COLAB si Drive
     quedó al día, para compararlo antes de arrancar.

No puede comprobar Drive. No tiene acceso, y afirmar «Drive está al día»
desde aquí sería exactamente el tipo de conclusión sin evidencia que el resto
del proyecto evita. Lo que hace es dejar la huella esperada a la vista para
que la comparación la haga quien sí ve las dos.

EL SELLO

`--sellar` guarda el manifiesto actual en `data/subida_sellada.txt` como «esto
es lo que está arriba». A partir de ahí, `--que-falta` dice solo lo que cambió
después. Sin sello no hay diferencia que calcular, y el script lo dice en vez
de listar los 40 archivos como si todos hicieran falta.

    python -I data/preparar_subida.py              # escribe SUBIR.md
    python -I data/preparar_subida.py --que-falta  # solo el diff, a consola
    python -I data/preparar_subida.py --sellar      # marca lo actual como subido
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "data"))

from manifiesto import manifiesto, total                      # noqa: E402

SELLO = RAIZ / "data" / "subida_sellada.txt"
SALIDA = RAIZ / "SUBIR.md"
NL = chr(10)

# De `arranque.ORDEN`, para que no haya dos listas del orden de ejecución que
# puedan divergir.
try:
    sys.path.insert(0, str(RAIZ / "src"))
    from arranque import ORDEN
except Exception:                                              # noqa: BLE001
    ORDEN = {}


def _leer_sello() -> dict[str, tuple[int, str]]:
    if not SELLO.exists():
        return {}
    out = {}
    for linea in SELLO.read_text(encoding="utf-8").splitlines():
        p = linea.split()
        if len(p) == 3 and not linea.startswith(("#", "_TOTAL")):
            out[p[0]] = (int(p[1]), p[2])
    return out


def _escribir_sello(m: list[tuple[str, int, str]]) -> None:
    lineas = ["# Manifiesto sellado como SUBIDO. Lo genera "
              "`preparar_subida.py --sellar`.",
              "# No se edita a mano: si no refleja lo que esta en Drive, el "
              "diff miente."]
    lineas += [f"{r} {t} {h}" for r, t, h in m]
    lineas.append(f"_TOTAL {sum(t for _, t, _ in m)} {total(m)}")
    SELLO.write_text(NL.join(lineas) + NL, encoding="utf-8", newline=NL)


def diferencia() -> dict:
    m = manifiesto()
    sello = _leer_sello()
    actual = {r: (t, h) for r, t, h in m}

    nuevos = [r for r in actual if r not in sello]
    cambiados = [r for r in actual
                 if r in sello and sello[r][1] != actual[r][1]]
    borrados = [r for r in sello if r not in actual]
    return {
        "manifiesto": m,
        "huella_total": total(m),
        "bytes_total": sum(t for _, t, _ in m),
        "hay_sello": bool(sello),
        "nuevos": sorted(nuevos),
        "cambiados": sorted(cambiados),
        "borrados": sorted(borrados),
        "a_subir": sorted(set(nuevos) | set(cambiados)),
    }


def _bloque_orden() -> list[str]:
    if not ORDEN:
        return ["> `arranque.ORDEN` no se pudo leer: el orden de ejecucion no "
                "se declara aqui para no escribirlo por duplicado."]
    L = []
    for mod, c in ORDEN.items():
        L.append(f"### {c['posicion']} · `{mod.upper()}` · {c['entorno']}")
        L.append("")
        L.append(f"- duracion: {c['duracion']}")
        L.append(f"- necesita: {', '.join(c['necesita'])}")
        L.append(f"- produce {len(c['produce'])} artefactos en `results/`")
        if c.get("nota"):
            L.append(f"- **{c['nota']}**")
        L.append("")
    return L


def _m1_dos_veces() -> list[str]:
    """Si la reproducibilidad de M1 sigue sin poder atribuirse, M1 va 2 veces.

    LA CONDICION SE LEE DEL ARTEFACTO, NO SE ESCRIBE

    `m1_estabilidad.json` compara la corrida con la anterior. Mientras no
    tenga `mismo_codigo` **y** `mismos_datos` a la vez, un `identicas: False`
    no se puede atribuir: puede ser no-determinismo o puede ser el cambio de
    codigo entre las dos. Y un `identicas: True` con el codigo distinto es
    suerte, no reproducibilidad.

    Dos corridas consecutivas con `src/` intacto resuelven las dos lecturas,
    porque entonces `identicas` significa algo en los dos sentidos:

        True  -> reproducible
        False -> no-determinismo REAL, medido, que tambien es un resultado

    Cuando una corrida lo consiga, esta funcion devuelve lista vacia y el
    bloque desaparece de SUBIR.md. Es lo que impide que una instruccion
    generada se quede caducada dentro del archivo que alguien sigue al pie de
    la letra.
    """
    p = RAIZ / "results" / "m1_estabilidad.json"
    if not p.exists():
        return []
    try:
        e = json.loads(p.read_text(encoding="utf-8"))
    except Exception:                                      # noqa: BLE001
        return []
    if e.get("mismo_codigo") is True and e.get("mismos_datos") is True:
        return []       # ya esta resuelto: una corrida basta
    return [
        "> ### M1 va DOS veces, y las dos en la misma sesion",
        ">",
        f"> La ultima comparacion de estabilidad "
        f"(`{e.get('corrida_previa')}` vs `{e.get('corrida_actual')}`) salio "
        f"con `identicas: {e.get('identicas')}`, "
        f"`mismo_codigo: {e.get('mismo_codigo')}` y "
        f"`mismos_datos: {e.get('mismos_datos')}`. Con el codigo distinto "
        "entre las dos, esa diferencia **no se puede atribuir**: puede ser "
        "no-determinismo o puede ser el cambio de codigo. Y coincidir con el "
        "codigo distinto seria suerte, no reproducibilidad.",
        ">",
        "> - **corrida A** · re-ancla la huella. Su celda de estabilidad "
        "volvera a decir `mismo_codigo: false` y eso es lo esperado: compara "
        "contra una corrida anterior al cambio.",
        "> - **corrida B** · compara contra A, con el mismo codigo. Esta es "
        "la que responde, y lo hace en los dos sentidos: identicas significa "
        "reproducible, y distintas significa no-determinismo medido.",
        ">",
        "> **Las dos en la MISMA sesion de Colab, sin reiniciar el entorno.** "
        "`estabilidad` compara tambien el hardware (`mismo_hardware`, por "
        "nombre de GPU). Si la sesion se cae en medio y Colab asigna otra "
        "GPU, la diferencia vuelve a tener dos explicaciones y se pierde la "
        "corrida.",
        ">",
        "> **Y M2 va despues de B, no de A**: lee "
        "`results/m1_predicciones.json`, que B sobrescribe. Corrido entre las "
        "dos, el juez puntuaria predicciones que el reporte no va a citar.",
        "",
    ]


def construir(dif: dict) -> list[str]:
    L: list[str] = []
    a = L.append
    a("# Qué subir y en qué orden correr")
    a("")
    a("> Generado por `python -I data/preparar_subida.py`. No se edita a "
      "mano: se vuelve a generar.")
    a("")
    a("## 1 · La huella con la que tiene que cuadrar")
    a("")
    a("Después de subir, en **cada** notebook, antes de correr nada:")
    a("")
    a("```")
    a("!python -I /content/drive/MyDrive/agenteAmparo/data/manifiesto.py")
    a("```")
    a("")
    a(f"Tiene que imprimir exactamente:")
    a("")
    a("```")
    a(f"_TOTAL  {dif['bytes_total']} bytes  {dif['huella_total']}")
    a("```")
    a("")
    a("Si no coincide, **no arranques**: la salida del manifiesto nombra el "
      "archivo que difiere. Correr con un `src/` distinto del que se reporta "
      "no produce un resultado peor, produce un resultado que no se puede "
      "atribuir a ningún código.")
    a("")
    a("Este script no ve Drive y no puede decir que esté al día. Deja la "
      "huella esperada para que la comparación la haga quien ve las dos.")
    a("")

    a("## 2 · Qué archivos tienen que viajar")
    a("")
    if not dif["hay_sello"]:
        a("No hay subida sellada previa (`data/subida_sellada.txt` no "
          "existe), así que **no se puede calcular qué cambió**: sube los "
          f"{len(dif['manifiesto'])} archivos del manifiesto y después "
          "`python -I data/preparar_subida.py --sellar`.")
        a("")
    elif not dif["a_subir"]:
        a("Nada cambió desde la última subida sellada. Si el `_TOTAL` de "
          "Colab no cuadra con el de arriba, entonces lo que está en Drive no "
          "es lo que se selló.")
        a("")
    else:
        a(f"**{len(dif['a_subir'])} archivos** cambiaron desde la última "
          "subida sellada. Cada uno viaja **completo**, sustituyendo el de "
          "Drive — no se pegan celdas sueltas:")
        a("")
        hs = {r: h for r, _, h in dif["manifiesto"]}
        bs = {r: t for r, t, _ in dif["manifiesto"]}
        L.append("| archivo | bytes | huella | estado |")
        L.append("|---|---|---|---|")
        for r in dif["a_subir"]:
            est = "nuevo" if r in dif["nuevos"] else "cambiado"
            L.append(f"| `{r}` | {bs[r]} | `{hs[r]}` | {est} |")
        a("")
    if dif["borrados"]:
        a(f"Y **{len(dif['borrados'])}** archivos que estaban sellados ya no "
          "existen aquí; si siguen en Drive, bórralos: "
          + ", ".join(f"`{r}`" for r in dif["borrados"]))
        a("")
    a("No subas `__pycache__/`.")
    a("")

    a("## 3 · El orden, y por qué es ese")
    a("")
    L += _bloque_orden()
    L += _m1_dos_veces()
    a("Se corren **seguidos y sin tocar nada en medio**. Cambiar "
      "`src/` entre M1 y M3 cambia la huella de código, y entonces "
      "`verificar_entrega.py` marca —con razón— que las corridas no son del "
      "mismo experimento.")
    a("")

    a("## 4 · Al terminar los tres")
    a("")
    a("```")
    a("python -I data/verificar_entrega.py   # artefactos, corridas, huellas")
    a("python -I data/reporte.py             # escribe REPORTE.md")
    a("```")
    a("")
    a("`verificar_entrega.py` tiene que salir con **exit 0**. `reporte.py` se "
      "niega a escribir si falta un artefacto, en vez de dejar huecos "
      "silenciosos en el documento.")
    a("")
    a("## 5 · Manifiesto completo")
    a("")
    L.append("| archivo | bytes | huella |")
    L.append("|---|---|---|")
    for r, t, h in dif["manifiesto"]:
        L.append(f"| `{r}` | {t} | `{h}` |")
    a("")
    a(f"**{len(dif['manifiesto'])} archivos · {dif['bytes_total']} bytes · "
      f"`{dif['huella_total']}`**")
    return L


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--sellar", action="store_true",
                   help="marca el manifiesto actual como lo que esta en Drive")
    g.add_argument("--que-falta", action="store_true",
                   help="solo el diff, a consola, sin escribir SUBIR.md")
    a = ap.parse_args()

    dif = diferencia()

    if a.sellar:
        _escribir_sello(dif["manifiesto"])
        print(f"sellado: {len(dif['manifiesto'])} archivos · "
              f"{dif['bytes_total']} bytes · {dif['huella_total']}")
        print(f"  -> {SELLO.relative_to(RAIZ)}")
        print("  A partir de ahora `--que-falta` dice solo lo que cambie "
              "despues de esto.")
        return 0

    print("=" * 74)
    print(f"  HUELLA ESPERADA EN COLAB: {dif['bytes_total']} bytes  "
          f"{dif['huella_total']}")
    print("=" * 74)
    if not dif["hay_sello"]:
        print("  sin subida sellada: no se puede calcular el diff.")
        print(f"  sube los {len(dif['manifiesto'])} archivos y luego "
              "--sellar.")
    elif dif["a_subir"]:
        print(f"  {len(dif['a_subir'])} archivos a subir:")
        for r in dif["a_subir"]:
            est = "nuevo" if r in dif["nuevos"] else "cambiado"
            print(f"    {est:9s} {r}")
    else:
        print("  nada cambio desde la ultima subida sellada.")
    for r in dif["borrados"]:
        print(f"    borrado   {r}  (si sigue en Drive, borralo)")
    print("=" * 74)

    if a.que_falta:
        return 0
    SALIDA.write_text(NL.join(construir(dif)) + NL, encoding="utf-8",
                      newline=NL)
    print(f"  escrito: {SALIDA.name}")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
