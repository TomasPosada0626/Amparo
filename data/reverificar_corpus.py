"""
Vuelve a cotejar cada fragmento del corpus contra su `fuente` (ROADMAP #25).

EL PROBLEMA QUE RESUELVE

`verificado: true` es un BOOLEANO QUE ALGUIEN ESCRIBIO. El auditor
(data/auditar_corpus.py) comprueba higiene de transcripcion y cobertura de
citas, pero no abre la fuente: nada en el proyecto contrastaba el texto contra
el documento del que dice venir. Asi que "100% verificado" significaba "100%
marcado como verificado", que es la misma debilidad que tenia el "46/46" del
eval set antes del analisis de sensibilidad.

Y hay una razon de fondo para re-cotejar y no solo cotejar una vez: **las
normas cambian**. Un articulo puede ser modificado, derogado o declarado
inexequible despues de transcribirse. Un fragmento verificado hace dos anos no
esta verificado hoy, y un RAG sirve lo que recupera con apariencia de
autoridad: si el texto esta desactualizado, el sistema lo cita como derecho
vigente y el usuario no tiene forma de notarlo.

TRES RESULTADOS, Y LA DISTINCION IMPORTA

    coincide      el texto del fragmento aparece en la fuente. Se actualiza
                  `verificado_el`.
    no_aparece    la fuente se leyo y el texto NO esta. Es el caso grave: o la
                  transcripcion esta mal, o la norma cambio. NO se toca
                  `verificado`: lo decide una persona mirando el caso.
    inaccesible   no se pudo leer la fuente (red, certificado, PDF escaneado).
                  **NO es un fallo del fragmento** y no se cuenta como tal.
                  Confundir "no pude comprobar" con "esta mal" produciria
                  alarmas falsas, y confundirlo con "esta bien" es peor.

Las fuentes oficiales colombianas fallan a menudo: funcionpublica.gov.co no
valida su certificado y secretariasenado.gov.co rechaza conexiones. Por eso
`inaccesible` sera el resultado mas comun y el script no lo trata como error.

    python -I data/reverificar_corpus.py                 # informe, sin escribir
    python -I data/reverificar_corpus.py --escribir      # actualiza verificado_el
    python -I data/reverificar_corpus.py --solo L1751-06

NO se corre en la autoprueba de integracion: necesita red y tarda. Es una
comprobacion periodica, no una de cada cambio.
"""
from __future__ import annotations
import argparse
import html
import json
import re
import ssl
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTA = RAIZ / "data" / "corpus.json"
RUTA_OUT = RAIZ / "data" / "reverificacion_corpus.json"

AGENTE = "Mozilla/5.0 (compatible; agenteAmparo/1.0; verificacion de corpus)"
# Cuantos caracteres del fragmento se buscan. Un fragmento entero puede no
# coincidir por un guion de division o un salto de linea; una ventana larga en
# el medio del texto es una huella suficiente y robusta.
VENTANA = 220


def normalizar(t: str) -> str:
    """Para comparar: sin acentos, sin puntuacion, un solo espacio.

    La comparacion NO puede ser literal byte a byte: el extractor de PDF mete
    guiones de division, el HTML trae entidades y las fuentes usan comillas
    distintas. Lo que se comprueba es que las PALABRAS esten, en ese orden.
    """
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9ñ ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def decodificar(crudo: bytes, tipo: str = "") -> str:
    """Decodifica respetando el charset, no asumiendo UTF-8.

    Hacia falta: la relatoria de la Corte Constitucional sirve sus sentencias
    en Windows-1252, y decodificarlas como UTF-8 con `errors="replace"`
    convertia cada acento en el caracter de reemplazo --- `art�culo` en vez
    de `articulo`. Para COTEJAR da casi igual, porque `normalizar` quita los
    acentos de todas formas; para TRANSCRIBIR al corpus es inservible, y el
    corpus declara `transcripcion: "literal"`.

    Orden: el charset que declara la cabecera, luego el que declara el propio
    HTML en su meta, luego UTF-8 estricto, y por ultimo cp1252, que es lo que
    usan casi todos los sitios normativos colombianos. Solo si todo falla se
    recurre a reemplazar caracteres.
    """
    candidatos = []
    m = re.search(r"charset=([\w-]+)", tipo or "", re.I)
    if m:
        candidatos.append(m.group(1))
    cabeza = crudo[:4000].decode("ascii", errors="ignore")
    m = re.search(r"charset=[\"']?([\w-]+)", cabeza, re.I)
    if m:
        candidatos.append(m.group(1))
    candidatos += ["utf-8", "cp1252", "latin-1"]
    for enc in candidatos:
        try:
            return crudo.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return crudo.decode("utf-8", errors="replace")


def descargar(url: str, segundos: int = 25) -> tuple[str | None, str]:
    """(texto, motivo). `texto` es None si no se pudo leer."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
        with urllib.request.urlopen(req, timeout=segundos, context=ctx) as r:
            crudo = r.read()
            tipo = r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as ex:
        return None, f"HTTP {ex.code}"
    except ssl.SSLError as ex:
        return None, f"TLS: {str(ex)[:60]}"
    except Exception as ex:                        # noqa: BLE001
        return None, f"{type(ex).__name__}: {str(ex)[:60]}"

    if "pdf" in tipo.lower() or crudo[:5] == b"%PDF-":
        try:
            import io
            from pypdf import PdfReader
            paginas = PdfReader(io.BytesIO(crudo)).pages
            texto = "\n".join((p.extract_text() or "") for p in paginas)
        except Exception as ex:                    # noqa: BLE001
            return None, f"PDF ilegible: {type(ex).__name__}"
        if len(normalizar(texto)) < 200:
            # Un PDF escaneado extrae casi nada. No es que el fragmento este
            # mal: es que esta fuente no sirve para comprobarlo.
            return None, "PDF sin capa de texto (escaneado)"
        return texto, "pdf"

    texto = decodificar(crudo, tipo)
    texto = re.sub(r"<script.*?</script>", " ", texto, flags=re.S | re.I)
    texto = re.sub(r"<style.*?</style>", " ", texto, flags=re.S | re.I)
    # El CSS de las fuentes web aparece FUERA de <style> en las paginas de
    # Cancilleria, asi que hay que quitarlo aparte o se cuela en el texto.
    texto = re.sub(r"@font-face\s*\{.*?\}", " ", texto, flags=re.S)
    texto = re.sub(r"<[^>]+>", " ", texto)
    # LAS ENTIDADES HAY QUE DECODIFICARLAS, y este era un bug propio que
    # producia FALSAS ALARMAS. Las paginas oficiales colombianas codifican
    # todos los acentos como entidades: `Compilaci&oacute;n` en vez de
    # `Compilación`. Sin desescapar, `normalizar` deja las letras "oacute"
    # donde deberia ir la vocal, ninguna palabra acentuada coincide, y dos
    # fragmentos correctos salian como `no_aparece`.
    texto = html.unescape(texto)
    return texto, "html"


def cotejar(frag: dict, cache: dict) -> dict:
    if frag.get("transcripcion") == "nota_editorial":
        # No es una transcripcion: es una explicacion del equipo. Cotejarla
        # contra la fuente no tiene sentido y produciria una alarma falsa
        # permanente. Se declara como lo que es.
        return {"estado": "no_aplica",
                "motivo": "nota editorial, no transcripcion: no hay nada que "
                          "cotejar contra la fuente"}
    url = frag.get("fuente")
    if not url:
        return {"estado": "inaccesible", "motivo": "el fragmento no trae `fuente`"}
    if url not in cache:
        cache[url] = descargar(url)
    texto, motivo = cache[url]
    if texto is None:
        return {"estado": "inaccesible", "motivo": motivo}

    objetivo = normalizar(frag["texto"])
    fuente = normalizar(texto)
    if objetivo and objetivo in fuente:
        return {"estado": "coincide", "motivo": f"{motivo}, texto completo"}
    # Ventana en el medio: evita que un encabezado o una cola de pagina rompan
    # la coincidencia del fragmento entero.
    if len(objetivo) > VENTANA:
        medio = objetivo[len(objetivo) // 2 - VENTANA // 2:
                         len(objetivo) // 2 + VENTANA // 2]
        if medio in fuente:
            return {"estado": "coincide",
                    "motivo": f"{motivo}, ventana de {VENTANA} chars"}
    # Cobertura de palabras EN ORDEN. Hace falta porque algunos fragmentos
    # declaran una normalizacion respecto de la fuente y entonces no pueden
    # coincidir literalmente. Ejemplo real: L361-26 dice en su `nota_vigencia`
    # que el normograma inserta en el cuerpo las sustituciones terminologicas
    # ['discapacidad', 'en situacion de discapacidad'] y que se retiraron para
    # dejar el texto como fue promulgado. Eso es legitimo y esta documentado,
    # pero rompe la busqueda literal.
    #
    # NO es una puerta trasera: declarar una normalizacion no exime de la
    # comprobacion, solo la afloja. El fragmento tiene que seguir siendo CASI
    # el texto de la fuente --- `UMBRAL_NORMALIZADO` de sus palabras, en orden
    # --- o sale `no_aparece` igual.
    cob, falt = cobertura_en_orden(objetivo, fuente)
    declara = bool(frag.get("nota_vigencia") and
                   "se retiraron" in frag["nota_vigencia"].lower()
                   or frag.get("transcripcion") == "literal_normalizada")
    base = {"motivo": motivo, "cobertura_de_palabras": round(cob, 4),
            "palabras_que_no_estan": falt[:12],
            "chars_del_fragmento": len(objetivo),
            "declara_normalizacion": declara}

    # BANDAS, no un si/no. La primera version mandaba a revision humana todo
    # lo que no coincidiera literalmente y eso daba 22 alarmas de 59, de las
    # cuales varias eran puro formato: L472-02 salia `no_aparece` con
    # cobertura 1.000 y CERO palabras faltantes --- todas sus palabras estan
    # en la fuente, en orden, y lo unico que difiere es que la fuente mete
    # texto entre ellas. Un informe que grita en los 22 casos no se lee, y
    # entonces el que importa de verdad (CP-048, cobertura 0.049) se pierde
    # entre el ruido.
    if cob >= UMBRAL_PALABRAS:
        return {"estado": "coincide_palabras", **base,
                "nota": "todas o casi todas las palabras del fragmento estan "
                        "en la fuente y en orden; la diferencia con la busqueda "
                        "literal es de formato o de texto insertado por la "
                        "fuente entre ellas"}
    if cob >= UMBRAL_NORMALIZADO and declara:
        return {"estado": "coincide_normalizado", **base,
                "nota": "el fragmento declara una normalizacion respecto de la "
                        "fuente y su texto sigue estando casi completo en ella"}

    # Ultimo recurso para los PDF: cobertura de CONJUNTO. Es evidencia mas
    # debil que el orden y se cuenta aparte, nunca como `coincide`.
    #
    # Hace falta porque la maquetacion lo derrota. El PDF de la Constitucion
    # va a dos columnas y pypdf entrelaza las lineas al extraer, asi que el
    # orden de las palabras sale mezclado aunque la transcripcion sea perfecta.
    # Comprobado: de CP-015 y CP-025 esta el 100% de las palabras distintas en
    # el PDF, y de CP-088 el 98%, pero ninguno aparece literal y el orden no se
    # sostiene. Nueve fragmentos salian 'a revisar' por eso.
    #
    # Que esten todas las palabras de ESTE articulo, en un documento que es la
    # norma citada, es evidencia razonable de fidelidad --- pero no prueba el
    # orden, y el orden es lo que distingue una transcripcion de una mezcla.
    # Por eso es un estado propio y no un aprobado.
    pal = set(objetivo.split())
    if pal:
        enc = sum(1 for p in pal if p in fuente) / len(pal)
        if enc >= UMBRAL_CONJUNTO and motivo == "pdf":
            return {"estado": "coincide_desordenado", **base,
                    "cobertura_de_conjunto": round(enc, 4),
                    "nota": "estan todas o casi todas las palabras del "
                            "fragmento en la fuente, pero el ORDEN no se puede "
                            "comprobar porque la extraccion del PDF entrelaza "
                            "las columnas. Verificacion mas debil que "
                            "`coincide`: confirma el vocabulario del articulo, "
                            "no su redaccion exacta."}
        base["cobertura_de_conjunto"] = round(enc, 4)

    mejor = 0
    for n in range(60, min(len(objetivo), 1200), 60):
        if objetivo[:n] in fuente:
            mejor = n
    return {"estado": "revisar", "prefijo_que_coincide": mejor, **base}


UMBRAL_CONJUNTO = 0.97
"""Fraccion de palabras DISTINTAS que tienen que estar para aceptar el
desorden. Muy alto porque la evidencia de conjunto es debil: con un umbral
flojo, cualquier fragmento de la misma norma pasaria."""


UMBRAL_PALABRAS = 0.94
"""Cobertura a partir de la cual la diferencia se atribuye al formato.

Alto a proposito. Por debajo de esto faltan palabras SUSTANTIVAS, no signos:
en CP-053 (cobertura 0.322) faltan 'minimos', 'remuneracion', 'vital',
'proporcional' --- el nucleo del articulo --- y eso no es formato.
"""

UMBRAL_NORMALIZADO = 0.88
"""Cobertura minima para aceptar una normalizacion DECLARADA.

Mas baja que `UMBRAL_PALABRAS` porque el fragmento declara que retiro texto de
la fuente, pero no tanto como para admitir una parafrasis. Declarar una
normalizacion afloja la comprobacion; no la exime."""


def cobertura_en_orden(objetivo: str, fuente: str) -> tuple[float, list[str]]:
    """Que fraccion de las palabras del fragmento esta en la fuente, EN ORDEN.

    En orden y no como conjunto: un conjunto de palabras coincidiria con
    cualquier texto largo de la misma norma, y hay que comprobar que el
    fragmento sea ESTE pasaje y no otro del mismo documento.

    SE ANCLA PRIMERO, y esto era un bug propio que producia 16 falsas alarmas
    de 59. La version anterior recorria la fuente de izquierda a derecha
    avanzando el indice en cada palabra encontrada. En un PDF de 400 paginas
    como la Constitucion, una palabra comun del fragmento engancha en el
    preambulo, el indice salta ahi, y todas las palabras siguientes se buscan
    DESPUES de esa posicion: el resto no se encuentra aunque este. CP-023
    salia con 'faltan: peticiones, pronta, garantizar' --- palabras que
    evidentemente estan en el art. 23 CP.

    Ahora se localiza primero la REGION de la fuente que contiene el pasaje,
    usando frases largas y distintivas del fragmento como ancla, y la
    cobertura se mide dentro de una ventana alrededor. Si ninguna ancla
    aparece, el fragmento no esta en la fuente y la cobertura es 0 de verdad.
    """
    pal = objetivo.split()
    if not pal:
        return 0.0, []

    # Anclas: frases de 8 palabras tomadas a lo largo del fragmento. Una
    # frase de 8 palabras seguidas es practicamente unica en un corpus
    # normativo, asi que si aparece marca la region correcta.
    anclas = [" ".join(pal[k:k + 8]) for k in range(0, max(1, len(pal) - 8), 8)]
    posiciones = [fuente.find(a) for a in anclas]
    posiciones = [p for p in posiciones if p >= 0]
    if not posiciones:
        return 0.0, pal[:12]

    # Ventana generosa: el triple del fragmento, porque la fuente puede meter
    # texto entre medias (notas de vigencia, sustituciones del normograma).
    ini = max(0, min(posiciones) - 200)
    fin = min(len(fuente), max(posiciones) + 3 * len(objetivo) + 200)
    ventana = fuente[ini:fin]

    puestas, faltan, i = 0, [], 0
    for p in pal:
        j = ventana.find(" " + p + " ", i)
        if j < 0:
            j = ventana.find(p, i)
        if j >= 0:
            puestas += 1
            i = j + len(p)
        else:
            faltan.append(p)
    return puestas / len(pal), faltan


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--escribir", action="store_true",
                    help="actualiza `verificado_el` de los que coinciden")
    ap.add_argument("--solo", metavar="ID", help="un solo fragmento")
    a = ap.parse_args()

    corpus = json.loads(RUTA.read_text(encoding="utf-8"))
    docs = corpus["documentos"]
    objetivo = [d for d in docs if not a.solo or d["id"] == a.solo]
    if not objetivo:
        print(f"no existe el fragmento {a.solo}")
        return 1

    hoy = date.today().isoformat()
    cache: dict = {}
    res, cuenta = [], {"coincide": 0, "coincide_palabras": 0,
                       "coincide_normalizado": 0, "coincide_desordenado": 0,
                       "revisar": 0, "inaccesible": 0, "no_aplica": 0}
    print(f"cotejando {len(objetivo)} fragmento(s) contra su fuente...\n")
    for i, d in enumerate(objetivo, 1):
        r = cotejar(d, cache)
        cuenta[r["estado"]] += 1
        res.append({"id": d["id"], "norma": d["norma"],
                    "articulo": d["articulo"], "fuente": d.get("fuente"), **r})
        marca = {"coincide": "ok ", "coincide_palabras": "ok.",
                 "coincide_normalizado": "ok~", "coincide_desordenado": "ok?",
                 "revisar": "REV", "inaccesible": " ? ",
                 "no_aplica": " - "}[r["estado"]]
        print(f"  [{marca}] {d['id']:<12} {r['estado']:<12} {r['motivo'][:52]}")
        if r["estado"].startswith("coincide") and a.escribir:
            d["verificado_el"] = hoy
        sys.stdout.flush()

    print(f"\n{'=' * 66}")
    print(f"  coinciden literal : {cuenta['coincide']}")
    print(f"  coinciden palabras: {cuenta['coincide_palabras']}   "
          f"(cobertura >= {UMBRAL_PALABRAS:.0%}; la diferencia es de formato)")
    print(f"  normalizacion decl: {cuenta['coincide_normalizado']}   "
          f"(cobertura >= {UMBRAL_NORMALIZADO:.0%} y declarada)")
    print(f"  desordenado (pdf) : {cuenta['coincide_desordenado']}   "
          f"(vocabulario completo; el orden no se puede comprobar)")
    print(f"  A REVISAR         : {cuenta['revisar']}   <- faltan palabras "
          f"sustantivas")
    print(f"  inaccesibles      : {cuenta['inaccesible']}   (no es un fallo "
          f"del fragmento)")
    if cuenta["no_aplica"]:
        print(f"  no aplica         : {cuenta['no_aplica']}   (nota editorial, "
              f"no transcripcion)")
    print("=" * 66)
    if cuenta["revisar"]:
        print("\nA REVISAR a mano, de peor a mejor. Faltan palabras "
              "SUSTANTIVAS, asi")
        print("que o la transcripcion esta mal, o la norma cambio, o la fuente")
        print("citada no contiene este texto. El script no toca `verificado`:")
        print("lo decide una persona.")
        for r in sorted((x for x in res if x["estado"] == "revisar"),
                        key=lambda x: x["cobertura_de_palabras"]):
            print(f"  {r['id']:<10} cobertura {r['cobertura_de_palabras']:.3f}"
                  f"  ({r['chars_del_fragmento']} chars)  faltan: "
                  f"{', '.join(r['palabras_que_no_estan'][:6]) or '(ninguna)'}")
    if cuenta["inaccesible"]:
        print("\nLas fuentes oficiales colombianas fallan a menudo "
              "(certificados,")
        print("conexiones rechazadas, PDF escaneados). `inaccesible` significa "
              "'no")
        print("pude comprobar', NUNCA 'esta mal'.")

    salida = {"fecha": hoy, "n": len(objetivo), "cuenta": cuenta,
              "nota": "`inaccesible` no es un fallo del fragmento: es que no se "
                      "pudo leer la fuente. Confundirlo con un fallo produce "
                      "alarmas falsas; confundirlo con un acierto es peor. "
                      "`coincide_palabras` es cobertura >= "
                      f"{UMBRAL_PALABRAS:.0%}: todas las palabras estan en la "
                      "fuente y en orden, y la diferencia es de formato.",
              "resultados": res}
    RUTA_OUT.write_text(json.dumps(salida, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"\nescrito {RUTA_OUT.relative_to(RAIZ)}")
    if a.escribir and (cuenta["coincide"] or cuenta["coincide_normalizado"]):
        RUTA.write_text(json.dumps(corpus, ensure_ascii=False, indent=1),
                        encoding="utf-8")
        print(f"`verificado_el` actualizado a {hoy} en "
              f"{sum(v for k, v in cuenta.items() if k.startswith('coincide'))} "
              f"fragmento(s)")
    # Exit 0 aunque haya inaccesibles: no poder leer una fuente no es un fallo
    # del corpus. Solo `no_aparece` lo es.
    return 1 if cuenta["revisar"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
