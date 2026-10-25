"""Regresiones docentes sin API ni modelos. Se carga el módulo completo.

schema/rag se sustituyen SOLO al importar; las métricas del juez son reales.
No es la suite completa del equipo ni una validación jurídica/end-to-end.
"""
import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def cargar(path):
    schema = types.ModuleType('schema')
    schema.citas = lambda value: value or []
    schema.parse_salida = json.loads
    rag = types.ModuleType('rag')
    rag._cita_de = lambda f: f.get('cita')
    rag.cubre = lambda f, cita: f.get('cita') == cita
    spec = importlib.util.spec_from_file_location('ragas_revision', path)
    modulo = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'schema': schema, 'rag': rag}):
        spec.loader.exec_module(modulo)
    return modulo


rm = cargar(ROOT / 'src/ragas_eval.py')
FRAG = {'articulo': '1', 'norma': 'fuente_de_prueba', 'texto': 'dato', 'cita': 'A'}


class Juez:
    def __init__(self, *respuestas):
        self.respuestas = iter(respuestas)
        self.llamadas = 0
        self.guardados = 0

    def _llamar(self, *args):
        self.llamadas += 1
        valor = next(self.respuestas)
        if isinstance(valor, Exception):
            raise valor
        return valor

    def guardar_cache(self):
        self.guardados += 1


class Encoder:
    def __init__(self, vectores=None):
        self.vectores = vectores
        self.llamadas = 0

    def encode(self, textos, **kwargs):
        self.llamadas += 1
        return self.vectores if self.vectores is not None else np.array([[1., 0.]] * len(textos))


class Parseo(unittest.TestCase):
    def test_json_con_texto(self):
        self.assertEqual(rm._json('Antes {"relevante": false} después'), {'relevante': False})

    def test_json_invalido_o_tipo_incorrecto(self):
        for v in (None, 1, [], {}, '', 'sin json', '{"a":', '[1, 2]'):
            with self.subTest(v=v):
                self.assertEqual(rm._json(v), {})


class Faithfulness(unittest.TestCase):
    def test_conserva_razon_por_afirmaciones(self):
        j = Juez('{"total": 2, "sostenidas": 1}', '{"total": 1, "sostenidas": 1}')
        d = {}
        self.assertAlmostEqual(rm.faithfulness_juez(j, ['a', 'b'], [[FRAG], [FRAG]], diagnostico=d), 2/3)
        self.assertEqual(d['faithfulness']['denominador'], 3)
        self.assertEqual(j.guardados, 1)

    def test_cero_es_medicion_valida(self):
        self.assertEqual(rm.faithfulness_juez(Juez('{"total": 3, "sostenidas": 0}'), ['a'], [[FRAG]]), 0.)

    def test_sin_respuesta_no_es_cero(self):
        self.assertIsNone(rm.faithfulness_juez(Juez(''), ['a'], [[FRAG]]))

    def test_rechaza_conteos_invalidos(self):
        for t, ok in [(True, True), (3, False), (1, -1), (-2, 0), (1, 2), ('2', 1), (2., 1), (0, 1), (None, 0)]:
            with self.subTest(total=t, sostenidas=ok):
                v = json.dumps({'total': t, 'sostenidas': ok})
                self.assertIsNone(rm.faithfulness_juez(Juez(v), ['a'], [[FRAG]]))

    def test_sin_afirmaciones_es_no_aplicable(self):
        d = {}
        self.assertIsNone(rm.faithfulness_juez(Juez('{"total": 0, "sostenidas": 0}'), ['a'], [[FRAG]], diagnostico=d))
        self.assertEqual(d['faithfulness']['indices_no_aplicables'], [0])
        self.assertEqual(d['faithfulness']['indices_invalidos'], [])

    def test_parcial_declara_indices_y_denominador(self):
        d = {}
        j = Juez('error', '{"total": 2, "sostenidas": 1}')
        self.assertEqual(rm.faithfulness_juez(j, ['a', 'b'], [[FRAG], [FRAG]], diagnostico=d), .5)
        self.assertEqual(d['faithfulness']['indices_validos'], [1])
        self.assertEqual(d['faithfulness']['indices_invalidos'], [0])

    def test_lote_vacio(self):
        self.assertIsNone(rm.faithfulness_juez(Juez(), [], []))

    def test_longitudes_invalidas_no_llaman_al_juez(self):
        j = Juez()
        with self.assertRaises(ValueError):
            rm.faithfulness_juez(j, ['a'], [])
        self.assertEqual(j.llamadas, 0)

    def test_excepcion_operativa_se_propaga(self):
        with self.assertRaises(TimeoutError):
            rm.faithfulness_juez(Juez(TimeoutError('prueba')), ['a'], [[FRAG]])


class Precision(unittest.TestCase):
    def test_booleano_false_es_cero(self):
        self.assertEqual(rm.context_precision_juez(Juez('{"relevante": false}'), ['q'], [[FRAG]]), 0.)

    def test_booleano_true_es_uno(self):
        self.assertEqual(rm.context_precision_juez(Juez('{"relevante": true}'), ['q'], [[FRAG]]), 1.)

    def test_no_convierte_strings_ni_numeros_a_bool(self):
        for valor in ('false', 'true', 0, 1, None, [], {}):
            with self.subTest(valor=valor):
                j = Juez(json.dumps({'relevante': valor}))
                self.assertIsNone(rm.context_precision_juez(j, ['q'], [[FRAG]]))

    def test_json_malformado_no_es_cero(self):
        self.assertIsNone(rm.context_precision_juez(Juez('error'), ['q'], [[FRAG]]))

    def test_ranking_incompleto_no_se_comprime(self):
        d = {}
        j = Juez('{"relevante": true}', '{}', '{"relevante": true}')
        self.assertIsNone(rm.context_precision_juez(j, ['q'], [[FRAG]*3], diagnostico=d))
        self.assertEqual(d['context_precision']['indices_invalidos'], [0])

    def test_average_precision_original(self):
        j = Juez(*(json.dumps({'relevante': v}) for v in (True, False, True)))
        self.assertAlmostEqual(rm.context_precision_juez(j, ['q'], [[FRAG]*3]), (1+2/3)/2)

    def test_conserva_convencion_sin_contexto(self):
        d = {}
        self.assertEqual(rm.context_precision_juez(Juez(), ['q'], [[]], diagnostico=d), 0.)
        self.assertEqual(d['context_precision']['estados_por_caso'], ['sin_contexto'])
        self.assertEqual(d['context_precision']['denominador'], 1)

    def test_media_excluye_solo_consulta_invalida(self):
        d = {}
        j = Juez('mal', '{"relevante": true}')
        self.assertEqual(rm.context_precision_juez(j, ['a', 'b', 'c'], [[FRAG], [FRAG], []], diagnostico=d), .5)
        self.assertEqual(d['context_precision']['indices_validos'], [1, 2])

    def test_lote_vacio(self):
        self.assertIsNone(rm.context_precision_juez(Juez(), [], []))

    def test_longitudes_invalidas(self):
        with self.assertRaises(ValueError):
            rm.context_precision_juez(Juez(), ['q'], [])


class Relevancia(unittest.TestCase):
    def test_similitud_original(self):
        enc = Encoder(np.array([[1., 0.], [1., 0.], [0., 1.]]))
        j = Juez('{"preguntas": ["q1", "q2"]}')
        self.assertEqual(rm.answer_relevancy(j, ['relato'], ['s'], enc), .5)

    def test_similitud_cero_valida(self):
        enc = Encoder(np.array([[1., 0.], [0., 1.]]))
        self.assertEqual(rm.answer_relevancy(Juez('{"preguntas": ["q"]}'), ['r'], ['s'], enc), 0.)

    def test_string_no_es_lista_de_preguntas(self):
        enc = Encoder()
        self.assertIsNone(rm.answer_relevancy(Juez('{"preguntas": "abc"}'), ['r'], ['s'], enc))
        self.assertEqual(enc.llamadas, 0)

    def test_lista_invalida_no_se_filtra_silenciosamente(self):
        for qs in ([], [' '], ['q', 1], ['q', None], {'q': 'v'}):
            with self.subTest(qs=qs):
                self.assertIsNone(rm.answer_relevancy(Juez(json.dumps({'preguntas': qs})), ['r'], ['s'], Encoder()))

    def test_parcial_declara_cobertura(self):
        d = {}
        j = Juez('mal', '{"preguntas": ["q"]}')
        self.assertEqual(rm.answer_relevancy(j, ['r', 'r'], ['s', 's'], Encoder(), diagnostico=d), 1.)
        self.assertEqual(d['answer_relevancy']['indices_invalidos'], [0])
        self.assertEqual(d['answer_relevancy']['denominador'], 1)

    def test_no_carga_modelo_si_juez_falla(self):
        with patch.dict(sys.modules, {'metricas': None}):
            self.assertIsNone(rm.answer_relevancy(Juez(''), ['r'], ['s']))

    def test_encoder_no_finito_se_rechaza(self):
        with self.assertRaises(ValueError):
            rm.answer_relevancy(Juez('{"preguntas": ["q"]}'), ['r'], ['s'], Encoder([[1., 0.], [float('nan'), 0.]]))

    def test_encoder_numero_incorrecto_vectores(self):
        with self.assertRaises(ValueError):
            rm.answer_relevancy(Juez('{"preguntas": ["q"]}'), ['r'], ['s'], Encoder([[1., 0.]]))

    def test_lote_vacio(self):
        self.assertIsNone(rm.answer_relevancy(Juez(), [], [], Encoder()))

    def test_longitudes_invalidas(self):
        with self.assertRaises(ValueError):
            rm.answer_relevancy(Juez(), ['r'], [], Encoder())


class Integracion(unittest.TestCase):
    def datos(self):
        return ['{"fundamento": ["A"]}'], [[FRAG]], [{'relato': 'r', 'fundamento': ['A']}]

    def test_exactas_siguen_iguales(self):
        s, c, g = self.datos()
        r = rm.evaluar('prueba', s, c, g)
        self.assertEqual(r['exactas'], {'faithfulness': 1., 'context_precision': 1., 'context_recall': 1.})
        self.assertNotIn('juez', r)
        self.assertNotIn('cobertura_juez', r)

    def test_evaluar_juez_invalido_publica_null_y_cobertura(self):
        s, c, g = self.datos()
        r = rm.evaluar('prueba', s, c, g, juez=Juez('', '', ''))
        self.assertTrue(all(v is None for v in r['juez'].values()))
        self.assertEqual(r['protocolo_juez'], rm.PROTOCOLO_JUEZ)
        self.assertIn('null', json.dumps(r, allow_nan=False))
        self.assertTrue(all(d['casos_validos'] == 0 for d in r['cobertura_juez'].values()))

    def test_evaluar_juez_valido_conserva_escala(self):
        s, c, g = self.datos()
        j = Juez('{"total": 2, "sostenidas": 1}', '{"relevante": false}', '{"preguntas": ["q"]}')
        metricas = types.ModuleType('metricas')
        metricas._encoder = lambda: Encoder()
        with patch.dict(sys.modules, {'metricas': metricas}):
            r = rm.evaluar('prueba', s, c, g, juez=j)
        self.assertEqual(r['juez'], {'faithfulness': .5, 'context_precision': 0., 'answer_relevancy': 1.})
        self.assertEqual(j.guardados, 3)

    def test_imprimir_admite_null_y_cobertura(self):
        s, c, g = self.datos()
        r = rm.evaluar('prueba', s, c, g, juez=Juez('', '', ''))
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            rm.imprimir([r])
        self.assertIn('N/D', stream.getvalue())
        self.assertIn('0/1 casos válidos', stream.getvalue())

    def test_imprimir_artefacto_previo_sin_campos_nuevos(self):
        s, c, g = self.datos()
        r = rm.evaluar('prueba', s, c, g)
        r['juez'] = {'faithfulness': .5, 'context_precision': 0., 'answer_relevancy': 1.}
        with contextlib.redirect_stdout(io.StringIO()):
            rm.imprimir([r])

    def test_no_trunca_lote(self):
        s, c, g = self.datos()
        with self.assertRaises(ValueError):
            rm.evaluar('prueba', s, c, g+g)

    def test_listas_opcionales_no_se_ignoran_si_vacias(self):
        s, c, g = self.datos()
        for kwargs in ({'relatos': []}, {'consultas': []}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                rm.evaluar('prueba', s, c, g, **kwargs)


if __name__ == '__main__':
    unittest.main()
