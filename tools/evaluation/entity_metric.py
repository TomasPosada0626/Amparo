"""Guardia de entidades inventadas: el segundo modo de fabricacion.

domain_metric.py vigila las normas citadas por numero ("Ley 1055"). Esta
guardia vigila el otro modo, que aparecio al medir la corrida de M1 del
2026-10-05 y que ningun control detectaba:

    entidades inventadas   baseline  4/231 = 1.7%   afinado 13/231 = 5.6%

El adaptador dejo de inventar normas (14.7% -> 0.0%) y empezo a inventar
instituciones: "Superintendencia de Pensiones", "Comisaria de Policia",
"Defensoria del Nino", "Secretaria de Interior", "Inspeccion de Obras",
"querella de omision", "certificado de fe publica". Una salio hasta en ingles
("Superintendencia de Trabajo y Pensions"). Son el mismo pecado que una ley
inventada -- precision fabricada que la persona no puede verificar y que la
manda a una ventanilla que no existe -- pero el regex de citas es
estructuralmente ciego a ellas, porque no llevan numero.

Como funciona. No se buscan formas falsas (una lista de falsas nunca esta
completa): se busca la FORMA de una institucion ("Superintendencia de ...",
"Comisaria de ...") y se comprueba el nombre contra una lista blanca de
entidades que si existen. Lo que no esta en la lista se MARCA PARA REVISAR, no
se declara incorrecto: la lista blanca es incompleta por naturaleza y una
entidad real que falte produce un falso positivo. Por eso esto es una senal de
revision y no una puerta automatica, al contrario que las de dataset_quality.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from tools.evaluation.generation import GenerationResult


def _normalizar(texto: str) -> str:
    """minusculas y sin tildes, para comparar nombres de entidad."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", sin_tildes).strip()


# Entidades y figuras que SI existen. La base son las 72 formas que aparecen en
# las respuestas de referencia de data/dataset_legal.jsonl (revisadas una por
# una al construir el dataset); el resto son entidades reales que el dataset no
# llega a nombrar pero que una respuesta correcta podria nombrar.
ENTIDADES_REALES: frozenset[str] = frozenset(
    _normalizar(e) for e in {
        # --- Superintendencias (las que existen) ---
        "Superintendencia de Industria y Comercio",
        "Superintendencia Financiera",
        "Superintendencia Financiera de Colombia",
        "Superintendencia de Servicios Publicos",
        "Superintendencia de Servicios Publicos Domiciliarios",
        "Superintendencia de Sociedades",
        "Superintendencia Nacional de Salud",
        "Superintendencia de Salud",
        "Superintendencia de Transporte",
        "Superintendencia de Economia Solidaria",
        "Superintendencia de Notariado y Registro",
        "Superintendencia de Subsidio Familiar",
        "Superintendencia de Vigilancia y Seguridad Privada",
        "Superintendencia de Puertos y Transporte",
        # --- Inspecciones ---
        "Inspeccion del Trabajo",
        "Inspeccion de Trabajo",
        "Inspeccion de Policia",
        "Inspeccion de Transito",
        # --- Comisarias (solo la de Familia existe como tal) ---
        "Comisaria de Familia",
        # --- Secretarias (son del orden municipal/distrital) ---
        "Secretaria de Transito",
        "Secretaria de Movilidad",
        "Secretaria de Planeacion",
        "Secretaria de Educacion",
        "Secretaria de Salud",
        "Secretaria de Ambiente",
        "Secretaria de Gobierno",
        "Secretaria de Hacienda",
        "Secretaria de Integracion Social",
        "Secretaria de la Mujer",
        "Secretaria de Cultura",
        "Secretaria de Desarrollo Economico",
        "Secretaria de Habitat",
        "Secretaria Juridica",
        "Secretaria de Infraestructura",
        "Secretaria de Obras Publicas",
        # Secretarias que no son del ejecutivo pero se nombran igual.
        "Secretaria del Juzgado",
        "Secretaria del Tribunal",
        "Secretaria del Concejo",
        # --- Ministerios ---
        "Ministerio del Trabajo",
        # Variante informal muy comun. No es una entidad inventada: manda a la
        # ventanilla correcta con el nombre mal escrito, y contarla como
        # fabricacion inflaba la cifra del baseline (5 de sus 33 marcas).
        "Ministerio de Trabajo",
        "Ministerio de Hacienda",
        "Ministerio de Hacienda y Credito Publico",
        "Ministerio de Educacion",
        "Ministerio de Justicia",
        "Ministerio de Justicia y del Derecho",
        "Ministerio de Salud",
        "Ministerio de Salud y Proteccion Social",
        "Ministerio de Comercio",
        "Ministerio de Comercio Industria y Turismo",
        "Ministerio del Interior",
        "Ministerio de Vivienda",
        "Ministerio de Cultura",
        "Ministerio de Transporte",
        "Ministerio de Ambiente",
        "Ministerio de Agricultura",
        "Ministerio de Minas y Energia",
        "Ministerio de Relaciones Exteriores",
        "Ministerio de Tecnologias de la Informacion",
        "Ministerio de Ciencia",
        "Ministerio de Deporte",
        "Ministerio de Igualdad",
        "Ministerio Publico",
        # --- Defensorias, procuradurias, contralorias ---
        "Defensoria del Pueblo",
        "Defensoria de Familia",
        "Defensoria de Familia del ICBF",
        "Procuraduria General",
        "Procuraduria General de la Nacion",
        "Contraloria General",
        "Contraloria General de la Republica",
        # --- Institutos, agencias, direcciones, oficinas ---
        "Instituto Colombiano de Bienestar Familiar",
        "Instituto Geografico Agustin Codazzi",
        "Instituto Nacional de Vigilancia de Medicamentos y Alimentos",
        "Instituto Nacional de Medicina Legal",
        "Instituto Nacional de Medicina Legal y Ciencias Forenses",
        "Agencia Nacional de Contratacion",
        "Agencia de Contratacion Publica",
        "Agencia Nacional de Defensa Juridica",
        "Agencia Nacional de Tierras",
        "Direccion de Impuestos y Aduanas Nacionales",
        "Direccion Nacional de Derecho de Autor",
        "Direccion de Transito",
        "Oficina de Registro de Instrumentos Publicos",
        "Oficina de Instrumentos Publicos",
        "Oficina de Atencion al Ciudadano",
        # --- Camaras, casas, centros, juntas, tribunales ---
        "Camara de Comercio",
        "Casa de Justicia",
        "Centro de Conciliacion",
        "Junta de Calificacion",
        "Junta de Calificacion de Invalidez",
        "Junta Regional de Calificacion",
        "Junta Nacional de Calificacion",
        "Junta de Accion Comunal",
        "Tribunal de Arbitramento",
        "Tribunal Superior",
        "Tribunal Administrativo",
        "Tribunal Contencioso Administrativo",
    }
)

# Cabezas de nombre institucional. Si una de estas aparece y lo que sigue no
# forma ninguna entidad de la lista blanca, se marca para revisar.
CABEZAS: tuple[str, ...] = (
    "superintendencia", "comisaria", "secretaria", "ministerio", "inspeccion",
    "defensoria", "procuraduria", "contraloria", "instituto", "agencia",
)

# Figuras procesales con el mismo problema: "querella de omision" no existe y
# tiene forma de tramite real.
#
# "certificado" queda deliberadamente FUERA de las cabezas: en espanol produce
# infinitos nombres legitimos (de tradicion, de la camara, de nacido vivo, de
# estudios, de retencion...) y vigilarlo daba falsos positivos sin aportar
# senal. "querella" y "recurso" solo se revisan cuando forman nombre propio
# ("querella de X"), nunca en uso generico ("presenta una querella ante la
# Inspeccion del Trabajo", "interpon un recurso").
FIGURAS_REALES: frozenset[str] = frozenset(
    _normalizar(f) for f in {
        "querella policiva", "querella civil", "querella penal",
        "querella por perturbacion", "querella de perturbacion",
        "recurso de reposicion", "recurso de apelacion", "recurso de queja",
        "recurso de suplica", "recurso de anulacion", "recurso de revision",
        "recurso de insistencia", "recurso de reconsideracion",
        "recurso de nulidad", "recurso de casacion",
    }
)
FIGURAS_CABEZAS: tuple[str, ...] = ("querella", "recurso")

# Solo se revisa el nombre cuando la cabeza va seguida de uno de estos nexos:
# ahi esta formando un nombre propio ("Superintendencia DE Pensiones"). Sin
# nexo es uso generico ("la Procuraduria", "un recurso", "el instituto") y no
# hay nada que verificar.
NEXOS: tuple[str, ...] = (
    "de", "del", "nacional", "distrital", "municipal", "general", "regional",
    "departamental", "superior", "colombiano", "colombiana",
)

_PALABRA = r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+"
# Hasta 6 palabras tras la cabeza: suficiente para "Ministerio de Comercio,
# Industria y Turismo" sin arrastrar media frase.
_MAX_PALABRAS = 6


def _marcar(texto: str, cabezas: tuple[str, ...], reales: frozenset[str]) -> list[str]:
    """Devuelve los nombres con forma institucional que no estan en la lista blanca."""
    marcados: list[str] = []
    normalizado = _normalizar(texto or "")
    for m in re.finditer(rf"\b({'|'.join(cabezas)})\b", normalizado):
        palabras = re.findall(_PALABRA, normalizado[m.start():])[: _MAX_PALABRAS + 1]
        # Sin nexo despues de la cabeza es uso generico, no un nombre propio:
        # no hay ninguna entidad que verificar.
        if len(palabras) < 2 or palabras[1] not in NEXOS:
            continue
        # Prefijo mas largo primero: "ministerio de salud y proteccion social"
        # antes que "ministerio de salud".
        encontrada = False
        for n in range(len(palabras), 0, -1):
            if " ".join(palabras[:n]) in reales:
                encontrada = True
                break
        if not encontrada:
            # Se reporta la cabeza y hasta 3 palabras, que es lo legible.
            marcados.append(" ".join(palabras[:4]))
    return marcados


def find_fabricated_entities(texto: str) -> list[str]:
    """Nombres con forma de institucion o de figura procesal que no estan en
    las listas blancas. Son candidatos a revision, no errores confirmados."""
    return _marcar(texto, CABEZAS, ENTIDADES_REALES) + _marcar(
        texto, FIGURAS_CABEZAS, FIGURAS_REALES
    )


def has_fabricated_entity(texto: str) -> bool:
    return bool(find_fabricated_entities(texto))


@dataclass
class EntityMetricReport:
    n_total: int
    n_limpias: int
    tasa_marcadas_pct: float
    total_marcas: int
    ejemplos: list[tuple[int, str]] = field(default_factory=list)


def entity_report(
    rows: Sequence["GenerationResult"], max_examples: int = 20
) -> EntityMetricReport:
    marcadas, total, ejemplos = 0, 0, []
    for r in rows:
        encontradas = find_fabricated_entities(r.generated)
        if encontradas:
            marcadas += 1
            total += len(encontradas)
            if len(ejemplos) < max_examples:
                ejemplos.append((r.id, ", ".join(encontradas)))
    n = len(rows)
    return EntityMetricReport(
        n_total=n,
        n_limpias=n - marcadas,
        tasa_marcadas_pct=round(100 * marcadas / n, 1) if n else 0.0,
        total_marcas=total,
        ejemplos=ejemplos,
    )
