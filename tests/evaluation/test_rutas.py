"""Guardia de rutas: entidades reales usadas donde no corresponden.

Los positivos son respuestas reales del modelo afinado en la corrida de M1 del
2026-10-06 (results/m1_2026-10-06/finetuned_results.jsonl). Los negativos son
las respuestas de referencia del dataset: una regla que marque una referencia
esta mal escrita (o encontro un error del dataset, y entonces hay que
corregirlo alla).
"""
from __future__ import annotations

import json

import pytest

from tools.evaluation import config, dataset, entity_metric, eval_set, rutas

RESULTADOS_M1 = config.PROJECT_ROOT / "results" / "m1_2026-10-06"


@pytest.fixture(scope="module")
def registros():
    return dataset.load_records()


@pytest.fixture(scope="module")
def mapa(registros):
    train, _ = dataset.stratified_split(registros)
    return rutas.construir_mapa(train)


@pytest.mark.parametrize("respuesta, regla", [
    ("Si no responden, radica una querella ante la Procuraduria por omision administrativa.",
     "querella_ante_procuraduria"),
    ("Si no cumple, presenta querella ante el juez de familia y, si hay riesgo, denuncia ante la Fiscalia.",
     "querella_ante_juez"),
    ("Radica una querella ante el curador urbano y la Fiscalia por construccion irregular.",
     "querella_ante_entidad_sin_competencia"),
    ("Presenta querella por publicidad enganosa ante la Superintendencia Financiera.",
     "querella_ante_entidad_sin_competencia"),
    ("Interpon recurso de reposicion y, despues, demanda de nulidad ante la Procuraduria.",
     "demanda_ante_autoridad_no_judicial"),
    ("Puedes reclamar ante el juez civil o demandar ante el comisario del contrato.",
     "demanda_ante_autoridad_no_judicial"),
    ("Con eso radica la accion de tutela ante la Inspeccion del Trabajo, que puede ordenar el pago.",
     "tutela_ante_autoridad_no_judicial"),
    ("Puedes pedir la nulidad del comparendo ante el inspector de transito o ante el juez de control.",
     "juez_de_control_fuera_de_lo_penal"),
    ("La fuga es una emergencia: llama al 123 y a la Linea 123 del Ministerio del Interior.",
     "linea_123_atribuida_a_ministerio"),
])
def test_cada_regla_marca_su_error(respuesta, regla):
    assert regla in rutas.rutas_incorrectas(respuesta)


def test_las_reglas_que_dependen_de_la_pregunta():
    pregunta = "Un juez de Mexico dicto una sentencia a mi favor, la puedo cobrar en Colombia?"
    mal = "Puedes solicitar la ejecucion de esa sentencia ante el tribunal superior de Colombia."
    bien = "Primero hay que pedir el exequatur ante la Corte Suprema de Justicia."
    assert "sentencia_extranjera_sin_corte_suprema" in rutas.rutas_incorrectas(mal, pregunta)
    assert rutas.rutas_incorrectas(bien, pregunta) == []
    # La misma respuesta, para una sentencia colombiana, no se marca.
    assert rutas.rutas_incorrectas(mal, "Me ganaron un proceso, puedo apelar?") == []

    gota = "Estoy en peligro porque un prestamista gota a gota me persigue, pido conciliacion?"
    resp = "La conciliacion se hace despues, con el expediente en la Comisaria de Familia."
    assert "conciliacion_familiar_fuera_de_familia" in rutas.rutas_incorrectas(resp, gota)
    alimentos = "El papa de mi hijo no paga la cuota y me debe plata, concilio?"
    assert rutas.rutas_incorrectas(resp, alimentos) == []


@pytest.mark.parametrize("respuesta", [
    # Usos correctos que estan en el dataset.
    "Presenta una querella ante la Inspeccion del Trabajo y guarda el radicado.",
    "Cambian segun sea la demanda ante el juez civil o la denuncia ante la Fiscalia.",
    "Si te niegan atencion, cabe tutela y queja ante la Supersalud.",
    "La conciliacion prejudicial ante la Procuraduria es requisito antes de demandar.",
    "Denuncia ante la Fiscalia; el juez de control de garantias revisa la captura.",
    # Casos de la revision independiente del 2026-10-06 (eran falsos positivos):
    "Presenta la querella y, si no hay acuerdo, acude ante el juez civil.",
    "Radica la tutela ante la secretaria del juzgado de reparto.",
    "Presenta una querella policiva ante la alcaldia si en tu municipio no hay inspector.",
    "Presenta la querella ante la Fiscalia: la injuria es un delito querellable.",
    "La conciliacion de alimentos se hace en la Comisaria de Familia.",
])
def test_usos_correctos_no_se_marcan(respuesta):
    assert rutas.rutas_incorrectas(respuesta) == []


def test_preguntas_que_solo_nombran_un_pais_no_son_sentencia_extranjera():
    resp = "Presenta la demanda de divorcio ante el juez de familia de tu ultimo domicilio comun."
    assert rutas.rutas_incorrectas(resp, "Mi esposo vive en Espana, como me divorcio?") == []
    assert rutas.rutas_incorrectas(
        "Pide la revision ante el tribunal.", "La curaduria tomo una decision sobre la fachada exterior") == []


def test_ninguna_regla_marca_una_respuesta_de_referencia(registros):
    """Las 1536 referencias del dataset y las del eval set: 0 marcas."""
    referencias = [(r["id"], r["messages"][1]["content"], r["messages"][2]["content"])
                   for r in registros + eval_set.load_eval_set()]
    marcadas = [(i, rutas.rutas_incorrectas(resp, preg)) for i, preg, resp in referencias]
    assert [m for m in marcadas if m[1]] == []


def test_ninguna_referencia_tiene_entidades_inventadas(registros):
    """Mismo control para entity_metric, con las cabezas nuevas (comisario, inspector)."""
    referencias = registros + eval_set.load_eval_set()
    marcadas = [(r["id"], entity_metric.find_fabricated_entities(r["messages"][2]["content"]))
                for r in referencias]
    assert [m for m in marcadas if m[1]] == []


def test_comisario_e_inspector_inventados_se_marcan():
    assert entity_metric.find_fabricated_entities("Demanda ante el comisario de policia.")
    assert entity_metric.find_fabricated_entities("Reclama ante el comisario del arrendamiento.")
    assert entity_metric.find_fabricated_entities("Acude al inspector de construcciones.")
    assert not entity_metric.find_fabricated_entities("Acude al comisario de familia.")
    assert not entity_metric.find_fabricated_entities("Habla con el inspector de transito.")
    assert not entity_metric.find_fabricated_entities("Pide el acta al inspector de la obra.")


def test_fuera_de_contexto_usa_el_tema_de_la_pregunta(mapa):
    """Un accidente de transito no se denuncia ante la Inspeccion de Policia: el
    train nunca la nombra para ese tema (respuesta 80 del afinado)."""
    marcados = rutas.fuera_de_contexto(
        "Radica la denuncia ante la Inspeccion de Policia y demanda ante el juez civil.",
        "Me choco un carro y el conductor no tiene seguro, que hago?",
        "Accidentes de transito", mapa)
    assert "Inspeccion de Policia" in marcados


def test_lo_que_nombra_la_pregunta_no_esta_fuera_de_contexto(mapa):
    """Si la persona misma pregunta por Colpensiones, nombrarla no es salirse del tema."""
    assert "Colpensiones" not in rutas.fuera_de_contexto(
        "Pide a Colpensiones la historia laboral.", "Colpensiones me nego la pension, que hago?",
        "Despido", mapa)


def test_categoria_de_abstencion_toma_el_tema_de_las_vecinas(mapa):
    """"Urgencia con ayuda inmediata" mezcla temas: para un gota a gota, el
    tema sale de las preguntas vecinas (Prestamos informales y usura)."""
    cats = {c for c, _ in mapa.vecinos("Un prestamista gota a gota me amenaza, que hago?")}
    assert "Prestamos informales y usura" in cats


def test_ruido_sobre_referencias_de_validacion(registros, mapa):
    """Las referencias de val son correctas por construccion: lo que la guardia
    marque ahi es ruido. Medido el 2026-10-06: 0 reglas y 2/231 (0.9 %) fuera
    de contexto. Si sube de 3 %, la guardia ya no distingue errores de ruido."""
    _, val = dataset.stratified_split(registros)
    rep = rutas.reporte("referencia_val", rutas.referencias_como_filas(val), mapa)
    assert rep.con_ruta_incorrecta == 0
    assert rep.pct_fuera_de_contexto <= 3.0


@pytest.mark.skipif(not (RESULTADOS_M1 / "finetuned_results.jsonl").exists(), reason="sin resultados de M1")
def test_la_guardia_separa_al_afinado_de_las_referencias(registros, mapa):
    """Corrida de M1 del 2026-10-06: el afinado viola reglas en 19/231 respuestas
    y el baseline en 1/231. Si estos numeros cambian, cambio la guardia: revisar
    que no se haya roto (o actualizar el comentario con la razon)."""
    def cargar(nombre):
        filas = []
        for linea in (RESULTADOS_M1 / nombre).read_text(encoding="utf-8").splitlines():
            d = json.loads(linea)
            filas.append({"id": d["id"], "category": d["category"],
                          "query": d["messages"][1]["content"], "generated": d["generated"]})
        return filas

    ft = rutas.reporte("fine_tuned", cargar("finetuned_results.jsonl"), mapa)
    base = rutas.reporte("baseline", cargar("baseline_results.jsonl"), mapa)
    assert ft.con_ruta_incorrecta == 19
    assert base.con_ruta_incorrecta == 1
