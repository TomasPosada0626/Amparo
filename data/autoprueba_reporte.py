"""Comprueba que la prosa del REPORTE no pueda contradecir a sus artefactos.

POR QUE ESTA AQUI Y NO EN `src/autoprueba_integracion.py`
    Porque `corridas.version_codigo()` hashea **todos** los `src/*.py`, y el
    archivo de pruebas es uno de ellos. Anadir una prueba ahi mueve la huella
    de codigo --- lo comprobe: `84520a06cc4e8a2a` paso a `dda6de212e018522`
    solo por registrar una funcion de test --- y eso dejaria las tres
    corridas entregadas (m1, m2, m3, todas a `84520a06cc4e8a2a`) sin codigo
    que las respalde. Una prueba no cambia ningun resultado, asi que invalidar
    la entrega para anadirla seria el peor negocio posible.

    `data/*.py` entra en el sello del manifiesto pero NO en la huella de
    codigo, asi que esto se puede correr hoy. Cuando la huella cambie por una
    razon de verdad, esta prueba se dobla dentro de la suite principal.

QUE COMPRUEBA
    La seccion 7 del reporte tenia TRES parrafos escritos a mano y los tres
    caducaron en la misma corrida:

      - 7.2 afirmaba «los dos jueces son de la misma familia» mientras
        `m2_acuerdo_entre_jueces.json` guardaba `misma_familia: false`
        (`gpt-oss` contra `allam`) en la MISMA carpeta.
      - 7.3 afirmaba que el brazo del agente «falla esa via por completo»
        cuando el F1 ya valia 0.3636: corregir `derecho_colectivo` y
        `acto_general` movio la cifra y la frase no se movio con ella.
      - 7.4 afirmaba que «los intervalos se solapan» en un estrato que **no
        publica intervalo**: `por_tipo.adversarial` trae `n` y un punto.

    Una cifra equivocada se ve. Un parrafo afirmado que ya no corresponde no
    se ve, y es el que se cita. Esto no comprueba que el texto sea bonito:
    comprueba que **cambie** cuando cambia el dato, y que no se pueda volver
    a escribir a mano.

    Uso: `python -I data/autoprueba_reporte.py`
"""
import inspect
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "data"))
import reporte  # noqa: E402

FALLOS: list[str] = []


def _brazo(nombre, f1_cumplimiento, adversarial):
    return {"sistema": nombre, "n": 63,
            "campos": {"mecanismo": {
                "f1_por_clase": {"accion_cumplimiento": f1_cumplimiento,
                                 "tutela": 0.9},
                "soporte_por_clase": {"accion_cumplimiento": 8,
                                      "tutela": 27}}},
            "por_tipo": {"gold": {"n": 45, "acierto_juridico": 0.8},
                         "adversarial": {"n": 18,
                                         "acierto_juridico": adversarial}}}


def _texto(acuerdo, f1_agente, adv_agente, adv_uno=0.8333):
    """Las tres secciones, en minusculas, contra artefactos sinteticos."""
    reporte._CACHE.clear()
    reporte._FALTAN.clear()
    reporte._CACHE["m2_acuerdo_entre_jueces.json"] = acuerdo
    reporte._CACHE["m3_scorecards_comunes.json"] = {"datos": [
        _brazo("1 · fine-tuned solo (M1)", 0.9412, adv_uno),
        _brazo("4 · agente + reglas", f1_agente, adv_agente)]}
    return ("\n".join(reporte.jueces_de_familia()).lower(),
            "\n".join(reporte.cumplimiento_en_el_agente()).lower(),
            "\n".join(reporte.adversarial_separa()).lower())


def comprobar(condicion, mensaje):
    if not condicion:
        FALLOS.append(mensaje)


BASE = {"kappa_aprueba": 0.3831, "media_a": 3.174, "media_b": 3.783,
        "modelo_a": "openai/gpt-oss-120b", "modelo_b": "allam-2-7b"}
DISTINTOS = dict(BASE, _familias={"conocido": True, "familia_a": "gpt-oss",
                                  "familia_b": "allam",
                                  "misma_familia": False})
PARIENTES = dict(BASE, _familias={"conocido": True, "familia_a": "gpt-oss",
                                  "familia_b": "gpt-oss",
                                  "misma_familia": True,
                                  "por_que_no_otra_familia": "ninguno"})


def main() -> int:
    print("=" * 78)
    print("  LA PROSA DEL REPORTE CONTRA SUS PROPIOS ARTEFACTOS")
    print("=" * 78)

    # --- 7.2 · la familia sale del artefacto, no de la memoria -----------
    j, _c, _a = _texto(DISTINTOS, 0.3636, 0.8333)
    comprobar("misma familia" not in j,
              "7.2 con `misma_familia: false` sigue diciendo «misma familia»")
    comprobar("gpt-oss" in j and "allam" in j, "7.2 no nombra los dos linajes")

    j, _c, _a = _texto(PARIENTES, 0.3636, 0.8333)
    comprobar("misma familia" in j, "7.2 con dos parientes no lo advierte")

    # Medido SIN linaje registrado no es lo mismo que NO medido. Confundir
    # los dos fue el bug de la primera version de `jueces_de_familia()`: la
    # corrida anterior trae kappa 0.6835 y ningun `_familias`.
    j, _c, _a = _texto(dict(BASE), 0.3636, 0.8333)
    comprobar("no se midio" not in j,
              "7.2 declara no medido un acuerdo que SI tiene kappa")
    comprobar("0.383" in j, "7.2 no reporta la kappa que existe")
    comprobar("misma familia" not in j,
              "7.2 afirma un linaje que nadie registro")

    # --- 7.3 · «falla por completo» solo si el F1 es 0 -------------------
    _j, c, _a = _texto(DISTINTOS, 0.0, 0.8333)
    comprobar("falla esa via por completo" in c,
              "7.3 con F1 0.000 no dice que falla por completo")
    _j, c, _a = _texto(DISTINTOS, 0.3636, 0.8333)
    comprobar("no falla por completo" in c,
              "7.3 con F1 0.3636 no se retracta de «por completo»")
    comprobar("falla esa via por completo" not in c,
              "7.3 con F1 0.3636 sigue afirmando que falla por completo")
    comprobar("0.3636" in c, "7.3 no cita el F1 medido")
    comprobar("peor" in c, "7.3 con el F1 mas bajo de la tabla no lo dice")
    _j, c, _a = _texto(DISTINTOS, 0.99, 0.8333)
    comprobar("ya no es el peor" in c,
              "7.3 no se retracta cuando el agente deja de ser el peor brazo")
    comprobar("sigue siendo" not in c,
              "7.3 lo llama el peor cuando es el mejor de la clase")

    # --- 4.4 - las citas: dos planos, y la asimetria declarada ----------
    #
    # La seccion no existia: `precision_citas` 0.5506 se calculaba, se
    # publicaba en el artefacto y NO llegaba al reporte --- la cifra mas baja
    # de M1 y la unica corroborada por una via independiente. Y al anadirla no
    # basta el agregado: esta sesgado por una asimetria del gold que NO se
    # puede corregir, porque `fundamento` es un campo congelado del puente.
    # Publicar el agregado sin esa declaracion seria publicar un numero que
    # penaliza al modelo por citar la norma correcta de la tutela.
    reporte._CACHE.clear()
    reporte._FALTAN.clear()
    reporte._CACHE["m1_scorecard_finetuned.json"] = {
        "alucinacion_normativa": {"tasa_alucinacion": 0.0},
        "pertinencia_citas": {
            "citas_emitidas": 178, "correctas": 98, "impertinentes": 80,
            "inventadas": 0, "incompletas": 0,
            "precision_citas": 0.5506, "recall_citas": 0.4135,
            "por_plano": {
                "disponible": True,
                "precision_mecanismo": 0.5682, "recall_mecanismo": 0.3876,
                "precision_derecho": 0.5556, "recall_derecho": 0.3185,
                "cajas": {"mecanismo_correcto": 50, "mecanismo_equivocado": 38,
                          "derecho_correcto": 50, "derecho_impertinente": 40},
                "ejemplos_mecanismo_equivocado": [
                    ["art. 6.1 Decreto 2591 de 1991", 26]]}}}
    c44 = chr(10).join(reporte.pertinencia_de_las_citas()).lower()
    comprobar("0.5506" in c44, "4.4 no publica `precision_citas`")
    comprobar("0.5682" in c44 and "0.5556" in c44,
              "4.4 publica el agregado sin la particion por planos, que es la "
              "unica que se puede leer")
    comprobar("art. 86 cp" in c44,
              "4.4 no declara la asimetria del gold: omite art. 86 CP en los "
              "casos de tutela, asi que penaliza al modelo por citar la norma "
              "que crea la tutela")
    comprobar("byte a byte" in c44 or "comparabilidad" in c44,
              "4.4 no dice POR QUE la asimetria no se arregla (el puente "
              "congela `fundamento`), y sin eso parece un descuido")
    comprobar("59 de 123" in c44,
              "4.4 no cita la causa establecida en `causas_abiertas.json`")
    comprobar("5 de sus 10" in c44 or "5 de 10" in c44,
              "4.4 no menciona que el abogado lo corroboro por otra via")

    # Sin el artefacto, lo dice en vez de callarlo.
    reporte._CACHE.clear()
    reporte._FALTAN.clear()
    reporte._CACHE["m1_scorecard_finetuned.json"] = {}
    c44 = chr(10).join(reporte.pertinencia_de_las_citas()).lower()
    comprobar("no se midio" in c44,
              "sin `pertinencia_citas`, 4.4 no distingue «las citas vienen al "
              "caso» de «no se comprobo»")
    reporte._CACHE.clear()
    reporte._FALTAN.clear()

    # --- 7.1 - la validacion humana se afirma solo si existe ------------
    #
    # El parrafo decia «queda abierta». Es verdad hoy y deja de serlo en
    # cuanto el abogado devuelva el formulario, y entonces el reporte
    # afirmaria una limitacion que su propio artefacto desmiente. Es el mismo
    # fallo que 7.2, 7.3 y 7.4, asi que se ata igual: los TRES estados.
    reporte._CACHE.clear()
    reporte._FALTAN.clear()
    # EL ESTADO "SIN ARTEFACTO" SE INYECTA, NO SE SIMULA BORRANDO LA CACHE.
    #
    # La version anterior limpiaba `_CACHE` y confiaba en que
    # `data/validacion_juez.json` no existiera. Dejo de funcionar en cuanto el
    # abogado devolvio el formulario: `_cargar_data` encontraba el archivo de
    # verdad y la comprobacion fallaba sobre una seccion correcta. Una prueba
    # que depende de que un archivo NO exista caduca el dia que se produce, y
    # justamente ese dia es cuando hay que seguir comprobando el otro camino.
    reporte._CACHE["data/validacion_juez.json"] = reporte.Ausente(
        "inyectado por la autoprueba")
    h = "\n".join(reporte.juez_vs_humano()).lower()
    comprobar("no esta validado" in h,
              "sin artefacto, 7.1 no declara que la validacion falta")
    comprobar("nadie lo ha rellenado" in h,
              "sin artefacto, 7.1 no dice que el formulario esta sin rellenar")
    comprobar("revision_abogado_v3" in h,
              "7.1 no distingue la validacion del JUEZ de la del GOLD, que es "
              "la confusion que ya hubo una vez (4.9/5 valido el gold)")

    # Con cifra: 7.1 deja de decir que falta y reporta el acuerdo.
    reporte._CACHE.clear()
    reporte._FALTAN.clear()
    reporte._CACHE["data/validacion_juez.json"] = {
        "acuerdo": {"concluyente": True, "n": 25, "kappa_aprueba": 0.72,
                    "corr_spearman": 0.81, "acuerdo_exacto": 0.56,
                    "acuerdo_a_un_punto": 0.92},
        "desacuerdos_de_2_o_mas": [{"id": "A07"}]}
    h = "\n".join(reporte.juez_vs_humano()).lower()
    comprobar("no esta validado" not in h,
              "7.1 sigue diciendo que no hay validacion con kappa 0.72 "
              "guardada al lado")
    comprobar("0.72" in h, "7.1 no reporta la kappa que existe")
    comprobar("sesgada a proposito" in h,
              "7.1 publica el acuerdo sin declarar que la muestra no es "
              "proporcional: la cifra se leeria como el acuerdo del eval set "
              "entero, y no lo es")
    comprobar("acuerdo, no" in h and "verdad" in h,
              "7.1 no advierte que mide acuerdo y no verdad")

    # A medias: el formulario existe y nadie lo relleno.
    reporte._CACHE.clear()
    reporte._FALTAN.clear()
    reporte._CACHE["data/validacion_juez.json"] = {
        "acuerdo": {"concluyente": False, "motivo": "ninguna nota"},
        "n_sin_nota": 25}
    h = "\n".join(reporte.juez_vs_humano()).lower()
    comprobar("sin cifra" in h or "no se completo" in h,
              "con el formulario vacio, 7.1 no distingue «no se midio» de "
              "«acuerdo bajo»")

    # --- 7.1.1 · la adherencia no se confunde con la kappa --------------
    reporte._CACHE.clear()
    reporte._FALTAN.clear()
    reporte._CACHE["m2_scorecard_finetuned.json"] = {"juez": {
        "kappa_vs_dominio": 0.361,
        "adherencia_a_la_rubrica": {"concluyente": True, "n": 103,
                                    "adherencia": 0.9417,
                                    "incumple_generoso": 4,
                                    "incumple_severo": 2}}}
    r = "\n".join(reporte.adherencia_del_juez()).lower()
    comprobar("0.361" in r, "7.1.1 no cita la kappa contra el dominio")
    comprobar("no seria una mejora" in r,
              "7.1.1 no dice que subir la kappa contra el dominio NO es una "
              "mejora: es la lectura equivocada que la seccion existe para "
              "impedir")
    comprobar("generosas" in r and "4" in r,
              "7.1.1 no separa las notas generosas de las severas")

    reporte._CACHE.clear()
    reporte._FALTAN.clear()
    reporte._CACHE["m2_scorecard_finetuned.json"] = {"juez": {
        "kappa_vs_dominio": 0.361}}
    r = "\n".join(reporte.adherencia_del_juez()).lower()
    comprobar("no se midio" in r,
              "en una corrida sin la medicion, 7.1.1 no dice que falta")
    reporte._CACHE.clear()
    reporte._FALTAN.clear()

    # --- 7.4 · un empate no es un solapamiento de intervalos ------------
    _j, _c, a = _texto(DISTINTOS, 0.3636, 0.8333, adv_uno=0.8333)
    comprobar("empatan" in a, "7.4 no ve el empate exacto")
    comprobar("los intervalos se solapan" not in a,
              "7.4 afirma un solapamiento en un estrato que no publica IC")
    comprobar("sin ic" in a, "7.4 no advierte que el estrato no trae IC")
    _j, _c, a = _texto(DISTINTOS, 0.3636, 0.5556, adv_uno=0.8333)
    comprobar("empatan" not in a, "7.4 habla de empate donde hay 28 puntos")

    # --- la ausencia se dice, no se rellena -----------------------------
    guardado = reporte.RESULTS
    try:
        reporte.RESULTS = Path(tempfile.mkdtemp())
        reporte._CACHE.clear()
        reporte._FALTAN.clear()
        j = "\n".join(reporte.jueces_de_familia()).lower()
        c = "\n".join(reporte.cumplimiento_en_el_agente()).lower()
        a = "\n".join(reporte.adversarial_separa()).lower()
        comprobar("no se midio" in j, "sin artefacto 7.2 no dice que falta")
        comprobar("no se puede sostener" in c, "sin F1 7.3 afirma igualmente")
        comprobar("no esta en la tabla" in a, "sin estrato 7.4 afirma igual")
        comprobar("m2_acuerdo_entre_jueces.json" in reporte._FALTAN,
                  "el artefacto ausente no queda registrado en _FALTAN")
    finally:
        reporte.RESULTS = guardado
        reporte._CACHE.clear()
        reporte._FALTAN.clear()

    # --- y que no se pueda volver a escribir a mano ---------------------
    fuente = inspect.getsource(reporte.construir)
    for sec in ("### 4.4", "### 7.1 ", "#### 7.1.1", "### 7.2", "### 7.3",
                "### 7.4"):
        comprobar(sec not in fuente,
                  f"la cabecera {sec} volvio a estar escrita a mano en "
                  "`construir()`: ahi no se entera de que el dato cambio, que "
                  "es exactamente lo que paso tres veces")

    print()
    if FALLOS:
        print(f"  {len(FALLOS)} comprobaciones FALLAN:")
        for f in FALLOS:
            print(f"    - {f}")
        print("=" * 78)
        return 1
    print("  7.2 sigue al artefacto en las cuatro situaciones posibles")
    print("     (familias distintas · parientes · medido sin linaje · ausente)")
    print("  7.3 sigue al F1 por clase y se retracta sola cuando deja de ser 0")
    print("  7.4 distingue un EMPATE de un solapamiento de intervalos que no")
    print("     se publican")
    print("  4.4 publica los DOS planos de la cita y declara la asimetria")
    print("     del gold que el puente de comparacion impide corregir")
    print("  7.1 solo afirma validacion humana si el artefacto existe, y")
    print("     distingue la del JUEZ de la del GOLD (4.9/5 fue el gold)")
    print("  7.1.1 dice que subir la kappa contra el dominio NO es una mejora")
    print("  las cabeceras de 7.1, 7.1.1, 7.2, 7.3 y 7.4 no se pueden volver")
    print("     a escribir a mano dentro de `construir()`")
    print()
    print("  Lo que esto NO dice: si las cifras son correctas. Comprueba que")
    print("  la PROSA siga al artefacto, no que el artefacto tenga razon.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
