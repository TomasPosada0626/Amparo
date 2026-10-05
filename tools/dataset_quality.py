"""Controles de calidad del dataset de fine-tuning (M1).

El dataset de M1 es el cimiento del proyecto: lo que el modelo aprenda aqui se
arrastra a M2 (que lo evalua) y a M3 (que le pone contexto recuperado encima).
La version anterior fallaba de forma silenciosa -- pasaba cualquier revision
manual porque cada ejemplo, leido suelto, se veia bien -- y solo al medirla en
conjunto se vio que el 89.8% de las respuestas daba consejo generico sin nombrar
ningun mecanismo legal, justo lo que el principio 3 de PRODUCT.md prohibe.

Este modulo convierte esos principios en comprobaciones ejecutables, para que la
calidad del dataset sea una cifra que se mide y no una impresion de quien lo
revisa. Se corre con:

    python -m tools.dataset_quality                 # sobre data/dataset_legal.jsonl
    python -m tools.dataset_quality <ruta.jsonl>    # sobre un lote en construccion

Devuelve codigo de salida 1 si alguna puerta de calidad no pasa, para poder
usarlo como gate en CI o antes de lanzar un entrenamiento.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = PROJECT_ROOT / "data" / "dataset_legal.jsonl"

# --- Contrato de una respuesta -------------------------------------------------
# Principio 3 de PRODUCT.md: cada respuesta apunta a una figura juridica concreta.
# La lista es deliberadamente amplia (incluye autoridades ante las que se acude,
# no solo acciones judiciales): "acude a la Comisaria de Familia" ancla tanto como
# "interpon una tutela". Lo que NO cuenta como anclaje es el consejo generico
# ("revisa el contrato", "solicita por escrito") sin nombrar a donde acudir.
#
# Dos familias cuentan como anclaje, porque las dos le dicen a la persona que
# hacer en concreto: (A) la figura o accion juridica, y (B) la autoridad o
# entidad ante la cual acudir. "Acude a la Comisaria de Familia" orienta tanto
# como "interpon una tutela". Lo que NO cuenta es el consejo generico sin
# destino: "revisa el contrato", "solicita por escrito", "reune evidencia".
#
# El catalogo es la definicion operativa de "nombra un mecanismo", asi que
# tiene que ser amplio y literal: si falta una ruta real, la puerta produce
# falsos negativos y castiga respuestas correctas (paso en el piloto de
# Despido, donde "Inspeccion DEL Trabajo" no hacia match con un patron escrito
# como "Inspeccion DE Trabajo").
MECANISMOS = {
    # --- (A) Figuras y acciones juridicas ---
    "tutela": r"\btutelas?\b|acci[oó]n de tutela",
    "derecho de peticion": r"derecho de petici[oó]n",
    "habeas data": r"h[aá]beas data",
    "conciliacion": r"conciliaci[oó]n|conciliar ante|centro de conciliaci[oó]n",
    "recurso (reposicion/apelacion/queja)": r"\breposici[oó]n\b|\bapelaci[oó]n\b|recursos? de (queja|s[uú]plica)"
                                            r"|recursos? de ley|v[ií]a gubernativa|insistencia",
    "jurisdiccion contencioso administrativa": r"contencioso administrativ|nulidad y restablecimiento",
    "contratacion estatal": r"\bSECOP\b|supervisor del contrato|ordenador del gasto|agencia de contrataci[oó]n",
    "restitucion de inmueble": r"restituci[oó]n (del? )?(inmueble|bien)|proceso de restituci[oó]n|lanzamiento por ocupaci[oó]n",
    "proceso ejecutivo": r"proceso ejecutivo|cobro ejecutivo|t[ií]tulo ejecutivo",
    "arbitraje": r"tribunal de arbitramento|cl[aá]usula compromisoria|centro de arbitraje|arbitraje",
    "requerimiento / resolucion del contrato": r"requerimiento escrito|requiere por escrito"
                                               r"|(resoluci[oó]n|terminaci[oó]n) del contrato|junta o asamblea de socios",
    "demanda / juez competente": r"demand(a|ar|as)\b|juez (laboral|civil|de familia|administrativo|de peque[nñ]as causas)"
                                 r"|juzgado|v[ií]a judicial|proceso (ordinario|verbal|declarativo)",
    "querella": r"\bquerellas?\b",
    "denuncia penal": r"denuncia(r|s)? (penal|ante la [Ff]iscal)|\bFiscal[ií]a\b|\bURI\b|\bSAU\b|[Cc]asa de [Jj]usticia",
    "medida de proteccion / VIF": r"medida de protecci[oó]n|[Cc]omisar[ií]a de [Ff]amilia",
    "reintegro / fuero": r"\breintegro\b|fuero (de maternidad|sindical|de salud|circunstancial)"
                         r"|estabilidad laboral reforzada|permiso del inspector",
    "PQR / reclamacion formal": r"\bPQRS?\b|reclamaci[oó]n formal|derecho de reclamaci[oó]n|reclamaci[oó]n directa",
    "silencio administrativo": r"silencio administrativo",
    "accion de cumplimiento": r"acci[oó]n de cumplimiento",
    "accion popular / de grupo": r"acci[oó]n (popular|de grupo)",
    "desacato": r"\bdesacato\b",
    "nulidad": r"\bnulidad\b|revocatoria directa",
    "insolvencia persona natural": r"insolvencia de persona natural|insolvencia econ[oó]mica",
    "objecion / oposicion": r"objeta(r|la|lo|ndo)?\b|oposici[oó]n a la (diligencia|medida)"
                            r"|levantamiento (del|de la) (embargo|medida)|excepciones de m[eé]rito",

    # --- (B) Autoridades y entidades concretas ---
    "inspeccion / ministerio de trabajo": r"[Ii]nspecci[oó]n del? [Tt]rabajo|[Ii]nspector del? [Tt]rabajo"
                                          r"|[Mm]inisterio del? [Tt]rabajo",
    "superintendencia": r"[Ss]uperintendencia|\bSIC\b|\bSuperSalud\b|\bSupersalud\b",
    "proteccion al consumidor": r"protecci[oó]n al consumidor",
    "defensoria / personeria / procuraduria": r"[Dd]efensor[ií]a del [Pp]ueblo|[Pp]ersoner[ií]a|[Pp]rocuradur[ií]a"
                                              r"|[Cc]ontralor[ií]a|[Vv]eedur[ií]a",
    "consultorio juridico / abogado": r"consultorio jur[ií]dico|\babogad[oa]s?\b",
    "autoridad de transito": r"(autoridad|[Ss]ecretar[ií]a|organismo|entidad) de tr[aá]nsito|\bSIMIT\b"
                             r"|inspector de tr[aá]nsito|impugna(r|cion|ción)|descargos|comparendo ante",
    "SOAT / aseguradora": r"\bSOAT\b|aseguradora|[Mm]edicina [Ll]egal",
    "linea de emergencia / policia": r"[Ll][ií]nea 123|\b123\b|[Ll][ií]nea 155|[Pp]olic[ií]a|urgencias",
    "ICBF / familia": r"\bICBF\b|[Bb]ienestar [Ff]amiliar|[Dd]efensor de [Ff]amilia|[Cc]omisar[ií]a"
                      r"|r[eé]gimen de visitas|\bcustodia\b|alimentos provisionales|\bsucesi[oó]n\b"
                      r"|[Cc]onsulado|[Cc]anciller[ií]a",
    "educacion (secretaria / ministerio)": r"[Ss]ecretar[ií]a de [Ee]ducaci[oó]n|[Mm]inisterio de [Ee]ducaci[oó]n"
                                           r"|manual de convivencia|reglamento (acad[eé]mico|estudiantil)",
    "curador urbano / planeacion": r"[Cc]urador [Uu]rbano|[Pp]laneaci[oó]n [Mm]unicipal|[Ss]ecretar[ií]a de [Pp]laneaci[oó]n"
                                   r"|[Aa]lcald[ií]a",
    "autoridad ambiental": r"[Aa]utoridad ambiental|\bCAR\b|\bANLA\b|[Cc]orporaci[oó]n [Aa]ut[oó]noma"
                           r"|[Ss]ecretar[ií]a (Distrital |Municipal )?de [Aa]mbiente",
    "DIAN / UGPP": r"\bDIAN\b|\bUGPP\b",
    "SENA": r"\bSENA\b",
    "migracion colombia": r"[Mm]igraci[oó]n [Cc]olombia",
    "camara de comercio / notaria": r"[Cc][aá]mara de [Cc]omercio|[Nn]otar[ií]a|[Oo]ficina de [Ii]nstrumentos [Pp][uú]blicos"
                                    r"|\bORIP\b|\bIGAC\b",
    "propiedad industrial": r"registro de marca|infracci[oó]n marcaria|competencia desleal|oposici[oó]n al registro"
                            r"|cancelaci[oó]n por no uso|b[uú]squeda de antecedentes|[Dd]erecho de [Aa]utor|\bInvima\b",
    "control urbano / patrimonio": r"control urbano|reconocimiento de (la )?edificaci[oó]n|espacio p[uú]blico"
                                   r"|[Mm]inisterio de [Cc]ultura",
    "ARL / seguridad social": r"\bARL\b|\bEPS\b y la \bARL\b|[Jj]unta de [Cc]alificaci[oó]n",
    "pensiones (colpensiones / fondo)": r"[Cc]olpensiones|fondo de pensiones|administradora de pensiones"
                                        r"|[Cc]aja de [Cc]ompensaci[oó]n|operador de aportes",
    "comite (convivencia / seguridad y salud)": r"comit[eé] de (convivencia|seguridad y salud)|\bCOPASST\b",
    "entidad financiera / central de riesgo": r"central(es)? de riesgo|[Dd]atacr[eé]dito|[Tt]ransUni[oó]n"
                                              r"|[Dd]efensor del [Cc]onsumidor [Ff]inanciero|casa de cobranza|paz y salvo",
    "registraduria / RUNT": r"[Rr]egistradur[ií]a|\bRUNT\b",
}

# Lo que el dataset NO debe ensenar: precision normativa no verificable. Eso lo
# aporta el RAG de M3 contra el corpus real, no la memoria del modelo.
#
# La definicion NO se escribe aqui: se toma de tools/evaluation/domain_metric.py,
# que es la que usa el harness de M2 para medir el mismo fenomeno sobre las
# respuestas generadas. Tener dos definiciones distintas hacia que M1 y M2
# reportaran cifras no comparables de "citas inventadas" (10.8%->0.0% en uno,
# 89.2%->100% en el otro) para lo que en principio es la misma propiedad.
from tools.evaluation.domain_metric import CITATION_PATTERNS

CITA_NORMATIVA = re.compile(
    "|".join(p.pattern for p in CITATION_PATTERNS.values()),
    re.IGNORECASE,
)
# Plazos exactos: tampoco se memorizan (cambian por norma y por tramite).
PLAZO_EXACTO = re.compile(r"\b\d+\s*(d[ií]as?|meses?|a[nñ]os?)\s*(h[aá]biles|calendario)?\b", re.IGNORECASE)

# Promesa de resultado: viola el principio 2 (prudencia sobre certeza).
PROMESA = re.compile(
    r"\b(te van a dar|vas a ganar|seguro que ganas|con seguridad obtendr|garantiza(do|r)?\s+(el|un)\s+resultado"
    r"|siempre procede|nunca procede|es automatic)",
    re.IGNORECASE,
)

URGENCIA = re.compile(
    r"amenaz|me van a (echar|sacar)|desalojo|violencia|golpe|peligro|riesgo (de|para)|urgen|emergencia"
    r"|no me atienden|me negaron la atenci[oó]n|sin medicamento",
    re.IGNORECASE,
)
AYUDA_INMEDIATA = re.compile(
    r"[Ll][ií]nea 123|\b123\b|[Cc]omisar[ií]a de [Ff]amilia|[Ff]iscal[ií]a|[Pp]olic[ií]a|urgencias"
    r"|[Dd]efensor[ií]a del [Pp]ueblo|[Pp]ersoner[ií]a|[Ll][ií]nea 155",
)

MIN_PALABRAS, MAX_PALABRAS = 15, 75
SOLAPAMIENTO_MAX = 0.5  # jaccard de 4-gramas entre respuestas de una misma categoria


def cargar(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(linea) for linea in f if linea.strip()]


def menciona_mecanismo(texto: str) -> bool:
    """Se compara SIN distinguir mayusculas, igual que el catalogo embebido en
    colab/m1_finetune.ipynb (que compila con re.I).

    Antes esta funcion comparaba con mayusculas significativas y el notebook no,
    asi que la misma respuesta podia "nombrar una ruta" para M1 y no para la
    puerta de calidad: dos cifras distintas de la misma propiedad. El caso
    concreto eran los patrones escritos en minuscula ("... de tr[aá]nsito")
    frente a la mayuscula natural de un nombre propio ("Secretaria de Transito",
    40 respuestas del dataset); dos de ellas se contaban como consejo generico
    aunque si daban el destino.
    """
    return any(re.search(p, texto, re.IGNORECASE) for p in MECANISMOS.values())


def _shingles(texto: str, n: int = 4) -> set[str]:
    palabras = re.sub(r"[^\w ]", " ", texto.lower()).split()
    return {" ".join(palabras[i : i + n]) for i in range(max(1, len(palabras) - n + 1))}


def analizar(registros: list[dict]) -> dict:
    total = len(registros)
    respuestas = [r["messages"][2]["content"] for r in registros]
    preguntas = [r["messages"][1]["content"] for r in registros]

    sin_mecanismo = [r for r in registros if not menciona_mecanismo(r["messages"][2]["content"])]
    con_cita = [r for r in registros if CITA_NORMATIVA.search(r["messages"][2]["content"])]
    con_plazo = [r for r in registros if PLAZO_EXACTO.search(r["messages"][2]["content"])]
    con_promesa = [r for r in registros if PROMESA.search(r["messages"][2]["content"])]

    fuera_de_rango = [
        r for r in registros
        if not (MIN_PALABRAS <= len(r["messages"][2]["content"].split()) <= MAX_PALABRAS)
    ]

    # Urgencia: si la pregunta describe riesgo, la respuesta debe orientar a ayuda
    # inmediata, no solo explicar la figura legal (hallazgo del caso 9103 de M3).
    urgentes = [r for r in registros if URGENCIA.search(r["messages"][1]["content"])]
    urgentes_sin_ayuda = [r for r in urgentes if not AYUDA_INMEDIATA.search(r["messages"][2]["content"])]

    # Repeticion: lo que degrado la version anterior del dataset.
    por_categoria: dict[str, list[dict]] = defaultdict(list)
    for r in registros:
        por_categoria[r["category"]].append(r)
    pares_repetidos = []
    for categoria, items in por_categoria.items():
        firmas = [(r, _shingles(r["messages"][2]["content"])) for r in items]
        for i in range(len(firmas)):
            for j in range(i + 1, len(firmas)):
                a, b = firmas[i][1], firmas[j][1]
                if not a or not b:
                    continue
                jaccard = len(a & b) / len(a | b)
                if jaccard >= SOLAPAMIENTO_MAX:
                    pares_repetidos.append((jaccard, categoria, firmas[i][0]["id"], firmas[j][0]["id"]))

    ids = [r["id"] for r in registros]
    system_prompts = {r["messages"][0]["content"] for r in registros}

    return {
        "total": total,
        "categorias": len(por_categoria),
        "por_categoria": {c: len(v) for c, v in sorted(por_categoria.items())},
        "sin_mecanismo": sin_mecanismo,
        "con_cita": con_cita,
        "con_plazo": con_plazo,
        "con_promesa": con_promesa,
        "fuera_de_rango": fuera_de_rango,
        "urgentes": urgentes,
        "urgentes_sin_ayuda": urgentes_sin_ayuda,
        "pares_repetidos": sorted(pares_repetidos, reverse=True),
        "preguntas_duplicadas": [q for q, n in Counter(preguntas).items() if n > 1],
        "respuestas_duplicadas": [a for a, n in Counter(respuestas).items() if n > 1],
        "ids_duplicados": [i for i, n in Counter(ids).items() if n > 1],
        "system_prompts_distintos": len(system_prompts),
    }


def reportar(a: dict) -> list[str]:
    """Imprime el informe y devuelve la lista de puertas de calidad falladas."""
    total = a["total"]
    pct = lambda n: f"{100 * n / total:.1f}%" if total else "-"
    fallos: list[str] = []

    def puerta(ok: bool, etiqueta: str) -> str:
        if ok:
            return "OK  "
        fallos.append(etiqueta)
        return "FALLA"

    print(f"Dataset: {total} ejemplos en {a['categorias']} categorias\n")
    print("PUERTAS DE CALIDAD")

    n = total - len(a["sin_mecanismo"])
    print(f"  [{puerta(len(a['sin_mecanismo']) <= total * 0.05, 'mecanismo legal')}] "
          f"nombran un mecanismo legal: {n}/{total} ({pct(n)})  -- meta >=95%")

    print(f"  [{puerta(not a['con_cita'], 'citas normativas')}] "
          f"sin citar articulos/leyes: {total - len(a['con_cita'])}/{total}  -- meta 100% (eso lo aporta el RAG)")

    print(f"  [{puerta(not a['con_plazo'], 'plazos exactos')}] "
          f"sin plazos exactos memorizados: {total - len(a['con_plazo'])}/{total}  -- meta 100%")

    print(f"  [{puerta(not a['con_promesa'], 'promesas de resultado')}] "
          f"sin promesas de resultado: {total - len(a['con_promesa'])}/{total}  -- meta 100%")

    nu = len(a["urgentes"])
    ok_urg = len(a["urgentes_sin_ayuda"]) == 0
    print(f"  [{puerta(ok_urg, 'urgencia sin ayuda inmediata')}] "
          f"casos urgentes que orientan a ayuda inmediata: {nu - len(a['urgentes_sin_ayuda'])}/{nu}  -- meta 100%")

    print(f"  [{puerta(len(a['pares_repetidos']) <= total * 0.01, 'repeticion')}] "
          f"pares de respuestas casi iguales: {len(a['pares_repetidos'])}  -- meta <=1% de los ejemplos")

    print(f"  [{puerta(not a['fuera_de_rango'], 'longitud')}] "
          f"longitud entre {MIN_PALABRAS} y {MAX_PALABRAS} palabras: "
          f"{total - len(a['fuera_de_rango'])}/{total}")

    integridad_ok = (
        not a["ids_duplicados"] and not a["preguntas_duplicadas"]
        and not a["respuestas_duplicadas"] and a["system_prompts_distintos"] == 1
    )
    print(f"  [{puerta(integridad_ok, 'integridad')}] "
          f"integridad: ids unicos, sin preguntas/respuestas duplicadas, 1 solo system prompt")

    if a["sin_mecanismo"]:
        print(f"\n  Ejemplos sin mecanismo legal (primeros 5 de {len(a['sin_mecanismo'])}):")
        for r in a["sin_mecanismo"][:5]:
            print(f"    id {r['id']} [{r['category']}]: {r['messages'][2]['content'][:90]}")
    if a["urgentes_sin_ayuda"]:
        print(f"\n  Urgentes sin orientacion inmediata (primeros 5 de {len(a['urgentes_sin_ayuda'])}):")
        for r in a["urgentes_sin_ayuda"][:5]:
            print(f"    id {r['id']}: {r['messages'][1]['content'][:85]}")
    if a["con_cita"]:
        print(f"\n  Con cita normativa (primeros 5 de {len(a['con_cita'])}):")
        for r in a["con_cita"][:5]:
            print(f"    id {r['id']}: {r['messages'][2]['content'][:90]}")

    return fallos


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATASET
    registros = cargar(path)
    fallos = reportar(analizar(registros))
    if fallos:
        print(f"\nRESULTADO: {len(fallos)} puerta(s) sin pasar -> {', '.join(fallos)}")
        raise SystemExit(1)
    print("\nRESULTADO: todas las puertas de calidad pasan.")


if __name__ == "__main__":
    main()
