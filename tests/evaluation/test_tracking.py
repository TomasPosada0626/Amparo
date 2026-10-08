"""Tests del registro en W&B, con un modulo wandb falso (sin red)."""
from tools.evaluation import tracking


class FakeTable:
    def __init__(self, columns):
        self.columns, self.data = columns, []

    def add_data(self, *fila):
        assert len(fila) == len(self.columns)
        self.data.append(fila)


class FakeWandb:
    Table = FakeTable

    def __init__(self):
        self.runs, self.logs, self.finished = [], [], 0

    def init(self, **kwargs):
        self.runs.append(kwargs)
        return type("Run", (), {"url": f"https://wandb.ai/x/{kwargs['name']}"})()

    def log(self, datos):
        self.logs.append(datos)

    def finish(self):
        self.finished += 1


def test_sin_key_corre_offline(monkeypatch):
    monkeypatch.delenv("WANDB_API_KEY", raising=False)
    assert tracking.modo_de_ejecucion() == "offline"
    import os
    assert os.environ["WANDB_MODE"] == "offline"


def test_con_key_corre_online(monkeypatch):
    monkeypatch.delenv("WANDB_API_KEY", raising=False)
    monkeypatch.setenv("WANDB_MODE", "offline")
    assert tracking.modo_de_ejecucion("clave-de-prueba") == "online"
    import os
    assert "WANDB_MODE" not in os.environ


def test_registrar_ruta_loguea_escalares_tabla_y_traza():
    wb = FakeWandb()
    records = [{"id": 1, "tipo": "gold", "category": "Arriendo", "question": "q", "answer": "a",
                "contexts": ["c1"], "traza": [{"paso": 1, "pensamiento": "p", "accion": "buscar_normas",
                                               "argumento": "x", "observacion": "o"}]}]
    filas = [{"registro_id": 1, "faithfulness": 1.0, "context_precision": 0.5,
              "context_recall": 1.0, "answer_relevancy": 0.9, "escape": False}]

    url = tracking.registrar_ruta(
        wb, sistema="una_pasada_dspy", resumen_ragas={"faithfulness": 1.0, "casos": 1, "context_recall": None},
        escape={"escape_en_gold": 0.0}, latencia_s=4.2, filas_ragas=filas, records=records,
        config={"modelo": "qwen"}, entity="equipo", project="amparo-rag",
    )

    assert url == "https://wandb.ai/x/una_pasada_dspy"
    assert wb.runs[0]["entity"] == "equipo" and wb.runs[0]["config"]["sistema"] == "una_pasada_dspy"
    escalares = wb.logs[0]
    assert escalares["faithfulness"] == 1.0 and escalares["latencia_s_por_consulta"] == 4.2
    assert "context_recall" not in escalares            # los None no se loguean
    assert wb.logs[1]["casos"].data[0][7] == 1.0          # faithfulness del caso
    assert wb.logs[1]["traza_agente"].data[0][3] == "buscar_normas"
    assert wb.finished == 1


def test_la_ruta_de_una_pasada_no_registra_traza():
    wb = FakeWandb()
    tracking.registrar_ruta(wb, sistema="una_pasada", resumen_ragas={}, escape={}, latencia_s=None,
                            filas_ragas=[], records=[{"id": 1, "traza": []}], config={})
    assert "traza_agente" not in wb.logs[1]


def test_comparativa_pone_las_rutas_lado_a_lado():
    wb = FakeWandb()
    tracking.registrar_comparativa(
        wb, resumenes={"una_pasada": {"faithfulness": 0.7, "casos": 50}, "una_pasada_dspy": {"faithfulness": 0.9}},
        escapes={"una_pasada_dspy": {"prudencia_en_adversariales": 1.0}}, latencias={"una_pasada_dspy": 9.1}, config={},
    )
    tabla = wb.logs[0]["comparativa"]
    assert [fila[0] for fila in tabla.data] == ["una_pasada", "una_pasada_dspy"]
    assert tabla.data[1][5] == 1.0 and tabla.data[1][8] == 9.1
