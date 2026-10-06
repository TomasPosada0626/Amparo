"""El notebook de M1 no debe llevar copias de las metricas: debe importarlas.

Historia de por que existe este test. El catalogo de rutas legales vivia
copiado dentro del notebook, porque M1 leia el dataset de Drive y no tenia el
repo disponible para importar nada. Esa copia se desincronizo con consecuencias
reales: la version del notebook estaba recortada (le faltaban "Secretaria de
Transito", "apelar", SIMIT, Colpensiones...) y marcaba como "no nombra ruta
legal" respuestas que si la nombraban, subestimando al modelo. El fallo era
silencioso: el notebook corria sin errores y producia una cifra creible y
equivocada. Lo mismo paso con la definicion de "cita inventada", que llego a
tener tres versiones distintas entre M1, las puertas del dataset y M2.

La solucion de fondo fue quitar la causa, no vigilar el sintoma: el notebook
clona el repo e importa cada metrica de tools/. Por eso este test ya no compara
dos copias -- comprueba que no haya una segunda copia que comparar.
"""
from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK = Path(__file__).resolve().parents[1] / "colab" / "m1_finetune.ipynb"


def _codigo() -> str:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"
    )


def test_el_notebook_clona_el_repo():
    """Sin el clone no puede importar tools/, y volveria a necesitar copias."""
    codigo = _codigo()
    assert "git clone" in codigo and "Amparo.git" in codigo, (
        "el notebook ya no clona el repo: sin eso no puede importar las metricas "
        "y habria que volver a copiarlas dentro, que es el bug que esto evita"
    )


def test_el_notebook_importa_las_metricas_del_repo():
    codigo = _codigo()
    for importacion in (
        "from tools.dataset_quality import menciona_mecanismo",
        "from tools.evaluation.domain_metric import has_invented_citation",
        "from tools.evaluation.entity_metric import find_fabricated_entities",
    ):
        assert importacion in codigo, f"el notebook ya no importa: {importacion}"


def test_el_notebook_no_redefine_las_metricas_que_ya_importa():
    """Una definicion propia dentro del notebook es la segunda copia que se
    desincroniza. Si alguna vuelve a aparecer, este test lo dice."""
    codigo = _codigo()
    for copia in (
        "MECANISMO = re.compile",
        "CITA_NO_VERIFICABLE = re.compile",
        "MECANISMOS = {",
        "CITATION_PATTERNS = {",
        "ENTIDADES_REALES = ",
    ):
        assert copia not in codigo, (
            f"el notebook volvio a definir una metrica por su cuenta ({copia!r}). "
            "Importala de tools/ en vez de copiarla: las dos copias se "
            "desincronizan y producen cifras creibles y equivocadas."
        )


def test_la_metrica_de_ruta_ignora_mayusculas():
    """"Secretaria de Transito" es un nombre propio y se escribe con mayuscula.

    Cuando la puerta comparaba con mayusculas significativas y el notebook no,
    la misma respuesta nombraba una ruta para M1 y no para la puerta: la misma
    propiedad con dos cifras. Ahora hay una sola funcion, y esta es la propiedad
    que tiene que cumplir.
    """
    from tools.dataset_quality import menciona_mecanismo

    for texto in ("acude a la Secretaria de Transito",
                  "acude a la Secretaría de Tránsito",
                  "ACUDE A LA SECRETARIA DE TRANSITO"):
        assert menciona_mecanismo(texto), f"la puerta no reconoce la ruta en {texto!r}"
    for texto in ("revisa el contrato con calma", "reune toda la evidencia disponible"):
        assert not menciona_mecanismo(texto), (
            f"cuenta como ruta un consejo generico sin destino: {texto!r}"
        )


def test_el_notebook_no_vuelve_a_la_similitud_lexica():
    """difflib daba 3.2 contra 6.0 sobre 100 y no distingue una respuesta
    correcta de una incorrecta. La comparacion contra la referencia la hace M2
    con BLEU/ROUGE/BERTScore sobre el mismo split; duplicarla aqui era otra
    cifra de la misma propiedad."""
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for celda in nb["cells"]:
        if celda["cell_type"] != "code":
            continue
        for linea in "".join(celda["source"]).splitlines():
            if linea.lstrip().startswith("#"):
                continue  # los comentarios explican por que se quito
            assert "difflib" not in linea and "similarity_pct" not in linea, (
                f"volvio la similitud lexica al notebook: {linea.strip()!r}"
            )


def test_la_evaluacion_persiste_cada_ejemplo_y_valida_el_checkpoint():
    """Con 900 tokens la evaluacion toma horas; sin escritura incremental una
    desconexion de Colab borra la corrida. Y el resume necesita sus guardas: en
    Drive quedan checkpoints de corridas anteriores."""
    codigo = _codigo()
    assert "def evaluate(model, val_set, label: str, checkpoint: str)" in codigo
    assert "'a', encoding='utf-8'" in codigo, "la evaluacion ya no hace append incremental"
    for guarda in ("es de otra corrida", "ids distintos a los esperados",
                   "es de un esquema anterior"):
        assert guarda in codigo, f"falta la guarda del checkpoint: {guarda!r}"


def test_la_perdida_cae_solo_sobre_la_respuesta():
    """El 68% del gradiente se gastaba en tokens que el modelo nunca debe
    generar, y el 60% era un system prompt identico en los 1536 ejemplos."""
    codigo = _codigo()
    assert "def a_prompt_completion" in codigo, (
        "el entrenamiento ya no usa formato prompt/completion: sin eso la perdida "
        "vuelve a incluir el system prompt y la pregunta"
    )
    # Solo lineas de codigo: los comentarios mencionan dataset_text_field
    # justamente para explicar por que ya no se usa.
    efectivo = [l for l in codigo.splitlines() if not l.lstrip().startswith("#")]
    assert not any("dataset_text_field" in l for l in efectivo), (
        "volvio dataset_text_field: eso entrena sobre el texto completo"
    )
    assert "_ignorados > _aprendidos" in codigo, (
        "falta la verificacion del enmascarado, que es lo unico que delata que "
        "TRL no reconocio el formato (el notebook corre igual, sin un solo error)"
    )


def test_el_checkpoint_se_elige_con_un_dev_que_no_es_la_validacion():
    codigo = _codigo()
    assert "DEV_FRACTION" in codigo and "dev_records" in codigo
    assert "eval_dataset=dev_dataset" in codigo, (
        "el trainer no evalua contra el dev: sin eso no hay forma de ver "
        "sobreajuste ni de justificar el numero de epocas"
    )
    assert "load_best_model_at_end=True" in codigo
    assert "eval_dataset=val" not in codigo, (
        "la validacion de 231 no puede usarse para elegir el checkpoint: si se "
        "elige mirandola, deja de ser held-out y el reporte queda contaminado"
    )
