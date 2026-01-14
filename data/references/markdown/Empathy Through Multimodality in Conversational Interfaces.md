# Empathy Through Multimodality in Conversational Interfaces

## Metadata
- **Autores**: Mahyar Abbasian, Iman Azimi, Mohammad Feli, Amir M. Rahmani, Ramesh Jain
- **Año**: 2024
- **Keywords**: Conversational Health Agents, LLM, empatía, multimodal, reconocimiento de emociones en voz, wav2vec2, Whisper, gTTS, Tree of Thought, orquestador, salud mental, openCHA, búsqueda en la web

## Abstract
El trabajo presenta un Agente de Salud Conversacional (CHA) impulsado por un LLM y diseñado para diálogos multimodales en apoyo a la salud mental. El sistema integra reconocimiento de emociones en voz para inferir el estado afectivo del usuario y adaptar respuestas verbales empáticas y contextualizadas. Basado en el marco openCHA, combina módulos de speech-to-text, detección de emoción en voz, búsqueda en Internet y text-to-speech. La evaluación incluye: (1) consistencia y repetibilidad del planeamiento del agente, y (2) valoración humana de la empatía de las respuestas ante consultas neutrales expresadas con tonos emocionales de tristeza, ira y alegría. Los resultados muestran alta concordancia entre las respuestas del CHA y las evaluaciones humanas, subrayando el papel clave del reconocimiento emocional vocal para fortalecer la conexión empática.

## Contribuciones Principales
- Propone un CHA multimodal basado en LLM que integra reconocimiento de emociones en voz para ajustar el contenido y tono de las respuestas.
- Implementa una arquitectura orquestada (openCHA) con módulos de STT (Whisper), SER (wav2vec2 afinado en IEMOCAP), TTS (gTTS) y búsqueda web (SerpAPI + Playwright).
- Introduce un planificador con Tree of Thought sobre GPT-3.5-turbo para descomponer consultas en tareas, evaluar estrategias y ejecutar herramientas externas.
- Evalúa consistencia/repetibilidad del planificador en 500 corridas y realiza evaluación humana de empatía en 5 preguntas neutrales expresadas con tres emociones (tristeza, ira, alegría).
- Evidencia que incorporar señales vocales emocionales mejora la alineación empática de las respuestas, especialmente en casos de tristeza.

## Metodología
Arquitectura de CHA con cinco componentes: (1) Interfaz web para grabación/reproducción de voz; (2) Conversación Multimodal: STT con Whisper-base (OpenAI) y TTS con gTTS; (3) Orquestador: núcleo de decisión que planifica, ejecuta tareas, maneja memoria de corto plazo y genera respuestas. El planificador emplea Tree of Thought con GPT-3.5-turbo para proponer estrategias, analizar pros/cons y seleccionar la óptima; la ejecución coordina detección de emoción en voz y búsquedas web; la memoria almacena datos intermedios multimodales; el generador de respuestas (GPT-3.5-turbo) produce mensajes empáticos personalizados; (4) Detección Multimodal de Emociones: implementación actual centrada en voz, usando wav2vec2 (SpeechBrain) afinado en IEMOCAP para clasificar emociones; (5) Fuentes Fiables de Salud Mental: búsqueda y extracción de información en sitios confiables mediante SerpAPI (Google Search API) y Playwright. Evaluación: (a) Consistencia del planificador: 500 iteraciones con una pregunta aleatoria (de 5) expresada con una de 3 emociones (alegre, triste, enojado). Métrica 1: aciertos al identificar emoción y recuperar información pertinente; Métrica 2: uso correcto de la emoción para guiar la búsqueda web. (b) Empatía y alineación: 5 preguntas neutrales (tabla I) presentadas en tres tonos emocionales; 3 evaluadores externos puntuaron de 0 a 10 la alineación con la emoción y la empatía; se promediaron puntuaciones por par pregunta-emoción.

## Resultados Clave
- Planificador: 89% de acierto al identificar la emoción desde la voz y recuperar información relevante a la consulta del usuario (Métrica 1).
- Planificador: 61% de acierto al usar explícitamente la emoción para accionar búsquedas web dirigidas (Métrica 2).
- Evaluación humana (promedios globales por emoción): Alegría 6.24, Tristeza 7.24, Ira 6.56 (umbral de adecuación ≥6 según evaluadores).
- Respuestas a consultas en tono triste fueron percibidas como más empáticas y mejor alineadas que en alegría o ira.
- Demostraciones (Fig. 2): para emoción "Sad" el agente prioriza recursos de apoyo (p. ej., SAMHSA) y tono de contención; para "Happy" utiliza un tono motivacional y sugerencias prácticas (p. ej., recursos NHS).

## Limitaciones
- Modalidad limitada: solo se implementa reconocimiento de emoción en voz; no incluye aún video (rostro/gestos) ni biomarcadores fisiológicos.
- Evaluación a pequeña escala: 5 preguntas, 3 evaluadores; no hay análisis clínico ni ensayos controlados.
- Dependencia de GPT-3.5-turbo y herramientas externas; posible variabilidad y sesgos.
- El 61% en búsqueda guiada por emoción indica margen de mejora en el uso sistemático de señales afectivas durante la planificación.
- El modelo SER se afinó en IEMOCAP (datos actuados), lo que puede limitar la generalización a escenarios naturales.
- Ausencia de memoria a largo plazo y control fino de prosodia en TTS para expresar empatía.

## Trabajo Futuro
- Integrar modalidades adicionales: análisis facial, gestual y biomarcadores (p. ej., VFC) para una empatía computacional más holística.
- Mejorar el planificador para usar de forma más consistente la emoción en búsquedas y razonamiento (p. ej., mejores prompts, modelos LLM más capaces).
- Evaluaciones más amplias y rigurosas con usuarios reales y métricas estandarizadas; potencialmente ensayos controlados.
- Control de prosodia y estilo en TTS para matizar expresividad empática; soporte multilingüe.
- Mecanismos de seguridad, derivación y personalización sostenida (memoria de largo plazo).

## Citas Relevantes
- "This paper introduces an LLM-based CHA engineered for rich, multimodal dialogue—especially in the realm of mental health support."
- "findings revealing a striking concordance between the CHA’s outputs and evaluators’ assessments."
- "We obtained %89 accuracy to identify the emotional state from the voice and retrieve related information pertinent to the user’s query. It also obtained %61 accuracy to correctly call the Internet searches tool based on the emotion states."
- "We posit that CHAs have the capability to transcend LLM limitations in conveying empathy by integrating a rich array of multimodal data channels."

## Notas Adicionales
El sistema se construye sobre openCHA (código referido), usa Whisper-base para STT y gTTS para TTS, y wav2vec2 (SpeechBrain) afinado en IEMOCAP para SER. La búsqueda en fuentes fiables se implementa con SerpAPI y Playwright para extraer contexto. El planificador aplica Tree of Thought con GPT-3.5-turbo y un generador de respuestas también con GPT-3.5-turbo. Los ejemplos muestran recomendaciones a recursos como SAMHSA y NHS. Los evaluadores consideraron puntuaciones ≥6 como alineación razonable; la tristeza mostró la mayor empatía percibida. El trabajo posiciona el reconocimiento emocional vocal como pieza clave para fortalecer la conexión empática en CHAs.
