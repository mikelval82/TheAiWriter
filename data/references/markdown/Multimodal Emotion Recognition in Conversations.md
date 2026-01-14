# Multimodal Emotion Recognition in Conversations: A Survey of Methods, Trends, Challenges and Prospects

## Metadata
- **Autores**: Chengyan Wu, Yiqiang Cai, Yang Liu, Pengxu Zhu, Yun Xue, Ziwei Gong, Julia Hirschberg, Bolei Ma
- **Año**: 2025
- **Keywords**: Multimodal Emotion Recognition in Conversations, MERC, Emotion Recognition in Conversation, multimodal, diálogo, texto, audio, visión, fusión multimodal, grafos, GNN, hipergráficos, Fourier GNN, Transformers, LLM, MLLM, instruction tuning, datasets, evaluación

## Abstract
El artículo presenta una revisión sistemática de la tarea de Reconocimiento de Emociones Multimodal en Conversaciones (MERC), motivada por la necesidad de integrar texto, audio y señales visuales para captar matices emocionales que una sola modalidad no puede ofrecer. Describe la definición de la tarea, la metodología de revisión, los conjuntos de datos y métricas de evaluación más usados, y un panorama de técnicas de preprocesamiento (extracción de características y modelado de contexto a nivel de situación y de hablante). Propone una taxonomía de métodos recientes: basados en grafos (tradicionales, hipergráficos y con operadores en el dominio de Fourier), de fusión (pesos iguales vs. texto como modalidad dominante) y generativos (basados en LLM/MLLM con prompt engineering, instruction tuning, adaptadores ligeros). La revisión identifica tendencias (creciente diversidad lingüística y modal, auge de MLLMs) y retos clave (alineación intermodal, modalidades ausentes/ruidosas, conflictos entre modalidades, selección de modalidades, eficiencia de ajuste fino y cumplimiento FAIR). Concluye con perspectivas y oportunidades de investigación futura para sistemas MERC más robustos, inclusivos y aplicables en entornos reales.

## Contribuciones Principales
- Compilación de avances recientes en MERC, integrando datasets, tareas y metodologías.
- Comparación y síntesis de enfoques MERC, con análisis de fortalezas y limitaciones de métodos representativos.
- Identificación de desafíos abiertos y propuestas de direcciones futuras para guiar investigaciones y aplicaciones en MERC.

## Metodología
La revisión se realizó mediante búsquedas en ACL Anthology, Google Scholar y motores de búsqueda generales, focalizando en conferencias principales (EMNLP, ACL, NAACL y talleres afines). Criterios de selección: trabajos directamente relevantes a MERC que usen ≥2 modalidades (texto, audio, visión), incluyan contexto conversacional y evalúen en benchmarks (p. ej., IEMOCAP, MELD, CMU-MOSEI). Se priorizaron artículos desde 2020 para reflejar el estado del arte, incorporando trabajos fundacionales cuando aportaban contexto histórico. La selección se basó en el análisis del resumen, introducción, conclusiones y limitaciones de cada paper.

## Resultados Clave
- Definición formal de MERC: predicción de la emoción por enunciado en diálogos multimodales, integrando representaciones textuales, acústicas y visuales con modelado de contexto situacional y de hablante.
- Datasets y cobertura lingüística: consolidación de recursos en inglés (IEMOCAP, MELD, CMU-MOSEI, AVEC, EmoryNLP, MEmoR) y expansión a idiomas no ingleses (M-MELD en fr, es, el, pl; M3ED en zh; ACE en akan), con fuentes que abarcan TV, videos y cine.
- Métricas de evaluación: uso combinado de Accuracy, Weighted-F1, Macro-F1 y Micro-F1, más análisis por emoción para granularidad fina.
- Preprocesamiento multimodal: catálogo de extractores por modalidad (p. ej., RoBERTa/sBERT para texto; openSMILE/librosa para audio; OpenFace/3D-CNN para visión) y estrategias de modelado contextual (secuencial y por hablante, incluyendo embeddings de hablante y GNNs).
- Taxonomía metodológica:
  - Métodos basados en grafos: GNNs tradicionales (DialogueGCN, MMGCN, módulos de atención cruzada), hipergráficos para relaciones de orden superior y manejo de modalidades incompletas, y Fourier GNNs para señales emocionales de alta/baja frecuencia con aprendizaje contrastivo.
  - Métodos de fusión: esquemas de pesos iguales (Transformers con restricciones locales, memoria contextual, distilación) vs. esquemas texto-dominante con atención cruzada, extracción jerárquica de indicios emocionales y destilación asimétrica.
  - Métodos generativos: LLM/MLLM con instruction tuning y recuperación contextual (InstructERC, CKERC/LaERC-S), integración multimodal y señales conductuales (BeMERC, DialogueLLM), y adaptadores ligeros sobre LLMs congelados (MSE-Adapter, SpeechCueLLM) para eficiencia computacional.
- Tendencias: auge de MLLMs en ERC, creciente atención a datos multilingües y de bajos recursos, y diseños que equilibran complementariedad/consistencia intermodal con robustez ante modalidades ruidosas o ausentes.
- Desafíos sistematizados: cumplimiento FAIR en datos, alineación y conflictos entre modalidades, asincronía temporal multimodal, selección de modalidades, y ajuste fino eficiente de MLLMs en contextos multilingües y multiculturales.
- Aplicaciones: HCI, salud, educación y colaboración virtual; estudios sobre condiciones realistas (oclusiones faciales, métodos no intrusivos) para robustez en el despliegue.

## Limitaciones
- Cobertura técnica a nivel alto de métodos representativos, con menor detalle de enfoques previos a 2020 por énfasis en tendencias recientes.
- Revisión predominantemente basada en publicaciones en inglés de conferencias principales y arXiv, pudiendo subrepresentar aportes de otras regiones/idiomas/dominios.
- La comparación de benchmarks no es exhaustiva; se remite a encuestas complementarias para mayor profundidad.
- La enumeración de retos y direcciones futuras no pretende ser exhaustiva; busca estimular investigación adicional.

## Trabajo Futuro
- Mejorar el cumplimiento FAIR en datasets MERC: metadatos ricos, identificadores persistentes, accesibilidad y esquemas de etiquetas interoperables.
- Construcción y anotación de corpus multimodales multilingües y multiculturales, con estrategias de bajo costo (transfer, zero-/few-shot) y control de sesgos culturales.
- Alineación y sincronización temporal robusta entre modalidades con diferentes escalas y asincronías; modelado de dependencias de largo alcance.
- Manejo explícito de modalidades ruidosas/ausentes y resolución de conflictos intermodales, incorporando incertidumbre y aprendizaje contrastivo/mutuo.
- Selección/adaptación dinámica de modalidades según contexto y tarea, con criterios de contribución y coste-beneficio.
- Ajuste fino y adaptación eficiente de MLLMs para ERC en entornos de bajos recursos y multilingües, preservando matices culturales.
- Evaluaciones más realistas y orientadas a despliegue (latencia, robustez a oclusiones/ruido, generalización cross-dominio) en HCI, salud y educación.
- Integrar señales adicionales (p. ej., fisiológicas) y razonamiento explícito sobre estados/teoría de la mente para mejorar interpretabilidad.

## Citas Relevantes
- "This survey offers a systematic overview of MERC, including its motivations, core tasks, representative methods, and evaluation strategies."
- "Despite growing interest, the MERC task remains underexplored."
- "Dialogues can be naturally interpreted as graph structures due to the intrinsic correlations and dependencies among utterances."
- "The FAIR principles provide guidelines for improving the Findability, Accessibility, Interoperability, and Reusability of digital assets (Wilkinson et al., 2016)."
- "MERC seeks to understand emotions by integrating various modalities in to dialogue of linguistic, acoustic, visual signals, and beyond."
- "We identify key open issues in the MERC domain and put forward several potential future research directions."

## Notas Adicionales
El trabajo estructura el panorama MERC desde la definición formal y el preprocesamiento (extracción por modalidad y modelado contextual con embeddings de hablante y grafos) hasta una taxonomía de métodos: grafos (tradicionales, hipergráficos, Fourier), fusión (pesos iguales vs. texto-dominante) y generación (LLM/MLLM con retrieval, instruction tuning, módulos ligeros). Recolecta métricas estándar (Accuracy, Weighted-/Macro-/Micro-F1) y detalla datasets (incluye apéndice con IEMOCAP, MELD, CMU-MOSEI, M3ED, ACE, etc.). Destaca retos de alineación intermodal, asincronía temporal, modalidades ausentes/ruidosas y conflictos, así como el énfasis en eficiencia y adaptación de MLLMs. Incluye reconocimiento del uso de ChatGPT para revisión gramatical y apoyos de financiación. Año de preprint: 2025 (arXiv v1, 26 May 2025).
