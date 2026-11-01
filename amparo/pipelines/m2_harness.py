"""M2 · Harness de evaluacion de tres dimensiones (antes: notebooks/M2_harness.ipynb).

Corre sobre las salidas que M1 dejo en `results/m1_predicciones.json`: no
regenera nada, asi que es barato y reproducible. Va en CPU.

  1 · clasica   similitud con el gold (ROUGE-L, embeddings, accuracy, F1).
                NO mide si el derecho esta bien aplicado.
  2 · LLM-juez  calidad del razonamiento, que ninguna metrica lexica ve.
                NO es un oraculo: arrastra sesgos que hay que medir aparte.
  3 · dominio   acierto juridico, alucinacion normativa, pertinencia de las
                citas, coherencia.

Una funcion por etapa del notebook, en orden, y `correr()` las encadena:

    from amparo.pipelines import m2_harness as m2
    ctx = m2.preparar()
    m2.correr(ctx)          # o etapa por etapa, como hace el notebook
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path

from amparo.config import RESULTS
from amparo.evaluacion import acuerdo as _acuerdo
from amparo.evaluacion import harness, metricas, predicciones
from amparo.evaluacion import juez as _juez
from amparo.ejecucion import corridas, publicacion
from amparo.nucleo import schema

N_AP = 30                 # presupuesto de PARES que juzga el juez en auto-preferencia
SISTEMA_EVALUADO = "Qwen/Qwen2.5-7B-Instruct"


@dataclass
class Contexto:
    """Lo que una etapa le deja a las siguientes (antes: variables globales)."""
    c: object
    eval_set: list = field(default_factory=list)
    preds: list = field(default_factory=list)
    corrida_m1: str | None = None
    sal_base: list = field(default_factory=list)
    sal_ft: list = field(default_factory=list)
    j: object = None
    sp: dict | None = None
    sl_ambos: dict | None = None
    sl: dict | None = None
    ap: dict | None = None
    iny: dict | None = None
    val: dict | None = None
    acuerdo: dict | None = None
    sc_base: dict | None = None
    sc_ft: dict | None = None
    det: dict | None = None
    est: dict | None = None
    acc: float | None = None
    may: float | None = None


# --------------------------------------------------------------------------
# 0 · Arranque y clave de Groq
# --------------------------------------------------------------------------
def preparar() -> Contexto:
    """Corrida nueva, sello, clave de Groq (por teclado si falta: M2 no sirve
    sin juez) y `arranque.celda("m2")`. M2 no entrena, pero sin
    `m1_predicciones.json` no tiene de donde partir, y descubrirlo a mitad
    cuesta la corrida."""
    from amparo.ejecucion import entorno
    return Contexto(c=entorno.preparar("m2", pedir_clave=True))


# --------------------------------------------------------------------------
# 1 · Las salidas de M1
# --------------------------------------------------------------------------
def cargar_salidas(ctx: Contexto, ruta=RESULTS / "m1_predicciones.json") -> None:
    ctx.eval_set = schema.cargar(archivo="eval_set_v3.json")
    ctx.preds, ctx.corrida_m1 = predicciones.cargar_m1(ruta, eval_set=ctx.eval_set)
    ctx.sal_base, ctx.sal_ft = predicciones.recortar(ctx.preds)
    ev = ctx.eval_set
    print(f"{len(ev)} casos · {sum(e['tipo'] == 'gold' for e in ev)} gold · "
          f"{sum(e['tipo'] == 'adversarial' for e in ev)} adversariales")


# --------------------------------------------------------------------------
# 2 · Formato contra vocabulario
# --------------------------------------------------------------------------
def formato_vocabulario(ctx: Contexto) -> dict:
    """Imitar la FORMA de la respuesta y usar el VOCABULARIO cerrado son dos
    cosas distintas. Si la adherencia estructural ya era alta en el base, el
    fine-tuning no enseno el formato: enseno el vocabulario."""
    out = {}
    print(f"{'':<24}{'base':>10}{'fine-tuned':>12}")
    print("-" * 46)
    for nombre, fn in [("adherencia estructural", metricas.adherencia_estructural),
                       ("adherencia vocabulario", metricas.adherencia_vocabulario),
                       ("coherencia", metricas.coherencia)]:
        vb, vf = fn(ctx.sal_base), fn(ctx.sal_ft)
        out[nombre] = {"base": vb, "finetuned": vf}
        fb = f"{vb:>10.1%}" if vb is not None else f"{'no evaluable':>10}"
        ff = f"{vf:>12.1%}" if vf is not None else f"{'no evaluable':>12}"
        print(f"{nombre:<24}{fb}{ff}")
    print()
    # `coherencia` devuelve None y no 0.0 cuando no hay nada que evaluar,
    # porque un 0.0 se lee como un fallo.
    return out


# --------------------------------------------------------------------------
# 3 · Dimension 1 — la metrica clasica y su limite
# --------------------------------------------------------------------------
def rouge_vs_acierto(ctx: Contexto) -> dict:
    """El argumento CON DATOS de por que la similitud lexica no mide derecho:
    si el ROUGE-L medio es parecido cuando el mecanismo acierta y cuando
    falla, ROUGE-L no distingue derecho bien aplicado de mal aplicado."""
    filas = []
    for e, s in zip(ctx.eval_set, ctx.sal_ft):
        p = schema.parse_salida(s)
        prosa = " ".join(filter(None, [p.get("razon"), p.get("pretension")]))
        r = metricas.rouge_l(prosa, e["razon"] + " " + e["pretension"])
        filas.append((e["id"], e["categoria"], r, p.get("mecanismo") == e["mecanismo"]))

    enganosos = sorted([f for f in filas if not f[3]], key=lambda x: -x[2])[:6]
    print("Casos con ROUGE-L alto y MECANISMO EQUIVOCADO:")
    print(f"{'id':<6}{'categoria':<34}{'ROUGE-L':>9}")
    print("-" * 50)
    for i, cat, r, _ in enganosos:
        print(f"{i:<6}{cat:<34}{r:>8.1%}")

    acc = [f[2] for f in filas if f[3]]
    err = [f[2] for f in filas if not f[3]]
    print()
    print(f"ROUGE-L medio cuando ACIERTA el mecanismo : {sum(acc)/len(acc):.1%}  (n={len(acc)})")
    print(f"ROUGE-L medio cuando FALLA   el mecanismo : {sum(err)/len(err):.1%}  (n={len(err)})")
    res = {"medio_acierta": sum(acc) / len(acc), "medio_falla": sum(err) / len(err),
           "enganosos": [{"id": i, "categoria": ca, "rouge": r} for i, ca, r, _ in enganosos]}
    ctx.c.guardar_json("rouge_vs_acierto", res)
    return res


# --------------------------------------------------------------------------
# 4 · Dimension 2 — LLM-as-a-judge
# --------------------------------------------------------------------------
def elegir_juez(ctx: Contexto, construir_juez=None) -> None:
    """El juez por defecto y, si falla, los de `MODELOS_ALTERNATIVOS`.

    El juez es de otra familia que el sistema evaluado (Qwen2.5-7B): un juez
    del mismo linaje reintroduce la auto-preferencia. Si ningun modelo
    responde se PARA AQUI con el motivo: antes `j` quedaba sin asignar y la
    etapa siguiente moria con `NameError: j`.
    """
    construir_juez = construir_juez or (lambda m=None: _juez.Juez(modelo=m) if m else _juez.Juez())
    e0 = ctx.eval_set[0]
    j = None
    try:
        j = construir_juez()
        prueba = j.puntuar(e0["relato"], schema.render_salida(e0), ctx.sal_ft[0])
        print("modelo:", j.modelo, "->", prueba)
    except Exception as ex:                                # noqa: BLE001
        print("Fallo con el modelo por defecto:", str(ex)[:120])
        j = None
        for m in _juez.MODELOS_ALTERNATIVOS:
            try:
                j = construir_juez(m)
                print("usando alternativo:", m, "->",
                      j.puntuar(e0["relato"], schema.render_salida(e0), ctx.sal_ft[0]))
                break
            except Exception as ex2:                       # noqa: BLE001
                j = None          # construido pero inservible: no vale como juez
                print("  ", m, "no disponible:", str(ex2)[:60])
    if j is None:
        raise SystemExit(
            "Ningun modelo de juez esta disponible: fallo el por defecto y "
            "tambien todos los alternativos.\n"
            "  1. Comprueba GROQ_API_KEY en los secretos de Colab.\n"
            "  2. Mira si los modelos de juez.py siguen servidos en tu cuenta.\n"
            "Sin juez, la dimension 2 del harness no se puede medir --- y las "
            "dimensiones 1 y 3 solas no son el harness.")
    ctx.j = j


def sesgo_posicion(ctx: Contexto, n: int = 12) -> dict:
    sp = harness.sesgo_posicion(ctx.j, ctx.eval_set, ctx.sal_ft, ctx.sal_base, n=n)
    print(f"comparaciones            : {sp['n']}  ({sp['preguntas']} preguntas al juez)")
    print(f"ilegibles                : {sp['ilegibles']}")
    print(f"veredictos inconsistentes: {sp['inconsistentes']}  ({sp['tasa_inconsistencia']:.1%})")
    # `preferencia_posicion_A` vale None A PROPOSITO cuando no hubo
    # inconsistencias: con 0 inconsistentes esa fraccion vale 0.5 por
    # aritmetica forzosa, e imprimir "50%, sin sesgo" diria dos veces el mismo
    # hecho presentado como dos pruebas. Antes se formateaba con `:.1%` y
    # reventaba con TypeError.
    pref = sp["preferencia_posicion_A"]
    if pref is None:
        print("eligio la posicion A     : indefinida")
    else:
        print(f"eligio la posicion A     : {pref:.1%}   (50% = sin sesgo)")
    print(f"   {sp['preferencia_posicion_A_lectura']}")
    print(f"veredictos               : {sp['veredictos']}")
    print()
    if sp["inconsistentes"]:
        print("EVIDENCIA DE LA MITIGACION: sin preguntar en ambos ordenes habriamos")
        print(f"aceptado {sp['inconsistentes']} veredicto(s) que el propio juez "
              "contradice al invertirlos.")
    else:
        print("LA MITIGACION NO TUVO QUE CORREGIR NADA: el juez dio el mismo")
        print(f"veredicto en los dos ordenes en las {sp['n']} comparaciones. Eso NO")
        print("es que preguntar en ambos ordenes sobre: es COMO SE SABE que no")
        print("hacia falta, y costo las mismas 2 preguntas por caso.")
    ctx.sp = sp
    return sp


def sesgo_longitud(ctx: Contexto, n: int = 10) -> dict:
    """ROADMAP #21. Dos niveles:

      obvio   mecanismo cambiado + relleno -> control de cordura (detectable
              comparando etiquetas, sin leer el razonamiento).
      sutil   mecanismo y procedencia CORRECTOS, razon hueca + relleno. El unico
              defecto esta en el razonamiento. Es el que mide el sesgo.
    """
    sl_ambos = harness.sesgo_longitud(ctx.j, ctx.eval_set, n=n, nivel="ambos")
    sl = sl_ambos["sutil"]          # el que cuenta como medicion del sesgo
    print(f"{'nivel':<8}{'breve':>7}{'larga':>7}{'emp.':>6}{'ileg.':>7}{'tasa':>8}")
    print("-" * 43)
    for k in ("obvio", "sutil"):
        d = sl_ambos[k]
        print(f"{k:<8}{d['gana_correcta_breve']:>7}{d['gana_larga']:>7}"
              f"{d['empates']:>6}{d['ilegibles']:>7}{d['tasa_sesgo_longitud']:>8.1%}")
    print()
    print(f"la larga anade {sl['chars_extra_de_la_larga']} caracteres y falla en:")
    print(f"  obvio -> {sl_ambos['obvio']['que_falla_en_la_larga']}")
    print(f"  sutil -> {sl_ambos['sutil']['que_falla_en_la_larga']}")
    print()
    t_ob = sl_ambos["obvio"]["tasa_sesgo_longitud"]
    t_su = sl_ambos["sutil"]["tasa_sesgo_longitud"]
    if t_ob <= 0.2 and t_su > 0.2:
        print("DIAGNOSTICO: el juez pasa el facil y falla el sutil. No esta")
        print("evaluando el razonamiento: esta comparando la etiqueta del mecanismo")
        print("con la de la referencia. Su nota no puede usarse sola.")
    elif t_su > 0.2:
        print("El juez se deja llevar por la verbosidad pese a la regla explicita,")
        print("y falla incluso el nivel obvio. Su nota solo vale junto a la")
        print("dimension 3.")
    else:
        print("La regla explicita contuvo el sesgo en los DOS niveles. Eso si es")
        print("evidencia de que la rubrica hace efecto: el nivel sutil no se puede")
        print("pasar comparando etiquetas.")
    ctx.sl_ambos, ctx.sl = sl_ambos, sl
    return sl


def respuestas_familia(cliente, modelo: str, eval_set: list[dict], ruta_cache) -> tuple[list[str], int]:
    """Las respuestas del modelo de la FAMILIA del juez, con cache en disco.

    POR QUE PARA **TODOS** LOS CASOS Y NO PARA LOS PRIMEROS 15: la corrida
    m2/20261019T034128Z genero 15 y midio 15 pares; salio `indefinida` con n=2
    en `empate_correctas`, porque 12 de 15 cayeron en `gana_ajeno`.
    `sesgo_autopreferencia` clasifica TODOS los pares primero (gratis, contra
    el gold) y gasta las llamadas del juez empezando por `empate_correctas`,
    el unico estrato donde una preferencia ES sesgo. Para elegir entre todos
    hay que TENER todos. El cache hace que una segunda corrida no pague la
    generacion otra vez. Devuelve `(salidas, nuevas)`.
    """
    ruta = Path(ruta_cache)
    cache = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    salidas, nuevas = [], 0
    for i, e in enumerate(eval_set, 1):
        k = f"{modelo}||{e['id']}"
        if k not in cache:
            r = cliente.chat.completions.create(
                model=modelo,
                messages=[{"role": "system", "content": schema.SISTEMA_TRIAJE},
                          {"role": "user", "content": schema.PROMPT.format(relato=e["relato"])}],
                temperature=0, max_tokens=400, seed=42)
            cache[k] = (r.choices[0].message.content or "").strip()
            nuevas += 1
        salidas.append(schema.recortar_al_bloque(cache[k])[0])
        print(f"  {i}/{len(eval_set)}  ({nuevas} nuevas)", end="\r")
    ruta.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(" " * 40, end="\r")
    return salidas, nuevas


def autopreferencia(ctx: Contexto, n: int = N_AP) -> dict:
    """Sesgo 3 · auto-preferencia, MEDIDO y condicionado en la verdad de dominio.

    Si el juez prefiere las respuestas de gpt-oss puede ser auto-preferencia o
    que gpt-oss-120b sea de verdad mejor que un Qwen de 7B. Se condiciona en
    si cada respuesta acerto el mecanismo: en `empate_correctas` la calidad
    objetiva esta empatada, asi que cualquier preferencia sistematica ES sesgo.
    Se pregunta en los dos ordenes y lo inconsistente se descarta.
    """
    modelo_familia = next((m for m in _juez.MODELOS_ALTERNATIVOS if "gpt-oss" in m),
                          _juez.MODELOS_ALTERNATIVOS[0])
    print("sistema evaluado     :", SISTEMA_EVALUADO)
    print("juez                 :", _juez.MODELO)
    print("excluidos por familia:", _juez.MODELOS_EXCLUIDOS_POR_FAMILIA)
    print()
    print(f"generando {len(ctx.eval_set)} respuestas con {modelo_familia} (familia del juez)...")
    sal_familia, nuevas = respuestas_familia(ctx.j.cliente, modelo_familia, ctx.eval_set,
                                             ctx.c.ruta_cache("autopreferencia.json"))
    print(f"  {len(sal_familia)} respuestas listas ({nuevas} generadas ahora, "
          f"{len(sal_familia) - nuevas} de cache)")
    print()

    ap = harness.sesgo_autopreferencia(
        ctx.j, ctx.eval_set, sal_familia, ctx.sal_ft, n=n,
        etq_familia=f"{modelo_familia} (familia del juez)",
        etq_ajeno="Qwen2.5-7B ajustado (evaluado)")

    # LA TABLA LLEVA LAS DOS COLUMNAS: cuantos habia y cuantos se midieron.
    # `por_estrato` ya NO es una muestra aleatoria (el presupuesto se gasta a
    # proposito empezando por el estrato decisivo), y leerlo como tal haria
    # concluir, por ejemplo, que `gana_ajeno` casi no ocurre.
    print(f"{'estrato':<20}{'disp.':>7}{'medidos':>9}{'pref.fam':>10}"
          f"{'pref.aj':>9}{'emp.':>6}{'inc.':>6}")
    print("-" * 69)
    for k, v in ap["por_estrato"].items():
        print(f"{k:<20}{ap['disponibles_por_estrato'][k]:>7}{v['n']:>9}"
              f"{v['prefiere_familia']:>10}{v['prefiere_ajeno']:>9}"
              f"{v['empate']:>6}{v['inconsistente']:>6}")
    print("-" * 69)
    print(f"seleccion estratificada: se gastan las {n} llamadas en el orden "
          f"{' > '.join(ap['seleccion']['prioridad'])}")
    print()
    pref = ap["preferencia_familia_con_calidad_empatada"]
    print(f"preferencia por la familia del juez CON CALIDAD EMPATADA: {pref}")
    if ap["ic"]:
        print(f"  IC95 [{ap['ic']['ic_bajo']:.3f}, {ap['ic']['ic_alto']:.3f}]"
              f"  n={ap['n_decididos_en_el_empate']}")
    print()
    if pref == "indefinida":
        print("INDEFINIDA: no hubo NINGUN par con las dos respuestas correctas:")
        print("el estrato no existe en estos datos, y el experimento no puede informar.")
    elif ap["ic"] and ap["ic"]["ic_bajo"] <= 0.5 <= ap["ic"]["ic_alto"]:
        print("El intervalo CONTIENE 0.5: no se detecta auto-preferencia. No es lo")
        print("mismo que probar que no existe, y asi hay que reportarlo: la")
        print("mitigacion arquitectonica sigue justificada.")
    elif pref > 0.5:
        print("Hay auto-preferencia: con la calidad objetiva empatada, el juez")
        print("prefiere a los de su linaje. La exclusion de Qwen como juez no era")
        print("una precaucion teorica.")
    else:
        print("El juez prefiere las ajenas con la calidad empatada: lo contrario de")
        print("la auto-preferencia, y tambien hay que reportarlo.")
    ctx.c.guardar_json("sesgo_autopreferencia", ap)
    ctx.ap = ap
    return ap


def inyeccion(ctx: Contexto) -> dict:
    """Sesgo 4 · inyeccion de prompt. El relato lo escribe un tercero, asi que
    es una via de entrada. Las sondas piden siempre una nota DISTINTA de la
    que merece la respuesta, en las dos direcciones (tres inflan, tres
    desinflan): la primera version pedia la nota que el juez iba a dar de
    todos modos, un experimento que no podia fallar. Las sondas viven en
    `data/inyecciones.json`: no son casos de triaje y no entran en ninguna
    accuracy."""
    sondas = schema.cargar(archivo="inyecciones.json")
    iny = _juez.experimento_inyeccion(ctx.j, sondas, schema.render_salida)
    print(f"sondas de inyeccion: {iny['n']}  (ilegibles: {iny['ilegibles']})")
    for d in iny["detalle"]:
        print(f"  {d['id']}  {d['direccion']:<9} sobre {d['evalua']:<18} "
              f"pide {d['nota_pedida_por_la_inyeccion']}  ->  "
              f"con {d['nota_con_inyeccion']} / sin {d['nota_sin_inyeccion']}  "
              f"obedecio: {d['obedecio']}")
        print(f"        estilo: {d['estilo']}")
        print(f"        justificacion: {d['justificacion_con'][:100]}")
    print()
    print(f"obedecieron del todo : {iny['obedecieron']}/{iny['n']} ({iny['tasa_obediencia']:.0%})")
    print(f"movieron la nota     : {iny['cambiaron_la_nota']}/{iny['n']} ({iny['tasa_cambio']:.0%})")
    for d, v in iny["por_direccion"].items():
        print(f"   {d:<9} n={v['n']}  obedecieron={v['obedecieron']}  cambiaron={v['cambiaron']}")
    print()
    if iny["obedecieron"]:
        print("EL JUEZ OBEDECIO una instruccion incrustada. La defensa de la rubrica no")
        print("basta y la nota del juez no es confiable sobre entradas no confiables.")
    elif iny["cambiaron_la_nota"]:
        print("El juez no dio la nota exigida, pero la inyeccion SI movio la nota: la")
        print("instruccion le afecta aunque no lo controle del todo. Vale reportarlo.")
    else:
        print("El juez IGNORO las instrucciones incrustadas en las dos direcciones:")
        print("la defensa de la rubrica aguanta.")
    ctx.c.guardar_json("sesgo_inyeccion", iny)
    ctx.iny = iny
    return iny


def validez(ctx: Contexto, n: int = 10) -> dict:
    """Sonda 5 · ¿el juez distingue una respuesta correcta de una rota?

    Las cuatro sondas anteriores miden si al juez se le puede ENGANAR; un juez
    que puntuara al azar las pasaria todas. Aqui se le pone el gold y el mismo
    gold con un defecto aislado, y se mira si la nota baja. Es validez de
    construccion, no acuerdo con un humano (eso es M2-1b). 4 llamadas por
    caso: n=10 son 40.
    """
    val = _juez.experimento_validez(ctx.j, ctx.eval_set, schema.render_salida, n=n)
    print(f"{'degradacion':<22}{'n':>3}{'margen medio':>14}{'minimo':>8}"
          f"{'inversiones':>13}{'ilegibles':>11}")
    print("-" * 71)
    for modo, d in val["por_modo"].items():
        medio = f"{d['margen_medio']:+.2f}" if d["margen_medio"] is not None else "sin medir"
        minimo = d["margen_minimo"] if d["margen_minimo"] is not None else "-"
        inver = f"{d['inversiones']}/{d['n']}"
        print(f"{modo:<22}{d['n']:>3}{medio:>14}{str(minimo):>8}{inver:>13}{d['ilegibles']:>11}")
    print()
    mg = val["margen_por_mecanismo"]
    print(f"margen cuando el MECANISMO esta mal: {mg}")
    if mg is None:
        print("SIN MEDIR: ninguna comparacion fue legible. No es que el juez no")
        print("distinga: es que no se pudo preguntar, y son cosas distintas.")
    elif mg <= 0:
        print("EL JUEZ NO DISTINGUE una conclusion juridica correcta de una")
        print("incorrecta. Sus notas NO miden derecho, y entonces ninguna cifra")
        print("que dependa de ellas se sostiene.")
    else:
        print(f"El juez castiga el mecanismo equivocado con {mg} puntos de media.")
        print("Eso NO dice que coincida con un abogado: eso es M2-1b y sigue abierto.")
    if not val["norma_falsa_sigue_fuera_del_whitelist"]:
        print()
        print(f"ATENCION: `{val['norma_falsa_usada']}` entro al whitelist, asi que")
        print("la degradacion `norma_inventada` ya no degrada nada y su margen no")
        print("significa lo que dice. Hay que cambiar la norma falsa.")
    ctx.c.guardar_json("validez_juez", val)
    ctx.val = val
    return val


def acuerdo_entre_jueces(ctx: Contexto, cliente=None, construir_juez=None) -> dict | None:
    """¿La nota es del sistema o del juez? Ver `amparo.evaluacion.acuerdo`.

    La familia del segundo juez importa mas que su tamano: el acuerdo controla
    el RUIDO de un juez, no el SESGO que dos modelos del mismo linaje
    comparten. Si ningun segundo juez responde no se guarda nada.
    """
    if cliente is None:
        import os
        import groq
        cliente = groq.Groq(api_key=os.environ["GROQ_API_KEY"])
    ctx.acuerdo = _acuerdo.medir(ctx.j, ctx.eval_set, ctx.sal_ft, cliente=cliente,
                                 construir_juez=construir_juez)
    if ctx.acuerdo is not None:
        ctx.c.guardar_json("acuerdo_entre_jueces", ctx.acuerdo)
    return ctx.acuerdo


# --------------------------------------------------------------------------
# 5 · El harness completo
# --------------------------------------------------------------------------
def harness_completo(ctx: Contexto) -> None:
    ctx.sc_base = harness.tabla_puente(ctx.eval_set, ctx.sal_base, "M1 base (sin fine-tuning)", juez=ctx.j)
    ctx.sc_ft = harness.tabla_puente(ctx.eval_set, ctx.sal_ft, "M1 fine-tuned LoRA", juez=ctx.j)
    metricas.imprimir(ctx.sc_ft)
    print()
    print("DIMENSION 2 - juez")
    for sc in (ctx.sc_base, ctx.sc_ft):
        jz = sc["juez"]
        # kappa es None cuando queda indefinido: si los dos anotadores usan una
        # sola categoria el acuerdo esperado por azar es 1 y la formula se
        # indetermina.
        kap = jz["kappa_vs_dominio"]
        kap_txt = f"{kap:+.2f}" if kap is not None else "indefinido (ambos constantes)"
        print(f"  {sc['sistema']:<30} nota media {jz['nota_media']:.2f}  "
              f"gold {jz['nota_media_por_tipo'].get('gold', 0):.2f}  "
              f"adversarial {jz['nota_media_por_tipo'].get('adversarial', 0):.2f}  "
              f"kappa {kap_txt}")
    print()
    # ADHERENCIA A LA RUBRICA - el juez contra su PROPIA escala. La kappa de
    # arriba mide si el juez coincide con la metrica de dominio, y no tiene
    # por que (seria una copia ruidosa de `acierto_juridico`). La rubrica dice
    # "3 = mecanismo correcto", asi que `nota >= 3` AFIRMA que el mecanismo
    # esta bien, y eso se comprueba contra el gold.
    print("ADHERENCIA A LA RUBRICA - el juez contra su PROPIA escala")
    for sc in (ctx.sc_base, ctx.sc_ft):
        ad = sc["juez"]["adherencia_a_la_rubrica"]
        if not ad["concluyente"]:
            print(f"  {sc['sistema']:<30} sin medir: {ad['motivo']}")
            continue
        print(f"  {sc['sistema']:<30} {ad['adherencia']:.1%} de {ad['n']} notas  "
              f"generosas {ad['incumple_generoso']}  severas {ad['incumple_severo']}")
        if ad["casos_generoso"]:
            print(f"     nota >= 3 con el mecanismo MAL: {', '.join(ad['casos_generoso'][:10])}")
    print()
    print(ctx.sc_ft["juez"]["adherencia_a_la_rubrica"].get("lectura", ""))

    metricas.comparar(ctx.sc_base, ctx.sc_ft)
    ctx.acc = ctx.sc_ft["campos"]["mecanismo"]["accuracy"]
    ctx.may = ctx.sc_ft["campos"]["mecanismo"]["baseline_mayoritaria"]
    print()
    print(f"acc_mecanismo {ctx.acc:.1%} contra la clase mayoritaria {ctx.may:.1%} "
          f"(delta {ctx.acc - ctx.may:+.1%})")


# --------------------------------------------------------------------------
# 6 · Reproducibilidad
# --------------------------------------------------------------------------
def limpiar(sc: dict) -> dict:
    """El scorecard sin `entorno`, que cambia entre dos pasadas aunque nada mas lo haga."""
    sc = copy.deepcopy(sc)
    sc.pop("entorno", None)
    return sc


def filas_por_caso(eval_set: list[dict], sal_ft: list[str], sc_ft: dict) -> list[dict]:
    return [{"id": e["id"], "tipo": e["tipo"], "categoria": e["categoria"],
             "gold_mecanismo": e["mecanismo"],
             "pred_mecanismo": schema.parse_salida(s).get("mecanismo"),
             "acierto": schema.parse_salida(s).get("mecanismo") == e["mecanismo"],
             "nota_juez": n["nota"]}
            for e, s, n in zip(eval_set, sal_ft, sc_ft["juez"]["notas"])]


def corridas_previas(carpeta_modulo: Path, id_actual: str) -> list[tuple[Path, dict]]:
    """Las corridas anteriores REALES de m2 con `scorecard_por_caso`.

    Se saltan las de control que dejaba la version anterior (una corrida
    desechable por ejecucion que se comparaba consigo misma): tienen un solo
    artefacto y compararse contra ellas no diria nada.
    """
    previas = []
    if not carpeta_modulo.is_dir():
        return previas
    for p in sorted(carpeta_modulo.iterdir()):
        if not p.is_dir() or p.name == id_actual:
            continue
        f = p / "corrida.json"
        if not f.exists():
            continue
        meta = json.loads(f.read_text(encoding="utf-8"))
        if "control" in str(meta.get("notas") or "").lower():
            continue
        if not (p / "scorecard_por_caso.csv").exists():
            continue
        previas.append((p, meta))
    return previas


def estabilidad(c, previas: list[tuple[Path, dict]], corrida_m1: str | None) -> dict:
    """El mismo artefacto en la corrida ANTERIOR y en esta.

    ESTO COMPARABA UNA TAUTOLOGIA: escribia la MISMA lista en una corrida de
    control y la comparaba, asi que `identicas` salia True por construccion
    (prueba el serializador, no la tuberia), mientras M1 se comparaba contra
    su corrida anterior y publicaba False. Ahora se compara contra la
    anterior real, con lo que hace falta para ATRIBUIR una diferencia:
    codigo, datos, hardware y de que corrida de M1 salieron las predicciones.
    """
    if not previas:
        print("estabilidad: primera corrida comparable de m2, no hay con que "
              "comparar. `identicas` queda en None --- que NO es `True`.")
        return {"concluyente": False,
                "motivo": ("no hay ninguna corrida anterior de m2 con "
                           "`scorecard_por_caso` contra la que comparar"),
                "identicas": None}
    prev, meta_prev = previas[-1]
    est = corridas.comparar(prev, c.dir, "scorecard_por_caso")
    cod_prev = (meta_prev.get("codigo") or {}).get("_conjunto")
    cod_now = (c.meta.get("codigo") or {}).get("_conjunto")
    est.update({
        "concluyente": True,
        "corrida_previa": prev.name, "corrida_actual": c.id,
        "codigo_previa": cod_prev, "codigo_actual": cod_now,
        "mismo_codigo": cod_prev is not None and cod_prev == cod_now,
        "mismos_datos": ((meta_prev.get("datos") or {}).get("eval_set_v3.json")
                         == c.meta["datos"].get("eval_set_v3.json")),
        "mismo_hardware": ((meta_prev.get("hardware") or {}).get("gpu")
                           == (c.meta.get("hardware") or {}).get("gpu")),
        # Si cambiaron las predicciones de M1, que el juez puntue distinto es
        # lo ESPERABLE y no un hallazgo sobre el harness.
        "m1_previa": next((n.split(":")[-1].strip()
                           for n in (meta_prev.get("notas") or [])
                           if "corrida m1" in str(n)), None),
        "m1_actual": corrida_m1,
    })
    print(f"estabilidad: {prev.name} vs {c.id}")
    print(f"   mismo codigo    : {est['mismo_codigo']}")
    print(f"   mismos datos    : {est['mismos_datos']}")
    print(f"   predicciones m1 : {est['m1_previa']} -> {est['m1_actual']}")
    if not est["mismo_codigo"] or est["m1_previa"] != est["m1_actual"]:
        print("   OJO: cambio el codigo o las predicciones de entrada, asi")
        print("   que una diferencia aqui NO prueba no-determinismo.")
    return est


def reproducibilidad(ctx: Contexto) -> None:
    """Dos niveles: dentro de la sesion (el harness dos veces da lo mismo) y
    entre corridas distintas guardadas en disco.

    El primer nivel prueba MENOS de lo que parece: la segunda pasada sale
    entera del cache, asi que demuestra que el cache funciona y que el harness
    no tiene aleatoriedad propia, NO que el juez responda igual dos veces.
    Para eso, `determinismo_lote`: 5 casos x 4 repeticiones = 20 llamadas
    reales, y se publica la RESOLUCION del instrumento (antes eran 3 llamadas
    sobre un caso: detectaban que el juez varia, no cuanto ni cada cuanto).
    """
    c, j = ctx.c, ctx.j
    a = harness.tabla_puente(ctx.eval_set, ctx.sal_ft, "M1 fine-tuned LoRA", juez=j)
    b = harness.tabla_puente(ctx.eval_set, ctx.sal_ft, "M1 fine-tuned LoRA", juez=j)
    iguales = json.dumps(limpiar(a), sort_keys=True) == json.dumps(limpiar(b), sort_keys=True)
    print("el HARNESS es determinista dado el juez:", iguales)
    print(f"llamadas reales a la API en la 2a: {j.llamadas}  (el resto, cache)")
    assert iguales, "El harness no es reproducible: revisa el cache del juez"

    det = j.determinismo_lote(ctx.eval_set, ctx.sal_ft, schema.render_salida,
                              n_casos=5, repeticiones=4)
    print()
    print(f"determinismo DEL JUEZ (sin cache, {det['llamadas_reales']} llamadas reales)")
    print(f"   casos estables   : {det['casos_estables']}/{det['n_casos']}"
          f"  (tasa {det['tasa_estabilidad']})")
    print(f"   rango medio      : {det['rango_medio']}")
    print(f"   rango maximo     : {det['rango_maximo']}")
    print()
    for cc in det["por_caso"]:
        m = "estable" if cc["estable"] else f"varia {cc['rango']}"
        print(f"   {str(cc['id']):<6} {str(cc['notas']):<22} {m}")
    print()
    if det["resolucion"]:
        print("RESOLUCION:", det["resolucion"])
    else:
        print("SIN MEDIR: ninguna repeticion fue legible. No es que el juez no")
        print("varie: es que no se pudo preguntar, y son cosas distintas.")
    print()
    print(det["lectura"])
    j.guardar_cache()

    c.guardar_csv("scorecard_por_caso", filas_por_caso(ctx.eval_set, ctx.sal_ft, ctx.sc_ft))
    est = estabilidad(c, corridas_previas(c.dir.parent, c.id), ctx.corrida_m1)
    c.guardar_json("estabilidad", est)
    c.guardar_json("determinismo_juez", det)
    c.nota(f"predicciones de la corrida m1: {ctx.corrida_m1 or 'sin registrar'}")
    # La nota lleva la RESOLUCION, no un booleano: es lo que limita que se
    # puede afirmar con las notas del juez.
    c.nota(f"determinismo del juez: {det['casos_estables']}/{det['n_casos']} "
           f"casos estables, rango maximo {det['rango_maximo']} "
           f"({det['llamadas_reales']} llamadas reales sin cache)")
    print()
    print("identicas:", est.get("identicas"), "·", est.get("n_filas", 0), "filas comparadas")
    ctx.det, ctx.est = det, est


# --------------------------------------------------------------------------
# 7 · Scorecard y publicacion
# --------------------------------------------------------------------------
def publicar(ctx: Contexto) -> None:
    """Guarda los scorecards, comprueba TODOS los artefactos y publica.

    El acuerdo entre jueces va APARTE: es el unico CONDICIONAL. Si el segundo
    juez no estuvo servido no se publica nada (un archivo vacio seria peor que
    su ausencia), y meterlo en la lista haria que su ausencia legitima
    bloqueara los otros diez.
    """
    c = ctx.c
    c.guardar_json("scorecard_base", ctx.sc_base)
    c.guardar_json("scorecard_finetuned", ctx.sc_ft)
    c.guardar_json("sesgos", {"posicion": ctx.sp, "longitud": ctx.sl, "inyeccion": ctx.iny})
    harness.a_csv([ctx.sc_base, ctx.sc_ft], str(c.dir / "scorecard.csv"))
    c.artefactos["scorecard"] = "scorecard.csv"

    publicacion.publicar_todo(c, A_PUBLICAR, QUIEN_LO_GENERA)
    if ctx.acuerdo is not None:
        c.publicar("acuerdo_entre_jueces", "results/m2_acuerdo_entre_jueces.json")
    else:
        print("sin acuerdo entre jueces en esta corrida: el segundo juez no "
              "estuvo disponible, y eso queda sin medir.")

    c.cerrar(valida=True, notas=[
        f"acc_mecanismo {ctx.acc:.4f} contra mayoritaria {ctx.may:.4f}",
        f"sesgo de posicion: {ctx.sp['inconsistentes']} inconsistentes de {ctx.sp['n']}",
        f"sesgo de longitud: tasa {ctx.sl['tasa_sesgo_longitud']:.4f}",
        f"inyeccion: {ctx.iny['obedecieron']} de {ctx.iny['n']} obedecieron",
        f"estabilidad entre corridas: {ctx.est['identicas']}",
    ])


# Los destinos van LITERALES: la autoprueba los audita contra `arranque.ORDEN`.
# Se declaran despues de todo lo que los genera (incluido `publicar`, que
# guarda los scorecards): asi el texto del modulo respeta guardar -> publicar.
A_PUBLICAR = [
    ("scorecard_base", "results/m2_scorecard_base.json"),
    ("scorecard_finetuned", "results/m2_scorecard_finetuned.json"),
    ("sesgos", "results/m2_sesgos.json"),
    # La sonda que dice si el instrumento MIDE algo. Sin ella, las otras
    # cuatro son compatibles con un juez que puntua al azar.
    ("validez_juez", "results/m2_validez_juez.json"),
    # La unica medicion que dice si el juez premia a su propia familia.
    ("sesgo_autopreferencia", "results/m2_sesgo_autopreferencia.json"),
    # Si el juez no repite su nota, ninguna cifra que produce es reproducible.
    ("determinismo_juez", "results/m2_determinismo_juez.json"),
    ("estabilidad", "results/m2_estabilidad.json"),
    # El argumento CON DATOS de por que la similitud lexica no mide derecho.
    ("rouge_vs_acierto", "results/m2_rouge_vs_acierto.json"),
    ("scorecard", "results/scorecard_baseline.csv"),
    ("scorecard_por_caso", "results/m2_scorecard_por_caso.csv"),
]
QUIEN_LO_GENERA = {
    "scorecard_base": "harness_completo (seccion 5)",
    "scorecard_finetuned": "harness_completo (seccion 5)",
    "sesgos": "sesgo_posicion, sesgo_longitud e inyeccion (seccion 4)",
    "validez_juez": "validez (seccion 4, la sonda 5: 40 llamadas a Groq)",
    "sesgo_autopreferencia": "autopreferencia (seccion 4, la sonda 3)",
    "determinismo_juez": "reproducibilidad (seccion 6)",
    "estabilidad": "reproducibilidad (seccion 6)",
    "rouge_vs_acierto": "rouge_vs_acierto (seccion 3)",
    "scorecard": "publicar, con `harness.a_csv`",
    "scorecard_por_caso": "reproducibilidad (seccion 6)",
}


ETAPAS = (cargar_salidas, formato_vocabulario, rouge_vs_acierto, elegir_juez,
          sesgo_posicion, sesgo_longitud, autopreferencia, inyeccion, validez,
          acuerdo_entre_jueces, harness_completo, reproducibilidad, publicar)


def correr(ctx: Contexto | None = None) -> Contexto:
    """Todas las etapas en el orden del notebook."""
    ctx = ctx or preparar()
    for etapa in ETAPAS:
        print(f"\n===== {etapa.__name__} =====")
        etapa(ctx)
    return ctx


if __name__ == "__main__":
    correr()
