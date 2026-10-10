"""Propuesta para los 12 objetivos de urgencia que v3 dejo sin generar.

**Nada de aqui queda aprobado ni entra al dataset.** Escribe un archivo de
revision; incorporar cada objetivo exige marcarlo revisado.

## De donde sale la propuesta, y por que no es inventar derecho

Los 12 son variantes B2 de un ejemplo B1 que **ya existe, escrito y pasado por
las puertas de calidad**. Y la respuesta de ese B1 tiene dos partes separables:

    "Si estas en riesgo, llama a la Linea 155 o a la Linea 123 y acude a la
     Comisaria de Familia.  |  Sobre el contrato, el articulo 24 de la Ley 820..."
     ^ orientacion de seguridad            ^ afirmacion juridica
       NO depende del contexto               SI depende del contexto

En modo B2 el contexto no respalda la parte juridica, asi que esa se sustituye
por la frase de escape. **La orientacion de seguridad no depende de ninguna
cita**: es una ruta institucional, y sigue siendo valida aunque la busqueda no
haya traido nada. Por eso sobrevive.

Eso es exactamente lo que la metrica de urgencias exige: **abstenerse del fondo
y encaminar**. Y es lo contrario de lo que hacian los dos casos que cumplian la
abstencion literal y resultaron inseguros (9130 y 9133).

## La trampa, y por que los 12 no son uno solo

En un B1, *"si estas en riesgo, llama al 123"* es aceptable: la respuesta de
fondo tambien se da. En un **B2** se retira el fondo, la ruta queda como lo
unico accionable, y condicionarla es **el fallo del caso 9132**, cuyo criterio
prohibe condicionar la ayuda. Medido con `ayuda_condicionada`:

    5 de 12   la ruta aparece sin condicionar -> la clausula se reutiliza tal cual
    7 de 12   la ruta va detras de una condicion -> hay que descondicionarla, y
              eso es reescribir una orientacion de seguridad: decision de
              producto con revision juridica, no una operacion de texto

    python -m tools.propuesta_urgencias_b2
"""
from __future__ import annotations

import argparse
import json
import re

from tools.evaluation import config as eval_config

RAIZ = eval_config.PROJECT_ROOT
SALIDA = RAIZ / "docs" / "m1_urgencias_b2_propuesta.md"

_ARTICULO = re.compile(r"\bart[ií]culo", re.IGNORECASE)

# Anafora que apunta a algo del texto retirado. En B2 ese referente desaparece y
# la frase queda colgando. Caso 4605: "Pide ESA MEDIDA en la Comisaria de
# Familia" -- la medida la nombraba el art. 19 de la Ley 1257, que en B2 ya no
# esta. Una version anterior de esta comprobacion no incluia "esa" y dio el caso
# por limpio.
_ANAFORA = re.compile(r"\b(es[ae]|eso|dich[oa]|el citado|mencionad\w*|lo anterior)\b",
                      re.IGNORECASE)

# Los 12 originales cuya variante B2 no se genero. Vienen del manifiesto de v3
# (`variantes_descartadas`, razon URGENCIA_REQUIERE_OBJETIVO_A_MANO); se listan
# aqui para que el archivo de revision sea reproducible sin reconstruir v3.
ORIGINALES = [2105, 2411, 2508, 2613, 4009, 4205, 4206, 4207, 4219, 4605, 4607, 4617]

# Lo que un objetivo B2 de urgencia tiene que cumplir para incorporarse. Son las
# condiciones que ya estan implementadas y medidas; no se añade ninguna nueva.
CRITERIOS = [
    ("empieza con la frase de escape exacta",
     "`es_valvula_de_escape` y el juez la buscan literal"),
    ("ofrece al menos una ruta de ayuda inmediata",
     "`AYUDA_INMEDIATA`; es el fallo por omision de 9130 y 9133"),
    ("la ruta NO va condicionada",
     "`ayuda_condicionada`; es el fallo de 9132, cuyo criterio lo prohibe"),
    ("no cita ningun articulo",
     "puerta `cita en escape`: el contexto no respalda nada"),
    ("no propone un tramite escrito como unico paso",
     "`actuacion_diferida`; es el fallo de 9129"),
    ("10-45 palabras",
     "mismo rango que los demas B2 (`PALABRAS` de dataset_v2_quality)"),
]


def clausulas_de_seguridad(respuesta: str) -> list[str]:
    """Las frases que dan una ruta inmediata y no dependen de ninguna cita."""
    from tools.dataset_quality import AYUDA_INMEDIATA

    frases = [s.strip() for s in re.split(r"(?<=[.;])\s+", respuesta or "") if s.strip()]
    return [s for s in frases
            if AYUDA_INMEDIATA.search(s) and not _ARTICULO.search(s)]


def propuesta_de(registro: dict) -> dict:
    """La propuesta de un caso, con su clasificacion y por que."""
    from tools.evaluation.seguridad_urgencias_reglas import (ayuda_condicionada,
                                                         emergencia_condicionada)
    from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

    clausulas = clausulas_de_seguridad(registro["messages"][-1]["content"])
    objetivo = f"{RESPUESTA_SIN_CONTEXTO}. {' '.join(clausulas)}".strip()
    cuerpo = " ".join(clausulas)
    condicionada = ayuda_condicionada(objetivo)
    emergencia = emergencia_condicionada(objetivo)
    anaforas = sorted(set(m.group(0).lower() for m in _ANAFORA.finditer(cuerpo)))
    problemas = []
    if condicionada:
        problemas.append(f"ruta condicionada: {condicionada}")
    if emergencia:
        problemas.append(f"ruta de EMERGENCIA condicionada: {emergencia}")
    if anaforas:
        problemas.append(f"anafora sin referente en B2: {anaforas}")
    return {
        "original": registro["id"],
        "categoria": registro["category"],
        "pregunta": registro["pregunta"],
        "clausulas_del_b1": clausulas,
        "objetivo_propuesto": objetivo if not problemas else "",
        "clase": "B_REDACTAR" if problemas else "A_REUTILIZABLE",
        "problemas": problemas,
        "condicionada": condicionada,
        "estado": "pendiente_validacion_juridica",
    }


def verificar(objetivo: str, pregunta: str) -> list[str]:
    """Que criterios NO cumple un objetivo. Vacio = los cumple todos."""
    from tools.dataset_quality import AYUDA_INMEDIATA
    from tools.evaluation.ragas_metrics import es_valvula_de_escape
    from tools.evaluation.seguridad_urgencias_reglas import (actuacion_diferida,
                                                             ayuda_condicionada)
    from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

    fallos = []
    if not (objetivo or "").startswith(RESPUESTA_SIN_CONTEXTO):
        fallos.append("no empieza con la frase de escape")
    if not es_valvula_de_escape(objetivo):
        fallos.append("no se reconoce como valvula de escape")
    if not AYUDA_INMEDIATA.search(objetivo or ""):
        fallos.append("sin ruta de ayuda inmediata")
    if ayuda_condicionada(objetivo):
        fallos.append("la ruta va condicionada")
    if _ARTICULO.search(objetivo or ""):
        fallos.append("cita un articulo")
    if actuacion_diferida(objetivo):
        fallos.append("solo propone un tramite escrito")
    n = len((objetivo or "").split())
    if not 10 <= n <= 45:
        fallos.append(f"longitud {n}, fuera de 10-45")
    return fallos


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--json", action="store_true", help="imprime el detalle en JSON")
    args = p.parse_args(argv)

    regs = {r["id"]: r for r in (json.loads(l) for l in
            (RAIZ / "data" / "dataset.jsonl").read_text(encoding="utf-8").splitlines()
            if l.strip())}
    props = [propuesta_de(regs[i]) for i in ORIGINALES if i in regs]
    a = [x for x in props if x["clase"] == "A_REUTILIZABLE"]
    b = [x for x in props if x["clase"] == "B_REDACTAR"]

    if args.json:
        print(json.dumps(props, ensure_ascii=False, indent=2))
        return 0

    partes = [
        "# Los 12 objetivos de urgencia de B2: propuesta para validacion",
        "",
        "**Ninguno esta aprobado.** Son propuestas; cada una necesita el visto",
        "bueno juridico antes de entrar al entrenamiento. El dataset v3 los dejo",
        "fuera a proposito, y mientras no se validen sigue entrenando sin ellos.",
        "",
        "## De donde sale cada propuesta",
        "",
        "Cada uno es la variante B2 de un ejemplo B1 **que ya existe y paso las",
        "puertas**. La respuesta de ese B1 tiene dos partes: una orientacion de",
        "seguridad que **no depende de ninguna cita**, y una afirmacion juridica que",
        "si depende. En B2 la segunda se sustituye por la frase de escape y la",
        "primera sobrevive, porque una ruta institucional sigue siendo valida aunque",
        "la busqueda no haya traido nada.",
        "",
        "## Criterios de aceptacion (fijados antes de redactar)",
        "",
        "| criterio | de donde viene |",
        "|---|---|",
    ]
    partes += [f"| {c} | {por} |" for c, por in CRITERIOS]
    partes += [
        "",
        "---",
        "",
        f"# Clase A -- la clausula se reutiliza tal cual ({len(a)} casos)",
        "",
        "La ruta de ayuda aparece **sin condicionar** en el B1 original, asi que",
        "pasa los criterios sin reescribir nada. Lo que se pide validar es que la",
        "ruta siga siendo la correcta cuando se retira la parte juridica.",
        "",
    ]
    for x in a:
        fallos = verificar(x["objetivo_propuesto"], x["pregunta"])
        partes += [
            f"### {x['original']} — {x['categoria']}",
            "",
            f"**Pregunta:** {x['pregunta']}",
            "",
            f"**Objetivo propuesto:** {x['objetivo_propuesto']}",
            "",
            f"**Criterios automaticos:** {'TODOS OK' if not fallos else 'FALLA: ' + ', '.join(fallos)}",
            "",
            "**Validar:** [ ] la ruta es la correcta para esta situacion  "
            "[ ] no falta un paso inmediato",
            "",
        ]
    partes += [
        "---",
        "",
        f"# Clase B -- hay que descondicionar la ruta ({len(b)} casos)",
        "",
        "**No se propone un texto.** En estos la ruta va detras de una condicion",
        "(*\"si estas en riesgo, llama al 123\"*). En un B1 eso es aceptable porque",
        "la respuesta de fondo tambien se da; en un **B2** se retira el fondo, la",
        "ruta queda como lo unico accionable, y condicionarla es **el fallo del caso",
        "9132**, cuyo criterio lo prohibe expresamente.",
        "",
        "Descondicionar una orientacion de seguridad -- decidir que la persona debe",
        "llamar **ya**, no \"si lo cree necesario\" -- es una decision de producto con",
        "revision juridica, no una operacion de texto. Por eso aqui va la clausula",
        "original y la casilla vacia.",
        "",
    ]
    for x in b:
        partes += [
            f"### {x['original']} — {x['categoria']}",
            "",
            f"**Pregunta:** {x['pregunta']}",
            "",
            f"**Clausula del B1 (condicionada):** {' '.join(x['clausulas_del_b1'])}",
            "",
            f"**Condicionada en:** {', '.join(x['condicionada'])}",
            "",
            "**Objetivo a redactar:** _(vacio a proposito)_",
            "",
            "```",
            "No tengo informacion verificada sobre esto en mi base de conocimiento. ",
            "```",
            "",
        ]
    partes += [
        "---",
        "",
        "# Resumen",
        "",
        "| clase | casos | que falta |",
        "|---|---|---|",
        f"| A reutilizable | {len(a)} | confirmar que la ruta sigue siendo la correcta |",
        f"| B descondicionar | {len(b)} | redactar la orientacion sin condicion |",
        f"| **total** | **{len(props)}** | |",
        "",
        "Mientras no se validen, el entrenamiento corre **sin** estos 12. Son 12 de",
        "2703 ejemplos: la perdida en masa de entrenamiento es despreciable y el",
        "riesgo que se evita -- ensenar una abstencion peligrosa sobre una urgencia",
        "-- es el peor del dataset.",
        "",
    ]
    SALIDA.write_text("\n".join(partes), encoding="utf-8", newline="\n")
    print(f"Escrito {SALIDA.relative_to(RAIZ)}")
    print(f"  clase A (reutilizable tal cual): {len(a)}  -> {[x['original'] for x in a]}")
    print(f"  clase B (descondicionar):        {len(b)}  -> {[x['original'] for x in b]}")
    for x in a:
        fallos = verificar(x["objetivo_propuesto"], x["pregunta"])
        if fallos:
            print(f"    AVISO {x['original']}: {fallos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
