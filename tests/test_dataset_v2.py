"""Dataset de M1 v2 (tools/dataset_v2.py): puertas de calidad y particion.

Las puertas se prueban con ejemplos armados a mano: una puerta que no falla
cuando debe es peor que no tenerla, porque da por buena una cita inventada."""
from __future__ import annotations

from tools import dataset_v2_quality as q
from tools.evaluation import dataset

CONTEXTO = [
    {"cita": "Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana), Articulo 20",
     "doc_id": "ley820", "articulos": ["20"]},
    {"cita": "Ley 100 de 1993 (Sistema de Seguridad Social Integral), Articulo 18",
     "doc_id": "ley100", "articulos": ["18"]},
]


def test_cita_con_su_norma_esta_respaldada():
    ok, no, ajenas = q.citas("Según el artículo 20 de la Ley 820 de 2003, el canon...", CONTEXTO)
    assert ok == ["articulo 20"] and no == [] and ajenas == []


def test_el_numero_solo_no_basta_si_la_norma_es_otra():
    """El articulo 18 esta en el contexto, pero de la Ley 100: citarlo como de la
    Ley 820 es atribuirle a una ley lo que dice otra."""
    _, no, _ = q.citas("El artículo 18 de la Ley 820 de 2003 limita el canon.", CONTEXTO)
    assert no == ["articulo 18"]


def test_la_misma_ley_remite_a_la_norma_citada_antes():
    texto = "El artículo 20 de la Ley 820 de 2003 dice X, y el artículo 18 de la misma ley dice Y."
    _, no, _ = q.citas(texto, CONTEXTO)
    assert no == ["articulo 18"]          # el 18 del contexto es de la Ley 100, no de la 820
    contexto = CONTEXTO + [{"cita": "Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana), "
                                     "Articulo 18", "doc_id": "ley820", "articulos": ["18"]}]
    ok, no, _ = q.citas(texto, contexto)
    assert no == [] and ok == ["articulo 20", "articulo 18"]


def test_una_ley_que_no_esta_en_el_contexto_se_marca():
    _, _, ajenas = q.citas("Lo dice la Ley 1480 de 2011.", CONTEXTO)
    assert ajenas == ["Ley 1480 de 2011"]


def _registro(modo, respuesta, fuentes=("LEY-820-2003:20",), pregunta="Me subieron el arriendo, es legal?"):
    user = f"CONTEXTO:\n...\n\nPREGUNTA DEL USUARIO:\n{pregunta}"
    return {"id": 2999, "category": "Arriendo", "modo": modo, "base_id": None,
            "fuentes": list(fuentes) if modo in ("B1", "B3") else [], "contexto": CONTEXTO,
            "messages": [{"role": "system", "content": "s"}, {"role": "user", "content": user},
                         {"role": "assistant", "content": respuesta}]}


def test_b1_que_no_cita_la_fuente_falla():
    r = _registro("B1", "Sube solo con el IPC del año anterior y debe avisarte por correo certificado; "
                        "si no, objétalo por escrito y acude a un centro de conciliación con tus recibos y el contrato.")
    assert "no cita la fuente" in q.revisar(r)


def test_b1_correcto_pasa():
    r = _registro("B1", "Según el artículo 20 de la Ley 820 de 2003, el canon solo se reajusta cada doce meses "
                        "y hasta el IPC del año anterior, con aviso escrito. Objétalo por escrito y, si insiste, "
                        "acude a un centro de conciliación con el contrato y los recibos.")
    assert q.revisar(r) == []


def test_b2_debe_empezar_con_la_frase_de_escape_y_no_citar():
    assert "escape" in q.revisar(_registro("B2", "Te sugiero consultar un consultorio jurídico universitario, "
                                                 "porque no tengo informacion verificada sobre esto."))
    malo = _registro("B2", "No tengo informacion verificada sobre esto en mi base de conocimiento. "
                           "Pero el artículo 20 de la Ley 820 de 2003 dice que sube con el IPC.")
    assert "cita en escape" in q.revisar(malo)


def test_b3_debe_decir_lo_que_falta():
    r = _registro("B3", "Según el artículo 20 de la Ley 820 de 2003, el canon sube cada doce meses hasta el IPC. "
                        "Sobre el depósito, revisa tu contrato y acude a un centro de conciliación si hay conflicto.")
    assert "B3 sin la parte que falta" in q.revisar(r)


def test_plazo_que_no_esta_en_el_contexto_falla():
    r = _registro("B1", "Según el artículo 20 de la Ley 820 de 2003, tienes 10 días hábiles para objetar el "
                        "reajuste. Hazlo por escrito y acude a un centro de conciliación con el contrato y los recibos.")
    assert "plazo sin respaldo" in q.revisar(r)


def test_split_v2_respeta_el_lado_de_la_pregunta_base():
    m1 = dataset.load_records()
    _, val = dataset.stratified_split(m1)
    id_val = val[0]["id"]
    id_train = next(r["id"] for r in m1 if r["id"] not in {v["id"] for v in val})
    v2 = [{"id": 2001, "category": "Arriendo", "modo": "B1", "base_id": id_val},
          {"id": 2002, "category": "Arriendo", "modo": "B1", "base_id": id_train}]
    train2, val2 = dataset.split_v2(v2, m1)
    assert [r["id"] for r in val2] == [2001] and [r["id"] for r in train2] == [2002]


def test_split_v2_no_mueve_el_split_de_m1():
    m1 = dataset.load_records()
    antes = dataset.stratified_split(m1)
    dataset.split_v2([{"id": 2001, "category": "Arriendo", "modo": "B2", "base_id": None}], m1)
    assert dataset.stratified_split(m1) == antes


def test_las_fuentes_del_dataset_v2_pasan_todas_las_puertas():
    """Las fuentes versionadas en data/dataset_src_v2 (sin GPU: chunkea el corpus)."""
    from tools import dataset_v2

    registros = dataset_v2.construir(dataset_v2.cargar_especificaciones(), dataset.load_records())
    analisis = q.analizar(registros)
    assert not analisis["problemas"], analisis["problemas"]
    assert not analisis["repetidos"] and not analisis["fuga_eval_set"]


def test_un_ejemplo_sin_contexto_no_pasa():
    """Regla de Tomas: ningun ejemplo de v2 queda con contexto vacio. En
    servicio, sin contexto el codigo responde la frase de escape sin llamar al
    modelo; un ejemplo asi ensenaria algo que el modelo nunca vive."""
    r = _registro("B1", "Según el artículo 20 de la Ley 820 de 2003, el canon solo se reajusta cada doce meses "
                        "y hasta el IPC; objétalo por escrito y acude a un centro de conciliación con tus recibos.")
    r["contexto"] = []
    assert "contexto vacio" in q.revisar(r)


def test_cada_ejemplo_trae_en_su_contexto_los_articulos_que_cita():
    """B1/B3: el contexto viene de la busqueda; si no trajo el articulo que
    responde, se mete (busqueda+oraculo). Nunca queda un B1 sin su fuente."""
    from tools import dataset_v2

    registros = dataset_v2.construir(dataset_v2.cargar_especificaciones(), dataset.load_records())
    assert {r["modo"] for r in registros} <= {"B1", "B2", "B3"}
    for r in registros:
        assert len(r["contexto"]) == dataset_v2.FRAGMENTOS_POR_EJEMPLO
        if r["modo"] == "B2":
            assert r["contexto_origen"] == "busqueda-otras-normas"
            continue
        assert r["contexto_origen"] in ("busqueda", "busqueda+oraculo")
        vistos = {a for f in r["contexto"] for a in f["articulos"]}
        for fuente in r["fuentes"]:
            assert fuente.rsplit(":", 1)[1] in vistos, (r["id"], fuente)


def test_una_pregunta_del_eval_set_en_el_train_de_v2_es_fuga(monkeypatch):
    from tools.evaluation import eval_set

    ev = eval_set.load_eval_set()
    copia = _registro("B2", "No tengo informacion verificada sobre esto en mi base de conocimiento.",
                      pregunta=ev[0]["messages"][1]["content"])
    copia["pregunta"] = ev[0]["messages"][1]["content"]
    copia["id"] = 2998
    analisis = q.analizar([copia])
    assert analisis["fuga_eval_set"], "la copia literal de una pregunta del eval set no se detecto"

