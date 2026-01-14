# Empathic Conversational Agent Platform Designs and Their Evaluation in the Context of Mental Health: Systematic Review

## Metadata
- **Autores**: Ruvini Sanjeewa, Ravi Iyer, Pragalathan Apputhurai, Nilmini Wickramasinghe, Denny Meyer
- **Año**: 2024
- **Keywords**: conversational agents, chatbots, virtual assistants, empathy, emotionally aware, mental health, mental well-being

## Abstract
Ante el déficit de oferta en servicios de salud mental y los avances en IA, esta revisión sistemática identifica y evalúa arquitecturas de agentes conversacionales (AC) diseñados para transmitir empatía en salud mental. Se analizaron su desempeño técnico (detección, clasificación y respuesta a emociones) y su aceptabilidad mediante evaluaciones humanas. De 19 estudios incluidos (2010-2023), el 63% empleó aprendizaje automático (47% redes neuronales; 37% transformadores), 26% motores híbridos y 11% sistemas basados en reglas. Los híbridos lograron mayor exactitud y respuestas más matizadas. El 84% realizó evaluaciones humanas, pero solo el 26% midió directamente la empatía y generalmente mediante autoinformes; solo un estudio combinó valoraciones de usuarios y expertos. Se destaca la necesidad de definiciones claras de empatía, escalas estandarizadas y mayor homogeneidad en métricas técnicas para facilitar comparaciones. Existen AC con buen rendimiento técnico y empático con potencial para aplicaciones como líneas de ayuda.

## Contribuciones Principales
- Primera revisión que centra su análisis en cómo se diseña y evalúa la empatía en AC para salud mental.
- Mapeo exhaustivo de arquitecturas: ML (63%), híbridas (26%) y basadas en reglas (11%); fuerte presencia de transformadores/LLM (37%).
- Síntesis de métricas técnicas para detección, clasificación, predicción emocional y generación de respuestas; evidencia de superioridad de modelos híbridos en exactitud y matización.
- Análisis crítico de evaluaciones humanas: predominio de autoinformes, poca estandarización y escasa participación de expertos.
- Identificación de vacíos: falta de definiciones operativas de empatía, heterogeneidad de medidas, mínima incorporación de voz, consideraciones éticas y de sesgo en LLM.
- Propuestas concretas: uso de escalas estandarizadas, diseños RCT, co-diseño con usuarios y expertos, integración de rasgos vocales y protocolos de IA responsable.

## Metodología
Revisión sistemática (PRISMA) de artículos de revistas y actas de congreso en 6 bases (Web of Science, Scopus, EBSCOhost: Academic Search Complete, CINAHL Complete, Computers and Applied Sciences Complete, IEEE Xplore) entre 01/01/2010 y 30/09/2023. Estrategia de búsqueda con términos y sinónimos de tres ejes: "conversational agents", "mental health" y "empathy", con operadores booleanos, comodines (empath*), y MeSH cuando aplicó. Criterios de inclusión: intervenciones de AC en salud mental, entradas textuales y/o vocales, mención de empatía/emoción (p.ej., inteligencia/emocionalidad/conciencia emocional, compasión) y descripción metodológica del diseño (arquitectura, datos, participantes). Exclusiones: revisiones (sistemáticas, de alcance, meta-análisis) y entradas de datos no textuales/vocales (p.ej., reconocimiento facial). Detección de duplicados en EndNote 20; cribado de títulos/resúmenes por la autora principal y lectura a texto completo por tres autores de forma independiente con resolución por consenso. Extracción de datos sobre diseño técnico, evaluación de empatía y medidas de desempeño. Evaluación de calidad: herramienta JBI para diversos diseños. Riesgo de sesgo: RoB 2 (ensayos aleatorizados) y ROBINS-I (no aleatorizados).

## Resultados Clave
- Se incluyeron 19 estudios: 47% transversales, 26% RCT, 21% cuasi-experimentales, 5% cualitativo; procedencia: EE. UU. (32%), India (32%) y otros (36%).
- Modalidad de interacción: 89% texto; 11% texto+voz.
- Arquitecturas: 63% ML; 26% híbridas; 11% basadas en reglas. Dentro de ML: 47% redes neuronales; 37% transformadores (BERT, SBERT, RoBERTa, GPT-2, seq2seq); 16% no especificadas.
- Desempeño técnico (ejemplos):
  - Clasificación empática (transformador con tres clasificadores): W-ACC=0.977; Macro F1=0.972.
  - Clasificador temático (GPT-2 controlado): exactitud=95%; precisión=0.954; recall=0.947; F1=0.95.
  - Híbridos: mayores exactitudes y respuestas más matizadas en tareas de reconocimiento y generación (p.ej., recomendación de recursos F1=0.87; reconocimiento emocional hasta ~95%).
  - EMMA (híbrido): valencia 80.4–82.2%; activación 50.4–65.7%.
- Evaluación humana: 84% (16/19) realizaron evaluación con usuarios; solo 26% (5/19) midieron empatía directamente; todas con autoinformes (escalas simples/múltiples o entrevistas). Un único estudio incluyó valoraciones de usuarios y expertos.
- Efectos de uso: mayor interacción y rapidez de respuesta con chatbot empático frente a control no empático; valoraciones de empatía/usabilidad variables (p.ej., 75% percibió un bot específico como empático, útil y atractivo).
- Definición de empatía: solo 26% (5/19) ofrecieron definición explícita.
- Sesgo y calidad: RCTs con bajo riesgo; no aleatorizados con riesgo moderado-alto. Calidad global moderada cuando se reportó diseño+implementación; baja cuando solo diseño.
- Tendencias: incremento de publicaciones desde 2022; mínima integración de voz pese a su relevancia para empatía.

## Limitaciones
- Alta heterogeneidad de diseños de AC, métricas técnicas y formatos de evaluación humana, dificultando comparaciones y síntesis.
- Escasez de definiciones operativas de empatía y ausencia de escalas estandarizadas en la mayoría de estudios.
- Predominio de autoinformes (sesgo subjetivo) y limitada participación de expertos clínicos.
- Poca incorporación de señales vocales (solo 2 estudios), pese a su valor para detectar afecto/empatía.
- Calidad metodológica dispar: varios estudios con informes incompletos y riesgo de sesgo moderado-alto.
- Posibles sesgos y riesgos éticos/privacidad asociados a LLM/transformadores no consistentemente evaluados.

## Trabajo Futuro
- Adoptar definiciones claras y consensuadas de empatía (p.ej., OMS) y emplear escalas estandarizadas y validadas; incluir evaluación por expertos.
- Diseñar y ejecutar RCTs y estudios longitudinales que midan resultados clínicos (p.ej., PHQ, estrés/ansiedad) además de empatía percibida.
- Potenciar arquitecturas híbridas que combinen detección afectiva y gestión de diálogo, integrando señales textuales y vocales.
- Incorporar co-diseño/coevaluación con usuarios, clínicos y partes interesadas; iterar prototipos.
- Estandarizar métricas técnicas (clasificación, predicción, generación) para facilitar comparabilidad entre AC.
- Mitigar sesgos en datos/modelos (género, raza, cultura), y robustecer marcos de seguridad, ética y privacidad (transparencia, gobernanza de datos, latencia/fiabilidad en tiempo real).

## Citas Relevantes
- "The integration of CA design and its evaluation is crucial to produce empathic CAs."
- "Future studies should focus on using a clear definition of empathy and standardized scales for empathy measurement, ideally including expert assessment."
- "In addition, the diversity in measures used for technical assessment and evaluation poses a challenge for comparing CA performances, which future research should also address."
- "However, CAs with good technical and empathic performance are already available to users of MH care services, showing promise for new applications, such as helpline services."
- "Hybrid architecture seems best suited to the detection of user emotion followed by the retrieval of a suitable response."

## Notas Adicionales
Artículo de acceso abierto (JMIR Mental Health, vol. 11, e58974, doi: 10.2196/58974). Se observa un auge desde 2022 y fuerte presencia de modelos transformadores/LLM. Solo 2/19 estudios integraron voz a pesar de su relevancia para comunicar empatía. Solo 5/19 definieron explícitamente la empatía. Las evaluaciones humanas se centraron más en satisfacción/aceptación que en empatía, y casi siempre con autoinformes. Los motores híbridos destacaron en exactitud y riqueza de respuesta. Los autores subrayan necesidades de estandarización, co-diseño y evaluación ética/privacidad, y proponen aplicaciones en líneas de ayuda, triaje y postvención.
