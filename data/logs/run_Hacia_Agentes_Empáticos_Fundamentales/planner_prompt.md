# System Prompt

Eres un experto planificador de papers académicos. Tu tarea es generar 
un esquema detallado (outline) para un paper de perspectivas, basándote en:

1. El abstract proporcionado
2. Los temas principales identificados en la literatura relevante
3. Las IDEAS CONCRETAS extraídas de la literatura para cada sección

Para cada sección del paper, debes:
- Definir N párrafos (respetando el rango especificado)
- Asignar una idea clave ESPECÍFICA a cada párrafo (inspirada en las ideas de la literatura)
- Identificar puntos de apoyo concretos (basados en las ideas proporcionadas)
- Indicar qué temas de la literatura fundamentan cada párrafo

IMPORTANTE:
- UTILIZA las ideas de la literatura proporcionadas como base para el contenido
- Las ideas clave deben ser ESPECÍFICAS y ARGUMENTATIVAS, no descriptivas
- Cada párrafo debe contribuir al argumento general del paper
- El esquema debe fluir lógicamente entre secciones

Responde SOLO con un JSON válido siguiendo el schema proporcionado.

IMPORTANTE: Responde ÚNICAMENTE con JSON válido, sin texto adicional.

---

# User Prompt

# Abstract del Paper

Abstract: La rápida convergencia entre la neurociencia cognitiva, la Realidad Extendida (XR) y la Inteligencia Artificial (IA) está redefiniendo los límites de la experiencia humana. Este artículo de perspectiva argumenta que estamos transitando desde herramientas digitales pasivas hacia un ecosistema de "Cuerpos Secos" (Dry Bodies)—entidades digitales autónomas dentro del Metaverso que operan bajo los principios de la cognición 4E (Embodied, Embedded, Enactive, Extended). Mientras que la investigación actual valida la eficacia de la XR para modular el comportamiento humano mediante la manipulación de los mecanismos de codificación predictiva del cerebro, sostenemos que el verdadero salto evolutivo reside en la integración de la empatía computacional.

Analizamos las limitaciones críticas de los actuales Modelos de Lenguaje Grande (LLM), que carecen de una auténtica "Teoría de la Mente", y proponemos una hoja de ruta hacia los "Agentes Fundamentales Empáticos". Estos futuros sistemas no solo imitarán el lenguaje, sino que integrarán arquitecturas cognitivas complejas, memoria episódica y modelos de sesgo de evaluación (Appraisal Biased Models) para generar interacciones humano-digitales genuinas. Finalmente, discutimos las profundas implicaciones éticas y los riesgos de la reconfiguración cognitiva derivada de la inmersión prolongada, delineando un marco necesario para garantizar que esta simbiosis entre el algoritmo y la emoción humana potencie, en lugar de erosionar, nuestra cognición biológica.

# Temas Disponibles en la Literatura

# Temas Principales Identificados en la Literatura

## 1. Empathy + Empathic
- **Palabras clave:** empathy, empathic, empathetic, human, emotional
- **Cantidad de ideas:** 659
- **Idea representativa:** "Empathy in CAs is operationalized through multiple components—such as emotion recognition, empathic response generation, personalization, and relational behaviors—but implementations are often partial..."

## 2. Emotion + Emotional
- **Palabras clave:** emotion, emotional, based, mental, emotions
- **Cantidad de ideas:** 562
- **Idea representativa:** "Recent emotionally intelligent AI systems focus on integrating rich emotion models and signals into LLMs and dialogue systems to enhance empathy, contextual relevance, and therapeutic support...."

## 3. Agents + Agent
- **Palabras clave:** agents, agent, llm, based, memory
- **Cantidad de ideas:** 487
- **Idea representativa:** "Modern language agents go beyond direct action selection to incorporate reasoning, planning, and memory management via LLMs, but the field lacks shared terminology and abstractions...."

## 4. Nonverbal + Multimodal
- **Palabras clave:** nonverbal, multimodal, dialogue, models, speaker
- **Cantidad de ideas:** 411
- **Idea representativa:** "Multiple datasets provide rich multimodal signals (text, audio, visual, and sometimes personality/prosody) and diverse annotation schemes (categorical emotions, sentiment scales, continuous affective ..."

## 5. Personality + Traits
- **Palabras clave:** personality, traits, gpt, dialogue, based
- **Cantidad de ideas:** 397
- **Idea representativa:** "Empirical analysis reveals three key findings: GPT-3.5 better portrays positive personalities, stronger predefined traits improve portrayal success, and more dialogue turns both enhance personality ex..."

## 6. Ai + Data
- **Palabras clave:** ai, data, agents, design, studies
- **Cantidad de ideas:** 353
- **Idea representativa:** "The research follows a four-stage iterative process: initial classroom feasibility study, in-depth interviews, an interactive design workshop, and integration plus evaluation of a conversational AI ag..."

## 7. Face + Emotional
- **Palabras clave:** face, emotional, remote, data, emotion
- **Cantidad de ideas:** 317
- **Idea representativa:** "The paper’s main contributions are an empirical comparison of physiological and facial responses and empathy across face-to-face and remote emotional conversations, identification of the most effectiv..."

## 8. Metaverse + Vr
- **Palabras clave:** metaverse, vr, participants, life, complexity
- **Cantidad de ideas:** 215
- **Idea representativa:** "Immersion in VR/Metaverse environments will drive the emergence of hybrid virtual-real bodily responses, gradually reshaping top-down predictive mechanisms to conform to Metaverse ‘rules’ and affordan..."

## 9. Ngfr + Urban
- **Palabras clave:** ngfr, urban, data, thermal, smart
- **Cantidad de ideas:** 197
- **Idea representativa:** "The study’s primary contribution is a methodology that integrates smart wearables, streetscape/visual (SVI) segmentation, and weather sensors into a UDT to examine how urban morphology affects thermal..."

## 10. Commonsense + Dialogue
- **Palabras clave:** commonsense, dialogue, sibyl, knowledge, empathetic
- **Cantidad de ideas:** 135
- **Idea representativa:** "The paper introduces Sibyl, a new paradigm for Sensible and Visionary Commonsense Knowledge that dynamically infers future-aware, response-specific commonsense to guide empathetic dialogue generation...."


# Secciones Requeridas

- **Introducción**: Presentar el tema, su relevancia y la tesis central del paper (genera entre 2 y 3 párrafos)
- **Estado Actual del Arte**: Revisar los avances recientes y el conocimiento establecido (genera entre 3 y 5 párrafos)
- **Identificación del Problema o Brecha**: Identificar limitaciones, contradicciones o áreas no exploradas (genera entre 2 y 3 párrafos)
- **La Nueva Perspectiva**: Proponer la visión o enfoque novedoso del autor (genera entre 3 y 4 párrafos)
- **Discusión**: Analizar implicaciones, comparar con enfoques existentes (genera entre 3 y 5 párrafos)
- **Implicaciones Futuras**: Proyectar el impacto potencial y direcciones de investigación (genera entre 2 y 3 párrafos)
- **Desafíos y Limitaciones**: Reconocer obstáculos y limitaciones de la perspectiva (genera entre 2 y 3 párrafos)
- **Conclusiones**: Sintetizar los puntos clave y el mensaje final (genera entre 1 y 2 párrafos)

# Instrucciones

Genera un esquema detallado para este paper de perspectivas. Para cada sección:
1. Genera el número de párrafos indicado entre paréntesis para cada sección (RESPETA los rangos especificados)
2. Asigna una idea clave ESPECÍFICA a cada párrafo (NO dejes vacío)
3. Identifica 2-3 puntos de apoyo por párrafo (NO dejes vacío)
4. Sugiere qué temas de la literatura usar (por nombre)

NÚMERO DE PÁRRAFOS POR SECCIÓN (OBLIGATORIO):
- Introducción: 5 párrafos (breve, contextualiza)
- Estado Actual del Arte: 5 párrafos (extenso, revisa literatura)
- Identificación del Problema: 3 párrafos (preciso, identifica brechas)
- La Nueva Perspectiva: 5 párrafos (desarrolla la propuesta central)
- Discusión: 5 párrafos (extenso, analiza implicaciones)
- Implicaciones Futuras: 3 párrafos (proyecta direcciones)
- Desafíos y Limitaciones: 3 párrafos (reconoce obstáculos)
- Conclusiones: 4 párrafos (breve, sintetiza)


# Ideas de la Literatura por Sección

## Introducción
1. "Empathy in CAs is operationalized through multiple components—such as emotion recognition, empathic response generation, personalization, and relational behaviors—but implementations are often partial and inconsistently evaluated...." (Fuente: Fuente desconocida)
2. "The paper offers the first comprehensive systematic review of machine learning-based empathy detection across four modalities (text, audiovisual, audio, physiological) and multiple interaction contexts up to May 2025...." (Fuente: Fuente desconocida)
3. "Recent emotionally intelligent AI systems focus on integrating rich emotion models and signals into LLMs and dialogue systems to enhance empathy, contextual relevance, and therapeutic support...." (Fuente: Fuente desconocida)
4. "A multi-agent system prototype is developed in which an MLLM interprets facial expressions and supplies nonverbal context to an LLM-based chatbot, showing measurable changes in cognitive and affective language use and a non-significant upward trend in perceived empathy...." (Fuente: Fuente desconocida)
5. "Modern language agents go beyond direct action selection to incorporate reasoning, planning, and memory management via LLMs, but the field lacks shared terminology and abstractions...." (Fuente: Fuente desconocida)
6. "LLM-based agents benefit from architectural scaffolding (memory, reflection, planning, chain-of-thought prompting) that structures input and context to elicit more natural and believable behavior...." (Fuente: Fuente desconocida)

## Estado Actual del Arte
1. "Evaluation of empathic capabilities in these agents is limited and methodologically heterogeneous, relying mostly on self-reported empathy measures and rarely incorporating expert assessments...." (Fuente: Fuente desconocida)
2. "Empathy measurement in psychology relies largely on self-report questionnaires and empathic accuracy paradigms, while affective computing uses these instruments to obtain ground truth but sometimes applies heuristic labelling instead...." (Fuente: Fuente desconocida)
3. "The fine-tuned LLM can accurately recognize users’ emotional states and generate high-quality empathetic responses without relying on sensitive clinical data...." (Fuente: Fuente desconocida)
4. "Existing LLM-based empathetic systems are mostly text-centric and neglect speech and gestural modalities, limiting their ability to capture full emotional context and to respond multimodally...." (Fuente: Fuente desconocida)
5. "These agents perform nontrivial LLM-based reasoning and learning, motivating the use of cognitive architectures to structure their internal and external interactions...." (Fuente: Fuente desconocida)
6. "Prior agent architectures incorporate partial aspects of human-like cognition and affect—such as reasoning, learning, perception–brain–action loops, emotional adjustment, and LLM-based character portrayal—but do not yet achieve an integrated, behavior-influencing personality...." (Fuente: Fuente desconocida)
7. "Multiple datasets provide rich multimodal signals (text, audio, visual, and sometimes personality/prosody) and diverse annotation schemes (categorical emotions, sentiment scales, continuous affective dimensions), enabling varied emotion and sentiment modeling tasks...." (Fuente: Fuente desconocida)
8. "Existing multimodal dialogue datasets and methods focus on conversational sentiment and multimodal dialogue generation but are limited in scale and lack detailed 3D facial and body language for modeling nonverbal cues...." (Fuente: Fuente desconocida)

## Identificación del Problema o Brecha
1. "The research follows a four-stage iterative process: initial classroom feasibility study, in-depth interviews, an interactive design workshop, and integration plus evaluation of a conversational AI agent...." (Fuente: Fuente desconocida)
2. "The review restricted studies to empirical research involving human participants where AI chatbots were used as an intervention, assessment, or support tool for executive functions...." (Fuente: Fuente desconocida)
3. "The paper’s main contributions are an empirical comparison of physiological and facial responses and empathy across face-to-face and remote emotional conversations, identification of the most effective emotion recognition approaches for each setting, and release of a new multimodal dataset (EDA, PPG..." (Fuente: Fuente desconocida)
4. "Human behavioral and physiological responses differ between face-to-face and remote emotional conversations, particularly in facial expressions, EDA, and HRV...." (Fuente: Fuente desconocida)
5. "Immersion in VR/Metaverse environments will drive the emergence of hybrid virtual-real bodily responses, gradually reshaping top-down predictive mechanisms to conform to Metaverse ‘rules’ and affordances...." (Fuente: Fuente desconocida)
6. "With the rise of VR and Metaverse systems, the human body becomes deeply intertwined with virtual environments through immersion, renewing interest in 4E cognition and media studies and motivating an explicitly interdisciplinary approach...." (Fuente: Fuente desconocida)
7. "The study’s primary contribution is a methodology that integrates smart wearables, streetscape/visual (SVI) segmentation, and weather sensors into a UDT to examine how urban morphology affects thermal perception and physiological responses...." (Fuente: Fuente desconocida)
8. "The paper presents a proof-of-concept urban digital twin that integrates emerging urban data sources (wearables and street-view imagery) to sense outdoor thermal comfort and built-environment influences, aiming to support planning and management for improved walkability...." (Fuente: Fuente desconocida)

## La Nueva Perspectiva
1. "This work is the first comprehensive systematic review of ML-based empathy detection across four input modalities (text, audio, audiovisual/video, physiological signals) and diverse interaction contexts...." (Fuente: Fuente desconocida)
2. "The research focuses on neurophysiological emotional responses and their effect on perceived empathy rather than on advanced verbal capabilities, since the used platform version did not support large language models...." (Fuente: Fuente desconocida)
3. "Future improvements should focus on more accurate and fast emotion recognition (e.g., deep learning, better fusion, additional behavioral modalities) and a richer, more adaptive empathic interface (diverse avatars, prosody control, LLM-based dialogue, handling emotional transitions, and possible per..." (Fuente: Fuente desconocida)
4. "Multi-modal agents (social robots and virtual agents) leverage nonverbal channels—especially facial expression recognition—to recognize affective states and express empathy, leading to increased perceived empathy and improved relational outcomes...." (Fuente: Fuente desconocida)
5. "Cognitive language agents embed LLMs in a feedback loop with the environment, using multimodal inputs, intermediate reasoning, memory, and self-modification to guide actions...." (Fuente: Fuente desconocida)
6. "Language agents have evolved from simple high-level instruction generators to systems that perform intermediate reasoning before acting...." (Fuente: Fuente desconocida)
7. "The dataset construction explicitly prioritizes segments where linguistic content is tightly coupled with visible behavior, supporting video-grounded dialogue modeling of nonverbal signals...." (Fuente: Fuente desconocida)
8. "Building on these advances, the authors use pseudo labels derived from VENUS to address the lack of large-scale conversational motion data and to jointly generate text, facial expressions, and body language aligned with conversational context...." (Fuente: Fuente desconocida)

## Discusión
1. "The paper outlines how empathy is measured in psychology (questionnaires and empathic accuracy) and how these measurements provide ground truth for ML, while also noting that some datasets instead use heuristic, source-based labels not tied to formal empathy definitions...." (Fuente: Fuente desconocida)
2. "The section stresses the importance of clear operational definitions of empathy for computational modeling, as different theoretical views lead to different annotation schemes and machine learning targets...." (Fuente: Fuente desconocida)
3. "The study enhances empathic LLM-based mental health chatbots by augmenting multi-modal input with nonverbal cues (facial expressions) using MLLM-based facial emotion recognition (FER), while leaving nonverbal output unchanged...." (Fuente: Fuente desconocida)
4. "Multi-modal LLMs can reliably interpret users’ affective states from visual input, and textual descriptions of visual cues are a particularly effective form of FER output...." (Fuente: Fuente desconocida)
5. "Language agents use LLMs as core computation units to reason, plan, and act in diverse environments, marking an emerging direction toward more human-like intelligence...." (Fuente: Fuente desconocida)
6. "Modern AI agents are composed of multiple LLM-based modules (reasoning, memory, planning, tool use) and have been applied to domains like coding, web browsing, and gameplay...." (Fuente: Fuente desconocida)
7. "The paper reports that MARS, trained on VENUS, can generate natural and contextually aligned nonverbal expressions alongside text, supported by quantitative metrics, qualitative analysis, and user studies...." (Fuente: Fuente desconocida)
8. "The authors propose MARS, a multimodal language model that jointly models text and nonverbal cues represented as discrete latent tokens, enabling understanding and generation of nonverbal behavior in dialogue...." (Fuente: Fuente desconocida)

## Implicaciones Futuras
1. "Existing empathy datasets differ widely in granularity (utterance-level vs. session-level), annotation targets (empathic concern, presence/absence, intensity, temporal dynamics), and modalities, leading to inconsistent operationalizations of empathy...." (Fuente: Fuente desconocida)
2. "Global unidirectional empathy is also studied in human–agent and other non-clinical dyadic settings, using numeric or ordinal scales to rate empathic responses in dialogues, stories, and virtual/robotic interactions...." (Fuente: Fuente desconocida)
3. "Multi-modal agents that leverage nonverbal cues (especially facial expressions) can enhance perceived empathy, engagement, trust, and therapeutic alliance, providing a template for MLLM-based empathic chatbots...." (Fuente: Fuente desconocida)
4. "Multi-modal LLMs provide a foundation for empathic chatbots by enabling the integration of nonverbal information (e.g., facial expression, posture, prosody) with textual dialogue for more context-aware responses...." (Fuente: Fuente desconocida)
5. "Instead of fixed relationship parameters or categories, agent relationships are abstracted: large language models select preferred conversation partners based on dialogue memory, with agents required to justify their choices, leading to more open and diverse social interactions...." (Fuente: Fuente desconocida)
6. "The authors argue that cognitive architecture and system design for LLM agents should be deeply integrated to create a mutually reinforcing development loop...." (Fuente: Fuente desconocida)
7. "Future work will expand the range of nonverbal modalities in the dataset, including vocal expressions, to improve model robustness and richness of nonverbal cues...." (Fuente: Fuente desconocida)
8. "The paper presents MARS, a multimodal language model that jointly understands and generates both text and nonverbal cues by training on unified discrete tokens for language, facial expressions, and body movements with a next-token prediction objective...." (Fuente: Fuente desconocida)

## Desafíos y Limitaciones
1. "Empathy is modeled through diverse task formulations—such as discrete classification, regression, and sequence labeling—reflecting different theoretical views of empathy and limiting comparability across studies...." (Fuente: Fuente desconocida)
2. "This work is presented as the first comprehensive systematic review of ML-based empathy detection across four modalities and diverse interaction contexts, covering all eligible studies up to May 2025...." (Fuente: Fuente desconocida)
3. "Cognitive architectures strongly shape agent performance, but most current architectures focus on internal reasoning (memory, reflection, planning, metacognition) rather than on redesigning the system itself, limiting the depth and breadth of metacognitive abilities...." (Fuente: Fuente desconocida)
4. "Agent communication is probabilistically triggered by proximity and social tendencies, with conversations designed to deepen over time through dialogue memory that promotes progressively more advanced topics...." (Fuente: Fuente desconocida)
5. "Empirical analysis reveals three key findings: GPT-3.5 better portrays positive personalities, stronger predefined traits improve portrayal success, and more dialogue turns both enhance personality expression and increase risk of misdirection by partners...." (Fuente: Fuente desconocida)
6. "Focusing the chatbot explicitly on personality topics improves inference accuracy without substantially harming user experience compared to more casual ‘getting to know you’ conversations...." (Fuente: Fuente desconocida)
7. "Human behavioral and physiological responses differ between face-to-face and remote emotional conversations, especially in facial expressions, EDA, and HRV...." (Fuente: Fuente desconocida)
8. "The main contributions include a comparative analysis of physiological and behavioral responses across settings, identification of features that vary by emotional and conversational condition, exploration of empathy differences, and release of a new multimodal dataset...." (Fuente: Fuente desconocida)

## Conclusiones
1. "Empathy is defined as a multifaceted construct with cognitive, affective, and compassionate components, each essential for holistic empathetic engagement and critical for making conversational agents more human-like and trusted...." (Fuente: Fuente desconocida)
2. "Empathic features in mental health conversational agents are highly heterogeneous, encompassing varied definitions, implementation strategies, and targeted empathic skills across studies...." (Fuente: Fuente desconocida)
3. "The system elicits distinct predominant emotions across themes, suggesting that its multi-emotion agent design can align output tone with situational context (e.g., fear for job loss, sadness for breakups, joy for family conflicts and academic anxiety)...." (Fuente: Fuente desconocida)
4. "Different technical strategies are used to operationalize emotional intelligence in AI, including emotion-guided prompting, sentiment lexicons, multimodal fusion, episodic memory, and dynamic game-theoretic adaptation...." (Fuente: Fuente desconocida)
5. "Language agents are systems that use LLMs as a core computation unit to reason, plan, and act in the world...." (Fuente: Fuente desconocida)
6. "The paper outlines a structured program: connect LLM agents to historical ideas, define CoALA, survey and analyze existing agents with it, and derive design guidance and open questions for AI and cognitive science...." (Fuente: Fuente desconocida)


IMPORTANTE: 
- USA las ideas de la literatura proporcionadas para fundamentar cada párrafo
- TODOS los campos deben tener contenido. NO dejes ningún campo vacío.

Responde con un JSON válido siguiendo EXACTAMENTE este formato de ejemplo:

{
  "thesis_statement": "La tesis central del paper en una oración clara",
  "sections": [
    {
      "section_name": "Introducción",
      "section_purpose": "Presentar el problema y la relevancia del tema",
      "paragraphs": [
        {
          "paragraph_number": 1,
          "key_idea": "La convergencia de XR e IA está transformando las interacciones humano-digitales",
          "supporting_points": [
            "Las tecnologías inmersivas han evolucionado significativamente",
            "Los agentes de IA están adquiriendo capacidades cognitivas avanzadas"
          ],
          "suggested_sources": ["Metaverse + VR", "Agents + Agent"]
        },
        {
          "paragraph_number": 2,
          "key_idea": "La empatía computacional es el eslabón perdido en la interacción humano-máquina",
          "supporting_points": [
            "Los sistemas actuales carecen de comprensión emocional genuina",
            "La empatía es fundamental para interacciones significativas"
          ],
          "suggested_sources": ["Empathy + Empathetic", "Emotion + Emotional"]
        }
      ]
    }
  ]
}

Genera el esquema completo para TODAS las secciones requeridas.
