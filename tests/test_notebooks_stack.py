"""H9: todos los notebooks de Colab instalan versiones fijadas."""
from __future__ import annotations

import json

import pytest

from tools.evaluation import config

COLAB = config.PROJECT_ROOT / "colab"
NOTEBOOKS = sorted(COLAB.glob("*.ipynb"))
REQUISITOS = {"m1": COLAB / "requirements-m1.txt", "m2": COLAB / "requirements-m2.txt",
              "m3": COLAB / "requirements-m3.txt"}


def _instalaciones(nb_path):
    nb = json.loads(nb_path.read_bytes().decode("utf-8"))
    return [l.strip() for c in nb["cells"] for l in "".join(c["source"]).splitlines()
            if l.strip().startswith(("!", "%")) and "pip install" in l]


@pytest.mark.parametrize("nb_path", NOTEBOOKS, ids=lambda p: p.stem)
def test_ningun_notebook_instala_sin_version(nb_path):
    for l in _instalaciones(nb_path):
        assert " -U" not in l and "--upgrade" not in l, f"{nb_path.name}: {l}"
        # o un archivo de requisitos, o nada suelto sin version
        if " -r " not in l:
            paquetes = [x for x in l.split()[3:] if not x.startswith("-")]
            assert all("==" in p for p in paquetes), f"{nb_path.name}: {l}"


@pytest.mark.parametrize("nb_path", NOTEBOOKS, ids=lambda p: p.stem)
def test_cada_notebook_usa_el_stack_de_su_modulo(nb_path):
    modulo = nb_path.stem.split("_")[0]
    archivo = REQUISITOS[modulo].name
    assert any(archivo in l for l in _instalaciones(nb_path)), f"{nb_path.name} no instala {archivo}"


@pytest.mark.parametrize("modulo", sorted(REQUISITOS))
def test_cada_paquete_lleva_version_exacta_y_torch_no(modulo):
    lineas = [l.strip() for l in REQUISITOS[modulo].read_text(encoding="utf-8").splitlines()
              if l.strip() and not l.lstrip().startswith("#")]
    assert lineas
    for l in lineas:
        assert "==" in l, f"{modulo}: {l} sin version exacta"
    assert "torch" not in {l.split("==")[0] for l in lineas}


def test_los_modulos_comparten_las_versiones_del_stack_comun():
    """transformers, peft, accelerate y bitsandbytes generan en M1, M2 y M3: si
    difieren, las cifras de un modulo no se comparan con las de otro."""
    def versiones(m):
        return dict(l.strip().split("==") for l in REQUISITOS[m].read_text(encoding="utf-8").splitlines()
                    if "==" in l and not l.lstrip().startswith("#"))
    v = {m: versiones(m) for m in REQUISITOS}
    for p in ("transformers", "peft", "accelerate", "bitsandbytes"):
        assert len({v[m][p] for m in v}) == 1, (p, {m: v[m][p] for m in v})


def test_m2_verifica_el_adaptador_antes_de_generar():
    """El adaptador de Drive se sobrescribio una vez y las cifras quedaron
    atribuidas a otro. M2 comprueba la huella antes de la primera generacion y
    el manifiesto firma el adaptador que se evaluo, no siempre la ruta de v1."""
    nb = json.loads((COLAB / "m2_evaluacion.ipynb").read_bytes().decode("utf-8"))
    codigo = "".join("".join(c["source"]) for c in nb["cells"])
    assert codigo.index("HUELLA_ADAPTADOR_ESPERADA") < codigo.index("generation.load_base_model()")
    assert "generation.attach_adapter(model, ADAPTADOR_DIR)" in codigo
    assert "build_manifest(n_val=len(val_records), adapter_dir=ADAPTADOR_DIR" in codigo
    assert "attach_adapter(model, config.DRIVE_ADAPTER_DIR)" not in codigo


@pytest.mark.parametrize("nombre", ["m1_finetune", "m3_s08_rag_avanzado", "m3_s10_rag_agentico"])
def test_el_indice_se_verifica_antes_de_medir(nombre):
    """El indice no esta en git: se copia de Drive. Con otro indice las cifras no
    se comparan con las anteriores, asi que se verifica por huella antes de usarlo."""
    nb = json.loads((COLAB / f"{nombre}.ipynb").read_bytes().decode("utf-8"))
    codigo = "".join("".join(c["source"]) for c in nb["cells"])
    assert "_verificar_indice(" in codigo
    assert codigo.index("_verificar_indice(") < codigo.index("load_index()" if "load_index()" in codigo
                                                             else "_c6.correr(")
