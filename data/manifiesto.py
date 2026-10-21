"""
Huella de todos los archivos del proyecto, para comprobar que Drive y el
disco local tienen LO MISMO.

POR QUE HACE FALTA

Los notebooks montan Drive y leen el proyecto desde ahi. Si un archivo quedo
sin sincronizar, Colab corre con el codigo VIEJO y el fallo no se parece a un
fallo de sincronizacion: se parece a un resultado. Una corrida de 55 minutos
sobre `src/` desactualizado produce cifras perfectamente plausibles y
perfectamente inservibles, y nada en la salida lo delata.

La celda de arranque (`src/arranque.py`) comprueba que los archivos EXISTAN.
Esto comprueba que sean los MISMOS, que es otra cosa: un `metricas.py` viejo
existe igual de bien que el nuevo.

COMO SE USA

    # en la maquina local
    python -I data/manifiesto.py > manifiesto_local.txt

    # en Colab, en una celda, despues de montar Drive
    !python -I /content/drive/MyDrive/agenteAmparo/data/manifiesto.py

Si las dos huellas `_TOTAL` coinciden, Drive esta al dia. Si no, la salida
lista que archivo difiere, y con `--comparar` se le pasa el manifiesto de la
otra maquina y dice exactamente cuales:

    python -I data/manifiesto.py --comparar manifiesto_de_colab.txt
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Lo que el proyecto necesita para correr. Se excluyen `runs/` y `results/`,
# que son SALIDA: sincronizarlos no hace falta y compararlos daria diferencias
# legitimas entre una corrida y otra.
PATRONES = ("src/*.py", "data/*.py", "data/*.json", "notebooks/*.ipynb")
EXCLUIR = {"reverificacion_corpus.json", "acuerdo_anotadores.json",
           "calibracion_juez.json",
           # Auditorias DERIVADAS del corpus y los eval sets. Van en `data/`
           # porque son propiedades de los datos, no de una corrida, pero no
           # pueden entrar en la huella: correr una auditoria la moveria.
           "cobertura_corpus.json",
           # Esta importa mas que las otras. `diagnostico_cumplimiento.json`
           # incluye la lectura de `agente_trazas.json`, que existe solo si ya
           # corrio M3. Si entrara en la huella, correr el diagnostico entre
           # M1 y M3 les daria huellas de codigo distintas --- y
           # `verificar_entrega.py` marcaria que no son el mismo experimento
           # por una razon que no tiene nada que ver con el codigo.
           "diagnostico_cumplimiento.json",
           # Salida de `validar_extractor.py`. Tercera vez que un artefacto
           # DERIVADO se cuela en la huella: correr el validador hacia que la
           # siguiente comprobacion del manifiesto denunciara su propia
           # salida y bloqueara el arranque. La prueba 33 ya no deja que se
           # olvide un cuarto.
           "validacion_extractor.json",
           # Salida de `descomponer_baseline.py`, que lee
           # `results/m1_predicciones.json`. Cuarta vez que un artefacto
           # DERIVADO entra en `data/`: si estuviera en la huella, descomponer
           # el baseline entre M1 y M2 les daria huellas distintas y
           # `verificar_entrega.py` diria que no son el mismo experimento por
           # una razon que no tiene nada que ver con el codigo.
           "descomposicion_baseline.json",
           # Salida de `validacion_juez.py --leer`, que lee
           # `results/m2_scorecard_por_caso.csv`. QUINTA vez. Esta es la mas
           # facil de pasar por alto porque PARECE una anotacion humana ---
           # como `revision_abogado_v3.json`, que si esta en la huella y debe
           # estarlo --- y no lo es: aquella depende solo del eval set, y esta
           # depende de una CORRIDA. Leer la validacion del juez entre M2 y M3
           # les daria huellas de codigo distintas.
           "validacion_juez.json",
           # Salida de `validacion_juez.py --simular`. Depende de una
           # CORRIDA igual que la anterior, y ademas es una simulacion:
           # si entrara en la huella, probar la tuberia contaria como
           # cambiar el codigo.
           "validacion_juez_simulacion.json",
           # Salida de `Agente.determinismo_extractor`. Son 20 llamadas
           # a la API, no una corrida, y se puede repetir cuando se
           # quiera: si entrara en la huella, medir el ruido del
           # extractor contaria como cambiar el codigo.
           "determinismo_extractor.json",
           # Salida de `auditar_causas_abiertas.py` y de la medicion del
           # acuerdo entre familias. Las dos leen `results/`, asi que
           # dependen de una CORRIDA: si entraran en la huella,
           # establecer la causa de un defecto contaria como cambiar el
           # codigo. Septima y octava vez.
           "causas_abiertas.json",
           "acuerdo_entre_familias.json",
           # Mediciones hechas EN LOCAL contra la API, no por un
           # notebook: la resolucion del juez con la sonda nueva y el
           # contraste con la libreria `ragas`. Dependen de `results/`,
           # asi que valen lo mismo que las demas derivadas.
           "determinismo_juez_lote.json",
           "ragas_libreria_local.json",
           # Salida de `medir_metricas_nuevas.py`: metricas anadidas
           # DESPUES de la corrida y recalculadas de sus predicciones.
           # Lee `results/`, asi que depende de una corrida.
           "metricas_posteriores.json",
           # Casos de entrenamiento PROPUESTOS por `pares_minimos.py`.
           # No son datos del experimento todavia --- no estan en
           # `dataset.json` --- y regenerarlos no puede mover la huella
           # de la corrida que ya se entrego.
           "pares_minimos_propuestos.json",
           # Una hipotesis sobre el RAG, probada y refutada. Lee
           # `results/` y se puede repetir: no puede mover la huella.
           "hipotesis_rag_refutada.json"}
"""Salidas de los verificadores y de las auditorias: cambian solas, no
afectan a una corrida, y meterlas en la huella haria que mirar los datos
contara como cambiar el codigo."""

EXCLUIR_PREFIJO = ("acuerdo_anotadores_",)
"""Lo mismo, por prefijo: hay un artefacto por anotador y la lista no se
puede enumerar de antemano. Medir una anotacion no puede mover la huella del
codigo --- es el mismo fallo que ya se corrigio con las auditorias."""


def _canonico(p: Path) -> bytes:
    """Los bytes que de verdad deciden una corrida.

    POR QUE UN NOTEBOOK NO SE PUEDE HASHEAR TAL CUAL

    Colab reescribe el `.ipynb` cada vez que ejecutas una celda, metiendo las
    `outputs` dentro. Medido: `M1_finetuning.ipynb` pesa 79 392 bytes limpio y
    **368 903** despues de una corrida --- el mismo codigo. Un manifiesto que
    los incluya grita en cuanto haces lo que tienes que hacer, y un guardian
    que se dispara solo deja de ser un guardian.

    La salida de una celda no cambia lo que la corrida calcula; el codigo de
    la celda si. Asi que se hashea el notebook SIN `outputs` ni
    `execution_count`: detecta una celda editada e ignora el ruido de haberla
    corrido.
    """
    b = p.read_bytes()
    if p.suffix != ".ipynb":
        return b
    try:
        nb = json.loads(b)
    except Exception:                                      # noqa: BLE001
        return b          # si no es JSON valido, se hashea crudo y se vera
    for celda in nb.get("cells", []):
        celda.pop("outputs", None)
        celda.pop("execution_count", None)
        # `id` es de nbformat 4.5 y Colab lo REGENERA al abrir el notebook,
        # sin que nadie edite nada. Medido: abrir M1 cambio su huella en 20
        # bytes y nos hizo parar una corrida para investigarlo. Un guardian
        # que se dispara al no hacer nada ensena a ignorarlo, y eso es peor
        # que no tenerlo.
        celda.pop("id", None)
        # `metadata` de celda acumula ids de ejecucion de Colab.
        celda["metadata"] = {}
        # EL SALTO DE LINEA FINAL TAMPOCO CUENTA. Pegar una celda en Colab le
        # anade `\n` al final del `source`, que en el JSON son DOS bytes.
        # Medido: M3 se nego a arrancar porque `M2_harness.ipynb` daba 48257
        # en vez de 48255 --- dos bytes de espacio en blanco que no cambian
        # ninguna cifra --- y costo una ronda de subida. Es ruido de la misma
        # clase que las `outputs` y los ids, asi que se normaliza igual: una
        # celda editada sigue moviendo la huella; pegarla, no.
        if isinstance(celda.get("source"), list) and celda["source"]:
            celda["source"] = [ln for ln in celda["source"]]
            celda["source"][-1] = celda["source"][-1].rstrip("\r\n")
            if not celda["source"][-1]:
                celda["source"].pop()
    nb.pop("metadata", None)
    return json.dumps(nb, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def manifiesto() -> list[tuple[str, int, str]]:
    out = []
    for pat in PATRONES:
        for p in sorted(RAIZ.glob(pat)):
            if (p.name in EXCLUIR or p.name.startswith("_")
                    or any(p.name.startswith(x) for x in EXCLUIR_PREFIJO)):
                continue
            b = _canonico(p)
            out.append((str(p.relative_to(RAIZ)).replace("\\", "/"),
                        len(b), hashlib.sha256(b).hexdigest()[:16]))
    return out


def total(m: list[tuple[str, int, str]]) -> str:
    crudo = "".join(f"{n}:{h}" for n, _, h in m)
    return hashlib.sha256(crudo.encode()).hexdigest()[:16]


def leer(ruta: str) -> dict[str, tuple[int, str]]:
    d = {}
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        partes = linea.split()
        if len(partes) == 3 and not linea.startswith(("#", "_TOTAL")):
            d[partes[0]] = (int(partes[1]), partes[2])
    return d


SELLO = "subida_sellada.txt"
"""Lo que `preparar_subida.py --sellar` declara que esta subido.

POR QUE EL NOTEBOOK COMPARA CONTRA ESTO Y NO IMPRIME Y CONFIA

La celda que corre esto en Colab imprimia la huella y le pedia a quien mira
que la comparase con la del disco local. Tres fallos de una sola sesion
vinieron de ahi: una celda que no se subio, una que se subio a medias, y una
huella que no cuadraba y se arranco igual. Pedirle a una persona que compare
dos cadenas de 16 hex antes de gastar una A100 es pedirle que haga el trabajo
de un `assert`.

El sello viaja con el proyecto --- lo sube quien sube los archivos --- asi que
en Drive esta el manifiesto de lo que DEBERIA haber. Si lo que hay no coincide,
este script lo dice y sale con 1, nombrando el archivo. No hay nada que
comparar a ojo.

El sello es `.txt`, que no esta en `PATRONES`, asi que no forma parte de la
huella que certifica: no hay circularidad.
"""


def contra_sello() -> int:
    """0 si lo que hay coincide con el sello. 1 si no. 2 si no hay sello."""
    ruta = RAIZ / "data" / SELLO
    m = manifiesto()
    if not ruta.exists():
        print(f"_TOTAL  {sum(t for _, t, _ in m)} bytes  {total(m)}")
        print(f"(sin {SELLO}: no hay nada contra lo que comparar. Corre "
              "`python -I data/preparar_subida.py --sellar` en local y subelo.)")
        return 2
    esperado = leer(str(ruta))
    mio = {n: (t, h) for n, t, h in m}
    difieren = sorted(set(mio) | set(esperado))
    difieren = [n for n in difieren if mio.get(n) != esperado.get(n)]
    print(f"_TOTAL  {sum(t for _, t, _ in m)} bytes  {total(m)}")
    if not difieren:
        print(f"COINCIDE con {SELLO}: {len(mio)} archivos, todos al dia.")
        return 0
    print()
    print("=" * 70)
    print(f"  NO ARRANQUES: {len(difieren)} archivo(s) no coinciden con el sello")
    print("=" * 70)
    for n in difieren:
        a, b = mio.get(n), esperado.get(n)
        if a is None:
            print(f"  {n:<44} falta AQUI (esta en el sello)")
        elif b is None:
            print(f"  {n:<44} esta aqui y no en el sello")
        else:
            print(f"  {n:<44} DISTINTO ({a[0]} vs {b[0]} bytes)")
    print()
    print("  Sube los que salen arriba y vuelve a correr esta celda.")
    print("  Una corrida con estos archivos desincronizados produce cifras")
    print("  plausibles e inservibles, y nada en la salida lo delata.")
    print("=" * 70)
    return 1


def main() -> int:
    if "--contra-sello" in sys.argv:
        return contra_sello()
    m = manifiesto()
    if "--comparar" in sys.argv:
        otro = leer(sys.argv[sys.argv.index("--comparar") + 1])
        mio = {n: (t, h) for n, t, h in m}
        difieren = [n for n in sorted(mio.keys() | otro.keys())
                    if mio.get(n) != otro.get(n)]
        print(f"archivos aqui: {len(mio)} · en el otro manifiesto: {len(otro)}")
        if not difieren:
            print("\nIDENTICOS. Drive y el disco local tienen lo mismo.")
            return 0
        print(f"\n{len(difieren)} archivo(s) DIFIEREN:\n")
        for n in difieren:
            a, b = mio.get(n), otro.get(n)
            if a is None:
                print(f"  {n:<42} solo en el otro")
            elif b is None:
                print(f"  {n:<42} FALTA alla  <- hay que subirlo")
            else:
                print(f"  {n:<42} distinto ({a[0]} vs {b[0]} bytes)"
                      f"  <- hay que subirlo")
        print("\nUna corrida con estos archivos desincronizados produce cifras")
        print("plausibles e inservibles, y nada en la salida lo delata.")
        return 1

    print(f"# manifiesto de {RAIZ.name} · {len(m)} archivos")
    print("# los .ipynb se hashean SIN `outputs`: Colab los reescribe al "
          "ejecutar")
    print(f"# {'archivo':<44}{'bytes':>9}  sha256[:16]")
    for n, t, h in m:
        print(f"{n:<46}{t:>9}  {h}")
    print(f"_TOTAL  {sum(t for _, t, _ in m)} bytes  {total(m)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
