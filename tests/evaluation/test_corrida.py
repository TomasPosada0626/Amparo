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
            corrida.verificar_checkpoint(tmp_path, actual, "afinado", n_esperado=334,
                                         huella_adaptador="pesos")
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
        assert corrida.verificar_checkpoint(tmp_path, f, "afinado",
                                            huella_adaptador="pesos") == []

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


class TestIdentidadDeLosPesos:
    """El hueco que la firma de configuracion NO cierra.

    `corrida_id` identifica COMO se entreno, no QUE salio. Dos entrenamientos
    con la misma configuracion el mismo dia dan el mismo `corrida_id` y pesos
    distintos -- basta que cambie el orden de un lote o la version de una
    libreria. Sin la huella de los pesos, el segundo reusa el checkpoint
    parcial del primero.
    """

    def test_misma_etiqueta_v3_pero_otros_pesos_no_reusa(self, tmp_path):
        """**La prueba central del auditor.** Misma corrida, misma etiqueta de
        adaptador, resultados parciales guardados, y otros pesos."""
        f = _firma(adaptador="v3")
        _checkpoint(tmp_path, f, "afinado", n=120)
        corrida.registrar_adaptador(tmp_path, "afinado", "pesos_del_primero")

        with pytest.raises(SystemExit) as e:
            corrida.verificar_checkpoint(tmp_path, f, "afinado", n_esperado=334,
                                         huella_adaptador="pesos_del_segundo")
        assert "pesos_del_primero" in str(e.value)
        assert "No se borra nada" in str(e.value)

    def test_los_mismos_pesos_si_reanudan(self, tmp_path):
        f = _firma()
        _checkpoint(tmp_path, f, "afinado", n=120)
        corrida.registrar_adaptador(tmp_path, "afinado", "pesos_a")
        filas = corrida.verificar_checkpoint(tmp_path, f, "afinado", n_esperado=334,
                                             huella_adaptador="pesos_a")
        assert len(filas) == 120

    def test_evaluar_afinado_sin_huella_no_arranca(self, tmp_path):
        """Si no se exige, el fallo vuelve en cuanto alguien la olvide."""
        f = _firma()
        _checkpoint(tmp_path, f, "afinado", n=10)
        with pytest.raises(SystemExit) as e:
            corrida.verificar_checkpoint(tmp_path, f, "afinado")
        assert "exige la huella del adaptador" in str(e.value)

    def test_el_baseline_no_necesita_huella_de_adaptador(self, tmp_path):
        """El baseline es el modelo sin adaptador: no hay pesos que firmar."""
        f = _firma()
        _checkpoint(tmp_path, f, "base", n=50)
        assert len(corrida.verificar_checkpoint(tmp_path, f, "base")) == 50


class TestGuardadoSinSobrescritura:
    def test_no_sobrescribe_una_carpeta_de_adaptador_existente(self, tmp_path):
        """`dirs_exist_ok=True` sobre una ruta que solo dependia de la etiqueta
        y la fecha: una segunda corrida el mismo dia borraba el adaptador de la
        primera. Asi se perdio el del 27 de septiembre."""
        origen = tmp_path / "salida"
        origen.mkdir()
        (origen / "adapter_model.safetensors").write_bytes(b"pesos_nuevos")

        destino = tmp_path / "drive" / "adaptador-v3"
        destino.mkdir(parents=True)
        (destino / "adapter_model.safetensors").write_bytes(b"pesos_viejos")

        with pytest.raises(SystemExit) as e:
            corrida.guardar_adaptador(origen, destino)
        assert "no se sobrescribe" in str(e.value)
        # y el adaptador anterior sigue intacto
        assert (destino / "adapter_model.safetensors").read_bytes() == b"pesos_viejos"

    def test_guarda_y_devuelve_la_huella_de_los_pesos(self, tmp_path):
        origen = tmp_path / "salida"
        origen.mkdir()
        (origen / "adapter_model.safetensors").write_bytes(b"pesos")
        h = corrida.guardar_adaptador(origen, tmp_path / "drive" / "ad-v3-20261010")
        assert h == corrida.huella_directorio(tmp_path / "drive" / "ad-v3-20261010")

    def test_dos_corridas_distintas_no_colisionan(self, tmp_path):
        origen = tmp_path / "salida"
        origen.mkdir()
        (origen / "w.bin").write_bytes(b"a")
        corrida.guardar_adaptador(origen, tmp_path / "ad-v3-corridaA")
        (origen / "w.bin").write_bytes(b"b")
        h2 = corrida.guardar_adaptador(origen, tmp_path / "ad-v3-corridaB")
        assert corrida.huella_directorio(tmp_path / "ad-v3-corridaA") != h2


class TestRevisionObligatoria:
    def test_una_revision_sin_resolver_detiene_la_corrida(self):
        """`main` puede cambiar sin que cambie la firma: dos corridas con el
        mismo `corrida_id` tendrian pesos base distintos."""
        with pytest.raises(SystemExit) as e:
            corrida.exigir_revision(None)
        assert "no es reproducible" in str(e.value) or "reproducible" in str(e.value)
        with pytest.raises(SystemExit):
            corrida.exigir_revision("")

    def test_una_revision_resuelta_pasa(self):
        assert corrida.exigir_revision("abc123") == "abc123"

    def test_un_checkpoint_sin_revision_no_se_reusa(self, tmp_path):
        """Aunque alguien haya corrido con EXIGIR_REVISION = False, lo que
        quedo no sirve para reanudar: no hay forma de saber si los pesos base
        son los mismos."""
        f = _firma(revision_base=None)
        _checkpoint(tmp_path, f, "base", n=40)
        with pytest.raises(SystemExit) as e:
            corrida.verificar_checkpoint(tmp_path, f, "base")
        assert "revision inmutable" in str(e.value)
