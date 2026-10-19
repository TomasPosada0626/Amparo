"""Separa dos preguntas que el `hit@5` mezcla, y que llevaban mal diagnosticadas.

EL ERROR QUE ESTE SCRIPT CORRIGE

ROADMAP3 · M3-4 decia: «11 de 63 casos no recuperan nada relevante [...] No es
del recuperador: 69 fragmentos no cubren el eval», y prescribia ampliar el
corpus hasta `casos_sin_ninguna <= 5`.

La prescripcion estaba mal porque el diagnostico estaba mal. `recall == 0` en
`evaluar_recuperacion` solo dice que lo relevante no entro en el top-5. Eso
tiene dos causas que no se arreglan igual:

  COBERTURA  el corpus no contiene ningun fragmento que respalde la cita
             esperada. Ninguna estrategia puede recuperar lo que no existe.
             Se arregla ampliando el corpus.

  RANKING    el fragmento existe pero queda por debajo del corte k. Se arregla
             en el recuperador --- y AMPLIAR EL CORPUS LO EMPEORA, porque mete
             mas candidatos a competir por los mismos 5 puestos.

Medido aqui: la cobertura es COMPLETA (0 citas esperadas sin fragmento, en los
dos eval sets) y el ranking es el cuello de botella (42 de 63 casos tienen su
fragmento por debajo del puesto 5 en BM25, alguno en el 49 de 77). Asi que
ampliar el corpus no solo no era la cura: iba en la direccion contraria.

Es, por cierto, lo que el propio `rag.py` ya decia en el comentario de
`PROMPT_CONSULTA`: «la consulta es el relato de un ciudadano y el corpus es
texto legal [...] no comparten casi vocabulario, y por eso BM25 solo devuelve
ruido». La transformacion de consulta existe precisamente para esto. El numero
que faltaba era cuanto de los 63 depende de ella.

QUE ES EXACTO Y QUE ES APROXIMADO

  - La parte de COBERTURA es exacta y no depende de ninguna estrategia: usa el
    mismo `cubre()` que las metricas, sobre el corpus entero, sin cortar en k.
  - La parte de RANKING es un PROXY: usa BM25 lexico, que es lo unico que corre
    sin GPU ni descargar modelos. Los brazos medidos usan denso, hibrido,
    reranked y transformacion de consulta, y rankean mejor. El proxy sirve para
    lo que se usa aqui --- demostrar que el fragmento ESTA y que el problema es
    de orden --- y no para estimar el hit@5 de ningun brazo.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from rag import Indice, citas_esperadas, cubre, trocear   # noqa: E402

RUTA_OUT = RAIZ / "data" / "cobertura_corpus.json"
FUENTES = ("corpus.json", "eval_set_v3.json", "eval_set_v2.json",
           "eval_set_m3.json")


def huellas_fuentes() -> dict[str, str]:
    """La huella de cada archivo del que depende esta auditoria.

    POR QUE UN ARTEFACTO DERIVADO TIENE QUE DECIR DE QUE DERIVA

    `cobertura_corpus.json` lo lee `data/reporte.py` para afirmar que la
    cobertura es completa. Si alguien amplia el corpus y no vuelve a correr
    esto, el archivo sigue ahi diciendo lo de antes, y el reporte lo publica
    sin que nada falle: un numero viejo con aspecto de vigente, que es el modo
    de fallo que `verificar_entrega.py` existe para cazar en `results/`.

    Con las huellas dentro, quien lo lea puede comprobar si sigue valiendo.
    `reporte.py` lo comprueba y marca la seccion como caducada en vez de
    imprimir cifras que no corresponden a los datos de al lado.
    """
    import hashlib
    return {f: hashlib.sha256(
        (RAIZ / "data" / f).read_bytes()).hexdigest()[:16] for f in FUENTES}
EVALS = (("eval_set_v3.json", "los 96 juzgables de v3"),
         ("eval_set_v2.json", "los 63 de v2, que v3 contiene"),
         ("eval_set_m3.json", "los puntuables de m3"))


def _casos(nombre: str) -> list[dict]:
    d = json.loads((RAIZ / "data" / nombre).read_text(encoding="utf-8"))
    return d["ejemplos"]


def auditar() -> dict:
    corpus = json.loads(
        (RAIZ / "data" / "corpus.json").read_text(encoding="utf-8"))["documentos"]
    chunks = trocear(corpus)
    ix = Indice(chunks, verbose=False)

    out: dict = {
        "_fuentes": huellas_fuentes(),
        "_como_comprobar": "si alguna huella de `_fuentes` no coincide con el "
                           "archivo actual, esta auditoria es de otros datos: "
                           "vuelve a correr `data/auditar_cobertura.py`.",
        "corpus": {"documentos": len(corpus), "chunks": len(chunks)},
        "por_eval_set": {},
        "lectura": "",
    }

    for nombre, etq in EVALS:
        casos = _casos(nombre)
        sin_cobertura, hondos, en_top5 = [], [], []
        citas_ausentes: dict[str, int] = {}

        for e in casos:
            esp = citas_esperadas(e)
            if not esp:
                continue
            faltan = [x for x in sorted(esp)
                      if not any(cubre(c, x) for c in corpus)]
            for x in faltan:
                citas_ausentes[x] = citas_ausentes.get(x, 0) + 1
            if faltan:
                sin_cobertura.append({"id": e["id"], "esperadas": sorted(esp),
                                      "sin_fragmento": faltan})
                continue

            # El fragmento existe: ¿en que puesto lo pone BM25?
            puntos = ix.bm25.puntuar(e["relato"])
            orden = sorted(range(len(chunks)), key=lambda i: -puntos[i])
            rango = next((i + 1 for i, k in enumerate(orden)
                          if any(cubre(chunks[k], x) for x in esp)), None)
            fila = {"id": e["id"], "rango_bm25": rango,
                    "esperadas": sorted(esp)}
            (en_top5 if rango and rango <= 5 else hondos).append(fila)

        hondos.sort(key=lambda f: -(f["rango_bm25"] or 0))
        n = len(sin_cobertura) + len(hondos) + len(en_top5)
        out["por_eval_set"][nombre] = {
            "etiqueta": etq,
            "casos_con_citas_esperadas": n,
            "sin_cobertura": len(sin_cobertura),
            "detalle_sin_cobertura": sin_cobertura,
            "citas_esperadas_sin_fragmento": citas_ausentes,
            "cubiertos_pero_fuera_del_top5_bm25": len(hondos),
            "cubiertos_y_en_top5_bm25": len(en_top5),
            "peor_rango_bm25": hondos[0]["rango_bm25"] if hondos else None,
            "los_15_mas_hondos": hondos[:15],
            "diagnostico": (
                "COBERTURA INCOMPLETA: hay citas esperadas sin ningun "
                "fragmento que las respalde. Ampliar el corpus ES la cura."
                if sin_cobertura else
                "COBERTURA COMPLETA: toda cita esperada tiene fragmento. Lo "
                "que falla es el ORDEN, y ampliar el corpus lo empeoraria."),
        }

    v2 = out["por_eval_set"]["eval_set_v3.json"]
    out["lectura"] = (
        f"De los {v2['casos_con_citas_esperadas']} casos comunes, "
        f"{v2['sin_cobertura']} no tienen fragmento para su cita esperada y "
        f"{v2['cubiertos_pero_fuera_del_top5_bm25']} si lo tienen pero por "
        f"debajo del puesto 5 en BM25 (el peor, en el "
        f"{v2['peor_rango_bm25']} de {out['corpus']['chunks']}). El techo que "
        "M3-4 atribuia al tamano del corpus es del ranking: la cura esta en la "
        "transformacion de consulta y el reranking, no en mas fragmentos.")
    return out


def main() -> int:
    r = auditar()
    RUTA_OUT.write_text(json.dumps(r, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print("=" * 78)
    print("  COBERTURA DEL CORPUS vs RANKING")
    print("=" * 78)
    print(f"  corpus: {r['corpus']['documentos']} documentos -> "
          f"{r['corpus']['chunks']} chunks")
    for nombre, d in r["por_eval_set"].items():
        print(f"\n  {nombre} · {d['etiqueta']} · n={d['casos_con_citas_esperadas']}")
        print(f"    sin cobertura (imposible de recuperar) : {d['sin_cobertura']}")
        print(f"    cubierto pero fuera del top-5 (BM25)   : "
              f"{d['cubiertos_pero_fuera_del_top5_bm25']}")
        print(f"    cubierto y en top-5 (BM25)             : "
              f"{d['cubiertos_y_en_top5_bm25']}")
        print(f"    peor rango del primer relevante        : {d['peor_rango_bm25']}")
        print(f"    -> {d['diagnostico']}")
    print()
    print("  " + r["lectura"].replace(". ", ".\n  "))
    print()
    print(f"  escrito: {RUTA_OUT.relative_to(RAIZ)}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
