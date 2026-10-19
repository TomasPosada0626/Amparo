"""Mide la capa de redaccion desde las predicciones ya publicadas de M1.

POR QUE EXISTE: NO HAY QUE GASTAR UNA A100 PARA ESTO

La seccion 6 de M1 mide la capa que convierte el bloque de triaje en lenguaje
natural. No usa la GPU --- el texto lo genera Groq --- pero vive dentro de un
notebook que tarda media hora en entrenar. En la corrida 20261018T070145Z la
seccion se salto entera porque M1 no tenia la celda que copia el secreto de
Colab al entorno: la clave estaba puesta y nadie la leia.

Re-correr M1 por eso seria pagar 30 minutos de A100 por una medicion que solo
necesita el texto que M1 ya publico. `results/m1_predicciones.json` trae la
salida cruda del modelo ajustado para los 69 casos, que es exactamente lo que
la seccion 6 consume.

QUE ESCRIBE, Y POR QUE LO DECLARA

Escribe `results/m1_redaccion.json`, el mismo artefacto que escribiria el
notebook, con dos campos de mas:

  _corrida                       copiado de las predicciones que uso, para
                                 que `verificar_entrega.py` siga viendo un
                                 solo id de corrida en el modulo M1.
  _medido_fuera_de_la_corrida    true, con el motivo.

Lo segundo no es decoracion. Todo lo demas en `results/` lo produjo el
notebook que dice `_corrida`; esto no. Un artefacto que aparenta venir de una
corrida sin venir de ella es el modo de fallo que `verificar_entrega.py`
existe para cazar, asi que se declara en vez de disimularse.

    GROQ_API_KEY=...  python -I data/medir_redaccion.py
    python -I data/medir_redaccion.py --registro abogado
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import redaccion                                           # noqa: E402
import schema                                              # noqa: E402
import sistema                                             # noqa: E402

RUTA_PREDS = RAIZ / "results" / "m1_predicciones.json"
RUTA_OUT = RAIZ / "results" / "m1_redaccion.json"
RUTA_CACHE = RAIZ / "runs" / "cache" / "redaccion_suelta.json"


def _predicciones() -> tuple[list[dict], str]:
    if not RUTA_PREDS.exists():
        print(f"Falta {RUTA_PREDS.relative_to(RAIZ)}: corre M1 primero.")
        raise SystemExit(1)
    d = json.loads(RUTA_PREDS.read_text(encoding="utf-8"))
    corrida = d.get("_corrida", "?") if isinstance(d, dict) else "?"
    filas = d.get("datos", d) if isinstance(d, dict) else d
    filas = [f for f in filas if isinstance(f, dict) and f.get("id")]
    return filas, corrida


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registro", default="ciudadano",
                    choices=list(redaccion.REGISTROS))
    ap.add_argument("--limite", type=int, default=0,
                    help="solo los primeros N casos (para probar)")
    a = ap.parse_args()

    clave = os.environ.get("GROQ_API_KEY")
    if not clave:
        print("Falta GROQ_API_KEY en el entorno.")
        print("  En Colab:  import os; from google.colab import userdata")
        print("             os.environ['GROQ_API_KEY'] = "
              "userdata.get('GROQ_API_KEY')")
        print("  En local:  GROQ_API_KEY=... python -I "
              "data/medir_redaccion.py")
        return 1
    try:
        import groq
    except ImportError:
        print("Falta el paquete `groq`:  pip install groq")
        return 1

    filas, corrida = _predicciones()
    ev = {e["id"]: e for e in json.loads(
        (RAIZ / "data" / "eval_set_v2.json").read_text(
            encoding="utf-8"))["ejemplos"]}
    if a.limite:
        filas = filas[:a.limite]

    RUTA_CACHE.parent.mkdir(parents=True, exist_ok=True)
    generar = sistema.generador_groq(groq.Groq(api_key=clave),
                                     cache_path=str(RUTA_CACHE))

    print("=" * 74)
    print(f"  REDACCION sobre {len(filas)} casos de la corrida {corrida}")
    print(f"  registro: {a.registro}")
    print("=" * 74)

    resultados, fallos = [], []
    for i, f in enumerate(filas, 1):
        bloque = schema.parse_salida(f.get("finetuned") or "")
        # La condicion que cambiaria la via sale del gold cuando esta
        # codificada; si no, no se dice nada en vez de suponerla.
        piv = (ev.get(f["id"]) or {}).get("etiqueta_pivota_en") or None
        try:
            r = redaccion.redactar(generar, bloque, piv,
                                   registro=a.registro, estricto=False)
            resultados.append(r)
            if not r["verificacion"]["valido"]:
                fallos.append((f["id"], r["verificacion"]))
        except Exception as ex:                             # noqa: BLE001
            fallos.append((f["id"], {"error": str(ex)[:140]}))
        print(f"  {i}/{len(filas)}", end="\r")
    print(" " * 30, end="\r")

    if not resultados:
        print("Ningun texto se pudo redactar. Los fallos:")
        for cid, v in fallos[:5]:
            print(f"  {cid}: {v}")
        return 1

    med = redaccion.medir(resultados)
    med["_corrida"] = corrida
    med["_modulo"] = "m1"
    med["_artefacto"] = "redaccion.json"
    med["_medido_fuera_de_la_corrida"] = {
        "si": True,
        "por": "data/medir_redaccion.py",
        "motivo": "la seccion 6 de M1 se salto por falta de GROQ_API_KEY en "
                  "el entorno del notebook; se mide aqui desde "
                  "results/m1_predicciones.json para no repetir 30 minutos "
                  "de GPU por una medicion que no la usa.",
        "lo_que_esto_NO_prueba": "que la seccion 6 del notebook funcione. "
                                 "Eso solo lo prueba una corrida de M1 con "
                                 "la clave cargada.",
    }
    med["registro"] = a.registro
    if fallos:
        med["fallos"] = [{"id": c, "detalle": v} for c, v in fallos[:10]]

    RUTA_OUT.write_text(json.dumps(med, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")

    print(f"{'textos redactados':<30}{med['n']}")
    print(f"{'con normas inventadas':<30}{med['textos_con_citas_intrusas']}  "
          f"(tasa {med['tasa_citas_intrusas']:.1%})")
    print(f"{'dicen el mecanismo':<30}{med['dicen_el_mecanismo']:.1%}")
    print(f"{'dicen la procedencia':<30}{med['dicen_la_procedencia']:.1%}")
    print(f"{'palabras de media':<30}{med['palabras_media']}")
    if fallos:
        print(f"{'casos con fallo':<30}{len(fallos)}")
    print()
    if med["textos_con_citas_intrusas"]:
        print("  HAY NORMAS INVENTADAS EN LA REDACCION. Eso deshace la")
        print("  medicion de alucinacion normativa del resto del proyecto: la")
        print("  cita que ve el lector ya no es la que se midio.")
        print(f"  {med['ejemplos_intrusas']}")
    elif (med["dicen_el_mecanismo"] < 1.0
          or med["dicen_la_procedencia"] < 1.0):
        # Las DOS coberturas. Con mecanismo 1.0 y procedencia 0.9855 la rama
        # de exito afirmaba "todos dicen la via y la procedencia", que era
        # falso, y la consola es la que se lee al acabar.
        falta = []
        if med["dicen_el_mecanismo"] < 1.0:
            falta.append(f"la VIA en {1 - med['dicen_el_mecanismo']:.1%}")
        if med["dicen_la_procedencia"] < 1.0:
            falta.append(
                f"la PROCEDENCIA en {1 - med['dicen_la_procedencia']:.1%}")
        print(f"  Hay texto(s) que callan {' y '.join(falta)} de los casos.")
        print("  Callar la via o la procedencia deja un error del triaje")
        print("  indetectable para quien lee.")
    else:
        print("  La capa respeta el bloque: 0 normas introducidas, y todos")
        print("  los textos dicen la via y la procedencia. El texto puede ser")
        print("  equivocado --- lo sera 1 de cada 8 --- pero sera COMPROBABLE.")
    print()
    print("  --- una muestra ---")
    print(resultados[0]["texto"])
    print()
    print(f"  escrito: {RUTA_OUT.relative_to(RAIZ)}")
    print("  (declarado como medido FUERA de la corrida, en "
          "`_medido_fuera_de_la_corrida`)")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
