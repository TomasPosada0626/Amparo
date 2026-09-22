"""Manifiesto del corpus de fuentes verificadas (decision 1 de M3).

Este modulo declara QUE normas entran al indice y QUE categorias del dataset de
M1 cubre cada una. La metadata citable (fuente, tipo, URL, vigencia) NO se
declara aca: se lee del frontmatter YAML que cada archivo de data/corpus/normas/
ya trae verificado por quien armo el corpus. Declarar a mano una URL que el
archivo ya trae seria una oportunidad de equivocarse sin ninguna ganancia.

Alcance (decidido para M3): solo las normas que cubren las 9 categorias
cotidianas de mayor frecuencia del dataset de M1. El corpus descargado tiene 17
normas; se indexan 10. Las demas quedan declaradas en FUERA_DE_ALCANCE con su
razon, para que la exclusion sea una decision visible y no un olvido.
"""
from __future__ import annotations

from dataclasses import dataclass

from tools.rag import config, ingest

# Portales oficiales del Estado colombiano. El corpus se descargo de un espejo
# comunitario que republica el texto consolidado de SUIN-Juriscol porque los
# dominios .gov.co estan bloqueados por la politica de red de la organizacion
# (ver data/corpus/normas/README.md y la decision 1 de docs/m3_decisiones_rag.md).
# El campo `source` de cada archivo apunta al documento SUIN correspondiente.
PORTALES_OFICIALES = (
    "https://www.suin-juriscol.gov.co/",  # SUIN-Juriscol (Ministerio de Justicia)
    "https://www.secretariasenado.gov.co/",
    "https://www.funcionpublica.gov.co/eva/gestornormativo/",
)

# Las 9 categorias cotidianas de mayor frecuencia del dataset de M1 (61-63
# ejemplos cada una; las otras 15 tienen 51). Mismo criterio de priorizacion que
# se uso para construir el dataset de fine-tuning.
CATEGORIAS_OBJETIVO = (
    "Salud / EPS",
    "Garantias de consumo",
    "Despido",
    "Relaciones laborales",
    "Arriendo",
    "Reporte en centrales de riesgo",
    "Accidentes de transito",
    "Embargos",
    "Comparendos de transito",
)

# Categorias transversales: no son una categoria del dataset, sino los
# mecanismos que casi toda respuesta recomienda como primer paso.
TRANSVERSAL = "__transversal__"

TIPOS_VALIDOS = ("constitucion", "ley", "decreto", "codigo", "sentencia", "resolucion")

# Estados de vigencia del frontmatter que se consideran norma viva.
ESTADOS_VIGENTES = ("in_force",)


@dataclass
class NormaEnAlcance:
    """Una norma del corpus que entra al indice.

    `nombre_comun` es como se cita en lenguaje corriente ("Codigo Sustantivo del
    Trabajo"); el numero y el ano de la norma salen del `identifier` del
    frontmatter, no se escriben a mano.
    """

    filename: str
    categorias: tuple[str, ...]
    nombre_comun: str = ""
    nota: str = ""

    @property
    def path(self):
        return config.RAW_CORPUS_DIR / self.filename


NORMAS_EN_ALCANCE: list[NormaEnAlcance] = [
    # --- Transversales ------------------------------------------------------
    NormaEnAlcance(
        filename="constitucion_politica_1991.md",
        categorias=(TRANSVERSAL,),
        nota=(
            "Articulos de mayor uso en las respuestas del dataset: 15 (habeas "
            "data), 23 (derecho de peticion), 49 (salud), 86 (accion de tutela)."
        ),
    ),
    NormaEnAlcance(
        filename="cpaca_ley_1437_2011.md",
        categorias=(TRANSVERSAL,),
        nombre_comun="CPACA",
        nota=(
            "Trae el derecho de peticion vigente: la Ley 1755 de 2015 no existe "
            "como archivo independiente en el corpus porque su texto sustituyo el "
            "Titulo II de esta ley y asi quedo consolidado."
        ),
    ),
    NormaEnAlcance(
        filename="tutela_decreto_2591_1991.md",
        categorias=(TRANSVERSAL,),
        nombre_comun="Reglamentacion de la accion de tutela",
        nota="La tutela es el mecanismo que mas recomienda el dataset, sobre todo en salud.",
    ),
    # --- Una categoria cada una ---------------------------------------------
    NormaEnAlcance(
        filename="seguridad_social_ley_100_1993.md",
        categorias=("Salud / EPS",),
        nombre_comun="Sistema de Seguridad Social Integral",
        nota=(
            "Es la norma que el baseline de M2 citaba mal (la invocaba para "
            "arrendamiento). Tenerla indexada con su texto real es justo lo que "
            "convierte una cita a esta ley en algo verificable."
        ),
    ),
    NormaEnAlcance(
        filename="codigo_sustantivo_trabajo_decreto_2663_1950.md",
        categorias=("Despido", "Relaciones laborales"),
        nombre_comun="Codigo Sustantivo del Trabajo",
    ),
    NormaEnAlcance(
        filename="arrendamiento_vivienda_urbana_ley_820_2003.md",
        categorias=("Arriendo",),
        nombre_comun="Regimen de arrendamiento de vivienda urbana",
        nota=(
            "Cubre vivienda urbana. El arrendamiento comercial (Codigo de "
            "Comercio) y el civil general quedan fuera de alcance: la categoria "
            "'Arriendo' del dataset es de vivienda."
        ),
    ),
    NormaEnAlcance(
        filename="habeas_data_financiero_ley_1266_2008.md",
        categorias=("Reporte en centrales de riesgo",),
        nombre_comun="Habeas data financiero",
    ),
    NormaEnAlcance(
        filename="estatuto_consumidor_ley_1480_2011.md",
        categorias=("Garantias de consumo",),
        nombre_comun="Estatuto del Consumidor",
    ),
    NormaEnAlcance(
        filename="codigo_nacional_transito_ley_769_2002.md",
        categorias=("Accidentes de transito", "Comparendos de transito"),
        nombre_comun="Codigo Nacional de Transito",
    ),
    NormaEnAlcance(
        filename="codigo_general_proceso_ley_1564_2012.md",
        categorias=("Embargos",),
        nombre_comun="Codigo General del Proceso",
    ),
]

# Normas descargadas que NO se indexan en M3, cada una con su razon. Excluir en
# silencio seria indistinguible de un olvido; quien retome el trabajo (RAG
# avanzado) necesita saber que ya estan disponibles y por que se dejaron fuera.
FUERA_DE_ALCANCE: dict[str, str] = {
    "codigo_civil_ley_84_1873.md": "fuera de las 9 categorias priorizadas",
    "codigo_comercio_decreto_410_1971.md": "fuera de las 9 categorias priorizadas",
    "codigo_penal_ley_599_2000.md": "fuera de las 9 categorias priorizadas",
    "codigo_procedimiento_penal_ley_906_2004.md": "fuera de las 9 categorias priorizadas",
    "codigo_infancia_adolescencia_ley_1098_2006.md": "fuera de las 9 categorias priorizadas",
    "ley_transparencia_acceso_info_ley_1712_2014.md": (
        "cubre 'Acceso a informacion publica', que no esta entre las 9 priorizadas"
    ),
    "habeas_data_datos_personales_ley_1581_2012.md": (
        "EXCLUIDA POR CALIDAD, no por alcance: el archivo del espejo intercala "
        "texto transcrito de otros instrumentos (p. ej. el articulo 27 de la "
        "Convencion sobre los Derechos del Nino), que el chunker atribuiria a la "
        "Ley 1581. Citar un articulo ajeno como si fuera de esta ley es "
        "exactamente lo que el producto no puede hacer. 'Reporte en centrales de "
        "riesgo' queda cubierto por la Ley 1266 de 2008, que si esta limpia."
    ),
}


class ManifestError(ValueError):
    """El manifiesto no esta listo para indexar (falta metadata verificable)."""


def fuente_desde_identifier(identifier: str, nombre_comun: str = "") -> str:
    """"LEY-820-2003" -> "Ley 820 de 2003"; con nombre comun, lo agrega entre parentesis.

    La cita se arma del identifier del frontmatter y no de una cadena escrita a
    mano, para que el numero y el ano de la norma no puedan divergir del archivo.
    """
    partes = identifier.split("-")
    if len(partes) >= 3 and partes[-1].isdigit() and partes[-2].isdigit():
        etiqueta = " ".join(p.capitalize() for p in partes[:-2])
        base = f"{etiqueta} {partes[-2]} de {partes[-1]}"
    elif partes and partes[-1].isdigit():
        base = " ".join(p.capitalize() for p in partes[:-1]) + f" de {partes[-1]}"
    else:
        base = identifier
    return f"{base} ({nombre_comun})" if nombre_comun else base


def metadata_de(norma: NormaEnAlcance) -> dict:
    """Arma la entrada del manifiesto leyendo el frontmatter del archivo."""
    if not norma.path.exists():
        raise ManifestError(
            f"{norma.filename}: no esta en {config.RAW_CORPUS_DIR}. "
            "El corpus se versiona en el repo (data/corpus/normas/); si falta, "
            "revisa que hiciste pull de la rama con el corpus."
        )

    campos = ingest.read_frontmatter(norma.path)
    faltantes = [c for c in ("identifier", "rank", "status", "source") if not campos.get(c)]
    if faltantes:
        raise ManifestError(
            f"{norma.filename}: al frontmatter le faltan {faltantes}. Sin esos "
            "campos el chunk no se puede citar de forma verificable."
        )
    if campos["rank"] not in TIPOS_VALIDOS:
        raise ManifestError(
            f"{norma.filename}: rank {campos['rank']!r} no esta en {TIPOS_VALIDOS}"
        )

    return {
        "filename": norma.filename,
        "fuente": fuente_desde_identifier(campos["identifier"], norma.nombre_comun),
        "tipo": campos["rank"],
        "url_fuente": campos["source"],
        "vigente": campos["status"] in ESTADOS_VIGENTES,
    }


def validate_manifest(normas: list[NormaEnAlcance] | None = None) -> None:
    """Falla si alguna norma del alcance no puede citarse de forma verificable.

    Se llama antes de ingerir (pipeline.build_index): preferimos fallar en la
    indexacion que indexar un chunk cuya fuente no se puede comprobar, porque un
    chunk sin procedencia produce respuestas que *parecen* trazables.
    """
    normas = NORMAS_EN_ALCANCE if normas is None else normas
    problemas: list[str] = []
    vistos: set[str] = set()

    for norma in normas:
        if norma.filename in vistos:
            problemas.append(f"{norma.filename}: declarada dos veces")
        vistos.add(norma.filename)
        if not norma.categorias:
            problemas.append(f"{norma.filename}: no declara ninguna categoria")
        try:
            metadata_de(norma)
        except ManifestError as e:
            problemas.append(str(e))

    sin_cubrir = set(CATEGORIAS_OBJETIVO) - categorias_cubiertas(normas)
    if sin_cubrir:
        problemas.append(f"categorias objetivo sin ninguna norma: {sorted(sin_cubrir)}")

    if problemas:
        raise ManifestError(
            "El manifiesto del corpus no esta listo para indexar:\n  - "
            + "\n  - ".join(problemas)
        )


def categorias_cubiertas(normas: list[NormaEnAlcance] | None = None) -> set[str]:
    """Categorias reales del dataset cubiertas (sin contar las transversales)."""
    normas = NORMAS_EN_ALCANCE if normas is None else normas
    return {c for n in normas for c in n.categorias if c != TRANSVERSAL}


def to_ingest_manifest(normas: list[NormaEnAlcance] | None = None) -> list[dict]:
    """Manifiesto en el formato que consume ingest.ingest_corpus()."""
    normas = NORMAS_EN_ALCANCE if normas is None else normas
    validate_manifest(normas)
    return [metadata_de(n) for n in normas]


def archivos_del_corpus() -> list[str]:
    """Todos los .md presentes en el directorio del corpus (README aparte)."""
    return sorted(
        p.name for p in config.RAW_CORPUS_DIR.glob("*.md") if p.stem.lower() != "readme"
    )


if __name__ == "__main__":
    print(f"Corpus en {config.RAW_CORPUS_DIR}")
    print(f"{len(archivos_del_corpus())} normas descargadas · "
          f"{len(NORMAS_EN_ALCANCE)} en alcance · {len(FUERA_DE_ALCANCE)} fuera\n")
    for entrada in to_ingest_manifest():
        print(f"  [x] {entrada['fuente']}")
        print(f"      {entrada['url_fuente']}")
    print(f"\nCategorias cubiertas: {len(categorias_cubiertas())} de 9 objetivo.")
