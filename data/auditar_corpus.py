"""
Audita el corpus buscando restos del conversor del normograma, y los limpia.

POR QUE EXISTE
    Al revisar a mano el art. 4 de la Ley 472 recien transcrito aparecieron
    tres defectos que la limpieza automatica no habia cazado:

      1. marcadores del normograma incrustados en medio del texto
         ("Jurisprudencia Unificacion"), que no son parte del articulo;
      2. una FRASE DUPLICADA, porque el conversor parte la oracion en un ancla
         y la repite: "...definidos como tales en la Igualmente son derechos e
         intereses colectivos los definidos como tales en la Constitucion...";
      3. el encabezado del capitulo siguiente pegado al final, porque el corte
         buscaba el articulo 5 y entre medias estaba "CAPITULO III".

    Un fragmento marcado `literal` tiene que serlo. Si el corpus dice que algo
    es texto de la ley y en realidad tiene basura del conversor o una frase
    repetida, el RAG lo recupera y lo cita igual, y nadie lo nota.

    Esta auditoria no es una limpieza puntual: revisa LOS 54 fragmentos con los
    mismos criterios y deja constancia de lo que encontro.

Uso:  python data/auditar_corpus.py [--arreglar]
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Marcadores del conversor. Cada uno es una etiqueta de navegacion del
# normograma, no texto de la norma. "Texto original" NO esta en la lista a
# proposito: es una expresion que aparece en prosa legitima ("su texto original
# decia que...") y quitarla rompe la frase.
MARCADORES = [
    "Jurisprudencia Vigencia", "Jurisprudencia Unificación",
    "Jurisprudencia Unificacion", "Jurisprudencia Concordante",
    "Concordancias", "Notas de Vigencia", "Notas del Editor",
    "Legislación Anterior", "Legislacion Anterior", "Doctrina Concordante",
    "Texto del Proyecto de Ley Anterior",
]
RE_MARCADORES = re.compile(
    r"\s*(" + "|".join(re.escape(m) for m in MARCADORES) + r")\s*",
    re.IGNORECASE)

# Encabezado de la division SIGUIENTE, pegado al final del articulo por el
# conversor. Tres salvaguardas, porque la version anterior de este patron
# truncaba texto real:
#
#   1. el numeral romano se exige en MAYUSCULA y sin IGNORECASE. Antes
#      `[IVXLCDM0-9]` con IGNORECASE hacia que la 'd' de "por parte de una
#      fundacion" contara como numeral, y el `.*$` se comia el resto del
#      articulo: asi se trunco el art. 53 CP y el art. 5 del Decreto 2591.
#   2. va anclado al FINAL del texto, para no cortar una referencia interna
#      como "lo establecido en el Capitulo III de este decreto".
#   3. no incluye PARTE ni SECCION, que son palabras de uso corriente.
RE_DIVISION = re.compile(
    r"\s*(CAP[IÍ]TULO|CAPITULO|T[IÍ]TULO|TITULO|LIBRO)\s+[IVXLCDM]+\s*\.?"
    r"\s*[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{0,60}$")


def duplicados_adyacentes(texto: str, minimo: int = 40) -> list[str]:
    """Frases repetidas pegadas una a la otra, como las deja el conversor."""
    hallados = []
    for m in re.finditer(r"(.{%d,120}?)\1" % minimo, texto):
        hallados.append(m.group(1).strip())
    return hallados


def quitar_duplicados(texto: str, minimo: int = 40) -> str:
    anterior = None
    while anterior != texto:
        anterior = texto
        texto = re.sub(r"(.{%d,120}?)\1" % minimo, r"\1", texto)
    return texto


def revisar(d: dict) -> dict:
    t = d["texto"]
    return {
        "marcadores": sorted({m.group(1) for m in RE_MARCADORES.finditer(t)}),
        "division_al_final": bool(RE_DIVISION.search(t)),
        "duplicados": duplicados_adyacentes(t),
        "espacio_antes_de_puntuacion": len(re.findall(r"\s[,.;:]", t)),
        "espacios_dobles": len(re.findall(r"  +", t)),
    }


def limpiar(t: str) -> str:
    t = RE_MARCADORES.sub(" ", t)
    t = RE_DIVISION.sub("", t)
    t = quitar_duplicados(t)
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def main() -> int:
    arreglar = "--arreglar" in sys.argv
    ruta = RAIZ / "data" / "corpus.json"
    corpus = json.loads(ruta.read_text(encoding="utf-8"))
    docs = corpus["documentos"]

    sucios, cambios = [], 0
    for d in docs:
        r = revisar(d)
        problemas = []
        if r["marcadores"]:
            problemas.append(f"marcadores={r['marcadores']}")
        if r["division_al_final"]:
            problemas.append("encabezado de division al final")
        if r["duplicados"]:
            problemas.append(f"{len(r['duplicados'])} frase(s) duplicada(s)")
        if r["espacio_antes_de_puntuacion"]:
            problemas.append(f"{r['espacio_antes_de_puntuacion']} espacio(s) antes de puntuacion")
        if r["espacios_dobles"]:
            problemas.append(f"{r['espacios_dobles']} espacio(s) doble(s)")
        if problemas:
            sucios.append((d["id"], problemas, r["duplicados"][:1]))
            if arreglar:
                antes = d["texto"]
                d["texto"] = limpiar(antes)
                if d["texto"] != antes:
                    cambios += 1

    # --- cobertura: toda cita de los datasets debe tener fragmento -------
    # El whitelist (normas.json) dice si una norma EXISTE; esto dice si el RAG
    # puede RESPALDARLA. Son cosas distintas y la segunda se nos escapo tres
    # veces: Ley 2157 de 2021, art. 42 CP y Ley 100 de 1993 estaban aceptadas
    # por el validador y no existian en el corpus.
    sys.path.insert(0, str(RAIZ / "src"))
    import rag, schema
    chunks = rag.trocear(docs)
    sin_respaldo = {}
    # `eval_set_v2.json` faltaba en esta lista, asi que los 23 casos que se le
    # anadieron no pasaban por el control de cobertura: una cita sin fragmento
    # que la respalde habria entrado sin que nadie lo viera.
    for archivo in ("dataset.json", "eval_set.json", "eval_set_v2.json",
                    "eval_set_m3.json"):
        ruta_d = RAIZ / "data" / archivo
        if not ruta_d.exists():
            continue
        for e in json.loads(ruta_d.read_text(encoding="utf-8"))["ejemplos"]:
            for cita in schema.citas(e.get("fundamento") or ""):
                if not any(rag.cubre(ch, cita) for ch in chunks):
                    sin_respaldo.setdefault(cita, []).append(e["id"])

    print(f"cobertura: {len(chunks)} chunks contra las citas de los datasets")
    if sin_respaldo:
        print(f"  {len(sin_respaldo)} cita(s) SIN fragmento que las respalde:")
        for cita, ids in sin_respaldo.items():
            print(f"    {cita}  <- {', '.join(ids[:6])}")
    else:
        print("  toda cita de los datasets tiene un fragmento que la respalda")
    print()

    print(f"auditoria de {len(docs)} fragmentos del corpus")
    if not sucios:
        print("  limpio: ningun resto del conversor, ninguna frase duplicada")
    for fid, probs, dup in sucios:
        print(f"  {fid:<12}{'; '.join(probs)}")
        if dup:
            print(f"               duplicado: \"{dup[0][:70]}...\"")

    if arreglar and cambios:
        corpus["meta"].setdefault("cambios", []).append(
            "1.1.1 (2026-10-15): auditoria de los 54 fragmentos con "
            "data/auditar_corpus.py. Se encontraron y limpiaron restos del "
            "conversor del normograma (marcadores de 'Jurisprudencia "
            "Unificacion', encabezados de capitulo pegados al final) y frases "
            "duplicadas que el conversor produce al partir una oracion en un "
            "ancla. Los defectos aparecieron al revisar a mano el art. 4 de la "
            "Ley 472; la auditoria los busca ahora en todos los fragmentos, "
            "porque revisar uno por uno a ojo no escala y no es evidencia.")
        corpus["meta"]["version"] = "1.1.1"
        ruta.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
        print(f"\n  arreglados: {cambios} fragmentos · corpus v1.1.1 · "
              f"{ruta.stat().st_size} bytes")
    elif arreglar:
        print("\n  nada que arreglar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
