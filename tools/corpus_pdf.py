"""Convierte a Markdown del corpus las normas que no estan en el espejo de SUIN.

El corpus de M3 (data/corpus/normas/) viene de legalize-co, un espejo de
SUIN-Juriscol en Markdown con frontmatter YAML. El espejo no tiene nada posterior
a 2014 ni la Ley 142, asi que esas normas se bajaron en PDF y se convierten aqui
al mismo formato. Los PDF originales quedan en data/corpus/pdf/ para que la
conversion se pueda repetir y auditar.

Que hace con cada PDF:

  1. Extrae el texto con pdftotext (poppler-utils), pagina por pagina.
  2. Quita lo que no es norma: el encabezado y el pie que el Gestor Normativo de
     Funcion Publica repite en cada pagina, el aviso de responsabilidad, las
     lineas "Ver Concepto ..." (remisiones, no texto) y, en la Ley 2452, el
     indice con numeros de pagina.
  3. Reconstruye los parrafos: el PDF corta cada linea al ancho de la pagina, y
     el chunker necesita parrafos enteros y cada articulo empezando parrafo. Un
     encabezado de articulo ("ARTICULO 5.", "Articulo 1o.", "Articulo 13.-")
     abre parrafo; una remision al inicio de linea ("Articulo 5 de la presente
     ley") no, porque despues del numero no viene puntuacion.
  4. Escribe el frontmatter con los mismos campos que usa el espejo
     (identifier, rank, status, source...), que corpus.metadata_de exige.

Las notas de vigencia de Funcion Publica ("Nota: ... declarado EXEQUIBLE ...",
"Modificado por el art. 18, Ley 689 de 2001") se conservan: dicen si un texto
sigue vigente. Lo que el PDF marca con subrayado (el texto exacto que la Corte
declaro inexequible) se pierde en la extraccion; la nota que lo explica queda.

Uso:  python -m tools.corpus_pdf            # convierte todas
      python -m tools.corpus_pdf --check    # solo verifica que no cambiarian
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from tools.rag import config

PDF_DIR = config.PROJECT_ROOT / "data" / "corpus" / "pdf"
FECHA_DESCARGA = "2026-10-08"


@dataclass(frozen=True)
class FuentePdf:
    pdf: str
    destino: str
    identifier: str
    rank: str
    title: str
    publication_date: str
    source: str
    entry_into_force: str = ""
    # Texto (regex) donde empieza el articulado. Lo anterior (indice, avisos) se
    # descarta. `ocurrencia` elige cual coincidencia, para saltar el indice.
    inicio: str = r"^DECRETA:?\s*$"
    ocurrencia: int = 1
    nota: str = ""
    # Extraer con -layout y reconstruir las tablas comportamiento -> medida
    # correctiva (Codigo de Policia). Sin layout, pdftotext saca la tabla por
    # columnas: primero todos los "Numeral N" y despues todas las medidas, y se
    # pierde que medida va con que numeral.
    tablas: bool = False


GESTOR = "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i="

FUENTES: list[FuentePdf] = [
    FuentePdf("Ley_142_de_1994.pdf", "servicios_publicos_domiciliarios_ley_142_1994.md",
              "LEY-142-1994", "ley",
              "Por la cual se establece el régimen de los servicios públicos domiciliarios y se dictan otras disposiciones",
              "1994-07-11", GESTOR + "2752"),
    FuentePdf("Ley_2220_de_2022.pdf", "estatuto_conciliacion_ley_2220_2022.md",
              "LEY-2220-2022", "ley",
              "Por medio de la cual se expide el Estatuto de Conciliación y se dictan otras disposiciones",
              "2022-06-30", GESTOR + "188766", entry_into_force="2022-12-30",
              nota="Rige seis meses despues de su promulgacion (articulo 146). Deroga la Ley 640 de 2001."),
    FuentePdf("Ley_1751_de_2015.pdf", "estatutaria_salud_ley_1751_2015.md",
              "LEY-1751-2015", "ley",
              "Por medio de la cual se regula el derecho fundamental a la salud y se dictan otras disposiciones",
              "2015-02-16", GESTOR + "60733"),
    FuentePdf("Ley_1010_de_2006.pdf", "acoso_laboral_ley_1010_2006.md",
              "LEY-1010-2006", "ley",
              "Por medio de la cual se adoptan medidas para prevenir, corregir y sancionar el acoso laboral y otros hostigamientos en el marco de las relaciones de trabajo",
              "2006-01-23", GESTOR + "18843"),
    FuentePdf("Ley_2126_de_2021.pdf", "comisarias_de_familia_ley_2126_2021.md",
              "LEY-2126-2021", "ley",
              "Por la cual se regula la creación, conformación y funcionamiento de las comisarías de familia, se establece el órgano rector y se dictan otras disposiciones",
              "2021-08-04", GESTOR + "168066"),
    FuentePdf("decision_486.pdf", "propiedad_industrial_decision_486_2000.md",
              "DECISION-486-2000", "decision",
              "Régimen Común sobre Propiedad Industrial (Comisión de la Comunidad Andina)",
              "2000-09-14", "https://www.wipo.int/wipolex/es/legislation/details/9451",
              inicio=r"^DECIDE:?\s*$",
              nota="Publicada en la Gaceta Oficial del Acuerdo de Cartagena 600 del 19 de septiembre de 2000. "
                   "Norma comunitaria andina: aplica directamente en Colombia."),
    FuentePdf("Ley_1801_de_2016.pdf", "codigo_policia_convivencia_ley_1801_2016.md",
              "LEY-1801-2016", "ley",
              "Por la cual se expide el Código Nacional de Seguridad y Convivencia Ciudadana",
              "2016-07-29", GESTOR + "80538", inicio=r"^DECRETA:?\s*$", tablas=True),
    FuentePdf("Ley_2452_de_2025.pdf", "codigo_procesal_trabajo_ley_2452_2025.md",
              "LEY-2452-2025", "ley",
              "Por la cual se expide el Código Procesal del Trabajo y de la Seguridad Social",
              "2025-04-02", "https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=177617",
              entry_into_force="2026-04-02",
              nota="Diario Oficial 53077 del 2 de abril de 2025. Rige un año despues de su publicacion "
                   "(articulo 330) y reemplaza el Decreto Ley 2158 de 1948."),
]

# --- Limpieza -------------------------------------------------------------------

_BOILERPLATE = (
    re.compile(r"^Departamento Administrativo de la Funci[oó]n P[uú]blica$"),
    re.compile(r"^EVA - Gestor Normativo$"),
    re.compile(r"^Los datos publicados tienen prop[oó]sitos exclusivamente informativos"),
    re.compile(r"^responsable de la vigencia de la presente norma"),
    re.compile(r"^\d{1,4}$"),                        # numero de pagina
    re.compile(r"^Fecha y hora de creaci[oó]n:"),
)
# Las firmas: lo que sigue ya no es norma.
_FIRMAS = re.compile(
    r"^((EL|LA) PRESIDENT[EA] (DEL|DE LA) (H\.\s*|HONORABLE\s+)?(SENADO|C[AÁ]MARA)|PUBL[IÍ]QUESE Y C[UÚ]MPLASE|"
    r"Dada en la ciudad de)", re.IGNORECASE)
_INDICE = re.compile(r"\.{5,}\s*\d+\s*$")             # "Articulo 1o. ... ..... 19"
_REMISION = re.compile(r"^(Ver|Ver:)\s")              # "Ver Concepto SSP 228 de 2011"

_ARTICULO = re.compile(
    r"^(?:ART[IÍ]CULO|Art[ií]culo)\s+(?:TRANSITORIO\s+|transitorio\s+)?\d+"
    r"(?:\s*[-–]\s*[A-Za-z](?![A-Za-z])|[A-Za-z](?![A-Za-z]))?\s*[°º]?\s*(?:[\.\-–:]|\s+[A-ZÁÉÍÓÚÑ]{3,}\b)"
)
_NUMERO = re.compile(r"^(?:ART[IÍ]CULO|Art[ií]culo)\s+(?:TRANSITORIO\s+|transitorio\s+)?(\d+)")
_ENCABEZADO = re.compile(r"^(LIBRO|PARTE|T[ÍI]TULO|CAP[ÍI]TULO|SECCI[ÓO]N)\b", re.IGNORECASE)
_ABRE_PARRAFO = re.compile(
    r"^(PAR[ÁA]GRAFO|Par[áa]grafo|NOTA|Nota|Numeral(?:es)? \d+[^:]{0,20}:|\d{1,3}[\.\)]\s|[a-zñ]\)\s|[A-Z]\)\s|[ivx]+\)\s)"
)
_CIERRA = re.compile(r"[\.:;]$")


def _texto_pdf(path: Path, layout: bool = False) -> list[str]:
    opciones = ["-layout"] if layout else []
    salida = subprocess.run(["pdftotext", *opciones, "-enc", "UTF-8", str(path), "-"],
                            check=True, capture_output=True, text=True).stdout
    return [unicodedata.normalize("NFKC", p) for p in salida.split("\f")]


_CABECERA_TABLA = re.compile(r"^COMPOR-?\s*TAMIENTOS\s*MEDIDAS?\s+CORRECTIVAS?", re.IGNORECASE)
_FILA = re.compile(r"^Numeral(?:es)?\s*\d")


def reconstruir_tablas(crudas: list[str]) -> list[str]:
    """Convierte cada tabla "COMPORTAMIENTOS | MEDIDA CORRECTIVA A APLICAR" (texto
    con -layout) en una linea por fila: "Numeral 3: Multa General tipo 2".

    En el PDF la medida va centrada verticalmente al lado de su numeral, partida
    en varias lineas arriba y abajo de el. Cada linea de medida se asigna al
    numeral mas cercano; en empate, al de arriba."""
    salida: list[str] = []
    i = 0
    while i < len(crudas):
        if not _CABECERA_TABLA.match(crudas[i].strip()):
            salida.append(crudas[i])
            i += 1
            continue
        salida.append("COMPORTAMIENTOS Y MEDIDA CORRECTIVA A APLICAR:")
        filas: list[dict] = []
        sueltas: list[tuple[int, str]] = []
        i += 1
        pos = 0
        while i < len(crudas):
            cruda = crudas[i].rstrip()
            texto = cruda.strip()
            if not texto:
                i += 1
                continue
            sangria = len(cruda) - len(cruda.lstrip())
            if _FILA.match(texto) and sangria < 5:
                partes = re.split(r"\s{2,}", texto, maxsplit=1)
                numeral = re.sub(r"Numeral(?=\d)", "Numeral ", partes[0])
                filas.append({"pos": pos, "numeral": numeral, "lineas": [(pos, partes[1])] if len(partes) > 1 else []})
            elif (sangria >= 5 and not _ARTICULO.match(texto) and not _ABRE_PARRAFO.match(texto)
                  and not _ENCABEZADO.match(texto)):
                sueltas.append((pos, texto))
            else:
                break                                      # termino la tabla
            pos += 1
            i += 1
        for p_linea, texto in sueltas:
            if filas:
                mejor = min(filas, key=lambda f: (abs(f["pos"] - p_linea), f["pos"] > p_linea))
                mejor["lineas"].append((p_linea, texto))
        for f in filas:
            medida = " ".join(texto for _, texto in sorted(f["lineas"]))
            salida.append(f"{f['numeral']}: {re.sub(r'[ ]+', ' ', medida).strip()}")
    return salida


def _es_mayusculas(linea: str) -> bool:
    letras = [c for c in linea if c.isalpha()]
    return len(letras) >= 4 and sum(c.isupper() for c in letras) / len(letras) > 0.9 and len(linea) < 140


def _lineas_limpias(paginas: list[str], titulo_pie: str, tablas: bool = False) -> list[str]:
    """Todas las lineas sin boilerplate. '' marca una linea en blanco del PDF."""
    crudas: list[str] = []
    for pagina in paginas:
        for cruda in pagina.split("\n"):
            linea = re.sub(r"\s+", " ", cruda).strip()
            if linea == titulo_pie or any(p.search(linea) for p in _BOILERPLATE):
                continue
            if _INDICE.search(linea) or _REMISION.match(linea):
                continue
            # Con -layout el pie sale en un solo renglon: "Ley 1801 de 2016   8   EVA - Gestor Normativo".
            if "EVA - Gestor Normativo" in linea or "Departamento Administrativo de la Funci" in linea:
                continue
            crudas.append(cruda.rstrip())
    if tablas:
        crudas = reconstruir_tablas(crudas)
    lineas: list[str] = []
    for cruda in crudas:
        linea = re.sub(r"\s+", " ", cruda).strip()
        # "ARTÍCULO. 101." (errata de la fuente) -> "ARTÍCULO 101."
        linea = re.sub(r"^(ART[IÍ]CULO|Art[ií]culo)\.\s+(?=\d)", r"\1 ", linea)
        lineas.append(linea)
    # El PDF a veces parte el encabezado: "Artículo" / "" / "239." / "" / "Sentencias...".
    unidas: list[str] = []
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        if re.fullmatch(r"(ART[IÍ]CULO|Art[ií]culo)", linea):
            j = i + 1
            while j < len(lineas) and not lineas[j]:
                j += 1
            if j < len(lineas) and re.match(r"\d+", lineas[j]):
                linea = f"{linea} {lineas[j]}"
                k = j + 1
                while k < len(lineas) and not lineas[k]:
                    k += 1
                if k < len(lineas) and re.fullmatch(r"\d+[A-Za-z]?\s*[°º]?\s*[\.\-–:]", lineas[j]):
                    linea = f"{linea} {lineas[k]}"
                    j = k
                unidas.append(linea)
                i = j + 1
                continue
        unidas.append(linea)
        i += 1
    return unidas


def marcar_articulos_citados(parrafos: list[str]) -> list[str]:
    """Pone entre comillas los articulos de OTRA norma que esta transcribe.

    Una ley que modifica otra la cita entera: "ARTICULO 17. Modifiquese el
    articulo 5 de la Ley 294 de 1996, el cual quedara asi:" y despues
    "ARTICULO 5o. Medidas de proteccion...". Sin marcarlo, el chunker lo toma
    como el articulo 5 de ESTA ley y se citaria "Ley 2126 de 2021, articulo 5".

    Regla: el articulado propio va en orden. Un encabezado es propio si su numero
    es el siguiente (o el mismo, para los "bis" 185A), o salta hasta 3 adelante
    (articulos que la fuente omitio) sin venir despues de un "asi:". Si no, es
    texto citado: se le antepone una comilla, y el chunker ya no lo reconoce
    como encabezado (queda dentro del articulo que lo modifica, que es su lugar).
    """
    salida, ultimo, anterior = [], 0, ""
    for p in parrafos:
        m = _NUMERO.match(p) if _ARTICULO.match(p) else None
        if m:
            n = int(m.group(1))
            tras_cita = anterior.rstrip().endswith(":")
            propio = n in (ultimo, ultimo + 1) or (ultimo + 1 < n <= ultimo + 3 and not tras_cita)
            if propio:
                ultimo = n
            else:
                p = "\u201c" + p
        salida.append(p)
        anterior = p
    return salida


def reconstruir_parrafos(lineas: list[str]) -> list[str]:
    """Une las lineas cortadas por el ancho de pagina en parrafos.

    Abre parrafo: un encabezado de articulo, de titulo/capitulo, un paragrafo, una
    nota, un numeral o literal, una linea en mayusculas (nombre de capitulo), o
    una linea que sigue a otra que termino en punto y quedo corta (fin de inciso).
    """
    llenas = sorted(len(l) for l in lineas if l)
    ancho = llenas[int(len(llenas) * 0.9)] if llenas else 80
    parrafos: list[str] = []
    actual = ""
    anterior = ""
    for linea in lineas:
        if not linea:
            continue
        abre = (
            not actual
            or _ARTICULO.match(linea)
            or _ENCABEZADO.match(linea)
            or _ABRE_PARRAFO.match(linea)
            or _es_mayusculas(linea)
            or _es_mayusculas(anterior)
            or (_CIERRA.search(anterior) and len(anterior) < 0.8 * ancho)
        )
        if abre:
            if actual:
                parrafos.append(actual)
            actual = linea
        else:
            actual = actual[:-1] + linea if actual.endswith("-") and linea[:1].islower() else f"{actual} {linea}"
        anterior = linea
    if actual:
        parrafos.append(actual)
    return parrafos


def _cuerpo(fuente: FuentePdf) -> str:
    paginas = _texto_pdf(PDF_DIR / fuente.pdf, layout=fuente.tablas)
    no_vacias = [l.strip() for l in (paginas[0].split("\n") if paginas else []) if l.strip()]
    pie = re.sub(r"\s+", " ", (no_vacias + ["", ""])[1])
    # El pie de Funcion Publica repite el nombre corto ("Ley 142 de 1994"), que es
    # la segunda linea de la primera pagina.
    lineas = _lineas_limpias(paginas, pie if re.match(r"^(Ley|Decreto)", pie) else "\x00", fuente.tablas)
    patron = re.compile(fuente.inicio)
    vistos = [i for i, l in enumerate(lineas) if patron.match(l)]
    if len(vistos) < fuente.ocurrencia:
        raise ValueError(f"{fuente.pdf}: no aparece el inicio {fuente.inicio!r} (ocurrencia {fuente.ocurrencia})")
    lineas = lineas[vistos[fuente.ocurrencia - 1] + 1:]
    # Lo que viene despues de las firmas (notas de publicacion, ministros) se corta.
    fin = next((i for i, l in enumerate(lineas) if _FIRMAS.match(l)), len(lineas))
    lineas = lineas[:fin]
    parrafos = marcar_articulos_citados(reconstruir_parrafos(lineas))
    salida = []
    for p in parrafos:
        if _ENCABEZADO.match(p) and len(p) < 140:
            salida.append(f"## {p}")
        else:
            salida.append(p)
    return "\n\n".join(salida)


def _yaml(valor: str) -> str:
    return '"' + valor.replace("\\", "\\\\").replace('"', '\\"') + '"'


def a_markdown(fuente: FuentePdf) -> str:
    campos = {
        "title": fuente.title,
        "identifier": fuente.identifier,
        "country": "co",
        "rank": fuente.rank,
        "publication_date": fuente.publication_date,
        "last_updated": FECHA_DESCARGA,
        "status": "in_force",
        "source": fuente.source,
        "entry_into_force": fuente.entry_into_force,
        "converted_from": f"data/corpus/pdf/{fuente.pdf}",
        "conversion_note": fuente.nota,
    }
    cabecera = "\n".join(f"{k}: {_yaml(v)}" for k, v in campos.items() if v)
    return f"---\n{cabecera}\n---\n# {fuente.title}\n\n{_cuerpo(fuente)}\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="no escribe; falla si algun .md cambiaria")
    args = parser.parse_args(argv)
    distintos = []
    for fuente in FUENTES:
        texto = a_markdown(fuente)
        destino = config.RAW_CORPUS_DIR / fuente.destino
        if args.check:
            if not destino.exists() or destino.read_text(encoding="utf-8") != texto:
                distintos.append(fuente.destino)
            continue
        destino.write_text(texto, encoding="utf-8")
        print(f"{fuente.pdf} -> {destino.name}")
    if distintos:
        print("Cambiarian:", distintos)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
