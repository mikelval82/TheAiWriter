# Project Riley: Multimodal Multi-Agent LLM Collaboration with Emotional Reasoning and Voting

## Metadata
- **Autores**: Ana Rita Ortigoso, Gabriel Vieira, Daniel Fuentes, Luis Frazão, Nuno Costa, António Pereira
- **Año**: 2025
- **Keywords**: multimodal, multi-agent, LLM, emotional reasoning, voting, Inside Out, symbolic reasoning, RAG, emergency response, abliterated models, Ollama, user study, explainability, vision-language models

## Abstract
El trabajo presenta Project Riley, una arquitectura conversacional multimodal y multi-modelo que simula razonamiento influido por estados emocionales. Inspirada en Inside Out, orquesta cinco agentes emocionales (Alegría, Tristeza, Miedo, Ira, Asco) que debaten en múltiples rondas para generar y refinar respuestas. Un mecanismo final de síntesis y votación integra o prioriza perspectivas emocionales, segmentando la salida en REASONING, THOUGHTS y FINAL ANSWER. El prototipo local combina LLMs de texto y visión y emplea modelos de razonamiento y procesos de autorrefinamiento; se optimiza con modelos “abliterated” para mayor expresividad emocional. A partir de Riley se desarrolla Armando, variante para emergencias que incorpora RAG y seguimiento de contexto acumulativo para respuestas verificadas y emocionalmente calibradas. Una evaluación con usuarios sugiere buen desempeño en escenarios estructurados, con alta alineación emocional y claridad comunicativa.

## Contribuciones Principales
- Presenta una arquitectura conversacional multimodal y multi-agente que simula razonamiento afectivo mediante cinco agentes emocionales con diálogo multi-ronda.
- Introduce un flujo de votación y análisis con modelos de razonamiento y justificaciones, seguido de una síntesis final segmentada (REASONING, THOUGHTS, FINAL ANSWER) que integra o prioriza emociones dominantes.
- Integra LLMs de texto y visión en entorno local con selección de modelos ligera y uso de modelos “abliterated” para mejorar la expresividad emocional.
- Desarrolla Armando, variante orientada a emergencias que incorpora RAG y contexto acumulativo, y simplifica votación/síntesis para reducir latencia en situaciones críticas.
- Ofrece transparencia mediante registro exhaustivo de interacciones y parámetros, y evalúa el prototipo con 17 participantes y un cuestionario estructurado en tres dimensiones (Apropiación Emocional; Claridad y Utilidad; Naturalidad/Humanización).
- Propone una fusión simbólico-neuronal (roles por agente, historial, votación con justificación, salidas segmentadas) para mejorar la explicabilidad.

## Metodología
Arquitectura por fases: (1) Input: el usuario puede aportar texto e imágenes; un LLM de visión describe imágenes para enriquecer el contexto. Se inicializan historiales separados por emoción. (2) Multi-round Processing (LLM de texto): Round 0, cada emoción genera una respuesta inicial, almacenada en su historial. Round 1, los agentes revisan las respuestas de los demás y responden manteniendo su identidad emocional. Round 2, cada agente sintetiza una perspectiva refinada tras el intercambio. Round 3, cada agente reevalúa la pregunta original y ofrece una respuesta final por emoción. (3) Voting and Analysis: cada agente cambia a un modelo de razonamiento manteniendo su identidad emocional y emite un voto con breve justificación evaluando las respuestas candidatas. (4) Final Synthesis: un modelo de razonamiento integra las perspectivas; si hay emoción ganadora, la respuesta final refleja principalmente esa emoción; si hay empate, sintetiza múltiples perspectivas. La salida se segmenta en REASONING, THOUGHTS y FINAL ANSWER, y se exponen a los usuarios todos los registros y procesos.
Implementación del prototipo (Riley): despliegue local con Ollama. Hardware: Intel i3-9100, 8 GB RAM, GPU RTX 3070 8 GB VRAM. Modelos: huihui_ai/llama3.2-abliterate:3b (texto), gemma3:4b (visión), huihui_ai/deepseek-r1-abliterated:8b (razonamiento). Se priorizan modelos compactos para permanecer en VRAM y minimizar cambios; se usa abliteration para reducir sobre-filtrado de contenidos emocionales.
Evaluación con usuarios: 17 participantes; 5 temas (pérdida de empleo, rupturas/pérdida de amistad, decisiones personales difíciles, ansiedad académico-laboral, conflictos familiares/intergeneracionales). Cuestionario Likert (1–5) en tres dimensiones: Apropiación Emocional, Claridad y Utilidad, Naturalidad/Humanización; además, pregunta abierta sobre la emoción predominante.
Variante Armando (emergencias): mantiene la estructura emocional pero simplifica votación/síntesis para reducir latencia; integra RAG con embeddings (mxbai-embed-large) y contexto acumulativo (tópicos clave, keywords, tres últimas preguntas, resumen dinámico). El enriquecimiento RAG se aplica justo antes de la síntesis final para evitar que los hechos se diluyan durante el debate emocional.

## Resultados Clave
- Apropiación emocional: empatía más alta en Conflictos familiares/intergeneracionales (4.59, moda=5). Adecuación emocional al contexto más alta en Pérdida de empleo y Decisiones difíciles (4.71, moda=5). Rupturas/pérdida de amistad obtiene sistemáticamente las puntuaciones más bajas (empatía 4.12; adecuación 4.41).
- Alineación votos-usuario: mayor en Conflictos familiares/intergeneracionales (4.35); menor en Rupturas/pérdida de amistad (3.94).
- Claridad y utilidad: claridad máxima en Pérdida de empleo (4.71, moda=5). Consistencia con la pregunta más alta en Decisiones difíciles (4.65) y más baja en Rupturas/pérdida de amistad (4.41). Utilidad más baja en Rupturas/pérdida de amistad (3.88) y más alta en Decisiones difíciles y Conflictos familiares (4.29).
- Visualización del proceso: la peor valorada (3.76–4.24), indicando beneficio percibido limitado.
- Naturalidad/Humanización: moderada; máxima en Conflictos familiares (3.88) y mínima en Ansiedad académico/profesional (3.59).
- Emoción predominante percibida por tema: Ansiedad académico/profesional → Alegría; Rupturas/pérdida de amistad → Tristeza; Decisiones difíciles → Miedo y Alegría (equilibradas); Conflictos familiares → Alegría; Pérdida de empleo → Miedo.
- Armando (RAG vs no RAG): para "Where is the fire happening?", RAG produce ubicación precisa (dirección y coordenadas) y pautas concretas; sin RAG, respuesta genérica. Para "A fire is happening! It's difficult to breathe.", ambos dan pautas útiles, RAG añade estructura. Para "Which number should I call? (Portugal)", RAG identifica 112 pero sugiere verificar país, introduciendo ambigüedad sobre la conciencia geográfica del sistema.
- Posicionamiento de RAG: aplicar el enriquecimiento justo antes de la síntesis final mantiene el equilibrio emocional y asegura exactitud factual en la salida.

## Limitaciones
- Tamaño muestral reducido (n=17) y dominios de interacción limitados, lo que restringe la generalización.
- Desempeño más débil en escenarios de alta complejidad relacional (rupturas/pérdida de amistad); naturalidad percibida solo moderada.
- Dependencia de modelos “abliterated”, que pueden conllevar riesgos de seguridad/seguridad de contenidos y sesgos al disminuir filtros.
- Restricciones de hardware/VRAM que provocan cambios de modelo (p. ej., al describir imágenes), aumentando latencia.
- Visualizaciones del proceso con utilidad percibida baja; la interfaz puede no apoyar suficientemente la reflexión del usuario.
- Posible ambigüedad geográfica en Armando por formulaciones de prompt que piden verificar país incluso cuando hay datos de localización.
- Falta de evaluación en benchmarks estandarizados y métricas objetivas de razonamiento/verdad factual más allá de la encuesta de usuarios.
- Conjunto de emociones fijado en cinco básicas (aunque extensible), no se exploran empíricamente otras taxonomías en este estudio.

## Trabajo Futuro
- Afinar LLMs por emoción entrenados por separado y comparar contra un único modelo condicionado por prompt con métricas objetivas.
- Ampliar la evaluación con muestras mayores, contextos más variados y benchmarks (p. ej., tareas multimodales y de razonamiento factual) para medir precisión y robustez.
- Mejorar la visualización del proceso (hacerla opcional/discreta) y adaptar prompts según el tipo de situación para mayor inmersión y adecuación contextual.
- Establecer una sintaxis/annotación estructurada para las fuentes RAG (marcadores de urgencia, localización, contactos) que priorice la recuperación precisa.
- Refinar el manejo de contexto geográfico en Armando para emitir recomendaciones inequívocas y locales sin introducir dudas.
- Optimizar la gestión de modelos/VRAM para reducir latencia (carga persistente, modelos multimodales unificados, cuantización adicional).
- Explorar modelos emocionales alternativos (Plutchik, PAD, Circumplex) y su impacto en resultados y usabilidad.
- Reforzar salvaguardas y alineación ética al usar modelos abliterated, equilibrando expresividad y seguridad.

## Citas Relevantes
['"This paper presents Project Riley, a novel multimodal and multi-model conversational AI architecture oriented towards the simulation of reasoning influenced by emotional states."', '"The system comprises five distinct emotional agents — Joy, Sadness, Fear, Anger, and Disgust — that engage in structured multi-round dialogues to generate, criticise, and iteratively refine responses."', '"A final reasoning mechanism synthesises the contributions of these agents into a coherent output that either reflects the dominant emotion or integrates multiple perspectives."', '"To the best of our knowledge, this is the first framework that leverages generative AI to orchestrate structured affective reasoning through independent emotional agents, introducing a novel paradigm for information fusion via generative emotional modelling."', '"A emergency-oriented variant of the system, named Armando, ... delivering emotionally calibrated and factually accurate information through the integration of Retrieval-Augmented Generation (RAG) and cumulative context tracking."', '"Through empirical testing, we observed that abliterated models consistently produced more genuine and emotionally resonant outputs, better aligned with the behavioural profiles expected from each emotional agent."', '"The final output is clearly segmented into REASONING (analytical assessment), THOUGHTS (representing Riley’s internal cognitive processes), and FINAL ANSWER (a balanced and consumable synthesis for the user)."', '"As illustrated in Figure 5, RAG enrichment is applied immediately before the final synthesis stage..."', '"Visualisation support, assessed through the question Did the visualisation of the process leading to the final response help you reflect on your question?, received the lowest overall scores, ranging from 3.76 to 4.24, indicating limited perceived benefit."']

## Notas Adicionales
Preprint en arXiv bajo revisión para Information Fusion. Implementación local con Ollama y modelos compactos (3B–8B) para viabilidad en GPU de 8 GB. La arquitectura combina debate emocional multi-ronda, votación con justificación y síntesis explicable, integrando datos textuales y visuales. La elección de modelos “abliterated” busca mayor expresividad emocional, pero requiere atención a riesgos de seguridad. En Armando, el enriquecimiento RAG justo antes de la síntesis final evita la dilución de hechos durante el debate emocional y mejora la precisión en emergencias. Se proporciona trazabilidad completa (logs de conversaciones y parámetros) para transparencia y auditoría. Financiación: FCT UIDB/04524/2020. Declaración de uso de ChatGPT para mejorar legibilidad.
