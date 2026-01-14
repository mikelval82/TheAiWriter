# Empathy Detection from Text, Audiovisual, Audio or Physiological Signals: A Systematic Review of Task Formulations and Machine Learning Methods

## Metadata
- **Autores**: Md Rakibul Hasan, Md Zakir Hossain, Shreya Ghosh, Aneesh Krishna, Tom Gedeon
- **Año**: 2025
- **Keywords**: Empathy, Empathy Computing, Deep Learning, Machine Learning, Pattern Recognition, Systematic Review

## Abstract
Revisión sistemática de 82 trabajos (2013–mayo 2025) sobre detección de empatía con aprendizaje automático en cuatro modalidades: texto, audiovisual, audio y señales fisiológicas. A partir de 849 registros en 10 bases de datos (cribado con criterios PRISMA), el estudio organiza las formulaciones de tarea (monádica, diádica y grupal) y variantes (medición localizada y global; empatía unidireccional, paralela y bidireccional; contagio emocional). Resume 45 datasets (25 públicos), tendencias metodológicas por modalidad y arquitecturas, así como la disponibilidad de código. Identifica retos: escasez de benchmarking fuera de texto, definiciones y anotaciones heterogéneas (auto vs terceros), poca estandarización de métricas, y baja disponibilidad de datos/código. Señala oportunidades en empatía paralela/bidireccional y señales fisiológicas, y el potencial de LLMs y enfoques multimodales para mejorar la detección de empatía.

## Contribuciones Principales
- Sistematización de las formulaciones de tareas en computación de la empatía
- Análisis comparativo de 45 datasets, incluyendo composición y acceso
- Revisión de enfoques de modelado, modelos usados y disponibilidad de código
- Identificación de métodos de alto rendimiento aplicados a benchmarks
- Síntesis de dominios de aplicación de la detección de empatía
- Discusión de desafíos clave y oportunidades abiertas en tareas y modelado

## Metodología
Búsqueda sistemática (24 feb 2023, actualizada a jun 2024 y mayo 2025) en 10 bases (Scopus, Web of Science, IEEE Xplore, ACM, ScienceDirect, dblp, Google Scholar, PubMed, ProQuest, ACL Anthology) con la cadena: empath* AND (detect* OR recog*) AND ("deep learning" OR "machine learning" OR "artificial intelligence" OR AI). Inclusión: detección de empatía con ML/DL/IA; artículo completo revisado por pares; 2013–2025. Exclusión: no artículo completo; sin IA/ML; revisión/tesis; no inglés. De 849 registros, tras deduplicación y cribado por título/resumen y texto completo (con Covidence y consenso de autores), se incluyeron 82 estudios. Se aplicaron aspectos relevantes de PRISMA 2020 y se añadieron trabajos mediante alertas y snowballing. Se clasificaron tareas por: tipo de interacción (monádica, diádica, grupal), granularidad (localizada vs global), dirección (unidireccional, paralela, bidireccional) y contagio emocional; y métodos por modalidad (texto, audiovisual, audio, fisiología). Se extrajeron estadísticas de conjuntos de datos, protocolos de anotación (auto vs terceros), acceso público, modelos y métricas; y se sintetizaron hallazgos, desafíos y aplicaciones.

## Resultados Clave
- Distribución por modalidad: 57 estudios de texto, 15 audiovisuales, 7 de audio y 3 de señales fisiológicas
- Tareas identificadas: monádicas (p. ej., MedicalCare/LeadEmpathy/SpeechEmpathy), diádicas (unidireccional, paralela y bidireccional; p. ej., iEmpathize, MultimodalMI, MEDIC, NewsConvT/NewsConvD, EmpathicStories), contagio emocional (OMG-Empathy, EEG, PainEmp, PathogenicEmp) y una interacción grupal (Teacher-Student)
- Datasets: 45 en total; 25 públicos; WASSA (NewsEssay v1–v4, NewsConvT/NewsConvD) centraliza benchmarks textuales
- Texto (regresión): RoBERTa/DeBERTa dominan; en NewsEssay v2 PCC≈0.47–0.56; en v3 hasta 0.563 con LLM-GEm (GPT‑3.5 + RoBERTa); en NewsConvT mejores resultados (hasta 0.708 con DeBERTa), posiblemente por anotación de terceros y mayor tamaño
- Texto (clasificación): EPITOME (RoBERTa; Acc máx≈95.3% pero F1 menor) e iEmpathize (BERT/RoBERTa competitivos); enfoques explicables (Micromodels + EBM) muestran que los sistemas actuales usan rasgos superficiales más que contexto
- Audiovisual (regresión): OMG-Empathy baseline VGG16‑LSTM‑SVM (CCC 0.17 personal., 0.23 general.); participantes no superan baseline; alternativas multimodales (GRU/LSTM/CNN) y WANN (val CCC 0.25)
- Audiovisual (clasificación): fusiones multimodales (texto BERT + visión ResNet + audio OpenSMILE/MFCC) mejoran sobre unimodal; texto suele contribuir más que audio/visión en DAIC‑WOZ
- Audio: pipelines con diarización + ASR; texto > acústico en COPE; MultimodalMI muestra ventajas de fusión tardía (HuBERT + RoBERTa + BiGRU)
- Fisiología: enfoques clásicos (LR/SVM/DT) sobre EEG/ECG/GSR/fMRI; mejor predicción de empatía basal (antes) que durante/después en EEG
- Anotación: 13 datasets con autoevaluación vs 30 con terceros; evidencia mixta (NewsConvT > NewsEssay v3 en rendimiento sugiere mayor consistencia con terceros), necesidad de estrategias de consenso (ensemble) y estudios controlados
- Benchmarking y reproducibilidad: escasa reutilización de datasets en audio/fisiología y baja liberación de código (texto 29/77; audiovisual 7/17; audio 2/7; fisiología 0/4); métricas heterogéneas dificultan comparabilidad
- Tendencias: fuerte sesgo hacia texto; se vislumbra potencial de LLMs (GPT‑3.5/4o, Llama‑3) y LLMs multimodales para interacción real

## Limitaciones
- Heterogeneidad en definiciones operativas de "empatía" y en esquemas de anotación (auto vs terceros, binario vs continuo)
- Baja disponibilidad pública de datos (20/45 privados) y de código (especialmente en audio/fisiología), limitando benchmarking y replicabilidad
- Métricas no estandarizadas entre estudios (PCC, CCC, MSE, Acc, F1, AUC, etc.), dificultando comparaciones
- Poca evidencia en modalidades no textuales y en configuraciones de grupo, empatía paralela/bidireccional
- Tamaños muestrales reducidos y escenarios controlados (p. ej., OMG‑Empathy, EEG) que limitan generalización
- Riesgos de sesgo cultural y demográfico en datos y modelos
- Limitaciones de la propia revisión: posibles omisiones por cobertura de bases y ambigüedad en algunos registros

## Trabajo Futuro
- Explorar empatía paralela y bidireccional, especialmente en contextos de grupo y medición global
- Diseñar estudios comparativos rigurosos entre autoanotación y anotadores terceros (incluyendo ensembles e inter‑rater reliability)
- Ampliar datasets públicos, multimodales y naturalistas; estandarizar métricas y protocolos de evaluación
- Impulsar detección multimodal (texto+audio+visión) y análisis de contribución por modalidad
- Investigar señales fisiológicas adicionales (pupilometría, BVP) y su combinación con audio/visión/texto
- Evaluar "empatía desde el observador" mediante señales fisiológicas de terceros que observan la interacción
- Desarrollar y adaptar LLMs/multi‑LLMs para empatía en escenarios conversacionales audiovisuales, con enfoques de few‑shot y calibración
- Estudiar equidad, robustez ante empatía fingida y generalización intercultural

## Citas Relevantes
- "Empathy is defined as ‘an affective response more appropriate to another’s situation than one’s own’."
- "The two most related terms are empathy and sympathy, which can be described as ‘feeling as’ versus ‘feeling for’."
- "In other words, cognitive empathy is ‘I understand what you feel’, whereas emotional empathy is ‘I feel what you feel’."
- "The overarching objective of this study is to systematically review all ML-based empathy detection works published between 2013 and May 2025."
- "Empathy detection differs from emotion detection... Emotion detection focuses on recognising an individual’s emotional state... In contrast, empathy detection goes into a deeper analysis of the interactions between multiple individuals."

## Notas Adicionales
La revisión mapea jerárquicamente las formulaciones de tarea (monádica, diádica, grupal; localizada vs global; unidireccional, paralela, bidireccional; contagio emocional) y alinea datasets representativos (p. ej., NewsEssay v1–v4, NewsConvT/NewsConvD, iEmpathize, MEDIC, MultimodalMI, OMG‑Empathy, EEG). WASSA ha catalizado benchmarks textuales y la adopción de transformers (RoBERTa/DeBERTa), con mejoras recientes mediante LLMs (LLM‑GEm, role‑play prompts, razonamiento contrastivo). Se observa mejor desempeño con anotación de terceros en conversaciones (NewsConvT) que con autoevaluación en ensayos (NewsEssay v3/v4). En audiovisual, el baseline de OMG‑Empathy no ha sido superado consistentemente; el texto suele aportar más que audio/visión, aunque la fusión multimodal es prometedora. En audio, pipelines ASR+NLP y fusión tardía destacan; en fisiología prevalece ML clásico con señales EEG/ECG/GSR/fMRI. El paper incluye checklist PRISMA, estadísticas de acceso de datos/código y recomendaciones para estandarización, equidad y despliegues éticos.
