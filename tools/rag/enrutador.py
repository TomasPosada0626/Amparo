"""Enrutador por categoria: antes de buscar, decide en que normas buscar.

Hallazgo que lo motiva (corrida de S08 del 2026-10-07, 45 casos gold): con 36
normas y unos 12 000 chunks, la busqueda trae articulos de la norma equivocada.
Una pregunta de salud recupera articulos del CST y del CPACA; una de cheques,
articulos de la Constitucion. El coseno de e5 entre una pregunta coloquial y
cualquier articulo cae en una franja estrecha (0.82-0.86), asi que el ranking
entre normas es casi ruido.

La pregunta, en cambio, si dice de que tema es, y para eso hay 1 536 ejemplos
etiquetados: el dataset de M1 (data/dataset_legal.jsonl) trae la categoria de
cada pregunta. Un clasificador lineal (TF-IDF de palabras y de trigramas a
pentagramas de caracteres + regresion logistica) aprende a ponerle categoria a
una pregunta nueva, y cada categoria tiene sus normas declaradas en
corpus.NORMAS_EN_ALCANCE. La busqueda se hace igual que antes, pero los
candidatos de las normas de las categorias probables suben al frente; los demas
quedan detras, no se borran (si el enrutador se equivoca, la busqueda sigue
teniendo de donde sacar).

Medido sobre los 45 gold con articulos etiquetados (data/eval_set_articulos.json),
con BM25 (lo unico que corre sin descargar modelos): acierto en el top-5 de 10/45
a 17/45. El efecto sobre e5 se mide en Colab con tools/rag/benchmark_busqueda.py.

Por que un clasificador y no pedirle la categoria al LLM: corre en milisegundos
en CPU, sin GPU ni red, y se entrena en 2 segundos al cargar el indice. Las
preguntas del eval set no estan en el dataset de M1 (tools/evaluation/eval_set.py
lo verifica), asi que medirlo sobre el eval set no es medir sobre el train.
"""
from __future__ import annotations

import json
from functools import lru_cache

from tools.evaluation import config as eval_config
from tools.rag import corpus

# El dataset unico. Los ejemplos sin contexto (origen v1) traen la categoria de
# cada pregunta, que es lo que entrena el clasificador.
DATASET_PATH = eval_config.DATASET_PATH

# Cuantas categorias tematicas se toman de la prediccion. Con 2 entran las
# confusiones esperables (Despido / Relaciones laborales, Derecho administrativo
# / Acceso a informacion) sin abrir tanto que el filtro deje de filtrar.
CATEGORIAS_POR_CONSULTA = 2


def _normalizar(texto: str) -> str:
    from tools.rag.hybrid import _sin_tildes

    return _sin_tildes((texto or "").lower())


class Enrutador:
    def __init__(self, modelo, normas_de: dict[str, set[str]], transversales: set[str]):
        self._modelo = modelo
        self.normas_de = normas_de
        self.transversales = transversales

    @classmethod
    def entrenar(cls, registros: list[dict] | None = None) -> "Enrutador":
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline, make_union

        if registros is None:
            # SOLO los ejemplos sin contexto. En servicio el enrutador recibe la
            # consulta sola, asi que entrenarlo con otra cosa es un desajuste
            # entre entrenamiento y uso.
            #
            # Importa porque messages[1] de un ejemplo con contexto NO es la
            # pregunta: es el bloque CONTEXTO con hasta 5 fragmentos de norma y
            # la pregunta al final, miles de caracteres. Al unificar el dataset
            # el 2026-10-10 esto quedo leyendo los 2709 sin filtrar y el
            # clasificador se habria entrenado con 1173 entradas que nunca ve.
            from tools.evaluation import dataset as _dataset

            registros = _dataset.load_records(DATASET_PATH, origen="v1")
        preguntas = [_normalizar(r["messages"][1]["content"]) for r in registros]
        categorias = [r["category"] for r in registros]
        modelo = make_pipeline(
            make_union(
                TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
                TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True),
            ),
            LogisticRegression(C=10, max_iter=3000),
        ).fit(preguntas, categorias)

        normas_de: dict[str, set[str]] = {}
        transversales: set[str] = set()
        for norma in corpus.NORMAS_EN_ALCANCE:
            doc_id = norma.filename.rsplit(".", 1)[0]
            for categoria in norma.categorias:
                if categoria == corpus.TRANSVERSAL:
                    transversales.add(doc_id)
                else:
                    normas_de.setdefault(categoria, set()).add(doc_id)
        return cls(modelo, normas_de, transversales)

    def probabilidades(self, consulta: str) -> list[tuple[str, float]]:
        p = self._modelo.predict_proba([_normalizar(consulta)])[0]
        orden = sorted(zip(self._modelo.classes_, p), key=lambda x: -x[1])
        return [(str(c), float(v)) for c, v in orden]

    def categorias(self, consulta: str) -> list[str]:
        """Las categorias tematicas probables, o [] si la pregunta parece de
        otro tipo (fuera del derecho colombiano, pedir una garantia...): esas
        no tienen normas propias y no se filtra."""
        orden = self.probabilidades(consulta)
        if orden[0][0] not in self.normas_de:
            return []
        return [c for c, _ in orden if c in self.normas_de][:CATEGORIAS_POR_CONSULTA]

    def normas(self, consulta: str) -> set[str] | None:
        """doc_ids donde buscar primero, o None si no se filtra."""
        cats = self.categorias(consulta)
        if not cats:
            return None
        permitidas = set(self.transversales)
        for c in cats:
            permitidas |= self.normas_de[c]
        return permitidas


def priorizar(resultados: list, permitidas: set[str] | None) -> list:
    """Los resultados de las normas permitidas primero, en su orden; despues el
    resto, tambien en su orden. Con permitidas=None no cambia nada."""
    if permitidas is None:
        return list(resultados)
    dentro = [r for r in resultados if r.doc_id in permitidas]
    fuera = [r for r in resultados if r.doc_id not in permitidas]
    return dentro + fuera


@lru_cache(maxsize=1)
def enrutador_por_defecto() -> Enrutador:
    return Enrutador.entrenar()
