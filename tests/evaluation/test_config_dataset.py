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


# --- Contratos del notebook que no se ven ejecutando la suite ----------------
#
# Son comprobaciones estaticas sobre el .ipynb. Feas, pero el notebook no se
# importa y estos dos fallos solo aparecerian en Colab, con la GPU ya pagando.

def _codigo_del_notebook() -> str:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return "".join("".join(c["source"]) for c in nb["cells"])


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="sin notebook")
def test_la_revision_resuelta_se_usa_en_las_dos_cargas():
    """`REVISION_BASE` se resolvia y solo se imprimia: el notebook anotaba una
    revision y `from_pretrained` bajaba la que apuntara main, que puede ser
    otra. Las dos cargas tienen que recibirla."""
    codigo = _codigo_del_notebook()
    assert "AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION_BASE)" in codigo
    assert "revision=REVISION_BASE," in codigo
    # y no puede quedar como el texto de un error
    assert "REVISION_BASE = f'no se pudo resolver" not in codigo
    assert "REVISION_BASE = None" in codigo


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="sin notebook")
def test_los_resultados_van_a_un_directorio_por_corrida():
    """Todas las corridas escribian en `{DRIVE_DIR}/evaluacion` y la siguiente
    reusaba los resultados de la anterior."""
    codigo = _codigo_del_notebook()
    assert "SALIDA_DIR = f'{EVAL_ROOT}/{CORRIDA_ID}'" in codigo
    assert "SALIDA_DIR = f'{DRIVE_DIR}/evaluacion'" not in codigo
    assert "_corrida.verificar_checkpoint(" in codigo
    assert "_corrida.escribir(SALIDA_DIR, FIRMA)" in codigo


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="sin notebook")
def test_los_nombres_de_salida_no_implican_v2_ni_pisan_una_corrida_previa():
    codigo = _codigo_del_notebook()
    for viejo in ("historial_entrenamiento_v2.json", "hiperparametros_v2.json",
                  "data/dataset_v2.jsonl"):
        assert viejo not in codigo, f"el notebook todavia escribe {viejo}"
    # el adaptador de produccion no se sobrescribe
    assert "assert ADAPTADOR != 'v1'" in codigo


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="sin notebook")
def test_el_manifiesto_registra_la_identidad_de_la_corrida():
    codigo = _codigo_del_notebook()
    for campo in ('"corrida_id": CORRIDA_ID', '"revision_base": REVISION_BASE',
                  '"revision_verificada": FIRMA["revision_verificada"]',
                  '"huella_dataset": FIRMA["huella_dataset"]'):
        assert campo in codigo, f"el manifiesto no registra {campo}"


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="sin notebook")
def test_el_adaptador_se_guarda_por_corrida_y_sin_sobrescribir():
    """`dirs_exist_ok=True` sobre una ruta que solo dependia de la etiqueta y
    la fecha: una segunda corrida el mismo dia borraba el adaptador de la
    primera."""
    codigo = _codigo_del_notebook()
    assert "shutil.copytree(" not in codigo, "vuelve a copiar a mano"
    assert "_corrida.guardar_adaptador(" in codigo
    assert "ADAPTER_DIR = f'{ADAPTADOR_ROOT}/amparo-lora-adapter-{ADAPTADOR}-{CORRIDA_ID}'" in codigo
    assert "ADAPTER_DIR_VERSIONADO" not in codigo


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="sin notebook")
def test_los_resultados_afinados_se_atan_a_los_pesos():
    """El corrida_id identifica COMO se entreno, no QUE salio."""
    codigo = _codigo_del_notebook()
    assert "_corrida.registrar_adaptador(SALIDA_DIR, 'afinado', HUELLA_ADAPTADOR)" in codigo
    assert "huella_adaptador=HUELLA_ADAPTADOR if estado == 'afinado' else None" in codigo
    assert '"huella_adaptador": HUELLA_ADAPTADOR' in codigo


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="sin notebook")
def test_una_revision_sin_resolver_detiene_antes_de_cargar_el_modelo():
    """Bajar 15 GB para descubrir despues que la corrida no sirve es tiempo de
    GPU tirado, asi que la comprobacion va antes de `from_pretrained`."""
    codigo = _codigo_del_notebook()
    assert "_corrida.exigir_revision(REVISION_BASE)" in codigo
    assert codigo.index("_corrida.exigir_revision(") < codigo.index("AutoTokenizer.from_pretrained")
