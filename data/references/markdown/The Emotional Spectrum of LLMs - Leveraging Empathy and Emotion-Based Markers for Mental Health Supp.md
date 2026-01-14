# The Emotional Spectrum of LLMs: Leveraging Empathy and Emotion-Based Markers for Mental Health Support

## Metadata
- **Autores**: Alessandro De Grandi, Federico Ravenda, Andrea Raballo, Fabio Crestani
- **Año**: 2024
- **Keywords**: empathetic chatbots, large language models, emotion recognition, emotion embeddings, cognitive empathy, mental health assessment, RACLETTE, Mistral 7B, Empathetic Dialogues, DailyDialog, Reddit Mental Health, suicide risk detection, explainable markers, Top-K sampling, QLoRA

## Abstract
El trabajo propone RACLETTE, un sistema conversacional empático basado en LLMs para apoyo en salud mental que: (1) reconoce y responde a estados emocionales con alta fidelidad mientras construye progresivamente un perfil emocional del usuario; y (2) utiliza dichos perfiles como marcadores interpretables para evaluación preliminar de trastornos mentales. El modelo (Mistral 7B afinado) emplea una estructura de 3 turnos (Prompt–Emotion–Response), predice emociones como siguiente token con muestreo Top-K y genera respuestas empáticas. Los perfiles emocionales se agregan a lo largo de la conversación y se comparan con perfiles característicos derivados de subreddits de salud mental (control: DailyDialog). RACLETTE supera baselines en clasificación de emociones y muestra que los embeddings emocionales permiten discriminar comunidades y detectar riesgo de suicidio en un esquema no supervisado con alta sensibilidad. El enfoque ofrece explicabilidad, evita datos clínicos sensibles y sugiere un marco para tamizaje temprano.

## Contribuciones Principales
- Introducción de RACLETTE, un chatbot empático que predice la emoción como tarea generativa de next-token y responde en consecuencia usando una estructura de 3 turnos.
- Actualización en tiempo real del perfil emocional del usuario durante la conversación y uso de dicho perfil para ajustar respuestas empáticas.
- Definición de embeddings emocionales explicables como combinaciones ponderadas de emociones discretas, agregadas a través de turnos y conversaciones.
- Creación de perfiles emocionales de trastornos mentales a partir de Reddit (p. ej., depresión, BPD, bipolaridad, PTSD, esquizofrenia, adicción, suicidio) y comparación con perfiles de usuarios como marcadores interpretables.
- Mejora del estado del arte en exactitud de clasificación emocional en Empathetic Dialogues frente a CAiRE y otros baselines.
- Demostración cualitativa de propiedades algebraicas de los embeddings (p. ej., depresión + esquizofrenia ≈ bipolar en el espacio reducido con t-SNE).
- Detección no supervisada de riesgo de suicidio con alta recall, usando divergencias KL/JS y similitud coseno entre perfiles emocionales.

## Metodología
RACLETTE se basa en Mistral 7B afinado con SFT + QLoRA para eficiencia (nf4, bfloat16), empleando un formateo de datos de 3 turnos: <|prompter|> Prompt <|endoftext|>, <|emotion|> Etiqueta, <|assistant|> Respuesta. La máscara causal permite que el decodificador aprenda simultáneamente: (a) predecir la emoción como siguiente token (clasificación generativa) y (b) generar la respuesta empática condicionada al prompt y a la emoción. La predicción emocional usa muestreo Top-K (K=10) repetido 10 veces por prompt para obtener una distribución empírica sobre un vocabulario de 32 emociones. Los perfiles emocionales del hablante se obtienen agregando (promedio de muestras por frase y promedio sobre turnos) dichas distribuciones a lo largo de la conversación.
Un embedding emocional se define como combinación convexa de vectores base de emociones discretas (coeficientes no negativos que suman 1). La suma de embeddings a lo largo de interacciones representa estados afectivos complejos y acumulados. Para construir marcadores de trastornos, se procesan 1.000 posts por subreddit (Reddit Mental Health Dataset), segmentando en oraciones y aplicando el clasificador emocional (10 muestreos por oración), sumando y normalizando para obtener el perfil por trastorno. Como grupo control se usa DailyDialog, extrayendo su distribución emocional.
Evaluación 1 (empatía): en Empathetic Dialogues (24.850 diálogos), se reporta clasificación emocional a nivel de turno y conversación, y calidad de respuestas con BERTScore. Evaluación 2 (perfiles de trastornos): análisis cualitativo y t-SNE de embeddings; comparación de perfiles (p. ej., similitudes entre depresión y suicidio). Evaluación 3 (riesgo de suicidio no supervisado): dataset binario (SuicideWatch vs CasualConversation, ~10.585 muestras en test). Para cada post se genera embedding por agregación; se calcula distancia/similitud con embeddings de referencia (suicidio, depresión, BPD, bipolar, PTSD, adicción, esquizofrenia; negativos: control DailyDialog, distribución uniforme y CasualConversation). Se decide por cercanía usando KL, JS o coseno; método combinado marca positivo si cualquiera de las métricas indica riesgo. Entrenamiento: QLoRA (lora_alpha=16, lora_dropout=0.1, lora_r=64), batch_size=1 con acumulación de gradiente=16, warmup_ratio=0.3, scheduler coseno, lr=2e-5, 3 épocas, AdamW.

## Resultados Clave
- Clasificación emocional (Empathetic Dialogues): exactitud a nivel de turno 0.56; a nivel de conversación 0.59 (macro/weighted P/R/F1≈0.59/0.59/0.58). BERTScore en generación empática ≈0.87, indicando alta similitud semántica con respuestas humanas.
- Comparativa con baselines en exactitud emocional: RACLETTE 0.59 vs Chen et al. 2024 (0.53), CAiRE (0.51), Li et al. 2022 (0.46), Gao et al. 2021 (0.42).
- Perfiles de trastornos (Reddit): embeddings muestran patrones distintivos y relaciones esperadas (p. ej., depresión≈suicidio; adicción≈alcoholismo; PTSD cercano a esquizofrenia). t-SNE refleja agrupamientos coherentes; la suma depresión+esquizofrenia produce embedding cercano a bipolar.
- Detección de riesgo de suicidio (no supervisado):
  - KL: Prec=0.71, Rec=0.90, F1=0.79, Acc=0.77
  - JS: Prec=0.67, Rec=0.93, F1=0.78, Acc=0.76
  - Coseno: Prec=0.65, Rec=0.93, F1=0.77, Acc=0.74
  - Combinado (OR): Prec=0.63, Rec=0.95, F1=0.76, Acc=0.72
  - Baselines no supervisados: RoBERTa+KMeans (Prec=0.72, Rec=0.84, F1=0.78, Acc=0.77); BERT+KMeans (0.65/0.80/0.71/0.69). El método combinado maximiza la sensibilidad.

## Limitaciones
- Dependencia de datos emocionales etiquetados y de calidad; la anotación es costosa y compleja.
- Sesgos y ruido de datos en redes sociales (auto-reporte, hablar por terceros, estilos y contextos de expresión heterogéneos), no representativos de poblaciones clínicas.
- Comorbilidades y perfiles psicológicos superpuestos complican la interpretación de perfiles emocionales.
- Diferencias entre expresión en línea y cara a cara pueden degradar la validez ecológica.
- Riesgos éticos de uso clínico inapropiado, potenciales sesgos y conductas dañinas del sistema; necesidad de salvaguardas.
- Falta de validación clínica formal y de datos profesionales diagnosticados; el sistema se posiciona como herramienta de apoyo y tamizaje preliminar, no diagnóstico.

## Trabajo Futuro
- Validación clínica rigurosa con cohortes diagnosticadas profesionalmente y evaluación longitudinal.
- Curación/expansión de datasets con anotaciones expertas y mayor diversidad cultural/lingüística; reducción de sesgos.
- Integración de más clases emocionales y señales multimodales (voz, prosodia, fisiología) para perfiles más ricos.
- Modelado explícito de intensidades y co-ocurrencias emocionales; calibración de incertidumbre.
- Mecanismos de seguridad, detección de daños y alineación ética; protocolos de derivación a profesionales.
- Adaptación de dominio a entornos clínicos reales y evaluación de impacto en flujo terapéutico.
- Exploración de otros marcadores interpretables (p. ej., coherencia semántica) combinados con perfiles emocionales.

## Citas Relevantes
- "First, we present RACLETTE, a conversational system that demonstrates superior emotional accuracy compared to considered benchmarks in both understanding users’ emotional states and generating empathetic responses during conversations, while progressively building an emotional profile of the user through their interactions."
- "Second, we show how the emotional profiles of a user can be used as interpretable markers for mental health assessment."
- "RACLETTE uses an unconventional 3-turn structure where the model is trained to predict the user’s emotion as a next-token prediction, leveraging the generative capabilities of the underlying Mistral 7B model, and responds empathetically based on the predicted emotion."
- "by summing the depression and schizophrenia’s embeddings, a new representation can be obtained, that is very close, in the embedding space, to bipolar."
- "A BERTSCORE of 0.87 indicates high semantic similarity between the responses given by the model and the target replies contained in the test set that were given by the human listeners."
- "This experiment is designed to maximize recall, a critical metric in scenarios where missing a positive instance has severe consequences"

## Notas Adicionales
El enfoque convierte la predicción de emociones en una tarea generativa con muestreo estocástico repetido, permitiendo estimar distribuciones (y por tanto embeddings) que se agregan como marcadores explicables. La arquitectura y el formateo de 3 turnos explotan la autoregresividad para clasificación y respuesta conjunta. Observación notable: el modelo generaliza a emociones fuera del conjunto de 32 etiquetas cuando aparecen explícitamente en los prompts (p. ej., bored, confused), aunque se descartan en evaluación. El pipeline evita datos clínicos sensibles; utiliza Empathetic Dialogues para entrenamiento, Reddit para perfiles de trastornos y DailyDialog como control. El análisis comparativo (KL, JS, coseno) y la regla OR priorizan sensibilidad para tamizaje de suicidio, con trade-off esperado en precisión. arXiv:2412.20068.
