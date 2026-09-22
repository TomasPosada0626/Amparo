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
    "Eres un asistente juridico que responde consultas de derecho colombiano. "
    "Responde de forma breve, fundamentada y prudente. No inventes normas ni "
    "cites fuentes que no existan; si no estas seguro, dilo explicitamente."
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


def build_messages(query: str, retrieved: list[SearchResult]) -> list[dict]:
    """Las mismas 4 partes, separadas en roles system/user.

    Es el formato que consume apply_chat_template, y mantiene la comparabilidad
    con M1/M2: ahi el rol y las reglas iban siempre en el mensaje system y la
    consulta en el user. Las partes 1 y 3 (instruccion y valvula de escape) son
    reglas -> system; las partes 2 y 4 (contexto y pregunta) son el caso
    concreto -> user.
    """
    return [
        {"role": "system", "content": f"{INSTRUCCION}\n\n{VALVULA_DE_ESCAPE}"},
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
