"""Tests de T6 (m4/harness/scorecard.py). Sin GPU, sin VLM, sin M3 real.

Los artefactos de M3 se fabrican con las columnas y claves REALES de
results/ (verificadas en origin/main, corrida m3/20261022T105449Z) pero con
numeros inventados: aqui se prueba el harness, no M3.

    python -m pytest m4/tests -v
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import criterios  # noqa: E402
import scorecard  # noqa: E402

schema = criterios._schema()

SALIDA_TUTELA = schema.render_salida({
    "derecho": "salud", "accionado": "EPS Sura", "mecanismo": "tutela",
    "procede": True, "razon": "no hay otro medio judicial",
    "pretension": "ordenar el medicamento", "fundamento": "",
})
SALIDA_ABSTENCION = schema.render_salida({
    "derecho": schema.DERECHO_ESCAPE, "accionado": "no aplica", "mecanismo": None,
    "procede": False, "razon": "hechos insuficientes", "pretension": "ninguna",
})

# Las 4 etiquetas reales de m3_scorecard.csv / m3_costos.json (origin/main).
BRAZOS = ["1 · fine-tuned solo (M1)", "2 · fine-tuned + RAG ingenuo",
          "3 · fine-tuned + RAG avanzado", "4 · agente + reglas"]
# Encabezado real de m3_scorecard.csv (lo escribe src/harness.py:a_csv).
COLUMNAS_M3 = ["sistema", "n", "acc_derecho", "acc_mecanismo", "acc_procede", "macroF1_mecanismo",
               "baseline_mayoritaria", "rouge_l", "similitud_embeddings", "adherencia_estructural",
               "adherencia_vocabulario", "coherencia", "acierto_juridico", "acierto_gold",
               "acierto_adversarial", "tasa_alucinacion", "tasa_alucinacion_salida",
               "inventadas_fuera_del_fundamento", "precision_citas", "recall_citas", "citas_impertinentes",
               "precision_citas_mecanismo", "precision_citas_fondo", "citas_via_equivocada",
               "juez_nota_media", "juez_nota_gold", "juez_nota_adversarial", "juez_kappa_vs_dominio",
               "juez_sin_parsear"]


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
def casos_validos() -> list[dict]:
    return [
        {"id": "m01", "pregunta": "¿Que hago?", "imagen": "m01.png", "esperado": "tutela",
         "criterio": "exacto", "tipo": "normal"},
        {"id": "m02", "pregunta": "¿Que hago?", "imagen": "m02.png", "esperado": "no_determinable",
         "criterio": "exacto", "tipo": "normal"},
        {"id": "m03", "pregunta": "¿Que dice?", "imagen": "m03.png",
         "esperado": '{"tipo_documento": "oficio", "plazo_dias": 15}', "criterio": "campos", "tipo": "normal"},
        {"id": "m04", "pregunta": "¿Se sostiene?", "imagen": "m04.png", "esperado": "",
         "criterio": "juez_vlm", "tipo": "normal"},
        {"id": "m05", "pregunta": "¿Cuando vence?", "imagen": "m05.png", "esperado": "fecha|plazo_dias",
         "criterio": "valvula", "tipo": "adversarial"},
    ]


@pytest.fixture
def carpeta(tmp_path):
    d = tmp_path / "imagenes"
    d.mkdir()
    for c in casos_validos():
        (d / c["imagen"]).write_bytes(b"")
    return d


class Pipeline:
    """ver / M3 / preguntar / cargar falsos que registran cada llamada en orden."""

    def __init__(self, lecturas=None, salidas=None, respuesta_juez="SI"):
        self.eventos = []
        self.lecturas = lecturas or {}
        self.salidas = salidas or {}
        self.respuesta_juez = respuesta_juez
        self.vistas, self.miradas, self.relatos = [], [], []

    def cargar(self, ruta):
        self.eventos.append(("cargar", Path(ruta).name))
        return {"img": Path(ruta).name}  # objeto nuevo en cada carga

    def ver(self, imagen):
        self.eventos.append(("ver", imagen["img"]))
        self.vistas.append(imagen)
        js = self.lecturas.get(imagen["img"], {"tipo_documento": "oficio", "plazo_dias": 15,
                                                "fecha": None})
        return ("crudo de " + imagen["img"], js)

    def m3(self, relato):
        self.eventos.append(("m3", None))
        self.relatos.append(relato)
        for img, salida in self.salidas.items():
            if img in relato:
                return salida
        return SALIDA_TUTELA

    def preguntar(self, imagen, texto):
        self.eventos.append(("juez", imagen["img"]))
        self.miradas.append(imagen)
        return self.respuesta_juez


def correr(p: Pipeline, carpeta, casos=None, **kw):
    return scorecard.correr_harness(casos or casos_validos(), p.ver, p.m3, p.cargar,
                                    preguntar_fn=kw.pop("preguntar_fn", p.preguntar),
                                    carpeta_imagenes=carpeta, **kw)


def escribir_m3(tmp_path, filas: dict[str, dict]) -> Path:
    ruta = tmp_path / "m3_scorecard.csv"
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS_M3, restval="")
        w.writeheader()
        for sistema, valores in filas.items():
            w.writerow({"sistema": sistema, **valores})
    return ruta


def escribir_costos(tmp_path, latencias: dict[str, float | None]) -> Path:
    ruta = tmp_path / "m3_costos.json"
    datos = [{"etiqueta": s, "latencia_media": lat, "latencia_p50": lat} for s, lat in latencias.items()]
    ruta.write_text(json.dumps({"_corrida": "ENSAYO", "_modulo": "m3", "datos": datos}), encoding="utf-8")
    return ruta


FILA_M3 = {"n": "80", "acc_mecanismo": "0.6", "acierto_juridico": "0.55"}


# --------------------------------------------------------------------------
# armar_relato == sistema_multimodal del notebook
# --------------------------------------------------------------------------
def test_armar_relato_con_json_es_la_formula_del_notebook():
    js = {"tipo_documento": "oficio", "entidad": "Alcaldía"}
    esperado = "¿Que hago?\n\nDATOS DEL DOCUMENTO ADJUNTO:\n" + json.dumps(js, ensure_ascii=False)
    assert scorecard.armar_relato("¿Que hago?", js, "crudo") == esperado


@pytest.mark.parametrize("js", [None, {}])
def test_armar_relato_sin_json_usa_el_texto_crudo(js):
    # `if js` del notebook: None y {} caen al texto crudo.
    assert scorecard.armar_relato("P", js, "texto crudo") == "P\n\nDATOS DEL DOCUMENTO ADJUNTO:\ntexto crudo"


# --------------------------------------------------------------------------
# correr_harness
# --------------------------------------------------------------------------
def test_una_fila_por_caso_con_las_columnas_del_plan(carpeta):
    filas, trazas = correr(Pipeline(), carpeta)
    assert [f["id"] for f in filas] == [c["id"] for c in casos_validos()]
    assert all(list(f) == scorecard.COLUMNAS_SCORECARD for f in filas)
    assert set(trazas) == {c["id"] for c in casos_validos()}
    assert all(0.0 <= f["nota"] <= 1.0 for f in filas)


def test_juez_mira_el_mismo_objeto_que_ver(carpeta):
    p = Pipeline()
    correr(p, carpeta)
    assert len(p.miradas) == 1
    assert p.miradas[0] is p.vistas[3]  # m04 es el caso juez_vlm


def test_cada_imagen_se_carga_una_vez(carpeta):
    p = Pipeline()
    correr(p, carpeta)
    cargas = [e for e in p.eventos if e[0] == "cargar"]
    assert [n for _, n in cargas] == [c["imagen"] for c in casos_validos()]


def test_cronometro_mide_ver_mas_m3_y_deja_fuera_carga_y_juez(carpeta, monkeypatch):
    p = Pipeline()
    reloj = iter(range(0, 1000, 10))  # cada lectura avanza 10 s

    def perf_counter():
        p.eventos.append(("reloj", None))
        return next(reloj)

    monkeypatch.setattr(scorecard.time, "perf_counter", perf_counter)
    filas, _ = correr(p, carpeta)
    tipos = [e[0] for e in p.eventos]
    # Por caso: cargar, reloj, ver, m3, reloj (y el juez DESPUES del segundo reloj).
    assert tipos[:5] == ["cargar", "reloj", "ver", "m3", "reloj"]
    i_juez = tipos.index("juez")
    assert tipos[i_juez - 1] == "reloj" and tipos[i_juez - 2] == "m3"
    assert all(f["segundos"] == 10 for f in filas)


def test_csv_invalido_no_corre_nada(carpeta):
    p = Pipeline()
    casos = casos_validos()
    casos[0]["esperado"] = "acción de tutela"
    with pytest.raises(ValueError, match="eval set invalido"):
        correr(p, carpeta, casos)
    assert p.eventos == []


def test_imagen_faltante_no_corre_nada(carpeta):
    (carpeta / "m03.png").unlink()
    p = Pipeline()
    with pytest.raises(ValueError, match="m03.png"):
        correr(p, carpeta)
    assert p.eventos == []


def test_juez_vlm_sin_preguntar_fn_no_corre_nada(carpeta):
    p = Pipeline()
    with pytest.raises(ValueError, match="preguntar_fn"):
        correr(p, carpeta, preguntar_fn=None)
    assert p.eventos == []


def test_sin_casos_juez_vlm_no_hace_falta_preguntar_fn(carpeta):
    casos = casos_validos()
    casos[3] = {**casos[3], "criterio": "exacto", "esperado": "tutela"}
    filas, _ = correr(Pipeline(), carpeta, casos, preguntar_fn=None)
    assert len(filas) == 5


def test_excepcion_del_sistema_detiene_la_corrida(carpeta):
    p = Pipeline()

    def ver_que_falla(imagen):
        raise RuntimeError("CUDA out of memory")

    with pytest.raises(RuntimeError, match="CUDA"):
        scorecard.correr_harness(casos_validos(), ver_que_falla, p.m3, p.cargar,
                                 preguntar_fn=p.preguntar, carpeta_imagenes=carpeta)


def test_m3_recibe_el_relato_armado_con_el_json_de_ver(carpeta):
    p = Pipeline(lecturas={"m01.png": {"tipo_documento": "sentencia"}})
    correr(p, carpeta)
    assert p.relatos[0] == scorecard.armar_relato("¿Que hago?", {"tipo_documento": "sentencia"}, "crudo de m01.png")


def test_trazas_guardan_crudo_js_salida_etapa_y_respuesta_del_juez(carpeta):
    p = Pipeline(respuesta_juez="Probablemente sí")
    _, trazas = correr(p, carpeta)
    for t in trazas.values():
        assert {"crudo", "js", "salida", "etapa"} <= set(t)
    assert trazas["m04"]["respuesta_juez"] == "Probablemente sí"
    assert "respuesta_juez" not in trazas["m01"]


def test_js_none_da_cero_en_campos_y_valvula(carpeta):
    p = Pipeline(lecturas={"m03.png": None, "m05.png": None})
    filas, trazas = correr(p, carpeta)
    notas = {f["id"]: f["nota"] for f in filas}
    assert notas["m03"] == 0.0 and notas["m05"] == 0.0
    assert trazas["m03"]["etapa"] == trazas["m05"]["etapa"] == "ver() no produjo JSON"


# --------------------------------------------------------------------------
# diagnosticar
# --------------------------------------------------------------------------
def _diag(caso, **traza):
    nota = criterios.calificar(caso, traza, preguntar_fn=lambda i, t: traza.get("respuesta_juez"), imagen="x")
    return scorecard.diagnosticar(caso, traza, nota)


def test_diagnostico_ok_cuando_la_nota_es_1():
    assert _diag({"id": "a", "criterio": "exacto", "esperado": "tutela"}, js={}, salida=SALIDA_TUTELA) == "ok"


def test_diagnostico_exacto_con_json_no_culpa_a_una_sola_etapa():
    etapa = _diag({"id": "a", "criterio": "exacto", "esperado": "habeas_corpus"},
                  js={"tipo_documento": "oficio"}, salida=SALIDA_TUTELA)
    assert "M3 respondio tutela (esperado habeas_corpus)" in etapa
    assert "motor de reglas" in etapa and "hechos leidos" in etapa


def test_diagnostico_exacto_sin_json():
    etapa = _diag({"id": "a", "criterio": "exacto", "esperado": "tutela"}, js=None, salida=SALIDA_ABSTENCION)
    assert etapa.startswith("ver() no produjo JSON") and "respondio abstencion" in etapa


def test_diagnostico_campos_nombra_lo_que_leyo_mal():
    etapa = _diag({"id": "a", "criterio": "campos", "esperado": '{"tipo_documento": "oficio", "plazo_dias": 15}'},
                  js={"tipo_documento": "oficio", "plazo_dias": 10})
    assert etapa == "campos: leyo mal plazo_dias (esperado 15, leyo 10)"


def test_diagnostico_valvula_nombra_lo_inventado():
    etapa = _diag({"id": "a", "criterio": "valvula", "esperado": "fecha|plazo_dias"},
                  js={"fecha": "2026-01-15", "plazo_dias": None})
    assert etapa == "valvula: invento fecha='2026-01-15'"


@pytest.mark.parametrize("respuesta, fragmento", [
    ("NO.", "respondio NO"),
    ("Probablemente sí", "respuesta no valida 'Probablemente sí'"),
    (None, "respuesta no valida None"),
])
def test_diagnostico_juez_distingue_no_de_ambiguo(respuesta, fragmento):
    etapa = _diag({"id": "a", "criterio": "juez_vlm", "esperado": ""}, salida=SALIDA_TUTELA,
                  respuesta_juez=respuesta)
    assert fragmento in etapa


# --------------------------------------------------------------------------
# guardar
# --------------------------------------------------------------------------
def test_guardar_escribe_scorecard_y_trazas(carpeta, tmp_path):
    filas, trazas = correr(Pipeline(), carpeta)
    sc, tr = tmp_path / "out" / "scorecard_m4.csv", tmp_path / "out" / "trazas_m4.json"
    scorecard.guardar(filas, trazas, sc, tr)
    with sc.open(encoding="utf-8", newline="") as f:
        leidas = list(csv.DictReader(f))
    assert len(leidas) == len(casos_validos())
    assert list(leidas[0]) == ["id", "criterio", "tipo", "nota", "segundos", "salida"]
    assert leidas[0]["salida"] == SALIDA_TUTELA  # la salida multilinea sobrevive al CSV
    assert json.loads(tr.read_text(encoding="utf-8")).keys() == trazas.keys()
    assert b"\r" not in tr.read_bytes()


# --------------------------------------------------------------------------
# leer_fila_m3 / leer_latencia_m3
# --------------------------------------------------------------------------
def test_leer_fila_m3_devuelve_el_brazo_pedido(tmp_path):
    ruta = escribir_m3(tmp_path, {b: FILA_M3 for b in BRAZOS})
    fila = scorecard.leer_fila_m3("4 · agente + reglas", ruta)
    assert fila["sistema"] == "4 · agente + reglas" and fila["acierto_juridico"] == "0.55"


@pytest.mark.parametrize("sistema", [None, ""])
def test_leer_fila_m3_sin_brazo_lista_los_disponibles_y_para(tmp_path, sistema):
    ruta = escribir_m3(tmp_path, {b: FILA_M3 for b in BRAZOS})
    with pytest.raises(ValueError, match="4 · agente \\+ reglas"):
        scorecard.leer_fila_m3(sistema, ruta)


def test_leer_fila_m3_brazo_desconocido(tmp_path):
    ruta = escribir_m3(tmp_path, {b: FILA_M3 for b in BRAZOS})
    with pytest.raises(KeyError, match="agente"):
        scorecard.leer_fila_m3("agente", ruta)


def test_leer_fila_m3_sin_results_explica_donde_esta(tmp_path):
    with pytest.raises(FileNotFoundError, match="origin/main"):
        scorecard.leer_fila_m3("4 · agente + reglas", tmp_path / "no_existe.csv")


def test_latencia_m3_es_por_caso_y_no_por_llamada(tmp_path):
    # El brazo 4 hace varias llamadas por caso: m3/20261022T105449Z trae 548
    # llamadas en 130 casos, 3.238 s por llamada y 1774.3 s en total.
    ruta = tmp_path / "m3_costos.json"
    ruta.write_text(json.dumps({"datos": [{
        "etiqueta": BRAZOS[3], "casos": 130, "llamadas_reales": 548,
        "latencia_media": 3.238, "latencia_total_s": 1774.3}]}), encoding="utf-8")
    assert scorecard.leer_latencia_m3(BRAZOS[3], ruta) == round(1774.3 / 130, 3)


def test_leer_latencia_m3(tmp_path):
    ruta = escribir_costos(tmp_path, {BRAZOS[0]: None, BRAZOS[3]: 2.834})
    assert scorecard.leer_latencia_m3(BRAZOS[3], ruta) == 2.834
    assert scorecard.leer_latencia_m3(BRAZOS[0], ruta) is None  # "sin instrumentar": no es 0
    with pytest.raises(KeyError):
        scorecard.leer_latencia_m3("otro", ruta)
    with pytest.raises(FileNotFoundError, match="origin/main"):
        scorecard.leer_latencia_m3(BRAZOS[3], tmp_path / "no.json")


# --------------------------------------------------------------------------
# construir_tabla_delta / tabla_markdown
# --------------------------------------------------------------------------
def _filas(*specs):
    return [{"id": i, "criterio": c, "tipo": t, "nota": n, "segundos": s, "salida": ""}
            for i, c, t, n, s in specs]


FILAS = _filas(("a", "exacto", "normal", 1.0, 2.0), ("b", "exacto", "normal", 0.0, 4.0),
               ("c", "campos", "normal", 0.5, 3.0), ("d", "juez_vlm", "normal", 1.0, 3.0),
               ("e", "valvula", "adversarial", 0.0, 8.0))
TRAZAS = {"b": {"etapa": "M3 respondio tutela"}, "e": {"etapa": "valvula: invento fecha='x'"}}


def test_tabla_delta_tiene_las_5_filas_con_metrica_nombrada():
    res = scorecard.construir_tabla_delta(FILAS, TRAZAS, {"sistema": BRAZOS[3], **FILA_M3}, latencia_m3=2.834)
    assert [r["fila"] for r in res["tabla"]] == ["Casos sin imagen (M3)", "Casos con imagen (M4)",
                                                "Adversarial (valvula)", "Latencia media", "Peor caso"]
    assert all(r["metrica"] for r in res["tabla"])
    assert "acierto_juridico" in res["tabla"][0]["metrica"] and BRAZOS[3] in res["tabla"][0]["metrica"]
    assert res["sistema_m3"] == BRAZOS[3]


def test_tabla_delta_valores():
    res = scorecard.construir_tabla_delta(FILAS, TRAZAS, {"sistema": BRAZOS[3], **FILA_M3}, latencia_m3=2.834)
    t = {r["fila"]: r for r in res["tabla"]}
    assert t["Casos sin imagen (M3)"]["valor"] == 0.55 and t["Casos sin imagen (M3)"]["latencia"] == 2.834
    assert t["Casos con imagen (M4)"]["valor"] == 0.625      # (1 + 0 + 0.5 + 1) / 4: sin el adversarial
    assert t["Casos con imagen (M4)"]["latencia"] == 3.0
    assert t["Adversarial (valvula)"]["valor"] == 0.0 and t["Adversarial (valvula)"]["latencia"] == 8.0
    assert t["Latencia media"]["latencia"] == 4.0            # los 5 casos
    cd = res["comparacion_directa"]
    assert cd == {"metrica": "acierto de mecanismo (misma magnitud en ambos)", "m4_casos_exacto": 0.5,
                  "n_m4": 2, "m3_acc_mecanismo": 0.6, "n_m3": 80}


def test_peor_caso_lista_todos_los_empatados_con_su_etapa():
    res = scorecard.construir_tabla_delta(FILAS, TRAZAS, {"sistema": BRAZOS[3], **FILA_M3})
    assert [p["id"] for p in res["peores"]] == ["b", "e"]
    assert res["peores"][1]["etapa"] == "valvula: invento fecha='x'"
    assert res["tabla"][4]["valor"] == "b (0.0), e (0.0)"


def test_tabla_markdown_tiene_la_forma_de_la_plantilla_y_no_inventa_latencia():
    res = scorecard.construir_tabla_delta(FILAS, TRAZAS, {"sistema": BRAZOS[0], **FILA_M3}, latencia_m3=None)
    md = scorecard.tabla_markdown(res)
    assert md.splitlines()[0] == "| | Métrica | Valor | Latencia (s) |"
    assert "no disponible" in md.splitlines()[2]   # brazo sin instrumentar: no 0.000
    filas_md = {l.split(" | ")[0].strip("| "): l for l in md.splitlines() if l.startswith("| ")}
    assert filas_md["Latencia media"].split(" | ")[2] == "—"       # sin valor: guion, nunca 0
    assert filas_md["Peor caso"].rstrip(" |").endswith("—")
    assert "(n = 2)" in md and "Peor caso" in md
    assert "0.74" not in md


# --------------------------------------------------------------------------
# correr_t6 de punta a punta (con el CSV de ejemplo para Lucas)
# --------------------------------------------------------------------------
@pytest.fixture
def ejemplo(tmp_path):
    ruta = Path(__file__).resolve().parents[1] / "eval_set" / "casos_m4.ejemplo.csv"
    img = tmp_path / "imagenes"
    img.mkdir()
    for c in criterios.cargar_casos(ruta):
        (img / c["imagen"]).write_bytes(b"")
    return ruta, img


def _rutas(tmp_path):
    return {"ruta_scorecard": tmp_path / "scorecard_m4.csv", "ruta_trazas": tmp_path / "trazas_m4.json",
            "ruta_delta": tmp_path / "delta_m4.json"}


def test_correr_t6_de_punta_a_punta(ejemplo, tmp_path, capsys):
    ruta, img = ejemplo
    p = Pipeline()
    m3 = escribir_m3(tmp_path, {b: FILA_M3 for b in BRAZOS})
    costos = escribir_costos(tmp_path, {b: 3.0 for b in BRAZOS})
    res = scorecard.correr_t6(p.cargar, p.ver, p.preguntar, p.m3, sistema_m3=BRAZOS[3],
                              ruta_casos=ruta, carpeta_imagenes=img, ruta_m3_scorecard=m3,
                              ruta_m3_costos=costos, **_rutas(tmp_path))
    n = len(criterios.cargar_casos(ruta))
    with (tmp_path / "scorecard_m4.csv").open(encoding="utf-8", newline="") as f:
        assert len(list(csv.DictReader(f))) == n          # prueba de T6: una fila por caso
    assert json.loads((tmp_path / "delta_m4.json").read_text(encoding="utf-8")) == res
    assert res["sistema_m3"] == BRAZOS[3]
    assert "| Casos sin imagen (M3) |" in capsys.readouterr().out


def test_correr_t6_sin_results_guarda_el_scorecard_antes_de_fallar(ejemplo, tmp_path):
    ruta, img = ejemplo
    p = Pipeline()
    with pytest.raises(FileNotFoundError, match="origin/main"):
        scorecard.correr_t6(p.cargar, p.ver, p.preguntar, p.m3, sistema_m3=BRAZOS[3],
                            ruta_casos=ruta, carpeta_imagenes=img,
                            ruta_m3_scorecard=tmp_path / "no.csv", ruta_m3_costos=tmp_path / "no.json",
                            **_rutas(tmp_path))
    assert (tmp_path / "scorecard_m4.csv").exists() and (tmp_path / "trazas_m4.json").exists()
    assert not (tmp_path / "delta_m4.json").exists()


def test_cargar_guardado_devuelve_lo_mismo_que_se_guardo(carpeta, tmp_path):
    filas, trazas = correr(Pipeline(lecturas={"m03.png": None}), carpeta)
    scorecard.guardar(filas, trazas, tmp_path / "s.csv", tmp_path / "t.json")
    assert scorecard.cargar_guardado(tmp_path / "s.csv", tmp_path / "t.json") == (filas, trazas)


def test_tabla_desde_disco_da_la_misma_tabla_que_la_corrida_completa(ejemplo, tmp_path):
    # Corrida sin results/: falla al final, pero deja scorecard y trazas.
    ruta, img = ejemplo
    p = Pipeline(respuesta_juez="NO")
    with pytest.raises(FileNotFoundError):
        scorecard.correr_t6(p.cargar, p.ver, p.preguntar, p.m3, sistema_m3=BRAZOS[3],
                            ruta_casos=ruta, carpeta_imagenes=img, ruta_m3_scorecard=tmp_path / "no.csv",
                            ruta_m3_costos=tmp_path / "no.json", **_rutas(tmp_path))
    # Llega results/: la tabla se arma sin volver a correr nada.
    m3 = escribir_m3(tmp_path, {b: FILA_M3 for b in BRAZOS})
    costos = escribir_costos(tmp_path, {b: 3.0 for b in BRAZOS})
    desde_disco = scorecard.tabla_desde_disco(BRAZOS[3], ruta_m3_scorecard=m3, ruta_m3_costos=costos,
                                              **_rutas(tmp_path))
    # Misma tabla que la corrida completa (los segundos dependen del reloj: se igualan).
    filas, trazas = scorecard.cargar_guardado(tmp_path / "scorecard_m4.csv", tmp_path / "trazas_m4.json")
    directa = scorecard.construir_tabla_delta(filas, trazas, scorecard.leer_fila_m3(BRAZOS[3], m3),
                                              latencia_m3=3.0)
    assert desde_disco == directa
    assert json.loads((tmp_path / "delta_m4.json").read_text(encoding="utf-8")) == desde_disco
    assert any("juez: respondio NO" in (p_["etapa"] or "") for p_ in desde_disco["peores"])


def test_tabla_desde_disco_exige_el_brazo(tmp_path):
    with pytest.raises(ValueError, match="sistema_m3"):
        scorecard.tabla_desde_disco("", **_rutas(tmp_path))


@pytest.mark.parametrize("sistema", [None, ""])
def test_correr_t6_exige_el_brazo_antes_de_correr(ejemplo, tmp_path, sistema):
    ruta, img = ejemplo
    p = Pipeline()
    with pytest.raises(ValueError, match="sistema_m3"):
        scorecard.correr_t6(p.cargar, p.ver, p.preguntar, p.m3, sistema_m3=sistema,
                            ruta_casos=ruta, carpeta_imagenes=img, **_rutas(tmp_path))
    assert p.eventos == []


# --------------------------------------------------------------------------
# delta_con_sin_imagen: el efecto del componente, caso por caso
# --------------------------------------------------------------------------
def test_delta_con_sin_imagen_separa_lo_que_aporta_de_lo_que_no(tmp_path):
    casos = tmp_path / "casos.csv"
    casos.write_text(
        "id,pregunta,imagen,esperado,criterio,tipo\n"
        "a1,pregunta uno,x.png,tutela,exacto,normal\n"
        "a2,pregunta dos,x.png,accion_popular,exacto,normal\n"
        "a3,pregunta tres,x.png,{\"tipo_documento\": \"oficio\"},campos,normal\n",
        encoding="utf-8")

    def bloque(mec):
        return (f"Derecho: salud\nAccionado: X\nMecanismo: {mec}\n"
                "Procedencia: si\nPretension: y")
    trazas = tmp_path / "trazas.json"
    trazas.write_text(json.dumps({
        "a1": {"salida": bloque("accion de tutela"), "js": {}},
        "a2": {"salida": bloque("accion popular"), "js": {}},
        "a3": {"salida": "", "js": {}}}), encoding="utf-8")
    # Sin imagen: a1 acierta igual y a2 falla.
    sin = {"pregunta uno": bloque("accion de tutela"), "pregunta dos": bloque("accion de tutela")}
    res = scorecard.delta_con_sin_imagen(lambda p: sin[p], ruta_casos=casos,
                                         ruta_trazas=trazas, ruta_salida=tmp_path / "d.json")
    efectos = {f["id"]: f["efecto"] for f in res["casos"]}
    assert res["n"] == 2                                    # solo los `exacto`
    assert efectos == {"a1": "no aporta (acierta igual)", "a2": "aporta"}
    assert (res["acierto_con_imagen"], res["acierto_sin_imagen"]) == (1.0, 0.5)


def test_delta_con_sin_imagen_registra_latencia_de_las_dos_condiciones(tmp_path):
    casos = tmp_path / "casos.csv"
    casos.write_text("id,pregunta,imagen,esperado,criterio,tipo\n"
                     "a1,pregunta uno,x.png,tutela,exacto,normal\n", encoding="utf-8")
    salida = ("Derecho: salud\nAccionado: X\nMecanismo: accion de tutela\n"
              "Procedencia: si\nPretension: y")
    trazas = tmp_path / "trazas.json"
    trazas.write_text(json.dumps({"a1": {"salida": salida, "js": {}}}), encoding="utf-8")
    sc = tmp_path / "sc.csv"
    sc.write_text("id,criterio,tipo,nota,segundos,salida\na1,exacto,normal,1.0,9.5,x\n",
                  encoding="utf-8")
    res = scorecard.delta_con_sin_imagen(lambda p: salida, ruta_casos=casos, ruta_trazas=trazas,
                                         ruta_salida=tmp_path / "d.json", ruta_scorecard=sc)
    fila = res["casos"][0]
    assert fila["segundos_con_imagen"] == 9.5
    assert fila["segundos_sin_imagen"] >= 0
    assert res["latencia_con_imagen"] == 9.5 and res["latencia_sin_imagen"] is not None
