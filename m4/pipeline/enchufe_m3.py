"""
T7 · El enchufe real: `responder_m3` deja de ser un sustituto.

QUE BRAZO DE M3 SE ENCHUFA, Y POR QUE ESE

Se enchufa el brazo **4 · agente + reglas** de `notebooks/M3_rag.ipynb`, armado
exactamente como alli: el agente busca en el corpus (el RAG de la rama 3.5),
extrae HECHOS del relato y el motor del art. 6 (`src/reglas.py`) decide el
mecanismo. Tres razones, por orden de peso:

  1. ES EL MISMO PATRON QUE M4. El VLM extrae hechos del documento y no decide
     derecho; el agente extrae hechos del relato y tampoco. Enchufar un brazo
     que GENERA el mecanismo (1, 2 o 3) mezclaria dos decisiones juridicas,
     la del VLM leyendo y la del decoder escribiendo, y el delta no se podria
     atribuir a ninguna.
  2. CABE EN UNA T4 JUNTO AL VLM. El agente razona por la API de Groq y el
     indice usa un codificador pequeno. Los brazos 1-3 necesitan el LoRA de
     Qwen2.5-7B en GPU, y 7B + Qwen2-VL-2B no caben juntos en 15 GB.
  3. ES EL QUE MEJOR AGUANTA LAS TRAMPAS: gana el estrato adversarial de M3 y
     tiene alucinacion normativa 0 por construccion, porque el fundamento lo
     pone la regla. Un documento mal leido es, para M3, un relato con trampa.

Lo que NO es: el mejor brazo en el agregado. Ese es el 1 (fine-tuned solo).
La tabla de delta compara contra la fila del brazo 4, no contra el mejor, y
el README de entrega tiene que decirlo.

QUE SE REPRODUCE DE M3 Y DE DONDE SALE

Nada se escribe a mano si M3 ya lo decidio y lo publico:

  - el chunking es el que eligio la regla de M3 (`results/m3_chunking.json`);
  - la estrategia de recuperacion del agente es `reranked`, k=4, con la
    reescritura simple de consulta: son los argumentos literales con los que
    `M3_rag.ipynb` construye el brazo 4;
  - el nombre del brazo es el de `results/m3_scorecard.csv`, para que
    `tabla_desde_disco()` encuentre su fila.

Si M3 vuelve a correr y cambia su eleccion de chunking, esto la sigue. Si el
nombre del brazo cambia, `comprobar_brazo()` falla ANTES de gastar GPU.

`src/` no se toca: se importa. Es intocable porque `corridas.version_codigo()`
hashea sus bytes y un cambio aqui desacoplaria a M4 de las corridas de M3.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

# El nombre EXACTO de la fila en results/m3_scorecard.csv (con el punto medio).
SISTEMA_M3 = "4 · agente + reglas"

# Los argumentos con los que M3_rag.ipynb construye el brazo 4 (celda de los
# brazos): `agente.Agente(cliente, indice, estrategia="reranked", k=4,
# transformador=tr, ...)`.
ESTRATEGIA = "reranked"
K = 4

RUTA_CHUNKING = RAIZ / "results" / "m3_chunking.json"
RUTA_M3_SCORECARD = RAIZ / "results" / "m3_scorecard.csv"


def chunking_de_m3(ruta: Path = RUTA_CHUNKING):
    """El troceado que eligio la regla de M3, no uno escrito aqui.

    Devuelve (nombre, funcion). Las funciones son las mismas que mapea el
    diccionario `CONFIGS` de `M3_rag.ipynb`.
    """
    import rag
    configs = {
        "articulo (nuestro)": rag.trocear,
        "fijo 400/60": rag.trocear_fijo,
        "fijo 900/120": lambda d: rag.trocear_fijo(d, 900, 120),
    }
    elegido = json.loads(ruta.read_text(encoding="utf-8"))["elegido"]
    if elegido not in configs:
        raise KeyError(
            f"m3_chunking.json eligio {elegido!r}, que este enchufe no sabe "
            f"construir. Los conocidos: {sorted(configs)}.")
    return elegido, configs[elegido]


def comprobar_brazo(sistema: str = SISTEMA_M3, ruta: Path = RUTA_M3_SCORECARD) -> dict:
    """La fila de M3 contra la que se medira el delta. Falla antes de la GPU."""
    with ruta.open(encoding="utf-8", newline="") as f:
        filas = {r["sistema"]: r for r in csv.DictReader(f)}
    if sistema not in filas:
        raise KeyError(f"{sistema!r} no esta en {ruta.name}: {sorted(filas)}")
    return filas[sistema]


def construir_responder_m3(cliente=None, *, indice=None, transformador=None,
                           cache_dir: Path | str = RAIZ / "runs" / "cache" / "m4",
                           verbose: bool = False):
    """Devuelve `responder_m3(relato) -> str` sobre el brazo 4 real, y el agente.

    `cliente`, `indice` y `transformador` se pueden inyectar para probarlo sin
    red ni modelos (`m4/tests/test_enchufe.py`). En Colab no se pasa nada: el
    cliente sale de `GROQ_API_KEY` y el indice se construye del corpus.

    El agente se devuelve aparte porque sus `trazas` y `contadores` dicen QUE
    hizo M3 con lo que leyo el VLM (que herramientas, que hechos, que regla
    cerro), y eso es lo que permite explicar el peor caso.
    """
    import agente
    import rag

    comprobar_brazo()
    if cliente is None:
        from groq import Groq
        clave = os.environ.get("GROQ_API_KEY")
        if not clave:
            raise RuntimeError(
                "Falta GROQ_API_KEY: el brazo 4 razona por la API de Groq. En "
                "Colab: icono de la llave -> GROQ_API_KEY -> acceso al notebook.")
        cliente = Groq(api_key=clave)
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    if indice is None:
        nombre, trocear = chunking_de_m3()
        chunks = trocear(rag.cargar_corpus())
        indice = rag.Indice(chunks, verbose=verbose).construir()
        if verbose:
            print(f"indice: {len(chunks)} chunks con el chunking {nombre!r} de M3")
    if transformador is None:
        transformador = rag.TransformadorConsulta(
            cliente=cliente, cache=str(cache_dir / "consultas.json"), verbose=verbose)
    ag = agente.Agente(cliente, indice, estrategia=ESTRATEGIA, k=K,
                       transformador=transformador,
                       cache_path=str(cache_dir / "agente.json"),
                       etiqueta=SISTEMA_M3, verbose=verbose)

    def responder_m3(relato: str) -> str:
        return ag(relato)

    return responder_m3, ag
