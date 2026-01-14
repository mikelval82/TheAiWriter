# AIVA: An AI-based Virtual Companion for Emotion-aware Interaction

## Metadata
- **Autores**: Chenxi Li
- **Año**: 2025
- **Keywords**: multimodal sentiment analysis, large language models, emotion-aware HCI, cross-modal fusion transformer, supervised contrastive learning, sentiment prototypes, prompt engineering, virtual companion, text-to-speech, animated avatar

## Abstract
El trabajo presenta AIVA, un compañero virtual basado en IA que integra percepción multimodal de sentimientos con LLMs para lograr interacciones empáticas. Propone MSPN, una red de percepción de sentimientos que fusiona texto e imagen mediante atención cruzada y un transformer de fusión con prototipos de sentimiento y aprendizaje contrastivo supervisado. Los estados emocionales detectados alimentan a un LLM mediante ingeniería de prompts sensible a la emoción (EPE), y la respuesta se expresa con TTS y un avatar animado. En benchmarks (MVSA-Single, MVSA-Multi) MSPN supera a baselines multimodales y unimodales, y muestra sólido desempeño previo en TumEmo. La arquitectura se orienta a aplicaciones en asistentes sociales, cuidado y salud mental.

## Contribuciones Principales
- Puente entre computación afectiva multimodal y LLMs para construir un agente consciente de emociones y capaz de interacción empática.
- MSPN: método de análisis de sentimiento multimodal con transformer de fusión cruzada, prototipos de sentimiento y aprendizaje contrastivo supervisado a nivel de prototipos.
- EPE: estrategia de ingeniería de prompts que inyecta pistas emocionales en el LLM para respuestas alineadas afectivamente.
- Integración extremo a extremo con TTS (GPT-SoVITS) y avatar animado (Live2D) para retroalimentación expresiva verbal y visual.
- Validación experimental que demuestra mejoras sobre baselines en clasificación de sentimientos y ejemplos cualitativos de interacción empática en tiempo real.

## Metodología
Arquitectura general (AIVA):
- Percepción: MSPN captura señales emocionales desde entradas multimodales (texto + imagen) con dos codificadores (BERT para texto; ViT para visión).
- Fusión: Atención cruzada bidireccional (CA) produce representaciones enriquecidas por modalidad y una representación multimodal unificada Z. Un transformer de fusión cruzada introduce tokens aprendibles de prototipos de sentimiento (uno por categoría) que extraen información afectiva de Z mediante atención.
- Objetivos de entrenamiento: combinación de pérdida de clasificación (cross-entropy) y aprendizaje contrastivo supervisado bidireccional (representación→prototipo y prototipo→representación) para alinear espacios y robustecer la discriminación emocional. Un hiperparámetro λ equilibra ambas pérdidas.
- Inyección al LLM: Los resultados de MSPN se incorporan como prefijo/etiquetas en el prompt (EPE). El prompt incluye: rol empático, few-shot con marcadores de emoción (p. ej., #Sad#, #Happy#), historial para contexto emocional y CoT para razonar antes de responder.
- Generación expresiva: Un LLM preentrenado (LLaMA2-Chat) genera la respuesta textual; TTS (GPT-SoVITS) convierte el texto en voz expresiva; un avatar Live2D sincroniza expresiones faciales/gestos con el estado emocional.
Datos y configuración:
- Preentrenamiento MSPN en TumEmo (~195k tripletas imagen-texto-emoción). Fine-tuning/evaluación en MVSA-Single (etiquetas positivo/neutral/negativo) y MVSA-Multi (anotaciones multi-etiqueta).
- Hiperparámetros: lr=2e-5; batch=24 (TumEmo) y 16 (MVSA); optimizador Adam; 1 época en TumEmo; 10 épocas en cada MVSA.

## Resultados Clave
- MVSA-Single: MSPN alcanza 74.25% de accuracy y 72.84% de F1, superando a modelos text-only (BERT: 71.11%/69.70%) y multimodales previos (MGNNS: 73.77%/72.70%).
- MVSA-Multi: MSPN logra 73.48% de accuracy y 70.01% de F1, por encima de MGNNS (72.49%/69.34%) y BERT (67.59%/66.24%).
- TumEmo (preentrenamiento MSPN): 81.81% accuracy, 82.48% precisión, 81.81% recall, 81.89% F1, con t-SNE mostrando clusters bien separados para emociones (p. ej., Happy, Sad, Angry) y solapamientos parciales (Fear-Sad).
- Cualitativo (MSPN): predicciones correctas en ejemplos con señales textuales y visuales combinadas (p. ej., Happy en paisaje invernal con texto positivo; Love en imagen de pareja).
- Cualitativo (AIVA): respuestas empáticas y avatares coherentes con el sentimiento detectado (p. ej., alegría ante la compra de un perro; consuelo ante pérdida/daño de teléfono).
- Ablaciones MSPN:
  - Sin Cross Attention Fusion (CAF): MVSA-Single 72.94%/71.17; MVSA-Multi 18.70%/67.41 (degradación marcada).
  - Sin Cross-Modal Fusion Transformer (CMFT): MVSA-Single 71.68%/71.19; MVSA-Multi 70.76%/68.76.
  - Sin Supervised Contrastive Learning (SCL): MVSA-Single 73.01%/71.78; MVSA-Multi 69.41%/68.25.
- Sensibilidad a λ (pérdida contrastiva): mejor desempeño con λ=1.0 (MVSA-Single 74.25%/72.84; MVSA-Multi 73.48%/70.01); valores menores o mayores reducen F1/accuracy.

## Limitaciones
- No se presenta evaluación humana sistemática de la calidad empática, naturalidad o adecuación clínica de las respuestas.
- Modalidades consideradas en MSPN: texto e imagen; la voz (prosodia) y gestos no se incorporan en la percepción, pese a su relevancia afectiva.
- Validación centrada en benchmarks de redes sociales (MVSA) y TumEmo; falta evaluación en entornos en vivo o dominios sensibles (salud mental, cuidado).
- Dependencia de etiquetados discretos de emoción/sentimiento; posible desalineación entre categorías de datasets (p. ej., pos/neu/neg vs. emociones finas como Love, Calm, Angry).
- Posible error tipográfico en ablación (accuracy 18.70% en MVSA-Multi sin CAF), lo que dificulta interpretar el impacto real de ese componente.
- No se reportan análisis de robustez (ruido, sesgos), latencia en tiempo real ni consumos computacionales para despliegue.
- Aspectos éticos/privacidad y manejo de datos sensibles no se discuten en profundidad.

## Trabajo Futuro
- El paper no detalla explícitamente trabajo futuro; posibles direcciones incluyen:
- Incorporar audio/prosodia y señales no verbales adicionales (gestos, postura) en la percepción multimodal.
- Personalización y modelado de usuario a largo plazo para respuestas empáticas continuas y adaptativas.
- Evaluaciones humanas controladas (estudios con usuarios) y métricas psico-sociales de empatía y bienestar.
- Ampliación de categorías emocionales, detección continua de valencia/arousal e incertidumbre en las predicciones.
- Robustez, equidad y mitigación de sesgos; privacidad y seguridad en aplicaciones sensibles.
- Optimización para despliegue en tiempo real (latencia, eficiencia), y pruebas en escenarios clínicos/educativos.

## Citas Relevantes
- "We propose AIVA, an AI-based virtual companion that captures multimodal sentiment cues, enabling emotionally aligned and animated HCI."
- "AIVA introduces a Multimodal Sentiment Perception Network (MSPN) using a cross-modal fusion transformer and supervised contrastive learning to provide emotional cues."
- "This approach adapts the sentiment classification results as a prefix in the prompt, guiding the LLM to generate emotionally aligned responses."
- "An ideal HCI system, as illustrated in Figure 1, perceives user intentions and affective states through multimodal cues, combining language, facial expressions, and voice to support emotionally intelligent interaction."
- "The proposed AIVA framework aims to integrate multimodal sentiment perception with LLMs to construct emotionally intelligent virtual companion, enabling empathetic HCI."
- "Our extensive experiments demonstrate that AIVA outperforms existing methods in sentiment classification, emotion alignment, and multimodal interaction, providing a solid foundation for virtual companions and other human-centered AI applications."

## Notas Adicionales
– AIVA combina MSPN + EPE + TTS (GPT-SoVITS) + avatar Live2D sobre LLaMA2-Chat para interacción empática.
– Datasets: TumEmo para preentrenamiento; MVSA-Single/Multi para evaluación. Hiperparámetros: lr 2e-5; batch 24/16; 1 época (TumEmo) y 10 (MVSA); Adam.
– MSPN emplea BERT (texto) y ViT (imagen), atención cruzada, prototipos de sentimiento aprendibles y aprendizaje contrastivo supervisado bidireccional, además de pérdida de clasificación; λ=1.0 es óptimo en ablaciones.
– La visualización t-SNE de prototipos sugiere buena separabilidad entre emociones principales y solapamientos en clases cercanas (p. ej., Fear y Sad).
– Categorías ilustrativas en figuras incluyen Love, Calm, Angry, Bored; las métricas de MVSA se reportan en positivo/neutral/negativo y multi-etiqueta, lo que indica que MSPN se adapta a distintos esquemas de etiquetas.
– El valor 18.70% de accuracy en MVSA-Multi sin CAF parece atípico; podría ser errata y conviene confirmarlo.
– El año de la versión arXiv indicada es 2025 (arXiv:2509.03212v1, 3 Sep 2025).
