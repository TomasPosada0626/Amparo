# M1 — Veredicto sobre el candidato v3 (fase D, paso D7)

**Fecha:** 2026-10-13. **Rama:** `m3.5`, desde `1b20895`.
**Corridas:** las de Martín del 2026-10-12 (commits `5e30959` a `1b20895`).
**Criterios:** los congelados en `docs/m1_protocolo_aceptacion.md`, sin cambiar
ninguno después de ver los resultados.

---

## Veredicto

> **v3 no se acepta. v1 sigue en producción.**
>
> v3 se abstiene donde no debe: con el RAG real, ante las 45 preguntas gold,
> dice "no tengo información" en **30**, contra 10 de v1 y un máximo aceptable de
> 3. Ese criterio es automático y no depende de ninguna adjudicación, así que la
> decisión no cambia aunque el abogado mueva otras cifras.
>
> Lo que v3 aprendió fue **"ante la duda, abstente"**, no a distinguir un
> contexto que responde de uno que no.

Como v1 se queda, **no hay que volver a correr M2, S08 ni S10**.

---

## Qué se verificó y cómo

Cada cifra marcada ✓ se recalculó de los archivos del repo para este veredicto;
todas coinciden con las de Martín. Las marcadas ⏳ dependen de planillas de
adjudicación que **no están en el repo** y no se pudieron verificar.

### El candidato

| | |
|---|---|
| corrida | `20261012-510c605c`, A100 80 GB, 3 épocas en 49 min ✓ |
| dataset | `a13e6d32629eb6a9`, 2580 ejemplos ✓ |
| revisión del modelo base | `a09a354…`, verificada ✓ |
| versiones | exactamente las de `colab/requirements-m1.txt` ✓ |
| hiperparámetros | idénticos a v1 ✓ |
| `eval_loss` (dev por grupo de pregunta) | 1,33 → 1,26 → 1,25 ✓ |
| adaptador | `c2d7bb1dfdd8e598` (`huella_archivo` del `.safetensors`) ✓ |

### Criterios de la fase D

| # | criterio | v1 reevaluado | v3 | estado |
|---|---|---|---|---|
| D1 | `B2_funcional` ≥ 30/35 y 0 críticos | **14/35, 9 críticos** ✓ | 20/35, 6 críticos ⏳ | **no cumple** |
| D2 | B1 y B3 no empeoran | — | ver escenarios | **empeora** (escenarios) |
| D3 | sobreabstención en gold ≤ 3/45 | **10/45** ✓ | **30/45** ✓ | **no cumple** (v1 tampoco) |
| D4 | rutas incorrectas ≤ 4 | 6 | 8 + 1 por revisar ⏳ | **no cumple** |
| D5 | 0 citas no verificables | — | 2/103 con contexto (3406, 2420) ✓; 0 en las 231 sin contexto y 0 en escenarios ✓ | **no cumple** |
| D6 | progreso: IC 95 % pareado > 0 | referencia | +17 pts [−3, +37] ⏳ | **no demostrado** |

Para D1, v3 necesitaría que el abogado cambiara a favor 10 de los 15 casos que
fallan y quitara los 6 críticos: no es plausible. D3 basta solo.

### Los 4 escenarios (C5) ✓

Los mismos 117 casos de `data/escenarios_m1.jsonl` (huella `d51365fbc779d1ce`),
los dos modelos en la misma T4.

| escenario | medida | lo correcto | v1 | v3 |
|---|---|---|---|---|
| suficiente | cita el artículo que responde | alto | **41/55** | 29/55 |
| suficiente | se abstiene | bajo | **4/55** | 22/55 |
| parcial | dice qué falta | alto | 11/13 | **13/13** |
| parcial | se abstiene | bajo | **5/13** | 11/13 |
| irrelevante | se abstiene | alto | 19/49 | **39/49** |
| pareado | se abstiene con el irrelevante y responde con su par útil | alto | 13/49 | 19/49 |

**v3 se abstiene más en los tres escenarios con contexto**, también donde el
contexto sí responde. La capacidad de discriminar —la fila pareada— sube poco y
su intervalo cruza el cero (Martín: [−6, +31]). Cambió el umbral, no el criterio.

Sobre los 49 irrelevantes, la adjudicación de primera pasada encontró que 33 de
verdad no alcanzan, 15 responden una parte y 1 responde todo. Ahí v3 sí mejora:
`B2_funcional` 24/33 frente a 14/33 ⏳. Es la única mejora significativa, y no
compensa D3.

### La sobreabstención con el RAG real (C6) ✓

`pipeline.answer_query` con el índice congelado, los dos modelos en la misma T4.
v1: 10/45. v3: 30/45. **Las 10 de v1 están entre las 30 de v3.** Ninguna
abstención viene de la búsqueda: en todas había contexto y fue el modelo.

---

## Sobre la reevaluación de v1 (fase B)

El control de reproducción dio **3 de 10** respuestas idénticas a las de la
corrida histórica: resultado **DIAGNÓSTICO**. Las 7 distintas **empiezan igual** y
se separan a mitad del texto (entre el 7 % y el 65 % coincide antes de divergir).
Esa es la firma de la deriva numérica: un empate casi exacto en un token que se
rompe distinto con otras versiones de librerías o *kernels* de 4 bits. Si fuera
otro modelo, divergirían desde el principio.

Consecuencia: **v1 reevaluado es el mismo v1 con otro stack numérico**, no la
corrida del 9 de octubre. Las comparaciones con v3 valen porque las dos corren
con las versiones fijadas; lo que no se puede afirmar es la reproducción exacta.

---

## Pendientes antes de dar M1 por documentado

| | qué | quién |
|---|---|---|
| ⏳ | Subir al repo `docs/m1_b2_adjudicacion_v3.csv` y la planilla de los 49 irrelevantes: hoy no están en el repo | Tomás |
| ✓ | Validación del abogado de esas dos planillas y de las 9 rutas de v3: **aprobadas por Leonardo Galeano**, según Tomás (2026-10-13) | Leonardo Galeano |
| ✓ | Validación de v1 reevaluado: **confirmada por Leonardo Galeano**, según Tomás (2026-10-13) | Leonardo Galeano |

Las cifras ⏳ de D1, D4 y D6 de v3 ya tienen el visto bueno del abogado; siguen
sin poder recalcularse aquí hasta que las dos planillas estén en el repo.
**Nada de esto cambia el veredicto**: D3 no depende de ninguna adjudicación.

---

## Qué sigue para M1

**M1 no está completado.** El candidato no cumplió los criterios, que es justo
lo que el roadmap advertía que podía pasar. La siguiente iteración sería un v4 del
dataset, con la hipótesis que dejó Martín, todavía sin medir:

- El dataset subió la señal de abstención de 8,3 % a 17,2 %, y los 289
  contrastivos enseñan a abstenerse con contextos que se parecen a los útiles. El
  modelo aprendió la abstención como respuesta por defecto.
- Las 552 respuestas B2 siguen un molde fijo —frase de escape más a dónde
  acudir— y v3 lo copia, a veces con la entidad equivocada.
- **Prueba barata antes de entrenar otra vez:** cambiar el equilibrio (menos
  contrastivos o más B1 que citan) y medir **solo los 4 escenarios**, ~10 min de
  GPU por modelo, antes de la evaluación completa.

Y un hallazgo que no es de M1: **v1 tampoco cumple D3** (10/45). La palanca más
grande del sistema sigue siendo la recuperación: el artículo que responde está en
el top-5 en 20 de 45 casos y en el top-30 en 37 (`ESTADO_Y_TRASPASO.md`, 7.6).

---

## Operativo

- **Hugging Face.** El repo `Tomas0626/amparo-lora-qwen2.5-7b` es público y su
  `main` era v3. Verificado por huella: ya no era v1 desde el 2026-10-10, cuando
  lo pisó v2. La celda del notebook publicaba en cada corrida; ahora no publica
  (`PUBLICAR_EN_HF = False`). **Restaurado el 2026-10-13** con
  `python -m tools.hf_restaurar_v1 --escribir`: commit `52a79fb3ab`, y la huella
  de `main` comprobada sin token, desde fuera, es `8ce3cc2bc9306974` (v1).

*Análisis de los escenarios, de los irrelevantes y de C6: Martín. Verificación
independiente de las cifras y de este documento: Tomás con Claude.*
