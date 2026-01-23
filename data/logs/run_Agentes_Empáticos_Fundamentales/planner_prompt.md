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

# TAREA: Generar esquema detallado para paper de perspectivas

## Abstract
Abstract: La rápida convergencia entre la neurociencia cognitiva, la Realidad Extendida (XR) y la Inteligencia Artificial (IA) está redefiniendo los límites de la experiencia humana. Este artículo de perspectiva argumenta que estamos transitando desde herramientas digitales pasivas hacia un ecosistema de "Cuerpos Secos" (Dry Bodies)—entidades digitales autónomas dentro del Metaverso que operan bajo los principios de la cognición 4E (Embodied, Embedded, Enactive, Extended). Mientras que la investigación actual valida la eficacia de la XR para modular el comportamiento humano mediante la manipulación de los mecanismos de codificación predictiva del cerebro, sostenemos que el verdadero salto evolutivo reside en la integración de la empatía computacional.

Analizamos las limitaciones críticas de los actuales Modelos de Lenguaje Grande (LLM), que carecen de una auténtica "Teoría de la Mente", y proponemos una hoja de ruta hacia los "Agentes Fundamentales Empáticos". Estos futuros sistemas no solo imitarán el lenguaje, sino que integrarán arquitecturas cognitivas complejas, memoria episódica y modelos de sesgo de evaluación (Appraisal Biased Models) para generar interacciones humano-digitales genuinas. Finalmente, discutimos las profundas implicaciones éticas y los riesgos de la reconfiguración cognitiva derivada de la inmersión prolongada, delineando un marco necesario para garantizar que esta simbiosis entre el algoritmo y la emoción humana potencie, en lugar de erosionar, nuestra cognición biológica.

## Secciones (genera el JSON para TODAS)

## Introducción
**Propósito:** Presentar el tema, su relevancia y la tesis central del paper
**Párrafos:** 2-3
**Ideas de la literatura:**
  1. Empathy in CAs is operationalized through multiple components—such as emotion recognition, empathic response generation, personalization, and relational behaviors—but implementations are often partial and inconsistently evaluated. [Empathy + Empathic]
  2. The paper offers the first comprehensive systematic review of machine learning-based empathy detection across four modalities (text, audiovisual, audio, physiological) and multiple interaction contexts up to May 2025. [Empathy + Empathic]
  3. Recent emotionally intelligent AI systems focus on integrating rich emotion models and signals into LLMs and dialogue systems to enhance empathy, contextual relevance, and therapeutic support. [Emotion + Emotional]
  4. A multi-agent system prototype is developed in which an MLLM interprets facial expressions and supplies nonverbal context to an LLM-based chatbot, showing measurable changes in cognitive and affective language use and a non-significant upward trend i. [Emotion + Emotional]
  5. Modern language agents go beyond direct action selection to incorporate reasoning, planning, and memory management via LLMs, but the field lacks shared terminology and abstractions. [Agents + Agent]
  6. LLM-based agents benefit from architectural scaffolding (memory, reflection, planning, chain-of-thought prompting) that structures input and context to elicit more natural and believable behavior. [Agents + Agent]

## Estado Actual del Arte
**Propósito:** Revisar los avances recientes y el conocimiento establecido
**Párrafos:** 3-5
**Ideas de la literatura:**
  1. Evaluation of empathic capabilities in these agents is limited and methodologically heterogeneous, relying mostly on self-reported empathy measures and rarely incorporating expert assessments. [Empathy + Empathic]
  2. Empathy measurement in psychology relies largely on self-report questionnaires and empathic accuracy paradigms, while affective computing uses these instruments to obtain ground truth but sometimes applies heuristic labelling instead. [Empathy + Empathic]
  3. The fine-tuned LLM can accurately recognize users’ emotional states and generate high-quality empathetic responses without relying on sensitive clinical data. [Emotion + Emotional]
  4. Existing LLM-based empathetic systems are mostly text-centric and neglect speech and gestural modalities, limiting their ability to capture full emotional context and to respond multimodally. [Emotion + Emotional]
  5. These agents perform nontrivial LLM-based reasoning and learning, motivating the use of cognitive architectures to structure their internal and external interactions. [Agents + Agent]
  6. Prior agent architectures incorporate partial aspects of human-like cognition and affect—such as reasoning, learning, perception–brain–action loops, emotional adjustment, and LLM-based character portrayal—but do not yet achieve an integrated, behavio. [Agents + Agent]
  7. Multiple datasets provide rich multimodal signals (text, audio, visual, and sometimes personality/prosody) and diverse annotation schemes (categorical emotions, sentiment scales, continuous affective dimensions), enabling varied emotion and sentiment. [Nonverbal + Multimodal]
  8. Existing multimodal dialogue datasets and methods focus on conversational sentiment and multimodal dialogue generation but are limited in scale and lack detailed 3D facial and body language for modeling nonverbal cues. [Nonverbal + Multimodal]

## Identificación del Problema o Brecha
**Propósito:** Identificar limitaciones, contradicciones o áreas no exploradas
**Párrafos:** 2-3
**Ideas de la literatura:**
  1. The research follows a four-stage iterative process: initial classroom feasibility study, in-depth interviews, an interactive design workshop, and integration plus evaluation of a conversational AI agent. [Ai + Data]
  2. The review restricted studies to empirical research involving human participants where AI chatbots were used as an intervention, assessment, or support tool for executive functions. [Ai + Data]
  3. The paper’s main contributions are an empirical comparison of physiological and facial responses and empathy across face-to-face and remote emotional conversations, identification of the most effective emotion recognition approaches for each setting,. [Face + Emotional]
  4. Human behavioral and physiological responses differ between face-to-face and remote emotional conversations, particularly in facial expressions, EDA, and HRV. [Face + Emotional]
  5. Immersion in VR/Metaverse environments will drive the emergence of hybrid virtual-real bodily responses, gradually reshaping top-down predictive mechanisms to conform to Metaverse ‘rules’ and affordances. [Metaverse + Vr]
  6. With the rise of VR and Metaverse systems, the human body becomes deeply intertwined with virtual environments through immersion, renewing interest in 4E cognition and media studies and motivating an explicitly interdisciplinary approach. [Metaverse + Vr]
  7. The study’s primary contribution is a methodology that integrates smart wearables, streetscape/visual (SVI) segmentation, and weather sensors into a UDT to examine how urban morphology affects thermal perception and physiological responses. [Ngfr + Urban]
  8. The paper presents a proof-of-concept urban digital twin that integrates emerging urban data sources (wearables and street-view imagery) to sense outdoor thermal comfort and built-environment influences, aiming to support planning and management for . [Ngfr + Urban]

## La Nueva Perspectiva
**Propósito:** Proponer la visión o enfoque novedoso del autor
**Párrafos:** 3-4
**Ideas de la literatura:**
  1. This work is the first comprehensive systematic review of ML-based empathy detection across four input modalities (text, audio, audiovisual/video, physiological signals) and diverse interaction contexts. [Empathy + Empathic]
  2. The research focuses on neurophysiological emotional responses and their effect on perceived empathy rather than on advanced verbal capabilities, since the used platform version did not support large language models. [Empathy + Empathic]
  3. Future improvements should focus on more accurate and fast emotion recognition (e.g. [Emotion + Emotional]
  4. Multi-modal agents (social robots and virtual agents) leverage nonverbal channels—especially facial expression recognition—to recognize affective states and express empathy, leading to increased perceived empathy and improved relational outcomes. [Emotion + Emotional]
  5. Cognitive language agents embed LLMs in a feedback loop with the environment, using multimodal inputs, intermediate reasoning, memory, and self-modification to guide actions. [Agents + Agent]
  6. Language agents have evolved from simple high-level instruction generators to systems that perform intermediate reasoning before acting. [Agents + Agent]
  7. The dataset construction explicitly prioritizes segments where linguistic content is tightly coupled with visible behavior, supporting video-grounded dialogue modeling of nonverbal signals. [Nonverbal + Multimodal]
  8. Building on these advances, the authors use pseudo labels derived from VENUS to address the lack of large-scale conversational motion data and to jointly generate text, facial expressions, and body language aligned with conversational context. [Nonverbal + Multimodal]

## Discusión
**Propósito:** Analizar implicaciones, comparar con enfoques existentes
**Párrafos:** 3-5
**Ideas de la literatura:**
  1. The paper outlines how empathy is measured in psychology (questionnaires and empathic accuracy) and how these measurements provide ground truth for ML, while also noting that some datasets instead use heuristic, source-based labels not tied to formal. [Empathy + Empathic]
  2. The section stresses the importance of clear operational definitions of empathy for computational modeling, as different theoretical views lead to different annotation schemes and machine learning targets. [Empathy + Empathic]
  3. The study enhances empathic LLM-based mental health chatbots by augmenting multi-modal input with nonverbal cues (facial expressions) using MLLM-based facial emotion recognition (FER), while leaving nonverbal output unchanged. [Emotion + Emotional]
  4. Multi-modal LLMs can reliably interpret users’ affective states from visual input, and textual descriptions of visual cues are a particularly effective form of FER output. [Emotion + Emotional]
  5. Language agents use LLMs as core computation units to reason, plan, and act in diverse environments, marking an emerging direction toward more human-like intelligence. [Agents + Agent]
  6. Modern AI agents are composed of multiple LLM-based modules (reasoning, memory, planning, tool use) and have been applied to domains like coding, web browsing, and gameplay. [Agents + Agent]
  7. The paper reports that MARS, trained on VENUS, can generate natural and contextually aligned nonverbal expressions alongside text, supported by quantitative metrics, qualitative analysis, and user studies. [Nonverbal + Multimodal]
  8. The authors propose MARS, a multimodal language model that jointly models text and nonverbal cues represented as discrete latent tokens, enabling understanding and generation of nonverbal behavior in dialogue. [Nonverbal + Multimodal]

## Implicaciones Futuras
**Propósito:** Proyectar el impacto potencial y direcciones de investigación
**Párrafos:** 2-3
**Ideas de la literatura:**
  1. Existing empathy datasets differ widely in granularity (utterance-level vs. session-level), annotation targets (empathic concern, presence/absence, intensity, temporal dynamics), and modalities, leading to inconsistent operationalizations of empathy. [Empathy + Empathic]
  2. Global unidirectional empathy is also studied in human–agent and other non-clinical dyadic settings, using numeric or ordinal scales to rate empathic responses in dialogues, stories, and virtual/robotic interactions. [Empathy + Empathic]
  3. Multi-modal agents that leverage nonverbal cues (especially facial expressions) can enhance perceived empathy, engagement, trust, and therapeutic alliance, providing a template for MLLM-based empathic chatbots. [Emotion + Emotional]
  4. Multi-modal LLMs provide a foundation for empathic chatbots by enabling the integration of nonverbal information (e.g., facial expression, posture, prosody) with textual dialogue for more context-aware responses. [Emotion + Emotional]
  5. Instead of fixed relationship parameters or categories, agent relationships are abstracted: large language models select preferred conversation partners based on dialogue memory, with agents required to justify their choices, leading to more open and. [Agents + Agent]
  6. The authors argue that cognitive architecture and system design for LLM agents should be deeply integrated to create a mutually reinforcing development loop. [Agents + Agent]
  7. Future work will expand the range of nonverbal modalities in the dataset, including vocal expressions, to improve model robustness and richness of nonverbal cues. [Nonverbal + Multimodal]
  8. The paper presents MARS, a multimodal language model that jointly understands and generates both text and nonverbal cues by training on unified discrete tokens for language, facial expressions, and body movements with a next-token prediction objectiv. [Nonverbal + Multimodal]

## Desafíos y Limitaciones
**Propósito:** Reconocer obstáculos y limitaciones de la perspectiva
**Párrafos:** 2-3
**Ideas de la literatura:**
  1. Empathy is modeled through diverse task formulations—such as discrete classification, regression, and sequence labeling—reflecting different theoretical views of empathy and limiting comparability across studies. [Empathy + Empathic]
  2. This work is presented as the first comprehensive systematic review of ML-based empathy detection across four modalities and diverse interaction contexts, covering all eligible studies up to May 2025. [Empathy + Empathic]
  3. Cognitive architectures strongly shape agent performance, but most current architectures focus on internal reasoning (memory, reflection, planning, metacognition) rather than on redesigning the system itself, limiting the depth and breadth of metacog. [Agents + Agent]
  4. Agent communication is probabilistically triggered by proximity and social tendencies, with conversations designed to deepen over time through dialogue memory that promotes progressively more advanced topics. [Agents + Agent]
  5. Empirical analysis reveals three key findings: GPT-3. [Personality + Traits]
  6. Focusing the chatbot explicitly on personality topics improves inference accuracy without substantially harming user experience compared to more casual ‘getting to know you’ conversations. [Personality + Traits]
  7. Human behavioral and physiological responses differ between face-to-face and remote emotional conversations, especially in facial expressions, EDA, and HRV. [Face + Emotional]
  8. The main contributions include a comparative analysis of physiological and behavioral responses across settings, identification of features that vary by emotional and conversational condition, exploration of empathy differences, and release of a new . [Face + Emotional]

## Conclusiones
**Propósito:** Sintetizar los puntos clave y el mensaje final
**Párrafos:** 1-2
**Ideas de la literatura:**
  1. Empathy is defined as a multifaceted construct with cognitive, affective, and compassionate components, each essential for holistic empathetic engagement and critical for making conversational agents more human-like and trusted. [Empathy + Empathic]
  2. Empathic features in mental health conversational agents are highly heterogeneous, encompassing varied definitions, implementation strategies, and targeted empathic skills across studies. [Empathy + Empathic]
  3. The system elicits distinct predominant emotions across themes, suggesting that its multi-emotion agent design can align output tone with situational context (e.g. [Emotion + Emotional]
  4. Different technical strategies are used to operationalize emotional intelligence in AI, including emotion-guided prompting, sentiment lexicons, multimodal fusion, episodic memory, and dynamic game-theoretic adaptation. [Emotion + Emotional]
  5. Language agents are systems that use LLMs as a core computation unit to reason, plan, and act in the world. [Agents + Agent]
  6. The paper outlines a structured program: connect LLM agents to historical ideas, define CoALA, survey and analyze existing agents with it, and derive design guidance and open questions for AI and cognitive science. [Agents + Agent]


## Formato de Salida (JSON)

```json
{
  "thesis_statement": "Tesis central en una oración",
  "sections": [
    {
      "section_name": "Nombre de la sección",
      "section_purpose": "Propósito breve",
      "paragraphs": [
        {
          "paragraph_number": 1,
          "key_idea": "Idea específica y argumentativa (NO genérica)",
          "supporting_points": ["Punto de apoyo 1", "Punto de apoyo 2"],
          "suggested_sources": ["Topic1", "Topic2"]
        }
      ]
    }
  ]
}
```

## Instrucciones
1. Genera exactamente el número de párrafos indicado por sección
2. Basa cada key_idea en las ideas de literatura proporcionadas
3. Todos los campos deben tener contenido
