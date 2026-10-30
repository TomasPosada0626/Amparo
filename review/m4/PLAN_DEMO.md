# Plan para Demo Day — Amparo

Tres prioridades, en orden. Cada una enlaza con una observación de [`README.md`](README.md).

## 1. [P1] Mostrar el costo y el efecto real del componente visual (H1, H4)

- **Qué:**
  - Medir la latencia con y sin imagen por caso, reportando la mediana y la media sin el arranque en frío.
  - Repetir el delta con y sin imagen al menos 3 veces por caso, con caché vacía.
- **Por qué:** hoy el delta muestra acierto, pero no costo. Además, el caso donde la imagen aporta (m06) cambia entre corridas.
- **Cómo comprobarlo:** una tabla en el README y en la diapositiva con los segundos con y sin imagen, y la tasa de acierto con y sin imagen por caso.
- **Esfuerzo estimado:** unas 2 horas, más 3 corridas de M3 (unas 18 llamadas).

## 2. [P1] Marcar lo que lee el VLM como «no verificado» (H2)

- **Qué:** rotular el bloque leído de la imagen y añadir una guarda que avise cuando el texto libre menciona un plazo que `plazo_dias` no tiene.
- **Por qué:** m10 y m04 son los casos que más pueden confundir al público si la lectura se presenta como un hecho del documento.
- **Cómo comprobarlo:** en la Demo, m10 muestra la advertencia y ningún otro caso la muestra. m04 aparece con su limitación declarada.
- **Esfuerzo estimado:** alrededor de 1 hora.

## 3. [P2] Corrida de Demo reproducible (H3)

- **Qué:** clonar un SHA o tag fijo en el notebook, generar `m4/corrida_m4.json` con commit, GPU, modelo, reranker y hora, y guardar las salidas de las celdas clave.
- **Por qué:** evita que la Demo ejecute un código distinto al evaluado.
- **Cómo comprobarlo:** el commit del manifiesto coincide con el mostrado en la Demo.
- **Esfuerzo estimado:** unos 30 minutos.
