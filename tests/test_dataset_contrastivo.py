"""Pares contrastivos para que la abstencion dependa del contexto y no de la pregunta.

Lo que protege. El 2026-10-09 el modelo se abstuvo en 0 de 35 casos B2 con 228
ejemplos B2 en entrenamiento. La causa no era falta de ejemplos: de las 601
preguntas base con contexto, solo UNA aparecia en mas de un modo, asi que el
modo era predecible desde la pregunta y el modelo podia memorizarlo en vez de
leer el contexto.

Estas pruebas cuidan las dos cosas que hacen que la correccion sirva: que la
variante use la MISMA pregunta (si no, no hay contraste) y que su contexto NO
traiga el articulo que responde (si lo trae, el ejemplo ensena a abstenerse
teniendo la respuesta delante, que es peor que no tener el ejemplo).
"""
from __future__ import annotations

from tools.dataset_contrastivo import candidatas, respuesta_de_escape, revisar
from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO


def registro(id_, modo, split="train", base_id=None, fuentes=(), categoria="Arriendo"):
    return {"id": id_, "modo": modo, "split": split, "base_id": base_id,
            "category": categoria, "pregunta": f"pregunta {base_id or id_}",
            "fuentes": list(fuentes),
            "messages": [{"role": "assistant", "content": "respuesta"}]}


def variante(id_, par_de, base_id=None, contexto=(), split="train",
             target=None, categoria="Arriendo", fuentes_originales=()):
    return {"id": id_, "modo": "B2", "split": split, "base_id": base_id,
            "category": categoria, "pregunta": f"pregunta {base_id or par_de}",
            "fuentes": [], "par_de": par_de,
            "fuentes_originales": list(fuentes_originales),
            "contexto": list(contexto) or [{"doc_id": "otra_ley", "articulos": ["99"]}],
            "messages": [{"role": "assistant",
                          "content": target or respuesta_de_escape(categoria)}]}


# --- a que ejemplos les toca variante ----------------------------------------

def test_solo_se_generan_variantes_de_B1_y_B3():
    """Los B2 ya ensenan a abstenerse: duplicarlos no agrega contraste."""
    registros = [registro(1, "B1"), registro(2, "B2"), registro(3, "B3")]

    assert [r["id"] for r in candidatas(registros)] == [1, 3]


def test_no_se_toca_validacion():
    """Generar sobre val seria entrenar sobre la medicion."""
    registros = [registro(1, "B1", split="val"), registro(2, "B1")]

    assert [r["id"] for r in candidatas(registros)] == [2]


def test_no_se_genera_si_la_pregunta_base_esta_en_validacion():
    """Meteria esa pregunta en entrenamiento por la puerta de atras."""
    registros = [registro(10, "B1", base_id=500),
                 registro(11, "B1", base_id=501),
                 registro(99, "B2", split="val", base_id=500)]

    assert [r["id"] for r in candidatas(registros)] == [11]


def test_los_ejemplos_sin_contexto_no_entran():
    """v1 no tiene modo: son los 1305 de dataset_legal, sin contexto."""
    registros = [{"id": 1, "split": "train", "modo": None, "category": "Arriendo"}]

    assert candidatas(registros) == []


# --- el target ---------------------------------------------------------------

def test_el_target_empieza_con_la_frase_exacta():
    """`es_valvula_de_escape` y el juez la buscan tal cual; si cambia el prefijo,
    la abstencion deja de contarse."""
    assert respuesta_de_escape("Salud / EPS").startswith(RESPUESTA_SIN_CONTEXTO)


def test_el_puntero_depende_de_la_categoria():
    assert "Ministerio del Trabajo" in respuesta_de_escape("Despido")
    assert "Supersalud" in respuesta_de_escape("Salud / EPS")


def test_una_categoria_desconocida_no_queda_sin_puntero():
    salida = respuesta_de_escape("Categoria que no existe")

    assert salida.startswith(RESPUESTA_SIN_CONTEXTO)
    assert "consultorio juridico" in salida


# --- lo que revisar() tiene que atrapar --------------------------------------

def test_una_variante_bien_formada_no_da_problemas():
    registros = [registro(1, "B1", base_id=500, fuentes=["LEY-820-2003:20"])]
    v = [variante(6001, par_de=1, base_id=500)]

    assert revisar(v, registros) == []


def test_atrapa_el_articulo_que_responde_dentro_del_contexto():
    """El fallo que arruinaria el ejemplo: ensenar a abstenerse con la respuesta
    delante."""
    registros = [registro(1, "B1", base_id=500, fuentes=["LEY-820-2003:20"])]
    v = [variante(6001, par_de=1, base_id=500,
                  fuentes_originales=["arrendamiento_ley_820_2003:20"],
                  contexto=[{"doc_id": "arrendamiento_ley_820_2003", "articulos": ["20"]}])]

    problemas = revisar(v, registros)

    assert problemas and "el articulo que responde" in problemas[0]


def test_el_mismo_numero_de_otra_ley_no_es_conflicto():
    """El falso positivo que paro la primera generacion: el articulo 18 de otra
    ley no es el articulo 18 de la Ley 820. Comparar numeros sueltos marcaba 5
    variantes buenas."""
    registros = [registro(1, "B1", base_id=500, fuentes=["LEY-820-2003:18"])]
    v = [variante(6001, par_de=1, base_id=500,
                  fuentes_originales=["arrendamiento_ley_820_2003:18"],
                  contexto=[{"doc_id": "codigo_general_proceso_ley_1564_2012",
                             "articulos": ["18"]}])]

    assert revisar(v, registros) == []


def test_atrapa_un_id_que_ya_existe():
    registros = [registro(6001, "B1")]
    v = [variante(6001, par_de=6001)]

    assert any("ya existen" in p for p in revisar(v, registros))


def test_atrapa_ids_repetidos_entre_las_variantes():
    registros = [registro(1, "B1"), registro(2, "B1")]
    v = [variante(6001, par_de=1), variante(6001, par_de=2)]

    assert any("repetidos" in p for p in revisar(v, registros))


def test_atrapa_una_variante_que_no_es_de_train():
    registros = [registro(1, "B1")]
    v = [variante(6001, par_de=1, split="val")]

    assert any("no son de train" in p for p in revisar(v, registros))


def test_atrapa_una_variante_sin_su_ejemplo_original():
    """Sin el original no hay par, y sin par no hay contraste."""
    registros = [registro(1, "B1")]
    v = [variante(6001, par_de=999)]

    assert any("sin el ejemplo original" in p for p in revisar(v, registros))


def test_atrapa_una_variante_sin_contexto():
    registros = [registro(1, "B1")]
    v = [variante(6001, par_de=1)]
    v[0]["contexto"] = []

    assert any("sin contexto" in p for p in revisar(v, registros))


def test_atrapa_un_target_que_no_empieza_con_la_frase():
    registros = [registro(1, "B1")]
    v = [variante(6001, par_de=1, target="Puedes presentar una tutela.")]

    assert any("no empieza con la frase" in p for p in revisar(v, registros))


def test_atrapa_una_variante_de_una_pregunta_que_esta_en_validacion():
    registros = [registro(1, "B1", base_id=500),
                 registro(99, "B2", split="val", base_id=500)]
    v = [variante(6001, par_de=1, base_id=500)]

    assert any("esta en validacion" in p for p in revisar(v, registros))
