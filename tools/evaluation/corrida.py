"""Identidad de una corrida: que se reusa de un checkpoint y que no.

## El fallo que cierra

`evaluate()` del notebook guarda cada respuesta a Drive y, si el archivo ya
existe, sigue desde ahi. Sus guardas comprobaban tres cosas -- que no haya mas
registros que ejemplos, que los ids coincidan y que esten los campos del
esquema vigente -- y **ninguna mira de que corrida salieron esas respuestas.**

La validacion son siempre los mismos 334 ids. Asi que un `finetuned_results.jsonl`
de la corrida anterior, con otro adaptador y otro dataset, pasa las tres guardas
y se reusa entero: la comparacion baseline/afinado saldria de dos modelos
distintos y **nada falla**. Es el peor modo de fallo posible, porque produce un
numero creible.

## Que ata una corrida

Seis cosas, y basta que cambie una para que los resultados no sean comparables:

| campo | por que |
|---|---|
| `huella_dataset` | otro dataset es otro entrenamiento |
| `commit` | el codigo que calcula las metricas cambio |
| `model_id` | modelo base distinto |
| `revision_base` | el mismo repo de HF sirve otro peso si se publico un commit |
| `adaptador` | el nombre del adaptador que se entrena |
| `estado` | **`base` o `afinado`**: el notebook llama a `evaluate()` dos veces con el MISMO objeto `model`, antes y despues de entrenar. Sin esto, el baseline y el afinado comparten identidad |

El `corrida_id` sale del hash de esas seis mas la fecha, asi que dos corridas
con la misma configuracion el mismo dia **comparten directorio y se reanudan**,
que es lo que se quiere cuando Colab se desconecta. Dos con cualquier diferencia
no se tocan.

## Lo que NO hace

No borra nada. Si la identidad no coincide, **se detiene**; no limpia el
directorio ajeno ni lo sobrescribe. Decidir que hacer con los resultados de otra
corrida es del que la corrio.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

# El archivo que marca un directorio de resultados como propiedad de una
# corrida. Se escribe una vez, al empezar, y a partir de ahi manda.
NOMBRE_FIRMA = "corrida.json"

ESTADOS = ("base", "afinado")

# Los campos que tienen que coincidir para reusar un checkpoint. `estado` entra
# aparte, por checkpoint, porque un mismo directorio tiene el del baseline y el
# del afinado.
CAMPOS_IDENTIDAD = ("huella_dataset", "commit", "model_id", "revision_base",
                    "adaptador")


def huella_directorio(ruta) -> str | None:
    """sha256 del contenido de un directorio, igual en cualquier sistema.

    Las rutas se ordenan por su forma posix **sensible a mayusculas** y los
    saltos se normalizan a LF. Las dos cosas importan: `sorted()` sobre objetos
    `Path` es insensible a mayusculas en Windows y da otro orden que en Linux, y
    un archivo de texto con CRLF da otro hash con el mismo contenido. Las dos
    hicieron fallar una comprobacion de huella antes.
    """
    p = Path(ruta)
    if not p.is_dir():
        return None
    h = hashlib.sha256()
    archivos = sorted((f for f in p.rglob("*") if f.is_file()),
                      key=lambda f: f.relative_to(p).as_posix())
    for f in archivos:
        h.update(f.relative_to(p).as_posix().encode("utf-8"))
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]


def _commit(raiz=None) -> str:
    import subprocess

    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=raiz,
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except Exception:
        return "desconocido"


def firma(huella_dataset: str, model_id: str, adaptador: str,
          revision_base: str | None = None, raiz=None,
          hoy: str | None = None) -> dict:
    """La identidad de esta corrida, con su `corrida_id`.

    `revision_base` **es `None` si no se pudo resolver**, nunca un mensaje de
    error: un texto ahi se guardaria en el manifiesto como si fuera una
    revision verificada. `revision_verificada` lo dice explicitamente.
    """
    datos = {
        "huella_dataset": huella_dataset,
        "commit": _commit(raiz),
        "model_id": model_id,
        "revision_base": revision_base or None,
        "revision_verificada": bool(revision_base),
        "adaptador": adaptador,
        "fecha": hoy or date.today().isoformat(),
    }
    semilla = json.dumps({k: datos[k] for k in (*CAMPOS_IDENTIDAD, "fecha")},
                         sort_keys=True, ensure_ascii=False)
    datos["corrida_id"] = (f"{datos['fecha'].replace('-', '')}-"
                           f"{hashlib.sha256(semilla.encode()).hexdigest()[:8]}")
    return datos


def escribir(directorio, f: dict) -> Path:
    """Deja la firma en el directorio. Si ya hay una, **no la pisa**: la valida."""
    d = Path(directorio)
    d.mkdir(parents=True, exist_ok=True)
    ruta = d / NOMBRE_FIRMA
    if ruta.exists():
        verificar_firma(leer(d), f, str(ruta))
        return ruta
    ruta.write_text(json.dumps(f, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    return ruta


def leer(directorio) -> dict | None:
    ruta = Path(directorio) / NOMBRE_FIRMA
    if not ruta.exists():
        return None
    return json.loads(ruta.read_text(encoding="utf-8"))


def diferencias(guardada: dict, actual: dict) -> list[str]:
    """Campos de identidad que no coinciden, legibles."""
    return [f"{c}: el checkpoint dice {guardada.get(c)!r} y esta corrida "
            f"es {actual.get(c)!r}"
            for c in CAMPOS_IDENTIDAD if guardada.get(c) != actual.get(c)]


def verificar_firma(guardada: dict | None, actual: dict, donde: str) -> None:
    """Se detiene si la firma guardada no es la de esta corrida."""
    if guardada is None:
        raise SystemExit(
            f"{donde} tiene resultados pero no {NOMBRE_FIRMA}: no se sabe de que "
            f"corrida salieron. Son de antes de que existiera la firma. Muevelos "
            f"a otro sitio (no los borres) y vuelve a empezar.")
    malas = diferencias(guardada, actual)
    if malas:
        raise SystemExit(
            f"{donde} es de OTRA corrida y reusarlo mezclaria dos modelos en una "
            f"sola cifra:\n  - " + "\n  - ".join(malas) +
            f"\n\nNo se borra nada. Usa otro directorio o mueve esos resultados.")


def exigir_revision(revision: str | None) -> str:
    """La revision del modelo base, o se detiene.

    Por que es un error y no un aviso. Sin `revision` fijada, Hugging Face
    sirve lo que apunte `main`, y `main` **puede cambiar sin que cambie nada de
    la firma**: mismo dataset, mismo commit, mismo adaptador, mismo
    `corrida_id`, y otros pesos debajo. Un checkpoint guardado ayer se reusaria
    hoy contra un modelo base distinto sin que nada falle.

    Una corrida experimental que no se puede reproducir no sirve para decidir
    si se adopta un adaptador, que es justo para lo que se hace.
    """
    if not revision:
        raise SystemExit(
            "No se pudo resolver la revision del modelo base.\n\n"
            "Sin revision fijada se baja lo que apunte main, que puede cambiar "
            "sin que cambie la firma de la corrida: dos corridas con el mismo "
            "corrida_id podrian tener pesos base distintos.\n\n"
            "Reintenta cuando huggingface_hub responda. Si decides correr igual "
            "-- sabiendo que la corrida NO es reproducible y que no podra "
            "reanudarse -- pon EXIGIR_REVISION = False en el notebook.")
    return revision


def ruta_meta(directorio, estado: str) -> Path:
    return Path(directorio) / f"{estado}.meta.json"


def registrar_adaptador(directorio, estado: str, huella: str | None) -> None:
    """Deja la huella de los pesos junto a los resultados de ese estado.

    Si ya hay una y es otra, **se detiene**: son pesos distintos y sus
    respuestas no se pueden juntar en una sola cifra.
    """
    ruta = ruta_meta(directorio, estado)
    if ruta.exists():
        previa = json.loads(ruta.read_text(encoding="utf-8")).get("huella_adaptador")
        if previa != huella:
            raise SystemExit(
                f"{ruta} dice que los resultados de '{estado}' son del adaptador "
                f"{previa!r} y los pesos actuales son {huella!r}.\n\n"
                f"Es el caso que la firma de la corrida NO detecta: misma "
                f"configuracion, misma etiqueta de adaptador y mismo dia, pero "
                f"un entrenamiento distinto. Reusar esos resultados mezclaria "
                f"dos modelos.\n\nNo se borra nada: usa otro directorio.")
        return
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"huella_adaptador": huella}, ensure_ascii=False,
                               indent=2) + "\n", encoding="utf-8", newline="\n")


def verificar_checkpoint(directorio, actual: dict, estado: str,
                         n_esperado: int | None = None,
                         huella_adaptador: str | None = None) -> list[dict]:
    """Los resultados reusables de `<directorio>/<estado>_results.jsonl`.

    Devuelve [] si no hay nada que reusar. Se detiene -- no borra, no sigue --
    si lo que hay es de otra corrida o de otros pesos.

    `huella_adaptador` es **obligatoria para `afinado`**. El `corrida_id`
    identifica la configuracion del entrenamiento, no su resultado: dos
    entrenamientos con la misma configuracion el mismo dia dan el mismo
    `corrida_id` y **pesos distintos**, porque basta que cambie el orden de un
    lote o la version de una libreria. Sin esta comprobacion, el segundo
    reusaria el `afinado_results.jsonl` parcial del primero.
    """
    if estado not in ESTADOS:
        raise SystemExit(f"estado {estado!r} no esta en {ESTADOS}")
    if estado == "afinado" and not huella_adaptador:
        raise SystemExit(
            "evaluar 'afinado' exige la huella del adaptador entrenado: sin ella "
            "no se puede saber si unos resultados guardados son de ESTOS pesos.")
    d = Path(directorio)
    ruta = d / f"{estado}_results.jsonl"
    if not ruta.exists():
        registrar_adaptador(d, estado, huella_adaptador)
        return []
    firma_guardada = leer(d)
    verificar_firma(firma_guardada, actual, str(ruta))
    if not (firma_guardada or {}).get("revision_base"):
        raise SystemExit(
            f"{ruta} se genero sin una revision inmutable del modelo base, asi "
            f"que no hay forma de saber si los pesos base son los mismos de hoy. "
            f"No se reusa.")
    registrar_adaptador(d, estado, huella_adaptador)
    filas = [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines()
             if l.strip()]
    if n_esperado is not None and len(filas) > n_esperado:
        raise SystemExit(
            f"{ruta} tiene {len(filas)} registros y la validacion {n_esperado}.")
    return filas


def guardar_adaptador(origen, destino) -> str:
    """Copia el adaptador a `destino`, que **no puede existir**, y da su huella.

    Sin `dirs_exist_ok`. La version anterior copiaba con `dirs_exist_ok=True`
    sobre una ruta que solo dependia de la etiqueta y la fecha, asi que una
    segunda corrida el mismo dia **borraba el adaptador de la primera**. Ya
    paso: el adaptador del 27 de septiembre se perdio asi.
    """
    import shutil

    d = Path(destino)
    if d.exists():
        raise SystemExit(
            f"{d} ya existe y no se sobrescribe. Si vienes a reanudar la "
            f"evaluacion, NO reentrenes: carga ese adaptador y sigue. Si quieres "
            f"otro entrenamiento, usa otra ruta -- el adaptador de ahi es el "
            f"unico ejemplar de su corrida.")
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(origen, d)
    return huella_directorio(d)


def resumen(f: dict) -> str:
    rev = f.get("revision_base")
    return (f"corrida {f['corrida_id']}\n"
            f"  dataset   {f['huella_dataset']}\n"
            f"  commit    {f['commit']}\n"
            f"  modelo    {f['model_id']}\n"
            f"  revision  {rev if rev else 'NO RESUELTA -- no se presenta como verificada'}\n"
            f"  adaptador {f['adaptador']}")
