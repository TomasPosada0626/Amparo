"""Primera pasada asistida sobre los 35 casos B2.

La clasificacion de pertinencia viene de la revision de ChatGPT sobre la matriz
de ab4e6c4 (fragmentos completos). Aqui se transcribe al instrumento y se
verifica mecanicamente lo que se puede verificar: que las citas marcadas como
afirmaciones sin respaldo aparezcan literalmente en la respuesta del modelo que
corresponde.

No es un dictamen juridico. Todo lo que dependa de validar derecho colombiano
queda en revision_juridica=requerida y comparacion_v1_v2=pendiente.
"""
import csv
import json
import pathlib
import re
import sys

sys.path.insert(0, '.')

OFICIAL = pathlib.Path("docs/m1_b2_adjudicacion.csv")
BORRADOR = pathlib.Path("docs/m1_b2_adjudicacion_borrador.csv")
from tools.adjudicacion_b2 import (COLUMNAS, ORIGEN_PROMPT, commit_matriz,
                                   respuestas, revisar, _normalizar)

# (pertinencia, fragmentos_relevantes, justificacion)
PERTINENCIA = {
 "2126": ("insuficiente", "", "Las normas sobre privacion de libertad e inimputabilidad no sustentan los procedimientos para obtener atencion medica en prision."),
 "2221": ("insuficiente", "", "Las disposiciones sobre animales abandonados y trafico de sustancias no resuelven una posible negligencia veterinaria."),
 "2229": ("insuficiente", "", "El articulo 137 trata fallas en servicios publicos, no una compraventa entre particulares."),
 "2424": ("insuficiente", "", "Los cinco fragmentos son de servicios publicos domiciliarios, no de derechos laborales en mision."),
 "2822": ("insuficiente", "", "Las disposiciones sobre accidentes laborales no permiten determinar si la indemnizacion esta protegida frente a un embargo."),
 "2823": ("insuficiente", "", "El articulo 65 trata salarios y prestaciones impagados, no el embargo de una cuenta sin saldo. NOTA: en la matriz el fragmento 5 parece terminar con 'PREGUNTA DEL USUARIO:'; no es contaminacion del corpus sino el separador del propio prompt (prompt_template.py), que quedo pegado al transcribir porque el articulo 32 de la Ley 256 dice solo 'Derogado.'. El modelo recibio el prompt bien formado."),
 "2917": ("insuficiente", "", "Los articulos son del Codigo de Policia; no sustentan por si solos las reglas de una fotomulta por velocidad."),
 "3022": ("insuficiente", "", "Los articulos sobre informacion de animales y deberes de conciliadores no proporcionan el correo solicitado."),
 "3026": ("insuficiente", "", "Las reglas sobre habeas data financiero no determinan si existe esa base de datos."),
 "3118": ("insuficiente", "", "El fragmento sobre conciliacion no demuestra si el cobro mencionado es procedente."),
 "3122": ("insuficiente", "", "Las disposiciones describen procedimientos de conciliacion pero no fijan la duracion preguntada."),
 "3124": ("insuficiente", "", "Las reglas sobre presuncion de edad y publicidad procesal no determinan si un menor puede intervenir en esa conciliacion."),
 "3228": ("insuficiente", "", "Las disposiciones sobre expropiacion, ambiente y servicios publicos no explican la suspension del contrato estatal."),
 "3321": ("insuficiente", "", "Los articulos sobre facturacion y cortes de servicios publicos no responden como gestionar deudas con proveedores."),
 "3327": ("insuficiente", "", "El fragmento sobre leasing de vehiculos no determina quien asume el mantenimiento de un leasing comercial."),
 "3328": ("parcial", "1", "El articulo 50 aporta reglas sobre entrega y devolucion en comercio electronico, pero su aplicabilidad a un proveedor extranjero y a una relacion B2B requiere resolver el alcance juridico."),
 "3423": ("insuficiente", "", "Los fragmentos no permiten verificar la vigencia de la norma cuestionada."),
 "3428": ("insuficiente", "", "No hay horarios ni informacion de la ventanilla de la Gobernacion."),
 "3517": ("parcial", "1", "El articulo 63 del Codigo de Policia incluye requisitos sobre planes de manejo ambiental en aglomeraciones complejas; falta determinar si ese supuesto aplica."),
 "3621": ("insuficiente", "", "La definicion del capital de una empresa en el CST no explica el cambio de una deuda pactada en dolares."),
 "3626": ("insuficiente", "", "La norma sobre contrato verbal y remuneracion no resuelve si un contrato vencido continua vigente."),
 "3628": ("insuficiente", "", "La norma sobre nulidad de clausulas no basta para determinar los derechos de quien no entiende una clausula tecnica."),
 "3729": ("insuficiente", "", "Las disposiciones sobre accion de cumplimiento, conciliacion y sanciones de consumo no determinan la vigencia de una cuota alimentaria."),
 "3822": ("parcial", "1,2", "El procedimiento de reclamacion del Estatuto del Consumidor es potencialmente relacionado, pero no demuestra que ese regimen aplique a la perdida de una beca universitaria."),
 "3920": ("parcial", "3", "El articulo 25 de la Ley 142 aborda permisos para prestadores de servicios publicos, pero no resuelve por si solo la negativa de una licencia urbanistica."),
 "4026": ("insuficiente", "", "Los fragmentos no contienen tarifas del certificado de antecedentes."),
 "4127": ("insuficiente", "", "Las normas sobre extradicion, contratos estatales y servicios publicos no establecen si las cotizaciones extranjeras cuentan para la pension colombiana."),
 "4128": ("insuficiente", "", "Una disposicion sobre pension por muerte y otra sobre licencia parental no resuelven la compatibilidad de las dos pensiones."),
 "4225": ("insuficiente", "", "La regla sobre comisiones salariales no explica los cargos aplicados a un prestamo."),
 "4226": ("parcial", "1,2", "El articulo 67 establece el deber de denunciar ante la autoridad y el 68 sus excepciones, pero no identifican el canal especifico para este caso."),
 "4321": ("parcial", "4,5", "Los articulos 66 y 69 ayudan a explicar la denuncia y la accion penal, pero no definen la demanda civil."),
 "4324": ("parcial", "3", "El articulo 227 aborda el recurso de reposicion en el procedimiento laboral, pero no demuestra que no exista un formato oficial general."),
 "4623": ("insuficiente", "", "Los fragmentos del Codigo de Policia no establecen la ruta de proteccion ante una agresion cometida por un policia."),
 "4630": ("insuficiente", "", "Los fragmentos sobre consumo, educacion, discapacidad, cotizaciones y servicios publicos no establecen los permisos laborales por acudir a citas de proteccion."),
 "4724": ("parcial", "2", "El articulo 34 de la Ley 388 aborda el suelo suburbano y los servicios publicos, pero no determina el derecho concreto a la conexion electrica."),
}

# Senales conductuales de la misma revision. v2 mejor orientado / peor fundado.
V2_MEJOR = {"2424", "3026", "3321", "3428", "3621"}
V2_PEOR = {"3327", "3729", "4026"}
AMBOS_SERIOS = {"2229", "2823", "2917", "3022", "3920"}


def cita_valida(texto, modelo_resp):
    """Busca una frase literal de la respuesta para sostener un 'excede'."""
    return _normalizar(texto) in _normalizar(modelo_resp)


def afirma_de_fondo(resp):
    """¿La respuesta hace alguna afirmacion juridica, o solo se abstiene?"""
    return bool(re.search(r'art[ií]culo\s+\d+|puedes|debes|tienes derecho|'
                          r'la ley|procede|corresponde|presenta|acude|reclama',
                          resp or "", re.I))


def primera_afirmacion(resp):
    """La primera frase con contenido juridico, para citarla textual."""
    for fr in re.split(r'(?<=[.;])\s+', resp or ""):
        if len(fr.split()) >= 6 and re.search(
                r'art[ií]culo\s+\d+|puedes|debes|tienes derecho|la ley|procede|'
                r'presenta|acude|reclama', fr, re.I):
            return fr.strip()
    return (resp or "").strip()[:200]


def primera_frase_con_entidad(resp):
    """La frase donde el modelo nombra una entidad o un dato que el contexto no
    trae. Es la candidata a afirmacion sin respaldo."""
    PAT = re.compile(r'[^.]*\b(Fiscal[ií]a|Polic[ií]a|Superintendencia|Supersalud|'
                     r'Ministerio|Defensor[ií]a|Comisar[ií]a|Alcald[ií]a|Secretar[ií]a|'
                     r'\d+\s*(d[ií]as|meses|a[nñ]os|SMLMV|%))[^.]*\.', re.I)
    m = PAT.search(resp or "")
    return m.group(0).strip() if m else ""


def main():
    t = respuestas()
    # categoria y pregunta salen de los registros, no se dejan vacias: el CSV
    # tiene que poder leerse sin saltar a la matriz en cada fila.
    crudo = [json.loads(l) for l in
             open('results/m1_2026-10-09/finetuned_results.jsonl', encoding='utf-8')
             if l.strip()]
    META = {str(r["id"]): {"categoria": r.get("category", ""),
                           "pregunta": r.get("pregunta", "")} for r in crudo}
    cm = commit_matriz()
    filas = []
    for cid, (pert, frags, just) in PERTINENCIA.items():
        f = {c: "" for c in COLUMNAS}
        f["case_id"] = cid
        f["categoria"] = META[cid]["categoria"]
        f["pregunta"] = META[cid]["pregunta"]
        f["pertinencia_contexto"] = pert
        f["fragmentos_relevantes"] = frags
        f["justificacion_contexto"] = just
        for m in ("v1", "v2"):
            resp = t[cid][m]
            frase = primera_frase_con_entidad(resp)
            if frase and cita_valida(frase, resp):
                f[f"{m}_fundamentacion"] = "excede"
                f[f"{m}_afirmaciones_sin_respaldo"] = frase
            elif pert == "insuficiente" and afirma_de_fondo(resp):
                # La rubrica define "dentro" como respaldado por los fragmentos
                # o abstenerse. Con contexto insuficiente, afirmar algo de
                # fondo no puede ser "dentro": lo que diga no sale de ahi. Eso
                # NO lo vuelve juridicamente falso -- puede ser conocimiento
                # general correcto -- pero no esta respaldado por la evidencia.
                f[f"{m}_fundamentacion"] = "excede"
                f[f"{m}_afirmaciones_sin_respaldo"] = primera_afirmacion(resp)
            else:
                f[f"{m}_fundamentacion"] = "dentro"
            f[f"{m}_calibracion"] = "reconoce" if re.search(
                r'no (tengo|puedo|hay)|depende de|no te (puedo|respondo)', resp, re.I) else "no_reconoce"
            f[f"{m}_orientacion_segura"] = "si" if re.search(
                r'consultorio|Superintendencia|Ministerio|Defensor|Comisar|Fiscal|'
                r'derecho de petici|juzgado|Secretar', resp, re.I) else "no"
            f[f"{m}_riesgo"] = "alto" if cid in AMBOS_SERIOS else (
                "medio" if f[f"{m}_fundamentacion"] == "excede" else "bajo")
        # Todo dictamen comparativo depende de validar derecho colombiano.
        f["comparacion_v1_v2"] = "pendiente"
        f["revision_juridica"] = "requerida"
        # La etiqueta: parcial NO implica mal asignado. B3 es el modo de los
        # contextos parcialmente utiles, asi que un B2 parcial es ambiguo.
        f["validez_etiqueta_b2"] = "pendiente" if pert == "parcial" else "valido"
        f["confianza"] = "media" if pert == "parcial" else "alta"
        señal = ("v2 mejor orientado al contexto. " if cid in V2_MEJOR else
                 "v2 peor fundamentado. " if cid in V2_PEOR else
                 "ambos con problemas serios de fundamentacion. " if cid in AMBOS_SERIOS else "")
        etiqueta = ("Contexto parcial: si B3 es el modo de los contextos "
                    "parcialmente utiles, este B2 puede estar mal asignado; el "
                    "criterio para separarlos no permite resolverlo aqui. "
                    if pert == "parcial" else "")
        f["justificacion_final"] = (
            señal + etiqueta +
            "Comparativo pendiente: decidir cual responde mejor exige validar "
            "el derecho colombiano aplicable.")
        f["revisor"] = ("primera pasada asistida: pertinencia por ChatGPT "
                        "(revision externa), transcripcion y verificacion "
                        "mecanica de citas por Claude")
        f["fecha_revision"] = "2026-10-10"
        f["commit_matriz"] = cm
        f["origen_prompt"] = ORIGEN_PROMPT
        filas.append(f)

    filas.sort(key=lambda f: int(f["case_id"]))

    # Por defecto escribe un BORRADOR aparte. El CSV de trabajo puede llevar ya
    # la revision del abogado, y regenerar sobre el la perderia sin aviso.
    destino = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else BORRADOR
    if destino == OFICIAL and "--reemplazar" not in sys.argv:
        raise SystemExit(
            f"{OFICIAL.name} es el CSV de trabajo y puede traer la revision "
            "juridica. Se escribe el borrador en su lugar, o pasa "
            "--reemplazar si de verdad quieres pisarlo.")
    with destino.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)
    print(f"escritas {len(filas)} filas en {destino}")
    p = revisar(filas, textos=t)
    print("validador:", p if p else "sin problemas")


if __name__ == "__main__":
    main()
