"""Correr y medir los brazos de M3 (antes: celdas 16, 28, 38 y 41 de
`notebooks/M3_rag.ipynb`).

Lo que aqui vive dejo de mutar variables globales del notebook: `correr_brazo`
devuelve salidas, latencia y fallos en un `ResultadoBrazo`, y quien llama
decide donde guardarlos (el pipeline los mete en su checkpoint).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from amparo.nucleo import schema


# --------------------------------------------------------------------------
# El costo de la transformacion de consulta, repartido por brazo (celda 16)
# --------------------------------------------------------------------------
class CostoPorBrazo:
    """Envuelve un transformador para tres cosas:

    1. DARLE `.costo()`. `evaluar_recuperacion` lo llama siempre, y los brazos
       de multiconsulta y HyDE no reciben el objeto sino un lambda y un metodo
       enlazado, que no lo tienen: AttributeError a mitad de la evaluacion.

    2. REPARTIR EL COSTO. Los tres brazos con transformacion comparten el
       mismo `tr`, cuyos contadores son acumulativos. Sin esto, el brazo de
       multiconsulta reportaria su costo mas el del anterior, y el de HyDE los
       tres juntos: numeros inflados con apariencia de medidos.

    3. CRONOMETRAR AQUI, que uniformiza. `multiples()` no registraba latencia
       y el brazo salia con latencia None, pareciendo gratis siendo el que
       hace una llamada EXTRA por caso, y el que gano la comparacion. Midiendo
       en el envoltorio, los tres se cronometran igual.

    Se cronometra SOLO cuando hubo llamada real (subio `dueno.llamadas`):
    mezclar los aciertos de cache bajaria la media por una razon falsa.
    """

    def __init__(self, fn, dueno, reloj=time.perf_counter):
        self._fn, self._d, self._reloj = fn, dueno, reloj
        self._llamadas0 = dueno.llamadas
        self._fallos0 = dueno.fallos
        self._usos = 0
        self._lat: list[float] = []

    def __call__(self, relato):
        n0 = self._d.llamadas
        t0 = self._reloj()
        out = self._fn(relato)
        ms = (self._reloj() - t0) * 1000
        self._usos += 1
        if self._d.llamadas > n0:
            self._lat.append(ms)
        return out

    def costo(self) -> dict:
        L = sorted(self._lat)
        reales = self._d.llamadas - self._llamadas0
        return {
            "llamadas_reales": reales,
            "desde_cache": self._usos - reales,
            "fallos": self._d.fallos - self._fallos0,
            "latencia_ms_media": round(sum(L) / len(L), 1) if L else None,
            "latencia_ms_p95": round(L[int(0.95 * (len(L) - 1))], 1) if L else None,
            "transformaciones": self._usos,
        }


def transformador_para(elegida: str, tr):
    """La estrategia y la transformacion que el brazo 3 tiene que desplegar.

    Devuelve `(estrategia, transformador, nombre)`. El brazo 3 tiene que
    desplegar LA TECNICA QUE GANO, no una parecida: `SistemaRAG` hace
    `self.transformador(relato)`, asi que pasar `tr` a secas invoca la
    reescritura simple. Si la ganadora fue multiconsulta o HyDE, se desplegaba
    una configuracion DISTINTA de la medida, y eso rompe justo la cadena que
    M3 existe para demostrar: comparar, elegir, desplegar.
    """
    estrategia = elegida.split(" + ")[0]
    if "multiconsulta" in elegida:
        return estrategia, (lambda r: tr.multiples(r, 3)), "multiconsulta (3)"
    if "hyde" in elegida:
        return estrategia, tr.hyde, "hyde"
    if "reescritura" in elegida or "transformacion" in elegida:
        return estrategia, tr, "reescritura simple"
    return estrategia, None, "ninguna"


# --------------------------------------------------------------------------
# Correr un brazo (celda 28)
# --------------------------------------------------------------------------
@dataclass
class ResultadoBrazo:
    salidas: dict[str, str]
    latencia_s: float                       # segundos por caso, de punta a punta
    fallos: list[dict] = field(default_factory=list)


def reloj_legible(seg: float) -> str:
    m, s = divmod(int(seg), 60)
    return f"{m}m{s:02d}s" if m else f"{s}s"


def correr_brazo(sis, nombre: str, casos: list[dict], reloj=time.perf_counter) -> ResultadoBrazo:
    """Corre un brazo sobre todos los casos, con ETA y sin morirse en el intento.

    - ETA. Los brazos tardan entre 6 y 10 minutos y la linea de progreso no
      decia cuanto faltaba: no habia forma de distinguir "va lento" de "se
      colgo" sin esperar hasta el final.
    - Tolerar un fallo de API. Un 400 de Groq en UN caso tumbaba el brazo
      entero, y con el los brazos anteriores que estaban en memoria. El caso
      que falla queda con salida VACIA ---no con una respuesta por defecto, que
      entraria en las metricas como si el sistema hubiera contestado algo--- y
      se cuenta aparte, para leer el numero del brazo sabiendo cuantos casos
      no se pudieron medir.
    """
    out, fallos, t0 = {}, [], reloj()
    n = len(casos)
    for i, e in enumerate(casos, 1):
        try:
            out[e["id"]] = sis(e["relato"])
        except Exception as ex:                       # noqa: BLE001
            fallos.append({"id": e["id"], "error": type(ex).__name__,
                           "detalle": str(ex)[:200]})
            out[e["id"]] = ""
        transcurrido = reloj() - t0
        eta = transcurrido / i * (n - i)
        print(f"  {nombre}: {i}/{n} · {transcurrido / i:.1f} s/caso · "
              f"transcurrido {reloj_legible(transcurrido)} · ETA {reloj_legible(eta)}   ",
              end="\r", flush=True)
    total = reloj() - t0
    latencia = total / n if n else 0.0
    print(f"  {nombre}: {n}/{n} listo · {latencia:.1f} s/caso · "
          f"total {reloj_legible(total)} · {len(fallos)} fallos de API      ")
    for f in fallos:
        print(f"     FALLO {f['id']}: {f['error']} · {f['detalle']}")
    return ResultadoBrazo(out, latencia, fallos)


# --------------------------------------------------------------------------
# Costos (celda 41)
# --------------------------------------------------------------------------
class BrazoNoMedido:
    """Un brazo sin coste medible AQUI. El brazo 1 son predicciones de M1:
    `costos.tabla` lo muestra con sus campos en None, no en 0, porque un 0 se
    leeria como "es gratis" y su coste es el de la corrida de M1."""

    def __init__(self, etiqueta: str = "1 · fine-tuned solo (M1)"):
        self.etiqueta = etiqueta


# --------------------------------------------------------------------------
# La matriz por caso y brazo, y el techo de combinarlos (celda 38)
# --------------------------------------------------------------------------
def matriz_por_caso(brazos: dict[str, dict[str, str]], eval_set: list[dict],
                    ids: list[str] | None = None) -> list[dict]:
    """De donde salen los agregados: una fila por caso con lo que dijo cada brazo.

    Sin esto no se puede responder «que casos acierta un brazo que otro
    falla», y esa es la pregunta que define el techo de cualquier combinacion
    de brazos. No es una metrica nueva: es la materia prima que ya se calcula
    y se tiraba al agregar. `acierta` es la conjuncion que usa
    `acierto_juridico`: mecanismo Y procedencia.
    """
    por_id = {e["id"]: e for e in eval_set}
    ids = ids if ids is not None else [e["id"] for e in eval_set]
    filas = []
    for i in ids:
        e = por_id[i]
        fila = {"id": i, "tipo": e.get("tipo"), "categoria": e.get("categoria"),
                "dificultad": e.get("dificultad"),
                "gold_mecanismo": e.get("mecanismo"), "brazos": {}}
        for nombre, salidas_por_id in brazos.items():
            if i not in salidas_por_id:
                continue
            pred = schema.parse_salida(salidas_por_id[i])
            fila["brazos"][nombre] = {
                "mecanismo": pred.get("mecanismo"),
                "procede": pred.get("procede"),
                "acierta": (pred.get("mecanismo") == e.get("mecanismo")
                            and bool(pred.get("procede")) == bool(e.get("procede"))),
                "fundamento": pred.get("fundamento"),
            }
        filas.append(fila)
    return filas


def techo_union(por_caso: list[dict]) -> dict:
    """Cuantos casos acierta ALGUN brazo, frente al mejor brazo suelto.

    Es una COTA SUPERIOR y no un resultado: la daria un enrutador perfecto,
    que nadie tiene. Si el margen es cero, ninguna combinacion de estos brazos
    puede superar al mejor suelto y construir la compuerta seria tiempo perdido.
    """
    nombres = sorted({b for f in por_caso for b in f["brazos"]})
    por_brazo = {n: sum(1 for f in por_caso if f["brazos"].get(n, {}).get("acierta"))
                 for n in nombres}
    union = sum(1 for f in por_caso if any(v.get("acierta") for v in f["brazos"].values()))
    mejor = max(por_brazo.values()) if por_brazo else 0
    n = len(por_caso)
    return {"n": n, "por_brazo": por_brazo, "union": union,
            "margen_sobre_el_mejor": round((union - mejor) / n, 4) if n else 0.0}
