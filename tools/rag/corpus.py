"""Manifiesto del corpus de fuentes verificadas (decision 1 de M3).

Este modulo declara QUE normas entran al indice y QUE categorias del dataset de
M1 cubre cada una. La metadata citable (fuente, tipo, URL, vigencia) NO se
declara aca: se lee del frontmatter YAML que cada archivo de data/corpus/normas/
ya trae verificado por quien armo el corpus. Declarar a mano una URL que el
archivo ya trae seria una oportunidad de equivocarse sin ninguna ganancia.

Alcance. En M3 se indexaron solo las normas de las 9 categorias cotidianas de
mayor frecuencia (10 normas). La corrida del 2026-10-07 mostro que el eval set
pregunta por 27 categorias y que las que no tienen norma dan context recall 0
(docs/m3_cobertura_corpus.md), y el dataset de M1 v2 necesita contexto real para
TODAS sus categorias tematicas. Desde el 2026-10-08 el alcance es toda categoria
tematica del dataset que tenga su norma en el corpus; las que no la tienen
quedan en CATEGORIAS_SIN_NORMA con la norma que falta. Lo que no se indexa queda
en FUERA_DE_ALCANCE con su razon, para que la exclusion sea una decision visible
y no un olvido.
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

# Categorias tematicas del dataset de M1 que el corpus cubre con al menos una
# norma. Hasta el 2026-10-07 eran solo las 9 de mayor frecuencia; ver el
# docstring del modulo.
CATEGORIAS_OBJETIVO = (
    # Las 9 originales (61-63 ejemplos cada una en el dataset).
    "Salud / EPS",
    "Garantias de consumo",
    "Despido",
    "Relaciones laborales",
    "Arriendo",
    "Reporte en centrales de riesgo",
    "Accidentes de transito",
    "Embargos",
    "Comparendos de transito",
    # Agregadas el 2026-10-08.
    "Acceso a informacion publica",
    "Conciliacion prejudicial",
    "Contratacion estatal y facturacion",
    "Contratos empresariales (B2B)",
    "Derecho administrativo general",
    "Derecho ambiental sancionatorio",
    "Derecho contractual general",
    "Derecho de familia - alimentos",
    "Educacion / debido proceso disciplinario",
    "Licencias urbanisticas",
    "Penal basico y derechos de las victimas",
    "Pensiones y seguridad social",
    "Prestamos informales y usura",
    "Procedimiento civil - recursos",
    "Propiedad intelectual - marcas",
    "Propiedad y linderos",
    "Violencia intrafamiliar y medidas de proteccion",
)

# Categorias tematicas que todavia no tienen su norma en el corpus, con la norma
# que falta. El espejo de SUIN (data/corpus/normas/README.md) no trae leyes
# posteriores a 2014 ni la Ley 142 de 1994, y la Decision 486 es norma andina,
# no colombiana, asi que SUIN no la publica. Se cargan cuando alguien con acceso
# a secretariasenado.gov.co las descargue.
CATEGORIAS_SIN_NORMA: dict[str, str] = {
    "Servicios publicos domiciliarios": (
        "Ley 142 de 1994 (regimen de servicios publicos domiciliarios): no esta en el espejo"
    ),
}

# Normas que cubririan mejor categorias que hoy solo quedan cubiertas en parte.
# No bloquean el indice; quedan a la vista para la proxima carga.
NORMAS_PENDIENTES: dict[str, str] = {
    "Ley 142 de 1994": "Servicios publicos domiciliarios (hoy sin norma)",
    "Ley 1801 de 2016": "Codigo de Policia: querellas policivas, Propiedad y linderos, Licencias urbanisticas",
    "Ley 2220 de 2022": "Estatuto de conciliacion (la Ley 640 de 2001 esta derogada)",
    "Ley 1751 de 2015": "Estatutaria de salud: Salud / EPS",
    "Ley 1010 de 2006": "Acoso laboral: Relaciones laborales",
    "Ley 2126 de 2021": "Comisarias de familia: Violencia intrafamiliar",
    "Decision 486 de 2000 (CAN)": "Regimen comun de propiedad industrial: Propiedad intelectual - marcas",
}

# Categorias del eval set de M2 que no existen en el dataset de M1, y la
# categoria del dataset (o el bloque transversal) que las cubre.
EQUIVALENCIAS_EVAL_SET: dict[str, str] = {
    "Derecho penal - denuncia": "Penal basico y derechos de las victimas",
    "Derecho comercial": "Contratos empresariales (B2B)",
    "Accion de tutela": "__transversal__",
    "Derecho de peticion": "__transversal__",
}

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
    # Si > 0, solo se indexan los primeros N articulos. Para archivos del espejo
    # que, despues del articulado completo de la ley, transcriben otro texto con
    # su propia numeracion (el proyecto de ley que reviso la Corte, p. ej.): ese
    # texto se citaria como si fuera la ley.
    articulos_propios: int = 0
    # Fragmentos de otra norma intercalados en el archivo del espejo, como pares
    # (texto donde empiezan, texto donde vuelve la norma). Se quitan al ingerir;
    # si un marcador no aparece, la ingesta falla en vez de indexar el texto ajeno.
    fragmentos_ajenos: tuple[tuple[str, str], ...] = ()

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
        categorias=(TRANSVERSAL, "Derecho administrativo general", "Acceso a informacion publica"),
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
        categorias=("Salud / EPS", "Pensiones y seguridad social"),
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
        categorias=("Embargos", "Procedimiento civil - recursos", "Conciliacion prejudicial"),
        nombre_comun="Codigo General del Proceso",
        nota=(
            "Conciliacion prejudicial queda cubierta solo en parte (audiencia y "
            "requisito de procedibilidad): el estatuto vigente es la Ley 2220 de "
            "2022, que no esta en el espejo."
        ),
    ),
    # --- Agregadas el 2026-10-08 (docs/m3_cobertura_corpus.md) ---------------
    NormaEnAlcance(
        filename="codigo_comercio_decreto_410_1971.md",
        categorias=("Contratos empresariales (B2B)", "Contratacion estatal y facturacion",
                    "Prestamos informales y usura"),
        nombre_comun="Codigo de Comercio",
        nota=(
            "Contratos mercantiles, factura (titulos valores) e intereses comerciales. "
            "El espejo intercala, despues del articulo 751, los 6 articulos de la ley "
            "de cheques fiscales numerados desde 1: se citarian como 'Codigo de "
            "Comercio, articulo 1'."
        ),
        fragmentos_ajenos=(("Artículo 1°. Denomínanse cheques fiscales", "Sección IV. Bonos"),),
    ),
    NormaEnAlcance(
        filename="codigo_civil_ley_84_1873.md",
        categorias=("Derecho contractual general", "Derecho de familia - alimentos",
                    "Propiedad y linderos", "Contratos empresariales (B2B)",
                    "Prestamos informales y usura", "Accidentes de transito"),
        nombre_comun="Codigo Civil",
        nota=(
            "Obligaciones y contratos, alimentos, bienes y servidumbres, mutuo y "
            "responsabilidad extracontractual. En B2B el Codigo de Comercio remite al "
            "Civil para lo que no regula; es la norma mas grande del corpus (unos "
            "2600 articulos), asi que su efecto en la precision se mide en la proxima "
            "corrida de S08. El espejo antepone al articulo 1 un 'Articulo 1' de un "
            "decreto de estado de sitio (jueces de instruccion criminal), que se quita."
        ),
        fragmentos_ajenos=(("Artículo 1. Los Jueces de Instrucción Criminal", "CAPITULO 1º"),),
    ),
    NormaEnAlcance(
        filename="codigo_penal_ley_599_2000.md",
        categorias=("Penal basico y derechos de las victimas", "Prestamos informales y usura",
                    "Derecho de familia - alimentos", "Violencia intrafamiliar y medidas de proteccion"),
        nombre_comun="Codigo Penal",
        nota="Usura, inasistencia alimentaria, violencia intrafamiliar y delitos frecuentes.",
    ),
    NormaEnAlcance(
        filename="codigo_procedimiento_penal_ley_906_2004.md",
        categorias=("Penal basico y derechos de las victimas",),
        nombre_comun="Codigo de Procedimiento Penal",
        nota="Denuncia, querella, derechos de las victimas.",
    ),
    NormaEnAlcance(
        filename="codigo_infancia_adolescencia_ley_1098_2006.md",
        categorias=("Derecho de familia - alimentos", "Violencia intrafamiliar y medidas de proteccion"),
        nombre_comun="Codigo de la Infancia y la Adolescencia",
    ),
    NormaEnAlcance(
        filename="ley_transparencia_acceso_info_ley_1712_2014.md",
        categorias=("Acceso a informacion publica",),
        nombre_comun="Ley de Transparencia",
        articulos_propios=33,
    ),
    NormaEnAlcance(
        filename="habeas_data_datos_personales_ley_1581_2012.md",
        # Transversal y no "Reporte en centrales de riesgo": la Ley 1581 excluye
        # los datos financieros que regula la Ley 1266.
        categorias=(TRANSVERSAL,),
        nombre_comun="Proteccion de datos personales",
        articulos_propios=30,
        nota=(
            "Antes excluida por calidad: despues de sus 30 articulos el archivo del "
            "espejo transcribe el proyecto de ley que reviso la Corte, con otra "
            "numeracion. articulos_propios=30 indexa solo la ley."
        ),
    ),
    NormaEnAlcance(
        filename="contratacion_estatal_ley_80_1993.md",
        categorias=("Contratacion estatal y facturacion",),
        nombre_comun="Estatuto General de Contratacion de la Administracion Publica",
    ),
    NormaEnAlcance(
        filename="contratacion_estatal_ley_1150_2007.md",
        categorias=("Contratacion estatal y facturacion",),
        nombre_comun="Eficiencia y transparencia en la contratacion estatal",
    ),
    NormaEnAlcance(
        filename="sancionatorio_ambiental_ley_1333_2009.md",
        categorias=("Derecho ambiental sancionatorio",),
        nombre_comun="Procedimiento sancionatorio ambiental",
    ),
    NormaEnAlcance(
        filename="ordenamiento_territorial_ley_388_1997.md",
        categorias=("Licencias urbanisticas",),
        nombre_comun="Ley de Ordenamiento Territorial",
    ),
    NormaEnAlcance(
        filename="ley_general_educacion_ley_115_1994.md",
        categorias=("Educacion / debido proceso disciplinario",),
        nombre_comun="Ley General de Educacion",
    ),
    NormaEnAlcance(
        filename="convivencia_escolar_ley_1620_2013.md",
        categorias=("Educacion / debido proceso disciplinario",),
        nombre_comun="Sistema Nacional de Convivencia Escolar",
    ),
    NormaEnAlcance(
        filename="violencia_intrafamiliar_ley_294_1996.md",
        categorias=("Violencia intrafamiliar y medidas de proteccion",),
        nombre_comun="Violencia intrafamiliar",
    ),
    NormaEnAlcance(
        filename="violencia_contra_la_mujer_ley_1257_2008.md",
        categorias=("Violencia intrafamiliar y medidas de proteccion",),
        nombre_comun="Violencia contra la mujer",
    ),
    NormaEnAlcance(
        filename="observancia_propiedad_industrial_ley_1648_2013.md",
        categorias=("Propiedad intelectual - marcas",),
        nombre_comun="Observancia de la propiedad industrial",
        nota="Cobertura parcial: el regimen de marcas es la Decision 486 de la CAN, que no esta.",
    ),
    NormaEnAlcance(
        filename="competencia_desleal_ley_256_1996.md",
        categorias=("Propiedad intelectual - marcas",),
        nombre_comun="Competencia desleal",
    ),
    NormaEnAlcance(
        filename="discapacidad_estabilidad_reforzada_ley_361_1997.md",
        categorias=("Despido",),
        nombre_comun="Integracion social de personas con discapacidad",
        nota="Estabilidad laboral reforzada (despido de persona en situacion de discapacidad).",
    ),
]

# Normas descargadas que NO se indexan en M3, cada una con su razon. Excluir en
# silencio seria indistinguible de un olvido; quien retome el trabajo (RAG
# avanzado) necesita saber que ya estan disponibles y por que se dejaron fuera.
FUERA_DE_ALCANCE: dict[str, str] = {
    # Vacio desde el 2026-10-08: todas las normas descargadas cubren alguna
    # categoria del dataset. La Ley 1581 se excluia por calidad; ahora entra con
    # articulos_propios (ver su entrada).
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
        "articulos_propios": norma.articulos_propios,
        "fragmentos_ajenos": [list(par) for par in norma.fragmentos_ajenos],
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
    print(f"\nCategorias cubiertas: {len(categorias_cubiertas())} de {len(CATEGORIAS_OBJETIVO)} objetivo.")
    for categoria, falta in CATEGORIAS_SIN_NORMA.items():
        print(f"  [ ] {categoria}: {falta}")
