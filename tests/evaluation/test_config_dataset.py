"""Coherencia entre el dataset en disco, `config.DATASET_SHA1` y el manifiesto.

Por que existe este archivo. El 2026-10-10 el dataset paso de 2709 a 2626
registros y **el contrato heredado quedo en tres sitios a la vez**:
`config.DATASET_SHA1` seguia con la huella del anterior, el notebook afirmaba
2709 y 418 contrastivos, y el manifiesto decia que los 263 B2 a mano estaban sin
corregir cuando si lo estaban. Nada de eso lo detecto la suite: 700 pruebas en
verde y la corrida se habria detenido en la primera celda, en Colab y con la GPU
ya pagando.

Estas pruebas cierran ese hueco. Son baratas -- leen archivos, no entrenan -- y
fallan en local antes de que alguien reserve una A100.
"""
from __future__ import annotations

import json

import pytest

from tools.evaluation import config

MANIFIESTO = config.PROJECT_ROOT / "data" / "dataset_manifiesto.json"
NOTEBOOK = config.PROJECT_ROOT / "colab" / "m1_finetune.ipynb"


@pytest.fixture(scope="module")
def manifiesto() -> dict:
    if not MANIFIESTO.exists():
        pytest.skip("sin manifiesto: se regenera con python -m tools.dataset_v3")
    return json.loads(MANIFIESTO.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def registros() -> list[dict]:
    if not config.DATASET_PATH.exists():
        pytest.skip("sin dataset en disco")
    return [json.loads(l) for l in
            config.DATASET_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_el_hash_declarado_es_el_del_dataset_en_disco():
    """Es lo que comprueba `verificar_dataset` en la primera celda del notebook.
    Si falla aqui, la corrida se detiene alla."""
    real = config.huella_dataset()
    assert real == config.DATASET_SHA1, (
        f"el dataset en disco tiene huella {real} y config declara "
        f"{config.DATASET_SHA1}. Si el cambio es intencional, actualiza "
        f"DATASET_SHA1 y el historico de su comentario.")


def test_verificar_dataset_pasa_sin_argumentos():
    assert config.verificar_dataset() == config.DATASET_SHA1


def test_el_sha1_no_es_la_huella_del_manifiesto(manifiesto):
    """Las dos son 'la huella del dataset' y **no son el mismo valor**: una es
    sha1 sobre los bytes con LF y la otra sha256 sobre los registros canonicos.
    Copiar una en la otra hace fallar la corrida antes de empezar, y es un error
    facil porque los dos campos se llaman parecido."""
    assert config.DATASET_SHA1 != manifiesto["huella"]
    assert len(config.DATASET_SHA1) == 16 and len(manifiesto["huella"]) == 16


def test_la_composicion_del_manifiesto_coincide_con_el_archivo(registros, manifiesto):
    from collections import Counter

    c = manifiesto["composicion"]
    assert len(registros) == c["total"]
    assert Counter(r.get("origen") for r in registros) == Counter(c["por_origen"])
    assert sum(1 for r in registros if r.get("split") == "val") == c["val"]
    assert sum(1 for r in registros if r.get("split") == "train") == c["train"]


def test_ninguna_variante_contrastiva_cae_en_validacion(registros):
    """La variante comparte pregunta con su original. Si una cae en validacion,
    su par esta en entrenamiento y la medicion queda contaminada."""
    en_val = [r["id"] for r in registros
              if r.get("origen") == "contrastivo" and r.get("split") == "val"]
    assert not en_val, f"variantes contrastivas en validacion: {en_val[:10]}"


def test_la_validacion_no_cambio_respecto_a_la_base(registros):
    """**Los mismos 334 ids que antes de reconstruir el dataset.**

    Es lo que permite comparar con las corridas anteriores: si un solo id entra
    o sale, las cifras de M1 y M2 dejan de ser comparables y no hay forma de
    notarlo mirando el total, que seguiria siendo 334.

    Se comparan los ids, no el conteo, y contra el commit base que declara
    `dataset_v3.BASE_REV`. Son 231 de v1 y 103 de v2 -- la validacion nunca fue
    solo de v1.
    """
    import subprocess

    from tools.dataset_v3 import BASE_PATH, BASE_REV

    r = subprocess.run(["git", "show", f"{BASE_REV}:{BASE_PATH}"],
                       cwd=config.PROJECT_ROOT, capture_output=True)
    if r.returncode != 0:
        pytest.skip("sin git no se puede leer la base")
    base = [json.loads(l) for l in r.stdout.decode("utf-8").splitlines() if l.strip()]

    ahora = {x["id"] for x in registros if x.get("split") == "val"}
    antes = {x["id"] for x in base if x.get("split") == "val"}
    assert len(ahora) == 334
    assert ahora == antes, (
        f"la validacion cambio: {len(antes - ahora)} ids salieron y "
        f"{len(ahora - antes)} entraron")


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="sin notebook")
def test_el_notebook_no_afirma_una_composicion_que_ya_no_existe(registros):
    """El notebook lleva las cifras escritas en aserciones y en prosa. Cuando el
    dataset cambia y el notebook no, la corrida muere en la celda de carga.

    Se buscan las cifras de la composicion ANTERIOR. No se valida que el
    notebook diga las nuevas -- eso es prosa y cambia de forma -- sino que no
    siga afirmando las viejas.

    **Solo se miran las celdas de codigo y markdown, no las salidas.** Una
    salida guardada de una corrida anterior contiene 2709 con toda razon: es el
    registro de lo que paso entonces. El contrato esta en el codigo.
    """
    from collections import Counter

    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    texto = "".join("".join(c["source"]) for c in nb["cells"])
    origenes = Counter(r.get("origen") for r in registros)
    obsoletas = {
        "2709": len(registros),
        "418": origenes["contrastivo"],
        "2375": sum(1 for r in registros if r.get("split") == "train"),
    }
    encontradas = [f"{viejo} (ahora {nuevo})"
                   for viejo, nuevo in obsoletas.items()
                   if viejo != str(nuevo) and viejo in texto]
    assert not encontradas, (
        "el notebook todavia afirma cifras del dataset anterior: "
        f"{encontradas}. Actualiza colab/m1_finetune.ipynb.")
