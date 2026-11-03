"""El arranque de una corrida: lo que los cuatro notebooks repetian en sus
primeras celdas, en un solo lugar.

Antes cada notebook copiaba el montaje de Drive, la busqueda de la raiz, la
comprobacion del sello, la lectura de `GROQ_API_KEY` y `arranque.celda()`.
Las copias divergieron (la de M3 leia el secreto con menos diagnostico, y M1
no lo leia en absoluto en la corrida 20261018T070145Z). Ahora la unica parte
que sigue en el notebook es la que no puede estar aqui: montar Drive y poner
la raiz en `sys.path`, porque hasta entonces `amparo` no se puede importar.

    from amparo.ejecucion import entorno
    c = entorno.preparar("m1")
"""
from __future__ import annotations

import os
import subprocess
import sys

from amparo.config import RAIZ


def verificar_sello(raiz=RAIZ) -> int:
    """¿Drive tiene lo MISMO que el disco local?

    `arranque.celda()` comprueba que los archivos EXISTAN. Esto comprueba que
    sean los MISMOS, que es otra cosa: un `metricas.py` viejo existe igual de
    bien que el nuevo, y una corrida sobre codigo desactualizado produce cifras
    perfectamente plausibles y perfectamente inservibles sin que nada lo delate.

    Compara contra `data/subida_sellada.txt` (lo genera
    `preparar_subida.py --sellar`): la comparacion la hace el codigo y nombra
    el archivo, en vez de imprimir una huella y confiar en que alguien la mire.
    Con `subprocess` y no con `!python` porque la ruta de Drive puede llevar un
    espacio ("Colab Notebooks") y el shell la partiria.

    Devuelve el codigo de `manifiesto.py`: 0 al dia, 2 sin sello (aviso).
    Con 1 (desincronizado) para la corrida.
    """
    r = subprocess.run([sys.executable, "-I", str(raiz / "data" / "manifiesto.py"),
                        "--contra-sello"], capture_output=True, text=True, cwd=str(raiz))
    print(r.stdout.strip() or (r.stderr or "")[-400:])
    if r.returncode == 1:
        raise SystemExit(
            "Hay archivos sin subir o desincronizados (arriba estan nombrados). "
            "Subelos y vuelve a correr esta celda ANTES de seguir.")
    if r.returncode == 2:
        print()
        print("AVISO: sin sello no se puede verificar que Drive este al dia.")
        print("Compara la huella de arriba con la del disco local a mano.")
    return r.returncode


def cargar_clave_groq(pedir_por_teclado: bool = False) -> bool:
    """Pone `GROQ_API_KEY` en el entorno desde los secretos de Colab.

    VA ANTES DE `arranque.celda()`, Y EL ORDEN NO ES COSMETICO: `arranque`
    comprueba `os.environ["GROQ_API_KEY"]` y es esta funcion la que lo pone.
    Estuvieron al reves en M2 y fallaba SIEMPRE, con el secreto bien puesto o
    sin poner.

    Si la clave ya esta en el entorno (local, CI) no se toca. Colab distingue
    dos fallos que se arreglan distinto ---el secreto no existe, o existe sin
    acceso para este notebook--- y decir cual evita buscar donde no hay nada.

    `pedir_por_teclado=False` en M1: la redaccion es opcional y una corrida de
    30 minutos no puede quedarse esperando a que alguien escriba.
    """
    if os.environ.get("GROQ_API_KEY"):
        print("clave de Groq ya presente en el entorno")
        return True
    try:
        from google.colab import userdata
        clave = userdata.get("GROQ_API_KEY")
        assert clave, "el secreto existe pero esta vacio"
        os.environ["GROQ_API_KEY"] = clave
        print("clave de Groq cargada desde los secretos de Colab")
        return True
    except Exception as ex:                                  # noqa: BLE001
        tipo = type(ex).__name__
        if "NotebookAccess" in tipo:
            print("El secreto GROQ_API_KEY existe pero este notebook NO tiene")
            print("acceso: panel izquierdo, icono de la llave, y activa el")
            print("interruptor de acceso para este notebook.")
        elif "SecretNotFound" in tipo:
            print("No hay ningun secreto llamado GROQ_API_KEY: panel izquierdo,")
            print("icono de la llave, 'Anadir secreto nuevo'.")
        else:
            print(f"No pude leer el secreto ({tipo}): {ex}")
    if pedir_por_teclado:
        import getpass
        os.environ["GROQ_API_KEY"] = getpass.getpass("GROQ_API_KEY: ")
        return bool(os.environ["GROQ_API_KEY"])
    return False


def preparar(modulo: str, *, sello: bool = True, pedir_clave: bool = False):
    """Todo el arranque de un modulo, en el orden que cada paso exige.

    1. `os.chdir(RAIZ)`: varios scripts de `data/` y rutas relativas
       (`results/...`) asumen la raiz como directorio de trabajo.
    2. `corridas.nueva(modulo)`: la carpeta inmutable `runs/<modulo>/<id>/`.
    3. El sello, ANTES de bajar pesos: enterarse antes cuesta dos segundos,
       enterarse despues cuesta la corrida.
    4. La clave de Groq, ANTES de `arranque.celda()` (ver `cargar_clave_groq`).
    5. `arranque.celda(modulo)`: entorno, datos y orden de los modulos.

    Devuelve la corrida.
    """
    from amparo.ejecucion import arranque, corridas
    os.chdir(RAIZ)
    c = corridas.nueva(modulo)
    print("raiz:", RAIZ)
    print("datos:", c.meta["datos"])
    if sello:
        verificar_sello()
    cargar_clave_groq(pedir_por_teclado=pedir_clave)
    arranque.celda(modulo)
    return c
