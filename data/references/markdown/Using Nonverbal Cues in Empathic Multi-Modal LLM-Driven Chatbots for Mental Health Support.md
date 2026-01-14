# Using Nonverbal Cues in Empathic Multi-Modal LLM-Driven Chatbots for Mental Health Support

## Metadata
- **Autores**: Matthias Schmidmaier, Jonathan Rupp, Cedrik Harrich, Sven Mayer
- **Año**: 2025
- **Keywords**: human-computer interaction, HCI, LLM, multi-modal LLM, MLLM, empathy, context awareness, nonverbal communication, mental health, facial expression recognition, GPT-4o

## Abstract
El paper explora cómo incorporar señales no verbales (expresiones faciales) en chatbots de salud mental impulsados por LLMs multimodales (MLLM). Primero valida el reconocimiento de expresiones faciales (FER) con GPT-4o/4o-mini usando un subconjunto balanceado del dataset FER (FER+1400) y una tarea temporal basada en secuencias del dataset MPI. Luego implementa un prototipo de chatbot multiagente que integra contexto visual (buffer de 4 s, 5 fps) en la generación de respuestas. En un estudio con N=200 y cuatro condiciones (texto; texto+placebo FER; texto+FER; texto+FER+proactividad), encuentran efectos significativos del contexto no verbal en el estilo lingüístico (cognitivo y afectivo) de las respuestas, pero sin incrementos significativos en la empatía percibida (PETS). El trabajo demuestra el potencial de usar contexto no verbal para adaptar el comportamiento de respuesta de LLMs y discute implicaciones éticas y de privacidad.

## Contribuciones Principales
- Validación sistemática de las capacidades de GPT-4o/4o-mini para FER con datos balanceados (FER+1400), alcanzando hasta 87% de exactitud con imágenes y mostrando limitaciones con blendshapes.
- Demostración de interpretación temporal usando rejillas de fotogramas (5 fps) para capturar dinámicas faciales breves.
- Diseño e implementación de un sistema multiagente (FER + asistente(s) GPT-4o) que integra contexto visual no verbal en la respuesta del chatbot.
- Evidencia experimental (N=200) de que el contexto no verbal cambia el estilo lingüístico (mayor percepción visual, menor certidumbre y pensamiento dicotómico), pero no aumenta significativamente la empatía percibida.
- Prototipo web ligero y código para facilitar investigación futura en MLLM móviles.

## Metodología
Enfoque en dos etapas. Pre-evaluación (RQ1): (1) FER desde imágenes con GPT-4o y GPT-4o-mini usando un subconjunto balanceado FER+1400 (200 imágenes por categoría del FER original, etiquetado reforzado con FER+; 48x48, B/N); métrica de exactitud, precisión, recall y F1. (2) FER desde descriptores numéricos de blendshapes (MediaPipe, 52 rasgos) comparado con imagen. (3) Interpretación temporal mediante rejillas de fotogramas (5 fps) creadas a partir de 54 vídeos del MPI Facial Expressions Database; se incluyeron categorías emocionales y conversacionales (agreement, contemplation) y se evaluó la predicción de la categoría superior.
Sistema: Frontend Vue.js con interfaz tipo chat y captura de webcam; detección facial (MediaPipe), recorte del rostro y buffer de 4 segundos (120x160 px, 5 fps) ensamblado en una imagen-rejilla base64. Backend Python para orquestación multiagente: una instancia GPT-4o-mini para FER (chat completions) y asistentes GPT-4o (Threads API) para la conversación. Eventos: @on_verbal (se envía buffer con cada mensaje de texto) y @on_inactivity (proactividad tras 15 s iniciales o 60 s desde la última reacción). Cuatro modos: A (solo texto), B (texto + placebo FER), C (texto + FER en @on_verbal), D (texto + FER + proactividad @on_inactivity). Prompts estandarizados para empatía breve, reactividad emocional concisa y uso del análisis no verbal en C y D.
Estudio de usuarios (RQ2, RQ3): N=200 (Prolific), asignación aleatoria a A–D, dos tareas (5–10 min) sobre situaciones interpersonales (trabajo/universidad; con desconocidos), encuesta tras cada tarea: PETS (10 ítems, 0–100) y escalas de percepción no verbal (nivel y efecto) y activación emocional. Análisis: pruebas no paramétricas (Kruskal–Wallis, post-hoc Dunn-Holm) y análisis LIWC-22 de las respuestas del sistema (procesos psicológicos, percepción, afecto, estilo lingüístico). Ética: aprobación institucional; enfoque de soporte informal, no terapéutico; separación de datos de imagen y conversación; capturas limitadas a la caja facial.

## Resultados Clave
- Pre-evaluación FER (imágenes): GPT-4o alcanzó 86–87% de exactitud y GPT-4o-mini 84% en FER+1400; descripciones textuales coherentes y sensibles al contexto.
- Pre-evaluación FER (blendshapes): rendimiento significativamente inferior (GPT-4o 35–36%, GPT-4o-mini 30%), con sobrepredicción de felicidad y confusiones para tristeza/neutral; H1b rechazada.
- Interpretación temporal (rejilla 5 fps): exactitud GPT-4o 53–58% y GPT-4o-mini 36–44%; análisis textual mostró razonamiento temporal útil (p. ej., fluctuaciones entre contemplación y confusión); apoya H1c.
- Tráfico conversacional: 3135 mensajes totales; 2369 con contexto visual; 240 proactivos (modo D). FER en estudio: alta frecuencia de contemplación (94–100%) y neutral (88–100%), seguida de tristeza (55–70%) y acuerdo (50–61%).
- LIWC (H2a): incrementos significativos en léxico de percepción visual en C y D; menor pensamiento dicotómico y menor certidumbre en C/D vs A/B; mayor diferenciación (D). En D también cambios en causalidad y tentatividad. Confirmado H2a.
- LIWC (H2b): reducciones significativas de afecto global, tono negativo y emociones globales en C/D vs A/B; disminución de emociones negativas y ansiedad (especialmente en D). H2b aceptada.
- Métricas lingüísticas: D tuvo mayor conteo de palabras (mediana ≈ 340) por proactividad; C mostró más palabras por oración y mayor analiticidad (vs B); D incrementó 1PL ("we").
- Empatía percibida (PETS): sin diferencias significativas entre grupos (medianas ≈ 79–82); H3a, H3b y H3c rechazadas. Las escalas de percepción no verbal sí distinguieron A de B/C/D (y B < D en calidad), sugiriendo leve efecto placebo en percepción NVC pero no en empatía.

## Limitaciones
- Activación emocional moderada en tareas puntuales; posible subexpresión afectiva y techo de empatía de LLM reducen sensibilidad de PETS.
- Diseño transversal y situacional; falta de evaluación longitudinal y de vínculo/alianza sostenida.
- Muestra predominantemente del EEEA; potencial sesgo cultural en NVC y uso de sistemas.
- Sin comparación directa con apps existentes o intervención humana estándar.
- FER no validado con ground truth en situación in-the-wild; riesgo de malinterpretaciones.
- Rendimiento pobre con blendshapes; tensión privacidad-rendimiento no resuelta.
- Limitaciones de hardware/latencia y sostenibilidad para MLLM en tiempo real.
- Falta de feedback cualitativo profundo y medidas adicionales (p. ej., fisiología).

## Trabajo Futuro
- Diseñar estudios longitudinales que fomenten mayor activación emocional y alianza con el agente.
- Integrar explicaciones del razonamiento no verbal y calibración personalizada (transparencia/uncertainty-aware).
- Explorar salidas multimodales (señales visuales de atención, "empathic continuers"), y estrategias de prompting ante expresiones neutras.
- Ampliar disparadores contextuales (@on_waiting, @on_reading, dinámica de tecleo) para captar fases conversacionales.
- Mejorar privacidad con preprocesamiento local y blendshapes mejorados (few-shot, enfoque por regiones faciales).
- Fusionar modalidades (audio, prosodia, gestos) vía "cue-to-text" para enriquecer el contexto no verbal.
- Comparativas controladas con aplicaciones de referencia y con profesionales humanos.
- Incluir medidas adicionales (p. ej., marcadores fisiológicos de vinculación) y muestras culturalmente diversas.

## Citas Relevantes
- "We found significant effects on cognitive and affective dimensions of linguistic expression in system responses, yet no significant increases in perceived empathy."
- "image-based FER resulted in a higher accuracy of up to 87 %"
- "The results of our pre-evaluation regarding image-based FER (Section 4.2) confirm H1a, showing accuracies of 84−87% compared to 49 −59% in previous studies"
- "Our research demonstrates the general potential of using nonverbal context to adapt LLM response behavior, providing input for future research on augmented interaction in empathic MLLM-based systems."
- "we therefore reject hypotheses H3a, H3b, and H3c (RQ3)."
- "The person appears to be surprised with their mouth open and hand on the face."
- "We conclude that additional FER input significantly influenced the system’s language style, particularly regarding expressions of visual perception and cognitive processing that reflect more nuanced thinking."

## Notas Adicionales
Artículo MHCI039, Proc. ACM Hum.-Comput. Interact., septiembre 2025; DOI: 10.1145/3743724. Modelos: gpt-4o-2024-05-13 y gpt-4o-mini-2024-07-18. FER+1400: subconjunto balanceado (200 imágenes por categoría; B/N 48x48). Rejilla temporal: 5 fps, ventana de 4 s, 120x160 px, recorte con padding 15%. Eventos: @on_verbal y @on_inactivity (15 s/60 s). Separación de flujo FER y conversación para privacidad. Escala PETS (0–100) y percepción NVC (nivel/efecto). Código del prototipo: https://github.com/kaiaka/mllm-chatbot.git. Aprobación ética institucional y enfoque de apoyo informal no sustitutivo de terapia profesional.
