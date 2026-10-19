"""
Reemplaza las sintesis del corpus por transcripciones literales de la fuente
oficial, y deja el corpus con CERO fragmentos sin cotejar.

EL PROBLEMA QUE RESUELVE
    La v1.0.0 del corpus tenia cinco fragmentos con `verificado: false`, y tres
    de ellos (`L1098-ALIM`, `L1437-NYR`, `L1581-SENS`) no eran transcripciones
    sino SINTESIS DE ENRUTAMIENTO escritas por el equipo. Para esas normas, el
    RAG recuperaba prosa nuestra y la servia con la apariencia de ley. Es el
    peor defecto posible en un corpus juridico: el usuario no tiene forma de
    distinguir la norma de nuestro resumen de la norma.

QUE SE HIZO
    Se descargaron las paginas del normograma de la Cancilleria (el mismo que
    ya se usaba para las leyes 1751, 1755 y 393), se extrajo el texto de cada
    articulo con un script y se inyecto aqui sin que nadie lo retipeara. Lo que
    se elimina del texto son los marcadores del normograma (Jurisprudencia
    Vigencia, Concordancias, Texto del Proyecto de Ley Anterior), que no son
    parte del articulo; lo que dice `<Articulo modificado por...>` se mueve a
    `nota_vigencia` en vez de borrarse.

DOS CORRECCIONES JURIDICAS QUE SALIERON DE ESTA COSECHA
    1. Ley 1266 art. 13. El corpus decia que la caducidad del dato negativo
       "paso de 4 a 8 anos" con la Ley 2157 de 2021. El texto vigente tiene
       LOS DOS PLAZOS A LA VEZ, con disparadores distintos: cuatro anos desde
       que se paga o se extingue la obligacion (cuerpo del articulo) y ocho
       anos desde que la obligacion entra en mora (paragrafo 1). No es un
       reemplazo. Ademas aparecen dos paragrafos que el corpus no tenia.
    2. Ley 361 art. 26. El corpus afirmaba que el Decreto-Ley 019 de 2012,
       art. 137, reescribio el articulo y traslado la autorizacion al
       Ministerio del Trabajo. La copia oficial de la Cancilleria sigue
       diciendo "oficina de Trabajo". Esa afirmacion pasa a nota marcada como
       NO verificada, en vez de darse por cierta.

Uso:  python data/reparar_corpus.py <cosecha.json>
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

BASE = "https://cancilleria.gov.co/sites/default/files/Normograma/docs"

# Marcadores que el conversor del normograma deja incrustados y que NO son
# parte del articulo.
RUIDO = re.compile(
    r"\s*(Jurisprudencia Vigencia|Texto del Proyecto de Ley Anterior|"
    r"Concordancias|Notas de Vigencia|Notas del Editor|Legislaci[óo]n Anterior|"
    r"Doctrina Concordante|Jurisprudencia Concordante)\s*", re.IGNORECASE)

RE_NOTA_INICIAL = re.compile(r"^\s*<([^<>]{10,300})>\s*")
RE_MARCA_PIE = re.compile(r"\s*<\s*\d+\s*>\s*")
RE_SUSTITUCION = re.compile(r"\s*<([^<>]{1,60})>\s*")


def limpiar(texto: str) -> tuple[str, list[str]]:
    """Devuelve (texto_limpio, notas_extraidas_del_propio_texto)."""
    notas = []
    m = RE_NOTA_INICIAL.match(texto)
    if m:
        notas.append(m.group(1).strip())
        texto = texto[m.end():]
    texto = RUIDO.sub(" ", texto)
    texto = RE_MARCA_PIE.sub(" ", texto)
    # Inserciones terminologicas del editor: se retiran del cuerpo y se deja
    # constancia, para que el texto quede como fue promulgado.
    sust = RE_SUSTITUCION.findall(texto)
    if sust:
        texto = RE_SUSTITUCION.sub(" ", texto)
        notas.append(
            "El normograma inserta en el cuerpo las sustituciones "
            f"terminologicas {sorted(set(sust))}; se retiraron para dejar el "
            "texto como fue promulgado. La Ley 1618 de 2013 sustituyo el "
            "termino 'limitacion' por 'discapacidad'.")
    texto = re.sub(r"\s+([,.;:])", r"\1", texto)
    return re.sub(r"\s+", " ", texto).strip(), notas


# clave_cosecha -> campos del fragmento nuevo
NUEVOS = {
    "L1581-05": {
        "id": "L1581-05", "norma": "Ley 1581 de 2012",
        "fuente": f"{BASE}/ley_1581_2012.htm", "vigencia": "vigente",
        "nota_extra": "Base legal de los DATOS SENSIBLES, entre ellos los relativos a la salud. Es lo que convierte la divulgacion de un diagnostico en una vulneracion del habeas data del art. 15 CP.",
    },
    "L1581-06": {
        "id": "L1581-06", "norma": "Ley 1581 de 2012",
        "fuente": f"{BASE}/ley_1581_2012.htm", "vigencia": "vigente",
        "nota_extra": "El tratamiento de datos sensibles esta PROHIBIDO salvo las cinco excepciones taxativas. La primera exige autorizacion EXPLICITA del titular.",
    },
    "L1266-13": {
        "id": "L1266-13", "norma": "Ley 1266 de 2008",
        "fuente": f"{BASE}/ley_1266_2008.htm",
        "vigencia": "vigente, modificado por el art. 3 de la Ley 2157 de 2021",
        "nota_extra": "DOS PLAZOS DISTINTOS QUE COEXISTEN, y confundirlos cambia la respuesta: (a) el cuerpo del articulo fija el doble del tiempo de mora, maximo CUATRO anos, contados desde que se pagan las cuotas vencidas o se extingue la obligacion; (b) el paragrafo 1 fija una caducidad de OCHO anos contados desde que la obligacion entra en mora, cumplidos los cuales el dato debe eliminarse. El (b) aplica aunque nunca se haya pagado. Una version anterior de este corpus decia que el plazo 'paso de 4 a 8 anos': es falso, no hubo reemplazo.",
    },
    "L361-26": {
        "id": "L361-26", "norma": "Ley 361 de 1997",
        "fuente": f"{BASE}/ley_0361_1997.htm",
        "vigencia": "vigente; inciso 2 CONDICIONALMENTE exequible (C-531 de 2000)",
        "nota_extra": "Fundamento de la ESTABILIDAD LABORAL REFORZADA. La Sentencia C-531 de 2000 declaro el inciso 2 exequible de forma condicionada: carece de todo efecto juridico el despido sin autorizacion previa de la autoridad de trabajo, de modo que la indemnizacion de 180 dias NO sanea el despido. PENDIENTE DE VERIFICAR: una version anterior de este corpus afirmaba que el Decreto-Ley 019 de 2012, art. 137, reescribio el articulo y traslado la autorizacion al Ministerio del Trabajo; la copia oficial de la Cancilleria sigue diciendo 'oficina de Trabajo', asi que esa afirmacion queda marcada como no cotejada.",
    },
    "L1437-138": {
        "id": "L1437-138", "norma": "Ley 1437 de 2011",
        "fuente": f"{BASE}/ley_1437_2011.htm", "vigencia": "vigente",
        "nota_extra": "REGLA DE ENRUTAMIENTO. Es el medio de control idoneo frente a un acto administrativo particular que se considera ilegal, y su existencia activa la causal de subsidiariedad del art. 6.1 del Decreto 2591 de 1991 salvo perjuicio irremediable. El plazo de cuatro meses del inciso 3 aplica al acto general.",
    },
    "L1098-111": {
        "id": "L1098-111", "norma": "Ley 1098 de 2006",
        "fuente": f"{BASE}/ley_1098_2006.htm",
        "vigencia": "vigente; numeral 5 derogado por la Ley 1564 de 2012",
        "nota_extra": "REGLA DE ENRUTAMIENTO. El numeral 2 describe la via propia de los alimentos: citacion a audiencia de conciliacion ante el defensor o comisario de familia y remision al Juez de Familia. Esa via especifica es la que hace improcedente la tutela por subsidiariedad (art. 6.1 del Decreto 2591 de 1991) salvo perjuicio irremediable. El numeral 4 extiende la regla al ofrecimiento de alimentos.",
    },
    "L1755-13": {
        "id": "L1755-13", "norma": "Ley 1755 de 2015",
        "fuente": f"{BASE}/ley_1755_2015.htm",
        "vigencia": "vigente; articulo CONDICIONALMENTE exequible",
        "nota_extra": "Aqui esta la base TEXTUAL de la 'respuesta de fondo', que antes se sostenia solo en jurisprudencia: el articulo exige obtener 'pronta resolucion COMPLETA Y DE FONDO'. Una respuesta formal que no resuelve lo preguntado no satisface el derecho. Tambien aclara que toda actuacion ante la autoridad es ejercicio del derecho de peticion sin necesidad de invocarlo.",
    },
    "L1755-20": {
        "id": "L1755-20", "norma": "Ley 1755 de 2015",
        "fuente": f"{BASE}/ley_1755_2015.htm", "vigencia": "vigente",
        "nota_extra": "ATENCION PRIORITARIA cuando resolver la peticion es necesario para evitar un perjuicio irremediable, y medidas de urgencia inmediatas si hay peligro inminente para la vida o la integridad. Es el puente entre el derecho de peticion y la urgencia que habilita la tutela.",
    },
}

# Fragmentos que salen: las cinco sintesis sin cotejar.
RETIRADOS = ["L1581-SENS", "L1437-NYR", "L1098-ALIM", "L1266-13", "L361-26"]


def main() -> int:
    cosecha = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    ruta = RAIZ / "data" / "corpus.json"
    corpus = json.loads(ruta.read_text(encoding="utf-8"))
    docs = corpus["documentos"]

    antes = len(docs)
    quitados = [d["id"] for d in docs if d["id"] in RETIRADOS]
    docs = [d for d in docs if d["id"] not in RETIRADOS]

    nuevos = []
    for clave, campos in NUEVOS.items():
        if clave not in cosecha:
            print(f"FALTA en la cosecha: {clave}")
            return 1
        c = cosecha[clave]
        texto, notas = limpiar(c["texto"])
        if len(texto) < 150:
            print(f"{clave}: texto sospechosamente corto ({len(texto)})")
            return 1
        nota = campos["nota_extra"]
        if notas:
            nota += " || Notas del texto fuente: " + " | ".join(notas)
        nuevos.append({
            "id": campos["id"],
            "norma": campos["norma"],
            "articulo": c["articulo"],
            "titulo": c["titulo"],
            "texto": texto,
            "fuente": campos["fuente"],
            "vigencia": campos["vigencia"],
            "transcripcion": "literal",
            "verificado": True,
            "nota_vigencia": nota,
        })

    docs = docs + nuevos
    docs.sort(key=lambda d: (d["norma"], d["id"]))

    sin_cotejar = [d["id"] for d in docs if not d["verificado"]]
    sintesis = [d["id"] for d in docs if d["transcripcion"] != "literal"]

    corpus["documentos"] = docs
    corpus["meta"]["version"] = "1.1.0"
    corpus["meta"]["total_fragmentos"] = len(docs)
    corpus["meta"]["fecha"] = "2026-10-15"
    corpus["meta"]["verificacion_pendiente"] = (
        "Cero fragmentos sin cotejar. Los cinco de la v1.0.0 se reemplazaron por "
        "transcripciones literales del normograma de la Cancilleria, extraidas con "
        "script (data/reparar_corpus.py) y no retipeadas a mano."
        if not sin_cotejar else
        f"Fragmentos sin cotejar: {sin_cotejar}")
    corpus["meta"].setdefault("cambios", []).append(
        "1.1.0 (2026-10-15): se retiraron las cinco sintesis sin cotejar "
        f"({', '.join(RETIRADOS)}) y se reemplazaron por siete transcripciones "
        "literales del normograma de la Cancilleria. Tres de las retiradas no eran "
        "transcripciones sino prosa del equipo que el RAG servia con apariencia de "
        "ley. De la cosecha salieron dos correcciones juridicas: (1) la caducidad "
        "del dato negativo de la Ley 1266 art. 13 NO paso de 4 a 8 anos, son dos "
        "plazos con disparadores distintos que coexisten; (2) la copia oficial del "
        "art. 26 de la Ley 361 no incorpora la modificacion del Decreto-Ley 019 de "
        "2012 que el corpus afirmaba, asi que esa afirmacion queda marcada como no "
        "cotejada. Se anaden ademas los arts. 13 y 20 de la Ley 1755 de 2015: el 13 "
        "es la base textual de la 'respuesta de fondo', que antes se sostenia solo "
        "en jurisprudencia.")

    ruta.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")

    print(f"corpus.json v{corpus['meta']['version']}: {antes} -> {len(docs)} fragmentos")
    print(f"  retirados ({len(quitados)}): {', '.join(quitados)}")
    print(f"  anadidos  ({len(nuevos)}): {', '.join(d['id'] for d in nuevos)}")
    print(f"  sin cotejar: {sin_cotejar or 'NINGUNO'}")
    print(f"  no literales: {sintesis or 'NINGUNO'}")
    print(f"  bytes: {ruta.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
