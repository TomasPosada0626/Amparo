"""
Celda de arranque de los notebooks: orden de ejecucion y prueba de humo
(ROADMAP #31 y #33).

POR QUE EXISTE, CON LO QUE COSTO NO TENERLA

Los tres notebooks tardan 7, 3 y 45 minutos y necesitan A100, API de Groq y
Drive montado. En esta sesion reventaron cuatro veces, y las cuatro por cosas
que se detectan en dos segundos ANTES de gastar nada:

  - un choque de versiones de torchao, despues de descargar 15 GB de pesos;
  - Drive sin montar, que aparecia como "no encuentro el proyecto" --- el
    sintoma, no la causa;
  - un `KeyError: 'recuperados'` en la celda 28 de M3, con los 45 minutos de
    los cuatro brazos ya gastados;
  - un 400 de Groq en un caso, que tumbaba el brazo de 61 entero.

Esto no evita los fallos de modelo ni de API. Evita los de ENTORNO, que son
los que no deberian costar una corrida.

QUE COMPRUEBA, Y POR QUE NO LANZA EXCEPCION

Devuelve un informe y un veredicto. No aborta: un notebook que se mata en la
primera celda no deja ver QUE falta, y la lista completa de lo que falla vale
mas que el primer error. Quien llama decide, y la celda de arranque de cada
notebook hace `assert`.

    import arranque
    arranque.celda("m1")      # imprime el orden y la prueba de humo
"""
from __future__ import annotations
import importlib
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# ROADMAP #33: el orden de ejecucion, dicho en el sitio donde importa.
# --------------------------------------------------------------------------
ORDEN = {
    "m1": {
        "posicion": "PRIMERO",
        "entorno": "GPU (A100 recomendada)",
        "duracion": "~30 min: ~10 de entrenamiento con gradient_checkpointing, ~4 de las dos generaciones por lotes, y ~14 del brazo hibrido, que genera caso a caso (lote 1) para no falsear la latencia que mide `costos`",
        # GROQ_API_KEY es OPCIONAL en M1 --- el entrenamiento y las dos
        # generaciones no la usan --- pero la seccion 6, la de redaccion, si.
        # No estaba declarada, asi que `arranque.celda("m1")` no aviso y la
        # seccion se salto entera con la clave bien puesta en los secretos.
        "necesita": ["Drive montado", "data/ en el proyecto", "GROQ_API_KEY"],
        "produce": [
                    # LA EVIDENCIA DEL TOKENIZADOR SE PUBLICA.
                    #
                    # `fertilidad_tokenizadores` y `cobertura_clasificador` se
                    # generaban en cada corrida y se quedaban en `runs/`. Son
                    # justo la evidencia empirica que pide el criterio de
                    # seleccion del modelo base --- "comportamiento del
                    # tokenizador sobre el dominio" --- y quien lea `results/`
                    # no las veia nunca. Medir algo y no publicarlo cuesta lo
                    # mismo que no medirlo.
                    "results/m1_fertilidad_tokenizadores.json",
                    "results/m1_cobertura_clasificador.json",
                    "results/m1_predicciones.json",
                    "results/m1_scorecard_base.json",
                    "results/m1_scorecard_finetuned.json",
                    "results/m1_hiperparametros.json",
                    "results/m1_seleccion_checkpoint.json",
                    "results/m1_scorecard_hibrido.json",
                    "results/m1_extractor.json",
                    "results/m1_degeneracion.json",
                    "results/m1_estabilidad.json",
                    "results/m1_redaccion.json"],
        "nota": "M2 y M3 leen `m1_predicciones.json`. Si M1 no corre, los "
                "otros dos no tienen de donde partir.",
    },
    "m2": {
        "posicion": "SEGUNDO",
        "entorno": "CPU basta",
        "duracion": "~3 min",
        "necesita": ["results/m1_predicciones.json", "GROQ_API_KEY"],
        "produce": ["results/m2_scorecard_base.json",
                    "results/m2_scorecard_finetuned.json",
                    "results/m2_sesgos.json",
                    "results/m2_scorecard_por_caso.csv",
                    "results/scorecard_baseline.csv",
                    "results/m2_acuerdo_entre_jueces.json",
                    "results/m2_sesgo_autopreferencia.json",
                    "results/m2_determinismo_juez.json",
                    "results/m2_estabilidad.json",
                    "results/m2_rouge_vs_acierto.json"],
        "nota": "Cambiar de GPU a CPU reinicia la sesion de Colab y vuelve a "
                "pedir el montaje de Drive. Es esperado.",
    },
    "m3": {
        "posicion": "TERCERO",
        "entorno": "GPU (A100 recomendada)",
        "duracion": "~45 min",
        "necesita": ["results/m1_predicciones.json", "GROQ_API_KEY",
                     "data/corpus.json"],
        "produce": ["results/m3_scorecard.csv", "results/m3_retrieval.json",
                    "results/m3_ragas.json", "results/m3_chunking.json",
                    "results/m3_agente.json", "results/m3_cruce.csv",
                    "results/m3_costos.json",
                    "results/m3_scorecard_comunes.csv",
                    "results/m3_scorecards_comunes.json",
                    "results/m3_ganadores.json",
                    "results/m3_decision_retrieval.json",
                    "results/m3_ragas_libreria.json",
                    # LA EVIDENCIA DEL MAYOR DEFECTO ABIERTO SE PUBLICA.
                    #
                    # `agente_trazas.json` se guardaba solo en la carpeta de
                    # la corrida. ROADMAP3 · M3-1 pide leerlo para establecer
                    # que hechos extrae el agente en los 8 casos de
                    # `accion_cumplimiento` --- es la unica evidencia que
                    # puede zanjar el defecto --- y una evidencia que no
                    # viaja con la entrega es una evidencia que no existe
                    # para quien la lea. Mismo criterio que D-4.
                    "results/m3_agente_trazas.json"],
        "nota": "No depende de M2. Guarda checkpoint entre brazos, asi que un "
                "fallo en el brazo 4 no se lleva los anteriores.",
    },
}

# Lo que tiene que existir antes de empezar, pase lo que pase.
DATOS = ("dataset.json", "eval_set.json", "eval_set_v2.json",
         "eval_set_v3.json", "eval_set_m3.json", "corpus.json",
         "normas.json")


def _en_colab() -> bool:
    return "google.colab" in sys.modules or Path("/content").is_dir()


def humo(modulo: str) -> dict:
    """ROADMAP #31: comprueba el entorno ANTES de gastar nada."""
    modulo = modulo.lower()
    cfg = ORDEN.get(modulo)
    fallos, avisos, ok = [], [], []

    if cfg is None:
        fallos.append(f"modulo desconocido: {modulo!r}. Usa m1, m2 o m3.")
        return {"ok": False, "fallos": fallos, "avisos": avisos, "pasa": ok}

    # --- los datos ----------------------------------------------------
    for n in DATOS:
        p = RAIZ / "data" / n
        if p.exists():
            ok.append(f"data/{n}")
        else:
            fallos.append(f"falta data/{n}")

    # --- los modulos propios ------------------------------------------
    for m in ("schema", "metricas", "corridas", "reglas"):
        try:
            importlib.import_module(m)
            ok.append(f"import {m}")
        except Exception as ex:                        # noqa: BLE001
            fallos.append(f"no importa {m}: {type(ex).__name__}: {ex}")

    # --- lo que pide este modulo --------------------------------------
    for req in cfg["necesita"]:
        if req == "GROQ_API_KEY":
            if os.environ.get("GROQ_API_KEY"):
                ok.append("GROQ_API_KEY presente")
            else:
                fallos.append("GROQ_API_KEY no esta en el entorno. En Colab va "
                              "en los secretos, con acceso para el notebook.")
        elif req.startswith("results/"):
            p = RAIZ / req
            if p.exists():
                ok.append(req)
            else:
                fallos.append(f"falta {req}: corre {'M1' if 'm1_' in req else 'el modulo anterior'} primero")
        elif req == "Drive montado":
            if _en_colab():
                if Path("/content/drive/MyDrive").is_dir():
                    ok.append("Drive montado")
                else:
                    fallos.append("Drive NO esta montado. Es un fallo de "
                                  "autorizacion, no del proyecto.")
            else:
                avisos.append("fuera de Colab: no se comprueba Drive")

    # --- GPU, solo si el modulo la pide -------------------------------
    if "GPU" in cfg["entorno"]:
        try:
            import torch
            if torch.cuda.is_available():
                ok.append(f"GPU: {torch.cuda.get_device_name(0)}")
            else:
                avisos.append("sin GPU disponible: este modulo va a tardar "
                              "mucho mas, o no caber en memoria")
        except ImportError:
            fallos.append("torch no esta instalado")

    # --- choques de version, que es lo que mas caro salio -------------
    try:
        import torch
        import transformers
        ok.append(f"torch {torch.__version__} / "
                  f"transformers {transformers.__version__}")
        try:
            import torchao                              # noqa: F401
            avisos.append("torchao esta instalado: en esta sesion choco con "
                          "transformers y tumbo la corrida DESPUES de bajar "
                          "15 GB de pesos. Si falla el entrenamiento, "
                          "desinstalalo.")
        except ImportError:
            ok.append("torchao ausente (bien: choca con transformers)")
    except ImportError:
        if "GPU" in cfg["entorno"]:
            fallos.append("torch/transformers no estan instalados")

    return {"ok": not fallos, "fallos": fallos, "avisos": avisos, "pasa": ok}


def celda(modulo: str, estricto: bool = True) -> dict:
    """Lo que la celda de arranque del notebook llama. Imprime y devuelve."""
    modulo = modulo.lower()
    cfg = ORDEN.get(modulo, {})
    print("=" * 72)
    print(f"  ARRANQUE · {modulo.upper()}   ({cfg.get('posicion', '?')} "
          f"de los tres)")
    print("=" * 72)
    if cfg:
        print(f"  entorno   : {cfg['entorno']}")
        print(f"  duracion  : {cfg['duracion']}")
        print(f"  necesita  : {', '.join(cfg['necesita'])}")
        print(f"  produce   : {len(cfg['produce'])} artefactos en results/")
        print(f"\n  {cfg['nota']}")
    print("\n  orden de los tres modulos:")
    for m, c in ORDEN.items():
        marca = " <-- estas aqui" if m == modulo else ""
        print(f"    {c['posicion']:<8} {m.upper():<4} {c['entorno']:<26}"
              f"{c['duracion']}{marca}")

    r = humo(modulo)
    print(f"\n  prueba de humo: {len(r['pasa'])} comprobaciones pasan")
    for a in r["avisos"]:
        print(f"    AVISO  {a}")
    for f in r["fallos"]:
        print(f"    FALLA  {f}")
    print("=" * 72)
    if r["fallos"]:
        print(f"  {len(r['fallos'])} problema(s) de ENTORNO. Arreglarlos cuesta")
        print("  segundos; descubrirlos a mitad de la corrida cuesta la corrida.")
    else:
        print("  entorno listo.")
    print("=" * 72)
    if estricto and r["fallos"]:
        raise SystemExit(
            f"El entorno de {modulo.upper()} no esta listo: "
            + " | ".join(r["fallos"]))
    return r


# --------------------------------------------------------------------------
# ROADMAP #32: checkpoint entre brazos de M3.
# --------------------------------------------------------------------------
def _procedencia() -> dict:
    """Con que codigo y que datos se genero lo que hay dentro.

    `runs/cache/` es COMPARTIDA entre corridas a proposito --- ahi viven los
    caches del juez y de las consultas, que conviene reutilizar --- y el
    checkpoint de los brazos acabo en el mismo sitio. Sin sello, se reutiliza
    entre corridas con codigo distinto.
    """
    try:
        from corridas import version_codigo, version_datos
        return {"codigo": version_codigo().get("_conjunto"),
                "datos": {k: (v or {}).get("version")
                          for k, v in version_datos().items()}}
    except Exception:                                      # noqa: BLE001
        # Sin procedencia, el checkpoint se comporta como antes: se usa. Es
        # preferible a que un fallo al sellar tumbe una corrida de 45 minutos.
        return {}


def guardar_checkpoint(ruta, datos: dict) -> None:
    """Guarda lo que ya se calculo, para que un fallo no se lo lleve.

    El fallo del brazo 4 casi se llevo 18 minutos de trabajo de los brazos 2 y
    3, que estaban solo en memoria. Un brazo que ya corrio es un hecho: no
    tiene por que depender de que el siguiente no reviente.
    """
    datos = dict(datos)
    datos["_procedencia"] = _procedencia()
    p = Path(ruta)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    tmp.replace(p)          # atomico: o esta el viejo o esta el nuevo


def cargar_checkpoint(ruta) -> dict:
    """Lo que haya, o {} si no hay nada o si es de OTRO codigo. Nunca lanza.

    EL DESCARTE POR PROCEDENCIA, Y LAS TRES CORRIDAS QUE LO EXIGEN

    `runs/cache/brazos_checkpoint.json` es compartido entre corridas, y en
    m3/20261017T001359Z, .../011043Z y .../024911Z sirvio las salidas de una
    corrida ANTERIOR al arreglo del prompt del agente. Las tres parecian
    correctas: `scorecard.csv` salia con sus cuatro filas y sus `n` bien,
    mientras `agente_resumen.json` decia `casos: 0` y el cruce salia vacio ---
    porque el checkpoint restaura las SALIDAS pero no las TRAZAS.

    Reutilizar salidas generadas con otro codigo es un cambio de vara dentro
    de la misma tabla, que es justo lo que `verificar_entrega.py` existe para
    detectar. El remedio no puede ser "acuerdate de borrar un archivo": eso
    fallo tres veces. Se descarta solo.
    """
    p = Path(ruta)
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:                                  # noqa: BLE001
        # Un checkpoint corrupto no puede tumbar la corrida: se ignora y se
        # recalcula, que es lo que habria pasado sin checkpoint.
        return {}

    guardada = d.pop("_procedencia", None)
    actual = _procedencia()
    if guardada is None:
        print("  checkpoint SIN sello de procedencia (de antes de este "
              "control): se descarta por precaucion.")
        return {}
    if actual and guardada != actual:
        print("  checkpoint DESCARTADO: se genero con otro codigo o con otros "
              "datos.")
        print(f"     guardado: codigo {guardada.get('codigo')}")
        print(f"     actual  : codigo {actual.get('codigo')}")
        if guardada.get("datos") != actual.get("datos"):
            print(f"     datos guardados: {guardada.get('datos')}")
            print(f"     datos actuales : {actual.get('datos')}")
        print("  Reutilizarlo mezclaria brazos de dos codigos en una tabla.")
        return {}
    return d
