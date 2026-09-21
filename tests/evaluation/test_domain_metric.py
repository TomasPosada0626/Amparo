import json

from tools.evaluation import config, domain_metric


def test_generic_law_mentions_do_not_trigger():
    """Estos son los casi-aciertos reales encontrados en data/dataset_legal.jsonl:
    "decreto" como verbo, "ley"/"sentencia" genericos sin numero, y
    "constitucion de una empresa" -- ninguno debe marcarse como cita inventada."""
    texts = [
        "El juez decreto la medida cautelar de inmediato.",
        "Debes actuar dentro de la ley aplicable a tu caso.",
        "Existe una sentencia que resuelve casos similares.",
        "Debes tramitar la constitucion de la empresa ante camara de comercio.",
    ]
    for text in texts:
        assert domain_metric.citation_count(text) == 0, text


def test_numbered_citations_trigger():
    cases = [
        "Puedes revisar la Ley 1755 de 2015 sobre el tema.",
        "Aplica el Decreto 1076 de 2015 en este caso.",
        "Consulta el Articulo 86 de la Constitucion.",
        "Ver Art. 23 del codigo.",
        "La Sentencia T-760 de 2008 desarrollo este derecho.",
        "Revisa la Resolucion 3100 de 2019.",
    ]
    for text in cases:
        assert domain_metric.citation_count(text) > 0, text
        assert domain_metric.has_invented_citation(text) is True


def test_citation_report_compliance_rate():
    class Row:
        def __init__(self, id, generated):
            self.id = id
            self.generated = generated

    rows = [
        Row(1, "Puedes presentar accion de tutela."),
        Row(2, "Revisa la Ley 1755 de 2015 sobre el tema."),
        Row(3, "Presenta un derecho de peticion ante la entidad."),
    ]
    report = domain_metric.citation_report(rows)

    assert report.n_total == 3
    assert report.n_compliant == 2
    assert report.compliance_rate_pct == round(100.0 * 2 / 3, 1)
    assert report.total_flagged_citations == 1
    assert report.flagged_examples == [(2, "Ley 1755")]


def test_gold_dataset_has_zero_citations():
    """Confirma sobre el dataset real que las respuestas gold nunca citan
    normas por numero -- es la premisa que justifica esta metrica."""
    with open(config.LOCAL_DATASET_PATH, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    total_citations = sum(
        domain_metric.citation_count(r["messages"][2]["content"]) for r in records
    )
    assert total_citations == 0
