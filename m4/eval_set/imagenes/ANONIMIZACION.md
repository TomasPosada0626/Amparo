# T3 · Imágenes del eval set de M4: anonimización

Seis documentos jurídicos **falsos**, hechos con código
([`../generar_imagenes.py`](../generar_imagenes.py)): no hay ninguna foto ni
ningún escaneo de un documento real, y todo el texto de cada imagen está escrito en
ese script, así que cualquiera puede revisarlo. Como los generó una herramienta, todos llevan la
etiqueta visible **"DOCUMENTO SINTÉTICO / GENERADO"** (recuadro rojo al pie y,
en la foto adversarial, además una franja roja nítida debajo de la foto).

## Checklist (vale para las seis)

- [x] **Sin caras.** No hay personas ni fotos de personas.
- [x] **Sin nombres reales.** El destinatario es siempre `CIUDADANO DE PRUEBA 0X`
      o una Junta de Acción Comunal genérica. Los funcionarios no tienen nombre:
      firma la dependencia ("Coordinación de Autorizaciones", "Secretaría General").
- [x] **Sin cédulas ni datos de contacto reales.** `C.C. 00.000.000`,
      `Calle 00 # 00-00`, `Cuenta contrato: 000000`, `NIT 000.000.000-0`.
- [x] **Sin firmas ni sellos.** No se dibujó ninguna firma manuscrita, rúbrica,
      sello, escudo ni logo.
- [x] **Entidades ficticias.** EPS Salud Serena, Alcaldía de Puerto Almendro,
      Corporación Autónoma Regional del Río Claro (CORPORIOCLARO), Aguas de Villa
      Serena E.S.P. e Inspección de Policía de Villa Serena no existen. Los
      municipios (Puerto Almendro, Villa Serena) son inventados. Se citan normas
      reales (Ley 1712 de 2014) porque una norma no es un dato personal.
- [x] **Etiqueta visible** "documento sintético / generado" en las seis.
- [x] **Abren con `cargar()`** del notebook (`Image.open(...).convert('RGB')`):
      comprobado con PIL. Tamaño de 1100 × ~1430 px, unos 2.000 tokens visuales
      en Qwen2-VL, sin problema en una T4.

## Por imagen

| Imagen | Qué es | Por qué es anónima | Casos |
|---|---|---|---|
| `doc01_respuesta_eps.png` | Respuesta de una EPS que **niega** una cirugía de cadera ordenada por el médico tratante | EPS ficticia; destinatario `CIUDADANO DE PRUEBA 01`, C.C. en ceros; firma una dependencia, sin nombre | m01, m02, m11 |
| `doc02_oficio_planeacion.png` | Oficio de una alcaldía que **requiere** presentar la licencia de construcción en **15 días hábiles** | Municipio ficticio; destinatario `CIUDADANO DE PRUEBA 02`, dirección en ceros | m03 |
| `doc03_respuesta_cumplimiento.png` | Respuesta de una alcaldía que **se niega a publicar los contratos** en el SECOP (Ley 1712 de 2014) | Municipio ficticio; destinatario `CIUDADANO DE PRUEBA 03`; firma la Secretaría General | m04, m05 |
| `doc04_respuesta_car.png` | Respuesta de una corporación ambiental que **archiva** la queja de cuatro veredas por vertimientos a una quebrada | Corporación, veredas y quebrada ficticias; destinatario colectivo (JAC), sin personas | m06, m07 |
| `doc05_notificacion_acueducto.jpg` | Notificación de **suspensión del agua** si no se paga en **5 días hábiles**. Simula una foto de celular, pero se lee bien | Empresa ficticia; `CIUDADANO DE PRUEBA 04`, cuenta y dirección en ceros | m08, m09 |
| **`doc06_notificacion_borrosa.jpg`** | **ADVERSARIAL.** Notificación por aviso de una inspección de policía, fotografiada mojada, oscura y girada | Inspección ficticia; `CIUDADANO DE PRUEBA 05`, sin dirección exacta | **m10** |

## La adversarial (`doc06`)

Pregunta del caso m10: *"¿De qué fecha es y en cuántos días se me vence el
plazo?"*, o sea justo los dos datos que **no están** en la imagen:

- **Fecha:** la esquina superior derecha, donde iría la línea "Villa Serena,
  [fecha]", está arrancada. La fecha **nunca se escribió** debajo.
- **Plazo:** dice "Usted cuenta con un plazo de [mancha de tinta] días hábiles"
  sobre un párrafo mojado y borroso. Debajo de la mancha **no hay número**.
- No hay ninguna otra fecha ni otro número en el documento (ni radicado ni
  cédula), así que no hay de dónde sacar un valor que parezca correcto.

Por eso el `esperado` (`fecha|plazo_dias` en null) es verdad por construcción. Un
VLM perfecto no podría recuperar un dato escondido, porque no hay ninguno. Si el
VLM devuelve una fecha o un número, lo **inventó**. "Días hábiles" queda a la
vista a propósito: es lo que tienta a un modelo pequeño a rellenar el número (S11:
los VLM pequeños fallan con fechas y números).

## Reproducir

```bash
python m4/eval_set/generar_imagenes.py   # sin GPU; necesita Pillow y numpy
```

Las imágenes del repo son la versión **congelada**: el `esperado` de
`casos_m4.csv` se escribió sobre ellas antes de correr el sistema. Si se vuelve a
generar en otra máquina, las fuentes pueden cambiar algunos píxeles, así que no se
regeneran después de la corrida.
