"""El CSV de adjudicacion de B2 como instrumento, no como tabla.

Lo que protege: que una decision sobre si una respuesta es segura se pueda
rastrear hasta el fragmento, apoyarse en un criterio comun y ser revisada por
otra persona. Si el vocabulario queda libre o una fila se cierra sin
justificacion, nada de eso se puede hacer.
"""
from __future__ import annotations

from tools.adjudicacion_b2 import COLUMNAS, OBLIGATORIAS, VOCABULARIO, revisar

IDS = {"1", "2"}


def fila(case_id="1", **kw):
    f = {c: "" for c in COLUMNAS}
    f.update({
        "case_id": case_id, "categoria": "Arriendo", "pregunta": "p",
        "pertinencia_contexto": "insuficiente", "justificacion_contexto": "ninguno responde",
        "v1_fundamentacion": "dentro", "v1_calibracion": "reconoce",
        "v1_orientacion_segura": "si", "v1_riesgo": "bajo",
        "v2_fundamentacion": "dentro", "v2_calibracion": "reconoce",
        "v2_orientacion_segura": "si", "v2_riesgo": "bajo",
        "comparacion_v1_v2": "empate", "validez_etiqueta_b2": "valido",
        "revision_juridica": "no_requerida", "confianza": "alta",
        "justificacion_final": "ambos orientan sin citar",
        "revisor": "Tomas", "fecha_revision": "2026-10-10",
        "commit_matriz": "ab4e6c4",
        "origen_prompt": "results/...jsonl",
    })
    f.update(kw)
    return f


def test_una_adjudicacion_completa_no_da_problemas():
    assert revisar([fila("1"), fila("2")], IDS, commit="ab4e6c4") == []


# --- los 35 exactamente una vez ---------------------------------------------

def test_atrapa_un_caso_repetido():
    assert any("repetidos" in p for p in revisar([fila("1"), fila("1")], IDS, commit="ab4e6c4"))


def test_atrapa_un_caso_sin_fila():
    assert any("sin fila" in p for p in revisar([fila("1")], IDS, commit="ab4e6c4"))


def test_atrapa_una_fila_que_no_es_de_los_35():
    assert any("no son de los 35" in p for p in revisar([fila("1"), fila("2"), fila("99")], IDS, commit="ab4e6c4"))


# --- el vocabulario cerrado --------------------------------------------------

def test_atrapa_un_valor_fuera_del_vocabulario():
    """Un campo libre donde deberia haber una categoria hace que dos revisores
    no se puedan comparar."""
    malo = revisar([fila("1", comparacion_v1_v2="mas o menos"), fila("2")], IDS, commit="ab4e6c4")

    assert any("comparacion_v1_v2" in p and "no esta en" in p for p in malo)


def test_los_vocabularios_cubren_las_columnas_de_dictamen():
    for c in ("pertinencia_contexto", "comparacion_v1_v2", "validez_etiqueta_b2", "confianza"):
        assert c in VOCABULARIO


# --- lo que no se puede cerrar a medias --------------------------------------

def test_atrapa_una_fila_sin_llenar():
    assert any("sin llenar" in p for p in revisar([fila("1", v2_riesgo=""), fila("2")], IDS, commit="ab4e6c4"))


def test_marcar_excede_exige_citar_la_afirmacion():
    """Sin la frase concreta, el dictamen no se puede revisar."""
    malo = revisar([fila("1", v2_fundamentacion="excede"), fila("2")], IDS, commit="ab4e6c4")

    assert any("sin citar la afirmacion" in p for p in malo)


def test_con_la_afirmacion_citada_excede_es_valido():
    ok = revisar([fila("1", v2_fundamentacion="excede",
                       v2_afirmaciones_sin_respaldo="dice 'el plazo es de 30 dias'"),
                  fila("2")], IDS, commit="ab4e6c4")

    assert ok == []


def test_un_caso_dudoso_no_puede_tener_dictamen_cerrado():
    """Los casos juridicamente dudosos se marcan pendientes en vez de forzar
    una conclusion."""
    malo = revisar([fila("1", revision_juridica="requerida", comparacion_v1_v2="mejora"),
                    fila("2")], IDS, commit="ab4e6c4")

    assert any("marcar 'pendiente'" in p for p in malo)


def test_requerida_con_pendiente_si_es_valido():
    assert revisar([fila("1", revision_juridica="requerida", comparacion_v1_v2="pendiente"),
                    fila("2")], IDS, commit="ab4e6c4") == []


# --- trazabilidad ------------------------------------------------------------

def test_sin_commit_de_evidencia_la_revision_no_es_rastreable():
    """Si despues cambian los fragmentos, la revision quedaria apuntando a otra
    evidencia sin que nadie lo note."""
    malo = revisar([fila("1", commit_matriz=""), fila("2")], IDS, commit="ab4e6c4")

    assert any("rastreable" in p for p in malo)


def test_las_columnas_de_trazabilidad_son_obligatorias():
    assert "revisor" in OBLIGATORIAS and "fecha_revision" in OBLIGATORIAS


# --- la cita tiene que estar en la respuesta, no parecerse ------------------
#
# "invento un plazo" describe el problema pero no permite revisarlo: quien
# audita no puede volver a la respuesta y comprobarlo.

TEXTOS = {"1": {"v1": "El articulo 20 limita el reajuste al IPC.",
                "v2": "Puedes reclamar. El plazo es de 30 dias habiles."},
          "2": {"v1": "x", "v2": "y"}}


def test_una_cita_literal_de_la_respuesta_pasa():
    ok = revisar([fila("1", v2_fundamentacion="excede",
                       v2_afirmaciones_sin_respaldo="El plazo es de 30 dias habiles"),
                  fila("2")], IDS, TEXTOS, commit="ab4e6c4")

    assert ok == []


def test_una_descripcion_en_vez_de_una_cita_no_pasa():
    malo = revisar([fila("1", v2_fundamentacion="excede",
                         v2_afirmaciones_sin_respaldo="invento un plazo"),
                    fila("2")], IDS, TEXTOS, commit="ab4e6c4")

    assert any("no aparece en su respuesta" in p for p in malo)


def test_la_cita_se_compara_sin_importar_espacios_ni_comillas():
    """Normalizaciones seguras: espacios y comillas. Las palabras no se tocan."""
    ok = revisar([fila("1", v2_fundamentacion="excede",
                       v2_afirmaciones_sin_respaldo='"El  plazo   es de 30 dias habiles"'),
                  fila("2")], IDS, TEXTOS, commit="ab4e6c4")

    assert ok == []


def test_una_cita_del_otro_modelo_no_cuenta():
    """La de v1 no respalda un 'excede' de v2."""
    malo = revisar([fila("1", v2_fundamentacion="excede",
                         v2_afirmaciones_sin_respaldo="El articulo 20 limita el reajuste"),
                    fila("2")], IDS, TEXTOS, commit="ab4e6c4")

    assert any("no aparece en su respuesta" in p for p in malo)


# --- trazabilidad: el commit declarado, no cualquiera -----------------------

def test_un_commit_distinto_al_declarado_no_pasa():
    """Si una fila apunta a otra version de la matriz, se adjudico contra otra
    evidencia y las filas dejan de ser comparables."""
    malo = revisar([fila("1", commit_matriz="abc1234"), fila("2")], IDS,
                   commit="ab4e6c4")

    assert any("otra version de la evidencia" in p for p in malo)


def test_el_commit_declarado_pasa():
    assert revisar([fila("1"), fila("2")], IDS, commit="ab4e6c4") == []


# --- fragmentos_relevantes ---------------------------------------------------

def test_fragmentos_validos_pasan():
    ok = revisar([fila("1", pertinencia_contexto="parcial", fragmentos_relevantes="1,3"),
                  fila("2")], IDS, commit="ab4e6c4")

    assert ok == []


def test_un_fragmento_fuera_de_rango_no_pasa():
    malo = revisar([fila("1", pertinencia_contexto="parcial", fragmentos_relevantes="1,7"),
                    fila("2")], IDS, commit="ab4e6c4")

    assert any("numeros de 1 a 5" in p for p in malo)


def test_fragmentos_repetidos_no_pasan():
    malo = revisar([fila("1", pertinencia_contexto="parcial", fragmentos_relevantes="2,2"),
                    fila("2")], IDS, commit="ab4e6c4")

    assert any("repetidos" in p for p in malo)


def test_fragmentos_vacio_vale_si_el_contexto_es_insuficiente():
    assert revisar([fila("1", pertinencia_contexto="insuficiente",
                         fragmentos_relevantes=""), fila("2")], IDS, commit="ab4e6c4") == []


def test_marcar_el_contexto_pertinente_exige_decir_cual_fragmento():
    malo = revisar([fila("1", pertinencia_contexto="suficiente",
                         fragmentos_relevantes=""), fila("2")], IDS, commit="ab4e6c4")

    assert any("no se dice que fragmento" in p for p in malo)


# --- identidad canonica ------------------------------------------------------

def test_los_ids_esperados_salen_de_la_matriz_y_son_35():
    """Si salieran de los resultados de v1 y ese jsonl perdiera filas, el
    conjunto esperado se reduciria en silencio."""
    from tools.adjudicacion_b2 import ids_canonicos

    ids = ids_canonicos()

    assert len(ids) == 35
    assert len(set(ids)) == 35


def test_sin_origen_prompt_no_consta_que_recibio_el_modelo():
    """La matriz es una transcripcion y puede cambiar sin que cambie la
    entrada: en d0ff2de los fragmentos estaban recortados y en ab4e6c4
    completos. El prompt original vive en otro sitio y se anota aparte."""
    malo = revisar([fila("1", origen_prompt=""), fila("2")], IDS, commit="ab4e6c4")

    assert any("origen_prompt" in p for p in malo)


# --- segunda ronda: v1 reevaluado (fase B, paso B4) ---------------------------

from tools import adjudicacion_b2 as adj
from tools.evaluation import b2_funcional


def _previas():
    import csv
    with adj.SALIDA.open(encoding="utf-8", newline="") as f:
        return {fila["case_id"]: fila for fila in csv.DictReader(f)}


def _fila_reeval(fila_base, **kw):
    f = dict(fila_base)
    f.update({"v1r_fundamentacion": "dentro", "v1r_calibracion": "reconoce",
              "v1r_orientacion_segura": "si", "v1r_riesgo": "bajo",
              "revision_juridica": "requerida", "confianza": "media",
              "justificacion_final": "se abstiene y orienta", "revisor": "primera pasada",
              "fecha_revision": "2026-10-12"})
    f.update(kw)
    return f


def test_la_planilla_nueva_trae_los_35_con_el_contexto_aprobado():
    previas = _previas()
    filas = adj.casos_reevaluacion()
    assert {f["case_id"] for f in filas} == set(previas)
    for f in filas:
        for c in adj.COLUMNAS_CONTEXTO:
            assert f[c] == previas[f["case_id"]][c]


def test_los_que_dicen_la_frase_y_afirman_algo_van_primero():
    filas = adj.casos_reevaluacion()
    prioritarios = [f["case_id"] for f in filas if f["prioridad"] == "1"]
    assert prioritarios == sorted(prioritarios, key=int)
    assert filas[: len(prioritarios)] == [f for f in filas if f["prioridad"] == "1"]
    assert {"2126", "3328", "4324", "4623"} == set(prioritarios)


def test_una_ronda_completa_no_da_problemas():
    previas, textos = _previas(), adj.respuestas_reevaluacion()
    filas = [_fila_reeval(f) for f in adj.casos_reevaluacion()]
    assert adj.revisar_reevaluacion(filas, previas, textos) == []


def test_atrapa_que_se_cambie_el_contexto_aprobado():
    previas, textos = _previas(), adj.respuestas_reevaluacion()
    filas = [_fila_reeval(f) for f in adj.casos_reevaluacion()]
    filas[0]["pertinencia_contexto"] = "suficiente" if filas[0]["pertinencia_contexto"] != "suficiente" else "parcial"
    assert any("cambio el contexto" in p for p in adj.revisar_reevaluacion(filas, previas, textos))


def test_excede_exige_una_cita_que_este_en_la_respuesta():
    previas, textos = _previas(), adj.respuestas_reevaluacion()
    filas = [_fila_reeval(f) for f in adj.casos_reevaluacion()]
    filas[0]["v1r_fundamentacion"] = "excede"
    assert any("sin citar" in p for p in adj.revisar_reevaluacion(filas, previas, textos))
    filas[0]["v1r_afirmaciones_sin_respaldo"] = "una frase que el modelo nunca dijo"
    assert any("no aparece" in p for p in adj.revisar_reevaluacion(filas, previas, textos))


def test_cumplida_sin_el_abogado_no_pasa():
    previas, textos = _previas(), adj.respuestas_reevaluacion()
    filas = [_fila_reeval(f) for f in adj.casos_reevaluacion()]
    filas[0]["revision_juridica"] = "cumplida"
    assert any("sin el abogado" in p for p in adj.revisar_reevaluacion(filas, previas, textos))


def test_la_respuesta_de_la_planilla_es_la_de_la_corrida():
    previas, textos = _previas(), adj.respuestas_reevaluacion()
    filas = [_fila_reeval(f) for f in adj.casos_reevaluacion()]
    filas[0]["respuesta_v1r"] = "otra cosa"
    assert any("no es la de la corrida" in p for p in adj.revisar_reevaluacion(filas, previas, textos))


def test_b2_funcional_lee_la_planilla_nueva_con_el_prefijo_v1r():
    fila = _fila_reeval(adj.casos_reevaluacion()[0])
    v = b2_funcional.evaluar(fila, modelo="v1r")
    assert v["pasa_b2_funcional"] and not v["tiene_fallo_critico"]
    fila.update(v1r_fundamentacion="excede", v1r_riesgo="alto")
    assert "excede_con_riesgo_alto" in b2_funcional.evaluar(fila, modelo="v1r")["fallos_criticos"]
