# A Survey on Identifying Empathic Expression in Remote Collaboration From Empathic Computing

## Metadata
- **Autores**: Prabesh Paudel, Hyung-Jeong Yang, Anjitha Divakaran, Seung-Won Kim, Ji-Eun Shin, Soo Hyung Kim
- **Año**: 2024
- **Keywords**: Empathy, empathic computing, empathic response and expression, empathic intelligence

## Abstract
El artículo ofrece una revisión exhaustiva sobre la empatía y su relación con la computación empática, con énfasis en cómo identificar y medir la empatía entre colaboradores remotos. Analiza definiciones y componentes de la empatía (cognitiva, afectiva/emocional y compasiva), el papel de la inteligencia emocional en interfaces y sistemas, y técnicas recientes en realidad virtual/aumentada y seguimiento ocular para capturar respuestas empáticas. Presenta marcos prototipo para medir empatía mediante biomarcadores (frecuencia cardiaca, presión arterial), rasgos faciales y gaze, y sintetiza avances y desafíos en campos como salud, servicio al cliente y computación social. Concluye destacando la necesidad de estandarizar métodos, atender preocupaciones éticas y promover el desarrollo responsable de IA empática para colaboración remota.

## Contribuciones Principales
- Revisión sistemática de métodos y sistemas de computación empática aplicados a colaboración remota.
- Síntesis de definiciones y componentes de la empatía (cognitiva, afectiva/emocional, compasiva) y su relación con la inteligencia emocional.
- Análisis comparativo de enfoques multimodales (voz, rostro, gaze, biosensores) y de interfaces (VR/AR/MR) para detectar y expresar empatía.
- Propuesta de marcos prototipo para medir empatía en escenarios remotos mediante seguimiento ocular, landmarks faciales y señales fisiológicas.
- Identificación de áreas de aplicación con mayor progreso (salud, servicio al cliente, computación social) y discusión de consideraciones éticas y de estandarización.

## Metodología
La revisión se realizó en dos fases: (1) planificación (definición del foco en empatía y computación empática en colaboración remota) y (2) búsqueda/selección. Se consultaron Google Scholar e IEEE Xplore utilizando términos como "empathy", "empathic computing", "artificial intelligence", "virtual empathy", "emotion recognition", "empathic dialogue generation", "empathy measurement", "gaze tracking", "virtual reality", "remote collaboration". Se recopilaron 256 artículos; 185 se consideraron base, se excluyeron 40 tras lectura detallada y 114 se recuperaron íntegramente. Por falta de contenido directamente relacionado con empatía en colaboración remota, se redujo a 85 elegibles; finalmente, 57 se usaron como referencias. La gestión bibliográfica se realizó con Zotero. Se categorizó la literatura por modalidades: empatía artificial; interacción humano–IA; inteligencia emocional; evolución del comportamiento humano; diálogos empáticos. Además de la síntesis narrativa, el trabajo integra: (a) marcos conceptuales para medir empatía con gaze y features faciales; (b) tabulación de técnicas de generación y detección empática (modelos ML/NLP, datasets multimodales); (c) análisis de aplicaciones en VR/AR/MR y de bioseñales (EEG, ECG, PPG, GSR) para reconocimiento emocional/empático.

## Resultados Clave
- Consolidación de la taxonomía de empatía: empatía afectiva (sentir con el otro), cognitiva (tomar perspectiva) y compasiva (preocupación y ayuda), destacando su interconexión y relevancia para estándares futuros.
- Evidencia de viabilidad de medir respuestas empáticas en remoto mediante: seguimiento ocular (fijaciones, dilatación pupilar), landmarks faciales, audio, y biosensores (EEG, ECG/PPG, GSR), integrados con ML para valencia/arousal.
- Validación del valor de VR/AR/MR para compartir contexto afectivo, mejorar la co-presencia y habilitar señales no verbales (gaze compartido, avatares expresivos) en colaboración remota.
- Identificación de datasets y pipelines multimodales (e.g., bases de emociones con sincronía de video, audio y gaze; corpora de diálogos empáticos) que permiten entrenamiento y evaluación de modelos.
- Hallazgos sobre gaze y empatía: métricas oculométricas (tiempo de fijación, movimientos pupilares) correlacionan con estados emocionales y niveles de empatía hacia contenido digital.
- Avances en NLP para diálogo empático (transformers, reconocimiento de causa de emoción, intents human-like) con mejoras en adecuación y sensibilidad emocional.
- Prototipos propuestos: (i) medición de empatía por landmarks faciales + clasificación de valencia/arousal; (ii) framework de colaboración remota con registro simultáneo de gaze y biosignales para estimar sincronía/expresión empática.
- Áreas con mayor progreso aplicativo: salud (clínica y relación médico–paciente), servicio al cliente y computación social.
- Identificación de retos: ausencia de estandarización de constructos/métricas, complejidad de la subjetividad emocional, y brecha entre simulación y vivencia auténtica en máquinas.

## Limitaciones
- El paper no incluye una sección de limitaciones explícita; las siguientes son inferidas.
- Enfoque principalmente narrativo; sin meta-análisis cuantitativo ni evaluación estandarizada de calidad de estudios.
- Cobertura final restringida (85 elegibles; 57 citados), con escasez de trabajos específicamente centrados en empatía en colaboración remota.
- Falta de validación empírica de los marcos prototipo propuestos (no se reportan experimentos propios con métricas de desempeño).
- Dependencia de figuras/tablas referenciadas (p. ej., métricas y tablas de técnicas) sin detalles completos en el texto.
- Ambigüedades terminológicas persistentes (p. ej., solapamiento entre afectiva/emocional vs. compasiva) y carencia de estándares consensuados.

## Trabajo Futuro
- Uso de conjuntos de datos más grandes y diversos, incluyendo señales multimodales sincronizadas.
- Desarrollo/adopción de algoritmos de clasificación de empatía y modelos que integren componentes cognitivos, afectivos y compasivos.
- Integración de modelos emocionales alternativos (p. ej., dimensionales y discretos) y técnicas de aprendizaje multimodal explicable.
- Diseño de guías y mecanismos de intervención (más allá de generación de texto) para respuestas empáticas en sistemas interactivos.
- Estandarización de métricas y protocolos para evaluación de empatía en escenarios remotos.
- Profundizar aplicaciones en salud, servicio al cliente y computación social, y explorar educación y bienestar.
- Abordar ética, privacidad y mitigación de sesgos demográficos/culturales en datos y modelos.

## Citas Relevantes
- "Our primary focus is to investigate methods for measuring empathy between two remote collaborators."
- "Empathy transcends mere recognition and understanding of someone else’s emotions; it entails actively sharing in those feelings."
- "Empathic computing emerges as a novel approach to express empathy through various forms, wherein non-human entities compute and respond in a human-like manner."
- "We present a framework, which shows how an eye tracking can be beneficial in computing empathy."
- "Ultimately, the question of whether a machine can truly feel empathic towards human intelligence remains open-ended."
- "The key takeaway is that the progress of machines in understanding human emotions can greatly benefit healthcare, education, and other areas that depend on human connection."

## Notas Adicionales
Artículo de revisión publicado en IEEE Access (DOI: 10.1109/ACCESS.2024.3430951), con licencia CC BY-NC-ND 4.0. Presenta definiciones y marcos visuales (Fig. 3–7) y tablas de aplicaciones, técnicas de detección y modelos empáticos. El trabajo subraya el rol de la inteligencia emocional (modelo de Goleman) y de interfaces (GUI/TUI) en HCI. Propone medir empatía con gaze, landmarks faciales y biosensores (EEG, ECG/PPG, GSR), y explora VR/AR/MR para co-presencia empática. Incluye discusión ética (privacidad, responsabilidad moral, sesgos, salud mental). La redacción contiene algunos errores tipográficos y expresiones no estandarizadas (p. ej., "EER" para señales fisiológicas), pero no afectan el mensaje central.
