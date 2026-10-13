# M1 — Cierre, 2026-10-13

**M1 queda cerrado con v1** (`8ce3cc2bc9306974`), que ya estaba en producción y
es el `main` del repo de Hugging Face. Lo decidió Tomás con el protocolo del
2026-10-13 (`docs/m1_protocolo_aceptacion.md`): la abstención deja de ser
requisito, y lo que se exige es que el modelo responda bien. Con ese criterio, v1
es el mejor de los adaptadores entrenados.

## Por qué v1

Todas las cifras son de la misma prueba, la de los 4 escenarios y las 45
consultas gold con el RAG real, medida el 2026-10-12 (v1, v3) y el 2026-10-13 (v4
y v1 como control en la misma sesión):

| responder bien | v1 | v3 | v4 |
|---|---|---|---|
| contexto suficiente: cita el artículo que responde | **41/55** (40 hoy) | 29/55 | 25/55 |
| contexto suficiente: se niega a responder | **4/55** (5 hoy) | 22/55 | 25/55 |
| contexto parcial: dice qué falta | 11/13 | 13/13 | 12/13 |
| consultas gold con RAG real: se niega | **10/45** (8 hoy) | 30/45 | 30/45 |
| citas no verificables, 103 con contexto | 1 (2420) | 2 (3406, 2420) | — |
| rutas incorrectas | 6 | 8 + 1 | — |

v3 y v4 se entrenaron para abstenerse más ante un contexto que no alcanza, y lo
hicieron: se niegan a responder incluso con el artículo correcto delante (13 de
21). Con el objetivo de responder, eso es peor.

## Lo que v1 no cumple, y queda escrito

- **1 cita no verificable en 103** (caso 2420, art. 210) en la evaluación sin
  RAG. En el sistema que se entrega no llega al usuario: el verificador del
  pipeline reemplaza una respuesta con citas no verificables; en las 45 gold de
  hoy, 0 casos.
- **6 rutas incorrectas** frente a un umbral de 4. Es una limitación conocida,
  no corregida en M1.
- **Responde bien 1 de 45 gold en S10.** No es un problema del modelo: el
  artículo correcto llega al contexto en 21 de 45 consultas (H23). Esa es la
  palanca de M3.

## Lo que queda de los candidatos

v3 y v4 están documentados (`docs/m1_veredicto_v3.md`, `docs/m1_veredicto_v4.md`)
y sus resultados siguen en `results/`. Sus adaptadores se borraron de Drive el
2026-10-13 (papelera, recuperables 30 días); v3 sigue además en el historial de
Hugging Face.

Lo que v4 dejó y sirve: el dataset sin el defecto H22 (las abstenciones ya no
mandan a la autoridad equivocada: de 8/30 a 2/30 en gold) y el notebook de M1 con
la prueba barata dentro. Si algún día se reentrena, se parte de ahí.

## Para M2 y M3

v1 es el adaptador que usan los dos (`tools/evaluation/config.DRIVE_ADAPTER_DIR`,
`tools/rag/config.LORA_ADAPTER_PATH`). M2 lo evalúa; M3 lo usa como generador
del RAG. Ninguno de los dos entrena.
