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
