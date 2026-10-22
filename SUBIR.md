# Qué subir y en qué orden correr

> Generado por `python -I data/preparar_subida.py`. No se edita a mano: se vuelve a generar.

## 1 · La huella con la que tiene que cuadrar

Después de subir, en **cada** notebook, antes de correr nada:

```
!python -I /content/drive/MyDrive/agenteAmparo/data/manifiesto.py
```

Tiene que imprimir exactamente:

```
_TOTAL  2545138 bytes  7b75680429404e9c
```

Si no coincide, **no arranques**: la salida del manifiesto nombra el archivo que difiere. Correr con un `src/` distinto del que se reporta no produce un resultado peor, produce un resultado que no se puede atribuir a ningún código.

Este script no ve Drive y no puede decir que esté al día. Deja la huella esperada para que la comparación la haga quien ve las dos.

## 2 · Qué archivos tienen que viajar

**14 archivos** cambiaron desde la última subida sellada. Cada uno viaja **completo**, sustituyendo el de Drive — no se pegan celdas sueltas:

| archivo | bytes | huella | estado |
|---|---|---|---|
| `data/auditar_tool_use.py` | 9850 | `a2f73d7792e2acbe` | nuevo |
| `data/autoprueba_reporte.py` | 20750 | `8368eb0464704cb9` | cambiado |
| `data/doble_anotacion.py` | 35350 | `5e083e82e75753f2` | cambiado |
| `data/manifiesto.py` | 13997 | `975e9652fdbd8321` | cambiado |
| `data/preparar_subida.py` | 14451 | `8cacdec6ad58dcb7` | cambiado |
| `data/reporte.py` | 85844 | `0b1250c1acf0c411` | cambiado |
| `data/validacion_juez.py` | 39827 | `f396d6735b583b2d` | cambiado |
| `notebooks/M1_finetuning.ipynb` | 105805 | `e59a1198a5ead71d` | cambiado |
| `notebooks/M3_rag.ipynb` | 80829 | `73288ab8b8c0e2b0` | cambiado |
| `src/agente.py` | 51307 | `fe95974053601dcc` | cambiado |
| `src/arranque.py` | 16685 | `a5b48e8b6750bf2a` | cambiado |
| `src/autoprueba_integracion.py` | 146936 | `8fe5e553a7afe3c3` | cambiado |
| `src/schema.py` | 37951 | `2e92783ca6bbd1ce` | cambiado |
| `src/terminos.py` | 13010 | `ab3db24fd44bc4f0` | cambiado |

### Y el sello, que no sale en la tabla

`data/manifiesto.py` cubre `data/*.py` y `data/*.json`, así que `data/subida_sellada.txt` no aparece arriba — y es **el único archivo que la celda 4 de los notebooks lee** para comprobar que Drive está al día. El orden importa:

```
python -I data/preparar_subida.py --sellar   # 1. sella el estado local
```

y después sube **los archivos de la tabla más `data/subida_sellada.txt`**. Se sella antes de subir porque el sello describe lo que vas a poner en Drive, no lo que ya estaba.

Si lo olvidas no pasa nada silencioso: la celda 4 para la corrida y nombra como desincronizados los archivos que sí subiste. El síntoma apunta al sitio equivocado, y por eso se avisa aquí.

No subas `__pycache__/`.

## 3 · El orden, y por qué es ese

### PRIMERO · `M1` · GPU (A100 recomendada)

- duracion: ~30 min: ~10 de entrenamiento con gradient_checkpointing, ~4 de las dos generaciones por lotes, y ~14 del brazo hibrido, que genera caso a caso (lote 1) para no falsear la latencia que mide `costos`
- necesita: Drive montado, data/ en el proyecto, GROQ_API_KEY
- produce 13 artefactos en `results/`
- **M2 y M3 leen `m1_predicciones.json`. Si M1 no corre, los otros dos no tienen de donde partir.**

### SEGUNDO · `M2` · CPU basta

- duracion: ~3 min
- necesita: results/m1_predicciones.json, GROQ_API_KEY
- produce 11 artefactos en `results/`
- **Cambiar de GPU a CPU reinicia la sesion de Colab y vuelve a pedir el montaje de Drive. Es esperado.**

### TERCERO · `M3` · GPU (A100 recomendada)

- duracion: ~45 min
- necesita: results/m1_predicciones.json, GROQ_API_KEY, data/corpus.json
- produce 14 artefactos en `results/`
- **No depende de M2. Guarda checkpoint entre brazos, asi que un fallo en el brazo 4 no se lleva los anteriores.**

> ### M1 va DOS veces, y las dos en la misma sesion
>
> La ultima comparacion de estabilidad (`20261019T163319Z` vs `20261021T115654Z`) salio con `identicas: False`, `mismo_codigo: False` y `mismos_datos: True`. Con el codigo distinto entre las dos, esa diferencia **no se puede atribuir**: puede ser no-determinismo o puede ser el cambio de codigo. Y coincidir con el codigo distinto seria suerte, no reproducibilidad.
>
> - **corrida A** · re-ancla la huella. Su celda de estabilidad volvera a decir `mismo_codigo: false` y eso es lo esperado: compara contra una corrida anterior al cambio.
> - **corrida B** · compara contra A, con el mismo codigo. Esta es la que responde, y lo hace en los dos sentidos: identicas significa reproducible, y distintas significa no-determinismo medido.
>
> **Las dos en la MISMA sesion de Colab, sin reiniciar el entorno.** `estabilidad` compara tambien el hardware (`mismo_hardware`, por nombre de GPU). Si la sesion se cae en medio y Colab asigna otra GPU, la diferencia vuelve a tener dos explicaciones y se pierde la corrida.
>
> **Y M2 va despues de B, no de A**: lee `results/m1_predicciones.json`, que B sobrescribe. Corrido entre las dos, el juez puntuaria predicciones que el reporte no va a citar.

Se corren **seguidos y sin tocar nada en medio**. Cambiar `src/` entre M1 y M3 cambia la huella de código, y entonces `verificar_entrega.py` marca —con razón— que las corridas no son del mismo experimento.

## 4 · Al terminar los tres

```
python -I data/verificar_entrega.py   # artefactos, corridas, huellas
python -I data/reporte.py             # escribe REPORTE.md
```

`verificar_entrega.py` tiene que salir con **exit 0**. `reporte.py` se niega a escribir si falta un artefacto, en vez de dejar huecos silenciosos en el documento.

## 5 · Manifiesto completo

| archivo | bytes | huella |
|---|---|---|
| `src/agente.py` | 51307 | `fe95974053601dcc` |
| `src/arranque.py` | 16685 | `a5b48e8b6750bf2a` |
| `src/autoprueba_agente.py` | 7608 | `79d55fde59970603` |
| `src/autoprueba_integracion.py` | 146936 | `8fe5e553a7afe3c3` |
| `src/corridas.py` | 22726 | `40c91e3784194799` |
| `src/costos.py` | 10456 | `51c3d67a92871c8f` |
| `src/harness.py` | 45681 | `cf5aaa69cb50f921` |
| `src/juez.py` | 45735 | `398f762b2b36e81a` |
| `src/metricas.py` | 69838 | `b6a5c52f8b4f00a6` |
| `src/rag.py` | 36243 | `8c1355eee23a502c` |
| `src/ragas_eval.py` | 11065 | `1b522e3f52ae02d7` |
| `src/redaccion.py` | 11009 | `3d97788aa4b2a345` |
| `src/reglas.py` | 20577 | `7fbb779af28f8cb5` |
| `src/schema.py` | 37951 | `2e92783ca6bbd1ce` |
| `src/sistema.py` | 37455 | `112650e9a547f6c2` |
| `src/terminos.py` | 13010 | `ab3db24fd44bc4f0` |
| `src/tokenizadores.py` | 9725 | `1020d269516503fb` |
| `data/ampliar_categorias.py` | 19615 | `e8efa777c6718589` |
| `data/ampliar_corpus.py` | 17490 | `763a1863abffa07c` |
| `data/ampliar_corpus_1095.py` | 12805 | `0a4c7421cfde5bee` |
| `data/ampliar_corpus_393_472.py` | 12096 | `4e794b12c6386380` |
| `data/ampliar_corpus_jurisprudencia.py` | 14718 | `eda4f1e818c8a6d0` |
| `data/ampliar_eval_set.py` | 63902 | `180733283d4866da` |
| `data/anotar_fundamentos.py` | 13901 | `a2d8c4ca96b9dedc` |
| `data/auditar_causas_abiertas.py` | 13434 | `2e60e6557d4e4db7` |
| `data/auditar_cobertura.py` | 8326 | `97139be7586fbfd5` |
| `data/auditar_corpus.py` | 8297 | `e7aa334303268801` |
| `data/auditar_notebooks.py` | 18311 | `5a71ea21d021d84c` |
| `data/auditar_proyecto.py` | 15496 | `770294249bd3f0e6` |
| `data/auditar_tool_use.py` | 9850 | `a2f73d7792e2acbe` |
| `data/autoprueba_reporte.py` | 20750 | `8368eb0464704cb9` |
| `data/calibracion_juez.py` | 18070 | `1d3e2576517c18ee` |
| `data/casos_reales.py` | 16822 | `ac9d1ef1123e9326` |
| `data/codificar_hechos_dataset.py` | 17101 | `33f74b1d9ddf6883` |
| `data/codificar_hechos_eval.py` | 18687 | `fcab95b27e726f36` |
| `data/codificar_hechos_m3.py` | 16167 | `dab5cd4bab8dec0d` |
| `data/construir_dataset.py` | 20653 | `49972facb86d5baf` |
| `data/construir_eval_m3.py` | 21883 | `649b5644c87db8a6` |
| `data/construir_eval_m3_terminos.py` | 14253 | `b9328467e077f02a` |
| `data/construir_eval_v2.py` | 37006 | `bba451dabd7677bd` |
| `data/descomponer_baseline.py` | 7934 | `58aa455723ac5b0c` |
| `data/diagnostico_cumplimiento.py` | 11752 | `93bb3008c9dc896c` |
| `data/doble_anotacion.py` | 35350 | `5e083e82e75753f2` |
| `data/formularios.py` | 12508 | `5c997e1d98f28b1b` |
| `data/manifiesto.py` | 13997 | `975e9652fdbd8321` |
| `data/medir_metricas_nuevas.py` | 6129 | `b93d8f4c6763b88f` |
| `data/medir_redaccion.py` | 8397 | `615e6377a5cf2d5e` |
| `data/nuevos_a.py` | 30974 | `3ac26573e786722c` |
| `data/nuevos_b.py` | 37186 | `25c29a638a1bfbc5` |
| `data/nuevos_c.py` | 13694 | `3a57e1b91b08a152` |
| `data/nuevos_d.py` | 9655 | `371017cefe4438ef` |
| `data/pares_minimos.py` | 35624 | `d65ad8469271c774` |
| `data/preparar_subida.py` | 14451 | `8cacdec6ad58dcb7` |
| `data/publicar_rezagados.py` | 4407 | `2c291d63ab4fb31f` |
| `data/reparar_corpus.py` | 11901 | `1fbcac92d83f066d` |
| `data/reparar_meta.py` | 5643 | `4c5894fb4779bc29` |
| `data/reporte.py` | 85844 | `0b1250c1acf0c411` |
| `data/reverificar_corpus.py` | 21098 | `81823de94149f6c7` |
| `data/revision_abogado_v3.py` | 10681 | `990b382d9ffa5e24` |
| `data/validacion_juez.py` | 39827 | `f396d6735b583b2d` |
| `data/validar_extractor.py` | 16624 | `4c689d526ae16045` |
| `data/verificar_entrega.py` | 11807 | `1cfee21fd8aa9f36` |
| `data/corpus.json` | 125864 | `391ea7d3c7c61bc5` |
| `data/dataset.json` | 249885 | `3af759260df7bdd3` |
| `data/eval_set.json` | 80388 | `9f409b0a0eb70702` |
| `data/eval_set_m3.json` | 39778 | `70d88761e183dcd1` |
| `data/eval_set_v2.json` | 113139 | `0750013bb6950f4e` |
| `data/eval_set_v3.json` | 175078 | `f422a2cdfce5811f` |
| `data/fixtures_salidas.json` | 4741 | `5c84738544707c97` |
| `data/inyecciones.json` | 21555 | `7b50eedf62875fd1` |
| `data/normas.json` | 6784 | `eeb451b814fa25b7` |
| `data/revision_abogado_v3.json` | 6593 | `77ddde52b17e46e8` |
| `notebooks/M1_finetuning.ipynb` | 105805 | `e59a1198a5ead71d` |
| `notebooks/M2_harness.ipynb` | 65576 | `2a61240c93144a70` |
| `notebooks/M3_rag.ipynb` | 80829 | `73288ab8b8c0e2b0` |

**75 archivos · 2545138 bytes · `7b75680429404e9c`**
