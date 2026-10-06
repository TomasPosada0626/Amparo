"""Guardia de rutas: entidades y figuras REALES usadas en el lugar equivocado.

entity_metric.py detecta instituciones que no existen ("Superintendencia de
Pensiones"). Esta guardia detecta el error que esa no puede ver, y que aparecio
al revisar a mano la corrida de M1 del 2026-10-06: el modelo afinado aprendio
los nombres del dataset y los aplica donde no corresponden.

    "querella ... ante la Procuraduria"   9 respuestas afinadas, 0 del baseline
    "conciliacion ... en la Comisaria de Familia" para un prestamo gota a gota
    "juez de control del tribunal superior" para ejecutar una sentencia extranjera
    "Linea 123 del Ministerio del Interior"

Todas las entidades existen, asi que una lista blanca no las marca. Pero
mandan a la persona a una ventanilla que no tramita su caso.

Se vigila de dos formas, que se complementan:

1. REGLAS: combinaciones tramite -> entidad que el derecho colombiano no
   admite, escritas a mano y explicadas una por una. Cada regla se valida
   contra las 1536 respuestas de referencia del dataset (tests/evaluation/
   test_rutas.py): una regla que marca una referencia esta mal escrita, o
   encontro un error del dataset. Detectan solo los errores que ya
   conocemos.

2. CONTEXTO: para cada concepto (entidad o figura) se aprende del TRAIN en que
   temas aparece. Si una respuesta usa un concepto que las referencias de
   train nunca usan para ese tema, se marca "fuera de contexto". El tema se
   toma de la categoria de la pregunta y de las preguntas de train mas
   parecidas (las categorias de abstencion mezclan temas: "gota a gota" cae en
   Urgencia, pero sus vecinas son de Prestamos informales). Detecta errores que
   nadie escribio en una regla, al precio de falsos positivos: un concepto
   correcto que el dataset no llego a usar para ese tema. Su tasa base se mide
   corriendo la misma guardia sobre las respuestas de REFERENCIA de val, que
   son correctas por construccion: lo que marque ahi es ruido.

Ninguna de las dos declara un error: marcan para revisar. La correccion juridica
la juzga Groq (judge.py pide los errores juridicos concretos) y una revision
humana de una muestra.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence

from tools.evaluation.similitud import IndiceTfidf, normalizar


# Categorias del dataset que no son un tema juridico sino un tipo de pregunta
# (ids 1411-1536). Su tema sale de las preguntas vecinas, no de la categoria.
CATEGORIAS_ABSTENCION: frozenset[str] = frozenset({
    "Fuera del derecho colombiano",
    "Peticiones de cita o plazo exacto",
    "Peticiones de garantia de resultado",
    "Peticiones de conducta ilegitima",
    "Preguntas ambiguas",
    "Urgencia con ayuda inmediata",
})


# --------------------------------------------------------------------------
# 1. Reglas: tramite -> entidad que no corresponde
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Regla:
    clave: str
    patron: str            # regex sobre la respuesta normalizada
    explicacion: str
    # regex sobre la PREGUNTA normalizada: la regla solo aplica si la pregunta
    # la cumple (para errores que dependen del caso, no solo de la respuesta).
    si_pregunta: Optional[str] = None
    # regex sobre la respuesta: si aparece, la regla NO marca (la respuesta ya
    # nombra la ruta correcta).
    salvo: Optional[str] = None
    # regex sobre la pregunta: si aparece, la regla NO marca (el caso si es del
    # tema donde esa ruta es correcta).
    salvo_pregunta: Optional[str] = None


# Entre el tramite y "ante" no puede haber otro "ante", otro tramite, otro verbo
# de ir a una oficina ni una coma: sin eso, "la demanda ante el juez civil o la
# denuncia ante la Fiscalia" (referencia 360) se leia como "demanda ante la
# Fiscalia", y "presenta la querella y, si no hay acuerdo, acude ante el juez"
# como "querella ante el juez".
_ANTE = (r"(?:(?!\bante\b|\b(?:denuncia|queja|querella|demanda|tutela|reclamo|solicitud|acud\w*|"
         r"concili\w*|ve|vaya|ir|si)\b)[^.;:,]){0,40}?\bante (?:el |la |los |las |un |una |tu |su )?")
# "secretaria" sin "del juzgado/tribunal": la tutela si se radica en la
# secretaria de un despacho judicial.
_NO_JUEZ = (r"(?:procuraduria|defensoria|personeria|superintendencia|super\w+|ministerio|"
            r"fiscalia|inspeccion|inspector|comisaria|comisario|alcaldia|"
            r"secretaria(?! (?:del|de la) (?:juzgado|tribunal|corte|oficina judicial))|"
            r"curador|curaduria|notaria|registraduria|policia)")

# Sentencia extranjera: el pais tiene que ir pegado al fallo o al juez ("un juez
# de Mexico dicto...", "mi divorcio en Espana", "una sentencia extranjera"). Que
# la pregunta solo nombre un pais ("mi esposo vive en Espana, como me divorcio?")
# no basta: ese divorcio se tramita ante un juez de familia colombiano.
_PAIS = (r"(?:espana|estados unidos|venezuela|ecuador|peru|mexico|chile|argentina|usa|eeuu|panama|"
         r"italia|francia|alemania|canada|brasil)\b")
_FALLO = r"(?:sentencia|fallo|divorcio|condena)"
_SENTENCIA_EXTRANJERA = (
    rf"\b{_FALLO}\s+(?:\w+\s+){{0,3}}?(?:extranjer\w*|del exterior|de otro pais|"
    rf"(?:de|en|del)\s+(?:los\s+|la\s+)?{_PAIS})"
    rf"|\b(?:juez|jueza|tribunal|corte|justicia)\s+(?:de|del|en)\s+(?:los\s+|la\s+)?{_PAIS}"
)

REGLAS: tuple[Regla, ...] = (
    Regla(
        "querella_ante_procuraduria",
        rf"\bquerella{_ANTE}procuraduria",
        "Ante la Procuraduria se presenta una queja disciplinaria contra un servidor "
        "publico, no una querella.",
    ),
    Regla(
        "querella_ante_juez",
        rf"\bquerella{_ANTE}(?:juez|juzgado)",
        "Ante un juez se presenta una demanda. La querella penal va a la Fiscalia y "
        "la policiva al inspector de policia.",
    ),
    Regla(
        "querella_ante_entidad_sin_competencia",
        rf"\bquerella{_ANTE}(?:curador|curaduria|superintendencia|super\w+|defensoria|"
        r"personeria|notaria)",
        "Ninguna de esas entidades tramita querellas: la policiva va a la Inspeccion "
        "de Policia (o al alcalde o corregidor donde no hay inspector, por eso la "
        "alcaldia no se marca), la laboral a la Inspeccion del Trabajo y la penal a "
        "la Fiscalia.",
    ),
    Regla(
        "demanda_ante_autoridad_no_judicial",
        rf"\bdemanda(?:r)?{_ANTE}(?:comisaria|comisario|inspeccion de policia|inspector|"
        r"fiscalia|procuraduria|personeria|defensoria|curador|curaduria|alcaldia)",
        "Una demanda se presenta ante un juez (o ante una superintendencia con "
        "funciones jurisdiccionales), no ante una autoridad administrativa o la Fiscalia.",
    ),
    Regla(
        "tutela_ante_autoridad_no_judicial",
        rf"\b(?:presenta\w*|interpon\w*|radica\w*|pon\w*|instaura\w*) (?:una |la )?"
        rf"(?:accion de )?tutela ante (?:el |la |un |una )?{_NO_JUEZ}",
        "La tutela se presenta ante un juez. Personeria y Defensoria pueden ayudar a "
        "redactarla, pero no la deciden.",
    ),
    Regla(
        "habeas_corpus_ante_autoridad_no_judicial",
        rf"\bhabeas corpus{_ANTE}{_NO_JUEZ}",
        "El habeas corpus lo resuelve un juez.",
    ),
    Regla(
        "juez_de_control_fuera_de_lo_penal",
        r"\bjuez(?:es)? de control\b",
        "El juez de control de garantias solo existe en el proceso penal.",
        salvo=r"fiscalia|denuncia|delito|penal|captura|imputacion|victima",
    ),
    Regla(
        "sentencia_extranjera_sin_corte_suprema",
        r"\b(?:juez|juzgado|tribunal superior|tribunal)\b",
        "Una sentencia extranjera solo produce efectos en Colombia tras el exequatur "
        "ante la Corte Suprema de Justicia.",
        si_pregunta=_SENTENCIA_EXTRANJERA,
        salvo=r"corte suprema|exequatur",
    ),
    Regla(
        "linea_123_atribuida_a_ministerio",
        r"\blinea 123 (?:del|de la) ministerio|\b123 del ministerio",
        "La linea 123 es el numero unico de emergencias (Policia y organismos de "
        "socorro), no una linea de un ministerio.",
    ),
    Regla(
        "conciliacion_familiar_fuera_de_familia",
        r"\bconcilia\w*[^.;]{0,100}?(?:comisaria de familia|comisario de familia|"
        r"defensoria de familia|defensor de familia)",
        "Comisarias y defensorias de familia concilian asuntos de familia (alimentos, "
        "custodia, visitas), no deudas ni conflictos civiles.",
        si_pregunta=r"prest|deuda|gota a gota|cobr|interes|arriend|contrato|compra|vend|banco",
        salvo_pregunta=(r"aliment|custodia|visitas|\bhij|pareja|conyug|esposo|esposa|familia|"
                        r"\bpapa\b|\bmama\b|padre|madre|violencia"),
    ),
)

def _re(patron: Optional[str]):
    return re.compile(patron) if patron else None


_REGLAS_RE = [(r, re.compile(r.patron), _re(r.si_pregunta), _re(r.salvo), _re(r.salvo_pregunta))
              for r in REGLAS]


def rutas_incorrectas(respuesta: str, pregunta: str = "") -> list[str]:
    """Claves de las reglas que la respuesta viola."""
    resp, preg = normalizar(respuesta), normalizar(pregunta)
    salida = []
    for regla, patron, si_preg, salvo, salvo_preg in _REGLAS_RE:
        if si_preg is not None and not si_preg.search(preg):
            continue
        if salvo is not None and salvo.search(resp):
            continue
        if salvo_preg is not None and salvo_preg.search(preg):
            continue
        if patron.search(resp):
            salida.append(regla.clave)
    return salida


EXPLICACIONES = {r.clave: r.explicacion for r in REGLAS}


# --------------------------------------------------------------------------
# 2. Contexto: conceptos que el train nunca usa para ese tema
# --------------------------------------------------------------------------

# Entidades y figuras con competencia acotada a ciertos temas. Quedan fuera las
# que sirven para casi todo (derecho de peticion, conciliacion, recursos,
# consultorio juridico, Personeria, Defensoria del Pueblo, Policia): marcarlas
# fuera de contexto seria ruido.
CONCEPTOS: dict[str, str] = {
    "Superintendencia de Industria y Comercio": r"superintendencia de industria y comercio|\bsic\b",
    "Superintendencia Financiera": r"superintendencia financiera|superfinanciera|defensor del consumidor financiero",
    "Superintendencia de Salud": r"superintendencia (?:nacional )?de salud|supersalud",
    "Superintendencia de Servicios Publicos": r"superintendencia de servicios publicos|superservicios",
    "Superintendencia de Transporte": r"superintendencia de (?:puertos y )?transporte|supertransporte",
    "Superintendencia de Sociedades": r"superintendencia de sociedades|supersociedades",
    "Superintendencia de Notariado y Registro": r"superintendencia de notariado|supernotariado",
    "Inspeccion del Trabajo": r"inspeccion (?:del|de) trabajo|inspector (?:del|de) trabajo",
    "Inspeccion de Policia": r"inspeccion de policia|inspector de policia",
    "Comisaria de Familia": r"comisaria de familia|comisario de familia|comisaria\b|comisario\b",
    "ICBF / Defensoria de Familia": r"\bicbf\b|bienestar familiar|defensoria de familia|defensor de familia",
    "Procuraduria": r"procuraduria",
    "Fiscalia": r"fiscalia",
    "Juez de control de garantias": r"juez(?:es)? de control",
    "Juez laboral": r"juez laboral|juzgado laboral|jurisdiccion laboral|juez del trabajo",
    "Juez de familia": r"juez de familia|juzgado de familia",
    "Jurisdiccion contencioso administrativa": (r"juez administrativo|juzgado administrativo|"
                                                r"contencioso administrativ|tribunal administrativo"),
    "Corte Suprema de Justicia": r"corte suprema",
    "Consejo de Estado": r"consejo de estado",
    "Medicina Legal": r"medicina legal",
    "Junta de Calificacion de Invalidez": r"junta (?:regional |nacional )?de calificacion",
    "DIAN": r"\bdian\b",
    "Registraduria": r"registraduria",
    "Oficina de Registro de Instrumentos Publicos": r"oficina de registro|instrumentos publicos",
    "Camara de Comercio": r"camara de comercio",
    "Secretaria de Transito / Movilidad": r"secretaria de (?:transito|movilidad)|organismo de transito|autoridad de transito",
    "Colpensiones": r"colpensiones",
    "Fondo de pensiones": r"fondo de pensiones|\bafp\b",
    "EPS": r"\beps\b",
    "ARL": r"\barl\b",
    "SOAT": r"\bsoat\b",
    "Curaduria urbana": r"curador urbano|curaduria",
    "Autoridad ambiental": r"corporacion autonoma|\bcar\b|autoridad ambiental|\banla\b",
    "Direccion Nacional de Derecho de Autor": r"derecho de autor",
    "Contraloria": r"contraloria",
    "Colombia Compra Eficiente": r"colombia compra",
    "Notaria": r"\bnotaria|\bnotario",
    "Querella": r"\bquerella",
    "Habeas corpus": r"habeas corpus",
    "Habeas data": r"habeas data",
    "Accion popular": r"accion popular",
    "Accion de cumplimiento": r"accion de cumplimiento",
    "Proceso ejecutivo": r"(?:demanda|proceso|accion) ejecutiv",
    "Restitucion de inmueble": r"restitucion de(?:l)? inmueble",
    "Proceso monitorio": r"monitorio",
    "Nulidad y restablecimiento": r"nulidad y restablecimiento",
    "Medida de proteccion": r"medidas? de proteccion",
    "Incidente de reparacion": r"incidente de reparacion",
    "Revocatoria directa": r"revocatoria directa",
    "Silencio administrativo": r"silencio administrativo",
    "Exequatur": r"exequatur",
    "Registro de marca": r"registro de (?:la )?marca|\bmarca registrada",
}
_CONCEPTOS_RE = {k: re.compile(v) for k, v in CONCEPTOS.items()}


def conceptos(texto: str) -> set[str]:
    t = normalizar(texto)
    return {k for k, p in _CONCEPTOS_RE.items() if p.search(t)}


@dataclass
class MapaContexto:
    """Lo que el train dice de cada tema. Se construye una vez con
    construir_mapa(train_records) y se reusa para todas las respuestas."""
    por_categoria: dict[str, set[str]]          # categoria -> conceptos usados en sus referencias
    vecinos_k: int
    _indice: Optional[IndiceTfidf] = field(repr=False, default=None)
    _docs: list[tuple[str, set[str]]] = field(repr=False, default_factory=list)

    def vecinos(self, pregunta: str) -> list[tuple[str, set[str]]]:
        """(categoria, conceptos de la referencia) de las k preguntas de train mas parecidas."""
        if self._indice is None:
            return []
        return [self._docs[i] for i, _ in self._indice.parecidos(pregunta, self.vecinos_k)]

    def permitidos(self, pregunta: str, categoria: str) -> set[str]:
        """Conceptos que el train usa para ese tema: los de la categoria (si es
        un tema) y los de las categorias de las preguntas vecinas. Una vecina de
        una categoria de abstencion aporta solo los conceptos de SU referencia."""
        ok: set[str] = conceptos(pregunta)   # lo que la persona misma nombra no esta fuera de tema
        if categoria not in CATEGORIAS_ABSTENCION:
            ok |= self.por_categoria.get(categoria, set())
        for cat, conc in self.vecinos(pregunta):
            ok |= conc if cat in CATEGORIAS_ABSTENCION else self.por_categoria.get(cat, set())
        return ok


def construir_mapa(train_records: Sequence[dict], vecinos_k: int = 5) -> MapaContexto:
    """train_records: registros del dataset (messages system/user/assistant).
    vecinos_k=5, medido sobre la corrida de M1 del 2026-10-06: con 3 el ruido
    sobre las referencias de val sube de 0.9 % a 1.7 %; con 8 baja a 0.4 %, pero
    las afinadas marcadas bajan de 24 a 20 (el vecindario se vuelve tan amplio
    que casi todo concepto cabe)."""
    por_categoria: dict[str, set[str]] = defaultdict(set)
    docs = []
    for r in train_records:
        conc = conceptos(r["messages"][2]["content"])
        por_categoria[r["category"]] |= conc
        docs.append((r["category"], conc))
    return MapaContexto(
        por_categoria=dict(por_categoria),
        vecinos_k=vecinos_k,
        _indice=IndiceTfidf([r["messages"][1]["content"] for r in train_records]),
        _docs=docs,
    )
def fuera_de_contexto(respuesta: str, pregunta: str, categoria: str, mapa: MapaContexto) -> list[str]:
    """Conceptos de la respuesta que el train nunca usa para ese tema."""
    return sorted(conceptos(respuesta) - mapa.permitidos(pregunta, categoria))


# --------------------------------------------------------------------------
# Reporte
# --------------------------------------------------------------------------

@dataclass
class RevisionRutas:
    id: int
    rutas_incorrectas: list[str]
    fuera_de_contexto: list[str]

    @property
    def marcada(self) -> bool:
        return bool(self.rutas_incorrectas or self.fuera_de_contexto)


def revisar(respuesta: str, pregunta: str, categoria: str, mapa: MapaContexto, id: int = 0) -> RevisionRutas:
    return RevisionRutas(
        id=id,
        rutas_incorrectas=rutas_incorrectas(respuesta, pregunta),
        fuera_de_contexto=fuera_de_contexto(respuesta, pregunta, categoria, mapa),
    )


@dataclass
class ReporteRutas:
    etiqueta: str
    n: int
    con_ruta_incorrecta: int
    fuera_de_contexto: int
    marcadas: int
    por_regla: dict[str, int]
    por_concepto: dict[str, int]
    detalle: list[RevisionRutas]

    @property
    def pct_ruta_incorrecta(self) -> float:
        return round(100 * self.con_ruta_incorrecta / self.n, 1) if self.n else 0.0

    @property
    def pct_fuera_de_contexto(self) -> float:
        return round(100 * self.fuera_de_contexto / self.n, 1) if self.n else 0.0

    @property
    def pct_marcadas(self) -> float:
        return round(100 * self.marcadas / self.n, 1) if self.n else 0.0


def reporte(etiqueta: str, filas: Iterable, mapa: MapaContexto) -> ReporteRutas:
    """filas: objetos con .id, .query, .category y .generated (GenerationResult,
    EvalRow) -- o dicts con esas claves."""
    detalle, por_regla, por_concepto = [], Counter(), Counter()
    for f in filas:
        g = (lambda k: f[k]) if isinstance(f, dict) else (lambda k: getattr(f, k))
        rev = revisar(g("generated"), g("query"), g("category"), mapa, id=g("id"))
        detalle.append(rev)
        por_regla.update(rev.rutas_incorrectas)
        por_concepto.update(rev.fuera_de_contexto)
    return ReporteRutas(
        etiqueta=etiqueta,
        n=len(detalle),
        con_ruta_incorrecta=sum(1 for d in detalle if d.rutas_incorrectas),
        fuera_de_contexto=sum(1 for d in detalle if d.fuera_de_contexto),
        marcadas=sum(1 for d in detalle if d.marcada),
        por_regla=dict(por_regla.most_common()),
        por_concepto=dict(por_concepto.most_common()),
        detalle=detalle,
    )


def referencias_como_filas(records: Sequence[dict]) -> list[dict]:
    """Las respuestas de referencia de val como si fueran generadas: es la
    calibracion. Lo que la guardia marque aqui es ruido, porque las
    referencias son correctas por construccion."""
    return [{"id": r["id"], "query": r["messages"][1]["content"], "category": r["category"],
             "generated": r["messages"][2]["content"]} for r in records]
