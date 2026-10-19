"""
Cierra el cuello de botella de la Ley 393 y la Ley 472 (ROADMAP #24).

ESTADO ANTES

    Ley 393 de 1997   3 fragmentos (arts. 1, 8, 9)   26 citas
    Ley 472 de 1998   3 fragmentos (arts. 2, 4, 9)   25 citas

Las dos estaban mejor cubiertas que la Ley 1095 porque sus articulos clave ya
estaban: el 8 (renuencia) y el 9 (improcedibilidad frente a la tutela) de la
393 --- que es la regla que reencauzo A09 --- y el 4 de la 472, que es la
lista cerrada de derechos colectivos. Lo que faltaba era amplitud para el
retrieval, no doctrina.

LO QUE SE ANADE

    Ley 393 art. 6    Accion de cumplimiento contra PARTICULARES cuando
                      ejercen funciones publicas. Sostiene los casos donde el
                      incumplimiento lo comete un concesionario o una empresa
                      de servicios, que hoy no tenian respaldo.
    Ley 472 art. 12   Titulares: quien puede ejercer la accion popular. A18
                      pregunta exactamente eso (un usuario que denuncia un
                      sobrecosto) y A15 tambien (una veeduria).
    Ley 472 art. 15   Jurisdiccion: contenciosa cuando el demandado es publico,
                      ordinaria civil en los demas casos.

LO QUE NO SE ANADE, Y POR QUE

**Ley 393 art. 5** se queda fuera a proposito. El normograma intercala las
anotaciones de jurisprudencia DENTRO del articulo: tras la primera frase mete
un bloque de cuatro sentencias ("Jurisprudencia vigencia Corte Constitucional
- Aparte subrayado declarado EXEQUIBLE...") y el articulado se REANUDA despues
con "Si contra quien se dirige la accion no es la autoridad obligada...".
Cortar en la anotacion truncaria el articulo a la mitad, y quitar el bloque
exige cirugia fina sobre un texto que ademas lleva un `<Aparte tachado
INEXEQUIBLE>` inline. Transcribirlo bien pide leer la sentencia C-157 de 1998
para saber que aparte quedo fuera, y eso es trabajo juridico, no de script.

El criterio es el mismo de todo este corpus: **no se transcribe lo que no se
puede transcribir con seguridad**. Queda anotado, no silenciado.

Cada articulo se coteja contra la fuente ANTES de escribir. Idempotente.
"""
from __future__ import annotations
import json
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "data"))

from reverificar_corpus import cobertura_en_orden, descargar, normalizar  # noqa: E402

HOY = date.today().isoformat()

F393 = "https://www.cancilleria.gov.co/sites/default/files/Normograma/docs/pdf/ley_0393_1997.pdf"
F472 = "https://cancilleria.gov.co/sites/default/files/Normograma/docs/ley_0472_1998.htm"

CROMO = ("Jurisprudencia Vigencia", "Jurisprudencia vigencia",
         "Notas de Vigencia", "Concordancias", "Legislación Anterior",
         "Legislacion Anterior")

NORMALIZACION = (
    "El normograma intercala los enlaces de su navegacion ('Jurisprudencia "
    "Vigencia', 'Concordancias') y los apartes de anotacion de sentencias en "
    "el cuerpo del articulado. Se retiraron los que van al final del articulo. "
    "Ni una palabra del articulado se modifico. Los articulos cuyas "
    "anotaciones quedan INTERCALADAS en medio del texto no se transcribieron "
    "--- ver `meta.ampliacion_1_4_0.no_transcritos`."
)

NUEVOS = [
    {
        "id": "L393-06", "norma": "Ley 393 de 1997", "articulo": "art. 6",
        "titulo": "Acción de cumplimiento contra particulares",
        "fuente": F393,
        "texto":
            "ACCION DE CUMPLIMIENTO CONTRA PARTICULARES. La Acción de "
            "Cumplimiento procederá contra acciones u omisiones de particulares "
            "que impliquen el incumplimiento de una norma con fuerza material "
            "de Ley o Acto administrativo , cuando el particular actúe o deba "
            "actuar en ejercicio de funciones públicas, pero sólo para el "
            "cumplimiento de las mismas. En el evento contemplado en este "
            "artículo, la Acción de Cumplimiento podrá dirigirse contra el "
            "particular o contra la autoridad competente para imponerle dicho "
            "cumplimiento al particular.",
        "por_que_importa":
            "Sostiene los casos donde el deber incumplido recae en un "
            "particular que ejerce funcion publica --- un concesionario, una "
            "empresa de servicios --- que es el supuesto de A15 (las empresas "
            "de transporte que no aplican la tarifa de la ordenanza) y que no "
            "tenia ningun fragmento que lo respaldara.",
    },
    {
        "id": "L472-12", "norma": "Ley 472 de 1998", "articulo": "art. 12",
        "titulo": "Titulares de las acciones populares",
        "fuente": F472,
        "texto":
            "TITULARES DE LAS ACCIONES. Podrán ejercitar las acciones "
            "populares: 1. Toda persona natural o jurídica. 2. Las "
            "organizaciones No Gubernamentales, las Organizaciones Populares, "
            "Cívicas o de índole similar. 3. Las entidades públicas que cumplan "
            "funciones de control, intervención o vigilancia, siempre que la "
            "amenaza o vulneración a los derechos e intereses colectivos no se "
            "haya originado en su acción u omisión. 4. El Procurador General de "
            "la Nación, el Defensor del Pueblo y los Personeros Distritales y "
            "municipales, en lo relacionado con su competencia. 5. Los alcaldes "
            "y demás servidores públicos que por razón de sus funciones deban "
            "promover la protección y defensa de estos derechos e intereses.",
        "por_que_importa":
            "Responde quien puede ejercer la accion, que es justo lo que "
            "preguntan A18 (un usuario que denuncia un sobrecosto) y A15 (una "
            "veeduria municipal). El numeral 1 --- 'toda persona natural o "
            "juridica' --- es lo que desactiva la objecion de que el "
            "solicitante no es el afectado directo.",
    },
    {
        "id": "L472-15", "norma": "Ley 472 de 1998", "articulo": "art. 15",
        "titulo": "Jurisdicción competente en acciones populares",
        "fuente": F472,
        "texto":
            "JURISDICCION. La jurisdicción de lo Contencioso Administrativo "
            "conocerá de los procesos que se susciten con ocasión del ejercicio "
            "de las Acciones Populares originadas en actos, acciones u "
            "omisiones de las entidades públicas y de las personas privadas que "
            "desempeñen funciones administrativas, de conformidad con lo "
            "dispuesto en las disposiciones vigentes sobre la materia. En los "
            "demás casos, conocerá la jurisdicción ordinaria civil.",
        "por_que_importa":
            "Dice ante que jurisdiccion se lleva, que cambia segun el accionado "
            "sea publico o privado. E43 (un constructor y la autoridad "
            "ambiental) y E45 (el municipio y una fundacion) son casos mixtos.",
    },
]
for n in NUEVOS:
    n.update(vigencia="vigente", transcripcion="literal",
             normalizacion=NORMALIZACION, verificado=True, verificado_el=HOY)

NO_TRANSCRITOS = {
    "Ley 393 de 1997, art. 5": {
        "titulo": "Autoridad publica contra quien se dirige",
        "por_que_no":
            "El normograma intercala las anotaciones de jurisprudencia DENTRO "
            "del articulo: tras la primera frase mete un bloque de cuatro "
            "sentencias y el articulado se REANUDA despues con 'Si contra quien "
            "se dirige la accion no es la autoridad obligada...'. Cortar en la "
            "anotacion truncaria el articulo a la mitad. Ademas lleva un "
            "'<Aparte tachado INEXEQUIBLE>' inline, asi que transcribirlo bien "
            "exige leer la Sentencia C-157 de 1998 para saber que aparte quedo "
            "fuera. Eso es trabajo juridico, no de script.",
    },
}

GENERADO = re.compile(r"(L393-06|L472-12|L472-15)$")


def limpiar(t: str) -> str:
    """Quita el cromo del normograma y pasa el normalizador DEL PROYECTO.

    `auditar_corpus.limpiar` es el que ya usa el corpus para los artefactos del
    extractor de PDF --- el meta lo declara: "normalizado a mano para corregir
    los espacios que el extractor inserta dentro de las palabras". Usarlo aqui
    en vez de escribir otro evita que el corpus tenga dos nociones distintas
    de "texto limpio".

    Hacia falta: el art. 6 de la Ley 393 sale del PDF con un espacio antes de
    una coma ("Acto administrativo , cuando"), y el auditor lo rechaza. El
    cotejo contra la fuente es por PALABRAS, asi que normalizar la puntuacion
    no lo afecta: lo que se guarda sigue siendo lo que se verifico.
    """
    import auditar_corpus as aud
    for c in CROMO:
        t = t.replace(c, " ")
    return aud.limpiar(t)


def main() -> int:
    fuentes, errores = {}, []
    print("cotejando contra las fuentes ANTES de escribir...\n")
    for n in NUEVOS:
        u = n["fuente"]
        if u not in fuentes:
            texto, motivo = descargar(u)
            if texto is None:
                errores.append(f"{n['id']}: fuente ilegible ({motivo})")
                fuentes[u] = None
                continue
            fuentes[u] = normalizar(texto)
            print(f"  [{motivo}] {u.split('/')[-1]}")
        if fuentes[u] is None:
            continue
        n["texto"] = limpiar(n["texto"])
        for c in CROMO:
            if c.lower() in n["texto"].lower():
                errores.append(f"{n['id']}: quedo cromo del normograma: {c}")
        cob, falt = cobertura_en_orden(normalizar(n["texto"]), fuentes[u])
        if cob < 0.995:
            errores.append(f"{n['id']}: NO esta en la fuente "
                           f"(cobertura {cob:.3f}, faltan {falt[:6]})")
            continue
        print(f"     {n['id']:<10} cobertura {cob:.4f}  "
              f"{len(n['texto']):>5} chars  OK")

    if errores:
        print(f"\nFALLA en {len(errores)} casos. No se escribio nada.")
        for e in errores:
            print(f"  - {e}")
        return 1

    ruta = RAIZ / "data" / "corpus.json"
    corpus = json.loads(ruta.read_text(encoding="utf-8"))
    docs = [d for d in corpus["documentos"] if not GENERADO.fullmatch(d["id"])]
    docs += NUEVOS
    docs.sort(key=lambda d: d["id"])

    import auditar_corpus as aud
    sucios = [(n["id"], [k for k, v in aud.revisar(n).items() if v])
              for n in NUEVOS]
    sucios = [(i, m) for i, m in sucios if m]
    if sucios:
        print("\nFALLA: no pasan la higiene del auditor. No se escribio.")
        for i, m in sucios:
            print(f"  {i}: {m}")
        return 1

    from collections import Counter
    corpus["documentos"] = docs
    corpus["meta"]["version"] = "1.4.0"
    corpus["meta"]["total_fragmentos"] = len(docs)
    corpus["meta"]["ampliacion_1_4_0"] = {
        "anadidos": [{"id": n["id"], "norma": n["norma"],
                      "articulo": n["articulo"],
                      "por_que": n["por_que_importa"]} for n in NUEVOS],
        "normalizacion": NORMALIZACION,
        "no_transcritos": NO_TRANSCRITOS,
        "cotejo_previo":
            "cada articulo se coteja contra su fuente ANTES de escribir, "
            "exigiendo cobertura de palabras >= 0.995. Si no esta, el script "
            "falla y no toca el corpus.",
    }
    por_norma = Counter(d["norma"] for d in docs)
    corpus["meta"]["fragmentos_por_norma"] = dict(por_norma.most_common())
    ruta.write_text(json.dumps(corpus, ensure_ascii=False, indent=1),
                    encoding="utf-8")

    print(f"\nOK: corpus v1.4.0 con {len(docs)} fragmentos")
    print("\n  norma                       frags   citas")
    for norma, citas in (("Ley 1751 de 2015", 28), ("Ley 393 de 1997", 26),
                         ("Ley 1095 de 2006", 25), ("Ley 472 de 1998", 25)):
        print(f"  {norma:<28}{por_norma[norma]:>4}{citas:>8}")
    print(f"\n  no transcritos a proposito: {list(NO_TRANSCRITOS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
