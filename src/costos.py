"""
Qué cuesta cada brazo (ROADMAP #12).

La tabla de M3 comparaba calidad y latencia media, y con eso no se puede
decidir nada. El brazo 4 tarda 8.24 s por caso contra ~0 del brazo 1, y eso no
es un detalle de implementación: es la conclusión. Un sistema que acierta tres
puntos más y cuesta veinte veces más no es "mejor", es otra elección.

Tres cosas que la media sola esconde:

  - la MEDIANA frente a la media. El agente hace entre 1 y 5 pasos según el
    caso, así que su distribución de latencia tiene cola. La media la arrastran
    los casos que agotan el presupuesto; la p50 dice lo que pasa normalmente.
  - las LLAMADAS REALES frente a las de caché. Una segunda corrida sale entera
    de caché y parece gratis. El coste real es el de la primera.
  - los TOKENS. Es lo que se factura y lo que topa el cupo de la API. Dos
    brazos con la misma latencia pueden diferir en un orden de magnitud si uno
    mete 5 fragmentos de contexto en cada llamada.

Lo que NO se mide y hay que decirlo: el coste en dinero. Depende de la tarifa
del proveedor, que cambia, y de si se corre en el crédito gratuito. Los tokens
quedan registrados para que el cálculo se pueda hacer con la tarifa que
corresponda.
"""
from __future__ import annotations
import time


class Costos:
    """Contador de coste de un brazo. Cada sistema tiene uno.

    `registrar` se llama una vez por llamada al modelo. `cacheada=True` cuenta
    la llamada pero no su latencia ni sus tokens: una respuesta de caché no
    consumió nada, y promediarla hacia abajo haría parecer barato un sistema
    que no lo es.
    """

    def __init__(self, etiqueta: str = ""):
        self.etiqueta = etiqueta
        self.llamadas_reales = 0
        self.llamadas_cache = 0
        self.segundos: list[float] = []
        self.tokens_entrada = 0
        self.tokens_salida = 0
        self.sin_usage = 0          # llamadas reales cuya API no reportó usage
        # De donde salieron los tokens: `api_usage` si los facturó la API,
        # `tokenizador` si los contó el tokenizador de un modelo local. La
        # tabla de costes no puede presentar las dos como la misma cifra sin
        # decirlo.
        self.fuentes_tokens: set[str] = set()
        self.casos = 0

    def nuevo_caso(self) -> None:
        self.casos += 1

    def registrar(self, segundos: float | None = None, usage=None,
                  cacheada: bool = False,
                  tokens: tuple[int, int] | None = None,
                  fuente_tokens: str | None = None) -> None:
        """Una llamada al modelo. `tokens` es para los modelos LOCALES.

        POR QUE HACEN FALTA DOS CAMINOS

        `usage` solo existe si la llamada fue a una API. Los brazos 2 y 3 de M3
        corren sobre el adaptador LOCAL con `model.generate()`, que no devuelve
        ningun `usage`: en m3/20261019T173316Z salieron con
        `llamadas_sin_usage: 90` y `tokens_por_caso: null`. Eso no era un fallo
        de contabilidad --- era la verdad, no habia nada que contar --- pero
        dejaba la tabla de costes sin la mitad de las filas.

        Los tokens de un modelo local SI se pueden contar: el tokenizador los
        da exactos. Asi que se aceptan por `tokens=(entrada, salida)` y se
        registra DE DONDE salieron en `fuente_tokens`. Dos fuentes distintas
        para la misma cifra se tienen que poder distinguir: lo que la API
        factura y lo que el tokenizador cuenta no son necesariamente iguales,
        y sumarlas sin decirlo seria inventar una precision que no hay.
        """
        if cacheada:
            self.llamadas_cache += 1
            return
        self.llamadas_reales += 1
        if segundos is not None:
            self.segundos.append(segundos)
        if tokens is not None:
            ent, sal = tokens
            self.tokens_entrada += int(ent or 0)
            self.tokens_salida += int(sal or 0)
            self.fuentes_tokens.add(fuente_tokens or "sin_declarar")
            return
        if usage is None:
            self.sin_usage += 1
            return
        # Los SDK no coinciden en los nombres; se intentan los dos usuales y
        # si no aparece ninguno se cuenta como `sin_usage` en vez de sumar 0,
        # que se leería como "esta llamada no gastó tokens".
        ent = (getattr(usage, "prompt_tokens", None)
               or getattr(usage, "input_tokens", None))
        sal = (getattr(usage, "completion_tokens", None)
               or getattr(usage, "output_tokens", None))
        if ent is None and sal is None:
            self.sin_usage += 1
            return
        self.tokens_entrada += int(ent or 0)
        self.tokens_salida += int(sal or 0)
        self.fuentes_tokens.add("api_usage")

    # ------------------------------------------------------------------
    def _pct(self, q: float) -> float | None:
        if not self.segundos:
            return None
        s = sorted(self.segundos)
        return round(s[min(len(s) - 1, int(q * (len(s) - 1)))], 3)

    def resumen(self) -> dict:
        n = self.casos or 1
        tot = self.tokens_entrada + self.tokens_salida
        return {
            "etiqueta": self.etiqueta,
            "casos": self.casos,
            "llamadas_reales": self.llamadas_reales,
            "llamadas_cache": self.llamadas_cache,
            "llamadas_por_caso": round(self.llamadas_reales / n, 2),
            "latencia_p50": self._pct(0.50),
            "latencia_p95": self._pct(0.95),
            "latencia_media": (round(sum(self.segundos) / len(self.segundos), 3)
                               if self.segundos else None),
            "latencia_total_s": round(sum(self.segundos), 1) if self.segundos else None,
            "tokens_entrada": self.tokens_entrada,
            "tokens_salida": self.tokens_salida,
            # None, no 0, cuando ninguna llamada reportó `usage`. Un 0 se lee
            # como "este brazo no gastó tokens" y lo cierto es "no se pudieron
            # contar": `generar` es una clausura del notebook y no devuelve el
            # usage de la API.
            "tokens_por_caso": (round(tot / n, 1) if tot
                                else (None if self.sin_usage else 0)),
            "llamadas_sin_usage": self.sin_usage,
            # De donde salieron los tokens. `api_usage` es lo que la API
            # factura; `tokenizador` es lo que el tokenizador cuenta en un
            # modelo local. Comparar un brazo que corre en la API contra uno
            # que corre en GPU local por su cuenta de tokens solo tiene
            # sentido si se sabe que no es la misma medicion.
            "fuente_tokens": (sorted(self.fuentes_tokens)
                              if self.fuentes_tokens else None),
        }


def tabla(sistemas: list, ruta_json=None) -> list[dict]:
    """Compara el coste de varios brazos. Acepta cualquier objeto con `costos`.

    Un brazo sin instrumentar --- el brazo 1 son predicciones ya calculadas por
    M1, no hay llamada que medir --- aparece con sus campos en None en vez de
    en 0. Un 0 ahí se leería como "es gratis", y lo correcto es "no se midió
    aquí": su coste es el de la corrida de M1.
    """
    filas = []
    for s in sistemas:
        c = getattr(s, "costos", None)
        etq = getattr(s, "etiqueta", "?")
        if c is None:
            filas.append({"etiqueta": etq, "casos": None,
                          "llamadas_reales": None, "latencia_p50": None,
                          "latencia_p95": None, "tokens_por_caso": None,
                          "nota": "sin instrumentar en este modulo"})
            continue
        r = c.resumen()
        r["etiqueta"] = etq
        filas.append(r)
    if ruta_json is not None:
        import json
        from pathlib import Path
        Path(ruta_json).write_text(json.dumps(filas, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
    return filas


def imprimir(filas: list[dict]) -> None:
    print(f"\n{'=' * 86}\n  COSTE POR BRAZO\n{'=' * 86}")
    print(f"  {'brazo':<30}{'casos':>6}{'llam.':>7}{'l/caso':>8}"
          f"{'p50 s':>8}{'p95 s':>8}{'tok/caso':>10}")
    print("  " + "-" * 82)
    for f in filas:
        def v(k, fmt="{}"):
            x = f.get(k)
            return "   n/d" if x is None else fmt.format(x)
        print(f"  {f['etiqueta'][:29]:<30}{v('casos'):>6}"
              f"{v('llamadas_reales'):>7}{v('llamadas_por_caso'):>8}"
              f"{v('latencia_p50'):>8}{v('latencia_p95'):>8}"
              f"{v('tokens_por_caso'):>10}")
    print("  " + "-" * 82)
    cache = sum(f.get("llamadas_cache") or 0 for f in filas)
    sinu = sum(f.get("llamadas_sin_usage") or 0 for f in filas)
    if cache:
        print(f"  {cache} llamadas salieron de cache: no cuentan ni latencia ni "
              f"tokens.")
    if sinu:
        print(f"  {sinu} llamadas reales sin `usage` en la respuesta: sus tokens "
              f"no estan contados.")
        # DOS EJES, NO UNA COLUMNA.
        #
        # Los brazos que generan con el modelo local no devuelven `usage`
        # porque no hay API que lo devuelva: su coste es tiempo de GPU, no
        # tokens facturados. Poner `n/d` en la columna de tokens es correcto,
        # pero leer la tabla como si un brazo fuera "mas barato" que otro
        # compara cosas distintas. En m3/20261016T215955Z los brazos 2 y 3
        # tenian 90 llamadas sin usage cada uno --- todas --- y el brazo 4
        # gastaba 9148 tokens por caso de un modelo de 120B.
        print("  Esos brazos NO son mas baratos: su coste es tiempo de GPU y")
        print("  esta en la columna de latencia. Los tokens solo se facturan en")
        print("  los brazos que llaman a una API, asi que las dos columnas son")
        print("  dos ejes distintos y no se suman.")
    print("  n/d = no se midio aqui. El brazo 1 son predicciones de M1: su coste")
    print("  es el de esa corrida, no cero.")
    print("=" * 86)


class Cronometro:
    """`with Cronometro() as t: ...` y luego `t.segundos`."""

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.segundos = time.perf_counter() - self._t0
        return False
