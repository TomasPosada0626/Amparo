"""Instrumento para cerrar fila por fila las 128 etiquetas de las clases B y C.

Por que hace falta: el dictamen de esas dos clases
(`docs/m3_articulos_gold_dictamen_claseBC.md`) dio los veredictos de forma
**agregada** -- 64/15/3 en B y 38/8/0 en C -- mas tres excepciones nombradas
una por una. No dejo constancia de que veredicto corresponde a cada fila, asi
que registrarlas exigiria deducirlo de la distribucion, que es inventarlo.

Este documento pone delante de quien revisa la consulta, el texto completo del
articulo y el estado de su fragmentacion, y **deja la casilla del veredicto
vacia** salvo en esas tres filas.

Por que importa, si ninguna mueve el acierto@5: porque **si determinan el @10 y
mas alla**. Las 82 de B y las 46 de C tienen `fue_recuperado = no`, o sea que
ninguna estuvo en el top-5 -- de ahi que no entren en el @5 --, pero un
articulo que aparece en el puesto 6 o mas abajo es, por construccion de las
clases, una fila de B o de C. Los @10, @30 y @100 de la auditoria 6.1 quedan
sujetos a cerrarlas.

    python -m tools.pendientes_bc
"""
from __future__ import annotations

from tools.validacion_articulos_gold import (
    HASH_METADATA,
    RAIZ,
    cargar_articulos,
    filas,
    texto_articulo,
)

SALIDA = RAIZ / "docs" / "m3_articulos_gold_pendientes_BC.md"

# Lo UNICO que el dictamen de las clases B y C documenta fila por fila. Todo lo
# demas va sin propuesta individual, a proposito.
NOMBRADAS = {
    ("9033", "discapacidad_estabilidad_reforzada_ley_361_1997", "26"): (
        "no_responde", "media",
        "El articulo prohibe que LA DISCAPACIDAD obstaculice una vinculacion "
        "laboral. Una incapacidad temporal por cirugia no es lo mismo, y la "
        "estabilidad laboral reforzada en incapacidad tiene otro fundamento. "
        "Es el mas discutible de los tres."),
    ("9060", "codigo_penal_ley_599_2000", "286"): (
        "no_responde", "media",
        "La falsedad ideologica en documento publico es del SERVIDOR PUBLICO "
        "que extiende el documento; quien pregunta es el contratista al que se "
        "lo piden firmar. El art. 287, falsedad en documento privado, encaja "
        "mejor y tambien esta etiquetado."),
    ("9004", "tutela_decreto_2591_1991", "1"): (
        "no_responde", "baja",
        "Es el objeto de la tutela y repite el art. 86 de la Constitucion. No "
        "aporta nada que el 86 no diga, y ninguno de los dos resuelve la "
        "demora. Es redundancia, no error."),
}

TITULOS = {
    "B_caso_fallido": (
        "Clase B -- etiquetas de casos que fallaron",
        "El articulo gold no se recupero y el caso figura como fallo. "
        "La pregunta: ¿este articulo responde la consulta?"),
    "C_redundante": (
        "Clase C -- redundantes",
        "El caso ya acerto por otro articulo. Misma pregunta, y la respuesta "
        "no cambia el acierto@5."),
}


def construir() -> str:
    fs = filas()
    por_doc = cargar_articulos()
    partes = [
        "# Clases B y C: las 128 filas que faltan por cerrar",
        "",
        "**La casilla del veredicto va vacia a proposito**, salvo en las tres "
        "filas que el dictamen de estas clases nombro individualmente. Su "
        "resumen era agregado -- 64/15/3 en B y 38/8/0 en C -- y deducir de ahi "
        "el veredicto de cada fila seria inventarlo.",
        "",
        "Ninguna de estas 128 filas cambia el **acierto@5**: las 82 de B y las "
        "46 de C tienen `fue_recuperado = no`, o sea que ninguna estuvo en el "
        "top-5, asi que su veredicto no entra en ese calculo. **Pero si "
        "determinan el acierto@10 y mas alla**, porque un articulo que aparece "
        "en el puesto 6 o mas abajo es, por construccion de las clases, una "
        "fila de B o de C.",
        "",
        f"Texto de los articulos tomado de la metadata del indice evaluado "
        f"(`hash_metadata_indice = {HASH_METADATA}`).",
        "",
        "Vocabulario: `responde` · `responde_parcial` · `no_responde` · "
        "`pendiente`. Lo que no pueda establecerse con certeza se deja en "
        "`pendiente`: un gold dudoso marcado como dudoso es informacion; "
        "forzado, es un diagnostico equivocado del sistema.",
        "",
    ]
    for clase, (titulo, nota) in TITULOS.items():
        grupo = [f for f in fs if f["clase_impacto"] == clase]
        casos = {f["case_id"] for f in grupo}
        partes += ["", "---", "", f"# {titulo}", "", nota, "",
                   f"{len(grupo)} filas en {len(casos)} casos.", ""]
        for f in grupo:
            prop = NOMBRADAS.get((f["case_id"], f["doc_id"], f["articulo"]))
            texto = texto_articulo(por_doc.get(f["doc_id"], {}).get(f["articulo"], []))
            propuesta = (
                f"**Propuesta:** `{prop[0]}` (confianza {prop[1]}) — {prop[2]}"
                if prop else
                "**Propuesta:** _(sin veredicto individual documentado: el "
                "dictamen de esta clase fue agregado)_")
            partes += [
                f"## {f['case_id']} · {f['norma'] or f['doc_id']} · articulo {f['articulo']}",
                "",
                f"**Consulta:** {f['pregunta']}",
                "",
                f"**Fragmentacion:** el articulo ocupa {f['n_chunks']} chunk(s)"
                + (" — **partido**" if f["esta_partido"] == "si" else ""),
                "",
                propuesta,
                "",
                "**Veredicto:** ______________   **Confianza:** ______",
                "",
                "**Texto del articulo:**",
                "",
                f"> {texto if texto else '(sin texto en el indice)'}",
                "",
            ]
    return "\n".join(partes) + "\n"


def main(argv=None) -> int:
    SALIDA.write_text(construir(), encoding="utf-8")
    fs = filas()
    n = sum(1 for f in fs if f["clase_impacto"] in TITULOS)
    print(f"Escrito {SALIDA.relative_to(RAIZ)} "
          f"({SALIDA.stat().st_size / 1000:.0f} KB, {n} filas)")
    print(f"con propuesta individual documentada: {len(NOMBRADAS)}")
    print(f"sin propuesta, a revisar desde cero:  {n - len(NOMBRADAS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
