"""¿La respuesta termino, o se le acabo el presupuesto de generacion?

Por que no basta con contar tokens. `n_generados >= max_new_tokens` marca como
cortada una respuesta que acaba justo en el tope, y al reves: el numero no dice
si el modelo pudo cerrar el turno. La senal fiable es si el ultimo token
generado es uno de fin de secuencia.

Y hay una trampa concreta con Qwen. En sus modelos chat el token que cierra el
turno es `<|im_end|>`, que **no siempre** es `tokenizer.eos_token_id`: ese puede
ser `<|endoftext|>`, que el modelo instruido casi nunca emite. Mirar solo
`eos_token_id` daria casi todas las respuestas como cortadas.

Esto vive aqui y no dentro del notebook para poder probarlo. En M1 v1 la
deteccion de truncamiento no existia, y al cerrar el modulo hubo que descartarlo
acotandolo por longitud de palabras en vez de medirlo.
"""
from __future__ import annotations

from typing import Iterable, Sequence

# Los tokens con que los modelos chat cierran el turno, por nombre. Se buscan
# por nombre porque su id cambia entre familias de modelos.
NOMBRES_DE_FIN = ("<|im_end|>", "<|endoftext|>", "<|eot_id|>", "</s>")


def ids_de_fin(tokenizer, model=None) -> set[int]:
    """Los ids que cuentan como fin de secuencia.

    Se juntan los tres sitios donde pueden estar, porque ninguno alcanza solo:

      - `tokenizer.eos_token_id`: en Qwen2.5-Instruct suele ser `<|endoftext|>`,
        que el modelo instruido casi no usa;
      - `model.generation_config.eos_token_id`: aqui si aparece `<|im_end|>`, y
        puede venir como lista;
      - los nombres de NOMBRES_DE_FIN, para cuando la configuracion no los trae.

    Devolver un conjunto vacio seria peor que fallar: todas las respuestas
    quedarian marcadas como cortadas y la metrica mentiria en silencio. Quien
    llama debe comprobarlo.
    """
    ids: set[int] = set()

    eos = getattr(tokenizer, "eos_token_id", None)
    for v in _como_lista(eos):
        ids.add(int(v))

    cfg = getattr(getattr(model, "generation_config", None), "eos_token_id", None)
    for v in _como_lista(cfg):
        ids.add(int(v))

    convertir = getattr(tokenizer, "convert_tokens_to_ids", None)
    if callable(convertir):
        for nombre in NOMBRES_DE_FIN:
            try:
                i = convertir(nombre)
            except Exception:
                continue
            # Un token que el tokenizer no conoce devuelve el id de <unk> o un
            # negativo segun la implementacion; ninguno de los dos es fin.
            if isinstance(i, int) and i >= 0 and i != getattr(tokenizer, "unk_token_id", None):
                ids.add(i)

    return ids


def _como_lista(v) -> list:
    if v is None:
        return []
    if isinstance(v, (list, tuple, set)):
        return [x for x in v if x is not None]
    return [v]


def se_corto(tokens_generados: Sequence[int], ids_fin: Iterable[int]) -> bool:
    """¿Se corto la respuesta?

    `tokens_generados` son SOLO los tokens nuevos, no el prompt concatenado con
    ellos: si se le pasa la secuencia completa, el ultimo token sigue siendo el
    correcto, pero una respuesta vacia (0 tokens nuevos) se leeria como el
    ultimo token del prompt y pasaria por terminada.

    Una respuesta vacia se cuenta como cortada: el modelo no produjo nada y
    desde luego no cerro el turno.
    """
    fin = set(ids_fin)
    if not fin:
        raise ValueError(
            "sin tokens de fin no se puede saber si una respuesta se corto; "
            "revisar ids_de_fin(tokenizer, model)")
    if len(tokens_generados) == 0:
        return True
    return int(tokens_generados[-1]) not in fin


# Por que paro la generacion. `se_corto` responde si/no, que es lo que necesita
# la metrica, pero no basta para arreglar nada: una salida vacia y una que
# agoto el presupuesto se arreglan distinto -- la primera es un fallo de
# generacion y la segunda un techo mal puesto -- y las dos dan "cortada".
TERMINO = "termino"
SIN_SALIDA = "sin_salida"
PRESUPUESTO_AGOTADO = "presupuesto_agotado"
PARO_SIN_CERRAR = "paro_sin_cerrar"


def motivo(tokens_generados: Sequence[int], ids_fin: Iterable[int],
           max_new_tokens: int | None = None) -> str:
    """Por que termino la generacion, cuando se puede determinar.

      TERMINO               el ultimo token es de fin: la respuesta esta completa.
      SIN_SALIDA            cero tokens nuevos. No es truncamiento: el modelo no
                            produjo nada, y la causa esta en otra parte.
      PRESUPUESTO_AGOTADO   se llego a max_new_tokens sin cerrar el turno.
      PARO_SIN_CERRAR       no cerro y tampoco agoto el presupuesto, asi que
                            paro por otra razon (un stop, un error del backend).
                            Tambien es lo que se devuelve cuando no se sabe
                            cuanto era el presupuesto.
    """
    fin = set(ids_fin)
    if not fin:
        raise ValueError(
            "sin tokens de fin no se puede saber por que paro la generacion; "
            "revisar ids_de_fin(tokenizer, model)")
    if len(tokens_generados) == 0:
        return SIN_SALIDA
    if int(tokens_generados[-1]) in fin:
        return TERMINO
    if max_new_tokens is not None and len(tokens_generados) >= max_new_tokens:
        return PRESUPUESTO_AGOTADO
    return PARO_SIN_CERRAR


def resumen(registros: Sequence[dict]) -> dict:
    """Cuantas se cortaron y cuantas agotaron el presupuesto, con su denominador.

    Las dos cifras no son la misma. Coinciden casi siempre, y cuando no, la
    diferencia informa: cortada sin agotar el presupuesto significa que la
    generacion paro por otra razon (un stop, un error), y agotada sin cortarse
    es una respuesta que cerro justo en el tope.
    """
    total = len(registros)
    cortadas = [r for r in registros if r.get("cortada")]
    agotadas = [r for r in registros if r.get("presupuesto_agotado")]
    return {
        "n": total,
        "cortadas": len(cortadas),
        "presupuesto_agotado": len(agotadas),
        "cortadas_sin_agotar": len([r for r in cortadas if not r.get("presupuesto_agotado")]),
        "agotadas_sin_cortarse": len([r for r in agotadas if not r.get("cortada")]),
        "ids_cortadas": [r.get("id") for r in cortadas][:20],
        # Por que paro cada una, cuando el registro lo trae. Una salida vacia y
        # una que agoto el presupuesto cuentan las dos como cortadas y se
        # arreglan distinto.
        "por_motivo": {
            m: sum(1 for r in registros if r.get("motivo") == m)
            for m in (TERMINO, SIN_SALIDA, PRESUPUESTO_AGOTADO, PARO_SIN_CERRAR)
            if any(r.get("motivo") == m for r in registros)
        },
    }
