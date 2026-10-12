"""Adjudicacion del escenario irrelevante (C5): los controles de la planilla."""
from tools import adjudicacion_escenarios as ae


def _filas():
    textos = {m: ae.respuestas(m) for m in ae.MODELOS}
    filas = []
    for c in ae.casos_irrelevantes():
        cid = str(c["id"])
        f = {k: "" for k in ae.COLUMNAS}
        f.update(case_id=cid, pertinencia_contexto="insuficiente", justificacion_contexto="no alcanza",
                 revision_juridica="requerida", confianza="media", justificacion_final="x",
                 revisor="primera pasada", fecha_revision="2026-10-12", origen="corridas")
        for m in ae.MODELOS:
            f.update({f"respuesta_{m}": textos[m][cid], f"{m}_fundamentacion": "dentro",
                      f"{m}_calibracion": "reconoce", f"{m}_orientacion_segura": "si",
                      f"{m}_riesgo": "bajo"})
        filas.append(f)
    return filas, textos


def test_son_los_49_irrelevantes_y_las_dos_corridas_los_traen():
    filas, textos = _filas()
    assert len(filas) == 49
    for m in ae.MODELOS:
        assert set(textos[m]) == {f["case_id"] for f in filas}


def test_una_planilla_completa_no_da_problemas():
    filas, textos = _filas()
    assert ae.revisar(filas, textos) == []


def test_atrapa_un_caso_que_falta_y_una_fila_sin_llenar():
    filas, textos = _filas()
    filas[1]["v3_riesgo"] = ""
    p = ae.revisar(filas[1:], textos)
    assert any("faltan" in x for x in p)
    assert any("sin llenar" in x for x in p)


def test_excede_exige_cita_de_la_respuesta_de_ese_modelo():
    filas, textos = _filas()
    f = filas[0]
    f["v1_fundamentacion"] = "excede"
    assert any("sin citar" in x for x in ae.revisar(filas, textos))
    f["v1_afirmaciones_sin_respaldo"] = "algo que v1 nunca dijo"
    assert any("no aparece" in x for x in ae.revisar(filas, textos))
    f["v1_afirmaciones_sin_respaldo"] = f["respuesta_v1"][:40]
    assert ae.revisar(filas, textos) == []


def test_la_respuesta_tiene_que_ser_la_de_la_corrida():
    filas, textos = _filas()
    filas[0]["respuesta_v3"] = filas[0]["respuesta_v1"] + " (cambiada)"
    assert any("no es la de la corrida" in x for x in ae.revisar(filas, textos))


def test_cumplida_exige_al_abogado():
    filas, textos = _filas()
    filas[0]["revision_juridica"] = "cumplida"
    assert any("sin el abogado" in x for x in ae.revisar(filas, textos))


def test_el_contexto_que_si_responde_se_reporta_aparte():
    filas, _ = _filas()
    filas[0]["pertinencia_contexto"] = "suficiente"
    a = ae.analizar(filas)
    assert a["v1"]["n"] == 49 and a["v1"]["n_insuficiente"] == 48
