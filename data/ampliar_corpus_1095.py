"""
Cierra el cuello de botella de la Ley 1095 de 2006 (ROADMAP #24).

POR QUE ESTABA "BLOQUEADO" Y NO LO ESTABA

El primer intento lo declaro inalcanzable porque WebFetch no sirve para esto:
tiene un limite de 125 caracteres por cita, asi que devuelve resumenes, y un
resumen no puede entrar en un corpus que declara `transcripcion: "literal"`.

Pero `data/reverificar_corpus.py` ya sabia leer estas fuentes --- las coteja
en cada corrida --- y de hecho L1095-01 verifico contra esta misma URL. La via
estaba dentro del proyecto y no se vio. Este script reutiliza `descargar()`,
la MISMA funcion que verifica el corpus, de modo que lo que se transcribe aqui
es exactamente lo que alli se comprueba.

EL HUECO QUE CIERRA

La Ley 1095 tenia **1 fragmento** (art. 1, la definicion) y se cita **25
veces**. Es la ley que regula todo el procedimiento del habeas corpus, y el
corpus solo podia respaldar con ella la definicion. Los ocho casos de habeas
corpus del eval v2 preguntan por el TERMINO (E31: 48 horas sin juez), por la
PROLONGACION (A10: pena cumplida), por quien puede pedirlo (A14: un tercero
por una persona retenida por particulares) --- nada de lo cual estaba.

Se anaden los cuatro articulos que sostienen esas respuestas:

  art. 2  Competencia: cualquier juez, y cada integrante de una corporacion
          cuenta como juez individual.
  art. 3  Garantias: el termino de TREINTA Y SEIS HORAS, que la accion la
          puede invocar un tercero sin mandato, y que procede en cualquier
          tiempo mientras la violacion persista.
  art. 5  Tramite: reparto inmediato, no hay recusacion, la entrevista con la
          persona privada de la libertad.
  art. 6  Decision: demostrada la violacion, liberacion INMEDIATA por auto
          interlocutorio sin recurso.

LA NORMALIZACION, DECLARADA

El normograma de Cancilleria intercala en el cuerpo del articulado los enlaces
de su propia navegacion: "Notas de Vigencia", "Concordancias", "Texto del
Proyecto de Ley Anterior", "Legislacion Anterior". No son texto de la ley: son
botones de la pagina que el conversor a texto deja caer entre las frases. Se
retiran, igual que L361-26 retira las sustituciones terminologicas del
normograma, y queda declarado en cada fragmento.

El script COMPRUEBA la transcripcion contra la fuente antes de escribir: si lo
que va a guardar no esta en el documento, falla y no toca el corpus.
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

FUENTE = "https://cancilleria.gov.co/normograma/compilacion/docs/ley_1095_2006.htm"
HOY = date.today().isoformat()

# El cromo de navegacion que el normograma intercala en el articulado.
CROMO = (
    "Notas de Vigencia",
    "Concordancias",
    "Texto del Proyecto de Ley Anterior",
    "Legislacion Anterior",
    "Legislación Anterior",
    "Jurisprudencia Vigencia",
)

NORMALIZACION = (
    "El normograma de Cancilleria intercala en el cuerpo del articulado los "
    "enlaces de su propia navegacion ('Notas de Vigencia', 'Concordancias', "
    "'Texto del Proyecto de Ley Anterior'). No son texto de la ley sino "
    "botones de la pagina que el conversor deja caer entre las frases; se "
    "retiraron. Ni una palabra del articulado se modifico."
)

ARTICULOS = {
    "2": ("Competencia para resolver el habeas corpus",
          "COMPETENCIA. La competencia para resolver solicitudes de Hábeas "
          "Corpus se establecerá de acuerdo con las siguientes reglas: 1. Son "
          "competentes para resolver la solicitud de Hábeas Corpus todos los "
          "jueces y tribunales de la Rama Judicial del Poder Público. 2. Cuando "
          "se interponga ante una Corporación, se tendrá a cada uno de sus "
          "integrantes como juez individual para resolver las acciones de "
          "Hábeas Corpus. Si el juez al que le hubiere sido repartida la acción "
          "ya hubiere conocido con antelación sobre la actuación judicial que "
          "origina la solicitud de Hábeas Corpus, deberá declararse impedido "
          "para resolver sobre esta y trasladar las diligencias, de inmediato, "
          "al juez siguiente –o del municipio más cercano– de la misma "
          "jerarquía, quien deberá fallar sobre la acción dentro de los "
          "términos previstos para ello."),
    "3": ("Garantías para el ejercicio del habeas corpus",
          "GARANTÍAS PARA EL EJERCICIO DE LA ACCIÓN CONSTITUCIONAL DE HÁBEAS "
          "CORPUS. Quien estuviera ilegalmente privado de su libertad tiene "
          "derecho a las siguientes garantías: 1. Invocar ante cualquier "
          "autoridad judicial competente el Hábeas Corpus para que este sea "
          "resuelto en un término de treinta y seis (36) horas. 2. A que la "
          "acción pueda ser invocada por terceros en su nombre, sin necesidad "
          "de mandato alguno. 3. A que la acción pueda ser invocada en "
          "cualquier tiempo, mientras que la violación persista. Para ello, "
          "dentro de los tres (3) meses siguientes a la entrada en vigencia de "
          "la presente ley, el Consejo Superior de la Judicatura reglamentará "
          "un sistema de turnos judiciales para la atención de las solicitudes "
          "de Hábeas Corpus en el país, durante las veinticuatro (24) horas del "
          "día, los días feriados y las épocas de vacancia judicial. 4. A que "
          "la actuación no se suspenda o aplace por la interposición de días "
          "festivos o de vacancia judicial. 5. A que la Defensoría del Pueblo y "
          "la Procuraduría General de la Nación invoquen el Hábeas Corpus en su "
          "nombre."),
    "5": ("Trámite del habeas corpus",
          "TRÁMITE. En los lugares donde haya dos (2) o más autoridades "
          "judiciales competentes de la misma categoría, la petición de Hábeas "
          "Corpus se someterá a reparto inmediato entre dichos funcionarios. La "
          "autoridad judicial a quien corresponda conocer del Hábeas Corpus no "
          "podrá ser recusada en ningún caso; una vez recibida la solicitud, se "
          "podrá decretar una inspección a las diligencias que pudieren existir "
          "en el asunto que dio origen a la petición. También podrá solicitar "
          "del respectivo director del centro de reclusión, y de las "
          "autoridades que considere pertinentes, información urgente sobre "
          "todo lo concerniente a la privación de la libertad. La falta de "
          "respuesta inmediata a estas solicitudes constituirá falta gravísima. "
          "La autoridad judicial competente procurará entrevistarse en todos "
          "los casos con la persona en cuyo favor se instaura la acción de "
          "Hábeas Corpus. Para ello se podrá ordenar que aquella sea presentada "
          "ante él, con el objeto de entrevistarla y verificar los hechos "
          "consignados en la petición. Con este mismo fin, podrá trasladarse al "
          "lugar donde se encuentra la persona en cuyo favor se instauró la "
          "acción, si existen motivos de conveniencia, seguridad u oportunidad "
          "que no aconsejen el traslado de la persona a la sede judicial. Con "
          "todo, la autoridad judicial podrá prescindir de esa entrevista, "
          "cuando no la considere necesaria. Los motivos de esta decisión "
          "deberán exponerse en la providencia que decida acerca del Hábeas "
          "Corpus."),
    "6": ("Decisión: liberación inmediata",
          "DECISIÓN. Demostrada la violación de las garantías constitucionales "
          "o legales, la autoridad judicial competente inmediatamente ordenará "
          "la liberación de la persona privada de la libertad, por auto "
          "interlocutorio contra el cual no procede recurso alguno."),
}

POR_QUE = {
    "2": "Los ocho casos de habeas corpus del eval set preguntan ante quien se "
         "pide. Hasta ahora el corpus solo tenia la definicion del art. 1.",
    "3": "Es el articulo del TERMINO DE 36 HORAS y el que dice que un tercero "
         "puede invocarlo sin mandato. Sostiene E31 (48 horas sin juez de "
         "control de garantias) y A14 (un hermano pide por su madre retenida "
         "en una clinica privada).",
    "5": "El tramite, incluida la entrevista con la persona privada de la "
         "libertad y el deber de informacion del director del centro de "
         "reclusion. Sostiene E37 y A13.",
    "6": "La consecuencia: liberacion INMEDIATA por auto sin recurso. Es lo "
         "que el sistema tiene que concluir en A10 (pena cumplida) y E38 "
         "(retenido por no pagar la multa).",
}

GENERADO = re.compile(r"L1095-0(2|3|5|6)$")


def limpiar(t: str) -> str:
    for c in CROMO:
        t = t.replace(c, " ")
    return re.sub(r"\s+", " ", t).strip()


def main() -> int:
    print("descargando la fuente para cotejar ANTES de escribir...")
    texto, motivo = descargar(FUENTE)
    if texto is None:
        print(f"FALLA: no se pudo leer la fuente ({motivo}). No se escribio.")
        return 1
    fuente_norm = normalizar(texto)
    print(f"  leida ({motivo}, {len(texto)} chars)\n")

    nuevos, errores = [], []
    for num, (titulo, crudo) in ARTICULOS.items():
        t = limpiar(crudo)
        for c in CROMO:
            if c.lower() in t.lower():
                errores.append(f"art. {num}: quedo cromo del normograma: {c}")
        cob, falt = cobertura_en_orden(normalizar(t), fuente_norm)
        if cob < 0.995:
            errores.append(
                f"art. {num}: la transcripcion NO esta en la fuente "
                f"(cobertura {cob:.3f}, faltan {falt[:6]})")
            continue
        print(f"  art. {num:<3} cobertura {cob:.4f}  {len(t):>5} chars  OK")
        nuevos.append({
            "id": f"L1095-{int(num):02d}",
            "norma": "Ley 1095 de 2006",
            "articulo": f"art. {num}",
            "titulo": titulo,
            "texto": t,
            "fuente": FUENTE,
            "vigencia": "vigente",
            "transcripcion": "literal",
            "normalizacion": NORMALIZACION,
            "verificado": True,
            "verificado_el": HOY,
            "por_que_importa": POR_QUE[num],
        })

    if errores:
        print(f"\nFALLA en {len(errores)} articulos. No se escribio nada.")
        for e in errores:
            print(f"  - {e}")
        return 1

    ruta = RAIZ / "data" / "corpus.json"
    corpus = json.loads(ruta.read_text(encoding="utf-8"))
    docs = [d for d in corpus["documentos"] if not GENERADO.fullmatch(d["id"])]
    docs += nuevos
    docs.sort(key=lambda d: d["id"])

    sys.path.insert(0, str(RAIZ / "data"))
    import auditar_corpus as aud
    sucios = [(n["id"], [k for k, v in aud.revisar(n).items() if v])
              for n in nuevos]
    sucios = [(i, m) for i, m in sucios if m]
    if sucios:
        print("\nFALLA: no pasan la higiene del auditor. No se escribio.")
        for i, m in sucios:
            print(f"  {i}: {m}")
        return 1

    corpus["documentos"] = docs
    corpus["meta"]["version"] = "1.3.0"
    corpus["meta"]["total_fragmentos"] = len(docs)
    corpus["meta"].setdefault("ampliacion_1_3_0", {})
    corpus["meta"]["ampliacion_1_3_0"] = {
        "norma": "Ley 1095 de 2006",
        "de": 1, "a": 1 + len(nuevos),
        "veces_citada": 25,
        "anadidos": [{"id": n["id"], "articulo": n["articulo"],
                      "por_que": n["por_que_importa"]} for n in nuevos],
        "fuente": FUENTE,
        "normalizacion": NORMALIZACION,
        "como_se_consiguio":
            "El primer intento la declaro inalcanzable por usar WebFetch, que "
            "limita las citas a 125 caracteres y solo devuelve resumenes. Pero "
            "data/reverificar_corpus.py ya leia esta misma URL para cotejar "
            "L1095-01. Este script reutiliza su `descargar()`, asi que lo "
            "transcrito es exactamente lo que el verificador comprueba.",
        "cotejo_previo":
            "cada articulo se coteja contra la fuente ANTES de escribir, "
            "exigiendo cobertura de palabras >= 0.995. Si no esta, el script "
            "falla y no toca el corpus.",
    }
    ruta.write_text(json.dumps(corpus, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print(f"\nOK: corpus v1.3.0 con {len(docs)} fragmentos")
    print(f"  Ley 1095 de 2006: 1 -> {1 + len(nuevos)} fragmentos "
          f"(se cita 25 veces)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
