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
  1. Human behavioral and physiological responses differ between face-to-face and remote emotional conversations, particularly in facial expressions, EDA, and HRV. [Face + Emotional]
  2. The paper’s main contributions are an empirical comparison of physiological and facial responses and empathy across face-to-face and remote emotional conversations, identification of the most effective emotion recognition approaches for each setting,. [Face + Emotional]
  3. The paper offers the first comprehensive systematic review of machine learning-based empathy detection across four modalities (text, audiovisual, audio, physiological) and multiple interaction contexts up to May 2025. [Empathy + Empathic]
  4. Empathy is modeled through diverse task formulations—such as discrete classification, regression, and sequence labeling—reflecting different theoretical views of empathy and limiting comparability across studies. [Empathy + Empathic]
  5. Evolving Agents consists of two tightly coupled subsystems, Behavior and Personality, which form a feedback loop where actions consider personality traits and experiences from actions in turn update personality. [Agents + Agent]
  6. Prior agent architectures incorporate partial aspects of human-like cognition and affect—such as reasoning, learning, perception–brain–action loops, emotional adjustment, and LLM-based character portrayal—but do not yet achieve an integrated, behavio. [Agents + Agent]
  7. Personality inference is most accurate when the chatbot is explicitly prompted to assess personality (assessment condition), yielding moderate correlations between about r = .33 and r = .64. [Personality + Gpt]
  8. In the assistant condition, where the chatbot does not ask personal questions and only reacts to user prompts, personality inference accuracy is lowest but still often above zero, indicating that everyday assistant-type interactions carry psychologic. [Personality + Gpt]
  9. Multiple datasets provide rich multimodal signals (text, audio, visual, and sometimes personality/prosody) and diverse annotation schemes (categorical emotions, sentiment scales, continuous affective dimensions), enabling varied emotion and sentiment. [Emotion + Multimodal]
  10. The analysis establishes that multimodal integration of neural, physiological, and textual signals enables more accurate and nuanced detection of users’ emotional states than single‑modality approaches. [Emotion + Multimodal]
  11. The study uses 2,000 prompts from EmpatheticDialogues, balanced across 32 positive and negative emotions, and prompts LLMs with an explicit empathy framework (cognitive, affective, compassionate) to enable fine-grained comparison with human responses. [Empathetic + Empathy]
  12. The experimental setup uses ED and ESConv as benchmarks and a comprehensive suite of overlap, diversity, embedding, human, and LLM-based metrics to evaluate empathetic dialogue quality. [Empathetic + Empathy]

## Estado Actual del Arte
**Propósito:** Revisar los avances recientes y el conocimiento establecido
**Párrafos:** 3-5
**Ideas de la literatura:**
  1. Human behavioral and physiological responses differ between face-to-face and remote emotional conversations, especially in facial expressions, EDA, and HRV. [Face + Emotional]
  2. Physiological and facial responses differ systematically between face-to-face and remote conversations, with remote settings linked to more positive, higher-arousal emotional states. [Face + Emotional]
  3. This work is the first comprehensive systematic review of ML-based empathy detection across four input modalities (text, audio, audiovisual/video, physiological signals) and diverse interaction contexts. [Empathy + Empathic]
  4. This work is presented as the first comprehensive systematic review of ML-based empathy detection across four modalities and diverse interaction contexts, covering all eligible studies up to May 2025. [Empathy + Empathic]
  5. Multimodal and game-based agent systems (e.g., in Minecraft) and social multi-agent frameworks demonstrate rich task execution and social behaviors but still operate with largely fixed or ad hoc personality settings. [Agents + Agent]
  6. Evolving Agents comprise two main systems—Personality (Cognition, Emotion, Character Growth) and Behavior (Planning, Action)—whose interaction produces a feedback loop of behavior-personality co-evolution. [Agents + Agent]
  7. Focusing the chatbot explicitly on personality topics improves inference accuracy without substantially harming user experience compared to more casual ‘getting to know you’ conversations. [Personality + Gpt]
  8. ChatGPT can infer users’ Big Five personality traits above chance from free-form interactions, as shown by positive, often significant correlations between self-reported and inferred scores. [Personality + Gpt]
  9. Existing surveys on multimodal emotion recognition largely focus on non-conversational settings or on feature fusion alone, failing to adequately address conversation-specific issues such as interlocutor modeling, context, cross-modal alignment, reas. [Emotion + Multimodal]
  10. The references list situates the survey within a broad body of work on multimodal emotion recognition, sentiment analysis, dialogic emotion analysis, datasets, feature toolkits, and large language model-based methods. [Emotion + Multimodal]
  11. The EmpathyAgent benchmark is positioned as a practical tool for building powerful empathetic agents by enabling effective training and evaluation of embodied empathetic behaviors. [Empathetic + Empathy]
  12. Baseline large-capacity conversation models trained on spontaneous internet conversations are not rated as very empathetic, but their empathetic performance can be improved using the new dataset. [Empathetic + Empathy]
  13. The review systematically maps existing empathic conversational agent architectures for mental health, assessing both their technical emotion-detection performance and user acceptability. [Empathic + Empathy]
  14. The review aims to assess conversational agent (CA) designs in mental health care that are specifically engineered to convey empathy and how that empathy is implemented technically. [Empathic + Empathy]
  15. These agents perform nontrivial LLM-based reasoning and learning, motivating the use of cognitive architectures to structure their internal and external interactions. [Llm + Agents]
  16. Modern language agents go beyond direct action selection to incorporate reasoning, planning, and memory management via LLMs, but the field lacks shared terminology and abstractions. [Llm + Agents]

## Identificación del Problema o Brecha
**Propósito:** Identificar limitaciones, contradicciones o áreas no exploradas
**Párrafos:** 2-3
**Ideas de la literatura:**
  1. The review restricted studies to empirical research involving human participants where AI chatbots were used as an intervention, assessment, or support tool for executive functions. [Studies + Chatbots]
  2. Using a PRISMA 2020–guided systematic search (2021–present) across major databases, the authors narrowed 115 initially identified articles down to 10 eligible empirical studies on AI chatbots and executive functions. [Studies + Chatbots]
  3. Earlier work on automatic personality recognition (e.g., Mehl et al.) used psycholinguistic attributes from daily-life conversations but only modeled the subject’s speech, ignoring interlocutors’ influence on personality expression. [Personality + Dialogue]
  4. The paper targets automatic recognition of Big-Five personality traits from dialogue, which is important for user-adaptive, effective human-robot interaction. [Personality + Dialogue]
  5. The paper introduces Sibyl, a new paradigm for Sensible and Visionary Commonsense Knowledge that dynamically infers future-aware, response-specific commonsense to guide empathetic dialogue generation. [Commonsense + Dialogue]
  6. Sibyl introduces a paradigm of ‘visionary commonsense’ by using a strong LLM (GPT‑4o) to generate four categories of commonsense inferences from dialogue history plus response, then validating these categories with human annotators. [Commonsense + Dialogue]
  7. The Metaverse is conceptualized as a form of artificial life whose evolution intertwines the human body with virtual environments, demanding new points of theoretical connection for understanding its cognitive effects. [Metaverse + Life]
  8. Immersion in VR/Metaverse environments will drive the emergence of hybrid virtual-real bodily responses, gradually reshaping top-down predictive mechanisms to conform to Metaverse ‘rules’ and affordances. [Metaverse + Life]
  9. Each configuration was evaluated in single-round experiments using four metrics across five personality traits to assess overall model capability. [Personality + Dialogue]
  10. Personality recognition in dialogue has recently attracted growing attention due to its utility in building user personas and understanding user needs in various applications. [Personality + Dialogue]
  11. The paper introduces a novel LLM-based, explainable depression assessment system that integrates multiple conversational data streams to generate a real-time, multidimensional, and continuously updating depression risk profile, aiming to overcome the. [Mental + Emotion]
  12. The paper proposes an LLM-based system that analyzes real-time conversational cues and subtle emotional language patterns to assess mental state more accurately and dynamically. [Mental + Emotion]
  13. Beyond technical aspects, the NGFR hub is proposed as a technological-societal readiness benchmark for smart cities, indicating their capacity to deploy advanced resources to protect lives and property, especially under climate change-induced disaste. [Ngfr + Hub]
  14. The paper proposes an NGFR AI-enabled hub (a modified SmartHub) as a practice-centric, expandable architecture that embeds next-generation first responder technologies into smart city infrastructures. [Ngfr + Hub]
  15. The study uses virtual reality to examine how the coherence and complexity of outdoor planting designs affect users’ perceptions of time and landscape aesthetics. [Participants + Complexity]
  16. The study introduces virtual reality as a controlled experimental tool to manipulate a specific design variable—vegetation layout along a campus path—to investigate its effects on perceived coherence, complexity, and sense of time. [Participants + Complexity]

## La Nueva Perspectiva
**Propósito:** Proponer la visión o enfoque novedoso del autor
**Párrafos:** 3-4
**Ideas de la literatura:**
  1. Conversation type and self-reported arousal and valence are treated as independent variables, while EDA, PPG features, facial action units, and reported empathy factors are dependent variables. [Face + Emotional]
  2. The study compares emotional video-mediated conversations with face-to-face interactions using behavioral and physiological measures to understand their impact on emotions, empathy, and bodily responses. [Face + Emotional]
  3. The section stresses the importance of clear operational definitions of empathy for computational modeling, as different theoretical views lead to different annotation schemes and machine learning targets. [Empathy + Empathic]
  4. The authors highlight substantial conceptual ambiguity in how empathy is defined and measured in psychology versus empathy computing, noting that computational work often collapses nuanced constructs (e.g. [Empathy + Empathic]
  5. Multi-agent simulations are being used in goal-oriented and game-like contexts, including collaborative software production, autonomous exploration and learning in game worlds, and human-like NPCs for text-based strategy games. [Agents + Agent]
  6. Agent communication is probabilistically triggered by proximity and social tendencies, with conversations designed to deepen over time through dialogue memory that promotes progressively more advanced topics. [Agents + Agent]
  7. When the chatbot is only instructed to ‘get to know’ the user (acquaintance condition), personality inference accuracy is lower than in the explicit assessment condition, with weaker but often still positive and significant correlations. [Personality + Gpt]
  8. Personality inferences showed relatively small demographic biases: traits were generally underestimated across groups, with only a few significant subgroup differences in residuals and correlations. [Personality + Gpt]
  9. The multimodal fusion approach enables modest but usable real-time emotion recognition accuracy, and the conversational protocol effectively induces target emotional states. [Emotion + Multimodal]
  10. The paper’s main hypothesis is that multimodal models combining acoustic and visual information are more suitable for valence-based empathy recognition than unimodal models. [Emotion + Multimodal]
  11. The study introduces an evaluation framework and dataset for assessing empathetic responding in LLMs versus humans, which can be reused to test newer LLM versions. [Empathetic + Empathy]
  12. The performance gain of EmpathyAgent is particularly notable on tasks requiring accurate interpretation of users’ emotional states and appropriate follow-up actions. [Empathetic + Empathy]
  13. This paper positions itself as the first review specifically focused on how empathic mental health conversational agents are designed and evaluated, addressing a gap in the literature. [Empathic + Empathy]
  14. The review examines types of conversational agent (CA) designs in mental health (MH) care that are specifically engineered to convey empathy. [Empathic + Empathy]
  15. Cognitive language agents embed LLMs in a feedback loop with the environment, using multimodal inputs, intermediate reasoning, memory, and self-modification to guide actions. [Llm + Agents]
  16. The authors distinguish between basic LLM use in NLP, simple language agents, and more advanced “cognitive language agents” that use LLMs not only for action selection but also for reasoning, planning, and long-term memory management. [Llm + Agents]

## Discusión
**Propósito:** Analizar implicaciones, comparar con enfoques existentes
**Párrafos:** 3-5
**Ideas de la literatura:**
  1. The main contributions include a comparative analysis of physiological and behavioral responses across settings, identification of features that vary by emotional and conversational condition, exploration of empathy differences, and release of a new . [Face + Emotional]
  2. The study adopts a quantitative approach to measure and compare physiological and behavioral indicators in face-to-face versus remote conversations. [Face + Emotional]
  3. The paper offers a rigorous, PRISMA-aligned systematic review of empathy detection using machine learning, covering 82 studies and organizing them by task formulations and input modalities. [Empathy + Empathic]
  4. Empathy detection is conceptually distinct from emotion detection because it models relational dynamics between at least two individuals—the initial expresser and the responder whose empathic reaction is assessed. [Empathy + Empathic]
  5. Current simulation research largely emphasizes extrinsic behaviors of agents—both individual task performance and group-level social actions—often in real-world and game-like virtual environments. [Agents + Agent]
  6. This modular design is intended to support complex interactions and the emergence of human-like societal dynamics in large-scale multi-agent simulations. [Agents + Agent]
  7. Different interaction modes (assessment, acquaintance, assistant) significantly affect inference accuracy and user experience; naturalistic, reciprocal conversation styles improve user experience without sacrificing personality-prediction accuracy. [Personality + Gpt]
  8. User experience remains highly positive even when LLMs are prompted to actively seek personality-relevant information. [Personality + Gpt]
  9. Despite recent progress and diverse modeling strategies, MERC still faces major challenges, particularly data scarcity, modality alignment, and cross-lingual and cross-cultural generalization. [Emotion + Multimodal]
  10. Multimodal (audio + visual) models outperform unimodal models for valence-based empathy recognition, confirming that both acoustic and visual signals carry relevant information. [Emotion + Multimodal]
  11. The paper benchmarks existing LLMs and MLLMs on the EmpathyAgent framework to evaluate their empathetic capabilities in embodied settings. [Empathetic + Empathy]
  12. The paper introduces a large-scale between-subjects user study comparing empathy in responses from humans and four state-of-the-art LLMs (GPT-4, LLaMA-2-70B-Chat, Gemini-1.0-Pro, Mixtral-8x7B-Instruct) using 1,000 Prolific participants. [Empathetic + Empathy]
  13. This review aims to systematically map and evaluate empathic conversational agent platform designs for mental health, focusing on design characteristics, empathy-related mechanisms, and reported outcomes. [Empathic + Empathy]
  14. User acceptability of empathic conversational agents is a core evaluation dimension in this review. [Empathic + Empathy]
  15. The structural analogy between production systems and LLMs motivates using cognitive architectures to organize and extend LLM-based language agents. [Llm + Agents]
  16. The authors argue that cognitive architecture and system design for LLM agents should be deeply integrated to create a mutually reinforcing development loop. [Llm + Agents]

## Implicaciones Futuras
**Propósito:** Proyectar el impacto potencial y direcciones de investigación
**Párrafos:** 2-3
**Ideas de la literatura:**
  1. Physiological and facial responses differ systematically between face-to-face and remote emotional conversations, with remote interactions linked to more positive affect and higher HRV, and face-to-face to stronger phasic EDA responses. [Face + Emotional]
  2. Findings highlight the potential to improve remote interactions by real-time multimodal emotion detection and transmission as an additional social cue. [Face + Emotional]
  3. Empathy detection is conceptually distinct from emotion detection: while emotion detection targets a single individual’s emotional state, empathy detection analyses how one person’s emotional response relates to another’s expressed emotion within an . [Empathy + Empathic]
  4. The review reveals that ML-based empathy detection research is dominated by text-based methods, with far fewer studies using audiovisual, audio-only, or physiological signals. [Empathy + Empathic]
  5. Through the interplay of Memory and Insight, agents exhibit evolving, trait-consistent cognitive trajectories (e.g. [Agents + Agent]
  6. Evolving Agents employ a two-system architecture—Behavior System and Personality System—based on a stimulus-response concept, integrating modules for emotion, cognition, and character growth. [Agents + Agent]
  7. The paper includes standardized user-experience and demographic questionnaires to characterize participants and contextualize personality inference performance. [Personality + Gpt]
  8. LLM-based personality inference can contribute to novel insights in human behavior and psychology. [Personality + Gpt]
  9. Multimodal large language models open new possibilities for MERC (e.g. [Emotion + Multimodal]
  10. The authors identify limitations in prior FER evaluations with MLLMs (imbalanced and poorly labeled datasets) and propose using balanced, improved FER data plus temporal context and alternative encodings to more fairly assess and enhance MLLM emotion. [Emotion + Multimodal]
  11. The benchmark’s evaluation framework maps specific empathy-related dimensions to different challenges: scenario understanding, planning empathetic actions, and executing actions/dialogue. [Empathetic + Empathy]
  12. Benchmarking current models on EmpathyAgent shows that performing empathetic actions is still a significant challenge for existing systems. [Empathetic + Empathy]
  13. Prior reviews have examined efficacy and technical/intervention characteristics of mental health CAs, highlighting empathy and personalization as key facilitators of efficacy but without deeply studying how empathy is incorporated. [Empathic + Empathy]
  14. The review describes evaluation approaches that assess empathic CAs in MH care from an implementation and user-acceptability perspective. [Empathic + Empathy]
  15. Language agents use LLMs as core computation units to reason, plan, and act in diverse environments, marking an emerging direction toward more human-like intelligence. [Llm + Agents]
  16. Language agents are systems that use LLMs as a core computation unit to reason, plan, and act in the world. [Llm + Agents]

## Desafíos y Limitaciones
**Propósito:** Reconocer obstáculos y limitaciones de la perspectiva
**Párrafos:** 2-3
**Ideas de la literatura:**
  1. Type of conversation and self-reported arousal and valence are treated as independent variables, while EDA, PPG features, facial action units, and reported empathy measures serve as dependent variables. [Face + Emotional]
  2. The novel contribution of this work is creating a comparative multimodal dataset of physiological and behavioral responses during emotional conversations in both face-to-face and remote settings, to analyze empathy, response differences, and cross-se. [Face + Emotional]
  3. Evolving Agents are grounded in psychological theories and are designed to simulate believable personality traits and personalized behavioral patterns that change over time in sandbox environments. [Agents + Agent]
  4. Agents with a social awareness module autonomously specialize into diverse and persistent social roles, forming heterogeneous role structures that resemble facets of human civilizations. [Agents + Agent]
  5. Emotions are multimodal and can be recognized using combinations of physiological and behavioral signals, but it is unclear if face-to-face–trained models generalize to video-mediated conversations. [Emotion + Multimodal]
  6. Multimodal Emotion Recognition in Conversations (MERC) addresses the limitations of single-modality (especially text-only) emotion recognition for real-world dialogue systems. [Emotion + Multimodal]
  7. Human evaluation of empathic CAs is methodologically weak: few RCTs, inconsistent and poorly defined measures of empathy, limited assessment of mental health outcomes, and minimal involvement of clinicians and stakeholders. [Empathic + Empathy]
  8. The review includes 19 studies of empathic conversational agents for mental health, with most reporting both system design and human evaluations. [Empathic + Empathy]
  9. The proposed affective agent architecture relies on a memory system that stores both observations and internal emotional states, forming a chain of emotion that conditions future language-model outputs. [Emotional + Emotion]
  10. The study implements an appraisal-based Chain-of-Emotion architecture in a role-playing game agent and compares it to No-Memory and Memory baselines using a controlled breakup scenario. [Emotional + Emotion]
  11. The final VENUS annotations align textual utterances with time-synchronized 3D nonverbal expression parameters, enabling video-grounded dialogue modeling of nonverbal behavior. [Nonverbal + Venus]
  12. The paper reports that MARS, trained on VENUS, can generate natural and contextually aligned nonverbal expressions alongside text, supported by quantitative metrics, qualitative analysis, and user studies. [Nonverbal + Venus]
  13. The review followed PRISMA 2020 guidelines to systematically identify, screen, and synthesize studies on AI chatbots and executive functions. [Studies + Chatbots]
  14. The review targets studies where chatbots are used to support executive functions or related conditions such as stress, anxiety, depression, memory, attention, cognitive load, and behavioral changes. [Studies + Chatbots]
  15. For response generation, Sibyl augments the dialogue context with the four visionary commonsense inferences Kp as a bridge to the next response, and explores both finetuned and prompt-based generation strategies. [Commonsense + Dialogue]
  16. The paper evaluates Sibyl by comparing it against several state-of-the-art empathetic dialogue and commonsense reasoning baselines. [Commonsense + Dialogue]

## Conclusiones
**Propósito:** Sintetizar los puntos clave y el mensaje final
**Párrafos:** 1-2
**Ideas de la literatura:**
  1. The study systematically compares emotional video-mediated conversations with face-to-face interactions using behavioral and physiological measures to clarify how remote communication impacts emotions and empathy. [Face + Emotional]
  2. The analysis framework explicitly targets differences between interaction modalities (face-to-face vs. remote) as a core dimension of emotional and physiological response variation. [Face + Emotional]
  3. Empathy is a crucial, cross-disciplinary construct central to human communication and well-being, and is increasingly being operationalised using machine learning. [Empathy + Empathic]
  4. Empathy detection is conceptually and computationally distinct from emotion detection because it concerns how one individual responds to another’s emotional state rather than identifying a single person’s emotion. [Empathy + Empathic]
  5. The system enables believable personality evolution over time in a sandbox simulation, where agents develop new traits and behavior patterns through reflection and interaction with the environment and other agents. [Agents + Agent]
  6. The authors define three criteria for agent specialization—autonomous role selection and switching, emergent specializations from interaction (not hard-coded), and role-consistent behaviors—and claim their system satisfies these in simulation. [Agents + Agent]
  7. Inference accuracy varies systematically across interaction conditions: explicit personality assessment conversations outperform acquaintance-style and assistant-style conversations, and constrained chats often underperform unconstrained text. [Personality + Gpt]
  8. The chatbot’s prompted behavior (assessment vs acquaintance vs assistant) has a strong impact on personality inference quality, whereas user instruction type (naturalistic conversation vs unconstrained use) has little effect on accuracy. [Personality + Gpt]
  9. Emotions are multimodal and can be recognized using combined physiological and behavioral signals; prior work in face-to-face conversation shows multimodal fusion improves emotion recognition, motivating tests of whether this generalizes to video-med. [Emotion + Multimodal]
  10. Multimodal Emotion Recognition in Conversations (MERC) extends ERC by integrating multiple modalities—typically text, audio, and visual cues—to capture subtle emotional states more effectively. [Emotion + Multimodal]


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
