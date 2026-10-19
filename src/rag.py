"""
Recuperación sobre el corpus normativo.

Tres niveles, para poder medir el delta entre ellos (criterio 2 de M3):

  1. INGENUO    embeddings densos, coseno, top-k. El baseline a batir.
  2. HÍBRIDO    BM25 + denso fusionados con Reciprocal Rank Fusion.
                BM25 acierta donde el denso falla: cuando la consulta trae el
                número del artículo o un término técnico exacto ("habeas data",
                "perjuicio irremediable"). El denso acierta donde BM25 falla:
                cuando el ciudadano describe el caso sin usar ni una palabra
                del texto legal, que es el caso normal aquí.
  3. RERANKING  un cross-encoder reordena los candidatos del híbrido leyendo
                consulta y fragmento JUNTOS, no por separado.

BM25 va implementado a mano, en veinte líneas, en vez de traer una dependencia:
es el corazón del criterio y conviene que se pueda auditar.

La verdad de campo para medir recuperación sale del propio eval set: el campo
`fundamento` de cada caso dice qué artículos tenían que aparecer.
"""
from __future__ import annotations
import json, math, re, time, unicodedata
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

MODELO_DENSO = "intfloat/multilingual-e5-base"
MODELO_DENSO_ALT = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RERANKERS = [
    "jinaai/jina-reranker-v2-base-multilingual",
    "BAAI/bge-reranker-base",
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
]

MAX_CHARS = 2000      # por encima de esto el artículo se parte


# --------------------------------------------------------------------------
# Corpus y troceado
# --------------------------------------------------------------------------
def cargar_corpus(archivo: str = "corpus.json") -> list[dict]:
    return json.loads((DATA / archivo).read_text(encoding="utf-8"))["documentos"]


def trocear(docs: list[dict], max_chars: int = MAX_CHARS) -> list[dict]:
    """Un fragmento por artículo, que es la unidad de cita.

    Solo se parte lo que no cabe: el art. 48 CP, al que el Acto Legislativo 1
    de 2005 le añadió ocho incisos sobre régimen pensional. Partir por defecto
    rompería la unidad que el modelo tiene que citar.
    """
    out = []
    for d in docs:
        t = d["texto"]
        if len(t) <= max_chars:
            out.append({**d, "parte": None})
            continue
        # cortes en frontera de frase para no partir a mitad de oración
        frases, buf = re.split(r"(?<=\.)\s+", t), ""
        trozos = []
        for f in frases:
            if len(buf) + len(f) > max_chars and buf:
                trozos.append(buf.strip())
                buf = ""
            buf += f + " "
        if buf.strip():
            trozos.append(buf.strip())
        for i, tr in enumerate(trozos, 1):
            out.append({**d, "id": f"{d['id']}-p{i}", "texto": tr,
                        "parte": f"{i}/{len(trozos)}"})
    return out


def texto_indexable(c: dict) -> str:
    """Lo que se indexa incluye norma y título: el ciudadano no dice 'artículo 49'
    pero sí dice 'salud', y el título lo acerca."""
    return f"{c['norma']} {c['articulo']} {c['titulo']}. {c['texto']}"


# --------------------------------------------------------------------------
# BM25 a mano
# --------------------------------------------------------------------------
def _tok(s: str) -> list[str]:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.findall(r"[a-z0-9]+", s)


class BM25:
    """Okapi BM25. k1 controla la saturación por frecuencia; b, la normalización
    por longitud. Los valores son los habituales y no se tunearon."""

    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [_tok(d) for d in corpus]
        self.n = len(self.docs)
        self.largos = [len(d) for d in self.docs]
        self.avg = sum(self.largos) / self.n if self.n else 0.0
        self.tf = [Counter(d) for d in self.docs]
        df = Counter(t for d in self.docs for t in set(d))
        self.idf = {t: math.log(1 + (self.n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def puntuar(self, consulta: str) -> list[float]:
        q = _tok(consulta)
        out = []
        for i in range(self.n):
            s, tf, dl = 0.0, self.tf[i], self.largos[i]
            for t in q:
                if t not in tf:
                    continue
                f = tf[t]
                s += self.idf[t] * f * (self.k1 + 1) / (
                    f + self.k1 * (1 - self.b + self.b * dl / self.avg))
            out.append(s)
        return out


# --------------------------------------------------------------------------
# Índice
# --------------------------------------------------------------------------
class Indice:
    def __init__(self, chunks: list[dict], modelo: str = MODELO_DENSO, verbose: bool = True):
        self.chunks = chunks
        self.textos = [texto_indexable(c) for c in chunks]
        self.bm25 = BM25(self.textos)
        self.modelo = modelo
        self.verbose = verbose
        self._emb = None
        self._st = None
        self._rer = None

    # -- denso ------------------------------------------------------------
    def _encoder(self):
        if self._st is None:
            from sentence_transformers import SentenceTransformer
            try:
                self._st = SentenceTransformer(self.modelo)
            except Exception as ex:
                if self.verbose:
                    print(f"  {self.modelo} no disponible ({str(ex)[:60]}); uso {MODELO_DENSO_ALT}")
                self.modelo = MODELO_DENSO_ALT
                self._st = SentenceTransformer(self.modelo)
        return self._st

    def _prefijo(self, texto: str, es_consulta: bool) -> str:
        # Los modelos e5 esperan los prefijos "query:" y "passage:"; sin ellos
        # pierden buena parte de su ventaja. Otros modelos los ignoran.
        if "e5" not in self.modelo:
            return texto
        return ("query: " if es_consulta else "passage: ") + texto

    def construir(self) -> "Indice":
        st = self._encoder()
        self._emb = st.encode([self._prefijo(t, False) for t in self.textos],
                              normalize_embeddings=True, show_progress_bar=False)
        if self.verbose:
            print(f"índice listo · {len(self.chunks)} fragmentos · denso {self.modelo}")
        return self

    def _denso(self, consulta: str) -> list[float]:
        import numpy as np
        if self._emb is None:
            self.construir()
        q = self._encoder().encode([self._prefijo(consulta, True)], normalize_embeddings=True)
        return (self._emb @ q[0]).tolist()

    # -- las tres estrategias ---------------------------------------------
    @staticmethod
    def _lista(consulta) -> list[str]:
        """Normaliza a lista. Una sola consulta sigue el camino de antes, byte
        por byte, para que los numeros de corridas anteriores sigan valiendo."""
        return [consulta] if isinstance(consulta, str) else list(consulta)

    @staticmethod
    def _rrf(rankings: list[dict[int, int]], k_rrf: int, n: int) -> dict[int, float]:
        """Reciprocal Rank Fusion sobre varios rankings: suma de 1/(k+puesto).

        Fusiona por PUESTO y no por puntaje, asi que sirve igual para mezclar
        denso con BM25 (escalas incomparables) que para mezclar tres consultas
        distintas del mismo relato.
        """
        return {i: sum(1 / (k_rrf + r[i]) for r in rankings) for i in range(n)}

    def ingenuo(self, consulta, k: int = 5) -> list[dict]:
        consultas = self._lista(consulta)
        if len(consultas) == 1:
            s = self._denso(consultas[0])
            orden = sorted(range(len(s)), key=lambda i: -s[i])[:k]
            return [{**self.chunks[i], "score": s[i], "via": "denso"} for i in orden]

        # Multi-consulta: un ranking denso por consulta, fusionados con RRF.
        rankings = []
        for c in consultas:
            s = self._denso(c)
            rankings.append({i: r for r, i in enumerate(
                sorted(range(len(s)), key=lambda j: -s[j]))})
        rrf = self._rrf(rankings, 60, len(self.chunks))
        orden = sorted(rrf, key=lambda i: -rrf[i])[:k]
        return [{**self.chunks[i], "score": rrf[i], "via": "denso_multi",
                 "n_consultas": len(consultas)} for i in orden]

    def hibrido(self, consulta: str, k: int = 5, k_rrf: int = 60) -> list[dict]:
        """Reciprocal Rank Fusion: 1/(k+rango). Fusiona por POSICIÓN y no por
        puntaje, así que no hay que normalizar escalas incomparables."""
        consultas = self._lista(consulta)
        rankings, rd0, rb0 = [], None, None
        for c in consultas:
            d, b = self._denso(c), self.bm25.puntuar(c)
            rd = {i: r for r, i in enumerate(sorted(range(len(d)), key=lambda i: -d[i]))}
            rb = {i: r for r, i in enumerate(sorted(range(len(b)), key=lambda i: -b[i]))}
            rankings += [rd, rb]
            if rd0 is None:
                rd0, rb0 = rd, rb
        rrf = self._rrf(rankings, k_rrf, len(self.chunks))
        orden = sorted(rrf, key=lambda i: -rrf[i])[:k]
        via = "hibrido" if len(consultas) == 1 else "hibrido_multi"
        return [{**self.chunks[i], "score": rrf[i], "via": via,
                 "rango_denso": rd0[i], "rango_bm25": rb0[i],
                 "n_consultas": len(consultas)} for i in orden]

    def _reranker(self):
        if self._rer is None:
            from sentence_transformers import CrossEncoder
            for m in RERANKERS:
                try:
                    self._rer = CrossEncoder(m, trust_remote_code=True)
                    self.reranker_usado = m
                    if self.verbose:
                        print(f"  reranker: {m}")
                    break
                except Exception as ex:
                    if self.verbose:
                        print(f"  {m} no disponible: {str(ex)[:60]}")
            if self._rer is None:
                raise RuntimeError("ningún reranker disponible")
        return self._rer

    def reranked(self, consulta: str, k: int = 5, k_candidatos: int = 15) -> list[dict]:
        """Recupera ancho con el híbrido y reordena estrecho con el cross-encoder.

        El bi-encoder codifica consulta y fragmento por separado; el cross-encoder
        los lee juntos y puede notar que un artículo habla del mismo supuesto
        aunque no comparta vocabulario.
        """
        cand = self.hibrido(consulta, k=k_candidatos)
        # El cross-encoder reordena contra UNA consulta: con multi-consulta se
        # usa la primera, que es la canonica. Pasarle varias obligaria a
        # promediar puntajes de pares distintos, que no son comparables.
        canonica = self._lista(consulta)[0]
        pares = [(canonica, texto_indexable(c)) for c in cand]
        try:
            s = self._reranker().predict(pares)
        except Exception as ex:
            if self.verbose:
                print(f"  reranking no disponible ({str(ex)[:50]}); devuelvo el híbrido")
            return cand[:k]
        orden = sorted(range(len(cand)), key=lambda i: -s[i])[:k]
        return [{**cand[i], "score": float(s[i]), "via": "reranked"} for i in orden]

    def recuperar(self, consulta, estrategia: str = "hibrido", k: int = 5) -> list[dict]:
        return {"ingenuo": self.ingenuo, "hibrido": self.hibrido,
                "reranked": self.reranked}[estrategia](consulta, k=k)


# --------------------------------------------------------------------------
# Transformación de consulta
#
# El problema concreto de este dominio: la consulta es el relato de un ciudadano
# ("la EPS no me da el medicamento") y el corpus es texto legal ("servicios y
# tecnologías de salud deberán ser suministrados de manera completa"). No
# comparten casi vocabulario, y por eso BM25 solo devuelve ruido: para el caso
# E01 su primer resultado es el artículo de Desacato.
#
# La transformación reescribe el relato en los términos del ordenamiento ANTES
# de buscar. Es la técnica que más debería rendir aquí, precisamente porque el
# vacío de vocabulario es el cuello de botella.
# --------------------------------------------------------------------------
PROMPT_CONSULTA = """Eres un asistente jurídico colombiano. Vas a recibir el relato de un ciudadano.

Escribe una consulta de búsqueda en el lenguaje técnico del ordenamiento colombiano
para encontrar los artículos aplicables. Incluye:
- el derecho fundamental que está en juego
- el mecanismo constitucional que podría proceder
- los términos técnicos pertinentes (subsidiariedad, perjuicio irremediable,
  derechos colectivos, prolongación ilegal de la libertad, daño consumado, etc.)

No resuelvas el caso ni cites números de artículo. Solo la consulta, en una o dos
frases, sin preámbulo."""


PROMPT_MULTI = """Eres un asistente juridico colombiano. Vas a recibir el relato de un ciudadano.

Escribe {n} consultas de busqueda DISTINTAS para encontrar los articulos aplicables,
cada una desde un angulo diferente: una por el derecho fundamental en juego, una por
la causal de procedencia o improcedencia, y una por el mecanismo o el procedimiento.

No repitas la misma consulta reformulada. No cites numeros de articulo.

Responde SOLO con JSON: {{"consultas": ["...", "..."]}}"""

PROMPT_HYDE = """Eres un asistente juridico colombiano. Vas a recibir el relato de un ciudadano.

Escribe el PARRAFO DE UNA NORMA hipotetica que resolveria ese caso: redactalo como si
fuera el texto de un articulo de ley o de la Constitucion colombiana, con su registro y
su vocabulario. No digas que es hipotetico, no lo expliques y no cites numeros de
articulo ni nombres de leyes. Solo el parrafo, maximo 120 palabras."""


class TransformadorConsulta:
    """Reescribe el relato en lenguaje jurídico. Cachea igual que el juez: sin
    caché, la recuperación deja de ser reproducible entre corridas."""

    def __init__(self, cliente=None, modelo: str = "openai/gpt-oss-120b",
                 cache: str = "runs/cache_consultas.json", verbose: bool = True):
        import os
        if cliente is None:
            from groq import Groq
            cliente = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.cliente, self.modelo, self.verbose = cliente, modelo, verbose
        self.ruta = Path(cache)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.cache = (json.loads(self.ruta.read_text(encoding="utf-8"))
                      if self.ruta.exists() else {})
        self.llamadas = self.fallos = 0
        # Latencia SOLO de las llamadas que de verdad salieron a la API. Con el
        # cache caliente la transformacion cuesta microsegundos, y reportar eso
        # como su costo seria enganoso: el costo real es el de la primera vez.
        self.latencias_ms: list[float] = []

    def __call__(self, relato: str) -> str:
        if relato in self.cache:
            return self.cache[relato]
        t0 = time.perf_counter()
        try:
            r = self.cliente.chat.completions.create(
                model=self.modelo,
                messages=[{"role": "system", "content": PROMPT_CONSULTA},
                          {"role": "user", "content": relato}],
                temperature=0, max_tokens=512, seed=42, reasoning_effort="low")
            q = (r.choices[0].message.content or "").strip()
            if not q:
                raise RuntimeError("consulta vacía")
            self.cache[relato] = q
            self.llamadas += 1
            self.latencias_ms.append((time.perf_counter() - t0) * 1000)
            return q
        except Exception as ex:
            # Degradación explícita: si la transformación falla se busca con el
            # relato crudo. Peor recuperación, pero el sistema no se cae — y el
            # contador deja constancia de cuántas veces pasó.
            self.fallos += 1
            if self.verbose:
                print(f"  transformación falló ({str(ex)[:50]}); uso el relato crudo")
            return relato

    def costo(self) -> dict:
        """Lo que cuesta la transformacion, para la tabla de deltas."""
        L = sorted(self.latencias_ms)
        return {
            "llamadas_reales": self.llamadas,
            "desde_cache": len(self.cache) - self.llamadas,
            "fallos": self.fallos,
            "latencia_ms_media": round(sum(L) / len(L), 1) if L else None,
            "latencia_ms_p95": round(L[int(0.95 * (len(L) - 1))], 1) if L else None,
        }

    # -- tecnicas 4 y 5 -------------------------------------------------
    def multiples(self, relato: str, n: int = 3) -> list[str]:
        """MULTI-CONSULTA: n reescrituras distintas del mismo relato.

        El relato de un ciudadano admite varias lecturas juridicas y una sola
        reescritura escoge una. Con tres y fusion por RRF, basta con que UNA
        acierte el vocabulario de la norma. Es la tecnica que S08 recomienda
        justo para consultas coloquiales.

        La primera siempre es la reescritura canonica (la de `__call__`), para
        que multi-consulta nunca pueda ser peor que la transformacion simple
        por haber perdido esa consulta.
        """
        out = [self(relato)]
        clave = f"MULTI::{n}::{relato}"
        if clave in self.cache:
            out += json.loads(self.cache[clave])
            return out
        # Se cronometra como en `__call__` y en `hyde`. La primera version
        # incrementaba `llamadas` pero no registraba en `latencias_ms`, asi que
        # multi-consulta reportaba latencia None y parecia gratis siendo la
        # tecnica que hace una llamada EXTRA por caso --- y la que gano la
        # comparacion de recuperacion. Un costo sin medir abarata al ganador.
        t0 = time.perf_counter()
        try:
            r = self.cliente.chat.completions.create(
                model=self.modelo,
                messages=[{"role": "system", "content": PROMPT_MULTI.format(n=n - 1)},
                          {"role": "user", "content": relato}],
                temperature=0, max_tokens=512, seed=42, reasoning_effort="low",
                response_format={"type": "json_object"})
            d = json.loads((r.choices[0].message.content or "{}").strip())
            extra = [q.strip() for q in (d.get("consultas") or [])
                     if isinstance(q, str) and q.strip()][:n - 1]
            if extra:
                self.cache[clave] = json.dumps(extra, ensure_ascii=False)
                self.llamadas += 1
                self.latencias_ms.append((time.perf_counter() - t0) * 1000)
            out += extra
        except Exception as ex:
            self.fallos += 1
            if self.verbose:
                print(f"  multi-consulta fallo ({str(ex)[:50]}); sigo con una sola")
        return out

    def hyde(self, relato: str) -> str:
        """HyDE: se genera el articulo HIPOTETICO que resolveria el caso y se
        busca con ese texto, no con el relato.

        La idea es cerrar el vacio de vocabulario por el lado del corpus: el
        texto hipotetico ya esta escrito en lenguaje de norma, asi que se
        parece mas a lo que hay indexado. El riesgo es el costo: hay que
        generar antes de buscar, y al grupo de referencia HyDE le salio 180
        veces mas lento que el hibrido y peor en recall. Aqui se mide para
        poder decir si en este dominio pasa lo mismo o no.
        """
        clave = f"HYDE::{relato}"
        if clave in self.cache:
            return self.cache[clave]
        t0 = time.perf_counter()
        try:
            r = self.cliente.chat.completions.create(
                model=self.modelo,
                messages=[{"role": "system", "content": PROMPT_HYDE},
                          {"role": "user", "content": relato}],
                temperature=0, max_tokens=400, seed=42, reasoning_effort="low")
            q = (r.choices[0].message.content or "").strip()
            if not q:
                raise RuntimeError("HyDE vacio")
            self.cache[clave] = q
            self.llamadas += 1
            self.latencias_ms.append((time.perf_counter() - t0) * 1000)
            return q
        except Exception as ex:
            self.fallos += 1
            if self.verbose:
                print(f"  HyDE fallo ({str(ex)[:50]}); uso el relato crudo")
            return relato

    def guardar(self) -> None:
        self.ruta.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1),
                             encoding="utf-8")


# --------------------------------------------------------------------------
# Evaluación de la recuperación contra el gold del eval set
# --------------------------------------------------------------------------
def citas_esperadas(ejemplo: dict) -> set[str]:
    """Los artículos que el `fundamento` del gold dice que había que recuperar."""
    from schema import citas
    return set(citas(ejemplo["fundamento"]))


def _cita_de(chunk: dict) -> str:
    """La forma en que ese fragmento aparecería citado en un `fundamento`."""
    if "Decreto 2591" in chunk["norma"]:
        return f"{chunk['articulo']} Decreto 2591 de 1991"
    if chunk["articulo"].endswith("CP"):
        return chunk["articulo"]
    return chunk["norma"]


def cubre(chunk: dict, cita: str) -> bool:
    """¿Este fragmento respalda esa cita?

    No basta comparar cadenas: el gold cita `art. 6.3 Decreto 2591 de 1991` y el
    corpus tiene un único fragmento para el `art. 6` completo, con sus cinco
    numerales dentro. Si se exige igualdad exacta, recuperar el artículo correcto
    cuenta como fallo, y eso hunde el recall justo en los casos de subsidiariedad
    y derechos colectivos, que son los que más numerales citan.
    """
    propia = _cita_de(chunk)
    if propia == cita:
        return True
    # Un fragmento puede respaldar la cita de otra norma cuando su texto
    # vigente es el que esa norma introdujo: el art. 13 de la Ley 1266 de 2008
    # ES el texto del art. 3 de la Ley 2157 de 2021. El corpus lo declara en
    # `tambien_cita` y no se duplica el fragmento.
    if cita in (chunk.get("tambien_cita") or ()):
        return True
    # "art. 6.3 Decreto 2591 de 1991" lo cubre el fragmento de "art. 6 ..."
    m = re.match(r"(art\. \d+)\.\d+(.*)$", cita)
    return bool(m) and propia == m.group(1) + m.group(2)


REGLA_CHUNKING = """Regla de decision del chunking, FIJADA ANTES DE CORRER
(version 2026-10-15):

  1. Mayor hit@3.
  2. Empate (<= 0.01): mayor mrr@10.
  3. Empate: menos chunks (un indice mas pequeno es mas barato y mas auditable).

La hipotesis a batir es que el chunking POR ARTICULO gana, porque el articulo es
la unidad de cita en derecho colombiano: un fragmento que corta un articulo por
la mitad produce una cita que no se puede verificar. Se compara contra tamano
fijo para que esa hipotesis sea una medicion y no una conviccion."""


def trocear_fijo(docs: list[dict], size: int = 400, overlap: int = 60) -> list[dict]:
    """Chunking de tamano fijo con solape, el de la Sesion 7.

    Parte por caracteres sin respetar la frontera del articulo. Se incluye para
    poder medir lo que se pierde al hacerlo, no porque sea una buena idea aqui.
    """
    out = []
    for d in docs:
        t = d["texto"]
        paso = max(1, size - overlap)
        trozos = [t[i:i + size] for i in range(0, max(1, len(t)), paso)]
        trozos = [x for x in trozos if x.strip()]
        for i, tr in enumerate(trozos, 1):
            out.append({**d, "id": f"{d['id']}-f{i}", "texto": tr,
                        "parte": f"{i}/{len(trozos)}"})
    return out


def comparar_chunking(docs: list[dict], eval_set: list[dict], configs: dict,
                      modelo: str = MODELO_DENSO, estrategia: str = "hibrido",
                      k: int = 5, verbose: bool = True) -> dict:
    """Evalua la recuperacion con cada chunking y aplica REGLA_CHUNKING.

    `configs` es {nombre: callable(docs) -> chunks}.
    """
    filas = []
    for nombre, trocear_fn in configs.items():
        chunks = trocear_fn(docs)
        idx = Indice(chunks, modelo=modelo, verbose=False).construir()
        r = evaluar_recuperacion(idx, eval_set, estrategia, k=k)
        r["chunking"] = nombre
        r["n_chunks"] = len(chunks)
        r["chars_medios"] = round(sum(len(c["texto"]) for c in chunks) / len(chunks))
        filas.append(r)

    if verbose:
        print(f"\n{'='*86}\n  CHUNKING · misma estrategia ({estrategia}), mismo k\n{'='*86}")
        print(f"{'config':<26}{'chunks':>8}{'chars':>8}{'hit@1':>9}{'hit@3':>9}"
              f"{'mrr@10':>9}{'recall@k':>10}{'lat p95':>9}")
        print("-" * 86)
        for r in filas:
            print(f"{r['chunking']:<26}{r['n_chunks']:>8}{r['chars_medios']:>8}"
                  f"{r['hit@1']:>9.1%}{r['hit@3']:>9.1%}{r['mrr@10']:>9.3f}"
                  f"{r['recall@k']:>10.1%}{r['latencia_ms_p95']:>9.1f}")
        print("=" * 86)

    mejor = max(f["hit@3"] for f in filas)
    cand = [f for f in filas if mejor - f["hit@3"] <= TOLERANCIA_EMPATE]
    traza = [f"mejor hit@3 = {mejor:.1%} · {len(cand)} config(s) en la tolerancia"]
    if len(cand) > 1:
        mm = max(f["mrr@10"] for f in cand)
        cand = [f for f in cand if mm - f["mrr@10"] <= TOLERANCIA_EMPATE]
        traza.append(f"desempate por mrr@10 = {mm:.3f} · quedan {len(cand)}")
    if len(cand) > 1:
        mn = min(f["n_chunks"] for f in cand)
        cand = [f for f in cand if f["n_chunks"] == mn]
        traza.append(f"desempate por menos chunks = {mn} · quedan {len(cand)}")
    elegida = cand[0]["chunking"]
    traza.append(f"ELEGIDO: {elegida}")
    if verbose:
        print("  Regla de chunking fijada antes de correr:")
        for t in traza:
            print(f"    {t}")
    return {"elegido": elegida, "traza": traza, "regla": REGLA_CHUNKING,
            "filas": [{k2: v for k2, v in f.items() if k2 != "detalle"} for f in filas]}


REGLA_DECISION = """Regla de decision de la estrategia de recuperacion, FIJADA ANTES DE CORRER
(version 2026-10-15, anterior a la primera corrida de M3):

  0. GUARDA DE SEGURIDAD. Una estrategia queda descalificada si su recall@k es
     INFERIOR al del RAG ingenuo. Una tecnica avanzada que recupera menos que el
     baseline no entra al sistema por mas elegante que sea.
  1. Mayor recall@k.
  2. Empate (diferencia <= 0.01): mayor mrr@10 -- premia traer lo relevante arriba.
  3. Empate: menor latencia p95 del retrieval.
  4. Empate: menos casos sin recuperar ningun articulo esperado.

Se escribe aqui, en el codigo y con fecha, para que la eleccion no se haga
despues de ver los numeros. Es la diferencia entre elegir una estrategia y
justificar la que salio mejor."""

TOLERANCIA_EMPATE = 0.01


def _percentil(xs: list[float], p: float) -> float | None:
    if not xs:
        return None
    ys = sorted(xs)
    return ys[min(len(ys) - 1, int(p * (len(ys) - 1)))]


def evaluar_recuperacion(indice: Indice, eval_set: list[dict], estrategia: str,
                         k: int = 5, transformador=None,
                         k_metricas: int = 10) -> dict:
    """Metricas de recuperacion PURAS: no dependen del generador ni de un juez,
    asi que aislan el efecto de la tecnica de retrieval.

    Se recupera hasta `k_metricas` (10) para poder calcular hit@1, hit@3 y
    mrr@10 sobre una lista mas profunda, y se usan los primeros `k` para el
    recall y la precision que van al prompt. Medir el ranking solo hasta k=5
    oculta si lo relevante estaba en el puesto 6 o no estaba en absoluto.

    La latencia se mide en el reloj de pared, separando dos costos que no son
    comparables: el del retrieval y el de la transformacion de consulta, que
    sale a una API. El segundo se lee de `transformador.costo()` porque con el
    cache caliente el tiempo observado aqui seria casi cero.
    """
    profundidad = max(k, k_metricas)
    recalls, precisiones, rangos, lat_ms = [], [], [], []
    hit1 = hit3 = hitk = 0
    detalle = []

    for e in eval_set:
        esperadas = citas_esperadas(e)
        if not esperadas:
            continue
        consulta = transformador(e["relato"]) if transformador else e["relato"]

        t0 = time.perf_counter()
        profundo = indice.recuperar(consulta, estrategia=estrategia, k=profundidad)
        lat_ms.append((time.perf_counter() - t0) * 1000)

        rec = profundo[:k]
        relevante = [any(cubre(c, x) for x in esperadas) for c in profundo]

        # Rango (1-based) del primer fragmento relevante en la lista profunda.
        rango = next((i + 1 for i, r in enumerate(relevante) if r), None)
        rangos.append(rango)
        hit1 += bool(relevante[:1] and relevante[0])
        hit3 += any(relevante[:3])
        hitk += any(relevante[:k])

        halladas = {x for x in esperadas if any(cubre(c, x) for c in rec)}
        utiles = sum(relevante[:k])
        recalls.append(len(halladas) / len(esperadas))
        precisiones.append(utiles / len(rec) if rec else 0.0)

        detalle.append({
            "id": e["id"],
            "esperadas": sorted(esperadas),
            "obtenidas": [_cita_de(c) for c in rec],
            "recall": round(len(halladas) / len(esperadas), 3),
            "rango_primer_relevante": rango,
            "latencia_ms": round(lat_ms[-1], 2),
        })

    n = len(recalls)
    if n == 0:
        return {"estrategia": estrategia, "k": k, "n": 0}

    # MRR: los casos sin ningun relevante aportan 0, no se excluyen. Excluirlos
    # premiaria a la estrategia que falla del todo en los casos dificiles.
    mrr = sum(1 / r if r else 0.0 for r in rangos) / n

    return {
        "estrategia": estrategia + (" + transformacion" if transformador else ""),
        "k": k,
        "k_metricas": profundidad,
        "n": n,
        "recall@k": sum(recalls) / n,
        "precision@k": sum(precisiones) / n,
        "hit@1": hit1 / n,
        "hit@3": hit3 / n,
        f"hit@{k}": hitk / n,
        "mrr@10": mrr,
        "acierto_top1": hit1 / n,          # se conserva el nombre anterior
        "casos_sin_ninguna": sum(1 for d in detalle if d["recall"] == 0),
        # LA MEDIA SOLA MIENTE CUANDO HAY UN ARRANQUE.
        #
        # Medido en m3/20261016T215955Z: la estrategia `reranked` reporto una
        # media de 413.19 ms con un p95 de 115.15. Una media 3.6 veces por
        # encima del p95 no describe el coste por consulta: describe la carga
        # del modelo del cross-encoder en la PRIMERA llamada, repartida entre
        # las 63. El p50 y el maximo lo hacen visible, y `_aviso_arranque`
        # dice cuando pasa en vez de dejarlo a quien lea la tabla.
        "latencia_ms_media": round(sum(lat_ms) / n, 2),
        "latencia_ms_p50": round(_percentil(lat_ms, 0.50), 2),
        "latencia_ms_p95": round(_percentil(lat_ms, 0.95), 2),
        "latencia_ms_max": round(max(lat_ms), 2) if lat_ms else None,
        "aviso_arranque": (
            "la media supera el p95: hay un coste de arranque (carga de modelo "
            "en la primera llamada) repartido entre todas las consultas. El "
            "coste por consulta en caliente es el p50."
            if lat_ms and (sum(lat_ms) / n) > _percentil(lat_ms, 0.95)
            else None),
        "costo_transformacion": transformador.costo() if transformador else None,
        "detalle": detalle,
    }


def elegir_estrategia(resultados: list[dict], k: int = 5) -> dict:
    """Aplica REGLA_DECISION a los resultados y devuelve la traza de la decision.

    El primer resultado de la lista debe ser el RAG ingenuo: es el baseline
    contra el que opera la guarda de seguridad.
    """
    base = resultados[0]
    traza = [f"baseline (ingenuo): recall@{k} = {base['recall@k']:.1%}"]

    vivos, descalificadas = [], []
    for r in resultados:
        if r is base:
            vivos.append(r)
            continue
        if r["recall@k"] < base["recall@k"] - 1e-12:
            descalificadas.append(r["estrategia"])
            traza.append(
                f"DESCALIFICADA {r['estrategia']}: recall@{k} {r['recall@k']:.1%} "
                f"< {base['recall@k']:.1%} del ingenuo (guarda de seguridad)")
        else:
            vivos.append(r)

    mejor_recall = max(r["recall@k"] for r in vivos)
    candidatos = [r for r in vivos if mejor_recall - r["recall@k"] <= TOLERANCIA_EMPATE]
    traza.append(
        f"mejor recall@{k} = {mejor_recall:.1%} · {len(candidatos)} estrategia(s) "
        f"dentro de la tolerancia de {TOLERANCIA_EMPATE:.0%}")

    if len(candidatos) > 1:
        mejor_mrr = max(r["mrr@10"] for r in candidatos)
        candidatos = [r for r in candidatos if mejor_mrr - r["mrr@10"] <= TOLERANCIA_EMPATE]
        traza.append(f"desempate por mrr@10 = {mejor_mrr:.3f} · quedan {len(candidatos)}")

    if len(candidatos) > 1:
        mejor_lat = min(r["latencia_ms_p95"] for r in candidatos)
        candidatos = [r for r in candidatos if r["latencia_ms_p95"] == mejor_lat]
        traza.append(f"desempate por latencia p95 = {mejor_lat} ms · quedan {len(candidatos)}")

    if len(candidatos) > 1:
        menos = min(r["casos_sin_ninguna"] for r in candidatos)
        candidatos = [r for r in candidatos if r["casos_sin_ninguna"] == menos]
        traza.append(f"desempate por casos sin recuperar nada = {menos} · quedan {len(candidatos)}")

    if len(candidatos) > 1:
        candidatos.sort(key=lambda r: r["estrategia"])
        traza.append(
            "empate total tras los cuatro criterios: se toma la primera por orden "
            "alfabetico y queda constancia de que la regla no discrimino")

    ganadora = candidatos[0]
    traza.append(f"ELEGIDA: {ganadora['estrategia']}")
    return {"elegida": ganadora["estrategia"], "descalificadas": descalificadas,
            "traza": traza, "regla": REGLA_DECISION}


def comparar_estrategias(resultados: list[dict], k: int = 5) -> dict:
    """Tabla de deltas + la decision. Es el entregable del criterio 2 de M3."""
    print(f"\n{'='*104}\n  RECUPERACION · tabla de deltas\n{'='*104}")
    print(f"{'estrategia':<30}{'recall@k':>10}{'prec@k':>9}{'hit@1':>8}"
          f"{'hit@3':>8}{'mrr@10':>9}{'lat ms':>9}{'p95':>8}{'sin nada':>10}{'delta':>9}")
    print("-" * 104)
    base = None
    for r in resultados:
        d = "" if base is None else f"{r['recall@k'] - base:+.1%}"
        if base is None:
            base = r["recall@k"]
        print(f"{r['estrategia']:<30}{r['recall@k']:>9.1%}{r['precision@k']:>9.1%}"
              f"{r['hit@1']:>8.1%}{r['hit@3']:>8.1%}{r['mrr@10']:>9.3f}"
              f"{r['latencia_ms_media']:>9.1f}{r['latencia_ms_p95']:>8.1f}"
              f"{r['casos_sin_ninguna']:>10}{d:>9}")
    print("=" * 104)

    for r in resultados:
        c = r.get("costo_transformacion")
        if c:
            print(f"  costo de la transformacion en {r['estrategia']}: "
                  f"{c['llamadas_reales']} llamadas reales, {c['desde_cache']} desde cache, "
                  f"{c['fallos']} fallos · {c['latencia_ms_media']} ms de media, "
                  f"{c['latencia_ms_p95']} ms p95")

    decision = elegir_estrategia(resultados, k=k)
    print(f"\n  Regla de decision fijada antes de correr:")
    for t in decision["traza"]:
        print(f"    {t}")
    return decision
