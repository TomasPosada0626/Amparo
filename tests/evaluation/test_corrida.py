"""Identidad de corrida (tools/evaluation/corrida.py).

La prueba que da sentido al modulo es
`test_mismos_334_ids_pero_otro_adaptador_se_rechaza`: el checkpoint tiene los
mismos identificadores y el mismo esquema que esta corrida, pasa todas las
guardas que habia antes, y **viene de otro adaptador**. Si eso se reusa, la
comparacion baseline/afinado sale de dos modelos distintos y produce un numero
creible y falso.
"""
from __future__ import annotations

import json

import pytest

from tools.evaluation import corrida


def _firma(**cambios) -> dict:
    """Una firma de prueba. `commit` se fija despues de construirla porque
    `firma()` lo resuelve de git, y una prueba no puede depender del HEAD."""
    commit = cambios.pop("commit", "30de724")
    base = dict(huella_dataset="37e579ad0bfac6bd", model_id="Qwen/Qwen2.5-7B-Instruct",
                adaptador="v3", revision_base="abc123", hoy="2026-10-10")
    base.update(cambios)
    f = corrida.firma(**base)
    f["commit"] = commit
    return f


def _checkpoint(tmp_path, f: dict, estado: str, n: int = 334):
    """Un directorio de resultados con su firma y `n` respuestas."""
    corrida.escribir(tmp_path, f)
    ruta = tmp_path / f"{estado}_results.jsonl"
    with ruta.open("w", encoding="utf-8", newline="\n") as fh:
        for i in range(n):
            fh.write(json.dumps({"id": 9000 + i, "generated": "x"}) + "\n")
    return ruta


class TestIdentidad:
    def test_la_misma_configuracion_el_mismo_dia_da_el_mismo_id(self):
        """Es lo que permite reanudar cuando Colab se desconecta."""
        assert _firma()["corrida_id"] == _firma()["corrida_id"]

    @pytest.mark.parametrize("campo,valor", [
        ("huella_dataset", "otrohash00000000"),
        ("model_id", "Qwen/Qwen2.5-14B-Instruct"),
        ("adaptador", "v4"),
        ("revision_base", "def456"),
    ])
    def test_cualquier_cambio_de_identidad_da_otro_id(self, campo, valor):
        assert _firma()["corrida_id"] != _firma(**{campo: valor})["corrida_id"]

    def test_una_revision_sin_resolver_no_se_presenta_como_verificada(self):
        """Si `model_info` falla, el notebook tenia `REVISION_BASE` con el texto
        del error, y ese texto habria entrado al manifiesto como si fuera una
        revision. Aqui queda `None` y marcado."""
        f = _firma(revision_base=None)
        assert f["revision_base"] is None
        assert f["revision_verificada"] is False
        assert "NO RESUELTA" in corrida.resumen(f)

    def test_una_revision_resuelta_si_se_marca(self):
        f = _firma(revision_base="abc123")
        assert f["revision_verificada"] is True


class TestRechazoDeCheckpointsAjenos:
    """Lo que el modulo existe para impedir."""

    def test_mismos_334_ids_pero_otro_adaptador_se_rechaza(self, tmp_path):
        """**La prueba central.** Mismos ids, mismo esquema, otro adaptador."""
        ajena = _firma(adaptador="v2")
        _checkpoint(tmp_path, ajena, "afinado", n=334)

        actual = _firma(adaptador="v3")
        with pytest.raises(SystemExit) as e:
            corrida.verificar_checkpoint(tmp_path, actual, "afinado", n_esperado=334)
        assert "adaptador" in str(e.value)
        assert "No se borra nada" in str(e.value)

    def test_mismos_334_ids_pero_otro_dataset_se_rechaza(self, tmp_path):
        _checkpoint(tmp_path, _firma(huella_dataset="db0b6e65126cab25"), "base")
        with pytest.raises(SystemExit) as e:
            corrida.verificar_checkpoint(tmp_path, _firma(), "base", n_esperado=334)
        assert "huella_dataset" in str(e.value)

    def test_otro_commit_se_rechaza(self, tmp_path):
        """El codigo que calcula las metricas cambio: las cifras no son
        comparables aunque el modelo sea el mismo."""
        _checkpoint(tmp_path, _firma(commit="33cc019"), "base")
        with pytest.raises(SystemExit) as e:
            corrida.verificar_checkpoint(tmp_path, _firma(commit="30de724"), "base")
        assert "commit" in str(e.value)

    def test_otra_revision_del_modelo_base_se_rechaza(self, tmp_path):
        """El mismo repo de HF puede servir otro peso si se publico un commit."""
        _checkpoint(tmp_path, _firma(revision_base="viejo"), "base")
        with pytest.raises(SystemExit) as e:
            corrida.verificar_checkpoint(tmp_path, _firma(revision_base="nuevo"), "base")
        assert "revision_base" in str(e.value)

    def test_resultados_sin_firma_se_rechazan(self, tmp_path):
        """Un checkpoint anterior a que existiera la firma. No se sabe de donde
        salio, asi que no se reusa -- y tampoco se borra."""
        (tmp_path / "base_results.jsonl").write_text(
            json.dumps({"id": 9000}) + "\n", encoding="utf-8")
        with pytest.raises(SystemExit) as e:
            corrida.verificar_checkpoint(tmp_path, _firma(), "base")
        assert "no se sabe de que corrida" in str(e.value)

    def test_el_baseline_no_se_confunde_con_el_afinado(self, tmp_path):
        """El notebook llama a `evaluate()` dos veces con el MISMO objeto
        `model`, antes y despues de entrenar. Cada estado tiene su archivo."""
        f = _firma()
        _checkpoint(tmp_path, f, "base", n=334)
        assert len(corrida.verificar_checkpoint(tmp_path, f, "base")) == 334
        assert corrida.verificar_checkpoint(tmp_path, f, "afinado") == []

    def test_un_estado_desconocido_no_pasa_en_silencio(self, tmp_path):
        with pytest.raises(SystemExit):
            corrida.verificar_checkpoint(tmp_path, _firma(), "finetuned")


class TestReanudacion:
    def test_la_misma_corrida_si_se_reanuda(self, tmp_path):
        """El caso que hay que preservar: Colab se desconecta a mitad y se
        sigue desde donde iba."""
        f = _firma()
        _checkpoint(tmp_path, f, "base", n=120)
        assert len(corrida.verificar_checkpoint(tmp_path, f, "base", n_esperado=334)) == 120

    def test_mas_registros_que_ejemplos_se_rechaza(self, tmp_path):
        f = _firma()
        _checkpoint(tmp_path, f, "base", n=400)
        with pytest.raises(SystemExit):
            corrida.verificar_checkpoint(tmp_path, f, "base", n_esperado=334)

    def test_escribir_no_pisa_una_firma_ajena(self, tmp_path):
        """Escribir la firma de otra corrida encima convertiria resultados
        ajenos en propios sin que nada falle."""
        corrida.escribir(tmp_path, _firma(adaptador="v2"))
        with pytest.raises(SystemExit):
            corrida.escribir(tmp_path, _firma(adaptador="v3"))


class TestHuellaDirectorio:
    def test_es_estable_y_sensible_al_contenido(self, tmp_path):
        d = tmp_path / "ad"
        d.mkdir()
        (d / "a.bin").write_bytes(b"uno")
        h1 = corrida.huella_directorio(d)
        assert h1 == corrida.huella_directorio(d)
        (d / "a.bin").write_bytes(b"dos")
        assert corrida.huella_directorio(d) != h1

    def test_el_crlf_no_cambia_la_huella(self, tmp_path):
        """Un adaptador bajado en Windows no puede dar otra huella que el mismo
        bajado en Linux. Ya paso con la huella del dataset."""
        a, b = tmp_path / "a", tmp_path / "b"
        for d, salto in ((a, b"\n"), (b, b"\r\n")):
            d.mkdir()
            (d / "config.json").write_bytes(b"{}" + salto)
        assert corrida.huella_directorio(a) == corrida.huella_directorio(b)

    def test_un_directorio_que_no_existe_da_None(self, tmp_path):
        assert corrida.huella_directorio(tmp_path / "no") is None
