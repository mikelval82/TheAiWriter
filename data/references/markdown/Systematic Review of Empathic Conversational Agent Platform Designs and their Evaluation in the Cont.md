# Empathic Conversational Agent Platform Designs and Their Evaluation in the Context of Mental Health: Systematic Review

## Metadata
- **Autores**: Ruvini Sanjeewa, Ravi Iyer, Pragalathan Apputhurai, Nilmini Wickramasinghe, Denny Meyer
- **Año**: 2024
- **Keywords**: agentes conversacionales, chatbots, asistentes virtuales, empatía, conciencia emocional, salud mental, bienestar mental

## Abstract
La revisión aborda la brecha entre la demanda y la oferta de servicios de salud mental y evalúa el potencial de los agentes conversacionales (AC) con IA para mitigarlo. Su objetivo fue identificar arquitecturas de AC empáticos en salud mental, valorar su desempeño técnico en la detección y respuesta a emociones (precisión de clasificación) y describir enfoques de evaluación de su aceptabilidad. Se realizó una búsqueda sistemática (2010-2023) en seis bases de datos. De 19 estudios incluidos, el 63% fueron de base ML, 26% híbridos y 11% basados en reglas; 37% emplearon transformadores. Los motores híbridos lograron mayor precisión y respuestas más matizadas. El 84% incluyó evaluación humana, pero solo el 26% midió explícitamente la empatía (principalmente autoinformes). Se concluye que integrar diseño y evaluación es crucial, urge usar definiciones claras y escalas estandarizadas de empatía (idealmente con evaluación experta), y homogeneizar métricas técnicas. Existen AC con buen desempeño técnico y empático, con potencial para aplicaciones como líneas de ayuda.

## Contribuciones Principales
- Primera síntesis específica de diseños de AC empáticos en salud mental, sus arquitecturas y desempeño técnico.
- Comparación de motores (ML, híbridos, basados en reglas) destacando la superioridad de los híbridos en precisión y matiz de respuesta.
- Mapeo de métodos de evaluación humana, mostrando predominio de autoinformes, escasa definición operativa de empatía y poca participación de expertos.
- Identificación de la heterogeneidad de métricas técnicas y de empatía como barrera a la comparación entre estudios.
- Propuestas concretas para estandarizar definiciones y medidas de empatía y para integrar señales vocales además de texto.

## Metodología
Revisión sistemática siguiendo PRISMA. Búsqueda en 6 bases (Web of Science, Scopus, EBSCOhost: Academic Search Complete, CINAHL Complete, Computers and Applied Sciences Complete, IEEE Xplore) entre 01/01/2010 y 30/09/2023. Estrategia con términos y sinónimos relacionados con 'conversational agents', 'mental health' y 'empathy' (incluyendo comodines y MeSH). Criterios de inclusión: intervenciones de AC en salud mental con entradas textuales o vocales, descripción de diseño/metodología, datos y participantes. Exclusiones: revisiones, metaanálisis, entradas multimodales no textuales/vocales (p.ej., reconocimiento facial), artículos sin metodología clara. Proceso: eliminación de duplicados (EndNote), cribado de títulos/resúmenes por un autor, cribado a texto completo por tres autores con resolución por consenso. Extracción de datos sobre diseños, evaluación de empatía y arquitecturas. Calidad: herramienta JBI para múltiples diseños; sesgo: RoB 2 para ECA y ROBINS-I para no aleatorizados.

## Resultados Clave
- Se incluyeron 19 estudios; países predominantes: EE. UU. (6) e India (6); fuerte aumento de publicaciones desde 2022.
- Diseños: 63% ML, 26% híbridos, 11% basados en reglas; 37% con arquitecturas transformer (p.ej., BERT, GPT‑2); 16% ML no especificado; 89% texto, 11% voz+texto.
- Desempeño técnico: buenos resultados generales; transformadores y, sobre todo, modelos híbridos obtuvieron mayor precisión y respuestas más matizadas. Ejemplos: clasificador de empatía con W-ACC=0.977 y macro F1=0.972 [36]; clasificador temático con accuracy=95%, precision=0.954, recall=0.947, F1=0.95 [33]; EMMA valencia/arousal (clasificación) 80.4%/50.4% y (predicción) 82.2%/65.7% [24].
- Evaluación humana: 84% (16/19) realizaron evaluación con usuarios; solo 26% (5/19) evaluaron explícitamente la empatía; todas las medidas de empatía fueron autoinformes (escalas, ratings o entrevistas); solo 1 estudio combinó valoración de usuarios y expertos. Hallazgos: mayor interacción con el AC empático EMMA vs control [24]; evaluaciones de empatía del 70–79% en Vhope/otros [28,34]; estudios cualitativos con Replika describen empatía cognitiva/afectiva.
- Riesgo de sesgo: ECA con bajo riesgo; no aleatorizados con riesgo moderado–alto. Calidad JBI moderada cuando se evaluó diseño+implementación; baja cuando solo se describió el diseño.
- Definición de empatía: solo 26% (5/19) la especificaron (p.ej., Rogers; Barrett‑Lennard).

## Limitaciones
- Alta heterogeneidad de diseños, métricas técnicas y medidas de empatía, dificultando comparaciones y síntesis cuantitativa.
- Escasez de definiciones operativas y escalas estandarizadas de empatía; predominio de autoinformes subjetivos.
- Poca inclusión de voces de expertos clínicos y de evaluaciones longitudinales/ECAs.
- Modalidad de entrada predominantemente textual; mínima integración de señales vocales pese a su relevancia para la empatía.
- Calidad metodológica variable y reporte incompleto de diseño/implementación en varios estudios.

## Trabajo Futuro
- Adoptar definiciones claras y consensuadas de empatía y emplear escalas estandarizadas, incorporando evaluación de expertos.
- Estandarizar métricas de evaluación técnica (clasificación/predicción/generación) para permitir comparaciones entre AC.
- Diseñar e implementar arquitecturas híbridas que separen detección afectiva de la generación/selección de respuestas.
- Integrar características vocales junto a texto para mejorar detección y expresión de empatía (p.ej., aplicaciones en líneas de ayuda, triaje).
- Realizar ECA y estudios longitudinales para evaluar efectos sostenidos en síntomas y bienestar.
- Mitigar sesgos de LLM/ML (datos diversos y técnicas de debiasing) y fortalecer salvaguardas éticas y de privacidad.
- Impulsar co-diseño y co-evaluación con usuarios, clínicos y decisores, con ciclos iterativos de mejora.

## Citas Relevantes
- "The integration of CA design and its evaluation is crucial to produce empathic CAs."
- "Future studies should focus on using a clear definition of empathy and standardized scales for empathy measurement, ideally including expert assessment."
- "Hybrid architecture seems best suited to the detection of user emotion followed by the retrieval of a suitable response."
- "This review suggests that a hybrid design is ideally used for the design of an empathic CA, allowing an initial assessment of user emotion before any CA response is developed."
- "However, the incorporation of this crucial empathy component within CAs has not been studied in any depth within the MH sector."

## Notas Adicionales
• Periodo de búsqueda: 2010–2023; guía PRISMA; financiación: Swinburne University of Technology. • Solo 2/19 estudios usaron voz; 17/19 exclusivamente texto. • Tipos de estudio: 47% transversales, 26% ECA, 21% cuasi-experimentales, 5% cualitativos. • Participación geográfica diversa; aumento de publicaciones tras 2022. • Ejemplos de AC: EMMA, Wysa, Replika, VHope, Koko, Saarthi, etc. • Riesgos y consideraciones: posibles sesgos en LLM, privacidad/ética y latencia; necesidad de métricas y guías de evaluación comunes.
