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
  1. LLM-based agents benefit from architectural scaffolding (memory, reflection, planning, chain-of-thought prompting) that structures input and context to elicit more natural and believable behavior. [Agents + Agent]
  2. Prior agent architectures incorporate partial aspects of human-like cognition and affect—such as reasoning, learning, perception–brain–action loops, emotional adjustment, and LLM-based character portrayal—but do not yet achieve an integrated, behavio. [Agents + Agent]
  3. Existing empathy datasets differ widely in granularity (utterance-level vs. session-level), annotation targets (empathic concern, presence/absence, intensity, temporal dynamics), and modalities, leading to inconsistent operationalizations of empathy. [Empathy + Empathetic]
  4. The paper offers the first comprehensive systematic review of machine learning-based empathy detection across four modalities (text, audiovisual, audio, physiological) and multiple interaction contexts up to May 2025. [Empathy + Empathetic]
  5. Recent emotionally intelligent AI systems focus on integrating rich emotion models and signals into LLMs and dialogue systems to enhance empathy, contextual relevance, and therapeutic support. [Emotional + Emotion]
  6. A multi-agent system prototype is developed in which an MLLM interprets facial expressions and supplies nonverbal context to an LLM-based chatbot, showing measurable changes in cognitive and affective language use and a non-significant upward trend i. [Emotional + Emotion]
  7. This review aims to systematically map and evaluate empathic conversational agent platform designs for mental health, focusing on design characteristics, empathy-related mechanisms, and reported outcomes. [Health + Mental]
  8. The review includes 19 studies of empathic conversational agents for mental health, with most reporting both system design and human evaluations. [Health + Mental]
  9. Focusing the chatbot explicitly on personality topics improves inference accuracy without substantially harming user experience compared to more casual ‘getting to know you’ conversations. [Personality + Traits]
  10. Explicitly focusing the chatbot on personality assessment does not degrade user experience; users rate these interactions as equally natural, pleasant, engaging, and humanlike as more naturalistic conditions. [Personality + Traits]
  11. The paper’s main contributions are an empirical comparison of physiological and facial responses and empathy across face-to-face and remote emotional conversations, identification of the most effective emotion recognition approaches for each setting,. [Face + Emotional]
  12. Human behavioral and physiological responses differ between face-to-face and remote emotional conversations, particularly in facial expressions, EDA, and HRV. [Face + Emotional]

## Estado Actual del Arte
**Propósito:** Revisar los avances recientes y el conocimiento establecido
**Párrafos:** 3-5
**Ideas de la literatura:**
  1. Modern language agents go beyond direct action selection to incorporate reasoning, planning, and memory management via LLMs, but the field lacks shared terminology and abstractions. [Agents + Agent]
  2. These agents perform nontrivial LLM-based reasoning and learning, motivating the use of cognitive architectures to structure their internal and external interactions. [Agents + Agent]
  3. The section stresses the importance of clear operational definitions of empathy for computational modeling, as different theoretical views lead to different annotation schemes and machine learning targets. [Empathy + Empathetic]
  4. Empathy is modeled through diverse task formulations—such as discrete classification, regression, and sequence labeling—reflecting different theoretical views of empathy and limiting comparability across studies. [Empathy + Empathetic]
  5. The system elicits distinct predominant emotions across themes, suggesting that its multi-emotion agent design can align output tone with situational context (e.g. [Emotional + Emotion]
  6. Future improvements should focus on more accurate and fast emotion recognition (e.g. [Emotional + Emotion]
  7. The review systematically maps existing empathic conversational agent architectures for mental health, assessing both their technical emotion-detection performance and user acceptability. [Health + Mental]
  8. Despite rapid development of mental health conversational agents, there is limited systematic knowledge about how empathy is concretely designed, implemented, and evaluated in these systems. [Health + Mental]
  9. Empirical analysis reveals three key findings: GPT-3. [Personality + Traits]
  10. Personality-infused role-playing, illustrated using Big Five traits in a job-hunting dialogue scenario, is argued to make conversational agents more realistic, engaging, and immersive for users. [Personality + Traits]
  11. Human behavioral and physiological responses differ between face-to-face and remote emotional conversations, especially in facial expressions, EDA, and HRV. [Face + Emotional]
  12. The main contributions include a comparative analysis of physiological and behavioral responses across settings, identification of features that vary by emotional and conversational condition, exploration of empathy differences, and release of a new . [Face + Emotional]
  13. Multiple datasets provide rich multimodal signals (text, audio, visual, and sometimes personality/prosody) and diverse annotation schemes (categorical emotions, sentiment scales, continuous affective dimensions), enabling varied emotion and sentiment. [Multimodal + Nonverbal]
  14. The paper reports that MARS, trained on VENUS, can generate natural and contextually aligned nonverbal expressions alongside text, supported by quantitative metrics, qualitative analysis, and user studies. [Multimodal + Nonverbal]
  15. The study’s primary contribution is a methodology that integrates smart wearables, streetscape/visual (SVI) segmentation, and weather sensors into a UDT to examine how urban morphology affects thermal perception and physiological responses. [Ngfr + Data]
  16. The paper presents a proof-of-concept urban digital twin that integrates emerging urban data sources (wearables and street-view imagery) to sense outdoor thermal comfort and built-environment influences, aiming to support planning and management for . [Ngfr + Data]

## Identificación del Problema o Brecha
**Propósito:** Identificar limitaciones, contradicciones o áreas no exploradas
**Párrafos:** 2-3
**Ideas de la literatura:**
  1. The authors propose MARS, a multimodal language model that jointly models text and nonverbal cues represented as discrete latent tokens, enabling understanding and generation of nonverbal behavior in dialogue. [Multimodal + Nonverbal]
  2. Existing multimodal dialogue datasets and methods focus on conversational sentiment and multimodal dialogue generation but are limited in scale and lack detailed 3D facial and body language for modeling nonverbal cues. [Multimodal + Nonverbal]
  3. The study integrates outdoor thermal comfort, walkability, and 3D urban form within an urban digital twin (UDT) using heterogeneous data sources such as wearables and street view imagery. [Ngfr + Data]
  4. The paper proposes integrating wearable sensing with a Digital Twin of the city to capture and model pedestrian comfort dynamics at high spatial and temporal resolution. [Ngfr + Data]
  5. The paper introduces Sibyl, a new paradigm for Sensible and Visionary Commonsense Knowledge that dynamically infers future-aware, response-specific commonsense to guide empathetic dialogue generation. [Commonsense + Dialogue]
  6. Sibyl introduces a paradigm of ‘visionary commonsense’ by using a strong LLM (GPT‑4o) to generate four categories of commonsense inferences from dialogue history plus response, then validating these categories with human annotators. [Commonsense + Dialogue]
  7. The Metaverse is conceptualized as a form of artificial life whose evolution intertwines the human body with virtual environments, demanding new points of theoretical connection for understanding its cognitive effects. [Metaverse + Life]
  8. Immersion in VR/Metaverse environments will drive the emergence of hybrid virtual-real bodily responses, gradually reshaping top-down predictive mechanisms to conform to Metaverse ‘rules’ and affordances. [Metaverse + Life]
  9. Modeling dialogues as heterogeneous conversational graphs, which incorporate speakers, utterances, and their relations, leads to better personality recognition than sequence-based or homogeneous graph baselines. [Personality + Dialogue]
  10. There is an identified need for models that jointly leverage data augmentation and heterogeneous graph networks to better capture complex conversational patterns for personality recognition. [Personality + Dialogue]
  11. The study uses virtual reality to examine how the coherence and complexity of outdoor planting designs affect users’ perceptions of time and landscape aesthetics. [Participants + Complexity]
  12. The study introduces virtual reality as a controlled experimental tool to manipulate a specific design variable—vegetation layout along a campus path—to investigate its effects on perceived coherence, complexity, and sense of time. [Participants + Complexity]

## La Nueva Perspectiva
**Propósito:** Proponer la visión o enfoque novedoso del autor
**Párrafos:** 3-4
**Ideas de la literatura:**
  1. GenAI-based agents have emerging potential to act as autonomous, cognitively capable teammates that proactively contribute in group settings. [Agents + Agent]
  2. Agents’ interaction design includes names, visible role labels, lifelike idle and speaking animations, hand-raising, and gaze/turn-taking behaviors, with a Wizard-of-Oz system controlling when agents speak to simulate socially appropriate contributio. [Agents + Agent]
  3. Empathy measurement in psychology relies largely on self-report questionnaires and empathic accuracy paradigms, while affective computing uses these instruments to obtain ground truth but sometimes applies heuristic labelling instead. [Empathy + Empathetic]
  4. The paper outlines how empathy is measured in psychology (questionnaires and empathic accuracy) and how these measurements provide ground truth for ML, while also noting that some datasets instead use heuristic, source-based labels not tied to formal. [Empathy + Empathetic]
  5. The fine-tuned LLM can accurately recognize users’ emotional states and generate high-quality empathetic responses without relying on sensitive clinical data. [Emotional + Emotion]
  6. Existing LLM-based empathetic systems are mostly text-centric and neglect speech and gestural modalities, limiting their ability to capture full emotional context and to respond multimodally. [Emotional + Emotion]
  7. Understanding the design and evaluation of empathic conversational agents has implications for future clinical integration, ethical deployment, and the development of guidelines or best practices in digital mental health. [Health + Mental]
  8. Data extraction focused on study designs, methods for evaluating empathy, and types of conversational agent architectures to summarize all findings. [Health + Mental]
  9. Personality inference is most accurate when the chatbot is explicitly prompted to assess personality (assessment condition), yielding moderate correlations between about r = .33 and r = .64. [Personality + Traits]
  10. Through personality back-testing with GPT-3.5, PsyPlay achieves about 80% success in accurately portraying intended personality traits, and reveals that LLMs aligned with positive values more reliably play positive personalities than negative ones. [Personality + Traits]
  11. The novel contribution of this work is creating a comparative multimodal dataset of physiological and behavioral responses during emotional conversations in both face-to-face and remote settings, to analyze empathy, response differences, and cross-se. [Face + Emotional]
  12. Conversation type and self-reported arousal and valence are treated as independent variables, while EDA, PPG features, facial action units, and reported empathy factors are dependent variables. [Face + Emotional]
  13. The paper presents MARS, a multimodal language model that jointly understands and generates both text and nonverbal cues by training on unified discrete tokens for language, facial expressions, and body movements with a next-token prediction objectiv. [Multimodal + Nonverbal]
  14. Visualization highlights VENUS’s capacity to detect and align nonverbal affective signals—such as facial expressions and gestures—with conversational context. [Multimodal + Nonverbal]
  15. The research aims to inform more responsive and human-centered urban design and mobility policies by revealing how specific urban features and conditions impact pedestrian comfort in situ. [Ngfr + Data]
  16. Future developments aim to use integrated data not only for visualization but also to classify paths by urban morphological features and identify commonly used routes and thermal hot spots. [Ngfr + Data]

## Discusión
**Propósito:** Analizar implicaciones, comparar con enfoques existentes
**Párrafos:** 3-5
**Ideas de la literatura:**
  1. Cognitive language agents embed LLMs in a feedback loop with the environment, using multimodal inputs, intermediate reasoning, memory, and self-modification to guide actions. [Agents + Agent]
  2. Agent communication is probabilistically triggered by proximity and social tendencies, with conversations designed to deepen over time through dialogue memory that promotes progressively more advanced topics. [Agents + Agent]
  3. This work is the first comprehensive systematic review of ML-based empathy detection across four input modalities (text, audio, audiovisual/video, physiological signals) and diverse interaction contexts. [Empathy + Empathetic]
  4. This work is presented as the first comprehensive systematic review of ML-based empathy detection across four modalities and diverse interaction contexts, covering all eligible studies up to May 2025. [Empathy + Empathetic]
  5. Multi-modal agents (social robots and virtual agents) leverage nonverbal channels—especially facial expression recognition—to recognize affective states and express empathy, leading to increased perceived empathy and improved relational outcomes. [Emotional + Emotion]
  6. Different technical strategies are used to operationalize emotional intelligence in AI, including emotion-guided prompting, sentiment lexicons, multimodal fusion, episodic memory, and dynamic game-theoretic adaptation. [Emotional + Emotion]
  7. The paper aims to systematically review empathic conversational agent platforms for mental health, focusing on their design characteristics, underlying empathy models, implementation techniques, and evaluation outcomes. [Health + Mental]
  8. Empathic conversational agents for mental health are typically evaluated on three fronts: technical performance (e.g., accuracy of emotion detection), user experience (e.g., perceived empathy, satisfaction), and clinical or mental health outcomes. [Health + Mental]
  9. In the assistant condition, where the chatbot does not ask personal questions and only reacts to user prompts, personality inference accuracy is lowest but still often above zero, indicating that everyday assistant-type interactions carry psychologic. [Personality + Traits]
  10. Focusing directly on personality-relevant topics can increase personality inference accuracy without degrading user experience relative to a more casual acquaintance-style interaction. [Personality + Traits]
  11. Findings highlight the potential to improve remote interactions by real-time multimodal emotion detection and transmission as an additional social cue. [Face + Emotional]
  12. The study compares emotional video-mediated conversations with face-to-face interactions using behavioral and physiological measures to understand their impact on emotions, empathy, and bodily responses. [Face + Emotional]
  13. Future work will expand the range of nonverbal modalities in the dataset, including vocal expressions, to improve model robustness and richness of nonverbal cues. [Multimodal + Nonverbal]
  14. Building on these advances, the authors use pseudo labels derived from VENUS to address the lack of large-scale conversational motion data and to jointly generate text, facial expressions, and body language aligned with conversational context. [Multimodal + Nonverbal]
  15. A methodological framework is introduced that fuses multimodal wearable data with urban context variables, enabling the detection and mapping of comfort hotspots and stressors along pedestrian trajectories. [Ngfr + Data]
  16. Beyond technical aspects, the NGFR hub is proposed as a technological-societal readiness benchmark for smart cities, indicating their capacity to deploy advanced resources to protect lives and property, especially under climate change-induced disaste. [Ngfr + Data]

## Implicaciones Futuras
**Propósito:** Proyectar el impacto potencial y direcciones de investigación
**Párrafos:** 2-3
**Ideas de la literatura:**
  1. Modern AI agents are composed of multiple LLM-based modules (reasoning, memory, planning, tool use) and have been applied to domains like coding, web browsing, and gameplay. [Agents + Agent]
  2. Instead of fixed relationship parameters or categories, agent relationships are abstracted: large language models select preferred conversation partners based on dialogue memory, with agents required to justify their choices, leading to more open and. [Agents + Agent]
  3. Empathy in CAs is operationalized through multiple components—such as emotion recognition, empathic response generation, personalization, and relational behaviors—but implementations are often partial and inconsistently evaluated. [Empathy + Empathetic]
  4. The authors differentiate empathy detection from emotion detection, emphasizing that empathy requires modeling relational dynamics between at least two individuals (the expresser and the responder) rather than a single emotional state. [Empathy + Empathetic]
  5. Multi-modal LLMs can reliably interpret users’ affective states from visual input, and textual descriptions of visual cues are a particularly effective form of FER output. [Emotional + Emotion]
  6. The system employs an emotion-aware prompt engineering strategy to steer the LLM toward generating empathetic responses aligned with detected emotional states. [Emotional + Emotion]
  7. The review also seeks to identify challenges and future research directions, including ethical and safety issues, robustness and accuracy of empathic inference, and the need for standardized evaluation metrics in mental health contexts. [Health + Mental]
  8. The review concludes that AI-empowered empathic CAs are feasible, are often rated satisfactory by users, and could help address gaps in mental health service provision across various settings. [Health + Mental]
  9. The method uses large language models as evaluators, with a dedicated prompt (Table 7) to back-test personality traits from dialogue, following recent work on LLM-based evaluation. [Personality + Traits]
  10. PsyPlay introduces a personality back-testing method that infers a role’s personality directly from dialogue using LLM evaluators, arguing this is more reflective than having agents fill out personality questionnaires. [Personality + Traits]
  11. Physiological and facial responses differ systematically between face-to-face and remote conversations, with remote settings linked to more positive, higher-arousal emotional states. [Face + Emotional]
  12. The paper’s main contribution is a comparative multimodal dataset of physiological and behavioral responses during emotional conversations in both face-to-face and remote settings, enabling analysis and modeling of differences between these modes. [Face + Emotional]
  13. The final VENUS annotations align textual utterances with time-synchronized 3D nonverbal expression parameters, enabling video-grounded dialogue modeling of nonverbal behavior. [Multimodal + Nonverbal]
  14. The references list situates the survey within a broad body of work on multimodal emotion recognition, sentiment analysis, dialogic emotion analysis, datasets, feature toolkits, and large language model-based methods. [Multimodal + Nonverbal]
  15. A key novel extension is to improve NGFR performance by adopting self-aware computing as a methodological framework, also viewed as a basis for a digital twin of the system, particularly for crowd monitoring (CW) and emergency services. [Ngfr + Data]
  16. The NGFR hub’s CW mode operates as a perception–action cycle embedded in a smart city infrastructure, using cloud resources for learning and reasoning and providing real-time CW risk estimates to human decision makers. [Ngfr + Data]

## Desafíos y Limitaciones
**Propósito:** Reconocer obstáculos y limitaciones de la perspectiva
**Párrafos:** 2-3
**Ideas de la literatura:**
  1. Cognitive architectures strongly shape agent performance, but most current architectures focus on internal reasoning (memory, reflection, planning, metacognition) rather than on redesigning the system itself, limiting the depth and breadth of metacog. [Agents + Agent]
  2. Language agents use LLMs as core computation units to reason, plan, and act in diverse environments, marking an emerging direction toward more human-like intelligence. [Agents + Agent]
  3. The study enhances empathic LLM-based mental health chatbots by augmenting multi-modal input with nonverbal cues (facial expressions) using MLLM-based facial emotion recognition (FER), while leaving nonverbal output unchanged. [Emotional + Emotion]
  4. Multi-modal agents that leverage nonverbal cues (especially facial expressions) can enhance perceived empathy, engagement, trust, and therapeutic alliance, providing a template for MLLM-based empathic chatbots. [Emotional + Emotion]
  5. The chatbot’s prompted role (assessment, acquaintance, assistant) strongly affects inference accuracy, whereas user interaction style (naturalistic vs unconstrained) has little impact. [Personality + Traits]
  6. Different interaction modes (assessment, acquaintance, assistant) significantly affect inference accuracy and user experience; naturalistic, reciprocal conversation styles improve user experience without sacrificing personality-prediction accuracy. [Personality + Traits]
  7. The dataset construction explicitly prioritizes segments where linguistic content is tightly coupled with visible behavior, supporting video-grounded dialogue modeling of nonverbal signals. [Multimodal + Nonverbal]
  8. Multimodal approaches that incorporate facial expressions, speech tone, and other audio-visual cues provide richer emotional information than text alone and can improve detection of affective states and opportunities for empathetic responses. [Multimodal + Nonverbal]
  9. For response generation, Sibyl augments the dialogue context with the four visionary commonsense inferences Kp as a bridge to the next response, and explores both finetuned and prompt-based generation strategies. [Commonsense + Dialogue]
  10. The paper evaluates Sibyl by comparing it against several state-of-the-art empathetic dialogue and commonsense reasoning baselines. [Commonsense + Dialogue]
  11. The authors propose heterogeneous conversational graph networks that separately capture contextual influences and inherent personality traits in dialogues. [Personality + Dialogue]
  12. The authors propose a heterogeneous conversational graph network that models multiple types of nodes and relations in dialogue (utterances, speakers, and conversations) to improve personality recognition. [Personality + Dialogue]
  13. Global unidirectional empathy is also studied in human–agent and other non-clinical dyadic settings, using numeric or ordinal scales to rate empathic responses in dialogues, stories, and virtual/robotic interactions. [Empathy + Empathetic]
  14. The authors highlight substantial conceptual ambiguity in how empathy is defined and measured in psychology versus empathy computing, noting that computational work often collapses nuanced constructs (e.g. [Empathy + Empathetic]
  15. The study adopts a quantitative approach to measure and compare physiological and behavioral indicators in face-to-face versus remote conversations. [Face + Emotional]
  16. Type of conversation and self-reported arousal and valence are treated as independent variables, while EDA, PPG features, facial action units, and reported empathy measures serve as dependent variables. [Face + Emotional]

## Conclusiones
**Propósito:** Sintetizar los puntos clave y el mensaje final
**Párrafos:** 1-2
**Ideas de la literatura:**
  1. The LLM pipeline maintains a continuous global conversation memory and uses the evolving discussion context to generate agent opinions and immediate responses grounded in both history and current context. [Agents + Agent]
  2. Language agents have evolved from simple high-level instruction generators to systems that perform intermediate reasoning before acting. [Agents + Agent]
  3. The paper is structured to move from psychological definitions through task and dataset analysis to modality-specific ML models and real-world applications of empathy detection. [Empathy + Empathetic]
  4. Empathy detection is conceptually distinct from emotion detection because it models relational dynamics between at least two individuals—the initial expresser and the responder whose empathic reaction is assessed. [Empathy + Empathetic]
  5. Current LLM-based empathic behavior is primarily achieved via generic pre-prompts and instructions to detect and express emotions in text, rather than deeper built-in empathic capabilities. [Emotional + Emotion]
  6. Across FER and temporal tasks, GPT-4-based MLLMs not only classify emotions but also generate meaningful textual descriptions, including recognition of occlusions and hand gestures. [Emotional + Emotion]
  7. The review aims to assess conversational agent (CA) designs in mental health care that are specifically engineered to convey empathy and how that empathy is implemented technically. [Health + Mental]
  8. Empathic conversational agents (CAs) for mental health show generally positive outcomes, but the existing evidence base is limited by small samples, short study durations, heterogeneous designs, and a focus on feasibility rather than robust clinical . [Health + Mental]
  9. Even in an assistant role without asking personal questions, ChatGPT still extracts psychologically meaningful personality signals from everyday interactions, though with lower accuracy. [Personality + Traits]
  10. Personality inference accuracy depends strongly on conversational setup, with highest performance when the chatbot is explicitly prompted to elicit personality-relevant information. [Personality + Traits]


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
3. Usa suggested_sources para indicar qué topics fundamentan cada párrafo
4. Todos los campos deben tener contenido
