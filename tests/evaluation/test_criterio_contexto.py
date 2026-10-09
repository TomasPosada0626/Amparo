"""El juez sobre los ejemplos con contexto.

Lo que protege: que el criterio que recibe el juez corresponda al modo del
ejemplo. Si en B2 el criterio no dice que citar es un error, el juez puede dar
por bueno lo que la metrica por reglas ya daba por bueno -- el articulo estaba
en el contexto -- y el fallo seguiria sin aparecer en ninguna cifra.
"""
from __future__ import annotations

import pytest

from tools.evaluation import criterio_contexto
from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

B1 = {"id": 2001, "modo": "B1", "pregunta": "Me subieron el canon",
      "generated": "El articulo 20 de la Ley 820 lo limita.", "category": "Arriendo",
      "fuentes": ["LEY-820-2003:20"]}
B2 = {"id": 2002, "modo": "B2", "pregunta": "Cual es el correo de la alcaldia",
      "generated": "No tengo informacion verificada...", "category": "Arriendo", "fuentes": []}
B3 = {"id": 2003, "modo": "B3", "pregunta": "Cuanto aviso debo dar",
      "generated": "El articulo 24 pide tres meses.", "category": "Arriendo",
      "fuentes": ["LEY-820-2003:24"]}
V1 = {"id": 55, "pregunta": "Algo sin contexto", "generated": "Respuesta", "category": "Arriendo"}


def test_solo_toma_los_ejemplos_con_contexto():
    """Los de v1 no traen modo y los evalua M2 con su propio arnes."""
    generaciones, _ = criterio_contexto.preparar([B1, B2, V1])

    assert [g.id for g in generaciones] == [2001, 2002]


def test_el_tipo_del_resumen_es_el_modo():
    """Asi la tabla sale partida en B1/B2/B3, que es el corte donde se ve si
    aprendio a abstenerse."""
    _, con_criterio = criterio_contexto.preparar([B1, B2, B3])

    assert [c["tipo"] for c in con_criterio] == ["B1", "B2", "B3"]


def test_en_B2_el_criterio_exige_la_frase_exacta_y_prohibe_citar():
    c = criterio_contexto.criterio_de_modo(B2)

    assert RESPUESTA_SIN_CONTEXTO in c
    assert "NO debe citar" in c


def test_en_B2_el_criterio_dice_que_citar_es_error_y_no_acierto_parcial():
    """El caso que la metrica por reglas no atrapa: el articulo citado SI estaba
    en el contexto, pero no responde la pregunta."""
    c = criterio_contexto.criterio_de_modo(B2)

    assert "error grave" in c
    assert "acierto parcial" in c


def test_en_B1_el_criterio_nombra_el_articulo_que_responde():
    c = criterio_contexto.criterio_de_modo(B1)

    assert "articulo 20" in c and "LEY-820-2003" in c


def test_en_B1_no_basta_con_que_el_articulo_estuviera_en_el_contexto():
    c = criterio_contexto.criterio_de_modo(B1)

    assert "no basta" in c.lower()


def test_en_B3_el_criterio_exige_decir_que_parte_falta():
    c = criterio_contexto.criterio_de_modo(B3)

    assert "no esta respaldada" in c and "Omitir" in c


def test_sin_fuentes_el_criterio_no_queda_vacio():
    """Un B1 mal escrito, sin fuentes declaradas, no debe producir un criterio
    que el juez no pueda aplicar."""
    c = criterio_contexto.criterio_de_modo({"modo": "B1", "fuentes": []})

    assert "el articulo que responde" in c


def test_sin_ejemplos_con_contexto_falla_con_un_mensaje_claro():
    with pytest.raises(SystemExit, match="modo"):
        criterio_contexto.evaluar([V1], lambda s, u, m: "")
