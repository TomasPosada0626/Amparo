"""Scorecard de M2: resumen, comparacion con IC y export (sin GPU)."""
from tools.evaluation import scorecard
from tools.evaluation.scorecard import EvalRow


def fila(i, label, *, corr, prud, clar, conc, palabras=10, cortada=False, citas=0):
    comp = (corr + prud + clar + conc) / 4
    return EvalRow(id=i, category="Arriendo", label=label, query=f"q{i}", expected="ref",
                   generated=" ".join(["p"] * palabras), similarity_pct=5.0, exact_match=0.0, token_f1=0.2,
                   bleu=1.0, rouge_l_f=0.1, bertscore_f1=70.0, citation_count=citas,
                   judge_correccion=corr, judge_prudencia=prud, judge_claridad=clar, judge_concision=conc,
                   judge_composite=comp, judge_parse_ok=True, latency_s=1.0, cortada=cortada)


def corrida():
    """El patron de la corrida real: el fine-tuned gana solo en concision y
    pierde en correccion; el compuesto queda casi igual."""
    rows = []
    for i in range(40):
        rows.append(fila(i, "baseline", corr=4, prud=4, clar=4, conc=2, palabras=180, cortada=i % 4 != 0,
                         citas=1 if i % 7 == 0 else 0))
        rows.append(fila(i, "fine_tuned", corr=3 + (i % 2), prud=4, clar=4, conc=4 - (i % 2), palabras=45))
    return rows


def test_resumen_trae_criterios_largo_y_cortadas():
    s = {x.label: x for x in scorecard.summarize_by_label(corrida())}
    assert s["baseline"].pct_cortadas == 75.0 and s["fine_tuned"].pct_cortadas == 0.0
    assert s["baseline"].avg_palabras == 180 and s["fine_tuned"].avg_palabras == 45
    assert s["baseline"].avg_judge_concision == 2 and s["fine_tuned"].avg_judge_correccion == 3.5


def test_comparar_separa_mejora_empeora_y_empate():
    c = scorecard.comparar(corrida())
    assert c["judge_correccion"].significativo and c["judge_correccion"].valor < 0
    assert c["judge_concision"].significativo and c["judge_concision"].valor > 0
    assert not c["judge_prudencia"].significativo


def test_narrativa_dice_lo_que_empeora_y_lo_trivial(tmp_path):
    rows = corrida()
    sums = scorecard.summarize_by_label(rows)
    comp = scorecard.comparar(rows)
    ganadores = {"Qwen (local)": {"baseline": 50, "fine_tuned": 8, "empate": 2}}
    eval_set = {"fine_tuned": {"adversarial": {"n": 6, "cumple": 3, "parcial": 0, "no_cumple": 3,
                                               "aprobacion": 0.5, "aprobacion_ic95": [0.19, 0.81],
                                               "con_errores_juridicos": 0.5, "errores_juridicos_total": 4,
                                               "con_citas_numeradas": 1, "sin_veredicto": 0}}}
    texto = scorecard.build_narrative(sums, {}, n_val=40, comparacion=comp, ganadores=ganadores, eval_set=eval_set)
    assert "EMPEORA" in texto and "correccion juridica" in texto
    assert "Respuestas cortadas" in texto and "baseline 75.0%" in texto
    assert "baseline 50" in texto and "fine_tuned/adversarial: cumple 50%" in texto

    ruta = tmp_path / "scorecard.md"
    scorecard.export_markdown(ruta, sums, {}, texto, {"position_bias_flip_rate_pct": 21.4},
                              {"git_commit": "abc"}, comparacion=comp, ganadores=ganadores, eval_set=eval_set,
                              ejemplos=[{"id": 9102, "query": "¿que articulo?", "baseline": "El 86.",
                                         "fine_tuned": "El articulo 81.", "nota": "cita inventada"}])
    md = ruta.read_text(encoding="utf-8")
    for esperado in ("## Juez por criterio", "**Sin concisión**", "## Comparación cara a cara",
                     "## Eval set propio, contra su criterio", "aprendio a no citar, no a citar bien",
                     "## Respuestas textuales", "El articulo 81.", "Cortadas (%)"):
        assert esperado in md


def test_csv_ida_y_vuelta(tmp_path):
    rows = corrida()
    ruta = tmp_path / "m.csv"
    scorecard.export_csv(ruta, rows)
    leidas = scorecard.load_csv(ruta)
    assert len(leidas) == len(rows)
    assert leidas[1].judge_correccion == rows[1].judge_correccion and leidas[2].cortada is True and leidas[0].cortada is False
    assert "judge_sin_concision" in ruta.read_text(encoding="utf-8").splitlines()[0]


def test_export_con_juez_externo_agrega_su_tabla(tmp_path):
    rows = corrida()
    sums = scorecard.summarize_by_label(rows)
    ruta = tmp_path / "s.md"
    scorecard.export_markdown(ruta, sums, {}, "x", {}, {}, comparacion=scorecard.comparar(rows),
                              juez_externo=("Groq gpt-oss-120b", sums, scorecard.comparar(rows)))
    md = ruta.read_text(encoding="utf-8")
    assert md.count("**Sin concisión**") == 2 and "## Juez por criterio — Groq gpt-oss-120b" in md


def test_elegir_ejemplos_trae_todos_los_adversariales_y_gold_reproducibles():
    from types import SimpleNamespace

    recs = ([{"id": i, "tipo": "gold", "criterio": "c", "messages": [{}, {"content": f"q{i}"}, {}]} for i in range(10)]
            + [{"id": 100 + i, "tipo": "adversarial", "criterio": "c", "messages": [{}, {"content": "a"}, {}]}
               for i in range(3)])
    gens = [SimpleNamespace(id=r["id"], generated=f"r{r['id']}") for r in recs]
    e1 = scorecard.elegir_ejemplos(recs, gens, gens, n_gold=4)
    assert [e["id"] for e in e1[:3]] == [100, 101, 102] and len(e1) == 7
    assert e1 == scorecard.elegir_ejemplos(recs, gens, gens, n_gold=4)


def test_parece_cortada():
    assert scorecard.parece_cortada("1. **Revisar el contrato**: Verifica si")
    assert not scorecard.parece_cortada("Reclama por escrito.")


def test_reanalizar_respeta_la_columna_cortada_real(tmp_path):
    """Una corrida nueva sin respuestas cortadas no debe pasar a la heuristica."""
    rows = corrida()
    for r in rows:
        r.cortada = False
        r.generated = r.generated + " 1."    # termina en algo que la heuristica no confunde
    ruta = tmp_path / "metricas_por_registro.csv"
    scorecard.export_csv(ruta, rows)
    assert scorecard.csv_tiene_columna(ruta, "cortada")


# --- Huellas en el manifiesto de M2 -----------------------------------------
# M2 nacio con un manifiesto sin huellas: declaraba fecha y commit, pero no con
# que adaptador ni sobre que eval set se midio. Eso dejo la corrida del
# 2026-10-06 sin forma de probar que uso el adaptador vigente -- solo se puede
# inferir por la hora. Estas pruebas fijan que las huellas esten y que sean las
# mismas que calcula M3, para que las cifras de los dos modulos se puedan cruzar.

def test_build_manifest_incluye_huellas_de_los_insumos():
    from tools.evaluation.pipeline import build_manifest

    m = build_manifest(n_val=10)

    assert hasattr(m, "hash_dataset")
    assert hasattr(m, "hash_eval_set")
    assert hasattr(m, "hash_adaptador")


def test_la_huella_del_eval_set_es_la_misma_que_calcula_m3():
    """Si M2 y M3 hashearan distinto, declarar 'el mismo eval set' no probaria
    nada: el punto de la huella es poder cruzar los dos modulos."""
    from tools.evaluation import eval_set
    from tools.evaluation.pipeline import build_manifest
    from tools.rag.manifiesto import huella_archivo

    m = build_manifest(n_val=10)

    assert m.hash_eval_set == huella_archivo(eval_set.EVAL_SET_PATH)


def test_el_manifiesto_no_se_cae_si_el_adaptador_no_esta():
    """Fuera de Colab la ruta de Drive no existe. Un campo en None dice 'no se
    pudo registrar', que es informacion; una excepcion tumbaria la corrida por
    un dato accesorio."""
    from tools.evaluation.pipeline import build_manifest

    m = build_manifest(n_val=10, adapter_dir="/ruta/que/no/existe")

    assert m.hash_adaptador is None
    assert m.hash_eval_set is not None
