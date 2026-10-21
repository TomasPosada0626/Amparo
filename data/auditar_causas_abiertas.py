"""
Establece la CAUSA de los defectos abiertos, en vez de atribuirlos al modelo.

POR QUÉ EXISTE

Tres defectos quedaron abiertos tras la corrida del 2026-10-21 y los tres se
despacharon con «necesita reentrenar»:

    precision_citas 0.55          el modelo cita normas que no vienen al caso
    abstencion_indebida 8.7%      9 de 103, y 8 con gold `via_ordinaria`
    accion_popular F1 0.4286      el brazo 4 confunde cumplimiento con popular

«Necesita reentrenar» no es un diagnóstico: es un presupuesto. Y en los tres
casos la causa está **en los datos**, es comprobable sin GPU, y tiene un
arreglo concreto distinto del que se habría hecho a ciegas.

Este script no mide el sistema. Mide si el conjunto de entrenamiento **hace
aprendible** lo que luego se le exige en el eval set. Son preguntas distintas y
la segunda casi nunca se hace.

    python -I data/auditar_causas_abiertas.py
"""
from __future__ import annotations
import collections
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

RUTA_OUT = RAIZ / "data" / "causas_abiertas.json"


def _cargar(nombre: str) -> list[dict]:
    return json.loads((RAIZ / "data" / nombre).read_text(encoding="utf-8"))["ejemplos"]


# NORMAS PURAMENTE PROCESALES: no dicen nada sobre ningun derecho.
#
# Esta lista es lo que separa un hallazgo de un sobre-recuento, y la primera
# version de esta auditoria no la tenia: contaba 72 de 123 (59%) porque
# marcaba como intrusa cualquier norma del campo del mecanismo. Pero varias
# son de DOBLE USO --- `art. 30 CP` fundamenta el habeas corpus Y la libertad
# personal; `art. 87 CP` la accion de cumplimiento Y el deber incumplido;
# `art. 88 CP` la accion popular Y el derecho colectivo --- y citarlas en la
# linea del derecho no esta mal.
#
# Lo que si esta mal es citar una causal de IMPROCEDENCIA como fundamento de
# un derecho: los numerales del art. 6 dicen cuando la tutela no procede, no
# que derecho esta en juego. Igual el art. 8 (mecanismo transitorio), el 42
# (competencia) y la Ley 1437 (procedimiento contencioso).
SOLO_PROCESALES = (
    "art. 6.1 Decreto 2591 de 1991", "art. 6.2 Decreto 2591 de 1991",
    "art. 6.3 Decreto 2591 de 1991", "art. 6.4 Decreto 2591 de 1991",
    "art. 6.5 Decreto 2591 de 1991", "art. 8 Decreto 2591 de 1991",
    "art. 42 Decreto 2591 de 1991", "Ley 1437 de 2011",
)


def fundamento_sobrecargado(train: list[dict]) -> dict:
    """¿El campo que el modelo copia mezcla el derecho con el mecanismo?

    EL HALLAZGO

    El dataset tiene los dos campos SEPARADOS:

        fundamento_del_derecho     ['art. 48 CP']
        fundamento_del_mecanismo   ['art. 6.1 Decreto 2591 de 1991']

    y el objetivo de entrenamiento los FUSIONA en `fundamento`, que
    `schema.render_salida` escribe en la línea `Derecho:`. Así que el modelo
    aprende a poner la norma **procesal del mecanismo** en la línea del
    **derecho**, y después lo repite donde está mal.

    Es exactamente la sobrecarga de `ninguno` otra vez: un campo con dos
    significados. Esa se corrigió; esta no se había visto.
    """
    conta, casos, dobles = collections.Counter(), [], collections.Counter()
    for e in train:
        fd = set(e.get("fundamento_del_derecho") or [])
        fm = set(e.get("fundamento_del_mecanismo") or [])
        fus = {x.strip() for x in (e.get("fundamento") or "").split(";") if x.strip()}
        # Lo que el modelo ve en la línea del DERECHO y no es del derecho.
        ajenas = (fus & fm) - fd
        # Y de esas, SOLO las que no dicen nada sobre ningun derecho. Ver
        # `SOLO_PROCESALES`: la distincion es lo que separa el hallazgo del
        # sobre-recuento.
        intrusas = {x for x in ajenas if x in SOLO_PROCESALES}
        dobles.update(ajenas - intrusas)
        if intrusas:
            conta.update(intrusas)
            casos.append({"id": e["id"], "derecho": e["derecho"],
                          "mecanismo": e["mecanismo"],
                          "intrusas": sorted(intrusas)})
    return {
        "n_train": len(train),
        "ejemplos_con_norma_PROCESAL_en_la_linea_del_DERECHO": len(casos),
        "proporcion": round(len(casos) / len(train), 4) if train else None,
        "normas_intrusas": dict(conta.most_common()),
        "normas_de_doble_uso_NO_contadas": dict(dobles.most_common()),
        "por_que_no_se_cuentan": (
            "`art. 30 CP` fundamenta el habeas corpus Y la libertad personal; "
            "`art. 87 CP` la accion de cumplimiento Y el deber incumplido; "
            "`art. 88 CP` la accion popular Y el derecho colectivo. Citarlas "
            "en la linea del derecho no esta mal. La primera version de esta "
            "auditoria las contaba y daba 72 de 123 (59%): un sobre-recuento "
            "que habria mandado a arreglar lo que no estaba roto."),
        "mecanismos_afectados": dict(collections.Counter(
            c["mecanismo"] or "abstencion" for c in casos)),
        "casos": casos[:25],
        "diagnostico": (
            "el objetivo de entrenamiento fusiona `fundamento_del_derecho` y "
            "`fundamento_del_mecanismo` en un solo campo `fundamento`, que se "
            "renderiza en la linea `Derecho:`. El modelo aprende a citar ahi "
            "la norma procesal del mecanismo."),
        "arreglo": (
            "separar los dos en `schema.render_salida`: el fundamento del "
            "DERECHO en la linea `Derecho:` y el del MECANISMO en la linea "
            "`Procedencia:`, donde pertenece. Los dos campos YA existen en el "
            "dataset, asi que no hay que anotar nada --- es un cambio de "
            "FORMATO. Exige reentrenar para que surta efecto, y mientras no se "
            "haga, `precision_citas` no puede subir por mucho que se entrene."),
    }


def cita_no_aprendible(train: list[dict], ev: list[dict]) -> dict:
    """¿Se le exige al modelo una cita que el train nunca le enseñó?

    EL HALLAZGO

    `habeas_data` en train cita **solo** la Ley 1266 de 2008 (datos
    financieros y crediticios). El eval set pide además la Ley 1581 de 2012
    (protección de datos personales, incluidos los sensibles) en 3 casos.

    El modelo no puede acertar una norma que no aparece ni una vez en su
    entrenamiento. Eso no es un fallo del modelo: es una exigencia que el
    conjunto de entrenamiento no hace aprendible.
    """
    def citas_por_derecho(src):
        out = collections.defaultdict(collections.Counter)
        for e in src:
            for c in (e.get("fundamento_del_derecho") or []):
                out[e.get("derecho")][c] += 1
        return out

    t, v = citas_por_derecho(train), citas_por_derecho(ev)
    huecos = []
    for der, cs in sorted(v.items()):
        faltan = {c: n for c, n in cs.items() if c not in t.get(der, {})}
        if faltan:
            huecos.append({
                "derecho": der,
                "citas_que_el_eval_pide_y_el_train_no_ensena": faltan,
                "lo_que_el_train_ensena": dict(t.get(der, {})),
            })
    return {
        "derechos_con_hueco": len(huecos),
        "casos_del_eval_afectados": sum(
            sum(h["citas_que_el_eval_pide_y_el_train_no_ensena"].values())
            for h in huecos),
        "detalle": huecos,
        "diagnostico": (
            "el eval set exige citas que el train no contiene ni una vez. El "
            "techo de `precision_citas` no lo pone el modelo: lo pone la "
            "cobertura del entrenamiento."),
        "arreglo": (
            "anadir casos de entrenamiento para cada hueco, y que CONTRASTEN "
            "con los que ya estan --- para `habeas_data`, casos de dato "
            "SENSIBLE (Ley 1581) frente a los de reporte CREDITICIO (Ley "
            "1266), que es la distincion que el eval evalua."),
    }


MARCAS = {
    "menciona una entidad":
        r"EPS|fondo|alcald|secretar|entidad|empresa|juzgad|universidad|banco",
    "pide algo concreto": r"quiero|necesito|solicito|pido|exijo",
    "dice que no sabe o no tiene": r"no s[eé]\b|no me acuerdo|no tengo|todav[ií]a no",
    "menciona una fecha": r"\d{1,2} de [a-z]+|hace \w+ (d[ií]as|meses|a[nñ]os)",
    "menciona un proceso judicial": r"proceso|demanda|recurso|sentencia|casaci[oó]n",
}


def frontera_no_aprendible(train: list[dict]) -> dict:
    """¿Se distinguen en superficie la abstención y la vía ordinaria?

    EL HALLAZGO

    8 de las 9 abstenciones indebidas de M1 tienen gold `via_ordinaria`. La
    hipótesis fácil es «faltan ejemplos de abstención». La medición dice otra
    cosa: los relatos de las dos clases comparten los mismos marcadores de
    superficie, así que la frontera **no es aprendible** de ellos.

    La distinción real es semántica —¿hay un problema jurídico, sí o no?— y un
    conjunto en el que las dos clases se parecen por fuera no la ensena.
    """
    ab = [e for e in train if e["mecanismo"] is None]
    vo = [e for e in train if e["mecanismo"] == "via_ordinaria"]
    tabla = {}
    for nombre, pat in MARCAS.items():
        a = sum(1 for e in ab if re.search(pat, e["relato"], re.I))
        v = sum(1 for e in vo if re.search(pat, e["relato"], re.I))
        tabla[nombre] = {
            "abstencion": f"{a}/{len(ab)}",
            "via_ordinaria": f"{v}/{len(vo)}",
            "diferencia_pp": round(
                100 * (a / len(ab) - v / len(vo)), 1) if ab and vo else None,
        }
    difs = [abs(d["diferencia_pp"]) for d in tabla.values()
            if d["diferencia_pp"] is not None]
    return {
        "n_abstencion_train": len(ab),
        "n_via_ordinaria_train": len(vo),
        "marcadores": tabla,
        "diferencia_media_pp": round(sum(difs) / len(difs), 1) if difs else None,
        "diagnostico": (
            "los relatos de `abstencion` y `via_ordinaria` comparten los "
            "marcadores de superficie, asi que la frontera entre «no hay "
            "mecanismo constitucional, vaya a la ordinaria» y «no se puede "
            "determinar nada» no se puede aprender de ellos. Anadir mas "
            "ejemplos de abstencion sin contrastarlos moveria la cifra sin "
            "ensenar la distincion."),
        "arreglo": (
            "pares MINIMOS: para cada caso de abstencion, un `via_ordinaria` "
            "que se le parezca en superficie y difiera en lo unico que "
            "importa --- que haya o no un problema juridico accionable. Es el "
            "mismo criterio que `ampliar_categorias.py` ya aplica («cada par "
            "es un contraste»), aplicado a esta frontera."),
    }


def main() -> int:
    train = [e for e in _cargar("dataset.json") if e["split"] == "train"]
    ev = _cargar("eval_set_v3.json")

    out = {
        "_que_es": ("la CAUSA de los defectos abiertos, medida en los datos. "
                    "No mide el sistema: mide si el train hace aprendible lo "
                    "que el eval exige."),
        "sobrecarga_del_fundamento": fundamento_sobrecargado(train),
        "citas_no_aprendibles": cita_no_aprendible(train, ev),
        "frontera_abstencion_via_ordinaria": frontera_no_aprendible(train),
    }
    RUTA_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                        encoding="utf-8", newline="\n")

    print("=" * 78)
    print("  CAUSA DE LOS DEFECTOS ABIERTOS · medida en los datos, sin GPU")
    print("=" * 78)
    s = out["sobrecarga_del_fundamento"]
    print(f"\n  1 · `precision_citas` 0.55 — la sobrecarga de `fundamento`")
    print(f"      {s['ejemplos_con_norma_PROCESAL_en_la_linea_del_DERECHO']}"
          f" de {s['n_train']} ejemplos de train "
          f"({s['proporcion']:.0%}) ensenan al modelo a citar la norma")
    print("      procesal del MECANISMO en la linea del DERECHO.")
    for n, v in list(s["normas_intrusas"].items())[:4]:
        print(f"         {v:3d}  {n}")
    print(f"      mecanismos afectados: {s['mecanismos_afectados']}")

    c = out["citas_no_aprendibles"]
    print(f"\n  2 · `precision_citas` 0.55 — citas que el train NO ensena")
    print(f"      {c['derechos_con_hueco']} derecho(s) con hueco, "
          f"{c['casos_del_eval_afectados']} caso(s) del eval afectados")
    for h in c["detalle"][:4]:
        print(f"         {h['derecho']}: el eval pide "
              f"{list(h['citas_que_el_eval_pide_y_el_train_no_ensena'])}")
        print(f"            y el train ensena {list(h['lo_que_el_train_ensena'])}")

    f = out["frontera_abstencion_via_ordinaria"]
    print(f"\n  3 · abstencion indebida 8.7% — frontera no aprendible")
    print(f"      train: {f['n_abstencion_train']} abstencion vs "
          f"{f['n_via_ordinaria_train']} via_ordinaria")
    print(f"      {'marcador':<32}{'abst':>8}{'v.ord':>8}{'dif pp':>9}")
    for n, v in f["marcadores"].items():
        print(f"      {n:<32}{v['abstencion']:>8}{v['via_ordinaria']:>8}"
              f"{v['diferencia_pp']:>9}")
    print(f"      diferencia media: {f['diferencia_media_pp']} puntos "
          "porcentuales")
    print()
    print("  Los tres arreglos estan en el artefacto. Ninguno es «entrenar")
    print("  mas»: dos son de FORMATO y COBERTURA, y el tercero pide pares")
    print("  minimos en vez de mas ejemplos.")
    print(f"\n  escrito: data/{RUTA_OUT.name}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
