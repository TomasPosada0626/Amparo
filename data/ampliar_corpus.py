"""
Amplia el corpus en las normas que son cuello de botella (ROADMAP #24)
y anota `verificado_el` en todos los fragmentos (ROADMAP #25).

EL CUELLO DE BOTELLA, MEDIDO

    norma                  fragmentos   veces citada en los golds
    Ley 1751 de 2015            2              28
    Ley 1095 de 2006            1              25
    Ley 393 de 1997             3              26
    Ley 472 de 1998             3              25

Un RAG no puede respaldar con dos fragmentos lo que se cita veintiocho veces.
`cubre()` da por respaldada la cita si existe ALGUN fragmento de esa norma, asi
que la cobertura salia al 100% mientras el retrieval seguia trayendo el
articulo equivocado de la norma correcta.

LO QUE SE ANADE, Y DE DONDE SALE

Dos articulos de la Ley 1751 de 2015, transcritos de la impresion oficial de
SUIN-Juriscol (el sistema de informacion normativa del Estado, una de las
fuentes que ya declara data/normas.json), extraidos con pypdf igual que el
Decreto 2591 del corpus original:

  art. 6   Elementos y principios del derecho fundamental a la salud. Sus
           principios d) Continuidad --- "no podra ser interrumpido por
           razones administrativas o economicas" --- y e) Oportunidad ---
           "sin dilaciones" --- son el fundamento exacto de los casos de
           insumos suspendidos (E12) y de lista de espera (E14), que hasta
           ahora se respaldaban con el art. 2, que habla de otra cosa.
  art. 14  Prohibicion de la negacion de prestacion de servicios. Es el
           fundamento del caso mas frecuente del eval set: la EPS que niega
           por un tramite administrativo (E01).

LO QUE NO SE ANADE, Y POR QUE

La Ley 1095 de 2006 sigue siendo el cuello de botella (1 fragmento, 25 citas)
y se queda asi a proposito. Las fuentes oficiales no se pudieron leer:
funcionpublica.gov.co falla la validacion del certificado, secretariasenado.gov.co
rechaza la conexion, y la unica copia accesible --- un PDF en un sitio
universitario --- NO PASO EL COTEJO: el texto del art. 1 que ya esta en el
corpus no aparece en ella, asi que o es otro documento o esta escaneada.

Meter texto legal de una fuente que no se puede verificar destruiria lo unico
que hace util este corpus, que es que cada fragmento es literal y cotejable.
Un resumen tampoco sirve: `transcripcion: "literal"` seria falso. Queda
anotado como trabajo pendiente con la causa, no como un hueco silencioso.

Idempotente: reconstruye desde los fragmentos que no genero este script.
"""
from __future__ import annotations
import json
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

FUENTE_1751 = "https://www.suin-juriscol.gov.co/viewDocument.asp?ruta=Leyes/30019746"
PROCEDENCIA_1751 = (
    "Impresion oficial de SUIN-Juriscol (Sistema Unico de Informacion "
    "Normativa del Estado colombiano), que encabeza 'DIARIO OFICIAL. ANO CL. "
    "N. 49427. 16, FEBRERO, 2015' y 'ESTADO DE VIGENCIA: Vigente'. Texto "
    "extraido con pypdf y normalizado quitando el cromo del visor web (las "
    "cabeceras de pagina y las URLs que SUIN inserta en cada hoja). Ni una "
    "palabra del articulado se modifico."
)

# Fecha en que se coteja el texto contra la fuente. Los fragmentos originales
# llevan la del corpus v1.1.1, que es la que declara su propio `meta`.
HOY = date.today().isoformat()
VERIFICADO_ORIGINAL = "2026-10-15"

NUEVOS = [
    {
        "id": "L1751-06",
        "norma": "Ley 1751 de 2015",
        "articulo": "art. 6",
        "titulo": "Elementos y principios del derecho fundamental a la salud",
        "texto":
            "El derecho fundamental a la salud incluye los siguientes elementos "
            "esenciales e interrelacionados: a) Disponibilidad. El Estado deberá "
            "garantizar la existencia de servicios y tecnologías e instituciones "
            "de salud, así como de programas de salud y personal médico y "
            "profesional competente; b) Aceptabilidad. Los diferentes agentes "
            "del sistema deberán ser respetuosos de la ética médica así como de "
            "las diversas culturas de las personas, minorías étnicas, pueblos y "
            "comunidades, respetando sus particularidades socioculturales y "
            "cosmovisión de la salud, permitiendo su participación en las "
            "decisiones del sistema de salud que le afecten, de conformidad con "
            "el artículo 12 de la presente ley y responder adecuadamente a las "
            "necesidades de salud relacionadas con el género y el ciclo de vida. "
            "Los establecimientos deberán prestar los servicios para mejorar el "
            "estado de salud de las personas dentro del respeto a la "
            "confidencialidad; c) Accesibilidad. Los servicios y tecnologías de "
            "salud deben ser accesibles a todos, en condiciones de igualdad, "
            "dentro del respeto a las especificidades de los diversos grupos "
            "vulnerables y al pluralismo cultural. La accesibilidad comprende la "
            "no discriminación, la accesibilidad física, la asequibilidad "
            "económica y el acceso a la información; d) Calidad e idoneidad "
            "profesional. Los establecimientos, servicios y tecnologías de salud "
            "deberán estar centrados en el usuario, ser apropiados desde el "
            "punto de vista médico y técnico y responder a estándares de calidad "
            "aceptados por las comunidades científicas. Ello requiere, entre "
            "otros, personal de la salud adecuadamente competente, enriquecida "
            "con educación continua e investigación científica y una evaluación "
            "oportuna de la calidad de los servicios y tecnologías ofrecidos. "
            "Así mismo, el derecho fundamental a la salud comporta los "
            "siguientes principios: a) Universalidad. Los residentes en el "
            "territorio colombiano gozarán efectivamente del derecho fundamental "
            "a la salud en todas las etapas de la vida; b) Pro homine. Las "
            "autoridades y demás actores del sistema de salud, adoptarán la "
            "interpretación de las normas vigentes que sea más favorable a la "
            "protección del derecho fundamental a la salud de las personas; "
            "c) Equidad. El Estado debe adoptar políticas públicas dirigidas "
            "específicamente al mejoramiento de la salud de personas de escasos "
            "recursos, de los grupos vulnerables y de los sujetos de especial "
            "protección; d) Continuidad. Las personas tienen derecho a recibir "
            "los servicios de salud de manera continua. Una vez la provisión de "
            "un servicio ha sido iniciada, este no podrá ser interrumpido por "
            "razones administrativas o económicas; e) Oportunidad. La prestación "
            "de los servicios y tecnologías de salud deben proveerse sin "
            "dilaciones; f) Prevalencia de derechos. El Estado debe implementar "
            "medidas concretas y específicas para garantizar la atención "
            "integral a niñas, niños y adolescentes. En cumplimiento de sus "
            "derechos prevalentes establecidos por la Constitución Política. "
            "Dichas medidas se formularán por ciclos vitales: prenatal hasta "
            "seis (6) años, de los (7) a los catorce (14) años, y de los quince "
            "(15) a los dieciocho (18) años; g) Progresividad del derecho. El "
            "Estado promoverá la correspondiente ampliación gradual y continua "
            "del acceso a los servicios y tecnologías de salud, la mejora en su "
            "prestación, la ampliación de capacidad instalada del sistema de "
            "salud y el mejoramiento del talento humano, así como la reducción "
            "gradual y continua de barreras culturales, económicas, geográficas, "
            "administrativas y tecnológicas que impidan el goce efectivo del "
            "derecho fundamental a la salud; h) Libre elección. Las personas "
            "tienen la libertad de elegir sus entidades de salud dentro de la "
            "oferta disponible según las normas de habilitación; i) "
            "Sostenibilidad. El Estado dispondrá, por los medios que la ley "
            "estime apropiados, los recursos necesarios y suficientes para "
            "asegurar progresivamente el goce efectivo del derecho fundamental a "
            "la salud, de conformidad con las normas constitucionales de "
            "sostenibilidad fiscal; j) Solidaridad. El sistema está basado en el "
            "mutuo apoyo entre las personas, generaciones, los sectores "
            "económicos, las regiones y las comunidades; k) Eficiencia. El "
            "sistema de salud debe procurar por la mejor utilización social y "
            "económica de los recursos, servicios y tecnologías disponibles para "
            "garantizar el derecho a la salud de toda la población; l) "
            "Interculturalidad. Es el respeto por las diferencias culturales "
            "existentes en el país y en el ámbito global, así como el esfuerzo "
            "deliberado por construir mecanismos que integren tales diferencias "
            "en la salud, en las condiciones de vida y en los servicios de "
            "atención integral de las enfermedades, a partir del reconocimiento "
            "de los saberes, prácticas y medios tradicionales, alternativos y "
            "complementarios para la recuperación de la salud en el ámbito "
            "global; m) Protección a los pueblos indígenas. Para los pueblos "
            "indígenas el Estado reconoce y garantiza el derecho fundamental a "
            "la salud integral, entendida según sus propias cosmovisiones y "
            "conceptos, que se desarrolla en el Sistema Indígena de Salud Propio "
            "e Intercultural (SISPI); n) Protección pueblos y comunidades "
            "indígenas, ROM y negras, afrocolombianas, raizales y palenqueras. "
            "Para los pueblos y comunidades indígenas, ROM y negras, "
            "afrocolombianas, raizales y palenqueras, se garantizará el derecho "
            "a la salud como fundamental y se aplicará de manera concertada con "
            "ellos, respetando sus costumbres. Parágrafo. Los principios "
            "enunciados en este artículo se deberán interpretar de manera "
            "armónica sin privilegiar alguno de ellos sobre los demás. Lo "
            "anterior no obsta para que sean adoptadas acciones afirmativas en "
            "beneficio de sujetos de especial protección constitucional como la "
            "promoción del interés superior de las niñas, niños y mujeres en "
            "estado de embarazo y personas de escasos recursos, grupos "
            "vulnerables y sujetos de especial protección.",
        "por_que_importa":
            "Los principios d) Continuidad y e) Oportunidad son el fundamento "
            "exacto de los casos de servicio interrumpido por razones "
            "administrativas (E12, insumos suspendidos) y de dilacion indebida "
            "(E14, lista de espera). Antes esos casos se respaldaban con el "
            "art. 2, que define la naturaleza del derecho y no dice nada sobre "
            "continuidad ni plazos.",
    },
    {
        "id": "L1751-14",
        "norma": "Ley 1751 de 2015",
        "articulo": "art. 14",
        "titulo": "Prohibición de la negación de prestación de servicios",
        "texto":
            "Para acceder a servicios y tecnologías de salud no se requerirá "
            "ningún tipo de autorización administrativa entre el prestador de "
            "servicios y la entidad que cumpla la función de gestión de "
            "servicios de salud cuando se trate de atención de urgencia. El "
            "Gobierno Nacional definirá los mecanismos idóneos para controlar el "
            "uso adecuado y racional de dichos servicios y tecnologías en salud. "
            "Parágrafo 1°. En los casos de negación de los servicios que "
            "comprenden el derecho fundamental a la salud con independencia a "
            "sus circunstancias, el Congreso de la República definirá mediante "
            "ley las sanciones penales y disciplinarias, tanto de los "
            "Representantes Legales de las entidades a cargo de la prestación "
            "del servicio como de las demás personas que contribuyeron a la "
            "misma. Parágrafo 2°. Lo anterior sin perjuicio de la tutela.",
        "por_que_importa":
            "Es el fundamento del caso mas frecuente del eval set: la EPS que "
            "niega un servicio por un tramite administrativo (E01, E02). El "
            "paragrafo 2 es explicito en que la prohibicion opera 'sin perjuicio "
            "de la tutela', que es justo lo que el sistema tiene que concluir.",
    },
]
for n in NUEVOS:
    n.update(fuente=FUENTE_1751, vigencia="vigente", transcripcion="literal",
             verificado=True, verificado_el=HOY,
             procedencia=PROCEDENCIA_1751)

GENERADO = re.compile(r"L1751-(06|14)$")

# Las normas que siguen siendo cuello de botella, con la causa. Va al `meta`
# para que el hueco quede DECLARADO y no solo pendiente en un roadmap.
PENDIENTES = {
    "Ley 1095 de 2006": {
        "fragmentos": 1,
        "veces_citada": 25,
        "por_que_no_se_amplio":
            "Las fuentes oficiales no se pudieron leer: funcionpublica.gov.co "
            "falla la validacion del certificado TLS y secretariasenado.gov.co "
            "rechaza la conexion. La unica copia accesible (un PDF en un sitio "
            "universitario) NO PASO EL COTEJO contra el art. 1 que ya esta en "
            "el corpus: su texto no aparece ahi, asi que es otro documento o "
            "esta escaneada. Anadir texto legal de una fuente no verificable "
            "destruiria la unica propiedad que hace util este corpus.",
    },
    "Ley 393 de 1997": {"fragmentos": 3, "veces_citada": 26,
                        "por_que_no_se_amplio": "pendiente, misma via que la 1751"},
    "Ley 472 de 1998": {"fragmentos": 3, "veces_citada": 25,
                        "por_que_no_se_amplio": "pendiente, misma via que la 1751"},
}


def main() -> int:
    ruta = RAIZ / "data" / "corpus.json"
    corpus = json.loads(ruta.read_text(encoding="utf-8"))
    docs = [d for d in corpus["documentos"] if not GENERADO.fullmatch(d["id"])]

    ids = {d["id"] for d in docs}
    for n in NUEVOS:
        if n["id"] in ids:
            print(f"FALLA: el id {n['id']} ya existe y no lo genero este script")
            return 1

    # ROADMAP #25: `verificado_el` en TODOS los fragmentos. `verificado: true`
    # sin fecha no dice cuando se coteja, y una norma puede cambiar.
    for d in docs:
        d.setdefault("verificado_el", VERIFICADO_ORIGINAL)

    docs += NUEVOS
    docs.sort(key=lambda d: d["id"])

    # Higiene: el mismo control que aplica data/auditar_corpus.py.
    sys.path.insert(0, str(RAIZ / "data"))
    import auditar_corpus as aud
    sucios = []
    for n in NUEVOS:
        r = aud.revisar(n)
        mal = [k for k, v in r.items() if v]
        if mal:
            sucios.append((n["id"], mal, r))
    if sucios:
        print("FALLA: los fragmentos nuevos no pasan la higiene. No se escribio.")
        for i, mal, r in sucios:
            print(f"  {i}: {mal}")
            for k in mal:
                print(f"     {k} = {r[k]}")
        return 1

    corpus["documentos"] = docs
    corpus["meta"]["version"] = "1.2.0"
    corpus["meta"]["total_fragmentos"] = len(docs)
    corpus["meta"]["verificado_el"] = {
        "que_significa":
            "fecha en que el texto del fragmento se cotejo contra su `fuente`. "
            "`verificado: true` sin fecha no dice cuando, y una norma puede "
            "cambiar: un fragmento verificado hace dos anos no esta verificado "
            "hoy. data/reverificar_corpus.py lo vuelve a cotejar.",
        "originales": VERIFICADO_ORIGINAL,
        "anadidos_en_1_2_0": HOY,
    }
    corpus["meta"]["ampliacion_1_2_0"] = {
        "anadidos": [{"id": n["id"], "articulo": n["articulo"],
                      "por_que": n["por_que_importa"]} for n in NUEVOS],
        "procedencia": PROCEDENCIA_1751,
        "fuente": FUENTE_1751,
        "cuellos_de_botella_que_siguen_abiertos": PENDIENTES,
        "por_que_hacia_falta":
            "`cubre()` da por respaldada una cita si existe ALGUN fragmento de "
            "esa norma, asi que la cobertura salia al 100% con 2 fragmentos de "
            "la Ley 1751 contra 28 citas: el retrieval traia el articulo "
            "equivocado de la norma correcta y la auditoria no lo veia.",
    }
    ruta.write_text(json.dumps(corpus, ensure_ascii=False, indent=1),
                    encoding="utf-8")

    print(f"OK: corpus v1.2.0 con {len(docs)} fragmentos "
          f"({len(docs) - len(NUEVOS)} + {len(NUEVOS)} nuevos)")
    for n in NUEVOS:
        print(f"   {n['id']}  {n['norma']} {n['articulo']}  "
              f"{len(n['texto'])} chars")
    print(f"\n`verificado_el` anotado en los {len(docs)} fragmentos")
    print(f"\ncuellos de botella que siguen abiertos: "
          f"{', '.join(PENDIENTES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
