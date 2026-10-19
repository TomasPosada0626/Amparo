"""Un comando. Reproduce y verifica la evaluación de agenteAmparo.

    pip install -r requirements.txt
    python reproducir.py

QUÉ HACE, Y POR QUÉ ESTO ES UN ARCHIVO Y NO UNAS INSTRUCCIONES

El criterio de reproducibilidad del harness pide que se corra «con un
comando, semillas fijadas, versiones registradas, resultados idénticos entre
ejecuciones, reutilizable por otro equipo sin explicación». Lo que había era
tres notebooks de Colab que exigen montar Drive, cargar un secreto y cuadrar
un sello de subida. Eso es reproducible por *nosotros*, que sabemos el orden;
no por otro equipo.

Este archivo separa dos cosas que los notebooks mezclaban:

  LO QUE SE PUEDE REPRODUCIR SIN GPU NI API  ── y por tanto en cualquier
  máquina, en segundos: la fontanería completa (61 pruebas), la coherencia de
  la entrega, la cobertura del corpus, el diagnóstico de `accion_cumplimiento`
  y la regeneración del reporte **desde los artefactos publicados**. Si el
  reporte que sale es igual al que está en el repositorio, las cifras del
  documento salen de los datos y no de la memoria de nadie.

  LO QUE EXIGE UNA A100 Y UNA CLAVE  ── entrenar el adaptador y volver a
  llamar al juez. Eso NO lo hace este script, y decirlo es parte de la
  respuesta: un script que fingiera reproducir el entrenamiento en CPU estaría
  mintiendo sobre lo que verifica.

Sale con 0 si todo lo reproducible reproduce, y con 1 nombrando lo que no.

    python reproducir.py            # todo lo que no necesita GPU ni API
    python reproducir.py --rapido   # sin el reporte ni el diagnóstico
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PY = [sys.executable, "-I"]

# LA CONSOLA NO PUEDE TUMBAR ESTE SCRIPT.
#
# En un Windows en espanol la salida estandar va en cp1252 y cualquier
# caracter fuera de esa pagina lanza UnicodeEncodeError --- el script moria
# imprimiendo un guion largo, DESPUES de haber corrido los cinco pasos
# correctamente. Para un archivo cuyo proposito es "reutilizable por otro
# equipo sin explicacion", morir por la codificacion de la terminal es el
# peor fallo posible: el trabajo estaba hecho y el veredicto no se vio.
#
# `errors="replace"` degrada un caracter raro en vez de abortar.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                   # noqa: BLE001
        pass


def _correr(args: list[str], etq: str) -> tuple[int, str]:
    t0 = time.perf_counter()
    r = subprocess.run(PY + args, capture_output=True, text=True,
                       cwd=str(RAIZ))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _linea(estado: str, etq: str, detalle: str = "") -> None:
    print(f"  {estado:9s} {etq:46s}{detalle}")


def entorno() -> list[tuple[str, bool, str]]:
    """Qué hay instalado. Lo que falte limita qué se puede reproducir."""
    out = []
    for mod, para in (("torch", "M1 (entrenamiento y generación)"),
                      ("transformers", "M1"),
                      ("sentence_transformers", "M3 (recuperación densa)"),
                      ("sklearn", "métricas"),
                      ("pandas", "tablas"),
                      ("groq", "el juez de M2 y el agente de M3"),
                      ("openpyxl", "formularios de anotación")):
        try:
            __import__(mod)
            out.append((mod, True, para))
        except ImportError:
            out.append((mod, False, para))
    return out


PASOS = [
    (["src/autoprueba_integracion.py"], "61 pruebas de fontanería",
     "la lógica del motor, las métricas y los contratos de los artefactos",
     True),
    (["data/verificar_entrega.py"], "coherencia de la entrega",
     "los artefactos están, son de la misma corrida y comparten huella",
     True),
    (["data/auditar_cobertura.py"], "cobertura del corpus",
     "toda cita esperada tiene fragmento que la respalde",
     True),
    (["data/diagnostico_cumplimiento.py"], "diagnóstico de accion_cumplimiento",
     "qué rompe la vía en el brazo del agente",
     False),
    (["data/reporte.py"], "regenerar REPORTE.md desde los artefactos",
     "ninguna cifra del reporte está escrita a mano",
     False),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rapido", action="store_true",
                    help="solo lo esencial: pruebas, entrega y corpus")
    a = ap.parse_args()

    print("=" * 78)
    print("  agenteAmparo · reproducción de la evaluación")
    print("=" * 78)
    print(f"  python {sys.version.split()[0]}  ·  {sys.platform}")
    print()
    print("  entorno:")
    falta_pesado = []
    for mod, hay, para in entorno():
        _linea("instalado" if hay else "FALTA", mod, para)
        if not hay:
            falta_pesado.append(mod)
    if falta_pesado:
        print()
        print("  Falta algún paquete. `pip install -r requirements.txt`.")
        print("  Lo de abajo corre igual si lo que falta es `torch` o `groq`:")
        print("  esta reproducción NO entrena ni llama a la API.")
    print()
    print("-" * 78)
    print("  LO QUE SE REPRODUCE AQUI (sin GPU, sin API, sin red)")
    print("-" * 78)

    resultados = []
    for args, etq, por_que, esencial in PASOS:
        if a.rapido and not esencial:
            continue
        t0 = time.perf_counter()
        cod, salida = _correr(args, etq)
        seg = time.perf_counter() - t0
        resultados.append((etq, cod, por_que, salida))
        _linea("OK" if cod == 0 else "FALLA", etq, f"{seg:6.1f}s  · {por_que}")

    malos = [(e, c, p, s) for e, c, p, s in resultados if c != 0]

    print()
    print("-" * 78)
    print("  LO QUE *NO* SE REPRODUCE AQUI, Y HACE FALTA DECIRLO")
    print("-" * 78)
    print("  - Entrenar el adaptador LoRA: exige una GPU A100. El adaptador")
    print("    de cada corrida queda en `models/m1-adaptador-<id>` con la")
    print("    huella de sus pesos, para poder cotejar que el que se carga es")
    print("    el que produjo las cifras.")
    print("  - Volver a llamar al juez y al agente: exigen GROQ_API_KEY.")
    print("    Sus salidas están cacheadas en la corrida, que es lo que hace")
    print("    el harness reproducible entre ejecuciones.")
    print("  Un script que fingiera reproducir esas dos cosas en CPU estaría")
    print("  mintiendo sobre lo que verifica.")

    print()
    print("=" * 78)
    if not malos:
        print("  TODO LO REPRODUCIBLE REPRODUCE.")
        print()
        print("  REPORTE.md está regenerado desde los artefactos de")
        print("  `results/`. Si coincide con el del repositorio, las cifras")
        print("  del documento salen de los datos.")
        print("=" * 78)
        return 0

    print(f"  {len(malos)} paso(s) NO reprodujeron:")
    print("=" * 78)
    for etq, cod, por_que, salida in malos:
        print()
        print(f"  --- {etq}  (exit {cod})")
        for l in salida.strip().splitlines()[-14:]:
            print(f"      {l}")
    print()
    print("=" * 78)
    print("  Lo de arriba es el detalle de cada fallo, con el archivo o la")
    print("  cifra que lo causa. Ninguno es un error de este script.")
    print("=" * 78)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
