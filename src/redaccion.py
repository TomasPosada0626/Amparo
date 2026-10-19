"""
Convierte el bloque de triaje en lenguaje natural, SIN añadirle nada.

POR QUÉ ESTA CAPA EXISTE, Y POR QUÉ ES UNA CAPA Y NO UN MODELO DISTINTO

El modelo de M1 se afinó con la instrucción literal «responde SIEMPRE con
exactamente cinco líneas... sin texto adicional». No conversa, y eso es
diseño: el bloque es **la decisión**, y vale 87.3% de acierto jurídico con
intervalo [0.794, 0.952]. Cuando alguien escribe «me echaron del trabajo sin
aviso, ¿qué hago?», quiere una respuesta en su idioma; pero la respuesta tiene
que venir de esa decisión, no de un modelo suelto.

La alternativa obvia --- apagar el adaptador y dejar que conteste el modelo
base --- está medida y descartada: **3.2% de acierto jurídico y cero citas
emitidas**. Hablaría con fluidez y se equivocaría en 30 de cada 31 casos. Es
lo peor que puede hacer un sistema jurídico: sonar convincente y estar mal.

    relato → modelo afinado → BLOQUE (auditable) → redactar() → texto

LA RESTRICCIÓN QUE HACE SEGURA LA CAPA

`redactar()` sólo puede reformular lo que el bloque ya dice. No puede añadir
una norma que no esté, ni afirmar un hecho que el bloque no contenga. Y no es
una promesa: `verificar_texto()` extrae las citas del texto y falla si alguna
no estaba en el bloque, con la misma maquinaria que mide la alucinación
normativa en el resto del proyecto.

EL RIESGO QUE HAY QUE DECIR EN VOZ ALTA

1 de cada 8 respuestas va a estar mal, y **en prosa fluida un error convence
más que en un bloque seco**. Por eso el texto dice siempre, explícitamente,
qué mecanismo procede y si procede la tutela: para que un error siga siendo
detectable de un vistazo. Y por eso cierra con una línea que dice lo que es.

LO QUE ESTA CAPA HACE Y GOOGLE NO

A «me echaron del trabajo sin aviso ni justificación», un buscador contesta
que tienes derecho a una indemnización. Es cálido y es la mitad fácil: no dice
ante quién vas ni por qué vía. El motor del art. 6 sí lo sabe --- vía laboral
ordinaria por subsidiariedad, art. 6.1 del Decreto 2591 --- y sabe además qué
dato lo cambiaría: si hubiera sujeto de especial protección o perjuicio
irremediable, pasaría a tutela transitoria. Eso último es lo más útil para
quien pregunta, y sale de `etiqueta_pivota_en`, no de la imaginación.
"""
from __future__ import annotations

import re

import metricas
import schema

REGISTROS = ("ciudadano", "abogado")

_SISTEMA = """Eres un redactor que explica en español claro el resultado de un
triaje de acciones constitucionales colombianas. NO eres el que decide: la
decisión ya está tomada y te llega en un bloque de campos.

REGLAS INVIOLABLES
1. NO añadas ninguna norma, ley, artículo ni sentencia que no esté en el
   bloque. Ni una. Si el bloque no cita nada, no cites nada.
2. NO afirmes hechos que el bloque no contenga. No supongas el tipo de
   contrato, el tiempo trabajado, la enfermedad ni nada parecido.
3. Di SIEMPRE y de forma explícita qué mecanismo procede y si procede la
   tutela. Es lo que permite detectar un error de un vistazo.
4. Si te doy una condición que cambiaría el mecanismo, menciónala: es lo más
   útil para quien pregunta.
5. Cierra con: «Esto es un triaje automático, no un concepto jurídico.»

REGISTRO {registro}
{instruccion}

Escribe entre 80 y 180 palabras. Sin encabezados ni listas numeradas: prosa."""

_INSTRUCCION = {
    "ciudadano": (
        "Habla como a una persona que no es abogada y está preocupada. "
        "Empieza reconociendo su situación en una frase, sin dramatizar. "
        "Di qué puede hacer y ante quién. Evita latinismos y nombres de "
        "normas en el cuerpo del texto: si el bloque trae una norma, "
        "menciónala una sola vez y entre paréntesis."),
    "abogado": (
        "Habla como a un colega. Nombra las normas del bloque y explica el "
        "razonamiento de procedencia --- en especial la subsidiariedad del "
        "art. 6.1 cuando aplique. Sin preámbulos empáticos."),
}

_PLANTILLA_BLOQUE = """BLOQUE DE TRIAJE (única fuente; no añadas nada)
derecho    : {derecho}
accionado  : {accionado}
mecanismo  : {mecanismo}
procede tutela: {procede}
razón      : {razon}
pretensión : {pretension}
normas citadas: {fundamento}
{pivote}"""


def _texto_pivote(pivota_en: list[str] | None) -> str:
    """Qué dato cambiaría el mecanismo, dicho en lenguaje llano.

    Sale de `reglas.estrato_verificacion`, que devuelve los campos en los que
    pivota la etiqueta. No se inventa: si la etiqueta no pivota en nada
    ponderable, no se dice nada.
    """
    if not pivota_en:
        return ""
    legible = {
        "perjuicio_irremediable":
            "que esperar al proceso ordinario hiciera inútil la protección "
            "(riesgo vital, enfermedad grave, edad avanzada sin ingresos)",
        "medio_eficaz":
            "que ese otro proceso no sirviera en concreto para esta persona, "
            "atendiendo su edad, salud y urgencia",
        "sujeto_especial_proteccion":
            "que fuera menor, adulto mayor, persona con discapacidad, mujer "
            "embarazada o persona en debilidad manifiesta",
        "titular_pide_lo_suyo":
            "que reclamara la afectación concreta de su propio derecho y no "
            "la del grupo",
    }
    cond = [legible[c] for c in pivota_en if c in legible]
    if not cond:
        return ""
    return ("condicion_que_cambiaria_el_mecanismo: " + "; o ".join(cond))


def construir_prompt(bloque: dict, pivota_en=None,
                     registro: str = "ciudadano") -> tuple[str, str]:
    """`(sistema, usuario)` para el generador. Separado para poder probarlo."""
    if registro not in REGISTROS:
        raise ValueError(f"registro desconocido: {registro!r}; "
                         f"usa uno de {REGISTROS}")
    sistema = _SISTEMA.format(registro=registro.upper(),
                              instruccion=_INSTRUCCION[registro])
    usuario = _PLANTILLA_BLOQUE.format(
        derecho=bloque.get("derecho") or "(no determinado)",
        accionado=bloque.get("accionado") or "(no determinado)",
        mecanismo=bloque.get("mecanismo") or "(ninguno: el caso no es de "
                                             "acción constitucional)",
        procede="sí" if bloque.get("procede") else "no",
        razon=bloque.get("razon") or "(sin razón registrada)",
        pretension=bloque.get("pretension") or "(sin pretensión registrada)",
        fundamento=bloque.get("fundamento") or "(ninguna)",
        pivote=_texto_pivote(pivota_en))
    return sistema, usuario


def citas_de(texto: str) -> set[str]:
    """Las normas que aparecen en un texto, con el mismo lector del harness."""
    return set(metricas.citas_en_texto(texto or ""))


def verificar_texto(texto: str, bloque: dict) -> dict:
    """¿El texto respeta el bloque? Es la guarda, no un adorno.

    Comprueba las tres cosas que pueden romperse al redactar:

      - que no haya introducido normas que el bloque no traía,
      - que el mecanismo siga estando dicho,
      - que la procedencia siga estando dicha.

    Las dos últimas no son cosmética: son lo que permite que un error del
    triaje --- 1 de cada 8 --- siga siendo detectable por quien lee.
    """
    del_bloque = citas_de(bloque.get("fundamento") or "")
    del_texto = citas_de(texto)
    intrusas = sorted(del_texto - del_bloque)

    mec = (bloque.get("mecanismo") or "").lower()
    nombre = {"tutela": "tutela", "accion_popular": "popular",
              "accion_cumplimiento": "cumplimiento",
              "habeas_corpus": "habeas corpus",
              "via_ordinaria": "ordinari"}.get(mec, mec)
    dice_mecanismo = bool(nombre) and nombre in (texto or "").lower()
    if not mec:
        dice_mecanismo = True          # sin mecanismo no hay nada que exigir

    t = (texto or "").lower()
    dice_procedencia = bool(re.search(
        r"\b(procede|no procede|s[íi] procede|cabe|no cabe|v[íi]a)\b", t))

    return {
        "citas_del_bloque": sorted(del_bloque),
        "citas_del_texto": sorted(del_texto),
        "citas_intrusas": intrusas,
        "dice_mecanismo": dice_mecanismo,
        "dice_procedencia": dice_procedencia,
        "valido": not intrusas and dice_mecanismo and dice_procedencia,
        "palabras": len((texto or "").split()),
    }


def redactar(generar, bloque: dict, pivota_en=None,
             registro: str = "ciudadano", estricto: bool = True) -> dict:
    """Texto en lenguaje natural a partir del bloque. `generar(sistema, usuario)`.

    Devuelve `{"texto", "verificacion", "registro"}`. Con `estricto=True`
    --- el default --- levanta `ValueError` si el texto introduce una norma
    que el bloque no traía: publicar prosa que inventa una ley sería perder de
    golpe la propiedad que el proyecto lleva toda su vida midiendo.
    """
    sistema, usuario = construir_prompt(bloque, pivota_en, registro)
    texto = (generar(sistema, usuario) or "").strip()
    v = verificar_texto(texto, bloque)
    if estricto and v["citas_intrusas"]:
        raise ValueError(
            "la redaccion introdujo normas que no estaban en el bloque: "
            + ", ".join(v["citas_intrusas"])
            + ". El texto solo puede reformular la decision, no ampliarla.")
    return {"texto": texto, "verificacion": v, "registro": registro}


def medir(resultados: list[dict]) -> dict:
    """Qué tan bien se comporta la capa sobre un lote. Para el artefacto.

    Una capa de presentación puede degradar sin que nadie lo note: se lee bien
    y dice otra cosa. Estas cuatro cifras son las que lo delatarían.
    """
    n = len(resultados)
    if not n:
        return {"n": 0, "concluyente": False,
                "motivo": "sin textos que medir"}
    v = [r["verificacion"] for r in resultados]
    con_intrusas = [r for r in resultados if r["verificacion"]["citas_intrusas"]]
    return {
        "n": n,
        "concluyente": True,
        "citas_intrusas_total": sum(len(x["citas_intrusas"]) for x in v),
        "textos_con_citas_intrusas": len(con_intrusas),
        "tasa_citas_intrusas": round(len(con_intrusas) / n, 4),
        "dicen_el_mecanismo": round(sum(x["dice_mecanismo"] for x in v) / n, 4),
        "dicen_la_procedencia": round(
            sum(x["dice_procedencia"] for x in v) / n, 4),
        "palabras_media": round(sum(x["palabras"] for x in v) / n, 1),
        "ejemplos_intrusas": sorted(
            {c for x in v for c in x["citas_intrusas"]})[:10],
        "lectura":
            "`tasa_citas_intrusas` tiene que ser 0: una norma en el texto que "
            "no estaba en el bloque es una invencion de la capa de "
            "presentacion, y destruiria la medicion de alucinacion normativa "
            "del resto del proyecto. `dicen_el_mecanismo` y "
            "`dicen_la_procedencia` tienen que ser 1.0: son lo que permite "
            "que un error del triaje --- 1 de cada 8 --- siga siendo "
            "detectable por quien lee el texto.",
    }
