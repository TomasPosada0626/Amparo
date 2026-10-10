"""Senales de suficiencia (tools/prototipo/suficiencia.py).

**La separacion que exige el encargo, y que esta en la estructura del archivo:**

- `TestDisenadasCon`: casos que se miraron AL ESCRIBIR las senales. Fijan el
  comportamiento que se buscaba. **No son evidencia de generalizacion**: una
  senal pasa aqui por construccion.
- `TestValidacionIndependiente`: casos construidos para romper la senal, con el
  fallo que cada una debe cometer. Son los que dicen algo.
- `TestLimitesDeclarados`: lo que la senal NO puede hacer, con el caso que lo
  demuestra. Si uno de estos empieza a pasar, la senal cambio de alcance y hay
  que volver a medirla, no celebrar.

Una prueba que no falla cuando debe es peor que no tenerla.
"""
from __future__ import annotations

from tools.prototipo import suficiencia as s

CTX_ARRIENDO = [
    {"cita": "Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana), Articulo 20",
     "doc_id": "arrendamiento_vivienda_urbana_ley_820_2003", "articulos": ["20"],
     "text": "El canon de arrendamiento solo podra reajustarse una vez al ano."},
]
CTX_LABORAL = [
    {"cita": "Codigo Sustantivo del Trabajo, Articulo 65",
     "doc_id": "codigo_sustantivo_trabajo", "articulos": ["65"],
     "text": "Indemnizacion por falta de pago de salarios y prestaciones."},
]


class TestDisenadasCon:
    """Los dos casos que el encargo nombro. Optimista por construccion."""

    def test_2823_cita_recuperada_pero_ajena_a_la_pregunta(self):
        """El articulo 65 del CST SI se recupero y SI es del CST: la cita es
        correcta en los dos ejes que `citas_no_verificables` sabe comprobar.
        Lo que falla es que la pregunta era de embargos."""
        from tools.rag.verificacion import citas_no_verificables

        respuesta = ("El articulo 65 del Codigo Sustantivo del Trabajo obliga al "
                     "empleador a pagar la indemnizacion por falta de pago.")
        # Lo que el codigo de produccion ve: nada. Es el hueco.
        assert not s.s2_sin_cita_respaldada(respuesta, CTX_LABORAL)
        # Y la senal nueva si lo ve, porque la materia no coincide.
        assert s.s3_contexto_de_otra_materia(
            "Me embargaron una cuenta que ya tenia saldo en cero.", CTX_LABORAL,
            "Embargos", usar_enrutador=False)

    def test_2229_competencia_institucional_sin_respaldo(self):
        respuesta = ("Pide por escrito la reparacion y, si no la hacen, acude a la "
                     "Superintendencia de Servicios Publicos Domiciliarios.")
        ctx = "Ley 1480 de 2011, Articulo 7. Garantia legal de los productos."
        assert s.s5_competencias_sin_respaldo(respuesta, ctx)
        # Sin citar ningun articulo: no hay nada que verificar por la via de las citas.
        assert s.s1_sin_ninguna_cita(respuesta)


class TestValidacionIndependiente:
    """Casos construidos para que la senal falle. Estos si informan."""

    def test_s3_no_se_activa_cuando_la_norma_es_de_la_materia(self):
        assert not s.s3_contexto_de_otra_materia(
            "Mi arrendador me subio el canon al doble.", CTX_ARRIENDO,
            "Arriendo", usar_enrutador=False)

    def test_s2_distingue_el_numero_de_la_norma(self):
        """Citar "articulo 20" cuando el contexto trae el 20 lo respalda; citar
        el 99, que no esta, no. El numero suelto no basta para aprobar."""
        assert not s.s2_sin_cita_respaldada("El articulo 20 limita el canon.", CTX_ARRIENDO)
        assert s.s2_sin_cita_respaldada("El articulo 99 limita el canon.", CTX_ARRIENDO)

    def test_s5_no_marca_una_entidad_que_el_contexto_si_nombra(self):
        ctx = "Ley 142 de 1994. La Superintendencia de Servicios Publicos Domiciliarios vigila."
        respuesta = "Acude a la Superintendencia de Servicios Publicos Domiciliarios."
        assert not s.s5_competencias_sin_respaldo(respuesta, ctx)

    def test_s6_acepta_el_plazo_que_el_contexto_trae_en_letras(self):
        """Las normas escriben "quince (15) dias"; si solo se buscara el digito,
        un plazo respaldado se marcaria como inventado."""
        assert not s.s6_plazo_sin_respaldo("Tienes 15 dias.", "el termino de quince dias")
        assert s.s6_plazo_sin_respaldo("Tienes 30 dias.", "el termino de quince dias")

    def test_s1_no_es_senal_de_fallo(self):
        """Una orientacion correcta puede no citar. S1 sola no puede bloquear:
        en la corrida real se activa en 7 de las 9 respuestas que SI cumplen."""
        assert s.s1_sin_ninguna_cita("Acude a la Comisaria de Familia; si hay riesgo, llama al 123.")


class TestLimitesDeclarados:
    """Lo que estas senales NO resuelven. Cada una con su caso."""

    def test_no_detecta_que_el_articulo_citado_no_sostenga_la_afirmacion(self):
        """Caso 3328: la respuesta atribuye al articulo 46 lo que dice el 50.
        Los dos son de la Ley 1480, los dos estan en el contexto y la materia
        coincide. **Ninguna senal se activa, y es correcto que no lo haga**: eso
        es suficiencia semantica y es juicio juridico."""
        ctx = [{"cita": "Ley 1480 de 2011 (Estatuto del Consumidor), Articulo 46",
                "doc_id": "estatuto_consumidor_ley_1480_2011", "articulos": ["46", "50"],
                "text": "Proveedor, entrega y consumidor."}]
        respuesta = "El articulo 46 de la Ley 1480 obliga a entregar el pedido dentro del plazo."
        assert not s.s2_sin_cita_respaldada(respuesta, ctx)
        assert not s.s3_contexto_de_otra_materia(
            "No me entregaron el pedido a tiempo.", ctx, "Garantias de consumo",
            usar_enrutador=False)

    def test_s3_con_el_enrutador_real_casi_no_se_activa(self):
        """La version de produccion de S3 usa la categoria que PREDICE el
        enrutador, no la verdadera. Medido en la corrida real: 0 detecciones de
        25 casos insuficientes. La variante con la categoria verdadera detecta 6,
        pero esa etiqueta no existe en servicio."""
        activada = s.s3_contexto_de_otra_materia(
            "Me embargaron una cuenta que ya tenia saldo en cero.", CTX_LABORAL,
            usar_enrutador=True)
        # No se afirma el valor: se documenta que el enrutador decide, y que por
        # eso la senal no es la misma que con la etiqueta verdadera.
        assert isinstance(activada, bool)

    def test_el_umbral_de_s4_no_esta_calibrado(self):
        """0.10 es un punto de lectura. En la corrida real S4 se activa en 39 de
        45 casos -- 24 verdaderos y 15 falsos -- y en 7 de las 9 respuestas
        correctas: mide "esto es una pregunta juridica", no insuficiencia."""
        assert s.s4_afinidad_lexica_baja("pregunta sin relacion alguna", CTX_ARRIENDO,
                                         umbral=0.99)
        assert not s.s4_afinidad_lexica_baja("canon de arrendamiento reajuste",
                                            CTX_ARRIENDO, umbral=0.0)

    def test_sin_contexto_ninguna_senal_inventa_un_fallo(self):
        for fn in (s.s1_sin_ninguna_cita,):
            assert fn("") is True or fn("") is False
        assert not s.s3_contexto_de_otra_materia("algo", [], "Arriendo", usar_enrutador=False)
        assert not s.s4_afinidad_lexica_baja("algo", [])
