"""Fase Groq de M2: retoma tras el cupo diario, no repite llamadas y el
informe dice lo que falta en vez de mostrar ceros."""
from __future__ import annotations

import json

import httpx
import openai
import pytest

from tools.evaluation import dataset, eval_set, external_judge, fase_groq, pipeline, rutas, scorecard
from tools.evaluation.generation import GenerationResult


def _gen(r, label, texto):
    return GenerationResult(id=r["id"], category=r["category"], query=r["messages"][1]["content"],
                            expected=r["messages"][2]["content"], generated=texto, label=label, latency_s=1.0)


@pytest.fixture()
def corrida(tmp_path):
    """Corrida chica: 6 preguntas de validacion y 3 del eval set."""
    registros = dataset.load_records()
    train, val = dataset.stratified_split(registros)
    elegidas = val[:6]
    base = [_gen(r, "baseline", "Respuesta larga del modelo base. " * 8) for r in elegidas]
    ft = [_gen(r, "fine_tuned", r["messages"][2]["content"]) for r in elegidas]
    ev = eval_set.load_eval_set()[:3]
    for nombre, gens in (("resultados_baseline.jsonl", base), ("resultados_finetuned.jsonl", ft),
                         ("eval_set_baseline_results.jsonl", [_gen(r, "baseline", "No se.") for r in ev]),
                         ("eval_set_finetuned_results.jsonl",
                          [_gen(r, "fine_tuned", r["messages"][2]["content"]) for r in ev])):
        (tmp_path / nombre).write_text("\n".join(json.dumps(g.__dict__, ensure_ascii=False) for g in gens) + "\n",
                                       encoding="utf-8")
    mapa = rutas.construir_mapa(train)
    scorecard.export_csv(tmp_path / "metricas_por_registro.csv",
                         pipeline.build_eval_rows(base, mapa=mapa) + pipeline.build_eval_rows(ft, mapa=mapa))
    (tmp_path / "run_manifest.json").write_text(json.dumps({"n_val": len(val), "git_commit": "x"}))
    return tmp_path


def _groq_falso(llamadas, cupo=None):
    def fake(system, user, max_tokens):
        if cupo is not None and len(llamadas) >= cupo:
            raise external_judge.CupoAgotado("cupo diario")
        llamadas.append(user)
        if "Respuesta A" in user:
            return '{"veredicto": "B", "confianza": 4}'
        if "Criterio que debe cumplir" in user:
            return '{"veredicto": "cumple", "errores_juridicos": []}'
        return ('{"correccion_juridica": 4, "prudencia": 4, "claridad_utilidad": 4, "concision": 4, '
                '"errores_juridicos": [], "justificacion": "ok"}')
    return fake


def test_sin_groq_el_informe_dice_pendiente(corrida):
    texto = fase_groq.informe(corrida)
    assert "PENDIENTE" in texto and "Juez: pendiente" in texto
    assert "Guardia de rutas y entidades" in texto


def test_cupo_agotado_se_retoma_sin_repetir_llamadas(corrida, monkeypatch):
    llamadas = []
    monkeypatch.setattr(external_judge, "call_groq", _groq_falso(llamadas, cupo=10))
    estado = fase_groq.calificar(corrida)
    assert estado["eval_set"] == "completa"          # 6 llamadas
    assert estado["validacion"] == "pendiente"       # se corto a mitad
    assert len(llamadas) == 10

    # Al dia siguiente: retoma. Total = 6 (eval set) + 12 (rubrica) + 12 (cara a cara), sin repetir.
    monkeypatch.setattr(external_judge, "call_groq", _groq_falso(llamadas))
    estado = fase_groq.calificar(corrida)
    assert set(estado.values()) == {"completa"}
    assert len(llamadas) == 30 and len(set(llamadas)) == 30

    texto = fase_groq.informe(corrida)
    assert "PENDIENTE" not in texto
    assert "Comparación cara a cara (sesgo de posición neutralizado)" in texto
    # "B" en los dos ordenes = gana uno distinto en cada orden: inconsistente, no suma.
    cara = json.loads((corrida / "groq_cara_a_cara.json").read_text())
    assert cara["veredicto_consistente"]["inconsistente"] == 6


def test_el_informe_puede_ir_a_otra_carpeta(corrida, monkeypatch, tmp_path_factory):
    monkeypatch.setattr(external_judge, "call_groq", _groq_falso([]))
    fase_groq.calificar(corrida)
    out = tmp_path_factory.mktemp("results")
    fase_groq.informe(corrida, out)
    for nombre in ("scorecard.md", "metricas_por_registro.csv", "run_manifest.json",
                   "eval_set_resultados.jsonl", "groq_validacion.jsonl", "groq_cara_a_cara.json"):
        assert (out / nombre).exists(), nombre


def test_informe_rechaza_otro_dataset(corrida):
    (corrida / "run_manifest.json").write_text(json.dumps({"n_val": 213}))
    with pytest.raises(ValueError, match="mismo dataset"):
        fase_groq.informe(corrida)


# --- call_groq ante los limites de Groq ---------------------------------------

def _error_429(mensaje, retry_after):
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(429, headers={"retry-after": str(retry_after)}, request=req)
    return openai.RateLimitError(mensaje, response=resp, body=None)


class _Cliente:
    def __init__(self, errores):
        self.errores, self.kwargs = list(errores), None
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self.errores:
            raise self.errores.pop(0)
        msg = type("M", (), {"content": "{}"})
        return type("R", (), {"choices": [type("C", (), {"message": msg})]})


def test_limite_por_minuto_espera_y_reintenta(monkeypatch):
    cliente = _Cliente([_error_429("Rate limit reached ... tokens per minute (TPM)", 2)])
    monkeypatch.setattr(external_judge, "_get_client", lambda: cliente)
    esperas = []
    monkeypatch.setattr(external_judge.time, "sleep", esperas.append)
    assert external_judge.call_groq("s", "u", 10) == "{}"
    assert esperas == [3]
    assert cliente.kwargs["temperature"] == 0 and cliente.kwargs["seed"] == 42


def test_limite_diario_para_el_lote(monkeypatch):
    cliente = _Cliente([_error_429("Rate limit reached ... tokens per day (TPD)", 900)])
    monkeypatch.setattr(external_judge, "_get_client", lambda: cliente)
    with pytest.raises(external_judge.CupoAgotado):
        external_judge.call_groq("s", "u", 10)
