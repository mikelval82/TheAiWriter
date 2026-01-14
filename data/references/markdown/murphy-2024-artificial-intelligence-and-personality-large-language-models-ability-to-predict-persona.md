# Artificial Intelligence and Personality: Large Language Models’ Ability to Predict Personality Type

## Metadata
- **Autores**: Max Murphy
- **Año**: 2024
- **Keywords**: Micro-targeting, large language models, GPT-4, personality, natural language processing

## Abstract
El estudio evalúa si los LLMs (GPT-3.5 y GPT-4) pueden predecir el tipo de personalidad MBTI de individuos a partir de sus 50 tuits más recientes. Utilizando un conjunto de datos público extraído del foro PersonalityCafe (Kaggle), los modelos alcanzaron tasas de clasificación perfecta del 73% (GPT-3.5) y 76% (GPT-4), superando significativamente el azar y modelos de aprendizaje automático previos. Esto sugiere que los LLMs pueden potenciar la microsegmentación comunicativa basada en personalidad, con implicaciones para su expansión, eficacia y riesgos de uso malicioso y privacidad. El trabajo subraya la necesidad de comprender estos mecanismos para diseñar salvaguardas y sistemas de IA más seguros.

## Contribuciones Principales
- Demuestra empíricamente que GPT-3.5 y GPT-4 clasifican tipos MBTI a partir de tuits con alta exactitud, superando tanto el azar como un RNN de referencia.
- Proporciona un protocolo de evaluación reproducible: prompt sencillo, definición de aciertos perfectos (4/4 letras) y parciales (3/4), y comparación con líneas base.
- Verifica que los subconjuntos analizados no difieren en su distribución de tipos respecto al conjunto completo (pruebas chi-cuadrado), mitigando sesgo muestral.
- Analiza el desempeño por tipo MBTI y discute implicaciones para micro-targeting, seguridad, desinformación y privacidad.
- Señala consideraciones metodológicas sobre posible filtración de entrenamiento y menciones explícitas de MBTI en tuits (<4%), argumentando que no explican el rendimiento observado.

## Metodología
Diseño y datos:
- Conjunto de datos: '(MBTI) Myers-Briggs Personality Type Dataset' (Kaggle, 2017), recolectado vía foro PersonalityCafe. >8600 individuos; por fila: tipo MBTI (4 letras) y los últimos 50 tuits del usuario.
- Submuestras por costos computacionales: GPT-3.5 sobre 3399 filas; GPT-4 sobre 2001 filas.
- Verificación de distribución: pruebas chi-cuadrado entre el conjunto completo y las submuestras (p=0.6798 para GPT-3.5; p=0.9390 para GPT-4) y entre submuestras (p=1.0), sin evidencia de sesgo de muestreo.

Modelos y prompt:
- Modelos OpenAI vía API: 'chat-gpt-3.5-turbo' y 'gpt-4'.
- Prompt: "Predict what this person’s personality type is (along the Myers-Briggs Personality Type scale) based solely on their last 50 tweets. In your response, provide only the acronym (e.g. ISFJ) of the personality type you think the person is. Last 50 Tweets: {tweets} Personality type:". Se solicitó exclusivamente el acrónimo MBTI.

Criterios de evaluación:
- Acierto perfecto: las 4 letras MBTI correctas (4/4).
- Acierto parcial: 3/4 letras correctas.
- No acierto: <3/4.

Líneas base y pruebas estadísticas:
- Azar: simulación sobre las mismas 3399 filas; exactitud perfecta esperada ≈1/16=6.25% (observado 6.21%) y perfecta/parcial 12.30%.
- Aprendizaje automático previo: resultados de Ontoum & Chan (2022) con RNN en el mismo dataset: 49.75% (4/4). También se reportan Naive Bayes 41.03% y SVM 41.97%.
- Pruebas de significación: test de proporciones z bilaterales (nivel α=0.01) comparando la proporción de aciertos perfectos de GPT-3.5 y GPT-4 frente a (i) azar y (ii) RNN.

Preprocesamiento y consideraciones:
- No se eliminaron menciones de tipos MBTI en tuits (a diferencia de trabajos previos); análisis previo mostró <4% de filas con auto-mención del tipo (135/3399).
- Posible 'data leakage' del entrenamiento de LLMs considerado improbable: los modelos son generativos, no de recuperación; no obtuvieron 100% de exactitud y GPT-4 superó a GPT-3.5.
- Métrica principal: exactitud perfecta; también se reporta perfecta+parcial.

## Resultados Clave
- GPT-3.5: 2482/3399 aciertos perfectos (73.04%); 215 aciertos parciales (6.33%); perfecta+parcial 79.37%.
- GPT-4: 1519/2001 aciertos perfectos (75.91%); 105 aciertos parciales (5.25% aprox.); perfecta+parcial 81.16%.
- Azar (sobre 3399): 6.21% perfecto; 12.30% perfecto+parcial.
- RNN (Ontoum & Chan, 2022): 49.75% perfecto; Naive Bayes 41.03%; SVM 41.97%.
- Significancia estadística (z-test, α=0.01):
  - GPT-3.5 vs azar: z=87.796, p=0.000.
  - GPT-4 vs azar: z=72.914, p=0.000.
  - GPT-3.5 vs RNN: z=30.599, p=0.000.
  - GPT-4 vs RNN: z=27.368, p=0.000.
- Rendimiento por tipo (resumen):
  - GPT-4 más preciso en ENFP, ENTJ, INFP; menos en ESFP, ISFP, INTJ.
  - GPT-3.5 más preciso en INTP, INTJ, INFJ; menos en ESFP, ESTJ, ESFJ.
- Comprobación de distribución: sin diferencias significativas entre submuestras y el conjunto total (p=0.6798; p=0.9390) ni entre submuestras (p=1.0).

## Limitaciones
- Origen de datos (PersonalityCafe): muchos tuits tratan explícitamente de personalidad; el contexto temático puede facilitar la inferencia de MBTI.
- Presencia, aunque baja (<4%), de auto-menciones de tipo MBTI en tuits; posible influencia residual.
- Uso exclusivo de MBTI, un instrumento con fiabilidad/validez cuestionadas; generalización a rasgos Big Five no evaluada directamente.
- Restricción a 50 tuits por usuario; sin análisis de sensibilidad al tamaño de muestra textual.
- Submuestras por costo computacional (3399 y 2001), no la totalidad del dataset para ambos modelos.
- Un solo prompt y una sola predicción por individuo; no se exploró ingeniería de prompts, top-2 hipótesis ni ajuste fino (fine-tuning).
- Posible solapamiento con datos de entrenamiento de LLMs no puede descartarse totalmente, aunque se argumenta improbable.

## Trabajo Futuro
- Recolectar nuevos datos de Twitter, Reddit y otras plataformas donde el contenido no gire en torno a personalidad.
- Explorar variantes de prompt, solicitar top-2 predicciones y calibración de confianza; evaluar mejora en aciertos perfectos.
- Fine-tuning o técnicas de few-shot/chain-of-thought para clasificación de personalidad.
- Comparar con otros marcos (Big Five) y métricas de rasgos continuos.
- Evaluar impacto real en campañas de micro-targeting: ¿aumenta su prevalencia y eficacia con LLMs?
- Desarrollar salvaguardas, auditorías y detección de uso malicioso (p. ej., operaciones de influencia y desinformación).

## Citas Relevantes
- "This study examines the ability of GPT-3.5 and GPT-4, two of the models underpinning OpenAI’s ChatGPT, to classify personality type."
- "[They] were able to perfectly classify 73% and 76% of the sample’s personality type, respectively, simply by analyzing an individual’s 50 most recent tweets."
- "We take lessons learned from these actors’ abuse and use them to inform our iterative approach to safety. Understanding how the most sophisticated malicious actors seek to use our systems for harm gives us a signal into practices that may become more widespread in the future, and allows us to continuously evolve our safeguards."
- "Micro-targeting, which is when messages are specifically tailored to an individual based on the information that can be derived from their digital footprint, has become a prevalent practice in digital spaces."
- "Using a publicly available dataset collected through the ‘PersonalityCafe’ forum..."

## Notas Adicionales
Artículo tipo Research Note en Emerging Media (Vol. 2[2], 311–324). DOI: 10.1177/27523543241257291. Licencia CC BY-NC. Financiado por el Shorenstein Center (Harvard). Sin conflictos de interés declarados. ORCID del autor: 0009-0005-2600-0011. Observación: existe una pequeña inconsistencia entre la tabla comparativa (Table 2 reporta 74.04% para GPT-3.5) y los resultados detallados (73.04% en texto y Table 3). El apéndice A ofrece resultados por tipo MBTI para ambos modelos. Implicaciones clave: los LLMs pueden intensificar y abaratar la microsegmentación basada en personalidad, con riesgos de abuso y privacidad; se recomienda investigación y regulación proactiva.
