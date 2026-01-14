# Large Language Models Can Infer Personality from Free-Form User Interactions

## Metadata
- **Autores**: Heinrich Peters, Moran Cerf, Sandra C. Matz
- **Año**: 2024
- **Keywords**: LLM, GPT-4, Chatbot, Personality, Big-Five, Assessment

## Abstract
El estudio evalúa la capacidad de modelos de lenguaje grandes (LLMs), específicamente GPT-4, para inferir los rasgos de personalidad Big Five a partir de conversaciones libres con usuarios. En un diseño 3×2 que varió tanto el comportamiento del chatbot (evaluación explícita de personalidad, conversación de conocimiento mutuo, asistente útil) como las instrucciones al usuario (conversación natural vs. uso no restringido), GPT-4 alcanzó correlaciones moderadas con la personalidad auto-reportada (BFI-2). El rendimiento fue mayor cuando el chatbot fue instruido para obtener información relevante de personalidad, sin detrimento de la experiencia de usuario, y menor cuando actuó como asistente genérico, aunque aún capturó señales psicológicas. Análisis preliminares sugieren diferencias mínimas en exactitud a través de subgrupos sociodemográficos. Los hallazgos evidencian el potencial de los LLMs para el perfilado psicológico conversacional y plantean implicaciones éticas y de privacidad.

## Contribuciones Principales
- Demuestra que GPT-4 puede inferir los rasgos Big Five a partir de conversaciones libres con exactitud moderada, superando enfoques previos basados en texto estático.
- Muestra que el prompting centrado en evaluación de personalidad aumenta notablemente la exactitud de inferencia, mientras que el estilo "asistente útil" es inferior pero aún informativo.
- Evidencia que focalizarse en evaluar personalidad no reduce la calidad de la experiencia de usuario (naturalidad, agrado, involucramiento, human-likeness).
- Presenta análisis preliminares de sesgos que muestran variación marginal en exactitud y sesgos de nivel entre subgrupos (género, edad, raza, educación, ingreso).
- Proporciona un protocolo reproducible: interfaz web, 15 turnos, GPT-4-0613, scoring triplicado, BFI-2, y métricas de experiencia de usuario.

## Metodología
Diseño: factorial 3×2 entre sujetos.
- Condiciones del bot (prompts):
  1) Assessment: conversación natural orientada a inferir Big Five sin explicitar evaluación.
  2) Acquaintance: conversación para conocer al usuario y su carácter.
  3) Assistant: comportamiento de asistente útil (estilo ChatGPT por defecto).
- Condiciones del usuario (instrucciones):
  1) Conversation: conversar de forma natural como con alguien recién conocido.
  2) Unconstrained Use: usar el chatbot como normalmente (preguntas, tareas, conversación).
Muestra y procedimiento:
- 600 reclutados en Prolific (EE. UU.; feb/2024); muestra final N=566 (50.2% mujeres; 62.7% blancos; 55.7% con grado universitario; edad media 37.67, SD=13.01). Consentimiento informado; aprobación IRB Columbia (#AAAV0800).
- Interacción: 15 turnos por participante en una app web (Google AppEngine; Firestore). Modelo: GPT-4 (gpt-4-0613). Los participantes sabían que era un agente de IA, sin revelar propósito del estudio.
Medidas:
- Personalidad auto-reportada: BFI-2 (60 ítems, Likert 1–5).
- Experiencia de usuario (6 ítems Likert 1–7): naturalidad, agrado, involucramiento, calidad de preguntas, calidad de respuestas, human-likeness; α=0.898.
Inferencia de personalidad por LLM:
- Cada conversación se transcribió (marcas "GPT:" y "User:") y se reinyectó a GPT-4 para calificar Big Five (1–5) en 3 llamadas independientes; se promedió por conversación.
Análisis:
- Exactitud: correlaciones de Pearson entre puntajes inferidos y BFI-2 por condición; pruebas unilaterales para r>0; IC 95% (dos colas) e IC inferiores 95% (una cola).
- Experiencia de usuario: comparación de medias por condición (Figura 2; SI D).
- Sesgos demográficos: residuos (inferencia – auto-reporte; sesgo de nivel) y correlaciones dentro de subgrupos; dicotomización: edad (mediana=36), raza (blanco vs no blanco), educación (college vs no), ingreso (<$50k vs ≥$50k), género; pooling de condiciones (Figura 3; SI E–F).

## Resultados Clave
- Exactitud de inferencia por condición del bot:
  • Assessment: mayor desempeño. Conversation: r en [0.326, 0.590], media≈0.438; Unconstrained: r en [0.245, 0.640], media≈0.448; todos r>0 significativos.
  • Acquaintance: intermedio. Conversation: r en [0.166, 0.373], media≈0.248; Unconstrained: r en [0.066, 0.317], media≈0.188; la mayoría significativos.
  • Assistant: menor. Conversation: r en [-0.004, 0.209], media≈0.126; Unconstrained: r en [0.018, 0.193], media≈0.109; varios significativos, aún con señales psicológicas.
- Instrucciones al usuario: no hubo diferencias sistemáticas en exactitud entre Conversation y Unconstrained dentro de cada condición del bot.
- Experiencia de usuario: Acquaintance fue valorada como más natural, agradable y atractiva; Assistant fue la peor (especialmente en naturalidad y human-likeness), aunque destacó en calidad de respuestas. No hubo diferencias consistentes entre Assessment y Acquaintance, sugiriendo que focalizarse en personalidad no reduce la experiencia.
- Sesgos demográficos: el modelo tendió a subestimar los rasgos (residuos negativos) de forma generalizada. Diferencias por subgrupo fueron pequeñas y esporádicas (p.ej., género en Neuroticismo; edad en Conscientiousness). Dos diferencias en exactitud por ingreso (Conscientiousness y Agreeableness). En conjunto, indican variación marginal en sesgos y exactitud entre subgrupos.
- Detalles ilustrativos (SI C): ejemplos de r por rasgo/condición incluyen: Assessment–Conversation Extraversion r=0.590 [0.441, 0.707]; Assessment–Unconstrained Neuroticism r=0.640 [0.507, 0.743]; Assistant–Conversation Conscientiousness r=-0.004 [-0.210, 0.202].

## Limitaciones
- Escenario zero-shot con prompts simples; no se usaron estrategias avanzadas (p.ej., chain-of-thought) ni fine-tuning, por lo que los resultados son un límite inferior.
- Interacciones relativamente cortas (15 turnos); es probable que interacciones más largas o repetidas mejoren la inferencia.
- Entorno experimental puede no capturar la riqueza de usos motivados intrínsecamente (especialmente en modo asistente).
- Solo se evaluó GPT-4 (gpt-4-0613); la generalización a otros LLMs, si bien plausible, no está validada empíricamente aquí.
- Análisis de subgrupos requiere dicotomización y pooling; tamaños de muestra por subgrupo limitan inferencias firmes.
- Muestra de EE. UU. reclutada en línea (Prolific); la generalización cultural/lingüística puede estar acotada.
- Sesgo sistemático de subestimación de rasgos (residuos negativos) no totalmente explicado.

## Trabajo Futuro
- Explorar prompting avanzado (p.ej., chain-of-thought, auto-rúbricas, entrevistas adaptativas) y fine-tuning específico para evaluación psicométrica.
- Aumentar longitud y/o número de sesiones, e incorporar memoria conversacional para mejorar validez y estabilidad.
- Evaluar interacciones ecológicas con datos no experimentales (uso real) para el modo asistente.
- Comparar y replicar con otros LLMs y arquitecturas; estudiar calibración y estabilidad entre versiones de modelo.
- Ampliar análisis de equidad con muestras más grandes y medidas continuas (sin dicotomización), y diversidad cultural/lingüística.
- Investigar mecanismos de subestimación y calibración de puntajes; integrar correcciones basadas en metadatos conversacionales.
- Desarrollar y evaluar lineamientos de transparencia, consentimiento informado dinámico y disclosure de inferencias en aplicaciones reales.

## Citas Relevantes
- "Performance was highest when the chatbot was prompted to elicit personality-relevant information from users (mean r=.443, range=[.245, .640]), followed by a condition placing greater emphasis on naturalistic interaction (mean r=.218, range=[.066, .373])."
- "A chatbot mimicking ChatGPT’s default behavior of acting as a helpful assistant led to markedly inferior personality inferences and lower user experience ratings but still captured psychologically meaningful information for some of the personality traits (mean r=.117, range=[-.004, .209])."
- "Notably, the direct focus on personality assessment did not result in a less positive user experience, with participants reporting the interactions to be equally natural, pleasant, engaging, and humanlike across both conditions."
- "The overall pattern of results suggests that LLMs possess accurate representations of personality constructs and are able to elicit personality-relevant information by asking pointed questions."
- "Our results highlight the potential of LLMs for psychological profiling based on conversational interactions."
- "We recommend clear regulations regarding the identification of artificial agents when they interact with humans and a transparent disclosure of the inferences made by the AI as a result of these interactions."

## Notas Adicionales
Repositorio OSF con datos y materiales: https://osf.io/edn3g/. Ética: aprobado por IRB Columbia (#AAAV0800). Implementación: app web en Google AppEngine; base de datos Firestore; GPT-4 gpt-4-0613. Inferencia: 3 evaluaciones por conversación promediadas. BFI-2 como gold standard (60 ítems). Experiencia de usuario con alta consistencia interna (α=0.898). Hallazgo clave aplicado: el prompting orientado a personalidad mejora fuertemente la exactitud sin costo en UX; el modo asistente estándar es subóptimo para inferencia, aunque informativo. Se observó un sesgo de nivel de subestimación de rasgos en general. Implicaciones: potencial para evaluación a escala y personalización, pero con riesgos en privacidad y persuasión personalizada; se recomiendan políticas de transparencia y regulación.
