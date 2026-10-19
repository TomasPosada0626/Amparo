"""
Justificación medida del modelo base, no argumentada.

POR QUE EXISTE
    Hasta ahora la elección de `Qwen2.5-7B-Instruct` se sostenía en un
    argumento. Un argumento no es evidencia, y la rúbrica de M1 pide justificar
    el modelo base. Aquí se mide.

    La justificación tiene DOS niveles, y el segundo es el que normalmente se
    salta:

      NIVEL 1 · POR QUE UN DECODER Y NO UN CLASIFICADOR
          La salida del sistema son cinco campos y TRES de ellos son texto
          libre: `fundamento` (las citas normativas), `razon` (el por qué) y
          `pretension` (qué pedir). Un clasificador puede producir los otros
          dos —`derecho` y `mecanismo`, que son vocabularios cerrados— y nada
          más. `cobertura_clasificador()` lo cuantifica sobre el dataset real
          en vez de afirmarlo: cuenta qué fracción de los caracteres de la
          salida gold podría emitir un clasificador.

          Esto no es un detalle académico. Un sistema de triaje que dice
          "tutela" sin decir con qué norma ni por qué no sirve para decidir
          nada: el usuario no puede verificarlo.

      NIVEL 2 · POR QUE ESTE DECODER
          Se mide la FERTILIDAD del tokenizador (tokens por palabra) sobre
          nuestro corpus, que es español jurídico colombiano. Un tokenizador
          que parte "inexequible" en seis piezas gasta más contexto, aprende
          peor el vocabulario del dominio y encarece cada ejemplo del
          fine-tuning. Se mide sobre tres textos distintos a propósito: el
          relato del ciudadano, la salida estructurada y el texto de la norma,
          porque los tres tienen registros distintos.

Uso:
    python src/tokenizadores.py            # tabla comparativa
    python src/tokenizadores.py --rapido   # solo los dos primeros modelos

Requiere `transformers`. Si no está instalado lo dice y sale sin reventar: la
medición se corre en Colab, no hace falta en local.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

# Candidatos. El orden es el de la comparación en el informe.
CANDIDATOS = [
    ("Qwen/Qwen2.5-7B-Instruct", "decoder · el elegido"),
    ("meta-llama/Llama-3.1-8B-Instruct", "decoder · alternativa de tamaño similar"),
    ("mistralai/Mistral-7B-Instruct-v0.3", "decoder · alternativa europea"),
    ("dccuchile/bert-base-spanish-wwm-cased", "encoder español (BETO) · no puede generar"),
]

# Términos del dominio cuya fragmentación importa: si el tokenizador los parte
# en muchas piezas, el modelo tiene que aprender a recomponerlos antes de poder
# usarlos.
TERMINOS = [
    "tutela", "inexequible", "subsidiariedad", "perjuicio irremediable",
    "habeas corpus", "accionado", "improcedencia", "fuero de maternidad",
    "estabilidad laboral reforzada", "daño consumado", "acción de cumplimiento",
    "Colpensiones", "EPS", "desacato", "Decreto 2591 de 1991",
]


def _textos() -> dict[str, list[str]]:
    """Tres registros distintos del mismo dominio."""
    import schema
    ds = json.loads((RAIZ / "data" / "dataset.json").read_text(encoding="utf-8"))
    corpus = json.loads((RAIZ / "data" / "corpus.json").read_text(encoding="utf-8"))
    ej = ds["ejemplos"]
    return {
        "relato del ciudadano": [e["relato"] for e in ej],
        "salida estructurada": [schema.render_salida(e) for e in ej],
        "texto de la norma": [d["texto"] for d in corpus["documentos"]],
    }


def _palabras(t: str) -> int:
    return len(re.findall(r"\w+", t))


def cobertura_clasificador() -> dict:
    """Qué fracción de la salida gold podría emitir un clasificador.

    Un clasificador predice etiquetas de vocabulario cerrado. De los cinco
    campos, solo `derecho` y `mecanismo` lo son. Se cuenta sobre los caracteres
    de la salida renderizada real, no sobre el número de campos, porque los
    campos no pesan igual: `razon` es una frase y `mecanismo` es una palabra.
    """
    import schema
    ds = json.loads((RAIZ / "data" / "dataset.json").read_text(encoding="utf-8"))
    cerrados = libres = 0
    for e in ds["ejemplos"]:
        cerrados += len(str(e["derecho"])) + len(str(e["mecanismo"] or "")) + len("si")
        libres += len(e.get("fundamento") or "") + len(e["razon"]) + len(e["pretension"]) \
            + len(e["accionado"])
    total = cerrados + libres
    return {
        "n": len(ds["ejemplos"]),
        "campos_de_vocabulario_cerrado": ["derecho", "mecanismo", "procede"],
        "campos_de_texto_libre": ["fundamento", "accionado", "razon", "pretension"],
        "chars_que_un_clasificador_podria_emitir": cerrados,
        "chars_de_texto_libre": libres,
        "cobertura_clasificador": cerrados / total if total else 0.0,
        "lectura": (
            "Un clasificador podría producir una fracción pequeña de la salida y "
            "ninguna de las citas normativas. El sistema quedaría sin `fundamento`, "
            "que es justo el campo que permite verificar la respuesta."),
    }


def medir(modelos: list[tuple[str, str]], verbose: bool = True) -> dict:
    try:
        from transformers import AutoTokenizer
    except ImportError:
        print("transformers no esta instalado: esta medicion se corre en Colab.")
        return {"error": "transformers no disponible"}

    textos = _textos()
    filas = []
    for nombre, nota in modelos:
        try:
            tok = AutoTokenizer.from_pretrained(nombre, trust_remote_code=True)
        except Exception as ex:
            if verbose:
                print(f"  {nombre}: no se pudo cargar ({str(ex)[:70]})")
            filas.append({"modelo": nombre, "nota": nota, "error": str(ex)[:120]})
            continue

        fila = {"modelo": nombre, "nota": nota,
                "vocabulario": len(tok), "fertilidad": {}}
        for registro, lista in textos.items():
            n_tok = sum(len(tok.encode(t, add_special_tokens=False)) for t in lista)
            n_pal = sum(_palabras(t) for t in lista)
            fila["fertilidad"][registro] = round(n_tok / n_pal, 3) if n_pal else None
        fila["fertilidad_media"] = round(
            sum(v for v in fila["fertilidad"].values() if v) /
            max(1, sum(1 for v in fila["fertilidad"].values() if v)), 3)
        fila["piezas_por_termino"] = {
            t: len(tok.encode(t, add_special_tokens=False)) for t in TERMINOS}
        fila["terminos_en_una_pieza"] = sum(
            1 for v in fila["piezas_por_termino"].values() if v == 1)
        fila["tokens_por_ejemplo"] = round(
            sum(len(tok.encode(r + s, add_special_tokens=False))
                for r, s in zip(textos["relato del ciudadano"],
                                textos["salida estructurada"]))
            / len(textos["relato del ciudadano"]))
        filas.append(fila)

    return {"filas": filas, "cobertura_clasificador": cobertura_clasificador()}


def imprimir(res: dict) -> None:
    cc = res.get("cobertura_clasificador")
    if cc:
        print(f"\n{'='*92}\n  NIVEL 1 · por que un decoder y no un clasificador\n{'='*92}")
        print(f"  campos de vocabulario cerrado : {', '.join(cc['campos_de_vocabulario_cerrado'])}")
        print(f"  campos de texto libre         : {', '.join(cc['campos_de_texto_libre'])}")
        print(f"  de la salida gold, un clasificador podria emitir el "
              f"{cc['cobertura_clasificador']:.1%} de los caracteres")
        print(f"  ({cc['chars_que_un_clasificador_podria_emitir']} de "
              f"{cc['chars_que_un_clasificador_podria_emitir'] + cc['chars_de_texto_libre']}), "
              f"y ninguna cita normativa")

    filas = [f for f in res.get("filas", []) if "error" not in f]
    if not filas:
        return
    print(f"\n{'='*92}\n  NIVEL 2 · fertilidad del tokenizador sobre espanol juridico colombiano\n{'='*92}")
    print(f"{'modelo':<42}{'vocab':>8}{'relato':>9}{'salida':>9}{'norma':>8}"
          f"{'media':>8}{'tok/ej':>8}")
    print("-" * 92)
    for f in filas:
        fe = f["fertilidad"]
        print(f"{f['modelo'][:41]:<42}{f['vocabulario']:>8}"
              f"{fe['relato del ciudadano']:>9.3f}{fe['salida estructurada']:>9.3f}"
              f"{fe['texto de la norma']:>8.3f}{f['fertilidad_media']:>8.3f}"
              f"{f['tokens_por_ejemplo']:>8}")
    print("=" * 92)
    print("  fertilidad = tokens por palabra. Mas bajo es mejor: menos contexto por")
    print("  ejemplo y menos piezas que recomponer para aprender el vocabulario.")
    print()
    print(f"{'modelo':<42}{'terminos del dominio en 1 pieza':>34}")
    print("-" * 92)
    for f in filas:
        print(f"{f['modelo'][:41]:<42}{f['terminos_en_una_pieza']:>20} de {len(TERMINOS)}")
    print("=" * 92)

    mejor = min(filas, key=lambda f: f["fertilidad_media"])
    print(f"  Mejor fertilidad media: {mejor['modelo']} ({mejor['fertilidad_media']})")
    print("  La decision no es solo fertilidad: el encoder (BETO) no puede generar")
    print("  los tres campos de texto libre, asi que queda descartado por el NIVEL 1")
    print("  aunque su tokenizador sea competitivo en espanol.")


def main() -> int:
    modelos = CANDIDATOS[:2] if "--rapido" in sys.argv else CANDIDATOS
    res = medir(modelos)
    imprimir(res)
    if "filas" in res:
        salida = RAIZ / "results" / "m1_tokenizadores.json"
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
        print(f"\n  -> {salida.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
