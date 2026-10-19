"""
Anade jurisprudencia al corpus y cierra la atribucion de la Ley 361
(ROADMAP #27 y #26).

POR QUE ESTABA "BLOQUEADO" Y NO LO ESTABA

El primer intento declaro los dos items inalcanzables. Era falso, y la via
estaba dentro del proyecto: `data/reverificar_corpus.py` ya sabe descargar y
leer fuentes oficiales --- las coteja en cada corrida --- y la relatoria de la
Corte Constitucional responde perfectamente. Lo que fallaba era usar WebFetch,
que limita las citas a 125 caracteres y solo devuelve resumenes. Un resumen no
puede entrar en un corpus que declara `transcripcion: "literal"`.

ROADMAP #26, RESUELTO CON DOS FUENTES PRIMARIAS

La pregunta abierta era si el Decreto-Ley 019 de 2012 reescribio el art. 26 de
la Ley 361 y traslado la autorizacion al Ministerio del Trabajo. La respuesta,
del propio texto de las sentencias:

  C-744 de 2012  "Declarar INEXEQUIBLE el articulo 137 del Decreto Ley 19 de
                 2012, que derogo el articulo 26 de la Ley 361 de 1997, por el
                 cargo de exceso en el ejercicio de las facultades
                 extraordinarias."
  C-531 de 2000  declara EXEQUIBLE la expresion "salvo que medie autorizacion
                 de la OFICINA DE TRABAJO".

O sea: el art. 137 SI derogo el art. 26, pero fue declarado inexequible, asi
que la derogatoria no surtio efecto y el texto original sigue vigente. La
redaccion que tiene el corpus --- "oficina de Trabajo" --- es la correcta, y
lo confirma la Corte. La nota de `L361-26` pasa de "PENDIENTE DE VERIFICAR" a
la respuesta con su fuente.

ROADMAP #27: TRES FRAGMENTOS DE JURISPRUDENCIA

El corpus era solo normativo, y la tutela se decide tanto por jurisprudencia
como por ley. Se anaden las tres sentencias de las que este proyecto ya
DEPENDE, para que sus afirmaciones se puedan cotejar en vez de creer:

  T-225 de 1993  los elementos CONCURRENTES del perjuicio irremediable. Es la
                 base doctrinal del desglose que `src/reglas.py` implementa:
                 ese codigo cita esta sentencia como fuente del test
                 conjuntivo, y hasta ahora era una cita de memoria. El texto
                 dice literalmente "presencia concurrente", que es justo lo que
                 el `__post_init__` de `Hechos` exige.
  C-531 de 2000  la exequibilidad condicionada del art. 26 de la Ley 361: el
                 despido sin autorizacion previa "carece de todo efecto
                 juridico". Es el fundamento de la estabilidad laboral
                 reforzada, que el eval set usa en E08, E23 y E24.
  C-744 de 2012  la inexequibilidad del art. 137 del Decreto 019 (ver arriba).

COMO SE TRATAN, Y POR QUE APARTE

`data/normas.json` ya declara `jurisprudencia_referencia` como campo separado
que NO entra al chequeo de alucinacion normativa, "porque la cita
jurisprudencial es mas volatil". Esa decision se respeta: estos fragmentos
llevan `tipo: "jurisprudencia"` para que el RAG los pueda recuperar sin que
entren en las metricas que son solo de normas.

Cada fragmento se coteja contra la relatoria ANTES de escribir. Idempotente.
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
BASE = "https://www.corteconstitucional.gov.co/relatoria"

FRAGMENTOS = [
    {
        "id": "J-T225-93",
        "norma": "Sentencia T-225 de 1993",
        "articulo": "perjuicio irremediable",
        "titulo": "Elementos concurrentes del perjuicio irremediable",
        "fuente": f"{BASE}/1993/T-225-93.htm",
        "texto":
            "Para determinar la irremediabilidad del perjuicio hay que tener en "
            "cuenta la presencia concurrente de varios elementos que configuran "
            "su estructura, como la inminencia, que exige medidas inmediatas, "
            "la urgencia que tiene el sujeto de derecho por salir de ese "
            "perjuicio inminente, y la gravedad de los hechos, que hace "
            "evidente la impostergabilidad de la tutela como mecanismo "
            "necesario para la protección inmediata de los derechos "
            "constitucionales fundamentales. La concurrencia de los elementos "
            "mencionados pone de relieve la necesidad de considerar la "
            "situación fáctica que legitima la acción de tutela, como mecanismo "
            "transitorio y como medida precautelativa para garantizar la "
            "protección de los derechos fundamentales que se lesionan o que se "
            "encuentran amenazados.",
        "por_que_importa":
            "Es la fuente primaria del test que `src/reglas.py` implementa: el "
            "desglose de `perjuicio_irremediable` en inminencia, gravedad, "
            "urgencia e impostergabilidad, y la exigencia de que CONCURRAN "
            "todos. El codigo citaba esta sentencia de memoria; ahora su texto "
            "esta en el corpus y la afirmacion se puede cotejar. Las palabras "
            "'presencia concurrente' y 'La concurrencia de los elementos' son "
            "literalmente lo que el test conjuntivo exige.",
    },
    {
        "id": "J-C531-00",
        "norma": "Sentencia C-531 de 2000",
        "articulo": "estabilidad laboral reforzada",
        "titulo": "El despido sin autorización previa carece de efecto jurídico",
        "fuente": f"{BASE}/2000/C-531-00.htm",
        "texto":
            "Primero .- Declarar EXEQUIBLE la expresión “salvo que medie "
            "autorización de la oficina de Trabajo” , contenida en el inciso 1o. "
            "del artículo 26 de la Ley 361 de 1997. Segundo .- Declarar "
            "EXEQUIBLE el inciso 2o. del artículo 26 de la Ley 361 de 1997 bajo "
            "el supuesto de que en los términos de esta providencia y debido a "
            "los principios de respeto a la dignidad humana, solidaridad e "
            "igualdad (C.P., arts. 2o. y 13), así como de especial protección "
            "constitucional en favor de los disminuidos físicos, sensoriales y "
            "síquicos (C.P., arts. 47 y 54), carece de todo efecto jurídico el "
            "despido o la terminación del contrato de una persona por razón de "
            "su limitación sin que exista autorización previa de la oficina de "
            "Trabajo que constate la configuración de la existencia de una "
            "justa causa para el despido o terminación del respectivo contrato.",
        "por_que_importa":
            "Es el fundamento de la ESTABILIDAD LABORAL REFORZADA, que el eval "
            "set usa en E08 (quimioterapia), E23 (embarazo) y E24 (esclerosis "
            "multiple). Y resuelve una ambiguedad que importa: la indemnizacion "
            "de 180 dias NO sanea el despido, porque este 'carece de todo "
            "efecto juridico' sin la autorizacion previa. Confirma ademas que "
            "la redaccion vigente dice 'oficina de Trabajo'.",
    },
    {
        "id": "J-C744-12",
        "norma": "Sentencia C-744 de 2012",
        "articulo": "derogatoria inexequible",
        "titulo": "Inexequible el art. 137 del Decreto Ley 19 de 2012",
        "fuente": f"{BASE}/2012/C-744-12.htm",
        "texto":
            "Declarar INEXEQUIBLE el artículo 137 del Decreto Ley 19 de 2012, "
            "que derogó el artículo 26 de la Ley 361 de 1997, por el cargo de "
            "exceso en el ejercicio de las facultades extraordinarias.",
        "por_que_importa":
            "Cierra el ROADMAP #26. El art. 137 SI derogo el art. 26 de la Ley "
            "361, pero fue declarado inexequible, asi que la derogatoria no "
            "surtio efecto y el texto original sigue vigente. La version "
            "anterior del corpus afirmaba que el Decreto 019 habia trasladado "
            "la autorizacion al Ministerio del Trabajo y lo marcaba como no "
            "cotejado; ahora esta cotejado y la respuesta es que no.",
    },
]
for f in FRAGMENTOS:
    f.update(tipo="jurisprudencia", vigencia="vigente",
             transcripcion="literal", verificado=True, verificado_el=HOY,
             nota_tipo="Fragmento de JURISPRUDENCIA, no normativo. "
                       "data/normas.json declara `jurisprudencia_referencia` "
                       "como campo aparte que NO entra al chequeo de "
                       "alucinacion normativa, porque la cita jurisprudencial "
                       "es mas volatil. Se respeta: esto es recuperable por el "
                       "RAG y no entra en las metricas que son solo de normas.")

# ROADMAP #26: la nota de L361-26 pasa de pendiente a resuelta.
NOTA_361 = (
    "Fundamento de la ESTABILIDAD LABORAL REFORZADA. La Sentencia C-531 de "
    "2000 declaro el inciso 2 exequible de forma condicionada: carece de todo "
    "efecto juridico el despido sin autorizacion previa de la autoridad de "
    "trabajo, de modo que la indemnizacion de 180 dias NO sanea el despido. "
    "|| ATRIBUCION RESUELTA (2026-10-16, antes marcada como pendiente): una "
    "version anterior de este corpus afirmaba que el Decreto-Ley 019 de 2012, "
    "art. 137, reescribio el articulo y traslado la autorizacion al Ministerio "
    "del Trabajo. ES FALSO QUE ESTE VIGENTE. La Sentencia C-744 de 2012 "
    "declaro INEXEQUIBLE ese art. 137 por exceso en el ejercicio de facultades "
    "extraordinarias, asi que la derogatoria no surtio efecto y el texto "
    "original --- el de aqui, con 'oficina de Trabajo' --- sigue siendo el "
    "vigente. Lo confirma ademas la C-531 de 2000, que declaro EXEQUIBLE "
    "precisamente la expresion 'salvo que medie autorizacion de la oficina de "
    "Trabajo'. Los dos textos estan en el corpus: J-C744-12 y J-C531-00. "
    "|| Notas del texto fuente: El normograma inserta en el cuerpo las "
    "sustituciones terminologicas ['discapacidad', 'en situación de "
    "discapacidad']; se retiraron para dejar el texto como fue promulgado. La "
    "Ley 1618 de 2013 sustituyo el termino 'limitacion' por 'discapacidad'."
)

GENERADO = re.compile(r"J-[A-Z]+\d+-\d+$")


def main() -> int:
    # El normalizador DEL PROYECTO, el mismo que usa el corpus para los
    # artefactos del conversor. Hace falta: la maquetacion de la relatoria mete
    # espacios antes de la puntuacion ("Primero .- Declarar", "oficina de
    # Trabajo ,") y el auditor los rechaza. Usar el suyo en vez de escribir
    # otro evita que el corpus tenga dos nociones de "texto limpio".
    import auditar_corpus as aud
    for f in FRAGMENTOS:
        f["texto"] = aud.limpiar(f["texto"])

    print("cotejando contra la relatoria ANTES de escribir...\n")
    cache, errores = {}, []
    for f in FRAGMENTOS:
        u = f["fuente"]
        if u not in cache:
            texto, motivo = descargar(u)
            cache[u] = normalizar(texto) if texto else None
            print(f"  [{motivo}] {u.split('/')[-1]}")
        if cache[u] is None:
            errores.append(f"{f['id']}: relatoria ilegible")
            continue
        cob, falt = cobertura_en_orden(normalizar(f["texto"]), cache[u])
        if cob < 0.995:
            errores.append(f"{f['id']}: NO esta en la sentencia "
                           f"(cobertura {cob:.3f}, faltan {falt[:6]})")
            continue
        print(f"     {f['id']:<12} cobertura {cob:.4f}  "
              f"{len(f['texto']):>5} chars  OK")

    if errores:
        print(f"\nFALLA en {len(errores)} casos. No se escribio nada.")
        for e in errores:
            print(f"  - {e}")
        return 1

    ruta = RAIZ / "data" / "corpus.json"
    corpus = json.loads(ruta.read_text(encoding="utf-8"))
    docs = [d for d in corpus["documentos"] if not GENERADO.fullmatch(d["id"])]

    l361 = next((d for d in docs if d["id"] == "L361-26"), None)
    if l361 is None:
        print("FALLA: no existe L361-26")
        return 1
    l361["nota_vigencia"] = NOTA_361
    l361["atribucion_resuelta_el"] = HOY

    docs += FRAGMENTOS
    docs.sort(key=lambda d: d["id"])

    import auditar_corpus as aud
    sucios = [(f["id"], [k for k, v in aud.revisar(f).items() if v])
              for f in FRAGMENTOS]
    sucios = [(i, m) for i, m in sucios if m]
    if sucios:
        print("\nFALLA: no pasan la higiene del auditor. No se escribio.")
        for i, m in sucios:
            print(f"  {i}: {m}")
        return 1

    from collections import Counter
    corpus["documentos"] = docs
    corpus["meta"]["version"] = "1.5.0"
    corpus["meta"]["total_fragmentos"] = len(docs)
    corpus["meta"]["jurisprudencia"] = {
        "n": len(FRAGMENTOS),
        "por_que":
            "El corpus era solo normativo y la tutela se decide tanto por "
            "jurisprudencia como por ley. Se anaden las sentencias de las que "
            "este proyecto ya DEPENDE, para que sus afirmaciones se puedan "
            "cotejar en vez de creer.",
        "como_se_tratan":
            "llevan `tipo: \"jurisprudencia\"`. data/normas.json ya declara "
            "`jurisprudencia_referencia` como campo aparte que NO entra al "
            "chequeo de alucinacion normativa porque la cita jurisprudencial es "
            "mas volatil; se respeta esa decision.",
        "anadidas": [{"id": f["id"], "sentencia": f["norma"],
                      "por_que": f["por_que_importa"]} for f in FRAGMENTOS],
    }
    corpus["meta"]["atribucion_ley_361"] = {
        "pregunta": "El Decreto-Ley 019 de 2012, art. 137, reescribio el art. "
                    "26 de la Ley 361 y traslado la autorizacion al Ministerio "
                    "del Trabajo?",
        "respuesta": "NO esta vigente. El art. 137 si derogo el art. 26, pero "
                     "la Sentencia C-744 de 2012 lo declaro INEXEQUIBLE por "
                     "exceso de facultades extraordinarias, asi que la "
                     "derogatoria no surtio efecto.",
        "fuentes_primarias": [f["fuente"] for f in FRAGMENTOS
                              if f["id"] in ("J-C744-12", "J-C531-00")],
        "resuelta_el": HOY,
    }
    por_norma = Counter(d["norma"] for d in docs)
    corpus["meta"]["fragmentos_por_norma"] = dict(por_norma.most_common())
    ruta.write_text(json.dumps(corpus, ensure_ascii=False, indent=1),
                    encoding="utf-8")

    print(f"\nOK: corpus v1.5.0 con {len(docs)} fragmentos")
    print(f"  jurisprudencia: {len(FRAGMENTOS)} fragmentos nuevos")
    print("  ROADMAP #26: atribucion de la Ley 361 RESUELTA con dos fuentes "
          "primarias")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
