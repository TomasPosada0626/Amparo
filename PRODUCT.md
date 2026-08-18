# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Definido en la wiki del proyecto (sección "Tecnologías" de Home): Python como lenguaje principal; PyTorch y Hugging Face Transformers para el modelo de lenguaje; PEFT, LoRA y TRL para el Fine-Tuning; FastAPI como backend; PostgreSQL como base de datos; FAISS o pgvector para la recuperación de información en el sistema RAG (aún por definir cuál de los dos); Docker para contenedores; Git y GitHub para control de versiones. La interfaz de usuario final del producto (más allá de herramientas internas de desarrollo, como el comparador de modelos en `tools/`) todavía no tiene tecnología definida en la wiki.

## Users

Público general en Colombia que enfrenta problemas legales de cualquier ámbito del derecho colombiano, no abogados ni estudiantes de derecho. El agente está pensado para cubrir la totalidad de los ámbitos legales existentes en Colombia, no solo un subconjunto; los casos más frecuentes en el día a día del público objetivo son de la vida cotidiana (salud/EPS, despido, arriendo, reporte en centrales de riesgo, accidentes de tránsito, relaciones laborales, garantías de consumo, embargos, comparendos de tránsito), pero esa lista es una muestra de los casos más comunes, no el límite del alcance. Suelen consultar en momentos de urgencia o vulnerabilidad (riesgo de salud, pérdida de empleo, desalojo).

## Product Purpose

Amparo es un asistente jurídico basado en IA (LLMs + RAG) que responde consultas legales, analiza documentos y entrega información fundamentada en fuentes verificadas, evitando inventar normas. Es un proyecto de portafolio/aprendizaje que simula deliberadamente un entorno de producción LegalTech (arquitectura escalable, seguridad, pruebas, APIs REST, DevOps) para demostrar buenas prácticas de ingeniería de software; todavía no está expuesto a usuarios reales ni asume responsabilidad legal real.

## Positioning

A diferencia de un chatbot genérico de LLM, Amparo fundamenta sus respuestas en fuentes verificadas (RAG) en vez de generar afirmaciones legales sin respaldo. El dataset de referencia exige respuestas "breves, fundamentadas y prudentes (sin inventar normas)": el mecanismo diferenciador es la disciplina de no alucinar derecho, no solo la fluidez conversacional.

## Operating Context

Un usuario sin formación jurídica describe su problema en lenguaje cotidiano, a veces en un momento de urgencia. El sistema puede analizar documentos que aporte el usuario. La respuesta debe orientar sobre la figura o mecanismo legal aplicable (p. ej. acción de tutela, derecho de petición, habeas data, restitución de inmueble, reclamación laboral) y qué evidencia reunir, dentro del marco legal colombiano.

## Capabilities and Constraints

- Responde consultas legales y analiza documentos usando LLMs + RAG.
- Restricción dura: nunca debe inventar normas ni citar fuentes inexistentes; ante incertidumbre, debe ser prudente en vez de asertivo.
- Alcance geográfico/legal: derecho colombiano (evidenciado por el dataset: tutela, EPS, habeas data, derecho de petición, etc.).
- Pendiente de decidir: si el producto final tendrá interfaz web además de la API, FAISS vs. pgvector para el RAG, y qué corpus de "fuentes verificadas" lo alimentará.

## Brand Commitments

Nombre del producto: "Amparo". No hay logo, tono de voz formalizado ni otros activos de marca confirmados todavía.

## Evidence on Hand

- `private/dataset_legal_30_ejemplos.md`: 30 ejemplos de entrada/salida (consulta → respuesta esperada) para el agente legal colombiano. Es un archivo privado, explícitamente marcado para no versionarse ni usarse como contenido público.
- No existen todavía testimonios, casos de estudio, prensa ni métricas reales de uso. El trabajo futuro no debe inventar estos elementos.

## Product Principles

1. Nunca inventar normas: toda respuesta debe ser trazable a una fuente verificada o señalar explícitamente la incertidumbre.
2. Prudencia sobre certeza: respuestas breves y cautelosas que orienten sin sustituir el criterio de un abogado.
3. Anclaje al mecanismo legal real: cada respuesta apunta a una figura jurídica concreta del ordenamiento colombiano (tutela, derecho de petición, habeas data, etc.), no a consejos genéricos.
4. Accesible para no abogados: el lenguaje debe ser comprensible para alguien sin formación jurídica, muchas veces en un momento de estrés o urgencia.
5. El rigor de ingeniería es parte del producto: como proyecto de portafolio, la calidad de arquitectura, seguridad, pruebas y DevOps demuestra tanto como la funcionalidad legal.

## Accessibility & Inclusion

No se ha definido un estándar formal de accesibilidad. Nota de contexto: los usuarios primarios suelen estar en situaciones de vulnerabilidad o urgencia (riesgo de salud, pérdida de empleo, desalojo), por lo que la claridad del lenguaje y la reducción de fricción cognitiva son relevantes para el trabajo de diseño futuro.
