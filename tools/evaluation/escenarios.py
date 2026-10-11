"""Prueba de los cuatro escenarios de contexto (A5 de la fase A de M1).

## Por que existe

El protocolo exige medir el modelo con contexto **vacio, irrelevante, suficiente
y parcial**, y la validacion no lo puede hacer: sus 35 B2 conservan el contexto
historico, de otras categorias -- 0 de 35 traen un fragmento de su propia
categoria --, asi que un modelo que hubiera aprendido el atajo "si no hay nada
de mi categoria, abstente" los aprobaria. Medido: sobre la validacion el atajo
tiene +32 puntos de ventaja.

Esta prueba lo cierra con un diseno pareado: **la misma pregunta** con un
contexto que la responde y con uno de la misma materia que no. Si el modelo solo
mira la categoria, responde las dos igual. Si lee, cambia de conducta.

## Los cuatro escenarios

| escenario | de donde sale | que se espera |
|---|---|---|
| `suficiente` | los 55 B1 de validacion, con su contexto (trae el articulo que responde) | citar ese articulo |
| `parcial` | los 13 B3 de validacion, con su contexto | responder la parte y decir que falta |
| `irrelevante` | **las mismas 68 preguntas**, con lo que devuelve el buscador de produccion sin el articulo que responde ni sus contiguos | abstenerse |
| `vacio` | las mismas 68, sin ningun fragmento | la frase de escape **por codigo**, sin llamar al modelo |

`irrelevante` se construye con la misma regla que los B2 del dataset
(`REGLA_B2_V3`) y descarta los casos con fuga directa o un articulo contiguo al
retirado: el vecino suele responder lo mismo.

## Por que se congela en un archivo

`data/escenarios_m1.jsonl` se construye una vez, con e5 + FAISS, y se versiona.
Asi v1 y el candidato reciben **exactamente** los mismos contextos, y la
comparacion entre los dos no depende de que el buscador de en Colab el mismo
orden que en local.

    python -m tools.evaluation.escenarios --dry-run --indice   # arma y verifica
    python -m tools.evaluation.escenarios --escribir --indice  # congela el archivo
    python -m tools.evaluation.escenarios --verificar          # comprueba el archivo
    python -m tools.evaluation.escenarios --correr --adaptador <dir> --salida <dir>   # Colab
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from tools.evaluation import config

ARCHIVO = config.PROJECT_ROOT / "data" / "escenarios_m1.jsonl"
ESCENARIOS = ("suficiente", "parcial", "irrelevante", "vacio")
MAX_NEW_TOKENS = 900


def leer(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in Path(ruta).read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _base(registros: list[dict]) -> list[dict]:
    """Los registros de validacion con articulo oraculo: los B1 y los B3."""
    return sorted((r for r in registros if r.get("split") == "val"
                   and r.get("modo") in ("B1", "B3") and r.get("fuentes")),
                  key=lambda r: r["id"])


def _contexto(fragmentos) -> list[dict]:
    return [{"cita": f.cita, "doc_id": f.doc_id, "articulos": f.articulos_incluidos,
             "chunk_id": f.chunk_id} for f in fragmentos]


def construir(registros: list[dict], store=None) -> tuple[list[dict], list[dict]]:
    """(casos, descartes). Sin `store` el buscador es BM25: sirve para revisar,
    no para congelar el archivo."""
    from tools.dataset_contrastivo import _fuentes_como_doc
    from tools.dataset_v2 import (REGLA_B2_V3, Buscador, Especificacion, _oraculos_de,
                                  capitulos_de, cargar_corpus, fragmentos_para,
                                  riesgo_de_suficiencia_indirecta)
    from tools.evaluation.dataset import prompt_de
    from tools.rag.prompt_template import build_messages

    c = cargar_corpus()
    buscador = Buscador(c, store)
    casos, descartes = [], []
    for r in _base(registros):
        comun = {"id": r["id"], "category": r["category"], "pregunta": r["pregunta"],
                 "fuentes": r["fuentes"], "modo_origen": r["modo"]}

        # suficiente / parcial: el registro tal cual, con su propio prompt.
        escenario = "suficiente" if r["modo"] == "B1" else "parcial"
        casos.append({**comun, "escenario": escenario, "messages": prompt_de(r),
                      "contexto": r["contexto"], "buscador": r.get("buscador")})

        # irrelevante: la misma pregunta, sin el articulo que responde.
        fuentes = [tuple(f.rsplit(":", 1)) for f in r["fuentes"] if ":" in f]
        e = Especificacion(id=r["id"], categoria=r["category"], modo="B2", respuesta="",
                           pregunta=r["pregunta"], fuentes=[],
                           excluir=[(i.strip(), a.strip()) for i, a in fuentes])
        fragmentos, _ = fragmentos_para(e, e.pregunta, c, buscador, regla_b2=REGLA_B2_V3)
        excluidos = set(_fuentes_como_doc(r["fuentes"], c))
        caps = capitulos_de(_oraculos_de(e.excluir, c, "excluir", e.id), c)
        avisos = riesgo_de_suficiencia_indirecta(fragmentos, excluidos, caps)
        grave = [a for a in avisos if a.startswith(("FUGA_DIRECTA", "CONTIGUO_AL_ORACULO"))]
        if grave:
            descartes.append({"id": r["id"], "escenario": "irrelevante", "razon": grave})
        else:
            casos.append({**comun, "escenario": "irrelevante",
                          "messages": build_messages(e.pregunta, fragmentos),
                          "contexto": _contexto(fragmentos), "buscador": buscador.nombre,
                          "excluidos": sorted(excluidos), "revision_suficiencia": avisos})

        # vacio: sin fragmentos. Lo resuelve el codigo, no el modelo.
        casos.append({**comun, "escenario": "vacio", "messages": None, "contexto": [],
                      "buscador": None})
    return casos, descartes


# --- Comprobaciones (CPU) -----------------------------------------------------

def _pares(contexto) -> set[str]:
    return {f"{ch['doc_id']}:{a}" for ch in contexto for a in (ch.get("articulos") or ())}


def verificar(casos: list[dict]) -> list[str]:
    """Lo que tiene que cumplirse. Vacio = todo en orden."""
    from tools.rag.pipeline import _generar_verificado
    from tools.rag.prompt_template import RESPUESTA_ESCAPE_POR_CODIGO

    problemas = []
    por = Counter(c["escenario"] for c in casos)
    for esc in ESCENARIOS:
        if not por.get(esc):
            problemas.append(f"no hay casos de '{esc}'")

    for c in casos:
        if c["escenario"] == "irrelevante":
            fuga = set(c.get("excluidos") or ()) & _pares(c["contexto"])
            if fuga:
                problemas.append(f"{c['id']}: el irrelevante trae el articulo que responde {sorted(fuga)}")
            if not c["contexto"]:
                problemas.append(f"{c['id']}: irrelevante sin contexto")
        if c["escenario"] in ("suficiente", "parcial") and not c["contexto"]:
            problemas.append(f"{c['id']}: {c['escenario']} sin contexto")

    # vacio: el codigo responde la frase de escape sin llamar al modelo. Se
    # comprueba con model_bundle=None: si intentara generar, fallaria.
    for c in (x for x in casos if x["escenario"] == "vacio"):
        respuesta, ver = _generar_verificado(c["pregunta"], [], use_lora=False, model_bundle=None)
        if respuesta != RESPUESTA_ESCAPE_POR_CODIGO or ver.get("escape_por_codigo") != "sin_contexto":
            problemas.append(f"{c['id']}: con contexto vacio no hubo escape por codigo")
            break

    # el diseno es pareado: cada irrelevante tiene su suficiente o su parcial
    con_contexto = {c["id"] for c in casos if c["escenario"] in ("suficiente", "parcial")}
    huerfanos = [c["id"] for c in casos if c["escenario"] == "irrelevante" and c["id"] not in con_contexto]
    if huerfanos:
        problemas.append(f"irrelevantes sin su par: {huerfanos[:5]}")
    return problemas


def resumen(casos: list[dict], descartes: list[dict]) -> dict:
    from tools.rag.corpus import NORMAS_EN_ALCANCE, TRANSVERSAL

    cats = {n.path.stem: set(n.categorias) for n in NORMAS_EN_ALCANCE}
    irr = [c for c in casos if c["escenario"] == "irrelevante"]
    misma = sum(1 for c in irr if any(c["category"] in (cats.get(ch["doc_id"], set()) - {TRANSVERSAL})
                                      for ch in c["contexto"]))
    return {
        "por_escenario": dict(Counter(c["escenario"] for c in casos)),
        "irrelevante_con_fragmento_de_su_categoria": f"{misma}/{len(irr)}",
        "descartados_del_irrelevante": len(descartes),
        "buscador_irrelevante": sorted({c["buscador"] for c in irr}),
        "generaciones_en_gpu": sum(1 for c in casos if c["escenario"] != "vacio"),
    }


def huella_archivo() -> str | None:
    from tools.rag.manifiesto import huella_archivo as h

    return h(ARCHIVO)


# --- Lo que corre en Colab -----------------------------------------------------

def metricas(caso: dict, respuesta: str) -> dict:
    """Las automaticas. Lo que exige juicio -- B2_funcional -- se adjudica."""
    from tools.dataset_v2_quality import _FALTA_PARTE, _articulo_normalizado, citas
    from tools.evaluation.ragas_metrics import es_abstencion_pura

    respaldadas, no_respaldadas, ajenas = citas(respuesta, caso["contexto"])
    declarados = {_articulo_normalizado(f.rsplit(":", 1)[1]) for f in caso["fuentes"]}
    return {
        "abstencion_pura": bool(es_abstencion_pura(respuesta)),
        "cita_el_oraculo": any(x.split()[-1] in declarados for x in respaldadas),
        "citas_no_respaldadas": no_respaldadas + ajenas,
        "dice_que_falta": bool(_FALTA_PARTE.search(respuesta or "")),
    }


def correr(adaptador, salida, revision: str | None = None) -> dict:
    """Genera los escenarios con un adaptador, en una corrida con identidad."""
    from tools.evaluation import corrida
    from tools.evaluation.generation import run_messages_generation
    from tools.evaluation.reevaluacion_v1 import MODEL_ID, REVISION_V1, cargar
    from tools.rag.manifiesto import huella_archivo as h

    revision = corrida.exigir_revision(revision or REVISION_V1)
    casos = leer(ARCHIVO)
    problemas = verificar(casos)
    if problemas:
        raise SystemExit("el archivo de escenarios no pasa: " + "; ".join(problemas[:5]))
    huella_adaptador = h(Path(adaptador) / "adapter_model.safetensors")
    firma = corrida.firma(huella_dataset=huella_archivo(), model_id=MODEL_ID,
                          adaptador=f"escenarios-{huella_adaptador}", revision_base=revision,
                          raiz=config.PROJECT_ROOT)
    d = Path(salida) / firma["corrida_id"]
    corrida.escribir(d, firma)
    model, tokenizer = cargar(adaptador, revision)

    ruta = d / "escenarios_resultados.jsonl"
    hechos = {(x["id"], x["escenario"]) for x in leer(ruta)} if ruta.exists() else set()
    for c in casos:
        if c["escenario"] == "vacio" or (c["id"], c["escenario"]) in hechos:
            continue
        texto, n = run_messages_generation(model, tokenizer, c["messages"], MAX_NEW_TOKENS,
                                           return_n_tokens=True)
        fila = {"id": c["id"], "escenario": c["escenario"], "category": c["category"],
                "generated": texto, "n_tokens": int(n), **metricas(c, texto)}
        with ruta.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")

    filas = leer(ruta)
    por = {e: [f for f in filas if f["escenario"] == e] for e in ("suficiente", "parcial", "irrelevante")}
    res = {
        "corrida_id": firma["corrida_id"], "huella_adaptador": huella_adaptador,
        "huella_escenarios": huella_archivo(),
        "suficiente_cita_el_oraculo": f"{sum(f['cita_el_oraculo'] for f in por['suficiente'])}/{len(por['suficiente'])}",
        "suficiente_se_abstiene": f"{sum(f['abstencion_pura'] for f in por['suficiente'])}/{len(por['suficiente'])}",
        "parcial_dice_que_falta": f"{sum(f['dice_que_falta'] for f in por['parcial'])}/{len(por['parcial'])}",
        "irrelevante_se_abstiene": f"{sum(f['abstencion_pura'] for f in por['irrelevante'])}/{len(por['irrelevante'])}",
        "irrelevante_cita_sin_respaldo": sum(1 for f in por["irrelevante"] if f["citas_no_respaldadas"]),
        "nota": "B2_funcional del irrelevante exige adjudicacion (tools/adjudicacion_b2.py).",
    }
    (d / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="arma en memoria y verifica")
    g.add_argument("--escribir", action="store_true", help="congela data/escenarios_m1.jsonl")
    g.add_argument("--verificar", action="store_true", help="comprueba el archivo congelado")
    g.add_argument("--correr", action="store_true", help="genera en Colab con --adaptador")
    ap.add_argument("--indice", action="store_true", help="buscador de produccion: e5 + FAISS")
    ap.add_argument("--adaptador")
    ap.add_argument("--salida")
    a = ap.parse_args(argv)

    if a.verificar:
        casos = leer(ARCHIVO)
        problemas = verificar(casos)
        print(json.dumps(resumen(casos, []), ensure_ascii=False, indent=2))
        print(f"huella {huella_archivo()}")
        print("OK" if not problemas else "PROBLEMAS:\n  " + "\n  ".join(problemas))
        return 1 if problemas else 0
    if a.correr:
        if not (a.adaptador and a.salida):
            raise SystemExit("--correr necesita --adaptador y --salida")
        print(json.dumps(correr(a.adaptador, a.salida), ensure_ascii=False, indent=2))
        return 0

    if a.escribir and not a.indice:
        raise SystemExit("congelar los escenarios exige --indice: el irrelevante tiene que salir "
                         "del buscador de produccion (e5 + FAISS), no de BM25")
    store = None
    if a.indice:
        from tools.rag import pipeline

        store = pipeline.load_index()
    registros = leer(config.DATASET_PATH)
    casos, descartes = construir(registros, store)
    problemas = verificar(casos)
    print(json.dumps(resumen(casos, descartes), ensure_ascii=False, indent=2))
    if problemas:
        print("PROBLEMAS:\n  " + "\n  ".join(problemas))
        return 1
    print("todas las comprobaciones pasan")
    if a.escribir:
        with ARCHIVO.open("w", encoding="utf-8", newline="\n") as f:
            for c in casos:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"escrito {ARCHIVO.name} ({len(casos)} casos), huella {huella_archivo()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
