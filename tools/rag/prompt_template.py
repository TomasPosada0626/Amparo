"""Augment: arma el prompt aumentado de 4 partes (S07).

Etapa 6 de 7 del pipeline RAG (S07). Online / consulta.

Las 4 partes:
    1. Instruccion         -- rol + reglas duras del producto (PRODUCT.md)
    2. Contexto con fuente -- chunks recuperados, cada uno con su cita visible
    3. Valvula de escape   -- que hacer si el contexto no alcanza
    4. Pregunta            -- la consulta del usuario, tal cual

La valvula de escape es la pieza central, no un adorno defensivo. El M2 midio
que el modelo fine-tuneado llega a 100% de cumplimiento de "no inventa citas"
sobre validacion, pero que en el eval set adversarial cede y cita cuando se le
presiona por un numero de articulo. Un RAG sin valvula de escape explicita no
arregla eso: le da contexto real al modelo y sigue dejandolo responder de
memoria cuando el contexto no alcanza -- o sea, esconde el problema mejor.
"""
from __future__ import annotations

from tools.rag.embed_store import SearchResult

# Primera parte: el SYSTEM_PROMPT real del dataset de M1 (data/dataset_legal.jsonl),
# textual, para no cambiar el rol con el que el modelo fue fine-tuneado -- mas las
# dos reglas que el RAG recien hace posibles (citar solo lo que esta en el
# contexto). Si se cambia el SYSTEM_PROMPT del dataset, hay que cambiarlo aqui.
SYSTEM_PROMPT_M1 = (
    "Eres un asistente jurídico que responde consultas de derecho colombiano a personas sin "
    "formación jurídica. Responde de forma breve y en lenguaje claro y cotidiano. Señala el "
    "mecanismo legal aplicable (tutela, derecho de petición, habeas data, conciliación, "
    "restitución de inmueble, etc.) y qué evidencia debe reunir la persona. Sé prudente: no "
    "inventes normas ni cites artículos o plazos que no puedas verificar; si no estás seguro, "
    "dilo explícitamente. Si hay riesgo para la integridad o la salud de alguien, lo primero "
    "es orientar a la ayuda inmediata."
)

INSTRUCCION = f"""\
{SYSTEM_PROMPT_M1}

Ahora cuentas con un CONTEXTO de fuentes normativas verificadas. Reglas para \
usarlo:
- Cita unicamente normas que aparezcan en el CONTEXTO, y citalas exactamente \
como figuran ahi (ley y articulo). Nunca cites de memoria.
- Si el CONTEXTO respalda tu respuesta, indica de que norma y articulo sale.
- Usa lenguaje comprensible para alguien sin formacion juridica."""

# Texto exacto que debe aparecer cuando no hay contexto suficiente. Es una
# constante (y no prosa dentro del prompt) para que el harness de evaluacion
# pueda comprobar de forma programatica que la valvula de escape se activo, en
# vez de tener que juzgarlo a ojo.
RESPUESTA_SIN_CONTEXTO = (
    "No tengo informacion verificada sobre esto en mi base de conocimiento"
)

VALVULA_DE_ESCAPE = f"""\
Si el CONTEXTO no contiene informacion suficiente para responder con \
fundamento, responde exactamente con esta frase y nada mas: \
"{RESPUESTA_SIN_CONTEXTO}." Puedes sugerir a quien pregunta donde consultar, \
pero no completes la respuesta con lo que creas que podria ser correcto: es \
preferible reconocer la falta de informacion que arriesgar una afirmacion \
legal sin fuente verificable."""

# Respuesta que devuelve el CODIGO (sin llamar al modelo) cuando no hay contexto
# o cuando la respuesta insiste en citar lo que no vio. Hallazgo de la corrida de
# S08 (2026-09-27): la valvula de escape escrita en el prompt no se activo ni una
# vez en 168 respuestas -- el modelo respondia de memoria aun sin contexto. La
# frase va primero (el harness la detecta) y despues una orientacion fija, sin
# normas: donde consultar y, si hay riesgo, la linea de emergencia.
RESPUESTA_ESCAPE_POR_CODIGO = (
    f"{RESPUESTA_SIN_CONTEXTO}. Te sugiero consultar un consultorio juridico "
    "universitario, la Personeria o la Defensoria del Pueblo. Si tu seguridad esta "
    "en riesgo, llama a la Linea 123."
)

# Bloque de servicio (paso 4 del plan de M3, docs/m3_protocolo_aceptacion.md).
# NO esta en el prompt de entrenamiento: se agrega AL FINAL del system prompt
# con que se entreno, que queda intacto delante, para que el modelo siga viendo
# el rol y las reglas que aprendio. Ataca los fallos que el juez del RAG vio con
# el articulo correcto en el contexto (2026-10-14): apoyarse en el fragmento
# equivocado (9002, 9032, 9034), omitir ante quien acudir (9054, 9059, 9066) y
# negarse teniendo de donde responder (3 casos). Afina la valvula de escape sin
# contradecirla: la frase sigue siendo para cuando ningun fragmento sirve.
# Tomas decidio el 2026-10-13 que abstenerse no es requisito.
INSTRUCCIONES_DE_SERVICIO = """\
Indicaciones para que la respuesta le sirva a quien pregunta:
- Primero identifica cual de los fragmentos del CONTEXTO responde la pregunta y \
apoya tu respuesta en ese. Si citas un articulo, que sea el que responde, no el \
primero que aparezca.
- Di que puede hacer la persona: el mecanismo, ante quien acudir y que pruebas \
reunir. No te quedes solo en citar la norma.
- La frase de falta de informacion es solo para cuando ningun fragmento tiene \
relacion con la pregunta. Si algun fragmento responde aunque sea una parte, \
responde esa parte y di que falta."""

# Version 2 (2026-10-14). La 1 (arriba) se midio en la corrida final del paso 7 y
# no se adopto: casi duplico las abstenciones (8 -> 15 en A). Causa probable: su
# tercera linea nombra la frase de falta de informacion, y nombrarla la vuelve mas
# probable. La 2 no la menciona (la valvula de escape del prompt de entrenamiento
# sigue intacta delante) y pide lo que el juez del RAG vio faltar con el articulo
# correcto en el contexto: responder la pregunta concreta y lo esencial del caso
# (la proteccion, el plazo o la excepcion que la decide, y ante quien acudir).
INSTRUCCIONES_DE_SERVICIO_V2 = """\
Indicaciones para que la respuesta le sirva a quien pregunta:
- Empieza respondiendo la pregunta concreta, apoyandote en el fragmento del \
CONTEXTO que la responde.
- Incluye lo esencial para que la persona pueda actuar: la proteccion, el plazo o \
la condicion que decide su caso, que puede hacer, ante que entidad o autoridad y \
que pruebas reunir.
- Si hay una excepcion o un requisito previo importante, mencionalo en una frase."""

VERSIONES_DE_SERVICIO = {"v1": INSTRUCCIONES_DE_SERVICIO, "v2": INSTRUCCIONES_DE_SERVICIO_V2}

SIN_CONTEXTO_RELEVANTE = (
    "(No se encontro contexto relevante en la base de conocimiento.)"
)


def format_context(results: list[SearchResult]) -> str:
    """Formatea los chunks recuperados con su cita visible.

    La cita va ANTES del texto, y esto no es cosmetico: es lo que permite que el
    modelo, al citar, cite algo que efectivamente esta en el contexto. Un bloque
    de texto anonimo no le da de donde derivar una cita verificable, y el modelo
    la completa de memoria -- el fallo exacto que el M2 documento.
    """
    if not results:
        return SIN_CONTEXTO_RELEVANTE

    bloques = []
    for i, r in enumerate(results, start=1):
        encabezado = f"[{i}] Fuente: {r.cita}"
        if r.capitulo:
            encabezado += f" ({r.capitulo})"
        bloques.append(f"{encabezado}\n{r.text}")
    return "\n\n---\n\n".join(bloques)


def build_augmented_prompt(query: str, retrieved: list[SearchResult]) -> str:
    """Las 4 partes en orden, como un solo bloque (formato de S07)."""
    return f"""{INSTRUCCION}

CONTEXTO:
{format_context(retrieved)}

{VALVULA_DE_ESCAPE}

PREGUNTA DEL USUARIO:
{query}"""


def build_messages(query: str, retrieved: list[SearchResult], servicio: bool | str = False) -> list[dict]:
    """Las mismas 4 partes, separadas en roles system/user.

    Es el formato que consume apply_chat_template, y mantiene la comparabilidad
    con M1/M2: ahi el rol y las reglas iban siempre en el mensaje system y la
    consulta en el user. Las partes 1 y 3 (instruccion y valvula de escape) son
    reglas -> system; las partes 2 y 4 (contexto y pregunta) son el caso
    concreto -> user.

    servicio agrega un bloque de servicio al final del system prompt: True o "v1"
    (INSTRUCCIONES_DE_SERVICIO), "v2" (INSTRUCCIONES_DE_SERVICIO_V2). Por defecto
    False: es lo que construye el dataset de entrenamiento (dataset_v3,
    escenarios) y no debe cambiar sin reentrenar.
    """
    system = f"{INSTRUCCION}\n\n{VALVULA_DE_ESCAPE}"
    if servicio:
        bloque = VERSIONES_DE_SERVICIO["v1" if servicio is True else servicio]
        system = f"{system}\n\n{bloque}"
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"CONTEXTO:\n{format_context(retrieved)}\n\n"
                f"PREGUNTA DEL USUARIO:\n{query}"
            ),
        },
    ]


if __name__ == "__main__":
    ejemplo = [
        SearchResult(
            chunk_id="ley_1755_2015::chunk3",
            text="ARTÍCULO 14. Terminos para resolver las distintas modalidades de peticiones...",
            fuente="Ley 1755 de 2015 (Derecho de peticion)",
            url_fuente="https://www.funcionpublica.gov.co/eva/gestornormativo/...",
            articulos_incluidos=["14"],
            score=0.87,
        )
    ]
    print(build_augmented_prompt("¿Cuanto tiempo tienen para responderme?", ejemplo))
    print("\n\n--- sin contexto (valvula de escape) ---\n")
    print(build_augmented_prompt("¿Que dice la ley de patentes mineras?", []))
