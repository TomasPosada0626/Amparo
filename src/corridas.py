"""
Artefactos por corrida: nada se sobrescribe, todo queda fechado y trazable.

EL PROBLEMA QUE RESUELVE
    Hasta la v1 cada notebook escribia `runs/m3_scorecard.csv` y la corrida
    siguiente lo pisaba. Eso tiene tres consecuencias malas:

      - no se puede PROBAR reproducibilidad, porque no quedan dos corridas que
        comparar, y "resultados identicos entre corridas" es un criterio
        explicito del harness;
      - no queda registro de con QUE version de los datos se midio. Paso de
        verdad: M2 se corrio contra el eval set anterior a la correccion de
        A09 y solo se noto comparando fechas de archivos en Drive;
      - un numero viejo y un numero nuevo quedan indistinguibles.

COMO SE USA

    import corridas
    c = corridas.nueva("m3")                     # runs/m3/<id>/ + corrida.json
    c.guardar_json("retrieval", resultados)
    c.guardar_csv("scorecard", filas)
    c.publicar("retrieval", "results/m3_retrieval.json")   # copia canonica
    c.cerrar(valida=True)

QUE ES CADA CARPETA

    runs/<modulo>/<id>/   artefactos CRUDOS de esa corrida. Inmutables.
    runs/cache/           caches del juez, de las consultas y de la generacion.
                          COMPARTIDOS entre corridas a proposito: versionarlos
                          por corrida destruiria la reproducibilidad que dan.
    results/              copias canonicas de lo que se entrega. Estas SI se
                          sobrescriben, deliberadamente, porque representan el
                          estado actual del proyecto; cada una registra de que
                          corrida salio.
    models/               pesos (adaptador LoRA). Fuera de las corridas porque
                          pesan y no cambian en cada evaluacion.

EL FLAG `valida`
    `cerrar(valida=False, ...)` marca una corrida como no concluyente. Existe
    porque un script que termina sin lanzar excepcion no es evidencia de una
    evaluacion valida: si todas las herramientas fallan y el codigo atrapa las
    excepciones, el scorecard sale completo, plausible y sin sentido.
"""
from __future__ import annotations
import csv
import json
import os
import platform
import shutil
import sys
from datetime import datetime, timedelta, timezone

# Colombia, UTC-5, sin horario de verano desde 1993. Se usa un desplazamiento
# FIJO y no `zoneinfo` a proposito: `zoneinfo` necesita la base tzdata, que no
# esta en todas las imagenes de Windows, y un fallo de importacion aqui
# tumbaria el arranque de una corrida por una cuestion de presentacion.
BOGOTA = timezone(timedelta(hours=-5), "America/Bogota")


def ahora_bogota(dt=None) -> str:
    """La misma hora, escrita en Bogota. Para que la lea una persona."""
    dt = dt or datetime.now(timezone.utc)
    return dt.astimezone(BOGOTA).isoformat(timespec="seconds")
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SEMILLA = 42

# CUBLAS_WORKSPACE_CONFIG SE PONE AL IMPORTAR, Y ESO ES DELIBERADO.
#
# cuBLAS lee esta variable cuando crea su handle --- en la primera
# multiplicacion de matrices --- y no vuelve a mirarla. Ponerla despues no da
# error: no hace nada, que es peor.
#
# El sitio natural seria la celda que siembra (`sembrar()`, mas abajo), y ahi
# llega tarde: `Corrida.__init__` llama a `hardware()`, que llama a
# `get_device_properties(0)`, que inicializa CUDA. Esa celda es la PRIMERA del
# notebook, doce antes de la que siembra. Asi que la variable tiene que estar
# puesta antes de que alguien importe este modulo para otra cosa, y el unico
# momento garantizado es el import.
#
# Un efecto de import que toca `os.environ` se mira con razon de reojo. La
# alternativa era confiar en que una linea quede en la celda correcta de tres
# notebooks, que es exactamente la clase de orden que este proyecto ya tuvo
# que atar con una prueba (la 68). Es inocuo donde no hay GPU: M2 y M3 corren
# en CPU y contra una API, y la variable solo la lee cuBLAS.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

LIBRERIAS = ("torch", "transformers", "peft", "datasets", "accelerate",
             "sentence_transformers", "numpy", "sklearn", "groq", "ragas",
             "rank_bm25", "pandas")


# --------------------------------------------------------------------------
def versiones() -> dict:
    """Versiones de lo que de verdad esta importado, no de un requirements."""
    import importlib
    out = {"python": platform.python_version(), "plataforma": platform.platform()}
    for nombre in LIBRERIAS:
        try:
            mod = importlib.import_module(nombre)
            out[nombre] = getattr(mod, "__version__", "sin __version__")
        except Exception:
            out[nombre] = None
    return out


def hardware() -> dict:
    out = {"gpu": None, "memoria_gpu_mb": None}
    try:
        import torch
        if torch.cuda.is_available():
            out["gpu"] = torch.cuda.get_device_name(0)
            out["memoria_gpu_mb"] = round(
                torch.cuda.get_device_properties(0).total_memory / 1024**2)
    except Exception:
        pass
    return out


def sembrar(semilla: int = SEMILLA, determinista: bool = True) -> dict:
    """Siembra el azar Y pide kernels deterministas. Devuelve lo que consiguio.

    POR QUE NO BASTA CON LA SEMILLA, Y QUE NUMERO LO DICE

    M1 ya sembraba `random`, `numpy` y `torch`, y aun asi dos corridas con los
    mismos datos, el mismo codigo y la misma semilla pueden dar artefactos
    distintos. La semilla fija de donde salen los numeros aleatorios; no fija
    el ORDEN en que la GPU los suma. cuBLAS elige su algoritmo de reduccion
    segun el workspace que tenga libre y cuDNN "autotunea" la convolucion en
    la primera llamada, asi que la misma operacion en bf16 puede acumular en
    dos ordenes distintos --- y en coma flotante sumar en otro orden da otro
    numero. Sobre 7 000 millones de parametros, esa diferencia se propaga
    hasta cambiar un token generado, que es un campo distinto en el scorecard.

    La generacion ya es greedy (`do_sample=False` en las dos celdas que
    generan), asi que el muestreo no es la causa y esto es lo que queda.

    LOS CUATRO INTERRUPTORES, Y EL LIMITE DE CADA UNO

      CUBLAS_WORKSPACE_CONFIG   ya la pone el import de este modulo, que es
                                el unico momento garantizado (ver la nota
                                junto a `SEMILLA`). Aqui solo se COMPRUEBA, y
                                se comprueba con una medida conservadora:
                                `cublas_a_tiempo` dice si CUDA todavia no
                                estaba inicializado, lo que basta para
                                afirmar que llego a tiempo. Al reves no
                                concluye: cuBLAS cachea la variable cuando
                                crea su handle, en la primera matmul, que
                                puede no haber ocurrido aun. Asi que un False
                                es "no se puede afirmar", no "llego tarde".
      cudnn.deterministic       obliga a cuDNN a usar kernels reproducibles.
      cudnn.benchmark = False   le quita el autotune, que es lo que hace que
                                la primera llamada elija algoritmo sola.
      use_deterministic_algorithms   la red de seguridad: hace fallar (o
                                avisar) cualquier op sin kernel determinista.

    `warn_only=True` ES UNA DECISION, NO UN DESCUIDO. Con `warn_only=False`
    una sola op sin kernel determinista --- y en un `Trainer` con atencion
    SDPA hay varias --- levanta `RuntimeError` y se lleva por delante un
    entrenamiento de 50 minutos de A100. Con `True` avisa y usa el kernel no
    determinista. Eso es MENOS determinismo, y el dict que se devuelve lo dice
    para que `corrida.json` lo registre: "pedido" no es "conseguido", y
    `estabilidad` se tiene que poder leer sabiendo cual de los dos fue.

    LO QUE ESTO NO ARREGLA: dos corridas en GPUs DISTINTAS. Los flags fijan el
    algoritmo, no el hardware; una A100 y una L4 pueden diferir igual. Por eso
    `hardware()` viaja en la misma meta.
    """
    import os
    import random
    estado = {"semilla": semilla, "determinista_pedido": determinista}

    random.seed(semilla)
    try:
        import numpy as np
        np.random.seed(semilla)
        estado["numpy"] = True
    except Exception:                                      # noqa: BLE001
        estado["numpy"] = False

    try:
        import torch
    except Exception:                                      # noqa: BLE001
        estado["torch"] = False
        return estado
    estado["torch"] = torch.__version__

    torch.manual_seed(semilla)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(semilla)

    if not determinista:
        return estado

    # La variable ya esta puesta desde el import; aqui se comprueba y se
    # registra, que es lo que permite leer `estabilidad` despues.
    ya = torch.cuda.is_available() and torch.cuda.is_initialized()
    estado["cublas_workspace_config"] = os.environ.get(
        "CUBLAS_WORKSPACE_CONFIG")
    estado["cublas_a_tiempo"] = not ya
    if estado["cublas_workspace_config"] not in (":4096:8", ":16:8"):
        estado["aviso_cublas"] = (
            "CUBLAS_WORKSPACE_CONFIG vale "
            f"{estado['cublas_workspace_config']!r}, que no es un valor "
            "determinista. Alguien la cambio despues de importar `corridas`.")
    elif ya:
        estado["aviso_cublas"] = (
            "CUDA ya estaba inicializado al llamar a sembrar(), asi que no se "
            "puede AFIRMAR que la variable llegara antes de la primera matmul "
            "(cuBLAS la cachea al crear su handle). El import de `corridas` "
            "la pone antes que nada, asi que lo normal es que si; esto queda "
            "registrado para no afirmar lo que no se comprobo.")

    try:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        estado["cudnn_deterministic"] = True
    except Exception as ex:                                # noqa: BLE001
        estado["cudnn_deterministic"] = f"no se pudo: {type(ex).__name__}"

    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
        estado["use_deterministic_algorithms"] = "True (warn_only)"
    except Exception as ex:                                # noqa: BLE001
        estado["use_deterministic_algorithms"] = f"no se pudo: {type(ex).__name__}"

    estado["lectura"] = (
        "Determinismo PEDIDO, no garantizado: `warn_only=True` deja pasar las "
        "ops sin kernel determinista en vez de tumbar el entrenamiento. Si "
        "`estabilidad.identicas` sale False con mismos datos y mismo codigo, "
        "mirar el hardware de las dos corridas antes de concluir nada.")
    if "aviso_cublas" in estado:
        estado["lectura"] += " OJO: " + estado["aviso_cublas"]
    return estado


def version_codigo() -> dict:
    """Huella de nuestro propio codigo, modulo por modulo.

    POR QUE HACE FALTA
        `versiones()` registra las librerias y `version_datos()` los datos,
        pero el codigo del equipo no quedaba en ninguna parte. Sin eso, la
        comparacion entre corridas no puede distinguir dos causas muy
        distintas de que dos corridas difieran con los mismos datos:
        no-determinismo del hardware, o que cambiamos el codigo en medio.

        No es hipotetico: la corrida m1/20261015T195623Z comparo contra la
        anterior con los mismos datos, salio distinta, y la celda de
        estabilidad aviso de no-determinismo de cuBLAS cuando la causa era que
        habiamos anadido el recorte de la cola degenerada. Una advertencia
        falsa es peor que no avisar, porque manda a buscar donde no hay nada.

        `_conjunto` resume todos los modulos en una sola huella, que es lo que
        la comparacion necesita; los hashes por archivo quedan para saber QUE
        cambio cuando el conjunto no coincide.
    """
    import hashlib
    out = {}
    carpeta = RAIZ / "src"
    if not carpeta.is_dir():
        return {"_conjunto": None}
    for p in sorted(carpeta.glob("*.py")):
        out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    out["_conjunto"] = hashlib.sha256(
        "".join(f"{k}:{v}" for k, v in sorted(out.items())).encode()
    ).hexdigest()[:16]
    return out


def version_datos() -> dict:
    """Que version de cada archivo de datos se uso. Sin esto, dos corridas con
    numeros distintos son indistinguibles de un cambio de datos."""
    out = {}
    # LA VARA QUE SE USA, NO LA QUE SE USABA.
    #
    # Esta tupla tenia `eval_set.json` y no los dos que de verdad se miden.
    # Consecuencia medida: `verificar_entrega.py` compara la version de datos
    # entre los tres modulos para detectar un cambio de vara, y en las
    # corridas del 2026-10-16 los tres declararon `eval_set.json v1.2.0 n=46`
    # --- un archivo que NINGUN modulo usa --- mientras median sobre
    # `eval_set_v2.json`. La comprobacion pasaba por vacio: comparaba una vara
    # que nadie habia tocado.
    #
    # `eval_set.json` se conserva en la lista porque esta congelado y sirve de
    # testigo: si cambia, algo lo esta tocando y no deberia.
    for nombre in ("dataset.json", "eval_set.json", "eval_set_v2.json",
                   "eval_set_v3.json", "eval_set_m3.json",
                   "corpus.json"):
        p = RAIZ / "data" / nombre
        if not p.exists():
            out[nombre] = None
            continue
        try:
            meta = json.loads(p.read_text(encoding="utf-8")).get("meta", {})
            n = meta.get("total_fragmentos")
            if n is None:
                d = json.loads(p.read_text(encoding="utf-8"))
                n = len(d.get("ejemplos") or d.get("documentos") or [])
            out[nombre] = {"version": meta.get("version"), "n": n,
                           "bytes": p.stat().st_size}
        except Exception as ex:
            out[nombre] = {"error": str(ex)[:80]}
    return out


# --------------------------------------------------------------------------
class Corrida:
    def __init__(self, modulo: str, ident: str | None = None, raiz: Path | None = None):
        self.modulo = modulo
        self.raiz = Path(raiz) if raiz else RAIZ
        self.id = ident or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.dir = self.raiz / "runs" / modulo / self.id
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.raiz / "runs" / "cache").mkdir(parents=True, exist_ok=True)
        (self.raiz / "results").mkdir(parents=True, exist_ok=True)

        self.artefactos: dict[str, str] = {}
        # EL ID SIGUE EN UTC, Y NO ES UN DESCUIDO.
        #
        # Es el nombre de la carpeta y el sello que cose M1 con M2 y M3, hay
        # 20 corridas con ese formato, y una `Z` no admite dos lecturas.
        # Cambiarlo a hora local haria que una corrida de las 19:09Z pareciera
        # anterior a una de las 14:09 del mismo dia. Lo que se traduce es lo
        # que lee una persona.
        _t0 = datetime.now(timezone.utc)
        self.inicio = _t0.isoformat(timespec="seconds")
        self.inicio_bogota = ahora_bogota(_t0)
        self.meta = {
            "id": self.id,
            "modulo": modulo,
            "inicio": self.inicio,
            "fin": None,
            "valida": None,
            "notas": [],
            "semilla": SEMILLA,
            "datos": version_datos(),
            "codigo": version_codigo(),
            "versiones": versiones(),
            "hardware": hardware(),
            "artefactos": self.artefactos,
        }
        self._escribir_meta()
        print(f"corrida {modulo}/{self.id} · {self.dir.relative_to(self.raiz)}")

    # -- rutas ----------------------------------------------------------
    @property
    def cache(self) -> Path:
        """Carpeta de caches, compartida entre corridas."""
        return self.raiz / "runs" / "cache"

    def ruta_cache(self, nombre: str) -> str:
        return str(self.cache / nombre)

    # -- escritura ------------------------------------------------------
    def _escribir_meta(self) -> None:
        (self.dir / "corrida.json").write_text(
            json.dumps(self.meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")

    def guardar_json(self, nombre: str, obj) -> Path:
        p = self.dir / f"{nombre}.json"
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8", newline="\n")
        self.artefactos[nombre] = p.name
        self._escribir_meta()
        return p

    def guardar_csv(self, nombre: str, filas: list[dict]) -> Path:
        p = self.dir / f"{nombre}.csv"
        if filas:
            with open(p, "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
                w.writeheader()
                w.writerows(filas)
        self.artefactos[nombre] = p.name
        self._escribir_meta()
        return p

    def guardar_texto(self, nombre: str, texto: str) -> Path:
        p = self.dir / nombre
        p.write_text(texto, encoding="utf-8", newline="\n")
        self.artefactos[nombre] = p.name
        self._escribir_meta()
        return p

    # -- publicacion ----------------------------------------------------
    def publicar(self, nombre: str, destino: str) -> Path:
        """Copia un artefacto de la corrida a `results/` como version canonica.

        La copia lleva de donde salio, para que nunca haya un numero en
        results/ del que no se sepa que corrida lo produjo.
        """
        origen = self.dir / self.artefactos.get(nombre, f"{nombre}.json")
        if not origen.exists():
            raise FileNotFoundError(f"no existe el artefacto '{nombre}' en {self.dir}")
        dst = self.raiz / destino
        dst.parent.mkdir(parents=True, exist_ok=True)

        if origen.suffix == ".json":
            obj = json.loads(origen.read_text(encoding="utf-8"))
            sello = {"_corrida": self.id, "_modulo": self.modulo,
                     "_artefacto": origen.name}
            obj = {**sello, **obj} if isinstance(obj, dict) else {**sello, "datos": obj}
            dst.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8", newline="\n")
        else:
            shutil.copyfile(origen, dst)
            (dst.parent / f"{dst.stem}.corrida.txt").write_text(
                f"{self.modulo}/{self.id}\n", encoding="utf-8", newline="\n")
        print(f"  publicado -> {destino}  (de {self.modulo}/{self.id})")
        return dst

    # -- cierre ---------------------------------------------------------
    def nota(self, texto: str) -> None:
        self.meta["notas"].append(texto)
        self._escribir_meta()

    def registrar(self, clave: str, valor) -> None:
        """Mete un dato en la meta y lo escribe YA, sin esperar a `cerrar`.

        Hace falta para lo que describe la corrida y no es un artefacto --- el
        estado del determinismo, por ejemplo. Asignar a `self.meta` a secas
        tambien funciona, pero solo llega al disco si la corrida llega a
        `cerrar()`, y justo las corridas que se caen a mitad son las que hay
        que poder leer despues.
        """
        self.meta[clave] = valor
        self._escribir_meta()

    def cerrar(self, valida: bool, notas: str | list[str] | None = None) -> dict:
        if notas:
            self.meta["notas"] += [notas] if isinstance(notas, str) else list(notas)
        self.meta["valida"] = bool(valida)
        _t1 = datetime.now(timezone.utc)
        self.meta["fin"] = _t1.isoformat(timespec="seconds")
        self.meta["fin_bogota"] = ahora_bogota(_t1)
        self.meta["inicio_bogota"] = getattr(self, "inicio_bogota", None)
        self.meta["zona_horaria"] = (
            "`id`, `inicio` y `fin` en UTC; `*_bogota` en America/Bogota "
            "(UTC-5, sin horario de verano). El id queda en UTC porque es el "
            "nombre de la carpeta y el sello que une los tres modulos.")
        self._escribir_meta()
        estado = "VALIDA" if valida else "NO VALIDA"
        print(f"corrida {self.modulo}/{self.id} cerrada · {estado}"
              f" · {len(self.artefactos)} artefactos")
        for n in self.meta["notas"]:
            print(f"    nota: {n}")
        return self.meta


# --------------------------------------------------------------------------
def nueva(modulo: str, ident: str | None = None) -> Corrida:
    return Corrida(modulo, ident)


def listar(modulo: str, raiz: Path | None = None) -> list[Path]:
    base = (Path(raiz) if raiz else RAIZ) / "runs" / modulo
    return sorted(p for p in base.glob("*") if p.is_dir()) if base.exists() else []


def ultimas(modulo: str, n: int = 2, raiz: Path | None = None) -> list[Path]:
    return listar(modulo, raiz)[-n:]


def comparar(a: Path | str, b: Path | str, artefacto: str,
             columnas: list[str] | None = None) -> dict:
    """Compara el mismo artefacto en dos corridas. Es la prueba de estabilidad.

    Devuelve `identicas: True` solo si cada fila coincide en las columnas
    comparadas. Si `columnas` es None se comparan todas.
    """
    pa, pb = Path(a), Path(b)

    def cargar(p: Path):
        f_csv, f_json = p / f"{artefacto}.csv", p / f"{artefacto}.json"
        if f_csv.exists():
            with open(f_csv, encoding="utf-8", newline="") as fh:
                return list(csv.DictReader(fh)), "csv"
        if f_json.exists():
            obj = json.loads(f_json.read_text(encoding="utf-8"))
            return (obj if isinstance(obj, list) else [obj]), "json"
        raise FileNotFoundError(f"{artefacto} no esta en {p}")

    fa, tipo = cargar(pa)
    fb, _ = cargar(pb)

    dif = []
    if len(fa) != len(fb):
        dif.append({"motivo": f"distinto numero de filas: {len(fa)} vs {len(fb)}"})
    else:
        cols = columnas or sorted(set(fa[0]) & set(fb[0]))
        for i, (x, y) in enumerate(zip(fa, fb)):
            for c in cols:
                if x.get(c) != y.get(c):
                    dif.append({"fila": i, "columna": c,
                                "corrida_1": x.get(c), "corrida_2": y.get(c)})

    out = {"corrida_1": pa.name, "corrida_2": pb.name, "artefacto": artefacto,
           "tipo": tipo, "n_filas": len(fa), "columnas": columnas or "todas",
           "identicas": not dif, "diferencias": dif[:40]}
    estado = "IDENTICAS" if out["identicas"] else f"{len(dif)} DIFERENCIAS"
    print(f"estabilidad · {artefacto} · {pa.name} vs {pb.name}: {estado}")
    for d in dif[:5]:
        print("   ", d)
    return out
