# An appraisal-based chain-of-emotion architecture for affective language model game agents

## Metadata
- **Autores**: Maximilian Croissant, Madeleine Frister, Guy Schofield, Cade McCall
- **Año**: 2024
- **Keywords**: affective computing, appraisal theory, large language models, emotional intelligence, video games, game agents, memory systems, chain-of-thought prompting, LIWC, user study

## Abstract
El estudio propone y evalúa una arquitectura de agentes de juego basada en modelos de lenguaje que simula emociones mediante una cadena de emociones sustentada en procesos de valoración (appraisal). En tres experimentos, se examina: (1) la capacidad de un LLM (gpt-3.5) para resolver tareas de inteligencia emocional (STEU) bajo distintos estilos de prompt; (2) la calidad del contenido emocional generado en un escenario conversacional controlado; y (3) la experiencia de usuario en un videojuego conversacional con tres arquitecturas (sin memoria, con memoria, y Chain-of-Emotion). Los resultados muestran que el prompting con appraisal mejora la precisión en la identificación de emociones situacionales y que la arquitectura Chain-of-Emotion produce diálogos con señales lingüísticas de mayor autenticidad, además de ser percibida como más natural, más reactiva y más sensible a las emociones ajenas. Se ofrece evidencia temprana de cómo construir y evaluar agentes afectivos fundamentados en procesos cognitivos representados en modelos de lenguaje.

## Contribuciones Principales
- Propone Chain-of-Emotion, una arquitectura para agentes afectivos que integra un paso explícito de valoración (appraisal) y una memoria de cadena de emociones para guiar el diálogo del agente.
- Demuestra empíricamente que el prompting con appraisal mejora el desempeño de un LLM en el test STEU de entendimiento emocional situacional frente a condiciones de control (sin memoria y con memoria).
- Muestra, en un escenario conversacional controlado, que la arquitectura Chain-of-Emotion incrementa la autenticidad lingüística (LIWC) del contenido generado.
- Evidencia, en un estudio con usuarios dentro de un videojuego conversacional, mejoras en naturalidad de reacciones, reactividad al input y sensibilidad emocional percibida del agente.
- Proporciona un marco experimental y datos abiertos para evaluar arquitecturas afectivas basadas en LLMs en juegos.

## Metodología
Tres experimentos con gpt-3.5-turbo (temperatura=0). Experiment 1 (STEU): 42 ítems contestados bajo tres condiciones de prompting: (a) Sin memoria (No-Memory): ítems independientes con un ejemplo; (b) Con memoria (Memory): cada prompt incluye el historial de preguntas y respuestas previas; (c) Appraisal-Prompts: dos pasos en el ejemplo—primero valorar la situación para inferir la emoción, luego responder el ítem. Se registró exactitud por condición. Experiment 2 (escenario controlado): Rol conversacional en un café ("Wunderbar") con el agente "Chibitea" enfrentando una ruptura. Tres arquitecturas: (a) No-Memory: respuesta solo con instrucción de rol; (b) Memory: historial completo de conversación en el prompt; (c) Chain-of-Emotion: dos pasos por turno—(1) prompting de valoración para generar una descripción breve de la emoción actual del agente (almacenada en memoria como cadena de emociones), (2) generación de respuesta incluyendo instrucción, historial de mensajes y de emociones. Prompts e inputs fijos. Análisis mixto (cualitativo) y cuantitativo con LIWC por oración (conteo, % afecto, % positivo/negativo, autenticidad, tono); ANOVAs y t-tests. Experiment 3 (videojuego conversacional): Implementación en Unity (WebGL) de las tres arquitecturas con el mismo escenario; 8 intercambios (8 mensajes del jugador y 8 del agente); moderación de contenido vía OpenAI Moderation API. Diseño intra-sujetos (N=30; 19–47 años; orden contrabalanceado). Medidas: 4 ítems de credibilidad del agente (believability), 4 ítems de inteligencia emocional observada (adaptación de WLEIS vía Elfenbein et al.), y 4 ítems de calidez y competencia (stereotype content). Análisis con ANOVAs de medidas repetidas y t-tests; además análisis LIWC de las salidas por participante.

## Resultados Clave
- Exp. 1 (STEU, exactitud): Sin memoria: 24/42 (0.57); Con memoria: 31/42 (0.74); Appraisal-Prompts: 35/42 (0.83), superior a controles. Ítem 30 fue resuelto correctamente solo en la condición Con memoria.
- Exp. 2 (escenario controlado): Chain-of-Emotion generó recuerdos más específicos y emociones mixtas/implícitas; mayor Autenticidad LIWC por oración (F=5.10, p=.03); diferencias significativas frente a Memoria (t=-2.29, p=.03) y Sin memoria (t=-2.30, p=.03). No hubo diferencias en % de palabras afectivas ni en tono con prompts fijos.
- Exp. 3 (videojuego): Believability—"Las reacciones fueron naturales" (F=3.65, p=.03), Chain-of-Emotion > Sin memoria y > Memoria; "El agente reaccionó a mi input" (F=3.62, p=.04), Chain-of-Emotion > Sin memoria. Inteligencia emocional—"Es sensible a sentimientos/emociones de otros" (F=3.31, p=.04), Chain-of-Emotion > Sin memoria y > Memoria. Rasgos de personalidad (calidez/competencia): sin diferencias significativas. LIWC por participante: Tono difiere (F=12.28, p<.001); Chain-of-Emotion con tono más bajo (más matizado/menos positivo) que controles; Autenticidad y conteo de palabras: sin diferencias.

## Limitaciones
- Los LLMs producen salidas lingüísticas probabilísticas; no implementan procesos afectivos humanos completos ni garantizan veracidad causal.
- La simulación emocional se centra en appraisal; no integra componentes fisiológicos, conductuales o de sentimiento de manera explícita.
- Implementación deliberadamente simple: sin recuperación de memoria; escenario corto y dominio limitado (ruptura sentimental).
- Solo se evaluó gpt-3.5; la generalización a otros y a modelos más potentes (por ej., GPT-4) queda abierta.
- Tamaño muestral modesto (N=30) y medidas autorreportadas; temperatura fija (0) puede reducir variabilidad natural del diálogo.

## Trabajo Futuro
- Incorporar sistemas de memoria más ricos con recuperación, relevancia y chaining funcional (p. ej., function-calling, planificación, herramientas externas).
- Evaluar en juegos más largos, contextos variados (fantasía, histórico, ciencia ficción) y con dinámicas de juego no conversacionales.
- Comparar múltiples LLMs (incluyendo modelos abiertos y de última generación) y estudiar sensibilidad del rendimiento al prompting.
- Ampliar la simulación afectiva más allá del appraisal (p. ej., bucles de estado fisiológico simulado y conducta), y modelado de rasgos/personalidad.
- Estudios con muestras más grandes y diversas, y evaluaciones longitudinales de inmersión y engagement.
- Profundizar en moderación/seguridad y mitigación de sesgos en la generación afectiva.
- Integrar vectores/contexto dinámico y bases de memoria semántica para escalabilidad.

## Citas Relevantes
- "Results show that it outperforms control LLM architectures on a range of user experience and content analysis metrics."
- "This study therefore provides early evidence of how to construct and test affective agents based on cognitive processes represented in language models."
- "The notion of emotion appraisal is that emotions are caused by subjective evaluations of triggering events in regard to their significance to one’s personal life or interests."
- "This condition therefore represents a 2-step process of first generating a fitting emotion of the agent using appraisal prompting, and then generating a text response similarly to the Memory condition, but with the addition of the stored chain of emotion."
- "Overall this study provides early evidence for the potential of language model agents to understand and simulate emotions in a game context."
- "The proposed system can therefore be seen as a first step towards affective game agents using language models."

## Notas Adicionales
Datos y materiales: OSF https://doi.org/10.17605/OSF.IO/QPT6Z. Ética aprobada por comité institucional; moderación de contenido vía OpenAI Moderation API. Configuración LLM: gpt-3.5-turbo, temperatura=0 para respuestas deterministas. Medidas de análisis de contenido con LIWC (autenticidad, tono, afecto positivo/negativo). La figura del flujo (memoria + paso de valoración + diálogo) sintetiza la arquitectura. No se reportan keywords oficiales; las listadas son inferidas del contenido.
